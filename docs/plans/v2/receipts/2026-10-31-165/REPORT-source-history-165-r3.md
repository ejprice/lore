brief-base v23 read

## SUMMARY (measured 2026-10-31 at `acbce73`)
- **State:** done-with-deviations.
- **Deviations:**
  - D1: my first lore_search returned an inline chunk of `REPORT-source-history-165-r2.md:50-58` (lore indexes repo-root REPORTs). I never opened the file. Every claim below is re-derived from primary sources: git, podman, findings, lore memory, files.
  - D2: I added out-of-sweep surfaces to Q5: MEMORY.md, the lore memory gotcha, the `~/.claude` prose and `~/.claude/plans`.
- **Packages considered:** none, no mechanism specified · **Odoo-20 portability:** n/a, no Odoo seam touched · **Reuse ledger:** none.
- **Graded:** `acbce73` · HEAD-at-report: `acbce73` · SAME (local is 546 ahead and 0 behind `origin/feat/surreal-unification` after a fetch).
- **Q1 origin:** `/source` is present from the root commit `407d7f7` (2026-05-31), only as prose: Containerfile run recipe, docstrings in `snapshot.py`, `indexer.py`, `test_source.py`. In the same commit the server reads `_DEFAULT_SNAPSHOT_ROOT = Path.home()/"docker"/"mcp"/"lore-snapshot"` (`server.py`, `index/cli.py`). Production Python has never held a quoted `"/source"` literal. The only `*.py` commit touching one is `407d7f7`, and that hit is the `test_config.py` fixture. **Verdict: an aspirational convention the code never implemented, not a contract the server drifted from.** HIGH. Pre-repo origin unknown; GUESS: borrowed from the `mcp-code` (odoo-code MCP) `/source/<tier>` layout.
- **Q2 ×2 shape:** two read-only binds of the same host dir: `~/docker/mcp/lore-snapshot:/source:ro` (vestigial) plus `~/docker/mcp/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro` (the one the server reads). MEDIUM:
  - **no receipt records the literal binds** (`:/source`, `lore-snapshot` and `/home/lore/docker` each have 0 hits over 848 receipt+INDEX files);
  - the shape is inferred from #186's 2026-07-25 recreate recipe, carried by verbatim-CreateCommand recreates, and matches the live `lore-lore` mounts.
- **Q3 dependents:** none.
  - Of 28 containers, only `lore-lore` mounts the lore snapshot at `/source`.
  - `lore-demand_intelligence` (exited) has no `/source` and no static roots.
  - `mcp-code` mounts `/source/*` from a different image and host dir, and is not created by this skill.
  - 39 `lore.yaml` files found: 37 are scratch copies, none with a container, so **no scratch dir is a live deployment**.
  - The `installed_modules_file: /source/installed.txt` value exists only in a test fixture. HIGH.
