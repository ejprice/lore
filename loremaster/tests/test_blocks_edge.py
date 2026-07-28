"""Contract tests for packet **04b-1** — the ``task->blocks->task`` DAG edge, the
atomic ``create_task``, the acyclicity guard over PERSISTED ids, the transitive
blocker read, the GENERALISED row-existence policy (lead ruling L3), and **#247**
(the message SENDER door).

*Every claim in this file is scoped to the tree at ``c5a2552`` (branch
``feat/surreal-unification``), 2026-07-28.  "RED today" means RED at that commit.*

Scope, verbatim from ``docs/plans/v2/04-comms-blocks-footer.md`` §04b SPLIT
("04b-1 — task DAG + the sender guard"), which is AUTHORITATIVE over the body of that
file (the body predates the split):

* the ``blocks`` edge in ``surreal_schema::_task_statements`` — ``ENFORCED`` from birth,
  emitted by **both** ``generate_task_ddl`` and ``generate_ddl`` (that ONE site is the
  only one feeding both; scout ``REPORT-scout-04b-seams.md`` §A1-NOTE);
* ``create_task`` converted to a TRANSACTION so the CREATE and the ``RELATE`` are atomic
  (today it is a bare ``self._query``, scout §A2 W1);
* the ``blocks`` ≡ ``blocked_by`` mirror at every write path, under THE QUANTIFIER LAW;
* the generalised blocker-existence pre-check (**L3**) — ONE implementation shared with
  packet 04a's agent policy, never a ``reject_unknown_tasks`` clone (#102's shape);
* an acyclicity guard over PERSISTED ids (today's only cycle check is
  ``AppContext._find_key_cycle``, over ``create_many``'s batch-local temp KEYS — scout §A4);
* the transitive read as a LEDGER-level helper (the RENDER is 04b-2's and is NOT pinned here);
* **#247** — the message ``sender`` is caller-supplied and unvalidated at the
  ``MessageLedger.send`` seam (scout §E1–§E3), closed here by operator ruling **R2**.

Binding reading, in the order it must be read:

* ``docs/reference/surrealdb-31-capabilities.md`` — the store law.  Load-bearing here:
  §1.1 (a ``TYPE RELATION`` table takes ``OVERWRITE``; ``IF NOT EXISTS`` is a MEASURED
  silent no-op — #107's shape), §1.6 (the virgin-DB blind spot), §3 (the SDK validates
  ``statement[0]`` only), §4 (``ENFORCED`` validates BOTH endpoints, guards the TABLE
  including ``INSERT RELATION``, and its error ergonomics: ONE bad endpoint, untyped
  prose, AFTER the write), §5 (an undeclared edge table is auto-created ``TYPE ANY``),
  §6.4 (a dangling edge reads as a FIRST-CLASS MEMBER, never ``[]``), §7 (``RecordID`` is
  UNHASHABLE on SDK 2.0.0; decode with ``str(record.id)``, never a ``split(":")``; you
  cannot reach through a field at the RELATE arrow).  **This file re-probes nothing.**
* ``docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-probe-pkt04-store.md`` §5 (P4) —
  the recursive-path facts, MEASURED on spike-surreal 3.2.1 2026-07-26 and SETTLED:
  ``@.{1..n}`` returns TERMINAL-DEPTH nodes only; ``+collect`` is the closure operator;
  ``TIMEOUT`` is a ``SELECT`` clause and a PARSE ERROR on a bare idiom;
  ``{..256+collect}`` TRUNCATES SILENTLY; the working acyclicity detector is *"the task
  appears in its own ``+collect`` reach"* and **the BARE form is NOT a detector** (it
  "worked" by arithmetic accident on a 4-cycle at depth 8).
* ``docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-adversary-04a.md`` §P1 — the four
  wrong builds (W-A/W-B/W-D/W-E) that survived 04a's contract, all four of which recur
  here; each class docstring below names the one it kills.

The shared migration idiom (DDL application, old-world derivation, the live-store
helpers, the edge vocabulary) lives in ``_enforced_relations_scaffold.py`` and is
IMPORTED, never copied — repo law #102.

============================================================================
RED-BY-DESIGN, AND WHAT THIS CONTRACT TURNS RED IN FILES IT DOES NOT OWN
============================================================================

Against ``c5a2552`` this file is RED in every pin describing the CHANGE and GREEN in the
controls.  Which is which is stated in every class docstring, because a contract whose
author cannot say why each pin is red has not written a contract.

It ALSO reddens three pins in ``test_enforced_relations.py``, **deliberately**, by
declaring ``blocks`` in ``_enforced_relations_scaffold.KNOWN_RELATION_EDGES``:

1. ``test_the_relation_edge_set_is_EXACTLY_the_five_known_edges`` — the exact-set pin.
   04a's contract §6.8 wrote this consequence down in advance: *"a ``blocks`` edge reddens
   it until 04b adds it … it forces a deliberate declaration."*  **That reddening IS the
   declaration, not a misfire.**
2. ``test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS[blocks]``
3. ``test_the_edge_declares_its_IN_and_OUT_endpoint_tables[blocks-endpoints4]``

All three go GREEN the moment the builder emits the edge, and **none of them may be
"fixed" by removing ``blocks`` from the declared set or by adding it to
``DEFERRED_TO_PACKET_43``** — the latter is measured wrong build **W-C**, and it reddens
only ``test_derivation_source_unification.py``, a file a 04b-1 builder might not be
running (04a adversary §RESIDUALS R3).  **The wave gate MUST include that file.**
:class:`TestTheBlocksEdgeIsDeclared` pins the exemption door shut from this side too.

============================================================================
ESCALATIONS — forks this contract had to settle, both readings written down
============================================================================

Recorded here because a picked reading with the alternative written down is not the
defect; a silently-picked one is (repo law; brief-base §2).  Full argument in
``REPORT-contract-04b1.md`` §ESCALATIONS.  Each is ONE edit to overturn.

* **E-1 — edge DIRECTION.**  PINNED: ``RELATE $blocker->blocks->$blocked_task`` (``in`` =
  the blocker, ``out`` = the task that waits).  Reads as English, and it puts the
  NEWLY-CREATED row on the ``out`` side — the side packet 04a MEASURED resolves inside an
  uncommitted transaction (reader §Q2.5).  Alternative: ``task->blocks->blocker``, which
  reads backwards and rides the UNMEASURED ``in`` side.
* **E-2 — the identity rendering when there is no display label.**  A ``blocked_by``
  entry is a bare id; a task has no name at the call site.  PINNED: the shared renderer
  emits ``name (id)`` where a label was supplied (the agent case, byte-identical to
  04a's pinned sentence) and the BARE id where none was (the task case).  Alternative:
  force a label, rendering ``abc (abc)`` — which teaches a reader that a task has a name
  equal to its id, a trust-doctrine wart.
* **E-3 — the transitive read's DIRECTION and its BOUND behaviour.**  PINNED: the helper
  serves a task's TRANSITIVE BLOCKERS (upstream — what it is waiting on, which is what
  04b-2's *"renders its critical path"* needs), and it is HONEST at its bound: a typed
  result carrying ``truncated``, never a silently short list (probe §5.3 measured
  ``{..256+collect}`` truncating with no error and no signal; a silent truncation on a
  served surface is a trust-doctrine defect).  Alternative for the bound: RAISE — rejected
  because it makes a legitimately deep DAG unreadable rather than honestly partial.
* **E-4 — #247's check ORDER.**  PINNED: the SENDER is validated in its own call, BEFORE
  the recipients, with its own error vocabulary.  A message from a ghost is worse than a
  message TO one, and folding the sender into the recipient call would raise
  ``UnknownRecipientError`` for a bad SENDER — a refusal that mis-teaches.  Cost, stated:
  one extra round trip on the send path.  Alternative: one call, one error class.

============================================================================
WHAT THIS FILE DOES NOT PIN
============================================================================

* Any RENDER.  The blocked-chain / critical-path render is **04b-2's** (§04b SPLIT).
* Concurrency.  Two racers forming a cycle neither sees is a real TOCTOU (reader §Q6-O16);
  a contract pin is the wrong instrument (≥8-way × 20 consecutive green runs).  Flagged in
  the report, NOT silently dropped.
* The engine cost of a fifth ``ENFORCED`` edge (reader §Q6-O17, unmeasured on 3.2.1).
"""

from __future__ import annotations

import ast
import inspect
import uuid
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _enforced_relations_scaffold import (
    BLOCKS_RELATION_NAME,
    DEFERRED_TO_PACKET_43,
    KNOWN_RELATION_EDGES,
    apply_ddl,
    every_emitted_relation_table,
    ghost_id,
    is_enforced,
    migration_db,  # noqa: F401 - re-exported pytest fixture
    record_exists,
    relate,
    relation_table_statements,
    seed_endpoint,
    statements,
    unenforced_ddl,
)
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealConnection,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.store.surreal import SurrealStoreError
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    MESSAGE_TABLE,
    TASK_TABLE,
    TO_RELATION,
    generate_agent_ddl,
    generate_ddl,
    generate_task_ddl,
)
from loremaster.tasks import (
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    TaskLedger,
    TaskLedgerError,
    TaskNotFoundError,
)
from surrealdb import RecordID

# --------------------------------------------------------------------------- #
# THE NAME-KEYED SURFACE — kept as small as the instruments allow, and every entry
# justified, because a name list is the instrument shape this repo has the most
# receipts against (CLAUDE.md, "the instrument lesson": six defeats, one shape).
#
# Everything that CAN be derived from a VALUE is derived from a value below: the error
# hierarchy is read off the raised exceptions, the edge set off the emitted DDL text, the
# ledger's verb set off its own AST.  What remains here are MUTATION POINTS — and a
# mutation point has a name, unavoidably (repo law: prove sharing by MUTATION, never by
# inspection).  Each one fails CLOSED: ``monkeypatch.setattr(..., raising=True)`` and
# ``getattr`` with no default redden rather than silently skipping.
#
# ⚠ RENAMING ANY OF THESE IS LEGAL AND COSTS ONE EDIT, HERE.  A red pin whose message
# names one of these constants is a NAMING mismatch, not a behavioural one — fix it here
# and say so in the wave report; do NOT weaken the pin.
# --------------------------------------------------------------------------- #

#: Packet 04a's shared policy module.  L3 rules that the blocker-existence check is a
#: GENERALISATION of what already lives here, never a sibling implementation: 04a's
#: ``reject_unknown_agents`` / ``format_unknown_agent_refusal`` own a POLICY (existence
#: probe + refusal rendering), and a ``reject_unknown_tasks`` twin would be copy #2 of it.
SHARED_POLICY_MODULE = "loremaster.agent_existence"

#: The GENERALISED policy's name — the row-existence decision, parameterised by table and
#: label, that BOTH 04a's agent adapter and 04b-1's blocker check must route through.
#: This is the mutation point for the two neutralising legs in section G.
SHARED_POLICY_ATTR = "reject_unknown_rows"

#: The GENERALISED refusal formatter's name.  ONE sentence skeleton, two vocabularies —
#: mutating it must change BOTH families' served text (L3, verbatim: *"change the shared
#: refusal text and BOTH the agent pins and the new task pins must go RED"*).
SHARED_FORMATTER_ATTR = "format_unknown_row_refusal"

#: The ledger-level transitive read (04b-2 renders it; this packet only serves it).
TRANSITIVE_BLOCKERS_ATTR = "transitive_blockers"

#: The module constant carrying the helper's DEFAULT depth bound.  A constant rather than
#: a literal so the bound is greppable, and so the pins below can exercise a DIFFERENT
#: explicit depth — a fixture that only ever used the default would be a monoculture over
#: the one value the code was written against.
MAX_DEPTH_CONSTANT = "TASK_BLOCKER_MAX_DEPTH"

#: SurrealDB's hard recursion ceiling (probe §5.3: ``{..257}`` raises *"Found 257 for
#: bound but expected 256 at most"*).  Our default must sit well inside it.
ENGINE_RECURSION_CEILING = 256


def _shared_policy() -> Any:
    """The shared row-existence policy module, imported at CALL time.

    ⚠ CALL-TIME, like 04a's own handle and for its reason (finding #133): a module-level
    import of a name that does not exist yet makes this whole file UNCOLLECTABLE rather
    than RED, and an uncollectable file DELETES its pins from the run instead of failing
    them.  Every BEHAVIOURAL pin below is written against the EXISTING public surface and
    needs none of this; only section G's sharing proofs reach for it.
    """
    import importlib

    return importlib.import_module(SHARED_POLICY_MODULE)


def _transitive_blockers(ledger: TaskLedger, task_id: str, **kwargs: Any) -> Any:
    """Call the ledger's transitive-blocker helper, failing CLOSED if it is absent."""
    helper = getattr(ledger, TRANSITIVE_BLOCKERS_ATTR, None)
    assert helper is not None, (
        f"TaskLedger.{TRANSITIVE_BLOCKERS_ATTR} does not exist. Packet 04b-1 owes a "
        f"LEDGER-level transitive blocker read — the render is 04b-2's, but the read is "
        f"this packet's (§04b SPLIT). See this file's E-3 escalation for the pinned shape."
    )
    return helper(task_id, **kwargs)


# --------------------------------------------------------------------------- #
# FIXTURE VOCABULARY — the identities, and why each SHAPE is here.
#
# AXIS: id SHAPE (04a cold-audit residual R-2, and reader §Q4 axis A1).  A hand-rolled
# ``str(row["id"]).split(":", 1)[-1]`` is right for ``task:abc`` and WRONG for a
# uuid-shaped id, which the SDK renders ``task:⟨0199c4f1-…⟩`` — that exact guess cost 130
# red pins across two suites (store reference §7; finding #248 records SEVEN hand-rolled
# copies of that parse package-wide, and ``tasks.py`` is on the list, so an EIGHTH is one
# careless line away in exactly the file this packet edits).
#
# AXIS: value MONOCULTURE (adversary W-B).  A "policy" that never queries the store —
# ``refuse iff id == "<the one literal>"`` — passed 04a's whole contract 38/38.  So no
# negative leg below uses one literal: every one is parametrised over all four shapes.
# --------------------------------------------------------------------------- #

#: A bare 32-hex id — the shape ``TaskLedger`` itself mints (``uuid4().hex``).  A phantom
#: blocker of the NATIVE shape, so a refusal keyed on "looks wrong" accepts it.
PHANTOM_TASK_ID_NATIVE_SHAPE = "0" * 32

#: A DASHED uuid.  ``str(RecordID("task", <this>))`` renders ``task:⟨0199c4f1-…⟩`` — the
#: bracketed rendering, i.e. the D-d.1 hazard, LIVE for tasks because ``create_many``
#: accepts caller-supplied ids and ``blocked_by`` is an unconstrained ``array<string>``.
PHANTOM_TASK_ID_UUID_SHAPE = "0199c4f1-7d2a-4e51-9a63-000000000000"

#: An ALL-NUMERIC id.  SurrealDB renders a numeric record-id component WITHOUT the table
#: separator conventions a hex id has, so this is a third distinct rendering.
PHANTOM_TASK_ID_NUMERIC_SHAPE = "20260728"

#: A DASH-BEARING but non-uuid id — the fourth shape, and the one nearest to a temp KEY,
#: which is what ``AppContext._create_many`` passes THROUGH when a key resolves to nothing
#: (``key_to_id.get(ref, ref)``, scout §A2-FLAG 3).  This is the realistic phantom.
PHANTOM_TASK_ID_KEY_SHAPE = "wave-7-charter"

#: Every phantom shape, as a parametrisation.  FIXTURES MUST DISCRIMINATE: if the code can
#: branch on a value, at least one pin must use a DIFFERENT value.
PHANTOM_TASK_IDS = (
    PHANTOM_TASK_ID_NATIVE_SHAPE,
    PHANTOM_TASK_ID_UUID_SHAPE,
    PHANTOM_TASK_ID_NUMERIC_SHAPE,
    PHANTOM_TASK_ID_KEY_SHAPE,
)

