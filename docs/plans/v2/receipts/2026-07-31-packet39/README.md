# Packet 39 — Google OAuth: the contract wave (2026-07-31)

Reports from the design + contract + four-adversary sequence. **The build was never
started**, deliberately: the contract never reached SUFFICIENT, and the reason became an
operator decision (finding **#296**) rather than another round.

**Read them as a sequence, not as independent verdicts.** Each adversary pass acted on the
one before it, and each found a real blocker that every prior gate had passed:

| report | verdict | what it found |
|---|---|---|
| `REPORT-design-sidecar-39-1.md` | — | the ruled design, R1–R16 (revised four times) |
| `REPORT-contract-39-auth-1.md` | — | the contract, revised **four** times: 422 → 448 → 467 → 480 pins |
| `REPORT-adversary-39-auth-1.md` | INSUFFICIENT | 45 wrong builds, **12 survived**; WB30 — guard dead on the wire |
| `REPORT-adversary-39-auth-2.md` | INSUFFICIENT | 10 of 12 killed, **9 new**; WB48 — guard ran *after* the tool body |
| `REPORT-adversary-39-auth-3.md` | INSUFFICIENT | WB93 — same class on `list_tools`, via an instance attribute |
| `REPORT-adversary-39-auth-4.md` | INSUFFICIENT | WB100 — same class on the **class** attribute; **flaky-green 5/10** |

**The through-line:** `FastMCP.__init__` calls `_setup_handlers`, which registers the
**bound** method — so anything installed afterwards is live in-process and **dead on the
wire**. Four doors, four waves. Pinning placements did not terminate, so the lead stopped
and escalated the design rather than run a fifth round.

**Final measured state** (contract only; no implementation exists):
480 collected / 444 RED / 36 GREEN · rest of suite 7705 passed / 0 failed · ruff clean ·
satisfiability re-discharged on every revision (0 failed against a correct reference build).

**Findings filed:** #291 · #294 · #295 · #296.
**Successor:** `docs/design/2026-08-01-multi-user-lore-proposal.md` — its part 2 answers #296.
