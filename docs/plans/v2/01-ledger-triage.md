# 01 — Ledger triage + the lore_index identity line (FIRST work packet) (formerly PKT-29)
size ~0.15 wu · pre-wave (runs before packet 02) · depends: none
law: repo CLAUDE.md sweep discipline ("all remaining hits are X" is banned — every row gets
an individual verdict) · DEPLOY: yes (one small code commit)

## Mission
Make the ledger tell the truth before the local-first plan executes on it, and ship the
zero-cost #125 honesty line. Replaces the retired "wave-A boot duty". Several rows the
plan treats as open bugs are already fixed; several routed destinations changed in the
2026-07-14 re-sequence.

## Scope IN
1. **Stale-row resolves, with receipts** (cite the INDEX Log line + a live smoke where
   cheap): #97 #98 #99 #107 (fixed + deployed 2026-07-13, image b0fce6904fc5);
   #34 + #90 resolve-as-superseded (#92 is the live successor); #112 resolve-as-documented
   (negative result, quadlet knob does not exist); #106 dedupe into #124 (canonical row,
   stays acknowledged-watch).
2. **Dead task rows**: close/supersede the #93 fix task (premise FALSE per #119; #93 itself
   resolved by 93a9aab) and the SMOKE-PKT06 rows (s1/s2/s3 — smoke artifacts, not work).
3. **Routing table applied** (operator-approved 2026-07-14) — every open/acknowledged
   finding acknowledged with a note naming its destination packet, individually:

   | findings | destination |
   |---|---|
   | #14 #16 #42 #44 #47 | resolve here — process law already covers; receipt per row |
   | #21 #29 #35 #48 | individual verdicts here (largely delivered by map/impact/C0-verbs/reference-doc; residue → packet 28 or 05) |
   | #22 + #55(ack) | mint the investigation row (fresh-session ToolSearch failure; pool item 14) |
   | #49 | present pool item 5 for operator ruling (REC: ACCEPT) |
   | #73 | pool item 20 (eval-fixture maintenance; decision point = next eval run) |
   | #111 | pool item 21 (typed conflict check on surrealdb-py 3.0.0) |
   | #100 #101 #103 #104 | packet 02 |
   | #105 | packet 04 |
   | #89 #121 | packet 05 |
   | #118 #119 #128 (+#126 #127 adjudication) | packet 07 |
   | #24 | packet 08 (rescoped) |
   | #15 #64 #80(ack) #82 #84 #85 #86 #88 #92 | packet 09 |
   | #83(ack) #87 | packets 10/11 |
   | #10 #11 #27 | packets 12/13 |
   | #26 #28 #72 | packet 14; #12 → packet 15 |
   | #109 #110 #113 #114 #116 #117 | packet 16 |
   | #13 | packet 19 |
   | #125 | packet 17 design → packet 23 build; honesty line ships HERE |
   | #3(ack) #20 #37 #40 #41 | packet 28 |
   | #124(ack) | watch (observability support via packet 16/#109) |

4. **The #125 honesty line (ONE small code commit, own concern):** `lore_index()` renders
   the WATCHED PATH + BRANCH prominently, so an agent in a sibling worktree sees the
   mismatch before trusting results (both #102-wave auditors had to infer it). Test pin +
   hostile-safe render; deploy BOTH.

## Scope OUT
- Fixing anything the table routes elsewhere — this packet moves state, not code
  (except item 4). A finding discovered mid-triage is filed, not fixed.

## Entry check
`lore_findings status=open` + `status=acknowledged` + `lore_tasks action=query` — diff the
live sets against the table; any row NOT in the table is a new finding to route (surface,
don't drop). Confirm image b0fce6904fc5 still deployed before citing it in receipts.

## Exit
Every open/acknowledged row transitioned or annotated with its destination; batch edges
via resolve_many/acknowledge_many where clean; the code commit gated (scoped pytest +
typecheck + ruff) + deployed BOTH; INDEX row + Log line; ledger row done.
