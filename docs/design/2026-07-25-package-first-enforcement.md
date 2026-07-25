# Enforcing packages-over-hand-rolling — a design, not a rule

**DRAFT for operator ruling.** Authored 2026-07-25 by `lead-11i-b` on the operator's directive:
*"Lastly, I need enforcement. The CLAUDE.md obviously wasn't enough."*

---

## 1. What actually failed, stated precisely

`CLAUDE.md` has carried the packages-over-hand-rolling rule, with worked examples from both sides,
for weeks. In ONE session it was broken **four times**, and three of those were inside the fixes for
the previous one:

| # | the hand-roll | caught by |
|---|---|---|
| 1 | the whole statistical core (ROC sweep, bootstrap, percentiles ×3) | the operator, in one sentence |
| 2 | §R3's "numpy candidate-rate evaluator" — written *while correcting* #1 | the operator's rule, applied again |
| 3 | §R2's lease algorithm — designed *after* #2 was corrected | the operator, again |
| 4 | `_txn.retry_on_conflict` (**correctly kept** — proven, guarded; #202) | a sweep that only ran because the operator asked for one |

**The rule was never disbelieved. It was never CONSULTED.** Every author agreed with it and none of
them ran it, because nothing ever asked them to. This is `CLAUDE.md`'s own diagnosis — *"A DIAGNOSIS
IS NOT AN INSTRUMENT… a rule people must remember is not a guard; it is a hope"* — reproduced by the
very document that states it.

**And the meta-lesson from the same file applies exactly:** *"when you catch yourself enumerating
what is FORBIDDEN, you have already lost. The forbidden set is unbounded; the SAFE set is small and
enumerable — so allowlist the safe."* The set of things that could be hand-rolled is unbounded. **The
set of mechanisms whose package question has been ANSWERED ON THE RECORD is enumerable.** That is the
allowlist, and it is the whole design.

**Verified before designing** (the rule applied to its own enforcement): no static-analysis tool
detects reinvented wheels — searched 2026-07-25; the Python static-analysis field covers style,
types, security and complexity, and nothing covers reimplementation. So this must be structural. The
design's own moving parts, however, are libraries: **pydantic** for schema, **pytest** for the pins.

---

## 2. The instrument, in three layers

Ordered by where the failure actually happens. Layer 1 is primary because **all four instances above
were DESIGN decisions**, made in a document, before any code existed.

### Layer 1 — the design-time gate (primary)

**Every file in `docs/design/` carries a `## Package survey` section.** No exceptions, including
docs that specify nothing — those write one line (`no mechanisms specified`). A missing section is
RED.

The section is a table, one row per mechanism the document specifies:

| mechanism | libraries evaluated | what I READ | verdict |
|---|---|---|---|
| bootstrap CI over a selection rule | `scipy.stats.bootstrap` 1.18.0 | installed signature: `data, statistic, n_resamples, batch, vectorized, paired, rng` | **REPLACE** |
| distributed lease | `kubernetes.leaderelection` 36.0.3 · `sherlock` | source: zero k8s imports, six-member lock iface · `sherlock.BaseLock`: no fencing token | **REPLACE-WITH-ADAPTER** (~129 LOC) |

**Why "what I READ" is a required column and not decoration:** the failure mode is not *"forgot to
check"*, it is ***asserting a package limitation without reading the API*** — which is how §R3's
evaluator and my own "scipy's percentile convention may not match" both happened. A verdict of
BESPOKE with an empty read-column is the defect this instrument exists to catch, and it is
mechanically detectable.

**Verdicts are a closed set** (exact-set pinned, per the repo's own state-set discipline):
`replace` · `replace_with_adapter` · `keep_with_trigger` · `bespoke`. A `keep_with_trigger` row
**must** name its re-open trigger (#202's shape — the disposition that keeps proven, guarded code
without pretending the question is closed forever).

### Layer 2 — the adversary phase (the grader)

`contract-adversary` gains a mandatory **P-PKG** phase with the same standing as the quantifier
law's P1b table:

> For every mechanism the contract specifies, the adversary produces its OWN package table —
> independently, before reading the author's — and DIFFS them. A mechanism the author marked
> `bespoke` that the adversary can implement with a library is a finding. **A verdict of SUFFICIENT
> without the table is itself INSUFFICIENT.**

Independent enumeration then diff, never shared — the same discipline as P6b's deleted-code
inventory. This is the layer that catches a dishonest or lazy entry, which no structural pin can.

### Layer 3 — the code-time backstop (the ledger)

`docs/reference/package-survey.yaml` — machine-readable, one entry per production module, pydantic
schema, YAML per house preference. Seeded by the four `pkgscout-*` sweeps now running.

A pin in the test tree asserts, mechanically:
1. **every production module under the workspace members has an entry** — a NEW module with no entry
   is RED (this is the allowlist-the-safe half, and it is the part that cannot be talked past);
2. every entry validates against the schema;
3. every `keep_with_trigger` carries a non-empty trigger;
4. **no entry names a module that no longer exists** — self-cleaning, and it closes the dangling-
   address class (#152/#203) rather than opening a new instance of it.

Most entries will be one line (`no_library_question: true`, with a reason). That is fine and cheap;
the point is that **adding a file forces the question to be asked once.**

---

## 3. What this does NOT claim

- **It cannot force honesty.** An author can write `bespoke` with a plausible read-column. Layer 2 is
  the answer to that, and Layer 2 is a *person-shaped* check, not a mechanical one. Stating this
  plainly because a gate that over-claims is the class this repo keeps getting bitten by.
- **It does not detect reinvention.** Nothing does (§1). It detects *the absence of the question*,
  which is a different and weaker property — but it is the property that was actually missing all
  four times.
- **Layer 3 will accumulate noise** if most modules have no library question. Mitigation is the cheap
  `no_library_question` form; the alternative (a risk predicate deciding which modules need entries)
  is fuzzy, and fuzzy gates get switched off — *"a gate that refuses honest code is a gate that gets
  SWITCHED OFF."*

---

## 4. Cost, honestly

- **Layer 1:** one section per design doc. Near zero ongoing; the table is what a careful author
  already did, written down.
- **Layer 2:** one phase added to an agent definition. Zero standing cost; it runs when the adversary
  runs.
- **Layer 3:** a schema, a pin, and a **backfill of ~86 production modules** — the expensive part, and
  it is already being produced by the four scouts as a side effect of the sweep the operator ordered.
  Sequencing is accidental but favourable: **do the backfill from the scout reports, or it will not
  get done.**

---

## 5. The open question the operator should rule

**Does Layer 3 earn its keep?** Layers 1 and 2 attack where all four failures actually happened
(design time) and cost almost nothing. Layer 3 is the only mechanically-unfoolable part *and* the
only part with real ongoing cost and real noise risk.

The lead's recommendation: **take all three, but build Layer 3 last**, after the scout reports land —
so the backfill is a transcription of work already done rather than a new sweep. If Layer 3 proves
noisy in practice, it can be narrowed to the workspace members' non-trivial modules with a recorded
reason, which is a decision to make on evidence rather than in advance.

**Also to rule:** whether `CLAUDE.md` gains a pointer to this document. It should — but as a
*pointer*, not a re-transcription, per the repo's own cite-don't-transcribe rule. The lesson of this
whole exercise is that the words in `CLAUDE.md` were never the problem.
