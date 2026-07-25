# Addendum F-r2 — the corrected-constraints revision (DRAFT, not ruled; SUPERSEDES Addendum F)

> ⚠ **DRAFT — NOT RULED.** Authored 2026-07-25 by `fable-design-11i-b` at the lead's commission.
> **Supersedes `docs/design/2026-07-25-floor-calibration-addendum-F.md` @ `e109e91` without editing
> it** — the original stays committed so the correction history is visible. Reason for revision:
> three constraints Addendum F was designed under are false or lifted, per the operator's statements
> of 2026-07-25 recorded at `CONTRACT-FREEZE-DECISIONS.md` §0.4 @ `2a2de41`: **(1)** the "no clock
> constants" prohibition was never an operator ruling (it is §5's rationale about the TRIGGER's
> debounce, unscoped by restatement across four artifacts) and **k8s is a deployment target**;
> **(2)** packages may be added via uv — numpy/scipy specifically — rather than coded around;
> **(3)** worktrees/branches are to be SUPPORTED, not worked around. Additionally the probe's §4b
> (detection power) has LANDED since F was authored (`REPORT-probe-bootstrap-11i.md` @ `f66b980`,
> final — F's F0.4 provisional hedge is discharged below).

Tags as before: **[design-cited]** · **[source-verified]** (this worktree @ `2a2de41`, symbol named
— plus two host-side measurements run this sitting, labelled as such) · **[my judgement]**.
Marking (FILLS-A-BLANK / AMENDS-RULED-TEXT) carries over; this file only re-marks where a verdict
changed. Per the lead's explicit instruction: **nothing below softens a finding that was right —
where a section survives, it is said to survive, and why.**

---

## R1 — THE SWEEP: every Addendum-F section against the corrected constraint set

Constraint keys: **[clocks]** = the false no-clock prohibition · **[pkgs]** = numpy/scipy absence ·
**[wt]** = worktrees-are-broken · **[1proc]** = single-process assumptions (the k8s consequence).
A null result is stated as such — it is information.

| F-section | verdict | which constraint, and what changes |
|---|---|---|
| F0.1 (§B flag) | **REVISED** | [wt] F10 is void; the flag now points at R4/R6. F0.2 (§A resolved) and F0.3 (§C executing) SURVIVE UNCHANGED. |
| F0.4 (§4b provisional) | **DISCHARGED** | §4b landed final (`f66b980`). Consequences folded into the F2 row below and R2.5 — the numbers moved (flap at N=448 is 9.5%, not the provisional 7.0%@896 framing) and a NEW measured result exists: the detection-power table. |
| F1 (adopted-N rule) | **SURVIVES UNCHANGED** | Null on all four keys. It rests on the measured non-monotonicity, which is constraint-independent. One honest note added: on the final leg-B curve, "R and every larger evaluated rung passes" adopts the TOP rung (only 3584 qualifies) — expensive but honest, and [pkgs] makes large-N affordable (R3), so the rule's cost objection weakens rather than the rule. |
| F2 (calibrated adoption bound) | **SURVIVES, EXTENDED** | Null on [clocks]/[wt]/[1proc] — it is statistics, not scheduling. [pkgs] makes its paired-pseudo-measurement machinery cheap. §4b-final EXTENDS it: see R2.5 — the K1 fallback trigger did NOT fire, and the row gains a measured **sensitivity floor**. |
| F3 (gate denominator) | **SURVIVES UNCHANGED** | Null. Pure statistics; the operator fork (which-samples) stands as posed. |
| F4 (state re-predication) | **SURVIVES UNCHANGED** | Null — with one explicit preservation: §0.4 scopes the correction to the LEASE; **§5's quiescence preference STANDS for the TRIGGER, where it was written** [design-cited §0.4 "what is actually ruled"]. So D3's measure-at-settled-post-sweep, the settled-index gate, and `invalidated_remeasuring`'s "awaiting reconcile settle" predicate are all untouched. The trigger stays event-driven; only the lease gets clocks. |
| F5 (cause enum) | **SURVIVES UNCHANGED** | Null. |
| F6 (head_identity + query_shape) | **SURVIVES UNCHANGED** | Null on the key design. One addition ([1proc]): the fence-guard clause now binds to R2's lease epoch — same field, same semantics, multi-pod-proof by construction. |
| F7 (pins re-evaluation) | **SURVIVES UNCHANGED** | Null. The dropped K-depth gate stays dropped. |
| F8-C1 (seed/replay) | **REVISED (principle stands; pasteable words were library-bound)** | [pkgs] The ACCEPT was of words written for `random.Random`/`random.*`. Under numpy the principle is restated library-neutrally: **exactly one explicitly-passed generator object** (`numpy.random.Generator` seeded per-(scope,leg,N), or stdlib if numpy is not adopted for the shell); the monkeypatch-raise pin covers module-level `random.*` **and** `numpy.random.*` (both global-state doors); fixture N≥200 and the mutation-proven replay control survive verbatim — the small-N quantization blindness is a property of the data, not the library. |
| F8-C2…C6 | **SURVIVE UNCHANGED** | Null ×5. |
| F8-C7 (verb receipt) | **REVISED** | [wt] Its git half was F10's; see R4/R6. What SURVIVES regardless: all-three-coordinates-explicit (A2), refuse-on-`unknown`-LORE_VERSION as belt-and-braces, `loremaster.__file__` demoted to namespace check (its build-invariance is measured fact independent of any constraint). What CHANGES: once R4's fix lands, **real runtime git identity becomes the primary receipt field** — the hole closes instead of being routed around. |
| F8-C8…C13 | **SURVIVE UNCHANGED** | Null ×6 (C8's memory concern, C11's size bound, C13's re-registration point — all constraint-independent). |
| F8-C14 | **VOID → R3** | [pkgs] As the lead ruled: scar tissue, excised not amended. |
| F9 (affordability) | **VOID → R3** | [pkgs] The 5.7 h/rung crisis, the E2 sort-sweep-as-necessity, and the crisis framing are all consequences of coding around a missing dependency. Three pieces SURVIVE on their own merits, named in R3: the byte-exact equality control, the affordability receipt (demoted from crisis-mitigation to cheap honesty), and `--max-embeds` (its driver — TEI embed cost — was never the CPU constraint). The 11-ii event-loop flag survives softened (R3.5). |
| F10 (§B provenance riders) | **VOID → R4** | [wt] Scar tissue. Two clauses survive re-homed: fail-loud-on-`(None,None)` (the operator's own §0.2 pre-ruling) and the LORE_VERSION build-arg verification item (belt-and-braces until R4's fix is measured working). |
| F11 (amendment ledger) | **REVISED** | Entries re-scoped: D1's *"free at any N"* falsity is now **"measured false for the pure-Python path; to be RE-MEASURED under the numpy path before being cited again"** — the zero-embeds half stands. The D2-ladder conditional cap softens to R3's receipt. B2's entry stands (superseded by D0/D2 regardless of [pkgs]). All other rows stand. |
| F12.1 (percentile duplicates) | **REVISED** | [pkgs] The raise sharpens: the third consumer should resolve to **`numpy.percentile`/`numpy.quantile` as the one home** — *iff* its `method=` semantics reproduce `token_survey.percentile`'s nearest-rank behaviour byte-for-byte (an equivalence to VERIFY against the installed API, never assumed; if it does not, the existing helper stays the single home and numpy is not forced in). |
| F12.2 (testpaths) | **SURVIVES UNCHANGED** | Null. Third report asking. |
| F12.3 (capture_git_identity) | **SURVIVES, SHARPENED** | [wt] The mount-fix does NOT discharge it: four causes still collapse to one sentinel with no logging. Closing #134's topology (R4) removes one cause; the defect is the indistinguishability. Now #199-adjacent (the lead assigned addresses at `5ea1285`); the fix should log WHICH cause fired. |
| F12.4 (event-loop CPU) | **SURVIVES, SOFTENED** | [pkgs] shrinks the arithmetic from hours to (projected) seconds — but a multi-second CPU burst in the serving loop still stalls the MCP, and numpy releases the GIL only inside kernels. The raise stands at lower severity and now folds into R5's loop helper (the natural home for "run arithmetic off-loop"). |
| F12.5 (probe in flight) | **DISCHARGED** | §4b landed and is committed; the caution is moot. |

**Sections the corrections do NOT touch, said plainly because the lead asked:** F1, F3, F4, F5, F6,
F7, and eleven of the fourteen F8 adjudications survive verbatim. The adversary's measured wrong
builds were real and remain real — nothing in §0.4 un-measures them.

---

## R2 — The lease, redesigned for the real constraint: it must WORK, on k8s

### R2.1 — Independent judgement on the lead's four determinations (attacked, not accepted)

1. *"TTL + heartbeat is mainstream; burden inverts."* **AGREE** — and the burden test resolves
   instantly: my clock-free design cannot justify itself on the target (point 3).
2. *"Option B is dead."* **AGREE, trivially:** an in-process guard is not single-flight at N>1 pods.
3. *"Boot reclamation is unsafe under rolling updates."* **AGREE — and it is WORSE than the lead
   stated** [my judgement]: my Q2/F design had TWO clock-free reclamation legs, and **both** are
   unsafe at N>1. Boot reclamation steals a live holder's lease during a rolling update (the lead's
   case). But leg (b) — "quiescent-trigger reclamation" — is the worse failure: its liveness proof
   was *"the holder is provably not this process, and this process is the only durable home"* —
   a **process-local inference elevated to a global liveness claim**. At N=2, pod B observes
   lease-held ∧ rerun-flag ∧ no-local-run and "proves" the holder dead while pod A is mid-run and
   healthy. Steady-state mutual theft, not a rolling-update edge case. The fencing made theft
   *state-safe* but not *cheap*: every stolen lease discards a healthy constant-cost run. The design
   was correct only in the world where B1's "one server process" was a topology guarantee; k8s makes
   it a per-pod statement, and the proof collapses.
4. *"Fencing survives; TTL and fencing are complements."* **AGREE** — this was the one load-bearing
   piece of Q2/F worth keeping, and it is what makes TTL theft-tolerant (a lapsed holder's commit
   fails its fence, loudly).

### R2.2 — The design: a `StoreLease` primitive with k8s-Lease semantics on the SurrealDB store

Why store-backed rather than `coordination.k8s.io/Lease` [my judgement]: lore also deploys as a
single podman container on this host; the store is the one coordination substrate present in every
topology, and the store connection already rides the hardened `_txn` seam. The design implements the
k8s Lease *semantics* (holder + duration + renewal + fencing) without the k8s API dependency.

**Row** (one per deployment — the lease guards the instance's measurement loop, not a head; F6's
axes do not apply): `holder_identity` (per-process uuid4, minted at engine construction) ·
`fence_epoch` (monotonic, bumped through the counter-mint shape on every acquisition —
[design-cited capabilities §5]) · `renewed_at` (datetime) · `lease_duration` (duration; a **named
config constant with a default** — proposed `60s`, renewal cadence `duration/3` — declared tunables
per the no-hardcoded-values rule, and now unremarkable: the operator judges the lease on working,
not on clocklessness [design-cited §0.4]).

**The one correctness detail that is k8s-specific — a SINGLE CLOCK AUTHORITY** [my judgement,
load-bearing]: expiry must never compare a pod-local `now()` against a store-stamped time — N pods
have N clocks. Every time comparison happens **engine-side**: acquisition's CAS predicate evaluates
`renewed_at + lease_duration < time::now()` inside the store's own query (the `time::` family —
[design-cited capabilities §2]), and `renewed_at` is stamped by the engine, never by Python. Pod
clock skew then cannot cause theft or wedging. This needs one live-probe verification (the exact
SurrealQL duration-arithmetic spelling) by the builder — order of authority per repo law; no store
access from this seat.

