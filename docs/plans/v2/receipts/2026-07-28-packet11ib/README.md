# Packet 11-i-b — kickoff receipts (2026-07-28)

## ⚠ PATH NOTE — read before running any command quoted in these reports

The consult material was authored at the **repo root** as `consult-11ib/` and was moved here
at close-out (finding #72-class root pollution; lore indexes the root). **Every path in these
reports of the form `consult-11ib/…` is relative to *this directory*, not to the repo root.**

```
consult-11ib/tools/grade.py          →  docs/plans/v2/receipts/2026-07-28-packet11ib/consult-11ib/tools/grade.py
```

Nothing in the repo *calls* these scripts — verified at close-out by searching every reference
to each filename: all hits are their own usage docstrings, sibling prose, or the reproduction
commands in these reports. They are **hand-run instruments for a consult**, in no gate
(`testpaths`, `typecheck.sh`) by design, and archived rather than promoted for exactly that
reason. If a future packet needs a battery grader, promote them to `scripts/` **then** — with
gating, and with the hand-rolled markdown table parsing replaced by `markdown-it-py` (already a
declared dev dependency; **finding #270** records why, and the published scoreboard in
`REPORT-exhibit-11ib-1.md` §F1 is the equality oracle for that swap).

## What is here

| artifact | what it is |
|---|---|
| `CONSULT-SYNTHESIS-11ib.md` | **the result** — four blind informants on what makes a served number trustworthy |
| `REPORT-informant-{opus,sonnet,fable,cold}-11ib.md` | the raw consult runs, incl. pre-registrations locked before any package was opened |
| `REPORT-exhibit-11ib-1.md` | the exhibit package + its author's own six holes (§7) |
| `REPORT-adversary-exhibit-11ib-1.md` | the battery attacked — **INSUFFICIENT**, six wrong packages scoring identical to honest |
| `REPORT-lawtest-{opus,sonnet,fable}-1.md` | the three-model derivation of the trust hard-definition now in `CLAUDE.md` |
| `REPORT-scout-11ib-1.md` | the 11-i-b build inventory and the as-shipped interface freeze |
| `REPORT-fable-design-11ib-2.md` | the design sidecar: Q1–Q6 + the FU1 reconciliation |
| `consult-11ib/` | the exhibit variants, the battery, the grader-only key, and the hand-run tools |

⚠ `REPORT-lawtest-sonnet-1.md` carries a **SUPERSEDED SYMBOL NOTICE** at its top: it names a
symbol that no longer exists, used only as an illustrative example. The prose is preserved
deliberately — read the banner there for which symbol and why.
