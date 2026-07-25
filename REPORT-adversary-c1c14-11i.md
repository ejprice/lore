# REPORT-adversary-c1c14-11i — adversarial grading of the fourteen pin-ready recommendations

brief-base v6 read

- **VERDICT: CONTRACT INSUFFICIENT** as a set of pin-ready sentences (§8). 13 of 14 admit a wrong
  build that satisfies them verbatim and ships the defect they exist to prevent; 5 are DEMONSTRATED
  with running code; the missing words for all 14 are written out and pasteable.
- **state:** done
- **deviations:** (1) target is PROSE → "wrong build" = an implementation satisfying the sentence
  verbatim that still ships the defect (§0). (2) NO store connection (#177); every number is
  arithmetic against the REAL `choose_cosine_floor`/`_cosine_absence_predicate`. (3) used the EXISTING
  `localhost/lore:latest`, not a worktree build — the measured seam is byte-identical in both (§1.2).
- **decisions-needed:** 8, all in §6 — §6.1 C14's ladder is not affordable as written · §6.2 the
  single-flight LEASE has no recommendation at all · §6.3 C3/C4's 30-vs-50 boundary · §6.4 the §B
  vehicle's provenance receipt is inert · §6.5 `capture_git_identity`'s silent `(None,None)` is a live
  production defect · §6.6 `scripts/` still has no `testpaths` entry · §6.7 two smaller residuals ·
  §6.8 C2's ambiguity is LARGER than the bar it feeds, which repo law makes a STOP.

## Per-item verdict (C1–C14)

| item | verdict | the wrong build that survives the sentence | §  |
|---|---|---|---|
| **C1** seed / replay | **ADMITS-A-WRONG-BUILD** (demonstrated) · UNCITED-GAP-FILL (verified: 0 occurrences of seed/RNG/random in 1176 design lines) | one `Random(SEED)` per RUN → the CI at a given N depends on which other ladder rungs ran first; the replay control PASSES on it | §2.1 |
| **C2** ≥98% denominator | **ADMITS-A-WRONG-BUILD** (demonstrated ×2) | (a) degenerate CI ⇒ 100% agreement ⇒ adopt smallest rung; (b) "denominator" fixes WHICH SAMPLES, never WHICH POOL — the two readings differ by 4.1 pts at N=100, i.e. **more than the entire 2% budget** | §2.2 |
| **C3** 30/15/30 | **ADMITS-A-WRONG-BUILD** (boundary) | a 35-probe pool passes C3's validity gate and has **no ladder rung** (C4's ladder starts at 50); adopted N records 50 for a 35-sample subsample | §2.3 |
| **C4** nested subsample | **ADMITS-A-WRONG-BUILD** (demonstrated) · UNCITED-GAP-FILL | "smallest rung that passes" is not "smallest rung such that every larger rung passes" — measured NON-MONOTONE agreement; nesting does not fix it | §2.4 |
| **C5** evidence address | **ADMITS-A-WRONG-BUILD** (weak) · UNCITED-GAP-FILL | "the package is committed" is satisfied by one file that points elsewhere; (a)–(f) are never individually demanded | §2.5 |
| **C6** R2 adopts | **ADMITS-A-WRONG-BUILD** (narrow — existing instrument covers most of it) | "head mint **via** `retry_on_conflict`" names the DRIVER, not the CLASSIFICATION; the driver's own docstring says classification is the caller's job | §2.6 |
| **C7** verb + receipt | **ADMITS-A-WRONG-BUILD** (measured) | `loremaster.__file__` is **`/app/loremaster/loremaster/__init__.py` for every image ever built** — the clause C7 calls "what converts a wrong-tree run to detectable" has ZERO discriminating power in the vehicle §B authorizes | §2.7 |
| **C8** bounded scroll | **ADMITS-A-WRONG-BUILD** | count-then-scroll is two reads: one benign concurrent insert ⇒ `measurement_failed` + a filed finding; and `SELECT * OMIT embedding` pulls every chunk's `source_text` in ONE result set — unbounded, unpriced | §2.8 |
| **C9** k′ / empty absent leg | **ADMITS-A-WRONG-BUILD** (demonstrated — the strongest finding) | the guard is keyed on the EMPTY leg; the SHORT leg (1..k−1 non-source hits) is ADMITTED and inflates catch **0.475 → 0.779, flipping `meets_adoption_bar` False → True**. Same licensing defect, unguarded door | §2.9 |
| **C10** change datum | **ADMITS-A-WRONG-BUILD** · UNCITED-GAP-FILL (but `content_hash` verified real) | "equal ⇔ skip" omits embedder fingerprint, bars, and instrument version from the skip predicate — a bars change never re-measures (#107's shape) | §2.10 |
| **C11** probe manifest | **ADMITS-A-WRONG-BUILD** | its "free discrimination fixture" is a determinism re-run — it can only see the UNCHANGED-corpus case, which is the one case the paired stat does not exist for | §2.11 |
| **C12** identifier sampling | **ADMITS-A-WRONG-BUILD** (weak) · UNCITED-GAP-FILL (labeled) | the named pin (insertion-perturbation) cannot see a lost DISTINCT dedup; the sentence says DISTINCT, the fixture does not test it | §2.12 |
| **C13** self-retrieval key | **ADMITS-A-WRONG-BUILD** | the ≤20% bar was pre-registered against an unspecified key; C13 TIGHTENS the key and inherits the bar, then forbids the only loosening that would relieve a false failure. Also: its escalation branch is dead — `Candidate.key` already IS the bare point_id | §2.13 |
| **C14** O(probes) vs full pool | **ADMITS-A-WRONG-BUILD** (measured) · UNCITED-GAP-FILL | mandates a ladder "to pool size" over an **O(N^1.92)** selection rule at B≥1000: **5.7 HOURS for one rung at pool 20k**, 32.9 h at 50k, pure Python, no numpy in the closure | §2.14 |

**#134 (§0.2's assignment) — ANSWERED: YES, it reaches a BAKED-IMAGE run.** The failure is a property
of the MOUNTED TREE, not of how the code got in: `git -C /workspace rev-parse HEAD` → `fatal: not a
git repository: …/worktrees/lore-pkt11i` → `capture_git_identity` → `(None, None)`, silently. Positive
control (main checkout) returns a real sha+branch. **FOUR distinct causes collapse to that one
sentinel**, one (`dubious ownership`) named by neither #134 nor #131. Fix, measured working: also
bind-mount the parent `.git` at its host-absolute path `:ro`. Receipts + 3 controls: §1.

**Ranking graded (§3):** C14 is ranked *"cheapest"* and is the most expensive item on the page; C9
carries no SILENT tag and I measured it flipping an adoption decision — both mis-ranked in the
expensive direction. **Nine findings are mine alone after the peer diff (§5).**

**Receipt pointers:** #134 §1 · per-item attacks §2 · ranking grade §3 · what the fourteen do NOT
cover §4 · peer diff §5 · escalations §6 · commands, raw output + control ledger §7 · verdict §8.

**Tool honesty (base §4):** lore's index watches the MAIN checkout, not this worktree (#125), so every
code-structure answer here is grep/Read against the worktree — a sanctioned fallback, said out loud;
no lore weakness routed around, so no friction row. Citations are SYMBOLS, not line numbers.
**Dating:** all measurements produced **2026-07-25**, in worktree `…/lore-pkt11i` at `0ff8868`,
against image `localhost/lore:latest` (`ae0e78d9a504`). Nothing here is "current" in any later sense.

---

## 0. Method, and the provenance receipt repo law demands

I did not make a `cp -a` scratch copy. My numeric probes are standalone scripts outside the repo
(`/home/ejprice/scratch-adv-11i/`, mine to delete — **deliberately not cited as an address**, per the
archive law; the code that matters is reproduced inline in §7) which `sys.path`-insert the worktree's
`scripts/` and run under `uv run --project /home/ejprice/PycharmProjects/lore-pkt11i`. I edited no
production code and no tests; nothing in the repo was mutated, so #140's three poison modes do not
arise — but the law still demands the receipt, and here it is, printed by every probe run:

```
loremaster.__file__          = /home/ejprice/PycharmProjects/lore-pkt11i/loremaster/loremaster/__init__.py
search_score_survey.__file__ = /home/ejprice/PycharmProjects/lore-pkt11i/scripts/search_score_survey.py
survey predicate IS production _cosine_absence_predicate: True
```

That last line is the one that matters: `search_score_survey.cosine_absence_verdict_fires is
loremaster.search._cosine_absence_predicate` evaluates **True**, so every catch/false-fire/flip number
below was scored by the *production* predicate object, not a paraphrase. `_cosine_absence_predicate`
is `best_cosine < floor and not has_verbatim_anchor` (verified at source in `search.py`).

**BASELINE-RED:** I ran no pytest at all, so the 394-failure baseline never entered any claim I make.
Said explicitly because the brief warns that "394 failed" reads identically either way.

**My probes' regime.** Synthetic captures in the 2026-07-07 regime (union ≈ N(0.60, 0.05); absent ≈
N(0.45, 0.05); anchored samples present), chosen so the floor lands 2–3 order statistics deep in the
union's lower tail — which is what the recorded false-fire of **1/56** implies. The regime is
inherited; **no value in this report is inherited** — every number was produced by this session.

