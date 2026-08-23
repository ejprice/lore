"""Contract — packet 61a-w1, the KeepStore REMEDIATION verbs (finding #402 / §FR-4 §4.3).

Written by ``contract-61a-w1`` (2026-08-23; D1 revision 2026-08-23). The builder builds FROM
this; it writes NO production code. *Every "RED at HEAD" claim is scoped to the tree at
``84d20a3``: ``KeepStore.set_keeper`` and ``KeepStore.delete_keep`` do not exist, so each verb
pin fails BEHAVIOURALLY (a guarded "verb is unbuilt" AssertionError), never an ImportError that
hides the module (finding #133).*

SPEC: ``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` §FR-4 "Riders" + the FR-4
addendum (D1/D2/D3 rulings) — the two admin remediation verbs that let an operator clear a
keeper's keeps so the principal delete (which REFUSES-WHILE-KEEPING) can proceed:

    KeepStore.set_keeper(*, keep_id, new_keeper_email) -> Keep
        Admin set_owner (§4.3 — the keeper IS the keep's owner field; spec-faithful name,
        the ``set-rank`` family). UPDATE keep.keeper to a NEW principal. A GHOST new-keeper is
        REFUSED (ENFORCED-flavoured: the email must resolve to a live principal), and the
        refusal changes nothing.
    KeepStore.delete_keep(*, keep_id) -> None
        Admin delete — remove the keep + its member_of edges (member_of auto-cascades on a
        keep-node delete, store-law §4 — probed, scripts/probe_member_of_cascade.py LEG C).

Both are CREDS-FREE admin-substrate verbs (like packet-60's keep verbs) — they do NOT route
through the 63/64 PDP at 61. STORE LAW (``docs/reference/surrealdb-31-capabilities.md``):
§2 (``record<principal>`` field links do NOT validate existence — hence the set_keeper
email-resolution guard is the ENFORCED-flavoured backstop); §4 (member_of auto-cascades on
endpoint delete). DRY (#102/#120): both verbs route through the shared ``KeepStore._query``
seam (auto-discovered by ``test_retry_seam.py``); they introduce no retry/query policy.

⚠ INTERFACE (D1 ruled 2026-08-23, FR-4 addendum): store methods ``set_keeper`` (RENAMED from
``reassign_keeper`` — spec-faithful §4.3 set_owner, one root) / ``delete_keep``; kwargs
``new_keeper_email`` / ``keep_id``. The CLI verbs stay ``set-keeper`` / ``delete-keep`` with
``--new-keeper`` (test_keep_remediation_cli_61.py).

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). Per-test unique database, reaped on exit.
NO skip marker — an unreachable store is a LOUD failure, not a skip.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from _enforced_relations_scaffold import ghost_id
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.keeps import KeepNotFoundError, KeepStore, KeepStoreError
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import PrincipalStore, PrincipalStoreError
from loremaster.store.surreal_schema import KEEP_TABLE, MEMBER_OF_RELATION
from surrealdb import RecordID

_KEEPER_EMAIL = "keeper@example.com"
_SUCCESSOR_EMAIL = "successor@example.com"
_MEMBER_EMAIL = "member@example.com"
_UNKNOWN_EMAIL = "nobody@example.com"


def _bare(record_id: str) -> str:
    return record_id.partition(":")[2] or record_id


def _verb(store: KeepStore, name: str) -> Any:
    """The bound remediation verb, or a LEGIBLE behavioural RED if it is unbuilt.

    Turns the HEAD ``AttributeError`` into a clean "verb is unbuilt" AssertionError (the
    ``_apply_key_ddl`` legible-RED idiom, finding #133) so a reader of the RED run sees the
    FEATURE is unbuilt, not that the TEST is broken. On a real build it returns the method."""
    method = getattr(store, name, None)
    assert callable(method), (
        f"KeepStore.{name} is unbuilt (packet 61a-w1, §FR-4 remediation verbs)"
    )
    return method


@pytest_asyncio.fixture()
async def remediation_env() -> AsyncIterator[tuple[PrincipalStore, KeepStore, SurrealEnv]]:
    """A ready principal + keep + member_of world on a fresh unique DB, with a keeper, a
    successor (reassign target) and a member seeded. Reaped on exit."""
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
    await principal_store.ensure_ready()  # principal FIRST (edge endpoint + link target)
    await key_store.ensure_ready()  # principal_key — PrincipalStore.delete cascades it
    await keep_store.ensure_ready()  # keep + member_of
    for email in (_KEEPER_EMAIL, _SUCCESSOR_EMAIL, _MEMBER_EMAIL):
        await principal_store.create(email=email)
    try:
        yield principal_store, keep_store, env
    finally:
        await keep_store.close()
        await key_store.close()
        await principal_store.close()
        await drop_database(env)


async def _member_of_count_out(env: SurrealEnv, keep_bare_id: str) -> int:
    """How many member_of edges have out == the (possibly-deleted) keep (0 on absent table)."""
    connection = await connect_admin(env)
    try:
        try:
            rows = await run(
                connection,
                f"SELECT count() FROM {MEMBER_OF_RELATION} WHERE out = $k GROUP ALL",
                {"k": RecordID(KEEP_TABLE, keep_bare_id)},
            )
        except Exception:  # noqa: BLE001 - an absent table is not the failure under test
            return 0
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            return 0
        return int(rows[0].get("count", 0))
    finally:
        await connection.close()


# =========================================================================== #
# set_keeper — admin set_owner (D1: RENAMED from reassign_keeper). RED at HEAD.
# =========================================================================== #


class TestSetKeeper:
    async def test_set_keeper_updates_the_keeper_to_the_new_principal(
        self, remediation_env: tuple[PrincipalStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD. ``set_keeper`` UPDATEs ``keep.keeper`` to the resolved new
        principal — the keep reads back with the SUCCESSOR as keeper. A build that no-op'd
        (kept the old keeper) or updated the wrong keep reddens on the readback."""
        principal_store, keep_store, _env = remediation_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        successor = await principal_store.get_by_email(_SUCCESSOR_EMAIL)
        assert successor is not None
        await _verb(keep_store, "set_keeper")(keep_id=keep.id, new_keeper_email=_SUCCESSOR_EMAIL)
        after = await keep_store.get_keep(keep.id)
        assert after is not None
        assert after.keeper_id == _bare(successor.id), (
            f"set_keeper must set keep.keeper to the successor {_bare(successor.id)!r}, "
            f"got {after.keeper_id!r}"
        )

    async def test_set_keeper_to_a_ghost_email_is_refused_and_changes_nothing(
        self, remediation_env: tuple[PrincipalStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD (ENFORCED-flavoured guard, §FR-4). A ``record<principal>`` field link
        does NOT validate existence (store-law §2), so the ONLY guard against a ghost keeper
        is the email resolution: an UNKNOWN email is REFUSED (``KeepStoreError``) BEFORE any
        UPDATE, and ``keep.keeper`` is UNCHANGED. FIXTURES-MUST-DISCRIMINATE: paired with the
        success pin above, this distinguishes "refuse a ghost keeper" from "refuse every
        set_keeper"."""
        principal_store, keep_store, _env = remediation_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        keeper = await principal_store.get_by_email(_KEEPER_EMAIL)
        assert keeper is not None
        set_keeper = _verb(keep_store, "set_keeper")
        with pytest.raises(KeepStoreError):
            await set_keeper(keep_id=keep.id, new_keeper_email=_UNKNOWN_EMAIL)
        after = await keep_store.get_keep(keep.id)
        assert after is not None and after.keeper_id == _bare(keeper.id), (
            "a refused set_keeper changed keep.keeper — the refusal must precede the UPDATE"
        )

    async def test_set_keeper_on_a_ghost_keep_is_loud(
        self, remediation_env: tuple[PrincipalStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD (#403 BLOCKER — the adversary's find). The GHOST guard has TWO axes:
        the new-keeper (above) AND the KEEP itself. ``set_keeper`` on a NONEXISTENT keep raises
        ``KeepNotFoundError`` (the D1/FR-3 "ghost keep is LOUD" rider — mirrors ``delete_keep``),
        NOT a silent ``None`` return; and no phantom keep is upserted at the ghost id. The
        new-keeper email is REAL, so the ghost is the KEEP (not the keeper). A build that guards
        only the new-keeper and silently no-ops a typo'd keep passes every other pin — this is
        the pin that catches it. Positive control: ``set_keeper`` on a REAL keep succeeds
        (``test_set_keeper_updates_the_keeper_to_the_new_principal``)."""
        _principal_store, keep_store, _env = remediation_env
        set_keeper = _verb(keep_store, "set_keeper")
        ghost = ghost_id(KEEP_TABLE)
        with pytest.raises(KeepNotFoundError):
            await set_keeper(keep_id=ghost, new_keeper_email=_SUCCESSOR_EMAIL)  # REAL email, GHOST keep
        assert await keep_store.get_keep(ghost) is None, (
            "set_keeper upserted a phantom keep at a ghost id (UPDATE must not create a keep)"
        )

    async def test_after_set_keeper_the_former_keeper_can_be_deleted(
        self, remediation_env: tuple[PrincipalStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD — the remediation actually WORKS (store-level flow). A keeper cannot
        be deleted while keeping (refuse-while-keeping); after setting the keep's keeper to a
        successor, the former keeper keeps nothing and ``PrincipalStore.delete`` PROCEEDS.
        This is the §FR-4 remediation story end-to-end at the store layer."""
        principal_store, keep_store, _env = remediation_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        # Refused while keeping (control that the block is real).
        with pytest.raises(PrincipalStoreError):
            await principal_store.delete(email=_KEEPER_EMAIL)
        # Remediate: set the keeper to the successor, THEN the delete proceeds.
        await _verb(keep_store, "set_keeper")(keep_id=keep.id, new_keeper_email=_SUCCESSOR_EMAIL)
        await principal_store.delete(email=_KEEPER_EMAIL)
        assert await principal_store.get_by_email(_KEEPER_EMAIL) is None, (
            "after setting a new keeper on their keep, the former keeper's delete must proceed"
        )
        # The keep survives under its new keeper (no data loss — the whole point of refuse).
        successor = await principal_store.get_by_email(_SUCCESSOR_EMAIL)
        after = await keep_store.get_keep(keep.id)
        assert after is not None and successor is not None and after.keeper_id == _bare(successor.id)


# =========================================================================== #
# delete_keep — admin delete. RED at HEAD (verb unbuilt).
# ⚠ FORWARD BOUNDARY (D2 ruling, note not a pin): at 61 a keep has no keep-scoped rows,
# so delete_keep = DELETE the keep node (member_of auto-cascades). When 63/64 add
# keep-scoped rows (owner_principal-governed tables), delete_keep MUST revisit the
# keep-scoped-row cascade — this test's "member_of cascade only" scope is a 61 boundary,
# not a permanent contract.
# =========================================================================== #


class TestDeleteKeep:
    async def test_delete_keep_removes_the_keep_and_cascades_its_member_of(
        self, remediation_env: tuple[PrincipalStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD. ``delete_keep`` removes the keep row; its ``member_of`` edges
        auto-cascade on the keep-node (``out``-endpoint) delete (store-law §4 — probed, LEG
        C). Behavioural: after delete_keep, ``get_keep`` is None, ZERO member_of edges point
        at the keep, and the member PRINCIPALS survive (a keep delete must not delete people)."""
        principal_store, keep_store, env = remediation_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        keep_bare = _bare(keep.id)
        assert await _member_of_count_out(env, keep_bare) == 2, "control: keeper + member edges pre-delete"

        await _verb(keep_store, "delete_keep")(keep_id=keep.id)

        assert await keep_store.get_keep(keep.id) is None, "delete_keep did not remove the keep row"
        assert await _member_of_count_out(env, keep_bare) == 0, (
            "delete_keep left dangling member_of edges (store-law §4 auto-cascades a keep-node "
            "delete — if the engine changed, re-derive the delete_keep mechanism)"
        )
        assert await principal_store.get_by_email(_KEEPER_EMAIL) is not None, "delete_keep deleted keeper"
        assert await principal_store.get_by_email(_MEMBER_EMAIL) is not None, "delete_keep deleted member"

    async def test_delete_keep_of_a_ghost_keep_is_loud(
        self, remediation_env: tuple[PrincipalStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD. ⚠ DECISION (ruling SILENT — flagged in the report): a destructive
        admin verb on a typo'd keep id must be LOUD, not a silent no-op — mirroring
        ``remove_household_member``'s FR-3 ghost-keep ``KeepNotFoundError`` and
        ``PrincipalStore.delete``'s ``PrincipalNotFoundError``. So ``delete_keep`` of a keep
        that does not exist raises ``KeepNotFoundError``. (Alternative reading: an idempotent
        no-op like a re-add — REJECTED here for a destructive verb; countermand renames the
        behaviour in one place.)"""
        _principal_store, keep_store, _env = remediation_env
        delete_keep = _verb(keep_store, "delete_keep")
        with pytest.raises(KeepNotFoundError):
            await delete_keep(keep_id=ghost_id(KEEP_TABLE))

    async def test_after_delete_keep_the_former_keeper_can_be_deleted(
        self, remediation_env: tuple[PrincipalStore, KeepStore, SurrealEnv]
    ) -> None:
        """⚠ RED at HEAD — the delete-keep remediation path (store-level flow). A sole-member
        / dm keep's natural remediation is to DELETE it; after that the former keeper keeps
        nothing and ``PrincipalStore.delete`` proceeds."""
        principal_store, keep_store, _env = remediation_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="dm")
        with pytest.raises(PrincipalStoreError):
            await principal_store.delete(email=_KEEPER_EMAIL)
        await _verb(keep_store, "delete_keep")(keep_id=keep.id)
        await principal_store.delete(email=_KEEPER_EMAIL)
        assert await principal_store.get_by_email(_KEEPER_EMAIL) is None, (
            "after deleting their only keep, the former keeper's delete must proceed"
        )
