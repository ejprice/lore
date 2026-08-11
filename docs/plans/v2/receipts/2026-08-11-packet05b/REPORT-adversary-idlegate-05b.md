brief-base v11 read
brief project v7 read

# REPORT-adversary-idlegate-05b — CONTRACT-ADVERSARY, idle-gate v2 (packet 05b)

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- model: **claude-opus-4-8** (contract-adversary frontmatter `model: opus`; the invoking brief pins opus48 — attested).
- state: **done** — CONTRACT graded empirically by building 11 wrong hooks + 1 correct reference and running the REAL contract against each.
- **VERDICT (r1, 18 pins): CONTRACT INSUFFICIENT.** 4 wrong builds pass all 18 pins.
- **⚠ DELTA RE-GRADE (r2, 23 pins) appended at the END — see §DELTA. r2 VERDICT: still INSUFFICIENT — MP-1..MP-4 all land, but ONE new survivor (`wb-r2-fullpath-archive`: full-path archive glob for a custom path) passes all 23. One cheap, proven fixture fix.**
- **P1 headline — wrong builds that SURVIVE the full contract (18/18 passed):** WB5 (custom path resolved ROOT-ONLY, reading z), WB6 (custom path given an ARCHIVE-basename glob, reading y), WB7 (a well-formed contract MISSING the `artifact` key treated as owes-nothing), WB10 (custom-absent path wake-loops — one-shot marker never written).
- **Satisfiability receipt:** a correct v2 hook (§Q2 + reading x) → **18 passed** (4 RED→GREEN, 14 stay GREEN). v1 control → **4 failed/14 passed**, reproducing the author's RED claim exactly, right reason.
- Attacks 1–4 from the brief are all **DEFENDED** by the contract (WB1/WB2/WB3a/WB3b/WB4 each redden ≥1 pin). Attack 5 (residual 1) is the hole.
- deviations: **did NOT run `scripts/scratch_copy.sh`** — reasoned: the contract imports no workspace member (pure stdlib+pytest, invokes bash via subprocess), so `.pth`/`__pycache__` poison is structurally impossible; provenance proven instead by controlling + printing `HOOK_SOURCE` and the passing `TestHarnessProvenance` byte-pin. See §Provenance.
- Packages considered: **none — no mechanism specified by me**; my probes are throwaway bash hooks. (The contract specifies bash+`jq`, already a hook dependency — `keep_with_trigger` per design §Q2, not my call to revisit.)
- Graded: `299e69a` · HEAD-at-report: `299e69a` · SAME. Contract file `scripts/test_teammate_idle_gate.py` @ its untracked `??` state; real hook untouched (byte-identical to HEAD).
- decisions-needed (for the contract author / lead):
  - Residual 1 is no longer a C-DEF trap — the **operator RULED reading (x)**, which makes (x) pinnable. **My verdict: the absence of these pins IS a missing pin — (x) must be pinned** so a builder cannot ship (y)/(z). (Answer to brief Q5.)
  - 4 missing pins below are the INSUFFICIENT basis; 2 lower-severity notes + 1 confirmed-safe row follow.
- receipt pointers: probe matrix = §"Wrong-build matrix"; discrimination proofs = §"Discriminating-scenario proofs"; P1b table = §"P1b quantifier table"; P1c table = §"P1c reach table"; instruments pasted verbatim = §"Appendix — instruments".

---

## The 4 MISSING PINS (each: the test that should exist + the defect it catches + the wrong build that survives today)

### MP-1 — custom path is NOT resolved at worktree roots (residual 1, reading-x worktree half)
- **Test that should exist:** a custom-declared artifact committed ONLY at a linked WORKTREE root → **exit 0** (mirrors `test_worktree_report_is_allowed`, but with a contract declaring `docs/design/FOO.md` instead of the default).
- **Defect it catches:** a v2 that applies the #121 worktree walk only to the DEFAULT `REPORT-<name>.md` and resolves a *custom* declared path at the main root only. Under operator reading (x) a custom path resolves at "root + worktrees"; a worktree-assigned agent that declares a custom artifact gets falsely nudged — the exact #121 defect, re-opened for the custom path.
- **Reproduction:** `wb5-custom-root-only.sh` → **18 passed** (survives). Discriminating scenario C: correct build `exit=0`, WB5 `exit=2` (see §Discriminating-scenario proofs).

### MP-2 — custom path IS (wrongly) allowed to match the archive glob (residual 1, reading-x no-archive half)
- **Test that should exist:** a custom-declared artifact present ONLY as `docs/plans/v2/receipts/<dir>/<basename>` (archive basename), declared path `docs/design/FOO.md` absent at root/worktree → **exit 2** (nudge). Reading (x): the `receipts/*/` glob stays scoped to the `REPORT-<name>.md` default; there is NO archive glob for a custom path.
- **Defect it catches:** a v2 implementing reading (y) — "archive basename anywhere" — which would exempt an agent because an unrelated file with the same basename sits in some archived receipts dir. False-clear of the gate.
- **Reproduction:** `wb6-custom-archive-basename.sh` → **18 passed** (survives). Discriminating scenario B: correct build `exit=2`, WB6 `exit=0`.

