brief-base v11 read
brief project v7 read

# REPORT-contract-idlegate-05b — idle-gate v2 CONTRACT (packet 05b)

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- state: **done (REVISED round 2)** — RED contract + first automated hook harness; adversary graded round-1 INSUFFICIENT (4 wrong builds slipped 18 pins); added MP-1..MP-4 + N1/N2, **each discrimination-proven against the adversary's own reference + wrong builds**. Ready for the adversary re-run (no revision skips the adversary).
- model: **claude-opus-4-8** (opus48-worker frontmatter pin; attested per brief).
- deviations: **one (ledger mechanics).** After round-1 I transitioned the row to `done`; the lead's round-2 note said keep it `in_progress`, but `done→in_progress` is an illegal state-machine edge (`lore_tasks` rejected it). Row is stuck at `done`; work continued regardless. Flagging so the lead re-opens via a fresh row if it needs a live in_progress marker. (Did NOT touch `.claude/hooks/teammate-idle-gate.sh` — byte-identical to HEAD.)
- **ROUND 2 receipts:** §Revision below. New split vs v1: **5 RED / 18 GREEN** (23 pins). Satisfiability: v2-correct → **23 passed**. Discrimination: each wrong build reddens exactly its target MP pin. **ND-1 delta closed** (MP-2 now reddens the full-path archive glob `wb-r2-fullpath-archive` too, one fixture line; reach-attack STOP-RULE observed — the pinned bound). Ready for the adversary's 1-line confirm.
- Packages considered: **`bats-core` (bash test framework) → verdict `bespoke`.** READ: not installed; the repo's gate collects only pytest via `[tool.pytest.ini_options] testpaths` and runs `-n auto` — a bats suite would be un-collected and un-gated, i.e. "a guard nobody runs is a hope with a filename" (the exact class `scripts/` testpaths entry exists to kill). The chosen harness (pytest + stdlib `subprocess` invoking the hook, `REPO_ROOT = Path(__file__).resolve().parent.parent`) is the EXISTING repo idiom — cloned in shape from `scripts/test_scratch_copy.py` (subprocess-driven guard test). No third-party dep added; no hand-roll vs library fork arose.
- Graded: `299e69a` · HEAD-at-report: `299e69a` · SAME — the RED verdict below is measured against the current-hook bytes at this sha (hook untouched by me).
- decisions-needed:
  - **(RESOLVED in round 2)** Custom-artifact path resolution — the operator RULED reading (x) (archive glob scoped to the REPORT-default; a custom declared path resolves at root+worktrees only), so it is now pinned: MP-1 (worktree half) + MP-2 (no-archive half). The round-1 C-DEF-trap deferral is discharged.
  - **(lead bookkeeping)** The 5 RED pins are contract-first expected-REDs the builder greens WITHIN 05b; if the contract is committed before the builder greens them, they need a `scripts/pending_contracts.yaml` adjudication (owner=builder, trigger=v2 hook shipped) to read RED_ADJUDICATED not RED_ORPHANED at the currency gate. Not my writable set — flagging.
  - **(seam)** WRITE-SIDE ↔ packet 06: this contract pins the READ side + the file-format spec; 06 promotes the write to brief-base. Named below so 06 inherits it with the format already pinned.
- receipt pointers:
  - contract file: `scripts/test_teammate_idle_gate.py` (module docstring = branch inventory + pin map + file-format spec + discrimination-harness note).
  - RED run receipt: §RED run (round-1 4/14) + §Revision (round-2 5/18 + discrimination matrix).
  - gates: §Gates (ruff clean · mypy Success · pytest `-n auto` · zero collection errors, +23 mine).
  - design of record: `REPORT-fable-design-05b.md` §Q2; adversary: `REPORT-adversary-idlegate-05b.md` (both archived at close-out to `docs/plans/v2/receipts/<date>-packet05b/`).
  - findings: #149 (owes-nothing false-fire + green-on-own-target), #121 (worktree-awareness), #152 (archiving law) — read via `lore_findings action=get`.