---

## 1. THE ASSIGNED MEASUREMENT (§0.2) — does #134 reach a baked-image run?

### 1.1 The question, restated as something measurable

`capture_git_identity(repo_root)` (in `loremaster/index/snapshots.py`) shells out via
`_run_git_rev_parse` → `subprocess.run(["git", "-C", str(repo_root), "rev-parse", …])` and returns
`(None, None)` on **any** failure: missing binary, `OSError`, non-zero exit, empty stdout. That is the
#131 silent-sentinel shape, unchanged.

So the question is not about the CODE's provenance at all — it is: *given a container built by
`Containerfile` (which `COPY`s `loremaster/ loresigil/ lorescribe/` and **never copies `.git`**), what
does `git -C /workspace rev-parse HEAD` do?* Four runs, one probe script, four topologies.

### 1.2 The probe can see what it is looking for (controls first)

| case | `/workspace` is | `git -C /workspace rev-parse HEAD` | `capture_git_identity` |
|---|---|---|---|
| **A** — the #134 topology | the WORKTREE (`.git` is a FILE) | `fatal: not a git repository: /home/ejprice/PycharmProjects/lore/.git/worktrees/lore-pkt11i` · exit 128 | `(None, None)` |
| **B** — POSITIVE CONTROL | the MAIN checkout (`.git` is a DIR) | `f3971bdfc54604b021601b2d4ce52e38f9b5b17b` · exit 0 | `('f3971bd…', 'feat/surreal-unification')` |
| **C** — differently-broken | a dir with no `.git` | `fatal: not a git repository (or any parent up to mount point /)` · exit 128 | `(None, None)` |
| **D** — FIX CANDIDATE | worktree **+** the parent `.git` bind-mounted at its host-absolute path `:ro` | `0ff8868b177a442b6c26a25f6033a9d12a76ad99` · exit 0 | `('0ff8868…', 'pkt11i-floor-calibration-dark')` |

B is the control the P0 rule demands: it proves git works in the container, the binary is present, and
a `:ro` mount is not the obstacle. C is the differently-broken control: it fails for a **different,
named** reason (discovery walked to the mount point) and is rejected by a different code path, which
is what stops me claiming "the probe rejects everything".

**The measurement transfers to the worktree's code:** `_run_git_rev_parse` + `capture_git_identity`
are **byte-identical** between the image and this worktree —

```
92fc017435eaa80e8fdc2935fea8dd91367ccca42b2f24bc6473c90f7458474d  (image)  snapshots.py::_run_git_rev_parse..capture_git_identity
92fc017…  == the same 62-line span extracted from the worktree — `diff` returned 0
```

(The *files* differ — the image predates this branch — so I extracted and diffed the seam span, not
the file. `sha256sum` of the whole file differs and I am saying so rather than letting the file-level
hash imply more than it does.)

### 1.3 The answer

1. **YES — #134 reaches a run from a BAKED image.** Baked-vs-mounted CODE is irrelevant: the failing
   operation reads the MOUNTED TREE's `.git`, and a worktree's `.git` is a file naming an absolute
   host path the container does not have. Case A is a fully baked image with no `/workspace` code
   dependency, and it still reads null.
