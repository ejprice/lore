"""Contract — packet 63a: the MEMORY RETROFIT — memory is the substrate's FIRST real consumer
(design §0(a)/§1.1). RED before the 63a build; authored by ``contract-63a`` (Opus 4.8 contract
author — tests ONLY).

SPEC: ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §0 item 2 (lore_remember/lore_recall
+ ``LocalMemoryBackend.remember``/``invalidate`` route through the substrate — stamp on write,
filter on read; identity-less call DENIES — removed-behavior 1), §2.4 (default scope = the project
keep — §10-N), §3.2 (the four families F2/F3/F4), §6 (the §9 isolation target).

⚠ FORK 5 (REPORT-contract-63a.md): the EXACT seam by which identity flows into the retrofitted
recall/remember (a ``capability=`` arg resolved to a Subject inside, vs a ``subject=`` arg) is a
builder/design ruling. Following the 62 ``_call_stamp_owner`` precedent, the retrofitted call is
ISOLATED in ``_exercise_recall`` / ``_exercise_remember`` so a signature ruling stays a ONE-function
edit and traps no build (C-DEF). The design's stated shape is ``capability=``; the pins assert
OBSERVABLE behaviour (isolation, owner stamp, default scope, identity-less DENY), never the wiring.

⚠ THE RUNTIME ROUTING OBSERVATION IS BEHAVIOURAL, not a spy (#420 memory leg): recall routes
through ``read_filter`` IFF cross-principal isolation holds (F3 — B cannot see A's private rows);
remember routes through ``stamp_owner``/``guarded_write`` IFF the stored owner is the RESOLVED
subject and a hostile ``owner_*=`` arg is ignored (F4). A verb that "routes" but whose effect is
absent reds here — routing is proven by its effect, never asserted.

STORE LAW cited: §1.4 (option<> dirty rows), §2 (record<> links; CONTENT). Live TEST store
``ws://127.0.0.1:18000`` (NEVER :18500); per-test unique DB, reaped; NO skip marker.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    MEMORY_TABLE,
    absent_scope,
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


class TestF3ServedCountEqualsServedSet:
    """F3 / trust-doctrine Leg 1 — the served COUNT of a filtered read equals the served SET size.
    A count over the UNFILTERED table beside a filtered listing is a FALSE CLEAR."""

    async def test_read_filter_count_equals_read_filter_set_size(self, oracle_conn: Any) -> None:
        """⚠ RED at HEAD (``read_filter`` NotImplementedError). ``SELECT count() WHERE <read_filter>``
        must equal the SIZE of ``SELECT id WHERE <read_filter>`` — same predicate, both filtered.
        REDDENS a build that counts over the whole table (``SELECT count() FROM memory``) beside a
        filtered id listing (the exact false-clear §6 item 2 forbids)."""
        subject = member("alice", "ag_a1", frozenset({pdp.keep_scope("k1")}))
        fragment, params = governed.read_filter(subject, MEMORY_TABLE)
        id_rows = await run(oracle_conn, f"SELECT id FROM {MEMORY_TABLE} WHERE {fragment}", params)
        count_rows = await run(
            oracle_conn, f"SELECT count() FROM {MEMORY_TABLE} WHERE {fragment} GROUP ALL", params
        )
        served_set_size = len(id_rows) if isinstance(id_rows, list) else 0
        served_count = count_rows[0]["count"] if count_rows else 0
        assert served_count == served_set_size, (
            f"served count {served_count} != served set size {served_set_size} — the count must be "
            f"OVER THE FILTERED set (Leg 1), never the unfiltered table"
        )


# =========================================================================== #
# The RETROFIT tool wiring — the runtime routing observation (behavioural), identity-less DENY,
# default scope, and F4 anti-injection. Uses the real LocalMemoryBackend.
# =========================================================================== #


@pytest_asyncio.fixture()
async def retrofit_world() -> Any:
    """A real ``LocalMemoryBackend`` on a fresh DB + a PrincipalStore/KeepStore + alice & bob
    principals + a canonical project keep (``key='project:lore'``, alice's household) — enough to
    exercise the retrofitted recall/remember over live behaviour."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    backend = await build_memory_backend(env)
    admin_conn = await connect_admin(env)
    await apply_ddl(admin_conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
    await principal_store.create(email=_EMAIL_ALICE, role="member")
    await principal_store.create(email=_EMAIL_BOB, role="member")
    project_keep = await keep_store.create_keep(keeper_email=_EMAIL_ALICE, type="project", name="lore")
    try:
        yield backend, principal_store, keep_store, admin_conn, env, project_keep
    finally:
        await admin_conn.close()
        await backend.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


async def _exercise_remember(backend: Any, *, text: str, capability: str, **kwargs: Any) -> Any:
    """The ONE place the RETROFITTED ``remember`` is called (FORK 5 — isolated per the 62
    ``_call_stamp_owner`` precedent; the design's shape is ``capability=``). A signature ruling is a
    ONE-function edit. RED at HEAD: ``remember`` has no ``capability`` param → TypeError."""
    return await backend.remember(text, kind="fact", capability=capability, **kwargs)


async def _exercise_recall(backend: Any, *, query: str, capability: str) -> Any:
    """The ONE place the RETROFITTED ``recall`` is called (FORK 5 — isolated). RED at HEAD."""
    return await backend.recall(query, capability=capability)


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
        self, retrofit_world: Any, alice_capability: str
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
        self, retrofit_world: Any, alice_capability: str
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
        self, retrofit_world: Any, alice_capability: str
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
        self, retrofit_world: Any, alice_capability: str, bob_capability: str
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


# --------------------------------------------------------------------------- #
# capability fixtures (register real owned agents so recall/remember have a credential).
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture()
async def alice_capability(retrofit_world: Any) -> str:
    return await _mint_capability(retrofit_world, email=_EMAIL_ALICE, agent_name="alice_worker")


@pytest_asyncio.fixture()
async def bob_capability(retrofit_world: Any) -> str:
    return await _mint_capability(retrofit_world, email=_EMAIL_BOB, agent_name="bob_worker")


async def _mint_capability(retrofit_world: Any, *, email: str, agent_name: str) -> str:
    """Register an owned agent for ``email`` and return its raw capability (62's register mint)."""
    from loremaster.agents import AgentRegistry

    _backend, principal_store, _keep_store, _admin, env, _keep = retrofit_world
    principal = await principal_store.get_by_email(email)
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        await registry.ensure_ready()  # the agent table lives on the SAME unified DB as the backend
        result = await registry.register(
            agent_name, session="s1", role="worker", owner_principal_id=_bare(str(principal.id))
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt (62 wave 2)"
        return str(capability)
    finally:
        await registry.close()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _one(rows: Any) -> Any:
    assert rows, f"expected one row, got {rows!r}"
    return rows[0]


def _bare(record_id: str) -> str:
    return record_id.partition(":")[2] or record_id


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