---

## Revision (round 2 — adversary INSUFFICIENT → SUFFICIENT-basis)

The `contract-adversary` graded round 1 **INSUFFICIENT**: 4 wrong builds (WB5/WB6/WB7/WB10)
passed all 18 pins (`REPORT-adversary-idlegate-05b.md` §"The 4 MISSING PINS"). All four holes
lived in the custom-artifact-path and missing-key surfaces I had deliberately under-pinned in
round 1 (the C-DEF-trap deferral) — now pinnable because the operator RULED reading (x). Added:

| pin | catches wrong build | v1 | discrimination (v2-correct vs wb) |
|-----|---------------------|----|-----------------------------------|
| **MP-1** custom artifact @ worktree root → 0 | WB5 (custom root-only) | RED | v2-correct **0** · wb5 **2** |
| **MP-2** custom under archive dir → 2 | WB6 (basename glob) **+ ND-1** (full-path glob) | GREEN | v2-correct **2** · wb6 **0** · wb-r2-fullpath **0** |
| **MP-3** missing `artifact` key + reportless → 2 | WB7 (missing-key→owes-nothing) | GREEN | v2-correct **2** · wb7 **0** |
| **MP-4** custom absent, idle ×2 → 2,0 | WB10 (custom wake-loop) | GREEN | v2-correct **2,0** · wb10 **2,2** |
| **N1** `assert_no_shell_error` | — (helper hardening) | — | broadened (case-insensitive; +`command not found`/`jq:`) + honest docstring: the EXIT CODE is the real crash guard, this catches a right-exit-code build that LEAKS a diagnostic |
| **N2** nudge keeps `continue as you were` softener | a v2 that drops #149's anti-cry-wolf body | GREEN | passes v1 & v2-correct; reddens the adversary's stub builds |

**Round-2 DELTA (ND-1).** The adversary re-graded r2 INSUFFICIENT by ONE survivor:
`wb-r2-fullpath-archive` archive-globs a custom path by its FULL declared path
(`receipts/*/docs/design/FOO.md`) — the reuse my own round-1 residual-1 named first — passing
all 23. Fixed per the adversary's proven scenario F with ONE fixture line: MP-2 now places the
custom file under `receipts/*/` in BOTH archive layouts (basename `FOO.md` AND full path
`docs/design/FOO.md`), so it reddens both archive-glob readings. Self-verified: v2-correct →
**23 passed**; wb6 → MP-2 reddens; wb-r2-fullpath-archive → MP-2 reddens; v1 → MP-2 still green.
Per the reach-attack STOP-RULE (adversary + CLAUDE.md), the two NATURAL archive readings are
both closed — deeper globs are adversarial-only — so this IS the pinned bound; not chased further.

**How discrimination was proven (the load-bearing method).** I added an `IDLE_GATE_HOOK` env
override to the harness so the SAME contract runs against an alternative hook build, then ran
it against the adversary's own surviving reference + wrong builds
(`/tmp/adv-idlegate-05b/hooks_variants/`, from its report Appendix):

```
DEFAULT (real v1 hook)              => 5 failed / 18 passed   (null×2, custom-present, MP-1, reach)
v2-correct.sh (satisfiability)      => 23 passed              (every pin, new ones incl., 0-failed on the correct build)
wb5-custom-root-only    (MP-1)      => MP-1 reddens  (+ N2*)
wb6-custom-archive-basename (MP-2)  => MP-2 reddens  (+ N2*)
wb7-missingkey-owes-nothing (MP-3)  => MP-3 reddens  (+ N2*)
wb10-custom-wakeloop    (MP-4)      => MP-4 reddens  (+ N2*)
wb-r2-fullpath-archive  (ND-1/MP-2) => MP-2 reddens            (full-path archive glob; the ND-1 fix)
```
*N2 also reddens on all four because the adversary's minimal repro stubs truncated the nudge
message — an incidental extra catch, not a confound: each MP pin's discrimination is isolated
(its target wb reddens it, v2-correct greens it). N2 itself is green on both v1 and v2-correct.