2. **There is a FOURTH cause nobody has named.** My first pass ran *without* the documented
   `--userns=keep-id --user $(id -u):$(id -g)` flags. On the MAIN checkout that produced
   `fatal: detected dubious ownership in repository at '/workspace'` — a real, silent
   `(None, None)` on a repository that is perfectly healthy. So the sentinel is reached by at least
   four distinct causes: missing binary (#131), `.git`-as-file (#134), no repo at all, and uid
   mismatch. **The bug is not any one cause — it is that `capture_git_identity` cannot tell them
   apart and neither can its caller.**
3. **The fix is one bind mount** (case D) and it is measured working. Cost: it exposes the whole
   `.git` directory to the container read-only.

### 1.4 …and the rider aims at the wrong field. THE RECEIPT §B AUTHORIZES CANNOT DISCRIMINATE.

§0.2's premise is that R2's receipt's value is its provenance. But R2's receipt, as **C7 specifies
it**, is `loremaster.__file__` + the store URL + a corpus fingerprint. **Git provenance is not in
it.** And the field C7 *does* specify is inert:

```
loremaster.__file__ = /app/loremaster/loremaster/__init__.py     <- case A (worktree mounted)
loremaster.__file__ = /app/loremaster/loremaster/__init__.py     <- case B (main checkout mounted)
loremaster.__file__ = /app/loremaster/loremaster/__init__.py     <- case C
loremaster.__file__ = /app/loremaster/loremaster/__init__.py     <- case D
```

Four different topologies, one 5-day-old image, **one identical string**. The `Containerfile`'s
`WORKDIR /app` + `COPY loremaster/ /app/loremaster/` + `uv sync --all-packages` fixes that path for
**every image this repo will ever build**. C7 calls this clause *"so a wrong-tree or wrong-corpus run
is visibly wrong in the receipt itself"* — for the wrong-TREE half, inside a container, it is not.
(Its value on a HOST run is real; §B rejected the host run.)

The field that *does* discriminate is already baked and already printed by my probe:
`LORE_VERSION=v0.4-236-g2b69616` — the host's `git describe --tags --always --dirty` passed at build
time as `--build-arg`. It defaults to `unknown` when the build arg is omitted.

**Missing words for C7's receipt clause (§6.4):** *"…prints the image's baked `LORE_VERSION` and the
image digest (`podman inspect --format '{{.Id}}'`), and REFUSES to run when `LORE_VERSION` is unset or
`unknown` — `loremaster.__file__` is recorded as a namespace check only, never as tree identity,
because it is a build-invariant constant inside the image (measured 2026-07-25). Git provenance, if
recorded at all, must FAIL LOUD when `capture_git_identity` returns `(None, None)` — the sentinel has
at least four distinct causes and the row cannot distinguish them."*

---

## 2. Per item: the wrong build, the missing words, the citation check

### C1 — bootstrap RNG seed and leg attribution · **ADMITS-A-WRONG-BUILD**

**Citation check.** The recommendation self-declares *"the seed mechanism itself is an admitted
gap-fill — the design never mentions a seed."* **Verified, and it is stronger than stated:**
`grep -ic "seed\|\brng\b\|random"` over all 1176 lines of `docs/design/2026-07-24-floor-calibration.md`
returns **0**, while `resample` appears twice. A design that mandates `B≥1000` resampling contains no
word for the thing doing the resampling. Its `§4.3`/R3 citation for *determinism* does check out (§4
item 3's fourth bullet, and R3's "determinism pin").

**THE WRONG BUILD.** One `random.Random(BOOTSTRAP_SEED)` created per RUN and threaded through the
whole N-ladder. It satisfies the sentence **exactly**: a per-run instance, seeded from a single named
module constant, no wall-clock, no OS entropy, no unseeded default anywhere. It also passes C1's own
arithmetic-replay control. And:

```
-- WRONG BUILD --
  ladder [50, 100, 200, 400]  -> N=200 CI = (0.501306, 0.525393)
  ladder [200]                -> N=200 CI = (0.499282, 0.524524)
  ladder [100, 200]           -> N=200 CI = (0.501306, 0.525393)
  SAME captured cosines, SAME N, SAME named seed. CIs equal? False

-- 12 ladder CONTEXTS all ending at N=200, same data, same seed --
  WRONG build: 5 DISTINCT N=200 intervals across 12 contexts
  RIGHT build: 1 DISTINCT N=200 interval  <- positive control: the probe CAN see agreement
```

**Why that is not academic.** D3's exact-skip rests on *"zero corpus change ⇒ … ⇒ bit-identical
floor"*, and C14 has R2 run a full ladder while steady-state runs only the adopted N. Under this
build, R2's adopted CI at N and 11-ii's fresh CI at the same N are computed at **different RNG stream
positions** — so "bit-identical on an unchanged corpus" is false across exactly the boundary the
disjoint-CI adoption test straddles. Phantom movement, attributed to the corpus.

**And C1's own control is blind at small N.** 20 runs of a **fully unseeded** bootstrap:

```
   N=200  B=1000  20 UNSEEDED runs -> 3 distinct intervals
   N=50   B=1000  20 UNSEEDED runs -> 1 distinct interval      <- 20/20 IDENTICAL
```

At N=50 the bootstrap interval is quantised so coarsely that **an unseeded build is
indistinguishable from a seeded one**. A determinism pin whose fixture is small-N certifies nothing —
this repo's fourth instance of the small-N non-discrimination class.

**Two more doors in the same sentence.**
- *It enumerates the forbidden* ("no wall-clock, no OS entropy, no unseeded default") — the repo's own
  six-defeat table says the forbidden set is unbounded. Allowlist the safe instead.
- *It is a prohibition with no positive obligation*: "a mismatch … **may never be recorded** as the
  TEI leg" tells a builder what not to write and never what to write. A build that writes `null` and
  continues satisfies it.

**MISSING WORDS.**
> The runner's arithmetic layer contains **exactly one** source of randomness: a generator instance
> created as `random.Random(f"{BOOTSTRAP_SEED}:{scope}:{leg}:{N}")` and passed EXPLICITLY as an
> argument to every function that draws — so the bootstrap at a given N is byte-identical whether it
> runs alone or as one rung of any ladder, pinned by a test that computes N=200's interval inside the
> ladder and standalone and asserts equality. **No module-level `random.*` call may appear anywhere
> in the runner**, pinned by a test that monkeypatches `random.random`/`random.randrange`/
> `random.choice` to raise and runs a full measurement. **The determinism/replay control's fixture
> uses N ≥ 200** (measured 2026-07-25: at N=50 an unseeded bootstrap reproduces its interval 20/20,
> so a small-N fixture cannot see the defect), and the control is itself **mutation-proven** — a test
> injects an unseeded generator and asserts the control goes RED. On a replay mismatch the run ends
> `measurement_failed` with a filed finding and **no adoption**; recording it as the TEI leg is
> forbidden and recording nothing is equally forbidden.

### C2 — the ≥98% gate's denominator · **ADMITS-A-WRONG-BUILD (two independent ways)**

**Citation check.** D2's *"agree on ≥98% of the union's samples — i.e. the floor's own wobble flips
≤2% of known decisions"* exists as claimed; the anchor-exclusion is honestly labeled as the sidecar's
resolution of a genuine ambiguity. ✓

**WRONG BUILD (a) — the degenerate interval.** The sentence defines the gate as `flips/denominator ≤
2%` and stops. Measured, against the real predicate:

```
  ci_low == ci_high == 0.50649: N=50   flips=0/50   agreement=1.0000  gate@2% = PASS
  ci_low == ci_high == 0.50649: N=800  flips=0/800  agreement=1.0000  gate@2% = PASS
  POSITIVE CONTROL  ci=(0.40,0.70): N=50 flips=50/50 agreement=0.0000 gate@2% = fail
```

A collapsed interval passes at the **smallest rung, unconditionally** — the exact defect C2 exists to
prevent ("the gate passes at too-small N"), reached through the door C2 does not guard. Whether the
interval actually collapses is S1's open question; **C2's sentence must not depend on the answer.**

**WRONG BUILD (b) — "denominator" fixes WHICH SAMPLES, never WHICH POOL.** At ladder rung N, is
agreement evaluated over the size-N subsample or over the full pool? Both readings are defensible;
they are different code. Measured on identical CIs:

```
      N    ci_low   ci_high   agree(subsample)   agree(FULL pool)
     50   0.49928   0.55215      0.9000              0.8575
    100   0.49841   0.52158      0.9200              0.9613     <- 4.1 points apart
    200   0.50131   0.52539      0.9500              0.9500
    400   0.50131   0.52158      0.9600              0.9663
    800   0.50665   0.52159      0.9775              0.9775
```

**The unspecified choice moves the measured quantity by more than the entire 2% budget the gate
allows.** That is the definition of a load-bearing ambiguity, and repo law makes it a STOP.

**A third thing, verified at source, that nobody has said out loud.** C2 excludes anchored samples
from the gate's denominator. `choose_cosine_floor` does the **opposite** for its own false-fire
denominator: `n_union = len(real_query_samples)`, anchored included. Two denominators inside one
instrument, on purpose, undocumented. It is defensible — but it must be *stated*, or the first
auditor to notice will read it as a bug.

**MISSING WORDS.**
> …gate = flips/denominator ≤ 2%, evaluated **at each ladder rung over that rung's own subsample**
> (the same samples the rung's interval was computed from — an in-sample agreement, stated as such);
> the row records both the anchored-excluded count **and** the full-pool agreement as a diagnostic.
> **The gate REFUSES to pass on a degenerate interval (`ci_high == ci_low`) or on a denominator below
> the C3 minimum** — a collapsed interval is a `measurement_failed`, never a 100%-agreement pass.
> Note explicitly that this denominator EXCLUDES anchored samples while `choose_cosine_floor`'s
> false-fire denominator INCLUDES them, and why.

### C3 — survival of the 30/15/30 minimums · **ADMITS-A-WRONG-BUILD (boundary)**

**Citation check.** D0 does retire them *"as the N rule"* (qualifier present and load-bearing ✓);
§3's `insufficient_corpus` sentence does survive Addendum D untouched ✓. The package already records
the honest conflict with the blind review's C4.

**THE WRONG BUILD — nothing joins C3's floor to C4's ladder.** C3 admits a corpus at **30–49**
answered probes. C4's ladder starts at **50** (D2: "subsample at N = 50, 100, 200, 400, … up to pool
size"). A pool of 35 therefore passes validity and has **no rung**. C4's rule — "the first N in that
order" — yields all 35, the gate is evaluated on 35 samples, and the row records **adopted N = 50**.
The persisted N is then a number no subsample ever had, and it is the number 11-ii's disjoint-CI
comparison and the C11 manifest are keyed on. Silent, and it only appears on small/foreign corpora —
i.e. exactly the deployments #179 is about.

**MISSING WORDS.** *"…the ladder is `[50, 100, 200, 400, …]` **truncated at pool size, with a final
rung equal to pool size whenever pool size is not already a ladder value**; the row records the
adopted subsample's ACTUAL size, never a nominal rung. A pool below the smallest ladder value is
evaluated at pool size or declared `insufficient_corpus` — say which."*

### C4 — N-curve subsample mechanism · **ADMITS-A-WRONG-BUILD (demonstrated)**

**Citation check.** Self-declared gap-fill ✓ (no design text specifies the subsample mechanism).

**THE WRONG BUILD — "the SMALLEST ladder value whose nested subsample passes the gate."** The
recommendation's own tiebreak paragraph names the hazard ("pass at 100 by luck, fail at 200") and
claims nesting dissolves it. **It does not.** Nesting removes the *sampling* noise between rungs; it
does not make pass-at-N monotone, because the bootstrap interval and the flip count are both
non-monotone in N. Measured, one dataset, real predicate:

```
  agreement(full pool) by N: 50:0.8575  100:0.9613  200:0.9500  400:0.9663  800:0.9775
                                            ^^^^^^     ^^^^^^  ← 200 is WORSE than 100

     bar | first rung that passes | smallest rung s.t. ALL >= it pass | differ?
   0.96  |                   100  |                             400   | *** YES
```

At a 0.96 bar the rule adopts **N=100 — a rung at which the larger rung 200 fails.** (Honest bound: at
the pre-registered 0.98 bar no rung passes in this synthetic, and the *subsample* denominator happens
to be monotone in this one dataset; one dataset is not a monotonicity proof, which is the point — the
recommendation is relying on a property nobody has established.)

**Second door, same sentence: what does N COUNT?** Each answered probe yields a paired
answered-sample AND its hold-out absent sample from ONE capture. "The pool is totally ordered … each
ladder value's subsample is the first N" is satisfied by a build that orders the flat list of
*samples* — which severs the pairing, so at rung N the absent set is no longer the hold-out of that
rung's answered set, and the catch bar is measured against a different population than the false-fire
bar.

**MISSING WORDS.**
> …**N counts PROBES, not samples**: each rung's subsample is the first N probes in point_id-key
> order, and that rung's answered leg, absent leg and identifier leg are exactly the legs derived
> from those N probes (the pairing is nested with them). **Adopted N is the smallest ladder value
> such that it AND every larger evaluated rung passes the gate** — a rung that passes while a larger
> rung fails is not a pass, and if no such N exists the run declares `measurement_failed` rather than
> adopting the first lucky rung.

### C5 — the R2 evidence package's address · **ADMITS-A-WRONG-BUILD (weak)** · UNCITED-GAP-FILL

**Citation check.** Honestly self-declared: support is repo law, not the design ✓.

**THE WRONG BUILD.** "The C6 (a)–(f) evidence package is committed under `…/receipts/…`" is satisfied
by ONE committed markdown file containing six headings and a sentence under each. Nothing in the
sentence demands the artefacts: C6(b) explicitly requires *"the per-query jsonl rows themselves"* and
C6(d) *"ten deterministically-chosen self-supervised probe texts beside ten human questions"*.
The blind review's S5 sharpens this into a hard requirement — the ONE dataset that could dry-run the
bootstrap (`scratchpad/survey_out_74w/`) is **already gone**, so R2's jsonl is the only observation
that will ever exist. A pointer-file satisfies C5 and loses it.

**MISSING WORDS.** *"…committed as SIX named artefacts under that directory — `(a)` the two selection
receipts, `(b)` the per-group summary table AND the per-query jsonl, `(c)` per-group anchor rates,
`(d)` the twenty probe texts, `(e)` the adopted row's typed fields dumped verbatim, `(f)` the #180
decomposition — each a file, listed by name in the run receipt, with a committed script that
regenerates (b)/(f) from the jsonl. `<run-date>` is the run's own UTC date."*

### C6 — whether the R2 run adopts · **ADMITS-A-WRONG-BUILD (narrow)**

**Citation check.** Strongest of the six ✓ — Addendum C's C6(e) does require *"the adopted row's
typed provenance fields, **with real values**"*, which is unproducible if the verb never adopts.

**THE WRONG BUILD — "head mint via `_txn.retry_on_conflict`" names the DRIVER, not the DECISION.**
That is the repo's own measured failure (#102/#120: eleven seams routed through the driver, each
matching `"Resource busy"` locally, **839 passed / 0 failed**, all eleven silently stopped retrying
under a reworded engine message). And it is not a hypothetical here — `retry_on_conflict`'s own
docstring says so:

> *"`attempt` is responsible for classifying whatever it catches into `RetryableConflictSignal` (or
> not); this function is responsible for everything that happens once that decision has been made."*