### MP-3 — missing `artifact` key is indistinguishable from `null` on the reportless path
- **Test that should exist:** a well-formed contract lacking the `artifact` key (`{"unrelated": 1}`) **with NO report anywhere** → **exit 2** (missing-key → v1 default → reportless → nudge). The existing `test_contract_missing_artifact_key_falls_open` places a root report, so correct-build and wrong-build BOTH exit 0 — the fixture cannot discriminate (its own docstring promises to kill "treats missing-key as owes-nothing and exits 0 for an agent that DOES owe a report", but the placed report makes that agent's owed artifact PRESENT, so the kill never fires).
- **Defect it catches:** the most natural jq parse — `declared=$(jq -r '.artifact' contract)` yields the string `"null"` for BOTH `{"artifact":null}` AND a missing key — so a build that treats `"null"` as owes-nothing silently **exempts from the gate any agent whose contract is malformed by a typo'd/absent key**, even one that owes a report. Spec (design §Q2 + contract docstring semantics) rules missing-key → V1 DEFAULT, not owes-nothing.
- **Reproduction:** `wb7-missingkey-owes-nothing.sh` → **18 passed** (survives). Discriminating scenario A: correct build `exit=2`, WB7 `exit=0`. Note the OTHER natural collapse (`jq -r '.artifact // empty'`, which maps null→"" wrongly) IS caught by the null pins (`wb9` → 2 failed) — so the hole is specifically the missing-key→owes-nothing direction, unguarded because the only missing-key fixture is report-present.

### MP-4 — the one-shot marker is not pinned on the custom (non-default) nudge path
- **Test that should exist:** a custom-declared artifact absent everywhere, idle **twice** → first idle **exit 2**, second idle **exit 0** (one-shot; marker consumed). Today `test_one_shot_nudge_then_allowed` exercises the one-shot only on the DEFAULT no-contract path; `test_custom_artifact_absent_nudges` checks a single idle.
- **Defect it catches:** a v2 that writes/consults the `.nudged` marker only on the default path and nudges a custom-owing reportless agent on EVERY idle — a wake-loop, the exact harm the one-shot exists to prevent (CLAUDE.md: "agents legitimately waiting … are never wake-looped").
- **Reproduction:** `wb10-custom-wakeloop.sh` → **18 passed** (survives). Discriminating scenario D: correct build `first=2 second=0`, WB10 `first=2 second=2`.

---

## Lower-severity notes (not the INSUFFICIENT basis, but surfaced per scope law)

- **N1 — `assert_no_shell_error`'s token set is narrow, and it is not the real crash guard.** It scans stderr for `unbound variable`/`syntax error` only. A `set -e` + un-suppressed `jq` crash on malformed JSON emits `jq: parse error …` and exits non-zero — the token set does NOT match (measured: WB4 stderr = `jq: parse error: Invalid literal…`, grep for the tokens = 0). Those crashes are still caught, but by the **exit-code** assertion in `assert_allowed`/`assert_nudged`, not by `assert_no_shell_error`. The helper therefore over-promises "the hook didn't crash" while only catching two specific bash diagnostics. It IS a real positive control for a `set -u` unbound crash (measured: WB8 stderr contains `unbound variable`, grep = 1). Recommendation: either broaden the token set (`error`, `command not found`, `jq:`) or relabel the helper as "no bash-level unbound/syntax crash" so a future reader does not over-trust it. Not a hole today because exit-code covers the escapes.
- **N2 — the nudge MESSAGE prose is not pinned beyond the `idle-gate:` token (P6b orphaned virtue).** v1's message carries the anti-cry-wolf softener *"If you are mid-work or waiting on a background process, continue as you were."* `assert_nudged` only checks the substring `idle-gate:` is present, so a v2 that drops the softener (or the whole helpful body) passes. Pinning exact prose is brittle and I do NOT recommend it; a single-substring pin on the *"continue as you were"* clause would preserve the one load-bearing UX behavior (#149's "a gate that cries wolf gets switched off") without freezing the wording. Author's call.

## Confirmed-SAFE row (a plausible gap that the contract DOES close — reported so it is not re-litigated)
- **The contract-file PATH is fully pinned (session AND teammate).** A build dropping `session_id` from the contract path (`${teammate}.contract`) cannot find the test's `${session}-${teammate}.contract` and falls to v1 → the 4 widening pins go RED. Measured: `wb11-teammate-only-path.sh` → **4 failed/14 passed**. The reach pin additionally varies the teammate (who_a vs who_b, same session), pinning teammate-keying. So no session/teammate-scoping pin is missing.

---

## Answers to the brief's five named attacks (all empirical)

