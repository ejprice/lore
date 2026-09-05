# REPORT — design-sidecar-63b (pointer)

brief-base v14 read
brief project v7 read

**State:** done · **Deviations:** none · **Packages considered:** see the design doc §6 ·
**Reuse ledger:** see the design doc §6 · **Graded:** `cedb20d` · HEAD-at-report: `cedb20d` · SAME ·
**Decisions-needed:** none (one ruled scope widening, design doc §4.C, carried as a brief line).

**The deliverable is the design doc, not this file:**
`docs/design/2026-09-03-packet63b-design.md` — the AUTHORITATIVE 63b rulings (operator-delegated
2026-09-03): §1 F5 runtime root-fix (effect-based state-diff detection via an `_sdk_guard` hook;
statement-scoped `governed_exempt`) · §2 #441 supersede atomicity (`authorize_guarded` + composed txn +
in-store `IF/THROW` conflict guard) · §3 #436 widened (ledger carries governance + lifecycle; replay
stamps + closes; sibling finding **#453** filed) + #437 (`render_subject_bound`) · §4 six comms-family
forks ruled · §5 wave structure (i / ii-a / ii-b / iii) · §6 ledgers · §7 riders roll-up.

Receipts: `lore_comms` send `#9000` → `lead-63b`; findings #449 / #441 / #436 / #437 annotated with
section pointers. This sidecar is long-running and STANDING BY for follow-ups (idle is benign).
