brief-base v22 read
brief project v7 read

# REPORT — source-history-165-r2 · history and external dependents of lore's `/source` bind (finding #165)

## SUMMARY (measured 2026-10-31 at HEAD `acbce73`)
- **State:** done-with-deviations. **Graded:** acbce73 · HEAD-at-report: acbce73 · SAME.
- **Deviation 1 (independence breach, disclosed):** one `lore_search` call returned a chunk of the forbidden prior run (`docs/plans/v2/receipts/2026-10-31-165/REPORT-source-trace-165.md`, ~20 lines). lore indexes that untracked directory and search cannot exclude a path. I opened nothing there. After that I used only git, awk and direct reads. §7 lists the one point that overlaps.
- **Deviation 2:** no ledger writes. I found lore friction but filed nothing, because the brief limits writes to this file. §7 gives the exact text to file.
- **Packages considered:** none (no mechanism specified). **Odoo-20 portability:** n/a (no Odoo seam touched). **Reuse ledger:** none (no symbols written).
- **Origin (§1):** `/source` is the **odoo-code (`mcp-code`) convention, carried over**. That quadlet binds its snapshot under `/source/*` and sets `SOURCE_SNAPSHOT_DIR=/source`, and lore's `snapshot.py` says it mirrors odoo-code. In git, lore's server has **never read `/source`**. At the first commit (`407d7f7`, 2026-05-31) the root was already hard-coded as `_DEFAULT_SNAPSHOT_ROOT = Path.home()/"docker"/"mcp"/"lore-snapshot"`. The `/source` prose (Containerfile and docstrings) and the skill's bind (`d0637ed`, 2026-06-02) were written **beside** that code, not to match it. Verdict: **an intended contract the server never implemented**, unread from the first commit. History before `407d7f7` is not in git.
- **The "/source:ro ×2" shape (§2):** two binds of the **same host dir**, `~/docker/mcp/lore-snapshot`, one to `/source` and one to `/home/lore/docker/mcp/lore-snapshot`. The second is the `$HOME` path, and it is the one that boots. Sources: live `CreateCommand` (container created 2026-10-31 10:15 EDT), #186 body, the lore memory `gotcha`. Apart from those two binds, the hand-rolled shape mounts exactly what the skill mounts: no corpora and no extra env.
- **Other deployments (§3):** none depend on `/source`.
  - `lore-demand_intelligence` binds only `/workspace` and the state dir. Its lore.yaml has one live root and **0 static roots**.
  - All 8 scratch dirs are git checkouts with slug `lore` and no container.
  - The only other `/source` user on the host is `mcp-code`, a separate quadlet that this skill does not touch.
- **Packet 19 (§4):** it keeps **no `/source` convention**. Its design runs the indexer in-container against "the same mounts" the server uses (corpora `:ro`, snapshot `rw` for the index run). Binding the snapshot at the server-read path now moves toward that design and pre-empts nothing. Packet 19's #165 wording needs an annotation once the stopgap ships.
- **Stale prose (§5):** 79 literal hits plus 4 non-literal locations, each with its own verdict.
  - **21 in-repo LIVE-INSTRUCTION rows:** 15 code/skill/Containerfile/docstring rows, plus packet 65 ×2, INDEX §Sequence and §Watch list, 11c Scope OUT, and the google-auth runbook. The runbook is LIVE at MEDIUM confidence: it is dated, but it is a runbook someone could follow.
  - **3 off-repo LIVE surfaces:** MEMORY.md and 2 lore memories.
  - **2 rows in packet 19 to annotate.** Everything else is HIST or OTHER.
