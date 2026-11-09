brief-base v25 read
brief project v7 read

# REPORT conform-sdk3-66: packet 66 (surrealdb SDK 2.0.0 → 3.0.0) IN-IMAGE CONFORMANCE, measured 2026-11-08 22:53–23:45Z

- **State:** done-with-deviations. **Verdict: PASS for the SDK-3 artifact, with named holes.** None of the defects found is SDK-3-caused.
- **Findings first:**
  - ⚠ **INCIDENT:** I printed the prod `SURREAL_PASS` via `surreal export --help` inside lore-surreal (§INCIDENT; #601). The lead owns the operator escalation (rotation / transcript purge).
  - **#604:** served `lore_tasks` rollup teaches `pass capability=`, but the tool rejects it and the dispatch never forwards it, so the governed message leg is unreachable over MCP. Its green pin drives `ctx._rollup` directly.
  - **#605:** in no-auth (localhost) mode a VALID capability crashes with `AttributeError` while a forged one gets the uniform deny. This is a validity oracle and an untaught error; no data is served either way.
  - **#606:** an unexpected-`capability` refusal echoes a head+tail slice of the secret in the served pydantic error.
  - Harness gaps are not new findings (lead annotated #386): 107 in-image-only reds, ALL image-environment (E1 /app-vs-/workspace 87 · E2 podman/rsync/jq 18 · E3 quadlets 2).
- **Holes (unexercised, NOT passes):**
  - the 64b migrate contract (its module fails to collect in-image; 30 of the audit's 530 reds therefore NOT COLLECTED);
  - governed memory/comms CONTENT on real data (DENY in no-auth mode by design until packet 65);
  - `lore_diff` / `snapshot_entry` (4 GiB `/import` cap, F2).
- **Deviations:**
  - F1-B: lowercase DB-name override via `conform66/restore_lowercase.py` (lead #19145; #525);
  - F2-B: restore = 27 tables minus `snapshot_entry`, because `--full` exceeds `/import`'s 4 GiB cap (lead #19147);
  - suite by hand (`-n 12`, junit), because conformance_run.sh hardcodes `-n auto`;
  - `surrealdb.__version__` does not exist in 3.0.0, so I used dist metadata;
  - my #600 duplicated #525 (resolved as a duplicate).
- **Packages considered:** none. No product mechanism specified; instruments only (listed in §Instruments).
- **Odoo-20 portability:** n/a, no Odoo seam touched.
- **Reuse ledger:** 0 new product symbols. The instruments' DRY rows are in §DRY ledger.
- **Graded:** 88b06be · HEAD-at-report: 88b06be · SAME (TREE 6cd9b153…e699, DIRTY_FILES=0).
- **Decisions needed:**
  1. rotate the prod store password? (incident);
  2. archive `conform66/`, since it holds the instruments the claims rest on;
  3. route #604/#605/#606 (packet 65?);
  4. `/backups/lore/lore-prod-20261108T225620Z.surql` (8.65 GB) is kept per the brief. Keep or prune?
- **Receipt pointers:** §Step 2 (provenance) · §Step 3 (suite + diff) · §Step 4/4b/4c (export + restores) · §Step 5 (bootstrap + DDL + tool table) · §Step 6 (Q2) · §Teardown · §Gate receipts.

**Capability check:**
- One brief demand was unmet as written: step 5's "lore config pointing at the minted DB". The driver's name is not a legal `SlugStr` (F1), resolved by ruling.
- `--full` was unmeetable at today's size (F2), resolved by ruling.
- `surrealdb.__version__` is absent in 3.0.0.
- Everything else was satisfiable.

## Routing table (written before first substantive step, 2026-11-08)
| step | tier | who | reason |
|---|---|---|---|
| 1 ground truth (HEAD, tree_id, Containerfile, uv.lock) | 1 | self, one parallel batch | 4 small reads on critical path, read in full anyway |
| 2 image build | 1 | self, background Bash | one command; its id/provenance feed every later step |
| 3 in-image suite run | 1 | haiku-runner (exact command) | test run; full-suite-sized log stays out of my context |
| 3b both-ways diff vs junit_1.xml | 1 | self (script I write, output = two id lists) | mechanical, output small; classification of new reds = tier 3, self |
| 4 prod export | 3 | self | touches PRODUCTION + secrets; an error here is not catchable downstream |
| 4b restore into minted DB | 1 | self | one committed script, critical path |
| 5 store bootstrap + tool exercise on copy | 3 | self | judgment on served text, R34 integrity, cursor-walk semantics |
| 6 Q2 grep counts | 1 | self, one batch | 2 patterns over ≤4 logs, output small |
| 7 teardown + proofs | 1 | self | destructive-adjacent; must not touch existing containers/tags |

## ⚠ INCIDENT — production secret exposed (2026-11-08, this agent, HARD RULE "Secrets" breached by accident)
- **What:** to learn the export CLI's flags I ran `podman exec lore-surreal /surreal export --help`. SurrealDB's CLI (clap)
  renders each env-backed option as `[env: NAME=<value>]`, so the help text printed the **production `SURREAL_PASS` value**
  (and `SURREAL_USER`) into my tool output. It is now in this agent's session transcript
  (session f1186cdc-89c1-4273-97b3-1391d099bcd4). I have not copied it into any file, report, finding or message.
- **Severity / blast radius:** the value lives in the local Claude Code transcript on this host; lore is pre-production
  and loopback-only (:18500 bound to 127.0.0.1). Still a breach of the brief's hard rule.
- **Recommendation (operator decision):** rotate the lore-surreal root password (`lore.env` → both quadlets' env-file +
  lore-lore recreate) and/or purge that transcript.
- **Class (for the ledger):** ANY `surreal <subcommand> --help` run inside a store container whose env carries
  `SURREAL_PASS` prints the secret. Askable form: *"does this help/usage/debug command echo its environment?"*
- **Did it change what I did next:** no. The export still used the CLI's env fallback, so no credential appears on any
  command line or in any log I wrote.

## Step 1 — ground truth (measured 2026-11-08 ~22:53Z)
- `tree_id.sh /home/ejprice/PycharmProjects/lore`: `HEAD=88b06be6d80a2088df8a34f3ca43687a9e441694` · `DIRTY_FILES=0` ·
  `TREE=6cd9b1537a37bd5ec77617814e2e0bb93fd53dfc9a7e76736555c54e5447e699`.
- `origin/feat/surreal-unification` = `c658781`, an ancestor of HEAD: local is **722 commits ahead, 0 behind** (unpushed). Not a
  staleness problem for this run; flagged so the lead knows the graded commit exists only locally.
- Containerfile installs via `uv sync --locked --all-packages` from the copied `uv.lock`; `uv.lock` pins `surrealdb` `3.0.0`;
  `loremaster/pyproject.toml` declares `surrealdb==3.0.0`.

## Step 2 — build + provenance
- `podman build --build-arg LORE_VERSION="$(git describe --tags --always --dirty)" -t localhost/lore:sdk3-conform-88b06be -f Containerfile .`
  → `EXIT=0`; log `conform66/build.log` (tree_id header = the TREE above).
- **Image id `78cbb019a39dc0235fe44c5e81a3183e46bb28c9cf90c49c304d56ab7a059f11`**, created 2026-11-08 22:54:43Z,
  `LORE_VERSION=pkt03b-tainted-corpus-1501-g88b06be` (not `-dirty`).
- In-image (`conform66/provenance_image.txt`):
  - `importlib.metadata.version("surrealdb") = 3.0.0` from `/app/.venv/lib/python3.14/site-packages/surrealdb/__init__.py`.
  - **Brief-premise deviation:** `surrealdb.__version__` does NOT exist in 3.0.0 (`AttributeError` from the package's module
    `__getattr__`). I used the distribution metadata instead. A reading that wanted the attribute specifically would have to
    record "absent".
  - `loremaster` → `/app/loremaster/loremaster/__init__.py`; `loresigil` → `/app/loresigil/…`; `lorescribe` → `/app/lorescribe/…`;
    `lorerunes` → `/app/lorerunes/…`. All four are baked (`/app`), none come from `/workspace`.

## Step 4 — prod export (the ONE read of :18500)
- Command (credentials from the container's OWN env via the CLI's `SURREAL_USER`/`SURREAL_PASS` env fallback; none on the
  command line): `podman exec lore-surreal /surreal export --endpoint http://127.0.0.1:18500 --namespace lore --database lore - > <dump> 2> conform66/export.stderr`
- `EXIT=0`, 2026-11-08T22:56:20Z → 23:01:53Z (5m33.8s); engine line `The SurrealQL file was exported successfully` present.
- **Dump: `/backups/lore/lore-prod-20261108T225620Z.surql`**: 8,651,619,355 bytes apparent (2.7 G on disk; the ZFS dataset
  compresses). It holds **28 `-- TABLE:` sections**: agent answers_to audit blocks brief brief_counter briefed chunk code_node
  command file file_text finding finding_counter keep member_of memory message meta name principal principal_key refers
  snapshot snapshot_entry task to trace. It also holds 2 export log lines, both matched by `restore_prod_dump.EXPORT_LOG_LINE_PATTERN`.
- Left in /backups/lore (the house location), so per the brief it is NOT torn down. Its size is a disk-budget item for the operator.

## ⚠ FORK F1 — the restore driver's minted DB name cannot be addressed by a lore config (raised 2026-11-08 ~23:10Z)
- **Fact, by construction (image 78cbb019a39d):** `SurrealConfig(database="test_dump_20261108T230000Z_<32 hex>")` raises
  `ValidationError … String should match pattern '^[a-z0-9][a-z0-9_]*$'` (`loremaster.config.SLUG_PATTERN`). The control
  `test_dump_20261108t230000z_<32 hex>` is ACCEPTED. `scripts/restore_prod_dump.py` mints `test_dump_%Y%m%dT%H%M%SZ_<hex>`
  (`DATABASE_STAMP_FORMAT` / `DATABASE_NAME_PATTERN`), so **brief step 5 as written (a lore config pointing at the minted DB) is
  not satisfiable**. lore has no other config door to a database name (`effective_surreal_database` = `surreal.database` or the
  slug, both `SlugStr`).
- **Why nobody hit it before:** the driver's only consumer so far is the S2 test leg, which connects through the test harness
  (no `LoreConfig`). It is a seam between two instruments, not a production defect. Still, a restore-the-prod-dump-and-boot-lore
  rehearsal (packet 65's dress rehearsal) needs exactly this path.
- **Options:**
  - **A (brief-literal):** STOP step 5, record it, and do steps 3/4/6/7.
  - **B (recommended):** run the SAME driver as a library (`uv run`, repo venv), overriding only `DATABASE_STAMP_FORMAT` and
    `DATABASE_NAME_PATTERN` to lowercase in-process. The repo file is not edited. It is still one `--full` import with all the
    driver's guarantees (constant :18000, verify, `[]`-only acceptance, declared-vs-read-back). Evidence that the override landed:
    the printed `LORE_PROD_DUMP_DB=` name is lowercase. The reap goes through the same patched driver. The artifact under test
    (the image) runs unmodified, with a valid config.
  - **C (rejected):** bypass config validation in the server (`model_construct`). That would test a config path production never takes.
- **RULED: B** (team-lead, lore_comms #19145, thread `q:conform66-fork-f1`, acked). Already ledgered as **#525**. My #600
  duplicated it (I filed before searching the ledger) and is resolved as a duplicate of #525 with this run's by-construction
  datum. Conditions, each receipted below: override only the two constants, in-process, from `conform66/restore_lowercase.py`;
  the repo file is untouched (git status); a lowercase minted name is the evidence the override landed; the reap goes through
  the same patched driver, proven by `INFO FOR NS`; the image runs unmodified with a valid config.
- Incident: lead acknowledged it and owns the operator escalation. Finding **#601** carries the class.

## Step 3 — the in-image suite (run 2026-11-08 22:56–23:11Z)
- **Command:** `conform66/run_suite.sh` (run by a haiku-runner; its `RAN:` line matched). It reproduces
  `skills/lore-deploy/scripts/conformance_run.sh` by hand, because that script hardcodes `-n auto` with no override. Deltas:
  `-n 12`, `--junitxml=/out/junit_inimage.xml` (scratch mount), `-rfE`, `podman --memory=16g --memory-swap=16g`, all under
  `flock /tmp/lore-full-suite.lock`. Mounts, `--network=host`, keep-id, env and **provenance gate FIRST** are verbatim.
  **Cap used: podman `--memory=16g --memory-swap=16g`.**
- **Provenance gate PASSED before pytest:** loremaster/loresigil/lorescribe/lorerunes → `/app/<member>/<member>/__init__.py`.
- **Receipt:** log `conform66/suite.log` · `HEAD=88b06be…` · `TREE=6cd9b153…e699` · `IMAGE_ID=78cbb019…` · **EXIT=1** ·
  count line **`601 failed, 13991 passed, 82 skipped, 3 xfailed, 41 warnings, 37 errors in 858.26s (0:14:18)`**.
  Failing ids: `conform66/inimage_failing_ids.txt` (605 distinct red node ids from the junit; failure OR error).
- **Both-ways diff vs the cold audit's junit at 672b6d6** (`audit66/junit_delta/junit_1.xml`: 14795 tests, 530 red), by
  `conform66/junit_diff.py`:
  - red in BOTH: **498**;
  - **red in-image, NOT in the 530: 107** (`conform66/diff_new_reds.json`, with full failure text);
  - **red in the 530, NOT red in-image: 32**. All 32 were **NOT COLLECTED** in-image, none passed: 30 are
    `test_findings_migrate_64b` (its module fails to import in-image, E1 below) and 2 are `test_reanchor_58_r4_state`
    parametrize ids. So **the 64b migrate contract is UNEXERCISED by the in-image run**: a hole in the conformance, not a pass;
  - collected only at the audit: 128; only in-image: 14. Path-derived parametrize ids differ, plus the uncollected 64b module.
- **Classification of the 107** (mechanical regex over the failure text, then the 2 leftovers read by hand). **No real product defect found:**
  | class | n | shape (verbatim heads) |
  |---|---|---|
  | **E1 mount/baked path split.** Tests derive the repo root from `loremaster.__file__` (=`/app`, which has no `scripts/ skills/ docs/ Containerfile lore.yaml`), or relate baked module paths to `/workspace` | **87** | `'/app/loremaster/loremaster/messages.py' is not in the subpath of '/workspace'` · `real repo config /app/lore.yaml is absent` · `GuardCannotSubstantiate: the runtime parse-guard is watching /app, but parse_production_trees … executes from /workspace/…` · `REACH no longer matches … declared-not-scanned … ['docs','scripts','skills']` · `FileNotFoundError: '/app/Containerfile'` / `'/app/scripts/restore_prod_dump.py'` · `include_scripts=True produced no scripts/ tree` · `ENV_READ_ALLOWLIST entries name no live site` · the `test_findings_migrate_64b` collection error (`test_memory_enforcement_63b_ia._rel`: `'/app/loremaster/loremaster/memory/local.py' is not in the subpath of '/workspace'`) and its 4 collection errors + the 1 importer `test_findings_scope_domain_64b` |
  | **E2 host binary absent from the slim image** (`podman`, `rsync`, `jq`: verified MISSING in-image; `git`, `flock` present) | **18** | `artifact pin needs podman on PATH` · `rsync: command not found` (scratch_copy) · idle-gate `expected NUDGE (exit 2), got 0` (11; the hook needs `jq`, gets an empty `teammate_name` and exits 0) |
  | **E3 host file absent** (`$HOME/.config/containers/systemd/spike-surreal.container`) | **2** | `restore_prod_dump.SelfTestFailure: … spike-surreal.container is missing` |
- **Is any of the 107 SDK-3?** No. 9 failure texts name an SDK/transport symbol. In all 9 the name sits inside a scan dump or
  test-id listing (`test_no_exact_type_check_on_surreal_store_error` ×2, `test_gated_ground` ×7), not a raise.
- **Flags for the lead (not findings against the product; scope is the operator's):**
  1. The conformance harness never opts these 107 out under `LORE_CONFORMANCE_IN_CONTAINER=1`, so the in-image result carries
     ~100 known-environmental reds and **hides the 64b migrate contract** behind a collection error. This is the #139
     instrument degrading quietly. Is it worth a finding/packet? (I did not file it: it is a harness-scope question.)
  2. The idle-gate hook **fails OPEN silently when `jq` is absent**: it exits 0, which reads as "report present". On the host
     jq exists, so this is latent only.

## Step 4b — restore attempt 1: `--full` is unsatisfiable at today's prod size (FORK F2, 2026-11-08 23:18Z)
- `uv run python conform66/restore_lowercase.py --dump /backups/lore/lore-prod-20261108T225620Z.surql --full`
  (under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`; log `conform66/restore.log`, TREE header = the
  graded TREE) → **EXIT=3** after 5m06s: `IMPORT REJECTED — /import answered HTTP 413: 'length limit exceeded'`; the driver
  reaped its own DB (`FAILED — reaped test_dump_20261108t231824z_88e3798eebc349248414d45c42ac3ec5`).
- **F1-B condition met here:** the minted name is lowercase, so the in-process override landed. `git status --porcelain` → 0 lines
  after the run; TREE unchanged.
- **Why:** vendor `surrealdb-docs:manage/instances/connect/via-http.mdx` (request-size table) gives `/import` a **4 GiB** cap.
  Per-table bytes in the dump (`conform66/dump_table_sizes.txt`, awk over the `-- TABLE:` sections): **snapshot_entry
  6,249,803,480** · chunk 2,263,312,281 · file_text 62,441,570 · all other 25 tables + preamble ≈ 78 MB. **One table alone
  exceeds the cap**, so no `--full` import of this store can succeed through the driver's single-POST design.
  The driver failed LOUD and cleaned up, so the instrument behaved honestly. But `--full` was "implemented but NOT exercised"
  (packet-64 note) and this is its first real exercise: it cannot work on today's prod size.
- **Options:**
  - **A (brief-literal):** STOP the restore item. Then step 5 has no copy either.
  - **B (recommended):** `--tables` = all 27 tables EXCEPT `snapshot_entry` (≈2.40 GB, under the cap). It keeps every governed
    table, `chunk` (lore_search), `file`/`code_node`/`snapshot` (boot/index state) and all ledgers. It drops only the index-SNAPSHOT
    entries, which back `lore_diff`, a tool not on the brief's list. `--tables` makes all 27 REQUIRED (all present).
  - **C:** the driver's default governed slice. Smaller, but no `chunk`, so `lore_search` reads nothing and boot may re-index.
- **RULED: B** (team-lead #19147, thread `q:conform66-fork-f2`, acked). The lead filed the 4 GiB `--full` cap for packet 65, and
  annotated **#386** (the pre-existing in-image harness gap, owned by packet 65) with this run's 107/32 numbers and the 64b
  collection hole. I filed neither. Caveats taken: don't wait on any boot re-index; ≤30 min per run; `lore_diff` out of scope.
- Ledger note: **#526** (wontfix, lead-63c-2) is an earlier sibling of #525 on the same name-mint seam.

## Step 4c — restore attempt 2 (F2-B): the prod COPY
- `uv run python conform66/restore_lowercase.py --dump /backups/lore/lore-prod-20261108T225620Z.surql --tables <27 tables, all but snapshot_entry>`
  (`conform66/restore2_tables.txt`; cgroup-capped; `timeout 1800`) → **EXIT=0**, 2026-11-08 23:20:32Z → 23:24:47Z (scan 70.9s,
  import 180.5s, read-back 3.2s); log `conform66/restore2.{log,stderr,stdout}`, TREE header = the graded TREE.
- **Minted DB: `test_dump_20261108t232143z_e9315481be354822af6772d0a78c1f87`** (namespace `lore_test`, :18000). It is lowercase,
  so the F1-B override landed. `git status --porcelain` after = 0 lines.
- Slice 2,401,815,688 B. **Declared == read-back on all 27 tables** (e.g. chunk 45,423 · refers 64,431 · name 41,619 ·
  answers_to 35,134 · code_node 17,567 · trace 9,187 · file 4,711 · to 1,550 · message 1,318 · snapshot 1,001 · briefed 696 ·
  agent 663 · finding 599 · memory 294 · task 234 · blocks 61 · brief 28; audit/command/keep/member_of/principal/principal_key = 0).
- **Dirtiness, measured by the driver:** agent / brief / finding / message / task are **pre-63 shape** (scope NONE on every row:
  663 / 28 / 599 / 1,318 / 234). memory has the governed shape in its DDL with **294/294 scope NONE**. Production at
  2026-11-08 22:56Z therefore carries the un-migrated legacy shape, which is exactly what a virgin test DB cannot show.

## Step 5 — lore's store path on the prod copy, from the image (2026-11-08 23:25–23:36Z)
- **Topology** (mirrors `lore_deploy.py`'s run args; deltas named): `podman run -d --name conform66-server --memory=16g --memory-swap=16g
  --network=host --userns=keep-id --user 1000:1000 -e HOME=/home/lore -v <repo>:/workspace:ro -v conform66/state:/home/lore/.local/state/lore
  -v ~/docker/mcp/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro -v conform66/lore-conform.yaml:/conform/lore.yaml:ro
  --env-file conform66/conform.env -e LORE_CONFIG=/conform/lore.yaml localhost/lore:sdk3-conform-88b06be` (the image's own CMD,
  `python -m loremaster.server`).
  - Config: `conform66/lore-conform.yaml` = repo lore.yaml with 4 deltas (diffed: `project.root` absolute; `surreal` → `ws://127.0.0.1:18000/rpc`,
    ns `lore_test`, db = the minted copy, `user_env/password_env` → `CONFORM_SURREAL_*`; server port 9266).
  - Env-file (0600): `LORE_TEI_KEY`, `ANTHROPIC_API_KEY`, and the TEST-store credentials under new names. **Prod `SURREAL_USER`/`SURREAL_PASS` never
    entered the container**, so it could not authenticate to :18500 even by mistake. Fresh state dir; never `~/.local/state/lore`.
  - **Tools were driven through the server's own HTTP MCP endpoint** (`http://127.0.0.1:9266/mcp`, streamable-HTTP, the baked `mcp` 1.27.2 client,
    from an ephemeral `conform66-probe*` container): `conform66/probe_tools.py`, `conform66/probe_tools2.py`.
- **Bootstrap outcome: BOOTED CLEAN, NO RE-INDEX.** `embed.probe.ok` 23:25:13Z → `Application startup complete` 23:28:38Z (~3.5 min).
  `reconcile.summary`: files_indexed 1 (`loremaster/tests/test_comms_tool.py`, 511 chunks, 187.7 s embed), files_skipped 1568, failed 0,
  purged 0; the 3 static tiers `index.tier.skip`. 0 WARN/ERROR lines at boot (`conform66/server.log`). The missing `snapshot_entry` (F2-B)
  triggered nothing at boot.
- **DDL convergence on the dirty store, MEASURED** (`conform66/probe_ddl.py` + `conform66/ddl_diff.py`; before = the dump's 266
  DEFINE/REMOVE lines, after = `INFO FOR DB`/`INFO FOR TABLE` post-boot, rendering-only `OVERWRITE`/`IF NOT EXISTS` normalised out;
  `conform66/ddl_diff.json`):
  - **257 identical · 9 CHANGED · 13 ADDED · 0 GONE.**
  - All 9 CHANGED are ASSERT drops on populated fields: agent.name/session/role, message.body/refs/refs.*/thread/task_id, to.ack_note.
    These are exactly the store ASSERTs 63b-ii-b / 63c-i-a moved into the writers (store reference §0a). **So `DEFINE FIELD OVERWRITE`
    migrated a long-lived store; #107 did not recur.**
  - The 13 ADDED: scope/owner_agent/owner_principal on agent + message, capability_hash/capability_expires_at on agent, and indexes
    agent_scope, agent_owner_principal, agent_capability_hash, message_scope, message_owner_principal.
  - **Cross-check:** the post-boot set of tables carrying `scope` = {agent, memory, message} = `loremaster.governed.ddl_governed_tables()`
    in the image, exactly. brief/finding/task are the package's declared `PENDING_GOVERNED_TABLES`.
  - DATA did not converge, as store reference §1.4 says it must not: `scope IS NONE` still = rows on agent 663, brief 28, finding 599,
    memory 294, message 1318, task 234. That is the migrate verb's job at the packet-65 cutover; boot does not backfill.
- **R34 integrity:** `store-integrity fault` → **0** across server.log, both probe logs and both call journals. No refusal on real data.

| tool (served over MCP) | served head (verbatim, truncated) | latency | verdict |
|---|---|---|---|
| lore_tasks rollup (tokenless, walk) | `rollup since 1970-01-01T00:00:00.000000000Z` / `tasks transitioned (showing 20 of 162 — the next cursor is the earliest resume point of any leg, so rows above it in any leg, this one included, are served again next call: dedupe by task id or finding number; …` | p50 0.069 s, max 0.31 s (33 calls) | **PASS on the ruled contract.** Full walk to exhaustion (`probe_tools2.py` COMPLETE_WALK): 32 pages, **0 skipped** (distinct served = epoch-declared leg totals: tasks **162/162**, findings **599/599**). **All 32 cursors nine-digit** (`2026-07-06T04:02:27.853111000Z` … `2026-11-08T22:53:35.706564000Z`), strictly increasing. ⚠ **The brief's literal "no re-served row" does NOT hold, by design:** 1116 rows served for 761 distinct. These re-serves are the bound every page names (R45 / RULING-16 S1; #590/#596/#598 already ledger its h3 wording). |
| lore_tasks rollup + `capability=` | `1 validation error for call[tasks] capability Unexpected keyword argument …` | 0.009 s | **FAIL → finding #604** (the render teaches `pass capability=`, the tool rejects it, and the dispatch never forwards it, so the message leg is unreachable over MCP) **+ #606** (the refusal echoes a head+tail slice of the capability secret) |
| lore_findings query (limit 5) | `- [#1 resolved] ```tests_for returns empty for helpers exercised only indirectly``` (id 877cbc44…, kind ```friction```, …` | 0.034 s | PASS |
| lore_findings get 525 | `- [#525 open] ```restore_prod_dump.py mints DB names (test_dump_<stamp with T/Z>_…) that LoreConfig.surreal.database's pattern … refuses``` …` | 0.010 s | PASS |
| lore_comms fleet | `fleet: 175 non-retired agents — 1 input_required, 111 active, 63 idle` / `session 63b-iib-20260911:` … | 0.094 s / 0.134 s | PASS (176 after my throwaway register on the COPY) |
| lore_comms register (throwaway `conform66-probe`, session `conform66-copy`, on the COPY only) | `registered conform66-probe (session conform66-copy, role ```conformance-probe```) — status active` | 0.037 s | PASS (capability minted; kept in memory, redacted in every artifact. One truncated slice escaped via #606, in `tools_calls2.jsonl`/`tools_probe2.log`; that copy DB is reaped) |
| lore_comms drain (peek) as existing `team-lead`, no capability | `the presented capability did not verify — register an owned agent first (`lore_comms action=register`) …` | 0.293 s | PASS (governance denies a borrowed identity, by design) |
| lore_comms drain (peek) with the minted capability | `'NoneType' object has no attribute 'subject'` | 0.066 s | **FAIL → finding #605** (no-auth mode: a valid capability crashes at `_verify_capability_owner`'s `access_token.subject` while a forged one gets the uniform deny, i.e. a validity oracle and an untaught error; no data served either way) |
| lore_recall, no capability / with capability | same two texts as drain | 0.213 s / 0.059 s | DENY by design without a transport token (governed memory is DENY until packet 65's posture flip; memory: packet 62/63 rulings). With the capability: **#605**. **Governed memory content was NOT exercised on real data**: unreachable in no-auth mode. |
| lore_search ×4 | `[SOURCE:loremaster/tests/test_sdk3_rollup_cursor_66b1.py:65] Key: fd68a87f-… class _CursorCtx(_RollupCtx): …` | **22.8 s**, 19.2 s, 18.5 s, 15.8 s | PASS (cited hits). The latency is pre-existing: prod's own `trace` history in the copy (SDK 2.0.0, n=798, 2026-08-11 → 11-08 22:05Z) gives lore_search **p50 23.2 s**, p90 64.0 s, p99 232 s (`conform66/probe_trace_latency.py`). No SDK-3 regression. |
| lore_diff | — | — | **OUT OF SCOPE** (lead ruling F2: needs `snapshot_entry`, which the 4 GiB `/import` cap kept out of the copy) |

- **Reading of "lore_comms fleet/drain (read-only identities)":** two readings. (i) Drain AS an existing identity without mutating it:
  done with `peek=True`; governance refused, correctly. (ii) Use an identity that only reads: done with a throwaway identity registered
  on the COPY, which is a write to the throwaway DB only. I did both. Nothing touched :18500.

## Step 6 — Q2 (R5 / R43; INDEX R-4/T3, R-5/T4)
| pattern | suite.log (step 3) | step 4–5 logs (server.log, probe logs ×2, call journals ×2, restore stderr ×2) |
|---|---|---|
| `TransportTimeoutError` | **0** | **0** |
| `SurrealOutcomeUnknownError` | **56 raw string hits, 0 raises**. All 56 are `E   <test-id>` lines naming parametrize ids (`…[plain-SurrealOutcomeUnknownError]`, `…[SurrealOutcomeUnknownError-row-landed]`) inside the 7 `test_gated_ground` failure dumps (an E1 environment red that prints its collector listing). Classified by script; 7/7 failure texts are id listings only. | **0** |
- Bound: a `-q` suite log carries failure text only, so a raise inside a PASSING test is invisible to this grep. The deliberate
  fault-injection tests are exactly those.
- **Slowest served call: `lore_search` 22.767 s** (first search after boot; steady state 15.8–19.2 s). It is at prod's own p50 (above).

## Step 7 — teardown (2026-11-08 ~23:40Z), each removal proven
| item | action | proof |
|---|---|---|
| `conform66-server` | `podman stop -t 20` + `podman rm` | rm EXIT=0. Every other `conform66-*` (prov, slugcheck, mcpcheck, bincheck, govcheck, ddlprobe, traceprobe, probe, probe2, nsprobe, suite) was `--rm`. `podman ps -a \| grep -c ^conform66` → **0**. lore-lore / lore-surreal / spike-surreal untouched and still listed. |
| minted copy DB `test_dump_20261108t232143z_e9315481be354822af6772d0a78c1f87` | `restore_lowercase.py --reap <name>` (the SAME patched driver, per lead F1 condition) | driver: `reaped … (absent from INFO FOR NS)`, EXIT=0 (`conform66/reap.log`, TREE header). Independent `INFO FOR NS` (`conform66/probe_ns.py`, `conform66/teardown_ns_proof.txt`): **`test_dump_20261108*` present: []**, `test_dump_*` (any date) 0. Positive control: 109 databases visible in `lore_test`. Attempt-1 DB `…t231824z_88e3…` was auto-reaped by the driver on its own failure and is also absent. |
| image `localhost/lore:sdk3-conform-88b06be` | `podman rmi` | `Untagged … Deleted: 78cbb019a39d…` (+14 own layers), EXIT=0; `podman image exists` → absent; id 78cbb019 → absent |
| `localhost/lore:latest` | never touched | **before `4312207128bb161a4d7cb3ac961ccaf08e329761de7b3578f5b352370fbf413c` = after `4312207128bb161a4d7cb3ac961ccaf08e329761de7b3578f5b352370fbf413c` → IDENTICAL** |
| `conform66/conform.env` (TEI key, Anthropic key, test-store creds) | `shred -u` | `ls` → No such file |
| export file | `/backups/lore/lore-prod-20261108T225620Z.surql` (the house location) | **kept**, per the brief (only exports OUTSIDE /backups/lore are removed). I wrote none outside it. No driver temp `.surql` left in /tmp or /var/tmp (find, newer than the dump). |
| repo | nothing edited | `git status --porcelain` → 0 lines; `tree_id.sh`: HEAD=88b06be…, DIRTY_FILES=0, TREE=6cd9b153…e699 (= step 1). REPORT-*.md at the root untouched. |
| worktrees | none created | — |
- Left behind on purpose: `conform66/state/` (the conform server's fresh state dir, no secrets), the instruments and logs in `conform66/`,
  the idle-gate contract + `.nudged` marker under `/tmp/claude-idle-gate-lore/`, and the throwaway `conform66-probe` identity, which
  lived only in the reaped copy.

## Gate receipts
| gate | exact command | log | EXIT | count line | TREE |
|---|---|---|---|---|---|
| image build | `podman build --build-arg LORE_VERSION=… -t localhost/lore:sdk3-conform-88b06be -f Containerfile .` | `conform66/build.log` | 0 | `Successfully tagged …` / id 78cbb019… | 6cd9b153…e699 |
| in-image suite | `bash conform66/run_suite.sh` (flock + podman 16g cap + provenance gate first + `-n 12`) | `conform66/suite.log` (+ `junit_inimage.xml`) | **1** | `601 failed, 13991 passed, 82 skipped, 3 xfailed, 41 warnings, 37 errors in 858.26s (0:14:18)` | 6cd9b153…e699 |
| prod export | `podman exec lore-surreal /surreal export --endpoint http://127.0.0.1:18500 --namespace lore --database lore - > <dump>` | `conform66/export.log` | 0 | `The SurrealQL file was exported successfully`; 28 tables | n/a (no tree) |
| restore 1 (`--full`) | `uv run python conform66/restore_lowercase.py --dump <dump> --full` | `conform66/restore.log` | 3 | `IMPORT REJECTED — HTTP 413` | 6cd9b153…e699 |
| restore 2 (F2-B) | `… restore_lowercase.py --dump <dump> --tables <restore2_tables.txt>` | `conform66/restore2.log` | 0 | declared == read-back, 27/27 tables | 6cd9b153…e699 |
| reap | `… restore_lowercase.py --reap <minted>` | `conform66/reap.log` | 0 | `reaped … (absent from INFO FOR NS)` | 6cd9b153…e699 |

## Instruments (brief-base §1: these are the instruments the claims rest on)
All are in the lead-named `conform66/`: `run_suite.sh`, `junit_diff.py`, `restore_lowercase.py`, `probe_tools.py`, `probe_tools2.py`,
`probe_ddl.py`, `ddl_diff.py`, `probe_trace_latency.py`, `probe_ns.py`, plus the lore-conform config template. ⚠ They survive only if
`conform66/` is archived (decision 2). None is committed, because the repo is not my writable set.

## DRY ledger (instrument symbols only; no product code written)
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `restore_lowercase.py` (wrapper) | `scripts/restore_prod_dump.py` (the brief's tool) | the driver; constants read at call time | **REUSED** `restore_prod_dump.main` (only two module constants overridden, per lead ruling) |
| `probe_tools*.py` MCP client | the image's `mcp` 1.27.2 (`mcp.client.streamable_http.streamablehttp_client`) | the package client | **REUSED** (package); rollup row/cursor parsers HAND-ROLLED over the served text (the contract under test IS the text) |
| `probe_ddl.py` / `probe_ns.py` / `probe_trace_latency.py` | `loremaster.store` driver vs the raw SDK | lore's driver would itself be the code under test | HAND-ROLLED on the raw `surrealdb` SDK on purpose (an independent reader) |

## Routing / fan-out
Routing table at the top (written before step 1). Test run: 1 `haiku-runner` (its `RAN:` matched; I read the count line from the log).
Everything else ran inline, as the table says. **Fan-out: haiku 1 · sonnet 0 · peak 1.**
Lore usage: lore_search/lore_read/lore_recall/lore_findings first. Grep fallbacks, SAID: `ensure_ready` (lore_search's top hit was an
unrelated 03b report span), plus non-symbol textual seams (`next cursor` render text, `SLUG_PATTERN`, `DATABASE_STAMP_FORMAT`, log strings).
No new friction filed for the ensure_ready miss: it is the known lore_search recall class (#490/#550).
