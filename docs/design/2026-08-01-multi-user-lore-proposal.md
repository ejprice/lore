# Proposal — multi-user lore: principals, tool gating, and scoped memory

**Status:** PROPOSAL, not ruled. Operator requested scoping only ("this is just a
proposal"); no forks are ruled and no contract exists.
**Author:** lead (Opus), 2026-08-01, at `cdec4ca` on `feat/surreal-unification`.
**Provenance:** three parallel read-only explorations of the memory subsystem, the store /
DDL patterns, tool registration, the config surface, the CLI idiom, and odoo-code's
per-user key path. Every claim below carries a `file:symbol` citation; nothing is inherited
un-derived.
**Supersedes:** the working note at `~/.claude/plans/` — an unrecoverable address by
standing law, which is why this doc exists.

---

## Context

Packet 39 (Google OAuth) is contract-complete and committed, but stopped on one open
decision: **finding #296** — the hosted read-only posture could not be defended inside
FastMCP. Four adversary passes, four wrong builds, one root cause: `FastMCP.__init__` calls
`_setup_handlers`, which registers the **bound** method, so anything installed afterwards is
live in-process and **dead on the wire** (WB30 `call_tool` → WB48 dispatch order → WB93
instance attribute → WB100 class attribute).

**This proposal's part 2 resolves #296.** That reframes the request from "more features"
into "the thing that unblocks the packet already in flight."

---

## ⚑ The headline: 2A is the answer to #296

**Verified at SDK source** (`mcp` 1.27.2):
- `FastMCP.list_tools()` → `self._tool_manager.list_tools()` → `list(self._tools.values())`
  (`fastmcp/tools/tool_manager.py:41-43`)
- `FastMCP.call_tool()` → `ToolManager.call_tool` → `get_tool(name)`; a miss raises
  `ToolError(f"Unknown tool: {name}")` (`tool_manager.py:88-93`)
- Both are bound at `__init__` via `_setup_handlers` (`fastmcp/server.py:302-308`) and both
  read `ToolManager._tools` **at call time**.

So a **never-registered** tool is absent from `tools/list` *and* uncallable via `tools/call`,
enforced by the SDK's own code on the handler it bound itself. **There is no handler to
shadow, no dispatch order to author, and no instance attribute involved — the four-door class
cannot recur through this door.** It is the strictly stronger form of packet 39 §7 R13's
data-dependency argument.

⚠ **The nuance that makes it work:** config is **per-deploy**; #296 is **per-principal**. They
reconcile only by running **two processes** — the hosted one's `lore.yaml` simply does not
enable the mutating tools. That is exactly option (a) of #296, and part 2 supplies the config
surface it was missing.

⚠ **One honest bound:** the SDK logs `"Tool '%s' not listed, no validation will be performed"`
and returns a generic `Unknown tool` error (`lowlevel/server.py:486-489`). A disabled tool
therefore teaches the agent nothing about *why*. Under the Consumer Law that is a served-surface
miss — accept it deliberately, or render the disabled set in `instructions`.

---

## Sizing

| # | Item | Size | Real cost sits in |
|---|---|---|---|
| 2 / 2A / 2B | tool enable/disable, default-deny, unlisted | **M–L** | **served prose**, not the SDK |
| 1A | principals in the store | **M** | a well-trodden new-table path |
| 1B | user-management CLI in the image | **S–M** | a template already exists |
| 1C | per-user API keys | **M** | key storage + *not* copying odoo's mint |
| 3A / 3B | user-scoped + system-wide memory | **L** | the SQLite ledger round-trip |

---

## Part 2 — tool enable/disable (do this first)

**Cheap:** `build_mcp_server` already binds `config` (`server.py:7822`), so no signature
change. `_register_extension_tools` is already a `for` loop over `server.tool_specs(...)`
(`server.py:9394-9408`) — a one-line `continue`.

**The three real costs:**

1. **`_register_tools` is 15 hardcoded `@mcp.tool(...)` decorators** (`server.py:7980`–`9256`),
   not a filterable registry, and the decorated functions are **nested closures** over `mcp`
   and `server`. `FastMCP.tool()` applies `add_tool` at definition time, so "register later"
   does not exist. The only DRY spelling is a config-consulting `_tool` indirection replacing
   `mcp.tool` at 15 sites — **one decision point**, not 15 forgettable obligations
   (`TracingFastMCP`'s own docstring, `server.py:7604-7605`, rejects the per-tool shape for
   exactly this reason).
2. **⚠ THE COST CENTRE — served prose.** `_INSTRUCTIONS` (`server.py:1472-1532`) is a
   hand-written module constant naming 14 of 15 tools, interpolated at `server.py:7875`.
   Worse: `test_mcp_server.py::test_every_lore_prefixed_token_in_served_text_is_a_live_tool_name`
   (`:1122-1149`) compares served text against the **runtime registered set** — so disabling
   `lore_impact` reddens on *surviving tools' own descriptions*. `lore_search`'s description
   says *"prefer lore_get_symbol… follow up with lore_read"* (`server.py:7987-7989`).
   **Every tool cross-references its neighbours.** That pin is correct and catching a genuine
   over-claim; it must be **satisfied, not waived**. Instructions *and* descriptions must
   become functions of the enabled set.
3. **~9 pins index `tools[name]` and would `KeyError`** — `test_every_tool_has_a_substantial_description`
   (`:1409`), `test_every_input_field_has_a_description` (`:1540`), both annotation pins
   (`:1698`, `:1707`), `test_the_minimal_args_registry_is_exactly_the_registered_surface`
   (`test_trace_telemetry.py:1172`), and others.

**Typo safety:** the enabled set must be checked against a **declared universe** — reuse
`test_mcp_server.py::_ALL_BUILTIN_TOOL_NAMES` (`:1034`). A bare `list[str]` of names is
un-typo-checkable by pydantic, and a hand-list is the artifact this repo has the most receipts
against.

**2B (stub every method as a commented `allow`)** is nearly free once the section exists and
doubles as the discoverability surface. **Generate it from the universe** so the sample cannot
drift from the code.

⚠ **A door this feature opens.** `_register_extension_tools` guards collisions with
`mcp._tool_manager.get_tool(spec.name) is not None` (`server.py:9396`). Disable a built-in and
an extension may legally claim the name `lore_search`. The guard must check the **declared
universe**, not the registered set.

⚠ **Composition with packet 39.** Part 2 filters *what exists* (static, per-deploy); packet 39
§7 filters *what a principal sees of what exists* (dynamic, per-request) and **explicitly
assumes registration stays full**. Both want to derive `_INSTRUCTIONS`. Resolution: the
partition function's input becomes *the registered set*, and `all_registered_tools()` (§17 R16
part 3) keeps meaning "everything actually registered".

