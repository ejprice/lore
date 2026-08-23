"""Contract — packet 61a-w1, ``PrincipalStore.delete`` = REFUSE-WHILE-KEEPING (finding #402).

Written by ``contract-61a-w1`` (2026-08-23). The builder builds FROM this; it writes NO
production code. *Every "RED at HEAD" claim below is scoped to the tree at ``84d20a3``:
``PrincipalStore.delete`` cascades ``principal_key`` ONLY and has no keeper check, so a
hard-delete of a principal who KEEPS a keep SUCCEEDS and silently leaves a dangling
``keep.keeper`` — the #402 data-integrity bug.*

SPEC (the work order, executed verbatim — never re-transcribed):
``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` §FR-4 — RULING: keeper-on-
principal-delete = REFUSE-WHILE-KEEPING (NOT cascade-delete, NOT silent-reassign). A hard
``delete`` of a principal who keeps ≥1 keep is REFUSED (loud, typed), naming the kept keep
ids + the remediation; a member-only principal (keeps nothing) deletes cleanly, its
``member_of`` memberships auto-cleaned. Finding #402 has the two-defect provenance.

STORE LAW (``docs/reference/surrealdb-31-capabilities.md``): §2 (``record<t>`` FIELD links
do NOT auto-clean on target delete — the ``keep.keeper`` dangle #402 is about); §4 (graph
RELATION edges DO self-delete when an endpoint node is deleted — so ``member_of`` cleans
itself); §3 (the delete is ONE ``execute_transaction``). The load-bearing member_of vs
keep.keeper cascade disagreement (#402 body vs store-law §4) was SETTLED BY CONSTRUCTION —
``scripts/probe_member_of_cascade.py`` (committed, self-checking, exit 0 with positive
controls): ``member_of`` AUTO-CASCADES on an ``in``-endpoint (member) delete; ``keep.keeper``
DANGLES on a keeper delete. So the fix needs NO explicit ``DELETE member_of`` for the member
case, and refuse-while-keeping is what prevents the ``keep.keeper`` dangle for the keeper case.

⚠ RED vs POSITIVE CONTROL. The RED-until-built pins are the REFUSE pins (a keeper delete
raises ``PrincipalHasKeepsError``; the type exists; no ``keep.keeper`` can dangle via
delete). The member-only / keeps-nothing pins are GREEN on HEAD by design — they are
POSITIVE CONTROLS (fixtures-must-discriminate, §FR-4 rider: a fixture that only tests the
keeper case cannot tell "refuse a keeper" from "refuse EVERY delete") and regression guards
(the fix must not turn a member-only delete into a refusal). Each pin says which it is.

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). Per-test unique database, reaped on exit.
NO skip marker — an unreachable store is a LOUD failure, not a skip.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import loremaster.principals as principals_module
import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.index.records import sha512_hex
from loremaster.keeps import KeepStore
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import PrincipalStore, PrincipalStoreError
from loremaster.store.surreal_schema import (
    MEMBER_OF_RELATION,
    PRINCIPAL_KEY_TABLE,
    PRINCIPAL_TABLE,
)
from surrealdb import RecordID

_KEEPER_EMAIL = "keeper@example.com"
_MEMBER_EMAIL = "member@example.com"
_LONER_EMAIL = "loner@example.com"  # keeps nothing AND member of nothing
_NEW_KEEPER_EMAIL = "successor@example.com"

# The typed error the builder introduces (§FR-4 rider). Referenced BY NAME via getattr, not
# imported at module top, so this file COLLECTS on HEAD (where the class does not exist yet)
# and every pin fails BEHAVIOURALLY, never as an ImportError that hides the whole module
# (finding #133).
_HAS_KEEPS_ERROR_NAME = "PrincipalHasKeepsError"


def _bare(record_id: str) -> str:
    """The id part of a ``table:id`` string (``keep:abc`` -> ``abc``); a bare id passes
    through. Mirrors ``PrincipalStore.delete``'s own ``partition(':')[2] or id``."""
    return record_id.partition(":")[2] or record_id