1. **Hook that exits 0 whenever a contract file EXISTS (value ignored) — does pin-1's positive control catch it?** YES. `wb1-contract-exists-allow.sh` → 5 failed, including `test_positive_control_owed_report_missing_still_nudges` (and `test_custom_artifact_absent_nudges`, both garbage-reportless pins, and the reach pin). The positive control is load-bearing and works.
2. **Hook that reads the contract but hardcodes `REPORT-<name>.md` — does the reach pin catch it?** YES for the value-at-root. `wb2-null-but-hardcoded.sh` → 2 failed (`test_custom_artifact_present_is_allowed`, `test_checked_path_tracks_the_contract_value`). **BUT the contract's OWN reach is not a fully checked variable:** pin 6 exercises the declared value only at the ROOT location — a build honoring the declared value at root while ignoring it at worktree/archive (WB5/WB6) escapes. See §P1c.
3. **Hook that DROPS a B1–B6 branch — do the regression pins redden?** YES on the DEFAULT path. `wb3a-drop-worktree.sh` → `test_worktree_report_is_allowed` RED; `wb3b-drop-archive.sh` → `test_archived_report_is_allowed` RED. (Caveat: the regression pins only exercise the default `REPORT-<name>.md`; the *custom-path* analogues of the worktree/archive branches are unpinned — that is MP-1/MP-2.)
4. **Hook that crashes under `set -u`/`set -e` on a malformed contract — do the fail-open pins catch it?** YES, via the exit-code leg. `wb4-set-e-crash.sh` → `test_garbage_json_with_root_report_is_allowed` + `test_garbage_json_reportless_nudges_without_crashing` RED (exit 5 ≠ expected 0/2). See N1 for the nuance that `assert_no_shell_error` itself does not fire on the jq crash.
5. **The custom-path under-spec (residual 1): (x) vs (y) vs (z) — does the contract distinguish them? Is the absence of a pin a MISSING pin?** NO, the contract does NOT distinguish them, and **YES, it is a missing pin.** (x) [correct], (y) [WB6], and (z=root-only) [WB5] ALL pass the current 18 pins. The contract author was RIGHT to defer while the point was under-specified (over-pinning an unruled design point is the C-DEF trap). But the **operator has now ruled (x)**, which removes the deferral justification and makes (x) mechanically pinnable — MP-1 + MP-2 are the two pins that enforce it. Ship them, or a builder implements (y)/(z) exactly as under-specified and the cold audit (which checks code-against-contract) cannot see it.

---

## Wrong-build matrix (real output; harness = `run_all.sh`, pasted in Appendix)

```
=== v2-correct                       => 18 passed                 (satisfiability ✓)
=== v1-current                       => 4 failed, 14 passed        (RED control; author's claim reproduced, right reason)
--- attacks the contract DEFENDS ---
=== wb1-contract-exists-allow        => 5 failed, 13 passed        RED incl. pin-1 positive control
=== wb2-null-but-hardcoded           => 2 failed, 16 passed        RED: custom-present, reach
=== wb3a-drop-worktree               => 1 failed, 17 passed        RED: worktree regression
=== wb3b-drop-archive                => 1 failed, 17 passed        RED: archive regression
=== wb4-set-e-crash                  => 3 failed, 15 passed        RED: both garbage pins (exit-code leg)
=== wb8-unbound-crash                => 11 failed, 7 passed        RED incl. assert_no_shell_error firing (P0 control)
=== wb9-artifact-or-empty            => 2 failed, 16 passed        RED: both null pins (null direction guarded ✓)
=== wb11-teammate-only-path          => 4 failed, 14 passed        RED: widening pins (path is pinned ✓)
--- wrong builds that SURVIVE (the INSUFFICIENT basis) ---
=== wb5-custom-root-only             => 18 passed                 SURVIVES -> MP-1
=== wb6-custom-archive-basename      => 18 passed                 SURVIVES -> MP-2
=== wb7-missingkey-owes-nothing      => 18 passed                 SURVIVES -> MP-3
=== wb10-custom-wakeloop             => 18 passed                 SURVIVES -> MP-4
```

## Discriminating-scenario proofs (P2 — each surviving wrong build vs the correct reference, on the fixture I recommend; instrument = `discriminate.sh`)

```
Scenario A — MP-3: {"unrelated":1} contract, reportless
   v2-correct                     exit=2   (spec: missing-key -> v1 default -> nudge)
   wb7-missingkey-owes-nothing    exit=0   (wrong: owes-nothing)                       => DIVERGE

Scenario B — MP-2: custom path present ONLY under receipts/*/<basename>
   v2-correct                     exit=2   (reading x: no archive glob for custom)
   wb6-custom-archive-basename    exit=0   (wrong: archive-basename glob)              => DIVERGE

Scenario C — MP-1: custom path committed at a linked WORKTREE root
   v2-correct                     exit=0   (reading x: root + worktrees)
   wb5-custom-root-only           exit=2   (wrong: root-only)                          => DIVERGE

Scenario D — MP-4: custom-absent, two idles
   v2-correct               first_idle=2 second_idle=0   (one-shot)
   wb10-custom-wakeloop     first_idle=2 second_idle=2   (wake-loop)                   => DIVERGE
```
Every recommended pin discriminates AND the correct-build control matches operator reading (x)/spec (the second P2 leg — without it a "diverging" scenario could just be a botched expectation).

---

## P1b quantifier table (∀-over-inputs vs guarded-by-a-failure-mode; every guarded row carries a receipt)

