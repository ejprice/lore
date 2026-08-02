# RESUME — D&D rules RAG scoping session (2026-08-01, pre-reboot handoff)

> **⚠ SUPERSEDED 2026-08-02 — this file is history.** Its §2 OPEN items were ruled by the
> slot-in session: option C ruled, wave D (packets 45–54) minted into the INDEX, forks
> 1/2/4/6/9 closed. Current state: the INDEX table + Log (2026-08-02 entry) +
> `docs/design/2026-08-02-dnd-graph-scope-rulings.md`. Kept per the archive law.

**PHASE STATE ONLY.** Process law lives in `CLAUDE.md` (repo root) + `~/.claude/CLAUDE.md`;
spawn protocol in `~/.claude/orchestration/brief-base.md`; store law in
`docs/reference/surrealdb-31-capabilities.md`. Nothing in this file overrides any of those.

**Written at:** `b3ba703` on `feat/surreal-unification`, working tree CLEAN, 2026-08-01.
The operator is rebooting the host; a fresh agent picks up from here.

---

## 0. FIRST ACTIONS AFTER REBOOT (before trusting anything)

1. **The SurrealDB stores auto-start** (systemd/quadlet, `WantedBy=default.target` + linger):
   `lore-surreal` :18500 (PROD) and `spike-surreal` :18000 (TEST). Verify:
   `systemctl --user status lore-surreal spike-surreal`. Recovery recipe if gone:
   `lore_recall("surreal stores systemd")` / capabilities doc §9.
2. **⚠ The `lore-lore` MCP container is NOT restart-durable** — it runs a hand-rolled `/source`
   mount (`MEMORY.md` landmine; pending #165/#166). **Do NOT `lore-deploy start` it** (a normal
   start re-mounts `/source` and re-breaks boot). If it did not survive the reboot, recreate it
   manually per `lore_recall("lore-lore hand-rolled mount")`.
3. A Claude session connects to lore only at session **start** — if `mcp__lore_lore__*` tools are
   unreachable, fix the container first, then `claude --continue`.
4. Once lore is up: `lore_index()` (cheap) — confirm the watched root is
   `/workspace` on `feat/surreal-unification` and freshness is sane before trusting any
   graph/impact answer.

## 1. What this session produced (all committed; nothing in flight)

| Commit | Content |
|---|---|
| `5b243ec` | **`docs/design/2026-08-01-dnd-rules-rag-proposal.md`** — the extend-vs-reuse proposal (options A/B/C, recommendation C, packet sketch, ten forks §9) + three scout reports archived at `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/` (`REPORT-corpus-scout-1.md`, `REPORT-lorearch-scout-1.md`, `REPORT-graph-scout-1.md` — the last carries six verbatim probe instruments in its §7). |
| `b3ba703` | **Capabilities-doc additions** (`docs/reference/surrealdb-31-capabilities.md`): §2 array-index element-path rule + silent-`[]` equality trap · §4 "a traversal never uses a secondary index" + return-shape note · §6.6 items 13–14 · §7 SDK string-id vs int-id-literal row · dated addition-pass note at the bottom. Each claim was verified against the `surrealdb-docs` / `surrealql-tests` tiers first; the check caught the scout's §6.3 "vendor-unwritten" claim being WRONG (int-vs-string ids ARE vendor-documented) — the archived report carries a correction header. |

Earlier, same day, same branch (previous session): `67b4438` —
`docs/design/2026-08-01-multi-user-lore-proposal.md` (principals / tool gating / scoped memory;
its **Part 2 is the lore.yaml tool allowlist**, which answers finding #296).

Lore memories saved (recall with `lore_recall`): *"dnd rag proposal"* → the proposal pointer
(`94c1bda6…`); *"surrealdb array index traversal gotchas"* → the probed engine facts, corrected
version (`c3c941c0…`, supersedes `d610fc9c…`).

## 2. Decision state

**Standing operator decisions (do not re-litigate):** tool allowlist goes in `lore.yaml`
(per-deploy, applied on restart) · the D&D MCP is multi-user · SurrealDB-native graph for
spell→class→level questions · chunker out of scope · capabilities-doc additions (proposal §9
fork 10) — **DONE at `b3ba703`**.

**OPEN — the resuming agent's first substantive step is getting these ruled** (proposal §9,
recommendations attached there; none ruled):
- **Fork 1: A / B / C** — the whole shape. Recommended **C** (wire the extension framework; D&D
  as its first extension; second instance `lore-dnd`; allowlist gates the tool surface).