#: Realistic work items, drawn from this repo's own backlog (the house idiom in
#: ``test_task_ledger.py`` — never ``foo``/``bar``).
SUBJECT = "Mirror blocked_by onto the blocks DAG edge"
DESCRIPTION = "The edge and the column must agree at every write path, for every input."
CREATOR = "contract-04b1"
ACTOR = "builder-04b1"


def _served_task_refusal(*ids: str) -> str:
    """The EXACT sentence a caller naming a phantom blocker is served.

    ⚠ **DELIBERATELY NOT DERIVED FROM PRODUCTION'S FORMATTER.**  A pin that asked the
    formatter what the text is would agree with it by construction and could never fail —
    the tautology in a new costume.  This IS the spec of the served surface (04a's
    ``_served_refusal`` is the same instrument for the agent half, and this one is
    deliberately its SIBLING SENTENCE so the shared skeleton is visible in both files).

    ``ids`` are passed already in the order the served text must show them, so a build
    that stopped sorting reddens here.

    THE CONSUMER IS AN AGENT (the trust doctrine): this string is the whole of what a
    refused caller learns, so it names EVERY unresolved id — which is precisely what
    ``ENFORCED`` structurally cannot do (store reference §4: ONE bad endpoint, as untyped
    prose, only AFTER the write, and the seam's error hygiene withholds even that).
    """
    return (
        f"unknown task(s): {', '.join(ids)} — every blocked_by id must name an existing "
        f"task row before a task can be created blocked on it"
    )


# =========================================================================== #
# SECTION A — THE EMITTED DDL.  Offline pins, no store.
#
# RED TODAY: every pin in this section (no ``blocks`` relation exists anywhere — MEASURED
# by a BARE, anchor-free grep over ``loremaster/loremaster/**.py``, scout §A1, re-derived
# by this contract's author 2026-07-28: zero schema hits, zero ``BLOCKS_RELATION`` hits).
# =========================================================================== #


def _blocks_statement(ddl: str) -> str:
    """The ``blocks`` ``DEFINE TABLE`` statement inside ``ddl``, or a teaching failure."""
    emitted = relation_table_statements(ddl)
    assert BLOCKS_RELATION_NAME in emitted, (
        f"this DDL emits no {BLOCKS_RELATION_NAME!r} relation table. Packet 04b-1 adds it "
        f"to surreal_schema::_task_statements — the ONE site feeding BOTH "
        f"generate_task_ddl and generate_ddl (scout §A1-NOTE). Emitted relation tables "
        f"here: {sorted(emitted)}"
    )
    return emitted[BLOCKS_RELATION_NAME]


class TestTheBlocksEdgeIsEmittedByBOTHGenerationPaths:
    """RED today.  ⛔ **The pin that kills "declared in the wrong place".**

    ``generate_ddl()`` is NOT the whole schema: it composes the chunk/file/memory/trace/
    meta/snapshot/command/**task**/finding slices and NOTHING comms or graph (scout
    §A1-NOTE, MEASURED).  The comms and graph tables ride their own generators.  So there
    is exactly ONE site — ``_task_statements`` — that both ``generate_task_ddl`` (applied
    by ``TaskLedger.ensure_ready``) and ``generate_ddl`` consume, and **putting the edge
    anywhere else creates a table one path defines and the other does not.**

    A store built by the full ``generate_ddl`` would then hold ``blocks`` as an
    AUTO-CREATED ``TYPE ANY`` table on first RELATE — which store reference §5 records as
    *silently discarding the ``IN``/``OUT`` guard*, i.e. the guard downgrades without
    failing.  That is a defect no per-path pin can see; only the both-paths pin can.
    """

    @pytest.mark.parametrize(
        ("label", "generator"),
        [
            ("generate_task_ddl", generate_task_ddl),
            ("generate_ddl", lambda: generate_ddl(dim=PRODUCTION_DIM)),
        ],
    )
    def test_the_path_emits_the_blocks_relation_table(
        self, label: str, generator: Callable[[], str]
    ) -> None:
        """Each generation path emits it. Parametrised, so a miss NAMES the path."""
        assert _blocks_statement(generator()), label

    def test_BOTH_paths_emit_the_IDENTICAL_blocks_statement(self) -> None:
        """⛔ The pin that kills a build declaring the edge TWICE, differently.

        DERIVED equality — not two hand-written expectations, which could agree with each
        other and disagree with production.  A builder who adds a ``_blocks_statements()``
        helper wired into ``generate_task_ddl`` only, and leaves ``generate_ddl`` to a
        second declaration, reddens here even if both say ``ENFORCED``.
        """
        from_slice = _blocks_statement(generate_task_ddl())
        from_full = _blocks_statement(generate_ddl(dim=PRODUCTION_DIM))
        assert from_slice == from_full, (
            "the task SLICE and the FULL ddl emit DIFFERENT blocks declarations. There "
            "must be exactly one emitter (surreal_schema::_task_statements), consumed by "
            f"both: slice={from_slice!r} full={from_full!r}"
        )

    def test_the_blocks_table_is_declared_AFTER_the_task_table_in_BOTH_paths(self) -> None:
        """The SELF-order-dependence nobody has examined (reader §Q2.4 item 6).

        04a's ``briefed`` flip made the brief slice order-dependent on the AGENT slice, and
        pinned it.  ``task->blocks->task`` is a different and unexamined shape: the slice
        becomes order-dependent on ITSELF.  ``DEFINE TABLE blocks … IN task OUT task``
        names a table that the SAME slice defines, so the statement order inside
        ``_task_statements`` is load-bearing rather than cosmetic.

        Pinned by POSITION in the emitted statement list — the property, not the recipe.
        """
        for label, generator in (
            ("generate_task_ddl", generate_task_ddl),
            ("generate_ddl", lambda: generate_ddl(dim=PRODUCTION_DIM)),
        ):
            emitted = statements(generator())
            task_prefix = f"DEFINE TABLE IF NOT EXISTS {TASK_TABLE} "
            task_at = next(
                (i for i, s in enumerate(emitted) if s.startswith(task_prefix)), None
            )
            blocks_at = next(
                (i for i, s in enumerate(emitted) if f" {BLOCKS_RELATION_NAME} TYPE RELATION" in s),
                None,
            )
            assert task_at is not None, f"{label}: no DEFINE TABLE for {TASK_TABLE!r} at all"
            assert blocks_at is not None, f"{label}: no {BLOCKS_RELATION_NAME!r} relation table"
            assert task_at < blocks_at, (
                f"{label}: the {BLOCKS_RELATION_NAME!r} relation table is declared at "
                f"position {blocks_at}, BEFORE the {TASK_TABLE!r} table it names as both "
                f"endpoints (position {task_at}). The task slice is now order-dependent on "
                f"ITSELF — record that in _task_statements' docstring as 04a recorded the "
                f"brief slice's dependency on the agent slice"
            )


class TestTheBlocksEdgeIsGuardedFromBirth:
    """RED today.  The clause pins — ``ENFORCED``, ``OVERWRITE``, and the endpoint types.

    Operator ruling **R3**: ``blocks`` ships ``ENFORCED`` **from birth**, with an app-level
    pre-check beside it.  Neither is redundant (store reference §4): ``ENFORCED`` guards
    the TABLE — including the ``INSERT RELATION`` door an app check on one verb can never
    reach — while only the app check can TEACH, because the seam's error hygiene (#31)
    replaces the engine's *"The record 'task:x' does not exist"* with *"statement N of M
    was rejected (unspecified rejection); see the server log"*.

    ⚠ The ``OVERWRITE`` pin is not decoration on a NEW table.  It is the pin that keeps the
    edge migratable FOREVER: the day anyone changes ``IN``/``OUT``/``ENFORCED``,
    ``IF NOT EXISTS`` would be a MEASURED silent no-op on the existing table (store
    reference §1.1, re-probed on 3.2.1) and the change would never reach a live store —
    #107, exactly, and invisible to every virgin-DB fixture.
    """

    @pytest.mark.parametrize("label", ["generate_task_ddl", "generate_ddl"])
    def test_the_blocks_edge_carries_ENFORCED_in_its_own_slice(self, label: str) -> None:
        ddl = generate_task_ddl() if label == "generate_task_ddl" else generate_ddl(dim=PRODUCTION_DIM)
        statement = _blocks_statement(ddl)
        assert is_enforced(statement), (
            f"{label}: {BLOCKS_RELATION_NAME} must be declared ENFORCED from birth "
            f"(operator ruling R3) — it is the only guard that validates BOTH endpoints "
            f"and covers INSERT RELATION: {statement!r}"
        )

    def test_the_blocks_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS(self) -> None:
        statement = _blocks_statement(generate_task_ddl())
        assert statement.startswith(f"DEFINE TABLE OVERWRITE {BLOCKS_RELATION_NAME} "), (
            f"{BLOCKS_RELATION_NAME}'s relation clause must be OVERWRITE. IF NOT EXISTS is "
            f"a MEASURED silent no-op on an existing edge table (store reference §1.1) — "
            f"harmless on the day the table is created, and #107 on the day anyone changes "
            f"IN/OUT/ENFORCED: {statement!r}"
        )

    def test_the_blocks_edge_declares_IN_task_OUT_task(self) -> None:
        """``ENFORCED`` is meaningless without ``IN``/``OUT``: the clause validates that the
        endpoints EXIST, the typing validates that they are of the right TABLE, and both
        halves are wanted.  ``IN task OUT task`` also pins ESCALATION E-1's direction at
        the type level: a self-referential edge over one table.
        """
        statement = _blocks_statement(generate_task_ddl())
        assert f"IN {TASK_TABLE} OUT {TASK_TABLE}" in statement, (
            f"{BLOCKS_RELATION_NAME} must declare IN {TASK_TABLE} OUT {TASK_TABLE}: "
            f"{statement!r}"
        )

    def test_the_blocks_edge_carries_NO_required_edge_field(self) -> None:
        """The edge is a PURE MIRROR of ``blocked_by`` — pinned, because it constrains
        every RELATE in this file and in production.

        ``blocked_by`` is an ``array<string>`` carrying no per-dependency metadata, so an
        edge field would make the edge hold state the column cannot, and the mirror
        invariant (section D) could not be STATED, let alone checked.  A builder who adds a
        required ``at``/``via`` column to ``blocks`` reddens here and must escalate rather
        than quietly widen the edge.

        MEASURED PROPERTY, not a text scan: no ``DEFINE FIELD`` statement in either
        generation path targets the edge.
        """
        for label, generator in (
            ("generate_task_ddl", generate_task_ddl),
            ("generate_ddl", lambda: generate_ddl(dim=PRODUCTION_DIM)),
        ):
            fields = [
                s
                for s in statements(generator())
                if s.startswith("DEFINE FIELD") and f" ON {BLOCKS_RELATION_NAME}" in s
            ]
            assert fields == [], (
                f"{label}: {BLOCKS_RELATION_NAME} must carry no edge-local field — it is a "
                f"pure mirror of blocked_by. Found: {fields}"
            )


class TestTheBlocksEdgeIsDeclared:
    """The DELIBERATE DECLARATION, and the exemption door pinned shut from this side.

    RED today: the schema exports no ``BLOCKS_RELATION`` constant.
    GREEN today: the two declaration pins — this contract already added ``blocks`` to
    ``KNOWN_RELATION_EDGES`` and did NOT add it to ``DEFERRED_TO_PACKET_43``.

    ⛔ **The pin that kills W-C** (adversary §P1: *escape the ∀ by widening the
    exemption*), from a file the 04b-1 builder IS running.  04a killed W-C too, but its
    forward-looking half is guarded only by ``test_derivation_source_unification.py``, and
    the adversary's §RESIDUALS R3 says outright: *"the wave's gate must include that file,
    or a future author who widens the exemption goes green on the file they are editing."*
    This class removes that dependency for ``blocks`` specifically — it does NOT remove the
    obligation to run that file, which still guards the exemption's exact contents.
    """

    def test_the_schema_exports_BLOCKS_RELATION_under_this_exact_name(self) -> None:
        """The edge name is a module CONSTANT, like its four siblings — never a literal
        typed at each site.  ``_enforced_relations_scaffold`` currently carries the name as
        a string (see its ``BLOCKS_RELATION_NAME`` comment for why an import would make
        three files uncollectable); this pin is what holds the two equal.
        """
        from loremaster.store import surreal_schema

        constant = getattr(surreal_schema, "BLOCKS_RELATION", None)
        assert constant == BLOCKS_RELATION_NAME, (
            f"surreal_schema must export BLOCKS_RELATION == {BLOCKS_RELATION_NAME!r} "
            f"(got {constant!r}), beside BRIEFED_RELATION / TO_RELATION / REFERS_RELATION "
            f"/ ANSWERS_TO_RELATION. Once it exists, _enforced_relations_scaffold's "
            f"BLOCKS_RELATION_NAME literal may be replaced by the import, in one edit"
        )

    def test_blocks_is_in_the_DECLARED_edge_set(self) -> None:
        assert KNOWN_RELATION_EDGES.get(BLOCKS_RELATION_NAME) == (TASK_TABLE, TASK_TABLE), (
            "blocks must be declared in _enforced_relations_scaffold.KNOWN_RELATION_EDGES "
            f"with its endpoints, and they must be ({TASK_TABLE}, {TASK_TABLE})"
        )

    def test_blocks_is_NOT_in_the_DEFERRED_exemption_set(self) -> None:
        """⛔ W-C.  The ∀ pin ``test_EVERY_relation_table_the_schema_emits_is_ENFORCED``
        takes exactly ONE deny-by-default exemption, ``DEFERRED_TO_PACKET_43``, and a
        builder meeting that pin red can silence it by widening the exemption instead of
        shipping the guard.  ``blocks`` is packet 04b-1's, not packet 43's — the exemption
        is for the two CODE-GRAPH edges whose flip is blocked on a derivation-source fix.
        """
        assert BLOCKS_RELATION_NAME not in DEFERRED_TO_PACKET_43, (
            f"{BLOCKS_RELATION_NAME} was added to DEFERRED_TO_PACKET_43. That set exempts "
            f"the two CODE-GRAPH edges (refers/answers_to) whose flip needs packet 43's "
            f"derivation-source unification. Deferring the blocks guard is a SCOPE "
            f"decision that belongs to the operator, not a way to silence a red ∀ pin — "
            f"operator ruling R3 says blocks ships ENFORCED from BIRTH"
        )

    def test_the_universal_pin_now_covers_blocks(self) -> None:
        """The ∀ instrument reaches the fifth edge.  RED today (nothing emits it), and the
        pin that makes ``blocks`` subject to the same law as its four siblings.

        Deliberately re-asserted HERE as well as in ``test_enforced_relations.py``: that
        file's ∀ sweeps the emitters and would also catch it, but a 04b-1 builder reading
        only its own contract must be able to see the law it is being held to.
        """
        emitted = every_emitted_relation_table()
        assert BLOCKS_RELATION_NAME in emitted, (
            f"the ∀ sweep over every DDL generator found no {BLOCKS_RELATION_NAME!r} "
            f"relation table. Emitted: {sorted(emitted)}"
        )
        _label, statement = emitted[BLOCKS_RELATION_NAME]
        assert is_enforced(statement), statement