So a calibration mint that wraps `except Exception as e: if "Resource busy" in str(e): raise
RetryableConflictSignal()` satisfies C6 word-for-word and is a private copy wearing the shared name.
The shared classifier exists and has a name: **`_txn.is_retryable_conflict_error`**.

**Honest de-escalation, because the repo already built the instrument.** `test_retry_seam.py` carries
`TestNoSdkCallEscapesTheDriverAtRuntime` (a runtime guard over the real SDK object),
`test_every_production_sdk_call_site_was_OBSERVED_by_the_guard` (coverage as a CHECKED variable, over
`_all_sdk_call_sites` scanned from the whole package), and `TestEverySdkCallSiteActuallyRetries` with
the `_MUTATED_CONFLICT_TEXT` mutation. A new module that reaches the SDK is scanned automatically; a
mint routed through an existing `SurrealStore`/`_txn` seam inherits classification for free. So the
door is narrow — but it is open exactly where 11-i is most likely to walk: a **new** `attempt` body
written by hand around a hot-row mint. And the SINGLE-FLIGHT LEASE (see §4.1) is covered by none of
these instruments at all.

**MISSING WORDS.** *"…head mint via `_txn.retry_on_conflict`, **classifying with
`_txn.is_retryable_conflict_error` — no message match, no exception-text inspection, anywhere in the
calibration module** (ROUTING IS NOT SHARING; #102/#120). Proven by mutation: reword the engine's
conflict text at the classifier and the calibration mint's retry pin must go RED, exactly as
`test_retry_seam.py`'s `_MUTATED_CONFLICT_TEXT` proof does for the existing seams. The new module's
entry points are added to `test_every_production_sdk_call_site_was_OBSERVED_by_the_guard`'s driver
set in the same change."*

### C7 — ESC-1 mechanics · **ADMITS-A-WRONG-BUILD (measured)**

**Citation check.** The `loremaster.index` precedent is real — `index/__main__.py` and `index/cli.py`
both exist ✓. `scripts/` is genuinely absent from the image (`Containerfile` COPY lines) ✓.

**THE WRONG BUILD.** A verb that prints exactly what C7 demands and is *still* a wrong-tree run: see
§1.4 — `loremaster.__file__` is `/app/loremaster/loremaster/__init__.py` for **every** image, measured
across four topologies on a 5-day-old image. The clause C7 identifies as "what converts it to
detectable-by-reading" reads identically for the right image and the wrong one.

Second, smaller door: *"carries NO default store URL and REFUSES to run without an explicit
coordinate"* forbids a default **URL**. §B's own rider is broader — it names the *coordinate*,
because Addendum A2's hazard is a mistyped **ns/db** silently materialised as empty, not a wrong URL.
A build with `--url` required and `--namespace lore --database lore` defaulted satisfies C7's sentence
and re-opens A2 exactly.

**MISSING WORDS.** As in §1.4, plus: *"…REFUSES to run unless **all three** of url, namespace and
database are supplied explicitly — no default for any of them (Addendum A2: a wrong ns/db is
MATERIALISED, not rejected) — and refuses if the resolved namespace/database pair is not the one named
on the command line."*

### C8 — exhaustive pool enumeration through a bounded `scroll` · **ADMITS-A-WRONG-BUILD**

**Source facts, verified.** `SurrealStore.count(tier=None)` exists, so "reads the chunk-table count"
is buildable. `SurrealStore.scroll` emits `SELECT * OMIT embedding FROM chunk … ORDER BY id LIMIT
$limit` — a SINGLE query, deterministic ascending record-id order, **no pagination, no server-side
cap on `limit`** (the `_MAX_HYBRID_K = 1000` clamp is on `hybrid_search`, not on `scroll`).
`IDENTIFIER_SCROLL_LIMIT = 20_000` is real ✓.

**THE WRONG BUILD (a) — a benign insert becomes a filed finding.** Count and scroll are two separate
reads. One chunk indexed between them makes `returned != counted`, and C8 says that is
`measurement_failed` — which §4.5 defines as *filing a deduped finding* because "the instrument, not
the corpus, is suspect". On an actively-watched tree that is a routine race being escalated as an
instrument fault. The design already owns the right mechanism for this and C8 does not use it: the
**settled-index gate** discards and re-queues.

**THE WRONG BUILD (b) — the projection is unbounded and unpriced.** `SELECT *` includes `source_text`
and `ident_text` for **every chunk in the corpus**, in one result set, in memory. C8 mandates
`limit > count`, i.e. deliberately no truncation, at corpus scale, inside the server process the MCP
is serving from. Nobody has priced that; the retired 20k cap was at least a bound. C8's own analysis
(rightly) demolishes the cap's *sampling* consequences and silently inherits its *resource* role.

**MISSING WORDS.** *"…scrolls with a limit strictly greater than the counted total and, when the
returned count disagrees with it, **discards and re-queues the run through the settled-index gate**
(not `measurement_failed`; a concurrent write is the corpus moving, not the instrument failing) —
reserving `measurement_failed` for `returned == limit`, which is a real truncation. The enumeration
reads only the columns it needs (`id`, `identity`, `file_path`, `content_hash`, `chunk_type`,
`ident_text`) — never `SELECT *` at corpus scale — and the row records the enumerated count and the
scroll's peak result size."*
⚠ A narrowed projection needs a `scroll`-shaped store read that does not exist today: that is a
**production surface change inside a `DEPLOY: no` packet** and should be ruled, not improvised.

### C9 — k′, the absent-leg statistic, the empty absent leg · **ADMITS-A-WRONG-BUILD — my strongest finding**

**Citation check.** §3's *"capture k′ > k hits to survive filtering"* exists ✓; **the value 30 is a
gap-fill** and is not in the design. `SURVEY_K = 10` ✓; k′=30 is within `_MAX_HYBRID_K = 1000` ✓.

**THE QUANTIFIER ATTACK, and it lands.** C9 guards **one** value of a continuum. "An answered probe
whose k′ hits **all** come from its source file contributes NO absent sample." But a probe with 1, 2
or 9 non-source hits is **admitted**, and its absent-leg max is taken over hits pulled from deep in
the fused ranking — systematically LOWER cosines, systematically MORE catch. That is precisely the
"catch inflated → a floor licensed that the corpus does not support" failure C9 names for the empty
leg, reached through a door C9 explicitly opens.

Measured, real `choose_cosine_floor`, k=10, k′=30, a source-concentrated probe mix (20 probes with no
same-file hits, 20 at 40%, 30 at 75%, 25 at 90%, 5 fully self-concentrated):

```
  C9 AS WRITTEN (short slices admitted): n_absent=95  median absent=0.4694  floor=0.52902  catch=0.779  ADOPTS=True
  CLOSED  (short slices dropped too)   : n_absent=40  median absent=0.5457  floor=0.52902  catch=0.475  ADOPTS=False

  POSITIVE CONTROL — same mix with NO source-concentration (the two rules must agree):
  C9 AS WRITTEN: n_absent=100 floor=0.51051 catch=0.000 ADOPTS=False
  CLOSED       : n_absent=100 floor=0.51051 catch=0.000 ADOPTS=False
```

**`meets_adoption_bar()` flips False → True on the sentence's wording alone.** The control shows the
probe is not just reporting a difference wherever it looks: with no source concentration the two
rules are identical to five decimal places. This is a licensing decision — the D2 precision-first
asymmetry inverted at its source, exactly as C9's own body says.

**Second hole in the same item, and no recommendation covers it: THE ABSENT LEG HAS NO ANCHOR RULE.**
A `VerdictSample` carries TWO fields. C9 defines the absent leg's `max_cosine` and says nothing about
`has_verbatim_anchor`. Verified at source: `capture_query` computes `has_anchor = any(
has_verbatim_identifier_anchor(query, hit.ident_text) for hit in hits)` — **per query, over ALL k
hits, including source-file hits**. Re-using that flag for the hold-out sample marks a probe anchored
because of a hit the hold-out just removed. Direction: it over-marks anchored ⇒ those samples can
never fire ⇒ catch understated (conservative) **but** they are also dropped from C2's gate denominator
⇒ fewer possible flips ⇒ **agreement inflated ⇒ the gate passes at a smaller N.** Non-conservative
where it matters.

**MISSING WORDS.**
> …the absent leg is the max cosine over **exactly k** non-source hits (fused-rank order) from the k′
> capture, **with `has_verbatim_anchor` RECOMPUTED over those same non-source hits** — never inherited
> from the answered leg. **An answered probe whose k′ capture yields FEWER THAN k non-source hits
> contributes NO absent sample** — dropped AND counted, in the same bucket as the all-source case;
> the ≥30 absent-leg minimum is evaluated after such drops, and the row records the drop count split
> by cause (zero non-source vs short slice). **Pinned with a fixture in which a majority of probes are
> source-concentrated**, asserting that the short-slice probes are dropped and that the resulting
> catch rate is the closed-rule value — a fixture with no source concentration cannot see this
> (measured 2026-07-25: the two rules agree to 5 d.p. on an unconcentrated fixture and differ by 0.30
> in catch, flipping adoption, on a concentrated one).

### C10 — the exact-skip's change-detection datum · **ADMITS-A-WRONG-BUILD** · UNCITED-GAP-FILL

**Source check — the good news first.** `content_hash` **is** a real chunk column
(`surreal_schema.py::_CHUNK_FIELD_SPECS`), so C10 is buildable and does NOT repeat the #170 phantom-
field shape that D2's own correction had to fix. Verified rather than assumed, because that is the
class this packet has already produced twice.

**THE WRONG BUILD — "equal ⇔ zero chunks added, removed, or edited ⇔ skip."** The right-hand
biconditional is false as a SKIP predicate. Digest equality says the CHUNK TABLE is unchanged. It says
nothing about: the embedding-schema fingerprint (leg 1 — a re-embed under a new model leaves
`content_hash` untouched and moves every cosine), the **bars** (`D2_MAX_FALSE_FIRE_RATE`,
`D2_MIN_NONSENSE_CATCH_RATE`, the ≥98% gate), the instrument version, or k′/N. A build that skips on
digest equality alone will **never re-measure after a code change to the selection rule** — the
adopted floor silently outlives the rule that produced it. That is #107's shape: a change that never
migrates, invisible because nothing re-runs.

**MISSING WORDS.** *"…11-ii's exact-skip compares the current digest to the head row's **and**
requires the head row's embedding-schema fingerprint, bars tuple, instrument version and k′ to equal
the current ones; ANY inequality re-measures. The row persists all of them so the comparison is a row
read, not an inference."*

### C11 — the probe manifest's persistence home · **ADMITS-A-WRONG-BUILD**

**Citation check.** D4's surviving-subset mechanism (same `point_id` present AND unchanged probe-text
sha via `records.sha512_hex`) is real ✓.

