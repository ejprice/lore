# REPORT — consultant-sonnet-1

`brief-base v7 read`. state: **done**. deviations: brief said "final text only, no
files" — brief-base v7 §1 overrides that ("if your brief tells you your final message
is the deliverable, WRITE THE FILE ANYWAY") after the idle-gate flagged the report's
absence; writing it now as a deviation, not a silent skip.
Packages considered: none — no mechanism specified (this is a design-opinion consult,
not a build).
decisions-needed: the operator ruling on §E below (branch/diff awareness scope: v1
changed-symbol field vs defer to v2).
receipt pointers: full answer in the "Body" section below; citations inline
(`17-worktree-overlay-design.md`, `23-worktree-overlay-build.md`, finding #125,
`DESIGN-LAW.md` §1, `loremaster/loremaster/diff.py`).

## Body — the design consult answer (verbatim, sent to the lead)

**A. CONSUMER.** Working a feature branch/worktree, the questions I actually ask, and
what I reach for:

1. "What have I changed vs base so far?" (`git diff --stat` / `--name-only` against
   merge-base) — **git, always.** Byte-exact, zero latency, zero staleness. A lore
   surface re-serving this line-diff adds a hop with no informational gain and a new
   staleness risk git-native doesn't have.
2. "What exactly changed inside this file/hunk?" (`git diff <path>`, `git show`) —
   **git.** Same reasoning; this is the textbook packages-over-hand-rolling case — git
   *is* the diff engine.
3. "What breaks downstream if I ship this?" — **not a git question.** I currently loop
   grep/Explore, or `lore_impact` per symbol when available. This is where I'd want a
   lore surface — but scoped to my *whole delta*, not one symbol at a time.
4. "What tests cover what I touched?" — same bucket as #3, currently manual per-symbol.
5. "Is my change consistent with how sibling code does this?" — semantic search,
   genuinely lore's job, not git's.
6. "What's on a branch not checked out anywhere?" — `git log a..b` / `gh pr diff`,
   after a fetch. Not a lore question at all.

For #1/#2/#6, I would **route around** any lore diff surface back to `git diff` — it
would have to beat byte-exact-and-instant to win, and nothing beats that. For #3/#4,
I'd call a lore surface **only if it batches over my whole changed set in one call** —
collapsing N manual per-symbol `lore_impact` calls into one "impact of everything I
touched" answer is the one thing that would make me prefer it over doing the loop
myself.

**B. DESIGNER.** Candidates, dispositioned:
1. **Textual-diff re-serve** — never. Git already does this perfectly; re-serving
   loses to git on every axis and adds a trust surface (staleness) with zero gain.
2. **Changed-symbol inventory** (which functions/classes changed, at symbol
   granularity, over the merge-base changed-file list) — **v1.** Packet 17 already
   computes this exact input as the overlay's own enumeration mechanism —
   `git diff --name-only` against merge-base, chunked to symbol granularity for the
   overlay tier (`17-worktree-overlay-design.md:14-15`). Rendering "which symbols in
   my delta changed" is a re-projection of data the overlay resides on anyway, not a
   new mechanism.
3. **Impact/blast-radius of the changed set** — packet 17 already ruled this **v2, not
   v1**: "impact/dead_code stay base-served with an EXPLICIT caveat... scoped
   delta-derivation... is the designed-for v2" (`17-worktree-overlay-design.md:22-24`,
   mirrored `23-worktree-overlay-build.md:16-17,27`). Cite the ruling, don't re-decide
   it.
4. **Covering tests for the delta** — rides the same impact/covering-tests join
   (`DESIGN-LAW.md:39-40`), so it inherits #3's v2 disposition.
5. **Semantic search scoped to "my changes"** — effectively free today: `lore_search`
   already takes an exact `path` filter, so this is calling it per changed file, not a
   new capability. Thin v1 sugar at most, not essential.
6. **Branch-vs-branch for refs not checked out anywhere** — never, for lore or
   arguably git. It's outside the overlay's model entirely (one live worktree delta,
   not arbitrary refs) and outside scope — plain `git diff refA...refB` after a fetch
   already answers it.

**C. SURFACE.** Growing `lore_diff` to also mean "ref A vs ref B" would overload one
verb with two **different identity spaces**: today `diff(since, until)` is keyed on
*snapshot ids* (`"snapshot:sn<hex>"`, confirmed `loremaster/loremaster/diff.py:707-768`,
raising `SnapshotNotFoundError` from `_parse_snapshot_id` when the id isn't a recorded
snapshot). A git ref is not a snapshot id. Notably, `lore_diff` *already* produces
function-level `function_deltas` — but only between two things the index actually
recorded, never between two git refs. Making the same verb sometimes mean "temporal
index diff" and sometimes "structural git diff" is exactly the client-law hazard: the
consumer has to guess which universe its argument lives in before calling
(`DESIGN-LAW.md:9-30`, source `docs/design/2026-07-06-client-needs-consult.md:449-473`).
That's a **no**. A new 16th tool also cuts against packet 17's own stated preference
("prefer no new tool," `17-worktree-overlay-design.md:32-33`) and the exact-set
tool-count pin it references. The right home: a **field on the existing worktree-view
/status render** — the same surface finding #125's candidate (c) already ships on
(watched-path + branch, per packet 01) — carrying the changed-symbol inventory
alongside it. Zero new tools, reuses data the overlay already computed.

**D. TRUST.** Every such render must carry: the merge-base **commit sha** (branch names
move), the worktree path, whether the enumeration is committed-only or includes
working-tree/staged edits (packet 17 says uncommitted is captured — the render must say
so per-response, not just in the design doc, per `DESIGN-LAW.md` clause 5), a staleness
flag mirroring `lore_read`'s STALE notice (the overlay's own reconcile lag), and —
critically — it must **not** imply impact/coverage for the delta in v1: packet 17 keeps
those base-served-with-caveat, so a render that looks like "these are all the consumers
of your delta" over-claims exactly what clause 3/7 (the trust ruling) forbids.

**E. VERDICT.** Recommend: ship a **v1 changed-symbol-inventory field on the existing
worktree-view render** (no new tool, no `lore_diff` overload), carrying ref-sha + path +
staleness + committed-vs-uncommitted disclosure, scoped strictly to the overlay's
already-computed merge-base changed set — and leave impact/covering-tests/
branch-vs-branch exactly where packet 17 already put them (v2/never). Alternative:
defer entirely and let wave-O experience decide whether the batched-impact-over-delta
question (B.3) comes up often enough to pull v2 forward. Operator's call on timing; I
don't think either needs re-litigating packet 17's existing rulings.

## Sources cited (durable addresses)
- `docs/plans/v2/17-worktree-overlay-design.md:14-15,22-24,32-33`
- `docs/plans/v2/23-worktree-overlay-build.md:16-17,27`
- `lore_findings` id/number 125 (worktree auditors fell back to grep; candidate (c))
- `docs/plans/v2/DESIGN-LAW.md:9-30` (source `docs/design/2026-07-06-client-needs-consult.md:449-473,490-495`)
- `loremaster/loremaster/diff.py:707-768` (`SurrealManifest.diff`), `DiffResult` class
  docstring (symbol lookup, `loremaster/loremaster/diff.py:270-308`)
