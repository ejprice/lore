"""Contract — packet 60 wave 1, the ``KeepStore`` CRUD surface.

Written by ``contract-60-w1`` (2026-08-22). The builder builds FROM this; it writes
NO production code. *Every "RED today" claim is scoped to the tree at ``f0ebbf4``:
``loremaster.keeps.KeepStore``'s CRUD verbs are RED STUBS that raise
:class:`NotImplementedError`, so every pin below fails BEHAVIOURALLY — never an
ImportError.*

SPEC: ``docs/design/2026-08-22-packet60-keep-substrate-rulings.md`` — Fork A (keeper is
a ``keep.keeper`` FIELD LINK), Fork B (``create_keep`` fields + closed ``type``), Fork D
(``create_keep`` AUTO-ADDS the keeper to the household at ``rank='contributor'``,
atomically — the load-bearing pin), Fork E (a ``dm`` keep is JUST ``type='dm'`` + a
manually-populated household — NO auto-creation, NO 2-member cap in packet 60), Fork F
(``member_of`` ENFORCED + UNIQUE(in, out); ``add_household`` IDEMPOTENT;
``remove_household`` REFUSES the keeper; ``set_rank`` trivial today). Store law binds
(``docs/reference/surrealdb-31-capabilities.md``): §2 (CONTENT / ``type::record`` / a
missing projection reads NONE), §3 (``create_keep`` writes the keep row + the keeper
edge in ONE ``execute_transaction`` — never a multi-statement ``query()``), §4 (a
graph traversal never indexes — read the edge table as a PLAIN table).

⚠ NO OVER-REACH INTO PACKET 63 (Fork E): this contract pins NO DM auto-creation-on-send,
NO 2-member cap on ``dm`` keeps, NO ``lore_comms`` coupling. A ``dm`` keep here is just
``type='dm'`` + a household the caller populated with ``add_household_member``.

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). NO skip marker — an unreachable store
is a LOUD failure, not a skip.
"""

from __future__ import annotations

import ast
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import loremaster.keeps as keeps_module
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
from loremaster.keeps import (
    Keep,
    KeeperLockoutError,
    KeepNotFoundError,
    KeepStore,
    KeepStoreError,
    Membership,
)
from loremaster.principals import Principal, PrincipalStore
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
)
from loremaster.store.surreal_schema import (
    _KEEP_RANK_CONTRIBUTOR,
    KEEP_TABLE,
    PRINCIPAL_TABLE,
)

_KEEPER_EMAIL = "alice@example.com"
_MEMBER_EMAIL = "bob@example.com"
_MEMBER2_EMAIL = "carol@example.com"
_OUTSIDER_EMAIL = "dave@example.com"
_UNKNOWN_EMAIL = "nobody@example.com"


@pytest_asyncio.fixture()
async def keep_env() -> AsyncIterator[tuple[KeepStore, PrincipalStore, SurrealEnv]]:
    """A ready :class:`KeepStore` + :class:`PrincipalStore` on a fresh unique database,
    with four principals seeded (keeper + two members + an outsider), reaped on exit.

    The ``principal`` table is readied FIRST (it is ``member_of``'s ``IN`` endpoint and
    ``keep``'s ``keeper`` link target), then the keep slice. The ``PrincipalStore`` is
    yielded too so a test can seed further principals. ⚠ At the STUB stage
    ``keep_store.ensure_ready`` applies an EMPTY DDL (``generate_keep_ddl`` emits ``""``),
    so no keep table exists yet — the CRUD verbs raise ``NotImplementedError`` before any
    read, so the RED is behavioural.
    """
    env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    principal_store = PrincipalStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    keep_store = KeepStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await principal_store.ensure_ready()  # principal table (endpoint) FIRST
    await keep_store.ensure_ready()  # keep + member_of
    for email in (_KEEPER_EMAIL, _MEMBER_EMAIL, _MEMBER2_EMAIL, _OUTSIDER_EMAIL):
        await principal_store.create(email=email)
    try:
        yield keep_store, principal_store, env
    finally:
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


async def _count(env: SurrealEnv, table: str, where: str = "", params: dict[str, Any] | None = None) -> int:
    """Raw row count via a fresh admin connection — tolerant of an ABSENT table (a SELECT
    on a not-yet-created table RAISES on 3.2.4), so a pre-build read reports 0 rather than
    erroring for the wrong reason."""
    connection = await connect_admin(env)
    try:
        clause = f" WHERE {where}" if where else ""
        try:
            rows = await run(connection, f"SELECT count() FROM {table}{clause} GROUP ALL", params or {})
        except Exception:  # noqa: BLE001 - an absent table is not the failure under test
            return 0
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            return 0
        return int(rows[0].get("count", 0))
    finally:
        await connection.close()


