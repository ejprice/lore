> Provenance: verbatim content of REPORT-scout-13-1.md (scout-13-1, opus, P8c,
> 2026-07-04), preserved by the P8c lead after the pre-build REPORT purge deleted
> the repo-root original. Lead spot-verified 4 of its load-bearing claims against
> on-disk source before delivery (one benign citation slip: watcher rows omit the
> index/ path segment).
>
> **OPERATOR RULING (2026-07-05): ACCEPTED AS-IS** — all dispositions adopted
> wholesale; the 5 derive-at-boot items + the validate-against-reality set + the
> 9-dead-field cleanup are the approved P8e/P8f work list, hazard guards binding
> as written. (Scaffold-defect routing not separately ruled — defaults to the P8e
> scaffold rework window.)

# REPORT-scout-13-1 — Config-dynamism disposition table (ledger #13, P8c)

**Scope:** every configurable field of `LoreConfig` and its nested models (`loremaster/loremaster/config.py`), plus the prospective `anthropic:` block. Disposition ∈ { **derive-at-boot**, **validate-against-reality**, **must-stay-config** }. The operator strikes this table; approved rows implement in P8e/P8f. I implemented nothing.

**Method note (dogfood, honest scope):** lore's structural graph (`lore_references` / `lore_what_imports` / `lore_get_symbol`) answers symbol-level questions but **cannot enumerate attribute reads** like `config.embedding.dim` — a pydantic field is not a referenceable symbol. Both consumption-site scouts and I **fell back to `grep -rn "config.<field>"`** over `loremaster/`, `loresigil/`, `lorescribe/` (excluding tests + config.py). Filed as **finding #3** (`lore_references`, capability_gap). Every file:line below was read against on-disk text.

**Headline:** **9 fields are consumed NOWHERE in production** (dead config, flagged `⚰️ DEAD` in the rationale). Static config rots exactly as the DI 3,394-inotify-watch incident predicted; several fields are pure schema-fingerprint ballast.

---

## Disposition table