**THE WRONG BUILD — the "free discrimination fixture" discriminates in the wrong world.** C11 pins:
*"on a determinism-control re-run the surviving subset MUST equal the full pool and the paired floor
MUST equal the full floor."* That fixture is an **UNCHANGED corpus** — the one case in which the
paired decomposition has no work to do. It cannot see: a surviving-subset computation that compares
against the wrong run's manifest, a probe-text normalisation mismatch that survives because nothing
changed, or a paired floor computed over the wrong leg. The pin the recommendation calls free is
free because it is nearly empty.

**Second door: "the run's answered pool" is ambiguous** — the full derivable pool or the adopted-N
subsample? Run 1 writing one and run 2 expecting the other yields a surviving subset that is wrong
without ever being empty. And it only appears **at run 2, in 11-ii**, which is C11's own stated cost.

**Third, unpriced: SIZE.** An in-row array of (point_id, sha512hex) over the full pool is ~200 bytes
per probe. At a pool in the tens of thousands that is a multi-megabyte array on **every append-only
row, every sweep cycle**. C11's tiebreak against a separate table was argued on provenance grounds
and never on size.

**MISSING WORDS.** *"…the manifest covers the run's **full derivable answered pool** (not the adopted-N
subsample), and the row records `len(manifest)` beside it. Pinned by TWO fixtures: (i) the
determinism re-run (subset == pool, paired == full) and (ii) **a changed-corpus fixture in which a
named subset of probe texts is mutated, asserting the surviving subset is exactly the unmutated probes
and the paired floor equals the floor computed on those probes alone** — (i) alone cannot fail on any
build that is wrong only when something changed. The expected row size at lore's pool scale is
measured at R2 and recorded; if it exceeds [operator-set bound], the manifest moves to its own table
— a decision to make before the table ships, not after."*

### C12 — identifier-probe sampling under D2 · **ADMITS-A-WRONG-BUILD (weak)** · UNCITED-GAP-FILL

**Citation check.** Honestly labeled as gap-fill by analogy ✓. `IDENTIFIER_QUERY_COUNT = 15` ✓. D2's
key is chunk-scoped and one identity maps to many point_ids ✓.