# =========================================================================== #
# The value objects + typed errors (offline — no store).
# =========================================================================== #


class TestTheValueObjectsAndErrors:
    def test_keep_model_is_frozen_and_forbids_extra(self) -> None:
        keep = Keep(
            id="keep:1",
            keeper_id="alice",
            type="project",
            name="space",
            created_at=datetime.now(UTC),
        )
        with pytest.raises(Exception):  # noqa: B017 - pydantic frozen-instance error
            keep.type = "team"  # type: ignore[misc]
        with pytest.raises(Exception):  # noqa: B017 - pydantic extra="forbid"
            Keep(
                id="keep:1",
                keeper_id="alice",
                type="project",
                name=None,
                created_at=datetime.now(UTC),
                rogue="x",  # type: ignore[call-arg]
            )

    def test_membership_model_is_frozen_and_forbids_extra(self) -> None:
        membership = Membership(
            keep_id="keep:1", member_id="bob", rank="contributor", since=datetime.now(UTC)
        )
        with pytest.raises(Exception):  # noqa: B017 - pydantic frozen-instance error
            membership.rank = "steward"  # type: ignore[misc]

    def test_keep_name_is_optional(self) -> None:
        keep = Keep(id="keep:1", keeper_id="alice", type="dm", name=None, created_at=datetime.now(UTC))
        assert keep.name is None

    def test_error_hierarchy(self) -> None:
        assert issubclass(KeepStoreError, RuntimeError)
        assert issubclass(KeepNotFoundError, KeepStoreError)
        assert issubclass(KeeperLockoutError, KeepStoreError)


# =========================================================================== #
# create_keep — Fork B (shape) + Fork D (the atomic keeper auto-add).
# =========================================================================== #