**A real bug in my own harness, found and fixed during the discrimination run** (receipt for
honesty): the fixture copied the hook to `HOOK_SOURCE.name`, which under the override became
`v2-correct.sh` while `gate.hook` looked for the canonical `teammate-idle-gate.sh` → `bash`
ran a nonexistent file (exit 127) → all 23 "failed" for every override build. Fixed by
installing under a fixed `HOOK_BASENAME`. Caught precisely because "v2-correct → 23 failed"
is an impossible satisfiability result — the check that the correct build goes 0-failed is
what exposed it (the C-DEF satisfiability receipt doing its job on my own instrument).

---

## What I built

`scripts/test_teammate_idle_gate.py` — the **first automated instrument** for
`.claude/hooks/teammate-idle-gate.sh`. It was previously guarded only by the hand-run
"pipe-test all four branches" habit. **23 pins** (18 round-1 + 5 round-2 adversary-added),
subprocess-driven, hermetic.

**Harness design (hermeticity — the load-bearing property).** Each test copies the REAL
committed hook byte-exact into a `tmp_path` sandbox and invokes it there, so the hook's
`BASH_SOURCE`-derived `repo_root`, its `/tmp/claude-idle-gate-<basename>` marker dir, and
every report path resolve INSIDE the sandbox. The real repo root and the real
`/tmp/claude-idle-gate-lore` marker dir are NEVER touched. `session`/`teammate` are per-test
uuids → markers/contracts collision-free across runs and xdist workers. A provenance pin
(`TestHarnessProvenance`) asserts the sandbox copy == `HOOK_SOURCE` bytes, so when the
builder edits the real hook these tests exercise the NEW bytes automatically (the #140
"which tree am I testing?" class, in miniature — a bash file has no `.pth`/`__pycache__`
poison, so byte-equality IS identity here).

---

## Current-hook (v1) BRANCH INVENTORY — the removed-behavior inventory (pin-per-branch)

Read @ `299e69a`. v2 is a **PURE WIDENING**: it may prepend contract-reading in front of
these six branches; it may drop none. Each branch has a regression pin that goes RED the day
v2 drops it.