**THE WRONG BUILD — the named pin cannot see the named property.** The sentence says the pool is *"the
first 15 identities in ascending `sha512_hex(identity)` order"* over **DISTINCT** identity strings, and
then names ONE fixture: *"a single insertion changes membership by AT MOST ONE (pinned with an
insertion-perturbation fixture)"*. A build that forgets the dedup — easy, because `every_nth` is being
retired and `sorted({…})` is being rewritten — passes the insertion-perturbation fixture perfectly
(one insert still changes at most one slot) while filling 15 slots with 3 distinct identities repeated
across many chunks. The identifier leg silently becomes 3 queries. This is the "a message that
promises a check the assertion does not perform" class: the sentence says DISTINCT, the fixture tests
insertion stability. (Today's `sample_identifier_queries` **does** dedup — `sorted({str(row[identity])
…})` — so this is a rewrite-regression risk, not a live bug.)

**MEASURED, and NOT confirmed — reported because a negative result with a control is worth more than
a hunch.** I hypothesised that fixing the identifier leg at 15 while the answered leg scales would
move the floor materially, because anchored samples enlarge `choose_cosine_floor`'s false-fire
denominator without ever contributing to its numerator (the anchored fraction falls 27% → 3.6%). 40
independent draws per row, identical generating distribution:

```
  41 answered + 15 anchored (27% anchored)   median floor=0.52356  [0.49897 .. 0.55588]
 100 answered + 15 anchored (13% anchored)   median floor=0.52273  [0.48738 .. 0.54377]
 400 answered + 15 anchored (3.6% anchored)  median floor=0.51799  [0.50844 .. 0.52467]
 CONTROL ratio held: 400 + 146 (27%)         median floor=0.52375  [0.51689 .. 0.53409]
 CONTROL no anchors: 41 + 0                  median floor=0.52356  (identical to 41+15)
 CONTROL no anchors: 400 + 0                 median floor=0.51799  (identical to 400+15)
```

The effect is **real but second-order**: the 27%-anchored regime sits ≈0.006 above the 3.6% one, and
15 anchored samples move nothing at all at either N (the budget `floor(0.05·n_union)` does not cross an
integer). My hypothesis was largely **wrong at these compositions**, and the blind review's item 9
already names the composition question in general. C2's "the anchored-excluded count is recorded in
the row" mostly discharges it. I am recording the measurement so nobody re-derives it.

**MISSING WORDS.** *"…the first 15 **distinct** identity strings in ascending `sha512_hex(identity)`
order, pinned with TWO fixtures: the insertion perturbation, **and a corpus in which one identity
occurs in many chunks, asserting the pool still holds 15 distinct identities**. The row records the
distinct-identity count and the union's anchored/non-anchored split by group."*

### C13 — the self-retrieval match key · **ADMITS-A-WRONG-BUILD**

**Citation check.** Both scope claims check out: R3 says *"fails to retrieve its own chunk in top-k′"*
(chunk-scoped) and §3 says *"excluding the probe's source file"* (file-scoped). ✓ The "two scopes
differ BY DESIGN" reading is correct.

**But its escalation branch is dead on arrival.** C13 hedges: *"If the search `Candidate` does not
expose the row id, that is a search-surface gap to escalate."* Verified at source: `Candidate.key` is
documented as *"The chunk's BARE `uuid5` point id (no `chunk:` record-table prefix), identical to what
the indexer minted via `records.point_id`."* The escalation branch cannot fire. A pin-ready sentence
should not ship a conditional whose condition was already settled — it invites a builder to spend a
day on a fork that does not exist.

**THE WRONG BUILD — the bar is inherited across a change in what it measures.** The ≤20% self-retrieval
drop gate is **pre-registered** (§4 item 3, R3). C13 TIGHTENS the match key to chunk scope. On a
corpus chunked finely — lore indexes summary *and* source chunks per symbol, many chunks per file — a
docstring-derived probe that retrieves a **sibling chunk of its own file** now counts as a DROP where
a file-scoped key would have counted a hit. The measured drop rate rises for a definitional reason, on
a healthy corpus, toward a bar that §4 says means *"the instrument, not the corpus, is suspect"* and
that files a finding. And C13 forecloses the only cheap relief by declaring path matching "NOT
self-retrieval". A builder meeting a 25% drop rate has a bar it cannot pass and a fix it may not use.

**Third door: what if a hit has no point_id?** `HitCapture` gains the field; a build that treats a
missing/None point_id as a non-match silently converts a plumbing failure into a corpus verdict —
drop rate 100%, "the instrument is suspect", and nobody looks at the projection.

**MISSING WORDS.** *"…matched on `Candidate.key` (which IS the bare point_id — verified at source; no
search-surface change is needed). **The run reports the drop rate under BOTH keys — chunk-scoped
(the gate) and file-scoped (a diagnostic) — and R2 publishes the delta**, because the ≤20% bar was
pre-registered against an unspecified key and tightening the key without re-registering the bar
changes what the gate means. A hit whose point_id is absent is a **run-invalidating condition**
(`measurement_failed`, plumbing named in the note), never a non-match. Pinned with a two-chunks-one-
file fixture asserting a sibling chunk is NOT self-retrieval under the gate and IS counted in the
diagnostic."*

### C14 — "O(probes), never O(corpus)" vs the R2 full-pool embed · **ADMITS-A-WRONG-BUILD (measured)**

**Citation check.** *"Neither document states this reconciling sentence"* ✓ — the packet's Scope IN
says *"cost is O(probes), NEVER O(corpus)"* and D2 says *"R2 embeds the full derivable-text pool
once"*. A genuine, unreconciled contradiction.

**THE WRONG BUILD IS THE SENTENCE ITSELF.** C14 rules that *"the curve's ladder extends to pool
size"*, over a selection rule that D1 calls **free at any N**. Measured on this box, 2026-07-25,
Python 3.14.6, no numpy/scipy anywhere in the closure (blind FA3, which I did not re-derive):

```
  choose_cosine_floor at N=50    :     0.314 ms/call
  choose_cosine_floor at N=100   :     0.910 ms/call
  choose_cosine_floor at N=200   :     3.156 ms/call
  choose_cosine_floor at N=400   :    10.929 ms/call
  choose_cosine_floor at N=800   :    42.727 ms/call
  choose_cosine_floor at N=1600  :   161.357 ms/call
  measured exponent alpha = 1.92     (t = c·N^alpha — O(N^2), as the two nested scans in the code imply)

  ONE ladder rung at B=1000:
    N=1600   ->    2.7 minutes
    N=5000   ->    0.4 HOURS
    N=20000  ->    5.7 HOURS
    N=50000  ->   32.9 HOURS