- **Q4 packet 19:** open DESIGN. It subsumes #165 into #166's one-toolchain redesign ("DISSOLVES #165") and never asks to keep `/source`. #165's option A replaces `/source` with the server path; #186 and the lore memory call `/source` vestigial ("shape-parity only").
- **Q5:** 79 tracked hits plus 8 out-of-sweep rows = 87. LIVE 24 · HIST 20 · OTHER 7 · UNRELATED 36 (2 key-gap rows, see §Q5). Sonnet draft sampled 14/79 (3 Containerfile, 3 INDEX Log, 2 INDEX pre-Log, skill ×2, receipts ×2, packet 65, test fixture): 11 exact, 1 column error (row 32), 2 key-gap.
- **Decisions needed:** D-1, the INDEX pre-Log key gap (§Q5); also the Q4 fork (ship option A before the packet-19 design?) · **Pointers:** §Q1–§Q5; W=`/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/20263ea7-8306-4f06-bdb7-e8ebae312b13/scratchpad/r3/history/` (`git.txt`, `deploy.txt`, `sweep.txt`, `rcpt-*.txt`, `verdicts-draft.md`); findings #165 #166 #186, new #550.
- **VERDICT: can the skill drop `/source` now? ONLY-IF**, on HISTORY and EXTERNAL-DEPENDENT grounds, all three in the same change:
  - (a) it adds the `$HOME` snapshot bind (the brief's premise);
  - (b) the sibling code trace confirms zero current readers (my history leg finds none ever);
  - (c) it updates the live prose that pins `/source:ro ×2` as the known-good shape, or packet 65 runbook step 2's diff will flag a correct container as deviant. Sites: `65-hosted-write-joint-cutover.md:130`, the lore memory gotcha, MEMORY.md:15-16, INDEX.md:581.
  - Confidence: HIGH on history and dependents; MEDIUM overall, because the code-reader leg is the sibling's.

## Routing table (written at spawn, before tier-3 reads)

| step | tier | who | reason |
|---|---|---|---|
| 1 prose sweep `/source` over git ls-files | 1 | haiku-worker | brief-routed; literal awk sweep + coverage |
| 2 git archaeology (-S '/source', _DEFAULT_SNAPSHOT_ROOT, LORE_SNAPSHOT) | 1 | haiku-worker | brief-routed |
| 3 receipts search (5 patterns, excl. 2026-10-31-165) | 1 | haiku-worker | brief-routed |
| 4 deployment inventory (podman ps/inspect, lore.yaml find) | 1 | haiku-worker | brief-routed; no env printing |
| 5 prose verdict draft | 2 | Sonnet general-purpose | brief-routed; after step 1 landed; I sampled 14 rows incl. 5 INDEX.md |
| 6 origin/intent, ×2 shape, packet 19, final verdict | 3 | me | brief-routed; verdicts depend on state elsewhere (server default, skill launch code, HOME env) |
| 6a (added) out-of-sweep prose: `~/.claude/**` + MEMORY.md + `~/.claude/plans` + lore memory | inline | me | one parallel batch of 3 small awk sweeps (24 + 60 files, output < 15 lines), read in full; on critical path |
| 6b (added) `installed_modules_file` literal check | inline | me | 1 command, 2 hits; config key = grep-honest seam; lore_search miss filed #550 |

Capability check: every tool the brief demands is present. No deadline in the brief, so none binds.
Fan-out: haiku 4 · sonnet 1 · peak 4. Test runs: none (read-only investigation; no test command in scope).

Haiku output checks (`RAN`-equivalent, workers not runners):
- Step 1: `files_opened=1618 hits=79` vs `git ls-files | wc -l` = 1620. The 2-file gap is the two empty tracked files (`loremaster/loremaster/index/__init__.py`, `lorescribe/tests/__init__.py`), measured by `test -s`.
- Step 3: each pattern opened 848 files (FILESET_SIZE 848); hits CreateCommand 12, `podman run` 14, the others 0. No output row is prefixed with the excluded dir.
- Step 4: 28 containers checked.

## Q1 — origin and intent of `/source`

**History (git.txt list B, `407d7f7` with `git grep` at that sha):**
- The repo has one root, `407d7f7` (2026-05-31, "Initial public release"). `/source` arrives there fully formed. Pre-repo history is not in git. `~/.claude/plans/` (60 files) holds no lore `/source` design; its only `/source` hits are odoo-code MCP plans (`mcp-project-docs-odoo-custom-tdd-light.md:21,30`). Hence the GUESS in the summary.
- At `407d7f7`, the prose says `/source`:
  - `Containerfile` (header line 8, user comment, run recipe `[ -v <snapshot>:/source:ro ]`, annotated `static-tier snapshot dir (~/docker/mcp/lore-snapshot)`);
  - `source/snapshot.py` module docstring ("the server bind-mounts that dir `:ro` at `/source`", citing "plan AMENDMENT 1 / D8", a pre-repo plan);
  - `index/indexer.py` and `tests/test_source.py` docstrings.
- At `407d7f7`, the code reads `_DEFAULT_SNAPSHOT_ROOT = Path.home() / "docker" / "mcp" / "lore-snapshot"`, in both `server.py` (passed as `snapshot_root=`) and `index/cli.py` (the indexer default).
- The Containerfile recipe sets `-e HOME=/home/lore`, so in-container that resolves to `/home/lore/docker/mcp/lore-snapshot`, never `/source`.
- `git log -S'LORE_SNAPSHOT'` is empty: no env override ever existed. That is #165's "option B", never built.
- `git log -G'["\']/source' -- '*.py'` returns only `407d7f7`. The only quoted `/source` in Python at that sha is the `test_config.py` fixture `"/source/installed.txt"`.

**Did the server ever read it?** No, as far as the history goes (HIGH). `_DEFAULT_SNAPSHOT_ROOT` changed in 4 later commits (`001f632`, `3552285`, `497bcaf`, `130fa16`). None introduced a `/source` path: list A's code commits all fall in `407d7f7`…`d081bae` (skill adoption on 2026-06-02 and the stale-image check). I did not open those 4 diffs line by line; that is the sibling's current-code leg.

**Contract or leftover?** Neither cleanly. It is an **aspirational convention, documented and never implemented**:
- The docs described a `/source` contract the code never had.
- The skill (adopted into the repo at `d0637ed` 2026-06-02, symlinked from `~/.claude/skills/lore-deploy`) implemented the docs, not the code.
- That disagreement was latent until the first static-tier deploy, on 2026-07-22 (#165).
- Same-file precedent: the Containerfile's state-dir comment records that "the old /state mount was a dead path the server never reads". That is the same drift class, already fixed for the state dir and never for the snapshot.

## Q2 — the "`/source:ro` ×2" shape (INDEX.md Log, 2026-08-03 04b-2 entries)

- INDEX.md:1747-1748 (rollback receipts) and :1752 (deployed) say the recreate was "the outgoing container's captured `CreateCommand` verbatim", with the shape `/source:ro ×2`. The flag list carries no paths.
- **No receipt holds the literal binds.** Over 848 files (receipts minus `2026-10-31-165/`, plus INDEX.md): `:/source` 0 hits, `lore-snapshot` 0, `/home/lore/docker` 0 (step-3 coverage lines). The wave-C deploy receipt (`receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md` §R2-12) records "ran the captured CreateCommand verbatim", again without paths.
- **Two readings of "×2":**
  - (i) both binds have destinations under `/source`;
  - (ii) two `:ro` binds of the snapshot dir, one at `/source` and one at the server path.

  I pick (ii), MEDIUM. Evidence chain:
  1. #186 body (2026-07-25) records that recreate with both lines: `-v ~/docker/mcp/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro` and `-v ~/docker/mcp/lore-snapshot:/source:ro`, "kept only for shape-parity".
  2. The 04b-2 design sidecar's precondition 3 (`receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md:115-117`) defines known-good as "the snapshot mounted at the path the server READS, never `/source`". Reading (i) would violate it, and that deploy booted clean.
  3. The live `lore-lore` mounts on 2026-10-31: `/home/ejprice/docker/mcp/lore-snapshot->/source` and `->/home/lore/docker/mcp/lore-snapshot` (deploy.txt §2).
- Caveat: that live container was itself hand-recreated on 2026-10-31 (the #165 annotation "kept /source too"), so it corroborates the recipe, not the 2026-08-03 container.
- The same "×2" phrase is LIVE in `65-hosted-write-joint-cutover.md:130` as a diff target, which is condition (c) of the verdict.

## Q3 — other dependents of `/source`

From deploy.txt (podman `ps`/`inspect`, read-only):

| container | status | `/source` binds | depends on the skill's `/source`? |
|---|---|---|---|
| `lore-lore` | Up | `~/docker/mcp/lore-snapshot` → `/source` (ro) **and** → `/home/lore/docker/mcp/lore-snapshot` (ro) | no reader (Q1); the second bind carries the load |
| `lore-demand_intelligence` | Exited | none (`/workspace` + state only); its `lore.yaml` has `watch_static_lines=0` and 0 `/source` hits | no |
| `lore-surreal` | Up | none (store) | no |
| `mcp-code` | Up | 7 binds into `/source/{odoo-custom,addons,apt-packages,enterprise,odoo,pip-packages,stdlib}` from `~/docker/mcp/source-snapshot/*` and the odoo-custom tree | **no**: a different image (`localhost/mcp-code:latest`), not launched by `lore_deploy.py`; a namesake path only |
| the other 24 | — | no `/source*` destination | no |

- **Scratch dirs.** 39 `lore.yaml` files under `~` (maxdepth 5):
  - 1 is the repo itself;
  - 1 is `pp-odoo/demand_intelligence` (slug `demand_intelligence`);
  - 37 are scratch/adversary copies (`~/scratch/*`, `~/adv39-*`, `~/*-scratch*`, …), each its own git toplevel, all slug `lore` with 3 `watch: static` lines (copies of the repo config).
  - The only `lore-*` containers are the three above. **No scratch dir is a live deployment.** A scratch copy started via `lore-deploy start` would be named `lore-<dirname>` and would appear in `podman ps -a`; none does.
- **Config dependents:** `installed_modules_file` appears in exactly 2 tracked lines, both in `loremaster/tests/test_config.py` (`git grep`; lore_search missed it, filed as #550). It is an opaque-extension passthrough fixture, not a reader.
- The ledger agrees with the measurements: #165 ("`/source` is vestigial — nothing reads it"), #186 ("nothing reads it"), and the lore memory gotcha ("The `/source` line is vestigial").

## Q4 — packet 19 (`docs/plans/v2/19-lore-deploy-rework.md`, findings #165/#166/#186)

- **Status:** INDEX.md:373 says "open — REDESIGNATED 2026-07-22; urgency ↑ 2026-07-25 (#186)". The design doc it owes (`docs/design/2026-07-XX-deploy-architecture.md`) does not exist (`ls docs/design | awk index "deploy"` returned nothing). So there is no ruling yet.
- **Stance:** packet 19 frames #165 as a symptom. Its fix is #166's one-toolchain architecture: run the indexer in the container on the same mounts the server uses, which "DISSOLVES #165". Scope IN asks for "#165 dissolution stated as a design consequence with the verification receipt the build must produce (a static-tier deploy where indexer and server read the same mounts)", plus a store-keyed boot skip that could remove the snapshot mount for DB-served tiers entirely (#166 adjacent gap 2).
- **Nothing in packet 19 asks to keep `/source`.** Its two `/source` mentions (lines 15, 22) describe the bug.
- **#165** (acknowledged → packet 19): recommends option A, mounting at `{CONTAINER_HOME}/docker/mcp/lore-snapshot` *instead of* `/source`, and updating the `/source` docstrings and the mount-string test. It also names the owed invariant: a boot-level test that a static tier reconcile-SKIPS, because "the current test asserts the mount STRING, which is exactly the check that passed while the container crashed".
  - Its 2026-10-31 annotation records a third recurrence. It says option A "since 07-22 is still unshipped, which makes `start` a standing trap", and that the MEMORY.md landmine "did NOT stop the agent".
- **#186:** the recurrence receipt; "kept only for shape-parity".
- **Fork I'm surfacing, not settling:** shipping option A now (the cheap fix the brief is evaluating) is compatible with packet 19. The design would later remove the snapshot mount or re-home it, not restore `/source`. But packet 19's own exit says #165 resolves as a design consequence. Whether the operator wants the stop-gap ahead of the design is their call. The 3 recurrences are the cost receipt for waiting.

## Q5 — every prose location (per-row verdicts)

Key: the brief's (HISTORICAL-RECORD / LIVE-INSTRUCTION / UNRELATED / OTHER). The Sonnet draft (W/`verdicts-draft.md`) was sampled; my overrides are marked **[r3]**.

**Sample (14 rows):** I checked these against my own reads of the lines: 3, 4, 5, 22, 23, 24, 27, 28, 29, 32, 39, 63, 76, 77.
- 11 agree exactly.
- Row 32: the verdict is right (HIST), but describes-mount should be **N**. The line says "never `/source`".
- Rows 23 and 24 fall in a key gap (D-1 below).

**D-1 (key gap; decision for the lead):** INDEX.md pre-Log text (lines 269, 581) is not a class the key lists.
- Reading A: LIVE, because it is undated standing plan-of-record text that agents act on. Line 581 is a ⚠ standing warning "until packet 19 lands".
- Reading B: OTHER, per the strict key.
- I pick A for both and keep B written here. The verdict's condition (c) names 581 either way.

The full table follows, generated from the draft with overrides applied.

| # | file:line | verdict | describes-snapshot-mount? | reason |
|---|---|---|---|---|
| 1 | .claude/agents/package-scout.md:146 | UNRELATED | N | "signature/source" prose, not a mount |
| 2 | Containerfile:8 | LIVE-INSTRUCTION | Y | Containerfile header comment: read-only snapshot of static tiers at /source |
| 3 | Containerfile:102 | LIVE-INSTRUCTION | Y | Containerfile comment: ro bind mounts at /workspace and /source |
| 4 | Containerfile:167 | LIVE-INSTRUCTION | Y | Containerfile run-invocation comment: -v snapshot:/source:ro |
| 5 | Containerfile:186 | LIVE-INSTRUCTION | Y | Containerfile comment: -v snapshot:/source:ro, static-tier snapshot dir |
| 6 | EXTENDING.md:372 | UNRELATED | N | loremaster/source/snapshot.py module path, "single source of" prose |
| 7 | LORE_EXTERNAL_REVIEW.md:125 | UNRELATED | N | "fact/source confidence" prose |
| 8 | docs/design/2026-07-31-packet39-google-oauth.md:330 | OTHER | Y | dated docs/design doc (not receipts/packet/live class): #165 recreate re-mounts /source |
| 9 | docs/design/2026-08-01-google-auth-restart-runbook.md:87 | OTHER | Y | dated docs/design runbook (not a key class): #165 recreate re-mounts /source |
| 10 | docs/design/2026-08-14-packet47-ingest-entity-seam-design.md:629 | UNRELATED | N | field name source_book |
| 11 | docs/design/2026-08-28-packet63-retrofit-rulings.md:52 | UNRELATED | N | memory field list "labels/source" |
| 12 | docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md:151 | UNRELATED | N | "served/source prose" phrase |
| 13 | docs/plans/v2/03b-comms-message-surface.md:69 | HISTORICAL-RECORD | Y | packet 03b (INDEX row DONE+DEPLOYED): hand-rolled /source mount reapply |
| 14 | docs/plans/v2/10-d-weak-match-disarm.md:82 | HISTORICAL-RECORD | Y | packet 10-d (INDEX DONE+DEPLOYED): hand-rolled /source mount landmine |
| 15 | docs/plans/v2/10-d-weak-match-disarm.md:83 | HISTORICAL-RECORD | Y | packet 10-d (INDEX DONE+DEPLOYED): normal start re-mounts /source |
| 16 | docs/plans/v2/11c-index-boot-reconcile-honesty.md:80 | LIVE-INSTRUCTION | Y | packet 11c (INDEX open): hand-rolled /source mount cited as #165/#166 |
| 17 | docs/plans/v2/19-lore-deploy-rework.md:15 | LIVE-INSTRUCTION | Y | packet 19 (INDEX open): #165 /source-vs-snapshot mount bug |
| 18 | docs/plans/v2/19-lore-deploy-rework.md:22 | LIVE-INSTRUCTION | Y | packet 19 (INDEX open): /source snapshot-mount mismatch recurrence |
| 19 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:23 | OTHER | Y | dated RESUME doc, no INDEX packet row; hand-rolled /source mount landmine |
| 20 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:25 | OTHER | Y | dated RESUME doc, no INDEX packet row; start re-mounts /source |
| 21 | docs/plans/v2/65-hosted-write-joint-cutover.md:33 | LIVE-INSTRUCTION | Y | packet 65 (INDEX open): lore-lore hand-rolled /source mount |
| 22 | docs/plans/v2/65-hosted-write-joint-cutover.md:130 | LIVE-INSTRUCTION | Y | packet 65 (INDEX open): CreateCommand shape /source:ro x2 |
| 23 | docs/plans/v2/INDEX.md:269 | LIVE-INSTRUCTION | Y | INDEX.md pre-Log (line 269 < Log 602) prose on open packet 19; hand-rolled /source mount **[r3]** key-gap D-1; alt reading OTHER |
| 24 | docs/plans/v2/INDEX.md:581 | LIVE-INSTRUCTION | Y | INDEX.md pre-Log standing warning until packet 19 lands; hand-rolled /source mount **[r3]** key-gap D-1; alt reading OTHER |
| 25 | docs/plans/v2/INDEX.md:1055 | HISTORICAL-RECORD | Y | INDEX.md Log entry (after line 602): #165 /source-mount |
| 26 | docs/plans/v2/INDEX.md:1058 | HISTORICAL-RECORD | Y | INDEX.md Log entry: lore-lore on hand-rolled /source mount |
| 27 | docs/plans/v2/INDEX.md:1748 | HISTORICAL-RECORD | Y | INDEX.md Log entry: CreateCommand with /source:ro x2 |
| 28 | docs/plans/v2/INDEX.md:1752 | HISTORICAL-RECORD | Y | INDEX.md Log entry: #165 known-good /source shape |
| 29 | docs/plans/v2/INDEX.md:1785 | HISTORICAL-RECORD | Y | INDEX.md Log entry: #165 known-good /source shape |
| 30 | docs/plans/v2/MASTER-PLAN.md:283 | UNRELATED | N | search detail option "refs |
| 31 | docs/plans/v2/receipts/2026-07-28-packet11ib/REPORT-informant-fable-11ib.md:52 | UNRELATED | N | "tiers/sources included" prose |
| 32 | docs/plans/v2/receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md:117 | HISTORICAL-RECORD | N **[r3]** | receipt: snapshot mounted at server-read path, never /source — says the OPPOSITE (never /source) |
| 33 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:92 | UNRELATED | N | URL path /sources/dnd/... |
| 34 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:564 | UNRELATED | N | URL path /sources/dnd/... |
| 35 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:169 | UNRELATED | N | loremaster/source/local_directory.py module path |
| 36 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:448 | HISTORICAL-RECORD | Y | receipt: hand-rolled /source mount, not restart-durable |
| 37 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:609 | HISTORICAL-RECORD | Y | receipt: hand-rolled /source mount pending #165/#166 |
| 38 | docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:283 | HISTORICAL-RECORD | Y | receipt: hand-rolled /source mount, not restart-durable |
| 39 | docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:304 | HISTORICAL-RECORD | Y | receipt: no /source break, #165 held |
| 40 | docs/plans/v2/receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:733 | HISTORICAL-RECORD | Y | receipt: lore-lore hand-rolled mount, start re-mounts /source |
| 41 | docs/plans/v2/receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:734 | HISTORICAL-RECORD | Y | receipt: start re-mounts /source and re-breaks boot |
| 42 | docs/plans/v2/receipts/2026-08-08-packet05aiii/REPORT-contract-fix-05aiii.md:201 | UNRELATED | N | "read-only/source leg" test-scenario phrase |
| 43 | docs/plans/v2/receipts/2026-08-09-defect-class/REPORT-adversary-g.md:70 | UNRELATED | N | "AST/source pin" phrase |
| 44 | docs/plans/v2/receipts/2026-08-10-packet05aii/REPORT-adversary-05a-ii.md:432 | UNRELATED | N | "AST/source guard" phrase |
| 45 | docs/plans/v2/receipts/2026-08-12-packet06a/REPORT-coldaudit-honesty-06a.md:17 | HISTORICAL-RECORD | Y | receipt: lore-lore hand-rolled /source mount landmine (match beyond excerpt) |
| 46 | docs/plans/v2/receipts/2026-08-16-packet59/REPORT-lead-59.md:146 | HISTORICAL-RECORD | Y | receipt: lore-lore hand-rolled /source mount, not restart-durable |
| 47 | docs/plans/v2/receipts/2026-08-16-packet59/REPORT-sweep-59.md:319 | UNRELATED | N | "signature/source/" in doc-read sentence |
| 48 | docs/plans/v2/receipts/2026-08-17-packet07/DESIGN-sidecar-144-posture.md:115 | UNRELATED | N | "signature/source" prose |
| 49 | docs/plans/v2/receipts/2026-08-17-regression-fix/REPORT-regr-fixer.md:68 | UNRELATED | N | "scheme/source" prose |
| 50 | docs/plans/v2/receipts/2026-08-20-packet48/REPORT-build-48b.md:11 | UNRELATED | N | "signature/source" prose |
| 51 | docs/plans/v2/receipts/2026-08-20-packet48/REPORT-builder-48b.md:11 | UNRELATED | N | "signature/source" prose |
| 52 | docs/plans/v2/receipts/2026-08-24-packet62/REPORT-adversary-62w2.md:293 | UNRELATED | N | "package/source considered" table header |
| 53 | docs/plans/v2/receipts/2026-09-04-packet63b/REPORT-contract-63b-i-b.md:52 | UNRELATED | N | "labels/source/expires_at" field list |
| 54 | docs/plans/v2/receipts/2026-09-09-packet63b-ib/REPORT-lead-63b-s2.md:58 | HISTORICAL-RECORD | Y | receipt: do not start lore-lore, hand-rolled /source mount |
| 55 | docs/plans/v2/receipts/2026-09-12-packet63b-ii-b/REPORT-contract-63b-ii-b.md:98 | UNRELATED | N | "AST/source pin" phrase |
| 56 | docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:110 | UNRELATED | N | log JSON path loremaster/loremaster/source/__init__.py |
| 57 | docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:111 | UNRELATED | N | log JSON path .../source/local_directory.py |
| 58 | docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:112 | UNRELATED | N | log JSON path .../source/snapshot.py |
| 59 | docs/plans/v2/receipts/2026-10-04-531-536/REPORT-fix531.md:190 | UNRELATED | N | path loremaster/loremaster/source/local_directory.py |
| 60 | loremaster/loremaster/index/indexer.py:395 | LIVE-INSTRUCTION | Y | docstring: snapshot bind-mounted ro at /source in live server |
| 61 | loremaster/loremaster/source/snapshot.py:6 | LIVE-INSTRUCTION | Y | module docstring: server bind-mounts snapshot dir ro at /source |
| 62 | loremaster/loremaster/source/snapshot.py:70 | LIVE-INSTRUCTION | Y | docstring: snapshot served from bind-mounted ro at /source |
| 63 | loremaster/tests/test_config.py:96 | OTHER | N | **[r3]** only use of `installed_modules_file` in the repo (git grep, 2 lines); opaque-extension passthrough fixture, not a reader |
| 64 | loremaster/tests/test_config.py:305 | OTHER | N | **[r3]** only use of `installed_modules_file` in the repo (git grep, 2 lines); opaque-extension passthrough fixture, not a reader |
| 65 | loremaster/tests/test_mcp_server.py:1719 | UNRELATED | N | "auto/summary/source" enum values |
| 66 | loremaster/tests/test_memory_replay_fidelity_63b_ib.py:9 | UNRELATED | N | "labels/source/expires_at" field list |
| 67 | loremaster/tests/test_render_slot_inventory.py:168 | UNRELATED | N | "store/source-minted" phrase |
| 68 | loremaster/tests/test_search.py:2870 | UNRELATED | N | "summary/source/auto" chunk types |
| 69 | loremaster/tests/test_source.py:6 | LIVE-INSTRUCTION | Y | test module docstring: server bind-mounts snapshot dir ro at /source |
| 70 | lorescribe/tests/test_astroid_parse.py:828 | UNRELATED | N | "chunk_type/source's" phrase |
| 71 | loresigil/loresigil/data/voyage4_tokenizer.json:54621 | UNRELATED | N | tokenizer vocab entry "/source", data not mount |
| 72 | loresigil/loresigil/data/voyage4_tokenizer.json:96938 | UNRELATED | N | tokenizer vocab entry "/sources", data not mount |
| 73 | skills/lore-deploy/references/lifecycle.md:18 | LIVE-INSTRUCTION | Y | lore-deploy lifecycle.md: snapshot dir bind-mounted ro at /source |
| 74 | skills/lore-deploy/references/lifecycle.md:19 | LIVE-INSTRUCTION | Y | lore-deploy lifecycle.md: bare project needs no /source mount |
| 75 | skills/lore-deploy/references/lifecycle.md:146 | LIVE-INSTRUCTION | Y | lore-deploy lifecycle.md: run template -v snapshot:/source:ro |
| 76 | skills/lore-deploy/scripts/lore_deploy.py:662 | LIVE-INSTRUCTION | Y | lore_deploy.py docstring: adds /source snapshot bind when static root declared |
| 77 | skills/lore-deploy/scripts/lore_deploy.py:684 | OTHER | N | code line building -v snapshot:/source:ro arg, not prose |
| 78 | skills/lore-deploy/scripts/test_lore_deploy.py:39 | LIVE-INSTRUCTION | Y | test comment: no static roots, no /source mount |
| 79 | skills/lore-deploy/scripts/test_lore_deploy.py:219 | LIVE-INSTRUCTION | Y | test inline comment: no static roots, no /source mount |
| A1 | ~/.claude/projects/-home-ejprice-PycharmProjects-lore/memory/MEMORY.md:15 (untracked, auto-loaded) | LIVE-INSTRUCTION | Y | landmine: lore-lore on hand-rolled `/source` mount; do NOT `lore-deploy start` — false once option A ships |
| A2 | same file :16 | LIVE-INSTRUCTION | Y | "a normal start re-mounts `/source` and re-breaks boot" |
| A3 | lore memory, kind gotcha, "lore-lore's working podman run — the ONLY mount shape that boots" (served by lore_recall) | LIVE-INSTRUCTION | Y | recreate recipe includes the vestigial `/source:ro` line; states it is vestigial |
| A4 | finding #165 body (2026-07-22) | HISTORICAL-RECORD | Y | dated ledger row; mechanism + option A; open status, but body is dated |
| A5 | finding #186 body (2026-07-25) | HISTORICAL-RECORD | Y | dated recurrence receipt; "kept only for shape-parity" |
| A6 | ~/.claude/CLAUDE.md:102 | UNRELATED | N | "installed API/source" |
| A7 | ~/.claude/orchestration/receipts.md:230 | UNRELATED | N | "API/source" |
| A8 | ~/.claude/agents/package-scout.md:142 | UNRELATED | N | "signature/source" (global copy of tracked row 1) |

Out-of-sweep coverage: `~/.claude/CLAUDE.md` + `~/.claude/orchestration/*.md` + `~/.claude/agents/*.md` + project MEMORY files = 24 files opened, 5 hits (A1, A2, A6–A8). `~/.claude/plans/**/*.md` = 60 files opened, 6 hits, all UNRELATED to lore (odoo-code MCP plan `mcp-project-docs-odoo-custom-tdd-light.md:21,30` = the mcp-code container's `/source/*`; `okay-then-i-need-mossy-nygaard.md:57` = mcp-code's source-snapshot; 3 dndlorescraper `/sources`/`source_page` hits). `~/.claude/skills/lore-deploy` is a symlink into the repo, so its tracked rows above ARE the loaded skill.

**Tally (87 rows = 79 tracked + 8 out-of-sweep):** LIVE-INSTRUCTION 24 · HISTORICAL-RECORD 20 · OTHER 7 · UNRELATED 36. Check: 24+20+7+36 = 87.

**LIVE-INSTRUCTION rows that a /source drop must update in the same change** (this is verdict condition (c), listed individually):
- Containerfile:8, :102, :167, :186: header, user comment, run recipe and its annotation.
- skills/lore-deploy/references/lifecycle.md:18, :19, :146.
- lore_deploy.py:662 (docstring); :684 is the code line itself (OTHER).
- test_lore_deploy.py:39, :219 (comments); per #165, the mount-STRING test also needs updating (the sibling's code leg).
- loremaster docstrings: snapshot.py:6, :70; indexer.py:395; test_source.py:6.
- open packet docs: 11c:80, 19:15, 19:22, 65:33 and **65:130 (the `/source:ro ×2` diff target, which would false-flag a corrected container)**.
- INDEX.md:269, :581 (D-1).
- out of repo: MEMORY.md:15-16 and the lore memory gotcha A3 (the recipe agents copy).

**OTHER rows:**
- 8, 9: dated docs/design (39 OAuth design, the restart runbook). They state "#165 open, recreate re-mounts /source"; that becomes stale once fixed, but they are dated.
- 19, 20: the dated 2026-08-01 RESUME doc.
- 63, 64: test fixture.
- 77: the code line.

## Residuals / flags
- **R1:** `git log -S'/source'` list A (44 commits) is dominated by docs/receipts archive moves. I did not adjudicate each of the 44. I read only the origin commit and the code-path commits (`407d7f7`, `d0637ed`, `d081bae`, `744734c`). That is enough for Q1 (no Python `/source` literal ever existed; `-G` check) but is not a per-commit audit.
- **R2:** INDEX.md:581's warning and MEMORY.md's landmine have already failed once as controls (#165 annotation, 2026-10-31: the agent ran `start` anyway). Text warnings are not a guard; #165's owed boot-level invariant is.
- **R3:** `lore-demand_intelligence` shows "Exited (0) 292 years ago" (a podman timestamp artefact). It is not running; I noted it and did not investigate.
- **R4 (friction filed, #550):** lore_search missed a literal config key. Separately, repo-root REPORT-*.md files are indexed, which is how D1 happened.
