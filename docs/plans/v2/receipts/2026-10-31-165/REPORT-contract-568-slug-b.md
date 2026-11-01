# REPORT-contract-568-slug-b

brief-base v25 read

brief project v7 read

## SUMMARY (contract-568-slug-b · finding #568 · 2026-10-31 · HEAD `eba0a46`)
- **STATE: DONE — contract written; RED at HEAD and satisfiable. FORKS F1–F5 below need rulings before a builder starts.** No adversary has graded it (tdd-light).
- **File:** `skills/lore-deploy/scripts/test_scaffold_slug.py` (new). Nothing else was edited.
- **Chokepoint named:** ONE project-slug resolver in `lore_deploy.py`, routing ALL EIGHT sites that today derive `project.name` independently, plus a scaffold that validates before leaving a file and quotes the slug. **#568 is the scaffold instance of a class**: seven more verbs and helpers derive the slug from the raw dir name, so a scaffold-only fix leaves the container name, env-file, manifest, `.mcp.json` key and setup's provisioned check disagreeing with the config's slug.
- **Phase 0:** eight consumers (table below) · no normaliser anywhere (lorerunes / loremaster / skills / scripts searched) · python-slugify 9.1.3 read: it matches the whole valid table but strips/collapses/transliterates the edge names (F1) · the scaffold runs ONLY when lore.yaml is absent (`verb_setup`), and both live deployments (`lore`, `demand_intelligence`) are already-valid slugs equal to their dir names, so an identity-on-valid normaliser renames nothing (pinned).
- **RED at HEAD** (the final file): **46 failed / 17 passed / 63 collected** (`test_scaffold_slug.py` + unchanged `test_scaffold_config.py`), 0 collection/import errors. Every failure is an assertion or `pytest.fail`. The 17 passing are by-design guards: 4 existing scaffold tests; identity rows for `lore`/`demand_intelligence`; valid-or-nothing for `lore #2` and the newline name; 4 fork-name rows that HEAD refuses; the existing-lore.yaml pin.
- **Satisfiability** (scratch `/var/tmp/claude-1000/slug568b-scratch` via `scripts/scratch_copy.sh`, `LORE_PYTHON` exported, `loremaster.__file__ = /var/tmp/claude-1000/slug568b-scratch/loremaster/loremaster/__init__.py`): the whole skill suite (`. ../tests`) gives **321 passed / 0 failed**.
- **Gates:** `ruff` GREEN. Currency `--legs typecheck,ruff`: typecheck RED_ADJUDICATED (packet-58 owned, none of mine), ruff GREEN, **RED_ORPHANED 0**. The CURRENCY line still reads FAIL only for `pytest NOT_RUN`, which `--legs` causes by design.
- **HEAD defects measured beyond #568:** (1) a failed scaffold LEAVES the invalid lore.yaml behind, so the next setup skips the scaffold; (2) the dir name is rendered into YAML unescaped: `lore #2` → slug `lore` (silent truncation via a YAML comment), and `demo\n  root: elsewhere` → slug `demo` with an injected duplicate `root:` key, masked only by template ordering. Both are pinned.
- **Odoo-20 portability: n/a — no Odoo seam touched.**
- **Package line:** slug normalisation → python-slugify 9.1.3 (`slugify(text, separator=..., regex_pattern=..., lowercase=..., allow_unicode=...)`, read via the installed signature + a live run over the fixture names) → **does the job on every valid-table row; edge semantics differ from the brief → fork F1; packaging → fork F2.**
- **Fan-out:** haiku 8 (all `haiku-runner`: RED×2, satisfiability×2, currency×3, ruff×1) · sonnet 0 · peak 3. Phase 0 sweeps ran inline as two parallel batches (small; I read all output).

### Runs used (more than 2: reason below)
| # | label | result |
|---|---|---|
| 1 | RED at HEAD | 50 F / 13 P |
| 2 | satisfiability (scratch) | 2 F / 319 P: **both CONTRACT defects**, fixed: the alphanumeric pin failed a fork name's allowed refusal (`_private`); the fixture `demo\n  root: /etc` held a `/`, so the tmp path nested and `project.name` was `etc` (my first-round "HEAD forges slug `etc`" claim is RETRACTED) |
| 3 | currency | typecheck orphan in my file (`real_run: object` → Any), fixed with a typed `Callable` |
| 4 | RED re-run after fixture fix | 46 F / 17 P (final) |
| 5 | satisfiability re-run | 321 P / 0 F (final) |
| 6 | currency | ruff E501 on my new comment, fixed (comment-only; runs 4–5 are behaviourally identical) |
| 7 | currency | RED_ORPHANED 0 (final) |
| 8 | ruff (file) | All checks passed |

### FORKS (escalated; none silently chosen in the PINS. My pick is stated for each.)
- **F1 — edge-name policy.** (a) The brief: per-character map to `_`; refuse a leading `_` after mapping (`_private`, `-draft`, `.config` refused; `café` → `caf_`; `odoo--custom` → `odoo__custom`). (b) python-slugify: strip leading/trailing separators, collapse runs, transliterate (`_private` → `private`, `café` → `cafe`, `日本語` → `ri_ben_yu`); refuse only when the result is empty. **Contract:** pins only the intersection; the edge names are bound by the ∀ pins (valid-or-nothing, no ASCII alphanumeric lost). **My pick: (b)** (packages-over-hand-rolling; friendlier edges), IF F2 resolves cleanly. Otherwise (a).
- **F2 — where the normaliser lives.** `lore_deploy.py` is stdlib-only and invoked as bare `python3 …/lore_deploy.py` (SKILL.md). Options: (i) stdlib per-character map in the skill (forces F1=a); (ii) python-slugify via a PEP 723 uv-script conversion (changes the documented invocation); (iii) a normaliser beside `SLUG_PATTERN` in loremaster (or `lorerunes`), reached through `_loremaster_python()`, which the scaffold already depends on for validation. **My pick: (iii)**: the slug RULE then lives with its PATTERN, one owner; python-slugify joins loremaster's deps.
- **F3 — which slug the verbs use when an operator hand-edits `project.slug` ≠ the derived one.** (A) normalise(dir) everywhere: pure, no config read (my reference build). (B) the config's `project.slug` when lore.yaml exists, else the normaliser: the config is the single source of truth, but stop/status/env-file need a config read. **Spec-silent; my pick: (B).** The contract's agreement pins use a config whose slug equals the derived one, so they bind both readings.
- **F4 — cross-project slug collision (NEW, spec-silent).** `odoo-custom` and `odoo_custom` (or `Lore` and `lore`) derive the SAME slug under every reading, and so share a store database, a manifest, a container name and a secrets file. Nothing detects it. Should `setup` refuse when the derived slug's manifest or container already belongs to a different project path? **My pick: yes, refuse loudly. Operator ruling needed.** Not pinned.
- **F5 — refusal surface.** Raise (`RuntimeError`, today's scaffold-failure style, a traceback from `main`) vs return `_EXIT_ERROR` with a stderr line (every other setup refusal's style). The contract accepts either. **My pick: `_EXIT_ERROR` + stderr.** Related: `main` resolves the env-file (a slug consumer) BEFORE its `project.is_dir()` check, so a raising resolver crashes `main` before the friendlier guard.

## Routing table (written before the first sweep, per brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| Phase 0a slug-consumer sweep (skill dir + scripts/, grep; lore_impact for loremaster side) | 1 | self, ONE parallel batch | set is small (one skill dir, ~10 files); I read all output anyway; coverage line recorded |
| Phase 0b normaliser search (lorerunes, loremaster, skills, scripts) | 1 | self, same parallel batch | small; feeds the chokepoint decision directly |
| Phase 0c package survey (python-slugify installed API) | 3 | self | a ruling; read the installed signature |
| Phase 0d existing-lore.yaml guard receipt | 3 | self | load-bearing claim about control flow |
| contract design + test file | 3 | self | contract authorship (never delegated) |
| RED at HEAD run | 1 | haiku-runner | test run |
| satisfiability: scratch_copy + reference fix | 3 | self | reference build is a correctness claim |
| satisfiability full skill suite in scratch | 1 | haiku-runner | test run |
| ruff + currency typecheck,ruff | 1 | haiku-runner | gate run |

## Phase 0 (measured 2026-10-31 at `eba0a46`)

