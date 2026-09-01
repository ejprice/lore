"""Contract — packet 63a: the MEMORY RETROFIT — memory is the substrate's FIRST real consumer
(design §0(a)/§1.1). RED before the 63a build; authored by ``contract-63a`` (Opus 4.8 contract
author — tests ONLY).

SPEC: ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §0 item 2 (lore_remember/lore_recall
+ ``LocalMemoryBackend.remember``/``invalidate`` route through the substrate — stamp on write,
filter on read; identity-less call DENIES — removed-behavior 1), §2.4 (default scope = the project
keep — §10-N), §3.2 (the four families F2/F3/F4), §6 (the §9 isolation target).

⚠ FORK 5 (design §10.5, CONFIRMED 2026-08-29 — REPORT-contract-63a-4.md): identity flows into the
retrofitted recall/remember/invalidate as a typed ``subject=`` at the BACKEND, resolved from a
``capability`` at the TOOL layer (Reading A; Reading B — the backend accepting a capability string —
is REJECTED, it makes the backend read the environment). Following the 62 ``_call_stamp_owner``
precedent, the tool-layer resolution is ISOLATED in ``_exercise_recall`` / ``_exercise_remember`` /
``_exercise_invalidate`` (via ``_subject_from_capability``) so the ruling stayed a one-function-family
edit and traps no build. The pins assert OBSERVABLE behaviour (isolation, owner stamp, default scope,
identity-less DENY), never the wiring.

⚠ THE RUNTIME ROUTING OBSERVATION IS BEHAVIOURAL, not a spy (#420 memory leg): recall routes
through ``read_filter`` IFF cross-principal isolation holds (F3 — B cannot see A's private rows);
remember routes through ``stamp_owner``/``guarded_write`` IFF the stored owner is the RESOLVED
subject and a hostile ``owner_*=`` arg is ignored (F4). A verb that "routes" but whose effect is
absent reds here — routing is proven by its effect, never asserted.

STORE LAW cited: §1.4 (option<> dirty rows), §2 (record<> links; CONTENT). Live TEST store
``ws://127.0.0.1:18000`` (NEVER :18500); per-test unique DB, reaped; NO skip marker.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    MEMORY_TABLE,
    absent_scope,
    access_token,
    admin,
    apply_ddl,
    authorize_filter_ids,
    build_memory_backend,
    build_principal_and_keep_stores,
    governed_overlay_ddl,
    member,
    observes_routing,
    python_allowed_ids,
    read_filter_ids,
    seed_memory_governed,
)
from _surreal_harness import (
    connect_admin,
    drop_database,
    make_env,
    run,
    surreal_password,
    surreal_url,
    surreal_user,
    unique_database,
)
from loremaster.config import LoreConfig
from loremaster.server import LoreServer, build_app_context
from loremaster.store import surreal_schema
from loresigil.testing import FakeEmbedder

# The store-free tool-surface builder (the reach-pin idiom) — for the §10.5 capability= schema pin.
from test_mutating_set_derivation import _build_tools

import lorerunes as pdp
from loremaster import governed

_SURREAL_TEST_NAMESPACE = "lore_test"
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"

_DIM = 8
_EMAIL_ALICE = "alice@example.com"
_EMAIL_BOB = "bob@example.com"

# The F2 / F3 hostile fixture over the REAL memory table: ≥2 principals × ≥2 agents each, EVERY
# scope, keeps IN and OUT of a member's set, a server row, NONE-owner rows, and a NONE-scope
# dirty row (the §2.3 grandfather shape). (id, owner_principal, owner_agent, scope) — None ⟺ NONE.
_HOSTILE_ROWS: tuple[tuple[str, str | None, str | None, str | None], ...] = (
    ("m1", "alice", "ag_a1", "agent-private"),
    ("m2", "alice", "ag_a2", "agent-private"),
    ("m3", "alice", "ag_a1", "principal-private"),
    ("m4", "bob", "ag_b1", "principal-private"),
    ("m5", "alice", "ag_a1", "server"),
    ("m6", "bob", "ag_b1", "server"),
    ("m7", "alice", "ag_a1", "keep:k1"),
    ("m8", "bob", "ag_b1", "keep:k1"),
    ("m9", "alice", "ag_a1", "keep:k9"),
    ("m10", None, None, "server"),  # NONE-owner server row (readable by all)
    ("m11", None, None, "agent-private"),  # NONE-owner private row (owned by nobody)
    ("m12", None, None, None),  # NONE-SCOPE dirty/legacy row (§2.3; FORK 1 — pinned observably)
    ("m13", "alice", "ag_a1", None),  # EXACT-OWNER NONE-scope legacy row (§10.1 rider (ii) — the
    #                                   DELETE positive control: its owner CAN hard-delete it)
)

# The rows the Python ``authorize`` side CAN represent (FORK 1 — ``Resource`` requires a domain
# scope). The NONE-scope row m12 is EXCLUDED from the oracle equality (both sides) and pinned
# SEPARATELY by ``test_the_none_scope_dirty_row_is_member_invisible_and_admin_visible`` — because
# admin's store filter (AllRows) includes m12 while the Python side cannot construct it, so
# including it in the equality would make the oracle disagree by construction, not by defect.
_REPRESENTABLE_ROWS = tuple(row for row in _HOSTILE_ROWS if row[3] is not None)
_REPRESENTABLE_IDS = frozenset(row[0] for row in _REPRESENTABLE_ROWS)


@pytest_asyncio.fixture()
async def oracle_conn() -> Any:
    """A signed-in connection on a fresh unique DB carrying the REAL memory DDL + the §4.1 governed
    overlay (hand-transcribed, decoupled from the emitter — the schema module owns the emitter) +
    the hostile row set. Reaped on exit (NEVER :18500)."""
    env = make_env(database=unique_database(), dim=_DIM)
    connection = await connect_admin(env)
    try:
        await apply_ddl(connection, surreal_schema.generate_memory_ddl(dim=_DIM), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
        for row_id, owner_principal, owner_agent, scope in _HOSTILE_ROWS:
            await seed_memory_governed(
                connection, row_id=row_id, dim=_DIM,
                owner_principal=owner_principal, owner_agent=owner_agent, scope=scope,
            )
        yield connection
    finally:
        await connection.close()
        await drop_database(env)


def _subjects() -> list[tuple[str, Any]]:
    return [
        ("alice/member/{k1}", member("alice", "ag_a1", frozenset({pdp.keep_scope("k1")}))),
        ("bob/member/{k1}", member("bob", "ag_b1", frozenset({pdp.keep_scope("k1")}))),
        (
            "alice/member/{k1,k9}",
            member("alice", "ag_a1", frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k9")})),
        ),
        ("alice/member/no-keeps", member("alice", "ag_a1", frozenset())),
        ("alice/admin", admin("alice", "ag_a1")),
    ]


# =========================================================================== #
# F2 — SINGLE-BRAIN ORACLE over the REAL memory table incl. DIRTY rows (design §3.2 F2).
# =========================================================================== #


class TestF2SingleBrainOverTheRealMemoryTable:
    """F2 — for every (subject, READ), the Python ``authorize`` set EQUALS the SUBSTRATE
    ``read_filter`` set over the real memory table, byte for byte, INCLUDING dirty rows."""

    async def test_read_filter_equals_authorize_over_the_real_table(self, oracle_conn: Any) -> None:
        """⚠ RED at HEAD (``read_filter`` is NotImplementedError). The substrate READ splice must
        select EXACTLY the rows Python ``authorize`` allows, ∀ subjects. Dirty NONE-owner rows are
        included (m10 readable by all, m11 by nobody); the NONE-scope row m12 is handled by the
        companion observable pin below. REDDENS a read_filter that diverges from authorize."""
        mismatches: list[str] = []
        for label, subject in _subjects():
            python_ids = python_allowed_ids(_REPRESENTABLE_ROWS, subject, pdp.Action.READ)
            store_ids = (await read_filter_ids(oracle_conn, subject, _memory_case())) & _REPRESENTABLE_IDS
            if python_ids != store_ids:
                mismatches.append(
                    f"[{label}] python={sorted(python_ids)} store={sorted(store_ids)} "
                    f"(only-py={sorted(python_ids - store_ids)}, only-store={sorted(store_ids - python_ids)})"
                )
        assert not mismatches, "the substrate read splice diverged from authorize:\n" + "\n".join(mismatches)

    async def test_GREEN_control_authorize_filter_equals_authorize_over_the_real_table(
        self, oracle_conn: Any
    ) -> None:
        """⚠ GREEN CONTROL (the PDP side is sound on the REAL table incl. NONE-owner rows). Proves
        the F2 RED above is attributable to ``read_filter`` (a private copy / divergent splice), NOT
        to the PDP being wrong on the real memory DDL — the 61b oracle bound re-confirmed here. If
        THIS reds, the PDP itself mis-handles the real option<record<>> owner columns."""
        mismatches: list[str] = []
        for label, subject in _subjects():
            python_ids = python_allowed_ids(_REPRESENTABLE_ROWS, subject, pdp.Action.READ)
            store_ids = (
                await authorize_filter_ids(oracle_conn, subject, pdp.Action.READ, MEMORY_TABLE)
            ) & _REPRESENTABLE_IDS
            if python_ids != store_ids:
                mismatches.append(f"[{label}] python={sorted(python_ids)} store={sorted(store_ids)}")
        assert not mismatches, (
            "authorize_filter (the PDP directly) diverged from authorize on the REAL memory table — "
            "the PDP mis-handles the real option<record<>> owner columns:\n" + "\n".join(mismatches)
        )

    async def test_the_none_scope_dirty_row_is_member_invisible_and_admin_visible(
        self, oracle_conn: Any
    ) -> None:
        """⚠ RED at HEAD (``read_filter`` NotImplementedError). §2.3 single-brain-on-dirty-rows: the
        NONE-scope legacy row m12 matches no member ``scope=$x`` disjunct → member-INVISIBLE
        (fail-closed), and admin's AllRows → admin-VISIBLE. This is the §2.3 fail-closed direction
        proven observably (FORK 1 — pinned WITHOUT constructing Resource(scope=None), so neither
        reading of FORK 1 is trapped). REDDENS a build whose read_filter leaks a NONE-scope row to a
        member (a legacy row silently visible to the wrong principal)."""
        for label, subject in _subjects():
            if subject.role == pdp.PRINCIPAL_ROLE_ADMIN:
                admin_ids = await read_filter_ids(oracle_conn, subject, _memory_case())
                assert "m12" in admin_ids, f"admin ({label}) must SEE the NONE-scope legacy row m12"
            else:
                member_ids = await read_filter_ids(oracle_conn, subject, _memory_case())
                assert "m12" not in member_ids, (
                    f"member ({label}) must NOT see the NONE-scope legacy row m12 — a NONE scope is "
                    f"fail-closed (invisible to every member, §2.3)"
                )


# =========================================================================== #
# F2 (DELETE leg) — DELETE is scope-INDEPENDENT on DIRTY rows (design §10.1 rider (ii), 61 D4(a)).
# The POSITIVE CONTROL that a NONE-scope row is NOT universally invisible.
# =========================================================================== #

# The targeted DELETE probe: an EXACT-owner NONE-scope row (m13), an UNOWNED NONE-scope row (m12),
# and an EXACT-owner domain-scope control (m1). Intersecting the store's DELETE-filter result with
# this small set keeps the single-brain oracle focused on the dirty-row question.
_DELETE_PROBE_IDS = frozenset({"m13", "m12", "m1"})


def _delete_allowed_ids(subject: Any, rows: tuple[tuple[str, Any, Any, Any], ...]) -> set[str]:
    """The Python ``authorize(subject, DELETE, ·)`` verdict over ``rows`` INCLUDING NONE-scope rows
    (the DELETE leg CANNOT skip them — they are the whole question). Constructs
    ``Resource(scope=absent_scope())`` for a NONE-scope row, so at HEAD it RAISES (FORK 1 unbuilt →
    behavioural RED) and on the correct build it evaluates the scope-independent DELETE predicate."""
    allowed: set[str] = set()
    for row_id, owner_principal, owner_agent, scope in rows:
        raw_scope: Any = scope if scope is not None else absent_scope()
        resource = pdp.Resource(
            table=MEMORY_TABLE,
            owner_principal=owner_principal,
            owner_agent=owner_agent,
            scope=raw_scope,
        )
        if pdp.authorize(subject, pdp.Action.DELETE, resource).allowed:
            allowed.add(row_id)
    return allowed


class TestF2DeleteIsScopeIndependentOnDirtyRows:
    """§10.1 rider (ii) / 61 D4(a) — DELETE is scope-INDEPENDENT: an exact ``(principal, agent)``
    owner CAN hard-delete its OWN NONE-scope legacy row, single-brain (Python ``authorize`` ==
    store ``authorize_filter``). This is THE positive control that a NONE-scope row is NOT
    universally invisible — WITHOUT it, a build that special-cases ``None`` → "deny everything"
    passes every READ-only pin (design §10.1 rider (ii))."""

    _PROBE_ROWS = tuple(row for row in _HOSTILE_ROWS if row[0] in _DELETE_PROBE_IDS)

    async def test_the_delete_filter_is_single_brain_over_none_scope_dirty_rows(
        self, oracle_conn: Any
    ) -> None:
        """⚠ RED at HEAD (``Resource(scope=None)`` raises — FORK 1 unbuilt). For the OWNER
        (alice/ag_a1): the Python DELETE-allowed set EQUALS the store DELETE-filter set over the
        dirty probe rows, and it CONTAINS m13 (owner deletes its own NONE-scope row — positive) and
        EXCLUDES m12 (an UNOWNED NONE-scope row is not deletable by alice — negative). For a NON-owner
        (bob): both sets are empty and m13 is absent. REDDENS a build that special-cases None → deny
        (m13 wrongly excluded, Python≠store) AND one that lets a non-owner delete a NONE-scope row."""
        owner = member("alice", "ag_a1", frozenset())
        non_owner = member("bob", "ag_b1", frozenset())

        owner_python = _delete_allowed_ids(owner, self._PROBE_ROWS)
        owner_store = (
            await authorize_filter_ids(oracle_conn, owner, pdp.Action.DELETE, MEMORY_TABLE)
        ) & _DELETE_PROBE_IDS
        assert owner_python == owner_store, (
            f"DELETE single-brain diverged for the owner: python={sorted(owner_python)} "
            f"store={sorted(owner_store)}"
        )
        assert "m13" in owner_python, (
            "the exact (principal, agent) owner must be able to DELETE its own NONE-scope legacy row "
            "(61 D4(a) — DELETE is scope-independent); a build denying it special-cases None→deny"
        )
        assert "m12" not in owner_python, (
            "an UNOWNED NONE-scope row must NOT be deletable by a member — NONE scope is not "
            "universally deletable, only by the exact owner"
        )

        non_owner_python = _delete_allowed_ids(non_owner, self._PROBE_ROWS)
        non_owner_store = (
            await authorize_filter_ids(oracle_conn, non_owner, pdp.Action.DELETE, MEMORY_TABLE)
        ) & _DELETE_PROBE_IDS
        assert non_owner_python == non_owner_store == set(), (
            f"a non-owner must DELETE none of the probe rows (incl. m13): "
            f"python={sorted(non_owner_python)} store={sorted(non_owner_store)}"
        )

    async def test_a_none_scope_owned_row_is_read_write_invisible_but_delete_able_to_its_owner(
        self, oracle_conn: Any
    ) -> None:
        """⚠ RED at HEAD (``Resource(scope=None)`` raises). THE CONTRAST that discriminates BOTH
        wrong builds: for the owner of m13 (a NONE-scope owned row), READ and WRITE are DENIED
        (scope-dependent — no scope disjunct matches) while DELETE is ALLOWED (scope-independent
        owner check). REDDENS a build that special-cases None→deny-everything (DELETE wrongly False)
        AND a build that lets an owner READ/WRITE a NONE-scope row via the scope-dependent path."""
        owner = member("alice", "ag_a1", frozenset())
        m13_resource = pdp.Resource(
            table=MEMORY_TABLE, owner_principal="alice", owner_agent="ag_a1", scope=absent_scope()
        )
        assert not pdp.authorize(owner, pdp.Action.READ, m13_resource).allowed, (
            "a NONE-scope owned row must be READ-invisible even to its owner (scope-dependent)"
        )
        assert not pdp.authorize(owner, pdp.Action.WRITE, m13_resource).allowed, (
            "a NONE-scope owned row must be WRITE-invisible even to its owner (scope-dependent)"
        )
        assert pdp.authorize(owner, pdp.Action.DELETE, m13_resource).allowed, (
            "a NONE-scope owned row must be DELETE-able by its owner (scope-INDEPENDENT, 61 D4(a))"
        )


# =========================================================================== #
# F3 — CROSS-PRINCIPAL ISOLATION ∀ read verbs + served-COUNT == served-SET (design §3.2 F3, §6).
# The store-level isolation is F2's read_filter leg; here the TOOL-level (recall) served count.
# =========================================================================== #


class TestF3RecallServesOnlyTheCallerVisibleSet:
    """F3 / trust-doctrine Leg 1 (design §3.2 F3, §6 item 2) — the REAL ``recall`` serves ONLY the
    caller's visible rows: its served-set SIZE reflects the caller-VISIBLE matches, never the
    unfiltered total. A row the caller cannot see never enters the answer, even when it matches the
    query — *a count over the unfiltered table beside a filtered listing is a false clear.*

    ⚠ MISSING PIN 4 (adversary §MISSING-PINS): this REPLACES the tautological
    ``test_read_filter_count_equals_read_filter_set_size``, which built ONE ``read_filter`` fragment
    and used it on BOTH sides (``SELECT count() … WHERE {frag}`` and ``SELECT id … WHERE {frag}``) —
    so ``count == size`` held TRIVIALLY on any build, while its docstring PROMISED to red a build
    that counts over the whole table. Its assertion never exercised ``recall``, where the false clear
    lives (a failure message promising a check the assertion never performs — CLAUDE.md). ⚠ MEMORY
    NOTE: ``recall`` reports NO separate count line — ``AppContext._render_recalled_memories``
    renders one block per served row (``server.py``) — so the realizable Leg-1 property for memory is
    that the served SET is the caller-filtered set, size-discriminated against the unfiltered total.
    (The literal "separately-computed count over the whole table" false clear belongs to comms
    ``drain``/``rollup``, 63b/64, where a count IS reported; flagged to lead-63 in the report.)"""

    @observes_routing("lore_recall", "lore_recall")
    async def test_recall_serves_the_caller_filtered_set_not_the_unfiltered_total(
        self, retrofit_world: Any, alice_capability: _Credential, bob_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD (retrofit unbuilt — ``get_or_create_keyed`` stub / no ``capability`` param).
        Over a ≥2-principal hostile fixture where a shared query matches BOTH alice's visible rows AND
        a bob principal-private row INVISIBLE to alice, alice's ``recall`` serves ONLY her visible
        matches — the served set NEVER contains bob's row, and its size is STRICTLY BELOW the
        unfiltered matching total (measured from the store, not a literal). REDDENS the false clear §6
        item 2 forbids: a build whose ``recall`` serves the unfiltered set (bob's private row appears,
        served size == the whole-table total) — the count-over-the-whole-table-beside-a-filtered-
        listing defect. Ranking-robust: bob's row is EXCLUDED by the read filter regardless of the
        hybrid-search ordering, so the ``not in`` / ``subset`` legs cannot flake on a correct build."""
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        # alice's two VISIBLE matching rows: one default (project-keep) scoped, one her own
        # principal-private. Distinct texts (identical text collapses to ONE deterministic id).
        await _exercise_remember(backend, text="marker topic alpha", capability=alice_capability)
        await _exercise_remember(
            backend, text="marker topic beta", capability=alice_capability, scope="principal-private"
        )
        # ... and a bob principal-private row INVISIBLE to alice, matching the SAME query token.
        await _exercise_remember(
            backend, text="marker topic gamma", capability=bob_capability, scope="principal-private"
        )
        alice_visible_texts = {"marker topic alpha", "marker topic beta"}

        served = await _exercise_recall(backend, query="marker topic", capability=alice_capability)
        served_texts = {memory.text for memory in served}

        # The unfiltered matching total, MEASURED from the store (all three seeds share the token) —
        # the count a false-clear build would report beside a filtered listing.
        unfiltered_total = _count(
            await run(admin_conn, f"SELECT count() FROM {MEMORY_TABLE} GROUP ALL")
        )
        assert unfiltered_total == 3, (
            f"fixture setup failed — expected 3 seeded memory rows, store holds {unfiltered_total}"
        )
        # Anti-vacuity: recall is not empty (a build that over-denies alice's OWN rows would pass the
        # negatives trivially — this catches it).
        assert served_texts, "alice's recall returned NOTHING — a build that over-denies her own rows"
        # Leg-1 NEGATIVE (the false clear): bob's invisible private row never enters alice's answer.
        assert "marker topic gamma" not in served_texts, (
            "alice's recall surfaced bob's principal-private note — the served set is the UNFILTERED "
            "table, not the caller-filtered set (the exact false clear §6 item 2 forbids)"
        )
        # Every served row is alice-visible (no foreign leak of ANY kind).
        assert served_texts <= alice_visible_texts, (
            f"alice's recall served a row she cannot see: {sorted(served_texts - alice_visible_texts)}"
        )
        # Leg-1 COUNT corollary: the served count is the caller-filtered count, STRICTLY BELOW the
        # unfiltered total (an unfiltered build serves all 3 → not < 3 → RED). No dup inflation.
        assert len(served) == len(served_texts), "recall served duplicate rows (id-collapse broken)"
        assert len(served) < unfiltered_total, (
            f"alice's recall served {len(served)} rows == the unfiltered total {unfiltered_total} — a "
            f"count over the whole table, not the caller-filtered set (trust Leg 1)"
        )


