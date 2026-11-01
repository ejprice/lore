# REPORT-contract-165: tdd-light contract for lore #165 (snapshot bind target + launch refusal)

## SUMMARY (measured 2026-10-31 at `acbce73`)
- brief-base v23 read · brief project v7 read
- state: **done-with-deviations** · **r2 amendment DONE** (#18003): 26 tests; RED 17F/9P; satisfiability 198 passed with scratch provenance ×3; ruff GREEN; typecheck skills OK. See §Amendment r2.
- r2 decisions-needed: none. r2 flags: #558 (`_loremaster_python` scratch poison); an implementer constraint (existing stubs answer "0" to any `static` expr, so count first).
- deviation D1: all test runs were inline, not through `haiku-runner`. My instructions for this run forbid spawning subagents (§Capability check).
- deviation D2: pin 2 redirects `MANIFEST_DIR` to a tmp dir, so the probe never mounts the live manifest/graph state. Every other argv byte is the real `_launch_container` output.
- deviation D3: the satisfiability run used a mirrored scratch repo (symlinks plus a real copy of `skills/lore-deploy`), not a plain `cp -a`. A plain copy fails 11 `../tests` for location reasons; §Satisfiability has the control.
- Packages considered: none — no mechanism specified (podman argv construction; the brief's discovery agrees)
- Odoo-20 portability: n/a — no Odoo seam touched
- Reuse ledger: 0 new production symbols. Test helpers reuse `test_lore_deploy._RecreatePathFixture` (§DRY).
- Graded: acbce73 · HEAD-at-report: acbce73 · SAME
- Test file: `skills/lore-deploy/scripts/test_launch_snapshot_bind.py`, 18 tests (collect-only).
- RED at HEAD: **10 failed, 8 passed**, every failure an assertion, DID-NOT-RAISE or fail-on-raise (0 import/collection errors).
- Satisfiability: **138 passed, 0 failed** over the full skill idiom (`. ../tests`) against the reference build; `lore_deploy.__file__` = mirror path.
- Gates: ruff GREEN. typecheck `skills` leg OK; the typecheck gate is RED_ADJUDICATED (83 residuals owned by packet-58 / packet-64b-i, none in skills).
- decisions-needed: (1) SPEC-SILENT S1/S2 (§Inventory) for the operator. (2) Finding #555 filed: the currency `--legs` verdict reads FAIL.
- F1 escalated and RULED (`docs/plans/v2/receipts/2026-10-31-165/RULING-F1-pin4.md`); (c)(ii), R1 and R2 are all written into the contract.

## Capability check · routing
- **Demanded:** `haiku-runner` for steps 3–5. **Had:** a prompt-level "do not spawn subagents" rule. **Did:** ran each brief
  command inline, with RAN + count pasted. **Lead must change:** spawn this role from a definition without that clause if
  Haiku runners are wanted.
- grep is blocked by a repo hook on the live-indexed checkout. Code reads went through lore (`lore_get_symbol`/`lore_search`)
  and `Read`. No lore friction was found on the code-structure questions.

| step | tier | who | reason |
|---|---|---|---|
| 1 reads | 3 | me | brief-routed |
| 2 contract | 3 | me | never delegated |
| 3 RED run | 1 | me, inline | no-subagent rule (D1) |
| 4 reference build | 3 | me | brief-routed |
| 4b satisfiability + control | 1 | me, inline | D1 |
| 5 ruff/typecheck/currency | 1 | me, inline | D1 |

Fan-out: haiku 0 · sonnet 0 · peak 0.

## Contract, per pin (plain English · tests · the wrong build each catches)
1. **Derived target.** With 1 or 3 static roots (boundary plus the real repo), the command carries exactly one snapshot bind,
   from host `SNAPSHOT_ROOT`, at `CONTAINER_HOME + server._DEFAULT_SNAPSHOT_ROOT.relative_to(Path.home())`. The test imports
   that path and never retypes it. The bind is `:ro`, and nothing binds at `/source`.
   - Tests: `TestStaticRootsBindSnapshotAtServerDefaultRoot::{test_static_roots_bind_host_snapshot_once_at_server_default_root[1|3], test_no_bind_targets_the_retired_source_path}`
   - Catches: HEAD's `/source` target; a supplement build (both binds); a rw bind; a hardcoded target that drifts from the
     server. Binds are parsed by meaning across `-v`/`--volume`/`--mount`, so a respelled flag cannot dodge the pin.
2. **Artifact pin.** The real `_launch_container`, over the real repo `lore.yaml`, with the real config reader and an empty env
   file. The captured argv is turned into a one-shot probe. The transform checks its own RESULT: no detach, no name,
   `--network=none` only. The probe runs against `localhost/lore:latest` with a python `-c` command.
   - In-image checks: provenance (not `/workspace`); server root == derived target; in-image static tiers == lore.yaml's
     (non-empty, so the ∀ is not vacuous); guard over an unbound control path is False×N; real `Indexer._snapshot_materialized`
     over the server root is True×N. Missing podman, image or host snapshot calls `pytest.fail` naming which one.
     The subprocess timeout is 240 s.
   - Test: `TestLaunchCommandBootsTheGuardTrueInTheRealImage::test_launch_command_makes_guard_true_for_every_static_tier`
   - Catches: any bind the server does not read, including ones that look right. RED at HEAD shows False×3 for all 3 tiers.
3. **No static roots → no snapshot bind.** This holds whether or not a host snapshot exists, and the launch still issues one
   `podman run`.
   - Test: `TestLiveOnlyProjectHasNoSnapshotBind::…[True|False]`
   - Catches: an unconditional bind, and a refusal that ignores the static-root count (the `False` leg).
4. **Refusal (RULING F1, option c).**
   - (c)(i): `_launch_container` raises `RuntimeError`; the message names the host path, `-m loremaster.index` and `--config`.
     No podman call is issued.
   - (c)(ii): `verb_start` on the fresh AND recreate paths returns `_EXIT_ERROR`, with the same teaching text on stderr. It
     issues no stop, no rm, no launch and no `podman run`. A raise counts as a failure.
   - Control: a healthy recreate still stops, removes and relaunches once.
   - **R1:** a 7-cell matrix (static 0/1/3 × snapshot absent/present, plus a regular *file* at the path). In every cell, `_launch_container` refuses iff `verb_start`
     refuses. The spec-dictated cells are also anchored, so agreement cannot come from both levels being wrong. The file cell
     is where an `exists()` clone and an `is_dir()` clone diverge.
   - **R2:** recreate path with an operator typo (`watch: statc`) gives `_EXIT_ERROR`, no stop, no rm, no launch, and the
     config path on stderr. At HEAD it does stop+rm and then raises.
   - Tests: `TestMissingHostSnapshotRefusesLaunch`, `TestVerbStartRefusesMissingSnapshotBeforeTeardown`, `TestOneLaunchPreconditionDecidesBothLevels`, `TestMalformedConfigAbortsRecreateBeforeTeardown`
   - Catches: a refusal placed after teardown (the outage), a CalledProcessError lie, two cloned conditions, a silent skip.

`_read_config_field` returning `""` is **unreachable**. The real reader prints `sum(...)`, always an int, and raises
`RuntimeError` on a non-zero exit. HEAD's `""` arm is dead code. The contract runs the REAL reader over configs derived from
the real `lore.yaml`, so it neither pins `""` nor depends on the expression's spelling.

## Adversarial pre-flight
| input / failure | covered by |
|---|---|
| wrong target (`/source`, or retyped) | pin 1 (derived from loremaster) + pin 2 |
| bind present but not where the server reads | pin 2 (real guard in real image) |
| supplement instead of replace | pin 1, exactly one bind + no `/source` |
| rw instead of ro | pin 1 options |
| boundary count 1 vs N; 0 | pin 1 [1], [3]; pin 3 |
| host snapshot absent | pin 4 (both levels, both paths) |
| regular file at the snapshot path | R1 file cell (agreement only; verdict is S2) |
| refusal fires after teardown | (c)(ii) recreate leg (B1/B2 shape) |
| malformed config on recreate | R2 |
| HOME / server root moves | pin 1 derivation; pin 2 asserts the in-image root == derived target |
| probe grades the mount, not the image | pin 2 provenance assert |
| probe step no-ops (still detached/named/networked) | `_as_one_shot_probe` checks the result |
| vacuous ∀ (no static tiers) | pin 2 asserts the tier list is non-empty and equal to lore.yaml's |
| one tier's dir absent/empty under an existing root | **scoped out: spec-silent S1** (below) |
| `effective_roots` ≠ `c.roots` (count undercount) | scoped out: not measured. For this repo both give 3 (live read); flagged below |

## Realism checklist
- ☑ Production-realistic inputs: configs derived from the real `lore.yaml`; real tier names; the host snapshot shaped like `~/docker/mcp/lore-snapshot`.
- ☑ Independent expected values: target from `loremaster.server`; tiers from raw YAML in the test, not from loremaster.
- ☑ Seam coverage: the real `_read_config_field` subprocess (host→loremaster), and the real argv→podman→image seam (pin 2).
- ☐ Magnitude bound: not applicable because there are no derived numeric outputs (argv and booleans only).
- ☑ Shared conventions: `CONTAINER_HOME`, `IMAGE`, `DEFAULT_PORT_BASE`, `SNAPSHOT_ROOT` come from `lore_deploy`; the server root from loremaster.
- ☐ Hostile rendered text: not applicable because nothing renders stored free text.
- ☐ Input accounting: not applicable because no collection is transformed.

## Inventory adjudication (PLAN §Removed-behaviour inventory)
| item | verdict | pin / note |
|---|---|---|
| `/source:ro` bind | **dropped-deliberately**: 0 readers (r1–r3), operator "REPLACE" | pin 1 `test_no_bind_targets_the_retired_source_path` |
| silent skip when host snapshot missing | **dropped-deliberately** → loud refusal (operator pin-4 grant, PLAN §The change 2) | pin 4 + (c)(ii) |
| docstrings claiming `/source` | **old-bug** (false since `407d7f7`), corrected by prose wave; not pinned | — |
| `""` count arm | **old-bug / dead code** (unreachable, above) | not pinned |
| ro-ness of snapshot bind | **preserved-with-pin**, citing PLAN §The change 1 (`…:ro`) | pin 1 |

**Deliberate drops:** `/source` bind; the silent skip.
**Spec-silent (operator ruling needed):**
- S1: host root exists, but a static tier's dir is absent or empty. Boot crashes the same way (the guard treats empty as
  unmaterialised). Should pin 4 refuse per tier?
- S2: a regular file at `SNAPSHOT_ROOT`. Refuse, or not? R1 pins only that both levels agree. The reference build refuses
  (it uses `is_dir`).

## Receipts
- RED (HEAD `acbce73`). RAN: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q test_launch_snapshot_bind.py --timeout=300 -p no:cacheprovider` → `10 failed, 8 passed in 17.30s`.
  - Greens: pin 3 ×2; R1 cells 0-absent, 0-present, 1-present, 3-present, 3-file; the healthy-recreate control.
- Satisfiability.
  - RAN, cwd `/var/tmp/claude-1000/contract-165-mirror/repo/skills/lore-deploy/scripts`: `systemd-run … /home/ejprice/PycharmProjects/lore/.venv/bin/python -m pytest -q . ../tests --timeout=300 -p no:cacheprovider -n 8` → **`138 passed in 8.20s`**.
  - `lore_deploy.__file__ = /var/tmp/claude-1000/contract-165-mirror/repo/skills/lore-deploy/scripts/lore_deploy.py`. Also self-evident: pins 1 and 4 cannot pass against HEAD's module.
  - Plain-`cp -a` leg (`contract-165-ref`): test_launch_snapshot_bind + test_lore_deploy gave `55 passed`. `. ../tests` there gave 11 failed.
  - CONTROL on an unmodified `cp -a` (`contract-165-ctl`, `cmp` == HEAD): the same 11 node ids fail (`11 failed, 46 passed`). Cause: `REPO_ROOT = parents[3]` in `../tests`. That is location, not attributable, which is why the mirror run exists.
- Ruff: `All checks passed!` + `1 file already formatted`.
- typecheck.sh covers `skills` (`MEMBERS=(… skills …)`): `typecheck: skills OK`.
- Currency `--legs typecheck,ruff`: ruff GREEN, typecheck RED_ADJUDICATED. It renders `CURRENCY: FAIL` only because pytest is "NOT_RUN". RED_ORPHANED over the run legs: 0. Filed as **#555**.
- Reference build (pasted verbatim, brief-base §1 instrument rule):
```diff
+CONTAINER_SNAPSHOT_DIR = f"{CONTAINER_HOME}/docker/mcp/lore-snapshot"
+def _static_root_count(config_path: Path) -> int:
+    return int(_read_config_field(config_path, "sum(1 for r in c.roots if r.watch == 'static')"))
+def _snapshot_precondition_error(config_path: Path) -> str | None:
+    if _static_root_count(config_path) > 0 and not SNAPSHOT_ROOT.is_dir():
+        return (f"static roots configured but host snapshot {SNAPSHOT_ROOT} is absent; "
+                f"cold-index first: python -m loremaster.index --config {config_path}")
+    return None
 # in _launch_container, replacing the old count/exists/`/source` block:
+    refusal = _snapshot_precondition_error(config_path)
+    if refusal is not None:
+        raise RuntimeError(refusal)
+    if _static_root_count(config_path) > 0:
+        cmd += ["-v", f"{SNAPSHOT_ROOT}:{CONTAINER_SNAPSHOT_DIR}:ro"]
 # in verb_start, after the env-file check on BOTH the recreate (pre-teardown) and fresh paths:
+    try:
+        refusal = _snapshot_precondition_error(config_path)
+    except RuntimeError as error:
+        refusal = str(error)
+    if refusal is not None:
+        print(f"start: {refusal}", file=sys.stderr)
+        return _EXIT_ERROR
```
  Full diff: `/var/tmp/claude-1000/c165-reference.diff`. Mirror recipe: symlink every top-level repo entry except `.git` and
  `skills`, symlink `skills/*` except `lore-deploy`, `cp -a skills/lore-deploy`, overwrite `lore_deploy.py` with the reference.

## DRY ledger (test-side symbols)
| new symbol | looked | found | disposition |
|---|---|---|---|
| recreate wiring + launch recorder | `test_lore_deploy.py` read | `_RecreatePathFixture` | **REUSED** (imported) |
| `_bind_mounts`, `_as_one_shot_probe`, `_VerbStartArrangement` | `lore_search` over the skill tests; read `test_lore_deploy.py` | no argv-mount parser or one-shot transform | HAND-ROLLED (test-only) |
| in-image probe | r3 §Execution probe | the r3 instrument | **adapted** (JSON output, LORE_CONFIG-driven) |

## Anything else noticed (raised, not dropped)
1. The reference repeats the verb_start try/print block twice. The implementer should factor it (one helper), or R1's spirit erodes at the reporting layer.
2. R1 is pinned by behavioural agreement. The **mutation proof of sharing** (change the shared predicate, both levels move) belongs to the audit; I did not run it (ROLE BOUNDARY).
3. `_launch_container` counts `c.roots` while the server iterates `effective_roots`. They are equal for this repo (3/3, live read) but not proven equal in general. If `effective_roots` can synthesise a static root, the deploy undercounts.
4. The teaching message is pinned as `-m loremaster.index` + `--config`, not the exact config path. The stronger reading (paste-ready path) is available if the lead wants it.
5. Pre-existing, outside the snapshot condition: B3's CalledProcessError handler drops the error text.
6. The R2 failure message embeds the whole reader traceback. That is noisy but harmless.
7. `skills/lore-deploy/references/lifecycle.md` is modified in the working tree, not by me (presumably the prose wave).
8. Brief said "67 covering tests". Re-derived: `test_lore_deploy.py` collects **37**; the skill idiom collects 138 including this file's 18.
9. Scratch left for the lead (my `rm -rf` was denied by permissions): `/var/tmp/claude-1000/contract-165-{ref,ctl,mirror}`, `/var/tmp/claude-1000/c165-*`.

## Amendment r2 (directive #18003, acked 16:37Z; deadline 17:22Z; base HEAD 26c3a20)
### Routing table (written first)
| step | tier | who | reason |
|---|---|---|---|
| A lookups (SnapshotLayout API, test_indexer Indexer construction, `_loremaster_python`/`_schema_load_snippet`) | 1 | me, ONE parallel batch of 3 reads (~60 lines) | small set, all read in full anyway, on the critical path |
| B pins | 3 | me | contract authorship |
| C RED run | 1 | haiku-runner | brief-routed; spawned after B (it needs the new tests), not together with D.1 |
| D.1 scratch_copy.sh | 1 | haiku-worker | brief-routed; spawned now, in parallel with A/B |
| D.2 reference build | 3 | me | judgment |
| D.3 satisfiability | 1 | haiku-runner | brief-routed |
| E gates | 1 | haiku-runner | brief-routed |

### A. Lookups (one parallel batch, 3 reads + 2 small probes, ~120 lines)
- `SnapshotLayout`: `__init__(snapshot_root)`, `tier_locations`, `materialization_dir` (= first location). `TIER_SUBDIRS` maps `pip` → (`pip-packages`, `apt-packages`); every other tier, including our 3 static ones, maps to `<root>/<tier>` (live probe).
- `Indexer.__init__` only ASSIGNS its collaborators (`self._snapshot_layout = SnapshotLayout(snapshot_root)`), so the contract builds a REAL `Indexer` with placeholder store/embedder/manifest/registry. No private-attribute poke, unlike the r3 probe. `test_indexer.py::_make_indexer` needs `_surreal_fakes`, which the skill dir cannot import.
- `_loremaster_python` / `_schema_load_snippet`: already read in r1 (§Contract); the precondition can evaluate loremaster code through `_read_config_field`'s venv.

### New and changed tests (26 total, was 18)
| test | change | wrong build it catches |
|---|---|---|
| `TestDeployPreconditionAgreesWithServerGuard::test_deploy_refuses_a_tier_iff_server_guard_reads_it_unmaterialised[absent/empty/non_empty/file]` | NEW (S1 pin 2) | a deploy-side copy of the rule: `exists()` (passes the `file` cell), presence without the non-empty leg (passes `empty`), a root-only check (passes all three). It also asserts the fixture really drove the server: the server reads exactly the probed tier unmaterialised |
| `…::test_deploy_reads_the_server_layout_not_a_retyped_root_slash_tier` | NEW | a precondition that hand-builds `<root>/<tier>` instead of calling SnapshotLayout. The tier comes from production `TIER_SUBDIRS` (first whose dir ≠ name, currently `pip`), so the server serves it and a clone refuses it. GREEN at HEAD by design (HEAD never refuses) |
| `TestOneLaunchPreconditionDecidesBothLevels[3-tier_absent, 3-tier_empty]` | NEW cells (S1 pin 1) | a refusal that only looks at the root; a level that checks per tier while the other does not |
| `…[3-file]` | anchored to REFUSE (S2) | an `exists()`-based refusal at both levels (agreement alone let it through) |
| every refusal assertion (`_assert_teaches_every_failing_tier`) | CHANGED (item 3 + S1 text) | a placeholder remedy, a missing tier name or dir, and a refusal that names HEALTHY tiers' dirs |
| `TestRecreateLaunchFailureCarriesTheErrorText` | NEW (R3) | HEAD's generic hint. The test asserts the exit code AND the image token, which only the error's own command carries, because the hint already contains "125" and "podman" |
| `_make_host_snapshot` | CHANGED | places tier dirs with `SnapshotLayout.materialization_dir`, not a retyped `root/tier` (clause 5) |
| `test_indexer.py` / `test_source.py` | not edited | S1 pin 3: they run in D.3 against the reference's delegation |

No optional `loremaster/tests/test_snapshot_materialized.py`: the server leg lives in the skill file, because the skill env imports loremaster and the agreement pin needs ONE fixture set driving both sides.

### Reference build (scratch `/var/tmp/claude-1000/c165-r2-scratch`, applied over the r1 reference shape)
- `SnapshotLayout.tier_materialized(tier)` = `materialization_dir(tier).is_dir() and any(iterdir())`; `Indexer._snapshot_materialized` returns it.
- `lore_deploy._unmaterialised_static_tiers(config_path)` evaluates THAT predicate over the host `SNAPSHOT_ROOT` through `_read_config_field` (loremaster venv; the result goes back as JSON). `_snapshot_precondition_error` lists `tier at dir` plus `python -m loremaster.index --config <path>`.
- The two verb_start pre-teardown blocks are as in r1. R3 appends `({error})` to the existing recreate-failure message.

### r2 receipts (measured 2026-10-31; tree HEAD `26c3a20`, plus uncommitted prose-wave edits that are not mine)
- **D.1** (haiku-worker): `./scripts/scratch_copy.sh /var/tmp/claude-1000/c165-r2-scratch` → `exit=0`; provenance: loremaster/loresigil/lorescribe/lorerunes all resolve inside the copy.
- **C RED** (haiku-runner; RAN == my command): **`17 failed, 9 passed in 20.58s`**. I re-read the log myself. Every failure is behavioural: assertion messages, `DID NOT RAISE RuntimeError`, the R2 fail-on-raise after an observed stop+rm, and R3 `stderr must carry the failed command`. No import or collection errors.
  - Greens (9): pin 3 ×2; R1 cells 0-absent, 0-present, 1-present, 3-present; the healthy-recreate control; agreement `[non_empty]`; the layout-divergent pin. The last three are GREEN at HEAD by design, because HEAD never refuses.
- **D.3 satisfiability**, first attempt: `25 failed, 173 passed`. Two causes, neither a contract defect:
  - (a) `_loremaster_python()` hardcodes the ORIGINAL repo venv, so the reader subprocess imported the original loremaster: `AttributeError: … no attribute 'tier_materialized'`. Filed **#558**.
  - (b) My reference issued its JSON tier query to `test_lore_deploy._stub_read_config_field`, which answers `"0"` to ANY expression containing "static" (`TypeError: 'int' object is not iterable`, 9 existing tests). Fixed in the reference by checking the static count first.
- **D.3 rerun** (haiku-runner, `LORE_PYTHON=<scratch>/.venv/bin/python`): **`198 passed in 12.60s`**, 0 failed, over `. ../tests ../../../loremaster/tests/test_indexer.py ../../../loremaster/tests/test_source.py`. I verified this in the log myself.
  - `loremaster.__file__` = `/var/tmp/claude-1000/c165-r2-scratch/loremaster/loremaster/__init__.py`
  - `lore_deploy.__file__` = `/var/tmp/claude-1000/c165-r2-scratch/skills/lore-deploy/scripts/lore_deploy.py`
  - spawned `_loremaster_python()` → `/var/tmp/claude-1000/c165-r2-scratch/loremaster/loremaster/__init__.py`
  - S1 pin 3: test_indexer + test_source green against the delegating `Indexer._snapshot_materialized`.
- **E gates** (haiku-runner): ruff `All checks passed!`. typecheck: `skills OK`; `loremaster FAILED` (82) and `scripts FAILED` (1) are the same 83 RED_ADJUDICATED residuals as r1, owned by packet-58 / 64b-i, none in skills.

Fan-out: haiku 5 (1 worker, 4 runners) · sonnet 0 · peak 2 (D.3 + E concurrent; C ran alongside my D.2 build).

### r2: anything noticed
1. **Constraint for the implementer:** existing `test_lore_deploy.py` stubs answer `"0"` to any `_read_config_field` expression containing "static". A build whose first static-related read is not a count breaks 9 existing tests. Count first, as the reference does, or the lead routes a test edit. This is a stub-spelling coupling in the existing suite, and I did not edit it (outside my writable set).
2. **#558:** `_loremaster_python` defeats scratch isolation for anything `lore_deploy` spawns. scratch_copy.sh's provenance check cannot see it. Every future mutation proof of the deploy needs `LORE_PYTHON` set until it is fixed.
3. Uncommitted prose-wave edits in `indexer.py`, `snapshot.py`, `server.py`, `test_source.py` and docs (not mine) were copied into the scratch by scratch_copy.sh, so D.3 graded them too (green).
4. S1's named bound (#166, the version-stamp leg) is not pinned pre-launch, as ruled.
5. The sharing mutation proof (S1 pin 4) is the audit's; not run (ROLE BOUNDARY).
6. Scratch left: `/var/tmp/claude-1000/c165-r2-scratch`, `/var/tmp/claude-1000/c165-r2-*.log`.
