# REPORT-consultant-opus-1 — branch/diff awareness in the worktree overlay (design consult)

brief-base v7 read
state: done-with-deviations
deviations:
- My spawn brief said "you write no code and no files" and named my final text as the
  deliverable. brief-base v7 §1 overrides that shape explicitly ("if your brief tells you your
  final message is the deliverable, WRITE THE FILE ANYWAY and point at it"), so this report
  exists as the durable address. No other file was written; no git state was touched.
Packages considered: **git CLI** (the diff/merge-base engine) — verdict `replace`, i.e. lore
  never implements a diff: the changed set is enumerated by `git diff --name-only` against the
  merge-base, which is already packet 17's binding constraint (`docs/plans/v2/17-worktree-overlay-design.md`,
  "Binding operator constraints"). What I READ to decide: `loremaster/loremaster/index/snapshots.py::capture_git_identity`
  and `_run_git_rev_parse` (the existing, sanctioned shell-out to git), plus
  `loremaster/loremaster/shellout.py::SANCTIONED_EXEC_MODULES`. **`GitPython` / `pygit2` NOT
  evaluated** — I did not read their APIs, and I am not asserting a limitation: adopting either
  would open a second git-reading path outside the one sanctioned exec seam and needs install
  authorization, so it is an OPERATOR QUESTION (see §C), not a verdict I may render.
decisions-needed:
- E: which of the three options ships in packet 23's v1 (I recommend Option 1).
- C: whether `git merge-base` / `git diff --name-only` extend the existing sanctioned seam
  (`index/snapshots.py`) or justify a reviewed `SANCTIONED_EXEC_MODULES` addition.
- B/§6: branch-vs-branch for refs checked out nowhere — I recommend NEVER; operator owns it.
receipt pointers: §A–§E below; every code claim carries file+symbol.

Dated: written 2026-07-26 against `feat/surreal-unification` @ 6a21fb6. Claims about the code
are true at that sha, not "currently".

---

## Ground truth established (receipts for every factual claim below)

- **`lore_diff` is a SNAPSHOT/temporal diff, not a git-ref diff.** `loremaster/loremaster/diff.py::DiffEngine.diff(since, until)`
  takes `since`/`until` as snapshot ids of the form `snapshot:sn<hex>` and composes added /
  removed / modified files plus `DiffEngine._function_deltas`, with `until=None` meaning the
  live "now" state. Its MCP registration (`loremaster/loremaster/server.py`, tool
  `name="lore_diff"`) says so in words: *"Show what changed between two index SNAPSHOTS."*
- **But its listing already renders git identity.** `AppContext._render_snapshot_rows`
  (server.py) emits `", {git_branch or '?'}@{git_ref[:12]}"` per snapshot row. So a consumer
  already sees BRANCH NAMES inside a `lore_diff` render. This is the concrete
  consumer-confusion hazard in §C — the verb is primed to be misread as branch-aware.