class TestCreateKeep:
    async def test_create_keep_returns_a_keep_with_the_ruled_shape(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        keep_store, _principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="Q3 launch")
        assert isinstance(keep, Keep)
        assert keep.type == "project"
        assert keep.name == "Q3 launch"
        assert keep.id, "the keep must carry a non-empty id"

    async def test_create_keep_keeper_field_is_the_creator(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """Fork A: the keep's ``keeper`` field equals the resolved creator principal."""
        keep_store, principals, _env = keep_env
        keeper = await principals.get_by_email(_KEEPER_EMAIL)
        assert keeper is not None
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="ops")
        # keeper.id is str(RecordID) (``principal:xyz``); Keep.keeper_id is the bare id.
        assert keep.keeper_id and keep.keeper_id in keeper.id

    async def test_create_keep_AUTO_ADDS_the_keeper_to_the_household_at_contributor(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """⚠ THE LOAD-BEARING FORK-D PIN. After ``create_keep``, BOTH (a) ``keep.keeper``
        equals the creator AND (b) the keeper is IN the household (``member_of`` traversal
        returns the keeper) at ``rank='contributor'`` — in ONE test, so a build that writes
        the FIELD but FORGETS the edge (locking the keeper out of writing their own keep)
        goes RED. Fork D: the keeper's write access rides household membership, so a
        keeper who is not householded cannot write their own keep."""
        keep_store, principals, _env = keep_env
        keeper = await principals.get_by_email(_KEEPER_EMAIL)
        assert keeper is not None
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="atomic")

        # (a) the keeper FIELD is the creator
        assert keep.keeper_id in keeper.id

        # (b) the keeper is IN the household at contributor
        household = await keep_store.list_household(keep.id)
        keeper_memberships = [m for m in household if m.member_id in keeper.id]
        assert len(keeper_memberships) == 1, (
            f"create_keep did not auto-add the keeper to the household — keeper lockout (Fork D). "
            f"household={household!r}"
        )
        assert keeper_memberships[0].rank == _KEEP_RANK_CONTRIBUTOR

    async def test_create_keep_of_type_dm_produces_a_dm_keep(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """Fork E boundary: a ``dm`` keep is JUST ``type='dm'`` — no auto-creation, no
        2-member cap. This contract pins only that the substrate holds ``type='dm'``; the
        automatic wire is packet 63."""
        keep_store, _principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="dm")
        assert keep.type == "dm"
        assert keep.name is None, "a dm keep created with no name carries name=None"

    async def test_a_REJECTED_create_keep_leaves_NO_keep_row(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """Atomicity, the CREATE-failure path: a create with an unruled ``type`` is
        rejected by the store-side ASSERT and rolls the whole transaction back — no keep
        row, no keeper edge. (One ``execute_transaction`` — store §3.)"""
        keep_store, _principals, env = keep_env
        before = await _count(env, KEEP_TABLE)
        # FR-2 Q2b: the unruled-type rejection is a raw engine SurrealStoreError that KeepStore
        # must WRAP as KeepStoreError (consumer-law parity with PrincipalStore.create). Asserting
        # the TYPED KeepStoreError — not a bare Exception — is what stops this pin certifying the
        # corpse: a bare-Exception catch stays green whether KeepStore wraps or leaks raw. RED
        # against the wave-1 (unwrapped) keeps.py, which leaks the raw SurrealStoreError.
        with pytest.raises(KeepStoreError):
            await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="workspace")
        assert await _count(env, KEEP_TABLE) == before, "a rejected create_keep left a keep row behind"

    async def test_create_keep_is_ATOMIC_a_failed_keeper_edge_leaves_NO_keep_row(
        self,
        keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """⛔ Atomicity, the RELATE-failure path — the two-transaction wrong build. The
        keeper email is made to resolve to a GHOST principal id (via the COMPOSED
        ``PrincipalStore.get_by_email`` the brief mandates create_keep use), so the keep
        CREATE succeeds (a ``record<principal>`` link does NOT validate existence, store
        §4) but the keeper's ``member_of`` RELATE is REFUSED by ENFORCED (the ghost IN
        endpoint). If CREATE and RELATE ride ONE ``execute_transaction`` the CREATE rolls
        back → NO keep row → GREEN; a build issuing the RELATE in a SEPARATE ``_query``
        leaves an orphan keep → RED.

        ⚠ BUILD-DEPENDENCY: this pin assumes create_keep resolves the keeper email
        through the composed ``self._principals.get_by_email`` (the ``PrincipalKeyStore``
        precedent the brief cites). If the builder resolves differently, the injection
        seam must move — see REPORT-contract-60-w1.md.
        """
        keep_store, _principals, env = keep_env
        ghost_principal_id = f"{PRINCIPAL_TABLE}:{ghost_id('ghost_keeper')}"
        fake = Principal(
            id=ghost_principal_id,
            email=_KEEPER_EMAIL,
            subject=None,
            display_name=None,
            status="active",
            role="member",
            expires_at=None,
            created_at=datetime.now(UTC),
        )

        async def _ghost_get_by_email(email: str) -> Principal | None:
            return fake

        monkeypatch.setattr(keep_store._principals, "get_by_email", _ghost_get_by_email)

        before = await _count(env, KEEP_TABLE)
        # FR-2 Q2b: the ENFORCED ghost-keeper-edge refusal is a raw engine SurrealStoreError that
        # KeepStore must WRAP as KeepStoreError (consumer-law parity). Typed, not a bare Exception,
        # so the pin does not certify the corpse. RED against the unwrapped wave-1 keeps.py.
        with pytest.raises(KeepStoreError):
            await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="atom")
        assert await _count(env, KEEP_TABLE) == before, (
            "a create_keep whose keeper member_of RELATE was refused left a keep row behind — "
            "the CREATE and the RELATE must ride ONE execute_transaction (store §3)"
        )

    async def test_create_keep_with_an_unknown_keeper_email_raises(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        keep_store, _principals, _env = keep_env
        with pytest.raises(KeepStoreError):
            await keep_store.create_keep(keeper_email=_UNKNOWN_EMAIL, type="project", name="x")


class TestGetKeep:
    async def test_get_keep_reads_back_a_created_keep(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        keep_store, _principals, _env = keep_env
        created = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="findme")
        fetched = await keep_store.get_keep(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.type == "project"
        assert fetched.name == "findme"

    async def test_get_keep_reads_back_a_NAMELESS_keep(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """⚠ store-law §2 (the ``SELECT *`` NONE-column trap — the missing pin, adversary
        attack 9). A ``dm`` keep is ALWAYS nameless (``name=None`` — Fork E; the reason
        ``name`` is ``option<>``). ``get_keep`` must round-trip ``name=None`` through a
        FRESH store read — not by echoing ``create_keep``'s own return object. A ``get_keep``
        that reads ``SELECT *`` and maps the name by BRACKET access (``row["name"]``)
        ``KeyError``s here, because ``SELECT *`` OMITS a NONE-valued column ENTIRELY (store
        §2, verbatim), and the always-nameless ``dm`` type makes that a 100%-broken read for
        a first-class keep type. The correct build uses an explicit projection (or
        ``.get("name")``), so ``name=None`` comes back as ``Keep.name is None``.

        Reads through ``get_keep`` (a FRESH store read), never ``create_keep``'s return, so
        a build that echoes the returned object correctly but reads back wrongly is still
        caught (the discrimination the pin exists for)."""
        keep_store, _principals, _env = keep_env
        nameless = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="dm")
        named = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="has a name")

        # The NAMELESS keep round-trips as name=None through a FRESH read (the bug site).
        fetched_nameless = await keep_store.get_keep(nameless.id)
        assert fetched_nameless is not None, "get_keep returned None for a freshly-created nameless keep"
        assert fetched_nameless.type == "dm"
        assert fetched_nameless.name is None, (
            "get_keep did not round-trip a nameless keep's name as None — a `SELECT *` + bracket "
            "read KeyErrors on the omitted NONE column (store §2); use an explicit projection"
        )

        # POSITIVE CONTROL: a NAMED keep read back through the SAME verb carries its name, so
        # the assertion above is not vacuously true of a verb that always returns name=None.
        fetched_named = await keep_store.get_keep(named.id)
        assert fetched_named is not None
        assert fetched_named.name == "has a name", (
            "the positive control failed — get_keep must read a real name back, not always None"
        )

    async def test_get_keep_of_an_unknown_id_returns_none(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        keep_store, _principals, _env = keep_env
        missing = await keep_store.get_keep(f"{KEEP_TABLE}:{ghost_id('missing')}")
        assert missing is None


# =========================================================================== #
# add_household_member — Fork F: idempotent, dedupe-before-RELATE.
# =========================================================================== #


class TestAddHouseholdMember:
    async def test_add_household_member_returns_a_membership(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        keep_store, principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        member = await principals.get_by_email(_MEMBER_EMAIL)
        assert member is not None
        membership = await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        assert isinstance(membership, Membership)
        assert membership.member_id in member.id
        assert membership.rank == _KEEP_RANK_CONTRIBUTOR

    async def test_add_household_member_is_IDEMPOTENT_a_re_add_is_a_benign_no_op(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """⚠ Fork F: re-adding an existing member is a BENIGN no-op (check-first or catch
        the UNIQUE(in, out) backstop), NEVER an error to the caller — and it leaves EXACTLY
        ONE edge, not two. A build that let the UNIQUE ERR escape, or wrote a second edge,
        goes RED."""
        keep_store, principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="idem")
        member = await principals.get_by_email(_MEMBER_EMAIL)
        assert member is not None
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        # The re-add must NOT raise.
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        household = await keep_store.list_household(keep.id)
        member_edges = [m for m in household if m.member_id in member.id]
        assert len(member_edges) == 1, (
            f"a re-add wrote a SECOND member_of edge (or raised) — it must be a benign no-op "
            f"leaving exactly one edge. member edges={member_edges!r}"
        )

    async def test_add_two_DIFFERENT_members_positive_control(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """The control the idempotency pin needs: two DIFFERENT members BOTH land (so the
        idempotency pin's 'exactly one edge' is not just 'the store only ever writes one
        edge'). Uses ≥2 members so ``len()`` and the real count differ."""
        keep_store, _principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="two")
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER2_EMAIL)
        household = await keep_store.list_household(keep.id)
        member_ids = {m.member_id for m in household}
        # keeper + two members = three distinct members.
        assert len(member_ids) == 3, f"expected keeper + 2 members = 3 distinct members: {household!r}"

    async def test_add_household_member_with_an_unknown_email_raises(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        keep_store, _principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="x")
        with pytest.raises(KeepStoreError):
            await keep_store.add_household_member(keep_id=keep.id, member_email=_UNKNOWN_EMAIL)


# =========================================================================== #
# remove_household_member — Fork F rider: the keeper-lockout guard.
# =========================================================================== #


class TestRemoveHouseholdMember:
    async def test_remove_a_non_keeper_member_deletes_the_edge(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        keep_store, principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="crew")
        member = await principals.get_by_email(_MEMBER_EMAIL)
        assert member is not None
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        await keep_store.remove_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        household = await keep_store.list_household(keep.id)
        assert not any(m.member_id in member.id for m in household), (
            f"the removed member is still in the household: {household!r}"
        )

    async def test_remove_household_REFUSES_to_remove_the_KEEPER(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """⚠ Fork F rider (load-bearing): removing the keeper from the household would lock
        the keeper out of writing their own keep (undoing Fork D). ``remove_household_member``
        REFUSES it with a typed :class:`KeeperLockoutError`. Positive control provided by
        the non-keeper removal above (a legal removal succeeds)."""
        keep_store, _principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="locked")
        with pytest.raises(KeeperLockoutError):
            await keep_store.remove_household_member(keep_id=keep.id, member_email=_KEEPER_EMAIL)
        # The keeper is STILL in the household (the refusal changed nothing).
        keeper_still_present = await keep_store.list_household(keep.id)
        assert keeper_still_present, "the keeper was removed despite the refusal"


# =========================================================================== #
# set_rank — Fork F rider: a trivial seam today (one legal value).
# =========================================================================== #


class TestSetRank:
    async def test_set_rank_to_contributor_returns_the_membership(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """Fork F rider: ``set_rank`` UPDATEs the edge's ``rank`` field. TRIVIAL today —
        the only legal value is ``'contributor'``, so this exercises the seam without
        gating 60 on multi-rank behaviour (the real test lands with the rank widening)."""
        keep_store, principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="rank")
        member = await principals.get_by_email(_MEMBER_EMAIL)
        assert member is not None
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        membership = await keep_store.set_rank(
            keep_id=keep.id, member_email=_MEMBER_EMAIL, rank=_KEEP_RANK_CONTRIBUTOR
        )
        assert isinstance(membership, Membership)
        assert membership.rank == _KEEP_RANK_CONTRIBUTOR
        assert membership.member_id in member.id


# =========================================================================== #
# list_household / list_keeps_for_keeper — the read surface (store §4: read the edge
# table as a PLAIN table / the keeper index, never an arrow traversal).
# =========================================================================== #


class TestListHousehold:
    async def test_list_household_returns_every_member(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """≥2 added members + the auto-added keeper, so a build that returned a truncated
        or single-member list is caught (small-N discrimination)."""
        keep_store, _principals, _env = keep_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="household")
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER2_EMAIL)
        household = await keep_store.list_household(keep.id)
        assert all(isinstance(m, Membership) for m in household)
        assert len({m.member_id for m in household}) == 3, (
            f"expected the keeper + 2 members = 3 memberships: {household!r}"
        )

    async def test_list_household_of_a_DIFFERENT_keep_does_not_bleed(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """Discrimination: a member of keep A must not appear in keep B's household — a
        build that read ALL member_of edges (not scoped by ``out = $keep``) is caught."""
        keep_store, principals, _env = keep_env
        keep_a = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="A")
        keep_b = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="B")
        await keep_store.add_household_member(keep_id=keep_a.id, member_email=_MEMBER_EMAIL)
        member = await principals.get_by_email(_MEMBER_EMAIL)
        assert member is not None
        household_b = await keep_store.list_household(keep_b.id)
        assert not any(m.member_id in member.id for m in household_b), (
            f"keep A's member bled into keep B's household: {household_b!r}"
        )


