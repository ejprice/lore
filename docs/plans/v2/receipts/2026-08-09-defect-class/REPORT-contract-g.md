brief-base v10 read
brief project v7 read

# REPORT-contract-g — INSTRUMENT G contract (the non-omittable gate bundle, #344)

## SUMMARY
- state: **done** — RED contract authored at `scripts/wave_gate.py`'s future seam; `wave_gate.py` intentionally not implemented.
- capability check: all tools present; lore MCP loaded via `ToolSearch "+lore"`; no fallbacks needed (structure work used lore-adjacent Reads of the two named files + a live `pending_contract_gate` import). No grep-for-structure fallback occurred.
- deliverable: `scripts/test_wave_gate.py` — **15 pins**, canned data under `tmp_path`, never runs the real gates.
- RED confirmed: sole failure is `ModuleNotFoundError: No module named 'wave_gate'` at collection (sibling `pending_contract_gate` import resolves cleanly). Body §RED.
- gates on the file itself: **mypy Success** (strict, `MYPYPATH=scripts`, no ignore-missing crutch) · **ruff clean** · so the contract plants NO orphaned red now OR after the build (importlib acquisition avoids the `warn_unused_ignores` trap — body §Lifecycle).
- Packages considered: none — no mechanism specified. Reused `pending_contract_gate`'s readers/types (`READERS`, `GateManifest`, `GateRunner`, `PendingContractGate`, the three `*Reader`s) + stdlib `ast`/`importlib`; nothing hand-rolled (ONE IMPLEMENTATION).
- Graded: e1dfa14 · HEAD-at-report: e1dfa14 · SAME. (Design doc was graded at `74694dc`; tree moved via siblings, but this contract binds only `pending_contract_gate`'s stable public surface, verified live at HEAD.)
- decisions-needed (6): the mandated seam · in-process-vs-subprocess architecture · scoped-pytest-failure reading · scopable-gate-by-reader · the brief-prose pin is NOT in this file · CLI test assumes `GateRunner` reuse. See §DECISIONS.
- receipt pointers: contract `scripts/test_wave_gate.py` (module docstring carries the W1–W7 wrong-build catalog; each `test_` docstring carries its own "what wrong build survives"); wrong-build analysis §WRONG-BUILDS; RED/gate tails §RED.

## The task, executed
INSTRUMENT G (`docs/plans/v2/design/2026-08-09-defect-class-prevention.md` §3 + §4 F1) + finding #344: "the gates" is a hand-list re-typed per spawn-brief and omittable; 05a-i omitted `pending_contract_gate.py --currency` and 8 RED_ORPHANED pins went unseen two cycles. The fix is a single derived entrypoint `scripts/wave_gate.py` that a brief points at. This contract pins that entrypoint's behaviour, RED-first, before any builder.

The contract mandates a small public surface on `wave_gate`, chosen to MIRROR `pending_contract_gate._render_currency` (the machinery it wraps) so the wrapper re-lists and re-implements nothing:
- `MODE_WAVE` / `MODE_CHECKPOINT` — distinct non-empty str constants.
- `render_wave_receipt(gate, manifest, results, *, mode, pytest_selector=()) -> tuple[list[str], bool]` — the pure, mode-aware currency renderer (`mode` keyword-only, NO DEFAULT).
- `pytest_args_for(mode, pytest_selector) -> tuple[str, ...]` — scoping decision (selector in wave, `()` in checkpoint).
- `main(argv=None) -> int` — CLI entrypoint; mode required.

## §WRONG-BUILDS — the per-pin "what wrong build survives?" analysis
Each brief requirement → the pin(s) → the wrong build each pin kills:

| brief requirement | pin(s) | wrong build killed |
|---|---|---|
| RE-LISTS NO gates; derived from gates.yaml; NO hardcoded tuple (#312) | `test_no_hardcoded_gate_id_collection` (AST source scan) + `test_render_enumerates_exactly_the_manifest_gates` (add/drop a gate → render tracks it, BOTH directions) | a hardcoded `("typecheck","ruff","pytest")` that ignores the manifest |
| mutation proof: add/remove gate changes behaviour | `test_render_enumerates_exactly_the_manifest_gates` (4-gate manifest shows `extra`; 2-gate manifest drops `ruff`'s line) | any hardcode diverging from `manifest.ids` |
| non-omittable CORE always FULL; only pytest scopable | `test_wave_core_gates_run_full_and_still_fail` (typecheck RED_ORPHANED fails even in wave; typecheck line never SCOPED) | a build that scopes/skips typecheck or ruff in wave mode |
| `--wave` pytest scoped, selector ECHOED, marked SCOPED, NEVER GREEN | `test_wave_pytest_scoped_never_green_and_echoes_selector` | calling `_render_currency` straight (pytest renders GREEN on a `-k` subset) |
| `--checkpoint` pytest FULL | `test_checkpoint_all_green_passes` (pytest line GREEN, not SCOPED) | a build that scopes in checkpoint too |
| MODE required & recorded | `test_render_requires_mode_declared` (TypeError, no default) + `test_receipt_header_records_the_chosen_mode` + `test_cli_refuses_without_a_declared_mode` (SystemExit) | a build that defaults/hides the mode |
| output NAMES which gates ran + exact pytest scope | enumeration + selector-echo pins above | a receipt that omits the roster or the scope |
| SCOPED run never renders unqualified pass | `test_wave_pytest_scoped_never_green_and_echoes_selector` (SCOPED, GREEN absent on the pytest line) | scoped-shown-as-green |
| currency RED_ORPHANED fails the bundle (POSITIVE CONTROL) | `test_checkpoint_red_orphaned_fails` | a build that waves an orphaned pin through |
| NOT_RUN fails (the literal #344 subset event) | `test_claimed_gate_absent_from_results_is_not_run_and_fails` | a subset rendered as an unqualified pass |
| all-green at checkpoint passes (POSITIVE CONTROL) | `test_checkpoint_all_green_passes` | an always-fail build |
| scopable gate DERIVED, not named `"pytest"` (FIXTURES DISCRIMINATE) | `test_scopable_gate_identified_by_reader_not_literal_id` (junit gate renamed `suite`) | scopability keyed on `id == "pytest"` |
| run-side scoping | `test_pytest_args_for_scopes_only_in_wave_mode` | a build that forwards the selector in checkpoint (or never) |

Discrimination technique used throughout (per CLAUDE.md FIXTURES MUST DISCRIMINATE): the empty-registry `gate` fixture makes a clean tree render GREEN and any injected defect render RED_ORPHANED — a real positive/negative pair, not a monoculture; the `junit_id="suite"` fixture is the parameter-value-DIFFERENT pin that kills the `"pytest"`-hardcode.

## §RED — receipts (HEAD e1dfa14)
```
$ uv run python -m pytest scripts/test_wave_gate.py -q   # RED (contract-first)
E   ModuleNotFoundError: No module named 'wave_gate'   (scripts/test_wave_gate.py, importlib acquisition)
ERROR scripts/test_wave_gate.py — 1 error during collection
$ MYPYPATH=scripts uv run mypy scripts/test_wave_gate.py     → Success: no issues found in 1 source file
$ uv run ruff check scripts/test_wave_gate.py               → All checks passed!
```
RED is a COLLECTION error (module absent), not a per-test failure — standard contract-first. Once the builder creates `wave_gate.py` with the mandated surface, the 15 pins collect and run.

## §Lifecycle — why importlib, not a static import (a trap avoided)
A static `import wave_gate` needs `# type: ignore[import-not-found]` today (module absent). Under `[tool.mypy] strict = true` (`warn_unused_ignores`), that ignore flips to an **unused-ignore RED the moment the builder creates the module** — a latent orphaned red the contract would plant, surfacing only at cycle G's close. `wave_gate = importlib.import_module("wave_gate")` is a runtime call mypy never statically resolves: no import-not-found, no dangling ignore, typecheck-clean in BOTH states, and it couples the builder to nothing. Still RED at collection (raises `ModuleNotFoundError`). `wave_gate.__file__` is guarded (`assert … is not None`) so the AST source-scan stays strict-clean too.

## §DECISIONS — forks surfaced (escalating is a success state, brief-base §2)
1. **The mandated seam is a contract-defined interface.** A CORRECT `wave_gate` with a different decomposition (e.g. a dataclass return instead of `(lines, ok)`, or differently-named functions) would fail this contract. I chose the seam to mirror `_render_currency` exactly. **Recommend** the builder implement to it; operator/lead may adjust the seam before the build.
2. **Architecture presupposition: IN-PROCESS composition, not a subprocess wrapper.** `render_wave_receipt(gate, manifest, results, …)` presupposes `wave_gate` composes `pending_contract_gate`'s machinery in-process — necessary because the SCOPED-not-GREEN override needs STRUCTURED access to the pytest currency verdict; a stdout-parsing subprocess wrapper (parsing `pending_contract_gate.py --currency` output) cannot do it cleanly and would be exactly the natural-language-surface class this repo forbids. The design's word "invokes" admits both readings; **I pin (B) in-process** and recommend it.
3. **Reading pinned — a scoped-pytest FAILURE fails the wave bundle** (`test_wave_scoped_pytest_failure_fails_the_bundle`). Alternative reading: "wave never fails on pytest since it is not a currency clear." I pin fail-on-scoped-failure because the other reading lets a real regression in the changed suite pass silently, defeating the wave posture. **Confirm.**
4. **Scopable gate identified by READER (`JUnitReportReader`), not the literal id `"pytest"`** — mirrors `pending_contract_gate._typecheck_gate` (finds the mypy gate by reader). Pinned via the `junit_id="suite"` fixture. If the builder must key on the id, reconcile.
5. **NOT IN THIS FILE (surfaced gap, not silently dropped):** INSTRUMENT G ALSO calls for a repo pin over spawn-brief / `brief-base` / `lead-base` PROSE asserting they point at the bundle rather than enumerating gates inline (allowlist-the-safe over brief prose). That is a SEPARATE instrument touching brief templates — outside my writable set (`scripts/test_wave_gate.py` only). **Lead to route** it (a sibling cycle, or its own). It is the other half of #344's enforcement and is not covered here.
6. **CLI mode-required test assumes reuse of `pending_contract_gate.GateRunner`.** `test_cli_refuses_without_a_declared_mode` monkeypatches `GateRunner.run` to keep the test SAFE (a wrong mode-defaulting build fails fast instead of launching real gates) AND discriminating. If the builder uses a different runner class, that safety guard won't engage (the pin still passes for a correct build). Consistent with design intent (reuse the machinery).

## Scope / verification notes
- Writable set honoured: created ONLY `scripts/test_wave_gate.py`; edited no existing file. No git state touched.
- No worktree used (standing law #134/#125 — shared single tree).
- lore currency: read-only session for me; I authored one new untracked file, so graph-derived answers were not relied upon as deletion/consumer gates. `pending_contract_gate`'s surface was confirmed by a LIVE import in the pytest run, not from the index.
