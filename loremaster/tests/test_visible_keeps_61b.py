"""CONTRACT (contract-61b-w2, Fork B/D) — the visible-Keeps RESOLVER shell.

``resolve_visible_keeps`` is the thin ``loremaster`` shell (design
``2026-08-22-packet61-pdp-audit-rulings.md`` Fork B/F) that turns a member's household
membership into the PDP's ``Subject.visible_keep_ids`` — the ``keep:<id>`` scope set the
pure ``lorerunes`` PDP (``authorize_filter`` / ``ScopeInKeeps``) consumes:

    async def resolve_visible_keeps(keep_store, *, member_email) -> frozenset[str]

It reads the keeps whose household the member is in (``KeepStore.list_keeps_for_member`` —
Fork F, ``test_keeps_store.py``) and maps each keep id → its ``keep:<id>`` scope string via
the SHIPPED ``lorerunes.pdp.keep_scope`` helper (the ONE spelling — the PDP and the resolver
MUST agree on the scope value, so the resolver never hand-rolls ``f"keep:{k}"``; that is the
ROUTING-IS-NOT-SHARING trap, #102). The store READ lives in ``loremaster`` (Fork B: the pure
core stays store-free); the mapping is pure string work over the shared helper.

⚠ RED at HEAD: ``loremaster.visible_keeps`` does not exist → ImportError (every node here
RED via collection error). The builder creates the module + the resolver; the satisfiability
receipt (``REPORT-contract-61b-w2.md``) proves a known-correct build greens them.

⚠ Home flag (surfaced per brief-base §2): this contract imports the resolver from
``loremaster.visible_keeps`` (a NEW dedicated module — the cleanest split: a store-touching
shell that packet 62 will import to build the full ``Subject``). ``loremaster.auth`` (request-
auth primitives) is a plausible alternative home. The contract pins BEHAVIOUR; only this
import path couples to placement. Low-stakes — the lead/builder may relocate it, updating this
import. It is NOT ``lorerunes`` API (it calls ``KeepStore``), so no ``registration_sites.py``
run is owed by w2.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.keeps import KeepStore, KeepStoreError
from loremaster.principals import PrincipalStore

# RED at HEAD: this symbol does not exist yet (the whole file fails to collect until the
# builder lands loremaster.visible_keeps.resolve_visible_keeps).
from loremaster.visible_keeps import resolve_visible_keeps
from lorerunes.pdp import (
    KEEP_SCOPE_PREFIX,
    PRINCIPAL_ROLE_MEMBER,
    SCOPE_SERVER,
    Action,
    Resource,
    Subject,
    authorize,
    keep_scope,
)

from lorerunes import pdp

_KEEPER_EMAIL = "alice@example.com"
_MEMBER_EMAIL = "bob@example.com"
_MEMBER2_EMAIL = "carol@example.com"
_UNKNOWN_EMAIL = "nobody@example.com"


@pytest_asyncio.fixture()
async def resolver_env() -> AsyncIterator[tuple[KeepStore, PrincipalStore, SurrealEnv]]:
    """A ready KeepStore + PrincipalStore on a fresh unique database with three principals
    seeded (mirrors ``test_keeps_store.py::keep_env`` — the ``principal`` table readied FIRST
    as ``member_of``'s IN endpoint + ``keep``'s ``keeper`` target)."""
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
    await principal_store.ensure_ready()
    await keep_store.ensure_ready()
    for email in (_KEEPER_EMAIL, _MEMBER_EMAIL, _MEMBER2_EMAIL):
        await principal_store.create(email=email)
    try:
        yield keep_store, principal_store, env
    finally:
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


class TestResolveVisibleKeepsShapeAndMapping:
    """The pure mapping contract: the resolver produces the ``keep:<id>`` scope frozenset the
    PDP consumes, via the shipped ``keep_scope`` helper (ONE spelling)."""

    async def test_returns_a_frozenset_of_keep_scope_strings(
        self, resolver_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """A member of ≥2 keeps → a FROZENSET (immutable — it feeds the frozen ``Subject``) of
        exactly the ``keep:<id>`` scopes for those keeps. ≥2 keeps = small-N discrimination
        (a build returning one scope is caught)."""
        keep_store, _principals, _env = resolver_env
        keep_a = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="A")
        keep_b = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="team", name="B")
        await keep_store.add_household_member(keep_id=keep_a.id, member_email=_MEMBER_EMAIL)
        await keep_store.add_household_member(keep_id=keep_b.id, member_email=_MEMBER_EMAIL)

        scopes = await resolve_visible_keeps(keep_store, member_email=_MEMBER_EMAIL)

        assert isinstance(scopes, frozenset), (
            f"resolve_visible_keeps must return a frozenset (it feeds the frozen Subject): "
            f"{type(scopes)!r}"
        )
        expected = {
            keep_scope(KeepStore._record_id_part(keep_a.id)),
            keep_scope(KeepStore._record_id_part(keep_b.id)),
        }
        assert scopes == expected, (
            f"the resolver must map each visible keep id → its keep:<id> scope: "
            f"got {scopes!r}, expected {expected!r}"
        )

    async def test_every_scope_is_a_valid_non_double_prefixed_keep_scope(
        self, resolver_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """Each produced scope starts with EXACTLY one ``keep:`` prefix (never ``keep:keep:…``
        — the double-prefix bug if the resolver fed ``keep_scope`` a ``str(RecordID)`` instead
        of a bare id) and is accepted by the PDP's scope domain."""
        keep_store, _principals, _env = resolver_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="P")
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)

        scopes = await resolve_visible_keeps(keep_store, member_email=_MEMBER_EMAIL)

        assert scopes, "the member is in one keep — the resolved set must be non-empty"
        for scope in scopes:
            assert scope.startswith(KEEP_SCOPE_PREFIX), f"{scope!r} is not a keep scope"
            remainder = scope[len(KEEP_SCOPE_PREFIX) :]
            assert remainder and not remainder.startswith(KEEP_SCOPE_PREFIX), (
                f"double-prefixed keep scope {scope!r} — the resolver fed keep_scope a "
                f"str(RecordID) ('keep:xyz') instead of a bare id ('xyz')"
            )
            # The scope must be a valid Resource scope (round-trips through the PDP domain).
            Resource(table="memory", owner_principal=None, owner_agent=None, scope=scope)

    async def test_a_member_of_no_keep_resolves_to_the_empty_frozenset(
        self, resolver_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """carol is in no keep → ``frozenset()`` (never None, never an error) — the empty
        ``$my_keep_scopes`` the PDP's ``ScopeInKeeps`` handles as ``false``."""
        keep_store, _principals, _env = resolver_env
        scopes = await resolve_visible_keeps(keep_store, member_email=_MEMBER2_EMAIL)
        assert scopes == frozenset(), f"a member of no keep must resolve to the empty set: {scopes!r}"

    async def test_an_unknown_member_email_raises_KeepStoreError(
        self, resolver_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """An unresolvable email surfaces the domain ``KeepStoreError`` (propagated from
        ``list_keeps_for_member``), never a raw engine error and never an empty set (an empty
        visible-keep set for a typo'd identity would silently under-authorize — feeding the
        PDP a smaller-than-true $my_keeps is a fail-closed-but-wrong confused-deputy risk)."""
        keep_store, _principals, _env = resolver_env
        with pytest.raises(KeepStoreError):
            await resolve_visible_keeps(keep_store, member_email=_UNKNOWN_EMAIL)


class TestResolveVisibleKeepsRoutesThroughTheSharedKeepScopeHelper:
    """ONE IMPLEMENTATION / prove-by-mutation (#102, ROUTING-IS-NOT-SHARING): the resolver
    maps ids via the SHIPPED ``lorerunes.pdp.keep_scope``, never a private ``f"keep:{k}"``."""

    async def test_mutating_the_shared_prefix_moves_the_resolver_output(
        self,
        resolver_env: tuple[KeepStore, PrincipalStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """PROVE-BY-MUTATION: ``keep_scope`` reads ``lorerunes.pdp.KEEP_SCOPE_PREFIX`` at CALL
        time (``f"{KEEP_SCOPE_PREFIX}{keep_id}"``), so monkeypatching that constant changes the
        SHARED helper's output. A resolver that ROUTES through ``keep_scope`` moves with it; a
        resolver that hand-rolled ``f"keep:{k}"`` stays on the old prefix — a private copy
        wearing the shared name. This reds that wrong build.

        (The mutation reaches the helper regardless of HOW the resolver imported it — a bound
        ``from lorerunes.pdp import keep_scope`` still reads the module global at call time.)"""
        keep_store, _principals, _env = resolver_env
        keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="mut")
        await keep_store.add_household_member(keep_id=keep.id, member_email=_MEMBER_EMAIL)

        monkeypatch.setattr(pdp, "KEEP_SCOPE_PREFIX", "MUTATED_KEEP:")
        scopes = await resolve_visible_keeps(keep_store, member_email=_MEMBER_EMAIL)

        assert scopes, "the member is in one keep — the resolved set must be non-empty"
        assert all(scope.startswith("MUTATED_KEEP:") for scope in scopes), (
            f"the resolver did NOT route through the shared lorerunes.pdp.keep_scope helper — "
            f"mutating KEEP_SCOPE_PREFIX left its output on the old prefix (a private "
            f"f'keep:{{k}}' clone, ROUTING-IS-NOT-SHARING / #102): {scopes!r}"
        )


class TestResolveVisibleKeepsFeedsThePdpEndToEnd:
    """The resolver's output IS the PDP's ``$my_keep_scopes`` — the whole point of Fork F."""

    async def test_the_resolved_set_authorizes_a_keep_row_the_member_can_see(
        self, resolver_env: tuple[KeepStore, PrincipalStore, SurrealEnv]
    ) -> None:
        """END-TO-END: feed the resolver output into a ``Subject`` and the PDP READ-authorizes a
        ``keep:<id>`` row for a keep the member is IN, and DENIES one for a keep the member is
        NOT in — proving the resolved frozenset is exactly the visible-keep predicate input."""
        keep_store, principals, _env = resolver_env
        in_keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="in")
        out_keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="out")
        await keep_store.add_household_member(keep_id=in_keep.id, member_email=_MEMBER_EMAIL)

        visible = await resolve_visible_keeps(keep_store, member_email=_MEMBER_EMAIL)
        member = await principals.get_by_email(_MEMBER_EMAIL)
        assert member is not None
        subject = Subject(
            principal_id=KeepStore._record_id_part(member.id),
            agent_id="agent_bob",
            role=PRINCIPAL_ROLE_MEMBER,
            visible_keep_ids=visible,
        )

        in_scope = keep_scope(KeepStore._record_id_part(in_keep.id))
        out_scope = keep_scope(KeepStore._record_id_part(out_keep.id))
        in_row = Resource(table="memory", owner_principal=None, owner_agent=None, scope=in_scope)
        out_row = Resource(table="memory", owner_principal=None, owner_agent=None, scope=out_scope)

        assert authorize(subject, Action.READ, in_row).allowed, (
            "a keep row the member's household is in must be READ-authorized via the resolved "
            "visible_keep_ids"
        )
        assert not authorize(subject, Action.READ, out_row).allowed, (
            "a keep row the member is NOT in must be DENIED (the resolved set is a real filter)"
        )
        # POSITIVE CONTROL: a server row is readable regardless (proves the deny above is the
        # keep-scope filter discriminating, not a blanket deny).
        server_row = Resource(
            table="memory", owner_principal=None, owner_agent=None, scope=SCOPE_SERVER
        )
        assert authorize(subject, Action.READ, server_row).allowed
