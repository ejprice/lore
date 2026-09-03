"""Contract — packet 63b wave i-a: THE F5 RUNTIME ROOT-FIX (design
``docs/design/2026-09-03-packet63b-design.md`` §1 + §5.1 ADDENDUM; task ``571ef1a`` / finding #449).
Authored by ``contract-63b-i-a`` (Opus 4.8 contract author; CONTRACT TESTS ONLY — no production).

WHAT F5 WAS AT ``e4b8945`` AND WHY IT WAS ROOT-BROKEN (design §1.1). The runtime layer read the
STATEMENT to infer the EFFECT: ``_mutation_verb_for_table`` matched a bounded verb regex
(UPSERT/UPDATE/DELETE/REMOVE) over the resolved statement, and ``governed_exempt(name)`` blessed
EVERY mutation in its block. Two wrong builds passed every 63a gate (adversary-63a-v3 §R4):
  R4-a — ``UPDATE memory SET scope = $s WHERE scope IS NONE OR scope = $victim`` seizes OWNED rows
         and passes a ``WHERE scope IS NONE`` SUBSTRING check.
  R4-c — ``INSERT … ON DUPLICATE KEY UPDATE`` / ``CREATE`` / ``RELATE`` returns None from the verb
         regex → never recorded → deny-by-default cannot fire.
Both are ONE class: the instrument reads an OPEN SET (statements) to infer the effect — the reach
law (CLAUDE.md "the instrument lesson"). The root fix STOPS READING STATEMENTS.

THE ROOT FIX THIS CONTRACT PINS (design §1.2–§1.5 + §5.1 Q1):
  §1.2  detection is an EFFECT — a per-SDK-call before/after STATE DIFF of the governed population
        (``SELECT *`` row deltas + ``INFO FOR TABLE`` schema delta). No verb list, no shape regex,
        no statement classification. Verb-agnostic, shape-agnostic, table-generic.
  §1.3  the observer's REACH is the ``_sdk_guard`` hook (the SDK connection CLASS), armed by the
        F5 battery — NOT a module list. ``extra_modules`` / ``seam_modules_for_tree_allowlist`` /
        ``test_the_observer_patch_set_is_derived_from_the_allowlist`` are RETIRED/DELETED.
  §1.4  ``governed_exempt(name, *, statement)`` is STATEMENT-SCOPED: an observed exempt write is
        CLASSIFIED iff ALL FOUR legs hold — name ∧ golden-text (==token==observed) ∧ effect ∧ origin.
  §1.5  L1 is DEMOTED to a coverage FLOOR with a DERIVED keyword grammar; the population set is
        DERIVED from ``surreal_schema``; R4-a/R4-c pins are DELETED (their own instruction).
  §5.1  ``ensure_ready`` becomes an allowlisted DDL frame (schema-delta effect == the emitter's own
        output, no rows moved); ``_recreate_memory_table`` flips to ``runtime_observed=True`` and the
        battery drives ``rebuild_embeddings`` under observation, asserting the REMOVE→ensure_ready
        →replay arc.

RED-AT-``e4b8945`` isolates the UNBUILT INSTRUMENT (the 63b-i-a builder's GREEN), each for the
RIGHT reason (the effect instrument / hook seam / statement-scoped exempt / derived grammar /
population derivation are unbuilt — never a TypeError/parse error). The behavioural battery drives
the REAL memory backend / migrate verb over the LIVE test store and reads ``ObservedWrite.effect``
(None at HEAD — the old verb-observer never fills it) and the 4-leg classifier (2-leg at HEAD).

SUBSTRATE-SHAPE DECISIONS (contract-author authority; documented in REPORT-contract-63b-i-a.md,
lead may veto): (1) an allowlist entry's ``effect`` predicate takes the WHOLE ``ObservedEffect``
(rows + schema delta), not the literal ``Callable[[RowDelta], bool]`` §1.4 wrote — one field serves
a row entry AND a DDL frame (§5.1 Q1's schema-delta effect). (2) a DDL/label frame (``ensure_ready``
/ ``guarded_write``) carries ``l1_site=False`` — it has NO raw-literal L1 site, so the L1 ghost-check
excludes it (covered by the L2 effect leg + L2a ``function_calls_write_guard``).

The 63a-iv/63a-v F5 pins keyed on the RETIRED verb-based shapes (the 2-leg classifier controls, the
live-migration ``extra_modules`` leg, the L2b label-seam battery, the R4-a/R4-c bounds, the
observer-patch-set meta-pin) are DELETED/migrated in those modules as part of this wave (a test that
certifies the OLD world is a corpse; CLAUDE.md rename-law). This module is the SINGLE F5 contract
for the MEMORY table under the effect model. ``MEMORY_TREE_ALLOWLIST`` LIVES HERE (63a-v imports it).

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker
for an unreachable store — a LOUD failure, never a skip. pytest runs ``-n auto``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import _sdk_guard
import loremaster.governed as governed_mod
import loremaster.memory.local as local_mod
import loremaster.principals as principals_mod
import pytest
import pytest_asyncio
from _governed_contract import (
    MEMORY_TABLE,
    SURREALQL_MUTATION_KEYWORDS,
    SURREALQL_READ_KEYWORDS,
    SURREALQL_STATEMENT_KEYWORDS,
    ExemptToken,
    ObservedEffect,
    ObservedWrite,
    RowDelta,
    SchemaDelta,
    SchemaSnapshot,
    TreeMutationSite,
    TreeWriteAllowlistEntry,
    _raw_mutation_of_table,
    apply_ddl,
    classify_tree_observed_write,
    derive_surrealql_statement_keywords_from_corpus,
    function_calls_named,
    governed_populations,
    governed_table_raw_mutation_sites_in_tree,
    observe_governed_table_writes,
    schema_snapshot_from_info,
    store_handle,
)
from _surreal_harness import (
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.memory.ledger import MemoryLedger
from loremaster.memory.local import LocalMemoryBackend
from loremaster.store import surreal_schema
from loresigil.testing import FakeEmbedder

# The member-verb battery world + its exercisers, and the migration world (DRY — the ONE world each,
# never re-wired; imported by NAME as the 63a modules do).
from test_governed_migration_63a import migration_world  # noqa: F401 (fixture used by name)
from test_memory_retrofit_63a import (  # noqa: F401 (fixtures used by name)
    _exercise_invalidate,
    _exercise_recall,
    _exercise_remember,
    alice_capability,
    retrofit_world,
)

import lorerunes as pdp

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DIM = 8


def _rel(module: Any) -> str:
    """A module's repo-relative posix path — the key shape the whole-tree scanner emits."""
    return Path(module.__file__).resolve().relative_to(_REPO_ROOT).as_posix()


_LOCAL = _rel(local_mod)
_PRINCIPALS = _rel(principals_mod)
_GOVERNED = _rel(governed_mod)

# A direct governance Subject for the rebuild battery (mirrors test_schema_rebuild::_GOV_SUBJECT):
# an admin so a fixed ``scope="server"`` is grantable without wiring a keep household.
_GOV_SUBJECT = pdp.Subject(
    principal_id="ia_admin",
    agent_id="ia_agent",
    role=pdp.PRINCIPAL_ROLE_ADMIN,
    visible_keep_ids=frozenset(),
)

# The GOLDEN adjudicated migrate statement (design §1.4 — an oracle the adjudicator WROTE DOWN, not
# read from production, so leg 2 can red when the production statement drifts). ⚠ §1.9 item 1
# (adversary F-TRAP-2) — the adjudicated statement is a FUNCTION-LOCAL variable inside
# ``principals._migrate_memory_scope``: the 63b-i-a builder assigns
# ``stmt = f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"`` and passes it BOTH to
# ``governed_exempt(name, statement=stmt)`` AND to ``run_query(statement=stmt)`` — ONE source in
# code, derived at the entry's OWN site. It is NEVER a module constant
# ``principals.MIGRATE_MEMORY_SCOPE_STATEMENT``: the L1 whole-tree scan attributes a module-level
# literal to ``<module>`` scope, so a module constant is an L1 ORPHAN → RED (and R1 self-containment
# demands the literal live in the SAME symbol as the seam call + the exempt entry). Stated once
# (§1.9 item 1): an exempt-adjudicated statement lives in the function that EXECUTES it.
_MIGRATE_GOLDEN = f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"


def _normalise(statement: str) -> str:
    """Whitespace-collapse a SurrealQL statement for the golden compare (design §1.4 leg 2)."""
    return " ".join(statement.split())


# =========================================================================== #
# THE CONSTRUCTED ensure_ready ORACLE (design §1.9 item 4, SUPERSEDING the retired DDL-text regex
# _memory_ddl_object_names). The expected memory schema is the ENGINE's OWN rendering of
# generate_memory_ddl(dim) on a VIRGIN database — never a hand-model of the engine's implicit
# expansions (array-element field defs render as embedding[*]/embedding.*, measured — the exact
# #107/#131 "the test environment is a fiction" class the DDL-text regex fell to). A session-cached
# fixture (keyed by dim) mints one more harness DB, applies the SAME emitter, reads INFO FOR TABLE,
# and caches the SchemaSnapshot here so _effect_ensure_ready — called by the classifier, which cannot
# take a fixture arg — can read it. Trust-doctrine CONSTRUCTION, not reasoning: the oracle is the
# engine's own rendering of the same recipe, correct for every implicit expansion it has or will have.
# =========================================================================== #

_ENSURE_READY_ORACLE: dict[int, SchemaSnapshot] = {}


async def _read_memory_schema_snapshot(dim: int) -> SchemaSnapshot:
    """Apply ``generate_memory_ddl(dim)`` to a VIRGIN harness DB and return the engine's own rendered
    ``memory`` schema as a :class:`SchemaSnapshot` (design §1.9 item 4). Reaped on exit."""
    env = make_env(database=unique_database(), dim=dim)
    connection = await connect_admin(env)
    try:
        await apply_ddl(connection, surreal_schema.generate_memory_ddl(dim=dim), url=env.url)
        return schema_snapshot_from_info(await run(connection, f"INFO FOR TABLE {MEMORY_TABLE}"))
    finally:
        await connection.close()
        await drop_database(env)


@pytest_asyncio.fixture()
async def ensure_ready_oracle() -> SchemaSnapshot:
    """The CONSTRUCTED ensure_ready oracle (design §1.9 item 4). FUNCTION-scoped but the snapshot is
    CACHED in the module holder keyed by dim, so the virgin-DB apply happens ONCE per worker (a
    session-scoped async fixture would fight pytest-asyncio's function-scoped event loop under
    ``-n auto``). Populates the holder :func:`_effect_ensure_ready` reads; yields the snapshot for the
    non-vacuity pin. A test that CLASSIFIES an ``ensure_ready`` write MUST depend on this fixture."""
    oracle = _ENSURE_READY_ORACLE.get(_DIM)
    if oracle is None:
        oracle = await _read_memory_schema_snapshot(_DIM)
        _ENSURE_READY_ORACLE[_DIM] = oracle
    return oracle


