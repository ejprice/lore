# REPORT-builder-03b-1-designwave — packet 03b, the deferred-design wave

brief-base v6 read

## SUMMARY BLOCK

- **state:** done-with-deviations. All six items landed (DD-1.a, DD-1.b, DD-3, DD-2.b, DD-4.b,
  cold-R4). Designs were IMPLEMENTED, not re-derived; no ruling was second-guessed.
- **verdict:** every load-bearing pin is mutation-proven. **Two mutations did not discriminate on
  first attempt and exposed two MISSING pins I then wrote** — §4 is the record.
- **gates — RE-RUN under finding #192, with before/after TREE FINGERPRINTS (§3.1):** full suite
  **6581 passed, 0 failed, 17 skipped, 3 xfailed** · `./scripts/typecheck.sh` **0 errors, all three
  members, 149 source files** · `uv run ruff check .` **All checks passed** · skill suite
  **117 passed** · 20-consecutive concurrency **20/20, 14 passed each,
  TOTAL_RUNS_WITH_FAILURES=0**. Fingerprints IDENTICAL before and after every run — these counts
  describe a tree that provably did not move under them.
- **deviations:** G1 an ORACLE change (`_message_fakes.py`) — required by DD-3.c's "mirror `body`
  exactly", done by CALLING the production validator rather than cloning it · G2 the DD-3.d
  descriptions + cold-R4 landed inside `ad8153b` instead of their own commit, because
  `git commit --only` scopes PATHS not HUNKS; disclosed, history NOT rewritten · G3 two committed
  contract call sites gained the required `window_days` kwarg (mechanical collateral)
- **decisions needed:** none. Two items for the ledger, not for me: the `--only` sharp edge belongs
  in #191, and DD-1.c's retention row is the lead's to file (§6 R3).
- **receipt pointers:** §1 the six items · §2 the two live store receipts (DDL apply + ASSERT
  behaviour) · §3 the EXPLAIN receipt with its control · §4 mutation proofs incl. the two that
  failed · §5 deviations · §6 residuals

---

## 1 — The six items

Read first, in order: `docs/plans/v2/03b-deferred-design-rulings.md` (DD-1, DD-2.b, DD-3 including
DD-3.g, DD-4.b) and the store reference's §7 additions. **Nothing was re-derived** — DD-3.g's DDL
shape in particular was written as specified, and I did not re-probe the syntax it settled. I did
verify that what I shipped BEHAVES (§2), which is a different question from re-deriving it.

| item | what shipped | where |
|---|---|---|
| **DD-1.a** | `trace_ts` plain index, `IF NOT EXISTS`, in `_trace_statements` | `1a6010f`, its own deploy-gated commit |
| **DD-1.b** | `WHERE ts > $cutoff` on `trace_aggregates`; `TelemetryConfig.aggregate_window_days` (default 14); the window SERVED on `TraceSummary.window_days` and derived into its prose | `ad8153b` |
| **DD-3** | `MESSAGE_POINTER_MAX_CHARS = 256` (each refs entry / `thread` / `task_id`), `MESSAGE_REFS_MAX_COUNT = 20`, `note` at the BODY cap; ledger teaching reject + store ASSERT backstop; the `refs` description rewritten | `d4e4778` (+ descriptions in `ad8153b`, §5 G2) |
| **DD-2.b** | schema pin: `message.thread` is a required non-`option` `string` | `d4e4778` |
| **DD-4.b** | structural pin: no awaited work after `ledger.drain()` returns | `326846d` |
| **cold-R4** | the `to` description: "writes no message and no delivery — all-or-nothing" | `ad8153b` (§5 G2) |

Three things worth stating because they are choices a reader will otherwise wonder about:

**The pointer bound is ONE constant for a CLASS, not three constants.** `refs` entries, `thread`
and `task_id` are the same kind of thing — an address or a label — and three constants would be
three things to drift. `note` deliberately takes the BODY constant instead, because it is prose
that is read back, not an address.

**NO charset on `thread`.** Settled in DD-3.e and pinned so nobody "hardens" it later: `thread` is
a topic label, it is a bound param at every site, and the surface's own taught `q:<topic>` form
contains a `:` the identity charset forbids — applying that charset would REJECT this packet's own
teaching. The pin asserts the taught form is ACCEPTED, so the reasoning is executable rather than a
comment.

