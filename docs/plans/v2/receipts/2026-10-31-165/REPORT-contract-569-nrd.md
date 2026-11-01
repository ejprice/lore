brief-base v25 read
brief project v7 read

# REPORT-contract-569-nrd — #569 drift pin for `PYTEST_DEFAULT_NORECURSEDIRS` (tdd-light Phase 1, 2026-10-31)

## SUMMARY BLOCK
- **STATE: DONE.** One pin added to `scripts/test_gated_ground.py` (only file edited). `scripts/gated_ground.py` untouched. Nothing staged or committed.
- **THE PIN:** `scripts/test_gated_ground.py::TestTheExecutionAxisScope::test_the_declared_norecursedirs_default_matches_what_pytest_puts_in_force`, plus its helper `_pytest_norecursedirs_in_force` (with the module constants `_NORECURSEDIRS_PROBE_CONFTEST` and `_PROBE_SCRUBBED_ENVIRONMENT_VARIABLES`).
- **ROUTE: PUBLIC API, no private import.** A subprocess `sys.executable -m pytest -c <tmp>/pytest.ini --rootdir <tmp> -p no:cacheprovider -q <tmp>` runs in a throwaway rootdir. Its `conftest.py` writes `config.getini("norecursedirs")` (public `Config.getini` / `Config.rootpath`) to a JSON file. The ini sets nothing, so the value is pytest's in-force default. `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` are scrubbed and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` is set, so the surrounding session's config cannot leak in. The run must exit `pytest.ExitCode.NO_TESTS_COLLECTED`, or the probe is treated as broken.
- **CONTROL LEG (the probe needs a control):** in the same test, a second throwaway rootdir sets `norecursedirs = nrd569_sentinel_dir`. The probe must report back exactly `["nrd569_sentinel_dir"]` before its answer for the default is trusted. This rules out a probe that crashes into an empty answer or returns a constant. It is also the evidence for the "pytest's side changes" direction: the probe reports whatever pytest actually has in force. Measured green at HEAD 169539d + this edit.
- **MUTATION (scratch, `scripts/mutation_proof.py`):** deleted the `"_darcs",` line from the constant.
  - Declared RED set, taken from `--collect-only` before the run: `{…::TestTheExecutionAxisScope::test_the_declared_norecursedirs_default_matches_what_pytest_puts_in_force}`.
  - Observed: that exact set, `1 failed, 351 passed in 48.99s`. **PROOF HELD.** The tree was restored byte-exact (`scripts/gated_ground.py` md5 `f1accbcbec335a5f9c6ef4417bb526d1`).
- **BUILD (real tree, committed module 169539d + this test edit):** `352 passed in 33.16s`, EXIT=0, 0 ImportError.
- **PROVENANCE:** `loremaster.__file__ = /var/tmp/claude-1000/nrd569-scratch/loremaster/loremaster/__init__.py`. The scratch copy was made by `./scripts/scratch_copy.sh /var/tmp/claude-1000/nrd569-scratch` (EXIT=0, provenance asserted). `LORE_PYTHON=/var/tmp/claude-1000/nrd569-scratch/.venv/bin/python`, and the mutation run used it.
- **RUFF:** `uv run ruff check scripts/test_gated_ground.py` → `All checks passed!` EXIT=0.
- **CURRENCY `--legs typecheck,ruff` (no pytest):**
  - ruff GREEN.
  - typecheck RED_ADJUDICATED, 83 residuals owned by packet-58-contract and packet-64b-i-contract.
  - RED_ORPHANED 0.
  - Ran `scripts/typecheck.sh` directly: 83 `error:` lines total, **none in `gated_ground.py` / `test_gated_ground.py`**.