| # | invariant | ∀ or guarded | receipt |
|---|-----------|--------------|---------|
| I1 | owes-nothing (`null`) → exit 0 | ∀ over idle-count (first/repeat) + no-marker-consumed | SAFE — WB1 & WB9 both redden |
| I2 | owed-report-missing → nudge (positive control) | ∀ (value-keyed) | SAFE — WB1 reddens |
| I3 | custom-present → exit 0 | **GUARDED by location = root only** | **MISSING (MP-1)** — WB5 survives (custom@worktree unpinned) |
| I4 | custom-absent → nudge | **GUARDED to first idle only** | **MISSING (MP-4)** — WB10 survives (2nd-idle wake-loop) |
| I5 | absent contract → v1 default | ∀ (report-present→0 AND reportless→2 both pinned) | SAFE |
| I6 | malformed → v1 default | garbage & empty ∀; **missing-key sub-case GUARDED by report-present** | **MISSING (MP-3)** — WB7 survives |
| I7 | reach = declared value tracked | value ∀, but **GUARDED by location = root only** | **MISSING (MP-1/MP-2)** — WB5/WB6 survive |
| I8 | regressions B1–B6 (default path) | ∀ on default path | SAFE — WB3a/WB3b redden |

## P1c reach table (the contract's INSTRUMENT-0 guard + the guards it relies on; legs = EMPIRICAL, whole contract is in-tree)

| instrument | site-SET it must cover | reach DERIVED or hand-list | coverage a CHECKED variable? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|---|
| **pin 6 `TestReachIsCheckedVariable`** | the hook's resolution of the declared artifact across {root, archive, worktree} | value is varied (A.md/B.md — not a hidden constant), **but the LOCATION set is a hidden constant = root only** | **NO** — no pin reddens when a build honors the value at root yet ignores it at worktree/archive | effect (exit code) ✓ | n/a (single hook) | **MISSING PIN** — WB5 (root-only) & WB6 (archive-basename) both pass 18: they honor the declared value at root and diverge from (x) elsewhere. Empirical. |
| `assert_no_shell_error` | crash modes on the malformed/absent paths | hand-list of 2 stderr tokens (`unbound variable`, `syntax error`) | partial; the real crash guard is the exit-code assert | proxy (stderr tokens) — misses `jq:`/`set -e` exits; those caught by exit-code | n/a | note N1 — over-promises but not a hole (exit-code covers escapes). Empirical: WB4 (token miss, exit-code catch), WB8 (token hit). |
| `TestHarnessProvenance` | the single hook file under test | DERIVED (byte-equality vs HOOK_SOURCE) | yes (byte compare) | effect | n/a | SAFE |

Legs run: **EMPIRICAL** for every instrument (the whole contract is in-tree, so each guard got the wrong-build treatment). Each negative is paired with a positive control (P0): the correct reference build for every discrimination; WB8 for `assert_no_shell_error`; WB1 for the pin-1 positive control; WB9 for the null pins.

---

## Corpse / orphaned-virtue sweep (P6, P6b)
- **P6 (assertions pinning the OLD world):** the contract is NET-NEW (`scripts/test_teammate_idle_gate.py`, untracked); it introduces no assertion that pins retired behavior — the v1 branches it pins (B1–B6) are behaviors v2 must PRESERVE (a pure widening), not a corpse. No corpse hits.
- **P6b (orphaned virtues of code being changed):** v2 is a pure widening of the hook — the only "replaced" behavior is the hardcoded `REPORT-<name>.md` reach, which the widening pins (custom/reach) explicitly retire and re-pin. Two v1 observable behaviors are NOT fully carried into the new pins: the **nudge message prose** (N2) and the **one-shot semantics on the new custom path** (MP-4). MP-4 is a blocker-basis miss; N2 is a low-severity note.

## RED honesty (P7) — reproduced
Ran the contract against the current v1 hook @ `299e69a`: **4 failed, 14 passed**, identical set and reasons to the author's claim (null-exemption ×2, custom-present, reach). Each RED fails because v1 ignores the contract and nudges where correct-v2 allows — the RIGHT reason (not an import/fixture/path error; the failure messages show the real nudge stderr). Correct reference build flips exactly those 4 to green with the 14 unchanged → 18 passed (the C-DEF satisfiability receipt: a known-correct build goes 0-failed).

## Provenance (which tree was tested)
- The contract resolves its hook as `HOOK_SOURCE = REPO_ROOT/.claude/hooks/teammate-idle-gate.sh` where `REPO_ROOT = Path(__file__).resolve().parent.parent`. I copied the contract to `/tmp/adv-idlegate-05b/scripts/`, so `REPO_ROOT = /tmp/adv-idlegate-05b` and `HOOK_SOURCE = /tmp/adv-idlegate-05b/.claude/hooks/teammate-idle-gate.sh` (printed and verified). Every variant run swaps that exact file before invoking pytest; `TestHarnessProvenance` (which the reference build passes) asserts the per-test sandbox copy equals `HOOK_SOURCE` bytes — so the bytes under test are the bytes I placed, per run.
- **No `loremaster.__file__` receipt exists because the contract imports NO workspace member** (only `json/shutil/subprocess/uuid/dataclasses/pathlib/pytest`); it drives the hook purely via `subprocess.run(["bash", …])`. The #140 `.pth`/`__pycache__` poison class is therefore structurally unreachable here, which is why I did not run `scratch_copy.sh` (it would `uv sync --all-packages` for a test that imports nothing — pure wall-clock). The identity-of-code-under-test is the `HOOK_SOURCE` path, which I control and printed. Real hook untouched: `git status --porcelain -- .claude/hooks/teammate-idle-gate.sh` empty.

