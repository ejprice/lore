# 09 — Served-surface + docs-truth residues (formerly PKT-03)
size ~0.20 wu → RE-SIZE AT KICKOFF (4 findings added by the 2026-07-26 sweep; the sizing
law's ≥0.30 split clause applies) · wave L (parallel-safe; re-waved 2026-07-14) · depends:
none · #92 supersedes the #34/#90 chain this file predates
law: DESIGN-LAW §1 (client law), §2 (map semantics — read before touching map renders)

## Mission
Close the small open accounting/affordance findings and the stale-docs residue in one
hygiene pass. All are confirmed-filed, none has a home elsewhere in the packet set.

## Scope IN (each item: fix red-first, resolve the finding with a note)
- **#84 + #85** — the PLAIN-bare `lore_get_symbol` miss arm lacks the suffix knowledge
  the dotted-wrong arm has; the two miss texts can read as contradicting. Give both
  arms the same teach quality (client law: misses teach a decision tree).
- **#86** — off-by-one in the at-cap visibility clause ("5 of 13" while 4 serve).
- **#88** (external review, 2026-07-10) — exact-symbol miss on a plausible-but-wrong
  method of an already-RESOLVED class suggests unrelated modules instead of listing
  nearest methods on that class (`SearchPipeline.search`, `Indexer.apply` repros).
- **#64** — lore_read nested-path teach gap.
- **#80** — lore_map mandatory-tail latent edge.
- **#82** — 10k suffix-bound growth tripwire (implement the tripwire it names).
- **#34** — promote the shared render-sanitiser seam to a public module
  (`loremaster.search._sanitise_line` today; three consumers: search, diff,
  findings-detail — repo CLAUDE.md names this promotion as pending). Hostile fixtures
  mandatory (newlines + row-shaped forgery + backtick runs).
- **#197** (slotted 2026-07-26) — `capture_git_identity` swallows failure into a silent
  `(None, None)`: FOUR indistinguishable causes (#131's shape), live in production today.
  Classify, log loud, serve honest absence.
- **#208** (slotted 2026-07-26) — XML chunk line spans are element-relative BY DESIGN but
  served through the same `file:line` citation format as real offsets — an honest local
  decision became a misleading served byte (trust doctrine). Serve real offsets or label
  the span honestly; packets 25/26 (Odoo XML at scale) inherit whichever is ruled.
- **#230** (slotted 2026-07-26) — SIX unfailable isinstance-on-raises assertions remain
  repo-wide; in test_store_read.py the hollow line is the test's ONLY assertion. Replace
  each with the property it claimed (`7379b48` is the pattern), both-ways mutation-proven
  per #229.
- **#231** (slotted 2026-07-26) — the #210 anchored-pattern gate's allowlist is keyed on
  the pattern NAME, so exempting one legitimate call site blinds EVERY site using that
  pattern. Re-key the exemption on (pattern, site).
- **#244** (slotted 2026-07-27; priority LOWERED by its own ack note — #246's zero-on-start
  mooted the reaper rationale) — 23 hand-rolled clones of `unique_database()` across 22 test
  modules: 22 drop the pid, one FAKES it with a MAC-derived constant. Plain ONE-IMPLEMENTATION
  debt now: collapse onto the harness mint, PROVE SHARING BY MUTATION, and render a PER-SITE
  verdict (reuse vs deliberate-divergence-with-reason) — do not assume all 23 are accidents.
- **Docs truth pass:** README stale "still on Qdrant … until P7" prose (~L167) +
  historical mentions refresh; adopt the external review's recommended positioning
  language (operator approves wording); annotate docs/design/2026-07-05-p13 stale
  mention (:113) if finding #12 is still open at boot.

## Scope OUT
- D4 `score`→`fusion_rank` rename — ONLY if the operator approves pool item 8; else skip.
- Anything touching map/impact semantics beyond render truthfulness (DESIGN-LAW §2).

## Entry check
`lore_findings status=open` — confirm each listed finding is still open (#12 may have
been consumed; skip any already resolved, note it in the Log).

## Exit
Scoped tests + gates; cold audit (touches served renders); deploy BOTH; each finding
resolved with a receipt; INDEX row + Log.
