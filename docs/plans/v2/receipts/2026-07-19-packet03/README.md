# Packet 03 kickoff receipts — 2026-07-19/20

Preserved because repo law deletes root-level `REPORT-*.md` before an image build. **A fresh
packet-03 session does not need to read these** — every conclusion is already in the packet files,
`docs/reference/surrealdb-31-capabilities.md`, and the finding ledger. They are here so a claim can
be audited back to its receipt.

| file | what it settles |
|---|---|
| `REPORT-recon-pkt03.md` | Structural map: ledger blueprint · retry seam + its guard obligations · schema slices · the render seam and every instrument that polices it · tool surface pins · test harness. ⚠ Its claim that two counter tables are "outside the pins" is **WRONG** — lead-verified, both have dedicated pins. |
| `REPORT-probe-pkt03-store.md` | Five live store probes: RELATE validates NEITHER endpoint · #7061 cascade ABSENT · `sequence::nextval` in the real write shape · the four-way-ambiguous CAS return · table-definition coverage (and #124's mechanism correction → #144). |
| `REPORT-docs-surreal-31-reconcile.md` | The documentation-first pass. **Found `ENFORCED`, which five probes and a cold audit missed.** Two vendor falsehoods (§6.4/§6.5), the citation upgrades, and the list of claims we are the sole source for. |
| `REPORT-probe-enforced-clause.md` | `ENFORCED` in eight legs: works on 3.1.5, validates both endpoints, `IF NOT EXISTS` is a silent no-op so `OVERWRITE` is required, pre-existing ghosts unaffected, composes with UNIQUE+SCHEMAFULL, no measurable cost, error ergonomics (why the app check survives), `INSERT RELATION` is the door only it shuts. |
| `REPORT-audit-edge-preflight.md` | Read-only production audit: all **101,479** live edge rows endpoint-homogeneous, **zero** would be poisoned, **zero** ghosts. `message`/`to` absent from production (greenfield). The data is safe; the mechanism is the risk. |
| `REPORT-contract-pkt03.md` | The 400-pin contract's own documentation. **Read its two UPDATE sections at the end first** — they supersede every earlier count, sizing and escalation in the summary block. |
| `REPORT-adversary-pkt03.md` | Adversary grading: eight wrong builds passed the ledger contract **57/0**. Three BLOCKERs + MAJOR + lesser, all now closed and mutation-proven RED. §5 lists six instruments verified strong — **do not weaken them**. §7 residuals include the ungraded `[real]` leg. |
| `REPORT-probe-racer-contention.md` | Settles a repo-wide worry: the single-operation concurrency pattern **DOES** contend (0 conflict-free runs in 20, at 8/16/32-way, serial and `-n auto`). No rewrite needed — and the proposed "fix" would have made the pin *weaker*. |