# =========================================================================== #
# SECTION B — THE DIRTY-STORE MIGRATION AND THE UN-ENFORCING DOOR.
#
# THE TEST ENVIRONMENT IS A FICTION.  Every test mints a VIRGIN database
# (``_surreal_harness.unique_database``), and on a virgin database ANY clause creates the
# table with whatever the generator says — so a guard that never MIGRATES is invisible to
# every offline pin and every ordinary live pin.  Production is a LONG-LIVED store that
# already holds ``task`` rows and has never heard of ``blocks``.
#
# ⚠ AND THE HAZARD IS NOT HYPOTHETICAL FOR A *NEW* TABLE.  Store reference §5: a RELATE
# onto an UNDECLARED table auto-creates it ``TYPE ANY``, silently discarding the IN/OUT
# guard.  So the realistic dirty store is not "no blocks table" — it is "a blocks table
# that already exists, untyped, holding rows nobody guarded", which is exactly what a
# deploy of 04b-1's ledger code WITHOUT its DDL, or a rollback, produces.
#
# RED TODAY: every pin except the two BASELINE/anti-vacuity controls.
# =========================================================================== #


def _task_ddl_without_blocks() -> str:
    """Today's task DDL with the ``blocks`` declaration REMOVED — the OLD WORLD.

    DERIVED from the production emitter, never hand-written, for the reason 04a's
    ``old_world_ddl`` states: a hand-copied old-DDL string tests a COPY of the code and
    passes while production stays broken (scout §S4).  Here the derivation is a REMOVAL
    rather than a re-emission, because ``blocks``' old world is a store that never had the
    table at all.

    Its non-vacuity gets its own pin (``TestTheOldWorldIsGenuinelyOlder``), so the
    BASELINE and survival controls stay readable-green.
    """
    current = generate_task_ddl()
    kept = [s for s in statements(current) if f" {BLOCKS_RELATION_NAME} TYPE RELATION" not in s]
    return ";\n".join(kept) + ";\n"


async def _blocks_edge_count(connection: SurrealConnection) -> int:
    """The RAW total ``blocks`` edge count — a read that SEES orphan edges.

    Raw, because a traversal cannot distinguish a ghost at all: store reference §6.4
    MEASURED that ``SELECT ->edge->t`` lists a dangling endpoint as a FIRST-CLASS MEMBER
    and the vendor's *"returns an empty array"* claim is FALSE.  Counting the edge ROWS is
    the only reading that answers "did an edge land".
    """
    rows = await run(connection, f"SELECT count() FROM {BLOCKS_RELATION_NAME} GROUP ALL")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


@pytest_asyncio.fixture()
async def dirty_task_store(
    migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the imported fixture
) -> AsyncIterator[tuple[SurrealConnection, SurrealEnv, str, str]]:
    """A store in the OLD world: task rows, and a ``blocks`` edge nobody guards.

    Five steps, cloned in shape from ``test_enforced_relations.py``'s
    ``_dirty_old_world`` (scout §S4's idiom): apply the OLD DDL, seed two real task rows,
    write a DANGLING edge to a task that does not exist, and hand back both ids.

    Yields ``(connection, env, real_task_id, ghost_task_id)``.
    """
    connection, env = migration_db
    await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
    real_task_id = f"real_{uuid.uuid4().hex}"
    ghost_task_id = ghost_id("ghost_task")
    await seed_endpoint(connection, TASK_TABLE, real_task_id)
    assert not await record_exists(connection, TASK_TABLE, ghost_task_id), (
        "the negative fixture's task id must genuinely NOT exist"
    )
    yield connection, env, real_task_id, ghost_task_id


class TestTheOldWorldIsGenuinelyOlder:
    """RED today, and it is the pin that keeps this whole section honest.

    Every migration pin below applies an "old" DDL and then the current one.  If the two
    are IDENTICAL the pins migrate a schema to ITSELF and test NOTHING while looking
    perfectly green — a fixture that guarantees the one condition under which the defect is
    invisible, which is the class THE TEST ENVIRONMENT IS A FICTION exists to name.
    """

    def test_the_old_world_DIFFERS_from_todays_task_ddl(self) -> None:
        assert _task_ddl_without_blocks() != generate_task_ddl(), (
            "the derived OLD world is byte-identical to today's task DDL, so every "
            "migration pin in section B is migrating a schema to itself and proving "
            "nothing. Today's DDL must emit a blocks relation table that the old world "
            "does not"
        )


class TestTheLedgersOwnMigrationPathLandsTheGuard:
    """⛔ **The pins that kill W-A** — *the emitter is perfect and the guard never LANDS.*

    MEASURED on 04a (adversary §P1 W-A): a build whose ``ensure_ready`` stripped the clause
    out of its own generated DDL passed the contract **38/38** and **6 failed / 2073
    passed** across seven suites — the SAME six the correct build has.  ZERO new failures
    repo-wide.  Every migration pin 04a had at the time applied the DDL ITSELF, so none of
    them could see it.

    These pins therefore drive ``TaskLedger.ensure_ready()`` — the PRODUCTION entry point —
    **and nothing else**.  Offline pins prove the RECIPE; only this proves the CAKE.

    ⚠ Reader §Q2.4 item 4 flagged that no 04a report established whether ``TaskLedger``
    even HAS an ``ensure_ready``.  It does (``tasks.py::TaskLedger.ensure_ready``, applying
    ``generate_task_ddl()`` inside ONE ``BEGIN … COMMIT`` via ``execute_transaction``,
    verified 2026-07-28), so ``TaskLedger`` is the correct owner to drive.
    """

    @staticmethod
    def _ledger_on(env: SurrealEnv) -> TaskLedger:
        return TaskLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )

    async def test_BASELINE_the_old_world_really_ACCEPTS_a_dangling_blocks_edge(
        self, dirty_task_store: tuple[SurrealConnection, SurrealEnv, str, str]
    ) -> None:
        """GREEN today (and after).  The control WITHOUT which every pin below is vacuous:
        it proves the old world is genuinely un-guarded, so a later rejection is caused by
        the migration rather than by the fixture.

        Store reference §5: the undeclared edge table auto-creates ``TYPE ANY``, which is
        why this succeeds at all — and is itself the silent guard-downgrade this packet
        closes.
        """
        connection, _env, real_task_id, ghost_task_id = dirty_task_store
        await relate(
            connection,
            BLOCKS_RELATION_NAME,
            in_table=TASK_TABLE,
            in_id=ghost_task_id,
            out_table=TASK_TABLE,
            out_id=real_task_id,
        )
        assert await _blocks_edge_count(connection) == 1, (
            "the OLD world must accept a dangling blocks edge — if it does not, every "
            "migration pin below passes for a fixture reason"
        )

    async def test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE(
        self, dirty_task_store: tuple[SurrealConnection, SurrealEnv, str, str]
    ) -> None:
        """RED today.  ⛔ W-A.  ``ensure_ready`` and nothing else."""
        connection, env, real_task_id, ghost_task_id = dirty_task_store
        ledger = self._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        with pytest.raises(Exception):  # noqa: B017 - the engine's own rejection type
            await relate(
                connection,
                BLOCKS_RELATION_NAME,
                in_table=TASK_TABLE,
                in_id=ghost_task_id,
                out_table=TASK_TABLE,
                out_id=real_task_id,
            )

    async def test_POSITIVE_CONTROL_ensure_ready_still_accepts_two_REAL_endpoints(
        self, dirty_task_store: tuple[SurrealConnection, SurrealEnv, str, str]
    ) -> None:
        """The control the pin above needs.  A build that rejected EVERY RELATE — a broken
        DDL, a wrong endpoint type, a botched migration — would satisfy it.  Here the same
        migration runs and a RELATE between two REAL tasks must still land.
        """
        connection, env, real_task_id, _ghost = dirty_task_store
        second_id = f"real_{uuid.uuid4().hex}"
        await seed_endpoint(connection, TASK_TABLE, second_id)
        ledger = self._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        await relate(
            connection,
            BLOCKS_RELATION_NAME,
            in_table=TASK_TABLE,
            in_id=real_task_id,
            out_table=TASK_TABLE,
            out_id=second_id,
        )
        assert await _blocks_edge_count(connection) == 1

    async def test_the_PRE_EXISTING_dangling_edge_and_the_task_ROWS_SURVIVE(
        self, dirty_task_store: tuple[SurrealConnection, SurrealEnv, str, str]
    ) -> None:
        """RED today.  Two properties in one migration, both from store reference §4.

        1. ``DEFINE TABLE OVERWRITE`` preserves fields, indexes and ROWS — the task rows a
           long-lived store already holds must survive their table's slice being re-applied.
        2. Pre-existing dangling edges are *"entirely unaffected … turning it on and
           calling the ghost problem closed is a FALSE ALL-CLEAR"*.  Pinned as a SURVIVAL,
           not a cleanup: cleanup is operator-ruled OUT as **#236** (*"We're on a
           localhost"*), with a named re-open trigger — the first non-local deployment.

        ⚠ Nobody has measured how many ghosts a real store holds; any number quoted before
        that sweep runs is a rumour (packet §Scope OUT).
        """
        connection, env, real_task_id, ghost_task_id = dirty_task_store
        await relate(
            connection,
            BLOCKS_RELATION_NAME,
            in_table=TASK_TABLE,
            in_id=ghost_task_id,
            out_table=TASK_TABLE,
            out_id=real_task_id,
        )
        ledger = self._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert await _blocks_edge_count(connection) == 1, (
            "the pre-existing dangling edge was destroyed by the migration. ENFORCED "
            "guards FUTURE writes only (store reference §4); a migration that silently "
            "deletes rows is a data-loss bug, and cleanup is #236's, not this packet's"
        )
        assert await record_exists(connection, TASK_TABLE, real_task_id), (
            "a pre-existing task row did not survive its slice being re-applied"
        )

    async def test_the_migration_is_IDEMPOTENT_on_an_ALREADY_migrated_store(
        self, dirty_task_store: tuple[SurrealConnection, SurrealEnv, str, str]
    ) -> None:
        """RED today.  ``ensure_ready`` runs at EVERY boot, so a clause that raises the
        second time is a boot-time crash — the exact failure mode that makes ``DEFINE
        SEQUENCE``/``DEFINE INDEX`` keep ``IF NOT EXISTS`` (store reference §1.1).
        """
        connection, env, real_task_id, ghost_task_id = dirty_task_store
        ledger = self._ledger_on(env)
        try:
            await ledger.ensure_ready()
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        with pytest.raises(Exception):  # noqa: B017
            await relate(
                connection,
                BLOCKS_RELATION_NAME,
                in_table=TASK_TABLE,
                in_id=ghost_task_id,
                out_table=TASK_TABLE,
                out_id=real_task_id,
            )


class TestTheUnEnforcingDoor:
    """RED today.  The REGRESSION door, and it is invisible on a virgin DB.

    Probe §3(a): ``DEFINE TABLE OVERWRITE <edge> TYPE RELATION IN a OUT b SCHEMAFULL`` —
    the same statement MINUS ``ENFORCED`` — **silently un-guards** an already-guarded
    table.  No error, no signal.  On a virgin database the un-enforced clause and the
    enforced one both "work", so only a store that was ALREADY guarded can see it.

    This is the fifth edge's leg of the packet's *"one dirty-store pin per edge"*
    requirement.  Its mutation half — deleting ``enforced=True`` from the generator call —
    is declared in the ``MUTATION_PROOF`` block at the foot of this file.
    """

    async def test_re_emitting_blocks_WITHOUT_ENFORCED_silently_un_guards_it(
        self, dirty_task_store: tuple[SurrealConnection, SurrealEnv, str, str]
    ) -> None:
        connection, env, real_task_id, ghost_task_id = dirty_task_store
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        with pytest.raises(Exception):  # noqa: B017 - the guard is live
            await relate(
                connection,
                BLOCKS_RELATION_NAME,
                in_table=TASK_TABLE,
                in_id=ghost_task_id,
                out_table=TASK_TABLE,
                out_id=real_task_id,
            )
        await apply_ddl(
            connection,
            unenforced_ddl(BLOCKS_RELATION_NAME, TASK_TABLE, TASK_TABLE),
            url=env.url,
        )
        await relate(
            connection,
            BLOCKS_RELATION_NAME,
            in_table=TASK_TABLE,
            in_id=ghost_task_id,
            out_table=TASK_TABLE,
            out_id=real_task_id,
        )
        assert await _blocks_edge_count(connection) == 1, (
            "re-emitting the edge WITHOUT ENFORCED did not un-guard it, so this pin is not "
            "observing the door it exists to describe — check that the guard was live "
            "before the re-emission (the raises leg above)"
        )


# =========================================================================== #
# SECTION C — LIVE LEDGER FIXTURES.  Shared by sections C–G.
# =========================================================================== #


