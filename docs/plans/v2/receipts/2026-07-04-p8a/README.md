# P8a / P8d evaluation records (2026-07-04 → 2026-07-06)

## ⚠ PATH NOTE — read before running any command or following any link quoted in these files

These six artifacts were authored and lived at **`docs/eval/`** until they were archived here on
**2026-07-29** (packet 44, "UNGATED GROUND"). **Every path of the form `docs/eval/<one of the six
names below>` written inside these files — and inside the reports that cite them — is relative to
*this directory*, not to `docs/eval/`.**

```
docs/eval/evaluation_harness_p8a.py  →  docs/plans/v2/receipts/2026-07-04-p8a/evaluation_harness_p8a.py
docs/eval/2026-07-04-p8a-baseline.md →  docs/plans/v2/receipts/2026-07-04-p8a/2026-07-04-p8a-baseline.md
```

**The bytes are unchanged.** The move was a `git mv` and git recorded all six as 100%-similarity
renames (`6 files changed, 0 insertions(+), 0 deletions(-)`) — which matters because
`docs/plans/v2/DESIGN-LAW.md` §6 pins these instruments as **"REUSED VERBATIM — measurement pins
are never upgraded"**. That pin is about the ARTIFACT, and the artifact is byte-identical; only its
address changed. Their own internal self-citations (`docs/eval/…`) were therefore **not** rewritten
— editing an archived receipt is a falsification, not a fix — which is exactly what this path note
exists to translate.

## Why they moved

`docs/eval/` is a **live** tree: it holds `smoke_p8b.py`, the deploy smoke that caught #107 and
#131, plus that smoke's own suite. Packet 44 brought the tree under `scripts/typecheck.sh` (its own
leg, `MYPYPATH=docs/eval uv run mypy docs/eval`). These six files are July-2026 **records**, not
live source — measured 2026-07-29 at `5a850c3` under the gate's own invocation
(`MYPYPATH=docs/eval uv run mypy docs/eval` → `Found 36 errors in 2 files (checked 4 source files)`),
the two `.py` relics carried **all 36** and the two smoke files carried **zero**. Archiving the records is
what let the live tree be gated wholesale instead of behind a per-file carve-out, which would have
been an enumerated exemption list — the losing shape by this repo's own instrument lesson.

## What is here

| artifact | what it is |
|---|---|
| `evaluation_harness_p8a.py` | the P8a A/B evaluation harness — the instrument `DESIGN-LAW.md` §6 mandates be reused verbatim for any A/B gate |
| `connections_p8a.py` | its REQUIRED sibling (`from connections_p8a import create_connection`); the two only run as a pair |
| `2026-07-04-p8a-baseline.md` | the P8a baseline digest — the per-task baseline table `DESIGN-LAW.md` §6 sources |
| `2026-07-04-p8a-baseline-raw.md` | the raw transcripts behind that digest |
| `p8d-flip-eval-raw.md` | the P8d flip-eval raw transcripts (35 runs) |
| `p8dprime-rerun-raw.md` | the P8d′ rerun raw transcripts |

## Gating status — ungated BY DESIGN, and that is law-backed

Nothing in the repo *imports* these two modules: verified 2026-07-29 with a bare, anchor-free
`git grep --fixed-strings` over all tracked files for each of the six names — the only `import` of
either module is `evaluation_harness_p8a.py`'s own `from connections_p8a import create_connection`,
and both files moved together, so it still resolves. Every other hit was prose.

They sit in `docs/plans/v2/receipts/`, which is excluded from ruff (`pyproject.toml`
`[tool.ruff] extend-exclude`, whose committed comment gives the reason: *"a receipt that has been
reformatted is no longer evidence of the run it documents"*), outside every `scripts/typecheck.sh`
member, and outside every `testpaths` entry. That is deliberate, and it is the same disposition the
`2026-07-28-packet11ib/consult-11ib/tools/` README records for the consult instruments.

**Re-open trigger:** if a future packet needs to RUN the A/B gate again, run these bytes as they
are — that is what the `DESIGN-LAW.md` §6 pin demands. If a packet ever needs to *change* the
harness, that is a promotion to a gated tree (`scripts/`), and it must be justified against §6's
"measurement pins are never upgraded" clause first — not done quietly here.