- **Corrections to inherited claims (§6):** #165's "the test in test_lore_deploy.py asserts the /source mount" is **false at HEAD**. No skill test reaches the static-root branch; every stub returns `0` static roots. #165/#186's "nothing reads /source" holds at runtime. For git history, I add that the server never read it.
- **Decisions needed:** (a) whether off-repo memory (MEMORY.md landmine, 2 lore memories) is updated in the build's commit or by the lead; (b) whether the latent in-container re-acquire crash (§7) is in scope. It is separate from `/source`.
- **VERDICT — can the skill drop `/source` now? ONLY-IF** the same change binds the snapshot at `/home/lore/docker/mcp/lore-snapshot` (the premise of the brief), and the sibling code trace finds no runtime reader of `/source` in the baked image. For history and external dependents: **no dependent exists**. Confidence: **HIGH** on dependents and history (live inspects plus a full-tree sweep); **MEDIUM-HIGH** overall until the sibling's code trace lands.
- **Receipt pointers:** §1 origin table · §2 binds · §3 deployment table · §4 packet 19 · §5 prose table · §6 corrections · §7 flags · §8 routing.

---

## 0. Capability check
- **Demanded:** lore tools, `git log/show`, awk sweeps, `podman inspect/ps`, and writes only to this report.
- **Available:** all of the above. lore loaded with `ToolSearch "+lore"`.
- **Limit hit:** lore indexes the untracked `docs/plans/v2/receipts/2026-10-31-165/`, and no search parameter excludes a path. The brief's independence rule could not be enforced on `lore_search` (Deviation 1).
- **Textual sweeps:** used for `/source`, `lore-snapshot`/`CreateCommand`, `snapshot` and `SNAPSHOT_ROOT`. These are non-symbol textual seams (Containerfile comments, markdown, YAML, string literals), so this is case (b) of the dogfood protocol. Every sweep carries a coverage line.

## 1. Origin and intent

| evidence | receipt | what it shows |
|---|---|---|
| `git log -S'/source' -- skills/ loremaster/ Containerfile* docs/` | earliest commits `407d7f7` (2026-05-31 "Initial public release"), `d0637ed` (2026-06-02 "adopt lore-deploy skill into repo"), `d081bae` (2026-06-02) | `/source` was present from the first commit. No later commit introduced it. |
| `git show 407d7f7` `/source` lines | Containerfile 8/102/167/186 comments; `snapshot.py` docstring ("the server bind-mounts that dir `:ro` at `/source`"); `indexer.py` docstring; `test_source.py` docstring | Only prose and comments, with no code reading it. |
| `git show 407d7f7:loremaster/loremaster/server.py`, line 1486 | `_DEFAULT_SNAPSHOT_ROOT = Path.home() / "docker" / "mcp" / "lore-snapshot"`, passed at line 1283 as `snapshot_root=` | The server read the `$HOME` path from day 0. |
| `git log -S'_DEFAULT_SNAPSHOT_ROOT'` | `407d7f7` → `001f632` (2026-06-03 eager build) → `3552285` (2026-07-03 scout) → `130fa16` (2026-08-16 fastmcp façade) | The constant moved between modules but was never `/source`. |
| `d0637ed` `lore_deploy.py` | `cmd += ["-v", f"{SNAPSHOT_ROOT}:/source:ro"]` plus docstring "Adds the `/source` snapshot bind" | The skill implemented the prose convention, not the server's read path. The same skill's test docstring says the manifest dir "mounts to `$HOME/.local/state/lore` — NOT `/state` — so the container server reads the exact manifest + graph the host cold-index wrote". That is the right principle, applied to the manifest but not the snapshot. |
| pre-git history | `~/.claude/skills/lore-deploy` is a symlink into the repo (2026-06-02); `git log` of the skill shows the same repo history | **Not recoverable:** whatever predates `407d7f7` is outside git. The plan named in the docstrings ("plan AMENDMENT 1 / D8") is not in the repo or under `~/.claude/plans/`, which I swept for `lore-snapshot`/`AMENDMENT 1`+`D8` with 0 hits. |
| where `/source` comes from | `~/.config/containers/systemd/mcp-code.container`: `Volume=%h/docker/mcp/source-snapshot/<tier>:/source/<tier>:ro,Z` ×6, plus `odoo-custom`, plus `Environment=SOURCE_SNAPSHOT_DIR=/source`. `snapshot.py` docstring: "mirroring odoo-code's `read_file.py:144-159`"; `TIER_SUBDIRS` comment: "mirrors odoo-code read_file.py:116-117" | lore's snapshot layer is a port of odoo-code, and odoo-code's server **does** read `/source` (through env). lore ported the layout and the mount prose but not the env indirection. The server kept a `$HOME` default instead. This attribution is **MEDIUM**: it rests on the docstrings' stated lineage plus the identical convention, not on a commit message. |