@pytest_asyncio.fixture()
async def delete_env() -> AsyncIterator[tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]]:
    """A ready principal + principal_key + keep + member_of world on a fresh unique DB.

    Readied in dependency order: ``principal`` (the ``keep.keeper`` link target AND the
    ``member_of`` ENFORCED ``IN`` endpoint) FIRST, then ``principal_key``, then keep +
    member_of. Three principals are seeded — a keeper, a member, and a loner (keeps nothing
    and belongs to no household). Reaped on exit.

    ⚠ ``PrincipalStore.delete``'s new keep-count runs on the PrincipalStore's OWN connection
    (§FR-4: no ``KeepStore`` dependency), so the ``keep`` table MUST exist in this database —
    the KeepStore.ensure_ready here provides it. (The CLI's equivalent guarantee is pinned in
    ``test_keep_remediation_cli_61.py``.)
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    principal_store = PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    key_store = PrincipalKeyStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    keep_store = KeepStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await principal_store.ensure_ready()  # principal FIRST (link target + edge endpoint)
    await key_store.ensure_ready()  # principal_key
    await keep_store.ensure_ready()  # keep + member_of
    for email in (_KEEPER_EMAIL, _MEMBER_EMAIL, _LONER_EMAIL, _NEW_KEEPER_EMAIL):
        await principal_store.create(email=email)
    try:
        yield principal_store, key_store, keep_store, env
    finally:
        await keep_store.close()
        await key_store.close()
        await principal_store.close()
        await drop_database(env)


async def _count(env: SurrealEnv, statement: str, params: dict[str, Any] | None = None) -> int:
    """Raw ``count()`` via a fresh admin connection (tolerant of an ABSENT table → 0)."""
    connection = await connect_admin(env)
    try:
        try:
            rows = await run(connection, statement, params or {})
        except Exception:  # noqa: BLE001 - an absent table is not the failure under test
            return 0
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            return 0
        return int(rows[0].get("count", 0))
    finally:
        await connection.close()


async def _dangling_member_of_where_in(env: SurrealEnv, principal_bare_id: str) -> int:
    """How many ``member_of`` edges still have ``in`` == the (possibly-deleted) principal."""
    return await _count(
        env,
        f"SELECT count() FROM {MEMBER_OF_RELATION} WHERE in = $p GROUP ALL",
        {"p": RecordID(PRINCIPAL_TABLE, principal_bare_id)},
    )


async def _principal_key_count(env: SurrealEnv, principal_bare_id: str) -> int:
    return await _count(
        env,
        f"SELECT count() FROM {PRINCIPAL_KEY_TABLE} WHERE principal = $p GROUP ALL",
        {"p": RecordID(PRINCIPAL_TABLE, principal_bare_id)},
    )


async def _mint_key(key_store: PrincipalKeyStore, *, email: str, name: str) -> None:
    """Mint a key for ``email`` (the CLI's mint recipe — a hashed ``name:secret``)."""
    await key_store.mint(email=email, name=name, secret_hash=sha512_hex(f"{name}:secret-{name}"))


# =========================================================================== #
# The typed error (offline — no store). RED at HEAD (the class does not exist).
# =========================================================================== #


class TestPrincipalHasKeepsErrorType:
    def test_the_error_class_exists_and_subclasses_principal_store_error(self) -> None:
        """§FR-4 rider: the refusal is a LOUD typed error
        ``PrincipalHasKeepsError(PrincipalStoreError)`` — so ``_dispatch``'s existing
        ``except PrincipalStoreError`` launders it to a ``lore-adm:`` stderr line + exit 1
        with NO new catch clause. RED at HEAD (the attribute is absent). A build that raised
        a bare ``PrincipalStoreError`` (no dedicated subclass) or a non-``PrincipalStoreError``
        would redden here."""
        error_cls = getattr(principals_module, _HAS_KEEPS_ERROR_NAME, None)
        assert error_cls is not None, (
            f"{_HAS_KEEPS_ERROR_NAME} is not defined in loremaster.principals — the "
            f"refuse-while-keeping typed error is unbuilt (packet 61a-w1, §FR-4)"
        )
        assert isinstance(error_cls, type) and issubclass(error_cls, PrincipalStoreError), (
            f"{_HAS_KEEPS_ERROR_NAME} must subclass PrincipalStoreError so the existing CLI "
            f"launder (_dispatch's except PrincipalStoreError) catches it: {error_cls!r}"
        )


# =========================================================================== #
# REFUSE-WHILE-KEEPING (live). The RED-until-built core of #402.
# =========================================================================== #


class TestDeleteRefusesAKeeperWhileKeeping:
    async def test_deleting_a_keeper_raises_the_typed_error_naming_the_keep_and_remediation(
        self, delete_env: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD. A hard-delete of a principal who keeps ≥1 keep is REFUSED with the
        typed ``PrincipalHasKeepsError`` (a ``PrincipalStoreError``), and the message NAMES
        the kept keep id AND the remediation (§FR-4 rider). On HEAD the delete SUCCEEDS (no
        raise), so ``pytest.raises`` reddens."""
        principal_store, _key_store, keep_store, _env = delete_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        with pytest.raises(PrincipalStoreError) as exc_info:
            await principal_store.delete(email=_KEEPER_EMAIL)
        error = exc_info.value
        assert type(error).__name__ == _HAS_KEEPS_ERROR_NAME, (
            f"the refusal must be the dedicated {_HAS_KEEPS_ERROR_NAME}, not a bare "
            f"{type(error).__name__} (§FR-4 rider — a typed refusal)"
        )
        message = str(error)
        assert _bare(keep.id) in message, (
            f"the refusal must NAME the kept keep id so the admin can remediate it; "
            f"expected {_bare(keep.id)!r} in {message!r}"
        )
        assert any(word in message.lower() for word in ("reassign", "delete")), (
            f"the refusal must name the remediation (reassign the keeper or delete the keep); "
            f"got {message!r}"
        )

    async def test_a_refused_delete_removes_NOTHING(
        self, delete_env: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD. The refusal is raised BEFORE any DELETE (state unchanged): the
        keeper principal, its keys, its ``member_of`` membership (Fork D auto-add) AND the
        keep all SURVIVE. On HEAD the keeper IS deleted (and its keep.keeper left dangling),
        so the survivor assertions redden. A keeper with a key AND a household membership is
        the discriminating fixture — a build that deleted ANY of them fails here."""
        principal_store, key_store, keep_store, env = delete_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="ship")
        await _mint_key(key_store, email=_KEEPER_EMAIL, name="laptop")
        keeper_before = await principal_store.get_by_email(_KEEPER_EMAIL)
        assert keeper_before is not None
        keeper_bare = _bare(keeper_before.id)

        with pytest.raises(PrincipalStoreError):
            await principal_store.delete(email=_KEEPER_EMAIL)

        assert await principal_store.get_by_email(_KEEPER_EMAIL) is not None, "keeper deleted despite refusal"
        assert await keep_store.get_keep(keep.id) is not None, "the kept keep vanished despite refusal"
        assert await _principal_key_count(env, keeper_bare) == 1, "keeper's key cascaded despite refusal"
        assert await _dangling_member_of_where_in(env, keeper_bare) == 1, (
            "the keeper's own member_of membership (Fork D) was removed despite refusal"
        )

    async def test_deleting_a_keeper_of_MULTIPLE_keeps_names_them_ALL(
        self, delete_env: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD (THE QUANTIFIER LAW; N=3 per the adversary residual). The refuse
        property is ∀ kept keeps, and the message must name EVERY kept keep so the admin can
        remediate them all — not just the first. A keeper of THREE keeps is refused and ALL
        THREE keep ids appear in the message. N=3 (not 2) so a ``[:2]``-style slice / name-first
        bug cannot pass: a build that refuses only on keeper-of-exactly-one, names only the
        first, or truncates the list, passes the single-keep pins but reddens here (the
        monoculture that hides an off-by-one / name-only-first / slice-cap)."""
        principal_store, _key_store, keep_store, _env = delete_env
        keep_a = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="a")
        keep_b = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="b")
        keep_c = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="session", name="c")
        with pytest.raises(PrincipalStoreError) as exc_info:
            await principal_store.delete(email=_KEEPER_EMAIL)
        message = str(exc_info.value)
        missing = [_bare(k.id) for k in (keep_a, keep_b, keep_c) if _bare(k.id) not in message]
        assert not missing, f"the refusal must name ALL 3 kept keeps; missing {missing} from {message!r}"

    async def test_a_member_only_principal_STILL_deletes_cleanly(
        self, delete_env: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ POSITIVE CONTROL (fixtures-must-discriminate, §FR-4 rider). GREEN on HEAD AND on
        the fix. A principal who keeps NOTHING but is a household MEMBER deletes cleanly
        (returns, no raise) — so the refuse pins above discriminate "refuse a KEEPER" from
        "refuse EVERY delete". A build whose keeper check refuses ALL deletes reddens here."""
        principal_store, _key_store, keep_store, _env = delete_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        # Must NOT raise — the member keeps nothing.
        await principal_store.delete(email=_MEMBER_EMAIL)
        assert await principal_store.get_by_email(_MEMBER_EMAIL) is None, "member-only principal not deleted"


# =========================================================================== #
# THE MEMBER DIMENSION, ruled decisively (§FR-4). Case 1 is the refuse class above;
# cases 2 & 3 are POSITIVE CONTROLS / regression guards (green on HEAD and the fix).
# =========================================================================== #


class TestDeleteMemberDimension:
    async def test_member_only_delete_proceeds_and_cleans_member_of(
        self, delete_env: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]
    ) -> None:
        """§FR-4 case 2 (POSITIVE CONTROL + regression guard). A member-only principal
        delete PROCEEDS and its ``member_of`` memberships are cleaned (auto-cascade, store-law
        §4 — probed). Behavioural: after the delete, ZERO ``member_of`` edges have
        ``in`` == the deleted member, and the keep + keeper survive. GREEN on HEAD (the edge
        auto-cascades and HEAD has no keeper check); the guard is that the fix does not
        REGRESS it (e.g. by refusing the member or by leaving the edge)."""
        principal_store, _key_store, keep_store, env = delete_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="ship")
        membership = await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        member_bare = membership.member_id
        pre = await _dangling_member_of_where_in(env, member_bare)
        assert pre == 1, "control: membership exists pre-delete"

        await principal_store.delete(email=_MEMBER_EMAIL)

        assert await principal_store.get_by_email(_MEMBER_EMAIL) is None, "the member was not deleted"
        assert await _dangling_member_of_where_in(env, member_bare) == 0, (
            "a member-only delete left a dangling member_of edge (store-law §4 says it "
            "auto-cascades — if the engine changed, re-derive the delete mechanism)"
        )
        assert await keep_store.get_keep(keep.id) is not None, "deleting a MEMBER destroyed the keep"
        keeper_after = await principal_store.get_by_email(_KEEPER_EMAIL)
        assert keeper_after is not None, "deleting a MEMBER destroyed the keeper"

    async def test_a_loner_delete_is_clean_and_cascades_only_its_keys(
        self, delete_env: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]
    ) -> None:
        """§FR-4 case 3 (POSITIVE CONTROL + regression guard). A principal who keeps nothing
        and is a member of nothing deletes cleanly, cascading ONLY its ``principal_key`` rows
        (today's behaviour). ``delete`` returns the cascaded key count. GREEN on HEAD and on
        the fix — the guard is that adding the keeper check does not break the ordinary
        delete-with-keys path."""
        principal_store, key_store, _keep_store, env = delete_env
        await _mint_key(key_store, email=_LONER_EMAIL, name="laptop")
        await _mint_key(key_store, email=_LONER_EMAIL, name="desktop")
        loner_before = await principal_store.get_by_email(_LONER_EMAIL)
        assert loner_before is not None
        loner_bare = _bare(loner_before.id)
        assert await _principal_key_count(env, loner_bare) == 2, "control: two keys exist pre-delete"

        cascaded = await principal_store.delete(email=_LONER_EMAIL)

        assert cascaded == 2, f"delete must report the 2 cascaded keys, got {cascaded!r}"
        assert await principal_store.get_by_email(_LONER_EMAIL) is None, "the loner was not deleted"
        assert await _principal_key_count(env, loner_bare) == 0, "the loner's keys were not cascaded"


