# Packet 58 — ruling amendment 2 (sidecar-64, 2026-09-26): the contract's two DECISIONS — (a) `owner=`-only queries over a superseded row; (b) the boot heal's transaction size on a large legacy population

Rules `REPORT-contract-58.md` §DECISIONS 1–2 (contract committed `5a43aeb`; the adversary is running).
Amends `docs/design/2026-09-26-packet58-kickoff-rulings.md` §5 and `…packet58-amendment-1.md` §FORK-C
(the heal). Facts: `_candidate_statement(status=, owner=)` pushes both equality filters into the
statement and the kickoff §5 ruled `status=` EXCLUDES superseded rows; `_render_task_rows` decorates a
superseded row `[superseded → <successor>]`; `_validate_transition` REFUSES every transition on a
superseded row; the F-1 cap accessor `max_reanchor_dependents(k)` is derived off `compose`'s measured
counts; the real legacy population (probe-64's restore of the 2026-08-03 dump): **task 116, finding
324** — so the task heal's worst case at the 65 boot is bounded by 116 rows × 3 statements = 348, under
the 800 WARN and far under the 5000 hard cap.

## (a) — RULING: `owner=` serves a superseded row the caller HOLDS, decorated; `status=` still excludes it

- **Question.** `query owner=<me>` (no `status=`) — is a superseded row the claimant still holds served?
- **Answer: YES, decorated.** `owner=` asks *"what do I hold"* — a fact about the CLAIMANT column, which
  supersession does not touch (the stamp writes `superseded_by`/`updated_at`/provenance only; kickoff
  F2: the claimant string is untouched by everything but the claim CAS and the release edge). The row IS
  held; hiding it would tell a holder they hold nothing while the CAS still records them. `status=`
  asks *"what is in live state s"* — a label supersession FALSIFIES (the stored status is stale by
  construction), which is why §5 excludes superseded rows from every `status=` filter. Two questions,
  two answers, one rule each: **`status=` filters the LIVE state; `owner=`/unfiltered/`get` serve the
  ROW, and the marker names the supersession.** `owner=X status=claimed` therefore EXCLUDES it (the
  `status=` rule wins — AND-combined filters compose by exclusion).
- **The consumer consequence, stated (Leg 1):** a holder cannot `transition` a superseded row it holds
  (refused — the work moved to X'); the marker on its `owner=` listing is the ONLY served signal that
  its held row is dead, so the marker is load-bearing — pinned. A held-and-superseded row stays in the
  holder's `owner=` listing until 57's release/reap verbs land (P57 item 2 — the owner-guarded release;
  that is where "what do I hold" gets a way to let go of a superseded row). Named, not fixed here.
- **Pin it like this:** claim Y (owner = alice), supersede Y → `query owner=alice` serves Y with
  `[superseded → Y']`; `query owner=alice status=claimed` serves nothing; `query owner=alice
  blocked=False` — Y is NOT claimable-partition material (superseded) → excluded (§5's `blocked=False`
  rule); `get Y` serves it decorated; a `transition` by alice → `IllegalTransitionError` naming the
  supersession (existing). Fixture: alice ALSO holds an un-superseded Z (served plain) — the two-row
  discriminator against "exclude everything superseded" AND "serve everything".

## (b) — RULING: the boot heal CHUNKS at the derived cap; it never refuses; each chunk is one transaction; the sweep is idempotent so a chunk boundary is a safe stopping point

- **Question.** `_reanchor_stragglers()` composes ONE transaction; a large legacy population could
  exceed `TXN_STATEMENT_HARD_CAP` (or the WARN). Refuse, batch, or accept?
- **Answer: BATCH — and this is NOT F-1's answer reversed, because the two operations differ in the
  one property that decided F-1.** The supersede is ONE user action whose parts must land together (a
  half-re-anchored supersede is a strand nobody can see — A-174); the heal is a CONVERGENCE SWEEP over
  independent rows that runs at EVERY boot: a straggler left for the next chunk — or the next boot — is
  exactly the state the sweep exists to fix, and the sweep's own idempotence makes any chunk boundary
  a consistent state (each row's rewrite + edge DELETE + RELATE + note ride together INSIDE its chunk;
  rows are never split across chunks). So: stragglers are read once (`WHERE blocked_by CONTAINSANY
  $superseded_ids`, resolved to the chain HEAD per row), partitioned into chunks of
  `max_reanchor_dependents(0)` rows (the SAME derived accessor F-1 uses — one constant, one derivation),
  each chunk `_apply`'d as one transaction in order, `logger.info("task.backfill.stragglers_reanchored",
  extra={"count": N, "chunks": C})` once at the end, and 0 → silent. A boot heal NEVER refuses: a
  refusing heal leaves the fleet stranded forever with a log line nobody reads (the #131 shape), which
  is worse than a slow boot.
- **Cost, named:** the 65 boot heals at most the legacy strand population (≤ 116 task rows today — one
  chunk, no WARN); a later boot after N supersedes heals only the R2 stragglers (rare). The WARN
  threshold can fire only on a chunk sized by the accessor above 800 — the accessor is derived from the
  HARD cap, so a chunk MAY log the WARN; that is the WARN doing its job on a legitimately large sweep,
  not a refusal (F-1's rule).
- **Failure mid-sweep:** a chunk that rolls back (a store fault, a raced supersede on one of its rows —
  the R1 guard's THROW inside the heal's shell) is LOGGED at WARNING with the chunk index and the
  rows, and the sweep CONTINUES with the next chunk; the failed rows are healed at the next boot (the
  sweep is the retry — no hand-rolled loop). The boot itself never fails on a heal fault (fail-OPEN for
  the fleet, LOUD in the log — the backfill's own posture for phantoms).
- **Pin it like this:** seed `cap + 1` raw stragglers (cap from the accessor, K=0) → two transactions
  observed at the `_apply` seam (a spy counts), ALL healed, `count == cap + 1`, `chunks == 2`; second
  boot → 0, silent; inject a fault into chunk 1 of 2 → chunk 1's rows byte-identical, chunk 2's rows
  healed, one WARNING naming chunk 1, the boot completes; next boot heals chunk 1's rows. Real-population
  receipt: run the heal against probe-64's restored 2026-08-03 DB (`LORE_PROD_DUMP_DB`) at 58's
  close-out and paste `count`/`chunks` (the first measurement of the fleet's legacy strand count).
- **Mutation:** pad the shell by one statement → the chunk size moves (the same F-1 mutation, second
  consumer — sharing by mutation of the accessor).

## Riders roll-up

| pin | where | RED when |
|---|---|---|
| `owner=` serves a held superseded row decorated; `owner=+status=` and `blocked=False` exclude it; two-row discriminator | `test_task_claimable_partition_58.py` | exclude-everything; serve-everything; a bare `[claimed]` marker |
| heal chunks at the derived cap, never refuses, `count`/`chunks` logged once, fault in chunk k isolated + WARNING + continue | the boot-heal pins | one giant txn; a refusing heal; a fault that aborts the boot; a hand-rolled retry |
| real-population receipt at 58 close-out | `REPORT-builder-58` / cold audit | a close-out without it (`done-with-deviations`) |
| accessor mutation moves BOTH the supersede cap and the heal chunk | mutation proof (declared from `--collect-only`) | a private chunk constant |

## Discipline
- Store law: §3 (each chunk verified per statement), §5 (no hand-rolled retry — the boot is the retry).
- Packages considered: none (extends `_backfill_blocks_edges`' posture and F-1's accessor).
- No code/tests/store touched; this doc only; no attribution trailer.