**The windowing changed served SEMANTICS, so the surface says so.** `total`/`by_tool` are now
"calls in the window", and a consumer reading them as lifetime totals would draw the wrong
conclusion from a quiet week. `window_days` travels WITH the numbers, read from config ONCE and
passed into both the query's cutoff and the served model — so the value and the prose describing it
cannot drift apart.

---

## 2 — Live store receipts (TEST store only; `:18500` never touched)

Both on `ws://127.0.0.1:18000`, 3.2.1, throwaway databases.

**(a) The DDL applies, and is idempotent.** The full new message slice applied cleanly and applied
AGAIN cleanly — the re-apply matters because `ensure_ready` runs it on every boot, and the element
row is the one that would raise on a second pass if it lost its `OVERWRITE`.

**(b) The ASSERTs actually fire — behaviour, not an echo diff.** `INFO FOR TABLE` normalises what
it echoes (`refs[*]` comes back as `refs.*`, `option<string>` as `none | string`), so the echo is
not the oracle. Six legs plus three controls:

```
CONTROL legal row                                 ACCEPTED
CONTROL legal refs                                ACCEPTED
CONTROL task_id OMITTED (option, no NONE-guard)   ACCEPTED
over-length ref (257)                             REJECTED
over-count refs (21)                              REJECTED
over-length thread (257)                          REJECTED
over-length task_id (257)                         REJECTED
over-length body (2001) [pre-existing]            REJECTED
```

The three controls are what make the rejections meaningful: a schema that rejected everything would
satisfy the reject legs alone, and the omitted-`task_id` control is the one that proves the
`option<>` ASSERT is genuinely not evaluated on NONE — i.e. that the missing NONE-guard is correct
rather than lucky.

---

## 3 — The EXPLAIN receipt (DD-1.b), with its control

The question: does `WHERE ts > $cutoff` ride the new `trace_ts` index, or is the window only a
render-level fiction?

```
--- WINDOWED (DD-1.b, shipped) ---
Aggregate
  IndexScan {'access': ">d'2026-07-11T15:45:26.048994Z'", 'direction': 'Forward', 'index': 'trace_ts'}

--- UNWINDOWED (the pre-change shape) — the CONTROL ---
Aggregate
  TableScan {'table': 'trace', 'direction': 'Forward'}
```

**The control is the whole point.** The same probe, one conjunct apart, shows the `TableScan` the
window removes — so the `IndexScan` is a real result and not an instrument that reports "index"
for everything. This is also the discriminator for the design's first named wrong build
(render-windowed, scan-unbounded): that build produces the bottom plan while every served number
looks identical.

Regenerating it: apply `generate_ddl(dim=…)` to a throwaway DB and run the aggregate statement with
`EXPLAIN` appended, with and without the `WHERE ts > $cutoff` conjunct. The statements are in
`SurrealStore.trace_aggregates`; nothing depends on a `/tmp` path surviving.

### 3.1 — The tree these numbers describe (finding #192)

A suite count is a claim about a TREE, and in a shared tree with four live agents an unfingerprinted
count is unfalsifiable. My first pass at these gates had exactly that defect — the numbers were
right, but nothing proved the tree was still. Re-run with a fingerprint captured immediately BEFORE
and immediately AFTER each run:

```
BEFORE   HEAD=0a0b38d  STATUS_LINES=0  TRACKED_TREE_MD5=801e9cb9c8cf7c4376f35ca575136594
AFTER    HEAD=0a0b38d  STATUS_LINES=0  TRACKED_TREE_MD5=801e9cb9c8cf7c4376f35ca575136594
```

**Diff: EMPTY, across a 5m36s full-suite run and again across the ~2.5-minute 20-run concurrency
block.** Per-file MD5s of the ten files this wave touched are also identical at both ends (captured
in the run log); they are the diagnosis half — WHICH file moved — while the tracked-tree hash is
the detection half, and only it is complete.

**One refinement I would fold into #192, learned from writing the capture:** a list of
"likely-to-move files" is a NAME LIST, and the forbidden set is unbounded — a sibling editing a
file nobody predicted is invisible to it. So the capture takes `git ls-files -s | md5sum` over the
whole tracked tree alongside the per-file hashes. Detection on the closed set, diagnosis with the
list — the same shape as allowlist-the-safe.