### Recommendation on the default-deny fork
Absent `tools:` section ⇒ **all built-ins**; deny-by-default applies **within** the section.
Literal default-deny (absent ⇒ zero tools) breaks every existing `lore.yaml`, the `_config()`
helper (`test_mcp_server.py:374-420`), and most of `test_mcp_server.py`. The recommended shape
matches `AuthConfig.enabled` (`config.py:353`) and the repo's stated *"an existing `lore.yaml`
still validates"* idiom, and keeps the ~9 `KeyError` pins green untouched — new pins become
purely additive.

---

## Part 1A — principals in the store

**Name it `principal`, not `user`.** `user` collides with SurrealQL's `DEFINE USER`,
`DEFINE ACCESS`, and `_txn.signin_credentials(user=…)` (`store/_txn.py:960`). A grep for
`user` is already noisy, and this repo's rename-sweep discipline (bare anchor-free patterns,
per-hit verdicts) makes that materially expensive.

**Schema** — follow the `floor_measurement`/`floor_head`/`lease` precedent (commit `7acbef4`,
`surreal_schema.py:1801-2120`): a `_PRINCIPAL_FIELD_SPECS` tuple, a `_principal_statements()`
emitter, a `generate_principal_ddl()` slice, an owner class whose `ensure_ready()` calls
`execute_transaction` (**never** `query()` — the SDK validates `statement[0]` only).

Fields: `email` (unique, `_NON_EMPTY_STRING_ASSERT`), `subject`, `display_name`,
`status` (closed domain `active|suspended`, derived `ASSERT $value IN [...]` per
`_TASK_STATUS_ALLOWED`), `expires_at: option<datetime>`, `role` (closed domain
`member|admin`), `created_at`.

**Migration clauses** — `docs/reference/surrealdb-31-capabilities.md` §1.1: TABLE
`IF NOT EXISTS`, FIELD `OVERWRITE`, INDEX `IF NOT EXISTS`; `ALTER` is a trap (§1.3).

**Relations:** leave `finding.created_by` / `task.owner` as free strings. Narrowing an existing
`string` to `record<>` **write-poisons every existing row** (§1.4). Any link is additive
`option<record<principal>>`, or an edge. The asymmetry that decides which: `record<t>` links do
**not** auto-clean on target delete; RELATION edges **do** self-delete. Also §2: `UPDATE` of a
relation edge's `in`/`out` is a **silent no-op** — re-pointing means DELETE + re-`RELATE`.

⚠ **A standing law to argue with, not ignore.** `server.py:7577-7581` forbids mixing identity
vocabularies in one column (*"the same dishonesty as overloading `session` with a transport
id"*). A `principal` table is a **third** vocabulary alongside ledger actors (`created_by`,
`actor`, `owner` — all free strings) and comms agents (`agent`, the only typed identity FK, via
`message.sender: record<agent>`). The design must state explicitly that `principal` is the
*human* vocabulary and that ledger-actor strings are **not** retro-fitted to it.

