# Packet 11-i — contract-freeze decision package

> ⚠ **SELF-CORRECTION (lead, 2026-07-24).** An earlier revision of this file wrote
> `SearchPipeline._format_result` in §E. **That symbol does not exist** — the per-hit gate is
> `SearchPipeline._to_result`; `_format_result` matches no `def` in `search.py`. Corrected
> throughout, not laundered, because the propagation path is the lesson: the dead name originates
> in packet 10-d's own comment block above `_COSINE_WEAK_MATCH_FLOOR`, travelled into the 10-d
> **cold audit**, then into the design sidecar's report, then into this package — **four artifacts
> deep, past a cold audit that specifically hunted this defect class.** Verified at source by the
> lead after `design-blind-11i` flagged it (FA6). The in-tree comment is still wrong and is
> raised as §D.9.

**Status:** ~~DRAFT~~ **PARTLY RULED 2026-07-25** — see §0. Both inputs that were outstanding in the
draft have landed (`design-blind-11i`'s verdict is folded into §C-ter; the sidecar's eight
remaining recommendations are C7–C14). This file is the durable address the 11-i contract cites; it
exists as a tracked path rather than a chat message precisely because of ESC-13's own finding (a
decision recorded at an unrecoverable address is a promise already broken — #152/#153/#154).

---

## 0. OPERATOR RULINGS — 2026-07-25

Ruled by the operator on 2026-07-25, on the session resuming this packet after a system crash.
Recorded here rather than in the session transcript per this package's own C5/ESC-13 finding.

| ref | ruling | binding effect |
|---|---|---|
| **§A sizing** | **SPLIT at the store/runner seam.** 11-i-a = store + engine skeleton (~0.13); 11-i-b = runner + R2 (~0.29). D7's literal line and keep-whole are both REJECTED. | The packet doc and INDEX row are rewritten into two packets — **but not until S1 lands** (below), because a DEGENERATE verdict forks to design repair and moots the slice. |
| **§B ESC-1 vehicle** | **Ephemeral container built from the worktree image, run against `:18500`.** Not a deploy — `lore-lore` is untouched. | Authorized WITH the §B riders, which are now binding contract items, not suggestions: (1) runs only AFTER the cold audit, never before; (2) the verb REFUSES to run without an explicit store coordinate — no default of any kind (Addendum A2's mistyped-coordinate hazard); (3) the DDL is reviewed against `docs/reference/surrealdb-31-capabilities.md` §1.1 as a named audit item. **Plus the #134 rider below.** |
| **§C C1–C14** | **A fresh contract-adversary attacks the fourteen recommendations BEFORE the operator rules them.** | Wholesale ratification is rejected: the sidecar and the lead are otherwise the only graders of their own list, which is the exact structural fault the adversary role exists to fix. The operator rules after the adversary reports. |
| **§D.12 10-d deploy** | **LEAVE IT undeployed; the accruing cost is noted and accepted.** | Deploy rides packet 03b's, as originally intended, rather than forcing a second hazardous `lore-lore` recreate (#165/#166). No new task; this row is the record. |

### 0.1 The §D.12 cost, re-measured rather than inherited

Confirmed by the resuming lead's own `lore_index()` call on 2026-07-25: production still renders
`cosine_floor.floor = 0.50649`, `state = "stale"`. Packet 10-d's disarm is merged and NOT serving.
Addendum E5's line — *"every day the disarm waits serves confident-wrong output"* — is live and the
operator has accepted it as a known, dated cost against the recreate hazard. **Evidence the hazard
is real and not theoretical:** a `lore-lore` recreate FAILED on this host on 2026-07-25 at 09:13
(`FileNotFoundError: source directory for tier 'surrealdb-docs' does not exist:
/home/ejprice/docker/mcp/lore-corpora/surrealdb-docs` — an eager-startup build failure that exited
the application); a subsequent recreate at 09:13:34 succeeded. **Re-open trigger:** packet 03b's
build phase reaching its deploy, or any independent `lore-lore` recreate — whichever comes first
carries 10-d with it.

### 0.2 The #134 rider on §B — RAISED, UNVERIFIED, and it is not a blocker yet

The §B table below was assembled without reference to **#134**, which `CLAUDE.md` records as: *lore
CANNOT BE DEPLOYED against a worktree — `.git` is a FILE naming an absolute host gitdir OUTSIDE the
`/workspace` mount, so git fails inside the container and the honesty line reads null for the exact
topology it is named after.*

R2's entire deliverable is a **receipt whose value is its provenance** (probe strategy, corpus,
embedder+prompt fingerprint, date — packet Exit). A run whose git provenance silently reads null is
a defective receipt of exactly the #131 shape, and #131 went invisible for months precisely because
nothing rendered the field.