**Operations, all through `_txn.retry_on_conflict`, CAS-shaped with defined-empty-result semantics
(the `scout.CommandSubscriber._mark` precedent — [source-verified], FU-era):**
- **ACQUIRE:** `UPDATE lease SET holder=$me, fence_epoch=$next, renewed_at=time::now() WHERE holder
  = NONE OR renewed_at + $duration < time::now()` — empty result = live holder exists = lost race:
  set the coalescing re-run flag (now a store field, since the flag must be cross-pod too) and
  return. Never retried, never blocked on.
- **RENEW (heartbeat):** every `duration/3` while running: `UPDATE … SET renewed_at = time::now()
  WHERE holder = $me AND fence_epoch = $mine`. **Empty result = lease lost ⇒ the holder aborts its
  run cooperatively** — and even an un-cooperative zombie is harmless, because…
- **COMMIT (fenced):** the run's end-of-run transaction (measurement row + head mint/adoption)
  carries `WHERE lease.fence_epoch = $mine` in the same transaction. A lapsed/stolen holder's commit
  fails LOUDLY and is discarded as a lost race (logged, typed, never retried).
- **RELEASE:** `UPDATE … SET holder = NONE WHERE holder = $me AND fence_epoch = $mine` in the
  runner's `try/finally` — the graceful path; the TTL is the ungraceful one.

