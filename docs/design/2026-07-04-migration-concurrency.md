# v0.3 → v2 fleet migration — the CONCURRENCY design

**Status:** design, for operator review (plan §6 P8 amendment "v0.3→v2 FLEET
MIGRATION TOOL"; ledger task #11). **Scope:** the open concurrency item only —
_the old v0.3 instance is LIVE and serving agents while the migration runs._ The
no-loss guarantee, the serving-window story, and the failure/rollback story, each
with receipts. **Out of scope** (per the amendment): the DI doc-content import
(DECISIONS.md/GOTCHAS.md → kind-tagged memories) is a separate per-project content
migration; the `lore.yaml` rewrite mechanics and the `start` refuse-and-point guard
are named here only where they gate concurrency.

Every mechanism this design leans on is cited to `file:line` as built. Where a
mechanism does **not** exist yet it is called out in **New machinery required**.

---

## 1. The problem

A live v0.3 deployment (first real target: `lore-demand_intelligence`, slug
`demand_intelligence`) holds the one piece of non-derivable project data: the
memory store. Everything else (code chunks, graph, manifest, fingerprint)
rebuilds from source by design and re-embedding cost is accepted policy. Agents
may be actively `save_memory`-ing **during** the migration window. We must:

- **(a) No-loss:** every memory whose `save_memory` returned before v2 takes over
  is present in v2. "Takes over" defined precisely in §4.
- **(b) Serving story:** a defined experience for agents during the window.
- **(c) Failure/rollback:** at every step, a way back to a serving v0.3 unharmed.
- **(d) Receipts:** counts + spot recalls at every gate.

Design for the worst realistic case: a pre-v0.3.6 old build (memories live only in
Qdrant, no write-through ledger) that keeps taking writes until the last second.

---

## 2. Invariants (what must hold at all times)

1. **I1 — no acknowledged memory is ever lost.** If `save_memory` returned to an
   agent, that memory reaches v2.
2. **I2 — the migration is non-destructive until the operator confirms retire.**
   The old Qdrant memory collection and the v0.3 image pin survive the whole run;
   nothing the migration does can prevent a return to a serving v0.3.
3. **I3 — no duplicate memories.** A memory present in both stores collapses to one
   row (same id), never two.
4. **I4 — receipts before you trust.** No gate is passed on a subagent's "done";
   each gate has a count parity or a live recall.

---

## 3. Load-bearing facts (as built, with citations)

These are the facts the whole design rests on. Each is a live property of the code
on disk today, not an intention.

- **F1 — the ledger is the durable source of truth, written WRITE-THROUGH-FIRST.**
  `save_memory`/`remember` records the SQLite ledger row **before** the volatile
  vector-store write, so a memory survives even if the embed/upsert then fails.
  v0.3: `store.py:239-248`. v2: `local.py:449-461`. _Consequence:_ the instant
  `save_memory` returns, the memory is already in the ledger — this is what makes
  I1 provable (§4).

- **F2 — the ledger is keyed on a deterministic `uuid5` id and upserts.** PK is
  `memory_id` (`ledger.py:36-42`); `record()` is `INSERT … ON CONFLICT(memory_id)
  DO UPDATE` (`ledger.py:150-162`). Recording the same memory twice collapses to
  one row.

- **F3 — THE load-bearing fact: the `uuid5` id is byte-identical across v0.3 and
  v2.** v2 mints ids by reusing v0.3's own derivation verbatim —
  `MemoryStore._refs_stamp` + `MemoryStore._memory_id` (`local.py:437-438`,
  derivation at `store.py:417-436` and `store.py:480-499`). Same `(text, refs)` ⇒
  same id in both versions. _Consequence:_ replaying a v0.3-authored ledger row
  into v2 **overwrites in place** — it can never duplicate (I3), and a replay is
  safe to run any number of times.

- **F4 — replay is membership-by-id, therefore incremental AND idempotent.** v2's
  `restore_from_ledger` skips any row whose id the store already carries
  (`local.py:569-576`); v0.3's `backfill_ledger_from_store` skips any Qdrant point
  already in the ledger (`store.py:334,343`). _Consequence:_ "replay again, catch
  the tail" only embeds the NEW rows — a second catch-up pass is cheap, and **no
  ledger sequence cursor is needed** (see §7, item N4: the amendment's hypothetical
  cursor is unnecessary because id-diffing already makes catch-up incremental).

- **F5 — v2's boot ALREADY replays the ledger.** The server lifespan opens the
  ledger at `<slug>.memory.db` (`server.py:2235`), wires it into the backend
  (`server.py:2288-2298`), and calls `restore_from_ledger()` at boot
  (`server.py:2311-2315`) **inside the ready guard** (`server.py:2316-2322`).
  _Consequence:_ starting a v2 container against the shared ledger **is** the
  replay — there is no separate "replay" program to write for the common path.

- **F6 — `backfill_ledger_from_store` makes the ledger version-agnostic-complete.**
  It scrolls every point in the old Qdrant `lore_<slug>_memory` collection,
  reconstructs text/metadata/refs, recomputes the SAME stamp the id folds in, and
  records it under its existing id (`store.py:307-359`). _Consequence:_ one
  backfill pass against the old collection proves the ledger covers **every stored
  memory**, even ones a pre-v0.3.6 build only ever wrote to Qdrant.

- **F7 — the ledger file is SHARED between the old and new container.** The path is
  `<state-dir>/<slug>.memory.db`, derived from the slug (`config.py:79,108`;
  `server.py:2235`). Both containers bind-mount the same host state dir
  (`~/.local/state/lore`, per the two-container-topology record). _Consequence:_ the
  ledger is the **handoff channel** — v0.3 writes it, v2 reads it, one file, no
  copy step. WAL open (`ledger.py:107-111`, docstring `ledger.py:93-98`) permits
  concurrent readers + the single writer on a **local** FS (satisfied: state dir is
  local disk, not a network mount).

- **F8 — v0.3 (Qdrant) and v2 (Surreal) write disjoint stores.** v0.3 memory =
  Qdrant `lore_<slug>_memory`; v2 memory = the Surreal `memory` table on a
  per-project database. The two share the host (Qdrant pod, Surreal server, state
  dir) but the ONLY store they both touch is the ledger. _Consequence (I2):_ v2
  cannot corrupt v0.3's data — running both at once is safe, and rollback is a
  clean pointer flip.

---

## 4. The no-loss argument (defining "takes over")

**"v2 takes over"** ≝ the instant the project's `.mcp.json` `lore_<slug>` entry is
re-pointed from the v0.3 endpoint to the v2 endpoint (Phase C below) — i.e. the
first moment an agent's session resolves `lore_<slug>` to v2's port.

**Claim (I1):** every memory whose `save_memory` returned before v2 takes over is
present in v2.

**Proof sketch:**
1. By F1, when `save_memory` returned on v0.3, the ledger row was already
   committed (write-through-first, synchronous commit `ledger.py:162`).
2. Before v2 takes over we **stop the v0.3 container** (Phase B). After the stop
   there is no v0.3 process, hence no new `save_memory`, hence the ledger has **no
   writer** — it is frozen.
3. After the freeze we run one `backfill_ledger_from_store` against the still-live
   Qdrant collection (Qdrant is a separate always-up pod, not the v0.3 container),
   catching any memory a **pre-v0.3.6** old build wrote to Qdrant only (F6). On a
   v0.3.6+ old build this is a no-op — the write-through already covered it.
4. v2's final replay (F4/F5) reads the now-frozen, now-complete ledger and covers
   every row by id-diff. Because the ledger cannot grow after step 2, no row can
   escape the replay's snapshot.
5. Therefore every acknowledged memory is in v2 before the endpoint swap. ∎

**Edge case — a save in flight at the exact stop instant:** if the ledger row
committed but the process died before the Qdrant/Surreal upsert, the row is still
in the ledger (F1) → replayed. If the process died before the ledger commit, the
agent's `save_memory` did **not** return success → nothing was acknowledged →
nothing to lose. Use a **graceful** stop (SIGTERM, let the in-flight synchronous
commit finish); the exposure is one un-acknowledged call at worst, never a lost
acknowledged write.

---

## 5. Options considered

| Shape | No-loss? | Outage | Op complexity | Notes / failure modes |
|---|---|---|---|---|
| **A. Declared freeze, boot v2 fresh** | Yes (§4) | **= v2 cold index** (minutes on DI's large tree — the fresh Surreal DB rebuilds all chunks+graph from source before the port binds; SKILL.md port-probe note, `server.py` lifespan). Memory replay itself is trivial. | Lowest | Dead simple, airtight. Outage dominated by the code re-index, NOT the memory work. Fine for a tiny repo (lore: seconds); poor for DI. |
| **B. Dual-write bridge** (agents write both stores during window) | Yes | ~0 | **Highest** | Needs a live v0.3→v2 forwarding shim + split-brain reads (a memory written on one endpoint is invisible on the other until replay). Idempotent ids make the writes safe but the read-consistency + shim code is real new machinery on a soon-retired codebase. Rejected. |
| **C. Ledger-tail catch-up after cutover** | **No by itself** | ~0 | Medium | Swap first, replay the tail after. Violates I1 for the gap between swap and the final replay (a memory written on v0.3 after the swap, if v0.3 kept serving, is lost to v2 until — and unless — a later pass runs). Good as a _component_ (F4), unsafe as the _whole_ story. |
| **D. Pre-warm + brief freeze + catch-tail** (recommended) | Yes (§4) | **seconds** | Medium | Pay the cold index OFFLINE with v0.3 still serving (start v2 on its own port, endpoint NOT swapped). Freeze is then just stop-v0.3 + final-backfill + a cheap v2 restart (delta-reconcile, index persisted) that re-replays the frozen ledger + endpoint swap. Exploits F3/F4/F5/F8. |

**MCP endpoint-swap ordering** (cross-cutting all shapes): the swap is the LAST
data step and is the definition of "takes over" (§4). It must come **after** the
final replay + parity receipt, never before (that is exactly what makes C unsafe on
its own).

---

## 6. Recommendation — Shape D, unified runbook

**Pre-warm v2 online, freeze briefly, restart-to-catch-tail, then swap.** One
runbook covers both a large repo (DI) and a tiny one (on lore the Phase-A pre-warm
is just fast, so the operator may collapse it into the freeze). Near-zero serving
outage; airtight no-loss; clean rollback; no new backend code on the common path.

**Serving story:** agents see **no outage during Phase A** (v0.3 still serves while
v2 cold-indexes on its own port). They see a **brief outage during Phase B** — the
seconds between stopping v0.3 and the `.mcp.json` swap taking effect on their next
tool call/reconnect. A read-only window instead of a brief outage is possible but
needs new machinery (§7 N5) and is **not recommended** — agents tolerate a
seconds-long reconnect, and the target codebase is about to be retired.

### Runbook (each step: what it does · receipt · abort/rollback)

**Phase A — online pre-warm (v0.3 keeps serving; ZERO outage)**

1. **Pre-backfill the ledger** from the old Qdrant collection.
   `backfill_ledger_from_store` against `lore_<slug>_memory` (F6). Reads Qdrant,
   writes the shared ledger; idempotent.
   · **Receipt:** `ledger.count()` == old-collection `count_points()`.
   · **Abort:** none needed — read-only w.r.t. Qdrant; ledger upsert is idempotent.
2. **Upgrade `lore.yaml` additively.** Insert the `surreal:` block (shared server
   `ws://127.0.0.1:18500/rpc`, `namespace: <slug>`, `user_env`/`password_env`;
   `database` defaults to the slug), preserving every existing key; back up the
   prior file beside it (`lore.yaml.pre-v2.bak`).
   · **Receipt:** `LoreConfig.model_validate` passes; `diff` shows ONLY additions;
   backup exists.
   · **Rollback:** restore the backup.
3. **Ensure the v2 image** (build/pull `localhost/lore:latest` if missing). No
   serving impact.
   · **Receipt:** image present.
   · **Rollback:** n/a (v0.3 untouched).
4. **Start v2 on its OWN port, endpoint NOT swapped.** The container boots,
   cold-indexes code+graph into its fresh per-project Surreal DB, and runs its boot
   `restore_from_ledger` (F5) over the ledger-as-of-now. v0.3 keeps serving the
   live endpoint the whole time.
   · **Receipt:** v2 port ACCEPTING (SKILL port-probe / wait-for-bind); boot replay
   count logged; v2 `memory` row-count == `ledger.count()` at this instant.
   · **Rollback:** stop+remove the v2 container; v0.3 and its stores are untouched
   (F8). Nothing lost.

**★ OPERATOR GO/NO-GO CHECKPOINT ★** — review the Phase-A receipts (ledger parity,
`lore.yaml` diff, v2 warm + row-count parity) before entering the freeze. This is
the last point before any outage.

**Phase B — freeze (the ONLY outage; seconds if pre-warmed)**

5. **Gracefully stop the v0.3 container** (SIGTERM). The ledger now has no writer —
   it is frozen (§4 step 2). Qdrant stays up (separate pod).
   · **Receipt:** v0.3 container stopped; its endpoint NOT ACCEPTING.
   · **Rollback:** `start` v0.3 again → back to serving in seconds (I2).
6. **Final catch-up backfill** against the old Qdrant collection (F6) — captures any
   Qdrant-only tail from a pre-v0.3.6 build written since step 1; a no-op on
   v0.3.6+.
   · **Receipt:** backfill returns T (small/zero); `ledger.count()` ==
   old-collection `count_points()`.
   · **Rollback:** restart v0.3 (I2); the ledger is only ever appended-to, never
   mutated, so v0.3 reads it unharmed.
7. **Restart v2 to re-replay the frozen ledger** (`podman restart`). Boot re-runs
   `restore_from_ledger` (F5) and, by F4, embeds ONLY the tail rows written during
   Phase A; the code index is now a cheap delta-reconcile (Surreal persisted from
   step 4), so the port re-binds in seconds — not a second cold build.
   · **Receipt:** v2 port ACCEPTING; replay count == the Phase-A tail; v2 `memory`
   row-count == `ledger.count()`; **spot-recall** 2–3 known memory texts directly
   against v2 → hits.
   · **Rollback:** if v2 fails to re-bind or replay raises (see N1), stop v2, start
   v0.3, done — no swap has happened yet, so agents were only briefly out.

**Phase C — swap + verify (v2 takes over)**

8. **Merge `.mcp.json`** to point `lore_<slug>` at the v2 endpoint (idempotent
   merge, preserves other servers).
   · **Receipt:** `.mcp.json` diff shows only the `lore_<slug>` url/port change.
   · **Rollback:** revert the `.mcp.json` entry to the v0.3 endpoint; start v0.3.
9. **End-to-end recall** through the live v2 MCP endpoint (not just the DB) — the
   final receipt that agents will actually get their memories.
   · **Receipt:** `recall_memory` via the v2 endpoint returns the spot-check hits.
   · **Rollback:** as step 8 (still clean — see the post-swap note below).

**Retire (deferred; a SEPARATE operator-confirmed step after a soak)**

10. After a soak period the operator explicitly confirms retire: delete the old
    Qdrant `lore_<slug>_memory` collection and drop the v0.3 image pin. **This is
    the point of no return** and is never automated.

**Post-swap rollback note (honesty):** rollback is _clean and lossless before step
8_. After the swap, if agents write NEW memories to v2 and we then roll back, those
v2-era rows are in the shared ledger (v2 also write-throughs, F1); on restart v0.3's
own `restore_if_diverged` (`store.py:279-305`) re-absorbs them (its Qdrant count is
now below the ledger count), so they are **not lost** — but the v2 metadata rides
along inertly in v0.3's payload. Treat "extended v2 operation" as the practical
point of no return; keep the swap the last, quickly-reversible step.

### What `migrate` automates vs. what the operator confirms

**Automated by the `lore-deploy migrate` verb:** steps 1 (pre-backfill), 2
(`lore.yaml` upgrade + backup), 3 (image), 4 (pre-warm start on own port), 5
(graceful stop v0.3), 6 (final backfill), 7 (restart + re-replay), 8 (`.mcp.json`
merge), and every count/parity/spot-recall receipt.

**Operator confirms manually:** (i) the **GO/NO-GO checkpoint** after Phase A
before any outage; (ii) the **retire** in step 10 (delete old collection + drop
image pin) after a soak — the only irreversible act; (iii) **reload the Claude
session** to activate the swapped `.mcp.json` (standard project-MCP behavior,
un-automatable — SKILL.md "Activating it in-session").

---

## 7. New machinery required

- **N1 — v2 boot replay is FAIL-CLOSED on an un-embeddable row (robustness gap,
  recommend fixing before the fleet run).** `restore_from_ledger` has no try/except
  around the per-row replay (`local.py:571-576`) and `_embed_document` **raises** on
  a permanent embed failure (`local.py:930-931`); the boot ready guard re-raises
  (`server.py:2316-2322`) → a single un-embeddable ledger row **fails v2 boot**.
  v0.3's equivalent SKIPS-and-continues (`store.py:378-382`). During the freeze a
  transient embedder outage would abort the cutover (rollback is clean, but it
  wastes the window). _Fix options:_ (a) align v2 to v0.3's skip-and-log posture;
  (b) a pre-flight embed dry-run in `migrate` before the freeze. **Cost:** small
  (a: ~5 lines + a test; b: a script pass). Surface to operator as a decision.

- **N2 — a public row-count / health read on `LocalMemoryBackend` for receipts.**
  Only the private `_existing_ids()` (`local.py:786-789`) exists; the migrate
  receipts need a `count()` (a `SELECT count() FROM memory`) or `len(_existing_ids())`.
  **Cost:** trivial (~5 lines + test), or the script issues the raw query.

- **N3 — a migration driver that opens BOTH stores against the SHARED ledger.** A
  `scripts/lore_migrate.py` (invoked by the skill verb) that constructs a
  `QdrantStore` on the old `lore_<slug>_memory` collection (for F6 backfill) and
  drives the v2 container lifecycle (pre-warm start / stop-v0.3 / restart) + the
  `.mcp.json` merge. Pure orchestration — both classes exist. **Cost:** moderate
  (the script + the skill wiring; the amendment already scopes this).

- **N4 — a ledger sequence cursor: NOT required.** The amendment floats one for
  tail catch-up; F4's membership-by-id diffing already makes catch-up incremental,
  so this is explicitly **not built**. (Recorded so it isn't re-raised.)

- **N5 — a v0.3 read-only mode flag: optional, NOT recommended.** Would convert the
  Phase-B outage into a read-only window (gate `save_memory` in the v0.3 MCP server
  while reads keep serving). **Cost:** small-moderate (a flag + a guard on the write
  path) but on a soon-retired codebase; the brief outage is the better trade.

- **N6 — the `lore.yaml` upgrader + `start` refuse-and-point guard** (named in the
  amendment; concurrency-adjacent). Additive `surreal:` block writer preserving all
  project keys + backup; `start` on a version-mismatched deployment (config lacks
  `surreal:` / container runs a pre-v2 pin) refuses with "run migrate first" so no
  verb ever silently starts v2 over an unmigrated state dir. **Cost:** moderate.

---

## 8. Open questions for the operator

1. **N1 fail-closed replay** — fix v2 to skip-and-log like v0.3 (a), add a
   pre-flight embed dry-run (b), or accept the risk (clean rollback, wasted window)?
   Recommend (a)+(b).
2. **"per-project port" for Surreal** — the amendment says the upgrader assigns a
   "per-project port/namespace." As built the Surreal **server is shared** (one
   `lore-surreal` container at `:18500`); per-project isolation is by
   **namespace/database = slug**, not a port (this repo's block has no surreal
   port; only the MCP `server.port` is per-project — DI 9201, lore 9202). Confirm:
   upgrader assigns **namespace/database only**, shared server, no new surreal port?
3. **Serving window** — accept a **seconds-long outage** during Phase B (recommended)
   or invest in the N5 read-only flag for a zero-outage read window?
4. **DI first-run** — run the full Shape-D runbook against `demand_intelligence`
   with me driving the receipts live, or dry-run Phases A + GO/NO-GO first and stop
   before the freeze for a look?