# =========================================================================== #
# THE ADJUDICATED EFFECT PREDICATES (design §1.4) — each says what its frame is ALLOWED to do, over
# the WHOLE ObservedEffect. A golden EDITED to bless a seizure, or a frame that grows a second write
# with a different effect, reds the classifier's leg-3. Pure functions (unit-pinned below AND applied
# by the classifier via the allowlist entry).
# =========================================================================== #

_COL_SCOPE = "scope"
_COL_IMPORTANCE = "importance"
_COL_OWNER_PRINCIPAL = "owner_principal"
_COL_OWNER_AGENT = "owner_agent"


def _effect_migrate(effect: ObservedEffect) -> bool:
    """The migrate-governed backfill: EVERY changed row is an UPDATE of a previously-UNOWNED,
    NONE-scope row whose ONLY changed column is ``scope`` — a golden edited to bless
    ``OR scope = $victim`` reds here (the seized row HAD a scope/owner before). Schema unchanged."""
    if not effect.schema_delta.is_empty or not effect.row_deltas:
        return False
    for delta in effect.row_deltas:
        before = delta.before or {}
        if delta.kind != "updated":
            return False
        if before.get(_COL_SCOPE) is not None:
            return False
        if before.get(_COL_OWNER_PRINCIPAL) is not None or before.get(_COL_OWNER_AGENT) is not None:
            return False
        if delta.changed_columns != frozenset({_COL_SCOPE}):
            return False
    return True


def _effect_reinforce(effect: ObservedEffect) -> bool:
    """The reinforcement bump: every changed row is an UPDATE whose ONLY changed column is the
    NON-governed ``importance`` (§10.9-C). A build that also touches a governed column reds."""
    if not effect.schema_delta.is_empty or not effect.row_deltas:
        return False
    return all(
        delta.kind == "updated" and delta.changed_columns == frozenset({_COL_IMPORTANCE})
        for delta in effect.row_deltas
    )


def _effect_upsert(effect: ObservedEffect) -> bool:
    """The create / ledger-replay UPSERT: a non-empty row effect (created or updated memory rows),
    schema unchanged. (i-a keeps this coarse; i-b WIDENS it — the created row owned by the subject +
    the predecessor-close delta — a per-entry DATA change, never the instrument, §5.1 Q2 ii.)"""
    if not effect.schema_delta.is_empty or not effect.row_deltas:
        return False
    return all(delta.kind in {"created", "updated"} for delta in effect.row_deltas)


def _effect_guarded_write(effect: ObservedEffect) -> bool:
    """``guarded_write`` (invalidate / the current supersede-close): EXACTLY ONE governed row
    changed or deleted, schema unchanged (§5.1 Q2 ii — its standalone-caller contract)."""
    if not effect.schema_delta.is_empty or len(effect.row_deltas) != 1:
        return False
    return effect.row_deltas[0].kind in {"updated", "deleted"}


def _effect_recreate(effect: ObservedEffect) -> bool:
    """``_recreate_memory_table``'s REMOVE TABLE: a NON-EMPTY schema delta (the table + its
    fields/indexes removed). A REMOVE with an empty schema delta would mean nothing was dropped."""
    return not effect.schema_delta.is_empty


def _effect_ensure_ready(effect: ObservedEffect) -> bool:
    """The ``ensure_ready`` DDL apply (design §5.1 Q1 / §1.9 item 4): NO ROWS move AND the after-schema
    EQUALS the CONSTRUCTED oracle (``generate_memory_ddl`` on a virgin DB, engine-rendered) by DICT
    EQUALITY — no regex, no hand-model of implicit expansions (the retired ``_memory_ddl_object_names``
    class). Satisfies the virgin (no table → full schema == oracle) AND re-apply (idempotent,
    after-schema still == oracle) cases. The oracle is populated by the ``ensure_ready_oracle``
    fixture; classifying an ensure_ready write without it is a LOUD raise, never a vacuous False."""
    if effect.row_deltas:
        return False  # a DDL frame that MOVES rows is RED (short-circuit — no oracle needed)
    oracle = _ENSURE_READY_ORACLE.get(_DIM)
    if oracle is None:
        raise RuntimeError(
            "the ensure_ready oracle is not populated — a test classifying an ensure_ready write must "
            "depend on the `ensure_ready_oracle` fixture (design §1.9 item 4); this is a LOUD failure, "
            "never a vacuous False"
        )
    return effect.schema_after is not None and effect.schema_after == oracle


# =========================================================================== #
# THE WHOLE-TREE DENY-BY-DEFAULT ALLOWLIST (design §1.4/§1.5 — widened with the golden ``statement``
# + the ``effect`` predicate; the 4 site-backed L1 entries + 2 DDL/label frames). LIVES HERE; 63a-v
# imports it. Every 63b-new frame carries an ``effect`` predicate (design §1.4 — REQUIRED).
# =========================================================================== #

_UPSERT_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_LOCAL, "_upsert_fragment", "UPSERT"),
    justification=(
        "deterministic-id UPSERT; the CREATE caller folds the owner pair into the id (#439) so it "
        "cannot name a foreign row, the REPLAY caller uses the STORED id (RES-1)."
    ),
    pin="test_a_non_owner_reremember_mints_a_distinct_id_and_does_not_seize_or_rescope",
    frames=("remember", "_replay_record"),
    effect=_effect_upsert,
)
_REINFORCE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_LOCAL, "_reinforce", "UPDATE"),
    justification="read-side-effect on the NON-governed importance column only (§10.9-C).",
    pin="test_the_reinforce_update_sets_only_the_importance_column",
    frames=("_reinforce",),
    effect=_effect_reinforce,
)
_RECREATE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_LOCAL, "_recreate_memory_table", "REMOVE"),
    justification="boot/admin table recreate, reachable ONLY via rebuild_embeddings (RES-1).",
    pin="test_recreate_memory_table_is_reachable_only_from_rebuild_embeddings",
    frames=("_recreate_memory_table",),
    effect=_effect_recreate,
    # §5.1 Q1 / §1.6-vi: FLIPPED to observed (was False at 63a-v under the #445 bound). The battery
    # drives rebuild_embeddings under observation, so #445 shrinks to nothing on the memory table.
    runtime_observed=True,
)
_MIGRATE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_PRINCIPALS, "_migrate_memory_scope", "UPDATE"),
    justification=(
        "the migrate-governed backfill (§1.4 statement-scoped exempt). Admin-CLI-only; the golden "
        "statement can only touch UNMIGRATED NONE-scope rows; idempotent; R4 driver-routed. NOT "
        "member-reachable → attributes via governed_exempt('migrate-governed', statement=…)."
    ),
    pin="test_migrate_memory_scope_updates_only_none_scope_rows",
    frames=("_migrate_memory_scope",),
    exempt_name="migrate-governed",
    statement=_MIGRATE_GOLDEN,
    effect=_effect_migrate,
)
_ENSURE_READY_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_LOCAL, "ensure_ready", "DEFINE"),
    justification=(
        "the boot/rebuild memory DDL apply (§5.1 Q1 / §1.9 item 4). A LABEL frame "
        "(write_guard('ensure_ready')) with no raw literal — it passes generate_memory_ddl(), not a "
        "literal — so l1_site=False; its effect is the after-schema == the CONSTRUCTED oracle "
        "(generate_memory_ddl on a virgin DB, engine-rendered — dict equality, no regex), no rows moved."
    ),
    pin="test_ensure_ready_carries_the_ddl_frame_label_and_effect",
    frames=("ensure_ready",),
    effect=_effect_ensure_ready,
    l1_site=False,
)
_GUARDED_WRITE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_GOVERNED, "guarded_write", "UPDATE"),
    justification=(
        "the shared single-row guarded WRITE/DELETE (invalidate + the current supersede-close). A "
        "LABEL frame in governed.py building its mutation dynamically — no raw literal, l1_site=False; "
        "its effect is exactly one governed row changed or deleted (§5.1 Q2 ii)."
    ),
    pin="test_guarded_write_carries_its_label_and_one_row_effect",
    frames=("guarded_write",),
    effect=_effect_guarded_write,
    l1_site=False,
)
MEMORY_TREE_ALLOWLIST: tuple[TreeWriteAllowlistEntry, ...] = (
    _UPSERT_ENTRY,
    _REINFORCE_ENTRY,
    _RECREATE_ENTRY,
    _MIGRATE_ENTRY,
    _ENSURE_READY_ENTRY,
    _GUARDED_WRITE_ENTRY,
)

#: The site-backed (L1-derivable) subset — the ONLY entries the whole-tree L1 containment ghost-check
#: applies to (a DDL/label frame has no raw literal, so it is not in the derived set). 63a-v imports
#: THIS for its ghost leg.
L1_SITE_ENTRIES: tuple[TreeWriteAllowlistEntry, ...] = tuple(
    entry for entry in MEMORY_TREE_ALLOWLIST if entry.l1_site
)
L1_ALLOWLISTED_SITES = frozenset(entry.site for entry in L1_SITE_ENTRIES)


# =========================================================================== #
# BATTERY DRIVERS — the ONE place each governed flow is exercised under the effect observer. RED at
# HEAD: the observer's ``.effect`` is None (the old verb-observer never fills it). GREEN on the build.
# =========================================================================== #


async def _observed_member_writes(backend: Any, capability: Any) -> list[ObservedWrite]:
    """Drive the member-verb battery (create → reinforce → guarded close) over the LIVE store under
    the effect observer, and return every observed governed write. The remembered note is seeded
    BELOW the importance ceiling (importance=0.1) so the reinforcement bump CHANGES the value —
    without that the reinforce effect is empty and its coverage leg is vacuous (§5.1 Q2 ii)."""
    with observe_governed_table_writes(MEMORY_TABLE) as observed:
        note_id = await _exercise_remember(
            backend, text="f5 ia battery note alpha", capability=capability, importance=0.1
        )
        await _exercise_recall(backend, query="f5 ia battery note alpha", capability=capability)
        await _exercise_invalidate(backend, memory_id=note_id, capability=capability)
    return list(observed)


@pytest_asyncio.fixture()
async def rebuild_world() -> Any:
    """A ledger-backed ``LocalMemoryBackend`` on a fresh DB with ONE stored+ledgered memory note —
    enough to drive ``rebuild_embeddings`` (REMOVE → ensure_ready → replay) under observation. The
    retrofit fixture's backend is ledger-LESS (rebuild is a no-op there), so this builds a ledgered
    one the test_schema_rebuild idiom (``MemoryLedger(...)`` + ``ledger=``). Reaped on exit."""
    env = make_env(database=unique_database(), dim=_DIM)
    ledger = MemoryLedger(str(Path(env.database + ".memory.db")))
    backend = LocalMemoryBackend(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=_DIM,
        user=env.user,
        password=env.password,
        embedder=FakeEmbedder(dim=_DIM),
        existing_chunks=_no_chunks,
        ledger=ledger,
    )
    await backend.ensure_ready()
    await backend.remember(
        "a durable ledgered note for the rebuild arc", kind="fact", subject=_GOV_SUBJECT, scope="server"
    )
    try:
        yield backend, ledger, env
    finally:
        await backend.close()
        ledger.close()
        await drop_database(env)
        Path(env.database + ".memory.db").unlink(missing_ok=True)