**Failure matrix, k8s-first:** holder pod killed ⇒ progress resumes ≤ `lease_duration` later, any
pod. Rolling update ⇒ old pod holds until termination (graceful release in `finally`; SIGTERM grace
period covers it) — the new pod *waits* instead of stealing. GC-pause/slow holder past TTL ⇒ lease
lapses, another pod acquires, the zombie's commit fails its fence. Pod↔store partition ⇒ renewals
fail ⇒ holder aborts; the partition that blocks renewal also blocks the fenced commit, so no
split-brain write exists even in the abort-race window. Clock skew ⇒ irrelevant (one clock).

**Pins (11-i-a):** the standing hot-row laws — ≥8-way with overlapping racer lifetimes, 20
consecutive greens [design-cited capabilities §5] — plus three lease-specific discriminating
fixtures: (i) **expiry-seize**: short-duration lease, holder silenced, second claimant must acquire
and the zombie's fenced commit must be REJECTED (the fixture that kills a fence-less build);
(ii) **live-holder-not-stolen**: claimant races a renewing holder through > duration wall-clock and
must never acquire (kills a boot-reclaim-style build); (iii) **renewal-loss-aborts**: holder whose
lease is administratively reassigned must abort before its commit (kills an ignore-the-heartbeat
build). Coverage obligation per scout §3.3 stands: a conventional `_query`-owning ledger shape gets
the mutation proofs free; any bespoke shape is hand-added to the observed-coverage drive list.

### R2.3 — What survives from Q2/F, for the record

The **reframe** (correctness off the lease; economy on it), the **fencing epoch + counter-mint**,
the **CAS defined-empty-result discipline**, and the **no-serving-path-frame-ever-touches-the-lease
property** (now consult-backed — "the mechanism must never eat the function") all carry over intact.
What dies: both clock-free reclamation legs, Option B, and the TTL rejection — each traced to the
false [clocks] constraint or the false [1proc] assumption.

### R2.4 — Scope note