## Tool honesty
- lore code-structure tools (search/impact/get_symbol) were **not applicable and not used**: the graded artifact is a bash hook + a self-contained pytest file with no symbol graph, consumer-set, or covering-test question. No fallback-to-grep to disclose (I read the four named files directly and built empirical probes — the correct instrument for a "does this contract discriminate" question). Registered on `lore_comms` (session packet-05b, role auditor) per brief; no lore friction encountered to file.

---

## Appendix — instruments (pasted verbatim per brief-base §1; scratch is disposable)

Scratch root `/tmp/adv-idlegate-05b/` — layout: `scripts/test_teammate_idle_gate.py` (copy of the contract @299e69a), `.claude/hooks/teammate-idle-gate.sh` (swapped per run), `hooks_variants/*.sh`, `run_all.sh`, `discriminate.sh`.

### run_all.sh (the harness)
```bash
#!/bin/bash
set -u
REPO=/home/ejprice/PycharmProjects/lore
SCRATCH=/tmp/adv-idlegate-05b
HOOK="${SCRATCH}/.claude/hooks/teammate-idle-gate.sh"
TEST="${SCRATCH}/scripts/test_teammate_idle_gate.py"
for variant in "$@"; do
    cp "${SCRATCH}/hooks_variants/${variant}.sh" "${HOOK}"
    out=$(cd "${SCRATCH}" && uv run --project "${REPO}" pytest "${TEST}" -o addopts= -p no:cacheprovider -q 2>&1)
    summary=$(printf '%s\n' "${out}" | grep -E '^[0-9]+ (passed|failed)|passed|failed' | tail -1)
    failed=$(printf '%s\n' "${out}" | grep -E '^FAILED ' | sed 's#scripts/test_teammate_idle_gate.py::##' | paste -sd' ' -)
    printf '=== %-32s => %s\n' "${variant}" "${summary}"
    [ -n "${failed}" ] && printf '        RED: %s\n' "${failed}"
done
```

### v2-correct.sh (reference build — §Q2 + operator reading x; the satisfiability leg and every discrimination's control)
```bash
#!/bin/bash
set -u
hook_input=$(cat)
teammate_name=$(jq -r '.teammate_name // .teammate // .agent_name // .name // empty' <<<"${hook_input}" 2>/dev/null)
session_id=$(jq -r '.session_id // "nosession"' <<<"${hook_input}" 2>/dev/null)
[ -z "${teammate_name}" ] && exit 0
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
report_name="REPORT-${teammate_name}.md"
marker_dir="/tmp/claude-idle-gate-$(basename "${repo_root}")"
contract_file="${marker_dir}/${session_id}-${teammate_name}.contract"
owed_path="${report_name}"; use_archive_glob=1
if [ -f "${contract_file}" ] && jq -e 'has("artifact")' "${contract_file}" >/dev/null 2>&1; then
    if jq -e '.artifact == null' "${contract_file}" >/dev/null 2>&1; then exit 0; fi   # owes nothing
    declared=$(jq -r '.artifact' "${contract_file}" 2>/dev/null)
    if [ -n "${declared}" ]; then owed_path="${declared}"; use_archive_glob=0; fi        # custom: root+worktrees only
fi
[ -f "${repo_root}/${owed_path}" ] && exit 0
if [ "${use_archive_glob}" -eq 1 ]; then
    compgen -G "${repo_root}/docs/plans/v2/receipts/*/${owed_path}" >/dev/null 2>&1 && exit 0
fi
while IFS= read -r worktree_root; do
    [ -n "${worktree_root}" ] && [ -f "${worktree_root}/${owed_path}" ] && exit 0
done < <(git -C "${repo_root}" worktree list --porcelain 2>/dev/null | awk '/^worktree /{ sub(/^worktree /, ""); print }')
marker_file="${marker_dir}/${session_id}-${teammate_name}.nudged"
[ -f "${marker_file}" ] && exit 0
mkdir -p "${marker_dir}"; touch "${marker_file}"
echo "idle-gate: REPORT-${teammate_name}.md is not at the repo root. If your task is complete, write your report and transition your ledger item now, per your brief. If you are mid-work or waiting on a background process, continue as you were. (One-time automated nudge — it will not repeat.)" >&2
exit 2
```

### The 4 SURVIVING wrong builds (the load-bearing holes) — WRONG line marked

**wb5-custom-root-only.sh** (MP-1): after `declared=…; if [ -n "${declared}" ]; then`
```bash
        owed_path="${declared}"; use_archive_glob=0; use_worktree=0   # WRONG: root-only for custom
```
…and the worktree loop is guarded by `if [ "${use_worktree}" -eq 1 ]`, so a custom path never reaches it.

**wb6-custom-archive-basename.sh** (MP-2): custom sets `glob_name="$(basename "${declared}")"` and then
```bash
compgen -G "${repo_root}/docs/plans/v2/receipts/*/${glob_name}" >/dev/null 2>&1 && exit 0   # WRONG: archive glob for custom
```