async def _no_chunks(_keys: Any) -> set[str]:
    return set()


# =========================================================================== #
# §1.2 — DETECTION IS AN EFFECT, NOT A STATEMENT CLASSIFICATION.
# =========================================================================== #


class TestDetectionIsAnEffectNotAStatement:
    """§1.2 — the property is "this SDK call CHANGED the governed population's state", observed as a
    before/after STATE DIFF; no verb list, no shape regex, no statement text is consulted for
    detection. RED at HEAD (the verb-observer fills no ``.effect`` and misses exotic verbs)."""

    async def test_every_observed_member_write_carries_a_state_diff_effect(
        self, retrofit_world: Any, alice_capability: Any  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — the observer records ``.effect`` (an ObservedEffect state diff) for every
        observed governed write. At HEAD ``ObservedWrite.effect`` is None (the verb-observer never
        diffs state). ANTI-VACUITY: the battery drove real writes, so ``observed`` is non-empty and
        each carries a NON-empty effect (a governance event). REDDENS a build that reverts to
        statement-classified detection (effect stays None) or observes no-effect writes."""
        backend, *_rest = retrofit_world
        observed = await _observed_member_writes(backend, alice_capability)
        assert observed, "the effect battery observed NO governed write — the observer is blind"
        no_effect = [o.label for o in observed if o.effect is None]
        assert not no_effect, (
            f"observed governed writes with NO state-diff effect (detection is still statement-based, "
            f"not effect-based — §1.2 root fix unbuilt): {no_effect}"
        )
        empty = [o.label for o in observed if o.effect is not None and o.effect.is_empty]
        assert not empty, (
            f"observed writes recorded with an EMPTY effect (a no-effect write is NOT a governance "
            f"event, §1.2 self-attack row 1 — the observer must record only real state changes): {empty}"
        )

    async def test_detection_is_verb_agnostic_insert_create_relate_are_observed(
        self, migration_world: Any  # noqa: F811 (pytest fixture imported by name)
    ) -> None:
        """⚠ RED at HEAD (§1.6 rider i) — an INSERT..ON DUPLICATE / CREATE / RELATE that LANDS a
        governed memory row is OBSERVED (it moved state) and, carrying NO label/exempt, UNCLASSIFIED
        (deny-by-default). At HEAD the verb-observer returns None for these verbs → never observed →
        this reds. POSITIVE CONTROL: an in-set UPDATE under a passing label classifies. The exotic
        writes run DIRECTLY on the store connection (no production frame) — an escape by construction."""
        _p, _k, connection, env = migration_world
        exotic = (
            f"CREATE type::record('{MEMORY_TABLE}', 'verb_create') CONTENT "
            f"{{ note_text: 'x', kind: 'fact', source: {{ kind: 'test', trust: 'experiential' }}, "
            f"created_at: time::now(), embedding: {[0.0] * _DIM}, scope: 'seized' }}"
        )
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            await run(connection, exotic)
        landed = [o for o in observed if o.effect is not None and not o.effect.is_empty]
        assert landed, (
            "a CREATE that LANDED a governed memory row was NOT observed as an effect — detection is "
            "still verb-keyed (the R4-c class), so an exotic-verb seizure is invisible (§1.2/§1.6-i)"
        )
        unclassified = [o for o in landed if not classify_tree_observed_write(o, MEMORY_TREE_ALLOWLIST)]
        assert unclassified, (
            "the label-less CREATE was CLASSIFIED — deny-by-default is not firing on an effect that "
            "carries no write_guard label and no valid exempt token (§1.2 verb-agnostic detection)"
        )

    async def test_a_no_effect_write_is_not_a_governance_event(self, migration_world: Any) -> None:  # noqa: F811 (pytest fixture imported by name)
        """§1.2 self-attack row 1 — a write that changes NOTHING (``SET scope = scope`` on the
        migrated row) produces an EMPTY effect and is NOT a governance event. First backfill the row
        so it HAS a scope, then a self-assign moves no state. GREEN-VACUOUS at HEAD (no ``.effect`` to
        be non-empty) and GREEN on the build (the self-assign genuinely moves no state); it
        DISCRIMINATES against a build whose observer records a no-op write by verb regardless of
        effect (→ a false governance event → RED)."""
        _p, _k, connection, env = migration_world
        # give the legacy row a scope, so a subsequent self-assign is genuinely a no-op.
        await run(
            connection,
            f"UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'keep:k'",
        )
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            await run(
                connection,
                f"UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = {_COL_SCOPE}",
            )
        events = [o for o in observed if o.effect is not None and not o.effect.is_empty]
        assert not events, (
            f"a no-effect write (SET scope = scope) was recorded as a governance event — detection is "
            f"not effect-based (it counts the statement, not the state change; §1.2 self-attack): "
            f"{[(o.verb, o.statement) for o in events]}"
        )

    async def test_a_write_inside_a_rolled_back_txn_is_not_observed(
        self, migration_world: Any  # noqa: F811 (pytest fixture imported by name)
    ) -> None:
        """§1.2 self-attack row 4 — a mutation inside a transaction that ROLLS BACK lands nothing, so
        the before/after diff is empty and nothing is observed (deny-by-default asks "did an
        unattributed write LAND"). A ``THROW`` after an UPDATE aborts the whole txn (store-ref §3).
        GREEN-VACUOUS at HEAD (no ``.effect`` to be non-empty) and GREEN on the build (the rollback
        landed nothing → empty effect); it DISCRIMINATES against a build whose observer records
        intra-txn intermediate state (→ a landed effect → RED). ANTI-VACUITY: the control asserts the
        rollback truly landed nothing (the scope is unchanged), so 'no landed effect' is not free."""
        _p, _k, connection, env = migration_world
        await run(
            connection,
            f"UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'keep:before'",
        )
        rolled_back = (
            f"BEGIN;\nUPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'seized';\n"
            'THROW "abort";\nCOMMIT;\n'
        )
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            try:
                # `run` is a single `.query()` (validates statement[0] only, store-ref §3): the THROW
                # may or may not surface as a Python exception, but the txn rolls back server-side
                # either way. Tolerate both; the control below proves the rollback actually happened.
                await run(connection, rolled_back)
            except Exception:  # noqa: BLE001 - the point is the ROLLBACK landed nothing, not the raise
                pass
        row = await run(
            connection, f"SELECT {_COL_SCOPE} FROM type::record('{MEMORY_TABLE}', 'legacy')"
        )
        assert row and row[0][_COL_SCOPE] == "keep:before", (
            f"control: the THROW did not roll the txn back (the seizure LANDED) — the fixture cannot "
            f"test rollback invisibility, so 'no landed effect' below would be vacuous: {row!r}"
        )
        landed = [o for o in observed if o.effect is not None and not o.effect.is_empty]
        assert not landed, (
            f"a mutation inside a ROLLED-BACK transaction was observed as a landed effect — the "
            f"observer diffs the STATEMENT, not the committed STATE (§1.2 self-attack row 4): "
            f"{[(o.verb, o.statement) for o in landed]}"
        )


class TestTheWriteThenRevertBoundIsPinned:
    """§1.2 self-attack row 2 + §1.6-ix (WHEN YOU CANNOT CLOSE A HOLE, PIN IT). A write-then-revert
    WITHIN ONE txn nets a zero diff, so an effect observer sees no change and does not classify it —
    the #138 HOSTILE-AUTHOR shape (an honest developer does not write a self-cancelling transaction).
    This is a NAMED ACCEPTED BOUND: the pin constructs it, asserts the miss, and carries the trigger.
    GREEN on the build (the net-zero txn is genuinely unobserved); it REDS the day someone closes the
    hole (the observer starts seeing intra-txn intermediate state) — delete the pin + re-adjudicate."""

    async def test_a_write_then_revert_in_one_txn_is_unobserved_named_bound(
        self, migration_world: Any  # noqa: F811 (pytest fixture imported by name)
    ) -> None:
        """⚠ NAMED BOUND (#138 class) — a txn that seizes then reverts (net-zero) is UNOBSERVED.
        GREEN-VACUOUS at HEAD (no ``.effect`` to be non-empty); GREEN on the build (net-zero → empty
        effect → not a governance event). RE-OPEN TRIGGER: the threat model changes to an UNTRUSTED
        CONTRIBUTOR (packet 39), at which point intra-txn effect tracking must be re-adjudicated.
        ANTI-VACUITY CONTROL: the row's scope is restored to its pre-txn value, so the net-zero claim
        is real (the txn did run) — a build seeing intra-txn state would observe the seizure step."""
        _p, _k, connection, env = migration_world
        await run(
            connection, f"UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'keep:k'"
        )
        net_zero = (
            f"BEGIN;\nUPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'seized';\n"
            f"UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'keep:k';\nCOMMIT;\n"
        )
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            await run(connection, net_zero)
        # ANTI-VACUITY: the txn actually ran and its NET effect is zero (scope back to 'keep:k').
        row = await run(
            connection, f"SELECT {_COL_SCOPE} FROM type::record('{MEMORY_TABLE}', 'legacy')"
        )
        assert row and row[0][_COL_SCOPE] == "keep:k", (
            f"control: the net-zero txn did not run or did not net to zero — 'unobserved' below would "
            f"be vacuous: {row!r}"
        )
        events = [o for o in observed if o.effect is not None and not o.effect.is_empty]
        assert not events, (
            "a write-then-revert net-zero txn was observed as a governance event — this is the #138 "
            "hostile-author NAMED BOUND (an effect observer sees net state, not intra-txn steps). If "
            "you closed it deliberately (threat model → untrusted contributor, packet 39), DELETE "
            f"this pin and re-adjudicate. observed: {[o.verb for o in events]}"
        )


# =========================================================================== #
# §1.3 — THE OBSERVER'S REACH IS THE _sdk_guard HOOK (the SDK connection CLASS), not a module list.
# =========================================================================== #


class TestTheObserverReachIsTheSdkGuardHook:
    """§1.3/§1.8 — the F5 observer is a HOOK the ``_sdk_guard`` wrapper calls (armed by the battery),
    so its reach is the SDK connection CLASS (every door, every module) — never ``extra_modules`` /
    ``seam_modules_for_tree_allowlist`` (RETIRED). The reach is a checked variable via
    ``require_observations`` (detach the hook → every runtime pin reds "0 observed", never green)."""

    def test_the_sdk_guard_hook_seam_is_built(self) -> None:
        """⚠ RED at HEAD — the ``_sdk_guard`` hook seam (``_CALL_HOOKS`` + ``CallEvent``, design
        §1.8) is unbuilt. Split out so the RED reason is legible (the mechanism), distinct from the
        behavioural reach pin below. On the build ``install()``'s ``_guarded`` applies every hook in
        ``_CALL_HOOKS`` to the door coroutine AFTER ``_judge()`` (the frame depth is untouched)."""
        assert hasattr(_sdk_guard, "_CALL_HOOKS") and hasattr(_sdk_guard, "CallEvent"), (
            "_sdk_guard has no hook seam (_CALL_HOOKS / CallEvent) — the F5 observer cannot be a hook "
            "the guard's wrapper calls, so its reach cannot be the SDK class (§1.3/§1.8 unbuilt)"
        )

    async def test_detaching_the_hook_reds_every_runtime_observation_never_green(
        self, retrofit_world: Any, alice_capability: Any  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD (§1.6 rider v) — the observer is armed THROUGH the guard: with the hook
        DETACHED from ``_sdk_guard._CALL_HOOKS`` the battery observes ZERO governed writes, and a
        cleanliness verdict there is BLINDNESS not cleanliness — a report that requires observations
        must RAISE, never return a false green. RED at HEAD: the hook seam is unbuilt, so there is no
        ``_CALL_HOOKS`` to detach and no hook-armed observer to blind — the mechanism is absent."""
        if not hasattr(_sdk_guard, "_CALL_HOOKS"):
            pytest.fail(
                "the _sdk_guard hook seam (_CALL_HOOKS) is unbuilt, so the F5 observer's reach is NOT "
                "the guard hook (§1.3) — 'detach the hook' is unrepresentable until the seam exists"
            )
        backend, *_rest = retrofit_world
        saved = list(_sdk_guard._CALL_HOOKS)  # noqa: SLF001 - the reach-as-checked-variable pin
        try:
            _sdk_guard._CALL_HOOKS.clear()  # noqa: SLF001 - detach every hook
            with observe_governed_table_writes(MEMORY_TABLE) as observed:
                await _exercise_remember(
                    backend, text="reach probe", capability=alice_capability, importance=0.1
                )
            assert not [o for o in observed if o.effect is not None and not o.effect.is_empty], (
                "with the guard hook DETACHED the F5 observer STILL saw governed writes — its reach "
                "is NOT the guard hook (it is patching seam names again — the RETIRED §1.3 shape)"
            )
        finally:
            _sdk_guard._CALL_HOOKS[:] = saved  # noqa: SLF001 - re-arm for the rest of the suite

    async def test_a_raising_hook_is_loud_never_a_silent_un_observation(self) -> None:
        """⚠ RED at HEAD (§1.8) — a hook that RAISES must NOT be swallowed by ``install``'s wrapper: a
        broken observer is a LOUD test failure, never a silent un-observation (a swallowed hook error
        would leave the F5 seam blind while reporting clean — the #136 blindness class). RED at HEAD:
        the hook seam is unbuilt, so there is no wrapper to prove doesn't swallow. On the build,
        registering a raising hook and making an SDK call PROPAGATES the error."""
        if not hasattr(_sdk_guard, "_CALL_HOOKS"):
            pytest.fail(
                "the _sdk_guard hook seam is unbuilt (§1.8) — 'a raising hook is loud' is "
                "unrepresentable until install()'s _guarded applies _CALL_HOOKS to the door coroutine"
            )
        import asyncio

        from surrealdb import AsyncWsSurrealConnection

        class _Boom(RuntimeError):
            pass

        def _raising_hook(_event: Any, _coro: Any) -> Any:
            raise _Boom("hook blew up")

        saved = list(_sdk_guard._CALL_HOOKS)  # noqa: SLF001
        connection = AsyncWsSurrealConnection.__new__(AsyncWsSurrealConnection)
        try:
            _sdk_guard._CALL_HOOKS.append(_raising_hook)  # noqa: SLF001
            with pytest.raises(_Boom):
                # any guarded door call must run the hook AT CALL time and NOT swallow its raise.
                result = AsyncWsSurrealConnection.query(connection, "INFO FOR DB")
                if asyncio.iscoroutine(result):
                    result.close()
        finally:
            _sdk_guard._CALL_HOOKS[:] = saved  # noqa: SLF001


# =========================================================================== #
# §1.4 — governed_exempt(name, *, statement) IS STATEMENT-SCOPED: classified iff ALL FOUR legs.
# =========================================================================== #


class TestTheExemptMechanismIsStatementScoped:
    """§1.4 — the exemption names ONE exact statement. ``governed_exempt(name, *, statement)`` carries
    the ``(name, statement)`` pair; ``active_exempt()`` returns it. An observed exempt write is
    CLASSIFIED iff name ∧ golden-text (== token == observed) ∧ effect ∧ origin — legs 2 and 3
    independent. RED at HEAD (``governed_exempt`` takes no ``statement`` kwarg; ``active_exempt``
    returns a bare name; the classifier is 2-leg)."""

    def test_governed_exempt_takes_a_statement_and_active_exempt_returns_the_token(self) -> None:
        """⚠ RED at HEAD — ``governed_exempt(name)`` has no ``statement`` kwarg and ``active_exempt``
        returns the bare name. On the build ``governed_exempt(name, *, statement)`` is a CLASS context
        manager whose ``__enter__`` captures ``sys._getframe(1)`` (§1.9 item 3c), and ``active_exempt()``
        returns an ``ExemptToken(name, statement, origin)`` — ``origin`` = the ``(file, co_name)`` of
        the frame ENTERING the ``with`` (THIS test), exactly one up, with NO ``contextlib`` frame in
        between (the class-CM form removes the filename skip-list). Behavioural RED: ``statement=``
        raises TypeError today — caught here as the unbuilt-signal, never leaked. Read by ATTRIBUTE
        (production returns ``governed.ExemptToken``, structurally identical to the substrate twin)."""
        # Any-bridge (the absent_scope idiom): call the not-yet-widened signature through an Any-typed
        # reference so mypy stays green in BOTH worlds — at HEAD ``statement`` raises TypeError, on the
        # build it binds and active_exempt() returns the ExemptToken.
        exempt_cm: Any = governed_mod.governed_exempt
        active_exempt: Any = governed_mod.active_exempt
        try:
            with exempt_cm("probe", statement=_MIGRATE_GOLDEN):
                token = active_exempt()
        except TypeError:
            pytest.fail(
                "governed_exempt does not accept a keyword-only `statement` (design §1.4 / §1.9 item 3c "
                "statement-scoped exemption unbuilt) — the exemption cannot name ONE exact statement"
            )
        assert token is not None and getattr(token, "name", None) == "probe", (
            f"active_exempt() must return an ExemptToken carrying the block's name (§1.9 item 3c): {token!r}"
        )
        assert getattr(token, "statement", None) == _MIGRATE_GOLDEN, (
            f"the ExemptToken's golden statement is not the block's statement (§1.9 item 3c), got {token!r}"
        )
        origin = getattr(token, "origin", None)
        assert (
            isinstance(origin, tuple)
            and len(origin) == 2
            and origin[1] == "test_governed_exempt_takes_a_statement_and_active_exempt_returns_the_token"
        ), (
            "the ExemptToken.origin must be the (file, co_name) of the frame that ENTERED the `with` "
            f"(sys._getframe(1) — THIS test, §1.9 item 3c), never the driver/contextlib frame: got {origin!r}"
        )

    async def test_the_live_migrate_write_classifies_by_all_four_legs(
        self, migration_world: Any  # noqa: F811 (pytest fixture imported by name)
    ) -> None:
        """⚠ RED at HEAD — drive the REAL ``migrate_governed`` under the effect observer; the backfill
        UPDATE must be OBSERVED with a state-diff effect, carry an ``ExemptToken('migrate-governed',
        golden, origin=(principals, _migrate_memory_scope))`` whose ``origin`` is captured at the
        ``governed_exempt`` CONTEXT ENTRY (§1.9 item 3c — NOT the call-time ``_txn`` driver frame), and
        CLASSIFY by all four legs. RED at HEAD: no ``statement`` on the token, no ``origin`` on the
        token, effect unbuilt, 2-leg classifier."""
        principal_store, keep_store, connection, env = migration_world
        handle, _calls = store_handle(connection, url=env.url)
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            await principals_mod.migrate_governed(
                table=MEMORY_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
            )
        # leg-4 origin is a field of the exempt TOKEN (context-entry capture), not o.origin_site (the
        # call-time _txn driver frame). Read by attribute so HEAD's bare-name str exempt → None → RED.
        migrate = [
            o
            for o in observed
            if getattr(o.exempt, "origin", None) == (_PRINCIPALS, "_migrate_memory_scope")
            and o.effect is not None
            and not o.effect.is_empty
        ]
        assert migrate, (
            f"the migrate backfill was not observed as an effect carrying an ExemptToken whose origin "
            f"is principals._migrate_memory_scope (reach / effect / token-origin unbuilt): "
            f"{[(getattr(o.exempt, 'origin', o.exempt), o.effect is not None) for o in observed]}"
        )
        unclassified = [o for o in migrate if not classify_tree_observed_write(o, MEMORY_TREE_ALLOWLIST)]
        assert not unclassified, (
            "the live migrate backfill did NOT classify under the four-leg statement-scoped exemption "
            "(name ∧ golden ∧ effect ∧ origin) — §1.4 unbuilt"
        )

    def test_leg2_reds_a_widened_statement_with_the_same_effect(self) -> None:
        """⚠ LEG 2 (golden text) — an OR-extended statement ``… WHERE scope IS NONE OR scope =
        $victim`` (the R4-a seizure) carries a token whose statement ≠ the golden, so leg 2 REJECTS
        it EVEN THOUGH its per-row effect could look migrate-shaped. This is the leg that catches a
        different-shaped statement smuggled under the token. RED at HEAD (2-leg classifier ignores
        the statement). Legs 2 and 3 are INDEPENDENT — this constructs an effect that PASSES leg 3."""
        widened = f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE OR scope = $victim"
        effect = ObservedEffect(
            row_deltas=(
                RowDelta(
                    id="r1",
                    kind="updated",
                    changed_columns=frozenset({_COL_SCOPE}),
                    before={_COL_SCOPE: None, _COL_OWNER_PRINCIPAL: None, _COL_OWNER_AGENT: None},
                    after={_COL_SCOPE: "keep:k"},
                ),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
        )
        seizure = ObservedWrite(
            label=None,
            # token carries the WIDENED text (≠ golden); origin is the REAL migrate site (legs 1/4 pass)
            exempt=ExemptToken("migrate-governed", widened, (_PRINCIPALS, "_migrate_memory_scope")),
            statement=widened,
            effect=effect,
        )
        assert _effect_migrate(effect) is True, (
            "control: this effect is migrate-SHAPED (leg 3 passes), so the rejection below is leg 2 "
            "(golden text), not leg 3 — legs 2 and 3 are independent (§1.4)"
        )
        assert classify_tree_observed_write(seizure, MEMORY_TREE_ALLOWLIST) is False, (
            "a widened statement (WHERE scope IS NONE OR scope = $victim) carrying the migrate token "
            "CLASSIFIED — leg 2 (normalise(token.statement) == golden == observed) is not enforced; "
            "the R4-a substring-launder is not closed (§1.4 leg 2 unbuilt)"
        )

    def test_leg3_reds_a_golden_edited_to_bless_a_seizure(self) -> None:
        """⚠ LEG 3 (effect) — even if the golden text MATCHED (legs 1/2/4 pass), an effect that
        SEIZED an owned row (before.scope was set) fails leg 3 (``entry.effect`` holds ∀ changed row).
        This is the leg that catches a golden edited to match a seizure. Constructed so legs 1/2/4
        pass and ONLY the effect differs. RED at HEAD (2-leg classifier ignores the effect)."""
        seizing_effect = ObservedEffect(
            row_deltas=(
                RowDelta(
                    id="r2",
                    kind="updated",
                    changed_columns=frozenset({_COL_SCOPE}),
                    before={_COL_SCOPE: "keep:owned", _COL_OWNER_PRINCIPAL: "alice", _COL_OWNER_AGENT: "ag"},
                    after={_COL_SCOPE: "seized"},
                ),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
        )
        write = ObservedWrite(
            label=None,
            # token statement == golden AND origin == the real migrate site (legs 1/2/4 pass) — ONLY
            # the effect differs, so the rejection below is leg 3 (effect), not leg 2 or 4.
            exempt=ExemptToken("migrate-governed", _MIGRATE_GOLDEN, (_PRINCIPALS, "_migrate_memory_scope")),
            statement=_MIGRATE_GOLDEN,
            effect=seizing_effect,
        )
        assert _effect_migrate(seizing_effect) is False, (
            "control: this effect SEIZED an owned row (before.scope was set), so leg 3 must reject it"
        )
        assert classify_tree_observed_write(write, MEMORY_TREE_ALLOWLIST) is False, (
            "a seizure with the exact golden text and a matching origin CLASSIFIED — leg 3 (the effect "
            "predicate ∀ changed row) is not enforced (§1.4 leg 3 unbuilt); a golden edited to bless a "
            "seizure would launder"
        )

    def test_leg4_reds_a_borrowed_token_from_a_foreign_origin(self) -> None:
        """⚠ LEG 4 (origin) — a site BORROWING the migrate token+golden+effect but whose ``origin`` was
        captured at a DIFFERENT frame fails the ``token.origin == entry.site`` match (§1.9 item 3c: the
        origin is a field of the TOKEN, captured at context entry — a helper entering
        ``governed_exempt`` on the migrate frame's behalf yields a foreign origin). Legs 1/2/3 pass;
        ONLY the token's origin is foreign. RED at HEAD (the 2-leg classifier keyed on the bare name
        rejects an ExemptToken, so this passes at HEAD for the wrong reason — the leg-2/3 pins above
        and MISSING PIN #1 are the discriminating REDs; this pins the origin leg survives the rewrite)."""
        clean_effect = ObservedEffect(
            row_deltas=(
                RowDelta(
                    id="r3",
                    kind="updated",
                    changed_columns=frozenset({_COL_SCOPE}),
                    before={_COL_SCOPE: None, _COL_OWNER_PRINCIPAL: None, _COL_OWNER_AGENT: None},
                    after={_COL_SCOPE: "keep:k"},
                ),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
        )
        borrowed = ObservedWrite(
            label=None,
            # the token's ORIGIN is a FOREIGN frame (the borrowed-token construction, §1.9 item 3c) —
            # name+statement+effect all match the migrate entry; only leg 4 (origin) rejects it.
            exempt=ExemptToken("migrate-governed", _MIGRATE_GOLDEN, (_PRINCIPALS, "_some_other_function")),
            statement=_MIGRATE_GOLDEN,
            effect=clean_effect,
        )
        assert classify_tree_observed_write(borrowed, MEMORY_TREE_ALLOWLIST) is False, (
            "a foreign site borrowing the migrate token+golden+effect (its ExemptToken.origin captured "
            "at a foreign frame) CLASSIFIED — leg 4 (token.origin == entry.site) is not enforced; any "
            "site could launder a governed write through the exemption (§1.4 / §1.9 item 3c leg 4)"
        )

    def test_the_golden_is_proven_both_ways(self) -> None:
        """⚠ THE GOLDEN IS AN ORACLE, NOT A SECOND IMPLEMENTATION — proven live both ways (§1.4).
        (a) Change the PRODUCTION constant → the token statement ≠ the entry golden → leg 2 reds
            (a real write carrying the drifted token no longer classifies). Pinned by
            ``test_leg2_reds_a_widened_statement_with_the_same_effect`` (the widened statement IS a
            drifted production constant).
        (b) Change ONLY the golden (the allowlist entry's ``statement``) → NO production call ever
            matches it → the coverage leg (the live migrate write does not classify) reds. Pinned by
            ``test_the_live_migrate_write_classifies_by_all_four_legs`` failing under a drifted golden.
        This test asserts the golden's SHAPE contract holds so both directions are meaningful: the
        entry's golden is exactly the adjudicated migrate statement, whitespace-normalised."""
        assert _normalise(_MIGRATE_ENTRY.statement) == _normalise(_MIGRATE_GOLDEN), (
            "the migrate allowlist entry's golden statement drifted from the adjudicated oracle — the "
            "both-ways golden proof (§1.4) rests on entry.statement being the adjudicated text"
        )
        assert _MIGRATE_ENTRY.statement, "the exempt entry carries NO golden statement (§1.4 leg 2 vacuous)"


class TestTheClassifierRunsALabelFramesEffectPredicate:
    """§1.4 / §1.9 item 3 (adversary MISSING PIN #1) — the LABEL leg is NARROWED: a labeled write
    classifies ONLY IF its matched entry's ``effect`` predicate HOLDS for the observed effect. A
    labeled write whose effect FAILS its entry predicate is UNCLASSIFIED. RED at HEAD: the 2-leg
    classifier blesses ANY label (``if observed.label is not None: return True``), re-widening the
    #138/R2 hand-set-label bound §1.4 narrows — the EXACT wrong build the adversary walked through
    (``WB-label-ignores-effect``, 30/30 green). Every i-a memory label entry carries an effect
    predicate (§1.9 item 3 opening), so this ∀ is exercisable across the whole allowlist."""

    def test_a_reinforce_labeled_write_that_seizes_a_governed_column_is_unclassified(self) -> None:
        """⚠ RED at HEAD (MISSING PIN #1) — a ``_reinforce``-labeled write whose effect ALSO changes a
        GOVERNED column ({importance, scope}) FAILS ``_effect_reinforce`` (importance ONLY) →
        UNCLASSIFIED. POSITIVE CONTROL: the same label with an {importance}-only effect → CLASSIFIED.
        At HEAD ``if label is not None: return True`` blesses the seizure → RED. Pure-unit."""
        seizing = ObservedEffect(
            row_deltas=(
                RowDelta(
                    id="s",
                    kind="updated",
                    changed_columns=frozenset({_COL_IMPORTANCE, _COL_SCOPE}),
                    before={_COL_IMPORTANCE: 0.1, _COL_SCOPE: "keep:k"},
                    after={_COL_IMPORTANCE: 0.5, _COL_SCOPE: "seized"},
                ),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
        )
        assert _effect_reinforce(seizing) is False, (
            "control: a {importance, scope} change must FAIL the reinforce effect predicate, else the "
            "rejection below would not be the classifier RUNNING the predicate"
        )
        seizing_write = ObservedWrite(label="_reinforce", statement="<reinforce seizure>", effect=seizing)
        assert classify_tree_observed_write(seizing_write, MEMORY_TREE_ALLOWLIST) is False, (
            "a _reinforce-labeled write that ALSO seized the scope column CLASSIFIED — the classifier "
            "blesses any label WITHOUT running its entry's effect predicate (MISSING PIN #1; the "
            "#138/R2 re-widening; §1.4 label-effect unbuilt)"
        )
        clean = ObservedEffect(
            row_deltas=(
                RowDelta(
                    id="c",
                    kind="updated",
                    changed_columns=frozenset({_COL_IMPORTANCE}),
                    before={_COL_IMPORTANCE: 0.1},
                    after={_COL_IMPORTANCE: 0.5},
                ),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
        )
        assert _effect_reinforce(clean) is True, "control: an {importance}-only bump must PASS the predicate"
        clean_write = ObservedWrite(label="_reinforce", statement="<reinforce bump>", effect=clean)
        assert classify_tree_observed_write(clean_write, MEMORY_TREE_ALLOWLIST) is True, (
            "POSITIVE CONTROL: a clean _reinforce write (importance only) must CLASSIFY — else the "
            "classifier denies the honest frame too (a build that always denies labels; §1.4)"
        )

    def test_every_label_frame_rejects_an_effect_its_predicate_denies(self) -> None:
        """⚠ RED at HEAD (MISSING PIN #1, GENERALISED ∀ label frame) — for EVERY non-exempt allowlist
        entry carrying an effect predicate, a write carrying that entry's label but an effect the
        predicate REJECTS is UNCLASSIFIED. The classifier must RUN the matched entry's effect ∀ label
        frame, not just ``_reinforce``. Each row SELF-CHECKS (``entry.effect(rejected) is False``) so a
        future widening that ACCEPTS the candidate fails LOUDLY (pick a new rejected effect), never
        silently — the fixture-discriminates law. At HEAD every one reds (``if label is not None:
        return True``)."""
        # Candidate rejected effects; per entry we use the FIRST its predicate denies (the self-check).
        # Together they cover every i-a label predicate: two-scope-rows fails reinforce (scope≠
        # importance) / recreate (empty schema) / ensure_ready (has rows) / guarded_write (2 rows);
        # row-plus-schema fails upsert (schema non-empty).
        two_scope_rows = ObservedEffect(
            row_deltas=(
                RowDelta("b1", "updated", frozenset({_COL_SCOPE}), {_COL_SCOPE: None}, {_COL_SCOPE: "x"}),
                RowDelta("b2", "updated", frozenset({_COL_SCOPE}), {_COL_SCOPE: None}, {_COL_SCOPE: "y"}),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
        )
        row_plus_schema = ObservedEffect(
            row_deltas=(
                RowDelta("c1", "updated", frozenset({_COL_SCOPE}), {_COL_SCOPE: None}, {_COL_SCOPE: "x"}),
            ),
            schema_delta=SchemaDelta(
                added=frozenset({"__hostile_index"}), removed=frozenset(), changed=frozenset()
            ),
        )
        candidates = (two_scope_rows, row_plus_schema)
        checked = 0
        for entry in MEMORY_TREE_ALLOWLIST:
            if entry.exempt_name is not None or entry.effect is None or not entry.frames:
                continue  # exempt frames are the four-leg legs above; label leg needs frames + effect
            rejected = next((eff for eff in candidates if entry.effect(eff) is False), None)
            assert rejected is not None, (
                f"no candidate rejected effect for label entry {entry.site.function} — its predicate "
                f"ACCEPTS both candidates; add a rejected effect this pin can discriminate with"
            )
            label = entry.frames[0]
            off_predicate = ObservedWrite(
                label=label, statement=f"<{label} off-predicate>", effect=rejected
            )
            assert classify_tree_observed_write(off_predicate, MEMORY_TREE_ALLOWLIST) is False, (
                f"a '{label}'-labeled write whose effect its OWN entry predicate REJECTS was CLASSIFIED "
                f"— the classifier does not RUN this label frame's effect predicate (MISSING PIN #1 "
                f"generalised ∀ label frame; §1.4 label-effect): {entry.site.function}"
            )
            checked += 1
        assert checked >= 4, (
            f"expected ≥4 non-exempt label frames exercised (upsert/reinforce/recreate/ensure_ready/"
            f"guarded_write) — only {checked}; the ∀ generalisation went vacuous"
        )


# =========================================================================== #
# §1.5 — L1 is DEMOTED to a COVERAGE FLOOR with a DERIVED keyword grammar; the population set is a
# DERIVED OUTPUT; coverage is a CHECKED VARIABLE.
# =========================================================================== #


class TestL1IsACoverageFloorWithADerivedGrammar:
    """§1.5a — L1's verb list is INVERTED to a grammar keyed on the vendor's statement index
    (``SURREALQL_STATEMENT_KEYWORDS``), keeping the verb→operand ADJACENCY. So a keyword the engine
    gains cannot silently escape L1's reach, and the R4-c exotic verbs (CREATE/INSERT/RELATE) are now
    DERIVED at L1 (L2 covers them by effect regardless). RED at HEAD (bounded verb regex + empty
    constant)."""

    def test_the_derived_grammar_covers_the_exotic_write_verbs(self) -> None:
        """⚠ RED at HEAD (§1.6-ii shape/verb-agnostic at L1) — a CREATE / INSERT INTO / RELATE
        targeting the governed table is DERIVED by ``_raw_mutation_of_table`` (the R4-c verbs, now in
        the grammar). At HEAD the bounded regex returns None for all three. POSITIVE CONTROL: an
        in-set UPDATE derives, and a SELECT does NOT (the read safe set) — so the None above is a
        grammar gap, not a blind matcher."""
        create = f"CREATE type::record('{MEMORY_TABLE}', $id) SET scope = 'seized'"
        insert = f"INSERT INTO {MEMORY_TABLE} (id, scope) VALUES ($id, 'seized')"
        relate = f"RELATE $p->owns->type::record('{MEMORY_TABLE}', $id)"
        for statement in (create, insert, relate):
            assert _raw_mutation_of_table(statement, MEMORY_TABLE, "MEMORY_TABLE") is not None, (
                f"the L1 grammar does NOT derive an exotic-verb governed write (the R4-c verb set is "
                f"still a bounded enumeration — §1.5a unbuilt): {statement!r}"
            )
        assert _raw_mutation_of_table(
            f"UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'x'", MEMORY_TABLE, "MEMORY_TABLE"
        ) == "UPDATE", "control: an in-set UPDATE must derive (else the grammar is blind, not just narrow)"
        assert _raw_mutation_of_table(
            f"SELECT * FROM {MEMORY_TABLE}", MEMORY_TABLE, "MEMORY_TABLE"
        ) is None, "control: a SELECT is a READ (the safe set) and must NOT derive as a mutation"

    def test_the_grammar_keyword_set_is_derived_not_a_hand_list(self) -> None:
        """⚠ RED at HEAD — ``SURREALQL_STATEMENT_KEYWORDS`` is a DERIVED-from-corpus constant, not a
        hand list, and CONTAINS the mutation + read keywords the grammar keys on. Empty at HEAD (the
        builder derives + commits it) → this reds. REDDENS a build whose grammar hardcodes a verb list
        instead of deriving from the vendor statement index (§1.5a)."""
        assert SURREALQL_STATEMENT_KEYWORDS, (
            "SURREALQL_STATEMENT_KEYWORDS is empty — the grammar's keyword set is not DERIVED from the "
            "vendor statement index yet (§1.5a); it must be committed from the corpus, not hand-listed"
        )
        missing = (SURREALQL_MUTATION_KEYWORDS | SURREALQL_READ_KEYWORDS) - SURREALQL_STATEMENT_KEYWORDS
        assert not missing, (
            f"the derived keyword set is missing statement keywords the grammar keys on: {sorted(missing)}"
        )

    def test_the_keyword_currency_pin_tracks_the_corpus(self) -> None:
        """⚠ RED at HEAD (§1.6-viii keyword currency) — the committed constant EQUALS the set DERIVED
        from the ``surrealdb-docs`` corpus (the statements/*.mdx page stems). A keyword the vendor
        adds → the derivation grows → drift reds "classify its operand position"; a keyword deleted
        from the constant that the corpus lists → reds. RED at HEAD: the derivation is unbuilt
        (NotImplementedError). ⚠ IN-IMAGE PROFILE (packet 01a): where the corpus is unreadable this
        is ``RED_ADJUDICATED`` (design §1.5a) — on the dev host the corpus IS readable and this runs."""
        try:
            derived = derive_surrealql_statement_keywords_from_corpus()
        except NotImplementedError:
            pytest.fail(
                "derive_surrealql_statement_keywords_from_corpus is unbuilt (§1.5a) — the keyword "
                "currency pin cannot track the vendor statement index; the constant is a hand list"
            )
        assert SURREALQL_STATEMENT_KEYWORDS == derived, (
            f"SURREALQL_STATEMENT_KEYWORDS has DRIFTED from the corpus (§1.6-viii). "
            f"in corpus not constant: {sorted(derived - SURREALQL_STATEMENT_KEYWORDS)}; "
            f"in constant not corpus: {sorted(SURREALQL_STATEMENT_KEYWORDS - derived)}"
        )

    def test_every_mutation_keyword_has_an_operand_rule_in_the_grammar(self) -> None:
        """⚠ §1.5a / §1.6-viii — a mutation keyword with NO operand rule in the grammar reds
        "classify its operand position": for every mutation keyword, a statement whose verb IMMEDIATELY
        targets the table is DERIVED. RED at HEAD (CREATE/INSERT/RELATE/DEFINE/ALTER/REBUILD have no
        operand rule yet). This makes the grammar's coverage a CHECKED VARIABLE over the keyword SET —
        a new mutation keyword the corpus adds must gain an operand rule or this reds."""
        probes = {
            "UPDATE": f"UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'x'",
            "UPSERT": f"UPSERT type::record('{MEMORY_TABLE}', $id) CONTENT {{}}",
            "DELETE": f"DELETE type::record('{MEMORY_TABLE}', $id)",
            "CREATE": f"CREATE type::record('{MEMORY_TABLE}', $id) SET scope = 'x'",
            "INSERT": f"INSERT INTO {MEMORY_TABLE} (id) VALUES ($id)",
            "RELATE": f"RELATE $p->owns->type::record('{MEMORY_TABLE}', $id)",
            "REMOVE": f"REMOVE TABLE {MEMORY_TABLE}",
            "DEFINE": f"DEFINE FIELD scope ON {MEMORY_TABLE} TYPE option<string>",
            "ALTER": f"ALTER TABLE {MEMORY_TABLE} CHANGEFEED 1h",
            "REBUILD": f"REBUILD INDEX {MEMORY_TABLE}_scope ON {MEMORY_TABLE}",
        }
        unclassified = [
            keyword
            for keyword in SURREALQL_MUTATION_KEYWORDS
            if keyword in probes
            and _raw_mutation_of_table(probes[keyword], MEMORY_TABLE, "MEMORY_TABLE") is None
        ]
        assert not unclassified, (
            f"these mutation keywords have NO operand rule in the grammar (a keyword the corpus lists "
            f"but the grammar cannot classify its operand position — §1.5a): {sorted(unclassified)}"
        )


class TestTheGovernedPopulationSetIsADerivedOutput:
    """§1.5c-iii — the governed-population set is DERIVED from ``surreal_schema`` (tables whose DDL
    slice calls ``_governed_field_specs`` ∪ relation tables with a governed endpoint), an OUTPUT, so
    a new governed table joins F5's reach by the same derivation that governs it. At ``e4b8945`` the
    derivation yields ``{memory}`` (message/to arrive in ii-a). RED at HEAD (derivation unbuilt)."""

    def test_the_derived_population_set_is_the_known_set(self) -> None:
        """⚠ RED at HEAD — ``governed_populations()`` derives ``{memory}`` at this HEAD (an OUTPUT, not
        a hand list). At HEAD the derivation raises (unbuilt). REDDENS a surprise governed population
        with no F5 case, OR a build that hardcodes the set instead of deriving it from surreal_schema.
        ⚠ ii-a's DDL grows the set to {memory, message, to} — those cases are RED_ADJUDICATED(owner=
        63b-ii) rows; at i-a the set is exactly {memory}, satisfiable."""
        try:
            populations = governed_populations()
        except NotImplementedError:
            pytest.fail(
                "governed_populations is unbuilt (§1.5c-iii) — the governed-population set is not "
                "DERIVED from surreal_schema; F5's reach over the SET of populations is a hidden constant"
            )
        assert MEMORY_TABLE in populations, (
            f"the memory table is not in the derived governed-population set {sorted(populations)} — "
            f"the derivation does not see the emitter's _governed_field_specs slice (§1.5c-iii)"
        )
        assert populations == frozenset({MEMORY_TABLE}), (
            f"the derived governed-population set moved from the known i-a set {{memory}}: "
            f"{sorted(populations)}. A new governed population needs an F5 case (message/to ride ii-a "
            f"as RED_ADJUDICATED(owner=63b-ii)); a SURPRISE population is a deny-by-default RED"
        )

    def test_the_population_derivation_reach_is_a_checked_variable(self) -> None:
        """⚠ RED at HEAD (adversary MISSING PIN #2 / §1.9 item 2) — ``governed_populations()`` is
        DERIVED from ``surreal_schema``, NEVER a literal. Fed a SYNTHETIC schema source, a NEW
        ``_widget_statements`` that CALLS ``_governed_field_specs`` GROWS the set to include ``widget``,
        and a ``_define_relation_table('widget_edge', 'widget', …)`` whose endpoint is governed JOINS.
        Mutation proof: adding a ``_governed_field_specs`` caller MUST change the output. This is the
        reach-as-a-checked-variable pin the adversary found MISSING — it catches ``return
        frozenset({MEMORY_TABLE})`` (a hardcode passes ``test_the_derived_population_set_is_the_known_
        set`` but FAILS here). It ALSO pins the §1.9 item 2 / F-TRAP-1 correction: an emitter with a
        DIRECT ``owner_principal`` field (the packet-62 ``agent`` shape) that does NOT call
        ``_governed_field_specs`` is NOT included — the derivation keys on the CALLER, not a field name.
        The synthetic source uses the REAL helper names (``_governed_field_specs`` /
        ``_define_relation_table(name, in_table, out_table)``) so the build's derivation recognises it."""
        baseline_source = (
            "def _governed_field_specs():\n    return []\n\n"
            "def _define_relation_table(name, in_table, out_table):\n    return ''\n\n"
            "def _memory_statements():\n    return _governed_field_specs()\n\n"
            # F-TRAP-1 shape: agent carries a DIRECT owner_principal field, NOT via _governed_field_specs
            "def _agent_statements():\n"
            "    return ['DEFINE FIELD owner_principal ON agent TYPE option<record>']\n"
        )
        try:
            baseline = governed_populations(schema_source=baseline_source)
        except NotImplementedError:
            pytest.fail(
                "governed_populations is unbuilt (§1.5c-iii / §1.9 item 2) — its reach over the SET of "
                "populations cannot be exercised on a synthetic source; the reach is a hidden constant"
            )
        assert baseline == frozenset({MEMORY_TABLE}), (
            f"the synthetic baseline (only _memory_statements calls _governed_field_specs) did NOT "
            f"derive exactly {{memory}} — the derivation is not keyed on _governed_field_specs CALLERS "
            f"(§1.9 item 2 / F-TRAP-1: agent's owner_principal is a DIRECT field, not a governed slice): "
            f"{sorted(baseline)}"
        )
        grown_source = baseline_source + (
            "def _widget_statements():\n    return _governed_field_specs()\n\n"
            "def _widget_edge_statements():\n"
            "    return _define_relation_table('widget_edge', 'widget', 'note')\n"
        )
        grown = governed_populations(schema_source=grown_source)
        assert grown != baseline, (
            "adding a _governed_field_specs caller (_widget_statements) to the synthetic schema did "
            "NOT change the derived population set — governed_populations is a HARDCODED literal, not a "
            "derivation (the frozenset({memory}) wrong build; MISSING PIN #2 / §1.9 item 2 reach)"
        )
        assert "widget" in grown, (
            f"a NEW emitter calling _governed_field_specs did NOT join the governed-population set — "
            f"the derivation does not key on _governed_field_specs callers (§1.9 item 2): {sorted(grown)}"
        )
        assert "widget_edge" in grown, (
            f"a relation table (_define_relation_table) whose endpoint 'widget' is governed did NOT "
            f"join the population set — the relation-endpoint leg of the derivation is missing "
            f"(§1.9 item 2 ∪ relation tables with a governed endpoint): {sorted(grown)}"
        )


class TestCoverageIsACheckedVariableOverTheRuntimeObservedFrames:
    """§1.5c-ii — coverage is a CHECKED VARIABLE: EVERY ``runtime_observed=True`` allowlist entry's
    attribution channel (its write_guard label frames, or its exempt name) is OBSERVED mutating the
    table with a NON-EMPTY effect UNDER THE BATTERY. A frame the battery never drives (or drives with
    no effect) is a BLIND SPOT — the sixth-defeat lesson (a guard certifies only what it RUNS; reach
    is a checked variable, not a hidden constant). The ∀ is the OUTPUT: a NEW runtime_observed entry
    whose frame no battery exercises REDS here, forcing the battery to grow with the allowlist."""

    async def test_every_runtime_observed_frame_is_observed_with_a_nonempty_effect(
        self,
        retrofit_world: Any,  # noqa: F811 (pytest fixture imported by name)
        alice_capability: Any,  # noqa: F811 (pytest fixture imported by name)
        migration_world: Any,  # noqa: F811 (pytest fixture imported by name)
        rebuild_world: Any,
    ) -> None:
        """⚠ RED at HEAD — drives the WHOLE battery (member create/reinforce/close · rebuild
        REMOVE→ensure_ready→replay · migrate backfill) under the effect observer and aggregates the
        labels + exempt names of every observed write carrying a NON-EMPTY effect. Asserts every
        ``runtime_observed=True`` entry's channel is in that set. RED at HEAD: ``.effect`` is None, so
        the observed-with-effect set is empty and every runtime_observed frame is missing. GREEN on
        the build. DISCRIMINATES: a build whose battery/observer misses a frame → that frame missing
        → RED (coverage is a checked variable over the SET of runtime_observed frames, §1.5c-ii)."""
        observed_channels: set[str] = set()

        def _absorb(writes: list[ObservedWrite]) -> None:
            for write in writes:
                if write.effect is None or write.effect.is_empty:
                    continue
                if write.label:
                    observed_channels.add(write.label)
                if write.exempt is not None:
                    # The channel NAME — duck-typed: ExemptToken.name (production's governed.ExemptToken
                    # AND the substrate twin are DIFFERENT classes, so isinstance would be wrong), else
                    # the bare str (HEAD). str() coerces for the set[str] type + the sorted diagnostics.
                    observed_channels.add(str(getattr(write.exempt, "name", write.exempt)))

        # member battery (remember · _reinforce · guarded_write via invalidate).
        backend, *_member_rest = retrofit_world
        _absorb(await _observed_member_writes(backend, alice_capability))

        # rebuild battery (_recreate_memory_table · ensure_ready · _replay_record).
        rebuild_backend, _ledger, _rb_env = rebuild_world
        with observe_governed_table_writes(MEMORY_TABLE) as rebuild_observed:
            await rebuild_backend.rebuild_embeddings()
        _absorb(list(rebuild_observed))

        # migrate battery (_migrate_memory_scope, exempt).
        principal_store, keep_store, connection, env = migration_world
        handle, _calls = store_handle(connection, url=env.url)
        with observe_governed_table_writes(MEMORY_TABLE) as migrate_observed:
            await principals_mod.migrate_governed(
                table=MEMORY_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
            )
        _absorb(list(migrate_observed))

        expected: set[str] = set()
        for entry in MEMORY_TREE_ALLOWLIST:
            if not entry.runtime_observed:
                continue  # a runtime_observed=False entry carries L2a structural coverage only (named bound)
            expected |= {entry.exempt_name} if entry.exempt_name is not None else set(entry.frames)
        missing = expected - observed_channels
        assert not missing, (
            f"these runtime_observed frames were NOT observed mutating memory with a NON-EMPTY effect "
            f"under the battery — a COVERAGE BLIND SPOT (a guard certifies only what it RUNS; §1.5c-ii "
            f"coverage-as-a-checked-variable): {sorted(missing)}. observed channels: "
            f"{sorted(observed_channels)}"
        )


class TestL1CoverageIsDenyByDefaultOverTheSiteBackedEntries:
    """§1.5c-i — every L1-derived raw mutation site ∈ exactly ONE site-backed allowlist entry (deny-
    by-default); the site-backed allowlist has no GHOST. The DDL/label frames (l1_site=False) are
    EXCLUDED from this leg (they have no raw literal — covered by L2 effect + L2a). GREEN at HEAD (the
    four site-backed sites are enumerated); REDS a new unclassified raw write anywhere in the tree."""

    def test_every_derived_site_is_in_a_site_backed_entry_and_no_ghost(self) -> None:
        derived = governed_table_raw_mutation_sites_in_tree(MEMORY_TABLE)
        assert derived, "the whole-tree scan derived NO raw memory mutation — the scanner is blind"
        orphans = derived - L1_ALLOWLISTED_SITES
        ghosts = L1_ALLOWLISTED_SITES - derived
        assert not orphans, (
            f"UNCLASSIFIED raw memory mutation(s) across the tree (deny-by-default): {sorted(orphans)}"
        )
        assert not ghosts, (
            f"GHOST site-backed allowlist entry — no live raw mutation site: {sorted(ghosts)}"
        )

    def test_the_label_frames_are_excluded_from_l1_and_carry_an_effect(self) -> None:
        """The DDL/label frames (ensure_ready, guarded_write) are l1_site=False — NOT derived by L1 —
        and each carries an effect predicate (a 63b-new label frame REQUIRES one, §1.4). REDDENS a
        build that mis-marks a label frame as an L1 site (its sentinel site would ghost the L1 leg) or
        omits its effect predicate."""
        label_frames = [entry for entry in MEMORY_TREE_ALLOWLIST if not entry.l1_site]
        assert {entry.site.function for entry in label_frames} == {"ensure_ready", "guarded_write"}, (
            f"the label-frame set moved from {{ensure_ready, guarded_write}}: "
            f"{sorted(e.site.function for e in label_frames)}"
        )
        missing_effect = [e.site.function for e in label_frames if e.effect is None]
        assert not missing_effect, (
            f"a 63b-new label frame carries NO effect predicate (§1.4 REQUIRED): {missing_effect}"
        )


# =========================================================================== #
# §5.1 Q1 — ``ensure_ready`` becomes an allowlisted DDL frame + the ``_recreate_memory_table`` flip.
# =========================================================================== #


class TestEnsureReadyIsAnAllowlistedDdlFrame:
    """§5.1 Q1 — ``ensure_ready``'s re-DEFINE is a schema mutation of a governed population; at HEAD
    it runs OUTSIDE any guard → UNCLASSIFIED → the DDL leg is NON-SATISFIABLE on ANY fixture (every
    fixture calls ensure_ready on a virgin DB). The fix: ``write_guard('ensure_ready')`` + an effect
    predicate (schema delta == the emitter's own managed objects, no rows moved). RED at HEAD."""

    def test_ensure_ready_carries_the_ddl_frame_label_and_effect(self) -> None:
        """⚠ RED at HEAD (L2a structural) — ``ensure_ready`` enters ``governed.write_guard`` (label
        'ensure_ready') around its ``execute_transaction``. At HEAD it does not. This is ALSO the
        evidencing pin for ``_ENSURE_READY_ENTRY``. REDDENS a build that leaves the boot DDL apply
        unattributed (the DDL leg reds on every fixture)."""
        source = Path(local_mod.__file__).read_text(encoding="utf-8")
        assert function_calls_named(source, "ensure_ready", "write_guard"), (
            "memory.local.ensure_ready does NOT enter governed.write_guard — its DDL apply is "
            "UNATTRIBUTED at the F5 seam, so the DDL leg is non-satisfiable on every fixture (§5.1 Q1)"
        )

    async def test_the_ensure_ready_effect_predicate_discriminates(
        self, ensure_ready_oracle: Any
    ) -> None:
        """The DDL-frame effect predicate (design §5.1 Q1 / §1.9 item 4) is the CONSTRUCTED oracle,
        compared by DICT EQUALITY (no regex): a no-rows effect whose ``schema_after`` == the oracle
        classifies; one that MOVES ROWS reds; one whose after-schema differs by even ONE field reds
        (the NON-VACUITY leg — §1.9 item 4). GREEN at HEAD (the predicate + the live oracle read are
        contract-side, independent of the builder). What WRONG build passes this? one whose predicate
        is ``lambda e: not e.row_deltas`` (ignores the schema) — CAUGHT by the non-vacuity leg."""
        oracle = ensure_ready_oracle
        good = ObservedEffect(
            row_deltas=(),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
            schema_after=oracle,
        )
        assert _effect_ensure_ready(good) is True, (
            "an after-schema == the constructed oracle, no rows moved, must classify (§1.9 item 4)"
        )
        moves_rows = ObservedEffect(
            row_deltas=(
                RowDelta("r", "updated", frozenset({_COL_SCOPE}), {_COL_SCOPE: None}, {_COL_SCOPE: "x"}),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
            schema_after=oracle,
        )
        assert _effect_ensure_ready(moves_rows) is False, (
            "a DDL frame that MOVED rows passed the ensure_ready predicate — a DDL frame that moves "
            "rows is RED (§5.1 Q1)"
        )
        # NON-VACUITY (§1.9 item 4): the oracle DDL + one EXTRA field renders a DIFFERENT snapshot →
        # the dict-equality compare must red, proving it is not vacuously equal for any no-rows effect.
        env = make_env(database=unique_database(), dim=_DIM)
        connection = await connect_admin(env)
        try:
            await apply_ddl(connection, surreal_schema.generate_memory_ddl(dim=_DIM), url=env.url)
            await run(connection, f"DEFINE FIELD __oracle_probe ON {MEMORY_TABLE} TYPE option<string>")
            extra = schema_snapshot_from_info(await run(connection, f"INFO FOR TABLE {MEMORY_TABLE}"))
        finally:
            await connection.close()
            await drop_database(env)
        assert extra != oracle, (
            "control: adding a field to the oracle DB did not change its INFO FOR TABLE snapshot — the "
            "oracle comparison would be vacuous (schema_snapshot_from_info collapses distinct schemas)"
        )
        smuggled = ObservedEffect(
            row_deltas=(),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
            schema_after=extra,
        )
        assert _effect_ensure_ready(smuggled) is False, (
            "an after-schema with ONE EXTRA field (not in the constructed oracle) PASSED the ensure_"
            "ready predicate — the oracle comparison is vacuous / a DDL frame could smuggle an unmanaged "
            "schema change (§1.9 item 4 non-vacuity)"
        )

    async def test_the_rebuild_arc_is_observed_and_classified(
        self, rebuild_world: Any, ensure_ready_oracle: Any
    ) -> None:
        """⚠ RED at HEAD (§1.6-vi DDL leg) — drive ``rebuild_embeddings`` under the effect observer
        and assert the arc: a REMOVE (label ``_recreate_memory_table``, a schema-removal effect) → an
        ensure_ready re-DEFINE (label ``ensure_ready``, a schema delta == the emitter's managed
        objects) → a ``_replay_record`` UPSERT (label ``_replay_record``, a row-create effect). EVERY
        observed governed write in the arc carries a non-empty effect AND classifies. RED at HEAD:
        effect is None, and the ensure_ready re-DEFINE runs unlabelled → UNCLASSIFIED."""
        backend, _ledger, _env = rebuild_world
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            await backend.rebuild_embeddings()
        events = [o for o in observed if o.effect is not None and not o.effect.is_empty]
        assert events, (
            "rebuild_embeddings produced NO observed governed effect — the observer is blind to the "
            "REMOVE→ensure_ready→replay arc (effect / hook unbuilt, §5.1 Q1)"
        )
        labels = {o.label for o in events}
        # the DDL re-DEFINE must be attributed to 'ensure_ready' — the #445 memory bound shrinks to
        # nothing (the rebuild path is now observed).
        assert "ensure_ready" in labels, (
            f"the ensure_ready re-DEFINE was NOT observed under the 'ensure_ready' label — the boot "
            f"DDL apply is still unattributed (§5.1 Q1). observed labels: {sorted(str(x) for x in labels)}"
        )
        unclassified = [
            (o.label, o.verb) for o in events if not classify_tree_observed_write(o, MEMORY_TREE_ALLOWLIST)
        ]
        assert not unclassified, (
            f"these rebuild-arc governed writes ran UNCLASSIFIED (deny-by-default — §5.1 Q1 / §1.6-vi): "
            f"{unclassified}"
        )

    def test_recreate_entry_is_runtime_observed(self) -> None:
        """§5.1 Q1 / §1.6-vi — the ``_recreate_memory_table`` entry is FLIPPED to
        ``runtime_observed=True`` (was False under the #445 bound at 63a-v). The rebuild battery above
        drives it under observation, so the bound shrinks to nothing on the memory table. REDDENS a
        regression that re-marks it structural-only."""
        assert _RECREATE_ENTRY.runtime_observed is True, (
            "_recreate_memory_table is still runtime_observed=False (the #445 boot/admin bound) — §5.1 "
            "Q1 FLIPS it: the i-a battery drives rebuild_embeddings under observation"
        )


class TestGuardedWriteIsAnAllowlistedLabelFrame:
    """§5.1 Q2 ii — ``guarded_write`` is a label frame (write_guard('guarded_write')) whose effect is
    EXACTLY ONE governed row changed or deleted. Its L2a structural coverage STANDS from 63a; this
    module adds its effect predicate + the evidencing pin the entry names."""

    def test_guarded_write_carries_its_label_and_one_row_effect(self) -> None:
        """The evidencing pin for ``_GUARDED_WRITE_ENTRY``. (a) L2a: ``guarded_write`` enters
        ``write_guard`` (GREEN at HEAD — STANDS from 63a). (b) the effect predicate discriminates: one
        changed/deleted row passes; two rows, or a schema delta, red. GREEN at HEAD (pure predicate)."""
        source = Path(governed_mod.__file__).read_text(encoding="utf-8")
        assert function_calls_named(source, "guarded_write", "write_guard"), (
            "governed.guarded_write does not enter governed.write_guard (L2a) — its guarded mutation is "
            "unattributed at the F5 seam"
        )
        one = ObservedEffect(
            row_deltas=(
                RowDelta(
                    "r", "updated", frozenset({"valid_until"}), {"valid_until": None}, {"valid_until": "t"}
                ),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
        )
        assert _effect_guarded_write(one) is True, "exactly one changed governed row must pass"
        two = ObservedEffect(
            row_deltas=(
                RowDelta("r1", "updated", frozenset({"scope"}), {"scope": None}, {"scope": "x"}),
                RowDelta("r2", "updated", frozenset({"scope"}), {"scope": None}, {"scope": "x"}),
            ),
            schema_delta=SchemaDelta(frozenset(), frozenset(), frozenset()),
        )
        assert _effect_guarded_write(two) is False, (
            "TWO governed rows changed under guarded_write passed its one-row effect predicate — a "
            "guarded write must touch exactly one row (§5.1 Q2 ii)"
        )


# =========================================================================== #
# §1.6 remaining riders — ii shape-agnostic, iv serialised attribution.
# =========================================================================== #


class TestF5RootFixRemainingRiders:
    """§1.6 riders ii (shape-agnostic) and iv (serialised attribution) — each a behavioural pin over
    the effect observer. RED at HEAD (effect unbuilt)."""

    async def test_ii_shape_agnostic_a_concatenated_seizure_is_observed(
        self, migration_world: Any  # noqa: F811 (pytest fixture imported by name)
    ) -> None:
        """⚠ §1.6-ii — a concatenation-assembled seizure (the #444 STATIC bound, closed at L2 by
        effect) LANDS a state change and is OBSERVED with a non-empty effect, UNCLASSIFIED (no
        label). Detection does not care HOW the statement was assembled — only that state moved. RED
        at HEAD: effect is None. The concat runs directly on the store connection (an escape)."""
        _p, _k, connection, env = migration_world
        await run(
            connection, f"UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'keep:k'"
        )
        verb = "UP" + "DATE"  # assembled at runtime — invisible to a static shape scan (#444)
        concat = f"{verb} type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'seized'"
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            await run(connection, concat)
        landed = [o for o in observed if o.effect is not None and not o.effect.is_empty]
        assert landed, (
            "a concatenation-assembled seizure was NOT observed as an effect — detection still depends "
            "on statement shape (#444 not closed at L2 by effect, §1.6-ii)"
        )
        assert all(not classify_tree_observed_write(o, MEMORY_TREE_ALLOWLIST) for o in landed), (
            "the label-less concat seizure CLASSIFIED — deny-by-default is not firing (§1.6-ii)"
        )

    async def test_iv_two_gathered_writes_each_get_their_own_effect(
        self, migration_world: Any  # noqa: F811 (pytest fixture imported by name)
    ) -> None:
        """⚠ §1.6-iv serialised attribution — two writes issued via ``asyncio.gather`` are each
        observed with their OWN per-call effect (the observer holds one lock across before→call→after,
        so attribution is exact — no cross-attribution of one write's delta to the other). RED at
        HEAD: effect is None. ⚠ The lock-REMOVAL deterministic-red mutation proof (a fake door
        interleaving the two awaits, §1.6-iv) is the adversary's REACH-ATTACK P1c lever against the
        BUILT observer — this contract pins the observable property (distinct, correct per-call
        effects); the adversary proves the lock is load-bearing."""
        import asyncio

        _p, _k, connection, env = migration_world
        # two DISTINCT legacy rows so each write has its own, distinguishable effect.
        await run(
            connection,
            f"CREATE type::record('{MEMORY_TABLE}', 'g1') CONTENT {{ note_text: 'a', kind: 'fact', "
            f"source: {{ kind: 'test', trust: 'experiential' }}, created_at: time::now(), "
            f"embedding: {[0.0] * _DIM} }}",
        )
        await run(
            connection,
            f"CREATE type::record('{MEMORY_TABLE}', 'g2') CONTENT {{ note_text: 'b', kind: 'fact', "
            f"source: {{ kind: 'test', trust: 'experiential' }}, created_at: time::now(), "
            f"embedding: {[0.0] * _DIM} }}",
        )
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            await asyncio.gather(
                run(connection, f"UPDATE type::record('{MEMORY_TABLE}', 'g1') SET {_COL_SCOPE} = 'k1'"),
                run(connection, f"UPDATE type::record('{MEMORY_TABLE}', 'g2') SET {_COL_SCOPE} = 'k2'"),
            )
        with_effect = [o for o in observed if o.effect is not None and not o.effect.is_empty]
        changed_ids = {delta.id for o in with_effect for delta in o.effect.row_deltas}  # type: ignore[union-attr]
        assert {"g1", "g2"} <= changed_ids, (
            f"the two gathered writes were not each observed with their OWN per-call effect (rows "
            f"g1/g2) — attribution is not serialised/exact (§1.6-iv). observed changed ids: "
            f"{sorted(changed_ids)}"
        )
        # exactness: no single observed effect claims BOTH rows (a cross-attribution smear).
        smeared = [
            sorted(delta.id for delta in o.effect.row_deltas)  # type: ignore[union-attr]
            for o in with_effect
            if {"g1", "g2"} <= {delta.id for delta in o.effect.row_deltas}  # type: ignore[union-attr]
        ]
        assert not smeared, (
            f"an observed effect claimed BOTH gathered rows — cross-attribution (the per-call lock is "
            f"not held across before→call→after; §1.6-iv): {smeared}"
        )


# =========================================================================== #
# EVIDENCE — every allowlist entry's pin exists (an entry whose evidence is deleted leaves the
# allowlist), derived by AST across the whole test tree (never a hand list).
# =========================================================================== #


class TestEveryAllowlistEntryHasARealEvidencingPin:
    """§1.5c layer-3 — each allowlist entry's ``pin`` names a test DEFINED in the test tree (evidence,
    not opinion). GREEN at HEAD once every pin exists (the two new label-frame pins live here)."""

    def test_every_entry_pin_is_a_defined_test(self) -> None:
        import ast

        tests_dir = Path(__file__).resolve().parent
        defined: set[str] = set()
        for path in sorted(tests_dir.glob("test_*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name.startswith("test_"):
                    defined.add(node.name)
        missing = [(entry.site, entry.pin) for entry in MEMORY_TREE_ALLOWLIST if entry.pin not in defined]
        assert not missing, f"allowlist entries whose evidencing PIN does not exist: {missing}"
