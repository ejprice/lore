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
THE TRUST DEFINITION, APPLIED TO THIS PACKET (added 2026-07-28, wave r4)
============================================================================

``CLAUDE.md`` § *TRUST — THE HARD DEFINITION* landed on this branch at ``0acbf47``
(merged ``c55792a``): *a response is trustworthy iff a consumer who acts on it WITHOUT
CHECKING cannot be wrong in a way the response did not name*, achieved when BOTH legs
pass — **leg 1 SCOPE DIFF** (design-time, healthy path) and **leg 2 FORGERY PINS**
(build-time, degraded path: the surface's stateful dependencies × ``{stale, empty,
wrong-instance, partial}``, CONSTRUCTED and byte-diffed against the healthy response;
identical bytes = a false clear = STOP).

**LEG 1 — the scope diff for the surfaces THIS packet serves.**  For each: the question
the code actually answers (set / predicate / time) beside the question a consumer thinks
it asked.  A row with a difference names where that difference is carried.

⚠⚠ **ROWS 1 AND 2 WERE MEASURABLY FALSE AS FIRST WRITTEN, AND THE CORRECTIONS ARE THE
INTERESTING PART** (delta adversary §LEG1, 2026-07-28; both re-derived here).  Row 1 said the
edge-vs-column difference was *"CLOSED"* — a one-word claim about a whole set, contradicted by
two builds that pass this contract entire (§P1 WB-E, WB-O).  Row 2 said *"no unnamed difference
remains"* — contradicted by a live measurement.  **Leg 1 is a claim about the RESPONSE, so a
row may state only what the response is TRUE of; where a guarantee depends on something having
happened, the row names that something as a FACT rather than asserting the difference away.**

* ``transitive_blockers(task_id)``
  — **answers:** *"the tasks reachable UPSTREAM over the ``blocks`` EDGES **this ledger's last
  completed ``ensure_ready`` mirrored**, from this task, to a depth of at most
  ``max_depth_used``, **at this ledger**, as of this read."*
  — **asked:** *"what blocks this task?"*
  — **DIFFERENCES, and where each is carried:** (a) *edges vs the ``blocked_by`` COLUMN* —
  R11's backfill is what makes the two agree, and the agreement is pinned in SECTION K
  (``TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS``) rather than disclosed in the render.  ⚠ The
  predicate above says *"a COMPLETED migration"* because a migration that ran PARTIALLY, or
  failed and was swallowed, re-opens this difference exactly — a confident
  ``ids=[] truncated=False`` on production's real rows, which is sidecar S3, the packet's worst
  defect.  Those two states are now CONSTRUCTED, not argued
  (``TestTheBackfillCoversALegacyStoreLARGERThanEveryOtherFIXTURE``,
  ``TestANYBackfillFailureMakesEnsureReadyLOUD``).  (b) *the depth bound* — carried by
  ``truncated`` + ``max_depth_used`` on the result itself (``TestTheReadIsHONESTAtItsBound``,
  ``TestTheResultIsSELFDESCRIBING``).  (c) *a ``blocked_by`` entry that names NO task row* — a
  PHANTOM, which ``ENFORCED`` forbids as an edge and R11's backfill therefore SKIPS; the
  residue is legacy-only (new writes are refused by the pre-check) and is carried by the
  helper's own docstring (``TestTheScopeOfTheTransitiveReadIsSTATED``).  (d) *a mis-set
  ``database``* serves the same bytes from a different store — named by *"at this ledger"*,
  the treatment row 3 already had and this row did not.
* ``query_tasks(status=…, owner=…, blocked=…, limit=…)``
  — **answers:** *"tasks matching the store-side filters, partitioned by a ONE-HOP blocked
  predicate resolved against the candidate set's blockers, windowed to ``limit`` ANSWERS."*
  — **asked:** *"what work matches this?"*
  — **NAMED DIFFERENCES:** the one-hop-not-transitive partition and the
  answer-cap-not-scan-cap semantics, both pinned in ``test_query_tasks_bounded.py``
  (``TestTheBlockedPartitionIsONEHOPNeverTransitive``,
  ``TestTheCapAppliesToTheANSWERNotTheCandidateScan``).
  — ⚠ **AN UNNAMED DIFFERENCE REMAINS, AND IT IS THE ONE A CONSUMER ACTUALLY MEETS.**
  MEASURED 2026-07-28: ``lore_tasks action=query limit=5`` against a ledger of 40 matching
  tasks renders five rows and **nothing saying the listing is partial** — nor which five (this
  contract deliberately pins no ORDER, so the choice is arbitrary and unstable).  The reader is
  an AGENT; one that acts without checking concludes the ledger holds five open tasks, which
  is wrong in a way the response did not name.  **It is a RENDER, and the render is 04b-2's**
  (T1's rendered half + R9's counted-elision line), so 04b-1 pins the false clear as a BOUND
  rather than closing it: ``test_query_tasks_bounded.py::
  TestACappedListingDISCLOSESNothingAboutItsOwnBOUND`` constructs both worlds and reddens the
  day the disclosure lands.  Owner **04b-2**; escalation §ESC-5 of
  ``REPORT-contractfix-04b1-r6.md``.
* the blocker pre-check refusal — **answers:** *"these ids name no LIVE task row at this
  ledger, as of the check"*; **asked:** *"is this dependency valid?"*  Difference: a
  SUPERSEDED blocker exists but is never legitimate, and is named separately with its
  successor (R10(ii), ``TestASupersededBlockerIsNotASilentBlackHole``).
  ⚠ **This row is the model for the other four** — *"at this ledger"* names the wrong-instance
  difference (a mis-set ``database`` serves the same bytes) and *"as of the check"* names the
  TOCTOU window, both as FACTS, with no disclaimer word anywhere.  Do not weaken it.
* the ``send`` sender guard — **answers:** *"this sender id names no ``agent`` row"*, in the
  message ledger's OWN vocabulary (E-4), so a refusal cannot be misread as being about a
  recipient.
* the **cycle refusal** (``format_cycle_refusal`` / ``TaskCycleError``)
  — **answers:** *"these ids close a cycle in the ``blocked_by`` COLUMN, over the rows this
  guard read, as of that read."*
  — **asked:** *"why was my create refused?"*
  — **DIFFERENCES:** (a) it walks the COLUMN, so a cycle present only in the EDGES is invisible
  to it — which is a difference and not a defect, because R7's rider establishes that the
  closing dependency of a cycle CANNOT carry an edge; (b) the batch-KEY and PERSISTED-ID
  vocabularies deliberately differ (R6 permits it: *"the vocabularies may still differ because
  they name different things"*), so the ids in the refusal are the ids of the world the caller
  addressed, never a translation.
* the **migration's operator record** (the WARNING stream: phantom skips and legacy cycles)
  — **answers:** *"the phantom blockers this boot skipped, and every ``blocked_by`` cycle it
  mirrored, in the rows this boot read."*
  — **asked:** *"what is wrong with my store?"*
  — **DIFFERENCE, and it was a real hole:** it is per-BOOT and per-READ, not a survey of the
  store; and it used to name only the FIRST cycle, which is a claim about one loop read as a
  claim about the store's loops.  Now ∀ cycles
  (``TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST``), with the decomposition bound stated
  there.  The record's consumer is the OPERATOR (ESC-1 reading A); the AGENT-facing bound is
  the read surface's own scope statement, which is a separate row above.
* ``ensure_ready()``'s **normal return**
  — **answers:** *"the task schema is applied and every ``blocked_by`` column this boot read
  is mirrored onto ``blocks``."*
  — **asked, by the booting service:** *"is this store migrated?"*
  — **DIFFERENCE:** none is carried, and none needs to be — **because the claim is enforced
  rather than disclosed**: any failure of the backfill, at ANY of its doors, makes the call
  RAISE (``TestANYBackfillFailureMakesEnsureReadyLOUD``, ∀ over
  ``BACKFILL_FAILURE_DOORS``), and the coverage is ∀ rows rather than ∀ rows-up-to-a-fixture
  (``TestTheBackfillCoversALegacyStoreLARGERThanEveryOtherFIXTURE``).  ⚠ Both pins exist
  **because a build that returned normally over a silently absent edge set passed this
  contract whole** (WB-O, 234 passed / 0 failed) — this row would have been false, and no pin
  could see it.

⚠ **LEG 1'S OWN STATED BOUND, from the law:** it is sound on *set* and
*predicate-as-WRITTEN* only — **time, environment and predicate-as-EXECUTED are BELIEVED,
not known** (#24 · #107 · #131 · #139).  Every row above is a claim about what the code
SAYS, and only leg 2's constructions are claims about what it DOES.

**LEG 2 — and the bound on the table this contract works from, stated as a FACT.**
The owed-construction table is ``docs/design/2026-07-28-04b-model-consumer-audit.md``
§11.1.  **``scripts/forgery_sites.py`` — the DERIVATION §12.2 specifies — DOES NOT
EXIST.**  §11.1's table is therefore a **CURATED INTERIM, bounded to five served surfaces
and to one reader's sight**, not a derived failure set; §12.3 says so in its own words.
The law PERMITS a bounded interim and FORBIDS presenting it as complete, so this is
recorded here as a fact rather than a disclaimer: *the constructions in SECTION L cover
the dependencies and verbs written down in §11.1 and nothing else, and a false clear found
later is a RE-OPEN TRIGGER, never a retroactive pass.*  04b-1 owns the traversal-timeout
row, the pre-check-failed-read row and R9's honest-total row (the last of which resolves
to an ASSERTED EMPTINESS — see ``test_query_tasks_bounded.py``); 04b-2 owns the
fleet-column and footer rows.

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

✅ **AND IT NO LONGER REDDENS ANYTHING IN ``test_mcp_server.py`` (wave r5, 2026-07-28).**
A CORRECT build was MEASURED to break FIVE committed pins there, of which the contract
disclosed TWO — R9's two, plus R6's cycle CLASS against a ``pytest.raises(ValueError)``,
plus TWICE ``_task_fakes.FakeTaskLedger.query_tasks`` not accepting R5's ``limit``.  All
five were **RE-AUTHORED IN PLACE** to pin only what survives the rulings, so each is green
before the fix and after; each carries a ``RE-AUTHORED 2026-07-28`` docstring naming the
ruling that retired its old assertion and the pin that now owns the property.  **A builder
must never be trapped between a red test it may not edit and a fix that cannot make it
green** — disclosing that trap a third time would have moved the defect, not removed it.

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
import asyncio
import inspect
import logging
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _enforced_relations_scaffold import (
    BLOCKS_RELATION_NAME,
    DEFERRED_TO_PACKET_43,
    KNOWN_RELATION_EDGES,
    MIGRATION_DIM,
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
    StoreTraffic,
    SurrealConnection,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    measure_store_traffic,
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
    STATUS_BLOCKED,
    STATUS_CLAIMED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    STATUS_WONTFIX,
    Task,
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

#: The LEDGER-OWNED cycle DETECTION algorithm (operator ruling **R6**, 2026-07-28): the ONE
#: implementation that BOTH the ledger's write-time guard and ``server.py``'s batch-key
#: check route through.  R6, verbatim: *"The DETECTION ALGORITHM is shared; the vocabularies
#: may still differ (batch-local temp keys vs persisted ids) because they name different
#: things."*  This is the mutation point for section E's sharing proof.
SHARED_CYCLE_DETECTOR_MODULE = "loremaster.tasks"
SHARED_CYCLE_DETECTOR_ATTR = "find_blocked_by_cycle"

#: The shared cycle-refusal FORMATTER — R6's *"one refusal sentence shape"*, with the noun
#: supplied by the caller so a batch KEY cycle and a PERSISTED-ID cycle read as what they
#: are.  Mutating it must change BOTH served sentences (the L3 instrument, applied to the
#: cycle policy).  Pinned only BY MUTATION, never by signature: every proof below replaces
#: it with ``lambda *args, **kwargs: sentinel``, so any spelling of its parameters passes.
SHARED_CYCLE_FORMATTER_ATTR = "format_cycle_refusal"

#: ``server.py``'s dispatcher module — the SECOND consumer of the detector above, and the
#: one whose refusal a ``lore_tasks`` caller is actually served (R6: today it fires FIRST
#: with a bare ``ValueError`` and its own sentence, so no cycle pin in this file observes
#: anything an agent receives).
TOOL_SEAM_MODULE = "loremaster.server"


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

#: A bare 32-CHARACTER id of the LENGTH ``TaskLedger`` mints (``uuid4().hex``).  A phantom
#: blocker whose length and character class are unremarkable, so a refusal keyed on "looks
#: wrong" accepts it.
#:
#: ⚠ **IT IS NOT THE RENDERING ``uuid4().hex`` PRODUCES, and an earlier version of this
#: comment said it was** (adversary R-17, corrected 2026-07-28).  All-zeros is
#: all-DIGITS, and SurrealDB brackets a record-id component that is not a legal bare
#: identifier — so ``str(RecordID(TASK_TABLE, "0"*32))`` renders ``task:⟨00…0⟩``, while a
#: real ``uuid4().hex`` almost always contains a letter and renders BARE.  Read as "the
#: shape the ledger mints", this constant taught the OPPOSITE of the truth about which
#: shape is bracketed — which is the one axis finding #248 is about.  The genuinely
#: bare-rendering fixtures are the ledger-minted ids the live fixtures create; the
#: bracket-rendering shapes are pinned on the ACCEPTED side by
#: :class:`TestARealBlockerOfANyIDShapeRoundTrips`.
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
        f"unknown task(s): {', '.join(ids)} — every blocked_by entry must name an existing "
        f"task row or a task created in the same call; NOTHING was created, so a corrected "
        f"resend is safe"
    )


def _served_blocker_identity(blocker_id: str, *, item_index: int | None = None) -> str:
    """ONE unresolved blocker, as the served refusal must render it (**RIDER-A**).

    ``<id>`` on the single-task path, ``<id> (item <n>)`` on the batch path — the id
    FIRST, always, and always verbatim.

    **WHY the locus (design sidecar §2 R2-a, consult-unanimous):** an agent that sends
    ``create_many`` with twenty items and is told *"unknown task(s): step-schma"* cannot
    tell WHICH item carried it, and a value appearing in two of six items makes the first
    retry a coin flip.  The locus is what turns a refusal into a one-edit fix.

    **WHY the id stays FIRST and verbatim (§4, and it is the load-bearing half):** the
    property both consults named, identically, is *"the refusal contains the offending
    value verbatim, in the exact form the caller supplied it, round-trippable against the
    caller's own payload."*  ⚠ Note that this holds for a typo'd BATCH KEY too, without the
    ledger ever knowing what a key is: the dispatcher's ``key_to_id.get(ref, ref)``
    pass-through means an unresolved key ARRIVES as the "phantom id", so the caller is
    echoed its own token either way.

    ⚠ **THE LEDGER IS KEY-AGNOSTIC AND STAYS SO.** The sidecar's example carries the key
    as well (``'step-schma' (item 3, key 'step-migrate')``); ``TaskLedger.create_many``
    takes ``specs``/``ids`` and has never seen a key — that half belongs to
    ``AppContext._create_many`` and is a THIRD ``server.py`` touch beyond R5's and R6's
    named exceptions.  Escalated in ``REPORT-contractfix-04b1.md``, not silently folded in.
    """
    return blocker_id if item_index is None else f"{blocker_id} (item {item_index})"


def _served_superseded_clause(blocker_id: str, successor_id: str) -> str:
    """The RULED clause a caller naming a SUPERSEDED blocker is served (**R10(ii)**).

    Operator ruling **R10**, 2026-07-28, verbatim: *"04b-1's blocker pre-check refuses a
    superseded blocker and names its successor (``task X is superseded by Y — block on Y
    instead``) — near-zero cost, the grouped existence query already holds the rows, and a
    ``blocked_by`` naming a superseded task is NEVER legitimate."*

    ⚠ **DELIBERATELY NOT DERIVED FROM PRODUCTION**, for :func:`_served_task_refusal`'s
    reason: a pin that asked the formatter what the text is agrees with it by construction.
    THIS IS THE SPEC.

    ⚠⚠ **PINNED AS A CLAUSE, NOT AS THE WHOLE SENTENCE — AND THAT IS AN ESCALATION, NOT A
    PREFERENCE.**  R10 quotes one sentence and does not say whether it is the COMPLETE
    served text or a new clause inside the existing refusal skeleton (which RIDER-B requires
    to carry *"NOTHING was created"*).  Those two readings produce different code, so per
    brief-base §2 both are written down and neither is picked silently:

    * **(i) the clause reading** — the refusal is the shared skeleton plus this clause, so a
      caller learns BOTH what is wrong and that nothing landed;
    * **(ii) the whole-sentence reading** — this string, alone, is the served text.

    **Recommendation: (i)**, because RIDER-B's justification is general (*"an agent reading
    only 'refused' does not know whether a partial batch landed, so it must pay a
    reconnaissance read before it dare resend"*) and nothing in R10 retracts it.  **The pins
    below are satisfiable under BOTH** — they assert this clause appears VERBATIM and, in a
    separate leg with its own failure message, that the no-write fact is stated.  A
    by-value whole-sentence pin would have been a C-DEF under reading (i).
    """
    return (
        f"task {blocker_id} is superseded by {successor_id} — "
        f"block on {successor_id} instead"
    )


def _served_max_depth_refusal(value: int) -> str:
    """The EXACT sentence a caller passing an out-of-range ``max_depth`` is served.

    ⚠ **DELIBERATELY NOT DERIVED FROM PRODUCTION**, for :func:`_served_task_refusal`'s
    reason: a pin that asked the code what the text is would agree by construction.  THIS
    IS THE SPEC of the served surface, and the surface's consumer is an AGENT — a refusal
    that does not state the valid range leaves the caller guessing at a bound it cannot see.

    ⚠ **THE UPPER BOUND IS A CONTRACT DECISION AND BOTH READINGS ARE WRITTEN DOWN**
    (adversary MP-3, escalated 2026-07-28).  The adversary MEASURED two "correct" builds
    disagreeing about where this API breaks: a build that probes at ``max_depth + 1`` to
    detect truncation cannot honestly serve ``max_depth = 256`` (the engine refuses a bound
    of 257), while a single-query build can.  **PINNED: refuse at or above
    ``ENGINE_RECURSION_CEILING``** — satisfiable by BOTH build shapes, and it keeps the
    public bound a property of the API rather than of an implementation detail a caller
    cannot see.  *Alternative:* allow exactly 256 and forbid only 257+, which is one edit
    here and forecloses the probe-at-N+1 design.
    """
    return (
        f"max_depth={value} is out of range — it must be at least 1 and strictly below the "
        f"engine's recursion ceiling of {ENGINE_RECURSION_CEILING}"
    )


def _tool_seam(ledger: TaskLedger) -> Any:
    """``AppContext``'s ``lore_tasks`` dispatcher, wired to a REAL ledger and NOTHING else.

    ⚠ **WHY THIS EXISTS AT ALL (operator ruling R6):** every cycle pin in this contract
    calls ``TaskLedger`` directly, so none of them observes what a ``lore_tasks`` caller is
    actually served — and ``AppContext._find_key_cycle`` fires FIRST, with its own sentence
    and a bare ``ValueError``.  A contract that never drives the dispatcher cannot see that.
    THE CONSUMER IS AN AGENT: the served refusal is the whole of what it learns.

    ``__new__`` without ``__init__`` because the ``tasks`` handler's create/query paths
    touch exactly ONE attribute — ``self.task_ledger`` — plus its own classmethods, and
    building a whole runtime bundle (embedder, stores, watcher, five ledgers) to reach one
    dispatcher would be a fixture nobody can read.  The AppContext docstring names this
    posture itself: *"the handlers are the single, fully end-to-end-testable surface"*.
    ⚠ **Stated bound:** an attribute the dispatcher gains LATER and reads on these paths
    surfaces here as ``AttributeError``, which is a LOUD failure naming the attribute — not
    a silent skip.
    """
    from loremaster.server import AppContext

    context = AppContext.__new__(AppContext)
    context.task_ledger = ledger
    return context


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
    """RED today.  ⛔ **The pins that kill a BARE-IDIOM detector — IN THE READ.**

    ⚠⚠ **THIS CLASS IS ABOUT THE READ, NOT THE WRITE-TIME GUARD, AND ITS DOCSTRING USED TO
    CONFLATE THEM** (adversary MP-4a, corrected 2026-07-28).  What it used to say — *"the
    working acyclicity detector is the ``+collect`` self-reach"* — is TRUE of the transitive
    READ this class exercises and **FALSE of the guard that refuses a cycle at WRITE time**,
    which is :class:`TestCreateRefusesToFormACycle`'s subject and cannot use the engine at
    all.  See that class's docstring for why, and the package table in
    ``REPORT-contractfix-04b1.md`` for the verdict this correction changes.

    Probe §5.4, MEASURED on 3.2.1: the read's detector is *"the task appears in its own
    ``+collect`` reach"*.  The BARE form is **not** a detector — the probe's own ``@.{..8}``
    leg "detected" a 4-cycle **by arithmetic accident**, because 8 mod 4 = 0 landed back on
    the start node.  *A positive result for the wrong reason.*  With a **3-cycle** and depth
    8 the same query returns a different node and reports ACYCLIC.  (The adversary's §X1
    reproduced the same accident on the REVERSE arrow this design traverses: 3 misses, 4
    hits, 5 misses.)

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

    ⚠⚠ **THE WRITE-TIME GUARD MUST WALK THE ``blocked_by`` COLUMN, CLIENT-SIDE.  IT CANNOT
    BE THE ENGINE'S SELF-REACH OPERATOR, AND A BUILDER WHO REACHES FOR IT WILL FAIL ONE PIN
    HERE WITH NO SENTENCE EXPLAINING WHY** (adversary MP-4a; ruling R7's rider,
    2026-07-28).  The reason is structural and it is caused by this packet's OWN guard:
    ``test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED`` writes the
    closing dependency as a COLUMN-ONLY ``UPDATE``, and **no other write is possible** —
    the dependency names a task that does not exist yet, so ``ENFORCED`` rejects the
    ``RELATE``.  There is therefore no ``blocks`` edge on that link, and **any engine
    traversal returns "acyclic"**.  Measured: a build whose cycle check walks the EDGE
    fails exactly this one pin.

    The column is also the RIGHT thing to walk, not merely the possible one: the claim CAS
    reads ``blocked_by``, so a COLUMN cycle is what makes a task unclaimable forever — which
    is the harm this guard exists to prevent.

    ⚠ **AND IT COMPOSES WITH R7:** a client-side walk is N reads, and R7 puts the bounded
    read's N reads inside ONE ``BEGIN … COMMIT``.  A builder must not satisfy one by
    breaking the other — see
    :meth:`TestCreateRefusesToFormACycle.test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain`.

    ⚠ **PACKAGE VERDICT, CORRECTED TWICE — AND THE SECOND CORRECTION IS THE HONEST ONE.**

    v1 said *"replace with the engine operator"*.  That is right for the transitive READ (the
    closure stays on the engine — packages over hand-rolling) and WRONG for this guard, for
    the structural reason above: the closing dependency cannot carry an edge.

    v2 corrected it to ``bespoke`` — *"a DFS over the column, nothing more"* — and **its
    read-column evaluated no library at all.**  That is the exact shape ``brief-base.md``
    names as the defect the ``Packages considered:`` line exists to catch: *"asserting a
    package limitation without reading the API"*, and a correction is a specification too.

    **v3, MEASURED (final adversary §PKG, 2026-07-28): the verdict is ``replace``, and the
    library is STDLIB.**  ``graphlib.TopologicalSorter`` ships with Python;
    ``CycleError.args[1]`` IS the cycle, in the exact shape BOTH call sites need — RUN on six
    graph shapes: a 2-cycle yields ``['a', 'b', 'a']``, a SELF-loop yields ``['x', 'x']``
    (byte-for-byte the format ``AppContext._find_key_cycle``'s own docstring already
    promises), a 3-cycle yields ``['a', 'c', 'b', 'a']``, an acyclic diamond yields ``None``,
    and a dependency naming an id OUTSIDE the graph is tolerated — which is precisely what a
    ``blocked_by`` entry pointing outside the read needs.  ``CycleError`` is a ``ValueError``
    subclass.  The swap was made in a reference build and the whole contract stayed green.

    ⚠ **AND NO PIN IN THIS FILE REQUIRES IT**, deliberately: every cycle pin is behavioural
    (which graphs are refused, which are accepted, whether ONE implementation is shared —
    proved by MUTATION).  A builder may still hand-roll the walk; what the rule asks is that
    the choice be made against a READ API rather than an assumption, and that if the answer
    is still ``bespoke`` the report says what was read and why the stdlib did not fit.
    Whatever is chosen, ruling R6 stands: ONE implementation, shared with ``server.py``'s
    batch-key check rather than becoming policy copy #2.

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

    async def test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **R7's rider, as an instrument — the pin that stops one ruling being satisfied
        by breaking the other.**

        The guard above must walk the ``blocked_by`` COLUMN client-side (see this class's
        docstring), and a client-side walk over a chain of depth N is N reads.  Ruling R7
        puts exactly that shape inside ONE ``BEGIN … COMMIT`` so the reads share a snapshot
        — *"the TOCTOU is CLOSED BY CONSTRUCTION, not measured and accepted"*.  A build that
        issues one round trip per hop has neither the snapshot nor the bound, and NOTHING
        else in this contract can tell the two apart: both refuse the same cycles, both
        accept the same chains, both go green.

        THE DISCRIMINATION IS A GROWTH COMPARISON on ROUND TRIPS, not on rows and not
        against a threshold.  A per-hop walk costs N calls and grows with the chain; a
        walk inside one transaction costs the same number of calls at any depth.  Rows are
        deliberately NOT asserted: a deeper chain legitimately reads more rows, so a row
        comparison here would forbid the correct build.

        ⚠ Both creates run against the SAME ledger, so the only variable is the depth of
        the chain each one is blocked on.
        """
        ledger, env, _blocker = task_ledger
        setup = await connect_admin(env)
        try:
            shallow = await _seed_chain(setup, 3)
            deep = await _seed_chain(setup, 30)
        finally:
            await setup.close()

        shallow_traffic = await measure_store_traffic(
            ledger,
            lambda: ledger.create_task(
                "blocked on a shallow chain", DESCRIPTION, blocked_by=[shallow[-1]],
                created_by=CREATOR,
            ),
        )
        deep_traffic = await measure_store_traffic(
            ledger,
            lambda: ledger.create_task(
                "blocked on a deep chain", DESCRIPTION, blocked_by=[deep[-1]],
                created_by=CREATOR,
            ),
        )
        assert shallow_traffic.calls > 0, (
            f"the instrument saw NO store traffic for a create that must at least write a "
            f"row — it is not observing this path, so the comparison below is worthless: "
            f"{shallow_traffic}"
        )
        assert deep_traffic.calls == shallow_traffic.calls, (
            f"a create blocked on a 3-deep chain cost {shallow_traffic.calls} round trips "
            f"and one blocked on a 30-deep chain cost {deep_traffic.calls}. The acyclicity "
            f"walk is issuing one round trip PER HOP, so (a) its reads do not share a "
            f"snapshot — a writer committing between them can hide a cycle from the guard "
            f"that is looking for it — and (b) the cost grows with the graph. Ruling R7: "
            f"the reads go inside ONE BEGIN…COMMIT. ⚠ Do NOT satisfy this by dropping back "
            f"to an ENGINE traversal of the blocks edge: the closing dependency of a cycle "
            f"CANNOT carry an edge (see this class's docstring), so an engine detector "
            f"returns 'acyclic' and reddens the persisted-cycle pin above. "
            f"shallow={shallow_traffic.statements} deep={deep_traffic.statements}"
        )

    @staticmethod
    async def _create_many_traffic(unrelated_count: int) -> tuple[StoreTraffic, int]:
        """Traffic and answer size for ONE ``create_many`` naming ONE existing blocker.

        ``create_many`` rather than ``create_task``, and the choice is load-bearing: a
        ``create_task`` id is a fresh ``uuid4`` no caller has seen, so a build may skip the
        persisted-cycle walk on that path entirely and the measurement would observe nothing.
        ``create_many`` is the path the guard actually runs on.

        The noise tasks are unrelated, unblocked and open, so the WORK is identical at every
        ``unrelated_count`` by construction and any difference in rows-read is caused by the
        LEDGER's size.  The created count travels back beside the number for its sibling's
        reason: *"this number did not grow"* is TRUE of a build that reads nothing and
        creates nothing.
        """
        from loremaster.tasks import TaskSpec

        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        ledger = TaskLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )
        try:
            await ledger.ensure_ready()
            await _seed_unrelated_tasks(ledger, unrelated_count)
            blocker = await ledger.create_task("a real blocker", DESCRIPTION, created_by=CREATOR)
            created: list[str] = []

            async def _run() -> None:
                created.extend(
                    await ledger.create_many(
                        [
                            TaskSpec(
                                subject=SUBJECT,
                                description=DESCRIPTION,
                                blocked_by=[blocker],
                            )
                        ],
                        created_by=CREATOR,
                    )
                )

            traffic = await measure_store_traffic(ledger, _run)
            return traffic, len(created)
        finally:
            await ledger.close()
            await drop_database(env)

    @staticmethod
    async def _blocked_noise_traffic(blocked_pair_count: int) -> tuple[StoreTraffic, int]:
        """Traffic for ONE ``create_many`` against a ledger of ``blocked_pair_count``
        DEPENDENCY-BEARING rows that have nothing to do with the dependency under check.

        The sibling helper above seeds UNBLOCKED noise, which is exactly the population the
        write guard's own read excludes (``WHERE array::len(blocked_by) > 0``).  This one
        seeds the population it INCLUDES: ``blocked_pair_count`` blockers and one dependent
        each, so the guard's filtered read genuinely grows.
        """
        from loremaster.tasks import TaskSpec

        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        ledger = TaskLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )
        try:
            await ledger.ensure_ready()
            noise_blockers = await ledger.create_many(
                [
                    TaskSpec(subject=f"noise blocker {index}", description=DESCRIPTION)
                    for index in range(blocked_pair_count)
                ],
                created_by=CREATOR,
            )
            await ledger.create_many(
                [
                    TaskSpec(
                        subject=f"noise dependent {index}",
                        description=DESCRIPTION,
                        blocked_by=[blocker],
                    )
                    for index, blocker in enumerate(noise_blockers)
                ],
                created_by=CREATOR,
            )
            blocker = await ledger.create_task(
                "a real blocker", DESCRIPTION, created_by=CREATOR
            )
            created: list[str] = []

            async def _run() -> None:
                created.extend(
                    await ledger.create_many(
                        [
                            TaskSpec(
                                subject=SUBJECT,
                                description=DESCRIPTION,
                                blocked_by=[blocker],
                            )
                        ],
                        created_by=CREATOR,
                    )
                )

            traffic = await measure_store_traffic(ledger, _run)
            return traffic, len(created)
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_KNOWN_BOUND_the_write_paths_rows_READ_DOES_grow_with_the_BLOCKED_population(
        self,
    ) -> None:
        """**GREEN at ``b8607c4``, and it asserts a MISS.**  ⛔ **#253's residue on the write
        path, PINNED rather than left for the next auditor to rediscover from an incident.**

        ``CLAUDE.md`` § *WHEN YOU CANNOT CLOSE A HOLE, PIN IT*: *"an unpinned known limitation
        is indistinguishable from an unknown one."*  Its sibling leg below measures growth
        against the UNBLOCKED population — which is precisely the population the guard's own
        ``WHERE array::len(blocked_by) > 0`` excludes — so nothing in this contract had ever
        varied the population the read actually returns.  MEASURED here and independently by
        the delta adversary (§PINS-4): the guard reads ~one row per DEPENDENCY-BEARING row in
        the ledger, whatever the new dependency is.

        **THIS PIN GOES RED THE DAY SOMEONE CLOSES THE HOLE, and that is the point.**  If you
        closed it deliberately, DELETE this pin and say so in your wave report — do not
        weaken it, and do not widen its sibling to cover this axis without a ruling.

        ⚠ **WHY IT IS A BOUND AND NOT SIMPLY A DEFECT — the design fork is REAL and is
        escalated, not settled here** (`REPORT-contractfix-04b1-r6.md` §ESC-1).  R7's rider
        forces the acyclicity guard to walk the ``blocked_by`` COLUMN client-side, because the
        closing dependency of a cycle CANNOT carry an edge (``ENFORCED`` rejects a ``RELATE``
        to a task that does not exist yet), so an engine traversal returns *"acyclic"*; and R7
        puts that walk inside ONE round trip.  Whether a bound exists that satisfies both — an
        ancestor-closure seed, say — is a DESIGN question, and a builder must not be handed
        *"invent the general form"*.
        **NAMED RE-OPEN TRIGGER:** the first ledger whose dependency-bearing population makes
        a ``create_many`` measurably slow, or any ruling that supersedes R7's rider.
        """
        small, small_created = await self._blocked_noise_traffic(UNRELATED_TASK_COUNT_SMALL)
        large, large_created = await self._blocked_noise_traffic(UNRELATED_TASK_COUNT_LARGE)
        assert small_created == large_created == 1, (
            f"the two measurements created {small_created} and {large_created} tasks; each "
            f"must create the ONE item, or the comparison is between two different amounts "
            f"of work"
        )
        assert small.rows > 0, (
            f"the instrument counted ZERO rows for a create that landed a task — it is not "
            f"observing this call path, so this bound is unmeasured rather than confirmed: "
            f"{small}"
        )
        assert large.rows > small.rows, (
            f"a create_many naming ONE blocker read {small.rows} rows against "
            f"{UNRELATED_TASK_COUNT_SMALL} unrelated BLOCKED pairs and {large.rows} against "
            f"{UNRELATED_TASK_COUNT_LARGE} — it did NOT grow, so the known bound this pin "
            f"asserts no longer exists. ⚠ THIS IS A KNOWN BOUND (see this test's docstring "
            f"and §ESC-1 of the r6 contract wave): the write-time acyclicity guard reads "
            f"every dependency-bearing row on every create. If you CLOSED it deliberately, "
            f"DELETE this pin and say so in your wave report — a bound that is pinned is a "
            f"bound the next engineer meets deliberately, and one that is silently fixed "
            f"leaves a pin nobody can interpret. small={small.statements} "
            f"large={large.statements}"
        )

    async def test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_DEPENDENCY_FREE_population(
        self,
    ) -> None:
        """**GREEN at ``bfea1f8``, and GREEN after — the one leg of this class that is not
        RED today.**  DERIVED by running it, never asserted: at ``bfea1f8`` the ledger's
        ``create_many`` performs no persisted-id walk at all (the only cycle check in the tree
        is ``server.py``'s batch-local one), so there is no read to grow.  It is a guard on a
        hazard the FIX INTRODUCES — the delete/replace law's dual: *tests written for a NEW
        design certify only the new world*, so a pin that only ever went green after the
        rewrite would never have caught this.

        ⛔ **#253's OWN DEFECT, REACHABLE ON THE WRITE PATH** — and nothing measured it.

        R7's rider forces the acyclicity guard to walk the ``blocked_by`` COLUMN CLIENT-SIDE,
        and R7 puts that walk inside ONE round trip.  **One round trip says nothing about how
        many ROWS it reads.**  A walk seeded with ``SELECT * FROM task`` — one statement, one
        trip, the whole ledger — satisfies every pin this contract had: its sibling above
        measures ROUND TRIPS and says in its own docstring *"rows are deliberately NOT
        asserted"* (correct for its question, blind to this one), and
        :class:`TestTheReadIsBOUNDEDByTheCallersFilter` measures ``query_tasks`` only.
        MEASURED: dropping the dependency-bearing filter from the guard's single read took
        rows-read from 10 to 65 as the ledger grew from 5 to 60 unrelated tasks, with the
        whole contract green — **finding #253 reintroduced on the write path, invisible.**

        THE DISCRIMINATION IS A GROWTH COMPARISON, never a threshold, for the reason its
        sibling states: a magic number is a fixture value a builder can tune until it passes.

        ⚠⚠ **RENAMED 2026-07-28 (wave r6) — IT USED TO PROMISE "the size of the LEDGER" AND
        MEASURE SOMETHING NARROWER, WHICH IS THE FALSE-GATE CLASS THIS REPO ALREADY NAMES.**
        ``_seed_unrelated_tasks`` mints UNBLOCKED rows, and the guard's read is filtered
        ``WHERE array::len(blocked_by) > 0`` — so the population this leg varies is exactly
        the one the read EXCLUDES.  The old name and the old failure message both claimed a
        ∀-ledger property the assertion cannot perform (*"a failure message that promises a
        check the assertion does not perform is a false gate"*), and the residue is real:
        against BLOCKED noise the read DOES grow, which is now asserted as a KNOWN BOUND by
        :meth:`test_KNOWN_BOUND_the_write_paths_rows_READ_DOES_grow_with_the_BLOCKED_population`.
        The two legs together are the honest statement of what this build does.

        ⚠ **STATED SCOPE:** the guard legitimately reads more rows for a DEEPER dependency
        chain — that is the answer's cost, not the ledger's — so the chain is held constant at
        one hop, and this leg varies ONLY the dependency-free population.
        """
        small, small_created = await self._create_many_traffic(UNRELATED_TASK_COUNT_SMALL)
        large, large_created = await self._create_many_traffic(UNRELATED_TASK_COUNT_LARGE)
        assert small_created == large_created == 1, (
            f"the two measurements created {small_created} and {large_created} tasks; each "
            f"must create the ONE item. Either the fixture drifted — a rows-read comparison "
            f"between two different amounts of work measures nothing — or the create wrote "
            f"nothing at all, and 'the row count did not grow' is trivially true"
        )
        assert small.rows > 0, (
            f"the instrument counted ZERO rows for a create that landed a task — it is not "
            f"observing this call path, so its 'did not grow' verdict is worthless: {small}"
        )
        assert large.rows == small.rows, (
            f"a create_many naming ONE blocker read {small.rows} rows against a ledger of "
            f"{UNRELATED_TASK_COUNT_SMALL} unrelated DEPENDENCY-FREE tasks and {large.rows} "
            f"against one of {UNRELATED_TASK_COUNT_LARGE}. The work is identical at both "
            f"sizes, so the write path is scaling with rows it does not even need to look "
            f"at — a walk seeded with the whole task table (#253's shape, on the WRITE "
            f"side). The acyclicity walk must at minimum be filtered to the "
            f"dependency-BEARING rows. ⚠ This assertion measures the DEPENDENCY-FREE "
            f"population ONLY; growth with the dependency-BEARING population is a separate, "
            f"currently-OPEN bound asserted by "
            f"test_KNOWN_BOUND_the_write_paths_rows_READ_DOES_grow_with_the_BLOCKED_population. "
            f"⚠ Do NOT fix this by moving the walk onto an ENGINE traversal of the blocks "
            f"edge: the closing dependency of a cycle cannot carry an edge (see this class's "
            f"docstring), so an engine detector returns 'acyclic'. small={small.statements} "
            f"large={large.statements}"
        )
        assert large.rows < UNRELATED_TASK_COUNT_LARGE, (
            f"the write path touched {large.rows} rows, at least as many as the "
            f"{UNRELATED_TASK_COUNT_LARGE} unrelated dependency-free tasks that have nothing "
            f"to do with the dependency it was asked to check: {large.statements}"
        )