class TestListKeepsForKeeper:
    async def test_list_keeps_for_keeper_returns_their_keeps(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """≥2 keeps for one keeper, so a build returning a single keep is caught."""
        keep_store, _principals, _env = keep_env
        first = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="one")
        second = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="two")
        keeps = await keep_store.list_keeps_for_keeper(_KEEPER_EMAIL)
        ids = {keep.id for keep in keeps}
        assert {first.id, second.id} <= ids, f"the keeper's two keeps were not both listed: {keeps!r}"

    async def test_list_keeps_for_keeper_lists_a_NAMELESS_keep(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """⚠ store-law §2 mirror for the LIST verb (adversary attack 9). A keeper who keeps
        a nameless (``dm``) keep alongside a named one: ``list_keeps_for_keeper`` must return
        the nameless keep with ``name is None`` and must NOT raise. A ``SELECT *`` + bracket
        ``row["name"]`` read ``KeyError``s on the nameless row and takes the WHOLE listing
        down with it. The named keep in the SAME listing is the positive control (the verb
        reads real names back, so the nameless assertion is non-vacuous)."""
        keep_store, _principals, _env = keep_env
        nameless = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="dm")
        named = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="named one")
        keeps = await keep_store.list_keeps_for_keeper(_KEEPER_EMAIL)
        by_id = {keep.id: keep for keep in keeps}
        assert nameless.id in by_id, f"the keeper's nameless keep was not listed: {keeps!r}"
        assert by_id[nameless.id].name is None, (
            "list_keeps_for_keeper did not round-trip the nameless keep's name as None — a "
            "`SELECT *` + bracket read KeyErrors on the omitted NONE column (store §2)"
        )
        # POSITIVE CONTROL: the named keep in the same listing carries its name.
        assert named.id in by_id, "the keeper's named keep was not listed"
        assert by_id[named.id].name == "named one", (
            "the positive control failed — list_keeps_for_keeper must read a real name back"
        )

    async def test_list_keeps_for_keeper_excludes_ANOTHER_keepers_keeps(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """Discrimination (the keeper index / ``WHERE keeper = $p``): a keep kept by a
        DIFFERENT principal must not be listed for this keeper."""
        keep_store, _principals, _env = keep_env
        mine = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="mine")
        theirs = await keep_store.create_keep(keeper_email=_OUTSIDER_EMAIL, type="project", name="theirs")
        keeps = await keep_store.list_keeps_for_keeper(_KEEPER_EMAIL)
        ids = {keep.id for keep in keeps}
        assert mine.id in ids, "the keeper's own keep was not listed"
        assert theirs.id not in ids, "another keeper's keep leaked into this keeper's listing"