### Slug consumers: eight independent `slug = project.name` derivations in `skills/lore-deploy/scripts/lore_deploy.py`
Swept by grep: `scripts/` and the skill are a seam `lore_impact` cannot see (#507). Coverage: 1792 lines; 47 `project.name|slug` hits, each read.
| symbol | consumer | what breaks on `odoo-custom` with a scaffold-only fix |
|---|---|---|
| `_scaffold_lore_yaml` | `project.slug` in lore.yaml → loremaster store database (`effective_surreal_database`), state paths `<slug>.db` / `<slug>.memory.db` | **#568 itself**: schema error at scaffold time |
| `_resolve_env_file` | `~/docker/mcp/lore-secrets/<slug>.env` | env-file named for the raw dir, not the slug |
| `_launch_container` | `podman run --name lore-<slug>` | container named for the raw dir |
| `_launch_or_exit_loudly` | the `lore-<slug>` label in error text | wrong name in error text |
| `verb_setup` | the manifest `MANIFEST_DIR/<slug>.db` "already provisioned" check; `.mcp.json` `lore_<slug>` key (via `merge_mcp_json.py --slug`) | re-run never sees the provisioned manifest, so the cold index re-runs every time; `.mcp.json` key `lore_odoo-custom` ≠ slug |
| `verb_start` | container name (inspect / rm / await / gate); `.mcp.json` key | container-name mismatch with stop/status if only some sites are fixed |
| `verb_stop` | `podman stop/rm lore-<slug>` | cannot find the container `start` made if the two disagree |
| `verb_status` | container name; manifest `MANIFEST_DIR/<slug>.db` | reports "no manifest (not yet set up)" for a provisioned project |
**So a scaffold-only fix is the instance, not the class.** The contract pins the outcome over every door: for a scaffolded project, every slug a verb uses equals the `project.slug` in its `lore.yaml`.

### Normaliser search
Searched `lorerunes/lorerunes/*` (`identifiers.py` holds the comms identity charset `^[a-z0-9][a-z0-9_-]{0,63}$`, a predicate with no normaliser; the others are unrelated), `loremaster/**/*.py`, `skills/`, `scripts/` (grep `def (slugify|_?slug*|_?normali[sz]e*)`, `SLUG_PATTERN`, `slugify` imports; 480 tracked .py files). **No slug normaliser exists anywhere.** `SLUG_PATTERN` lives once, in `loremaster.config` (`SlugStr`). The `_normalise*` hits (`store/_txn.py`, `search.py`, tests) are SQL/filter/text normalisers, unrelated.

### Package survey
- **python-slugify 9.1.3**: read the installed signature `slugify(text, ..., separator='-', regex_pattern=None, lowercase=True, allow_unicode=False, ...)` and ran it live (`uv run --no-project --with python-slugify`, NOT added to any project). With `separator="_"`:
  - **The valid table matches**: `odoo-custom→odoo_custom`, `transcribe-craig→transcribe_craig`, `PP-Odoo→pp_odoo`, `pp-odoo→pp_odoo`, `lore→lore`, `demand_intelligence→demand_intelligence`, `my.project→my_project`, `My Project→my_project`, `2026-forecast→2026_forecast`, `LoreMaster→loremaster`.
  - **No-alnum names → `''`**: `---`, `...`, `_-_`. That is the natural refusal trigger.
  - **It DIFFERS from the brief's property on the edges**: it strips leading/trailing separators (`_private→private`, `-draft→draft`, `.config→config`, `project-→project`), collapses runs (`odoo--custom→odoo_custom`), and transliterates (`café→cafe`, `日本語→ri_ben_yu`). The brief says a leading `_` after mapping is REFUSED → **FORK F1**.
- **Packaging constraint**: `lore_deploy.py` is stdlib-only, invoked as bare `python3 ~/.claude/skills/lore-deploy/scripts/lore_deploy.py` (SKILL.md). The package needs either a PEP 723/uv-script conversion or a home in the loremaster venv (already reached via `_loremaster_python()` for config reads) → **FORK F2**.

### Existing deployments: a normaliser cannot change them
- Code (`verb_setup`): `if not config_path.exists(): _scaffold_lore_yaml(...)`. The scaffold runs ONLY when no lore.yaml exists. `verb_start` refuses without lore.yaml (`start: no ... run setup first`) and never scaffolds.
- Host, measured: containers `lore-lore`, `lore-demand_intelligence`; state `lore.db`, `demand_intelligence.db`; secrets `lore.env`, `demand_intelligence.env`; lore.yaml slugs `lore` (dir `lore`) and `demand_intelligence` (dir `pp-odoo/demand_intelligence`). **Both live slugs equal their directory names and are already valid**, so any normaliser that is the identity on valid slugs renames nothing. Pinned (identity rows plus an existing-lore.yaml-unchanged pin).

### Side defect found (at `eba0a46`)
`_scaffold_lore_yaml` writes lore.yaml BEFORE validating it. On failure it raises and leaves the invalid file behind, so the NEXT `setup` skips the scaffold (config exists) and fails later on a broken config. That is what happens to `odoo-custom` today. Pinned as an outcome: a scaffold that does not produce a valid lore.yaml leaves none.

## Contract
**File:** `skills/lore-deploy/scripts/test_scaffold_slug.py` (new; 63 collected together with the unchanged `test_scaffold_config.py`). Nothing else in the repo was edited.

**Plain English:**
1. A directory name that has a valid slug scaffolds a lore.yaml whose `project.slug` is the case-folded name with separators → `_`, loadable by the real `load_config`.
2. No ASCII letter or digit is dropped or invented.
3. A name with nothing to build a slug from is refused loudly and leaves nothing behind.
4. For every name, a scaffold leaves a loadable lore.yaml or none.
5. For `odoo-custom` declaring `odoo_custom`, every verb (env-file, start, stop, status, setup re-run, setup end-to-end) uses `odoo_custom`.
6. An existing lore.yaml is byte-identical after setup.

**Chokepoint the contract names:** ONE project-slug resolver in `lore_deploy.py`. All eight sites that today derive `project.name` independently route through it (`_resolve_env_file`, `_scaffold_lore_yaml`, `_launch_container`, `_launch_or_exit_loudly`, `verb_setup`, `verb_start`, `verb_stop`, `verb_status`).
- It owns: (a) the normalisation, (b) the loud refusal, (c) a scaffold that validates before leaving a file and quotes the slug in the YAML.
- The pins are seam-agnostic. They drive the verbs and observe podman argv, `.mcp.json`, the manifest read and the env-file path, never a function name. So a site that bypasses the resolver diverges on `odoo-custom` and goes RED.
- Where the normaliser's POLICY lives (stdlib in the skill, python-slugify, or loremaster/lorerunes beside `SLUG_PATTERN`) is FORK F2.

### Pins → the wrong build each one kills
| pin (class::test) | wrong build it kills |
|---|---|
| `TestScaffoldDerivesTheSlugFromTheDirectoryName` (11 rows) | lowercase-only (`odoo-custom` stays hyphenated); replace-only-`-` (`my.project`, `My Project`, `LoreMaster`, `PP-Odoo`→`PP_Odoo`); unquoted YAML (`2026` loads as int → rejected); a validator that accepts a slug the config rejects (round-trip via real `load_config`); a normaliser that is not the identity on `lore`/`demand_intelligence` (renames a live deployment) |
| `…ValidLoreYamlOrNone::test_scaffold_outcome_is_valid_or_nothing` (∀ 21 names) | write-then-validate leaving an invalid lore.yaml (**HEAD's own behaviour**); a refusal that does not name the dir; a rendered name forging `project.root` |
| `…::test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order` (∀ 17 ASCII names: 11 valid + 6 ASCII fork/hostile) | unescaped YAML render: **HEAD turns `lore #2` into slug `lore`** (observed in the RED log; a silent truncation through a YAML comment), and a newline-forged name loses letters; a normaliser that drops digits; a "collapse to first word" build. (A first-round claim that HEAD forged `demo\n  root: /etc` into slug `etc` is RETRACTED: the fixture's `/` nested the tmp path, so `project.name` was `etc`. The fixture is now `demo\n  root: elsewhere`.); a normaliser that drops digits or a "collapse to first word" build |
| `TestANameWithNoValidSlugIsRefusedLoudly` (`---`, `...`, `_-_`) | a build that mangles to a placeholder slug and carries on (probes pass, so it would reach the cold index: `index_calls` must be empty); a refusal that leaves lore.yaml behind; a message that names neither the dir, the field nor the file |
| `TestSetupProvisionsAHyphenatedProjectEndToEnd` | **the #568 path itself**; a build that fixes the scaffold but passes the raw name to `merge_mcp_json.py` (`.mcp.json` key) or indexes against another config |
| `TestEveryVerbUsesTheConfiguredSlug::test_env_file_…` | env-file still `odoo-custom.env` |
| `…::test_start_…` | `podman run --name lore-odoo-custom` / inspect on the raw name; `.mcp.json` `lore_odoo-custom` |
| `…::test_stop_…` | stop/rm still address the raw name (cannot stop the container start made) |
| `…::test_status_…` | status looks for `odoo-custom.db` and reports a provisioned project as "not yet set up" |
| `…::test_setup_recognises_a_provisioned_project_…` | the "already provisioned" check on the raw name misses the manifest and re-runs the expensive cold index (here: falls through to the absent env-file and fails) |
| `TestAnExistingLoreYamlIsNeverRewritten` | a normaliser that "migrates" an existing lore.yaml's slug, or re-scaffolds when slug ≠ normalise(dir). **Passes at HEAD by design** (preserved guard) |

### Adversarial pre-flight → coverage
- **Wrong unit / encoding:** case (capitals) → derivation rows `PP-Odoo`, `LoreMaster`. YAML typing (digits → int) → row `2026`.
- **Separator classes:** hyphen, dot, space → derivation rows. Leading/trailing separator, runs → ∀ pins only (fork F1).
- **Sign flip / null / zero / boundary:** an empty slug (`---`, `...`, `_-_`) → refusal pins. A leading digit (legal boundary) → `2026-forecast`, `2026`.
- **Degenerate driver:** an already-valid name must be inert → identity rows `lore`, `demand_intelligence`.
- **Real-distribution tails:** real names `odoo-custom`, `transcribe-craig`, `pp-odoo` (on this host), and the two live deployments.
- **Producer↔consumer seams:** scaffold → lore.yaml → `load_config` (round-trip); config slug → container / env-file / manifest / `.mcp.json` / cold-index (agreement class); lore.yaml existing → setup (byte-identical pin).
- **Hostile rendered text** (the dir name is rendered into YAML): newline + forged key, `: `, ` #` → ∀ pins. One truncation is observed at HEAD (`lore #2` → `lore`).
- **Non-ASCII** (`café`) → ∀ valid-or-nothing only (the value is fork F1; excluded from the alphanumeric pin because transliteration legitimately changes letters).
- **Scoped out, with reason:**
  - name length (no length bound in `SLUG_PATTERN`; podman and Surreal limits are not in the spec, and no real repo name approaches them);
  - the operator hand-editing `project.slug` to differ from the dir (fork F3, a spec-silent consumer choice).

### Realism & independence clauses
- ☑ **Production-realistic inputs:** real repo names (the #568 report, `~/PycharmProjects/pp-odoo`) and the two live slugs measured 2026-10-31. The operator config comes from the shared production-shaped builder `config_reader_fake.realistic_config_document`. Nothing reads a live DB or host state at test time; `MANIFEST_DIR` and `LORE_SECRETS_DIR` are redirected to tmp.
- ☑ **Independent expected values:** every slug is hand-computed from the requirement in `VALID_NAME_TO_SLUG`; the ∀ pins use properties (`SLUG_PATTERN`, alphanumeric sequence), never the implementation's formula.
- ☑ **Seam coverage:** the real scaffold, the real `_read_config_field` subprocess, the real `merge_mcp_json.py` (the `.mcp.json` on disk is asserted), and the real `load_config`. Only podman, the cold index and the network probes are stubbed, at `_run` / probe seams.
- ☐ **Magnitude bound:** not applicable because there is no derived numeric output (the manifest count in the status pin is a literal fixture echo).
- ☑ **Shared conventions:** `SLUG_PATTERN` is imported from `loremaster.config` (the one source); the secrets dir and manifest dir come from the module constants; container `lore-<slug>` and `.mcp.json` `lore_<slug>` come from SKILL.md / `merge_mcp_json.py`.
- ☑ **Hostile fixtures for rendered stored text:** APPLIES (the directory name is rendered into the lore.yaml template). Covered by the newline+forged-key, `: ` and ` #` names; the render must stay unambiguous (root unforged, no alphanumeric lost).
- ☐ **Input accounting:** not applicable because the unit maps one name to one slug, with no collection transform.

### Security note (to the lead)
The YAML render of a directory name is unescaped at HEAD: `lore #2` silently truncates to slug `lore` (measured), and a newline in the name injects raw YAML lines. The threat model is honest-operator (the operator names their own directory), so I classify this as a correctness defect, not a security boundary. But it is a render-injection class, so I am flagging it per the tdd-light rule. The fix (normalise before render, quote the scalar) closes it by construction.

## Reference diff (SATISFIABILITY ONLY — not a proposed build; it takes F1=a, F2=i, F3=A, F5=raise)
```diff
--- ../slug568b-lore_deploy.orig.py	2026-10-31 17:32:34.724169492 -0400
+++ skills/lore-deploy/scripts/lore_deploy.py	2026-10-31 17:32:34.744170027 -0400
@@ -30,6 +30,7 @@
 import argparse
 import json
 import os
+import re
 import shlex
 import shutil
 import socket
@@ -183,6 +184,21 @@
     )
 
 
+# The project slug charset (mirrors loremaster.config.SLUG_PATTERN — REFERENCE BUILD ONLY).
+_PROJECT_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9_]*")
+
+
+def _project_slug(project: Path) -> str:
+    """Derive the project slug from its directory name: case-fold, non-[a-z0-9] -> ``_``."""
+    slug = re.sub(r"[^a-z0-9]", "_", project.name.lower())
+    if not _PROJECT_SLUG_RE.fullmatch(slug):
+        raise RuntimeError(
+            f"project directory {project.name!r} has no valid lore slug (derived {slug!r}); "
+            f"write {project / 'lore.yaml'} by hand with a valid project.slug, or rename the directory"
+        )
+    return slug
+
+
 def _container_state(name: str) -> str | None:
     """Return a container's state string (e.g. ``running``/``exited``) or ``None`` if absent."""
     result = _run(
@@ -421,7 +437,7 @@
     if explicit is not None:
         # Honor an operator-supplied path verbatim — no per-slug rewriting.
         return Path(explicit)
-    slug = project.name
+    slug = _project_slug(project)
     return LORE_SECRETS_DIR / f"{slug}.env"
 
 
@@ -583,7 +599,7 @@
     should review them for the project's real layout. Validated by parsing the
     written file through the real LoreConfig before returning.
     """
-    slug = project.name
+    slug = _project_slug(project)
     port = _free_port(DEFAULT_PORT_BASE)
     always_prune = [".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]
     excludes = always_prune + [n for n in _gitignore_dir_names(project) if n not in always_prune]
@@ -594,7 +610,7 @@
 schema_version: 1
 
 project:
-  slug: {slug}
+  slug: "{slug}"
   root: .
 
 embedding:
@@ -663,6 +679,12 @@
   port: {port}
 """
     config_path.write_text(content, encoding="utf-8")
+    try:
+        _validate_config_schema(config_path)
+    except RuntimeError:
+        config_path.unlink(missing_ok=True)
+        raise
+    return
     # Fail loud if the scaffold does not parse against the real model. Schema-only
     # (LoreConfig.model_validate, NOT load_config): the scaffold emits env-var
     # *names*, never secrets, so validation must not require ANTHROPIC_API_KEY to
@@ -807,7 +829,7 @@
         subprocess.CalledProcessError: ``podman run`` fails.
     """
     binds_snapshot = _require_launchable_snapshot(config_path)
-    slug = project.name
+    slug = _project_slug(project)
     cmd = [
         "podman", "run", "-d", "--name", f"lore-{slug}",
         "--network=host",
@@ -862,7 +884,7 @@
     Returns:
         ``_EXIT_OK`` when the launch succeeded, ``_EXIT_ERROR`` otherwise.
     """
-    container_name = f"lore-{project.name}"
+    container_name = f"lore-{_project_slug(project)}"
     try:
         _launch_container(project, config_path, env_file)
     except _LAUNCH_FAILURES as error:
@@ -880,7 +902,7 @@
 def verb_setup(project: Path, env_file: Path) -> int:  # noqa: PLR0911 - P8e reworks this skill
     """``setup`` — idempotent one-time provisioning (expensive parts no-op on re-run)."""
     config_path = project / "lore.yaml"
-    slug = project.name
+    slug = _project_slug(project)
 
     # 1. Detect an existing deployment → no-op the expensive parts.
     already = config_path.exists() and (MANIFEST_DIR / f"{slug}.db").exists()
@@ -974,7 +996,7 @@
     not check".
     """
     config_path = project / "lore.yaml"
-    slug = project.name
+    slug = _project_slug(project)
     container_name = f"lore-{slug}"
     if not config_path.exists():
         print(f"start: no {config_path}; run `setup` first.", file=sys.stderr)
@@ -1137,7 +1159,7 @@
 
 def verb_stop(project: Path) -> int:
     """``stop`` — stop + remove the container (store data + manifest persist; idempotent)."""
-    slug = project.name
+    slug = _project_slug(project)
     state = _container_state(f"lore-{slug}")
     if state is None:
         print(f"stop: lore-{slug} not running — no-op.")
@@ -1158,7 +1180,7 @@
     hold the port unbound for minutes after the container starts). A stopped
     container skips the probe (nothing to probe).
     """
-    slug = project.name
+    slug = _project_slug(project)
     container_name = f"lore-{slug}"
     config_path = project / "lore.yaml"
     state = _container_state(container_name)
```

## Removed-behavior inventory
None was supplied. The change deletes no behaviour, except the raw-dir-name slug at eight sites, which is the defect itself.

## Noticed outside this change
- `test_scaffold_config.py`'s only fixture is `acme_widgets`, an already-valid name. That parameter-value monoculture is how #568 shipped green. Now covered by the new file; the old file is unchanged.
- The currency gate exits 1 under `--legs typecheck,ruff` even at RED_ORPHANED 0, because it renders the unrun pytest leg as an orphan. The brief already says to read verdicts, not the exit (#565); noting that it recurred here.
- The scratch copy `/var/tmp/claude-1000/slug568b-scratch` (with the reference patch) is left in place for the lead to keep or delete.
- Inbox: no lore_comms traffic was addressed to me during the run.


## Round 2 (2026-10-31, rulings `docs/plans/v2/receipts/2026-10-31-165/RULING-568-slug.md`; directive #18012)

**STATE: DONE.** At HEAD `eba0a46`, the only failures are the new pins. Satisfiable against a ruling-aligned reference. **One DEVIATION, disclosed: I edited a pre-existing test file** (below).

### What changed in `skills/lore-deploy/scripts/test_scaffold_slug.py` (80 collected; was 59)
- **F1 bound:** the fork names now carry python-slugify's values (`RULED_EDGE_NAME_TO_SLUG`): `_private→private`, `.config→config`, `project-→project`, `odoo--custom→odoo_custom`, `café→cafe`, plus the hostile `lore #2→lore_2`, `demo\n  root: elsewhere→demo_root_elsewhere`, `proj: ect→proj_ect`. Each is in the derivation, valid-or-nothing and (ASCII) alphanumeric pins. Kills a hand-rolled per-character map (refuses `_private`, gives `odoo__custom`, `caf_`).
- **F3 bound:** `TestEveryVerbUsesTheConfiguredSlug` is parametrized over `odoo_custom` (derived) AND `odoo` (an operator's hand edit), across env-file / start / stop / status / setup-provisioned. The `[odoo]` rows kill a verb that re-derives from the directory instead of reading the config.
- **F5 bound:** the no-valid-slug refusal now demands `_EXIT_ERROR` + stderr and NO raise. New `test_main_returns_exit_error_for_an_unslugifiable_dir_not_a_traceback` (the CLI door). New `test_main_reports_a_missing_project_dir_before_resolving_its_slug`, the F5 rider: is_dir before slug resolution; passes at HEAD as a guard.
- **F4 bound:** new `TestSetupRefusesASlugHeldByAnotherProject`:
  - `test_refuses_when_the_slugs_container_serves_another_project`: container `lore-odoo_custom` mounts `…/elsewhere/odoo_custom`. Expected: `_EXIT_ERROR`; stderr names the slug, THIS path and the HOLDER's path; nothing created (no lore.yaml, index, `.mcp.json`, or podman run/start/stop/rm/kill/restart/create).
  - `test_refuses_when_the_slugs_manifest_exists_for_a_project_without_config`: the stopped holder. Expected: `_EXIT_ERROR`; names the slug and this path; nothing created; manifest bytes untouched.
  - `test_same_project_rerun_with_its_running_container_is_not_refused`: own lore.yaml + manifest + container mounting THIS path. Expected: OK, no re-index, container untouched.
  - `test_same_project_resuming_after_its_scaffold_is_not_refused`: own lore.yaml, no manifest. Expected: completes, one index.
- **Shim:** `PodmanShim` now answers `podman container inspect` faithfully: JSON without `--format`, or a bounded Go-template subset (`{{.A.B}}`, `{{json .X}}`, `{{range .Mounts}}…{{if eq .Destination "…"}}…`). It RAISES on any podman command or template it does not model, so a builder's unmodelled query fails loudly instead of reading as "no container".

### F4b — a gap in the ruling (needs a ruling; not silently chosen)
F4 says name "both paths" when a slug's **manifest** belongs to another project. **The manifest records no owning path** (measured 2026-10-31 on `~/.local/state/lore/{lore,demand_intelligence}.db`: `meta` = `embedding_schema_fingerprint`, `schema_rebuild_status`; `files` = tier-relative `file_path`). `stop` removes the container, so a STOPPED holder leaves no record of its path anywhere. The contract therefore pins the manifest door as "refuse; name the slug and THIS path" and says so in the test docstring. Options:
- (a) Accept: name the holder's path only when a container shows it.
- (b) Have setup record its project path at provisioning (e.g. a manifest `meta` row `project_path`), then name it. Legacy manifests without the row still refuse as "owner unknown".

**My pick: (b)**, with the row written and pinned in the same change. It also gives `status` an owner to show.
- **Related, spec-silent:** a project WITH a lore.yaml whose hand-set slug is held by another project's container. F4 says "derives"; the reference refuses only when there is no lore.yaml. Not pinned. Ruling wanted.

### DEVIATION — `skills/lore-deploy/scripts/test_lore_deploy.py` edited (fixture alignment only; no assertion changed)
The ruling-aligned reference turned 12 pre-existing tests red: 4 were reference gaps (fixed in the reference), and **8 were pre-existing pins whose fixtures structurally contradict F3**.
- `_make_project` wrote a non-config stub (`# stub lore config`).
- `_install_config_reader` installed `ConfigReaderFake` with its DEFAULT slug `lore`, while the project dir was `myproject` / `freshproject` / …, and the tests asserted `lore-<dir>`.
- Under "the config wins" a builder could not satisfy both, and may not edit tests. This is the C-DEF trap.

**The edit:**
- `_make_project` now writes a production-shaped config (`realistic_config_document(slug=<dir>, …)`).
- `_install_config_reader(monkeypatch, tmp_path, project)` takes the project as a REQUIRED argument and installs the fake with `slug=project.name`. No default: CLAUDE.md "fixture factories must not default a parameter the code branches on", and that default manufactured this contradiction.
- 7 call sites, and 2 direct `ConfigReaderFake.install` calls in the fresh-path fixture, pass the project's slug.

The 8 tests affected: `TestVerbStartStaleImageRecreateBehavior::test_verb_start_stale_running_container_is_recreated`, `TestVerbSetupGatesOnSurreal::test_setup_aborts_when_surreal_probe_fails`, `TestVerbStatusImageCurrency` ×3, `TestRecreateGatesOnStorePreflight::test_recreate_proceeds_and_validates_before_teardown_when_probes_ok`, `TestVerbStartRecreateValidatesBeforeTeardown::test_recreate_happy_path_validates_before_teardown`, `TestVerbStartFreshPathParity::test_the_exited_container_is_removed_after_every_precondition_and_before_launch`. **All 8 still pass at HEAD** (whole-suite HEAD run below), so the edit changes no verdict on today's code. Writable-set reading: the brief allows "new or extended test files under `skills/lore-deploy/scripts/`". I read fixture alignment there as in scope. If the lead reads "extended" as add-only, this edit needs a ruling or a revert, and without it the contract is unsatisfiable.

```diff
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bc769b1e-ff81-4566-82cf-f79223799b61/scratchpad/test_lore_deploy.orig.py	2026-10-31 19:25:31.924822841 -0400
+++ /home/ejprice/PycharmProjects/lore/skills/lore-deploy/scripts/test_lore_deploy.py	2026-10-31 19:25:52.719364772 -0400
@@ -215,23 +215,39 @@
 
 
 def _make_project(tmp_path: Path, slug: str) -> Path:
-    """Create a minimal project directory with a stub lore.yaml."""
+    """Create a project directory named ``slug`` with a production-shaped lore.yaml declaring it.
+
+    The lore.yaml's ``project.slug`` equals the directory name, as a scaffolded project's
+    does: every verb reads its slug from that config (#568 ruling F3), so a stub config, or a
+    config naming a different slug, would test a project no setup ever produces.
+    """
     project = tmp_path / slug
     project.mkdir()
-    (project / "lore.yaml").write_text("# stub lore config\n", encoding="utf-8")
+    write_config_document(
+        realistic_config_document(
+            slug=slug, server_port=_LORE_SERVER_PORT, server_path=_LORE_MOUNT_PATH
+        ),
+        project / "lore.yaml",
+    )
     return project
 
 
-def _install_config_reader(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ConfigReaderFake:
+def _install_config_reader(
+    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, project: Path
+) -> ConfigReaderFake:
     """Patch _read_config_field with the shared meaning-based fake over a live-only config.
 
     The config holds the server port + mount these tests assert on and NO static roots,
     so no launch binds the snapshot. The fake answers whatever expression production
-    asks (a port, a mount, the static-root count) from that config, never by keyword.
+    asks (a port, a mount, the static-root count, the slug) from that config, never by
+    keyword. Its ``project.slug`` is ``project``'s directory name (#568 ruling F3: every
+    verb reads the slug from the config), and ``project`` is REQUIRED: a defaulted slug
+    would silently test a project whose config disagrees with its directory.
     """
     return ConfigReaderFake.install(
         monkeypatch,
         tmp_path / "config-reader",
+        slug=project.name,
         server_port=_LORE_SERVER_PORT,
         server_path=_LORE_MOUNT_PATH,
     )
@@ -344,7 +360,7 @@
             return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
 
         monkeypatch.setattr(lore_deploy, "_run", _recording_run)
-        _install_config_reader(monkeypatch, tmp_path)
+        _install_config_reader(monkeypatch, tmp_path, project)
 
         # Record _launch_container calls (the real one would shell out to podman run).
         launch_calls: list[tuple[Path, Path, Path]] = []
@@ -463,7 +479,7 @@
             return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
 
         monkeypatch.setattr(lore_deploy, "_run", _recording_run)
-        _install_config_reader(monkeypatch, tmp_path)
+        _install_config_reader(monkeypatch, tmp_path, project)
 
         launch_calls: list[tuple[Path, Path, Path]] = []
 
@@ -562,7 +578,7 @@
         monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
         monkeypatch.setattr(lore_deploy, "_probe_surreal", lambda *a, **k: lore_deploy._EXIT_OK)
 
-        _install_config_reader(monkeypatch, tmp_path)
+        _install_config_reader(monkeypatch, tmp_path, project)
 
         launch_calls: list[tuple[Path, Path, Path]] = []
 
@@ -846,7 +862,7 @@
         self.monkeypatch.setattr(
             lore_deploy, "_image_id", lambda image: _CURRENT_IMAGE_ID
         )
-        _install_config_reader(self.monkeypatch, self.tmp_path)
+        _install_config_reader(self.monkeypatch, self.tmp_path, self.project)
 
     def install_run_recorder(self) -> None:
         """Record (and succeed) every podman command issued via _run."""
@@ -1482,7 +1498,7 @@
             return lore_deploy._EXIT_OK
 
         monkeypatch.setattr(lore_deploy, "_probe_surreal", _recording_probe_surreal)
-        _install_config_reader(monkeypatch, tmp_path)
+        _install_config_reader(monkeypatch, tmp_path, project)
 
         launch_calls: list[tuple[Path, Path, Path]] = []
         monkeypatch.setattr(
@@ -1523,7 +1539,7 @@
         monkeypatch.setattr(
             lore_deploy, "_probe_surreal", lambda config_path: lore_deploy._EXIT_ERROR
         )
-        _install_config_reader(monkeypatch, tmp_path)
+        _install_config_reader(monkeypatch, tmp_path, project)
 
         launch_calls: list[tuple[Path, Path, Path]] = []
         monkeypatch.setattr(
@@ -2244,7 +2260,7 @@
         # thing a static tier fails against in the snapshot case.
         self.snapshot_root = tmp_path / "lore-snapshot"
         monkeypatch.setattr(lore_deploy, "SNAPSHOT_ROOT", self.snapshot_root)
-        self.reader = _install_config_reader(monkeypatch, tmp_path)
+        self.reader = _install_config_reader(monkeypatch, tmp_path, self.project)
         monkeypatch.setattr(lore_deploy, "_container_state", lambda name: state)
 
         def _recording_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
@@ -2285,13 +2301,16 @@
             self.reader = ConfigReaderFake.install(
                 self.monkeypatch,
                 self.tmp_path / "config-reader-static",
+                slug=self.project.name,
                 server_port=_LORE_SERVER_PORT,
                 server_path=_LORE_MOUNT_PATH,
                 static_tiers=RECORDED_STATIC_TIERS[:1],
             )
         elif precondition == "config_unreadable":
             # A lore.yaml that fails schema validation, so the config read raises (R2).
-            document = realistic_config_document(server_port=_LORE_SERVER_PORT)
+            document = realistic_config_document(
+                slug=self.project.name, server_port=_LORE_SERVER_PORT
+            )
             document["server"]["port"] = "nine-thousand"
             self.reader = ConfigReaderFake.install(
                 self.monkeypatch, self.tmp_path / "config-reader-invalid", document=document
```

### Receipts (round 2)
| run | scope | result |
|---|---|---|
| RED at HEAD | `test_scaffold_slug.py` + `test_scaffold_config.py` | **70 failed / 14 passed / 84**, 0 collection/import errors |
| HEAD, whole skill suite (`. ../tests`) | after the fixture alignment | **70 failed / 272 passed / 342**. **0 failures outside `test_scaffold_slug.py`** |
| satisfiability r2 #1 (scratch) | whole skill suite | 12 F / 330 P: 4 reference gaps (fixed), 8 F3-contradicting fixtures (aligned above) |
| satisfiability r2 #2 (scratch) | whole skill suite | **342 passed / 0 failed** (`LORE_PYTHON` exported; scratch provenance as round 1; python-slugify 9.1.3 + text-unidecode 1.3 in the scratch loremaster env) |
| ruff | both edited files | All checks passed |
| currency `--legs typecheck,ruff` #1 | repo | typecheck RED_ORPHANED: 2× `attr-defined` (`lore_deploy.shutil` is not an explicit export) in my two `main_` pins → fixed by patching `shutil.which` on `shutil` |
| currency #2 | repo | typecheck RED_ADJUDICATED (packet-58 owned), ruff GREEN, **RED_ORPHANED 0** (CURRENCY reads FAIL only for `pytest NOT_RUN`, by `--legs` design) |
| `-k main_` re-run after that fix | HEAD / scratch | HEAD **1 F / 1 P** (CLI-door pin RED: `main` raised the scaffold `RuntimeError`; missing-dir guard green) · scratch **2 P / 0 F** |

**Passing at HEAD (10 in the new file, all guards):** identity rows for `lore`/`demand_intelligence` (derivation + valid-or-nothing + alphanumeric = 6); valid-or-nothing for `lore #2` and the newline name (HEAD writes an on-pattern slug; the alphanumeric pins catch both: `lore #2→lore`, newline name → `demo`); `test_main_reports_a_missing_project_dir_before_resolving_its_slug`; `test_setup_leaves_an_operator_chosen_slug_byte_identical`.

### Round-2 node ids (new or reparametrized; from `--collect-only`)
```
test_scaffold_slug.py::TestScaffoldDerivesTheSlugFromTheDirectoryName::test_scaffolded_slug_is_the_slugified_directory_name[.config-config]
test_scaffold_slug.py::TestScaffoldDerivesTheSlugFromTheDirectoryName::test_scaffolded_slug_is_the_slugified_directory_name[_private-private]
test_scaffold_slug.py::TestScaffoldDerivesTheSlugFromTheDirectoryName::test_scaffolded_slug_is_the_slugified_directory_name[caf\xe9-cafe]
test_scaffold_slug.py::TestScaffoldDerivesTheSlugFromTheDirectoryName::test_scaffolded_slug_is_the_slugified_directory_name[demo\n  root: elsewhere-demo_root_elsewhere]
test_scaffold_slug.py::TestScaffoldDerivesTheSlugFromTheDirectoryName::test_scaffolded_slug_is_the_slugified_directory_name[lore #2-lore_2]
test_scaffold_slug.py::TestScaffoldDerivesTheSlugFromTheDirectoryName::test_scaffolded_slug_is_the_slugified_directory_name[odoo--custom-odoo_custom]
test_scaffold_slug.py::TestScaffoldDerivesTheSlugFromTheDirectoryName::test_scaffolded_slug_is_the_slugified_directory_name[proj: ect-proj_ect]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffold_outcome_is_valid_or_nothing[.config]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffold_outcome_is_valid_or_nothing[_private]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffold_outcome_is_valid_or_nothing[demo\n  root: elsewhere]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffold_outcome_is_valid_or_nothing[lore #2]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffold_outcome_is_valid_or_nothing[odoo--custom]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffold_outcome_is_valid_or_nothing[proj: ect]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffold_outcome_is_valid_or_nothing[project-]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order[.config]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order[_private]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order[demo\n  root: elsewhere]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order[lore #2]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order[odoo--custom]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order[proj: ect]
test_scaffold_slug.py::TestEveryNameScaffoldsAValidLoreYamlOrNone::test_scaffolded_slug_keeps_every_ascii_alphanumeric_in_order[project-]
test_scaffold_slug.py::TestANameWithNoValidSlugIsRefusedLoudly::test_main_returns_exit_error_for_an_unslugifiable_dir_not_a_traceback
test_scaffold_slug.py::TestANameWithNoValidSlugIsRefusedLoudly::test_main_reports_a_missing_project_dir_before_resolving_its_slug
test_scaffold_slug.py::TestEveryVerbUsesTheConfiguredSlug::test_env_file_resolves_under_the_configured_slug[odoo_custom]
test_scaffold_slug.py::TestEveryVerbUsesTheConfiguredSlug::test_env_file_resolves_under_the_configured_slug[odoo]
test_scaffold_slug.py::TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_container_serves_another_project
test_scaffold_slug.py::TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_manifest_exists_for_a_project_without_config
test_scaffold_slug.py::TestSetupRefusesASlugHeldByAnotherProject::test_same_project_rerun_with_its_running_container_is_not_refused
test_scaffold_slug.py::TestSetupRefusesASlugHeldByAnotherProject::test_same_project_resuming_after_its_scaffold_is_not_refused
```

### Reference diff, round 2 (SATISFIABILITY ONLY; follows F1/F2/F3/F5 and F4 as pinned. NOT a proposed build)
```diff
diff --git a/loremaster/loremaster/config.py b/loremaster/loremaster/config.py
index a95ae29..661ba53 100644
--- a/loremaster/loremaster/config.py
+++ b/loremaster/loremaster/config.py
@@ -104,6 +104,24 @@ SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"
 SlugStr = Annotated[str, StringConstraints(pattern=SLUG_PATTERN)]
 
 
+def derive_project_slug(directory_name: str) -> str:
+    """Derive a project slug from a directory name (python-slugify, ``separator="_"``).
+
+    Raises ``ValueError`` naming the directory when no valid slug can be built (REFERENCE BUILD).
+    """
+    import re as _re
+
+    from slugify import slugify
+
+    slug = slugify(directory_name, separator="_")
+    if not _re.fullmatch(SLUG_PATTERN, slug):
+        raise ValueError(
+            f"project directory {directory_name!r} has no valid lore slug (derived {slug!r}); "
+            f"set project.slug by hand in its lore.yaml, or rename the directory"
+        )
+    return slug
+
+
 def _reject_url_userinfo(value: str) -> str:
     """Reject a URL carrying inline credentials (a ``user:pass@host`` userinfo component).
 
diff --git a/loremaster/pyproject.toml b/loremaster/pyproject.toml
index b6f3592..97c9197 100644
--- a/loremaster/pyproject.toml
+++ b/loremaster/pyproject.toml
@@ -50,6 +50,7 @@ dependencies = [
     # ``[[tool.mypy.overrides]]`` block for networkx in the ROOT pyproject is re-scoped to
     # production accordingly.
     "networkx>=3.6.1",
+    "python-slugify>=9.1.3",
 ]
 
 [project.scripts]
--- ../slug568b-lore_deploy.orig.py	2026-10-31 17:32:34.724169492 -0400
+++ skills/lore-deploy/scripts/lore_deploy.py	2026-10-31 19:25:10.221257281 -0400
@@ -183,6 +183,42 @@
     )
 
 
+class _SlugRefusal(RuntimeError):
+    """A project whose slug cannot be resolved, or is held by another project (REFERENCE)."""
+
+
+def _derive_slug(project: Path) -> str:
+    """Derive the slug from the directory name through loremaster's ONE normaliser."""
+    code = ("import sys;from loremaster.config import derive_project_slug as d;"
+            "print(d(sys.argv[1]))")
+    result = _run([_loremaster_python(), "-c", code, project.name], check=False, capture=True)
+    if result.returncode != 0:
+        detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
+        raise _SlugRefusal(f"{detail} (project {project})")
+    return result.stdout.strip()
+
+
+def _project_slug(project: Path) -> str:
+    """The project's slug: its lore.yaml's project.slug when present (F3), else derived."""
+    config_path = project / "lore.yaml"
+    if config_path.exists():
+        return _read_config_field(config_path, "c.project.slug")
+    return _derive_slug(project)
+
+
+def _container_workspace_source(container_name: str) -> str | None:
+    """The host path mounted at /workspace in ``container_name``, or None when absent."""
+    result = _run(
+        ["podman", "container", "inspect", "--format",
+         '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}',
+         container_name],
+        check=False, capture=True,
+    )
+    if result.returncode != 0:
+        return None
+    return result.stdout.strip() or None
+
+
 def _container_state(name: str) -> str | None:
     """Return a container's state string (e.g. ``running``/``exited``) or ``None`` if absent."""
     result = _run(
@@ -421,7 +457,7 @@
     if explicit is not None:
         # Honor an operator-supplied path verbatim — no per-slug rewriting.
         return Path(explicit)
-    slug = project.name
+    slug = _project_slug(project)
     return LORE_SECRETS_DIR / f"{slug}.env"
 
 
@@ -583,7 +619,7 @@
     should review them for the project's real layout. Validated by parsing the
     written file through the real LoreConfig before returning.
     """
-    slug = project.name
+    slug = _derive_slug(project)
     port = _free_port(DEFAULT_PORT_BASE)
     always_prune = [".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]
     excludes = always_prune + [n for n in _gitignore_dir_names(project) if n not in always_prune]
@@ -594,7 +630,7 @@
 schema_version: 1
 
 project:
-  slug: {slug}
+  slug: "{slug}"
   root: .
 
 embedding:
@@ -663,6 +699,12 @@
   port: {port}
 """
     config_path.write_text(content, encoding="utf-8")
+    try:
+        _validate_config_schema(config_path)
+    except RuntimeError:
+        config_path.unlink(missing_ok=True)
+        raise
+    return
     # Fail loud if the scaffold does not parse against the real model. Schema-only
     # (LoreConfig.model_validate, NOT load_config): the scaffold emits env-var
     # *names*, never secrets, so validation must not require ANTHROPIC_API_KEY to
@@ -807,7 +849,7 @@
         subprocess.CalledProcessError: ``podman run`` fails.
     """
     binds_snapshot = _require_launchable_snapshot(config_path)
-    slug = project.name
+    slug = _read_config_field(config_path, "c.project.slug")
     cmd = [
         "podman", "run", "-d", "--name", f"lore-{slug}",
         "--network=host",
@@ -862,7 +904,10 @@
     Returns:
         ``_EXIT_OK`` when the launch succeeded, ``_EXIT_ERROR`` otherwise.
     """
-    container_name = f"lore-{project.name}"
+    try:
+        container_name = f"lore-{_project_slug(project)}"
+    except _LAUNCH_FAILURES:
+        container_name = "lore container"
     try:
         _launch_container(project, config_path, env_file)
     except _LAUNCH_FAILURES as error:
@@ -880,7 +925,23 @@
 def verb_setup(project: Path, env_file: Path) -> int:  # noqa: PLR0911 - P8e reworks this skill
     """``setup`` — idempotent one-time provisioning (expensive parts no-op on re-run)."""
     config_path = project / "lore.yaml"
-    slug = project.name
+    try:
+        slug = _project_slug(project)
+    except _SlugRefusal as error:
+        print(f"setup: {error}", file=sys.stderr)
+        return _EXIT_ERROR
+    if not config_path.exists():
+        holder = _container_workspace_source(f"lore-{slug}")
+        if holder is not None and Path(holder).resolve() != project.resolve():
+            print(f"setup: slug {slug!r} for {project} is already held by {holder} "
+                  f"(container lore-{slug}); set project.slug by hand in lore.yaml.",
+                  file=sys.stderr)
+            return _EXIT_ERROR
+        if (MANIFEST_DIR / f"{slug}.db").exists():
+            print(f"setup: slug {slug!r} for {project} already has a manifest "
+                  f"{MANIFEST_DIR / f'{slug}.db'} from another project; set project.slug by "
+                  f"hand in lore.yaml.", file=sys.stderr)
+            return _EXIT_ERROR
 
     # 1. Detect an existing deployment → no-op the expensive parts.
     already = config_path.exists() and (MANIFEST_DIR / f"{slug}.db").exists()
@@ -974,11 +1035,15 @@
     not check".
     """
     config_path = project / "lore.yaml"
-    slug = project.name
-    container_name = f"lore-{slug}"
     if not config_path.exists():
         print(f"start: no {config_path}; run `setup` first.", file=sys.stderr)
         return _EXIT_ERROR
+    try:
+        slug = _project_slug(project)
+    except RuntimeError as error:
+        print(f"start: {error}", file=sys.stderr)
+        return _EXIT_ERROR
+    container_name = f"lore-{slug}"
 
     state = _container_state(container_name)
     if state == "running":
@@ -1137,7 +1202,7 @@
 
 def verb_stop(project: Path) -> int:
     """``stop`` — stop + remove the container (store data + manifest persist; idempotent)."""
-    slug = project.name
+    slug = _project_slug(project)
     state = _container_state(f"lore-{slug}")
     if state is None:
         print(f"stop: lore-{slug} not running — no-op.")
@@ -1158,7 +1223,7 @@
     hold the port unbound for minutes after the container starts). A stopped
     container skips the probe (nothing to probe).
     """
-    slug = project.name
+    slug = _project_slug(project)
     container_name = f"lore-{slug}"
     config_path = project / "lore.yaml"
     state = _container_state(container_name)
@@ -1769,13 +1834,14 @@
         )
         return _EXIT_ERROR
     project = Path(args.project).resolve()
-    # Resolve the env-file AFTER the project is known so an unsupplied --env-file
-    # (default None) resolves per-slug; an explicit value passes through verbatim.
-    env_file = _resolve_env_file(project, args.env_file)
-
     if not project.is_dir():
         print(f"lore_deploy: --project {project} is not a directory.", file=sys.stderr)
         return _EXIT_ERROR
+    try:
+        env_file = _resolve_env_file(project, args.env_file)
+    except _SlugRefusal as error:
+        print(f"lore_deploy: {error}", file=sys.stderr)
+        return _EXIT_ERROR
 
     if args.verb == "setup":
         return verb_setup(project, env_file)
```

Fan-out (round 2): haiku 9 (RED, HEAD whole suite, satisfiability ×3, currency ×2, `-k main_` HEAD+scratch) · sonnet 0 · peak 2. The round-2 ruff check ran inline (one short command; I read all of it).


## Round 3 (2026-10-31, `RULING-568-slug.md` §Addendum: F4b → (b) + class lift; fixture alignment ACCEPTED)

**STATE: DONE.** At HEAD `eba0a46`, the only failures are this file's pins. Satisfiable against a ruling-aligned reference. One new fork (**F4c**), surfaced below.

### What changed in `skills/lore-deploy/scripts/test_scaffold_slug.py` (85 collected; was 80). `test_lore_deploy.py` is unchanged this round.
- **Production-shaped manifests.** `_write_manifest(slug, *, owner)` now builds the measured schema (`files` + `meta`, the `CREATE TABLE` text recorded from `~/.local/state/lore/{lore,demand_intelligence}.db` on 2026-10-31) with the two legacy `meta` keys. `owner` is REQUIRED: `None` means a legacy manifest with no `project_path` row. No default, because the code branches on it.
- **A fake indexer.** The `_run` shim's cold-index answer now creates `<slug>.db` exactly as the real indexer does: schema via `CREATE TABLE IF NOT EXISTS`, slug from the `--config` YAML, NO `project_path` row. So the row-written pin observes `setup`'s own write, and a row written before indexing survives.
- **(1) The row is written:** `TestSetupRecordsAndHonoursItsOwnProjectPath::test_fresh_setup_records_this_project_path_in_the_manifest`. After a fresh `setup` of `odoo-custom`, `odoo_custom.db` `meta['project_path']` resolves to the project. The resume pin asserts the same.
- **(2) The refusal names the holder AND this path:** `TestSetupRefusesASlugHeldByAnotherProject` × {container mounts another path, manifest `project_path` records another path}. Both require `_EXIT_ERROR`, a stderr naming the slug, THIS path and the holder's path, nothing created, and the manifest bytes untouched.
- **(3) A legacy manifest is an unknown owner:** `test_refuses_a_legacy_manifest_as_an_unknown_owner`. No row and no container → `_EXIT_ERROR`; stderr names the slug and this path and contains `"unknown owner"` (the ruling's pinned text, constant `UNKNOWN_OWNER_TEXT`).
- **(4) The hand-set door:** the whole F4 class is parametrized over `SlugDoor` ∈ {`derived` (no lore.yaml → `odoo_custom`), `hand_set` (lore.yaml declares `odoo`)}, so ONE rule is pinned for both doors. On the `hand_set` door, "nothing created" means the existing lore.yaml is byte-identical. A build that checks collisions only for derived slugs fails every `[hand_set]` row.
- **Round-2 pins updated to the new world:** the provisioned-project pins (status, setup-provisioned, same-project re-run) write their manifest with `owner=project`. Under F4b a manifest with no row is now a refusal, not a provisioned project.

### F4c — the ruling as written refuses the two LIVE deployments' next `setup` (escalated; not silently chosen)
Measured 2026-10-31:
- `lore.db` and `demand_intelligence.db` are both **legacy** (their `meta` keys are `embedding_schema_fingerprint` and `schema_rebuild_status` only).
- Both containers exist and mount their own paths: `lore-lore` is running and mounts `/home/ejprice/PycharmProjects/lore`; `lore-demand_intelligence` has exited and mounts `/home/ejprice/PycharmProjects/pp-odoo/demand_intelligence`.

"A legacy manifest is never accepted" therefore refuses `lore-deploy setup` on both, including its cheap already-provisioned `.mcp.json` re-merge, until something writes the row. `start`/`stop`/`status` are unaffected.

Options:
- (a) Literal: refuse; the operator migrates by hand (or with a one-shot) by writing the row.
- (b) **Adopt by container:** a legacy manifest whose `lore-<slug>` container (any state) mounts THIS path is this project's. Record the row and proceed.
- (c) A one-shot migration in the builder's wave that writes the row for every manifest whose container identifies its owner.

**My pick: (b).** It is decidable, it covers both live deployments, and it is what the ruling's own "from the container when that shows it" already implies.

**Pinned under every option:** a legacy manifest with NO container is refused (both doors). **NOT pinned:** legacy + a container mounting THIS path. The reference takes (b) there, but that choice is unpinned and needs your ruling. If you rule (b), it is one more cheap pin: legacy manifest + own exited container → OK, row written.

### Builder guidance, from the reference (not a pin)
`meta` belongs to loremaster's manifest code. The reference writes the row with raw `sqlite3` from `lore_deploy.py`, which makes it a second writer of a server-owned table. ONE IMPLEMENTATION says the row write and read belong with loremaster's manifest owner, reached via `_loremaster_python()` the way the normaliser is. Also check that a server-side manifest rebuild (`schema_rebuild_status`: `fingerprint_mismatch` / `store_divergence_heal`) cannot drop the row. If it can, every rebuilt project becomes an "unknown owner" (the F4c state again).

### Receipts (round 3)
| run | scope | result |
|---|---|---|
| HEAD, whole skill suite (`. ../tests`) | at `eba0a46` | **75 failed / 272 passed / 347**. **0 failures outside `test_scaffold_slug.py`**; all 9 F4/F4b/class-lift pins RED; 0 collection/import errors |
| satisfiability r3 (scratch, `LORE_PYTHON` exported) | whole skill suite | **347 passed / 0 failed** |
| currency `--legs typecheck,ruff` | repo | typecheck RED_ADJUDICATED (packet-58 / 64b-i owned), ruff GREEN, **RED_ORPHANED 0** (CURRENCY FAIL only for `pytest NOT_RUN`, by `--legs` design). Verdict lines read from the log myself; the runner skipped its runner block, so its `RAN:` line came from its own echo |
| ruff + mypy on the file | inline | All checks passed · Success: no issues |

Count reconciliation: 70 (round 2) − 4 (round-2 F4 pins, replaced) + 9 (round-3 F4 pins) = **75** ✓. The 10 HEAD-green guards are unchanged.

A runner handed back before its HEAD run finished, which made it a non-result. I waited for the process and read `head568r3.log` myself (scope id `d266fa81…`, distinct from the satisfiability log's `90854aa1…`, so the two runs were not crossed).

### Round-3 node ids
```
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_container_serves_another_project[derived]
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_container_serves_another_project[hand_set]
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_manifest_records_another_project[derived]
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_manifest_records_another_project[hand_set]
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_a_legacy_manifest_as_an_unknown_owner[derived]
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_a_legacy_manifest_as_an_unknown_owner[hand_set]
TestSetupRecordsAndHonoursItsOwnProjectPath::test_fresh_setup_records_this_project_path_in_the_manifest
TestSetupRecordsAndHonoursItsOwnProjectPath::test_same_project_rerun_with_its_running_container_is_not_refused
TestSetupRecordsAndHonoursItsOwnProjectPath::test_same_project_resuming_after_its_scaffold_is_not_refused
```

### Reference diff, round 3 (SATISFIABILITY ONLY; takes F4c=(b) where unpinned. NOT a proposed build)
```diff
diff --git a/loremaster/loremaster/config.py b/loremaster/loremaster/config.py
index a95ae29..661ba53 100644
--- a/loremaster/loremaster/config.py
+++ b/loremaster/loremaster/config.py
@@ -104,6 +104,24 @@ SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"
 SlugStr = Annotated[str, StringConstraints(pattern=SLUG_PATTERN)]
 
 
+def derive_project_slug(directory_name: str) -> str:
+    """Derive a project slug from a directory name (python-slugify, ``separator="_"``).
+
+    Raises ``ValueError`` naming the directory when no valid slug can be built (REFERENCE BUILD).
+    """
+    import re as _re
+
+    from slugify import slugify
+
+    slug = slugify(directory_name, separator="_")
+    if not _re.fullmatch(SLUG_PATTERN, slug):
+        raise ValueError(
+            f"project directory {directory_name!r} has no valid lore slug (derived {slug!r}); "
+            f"set project.slug by hand in its lore.yaml, or rename the directory"
+        )
+    return slug
+
+
 def _reject_url_userinfo(value: str) -> str:
     """Reject a URL carrying inline credentials (a ``user:pass@host`` userinfo component).
 
diff --git a/loremaster/pyproject.toml b/loremaster/pyproject.toml
index b6f3592..97c9197 100644
--- a/loremaster/pyproject.toml
+++ b/loremaster/pyproject.toml
@@ -50,6 +50,7 @@ dependencies = [
     # ``[[tool.mypy.overrides]]`` block for networkx in the ROOT pyproject is re-scoped to
     # production accordingly.
     "networkx>=3.6.1",
+    "python-slugify>=9.1.3",
 ]
 
 [project.scripts]
--- ../slug568b-lore_deploy.orig.py	2026-10-31 17:32:34.724169492 -0400
+++ skills/lore-deploy/scripts/lore_deploy.py	2026-10-31 19:32:28.881697707 -0400
@@ -183,6 +183,93 @@
     )
 
 
+class _SlugRefusal(RuntimeError):
+    """A project whose slug cannot be resolved, or is held by another project (REFERENCE)."""
+
+
+def _derive_slug(project: Path) -> str:
+    """Derive the slug from the directory name through loremaster's ONE normaliser."""
+    code = ("import sys;from loremaster.config import derive_project_slug as d;"
+            "print(d(sys.argv[1]))")
+    result = _run([_loremaster_python(), "-c", code, project.name], check=False, capture=True)
+    if result.returncode != 0:
+        detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
+        raise _SlugRefusal(f"{detail} (project {project})")
+    return result.stdout.strip()
+
+
+def _project_slug(project: Path) -> str:
+    """The project's slug: its lore.yaml's project.slug when present (F3), else derived."""
+    config_path = project / "lore.yaml"
+    if config_path.exists():
+        return _read_config_field(config_path, "c.project.slug")
+    return _derive_slug(project)
+
+
+def _container_workspace_source(container_name: str) -> str | None:
+    """The host path mounted at /workspace in ``container_name``, or None when absent."""
+    result = _run(
+        ["podman", "container", "inspect", "--format",
+         '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}',
+         container_name],
+        check=False, capture=True,
+    )
+    if result.returncode != 0:
+        return None
+    return result.stdout.strip() or None
+
+
+_PROJECT_PATH_META_KEY = "project_path"
+
+
+def _manifest_project_path(manifest: Path) -> str | None:
+    """The manifest's recorded owning project path, or None for a legacy manifest."""
+    import sqlite3
+
+    with sqlite3.connect(f"file:{manifest}?mode=ro", uri=True) as connection:
+        try:
+            row = connection.execute(
+                "SELECT v FROM meta WHERE k = ?", (_PROJECT_PATH_META_KEY,)
+            ).fetchone()
+        except sqlite3.OperationalError:
+            return None
+    return None if row is None else str(row[0])
+
+
+def _slug_collision(project: Path, slug: str) -> str | None:
+    """Why ``slug`` may not be used by ``project`` (held by another path), or None (REFERENCE)."""
+    here = project.resolve()
+    remedy = "set a different project.slug by hand in lore.yaml."
+    mounted = _container_workspace_source(f"lore-{slug}")
+    if mounted is not None:
+        if Path(mounted).resolve() != here:
+            return f"slug {slug!r} for {project} is held by {mounted} (container lore-{slug}); {remedy}"
+        return None
+    manifest = MANIFEST_DIR / f"{slug}.db"
+    if not manifest.exists():
+        return None
+    owner = _manifest_project_path(manifest)
+    if owner is None:
+        return (f"slug {slug!r} for {project} is held by an unknown owner (manifest {manifest} "
+                f"records no {_PROJECT_PATH_META_KEY}); {remedy}")
+    if Path(owner).resolve() != here:
+        return f"slug {slug!r} for {project} is held by {owner} (manifest {manifest}); {remedy}"
+    return None
+
+
+def _record_project_path(slug: str, project: Path) -> None:
+    """Record ``project`` as the owner of ``<slug>.db`` (meta row ``project_path``)."""
+    import sqlite3
+
+    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
+    with sqlite3.connect(MANIFEST_DIR / f"{slug}.db") as connection:
+        connection.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)")
+        connection.execute(
+            "INSERT OR REPLACE INTO meta VALUES (?, ?)",
+            (_PROJECT_PATH_META_KEY, str(project.resolve())),
+        )
+
+
 def _container_state(name: str) -> str | None:
     """Return a container's state string (e.g. ``running``/``exited``) or ``None`` if absent."""
     result = _run(
@@ -421,7 +508,7 @@
     if explicit is not None:
         # Honor an operator-supplied path verbatim — no per-slug rewriting.
         return Path(explicit)
-    slug = project.name
+    slug = _project_slug(project)
     return LORE_SECRETS_DIR / f"{slug}.env"
 
 
@@ -583,7 +670,7 @@
     should review them for the project's real layout. Validated by parsing the
     written file through the real LoreConfig before returning.
     """
-    slug = project.name
+    slug = _derive_slug(project)
     port = _free_port(DEFAULT_PORT_BASE)
     always_prune = [".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]
     excludes = always_prune + [n for n in _gitignore_dir_names(project) if n not in always_prune]
@@ -594,7 +681,7 @@
 schema_version: 1
 
 project:
-  slug: {slug}
+  slug: "{slug}"
   root: .
 
 embedding:
@@ -663,6 +750,12 @@
   port: {port}
 """
     config_path.write_text(content, encoding="utf-8")
+    try:
+        _validate_config_schema(config_path)
+    except RuntimeError:
+        config_path.unlink(missing_ok=True)
+        raise
+    return
     # Fail loud if the scaffold does not parse against the real model. Schema-only
     # (LoreConfig.model_validate, NOT load_config): the scaffold emits env-var
     # *names*, never secrets, so validation must not require ANTHROPIC_API_KEY to
@@ -807,7 +900,7 @@
         subprocess.CalledProcessError: ``podman run`` fails.
     """
     binds_snapshot = _require_launchable_snapshot(config_path)
-    slug = project.name
+    slug = _read_config_field(config_path, "c.project.slug")
     cmd = [
         "podman", "run", "-d", "--name", f"lore-{slug}",
         "--network=host",
@@ -862,7 +955,10 @@
     Returns:
         ``_EXIT_OK`` when the launch succeeded, ``_EXIT_ERROR`` otherwise.
     """
-    container_name = f"lore-{project.name}"
+    try:
+        container_name = f"lore-{_project_slug(project)}"
+    except _LAUNCH_FAILURES:
+        container_name = "lore container"
     try:
         _launch_container(project, config_path, env_file)
     except _LAUNCH_FAILURES as error:
@@ -880,7 +976,14 @@
 def verb_setup(project: Path, env_file: Path) -> int:  # noqa: PLR0911 - P8e reworks this skill
     """``setup`` — idempotent one-time provisioning (expensive parts no-op on re-run)."""
     config_path = project / "lore.yaml"
-    slug = project.name
+    try:
+        slug = _project_slug(project)
+    except _SlugRefusal as error:
+        print(f"setup: {error}", file=sys.stderr)
+        return _EXIT_ERROR
+    if (refusal := _slug_collision(project, slug)) is not None:
+        print(f"setup: {refusal}", file=sys.stderr)
+        return _EXIT_ERROR
 
     # 1. Detect an existing deployment → no-op the expensive parts.
     already = config_path.exists() and (MANIFEST_DIR / f"{slug}.db").exists()
@@ -929,6 +1032,7 @@
     if cold.returncode != 0:
         print(f"setup: cold index reported failures:\n{cold.stderr.strip()}", file=sys.stderr)
         return _EXIT_ERROR
+    _record_project_path(slug, project)
 
     # 8. Merge .mcp.json.
     _merge_mcp_from_config(project, slug, config_path)
@@ -974,11 +1078,15 @@
     not check".
     """
     config_path = project / "lore.yaml"
-    slug = project.name
-    container_name = f"lore-{slug}"
     if not config_path.exists():
         print(f"start: no {config_path}; run `setup` first.", file=sys.stderr)
         return _EXIT_ERROR
+    try:
+        slug = _project_slug(project)
+    except RuntimeError as error:
+        print(f"start: {error}", file=sys.stderr)
+        return _EXIT_ERROR
+    container_name = f"lore-{slug}"
 
     state = _container_state(container_name)
     if state == "running":
@@ -1137,7 +1245,7 @@
 
 def verb_stop(project: Path) -> int:
     """``stop`` — stop + remove the container (store data + manifest persist; idempotent)."""
-    slug = project.name
+    slug = _project_slug(project)
     state = _container_state(f"lore-{slug}")
     if state is None:
         print(f"stop: lore-{slug} not running — no-op.")
@@ -1158,7 +1266,7 @@
     hold the port unbound for minutes after the container starts). A stopped
     container skips the probe (nothing to probe).
     """
-    slug = project.name
+    slug = _project_slug(project)
     container_name = f"lore-{slug}"
     config_path = project / "lore.yaml"
     state = _container_state(container_name)
@@ -1769,13 +1877,14 @@
         )
         return _EXIT_ERROR
     project = Path(args.project).resolve()
-    # Resolve the env-file AFTER the project is known so an unsupplied --env-file
-    # (default None) resolves per-slug; an explicit value passes through verbatim.
-    env_file = _resolve_env_file(project, args.env_file)
-
     if not project.is_dir():
         print(f"lore_deploy: --project {project} is not a directory.", file=sys.stderr)
         return _EXIT_ERROR
+    try:
+        env_file = _resolve_env_file(project, args.env_file)
+    except _SlugRefusal as error:
+        print(f"lore_deploy: {error}", file=sys.stderr)
+        return _EXIT_ERROR
 
     if args.verb == "setup":
         return verb_setup(project, env_file)
```

Fan-out (round 3): haiku 3 (HEAD whole suite, satisfiability, currency) · sonnet 0 · peak 3.


### Round 3 — CORRECTION applied (directive #18015; supersedes item (3) and F4c above)
- **F4c is resolved by the ruling:** a legacy manifest is refused ONLY on a fresh setup (no lore.yaml). When the project's lore.yaml declares the slug, the manifest is its own: setup BACKFILLS `project_path` and proceeds. Re-running setup on an existing deployment is never refused. My F4c paragraph above and its option (b) are SUPERSEDED. The live `lore` / `demand_intelligence` deployments are covered by the backfill leg, with no container needed.
- **Pins, both legs:**
  - `TestSetupRecordsAndHonoursItsOwnProjectPath::test_fresh_setup_refuses_a_legacy_manifest_as_an_unknown_owner`: no lore.yaml, legacy `odoo_custom.db`, no container → `_EXIT_ERROR`, `"unknown owner"`, slug and this path named, nothing created, manifest bytes untouched.
  - `TestSetupRecordsAndHonoursItsOwnProjectPath::test_existing_deployment_backfills_its_legacy_manifest_and_proceeds[odoo_custom|odoo]`: lore.yaml declares the slug (derived OR hand-set), legacy manifest, no container, ABSENT env-file → OK, `project_path` backfilled to this project, no re-index, no container touched, `.mcp.json` `lore_<slug>`.
- The door-parametrized `test_refuses_a_legacy_manifest_as_an_unknown_owner[derived|hand_set]` is REMOVED. Its `[hand_set]` leg contradicted the correction.
- **A consequence the correction accepts, stated so it is a known bound and not a surprise:** a project that hand-sets a slug onto ANOTHER project's legacy manifest, while that holder's container is absent, is indistinguishable from the slug's real owner re-running setup. It will be backfilled and adopted. The container door and a recorded `project_path` still refuse it. The window closes once every live manifest has been backfilled (the first `setup` re-run on each). Not pinned as a miss: the ruling chose this trade; flagging it for the record.
- The reference was updated (backfill branch). Builder guidance stands: the row write and read belong with loremaster's manifest owner, not a raw `sqlite3` second writer in `lore_deploy.py`.

**Final round-3 receipts** (file at 86 collected; `test_lore_deploy.py` unchanged this round):

| run | scope | result |
|---|---|---|
| HEAD `eba0a46`, whole skill suite | `. ../tests` | **76 failed / 272 passed / 348**; **0 failures outside `test_scaffold_slug.py`**; 0 collection/import errors |
| satisfiability (scratch) | whole skill suite | **348 passed / 0 failed** |
| ruff · mypy (file) | inline | All checks passed · Success: no issues |
| currency `--legs typecheck,ruff` | repo, final file | typecheck RED_ADJUDICATED (packet-58 / 64b-i owned), ruff GREEN, **RED_ORPHANED 0**; CURRENCY FAIL only for `pytest NOT_RUN` (by `--legs` design). Verdict lines read from the log myself |

Count: 75 − 2 (door-parametrized legacy) + 1 (fresh-setup legacy) + 2 (backfill) = **76** ✓.

**Final round-3 node ids (F4 classes):**
```
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_container_serves_another_project[derived]
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_container_serves_another_project[hand_set]
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_manifest_records_another_project[derived]
TestSetupRefusesASlugHeldByAnotherProject::test_refuses_when_the_slugs_manifest_records_another_project[hand_set]
TestSetupRecordsAndHonoursItsOwnProjectPath::test_fresh_setup_records_this_project_path_in_the_manifest
TestSetupRecordsAndHonoursItsOwnProjectPath::test_fresh_setup_refuses_a_legacy_manifest_as_an_unknown_owner
TestSetupRecordsAndHonoursItsOwnProjectPath::test_existing_deployment_backfills_its_legacy_manifest_and_proceeds[odoo_custom]
TestSetupRecordsAndHonoursItsOwnProjectPath::test_existing_deployment_backfills_its_legacy_manifest_and_proceeds[odoo]
TestSetupRecordsAndHonoursItsOwnProjectPath::test_same_project_rerun_with_its_running_container_is_not_refused
TestSetupRecordsAndHonoursItsOwnProjectPath::test_same_project_resuming_after_its_scaffold_is_not_refused
```

**Reference diff, final (SATISFIABILITY ONLY. NOT a proposed build):**
```diff
diff --git a/loremaster/loremaster/config.py b/loremaster/loremaster/config.py
index a95ae29..661ba53 100644
--- a/loremaster/loremaster/config.py
+++ b/loremaster/loremaster/config.py
@@ -104,6 +104,24 @@ SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"
 SlugStr = Annotated[str, StringConstraints(pattern=SLUG_PATTERN)]
 
 
+def derive_project_slug(directory_name: str) -> str:
+    """Derive a project slug from a directory name (python-slugify, ``separator="_"``).
+
+    Raises ``ValueError`` naming the directory when no valid slug can be built (REFERENCE BUILD).
+    """
+    import re as _re
+
+    from slugify import slugify
+
+    slug = slugify(directory_name, separator="_")
+    if not _re.fullmatch(SLUG_PATTERN, slug):
+        raise ValueError(
+            f"project directory {directory_name!r} has no valid lore slug (derived {slug!r}); "
+            f"set project.slug by hand in its lore.yaml, or rename the directory"
+        )
+    return slug
+
+
 def _reject_url_userinfo(value: str) -> str:
     """Reject a URL carrying inline credentials (a ``user:pass@host`` userinfo component).
 
diff --git a/loremaster/pyproject.toml b/loremaster/pyproject.toml
index b6f3592..97c9197 100644
--- a/loremaster/pyproject.toml
+++ b/loremaster/pyproject.toml
@@ -50,6 +50,7 @@ dependencies = [
     # ``[[tool.mypy.overrides]]`` block for networkx in the ROOT pyproject is re-scoped to
     # production accordingly.
     "networkx>=3.6.1",
+    "python-slugify>=9.1.3",
 ]
 
 [project.scripts]
--- ../slug568b-lore_deploy.orig.py	2026-10-31 17:32:34.724169492 -0400
+++ skills/lore-deploy/scripts/lore_deploy.py	2026-10-31 19:35:29.489412104 -0400
@@ -183,6 +183,95 @@
     )
 
 
+class _SlugRefusal(RuntimeError):
+    """A project whose slug cannot be resolved, or is held by another project (REFERENCE)."""
+
+
+def _derive_slug(project: Path) -> str:
+    """Derive the slug from the directory name through loremaster's ONE normaliser."""
+    code = ("import sys;from loremaster.config import derive_project_slug as d;"
+            "print(d(sys.argv[1]))")
+    result = _run([_loremaster_python(), "-c", code, project.name], check=False, capture=True)
+    if result.returncode != 0:
+        detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
+        raise _SlugRefusal(f"{detail} (project {project})")
+    return result.stdout.strip()
+
+
+def _project_slug(project: Path) -> str:
+    """The project's slug: its lore.yaml's project.slug when present (F3), else derived."""
+    config_path = project / "lore.yaml"
+    if config_path.exists():
+        return _read_config_field(config_path, "c.project.slug")
+    return _derive_slug(project)
+
+
+def _container_workspace_source(container_name: str) -> str | None:
+    """The host path mounted at /workspace in ``container_name``, or None when absent."""
+    result = _run(
+        ["podman", "container", "inspect", "--format",
+         '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}',
+         container_name],
+        check=False, capture=True,
+    )
+    if result.returncode != 0:
+        return None
+    return result.stdout.strip() or None
+
+
+_PROJECT_PATH_META_KEY = "project_path"
+
+
+def _manifest_project_path(manifest: Path) -> str | None:
+    """The manifest's recorded owning project path, or None for a legacy manifest."""
+    import sqlite3
+
+    with sqlite3.connect(f"file:{manifest}?mode=ro", uri=True) as connection:
+        try:
+            row = connection.execute(
+                "SELECT v FROM meta WHERE k = ?", (_PROJECT_PATH_META_KEY,)
+            ).fetchone()
+        except sqlite3.OperationalError:
+            return None
+    return None if row is None else str(row[0])
+
+
+def _slug_collision(project: Path, slug: str) -> str | None:
+    """Why ``slug`` may not be used by ``project`` (held by another path), or None (REFERENCE)."""
+    here = project.resolve()
+    remedy = "set a different project.slug by hand in lore.yaml."
+    mounted = _container_workspace_source(f"lore-{slug}")
+    if mounted is not None:
+        if Path(mounted).resolve() != here:
+            return f"slug {slug!r} for {project} is held by {mounted} (container lore-{slug}); {remedy}"
+        return None
+    manifest = MANIFEST_DIR / f"{slug}.db"
+    if not manifest.exists():
+        return None
+    owner = _manifest_project_path(manifest)
+    if owner is None and (project / "lore.yaml").exists():
+        return None  # an existing deployment's own legacy manifest: setup backfills the row
+    if owner is None:
+        return (f"slug {slug!r} for {project} is held by an unknown owner (manifest {manifest} "
+                f"records no {_PROJECT_PATH_META_KEY}); {remedy}")
+    if Path(owner).resolve() != here:
+        return f"slug {slug!r} for {project} is held by {owner} (manifest {manifest}); {remedy}"
+    return None
+
+
+def _record_project_path(slug: str, project: Path) -> None:
+    """Record ``project`` as the owner of ``<slug>.db`` (meta row ``project_path``)."""
+    import sqlite3
+
+    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
+    with sqlite3.connect(MANIFEST_DIR / f"{slug}.db") as connection:
+        connection.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)")
+        connection.execute(
+            "INSERT OR REPLACE INTO meta VALUES (?, ?)",
+            (_PROJECT_PATH_META_KEY, str(project.resolve())),
+        )
+
+
 def _container_state(name: str) -> str | None:
     """Return a container's state string (e.g. ``running``/``exited``) or ``None`` if absent."""
     result = _run(
@@ -421,7 +510,7 @@
     if explicit is not None:
         # Honor an operator-supplied path verbatim — no per-slug rewriting.
         return Path(explicit)
-    slug = project.name
+    slug = _project_slug(project)
     return LORE_SECRETS_DIR / f"{slug}.env"
 
 
@@ -583,7 +672,7 @@
     should review them for the project's real layout. Validated by parsing the
     written file through the real LoreConfig before returning.
     """
-    slug = project.name
+    slug = _derive_slug(project)
     port = _free_port(DEFAULT_PORT_BASE)
     always_prune = [".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]
     excludes = always_prune + [n for n in _gitignore_dir_names(project) if n not in always_prune]
@@ -594,7 +683,7 @@
 schema_version: 1
 
 project:
-  slug: {slug}
+  slug: "{slug}"
   root: .
 
 embedding:
@@ -663,6 +752,12 @@
   port: {port}
 """
     config_path.write_text(content, encoding="utf-8")
+    try:
+        _validate_config_schema(config_path)
+    except RuntimeError:
+        config_path.unlink(missing_ok=True)
+        raise
+    return
     # Fail loud if the scaffold does not parse against the real model. Schema-only
     # (LoreConfig.model_validate, NOT load_config): the scaffold emits env-var
     # *names*, never secrets, so validation must not require ANTHROPIC_API_KEY to
@@ -807,7 +902,7 @@
         subprocess.CalledProcessError: ``podman run`` fails.
     """
     binds_snapshot = _require_launchable_snapshot(config_path)
-    slug = project.name
+    slug = _read_config_field(config_path, "c.project.slug")
     cmd = [
         "podman", "run", "-d", "--name", f"lore-{slug}",
         "--network=host",
@@ -862,7 +957,10 @@
     Returns:
         ``_EXIT_OK`` when the launch succeeded, ``_EXIT_ERROR`` otherwise.
     """
-    container_name = f"lore-{project.name}"
+    try:
+        container_name = f"lore-{_project_slug(project)}"
+    except _LAUNCH_FAILURES:
+        container_name = "lore container"
     try:
         _launch_container(project, config_path, env_file)
     except _LAUNCH_FAILURES as error:
@@ -880,7 +978,18 @@
 def verb_setup(project: Path, env_file: Path) -> int:  # noqa: PLR0911 - P8e reworks this skill
     """``setup`` — idempotent one-time provisioning (expensive parts no-op on re-run)."""
     config_path = project / "lore.yaml"
-    slug = project.name
+    try:
+        slug = _project_slug(project)
+    except _SlugRefusal as error:
+        print(f"setup: {error}", file=sys.stderr)
+        return _EXIT_ERROR
+    if (refusal := _slug_collision(project, slug)) is not None:
+        print(f"setup: {refusal}", file=sys.stderr)
+        return _EXIT_ERROR
+    manifest_path = MANIFEST_DIR / f"{slug}.db"
+    if (config_path.exists() and manifest_path.exists()
+            and _manifest_project_path(manifest_path) is None):
+        _record_project_path(slug, project)
 
     # 1. Detect an existing deployment → no-op the expensive parts.
     already = config_path.exists() and (MANIFEST_DIR / f"{slug}.db").exists()
@@ -929,6 +1038,7 @@
     if cold.returncode != 0:
         print(f"setup: cold index reported failures:\n{cold.stderr.strip()}", file=sys.stderr)
         return _EXIT_ERROR
+    _record_project_path(slug, project)
 
     # 8. Merge .mcp.json.
     _merge_mcp_from_config(project, slug, config_path)
@@ -974,11 +1084,15 @@
     not check".
     """
     config_path = project / "lore.yaml"
-    slug = project.name
-    container_name = f"lore-{slug}"
     if not config_path.exists():
         print(f"start: no {config_path}; run `setup` first.", file=sys.stderr)
         return _EXIT_ERROR
+    try:
+        slug = _project_slug(project)
+    except RuntimeError as error:
+        print(f"start: {error}", file=sys.stderr)
+        return _EXIT_ERROR
+    container_name = f"lore-{slug}"
 
     state = _container_state(container_name)
     if state == "running":
@@ -1137,7 +1251,7 @@
 
 def verb_stop(project: Path) -> int:
     """``stop`` — stop + remove the container (store data + manifest persist; idempotent)."""
-    slug = project.name
+    slug = _project_slug(project)
     state = _container_state(f"lore-{slug}")
     if state is None:
         print(f"stop: lore-{slug} not running — no-op.")
@@ -1158,7 +1272,7 @@
     hold the port unbound for minutes after the container starts). A stopped
     container skips the probe (nothing to probe).
     """
-    slug = project.name
+    slug = _project_slug(project)
     container_name = f"lore-{slug}"
     config_path = project / "lore.yaml"
     state = _container_state(container_name)
@@ -1769,13 +1883,14 @@
         )
         return _EXIT_ERROR
     project = Path(args.project).resolve()
-    # Resolve the env-file AFTER the project is known so an unsupplied --env-file
-    # (default None) resolves per-slug; an explicit value passes through verbatim.
-    env_file = _resolve_env_file(project, args.env_file)
-
     if not project.is_dir():
         print(f"lore_deploy: --project {project} is not a directory.", file=sys.stderr)
         return _EXIT_ERROR
+    try:
+        env_file = _resolve_env_file(project, args.env_file)
+    except _SlugRefusal as error:
+        print(f"lore_deploy: {error}", file=sys.stderr)
+        return _EXIT_ERROR
 
     if args.verb == "setup":
         return verb_setup(project, env_file)
```

Fan-out (round 3 total): haiku 6 (HEAD ×2, satisfiability ×2, currency ×2) · sonnet 0 · peak 3.
