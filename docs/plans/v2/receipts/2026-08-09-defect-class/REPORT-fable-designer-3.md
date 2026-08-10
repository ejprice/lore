brief-base v10 read
brief project v7 read

# REPORT-fable-designer-3 — G summary-honesty structural redesign (design escalation, #344)

## Capability check (tool honesty — brief-base §4, first)
Everything the brief demanded was satisfiable. Read the two delta-adversary reports, the
current `scripts/test_wave_gate.py` (uncommitted `M`), `scripts/pending_contract_gate.py`'s
`_render_currency`/`GateCurrency`/`_run_selected_gates`, design §9.1/§9.3/§9.4/§9.6, and
confirmed the `Rendered`/`SafeLine` seam via lore. Deliverable is a design section + a
recommendation — I wrote NO code/tests. `lore_comms` reachable (drained: no unread).

---

## SUMMARY BLOCK

- **State: done.** Appended **§11 — G summary-honesty structural redesign** to
  `docs/plans/v2/design/2026-08-09-defect-class-prevention.md`. The redesign makes an
  over-claim **unrepresentable by construction**, addressing all three survivors.
- **Root cause named:** every round treated the summary as a `str` a builder APPENDS, then
  INSPECTED it — string-shape inspection of an open-vocabulary line IS enumerate-the-forbidden
  (the 7th-defeat class), reproduced inside the fix for the finding about exactly that. The lie
  lives in the gap between the TYPED verdict the machinery computed and the FREE TEXT written
  beside it.
- **The fix (lift honesty from STRING to TYPE):** a closed `SummaryVerdict` enum
  (`PASS_FULL` / `PASS_SCOPED` / `FAIL`) computed by a pure total `summary_verdict(leg_quals)`;
  a **sole minter** `render_summary(verdict) -> SummaryLine` (a `Rendered`-style provenance
  `str`); the receipt's summary slot is TYPED, not a free-text append. `PASS_FULL` (the only
  unqualified-token render) is UNREACHABLE while any leg is SCOPED. DRY #1: the seam lives in
  `pending_contract_gate.py`, consumed by BOTH checkpoint (`_render_currency`) and wave.
