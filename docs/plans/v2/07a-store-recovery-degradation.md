# 07a — Store error-honesty: RECOVERY + DEGRADATION (#164, #128; #126/#127) · split from 07
size ~0.20 wu · wave L (parallel-safe) · depends: none hard; 07 recommended first (same seam — avoid concurrent edits to `_txn`/store session code)
law: repo CLAUDE.md store-reference law (**READ `docs/reference/surrealdb-31-capabilities.md`
FIRST**, incl. §0 — the engine is 3.2.1) · "a probe needs a control" · probe-derived
fixtures · DEPLOY: yes

## Why this packet exists
Split from packet 07 (2026-07-22) when #164 and #144 arrived: classification (07) and
recovery/degradation (this) are the two halves of the same error seam, and together they
exceeded the sizing law. This half is what the store DOES after an error is understood.

## Scope IN
- **#164** — a store bounce WEDGES the held SurrealDB connection: the retry seam retries
  the query on the dead socket but never re-establishes the session; only a container
  restart heals it (live receipt: the 3.2.1 migration, 2026-07-22). Teach the seam to
  classify dead-socket/closed-connection as RECONNECT-AND-RETRY — re-bootstrap through
  the existing `bootstrap_session` (never a second connect path; the #120 law), within
  the existing composed budget. Drill receipt: bounce spike-surreal mid-flow, verify
  recovery without a container restart, 20-consecutive. ⚠ The `[VENDOR]` 3.2.1 note names
  a cold-start `Session not found` router-race fix (#308) — probe whether it changes the
  wedge shape before pinning fixtures.
- **#128** — server.py's batched finding resolve/acknowledge: TxnContentionExhaustedError /
  SurrealStoreError on one item must degrade PER-ITEM (the best-effort contract the verbs
  already promise), never kill the whole batch response. Concurrency pin under real
  contention (20-consecutive law).
- **#126 / #127 adjudication**: fix-or-acknowledge-with-named-reopen-trigger, each with a
  written verdict (both are latent-by-design today; the verdict is the deliverable, a fix
  only if the verdict says so). NB #127's seam (`scout.CommandSubscriber._ensure_connection`,
  a bare check-then-set) is ADJACENT to #164's reconnect work — adjudicate them together
  so two sessions don't invent two reconnect policies (ONE IMPLEMENTATION law).

## Scope OUT
- Classification (#118/#119/#144) — packet 07.
- Any retry-budget/jitter change (the #102 seam is CLOSED; reconnect classification rides
  the existing driver, it does not fork it).

## Entry check
Store reference FIRST (repo law), §0 included. `lore_findings` → #164 #128 #126 #127
states; packet 07's landed state (shared files). Probe the dead-socket error shape on
spike-surreal 3.2.1 (bounce it live) BEFORE writing fixtures — commit the transcript.

## Exit
Full gates + cold audit; deploy BOTH; smoke: a live spike-store bounce mid-flow recovers
without a container restart; a contended batch degrades per-item; findings resolved with
receipts; INDEX row + Log.