**Verdict (HIGH for git history):** `/source` was an **intended contract that lore's server never implemented**. The Containerfile and docstrings describe it, but no lore server version in git reads it. It was neither a drift away from a working state nor a leftover from a removed reader. Within git history the snapshot root has never been `/source`. Before the first commit: unknown.

## 2. The "/source:ro ×2" known-good shape
- INDEX Log 2026-08-03 (04b-2 rollback receipts) and packet 65 runbook step 2 cite "`/source:ro` ×2" but carry **no paths**. A docs sweep for `lore-snapshot|CreateCommand` (files_opened=1059 = `git ls-files docs/ | wc -l`, hits=24) found no receipt with the literal binds.
- The literal binds come from three sources:
  1. **live** `podman inspect lore-lore --format '{{.Config.CreateCommand}}'`, created 2026-10-31 10:15:56 EDT, image `4312207128bb`:
     `-v /home/ejprice/docker/mcp/lore-snapshot:/source:ro` and `-v /home/ejprice/docker/mcp/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro`;
  2. finding #186 body (2026-07-25): the same two lines. It states the `/source` one is kept "only for shape-parity with the skill; nothing reads it";
  3. lore memory (kind `gotcha`, "the ONLY mount shape that boots"): the same recipe, "The `/source` line is vestigial … the SECOND snapshot mount is the one that matters."
- **Yes, the second bind is the `$HOME` snapshot path**, the one `_DEFAULT_SNAPSHOT_ROOT` resolves to with `-e HOME=/home/lore`.
- **Everything else in the hand-rolled shape matches the skill:** `--network=host --userns=keep-id --user 1000:1000 -e HOME=/home/lore`, `/workspace:ro`, the state-dir bind, `--env-file …/lore.env`, `-e LORE_CONFIG=/workspace/lore.yaml`. There is **no corpora mount** (`~/docker/mcp/lore-corpora` is not bound) and no extra env. Mounts as `.Mounts`: `/workspace rw=false`, state `rw=true`, both snapshot binds `rw=false`.
- A related design statement: design-sidecar 04b-2 (`docs/plans/v2/receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md` item 3) defines the known-good check as "the snapshot mounted at the path the server READS, never `/source`". The ×2 wording in INDEX and packet 65 is that same shape plus the vestigial bind.

## 3. Other deployments