- **Three survivors die by construction:** `alt` (alternate wording) → dies at the
  prove-sharing-by-mutation pin (P3, a hand-authored summary isn't derived); `double`
  (non-last line) → PASS_SCOPED emits no PASS_FULL line to inherit; a forged one dies at the
  sole-minter AST scan (P2) + the biconditional belt (P4); `inline` (marker+lie on one line) →
  the line is a FIXED minted string, no per-call seam to compose the lie into (P2/P4).
- **Contract pins (none is a forbidden-shape scan):** P1 ∀ over the per-leg-flag combination
  surface (typed→typed, coverage-checked meta-recursion); P2 sole-minter mutation + `Rendered`
  AST mint-scan; P3 prove-sharing-by-mutation (DRY); P4 biconditional belt (token IFF PASS_FULL,
  allowlist-the-safe). `_summary_line` (the round-2/3 hidden-constant reach) is retired.
- **PRODUCTION-DESIGN CHANGE — YES, and it is the DRY-correct answer.** A small
  behaviour-preserving extraction in shipped `scripts/pending_contract_gate.py` (pull the inline
  PASS/FAIL summary into the shared `summary_verdict`+`render_summary` seam). Option B (wave
  re-implements it) is rejected as the §9.1/#102 two-copies defect.
- **Packages considered:** stdlib `enum` + a `str` subclass (mirrors `loremaster.render.Rendered`);
  no library supplies "typed verdict + sole minter" — **bespoke (minimal), reusing four in-repo
  idioms** (`GateCurrency`, `_render_currency` extraction, `Rendered`/`SafeLine` mint-scan,
  the meta-recursion coverage pin, `mutation_proof.py`/`_rebind_everywhere`).
- **Graded:** design section, not an artifact verdict. Read the contract/machinery/reports at
  HEAD `14b62f2` · `wave_gate.py` ABSENT (RED) · `test_wave_gate.py` uncommitted (`M`).
- **Decisions needed (2, flagged to operator/lead):** (1) confirm `scripts/pending_contract_gate.py`
  enters G's writable set (a change to the #306/#312 enforcement surface — the "production-touching
  surprise" escalation trigger; I do not decide scope). (2) route as contract → adversary → build
  → cold audit (a fix wave needs the adversary most), with the adversary re-attacking all three
  survivors + a routing-not-sharing hybrid.
- **Receipt POINTERS:** design §11 (§11.1 root cause · §11.2 typed surface · §11.3 the fork
  answered · §11.4 the four pins · §11.5 each survivor's death · §11.6 reuse · §11.7 routing);
  `REPORT-delta-adversary-g-2.md` (W-summary-double/inline, MP-9); `REPORT-delta-adversary-g.md`
  (round-1 deny-list); `loremaster.render.Rendered` + `test_render_seam_pins.TestSafeLineRenderedMintPin`
  (the provenance-type idiom to reuse).

---

## Body — the reasoning, by section

The full design is §11 of the design doc (cited above); this body records the decisions and
their reasons so a stranger can reconstruct them without re-deriving.

### Why a redesign and not a 4th pin
The class has survived three rounds (deny-list → last-line marker → per-line marker still open
on `inline`). The lead's-own-tell fired. The delta-adversary (`REPORT-delta-adversary-g-2.md`
§MP-9) had already flagged the fork: a minimal ∀-over-verdict-lines pin closes double+alt but
NOT inline, and named the durable close as "derive the summary from a typed per-leg flag." §11
takes that structural close and makes the contract pin the STRUCTURE, not strings.

### The load-bearing insight
Every prior fix operated at the STRING level (inspect a builder-authored line for a
forbidden/safe shape). String-shape sets over free text are unbounded → enumerate-the-forbidden
→ the 7th defeat. Lifting to the TYPE level makes "unqualified pass" a single closed enum value
and "is this leg scoped" a typed flag: the SAFE set is small/closed/enumerable (allowlist-the-
safe), and a biconditional over a finite typed domain is ∀-checkable. This is CLAUDE.md's
"render from typed applicability, never a name compared" applied to the summary.

### The typed surface (§11.2)
`SummaryVerdict{PASS_FULL, PASS_SCOPED, FAIL}` (minimal — collapses today's GREEN-or-OWNED into
PASS_FULL so the extraction is byte-preserving; SCOPED is the one new state). `summary_verdict`
is a pure total function whose biconditional makes PASS_FULL unreachable when any leg is SCOPED.
`render_summary` is the SOLE minter (fixed string per enum value → no "alternate wording"
freedom), returning a `SummaryLine` — a `Rendered`-style provenance `str` whose constructor an
AST scan forbids outside the minter (reusing the exact `test_render_seam_pins` idiom). The
receipt's summary is a typed slot, not a free-text append — the seam the lies lived in is gone.

### The production fork, answered (§11.3)
The only shipped code is `pending_contract_gate.py`. DRY #1 forces Option A: extract the summary
into a shared seam there, consumed by both modes. Option B (wave clones the logic) is the
two-copies defect. The extraction is behaviour-preserving for checkpoint, guarded by the existing
`test_pending_contract_gate.py` (which certifies the OLD world — the anti-regression net) plus a
byte-exact oracle-equality control. `scoped` is derived from reader identity ∧ mode==wave (never
`id=="pytest"`), and is carried in the new leg-qualification surface, NOT bolted onto
`GateCurrency` (whose currency-vs-deploy separation stays intact).

### The pins and the deaths (§11.4/§11.5)
Four pins: P1 (∀ over the flag-combination surface, typed→typed, coverage-checked), P2
(sole-minter mutation + AST mint-scan → the summary type cannot carry the token when scoped), P3
(prove-sharing-by-mutation → any hand-authored summary is RED, whatever its wording — this is
what kills `alt` without reading its words), P4 (biconditional belt: token IFF PASS_FULL). All
three survivors require a free-text-authoring seam the redesign removes; each dies at the typed
pins, not at a shape scan.

### Reuse (§11.6)
`GateCurrency` (per-gate typed applicability), `_render_currency` (extract not clone),
`loremaster.render.Rendered`/`SafeLine` + `TestSafeLineRenderedMintPin` (provenance type + AST
mint-scan), the `test_enforcement_matrix_covers_...`/`_canonical_manifest_ids` meta-recursion
idiom, `scripts/mutation_proof.py` + `_rebind_everywhere`. New machinery is a stdlib enum + a
`str` subclass — no library covers it.

### Flags / forks for the operator/lead (§11.7)
1. Writable-set: `scripts/pending_contract_gate.py` must enter G's writable set (production
   enforcement surface — I flag, I do not decide scope).
2. Routing: contract → adversary → build → cold audit; the adversary must catch alt/double/inline
   AND a routing-not-sharing hybrid (`_render_currency` shares the minter but `render_wave_receipt`
   hand-rolls its summary).
3. Re-open trigger: a later split of OWNED into a distinct `PASS_OWNED` grows the P1/P2 domain by
   one enum value — the coverage pin reddens until the ∀ is extended (mechanism working as intended).
