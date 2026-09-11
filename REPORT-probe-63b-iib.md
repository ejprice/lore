brief-base v14 read
brief project v7 read

# REPORT — probe-63b-iib → see REPORT-probe-63b-ii-b.md

Name reconciliation: my spawn brief named the report **`REPORT-probe-63b-ii-b.md`** (with the dash)
and that is the canonical, full deliverable — committed at `0f36420`. The idle-gate hook derives the
name from my native/comms teammate id `probe-63b-iib` (no dash), so this thin pointer exists at that
spelling so the gate and a lookup by either spelling both resolve. **Read the full report at
`REPORT-probe-63b-ii-b.md`.**

## One-line result
`DD-3.c: ABORTS-WHOLE` — a legacy over-cap `to.ack_note` edge in an unstamped drain window aborts the
WHOLE drain `UPDATE ... SET seen_at` (standalone AND the §4.B one-txn shape) → total inbox denial;
the good edge is left unstamped. LEG A: every ii-b composed read shape IndexScans. LEG B: the §4.B
one-txn clean-store drain works. Instrument: `scripts/probe_drain_read_63b_ii_b.py` (exit 0).
