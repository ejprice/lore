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

from collections.abc import AsyncIterator
from datetime import UTC, datetime
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
from loremaster.keeps import (
    Keep,
    KeeperLockoutError,
    KeepNotFoundError,
    KeepStore,
    KeepStoreError,
    Membership,
)
from loremaster.principals import Principal, PrincipalStore
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
        with pytest.raises(Exception) as caught:  # noqa: B017 - store rejection of the unruled type
            await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="workspace")
        assert not isinstance(caught.value, NotImplementedError), (
            "create_keep is still a STUB — the rejection must come from the store's type ASSERT, "
            "not from an unbuilt method (RED-by-design until the builder lands create_keep)"
        )
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
        with pytest.raises(Exception) as caught:  # noqa: B017 - ENFORCED refuses the ghost keeper edge
            await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="atom")
        assert not isinstance(caught.value, NotImplementedError), (
            "create_keep is still a STUB — the refusal must come from the ENFORCED member_of edge, "
            "not from an unbuilt method (RED-by-design until the builder lands create_keep)"
        )
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
