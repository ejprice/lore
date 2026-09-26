# Packet 63c — ruling amendment 27 (sidecar-63c-2, 2026-09-26): the fix builder's FORK-1, FORK-2, DV-2

Rules `REPORT-builder-63c-i-a-fix.md` summary + §9. Directive: the lead's Task 27 (this session's lore client
is still down — `Read`/`awk`, said so). The build is under cold audit (`coldaudit-63c-i-a-2`, patch
`b23f3e43`); nothing here changes the patch under audit. Each item: ruled NOW on the merits; LANDS in the
cold audit's fix pass if the audit opens one, else as the first rows of 63c-i-b's contract — a named owner
and a named decision point either way, never "later".

## FORK-1 — Reading B, ruled: `backfilled` is the rows the UPDATE STAMPED, ∀ legs
- Amendment 22 §4's principle (a receipt serves only what was measured) and amendment 24 door #2's D2 are
  not message-leg rulings; they are the CONSUMER LAW applied to one field, and the builder is right that I
  derived it on one leg of a set this wave changed (F-3 made the agent WHERE self-guarding, so its pre-count
  and its WHERE disagree by construction — on the race only, but by construction). The builder was ALSO right
  not to build it: a served-surface change beyond the rulings is exactly its STOP trigger.
- **Pin shape:** one parametrised pin over `_migrate_legs` (the derived leg set the ∀-tables WHERE rider
  already walks): `backfilled == the number of rows whose governed columns CHANGED between a `SELECT *`
  before and after` — a measured byte-diff, not a re-read of the predicate. Memory's WHERE equals its count
  predicate, so it has no gap — and it is not excluded; ∀ means ∀. The message leg's D2 pin becomes one
  value of this parametrisation.
- **Lands:** the audit's fix pass if any (one line, `_rows_stamped` exists), else i-b row 1.

## FORK-2 — ruled: the message leg's preconditions are ONE refusal, in check order; the verb-level refusal precedes
- Amendment 26's rule applies to its own neighbour: a store with un-migrated agents AND a dangling sender
  must not take two round trips. The message leg's preconditions — ORDER guard, dangling senders, half-pairs
  — serve ONE refusal naming every failing check, in that check order (the ORDER remedy first, because it is
  the one the operator must run first: `--table agent`). The verb-level §2.1 refusal is a STORE fact and stays
  a separate, earlier answer (amendment 19 D-1) — the only precedence this packet keeps, because a
  multi-principal store has no leg to run.
- **Pin shape:** the amendment-26 fixture plus un-migrated agents → `refused=True`, all three diagnoses in
  order, byte-inert; control: migrate the agents, re-run → the remaining two. Authored with amendment 26's pin
  by whoever lands that (a19b if live, else i-b).
- **Lands:** the audit's fix pass if any, else i-b. The current behaviour is correct-but-slow (two honest
  refusals), so this is a served-text consolidation, not a data risk.

## DV-2 — ACCEPTABLE for this build; not a second copy of a policy; i-b extracts and classifies
- The policy — *on a registry refusal after a mint THIS call created, delete the keep; if the delete fails,
  append the remedy line to the same exception* — exists at exactly ONE site, because only `_comms_register`
  mints a keep on register. Inline is one implementation with no twin; ONE IMPLEMENTATION forbids the SECOND
  copy, not the first. The builder's two judgments were right: the link-5 gate reddened correctly (a served
  error surface must be driven or classified), and moving the helper to module level would have passed by
  being invisible to the scan, which is the wrong kind of green.
- **What is a smell and gets fixed at i-b:** the PLR0915 pressure that turned a declaration into a one-liner
  says `_comms_register` is over-full. i-b's contract author extracts `_release_the_minted_session_keep` (the
  builder's first draft) and adds its `_RENDER_OUT` entry (`store_backed`, beside the SF-63-1 text it
  extends), so the render gate is the pin; the extraction is proven by mutation (redirect the helper → the
  appended line moves) so routing is sharing. Until then the inline site is classified under
  `_comms_register`'s existing entry, which is honest.

## §W
| # | item | lands | pin |
|---|---|---|---|
| 1 | FORK-1: `backfilled` = measured stamped rows ∀ legs | audit fix pass, else i-b | ∀-legs byte-diff pin over `_migrate_legs` |
| 2 | FORK-2: one message-leg refusal (order → dangling → half-pairs); verb-level first | audit fix pass, else i-b | combined fixture + control |
| 3 | DV-2: inline accepted; helper extracted + `_RENDER_OUT` classified at i-b, mutation-proven | i-b | the link-5 gate |
| — | amendment 26's pin: same owner as row 2 | a19b if live, else i-b | — |

## §E
- None operator-visible. The cold audit's verdict and this ruling meet at the lead; where the audit names the
  same three items, its receipts are the ones to cite.
