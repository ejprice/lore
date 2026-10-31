# Packet 65 — Hosted-write enablement + JOINT deploy (39 + 60–64 cutover)
wave **D** · lead: **Opus + Fable design sidecar** · size **0.25 → PRE-SPLIT** (65-pre = the
pre-deploy blocker wave [code] · 65-cut = the cutover itself [ops + smoke]; re-price at kickoff —
see §SIZING) · **Depends on:** 39, 60, 61, 62, 63 (63c in progress at authoring), 64 (PLANNED at
authoring), and **11c — a HARD dependency, RULED 2026-09-24 (INDEX pool 29)** (index boot honesty, #355) so the recreate is not a 3–4 h
outage · **DEPLOY: YES** — rebuild + recreate `lore-lore`: THE ONE cutover. It also lands every
commit-only packet since the production image's git ref (48/49, 07 test-only, 39, 60–64, …).

*Authored 2026-09-24 at `d237ad7` by `packetdoc-65` (plan-review session). Every "at authoring"
fact below is dated to that commit; re-derive at kickoff (entry checks assert RELATIVE facts).*

## Mission
Land ~5 weeks of commit-only authorization work onto production in ONE cutover, in the order the
rulings fix, with rollback receipts written before anything irreversible happens: authN (39) +
read-only hosted enforcement + the Keep substrate (60) + the PDP/audit (61) + agent identity (62)
+ the governed retrofit and its **production data migration** (63/64) + **the hosted-write
enablement itself** (this packet's one code deliverable beyond cleanup). Authz model §8 (RULED):
**no 39-alone deploy** — the first hosted deploy is auth + read + row-scoped write together.

## FIRST READS (cite, never re-transcribe)
1. `docs/reference/surrealdb-31-capabilities.md` — **MANDATORY** (store/schema/DDL + a production
   data migration; #107 was a 100% outage whose answer was already in that file).
2. `docs/design/2026-08-21-lore-authorization-model.md` §8 (joint cutover), §3 (identity,
   anti-spoofing), §9 (threat model — the auditor's target).
3. `docs/design/2026-08-28-packet63-retrofit-rulings.md` §2 (per-table migration; **§2.6 the
   cutover ORDER**; §2.2 the project keep `keep.key='project:lore'`; §2.3 the boot NONE-count).
4. `docs/design/2026-08-21-packet39-recut-oauth.md` §6 (config + **posture derivation**), §10
   (kill switches / operator-side), §13 (live proof ladder).
5. `docs/plans/v2/receipts/2026-09-24-lore-cold-boot/README.md` — the 3h48m no-bind cold boot (#355).
6. INDEX Log **2026-08-03 · 04b-2 DEPLOY — ROLLBACK RECEIPTS** + **04b-2 DEPLOYED** — the template
   for a production data-migration deploy; and **2026-08-17 packet 07a DEPLOYED** — the
   candidate + production-CONTROL conformance precedent.
7. Repo `CLAUDE.md` §Deploy + the MEMORY landmines + INDEX Watch list (#165 stopgap, 2026-10-31):
   `lore-deploy start` now emits the correct single snapshot bind (no `/source`) and, before any
   teardown, refuses when any declared static tier is unmaterialised on the host (absent, empty or
   not a directory), so it is the recreate path. Still capture the `CreateCommand` first. The
   #166 bound still holds (an in-container static-tier re-acquire crashes boot), so see the
   runbook step 2 below. Full suites ALONE at `-n 12` (#466).

## ENTRY CHECK (relative facts — STOP and surface on any miss)
- E1. Every dependency's close commit (39, 60, 61a, 61b, 62, 63a, 63b-*, 63c-*, 64-*) is an
  ancestor of HEAD (`git merge-base --is-ancestor <sha> HEAD`). ⚠ At authoring 63c is mid-contract
  and 64 is PLANNED — this packet cannot start until both close.
- E2. `server._GOVERNED_TOOLS_PENDING_OWNER_STAMP` is **EMPTY** — every governed tool routes. At
  authoring it holds **4** entries (`lore_comms`, `lore_tasks`, `lore_claim_task`, `lore_findings`);
  63c drains the first, 64 the other three.
- E3. The #420 per-verb reach pin (`test_governed_routing_63a.py::test_every_governed_verb_is_routed_or_adjudicated`)
  and every #420 leg GREEN; `migrate_governed` supports every governed table (at authoring it
  accepts only `memory`/`agent`/`message` — `brief` lands 63c, `task`/`finding` land 64).
- E4. `uv run python scripts/pending_contract_gate.py --currency` → zero RED_ORPHANED **and**
  `scripts/pending_contracts.yaml` `bounds: []` (no packet-39-owned #333 bound left standing).
- E5. The production image's git ref is an ancestor of HEAD. At authoring: `lore-lore` on
  `localhost/lore:latest` = `4312207128bb`, `LORE_VERSION=0f5f2dc` (verified live 2026-09-24,
  `podman inspect`); `0f5f2dc` IS an ancestor of `d237ad7`.
- E6. **The build tree is CLEAN at a committed HEAD** — the Containerfile bakes the working tree
  and stamps `git describe --always --dirty`; a peer session's uncommitted edits would ship.
  `git status --porcelain` empty over the baked members; `LORE_VERSION` must not end `-dirty`.
- E7. An operator **principal + api key exist in the PROD store** (`lore-adm add` / `mint-key`,
  packet 49) **before** the posture flips — "configure login first, then flip posture" (39 §6).
  ⚠ The single-principal precondition (63 §2.1 `agent` row) means NO second principal may own any
  agent before `migrate-governed --table agent` runs.
- E8. A **fresh** backup taken THIS session (the newest at authoring is
  `/backups/lore/lore-prod-20260803T141930Z.surql` — 7 weeks stale, pre-dating the 3.2.4 engine;
  it is NOT the rollback for this migration).
- E9. Fleet quiescent: no peer lore session mid-suite or mid-write (`ListAgents`, `ps`, `lore_comms
  action=fleet`) — 63 §2.6 assumes the migration runs fleet-quiescent.

## 65-pre — the pre-deploy blocker wave (CODE; one concern per commit; contract → adversary → build → cold audit wherever code changes)
- **P1. HOSTED-WRITE ENABLEMENT (the packet's namesake — ⚠ absent from the pre-split brief this
  file was written from; added by the author).** At authoring `ReadOnlyGuardMiddleware`
  (`loremaster/loremaster/readonly_guard.py`) refuses EVERY mutating tool to every
  `HOSTED_OAUTH` principal (no hosted token carries `lore:write`; `LAN_BEARER` api-key principals
  do). Enabling row-scoped hosted write for the governed population, while shared-corpus writes
  (if any remain) stay refused, is a **property to INVENT** (how the #295 guard composes with the
  PDP for the governed set; what a hosted `member` vs `admin` token carries) → **Fable design
  sidecar rules it; never a builder's call** (roster law). Pins: the 39 §13 negative
  ("write refused-hosted PAIRED with the same tool via api-key") is RE-CUT — it certifies the OLD
  (read-only-hosted) world; the removed-behavior inventory adjudicates it.
- **P2. #396 — `config.auth.keys` MIGRATION-REJECT (BLOCKER).** A stray `keys` block becomes a LOUD
  boot refusal teaching `lore-adm` + `principal_key` (or is migrated into `principal_key` — sidecar
  picks). ADD the missing DUAL pin: a config-key does NOT authenticate under the new wire, paired
  with the positive control that a `principal_key` DOES. (At authoring the repo `lore.yaml` has no
  `auth:` block, so the live harm is latent — but the posture flip WRITES one.)
- **P3. DELETE `ApiKeyVerifier` / `build_api_key_verifier`** (`loremaster/loremaster/auth.py`;
  `lore_impact` at authoring: `build_api_key_verifier` 0 prod refs, `ApiKeyVerifier` consumed only
  by it). Gated on the DUAL inventory: adjudicate each `TestApiKeyVerifierIsPreservedVerbatim`
  behavior against `PrincipalKeyStore.verify` — **constant-time especially** (hash-equality over
  `sha512(name:secret)` vs `hmac.compare_digest` on the raw secret: "preserved-in-different-form"
  WITH a citation, never assumed). Retire those pins WITH the delete (they assert the corpse).
- **P4. #382 — conformance false-GREEN.** `conformance_run.sh` `exec`s pytest and trusts its exit
  code; a crashed/never-ran suite has exited 0. It must parse + assert a real pytest summary (a
  passed-COUNT) and fail loud when absent. (The BLAS-thread half of #382 is already fixed — the
  script sets `OPENBLAS_NUM_THREADS=1`/`OMP_NUM_THREADS=1`.) ⚠ The script hardcodes `-n auto`;
  reconcile with the #466 landmine (`-n 12`, alone) in the same fix.
- **P5. #386 — conformance environment baseline.** Before the gate is trusted, KNOW the expected
  image-only failure set (07a measured ~36–41 env-caused: no env-file, `:ro` mount, host tooling):
  either extend the `LORE_CONFORMANCE_IN_CONTAINER` opt-out to those meta-tests or commit a
  derived baseline the harness diffs against. A gate that is "always non-zero" is not a gate.
- **P6. 63b-ii-b §4.2/§12.8 `:18500` reachability reads** — count over-cap `to.ack_note` /
  `message` rows in PROD (expected 0), READ-ONLY. Folded into the deploy smoke; **MUST run before
  the new drain serves** (a single legacy over-cap `to` edge fails drain's one-statement UPDATE →
  total inbox denial — the DD-3.c class, CLAUDE.md "THE RIDER"). Grounds + controls:
  `receipts/2026-09-12-packet63b-ii-b/REPORT-lead-63b-ii-b.md` §Reachability and
  `REPORT-probe-63b-ii-b.md` LEG C (`DD-3.c: ABORTS-WHOLE`; `ack` HEALS a dirty edge — control C3).
  The design sections this brief called "§4.2/§12.8" were not located by that label (UNVERIFIED).
- **P7. Repo-root hygiene before the image build.** ARCHIVE every root `REPORT-*.md` by `git mv`
  into `receipts/<date>-<packet>/` (never `rm`); sweep stray `test_*.memory.db` / `resume` /
  pointer symlinks. At authoring: 9 root `REPORT-*.md` (all 63c-session), 0 `test_*.memory.db`,
  0 `resume`, 0 root symlinks.
- **P8. #299 — rename the MCP server to a fixed `lore`: OPERATOR DECISION (fork F3).** MCP config
  binds at session start, so the cutover — which re-keys every `.mcp.json` anyway — is the one
  natural acceptance moment. If ratified: `lore-deploy` skill + every `.mcp.json` + docs naming
  `mcp__lore_<slug>__*`; acceptance = a NEW session resolves `mcp__lore__lore_index`.
- **P9. 62's orchestration obligation (docs, not code).** After the cutover every governed call
  presents `capability=` (minted at `register`); a call without it DENIES with a teaching error
  (63 §2.6 step 5). Update `~/.claude/orchestration/brief-base.md` + `lead-base.md` (versioned)
  and the `lore_comms` standing brief, landing WITH the cutover, not after it.
- **P10. Deferred R5 sweep** (63 ruling amendment 2: the owner⇔scope writer invariant) —
  UNVERIFIED which residue remains at 63c close; the kickoff reads 63c's close-out and either
  confirms it discharged or lists it here as fix-before.
- **P11. DRESS REHEARSAL (author's recommendation, unruled — fork F4).** Restore the fresh prod
  backup into a throwaway DB on `ws://127.0.0.1:18000` (the 63 §2.3 S2 idiom, NEVER `:18500`),
  run the CANDIDATE image's full `migrate-governed` sequence + a recall byte-diff against it, then
  boot the ROLLBACK image against the migrated rehearsal DB. The last leg answers a question
  nothing else measures: **can `4312207128bb` serve a post-migration store?** (UNVERIFIED — it
  decides whether image rollback alone is sufficient.)

## 65-cut — THE CUTOVER RUNBOOK (F2 RULED 2026-09-24: a lead may run it UNATTENDED under the preconditions below)
1. **Fresh backup** of `:18500` → `/backups/lore/lore-prod-<UTC>.surql`; record size, table count,
   EXIT=0 (the 04b-2 receipt shape). 3.2.4 is forward-only — the restore engine must be ≥ it.
2. **Capture** `podman inspect lore-lore --format '{{.Config.CreateCommand}}'` NOW (never a stale
   capture); diff it against the known-good shape `lore-deploy start` emits since the #165
   stopgap (2026-10-31): `--network=host --userns=keep-id --user`, `/workspace:ro`, state dir,
   **ONE** snapshot bind `~/docker/mcp/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro`,
   `--env-file`, `LORE_CONFIG`. **No `/source` bind**: nothing reads it. A capture that still shows
   a `/source` bind next to the home-path bind is the pre-stopgap hand-rolled container. It boots,
   but it is stale, so recreate it with `lore-deploy start`. A capture with a `/source` bind and NO
   home-path bind is the #165 crash shape: STOP.
   ⚠ KNOWN BOUND (#166, packet 19): a re-acquire of a static tier inside the container cannot
   succeed (the corpora `source:` paths are unmounted, and the snapshot bind is `:ro`). If this
   cutover bumps a static tier's version or forces `rebuild_all`, boot still crashes. Re-index
   on the host first.
3. **Build** from the clean HEAD (E6): `podman build … --build-arg LORE_VERSION=$(git describe
   --tags --always --dirty)`; the Containerfile runs `uv sync --locked --all-packages`.
4. **In-image conformance** (#139/#140/#131; provenance gate first) against the CANDIDATE **and**
   the production image as a CONTROL (07a precedent), same test tree, run ALONE (#466); judged
   against the P5 baseline with P4's passed-count assertion. Candidate-only reds = STOP.
5. **Tag rollback:** `podman tag 4312207128bb localhost/lore:pre-65-rollback` (or the then-current
   prod id).
6. **Write ROLLBACK RECEIPTS into the INDEX Log BEFORE the recreate** (04b-2 §B6 shape): shipping
   image id + git ref, rollback tag + id, backup path/size, the captured `CreateCommand`, the
   rollback procedure.
7. **P6 reachability reads** against `:18500` (read-only). Non-zero ⇒ STOP (the new drain would
   deny whole inboxes).
8. **Recreate** `lore-lore` from the captured `CreateCommand` verbatim on the new image (NOT
   `lore-deploy start`). Posture at this step = UNCHANGED (loopback) — the flip is step 11.
9. **Boot watch.** Expect the #355 whole-tier cold reindex (~3h48m on 2026-09-24; uvicorn does not
   bind until it finishes, clients need `/mcp` to reconnect) **unless 11c has landed**. Watch for
   the new DDL convergence (the `scope`/`owner_principal` `IF NOT EXISTS` indexes BUILD over every
   existing row once — name the row counts) and the §2.3 per-table `scope IS NONE` WARNING counts.
10. **`lore-adm migrate-governed`** per 63 §2.6's order — **`agent` → `memory` → `message` →
    `brief` → (64's) `task`/`finding`** — preceded by `lore-adm report-unmigrated` per table
    (read-only preview). The `agent` leg's single-principal precondition refuses loud on a
    multi-principal store; the verb refuses `message` before `agent`; a refusal is **byte-inert**
    (verify: a re-read shows no row changed). Second run of each = 0 backfilled (idempotence).
    UNVERIFIED: whether `lore-adm` is on PATH in the image (`podman exec lore-lore lore-adm …`) and
    whether the verb may run before `Application startup complete` (concurrent reconcile writes) —
    default: wait for startup-complete.
11. **Posture flip — "configure login first"**: E7's principal + key exist → write the `auth:`
    block (no `keys:` — P2 now refuses it) + the env-file OAuth vars (client secret via env-ref
    only, 39 §6) → wire every local `.mcp.json` with its per-principal key IN THE SAME STEP (39 §6:
    in `HOSTED_OAUTH` the SDK gates `/mcp` for everyone — an unwired local session 401s) →
    recreate again from the same captured shape. ⚠ A second recreate may re-trigger #355.
12. **Proof ladder** (39 §13 + authz §9): `/.well-known/oauth-protected-resource/mcp` 200 anonymous
    · unauthenticated `POST /mcp` → 401 + `WWW-Authenticate` whose `resource_metadata=` resolves ·
    junk path 404 at the edge · api-key path authenticates · **Google connector flow end-to-end
    (operator-side: hades SNI route, claude.ai connector client secret)** · negatives: no-principal
    denied, different-client token denied · **cross-principal live smoke** (≥2 principals × ≥2
    agents, DISJOINT households — the 63b-iii shape): each sees only its own/household rows, the
    admin control sees all, THE BINDING holds; against PROD read-only where possible, with
    throwaway principals minted and deleted, every write paired with its cleanup receipt.
13. **Served-surface smoke from a FRESH session** (config binds at start): `lore_index` serves the
    new git ref; `lore_recall` of a KNOWN legacy note returns it through the new filter (63 §2.2
    pin, live); a governed call without `capability=` DENIES with the teaching error; with it,
    succeeds.
14. **Close-out:** INDEX rows 39/60–65 → DEPLOYED; ≤5-line Log entry; State of record gains the
    production image id + git ref; ledger rows done; findings resolved with production receipts.

## MANDATORY CONSULTS before any non-local exposure (INDEX watch list)
- **#236** — pre-existing dangling edges survive `ENFORCED`; trigger = the FIRST non-local
  deployment, which this is. Required: a READ-ONLY per-table ghost sweep (a real count — "any number
  before the sweep is a rumour"), then an operator decision on deletion. Never conflate the two.
- **#138** — the exec-seam threat model is "honest developer, not hostile author"; its re-open
  trigger names a hosted deployment. The consult records whether hosted exposure changes who can
  COMMIT (it does not by itself) and says so in the Log.
- **#467** — agent-registry touch-before-deny + foreign-roster enrichment; HARD trigger = this
  cutover; owned by 63c (E1 covers it — verify resolved, not merely acknowledged).

## ROLLBACK
Triggers: candidate-only conformance reds (step 4, pre-recreate — nothing to roll back) · boot
failure or a `migrate-governed` error/partial run · the legacy-note recall returns nothing · any
cross-principal leak or false DENY of an own row · the proof ladder fails at a lore-side rung.
Procedure: `podman rm -f lore-lore` → recreate from the captured `CreateCommand` on
`pre-65-rollback`; if the migration corrupted data, `surreal import` the step-1 backup into
`:18500` (engine ≥3.2.4). Revert every `.mcp.json` and the `auth:` block with the image.
Operator-side kill switches (39 §10): `lore-adm suspend` per principal; whole-service = stop the
edge → `podman stop lore-lore` → remove the hades route → remove the claude.ai connector.
⚠ At authoring there is **no `lore-caddy` user unit** (39 §10 names one); `mcp-caddy.service`
exists — confirm which edge fronts lore before relying on that switch.

## FINDINGS OWNED
| finding | disposition |
|---|---|
| #396 config.keys silent non-auth | **fix-before** (P2) — BLOCKER |
| ApiKeyVerifier orphan (39 residual, #396 body §2) | **fix-before** (P3) |
| #382 conformance false-GREEN | **fix-before** (P4) — the gate step 4 relies on |
| #386 conformance env baseline | **fix-before** (P5) — the criterion step 4 is judged by |
| 63b-ii-b §4.2/§12.8 `:18500` reads | **gate** (P6, cut step 7) |
| #236 / #138 | **gate** (mandatory consults above) |
| #467 | **gate** (E1 — 63c resolves) |
| #355 | **decision** (F1) — 11c before, or plan the outage window |
| #299 fixed `lore` server name | **decision** (F3) |
| deferred R5 sweep | **fix-before or confirm-discharged** (P10) |

## FORKS for the operator (questions)
- **F1.** Run the cutover **after 11c** (a delta boot, minutes) or **before it** (accept a ~4 h
  no-bind window, possibly TWICE — steps 8 and 11)? ~~Recommendation: after, unless 11c slips.~~
  **RULED 2026-09-24 (operator, INDEX pool 29): AFTER 11c — 11c is a hard dependency.**
- **F2.** May the production data migration (step 10) run **unattended**, or must the operator
  attend? The 04b-2 precedent asked exactly this (INDEX Log 2026-08-03) and it was never ruled.
  ~~Recommendation: attended — this one widens visibility for every row.~~ **RULED 2026-09-24
  (operator, INDEX pool 28): UNATTENDED is permitted, under this runbook's preconditions (fresh
  backup · rollback receipts in the Log before the recreate · single-principal precondition ·
  byte-inert refusal). Standing for every future migration deploy.**
- **F3.** Rename the MCP server to a fixed `lore` at this cutover (#299)?
- **F4.** Is the P11 dress rehearsal required? Recommendation: yes — it is the only instrument
  for rollback-compat and for the migration against real row distributions.
- **F5.** Does 65 also land **56** (`lore-dnd` go-live)? The INDEX row 65 says it "ALSO lands the
  commit-only 49/56 batch", but 56 is a different instance gated on 54 (open) and 51–53 (open) —
  the author reads 65 as landing 49 only.

## SIZING
The INDEX prices 65 at 0.25. P1 (a design + build) plus P2–P5 (three contracts) is unlikely to fit
0.25 beside the cutover; the sizing law splits at ≥0.30. Expect 65-pre to split further at kickoff
(e.g. 65-pre-a design+P1, 65-pre-b P2–P5 cleanup) — the lead re-prices before spawning anyone.

## EXIT
All entry checks and 65-pre items green with counts (passed-counts, not exit codes); conformance
candidate vs control diff = baseline only; every `migrate-governed` receipt (scanned / backfilled /
already_migrated / refused) recorded per table; proof ladder + cross-principal smoke + fresh-session
served smoke green with production receipts; consults recorded; INDEX rows 39/60–65 flipped to
DEPLOYED; ≤5-line Log entry; ledger rows done; the production image id + git ref written into the
State of record.