---

## Part 1B — the management CLI

**No Containerfile change needed.** There is no `ENTRYPOINT`, only
`CMD ["/app/.venv/bin/python", "-m", "loremaster.server"]` (`Containerfile:131`), and every CLI
here is `python -m …` with stdlib argparse (`index/cli.py:1`: *"stdlib argparse, no new dep"*).
A module under `loremaster/loremaster/` is reachable via
`podman exec lore-<slug> /app/.venv/bin/python -m loremaster.principals …` immediately. The
Containerfile comment at `:127-129` already establishes the second-entrypoint precedent.

**Template: `scripts/snapshot_gc.py`** — argparse, async, `--user-env`/`--password-env` (env var
**names**, never values, resolved via `resolve_config_value`/`resolve_secret`), and **strict
dry-run unless `--execute`**. That posture is mandatory for `delete` and `suspend`.

**House idiom to copy exactly:** `main(argv: list[str] | None = None) -> int`, a separate
testable `build_parser()`, `prog=` set to the `-m` name, non-zero exit on failure. ⚠ The
`__main__`-guard-must-be-last law applies (`test_server_entrypoint.py:32`).

**Verbs:** `add`, `list`, `delete`, `suspend`, `unsuspend`, `--expires`. Only `list` is safe by
default.

⚠ **Fix a duplication rather than adding to it.** The store-construction recipe is already
copy-pasted in **three** places — `build_app_context` (`server.py:6750+`),
`index/cli.py::_run` (`:120-178`), and `scout.py::Scout.from_config`. A fourth copy is the ONE
IMPLEMENTATION violation this repo has the most receipts against. **Extract `build_store(config)`
first**, then use it in all four.

---

## Part 1C — per-user API keys

**Take odoo-code's validation shape. Do NOT take its identity mint.**

✅ **Adopt** (`pp-odoo/mcp/src/code_mcp/auth.py::_validate_odoo_api_key`): SHA-512 cache keys,
never store the raw secret, 5-min positive / 1-min negative TTL, split on the **first** colon,
terminal failure (never silently retry as Google — `auth.py:174-184`).

⚠ **Reject the mint.** odoo-code returns `AccessToken(token=…, client_id="odoo_api_key_user",
scopes=["email"])` at `auth.py:265` — a **constant** — and *discards the login it already has in
hand* (`_validate_odoo_api_key` **returns** it). No `subject`, no `claims`. Since the SDK derives
session identity from exactly `client_id` + `claims["iss"]` + `subject`
(`auth/middleware/bearer_auth.py:28-43`), **every keyholder collapses to one identity.** Its own
tests pin `client_id == "odoo_api_key_user"` (`tests/test_auth.py:764`) and assert **nothing**
about `subject` — the collapse is unpinned in both directions. Porting it would *import* #206 and
make it live.

Use packet 39's already-designed mint (`2026-07-31-packet39-google-oauth.md` §4):
`client_id=f"api_key:{name}"`, `subject=name`.

**Storage:** odoo-code stores **no** keys because it delegates to Odoo's `res.users.apikeys` over
stock JSON-RPC. lore has no such authority, so it must store **hashed** keys itself — a
`principal_key` table (hash, label, `created_at`, `expires_at`, `revoked_at`), never plaintext.
The CLI shows the key **once** at mint.

**Revocation must beat the cache.** odoo-code's 5-minute positive TTL is an entirely untested
residual window. Packet 39's R12 already ruled the stronger property (re-check on **every**
verification, no residual window) — apply the same rule here.

---

## Part 3A / 3B — user-scoped and system-wide memory

**Largest risk, and the danger is not where it looks.**

**The cheap part:** an `option<record<principal>>` owner column. Per store-reference §1.4 a new
field on a **populated** table must be `option<>` — which makes **system-wide memories naturally
`owner IS NONE`**, exactly the desired semantics, composing with `_build_recall_filter`'s existing
`IS NONE` idiom (`memory/local.py:918`). Recall gains one predicate:
`(owner IS NONE OR owner = $principal)`.

**⚠ The trap that will bite.** `memory` is written through a **SQLite ledger**
(`memory/ledger.py:35-42`), and `rebuild_embeddings` (`local.py:690-735`) **drops and re-creates
the whole table from that ledger**. Any column not carried in `_ledger_metadata` (`local.py:1091`)
and `_replay_record` (`local.py:1048`) is **silently destroyed on every embedding-schema
rebuild**. Legacy rows have no owner, so the replay default must be "system-wide", stated
explicitly.

**Three more decisions with teeth:**

