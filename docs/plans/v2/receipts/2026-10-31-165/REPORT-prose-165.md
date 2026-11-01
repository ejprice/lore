brief-base v23 read
- brief project v7 read (lore_comms register, session fix-165-2026-10-31)
- State: done (2026-10-31T16:15Z, ~6 min wall-clock of the 60 min deadline; nothing NOT TRIED)
- Deviations: (1) I fixed one extra LIVE-MISSED site inside my writable set: `65-hosted-write-joint-cutover.md` read-list item 7 (~:33), which still said "HAND-ROLLED `/source` … NEVER `lore-deploy start`". (2) The first gate run was RED on ruff E501 at `test_source.py:8`. My own rewrap caused it; I fixed it and the re-run is green.
- Packages considered: none — no mechanism specified (prose only)
- Odoo-20 portability: n/a — no Odoo seam touched
- Reuse ledger: none (no new symbols; docstring/comment/doc text only)
- Graded: acbce73 · HEAD-at-report: acbce73 · SAME (uncommitted working-tree edits on top; lead commits)
- Gate: `ruff` All checks passed · `pytest loremaster/tests/test_source.py` **27 passed**, exit 0 (§Gate receipt)
- Sweep: hits=79 / files_listed=1620. Every hit has a verdict: LIVE-FIXED 15 · HISTORICAL 26 · UNRELATED 30 · LIVE-MISSED outside set 2 · implementer-owned 4 (§Residual sweep)
- Decisions needed:
  - D1: two LIVE-MISSED sites outside my set need the lead's call: `docs/design/2026-07-31-packet39-google-oauth.md:330` (packet 39 is OPEN) and `docs/plans/v2/11c-…:80` (11c is OPEN). Suggested text is in §Flags.
  - D2 (MEDIUM, my inference, unrun): the remedy "re-index on the host first, before a version bump or rebuild_all". Confirm it matches the refusal error text the implementer writes.
  - D3: `lore_deploy.py:662/684` and `test_lore_deploy.py:39/219` still read `/source` in this tree. They are implementer/contract-owned; confirm they change in the fix commit.
- Pointers: §Truth verified · §Per-site edits · §Residual sweep · §Gate receipt · §Flags
- Fan-out: haiku 3 (1 worker sweep, 2 runner gate runs) · sonnet 0 · peak 2

# REPORT-prose-165 — live-instruction prose for lore finding #165

Spawned 2026-10-31T16:09Z · base: acbce73ee353aed4a766ae17bf815a571e0e1ab1

## Routing table (written before any sweep; brief-base §3 FAN-OUT)
| step | tier | who | reason |
|---|---|---|---|
| 1. read each site + context, write new wording | 3 | self (inline) | brief routes it: rule/doc wording is never delegated |
| 1a. verify `build_app_context` "read-file static base" claim vs code | 3 | self | depends on state elsewhere (lore_read store path); error would self-seal in a docstring |
| 2. residual `/source` sweep after edits | 1 | haiku-worker | brief routes it; exact awk command, coverage line |
| 2a. per-hit verdicts on sweep output | 3 | self | brief requires each hit adjudicated by me; verdicts depend on deploy state (bind exists or not), which a sampled draft would misjudge on hits that read plausibly-current |
| 3. ruff + targeted pytest on touched .py | 1 | haiku-runner | brief routes it; exact command |

## Capability check
- Demanded: lore_comms register, lore tools, haiku-worker/haiku-runner spawns, file edits in writable set. Have all (lore loaded via ToolSearch; Agent tool present).

