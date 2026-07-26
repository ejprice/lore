# The two adversary REFERENCE BUILDS — graded instruments, NOT reference code

⚠ **READ THIS BEFORE OPENING EITHER DIFF.**

`REFERENCE-surface-03b.diff` and `REFERENCE-telemetry-03b.diff` are the production halves of the
two contract-adversaries' **reference implementations**, built 2026-07-24 to GRADE packet 03b's
test contract — by answering "if a builder satisfied this contract perfectly but fixed nothing,
would the tests still pass?" They were never audited as production code, and they are **not** what
shipped.

**They were deliberately WITHHELD from the builder** (packet file, BUILD-PHASE HANDOFF §1). The
shipped implementation was derived from the certified contract and the design rulings, never copied
from these. That withholding is load-bearing: finding #181 struck an earlier 03b contract phase
precisely because authors built their own references and then wrote the tests against them.

**Why they are archived here at all:** two SUFFICIENT contract certifications and the merged-build
gate all rest on these artifacts, and until now they existed ONLY under `/home/ejprice/scratch/` —
an address this repo's citation law forbids relying on, on trees that get reaped. This is the
merged-build gate's own residual **R2** (`REPORT-merged-gate-03b.md` §7), discharged.

**How to use them:** as EVIDENCE that a certification happened, and as raw material for a
blind-diff completeness check. **Never as a model for how the surface should be written** — for
that, read the shipped code and `docs/plans/v2/03b-design-rulings-r2.md`.

⚠ Both are STALE relative to what shipped: five subsequent fix/design waves changed the surface,
including the peek-convergence fix, the fence label, the pointer bounds and the windowed aggregate.
A diff that reproduces neither the graded build nor the shipped one is a trap; treat these as
dated snapshots of a grading instrument, nothing more.
