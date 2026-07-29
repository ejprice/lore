# REPORT-design-sidecar-44-1 — packet 44 design consult (Q1–Q4)

brief-base v9 read

## SUMMARY BLOCK
- state: done (initial deliverable; STANDING BY for follow-ups)
- deviations: none. Capability check: full toolset present; all probes ran. Read-only on the repo honoured.
- Packages considered: markdown-it-py (read: pyproject dev-group adoption comment + #270's probe receipts) → `keep_with_trigger` — trigger = "a future packet promotes a battery grader to scripts/", already named in the archived README; tomllib (read: `scripts/registration_sites.py::declared_members`) → `replace` (use it for all pyproject reads in the Q3 instrument); bash-array parsing of `typecheck.sh` MEMBERS → `bespoke` (one anchored line + loud-fail + cross-check vs workspace members; a full bash parser e.g. `bashlex` would be an install → escalate if ever wanted).
- decisions-needed (operator forks, one line each):
  1. **Q1-fork**: archive the two p8a-era relics out of `docs/eval` (recommended) vs pin a two-name mypy exemption — §Q1.3.
  2. **Q2-fork**: ratify that #270's archive arm was ALREADY TAKEN at `d74e1da` and resolve the finding; packet 44's "adopt the package" scope line is overtaken by events — §Q2.
  3. **skills exec gap**: skills' 117 tests are outside `testpaths` (hand-run idiom only) — one-line fix measured passing from root; approve adding, or pin — §Flags.1.
- receipt pointers: derivation table §GT; mypy control runs §Q1.1; docs/eval registration-sites probe (pasted verbatim) §Q1.4; instrument spec §Q3; sequencing table §Q4.

---

## GT — ground truth, measured 2026-07-29 at `7bd9b4e`

All derivations below are `git ls-files`/`git grep`/config-parse work — **non-symbol textual seams (path membership, config keys), so grep/git is the sanctioned instrument per the dogfood protocol; said out loud here.** lore was used for the findings ledger (#188 #233 #238 #261 #270 read in full). No index-derived claim below, so no reconcile was needed.

Tracked `.py` by gate coverage (typecheck roots parsed from `typecheck.sh` MEMBERS = lorerunes lorescribe loresigil loremaster skills; testpaths parsed from `pyproject.toml`):

| class | files | verdict |
|---|---|---|
| under a typecheck member | 268 (lorerunes 3, lorescribe 27, loresigil 35, loremaster 171, skills 12) | type-gated ✓ |
| `scripts/` (17) | in testpaths since #199; **NOT type-gated** | the #188 half-gap, standing disposition: its own work item |
| `docs/eval/` (4) | in testpaths since #238; **NOT type-gated** | the #261 half-gap — Q1 |
| `docs/plans/v2/receipts/**` (19, incl. the 5 consult tools) | neither gate | **the archived-receipts class — deliberately ungated by repo law** (ruff `extend-exclude` rationale) |
| anything else | **ZERO** | fully-ungated set outside the receipts class is EMPTY at `7bd9b4e` |

Two half-gaps in the OTHER direction (type-gated, exec-ungated), which the packet's stated binary property cannot see (§Q3.2):
- `skills/**` 8 test files (117 tests): outside `testpaths`, run only by the hand-run CLAUDE.md idiom. **Measured 2026-07-29 at `7bd9b4e`: `uv run pytest -q skills/lore-deploy/scripts skills/lore-deploy/tests` from the repo root → 117 passed in 15.14s.** The gap is one line wide.
- `scripts/registration_sites.py` itself has NO `test_*` wrapper and exits 1 on the current tree (20 incomplete sites) — it is a judgment WORKLIST, structurally unable to sit in a pass/fail gate. Its hand-run status should be *stated* (a docstring line), not silently inherited — §Flags.2.

---

## Q1 — #261: the docs/eval type-gate strategy. RULING: (a), leg-scoped, plus archive the relics.

### Q1.1 The mechanism, empirically verified

**Control reconfirmed 2026-07-29 at `7bd9b4e`:** `uv run mypy docs/eval/smoke_p8b.py docs/eval/test_smoke_p8b.py` → **7 errors in 1 file** (all resolution artifacts in `test_smoke_p8b.py`, exactly as #261 measured at `25e2985`).

**Fix verified, same sha:** `MYPYPATH=docs/eval uv run mypy docs/eval/smoke_p8b.py docs/eval/test_smoke_p8b.py` → **`Success: no issues found in 2 source files`**. Putting `docs/eval` on the path makes `smoke_p8b` a top-level module, so the test's `import smoke_p8b` resolves. The smoke is ALREADY strict-clean — the entire cost of the gate is one env var and one runner leg.

**Rider measurement:** `MYPYPATH=docs/eval uv run mypy docs/eval` (whole dir) → **36 errors, ALL in the two p8a-era relics** (`evaluation_harness_p8a.py`, `connections_p8a.py`). Zero in the smoke files. This is what makes the relic question (Q1.3) part of the strategy rather than tidying.

### Q1.2 Why leg-scoped MYPYPATH, not a global `mypy_path` entry

#261's suggested "a `mypy_path` entry" has a sharper form. A **global** `[tool.mypy] mypy_path` entry for `docs/eval` makes `smoke_p8b` type-resolvable in EVERY member's run — so a stray `import smoke_p8b` inside `loremaster` would *type-check* and then `ImportError` in the deployed image. That is a mypy-manufactured **false clear of exactly the #131 shape** (passes on the host, breaks in the artifact). Scoping the path to the docs/eval leg only — in `typecheck.sh`: `MYPYPATH=docs/eval uv run mypy docs/eval` as its own iteration — gives the resolution where it is needed and nowhere else.

- Honours the per-member-iteration law (each leg is its own invocation; `docs/eval` has no `tests/` subdir and no `conftest.py`, so the duplicate-`tests.conftest` hazard does not arise — verified by listing).
- Precedent: R9 already put a non-workspace-member (`skills`) in MEMBERS; the array is really "typecheck roots". A one-word comment update in `typecheck.sh` should say so.
- Cost traded: a dev hand-running `uv run mypy docs/eval` without the env var still sees the 7 phantom errors. Accepted — `scripts/typecheck.sh` is ALREADY canonical by repo law for exactly this class of reason, and the leg's comment should name the env var for the hand-runner.
- **Rider (and pin it like this):** the new leg gets a mutation proof — introduce one deliberate type error in a scratch copy of `smoke_p8b.py`, run `typecheck.sh`, watch the docs/eval leg (and only it) go red, restore. The RED→GREEN pair above (7→0) is the resolution receipt; the mutation proof is the leg-actually-fires receipt. Both belong in the wave report.

### Q1.3 Rejecting (b) and (c)

- **(b) move under a member — REJECTED on receipts, not taste.** #238's RULING 2 reversal is the controlling precedent: porting the smoke's percentile onto `scripts/` made `smoke_p8b.py` depend on an adjacent directory, and **run from a detached path it died on ImportError** while the pre-edit control ran fine. The smoke is deliberately a standalone, detachable instrument pointed at a deployed image; making it a member submodule re-introduces exactly that coupling, permanently. It is also more than "what the strategy demands" (Scope OUT), since (a) is measured to achieve the gate at near-zero cost without moving anything.
- **(c) pinned loud exclusion — REJECTED as strictly dominated.** A pinned exclusion is the correct move when the cure costs more than the disease ("WHEN YOU CANNOT CLOSE A HOLE, PIN IT"). Here the cure is measured at one runner leg + one env var and the smoke is already clean. Pinning a closable hole at that price would be recording a bound that isn't one.

**The relic fork (operator decision 1).** `docs/eval` holds two populations: the LIVE deploy instrument (`smoke_p8b.py`, `test_smoke_p8b.py`, plus two `.json` receipts the smoke reads via `Path(__file__).with_name(...)` — those stay) and **p8a/p8d-era archived records** (`connections_p8a.py`, `evaluation_harness_p8a.py`, the four `.md` baselines/raws; July 4–6 vintage, 36 mypy errors, referenced by nothing live — verified: `smoke_p8b.py` cites `connections_p8a` in PROSE only, "modeled on", and nothing outside `docs/eval`+receipts names either file). Recommended: `git mv` the six relics to `docs/plans/v2/receipts/2026-07-04-p8a/` with a `d74e1da`-style README base-path note, and update the smoke's 3–4 prose citations. Then `uv run mypy docs/eval` is clean WHOLESALE and the gate needs no per-file carve-out. The alternative — a two-name `[[tool.mypy.overrides]] ignore_errors` block — works but embeds an enumerated forbidden-list in config (the instrument lesson's losing shape) and leaves dead code in a live tree lore will eventually index (#260). **This is a file move, so it is surfaced as a fork, not assumed: I read Scope OUT ("no restructuring where the smoke LIVES beyond what the strategy demands") as satisfied — the smoke does not move; the strategy demands the tree it lives in be wholly gateable — but that reading is the operator's to confirm.**

### Q1.4 The `:!docs/eval` exclusion in registration_sites.py — RULING: remove it entirely

Its stated reason ("archived-records tree") is false for the live half, as #261 measured. And removal is **measured free**: I ran the REAL script's own functions with only the exclusion narrowed —

```python
#!/usr/bin/env python3
"""Probe: what would registration_sites.py report from docs/eval if `:!docs/eval` were dropped?

Uses the REAL script's own functions (no reimplementation — ONE IMPLEMENTATION law);
only the module-level _EXCLUDED constant is overridden, narrowed to keep the receipts
exclusion but drop the docs/eval one. Output is the docs/eval-only site list.

Probe for REPORT-design-sidecar-44-1.md (design consult, packet 44). Read-only on the repo.
"""

import sys
from pathlib import Path

REPO_ROOT = Path("/home/ejprice/PycharmProjects/lore")
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import registration_sites  # noqa: E402

# Drop ONLY the docs/eval exclusion; keep the rest exactly as shipped.
registration_sites._EXCLUDED = tuple(
    pattern for pattern in registration_sites._EXCLUDED if pattern != ":!docs/eval"
)

members = registration_sites.declared_members(REPO_ROOT)
sites = registration_sites.find_sites(REPO_ROOT, members)

eval_sites = [(path, line, named) for path, line, named in sites if path.startswith("docs/eval")]
print(f"docs/eval co-occurrence sites (threshold {registration_sites._MIN_MEMBERS_FOR_A_SITE}, "
      f"window {registration_sites._WINDOW_LINES}): {len(eval_sites)}")
for path, line, named in eval_sites:
    missing = sorted(set(members) - named)
    verdict = f"STALE missing: {', '.join(missing)}" if missing else "ok (names every member)"
    print(f"  {path}:{line}  names {sorted(named)}  ->  {verdict}")
```

**Output, 2026-07-29 at `7bd9b4e`: `docs/eval co-occurrence sites (threshold 3, window 4): 0`.** Zero sites, zero noise. (The member-name hits in docs/eval live overwhelmingly in the p8a-era `.md` raws — which move to receipts under the Q1.3 fork and fall under the already-kept `:!docs/plans/v2/receipts` — and the smoke itself never clusters ≥3 member names within the window; `lorerunes` appears in docs/eval exactly 0 times.) So: delete the pattern, update the `_EXCLUDED` comment (whose "archived records" rationale currently over-claims), one-line change, no new worklist entries. The probe above lives in my scratchpad (disposable by design) and is therefore **pasted verbatim here as the surviving copy**.

---

## Q2 — #270: the consult tools. RULING: the archive fork was ALREADY TAKEN — ratify it, resolve the finding, build nothing.

**Measured 2026-07-29:** the five tools are no longer at the repo root. Commit `d74e1da` (2026-07-28 22:26 −0400, ~1.5h AFTER #270 was filed, ~9.5h BEFORE the sweep routed #270 into packet 44) moved them to `docs/plans/v2/receipts/2026-07-28-packet11ib/consult-11ib/tools/`, with an operator-prompted zero-callers derivation ("searched every reference to each of the five filenames — ZERO invocations") and a README at the arrival address carrying the base-path rule, the deliberately-ungated statement, and the promotion path. **Packet 44's Scope IN line for #270 ("adopt the package, and gate the tools") is overtaken by events — the sweep appears not to have seen `d74e1da`.** Surfacing this as decision 2 rather than silently reconciling.

What remains, and what does NOT:

1. **The bound-pin.** The bound is: *hand-run consult instruments, archived, ungated BY DESIGN, hand-rolled table parsing preserved as-is.* Its pin has three legs, two of which already exist: (i) the README at the only address a future promoter would copy from — the re-open trigger IS named there ("if a future packet needs a battery grader, promote to `scripts/` **then** — with gating, and with the parsing replaced by `markdown-it-py`; scoreboard in `REPORT-exhibit-11ib-1.md` §F1 is the equality oracle"); (ii) the receipts tree's law-backed exclusion from every gate; (iii) **new, from Q3**: the derived invariant's archived-receipts exemption class, whose anti-vacuity assertion (class non-empty, root present in ruff's `extend-exclude`) makes the class's existence a checked fact rather than a comment. A promoted copy that lands anywhere OUTSIDE receipts is caught structurally by the Q3 instrument (it would be new ungated ground) or by the normal gates (if put in `scripts/`, it is type- and test-gated on arrival). The residual door — someone promotes, ignores the README at the directory they are copying from, AND re-hand-rolls the parsing — is a door only deliberately unusual behaviour opens; per "A GATE NEEDS A THREAT MODEL" it is LEDGERED (it is: #270's body + the README), not paid for.
2. **Do NOT do the markdown-it-py swap on the archived copies.** Receipts are preserved BYTE-FAITHFUL by repo law (the ruff-exclude rationale: "a receipt that has been reformatted is no longer evidence of the run it documents"). Editing the archived graders' parsing would falsify the instruments behind the published scoreboard. The swap belongs to the promotion event, if it ever comes, with §F1 as the equality oracle — exactly as the README says. Verified there is no LIVE copy of the hand-rolled idiom left to fix: `git grep 'strip("|")' -- '*.py' ':!docs/plans/v2/receipts'` → zero hits (2026-07-29 at `7bd9b4e`).
3. **Bookkeeping**: resolve #270 citing `d74e1da` + the README path + this section; the resolution note should state explicitly that "adopt the package" was discharged as `keep_with_trigger`, not as a swap.

**If the operator instead rules PROMOTE** (rejecting the standing archive): that is un-archiving + gating + the oracle-tested swap — a design-plus-build item that CANNOT fit packet 44's 0.15 wu beside Q3; it would be a minted sibling packet. The oracle test would parse the §F1 scoreboard table with BOTH parsers over the archived exhibit corpus and assert identical grade tuples, with #270's escaped-pipe-in-code-span sample as the discriminating fixture (the case where the two parsers measurably disagree — a fixture that cannot tell them apart is decoration).

---

## Q3 — the DERIVED invariant. Design: `scripts/test_gated_ground.py`.

### Q3.1 Form and home

**One pytest file, `scripts/test_gated_ground.py` — the test IS the instrument.** Not a script-with-wrapper: a wrapper is a seam where step N (the script) can silently no-op while step N+1 (the wrapper) still prints green — the exact two-step failure "FILING A RULE DOES NOT INSTALL IT" documents (`mutation_proof` piped to `tail` under `set -e`). `registration_sites.py` is a script because its output is a judgment worklist that exits 1 on a healthy tree; this instrument is the opposite — a pass/fail invariant that must sit GREEN in the standard gate and go RED on new ungated ground — so the pytest form is correct and the collection home (`scripts/` is in `testpaths`) gates it from birth, closing the "both newest instruments sat outside testpaths" recurrence by construction. Helper functions stay importable for hand-running; no `main()` required.

### Q3.2 The property, interrogated — the packet's stated property is WRONG as written, and would miss its own history

*"A committed `.py` outside every typecheck member AND outside every testpaths entry"* is a **binary** property. Applied at `7bd9b4e` it flags exactly the receipts class (exempt) and nothing else — it would sit green TODAY over a tree where `scripts/` carries 41 known mypy errors (#188) and skills' 117 tests never run in any gate. **Three of the four historical instances (#188, #233, #261) were HALF-gaps: covered on one axis, naked on the other.** A guard implementing the packet's sentence literally is a wrong build that passes — the first entry in the wrong-build table below. The property must be **per-axis**:

- **LEG A (types)**: every tracked `.py` is under a typecheck root (parsed live from `typecheck.sh`), **or** carries a pinned exemption, **or** is in the archived-receipts class.
- **LEG B (execution)**: every tracked `test_*.py` **and every `conftest.py`** is under a `testpaths` entry (parsed live from `pyproject.toml`), same outs. Scoped honestly: full execution-coverage of NON-test files is a coverage-measurement problem this instrument does not claim — a library file's execution comes via importers and the type gate is the enforceable invariant there. A test file named outside pytest's collection convention (`check_foo.py` full of asserts) is invisible to pytest EVERYWHERE, which is a different defect class; both bounds are stated in the docstring per "state the model IN the instrument".
- The **lore-index axis** (#233/#260's third direction) is explicitly a NAMED BOUND with re-open trigger = #260 landing in 04b-2 (Scope OUT here); one docstring line so the bound is met deliberately.
- **Files inside a member that mypy skips**: today `[tool.mypy]` has no `exclude` and no `ignore_errors` override (verified at `7bd9b4e`). The guard PARSES for both and **fails loud if either ever appears** for a module not in the pinned table — message: "this guard does not model mypy excludes; extend it or remove the exclude." Refusing to mis-model beats silently mis-modelling (#136's shape: never certify what you cannot see).
- **Legitimately-ungated `.py` data/fixtures**: none exist at `7bd9b4e` (the calibration corpus uses `.md.txt` naming precisely to stay out of the gates). If one is ever needed, its home is the pinned-exemption table with the consuming test as evidence — deny-by-default, evidence-backed, per the allowlist law.

### Q3.3 Inputs from the REAL config (the anti-stale-mirror requirement)

- Typecheck roots: regex-parse the single anchored `MEMBERS=(...)` declaration in `scripts/typecheck.sh`. Parse failure or empty result → **hard FAIL** ("cannot find MEMBERS — the guard is blind, not the tree clean"), never a skip.
- Testpaths + workspace members + mypy overrides: `tomllib` over `pyproject.toml` (same instrument `registration_sites.py::declared_members` uses — ONE implementation; the builder should check whether that tiny reader is worth sharing rather than cloning, and escalate per the DRY law rather than quietly writing copy #2).
- **Cross-derivation pin (free, and it closes a real door):** assert parsed typecheck roots ⊇ `[tool.uv.workspace] members`. This makes `typecheck.sh` silently dropping a workspace member a RED test — a registration-sites-class invariant nobody currently checks mechanically.
- Membership tests are **path-component-wise** (`Path.parts` prefix), never `str.startswith` — `scripts_extra/foo.py` must NOT pass as under `scripts` (wrong-build table, row 3).

### Q3.4 Exemptions — allowlist the safe

1. **Archived-receipts class**: exactly one root, `docs/plans/v2/receipts`, hardcoded WITH the law citation — this is a single law-backed address, not a growing list (the stale-mirror hazard is lists that must track other lists). Two pins keep it honest: (i) assert the root appears in ruff's `extend-exclude` (read from pyproject — if the archive tree is ever renamed or the ruff rationale removed, the guard fails loud instead of exempting nothing/the wrong thing); (ii) **anti-vacuity**: assert the class matched ≥1 tracked file (19 at `7bd9b4e`).
2. **Pinned per-file/per-tree exemption table**, each entry = `(root_or_path, axis, finding#, reason, named re-open trigger)`. **At landing it should hold exactly ONE row**: `("scripts", LEG_A, "#188", "41 measured errors, standing disposition: own work item — config half first", trigger="the #188 cleanup lands; delete this row and the leg goes live")` — assuming Q1/skills land as recommended. An exemption row without a finding number and a trigger is rejected by the table's own validation (a trigger nobody names is a hope).
3. `scratchpad/` needs no exemption: the derivation walks `git ls-files`, and untracked ground is out of the threat model by construction.

### Q3.5 Threat model — IN the instrument's docstring

*This gate is for the HONEST ENGINEER who commits a load-bearing `.py` into a tree no gate (or only half the gates) covers, believing the repo's gates see it — #188/#233/#238/#261 verbatim, four instances, each found by someone tripping. It is NOT a security boundary: anyone who can commit can delete this test. Therefore: a deliberately disguised file (`.py.txt`, generated code, an exec'd string) is out of scope and NOT a defect of this gate; a new `tools/` directory of honest Python is exactly in scope, and a false positive on honest archived receipts would get this gate switched off — which is why the receipts class is exempted by law-backed address rather than by anyone's judgment call.*

### Q3.6 "What WRONG build would still pass this?" — answered in writing

| wrong build | caught by |
|---|---|
| implements the packet's literal BINARY property (union of both gate sets) | contract fixture: a tree in `testpaths` but not typecheck roots must flag on LEG A — at `7bd9b4e` `scripts/` itself is that fixture (it must appear as pinned-exempt, not as covered) |
| `str.startswith` membership | fixture with a sibling-prefix tree (`scripts_extra/`) in a scratch repo |
| parses MEMBERS with a pattern that matches nothing → empty roots → everything "outside" → but exemptions eat it / or code treats empty as "no roots configured, pass" | hard-fail-on-empty + the ⊇-workspace-members cross-pin |
| `git ls-files` fails / wrong cwd → empty file list → vacuous green | anti-vacuity: file list non-empty AND every workspace member contributed ≥1 `.py` (derived anchors, not an enumerated one) |
| checks only counts (len parity), not identities | contract pins name EXACT paths in fixtures, small-N ≠ 1 (the C1 lesson: no fixture where `len()` ≡ `sum()`) |
| exemption table entries accepted without finding#/trigger | table-validation pin with a deliberately malformed row fixture |
| honours a future `[tool.mypy] exclude` silently | the fail-loud-on-unmodelled-config pin |

**"If step N silently no-opped, would step N+1 still print something that reads as success?"** — the three subprocess/parse steps (git ls-files, MEMBERS parse, toml read) each terminate in either data-used-by-an-assertion or a raise; there is no step whose silent empty output flows into a green print, because every empty intermediate has its own named assertion (the four anti-vacuity pins above). The contract-adversary should attack exactly this claim (§Q4).

### Q3.7 Failure message — promising only what the assertion performs

> `UNGATED GROUND (LEG A — types): docs/consult/foo.py is a committed .py outside every typecheck root (lorerunes, lorescribe, loresigil, loremaster, skills, docs/eval) and not exempt. This test proves REGISTRATION in the gates' config — it does NOT prove mypy ran or passed; the gate's own exit code proves that. Fix: add its tree to typecheck.sh MEMBERS (its own iteration — read the header), or add a pinned exemption row with a finding number and a named re-open trigger. Do NOT widen the receipts class to admit it.`

(LEG B analogous, naming `testpaths`.) The message states the registration/execution distinction explicitly because that gap is this instrument's own residual bound — a false gate is a message promising a check the assertion does not perform, and "this tree is type-checked" is precisely what this assertion does NOT check.

### Q3.8 Rider — and pin it like this

Every load-bearing pin above ships with a `scripts/mutation_proof.py` run, expected-RED node ids declared from `--collect-only` BEFORE the run, both-ways diff: (m1) remove `docs/eval` from MEMBERS in a scratch copy → LEG A red; (m2) remove a `testpaths` entry → LEG B red; (m3) `git add` a stray tracked `.py` at the scratch repo root → LEG A red; (m4) delete the #188 exemption row → red naming `scripts/`. Scratch copies via `./scripts/scratch_copy.sh` with the provenance receipt printed (#140 law); note m1–m4 mutate CONFIG and tracked-file state, so the scratch tree must be a git repo — `git add` in the scratch is part of the fixture, and the builder must confirm `scratch_copy.sh` preserves a usable `.git` or arrange the fixture repo explicitly (flag for the contract author; I did not verify this property of `scratch_copy.sh`).

---

## Q4 — sizing, sequencing, TDD scope, the balloon line, adversary targets

**Sizing law context: ≤0.25 wu target, split at 0.30 (INDEX, operator-ruled 2026-07-14). Packet 44 is 0.15.**

Landing order (rationale: ground first, instrument LAST and GREEN — #188's own disposition warns that a gate landing red on day one gets switched off):

| step | what | TDD? |
|---|---|---|
| 0 | reconcile sweep-44-1's derivation against §GT; diff, don't merge blindly; sweep files findings (I deliberately filed none to avoid double-rows — §Flags) | — |
| 1 | Q2 ratification: resolve #270 citing `d74e1da` (docs/ledger only) | no |
| 2 | Q1: relic archive (fork 1) + `typecheck.sh` docs/eval leg + `:!docs/eval` removal | config/infra: receipts-based (RED→GREEN 7→0 pair + leg mutation proof), not full TDD |
| 3 | skills `testpaths` addition (fork 3) + CLAUDE.md idiom note update; verify full-suite `-n auto` interaction (my 117-passed run was standalone — the full-suite interaction is UNVERIFIED, builder must run it) | one-line config + suite receipt |
| 4 | the Q3 instrument | **full TDD**: contract → contract-adversary → build → cold audit. The contract is a spec-to-implement (this section), not a property-to-invent — buildable; but note the routing rule: if the builder finds itself INVENTING a property I did not pin, that is an escalation, not a judgment call |
| 5 | findings resolved with receipts, INDEX row + Log | no |

**Ballooned = mandatory split** when any of these fires (each is a fact, not a feel):
1. Operator rules the #188 41-error cleanup lands in-packet (its own standing disposition already says "own work item, ~half a session, NOT folded" — honouring that keeps 44 at size via the exemption pin).
2. Operator rules PROMOTE on Q2 (un-archive + gate + oracle swap ≈ its own packet, §Q2).
3. sweep-44-1 surfaces live trees beyond §GT's table (my derivation found zero, but two independent derivations are DIFFED, never assumed equal).
4. Step 3 fails in full-suite shape (skills tests interact with `-n auto`/importlib in a way a one-line fix can't cover) — then skills becomes a pinned exemption row + its own item, NOT an in-packet rework.
Numerically: the five steps above are ~0.15 wu with the instrument as the only real build; any single added item of build-shape pushes toward 0.25–0.30 and the Entry check's own sentence governs — split before building.

**Contract-adversary frontier (what to attack):** the §Q3.6 wrong-build table row-by-row (it must BUILD them — especially the binary-property build and the empty-MEMBERS-parse build); the §Q3.6 no-op claim (construct each silent-empty state and check the guard's bytes differ from healthy — Leg-2 forgery pins, dependencies {git, typecheck.sh, pyproject} × {empty, missing, malformed, wrong-cwd}); fixture monoculture (fixtures must include: covered-both, type-only, test-only, neither, exempt-class, pinned-exempt, `conftest.py` outside testpaths, sibling-prefix dir); exemption-table validation with a hostile row; and the scratch-git-fixture question flagged in §Q3.8.

---

## Flags & residuals (everything noticed, per scope law — operator owns all of these)

1. **skills exec-axis gap** (§GT): 117 tests outside every gate, hand-run idiom only. Found by this consult's derivation — i.e., the packet's method working before its instrument exists. One-line fix measured passing standalone (2026-07-29 at `7bd9b4e`); full-suite interaction unverified. NOT filed as a finding by me — sweep-44-1 owns filing per the packet's "file BEFORE fixing" line; reconcile at follow-up 1 so exactly one row exists.
2. **`registration_sites.py` is itself hand-run** — no test wrapper, exits 1 on the current tree (20 incomplete sites), so it cannot sit in a pass/fail gate as-is. Recommend one docstring line stating hand-run is DELIBERATE (worklist tool, non-zero exit by design) so the ungatedness is met deliberately; anything more is out of packet 44's scope unless ruled otherwise.
3. **#270's packet text is OBE** (§Q2) — the sweep routed a finding whose recommended arm had already been executed 9.5h earlier. Cheap process note for the sweep protocol: a routing pass should `git log --oneline -- <area>` the finding's area before minting scope.
4. The four p8a-era `.md` files in docs/eval are the same archived-records population as the two `.py` relics — fork 1 should move all six together, or the "archived records live in receipts" rationale stays half-true for docs/eval.
5. My probe (§Q1.4) monkeypatches a private constant of `registration_sites.py` — fine for a consult probe, but if the builder wants the same capability durably, `_EXCLUDED` deserves a parameter, not a doc'd pattern to copy (the #102 law).

---

*Standing by for follow-ups (first expected: sweep-44-1's output). I will answer from loaded context and not re-read the world.*

---

# FU1 ANSWERS (2026-07-29; answered from loaded context per the lead's instruction — NO repo files re-read after the tree change; peer HEAD moved `7bd9b4e → fe576ba → 5a850c3`, work now in worktree `pkt44/ungated-ground` @ `5a850c3`)

## FU1-A — the exemption table: CONFIRMED exactly one row, with one correction to my own draft

One row: `("scripts", LEG_A, #188, trigger = "the #188 cleanup lands; delete this row and the leg goes live")`. Everything else is discharged by the rulings: relics → receipts class; skills → both axes covered (typecheck root + the new testpaths entries); docs/eval → new leg. The row is a TREE ROOT, so `fe576ba`'s new `scripts/forgery_door_sweep.py` + test fall under it automatically — no per-file churn, which is why root-scoped rows are right.

`registration_sites.py` needs **NO LEG_B row**: LEG B quantifies over `test_*.py` and `conftest.py` only, and it is neither. Its never-run-in-a-gate status is the *stated bound* of LEG B (execution of non-test files is not claimed), handled by the Flags.2 docstring line — a table row would promise a check the instrument does not perform (the false-gate law, applied to an exemption).

**Correction to my own §Q3.4 draft (the re-derive law biting me):** I wrote "41 measured errors" into the row's reason text. That count was #188's 2026-07-26 measurement and has ALREADY drifted (lead-measured **45 in 7 files at `5a850c3`**). **The row must carry NO count in its reason** — a finding number and a trigger only; any count appears in a comment, dated and sha'd. An undated count in an exemption row is an inherited number wearing an assertion — the adversary should attack this (FU1-D).

## FU1-B — the three relic-archive consequences

**(i) DESIGN-LAW §6 — path-only edit, no new ruling needed.** Two readings of the "REUSED VERBATIM" pin, converging on the same edit, so no fork: (r1) the mandate is historical (P8d's A/B gate ran 2026-07-06; the reuse it mandated happened) — the citation is provenance, and a path update + "moved 2026-07-29 at `<move-sha>`, content byte-identical (`git mv`), see the receipts README" note preserves it exactly; (r2) the mandate is still live for future A/B gates — then the pin's substance is the ARTIFACT (bytes), not the address, and `git mv` preserves bytes while the path update keeps the address resolvable (#152 class). Either way: path-only edit + dated note, faithful to the pin; the operator's ruling 1 already implies its mechanical citation consequences. List the edit in the wave report for visibility.

**(ii) CONFIRMED — the two `.json` files STAY.** `deploy-receipt-pre-ddl.json` and `deploy-baseline-latency.json` are LIVE inputs read via `Path(__file__).with_name(...)` (`PRE_DDL_RECEIPT_PATH`, `LATENCY_BASELINE_PATH` — measured 2026-07-29 at `7bd9b4e`, symbols not line numbers). They are current-state receipts the smoke consumes, not archived records. The new `2026-07-04-p8a/` README must not name them, and the mover must not sweep `docs/eval/*.json` wholesale — the move list is the SIX named files only.

**(iii) YES — stale prose citations are the P8d natural-language-surface class, and the wave owes the sweep.** In the smoke itself, measured at `7bd9b4e`: `connections_p8a` at lines 15, 24, 242 and `evaluation_harness_p8a` at line 36 (4 prose sites; line numbers will drift — re-grep, don't reuse). **And a deviation of mine to own: my §Q1.3 repo-wide grep was file-type-anchored (`--include='*.py','*.sh','*.toml','*.yaml'`) — it structurally could not see `.md`, and the lead's DESIGN-LAW §6 hit proves the miss.** The rename-sweep law was right and I under-applied it. The wave's sweep must be bare and anchor-free over ALL tracked files, all six moved names:

```
git grep -nI --fixed-strings \
  -e connections_p8a -e evaluation_harness_p8a \
  -e 2026-07-04-p8a-baseline -e p8d-flip-eval-raw -e p8dprime-rerun-raw \
  -- . ':!docs/plans/v2/receipts'
```

(`2026-07-04-p8a-baseline` covers both the digest and the `-raw` file.) Every residual hit gets file:line + an INDIVIDUAL verdict — update (live prose) / leave (inside the moved relics themselves, now archived self-references) — never "all remaining hits are X". Hits already inside receipts are left alone per the `d74e1da` base-path-README convention.

## FU1-C — mutation proofs in a worktree: scratch-git is POISONED; here is the fallback shape

**The specific hazard, worse than "doesn't work": a `cp -a`/`scratch_copy.sh` copy of a WORKTREE copies the `.git` FILE, which names the ORIGINAL repo's absolute gitdir (`gitdir: …/.git/worktrees/pkt44`). Git commands in the scratch then operate on the REAL worktree's index — a scratch `git add` MUTATES THE TREE YOU MEANT TO ISOLATE.** That is #140's poison mode wearing git clothes, and it is silent. So m1–m4 as I drafted them (scratch_copy + git fixtures) are OUT for this packet. Replacement, two legs:

1. **Contract pins run in `tmp_path` git-init fixture repos, and the guard is built for it**: its readers take an explicit `repo_root` parameter (the `registration_sites.py::declared_members` pattern — same idiom, possibly the same shared reader per the DRY escalation in §Q3.3). A fixture repo is `tmp_path` + `git init` + a handful of files + one commit: tiny, fast, fully isolated, no scratch_copy involved. This is the natural home for the stray-tracked-file pin (old m3), the sibling-prefix pin, the empty-MEMBERS pin, the malformed-exemption-row pin — and for m1/m2/m4-shaped config mutations too, since the fixture writes its own `typecheck.sh`/`pyproject.toml`.
2. **The both-ways `mutation_proof.py` receipts run against the REAL worktree with a `cp -a` CONTENT backup + byte-exact restore** — the standing-law "always sound" alternative, unaffected by worktree topology because it never copies `.git` at all. Expected-RED ids declared from `--collect-only` before the run, as ruled. Commit the green state first (commit-at-natural-boundaries), but restore from CONTENT regardless — never `git checkout --` in a tree with uncommitted wave work.

Two worktree facts to keep straight: `git ls-files` INSIDE the worktree is fine (git resolves worktrees natively) — production use of the guard in the worktree is unaffected; only COPIES of a worktree are poisoned. And the builder's + adversary's briefs must carry the scratch-git hazard as a named landmine — an agent that "helpfully" scratch_copies the worktree for a mutation will mutate the real index while its receipts show isolation.

## FU1-D — balloon: UNCHANGED ~0.15 wu (provisional on FU2), adversary frontier grows by three

Net of the rulings: Q2 ratify is CHEAPER than the built alternative; the relic archive adds a bounded mechanical item (6-file `git mv` + README + the (iii) sweep + ≤5 prose-line edits); skills-in-packet adds one `testpaths` line + a CLAUDE.md idiom note + the full-suite `-n auto` run the builder already owed. The instrument remains the only build. ~0.15, ceiling ~0.20 — no split trigger fired. **Provisional**: trigger 3 (sweep-44-1 finds ground beyond my §GT derivation) stays open until FU2; note my §GT is now dated at `7bd9b4e` and the sweep's numbers at the worktree base supersede mine where they differ (two derivations, DIFFED, per §Q4 step 0).

Adversary frontier additions (on top of §Q4's list):
1. **Frozen-count attack**: any count embedded in an exemption row's reason text (per FU1-A) — build the wrong build whose row says "41 errors" while the tree has 45; the contract must reject undated counts structurally (row schema: finding# + trigger, no free numeric claims) or the pin is prose.
2. **Skills growth-case pin**: a fixture repo with a NEW `skills/otherskill/tests/test_x.py` must go RED on LEG B (the two new testpaths entries cover `lore-deploy` only — the guard must catch the next skill, not just this one). Plus the collection≠execution bound: the +117 collected (lead-measured at `5a850c3`) still owes an EXECUTED passed-count under `-n auto` before green is claimed.
3. **Worktree-topology attack on the proofs themselves**: verify the mutation receipts were produced by the content-backup path, not a scratch copy — the receipt to demand is the backup dir listing + byte-exact restore diff, and the ABSENCE of any scratch_copy provenance line for git-touching fixtures (its presence for a git fixture is the FU1-C hazard fingerprint).

**SHA-sensitivity of §GT, restated as asked:** SHA-SENSITIVE (re-derive at the worktree base; builder step 0): all file/error counts (scripts 17→**19** and #188's 41→**45 in 7 files**, both lead-measured at `5a850c3`; member `.py` counts; receipts-class 19; "fully-ungated set EMPTY"), and the three cheap re-run receipts the wave owes in-worktree before relying on them: the MYPYPATH 7→0 pair, the zero-sites probe, the zero-live-handrolled-parsing grep. SHA-STABLE: the `d74e1da` history facts (Q2), the #238-reversal argument against strategy (b), the mechanism claims (leg-scoped MYPYPATH resolution; per-axis property design), and the skills 117-collect result (independently corroborated by the lead at `5a850c3`).

*Standing by for FU2 (sweep-44-1's output).*

---

# FU2 ANSWERS (2026-07-29; adjudication of the sweep contradiction. Evidence basis: my §GT derivation at `7bd9b4e` + the lead's three reproduced mypy shapes and collection probes, lead-measured at `5a850c3` in the provenance-asserted worktree — I did not re-read the moving tree; where I rely on a lead-measured number I say so)

## FU2-A — SIZING VERDICT: ONE PACKET. The lead's reconciliation is correct — and the discount is the OPERATOR'S, not mine.

**Attacking my own number first, as asked.** The honest attacks on ~0.15 wu are: (1) the `.sh` tree — **a bound my report failed to STATE**: my property was silently scoped to `.py`; §Q3.2 states the lore-index and collection-convention bounds but never the shell one. That is a real miss of mine, sweep-caught, and I own it. It does not add weight to THIS packet unless the operator routes it in (C1 below) — but the omission was mine, not a discount. (2) The "CI-shape" Exit line — if it means standing up CI, my number is wrong by an order of magnitude; I read it otherwise (C2), but it is a genuine two-readings fork and goes up as one. (3) The archive could snag on the DESIGN-LAW pin or a larger-than-expected citation sweep — bounded: the sweep command is written (FU1-B.iii) and its hit set is enumerable, not open-ended.

**Why the 87 discounts legitimately.** The sweep's 87 is a true measurement of the tree it saw, but it conflates **two populations with different, already-issued dispositions** — the exact two-populations-in-one-count class (#102/#120, and the archive-law's own receipt):
- **42 (docs/eval, sweep-measured; lead-reproduced at `5a850c3`)**: under the operator's FU1 archive ruling these are not "errors to fix" — 36 of them leave the live tree inside two `git mv`'d relics into the law-backed receipts exempt class, and the remaining 7 (shape A's `test_smoke_p8b` resolution artifacts) are extinguished by the leg-scoped MYPYPATH, control-proven: shape C (`MYPYPATH=docs/eval mypy` on the two smoke files) = **clean**, my measurement at `7bd9b4e`, lead-reproduced at `5a850c3`. Post-ruling docs/eval debt: **zero code fixes**. 44c evaporates.
- **45 (scripts, lead-measured at `5a850c3`)**: kept OUT by #188's own standing disposition ("its own work item, NOT folded into any packet's exit") — the very citation the sweep used to argue balloon is the ruling that keeps this weight out of 44. It rides the one pinned-exemption row. 44d already exists as an owned item; a split row would duplicate it.
- The sweep's remaining partition collapses under the FU1 rulings it could not see: 44b (strategy ruling) was DECIDED (Q1 fork), 44a + 44e ≈ what my §Q4 already scopes. **The surviving content of the sweep's own five-way split is one packet.**

**Verdict: hold at ~0.15–0.20 wu, under the ≤0.25 target**, with the split triggers still armed — and two of them (C1, C2 routed IN) are operator forks that COULD legitimately flip this verdict, which I state rather than pretend the number is unconditional. Discount authority: each subtracted population has an OPERATOR ruling disposing of it — the scope law's own arbiter, not my convenience.

## FU2-B — the recursion (sweep §8.4): REAL, and the fix is a mechanism, not a shrug — a file-scoped MEMBERS entry

The catch is correct: at `scripts/`, the instrument would be collected-but-untyped on day one, sitting under the exemption row it ships. Neither "accept it" bare nor "move its home" survives inspection (moving to a member couples repo-gate tooling into a package; moving to docs/eval is the wrong domain). The fix:

**Add `scripts/test_gated_ground.py` — the FILE — as its own MEMBERS iteration in `typecheck.sh`.** MEMBERS already stopped meaning "workspace members" at R9; an entry that is a file is just a finer iteration, and `uv run mypy scripts/test_gated_ground.py` needs no MYPYPATH **provided the instrument is SELF-CONTAINED (stdlib-only imports)** — which I now rule it should be, refining my own §Q3.3: the builder need NOT share `declared_members` with `registration_sites.py`. The shared POLICY lives in `pyproject.toml` itself (the one registry both read); two 4-line `tomllib` readers of one source are consumers of a registry, not clones of a policy, and the sharing-by-mutation test passes AT THE SOURCE (change `members` → both see it). A cross-file import would force a MYPYPATH leg and a coupling for no policy gain.

This also resolves the guard-vs-reality mismatch mechanically: the guard's LEG A checks every file against ALL parsed MEMBERS entries (an entry covers itself: `path == entry or under it`, component-wise) BEFORE consulting exemptions — so the instrument reads as **covered**, and the #188 row covers only the residue of `scripts/`. Exemptions apply to residue by construction; no special case, no second array. Rider, in the same breath: the file-leg gets the same mutation proof as the docs/eval leg (deliberate type error in the instrument → that leg red → restore), and its comment names the dissolution trigger — *"#188 lands → widen to whole `scripts/`, delete this entry"*.

## FU2-C — one-line recommendations on the five escalations

1. **Shell tree (7 `.sh`, no gate)**: escalate for `shellcheck` install authorization as a **follow-on row** (packages law: never code around the gap with a weaker hand-rolled lint); in 44 the instrument states `.sh` as a NAMED BOUND with that authorization as its re-open trigger — and if authorized, the first step is a MEASUREMENT (run it, count, then size), #188's pattern exactly.
2. **"CI-shape"**: read it as *"the gates pass in a CI-shaped run — clean environment, repo root, the exact commands a CI would issue"* (a 0.15 row cannot have meant "stand up CI"); satisfy with an `env -i`-style clean-shell run receipt in the wave report, and send **"this repo has no CI at all"** up as its own operator question with a finding row — two readings, wildly different sizes, so the fork goes up regardless.
3. **#282**: fix in-packet — the docstring is my Q1's natural-language class in the same tree (one prose edit), and DISCHARGE #198's fired trigger properly with a decision, which I recommend as **keep-the-4th-copy-re-pinned**: the trigger made consolidation *reconsiderable*, but the #238 reversal's actual reason — the smoke must run DETACHED, and a cross-directory import dies on ImportError from a detached path — is a standing functional requirement that gating did not change; record that as the reconsideration's outcome (a dated note on the pin), which is what discharging a trigger means. Also note the ledger nit: #238's resolution CLAIMED this trigger discharged; the sweep shows it wasn't — say so in #282's resolution.
4. **#283**: yes — ONE command before resolving #270: sweep the archived exhibit corpus for pipes inside graded cells (escaped pipes / pipes in code spans); zero hits ⇒ the parse defect was latent and the §F1 scoreboard stands, cited as the resolution receipt; any hit ⇒ STOP, the published number is suspect and that goes up, not into a quiet note. Cheap, decisive, and it is the Leg-2 question ("what broken state would serve exactly these bytes?") asked of a frozen receipt.
5. **`registration_sites.py`**: own follow-on row (contract for its mechanics — parse/cluster/filter — is real test-writing work, and its typing arrives with #188); in 44 it gets ONLY the Flags.2 docstring line stating hand-run-by-design. Keep 44 tight.

## FU2-D — findings reconciliation

**No duplicates**: I filed none by design; #280 (skills) matches my Flags.1 exactly — the sweep's row is the canonical one, as intended. #281/#282/#283: no overlap with anything of mine. **Gaps NEITHER of us filed — recommend rows for:**
1. **The worktree/scratch_copy hazard (my FU1-C)**: a `cp -a`/`scratch_copy.sh` copy of a WORKTREE carries a `.git` FILE naming the original gitdir — scratch git mutations hit the REAL index, silently. General, dangerous, not packet-scoped; deserves a finding (area `scripts/scratch_copy.sh`, kind gotcha) and eventually a guard in the script (detect `.git`-as-file → refuse or re-init). I can file it on request, or the lead does.
2. **Shell tree ungated** (C1) — currently only a report-section escalation; if the operator routes it anywhere, it needs a row to route.
3. **No CI exists** (C2) — same.
4. **`registration_sites.py` untested/untyped** (C5) — same, if routed as its own item.
5. Optional, process-class: sweep routing should `git log -- <area>` a finding's area before minting scope (the #270 OBE, my Flags.3) — friction row if the operator wants the protocol amended.

## FU2-E — my reading of the sweep's self-correction: same as the lead's, with one precision

Publishing the note-vs-error miscount AND catching the peer's commits because *"the arithmetic did not close"* is the **checked-expectation pattern** — the one thing CLAUDE.md records as working all four times where written rules did not. That earns its MEASUREMENTS trust. The precision: sound measurement ≠ sound COSTING — the split recommendation failed not on any number but on **rulings-visibility** (it costed docs/eval's 42 as fix-work under a counterfactual the FU1 archive ruling had already foreclosed, and weighed #188's 45 into a packet its own cited disposition keeps them out of). Rate the sweep's numbers sound and its sizing verdict superseded by rulings it could not have seen — no fault, just sequencing.

*Standing by (post-FU2).*