## Runs used (all 2026-10-31)
| # | label | command (abridged) | result |
|---|---|---|---|
| 1 | GREEN build at committed module | `systemd-run … MemoryMax=16G … uv run python -m pytest -q scripts/test_gated_ground.py -n 8 --timeout=300 -p no:cacheprovider -rfE` (repo root) | 352 passed, EXIT=0 |
| 2 | mutation (`"_darcs",` deleted) | `mutation_proof.py --expect-red <id> -- systemd-run … $LORE_PYTHON -m pytest -q scripts/test_gated_ground.py -n 8 --timeout=300 …` (scratch) | 1 failed (declared) / 351 passed, PROOF HELD |
| — | gates (not pytest) | ruff on the file; `pending_contract_gate.py --currency --legs typecheck,ruff`; `scripts/typecheck.sh` | as above |

There was no separate RED-at-HEAD run. This is a drift pin for an existing constant, so it is correctly GREEN at HEAD. The mutation run is its RED receipt. Runs 1 and 2 went to `haiku-runner`s; I checked each `RAN:` line against my command and read the count lines in the logs myself. The currency run also went to a `haiku-runner`. Logs: session scratchpad `build.log` / `mutation.log` / `currency.log` / `typecheck.log`. These are not durable; the receipts above are pasted.

## Package line
- Mechanism: "what is pytest's `norecursedirs` default". Package: pytest itself. Read: `_pytest.main.pytest_addoption` declares it inline (per the constant's own citation in `gated_ground.py`), and the public `Config.getini` returns the in-force value. I used `getini` through a subprocess rather than the private `_parser._inidict` read the sibling `python_files` pin uses.

## Odoo-20 portability: n/a — no Odoo seam touched.

## Adversarial pre-flight
- pytest upgrade changes the default → the equality goes RED. Proved for the constant side by mutation; for the pytest side by the control leg (the probe reports the in-force value).
- Surrounding config leaks in (repo `pyproject` `[tool.pytest.ini_options]`, `PYTEST_ADDOPTS -o norecursedirs=…`) → blocked by `-c` with its own ini, `--rootdir`, env scrub, and plugin autoload off.
- Probe breaks silently (crash, no file written, empty list) → exit-code assert plus the control leg.
- Order-only change by pytest → the list equality goes RED. I accept that strictness: the fix is a one-line update and the message names it.
- Wrong interpreter (pytest other than the one the gate runs) → `sys.executable`. In scratch, that is the scratch venv.

## Realism clauses
- ☑ Production-realistic inputs: the input is the real installed pytest (9.0.3), not a fixture value.
- ☑ Independent expected value: the expectation comes from pytest's live answer, never from `gated_ground`.
- ☑ Seam coverage: the seam is pytest → hand-copied constant, exercised for real.
- ☐ Magnitude bound: not applicable, because the output is a list of strings, not a derived number.
- ☑ Shared conventions: the expected value comes from the source of truth (pytest), not a literal.
- Hostile rendered text / input accounting: not applicable, because nothing renders stored text and nothing transforms a collection.

## Noticed outside this change (raised, not acted on — outside my writable set)
1. **The `gated_ground.py` docstring is now stale.** The comment above `PYTEST_DEFAULT_NORECURSEDIRS` says *"⚠ … no contract pin re-derives it against the installed pytest yet (#569 builder report)"*. From this pin on, that is false. It is served prose in the instrument, so it is the natural-language-drift class. Whoever owns `gated_ground.py` should reword it and cite this test by name.
2. **The sibling `python_files` drift pin uses a private API** (`_pytest_declared_default_patterns` → `get_config([])._parser._inidict`). Its docstring argues `getini` needs a parsed config tied to the cwd. This helper shows a public route without that dependency: subprocess plus `-c` plus `--rootdir`. Does the lead want the sibling moved onto `_pytest_norecursedirs_in_force`'s pattern (generalised by ini key)? That would leave one probe for both defaults.
3. **The currency gate prints `CURRENCY : FAIL — claimed but never run: pytest` under `--legs typecheck,ruff`.** It also prints `ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN`. CLAUDE.md sanctions that subset as the every-round run and asks for "RED_ORPHANED 0", which holds. But the FAIL/ORPHAN wording on a deliberately skipped leg reads as a failure to any agent that runs it. Possibly by design (#312). Flagging it so the lead can decide whether it needs a finding.