# =========================================================================== #
# Shared-seam reuse (#102/#120) — proven at the store level.
# =========================================================================== #


class TestTheStoreReusesTheSharedSeams:
    """The store hand-rolls NO retry/classification of its own — every read/write routes
    through the ONE shared ``run_query`` seam via ``_query`` (auto-discovered by
    ``test_retry_seam.py``'s scan, which is where the shared retry/backoff/exhaustion
    pins prove the sharing by mutation). This file pins the LOCAL structural facts."""

    def test_the_store_exposes_a__query_seam_named_exactly_query(self) -> None:
        """``test_retry_seam.py`` scans for a method named EXACTLY ``_query``; a differently
        named seam would silently escape the shared-retry mutation pins (the ``scout.py``
        defeat, CLAUDE.md instrument lesson)."""
        assert hasattr(KeepStore, "_query"), "KeepStore must expose a `_query` seam (test_retry_seam scan)"

    async def test_the_store_composes_a_principal_store_for_email_resolution(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """ONE IMPLEMENTATION: email→id resolution reuses the OWNED
        ``PrincipalStore.get_by_email`` (a composed ``PrincipalStore``), never a cloned
        resolver (the ``PrincipalKeyStore._require_principal_id`` precedent)."""
        keep_store, _principals, _env = keep_env
        assert isinstance(getattr(keep_store, "_principals", None), PrincipalStore), (
            "KeepStore must COMPOSE a PrincipalStore for keeper/member email resolution"
        )


# =========================================================================== #
# FR-2 Q2b — KeepStore WRAPS raw engine rejections as KeepStoreError at every write
# boundary (consumer law; the PrincipalStore.create parity — store ref §3, _txn.py:116-183).
# SurrealConnectionError / TxnContentionExhaustedError (both SUBCLASS SurrealStoreError,
# _txn.py:120/156) PASS THROUGH untouched for the retry/lifecycle layer. The write-path SET
# is DERIVED from production truth (reach law #344/#345), never a hand-list, so a NEW unwrapped
# write method reddens the coverage pin.
# =========================================================================== #

_MUTATING_STATEMENT_KEYWORDS = frozenset(
    {"CREATE", "RELATE", "UPDATE", "DELETE", "INSERT", "UPSERT"}
)

# The KeepStore READ verbs — the positive control proving the derivation DISCRIMINATES writes
# from reads (a derivation that returned "all public async methods" would fail the reach pin).
_KEEPSTORE_READ_METHODS = frozenset({"get_keep", "list_household", "list_keeps_for_keeper"})


def _method_has_mutating_statement(method: ast.AsyncFunctionDef) -> bool:
    """True iff ``method``'s OWN body (docstring excluded) contains a string literal whose
    first whitespace-delimited token is a mutating SurrealQL keyword.

    The whole-word check (``tokens[0] in ...``) stops an error message like
    ``"created keep … did not read back"`` from false-matching ``CREATE``; dropping the
    docstring stops method prose (``"Create a keep …"``) from doing the same. f-string literal
    parts are ``ast.Constant`` nodes under a ``JoinedStr``, so ``ast.walk`` reaches the
    ``CREATE …`` / ``RELATE …`` fragments a mutation statement is built from."""
    statements = method.body
    if (
        statements
        and isinstance(statements[0], ast.Expr)
        and isinstance(statements[0].value, ast.Constant)
        and isinstance(statements[0].value.value, str)
    ):
        statements = statements[1:]  # drop the docstring so its prose cannot false-match
    for statement in statements:
        for node in ast.walk(statement):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                tokens = node.value.strip().upper().split()
                if tokens and tokens[0] in _MUTATING_STATEMENT_KEYWORDS:
                    return True
    return False


def _derive_keepstore_write_paths() -> set[str]:
    """DERIVE the KeepStore public write-method set from production truth (reach law
    #344/#345) — a public ``async def`` whose own body carries a mutating SurrealQL statement
    literal (CREATE/RELATE/UPDATE/DELETE/INSERT/UPSERT).

    Read verbs (only ``SELECT``) are excluded; ``ensure_ready`` applies GENERATED DDL
    (``generate_keep_ddl()`` — no literal mutating statement in its body) and is excluded as
    bootstrap, not a CRUD write (the CLI dispatch catches its ``SurrealStoreError`` on its own
    branch). ⚠ Bound (stated per the reach law's honesty requirement): this detects a mutating
    statement LITERAL in the public method's OWN body; a future write verb routing its mutation
    entirely through a PRIVATE helper (no literal in the public body) escapes this scan —
    re-open trigger: the first KeepStore write verb that delegates its mutation to a private
    helper."""
    source = Path(keeps_module.__file__).read_text(encoding="utf-8")
    keepstore = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ClassDef) and node.name == "KeepStore"
    )
    return {
        method.name
        for method in keepstore.body
        if isinstance(method, ast.AsyncFunctionDef)
        and not method.name.startswith("_")
        and _method_has_mutating_statement(method)
    }