| deployment | what it is | static roots | `/source` dependence | receipt |
|---|---|---|---|---|
| `lore-demand_intelligence` (container) | exited; `StartedAt` 2026-07-25 21:23 EDT, `FinishedAt` zero-time (an unclean stop, likely a host reboot: hence podman's "Exited (0) 292 years ago"); image `b46bc1d5` (old) | **0**: one root `tier: demand_intelligence, watch: live, path: /workspace` (`pp-odoo/demand_intelligence/lore.yaml`) | **none**. CreateCommand binds only `pp-odoo/demand_intelligence:/workspace:ro`, the state dir, `--env-file …/demand_intelligence.env`, `LORE_CONFIG`. No snapshot bind of any kind. | `podman inspect` CreateCommand and `.Mounts` |
| `~/.local/state/lore/demand_intelligence.*` | legacy SQLite manifest, kuzu graph and memory DBs (content mtime 2026-07-04, shm 2026-08-12) | n/a | none. State files, not mounts. | `ls -la ~/.local/state/lore` |
| `~/adv_eh_scratch` | git checkout @ `e1dfa14`, lore.yaml byte-identical to lore's | 3 (copy) | none. No container. | `cmp`, `git rev-parse`, all-container mount scan |
| `~/coldaudit03b-scratch` | git checkout @ `fc3bb7b`; lore.yaml differs only by lacking `lorerunes/**` in include | 3 (copy) | none. No container. | same |
| `~/lore-scratch-04b4` | git checkout @ `5c5ff7a`, lore.yaml identical | 3 (copy) | none | same |
| `~/lore-scratch-adv04b4-2` | git checkout @ `37d4adc`, identical | 3 (copy) | none | same |
| `~/lore-scratch-adv04b4` | git checkout @ `5c5ff7a`, identical | 3 (copy) | none | same |
| `~/pkt06a-coldaudit-scratch` | git checkout @ `f9b5f2b`, identical | 3 (copy) | none | same |
| `~/scratch-adv-verbs-05b` | git checkout @ `c0071cd`, identical | 3 (copy) | none | same |
| `~/scratch-verbs-05b` | git checkout @ `c0071cd`, identical | 3 (copy) | none | same |
| `mcp-code` (quadlet) | **odoo-code** MCP, not lore | n/a | uses its **own** `/source` (`SOURCE_SNAPSHOT_DIR=/source`, host `~/docker/mcp/source-snapshot/*`). Independent of lore_deploy.py; unaffected. | quadlet file, `podman inspect` |

- **All-container scan:** every container's `.Mounts` (38 containers) was filtered for `/source|scratch|lore-snapshot|lore-corpora`. Only `mcp-code` (odoo-code) and `lore-lore` match.
- **Quadlets:** of the 13 units under `~/.config/containers/systemd/`, only `mcp-code.container` mentions `/source`. No lore quadlet exists.
- **No scratch dir is a live deployment** (HIGH): there is no container, quadlet or mount for any of them, and their slug `lore` would collide with the real deployment.
- **Only lore-lore has static roots among live deployments**, so the skill's static-root bind branch affects lore-lore alone.

## 4. Packet 19's stance
- `docs/plans/v2/19-lore-deploy-rework.md` (INDEX row 19 status: **open**, "REDESIGNATED 2026-07-22; urgency ↑ 2026-07-25"; no design doc exists under `docs/design/` matching `deploy`).
- **No `/source` convention is kept.** The Scope IN one-toolchain line reads: "in-container execution for all four shell-outs (`podman run --rm <image> … -m loremaster.index --config …`, corpora `:ro`, snapshot `rw`)". It also states that "#165 dissolution [is] a design consequence … a static-tier deploy where indexer and server read the same mounts". #166's body, which packet 19 adopts, describes `/source` as one of "three paths that must agree and didn't", which is a defect, not a convention.
- **Effect of dropping `/source` now:** it is consistent with the target. The server's read path becomes the single container path, and that is the path packet 19's in-container indexer would also write (rw for the index run). Packet 19 also lists "snapshot/boot-check keying" (key the boot skip on the store, not the disk), which might later remove the snapshot mount entirely for DB-served tiers. A stopgap that binds at the server path neither commits to nor blocks that.
- **What it does pre-empt (mildly):** packet 19's Exit says "#166/#165 annotated with their build destinations", and its prose treats #165 as dissolved *by* packet 19. If the stopgap ships, #165 resolves earlier. Packet 19 text at lines 15 and 22 (and INDEX row 19 / Sequence line 269) should then say #165 was closed by the stopgap, while #186's urgency rationale ("every new static tier widens the blast radius") lapses. #165's own "Option B" (a `LORE_SNAPSHOT_ROOT` env set to `/source`) would honour the convention. Packet 19 does not choose B, and nothing found here requires it.

## 5. Prose that would go stale
Two sweeps over `git ls-files` at `acbce73`: `/source` (files_opened=1620 = `git ls-files | wc -l`, hits=79) and a supplementary skill/top-level `snapshot` sweep (files_opened=21, hits=33). The verdict key: **LIVE** = a live instruction or claim that must change with the bind; **HIST** = a dated log, closed-packet record or archived receipt, so leave it; **OTHER** = not about the snapshot mount (a substring collision). Section context for plan docs comes from the nearest heading plus the packet's INDEX status.

### 5a. LIVE-INSTRUCTION (must change)

| file:line | verdict | note |
|---|---|---|
| `skills/lore-deploy/scripts/lore_deploy.py:684` | LIVE | the bind itself (`_launch_container`) |
| `skills/lore-deploy/scripts/lore_deploy.py:662` | LIVE | `_launch_container` docstring "Adds the `/source` snapshot bind" |
| `skills/lore-deploy/scripts/test_lore_deploy.py:39` | LIVE | comment "No static roots → no /source mount" |
| `skills/lore-deploy/scripts/test_lore_deploy.py:219` | LIVE | comment in `_stub_read_config_field` |
| `skills/lore-deploy/references/lifecycle.md:18` | LIVE | "bind-mounted `:ro` at `/source`" |
| `skills/lore-deploy/references/lifecycle.md:19` | LIVE | "needs no `/source` mount" |
| `skills/lore-deploy/references/lifecycle.md:146` | LIVE | run recipe `[ -v <snapshot>:/source:ro ]` |
| `Containerfile:8` | LIVE | header "read-only snapshot of static tiers at /source" |
| `Containerfile:102` | LIVE | "the :ro bind mounts at /workspace and /source" |
| `Containerfile:167` | LIVE | run recipe |
| `Containerfile:186` | LIVE | flag explanation (continues at 187-190) |
| `loremaster/loremaster/source/snapshot.py:6` | LIVE | module docstring |
| `loremaster/loremaster/source/snapshot.py:70` | LIVE | `SnapshotLayout` docstring |
| `loremaster/loremaster/index/indexer.py:395` | LIVE | `Indexer.__init__` docstring |
| `loremaster/tests/test_source.py:6` | LIVE | module docstring |
| `docs/plans/v2/65-hosted-write-joint-cutover.md:33` | LIVE | FIRST READS of an **open** packet: "HAND-ROLLED `/source` mount … NEVER `lore-deploy start`" |
| `docs/plans/v2/65-hosted-write-joint-cutover.md:130` | LIVE | cutover runbook step 2: diff against "`/source:ro` ×2" |
| `docs/plans/v2/INDEX.md:269` | LIVE | §Sequence + status: "the cutover's hand-rolled `/source` mount is its subject" |
| `docs/plans/v2/INDEX.md:581` | LIVE | §Watch list: "lore-lore runs on a HAND-ROLLED /source mount — NOT restart-durable" |
| `docs/plans/v2/11c-index-boot-reconcile-honesty.md:80` | LIVE | Scope OUT of an **open** packet names "#165/#166 (the hand-rolled `/source` mount)". Annotate. |
| `docs/design/2026-08-01-google-auth-restart-runbook.md:87` | LIVE (MEDIUM) | a runbook line "#165 is open — a container recreate re-mounts `/source` and re-breaks boot". It is dated, but it is a runbook someone could follow. Annotate rather than rewrite. |

21 rows: 15 are code, skill, Containerfile and docstrings, and 6 are docs (packet 65 ×2, INDEX ×2, 11c, the runbook).

### 5b. LIVE, but non-literal or off-repo (the `/source` sweep cannot see these)

| location | verdict | note |
|---|---|---|
| `~/.claude/projects/-home-ejprice-PycharmProjects-lore/memory/MEMORY.md` landmine 1 | LIVE (off-repo) | "lore-lore runs a HAND-ROLLED `/source` mount … do NOT `lore-deploy start` it until #165/#166 land". This file auto-loads every session. #165's 2026-10-31 annotation records that this text failed to stop an agent. |
| lore memory, kind `gotcha` ("lore-lore's working `podman run` — the ONLY mount shape that boots") | LIVE (off-repo, store) | the recipe with ×2 binds; says "do NOT `lore-deploy start` lore-lore". Supersede with `lore_remember(supersedes=…)` once the fix deploys. |
| lore memory, kind `fact` (2026-07-22 session, "⚠⚠ lore-lore runs a HAND-ROLLED /source mount") | LIVE (off-repo, store), or HIST if left as a dated session note | it is dated but phrased as a standing instruction; recall serves it for "hand-rolled mount" queries. |
| `docs/plans/v2/INDEX.md:1976` | HIST | Log 06b: "hand-rolled double-mount, verbatim CreateCommand" (no literal `/source`) |
| `docs/plans/v2/19-lore-deploy-rework.md:15` | OTHER→annotate | describes the #165 *defect* ("the /source-vs-snapshot three-paths-must-agree mount bug"). Still true as history, but annotate that the stopgap closed it. |
| `docs/plans/v2/19-lore-deploy-rework.md:22` | OTHER→annotate | the #186 urgency paragraph. Same treatment. |

### 5c. HISTORICAL-RECORD (leave)

| file:line | verdict | note |
|---|---|---|
| `docs/plans/v2/INDEX.md:1055` | HIST | Log 2026-07-22 |
| `docs/plans/v2/INDEX.md:1058` | HIST | Log 2026-07-22 |
| `docs/plans/v2/INDEX.md:1748` | HIST | Log 2026-08-03 04b-2 rollback receipts ("`/source:ro` ×2") |
| `docs/plans/v2/INDEX.md:1752` | HIST | Log 2026-08-03 04b-2 deployed |
| `docs/plans/v2/INDEX.md:1785` | HIST | Log 2026-08-04 #327 deploy |
| `docs/plans/v2/03b-comms-message-surface.md:69` | HIST | BUILD-PHASE HANDOFF 2026-07-24; 03b **DONE + DEPLOYED 2026-07-26** |
| `docs/plans/v2/10-d-weak-match-disarm.md:82` | HIST | Exit section; 10-d **DONE + DEPLOYED 2026-07-26** |
| `docs/plans/v2/10-d-weak-match-disarm.md:83` | HIST | same |
| `docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:23` | HIST | dated resume doc (phase state) |
| `docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:25` | HIST | same |
| `docs/design/2026-07-31-packet39-google-oauth.md:330` | HIST | ruled, dated design doc describing the #165 hazard at the time |
| `docs/plans/v2/receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md:117` | HIST | archived receipt |
| `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:448` | HIST | archived receipt |
| `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:609` | HIST | archived receipt |
| `docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:283` | HIST | archived receipt |
| `docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:304` | HIST | archived receipt |
| `docs/plans/v2/receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:733` | HIST | archived receipt |
| `docs/plans/v2/receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:734` | HIST | archived receipt |
| `docs/plans/v2/receipts/2026-08-16-packet59/REPORT-lead-59.md:146` | HIST | archived receipt |
| `docs/plans/v2/receipts/2026-09-09-packet63b-ib/REPORT-lead-63b-s2.md:58` | HIST | archived receipt |

### 5d. OTHER (substring collisions, not about the mount)

| file:line | verdict | note |
|---|---|---|
| `.claude/agents/package-scout.md:146` | OTHER | "installed signature/source" |
| `EXTENDING.md:372` | OTHER | path `loremaster/source/snapshot.py` |
| `LORE_EXTERNAL_REVIEW.md:125` | OTHER | "fact/source confidence" |
| `docs/design/2026-08-14-packet47-ingest-entity-seam-design.md:629` | OTHER | `file_path/source_book` |
| `docs/design/2026-08-28-packet63-retrofit-rulings.md:52` | OTHER | `labels/source/importance` |
| `docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md:151` | OTHER | "served/source prose" |
| `docs/plans/v2/MASTER-PLAN.md:283` | OTHER | "ident/source/llm_summary" |
| `docs/plans/v2/receipts/2026-07-28-packet11ib/REPORT-informant-fable-11ib.md:52` | OTHER | "tiers/sources" |
| `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:92` | OTHER | dndbeyond URL `/sources/` |
| `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:564` | OTHER | dndbeyond URL |
| `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:169` | OTHER | path `loremaster/source/local_directory.py` |
| `docs/plans/v2/receipts/2026-08-08-packet05aiii/REPORT-contract-fix-05aiii.md:201` | OTHER | "read-only/source leg" |
| `docs/plans/v2/receipts/2026-08-09-defect-class/REPORT-adversary-g.md:70` | OTHER | "and/or" fragment |
| `docs/plans/v2/receipts/2026-08-10-packet05aii/REPORT-adversary-05a-ii.md:432` | OTHER | "AST/source guard" |
| `docs/plans/v2/receipts/2026-08-12-packet06a/REPORT-coldaudit-honesty-06a.md:17` | OTHER | collision in prose |
| `docs/plans/v2/receipts/2026-08-16-packet59/REPORT-sweep-59.md:319` | OTHER | "signature/source" |
| `docs/plans/v2/receipts/2026-08-17-packet07/DESIGN-sidecar-144-posture.md:115` | OTHER | "signature/source" |
| `docs/plans/v2/receipts/2026-08-17-regression-fix/REPORT-regr-fixer.md:68` | OTHER | collision in prose |
| `docs/plans/v2/receipts/2026-08-20-packet48/REPORT-build-48b.md:11` | OTHER | collision in prose |
| `docs/plans/v2/receipts/2026-08-20-packet48/REPORT-builder-48b.md:11` | OTHER | collision in prose |
| `docs/plans/v2/receipts/2026-08-24-packet62/REPORT-adversary-62w2.md:293` | OTHER | "package/source considered" |
| `docs/plans/v2/receipts/2026-09-04-packet63b/REPORT-contract-63b-i-b.md:52` | OTHER | `labels/source/expires_at` |
| `docs/plans/v2/receipts/2026-09-12-packet63b-ii-b/REPORT-contract-63b-ii-b.md:98` | OTHER | "AST/source pin" |
| `docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:110` | OTHER | log `file_path: loremaster/loremaster/source/__init__.py` |
| `docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:111` | OTHER | log line, same shape |
| `docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:112` | OTHER | log line, same shape |
| `docs/plans/v2/receipts/2026-10-04-531-536/REPORT-fix531.md:190` | OTHER | path `loremaster/source/local_directory.py` |
| `loremaster/tests/test_config.py:96` | OTHER | odoo-extension fixture value `"/source/installed.txt"`, an arbitrary config string. **Flag:** it echoes the odoo-code `/source` layout, but nothing in lore resolves it. |
| `loremaster/tests/test_config.py:305` | OTHER | same fixture, asserted |
| `loremaster/tests/test_mcp_server.py:1719` | OTHER | "auto/summary/source" |
| `loremaster/tests/test_memory_replay_fidelity_63b_ib.py:9` | OTHER | `labels/source/` |
| `loremaster/tests/test_render_slot_inventory.py:168` | OTHER | "store/source-minted" |
| `loremaster/tests/test_search.py:2870` | OTHER | "summary/source/auto" |
| `lorescribe/tests/test_astroid_parse.py:828` | OTHER | "chunk_type/source's" |
| `loresigil/loresigil/data/voyage4_tokenizer.json:54621` | OTHER | tokenizer vocab entry |
| `loresigil/loresigil/data/voyage4_tokenizer.json:96938` | OTHER | tokenizer vocab entry |

Accounting for the 79 `/source` hits: 5a holds 21 (all literal hits), 5b's literal hits are `19:15` and `19:22` (2), 5c holds 20, and 5d holds 36. Total: 21 + 2 + 20 + 36 = **79**, which equals the sweep's `hits=79`. ✔ The non-literal 5b rows (MEMORY.md, 2 lore memories, INDEX:1976) are outside the 79.

## 6. Corrections to inherited claims
1. **#165 body: "the test in test_lore_deploy.py that asserts the /source mount".** False at HEAD `acbce73`. A sweep of `skills/` for `SNAPSHOT_ROOT|source:ro|static_root_count` (files_opened=17, hits=5) finds no test hit. Both `/source` mentions in `test_lore_deploy.py` are comments in stubs that return `"0"` static roots. **The static-root branch of `_launch_container` has no test at all.** The build should know this: removing the `/source` string breaks nothing, and nothing would catch a wrong replacement path either. #165's "owed invariant" (a boot-level test, not a string test) is still owed.
2. **#165/#186: "nothing reads /source".** Holds for the runtime per those findings; the code readers are the sibling's job. I add the git-history leg: no version of lore's server in git ever read it (§1).
3. **#186: "/source kept only for shape-parity with the skill".** Accurate. The parity argument disappears once the skill changes, and the INDEX/packet-65 "×2" runbook wording should then become ×1.

## 7. Flags (surfaced; not acted on)
- **F1. Independence breach mechanism (lore friction).** `lore_search` serves untracked receipt dirs, and no parameter excludes a path or tier subtree. A brief demanding a blind re-run cannot be honoured on lore. **For the lead to file:** `lore_findings action=report area=lore_search category=capability_gap subject="lore_search cannot exclude a path; untracked receipts of a prior run leak into a mandated-independent re-run"`. The single overlapping point (F2's re-acquire crash) appeared in that leaked chunk. My F2 statement rests on #165's own body and the live `.Mounts` (`rw=false`), not on the leaked text.
- **F2. In-container re-acquire still cannot succeed.** Per #165's mechanism, a re-acquire reads the tier's host `source:` path (`~/docker/mcp/lore-corpora/<tier>`). That path is not mounted in either the skill's shape or the hand-rolled one. The snapshot bind is also `:ro` (live `.Mounts rw=false`), so a copy into it would fail too. Dropping `/source` and adding the server-path bind fixes the **fast-skip** path only. A `version:` bump in lore.yaml, a lost snapshot or a rebuild still crash-loops. This is outside "drop /source". **Do you want it addressed now, or left to packet 19** (whose snapshot-`rw` plus in-container indexer design is its natural home)?
- **F3. Silent no-bind.** `_launch_container` adds the snapshot bind only when `SNAPSHOT_ROOT.exists()` (`lore_deploy.py:683`). A deployment with static roots and a missing host snapshot launches without it and then hits F2. **Do you want a fail-loud there in the same change?**
- **F4. MEMORY.md and lore memories (5b) are off-repo.** The build's commit cannot carry them. Someone must edit MEMORY.md and supersede the two lore memories after the fix deploys. Otherwise the auto-loaded landmine keeps telling every session not to `lore-deploy start` lore-lore, which by then is the correct way to start it.
- **F5. `lore-demand_intelligence`** is on old image `b46bc1d5`, stopped uncleanly (FinishedAt zero), with no restart policy (#339's class). It is unaffected by `/source`, but it is a deployment nobody is running. **Do you want it looked at?**
- **F6. Stale legacy SQLite state.** `~/.local/state/lore/lore.db-shm` mtime is 2026-10-31 08:08 and `lore.memory.db-shm` is 10:16, so something still opens the legacy SQLite files at boot. #186 flagged this as unresolved. It is unrelated to `/source`, but it misleads during outages.
- **F7. `test_config.py:96/305`** use `/source/installed.txt` as an odoo-extension fixture path. That is harmless, but it is a second place the odoo-code `/source` convention appears in lore. If the odoo extension ever resolves `installed_modules_file` inside a container, it would need the same mount decision.

## 8. Routing table and fan-out

| step | tier | who | reason |
|---|---|---|---|
| `/source` sweep (79 hits) | 1-eligible | me, inline | on the critical path; small output I read in full; 1 command |
| docs `lore-snapshot/CreateCommand` sweep (24 hits) | 1-eligible | me, inline | same; small |
| skill `snapshot` / `SNAPSHOT_ROOT` sweeps (33 and 5 hits) | 1-eligible | me, inline | same; small |
| podman inspects (lore-lore, DI, 38-container scan, quadlets) | 1 | me, inline | read-only, short output, on the critical path |
| hit classification (79 rows) | 2-eligible | me | many verdicts depend on state elsewhere: a packet's INDEX status (03b/10-d DONE vs 11c/65 open), the heading a line sits under (Log vs Watch list vs Sequence). Under the split rule those stay with the owner; a sampled Sonnet draft would miss the status lookups. |
| origin and history judgement, packet 19 reading, verdict | 3 | me | open judgement; errors here would seal themselves |

Fan-out: haiku 0 · sonnet 0 · peak 0. No test runs (read-only investigation; none were needed).