**wb7-missingkey-owes-nothing.sh** (MP-3): the natural naive parse
```bash
declared=""
[ -f "${contract_file}" ] && declared=$(jq -r '.artifact' "${contract_file}" 2>/dev/null)  # "null" for null AND missing-key
case "${declared}" in
    "")     : ;;                # unparseable/absent -> v1 default
    "null") exit 0 ;;           # WRONG: missing-key ALSO lands here
    *)      owed_path="${declared}"; use_archive_glob=0 ;;
esac
```

**wb10-custom-wakeloop.sh** (MP-4): after resolution fails, for a custom path
```bash
if [ "${is_custom}" -eq 1 ]; then
    echo "idle-gate: …(nudge)" >&2 ; exit 2   # WRONG: no one-shot marker for custom -> nudges forever
fi
```

### discriminate.sh (the P2 discrimination harness — full source)
```bash
#!/bin/bash
set -u
VAR=/tmp/adv-idlegate-05b/hooks_variants
BASE=/tmp/adv-idlegate-05b/scen
mkdir -p "${BASE}"
run_hook() { local hook_src="$1" root="$2" sess="$3" who="$4"
    mkdir -p "${root}/.claude/hooks"; cp "${hook_src}" "${root}/.claude/hooks/teammate-idle-gate.sh"
    printf '%s' "{\"teammate_name\":\"${who}\",\"session_id\":\"${sess}\"}" \
        | bash "${root}/.claude/hooks/teammate-idle-gate.sh" >/dev/null 2>/dev/null
    printf 'exit=%s' "$?"; }
marker_dir_for() { printf '/tmp/claude-idle-gate-%s' "$(basename "$1")"; }
# Scenario A — WB7 missing-key reportless
for build in v2-correct wb7-missingkey-owes-nothing; do
    root="${BASE}/A-${build}"; sess="s$(printf '%s' "$build" | cksum | cut -d' ' -f1)"; who="wA${build:0:4}"
    md=$(marker_dir_for "${root}"); mkdir -p "${md}"; printf '%s' '{"unrelated": 1}' > "${md}/${sess}-${who}.contract"
    printf '   %-30s %s\n' "${build}" "$(run_hook "${VAR}/${build}.sh" "${root}" "${sess}" "${who}")"; done
# Scenario B — WB6 custom under archive basename
for build in v2-correct wb6-custom-archive-basename; do
    root="${BASE}/B-${build}"; sess="s$(printf '%s' "$build" | cksum | cut -d' ' -f1)"; who="wB${build:0:4}"
    md=$(marker_dir_for "${root}"); mkdir -p "${md}"; printf '%s' '{"artifact": "docs/design/FOO.md"}' > "${md}/${sess}-${who}.contract"
    mkdir -p "${root}/docs/plans/v2/receipts/2026-08-11-x"; printf '# r\n' > "${root}/docs/plans/v2/receipts/2026-08-11-x/FOO.md"
    printf '   %-30s %s\n' "${build}" "$(run_hook "${VAR}/${build}.sh" "${root}" "${sess}" "${who}")"; done
# Scenario C — WB5 custom at worktree
for build in v2-correct wb5-custom-root-only; do
    root="${BASE}/C-${build}"; sess="s$(printf '%s' "$build" | cksum | cut -d' ' -f1)"; who="wC${build:0:4}"; mkdir -p "${root}"
    git init -q "${root}"; git -C "${root}" -c user.email=t@t -c user.name=t -c commit.gpgsign=false commit -q --allow-empty -m init
    wt="${root}-wt"; git -C "${root}" -c user.email=t@t -c user.name=t worktree add -q -b "wt-${build:0:4}" "${wt}"
    mkdir -p "${wt}/docs/design"; printf '# r\n' > "${wt}/docs/design/FOO.md"
    md=$(marker_dir_for "${root}"); mkdir -p "${md}"; printf '%s' '{"artifact": "docs/design/FOO.md"}' > "${md}/${sess}-${who}.contract"
    printf '   %-30s %s\n' "${build}" "$(run_hook "${VAR}/${build}.sh" "${root}" "${sess}" "${who}")"
    git -C "${root}" worktree remove --force "${wt}" 2>/dev/null || true; done
# Scenario D (one-shot on custom path) run inline in the report's Bash step, two idles per build.
```

---

## VERDICT: **CONTRACT INSUFFICIENT**
Four wrong builds pass all 18 pins (WB5/WB6/WB7/WB10). The contract is strong on the attacks the author anticipated (attacks 1–4 all defended, satisfiability proven, RED honesty confirmed, path-scoping and null-direction both pinned), but the **residual-1 custom-path resolution — now RULED (x) by the operator — is unpinned in both the worktree (MP-1) and archive (MP-2) directions**, the **missing-`artifact`-key case cannot discriminate on the reportless path (MP-3)**, and the **one-shot marker is unpinned on the custom nudge path (MP-4)**. Add MP-1..MP-4 (each with the discriminating fixture proven above); re-run the adversary on the revised contract before the builder greens it (no revision skips the adversary — CLAUDE.md).

---

# DELTA RE-GRADE — revised contract r2 (23 pins), graded 2026-08-11