@pytest_asyncio.fixture()
async def task_ledger() -> AsyncIterator[tuple[TaskLedger, SurrealEnv, str]]:
    """A REAL :class:`TaskLedger` on a fresh database, plus ONE real task to block on.

    The negative identities are ASSERTED ABSENT — a fixture where every endpoint exists
    cannot discriminate a guarded table from an un-guarded one, which is the packet's own
    *"negative fixtures REQUIRED"* clause and FIXTURES MUST DISCRIMINATE.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await ledger.ensure_ready()
    blocker_id = await ledger.create_task(
        "A blocker that genuinely exists", DESCRIPTION, created_by=CREATOR
    )
    setup = await connect_admin(env)
    try:
        for phantom in PHANTOM_TASK_IDS:
            assert not await record_exists(setup, TASK_TABLE, phantom), (
                f"the negative fixture's task id {phantom!r} must genuinely NOT exist"
            )
    finally:
        await setup.close()
    try:
        yield ledger, env, blocker_id
    finally:
        await ledger.close()
        await drop_database(env)


async def _raw(ledger: TaskLedger, statement: str, params: dict[str, Any] | None = None) -> Any:
    """A RAW read through the ledger's own seam.

    Raw, because the question these pins ask is *"did a row / an edge land at all"*, and
    the public readers filter or raise rather than answering it.
    """
    return await ledger._query(statement, params or {})  # noqa: SLF001 - the atomicity pins need it


async def _task_row_count(ledger: TaskLedger) -> int:
    rows = await _raw(ledger, f"SELECT count() FROM {TASK_TABLE} GROUP ALL")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


async def _edge_blockers_of(ledger: TaskLedger, task_id: str) -> set[str]:
    """The blocker ids reachable through the ``blocks`` EDGE for ``task_id``.

    Reads the edge rows directly (``in``/``out``), never a traversal: store reference §6.4
    MEASURED that a traversal cannot distinguish a ghost endpoint from a real one.
    ``record::id`` decodes the endpoint — never a hand-rolled ``str(...).split(":")``,
    which is right for ``task:abc`` and WRONG for a uuid-shaped id (store reference §7,
    finding #248).
    """
    rows = await _raw(
        ledger,
        f"SELECT VALUE record::id(in) FROM {BLOCKS_RELATION_NAME} WHERE out = $task",
        {"task": RecordID(TASK_TABLE, task_id)},
    )
    return {str(value) for value in rows} if isinstance(rows, list) else set()


async def _column_blockers_of(ledger: TaskLedger, task_id: str) -> list[str]:
    """The stored ``blocked_by`` column of ``task_id`` — an EXPLICIT projection.

    Explicit, not ``SELECT *``: store reference §2 records that ``SELECT *`` OMITS a
    ``NONE``-valued column entirely (``KeyError``), while a projection reads ``None``.
    """
    rows = await _raw(
        ledger,
        f"SELECT blocked_by FROM type::record('{TASK_TABLE}', $id)",
        {"id": task_id},
    )
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return []
    return list(rows[0].get("blocked_by") or [])


async def _assert_mirror(ledger: TaskLedger, task_id: str, *, where: str) -> None:
    """THE INVARIANT: the ``blocks`` edge set ≡ the ``blocked_by`` column, for one task.

    ONE function every write-path pin calls — never a pattern each pin clones (repo law
    #102).  ``where`` names the write path so a failure says which one broke it.
    """
    column = await _column_blockers_of(ledger, task_id)
    edges = await _edge_blockers_of(ledger, task_id)
    assert edges == set(column), (
        f"{where}: the blocks EDGE set and the blocked_by COLUMN disagree for task "
        f"{task_id!r}. column={sorted(column)} edges={sorted(edges)}. The edge is a pure "
        f"mirror of the column and the two are written in ONE transaction; a divergence "
        f"means the mirror is not inside the write txn, or a path was missed"
    )
    assert len(edges) == len(set(column)) == len(column), (
        f"{where}: blocked_by holds a DUPLICATE id ({column}), which the birth-time "
        f"order-preserving dedupe in _new_task_content exists to prevent — and which "
        f"UNIQUE-less edge writes would turn into two edges for one dependency"
    )


# =========================================================================== #
# SECTION D — ATOMICITY, AND THE MIRROR ∀ EVERY WRITE PATH.
# =========================================================================== #


async def _accept_everything(*_args: Any, **_kwargs: Any) -> None:
    """The neutralising stub: it looks at nothing and refuses nothing.

    ⚠ An ACCEPT-EVERYTHING stub, **never a raising sentinel**.  04a's adversary
    (§MISSING-PINS MP-2) measured why: a raising sentinel proves only that the function is
    CALLED, never that it DECIDES, and a build where both ledgers imported and called a
    shared function that returned ``None`` while each kept a private copy underneath passed
    04a's contract 38/38 **and every neighbouring suite**.
    """
    return None


def _neutralise_the_policy(monkeypatch: pytest.MonkeyPatch, module_name: str) -> None:
    """Replace the shared row-existence policy inside ``module_name`` with the stub.

    ``raising=True`` so a module that does not import the policy under
    :data:`SHARED_POLICY_ATTR` reddens rather than silently skipping — the mutation point
    fails CLOSED.
    """
    import importlib

    monkeypatch.setattr(
        importlib.import_module(module_name), SHARED_POLICY_ATTR, _accept_everything, raising=True
    )


class TestCreateTaskIsAtomic:
    """RED today.  ⛔ **The pins that kill W-D** — *write first, compensate afterwards.*

    MEASURED (scout §A2 W1): ``create_task`` is a **bare ``self._query(...)``**, not a
    ``TxnFragment``, not ``_apply``.  The packet's own phrase *"mirror the edge inside the
    existing write txn"* is a NO-OP PHRASE for it — there is no txn.  A builder that meets
    a red mirror pin and simply issues a second ``_query`` for the RELATE arrives exactly
    at W-D, which adversary §P1 measured as **GREENER than correct** on 04a
    (``2 failed, 2077 passed`` vs the correct build's ``6 failed, 2073 passed`` — four MORE
    pre-existing pins pass).  *The incentive gradient points at the wrong build.*

    The instrument: neutralise the app-level check so the ENGINE's ``ENFORCED`` rejection
    is what the RELATE meets, then ask whether a task row exists.

    * CREATE and RELATE in ONE transaction -> the CREATE rolls back -> no row -> GREEN
    * CREATE, then a separately-failable RELATE -> the row is there -> **RED**

    ⚠ These legs are the ONLY place a pin observes both layers on purpose, which is why
    they sit in the ``MUTATION_PROOF`` declared-RED set below while every other app-check
    pin stays out of it.
    """

    async def test_a_create_whose_RELATE_cannot_land_writes_NO_task_row(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        ledger, _env, _blocker = task_ledger
        before = await _task_row_count(ledger)
        _neutralise_the_policy(monkeypatch, "loremaster.tasks")
        with pytest.raises(SurrealStoreError):
            await ledger.create_task(
                SUBJECT, DESCRIPTION, blocked_by=[PHANTOM_TASK_ID_UUID_SHAPE], created_by=CREATOR
            )
        assert await _task_row_count(ledger) == before, (
            "a create whose blocks RELATE was rejected left a task row behind. The CREATE "
            "and the RELATE must ride ONE transaction (self._apply), or every rejected "
            "create leaks an orphan task — and with the mirror broken, a task whose "
            "blocked_by names a blocker with no edge"
        )

    async def test_POSITIVE_CONTROL_the_neutralised_policy_still_lets_a_LEGAL_create_through(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The control the leg above needs, load-bearing twice: a build that raised for
        EVERY create would satisfy it, and so would a run in which the substitution
        silently did not take.  Here the stub is installed identically and a REAL blocker
        must still create cleanly — so the red above is caused by the ID, not the patch.
        """
        ledger, _env, blocker_id = task_ledger
        _neutralise_the_policy(monkeypatch, "loremaster.tasks")
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker_id], created_by=CREATOR
        )
        assert await _edge_blockers_of(ledger, task_id) == {blocker_id}
        await _assert_mirror(ledger, task_id, where="create_task under the neutralised policy")

    async def test_POSITIVE_CONTROL_a_legal_create_writes_BOTH_the_row_AND_the_edges(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The pin that stops the atomicity pins passing by REFUSING EVERYTHING.

        TWO blockers, not one: with a single blocker ``len(edges) == 1`` is satisfied by a
        build that writes exactly one edge regardless of how many dependencies there are —
        the small-N trap where ``len()`` and the real count are indistinguishable.
        """
        ledger, _env, first_blocker = task_ledger
        second_blocker = await ledger.create_task("A second real blocker", DESCRIPTION, created_by=CREATOR)
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[first_blocker, second_blocker], created_by=CREATOR
        )
        assert await _task_row_count(ledger) == 3
        assert await _edge_blockers_of(ledger, task_id) == {first_blocker, second_blocker}
        await _assert_mirror(ledger, task_id, where="create_task with two blockers")

    async def test_create_many_is_ALL_OR_NOTHING_when_ONE_items_RELATE_cannot_land(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """``create_many`` is already transactional (scout §A2 W2) — this pins that the
        EDGES joined that transaction rather than being written after it.

        Pinned SEPARATELY from ``create_task`` on the scout's explicit warning: *"a
        contract that only pins ``create_many`` will miss it"* — and the converse holds
        too, since the two verbs have different txn shapes and a builder may fix one.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, blocker_id = task_ledger
        before = await _task_row_count(ledger)
        _neutralise_the_policy(monkeypatch, "loremaster.tasks")
        specs = [
            TaskSpec(subject="first", description=DESCRIPTION, blocked_by=[blocker_id]),
            TaskSpec(
                                subject="second",
                description=DESCRIPTION,
                blocked_by=[PHANTOM_TASK_ID_NUMERIC_SHAPE],
            ),
            TaskSpec(subject="third", description=DESCRIPTION, blocked_by=[]),
        ]
        with pytest.raises(SurrealStoreError):
            await ledger.create_many(specs, created_by=CREATOR)
        assert await _task_row_count(ledger) == before, (
            "one item's rejected RELATE did not roll back the whole batch — create_many is "
            "documented ALL-OR-NOTHING, so the edges must be in the same transaction as "
            "the CREATEs, not a second pass afterwards"
        )


#: The ``TaskLedger`` verbs that WRITE and must mirror the edge onto ``blocked_by``.
MIRRORING_VERBS = frozenset({"create_task", "create_many", "supersede_task"})

#: The ``TaskLedger`` verbs that WRITE but must NEVER touch the mirror.  MEASURED, scout
#: §A2: ``blocked_by`` is written at BIRTH ONLY and is IMMUTABLE afterwards — the claim
#: path's own docstring leans on it (*"blocked_by never changes after creation, so reading
#: it here is consistent"*).
MIRROR_IMMUTABLE_VERBS = frozenset({"transition", "claim_task"})

#: The ``TaskLedger`` verbs that write no task row at all.  ``transitive_blockers`` is
#: 04b-1's new READ and is declared here, which is what makes the exact-set pin below RED
#: until it exists.
NON_WRITING_VERBS = frozenset(
    {
        "ensure_ready",
        "close",
        "get_task",
        "query_tasks",
        "updated_since",
        TRANSITIVE_BLOCKERS_ATTR,
    }
)


class TestTheMirrorHoldsAtEveryWritePath:
    """RED today.  ⛔ **THE QUANTIFIER LAW** (PR93, 2026-07-13).

    *Never condition an invariant on the failure mode that prompted the work.*  Six PR93
    tests pinned *"no silent drop on supply failure"*; the rewrite dropped an input through
    a different door and every pin stayed green.  So the property here is not *"the mirror
    survives a create"* — it is **the edge set equals ``blocked_by``, for EVERY task, after
    EVERY verb, regardless of how the task got there** — and each verb's fate is FORCED by
    its own fixture below rather than left to a ∀ helper evaluated where no branch fires.

    The verb set is a CHECKED VARIABLE, not a derivation performed once
    (:meth:`test_EVERY_public_TaskLedger_verb_is_ADJUDICATED`): 04a learned this the
    expensive way when a *"one fixture, no test edits"* spec turned out to have SIX call
    sites, and again when the sweep built to catch that MATCHED ITSELF (reader §Q4 A6).
    """

    @pytest.mark.parametrize("blocker_count", [0, 1, 3])
    async def test_the_mirror_holds_after_create_task(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], blocker_count: int
    ) -> None:
        """Counts 0 / 1 / many.  ZERO is not decoration: it is the input class where a
        build that unconditionally RELATEs would write an edge to nothing, and where a
        build that unconditionally opens a transaction pays for one it does not need.
        """
        ledger, _env, first_blocker = task_ledger
        blockers = [first_blocker]
        while len(blockers) < blocker_count:
            blockers.append(
                await ledger.create_task(f"blocker {len(blockers)}", DESCRIPTION, created_by=CREATOR)
            )
        blockers = blockers[:blocker_count]
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=blockers or None, created_by=CREATOR
        )
        await _assert_mirror(ledger, task_id, where=f"create_task blocked_by×{blocker_count}")
        assert await _edge_blockers_of(ledger, task_id) == set(blockers)

    async def test_the_mirror_holds_after_create_task_with_a_DUPLICATE_blocker(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The dedupe input class, forced.  ``_new_task_content`` collapses duplicates
        order-preservingly *"so a DUPLICATE id must not double-count against the claim
        gate's ``array::len`` CAS"* — and a mirror that RELATEs the RAW list writes the same
        edge twice, which on a UNIQUE-less edge table is two rows for one dependency.
        """
        ledger, _env, blocker_id = task_ledger
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker_id, blocker_id], created_by=CREATOR
        )
        await _assert_mirror(ledger, task_id, where="create_task with a duplicate blocker")
        rows = await _raw(
            ledger,
            f"SELECT count() FROM {BLOCKS_RELATION_NAME} WHERE out = $task GROUP ALL",
            {"task": RecordID(TASK_TABLE, task_id)},
        )
        count = int(rows[0]["count"]) if isinstance(rows, list) and rows else 0
        assert count == 1, f"a duplicate blocked_by id produced {count} edges, not 1"

    async def test_the_mirror_holds_after_create_many_including_a_FORWARD_reference(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """RED today.  ⛔ The pin that kills *RELATE-before-all-CREATEs*.

        Item 0 is blocked by item 1's PRE-MINTED id — a reference FORWARD in batch order,
        which is exactly what ``AppContext._create_many`` produces once it resolves temp
        keys (it pre-mints every id and rewrites ``blocked_by`` before calling down, scout
        §A2-FLAG 3).  Under ``ENFORCED`` the endpoint must EXIST at RELATE time, so a
        builder that emits ``CREATE_0, RELATE_0, CREATE_1, RELATE_1`` sees item 0's RELATE
        reject an endpoint the very next statement would have created, and the whole batch
        rolls back.

        ⚠ **UNMEASURED STORE BEHAVIOUR, stated rather than assumed** (reader §Q2.5): 04a
        measured that ``ENFORCED`` resolves an ``out`` endpoint created earlier in the SAME
        uncommitted transaction, and left the ``in`` side unmeasured.  Here BOTH endpoints
        are minted in one transaction.  If the engine cannot do it, that is a STOP and an
        escalation — not a licence to move the edges out of the transaction, which is W-D.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, _blocker = task_ledger
        first_id = f"cm_{uuid.uuid4().hex}"
        second_id = f"cm_{uuid.uuid4().hex}"
        specs = [
            TaskSpec(subject="waits on b", description=DESCRIPTION, blocked_by=[second_id]),
            TaskSpec(subject="blocks a", description=DESCRIPTION, blocked_by=[]),
        ]
        created = await ledger.create_many(specs, created_by=CREATOR, ids=[first_id, second_id])
        assert created == [first_id, second_id]
        await _assert_mirror(ledger, first_id, where="create_many forward reference")
        await _assert_mirror(ledger, second_id, where="create_many unblocked sibling")
        assert await _edge_blockers_of(ledger, first_id) == {second_id}
        assert await _edge_blockers_of(ledger, second_id) == set()

    async def test_the_SUPERSEDED_successor_is_born_UNBLOCKED_with_no_blocks_edges(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """GREEN-ISH today for the column, RED for the edge.  **OLD-BEHAVIOUR-PRESERVED,
        DELIBERATELY** — the removed-behaviour law's adjudication, written down as a pin
        rather than as a sentence in a report.

        MEASURED (scout §A2 W3): ``supersede_task`` calls ``_new_task_content(..., None,
        ...)``, so the successor is born with an EMPTY ``blocked_by`` and the predecessor's
        dependencies are dropped.  Whether that is right is spec-silent; it is CONSISTENT
        with today's row, so *"mirror exactly"* is the safe read — and the inventory records
        it as **old-behaviour-preserved deliberately, not accidentally**.

        The pin also holds the PREDECESSOR's own edges intact: a supersede must not garbage
        -collect the edges of the row it stamps.
        """
        ledger, _env, blocker_id = task_ledger
        original = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker_id], created_by=CREATOR
        )
        successor = await ledger.supersede_task(
            original, subject="Reframed", description=DESCRIPTION, created_by=CREATOR
        )
        assert await _column_blockers_of(ledger, successor) == []
        assert await _edge_blockers_of(ledger, successor) == set(), (
            "the successor inherited blocks EDGES its blocked_by column does not carry — "
            "the mirror must follow the column, and supersede_task deliberately drops the "
            "predecessor's dependencies (scout §A2-FLAG 2)"
        )
        await _assert_mirror(ledger, successor, where="supersede_task successor")
        await _assert_mirror(ledger, original, where="supersede_task predecessor")
        assert await _edge_blockers_of(ledger, original) == {blocker_id}

    async def test_transition_and_claim_NEVER_touch_the_mirror(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """RED today.  ∀ over a task's whole legal lifecycle, with each step FORCED.

        MEASURED (scout §A2): ``_transition_fragment`` builds ``set_parts`` from
        ``status``/``updated_at``/``provenance.events`` (+ owner/claimed_at on release, +
        summary/report_path on done) and ``blocked_by`` appears in NO branch.  The mirror
        must be equally untouched — a builder who "keeps the edge in sync" on transition
        would silently make ``blocked_by`` mutable and break the claim path's stated
        assumption that it never changes after creation.
        """
        ledger, _env, blocker_id = task_ledger
        second = await ledger.create_task("second blocker", DESCRIPTION, created_by=CREATOR)
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker_id, second], created_by=CREATOR
        )
        expected = {blocker_id, second}
        for blocker in (blocker_id, second):
            claim = await ledger.claim_task(blocker, ACTOR)
            assert claim.claimed
            await _assert_mirror(ledger, task_id, where=f"after claim_task({blocker})")
            await ledger.transition(blocker, STATUS_IN_PROGRESS, actor=ACTOR)
            await _assert_mirror(ledger, task_id, where=f"after transition({blocker}, in_progress)")
            await ledger.transition(
                blocker, STATUS_DONE, actor=ACTOR, summary="blocker finished"
            )
            await _assert_mirror(ledger, task_id, where=f"after transition({blocker}, done)")
        assert await _edge_blockers_of(ledger, task_id) == expected, (
            "resolving every blocker changed the blocks edge set. The edge records the "
            "DEPENDENCY, not the dependency's STATE — a resolved blocker keeps its edge, "
            "exactly as it keeps its blocked_by entry"
        )
        claim = await ledger.claim_task(task_id, ACTOR)
        assert claim.claimed, "the task became claimable once every blocker reached a terminal status"
        await _assert_mirror(ledger, task_id, where="after the newly-unblocked task was claimed")

    def test_EVERY_public_TaskLedger_verb_is_ADJUDICATED(self) -> None:
        """⛔ Coverage as a CHECKED VARIABLE, deny-by-default.

        An exact-set pin over ``TaskLedger``'s public async methods, DERIVED from the class
        by AST rather than from a hand list — so a SIXTH write verb added next packet
        cannot silently escape the mirror invariant.  Repo law's *allowlist the safe*: the
        forbidden set (ways to write ``blocked_by``) is unbounded; the verb set is small and
        enumerable.

        RED today for exactly one reason: :data:`NON_WRITING_VERBS` declares
        ``transitive_blockers``, which does not exist yet.  It goes green with the helper.
        """
        source = Path(inspect.getfile(TaskLedger)).read_text(encoding="utf-8")
        tree = ast.parse(source)
        class_node = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == "TaskLedger"
        )
        public_async = {
            node.name
            for node in class_node.body
            if isinstance(node, ast.AsyncFunctionDef) and not node.name.startswith("_")
        }
        declared = MIRRORING_VERBS | MIRROR_IMMUTABLE_VERBS | NON_WRITING_VERBS
        assert public_async == declared, (
            "TaskLedger's public async verb set drifted from this contract's adjudication. "
            f"On the class but NOT adjudicated: {sorted(public_async - declared)}. "
            f"Adjudicated but NOT on the class: {sorted(declared - public_async)}. Every "
            "verb belongs in exactly one of MIRRORING_VERBS (writes and must mirror), "
            "MIRROR_IMMUTABLE_VERBS (writes and must NOT touch blocked_by) or "
            "NON_WRITING_VERBS — and a new MIRRORING verb owes a pin in this class"
        )