```

A full nested ladder costs ≈1.35× its top rung (the geometric sum of an N² series). So at a
derivable-text pool of 20k chunks, C14's ruled instrument is **~7–8 hours of single-threaded Python
arithmetic**, *after* the full-pool embed pass it also mandates. The blind review already recorded
*"a naive implementation of the ruled instruction does not finish"*; **C14 re-asserts the requirement
and prices nothing**, which is how a recommendation launders a known blocker into a contract.

The three exits (escalate for numpy/scipy; write a sort-based one-pass sweep **proven byte-equal to
`choose_cosine_floor`**; cap the bootstrap's N) are not equivalent and are a **DESIGN** question, not
a builder's — the repo's own routing rule says a property to INVENT does not go to a builder.

**MISSING WORDS.** *"…the curve's ladder extends to pool size **or to the largest rung the measured
per-rung cost allows, whichever is smaller — and the row records BOTH, so an adopted N chosen off a
truncated curve is visible in the receipt rather than inferred.** Before any ladder runs, the runner
measures one `choose_cosine_floor` call at pool size and records the projected total; a projection
above [operator-set bound] is an ESCALATION with the measured number, never a silent cap. **How the
B≥1000 bootstrap is computed is a DESIGN decision escalated with C14, not a builder's choice**: if a
one-pass sweep replaces the per-resample call, it ships with a pin asserting byte-equality with
`choose_cosine_floor` over randomised inputs (the identity-pin discipline, one level up)."*

---

## 3. Grading the package's own SILENT-vs-DETECTABLE ranking

The package ranked its items and asked to be graded on it. Two are mis-ranked in the expensive
direction, which is the kind that costs.

| item | its rank | my grade |
|---|---|---|
| C1 | 1, SILENT-plus-CORROSIVE | **CORRECT**, and under-stated — its own control is blind at small N (measured) |
| C2 | 2, SILENT | **CORRECT** — and the ambiguity is bigger than the bar it feeds (measured) |
| C3 | 3, silent in prod / cheap to guard | **CORRECT** |
| C4 | 4, unlabelled | **UNDER-RANKED** — "smallest passing rung" adopts an N at which a larger rung fails (measured); silent, and it sets 11-ii's entry condition |
| C5 | 5, detectable but late | **CORRECT** — and blind-S5 raises it: the only comparable dataset is already lost |
| C6 | 6, detectable/early/cheap | **CORRECT for the adopt/decline half**; the *classification* half is silent, and the repo has 839-passed receipts to prove it |
| C7 | batch 1 | right to rank first — but its detector is inert in the authorized vehicle (measured) |
| C8 | batch 2, SILENT | **CORRECT** on sampling; its resource half is unranked |
| C9 | batch 3, unlabelled | **BADLY UNDER-RANKED — this is the second SILENT-plus-LICENSING item on the page.** Measured: the sentence's own wording flips `meets_adoption_bar` False → True |
| C10 | batch 4 | **UNDER-RANKED** — the skip predicate omits the bars, so a selection-rule change never re-measures (#107's shape) |
| C11 | batch 5 | correct |
| C12 | batch 6 | correct (my measurement says the composition worry is second-order) |
| C13 | batch 7, SILENT | **CORRECT as to silence**, but its cost is also a LOUD false failure nobody can legally fix |
| C14 | **batch 8 — "cheapest"** | **MIS-RANKED BY SEVEN PLACES.** Its own body says the consequence is "the 11-ii entry condition judged on a broken instrument" — that is neither cheap nor detectable. Measured: 5.7 h/rung at pool 20k. The rank label contradicts the item's own text |

---

## 4. What the FOURTEEN do not cover at all (grading the frame, not the depth)

The fourteen answer fourteen escalations. A caller of this unit would assume more.

**4.1 THE SINGLE-FLIGHT LEASE HAS NO RECOMMENDATION.** §A puts *"ALL the concurrency risk"* in
11-i-a, and the lease is that risk. C6 covers the head mint; nothing covers the lease. The blind
review calls it *"a genuine hole, not a blank"* — §5 forbids clock constants, and a lease with no
expiry **deadlocks permanently when its holder dies** (a container restart mid-measurement is not
exotic; §0.1 records a `lore-lore` recreate failing on this host at 09:13 on 2026-07-25). None of
`test_retry_seam.py`'s instruments cover lease semantics — they cover retry classification. **A
fifteenth recommendation is needed**, and it is a design question (quiescence vs a fencing token vs
holder-liveness), not a builder's.

**4.2 Nothing says what R2's embed pass COSTS or when it aborts.** C14 governs the arithmetic; the
full-pool embed is O(pool) calls against the production TEI endpoint, from a container the operator
authorised for a one-shot. No bound, no abort, no operator-visible pre-flight count.

**4.3 Nothing pins that the two legs' bars still mean what they meant.** blind-S3 (absent ≤ answered
for every probe, by construction, because both come from one k′ capture — the legacy nonsense arm was
independent) and blind-S2 (the self-retrieval drop gate is a selection filter that retains only easy
probes) both change what 5% and 60% measure. C9 and C13 each make S2 *worse* and neither names it.

**4.4 Nothing says what happens if the stability gate never passes.** It is 11-ii's entry condition.
E5 ruled the determinism pin's RED case in advance precisely so nobody improvises; the gate deserves
the same and C4/C2 give it nothing.

**4.5 Nothing pins the `insufficient_corpus` / state SET against D3.** blind-C3/C4 show §7's state set
was specified against a model D3 deleted, and 11-i **writes this field's domain into the schema**. C3
restores one predicate; the closed set itself is unaddressed by any of the fourteen.

---

## 5. The peer diff — what survived as mine alone

I formed my attack on C1–C6 (and, as it happened, C9/C12/C13/C14) before opening
`REPORT-design-blind-11i.md` and `REPORT-scout-11i.md`. Diffing afterwards:

**Corroborated (theirs first, mine adds a measurement):** the ≥98% denominator (blind §7.14 — but
blind names *which samples*; the *which pool* axis in §2.2(b) is mine) · the degenerate-CI trivial pass
(blind S1 — mine adds the demonstration + positive control) · the union's composition setting the 5%
bar's strictness (blind §7.9 — mine adds 40-draw measurements showing it is second-order) · the
bootstrap's cost (blind §7.13 "does not finish" — mine adds α=1.92 and the hours) · the lease hole
(blind §7.3) · chunk-vs-file self-retrieval (blind §7.7, in passing) · in-row probe storage size
(blind §7.5) · committing the jsonl (blind §24 + S5).

**Mine alone, after the diff — nine findings appearing in neither peer report:**
1. **C1's per-run RNG admits ladder-context dependence** (5 distinct intervals / 12 contexts) — ESC-2
   is only-in-sidecar and no peer graded the proposed sentence.
2. **C1's replay control passes on that wrong build**, and is blind at N=50 (20/20 identical
   unseeded).
3. **C2's denominator ambiguity exceeds its own 2% budget** (4.1 pts at N=100).
4. **C4's "smallest passing rung" is not monotone** — measured, adopts N=100 where N=200 fails.
5. **C9's short absent leg** flips `meets_adoption_bar` False→True (0.475 → 0.779).
6. **The absent leg has no `has_verbatim_anchor` rule**, and inheriting the answered leg's flag
   inflates C2's gate.
7. **`loremaster.__file__` is build-invariant inside the image** — C7's detector cannot detect
   (measured across four topologies).
8. **The fourth cause of null git provenance (`dubious ownership`)**, named by neither #131 nor #134.
9. **C10's skip predicate omits the bars/fingerprint/instrument version** — a selection-rule change
   never re-measures.

Plus two smaller ones: **C13's escalation branch is already dead** (`Candidate.key` exposes the
point_id), and **C3's 30–49 pool has no ladder rung**.

---

## 6. Escalations (scope law — nothing dropped)

1. **C14 is not affordable as written.** 5.7 h/rung at pool 20k, ~7–8 h for the ladder, before the
   embed pass. The exit is a DESIGN decision (numpy install vs a proven-equal one-pass sweep vs a
   capped ladder) and must not reach a builder as "make it fast".
2. **The single-flight lease needs a fifteenth recommendation** (§4.1). It is 11-i-a's whole
   concurrency risk and it has no expiry semantics anywhere in R1–R8 or A–E.
3. **C3 (min 30) and C4 (ladder from 50) do not join.** Rule the 30–49 case.
4. **The §B vehicle's provenance receipt is inert as specified** (§1.4). Recommend `LORE_VERSION` +
   image digest, a loud refusal on `unknown`, and — if git provenance is wanted — the case-D gitdir
   mount plus a loud failure on `(None, None)`.
5. **`capture_git_identity`'s silent `(None, None)` is a live production defect, not 11-i's.** Four
   distinct causes, one sentinel, no logging, and the honesty line renders it as absent rather than
   failed. This is #131 still open one level up; I am raising it rather than folding it in.
6. **`scripts/` still has no `testpaths` entry** (§D.1). `TestPredicateParityWithProduction` — the
   `is`-identity pins that are the only thing stopping the survey's predicate drifting from
   production's — has never run in any gate, and neither has the `choose_cosine_floor` dominance suite
   that produced 0.50649. My probes depend on that parity holding and I verified it **by hand this
   session** (`sss.cosine_absence_verdict_fires is ls._cosine_absence_predicate` → True) precisely
   because no gate does.
7. **Two smaller residuals, escalated not buried:** (a) `SurrealStore.scroll` has no server-side limit
   clamp while `hybrid_search` does (`_MAX_HYBRID_K = 1000`) — C8 leans on that asymmetry without
   naming it; verdict: **fine as-is for C8's read, but say so in the contract rather than relying on
   it silently**. (b) C5's `<run-date>-packet11i` directory shape collides with this decision
   package's own `2026-07-24-packet11i`; verdict: **harmless today, but two same-suffixed receipt
   dirs will confuse a future citation — name R2's `<run-date>-11i-r2`**.
8. **C2's denominator ambiguity is a STOP, not a preference.** Repo law: *"if a contract author finds
   itself CHOOSING between two readings of a spec sentence, that is an escalation."* Measured, the two
   readings differ by 4.1 points at N=100 — larger than the entire 2% budget the gate allows. It must
   be ruled before the contract is authored, not chosen inside it.

---

## 7. Probe record — commands and real output

Every command below was run 2026-07-25 from `/home/ejprice/PycharmProjects/lore-pkt11i` at `0ff8868`.
Probe sources live outside the repo and are reproduced here in substance because a scratch path is not
a citable address (archive law).

### 7.1 The #134 measurement

Probe script (mounted into the container at `/probe.sh`):

```sh
/app/.venv/bin/python -c 'import loremaster; print("loremaster.__file__ =", loremaster.__file__)'
echo "LORE_VERSION=${LORE_VERSION}"
ls -la /workspace/.git; cat /workspace/.git 2>/dev/null
git -C /workspace rev-parse HEAD; echo "exit=$?"
/app/.venv/bin/python -c 'from pathlib import Path
from loremaster.index.snapshots import capture_git_identity
print("capture_git_identity =", capture_git_identity(Path("/workspace")))'
```

Invocation (per case; `$P` is the mounted tree):

```
podman run --rm --network=none --userns=keep-id --user "$(id -u):$(id -g)" -e HOME=/home/lore \
  -v "$P":/workspace:ro -v <probe>:/probe.sh:ro localhost/lore:latest /bin/sh /probe.sh