# =========================================================================== #
# THE CASCADE-CORRECTNESS GUARD (§FR-4 rider — the ACTUAL #402 fix, live-store).
# =========================================================================== #


class TestNoDanglingLinkIsReachableViaDelete:
    async def test_a_keeper_delete_is_refused_so_no_keep_keeper_can_dangle(
        self, delete_env: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD — the data-integrity half of #402. Because a keeper cannot be
        deleted while they keep, a ``keep.keeper`` FIELD LINK can never point at a deleted
        principal. Attempt the delete → it is refused → the keep's ``keeper`` STILL
        dereferences to a LIVE principal. On HEAD the delete succeeds and ``keep.keeper``
        dangles (the keeper principal is gone but ``keep.keeper`` still names it), so the
        live-principal assertion reddens."""
        principal_store, _key_store, keep_store, _env = delete_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        with pytest.raises(PrincipalStoreError):
            await principal_store.delete(email=_KEEPER_EMAIL)
        # The keep's keeper link still resolves to a live principal (no dangle).
        keep_after = await keep_store.get_keep(keep.id)
        assert keep_after is not None
        keeper_principal = await principal_store.get_by_email(_KEEPER_EMAIL)
        assert keeper_principal is not None, (
            "the keeper principal was deleted — keep.keeper now dangles (#402)"
        )
        assert keep_after.keeper_id == _bare(keeper_principal.id), (
            "keep.keeper no longer resolves to the live keeper principal (a dangling link)"
        )

    async def test_a_member_only_delete_leaves_zero_dangling_member_of(
        self, delete_env: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv]
    ) -> None:
        """§FR-4 rider (the ``member_of`` half — POSITIVE CONTROL, probe-consistent). After a
        member-only delete, no ``member_of`` edge anywhere still points at the deleted
        principal. Distinct from the case-2 pin: this asserts the GLOBAL absence of any
        dangling edge for that principal, the direct property #402's body doubted (and the
        probe refuted). GREEN on HEAD and the fix — the guard reddens if a future engine
        change stops auto-cascading, or a build resurrects the member."""
        principal_store, _key_store, keep_store, env = delete_env
        keep_a = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="a")
        keep_b = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="b")
        await keep_store.add_household_member(keep_id=keep_a.id, member_email=_MEMBER_EMAIL)
        membership_b = await keep_store.add_household_member(keep_id=keep_b.id, member_email=_MEMBER_EMAIL)
        member_bare = membership_b.member_id
        assert await _dangling_member_of_where_in(env, member_bare) == 2, "control: member in TWO households"

        await principal_store.delete(email=_MEMBER_EMAIL)

        assert await _dangling_member_of_where_in(env, member_bare) == 0, (
            "a member in multiple households left dangling member_of edges after delete"
        )