| field | current source (yaml key) | consumed by (module.symbol @ file:line) | disposition | rationale | risk-if-derived-wrong |
|---|---|---|---|---|---|
| `schema_version` | `schema_version` | ⚰️ none — only `EMBEDDING_SCHEMA_VERSION` (schema.py:123) is unrelated | validate-against-reality | Required `int`, validated at load, **read nowhere**. Boot should assert it equals the supported version and complain on drift; today a stale/future value passes silently. | Low — mislabels compatibility if enforced against a wrong constant. |
| `project.slug` | `project.slug` | `Indexer` @ index/indexer.py:416; `{slug}.db` @ server.py:3312; `lore-{slug}` container @ server.py:3341; `effective_surreal_database` @ config.py:542 | **must-stay-config** ⚠️ | Durable IDENTITY: SurrealDB database name + on-disk state-DB paths + container name. Scaffold SEEDS it from the dir name (fine), but it must FREEZE after first index. `SLUG_PATTERN` (hyphen ban) already guards the charset. | **HAZARD** — a silently re-derived slug points at the wrong DB/collection ⇒ cross-project leak or clobber. Never auto-derive post-onboarding. |
| `project.root` | `project.root` | `Scout.from_config` @ scout.py:541; server.py:2627; `effective_roots` @ config.py:528 | validate-against-reality | Almost always `.` (the lore.yaml's own dir). Boot should confirm the dir exists and is the intended repo root. | Medium — a wrong root indexes the wrong tree or nothing. |
| `embedding.backend` | `embedding.backend` | `to_loresigil_config` @ embedding.py:60 (factory dispatch) | must-stay-config | Operator chooses the implementation (tei / voyage-cloud / voyage-context). | — |
| `embedding.base_url` | `embedding.base_url` | `to_loresigil_config` @ embedding.py:61; probe-fail msg server.py:1177 | must-stay-config | Service location; **already validated** by the live `run_probe_gate` (server.py:1170) reaching it. | — |
| `embedding.endpoint` | `embedding.endpoint` | `to_loresigil_config` @ embedding.py:62 | must-stay-config | Endpoint path; operator/service topology. | — |
| `embedding.model` | `embedding.model` | `to_loresigil_config` @ embedding.py:68; fingerprint schema.py:125 | validate-against-reality | The name of the served model. TEI `/info` exposes `model_id`; boot could compare. **Today only `dim` is probe-checked, not the model name.** | **HAZARD** — a wrong model with the RIGHT dim passes the probe gate and silently serves wrong embeddings. |
| `embedding.dim` | `embedding.dim` | `run_probe_gate` @ server.py:1168–1187 (REFUSES on mismatch); embedding.py:64/65; fingerprint schema.py:126 | **validate-against-reality** ✅ | **Best-in-class exemplar** — probes the live endpoint and refuses to start on a dim mismatch. Can't be purely derived: voyage Matryoshka dim is an operator choice. | Gate already prevents corruption. |
| `embedding.max_input_tokens` | `embedding.max_input_tokens` | `to_loresigil_config` @ embedding.py:66 | validate-against-reality | Hard token cap. TEI `/info` exposes `max_input_length`; boot could compare and warn. | Medium — over-config ⇒ 422s at index; under-config ⇒ needless truncation of eligible chunks. |
| `embedding.max_batch_texts` | `embedding.max_batch_texts` | `to_loresigil_config` @ embedding.py:67 | validate-against-reality | Client batch size. TEI `/info` exposes `max_client_batch_size`; boot could clamp/warn. | Low — over-config ⇒ batch 413s. |
| `embedding.concurrency` | `embedding.concurrency` | `to_loresigil_config` @ embedding.py:69 | must-stay-config | Pure client tuning knob. | — |
| `embedding.connect_timeout_s` | `embedding.connect_timeout_s` | ⚰️ none — NOT in the `to_loresigil_config` copy (embedding.py:60–71); factory uses its own default | must-stay-config *(or remove)* | **⚰️ DEAD.** Docstring claims "connect timeout for the startup probe" but the value never reaches the factory/probe. Either wire it or delete it. | — |
| `embedding.api_key_env` | `embedding.api_key_env` | `to_loresigil_config` @ embedding.py:63; probe msg server.py:1178 | must-stay-config | Secret indirection (env-var NAME only). | — |
| `embedding.tokenizer` | `embedding.tokenizer` | ⚰️ fingerprint only @ schema.py:129 | **derive-at-boot** *(or remove)* | **⚰️ DEAD functionally** — only hashed into the schema fingerprint; no token-counting consumer reads it (loresigil derives its tokenizer from `model`). Derive from `model` or drop. | Low — if wired, a wrong tokenizer skews token counts. |
| `embedding.truncate` | `embedding.truncate` | ⚰️ fingerprint only @ schema.py:130 | **derive-at-boot** *(or must-stay-informational)* | **⚰️ DEAD functionally** — fingerprint-only; the real truncate behavior is server-side (TEI ⇒ hard 422). Derivable from `backend` (tei ⇒ false). | Low. |
| `embedding.query_prompt_name` | `embedding.query_prompt_name` | `to_loresigil_config` @ embedding.py:70; fingerprint schema.py:131 | validate-against-reality | Asymmetric-retrieval prompt name. TEI `/info` exposes configured prompt names; boot could verify the name exists on the endpoint. | **HAZARD-ish** — a typo'd prompt name silently degrades retrieval quality (no error). |
| `embedding.document_prompt_name` | `embedding.document_prompt_name` | `to_loresigil_config` @ embedding.py:71; fingerprint schema.py:132 | validate-against-reality | Same as above, for index-time document embedding. | **HAZARD-ish** — silent asymmetry break; a prompt drift also invalidates already-indexed vectors. |
| `embedding.batch.mode` | `embedding.batch.mode` | `Indexer._sweep_uses_batch_dispatch` @ index/indexer.py:1188/1228 | must-stay-config | Operator dispatch policy (realtime / batch / auto). | — |
| `embedding.batch.chunk_count_threshold` | `embedding.batch.chunk_count_threshold` | `Indexer` auto-dispatch @ index/indexer.py:1229 | must-stay-config | Tuning threshold for auto batch. | — |
| `embedding.batch.poll_interval_s` | `embedding.batch.poll_interval_s` | `Indexer._run_batch_pass_two` @ index/indexer.py:1487 | must-stay-config | Default is ALREADY sourced from loresigil's `DEFAULT_POLL_INTERVAL_S` (config.py:147) — the derived-default pattern done right. | — |
| `surreal.url` | `surreal.url` | `Scout.from_config` @ scout.py:544; cli.py:120; server.py:2559 | must-stay-config | Store RPC location; validated by the boot connection failing loudly. | — |
| `surreal.namespace` | `surreal.namespace` | `Scout.from_config` @ scout.py:545; cli.py:121; server.py:2560 | must-stay-config | Topology; default `"lore"` already. | — |
| `surreal.database` | `surreal.database` | via `effective_surreal_database` @ config.py:534–542 (→ scout.py:540, server.py:2557, cli.py:111) | **derive-at-boot** ✅ | **Proven exemplar** — `None` ⇒ derives from `project.slug`. The template for other derive-at-boot rows. | **HAZARD if mis-derived** — a wrong DB name = cross-project leak; slug charset guard is the protection. |
| `surreal.user_env` | `surreal.user_env` | `Scout.from_config` @ scout.py:538 (resolve_secret); cli.py:109; server.py:2555 | must-stay-config | Secret indirection. | — |
| `surreal.password_env` | `surreal.password_env` | `Scout.from_config` @ scout.py:539 (resolve_secret); cli.py:110; server.py:2556 | must-stay-config | Secret indirection. | — |
| `roots` | `roots` | `effective_roots` @ config.py:501; iterated everywhere (indexer.py:150, reconcile.py:139, watcher.py:641, cli.py:160) | must-stay-config | Tier topology / freshness policy. Empty ⇒ single-tree LIVE root synthesised (config.py:522–531) — a derive-at-boot fallback already shipped. | Medium — wrong roots index the wrong trees. |
| `roots[].tier` | `roots[].tier` | `reconcile.files_for_tier` @ reconcile.py:238; cli.py:160; indexer/server | must-stay-config | First-class partition key (records/manifest/store/graph partition by it). | **HAZARD** — a tier RENAME orphans every record under the old tier. |
| `roots[].watch` | `roots[].watch` | `indexer` @ indexer.py:151 (`== WATCH_LIVE`); reconcile.py:233; watcher.py:641 | must-stay-config | Freshness policy (live vs static). | — |
| `roots[].path` | `roots[].path` | `watcher.watched_paths` @ watcher.py:676; reconcile.py:236; indexer.py:152 | validate-against-reality | Live-root disk location. Boot should confirm it exists. | Medium — a stale path silently indexes/watches nothing. |
| `roots[].source` | `roots[].source` | `_build_source_providers` @ server.py:2953; cli.py:93 | validate-against-reality | Static-root materialisation source. Should exist at rebuild. | Medium. |
| `roots[].version` | `roots[].version` | `indexer` @ indexer.py:993/1018/1285/1303/1333 (version-stamp rebuild trigger) | must-stay-config | Operator's rebuild trigger for a static tier. | — |
| `roots[].provider` | `roots[].provider` | ⚰️ none — provider is selected by extension registration else default `LocalDirectorySourceProvider` keyed on `source` | must-stay-config *(or remove)* | **⚰️ DEAD.** Required on static roots by `_check_policy_fields` (config.py:307) but **never read** — selection ignores it. Either wire it or drop it from the required set. | — |
| `roots[].include` | `roots[].include` | `is_included` @ index/paths.py:53,55 | must-stay-config | Per-root scope. | — |
| `roots[].exclude` | `roots[].exclude` | `is_included` @ index/paths.py:50 | must-stay-config | Per-root scope. | — |
| `include` | `include` | `effective_roots` @ config.py:529 → `root.include` in `is_included` (paths.py:55) | must-stay-config | Single-tree scope; scaffold seeds a code/docs default. Operator scope choice. | Medium — too-broad indexes junk; too-narrow misses source. |
| `exclude_dirs` | `exclude_dirs` | `walked_dirs` @ index/paths.py:74 (basename prune); `watcher._dir_excluded` @ watcher.py:737; `watcher._resolve` @ watcher.py:1110 | **derive-at-boot** 🎯 | **P8e candidate — venv+binary-dir heuristic.** Basename-only prune; scaffold seeds from `.gitignore`. The DI rot (missing `.venv` ⇒ 3,394 inotify watches) is THIS field going stale. Boot should auto-detect venv / `__pycache__` / `node_modules` / build / VCS dirs additively. | **HAZARD** — over-aggressive derivation could exclude a real source dir that *looks* like a build dir ⇒ silently unindexed. Make derivation ADDITIVE to operator config and LOG it. |
| `exclude_globs` | `exclude_globs` | `is_included` @ index/paths.py:50 | must-stay-config | File-glob excludes; some (lockfiles/minified) derivable, but low-value. | Low. |
| `chunkers` | `chunkers` | ⚰️ fingerprint only @ schema.py:133 — **NOT used for selection** | **derive-at-boot** 🎯 *(or wire the override)* | **P8e candidate — yaml chunker-or-documented-override.** `ChunkerRegistry.dispatch_file` (registry.py:118) selects via hardcoded defaults (`server._register_default_chunkers`) + each chunker's `handles()`; `apply_overrides` EXISTS but is **never called from prod**. The yaml map only feeds the fingerprint. Either derive it from the hardcoded default map (stop shipping misleading config) OR wire `config.chunkers` → `apply_overrides` to make it a real documented override. | **HAZARD-ish** — operator edits `chunkers:` expecting an effect and gets none (only a rebuild from the fingerprint change). If later wired, re-chunking a large static tier is expensive — must be intentional. |
| `watcher.enabled` | `watcher.enabled` | `Scout.start` @ scout.py:686; server.py:2835/2896 | must-stay-config | Gates the live watcher + periodic reconcile. | — |
| `watcher.observer` | `watcher.observer` | ⚰️ none — `LiveWatcher._make_observer` @ watcher.py:714 hardcodes `_OverflowAwareObserver` | **derive-at-boot** *(or remove)* | **⚰️ DEAD.** Field is read nowhere; the observer is hardcoded. Derivable from platform (inotify on Linux) or drop. | — |
| `watcher.debounce_ms` | `watcher.debounce_ms` | `LiveWatcher.__init__` @ watcher.py:639 (÷1000 → seconds) | must-stay-config | Tuning knob. | — |
| `watcher.reconcile_interval_s` | `watcher.reconcile_interval_s` | `Scout.start` @ scout.py:700; server.py:2898 | must-stay-config | Tuning knob. | — |
| `server.host` | `server.host` | `LoreServer.run` @ server.py:768; `_lifespan` @ server.py:3344 | must-stay-config | uvicorn bind host. | — |
| `server.path` | `server.path` | `_lifespan` @ server.py:3346 (FastMCP `streamable_http_path`) | must-stay-config | MCP mount path. | — |
| `server.port` | `server.port` | `LoreServer.run` @ server.py:769; `_lifespan` @ server.py:3345 | validate-against-reality | Scaffold DERIVES it once via `_free_port` (lore_deploy.py:425). Boot could verify it's free / matches `.mcp.json` / the running container. | **HAZARD-ish** — a port collision between projects (topology: lore=9202, DI=9201) crosses wires. |
| `logging.level` | `logging.level` | server.py:1116 (`os.environ.get("LORE_LOG_LEVEL", …)` — env overrides) | must-stay-config | Operator verbosity; env-overridable. | — |
| `logging.format` | `logging.format` | server.py:1117 → `configure_logging(fmt=…)` | must-stay-config | json / keyvalue. | — |
| `logging.destination` | `logging.destination` | ⚰️ none — `configure_logging` (logging_setup.py:216) takes no destination; stderr hardcoded @ logging_setup.py:239 | must-stay-config *(or remove)* | **⚰️ DEAD.** `Literal["stderr"]` pinned to one value AND never read. Cosmetic; drop or wire. | — |
| `search.reranker` | `search.reranker` | `SearchService._maybe_rerank` @ search.py:613 (presence gate) | must-stay-config | Presence-gated seam. **But see next two rows — the block is currently INERT.** | — |
| `search.reranker.url` | `search.reranker.url` | ⚰️ none — no reranker client is built; server.py:2753 hardcodes `reranker=None` | must-stay-config | **⚰️ DEAD.** The gate at search.py:613 also checks `self._reranker is None`, which is ALWAYS None (never constructed). Configuring a reranker block today is a silent no-op. [Lead note: the hardcode carries a P6 comment marking this DELIBERATE seam-only state.] | **HAZARD-ish** — operator configures a reranker and gets nothing, no warning. |
| `search.reranker.model` | `search.reranker.model` | ⚰️ none — same as above | must-stay-config | **⚰️ DEAD** — same reason. | — |
| `auth.enabled` | `auth.enabled` | `build_asgi_app` @ server.py:5063 (`config.auth is not None and config.auth.enabled`) | must-stay-config | Gates BearerAuth wiring. | — |
| `auth.keys` | `auth.keys` | `build_api_key_verifier` @ auth.py:194 | must-stay-config | Rotatable key set. | — |
| `auth.tls_terminated_upstream` | `auth.tls_terminated_upstream` | ⚰️ none — no production read anywhere | must-stay-config *(or remove)* | **⚰️ DEAD.** Documents an assumption (plain HTTP behind TLS ingress) but is read nowhere. Drop or wire into the origin/transport check. | — |
| `auth.keys[].name` | `auth.keys[].name` | auth.py:195 (`resolved[key.name]`) | must-stay-config | Per-identity revocation label. | — |
| `auth.keys[].key_env` | `auth.keys[].key_env` | auth.py:195 (`resolve_secret(key.key_env)`) | must-stay-config | Secret indirection. | — |
| `extensions` | `extensions` | `LoreServer` @ server.py:430 (`config.extensions.get(ext.name, {})`) | must-stay-config | Opaque per-extension pass-through, validated downstream. | — |
| **`anthropic.api_key_env`** *(landed in P8c)* | `anthropic.api_key_env` | `load_config` eager resolve + `build_app_context` engine construction | must-stay-config | Secret indirection for the yardstick/calibration API key. | — |
| **`anthropic.yardstick_model`** *(landed in P8c)* | `anthropic.yardstick_model` | calibration engine `count_tokens` probe | must-stay-config + validate-against-reality | Operator choice, but the calibration engine PROBES it. Boot should confirm the model exists (a retired model 404s — the P8a baseline hit exactly this: `claude-3-7-sonnet` → `NotFoundError 404`). Complain loudly rather than crash calibration. [Lead note: shipped P8c behavior — a 404 is a TerminalCountError: probe stops with a status note, committed constant serves on.] | Medium — a retired/typo'd model breaks calibration; validate at boot, serve cached values + retry per the plan (§P8c). |

---

## Top candidates — 5 highest-value derive-at-boot items

Ranked by value (rot-prevention × blast radius). Note `surreal.database` is already derived — it's the **template**, cited as precedent, not a new item.

1. **`exclude_dirs` — venv + binary-dir + VCS auto-detection** (P8e). The single field whose staleness caused the DI 3,394-inotify-watch incident. Boot auto-detects `.venv`/`venv`/`__pycache__`/`node_modules`/`.git`/`target`/`build`/`dist` and folds them in ADDITIVELY (never replacing operator entries), then logs the merged set. Highest value: prevents both watch explosions and junk indexing. Pairs with the **path-anchored excludes** P8e item — the basename prune (`walked_dirs`, paths.py:74) can't say "exclude `./build` but keep `src/build`".
2. **`chunkers` — resolve the fingerprint-vs-selection lie** (P8e "yaml chunker-or-documented-override"). Today the yaml map only feeds the schema fingerprint (schema.py:133); selection is hardcoded + `handles()`, and `apply_overrides` is dead. Either DERIVE the block from the hardcoded default map (so the config reflects reality) or WIRE `config.chunkers → apply_overrides` (so editing it does something). Either kills a silent operator foot-gun.
3. **`embedding.tokenizer` — derive from `model`.** Currently fingerprint-only dead config; loresigil already derives the real tokenizer from the model. Deriving (or deleting) removes a field that can silently disagree with the model.
4. **`watcher.observer` — derive from platform.** Dead (hardcoded `_OverflowAwareObserver`). Derive from OS (inotify on Linux) or remove; stops the config from advertising a knob that does nothing.
5. **`embedding.truncate` — derive from `backend`.** Fingerprint-only dead config; TEI ⇒ always false. Derive from backend or make it explicitly informational.

*Honorable mention:* **`server.port`** — the scaffold already free-port-derives it (lore_deploy.py:425); promoting a boot-time "is my port free / does it match `.mcp.json`" check (validate-against-reality) would catch the lore=9202 / DI=9201 collision class.

---

## Hazards — wrong auto-derivation could corrupt an index or leak across projects

| field | hazard | guard / mitigation |
|---|---|---|
| `project.slug` | Re-deriving the slug after first index points state at the WRONG SurrealDB database / collection ⇒ cross-project leak or clobber. It is an IDENTITY, not a setting. | Derive-at-ONBOARD only (seed from dir name), then FREEZE. `SLUG_PATTERN` (hyphen ban, config.py:87) already blocks path/DB-parse hazards. Never re-derive on a live index. |
| `surreal.database` / `surreal.namespace` | A mis-derived DB/namespace name reads/writes another project's data (two-container topology shares one Surreal). | Keep deriving strictly from the frozen slug via `effective_surreal_database`; the slug charset guard is the backstop. Do not add any other derivation source. |
| `embedding.model` | A wrong model with the RIGHT `dim` passes `run_probe_gate` (which only checks dim) and silently serves semantically-wrong embeddings into the same-dim collection ⇒ corrupt retrieval, no error. | VALIDATE (probe TEI `/info` for `model_id`), never derive. Extend the probe gate to compare the model name. |
| `embedding.dim` | A wrong dim silently corrupts retrieval. | Already gated — `run_probe_gate` REFUSES on mismatch (server.py:1180). Keep it validate-not-derive (voyage Matryoshka dim is an operator choice). |
| `embedding.{query,document}_prompt_name` | A typo'd prompt name silently breaks asymmetric retrieval; a drift also invalidates already-indexed document vectors (index/search asymmetry). | Validate against the endpoint's configured prompt names (`/info`); fold into the schema fingerprint so a change forces a rebuild (already fingerprinted, schema.py:131–132). |
| `exclude_dirs` (auto-derived) | Over-aggressive detection excludes a real source dir that looks like a build/venv dir ⇒ that code is silently NOT indexed and search misses it forever. | Make derivation ADDITIVE to operator config (union, never replace), LOG the merged set + the watched-dir count, and require a real directory-shape signal (e.g. `pyvenv.cfg` for venvs) rather than name heuristics alone. |
| `chunkers` (if wired to selection) | Wiring a previously-ignored field changes chunk boundaries; the fingerprint fold (schema.py:133) then triggers a full re-chunk/re-embed of every tier — expensive and surprising on a large static corpus. | Gate behind an explicit operator opt-in; announce the rebuild in `lore_index_status` before executing. |

---

## Cross-coupling to the lore-deploy scaffold (skills/lore-deploy/scripts/lore_deploy.py)

A derive-at-boot disposition changes what the scaffold should template (`_scaffold_lore_yaml`, lore_deploy.py:415–490). Rows that couple:

- **`exclude_dirs`** — scaffold already seeds from `.gitignore` (lore_deploy.py:393–413, 427). A boot-time venv/binary-dir derivation would let the scaffold stop hand-listing these; the two must agree on the always-prune set.
- **`server.port`** — scaffold free-port-derives (lore_deploy.py:425); a boot validate-against-reality check should reconcile with this seed.
- **`chunkers`** — scaffold hardcodes `.py/.md/.sql` (lore_deploy.py:472–475); if the field becomes derive-at-boot, the scaffold should stop emitting it (or emit it as a commented documented-override).
- **`project.slug`** — scaffold seeds from `project.name` (lore_deploy.py:424); this is the correct derive-at-onboard-only pattern — do NOT extend it to boot.

### ⚠️ Adjacent defect found while reading the scaffold (out of #13 scope — raising per policy, operator decides)

`_scaffold_lore_yaml` still emits a **`qdrant:` block** (lore_deploy.py:452–454) and **no `surreal:` block**. Qdrant was retired from the boot path at P8a and there is no `qdrant` field on `LoreConfig`; `_StrictModel` has `extra="forbid"`. So a freshly-scaffolded `lore.yaml` would **fail to parse** against the real model — and the scaffold's own validation line (`_read_config_field(config_path, "c.project.slug")`, lore_deploy.py:490) would raise. **Onboarding a brand-new project via `lore-deploy setup` appears broken today.** [Lead verification: qdrant block + strict no-qdrant-field both CONFIRMED against source.] This is a code bug, not a lore-tool friction, so it's here rather than in the findings ledger — flagging for the operator to route into P8e (the scaffold rework window) or sooner. **Also now needs: template the `anthropic:` block (P8c made it REQUIRED).**

---

*Read-only scout — one file written (this report), no code/config touched, finding #3 filed via `lore_findings`. Preserved to docs/design/ by the P8c lead 2026-07-05.*