**What is NOT established:** how far #134 reaches into a run from a BAKED image (code COPYed in, no
`/workspace` git dependency at runtime) as opposed to the mounted-worktree topology #134 was
measured against. These may be different failure surfaces. **This is assigned as a verification
item on the C7 adversary pass** (§C7 is ESC-1's mechanics half) — it must be measured, not reasoned
about, before the authorized §B vehicle is used. If provenance does read null, the vehicle still
stands; what changes is that the verb must FAIL LOUD on absent provenance rather than write a row
with an empty field.

**ANSWERED 2026-07-25 by the C1–C14 adversary pass** (`REPORT-adversary-c1c14-11i.md` @ `6c18bfb`
§1, with three controls): **#134 DOES reach a baked-image run** — the failure belongs to the
MOUNTED TREE, not to how the code got in, so baking does not escape it. `git -C /workspace
rev-parse HEAD` → `fatal: not a git repository: …/worktrees/lore-pkt11i` → `capture_git_identity`
→ silent `(None, None)`. **FOUR** distinct causes collapse into that one sentinel, one (`dubious
ownership`) named by neither #134 nor #131. Mechanism independently verified by the lead: the
worktree's `.git` is a 70-byte FILE naming `/home/ejprice/PycharmProjects/lore/.git/worktrees/lore-pkt11i`,
outside any `/workspace` mount; the main checkout's `.git` is a directory (control). **And C7's
receipt clause is INERT** — `loremaster.__file__` is `/app/loremaster/loremaster/__init__.py` for
every image ever built, so the clause called *"what converts a wrong-tree run to detectable"* has
zero discriminating power in the authorized vehicle. Rider proposals: Addendum F §F10 — the
operator's to rule, per §0's own "riders on an operator ruling are the operator's".

### 0.3 Where §D's raised items now live — addresses, so they stop being rediscovered

Three of §D's items (restated at Addendum F §F12) were filed as findings on 2026-07-25. Each had
been independently re-raised by multiple reports with no address to point at — the exact cost the
archive/citation law exists to prevent:

| item | finding | note |
|---|---|---|
| `capture_git_identity`'s silent `(None, None)` | **#197** | #131's shape, still live; four causes, one sentinel. Needs an owner; NOT 11-i's. |
| `weighted_percentile` hand-rolled twice, 11-i adds a third consumer | **#198** | ONE IMPLEMENTATION — escalate before copy #3, not after. |
| `scripts/` has no `testpaths` entry (§D.1 / RAISED-4) | **#199** | **Third independent report asking** — the scout, the adversary and the probe each found it separately. 11-i's port re-homes these tests by construction, so the live window is the interim; accepting that window is a legitimate answer, but it is the operator's. |

The remaining §D items keep their §D numbering as their address; §D.12 is ruled in §0 above.

### 0.4 ⚠ CORRECTION — the "no clock constants" prohibition is NOT an operator ruling, and k8s is a target

**Operator, 2026-07-25, verbatim intent:** *"I don't know who made the anti-wall clock ruling but it
wasn't the operator. I don't care how it works, only that it works. And that it works on k8s."*

**Traced to source.** The design's §5 says: *"**Quiescence over clocks:** the trigger defers while the
index is unsettled and dedupes while a run is queued/running. **No invented cooldown constant**; a
continuously-churning corpus renders `stale_remeasuring` honestly until it settles. (A clock-based
cooldown is a guessed constant with a failure mode; quiescence is a measured condition.)"*

That is a design author's rationale about **the TRIGGER's debounce** — when to SCHEDULE a
re-measurement. **It says nothing about lease expiry, and it is not an operator ruling.**

**How it became one.** §5 (trigger scope) → the blind review restated it as *"§5 forbids clock
constants"* (§7.3, unscoped) → this package carried that forward at §C-ter → the sidecar's Q2
**rejected TTL expiry "on §5's own grounds"** and designed a clock-free lease to satisfy it →
Addendum F's lease recommendation inherited it. **Four artifacts, and a rationale about one mechanism
became a prohibition governing a different one.** Same propagation shape as the dead
`SearchPipeline._format_result` symbol corrected at the head of this file — and the same lesson: a
restatement acquires authority the original never claimed.

**What is actually ruled:** nothing about clocks. §5's quiescence preference stands **for the trigger**,
where it was written and where its argument applies. **The lease is unconstrained on mechanism** and is
judged only on whether it works — on k8s.

**Consequences, and they are not cosmetic:**
1. **TTL + heartbeat renewal is back on the table as the mainstream answer**, and the burden of proof
   inverts: a clock-free lease must now justify itself, not the reverse.
2. **Option B (in-process single-flight) is DEAD.** k8s means multiple pods and rolling updates;
   single-flight must be cross-process or it is not single-flight.
3. **Option A's "boot reclamation" is UNSAFE on k8s, not merely contorted.** Under a rolling update the
   new pod boots *while the old pod is still serving* — boot-reclamation would let an incoming pod
   steal a live holder's lease. The design's clock-free condition fails on the target platform.
4. **The sidecar's epoch-FENCING survives and should be kept.** Fencing and TTL are complements, not
   alternatives: TTL bounds how long a dead holder blocks progress; the fencing token stops a slow or
   resurrected holder corrupting state after its lease lapsed. That pairing is the standard distributed
   answer and is what k8s's own `coordination.k8s.io/Lease` does (`leaseDurationSeconds` + renewal).
5. **k8s reaches past the lease.** N replicas each running a self-maintenance loop is a leader-election
   problem — which makes the lease MORE central to the architecture, not a detail of one engine. This
   is now an input to the maintenance-loop extraction, not just to 11-i.

**Process residual, raised not buried:** no instrument in this repo distinguishes *operator-ruled* from
*design-author-asserted* once a claim has been restated once. Both render as "ruled law" in prose. That
is a live defect class — this is its second instance in one packet.

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

### C7 — ESC-1 mechanics (the contract half; the vehicle half is §B, operator's) [batch RANK 1]
> The R2 verb is `python -m loremaster.<floor_module>` (the `loremaster.index` precedent) — NOT an
> MCP tool in 11-i; the module carries NO default store URL and REFUSES to run without an explicit
> coordinate; its receipt prints `loremaster.__file__`, the store URL, and the run's own corpus
> fingerprint, so a wrong-tree or wrong-corpus run is visibly wrong in the receipt itself.

The wrong-corpus failure is **silent in the numbers** — a floor measured against the spike store is
just as plausible-looking as the real one. The provenance-receipt clause is what converts it to
detectable-by-reading.

### C8 — ESC-6: exhaustive pool enumeration through a bounded `scroll` [batch RANK 2 — SILENT]
> Pool enumeration is EXHAUSTIVE and PROVEN so per run: the runner reads the chunk-table count,
> scrolls with a limit strictly greater than that count, and declares `measurement_failed` — never
> a silent truncation — if the returned row count equals the limit or disagrees with the counted
> total; fixed caps of the `IDENTIFIER_SCROLL_LIMIT = 20_000` kind are retired from the portable
> runner.

Why the inherited cap is nastier than it looks: uuid record-id order makes a truncated set a
*quasi-uniform subsample*, so the floor stays plausible while "pool size" and the N-curve's "up to
pool size" silently lie — and when the corpus crosses the cap between runs, WHICH 20k survive
changes, so membership churns with zero edits. That yields **phantom drift, spurious disjoint-CI
adoptions, and a broken determinism control, all attributed to the corpus.**

### C9 — ESC-8: k′, the absent-leg statistic, and the empty absent leg [batch RANK 3]
> k′ = 30 (a named, pre-registered module constant); the absent leg is the max cosine over the
> first k (fused-rank order) of the NON-source hits from the k′ capture — mirroring the shown set
> the verdict actually judges; an answered probe whose k′ hits all come from its source file
> contributes NO absent sample (dropped AND counted — never a synthetic 0.0), and the ≥30
> absent-leg minimum is evaluated AFTER such drops; serving-relevant per-hit statistics use the
> shown-k slice (C6f bound ii).

The dangerous branch is the empty leg: a synthetic `0.0` manufactures perfect-catch samples →
**catch inflated → a floor licensed that the corpus does not support** — the precision-first
asymmetry inverted at its source. Adversary-catchable only if the contract demands an
all-source-hits fixture. Demand it.

### C10 — ESC-10: the exact-skip's change-detection datum [batch RANK 4]
> Each measurement row persists `corpus_content_digest` = `sha512_hex` over the ascending-id
> concatenation of every chunk's (point_id ‖ content_hash), computed from the run's own exhaustive
> scroll (the C8 walk — no extra read); 11-ii's exact-skip compares the current digest to the head
> row's: equal ⇔ zero chunks added, removed, or edited ⇔ skip.

11-i owns the row 11-ii will compare against. Absent it, 11-ii's scheduler falls back to counts —
**§1.3's edit-blindness, the design's original sin, resurrected.** Tiebreak over B3's shared
embed-wrapper counter: the digest derives from the store's ACTUAL state, where a counter can miss
out-of-band writes and would need its own coverage proof.

### C11 — ESC-4: the probe manifest's persistence home [batch RANK 5]
> Each row persists its probe manifest in-row: an array of (point_id, probe_text_sha512) pairs over
> the run's answered pool, written in the same row-write as the measurement, so the NEXT run
> computes D4's surviving subset from the head row alone; on a determinism-control re-run the
> surviving subset MUST equal the full pool and the paired floor MUST equal the full floor.

That last clause is a free discrimination fixture and the contract should pin it. Cost if unpinned:
run 1 succeeds without a manifest (there is no prior run to need one), so **the gap surfaces only at
run 2, in 11-ii steady state, as a quietly-missing diagnostic** — D4's ruler-vs-measurand honesty
simply never gets logged.

### C12 — ESC-5: identifier-probe sampling under D2 [batch RANK 6]
> Identifier-probe membership is hash-stable over DISTINCT identity strings: the pool is the first
> 15 identities in ascending `sha512_hex(identity)` order (15 = the existing pre-registered count)
> — a single insertion changes membership by AT MOST ONE (pinned with an insertion-perturbation
> fixture) — and `every_nth` is retired from the portable runner entirely.

D2's `point_id` key is chunk-scoped and cannot apply verbatim to identity strings (one identity ↔
many point_ids), so this is gap-fill by analogy, labeled. Letting `every_nth` survive in this one
group re-imports the exact sampler-discontinuity defect D2 was written to kill.

