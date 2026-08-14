# REPORT-builder-46-1 — packet 46 extension-discovery BUILD

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — frozen 11-pin contract GREEN by IMPLEMENTING (contract untouched); R14 rider paid; ruled test-migration executed; all touched suites GREEN; mutation-proven (4 mutations, both-way diff); zero-new gate delta. NO DEPLOY.
- deviation 1: **two commits, neither independently gate-green — inherent, documented.** Real discovery and the test-migration are mutually dependent (real discovery breaks the pre-existing composition suite; the migration only goes green once discovery is live). Commit 1 (server.py) makes the *contract* 11-GREEN but leaves the pre-existing composition suite RED (the known fork); commit 2 (test-migration) brings the FINAL tree fully green. Split for reviewability per the brief's suggested shape; the shipped HEAD is green on every touched suite.
- deviation 2: scratch copy `rm -rf` **sandbox-denied** (same as contract-46-1) — operator/lead may safely `rm -rf /home/ejprice/PycharmProjects/scratch-pkt46-builder` (disposable by `scratch_copy.sh` design; nothing load-bearing lives there — the mutation instrument is the committed `scripts/mutation_proof.py`).
- Packages considered: **none — no NEW mechanism specified.** Implemented the ruled static-`dict` registry discovery; `importlib.metadata` entry-points remain **keep_with_trigger** (deferred until the first off-repo extension exists) per contract-46-1 §Packages + wave-D §3. R14 uses the already-imported `mcp.types.ToolAnnotations` (no package decision).
- Reuse ledger: **1 new shared symbol** (`register_in_discovery`), dispositioned HAND-ROLLED (new shared test-composition policy, ≥2 call sites) — see §DRY. Plus test-local doubles (not shared policy).
- Graded: n/a — this is a build deliverable, not a verdict on another agent's artifact.
- **Store touch: NONE** (discovery is pure in-process composition; registry lookup + `cls()` + `register_extension`, none of which touch the store — confirmed against the read bodies, not assumed).
- decisions-needed: **none**. (PIN6 guard already ruled by contract; migration shape already ruled by Fable; both implemented as ruled.)
- receipt pointers: impl → `loremaster.server.LoreServer._discover_extensions` + `loremaster.server._register_extension_tools` (R14 `mcp.add_tool`); migration census → §CENSUS; category map + DUAL → §MIGRATION/§DUAL; mutation proof (instrument = `scripts/mutation_proof.py`) → §MUTATION; gates → §GATES; SHAs → §COMMITS.

## Phase 0 — investigation (tests-before-code; HEAD `efd03f1`)
- FROZEN contract `loremaster/tests/test_extension_discovery.py` = **11 pins** (7 classes). The contract-46-1 report describes an earlier **9-pin** cut; PIN 7 `TestAllConfiguredExtensionsAreComposed` (2 ∀-over-config-keys legs) was added at commit `efd03f1` ("11 pins"). I implement to the FROZEN 11.
- Reference logic: `REPORT-contract-46-1.md` §SAT. Migration bible: `REPORT-fable-46.md` §MECH/§BLAST/§SHAPE/§DUAL. Adversary I7 pin (module-attribute read, not import-bound): honoured.
- Read at `efd03f1` (lore `lore_get_symbol`/`lore_read`): `_discover_extensions` (inert stub), `_register_extension_tools` (extension `add_tool` passed no annotations), `register_extension` (seam-7 validate FIRST), `_validate_extension_config`, `__init__` (calls `_discover_extensions()` LAST, after `_apply_config_chunker_overrides()`, server.py:405), `_extension_helpers.py`, `Extension` base (ABC; `name` the sole `@abstractmethod`; every seam inert-default).
- `ToolAnnotations` already imported (`server.py:79`).