_WRITE_PATHS = _derive_keepstore_write_paths()

# A ghost keep id (its OUT endpoint does not exist) — under fault injection the patched seam
# raises before the id is used, so any well-formed id serves.
_WRAP_PROBE_GHOST_KEEP = f"{KEEP_TABLE}:{ghost_id('wrap_probe_keep')}"

# One invocation per DERIVED write path — the HANDLED set the reach pin checks the derived set
# against. A new write path grows ``_WRITE_PATHS`` but not this map → the reach pin reds
# (coverage-as-checked-variable). Every invocation resolves a SEEDED principal email (via the
# composed PrincipalStore, whose ``principals``-module ``run_query`` is NOT patched), so under
# fault injection resolution succeeds and the patched KeepStore seam is what raises.
_WRITE_PATH_INVOCATIONS: dict[str, Callable[[KeepStore], Awaitable[object]]] = {
    "create_keep": lambda store: store.create_keep(
        keeper_email=_KEEPER_EMAIL, type="project", name="wrap"
    ),
    "add_household_member": lambda store: store.add_household_member(
        keep_id=_WRAP_PROBE_GHOST_KEEP, member_email=_MEMBER_EMAIL
    ),
    "remove_household_member": lambda store: store.remove_household_member(
        keep_id=_WRAP_PROBE_GHOST_KEEP, member_email=_MEMBER_EMAIL
    ),
    "set_rank": lambda store: store.set_rank(
        keep_id=_WRAP_PROBE_GHOST_KEEP, member_email=_MEMBER_EMAIL, rank=_KEEP_RANK_CONTRIBUTOR
    ),
}


