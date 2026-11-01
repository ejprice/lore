brief-base v25 read · brief project v7 read

# REPORT — contract-572-ledger, ROUND 2 (directive #18019, HEAD f247deb, 2026-11-01)

## Round-2 summary
- **State:** done-with-deviations.
- **Directive #18019:** acked. It landed: every item below is built.
- **Deviations:**
  1. RED and satisfiability took 2 runs each, not 1. The first RED run (`gate-572-ledger-r2-RED.log`) exposed two fixture defects: C5/status hit an unmodelled `podman image inspect`, and the C6 schema fixture's first pydantic error was "Field required", not the slug error. Both were fixed. The first-pass logs are kept and marked VOID here.
  2. I added one pin beyond C1–C6: status over a corrupt ledger. C1's class covers every ledger reader, not only setup.
- **Rulings applied:**
  - F-1 (a): the 7 C-DEF nodes are rewritten in `test_scaffold_slug.py`.
  - F-2 (a): accept the re-index; no migration.
  - F-3 = #565: no new finding.
  - S1: `PodmanShim`'s cold-index stub no longer writes `<slug>.db`. `_index_like_the_real_indexer` is deleted.
- **E501 at test_ledger_572.py:359:** already clear at f247deb (ruff passed before any round-2 edit). The RED_ORPHANED that #18019 cites came from a run before my round-1 line-length fix.
- **RED at f247deb (final tree):** 57 failed, 362 passed. Every failure is an assertion in a new or rewritten node. No unmodified pre-existing test fails. No ImportError or collection error.
- **Satisfiability (fresh scratch `/var/tmp/claude-1000/ledger572-scratch-r2`, reference covers #572 + C1–C6):** **419 passed, 0 failed.** `loremaster.__file__` = `/var/tmp/claude-1000/ledger572-scratch-r2/loremaster/loremaster/__init__.py`; `lore_deploy.__file__` is in scratch.
- **Currency `--legs typecheck,ruff`:** typecheck RED_ADJUDICATED (packet-58 / 64b-i; neither of my files is named), ruff GREEN, **RED_ORPHANED 0**. CURRENCY FAIL comes only from pytest NOT_RUN (#565).
- **Packages considered:** stdlib `sqlite3`; PyYAML and pydantic serve as the C6 oracle (the loader's own libraries). No new mechanism.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** round 2 adds test-side helpers only (`_provision`, `_write_unreadable_config`, `_config_problem`, `_truncated_sqlite_bytes`, `_text_over_the_file`, `_nonblank_lines`), all in `test_scaffold_slug.py` beside the harness they extend. Looked in `config_reader_fake.py` and `test_scaffold_slug.py`; none existed.
- **Decisions needed:** none new. The F-2 re-index cost is unmeasured (the lead flags it at close-out).
- **Receipts:** `## Round-2 gate receipts` · reference `docs/plans/v2/receipts/2026-10-31-165/reference-572-ledger-r2.SATISFIABILITY-ONLY.diff`.

## F-1: the 7 C-DEF nodes, rewritten (`test_scaffold_slug.py`)
Each now gets its provisioned state from the new `_provision` helper, a real successful `setup`, never from `_write_manifest(owner=…)`. None asserts a ledger count.

| node (after) | was | now pins |
|---|---|---|
| `TestEveryVerbUsesTheConfiguredSlug::test_status_reads_the_manifest_the_slug_names[odoo_custom,odoo]` | `indexed=3` printed | the owner recorded in `<configured_slug>.db` is shown; `indexed=3` is NOT shown, even with a legacy `files` table planted |
| `…::test_setup_recognises_a_provisioned_project_and_rewires_its_slug[odoo_custom,odoo]` | owner-only fixture = provisioned | provisioned by a real setup; `.mcp.json` deleted; re-run with an absent env-file is a no-op, does not re-index, and rewires `lore_<slug>` |
| `TestSetupRecordsAndHonoursItsOwnProjectPath::test_existing_deployment_with_a_legacy_manifest_is_reindexed_and_claimed[odoo_custom,odoo]` (renamed from `…backfills_its_legacy_manifest_and_proceeds`) | backfill + no-op, no index | F-2 (a): not refused; cold-indexes once; records the owner; touches no container; wires `.mcp.json`; the NEXT setup (absent env-file) is a no-op |
| `…::test_same_project_rerun_with_its_running_container_is_not_refused` | owner-only fixture | provisioned by a real setup, then the re-run with its own container running: no re-index, no mutating podman call |

The module docstring and the `MANIFEST_SCHEMA` / `MANIFEST_INDEXED_ROWS` comments now say "pre-P5" and "never counted".

## C1–C6 → pins → the wrong build each kills
| item | pin (`test_scaffold_slug.py` unless noted) | wrong build killed | at f247deb |
|---|---|---|---|
| C1 read | `TestSetupRefusesACorruptLedgerLoudly::test_a_corrupt_ledger_refuses_naming_the_file_and_creates_nothing[{text_over_the_file,truncated_sqlite}-{derived,hand_set}]` | uncaught `sqlite3.DatabaseError`; catching only `OperationalError` (both shapes raise the `DatabaseError` base, probed); a multi-line message; scaffolding or wiring before the refusal | RED ×4 |
| C1 write | `…::test_a_ledger_write_that_fails_refuses_naming_the_file[derived,hand_set]` (ledger dir 0555, a uid-mismatch door; skipped under root) | `record` / marker write raises `OperationalError: unable to open database file` | RED ×2 |
| C1 class | `test_ledger_572.py::TestStatusOverACorruptLedger::test_status_names_a_corrupt_ledger_without_a_traceback` | the #572 status rewrite reading the ledger without the C1 guard (the old `_manifest_counts` caught `sqlite3.Error`; a rewrite can drop that) | green ×2: HEAD's `_manifest_counts` catches it. It guards the rewrite |
| C2 | `TestCollisionReadsBothHolders::test_refuses_when_the_container_is_ours_but_the_manifest_records_another_project[derived,hand_set]` | collision returns "ok" when the container mounts this path (short-circuit on the container) | green ×2 (HEAD reads both); pins F4 "manifest OR container" |
| C3 | `…::test_refuses_an_ownerless_manifest_without_a_lore_yaml_even_when_the_container_is_ours` | the container match excusing an ownerless manifest on a fresh setup | green (HEAD) |
| C4 | `TestScaffoldKeepsTheUmaskMode::test_scaffolded_lore_yaml_has_the_umask_default_mode[umask022,027,002]` | the staged 0600; a hard-coded 0644 (killed by 027 → 0640 and 002 → 0664) | green ×3 (the A3 fix) |
| C5 | `TestVerbsWithoutALoreYamlUseTheDerivedSlug::test_verb_addresses_the_derived_slugs_container[stop,status]` | raw name `lore-odoo-custom`; stop issuing no stop | green ×2 |
| C6 | `TestVerbsRefuseAnUnreadableLoreYaml::test_verb_refuses_with_one_readable_remedy_and_touches_no_container[{stop,status}-{truncated_yaml,schema_invalid_slug}]` | the child traceback; no remedy as the LAST stderr line (`lore.yaml` + `podman stop`); not naming the file; dropping the parse error (oracle: PyYAML `problem` / pydantic's first `msg`, the loader's own libraries); **guessing the slug from the directory and stopping a container** (its own container is running, so a guess would stop it) | RED ×4 |

C6 doors: an editor-truncated file (production-shaped lore.yaml cut inside a flow sequence), and the production-shaped document with only `project.slug` set to the hyphenated directory name (the #568 mistake, hand-made).
**Bounds stated:** C1 pins "one stderr line", per the addendum. The remedy pin checks substrings (`lore.yaml`, `podman stop`) on the last line; that is the minimum the ruling's wording demands. The C1-class status pin leaves the exit code unpinned (spec-silent: status is a report).

## Round-2 adversarial pre-flight additions
| break | covered by / note |
|---|---|
| a corrupt ledger raises a traceback (read) | C1 read ×4 |
| a corrupt-ledger refusal scaffolds or wires first | C1 `assert_nothing_created` |
| a ledger write that fails raises a traceback | C1 write ×2 |
| `except OperationalError` only (misses `DatabaseError`) | both corrupt shapes raise the `DatabaseError` base |
| a status reader without the guard | C1 class pin |
| collision short-circuits on a matching container | C2 ×2, C3 |
| a hard-coded mode | C4 ×3 umasks |
| an unreadable config: guessing the slug | C6: no mutating podman call with the container running |
| an unreadable config: a traceback, or a buried remedy | C6 ×4 |
| a corrupt ledger under `status` with an unreadable lore.yaml | scoped out: the config failure fires first (slug unknowable), so C6 covers it |

## Round-2 realism clauses (deltas only)
- ☑ Corrupt-ledger shapes are probed, not assumed: `file is not a database` / `database disk image is malformed`, both `sqlite3.DatabaseError`.
- ☑ The C6 expected error text comes from the loader's own libraries run on the same text (an independent oracle), not from `lore_deploy`.
- ☑ The C6 / C4 configs come from the shared `realistic_config_document` builder.
- ☑ Hostile fixture: the corrupt "text" ledger is status-shaped text (`status: lore-odoo_custom container = absent`).

## Round-2 gate receipts
| gate | command | log | EXIT | count line | TREE |
|---|---|---|---|---|---|
| RED at f247deb (FINAL) | `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q test_ledger_572.py . ../tests -n 8 --timeout=300 -p no:cacheprovider -rfE` | `docs/plans/v2/receipts/2026-10-31-165/gate-572-ledger-r2b-RED.log` | 1 (expected RED) | 57 failed, 362 passed | 9ecdccee4c4f7bec1acddfc449b1ccac064c16b9b5b3748d72a4241c6caf2040 (HEAD f247deb) |
| satisfiability (FINAL) | same command in `/var/tmp/claude-1000/ledger572-scratch-r2/skills/lore-deploy/scripts`, `LORE_PYTHON=<scratch>/.venv/bin/python`, PROVENANCE print first | `docs/plans/v2/receipts/2026-10-31-165/gate-572-ledger-r2b-SAT.log` | **0** | **419 passed** | 063228b96f0e80fbed836dcf9a14a8b49bf022aee5d439082dd010dc9dd814c5 (scratch) |
| currency typecheck,ruff | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `docs/plans/v2/receipts/2026-10-31-165/gate-572-ledger-r2b-currency.log` | 1 (#565) | typecheck RED_ADJUDICATED · ruff GREEN · RED_ORPHANED 0 | 06e39500519d07f4ef16f55f248deb08d82c461f717b9ca56b82b9efd1c1fcd4 |
| VOID first pass (fixture defects, see deviation 1) | same | `gate-572-ledger-r2-RED.log` (58 failed / 359 passed), `gate-572-ledger-r2-SAT.log` (1 failed / 418 passed: C5 status, a shim gap) | — | VOID | — |

Runs used, round 2: 4 pytest runs (2 void + 2 final). The reason is deviation 1.
The RED tree differs from the currency tree only because this report changed after the RED run.

## Round-2 reference (SATISFIABILITY ONLY; full diff archived above)
On top of the round-1 ledger reference:
- **`LedgerError(RuntimeError)`:**
  - `ManifestOwner._meta` turns any `sqlite3.DatabaseError`, and any `OperationalError` other than "no such table", into one line naming the file;
  - `record` / `mark_provisioned` wrap `sqlite3.Error` the same way.
- **`verb_setup`:** wraps the collision check, provisioned check and marker write in `except LedgerError` → `_EXIT_ERROR` plus one stderr line.
- **`_read_config_field`:** the child snippet catches `Exception` and exits with `TypeName: message` (no traceback).
- **`verb_stop` / `verb_status`:** after the config error, print a final remedy line, `fix <project>/lore.yaml, or stop the container by hand: podman stop lore-<slug>`.
- **`verb_status`:** prints a `LedgerError` as its ledger line.

The builder chooses the actual shape.

## Noticed (round 2)
- The schema door's real-world shape is exactly #568's own failure: an operator hand-writing the hyphenated directory name as `project.slug`. Before C6, that `stop` printed a 30-line pydantic traceback.
- The 3 `wire_test_*.memory.db` strays in `~/.local/state/lore/` (round 1) are still unowned.

---

# ROUND 1 (superseded where round 2 says so)

brief-base v25 read · brief project v7 read

# REPORT — contract-572-ledger (tdd-light Phase 1, finding #572, wave #165)

## Summary
- **State:** done-with-deviations. **C-DEF trap: 7 pre-existing pins contradict the ruling** (listed below). They need a lead/operator decision before a builder starts.
- **Deviations:**
  1. RED and satisfiability ran on HEAD 99c2b8e plus a sibling's uncommitted diff (`lore_deploy.py`: umask chmod in the scaffold, `import sqlite3` hoisted, `--project` help text; `loremaster/config.py`). None of it touches setup's provisioned check or status.
  2. I did not reuse `PodmanShim` from `test_scaffold_slug.py` (DRY ledger).
  3. **Shell incident:** a report-writing heredoc was unquoted, so bash ran the backtick spans as command substitutions. One extra pytest run (cgroup-capped, unlogged), one currency `--legs typecheck,ruff` run, ruff, and a failed mypy call ran unplanned. No gate log was overwritten (each still has its one `EXIT=` line; mtimes are from before the incident). No tracked file changed. Nothing destructive.
- **Pins:** `skills/lore-deploy/scripts/test_ledger_572.py`, 51 tests collected, ruff clean, mypy clean.
- **RED at HEAD 99c2b8e (+ the sibling diff):** 43 failed, 356 passed. All 43 failures are in the new file and every one is an AssertionError (no ImportError or collection error). Every pre-existing test passes.
- **Satisfiability (scratch, reference diff below):** 7 failed, 392 passed. **All 51 new pins pass.** The 7 failures are exactly the C-DEF pins. `loremaster.__file__` = `/var/tmp/claude-1000/ledger572-scratch/loremaster/loremaster/__init__.py`, and `lore_deploy.__file__` is in scratch.
- **Packages considered:** stdlib `sqlite3` (the ledger's existing reader/writer, `ManifestOwner`, read in full). No new mechanism is specified; the marker is one meta row.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 2 new test-side symbols (`DeployShim`, `LedgerScene`), both dispositioned below.
- **Graded:** n/a (author report, not a verdict).
- **Decisions needed:**
  - F-1: rewrite or retire the 7 C-DEF pins.
  - F-2: the live deployments re-index on their next `setup`.
  - F-3: `--legs typecheck,ruff` prints CURRENCY FAIL by construction.
- **Receipts:** `## Gate receipts` below · reference diff archived at `docs/plans/v2/receipts/2026-10-31-165/reference-572-ledger.SATISFIABILITY-ONLY.diff`.

## Capability check
Nothing was denied. The brief's `-rfE` summary lines carry no reason text in this pytest version, so the runners took reasons from the E lines instead.

## Routing table (written at start; final)
| step | tier | who | reason |
|---|---|---|---|
| read the ruling, the setup/status code, the existing #568 harness | 3 | self | contract fixture judgment |
| legacy ledger `.schema` (2 files) | 1 | self, inline | one command, output read whole, on the critical path |
| write pins | 3 | self | contract |
| RED run | 1 | haiku-runner | |
| scratch copy + reference build | 3 / 1 | self (`scratch_copy.sh` in the background) | reference design |
| satisfiability run | 1 | haiku-runner | |
| currency typecheck,ruff | 1 | haiku-runner | |
| ruff / mypy on one file, collect-only | 1 | self, inline | each under 1 s, output read whole |

Fan-out: haiku 3 · sonnet 0 · peak 3.

## Contract in plain English
- **The ledger.** The host `<slug>.db` is a ledger, not an index. `setup` writes the owner path. It writes a provisioned marker only after its cold index exits 0.
- **"Already provisioned" means the marker is present.** It never means "the file exists", "an owner row exists" or "a legacy `files` table has rows".
- **What `status` prints.** It never prints a count derived from the ledger. In every ledger state, absent included, it names `lore_index()` as where the index counts live. It prints no "unreadable" line for a meta-only ledger. It shows the owner path, and it prints a different report once the marker exists.
- **The marker's spelling is the builder's choice.** The pins observe it only through behaviour: what the next `setup` does and what `status` prints.

## Pins → the wrong build each one kills
| pin (class::test) | wrong build it kills |
|---|---|
| TestSetupMarksProvisionedOnlyAfterASuccessfulColdIndex::test_a_project_setup_provisioned_is_recognised_on_the_next_setup | marker never written, or ignored (re-indexes on every run) |
| …::test_a_failed_cold_index_leaves_the_project_unprovisioned | marker written BEFORE the index, or regardless of its exit |
| …::test_a_failed_cold_index_over_an_owner_only_ledger_leaves_it_unprovisioned | "provisioned = owner row"; marker written on the owner-record path |
| TestProvisionedDecisionFollowsTheMarker::test_an_owner_only_ledger_is_not_provisioned | "provisioned = file exists" or "= owner recorded" (the #568 backfill's shape) |
| …::test_an_owner_only_ledger_is_never_a_no_op | same, seen as a no-op success that indexed nothing (absent secrets, failing probes) |
| …::test_a_legacy_ledger_with_indexed_files_is_not_provisioned[small, large] | "provisioned = files table has rows" (index state inferred from the ledger) |
| …::test_the_cold_index_runs_against_this_projects_config | indexes some other config |
| …::test_status_does_not_provision_an_owner_only_ledger | status (a non-setup verb) writes the marker |
| TestStatusShowsNoIndexFactFromTheLedger::test_status_output_does_not_depend_on_the_ledgers_files_table[3 states] | ANY count of the files table in any wording, "no files indexed yet", or "unreadable": output must be byte-identical across files = absent / empty / 412 / 2917 rows |
| …::test_status_prints_no_count_of_the_legacy_files_rows[3 states] | prints the per-state, total or chunk counts (2917 / 20419 / 2188 / 729), with tmp paths scrubbed |
| …::test_status_names_where_the_index_counts_live[absent + 3 states] | no pointer to `lore_index` |
| …::test_status_over_a_meta_only_ledger_reports_nothing_unreadable[absent, owner, owner+marker] | HEAD's `(unreadable: no such table: files)` |
| TestStatusShowsTheLedgerAsWhatItIs::test_status_shows_the_recorded_owner_path | owner path not shown |
| …::test_status_tells_provisioned_from_owner_only | marker not shown (one project path, so the marker is the only difference) |
| …::test_a_hostile_owner_path_cannot_forge_a_status_line | owner path rendered raw: a directory name containing a newline prints a forged `status: index = 2917 files…` line |

Every scene-based pin runs over 2 project names and slugs (`odoo-custom`→`odoo_custom`, `demand_intelligence`).

**The 8 new pins that pass at HEAD, and why:**
- recognised-on-next-setup ×2 and failed-index-leaves-unprovisioned ×2: HEAD writes its file after the index, so these doors open only for a wrong build;
- meta-only-unreadable[None] ×2: HEAD prints no unreadable line for an absent ledger;
- hostile-owner ×2: vacuous at HEAD, which prints no owner. It starts to bite once the owner is shown.

**Named residual:** "tells provisioned from owner-only" pins only that the two outputs differ, not the marker's wording. That is deliberate, to stay off prose spelling.

## C-DEF — pre-existing pins the ruling contradicts (red on the reference build; not edited)
All are in `skills/lore-deploy/scripts/test_scaffold_slug.py`:
1. `TestEveryVerbUsesTheConfiguredSlug::test_status_reads_the_manifest_the_slug_names[odoo_custom]` and `[odoo]` assert status prints `indexed=3`, which is a ledger count. **Fix:** assert that status addresses the configured slug's ledger (its path or owner), with no count.
2. `TestEveryVerbUsesTheConfiguredSlug::test_setup_recognises_a_provisioned_project_and_rewires_its_slug[odoo_custom]` and `[odoo]` build their fixture with `_write_manifest(owner=project)`: an owner row, no marker. They then assert no re-index. **Fix:** arrange the provisioned state with a real successful setup (as `LedgerScene.provision` does).
3. `TestSetupRecordsAndHonoursItsOwnProjectPath::test_existing_deployment_backfills_its_legacy_manifest_and_proceeds[odoo_custom]` and `[odoo]` assert: a legacy ledger (no owner, no marker) plus an absent env-file gives a no-op success with no index. The ruling says index state is never inferred from the ledger, so setup indexes and needs the secrets. See fork F-2.
4. `TestSetupRecordsAndHonoursItsOwnProjectPath::test_same_project_rerun_with_its_running_container_is_not_refused` uses the same owner-only fixture and asserts no re-index. Same fix as item 2.

Also in that file, `PodmanShim._index_like_the_real_indexer` fakes the cold index writing `<slug>.db` with `files` rows. Two sources say it does not:
- the ruling, measured at 0c7477c;
- my grep of `loremaster/loremaster`: `manifest_path` only anchors `<slug>.memory.db` and the state dir in `server.py`.

So nothing has written that file since P5, and the fixture models the pre-P5 world. That fixture is why pins 2 and 4 could pass for a build whose check was "the file exists".

## Forks (both readings written; my pick stated)
- **F-1 (lead): the 7 C-DEF pins.** They must be rewritten or retired in the same wave as the build, by a test author, never the builder.
  - (a) Rewrite them to arrange the ledger through a real setup. **This is my pick.**
  - (b) Delete items 1–4 as superseded by `test_ledger_572.py`.
- **F-2 (operator): live deployments.** Schema measured 2026-10-31: `~/.local/state/lore/lore.db` and `demand_intelligence.db` are `files` + `meta` tables (rows not read). If they carry no marker (none could: none exists before this build), the next `setup` on lore and on demand_intelligence re-runs the cold index and needs the secrets env-file.
  - Directive #18015 ("never refused") still holds: setup is not refused, it re-indexes.
  - Not measured here: whether a cold index against an already-populated store is a cheap delta or the #355 ~3h48m rebuild.
  - (a) Accept the re-index. That is what "index state is never inferred from the ledger" says, and it is what I pinned.
  - (b) A one-time migration that marks the live deployments provisioned. That is index state from a source other than setup's own successful index, so it is a ruling, not a contract choice.
- **F-3 (lead, instrument): `--legs typecheck,ruff` FAILs by construction.** `pending_contract_gate.py --currency --legs typecheck,ruff` prints `CURRENCY: FAIL — claimed but never run: pytest` and exits 1. That is the form CLAUDE.md prescribes for every round. Per-gate verdicts: typecheck RED_ADJUDICATED (owned by packet-58 / packet-64b-i), ruff GREEN, RED_ORPHANED 0. I read the verdicts, not the exit (#565). If #565 does not already cover the pytest-NOT_RUN orphan under `--legs`, it needs its own finding.

## Adversarial pre-flight
| break | covering case / note |
|---|---|
| marker written before the index | failed-index pins ×2 |
| marker written on a non-zero exit | same |
| provisioned = file exists | owner-only pins; legacy pins |
| provisioned = owner row (the #568 backfill) | owner-only pins |
| provisioned = legacy files rows | legacy pins (412 and 2917 rows) |
| status still counts the legacy files table, any wording | invariance pin + count-absence pin |
| "no files indexed yet" for an empty table | invariance pin (empty vs populated) |
| `(unreadable: …)` for a meta-only ledger | invariance pin (absent table) + unreadable pin |
| pointer missing for the never-set-up state | names-pointer[None] |
| a verb other than setup writes the marker | status-does-not-provision. `start`/`stop` scoped out: neither reads or writes the ledger at HEAD (grep of verb_start). Re-open if a builder adds a writer |
| owner path rendered raw (forgery) | hostile-owner pin |
| slug monoculture | 2 project names in the `scene` fixture |
| a count's digits inside a pytest tmp-dir number | tmp root scrubbed (`LedgerScene.tmp_root`) |
| status/setup dialling the production store | setup's probes stubbed; status reaches no probe for an absent container; root conftest :18500 guard active |
| cold index exits 0 but logs failures on stderr | scoped out: setup keys on the exit status, which is the indexer's contract, not the ledger's |

## Realism and independence clauses
- ☑ **Production-realistic inputs:**
  - the legacy schema was measured with `.schema` only (no row data read);
  - file counts of 412 and 2917 are repository-scale;
  - lore.yaml comes from the shared `realistic_config_document` builder;
  - the cold index writes nothing to the ledger, matching the measured post-P5 indexer.
- ☑ **Independent expected values:** every expectation comes from a clause of the ruling. The counts asserted absent were hand-computed from the fixture: 2188 indexed, 729 failed, 20419 chunks.
- ☑ **Seam coverage:** the real `verb_setup` / `verb_status`, slug resolver, config reads and `.mcp.json` merge all run. Only podman and the cold index are stubbed, at `_run`.
- ☐ **Magnitude bound:** not applicable. The contract asserts the absence of counts and derives none.
- ☑ **Shared conventions:** the owner row comes from production `ManifestOwner.record`, and the provisioned state from a real `setup`. No marker key is hardcoded.
- ☑ **Hostile fixture:** the owner path is stored text rendered to agents, so a newline plus a status-shaped forgery is pinned.
- ☐ **Input accounting:** not applicable, because nothing here is a collection transform.

## Reuse ledger
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `DeployShim` (test) | `test_scaffold_slug.PodmanShim`, read in full | Its podman model fits. But its cold-index answer writes a legacy `<slug>.db` (the pre-P5 world the ruling measured false), and it lives in a test module that `--import-mode=importlib` would import a second time. | HAND-ROLLED: about 20 lines; its index writes nothing |
| `LedgerScene` (test) | `test_scaffold_slug` `_create_manifest` / `_drive_setup` | They create the legacy manifest and owner rows. They have no failed-index or marker arrangement. | HAND-ROLLED; reuses `config_reader_fake` and `lore_deploy.ManifestOwner` |

Recommendation: when F-1 rewrites the C-DEF pins, promote one deploy-test harness (podman shim + scene) into a non-test module beside `config_reader_fake.py`.

## Gate receipts
| gate | command | log | EXIT | count line | TREE |
|---|---|---|---|---|---|
| RED at HEAD | `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q test_ledger_572.py . ../tests -n 8 --timeout=300 -p no:cacheprovider -rfE` | `docs/plans/v2/receipts/2026-10-31-165/gate-572-ledger-RED.log` | 1 (expected RED) | 43 failed, 356 passed | 2a250935e914d6efc79e23eeb7dc9632b2994e0bcbd10df04045cfb9cebb8f74 (HEAD 99c2b8e, 37 dirty) |
| satisfiability | same command in `/var/tmp/claude-1000/ledger572-scratch/skills/lore-deploy/scripts`, with `LORE_PYTHON=<scratch>/.venv/bin/python` and a PROVENANCE print first | `docs/plans/v2/receipts/2026-10-31-165/gate-572-ledger-SAT.log` | 1 (the 7 C-DEF pins only) | 7 failed, 392 passed | 10a6ddb74a608fdfac0aaa62f7d7a60728c79f2542cb99d9fae739499ad0385f (scratch) |
| currency typecheck,ruff | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `docs/plans/v2/receipts/2026-10-31-165/gate-572-ledger-currency.log` | 1 (F-3) | typecheck RED_ADJUDICATED · ruff GREEN · RED_ORPHANED 0 | bb1cdad5a60daabf2596493a76a6ed9f5320fc8de1fb037ae30a2b716eedf6fa |
| ruff (file) | `uv run ruff check skills/lore-deploy/scripts/test_ledger_572.py` | inline | 0 | All checks passed! | — |
| mypy (file, ad hoc; the canonical `typecheck.sh` MEMBERS includes `skills`, and no currency line names this file) | `uv run mypy test_ledger_572.py` (from scripts/) | inline | 0 | Success: no issues found in 1 source file | — |

**Runs used:** 2 planned pytest runs (RED, satisfiability), plus 1 unplanned run from the shell incident (deviation 3), whose result I did not use.
**Why the TREE values differ between rows:** the RED and currency rows differ only because report and log files changed between those runs.

## Reference diff — SATISFIABILITY ONLY
This is not a design for the builder to copy: the marker key and the status wording are the builder's choice. The diff is against the scratch tree, which includes the sibling's diff.

```diff
@@ imports
+import datetime
 import sqlite3
@@ constants
 PROJECT_PATH_META_KEY = "project_path"
+#: The ledger ``meta`` key ``setup`` writes only after a successful cold index (#572).
+PROVISIONED_META_KEY = "provisioned_at"
@@ class ManifestOwner
-    def recorded_path(self) -> str | None:
-        """The recorded owning project path, or ``None`` (no manifest, or a legacy one)."""
+    def _meta(self, key: str) -> str | None:
         if not self.manifest.exists():
             return None
         try:
             connection = sqlite3.connect(f"file:{self.manifest}?mode=ro", uri=True)
             try:
-                row = connection.execute(
-                    "SELECT v FROM meta WHERE k = ?", (PROJECT_PATH_META_KEY,)
-                ).fetchone()
+                row = connection.execute("SELECT v FROM meta WHERE k = ?", (key,)).fetchone()
             finally:
                 connection.close()
         except sqlite3.OperationalError:
-            # No ``meta`` table: a manifest that predates every meta row is ownerless.
             return None
         return None if row is None else str(row[0])
 
+    def recorded_path(self) -> str | None:
+        return self._meta(PROJECT_PATH_META_KEY)
+
+    def provisioned_at(self) -> str | None:
+        return self._meta(PROVISIONED_META_KEY)
+
+    def mark_provisioned(self, project: Path) -> None:
+        self.record(project)
+        connection = sqlite3.connect(self.manifest)
+        try:
+            with connection:
+                connection.execute(
+                    "INSERT OR REPLACE INTO meta (k, v) VALUES (?, ?)",
+                    (PROVISIONED_META_KEY, datetime.datetime.now(datetime.UTC).isoformat()),
+                )
+        finally:
+            connection.close()
@@ def verb_setup
-    already = config_path.exists() and owner.exists()
+    already = config_path.exists() and owner.provisioned_at() is not None
     if already:
-        if owner.recorded_path() is None:
-            # A legacy manifest this project's own lore.yaml declares: claim it (F4b).
-            owner.record(project)
         print(f"setup: {slug} already provisioned (config + manifest present) — no-op.")
@@ after the cold index succeeds
-    owner.record(project)
+    owner.mark_provisioned(project)
@@ def verb_status
-    if manifest.exists():
-        counts = _manifest_counts(manifest)
-        print(f"status: manifest {manifest} → {counts}")
+    ledger = ManifestOwner(slug)
+    if ledger.exists():
+        print(f"status: ledger {str(manifest)!r} owner={ledger.recorded_path()!r} "
+              f"provisioned_at={ledger.provisioned_at()!r}")
     else:
-        print(f"status: no manifest at {manifest} (not yet set up).")
+        print(f"status: no ledger at {str(manifest)!r} (not yet set up).")
+    print("status: index counts live in the store — call lore_index() for them.")
```
(Hunk headers are abbreviated; the full unified diff is in the archived file named above.)

What a real build still owes:
- deletes the now-dead `_manifest_counts`;
- drops the owner-backfill branch (as here; the marker write records the owner);
- sweeps the prose ("manifest" in the `verb_status` docstring, in `stop`'s "store data + manifest preserved", and in the "config + manifest present" message).

## Noticed outside this change
- **Test leakage into the host state dir.** On 2026-10-31, `~/.local/state/lore/` held 3 `wire_test_<pid>_<uuid>.memory.db` files. Some suite writes memory ledgers into the real `MANIFEST_DIR` (non-hermetic). I did not trace which one. Do you want it ledgered?
- `test_scaffold_slug.PodmanShim` models a pre-P5 indexer (see C-DEF).
- The `--project` help text change in the working tree is the sibling's uncommitted edit, not mine.
