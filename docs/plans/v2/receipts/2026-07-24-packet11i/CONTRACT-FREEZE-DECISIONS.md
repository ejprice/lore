# Packet 11-i — contract-freeze decision package (DRAFT — awaiting blind review + sidecar follow-up 2)

**Status:** DRAFT, assembled by `lead-11i` 2026-07-24. Not yet ruled. Two inputs outstanding:
`design-blind-11i`'s independent verdict, and the design sidecar's recommendations for
ESC-1/4/5/6/7/8/10/12. This file is the durable address the 11-i contract cites; it exists as a
tracked path rather than a chat message precisely because of ESC-13's own finding (a decision
recorded at an unrecoverable address is a promise already broken — #152/#153/#154).

**Provenance of the inputs.** Three agents, deliberately structured so no list grades itself:
- `REPORT-scout-11i.md` — Opus discovery scout; source-verified seam map + measured sizing.
- `REPORT-fable-design-11i.md` — the Fable design sidecar (authored most of the design under
  review; holds it in loaded context). Its §5 carries six recommendations.
- `REPORT-design-blind-11i.md` — independent Opus reviewer, **withheld from both reports above**
  so its gap enumeration is independent and DIFFABLE against the sidecar's.

⚠ These three reports must be archived under this directory at close-out per the archive law —
never deleted, and never cited as bare `REPORT-*.md` once archived.

---

## Why this package exists

The ruled design (`docs/design/2026-07-24-floor-calibration.md`, R1–R8 + Addenda A–E) is
operator-ruled and is not being re-opened. But it was authored before any builder touched it, and
kickoff discovery surfaced a consistent asymmetry: **it is well-ruled on POLICY and thin on
MECHANICS.** Disjoint-CI adoption, the identity-keyed sampler, and the interval machinery are
settled and correct. Seeds, denominators, k′, and where the probe manifest lives are not.

Repo law makes this a stop rather than a builder's judgement call: *"Spec ambiguity is a defect,
not a judgment call. If a contract author finds itself CHOOSING between two readings of a spec
sentence, that is an escalation — not a contract decision."* Two C1 contract authors once read one
sentence opposite ways, both chose silently, and their suites contradicted each other. This package
exists so that does not happen fourteen times.

**The operator's kickoff narrowed the sidecar's Addendum-E0 delegation** — *"It decides nothing.
Its output is analysis + recommendation; the operator rules."* So every entry below is a
recommendation with a cost, not a ruling.

---

## A. The sizing decision (measured, not inherited)

**11-i measures ~0.42 wu against the packet's ~0.20 header and D7's ~0.25–0.30 re-estimate.**
Reference points the scout measured at `d0ee2be`: `calibration/engine.py` is 660 prod LOC against
1,256 test LOC — and it serves ONE scalar, runs ONE probe kind, and has five states. 11-i has eight
states, an interval, a bootstrap over the entire selection procedure, a stratified sampler, two
probe legs, a paired decomposition, a store table with a head mint AND a single-flight lease, cost
capture, a one-shot verb, and a ~450-LOC core port.

Three costs the design never priced:
1. the ported core's 50 tests must be **re-homed into the gate**, not merely moved (§C item 3);
2. the exact-set state pin B5 names as reusable **does not exist** and must be built;
3. C6's evidence package is **six deliverables**, not one report.