Graded: `299e69a` · HEAD-at-report: `299e69a` · SAME. Contract file `scripts/test_teammate_idle_gate.py` at its untracked `??` r2 state (23 pins; the author added MP-1..MP-4 + N1/N2 and an `IDLE_GATE_HOOK` env override). Same scratch (`/tmp/adv-idlegate-05b/`); re-graded by running the REAL repo contract against each build via `IDLE_GATE_HOOK=<variant> uv run pytest scripts/test_teammate_idle_gate.py` (harness `run_r2.sh`, pasted below). Real hook still untouched.

## r2 SUMMARY
- **VERDICT (r2): CONTRACT INSUFFICIENT — by ONE new survivor.** The four r1 holes are CLOSED (MP-1..MP-4 each redden their target wrong build); satisfiability holds (v2-correct → 23/23); N1/N2 are sound and non-brittle. But a fresh-class survivor appeared — the exact "fix wave adds a survivor" risk the lead named.
- **NEW MISSING PIN (ND-1):** MP-2 tests only the **basename** archive-glob reading; a hook that archive-globs a custom path by its **FULL declared relative path** (`receipts/*/docs/design/FOO.md`) — the reading the author's OWN residual-1 named FIRST, and the most natural v1-pattern reuse — passes all 23 pins while violating operator reading (x). Reproduced: `wb-r2-fullpath-archive.sh` → **23 passed**; discrimination scenario E: correct(x) → exit 2, wrong → exit 0.
- **Cheap, proven fix:** extend `test_mp2_custom_artifact_under_archive_basename_still_nudges` to place the custom file under `receipts/<dir>/` in BOTH layouts — the basename (`FOO.md`, already there) AND the full declared path (`docs/design/FOO.md`) — and keep `assert_nudged`. Proven (scenario F): correct → 2 (GREEN), wb6 → 0 (RED), wb-r2-fullpath → 0 (RED). One fixture line; no new test needed.
- **STOP-rule note (reach attack, CLAUDE.md):** two archive-glob readings are natural (basename, full-relative-path); the two-placement fixture closes BOTH. Deeper/exotic globs (`receipts/*/*/…`) are adversarial-only — do NOT chase them with more fixtures; if the author wants belt-and-braces, a one-line note that the custom branch sets `use_archive_glob=0` (a code-visible constant) is the property-form guard, and a pinned bound with a re-open trigger covers the rest. Right-size: this is one surface, one fixture line — not a new wave.

## Requirement 1 — MP-1..MP-4 KILL WB5/WB6/WB7/WB10 (confirmed, real output via `run_r2.sh`)
```
=== v2-correct                    => 23 passed                 (satisfiability ✓; N1/N2 do NOT false-positive)
=== v1-current                    => 5 failed, 18 passed        RED: null×2, custom-present, MP-1, reach (matches author's r2 claim)
=== wb5-custom-root-only          => 2 failed  RED: test_mp1_custom_artifact_at_worktree_root_is_allowed (+N2*)     -> MP-1 KILLS WB5
=== wb6-custom-archive-basename   => 2 failed  RED: test_mp2_custom_artifact_under_archive_basename_still_nudges (+N2*) -> MP-2 KILLS WB6
=== wb7-missingkey-owes-nothing   => 2 failed  RED: test_mp3_missing_artifact_key_reportless_nudges (+N2*)          -> MP-3 KILLS WB7
=== wb10-custom-wakeloop          => 2 failed  RED: test_mp4_custom_absent_one_shot_then_allowed (+N2*)             -> MP-4 KILLS WB10
```
`*` Each wb ALSO reddens `test_nudge_message_carries_anti_crywolf_softener` — INCIDENTAL: my r1 wb stubs echo a truncated `(nudge)` message, so the new N2 softener pin catches them too. This is noise for the MP conclusion (each MP independently reddens on its own exit-code scenario) AND side-evidence that N2 discriminates a dropped-softener build.

## Requirement 2 — new holes the revision introduced
- **ND-1 (the survivor, above):** full-path archive glob for custom. `wb-r2-fullpath-archive` → **23 passed**. Scenario E receipt: `v2-correct exit=2` vs `wb-r2-fullpath-archive exit=0` on a custom file present ONLY at `receipts/<dir>/docs/design/FOO.md`.
- **N1 is SOUND, not brittle (positive control):** `wb-r2-jqleak.sh` — a build that fail-opens with the CORRECT exit codes but does not suppress jq stderr — fails EXACTLY `test_garbage_json_with_root_report_is_allowed` + `test_garbage_json_reportless_nudges_without_crashing`, via `assert_no_shell_error` ALONE (full message kept, so N2 does not fire; exit codes correct, so the exit-code leg does not fire). So the broadened token set (`jq:`, `command not found`, case-insensitive) catches a real leak class the exit-code guard cannot, and does NOT false-positive on the correct build (23/23). No brittleness.
- **N2 minor coverage gap (note, not blocking):** the softener pin fires only on the DEFAULT nudge path (`test_nudge_message_carries_anti_crywolf_softener` uses no-contract/no-report). A build that keeps `continue as you were` on the default nudge but drops it on the CUSTOM/MP nudge paths passes. Low severity (the message is one shared `echo` in the natural build); optional to widen. Single-substring, so not brittle.
- **Marginal (note only, not built — STOP rule):** the one-shot marker is pinned on the default path (B5/B6) and the custom-absent path (MP-4) but NOT on the "contract declares `REPORT-<name>.md` that is missing" positive-control path (single idle). Contrived to break in a natural build (shared marker logic); flagging for completeness, not recommending a pin.