| # | hook line | branch | v1 exit | pin (in `TestRegressionBranchInventory`) | today |
|---|-----------|--------|---------|-------------------------------------------|-------|
| B1 | 33 | empty `teammate_name` (unidentifiable payload) | 0 | `test_unidentifiable_payload_is_allowed` | GREEN |
| B2 | 39 | `REPORT-<name>.md` at repo root | 0 | `test_report_at_root_is_allowed` | GREEN |
| B3 | 54 | archived report `receipts/*/` (compgen -G, #149) | 0 | `test_archived_report_is_allowed` | GREEN |
| B4 | 63 | report in ANY registered worktree (#121) | 0 | `test_worktree_report_is_allowed` | GREEN |
| B5 | 72 | `.nudged` marker present (already nudged once) | 0 | `test_one_shot_nudge_then_allowed` (2nd idle) | GREEN |
| B6 | 78 | else: write marker + nudge | 2 | `test_one_shot_nudge_then_allowed` (1st idle) | GREEN |

---

## PIN MAP (§Q2 pins 1–6) and RED run receipt — ROUND 1

> ⚠ ROUND-1 record (18 pins, 4 RED / 14 GREEN). Superseded by §Revision above, which adds
> MP-1..MP-4 + N1/N2 → 23 pins, 5 RED / 18 GREEN. Kept for the round-1 reasoning.

Run against the CURRENT v1 hook @ `299e69a` (`uv run pytest scripts/test_teammate_idle_gate.py`):
**`4 failed, 14 passed`** — reproduced identically under `-n auto`. v1 never reads the
contract file, so the four WIDENING pins are RED; the regression / positive-control /
fail-open pins are GREEN (they guard the v2 *rewrite*, not the v1→v2 delta).

**The 4 RED pins (each fails for the RIGHT reason — v1 ignores the contract and nudges where correct-v2 allows):**

1. `TestOwesNothingExemption::test_null_artifact_never_nudges_even_reportless`
   — contract `{"artifact": null}` + no report → asserts exit 0; v1 → **exit 2** (nudge:
   `idle-gate: REPORT-<uuid>.md is not at the repo root …`). **RED.** This is the whole point
   of v2 (the await/sidecar/drill exemption #149 asked for).
2. `TestOwesNothingExemption::test_null_artifact_allowed_on_repeated_idle_without_consuming_one_shot`
   — `{"artifact": null}`, run twice → both exit 0 + no `.nudged` marker; v1 → **exit 2** on
   the first run. **RED.**
3. `TestCustomArtifactPath::test_custom_artifact_present_is_allowed`
   — contract `{"artifact": "docs/design/FOO.md"}` + that file present (no `REPORT-<name>.md`)
   → asserts exit 0; v1 → **exit 2** (checks the hardcoded `REPORT-<name>.md`). **RED.** Kills
   the hardcoded-filename assumption.
4. `TestReachIsCheckedVariable::test_checked_path_tracks_the_contract_value`
   — `A.md` present at root; agent declaring `A.md` → 0, agent declaring `B.md` (absent) → 2;
   v1 → **exit 2** for the `A.md` agent (ignores the contract). **RED.** The INSTRUMENT-0 pin:
   proves the checked path is READ from the contract, not a hidden constant — the one pin that
   stops v2 becoming another hardcoded-name guard (CLAUDE.md instrument-lesson table).

**The 14 GREEN pins** (harness provenance ×1; B1–B6 regressions ×5 incl. worktree/archive;
pin-1 positive control ×1; pin-2 absent control ×1; pin-3 fail-open ×2; pin-4 malformed
fail-open ×4). Notable discriminators:
- **pin-1 POSITIVE CONTROL** (`test_positive_control_owed_report_missing_still_nudges`,
  GREEN): a contract declaring an OWED-but-missing report → exit 2. Load-bearing — proves the
  `null` exemption is keyed on the VALUE, killing a wrong-v2 that exits 0 whenever a contract
  file merely EXISTS (which would pass every null test while disabling the gate).
- **pin-4 malformed** (4 pins, GREEN): garbage JSON, missing `artifact` key, and empty file
  each fail-open to the v1 default with NO `set -u`/`set -e` crash (`assert_no_shell_error`
  scans stderr for `unbound variable`/`syntax error`) — guards a crashing v2, the #131 leg.

RED→GREEN is the builder's job: implementing §Q2's contract-read flips exactly these 4 to
green while the 14 stay green.

---

## The declared-artifact-contract FILE FORMAT — this contract owns and pins it (→ 06)

Pinned BEHAVIOURALLY by the tests (a builder reading a different path/key leaves the RED pins
RED). Authoritative spec:

- **Path:** `/tmp/claude-idle-gate-$(basename "$repo_root")/${session_id}-${teammate_name}.contract`
  — the SAME dir family the hook already `mkdir -p`s for `.nudged` markers (§Q2; no new
  location, no env var — #121 measured `CLAUDE_PROJECT_DIR` unset for spawned agents; no
  MCP — the hook has none).
- **Content:** jq-readable JSON, one key `artifact`:
  - `{"artifact": "REPORT-<name>.md"}` → owes that path
  - `{"artifact": null}` → owes NOTHING (idle always allowed)
  - `{"artifact": "docs/design/FOO.md"}` → owes a custom path
- **Fail-open semantics:** absent / unparseable / missing-`artifact`-key → v1 default
  (`REPORT-<name>.md` resolved across root + archive + worktree, then the one-shot nudge).

Packet 06 inherits this for the WRITE side (making every agent write its own contract as a
brief-base first action). 05b ships only the READ side + this format — value lands
immediately (per-agent spawn briefs can already write the contract; no contract ⇒ pure v1).

---

## Gates (my file only — brief-scoped)

- `uv run ruff check scripts/test_teammate_idle_gate.py` → **All checks passed!**
- `MYPYPATH=scripts uv run mypy scripts/test_teammate_idle_gate.py` → **Success: no issues found.**
- `uv run pytest scripts/test_teammate_idle_gate.py -n auto` → **5 failed / 18 passed** (round-2 contract-first split; hermetic under parallelism).
- **ZERO-NEW (#333 baseline):** full-testpaths `--collect-only` → **ZERO collection errors**; my file contributes **exactly 23**. Adds no mypy debt, breaks no existing green test, imports cleanly. The 5 REDs are the DELIVERABLE (contract-first), not baseline breakage — the auth-WIP #333 set is untouched.

---

## Residuals / flags (escalating is a success state)

1. **Custom-path archive/worktree resolution is under-specified (builder decision).** §Q2
   step 3 says "resolve that path in root AND archive AND worktrees … applied to the declared
   path." For the default `REPORT-<name>.md` the archive glob (`receipts/*/REPORT-<name>.md`)
   and worktree walk are well-defined. For an arbitrary custom path like `docs/design/FOO.md`,
   "archive resolution" is ambiguous (glob `receipts/*/docs/design/FOO.md`? or is the archive
   branch only meaningful for the REPORT default?). I **pinned only the unambiguous core**
   (custom-present-at-root → 0, custom-absent-everywhere → 2) and deliberately did NOT pin the
   archive/worktree resolution of a *custom* path — over-pinning an under-specified design
   point is the C-DEF trap (a pin the builder cannot satisfy without guessing). **My
   recommended reading:** apply the worktree walk to the declared path (matches §Q2 and the
   #121 spirit); treat the archive glob as REPORT-default-only (a custom design doc is not
   archived under `receipts/` by the #152 ritual — that ritual moves `REPORT-*.md`). Builder
   should confirm and add the pin they land on.

2. **`jq`-absent path is a documented BOUND, not a pin.** The malformed-JSON pins cover
   "`jq` cannot parse". "`jq` binary absent" (the #131-shaped host gap) is untestable
   hermetically on a host that has `jq` (this one does: jq-1.8.2). v1's existing `jq` calls
   already `2>/dev/null`; v2's contract-read must do the same and fail-open. Flagging so the
   builder keeps the suppression; a pin would require a `jq`-less PATH shim (possible but
   heavy — recommend the builder add it only if cheap).

3. **pending_contracts.yaml adjudication** (bookkeeping, above in decisions-needed): the 4
   REDs green within the wave; if committed before greening, they need an owned/triggered
   adjudication to avoid RED_ORPHANED. Outside my writable set.

4. **`comms_cli.py` is a SEPARATE track, no collision.** `loremaster/comms_cli.py` (packet
   05a-iii) is the lore-status "hook bridge" — the approach §Q2 explicitly REJECTED for THIS
   bash hook (an MCP/store dependency on a fail-open guard). It does not touch this hook and
   my contract does not touch it. Noted for scope honesty; no action.

## Confirmations
- **Hook untouched:** `git diff --stat -- .claude/hooks/teammate-idle-gate.sh` → empty. The
  provenance pin also asserts the sandbox copy equals `HOOK_SOURCE` bytes.
- **Writable set honored:** `git status --porcelain` shows only `REPORT-contract-idlegate-05b.md`
  and `scripts/test_teammate_idle_gate.py` as mine (the other untracked `REPORT-*.md` predate me).
- **Ledger:** task `e574e2abd16c49d2bb7f9f76e0b0e900` claimed → in_progress (driven by me).