### C13 — ESC-12: the self-retrieval match key [batch RANK 7 — SILENT]
> Self-retrieval is matched on the HIT's point_id equalling the probe's source-chunk point_id —
> `HitCapture` and the persisted per-hit jsonl gain a `point_id` field — and file-path-only
> matching is NOT self-retrieval. The two scopes differ BY DESIGN: self-retrieval is CHUNK-scoped
> (D2/R3 "its own chunk") while the hold-out exclusion is FILE-scoped (§3 "excluding the probe's
> source file").

If the search `Candidate` does not expose the row id, that is a search-surface gap to escalate,
never to work around with path matching. Path matching would let a sibling chunk from the same file
count as self-retrieval → drop-rate understated → the ≤20% `measurement_failed` gate silently
weakened. Catchable with a two-chunks-one-file fixture; demand it.

### C14 — ESC-7: "O(probes), never O(corpus)" vs the R2 full-pool embed [batch RANK 8 — cheapest]
> Steady-state runs embed O(adopted-N) probes; the R2 lab-validation run ALONE embeds the full
> derivable-text pool once to measure the N-noise curve, its embed count and wall-clock recorded in
> the row, and the curve's ladder extends to pool size — the packet's O(probes) clause binds the
> runner's steady state, not the one-time N-calibration.

Neither document states this reconciling sentence. Without it a builder can honour the packet's
literal wording, cap R2's pool, and **choose adopted N off a truncated curve** — the 11-ii entry
condition judged on a broken instrument.

---

## C-bis. The design author's own soundness judgement (evidence, not verdict)

Asked directly whether the design is sound-but-under-specified or structurally troubled, the
sidecar answered **ARCHITECTURALLY SOUND, factual substrate UNEVENLY VERIFIED** — a verification
sweep plus two doc corrections, not a design-repair fork — and volunteered that **it is a biased
instrument on exactly this question because it wrote the design.** Recorded here as evidence to be
weighed against the independent read, not as a finding.

Its argument for "sound": every one of the ~22 defects now on the table has a LOCAL fix that leaves
every load-bearing ruling standing. The interval-and-disjoint-CI staleness model, the identity-keyed
sampler (the correction STRENGTHENS it), two-leg determinism with recorded attribution, the
dark/cutover split, and the C6 handoff are contradicted by nothing found. The scout — functionally
an independent adversarial reader of the design's factual claims — found two false facts and **zero
architectural contradictions.**

Its argument for "unevenly verified", which convicts the design PROCESS rather than the
architecture: three failures share one shape — D2's bullet wrong twice, B5(c) naming a nonexistent
instrument as reusable, and the sizing wrong twice in the same direction (0.20 → 0.25–0.30 →
measured 0.42). *"The design asserts as verified-fact things derived from memory or partial reads,
at amendment speed, across seven same-day rounds."* Its own diagnosis of the mechanism is worth
preserving verbatim, because it is a reusable lesson:

> the correction swapped the key but inherited the original's verification debt — its "(verified)"
> parenthetical covered TWO claims with one tag (the `OMIT embedding` projection: verified, true;
> "every input is present": never verified, false). **A correction made under challenge must be
> re-derived in full at source, or it is the same error wearing a fix.**

That is the two-populations-under-one-count defect class applied to a provenance tag, inside a
document that cites that very law. Note also the structural contrast it draws: the design doc
carries **no provenance discipline**, while `docs/reference/surrealdb-31-capabilities.md` tags every
claim `[PROBED]`/`[CODE]`/`[INFERRED]` — and the difference in defect rate between the two documents
is the argument for adopting the discipline.

**Its recommendations to the operator:** (1) the contract-freeze checklist; (2) the two design-doc
corrections applied with existing corrections preserved, not laundered; (3) a one-pass provenance
sweep downgrading every unreceipted "verified" claim to stated-not-verified; (4) an independent read
that is **architecture-only**, asking one question — *do any two rulings contradict each other or
the packet's own constraints?* — rather than a fact re-sweep the scout has already done well.

⚠ **Item (4) is already running** (`design-blind-11i`), commissioned before this self-assessment was
written, though with a broader brief than architecture-only. Its verdict and the DIFF against the
sidecar's fourteen silences are the outstanding input to this package.

### The two design-doc corrections, as the sidecar drafted them

**RAISED-1 — append to D2 (preserving the existing ⚠ block, not replacing it):**
> ⚠ Second correction (scout-11i, confirmed at source 2026-07-24): `slug` is not a chunk column, so
> `point_id(...)` cannot be recomputed from a scrolled row alone — membership is keyed on the row's
> own `id`, which IS the stored point_id (`upsert` writes `id = record.point_id`), read never
> re-derived. The uniformity argument is unchanged.

**RAISED-5 — correct B5(c):** the DISCIPLINE is the reusable thing; the PIN must be BUILT. The
sidecar recommends folding the pre-existing calibration retrofit into 11-i, on the grounds that the
11-i contract is authoring the identical pin for its own eight states anyway — so one parametrized
pin covering BOTH engines' state sets costs near-nothing marginal, kills the unpinned-sixth-state
hole and the hand-copied `_CALIBRATION_STATES` tuple together, and is test-only (dark boundary
untouched).

**RAISED-8 — DEFER to 11-ii, with the decision point named now.** 11-i has no consumer for
`start/stop/wait_until_settled` at all (its engine runs synchronously via the one-shot verb); the
lifecycle's consumer is B7.3, which is 11-ii. Extracting in 11-i would build shared machinery ahead
of its second caller inside an already-oversized packet. Recommended 11-ii packet-file line:
*"B7.3's contract extracts the shared task-lifecycle helper (idempotent start / cancel+suppress /
wait_until_settled / lock-guarded status) and re-homes CalibrationEngine onto it — escalate, never
copy (B5)."* This is the deferral law's legitimate shape: named work, named owner, named trigger.