class TestKeepStoreWrapsEngineRejections:
    """FR-2 Q2b: every KeepStore WRITE boundary wraps a raw engine ``SurrealStoreError`` as
    ``KeepStoreError`` (consumer law — a consumer never sees a raw engine error), while
    ``SurrealConnectionError`` / ``TxnContentionExhaustedError`` PASS THROUGH untouched for the
    retry/lifecycle layer (store ref §3; the ``PrincipalStore.create`` precedent —
    ``except (SurrealConnectionError, TxnContentionExhaustedError): raise`` BEFORE
    ``except SurrealStoreError``). RED against the wave-1 (unwrapped) keeps.py at ``efccdc8``."""

    def test_the_derived_write_path_set_matches_the_coverage_map(self) -> None:
        """REACH PIN (#344/#345): the write-path set is DERIVED from keeps.py (not a hand-list)
        and must equal the fault-injection coverage map — so a NEW write method grows the derived
        set, fails this equality, and forces a coverage entry (the observed set cannot silently
        lag production truth). Positive control: the derivation EXCLUDES the read verbs (a
        derivation returning all public methods would fail this)."""
        assert _WRITE_PATHS, "the derived KeepStore write-path set is empty — the AST scan broke"
        assert _WRITE_PATHS == set(_WRITE_PATH_INVOCATIONS), (
            "the DERIVED KeepStore write-path set has drifted from the fault-injection coverage "
            "map — a new write path must add a coverage entry (reach law #344/#345). "
            f"derived={sorted(_WRITE_PATHS)!r} mapped={sorted(_WRITE_PATH_INVOCATIONS)!r}"
        )
        assert _KEEPSTORE_READ_METHODS.isdisjoint(_WRITE_PATHS), (
            "the derivation misclassified a READ verb as a write path: "
            f"{sorted(_KEEPSTORE_READ_METHODS & _WRITE_PATHS)!r}"
        )

    @pytest.mark.parametrize("method_name", sorted(_WRITE_PATHS))
    async def test_each_write_path_wraps_engine_rejection_as_KeepStoreError(
        self,
        keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        method_name: str,
    ) -> None:
        """COVERAGE (fault injection over the DERIVED set): when the engine seam raises a raw
        ``SurrealStoreError``, EACH write path surfaces ``KeepStoreError`` — never the raw engine
        error. Injecting at the shared ``keeps.run_query`` / ``keeps.execute_transaction`` seams
        proves the WHOLE verb wraps (including a read inside a write verb — e.g.
        ``remove_household_member``'s internal ``get_keep``), which is how
        ``remove_household_member`` (whose DELETE cannot naturally reject) gets its coverage. RED
        against the unwrapped wave-1 keeps.py (a raw ``SurrealStoreError`` escapes
        ``pytest.raises(KeepStoreError)``); patching only the ``keeps``-module seams leaves the
        COMPOSED ``PrincipalStore``'s ``principals``-module ``run_query`` intact, so email
        resolution still succeeds and the WRITE seam is what raises."""
        keep_store, _principals, _env = keep_env
        invoke = _WRITE_PATH_INVOCATIONS.get(method_name)
        assert invoke is not None, (
            f"new KeepStore write path {method_name!r} has no fault-injection invocation — add one "
            "to _WRITE_PATH_INVOCATIONS (reach law #344/#345)"
        )

        async def _raise_store_error(*args: object, **kwargs: object) -> object:
            raise SurrealStoreError(f"injected engine rejection ({method_name})")

        monkeypatch.setattr(keeps_module, "run_query", _raise_store_error)
        monkeypatch.setattr(keeps_module, "execute_transaction", _raise_store_error)
        with pytest.raises(KeepStoreError):
            await invoke(keep_store)

    @pytest.mark.parametrize("transport_error", ["connection", "contention"])
    @pytest.mark.parametrize("method_name", sorted(_WRITE_PATHS))
    async def test_each_write_path_propagates_transport_faults_untouched(
        self,
        keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        method_name: str,
        transport_error: str,
    ) -> None:
        """PASS-THROUGH / DISCRIMINATOR: a ``SurrealConnectionError`` (transport) or
        ``TxnContentionExhaustedError`` (exhausted retry) raised at the seam PROPAGATES untouched
        — it must NOT be masked as a domain ``KeepStoreError`` (store ref §3: it belongs to the
        retry/lifecycle layer). GREEN today (the unwrapped keeps.py propagates it) AND after the
        correct fix; it REDS only against the WRONG fix — a naive ``except SurrealStoreError:
        raise KeepStoreError`` that omits the ``except (SurrealConnectionError,
        TxnContentionExhaustedError): raise`` re-raise FIRST (both subclass ``SurrealStoreError``,
        _txn.py:120/156). This is the discriminator the coverage pin above cannot see — without
        it, a catch-all wrong build passes the whole wrap contract."""
        keep_store, _principals, _env = keep_env
        invoke = _WRITE_PATH_INVOCATIONS.get(method_name)
        assert invoke is not None, (
            f"new KeepStore write path {method_name!r} has no fault-injection invocation (reach law)"
        )
        expected: type[SurrealStoreError]
        error_instance: SurrealStoreError
        if transport_error == "connection":
            expected = SurrealConnectionError
            error_instance = SurrealConnectionError("injected transport fault")
        else:
            expected = TxnContentionExhaustedError
            error_instance = TxnContentionExhaustedError(
                "injected exhausted contention", attempts=8, elapsed_seconds=1.0
            )

        async def _raise_transport_error(*args: object, **kwargs: object) -> object:
            raise error_instance

        monkeypatch.setattr(keeps_module, "run_query", _raise_transport_error)
        monkeypatch.setattr(keeps_module, "execute_transaction", _raise_transport_error)
        with pytest.raises(expected):
            await invoke(keep_store)

    async def test_add_household_member_wraps_a_ghost_keep_engine_rejection(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """BEHAVIOURAL (a REAL engine rejection): add-household to a GHOST keep is refused by the
        ENFORCED ``member_of`` edge (the ghost OUT endpoint does not exist — store ref §4) — a
        raw ``SurrealStoreError`` KeepStore must WRAP as ``KeepStoreError``. RED against the
        unwrapped wave-1 keeps.py, which leaks the raw error."""
        keep_store, _principals, _env = keep_env
        ghost_keep = f"{KEEP_TABLE}:{ghost_id('behavioural_ghost_keep')}"
        with pytest.raises(KeepStoreError):
            await keep_store.add_household_member(keep_id=ghost_keep, member_email=_MEMBER_EMAIL)

    async def test_set_rank_wraps_an_unruled_rank_engine_rejection(
        self, keep_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """BEHAVIOURAL (a REAL engine rejection): set-rank to an UNRULED rank is refused by the
        rank ASSERT (store-side closed domain — design Fork C) — a raw ``SurrealStoreError``
        KeepStore must WRAP as ``KeepStoreError``. The member is a real household member first, so
        the UPDATE matches a row and the ASSERT fires (an UPDATE matching no row would no-op).
        RED against the unwrapped wave-1 keeps.py."""
        keep_store, _principals, _env = keep_env
        keep = await keep_store.create_keep(
            keeper_email=_KEEPER_EMAIL, type="project", name="rankwrap"
        )
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)
        with pytest.raises(KeepStoreError):
            await keep_store.set_rank(keep_id=keep.id, member_email=_MEMBER_EMAIL, rank="tyrant")