- Forks 2–9: extension-package home · MCDM duplicate pair · 2014-vs-2024 edition policy ·
  class-node edition scoping · 2014 stat-block scope · edge-only membership vs `classes` array ·
  `ENFORCED` from birth · which generic tools the dnd instance enables.

**If C is ruled:** packet sequence is proposal §5 — (1) allowlist (= multi-user Part 2; also
unblocks packet 39's hosted posture) → (2) extension discovery wiring → (3) **twelfth-seam
DESIGN packet** (ingest entity-fragment — the one invent-a-property item; per the routing rule it
never reaches a builder as "figure out the general form") → (4–6) dnd extension (extractor /
schema+`SpellStore` / domain tools) → (7) deploy `lore-dnd`. Every packet under the standing
process: contract → adversary → build → cold audit.

## 3. Load-bearing technical facts the next agent should NOT re-derive

All cited in the proposal + archived reports; headline only:
- The extension framework (`loremaster/extension.py`, 11 seams) is **complete and unwired** — 0
  production `register_extension` call sites, no config→extension discovery. The ingest
  write-fragment seam **does not exist** in any option (the "twelfth seam").
- Corpus: all three target queries verified from **two independent sources agreeing exactly**
  (987/987 class edges; 21 Druid L4; 14 Druid rituals) — that diff ships as a permanent
  build-time pin. Traps: ritual lives in the Casting-Time VALUE (H1); entity names nest (H7b —
  longest-match-first, `\b` does not fix it); zero links/anchors corpus-wide.
- Graph model: hybrid — `learnable_by` edge (ENFORCED + UNIQUE(in,out) + `source_book` scope
  column) for membership; level/ritual as indexed FIELDS (a traversal never uses a secondary
  index). DDL sketch: archived graph report §5. Re-ingest = purge-by-scope + re-RELATE in ONE
  transaction.
- Store access for domain tools: `SurrealStore` has **no arbitrary-query verb** — a `SpellStore`
  follows the ledger pattern (own connection, `_txn` driver).
- Slug law: hyphens rejected — `dnd`, never `dnd-2024`.

## 4. Unrelated open work (pre-existing; untouched this session)

- **Packet 39 (Google OAuth): build not started** — harness tasks #4 (build), #5 (cold audit),
  #6 (Caddy edge), #7 (operator-side go-live items) are pending; it was BLOCKED on #296, whose
  answer is the multi-user proposal §2 / the allowlist. The allowlist packet, if C is ruled,
  unblocks it. See the INDEX Log entry of 2026-07-31/08-01 for full state.
- **`REPORT-builder-forgery-sites.md` sits un-archived at the repo root** (2026-07-29, packet-39
  era, predates this session). Flagged twice to the operator; not moved because it belongs to a
  wave this session did not own. Needs an owner to `git mv` it into its wave's receipts dir.

## 5. Loose ends owned by the D&D track (deferred WITH decision points, not can-kicks)

1. Graph-probe scripts → lift verbatim from the archived graph report §7 into `scripts/` **when
   the schema packet builds** (they are its natural regression probes). Decision point: packet 5
   of the C sequence.
2. Corpus re-scrape freshness: the corpus is a static scrape (2026-07-31, `content_sha256` +
   manifest validated). A re-scrape re-opens the ingest-idempotency questions the graph report
   §6.1 answers; the `.crawl-state.json` manifest is the change detector.
3. The corpus scout's stated bounds (its report §9): XGtE's 205K subclass file uncounted;
   equipment/glossary entities uncounted; 2014-dialect field completeness unswept. Revisit when
   scope expands past spells.