---

## C-ter. The independent blind review — verdict, and the DIFF

`design-blind-11i` (fresh Opus, both peer reports withheld and compliance affirmed unprompted)
returned **SOUND-BUT-UNDER-SPECIFIED**, independently corroborating the author's self-assessment
from a position that could not have inherited its frame. **25 named decisions**, six blocking a
builder on day one, and **three amendments to RULED TEXT rather than unfilled blanks** — so the
checklist must execute as a short design addendum plus a packet rewrite, NOT as a builder's Q&A.

It explicitly declined to hedge toward NEEDS-REPAIR, on the grounds that each of the three
ruled-text amendments is repaired by choosing between options the design *already contains*.

### The diff, classified

**In BOTH lists (corroborated — spend contract-freeze attention here first):** the D2 scrolled-payload
falsehood (its FA2 / scout RAISED-1); R2's execution vehicle and the DEPLOY-vs-in-container collision
(its C7/C9 / ESC-1); the ≥98% gate's unstated denominator (its §6 / ESC-3); k′ undefined (its §7.7 /
ESC-8); the probe-manifest home (its §7.5 / ESC-4); the exact-skip's change datum (its §7.2 / ESC-10).

**ONLY-IN-BLIND — the author's blind spots, and the highest-value output of the exercise:**
- **FA1 — B3's "ONE shared embed wrapper (#169/11a already route every embed through it)" DOES NOT
  EXIST.** Verified: at least three distinct embed paths (`Indexer._embed_records`, the batch path,
  `memory/local.py`'s own embedder). `embedding.py` is a config→embedder *constructor*, not a call
  wrapper. The wrapper is **future work in packets 11a/11b, both status `open`.** The sentence is
  written in the present tense about unbuilt work — and it is the only place the design says where
  D3's change-signal comes from.
- **FA3 — D1's "bootstrap costs ZERO embeds … free at any N" is half true, and the false half is the
  operative one.** Zero embeds: true. Free at any N: **false.** `choose_cosine_floor` is O(U·(U+A))
  per invocation, so B≥1000 re-runs per N-point is **O(B·N²)** — and there is **no numpy, no scipy
  anywhere in the dependency closure** (all four `pyproject.toml` files checked) and no bootstrap/CI
  helper in tree. *A naive implementation of the ruled instruction does not finish on a corpus-scale
  pool.*
- **FA4 — B2's constant-cost guarantee is superseded and never retracted.** It rests explicitly on
  "probe counts are fixed-N by design (R3 minimums)"; D0 retired those and D2 replaced R2's count
  with the full pool. B2's claim was **the entire answer to the operator's "often stale ⇒ thrash"
  concern**, and it now rests on a premise its own design deleted.
- **FA5 — this packet's OWN entry check is false.** It asserts #83/#87/#161/#179 all `open`; the
  ledger says **#83, #87 and #179 are `acknowledged`** (only #161 is open). A builder running the
  check literally sees none of the three and cannot tell whether entry failed.
- **C2 — the head-pointer key collides with D6.** B4 mints one head *per scope*; D6 generalises the
  served unit to *(statistic, point, CI, scope)* and says a per-hit floor is "one more row". A head
  keyed on `scope` alone collides the moment a second statistic exists — and the second statistic is
  #180's likely fix. **Deciding this after the table ships is a migration.**
- **C3 — §7's state set is specified against a model D3 DELETED.** `stale_remeasiring` means "leg
  fired; run queued", and B6-F4 rules the per-hit flag live under *churn* staleness — but D0/D3 retire
  the churn leg entirely and redefine staleness as a post-measurement verdict. Under D3 there is no
  churn staleness, and (leg 1 aside) you cannot be stale before you have measured. **11-i writes this
  field's domain**, so it reaches the schema.
- **C4 — `insufficient_corpus` lost its predicate.** §7 defines it as "min samples unreachable"; D0
  retired the minima and supplied no replacement trigger. The state survives; its definition does not.
  (Note this CUTS AGAINST the sidecar's ESC-9 recommendation — see below.)
- **C8 — THE PACKET WAS NEVER UPDATED FOR ADDENDUM D AT ALL.** It names the binding design as
  "R1–R8 + Addenda A and B", describes step 2 in pre-D7 terms, and contains **no mention of** the
  bootstrap interval, `B≥1000`, the N-noise curve, the ≥98% gate, hash-stable sampling, the paired
  decomposition, per-run cost capture, or disjoint-CI — *none of the six deliverables D7 assigns to
  11-i step 2*. The packet WAS maintained against Addenda C and E (F3's re-framing, E5's fallback
  both landed) and **skipped D**. This is the structural explanation for the sizing miss.
- **§7.3 — the single-flight lease has no expiry or crash-recovery semantics.** §5 forbids clock
  constants ("quiescence over clocks; no invented cooldown"), but a lease with no expiry **deadlocks
  permanently when its holder dies.** The blind reviewer calls this "a genuine hole, not a blank" —
  nothing in R1–R8 or A–E addresses lease release. This is 11-i's own hot-row work.

**ONLY-IN-SIDECAR — context advantages vs judged non-issues.** Its ESC-2 (bootstrap seed / leg
attribution), ESC-6 (the 20k scroll cap) and ESC-5 (identifier sampling) do not appear in the blind
list; all three are genuine and the first two are high-value, so these read as **context advantages**
(it holds D2's correction history and E5's leg-recording rationale). No sidecar item is contradicted
by the blind review. **One genuine conflict, and the blind reviewer is right:** the sidecar's ESC-9
recommends keeping 30/15/30 as validity floors, citing D0's "as the N rule" qualifier; the blind
review's C4 shows the design *also* retired the predicate that made `insufficient_corpus` meaningful.
Both can be satisfied — adopt ESC-9's pin AND record that it is *restoring* a predicate D0 removed,
rather than merely reading a qualifier. Stated so the operator rules on the real question.

### S1 — the one finding that could still escalate the verdict [MEDIUM confidence, HIGH stakes]

**The floor is a TAIL order statistic, and the nonparametric bootstrap is not consistent for extreme
order statistics.** Receipt: the 2026-07-07 adoption recorded false-fire **1/56** — exactly ONE union
sample sits below the chosen floor — so the floor is ≈ the 2nd-smallest order statistic, and its value
is one real sample's own cosine. Bootstrapping that deep in the tail yields a lumpy, possibly
**degenerate** interval.

**Both pre-registered rules then fail SILENTLY:**
- the ≥98% decision-agreement gate passes **trivially** at `ci_low == ci_high`, adopting the
  **smallest N tried**;
- disjoint-CI adoption fires on **any** movement, so D3's "hysteresis falls out free" **inverts into
  maximal flapping.**

Since one disjoint-CI test governs adoption, per-tier upgrade AND staleness (D6), a degenerate CI
breaks the design's central innovation — which would need **replacing, not parameterising.**

**This is now being measured before any contract is authored** (`probe-bootstrap-11i`): a synthetic
dataset in the 2026-07-07 regime, bootstrapped through the REAL `choose_cosine_floor`, with a
positive control and an N-ladder to find whether degeneracy resolves and at what N. Costs one
function and no store access. **The verdict on this packet's shape — contract-freeze checklist vs
design-repair fork — waits on that number.**

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
   be ruled before 11-ii builds it. ⚠ The blind review sharpens this: E4 records the cache as ALSO
   the determinism instrument backstopping E5 — but the cache is scheduled for **11-ii** while the
   determinism pin it backstops is a **must-prove pin in 11-i**. The fallback leans on something
   that will not exist yet.
9. **The dead symbol `SearchPipeline._format_result` in `search.py`'s 10-d comment block.** The gate
   is `_to_result`. One-line fix, but the propagation is the finding: 10-d's comment → the 10-d cold
   audit → the design sidecar's report → this package, **four artifacts and one cold audit deep.**
   Exactly the class `CLAUDE.md`'s rename-sweep section exists to catch, and evidence that prose
   naming a symbol needs a mechanical guard rather than a reader's diligence.
10. **`_surreal_fakes.py` deliberately does not model `id` on scroll rows**, and no production
    `scroll` caller reads `row["id"]` today. D2's sampler will be the **first**. Extending a fake to
    match a not-yet-written consumer is precisely where "the test environment is a fiction" starts —
    and the recommended `point_id` fix (§D.2) routes straight through it.
11. **`str(RecordID)` angle-bracket wrapping is undocumented in-tree.** The store reference says
    `str(RecordID)` round-trips but never records that a uuid-shaped id stringifies as
    `chunk:⟨3f1b2c4a-…⟩` — only `.id` / `_bare_id` strips it. Establishing that took a live probe.
    Given the file is a **required first read** for every store change, the omission earns a line in
    it — and it is a live landmine for the §D.2 fix.
12. **10-d is MERGED BUT NOT DEPLOYED — production is still serving the confident-wrong surfaces.**
    Confirmed independently: `lore_index()` at 2026-07-24T17:23Z still renders
    `cosine_floor.floor = 0.50649`, `state = "stale"`. Addendum E5 ruled that *"every day the disarm
    waits serves confident-wrong output"*, and E1 shipped precisely to stop that. The deploy was
    intended to ride packet 03b's rather than force a second hazardous `lore-lore` recreate
    (#165/#166). **Not 11-i's work — `DEPLOY: no` — but nobody appears to be holding it**, and it is
    the one item on this page with a live cost accruing daily. Operator's call.

---

## E. The dark boundary — what 11-i must not touch

Enumerated so a conscientious builder does not "fix" something while in the neighbourhood:
the R6 constant retirement (11-ii); `lore_index` becoming a pure read (11-ii); R5's render changes
(11-ii); **any existing served model's CLASS docstring** — measured by the 10-d cold audit to be
rendered verbatim into `lore_index`'s `outputSchema`, so a "harmless docstring edit" IS a served
byte; the E1 disarm note string (byte-frozen); **R-11ii — `_to_result`'s per-hit gate still has
no `disarmed_by_drift` term, so the disarm MASKS #176 rather than fixing it** (hands off in 11-i;
11-ii inherits it); the 10-d audit's R3 residual (adjudication is 11-ii's). `smoke_p8b` is
render-shape-coupled — a builder editing smoke here is a tell that the boundary slipped.

Findings **#83/#87/#161/#176/#179/#180 stay OPEN.** They close in 11-ii when an honest measured
surface actually arms.