## Requirement 3 — satisfiability + originals hold
- **v2-correct → 23/23** (0-failed reference build; the r1 C-DEF satisfiability receipt extends to r2). N1's broadened tokens and N2's softener both pass on the correct build.
- **Original 18 behaviors all still GREEN on the correct build** (regressions B1–B6 incl. worktree/archive via the shared `make_git_worktree` helper, null exemption ×2 + positive control, custom present/absent, absent-contract fail-open ×2, malformed fail-open incl. the honestly-relabelled report-present missing-key case, reach). No regression from the revision.
- **All r1 caught-builds stay caught under r2** (`run_r2.sh`): wb1 (9 failed), wb2 (4), wb4 (6), wb8 (16), wb9 (3), wb11 (6) — each reddens ≥1 pin.

## r2 VERDICT: **CONTRACT INSUFFICIENT** (one cheap, proven fixture fix from SUFFICIENT)
Close ND-1 by placing the custom file under `receipts/<dir>/` in the full-declared-path layout as well as the basename in `test_mp2_custom_artifact_under_archive_basename_still_nudges` (proven in scenario F to catch both readings while the correct build passes). No other new hole; MP-1/MP-3/MP-4, N1, satisfiability, and every r1-confirmed property hold. After that fixture line the contract is SUFFICIENT on everything I can construct — re-run is a 1-line delta, not a fresh wave.

### DELTA instruments (pasted verbatim; scratch is disposable)
```bash
# run_r2.sh — grade the REAL r2 contract against a variant via the new env override
REPO=/home/ejprice/PycharmProjects/lore; TEST="${REPO}/scripts/test_teammate_idle_gate.py"
for variant in "$@"; do
  out=$(cd "${REPO}" && IDLE_GATE_HOOK="/tmp/adv-idlegate-05b/hooks_variants/${variant}.sh" \
        uv run pytest "${TEST}" -o addopts= -p no:cacheprovider -q 2>&1)
  printf '=== %-34s => %s\n' "${variant}" "$(printf '%s\n' "${out}" | grep -E 'passed|failed' | tail -1)"
  printf '%s\n' "${out}" | grep -E '^FAILED ' | sed 's#.*::##' | paste -sd' ' -
done
```
```bash
# wb-r2-fullpath-archive.sh — the ND-1 survivor: correct v2 EXCEPT the custom branch leaves
# use_archive_glob=1, so the resolver runs  compgen -G receipts/*/${owed_path}  with
# owed_path=docs/design/FOO.md  (full-path archive glob for a custom path — forbidden by x).
# Full nudge message retained so it does NOT trip N2. Result: 23 passed.
```
```bash
# Scenario E (ND-1 divergence) and Scenario F (recommended fix discriminates both readings):
# E: contract {"artifact":"docs/design/FOO.md"}; place ONLY receipts/<d>/docs/design/FOO.md
#    -> v2-correct exit=2, wb-r2-fullpath exit=0.
# F: same contract; place receipts/<d>/FOO.md AND receipts/<d>/docs/design/FOO.md, assert nudge
#    -> v2-correct exit=2 (GREEN), wb6 exit=0 (RED), wb-r2-fullpath exit=0 (RED).
```

---

# DELTA-2 CONFIRM — ND-1 fixture landed (2026-08-11)

Author extended `test_mp2_custom_artifact_under_archive_basename_still_nudges` to place the custom file under `receipts/*/` in BOTH layouts (basename `FOO.md` + full `docs/design/FOO.md`), `assert_nudged` kept, STOP-rule documented in the docstring. Re-graded the REAL fixed contract (`run_r2.sh`, `IDLE_GATE_HOOK` override); still 23 pins.

- **(a) ND-1 KILLED:** `wb-r2-fullpath-archive` → **1 failed, 22 passed** — RED on exactly `test_mp2_custom_artifact_under_archive_basename_still_nudges` (full message kept, so the kill is targeted, not an N2 artifact).
- **(b) satisfiability:** `v2-correct` → **23 passed**.
- **(c) no other hole / no regression:** `v2-correct` is the ONLY build that passes 23. `wb6-custom-archive-basename` still reddens MP-2 (basename reading still caught); `wb5`→MP-1, `wb7`→MP-3, `wb10`→MP-4, `wb-r2-jqleak`→N1 garbage pins, `wb1/wb2/wb9/wb11` all still caught; `v1-current` unchanged (5 RED/18 GREEN). The extra archive placement can only ADD reddening for a globbing build and cannot affect the non-globbing correct build (custom branch sets `use_archive_glob=0`) — confirmed empirically.
- STOP-rule (operator-adopted into the MP-2 docstring): deeper/exotic archive globs (`receipts/*/*/…`) are the accepted PINNED BOUND — not chased.

## FINAL VERDICT (r2, fixed): **CONTRACT SUFFICIENT**
Every wrong build I can construct is now caught; the correct reference build is 0-failed at 23/23; the two natural archive-glob readings are both closed and deeper ones are a documented pinned bound. No residual. Releases the builder.