⚠ **Honest bound, because a fingerprint that over-claims is worse than none:** `git ls-files -s`
covers TRACKED files only, so a new UNTRACKED file is caught by `STATUS_LINES` rather than the hash,
and a sibling commit landing mid-run moves HEAD rather than either. All three lines are load-bearing
and none alone is sufficient.

---

## 4 — Mutation proofs, including the two that failed first

`cp -a` content backups of all four production files, restore from content, md5-verified identical
after every proof (`server.py de57fe6b…`, `surreal.py 2bfd445f…`, `surreal_schema.py 71a94f71…`,
`messages.py 097a3331…`).

| # | mutation | result |
|---|---|---|
| **MP-DW1** | delete the `trace_ts` index line | **1 failed** — the schema pin. (First attempt: GREEN. See below.) |
| **MP-DW2** | drop the `WHERE ts > $cutoff` conjunct (render-windowed, scan-unbounded) | **2 failed** — the query-text pin and the out-of-window-row pin |
| **MP-DW3** | freeze the cutoff at a constant (the cached-cutoff build) | **2 failed** — the per-call-cutoff pin and the out-of-window pin |
| **MP-DW4** | flip `message.thread` to `option<string>` | **2 failed** — the spec pin and the emitted-DDL pin |
| **MP-DW5** | delete the ledger's pointer rejects | **4 failed**, all `[real]` and `[fake]` legs of the pointer battery |
| **MP-DW6** | delete the `refs` store ASSERT (the ledger-only build) | **1 failed** — the backstop pin. (First attempt: GREEN. See below.) |
| **MP-DW7** | insert an `await` after the drain stamps | **2 failed** — both DD-4.b legs |

### 4.1 — Two mutations that did not discriminate, and the pins they were missing

**MP-DW1 was GREEN on first attempt: the `trace_ts` index had NO pin at all.** Deleting the
deploy-gated line was invisible. That is defensible-sounding — DD-1.a says outright *"Wrong build
stopped: none by itself"*, because an index changes the PLAN, not the RESULT — but it is exactly
why it needed a STRUCTURAL pin, and DD-1.a's own rider specifies one (parse the `FIELDS` clause,
never substring the statement, since an index NAMED `trace_ts` contains `ts`). I had implemented
the ruling and skipped its rider. Pin written, re-proved RED.

**MP-DW6 was GREEN on first attempt: the store ASSERT backstop had no pin.** Deleting it left every
test passing, because the ledger's teaching reject fires first and no pin looked at the emitted
DDL. This is the "ledger-only build" the design's OWN adversary section names — *"a future writer
bypasses silently; stopped by the schema pins on the ASSERT text"* — and I had not written those
pins. Five added (refs count, the element row including its `OVERWRITE` requirement, `thread`,
`task_id`, `ack_note`), pinning the EMITTED statement per the house idiom rather than the engine's
normalised echo. Re-proved RED.

**The pattern in both is the same and worth naming:** I implemented the RULING and skipped the
RIDER attached to it. A ruling's "and pin it like this" clause is not commentary; in both cases it
was the only thing standing between a correct build and a silently deletable one.

---

## 5 — Deviations

**G1 — I changed the ORACLE (`_message_fakes.py`).** Oracle edits are contract-author + adversary
territory by default. What made this one in-scope: DD-3.c rules "enforce at BOTH layers, **mirroring
`body` exactly**", and the fake mirrors `body`'s reject today — verbatim, message included. So the
fake enforcing the pointer bounds is the ruled shape, not my judgement; leaving it divergent would
have meant every surface pin riding an oracle that permits what production refuses.