**D7's named sub-split line does not work.** It maps to ~0.36 vs ~0.03 — a packet with an offcut —
and it leaves R2 unassigned, though the packet's own Exit calls R2 a HANDOFF that two downstream
decisions block on (the F3 client consult and #180's fix choice).

**Recommended split — at the store/runner seam (B7.1 vs B7.2+B7.5):**

| half | contents | est. | character |
|---|---|---|---|
| **11-i-a** store + engine skeleton | table + fields + indexes; ledger with head mint + single-flight lease via `retry_on_conflict`; 8-state closed set + its new exact-set pin; render model | ~0.13 | ALL the concurrency risk, NO arithmetic risk — the shape a cold audit grades well |
| **11-i-b** runner + R2 | core port + test re-homing; hash-stable sampler; self-supervised answered probes; hold-out leg; bootstrap intervals; N-curve + stability gate; paired decomposition; cost capture; determinism pin; R2 verb + C6 package | ~0.29 | ALL the arithmetic; lands against an already-audited store |

**Operator decision required:** accept this split line, accept D7's literal line, or keep 11-i whole
at ~0.42.

---

## B. The one decision no agent on this packet can make: ESC-1 (R2's execution vehicle)

**Three facts collide.**
1. R2's entire value is lore's REAL corpus — and that corpus exists in exactly one place:
   `ws://127.0.0.1:18500`, ns/db `lore`. That is **production** lore-surreal.
2. The packet header says **DEPLOY: no**, so the running `lore-lore` container never receives 11-i's
   code. "An in-container one-shot verb" therefore has no container to run in.
3. The kickoff brief says never point anything at `:18500` (finding #177 — the survey script's
   dangerous default).

**What R2 running implies**, beyond a read: the new table's DDL landing on the production store
before 11-ii; measurement rows and possibly an adopted head written there; possibly a
`measurement_failed` finding filed there.

**Candidate vehicles, with what each costs:**

| option | verdict |
|---|---|
| run against spike `:18000` | R2 measures the WRONG CORPUS; the F3 consult then judges on garbage. Rejected on merit. |
| host-side process against `:18500` | violates the #166 in-container architectural shape and sits inside #177's coordinate hazard; also tests the recipe, not the cake (#139). |
| **ephemeral container from a worktree-built image against `:18500`** | the packet-01a precedent; NOT a deploy (`lore-lore` untouched); tests the ARTIFACT. **Lead's recommendation** — but it is production access by not-yet-audited code and nobody has ruled it. |

**Recommended shape if the operator authorizes the third option:**
- run only AFTER the cold audit, never before;
- the verb **REFUSES to run without an explicit store coordinate** — no default of any kind
  (Addendum A2's mistyped-coordinate hazard: a wrong ns/db against production is silently
  MATERIALIZED as empty, not rejected);
- the DDL reviewed against `docs/reference/surrealdb-31-capabilities.md` §1.1 as an audit item.

**Related, and settled by measurement rather than opinion (scout RAISED-3):** the verb must NOT be
an MCP tool. `test_instructions_names_every_tool` iterates `_ALL_BUILTIN_TOOL_NAMES` and requires
the instructions to name every builtin tool — so registering one **changes a served byte** and
breaks Scope OUT, while not registering it ships an untaught tool, which the Trust Doctrine reads as
a defect. Both branches are bad. The in-repo precedent is `python -m loremaster.index`
(`index/__main__.py` + `index/cli.py`), which is in-container, serves nothing, and needs no
instructions change. **Also measured: `scripts/` is not COPYed into the image at all**, so the
legacy survey cannot run in-container regardless — which makes the port to `loremaster/` a hard
requirement for R2, not a preference.

---

## C. Design-mechanics decisions (the contract-freeze checklist)

Six recommendations are final (sidecar §5, reproduced below in rank order). Eight are pending.
Each carries the axis that turned out to matter most: **is a wrong choice SILENT or DETECTABLE?**
A wrong choice the adversary or cold audit would catch is cheap. One that yields a plausible number
nobody can challenge is expensive.

### C1 — ESC-2(b): the bootstrap RNG seed and leg attribution [RANK 1 — SILENT-plus-CORROSIVE]

The only item on this list whose wrong choice **writes a false fact into the durable record while
wearing a ruled fallback as cover.** An unseeded bootstrap reds the determinism pin for an
ARITHMETIC reason; E5's ruled fallback frames a red pin as the embedder's fault; the run receipts
then record *"bit-exactness broken at the embedder"* — which is false, and which has **two**
downstream victims: 11-ii's exact-skip rationale, and the E4 cache's justification (the cache
"restores bit-exactness for unchanged probes" — it restores nothing if the breaker is the
bootstrap, so the pin stays inexplicably red, or nobody re-checks because the receipts already
"explained" it).

**Recommended pin, two sentences — the second is what makes it detectable:**
> The bootstrap RNG is a per-run instance seeded from a single named module constant (no
> wall-clock, no OS entropy, no unseeded default anywhere in the runner), so the arithmetic layer —
> sampling, bootstrap, selection — is a pure function of the captured cosines. E5's
> which-leg-held receipt is only writable after an arithmetic-replay control: re-running
> selection+bootstrap on the SAME captured cosines twice must be bit-identical unconditionally — a
> mismatch there is an arithmetic defect and may never be recorded as the TEI leg.

Citation: §4.3's determinism control and R3 establish that the arithmetic must be deterministic;
**the seed mechanism itself is an admitted gap-fill** — the design never mentions a seed.

### C2 — ESC-3: the ≥98% gate's denominator [RANK 2 — SILENT]
> The gate's denominator is every portable-union sample (answered + identifier + hold-out-absent)
> WITHOUT a verbatim anchor — i.e. every sample whose verdict is decided by the floor comparison;
> flips are those whose `_cosine_absence_predicate` outcome differs between ci_low and ci_high;
> gate = flips/denominator ≤ 2%; the anchored-excluded count is recorded in the row beside the
> rate; legacy groups are never in the denominator on any instance.

Cost of the lenient reading: on an anchor-heavy corpus the never-flip mass mechanically inflates
agreement, the gate passes at too-small N, and **11-ii's entry condition is satisfied by a floor
noisier than the 2% the gate exists to bound.** Partial citation (D2's "known decisions" gloss);
the anchor-exclusion is the sidecar's labeled resolution of a genuine ambiguity.

### C3 — ESC-9: survival of the 30/15/30 minimums [RANK 3 — silent in prod, cheap to guard]
> The run declares `insufficient_corpus` (no adoption, honest note) iff derivable answered probes
> < 30, identifier probes < 15, or absent-leg samples < 30; these minimums gate VALIDITY only —
> adopted N is chosen solely by the D2 stability gate.

Strongest citation of the six: D0 retires them *"as the N rule"* (the qualifier is load-bearing),
and §3's `insufficient_corpus` sentence survives Addendum D untouched. Cost of the opposite
reading: a 12-probe foreign corpus trivially passes ≥98% (12 decisions agreeing at both bounds =
100%) and **adopts a meaningless floor — the #179 class re-created by the new machinery.**

### C4 — ESC-11: N-curve subsample mechanism [RANK 4]
> The pool is totally ordered ascending by the same point_id-derived key that decides membership;
> each ladder value's subsample is the first N in that order — nested, deterministic, RNG-free —
> and adopted N is the smallest ladder value whose nested subsample passes the gate.

Gap-fill. Tiebreak: with independent draws, "passes at N" is itself a noisy event and the
smallest-N rule becomes ill-defined (pass at 100 by luck, fail at 200).

### C5 — ESC-13: the R2 evidence package's address [RANK 5 — detectable but late-and-unrecoverable]
> The C6 (a)–(f) evidence package is committed under
> `docs/plans/v2/receipts/<run-date>-packet11i/` in the same change that lands the run receipts,
> and every citation of it — the consult doc, 11-ii's contract — uses that tracked path.

Support is repo law, not the design (admitted gap-fill). Cost: the F3 consult's evidence base
becomes unauditable and W-C's judged rendered shape (C6e) unverifiable — the #154 class.

### C6 — ESC-14: whether the R2 run adopts [RANK 6 — detectable, early, cheap]
> The lab-validation verb executes the COMPLETE engine path — measure → validity gates →
> adopt-or-decline per the bars → head mint via `_txn.retry_on_conflict` — producing a real
> measurement row and (bars met) a real adopted head; "dark" constrains what READS the rows, never
> what the verb writes.

Strong citation: C6e requires *"the adopted row's typed provenance fields, with real values"*,
which is unproducible if the verb never adopts.

### C7–C14 — PENDING (ESC-1 mechanics, 4, 5, 6, 7, 8, 10, 12)
Awaiting the sidecar's follow-up 2, which is reading the scout's source facts first.

---

## D. Raised items that are NOT 11-i's, and are not mine to bury

Scope law: nothing may be declared out of scope without the operator. These were found while
mapping and are surfaced for a ruling, not folded in silently.

1. **RAISED-4 — the prior art's guard suite has NEVER run in any gate.** `pyproject.toml`
   `testpaths` covers `lorescribe/tests`, `loresigil/tests`, `loremaster/tests` — **not
   `scripts/`**. Measured: `pytest --collect-only` collects 6,552 tests, of which
   `test_search_score_survey` accounts for **zero**; named explicitly the file collects **50**.
   So `TestPredicateParityWithProduction` — the `is`-identity pins that are the only thing
   preventing the survey's predicate from drifting away from production's — has never been checked
   by CI, and neither has the `choose_cosine_floor` dominance suite **that produced the 0.50649
   this entire packet exists to re-measure.** 11-i's port re-homes these (priced). The interim
   question — whether `scripts/` gets a `testpaths` entry now — is the operator's.
2. **RAISED-1 — the ruled design carries a factual error at the mechanism Addendum D was itself
   correcting.** D2 states every `point_id` input is in the scrolled payload; `slug` is not a chunk
   column, so `point_id(...)` cannot be recomputed from a scrolled row alone. Recommended fix: read
   `point_id` off the row's own `id` (`SurrealStore.upsert` writes `id = record.point_id`), which
   cannot drift from the stored key. Caveat: the row's `id` is a `RecordID` and `_bare_id` is a
   private staticmethod — the builder needs a sanctioned accessor. **Note the shape: D2's ⚠
   correction block was already fixing one phantom field and introduced a second error doing it.**
3. **RAISED-5 — B5 instructed the builder to reuse an exact-set state pin that does not exist**,
   and the calibration engine's own five states are unpinned AS A SET (`test_state_string_constants`
   asserts four of five individually; `_CALIBRATION_STATES` in the MCP tests is a hand-copied tuple
   used only as a parametrize source, with nothing asserting it equals the engine's constants).
   A sixth state could be added and nothing would notice — finding #4's shape, still live.
4. **RAISED-8 — the probe-task lifecycle is a genuine shared-policy candidate.**
   `CalibrationEngine.start/stop/wait_until_settled/status` is the identical POLICY 11-i needs, and
   B5 itself says *"extract a helper both engines call — escalate, never copy."* The design invokes
   its own escalation clause here. Extract in 11-i, or defer with a named decision point?
5. **RAISED-2 — `MessageLedger` has full DDL, a ledger class, and zero production wiring** at
   `d0ee2be`. Either deliberate staging or a wiring gap — not 11-i's either way, but it is the
   measured proof that **this repo has no registry preventing a silently-unwired table**, which is
   precisely the risk 11-i incurs by adding one.
6. **RAISED-6 — `ident_text` is not persisted per hit**, bounding any future per-hit anchor
   analysis. C6f's #180 rider remains computable (the predicate is query-level and
   `has_verbatim_anchor` IS persisted per query) — verified, not assumed. Cheap fix while porting.
7. **RAISED-7 — the survey's embedder bypasses the production config seam**
   (`_make_embedder` builds `EmbeddingConfig` from hardcoded constants rather than
   `to_loresigil_config`, which exists so `config.dim` reaches both `dim` and `output_dimension`).
   The in-process port retires this by construction — worth saying in the contract so nobody
   "helpfully" ports `_make_embedder` along with the core.
8. **RAISED-9 — where D5's probe-embed cache lives is an unmade shared-object decision.** Because
   `AppContext.embedder` is the SAME object the live search path uses, a cache installed on it is
   shared with live query traffic. Deferred out of 11-i by D5's YAGNI clause, but placement should
   be ruled before 11-ii builds it.

---

## E. The dark boundary — what 11-i must not touch

Enumerated so a conscientious builder does not "fix" something while in the neighbourhood:
the R6 constant retirement (11-ii); `lore_index` becoming a pure read (11-ii); R5's render changes
(11-ii); **any existing served model's CLASS docstring** — measured by the 10-d cold audit to be
rendered verbatim into `lore_index`'s `outputSchema`, so a "harmless docstring edit" IS a served
byte; the E1 disarm note string (byte-frozen); **R-11ii — `_format_result`'s per-hit gate still has
no `disarmed_by_drift` term, so the disarm MASKS #176 rather than fixing it** (hands off in 11-i;
11-ii inherits it); the 10-d audit's R3 residual (adjudication is 11-ii's). `smoke_p8b` is
render-shape-coupled — a builder editing smoke here is a tell that the boundary slipped.

Findings **#83/#87/#161/#176/#179/#180 stay OPEN.** They close in 11-ii when an honest measured
surface actually arms.