## Truth verified before rewording (read at acbce73, 2026-10-31)
- HIGH: `build_app_context(snapshot_root=…)` passes it only to `graph_roots(config, snapshot_root)` (astroid resolution) and `Indexer(snapshot_root=…)`. `lore_read` is `StoreReadTool(store=write_store, manifest=manifest)` and takes no snapshot root. `ReadFileTool(` is constructed nowhere in production (`git ls-files '*.py' | xargs awk` over `loremaster/loremaster`); `store_read.py` imports it only for its span helpers. So "also the read-file static base" and "served from (…/source)" were both stale.
- HIGH: the snapshot root's live job is `Indexer._snapshot_materialized`, the fast-skip guard: version stamp matches AND the dir is present and non-empty → `index.tier.skip`; otherwise a re-acquire.
- HIGH (measured 2026-10-31, `podman inspect lore-lore` Mounts): the hand-rolled lore-lore carries TWO snapshot binds, `…/lore-snapshot -> /source` (ro) AND `…/lore-snapshot -> /home/lore/docker/mcp/lore-snapshot` (ro). That is what "`/source:ro` ×2" in 65-cut meant.

## Per-site edits (before → after; acbce73 line numbers, re-located by content)
| site | before | after |
|---|---|---|
| Containerfile:8 (comment) | "optional read-only snapshot of static tiers at /source" | at `/home/lore/docker/mcp/lore-snapshot` (= `_DEFAULT_SNAPSHOT_ROOT` under HOME=/home/lore, the only root), no /source since the #165 stopgap |
| Containerfile:102 (comment) | ":ro bind mounts at /workspace and /source" | "/workspace and /home/lore/docker/mcp/lore-snapshot" |
| Containerfile:167 (comment) | `[ -v <snapshot>:/source:ro ]` | `[ -v <snapshot>:/home/lore/docker/mcp/lore-snapshot:ro ]` |
| Containerfile:186–190 (comment) | `-v <snapshot>:/source:ro` + "only needed when…" | home-path target, why (only root), refusal on missing host dir + cold-index remedy, the old /source history (#165), KNOWN BOUND #166 |
| lifecycle.md:17–19 | "bind-mounted :ro at /source … needs no /source mount" | home-path bind = `_DEFAULT_SNAPSHOT_ROOT`; no /source (history); no static roots → no bind; missing host dir → `start` refuses (path + remedy); KNOWN BOUND #166 |
| lifecycle.md:146 | `[ -v <snapshot>:/source:ro ]` | `[ -v <snapshot>:/home/lore/docker/mcp/lore-snapshot:ro ]` |
| snapshot.py:6 (module docstring) | "the server bind-mounts that dir :ro at /source and locates files within it" | "the deployed container bind-mounts that dir :ro at the server's snapshot root (`_DEFAULT_SNAPSHOT_ROOT` …; no /source since #165 stopgap), and the indexer and code graph locate files within it" |
| snapshot.py:70 (`SnapshotLayout` Args) | "materialised under and served from (bind-mounted :ro at /source in the live server)" | "materialised under (in the deployed container, the :ro bind at `_DEFAULT_SNAPSHOT_ROOT`)" |
| indexer.py:395 (`Indexer` Args) | "materialised under and served from (bind-mounted :ro at /source …)" | "materialised under and walked from; `_snapshot_materialized` checks it before a version-stamp skip. In-container: the :ro bind at `_DEFAULT_SNAPSHOT_ROOT`, so an in-container re-acquire cannot write it (KNOWN BOUND #166)" |
| server.py `build_app_context` Args | "Static-tier snapshot root (also the read-file static base)." | handed to `Indexer` (materialisation + skip guard) and `graph_roots` (astroid); "Not a read base: lore_read serves from the store (`StoreReadTool`)" |
| test_source.py:6 (module docstring) | "the server bind-mounts that dir :ro at /source" | "the deployed container bind-mounts that dir :ro at the server's snapshot root (`_DEFAULT_SNAPSHOT_ROOT`; not /source, which nothing read, #165)" |
| 65-hosted-write-joint-cutover.md:130 | known-good = "`/source:ro` ×2" | known-good = ONE snapshot bind at the home path, no /source; /source + home bind = stale hand-rolled (boots, recreate via `lore-deploy start`); /source only, no home bind = #165 crash shape → STOP; KNOWN BOUND #166 (re-index on the host before a version bump or rebuild_all) |
| INDEX.md:581 (standing landmine) | "HAND-ROLLED /source mount — NOT restart-durable until packet 19" | stopgap shipped 2026-10-31: binding, ONE-bind correct shape, the redundant /source on the 07-22 container, refusal on missing host dir + remedy; KNOWN BOUND #166 (version bump / rebuild_all still crashes boot; re-index on the host first; operator-visible) |
| INDEX.md:269 | ANNOTATED: "(2026-10-31: superseded by the #165 stopgap …; 19 still owns #166 …)" | — |
| runbook 2026-08-01:87 | "#165 is open — a recreate re-mounts /source and re-breaks boot" | stopgap shipped: home bind, refusal on missing dir, a plain recreate no longer re-breaks boot; still true: the re-acquire bound (version bump / rebuild_all); capture CreateCommand kept |
| 19-lore-deploy-rework.md:15 | ANNOTATED after "DISSOLVES #165" para: stopgap; class NOT dissolved; re-acquire bound is still 19's | — |
| 19-lore-deploy-rework.md:22 | ANNOTATED after the #186 para: a plain recreate no longer crash-loops; version bump / rebuild_all still does (#166) | — |

Wording judgement flagged (MEDIUM): "re-index on the host first" in the 65-cut, INDEX:581 and Containerfile remedy text is my inference. A host `python -m loremaster.index --config …` writes the host snapshot plus the tier version stamp, so the container boot's `_snapshot_materialized` + stamp match should skip. I did not run it. The lead or the contract owner should confirm it matches the refusal error's remedy text.

## Residual sweep (haiku-worker, after edits; before the 65:33 fix)
`RAN: … git ls-files -z | xargs -0 awk 'index($0,"/source"){…}' > /var/tmp/claude-1000/prose-165-sweep.txt` · `awk_exit=0 · files_listed=1620 · hits=79`.
Verdict key: LIVE-FIXED (the new correct prose, or fixed by me) · HISTORICAL (a dated Log entry, a receipt, a done packet, a superseded doc) · UNRELATED (the substring is not the mount, e.g. `…/sources`, `signature/source`) · LIVE-MISSED (stale live prose still standing).
Line numbers are those of the post-edit tree at sweep time.

| # | file:line | verdict | note |
|---|---|---|---|
| 1 | .claude/agents/package-scout.md:146 | UNRELATED | "signature/source" |
| 2 | Containerfile:11 | LIVE-FIXED | new text ("no /source mount since…") |
| 3 | Containerfile:199 | LIVE-FIXED | new history clause |
| 4 | EXTENDING.md:372 | UNRELATED | path `loremaster/source/snapshot.py` |
| 5 | LORE_EXTERNAL_REVIEW.md:125 | UNRELATED | "fact/source confidence" |
| 6 | docs/design/2026-07-31-packet39-google-oauth.md:330 | **LIVE-MISSED (outside set)** | packet 39 is OPEN; rationale says "#165 is open … a recreate re-mounts `/source` and re-breaks boot". Suggested annotation for the lead below |
| 7 | docs/design/2026-08-01-google-auth-restart-runbook.md:88 | LIVE-FIXED | my rewrite |
| 8 | docs/design/2026-08-14-packet47-…:629 | UNRELATED | `file_path/source_book` |
| 9 | docs/design/2026-08-28-packet63-retrofit-rulings.md:52 | UNRELATED | `labels/source/importance` |
| 10 | docs/design/2026-09-11-packet63b-ii-b-…:151 | UNRELATED | "served/source prose" |
| 11 | docs/plans/v2/03b-comms-message-surface.md:69 | HISTORICAL | 03b ✅ DONE + DEPLOYED (INDEX table) |
| 12 | docs/plans/v2/10-d-weak-match-disarm.md:82 | HISTORICAL | 10-d ✅ DONE + DEPLOYED 2026-07-26 |
| 13 | docs/plans/v2/10-d-weak-match-disarm.md:83 | HISTORICAL | same packet |
| 14 | docs/plans/v2/11c-index-boot-reconcile-honesty.md:80 | **LIVE-MISSED (outside set)** | 11c OPEN; Scope-OUT label "#165/#166 (the hand-rolled `/source` mount)". Low severity, it is a label. Suggested: "#165 (stopgap shipped 2026-10-31) / #166 (in-container re-acquire bound)" |
| 15 | docs/plans/v2/19-lore-deploy-rework.md:15 | HISTORICAL | original packet-19 framing, annotated per brief (my note follows at :17–20) |
| 16 | docs/plans/v2/19-lore-deploy-rework.md:18 | LIVE-FIXED | my annotation |
| 17 | docs/plans/v2/19-lore-deploy-rework.md:26 | HISTORICAL | #186 para, annotated per brief |
| 18 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:23 | HISTORICAL | header: "SUPERSEDED 2026-08-02 — this file is history" |
| 19 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:25 | HISTORICAL | same |
| 20 | docs/plans/v2/65-hosted-write-joint-cutover.md:33 | LIVE-MISSED → **LIVE-FIXED** | inside my set; the read-list item 7 said "HAND-ROLLED `/source` … NEVER `lore-deploy start`". Rewritten (see below) |
| 21 | docs/plans/v2/65-hosted-write-joint-cutover.md:132 | LIVE-FIXED | my rewrite |
| 22 | docs/plans/v2/65-hosted-write-joint-cutover.md:133 | LIVE-FIXED | my rewrite |
| 23 | docs/plans/v2/65-hosted-write-joint-cutover.md:134 | LIVE-FIXED | my rewrite |
| 24 | docs/plans/v2/INDEX.md:269 | HISTORICAL | original wording, annotated per brief |
| 25 | docs/plans/v2/INDEX.md:271 | LIVE-FIXED | my annotation |
| 26 | docs/plans/v2/INDEX.md:586 | LIVE-FIXED | rewritten landmine |
| 27 | docs/plans/v2/INDEX.md:588 | LIVE-FIXED | rewritten landmine |
| 28 | docs/plans/v2/INDEX.md:1066 | HISTORICAL | `## Log` (starts at :613), 2026-07-22 entry |
| 29 | docs/plans/v2/INDEX.md:1069 | HISTORICAL | Log, 2026-07-22 |
| 30 | docs/plans/v2/INDEX.md:1759 | HISTORICAL | Log, 04b-2 deploy receipts 2026-08-03 |
| 31 | docs/plans/v2/INDEX.md:1763 | HISTORICAL | Log |
| 32 | docs/plans/v2/INDEX.md:1796 | HISTORICAL | Log |
| 33 | docs/plans/v2/MASTER-PLAN.md:283 | UNRELATED | `ident/source/llm_summary` |
| 34 | receipts/2026-07-28-packet11ib/REPORT-informant-fable-11ib.md:52 | UNRELATED | receipt; "tiers/s…" |
| 35 | receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md:117 | HISTORICAL | receipt |
| 36 | receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:92 | UNRELATED | dndbeyond URL `/sources/` |
| 37 | receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:564 | UNRELATED | URL `/sources/` |
| 38 | receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:169 | UNRELATED | path `loremaster/source/…` |
| 39 | receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:448 | HISTORICAL | receipt |
| 40 | receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:609 | HISTORICAL | receipt |
| 41 | receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:283 | HISTORICAL | receipt |
| 42 | receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:304 | HISTORICAL | receipt |
| 43 | receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:733 | HISTORICAL | receipt |
| 44 | receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:734 | HISTORICAL | receipt |
| 45 | receipts/2026-08-08-packet05aiii/REPORT-contract-fix-05aiii.md:201 | UNRELATED | "read-only/source leg" |
| 46 | receipts/2026-08-09-defect-class/REPORT-adversary-g.md:70 | UNRELATED | "and/or" + `GateManifest` |
| 47 | receipts/2026-08-10-packet05aii/REPORT-adversary-05a-ii.md:432 | UNRELATED | "AST/source guard" |
| 48 | receipts/2026-08-12-packet06a/REPORT-coldaudit-honesty-06a.md:17 | HISTORICAL | receipt citing the MEMORY landmine (my first pass said UNRELATED off a truncated line; re-read and corrected) |
| 49 | receipts/2026-08-16-packet59/REPORT-lead-59.md:146 | HISTORICAL | receipt |
| 50 | receipts/2026-08-16-packet59/REPORT-sweep-59.md:319 | UNRELATED | "signature/source" |
| 51 | receipts/2026-08-17-packet07/DESIGN-sidecar-144-posture.md:115 | UNRELATED | "signature/source" |
| 52 | receipts/2026-08-17-regression-fix/REPORT-regr-fixer.md:68 | UNRELATED | "SERVER-si…/source" wording |
| 53 | receipts/2026-08-20-packet48/REPORT-build-48b.md:11 | UNRELATED | substring in a packages line |
| 54 | receipts/2026-08-20-packet48/REPORT-builder-48b.md:11 | UNRELATED | same |
| 55 | receipts/2026-08-24-packet62/REPORT-adversary-62w2.md:293 | UNRELATED | "package/source considered" |
| 56 | receipts/2026-09-04-packet63b/REPORT-contract-63b-i-b.md:52 | UNRELATED | `labels/source/expires_at` |
| 57 | receipts/2026-09-09-packet63b-ib/REPORT-lead-63b-s2.md:58 | HISTORICAL | receipt |
| 58 | receipts/2026-09-12-packet63b-ii-b/REPORT-contract-63b-ii-b.md:98 | UNRELATED | "AST/source pin" |
| 59 | receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:110 | HISTORICAL | captured boot log |
| 60 | receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:111 | HISTORICAL | captured boot log |
| 61 | receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:112 | HISTORICAL | captured boot log |
| 62 | receipts/2026-10-04-531-536/REPORT-fix531.md:190 | UNRELATED | path `loremaster/source/…` |
| 63 | loremaster/loremaster/source/snapshot.py:9 | LIVE-FIXED | my docstring |
| 64 | loremaster/tests/test_config.py:96 | UNRELATED-but-FLAGGED | odoo-extension fixture value `"installed_modules_file": "/source/installed.txt"`. It is a config-parse fixture, not a mount claim, but it models an Odoo deployment reading from `/source`, which no container mounts any more. Outside my set. Flagged for packet 25 (Odoo onboarding) |
| 65 | loremaster/tests/test_config.py:305 | UNRELATED-but-FLAGGED | same fixture's assertion |
| 66 | loremaster/tests/test_mcp_server.py:1719 | UNRELATED | "auto/summary/source" |
| 67 | loremaster/tests/test_memory_replay_fidelity_63b_ib.py:9 | UNRELATED | `labels/source/expires_at` |
| 68 | loremaster/tests/test_render_slot_inventory.py:168 | UNRELATED | "store/source-minted" |
| 69 | loremaster/tests/test_search.py:2870 | UNRELATED | "summary/source/auto" |
| 70 | loremaster/tests/test_source.py:7 | LIVE-FIXED | my docstring |
| 71 | lorescribe/tests/test_astroid_parse.py:828 | UNRELATED | "chunk_type/source's" |
| 72 | loresigil/loresigil/data/voyage4_tokenizer.json:54621 | UNRELATED | tokenizer vocab entry |
| 73 | loresigil/loresigil/data/voyage4_tokenizer.json:96938 | UNRELATED | vocab `/sources` |
| 74 | skills/lore-deploy/references/lifecycle.md:20 | LIVE-FIXED | my rewrite |
| 75 | skills/lore-deploy/references/lifecycle.md:21 | LIVE-FIXED | my rewrite |
| 76 | skills/lore-deploy/scripts/lore_deploy.py:662 | LIVE (owned elsewhere) | `_launch_container` docstring. DO-NOT-TOUCH for me; plan step 3 gives it to the implementer. Lead: confirm it changes in the fix commit |
| 77 | skills/lore-deploy/scripts/lore_deploy.py:684 | LIVE (owned elsewhere) | the bind itself, i.e. the production change the implementer is building. At sweep time it still read `:/source:ro`, so the fix had not landed in this tree yet |
| 78 | skills/lore-deploy/scripts/test_lore_deploy.py:39 | LIVE (owned elsewhere) | test comment; contract/implementer own it (plan lists it) |
| 79 | skills/lore-deploy/scripts/test_lore_deploy.py:219 | LIVE (owned elsewhere) | same |

Counts (recounted row by row): LIVE-FIXED 15 · HISTORICAL 26 · UNRELATED 30 (incl. 2 flagged fixture hits, #64/#65) · LIVE-MISSED outside set 2 (#6, #14) · LIVE owned by implementer/contract 4 (#76–79). Sum 79 = hits. LIVE-MISSED inside my set: 1 (#20), fixed.

## 65-cut read-list item 7 (the extra LIVE-MISSED fix, sweep #20)
before: "`lore-lore` runs a HAND-ROLLED `/source` mount (#165/#166) — recreate from the captured `CreateCommand`, **NEVER `lore-deploy start`**"
after: since the #165 stopgap `lore-deploy start` emits the correct single snapshot bind and refuses on a missing host snapshot, so it is the recreate path. Still capture the `CreateCommand` first. The #166 bound still holds (see runbook step 2). `-n 12` line kept.
⚠ Ordering caveat for the lead: that sentence is true only once the implementer's `_launch_container` change lands in the same commit series. At sweep time `lore_deploy.py:684` still emitted `:/source:ro`. If the fix commit slips, this prose commit must not land before it.

## Gate receipt (haiku-runner, RAN line checked = my command)
Command: `cd /home/ejprice/PycharmProjects/lore && uv run ruff check loremaster/loremaster/source/snapshot.py loremaster/loremaster/index/indexer.py loremaster/loremaster/server.py loremaster/tests/test_source.py && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q loremaster/tests/test_source.py -n 4 -p no:cacheprovider`
- Run 1 (2026-10-31 ~16:12Z): EXIT 1. `E501 Line too long (123 > 110) --> loremaster/tests/test_source.py:8:111` came from my rewrap; pytest did not run (`&&` short-circuit).
- Run 2 (after the rewrap fix): EXIT 0 · `All checks passed!` · **`27 passed in 1.26s`** (0 failed, 0 errors).
- Also checked: `git diff -U0 Containerfile` gives changed_lines=31, non_comment=0, so no instruction line was touched. The `.py` diff (34 ± lines) is docstring-only (read in full).

## Flags (everything noticed; operator/lead owns scope)
1. **LIVE-MISSED, outside my set.** `docs/design/2026-07-31-packet39-google-oauth.md:330`. Packet 39 is OPEN. The design's rationale says "#165 is open … a recreate re-mounts `/source` and re-breaks boot, making 'recreate to revoke' actively dangerous". Suggested annotation: `(2026-10-31: the #165 stopgap removed the /source re-break, so a plain recreate is safe. A recreate that coincides with a static-tier version bump or rebuild_all still crashes boot (#166), so the roster-outside-the-image ruling stands on its other ground: operational data, not deploy config.)`
2. **LIVE-MISSED, outside my set.** `docs/plans/v2/11c-index-boot-reconcile-honesty.md:80`. 11c is OPEN. Scope-OUT label "#165/#166 (the hand-rolled `/source` mount)". Suggested: "#165 (stopgap 2026-10-31) / #166 (in-container static-tier re-acquire bound)".
3. **Fixture modelling a dead path.** `loremaster/tests/test_config.py:96,305` uses `"installed_modules_file": "/source/installed.txt"` for the odoo extension. It is not a mount claim, but it is the only example of an Odoo config, and it points at a path no container mounts. Worth raising at packet 25 (Odoo onboarding).
4. **Adjacent stale prose I did NOT change (not in the brief's site list).**
   - `snapshot.py` `SnapshotLayout.snapshot_root` property docstring: "materialised/served under".
   - `snapshot.py` module docstring: "the file-serving boundary".
   - `read_file.py` module docstring.

   All describe `ReadFileTool`, which is never constructed in production (lore_read is store-backed via `StoreReadTool`). "Served" is true of that class but not of the live server. It is unrelated to `/source`, so I left it. Ask: is `ReadFileTool` dead code to dispose of, or a dormant fallback?
5. **The one-implementation root, re-confirmed in passing.** The snapshot path is written literally in the Containerfile comments, lifecycle.md, lore_deploy.py `SNAPSHOT_ROOT`, and `server._DEFAULT_SNAPSHOT_ROOT`. My prose names `_DEFAULT_SNAPSHOT_ROOT` as the authority instead of adding another free-standing literal, but the docs still spell the path out. This is D2-flag 4 of the plan, already queued.
6. **Indexer docstring scope (MEDIUM).** I wrote "an in-container re-acquire cannot write it (KNOWN BOUND #166)", which names only the `:ro` half of the bound. The unmounted corpora `source:` paths are the other half. The fuller statement is in the Containerfile, lifecycle.md and INDEX.

## Follow-up (lore_comms #18002 · ruling `docs/plans/v2/receipts/2026-10-31-165/RULING-prose-followup.md`, 2026-10-31)
Applied Flags 1, 2 and 6. Flags 3, 4 and D2 stay with the lead, per the ruling.
| flag | site | before | after |
|---|---|---|---|
| 1 | `docs/design/2026-07-31-packet39-google-oauth.md` (after the "#165 is open … re-mounts `/source` … actively dangerous" sentence, ~331) | (no note) | ANNOTATION appended: "(2026-10-31: the #165 stopgap removed the `/source` re-break, so a plain recreate is safe. A recreate that coincides with a static-tier version bump or `rebuild_all` still crashes boot (#166), so the roster-outside-the-image ruling stands on its other ground: operational data, not deploy config.)" The original sentence is kept. |
| 2 | `docs/plans/v2/11c-index-boot-reconcile-honesty.md` §Scope OUT (~80) | "#165/#166 (the hand-rolled `/source` mount)" | "#165 (stopgap 2026-10-31) / #166 (in-container static-tier re-acquire bound)" |
| 6 | `loremaster/loremaster/index/indexer.py` `Indexer` Args `snapshot_root` | "…so an in-container re-acquire cannot write it (KNOWN BOUND #166)." (named only the `:ro` half) | "…the `:ro` bind at `loremaster.server._DEFAULT_SNAPSHOT_ROOT`. KNOWN BOUND #166: an in-container re-acquire of a static tier cannot succeed, because the corpora `source:` paths are not mounted AND this snapshot bind is `:ro`." |

Gate (haiku-runner; `indexer.py` was already in the original ruff list, so the command is unchanged):
- 1st follow-up runner: its RAN line omitted the `cd …lore &&` prefix, and the log it cited does not exist on disk (`ls`: No such file). **Discarded**, per the RAN-line rule.
- 2nd runner, briefed with a fixed log path: RAN = my command verbatim (in a subshell, teed to `/var/tmp/claude-1000/prose-165-followup-gate.log`). I read that log myself (mtime 2026-10-31T16:16:57Z, after the edits): `All checks passed!` · **`27 passed in 1.22s`** · `EXIT=0`.
- Flag 6 is docstring-only (diff read). Flags 1 and 2 are doc-only.
Fan-out (cumulative): haiku 5 (1 worker, 4 runners; 1 discarded) · sonnet 0 · peak 2.
