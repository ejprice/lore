# Packet 63c — ruling amendment 16 (sidecar-63c-2, 2026-09-25): r4b-fix adversary — G5, G6, the four bounds, and right-sizing the fifth round

Rules `REPORT-adversary-63c-i-a-r4b-fix.md` §8 (`dcc88c6`): G5, G6, and whether a further narrow adversary
is warranted. Directive: `REPORT-lead-63c.md@dcc88c6` (durable copy; this session's lore client is still down
— `Read`/`awk`, said so). Amends amendment-13 §G4 prose and amendment-15's effect-leg prose. HEAD at
ruling: `dcc88c6`. F-A1's fix is accepted as proven (§8, §4d), with its proposed non-agent-count bound line.

## Right-sizing first, because it decides the shape of the other two
- **Where the packet stands:** five contract rounds on 63c-i-a; production byte-identical to `8b9eb6d`
  throughout; every author claim confirmed independently each round; LIVE defects found: zero, five times.
  The remaining doors live in a FOOTER gate whose worst consequence is one extra registry read on an
  attribution that can never register, and in a TEST DOUBLE. The cost/importance ratio has inverted: each
  round now spends a full adversary session to move a footer gate's sampling one axis. CLAUDE.md's STOP-rule
  names this exactly — *"surface the value-vs-depth trade … rather than defaulting to max machinery because
  the findings exist"* — and its right-sizing law says maximal rigor on a trivial surface is the same error
  as under-verifying an important one.
- **Ruling:** the fix2 agent lands F-A1 (verbatim, as proven), the four bound docstrings, the two over-claim
  deletions, AND the G5/G6 closures — and the builder is spawned on its SAT receipt. **No further pre-build
  adversary round.** Reading of the 2026-07-28 law, flagged §E: its purpose is an INDEPENDENT grader of every
  contract change, and for G5/G6 that grading already exists — the adversary itself authored both closures
  and proved them at contract level with RED sets declared before the run (§4f: satisfiable on the correct
  build, kills every build in class, all ten diffs empty both ways). A change the fix2 agent implements
  VERBATIM from the adversary's pasted diff is not a new authored revision; it is the adversary's own graded
  edit landing. Condition: byte-equal to §A's diffs, and fix2's SAT receipt re-runs the adversary's own
  runner. **If fix2 deviates from verbatim in any of the three edits, a narrow delta is required** — that is
  the law's letter and its intent, both kept.
- After the build: the cold audit is the next independent instrument; any door found in these classes
  afterwards is a lead-recorded bound (amendment-13's carrier rule) or an i-b item — never an i-a round.

## G5 — CLOSE with the one line; and an erratum on "sample space"
- **Ruling:** `hypothesis.target(float(len(attribution)), label="length")` inside the generated legal leg —
  the package's own steering API, one line, proven (GL kills Nmid; Ncap48/Ncap64 red exactly GL + MW + HC).
  `derandomize=True` keeps it deterministic.
- **Erratum against amendment-13 §G4:** I wrote *"G1's cap … in the sample space by construction — the
  language IS the generator"*. Space ≠ sample: 200 derandomized draws maxed at 27 characters and never reached
  the cap. A generator's sample space is a fact about what it CAN draw; a pin certifies only what it DID
  draw. Both over-claiming lines are narrowed: the corpus comment to *"the generator's sample space is the
  language; `target` steers the sample up the length axis; the other axes are covered probabilistically at
  200 examples"*, the leg's docstring to *"every narrowing conjunct on an axis a draw REACHES"*. The hand-list
  keeps the cap witness as the deterministic control it already is.

## G6 — CLOSE, exhaustively, because it is cheaper than the bound and ends its class by construction
- **Ruling:** the single-character leg — ∀ ASCII `c`, the predicate-rejected one-edit neighbours
  (`a{c}b`, `{c}a`, `a{c}`) are never looked up (≤ 384 in-memory spy calls, derived from the predicate; no store).
  Proven: SC kills Wat/Wplus/Wtab; Wspace/Wnl red SC + HC exactly; correct build 333 passed. Sampling
  measurably cannot close this (0 hits in 200 under either alphabet), exhaustion can, and exhaustion over a
  finite alphabet is the allowlist-the-safe shape — it does not recede.
- **Sized honestly, as the adversary sized it:** the consequence is read-budget only — the served traffic line
  cannot change, since no such identity can be registered. It is closed because the closure is one function
  and ends the single-edit class outright, not because the door matters. **Stated bound:** multi-character
  widenings (`@@`, a two-edit neighbour) are outside the leg; re-open trigger: a widening with a served
  consequence beyond one registry read — which, by construction of `register`'s refusal, cannot arise while
  the shared predicate is the registry's gate.

## The four SAME-FAMILY bounds — recorded as the lead did, with two notes
- **FXtVE / FXand / FXname** (fake-guard) and **RS1combo** (ownership): KNOWN BOUNDS, carrier = the bounded
  pin's docstring (amendment 13), texts and triggers as the adversary proposed. The adversary's cheaper
  closures (a WIDENING direction in the sharing pin for FXand; a sentinel subclassing `ValueError, TypeError,
  LookupError` for FXtVE; four single-optional params for RS1combo) are UNMEASURED and are therefore written
  into each bound as its *closure-if-reopened*, not landed — landing an unmeasured pin now is exactly the
  round this amendment declines.
- **RS1combo becomes MOOT at i-b:** amendment-10 C-3's served refusal (a householded joiner may not
  re-register another principal's agent) closes the entire 2⁴ lattice at once, because no joiner re-register
  succeeds at all. The bound text says so, so i-b's author deletes it deliberately.
- **Over-claims deleted (both mine):** amendment-15's *"REACHED and TRUSTED"* (FXdisc is reached, not
  trusted — the SHARING pins kill it, not the effect leg) and the effect leg's *"whatever the handler
  spells"* (FXtVE: a narrower handler than the sentinel). The leg's docstring says what it observes: the
  shared decision is REACHED and ITS exception propagates.

## §W — the fix2 agent (tests-only; verbatim from the adversary's §A where a diff exists)
| # | item | source | grading |
|---|---|---|---|
| 1 | F-A1 fix (12 lines, verbatim) + the non-agent-count bound line | F-A1 | adversary §4d; fix2 re-runs the runner |
| 2 | G5: `hypothesis.target(...)` line; two prose lines narrowed | G5 | adversary §4f (verbatim) |
| 3 | G6: single-character exhaustive leg; multi-edit bound stated | G6 | adversary §4f (verbatim) |
| 4 | four bound docstrings with closure-if-reopened; RS1combo's "moot at i-b" line | §8 | prose |
| 5 | delete "whatever the handler spells" and "REACHED and TRUSTED" | §8 | prose |
| → | SAT receipt on both helper shapes via the adversary's runner; then the BUILDER | — | — |

## §E — operator-visible
- **The 2026-07-28 law is READ, not waived:** a contract edit authored and empirically graded by the adversary,
  landed byte-equal, carries its own independent grading; any deviation from verbatim re-triggers a narrow
  delta. Flagged because it is the first time this packet spawns a builder without a fresh adversary pass over
  the last test edit; my reading is that a sixth pre-build round on a footer gate's sampling is the machinery
  the STOP-rule exists to stop, and that the cold audit is the right next independent instrument.
- Erratum: amendment-13's "sample space by construction" (space ≠ sample); amendment-15's "REACHED and
  TRUSTED" and "whatever the handler spells".