- **Snapshots capture git identity at stamp time** via `loremaster/loremaster/index/snapshots.py::capture_git_identity`
  (fields `git_ref` / `git_branch`, schema'd in `loremaster/loremaster/store/surreal_schema.py`).
- **ONE git reader, by law.** `build_workspace_status` (server.py) reuses `capture_git_identity`
  and its docstring says explicitly "ONE IMPLEMENTATION — never a second git reader here."
- **ONE sanctioned exec seam.** `loremaster/loremaster/shellout.py::SANCTIONED_EXEC_MODULES`
  is a frozenset holding exactly `{"loremaster/loremaster/index/snapshots.py"}`. Every other
  shipped module that so much as *reaches* a spawner is refused by the deploy gate.
- **The tool surface is 15 and pinned exactly.** `loremaster/tests/test_mcp_server.py::_BARE_TOOL_NAMES`
  holds 12 prefixed names; `_ALL_BUILTIN_TOOL_NAMES` adds `lore_claim_task` / `lore_tasks` /
  `lore_comms`, and `TestToolRegistration` asserts `names == _ALL_BUILTIN_TOOL_NAMES`. A 16th
  tool is a deliberate pin bump — packet 17 open question 2 says "prefer no new tool."
- **A "scope to what changed" affordance already has precedent**: `lore_map(changed_since=...)`
  takes a snapshot id and teaches `lore_diff` on a miss (`loremaster/loremaster/map.py::MapChangedSinceError`).
- **The gap is real and live right now**: `git worktree list` at write time shows
  `/home/ejprice/PycharmProjects/lore-pkt42` on `pkt42-prevent-the-leak` — a sibling worktree
  the index cannot see, which is finding #125's exact shape.
- **Finding #125** (`lore_findings action=get id_or_number=125`, acknowledged): both #102-wave
  auditors fell back to grep for every structure question in a sibling worktree.

Tool honesty (brief-base §4): lore_search / lore_get_symbol / lore_findings answered the
"where is the diff tool / what is DESIGN-LAW §1 / what is #125" questions. I fell back to
**grep** for three things and say so: the exact-set tool pin (a test-file constant, not a
symbol), `SANCTIONED_EXEC_MODULES`'s membership, and the `git_branch` render site — all
non-symbol textual seams, i.e. case (b)/(c) of the repo's sanctioned fallback list. No
friction filed: these are the documented cases where grep is the honest instrument, not a
lore weakness.

---

## A. CONSUMER — what I actually ask, and where I actually go

Honest self-report, separated per brief-base §5: this is what I **observe myself doing** in
worktree/branch sessions, not a theory about myself.

| Question I actually ask | Tool I reach for TODAY | Would I call lore? |
|---|---|---|
| "What files have I changed?" | `git status --porcelain` / `git diff --name-only <base>` | **ROUTE AROUND.** Instant, exact, already trusted. |
| "What does my change look like in file X?" | `git diff` | **ROUTE AROUND.** Textual diff is git's job. |
| "Who calls the function I just changed — across the WHOLE repo, including files I did NOT touch?" | **grep** (this is #125's receipt, verbatim) | **CALL.** Git structurally cannot answer it. |
| "Which tests cover my changed set?" | filename guessing (`test_<module>.py`) + grep | **CALL.** `lore_impact`'s covering-tests join already answers it per-symbol; over a SET is a fan-out I do by hand. |
| "What did the deleted code do, and who used it?" (the repo's removed-behavior inventory law) | `git show` for the text, grep for the users | **SPLIT:** git for the text, lore for the users. |
| "Does a helper for this already exist?" | `lore_search` | **CALL** — already do; not branch-scoped. |
| "Is my branch behind base? what moved under me?" | `git log` / `git merge-base` | **ROUTE AROUND.** |

**The line, stated once, because it is the whole design:** *git answers "what did I change";
git cannot answer "what does what I changed TOUCH."* Every question I would route to lore sits
on the far side of that line. Every question git already answers, I will route around — and a
lore re-serve of one is **worse than nothing**, because it costs a tool call and an
index-staleness risk to obtain a lower-confidence copy of an answer I already trust
completely. That is a DESIGN-LAW §1.7 trust debit for zero gain.

**What a lore diff surface must serve for me to prefer it:**
1. It answers a question git structurally cannot (graph, not text).
2. It names the exact refs compared AND the index state it derived from, so I can judge
   staleness myself instead of guessing.
3. It does the fan-out: ONE call over the whole changed set, not N calls I have to remember
   to make per symbol. The fan-out is the actual labour; per-symbol `lore_impact` already
   exists and I still don't run it 40 times.

---

## B. DESIGNER — should lore serve this, and what exactly

**Yes, but only the graph half.** The packages-over-hand-rolling law settles the other half
before the design starts: git IS the diff engine, and packet 17's overlay **already shells out
to `git diff --name-only` against the merge-base as its INPUT** (17, Binding operator
constraints). So the changed set is computed either way. The marginal cost of serving
*graph* answers over a set you already hold is near zero; the marginal cost of re-serving
*textual* diff is a permanent second implementation of something git does better.

| # | Candidate surface | Disposition | Reason |
|---|---|---|---|
| 1 | **Textual-diff re-serve** | **NEVER** | git does it; I would route around it (§A rows 1–2); and it is copy #2 of a diff engine (ONE IMPLEMENTATION + packages law). |
| 2 | **Changed-symbol inventory** (symbols added / removed / modified in the changed set) | **v1** | Nearly free: the overlay chunks and embeds exactly those files, the base index holds the pre-change symbol set for the same paths, so it is a set-difference over data already in hand. And the machinery has a working precedent — `DiffEngine._function_deltas` already computes function-level deltas between two states. This is the answer `git diff` gives only as text I must parse. |
| 3 | **Impact / blast-radius of the changed set** | **v1 in its BASE-SERVED form (with the ruled caveat); delta-derived form is v2** | Packet 17 is binding: "impact/dead_code stay base-served with an EXPLICIT caveat … scoped delta-derivation … is the designed-for v2, not v1." The cheap v1 half — fan out base-served `lore_impact` over the changed set, label every result — is *authorised by that same clause*, and it is the single highest-value item in §A. |
| 4 | **Covering tests for the delta** | **v1** | Same base-served join, and its error direction is benign: base-served covering tests UNDER-report the tests I just wrote (which I know about) and correctly report the pre-existing tests that cover what I touched (which is the answer I want). Cheap, high signal, low over-claim risk. |
| 5 | **Semantic search scoped to "my changes"** | **v1, essentially free** | It IS the overlay's own tier — scoping search to it is a filter, not a feature. Precedent for the shape exists: `lore_map(changed_since=<snapshot id>)`. |
| 6 | **Branch-vs-branch for refs checked out NOWHERE** | **NEVER (or a far-future packet with its own ruling)** | It requires materialising a tree lore does not watch (a `git worktree add`, or reading blobs out of the object database) — full-tree-shaped work for a ref nobody is sitting in, against the spirit of the delta-only ban. And it is the question I ask least; when I do ask it, `git diff a..b --stat` suffices. If wave-O experience demands it, it is a new packet, not a v1 stretch. |

---

## C. SURFACE — where it lives

**Do NOT grow `lore_diff`.** Overloading one verb with two diff domains is a trust hazard, and
here it is a *primed* one: `lore_diff`'s snapshot listing already prints
`{git_branch}@{git_ref[:12]}` per row (`AppContext._render_snapshot_rows`), so an agent who
sees branch names in a `lore_diff` render can reasonably conclude the verb diffs branches. It
does not — it diffs `snapshot:sn<hex>` generations (`DiffEngine.diff`). Adding a git-ref mode
would make `since=` polymorphic across a snapshot id, a branch name and a ref, and a
polymorphic id space where one form silently means something else is precisely the
confident-wrong that DESIGN-LAW §1.3/§1.7 says costs authority for the whole session.

**Preferred surface: no new tool, no new verb.** The answers ride the EXISTING tools, scoped
by the overlay view that packet 17 open questions 1–2 must introduce anyway:
- **The changed-symbol inventory is part of the overlay REGISTRATION render.** Registration
  already computes the merge-base changed set; returning it once, at registration, with ref
  identity in the header, is zero marginal cost and zero new surface. It is also the right
  ergonomics: I get the inventory at the moment I opt in, without having to know to ask.
- **Search / impact / covering-tests take a SCOPE, not a new tool** (e.g. a `scope="changed"`
  or the view addressing chosen for Q2). This keeps `_BARE_TOOL_NAMES` at 12 and
  `_ALL_BUILTIN_TOOL_NAMES` at 15 — no exact-set pin bump, honouring Q2's "prefer no new tool."

**A constraint the brief did not name, and packet 23 must:** `loremaster/loremaster/shellout.py`
sanctions exactly ONE module to spawn a process — `loremaster/loremaster/index/snapshots.py`.
`git merge-base` and `git diff --name-only` therefore live in that seam (beside
`capture_git_identity` / `_run_git_rev_parse`), or the addition of an overlay module to
`SANCTIONED_EXEC_MODULES` is a deliberate, reviewed edit with the operator's knowledge. The
good news: the derived BINARY set does not move — `git` is already in it — so the image
contract is unchanged. The ONE IMPLEMENTATION law applies too: `build_workspace_status`
already reuses `capture_git_identity` rather than reading git a second time, and the overlay
must join that seam rather than fork it.

---

## D. TRUST — the honesty requirements

1. **Ref identity in every render, and it is THREE values, not two:** the worktree path, its
   branch + HEAD sha, AND **the merge-base sha the changed set was computed against**. Two of
   three is a lie by omission the moment anyone rebases — which is packet 17 open question 4
   ("what happens to an overlay whose base moved") wearing its consumer-facing clothes.
2. **Committed vs uncommitted is distinguished PER FILE**, because the two have different
   lifetimes: an uncommitted change evaporates on a `git checkout`, a committed one does not.
   An agent trusting a symbol that exists only in a dirty working tree must be told that,
   or it will cite it in a report a stranger cannot resolve.
3. **Staleness is rendered, not assumed.** The changed set is enumerated at registration; the
   working tree moves on every save. Every delta-scoped answer carries the age of the
   enumeration. `lore_read`'s existing visible STALE notice is the house convention to follow.
4. **The over-claim hazard, named exactly:** base-derived impact over an overlay-changed symbol
   IS the confident-wrong case. The caveat must name WHAT is unverified with a NUMBER, per
   packet 17 open question 6 and DESIGN-LAW §1.3 — e.g. *"consumers listed come from the BASE
   index at `<sha>`; **N** files in your changed set are not graph-analysed, so a consumer you
   wrote in this worktree is invisible here."* A caveat with an unnamed quantity is decoration,
   and the repo has already paid for that lesson ("A DIAGNOSIS IS NOT AN INSTRUMENT").
5. **Hostile fixtures are already binding** (packet 23 invariants) and apply doubly here: the
   render interpolates a worktree-supplied branch name and path — newlines, a row-shaped
   forgery line, and backtick runs, per repo law.
6. **The honesty FLOOR: refuse, never serve empty.** If git is unavailable, or `merge-base`
   fails, or the worktree is not a git checkout, the surface REFUSES loudly. An empty changed
   set and a failed enumeration are indistinguishable to the consumer, and #131 was exactly
   that: a swallowed `OSError` becoming a silent `None` that shipped for three months
   (`loremaster/loremaster/shellout.py` module docstring).
7. **Corollary for the graph answers:** never render a base-served consumer list for a changed
   symbol *without* the caveat attached to that same render. Caveats ship WITH verdicts
   (DESIGN-LAW §1.3), not in a preamble the consumer may not receive — a retrieved render
   arrives without its header.

---

## E. VERDICT — for the operator to rule

**Option 1 (PREFERRED) — "graph over the delta; git keeps the text."** v1 ships: the
changed-symbol inventory inside the overlay registration render; search scoped to the changed
set; base-served impact and covering-tests fanned out over the changed set behind packet 17's
ruled, NUMBER-BEARING caveat. No textual diff, no 16th tool, no change to `lore_diff`'s
snapshot semantics. Scoped delta-derived impact stays the v2 packet 17 already designed for.

**Option 2 (minimal) — overlay exactly as ruled, no delta-scoped renders.** Cheapest and
lowest-risk, but it leaves the precise question #125 was filed about — *what does my
uncommitted work touch?* — answered only if the agent thinks to ask `lore_impact` per symbol,
which §A says I demonstrably do not.

**Option 3 (maximal) — a git-ref mode on `lore_diff` plus branch-vs-branch.** I recommend
against it: it rebuilds git, overloads a verb whose id space is already snapshot-shaped and
whose render already shows branch names, and requires materialising trees nobody is working in.

I recommend **Option 1**, and the one-line reason is a consumer fact rather than a design
preference: *I will route around any lore surface that re-serves `git diff`, and I will call —
every time — a surface that tells me which callers and which tests my changed set touches,
because that is the question I currently answer with grep.* Closing that one gap is the whole
value of #125; everything else on the candidate list is either free (it falls out of the
overlay) or a liability (it competes with git).