**How, and why it matters:** the fake CALLS `MessageLedger._reject_oversize_pointers` /
`_reject_oversize_note` rather than cloning their rules. The fake's body and grade checks ARE clones,
and that pattern is precisely how its `EmptyRecipientSetError` prose drifted from production's
(finding #190) — a divergence no surface pin can see. Routing the new policy through the real
staticmethod makes that class impossible for it. The note bound was extracted from `ack` for the
same reason.

**G2 — the DD-3.d descriptions and cold-R4 landed in `ad8153b` (the windowing commit) instead of
their own.** Cause, stated plainly because it is a reusable lesson: **`git commit --only <paths>`
scopes which PATHS are committed, not which HUNKS** — it commits each named path's full WORKING-TREE
content, so the `git apply --cached` hunk-staging I had done was silently ignored for `server.py`.

**History was NOT rewritten.** Four agents are live in this tree; `--amend` operates on HEAD, and a
sibling committing between my commit and the amend would mean I amend THEIR commit. An
under-described message is a smaller failure than that. `ad8153b` therefore contains more than its
message says, `326846d`'s message records the discrepancy, and the full content is itemised in §1
here. **The `--only` sharp edge belongs in #191** next to the bare-`git commit` hazard: the safe
rule is not "use `--only`", it is "name your paths AND expect the whole path".

**G3 — two committed contract call sites gained a required kwarg.** `trace_aggregates` now demands
`window_days`, so `test_trace_telemetry.py`'s two direct call sites carry it, DERIVED from the
production constant rather than written as 14. Mechanical collateral of a ruled change; no assertion
altered.

---

## 6 — Residuals, individually adjudicated

| id | residual | verdict |
|---|---|---|
| **R1** | The DD-1.b window changes what `TraceSummary` MEANS, and `test_mcp_server.py`'s two committed aggregate pins write fresh rows and read them back. | **VERIFIED GREEN, not assumed** — the design asked for exactly this check. Both pass unchanged, because fresh rows are trivially inside a 14-day window. No amendment needed. |
| **R2** | `TraceSummary` gained a `window_days` field, so the served structured output changed shape. | **ADDITIVE with a default**, so no consumer breaks. Recorded because it IS a served-surface change and the next reader should meet it deliberately: it exists so the numbers can never be read as lifetime totals. |
| **R3** | DD-1.c requires a `lore_findings` row for trace retention (owner packet 06), so the deferral is pinned where the fleet looks rather than only in a design doc. | **NOT FILED BY ME — the lead's.** A builder drive-by on the ledger board is not mine, exactly as with #183 last wave. Flagging it because DD-1.c calls the ledger row part of the ruling, not an optional extra. |
| **R4** | Nothing deletes a trace row. The table grows unbounded until packet 06 lands the sweep. | **DELIBERATE AND RULED** — the rows ARE 06's instrument, and deleting before the curve is read destroys the measurement. DD-1.a+b keep the hot READ flat regardless of row count, which is what makes the deferral affordable. Its escalation trigger (a smoke observing >1,000,000 rows) is the lead's to watch. |
| **R5** | The `refs` description now teaches the bounded pattern, which trips the client-battery re-run trigger (any schema-description change). | **THE LEAD'S CALL, flagged.** One floor-model gate run, already budgeted. I did not run it — the battery is not mine. |
| **R6** | DD-3's adversary names CONTENT DISPLACEMENT: capping refs/thread/task_id/note pushes a payload into the BODY across MULTIPLE messages. | **NAMED, not absorbed.** Volume across messages is a rate concern outside this packet's controls. Recorded so it is met deliberately rather than discovered. |
| **R7** | `message.thread` now carries a length ASSERT it did not have. Existing rows: none — production has no `message` table until this deploy. | **FREE WINDOW USED, and it closes here.** A narrowing ASSERT landed later still could not write-poison (message rows are never UPDATEd), but the window cost nothing to use. |
| **R8** | The `_TraceRecorder`/oracle prose-parity instrument (#190) and the packet-05 items (DD-2.a waiting line, DD-4.c `since=`) are untouched. | **OUT OF SCOPE, ledgered by the lead.** Named so this report cannot be read as "all deferred items closed". |

---

## 7 — What I did NOT do

- **No deploy**, no container touched, `:18500` never opened — the two live probes and every test
  ran against `ws://127.0.0.1:18000` on throwaway databases.
- **No `git stash` / `checkout --` / `reset` / `clean`**, and `git status` was read before every
  commit (#191). No sibling's staged work was adopted.
- **No history rewrite** (§5 G2).
- **I did not re-derive any DD ruling**, and I did not re-probe DD-3.g's settled DDL syntax — I
  verified that what I shipped behaves, which is a different question.
- **I did not build**: trace GC/retention, the `awaiting_answer` waiting line, `since=`/recovery, or
  the oracle prose-parity instrument.
- **I did not file the DD-1.c findings row** (§6 R3) or run the client battery (§6 R5).

---

*Measured 2026-07-25 at commits `1a6010f`..`326846d` on branch `feat/surreal-unification`; the
gates re-run at `0a0b38d` under finding #192 with the fingerprints in §3.1. Every number above was
produced by the command shown beside it, in this session, on a tree proven not to have moved under
it.*