`StoreLease` is 11-i-a work (store-half, per the split's assignment rule) and is **built as the
shared primitive R5 consumes** — leader election for every maintenance loop, not a floor-engine
private. That is the k8s reframing §0.4 point 5 names, honored at birth rather than refactored in
later.

### R2.5 — F2 under the FINAL §4b (the provisional hedge discharged, and the fallback trigger answered)

§4b landed [design-cited probe §6.2 @ `f66b980`]: at N=56 the disjoint-CI test is **blind to a
+0.010 true move** (adopts at its own 1.5% null rate — zero discrimination), reaches a coin flip at
≈+0.05; at N=224 power at +0.020 is 33.5% against a 7.5% null. Two consequences:

1. **F2's K1 fallback trigger did NOT fire** — the mechanism detects real moves; it has a
   quantified sensitivity/null trade, priced by N, which is exactly what F2's calibrated bound
   manages. F2 stands.
2. **F2 gains one row field and one obligation, adopting the probe's own recommendation:** each run
   computes and persists its **measured sensitivity floor** — the injected-shift magnitude at which
   the calibrated adoption criterion reaches ~50% power, computed by the same paired-pseudo-
   measurement machinery with translated arms (arithmetic only, zero embeds, cheap under [pkgs]).
   *"The staleness detector's resolution is ±X cosine at the adopted N"* becomes a recorded number
   instead of an emergent property nobody wrote down. Whether/how that number is ever SERVED is a
   consult-channel question (the CI-refusal ruling suggests: as a pre-digested comparison, never a
   raw statistic) — flagged, not decided here [design-cited consult §1.3].

---

## R3 — F9 redone: the environment has numpy and scipy in it

**The corrected frame:** the crisis was manufactured by the missing dependency. What F9 got right
survives; what it built around the absence dies.

1. **Investigate `scipy.stats.bootstrap` FIRST — and the investigation has a known shape** [my
   judgement, from prior knowledge, every clause to be VERIFIED against the INSTALLED API per the
   packages rule]: it takes a statistic callable, supports `paired=True` multi-array input,
   percentile-method CIs at `confidence_level=0.90`, and a seedable `rng`. Two fit-risks to check
   rather than assume: (a) our resampling unit is **structured** — paired two-leg probes plus an
   unpaired identifier arm, each sample a (cosine, anchor) pair — which may exceed its paired-arrays
   shape; (b) its API surface renamed across scipy versions (`random_state`→`rng`). **If it fits,
   the hand-rolled resampling loop dies. If the joint structure exceeds it, hand-roll ONLY the
   resampler** (a dozen lines over a `numpy.random.Generator`) and keep the library for percentiles
   — the two-sided rule, minimal-surface clause.
2. **The decisive fact F9 discovered survives the correction: the COST LIVES IN THE STATISTIC, not
   the shell.** `scipy.stats.bootstrap` calling pure-Python `choose_cosine_floor` B times is the
   same O(B·N²). So the vectorized candidate-rate evaluator is still needed — but it is now a
   **numpy implementation** (sorted arrays + `searchsorted` counting, O((U+A)log(U+A))), not a
   bespoke pure-Python sweep. **The byte-exact equality control survives and matters MORE** (the
   lead's instruction, and F9's own): the evaluator ships with a property pin asserting equality
   with `choose_cosine_floor` over randomised inputs — achievable exactly because the computation is
   **counting and selection, not float accumulation** (candidate floors are observed cosines;
   rates are integer counts; no summation drift) [my judgement, verifiable]. And the containment
   pin sharpens: **every ADOPTED point floor is computed by the real `choose_cosine_floor`, once
   per measurement** (one call is cheap even at pool scale); only the B resamples ride the
   evaluator. The served number never touches the twin.
3. **Vectorizing must not rewrite the selection rule** — preserved verbatim per the lead: numpy is
   machinery for the bootstrap's internals; `choose_cosine_floor` remains the single definition of
   selection semantics, identity-pinned, and the equality pin is the instrument that keeps the
   numpy path honest.
4. **Re-measure; do not carry the crisis numbers.** The 5.7 h/rung figure is a pure-Python fact.
   Under the numpy evaluator the projected cost is minutes-or-less at pool scale — **[my judgement]
   until timed**; the E3 affordability receipt survives, demoted from crisis-mitigation to cheap
   honesty (the runner still times one pool-scale call and records the projected ladder cost in the
   row). If the measured number is still unaffordable, THAT is the moment a design escalation
   re-opens — a named trigger, not a standing crisis.
5. **`--max-embeds` (required, no default) SURVIVES UNCHANGED** — its driver is TEI embed cost,
   which no CPU library touches. **F12.4 (event-loop starvation) survives softened**: seconds of
   GIL-holding kernels still stall a serving loop; the R5 loop helper is its structural home
   (run-arithmetic-off-loop belongs to the shared runner, not to one engine).
6. **Dependency mechanics:** numpy (and scipy iff the shell fits) enter via uv at the workspace
   root, into the image — with the F12.1 consolidation rider (one percentile home, equivalence
   verified). The C1 seed discipline is restated library-neutrally (R1's F8-C1 row).

---

## R4 — The worktree/index determination: attacked, with two new measurements

### R4.1 — What I measured this sitting (host git 2.55.0, scratch repo in /tmp — outside the repo)

**[source-verified: host probe]** `git worktree add --relative-paths` produces a worktree `.git`
file of `gitdir: ../main/.git/worktrees/wt-a` (relative both directions — the back-pointer is
relative too), **and it silently marks the MAIN repository**:
`core.repositoryformatversion = 1` + `extensions.relativeworktrees = true`.

### R4.2 — Where the lead's determination is RIGHT

Root cause correctly named (the absolute-path `.git` file); `--relative-paths` correctly identified
as git's real fix; the one-mount-covers-all consequence is real (measured: both paths relative);
bumping the image's git "regardless" — correct, and R4.3 upgrades it from advisable to mandatory.

### R4.3 — What the lead's decisive-unknown MISSES: the version gate is not read-compatibility, it is a MANDATORY EXTENSION

The question "can 2.47.3 READ a relative gitdir?" is aimed at the wrong mechanism [my judgement +
measured basis]: relative `gitdir:` files are the ancient gitfile mechanism (submodules have used
relative gitdirs for a decade) — reading them is almost certainly fine. **The real gate is that the
2.48 flow bumps the repo to format version 1 with `extensions.relativeworktrees` — measured above —
and the v1 contract requires a git that does not recognise an extension to REFUSE the repository
outright.** Consequence: the moment the HOST creates one relative worktree, git 2.47.3 in the
container refuses **every** operation on the main repo and every worktree — not a null provenance
field, a hard error. *(The v1-refusal semantics are prior knowledge, flagged: the gating probe is
now "does the container's 2.47.3 refuse a v1+relativeworktrees repo" — one command against the
image, and I predict refusal.)* **So: the image git bump to ≥2.48 is MANDATORY for this path, not
hygiene** — and once both ends are ≥2.48 the compatibility question dissolves entirely. Interim
(before the bump + layout land): the adversary's case-D absolute path-identical mount is measured
working TODAY with 2.47.3 [design-cited adversary §1.2 case D] and needs no layout change.

### R4.4 — The layout half: "one directory" is mechanically right and underpriced

The relative paths only resolve if main repo and worktrees share a common mount ancestor — the
operator's one-directory sketch is exactly that. **The unpriced cost: it implies RELOCATING the
main checkout** under the shared root, and the current path is load-bearing across host config
(the lore-lore mount, `.mcp.json` entries, quadlet units, backup/cron references — an inventory to
take, not to guess). Two orderings exist: relocate-then-relative (clean end state, one migration
sweep) vs path-identical mounts now + relocation later (zero migration today). Recommendation:
treat the layout as its own small operator decision with the inventory attached; do not let it ride
in silently on 11-i.

### R4.5 — The index half: route it through the EXISTING overlay design, and price the embedding bill

Indexing every worktree as its own scope has a cost the sketch doesn't name [my judgement,
mechanism source-verified]: `records.point_id` keys chunks by (slug, tier, file_path, …) — distinct
scopes mean distinct point_ids, so N worktrees ≈ N× embeddings **with zero reuse across trees even
for identical files**, plus blast-radius/dead-code semantics per scope. This is not a green field:
**#125 / packets 17+23 already designed the worktree overlay** (CLAUDE.md's no-worktrees section:
"the overlay is designed but unbuilt"; #136's guard fix explicitly unblocked those packets). The
one-directory layout should land as an INPUT to reviving that design — not as a parallel
per-worktree-slug scheme invented inside 11-i's orbit. The `lore_index()` multi-root+branch render
surface already exists and is the right honesty vehicle. **Scope law: none of R4 is 11-i's to
build** — it gates R2-the-run's provenance receipt (via R6's C7 disposition) and otherwise belongs
to the worktree-support effort the operator just opened.