# =========================================================================== #
# The RETROFIT tool wiring — the runtime routing observation (behavioural), identity-less DENY,
# default scope, and F4 anti-injection. Uses the real LocalMemoryBackend.
# =========================================================================== #


@pytest_asyncio.fixture()
async def retrofit_world() -> Any:
    """A real ``LocalMemoryBackend`` on a fresh DB + a PrincipalStore/KeepStore + alice & bob
    principals + a canonical project keep (``key='project:lore'``, alice's household) — enough to
    exercise the retrofitted recall/remember over live behaviour.

    ⚠ MISSING PIN 1 (C-DEF fix, adversary §MISSING-PINS): the project keep is minted via
    ``get_or_create_keyed(key='project:lore', …)`` — the SF-63-4 verb (``keeps.py``) — NOT
    ``create_keep`` (which sets NO ``key``). Design §2.2 RULES that ``remember``'s default-scope
    resolution finds the project keep by ONE indexed read ``KeepStore.get_by_key('project:lore')``,
    and store law §1.8 says a ``key IS NONE`` row is never matched by ``WHERE key=$k`` — so a
    ``create_keep``-minted (keyless) keep is UNRESOLVABLE by the ruled path, making
    ``test_a_remembered_note_defaults_to_the_project_keep_scope`` UNSATISFIABLE by a §2.2-compliant
    build (it would have to resolve by ``(type,name)``, the exact path §2.2 rejects). The migration
    module's own ``test_the_verb_backfills_the_project_keep_scope`` already asserts the project keep
    is ``WHERE key='project:lore'`` — this fix makes the two consistent.
    ⚠ ``get_or_create_keyed`` is a builder-GREEN stub, so at HEAD this fixture raises
    ``NotImplementedError`` → every ``retrofit_world``-dependent test is a SETUP-ERROR RED at HEAD
    (HONEST: the keyed-keep mechanism is a builder deliverable, like the absent schema columns; on a
    correct build the fixture succeeds and every body assertion runs meaningfully)."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    backend = await build_memory_backend(env)
    admin_conn = await connect_admin(env)
    await apply_ddl(admin_conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
    await principal_store.create(email=_EMAIL_ALICE, role="member")
    await principal_store.create(email=_EMAIL_BOB, role="member")
    project_keep = await keep_store.get_or_create_keyed(
        key="project:lore", type="project", keeper_email=_EMAIL_ALICE, name="lore"
    )
    try:
        yield backend, principal_store, keep_store, admin_conn, env, project_keep
    finally:
        await admin_conn.close()
        await backend.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


@dataclass(frozen=True)
class _Credential:
    """The TOOL-LAYER credential the ``_exercise_*`` seam resolves to a
    :class:`lorerunes.pdp.Subject` (design §10.5 CLARIFICATION, 2026-08-29). It carries the
    principal EMAIL (the access-token subject), the raw capability TOKEN (62's ``register`` mint),
    and the identity stores + ``AgentRegistry`` that ``governed.resolve_subject`` reads — everything
    the ONE production constructor needs, since a test's call site may pass only ``capability=``."""

    email: str
    token: str
    registry: Any
    principal_store: Any
    keep_store: Any


async def _subject_from_capability(capability: Any) -> Any:
    """Resolve a tool-layer credential to a :class:`lorerunes.pdp.Subject` via the REAL production
    constructor ``governed.resolve_subject`` (design §10.5 CLARIFICATION shape point 1, 2026-08-29 —
    the R-a.2 ONE ``Subject(`` site). A test-side ``Subject(...)`` construction is FORBIDDEN here: it
    would make the routing observation a fixture rather than the production seam. ONE helper, three
    verbs — the capability→Subject resolution is policy that must AGREE across
    recall/remember/invalidate (ONE IMPLEMENTATION)."""
    return await governed.resolve_subject(
        access_token(subject=capability.email),
        capability.token,
        registry=capability.registry,
        principal_store=capability.principal_store,
        keep_store=capability.keep_store,
    )


async def _exercise_remember(
    backend: Any, *, text: str, capability: Any, **kwargs: Any
) -> Any:
    """The ONE place the RETROFITTED ``remember`` is called (FORK 5 / §10.5 — isolated per the 62
    ``_call_stamp_owner`` precedent, so the ruling stays a one-function-family edit). §10.5 Reading A
    (CONFIRMED 2026-08-29): this seam plays the TOOL-LAYER role — it resolves ``capability`` → a
    typed ``Subject`` and calls ``backend.remember(..., subject=subject)``. The BACKEND takes
    ``subject=`` and NEVER a capability string (it must not read the environment). ``scope=`` (via
    ``**kwargs``) is the ONE wire argument that legitimately crosses beside ``subject=`` — a
    PDP-validated request, not identity (§2.4). RED before the 63a build (``resolve_subject`` /
    ``backend.remember(subject=)`` unbuilt)."""
    subject = await _subject_from_capability(capability)
    return await backend.remember(text, kind="fact", subject=subject, **kwargs)


async def _exercise_recall(backend: Any, *, query: str, capability: Any) -> Any:
    """The ONE place the RETROFITTED ``recall`` is called (FORK 5 / §10.5 — isolated). §10.5 Reading
    A: resolve ``capability`` → ``Subject`` at this tool-layer seam, then
    ``backend.recall(query, subject=subject)``. RED before the 63a build."""
    subject = await _subject_from_capability(capability)
    return await backend.recall(query, subject=subject)


async def _exercise_invalidate(backend: Any, *, memory_id: str, capability: Any) -> Any:
    """The ONE place the RETROFITTED ``invalidate`` (the backend's close/retire write path) is
    called (FORK 5 / §10.5 — isolated, mirroring ``_exercise_remember``). §10.5 Reading A: resolve
    ``capability`` → ``Subject`` here, then ``backend.invalidate(memory_id, subject=subject)`` — the
    close authorizes the WRITE on the existing (possibly foreign-owned) row via ``guarded_write``.
    RED before the 63a build (``invalidate`` today, ``local.py``, issues a BARE ungoverned
    ``UPDATE … SET valid_until`` with no ``subject``)."""
    subject = await _subject_from_capability(capability)
    return await backend.invalidate(memory_id, subject=subject)


class TestIdentityLessCallsDeny:
    """§0 removed-behavior 1 — post-retrofit an identity-LESS recall/remember DENIES with a teaching
    error (never a silent empty result, never the pre-retrofit unfiltered answer)."""

    async def test_an_identity_less_recall_denies(self, retrofit_world: Any) -> None:
        """⚠ RED at HEAD — today ``recall(query)`` returns a rendered digest with NO identity. Post-
        retrofit an identity-less call DENIES (GovernedDenied, a TEACHING error), because an
        unauthenticated read of the fleet's memory is exactly what the retrofit closes. REDDENS a
        build that keeps answering identity-less calls, AND a build that DENIES via a bare crash
        (the design says a teaching error, not a TypeError)."""
        backend, *_rest = retrofit_world
        with pytest.raises(governed.GovernedDenied):
            await backend.recall("anything")

    async def test_an_identity_less_remember_denies(self, retrofit_world: Any) -> None:
        """⚠ RED at HEAD — today ``remember(text, kind=…)`` writes with NO owner. Post-retrofit an
        identity-less write DENIES (the owner is server-derived from the credential, never absent).
        REDDENS a build that writes an ownerless row on an identity-less call."""
        backend, *_rest = retrofit_world
        with pytest.raises(governed.GovernedDenied):
            await backend.remember("anything", kind="fact")


# --------------------------------------------------------------------------- #
# §10.5(ii) — the TOOL-LAYER identity-less DENY twin (the backend-level twin is above). The design
# names the tool layer as ``AppContext.recall``/``remember`` (capability= at the composition root);
# the ONLY robust, non-trapping way to exercise the retrofitted handler is a REAL AppContext (a
# duck ``self`` would trap the builder if the deny routes through ``resolve_subject``, which reads
# the identity stores the builder wires into AppContext). So this boots the genuine handler via
# ``build_app_context`` (the ``test_memory_cutover`` / ``test_mcp_server._make_context`` pattern).
# --------------------------------------------------------------------------- #


def _boot_config(slug: str, root: Path) -> LoreConfig:
    """A validated config on the dev harness with ``surreal.database`` UNSET (derives from the
    uuid-unique ``slug``), so each boot writes its own throwaway DB (mirrors
    ``test_memory_cutover._config``)."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": surreal_url(),
            "namespace": _SURREAL_TEST_NAMESPACE,
            "user_env": _SURREAL_USER_ENV,
            "password_env": _SURREAL_PASS_ENV,
        },
        "roots": [
            {"tier": "custom", "watch": "live", "path": str(root), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9244},
    }
    return LoreConfig.model_validate(payload)


@pytest_asyncio.fixture()
async def app_context(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    """A REAL booted :class:`AppContext` on a throwaway DB (FakeEmbedder, no background tasks) — the
    tool-layer surface the MCP tools dispatch through. Reaped on exit (NEVER :18500)."""
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password().get_secret_value())
    slug = unique_database()
    context = await build_app_context(
        server=LoreServer(_boot_config(slug, tmp_path)),
        embedder=FakeEmbedder(dim=_DIM),
        manifest_path=tmp_path / "m.db",
        snapshot_root=tmp_path / "snap",
        start_tasks=False,
        calibration_engine=None,
    )
    try:
        yield context
    finally:
        await context.aclose()
        await drop_database(make_env(database=slug, dim=_DIM))


class TestIdentityLessToolLayerCallsDeny:
    """§10.5(ii) — the TOOL-LAYER twin of ``TestIdentityLessCallsDeny``: an identity-less call at the
    ``AppContext`` handler (the MCP tool surface) DENIES with a :class:`~loremaster.governed.
    GovernedDenied` teaching error — NEVER a ``TypeError`` (``capability=`` must be OPTIONAL) and
    NEVER the pre-retrofit unfiltered answer. Closes the tool-layer bypass: an unauthenticated read
    of the fleet's memory must fail at the composition root too, not only at the backend."""

    async def test_an_identity_less_tool_recall_denies(self, app_context: Any) -> None:
        """⚠ RED at HEAD — today ``AppContext.recall(query)`` renders a digest with NO identity.
        Post-retrofit an identity-less tool call raises ``GovernedDenied``. REDDENS a build that
        keeps answering identity-less tool calls AND one that denies via a bare ``TypeError``
        (``capability=`` must be optional per §10.5, an absent identity is a TEACHING deny)."""
        with pytest.raises(governed.GovernedDenied):
            await app_context.recall("anything")

    async def test_an_identity_less_tool_remember_denies(self, app_context: Any) -> None:
        """⚠ RED at HEAD — today ``AppContext.remember(text, kind=…)`` writes with NO owner. Post-
        retrofit an identity-less tool write raises ``GovernedDenied``. REDDENS a build that writes
        an ownerless row from the tool layer, or that denies via a bare ``TypeError``."""
        with pytest.raises(governed.GovernedDenied):
            await app_context.remember("anything", kind="fact")


class TestTheCapabilityParamDescriptionIsOneSharedConstant:
    """§10.5 rider (i) — the ``capability=`` parameter description is ONE shared constant across
    every governed tool (the packet-45 ``_comms_identity_agent_description`` idiom), NEVER N copies
    of the teaching prose. A per-tool copy is how the teaching drifts (PKT-28 C1: served prose no
    gate checks)."""

    async def test_lore_recall_and_lore_remember_share_one_capability_description(
        self, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD — today neither ``lore_recall`` nor ``lore_remember`` has a ``capability=``
        param, so the description is ABSENT. Post-retrofit both carry an OPTIONAL ``capability=``
        whose description is BYTE-IDENTICAL across the two (one shared source). REDDENS a build that
        ships N divergent copies of the teaching prose, or that adds the param to only one tool."""
        tools = {tool.name: tool for tool in await _build_tools(tmp_path)}
        descriptions: dict[str, Any] = {}
        for name in ("lore_recall", "lore_remember"):
            properties = (tools[name].parameters or {}).get("properties", {})
            capability = properties.get("capability")
            assert capability is not None, (
                f"{name} has no capability= param — the retrofit's OPTIONAL identity seam is unbuilt "
                f"(§10.5). Post-retrofit every governed tool carries it."
            )
            descriptions[name] = capability.get("description")
        assert all(descriptions.values()) and len(set(descriptions.values())) == 1, (
            f"the capability= description must be ONE shared constant across governed tools (packet-45 "
            f"idiom), never N copies: {descriptions}"
        )


class TestRememberStampsTheOwnerAndDefaultsToProjectScope:
    """§0 item 2 + §2.4 — remember ROUTES through the stamp (the stored owner is the RESOLVED
    subject, never a caller arg — F4) and defaults a note's scope to the canonical PROJECT keep
    (§10-N — so the fleet still sees a fleet agent's fresh note)."""

    @observes_routing("lore_remember", "lore_remember")
    async def test_a_remembered_note_is_owner_stamped_from_the_credential(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD (no ``capability`` param → TypeError; routing unbuilt). The stored row's
        ``owner_principal`` names ALICE (derived from the verified capability), proving remember
        routes through ``stamp_owner``/``guarded_write``. REDDENS a build that writes no owner (the
        runtime routing observation for the write verb — behavioural, not a spy)."""
        backend, principal_store, _k, admin_conn, _env, _keep = retrofit_world
        alice = await principal_store.get_by_email(_EMAIL_ALICE)
        memory_id = await _exercise_remember(backend, text="alice note", capability=alice_capability)
        row = _one(
            await run(
                admin_conn,
                "SELECT owner_principal, scope FROM type::record('memory', $id)",
                {"id": _bare(memory_id)},
            )
        )
        assert row["owner_principal"] is not None and _bare(str(alice.id)) in str(row["owner_principal"]), (
            f"the remembered note must be owner-stamped as alice ({alice.id}) from the credential, "
            f"got owner_principal={row['owner_principal']!r}"
        )

    async def test_a_remembered_note_defaults_to_the_project_keep_scope(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD. §2.4/§10-N: a note with no explicit scope defaults to ``keep:<project>``
        (NOT principal-private — that would silently privatise the fleet's shared notebook). So a
        fleet agent's fresh note stays fleet-visible post-cutover. REDDENS a build that defaults to
        principal-private (the dogfood-breaking default)."""
        backend, _p, _k, admin_conn, _env, project_keep = retrofit_world
        memory_id = await _exercise_remember(backend, text="shared note", capability=alice_capability)
        row = _one(
            await run(admin_conn, "SELECT scope FROM type::record('memory', $id)", {"id": _bare(memory_id)})
        )
        assert row["scope"] == f"keep:{_bare(project_keep.id)}", (
            f"a default-scope note must be scoped to the PROJECT keep keep:{_bare(project_keep.id)} "
            f"(§2.4/§10-N — never principal-private), got scope={row['scope']!r}"
        )

    async def test_a_hostile_owner_argument_does_not_move_the_stamp(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD (F4 anti-injection). A caller passing ``owner_principal=<bob>`` /
        ``as_agent=`` / ``created_by=`` must NOT move the stamp — the owner stays ALICE (server-
        derived from the credential). Either the tool exposes NO such parameter (a TypeError on the
        kwarg — the strongest form) OR it is ignored; EITHER way the stored owner is alice, never
        bob. REDDENS a build where a caller arg forges the owner (§3.2.2 confused-deputy)."""
        backend, principal_store, _k, admin_conn, _env, _keep = retrofit_world
        alice = await principal_store.get_by_email(_EMAIL_ALICE)
        bob = await principal_store.get_by_email(_EMAIL_BOB)
        bob_id = _bare(str(bob.id))
        try:
            memory_id = await _exercise_remember(
                backend, text="forge attempt", capability=alice_capability, owner_principal=bob_id,
            )
        except TypeError:
            return  # the tool exposes no owner arg at all — the strongest anti-injection (accepted)
        row = _one(
            await run(
                admin_conn,
                "SELECT owner_principal FROM type::record('memory', $id)",
                {"id": _bare(memory_id)},
            )
        )
        assert _bare(str(alice.id)) in str(row["owner_principal"]), (
            f"a hostile owner_principal= arg forged the owner — it must stay alice ({alice.id}), the "
            f"credential-derived owner, got {row['owner_principal']!r}"
        )


class TestF3RecallIsolationAcrossPrincipals:
    """F3 / §6 item 1 — recall by principal B never returns principal A's private rows (the runtime
    routing observation for the READ verb: isolation holds IFF recall routes through read_filter)."""

    @observes_routing("lore_recall", "lore_recall")
    async def test_recall_by_bob_does_not_surface_alices_private_note(
        self, retrofit_world: Any, alice_capability: _Credential, bob_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD (no identity → TypeError; unbuilt). Alice remembers a principal-private
        note; Bob's recall of the same text must return NOTHING of alice's — cross-principal
        isolation over the wire (§6 item 1). REDDENS a build where recall does not filter by the
        caller's identity (B sees A's private memory — the leak the retrofit exists to close)."""
        backend, _p, _k, _admin, _env, _keep = retrofit_world
        await _exercise_remember(
            backend, text="alice private secret", capability=alice_capability, scope="principal-private",
        )
        bob_hits = await _exercise_recall(backend, query="alice private secret", capability=bob_capability)
        assert "alice private secret" not in str(bob_hits), (
            "bob's recall surfaced alice's principal-private note — recall must filter by the caller's "
            "identity (read_filter); cross-principal isolation is the §9 headline"
        )


class TestInvalidateRoutesThroughGuardedWrite:
    """§1.1 / §2.5 (MISSING PIN 2) — the backend's ``invalidate``/supersede write path is GOVERNED:
    closing a memory row authorizes the WRITE on the EXISTING (possibly foreign-owned) row via
    ``governed.guarded_write``, so a member cannot retire ANOTHER principal's note. This is the
    contract's ONLY exercise of the ``guarded_write`` seam through a real retrofit consumer (the
    F2/F3 legs exercise ``read_filter``; the substrate module pins ``guarded_write`` directly, but
    NOTHING proved ``invalidate`` ROUTES through it — ``write_verbs=('remember','invalidate')`` in
    ``_memory_case`` is decoration no runner iterates). The mutating write verb is the DANGEROUS one:
    it touches an existing row, and at HEAD ``invalidate`` issues a BARE ungoverned ``UPDATE``."""

    @observes_routing("lore_remember", "lore_remember")
    async def test_a_member_cannot_close_a_foreign_owned_row(
        self, retrofit_world: Any, alice_capability: _Credential, bob_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD (retrofit unbuilt — ``get_or_create_keyed`` stub / no ``capability`` param).
        alice remembers a note (default project-keep scope, alice's household); bob — NOT householded
        in the project keep — tries to ``invalidate`` it. The close routes through ``guarded_write``,
        which authorizes the WRITE on the existing row → bob is DENIED (``GovernedDenied``) AND the
        row is UNCHANGED (still valid — a denied close never mutates, single-brain on writes).
        REDDENS the wrong build the adversary names: ``invalidate`` issues a bare ``UPDATE`` bypassing
        ``guarded_write`` → bob retires alice's note (no exception raised, ``valid_until`` set). This
        is the behavioural routing observation for the WRITE verb — routing proven by its EFFECT."""
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        memory_id = await _exercise_remember(
            backend, text="alice note to keep", capability=alice_capability
        )
        with pytest.raises(governed.GovernedDenied):
            await _exercise_invalidate(backend, memory_id=memory_id, capability=bob_capability)
        row = _one(
            await run(
                admin_conn, "SELECT valid_until FROM type::record('memory', $id)", {"id": _bare(memory_id)}
            )
        )
        assert row["valid_until"] is None, (
            "a DENIED invalidate retired the row — a member closed another principal's note; the "
            "close must route through guarded_write (single-brain on writes), not a bare UPDATE"
        )

    async def test_an_owner_can_close_its_own_row(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD. THE POSITIVE CONTROL for the deny pin: alice (householded in the project
        keep) CAN close her OWN project-scoped note → ``valid_until`` is set. Without it, a build that
        special-cases invalidate to "deny everything" would pass the deny pin above while breaking
        every legitimate close (a guard nobody can pass is as wrong as one nobody can fail)."""
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        memory_id = await _exercise_remember(
            backend, text="alice note to retire", capability=alice_capability
        )
        await _exercise_invalidate(backend, memory_id=memory_id, capability=alice_capability)
        row = _one(
            await run(
                admin_conn, "SELECT valid_until FROM type::record('memory', $id)", {"id": _bare(memory_id)}
            )
        )
        assert row["valid_until"] is not None, (
            "alice could not close her OWN note — the owner's legitimate invalidate was denied "
            "(a build that special-cases invalidate to deny-everything)"
        )

    # ----------------------------------------------------------------------- #
    # MISSING PIN 2's SUPERSEDE leg (the QUANTIFIER-LAW fix — cold-audit REPORT-cold-audit-63a §F1).
    # The class above pinned the invariant "no member closes a foreign row" on ONE of the two write
    # verbs design §2.5 names ("both route through guarded_write/the stamp"). `remember(supersedes=X)`
    # ALSO closes an EXISTING, possibly foreign-owned row (`_close_superseded_fragment` — a WRITE),
    # and the shipped build routed only invalidate: the supersede-close is a BARE ungoverned UPDATE,
    # so bob retires alice's note by id. Added by contract-63a-iii — completing the under-quantified
    # pin, not weakening it. RED before the 63a-iii fix (proven LIVE in the cold audit's §F1 repro).
    # ----------------------------------------------------------------------- #

    @observes_routing("lore_remember", "lore_remember")
    async def test_a_member_cannot_supersede_close_a_foreign_owned_row(
        self, retrofit_world: Any, alice_capability: _Credential, bob_capability: _Credential
    ) -> None:
        """⚠ RED before the 63a-iii fix (measured at ``dd5c9b2`` — cold-audit §F1, CONFIRMED live).
        The QUANTIFIER-LAW twin of ``test_a_member_cannot_close_a_foreign_owned_row``: alice remembers
        a note (default project-keep scope, alice's household); bob — NOT householded in the project
        keep — calls ``remember(supersedes=<alice's id>)``. The supersede-CLOSE of the old row routes
        through ``guarded_write`` (design §2.5: 'both route through guarded_write/the stamp'), which
        authorizes the WRITE on the existing row → bob is DENIED (``GovernedDenied``) AND alice's row
        is UNCHANGED (``valid_until`` still None, ``superseded_by`` unset — a denied close never
        mutates). REDDENS the shipped build the cold audit reproduced: the bare
        ``_close_superseded_fragment`` UPDATE (no WHERE guard, no authorize_filter) lets bob retire
        alice's note by id — no exception, ``valid_until`` set, ``superseded_by`` → bob's note
        (REPORT-cold-audit-63a §F1). Behavioural routing observation for the WRITE verb — routing
        proven by its EFFECT (a denied member cannot close a foreign row through EITHER close verb)."""
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        alice_memory_id = await _exercise_remember(
            backend, text="alice note bob must not retire", capability=alice_capability
        )
        before = _one(
            await run(
                admin_conn,
                "SELECT valid_until, superseded_by FROM type::record('memory', $id)",
                {"id": _bare(alice_memory_id)},
            )
        )
        assert before["valid_until"] is None, "fixture: alice's note must start live (valid_until None)"
        with pytest.raises(governed.GovernedDenied):
            await _exercise_remember(
                backend, text="bob hostile replacement of alice's note",
                capability=bob_capability, supersedes=alice_memory_id,
            )
        after = _one(
            await run(
                admin_conn,
                "SELECT valid_until, superseded_by FROM type::record('memory', $id)",
                {"id": _bare(alice_memory_id)},
            )
        )
        assert after["valid_until"] is None, (
            "a DENIED supersede RETIRED alice's note — bob closed a foreign-owned row through the "
            "supersede path; the supersede-close must route through guarded_write (§2.5), not a bare "
            "UPDATE (cold-audit §F1)"
        )
        assert after["superseded_by"] is None, (
            "a DENIED supersede stamped superseded_by on alice's note — the foreign close leaked "
            "through the unguarded supersede path (cold-audit §F1: the supersession chain is corrupted)"
        )

    @observes_routing("lore_remember", "lore_remember")
    async def test_an_owner_can_supersede_close_its_own_row(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """POSITIVE CONTROL / DISCRIMINATOR for the supersede deny above (GREEN in BOTH worlds — the
        bare UPDATE at HEAD already closes an OWNER's row correctly, and a guarded build allows the
        owner too). alice (householded in the project keep) supersedes her OWN project-scoped note →
        the close SUCCEEDS: her old row carries ``valid_until`` (set) + ``superseded_by`` → the NEW
        note (chain correct). Without it, a build that special-cases the supersede-close to
        deny-everything would pass the deny pin above while breaking every legitimate supersession (a
        guard nobody can pass is as wrong as one nobody can fail)."""
        backend, _p, _k, admin_conn, _env, _keep = retrofit_world
        old_id = await _exercise_remember(
            backend, text="alice note to supersede", capability=alice_capability
        )
        new_id = await _exercise_remember(
            backend, text="alice replacement note", capability=alice_capability, supersedes=old_id
        )
        row = _one(
            await run(
                admin_conn,
                "SELECT valid_until, superseded_by FROM type::record('memory', $id)",
                {"id": _bare(old_id)},
            )
        )
        assert row["valid_until"] is not None, (
            "alice could not supersede-close her OWN note — the owner's legitimate supersede was "
            "denied (a build special-casing the supersede-close to deny-everything)"
        )
        assert row["superseded_by"] is not None and str(row["superseded_by"]).endswith(_bare(new_id)), (
            f"the superseded chain is wrong: old.superseded_by must point at the new note {new_id}, "
            f"got {row['superseded_by']!r}"
        )


class TestExplicitScopeArgumentIsGrantableValidated:
    """§2.4 (MISSING PIN 3) — an explicit ``scope=`` on ``remember`` is a PDP-VALIDATED REQUEST,
    checked by the SAME ``lorerunes.pdp._grantable`` predicate the SET_SCOPE action uses (61 D4(b)):
    the fixed scopes + the caller's OWN keeps are grantable; a keep the caller is NOT householded in
    → DENY with a teaching error naming ``lore-adm add-household``. The contract's other F4 pin
    (``test_a_hostile_owner_argument_does_not_move_the_stamp``) fuzzes only ``owner_principal=``; a
    caller-supplied ``scope=`` into a foreign keep is a DIFFERENT injection door (cross-keep
    injection / unauthorized scope assignment), and it was unpinned."""

    async def test_an_ungrantable_scope_argument_denies_with_a_teaching_error(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD (retrofit unbuilt — ``get_or_create_keyed`` stub / no ``scope`` validation).
        alice (householded ONLY in the project keep) tries to ``remember(scope=keep:<bob's keep>)`` —
        a keep she is not householded in. ``_grantable(alice, that keep)`` is False → ``GovernedDenied``
        with a teaching message naming ``lore-adm add-household``. REDDENS the wrong build the
        adversary names: ``remember`` writes the caller's ``scope=`` verbatim, never calling
        ``_grantable`` → a member files a note into a keep it is not in (cross-keep injection).
        MUTATION-PROOF (§9-rider-3, routing-is-not-sharing): patch ``lorerunes.pdp._grantable`` to
        ``return True`` → this DENY vanishes → the pin REDs, proving the write-time scope validation
        routes through ``_grantable``, not a hand-rolled copy (builder/adversary runs the mutation)."""
        backend, principal_store, keep_store, _admin, _env, _project_keep = retrofit_world
        # A keep alice is NOT householded in — kept by BOB, so alice cannot grant its scope.
        bob_keep = await keep_store.create_keep(keeper_email=_EMAIL_BOB, type="project", name="bobspace")
        with pytest.raises(governed.GovernedDenied) as denial:
            await _exercise_remember(
                backend, text="cross-keep injection attempt", capability=alice_capability,
                scope=pdp.keep_scope(_bare(str(bob_keep.id))),
            )
        assert "lore-adm add-household" in str(denial.value), (
            f"the deny must TEACH the fix (name `lore-adm add-household`, design §2.4), got: "
            f"{denial.value!r}"
        )

    async def test_a_grantable_scope_argument_is_accepted_and_applied(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """⚠ RED at HEAD. THE POSITIVE CONTROL: a GRANTABLE explicit ``scope=`` (a fixed scope —
        ``principal-private`` is always grantable, ``_grantable`` returns True) is ACCEPTED and the
        stored row carries THAT scope. Without it, a build that denies EVERY explicit ``scope=`` (or
        one that IGNORES it and writes the default project scope) would pass the deny pin above.
        REDDENS both: a deny-everything build (the write fails) AND an ignore-scope build (the stored
        scope is the project keep, not ``principal-private``)."""
        backend, _p, _k, admin_conn, _env, _project_keep = retrofit_world
        memory_id = await _exercise_remember(
            backend, text="alice private via explicit scope", capability=alice_capability,
            scope="principal-private",
        )
        row = _one(
            await run(admin_conn, "SELECT scope FROM type::record('memory', $id)", {"id": _bare(memory_id)})
        )
        assert row["scope"] == "principal-private", (
            f"a grantable explicit scope= (principal-private) was not applied — got scope={row['scope']!r} "
            f"(a build that ignores scope= and writes the default project keep, or denies all scope=)"
        )


# =========================================================================== #
# RES-2 (cold-audit §RES) — the memory close paths WIRE A REAL AuditStore so an admin BYPASS is
# AUDITED (the §9 erase-the-trail shape, from the consumer side). Authored by contract-63a-iii.
# =========================================================================== #


class TestMemoryBypassCloseIsAudited:
    """RES-2 — a memory CLOSE that is an admin BYPASS (a close a member could not make →
    ``requires_audit`` fires) leaves a trail: exactly +1 ``audit`` row. At HEAD ``dd5c9b2``
    ``invalidate`` calls ``guarded_write(..., audit=None)`` and the supersede-close is an ungoverned
    bare UPDATE, so an admin bypass close runs UNAUDITED (0 rows) — the §9 'compromised admin erases
    its trail' shape (design §10.6 rider ii). Companion to the substrate pin
    ``TestGuardedWriteRefusesAnUnauditedBypass`` (which REFUSES an unaudited bypass at the seam): the
    memory consumer must therefore SUPPLY a real ``AuditStore`` on its bypass-reachable close paths —
    the natural shape is the backend building its own from its connection params (mirroring the
    ``LocalMemoryBackend.handle`` accessor idiom, §10.6 rider v), so ``build_memory_backend`` needs
    NO new argument. Quantified over BOTH close verbs (invalidate + supersede) per the QUANTIFIER LAW.
    ⚠ The +1-audit-row POSITIVE CONTROL at the SUBSTRATE seam (a bypass WITH a real store appends one
    row) is the unchanged ``TestGuardedWriteComposesAudit`` pin; here the property is proven end-to-end
    through the real memory consumer."""

    async def test_an_admin_bypass_invalidate_appends_exactly_one_audit_row(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """⚠ RED before the 63a-iii fix (measured at ``dd5c9b2``). carol (ADMIN, AllRows) invalidates
        ALICE's project-scoped note — a bypass a member could not make (``requires_audit`` fires) →
        exactly +1 ``audit`` row lands. At HEAD ``invalidate`` passes ``audit=None`` so the bypass runs
        UNAUDITED (0 rows). REDDENS a build whose invalidate does not wire a real ``AuditStore`` (no
        trail for an admin bypass — RES-2 / §9)."""
        backend, principal_store, _k, admin_conn, env, _keep = retrofit_world
        # carol: an ADMIN principal (AllRows) — the bypass actor. Minted here (retrofit_world seeds
        # only alice+bob members); her capability is a REAL registry mint verified by resolve_subject.
        await principal_store.create(email="carol@example.com", role="admin")
        audit_store = _build_audit_store(env)
        await audit_store.ensure_ready()  # the `audit` table exists in BOTH worlds → the count is defined
        try:
            alice_id = await _exercise_remember(
                backend, text="alice note carol will retire", capability=alice_capability
            )
            before = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL"))
            async with _minted_credential(
                retrofit_world, email="carol@example.com", agent_name="carol_admin"
            ) as carol_capability:
                await _exercise_invalidate(backend, memory_id=alice_id, capability=carol_capability)
            after = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL"))
            assert after == before + 1, (
                f"an admin bypass invalidate must append exactly ONE audit row (the trail), "
                f"before={before} after={after} — the memory close path did not wire a real AuditStore "
                f"(RES-2 / §9 erase-the-trail); a bypass with no sink must not run silently"
            )
        finally:
            await audit_store.close()

    async def test_an_admin_bypass_supersede_close_appends_exactly_one_audit_row(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """⚠ RED before the 63a-iii fix (``dd5c9b2``) — the supersede twin (quantifier over BOTH close
        verbs). carol (ADMIN) supersedes ALICE's note: her supersede-CLOSE of alice's row is an admin
        bypass → +1 ``audit`` row. At HEAD the supersede-close is a bare ungoverned UPDATE (no guard,
        no audit) → 0 rows. REDDENS a build whose supersede-close does not route through
        ``guarded_write`` WITH a real ``AuditStore`` (cold-audit §F1 supersede leg + RES-2 compounded:
        the admin supersede leaves neither a guard nor a trail)."""
        backend, principal_store, _k, admin_conn, env, _keep = retrofit_world
        await principal_store.create(email="carol@example.com", role="admin")
        audit_store = _build_audit_store(env)
        await audit_store.ensure_ready()
        try:
            alice_id = await _exercise_remember(
                backend, text="alice note carol will supersede", capability=alice_capability
            )
            before = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL"))
            async with _minted_credential(
                retrofit_world, email="carol@example.com", agent_name="carol_admin"
            ) as carol_capability:
                await _exercise_remember(
                    backend, text="carol replacement of alice's note",
                    capability=carol_capability, supersedes=alice_id,
                )
            after = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL"))
            assert after == before + 1, (
                f"an admin bypass supersede-close must append exactly ONE audit row, before={before} "
                f"after={after} — the supersede-close did not route through guarded_write WITH a real "
                f"AuditStore (cold-audit §F1 supersede leg + RES-2)"
            )
        finally:
            await audit_store.close()

    async def test_a_member_self_close_appends_no_audit_row(
        self, retrofit_world: Any, alice_capability: _Credential
    ) -> None:
        """DISCRIMINATOR (before==after only when it SHOULD — fixtures-must-discriminate): alice
        invalidates her OWN note — NOT a bypass (``requires_audit`` False) → ZERO audit rows. GREEN in
        BOTH worlds; proves the +1 above is the BYPASS being audited, not every close writing a row. A
        build that audits EVERY close (or NONE) reds against one of these three legs."""
        backend, _p, _k, admin_conn, env, _keep = retrofit_world
        audit_store = _build_audit_store(env)
        await audit_store.ensure_ready()
        try:
            alice_id = await _exercise_remember(
                backend, text="alice note alice will retire", capability=alice_capability
            )
            before = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL"))
            await _exercise_invalidate(backend, memory_id=alice_id, capability=alice_capability)
            after = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL"))
            assert after == before, (
                f"a member closing its OWN note (not a bypass, requires_audit False) appended an audit "
                f"row (before={before} after={after}) — only an admin BYPASS is audited, never a "
                f"legitimate self-close"
            )
        finally:
            await audit_store.close()


# --------------------------------------------------------------------------- #
# capability fixtures (register real owned agents so recall/remember have a credential).
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture()
async def alice_capability(retrofit_world: Any) -> AsyncIterator[_Credential]:
    async with _minted_credential(
        retrofit_world, email=_EMAIL_ALICE, agent_name="alice_worker"
    ) as credential:
        yield credential


@pytest_asyncio.fixture()
async def bob_capability(retrofit_world: Any) -> AsyncIterator[_Credential]:
    async with _minted_credential(
        retrofit_world, email=_EMAIL_BOB, agent_name="bob_worker"
    ) as credential:
        yield credential


@asynccontextmanager
async def _minted_credential(
    retrofit_world: Any, *, email: str, agent_name: str
) -> AsyncIterator[_Credential]:
    """Register an owned agent for ``email`` (62's ``register`` mint) and yield the TOOL-LAYER
    :class:`_Credential` the ``_exercise_*`` seam resolves to a ``Subject`` (§10.5). The
    ``AgentRegistry`` is kept OPEN for the test's duration — ``resolve_subject`` verifies the
    capability against it (62's ``verify_capability``/``stamp_owner`` seam) — and closed on
    teardown. The principal/keep stores are the SAME live instances ``retrofit_world`` built on the
    ONE unified DB, so the resolved Subject reads the same identities the backend writes against."""
    from loremaster.agents import AgentRegistry

    _backend, principal_store, keep_store, _admin, env, _keep = retrofit_world
    principal = await principal_store.get_by_email(email)
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        await registry.ensure_ready()  # the agent table lives on the SAME unified DB as the backend
        result = await registry.register(
            agent_name, session="s1", role="worker", owner_principal_id=_bare(str(principal.id))
        )
        token = getattr(result, "capability", None)
        assert token, "capability mint unbuilt (62 wave 2)"
        yield _Credential(
            email=email,
            token=str(token),
            registry=registry,
            principal_store=principal_store,
            keep_store=keep_store,
        )
    finally:
        await registry.close()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _one(rows: Any) -> Any:
    assert rows, f"expected one row, got {rows!r}"
    return rows[0]


def _count(rows: Any) -> int:
    """The ``count`` of a ``SELECT count() … GROUP ALL`` result (0 on an empty table)."""
    return rows[0]["count"] if rows else 0


def _bare(record_id: str) -> str:
    return record_id.partition(":")[2] or record_id


def _build_audit_store(env: Any) -> Any:
    """Construct an :class:`~loremaster.audit.AuditStore` on the SAME unified test DB (the
    ``test_governed_substrate_63a._build_audit_store`` idiom — a test-fixture CONSTRUCTOR, not
    policy, so mirroring it is trivia not a §6 clone). DRY note (contract-63a-iii): the shared home
    would be ``_governed_contract`` (out of this contract's writable set); folding the two local
    copies there is a cheap follow-up, flagged in the report's Reuse ledger."""
    from loremaster.audit import AuditStore
    from pydantic import SecretStr

    password = env.password if isinstance(env.password, SecretStr) else SecretStr(str(env.password))
    return AuditStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=password
    )


def _memory_case() -> Any:
    from _governed_contract import GovernedTableCase

    return GovernedTableCase(
        table=MEMORY_TABLE,
        make_ddl=lambda: surreal_schema.generate_memory_ddl(dim=_DIM),
        seed_legacy=seed_memory_governed,
        seed_governed=seed_memory_governed,
        read_verbs=("recall",),
        write_verbs=("remember", "invalidate"),
    )
