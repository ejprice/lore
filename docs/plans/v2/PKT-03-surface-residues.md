# PKT-03 — Served-surface + docs-truth residues
size ~0.20 wu · wave A (parallel-safe; operator may fold into wave A or B) · depends: none
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