```

```
===== CASE A-worktree  (/home/ejprice/PycharmProjects/lore-pkt11i) =====
loremaster.__file__ = /app/loremaster/loremaster/__init__.py
LORE_VERSION=v0.4-236-g2b69616
-rw-r--r-- 1 ejprice ejprice 70 Jul 24 17:14 /workspace/.git
gitdir: /home/ejprice/PycharmProjects/lore/.git/worktrees/lore-pkt11i
fatal: not a git repository: /home/ejprice/PycharmProjects/lore/.git/worktrees/lore-pkt11i
exit=128
capture_git_identity = (None, None)

===== CASE B-main-checkout  (/home/ejprice/PycharmProjects/lore) =====
loremaster.__file__ = /app/loremaster/loremaster/__init__.py
f3971bdfc54604b021601b2d4ce52e38f9b5b17b
exit=0
capture_git_identity = ('f3971bdfc54604b021601b2d4ce52e38f9b5b17b', 'feat/surreal-unification')

===== CASE C-nogit =====
fatal: not a git repository (or any parent up to mount point /)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
exit=128
capture_git_identity = (None, None)

===== CASE D — + -v /home/ejprice/PycharmProjects/lore/.git:/home/ejprice/PycharmProjects/lore/.git:ro =====
0ff8868b177a442b6c26a25f6033a9d12a76ad99
exit=0
capture_git_identity = ('0ff8868b177a442b6c26a25f6033a9d12a76ad99', 'pkt11i-floor-calibration-dark')
```

The fourth cause, from the same probe run WITHOUT `--userns=keep-id --user`:

```
===== CASE B (no keep-id) =====
fatal: detected dubious ownership in repository at '/workspace'
capture_git_identity = (None, None)
```

Seam identity (image vs worktree), `sed`-extracted span diffed:

```
diff <(image: sed -n '/^def _run_git_rev_parse/,/^# ----/p' snapshots.py) <(worktree: same span)
-> exit 0, 62 lines: IDENTICAL
```

### 7.2 The arithmetic probes

All run as `uv run --project /home/ejprice/PycharmProjects/lore-pkt11i python <probe>.py`, each
printing the provenance block in §0 first. Shared rig:

```python
WT = Path("/home/ejprice/PycharmProjects/lore-pkt11i"); sys.path.insert(0, str(WT / "scripts"))
import search_score_survey as sss; from token_survey import percentile
VS, choose = sss.VerdictSample, sss.choose_cosine_floor

def bootstrap_ci(union, absent, *, b, rng):          # D1's bootstrap, verbatim
    floors = []
    for _ in range(b):
        ru = [union[rng.randrange(len(union))] for _ in range(len(union))]
        ra = [absent[rng.randrange(len(absent))] for _ in range(len(absent))]
        floors.append(choose(ru, ra).floor)
    floors.sort(); return percentile(floors, 5.0), percentile(floors, 95.0), statistics.median(floors)

def agreement(samples, ci_low, ci_high, *, drop_anchored):   # C2's gate, verbatim
    pool = [s for s in samples if not (drop_anchored and s.has_verbatim_anchor)]
    flips = sum(1 for s in pool
                if sss.cosine_absence_verdict_fires(s.max_cosine, ci_low,  s.has_verbatim_anchor)
                != sss.cosine_absence_verdict_fires(s.max_cosine, ci_high, s.has_verbatim_anchor))
    return (1.0 - flips/len(pool)) if pool else 1.0, flips, len(pool)
```

Outputs are reproduced inline in §2.1 (C1, B=300, union N(0.60,0.05)/absent N(0.45,0.05), 400+15
anchored), §2.2 and §2.4 (C2/C4, B=400, pool 800+120 anchored / 800 absent, ladder 50–800), §2.9 (C9,
k=10, k′=30, source-concentration mix stated in situ), §2.12 (C12, 40 draws per row), and §2.14 (C14,
timing, `time.perf_counter`, reps scaled by N).

**Control ledger — every negative result in this report is paired:**

| probe | positive control (shown firing / agreeing) | differently-broken control |
|---|---|---|
| C1 ladder-context | per-N-reseeded build: **1** distinct interval over 12 contexts | fully unseeded build: 3 distinct intervals at N=200 (fails REPLAY, which the wrong build passes) |
| C2 degenerate gate | wide CI (0.40, 0.70) at N=50 → agreement 0.0000, gate FAILS | — |
| C4 monotonicity | subsample denominator IS monotone in this dataset (so the probe is not reporting noise everywhere) | — |
| C9 short leg | unconcentrated mix → the two rules agree to 5 d.p. (0.51051 / 0.000 / False both ways) | — |
| C12 composition | anchor-free rows reproduce the anchored rows exactly at both N (so the ratio row is the only mover) | ratio-held row (400+146) reproduces the 27% regime |
| C14 timing | measured α=1.92 across six N, fitted on the two largest only | — |
| #134 | main checkout returns a real sha+branch | no-`.git` dir fails with a DIFFERENT named message |

**What I could NOT probe, said plainly:** no store, no embedder, no live corpus — so pool size, real
source-concentration, real cosine distributions and the actual degeneracy of the bootstrap are all
open. My probes show what each SENTENCE admits; they do not claim to predict lore's numbers. The one
place that matters most is C9: I demonstrated the mechanism and the direction, and the magnitude on
lore's corpus is R2's to measure.

---

## 8. VERDICT

**CONTRACT INSUFFICIENT** — as a set of pin-ready sentences. Thirteen of fourteen admit a wrong build
that satisfies them verbatim and ships the defect they exist to prevent; the fourteenth (C6) admits a
narrow one that an existing instrument mostly covers. Every item's missing words are written above and
can be pasted; nine of the findings are new to this pass and five carry a demonstrated wrong build.

This is not a verdict against the package. Its diagnoses are largely right — C1, C2, C8, C9 and C13
each identify a real, silent hazard, and C9's own body names the exact failure I then measured coming
through the door its sentence leaves open. The gap is uniform and structural: **the recommendations
were written as diagnoses, and a diagnosis is not an instrument.** They name the hazard, and then
close the door the last debugging session came through — the empty absent leg, the unseeded RNG, the
20k cap — rather than quantifying over the transform's inputs. That is this repo's own quantifier law,
applied to prose instead of tests, and it is why five wrong builds walked straight through.

Three items should not be ruled at all until something else happens: **C14** (escalate the bootstrap's
implementation as a design fork), **C4/C2** (they depend on whether the interval degenerates — S1's
measurement), and **the fifteenth item that does not exist yet** (the lease). The other eleven can be
ruled as soon as the missing words are folded in.