# =========================================================================== #
# SECTION E — ACYCLICITY OVER PERSISTED IDS.
#
# MEASURED (scout §A4): the ONLY cycle check in the tree is
# ``AppContext._find_key_cycle``, a DFS over ``create_many``'s BATCH-LOCAL TEMP KEYS — its
# edge set is built with ``{ref for ref in item.blocked_by if ref in key_index}``, so a
# ``blocked_by`` entry naming a REAL, already-persisted id is EXCLUDED from the graph
# entirely.  ``create_task`` has no check of any kind.
# =========================================================================== #


async def _seed_chain(connection: SurrealConnection, length: int) -> list[str]:
    """RAW-seed an acyclic chain ``ids[0] <- ids[1] <- … <- ids[length-1]``.

    ``ids[i]`` is blocked by ``ids[i-1]``, so ``ids[-1]``'s transitive blocker set is every
    earlier id.  Returned deepest-blocker-first.  Raw for the same reason
    :func:`_seed_cycle` is: sections E and F must hold the DETECTOR to account over graphs
    that already exist, not only over graphs the guarded write path was willing to build.
    """
    ids = [f"chain{index}_{uuid.uuid4().hex}" for index in range(length)]
    for task_id in ids:
        await seed_endpoint(connection, TASK_TABLE, task_id)
    for index in range(1, length):
        await run(
            connection,
            f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
            {"id": ids[index], "blocked_by": [ids[index - 1]]},
        )
        await relate(
            connection,
            BLOCKS_RELATION_NAME,
            in_table=TASK_TABLE,
            in_id=ids[index - 1],
            out_table=TASK_TABLE,
            out_id=ids[index],
        )
    return ids


async def _seed_cycle(connection: SurrealConnection, length: int) -> list[str]:
    """RAW-seed a ``blocks`` cycle of ``length`` tasks, bypassing every ledger guard.

    Deliberately raw: once 04b-1 lands, the ledger REFUSES to create a cycle, so the only
    way to hold the detector to account is to put one in the store the way history can — a
    row written before this packet, or by a verb nobody has written yet.  A detector that
    can only be tested through the guard that prevents the condition is a detector nobody
    has tested.
    """
    ids = [f"cycle{index}_{uuid.uuid4().hex}" for index in range(length)]
    for task_id in ids:
        await seed_endpoint(connection, TASK_TABLE, task_id)
    for index, task_id in enumerate(ids):
        blocker = ids[(index - 1) % length]
        await run(
            connection,
            f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
            {"id": task_id, "blocked_by": [blocker]},
        )
        await relate(
            connection,
            BLOCKS_RELATION_NAME,
            in_table=TASK_TABLE,
            in_id=blocker,
            out_table=TASK_TABLE,
            out_id=task_id,
        )
    return ids


