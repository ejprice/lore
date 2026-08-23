# REPORT — contract-61a-w3

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done (rev 2 — adversary RG-A blocker CLOSED) — RED contract for packet 61a-w3 (#398/#399 recurrence invariant); satisfiability re-proven.
- **Deliverable:** `loremaster/tests/test_schema_fold_coverage.py` (**29 pins**, tests only — NO production code).
- **Rev-2 change (adversary RG-A):** added a VARIABLE-returner fixture (`return statements`, the idiom **20 of 28** real slices use) + 5 pins that RED a literal-only `_emits`; mutation-proven (§"Adversary RG-A closure"). Also added the SECONDARY standalone-via-dead-generate pin-the-miss.
- **Deviations:**
  - Standalone membership is DERIVED (called-by-some-`generate_*_ddl`), NOT a literal hand-list — §Fork J writes "explicit allowlist" but its own rider + INSTRUMENT-0 demand derived-not-hand-list. Reasoned decision; alternative noted (§"Standalone allowlist"). Adversary/lead to confirm.
  - Scan is SOURCE-based (not dynamic import+call): emptiness is conservative-static (empty iff provably `return []`), fail-toward-flagging, never a false clear (§"Why source-based").
- **Packages considered:** none — no runtime mechanism; the instrument is a stdlib `ast` scan. Reuse is INTERNAL (see Reuse ledger).
- **Reuse ledger:** 0 new *production* symbols. The scan (builder's) should prefer existing test-support home `_logging_fixtures` or a dedicated `_schema_fold_guard`; my contract adds only test symbols. See §"DRY".
- **Graded:** n/a (contract author — I render no verdict on another's artifact). Authored at `f87e774`; HEAD-at-report `f87e774` (SAME).
- **Decisions-needed:**
  1. Confirm DERIVED-standalone vs literal-allowlist reading (I chose derived; see §"Standalone allowlist").
  2. Scope-adjacent: `test_principal_keys_schema.py:4-6` is a LIVE stale RED-STUB docstring (same #398/#399 class, in the test tree) — fix now or ledger? (§"Flags").
- **Receipt pointers:** derivation → §"How the slice-fn set was derived"; evidence table → §"Standalone allowlist"; satisfiability → §"Satisfiability receipt"; reference scan verbatim → §"Appendix A"; node sets → §"Node sets".

---

## What the contract pins (§Fork J executed)

The instrument is a structural AST scan of `surreal_schema.py` + a pytest contract. My contract
specifies WHAT the scan must do and pins its discrimination; the **builder writes the scan**. Two
legs, per the ruling:

1. **PRIMARY — structural fold-coverage (undefeatable by rewording).** Slice-fn set DERIVED by AST
   (`^_[a-z0-9_]+_statements$`, re-derived each run). Every slice fn that EMITS ≥1 statement must be
   FOLDED (called in `generate_ddl`) OR STANDALONE (called in some other `generate_*_ddl`). A slice in
   neither → RED. No forbidden literal.
2. **BACKSTOP — prose-lie leg (KNOWN BOUND).** A folded/standalone emitting slice whose docstring /
   leading comment asserts emptiness (a phrase in a closed `KNOWN_EMPTINESS_PHRASES` set) → RED.
   Best-effort; a novel phrasing evades it (pinned as an accepted bound with a re-open trigger).

**INSTRUMENT-0 (the reach law on the guard itself):** an INDEPENDENT by-shape oracle (private
top-level `-> list[str]` defs) cross-checks the by-name set; the scan FAILS CLOSED
(`SchemaGuardReachError`) on divergence (a misnamed emitter) or an empty derivation (a wholesale
rename). So a rename of the convention REDS the guard rather than silently exempting the renamed fns.

## How the slice-fn set was derived (CONSTRUCTION, not assumption)

Grep + `ast` + a **dynamic call of every slice fn** (read-only import of the real module), receipts
regenerable via the probe pasted in **Appendix B**. Measured at `f87e774`:

- **28** top-level `_*_statements` fns; **all 28 non-empty** (dynamically called, 0 errors, every
  `len(result) ≥ 1`).
- **Return-shape split (adversary RG-A): 8 LITERAL-list returners, 20 VARIABLE returners**
  (`statements = [...]; … ; return statements` — e.g. `_trace`, `_chunk`, `_keep`). 0 other shapes.
  (Adversary said 19; re-derived → **20** per protocol.) This is why the emptiness detector MUST
  handle the variable idiom, and why the contract now pins it.
- **16 FOLDED** into `generate_ddl` (direct-name calls in its body).
- **12 UNFOLDED**, **zero orphans** — each consumed by a standalone `generate_*_ddl`.
- **INSTRUMENT-0 cross-check:** by-name (`_*_statements`) set == by-shape (private `-> list[str]`)
  set = **28 == 28**, no divergence. (This is the positive control the guard's fail-closed check rests
  on.) Grep confirmed no `-> list[str]` def escapes the `_*_statements` name and no `_*_statements`
  lacks the annotation — so the two derivations are genuinely independent AND currently coincident.

Grep was the honest tool for the EXHAUSTIVE def enumeration (rename-exhaustiveness — CLAUDE.md dogfood
case a; `lore_index` also transiently errored, filed #409). **Said out loud** per protocol.

## Standalone allowlist — EVIDENCE-BACKED (each entry a real `ensure_ready` consumer)

The 12 unfolded slices, each traced slice → `generate_*_ddl` → the store method that applies it
(`ddl = generate_*_ddl()`), grepped over `loremaster/loremaster` at `f87e774`:

| slice fn | standalone generate | store `ensure_ready` consumer |
|---|---|---|
| `_agent_statements` | `generate_agent_ddl` | `agents.py:482` (`AgentRegistry`) |
| `_brief_statements` | `generate_brief_ddl` | `briefs.py:496` (`BriefLedger`) |
| `_briefed_statements` | `generate_brief_ddl` | `briefs.py:496` |
| `_brief_counter_statements` | `generate_brief_ddl` | `briefs.py:496` |
| `_message_statements` | `generate_message_ddl` | `messages.py:598` (`MessageLedger`) |
| `_code_node_statements` | `generate_graph_ddl` | `graph_surreal.py:460` |
| `_name_statements` | `generate_graph_ddl` | `graph_surreal.py:460` |
| `_refers_statements` | `generate_graph_ddl` | `graph_surreal.py:460` |
| `_answers_to_statements` | `generate_graph_ddl` | `graph_surreal.py:460` |
| `_floor_measurement_statements` | `generate_floor_calibration_ddl` | `floor_calibration/store.py:307` |
| `_floor_head_statements` | `generate_floor_calibration_ddl` | `floor_calibration/store.py:307` |
| `_lease_statements` | `generate_lease_ddl` | `store/lease.py:392` |

(The 16 folded slices are applied by `generate_ddl` → the primary `write_store.ensure_ready()`.)

**Contract decision — DERIVED, not hand-listed.** §Fork J says *"an EXPLICIT allowlist"*, but the SAME
ruling's rider requires *"the derived-not-hand-list property"* (the adversary's P1c REACH ATTACK
forces it) and CLAUDE.md/`registration_sites.py` law is *"prefer converting a hand-list into a derived
one"*. A literal `_STANDALONE_SLICES = {...}` is a hidden reach constant — the 7th instrument-defeat.
So the scan DERIVES membership (b) as "called by some `generate_*_ddl`", and the table above is the
AUDIT that the derived set corresponds to real store consumers. **Alternative (literal allowlist)**: a
frozen 12-name set + a pin that it equals the derived set — strictly weaker (adds a hand-list to keep
current) and the adversary would flag it. I recommend DERIVED; flagging for lead/adversary confirmation.

## KNOWN BOUNDS (pinned, per §"WHEN YOU CANNOT CLOSE A HOLE")

1. **Prose leg is enumerate-the-forbidden.** A NOVEL emptiness phrasing not in `KNOWN_EMPTINESS_PHRASES`
   evades it. Pinned: `TestStaleEmptinessProseIsAKnownBound::test_a_novel_emptiness_phrasing_evades…`.
   **Threat model (in the instrument):** structural leg is the real defense; prose only covers an
   "emit []" comment on an ALREADY-folded slice (statements DO run, so structural can't see it).
   **Re-open:** a new prose-evasion in the wild → widen the set OR strengthen structural.
2. **A rename dropping BOTH the `_*_statements` name AND the `-> list[str]` annotation** evades both
   reach derivations. Pinned: `TestGuardReachIsACheckedVariable::test_a_rename_dropping_the_annotation…`.
   **Re-open:** such a slice found in the wild → add a 3rd derivation ("returns a list built from
   `_define_*`").
3. **Standalone-via-a-DEAD `generate_*_ddl`** (a slice consumed only by a generate fn that is itself
   never wired to a store) would pass. **Now PINNED** (adversary SECONDARY) as
   `TestStandaloneExemptionIsAKnownBound::test_a_slice_consumed_only_by_a_generate_ddl_is_exempt…` —
   asserting the over-exemption is the accepted single-module bound. NOT closed (would need a
   whole-tree wiring scan — the reach STOP-rule: don't chase the constant one level deeper). Verified
   false at HEAD (every `generate_*_ddl` is wired — table above). **Re-open:** a `generate_*_ddl` found
   unconsumed by any store `ensure_ready` → add a whole-tree reachability check.

## Why source-based, and the emptiness rule

The scan is a pure function of the module SOURCE TEXT (internal `ast.parse`) — every synthetic fixture
and every mutation proof is a string, no import fragility, ONE code path grades real + synthetic (no
static/dynamic divergence gap). **Emptiness is conservative:** a slice is treated empty ONLY if it
provably `return []`; every other body is treated as EMITTING. That bias may over-flag an exotically
dead-code-empty slice (harmless — folding `[]` is a no-op) but NEVER false-clears a real emitter, the
only dangerous direction for a coverage guard. The contract pins OBSERVABLE behavior, so the builder
may implement static OR dynamic as long as the discrimination fixtures pass (the adversary's reach
attack will push toward the more robust construction).

## Mutation proofs (§Fork J rider — BOTH legs, on the REAL module)

Both applied to a source-string COPY of the real module (no file touched):
- **Structural:** drop `_snapshot_statements`'s ONLY application (its `generate_ddl` fold) → scan flags
  `_snapshot_statements`. Positive control: unmodified real source → `[]`. Guard test asserts
  `_snapshot_statements` is fold-only (else vacuous). `TestFoldCoverageMutationProofsOnRealSource`.
- **Prose:** reintroduce `# ⚠ RED STUB: this slice emits nothing today.` above the folded
  `_keep_statements` → prose scan flags it. Positive control: unmodified → `[]`.
- Synthetic discrimination controls (both legs, positive + negative) in
  `TestFoldCoverageStructuralDiscrimination` / `TestStaleEmptinessProseBackstop`.

## Adversary RG-A closure (BLOCKER — fixtures-must-discriminate)

**The gap:** rev-1 emitting fixtures were a MONOCULTURE — all `return [literal]`. A wrong `_emits`
that recognizes only a literal-list return would pass the whole contract YET be blind to the 20 real
`return <variable>` slices (an unfolded variable-returner would evade the primary defense). **Fix
(rev 2):**
- New `_var_slice_src` fixture in the house idiom (`statements = [...]; … ; return statements`).
- `TestFoldCoverageStructuralDiscrimination::test_an_unfolded_variable_returning_slice_is_flagged`
  (+ folded-variable negative control).
- `TestFoldCoverageMutationProofsOnRealSource::test_removing_a_real_variable_returning_fold_call_reds_the_scan`
  — mutation-proven on the REAL `_trace_statements` (a fold-only VARIABLE returner; `_snapshot` is a
  literal returner) + a `test_the_variable_returner_mutation_target_is_fold_only` guard.
- **Discrimination proven by counter-build** (adversary P2 discipline): injecting the exact wrong
  literal-only `_emits` into the scratch reference makes **3 pins RED** —
  `test_an_unfolded_variable_returning_slice_is_flagged`,
  `test_removing_a_real_variable_returning_fold_call_reds_the_scan`, and (bonus, since `_keep` is also
  a variable returner) `test_reintroducing_stale_prose_on_a_real_folded_slice_reds_the_prose_scan` —
  `3 failed / 26 passed`. The correct build: 29/29. So the fixture is not decoration; it fails on the
  named wrong build.

## Satisfiability receipt (C-DEF class)

Reference scan built in a provenance-asserting scratch (`./scripts/scratch_copy.sh /tmp/scratch-61aw3b`):
- **`loremaster.__file__` = `/tmp/scratch-61aw3b/loremaster/loremaster/__init__.py`** (#140 — grades the
  scratch, not the original).
- Contract **29 passed / 0 failed** against the reference build (`_schema_fold_guard.py`, pasted verbatim
  in **Appendix A**), with BOTH the literal- and variable-returner fixtures. Re-proven after the ruff
  cleanup the lint demanded — the harder C-DEF leg.
- **Discrimination:** the wrong literal-only `_emits` counter-build → `3 failed / 26 passed` (above).
- On the REAL tree at HEAD (no scan): **29 failed**, every one a NAMED behavioral accessor failure
  (`#133` guarded-import idiom), collection clean — verified the sample failure carries the full
  build-instruction contract note.
- `ruff check` clean; `mypy tests/test_schema_fold_coverage.py` clean.

## Node sets (from `--collect-only`)

All **29** node ids are **RED at `f87e774`** (behavioral, NAMED) and **GREEN against the reference
build** (29/0). The invariant itself (`TestFoldCoverageOnRealSchema::test_the_real_schema_has_zero_*`)
is GREEN post-build (schema clean at HEAD); the rest are discrimination/reach/mutation/bound meta-tests
that are RED at HEAD only because they reference the not-yet-built scan. Under the WRONG literal-only
`_emits` counter-build, 3 of them RED (the variable-idiom pins) — see §"Adversary RG-A closure".

```
TestFoldCoverageOnRealSchema::test_the_real_schema_has_zero_fold_coverage_findings
TestFoldCoverageOnRealSchema::test_the_real_schema_has_zero_stale_prose_findings
TestFoldCoverageOnRealSchema::test_the_derived_slice_fn_set_is_nonempty
TestFoldCoverageOnRealSchema::test_name_and_shape_derivations_agree_on_the_real_schema
TestFoldCoverageOnRealSchema::test_every_folded_and_standalone_name_is_a_real_slice_fn
TestFoldCoverageStructuralDiscrimination::test_an_unfolded_nonempty_slice_is_flagged
TestFoldCoverageStructuralDiscrimination::test_an_unfolded_variable_returning_slice_is_flagged
TestFoldCoverageStructuralDiscrimination::test_a_folded_slice_is_not_flagged
TestFoldCoverageStructuralDiscrimination::test_a_folded_variable_returning_slice_is_not_flagged
TestFoldCoverageStructuralDiscrimination::test_a_standalone_slice_consumed_by_a_generate_ddl_is_not_flagged
TestFoldCoverageStructuralDiscrimination::test_a_genuinely_empty_stub_is_exempt
TestFoldCoverageStructuralDiscrimination::test_a_folded_slice_that_becomes_a_stub_is_still_clean
TestFoldCoverageStructuralDiscrimination::test_the_finding_names_the_offending_slice_and_its_reason
TestFoldCoverageMutationProofsOnRealSource::test_removing_a_real_fold_call_reds_the_scan
TestFoldCoverageMutationProofsOnRealSource::test_a_fold_only_slice_is_not_also_standalone
TestFoldCoverageMutationProofsOnRealSource::test_removing_a_real_variable_returning_fold_call_reds_the_scan
TestFoldCoverageMutationProofsOnRealSource::test_the_variable_returner_mutation_target_is_fold_only
TestFoldCoverageMutationProofsOnRealSource::test_reintroducing_stale_prose_on_a_real_folded_slice_reds_the_prose_scan
TestGuardReachIsACheckedVariable::test_a_misnamed_emitter_fails_the_scan_closed
TestGuardReachIsACheckedVariable::test_a_wholesale_convention_rename_fails_the_scan_closed
TestGuardReachIsACheckedVariable::test_name_and_shape_derivations_are_independent
TestGuardReachIsACheckedVariable::test_the_scan_is_rederived_per_call_not_cached
TestGuardReachIsACheckedVariable::test_a_rename_dropping_the_annotation_evades_both_is_a_known_bound
TestStandaloneExemptionIsAKnownBound::test_a_slice_consumed_only_by_a_generate_ddl_is_exempt_regardless_of_that_generate_being_wired
TestStaleEmptinessProseBackstop::test_a_folded_slice_with_a_stale_emptiness_docstring_is_flagged
TestStaleEmptinessProseBackstop::test_a_folded_slice_with_honest_prose_is_not_flagged
TestStaleEmptinessProseBackstop::test_an_empty_stub_with_truthful_emptiness_prose_is_not_flagged
TestStaleEmptinessProseBackstop::test_known_emptiness_phrases_covers_the_398_399_wording
TestStaleEmptinessProseIsAKnownBound::test_a_novel_emptiness_phrasing_evades_the_prose_backstop
```

## DRY

The scan operates on a SINGLE named module (`surreal_schema.py`), so the whole-tree `_logging_fixtures`
helpers (`parse_production_trees` / `production_sources`) are NOT the right reuse — a one-file
`ast.parse` is not worth routing through them. Searched for an existing fold/stub scanner:
`grep -rniE 'fold.?coverage|fold_guard|stub.?prose|slice.?fn'` over `loremaster/tests`, `loremaster`,
`scripts` → only the stale-prose docstrings themselves, **no scanner exists** (HAND-ROLL is correct).
Builder guidance: place the scan in `_schema_fold_guard.py` (dedicated) or `_logging_fixtures` (shared);
the contract's lazy accessors tolerate either.

## Flags (scope law — surfaced, not silently narrowed)

1. **LIVE same-class instance in the TEST tree:** `loremaster/tests/test_principal_keys_schema.py:4-6`
   — a module docstring stating `generate_principal_key_ddl returns "", _principal_key_statements
   returns [], principal_key is NOT folded into generate_ddl` — all FALSE now (fully green/folded, my
   ground truth). This is the #398/#399 class in a test docstring. It is OUTSIDE this guard's scope
   (production `surreal_schema.py` only) and outside a safe unilateral fix (editing another contract's
   docstring mid-flight). **Fork for lead/operator:** fix the stale docstring now vs ledger it. I did
   not touch it.
2. **`lore_index` transient failure** filed as **#409** (fell back to grep, sanctioned for
   exhaustive enumeration; said out loud).

## Handoff
Lead runs the `contract-adversary` (its P1c REACH ATTACK is exactly this instrument's grader — it will
attack the derived-standalone decision, the by-name/by-shape independence, and the emptiness rule).
Then build → cold-audit. **Resolve #398 AND #399 on the invariant's commit** (§Fork J).

---

## Appendix A — reference scan (satisfiability build, `/tmp/scratch-61aw3/loremaster/tests/_schema_fold_guard.py`)

⚠ NOT the shipped instrument — a throwaway reference proving the contract satisfiable. The builder
writes the real one (this is one correct shape).

```python
from __future__ import annotations

import ast
import re
from dataclasses import dataclass

_SLICE_RE = re.compile(r"^_[a-z0-9_]+_statements$")

KNOWN_EMPTINESS_PHRASES: frozenset[str] = frozenset({
    "emit []", "emits []", "emit nothing", "emits nothing", 'emit ""', 'emits ""',
    "red stub", "red stubs", "not folded", "do not implement",
    "do not 'fix' the emptiness", "raises notimplementederror", "stub emits", "stub note",
})


class SchemaGuardReachError(Exception):
    """Empty slice-fn derivation (fail-closed) or name/shape divergence (INSTRUMENT-0)."""


@dataclass(frozen=True)
class FoldFinding:
    slice_fn: str
    reason: str
    def __str__(self) -> str: return f"{self.slice_fn}: {self.reason}"


@dataclass(frozen=True)
class ProseFinding:
    slice_fn: str
    phrase: str
    reason: str
    def __str__(self) -> str:
        return f"{self.slice_fn}: stale emptiness prose ({self.phrase!r}) — {self.reason}"


def _tree(source): return ast.parse(source)
def _top_defs(tree): return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def derive_slice_fns(source):
    return {n.name for n in _top_defs(_tree(source)) if _SLICE_RE.match(n.name)}


def derive_statement_emitters(source):  # independent BY-SHAPE oracle
    out = set()
    for n in _top_defs(_tree(source)):
        if n.name.startswith("_") and n.returns is not None and ast.unparse(n.returns) in ("list[str]", "List[str]"):
            out.add(n.name)
    return out


def _call_names_in(fn_node):
    return {n.func.id for n in ast.walk(fn_node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


def derive_folded_slices(source):
    tree = _tree(source); slices = derive_slice_fns(source)
    gen = next((n for n in _top_defs(tree) if n.name == "generate_ddl"), None)
    return _call_names_in(gen) & slices if gen is not None else set()


def derive_standalone_slices(source):
    tree = _tree(source); slices = derive_slice_fns(source); out = {}
    for n in _top_defs(tree):
        if n.name == "generate_ddl" or not re.match(r"^generate_[a-z0-9_]+_ddl$", n.name):
            continue
        for called in _call_names_in(n) & slices:
            out.setdefault(called, set()).add(n.name)
    return out


def _emits(fn_node):  # conservative: emitting UNLESS every return is a literal []
    returns = [n for n in ast.walk(fn_node) if isinstance(n, ast.Return)]
    non_empty = [r for r in returns if not (isinstance(r.value, ast.List) and len(r.value.elts) == 0)]
    return bool(non_empty) or not returns


def _assert_reach(source):
    by_name = derive_slice_fns(source); by_shape = derive_statement_emitters(source)
    if not by_name:
        raise SchemaGuardReachError("no `_*_statements` slice fns — refusing a falsely-clean []")
    if by_name != by_shape:
        raise SchemaGuardReachError(f"reach divergence: name-only={sorted(by_name-by_shape)} shape-only={sorted(by_shape-by_name)}")
    return by_name


def scan_schema_fold_coverage(source):
    slices = _assert_reach(source); tree = _tree(source)
    by_node = {n.name: n for n in _top_defs(tree) if n.name in slices}
    folded = derive_folded_slices(source); standalone = set(derive_standalone_slices(source))
    findings = []
    for name in sorted(slices):
        if not _emits(by_node[name]): continue
        if name in folded or name in standalone: continue
        findings.append(FoldFinding(name, "emits >=1 statement but neither folded into generate_ddl nor consumed by a standalone generate_*_ddl"))
    return findings


def _leading_prose(source, fn_node):
    parts = []
    doc = ast.get_docstring(fn_node)
    if doc: parts.append(doc)
    lines = source.splitlines(); idx = fn_node.lineno - 2; block = []
    while idx >= 0 and lines[idx].lstrip().startswith("#"):
        block.append(lines[idx]); idx -= 1
    parts.extend(reversed(block))
    return "\n".join(parts)


def scan_stale_emptiness_prose(source):
    slices = _assert_reach(source); tree = _tree(source)
    by_node = {n.name: n for n in _top_defs(tree) if n.name in slices}
    folded = derive_folded_slices(source); standalone = set(derive_standalone_slices(source))
    findings = []
    for name in sorted(slices):
        node = by_node[name]
        if not _emits(node): continue
        if name not in folded and name not in standalone: continue
        prose = _leading_prose(source, node).lower()
        for phrase in KNOWN_EMPTINESS_PHRASES:
            if phrase in prose:
                findings.append(ProseFinding(name, phrase, "folded/standalone emitting slice claims emptiness"))
                break
    return findings
```

## Appendix B — ground-truth probe (regenerable receipt for the derivation counts)

Read-only import of the real module; derives slice/fold/standalone sets and dynamically CALLS every
slice fn to confirm non-emptiness. Output at `f87e774`: 28 slice fns, all non-empty, 16 folded, 12
unfolded, 0 orphans, by-name==by-shape (28==28).

```python
import ast, inspect, re, pathlib
import loremaster.store.surreal_schema as S
tree = ast.parse(pathlib.Path(S.__file__).read_text())
SLICE_RE = re.compile(r"^_[a-z0-9_]+_statements$")
slice_names = [n.name for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and SLICE_RE.match(n.name)]
gen = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "generate_ddl")
fold_calls = {n.func.id for n in ast.walk(gen) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
folded = sorted(n for n in slice_names if n in fold_calls)
def call_slice(fn):
    kw = {}
    for p in inspect.signature(fn).parameters.values():
        if p.name == "dim": kw[p.name] = 8
        elif "analyzer" in p.name: kw[p.name] = "code_ident"
        elif p.default is inspect.Parameter.empty: kw[p.name] = None
    return fn(**kw)
counts = {n: len(call_slice(getattr(S, n))) for n in slice_names}
print("slice fns:", len(slice_names), "| non-empty:", sum(c > 0 for c in counts.values()),
      "| folded:", len(folded), "| unfolded:", len(slice_names) - len(folded))
```