## Phase 1 — discovery + R14 (server.py) — the three-part build, parts 1 & 2
- `_discover_extensions` (replaces the inert stub body): reads `EXTENSION_REGISTRY` off the **module object** (`import loremaster.extension as extension_module; registry = extension_module.EXTENSION_REGISTRY`) — NOT an import-bound name (defeats monkeypatch; adversary §I7). Iterates **every** key (`for key in self._config.extensions:` — no `[:1]`/`next(iter())`/`break`). Unknown key → `ValueError` with exact literal `Known extensions:` + `", ".join(sorted(registry))` derived known-set (finding #371 R2: exact casing, DERIVED not hand-listed). `instance.name != key` → `ValueError` naming BOTH key and actual name (PIN6). Match → `register_extension(instance)`.
- R14 (`_register_extension_tools`, the extension `mcp.add_tool`): now passes `annotations=ToolAnnotations(readOnlyHint=False)` — matches all 15 built-ins (mutating-by-default honest posture).
- `EXTENSION_REGISTRY` stays `{}` in committed production (`extension.py:393`, UNCHANGED) — discovery dark until a later packet; NO real extension added.
- **Frozen contract now 11 GREEN** (`11 passed`, `-p no:randomly`).

## CENSUS — migration blast radius (grep-derived, per "sweep from the grep, never a hand-list")
`grep -rn "minimal_config" loremaster/tests/` + `grep -rn "_boot_from_yaml\|_config_with_chunkers" test_server_chunker_wiring.py`. Every hit an individual verdict (Fable's census confirmed; the contract's 4-file census missed 3):

| file:line | site | verdict |
|---|---|---|
| `_extension_helpers.py:53` | `minimal_config` def (default `{"fake":…}`) | **CHANGED default → `{}`** |
| `test_extension_discovery.py:42/64/134` | FROZEN contract, always explicit `extensions=` | DO-NOT-TOUCH; independent (untouched) |
| `test_server.py:80` | `config_path` fixture `minimal_config()` → disk → suite driver | **Cat A/B/C** |
| `test_server.py:289` | `TestConfigModelValidation::test_valid_slice_passes` | **Cat B** → discovery-driven |
| `test_server.py:301` | `test_bad_slice_fails_loud` | **Cat B** → discovery-driven |
| `test_server.py:315` | `test_missing_slice_for_extension_with_a_model_fails_loud` (`extensions={}`) | **Cat C** → KEEP manual + ROLE comment |
| `test_server_chunker_wiring.py:211` | `_config_with_chunkers` `minimal_config().model_dump()` → `_boot_from_yaml` | **Cat A** — FIXED FREE (uncounted by contract) |
| `test_server_chunker_wiring.py:329` | `minimal_config().include` (reads `.include` only, builds no server here) | SAFE — no change |
| `test_extension.py:73/100/320` | build `ExtensionContext` (config carried, never discovered) | SAFE under `{}` |
| `test_extension.py:232` | `LoreServer(minimal_config()).register_extension(_FieldIndexDeclaringExtension())` (no `config_model`) | **Cat A** — FIXED FREE |
| `test_search.py:2843` | `TestExtensionHooks._extension_pipeline` (`model_copy(extensions=minimal_config().extensions)` + manual register) | **Cat B** — uncounted, doubly-broken → discovery-driven |
| `test_lifespan_framework.py:48` | `minimal_config(extensions={})` explicit | SAFE — no change |

Fork breakage BEFORE migration (real discovery, working tree): `test_server.py` 26F/1P · `test_server_chunker_wiring.py` 15F/6P · `test_search.py::TestExtensionHooks` 2F/1P · `test_extension.py` 1F/46P — all the unknown-extension `'fake'` loud-boot ValueError. Exactly the reconciliation the migration resolves.

## MIGRATION — by category (Fable §SHAPE, executed)
- **Cat A — FIXED FREE by `minimal_config` default → `{}`** (zero per-test edits): `test_server.py` `TestFromConfig`/`TestBareServerIsGenericRag`; `test_extension.py::TestFieldIndexesCollectedByLoreServer`; ALL `test_server_chunker_wiring.py` boot-based tests. Verified: chunker_wiring 21✓, test_extension 47✓ after the flip alone.
- **Cat B — `config_model` extension WIRED → discovery-driven**: added the shared `_extension_helpers.register_in_discovery(monkeypatch, mapping)` + a `fake_discovered` fixture (registry-inject `{"fake": FakeExtension}` + explicit `{"fake":{"flavour":"vanilla"}}` slice, composed by `from_config` — no manual register). Members: `TestRegisterExtensionWiring` seams 1-11; `TestConfigModelValidation::{test_valid_slice_passes, test_bad_slice_fails_loud}` (bad-slice now raises where prod raises it — at BOOT inside discovery's internal register); **`test_search.py::TestExtensionHooks._extension_pipeline`** (one helper edit fixes all 3 hook tests).
- **Cat C — `register_extension`'s OWN guards → stay MANUAL** (no-`config_model` doubles vs empty-slice config): `TestNit1RegisterGuard` (4; shadow doubles **rebased off bare `Extension`**, not `FakeExtension`, so seam-7 no-ops and the chunker guard is what fires); extracted `test_register_returns_self_for_chaining` as a manual unit (chaining return is unobservable through discovery); and **`test_missing_slice_for_extension_with_a_model_fails_loud` KEPT EXACTLY AS-IS + a ROLE comment** — it is the SOLE coverage of the discovery-UNREACHABLE missing-slice branch (§MECH); a future rename that folds it into discovery would silently orphan the branch.

## DUAL — removed-behaviour inventory (Fable §DUAL), every item adjudicated preserved
| old behaviour | fate | coverage now |
|---|---|---|
| `register_extension` returns self / chains | **preserved-with-pin** | `test_register_returns_self_for_chaining` (manual unit) |
| slice validation — valid | **preserved-with-pin** | `test_valid_slice_passes` (discovery) |
| slice validation — bad (extra key) | **preserved-with-pin** | `test_bad_slice_fails_loud` (discovery, at boot) |
| slice validation — missing required | **preserved-with-pin** | `test_missing_slice_…` (MANUAL — sole coverage, discovery-unreachable) |
| nit-1 suffix-overlap + greedy-handles guard | **preserved-with-pin** | `TestNit1RegisterGuard` (4, manual, rebased) |
| filename-keyed chunker allowed (no suffix) | **preserved-with-pin** | `test_filename_keyed_chunker_without_a_suffix_is_allowed` (bare double) |
| seam composition 1-11 | **preserved-with-pin** | `TestRegisterExtensionWiring` seams (discovery calls the same `register_extension`) |
| the manual `register_extension` code path itself | **preserved** | executed by every Cat-C test AND internally by discovery |
Nothing dropped-deliberately, old-bug, or spec-silent. Nothing orphaned.

## MUTATION — proof on the FINAL implementation (#196), instrument = `scripts/mutation_proof.py`
Provenance-asserted scratch (`./scripts/scratch_copy.sh`): `loremaster.__file__ = /home/ejprice/PycharmProjects/scratch-pkt46-builder/loremaster/loremaster/__init__.py` (resolves INSIDE the scratch root — the mutations grade MY code, #140). Declared-RED node ids taken from `pytest --collect-only` (not source), diffed BOTH ways; server.py restored byte-exact (md5 `cb1bc9a8639776722051c44cc8c798a1`) after each.

| mutation | edit | declared RED = observed RED | verdict |
|---|---|---|---|
| **A — inert discovery** | `for key in self._config.extensions:` → `for key in []:` | 9: PIN1×2, PIN2×2, PIN4×2, PIN6, PIN7×2 (`9 failed, 2 passed`; PIN3 regression + PIN5 R14 stay GREEN) | PROOF HELD (exit 0) |
| **B — first_key_only** | → `for key in list(self._config.extensions)[:1]:` | 2: PIN7 both legs (`2 failed, 9 passed`) — the ∀-over-config-keys pin discriminates | PROOF HELD (exit 0) |
| **C — R14 removed** | `annotations=ToolAnnotations(readOnlyHint=False),` → `annotations=None,` | 1: PIN5 (`is not None` leg) | PROOF HELD (exit 0) |
| **D — R14 flipped** | → `annotations=ToolAnnotations(readOnlyHint=True),` | 1: PIN5 (`is False` leg) | PROOF HELD (exit 0) |

Each `PROOF HELD` = declared set fired EXACTLY (no unexpected reds, no declared-but-green), mutation landed (anchor matched exactly once), file restored byte-exact. C+D together mutation-prove R14 BOTH directions (contract PIN5 requirement).

## GATES — zero-new delta vs the adjudicated branch baseline (RED 191 typecheck / RED 444 pytest → packet-39)
- `uv run ruff check` on touched files AND whole tree → **All checks passed!** (exit 0).
- `scripts/typecheck.sh` → **191 `error:` lines == baseline**; grep of the error set for `server.py`/`_extension_helpers.py`/`test_server.py`/`test_search.py`/`extension.py` → **ABSENT** (zero new mypy errors name my files).
- Touched suites (`pytest -n auto`, PASSED-COUNT in each tail):
  - `test_extension_discovery.py` (FROZEN contract) — **11 passed**
  - `test_server.py` — **28 passed** (was 27 nodes; +1 from the chaining/discovery split)
  - `test_search.py::TestExtensionHooks` — **3 passed** (live store)
  - `test_server_chunker_wiring.py` — **21 passed**
  - `test_extension.py` — **47 passed**
  - `test_tool_allowlist.py` — **30 passed**
  - `test_lifespan_framework.py` — **6 passed**
  - `test_mcp_server.py` (structural/AST pins: registration / dead-name / instructions) — **669 passed**
- A failing test would be a STOP → none occurred; nothing called "flaky".

## DRY ledger (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `register_in_discovery(monkeypatch, mapping)` (`_extension_helpers.py`) | `grep -rn EXTENSION_REGISTRY loremaster/tests/`; read `test_extension_discovery.py::_inject_registry`; Fable §DRY | the contract has a LOCAL 2-line `monkeypatch.setattr(extension_module,"EXTENSION_REGISTRY",…)` fixture (private to that file); `test_server.py` AND `test_search.py` both now need the same injection | **HAND-ROLLED as a SHARED FUNCTION** in `_extension_helpers.py` — ≥2 call sites need the same test-composition POLICY ⇒ a function they call, not a pattern each clones (ONE-IMPLEMENTATION). The contract's local fixture is self-contained and predates this; left as-is. |

Test-local doubles (NOT shared policy, inline-double idiom per `test_extension.py::_DuplicateBumpExtension`): `_NoConfigExtension` (chaining), `_MakefileExtension` (filename-keyed allow-path); the nit-1 shadow doubles (`_ShadowExtension`/`_CfgExtension`/`_GreedyExtension`) were rebased off bare `Extension` (name + chunkers only). REUSED (no new symbol): `minimal_config`, `FakeExtension`, `FakeMakefileChunker`, `FakeThresholdProfile`, `Extension`, `LoreServer`.

## Tool honesty (brief-base §4)
lore MCP first-choice for all structure lookups (`lore_get_symbol`/`lore_read`/`lore_search` for `_discover_extensions`, `_register_extension_tools`, `register_extension`, `_validate_extension_config`, `__init__`, `Extension`). Grep fallbacks SAID OUT LOUD (CLAUDE.md case (a) rename-exhaustiveness where a missed `minimal_config` site compiles-but-breaks, case (b) non-symbol textual seams): the `minimal_config`/`_boot_from_yaml`/`ToolAnnotations`/`EXTENSION_REGISTRY` sweeps + the typecheck-error-set greps — cross-cutting textual maps the symbol graph does not own. No lore weakness encountered → no `lore_findings` filed.

## COMMITS
- `543ed72` — `feat(46): config-driven extension discovery + R14 rider` (server.py). Contract 11-GREEN; pre-existing composition suite RED (the documented fork).
- `89852b3` — `test(46): migrate extension-composition suite to live discovery` (_extension_helpers.py, test_server.py, test_search.py). FINAL tree fully green on every touched suite.
- shipped HEAD = `89852b3`; re-confirmed green post-commit: `test_extension_discovery.py` + `test_server.py` = **39 passed**. `git add` named my own paths only (shared-tree hazard #189/#191); REPORT-*.md left untracked for the lead to archive. NO DEPLOY.