- **`derive_memory_id(text, refs_stamp)` folds only text + refs** (`memory/backend.py:171`).
  Two users saving identical text collapse to **one row** today. Adding owner to the id changes
  **every existing id**. **Recommendation: do not** — keep ids stable, let the owner column carry
  the scope. If that is wrong, it is a migration, not a tweak.
- **`_reinforce` writes on the read path** (`local.py:931-949`): `lore_recall` UPDATEs every
  returned row's `importance`. So a user's recall would bump a *system-wide* memory's shared
  importance. **Recommendation: system-wide memories are not reinforced by individual recall** —
  otherwise one active user reshapes everyone's ranking.
- **Admin-writes-system-wide (3B)** rides `principal.role`, and its natural home is packet 39's
  already-designed `AuthContext` / `PermissionResolver` seam
  (`permitted: frozenset[str]`) — **not** a new parameter on `lore_remember`. The tool surface is
  identity-free today (`lore_remember` takes `text, refs, metadata, kind, trust, importance,
  supersedes, labels` — no actor), and `server.py:7577-7581` is a law against adding a third
  identity vocabulary at the tool seam.

**Indexing:** there is **no index on `kind` or `labels`** today — those filters ride unindexed
predicates on the two overfetch subqueries. An index on `owner` is `IF NOT EXISTS` and **builds
blocking at the next boot of every store**; make that argument explicitly (the `trace_ts` comment
at `surreal_schema.py:1109-1116` is the precedent) or decline it.

**Note also:** the `memory` table carries **zero ASSERTs** today — unlike `finding` and `task`.
It is the table with no precedent for a closed domain, so a scoping column needing one must clone
`_NON_EMPTY_STRING_ASSERT` (`surreal_schema.py:360`) deliberately.

---

## Sequencing

1. **Part 2** — independent, resolves #296, unblocks packet 39's hosted posture. **Ship first.**
2. **Extract `build_store(config)`** — pay down the 3-way duplication before adding a 4th.
3. **Part 1A** (`principal` table) — the substrate for 1C and 3A.
4. **Part 1B** (CLI) — needs 1A + the factory.
5. **Part 1C** (keys) — needs 1A.
6. **Part 3A/3B** (scoped memory) — needs 1A; largest blast radius; **do last**.

Each is its own packet under the standing process: design → contract → **adversary** → build →
cold audit. Packet 39's history is the argument for not skipping the adversary: it found a real
blocker on **every one of four passes**, including a read-only posture that would have shipped
refusing nothing.

---

## Forks — recommendations only; none is ruled

| # | Fork | Recommendation |
|---|---|---|
| 1 | absent `tools:` ⇒ zero tools, or all built-ins? | **all built-ins**; deny-by-default within the section |
| 2 | does `principal` **replace** R12's roster file? | **Yes.** The 1A request *is* R12's named re-open trigger (*"a second WRITER needing coordination"*); suspend/expiry are richer than a flat list. R12 says this fork is explicitly the operator's. |
| 3 | per-project DB or shared? | **Shared.** Principals are cross-project; every table today lives in `lore_<slug>` (`config.py:668-676`), so this is a new connection topology, not a column. |
| 4 | owner in `derive_memory_id`? | **No** — it rewrites every existing id. |
| 5 | table named `user`? | **No** — `principal`. |

---

## Verification

- **Part 2:** the exact-set pin becomes **parametrised over configs**, both directions — a
  disabled tool is **absent**, not merely "the enabled one is present" (membership-only is the
  WB50/WB72 hole packet 39 already paid for twice). Fixtures must include a **non-trivial
  subset** *and* an **empty** set: a fixture disabling one tool cannot distinguish "the filter
  works" from "the filter drops one hardcoded name". ⚠ The empty-set pin has an anti-vacuity
  hazard — an empty surface makes every downstream subset relation trivially true
  (`test_trace_telemetry.py:1181` already guards this by name). The instructions pin becomes
  **biconditional**: `names(instructions) == registered names`.
- **Store work:** the three-legged idiom — an offline DDL-text pin, a live round-trip pin, and a
  **dirty-store migration pin** (`test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore`,
  `:4855`). ⚠ Write the legacy row under the **OLD** DDL then migrate; a fixture creating its
  "legacy" row after the full DDL cannot see the hazard at all.
- **Memory:** a `rebuild_embeddings` round-trip pin proving `owner` survives the ledger replay,
  plus a legacy-row-replays-as-system-wide pin.
- **Keys:** a revoked key denied on the **next** verification, not after the cache TTL.
- **Gates:** `scripts/typecheck.sh`, `uv run ruff check .`, `uv run pytest -n auto`; live-store
  tests against `ws://127.0.0.1:18000` (**never** `:18500`).
- Mutation-prove every load-bearing pin with expected-RED ids declared from `--collect-only`
  **before** the run; every scratch copy via `./scripts/scratch_copy.sh`, printing
  `loremaster.__file__` as a provenance receipt.