---

## R5 — The maintenance-loop extraction (the one the lead thinks matters most; I concur, with a timing discipline)

**The count is real:** the index watcher/sweeper, the token `CalibrationEngine` loop, and 11-ii's
floor loop would be the third hand-written instance of one POLICY — and RAISED-8 already escalated
this with B5's own "extract a helper both engines call" clause [design-cited scout RAISED-8, B5].
k8s upgrades the policy's content: at N replicas, every maintenance loop is a **leader-election**
problem, which is why R2.4 builds `StoreLease` as a shared primitive rather than a floor-engine
private.

**What is SHARED (the extracted thing), layered:**
1. **`StoreLease`** (R2.2) — acquire/renew/release/fence. Built in **11-i-a** (store-half; its
   first consumer is the R2 verb's single-flight).
2. **A leader-elected maintenance-loop runner** (working name `MaintenanceLoop`): owns the task
   lifecycle RAISED-8 named (idempotent start · cancel+suppress · `wait_until_settled` ·
   lock-guarded status) **plus** hold-lease-while-running, heartbeat cadence, abdicate-on-loss,
   cross-pod coalescing flag, and run-arithmetic-off-the-event-loop (F12.4's home). Built in
   **11-ii at B7.3** — the deferral RAISED-8 already recorded, upgraded in content, unchanged in
   timing, because **11-i has no loop consumer** (the verb is one-shot, synchronous; extracting the
   loop before its first caller exists is machinery-ahead-of-need).
3. **What each engine KEEPS (deliberately not shared):** its measurement mechanics, state domain,
   findings semantics, cost capture, trigger predicates — B5's wholesale-reuse rejection stands;
   sharing those would be routing-not-sharing in reverse.

**Migration order:** floor engine consumes `MaintenanceLoop` from birth (11-ii) ·
`CalibrationEngine` re-homes onto it in the same packet (the RAISED-8 line already drafted for the
11-ii packet file) · the index watcher/sweeper re-homes in its own later packet (it predates the
lease, is boot-critical, and deserves its own contract — a named deferral with the owner being
whoever holds the 11-ii close-out). **Can it be specified now?** The INTERFACE yes — this section
plus R2.2 is the spec sketch; the lease half freezes with 11-i-a's contract; the loop half is a
one-page design item in 11-ii's contract, not a new packet. Mutation-proof obligation carries: one
lease implementation, provable by perturbing the shared classifier/duration and watching every
consumer's pins move.

---

## R6 — The thirteen decisions of Addendum F: void / stands / changed

| # | F-decision | status |
|---|---|---|
| 1 | F1+F2 adopted-N rule + calibrated bound | **STANDS**, F2 extended by R2.5 (sensitivity-floor field; §4b hedge discharged) |
| 2 | F3 denominator fork | **STANDS** as posed |
| 3 | F4 states + 30–49 join | **STANDS** |
| 4 | F5 cause enum + two-degeneracy split | **STANDS** |
| 5 | F6 head_identity + query_shape reserve | **STANDS** |
| 6 | F7 pins (incl. the explicit drop) | **STANDS** |
| 7 | F8 fourteen adjudications | **STANDS for eleven**; C1 re-worded library-neutral (R1); C7 re-homed (R4/R6.12′); C14 void |
| 8 | C8 store-read authorization | **STANDS** (constraint-independent) |
| 9 | C11 manifest bound | **STANDS** |
| 10 | C13 bar re-registration point | **STANDS** |
| 11 | F9 bootstrap implementation | **VOID → replaced by R3** (scipy-first investigation; numpy evaluator + surviving equality control; re-measure; `--max-embeds` survives) |
| 12 | F10 §B riders | **VOID → replaced by R4 + this row:** interim = case-D path-identical mount + fail-loud-on-null + LORE_VERSION belt-and-braces; end-state = git ≥2.48 in the image + one-directory layout + real runtime git identity as primary receipt. The R2-run vehicle uses the INTERIM (it runs before the layout/bump land). |
| 13 | Lease = Q2 Option A | **VOID → replaced by R2** (TTL + heartbeat + fence, store-clock authority, `StoreLease` shared primitive) |

**New decisions this revision adds for the operator:** (14) adopt numpy(+scipy iff it fits) via uv
— [design-cited §0.4: pre-authorized in principle; the specific adoption should still be recorded]
· (15) bump the image's git to ≥2.48 (mandatory for the relative-paths path — R4.3) · (16) the
worktree-layout relocation decision with its config inventory (R4.4, its own small item) ·
(17) `StoreLease` parameters (`lease_duration` default 60s, renew at duration/3) — declared
tunables, recommended defaults · (18) the R5 extraction plan (lease in 11-i-a; loop helper in
11-ii B7.3; watcher re-home as a later packet).

---

## R7 — Raised under scope law (this sitting's finds)

1. **§0.4's process residual, seconded with this packet's second instance now measured:** nothing
   distinguishes operator-ruled from author-asserted once restated — the [clocks] chain crossed
   four artifacts. (The lead has raised it; recorded here as the sweep's own confirmation.)
2. **The v1-extension refusal probe** (R4.3) — one command against the image; should run before
   any host adopts `--relative-paths` on this repo, or the container's git goes dark repo-wide.
3. **The relocation config inventory** (R4.4) — needed before the one-directory layout is ruled.
4. **Is k8s lore intended to run N>1 replicas?** R2 is correct at any N; but if N>1 is near-term,
   the index watcher's lack of leader election becomes a live double-write hazard *before* its R5
   re-home — worth an explicit operator statement so the watcher re-home packet gets sequenced
   accordingly.
5. **The scratch probe left no residue:** `/tmp/wt-probe` is disposable and uncited (archive law —
   its findings are reproduced above with the exact commands implied; re-derivation is one
   `git init` away).

---

## R8 — CROSSING NOTE (appended same day): §0.5 @ `bd81906` landed while R4 was being written — reconciled here rather than left to mislead

The lead's own measurements (`CONTRACT-FREEZE-DECISIONS.md` §0.5, M1–M4) crossed this revision in
flight. Reconciliation, preserved not laundered:

1. **R4.3's measurement STANDS; its conclusion INVERTS in direction.** M1/M3 show #134 is a
   mount-topology problem: with the parent mounted at its identical absolute path (or a lore-owned
   worktree root where lore controls both sides), git **2.47.3 resolves both trees — no bump, no
   `--relative-paths` needed.** My measured v1+`extensions.relativeworktrees` poisoning therefore
   flips from "the bump is mandatory for the relative route" to **an argument AGAINST the relative
   route existing at all**: the moment any host adopts `--relative-paths` on this repo, the shipped
   2.47.3 refuses the repo wholesale. Two independent measurements, same verdict from opposite
   sides: **retire the relative-paths route; R4.3's "bump MANDATORY" is void with it** (the bump
   reverts to optional hygiene). R6's decision (15) is re-dispositioned accordingly.
2. **R4.4's relocation pricing SHRINKS:** M1's parent-mount needs no relocation on the dev host.
   Residual worth one line: mounting all of `~/PycharmProjects:ro` exposes sibling projects to the
   container — M3's lore-owned root avoids that and is the cleaner end-state; the layout inventory
   (R4.4) still applies to *that* migration, at smaller scope.
3. **M3's architecture, attacked as invited** [my judgement]: it holds. Two residuals to name in
   whatever packet builds it: (a) **`safe.directory` must be explicit image/config state** — M2
   shows uid-mismatch is the k8s DEFAULT, so the four-causes sentinel (#197) needs the
   distinguishing fix regardless of topology; (b) on k8s, a lore-owned root on a PVC puts git's
   file-based locking under whatever access mode the PVC has — single-writer (RWO) is fine;
   **RWX multi-pod git mutation is a flagged unknown**, which R5's leader election conveniently
   bounds (only the lease holder mutates worktrees).
4. **M4 corroborates R3 clause-for-clause** — scipy installs in ~1 s, `scipy.stats.bootstrap` has
   the statistic-callable/`paired`/`vectorized` shape, and the lead's ⚠ (interval convention must
   be verified against nearest-rank, never inherited — #198's drift class) is the same instrument
   R3.2 names: the byte-exact equality control. Convergent from independent seats; R3 stands
   unchanged.
5. **R4.5 (index-side: overlay routing via packets 17/23; the N× embedding-cost warning) is
   untouched by §0.5 and stands.**

---

## R9 — §R3 CORRECTED (appended same day, finding #201): the "numpy candidate-rate evaluator" was itself a hand-roll one level down

**The correction, owned:** §R3.2 concluded "the vectorized evaluator is still needed — a numpy
implementation." That wrote bespoke code for a library primitive: **`choose_cosine_floor`'s
candidate sweep IS an ROC sweep** [design-cited #201], and `sklearn.metrics.roc_curve` computes it
vectorised. §R3's decisive FACT stands (the cost lives in the statistic, not the shell — #201
confirms it as the root-cause chain); §R3's REMEDY is superseded by this section. Same failure
shape as the [clocks] chain: reasoning correctly up to the last step, then hand-rolling where a
package existed — this file's second instance, recorded as such.

### R9.1 — The investigation, MEASURED this sitting (not expected): the library path is exactly equal

Run in an ephemeral `uv run --no-sync --with scikit-learn --with scipy` overlay on this worktree
(repo env + libraries; `uv.lock` untouched; probe at `/tmp/roc_probe.py`, findings reproduced here
because a `/tmp` path is not a citable address). Environment: **sklearn 1.9.0 · numpy 2.5.1 ·
scipy 1.18.0** (numpy/scipy match the container's M4-measured versions; the container's sklearn
version is whatever the lead's probe installed — unmeasured by me, and the equality pin re-proves
the result wherever it runs, which is its job).

**[source-verified: ephemeral-env probe, ground truth = the REAL `choose_cosine_floor` imported
from `scripts/search_score_survey.py`]:**

1. **20/20 randomized trials: the roc_curve-derived selection equals `choose_cosine_floor`
   EXACTLY** — floor, false-fire rate, catch rate — on fixtures with duplicated cosine values,
   anchored samples on both arms, and dominance tie-breaks exercised.
2. **The reconciliation is an INDEX MAPPING, not arithmetic:** feed `roc_curve` the NEGATED
   cosines of the non-anchored samples (labels: absent=1), `drop_intermediate=False`; the returned
   arrays' +∞-prepended row makes **index j the strict-`<` counts for the j-th ascending
   candidate** (the strict-vs-`>=` boundary the lead measured as 96/96-wrong under the naive
   mapping is exactly one index of shift); rescale each arm's rate by (non-anchored n / full n) to
   restore the design's full-set denominators; restrict candidates to distinct UNION cosines; the
   dominance ordering is then three masked-array operations.
3. **Differently-broken control:** the naive un-shifted mapping differs at **44 of 75 candidates**
   on the same fixture — the probe can see the convention defect it exists to catch, so the 20/20
   agreement is not vacuous. Candidate-set check: 75 thresholds = 75 distinct fed cosines
   (corroborating the lead's 97-threshold measurement; `drop_intermediate=True` collapses it and
   is pinned FALSE).
4. **API facts read from the installed signatures, per the rule:** `roc_curve(y_true, y_score,
   pos_label, sample_weight, drop_intermediate)` · `scipy.stats.bootstrap(…, paired, …, method,
   bootstrap_result, rng, random_state)` — **both `rng` AND `random_state` exist in 1.18.0** (a
   transition-period dual; pin ONE — recommend `rng` — and record the dual as a #198-class drift
   hazard) · `np.percentile(…, method="inverted_cdf")` on 1..10 at p5 returns **1** (nearest-rank
   confirmed, matching #201's independent measurement) · `np.quantile` has a `weights` kwarg
   (both `weighted_percentile` copies are deletable, per #201).

**Consequence that makes everything else transfer:** because the library path is proven
**value-identical**, every probe measurement (§4b, the ladders, the flap tables) and every design
conclusion built on them (F1, F2, F3, F5, R2.5) carries over **unchanged**. Equality is what makes
the swap free.

### R9.2 — The §R3 re-check the lead asked for: the other one-level-down hand-rolls

- **Seeding:** C1's discipline maps onto the library: ONE `numpy.random.Generator`, seeded
  per-(scope,leg,N), passed as `bootstrap(..., rng=…)` — no bespoke seed plumbing beyond the seed
  derivation itself (domain). The replay control, the N≥200 fixture rule, and the
  no-module-level-randomness pin survive (now covering `random.*` and `numpy.random.*` module
  functions).
- **Paired draws:** `paired=` exists (read from the signature). The fit of our structured unit
  (paired two-leg probes + unpaired identifier arm) to its data model is the ONE remaining
  investigation for the contract author — with the index-array idiom (bootstrap over probe
  indices, statistic gathers the legs) as the documented in-library fallback shape. I read the
  signature, not the full paired semantics: said so rather than asserted.
- **The interval:** if `scipy.stats.bootstrap` is the shell, its `method="percentile"`
  interpolation convention is reconciled against ours the clean way: take
  `bootstrap_result.bootstrap_distribution` and apply `np.percentile(…, method="inverted_cdf")` —
  library resampling + the named nearest-rank convention, zero hand-rolled percentile code. #198's
  caveat is thereby a PARAMETER, exactly as #201 says.
- **BCa, noted not recommended:** in-library, built for skewed statistics (the S1 class) — but
  adopting it would AMEND D8's pre-registered "central 90% percentile", and the percentile method
  is measured non-degenerate here. Recorded as available if S1-class concerns recur on foreign
  corpora; a design change needing its own ruling, not a default.
- **The sensitivity floor (R2.5) and the N-ladder gate:** shifted pseudo-pairs and flip-counts are
  boolean/array glue over the same primitives — no new machinery.

### R9.3 — `choose_cosine_floor`'s role: I revise my own R3.2 containment pin [my judgement, flagged as a self-revision]

R3.2 kept the real `choose_cosine_floor` computing every ADOPTED floor, with the library path
confined to resamples. Under #201 ("the double loop should not exist") and the measured exact
equality, the cleaner architecture is: **the roc-derived path is the ONE production
implementation; `choose_cosine_floor` is retained as the executable SPEC and test ORACLE** — the
equality pin re-derives byte-agreement over randomized inputs on every suite run, and the
identity-pinned imports (predicate, bars) stay production-shared. One production implementation +
one test oracle is the stronger ONE-IMPLEMENTATION story; the R3.2 shape (spec on the hot path,
twin in the bootstrap) kept two production paths alive. Both options are before the operator
(decision 20); my recommendation is oracle-in-tests.

### R9.4 — The hand-roll sweep of the port (the lead's item 4): what carries, what dissolves

Against the scout's §1.1 symbol map, the ~988-LOC survey splits three ways:

- **DISSOLVES into library calls** (delete at port, oracle-pinned where semantics matter): the
  candidate sweep's production role (R9.1/R9.3) · the bootstrap loop that was never yet written ·
  `token_survey.percentile` + both `weighted_percentile` copies (#201 items 3–4) · the
  `GroupCosineSummary` percentile/mean/median arithmetic (np one-liners; the dataclass SHAPE
  stays for C6(b)'s report) · `every_nth` (already D2-retired).
- **CARRIES as domain code** (#201's "genuinely ours" residue, plus I/O): the identity-pinned
  imports (`_cosine_absence_predicate`, `_has_verbatim_identifier_anchor`, `_query_tokens`) · the
  bars · anchor masking as INPUT to the sweep · probe-text derivation rules · hold-out source-file
  exclusion · the capture pipeline (store/embedder I/O) · the hash-stable sampler (stdlib
  `hashlib`/`uuid` ARE the library) · `parse_eval_questions` · jsonl/report writers ·
  `VerdictSample`/`HitCapture` shapes.
- **Coarse quantum [my judgement]:** roughly the arithmetic third of the "pure core" dissolves;
  the domain two-thirds carries. The 50 re-homed tests re-target accordingly: the dominance suite
  becomes the ORACLE suite; arithmetic-helper tests retire with their helpers; the three
  `is`-identity pins carry verbatim.

### R9.5 — What this does to the §A split (the lead's item 5, answered plainly)

**The split LINE survives; the sizing figure attached to it is superseded; the character line for
11-i-b was always slightly wrong.** Re-derived against the scout's item table: the RUNTIME crisis
collapses entirely, but 11-i-b's BUILD cost was never mostly arithmetic — it was deliverables:
domain probes (0.06), the R2 verb + C6 evidence package (0.06), the determinism/equality pin suite
(~0.05 with the new oracle+convention pins), gate/ladder logic (~0.03), plus the port's
test-re-homing. Items that shrink: bootstrap 0.05→~0.02, N-curve 0.04→~0.03, paired decomposition
0.02→~0.01, port 0.04→~0.03; new cost: library adoption + convention pins ~+0.02. **Net: ~0.29 →
~0.24 ± 0.03** — a real reduction, not a collapse to glue. Recommendation: keep the ruled seam,
re-state b's character as *"domain probes + library-backed statistics + the pin suite + R2"*, and
re-surface the revised number to the operator rather than honouring the 0.29 mechanically. (11-i-a
is untouched by #201.)

### R9.6 — Decisions updated

Decision **11** (R3) is superseded by **R9**: the statistical core re-derives on
sklearn/scipy/numpy; the byte-exact equality control is the settling instrument for every
convention seam (boundary mapping, interval method, rng); `--max-embeds` and the affordability
receipt survive as before. **New: (19)** adopt scikit-learn as the third package (recommended —
the sweep is its primitive, measured exactly equal; the numpy-`searchsorted` assembly exists as
the two-package fallback if the operator declines, gated by the same pin — but assembling the
primitive from parts is the pattern this section exists to stop). **(20)** `choose_cosine_floor`'s
role: production path vs test oracle — recommend ORACLE (R9.3, a self-revision). **(21)** BCa:
available in-library, NOT recommended (would amend D8's pre-registration); recorded for foreign-
corpus contingency. **R9.5's** split note rides decision 1's re-surfacing.

*— end of revision. The operator rules; Addendum F @ `e109e91` remains the record of what was
designed under the false constraints, and this file is what replaces it.*