class TestACycleIsDetectedOverPERSISTEDIds:
    """RED today.  ⛔ **The pins that kill a BARE-IDIOM detector.**

    Probe §5.4, MEASURED on 3.2.1: the working acyclicity detector is *"the task appears in
    its own ``+collect`` reach"*.  The BARE form is **not** a detector — the probe's own
    ``@.{..8}`` leg "detected" a 4-cycle **by arithmetic accident**, because 8 mod 4 = 0
    landed back on the start node.  *A positive result for the wrong reason.*  With a
    **3-cycle** and depth 8 the same query returns a different node and reports ACYCLIC.

    So the fixtures here are a 3-cycle **and** a 4-cycle: no single depth is a multiple of
    both 3 and 4 unless it is a multiple of 12, and the packet requires a SMALL explicit
    bound.  A build that reports both correctly is not doing it by accident.

    ⚠ The 5-cycle leg exists for the same reason at a different modulus, and the ACYCLIC
    control is what stops all of this passing on a build that answers "cycle" to everything.
    """

    @pytest.mark.parametrize("length", [3, 4, 5])
    async def test_a_task_on_a_cycle_APPEARS_IN_ITS_OWN_transitive_blockers(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], length: int
    ) -> None:
        ledger, env, _blocker = task_ledger
        setup = await connect_admin(env)
        try:
            ids = await _seed_cycle(setup, length)
        finally:
            await setup.close()
        reach = await _transitive_blockers(ledger, ids[0])
        assert ids[0] in set(reach.ids), (
            f"a task on a {length}-cycle did not appear in its own transitive blocker "
            f"reach. The detector must be the +collect CLOSURE (probe §5.4); the bare "
            f"recursive idiom returns TERMINAL-DEPTH nodes and 'detects' a cycle only when "
            f"the bound happens to be a multiple of the cycle length. reach={reach.ids}"
        )
        assert set(reach.ids) >= set(ids), (
            f"the closure over a {length}-cycle is missing members: {sorted(set(ids) - set(reach.ids))}"
        )

    async def test_POSITIVE_CONTROL_a_task_on_NO_cycle_does_NOT_appear_in_its_own_reach(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The control that stops the three legs above passing on a build that says
        "cycle" unconditionally — and the ``+inclusive`` pin at the same time: the reach
        must NOT carry the root (probe §5.1 measured ``+inclusive`` as the operator that
        adds it, so a build that reaches for it makes every acyclic task look cyclic).
        """
        ledger, _env, blocker_id = task_ledger
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker_id], created_by=CREATOR
        )
        reach = await _transitive_blockers(ledger, task_id)
        assert task_id not in set(reach.ids), (
            "an ACYCLIC task appeared in its own transitive blocker reach — the traversal "
            "must not be +inclusive, or every task would read as cyclic"
        )
        assert set(reach.ids) == {blocker_id}


class TestCreateRefusesToFormACycle:
    """RED today.  The guard over PERSISTED ids that today's key-local DFS cannot give.

    Two reachable holes, both MEASURED-by-reading (scout §A4), both invisible to
    ``_find_key_cycle`` because it filters its edge set to ``ref in key_index``:

    1. a ``create_many`` batch whose items reference each other's **pre-minted IDS**
       (``AppContext._create_many`` pre-mints every id, so a caller-supplied batch can name
       them directly);
    2. a SELF-loop — ``ids=[X]`` with ``blocked_by=[X]`` — which is a 1-cycle and which
       ``ENFORCED`` alone cannot stop, because by RELATE time X genuinely exists.

    ⚠ Neither is closed by ``ENFORCED`` and neither is closed by the existing DFS.  A task
    on a cycle can NEVER be claimed (the claim CAS requires every blocker terminal, and a
    cyclic blocker can never reach one), so this is the same silent black hole R3 describes
    for phantom blockers — a row that exists and is unclaimable forever.
    """

    async def test_a_batch_whose_items_reference_each_others_IDS_is_REFUSED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        from loremaster.tasks import TaskSpec

        ledger, _env, _blocker = task_ledger
        before = await _task_row_count(ledger)
        first_id = f"cyc_{uuid.uuid4().hex}"
        second_id = f"cyc_{uuid.uuid4().hex}"
        specs = [
            TaskSpec(subject="a waits on b", description=DESCRIPTION, blocked_by=[second_id]),
            TaskSpec(subject="b waits on a", description=DESCRIPTION, blocked_by=[first_id]),
        ]
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_many(specs, created_by=CREATOR, ids=[first_id, second_id])
        message = str(caught.value)
        assert first_id in message and second_id in message, (
            "the cycle refusal must NAME every id on the cycle — a caller cannot break a "
            f"cycle it cannot see: {message!r}"
        )
        assert await _task_row_count(ledger) == before, (
            "a refused cyclic batch left task rows behind; the check must run BEFORE the write"
        )

    async def test_a_SELF_blocking_task_is_REFUSED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The 1-cycle.  ⚠ ``ENFORCED`` cannot catch this one, and that is the point: by
        RELATE time the row exists, so the engine is satisfied and the task is silently
        unclaimable forever.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, _blocker = task_ledger
        before = await _task_row_count(ledger)
        self_id = f"self_{uuid.uuid4().hex}"
        specs = [
            TaskSpec(subject="blocks itself", description=DESCRIPTION, blocked_by=[self_id])
        ]
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_many(specs, created_by=CREATOR, ids=[self_id])
        assert self_id in str(caught.value)
        assert await _task_row_count(ledger) == before

    async def test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """RED today.  The reach half of the guard — the half a batch-local DFS structurally
        cannot have, and the reason the packet says *"over PERSISTED ids"*.

        A caller-supplied id is reused across TWO calls: ``X`` is created first (unblocked),
        then a batch creates ``Y`` blocked by ``X`` **and** re-declares ``X``'s dependency
        on ``Y``… which it cannot do, so the reachable shape is the one seeded below — an
        existing chain that the new task closes into a loop.
        """
        from loremaster.tasks import TaskSpec

        ledger, env, _blocker = task_ledger
        setup = await connect_admin(env)
        try:
            chain = await _seed_chain(setup, 3)
        finally:
            await setup.close()
        before = await _task_row_count(ledger)
        new_id = f"closer_{uuid.uuid4().hex}"
        # ``chain[0]`` is the deepest blocker; making it depend on the new task while the
        # new task depends on ``chain[-1]`` closes the loop THROUGH persisted rows.
        setup = await connect_admin(env)
        try:
            await run(
                setup,
                f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
                {"id": chain[0], "blocked_by": [new_id]},
            )
        finally:
            await setup.close()
        specs = [
            TaskSpec(subject="closes the loop", description=DESCRIPTION, blocked_by=[chain[-1]])
        ]
        with pytest.raises(TaskLedgerError):
            await ledger.create_many(specs, created_by=CREATOR, ids=[new_id])
        assert await _task_row_count(ledger) == before

    async def test_POSITIVE_CONTROL_a_legal_CHAIN_in_one_batch_LANDS(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The control the three refusals need: a build that refuses EVERY batch with any
        intra-batch dependency would satisfy all of them.

        FOUR deep, not two — a 2-item chain cannot distinguish a real DAG walk from a
        one-hop check, which is the same small-N trap the transitive read carries.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, _blocker = task_ledger
        ids = [f"chain{index}_{uuid.uuid4().hex}" for index in range(4)]
        specs = [
            TaskSpec(
                                subject=f"step {index}",
                description=DESCRIPTION,
                blocked_by=[ids[index - 1]] if index else [],
            )
            for index in range(4)
        ]
        created = await ledger.create_many(specs, created_by=CREATOR, ids=ids)
        assert created == ids
        for index, task_id in enumerate(ids):
            await _assert_mirror(ledger, task_id, where=f"legal chain step {index}")
        assert await _edge_blockers_of(ledger, ids[3]) == {ids[2]}


# =========================================================================== #
# SECTION F — THE TRANSITIVE BLOCKER READ.
#
# ⚠ FIXTURE FLOOR, NON-NEGOTIABLE (packet §04b-1, probe §5.1): **≥3 deep AND branching.**
# A 2-node chain cannot discriminate the ``+collect`` CLOSURE from the TERMINAL-DEPTH read
# the old packet text prescribed — on a 2-node chain the two are the same answer, and a
# build written to the wrong idiom passes on a green suite.
# =========================================================================== #


@pytest_asyncio.fixture()
async def branching_dag(
    task_ledger: tuple[TaskLedger, SurrealEnv, str],
) -> AsyncIterator[tuple[TaskLedger, dict[str, str]]]:
    """A DAG that is **4 deep, branching, AND a diamond**, plus two controls.

    ::

        root                       (depth 3 from leaf; blocks nothing above it)
         ├── left  ──┐
         └── right ──┴── middle ── leaf
        isolated                   (no edges at all)

    ``leaf``'s TRANSITIVE blockers are {middle, left, right, root} — four nodes.
    ``leaf``'s TERMINAL-DEPTH blockers (the bare idiom, at depth 3) are {root} alone.
    **That is the discrimination**, and it needs both the depth AND the branch: on a
    straight chain the closure and the terminal read differ only in size, while the diamond
    also proves the closure DEDUPLICATES (``root`` is reachable by two paths and must
    appear once — probe §5.1: *"deduplicated, ordered by proximity"*).
    """
    ledger, env, _blocker = task_ledger
    names = ["root", "left", "right", "middle", "leaf", "isolated"]
    ids = {name: f"{name}_{uuid.uuid4().hex}" for name in names}
    edges = {
        "left": ["root"],
        "right": ["root"],
        "middle": ["left", "right"],
        "leaf": ["middle"],
    }
    setup = await connect_admin(env)
    try:
        for task_id in ids.values():
            await seed_endpoint(setup, TASK_TABLE, task_id)
        for child, parents in edges.items():
            await run(
                setup,
                f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
                {"id": ids[child], "blocked_by": [ids[parent] for parent in parents]},
            )
            for parent in parents:
                await relate(
                    setup,
                    BLOCKS_RELATION_NAME,
                    in_table=TASK_TABLE,
                    in_id=ids[parent],
                    out_table=TASK_TABLE,
                    out_id=ids[child],
                )
    finally:
        await setup.close()
    yield ledger, ids


class TestTheTransitiveBlockerRead:
    """RED today — no transitive or critical-path read exists anywhere in the tree (scout
    §A3, MEASURED: grep for ``@.{``, ``+collect``, ``->blocks``, ``critical`` over
    ``loremaster/loremaster/**.py`` returned ZERO hits; every blocked computation today is
    exactly ONE hop deep and is done CLIENT-SIDE in Python off an UNBOUNDED
    ``SELECT * FROM task``).

    ⛔ **The pins that kill the idiom the packet itself used to prescribe.**  The old
    Scope-IN sentence said ``@.{1..n}->blocks->task, always TIMEOUT``; probe §5 measured
    BOTH halves false.  A builder implementing that sentence returns *only the deepest
    blocker* on a green suite — and would have shipped, because no fixture in this repo was
    ever more than 2 deep.
    """

    async def test_the_read_returns_the_CLOSURE_not_the_TERMINAL_depth(
        self, branching_dag: tuple[TaskLedger, dict[str, str]]
    ) -> None:
        ledger, ids = branching_dag
        result = await _transitive_blockers(ledger, ids["leaf"])
        assert set(result.ids) == {ids["middle"], ids["left"], ids["right"], ids["root"]}, (
            "the transitive read returned the wrong set. The bare recursive idiom "
            "(@.{1..n}->blocks->task) returns TERMINAL-DEPTH nodes only — on this fixture "
            f"that is {{root}} alone. The closure operator is +collect (probe §5.1). "
            f"got={sorted(result.ids)}"
        )

    async def test_the_closure_DEDUPLICATES_a_diamond(
        self, branching_dag: tuple[TaskLedger, dict[str, str]]
    ) -> None:
        """``root`` is reachable from ``leaf`` by two distinct paths (via ``left`` and via
        ``right``) and must appear ONCE.  The bare form does not dedupe at all (probe §5.4,
        citing the engine's own ``cycles_bounded.surql`` spec, whose bare result carries
        repeats).
        """
        ledger, ids = branching_dag
        result = await _transitive_blockers(ledger, ids["leaf"])
        assert len(result.ids) == len(set(result.ids)), f"duplicates in the closure: {result.ids}"
        assert result.ids.count(ids["root"]) == 1

    async def test_a_task_with_NO_blockers_yields_an_EMPTY_set(
        self, branching_dag: tuple[TaskLedger, dict[str, str]]
    ) -> None:
        """Control (probe §5.1's own): the instrument must be able to say NOTHING."""
        ledger, ids = branching_dag
        result = await _transitive_blockers(ledger, ids["root"])
        assert result.ids == []
        assert result.truncated is False

    async def test_an_ISOLATED_task_yields_an_EMPTY_set(
        self, branching_dag: tuple[TaskLedger, dict[str, str]]
    ) -> None:
        """The second control.  ``root`` has no blockers but IS an endpoint of two edges;
        ``isolated`` touches the edge table not at all.  A build that read the edge table
        rather than traversing FROM the task could pass the leaf control and fail here.
        """
        ledger, ids = branching_dag
        result = await _transitive_blockers(ledger, ids["isolated"])
        assert result.ids == []
        assert result.truncated is False

    async def test_an_UNKNOWN_task_id_raises_TaskNotFoundError(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """An id naming no task must RAISE, never return an empty reach.  ``[]`` for an
        absent task and ``[]`` for an unblocked one are the same answer to two different
        questions — the silent-degradation shape store reference §2 names.
        """
        ledger, _env, _blocker = task_ledger
        with pytest.raises(TaskNotFoundError):
            await _transitive_blockers(ledger, PHANTOM_TASK_ID_KEY_SHAPE)


class TestTheReadIsHONESTAtItsBound:
    """RED today.  ⛔ **The trust-doctrine pin.**

    Probe §5.3, MEASURED on 3.2.1: ``{..256+collect}`` over a 299-deep chain returns **256
    nodes with NO error and NO signal**.  A served "critical path" over a graph deeper than
    the bound would be *wrong and confident* — and the bound is FIXED by the engine, not
    configurable.  Under the trust doctrine a served surface may be partial, but it may
    never claim to be whole: *a served count describes the whole set its label claims;
    failures are LOUD, never silent.*

    The DISCRIMINATING PAIR is the whole instrument: one fixture inside the bound and one
    past it.  A build hard-coding ``truncated = False`` dies on the second; a build
    hard-coding ``True`` dies on the first.  A single fixture proves neither.

    Escalation E-3 records the rejected alternative (RAISE at the bound) and why.
    """

    async def test_a_chain_DEEPER_than_max_depth_reports_TRUNCATED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        ledger, env, _blocker = task_ledger
        setup = await connect_admin(env)
        try:
            chain = await _seed_chain(setup, 5)
        finally:
            await setup.close()
        result = await _transitive_blockers(ledger, chain[-1], max_depth=2)
        assert result.truncated is True, (
            "a 5-deep chain read at max_depth=2 reported truncated=False. The engine "
            "TRUNCATES SILENTLY at the bound (probe §5.3) — a reader that passes that "
            "silence on serves a short answer as a complete one, which is the trust "
            "doctrine's core failure"
        )
        assert set(result.ids) == {chain[-2], chain[-3]}, (
            f"a bounded read must still return exactly the nodes WITHIN the bound: "
            f"got {sorted(result.ids)}"
        )

    async def test_a_chain_WITHIN_max_depth_reports_truncated_FALSE(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The other half of the pair, at the SAME depth against a SHORTER chain — so the
        only variable between the two legs is the data, never the call.
        """
        ledger, env, _blocker = task_ledger
        setup = await connect_admin(env)
        try:
            chain = await _seed_chain(setup, 3)
        finally:
            await setup.close()
        result = await _transitive_blockers(ledger, chain[-1], max_depth=2)
        assert result.truncated is False
        assert set(result.ids) == {chain[0], chain[1]}

    def test_the_default_bound_is_a_SMALL_EXPLICIT_constant_inside_the_engine_ceiling(
        self,
    ) -> None:
        """The bound is a named module constant, not a literal at the call site, and it sits
        well inside the engine's hard ceiling.

        ``{..257}`` raises *"Found 257 for bound but expected 256 at most"* and an OPEN
        bound past 256 raises *"Exceeded the idiom recursion limit"* (probe §5.3) — so a
        default at or above the ceiling turns a truncation into a boot-visible crash on the
        first deep graph.
        """
        import loremaster.tasks

        default = getattr(loremaster.tasks, MAX_DEPTH_CONSTANT, None)
        assert isinstance(default, int), (
            f"loremaster.tasks must export {MAX_DEPTH_CONSTANT} — the transitive read's "
            f"default depth bound, as a constant rather than a literal, so the packet's "
            f"'explicit small bound' is greppable and changeable in ONE place"
        )
        assert 1 < default < ENGINE_RECURSION_CEILING, (
            f"{MAX_DEPTH_CONSTANT}={default} must be >1 (a 1-hop 'transitive' read is the "
            f"one-hop check that already exists) and strictly below the engine's "
            f"{ENGINE_RECURSION_CEILING} ceiling"
        )

    async def test_the_traversal_statement_carries_collect_AND_a_SELECT_level_TIMEOUT(
        self, branching_dag: tuple[TaskLedger, dict[str, str]]
    ) -> None:
        """A TEXT pin, and its BOUND is stated rather than hidden.

        WHAT IT CHECKS: the statement the helper actually sends contains ``+collect`` and a
        ``TIMEOUT`` clause.  WHAT IT DOES NOT CHECK: that the timeout ever FIRES — no
        assertion here observes a timed-out query, and none pretends to.

        It is here because ``TIMEOUT`` is a ``SELECT`` clause and a PARSE ERROR on a bare
        idiom (probe §5.2: ``Unexpected token 'TIMEOUT'``), so *"always TIMEOUT"* is
        satisfiable ONLY through the ``SELECT id, @.{…+collect}(…) … FROM … TIMEOUT`` form.
        Which brake fires — depth or wall-clock — is a property of the DATA, not the query
        (probe §5.5), so the design must carry BOTH plus an explicit small bound.
        """
        ledger, ids = branching_dag
        seen: list[str] = []
        original = ledger._query  # noqa: SLF001 - capturing the seam is the point

        async def _capture(statement: str, params: dict[str, Any] | None = None) -> Any:
            seen.append(statement)
            return await original(statement, params)

        ledger._query = _capture  # type: ignore[method-assign]  # noqa: SLF001
        try:
            await _transitive_blockers(ledger, ids["leaf"])
        finally:
            ledger._query = original  # type: ignore[method-assign]  # noqa: SLF001
        traversals = [statement for statement in seen if "@." in statement]
        assert traversals, (
            f"the transitive read issued no recursive-path statement at all: {seen}"
        )
        for statement in traversals:
            assert "+collect" in statement, (
                f"the traversal must use the +collect CLOSURE operator; the bare form "
                f"returns terminal-depth nodes only (probe §5.1): {statement!r}"
            )
            assert "TIMEOUT" in statement, (
                f"the traversal must carry a SELECT-level TIMEOUT — the bare idiom cannot "
                f"carry one at all (probe §5.2), so its absence usually means the bare "
                f"form is in use: {statement!r}"
            )


# =========================================================================== #
# SECTION G — THE BLOCKER-EXISTENCE PRE-CHECK.  ONE IMPLEMENTATION (lead ruling L3).
#
# Operator ruling R3: this CHANGES a live verb.  A create naming a phantom blocker is
# REFUSED where today it silently produces a task that is unclaimable forever (scout
# §A2-FLAG 4: ``blocked_by`` is FAIL-OPEN at write, fail-closed at read).  The 2026-07-26
# "no comms consumers, change whatever" ruling does NOT cover this — ``lore_tasks`` is in
# active fleet use — and the change is deliberate: a loud refusal replaces a silent black
# hole.
#
# ⚠ AND THE APP CHECK IS REQUIRED, NOT GARNISH.  ``ENFORCED`` reports ONE bad endpoint, as
# untyped prose, only AFTER the write is attempted — and the seam's error hygiene (#31)
# withholds even that, serving ``statement N of M was rejected (unspecified rejection);
# see the server log``.  The app layer is the ONLY layer that can TEACH.
# =========================================================================== #


class TestAPhantomBlockerIsRefusedAndNamed:
    """RED today.  ⛔ **The pins that kill W-B** — *the policy keyed on the one fixture
    literal.*

    MEASURED (adversary §P1 W-B): a build that never queried the store and refused iff the
    id equalled the ONE literal every negative leg used passed 04a's whole contract 38/38;
    ``test_brief_ledger.py`` caught nothing, and only a neighbouring suite's independent
    ghost killed it — *"an accident of a neighbouring suite, not a property of this
    contract."*

    So every negative leg here is parametrised over FOUR differently-constructed phantom
    ids (see :data:`PHANTOM_TASK_IDS` for what each shape is for), and the multi-phantom
    leg forces the *"names EVERY one"* property that ``ENFORCED`` structurally cannot have.
    """

    @pytest.mark.parametrize("phantom", PHANTOM_TASK_IDS)
    async def test_a_create_naming_a_PHANTOM_blocker_is_REFUSED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], phantom: str
    ) -> None:
        ledger, _env, _blocker = task_ledger
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_task(SUBJECT, DESCRIPTION, blocked_by=[phantom], created_by=CREATOR)
        assert phantom in str(caught.value), (
            f"the refusal must NAME the bad id: {str(caught.value)!r}"
        )

    @pytest.mark.parametrize("phantom", PHANTOM_TASK_IDS)
    async def test_a_refused_create_writes_NO_task_row(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], phantom: str
    ) -> None:
        """BEFORE the write, not rolled back after it.  Row EXISTENCE is the discriminator
        (the MP-3 shape): a build that creates the row and compensates leaves evidence.
        """
        ledger, _env, _blocker = task_ledger
        before = await _task_row_count(ledger)
        with pytest.raises(TaskLedgerError):
            await ledger.create_task(SUBJECT, DESCRIPTION, blocked_by=[phantom], created_by=CREATOR)
        assert await _task_row_count(ledger) == before

    async def test_the_refusal_NAMES_EVERY_phantom_not_just_the_FIRST(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ THE PIN THAT DISTINGUISHES THE APP CHECK FROM ``ENFORCED``.

        THREE phantoms and one REAL blocker, handed in an order that is NOT the served
        order.  ``ENFORCED`` can only ever report ONE bad endpoint per attempt (store
        reference §4), so a build that leans on the engine — or that returns on the first
        miss — names one id and reddens here.  The real blocker in the list is what stops a
        build passing by refusing the whole list unexamined.
        """
        ledger, _env, real_blocker = task_ledger
        supplied = [
            PHANTOM_TASK_ID_KEY_SHAPE,
            real_blocker,
            PHANTOM_TASK_ID_NATIVE_SHAPE,
            PHANTOM_TASK_ID_UUID_SHAPE,
        ]
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_task(SUBJECT, DESCRIPTION, blocked_by=supplied, created_by=CREATOR)
        message = str(caught.value)
        for phantom in (
            PHANTOM_TASK_ID_KEY_SHAPE,
            PHANTOM_TASK_ID_NATIVE_SHAPE,
            PHANTOM_TASK_ID_UUID_SHAPE,
        ):
            assert phantom in message, f"the refusal did not name {phantom!r}: {message!r}"
        assert real_blocker not in message, (
            f"the refusal named a blocker that DOES exist ({real_blocker!r}) — it must name "
            f"the unresolved ids and only those: {message!r}"
        )

    async def test_the_SERVED_refusal_text_is_EXACTLY_the_task_sentence(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The served surface pinned BY VALUE, sorted, joined — never a substring check.

        F3 (04a cold audit) measured what substring pins cost: the shared refusal could be
        edited to anything containing the id with the full suite green, and the sentence had
        already been cloned into both test doubles and had already DIVERGED in both.  Under
        the TRUST DOCTRINE the served surface IS the contract, because the reader is an
        agent learning what to do next from it.

        TWO phantoms handed in NON-sorted order: a build that stopped sorting, or that joined
        with anything but ``", "``, reddens here and nowhere else.  ESCALATION E-2 records
        why the identities render as BARE ids here and as ``name (id)`` on the agent side.
        """
        ledger, _env, _blocker = task_ledger
        first, second = sorted((PHANTOM_TASK_ID_KEY_SHAPE, PHANTOM_TASK_ID_NUMERIC_SHAPE))
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_task(
                SUBJECT,
                DESCRIPTION,
                blocked_by=[second, first],
                created_by=CREATOR,
            )
        assert str(caught.value) == _served_task_refusal(first, second), (
            "the SERVED refusal text changed. It is not a message, it is the contract an "
            "agent learns from — if you meant to change it, change _served_task_refusal in "
            "the same commit and say so; if you did not, production has drifted"
        )

    async def test_POSITIVE_CONTROL_all_REAL_blockers_are_ACCEPTED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """Without this, every pin above passes on a build that refuses everything."""
        ledger, _env, first_blocker = task_ledger
        second_blocker = await ledger.create_task("second", DESCRIPTION, created_by=CREATOR)
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[first_blocker, second_blocker], created_by=CREATOR
        )
        await _assert_mirror(ledger, task_id, where="positive control, two real blockers")

    @pytest.mark.parametrize("empty", [None, []])
    async def test_an_EMPTY_dependency_list_is_ACCEPTED_and_writes_NO_edge(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], empty: list[str] | None
    ) -> None:
        """The third and fourth input classes, each forced.  THE QUANTIFIER LAW: every
        input class gets its stated fate, not just the one that prompted the work.

        ⚠ 04a's adversary (§P3) found the shared policy's empty-input early-return
        UNREACHABLE through both of its entry points — *"a builder will write it; no pin
        reaches it"*.  A ``blocked_by=None`` create reaches it, so this pin closes that
        dead branch as a side effect, and both spellings are pinned because ``None`` and
        ``[]`` travel different lines of ``_new_task_content``.
        """
        ledger, _env, _blocker = task_ledger
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=empty, created_by=CREATOR
        )
        assert await _column_blockers_of(ledger, task_id) == []
        assert await _edge_blockers_of(ledger, task_id) == set()

    @pytest.mark.parametrize("phantom", PHANTOM_TASK_IDS)
    async def test_create_many_ALSO_refuses_a_phantom_and_writes_NO_rows(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], phantom: str
    ) -> None:
        """Pinned separately from ``create_task``, on the scout's explicit warning that the
        two verbs have different transaction shapes and a fix may reach only one.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, real_blocker = task_ledger
        before = await _task_row_count(ledger)
        specs = [
            TaskSpec(subject="fine", description=DESCRIPTION, blocked_by=[real_blocker]),
            TaskSpec(subject="bad", description=DESCRIPTION, blocked_by=[phantom]),
        ]
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_many(specs, created_by=CREATOR)
        assert phantom in str(caught.value)
        assert await _task_row_count(ledger) == before


@pytest_asyncio.fixture()
async def agent_and_task_ledgers() -> AsyncIterator[tuple[Any, TaskLedger, str, str, SurrealEnv]]:
    """A BriefLedger and a TaskLedger on ONE database, each with one real endpoint.

    Both families in one fixture on purpose: section G's sharing proofs must observe the
    AGENT refusal and the TASK refusal reacting to the SAME mutation, in the same run.  A
    proof split across two databases could not tell "the shared thing changed" from "two
    things changed".

    Yields ``(brief_ledger, task_ledger, registered_agent_id, real_task_id, env)``.
    """
    from loremaster.briefs import BriefLedger

    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    registered_agent_id = f"registered_agent_{uuid.uuid4().hex}"
    setup = await connect_admin(env)
    try:
        await apply_ddl(setup, generate_agent_ddl(), url=env.url)
        await seed_endpoint(setup, AGENT_TABLE, registered_agent_id)
    finally:
        await setup.close()

    brief_ledger = BriefLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    task_ledger_instance = TaskLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await brief_ledger.ensure_ready()
    await task_ledger_instance.ensure_ready()
    real_task_id = await task_ledger_instance.create_task(
        "A real blocker", DESCRIPTION, created_by=CREATOR
    )
    try:
        yield brief_ledger, task_ledger_instance, registered_agent_id, real_task_id, env
    finally:
        await brief_ledger.close()
        await task_ledger_instance.close()
        await drop_database(env)


class TestTheRowExistencePolicyHasONEImplementation:
    """RED today.  ⛔ **The pins that kill W-E** — *routing is not sharing* — **on BOTH
    sides of the generalisation.**

    Lead ruling **L3**: the blocker-existence check is a GENERALISATION of packet 04a's
    agent policy, parameterised by table and label, with the agent entry point kept as a
    thin typed adapter so 04a's callers and pins are untouched.  A ``reject_unknown_tasks``
    sibling would be **copy #2 of a policy** — #102's shape, whose receipts are a
    deterministic-jitter bug cloned into a sibling module in a *different* wrong way.

    MEASURED why inspection is not enough (adversary §P1 W-E): a build where the shared
    function existed, both ledgers imported and CALLED it, and it decided NOTHING while each
    ledger kept a private copy underneath passed 04a's contract **38/38 and every
    neighbouring suite**.  *"Nothing anywhere catches it."*

    So the three legs below are all SEMANTIC MUTATIONS, and they cover both directions of
    the generalisation:

    * neutralise the shared policy inside ``loremaster.tasks`` -> the TASK verb must stop
      deciding and the phantom must reach the ENGINE;
    * neutralise it inside the SHARED MODULE -> the AGENT verb must ALSO stop deciding,
      which is what proves ``reject_unknown_agents`` is a delegating ADAPTER rather than a
      retained second implementation;
    * replace the shared FORMATTER -> BOTH families' served text must change, which is L3's
      own demanded proof stated as a runnable pin rather than a shell block.
    """

    async def test_MUTATION_neutralising_the_shared_policy_lets_a_CREATE_reach_the_ENGINE(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """A private copy underneath still refuses -> not a ``SurrealStoreError`` -> RED.
        Nothing refuses at either layer -> no raise at all -> RED (that is W-A's shape too:
        a guard that never LANDED).
        """
        ledger, _env, _blocker = task_ledger
        _neutralise_the_policy(monkeypatch, "loremaster.tasks")
        with pytest.raises(SurrealStoreError):
            await ledger.create_task(
                SUBJECT,
                DESCRIPTION,
                blocked_by=[PHANTOM_TASK_ID_NATIVE_SHAPE],
                created_by=CREATOR,
            )

    async def test_MUTATION_neutralising_the_SHARED_policy_lets_a_PUBLISH_reach_the_ENGINE(
        self,
        monkeypatch: pytest.MonkeyPatch,
        agent_and_task_ledgers: tuple[Any, TaskLedger, str, str, SurrealEnv],
    ) -> None:
        """⛔ The pin that proves the GENERALISATION actually landed.

        The mutation point is the SHARED module's generalised policy, not the agent
        adapter.  If ``reject_unknown_agents`` still owns its own probe — the *"generalise
        it, and also keep the old body"* build, which is copy #2 wearing a compatibility
        shim — publish keeps refusing and this stays RED.  Only an adapter that DELEGATES
        lets the ghost reach the engine's ``ENFORCED``.
        """
        brief_ledger, _tasks, _registered, _task_id, _env = agent_and_task_ledgers
        monkeypatch.setattr(
            _shared_policy(), SHARED_POLICY_ATTR, _accept_everything, raising=True
        )
        with pytest.raises(SurrealStoreError):
            await brief_ledger.publish(
                "project",
                "the standing law",
                created_by="lead",
                agent_id="unregistered_agent_0000000000000000",
            )

    async def test_POSITIVE_CONTROL_the_neutralised_SHARED_policy_still_lets_a_REGISTERED_publish_through(
        self,
        monkeypatch: pytest.MonkeyPatch,
        agent_and_task_ledgers: tuple[Any, TaskLedger, str, str, SurrealEnv],
    ) -> None:
        """The control for the leg above, load-bearing twice: a build that raised for EVERY
        publish would satisfy it, and so would a run where the substitution did not take.
        """
        brief_ledger, _tasks, registered, _task_id, _env = agent_and_task_ledgers
        monkeypatch.setattr(
            _shared_policy(), SHARED_POLICY_ATTR, _accept_everything, raising=True
        )
        result = await brief_ledger.publish(
            "project", "the standing law", created_by="lead", agent_id=registered
        )
        assert result.brief.version == 1

    async def test_MUTATION_replacing_the_shared_FORMATTER_changes_BOTH_refusals(
        self,
        monkeypatch: pytest.MonkeyPatch,
        agent_and_task_ledgers: tuple[Any, TaskLedger, str, str, SurrealEnv],
    ) -> None:
        """⛔ **L3's demanded proof, as a runnable pin**: *"change the shared refusal text
        and BOTH the agent pins and the new task pins must go RED."*

        A ONE-DIRECTION substitution observed from TWO call sites in ONE run.  A family
        whose refusal text does not change is serving a private copy wearing the shared
        name — which is exactly what F3 (04a cold audit) found had ALREADY happened twice
        with the agent sentence, invisibly, because every pin over it was a substring check.

        The sentinel is deliberately unlike either real sentence, so a build that merely
        CONCATENATES the shared text with its own cannot pass by accident.
        """
        brief_ledger, tasks, _registered, _task_id, _env = agent_and_task_ledgers
        sentinel = "SENTINEL-SHARED-REFUSAL-04b1"
        monkeypatch.setattr(
            _shared_policy(),
            SHARED_FORMATTER_ATTR,
            lambda *_args, **_kwargs: sentinel,
            raising=True,
        )
        with pytest.raises(Exception) as agent_side:  # noqa: B017 - the TYPE has its own pin
            await brief_ledger.publish(
                "project",
                "the standing law",
                created_by="lead",
                agent_id="unregistered_agent_0000000000000000",
            )
        assert str(agent_side.value) == sentinel, (
            "the AGENT refusal did not route through the shared formatter — packet 04a's "
            "format_unknown_agent_refusal must become a thin adapter over the generalised "
            f"one, not keep its own sentence: {str(agent_side.value)!r}"
        )
        with pytest.raises(Exception) as task_side:  # noqa: B017 - see above
            await tasks.create_task(
                SUBJECT,
                DESCRIPTION,
                blocked_by=[PHANTOM_TASK_ID_UUID_SHAPE],
                created_by=CREATOR,
            )
        assert str(task_side.value) == sentinel, (
            "the TASK refusal did not route through the shared formatter — a second "
            f"sentence is copy #2 of the served surface: {str(task_side.value)!r}"
        )

    async def test_the_two_families_errors_share_a_base_from_the_SHARED_module(
        self,
        agent_and_task_ledgers: tuple[Any, TaskLedger, str, str, SurrealEnv],
    ) -> None:
        """DERIVED FROM THE RAISED VALUES, never from a name-keyed handle — 04a's own
        instrument (``test_BOTH_verbs_raise_an_error_a_caller_can_catch_with_ONE_except``),
        whose rationale is that *"the base is derived from the raised VALUES"*.

        A caller who wants *"this id names no row"* across BOTH families must be able to
        write ONE ``except``; and the base must belong to the SHARED module, because a base
        owned by either ledger is exactly the coupling that module exists to prevent.
        """
        brief_ledger, tasks, _registered, _task_id, _env = agent_and_task_ledgers
        with pytest.raises(Exception) as agent_side:  # noqa: B017
            await brief_ledger.publish(
                "project",
                "the standing law",
                created_by="lead",
                agent_id="unregistered_agent_0000000000000000",
            )
        with pytest.raises(Exception) as task_side:  # noqa: B017
            await tasks.create_task(
                SUBJECT, DESCRIPTION, blocked_by=[PHANTOM_TASK_ID_NUMERIC_SHAPE], created_by=CREATOR
            )
        shared = [
            base
            for base in type(agent_side.value).__mro__
            if base in type(task_side.value).__mro__
            and getattr(base, "__module__", None) == SHARED_POLICY_MODULE
        ]
        assert shared, (
            "the agent refusal and the task refusal share no base class defined in "
            f"{SHARED_POLICY_MODULE}. agent mro="
            f"{[b.__name__ for b in type(agent_side.value).__mro__]} task mro="
            f"{[b.__name__ for b in type(task_side.value).__mro__]}"
        )
        assert isinstance(task_side.value, TaskLedgerError), (
            "the task-side error must ALSO be a TaskLedgerError so a task caller keeps ONE "
            "except for this ledger's whole vocabulary — the shared base is an ADDITIONAL "
            "base, never a replacement (04a's UnknownRecipientError shape)"
        )

    async def test_the_CYCLE_error_is_NOT_an_existence_error(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **W-F's shape** — *a subclass where identity was pinned.*

        A cycle and a phantom blocker are DIFFERENT problems needing DIFFERENT next moves
        (break the loop vs create the missing task), so a caller must be able to tell them
        apart.  Both are ``TaskLedgerError``; only one is a row-existence failure.
        DERIVED from the raised values.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, _blocker = task_ledger
        with pytest.raises(TaskLedgerError) as existence:
            await ledger.create_task(
                SUBJECT, DESCRIPTION, blocked_by=[PHANTOM_TASK_ID_NATIVE_SHAPE], created_by=CREATOR
            )
        self_id = f"self_{uuid.uuid4().hex}"
        with pytest.raises(TaskLedgerError) as cycle:
            await ledger.create_many(
                [TaskSpec(subject="loop", description=DESCRIPTION, blocked_by=[self_id])],
                created_by=CREATOR,
                ids=[self_id],
            )
        assert type(cycle.value) is not type(existence.value), (
            "the cycle refusal and the unknown-blocker refusal raise the SAME class, so a "
            "caller cannot tell 'break the loop' from 'create the missing task'"
        )
        existence_bases = {
            base
            for base in type(existence.value).__mro__
            if getattr(base, "__module__", None) == SHARED_POLICY_MODULE
        }
        assert not existence_bases & set(type(cycle.value).__mro__), (
            "the cycle error inherits the shared ROW-EXISTENCE base. A cycle is not an "
            "existence failure: every id on it exists, which is precisely why ENFORCED "
            "cannot catch it"
        )


# =========================================================================== #
# SECTION H — #247, THE MESSAGE SENDER DOOR.  Operator ruling R2: CLOSED HERE.
#
# MEASURED, and escalated THREE times without a ruling before R2 (adversary §RESIDUALS R8
# with a door-build receipt — on the CORRECT 04a build,
# ``send(sender=<unregistered>, recipients=[registered])`` **SUCCEEDS**; builder §7 E-2;
# cold audit R-8).
#
# Why ``to``'s ``ENFORCED`` cannot reach it (scout §E3): ``message.sender`` is a FIELD on
# the ``message`` row — ``("sender", "record<agent>", "")``, a record LINK with an EMPTY
# constraint clause — not an ENDPOINT of the ``to`` edge.  ``ENFORCED`` inspects the edge's
# ``in``/``out`` columns and has no reach into a field of the record one endpoint points
# at.  And ``record<agent>`` constrains the TABLE, never the EXISTENCE of the row: a
# ``RecordID("agent", "does-not-exist")`` is a perfectly well-typed ``record<agent>``.
#
# RED TODAY: every leg except the two positive controls.
# =========================================================================== #


class _Ref:
    """A minimal ``AgentRefLike`` — id + name, read-only, structurally satisfying the
    Protocol without importing ``loremaster.agents`` (04a's own test idiom)."""

    def __init__(self, ref_id: str, name: str) -> None:
        self._id = ref_id
        self._name = name

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name


#: Unregistered SENDER identities, two SHAPES.  The second deliberately wears the
#: REGISTERED prefix, so a refusal keyed on a prefix, a literal, a length or "looks
#: unregistered" accepts it — adversary W-B's axis, on the sender door.
UNREGISTERED_SENDER_IDS = (
    "unregistered_sender_0000000000000000",
    "registered_agent_00000000000000000000000000000000",
)


@pytest_asyncio.fixture()
async def message_ledger_with_a_real_agent() -> AsyncIterator[tuple[Any, str, SurrealEnv]]:
    """A REAL ``MessageLedger`` on a database whose ``agent`` table holds exactly one row.

    Both the registered id and every unregistered one are ASSERTED present/absent, so the
    positive and negative legs share a fixture and neither can pass for a fixture reason.
    """
    from loremaster.messages import MessageLedger

    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    registered_id = f"registered_agent_{uuid.uuid4().hex}"
    setup = await connect_admin(env)
    try:
        await apply_ddl(setup, generate_agent_ddl(), url=env.url)
        await seed_endpoint(setup, AGENT_TABLE, registered_id)
        for absent in UNREGISTERED_SENDER_IDS:
            assert not await record_exists(setup, AGENT_TABLE, absent), (
                f"the negative fixture's sender id {absent!r} must genuinely NOT exist"
            )
    finally:
        await setup.close()

    ledger = MessageLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await ledger.ensure_ready()
    try:
        yield ledger, registered_id, env
    finally:
        await ledger.close()
        await drop_database(env)


async def _message_row_count(ledger: Any) -> int:
    rows = await ledger._query(  # noqa: SLF001 - the atomicity pins need the raw seam
        f"SELECT count() FROM {MESSAGE_TABLE} GROUP ALL"
    )
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


async def _to_edge_count(ledger: Any) -> int:
    rows = await ledger._query(f"SELECT count() FROM {TO_RELATION} GROUP ALL")  # noqa: SLF001
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


class TestSendRefusesAGhostSENDER:
    """RED today.  #247.

    ⚠ The door is UNREACHABLE through ``lore_comms action=send`` — ``AppContext.comms``
    resolves the caller with ``agent_registry.touch`` and passes the resolved ``Agent`` row
    through (scout §E1 layer 1).  It is wide open at the LEDGER seam, whose validation
    sequence is grade -> body -> pointers -> empty-recipients -> recipients -> dedupe ->
    write, with ``sender`` in NONE of them, and whose ``AgentRefLike`` is a STRUCTURAL
    protocol satisfied by any object with an ``id`` string.

    ⚠ **Fixing this makes ``_reject_unknown_recipients``' name and docstring inaccurate**
    (they say *"recipients"*) — the #219 class, one packet later, inside the fix for #247.
    Adjudicate it in the removed-behaviour inventory; do not leave the prose teaching a
    contract the code no longer has.
    """

    @pytest.mark.parametrize("ghost_sender", UNREGISTERED_SENDER_IDS)
    async def test_a_send_whose_SENDER_names_no_agent_row_is_REFUSED_and_NAMES_it(
        self,
        message_ledger_with_a_real_agent: tuple[Any, str, SurrealEnv],
        ghost_sender: str,
    ) -> None:
        ledger, registered, _env = message_ledger_with_a_real_agent
        with pytest.raises(Exception) as caught:  # noqa: B017 - the TYPE has its own pin below
            await ledger.send(
                sender=_Ref(ghost_sender, "phantom-lead"),
                session="wave7",
                body="a message from nobody",
                grade="signal",
                recipients=[_Ref(registered, "fixer-b")],
            )
        assert ghost_sender in str(caught.value), (
            f"the refusal must NAME the unresolved sender: {str(caught.value)!r}"
        )

    @pytest.mark.parametrize("ghost_sender", UNREGISTERED_SENDER_IDS)
    async def test_the_refused_send_leaves_NO_message_row_and_NO_edge(
        self,
        message_ledger_with_a_real_agent: tuple[Any, str, SurrealEnv],
        ghost_sender: str,
    ) -> None:
        """The pin that distinguishes *"refused early"* from *"rolled back late"* — the
        packet's own required shape for the ``send`` leg.  Both counts, because a rollback
        that reclaimed the message row but left an edge is a third outcome.
        """
        ledger, registered, _env = message_ledger_with_a_real_agent
        with pytest.raises(Exception):  # noqa: B017
            await ledger.send(
                sender=_Ref(ghost_sender, "phantom-lead"),
                session="wave7",
                body="a message from nobody",
                grade="signal",
                recipients=[_Ref(registered, "fixer-b")],
            )
        assert await _message_row_count(ledger) == 0
        assert await _to_edge_count(ledger) == 0

    async def test_POSITIVE_CONTROL_a_REGISTERED_sender_is_DELIVERED(
        self, message_ledger_with_a_real_agent: tuple[Any, str, SurrealEnv]
    ) -> None:
        """Without this, every leg above passes on a build that refuses every send."""
        ledger, registered, _env = message_ledger_with_a_real_agent
        result = await ledger.send(
            sender=_Ref(registered, "fixer-b"),
            session="wave7",
            body="a message from somebody",
            grade="signal",
            recipients=[_Ref(registered, "fixer-b")],
        )
        assert result.recipient_count == 1
        assert await _message_row_count(ledger) == 1
        assert await _to_edge_count(ledger) == 1

    async def test_a_BAD_sender_and_a_BAD_recipient_refuse_on_the_SENDER_FIRST(
        self, message_ledger_with_a_real_agent: tuple[Any, str, SurrealEnv]
    ) -> None:
        """ESCALATION E-4, pinned.  The check ORDER is a served-teaching decision, not an
        implementation detail: folding the sender into the recipient call would raise
        ``UnknownRecipientError`` for a bad SENDER, and a refusal that mis-names the role is
        a refusal an agent acts on wrongly.

        A message FROM a ghost is the worse fault, so it is reported first — and the
        recipient's id must NOT appear, or the caller cannot tell which identity to fix.
        """
        from loremaster.messages import UnknownRecipientError

        ledger, _registered, _env = message_ledger_with_a_real_agent
        ghost_recipient = "unregistered_recipient_000000000000"
        with pytest.raises(Exception) as caught:  # noqa: B017
            await ledger.send(
                sender=_Ref(UNREGISTERED_SENDER_IDS[0], "phantom-lead"),
                session="wave7",
                body="nobody to nobody",
                grade="signal",
                recipients=[_Ref(ghost_recipient, "phantom-fixer")],
            )
        assert not isinstance(caught.value, UnknownRecipientError), (
            "a bad SENDER was reported as an unknown RECIPIENT. The sender needs its own "
            "vocabulary — see this file's E-4 escalation for the alternative reading and "
            "its cost"
        )
        assert UNREGISTERED_SENDER_IDS[0] in str(caught.value)
        assert ghost_recipient not in str(caught.value), (
            "the sender refusal also named the recipient, so a caller cannot tell which "
            "identity it must fix first"
        )

    async def test_a_GOOD_sender_with_a_BAD_recipient_still_raises_UnknownRecipientError(
        self, message_ledger_with_a_real_agent: tuple[Any, str, SurrealEnv]
    ) -> None:
        """GREEN today — a REGRESSION pin.  Packet 04a's recipient guard and its vocabulary
        must survive the sender guard landing beside it (the removed-behaviour law: a
        preserved behaviour is preserved WITH A PIN, never by assertion).
        """
        from loremaster.messages import UnknownRecipientError

        ledger, registered, _env = message_ledger_with_a_real_agent
        with pytest.raises(UnknownRecipientError) as caught:
            await ledger.send(
                sender=_Ref(registered, "fixer-b"),
                session="wave7",
                body="somebody to nobody",
                grade="signal",
                recipients=[_Ref("unregistered_recipient_000000000000", "phantom-fixer")],
            )
        assert "unregistered_recipient_000000000000" in str(caught.value)

    async def test_the_sender_refusal_routes_through_the_SHARED_policy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        message_ledger_with_a_real_agent: tuple[Any, str, SurrealEnv],
    ) -> None:
        """⛔ W-E, on the sender door.  *"The fix itself is small: pass the sender into the
        same shared call"* (04a builder §7 E-2) — and a hand-rolled sender check would be
        exactly the copy #2 repo law forbids.

        Neutralise the policy inside ``loremaster.messages`` and the ghost sender must reach
        the WRITE.  ⚠ It does NOT reach an ``ENFORCED`` rejection, because ``sender`` is a
        FIELD and not an endpoint (§E3) — so the send SUCCEEDS, which is the door itself,
        reproduced deliberately as the observable.  A private sender check underneath the
        shared call keeps refusing and reddens here.
        """
        ledger, registered, _env = message_ledger_with_a_real_agent
        _neutralise_the_policy(monkeypatch, "loremaster.messages")
        result = await ledger.send(
            sender=_Ref(UNREGISTERED_SENDER_IDS[0], "phantom-lead"),
            session="wave7",
            body="the door, reproduced",
            grade="signal",
            recipients=[_Ref(registered, "fixer-b")],
        )
        assert result.recipient_count == 1, (
            "with the shared policy neutralised the ghost sender must reach the write — a "
            "refusal here means MessageLedger.send re-decides underneath the shared call, "
            "which is a private copy wearing the shared name"
        )


# =========================================================================== #
# MUTATION_PROOF — the DECLARED-RED sets, written BEFORE any run (finding #196).
#
# ⚠ THE DECLARED SETS BELOW ARE PREDICTIONS AND ARE LABELLED AS SUCH.  They were derived
# from ``pytest --collect-only -q`` (never transcribed from a run — a set read off failures
# you just watched is the tautology in a new costume) plus reasoning about which pins depend
# on the mutated thing.  Proofs 1 and 2 CANNOT be executed until the build lands, because
# their mutations are no-ops on a tree that never added the code.  ``scripts/mutation_proof.py``
# diffs BOTH ways — unexpected reds AND declared reds that stayed GREEN — and a mismatch is
# a finding about the BUILD, never a licence to edit these lists to match the output.
#
# ⚠ DO NOT PIPE ``mutation_proof.py`` INTO ``tail``/``head``: the pipe's exit status is the
# LAST command's, so a non-zero verdict is discarded and the block reads as a pass. That is
# #194's mechanism one level up, and it bit the author of that script on its first live run.
#
# ─────────────────────────────────────────────────────────────────────────────
# PROOF 1 — the ``blocks`` clause.  This is packet 04b-1's OWN leg of the
# "relation-edge mutation proof WIDENED from one edge to five" (§04b SPLIT).
#
#   F=loremaster/tests/test_blocks_edge.py
#   G=loremaster/tests/test_enforced_relations.py
#   A="$F::TestTheBlocksEdgeIsGuardedFromBirth"
#   B="$F::TestTheLedgersOwnMigrationPathLandsTheGuard"
#   C="$F::TestTheUnEnforcingDoor"
#   D="$F::TestTheBlocksEdgeIsDeclared"
#   E="$F::TestCreateTaskIsAtomic"
#   H="$F::TestTheRowExistencePolicyHasONEImplementation"
#   OLD="_define_relation_table(BLOCKS_RELATION, TASK_TABLE, TASK_TABLE, enforced=True)"
#   NEW="_define_relation_table(BLOCKS_RELATION, TASK_TABLE, TASK_TABLE)"
#   ./scripts/mutation_proof.py \
#     --file loremaster/loremaster/store/surreal_schema.py \
#     --anchor "$OLD" --replacement "$NEW" \
#     --expect-red "$A::test_the_blocks_edge_carries_ENFORCED_in_its_own_slice[generate_task_ddl]" \
#     --expect-red "$A::test_the_blocks_edge_carries_ENFORCED_in_its_own_slice[generate_ddl]" \
#     --expect-red "$D::test_the_universal_pin_now_covers_blocks" \
#     --expect-red "$B::test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE" \
#     --expect-red "$B::test_the_migration_is_IDEMPOTENT_on_an_ALREADY_migrated_store" \
#     --expect-red "$C::test_re_emitting_blocks_WITHOUT_ENFORCED_silently_un_guards_it" \
#     --expect-red "$E::test_a_create_whose_RELATE_cannot_land_writes_NO_task_row" \
#     --expect-red "$E::test_create_many_is_ALL_OR_NOTHING_when_ONE_items_RELATE_cannot_land" \
#     --expect-red "$H::test_MUTATION_neutralising_the_shared_policy_lets_a_CREATE_reach_the_ENGINE" \
#     --expect-red "$X::test_EVERY_relation_table_the_schema_emits_is_ENFORCED" \
#     -- uv run pytest -q --show-capture=no "$F" "$G"
#
# (where X="$G::TestEveryRelationEdgeIsEnforced",
#        Y="$G::TestTheSERVEDRefusalTextHasONEImplementation",
#        P="$F::TestAPhantomBlockerIsRefusedAndNamed" — used below too.)
#
# WHY EACH: the two slice pins and the ∀ read the clause directly.  The three live-store
# pins observe the guard REFUSING a ghost, which it stops doing.  The two atomicity pins
# and the neutralised-policy pin deliberately OBSERVE BOTH LAYERS — they neutralise the app
# check precisely so the ENGINE's rejection is what they measure — so they redden CORRECTLY
# when the engine clause is gone, and they are the only app-adjacent pins in the set.
#
# WHY NOT the rest of sections F–H: every other app-check pin depends on the APP layer, not
# on the engine clause, and a build that reddened them here would have coupled two layers
# this contract requires to stay independent.  ``--show-capture=no`` is required or a
# captured log line mimics a summary line (04a fixwave §F1).
#
# ─────────────────────────────────────────────────────────────────────────────
# PROOF 2 — ONE IMPLEMENTATION.  L3's demanded proof, in its SHELL form: change the shared
# refusal SENTENCE and BOTH families' served-text pins must redden.
#
#   ./scripts/mutation_proof.py \
#     --file loremaster/loremaster/agent_existence.py \
#     --anchor '<the shared skeleton literal, e.g. f"unknown {noun}(s): ">' \
#     --replacement '<the same with "unknown" -> "unrecognised">' \
#     --expect-red "$P::test_the_SERVED_refusal_text_is_EXACTLY_the_task_sentence" \
#     --expect-red "$Y::test_the_PRODUCTION_refusal_text_is_EXACTLY_the_served_sentence" \
#     --expect-red "$Y::test_the_BRIEF_fake_serves_the_SAME_sentence_as_production" \
#     --expect-red "$Y::test_the_MESSAGE_fake_serves_the_SAME_sentence_as_production" \
#     -- uv run pytest -q --show-capture=no "$F" "$G"
#
# ⚠ THE ANCHOR IS THE ONE PART THAT CANNOT BE PREDICTED — it depends on how the builder
# spells the generalised skeleton.  The DECLARED-RED SET is the load-bearing half and is
# NOT negotiable: four legs, two families, one mutation.  Its IN-SUITE counterpart is
# ``TestTheRowExistencePolicyHasONEImplementation``'s
# ``test_MUTATION_replacing_the_shared_FORMATTER_changes_BOTH_refusals``, which runs in
# every gate and needs no shell block; this proof adds what a monkeypatch cannot, namely
# that the two families ride ONE LITERAL and not merely one function.
#
# ─────────────────────────────────────────────────────────────────────────────
# PROOFS 3–5 — the OTHER FOUR edges, so the widening is real and not a claim.
#
# ⚠ THE WIDENING IS NOT UNIFORM, AND THAT IS STATED RATHER THAN PAPERED OVER.  ``briefed``,
# ``to`` and ``blocks`` carry ``enforced=True``, so their mutation is DELETING it.
# ``refers`` and ``answers_to`` are deliberately UN-enforced pending packet 43 — there is no
# ``enforced=True`` to delete, so their per-edge mutation must be a DIFFERENT one (swap the
# IN/OUT tables), proving that THEIR pins are live rather than that their guard is.  A proof
# that declared the same mutation for all five would produce declared reds that stay GREEN.
#
#   PROOF 3 (``briefed``) — **EXECUTED 2026-07-28 at `c5a2552` + this contract: PROOF HELD,
#     12/12 declared, no unexpected reds, no declared-green, tree restored byte-exact
#     (surreal_schema.py md5 dc5dc6f18eb6dc87dbb8cd8d26df417d).**  It is 04a's own block in
#     ``test_enforced_relations.py``, run with THREE additions to its declared set: this
#     contract's three already-RED ``blocks`` declaration pins (which are red for a reason
#     unrelated to the mutation and would otherwise read as unexpected reds), and — the one
#     that matters — the new ``ack`` leg, which reddened exactly as predicted.  Do not
#     re-derive the other nine; re-run them.
#   PROOF 4 (``to``) — **EXECUTED 2026-07-28: PROOF HELD, 6/6, EXIT=0 (unpiped), tree
#     restored byte-exact.**  Declared set, MEASURED rather than guessed:
#     --anchor "_define_relation_table(TO_RELATION, MESSAGE_TABLE, AGENT_TABLE, enforced=True)"
#     --replacement "_define_relation_table(TO_RELATION, MESSAGE_TABLE, AGENT_TABLE)"
#     --expect-red "$X::test_EVERY_relation_table_the_schema_emits_is_ENFORCED"
#     --expect-red "$X::test_the_edge_carries_ENFORCED_in_its_own_slice[to-generate_message_ddl]"
#     --expect-red "$S::test_MUTATION_neutralising_the_shared_policy_lets_send_reach_the_ENGINE"
#         (S="$G::TestTheSharedPolicyIsTheSOLEDecisionPoint")
#     + this contract's three already-RED ``blocks`` declaration pins.
#     ⚠ **THE THIRD ENTRY IS THE FINDING.**  04a's own block records only ``briefed``'s
#     proof and had no reason to notice that the SEND leg of
#     ``TestTheSharedPolicyIsTheSOLEDecisionPoint`` is coupled to ``to``'s clause — it
#     neutralises the app policy precisely so the ENGINE's rejection is what it measures, so
#     un-enforcing ``to`` makes it DID-NOT-RAISE.  A four-entry declaration would have
#     reported an unexpected red and read as a wrong prediction.
#   PROOF 5 (``refers`` / ``answers_to``) — **NOT EXECUTED.**  Swap the endpoint tables in
#     each call and declare
#     "$X::test_the_edge_declares_its_IN_and_OUT_endpoint_tables[<edge>-endpointsN]"
#     — the parametrised id must be taken from ``--collect-only``, never typed from the
#     source (pytest ASCII-escapes and index-suffixes parametrised ids, and adding ``blocks``
#     to ``KNOWN_RELATION_EDGES`` RENUMBERED every ``endpointsN`` suffix in that pin).
# =========================================================================== #