class TestTheCyclePolicyHasONEImplementation:
    """RED today.  ⛔ **Operator ruling R6 (2026-07-28) — and the ONLY pins in this contract
    that observe what a ``lore_tasks`` CALLER is served.**

    MEASURED at ``faf035d`` through the real dispatcher (:func:`_tool_seam`): a batch whose
    keys form a cycle is refused by ``AppContext._find_key_cycle`` with a bare
    ``ValueError`` and its own sentence —

        ``create_many items contain a blocked_by cycle among batch keys: a -> b -> a — a
        cyclic batch can never be claimed; break the cycle``

    — and it fires FIRST, before the ledger sees the batch at all.  So after 04b-1 there
    would be TWO cycle detectors, TWO sentences and TWO error classes, and every cycle pin
    in this file (all of which call the ledger directly) would observe NEITHER of the two an
    agent actually receives.  That is #102's shape, and L3 already ruled it for the
    EXISTENCE policy; R6 rules the same for the CYCLE policy.

    What R6 requires, and what each pin below holds it to:

    * **ONE detection ALGORITHM**, ledger-owned — proven by MUTATION, never by inspection
      (routing is not sharing): neutralise it and BOTH shapes must stop being refused.
    * **ONE error CLASS** — derived from the raised VALUES, so the pin cannot be satisfied
      by a name.
    * **ONE sentence SHAPE, two vocabularies** — batch KEYS and persisted IDS name different
      things, which R6 explicitly permits; the shape is proven by replacing the shared
      formatter and requiring BOTH served sentences to change.
    """

    @staticmethod
    def _cycle_specs(first_key: str, second_key: str) -> list[dict[str, Any]]:
        """A two-item ``lore_tasks create_many`` batch whose KEYS reference each other."""
        return [
            {
                "key": first_key,
                "subject": "a waits on b",
                "description": DESCRIPTION,
                "blocked_by": [second_key],
            },
            {
                "key": second_key,
                "subject": "b waits on a",
                "description": DESCRIPTION,
                "blocked_by": [first_key],
            },
        ]

    @staticmethod
    async def _ledger_cycle_error(ledger: TaskLedger) -> BaseException:
        """The error the LEDGER raises for a cycle — read off a real refusal, never named.

        A self-loop through ``create_many`` is the smallest cycle the ledger owns, and
        :class:`TestCreateRefusesToFormACycle` already pins that it is refused; this reads
        the resulting VALUE so the tool-seam pins can compare classes without either side
        naming one.
        """
        from loremaster.tasks import TaskSpec

        self_id = f"self_{uuid.uuid4().hex}"
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_many(
                [TaskSpec(subject="loop", description=DESCRIPTION, blocked_by=[self_id])],
                created_by=CREATOR,
                ids=[self_id],
            )
        return caught.value

    async def test_a_BATCH_KEY_cycle_at_the_TOOL_SEAM_raises_the_LEDGERS_cycle_CLASS(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The refusal an AGENT is served for the cycle shape the DISPATCHER catches."""
        ledger, _env, _blocker = task_ledger
        expected = type(await self._ledger_cycle_error(ledger))
        with pytest.raises(Exception) as caught:  # noqa: B017 - the CLASS is the assertion
            await _tool_seam(ledger).tasks(
                action="create_many",
                created_by=CREATOR,
                items=self._cycle_specs("wave-7-charter", "wave-7-rollout"),
            )
        assert type(caught.value) is expected, (
            f"a cyclic batch at the lore_tasks seam raised {type(caught.value).__name__} "
            f"while the ledger raises {expected.__name__} for a cycle. R6: ONE error class "
            f"— today the dispatcher owns a second cycle policy with a bare ValueError, so "
            f"a caller cannot write one except for 'this batch has a loop'. The two "
            f"VOCABULARIES may differ (batch keys are not task ids); the CLASS may not"
        )
        assert "wave-7-charter" in str(caught.value) and "wave-7-rollout" in str(caught.value), (
            f"the refusal must NAME every member of the cycle — a caller cannot break a "
            f"loop it cannot see: {str(caught.value)!r}"
        )

    async def test_a_PERSISTED_ID_cycle_is_UNREACHABLE_at_the_TOOL_SEAM_by_construction(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **A KNOWN BOUND, PINNED** (repo law: *"when you cannot close a hole, pin
        it"*) — and it is the bound that decides how much R6 can be asked for.

        The ledger's persisted-id cycle guard
        (:meth:`TestCreateRefusesToFormACycle.test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED`)
        needs a caller-supplied id: a cycle closes only when an EXISTING row's
        ``blocked_by`` already names the id about to be created.  ``AppContext._create_many``
        **pre-mints every id itself** (``uuid4().hex`` per item), so a ``lore_tasks`` caller
        cannot name the id it is about to create, and that shape is UNREACHABLE through this
        seam.  MEASURED, not assumed — this pin drives the real dispatcher and watches the
        create LAND.

        ⚠ **Consequence for R6, stated so it is not mistaken for a gap:** the only cycle a
        tool caller can actually form is a BATCH-KEY cycle, which is why that is the shape
        the seam pin above uses.  The ledger's persisted-id vocabulary is reachable by a
        DIRECT ledger caller only.

        ⚠ **NAMED RE-OPEN TRIGGER:** the day ``lore_tasks`` accepts caller-supplied ids (or
        any other verb lets a caller name a not-yet-created task), this pin goes RED — and
        that reddening is the signal that the persisted-cycle refusal now needs its own
        tool-seam pin.  **If you opened that door deliberately, delete this pin and write
        the seam pin it is standing in for.**
        """
        ledger, env, _blocker = task_ledger
        setup = await connect_admin(env)
        try:
            chain = await _seed_chain(setup, 3)
            caller_named_id = f"closer_{uuid.uuid4().hex}"
            await run(
                setup,
                f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
                {"id": chain[0], "blocked_by": [caller_named_id]},
            )
        finally:
            await setup.close()
        before = await _task_row_count(ledger)
        rendered = str(
            await _tool_seam(ledger).tasks(
                action="create_many",
                created_by=CREATOR,
                items=[
                    {
                        "key": caller_named_id,
                        "subject": "would close the loop IF the caller could name its id",
                        "description": DESCRIPTION,
                        "blocked_by": [chain[-1]],
                    }
                ],
            )
        )
        assert await _task_row_count(ledger) == before + 1, (
            f"the create did not land, so this pin observed something other than the bound "
            f"it describes: {rendered!r}"
        )
        # ⚠ The check is on the served ID SET, never on the rendered text: the render
        # legitimately ECHOES the caller's key (`key closer_…`), so a substring check
        # against it fires on an echo and promises a check it does not perform — a FALSE
        # GATE. (Measured on the reference build, which is how this line came to exist.)
        served_ids = {task.id for task in await ledger.query_tasks()}
        assert caller_named_id not in served_ids, (
            f"a task now carries the CALLER-SUPPLIED id {caller_named_id!r}. The dispatcher "
            f"has stopped pre-minting, which closes the persisted-id cycle this seam was "
            f"believed unable to reach — this bound is void and the ledger's persisted-cycle "
            f"refusal now needs a tool-seam pin of its own. See the re-open trigger above"
        )

    async def test_MUTATION_neutralising_the_SHARED_detector_lets_BOTH_shapes_through(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **PROVE SHARING BY MUTATION — the only test that tells DRY from looks-DRY.**

        The stub is an ACCEPT-EVERYTHING (*"no cycle here"*), never a raising sentinel: 04a
        MEASURED that a sentinel proves only that a function is CALLED, never that it
        DECIDES, and a build where both modules call a shared function and then re-decide
        underneath it — ROUTING, not SHARING — passed 04a's whole contract.

        Substituted in BOTH consuming namespaces at once, then BOTH cycle shapes must be
        ACCEPTED.  A module keeping a private copy keeps refusing, and reddens here.

        ⚠ ``raising=True``: a module that does not hold the detector under
        :data:`SHARED_CYCLE_DETECTOR_ATTR` reddens rather than silently skipping.
        """
        ledger, _env, _blocker = task_ledger
        import importlib

        for module_name in (SHARED_CYCLE_DETECTOR_MODULE, TOOL_SEAM_MODULE):
            monkeypatch.setattr(
                importlib.import_module(module_name),
                SHARED_CYCLE_DETECTOR_ATTR,
                lambda *_args, **_kwargs: None,
                raising=True,
            )

        before = await _task_row_count(ledger)
        await _tool_seam(ledger).tasks(
            action="create_many",
            created_by=CREATOR,
            items=self._cycle_specs("wave-8-charter", "wave-8-rollout"),
        )
        assert await _task_row_count(ledger) == before + 2, (
            "with the SHARED cycle detector neutralised in both modules, a cyclic batch was "
            "still refused — so at least one of them is deciding acyclicity underneath the "
            "shared call. Routing is not sharing (#102)"
        )

        from loremaster.tasks import TaskSpec

        self_id = f"self_{uuid.uuid4().hex}"
        await ledger.create_many(
            [TaskSpec(subject="a self loop", description=DESCRIPTION, blocked_by=[self_id])],
            created_by=CREATOR,
            ids=[self_id],
        )
        assert await _task_row_count(ledger) == before + 3, (
            "with the shared detector neutralised, the LEDGER still refused a self-blocking "
            "task — its write-time guard keeps a private detector"
        )

    async def test_MUTATION_replacing_the_shared_FORMATTER_changes_BOTH_refusals(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ R6's *"one refusal sentence shape"*, as a runnable pin.

        ONE substitution observed from TWO call sites in ONE run — the instrument L3's
        existence proof already uses, applied to the cycle policy.  The sentinel is unlike
        either real sentence, so a build that CONCATENATES the shared text with its own
        cannot pass by accident.

        ⚠ This pins the SHAPE, not the WORDS: R6 permits the two vocabularies to differ
        (batch-local temp keys and persisted ids name different things), which is exactly
        why the shared thing is a formatter taking the noun rather than a constant string.
        """
        ledger, _env, _blocker = task_ledger
        import importlib

        sentinel = "SENTINEL-SHARED-CYCLE-REFUSAL-04b1"
        monkeypatch.setattr(
            importlib.import_module(SHARED_CYCLE_DETECTOR_MODULE),
            SHARED_CYCLE_FORMATTER_ATTR,
            lambda *_args, **_kwargs: sentinel,
            raising=True,
        )

        with pytest.raises(Exception) as seam_side:  # noqa: B017 - the TEXT is the assertion
            await _tool_seam(ledger).tasks(
                action="create_many",
                created_by=CREATOR,
                items=self._cycle_specs("wave-9-charter", "wave-9-rollout"),
            )
        assert str(seam_side.value) == sentinel, (
            f"the TOOL-SEAM cycle refusal did not route through the shared formatter — "
            f"server.py keeps its own sentence, which is copy #2 of a served surface: "
            f"{str(seam_side.value)!r}"
        )

        ledger_side = await self._ledger_cycle_error(ledger)
        assert str(ledger_side) == sentinel, (
            f"the LEDGER's cycle refusal did not route through the shared formatter: "
            f"{str(ledger_side)!r}"
        )


class TestASupersededBlockerIsNotASilentBlackHole:
    """RED at ``5a2dca9``.  ⛔ **Operator ruling R10(ii), 2026-07-28 — MP-5 is now RULED,
    and the ruling is NARROWER than the outcome pin this class used to carry.**

    Operator ruling **R3** changes a live verb on one justification: *"a loud refusal
    replaces a silent black hole"*, the black hole being *"a task created and then
    **unclaimable forever, silently**"*.  This contract guarded TWO causes — a phantom
    blocker and a cycle.  The adversary MEASURED a THIRD, on a known-correct build
    (``REPORT-adversary-04b1.md`` §B-3, reproduced independently at ``faf035d``):

        blocker superseded; its status is still 'open'; TERMINAL is {done, wontfix}
        create_task(blocked_by=[<superseded>]) -> ACCEPTED
        claim_task(waiter) -> claimed=False
          freed via transition->done?    NO  — IllegalTransitionError: task … is superseded
          freed via transition->wontfix? NO  — IllegalTransitionError: task … is superseded
          freed via supersede?           NO  — IllegalTransitionError: already superseded

    Existence passes (the row is right there).  No cycle.  Nothing refuses.  **The exact
    outcome R3 exists to abolish, through a door with a different cause** — THE QUANTIFIER
    LAW verbatim: the invariant was written over the failure modes already debugged instead
    of over the OUTCOME.

    ⚠⚠ **WHY THE OLD OUTCOME PIN IS GONE AND MUST NOT COME BACK.**  Until R10 this class
    held ONE pin written over the outcome — *refused at create* **or** *the blocker
    escapable* — deliberately satisfied by either of two readings, because neither had been
    ruled.  **R10 ruled one of them ILLEGAL**, so that pin now admits a build the operator
    rejected, verbatim: *"REJECTED: treating ``superseded`` as terminal in the CAS —
    supersession means the work MOVED, not finished, so it would silently un-block
    dependents while the successor is open: the INVERSE black hole, quieter and worse."*
    A contract that still passes a build its ruling forbids is not a looser contract, it is
    a broken one — *tests written before a semantic change certify the OLD world*
    (``CLAUDE.md``).  The forbidden reading is now pinned SHUT by
    :meth:`test_a_DEPENDENT_created_BEFORE_the_supersede_is_NOT_silently_unblocked`.

    **WHAT IS RULED, and therefore what is pinned:** the blocker pre-check REFUSES a
    superseded blocker and NAMES ITS SUCCESSOR, on both create verbs, before any row is
    written; and a dependency on a superseded task, however it arose, is never dissolved.
    R10(iii) — the ``supersede_task`` dependants warning and the claim render — is 04b-2's
    surface and is NOT pinned here.
    """

    @staticmethod
    async def _superseded_blocker(ledger: TaskLedger) -> tuple[str, str]:
        """A ``(blocker, successor)`` pair where ``blocker`` has been superseded.

        Built through the PUBLIC verbs only — this is a state the fleet reaches every time
        someone reframes a work item, not a contrivance a raw seed had to manufacture.
        """
        blocker = await ledger.create_task(
            "a blocker that will be reframed", DESCRIPTION, created_by=CREATOR
        )
        successor = await ledger.supersede_task(
            blocker,
            subject="the reframed work item",
            description=DESCRIPTION,
            created_by=CREATOR,
        )
        assert successor != blocker, (
            "supersede_task returned the predecessor's own id, so this fixture has no "
            "successor to name and every leg below would assert against one id twice"
        )
        return blocker, successor

    async def test_a_create_blocked_on_a_SUPERSEDED_task_is_REFUSED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ R10(ii)'s first clause.  *"A ``blocked_by`` naming a superseded task is NEVER
        legitimate: the CAS can never resolve it — the refusal is correct in all cases."*
        """
        ledger, _env, _blocker = task_ledger
        blocker, _successor = await self._superseded_blocker(ledger)
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_task(SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR)
        assert blocker in str(caught.value), (
            f"the refusal must NAME the superseded blocker the caller supplied, verbatim, "
            f"or the caller cannot tell which of its blocked_by entries to edit: "
            f"{str(caught.value)!r}"
        )

    async def test_the_refusal_NAMES_THE_SUCCESSOR_and_says_what_to_do_INSTEAD(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **The half that makes the refusal a RECOVERY rather than a rejection.**

        R10(ii)'s whole cost argument is that the successor is already in hand: *"the check
        already reads the blocker rows in one grouped query; projecting
        ``status``/``superseded_by`` alongside existence is free."*  A refusal that names
        only the bad id makes an agent pay a ``get_task`` round trip to learn what to block
        on instead — which is the difference between a one-edit fix and a reconnaissance
        trip, on the SERVED surface an agent learns the contract from.

        The clause is asserted BY VALUE (:func:`_served_superseded_clause`) rather than as
        *"the successor id appears somewhere"*: a message that happened to contain the
        successor for an unrelated reason would pass a membership check, and F3 measured
        what substring pins cost on exactly this surface.
        """
        ledger, _env, _blocker = task_ledger
        blocker, successor = await self._superseded_blocker(ledger)
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_task(SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR)
        message = str(caught.value)
        clause = _served_superseded_clause(blocker, successor)
        assert clause in message, (
            f"the served refusal does not carry ruling R10(ii)'s clause verbatim.\n"
            f"  want (as a substring): {clause!r}\n"
            f"  got the whole message: {message!r}\n"
            f"See _served_superseded_clause's docstring: this is pinned as a CLAUSE and not "
            f"as the whole sentence deliberately, because R10 does not say which it is — so "
            f"a build under EITHER reading passes this leg. If you changed the wording on "
            f"purpose, change the spec function in the same commit and say so"
        )

    async def test_the_refusal_ALSO_states_that_NOTHING_was_created(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **RIDER-B's property, applied to the second refusal cause.**

        RIDER-B ruled the no-write fact must be SERVED and not merely TRUE, and its
        justification names no particular cause: *"an agent reading only 'refused' does not
        know whether a partial batch landed, so it must pay a reconnaissance read before it
        dare resend."*  That is as true of a superseded blocker as of a phantom one — THE
        QUANTIFIER LAW: do not condition a served property on the one cause that prompted it.

        Its own leg, with its own message, because a by-value diff of a long sentence does
        not say WHICH clause went missing.
        """
        ledger, _env, _blocker = task_ledger
        blocker, _successor = await self._superseded_blocker(ledger)
        before = await _task_row_count(ledger)
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_task(SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR)
        assert "NOTHING was created" in str(caught.value), (
            f"the superseded-blocker refusal does not state that nothing was written, while "
            f"the phantom-blocker refusal beside it does (RIDER-B). Two refusals from ONE "
            f"pre-check that teach different amounts is the copy-#2 shape on a served "
            f"surface: {str(caught.value)!r}"
        )
        assert await _task_row_count(ledger) == before, (
            "…and the sentence must be TRUE: the refused create left a row behind"
        )

    async def test_a_refused_create_writes_NO_task_row(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """BEFORE the write, not rolled back after it — the MP-3 discriminator: a build that
        creates the row and compensates leaves the count changed at some point, and leaves
        an id minted that the caller was told never existed.
        """
        ledger, _env, _blocker = task_ledger
        blocker, _successor = await self._superseded_blocker(ledger)
        before = await _task_row_count(ledger)
        with pytest.raises(TaskLedgerError):
            await ledger.create_task(SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR)
        assert await _task_row_count(ledger) == before

    async def test_create_many_ALSO_refuses_a_SUPERSEDED_blocker_and_writes_NO_ROWS(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """Pinned separately from ``create_task`` for the reason the phantom twin is: the
        scout's explicit warning that the two verbs have DIFFERENT transaction shapes
        (``create_task`` is a bare ``_query``, ``create_many`` is transactional), so a fix
        may reach only one of them.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, real_blocker = task_ledger
        blocker, _successor = await self._superseded_blocker(ledger)
        before = await _task_row_count(ledger)
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_many(
                [
                    TaskSpec(
                        subject="item 0 waits on a live blocker",
                        description=DESCRIPTION,
                        blocked_by=[real_blocker],
                    ),
                    TaskSpec(
                        subject="item 1 waits on a REFRAMED blocker",
                        description=DESCRIPTION,
                        blocked_by=[blocker],
                    ),
                ],
                created_by=CREATOR,
            )
        assert blocker in str(caught.value), (
            f"create_many accepted or mis-reported a superseded blocker: {str(caught.value)!r}"
        )
        assert real_blocker not in str(caught.value), (
            f"the batch refusal named a blocker that is perfectly fine ({real_blocker!r}) — "
            f"it must name the offending entries and only those: {str(caught.value)!r}"
        )
        assert await _task_row_count(ledger) == before, (
            "the refused BATCH left rows behind — create_many is all-or-nothing"
        )

    async def test_a_DEPENDENT_created_BEFORE_the_supersede_is_NOT_silently_unblocked(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔⛔ **THE PIN THAT KILLS THE READING R10 REJECTED — and the one the pre-check
        structurally cannot cover.**

        Ruling R10, verbatim: *"REJECTED: treating ``superseded`` as terminal in the CAS —
        supersession means the work MOVED, not finished, so it would silently un-block
        dependents while the successor is open: the INVERSE black hole, quieter and worse."*

        The order of events here is the whole point, and it is ORDINARY: the dependent is
        created while the blocker is a perfectly good open task, and the blocker is
        superseded AFTERWARDS.  **No create-time pre-check can ever see this** — the
        quantifier law, which R10(iii) names explicitly (*"supersession can happen AFTER
        dependents exist — (ii) alone cannot catch it"*).

        GREEN at ``5a2dca9`` and therefore a REMOVED-BEHAVIOUR guard (delete/replace law):
        the measured wrong build it goes RED on is the adversary's reading (b) — resolve
        ``superseded_by IS NOT NONE`` as terminal — which passes every other leg in this
        class and every leg in ``TestTheBoundedReadKeepsTheClaimAgreement``, because none of
        them ever produces a dependent whose blocker was superseded after birth.

        BOTH mechanisms are asserted, not just the claim: an un-blocking build that reached
        only ``query_tasks`` would serve the fleet a task it is told to claim and cannot,
        and one that reached only the CAS would hide a claimable task.  Requirement 2(d)
        says they may never disagree; this is a shape where a plausible fix makes them.
        """
        ledger, _env, _blocker = task_ledger
        blocker = await ledger.create_task(
            "a blocker that is fine when the dependent is born", DESCRIPTION, created_by=CREATOR
        )
        dependent = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
        )
        successor = await ledger.supersede_task(
            blocker,
            subject="the reframed work item",
            description=DESCRIPTION,
            created_by=CREATOR,
        )

        unblocked = {task.id for task in await ledger.query_tasks(blocked=False)}
        assert dependent not in unblocked, (
            f"query_tasks(blocked=False) served task {dependent!r} as claimable after its "
            f"only blocker {blocker!r} was SUPERSEDED (successor {successor!r}). Ruling R10 "
            f"REJECTED exactly this: supersession means the work MOVED, not that it "
            f"finished, so dissolving the block un-blocks a dependent while the successor "
            f"is still open — the INVERSE black hole, quieter and worse than the one this "
            f"packet closes. The successor is the recovery, and naming it is 04b-2's render"
        )
        claim = await ledger.claim_task(dependent, ACTOR)
        assert not claim.claimed, (
            f"the claim CAS granted task {dependent!r} whose only blocker {blocker!r} is "
            f"superseded and not terminal. This is the same rejected reading as the leg "
            f"above, reached through the OTHER mechanism — and if only one of the two "
            f"changed, the served partition and the claim now disagree (requirement 2(d))"
        )

    async def test_POSITIVE_CONTROL_a_create_blocked_on_a_LIVE_blocker_is_ACCEPTED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """Without this, every refusal leg above passes on a build that refuses everything.

        The only variable against :meth:`test_a_create_blocked_on_a_SUPERSEDED_task_is_REFUSED`
        is the supersession — same verbs, same fixture shape, same one blocker — so a build
        that refuses for any OTHER reason reddens here rather than passing as if correct.
        """
        ledger, _env, _blocker = task_ledger
        live_blocker = await ledger.create_task(
            "a blocker that will NOT be reframed", DESCRIPTION, created_by=CREATOR
        )
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[live_blocker], created_by=CREATOR
        )
        await _assert_mirror(ledger, task_id, where="positive control, one live blocker")

    async def test_POSITIVE_CONTROL_a_waiter_on_a_NORMAL_blocker_IS_freed_by_done(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The second control, on the OTHER axis: a build where NO waiter is ever claimable
        satisfies every "still blocked" assertion in this class.  Same fixture shape, same
        verbs, an ordinary blocker driven to a terminal status.
        """
        ledger, _env, _blocker = task_ledger
        blocker = await ledger.create_task("an ordinary blocker", DESCRIPTION, created_by=CREATOR)
        waiter = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
        )
        assert not (await ledger.claim_task(waiter, ACTOR)).claimed, (
            "the waiter was claimable while its blocker was still open — the fixture is not "
            "producing a blocked task, so it can observe nothing about being freed"
        )
        await _drive_to(ledger, blocker, STATUS_DONE)
        assert (await ledger.claim_task(waiter, ACTOR)).claimed, (
            "a waiter whose ONLY blocker reached 'done' was still unclaimable — a defect "
            "worse and more general than the superseded-blocker door beside it"
        )


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

    ⚠⚠ **AND THE PAIR MUST BE RUN ON THE DEFAULT PATH TOO — the original pair was not, and
    a wrong build passed the WHOLE contract 80/80 because of it** (adversary B-1 / MP-1,
    closed 2026-07-28).  ``max_depth`` appeared in this file exactly twice, both times as
    the literal ``2``: a 100% parameter-value monoculture on a parameter the code branches
    on.  The measured survivor computed ``truncated`` only when ``max_depth`` was supplied
    EXPLICITLY and hard-coded ``False`` on the defaulted path — the path 04b-2's *"renders
    its critical path"* calls — so it served 32 of 34 upstream blockers as a WHOLE critical
    path, silently.  The default-path legs below close it, and they include the exact
    boundary (a chain of EXACTLY the bound, which must report ``truncated=False``) because
    ``truncated = len(ids) >= max_depth`` is the next plausible wrong build and the two
    other legs cannot tell it from correct.

    Escalation E-3 records the rejected alternative (RAISE at the bound) and why.
    """

    @staticmethod
    def _default_bound() -> int:
        """The build's own default depth bound, read at CALL time and failing CLOSED."""
        import loremaster.tasks

        bound = getattr(loremaster.tasks, MAX_DEPTH_CONSTANT, None)
        assert isinstance(bound, int), (
            f"loremaster.tasks must export {MAX_DEPTH_CONSTANT} (see "
            f"test_the_default_bound_is_a_SMALL_EXPLICIT_constant_inside_the_engine_ceiling)"
        )
        return bound

    @staticmethod
    async def _read_at_the_default_bound(
        ledger: TaskLedger, env: SurrealEnv, upstream_depth: int
    ) -> Any:
        """Seed a chain with ``upstream_depth`` blockers above its tail, read it UNBOUNDED.

        ⚠ The call passes **no** ``max_depth`` — that omission is the entire point of these
        legs.  Cost scales with the build's own default: at ``TASK_BLOCKER_MAX_DEPTH = 32``
        the deepest leg seeds 35 rows and 34 edges, which is the price of covering the path
        every caller actually uses.
        """
        setup = await connect_admin(env)
        try:
            chain = await _seed_chain(setup, upstream_depth + 1)
        finally:
            await setup.close()
        return chain, await _transitive_blockers(ledger, chain[-1])

    async def test_a_chain_DEEPER_than_the_DEFAULT_bound_reports_TRUNCATED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ The leg the ``truncated_explicit`` wrong build could not survive."""
        ledger, env, _blocker = task_ledger
        bound = self._default_bound()
        _chain, result = await self._read_at_the_default_bound(ledger, env, bound + 2)
        assert result.truncated is True, (
            f"a chain with {bound + 2} upstream blockers, read at the DEFAULT bound of "
            f"{bound}, reported truncated=False. The engine truncates SILENTLY at its bound "
            f"(probe §5.3), so a build that computes `truncated` only when max_depth is "
            f"supplied EXPLICITLY serves a short critical path as a complete one on the "
            f"path every caller uses — measured, and it passed this whole contract before "
            f"this leg existed (adversary B-1). got ids={len(result.ids)}"
        )
        assert len(result.ids) == bound, (
            f"a truncated read must still serve exactly the bound's worth of nodes: got "
            f"{len(result.ids)}, expected {bound}"
        )

    async def test_a_chain_EXACTLY_at_the_DEFAULT_bound_reports_truncated_FALSE(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **THE BOUNDARY — cap, not cap±1**, and the only leg that kills
        ``truncated = len(ids) >= max_depth``.

        A chain with EXACTLY ``TASK_BLOCKER_MAX_DEPTH`` upstream blockers is COMPLETE at the
        default bound: every node fits, nothing was cut, and a caller must be told so.  A
        build that infers truncation from a full result set answers ``True`` here and is
        indistinguishable from correct on both neighbouring legs.
        """
        ledger, env, _blocker = task_ledger
        bound = self._default_bound()
        chain, result = await self._read_at_the_default_bound(ledger, env, bound)
        assert len(result.ids) == bound, (
            f"the read served {len(result.ids)} of {bound} upstream blockers on a chain that "
            f"fits the bound exactly"
        )
        assert result.truncated is False, (
            f"a chain of EXACTLY {bound} upstream blockers, read at the default bound of "
            f"{bound}, reported truncated=True. Nothing was cut — every node is in the "
            f"answer. A build inferring truncation from `len(ids) >= max_depth` cannot tell "
            f"a complete answer from a cut one at the boundary, and tells every caller with "
            f"a full-depth graph that its critical path is incomplete. ids={len(result.ids)} "
            f"deepest={chain[0]!r}"
        )

    async def test_a_chain_WELL_WITHIN_the_DEFAULT_bound_reports_truncated_FALSE(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The pair's other half on the default path: a build hard-coding ``True`` dies."""
        ledger, env, _blocker = task_ledger
        chain, result = await self._read_at_the_default_bound(ledger, env, 2)
        assert result.truncated is False
        assert set(result.ids) == {chain[0], chain[1]}, (
            f"a 2-deep chain read at the default bound must serve both blockers: "
            f"{sorted(result.ids)}"
        )

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


class TestTheResultIsSELFDESCRIBING:
    """RED today.  ⛔ **RIDER-D** (design sidecar §3, amendments A3-a and A3-b).

    E-3 pinned a typed result carrying ``truncated``.  A bare boolean is the right LEDGER
    surface but it **strands the render**: measured from the consumer side, *"32 ids under
    an unstated bound of 32 — I cannot tell whether truncation was on depth or on count,
    and that ambiguity alone forces a re-run."*  So the result carries the bound it
    ACTUALLY ran at, and a render can teach a concrete re-ask without importing or
    re-deriving the ledger's default (which drifts the day the default changes).

    ⚠⚠ **AND THE NEGATIVE, WHICH IS THE HALF WITH TEETH.**  The tail beyond a truncated
    closure is **genuinely uncountable without walking it** — the server does not know how
    many blockers lie past the bound.  This repo's house grammar for an elided remainder is
    ``+K more``, and reaching for it here **forces a builder to fabricate K**.  Both blind
    consults rated an invented count the WORST outcome on the table: *"a tool caught
    inventing one number is untrustworthy on all of them."*  That is a categorical trust
    loss, not a cosmetic one — so the field set is pinned as an EXACT SET (allowlist the
    safe; the set of names a fabricated count could wear is unbounded).

    The RENDER of this result is 04b-2's and is NOT pinned here; §3's rider states its
    required shape (*"more exist beyond (count unknown at this depth); re-run with
    max_depth=…"*) and 04b-2 owns it.
    """

    #: EXACTLY the fields the typed result may carry.  A name outside this set is either a
    #: fabricated count of the unknowable tail or a second spelling of one of these.
    ALLOWED_RESULT_FIELDS = frozenset({"ids", "truncated", "max_depth_used"})

    async def test_the_result_carries_the_bound_it_ACTUALLY_ran_at(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """A DISCRIMINATING PAIR on the one axis that matters: supplied vs defaulted.

        A build hard-coding the module default passes the defaulted leg and dies on the
        explicit one; a build echoing the caller's argument dies on the defaulted leg,
        where there is no argument to echo.
        """
        import loremaster.tasks

        ledger, env, _blocker = task_ledger
        setup = await connect_admin(env)
        try:
            chain = await _seed_chain(setup, 4)
        finally:
            await setup.close()
        default_bound = getattr(loremaster.tasks, MAX_DEPTH_CONSTANT)

        defaulted = await _transitive_blockers(ledger, chain[-1])
        assert defaulted.max_depth_used == default_bound, (
            f"a read with NO max_depth reported max_depth_used="
            f"{getattr(defaulted, 'max_depth_used', None)!r}, expected the module default "
            f"{default_bound}. A render cannot teach a re-ask against a bound it has to "
            f"re-derive, and its re-derivation drifts the day the default changes"
        )
        explicit = await _transitive_blockers(ledger, chain[-1], max_depth=2)
        assert explicit.max_depth_used == 2, (
            f"a read at max_depth=2 reported max_depth_used="
            f"{getattr(explicit, 'max_depth_used', None)!r}. The field is the bound the read "
            f"RAN at, not the default it would have used"
        )

    async def test_a_TRUNCATED_result_lets_the_caller_compute_its_own_RE_ASK(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The consumer-side property, stated as arithmetic the caller can do.

        With ``truncated`` AND ``max_depth_used`` AND the ids in hand, a render can say
        *"shown to depth N, re-run with max_depth=2N"* without a schema read.  With the
        boolean alone it cannot, which costs a full turn mid-chain.
        """
        ledger, env, _blocker = task_ledger
        setup = await connect_admin(env)
        try:
            chain = await _seed_chain(setup, 6)
        finally:
            await setup.close()
        result = await _transitive_blockers(ledger, chain[-1], max_depth=2)
        assert result.truncated is True
        assert result.max_depth_used == 2
        assert len(result.ids) == result.max_depth_used, (
            f"a truncated read served {len(result.ids)} ids at max_depth_used="
            f"{result.max_depth_used}. The two must agree, or a caller cannot tell "
            f"truncation-on-DEPTH from truncation-on-COUNT — the exact ambiguity that "
            f"forces a re-run (sidecar §3, A3-a)"
        )

    def test_the_result_type_carries_NO_field_that_would_COUNT_the_unknown_tail(self) -> None:
        """⛔ The negative, as an EXACT-SET pin over the model's own fields.

        Deny-by-default, for the reason CLAUDE.md's instrument lesson gives: the set of
        names a fabricated count could wear (``remaining``, ``total``, ``more``, ``beyond``,
        ``tail_count``, …) is unbounded, and every gate this repo has keyed on a forbidden
        list has been defeated by the name nobody listed.  The SAFE set is three names.
        """
        # ⚠ Reached by ``getattr`` on the MODULE, never a typed import: the type does not
        # exist yet, and a typed import is a MYPY ERROR today rather than a RED pin — a
        # contract that fails its own gate before a builder sees it. (Finding #133's
        # sibling reasoning: the module-level version of that mistake makes the whole file
        # uncollectable instead.)
        import loremaster.tasks

        result_type = getattr(loremaster.tasks, "TransitiveBlockers", None)
        assert result_type is not None, (
            "loremaster.tasks must export TransitiveBlockers — the typed result escalation "
            "E-3 pinned. See this file's _transitive_blockers handle for why this is a "
            "call-time lookup"
        )
        declared = set(result_type.model_fields)
        assert declared == self.ALLOWED_RESULT_FIELDS, (
            f"the transitive-read result's field set drifted.\n"
            f"  present but NOT allowed: {sorted(declared - self.ALLOWED_RESULT_FIELDS)}\n"
            f"  allowed but ABSENT:      {sorted(self.ALLOWED_RESULT_FIELDS - declared)}\n"
            f"⚠ A field counting what lies BEYOND the bound cannot be honest: the server "
            f"does not know, and finding out means the walk the bound exists to avoid. Both "
            f"blind consults rated an invented count the worst outcome available — a tool "
            f"caught inventing one number is untrustworthy on all of them. If you added a "
            f"legitimate field, add it here in a diff a reviewer can see."
        )

    def test_the_helpers_docstring_states_the_FLOOR_property(self) -> None:
        """⛔ **A3-b** — one sentence that converts an honest partial answer into a USABLE one.

        The ``+collect`` traversal is breadth-complete at depths ≤ the bound
        (proximity-ordered, deduplicated closure — probe §5.1, re-measured on the reverse
        arrow by adversary §X1), so a truncated result is a valid FLOOR: *"at least these
        must resolve first."*  Without that stated, a consumer cannot tell a usable floor
        from a partial set that is untrustworthy at every level — and an unusable answer is
        a route-around.

        ⚠⚠ **A SERVED-ENGLISH pin, AND ITS BOUND IS WORSE THAN "IT CANNOT CHECK THEY ARE
        TRUE" — SO THE BOUND IS STATED EXACTLY** (ESC-3, lead-ruled 2026-07-28: *accept the
        bound, but the disclosure must state the REAL failure mode*).  It checks that the
        token ``floor`` is PRESENT.  MEASURED: a docstring reading *"Ignores the
        ``blocked_by`` column entirely; a ``phantom`` entry IS included in this answer, which
        is a **floor**"* — **the exact INVERSE of the truth** — satisfies this pin and its
        sibling in :class:`TestTheScopeOfTheTransitiveReadIsSTATED`.  So the failure mode this
        pin admits is not SILENCE, it is **INVERSION**: a docstring asserting the OPPOSITE of
        the property passes.  A disclosure that misdescribes its own bound is the false-gate
        class this repo already names.

        Reading (ii) — a phrase-level assertion requiring the sentence carrying ``floor`` to
        also carry a negation — was **REJECTED** by the same ruling: it invents a requirement
        no ruling carries, and that is the C-DEF class this packet has already hit three
        times.  What makes the words TRUE is pinned separately by
        ``TestTheTransitiveBlockerRead``'s closure/dedup legs.
        """
        helper = getattr(TaskLedger, TRANSITIVE_BLOCKERS_ATTR, None)
        assert helper is not None, (
            f"TaskLedger.{TRANSITIVE_BLOCKERS_ATTR} does not exist — see this file's "
            f"_transitive_blockers handle"
        )
        docstring = (helper.__doc__ or "").lower()
        assert "floor" in docstring, (
            f"the transitive read's docstring does not state the FLOOR property. A "
            f"truncated closure IS complete at every depth it reached, so the ids served "
            f"are the blockers that must resolve FIRST — a consumer that cannot tell that "
            f"from an arbitrary sample cannot use a partial answer at all (sidecar §3, "
            f"A3-b). docstring={helper.__doc__!r}"
        )


class TestTheCREATEPathsCostIsSTATED:
    """RED today.  ⛔ **RIDER-C** (design sidecar §2 R2-d; adversary §P6b #6 / R-15).

    Ruling **E-4** states the send path's extra round trip as an ACCEPTED COST with a named
    re-open trigger.  The CREATE path takes the same kind of hit — 1 round trip becomes
    ``≥2``, plus the acyclicity walk — and **no ruling states it anywhere**.  That
    asymmetry is the finding: an unstated cost is a surprise the next engineer rediscovers
    from a latency graph; a stated one is a decision with a trigger attached.

    ⚠⚠ **THE NUMBER IS DERIVED FROM THE BEHAVIOUR, NOT RE-STATED BESIDE IT** (CLAUDE.md,
    finding #104: *"prose that describes behaviour must be DERIVED from the behaviour"*).
    The pin MEASURES the round trips a real create costs and requires the docstring's
    stated figure to match.  It does NOT choose the number — a contract that pinned "3"
    would forbid a correct 2-round-trip build; it pins that whatever the build costs, the
    docstring says so.
    """

    #: The section header the cost sentence lives under, mirroring ``Raises:``. A NAMED
    #: section rather than a free sentence so the pin reads a structure, not a phrasing.
    COST_SECTION = "Cost:"

    async def test_create_tasks_docstring_states_its_MEASURED_round_trip_cost(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        import re

        ledger, _env, first_blocker = task_ledger
        second_blocker = await ledger.create_task(
            "a second real blocker", DESCRIPTION, created_by=CREATOR
        )
        traffic = await measure_store_traffic(
            ledger,
            lambda: ledger.create_task(
                SUBJECT,
                DESCRIPTION,
                blocked_by=[first_blocker, second_blocker],
                created_by=CREATOR,
            ),
        )
        docstring = TaskLedger.create_task.__doc__ or ""
        assert self.COST_SECTION in docstring, (
            f"create_task's docstring has no {self.COST_SECTION!r} section. E-4 states the "
            f"send path's extra round trip as an ACCEPTED COST; this packet adds the same "
            f"kind of cost to the create path and states it nowhere (adversary R-15). "
            f"Measured here: {traffic.calls} round trips for a create with two blockers"
        )
        section = docstring.split(self.COST_SECTION, 1)[1]
        stated = re.search(r"(\d+)\s+round trip", section)
        assert stated is not None, (
            f"the {self.COST_SECTION!r} section states no round-trip count. A cost sentence "
            f"without a number is not a decision anyone can re-open: {section.strip()[:200]!r}"
        )
        assert int(stated.group(1)) == traffic.calls, (
            f"create_task's docstring says {stated.group(1)} round trips; a create with two "
            f"blockers MEASURED {traffic.calls} ({list(traffic.statements)}). Prose that "
            f"describes behaviour is DERIVED from it or it rots — and this one rots into a "
            f"latency surprise nobody can attribute"
        )

    @pytest.mark.parametrize("verb", ["create_task", "create_many"])
    def test_the_create_verbs_docstrings_declare_their_NEW_error_classes(
        self, verb: str
    ) -> None:
        """The #219 class, at its second and third sites in this packet (adversary R-14).

        Both verbs gain two error classes this packet invents.  The names are DERIVED from
        the ledger module rather than typed here, so a rename costs one edit in production
        and none in this contract.
        """
        import loremaster.tasks

        docstring = getattr(TaskLedger, verb).__doc__ or ""
        assert "Raises:" in docstring, (
            f"TaskLedger.{verb}'s docstring has no 'Raises:' section, and this packet gives "
            f"it two new ways to fail. A caller reading only the signature cannot know what "
            f"to catch (#219's class)"
        )
        for error_name in ("UnknownBlockerError", "TaskCycleError"):
            assert getattr(loremaster.tasks, error_name, None) is not None, (
                f"loremaster.tasks must export {error_name} — this contract's error-hierarchy "
                f"pins derive from the raised VALUES, but this documentation pin needs the "
                f"NAME the docstring is supposed to carry"
            )
            assert error_name in docstring, (
                f"TaskLedger.{verb}'s 'Raises:' section does not name {error_name}: "
                f"{docstring[-600:]!r}"
            )


class TestTheBOUNDArgumentIsItselfBOUNDED:
    """RED today.  ⛔ **The argument nothing validated** (adversary MP-3 / I8b).

    ``max_depth`` is a PUBLIC parameter of a served read, and on a known-correct reference
    build the adversary MEASURED what a caller gets for values outside its usable range:

    * ``max_depth=0``  → ``ids=[] truncated=True`` — a nonsense answer served as an answer.
      A caller reads *"no blockers found, and the list was cut short"*, which is not what
      happened and cannot be acted on.
    * ``max_depth=256`` → ``SurrealStoreError … (unspecified rejection); see the server log``
      — the ENGINE's own *"Found 257 for bound but expected 256 at most"* withheld by the
      seam's error hygiene (store reference §4 ergonomics, P5b).  THE CONSUMER IS AN AGENT:
      a refusal that names no bound teaches nothing and the agent cannot self-correct.
    * ``max_depth=-1`` → a raw store error, same shape.

    THE PROPERTY, and it is stated over the OUTCOME rather than over a mechanism: an
    out-of-range bound is refused CLIENT-SIDE, in the ledger's own words, naming the value
    and the range — and **no statement reaches the engine**, which is the leg that
    distinguishes real validation from a prettier translation of the engine's complaint.

    ⚠ The exact upper boundary is a CONTRACT DECISION with both readings written down; see
    :func:`_served_max_depth_refusal`.
    """

    @pytest.mark.parametrize(
        "bad_depth",
        [-1, 0, ENGINE_RECURSION_CEILING, ENGINE_RECURSION_CEILING + 1],
        ids=["negative", "zero", "at-the-engine-ceiling", "past-the-engine-ceiling"],
    )
    async def test_an_OUT_OF_RANGE_max_depth_is_REFUSED_with_a_TEACHING_error(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], bad_depth: int
    ) -> None:
        ledger, _env, blocker_id = task_ledger
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker_id], created_by=CREATOR
        )
        traffic: StoreTraffic | None = None
        raised: BaseException | None = None

        async def _attempt() -> None:
            nonlocal raised
            try:
                await _transitive_blockers(ledger, task_id, max_depth=bad_depth)
            except Exception as error:  # noqa: BLE001 - the TYPE and TEXT are the assertions
                raised = error

        traffic = await measure_store_traffic(ledger, _attempt)

        assert raised is not None, (
            f"transitive_blockers(max_depth={bad_depth}) returned instead of refusing. "
            f"max_depth=0 answers 'ids=[] truncated=True', which is a served falsehood: no "
            f"traversal happened and nothing was truncated"
        )
        assert not isinstance(raised, SurrealStoreError), (
            f"max_depth={bad_depth} reached the ENGINE and came back as a store error. The "
            f"seam's error hygiene withholds the engine's own text, so the caller is served "
            f"'(unspecified rejection); see the server log' — an agent cannot act on that. "
            f"Validate the argument before any statement is built: {raised!r}"
        )
        assert str(raised) == _served_max_depth_refusal(bad_depth), (
            f"the refusal must state the offending value AND the valid range — that "
            f"sentence is the whole of what a refused caller learns. "
            f"got={str(raised)!r} want={_served_max_depth_refusal(bad_depth)!r}"
        )
        assert traffic.calls == 0, (
            f"an out-of-range max_depth sent {traffic.calls} statement(s) to the engine "
            f"before refusing: {traffic.statements}. A bound the caller cannot use is a "
            f"client-side rejection, not a round trip"
        )

    @pytest.mark.parametrize("good_depth", [1, 2, ENGINE_RECURSION_CEILING - 1])
    async def test_POSITIVE_CONTROL_an_IN_RANGE_max_depth_is_ACCEPTED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], good_depth: int
    ) -> None:
        """The control the four refusals need: a build that refused EVERY explicit bound
        would satisfy all of them.  ``ENGINE_RECURSION_CEILING - 1`` is here on purpose —
        it is the largest legal value under the decision recorded in
        :func:`_served_max_depth_refusal`, and a build that got the comparison off by one
        rejects it while passing every other leg.
        """
        ledger, _env, blocker_id = task_ledger
        task_id = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker_id], created_by=CREATOR
        )
        result = await _transitive_blockers(ledger, task_id, max_depth=good_depth)
        assert set(result.ids) == {blocker_id}
        assert result.truncated is False


#: Task ids that render BRACKETED — ``str(RecordID(TASK_TABLE, <id>))`` is
#: ``task:⟨…⟩``, never ``task:<id>``.  MEASURED 2026-07-28 on SDK 2.0.0 for all three
#: (a dashed uuid, an all-numeric id, a dash-bearing key-like id); a ledger-minted
#: ``uuid4().hex`` renders BARE, which is why every ACCEPTED id in this contract used to be
#: bare and why the ``split(":")`` decode was invisible.
#:
#: ⚠ DISTINCT VALUES from :data:`PHANTOM_TASK_IDS` on purpose: the ``task_ledger`` fixture
#: ASSERTS every phantom id absent, and a pin that creates one would contradict it.
REAL_BRACKET_RENDERING_TASK_IDS = (
    "0199c4f1-7d2a-4e51-9a63-0000000000aa",
    "20260729",
    "wave-7-charter-real",
)


class TestARealBlockerOfANyIDShapeRoundTrips:
    """RED today.  ⛔ **The pins that kill an EIGHTH hand-rolled ``split(":")``**
    (adversary B-2 / MP-2, closed 2026-07-28).

    ⚠ **THE HAZARD THIS CONTRACT NAMED AND DID NOT PIN.**  Its own fixture comment says
    finding #248 records SEVEN hand-rolled copies of that parse package-wide, *"and
    ``tasks.py`` is on the list, so an EIGHTH is one careless line away in exactly the file
    this packet edits"* — and then every id it ever ACCEPTED was ``uuid4().hex`` or
    ``<word>_<hex>``, both of which render BARE.  The four bracket-rendering shapes appeared
    ONLY on legs where the id is REFUSED, so no such shape ever travelled the edge, the
    mirror or the traversal.  A build decoding with ``str(x).split(":", 1)[-1]`` passed the
    whole contract 80/80 while serving ``'⟨0199c4f1-…⟩'`` as a task id — an id
    ``get_task`` cannot resolve.

    ``TaskLedger._bare_id`` already gets this right (``str(raw.id)`` for a ``RecordID``;
    store reference §7 records that ``RecordID`` is UNHASHABLE, which is why the API speaks
    bare ``str``).  These pins hold the NEW decode sites — the traversal's result, the
    traversal's START binding, and the mirror read — to the same standard.

    **Honest bound, stated rather than implied:** production's only id minter is
    ``uuid4().hex``, so the defect is LATENT today, not live.  ``create_many(ids=…)`` is
    public API and ``blocked_by`` is an unconstrained ``array<string>``, so the trigger is
    any caller-supplied id — which is precisely what the ``lore_tasks`` dispatcher's
    key-to-id pass-through can produce (``key_to_id.get(ref, ref)``, scout §A2-FLAG 3).
    """

    @staticmethod
    def _assert_shape_is_hostile(task_id: str) -> None:
        """The fixture's own discrimination check: an id that renders BARE proves nothing.

        Without this, a future edit could replace these values with innocuous ones and the
        whole class would keep passing while testing the case it was written to exclude.
        """
        assert str(RecordID(TASK_TABLE, task_id)) != f"{TASK_TABLE}:{task_id}", (
            f"{task_id!r} renders BARE as {str(RecordID(TASK_TABLE, task_id))!r}, so this "
            f"leg cannot observe a bracket-mangling decode at all — pick an id the SDK "
            f"brackets (a dashed uuid, an all-numeric id, or a dash-bearing key)"
        )

    @pytest.mark.parametrize("blocker_id", REAL_BRACKET_RENDERING_TASK_IDS)
    async def test_a_REAL_blocker_of_this_SHAPE_round_trips_through_create_task(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], blocker_id: str
    ) -> None:
        """``create_task``'s write path: the mirror and the traversal must both serve the
        id a caller can hand straight back to ``get_task``.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, _blocker = task_ledger
        self._assert_shape_is_hostile(blocker_id)
        created = await ledger.create_many(
            [TaskSpec(subject="a real blocker with a hostile id", description=DESCRIPTION)],
            created_by=CREATOR,
            ids=[blocker_id],
        )
        assert created == [blocker_id]
        waiter = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker_id], created_by=CREATOR
        )
        await _assert_mirror(ledger, waiter, where=f"create_task blocked on {blocker_id!r}")
        assert await _edge_blockers_of(ledger, waiter) == {blocker_id}, (
            f"the blocks EDGE decoded {blocker_id!r} into something else — a hand-rolled "
            f"str(...).split(':') is right for `task:abc` and WRONG for an id the SDK "
            f"brackets (store reference §7, finding #248)"
        )
        result = await _transitive_blockers(ledger, waiter)
        assert set(result.ids) == {blocker_id}, (
            f"the transitive read served {sorted(result.ids)} for a task blocked on "
            f"{blocker_id!r}. A bracketed id is what a hand-rolled split leaves behind"
        )
        for served in result.ids:
            assert (await ledger.get_task(served)).id == blocker_id, (
                f"the read served {served!r}, which get_task cannot resolve back to a task. "
                f"A served id that is not an id is worse than no answer: an agent will use "
                f"it, and every call it makes with it fails"
            )

    @pytest.mark.parametrize("blocker_id", REAL_BRACKET_RENDERING_TASK_IDS)
    async def test_the_TRAVERSAL_STARTS_from_a_task_whose_OWN_id_is_of_this_SHAPE(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], blocker_id: str
    ) -> None:
        """The SECOND decode site: the id the traversal BINDS as its start node.

        A build that decodes results correctly can still mis-BIND the start — and the
        failure is silent in exactly the way store reference §7 warns about: a traversal
        from a non-existent start id returns ``[]`` on both arrows, so a mis-bound start
        reads as *"this task has no blockers"* rather than as an error.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, _blocker = task_ledger
        self._assert_shape_is_hostile(blocker_id)
        waiter_id = f"{blocker_id}-waiter"
        self._assert_shape_is_hostile(waiter_id)
        await ledger.create_many(
            [TaskSpec(subject="the blocker", description=DESCRIPTION)],
            created_by=CREATOR,
            ids=[blocker_id],
        )
        await ledger.create_many(
            [
                TaskSpec(
                    subject="the waiter, itself hostile-shaped",
                    description=DESCRIPTION,
                    blocked_by=[blocker_id],
                )
            ],
            created_by=CREATOR,
            ids=[waiter_id],
        )
        await _assert_mirror(ledger, waiter_id, where=f"create_many minting {waiter_id!r}")
        result = await _transitive_blockers(ledger, waiter_id)
        assert set(result.ids) == {blocker_id}, (
            f"a traversal STARTING from {waiter_id!r} served {sorted(result.ids)}. An empty "
            f"answer here is the mis-bound-start failure: the engine returns [] silently "
            f"for a start id that names no row, so a wrong binding reads as 'unblocked'"
        )
        assert result.truncated is False


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

    async def test_the_BATCH_refusal_names_the_CARRYING_ITEM_of_every_unknown_blocker(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **RIDER-A** (design sidecar §2 R2-a) — the served text, BY VALUE, on the
        batch path.

        THREE items, only TWO of them carrying a phantom, and the phantoms deliberately in
        an order that is NOT the served order: a build that names the ids without their
        loci reddens, a build that names the wrong item reddens, and a build that reports
        only the first miss reddens.  The middle item is REAL and its blocker must not
        appear at all — the same non-vacuity guard the sibling pin uses.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, real_blocker = task_ledger
        specs = [
            TaskSpec(
                subject="item 0 waits on a ghost",
                description=DESCRIPTION,
                blocked_by=[PHANTOM_TASK_ID_NUMERIC_SHAPE],
            ),
            TaskSpec(
                subject="item 1 waits on a REAL blocker",
                description=DESCRIPTION,
                blocked_by=[real_blocker],
            ),
            TaskSpec(
                subject="item 2 waits on a different ghost",
                description=DESCRIPTION,
                blocked_by=[PHANTOM_TASK_ID_KEY_SHAPE],
            ),
        ]
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_many(specs, created_by=CREATOR)
        expected = _served_task_refusal(
            *sorted(
                (
                    _served_blocker_identity(PHANTOM_TASK_ID_NUMERIC_SHAPE, item_index=0),
                    _served_blocker_identity(PHANTOM_TASK_ID_KEY_SHAPE, item_index=2),
                )
            )
        )
        assert str(caught.value) == expected, (
            f"the batch refusal must name each unknown blocker WITH the item that carried "
            f"it. Without the locus, an agent holding a 20-item batch cannot tell which "
            f"item to edit, and an id appearing in two items makes the first retry a coin "
            f"flip (design sidecar §2 R2-a, consult-unanimous). "
            f"got={str(caught.value)!r} want={expected!r}"
        )
        assert real_blocker not in str(caught.value)

    async def test_the_refusal_TELLS_the_caller_that_NOTHING_was_created(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **RIDER-B** (design sidecar §2 R2-b) — the no-write fact is SERVED, not
        merely TRUE.

        The whole write is refused before any row lands, and this contract already pins
        that BEHAVIOUR (``test_a_refused_create_writes_NO_task_row`` and its batch twin).
        What it did not pin is that the caller is TOLD: an agent reading only *"refused"*
        does not know whether a partial batch landed, so it must pay a reconnaissance read
        before it dare resend.  Stating it is what makes a corrected resend known-safe.

        ⚠ Pinned as a SUBSTRING here **and** by value in the two sentence pins above — this
        leg exists to say, in its own failure message, WHICH clause went missing, because a
        by-value diff of a long sentence does not.
        """
        from loremaster.tasks import TaskSpec

        ledger, _env, _blocker = task_ledger
        before = await _task_row_count(ledger)
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_many(
                [
                    TaskSpec(
                        subject="the item that will be refused",
                        description=DESCRIPTION,
                        blocked_by=[PHANTOM_TASK_ID_UUID_SHAPE],
                    )
                ],
                created_by=CREATOR,
            )
        message = str(caught.value)
        assert "NOTHING was created" in message, (
            f"the refusal does not state that nothing was written. The behaviour is pinned "
            f"elsewhere; this is about the SERVED TEXT — without it an agent cannot know a "
            f"corrected resend is safe and must pay a read to find out: {message!r}"
        )
        assert await _task_row_count(ledger) == before, (
            "…and the sentence must be TRUE: the refused batch left rows behind"
        )

    @pytest.mark.parametrize("phantom", PHANTOM_TASK_IDS)
    async def test_the_offending_id_is_reproduced_VERBATIM_and_never_ELIDED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str], phantom: str
    ) -> None:
        """⛔ **RIDER-E** (design sidecar §4) — the one property both consults named
        identically, over all four id shapes.

        *"The refusal contains the offending value verbatim, in the exact form the caller
        supplied it, round-trippable against the caller's own payload."*  Its corollary:
        **ids in refusals are never elided or truncated** — a ``…``-shortened id has failed
        the only load-bearing job a refusal string has.

        ROUND-TRIPPABILITY is checked, not assumed: the token is lifted back OUT of the
        served sentence and handed to ``get_task``, which must refuse it BY THAT SAME
        TOKEN.  A build that rendered ``task:⟨0199c4f1-…⟩`` echoes something an agent
        cannot use anywhere — the #248 shape, on the refusal surface.
        """
        ledger, _env, _blocker = task_ledger
        with pytest.raises(TaskLedgerError) as caught:
            await ledger.create_task(
                SUBJECT, DESCRIPTION, blocked_by=[phantom], created_by=CREATOR
            )
        message = str(caught.value)
        assert phantom in message, (
            f"the refusal does not carry {phantom!r} verbatim: {message!r}"
        )
        for elision in ("…", "...", " more", "+"):
            assert elision not in message, (
                f"the refusal carries an elision marker {elision!r}. Every unresolved id "
                f"appears in full or the caller cannot act on it — and a COUNT of what was "
                f"elided is worse still, because the server would have to invent it: "
                f"{message!r}"
            )
        prefix, _, remainder = message.partition("unknown task(s): ")
        assert prefix == "", message
        echoed = remainder.partition(" — ")[0].split(", ")[0]
        assert echoed == phantom, (
            f"the served token {echoed!r} is not the id the caller supplied ({phantom!r}). "
            f"A refusal is round-trippable against the caller's own payload or it is not "
            f"actionable in one edit"
        )
        with pytest.raises(TaskNotFoundError) as resolved:
            await ledger.get_task(echoed)
        assert phantom in str(resolved.value), (
            f"the token lifted out of the refusal does not round-trip through get_task — "
            f"an agent handed it back gets a different failure: {resolved.value}"
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
# SECTION I — #253: ``query_tasks`` MATERIALISES THE WHOLE TABLE.
#
# Operator-ruled INTO 04b-1 on 2026-07-28 (packet §04b SPLIT, the "#253" block, committed
# `0f4656c`).  It is in THIS packet because 04b-1 already opens this ledger to mint
# ``blocks``, and that edge is plausibly the bounded blocker-resolution mechanism.
#
# THE SEAM, MEASURED at `c5a2552` — ``tasks.py::TaskLedger.query_tasks``:
#
#     rows = self._as_rows(await self._query(f"SELECT * FROM {TASK_TABLE}"))
#
# No WHERE, no LIMIT.  ``status`` / ``owner`` / ``blocked`` are then applied in a Python
# loop over every row in the ledger, and the tool-level ``limit`` slices only AFTER the whole
# table has been materialised into ``Task`` objects.
#
# ⚠⚠ THE OBVIOUS FIX IS WRONG, AND THE DOCSTRING OF THE METHOD SAYS SO:
# *"Blocker statuses are resolved against the full table so a blocker filtered OUT by the
# status/owner filter still counts."*  **The full read is LOAD-BEARING for the ``blocked``
# partition.**  Pushing the filters into the store naively mis-classifies it SILENTLY, and the
# DIRECTION of the error depends on which filter the caller supplied.  This is a
# removed-behaviour inventory item, not a footnote.
#
# ⚠ AND ``_is_blocked`` IS NOT THE DEFECT.  It is a PURE predicate over an
# already-fetched ``status_by_id`` dict and reads nothing; the unbounded read is its CALLER.
# An earlier framing named the wrong symbol; nothing below pins ``_is_blocked``.
#
# ⚠ TWO VERDICTED NON-DEFECTS, so nothing here re-flags them: the rollup read is bounded by
# ``WHERE updated_at > $since``, and ``_select_row`` is a single-record ``type::record(...)``
# read.
#
# RED TODAY: every pin in this section except the instrument's own positive control and the
# semantics pins that describe behaviour today's full read already gets right.
# =========================================================================== #

#: How many UNRELATED tasks the growth fixture mints at its LARGE-N leg.  ≫ the ≤3 blockers
#: any pin here uses, because a whole-table read and a bounded read are INDISTINGUISHABLE at
#: small N — this repo's most-repeated fixture failure, and the reason the assertion below is
#: a GROWTH comparison (small-N vs large-N) rather than a threshold: a threshold is a fixture
#: value someone can tune until it passes.
UNRELATED_TASK_COUNT_LARGE = 60
UNRELATED_TASK_COUNT_SMALL = 5


# --------------------------------------------------------------------------- #
# ⚠ THE ROWS-READ INSTRUMENT LIVES IN ``_surreal_harness`` (escalation E-C, closed
# 2026-07-28): :func:`~_surreal_harness.measure_store_traffic`, beside ``run`` — exactly as
# ``_enforced_relations_scaffold`` houses the migration idiom.  TWO modules measure with it
# (this one and ``test_query_tasks_bounded.py``), and a test module importing a sibling TEST
# module is the wrong address.
#
# It also CHANGED SEAM in that move, and that is not cosmetic.  The version that lived here
# wrapped ``TaskLedger._query`` — ONE of the ledger's doors to the engine.  Ruling R7 puts
# the bounded read's two reads inside ONE transaction, and a transaction that returns
# results must ride ``query_raw`` (store reference §3: ``execute_transaction`` returns
# ``None`` and cannot serve a READ).  A ``_query``-keyed counter would have reported ZERO
# ROWS for exactly the build R7 demands — and zero reads as *"the read did not grow"*, the
# instrument lying in the direction of false confidence.  ``measure_store_traffic`` counts at
# the CONNECTION, the one door every seam passes through, and reports ROUND TRIPS beside
# rows so R7 has an instrument at all.
#
# The tree's other instruments (``test_brief_ledger.py``'s
# ``TestCoverageQueryCountIsBounded::_coverage_query_count`` and its fleet sibling) stay put
# and stay right for their own question: they count QUERIES, and #253 is ONE query that
# reads the whole table, so their number is 1 before and after the fix.  ``keep_with_trigger``.
# --------------------------------------------------------------------------- #


async def _seed_unrelated_tasks(ledger: TaskLedger, count: int) -> list[str]:
    """Mint ``count`` unrelated, unblocked, open tasks in ONE transaction.

    Through ``create_many`` rather than N× ``create_task`` so the fixture cost is one
    round trip: the pins below care about what the READ touches, never about how the noise
    got there.
    """
    from loremaster.tasks import TaskSpec

    if count == 0:
        return []
    specs = [
        TaskSpec(subject=f"unrelated backlog item {index}", description=DESCRIPTION)
        for index in range(count)
    ]
    return await ledger.create_many(specs, created_by=CREATOR)


async def _seed_legacy_task(
    connection: SurrealConnection,
    task_id: str,
    *,
    blocked_by: list[str],
    status: str,
    owner: str | None = None,
) -> None:
    """RAW-CREATE a ``task`` row with an arbitrary ``blocked_by``, bypassing every guard.

    ⚠ **This is not a contrivance — it is the PRODUCTION state.**  Once requirement I lands,
    the ledger REFUSES to mint a task naming a phantom blocker; but every row written BEFORE
    this packet was written under a FAIL-OPEN ``blocked_by`` (scout §A2-FLAG 4), so a
    long-lived store holds exactly these rows and nothing will ever clean them (#236 is ruled
    OUT).  A fixture that can only produce rows the NEW guard allows is a fixture that
    guarantees the one condition under which the bug is invisible.

    Note what such a row does NOT have: a ``blocks`` EDGE.  ``ENFORCED`` cannot write an edge
    to a task that does not exist — which is exactly the divergence
    :meth:`TestTheBoundedReadKeepsTheClaimAgreement.test_a_LEGACY_row_with_a_phantom_blocker_is_fail_closed_UNRESOLVED`
    exists to catch.

    ``owner`` exists because a task that is BOTH blocked and OWNED is unreachable through
    the public verbs — the claim CAS refuses a blocked task, and no verb adds a dependency
    after birth — yet it is exactly the row the OWNER-filter pins need in order to observe
    anything at all (see :class:`TestTheBoundedReadKeepsTheClaimAgreement`).  Production
    holds such rows for the same reason it holds the phantom-blocker ones: they were legal
    when they were written.
    """
    now = datetime.now(UTC)
    content: dict[str, Any] = {
        "subject": "a legacy row written under the fail-open blocked_by",
        "description": DESCRIPTION,
        "status": status,
        "blocked_by": blocked_by,
        "provenance": {"created_by": "legacy", "created_at": now.isoformat(), "events": []},
        "created_at": now,
    }
    if owner is not None:
        content["owner"] = owner
        content["claimed_at"] = now
    await run(
        connection,
        f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $content",
        {"id": task_id, "content": content},
    )


async def _drive_to(ledger: TaskLedger, task_id: str, status: str) -> None:
    """Drive a freshly-created open task to ``status`` along a LEGAL edge.

    Uses the real state machine (``LEGAL_TRANSITIONS``) rather than a raw UPDATE, so the
    six-status fixture in :class:`TestTheTerminalSetIsExactlyDoneAndWontfix` exercises rows
    production can actually produce.
    """
    if status == STATUS_OPEN:
        return
    if status == STATUS_BLOCKED:
        await ledger.transition(task_id, STATUS_BLOCKED, actor=ACTOR)
        return
    if status == STATUS_WONTFIX:
        await ledger.transition(task_id, STATUS_WONTFIX, actor=ACTOR)
        return
    claim = await ledger.claim_task(task_id, ACTOR)
    assert claim.claimed, f"the fixture could not claim {task_id!r} on its way to {status!r}"
    if status == STATUS_CLAIMED:
        return
    await ledger.transition(task_id, STATUS_IN_PROGRESS, actor=ACTOR)
    if status == STATUS_IN_PROGRESS:
        return
    if status == STATUS_DONE:
        await ledger.transition(task_id, STATUS_DONE, actor=ACTOR, summary="blocker finished")
        return
    raise AssertionError(f"the fixture has no legal path to {status!r}")


class TestTheReadIsBOUNDEDByTheCallersFilter:
    """RED today.  ⛔ #253 — the pin a whole-table read cannot pass.

    THE DISCRIMINATION IS A GROWTH COMPARISON, not a threshold.  The same query, answering
    the same question, is measured against a ledger holding 5 unrelated tasks and one holding
    60.  A bounded read touches the candidate set and its blockers — identical at both N.  A
    ``SELECT * FROM task`` touches everything — 5 rows vs 60.

    ⚠ Why not a threshold: a magic number is a fixture value a builder can tune until it
    passes, and it would encode today's row shapes as a law.  The GROWTH property is the
    actual requirement (*"does the work scale with the size of the ledger, or with the size of
    the answer?"*) and no tuning satisfies it.

    ⚠ **THIS SECTION DOES NOT PIN THE UNFILTERED READ.**  ``query_tasks()`` with no
    ``status``/``owner``/``limit`` legitimately asks for every task, so its cost is the
    answer's cost.  The tool-level ``limit`` is closed SEPARATELY by operator ruling **R5**
    (2026-07-28) — ``query_tasks`` takes it and pushes it into the STATEMENT — and is pinned
    in ``test_query_tasks_bounded.py``'s ``TestTheLimitIsPUSHEDINTOTheStatement``.
    """

    @staticmethod
    async def _measure(unrelated_count: int, *, by_owner: bool) -> tuple[int, int]:
        """Rows read AND the answer's size, for ONE filtered ``query_tasks``.

        The ANSWER is identical at every ``unrelated_count`` by construction: the noise tasks
        are open + unowned, and the query filters on a status/owner only the target task
        has.  So any difference in rows-read is caused by the LEDGER's size, which is the
        whole question.

        ⚠ **THE ANSWER TRAVELS BACK BESIDE THE COUNT, and it is not decoration.**  *"This
        number did not grow"* is TRUE of a build that reads nothing and answers nothing, so a
        rows-read comparison alone is satisfied perfectly by ``return []``.  Every leg below
        asserts the answer's cardinality at BOTH sizes.  (The adversary's own question —
        *what WRONG build would still pass this?* — asked of this class's first draft, whose
        only guard was ``large < 60``: ``0 < 60`` holds.)

        ⚠ **AND THE BLOCKER IS DRIVEN TERMINAL BEFORE THE CLAIM** (escalation E-A, closed
        2026-07-28).  Without it, the owner leg died in FIXTURE SETUP on every build
        including a correct one: the claim CAS refuses a task whose only blocker is ``open``,
        so ``assert claim.claimed`` failed before ``query_tasks`` was ever called — a pin no
        implementation could make green, which is the C-DEF class this repo's law names.
        ``wontfix`` rather than ``done`` deliberately: ``_drive_to(..., done)`` CLAIMS the
        blocker on its way through, which would leave it owned by ``ACTOR`` and put TWO tasks
        in the owner leg's answer; ``wontfix`` is a single legal transition from ``open`` and
        leaves the blocker unowned, so the answer stays the ONE target the docstring above
        promises.
        """
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        ledger = TaskLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )
        try:
            await ledger.ensure_ready()
            await _seed_unrelated_tasks(ledger, unrelated_count)
            blocker = await ledger.create_task("a real blocker", DESCRIPTION, created_by=CREATOR)
            target = await ledger.create_task(
                SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
            )
            served: list[Task] = []

            async def _run(**filters: Any) -> None:
                served.clear()
                served.extend(await ledger.query_tasks(**filters))

            if by_owner:
                await _drive_to(ledger, blocker, STATUS_WONTFIX)
                claim = await ledger.claim_task(target, ACTOR)
                assert claim.claimed, (
                    "the fixture could not claim its target, so this measurement would "
                    "compare two empty answers and could not discriminate anything"
                )
                rows = (await measure_store_traffic(ledger, lambda: _run(owner=ACTOR))).rows
                return rows, len(served)
            await ledger.transition(target, STATUS_WONTFIX, actor=ACTOR)
            rows = (
                await measure_store_traffic(ledger, lambda: _run(status=STATUS_WONTFIX))
            ).rows
            return rows, len(served)
        finally:
            await ledger.close()
            await drop_database(env)

    @pytest.mark.parametrize("by_owner", [False, True], ids=["status-filter", "owner-filter"])
    async def test_rows_read_does_NOT_grow_with_the_size_of_the_LEDGER(self, by_owner: bool) -> None:
        """Both filters, because requirement 1 names both and a fix may reach only one."""
        small, small_answer = await self._measure(UNRELATED_TASK_COUNT_SMALL, by_owner=by_owner)
        large, large_answer = await self._measure(UNRELATED_TASK_COUNT_LARGE, by_owner=by_owner)
        assert small_answer == large_answer == 1, (
            f"the two measurements served {small_answer} and {large_answer} tasks; each must "
            f"serve the ONE target. Either the fixture drifted — a rows-read comparison "
            f"between two DIFFERENT answers measures nothing — or the build serves no answer "
            f"at all, and 'the row count did not grow' is trivially true of `return []`"
        )
        assert small > 0, (
            "the instrument counted ZERO rows for a query that served a task — it is not "
            "observing this call path at all, so its 'did not grow' verdict is worthless"
        )
        assert large == small, (
            f"a filtered query_tasks read {small} rows against a ledger of "
            f"{UNRELATED_TASK_COUNT_SMALL} unrelated tasks but {large} against one of "
            f"{UNRELATED_TASK_COUNT_LARGE}. The answer is the same at both sizes, so the "
            f"read is scaling with the LEDGER rather than with the ANSWER — that is #253. "
            f"The status/owner filters must push into the store, and blocker resolution must "
            f"be bounded by the CANDIDATE set's blocked_by / blocks edges. ⚠ Do NOT fix this "
            f"by dropping the full-table blocker resolution: it is load-bearing (see this "
            f"class's siblings in TestTheBoundedReadKeepsTheClaimAgreement)"
        )
        assert large < UNRELATED_TASK_COUNT_LARGE, (
            f"the read touched {large} rows, at least as many as the "
            f"{UNRELATED_TASK_COUNT_LARGE} unrelated tasks that are not in its answer"
        )

    async def test_POSITIVE_CONTROL_the_instrument_CAN_see_an_unbounded_read_grow(self) -> None:
        """⛔ A PROBE NEEDS A CONTROL.

        The pin above is a NEGATIVE result (*"this number did not grow"*), and a negative
        result from a blind instrument is indistinguishable from a negative result from a
        working one.  A counter that always returned 0 — because the reply shape is not one
        this wrapper recognises, or because the shadowing did not take — would satisfy it
        perfectly.

        So: run a DELIBERATELY unbounded read through the same instrument at the same two
        sizes and require the number to grow, and to grow by the amount seeded.
        """

        async def _unbounded(unrelated_count: int) -> int:
            env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
            ledger = TaskLedger(
                url=env.url,
                namespace=env.namespace,
                database=env.database,
                user=env.user,
                password=env.password,
            )
            try:
                await ledger.ensure_ready()
                await _seed_unrelated_tasks(ledger, unrelated_count)
                return (
                    await measure_store_traffic(
                        ledger,
                        lambda: _raw(ledger, f"SELECT * FROM {TASK_TABLE}"),
                    )
                ).rows
            finally:
                await ledger.close()
                await drop_database(env)

        small = await _unbounded(UNRELATED_TASK_COUNT_SMALL)
        large = await _unbounded(UNRELATED_TASK_COUNT_LARGE)
        assert small == UNRELATED_TASK_COUNT_SMALL, (
            f"the instrument counted {small} rows for a whole-table read of "
            f"{UNRELATED_TASK_COUNT_SMALL} tasks — it is not observing row counts, so every "
            f"'did not grow' result it produces is worthless"
        )
        assert large == UNRELATED_TASK_COUNT_LARGE, large
        assert large > small

    async def test_POSITIVE_CONTROL_the_instrument_ALSO_sees_a_read_inside_a_TRANSACTION(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **The control the R7 ruling made necessary, and the one that would have caught
        the instrument this file used to carry.**

        Ruling R7 puts the bounded read's two reads inside ONE ``BEGIN … COMMIT``.  A
        transaction that hands results back must ride ``query_raw`` (store reference §3:
        ``execute_transaction`` returns ``None``), so an instrument keyed on ``_query`` — as
        this file's original ``_rows_read`` was — reports **ZERO** for exactly the build R7
        demands, and zero reads as *"the read did not grow"*.  This proves the replacement
        can see BOTH doors: the same instrument, the same ledger, one measurement each.
        """
        ledger, _env, blocker_id = task_ledger
        await ledger.create_task("a second row", DESCRIPTION, created_by=CREATOR)
        connection = await ledger._ensure_connection()  # noqa: SLF001 - the seam IS the control

        plain = await measure_store_traffic(
            ledger, lambda: _raw(ledger, f"SELECT * FROM {TASK_TABLE}")
        )
        boxed = await measure_store_traffic(
            ledger,
            lambda: connection.query_raw(
                f"BEGIN; SELECT * FROM {TASK_TABLE}; SELECT * FROM {TASK_TABLE}; COMMIT;"
            ),
        )
        assert plain.rows == 2, f"the plain read saw {plain.rows} rows, expected 2: {plain}"
        assert plain.calls == 1, plain
        assert boxed.rows == 4, (
            f"the instrument saw {boxed.rows} rows through a BEGIN…COMMIT that read the same "
            f"two-row table twice. An instrument blind to the transaction door cannot see a "
            f"bounded read built the way ruling R7 requires, and would report 0 — which every "
            f"growth pin in this file would read as success: {boxed}"
        )
        assert boxed.calls == 1, (
            f"a whole BEGIN…COMMIT is ONE round trip; the instrument counted {boxed.calls}, "
            f"so its round-trip number cannot be trusted by the R7 pins: {boxed}"
        )
        assert blocker_id  # the fixture's real task is what makes the row count 2


class TestTheTerminalSetIsExactlyDoneAndWontfix:
    """GREEN today — a REGRESSION pin, and requirement 2(c).

    ∀ over the WHOLE six-status vocabulary, each fate forced by its own fixture: a blocker
    unblocks its dependent iff its status is ``done`` or ``wontfix``, and blocks it in all
    four other states.  Pinned as a universal rather than as "done unblocks" because a
    bounded rewrite most plausibly gets this wrong at the edges — and the sharpest edge is
    the status literally named ``blocked``, which is NOT terminal and which a rewrite
    conflating *dependency*-blocked with *status*-blocked would resolve.
    """

    @pytest.mark.parametrize(
        ("blocker_status", "unblocks"),
        [
            (STATUS_OPEN, False),
            (STATUS_CLAIMED, False),
            (STATUS_IN_PROGRESS, False),
            (STATUS_BLOCKED, False),
            (STATUS_DONE, True),
            (STATUS_WONTFIX, True),
        ],
    )
    async def test_a_blocker_unblocks_ONLY_from_a_terminal_status(
        self,
        task_ledger: tuple[TaskLedger, SurrealEnv, str],
        blocker_status: str,
        unblocks: bool,
    ) -> None:
        ledger, _env, _seed = task_ledger
        blocker = await ledger.create_task("the blocker", DESCRIPTION, created_by=CREATOR)
        dependent = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
        )
        await _drive_to(ledger, blocker, blocker_status)
        unblocked_ids = {task.id for task in await ledger.query_tasks(blocked=False)}
        blocked_ids = {task.id for task in await ledger.query_tasks(blocked=True)}
        assert (dependent in unblocked_ids) is unblocks, (
            f"with its only blocker in status {blocker_status!r}, the dependent's "
            f"blocked=False membership was {dependent in unblocked_ids}, expected "
            f"{unblocks}. TERMINAL is exactly {{done, wontfix}} — note that the status "
            f"literally named 'blocked' is NOT terminal"
        )
        assert (dependent in blocked_ids) is not unblocks, (
            "the blocked=True and blocked=False partitions disagree with each other about "
            f"{dependent!r} — they must be complementary"
        )


class TestTheBoundedReadKeepsTheClaimAgreement:
    """RED today in its bounded-read legs, GREEN in the semantics it preserves.

    ⛔ **THE PINS A NAIVE PUSH-DOWN BREAKS.**  ``query_tasks``' own docstring names the
    property the full read buys: *"Blocker statuses are resolved against the full table so a
    blocker filtered OUT by the status/owner filter still counts."*  Push the caller's filter
    into the store without separating the two reads and the blocker vanishes from
    ``status_by_id``, so ``_is_blocked`` sees an unresolvable id and the dependent flips —
    **silently, and in a direction that depends on which filter the caller supplied.**

    Requirement 2(d) is the one that matters most and is the hardest to get right: the query
    partition and the atomic claim's SERVER-SIDE CAS
    (``tasks.py::_claim_fragment``'s ``array::len(blocked_by) = array::len($clm_resolved)``)
    are two INDEPENDENT implementations of one question.  Today they agree because the query
    side reads everything.  A bounded rewrite is a second chance to make them disagree, and a
    disagreement is invisible until an agent is told a task is claimable and the claim then
    silently writes nothing.
    """

    @pytest.mark.parametrize(
        ("blocker_status", "dependent_is_unblocked"),
        [(STATUS_IN_PROGRESS, False), (STATUS_DONE, True)],
        ids=["non-terminal-blocker", "terminal-blocker"],
    )
    async def test_a_blocker_EXCLUDED_by_the_STATUS_filter_still_counts(
        self,
        task_ledger: tuple[TaskLedger, SurrealEnv, str],
        blocker_status: str,
        dependent_is_unblocked: bool,
    ) -> None:
        """GREEN today (the full read buys it) — RED on a naive push-down, **but only on
        the TERMINAL leg, and the terminal leg did not exist** (escalation E-H, closed
        2026-07-28).

        The blocker is outside the caller's ``status='open'`` candidate set either way; the
        AXIS is whether it is terminal.  MEASURED: with a NON-TERMINAL blocker the naive
        rewrite's fail-closed default (*"a blocker I cannot see is unresolved"*) gives the
        RIGHT answer for the WRONG reason, so the pin passed the exact build it was written
        to kill — value monoculture on the one axis that decides the branch.

        The TERMINAL direction is the finding's own damage pattern inverted: truth says the
        dependency resolved and the dependent is claimable, the naive build calls it
        unresolved, and **claimable work is silently dropped from the served answer** while
        the claim CAS still grants it to anyone asking by id.  A fleet reading
        ``lore_tasks`` never sees the work; the work never gets done.
        """
        ledger, _env, _seed = task_ledger
        blocker = await ledger.create_task("the excluded blocker", DESCRIPTION, created_by=CREATOR)
        dependent = await ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
        )
        await _drive_to(ledger, blocker, blocker_status)

        candidates = {task.id for task in await ledger.query_tasks(status=STATUS_OPEN)}
        assert dependent in candidates, (
            "the dependent is not in the caller's candidate set at all, so this leg cannot "
            "observe anything about blocker resolution — the fixture, not the build, is wrong"
        )
        assert blocker not in candidates, (
            f"the blocker (status {blocker_status!r}) is INSIDE the status='open' candidate "
            f"set, so nothing here is out-of-filter and the pin tests the easy case"
        )

        unblocked = {
            task.id for task in await ledger.query_tasks(status=STATUS_OPEN, blocked=False)
        }
        assert (dependent in unblocked) is dependent_is_unblocked, (
            f"with its only blocker in status {blocker_status!r} and EXCLUDED by the "
            f"caller's status filter, the dependent's blocked=False membership was "
            f"{dependent in unblocked}, expected {dependent_is_unblocked}. The candidate set "
            f"and the blocker-resolution set are DIFFERENT sets: pushing one filter into the "
            f"store must not narrow the other. ⚠ A build that answers 'unresolved' for every "
            f"blocker outside the candidate set passes the non-terminal leg by accident and "
            f"fails here — it drops claimable work from the served answer"
        )

    @pytest.mark.parametrize(
        ("blocker_status", "dependent_is_unblocked"),
        [(STATUS_CLAIMED, False), (STATUS_DONE, True)],
        ids=["non-terminal-blocker", "terminal-blocker"],
    )
    async def test_a_blocker_EXCLUDED_by_the_OWNER_filter_still_counts(
        self,
        task_ledger: tuple[TaskLedger, SurrealEnv, str],
        blocker_status: str,
        dependent_is_unblocked: bool,
    ) -> None:
        """The second filter, because a fix may reach only one — and because the OWNER filter
        excludes on a column the blocker-resolution read has no reason to project at all.

        ⚠ **THE DEPENDENT IS RAW-SEEDED OWNED, AND THAT IS A FIX, NOT A CONVENIENCE**
        (escalation E-H, 2026-07-28).  The previous fixture left the dependent UNOWNED —
        the claim it attempted was refused, which the pin itself asserted — so
        ``query_tasks(owner=other_owner)`` could never contain it whatever the build did,
        and *"the dependent is not served"* was true by the OWNER filter alone.  The pin
        could not fail.  A task that is both BLOCKED and OWNED is unreachable through the
        public verbs (the CAS refuses a blocked claim, and no verb adds a dependency after
        birth), so the row is seeded the way production got its own: written when it was
        legal.  See :func:`_seed_legacy_task`.
        """
        ledger, env, _seed = task_ledger
        other_owner = "someone-else"
        blocker = await ledger.create_task(
            "the other owner's blocker", DESCRIPTION, created_by=CREATOR
        )
        await _drive_to(ledger, blocker, blocker_status)  # owned by ACTOR, never other_owner

        dependent = f"legacy_owned_{uuid.uuid4().hex}"
        setup = await connect_admin(env)
        try:
            await _seed_legacy_task(
                setup,
                dependent,
                blocked_by=[blocker],
                status=STATUS_CLAIMED,
                owner=other_owner,
            )
        finally:
            await setup.close()

        candidates = {task.id for task in await ledger.query_tasks(owner=other_owner)}
        assert candidates == {dependent}, (
            f"the owner candidate set is {sorted(candidates)}, expected exactly the "
            f"dependent. If the dependent is missing this leg observes nothing (the previous "
            f"fixture's defect); if the blocker is present it is not out-of-filter"
        )

        unblocked = {
            task.id for task in await ledger.query_tasks(owner=other_owner, blocked=False)
        }
        assert (dependent in unblocked) is dependent_is_unblocked, (
            f"with its only blocker in status {blocker_status!r}, owned by a DIFFERENT "
            f"identity and therefore outside the caller's owner candidate set, the "
            f"dependent's blocked=False membership was {dependent in unblocked}, expected "
            f"{dependent_is_unblocked}. The owner filter narrows the CANDIDATES, never the "
            f"blocker-resolution set"
        )

    async def test_a_LEGACY_row_with_a_phantom_blocker_is_fail_closed_UNRESOLVED(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **THE MOST LIKELY WAY A BOUNDED REWRITE BREAKS, and requirement 2(b).**

        A row written before 04b-1 can name a blocker that was never minted (``blocked_by``
        was FAIL-OPEN at write).  Such a row has **no ``blocks`` EDGE** — ``ENFORCED`` cannot
        write an edge to a task that does not exist.  So a rewrite that resolves blockers
        through the EDGE rather than the COLUMN sees NO blockers, calls the row UNBLOCKED,
        and serves it as claimable — while the claim CAS, which reads the COLUMN, refuses it
        forever.  Two mechanisms, one question, opposite answers, no error anywhere.

        The row is raw-seeded because the new guard makes it unreachable through the ledger;
        see :func:`_seed_legacy_task` for why that is production's state and not a contrivance.
        """
        ledger, env, _seed = task_ledger
        legacy_id = f"legacy_{uuid.uuid4().hex}"
        setup = await connect_admin(env)
        try:
            await _seed_legacy_task(
                setup, legacy_id, blocked_by=[PHANTOM_TASK_ID_UUID_SHAPE], status=STATUS_OPEN
            )
            assert not await record_exists(setup, TASK_TABLE, PHANTOM_TASK_ID_UUID_SHAPE)
        finally:
            await setup.close()
        unblocked = {task.id for task in await ledger.query_tasks(blocked=False)}
        assert legacy_id not in unblocked, (
            "a task whose blocked_by names a NEVER-MINTED id was served as unblocked. An "
            "unresolvable blocker is FAIL-CLOSED: the claim CAS counts it "
            "(array::len(blocked_by) != array::len($clm_resolved)) and refuses forever, so a "
            "query that calls it claimable is telling an agent to attempt a claim that can "
            "never win. ⚠ If you resolved blockers through the blocks EDGE, note that a "
            "legacy row has no edge for a blocker that does not exist"
        )
        claim = await ledger.claim_task(legacy_id, ACTOR)
        assert not claim.claimed, (
            "the CAS itself accepted a task with an unresolvable blocker — that is a "
            "DIFFERENT and worse defect than the one this pin was written for"
        )

    async def test_the_PARTITION_and_the_CLAIM_can_never_DISAGREE(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **Requirement 2(d) — the ∀ agreement pin.**

        For every open, unowned, non-superseded task in the ledger: membership of
        ``query_tasks(blocked=False)`` must equal *"a claim would succeed"*.  Two independent
        mechanisms — a Python predicate over a read, and a server-side ``array::len`` CAS
        inside a transaction — held to one answer, over a fixture set that FORCES every
        interesting shape rather than sampling whichever the rewrite happens to handle.

        THE QUANTIFIER LAW: the property is not *"the rewrite still handles a done blocker"*.
        It is *"the two mechanisms agree, ∀ tasks, whatever made them blocked"* — and each
        fate below is forced by its own row.

        ⚠ The claim is DESTRUCTIVE (a win writes an owner), so it runs LAST, after the whole
        partition has been read; and the assertion is made per-task with the task named, so a
        failure says WHICH shape diverged rather than that some did.
        """
        ledger, env, _seed = task_ledger
        shapes: dict[str, str] = {}

        shapes["no blockers"] = await ledger.create_task(
            "no blockers", DESCRIPTION, created_by=CREATOR
        )
        for label, blocker_status in (
            ("blocker done", STATUS_DONE),
            ("blocker wontfix", STATUS_WONTFIX),
            ("blocker open", STATUS_OPEN),
            ("blocker in_progress", STATUS_IN_PROGRESS),
            ("blocker status-blocked", STATUS_BLOCKED),
        ):
            blocker = await ledger.create_task(f"blocker for {label}", DESCRIPTION, created_by=CREATOR)
            shapes[label] = await ledger.create_task(
                label, DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
            )
            await _drive_to(ledger, blocker, blocker_status)

        first = await ledger.create_task("first of two", DESCRIPTION, created_by=CREATOR)
        second = await ledger.create_task("second of two", DESCRIPTION, created_by=CREATOR)
        shapes["two blockers, one resolved"] = await ledger.create_task(
            "one of two resolved", DESCRIPTION, blocked_by=[first, second], created_by=CREATOR
        )
        await _drive_to(ledger, first, STATUS_DONE)
        both_a = await ledger.create_task("both a", DESCRIPTION, created_by=CREATOR)
        both_b = await ledger.create_task("both b", DESCRIPTION, created_by=CREATOR)
        shapes["two blockers, both resolved"] = await ledger.create_task(
            "both resolved", DESCRIPTION, blocked_by=[both_a, both_b], created_by=CREATOR
        )
        await _drive_to(ledger, both_a, STATUS_DONE)
        await _drive_to(ledger, both_b, STATUS_WONTFIX)

        legacy_id = f"legacy_{uuid.uuid4().hex}"
        setup = await connect_admin(env)
        try:
            await _seed_legacy_task(
                setup, legacy_id, blocked_by=[PHANTOM_TASK_ID_NUMERIC_SHAPE], status=STATUS_OPEN
            )
        finally:
            await setup.close()
        shapes["legacy row, phantom blocker"] = legacy_id

        unblocked = {task.id for task in await ledger.query_tasks(blocked=False)}
        partition_says = {label: task_id in unblocked for label, task_id in shapes.items()}

        disagreements: list[str] = []
        for label, task_id in shapes.items():
            claim = await ledger.claim_task(task_id, f"claimer-{uuid.uuid4().hex[:8]}")
            if claim.claimed != partition_says[label]:
                disagreements.append(
                    f"{label} ({task_id}): query_tasks(blocked=False) said "
                    f"{partition_says[label]}, the claim CAS said {claim.claimed}"
                )
        assert disagreements == [], (
            "the query partition and the atomic claim's server-side CAS disagree. These are "
            "two INDEPENDENT implementations of 'is every blocker terminal' — the full-table "
            "read is what makes them agree today, so a bounded rewrite must keep them equal "
            "BY CONSTRUCTION, not by coincidence. A disagreement is invisible in production: "
            "an agent is told a task is claimable and the claim silently writes nothing. "
            f"Diverging shapes: {disagreements}"
        )
        assert any(partition_says.values()) and not all(partition_says.values()), (
            "every shape in this fixture landed on the SAME side of the partition, so the "
            "agreement above holds for a fixture reason — a build answering one constant "
            "would pass it"
        )


#: How many racers the duplicate-blocker CAS pin runs.  Ruling **T5** ships this class with
#: *"the concurrency evidence that standard demands: ≥8-way × 20 consecutive green runs,
#: never a single green run"*, and the repo's standing rule is the same: a lone green run
#: gave a LEAD a false all-clear on a real concurrency defect (``CLAUDE.md``, C1).  The 8 is
#: encoded HERE; the 20 is an EXECUTION protocol and is stated in the class docstring,
#: because a test cannot assert how many times it was run.
DUPLICATE_BLOCKER_RACERS = 8


class TestTheDuplicateBlockerDivergence:
    """⛔ **RULING T5, 2026-07-28 — CLOSED. RED at ``5a2dca9``.**  (Was escalation E-6.)

    Found while writing requirement 2(d)'s agreement pin, not looked for.  The two mechanisms
    treat a DUPLICATED blocker id differently:

    * ``_is_blocked`` iterates ``blocked_by`` ENTRIES, so a repeated id is harmless;
    * ``_claim_fragment`` compares ``array::len(blocked_by)`` against
      ``array::len($clm_resolved)``, and the resolved list is a SET of matching rows — so
      ``blocked_by = [X, X]`` with X ``done`` is ``2 != 1`` and the claim **fails forever**.

    ``_new_task_content`` dedupes at birth *"so a DUPLICATE id must not double-count against
    the claim gate's array::len CAS"* — i.e. the normalisation exists **precisely because the
    CAS cannot tolerate duplicates**, and it is the ONLY thing standing between the two
    mechanisms.  A row that predates it, or any future write path that forgets it, produces a
    task the fleet is told is claimable and that can never be claimed.

    T5, verbatim: *"A divergence between the SERVED partition and what the CAS actually does
    is a trust defect by definition."*  The fix is the class's own one-line recommendation,
    MEASURED green on a reference build: **``array::len(array::distinct(blocked_by))`` in the
    CAS**, so the guard tolerates what the normalisation was silently protecting it from.

    ⚠⚠ **THE OLD PIN ADMITTED A WRONG BUILD, AND THAT IS WHY IT CHANGED.**  It asserted only
    that the two mechanisms AGREE (``claim.claimed == (legacy_id in unblocked)``) — which is
    equally true of a build that "fixes" the divergence by teaching ``query_tasks`` to
    double-count duplicates too, i.e. by making BOTH mechanisms call a fully-resolved task
    unclaimable forever.  That build closes the divergence and keeps the black hole.  The
    legs below assert the ANSWER, not merely the agreement: with every distinct blocker
    terminal, the task is CLAIMABLE, in both mechanisms.

    ⚠ **THIS TOUCHES THE LIVE CLAIM CAS, so it ships with the concurrency evidence this repo
    demands** (T5, verbatim): **≥8-way × 20 consecutive green runs, never a single green
    run.**  The 8-way leg is :meth:`test_EXACTLY_ONE_of_EIGHT_racers_wins_a_row_with_a_DUPLICATED_blocker`;
    the 20 consecutive runs are an execution protocol a test cannot assert about itself, so
    they are a RECEIPT the wave owes:

        for i in $(seq 20); do uv run pytest -q --show-capture=no \\
          "loremaster/tests/test_blocks_edge.py::TestTheDuplicateBlockerDivergence" \\
          || { echo "RUN $i FAILED"; break; }; done

    **A failing run is a STOP, never a "flaky".**  A builder may not downgrade a red
    concurrency test to flakiness and proceed (``CLAUDE.md``: the C1 mint defect failed ~4 of
    5 runs, was called flaky, and shipped).
    """

    @staticmethod
    async def _legacy_row_with_duplicate(
        ledger: TaskLedger, env: SurrealEnv, *, blocker_status: str
    ) -> tuple[str, str]:
        """A raw-seeded ``blocked_by=[X, X]`` row, with ``X`` driven to ``blocker_status``.

        Raw-seeded because ``_new_task_content``'s birth-time dedupe makes the shape
        unreachable through the ledger — which is exactly the point: production holds rows
        written before that normalisation existed, and a fixture that can only produce rows
        today's write path allows guarantees the one condition under which the bug is
        invisible (``CLAUDE.md``, "THE TEST ENVIRONMENT IS A FICTION").
        """
        blocker = await ledger.create_task("the duplicated blocker", DESCRIPTION, created_by=CREATOR)
        await _drive_to(ledger, blocker, blocker_status)
        legacy_id = f"legacy_dupe_{uuid.uuid4().hex}"
        setup = await connect_admin(env)
        try:
            await _seed_legacy_task(
                setup, legacy_id, blocked_by=[blocker, blocker], status=STATUS_OPEN
            )
        finally:
            await setup.close()
        return legacy_id, blocker

    async def test_a_LEGACY_row_with_a_DUPLICATED_resolved_blocker_is_CLAIMABLE_in_BOTH(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ The ANSWER, not merely the agreement — see the class docstring for the wrong
        build that "agree" alone waves through.
        """
        ledger, env, _seed = task_ledger
        legacy_id, blocker = await self._legacy_row_with_duplicate(
            ledger, env, blocker_status=STATUS_DONE
        )
        unblocked = {task.id for task in await ledger.query_tasks(blocked=False)}
        served_unblocked = legacy_id in unblocked
        claim = await ledger.claim_task(legacy_id, ACTOR)
        assert (served_unblocked, claim.claimed) == (True, True), (
            f"blocked_by=[X, X] with X ({blocker!r}) DONE: query_tasks(blocked=False) says "
            f"unblocked={served_unblocked}, the claim CAS says claimed={claim.claimed}. Every "
            f"DISTINCT dependency of this task is terminal, so the answer is CLAIMABLE and "
            f"both mechanisms must say so. The CAS compares array::len(blocked_by) with the "
            f"length of the DISTINCT resolved set, so a duplicate makes the counts differ and "
            f"the task is unclaimable forever while being served as claimable (T5). ⚠ Do NOT "
            f"close this by making the QUERY double-count too — that agrees, and keeps the "
            f"black hole"
        )

    async def test_POSITIVE_CONTROL_a_DUPLICATED_UNRESOLVED_blocker_stays_BLOCKED_in_BOTH(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """The control the leg above needs: a build that simply stopped counting blockers —
        or that answered ``claimable`` for every legacy row — passes it.

        Identical fixture, identical shape, ONE variable: the duplicated blocker is ``open``
        instead of ``done``.  ``array::distinct`` must make a duplicate harmless, never make
        a dependency disappear.
        """
        ledger, env, _seed = task_ledger
        legacy_id, blocker = await self._legacy_row_with_duplicate(
            ledger, env, blocker_status=STATUS_OPEN
        )
        unblocked = {task.id for task in await ledger.query_tasks(blocked=False)}
        served_unblocked = legacy_id in unblocked
        claim = await ledger.claim_task(legacy_id, ACTOR)
        assert (served_unblocked, claim.claimed) == (False, False), (
            f"blocked_by=[X, X] with X ({blocker!r}) still OPEN: query_tasks(blocked=False) "
            f"says unblocked={served_unblocked}, the claim CAS says claimed={claim.claimed}. "
            f"De-duplicating the dependency list must not DROP the dependency — a build that "
            f"resolved a duplicate by ignoring the entry fails closed in the fail-OPEN "
            f"direction, which is worse than the divergence T5 closes"
        )

    async def test_EXACTLY_ONE_of_EIGHT_racers_wins_a_row_with_a_DUPLICATED_blocker(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **T5's concurrency clause — the CAS is LIVE code and this changes it.**

        ``array::len(array::distinct(blocked_by))`` sits inside ``_claim_fragment``'s
        compare-and-set, the one statement standing between two agents claiming the same
        work.  A change there is not "one line" in risk terms, so the standard is the one
        the repo already demands for a claim path: **≥8-way**, on **8 SEPARATE live
        connections** (not eight coroutines on one socket — only separate sessions actually
        exercise the server-side CAS + optimistic-concurrency retry), **× 20 consecutive
        green runs**, per the protocol in the class docstring.

        THE ASSERTION IS EXACTLY-ONE, in both directions.  ``> 1`` is a broken CAS: two
        agents doing the same work, the failure this primitive exists to prevent.  ``0`` is
        the T5 defect itself, unfixed — the row is fully resolved and nobody can take it —
        and a pin asserting only ``<= 1`` would be GREEN on today's tree, which is the
        no-discrimination shape this contract's own law forbids.
        """
        ledger, env, _seed = task_ledger
        legacy_id, blocker = await self._legacy_row_with_duplicate(
            ledger, env, blocker_status=STATUS_DONE
        )

        racers = [
            TaskLedger(
                url=env.url,
                namespace=env.namespace,
                database=env.database,
                user=env.user,
                password=env.password,
            )
            for _ in range(DUPLICATE_BLOCKER_RACERS)
        ]
        try:
            # ⚠ SETUP IS SERIAL AND ONLY THE CLAIMS RACE, deliberately. ``ensure_ready``
            # runs the bootstrap DDL, and ``CLAUDE.md`` records that an unretried bootstrap
            # loses 6.2%–34.4% of concurrent virgin first-connects on ``use()``. That
            # contention has NOTHING to do with the property under test, and folding it in
            # would make a pin that must survive 20 consecutive runs flaky for a reason its
            # failure message does not name — which is how a real concurrency defect gets
            # dismissed as "flaky" (the C1 mint defect, verbatim).
            for racer in racers:
                await racer.ensure_ready()
            results = await asyncio.gather(
                *(
                    racer.claim_task(legacy_id, f"racer-{index}")
                    for index, racer in enumerate(racers)
                )
            )
        finally:
            await asyncio.gather(*(racer.close() for racer in racers), return_exceptions=True)

        winners = [index for index, result in enumerate(results) if result.claimed]
        assert len(winners) == 1, (
            f"{len(winners)} of {DUPLICATE_BLOCKER_RACERS} racers claimed task {legacy_id!r}, "
            f"whose blocked_by is [X, X] with X ({blocker!r}) done. Exactly one must win.\n"
            f"  ZERO winners is the T5 defect itself — array::len(blocked_by)=2 never equals "
            f"the DISTINCT resolved count of 1, so a fully-resolved task is unclaimable "
            f"forever while query_tasks serves it as claimable.\n"
            f"  MORE THAN ONE is a broken compare-and-set: two agents are now doing the same "
            f"work, which is the whole failure this primitive exists to prevent — and it "
            f"would mean array::distinct was added OUTSIDE the atomic statement.\n"
            f"  ⚠ A single green run NEVER clears this pin: 20 consecutive runs, and a red "
            f"run is a STOP, not a 'flaky'. winners={winners}"
        )
        persisted = await ledger.get_task(legacy_id)
        assert persisted.owner == f"racer-{winners[0]}", (
            f"the winning claim reported racer-{winners[0]} but the persisted row names "
            f"{persisted.owner!r} — the CAS and the row it writes disagree"
        )


# =========================================================================== #
# SECTION J — RULING T2: A RAW ``(unspecified rejection)`` REACHING A CALLER IS A DEFECT.
#
# Ruling **T2** (2026-07-28, from design sidecar §5.4, "MP-3 generalised"), verbatim:
# *"On every verb this packet touches, each caller-reachable engine rejection is either
# pre-checked into a teaching refusal or classified into a teaching error.  An
# undiagnosable error is the anti-teaching surface: the agent cannot tell its own mistake
# from a broken tool, and the measured consult behaviour is that it blames the tool."*
#
# ⚠ IT IS PINNED AS A PROPERTY OVER THE VERBS, NOT AS A CASE.  The enumeration below is a
# name-keyed table and that is stated rather than hidden — the repo's instrument lesson says
# a name list is the shape with the most receipts against it.  Two things bound the damage,
# and neither is a promise to remember:
#
#   * :class:`TestEveryCallerReachableRefusalTEACHES`'s verb-adjudication leg
#     derives the verb set FROM ``TaskLedger``'s own AST, exactly as SECTION D's mirror
#     adjudication does, and requires every public verb to be in exactly one bucket — so a
#     sixth verb cannot silently arrive with an unlaundered engine door.
#   * the POSITIVE CONTROL proves the hygiene text is REAL and REACHABLE (neutralise the
#     pre-check and the same call serves it), so the negative legs cannot pass vacuously.
#     A probe needs a control: "the bad string was absent" is worth nothing until you have
#     shown the instrument can see it present.
#
# ⚠ MEASURED HERE, 2026-07-28, against spike-surreal 3.2.1 (``ws://127.0.0.1:18000``, the
# TEST store) — because ``docs/reference/surrealdb-31-capabilities.md`` documents no ``LIMIT``
# behaviour at all and ruling R5/R9's newly-accepted parameter goes straight into one:
#
#     SELECT * FROM t LIMIT $k, $k = 3    -> 3 rows
#     SELECT * FROM t LIMIT $k, $k = 0    -> 0 rows, no error
#     SELECT * FROM t LIMIT $k, $k = -1   -> InternalError: LIMIT/START must be a
#                                            non-negative integer, got -1
#     SELECT * FROM t LIMIT $k, $k = NONE -> 0 rows, NO ERROR
#
# TWO consequences the builder needs, and neither was written down anywhere before:
#   1. A NEGATIVE ``limit`` is a genuine ENGINE REJECTION on a newly-widened public
#      parameter — T2's exact scope, and pinned below.
#   2. **A ``NONE`` limit bound into the statement serves NOTHING, silently.**  So the
#      obvious build — always emit ``LIMIT $limit`` and bind ``None`` when the caller passed
#      no cap — turns EVERY unlimited query into an empty answer with no error anywhere.
#      That build is killed by ``test_query_tasks_bounded.py``'s
#      ``TestTheLimitIsPUSHEDINTOTheStatement``'s UNLIMITED positive control, whose
#      docstring now names this measurement as the mechanism it catches.
# =========================================================================== #


def _engine_hygiene_markers() -> tuple[str, ...]:
    """The store seam's caller-facing hygiene strings — READ FROM PRODUCTION, never retyped.

    ``loremaster.store._txn`` owns the hygiene boundary (ledger #31): a rolled-back
    statement is served to the caller as a short generic CLASS plus a pointer at the server
    log, and the raw engine text — which can carry an interpolated value — is withheld.
    That is correct FOR THE STORE and catastrophic for a LEDGER CALLER, who is an agent with
    no server log and no way to tell its own bad input from a broken tool.

    ⚠ CALL-TIME import, for :func:`_shared_policy`'s reason (finding #133): a module-level
    import of a name that is later renamed makes this whole file UNCOLLECTABLE rather than
    RED, and an uncollectable file DELETES its pins from the run instead of failing them.

    ⚠ Derived rather than copied so a rename in production reddens these pins loudly instead
    of leaving them asserting the absence of a string nothing produces any more — which is
    how a served-English pin quietly stops discriminating.
    """
    import importlib

    txn = importlib.import_module("loremaster.store._txn")
    markers = (
        getattr(txn, "_ERROR_CLASS_UNSPECIFIED", None),
        getattr(txn, "_SERVER_LOG_HINT", None),
    )
    assert all(isinstance(marker, str) and marker for marker in markers), (
        "loremaster.store._txn no longer exposes _ERROR_CLASS_UNSPECIFIED / _SERVER_LOG_HINT "
        f"as non-empty strings ({markers!r}). This pin family asserts that neither string "
        "reaches a ledger caller; if they were renamed, re-point this accessor in the same "
        "commit — an absent marker makes every leg below pass vacuously"
    )
    return tuple(str(marker) for marker in markers)


#: A ``limit`` the engine itself refuses — MEASURED (SECTION J's header), not assumed.
#: Negative rather than zero because ``LIMIT 0`` is ACCEPTED by the engine (0 rows, no
#: error), so zero cannot discriminate a laundered rejection from a legal empty answer.
#: Whether ``limit=0`` should ALSO be refused is UNRULED and is escalated, not pinned.
_ILLEGAL_LIMIT = -1


async def _create_one(ledger: TaskLedger, *, blocked_by: list[str]) -> list[str]:
    """One ``create_many`` item carrying ``blocked_by`` — the batch path in one call."""
    from loremaster.tasks import TaskSpec

    return await ledger.create_many(
        [TaskSpec(subject=SUBJECT, description=DESCRIPTION, blocked_by=blocked_by)],
        created_by=CREATOR,
    )


#: Public ``TaskLedger`` verbs with a caller-reachable ENGINE-rejection or pre-check door
#: that ruling **T2** governs, each with the input that provokes it.  Every entry is a
#: ``(verb, label, offending token, provoke)`` row; ``provoke`` takes the ledger and a REAL
#: blocker id and returns the awaitable that must refuse.
#:
#: ⚠ The ``layer`` column is deliberate.  T2 accepts EITHER *"pre-checked into a teaching
#: refusal"* OR *"classified into a teaching error"*, and knowing which layer is supposed to
#: catch each door is what makes a failure diagnosable — an ``engine`` row that stops
#: refusing means the pre-check vanished, an ``app`` row that stops refusing means the
#: policy did.
ENGINE_REJECTION_PATHS: tuple[tuple[str, str, str, str, Callable[..., Any]], ...] = (
    (
        "create_task",
        "phantom blocker",
        "engine",
        PHANTOM_TASK_ID_UUID_SHAPE,
        lambda ledger, _real: ledger.create_task(
            SUBJECT, DESCRIPTION, blocked_by=[PHANTOM_TASK_ID_UUID_SHAPE], created_by=CREATOR
        ),
    ),
    (
        "create_many",
        "phantom blocker",
        "engine",
        PHANTOM_TASK_ID_KEY_SHAPE,
        lambda ledger, _real: _create_one(ledger, blocked_by=[PHANTOM_TASK_ID_KEY_SHAPE]),
    ),
    (
        "query_tasks",
        "negative limit",
        "engine",
        str(_ILLEGAL_LIMIT),
        lambda ledger, _real: ledger.query_tasks(limit=_ILLEGAL_LIMIT),
    ),
    (
        "transitive_blockers",
        "max_depth past the engine ceiling",
        "engine",
        str(ENGINE_RECURSION_CEILING + 1),
        lambda ledger, real: _transitive_blockers(
            ledger, real, max_depth=ENGINE_RECURSION_CEILING + 1
        ),
    ),
    (
        "transitive_blockers",
        "unknown task id",
        "app",
        PHANTOM_TASK_ID_NUMERIC_SHAPE,
        lambda ledger, _real: _transitive_blockers(ledger, PHANTOM_TASK_ID_NUMERIC_SHAPE),
    ),
)

#: Public ``TaskLedger`` verbs adjudicated as having NO caller-reachable engine-rejection
#: door this packet opens.  Declared explicitly rather than left off a list: an omission and
#: a considered "nothing to launder here" look identical in a name-keyed table, and only one
#: of them is a decision.
#:
#: ⚠ ``ensure_ready`` was RE-ADJUDICATED after ruling R11 gave it a BACKFILL (SECTION K),
#: and it stays here deliberately: R11's new failure surface is provoked by a DEGRADED
#: dependency, never by caller input, so there is no input a caller could supply to reach
#: it and no offending token a refusal could carry back.  Its degraded leg is pinned where
#: it belongs — ``TestTheBackfillRoutesThroughTheSHAREDExistencePolicy::
#: test_a_FAILED_existence_read_makes_ensure_ready_LOUD_not_SILENTLY_PARTIAL`` — rather
#: than bent into this table's ``(verb, offending token, provoke)`` shape, which would have
#: required inventing a token no caller ever types.
VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH = frozenset(
    {
        "close",
        "ensure_ready",
        "get_task",
        "claim_task",
        "transition",
        "supersede_task",
        "updated_since",
    }
)

class TestEveryCallerReachableRefusalTEACHES:
    """RED at ``5a2dca9``.  ⛔ **Ruling T2** — the anti-teaching surface, pinned as a ∀.

    THE CONSUMER IS AN AGENT.  ``statement 2 of 3 was rejected (unspecified rejection); see
    the server log for the full engine detail`` is, to that reader, indistinguishable from
    *"lore is broken"* — and the measured consult behaviour on an undiagnosable error is
    that it **blames the tool** and routes around it.  Under the trust doctrine that is not
    a cosmetic failure; it is the failure.

    Each leg asserts three things about what the CALLER receives, and each kills a different
    wrong build:

    1. **the ledger's OWN vocabulary** (``TaskLedgerError``) — kills the build that lets the
       store's exception through unlaundered.  ⚠ This is the load-bearing one, and a
       "names the value" check alone does NOT cover it: the engine's own text for a bad
       ``LIMIT`` is *"LIMIT/START must be a non-negative integer, got -1"*, which names the
       value perfectly well while telling an agent nothing about which of ITS parameters was
       wrong.  MEASURED, this file's SECTION J header.
    2. **no hygiene marker** — kills the build that catches the store error and re-raises it
       as a ledger error with the same undiagnosable body.
    3. **the offending token, verbatim** — kills the build that teaches generically
       (*"invalid dependency"*) and leaves a caller holding a 20-item batch with nothing to
       edit.  RIDER-E's property, applied across every refusal cause.
    """

    @pytest.mark.parametrize(
        ("verb", "label", "layer", "offending", "provoke"),
        ENGINE_REJECTION_PATHS,
        ids=[f"{verb}-{label.replace(' ', '_')}" for verb, label, _, _, _ in ENGINE_REJECTION_PATHS],
    )
    async def test_the_caller_receives_a_TEACHING_refusal_not_ENGINE_HYGIENE(
        self,
        task_ledger: tuple[TaskLedger, SurrealEnv, str],
        verb: str,
        label: str,
        layer: str,
        offending: str,
        provoke: Callable[..., Any],
    ) -> None:
        ledger, _env, real_blocker = task_ledger
        with pytest.raises(TaskLedgerError) as caught:
            await provoke(ledger, real_blocker)
        message = str(caught.value)
        for marker in _engine_hygiene_markers():
            assert marker not in message, (
                f"{verb} ({label}, expected to be caught at the {layer} layer) served the "
                f"caller the store's hygiene text {marker!r}. An agent holding this cannot "
                f"tell its own bad input from a broken tool, has no server log to read, and "
                f"the measured behaviour is that it blames the tool and routes around it "
                f"(ruling T2). Pre-check it into a teaching refusal, or classify it into a "
                f"teaching error: {message!r}"
            )
        assert offending in message, (
            f"{verb} ({label}) refused without naming {offending!r} — the value the caller "
            f"supplied. A refusal that does not carry the offending token back is not "
            f"actionable in one edit (RIDER-E): {message!r}"
        )

    async def test_EVERY_public_TaskLedger_verb_is_ADJUDICATED_for_engine_rejections(
        self,
    ) -> None:
        """⛔ Coverage as a CHECKED VARIABLE, deny-by-default — SECTION D's instrument,
        pointed at T2 instead of at the mirror.

        T2 says *"on every verb this packet touches"*, and *"every"* is only a quantifier if
        something enumerates the set.  The verb set is DERIVED from ``TaskLedger``'s own AST,
        so a verb added next packet lands in neither bucket and reddens here, rather than
        arriving with an unlaundered engine door nobody listed.

        ⚠ **STATED BOUND, because a gate that overstates its reach is what this repo
        polices:** this proves every verb is ADJUDICATED, not that every rejection path
        WITHIN an adjudicated verb was found. The table above is a name list and it is
        labelled as one; what it buys is that the *verbs* cannot silently grow.

        RED at ``5a2dca9`` for one reason: ``transitive_blockers`` does not exist yet.
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
        with_a_door = {verb for verb, _label, _layer, _offending, _provoke in ENGINE_REJECTION_PATHS}
        declared = with_a_door | VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH
        assert public_async == declared, (
            "TaskLedger's public async verb set drifted from ruling T2's adjudication. "
            f"On the class but NOT adjudicated: {sorted(public_async - declared)}. "
            f"Adjudicated but NOT on the class: {sorted(declared - public_async)}. Every "
            "verb belongs in exactly one of ENGINE_REJECTION_PATHS (has a caller-reachable "
            "rejection door, and here is the input that provokes it) or "
            "VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH (considered, and there is none) — an "
            "omission and a decision must not look the same"
        )
        assert not (with_a_door & VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH), (
            "a verb is declared BOTH as having a rejection door and as having none: "
            f"{sorted(with_a_door & VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH)}"
        )

    async def test_POSITIVE_CONTROL_the_hygiene_text_IS_reachable_when_the_precheck_is_GONE(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔⛔ **THE CONTROL WITHOUT WHICH EVERY LEG ABOVE IS WORTHLESS.**

        Each leg above is a NEGATIVE result — *"the hygiene marker was absent"* — and a
        negative result from a blind instrument is indistinguishable from one from a working
        instrument.  If ``_ERROR_CLASS_UNSPECIFIED`` were never what this seam produces, or
        if the engine simply accepted a phantom endpoint, every assertion above would pass
        for a reason that has nothing to do with the code being right.

        So: neutralise the shared pre-check, make the SAME call, and show that the caller is
        now served the store's hygiene text — proving (a) the marker is real and is what
        this path produces, (b) the pre-check is the ONLY thing standing between an agent
        and it, and therefore (c) the negative legs measure something.

        ⚠ The assertion is on the SERVER-LOG HINT rather than on a particular error CLASS
        label: ``_classify_engine_error`` picks its label by matching engine text, and which
        label an ``ENFORCED`` rejection earns is a measurement this contract does not own.
        The hint is appended to EVERY classified rollback message whatever the class, so it
        is the marker that cannot drift out from under this control.
        """
        ledger, _env, _blocker = task_ledger
        _neutralise_the_policy(monkeypatch, "loremaster.tasks")
        with pytest.raises(SurrealStoreError) as caught:
            await ledger.create_task(
                SUBJECT,
                DESCRIPTION,
                blocked_by=[PHANTOM_TASK_ID_UUID_SHAPE],
                created_by=CREATOR,
            )
        message = str(caught.value)
        _unspecified, server_log_hint = _engine_hygiene_markers()
        assert server_log_hint in message, (
            f"with the pre-check neutralised, a phantom blocker did NOT produce the store's "
            f"hygiene text — so the negative legs in this class are asserting the absence of "
            f"a string this path never produces, and they discriminate nothing. Either the "
            f"engine now accepts a dangling `blocks` endpoint (a far worse finding — see "
            f"TestTheBlocksEdgeIsGuardedFromBirth) or the seam's error hygiene changed: "
            f"{message!r}"
        )
        assert PHANTOM_TASK_ID_UUID_SHAPE not in message, (
            f"the store's own rejection message carried the offending id back to the caller. "
            f"That is not a licence to skip the app pre-check — the hygiene boundary exists "
            f"precisely because engine text can leak an interpolated VALUE, and a build that "
            f"relies on it is relying on a string the store is designed to withhold: "
            f"{message!r}"
        )

    async def test_a_ghost_SENDER_is_refused_in_the_MESSAGE_ledgers_OWN_vocabulary(
        self, message_ledger_with_a_real_agent: tuple[Any, str, SurrealEnv]
    ) -> None:
        """T2 over the OTHER ledger this packet touches (#247, operator ruling R2).

        Same property, different vocabulary — so it is a separate leg rather than a row in
        the table above: a ``MessageLedger`` caller catches ``MessageLedgerError``, and
        forcing both families through one parametrisation would have meant asserting a base
        class this contract does not rule on.
        """
        ledger, registered, _env = message_ledger_with_a_real_agent
        ghost = UNREGISTERED_SENDER_IDS[0]
        with pytest.raises(Exception) as caught:  # noqa: B017 - the TYPE has its own pin in §H
            await ledger.send(
                sender=_Ref(ghost, "phantom-lead"),
                session="wave7",
                body="a message from nobody",
                grade="signal",
                recipients=[_Ref(registered, "fixer-b")],
            )
        message = str(caught.value)
        for marker in _engine_hygiene_markers():
            assert marker not in message, (
                f"the ghost-sender refusal served the store's hygiene text {marker!r}. The "
                f"`to` edge is ENFORCED, so an unvalidated sender reaches the engine and the "
                f"seam launders its rejection into exactly this — which teaches an agent "
                f"nothing about the parameter it got wrong (ruling T2): {message!r}"
            )
        assert ghost in message, (
            f"the refusal does not name the unresolved sender {ghost!r}: {message!r}"
        )


# =========================================================================== #
# SECTION K — RULING R11: THE ``ensure_ready`` BACKFILL, AND THE DEGRADED WORLD
# THAT DEPLOYS ITSELF.
#
# ⚠⚠ SIDECAR FINDING S3 (packet §04b SPLIT, BLOCKER) — the defect that got past the
# contract, the contract-adversary, TWO contract-fix waves and the lead, and became
# visible only under ``CLAUDE.md``'s TRUST — THE HARD DEFINITION (leg 2):
#
#   The ``blocks`` mirror is ∀ verbs going FORWARD.  Production tasks carry ``blocked_by``
#   COLUMNS TODAY and will have NO ``blocks`` EDGES at deploy.  The transitive read rides
#   EDGES by design.  So the served answer, for exactly the rows the fleet is working, is
#   ``ids=[] truncated=False`` — clean, confident, WRONG.  ``truncated=False`` is not a
#   missing bound; it is a POSITIVE ASSERTION OF COMPLETENESS THAT IS FALSE, which is the
#   definition's central failure.
#
# It is worse than an ordinary forgery-pin gap, and the reason is worth keeping: every
# other owed construction has to be CONSTRUCTED.  **This degraded world needs no
# constructing — it is the default state at deploy.**
#
# ✅ RULING R11 (operator, 2026-07-28) adopts the sidecar's recommendation IN FULL — *fix
# the defect; do not disclose it*:
#   * mint the missing ``blocks`` edges from the existing ``blocked_by`` columns AT
#     MIGRATION TIME, inside ``TaskLedger.ensure_ready``;
#   * PRE-FILTERED through the L3 existence policy — ⚠ legacy rows carry PHANTOM blockers
#     (``blocked_by`` was FAIL-OPEN at write until this packet), phantoms meet ``ENFORCED``,
#     and a NAKED backfill therefore ROLLS BACK THE ENTIRE one-transaction migration.  That
#     failure mode is pinned BELOW as a BASELINE with its own positive control, so "the
#     backfill skipped the phantom" cannot pass for a fixture reason;
#   * phantom skips are RECORDED, never silent — *"a silent skip is a false clear in the
#     exact shape S3 identifies"*;
#   * IDEMPOTENT: ``ensure_ready`` runs at EVERY boot, and store reference §4 records that
#     ``UNIQUE(in, out)`` on a relation edge makes a duplicate a LOUD ERR — so a second boot
#     must neither raise nor double-mint;
#   * forgery-pinned in the dirty-store harness that ALREADY EXISTS.  ``_seed_legacy_task``
#     already constructs the production-real partial world; the instrument was built and was
#     simply never pointed at the traversal.
#   Rejected by the same ruling, recorded so neither is re-litigated: *render-names-the-
#   bound* (legal under the definition, but a permanent tax on every future read for a
#   one-time migration we declined to run) and *a separate one-shot script* (a deploy that
#   forgets it silently reproduces the defect with no signal).
#
# THE FIXTURE FLOOR IS THE PACKET'S, UNCHANGED: ≥3 deep AND branching.  A backfill that
# minted the transitive CLOSURE as direct edges, or one that stopped at the first hop, is
# indistinguishable from correct on a 2-node chain — so the legacy world below is the same
# 4-deep diamond ``branching_dag`` uses, written as COLUMNS ONLY.
#
# RED TODAY: every pin except the three BASELINE/CONTROL legs named in their docstrings.
# =========================================================================== #


#: The legacy DAG the backfill must reconstruct, as ``{task: (blockers,)}`` — COLUMNS ONLY,
#: no edges anywhere.  4 deep, branching, and a diamond (``root`` is reachable from ``leaf``
#: by two paths), so a one-hop backfill, a closure-minting backfill and a correct one all
#: serve DIFFERENT answers.
LEGACY_COLUMN_DAG: dict[str, tuple[str, ...]] = {
    "root": (),
    "left": ("root",),
    "right": ("root",),
    "middle": ("left", "right"),
    "leaf": ("middle",),
}

#: The legacy row carrying ONE resolvable blocker and ONE PHANTOM.  Production's real shape,
#: and the row that decides whether the whole migration lands or rolls back.
LEGACY_MIXED_TASK = "mixed"

#: A legacy row in a TERMINAL status that still carries a real ``blocked_by`` entry.  It is
#: here because *"backfill only the tasks that are still open"* is a plausible wrong build
#: that the DAG above cannot see: every row in it is ``open``.  The mirror is over the
#: COLUMN, ∀ rows, whatever their status.
LEGACY_TERMINAL_TASK = "terminal"


def _row_key(value: Any) -> str:
    """The bare row key of a record reference, however the SDK hands it back.

    ``str(record.id)``, never a ``split(':')`` — store reference §7 (``RecordID`` is
    UNHASHABLE on SDK 2.0.0 and its rendered form is not a parsing contract).  A value that
    is not a ``RecordID`` falls through as its own ``str``, so a shape change reddens the
    comparing pin with a readable diff instead of being silently normalised away.
    """
    identifier = getattr(value, "id", None)
    return str(identifier) if identifier is not None else str(value)


async def _blocks_edge_pairs(connection: SurrealConnection) -> set[tuple[str, str]]:
    """Every ``blocks`` edge as a ``(blocker_key, blocked_key)`` pair.

    ⚠ Direction is escalation **E-1**'s: ``RELATE $blocker->blocks->$task``, so ``in`` is
    the BLOCKER and ``out`` is the task that is blocked.  A pin comparing an unordered set
    of ids could not tell a correct backfill from one that RELATEs every pair backwards.

    RAW rather than traversed, for :func:`_blocks_edge_count`'s reason: store reference §6.4
    MEASURED that a traversal lists a dangling endpoint as a first-class member, so counting
    and reading the edge ROWS is the only reading that answers *"what actually landed"*.
    """
    rows = await run(connection, f"SELECT in, out FROM {BLOCKS_RELATION_NAME}")
    pairs: set[tuple[str, str]] = set()
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict):
            pairs.add((_row_key(row.get("in")), _row_key(row.get("out"))))
    return pairs


async def _blocks_edge_pairs_or_NO_TABLE(connection: SurrealConnection) -> set[tuple[str, str]]:
    """:func:`_blocks_edge_pairs`, tolerating a store whose edge table does not EXIST YET.

    ⚠ **MEASURED 2026-07-28 on spike-surreal 3.2.1, and it CONTRADICTS what this section's
    author first assumed** (the assumption cost 13 fixture errors, which is how it was
    found): ``SELECT … FROM blocks`` against a store with no ``blocks`` table **RAISES**
    ``NotFoundError: The table 'blocks' does not exist``.  It does NOT return an empty list.
    Store reference §5's auto-creation is a property of a *write* (``RELATE``), never of a
    read.

    Used ONLY by the PRE-migration legs.  Every post-migration assertion uses the strict
    reader, because once ``ensure_ready`` has run an absent edge table is a DEFECT and
    laundering it into *"zero edges"* would be this file's own false-clear class.
    """
    try:
        return await _blocks_edge_pairs(connection)
    except Exception as error:  # noqa: BLE001 - narrowed immediately, and loudly
        assert "does not exist" in str(error), (
            f"reading the blocks edge table failed for a reason OTHER than the table being "
            f"absent, and this helper must never swallow that: {error!r}"
        )
        return set()


def _expected_backfilled_pairs(ids: dict[str, str]) -> set[tuple[str, str]]:
    """EXACTLY the ``(blocker, blocked)`` pairs a correct backfill mints for the fixture.

    An EXACT set, not a superset: a build that minted the transitive CLOSURE as direct
    edges would serve the right ``transitive_blockers`` answer while breaking the
    edge ≡ ``blocked_by`` mirror this packet exists to establish, and only an exact-set
    comparison can tell them apart.  The phantom pair is absent BY CONSTRUCTION — it is
    what R11 requires to be skipped.
    """
    pairs = {
        (ids[blocker], ids[task])
        for task, blockers in LEGACY_COLUMN_DAG.items()
        for blocker in blockers
    }
    pairs.add((ids["root"], ids[LEGACY_MIXED_TASK]))
    pairs.add((ids["root"], ids[LEGACY_TERMINAL_TASK]))
    return pairs


def _served_shape(outcome: Any) -> str:
    """The SHAPE a consumer acts on, rendered so two worlds can be BYTE-DIFFED.

    The trust definition's leg 2 compares the DEGRADED response against the HEALTHY one and
    treats **identical bytes as a FALSE CLEAR**.  A ``TransitiveBlockers`` and a raised
    error are both *"what the caller got"*, so both render through here — otherwise the
    comparison could only be made where the shapes already match, which is the half of the
    space where the answer is obvious.
    """
    if isinstance(outcome, Exception):
        return f"RAISED {type(outcome).__name__}: {outcome}"
    return (
        f"OK ids={sorted(getattr(outcome, 'ids', []))} "
        f"truncated={getattr(outcome, 'truncated', None)!r} "
        f"max_depth_used={getattr(outcome, 'max_depth_used', None)!r}"
    )


async def _served_outcome(awaitable: Any) -> str:
    """Await ``awaitable`` and render whatever the caller ends up holding."""
    try:
        return _served_shape(await awaitable)
    except Exception as error:  # noqa: BLE001 - a failure IS part of the served shape
        return _served_shape(error)


def _patch_every_shared_policy_COROUTINE(
    monkeypatch: pytest.MonkeyPatch, replacement: Callable[..., Any]
) -> tuple[str, ...]:
    """Replace EVERY public coroutine the shared existence-policy module owns.

    DERIVED, never a name list, and applied at BOTH addresses — the policy module itself
    AND every name in ``loremaster.tasks`` bound to a coroutine that module DEFINES —
    because ``from … import name`` COPIES the reference, so patching only the module leaves
    an already-bound caller untouched.

    ⚠ Name-free BY CONSTRUCTION, and that is the point.  R11 requires the backfill's phantom
    filter to route through this module (L3 — ONE IMPLEMENTATION), but the builder must
    spell a NON-RAISING probe (``reject_unknown_rows`` raises; a filter needs the set of ids
    that resolved).  Keying this on a name would pin a spelling nobody has chosen yet, and
    CLAUDE.md's instrument lesson records six separate gates defeated by exactly that.

    Returns the patched addresses, for the caller's failure message.  Fails CLOSED: an empty
    derivation reddens rather than making its caller pass vacuously.
    """
    import importlib

    policy_module = importlib.import_module(SHARED_POLICY_MODULE)
    tasks_module = importlib.import_module("loremaster.tasks")
    patched: list[str] = []
    for name, value in list(vars(policy_module).items()):
        if name.startswith("_") or not inspect.iscoroutinefunction(value):
            continue
        monkeypatch.setattr(policy_module, name, replacement, raising=True)
        patched.append(f"{SHARED_POLICY_MODULE}.{name}")
    for name, value in list(vars(tasks_module).items()):
        if not inspect.iscoroutinefunction(value):
            continue
        if getattr(value, "__module__", None) != SHARED_POLICY_MODULE:
            continue
        monkeypatch.setattr(tasks_module, name, replacement, raising=True)
        patched.append(f"loremaster.tasks.{name}")
    assert patched, (
        f"no public coroutine was found in {SHARED_POLICY_MODULE} (nor any name in "
        f"loremaster.tasks bound from it), so this degradation patched NOTHING and every "
        f"assertion resting on it would pass vacuously. L3 rules the row-existence policy "
        f"to be ONE implementation living there; if it moved, re-point "
        f"SHARED_POLICY_MODULE in the same commit"
    )
    return tuple(patched)


def _degrade_every_STORE_seam(
    monkeypatch: pytest.MonkeyPatch, replacement: Callable[..., Any]
) -> tuple[str, ...]:
    """Replace every ``loremaster.store._txn`` coroutine ``loremaster.tasks`` imported.

    DERIVED the same way and for the same reason: the seam set is *"module-level names in
    ``loremaster.tasks`` that are coroutine functions DEFINED IN ``loremaster.store._txn``"*.
    A builder who adds ``execute_read_transaction`` for ruling R7 (escalation ESC-4) is
    covered automatically — a hand-written ``{"run_query", "execute_transaction"}`` would
    have gone blind on exactly the seam R7 introduces.

    ⚠ **THE CALLER MUST ALREADY HOLD A LIVE CONNECTION.**  ``bootstrap_session`` is one of
    the derived seams, so degrading before the first connect fails at the socket instead of
    at the read under test.  Every caller below drives a fixture that has already connected.

    Fails CLOSED, twice: an empty derivation reddens, and so does one that does not include
    the single-statement seam every ledger read rides.
    """
    import importlib

    tasks_module = importlib.import_module("loremaster.tasks")
    patched: list[str] = []
    for name, value in list(vars(tasks_module).items()):
        if not inspect.iscoroutinefunction(value):
            continue
        if getattr(value, "__module__", None) != "loremaster.store._txn":
            continue
        monkeypatch.setattr(tasks_module, name, replacement, raising=True)
        patched.append(name)
    assert "run_query" in patched, (
        f"the derived store-seam set {sorted(patched)} does not contain run_query, so this "
        f"degradation does not reach the ledger's single-statement reads and every "
        f"assertion resting on it passes vacuously"
    )
    return tuple(patched)


def _recorded_text(record: logging.LogRecord) -> str:
    """A log record's FULL surface — its message AND every value it carries in ``extra``.

    The repo's structured-logging idiom puts an EVENT NAME in the message and the data in
    ``extra`` (``logger.debug("task.schema.ready", extra={"database": …})``), so a pin that
    read only ``getMessage()`` would call a perfectly loud record silent.  Reading both
    keeps this pin tolerant of the builder's choice while still discriminating: a skip that
    is recorded NOWHERE fails it.
    """
    standard = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__)
    extras = {key: value for key, value in record.__dict__.items() if key not in standard}
    return f"{record.getMessage()} {extras!r}"


@pytest_asyncio.fixture()
async def legacy_column_store(
    migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the imported fixture
) -> AsyncIterator[tuple[SurrealConnection, SurrealEnv, dict[str, str]]]:
    """The world 04b-1 DEPLOYS INTO: ``blocked_by`` COLUMNS, and ZERO ``blocks`` edges.

    Built through :func:`_seed_legacy_task`, which is production's own shape and not a
    contrivance: every ``task`` row written before this packet was written under a
    FAIL-OPEN ``blocked_by``, and #236 rules the cleanup of what such rows left behind OUT.

    The OLD DDL is applied first, so there is no ``blocks`` table at all — a store that has
    never heard of the edge, which is exactly what the production store was measured to be
    at 04b's kickoff (*"``blocks`` is absent from the production store — confirmed, not
    assumed"*).

    Yields ``(connection, env, ids)`` where ``ids`` maps every fixture name — the DAG's five,
    ``LEGACY_MIXED_TASK``, ``LEGACY_TERMINAL_TASK`` and ``"phantom"`` — to its row key.
    """
    connection, env = migration_db
    await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
    names = (*LEGACY_COLUMN_DAG, LEGACY_MIXED_TASK, LEGACY_TERMINAL_TASK)
    ids = {name: f"{name}_{uuid.uuid4().hex}" for name in names}
    ids["phantom"] = ghost_id("ghost_blocker")
    for task, blockers in LEGACY_COLUMN_DAG.items():
        await _seed_legacy_task(
            connection,
            ids[task],
            blocked_by=[ids[blocker] for blocker in blockers],
            status=STATUS_OPEN,
        )
    await _seed_legacy_task(
        connection,
        ids[LEGACY_MIXED_TASK],
        blocked_by=[ids["root"], ids["phantom"]],
        status=STATUS_OPEN,
    )
    await _seed_legacy_task(
        connection,
        ids[LEGACY_TERMINAL_TASK],
        blocked_by=[ids["root"]],
        status=STATUS_DONE,
    )
    assert not await record_exists(connection, TASK_TABLE, ids["phantom"]), (
        "the legacy fixture's phantom blocker must genuinely NOT exist — a fixture whose "
        "every blocker resolves cannot tell a pre-filtered backfill from a naked one"
    )
    assert await _blocks_edge_pairs_or_NO_TABLE(connection) == set(), (
        "the legacy fixture already holds blocks edges, so the backfill it exists to "
        "measure has nothing to do and every pin below passes for a fixture reason"
    )
    yield connection, env, ids


class TestTheLegacyWorldIsGenuinelyTheDEGRADEDOne:
    """GREEN before and after.  The anti-vacuity control for the whole of SECTION K.

    Every pin below asserts that ``ensure_ready`` CHANGES something about a store built by
    ``legacy_column_store``.  If that store already agreed with its columns, the section
    would be measuring a migration against a world that needed none — a fixture that
    guarantees the one condition under which the bug is invisible, which is the class
    THE TEST ENVIRONMENT IS A FICTION exists to name.
    """

    async def test_the_legacy_rows_carry_COLUMNS_and_the_store_carries_NO_EDGES(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        connection, _env, ids = legacy_column_store
        rows = await run(
            connection,
            f"SELECT id, blocked_by FROM {TASK_TABLE} WHERE array::len(blocked_by) > 0",
        )
        with_columns = {_row_key(row["id"]) for row in rows if isinstance(row, dict)}
        expected = {
            ids[name]
            for name, blockers in LEGACY_COLUMN_DAG.items()
            if blockers
        } | {ids[LEGACY_MIXED_TASK], ids[LEGACY_TERMINAL_TASK]}
        assert with_columns == expected, (
            f"the legacy fixture did not produce the column-bearing rows it claims. "
            f"missing={sorted(expected - with_columns)} unexpected="
            f"{sorted(with_columns - expected)}"
        )
        assert await _blocks_edge_pairs_or_NO_TABLE(connection) == set(), (
            "the legacy fixture holds blocks edges before any migration ran"
        )


class TestTheBACKFILLClosesTheLEGACYEdgeGap:
    """RED today.  ⛔ **RULING R11** — the pins that kill the world that deploys itself.

    ⚠ **THE DISCRIMINATION IS A BYTE DIFF BETWEEN TWO CONSTRUCTED WORLDS**, per the trust
    definition's leg 2, not an assertion about one.  World A is production at deploy with
    NO backfill — today's schema applied, legacy columns intact, no edges — and it serves
    ``ids=[] truncated=False``.  World B is the same store after ``ensure_ready``.  If the
    two render the SAME BYTES the backfill did not happen, and *identical bytes are a false
    clear*: the caller cannot tell a task with no blockers from a task whose blockers the
    read cannot see.

    A build that satisfies every OTHER pin in this file — the mirror at every write path,
    the closure operator, the honest bound, the pre-check — still serves world A's answer
    on every row production already holds.  That is the whole of finding S3.
    """

    @staticmethod
    async def _outcome_without_the_backfill(
        connection: SurrealConnection, env: SurrealEnv, task_id: str
    ) -> str:
        """World A: today's SCHEMA, applied directly, and NOTHING else.

        The DDL goes on through :func:`apply_ddl` rather than ``ensure_ready`` precisely
        because ``ensure_ready`` is where R11 puts the backfill — so this is the deploy that
        landed the edge table and no edges, which is what a build without R11 produces at
        every boot.
        """
        await apply_ddl(connection, generate_task_ddl(), url=env.url)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            return await _served_outcome(_transitive_blockers(ledger, task_id))
        finally:
            await ledger.close()

    async def test_WITHOUT_the_backfill_the_traversal_serves_a_CONFIDENT_EMPTY(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        """RED today only because ``transitive_blockers`` does not exist yet; GREEN after,
        and it must STAY green — it describes the ENGINE plus the schema, never the build.

        ⛔ It is the degraded half of the byte diff, and the reason the section is not
        self-congratulatory: it MEASURES the false clear rather than asserting that someone
        avoided it.
        """
        import loremaster.tasks

        connection, env, ids = legacy_column_store
        served = await self._outcome_without_the_backfill(connection, env, ids["leaf"])
        bound = getattr(loremaster.tasks, MAX_DEPTH_CONSTANT)
        assert served == f"OK ids=[] truncated=False max_depth_used={bound!r}", (
            f"world A did not serve the confident empty this section is built around. If "
            f"the traversal now RAISES or reports truncated=True over an edge-less store "
            f"that is a BETTER world than S3 described — but the pins below compare against "
            f"this string, so re-derive them in the same commit. got={served!r}"
        )

    async def test_ensure_ready_BACKFILLS_the_edges_from_the_EXISTING_columns(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        """⛔ The headline, as an EXACT edge set.

        Exact rather than superset: a backfill that minted the transitive CLOSURE as direct
        edges would make ``transitive_blockers`` right and the edge ≡ ``blocked_by`` mirror
        wrong, and the two are indistinguishable to a read-side assertion.
        """
        connection, env, ids = legacy_column_store
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        landed = await _blocks_edge_pairs(connection)
        expected = _expected_backfilled_pairs(ids)
        assert landed == expected, (
            f"ensure_ready did not reconstruct the blocks edges from the legacy blocked_by "
            f"columns (ruling R11).\n"
            f"  MISSING (a column with no edge — the S3 false clear): "
            f"{sorted(expected - landed)}\n"
            f"  UNEXPECTED (an edge with no column — a closure minted as direct edges, or "
            f"the phantom that must be SKIPPED): {sorted(landed - expected)}\n"
            f"Direction is E-1's: (blocker, blocked). phantom={ids['phantom']!r}"
        )

    async def test_the_BACKFILLED_answer_DIFFERS_from_the_UN_backfilled_one(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        """⛔⛔ **THE BYTE DIFF ITSELF**, the leg the trust definition actually demands.

        Two stores, seeded identically, differing in ONE thing: whether the ledger's own
        migration ran.  The second store is minted here with its own env rather than by
        requesting ``migration_db`` a second time — pytest caches a fixture per test, so
        asking for both would hand back ONE store and the "diff" would compare a world with
        itself.  (A backfill is not undoable, so both worlds must genuinely exist.)
        """
        healthy_connection, healthy_env, ids = legacy_column_store
        degraded_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        degraded_connection = await connect_admin(degraded_env)
        try:
            await apply_ddl(degraded_connection, _task_ddl_without_blocks(), url=degraded_env.url)
            for task, blockers in LEGACY_COLUMN_DAG.items():
                await _seed_legacy_task(
                    degraded_connection,
                    ids[task],
                    blocked_by=[ids[blocker] for blocker in blockers],
                    status=STATUS_OPEN,
                )
            degraded = await self._outcome_without_the_backfill(
                degraded_connection, degraded_env, ids["leaf"]
            )
        finally:
            await degraded_connection.close()
            await drop_database(degraded_env)
        assert healthy_connection is not degraded_connection, (
            "the two worlds share one connection, so this pin is comparing a store with "
            "itself"
        )
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(healthy_env)
        try:
            await ledger.ensure_ready()
            healthy = await _served_outcome(_transitive_blockers(ledger, ids["leaf"]))
            result = await _transitive_blockers(ledger, ids["leaf"])
        finally:
            await ledger.close()
        assert healthy != degraded, (
            f"the store WITH the migration and the store WITHOUT it serve BYTE-IDENTICAL "
            f"answers for the same task: {healthy!r}. Under CLAUDE.md's TRUST — THE HARD "
            f"DEFINITION that is a FALSE CLEAR and a STOP: a consumer acting on this "
            f"without checking concludes the task is unblocked, and nothing in the response "
            f"names the reason it might not be. Ruling R11 exists to delete this difference "
            f"rather than disclose it"
        )
        assert set(result.ids) == {ids["middle"], ids["left"], ids["right"], ids["root"]}, (
            f"the backfilled traversal did not serve the legacy row's TRANSITIVE blocker "
            f"set. A one-hop backfill serves {{middle}} alone; a closure-minting one serves "
            f"the right ids off the wrong edges (caught by the exact-set pin above). "
            f"got={sorted(result.ids)}"
        )
        assert result.truncated is False, (
            f"a 4-deep legacy chain read at the default bound reported truncated=True: "
            f"{healthy!r}"
        )

    async def test_the_backfill_covers_a_TERMINAL_row_too_not_only_the_OPEN_ones(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        """The mirror is over the COLUMN, ∀ rows — *"backfill what is still open"* is the
        plausible wrong build the all-``open`` DAG above cannot see, and it would leave a
        ``done`` task's provenance permanently unreadable.
        """
        connection, env, ids = legacy_column_store
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert (ids["root"], ids[LEGACY_TERMINAL_TASK]) in await _blocks_edge_pairs(connection), (
            f"the backfill skipped {LEGACY_TERMINAL_TASK!r}, whose status is "
            f"{STATUS_DONE!r}. The edge ≡ blocked_by mirror is quantified over ROWS, not "
            f"over live ones"
        )


class TestThePHANTOMBlockerIsSKIPPEDAndRECORDED:
    """RED today.  ⛔ R11's two riders — and the second is the one that gets dropped.

    THE RIDER IS PART OF THE RULING (``CLAUDE.md``, six instances in one packet): R11 says
    *"pre-filtered through the L3 existence policy"* **and** *"phantom skips are RECORDED,
    never silent — a silent skip is a false clear in the exact shape S3 identifies"*.  A
    build that implements the clause before the "and" and not the one after it passes every
    other pin in this section.
    """

    async def test_the_PHANTOM_edge_is_NOT_minted_and_the_MIGRATION_STILL_LANDS(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        """⛔ Both halves in one assertion, because either alone admits a wrong build: a
        backfill that skipped EVERYTHING would satisfy "no phantom edge", and one that
        rolled back would satisfy it too — by writing nothing at all.
        """
        connection, env, ids = legacy_column_store
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        pairs = await _blocks_edge_pairs(connection)
        phantom_pairs = {pair for pair in pairs if ids["phantom"] in pair}
        assert phantom_pairs == set(), (
            f"the backfill minted an edge for the PHANTOM blocker {ids['phantom']!r}: "
            f"{sorted(phantom_pairs)}. ENFORCED rejects it (store reference §4), so inside "
            f"the one-transaction migration this rolls the WHOLE thing back — see this "
            f"class's BASELINE sibling"
        )
        assert (ids["root"], ids[LEGACY_MIXED_TASK]) in pairs, (
            f"the mixed row {ids[LEGACY_MIXED_TASK]!r} got no edge for its RESOLVABLE "
            f"blocker either, so the backfill dropped the whole ROW rather than the "
            f"offending ENTRY. R11 pre-filters entries; a row-level skip loses real "
            f"dependencies. pairs={sorted(pairs)}"
        )

    async def test_the_phantom_SKIP_is_RECORDED_never_silent(
        self,
        caplog: pytest.LogCaptureFixture,
        legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]],
    ) -> None:
        """⛔ R11's second rider, and the reason it exists: a skipped entry is a SCOPE BOUND
        on what the edge graph covers, and an unrecorded bound is one nobody can meet
        deliberately.  *"A silent skip is a false clear in the exact shape S3 identifies."*

        ⚠ Asserted over the record's WHOLE surface — message AND ``extra`` — because this
        repo's logging idiom puts the data in ``extra`` (:func:`_recorded_text`).  What is
        pinned is that BOTH ids reach a record at WARNING or above; how the builder spells
        the event is its own.
        """
        _connection, env, ids = legacy_column_store
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        loud = [
            _recorded_text(record)
            for record in caplog.records
            if record.levelno >= logging.WARNING
        ]
        naming_both = [
            text for text in loud if ids["phantom"] in text and ids[LEGACY_MIXED_TASK] in text
        ]
        assert naming_both, (
            f"the backfill skipped a phantom blocker and said NOTHING at WARNING or above. "
            f"R11: phantom skips are RECORDED, never silent. The record must name the "
            f"phantom ({ids['phantom']!r}) AND the task it was skipped for "
            f"({ids[LEGACY_MIXED_TASK]!r}) — an id alone tells an operator which row to "
            f"read but not which dependency vanished. loud records={loud!r}"
        )

    async def test_a_store_whose_blockers_ALL_RESOLVE_records_NO_skip(
        self,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ The control the leg above cannot do without: a build that logs a skip
        UNCONDITIONALLY — or that logs one per row, phantom or not — satisfies it perfectly
        while telling an operator nothing.  Same migration, same shape, no phantom.
        """
        connection, env = migration_db
        await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
        blocker_id = f"clean_blocker_{uuid.uuid4().hex}"
        blocked_id = f"clean_blocked_{uuid.uuid4().hex}"
        await _seed_legacy_task(connection, blocker_id, blocked_by=[], status=STATUS_OPEN)
        await _seed_legacy_task(connection, blocked_id, blocked_by=[blocker_id], status=STATUS_OPEN)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert (blocker_id, blocked_id) in await _blocks_edge_pairs(connection), (
            "the control's own backfill did not run, so its silence proves nothing"
        )
        noisy = [
            _recorded_text(record)
            for record in caplog.records
            if record.levelno >= logging.WARNING and blocked_id in _recorded_text(record)
        ]
        assert not noisy, (
            f"a migration in which EVERY blocker resolved still recorded a warning naming "
            f"{blocked_id!r}: {noisy!r}. A skip notice that fires when nothing was skipped "
            f"is noise an operator learns to ignore — and then the real one is invisible"
        )


class TestTheNakedBackfillWouldRollTheMigrationBack:
    """⛔ The BASELINE that makes R11's pre-filter a REQUIREMENT rather than a stylistic
    preference.

    ⚠ **COLOUR, DERIVED rather than assumed** (an earlier draft of this docstring said
    *"green before and after"* and was wrong): the first leg is **RED at ``70cc5a4``** and
    for a reason worth knowing — today's ``generate_task_ddl`` emits no ``blocks`` table at
    all, so the phantom ``RELATE`` AUTO-CREATES one ``TYPE ANY`` (store reference §5) and is
    accepted.  It goes GREEN the moment the edge ships ``ENFORCED``, and must STAY green.
    The positive control is GREEN before and after.

    R11's load-bearing wrinkle, verbatim: *"legacy rows carry phantom blockers, and those
    meet ``ENFORCED``, so a naked backfill rolls back the whole one-transaction migration"*.
    That is a claim about the ENGINE, and this class MEASURES it — because if it were
    false, *"the phantom was skipped"* would be a nicety instead of the difference between
    a store that migrates and a store that cannot boot.

    Store reference §3: ``execute_transaction`` verifies EVERY statement's status, which is
    why the rejection is visible at all — the SDK's own ``query()`` inspects only the first.
    """

    @staticmethod
    async def _in_one_transaction(
        connection: SurrealConnection, env: SurrealEnv, statement: str, params: dict[str, Any]
    ) -> None:
        """Run ``statement`` as ONE ``BEGIN … COMMIT``, exactly as the migration does."""
        from loremaster.store._txn import _SurrealConnection, execute_transaction

        async def _acquire() -> _SurrealConnection:
            return connection

        async def _never_drop(_connection: _SurrealConnection) -> None:
            raise AssertionError("a statement rejection must never drop the connection")

        await execute_transaction(
            f"BEGIN;\n{statement}COMMIT;\n",
            params,
            acquire=_acquire,
            drop=_never_drop,
            url=env.url,
        )

    async def test_ONE_phantom_RELATE_rolls_back_the_REAL_edges_beside_it(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        connection, env, ids = legacy_column_store
        await apply_ddl(connection, generate_task_ddl(), url=env.url)
        params = {
            "real_from": RecordID(TASK_TABLE, ids["root"]),
            "real_to": RecordID(TASK_TABLE, ids["left"]),
            "ghost_from": RecordID(TASK_TABLE, ids["phantom"]),
            "ghost_to": RecordID(TASK_TABLE, ids[LEGACY_MIXED_TASK]),
        }
        with pytest.raises(Exception):  # noqa: B017 - the seam's own rejection type
            await self._in_one_transaction(
                connection,
                env,
                f"RELATE $real_from->{BLOCKS_RELATION_NAME}->$real_to;\n"
                f"RELATE $ghost_from->{BLOCKS_RELATION_NAME}->$ghost_to;\n",
                params,
            )
        assert await _blocks_edge_pairs(connection) == set(), (
            "the phantom RELATE was rejected but the REAL edge beside it SURVIVED, so the "
            "migration is not one transaction and R11's pre-filter would be optional. "
            "Re-read store reference §3 before trusting any other pin in this section"
        )

    async def test_POSITIVE_CONTROL_the_SAME_transaction_WITHOUT_the_phantom_LANDS(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        """Without this, the leg above is satisfied by a transaction that never works —
        a broken DDL, a wrong endpoint type, a bad parameter binding.  The probe's own §6.2
        lesson: an instrument that fails for the wrong reason reads exactly like one that
        fails for the right one.
        """
        connection, env, ids = legacy_column_store
        await apply_ddl(connection, generate_task_ddl(), url=env.url)
        await self._in_one_transaction(
            connection,
            env,
            f"RELATE $real_from->{BLOCKS_RELATION_NAME}->$real_to;\n",
            {
                "real_from": RecordID(TASK_TABLE, ids["root"]),
                "real_to": RecordID(TASK_TABLE, ids["left"]),
            },
        )
        assert await _blocks_edge_pairs(connection) == {(ids["root"], ids["left"])}, (
            "a transaction holding only REAL endpoints did not land its edge, so the "
            "rejection measured above cannot be attributed to the phantom"
        )


class TestTheBackfillIsIDEMPOTENT:
    """RED today.  ``ensure_ready`` runs at EVERY BOOT.

    Two failure modes, opposite directions, and a single pin catches neither alone: a
    backfill that re-RELATEs unconditionally either DOUBLE-MINTS (no ``UNIQUE(in, out)``) or
    RAISES (with one — store reference §4: *"a duplicate is a loud ERR … the index is a
    correctness backstop, not a de-duplicator you can lean on silently"*).  The first is a
    silently wrong edge graph; the second is a container that boots once and never again.
    """

    async def test_a_SECOND_ensure_ready_neither_RAISES_nor_DUPLICATES(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        connection, env, ids = legacy_column_store
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            after_first = await _blocks_edge_count(connection)
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        after_second = await _blocks_edge_count(connection)
        assert after_first == len(_expected_backfilled_pairs(ids)), (
            f"the first migration minted {after_first} edges where the fixture's columns "
            f"call for {len(_expected_backfilled_pairs(ids))}"
        )
        assert after_second == after_first, (
            f"a SECOND ensure_ready took the blocks edge count from {after_first} to "
            f"{after_second}. ensure_ready runs at every boot, so a backfill that re-mints "
            f"grows the edge table without bound and breaks the edge ≡ blocked_by mirror "
            f"the moment it does"
        )

    async def test_the_backfill_does_NOT_re_mint_over_edges_a_WRITE_PATH_already_made(
        self, legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]]
    ) -> None:
        """The other half of idempotence, and it is not the same half: the first boot's
        backfill and a subsequent ``create_task`` both mint edges, so a second boot meets a
        store whose edges came from TWO sources.  A backfill keyed on *"did I already run"*
        rather than on the store's actual state passes the leg above and fails this one.
        """
        connection, env, ids = legacy_column_store
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            fresh = await ledger.create_task(
                SUBJECT, DESCRIPTION, blocked_by=[ids["root"]], created_by=CREATOR
            )
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        expected = _expected_backfilled_pairs(ids) | {(ids["root"], fresh)}
        assert await _blocks_edge_pairs(connection) == expected, (
            f"after a backfill, a normal create, and a second boot, the edge set is not "
            f"exactly the union of the two sources. got="
            f"{sorted(await _blocks_edge_pairs(connection))} expected={sorted(expected)}"
        )


class TestALEGACYCycleIsMINTEDAndRECORDED:
    """RED today.  ⛔ **ESCALATION ESC-4, RULED READING A (lead, 2026-07-28).**

    A legacy row can name itself, or two legacy rows can name each other: ``blocked_by`` was
    FAIL-OPEN at write, and the acyclicity guard R3 adds is a WRITE-time guard for NEW
    writes.  R11 said nothing about what the backfill does with such rows, so this contract's
    author flagged it and deliberately did NOT pin either reading — pinning one would have
    made a build that defensibly chose the other RED on a correct implementation.

    **The ruling, and its reason, because the reason is the load-bearing half:** the backfill
    **MINTS** legacy cycles and **RECORDS** them.  Refusing them would break
    **edge ≡ ``blocked_by``** on exactly the rows the invariant is hardest to reason about,
    and ``+collect`` terminates on cycles (probe P4).  Verbatim: *"a legacy cycle is a
    pre-existing DATA defect; the edge set must MIRROR reality, not quietly diverge from it —
    a divergence the invariant asserts does not exist is a false clear in the store itself.
    The RECORD is what stops it being silent."*

    ⚠ This store is built in its own database rather than in ``legacy_column_store``, so the
    acyclic fixture every other leg in SECTION K depends on stays acyclic and says so.
    """

    @staticmethod
    async def _cyclic_legacy_store(
        connection: SurrealConnection, env: SurrealEnv
    ) -> tuple[str, str]:
        """Two legacy rows that block EACH OTHER, columns only, no edges.

        The closing dependency is written by a RAW ``UPDATE``, and it has to be: after this
        packet lands, no public verb will mint it (the cycle guard refuses), and ``ENFORCED``
        could not carry it as an edge at creation time anyway (adversary MP-4a — the closing
        edge points at a task that does not exist yet).  Production holds such rows because
        they were legal when they were written.
        """
        await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
        first = f"cycle_first_{uuid.uuid4().hex}"
        second = f"cycle_second_{uuid.uuid4().hex}"
        await _seed_legacy_task(connection, first, blocked_by=[], status=STATUS_OPEN)
        await _seed_legacy_task(connection, second, blocked_by=[first], status=STATUS_OPEN)
        await run(
            connection,
            f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
            {"id": first, "blocked_by": [second]},
        )
        return first, second

    async def test_a_legacy_CYCLE_is_MINTED_so_the_edge_set_MIRRORS_the_COLUMN(
        self,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ The ruled behaviour, as an EXACT set — a build that REFUSED the cycle would
        leave two rows whose column says "blocked" and whose edge set says "not blocked",
        which is the divergence the mirror invariant asserts cannot happen.
        """
        connection, env = migration_db
        first, second = await self._cyclic_legacy_store(connection, env)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert await _blocks_edge_pairs(connection) == {(second, first), (first, second)}, (
            f"the backfill did not mirror the legacy CYCLE onto the edge table (ESC-4, ruled "
            f"reading A). Both directions must be present: {first!r} is blocked_by "
            f"{second!r} AND {second!r} is blocked_by {first!r}. A build that refused the "
            f"cycle leaves the column and the edge set disagreeing on exactly the rows the "
            f"invariant is hardest to reason about. "
            f"got={sorted(await _blocks_edge_pairs(connection))}"
        )

    async def test_the_legacy_CYCLE_is_RECORDED_never_silent(
        self,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ *"The RECORD is what stops it being silent."*  Minting a cycle is the ruled
        behaviour AND a pre-existing data defect; an operator who is never told cannot fix
        the rows, and the next reader rediscovers it from a stuck task.
        """
        connection, env = migration_db
        first, second = await self._cyclic_legacy_store(connection, env)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        loud = [
            _recorded_text(record)
            for record in caplog.records
            if record.levelno >= logging.WARNING
        ]
        assert [text for text in loud if first in text and second in text], (
            f"the backfill minted a legacy CYCLE and said NOTHING at WARNING or above. The "
            f"record must name both members ({first!r}, {second!r}) so an operator can "
            f"repair the data (ESC-4). loud records={loud!r}"
        )

    async def test_the_TRAVERSAL_TERMINATES_over_a_backfilled_legacy_cycle(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ The half of the ruling that says minting is SAFE: *"``+collect`` terminates on
        cycles (probe P4)."*  Pinned as a MEASUREMENT rather than inherited as a claim.

        ⚠ **STATED BOUND, so this pin does not over-claim:** it asserts that the read
        RETURNS, that it reaches the other member, and that it DEDUPLICATES.  It deliberately
        does NOT assert ``truncated`` or whether the ROOT appears in its own reach — the
        first depends on how a build derives truncation over a cyclic walk and the second on
        whether ``+inclusive`` is in play, and neither is ruled. Pinning an unruled value
        here is the C-DEF risk ESC-4 was escalated to avoid.
        """
        connection, env = migration_db
        first, second = await self._cyclic_legacy_store(connection, env)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            result = await _transitive_blockers(ledger, first)
        finally:
            await ledger.close()
        assert second in result.ids, (
            f"the traversal over a backfilled legacy cycle did not reach {second!r}, which "
            f"{first!r}'s column names as its blocker: {sorted(result.ids)}"
        )
        assert len(result.ids) == len(set(result.ids)), (
            f"the closure over a cycle returned DUPLICATES, so it is walking the cycle "
            f"rather than collecting it: {result.ids}"
        )


#: The legacy cycle ARITIES the ruled cycle pin's fixture does NOT construct.
#:
#: ⚠ **A MONOCULTURE AXIS, NAMED** (final adversary §P2).
#: :class:`TestALEGACYCycleIsMINTEDAndRECORDED` builds a TWO-member cycle and nothing else,
#: so every pin resting on it is silent about every other arity — and the two neighbours of
#: 2 fail in DIFFERENT ways:
#:
#: * **1 — the SELF-loop.**  The shape a single defensive line deletes
#:   (``if blocker == task_id: continue`` — *"a task cannot block itself, so don't mint that
#:   edge"*), and the shape production actually HOLDS, because ``blocked_by`` was FAIL-OPEN
#:   at write and this contract's own :class:`TestCreateRefusesToFormACycle` calls it
#:   *"the 1-cycle … which ``ENFORCED`` alone cannot stop"*.  MEASURED: a backfill carrying
#:   that line passed the WHOLE contract, 215 passed / 0 failed, while serving
#:   ``ids=[] truncated=False`` on an unclaimable row — sidecar S3's exact false clear,
#:   through the one door SECTION K did not guard.
#: * **3 — the first arity a PAIR-shaped detector cannot see.**  A build that recognises
#:   *"a and b name each other"* and nothing longer mirrors the 2-cycle and drops the 3-cycle.
#:
#: Arity 2 is deliberately NOT repeated here: it is the sibling class's, and a second copy
#: of a pin is copy #2 of a served-surface guard (repo law #102).
LEGACY_CYCLE_ARITIES = (1, 3)


class TestALegacyCycleOfEVERYARITYIsMINTEDAndRECORDED:
    """RED today.  ⛔ **ESC-4, ∀ ARITY** — the ruling held over the whole set it governs.

    ESC-4 (lead, 2026-07-28, reading A) rules that the backfill **MINTS** legacy cycles and
    **RECORDS** them, because refusing them would break **edge ≡ ``blocked_by``** on exactly
    the rows the invariant is hardest to reason about.  :class:`TestALEGACYCycleIsMINTEDAndRECORDED`
    pins that ruling on a TWO-member cycle.

    **THE QUANTIFIER LAW, in its migration clothes:** *"a property derived over one member of
    the set the ruling governs, then stated over the whole set."*  The ruling says *cycles*;
    the fixture said *pairs*.  See :data:`LEGACY_CYCLE_ARITIES` for the two arities this class
    adds and the measured wrong build each one kills.

    ⚠ **WHAT THIS CLASS DELIBERATELY DOES NOT ASSERT**, so it cannot become a C-DEF the way
    an over-specified cycle pin would: it says nothing about ``truncated`` over a cyclic walk,
    nothing about whether a row appears in its OWN reach (that depends on ``+inclusive``,
    which no ruling carries), and nothing about the SHAPE of the operator log beyond the ids
    it must name.  Its sibling states the same bound for the same reason.
    """

    @staticmethod
    async def _cyclic_legacy_store_of_arity(
        connection: SurrealConnection, env: SurrealEnv, arity: int
    ) -> list[str]:
        """``arity`` legacy rows forming ONE cycle, COLUMNS ONLY, no edges anywhere.

        Each member's ``blocked_by`` is written by a RAW ``UPDATE`` for the sibling
        fixture's reason: after this packet lands no public verb will mint such a row (the
        write-time guard refuses), and ``ENFORCED`` could not carry the closing dependency as
        an edge at creation time anyway.  Production holds these rows because they were legal
        when they were written.

        Returns the members in cycle order, so ``members[i]`` is blocked by
        ``members[i - 1]`` and the expected edge set is derivable rather than typed.
        """
        await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
        members = [f"cyc{arity}_{index}_{uuid.uuid4().hex}" for index in range(arity)]
        for member in members:
            await _seed_legacy_task(connection, member, blocked_by=[], status=STATUS_OPEN)
        for index, member in enumerate(members):
            await run(
                connection,
                f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
                {"id": member, "blocked_by": [members[index - 1]]},
            )
        assert await _blocks_edge_pairs_or_NO_TABLE(connection) == set(), (
            "the cyclic legacy fixture already holds blocks edges, so the backfill it exists "
            "to measure has nothing to do and every leg below passes for a fixture reason"
        )
        return members

    @staticmethod
    def _expected_cycle_edges(members: list[str]) -> set[tuple[str, str]]:
        """The ``(blocker, blocked)`` pairs the column calls for — E-1's direction."""
        return {(members[index - 1], member) for index, member in enumerate(members)}

    @pytest.mark.parametrize(
        "arity", LEGACY_CYCLE_ARITIES, ids=[f"arity-{n}" for n in LEGACY_CYCLE_ARITIES]
    )
    async def test_a_legacy_CYCLE_of_this_ARITY_is_MINTED_as_an_EXACT_edge_set(
        self,
        arity: int,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ **The pin that kills the measured wrong build.**

        An EXACT set, for :func:`_expected_backfilled_pairs`'s reason: a superset passes a
        membership check while breaking the mirror (a closure-minting backfill), and a subset
        is the skip this leg exists to catch.  At arity 1 the expected set is the single
        SELF-edge ``(x, x)``.
        """
        connection, env = migration_db
        members = await self._cyclic_legacy_store_of_arity(connection, env, arity)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        expected = self._expected_cycle_edges(members)
        landed = await _blocks_edge_pairs(connection)
        assert landed == expected, (
            f"the backfill did not mirror a legacy {arity}-member cycle onto the edge table "
            f"(ESC-4, ruled reading A). The edge set must MIRROR the column, whatever the "
            f"cycle's arity: a skipped member leaves a row whose column says 'blocked' and "
            f"whose edges say 'not blocked', which is the divergence the mirror invariant "
            f"asserts cannot happen — and the traversal then serves ids=[] truncated=False "
            f"on a task that can never be claimed (sidecar S3's shape). "
            f"missing={sorted(expected - landed)} unexpected={sorted(landed - expected)}"
        )

    @pytest.mark.parametrize(
        "arity", LEGACY_CYCLE_ARITIES, ids=[f"arity-{n}" for n in LEGACY_CYCLE_ARITIES]
    )
    async def test_a_legacy_CYCLE_of_this_ARITY_is_RECORDED_never_silent(
        self,
        arity: int,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ *"The RECORD is what stops it being silent."*

        ⚠ Asserted over the UNION of the WARNING records rather than demanding ONE record
        that names every member, and that is a deliberate weakening: a build that logs one
        record per repaired ROW and a build that logs one per detected CYCLE are both
        legitimate, and a pin requiring a single all-naming record would fail the first for a
        reason no ruling carries.  What the operator needs is that **no member goes
        unnamed** — that is what is asserted.
        """
        connection, env = migration_db
        members = await self._cyclic_legacy_store_of_arity(connection, env, arity)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        loud = [
            _recorded_text(record)
            for record in caplog.records
            if record.levelno >= logging.WARNING
        ]
        unnamed = [member for member in members if not any(member in text for text in loud)]
        assert loud and not unnamed, (
            f"the backfill minted a legacy {arity}-member cycle and left "
            f"{unnamed or 'every member'} unnamed at WARNING or above. A legacy cycle is a "
            f"pre-existing DATA defect: an operator who is never told cannot repair the rows, "
            f"and the next reader rediscovers it from a task that is stuck forever (ESC-4). "
            f"loud records={loud!r}"
        )

    @pytest.mark.parametrize(
        "arity", LEGACY_CYCLE_ARITIES, ids=[f"arity-{n}" for n in LEGACY_CYCLE_ARITIES]
    )
    async def test_the_TRAVERSAL_TERMINATES_over_a_backfilled_cycle_of_this_ARITY(
        self,
        arity: int,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ The half of ESC-4 that says minting is SAFE — *"``+collect`` terminates on
        cycles (probe P4)"* — held at the arities the sibling pin does not reach.

        Probe P4 measured termination on a 4-cycle; the SELF-loop is the shape most likely to
        behave differently (a one-hop edge whose endpoints are the same row), and it is the
        one this packet's own guard calls *"the 1-cycle which ``ENFORCED`` alone cannot
        stop"*.  Pinned as a MEASUREMENT rather than inherited as a claim.

        ⚠ **STATED BOUND, identical to the sibling's:** it asserts that the read RETURNS,
        that it DEDUPLICATES, and — for a cycle longer than one — that it reaches every OTHER
        member.  It deliberately asserts nothing about ``truncated`` and nothing about whether
        the starting row appears in its own reach; neither is ruled, and pinning an unruled
        value is the C-DEF risk ESC-4 was escalated to avoid.
        """
        connection, env = migration_db
        members = await self._cyclic_legacy_store_of_arity(connection, env, arity)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            result = await _transitive_blockers(ledger, members[0])
        finally:
            await ledger.close()
        others = set(members[1:])
        assert others <= set(result.ids), (
            f"the traversal over a backfilled {arity}-member legacy cycle did not reach "
            f"{sorted(others - set(result.ids))}, which the columns put upstream of "
            f"{members[0]!r}: {sorted(result.ids)}"
        )
        assert len(result.ids) == len(set(result.ids)), (
            f"the closure over a {arity}-member cycle returned DUPLICATES, so it is WALKING "
            f"the cycle rather than COLLECTING it: {result.ids}"
        )


class TestTheBackfillMirrorsADependencyOnASUPERSEDEDTask:
    """RED today.  ⛔ **THE INTERACTION OF TWO INDIVIDUALLY-CORRECT RULINGS.**

    R10(ii) rules that the blocker pre-check REFUSES a superseded blocker, because *"a
    ``blocked_by`` naming a superseded task is NEVER legitimate"*.  R11 rules that the
    backfill mirrors the ``blocked_by`` COLUMN onto the edge table.  A builder carrying
    R10(ii)'s notion into R11's filter — one line, ``resolved = resolved - superseded``,
    after the shared existence probe — satisfies both rulings as it reads them and **restores
    sidecar S3's exact false clear**: the dependency vanishes from the edge set, the traversal
    serves ``ids=[] truncated=False``, and the claim CAS refuses the row forever.
    MEASURED: that build passed the WHOLE contract, 215 passed / 0 failed.

    **The distinction the builder needs, stated once:** refusing a superseded blocker at
    WRITE time is a decision about a dependency someone is creating NOW.  Dropping one at
    MIGRATION time is a decision about a dependency that ALREADY EXISTS — and R10(iii) says
    outright that *"supersession can happen AFTER dependents exist"*, so this row is not a
    contrivance, it is the case R10(iii) was added to cover.  The mirror is over the COLUMN,
    ∀ rows and ∀ blocker STATES.

    ⚠ **A SECOND MONOCULTURE AXIS, NAMED** (final adversary §P2): every blocker in
    ``legacy_column_store`` is ``open`` and non-superseded, so the LIFECYCLE STATE of a
    blocker is a value no SECTION K fixture varies.
    """

    @staticmethod
    async def _legacy_dependent_of_a_superseded_task(
        connection: SurrealConnection, env: SurrealEnv
    ) -> tuple[str, str, str]:
        """A COLUMN-ONLY dependency on a blocker that has since been SUPERSEDED.

        Built through the real ledger and then stripped back to the edge-less world, because
        ``superseded_by`` is stamped by ``supersede_task`` inside its own transaction and no
        raw seed should re-implement that stamp (repo law #102 — the fixture calls the verb).
        ``DELETE blocks`` returns the store to the production-real partial state: columns
        present, edges absent.

        Returns ``(waiter, blocker, successor)``.
        """
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            blocker = await ledger.create_task(
                "work that got reframed", DESCRIPTION, created_by=CREATOR
            )
            successor = await ledger.supersede_task(
                blocker,
                subject="the reframed item",
                description=DESCRIPTION,
                created_by=CREATOR,
            )
        finally:
            await ledger.close()
        waiter = f"waiter_{uuid.uuid4().hex}"
        await _seed_legacy_task(connection, waiter, blocked_by=[blocker], status=STATUS_OPEN)
        await run(connection, f"DELETE {BLOCKS_RELATION_NAME}")
        rows = await run(
            connection,
            f"SELECT VALUE superseded_by FROM type::record('{TASK_TABLE}', $id)",
            {"id": blocker},
        )
        assert rows and rows[0] is not None, (
            f"the fixture's blocker {blocker!r} is NOT superseded, so this class measures "
            f"nothing about a superseded blocker: superseded_by={rows!r}"
        )
        assert await _blocks_edge_pairs(connection) == set(), (
            "the fixture still holds blocks edges, so the backfill it exists to measure has "
            "nothing to do and both legs below pass for a fixture reason"
        )
        return waiter, blocker, successor

    async def test_a_legacy_dependency_on_a_SUPERSEDED_task_is_STILL_MIRRORED(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ The EXACT set, so a build that mints the edge AND something else fails too."""
        connection, env = migration_db
        waiter, blocker, successor = await self._legacy_dependent_of_a_superseded_task(
            connection, env
        )
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        landed = await _blocks_edge_pairs(connection)
        assert landed == {(blocker, waiter)}, (
            f"the backfill did not mirror a legacy dependency whose blocker had been "
            f"SUPERSEDED (by {successor!r}). R10(ii) refuses such a blocker at WRITE time; "
            f"reusing that refusal as the MIGRATION's filter drops a dependency that already "
            f"exists — the case R10(iii) names verbatim, *'supersession can happen AFTER "
            f"dependents exist'* — and the row is then served as unblocked while the claim "
            f"CAS holds it blocked forever. The mirror is over the COLUMN, forall rows and "
            f"forall blocker states. expected={sorted({(blocker, waiter)})} got={sorted(landed)}"
        )

    async def test_a_SKIP_is_never_RECORDED_as_a_PHANTOM_when_the_row_EXISTS(
        self,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ **The operator record must not teach something false.**

        R11's rider makes phantom skips RECORDED *"so an operator can act"*.  A build that
        drops this dependency and files it under the phantom skip sends that operator after a
        row that is plainly there — the log is not merely incomplete, it ASSERTS a fact about
        the data that is false, which is the same class as a confident empty.

        ⚠ The POSITIVE control for this leg is its neighbour
        :meth:`TestThePHANTOMBlockerIsSKIPPEDAndRECORDED.test_the_phantom_SKIP_is_RECORDED_never_silent`,
        which proves a GENUINE phantom IS recorded as one — so this pin cannot be satisfied by
        a build that never records anything.  It is not duplicated here (repo law #102).
        """
        connection, env = migration_db
        waiter, blocker, _successor = await self._legacy_dependent_of_a_superseded_task(
            connection, env
        )
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        lying = [
            _recorded_text(record)
            for record in caplog.records
            if record.levelno >= logging.WARNING
            and "phantom" in _recorded_text(record).lower()
            and blocker in _recorded_text(record)
        ]
        assert not lying, (
            f"the migration recorded {blocker!r} as a PHANTOM blocker of {waiter!r}, and that "
            f"row EXISTS — the record an operator acts on is false. A phantom is a "
            f"blocked_by entry naming NO task row; this one names a row that is merely "
            f"superseded. records={lying!r}"
        )


class TestTheBackfillMirrorsADependencyOnATERMINALBlocker:
    """RED today.  ⛔ **The other half of the LIFECYCLE-STATE axis.**

    ``legacy_column_store`` holds a TERMINAL TASK (``LEGACY_TERMINAL_TASK``) and
    :meth:`TestTheBACKFILLClosesTheLEGACYEdgeGap.test_the_backfill_covers_a_TERMINAL_row_too_not_only_the_OPEN_ones`
    pins that the backfill covers it — but that is the status of the row being BACKFILLED.
    **Every BLOCKER in that fixture is ``open``**, so *"the dependency already finished, there
    is nothing to mint"* is a plausible, defensible-sounding wrong build that no pin sees.

    It is a quieter defect than its superseded sibling — a row blocked only by a ``done`` task
    IS claimable, so the traversal and the CAS still agree and
    :class:`TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS` cannot catch it.  What it breaks is
    **edge ≡ ``blocked_by``** itself, and 04b-2's critical-path render then cannot show a
    consumer WHY a chain finished the way it did.  The mirror is over the COLUMN; the backfill
    does not get to decide which dependencies were worth recording.

    Both terminal statuses, because the terminal SET is ``{done, wontfix}`` and a build may
    reach only one of them.
    """

    @staticmethod
    async def _legacy_dependent_of_a_terminal_task(
        connection: SurrealConnection, env: SurrealEnv, blocker_status: str
    ) -> tuple[str, str]:
        """A COLUMN-ONLY dependency on a blocker driven to ``blocker_status``."""
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            blocker = await ledger.create_task(
                "work that finished", DESCRIPTION, created_by=CREATOR
            )
            await _drive_to(ledger, blocker, blocker_status)
        finally:
            await ledger.close()
        waiter = f"waiter_{uuid.uuid4().hex}"
        await _seed_legacy_task(connection, waiter, blocked_by=[blocker], status=STATUS_OPEN)
        await run(connection, f"DELETE {BLOCKS_RELATION_NAME}")
        assert await _blocks_edge_pairs(connection) == set(), (
            "the fixture still holds blocks edges, so the backfill it exists to measure has "
            "nothing to do and the leg below passes for a fixture reason"
        )
        return waiter, blocker

    @pytest.mark.parametrize(
        "blocker_status", [STATUS_DONE, STATUS_WONTFIX], ids=["done-blocker", "wontfix-blocker"]
    )
    async def test_a_legacy_dependency_on_a_TERMINAL_task_is_STILL_MIRRORED(
        self,
        blocker_status: str,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        connection, env = migration_db
        waiter, blocker = await self._legacy_dependent_of_a_terminal_task(
            connection, env, blocker_status
        )
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        landed = await _blocks_edge_pairs(connection)
        assert landed == {(blocker, waiter)}, (
            f"the backfill did not mirror a legacy dependency whose blocker is already "
            f"{blocker_status!r}. 'That dependency is finished, there is nothing to mint' is "
            f"a decision the migration does not get to make: the mirror is over the COLUMN, "
            f"forall rows and forall blocker states, and an edge set that quietly disagrees "
            f"with the column is the divergence the invariant asserts cannot happen. "
            f"expected={sorted({(blocker, waiter)})} got={sorted(landed)}"
        )


class TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS:
    """RED today.  ⛔ **THE ∀-OVER-OUTCOMES PIN — the one that closes the CLASS.**

    Every other pin in SECTION K guards a CAUSE that was debugged: the missing backfill, the
    phantom skip, the 2-cycle, the superseded blocker, the cycle arities.  THE QUANTIFIER LAW
    says an invariant conditioned on the failure mode that prompted the work is not the
    invariant — so this class pins the OUTCOME instead:

        **no row may be SERVED as having nothing upstream while the claim CAS holds it
        blocked.**

    Any backfill filter — present, future, or not yet imagined — whose skip makes the
    traversal disagree with the CAS dies here.  MEASURED: it is RED on both of the wrong
    builds that survived the whole contract (the skipped SELF-loop and the dropped SUPERSEDED
    blocker) and GREEN on a correct one.

    ``TestTheBoundedReadKeepsTheClaimAgreement`` makes the same agreement demand of
    ``query_tasks``; **nothing made it of the TRAVERSAL**, which is the surface 04b-2 renders
    a critical path from.

    ⚠ **THE IMPLICATION IS ONE-DIRECTIONAL, AND THAT IS NOT A WEAKNESS.**  ``ids != []`` does
    NOT mean unclaimable — a task whose only blocker is ``done`` has an upstream blocker and
    is perfectly claimable, and one of the shapes below forces exactly that so the direction
    cannot be quietly inverted.  What must never happen is the confident empty.
    """

    #: Every shape's row is OPEN, UNOWNED and NOT superseded, so a refused claim is caused by
    #: a BLOCKER and never by the row's own lifecycle — a fixture where a claim could fail for
    #: two reasons cannot tell which one it observed.
    CLAIMER = "agreement-auditor"

    @staticmethod
    async def _legacy_world(
        connection: SurrealConnection, env: SurrealEnv
    ) -> tuple[dict[str, str], str]:
        """The shapes, as COLUMNS ONLY, then handed to the backfill.

        Live blockers are created through the ledger (a ``done`` blocker has to travel a legal
        transition; a superseded one has to be stamped by ``supersede_task``), the dependent
        rows are RAW-seeded because a blocked+legacy row is unreachable through the public
        verbs, and ``DELETE blocks`` returns the store to the edge-less world 04b-1 deploys
        into.  Returns ``(shapes, phantom_row_id)``.
        """
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            open_blocker = await ledger.create_task(
                "a live open blocker", DESCRIPTION, created_by=CREATOR
            )
            done_blocker = await ledger.create_task(
                "a live blocker that finished", DESCRIPTION, created_by=CREATOR
            )
            await _drive_to(ledger, done_blocker, STATUS_DONE)
            reframed = await ledger.create_task(
                "a live blocker that got reframed", DESCRIPTION, created_by=CREATOR
            )
            await ledger.supersede_task(
                reframed,
                subject="the reframed item",
                description=DESCRIPTION,
                created_by=CREATOR,
            )
        finally:
            await ledger.close()

        shapes: dict[str, str] = {}
        for label, blockers in (
            ("no blockers at all", []),
            ("blocked on a LIVE OPEN task", [open_blocker]),
            ("blocked on a LIVE DONE task", [done_blocker]),
            ("blocked on a SUPERSEDED task", [reframed]),
        ):
            row = f"agree_{uuid.uuid4().hex}"
            await _seed_legacy_task(connection, row, blocked_by=blockers, status=STATUS_OPEN)
            shapes[label] = row
        self_loop = f"selfloop_{uuid.uuid4().hex}"
        await _seed_legacy_task(
            connection, self_loop, blocked_by=[self_loop], status=STATUS_OPEN
        )
        shapes["blocked on ITSELF (the 1-cycle)"] = self_loop

        phantom_row = f"phantom_carrier_{uuid.uuid4().hex}"
        await _seed_legacy_task(
            connection,
            phantom_row,
            blocked_by=[ghost_id("ghost_blocker")],
            status=STATUS_OPEN,
        )
        await run(connection, f"DELETE {BLOCKS_RELATION_NAME}")
        return shapes, phantom_row

    async def test_a_row_whose_blockers_ALL_RESOLVE_is_CLAIMABLE_whenever_the_traversal_is_EMPTY(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔⛔ The ∀. For every shape whose ``blocked_by`` names only LIVE task rows:
        ``ids == [] and truncated is False`` ⇒ the claim is GRANTED.

        ⚠ **THE 'ALL RESOLVE' CONDITION IS ASSERTED, NOT ASSUMED.**  A ``blocked_by`` entry
        naming no task row is the ONE difference R11's backfill cannot delete (``ENFORCED``
        forbids the edge, #236 rules the cleanup out), so it is excluded here and pinned
        SEPARATELY as a known bound by the leg below.  Excluding it silently would be the
        quantifier defect this class exists to close, one level up.

        ⚠ The claim is DESTRUCTIVE, so every traversal is read FIRST and every claim is
        attempted afterwards; the verdict is recorded per shape so a failure says WHICH one
        diverged.
        """
        connection, env = migration_db
        shapes, _phantom_row = await self._legacy_world(connection, env)

        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            for label, row in shapes.items():
                for blocker in await _column_blockers_of(ledger, row):
                    assert await record_exists(connection, TASK_TABLE, blocker), (
                        f"shape {label!r} names a blocker ({blocker!r}) that is NOT a live "
                        f"task row, so it is outside this pin's stated scope and would make "
                        f"the quantifier below dishonest — fix the fixture, not the assertion"
                    )
            served = {
                label: await _transitive_blockers(ledger, row) for label, row in shapes.items()
            }
            confident_empty = {
                label: (result.ids == [] and result.truncated is False)
                for label, result in served.items()
            }
            claimed = {
                label: (await ledger.claim_task(row, self.CLAIMER)).claimed
                for label, row in shapes.items()
            }
        finally:
            await ledger.close()

        divergences = [
            f"{label} ({shapes[label]}): the traversal served "
            f"{_served_shape(served[label])} and the claim CAS said claimed="
            f"{claimed[label]}"
            for label in shapes
            if confident_empty[label] and not claimed[label]
        ]
        assert not divergences, (
            "the transitive read served a CONFIDENT EMPTY — ids=[] truncated=False, a "
            "positive assertion that nothing is upstream — for a task the claim CAS refuses. "
            "A consumer acting on that WITHOUT CHECKING concludes the task is ready and "
            "attempts a claim that can never win; nothing in the response names the reason. "
            "That is sidecar S3's defect, whatever backfill filter reintroduced it. "
            f"Diverging shapes: {divergences}"
        )
        assert any(confident_empty.values()), (
            f"no shape produced ids=[] truncated=False, so the implication above was VACUOUS "
            f"— a build serving a non-empty answer for everything would pass it: "
            f"{ {label: _served_shape(result) for label, result in served.items()} }"
        )
        assert not all(confident_empty.values()), (
            f"every shape produced ids=[] truncated=False, so the fixture cannot tell a "
            f"traversal that answers from one that answers CONSTANTLY: "
            f"{ {label: _served_shape(result) for label, result in served.items()} }"
        )
        assert any(claimed.values()) and not all(claimed.values()), (
            f"every shape landed on the SAME side of the claim gate, so the agreement above "
            f"holds for a fixture reason: {claimed}"
        )

    async def test_KNOWN_BOUND_a_PHANTOM_blocker_is_the_ONE_row_the_traversal_CANNOT_see(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ **WHEN YOU CANNOT CLOSE A HOLE, PIN IT** (repo law; #137/#138's instrument).

        A legacy ``blocked_by`` naming NO task row is, permanently, in the COLUMN and not in
        the traversal: ``ENFORCED`` forbids the edge, R11's backfill therefore SKIPS it, and
        #236 rules the cleanup of such rows OUT.  So the agreement above has exactly one
        exception, and this leg ASSERTS the exception rather than leaving it as a silent
        narrowing — the difference between a bound the next engineer meets DELIBERATELY and
        one they rediscover from an outage.

        The consumer-facing half of this bound is the read's own docstring
        (:class:`TestTheScopeOfTheTransitiveReadIsSTATED`) — *a bound is a FACT, never a
        disclaimer*.

        ⚠ **NAMED RE-OPEN TRIGGER:** this pin goes RED the day the phantom residue is closed
        — by a backfill that records it in some other channel the read consults, by #236 being
        overturned, or by the read falling back to the COLUMN.  **If you closed it
        deliberately, DELETE this pin and widen the ∀ above to cover every row.**
        """
        connection, env = migration_db
        _shapes, phantom_row = await self._legacy_world(connection, env)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
            result = await _transitive_blockers(ledger, phantom_row)
            claim = await ledger.claim_task(phantom_row, self.CLAIMER)
        finally:
            await ledger.close()
        assert result.ids == [] and result.truncated is False, (
            f"the traversal returned something for a row whose ONLY blocker names no task "
            f"row. ENFORCED forbids that edge and R11 skips it, so the read cannot see it — "
            f"if this build CAN, the residue is closed and the sibling ∀ pin should be "
            f"widened to cover every row. served={_served_shape(result)}"
        )
        assert not claim.claimed, (
            f"the claim CAS ACCEPTED a task whose blocked_by names a never-minted id. That "
            f"is a DIFFERENT and worse defect than the bound this pin describes: the CAS "
            f"counts an unresolvable blocker and must refuse forever. claim={claim!r}"
        )


#: How many legacy edges the ONE-TRANSACTION pin backfills at each leg.  A GROWTH comparison,
#: never a threshold: a per-edge write costs one round trip per edge and a single transaction
#: costs the same at any size, so the two builds are distinguishable only by comparing sizes.
#: 30 rather than 60 because the fixture writes each legacy row individually and the property
#: is a ratio, not a magnitude.
LEGACY_BACKFILL_EDGES_LARGE = 30
LEGACY_BACKFILL_EDGES_SMALL = 2


class TestTheBackfillIsONETransaction:
    """RED today.  ⛔ **R11's OWN RATIONALE, WHICH NOTHING PINNED.**

    R11 pre-filters the backfill through the existence policy for one stated reason: *"a naked
    backfill meets legacy phantom blockers, which meet ``ENFORCED``, and rolls back the entire
    **one-transaction** migration."*  That sentence is FALSE of a build that issues one
    ``RELATE`` per legacy edge — and MEASURED, such a build passed the whole contract, because
    :class:`TestTheNakedBackfillWouldRollTheMigrationBack` measures the **ENGINE** (a
    hand-composed transaction) and never the build.

    The consequence is concrete and it is not only theoretical hygiene: **PROOF 10b's declared
    RED set is derived from that premise** (*"the whole migration rolls back, so nothing lands
    at all"*).  Against an N-writes build the proof returns FEWER reds than declared →
    ``PROOF FAILED`` → and the builder's next move is to edit the declared list, which is the
    exact anti-pattern ``scripts/mutation_proof.py`` exists to prevent.

    ⚠ **STATED BOUND, so this class does not over-claim.**  Round trips are what it measures.
    One round trip is a NECESSARY condition for one transaction and is the property WB-C
    violates; the ROLLBACK itself is measured on the engine by
    :class:`TestTheNakedBackfillWouldRollTheMigrationBack`, and the two together are what make
    R11's rationale true rather than assumed.  A statement-text pin was deliberately NOT
    written: R7's sibling records why (*"a pin demanding the literal token ``BEGIN`` would
    redden a build that composes the same guarantee differently"*).
    """

    @staticmethod
    async def _boot_traffic(edge_count: int) -> tuple[StoreTraffic, int]:
        """Round trips for the BOOT that back-fills ``edge_count`` legacy edges.

        A chain rather than a star, so every legacy row carries exactly one blocker and the
        edge count is the row count minus one — a fixture whose arithmetic a reader can check.
        The ledger is fresh, so a backfill keyed on a per-instance *"did I already run"* flag
        cannot pass this by not running.
        """
        env = make_env(database=unique_database(), dim=MIGRATION_DIM)
        connection = await connect_admin(env)
        try:
            await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
            ids = [f"boot{index}_{uuid.uuid4().hex}" for index in range(edge_count + 1)]
            for index, task_id in enumerate(ids):
                await _seed_legacy_task(
                    connection,
                    task_id,
                    blocked_by=[ids[index - 1]] if index else [],
                    status=STATUS_OPEN,
                )
            ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
            try:
                traffic = await measure_store_traffic(ledger, ledger.ensure_ready)
            finally:
                await ledger.close()
            return traffic, len(await _blocks_edge_pairs(connection))
        finally:
            await connection.close()
            await drop_database(env)

    async def test_the_BOOTs_round_trips_do_NOT_grow_with_the_number_of_LEGACY_edges(
        self,
    ) -> None:
        small, small_edges = await self._boot_traffic(LEGACY_BACKFILL_EDGES_SMALL)
        large, large_edges = await self._boot_traffic(LEGACY_BACKFILL_EDGES_LARGE)
        assert (small_edges, large_edges) == (
            LEGACY_BACKFILL_EDGES_SMALL,
            LEGACY_BACKFILL_EDGES_LARGE,
        ), (
            f"the two boots minted {small_edges} and {large_edges} edges where their columns "
            f"call for {LEGACY_BACKFILL_EDGES_SMALL} and {LEGACY_BACKFILL_EDGES_LARGE}. A "
            f"round-trip comparison between two backfills that did DIFFERENT amounts of work "
            f"measures nothing — and 'the count did not grow' is trivially true of a backfill "
            f"that mints nothing at all"
        )
        assert small.calls > 0, (
            f"the instrument saw NO store traffic for a boot that applies DDL and mints "
            f"{small_edges} edges — it is not observing this path, so the comparison below "
            f"is worthless: {small}"
        )
        assert large.calls == small.calls, (
            f"a boot that back-filled {LEGACY_BACKFILL_EDGES_SMALL} legacy edges cost "
            f"{small.calls} round trips and one that back-filled "
            f"{LEGACY_BACKFILL_EDGES_LARGE} cost {large.calls}. The backfill is issuing one "
            f"write PER EDGE, so R11's own rationale — *'a naked backfill … rolls back the "
            f"entire one-transaction migration'* — is FALSE of this build, and PROOF 10b's "
            f"declared RED set (which assumes nothing lands at all) is measuring a "
            f"guarantee that does not exist. Compose the edge writes into ONE transaction. "
            f"small={small.statements} large={large.statements}"
        )


class TestTheBackfillRoutesThroughTheSHAREDExistencePolicy:
    """RED today.  ⛔ **L3 applied to R11** — *"pre-filtered through the L3 existence
    policy"*, proved the only way sharing can be proved: by MUTATION.

    ROUTING IS NOT SHARING, and a second copy of *"does this id name a live row"* is
    exactly the #102 shape this packet already generalised once.  So the pin does not look
    for a call; it makes the shared module's coroutines UNUSABLE and requires the backfill
    to notice.

    ⚠ **NAME-FREE BY CONSTRUCTION** (:func:`_patch_every_shared_policy_COROUTINE`): the
    filter needs the set of ids that RESOLVED, and the policy's shipped entry point RAISES
    instead of returning one — so the builder owes that module a non-raising probe and may
    spell it however it likes.  This contract's author escalated that gap rather than
    inventing the name (see the wave report's ESCALATIONS).
    """

    class _PolicyWasReached(RuntimeError):
        """A sentinel distinguishable from every real error on this path."""

    async def test_MUTATION_neutralising_the_shared_policy_STOPS_the_backfill(
        self,
        monkeypatch: pytest.MonkeyPatch,
        legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]],
    ) -> None:
        _connection, env, _ids = legacy_column_store

        async def _sentinel(*_args: Any, **_kwargs: Any) -> None:
            raise self._PolicyWasReached("the shared row-existence policy was reached")

        patched = _patch_every_shared_policy_COROUTINE(monkeypatch, _sentinel)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with pytest.raises(self._PolicyWasReached):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert patched, f"nothing was patched: {patched}"

    async def test_POSITIVE_CONTROL_a_store_with_NOTHING_to_backfill_never_reaches_it(
        self,
        monkeypatch: pytest.MonkeyPatch,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ Without this the leg above is satisfied by an ``ensure_ready`` that calls the
        policy for a reason having nothing to do with the backfill — or by one that calls it
        once per boot regardless.  Here there are no legacy columns at all, so a correct
        build has nothing to resolve and must complete.
        """
        connection, env = migration_db
        await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
        await _seed_legacy_task(
            connection, f"lonely_{uuid.uuid4().hex}", blocked_by=[], status=STATUS_OPEN
        )

        async def _sentinel(*_args: Any, **_kwargs: Any) -> None:
            raise TestTheBackfillRoutesThroughTheSHAREDExistencePolicy._PolicyWasReached(
                "the shared row-existence policy was reached with nothing to resolve"
            )

        _patch_every_shared_policy_COROUTINE(monkeypatch, _sentinel)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()

    async def test_a_FAILED_existence_read_makes_ensure_ready_LOUD_not_SILENTLY_PARTIAL(
        self,
        monkeypatch: pytest.MonkeyPatch,
        legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]],
    ) -> None:
        """⛔ **Leg-2 forgery construction — §11.1's "blocker pre-check × {empty, error}"
        row, at MIGRATION time.**

        A backfill that wraps its pre-filter in a swallowing ``except`` completes, boots the
        service, and leaves the traversal serving world A's confident empty on every legacy
        row — *the exact defect R11 exists to delete, restored by a degradation nobody
        constructed*.  The store's own seam raises rather than returning ``[]`` (its
        positive control is in SECTION L), so a failed check CANNOT be mistaken for a store
        with no matching rows: the only way to serve the false clear is to swallow.
        """
        _connection, env, _ids = legacy_column_store

        async def _rejecting(*_args: Any, **_kwargs: Any) -> None:
            raise SurrealStoreError("the existence read was rejected by the engine")

        _patch_every_shared_policy_COROUTINE(monkeypatch, _rejecting)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with pytest.raises(Exception) as caught:  # noqa: B017 - vocabulary is the builder's
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert not isinstance(caught.value, AssertionError), (
            f"ensure_ready raised the test's own AssertionError rather than propagating the "
            f"store failure: {caught.value!r}"
        )


#: The row count SECTION K's coverage pin seeds, **DERIVED from this file's own fixtures**
#: rather than typed.
#:
#: ⚠⚠ **THE FIXTURE CEILING *WAS* THE DEFECT** (delta adversary §PINS-1, measured
#: 2026-07-28 at ``0782450``).  Every legacy fixture in SECTION K topped out at
#: :data:`LEGACY_BACKFILL_EDGES_LARGE` = 30 rows, so a backfill carrying a single
#: ``LIMIT 50`` on its pending read passed the WHOLE contract — **234 passed / 0 failed** —
#: while serving **10 of 60** legacy rows a confident ``ids=[] truncated=False`` that the
#: claim CAS refuses.  That is sidecar S3's exact false clear, restored at a scale no
#: fixture in this file reached.  ONE pin fired at ``LIMIT 25``, and only through its own
#: *fixture-drift* guard — a check written for a different purpose.
#:
#: So the floor is computed from this file's row-count constants rather than typed: it RISES
#: the day someone raises a fixture, and a hard-coded 61 that nobody re-derives cannot rot
#: into a number a cap comes to sit just above.
#:
#: ⚠ **STATED BOUND ON THE FLOOR ITSELF, because a hand-list is the instrument shape this
#: repo has the most receipts against.**  The ``max()`` below is a LIST of names, not a
#: derivation over the module — so a future fixture constant that nobody adds here leaves the
#: floor stale.  That bound is affordable ONLY because the floor is not what carries the
#: discrimination: the pins below compare TWO sizes (``floor`` and ``2 × floor``) with an
#: EXACT-SET assertion at each, so a cap tuned to pass at either dies at the other.  The floor
#: decides where the comparison starts, never whether it can be tuned past — which is why it
#: is deliberately not a threshold assertion (a magic number is a value a builder can tune
#: until it passes; its sibling round-trip pin states the same reasoning).
#: Constants surveyed 2026-07-28 by ``grep -nE '^[A-Z_]+ = [0-9]+'`` over this file: the only
#: larger integer is ``ENGINE_RECURSION_CEILING`` (256), which is a DEPTH bound the engine
#: imposes and never a seeded row population — excluded deliberately, not overlooked.
_LARGEST_LEGACY_ROW_FIXTURE = max(
    LEGACY_BACKFILL_EDGES_LARGE,
    LEGACY_BACKFILL_EDGES_SMALL,
    UNRELATED_TASK_COUNT_LARGE,
    UNRELATED_TASK_COUNT_SMALL,
    len(LEGACY_COLUMN_DAG) + 2,
)
LEGACY_BACKFILL_SCALE_FLOOR = _LARGEST_LEGACY_ROW_FIXTURE + 1


class TestTheBackfillCoversALegacyStoreLARGERThanEveryOtherFIXTURE:
    """GREEN at ``b8607c4``.  ⛔ **THE SCALE AXIS — the third monoculture this section had.**

    Its siblings are ∀ over SHAPE (five of them), ∀ over blocker LIFECYCLE STATE and ∀ over
    cycle ARITY.  **None of them is ∀ over SCALE**, and
    :class:`TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS` says in its own docstring that *"any
    backfill filter — present, future, or not yet imagined — whose skip makes the traversal
    disagree with the CAS dies here"* while holding a SIX-row fixture.  A ``LIMIT 50`` walked
    straight through it (delta adversary §P1 WB-E, 234 passed / 0 failed).

    **Why a cap is the single most plausible wrong build in this packet, which is what makes
    the hole expensive:** 04b-1 is *about* bounded reads — #253, R9, R7 — so a builder who has
    just been told *"no read may scale with the ledger"* writes one here too.  The backfill is
    the ONE read in this ledger that must be unbounded, and nothing said so.

    ⚠ **STATED BOUND, so this class does not over-claim.**  It measures COVERAGE (which rows
    the migration reached), never round trips — its sibling
    :class:`TestTheBackfillIsONETransaction` owns that question, and the two are independent:
    a build can be perfectly bounded to one transaction and still cover only half the store.
    """

    @staticmethod
    async def _seed_star(
        connection: SurrealConnection, env: SurrealEnv, count: int
    ) -> tuple[str, list[str]]:
        """``count`` legacy rows, each blocked by ONE shared root, columns only, no edges.

        A STAR rather than a chain: every dependent carries exactly one blocker, so the
        expected edge set is ``count`` pairs a reader can check by counting rows, and the
        dependency-bearing population the backfill's own read filters on is exactly
        ``count`` — one row per edge, which is what makes a row-cap visible as a missing edge.
        """
        await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
        root = f"scaleroot_{uuid.uuid4().hex}"
        await _seed_legacy_task(connection, root, blocked_by=[], status=STATUS_OPEN)
        dependents = [f"scalewait{index}_{uuid.uuid4().hex}" for index in range(count)]
        for task_id in dependents:
            await _seed_legacy_task(
                connection, task_id, blocked_by=[root], status=STATUS_OPEN
            )
        return root, dependents

    @classmethod
    async def _backfill_at_scale(
        cls, count: int, *, probe_served: bool = False
    ) -> tuple[str, list[str], set[tuple[str, str]], dict[str, str]]:
        """Boot ONE fresh ledger over a ``count``-row legacy star and report what landed.

        Returns ``(root, dependents, minted_pairs, served)`` where ``served`` maps each
        dependent to its rendered :func:`_served_shape` — empty unless ``probe_served``,
        because that probe costs one round trip PER ROW and only one leg needs it.
        """
        env = make_env(database=unique_database(), dim=MIGRATION_DIM)
        connection = await connect_admin(env)
        try:
            root, dependents = await cls._seed_star(connection, env, count)
            ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
            served: dict[str, str] = {}
            try:
                await ledger.ensure_ready()
                minted = await _blocks_edge_pairs(connection)
                if probe_served:
                    for task_id in dependents:
                        served[task_id] = await _served_outcome(
                            _transitive_blockers(ledger, task_id)
                        )
            finally:
                await ledger.close()
            return root, dependents, minted, served
        finally:
            await connection.close()
            await drop_database(env)

    async def test_a_legacy_store_LARGER_than_every_other_fixture_is_backfilled_ENTIRELY(
        self,
    ) -> None:
        """⛔ WB-E and every other partial backfill, whatever its cause.

        TWO sizes, and the assertion is EXACT-SET at each — not a growth ratio, not a
        threshold.  A cap tuned to pass at :data:`LEGACY_BACKFILL_SCALE_FLOOR` dies at twice
        it; a cap set above both dies the day the derived floor rises past it; and an exact
        set (rather than a count) also kills the closure-minting build the section's other
        exact-set pins exist for.
        """
        floor = LEGACY_BACKFILL_SCALE_FLOOR
        assert floor > LEGACY_BACKFILL_EDGES_LARGE, (
            f"the derived scale floor {floor} does not exceed this file's largest legacy "
            f"fixture ({LEGACY_BACKFILL_EDGES_LARGE}), so this class adds no scale at all "
            f"and every leg below is a duplicate of a pin that already exists"
        )
        for count in (floor, 2 * floor):
            root, dependents, minted, _served = await self._backfill_at_scale(count)
            expected = {(root, task_id) for task_id in dependents}
            assert len(expected) == count, (
                f"the fixture built {len(expected)} distinct dependencies where it asked "
                f"for {count}; a coverage comparison against a fixture that did not come "
                f"out as intended measures nothing"
            )
            assert minted == expected, (
                f"a boot over {count} legacy dependency-bearing rows minted "
                f"{len(minted)} blocks edges where the COLUMNS call for {len(expected)}. "
                f"The backfill is not covering the whole store — a cap, a page, a batch "
                f"bound, or any other partial read — and every row it missed is served "
                f"'ids=[] truncated=False' by transitive_blockers while the claim CAS "
                f"refuses it: sidecar S3's confident lie, on production's real rows. The "
                f"backfill's pending read is the ONE read in this ledger that must be "
                f"UNBOUNDED. missing={sorted(expected - minted)[:5]} "
                f"unexpected={sorted(minted - expected)[:5]}"
            )

    async def test_NO_row_of_a_LARGE_legacy_store_is_served_a_CONFIDENT_EMPTY(self) -> None:
        """⛔ The same defect stated as the CONSUMER's experience rather than the store's.

        The pin above compares edge sets; this one asks what an agent is actually told.  A
        partially back-filled store answers ``OK ids=[] truncated=False`` for every row the
        migration missed — a positive assertion of completeness, not a missing bound — and
        the delta adversary MEASURED exactly that shape on 10 of 60 rows.

        Both legs are needed and neither implies the other: an edge set can be complete while
        the read is broken, and a read can be honest (raising) while the edge set is short.
        """
        _root, dependents, _minted, served = await self._backfill_at_scale(
            LEGACY_BACKFILL_SCALE_FLOOR, probe_served=True
        )
        assert len(served) == len(dependents) == LEGACY_BACKFILL_SCALE_FLOOR, (
            f"the probe collected {len(served)} outcomes for {len(dependents)} legacy rows; "
            f"it is not observing every row, so its verdict is worthless"
        )
        confident_empties = sorted(
            task_id for task_id, shape in served.items() if shape.startswith("OK ids=[] ")
        )
        assert not confident_empties, (
            f"{len(confident_empties)} of {len(dependents)} legacy rows were served a "
            f"CONFIDENT EMPTY — 'ids=[] truncated=False' — while their blocked_by COLUMN "
            f"names a live blocker the claim CAS still refuses them for. That is not a "
            f"missing bound, it is a false statement of completeness (sidecar S3), and it "
            f"is what a partial backfill leaves behind at a scale no other fixture in this "
            f"file reaches. first={confident_empties[:3]} "
            f"sample={served[confident_empties[0]]!r}"
        )


#: The DOORS through which the backfill can fail, as a set rather than as the one that was
#: debugged.
#:
#: ⚠⚠ **THE QUANTIFIER LAW, CAUGHT IN THIS SECTION'S OWN CODE** (delta adversary §P1 WB-O).
#: :class:`TestTheBackfillRoutesThroughTheSHAREDExistencePolicy` pins *"a failure of the
#: EXISTENCE READ makes ``ensure_ready`` raise"* — the invariant conditioned on the failure
#: mode that was debugged.  The invariant the packet NEEDS is *"ANY failure of the backfill
#: makes ``ensure_ready`` raise"*, and a ``try/except`` around the MINT alone passed the whole
#: contract (**234 passed / 0 failed**) while booting a service whose legacy edge set is
#: entirely absent — the single most-written defensive line in any migration (*"the backfill
#: must never stop the service booting"*), and the exact false clear R11 exists to delete.
#:
#: Stated as a PARAMETRISATION so the next door added here is an entry rather than a hole.
BACKFILL_FAILURE_DOORS = ("existence-read", "mint")


class TestANYBackfillFailureMakesEnsureReadyLOUD:
    """GREEN at ``b8607c4``.  ⛔ **WB-O, and the class of build it belongs to.**

    A boot that survives its own failed migration is worse than a boot that dies: the service
    comes up, every legacy row is served a confident empty, and there is no moment at which
    anybody learns the migration did not happen.  ``ensure_ready``'s consumer is the booting
    service, and it reads a normal return as *"this store is migrated"* — so a normal return
    over a failed backfill is a forged response in the trust definition's exact sense.

    ⚠ **HOW THE MINT DOOR IS DEGRADED, and why it is not a method name.**  The existence-read
    door is reached through :func:`_patch_every_shared_policy_COROUTINE` (derived, name-free).
    The mint door has no such derivation available — so it is keyed on a property of the
    STATEMENT instead: a transaction whose text names the ``blocks`` relation table and
    contains no ``DEFINE`` is an edge WRITE, whatever the builder called the method that
    composed it.  ``ENFORCED`` gives that property for free: an edge cannot be minted without
    naming its own table.  The degradation FAILS CLOSED — if no such statement is ever seen,
    the leg reddens as vacuous rather than passing because nothing was degraded.
    """

    @staticmethod
    def _fail_the_MINT_only(monkeypatch: pytest.MonkeyPatch) -> list[str]:
        """Make every edge-MINT transaction fail and let everything else through.

        Returns the (initially empty) list of statements that were REFUSED, so the caller can
        assert the degradation actually reached the door it is named after.
        """
        import importlib

        tasks_module = importlib.import_module("loremaster.tasks")
        real = tasks_module.execute_transaction
        refused: list[str] = []

        async def _selective(statement: str, *args: Any, **kwargs: Any) -> Any:
            if BLOCKS_RELATION_NAME in statement and "DEFINE" not in statement.upper():
                refused.append(statement)
                raise SurrealStoreError("the edge mint was rejected by the engine")
            return await real(statement, *args, **kwargs)

        monkeypatch.setattr(tasks_module, "execute_transaction", _selective, raising=True)
        return refused

    @pytest.mark.parametrize("door", BACKFILL_FAILURE_DOORS)
    async def test_a_FAILED_backfill_makes_ensure_ready_LOUD_not_SILENTLY_PARTIAL(
        self,
        door: str,
        monkeypatch: pytest.MonkeyPatch,
        legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]],
    ) -> None:
        """⛔ ∀ door, not just the one that was debugged."""
        connection, env, _ids = legacy_column_store
        refused: list[str] = []
        if door == "existence-read":

            async def _rejecting(*_args: Any, **_kwargs: Any) -> None:
                raise SurrealStoreError("the existence read was rejected by the engine")

            _patch_every_shared_policy_COROUTINE(monkeypatch, _rejecting)
        elif door == "mint":
            refused = self._fail_the_MINT_only(monkeypatch)
        else:  # pragma: no cover - a parametrisation entry with no degradation
            raise AssertionError(
                f"{door!r} is in BACKFILL_FAILURE_DOORS but this test degrades nothing for "
                f"it, so the leg would pass vacuously. Add its construction here"
            )

        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with pytest.raises(Exception) as caught:  # noqa: B017 - vocabulary is the builder's
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert not isinstance(caught.value, AssertionError), (
            f"ensure_ready raised the test's own AssertionError rather than propagating the "
            f"{door} failure — the pin is measuring itself: {caught.value!r}"
        )
        if door == "mint":
            assert refused, (
                f"no transaction naming {BLOCKS_RELATION_NAME!r} and free of DEFINE was ever "
                f"issued, so the MINT door was never degraded and this leg passed for a "
                f"reason having nothing to do with the invariant. Either the backfill minted "
                f"nothing (the fixture drifted) or the edge write no longer names its own "
                f"table, in which case re-derive this degradation in the same commit"
            )
            assert not await _blocks_edge_pairs_or_NO_TABLE(connection), (
                f"the mint was refused at the engine and yet edges exist: "
                f"{sorted(await _blocks_edge_pairs_or_NO_TABLE(connection))}"
            )

    async def test_POSITIVE_CONTROL_an_UNDEGRADED_boot_over_the_same_fixture_COMPLETES(
        self,
        legacy_column_store: tuple[SurrealConnection, SurrealEnv, dict[str, str]],
    ) -> None:
        """⛔ Without this, every leg above is satisfied by an ``ensure_ready`` that raises
        unconditionally — and by a fixture whose backfill has nothing to do, which would make
        the MINT door unreachable and its assertion vacuous.

        So: the SAME fixture, no degradation at all, must complete AND must mint the edges
        the mint leg's degradation is aimed at.
        """
        connection, env, ids = legacy_column_store
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert await _blocks_edge_pairs(connection) == _expected_backfilled_pairs(ids), (
            f"an undegraded boot over this fixture did not mint the expected edge set, so "
            f"the MINT door the legs above degrade is not on this path: "
            f"got={sorted(await _blocks_edge_pairs(connection))}"
        )


#: The legacy cycle TOPOLOGIES the record pin runs over, as ``{task: its blocked_by}`` specs.
#:
#: ⚠⚠ **CYCLE COUNT WAS THE THIRD MONOCULTURE AXIS** (delta adversary §PINS-3).  Every cycle
#: fixture in this file — :class:`TestALEGACYCycleIsMINTEDAndRECORDED` and
#: :class:`TestALegacyCycleOfEVERYARITYIsMINTEDAndRECORDED` alike — holds **exactly one
#: cycle**, so *"the cycle is RECORDED"* was ∀ over ARITY and ∀ over LIFECYCLE STATE and
#: silent about a store holding TWO.  MEASURED on a reference build: a legacy store with two
#: disjoint cycles left **2 of 4 members unnamed**, and the operator record — the surface
#: ESC-4 exists to create — served *"ONE cycle I found"* where the operator reads *"the
#: cycles in your store"*.
#:
#: ⚠ **AND IT IS NOT BAD LUCK: it is what the RECOMMENDED LIBRARY DOES.**
#: ``graphlib.CycleError`` reports exactly ONE cycle by construction (``prepare()``'s own
#: docstring: *"If any cycle is detected, CycleError will be raised"*) — correct for the
#: WRITE-time guard, where one witness is a complete refusal, and insufficient at migration
#: time, where the record is a claim about the whole store.  Enumeration is a DIFFERENT
#: mechanism from detection, and this contract pins the PROPERTY (every cycle recorded), never
#: a library.
#:
#: The three topologies are the axis this pin is ∀ over — a build that records only the first
#: cycle fails ALL THREE (measured 2026-07-28), and each fails it differently:
#: disjoint components, a shared-node overlap, and a fully-connected component.
LEGACY_CYCLE_TOPOLOGIES: dict[str, dict[str, tuple[str, ...]]] = {
    "disjoint-1-2-3": {
        "solo": ("solo",),
        "pairA": ("pairB",),
        "pairB": ("pairA",),
        "triA": ("triC",),
        "triB": ("triA",),
        "triC": ("triB",),
    },
    "overlapping": {"ova": ("ovb", "ovc"), "ovb": ("ova",), "ovc": ("ovb",)},
    "complete-triangle": {
        "cta": ("ctb", "ctc"),
        "ctb": ("cta", "ctc"),
        "ctc": ("cta", "ctb"),
    },
}

#: The disjoint topology's cycles, as member SETS — the only topology whose cycles can be
#: demanded one record each (see the class docstring's stated bound).
LEGACY_DISJOINT_CYCLE_MEMBERS: tuple[frozenset[str], ...] = (
    frozenset({"solo"}),
    frozenset({"pairA", "pairB"}),
    frozenset({"triA", "triB", "triC"}),
)


class TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST:
    """GREEN at ``b8607c4``.  ⛔ **ESC-4's load-bearing half, over the whole set it governs.**

    ESC-4's ruling is *"the backfill MINTS legacy cycles **and RECORDS them**"* — plural — and
    its stated reason is that *"the RECORD is what stops it being silent."*  A record naming
    one loop in a store holding three is itself a confident partial: the operator repairs what
    it names, re-boots, and is told the same thing about a store that is still broken.

    ⚠ **STATED BOUND, MEASURED 2026-07-28 and stated as a FACT rather than assumed away.**
    This class pins **MEMBER COVERAGE ∀ topology** (every member of every cycle is named
    somewhere at WARNING) and **ONE RECORD PER CYCLE only on the DISJOINT topology**.  It does
    NOT demand that the recorded cycle set equal ``networkx.simple_cycles``: on the
    ``complete-triangle`` topology the shipped enumeration records 4 loops where
    ``simple_cycles`` finds 5, while naming all 3 members — and pinning simple-cycle equality
    would make a correct-and-honest build RED, which is a C-DEF, not a catch.  What an
    operator needs is *which rows to repair*; what a cycle-count pin would demand is a
    particular decomposition of an overlapping component.  **RE-OPEN TRIGGER:** the day the
    record grows a per-cycle CONSUMER (a repair tool, a count served to an agent), that
    consumer's needs make the decomposition load-bearing and this bound must be re-argued.

    ⚠ **The independent enumerator is ``networkx``, and it is the TEST's oracle, never the
    build's mechanism** (operator-authorised at ``54d0585``).  Two independent enumerations
    are DIFFED — the contract does not hand the build its own answer key.
    """

    @staticmethod
    async def _seed_topology(
        connection: SurrealConnection, env: SurrealEnv, spec: dict[str, tuple[str, ...]]
    ) -> dict[str, str]:
        """Seed ``spec`` as legacy COLUMN rows, cycles and all; returns ``{name: row key}``.

        Every row is created with an EMPTY ``blocked_by`` and then closed by a raw ``UPDATE``,
        for :meth:`TestALEGACYCycleIsMINTEDAndRECORDED._cyclic_legacy_store`'s reason: after
        this packet lands no public verb mints a closing dependency, and ``ENFORCED`` could
        not carry one at creation time anyway.  Production holds such rows because they were
        legal when they were written.
        """
        await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
        ids = {name: f"{name}_{uuid.uuid4().hex}" for name in spec}
        for name in spec:
            await _seed_legacy_task(connection, ids[name], blocked_by=[], status=STATUS_OPEN)
        for name, blockers in spec.items():
            await run(
                connection,
                f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
                {"id": ids[name], "blocked_by": [ids[blocker] for blocker in blockers]},
            )
        return ids

    @classmethod
    async def _boot_and_capture(
        cls,
        caplog: pytest.LogCaptureFixture,
        store: tuple[SurrealConnection, SurrealEnv],
        spec: dict[str, tuple[str, ...]],
    ) -> tuple[dict[str, str], list[str]]:
        """Seed ``spec``, boot once, and return ``(ids, the WARNING+ records' full text)``.

        ⚠ The parameter is ``store``, not ``migration_db``: this module RE-EXPORTS the
        ``migration_db`` fixture at import, so a helper parameter of that name is an F811
        redefinition (ruff) rather than a readable echo of the caller's fixture.
        """
        connection, env = store
        ids = await cls._seed_topology(connection, env, spec)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        loud = [
            _recorded_text(record)
            for record in caplog.records
            if record.levelno >= logging.WARNING
        ]
        return ids, loud

    @staticmethod
    def _independent_cycles(spec: dict[str, tuple[str, ...]]) -> list[frozenset[str]]:
        """Every simple cycle of ``spec``, as member sets, enumerated by ``networkx``.

        The oracle is a SECOND implementation, deliberately: a contract that derived the
        expected set with the production detector would be grading a build against its own
        answer, and this section already has receipts against exactly that shape.

        ONE import site for the oracle, called by every leg that needs it — the alternative
        was the same four lines in three places, i.e. copy #2 of a policy (repo law #102).
        """
        # ⚠ ``types-networkx`` is not a dependency of this workspace; the house idiom for
        # that is a ``[[tool.mypy.overrides]]`` block in ``pyproject.toml`` (as ``astroid``
        # and ``kubernetes`` have), which is OUTSIDE this contract's writable set. Flagged in
        # ``REPORT-contractfix-04b1-r6.md`` §RESIDUALS with the exact edit; this inline
        # ignore is the version a test file may make on its own.
        import networkx  # type: ignore[import-untyped]

        graph = networkx.DiGraph()
        for node, blockers in spec.items():
            graph.add_node(node)
            for blocker in blockers:
                graph.add_edge(node, blocker)
        return [frozenset(cycle) for cycle in networkx.simple_cycles(graph)]

    @classmethod
    def _independent_cycle_members(cls, spec: dict[str, tuple[str, ...]]) -> set[str]:
        """Every node lying on SOME cycle of ``spec``, per the independent oracle."""
        members: set[str] = set()
        for cycle in cls._independent_cycles(spec):
            members.update(cycle)
        return members

    @pytest.mark.parametrize("topology", sorted(LEGACY_CYCLE_TOPOLOGIES))
    async def test_EVERY_MEMBER_of_EVERY_legacy_cycle_is_NAMED_in_the_record(
        self,
        topology: str,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ The property, ∀ topology: an operator can repair EVERY row that is in a loop.

        A build that records only the first cycle fails all three legs (measured): it names
        2 of 6 members on the disjoint topology and 2 of 3 on each of the other two.
        """
        spec = LEGACY_CYCLE_TOPOLOGIES[topology]
        expected_names = self._independent_cycle_members(spec)
        assert expected_names, (
            f"the {topology!r} spec holds NO cycle at all according to the independent "
            f"enumerator, so this leg asserts nothing: {spec}"
        )
        ids, loud = await self._boot_and_capture(caplog, migration_db, spec)
        named = {name for name in expected_names if any(ids[name] in text for text in loud)}
        assert named == expected_names, (
            f"the backfill mirrored the {topology!r} legacy cycles and left "
            f"{len(expected_names - named)} of {len(expected_names)} cycle members UNNAMED "
            f"at WARNING or above. ESC-4's ruling is that the backfill mints legacy cycles "
            f"AND RECORDS them, because 'the RECORD is what stops it being silent' — and a "
            f"record naming one loop in a store holding several is itself a confident "
            f"partial: the operator repairs what it names, re-boots, and is told the same "
            f"thing about a store that is still broken. ⚠ graphlib.CycleError reports "
            f"exactly ONE cycle by construction; DETECTION (one witness suffices) and "
            f"ENUMERATION (every loop) are different mechanisms. "
            f"unnamed={sorted(expected_names - named)} loud={loud!r}"
        )

    async def test_EVERY_DISJOINT_legacy_cycle_gets_its_OWN_record(
        self,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ Member coverage alone would be satisfied by ONE record listing every member of
        every loop — which tells an operator that some subset of six rows is tangled, not
        which three loops to break.  On DISJOINT components the decomposition is unambiguous,
        so it is demanded there and nowhere else (see the class's stated bound).
        """
        spec = LEGACY_CYCLE_TOPOLOGIES["disjoint-1-2-3"]
        ids, loud = await self._boot_and_capture(caplog, migration_db, spec)
        unrecorded = []
        for members in LEGACY_DISJOINT_CYCLE_MEMBERS:
            row_keys = {ids[name] for name in members}
            if not any(
                all(key in text for key in row_keys)
                and not any(
                    ids[other] in text for other in ids if other not in members
                )
                for text in loud
            ):
                unrecorded.append(sorted(members))
        assert not unrecorded, (
            f"{len(unrecorded)} of {len(LEGACY_DISJOINT_CYCLE_MEMBERS)} DISJOINT legacy "
            f"cycles have no record of their own — no WARNING names that loop's members and "
            f"only that loop's members. The three components share no row, so there is one "
            f"unambiguous decomposition and an operator is owed it per loop: 'these two rows "
            f"block each other' is actionable, 'six of your rows are tangled' is not. "
            f"unrecorded={unrecorded} loud={loud!r}"
        )

    async def test_POSITIVE_CONTROL_the_DISJOINT_fixture_really_holds_THREE_cycles(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - the fixture
    ) -> None:
        """⛔ Both legs above rest on the fixture holding more than one cycle.  If it held
        one, *"every cycle was recorded"* would be true of the record-the-first build this
        class exists to kill, and the whole class would be decoration.

        Asserted against the INDEPENDENT enumerator, at the arities the sibling classes pin
        one at a time — so this fixture is also the first place all three co-exist.
        """
        spec = LEGACY_CYCLE_TOPOLOGIES["disjoint-1-2-3"]
        cycles = self._independent_cycles(spec)
        assert sorted(cycles, key=len) == sorted(
            LEGACY_DISJOINT_CYCLE_MEMBERS, key=len
        ), (
            f"the disjoint fixture does not hold the three declared cycles: got "
            f"{[sorted(cycle) for cycle in cycles]}"
        )
        assert sorted(len(cycle) for cycle in cycles) == [1, 2, 3], (
            f"the three cycles are not one of each arity: "
            f"{sorted(len(cycle) for cycle in cycles)}"
        )
        connection, env = migration_db
        ids = await self._seed_topology(connection, env, spec)
        ledger = TestTheLedgersOwnMigrationPathLandsTheGuard._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        expected_edges = {
            (ids[blocker], ids[task])
            for task, blockers in spec.items()
            for blocker in blockers
        }
        assert await _blocks_edge_pairs(connection) == expected_edges, (
            f"the backfill did not MIRROR all three legacy cycles onto the edge table "
            f"(ESC-4 reading A), so the RECORD legs above are measuring a store whose "
            f"cycles were refused rather than minted: "
            f"got={sorted(await _blocks_edge_pairs(connection))}"
        )


# =========================================================================== #
# SECTION L — THE LEG-2 FORGERY CONSTRUCTIONS 04b-1 OWES.
#
# ``CLAUDE.md`` § TRUST — THE HARD DEFINITION, leg 2: derive the failure set (the surface's
# stateful dependencies × ``{stale, empty, wrong-instance, partial}``), CONSTRUCT each state,
# and BYTE-DIFF the served response against the healthy one.  **Identical bytes = a false
# clear = STOP.**  Construction, never reasoning: *"a missed world-state is discoverable …
# but a false belief about your own semantics is SELF-SEALING, and the only instrument that
# breaks it is execution."*
#
# ⚠ **THE BOUND ON THIS SECTION, STATED AS A FACT AND NOT AS A DISCLAIMER.**
# ``scripts/forgery_sites.py`` — the derivation the law's own clause implies and the design
# doc §12.2 specifies — DOES NOT EXIST.  The failure set worked from here is
# ``docs/design/2026-07-28-04b-model-consumer-audit.md`` §11.1's table, which its author
# labels (§12.3) a **CURATED INTERIM, bounded to five served surfaces and to one reader's
# sight**.  The law PERMITS a bounded interim and FORBIDS presenting it as complete.  So:
# **the constructions below cover the dependencies and verbs written down in §11.1 and
# nothing else.  A false clear found later is a RE-OPEN TRIGGER, never a retroactive pass.**
#
# Ownership, per this contract's brief: 04b-1 owns the TRAVERSAL-TIMEOUT row, the
# PRE-CHECK-FAILED-READ row (its migration-time half is SECTION K's last leg) and R9's
# HONEST-TOTAL row (which resolves to an ASSERTED EMPTINESS — see
# ``test_query_tasks_bounded.py::TestNoTOTALIsServedThatWasNotMEASURED``).  04b-2 owns the
# fleet-column and footer rows.
#
# ⚠ **A CORRECTION TO §11.1's OWN PRESCRIPTION, DERIVED HERE AND ESCALATED IN THE WAVE
# REPORT.**  That row asks for *"a TEACHING error naming the timeout"*.  The ledger CANNOT
# name it: ``_txn``'s hygiene boundary (ledger #31) withholds the engine text, and
# ``_classify_engine_error`` has no timeout label at all — every timeout arrives as
# ``unspecified rejection``.  A ledger that named it would be GUESSING, which is the
# fabrication class this packet already refused once (``TestTheResultIsSELFDESCRIBING``).
# The achievable and honest form is pinned instead: name the OPERATION, the BOUND it ran at,
# and the RECOVERY — and never serve a partial closure as a complete one.
# =========================================================================== #


class TestTheTraversalIsLOUDWhenTheSTOREFails:
    """RED today.  ⛔ §11.1 row 2 — *store × timeout/error mid-traversal*.

    THE FALSE CLEAR IT HUNTS: a partial set served as complete.  ``+collect`` truncating at
    the engine's bound is already handled honestly (``truncated``); a traversal that FAILS
    mid-flight is a different world, and a build that caught the failure and returned what
    it had — or returned an empty result — would render bytes a consumer cannot distinguish
    from *"this task has no blockers"*.

    THE CONSTRUCTION is the store seam raising, applied through
    :func:`_degrade_every_STORE_seam`, which DERIVES the seam set rather than listing it.
    The ledger is already connected by the fixture, which the helper's docstring requires.
    """

    @staticmethod
    async def _seed_then_degrade(
        monkeypatch: pytest.MonkeyPatch, ledger: TaskLedger, env: SurrealEnv
    ) -> tuple[str, list[str]]:
        """Seed a 4-chain, capture the HEALTHY served bytes, then break every store seam.

        Returns ``(healthy_served, chain)`` — the WHOLE chain, not just its leaf, because
        the caller has to REDACT every id out of a refusal before looking for a number in
        it.  A task id is a uuid4 hex, and a 32-char hex string contains a given two-digit
        substring more often than not: *"the bound is named in the message"* asserted over
        the raw text would pass on a message that names only the id.  A fixture that cannot
        distinguish the correct build from a plausible wrong one is decoration.

        On return the degraded world is live, so the caller's next ledger call is the
        constructed one.
        """
        setup = await connect_admin(env)
        try:
            chain = await _seed_chain(setup, 4)
        finally:
            await setup.close()
        healthy = await _served_outcome(_transitive_blockers(ledger, chain[-1]))
        unspecified, server_log_hint = _engine_hygiene_markers()

        async def _rejecting(*_args: Any, **_kwargs: Any) -> Any:
            raise SurrealStoreError(
                f"statement 1 of 1 was rejected ({unspecified}); {server_log_hint}"
            )

        _degrade_every_STORE_seam(monkeypatch, _rejecting)
        return healthy, chain

    async def test_a_FAILED_traversal_NEVER_renders_as_a_COMPLETE_answer(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔⛔ The byte diff.  A degraded read that renders the healthy bytes — or ANY
        ``OK …`` bytes — is a false clear and a STOP, not a pin to soften.
        """
        ledger, env, _blocker = task_ledger
        healthy, chain = await self._seed_then_degrade(monkeypatch, ledger, env)
        leaf = chain[-1]
        degraded = await _served_outcome(_transitive_blockers(ledger, leaf))
        assert healthy.startswith("OK "), (
            f"the healthy leg did not produce a result at all, so the diff below compares "
            f"two failures and discriminates nothing: {healthy!r}"
        )
        assert degraded != healthy, (
            f"a traversal whose store read was REJECTED served BYTE-IDENTICAL output to a "
            f"healthy one ({degraded!r}). Identical bytes across a healthy and a broken "
            f"world is the definition's false clear"
        )
        assert not degraded.startswith("OK "), (
            f"a traversal whose store read was REJECTED still returned a RESULT: "
            f"{degraded!r}. Whatever ids it carries, `truncated` on that object is a claim "
            f"about a walk that did not finish — partial served as complete, which is the "
            f"one thing the honest-bound design exists to prevent. leaf={leaf!r}"
        )

    async def test_the_FAILURE_teaches_the_OPERATION_the_BOUND_and_the_RECOVERY(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ Ruling T2 on the degraded path, in the only form the hygiene boundary permits.

        The ledger cannot name a TIMEOUT (see this section's header), so what it owes is:
        its OWN vocabulary (pinned by TYPE, so a subclass counts and a raw store error does
        not), no hygiene marker, the TASK it was asked about, and the BOUND it ran at —
        which is the whole of what a caller needs in order to choose between retrying
        smaller and giving up.
        """
        import loremaster.tasks

        ledger, env, _blocker = task_ledger
        _healthy, chain = await self._seed_then_degrade(monkeypatch, ledger, env)
        leaf = chain[-1]
        with pytest.raises(TaskLedgerError) as caught:
            await _transitive_blockers(ledger, leaf)
        message = str(caught.value)
        for marker in _engine_hygiene_markers():
            assert marker not in message, (
                f"the failed traversal served the store's hygiene text {marker!r} to the "
                f"caller: {message!r}"
            )
        assert leaf in message, (
            f"the failure does not name the task it was asked about ({leaf!r}): {message!r}"
        )
        redacted = message
        for task_id in chain:
            redacted = redacted.replace(task_id, "<task-id>")
        bound = getattr(loremaster.tasks, MAX_DEPTH_CONSTANT)
        assert str(bound) in redacted, (
            f"the failure does not name the depth bound it ran at ({bound}), so a caller "
            f"cannot compute a smaller re-ask — the same ambiguity amendment A3-a closed on "
            f"the SUCCESS path. (Asserted against the message with every task id REDACTED: "
            f"a uuid4 hex contains a given two-digit substring more often than not, so the "
            f"raw text would let a message naming only the id pass.) "
            f"redacted={redacted!r} raw={message!r}"
        )


async def _task_row_count_via_ADMIN(env: SurrealEnv) -> int:
    """The task-row count read on a SEPARATE admin connection.

    ⚠ Deliberately NOT :func:`_task_row_count`, which rides the ledger's own ``_query``:
    every caller below has DEGRADED that seam on purpose, so the ledger cannot be used to
    observe the store it is being tested against.  An instrument that shares the fault it is
    measuring reports whatever the fault says.
    """
    connection = await connect_admin(env)
    try:
        rows = await run(connection, f"SELECT count() FROM {TASK_TABLE} GROUP ALL")
    finally:
        await connection.close()
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


class TestTheBlockerPreCheckFAILSCLOSEDWhenItsOwnREADBreaks:
    """RED today.  ⛔ §11.1 row 5 — *blocker pre-check × {empty, error}*, on the WRITE path.

    THE FALSE CLEAR IT HUNTS IS FAIL-**OPEN**.  The pre-check exists to refuse a phantom
    blocker BEFORE anything is written; ruling R3 is explicit that this replaces *"a silent
    black hole"* (today a task naming a phantom blocker is created and is then unclaimable
    forever) with *"a loud refusal"*.  A degraded existence read that comes back EMPTY, or
    that throws, must never be read as *"nothing was wrong"* — that would restore the black
    hole through a door nobody constructed.

    ⚠ **AND THE TWO MODES ARE NOT THE SAME PIN**, which is §11.3's ran-and-empty vs
    check-FAILED distinction applied to this surface:

    * ``{empty}`` — indistinguishable, AT THIS LAYER, from *"the blockers genuinely are not
      there"*, so the correct behaviour IS the phantom refusal: **fail-closed**.  That the
      mode cannot be manufactured by a degraded store in the first place is what
      :class:`TestTheSTORESeamRAISESRatherThanReturningEMPTY` measures, one layer down.
    * ``{error}`` — a check that FAILED, and serving it as *"these ids name no task"* would
      be a lie with real consequences (the caller goes and creates a duplicate blocker).
      Its bytes must DIFFER from the phantom refusal's.
    """

    @staticmethod
    async def _create_naming(ledger: TaskLedger, blocker_id: str) -> None:
        await ledger.create_task(SUBJECT, DESCRIPTION, blocked_by=[blocker_id], created_by=CREATOR)

    async def test_an_EMPTY_existence_read_over_a_store_that_HAS_the_blocker_FAILS_CLOSED(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ Fail-CLOSED, and NOTHING written.  The blocker genuinely EXISTS in this store —
        the fixture created it — so a build that accepted this create would be accepting on
        the strength of a read that returned nothing.
        """
        ledger, env, real_blocker = task_ledger
        before = await _task_row_count_via_ADMIN(env)

        async def _empty(*_args: Any, **_kwargs: Any) -> Any:
            return []

        _degrade_every_STORE_seam(monkeypatch, _empty)
        with pytest.raises(TaskLedgerError) as caught:
            await self._create_naming(ledger, real_blocker)
        assert real_blocker in str(caught.value), (
            f"the refusal does not name the blocker whose existence could not be "
            f"established ({real_blocker!r}): {str(caught.value)!r}"
        )
        assert await _task_row_count_via_ADMIN(env) == before, (
            "a create whose blocker-existence read came back EMPTY still wrote a task row. "
            "That is the fail-open black hole ruling R3 closes, restored by a degraded "
            "dependency: the row is created and is then unclaimable forever, silently"
        )

    async def test_POSITIVE_CONTROL_the_SAME_create_SUCCEEDS_when_the_read_is_HEALTHY(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """Without this, the leg above is satisfied perfectly by a build that refuses EVERY
        create — the refuse-everything wrong build that a negative-only fixture cannot see.
        """
        ledger, env, real_blocker = task_ledger
        before = await _task_row_count_via_ADMIN(env)
        await self._create_naming(ledger, real_blocker)
        assert await _task_row_count_via_ADMIN(env) == before + 1, (
            "a create naming a REAL, existing blocker did not write a row, so the "
            "fail-closed leg above is measuring a build that refuses everything"
        )

    async def test_a_FAILED_existence_read_is_CLASSIFIED_not_served_as_the_PHANTOM_refusal(
        self, monkeypatch: pytest.MonkeyPatch, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔⛔ The byte diff, and the reason ``{error}`` is a separate mode from ``{empty}``.

        *"These ids name no task row"* is a FACT about the data.  Serving it when the check
        never ran is a false clear wearing the same bytes — §11.3's fourth leg, verbatim:
        *"ran-and-empty silence is a TRUE clear; check-failed silence is a false one wearing
        the same bytes."*  A caller told its blocker does not exist goes and creates a
        duplicate; a caller told the store is broken retries.

        ⚠ **ESCALATION ESC-3, RULED READING B (lead, 2026-07-28, on this wave's report):
        a failed pre-check is CLASSIFIED into the ledger's vocabulary, not merely
        distinguishable.**  This contract's author had pinned only the weaker property and
        recommended *"B eventually, A now"* out of C-DEF caution — a contract must not invent
        a requirement a correct build fails.  The ruling dissolves that risk: a correct build
        now classifies, so the type assertion below is satisfiable by construction.  Ruling,
        verbatim: *"T2 bans a raw ``(unspecified rejection)`` reaching a caller, and a store
        failure during the pre-check DOES reach one; that it is not caller-provoked changes
        who caused it, not what the caller can do with it."*

        ⚠ The stub raises with the seam's OWN laundered text rather than a friendly
        sentence, so the hygiene assertion measures something: a build that re-raises the
        store's error verbatim fails it, and a build that invents a nicer message could pass
        a check written against a nicer stub.
        """
        ledger, env, real_blocker = task_ledger
        before = await _task_row_count_via_ADMIN(env)
        unspecified, server_log_hint = _engine_hygiene_markers()

        async def _rejecting(*_args: Any, **_kwargs: Any) -> Any:
            raise SurrealStoreError(
                f"statement 1 of 1 was rejected ({unspecified}); {server_log_hint}"
            )

        _degrade_every_STORE_seam(monkeypatch, _rejecting)
        with pytest.raises(TaskLedgerError) as caught:
            await self._create_naming(ledger, real_blocker)
        message = str(caught.value)
        assert _served_task_refusal(real_blocker) not in message, (
            f"a create whose existence read FAILED was served the PHANTOM refusal — the "
            f"sentence that asserts, as a fact, that {real_blocker!r} names no task row. It "
            f"does name one; the check simply never ran. The caller acts on that by minting "
            f"a duplicate blocker. Two different worlds must not render the same bytes: "
            f"{message!r}"
        )
        for marker in (unspecified, server_log_hint):
            assert marker not in message, (
                f"the failed pre-check served the store's hygiene text {marker!r} to the "
                f"caller (ESC-3, ruled reading B). An agent holding this cannot tell its own "
                f"bad input from a broken tool: {message!r}"
            )
        assert await _task_row_count_via_ADMIN(env) == before, (
            "a create whose blocker-existence read FAILED still wrote a task row"
        )


#: The engine-rejection MODES this file constructs at the store seam, as
#: ``(label, statement, params)``.  ⚠ **A DERIVED-ENOUGH SET, AND ITS BOUND IS STATED IN THE
#: CLASS BELOW.**  Each is a DIFFERENT reason the engine refuses a statement — a malformed
#: one, an unresolvable function, a missing table, and a statement that ran and was cut off —
#: so a seam that raises for one reason and returns for another cannot pass by picking the
#: convenient mode.  MEASURED 2026-07-28 on spike-surreal 3.2.1: all four raise
#: ``SurrealStoreError`` through ``TaskLedger._query``.
#: ⚠ The labels are HYPHENATED and space-free ON PURPOSE: they become pytest parametrisation
#: ids, a parametrisation id becomes part of a node id, and a node id is what
#: ``scripts/mutation_proof.py --expect-red`` takes on a COMMAND LINE. A label carrying a comma
#: or a space is a declared-red entry somebody has to quote correctly under ``set -e``.
_ENGINE_REJECTION_MODES: tuple[tuple[str, str, dict[str, Any] | None], ...] = (
    ("malformed-statement", "SELECT * FROM task WHERE THIS IS NOT SURQL AT ALL", None),
    ("unknown-function", "SELECT no::such::function(1)", None),
    ("absent-table-SCANNED", "SELECT id FROM a_table_that_was_never_defined", None),
    ("cut-off-by-TIMEOUT", f"SELECT * FROM {TASK_TABLE} TIMEOUT 1ns", None),
)


class TestTheSTORESeamRAISESRatherThanReturningEMPTY:
    """GREEN before and after.  ⛔ The one-level-down control the ``{empty}`` mode needs.

    THE HONEST PROBLEM, stated rather than papered over: at the APP layer an existence read
    that returns ``[]`` because it FAILED and one that returns ``[]`` because the rows are
    genuinely absent are the SAME BYTES, and no amount of app-level care can separate them.
    Under the trust definition that would be a false clear — *unless the ``{empty}`` mode
    cannot be produced by a REJECTED read in the first place*.

    **WHAT THIS CLASS ESTABLISHES, stated exactly, because its first version did not.**
    A statement the ENGINE REJECTS raises through the ledger's shared seam; it never comes
    back as ``[]``.  So an app-layer ``{empty}`` cannot have been manufactured by a rejection,
    and every fail-closed refusal above is a refusal about the DATA rather than about a broken
    instrument.

    ⚠⚠ **AND THE CORRECTION THAT PRODUCED THIS VERSION, because the failure was this file's
    own class** (final adversary §SECL, 2026-07-28).  The single leg that used to close this
    mode measured **a PARSE ERROR** — *"SELECT \\* FROM task WHERE THIS IS NOT SURQL AT
    ALL"* — while promising, in its own name, that *"a REJECTED read RAISES"*.  A parse error
    is the ONE failure a FIXED statement string can never take: the existence policy's
    statement is a literal (``SELECT id FROM $ids``), so it parses on every run of every
    build.  The message named a general property; the assertion demonstrated one mode of it,
    and the mode it demonstrated was the unreachable one.  *Interrogate every assertion
    against its own failure message.*  The set is now :data:`_ENGINE_REJECTION_MODES`.

    ⚠ **THE BOUND, AS A FACT AND NOT A DISCLAIMER — and it is the ONE mode where an app-layer
    ``{empty}`` really can come from a degraded world.**  The existence read's shape is DIRECT
    RECORD ACCESS over bound ``RecordID``s, and that shape behaves DIFFERENTLY from a table
    scan: against a table that does not exist it returns **``OK []``**, not a rejection
    (MEASURED, and pinned below as ``test_KNOWN_BOUND_…``).  So this class's claim is bounded
    to *"the table exists"* — which the migration path guarantees, because ``ensure_ready``
    applies the DDL BEFORE the backfill reads anything.  The residue is a wrong-DATABASE or
    un-migrated world, and in that world there are no rows to back-fill either.
    **RE-OPEN TRIGGER, named: the first degraded state in which the shared existence probe
    returns a PARTIAL set** — a subset of the ids that really exist. That is the one shape
    neither this class nor the app layer can see, and finding it is a STOP.

    This is the ``ran-and-empty`` vs ``check-FAILED`` distinction §11.3 makes for the footer,
    applied one layer down and turned into a control rather than a claim.
    """

    @pytest.mark.parametrize(
        ("label", "statement", "params"),
        _ENGINE_REJECTION_MODES,
        ids=[label for label, _statement, _params in _ENGINE_REJECTION_MODES],
    )
    async def test_a_REJECTED_read_RAISES_it_does_not_come_back_as_an_EMPTY_LIST(
        self,
        label: str,
        statement: str,
        params: dict[str, Any] | None,
        task_ledger: tuple[TaskLedger, SurrealEnv, str],
    ) -> None:
        """⛔ Four modes, one property.  A seam that raised only on a malformed statement
        would pass a one-mode pin while laundering a TIMEOUT — the mode a deep traversal can
        actually take — into *"there was nothing"*.
        """
        ledger, _env, _blocker = task_ledger
        with pytest.raises(Exception) as caught:  # noqa: B017 - the seam's own type
            await _raw(ledger, statement, params)
        assert not isinstance(caught.value, AssertionError), (
            f"the seam raised the test's own AssertionError for mode {label!r}: "
            f"{caught.value!r}"
        )

    async def test_POSITIVE_CONTROL_a_read_that_MATCHES_NOTHING_returns_an_EMPTY_LIST(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """Without this the legs above are satisfied by a seam that raises on EVERYTHING, and
        then ``{empty}`` would be unreachable for a reason that has nothing to do with
        honesty.
        """
        ledger, _env, _blocker = task_ledger
        rows = await _raw(
            ledger,
            f"SELECT id FROM {TASK_TABLE} WHERE subject = $subject",
            {"subject": f"no task has this subject {uuid.uuid4().hex}"},
        )
        assert rows == [], (
            f"a legal read matching no rows did not come back as an empty list: {rows!r}"
        )

    async def test_POSITIVE_CONTROL_the_EXISTENCE_READS_OWN_SHAPE_answers_at_all(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ The control the bound below needs: the direct-record-access shape the shared
        policy actually issues RESOLVES a row that exists and DROPS one that does not.

        Without it, ``test_KNOWN_BOUND_…``'s empty answer is indistinguishable from a shape
        that reads nothing at all — a probe that always returns ``[]`` would satisfy it.
        """
        ledger, _env, real_blocker = task_ledger
        rows = await _raw(
            ledger,
            "SELECT id FROM $ids",
            {"ids": [RecordID(TASK_TABLE, real_blocker), RecordID(TASK_TABLE, ghost_id("nope"))]},
        )
        resolved = {_row_key(row["id"]) for row in rows if isinstance(row, dict)}
        assert resolved == {real_blocker}, (
            f"the existence read's own shape did not resolve exactly the one id that exists. "
            f"A non-existent RecordID is silently DROPPED (agent_existence's probed "
            f"property), so the missing set is requested − returned: {rows!r}"
        )

    async def test_KNOWN_BOUND_the_EXISTENCE_SHAPE_on_an_ABSENT_TABLE_returns_EMPTY_not_a_RAISE(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str]
    ) -> None:
        """⛔ **WHEN YOU CANNOT CLOSE A HOLE, PIN IT.**

        A table SCAN of an absent table is REJECTED (mode 3 above).  **Direct record access
        over the same absent table is not** — it returns ``OK []``, exactly as it does for a
        row that is merely missing.  So the two worlds *"this table has never been defined"*
        and *"these ids name no row"* render IDENTICAL BYTES at this seam, and the class
        docstring's claim is bounded to a store whose ``task`` table exists.

        This leg exists so the bound is met DELIBERATELY.  It is not a defect to fix at this
        layer: ``ensure_ready`` applies the DDL before anything reads, and a store with no
        ``task`` table has no rows to resolve either.

        ⚠ **NAMED RE-OPEN TRIGGER:** the day the engine starts REJECTING direct record access
        over an undefined table, this pin goes RED — and that reddening is good news, because
        it means the class docstring's bound can be deleted.  **If you are reading this after
        a SurrealDB upgrade, delete the pin and the bound together, in the same commit.**
        """
        ledger, _env, _blocker = task_ledger
        rows = await _raw(
            ledger,
            "SELECT id FROM $ids",
            {"ids": [RecordID("a_table_that_was_never_defined", ghost_id("nope"))]},
        )
        assert rows == [], (
            f"direct record access over an UNDEFINED table no longer returns an empty list: "
            f"{rows!r}. If it now RAISES, this bound is closed — delete this pin and the "
            f"paragraph in this class's docstring that states the bound"
        )


class TestTheScopeOfTheTransitiveReadIsSTATED:
    """RED today.  ⛔ **LEG 1 — the SCOPE DIFF**, for the one row where a difference REMAINS.

    R11's backfill deletes the *edges-vs-column* difference for every blocker that resolves.
    What it cannot delete is the PHANTOM entry: ``ENFORCED`` forbids the edge, R11 skips it,
    and #236 rules the cleanup of such rows OUT — so a legacy ``blocked_by`` naming no task
    row is, permanently, in the COLUMN and not in the traversal.

    Leg 1's question — *"what question did I actually answer, and is it the one the consumer
    thinks they asked?"* — therefore has one honest residue, and the law says a difference
    that exists goes in the render.  The LEDGER's half of that is its docstring; 04b-2 owns
    the rendered half.

    ⚠⚠ **A SERVED-ENGLISH pin, in this file's established idiom
    (``test_the_helpers_docstring_states_the_FLOOR_property``) — AND THE BOUND IS STATED
    EXACTLY RATHER THAN AS "PRESENT, NOT TRUE"** (ESC-3, lead-ruled 2026-07-28).  It checks
    that the tokens ``blocked_by`` and ``phantom`` are PRESENT.  MEASURED: a docstring reading
    *"Ignores the ``blocked_by`` column entirely; a ``phantom`` entry IS included in this
    answer, which is a floor"* — **the exact INVERSE of the truth** — passes this pin.  **A
    docstring asserting the OPPOSITE of the bound satisfies it.**  The failure mode a reader
    would infer from *"presence, not truth"* is SILENCE; the real one is INVERSION, and a
    disclosure that understates its own bound is the false-gate class this repo names (*"a
    failure message that promises a check the assertion does not perform"*).

    The ruling ACCEPTS this bound deliberately — reading (ii), a phrase-level assertion, was
    REJECTED as inventing a requirement no ruling carries and as a C-DEF risk.  This is
    *when you cannot close a hole, PIN it* applied to a hole we are keeping: the next engineer
    meets it with its rationale attached rather than rediscovering it.  What makes the words
    TRUE is SECTION K's exact-set backfill pin.
    """

    def test_the_helpers_docstring_names_the_PHANTOM_BLOCKER_bound(self) -> None:
        helper = getattr(TaskLedger, TRANSITIVE_BLOCKERS_ATTR, None)
        assert helper is not None, (
            f"TaskLedger.{TRANSITIVE_BLOCKERS_ATTR} does not exist — see this file's "
            f"_transitive_blockers handle"
        )
        docstring = (helper.__doc__ or "").lower()
        assert "blocked_by" in docstring and "phantom" in docstring, (
            f"the transitive read's docstring does not state its one remaining scope "
            f"difference. It answers 'blockers reachable over blocks EDGES'; a consumer "
            f"asks 'what blocks this task', and after R11's backfill those sets differ by "
            f"exactly one thing — a legacy blocked_by entry naming NO task row, which "
            f"ENFORCED forbids as an edge and the backfill skips. State it as a FACT (a "
            f"bound is a fact, never a disclaimer): the read covers blocked_by entries that "
            f"name a live task row, and a PHANTOM entry is not among them. "
            f"docstring={helper.__doc__!r}"
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
#   PROOF 5 (``refers`` / ``answers_to``) — **EXECUTED 2026-07-28 at `faf035d`, BOTH LEGS:
#     PROOF HELD, 4/4 declared, no unexpected reds, no declared-green, EXIT=0 unpiped, tree
#     restored byte-exact (surreal_schema.py md5 dc5dc6f18eb6dc87dbb8cd8d26df417d).**
#     Swap the endpoint tables in each call:
#
#     for pair in "REFERS_RELATION:refers-endpoints3" "ANSWERS_TO_RELATION:answers_to-endpoints0"; do
#       REL="${pair%%:*}"; PID="${pair##*:}"
#       ./scripts/mutation_proof.py \
#         --file loremaster/loremaster/store/surreal_schema.py \
#         --anchor "_define_relation_table($REL, CODE_NODE_TABLE, NAME_TABLE)" \
#         --replacement "_define_relation_table($REL, NAME_TABLE, CODE_NODE_TABLE)" \
#         --expect-red "$X::test_the_edge_declares_its_IN_and_OUT_endpoint_tables[$PID]" \
#         --expect-red "$X::test_the_edge_declares_its_IN_and_OUT_endpoint_tables[blocks-endpoints1]" \
#         --expect-red "$X::test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS[blocks]" \
#         --expect-red "$X::test_the_relation_edge_set_is_EXACTLY_the_five_known_edges" \
#         -- uv run pytest -q --show-capture=no "$G"
#     done
#
#     — the parametrised id must be taken from ``--collect-only``, never typed from the
#     source (pytest ASCII-escapes and index-suffixes parametrised ids, and adding ``blocks``
#     to ``KNOWN_RELATION_EDGES`` RENUMBERED every ``endpointsN`` suffix in that pin).
#
#     ⚠ **TWO CORRECTIONS TO THIS BLOCK, both found by RUNNING it (adversary R-2 + this
#     wave), and both of the same shape — a proof whose declared set was right for a tree
#     nobody said out loud:**
#
#     1. It carried NO "+ this contract's three already-RED ``blocks`` declaration pins"
#        clause, which PROOF 3's and PROOF 4's blocks both carry.  Verbatim execution
#        returned ``PROOF FAILED / EXIT=4`` on a correct tree — and the builder's next move
#        is to "fix" it by editing the declared list, which is the exact anti-pattern
#        ``mutation_proof.py`` exists to prevent.  The clause is now spelled out above.
#     2. It ran over ``"$F" "$G"``, inherited from PROOFS 1–2 whose declared reds span both
#        files.  Every red PROOF 5 declares lives in ``$G``; adding ``$F`` on a pre-build
#        tree contributes 70-odd unexpected reds that have nothing to do with the mutation.
#        Scope each proof to the files its declared set actually names.
#
# ⚠⚠ **AND THE CLAUSE ITSELF IS TREE-DEPENDENT — READ THIS BEFORE RE-RUNNING PROOFS 3–5.**
#   Those three ``blocks`` declaration pins are RED *because the build has not landed*.  The
#   moment the builder emits the edge they go GREEN, and a declared set still naming them
#   produces DECLARED REDS THAT STAYED GREEN — a FAILED verdict for the opposite reason, in
#   the direction the both-ways diff exists to catch.  So:
#
#     * BEFORE the build lands (where PROOFS 3–5 are runnable at all, since they mutate
#       clauses that already exist): declare the three.
#     * AFTER the build lands: DROP the three, and re-derive the rest from ``--collect-only``.
#
#   PROOFS 1 and 2 are the mirror image — they mutate code the build ADDS, so they can only
#   run afterwards, and their declared sets must never carry the clause.
#
# ─────────────────────────────────────────────────────────────────────────────
# PROOFS 6–9 — ROUND 3's rulings (R10(ii) · T1 · T5 · R9).  Added 2026-07-28.
#
# ⚠ ALL FOUR MUTATE CODE THE BUILD ADDS, so like PROOFS 1–2 they can only run AFTER it
# lands, and their declared sets must NOT carry the "three already-RED blocks declaration
# pins" clause.  Every node id below was taken from ``pytest --collect-only -q``, never
# typed from source and never transcribed from a run.
#
#   Q="$F::TestASupersededBlockerIsNotASilentBlackHole"
#   R="$F::TestTheDuplicateBlockerDivergence"
#   B=loremaster/tests/test_query_tasks_bounded.py
#   S="$B::TestTheCapAppliesToTheANSWERNotTheCandidateScan"
#   T="$B::TestLimitIsLEGALForQueryAtTheToolSeam"
#
# PROOF 6 — R10(ii), the superseded-blocker refusal.  Neutralise ONLY the supersession
#   branch of the pre-check (leave the phantom branch alone), e.g. drop the
#   ``superseded_by`` projection from the grouped existence read so every existing row
#   reads as live.  DECLARED RED (5): every refusal leg, and NOT the two controls.
#     --expect-red "$Q::test_a_create_blocked_on_a_SUPERSEDED_task_is_REFUSED"
#     --expect-red "$Q::test_the_refusal_NAMES_THE_SUCCESSOR_and_says_what_to_do_INSTEAD"
#     --expect-red "$Q::test_the_refusal_ALSO_states_that_NOTHING_was_created"
#     --expect-red "$Q::test_a_refused_create_writes_NO_task_row"
#     --expect-red "$Q::test_create_many_ALSO_refuses_a_SUPERSEDED_blocker_and_writes_NO_ROWS"
#   ⚠ ``test_a_DEPENDENT_created_BEFORE_the_supersede_is_NOT_silently_unblocked`` must stay
#   GREEN under this mutation, and that is the POINT: it guards the OTHER direction (the
#   reading R10 rejected), so a mutation to the pre-check may not move it. If it reddens,
#   the pre-check and the blocker-resolution path have been coupled.
#
# PROOF 7 — T5, the duplicate-blocker divergence.  Mutate the claim CAS back:
#     --anchor "array::len(array::distinct(blocked_by))" --replacement "array::len(blocked_by)"
#   DECLARED RED (2):
#     --expect-red "$R::test_a_LEGACY_row_with_a_DUPLICATED_resolved_blocker_is_CLAIMABLE_in_BOTH"
#     --expect-red "$R::test_EXACTLY_ONE_of_EIGHT_racers_wins_a_row_with_a_DUPLICATED_blocker"
#   ⚠ ``test_POSITIVE_CONTROL_a_DUPLICATED_UNRESOLVED_blocker_stays_BLOCKED_in_BOTH`` stays
#   GREEN — it is the leg that fires on the OPPOSITE error (dropping the dependency), so a
#   proof that reddened it would have proved the two legs are one leg.
#
# PROOF 8 — T1, the cap on the ANSWER.  Mutate the cap onto the CANDIDATE SCAN (push the
#   caller's ``limit`` into the WHERE-bearing statement and let the client-side ``blocked``
#   filter cut it afterwards — the naive composition of R5 and #253).  DECLARED RED (2):
#     --expect-red "$S::test_a_capped_BLOCKED_query_serves_the_FULL_cap_when_the_answer_is_bigger"
#     --expect-red "$S::test_a_SHORT_answer_means_the_scan_was_EXHAUSTED_never_silently_truncated"
#   ⚠ The SANDWICH control stays GREEN (it supplies no ``limit``). If it reddens, the
#   fixture drifted and the two legs above are measuring nothing.
#
# PROOF 10 — RULING R11, the ``ensure_ready`` BACKFILL.  Added 2026-07-28 (wave r4).
#   Like PROOFS 1–2 and 6–9 it mutates code the build ADDS, so it can only run afterwards
#   and its declared set must NOT carry the "three already-RED blocks declaration pins"
#   clause.  Node ids to be re-derived from ``--collect-only`` at execution time.
#
#   K="$F::TestTheBACKFILLClosesTheLEGACYEdgeGap"
#   L="$F::TestThePHANTOMBlockerIsSKIPPEDAndRECORDED"
#   M="$F::TestTheBackfillIsIDEMPOTENT"
#   N="$F::TestTheBackfillRoutesThroughTheSHAREDExistencePolicy"
#
# ⚠ FOUR MORE CLASSES JOINED SECTION K ON 2026-07-28 (wave r5), and every declared set below
# had to be RE-DERIVED against them — a declared set that predates a class is a declared set
# with a hole, in the direction the both-ways diff exists to catch:
#   (letters U/V/W/Z, because A/B/C/D/E/G/H/K/L/M/N/P/Q/R/S/T/X/Y are already bound above —
#    a reused letter silently re-points every proof that already used it.)
#   U="$F::TestALegacyCycleOfEVERYARITYIsMINTEDAndRECORDED"
#   V="$F::TestTheBackfillMirrorsADependencyOnASUPERSEDEDTask"
#   J="$F::TestTheBackfillMirrorsADependencyOnATERMINALBlocker"
#   W="$F::TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS"
#   Z="$F::TestTheBackfillIsONETransaction"
#
# PROOF 10a — DELETE THE BACKFILL (the S3 world, restored).  Whatever call ``ensure_ready``
#   makes into the backfill, remove it.  DECLARED RED (7):
#     --expect-red "$K::test_ensure_ready_BACKFILLS_the_edges_from_the_EXISTING_columns"
#     --expect-red "$K::test_the_BACKFILLED_answer_DIFFERS_from_the_UN_backfilled_one"
#     --expect-red "$K::test_the_backfill_covers_a_TERMINAL_row_too_not_only_the_OPEN_ones"
#     --expect-red "$L::test_the_PHANTOM_edge_is_NOT_minted_and_the_MIGRATION_STILL_LANDS"
#     --expect-red "$L::test_the_phantom_SKIP_is_RECORDED_never_silent"
#     --expect-red "$M::test_a_SECOND_ensure_ready_neither_RAISES_nor_DUPLICATES"
#     --expect-red "$M::test_the_backfill_does_NOT_re_mint_over_edges_a_WRITE_PATH_already_made"
#     --expect-red "$N::test_MUTATION_neutralising_the_shared_policy_STOPS_the_backfill"
#     --expect-red "$N::test_a_FAILED_existence_read_makes_ensure_ready_LOUD_not_SILENTLY_PARTIAL"
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_MINTED_as_an_EXACT_edge_set[arity-1]"
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_MINTED_as_an_EXACT_edge_set[arity-3]"
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_RECORDED_never_silent[arity-1]"
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_RECORDED_never_silent[arity-3]"
#     --expect-red "$U::test_the_TRAVERSAL_TERMINATES_over_a_backfilled_cycle_of_this_ARITY[arity-3]"
#     --expect-red "$V::test_a_legacy_dependency_on_a_SUPERSEDED_task_is_STILL_MIRRORED"
#     --expect-red "$J::test_a_legacy_dependency_on_a_TERMINAL_task_is_STILL_MIRRORED[done-blocker]"
#     --expect-red "$J::test_a_legacy_dependency_on_a_TERMINAL_task_is_STILL_MIRRORED[wontfix-blocker]"
#     --expect-red "$W::test_a_row_whose_blockers_ALL_RESOLVE_is_CLAIMABLE_whenever_the_traversal_is_EMPTY"
#     --expect-red "$Z::test_the_BOOTs_round_trips_do_NOT_grow_with_the_number_of_LEGACY_edges"
#   ⚠ ``$K::test_WITHOUT_the_backfill_the_traversal_serves_a_CONFIDENT_EMPTY`` and BOTH legs
#   of ``TestTheNakedBackfillWouldRollTheMigrationBack`` must stay GREEN: they describe the
#   ENGINE and the pre-R11 world, never the build. If they redden, the mutation reached
#   further than the backfill and the declared set above is measuring the wrong thing.
#   ⚠ THREE MORE MUST STAY GREEN, and each for a REASON worth knowing rather than as a
#   bookkeeping note — they are the legs whose subject is NOT the backfill:
#     * ``$U::test_the_TRAVERSAL_TERMINATES_over_a_backfilled_cycle_of_this_ARITY[arity-1]``
#       — at arity 1 there is no OTHER member to reach, so its reach assertion is vacuously
#       satisfied by an empty answer. It discriminates termination, not minting.
#     * ``$V::test_a_SKIP_is_never_RECORDED_as_a_PHANTOM_when_the_row_EXISTS`` — it asserts
#       an ABSENCE, and a backfill that never runs records nothing at all.
#     * ``$W::test_KNOWN_BOUND_a_PHANTOM_blocker_is_the_ONE_row_the_traversal_CANNOT_see``
#       — the phantom residue is what the backfill CANNOT close, so deleting the backfill
#       cannot change it.
#   (COUNT THE LINES rather than trusting a number. This block has now carried a wrong count
#   twice — "seven" where the list held nine, corrected below; and "EIGHTEEN" for one edit,
#   before $J's two legs joined it. That is exactly why the instruction is COUNT rather than
#   a number, and why no number is stated here now.)
#
# PROOF 10b — DROP THE PRE-FILTER (a NAKED backfill).  Let the phantom RELATE into the
#   migration transaction.  DECLARED RED: every leg of $K, $L and $M — the whole migration
#   rolls back, so nothing lands at all — plus
#   ``$B::test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE``, which drives the same
#   entry point on a store whose rows are edge-less, plus BOTH legs of $W (its fixture is the
#   only wave-r5 one carrying a PHANTOM, so it is the only one whose ``ensure_ready`` fails).
#   ⚠ THIS PROOF IS THE ONE THAT SAYS R11's wrinkle is real: if it comes back with FEWER reds
#   than that, the migration is not one transaction and
#   ``TestTheNakedBackfillWouldRollTheMigrationBack`` is lying.
#   ✅ **AND THAT PREMISE IS NOW PINNED ON THE BUILD, WHICH IT WAS NOT** —
#   ``$Z::test_the_BOOTs_round_trips_do_NOT_grow_with_the_number_of_LEGACY_edges``.  Before
#   wave r5 a build that issued one RELATE per edge satisfied the whole contract, and against
#   it this proof returns FEWER reds than declared → ``PROOF FAILED`` → and the builder's next
#   move is to edit the declared list, the exact anti-pattern the script exists to prevent.
#   ⚠ $U/$V (acyclic-or-cyclic but PHANTOM-FREE fixtures) and $Z (a phantom-free chain) must
#   stay GREEN: a naked backfill only rolls back a migration that MEETS a phantom.
#
# PROOF 10c — MAKE THE SKIP SILENT (delete the log call, keep the skip).  DECLARED RED (1):
#     --expect-red "$L::test_the_phantom_SKIP_is_RECORDED_never_silent"
#   ⚠ ``$L::test_a_store_whose_blockers_ALL_RESOLVE_records_NO_skip`` must stay GREEN — it
#   fires on the OPPOSITE error (recording a skip that never happened), so a proof that
#   reddened both would have proved the two legs are one leg.  So must
#   ``$V::test_a_SKIP_is_never_RECORDED_as_a_PHANTOM_when_the_row_EXISTS``, for the same
#   reason one level over: it fires on a skip record that names the WRONG row, and deleting
#   the record cannot produce one.
#
# PROOF 10d — ESC-4 (lead-ruled 2026-07-28), the LEGACY CYCLE.  Make the backfill REFUSE a
#   cycle instead of minting it (reading B, which the ruling rejected).  DECLARED RED (3):
#   every leg of C="$F::TestALEGACYCycleIsMINTEDAndRECORDED", PLUS every ARITY leg wave r5
#   added and the agreement pin the self-loop shape reaches:
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_MINTED_as_an_EXACT_edge_set[arity-1]"
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_MINTED_as_an_EXACT_edge_set[arity-3]"
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_RECORDED_never_silent[arity-1]"
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_RECORDED_never_silent[arity-3]"
#     --expect-red "$U::test_the_TRAVERSAL_TERMINATES_over_a_backfilled_cycle_of_this_ARITY[arity-3]"
#     --expect-red "$W::test_a_row_whose_blockers_ALL_RESOLVE_is_CLAIMABLE_whenever_the_traversal_is_EMPTY"
#   (SIX added; COUNT THE LINES.)  ⚠ Every leg of $K/$L/$M, all of $V and $Z, and
#   ``$U::…TERMINATES…[arity-1]`` must stay GREEN — those fixtures are ACYCLIC (or, at arity
#   1, reach nothing to lose), so a cycle-refusing backfill may not move them. If one reddens,
#   the refusal is firing on acyclic rows and the fixtures are not independent.
#
# PROOF 10e — WB-A (MEASURED to survive the pre-r5 contract, 215 passed / 0 failed): SKIP THE
#   SELF-LOOP.  Insert, inside the backfill's per-dependency loop and BEFORE the mint,
#   ``if blocker == task_id: continue`` — the one defensive line a builder writes for the
#   sincerely-held reason *"a task cannot block itself, so don't mint that edge"*.
#   DECLARED RED (2):
#     --expect-red "$U::test_a_legacy_CYCLE_of_this_ARITY_is_MINTED_as_an_EXACT_edge_set[arity-1]"
#     --expect-red "$W::test_a_row_whose_blockers_ALL_RESOLVE_is_CLAIMABLE_whenever_the_traversal_is_EMPTY"
#   ⚠ BOTH ``[arity-3]`` legs must stay GREEN — a 3-cycle contains no ``blocker == task``
#   pair, and that asymmetry is what proves the two arities discriminate DIFFERENT doors
#   rather than being one pin wearing two ids.  ``$U::…RECORDED…[arity-1]`` is NOT declared:
#   whether the cycle is still LOGGED depends on where the mutation sits relative to the
#   detector, and a declared red that turns on the mutation's placement is a prediction about
#   the mutation rather than about the build.
#
# PROOF 10f — WB-B (MEASURED to survive the pre-r5 contract, 215 passed / 0 failed): CARRY
#   R10(ii) INTO THE MIGRATION.  Subtract the SUPERSEDED ids from the resolved set the shared
#   probe returns, BEFORE the skip is recorded — so the migration both drops the edge and
#   files the drop under the phantom record.  DECLARED RED (3):
#     --expect-red "$V::test_a_legacy_dependency_on_a_SUPERSEDED_task_is_STILL_MIRRORED"
#     --expect-red "$V::test_a_SKIP_is_never_RECORDED_as_a_PHANTOM_when_the_row_EXISTS"
#     --expect-red "$W::test_a_row_whose_blockers_ALL_RESOLVE_is_CLAIMABLE_whenever_the_traversal_is_EMPTY"
#   ⚠ THE PLACEMENT IS PART OF THE MUTATION, not an incidental detail: subtracting AFTER the
#   skip record reddens only the first and third legs, and a declared set that does not say
#   which variant it was written against is a prediction nobody can reproduce.
#   ⚠ Every leg of $K/$L/$M/$U/$Z must stay GREEN — no other fixture holds a superseded row.
#
# PROOF 10g — WB-C (MEASURED to survive the pre-r5 contract): N SEPARATE WRITES.  Replace the
#   composed migration transaction with a loop issuing one write per fragment.  DECLARED
#   RED (1):
#     --expect-red "$Z::test_the_BOOTs_round_trips_do_NOT_grow_with_the_number_of_LEGACY_edges"
#   ⚠ EVERY leg of $K/$L/$M/$N/$U/$V/$J/$W must stay GREEN, and that is the whole point: the
#   edges still LAND, so nothing that looks at the resulting edge set can tell the two builds
#   apart. Only the round-trip growth can.
#
# PROOF 10h — THE OTHER HALF OF THE LIFECYCLE AXIS: SKIP A BLOCKER THAT ALREADY FINISHED.
#   Filter the backfill's dependency set to blockers whose status is NOT in the terminal set —
#   *"that dependency is done, there is nothing to mint"*.  DECLARED RED (2):
#     --expect-red "$J::test_a_legacy_dependency_on_a_TERMINAL_task_is_STILL_MIRRORED[done-blocker]"
#     --expect-red "$J::test_a_legacy_dependency_on_a_TERMINAL_task_is_STILL_MIRRORED[wontfix-blocker]"
#   ⚠ $W must stay GREEN, and that is the FINDING this proof records rather than a footnote:
#   a row blocked only by a DONE task is CLAIMABLE, so the traversal and the CAS still agree
#   and the ∀-over-outcomes pin cannot see this defect at all. It breaks the MIRROR and
#   nothing else — which is why the mirror needs a pin of its own over this axis.
#   ⚠ Every leg of $K/$L/$M/$U/$V/$Z must stay GREEN: no other fixture holds a TERMINAL blocker
#   (``LEGACY_TERMINAL_TASK`` is a terminal ROW whose blocker is ``open`` — a different axis,
#   and the reason this one went unnoticed).
#
# PROOF 11 — WB-D (MEASURED to survive the pre-r5 contract: rows read 10 → 65): #253 ON THE
#   WRITE PATH.  Drop the dependency-bearing filter from the write-time cycle guard's single
#   read, so the client-side walk is seeded with the whole task table.  DECLARED RED (1):
#     --expect-red "$E2::test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_DEPENDENCY_FREE_population"
#         (E2="$F::TestCreateRefusesToFormACycle")
#   ⚠ RENAMED in wave r6 (was "…_with_the_size_of_the_LEDGER"): the old name promised a
#   ∀-ledger property the assertion cannot perform — see the test's own docstring. The
#   MUTATION and its declared red set are unchanged; only the node id moved.
#   ⚠ ``$E2::test_KNOWN_BOUND_the_write_paths_rows_READ_DOES_grow_with_the_BLOCKED_population``
#   must stay GREEN under this mutation: dropping the filter makes the read grow with EVERY
#   population, and that pin asserts growth. It is a KNOWN-BOUND pin, not a boundedness one.
#   ⚠ ``$E2::test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain`` must stay GREEN —
#   the walk is still ONE round trip, it simply reads the whole ledger inside it. That a
#   round-trip pin cannot see a rows defect is exactly why the rows pin had to exist.
#
# PROOF 9 — R9, the surgical widening.  Mutate the strict-parameter guard back to ONE
#   sentence covering both parameters:
#     --anchor "'since'/'limit' apply only to action='rollup'"  (whatever the split spells)
#   DECLARED RED (1):
#     --expect-red "$T::test_SINCE_on_action_QUERY_is_STILL_REFUSED_and_stops_claiming_limit_is_too"
#   ⚠ ``test_limit_on_a_NON_query_NON_rollup_action_is_STILL_REFUSED`` stays GREEN under THIS
#   mutation — it is GREEN at ``5a2dca9`` too. It exists to catch the OPPOSITE one, and that
#   proof was EXECUTED 2026-07-28 in a scratch copy: deleting the whole guard block reddens
#   BOTH legs of $T (2/2, EXIT=0, server.py restored byte-exact md5
#   f0341e3e8558a1b67d063600763b57d5). That run is also why this class has no
#   "limit on query is ACCEPTED" leg — see the comment in $T's own body.
# =========================================================================== #
