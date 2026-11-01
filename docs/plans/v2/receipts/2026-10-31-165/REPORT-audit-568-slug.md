brief-base v25 read · brief project v7 read

# REPORT-audit-568-slug — tdd-light Phase 5 REFACTOR+AUDIT of 99c2b8e (#568)

## SUMMARY (2026-10-31)
- **State: done-with-deviations · Verdict: GO** for 99c2b8e + my 4 in-place fixes, conditional on the lead routing C1–C5 (no blocker found in the graded commit; A2 is a missing-refusal defect, routed with its edit).
- Deviations: (1) gate logs live at `/var/tmp/claude-1000/slug568-audit-logs/` (the brief named no log location; outside the repo writable set); (2) skill suite re-run with `--ignore=test_ledger_572.py` for a clean count, because the sibling's file was edited (20:03:52) while the first run was in flight; (3) M1 proof is FAILED, see §5b (an id-form error and an under-declaration, both mine).
- Packages considered: python-slugify (F1, already adopted): read the installed `slugify(text, separator=…)` signature, probed `odoo-custom→odoo_custom`, `café→cafe`, `---→''` → `replace` (kept). Owner-file sqlite: loremaster `open_resilient_sqlite` is the in-repo owner, but lore_deploy.py runs as bare python3 and cannot import loremaster (F2) → `bespoke` stdlib `sqlite3`, justified.
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: 1 new symbol (`_PLAIN_WRITE_MODE` constant, no rule decided); grep for an existing file-mode constant found none → HAND-ROLLED. The commit's new rule-deciders were graded in §1 DRY.
- Graded: 99c2b8e · HEAD-at-report: 99c2b8e · SAME (my fixes are uncommitted on top: config.py md5 badfe82e…, lore_deploy.py md5 7b600381…).
- Fixed in place: A1 lazy `slugify` import · A3 scaffold lore.yaml mode 0600→0644 (a regression from the commit) · A4 stale `--project` help prose · A5 redundant local import. **Lazy-import receipt:** `import loremaster.config` / `import loremaster.server` → `'slugify' in sys.modules` = **False** (was True); the control call still derives `odoo_custom` (§2.1).
- Routed (contract items, §6): C1 corrupt manifest → traceback (A2, violates F5) · C2 pin for reading 2 · C3 pin for reading 1 · C4 file-mode pin · C5 stop/status un-configured-dir pin. Escalated: A7 (the Addendum's legacy-backfill rule lets a hand-set slug claim another project's ownerless manifest; this is the ruled behaviour, flagged as a residual).
- Readings: both builder readings are CORRECT per the rulings; both are unpinned → C2/C3.
- Mutation M1 (`_project_slug` no-config branch → raw `project.name`): LANDED, killed by 4 setup tests; declared≠observed (EXIT=4) because of the #560 id form plus 3 under-declared reds. The branch is unpinned only through stop/status (S6).
- Gates: skill suite **348 passed** EXIT=0 (excluding the sibling's file; with it: 43 failed, all in `test_ledger_572.py`, the sibling's #572 RED contract) · test_config **90 passed** EXIT=0 · typecheck: 83 errors, all in packet-58/64b test files, RED_ADJUDICATED, 0 in config.py/lore_deploy.py · ruff on my files: clean · currency `--legs typecheck,ruff`: **RED_ORPHANED 1, the sibling's `test_ledger_572.py:359` E501; 0 in my files** (pytest NOT_RUN by `--legs` design, same as the builder's receipt).
- Decisions needed: A7 (accept the residual or rule a container/inspect cross-check) · whether the sibling's E501 orphan is that round's to clear (yes, I assume).
- Pointers: §1 findings · §2 fixes+receipts · §3 readings · §4 smells · §5/5b mutation · §6 routed items · §7 gate receipts · §8 routing/fan-out.

Role-boundary: operator grant quoted in brief ("Keep it", 2026-09-27) — audit+fix-in-place accepted for this one lens.

## Routing table (written before first sweep)
| step | tier | who | reason |
|---|---|---|---|
| cold review of diff (config.py, lore_deploy.py) | 3 | me | audit verdict; self-sealing errors |
| `project.name` / slug-consumer grep in lore_deploy.py | 1 | me, one parallel batch | small (1 file), I read all output anyway |
| prior-art lore_search for new symbols | 1/3 | me | ≤6 queries, feeds my judgment |
| lazy-import edit + sys.modules probe | 3 | me | the fix itself; probe is 1 cmd I read |
| skill suite / test_config / typecheck / ruff / currency gates | 1 | haiku-runner | test runs |
| mutation proof (scratch copy + mutation_proof.py) | 3 verdict / 1 run | me (setup+verdict), run via haiku-runner | mutation verdict is never Haiku |

## 1. Cold review findings (written 2026-10-31 BEFORE any edit; graded 99c2b8e)

Slug-consumer sweep (grep, case (c) cross-cutting textual map, said out loud): `grep -n 'project\.name|f"lore-{|MANIFEST_DIR /|LORE_SECRETS_DIR /|c\.project\.slug'` over `lore_deploy.py` — the only remaining `project.name` is the normaliser's own argv (`_derive_slug`) and `config_path.name` (tempfile prefix). Every container/manifest/env-file/mcp-key site routes through `_project_slug` / `_configured_slug` / `_manifest_path`. **PASS.**

Second-writer question: loremaster opens `<slug>.memory.db` (`server.py` `MemoryLedger(str(manifest_path.with_name(f"{slug}.memory.db")))`) and `calibration/<model>.json`; `<slug>.db` itself is only an anchor (`manifest_path=_DEFAULT_MANIFEST_DIR / f"{config.project.slug}.db"`). `ManifestOwner` therefore writes no file loremaster owns. **PASS** (#572 ledger semantics are a separate round; not implemented here).

| id | severity | finding | disposition |
|---|---|---|---|
| A1 | medium | `config.py` imports `slugify` at module level → the SERVER needs python-slugify at boot though only the host deploy path calls the normaliser | brief's known fix → FIX in place (§2) |
| A2 | medium | **Corrupt manifest → traceback.** `ManifestOwner.recorded_path` catches only `sqlite3.OperationalError`; a non-SQLite `<slug>.db` raises plain `sqlite3.DatabaseError` (not a `RuntimeError`) out of `_slug_collision`, and `verb_setup` does not wrap `_slug_collision` at all. Measured (probe §A2): `_slug_collision RAISED DatabaseError file is not a database is RuntimeError: False`. Violates F5 ("never a traceback"). | ROUTE as contract item (new refusal text needs a pin; edit given in §5) |
| A3 | low | **Scaffold file-mode regression.** `tempfile.NamedTemporaryFile` creates the staged file 0600; `os.replace` makes `lore.yaml` 0600. Pre-commit `write_text` gave umask default. Measured (probe §A2): `scaffold mode: 0o600 umask-default would be 0o644` (umask 0022). | FIX in place (restores pre-99c2b8e behaviour) + ROUTE the pin |
| A4 | low | Stale served prose: `--project` help reads "its name is the slug" — false since #568 (F3: lore.yaml wins, else derived). Rename-sweep class (natural-language surface). | FIX in place |
| A5 | trivial | `_manifest_counts` keeps a function-local `import sqlite3` now duplicated by the module-level import | FIX in place |
| A6 | low | `_scaffold_lore_yaml` re-derives the slug (second interpreter spawn) after `verb_setup` already derived it via `_project_slug`. Same answer by construction; cost only. | NOTE (signature change would touch direct test callers; not worth it) |
| A7 | residual (ruling-prescribed) | Addendum's legacy-manifest rule trusts `lore.yaml` existence: project B whose lore.yaml hand-sets slug `X`, where `X.db` is an ownerless legacy manifest of project A and A's container is absent (`stop` removes it), is NOT refused and BACKFILLS B as owner. The ruling literally prescribes this branch; without a row the owner is unknowable. | ESCALATE to lead (residual, not a build defect) |
| A8 | info | `_container_workspace_source` / `_derive_slug` raise `FileNotFoundError` if podman / the loremaster python is absent — same as pre-existing `_container_state`; not new | NOTE |
| A9 | info | Path equality uses `.resolve()` on both sides (symlinked project dirs); no pin exercises a symlinked path | NOTE (test-smell list §4) |

DRY / prior art (`lore_search` + grep): `derive_project_slug` — owner is python-slugify (package) beside `SLUG_PATTERN` per F2; no other slug normaliser in tree (grep `slugify|derive_.*slug` → only this). `ManifestOwner` — loremaster's `open_resilient_sqlite` is the sqlite-open owner but lore_deploy.py runs as bare python3 and cannot import loremaster (F2's own constraint); hand-rolled is justified. `_slug_collision` / `_project_slug` — new rule-deciders, no prior owner (the 8 sites were inline `project.name`).

## 5. Mutation M1 — DECLARED before the run (2026-10-31)
Weakest pin identified: `_project_slug`'s no-lore.yaml branch (`return _derive_slug(project)`). Every `TestEveryVerbUsesTheConfiguredSlug` case writes a lore.yaml first, and the scaffold calls `_derive_slug` directly, so only fresh-setup paths reach this branch.
- Mutation: in `lore_deploy.py::_project_slug`, `    return _derive_slug(project)\n\n\ndef _manifest_path` → `    return project.name\n\n\ndef _manifest_path` (raw directory name, the pre-#568 behaviour).
- Declared RED (ids from `pytest --collect-only -q` in the scratch copy, rootdir = scratch root):
  - `skills/lore-deploy/scripts/test_scaffold_slug.py::TestSetupProvisionsAHyphenatedProjectEndToEnd::test_setup_scaffolds_indexes_and_wires_under_the_derived_slug` (setup's `slug` var is raw → `.mcp.json` key `lore_odoo-custom`)
- Predicted SURVIVORS (the weakness, not declared red): `test_main_returns_exit_error_for_an_unslugifiable_dir_not_a_traceback` and `test_setup_refuses_naming_the_directory_and_writes_nothing[*]` (the scaffold's own `_derive_slug` still refuses); `stop`/`status` on an un-configured hyphenated dir have no pin at all.
- Command scope: `test_scaffold_slug.py` + `test_lore_deploy.py` in the scratch copy.

## 2. Fixes made in place (operator grant "Keep it", 2026-09-27) — all after §1 was written
| id | file · symbol | change | proof |
|---|---|---|---|
| A1 | `loremaster/loremaster/config.py` · `derive_project_slug` | module-level `from slugify import slugify` → function-local, with a one-line WHY comment | §2.1 |
| A3 | `lore_deploy.py` · `_scaffold_lore_yaml` + new constant `_PLAIN_WRITE_MODE = 0o666` | `os.chmod(staged, 0o666 & ~umask)` before validate+replace, restoring pre-99c2b8e mode | probe after fix: `scaffold mode: 0o644 umask-default would be 0o644`; leftover staged files `[]` |
| A4 | `lore_deploy.py` · `_build_parser` `--project` help | "its name is the slug" → "its slug is its lore.yaml's project.slug, else derived from its name" | `git grep "name is the slug"` → only a test docstring ("the name is the slug source", accurate); no test pins the help |
| A5 | `lore_deploy.py` · `_manifest_counts` | dropped the redundant function-local `import sqlite3` (module-level since 99c2b8e) | ruff/typecheck green on file; skill suite §6 |
Backups before edit: `cp -a` of both files at `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/6200082f-f4dd-4ad2-a32f-69e6a6ad2564/scratchpad/probe568/{config.py,lore_deploy.py}.orig`.

### 2.1 Lazy-import receipt (measured 2026-10-31, main tree, `.venv/bin/python`)
```
BEFORE  import loremaster.config → 'slugify' in sys.modules: True   (/home/ejprice/PycharmProjects/lore/loremaster/loremaster/config.py)
AFTER   import loremaster.config → 'slugify' in sys.modules: False
AFTER   import loremaster.server → 'slugify' in sys.modules: False
CONTROL derive_project_slug('odoo-custom') = odoo_custom, ('café') = cafe; slugify loaded after call: True
CONTROL derive_project_slug('---') → ValueError "project directory '---' has no valid lore slug (derived '', …"
```
python-slugify stays a declared loremaster dependency (lore_deploy reaches the normaliser through loremaster's interpreter, F2); the server just no longer needs it to boot.

### 2.2 The two probe instruments (pasted verbatim per brief-base §1)
```python
"""Probe: ManifestOwner on a corrupt (non-SQLite) manifest file, and scaffold file mode."""
import sys, os, stat
from pathlib import Path
sys.path.insert(0, os.getcwd())
import lore_deploy as ld
root = Path(sys.argv[1])
ld.MANIFEST_DIR = root / "state"
ld.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
(ld.MANIFEST_DIR / "corrupt.db").write_bytes(b"this is not a sqlite database at all, just text" * 20)
owner = ld.ManifestOwner("corrupt")
try:
    print("recorded_path ->", owner.recorded_path())
except Exception as error:
    print("recorded_path RAISED", type(error).__mro__[:3], error)
proj = root / "corrupt"
proj.mkdir(exist_ok=True)
ld._container_workspace_source = lambda name: None
try:
    print("_slug_collision ->", ld._slug_collision(proj, "corrupt"))
except Exception as error:
    print("_slug_collision RAISED", type(error).__name__, error, "is RuntimeError:", isinstance(error, RuntimeError))
mode_proj = root / "Mode Proj"
mode_proj.mkdir(exist_ok=True)
cfg = mode_proj / "lore.yaml"
cfg.unlink(missing_ok=True)
ld._scaffold_lore_yaml(mode_proj, cfg)
print("scaffold mode:", oct(stat.S_IMODE(cfg.stat().st_mode)), "umask-default would be", oct(0o666 & ~0o022))
print("leftover staged:", [p.name for p in mode_proj.iterdir() if p.name.endswith(".scaffold")])
```
Run: `cd skills/lore-deploy/scripts && ../../../.venv/bin/python probe_owner.py <scratch>`. Before A3: `0o600`; after: `0o644`. A2 output unchanged by my edits (still raises — routed, not fixed).

## 3. Builder's two unpinned readings — verdicts
1. **Container mounts THIS path + legacy manifest + no lore.yaml → builder refuses as "unknown owner" (reading a).** CORRECT per the Addendum: "only a FRESH setup (no `lore.yaml` yet) meeting an ownerless manifest is refused". F4's "from the container when that shows it" governs what a refusal NAMES, not what proves ownership. Reading (b) would invent an ownership rule nobody ruled. Nit: the refusal says "unknown owner" while the container names this path — true of the manifest, but a consumer could read it as false. Route: pin (a) (item C3).
2. **Container mounts THIS path, manifest records ANOTHER → builder refuses (either one naming another path refuses).** CORRECT per F4 ("whose manifest OR container already belongs to a DIFFERENT project path"). The wrong build that short-circuits on the container passes the whole contract → route a pin (item C2).

## 4. Test-smell list on the contract (reported, never patched)
| id | smell | wrong build that survives |
|---|---|---|
| S1 | **Fixture fiction.** `PodmanShim._index_like_the_real_indexer` says "Create the manifest the real cold index creates: `<slug>.db` with its schema", but per RULING-572 (measured at 0c7477c) no loremaster code writes `<slug>.db` since P5. Every fresh-setup pin therefore runs on a manifest production never has (THE FIXTURE GUARANTEES THE ONE CONDITION…). | any build whose `already provisioned` / `status` logic depends on the indexer creating `<slug>.db`. Overlaps #572; the sibling's round should replace it. |
| S2 | No pin for reading 2 (container=this, manifest=other). | `_slug_collision` returning `None` when the container mount equals this path |
| S3 | No pin for reading 1 (container=this + legacy manifest + no lore.yaml). | backfill-instead-of-refuse |
| S4 | No corrupt-manifest fixture (A2). | the current build (traceback) |
| S5 | No file-mode pin on the scaffolded lore.yaml (A3). | 99c2b8e as committed (0600) |
| S6 | `stop`/`status` on an UN-configured hyphenated dir: no pin. `TestEveryVerbUsesTheConfiguredSlug` always writes a lore.yaml first. | `_project_slug` returning raw `project.name` when no lore.yaml, for stop/status only (M1 shows setup's use of the branch IS pinned 4×) |
| S7 | No symlinked project-path fixture (A9); `tmp_path` is already resolved, so `.resolve()` on either side of the owner compare is undiscriminated. | owner compare by raw `str(project)` |
| S8 | `test_main_returns_exit_error_for_an_unslugifiable_dir_not_a_traceback` and `test_setup_refuses_naming_the_directory_and_writes_nothing[*]` stay green under M1: the scaffold's own `_derive_slug` refuses, so neither pins `_project_slug`'s branch. Not wrong — just narrower than its name suggests. | — |

## 5b. Mutation M1 — RESULT (log `/var/tmp/claude-1000/slug568-audit-logs/mutation-m1.log`, scratch TREE=c6e7d172…, `loremaster.__file__ = /var/tmp/claude-1000/slug568-audit-scratch/loremaster/loremaster/__init__.py`)
- mutation LANDED (anchor matched exactly once); tree restored byte-exact (md5 7b600381…).
- pytest: `4 failed, 138 passed`; `mutation_proof.py` EXIT=4 = **PROOF FAILED (declared ≠ observed)**, for two reasons, both mine:
  1. **id form (#560):** I declared the rootdir form `skills/lore-deploy/scripts/test_scaffold_slug.py::…` (what `--collect-only -q` printed); the run from the scripts dir reports the cwd form `test_scaffold_slug.py::…`. The declared test DID go red, under the other spelling. ⚠ So `--collect-only` and the FAILED summary can disagree on id form when cwd ≠ rootdir — the tool's own "take ids from --collect-only" advice is insufficient here. Known class #560 (the brief's "#560 id form"); not re-filed.
  2. **under-declared:** 3 more reds I did not predict: `TestSetupRecordsAndHonoursItsOwnProjectPath::test_fresh_setup_records_this_project_path_in_the_manifest`, `…::test_fresh_setup_refuses_a_legacy_manifest_as_an_unknown_owner`, `TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_manifest_records_another_project[derived]`.
- Predicted survivors stayed green (S8), as declared.
- **Verdict:** the branch I picked as weakest is pinned 4× through `setup`; it is UNPINNED only through `stop`/`status` (S6). Not re-run with a corrected declared set: the extra three were read off the output, and re-declaring them would be the tautology `mutation_proof.py` warns about. A clean re-proof needs a declaration made by someone who has not seen this output.

## 6. Routed contract items (for the lead → a contract author; I patched no tests)
- **C1 (A2, defect vs F5):** a corrupt (non-SQLite) `<slug>.db` makes `setup` traceback (`sqlite3.DatabaseError` from `ManifestOwner.recorded_path`, not caught, and `verb_setup` does not wrap `_slug_collision`). Pin: setup over a garbage manifest → `_EXIT_ERROR`, a stderr line naming the manifest, nothing created. Suggested edit: in `recorded_path`, keep `except sqlite3.OperationalError: return None` and add `except sqlite3.DatabaseError as error: raise SlugRefusal(f"manifest {self.manifest} is unreadable ({error}); {_SLUG_REMEDY}")`, then wrap `_slug_collision(...)` in `verb_setup` with `except RuntimeError` → `setup: {error}` + `_EXIT_ERROR`. (`record()` on a corrupt file would need the same handling.) ⚠ Overlaps #572's ledger round, which rewrites `ManifestOwner`; sequence C1 into that round.
- **C2:** container mounts THIS path, manifest records ANOTHER → refused (F4 "manifest or container"). Kills the container-short-circuit wrong build.
- **C3:** container mounts THIS path + legacy manifest + no lore.yaml → refused as unknown owner (Addendum literal).
- **C4:** a scaffolded lore.yaml has umask-default mode (0644 under umask 022), not 0600. RED on 99c2b8e as committed, GREEN after A3.
- **C5:** `stop` / `status` on a hyphenated dir with NO lore.yaml use the derived slug (`lore-odoo_custom`), not the raw name.
- **S1 (fixture fiction)** goes to the #572 round: the shim's "the real cold index creates `<slug>.db`" contradicts RULING-572's measurement.
- **A7 (escalation, ruled behaviour):** see §1. Possible closing rule if the operator wants it: on the legacy-backfill path, also consult `podman container inspect` of a STOPPED container (inspect works on stopped containers; only `stop`'s `rm` loses it). Not a builder decision.

## 7. Gate receipts (my runs; logs at `/var/tmp/claude-1000/slug568-audit-logs/`)
My two edited files were last written 20:02:34. Every gate below started after that, so all reflect the final content (config.py md5 `badfe82e4125c50e50a04832ce2e913d`, lore_deploy.py md5 `7b600381d9185264f05e9e3739715e11`). `TREE=` differs per row because untracked files (this report, the sibling's `test_ledger_572.py`) keep changing; it will not equal the commit's TREE. Re-verify by md5 of the two files.
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| skill suite (clean) | `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q . ../tests -n 8 --timeout=300 -p no:cacheprovider -rfE --ignore=test_ledger_572.py` | `skill-suite-no572.log` | 0 | 348 passed in 27.25s | f497192d… |
| skill suite (as briefed) | same without `--ignore` | `skill-suite.log` | 1 | 43 failed, 354 passed; 43/43 FAILED lines in `test_ledger_572.py`, 0 elsewhere (my grep) | 6f1a1457… |
| test_config | `systemd-run … uv run python -m pytest -q loremaster/tests/test_config.py -n 8 --timeout=300 -p no:cacheprovider -rfE` | `test-config.log` | 0 | 90 passed in 1.61s | 6f1a1457… |
| typecheck | `bash scripts/typecheck.sh` | `typecheck.log` | 1 | 82 errors (loremaster leg, 31 test files) + 1 (scripts leg, `test_forgery_door_sweep.py`); other legs Success; 0 hits for config.py/lore_deploy.py | 6f1a1457… |
| ruff (my files) | `uv run ruff check loremaster/loremaster/config.py skills/lore-deploy/scripts/lore_deploy.py` | `ruff-currency.log` | 0 | All checks passed! | c6e7d172… |
| currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `ruff-currency.log` | 1 | typecheck RED_ADJUDICATED (83; packet-58 + 64b-i) · ruff RED_ORPHANED 1 (`test_ledger_572.py:359:111` E501, the sibling's) · pytest NOT_RUN | c6e7d172… |
| mutation M1 | §5 | `mutation-m1.log` | 4 | 4 failed, 138 passed | c6e7d172… (scratch) |
I compared the typecheck count with the builder's receipt (83, same files): no new errors from either leg.

## 8. Routing / fan-out (actual)
| step | tier | who | note |
|---|---|---|---|
| cold review, readings, smells, mutation design+verdict | 3 | me | audit judgment |
| slug-consumer grep, prior-art grep (512 py files) | 1 | me, inline batch | 1 file / tiny output, read in full |
| probes (corrupt manifest, file mode, lazy import) | 1 | me, inline | 1 command each, on the critical path |
| 5 gate/mutation runs | 1 | haiku-runner ×5 | RAN lines checked; count lines re-read from logs myself |
Fan-out: haiku 5 · sonnet 0 · peak 3. Tools: no DENIED calls. lore: `lore_search` at budget=700 returned a single stub hit (floor-of-one notice, correctly disclosed); I fell back to grep for the prior-art sweep (case (c)) and say so here.
