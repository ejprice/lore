# Packet 48 — Principals substrate: ruled design (`build_store` extraction + the `principal` table)

`brief-base v14 read` · `brief project v7 read`

**Author:** `fable-sidecar-48` (design sidecar, model `fable`), 2026-08-19, at HEAD `9195839`.
**Role:** rules the design MECHANICS the operator delegated (plan §"Forks for Fable at
kickoff"); writes no code/tests. The operator has PRE-DECIDED scope = **schema + store
class + CRUD**, fork-3 = **per-slug now**, table name = **`principal`**, DDL idiom =
**Variant A**. This doc turns those into a contract author's build input.
**Source of truth:** the approved plan (`~/.claude/plans/you-are-going-to-goofy-sunrise.md`),
the packet (`docs/plans/v2/48-principals-substrate.md`), the design input
(`docs/design/2026-08-01-multi-user-lore-proposal.md` §Part 1A + §1B), and store law
(`docs/reference/surrealdb-31-capabilities.md` §1.1/§1.3/§1.4/§2) — CITED, never
re-transcribed.
**Verify-don't-assume:** every field:symbol below was read live at HEAD `9195839` (receipts
in the per-fork sections). Line numbers drift — citations are by SYMBOL.

---

## 0. Ruling summary

| # | Fork | RULING |
|---|---|---|
| 1 | Extraction scope: narrow vs broad | **NARROW.** `build_store(config) -> SurrealStore` owns the cred/db resolution + the 3-site `SurrealStore(...)` construction only; returns an **un-readied** store. The ~10 sibling re-resolvers (incl. `_await_live_connect`) are a separately-motivated future refactor, OUT of 48. |
| 2 | Principal DDL idiom | **Variant A CONFIRMED.** Module-level `_PRINCIPAL_FIELD_SPECS` + `_principal_statements()` FOLDED into global `generate_ddl()`, plus a standalone `generate_principal_ddl()` owned by `PrincipalStore.ensure_ready` via `execute_transaction`. Per-slug DB → this is correct; the shared-DB future is a documented seam (§2). |
| 3 | Field set + closed domains + clause selection | Ruled in §3. `email` required non-empty; **`subject` `option<string>`** (Model B — pre-created-by-email rows carry NONE) with the non-empty ASSERT retained (skipped on NONE); `display_name`/`expires_at` `option<>`; `status ∈ {active,suspended}` DEFAULT `active`; `role ∈ {member,admin}` **DEFAULT `member`** (least-privilege — my ruling, plan left it unspecified); `created_at` `DEFAULT time::now()`. **NEW** principal-specific `_PRINCIPAL_STATUSES`/`_PRINCIPAL_ROLES` tuples (R3), `status`/`role` ASSERTs derived at CALL TIME in the emitter (floor idiom — mutation-provable, not frozen at import; lead ruling A). FIELD=OVERWRITE, TABLE/INDEX=IF NOT EXISTS. |
| 4 | `subject` index: unique vs plain | **UNIQUE (plain, over `option<string>`).** Model B (operator-resolved F1): admin pre-creates by email, 39 fills the OAuth subject on first login. Probe-settled on 3.2.4 (§4): multiple NONE coexist; a duplicate non-NONE subject is rejected on CREATE and on the fill UPDATE. Anchored on `AccessToken.client_id` (R2). |
| 5 | CRUD surface | `PrincipalStore` ships `create` (subject OPTIONAL — email-only creation) / `get_by_subject` / `get_by_email` / `list` / `set_status` / **`set_subject`** (the 39 fill-on-login primitive — NEW fork, ruled YES §5), all routing through the **existing** store seams (`_query`→`run_query`, `ensure_ready`→`execute_transaction`) — NO new query/retry seam (#102/#120). Signatures in §5. 49 owns the CLI + `principal_key`. |
| 6 | Module docstring standing-law clause | Exact wording ruled in §6. |

**Escalation flags for the lead/operator (§7):** **F1 is RESOLVED** (operator → Model B;
the subject `option<string>` UNIQUE mechanics are probe-settled). No open operator-level
fork remains. The new `set_subject` fork is ruled YES (§5), with the fill-once-vs-overwrite
ORCHESTRATION named as a 39 policy. Nothing here blocks 48.

**Packages considered:** none — no new mechanism. Every 48 mechanism reuses INTERNAL lore
seams (`SurrealStore`, `run_query`, `execute_transaction`, `bootstrap_session`, the
`_define_*` DDL helpers, the `FindingLedger` owner idiom). This is store-layer machinery
the fastmcp framework never covered (plan §"Hand-roll audit"); there is no package to
prefer. The DRY discipline is *routing through existing seams*, enforced by §5's mutation
proofs.

---

## 1. Fork 1 — extraction scope: NARROW

**Ruling: NARROW.** `build_store(config)` owns exactly the credential/db resolution + the
`SurrealStore(...)` construction that is copy-pasted, byte-identical, at three sites.

### The three sites (read live, HEAD `9195839`)
All three are preceded by the identical recipe and construct with the identical 6-arg call:

```python
surreal_user = resolve_config_value(config.surreal.user_env)      # config.resolve_config_value
surreal_password = resolve_secret(config.surreal.password_env)    # config.resolve_secret
database = config.effective_surreal_database                      # config.LoreConfig.effective_surreal_database
store = SurrealStore(
    url=config.surreal.url,
    namespace=config.surreal.namespace,
    database=database,
    dim=config.embedding.dim,
    user=surreal_user,
    password=surreal_password,
)
```

- `server.build_app_context` — the `write_store` construction (readied on the
  `write_stack_readied` rail).
- `index.cli._run` — readied (`store.ensure_ready()`).
- `scout.Scout.from_config` — construction ONLY, deliberately **NOT** readied.

`SurrealStore.__init__` is keyword-only: `(*, url, namespace, database, dim, user, password,
analyzer_name=DEFAULT_ANALYZER_NAME, entity_tables=())`. The three sites all use the ctor
defaults for `analyzer_name`/`entity_tables`; `build_app_context` registers entity tables
*after* construction via `write_store.register_entity_tables(...)`, not through the ctor —
so `build_store` constructs with the 6 core args and leaves the two defaults alone.

### Ruled signature + readiness contract

```python
def build_store(config: LoreConfig) -> SurrealStore:
    """Construct the unified SurrealDB write store from config. UN-READIED.

    The single factory for the store-construction recipe copy-pasted at three
    sites (server.build_app_context / index.cli._run / scout.Scout.from_config).
    Returns a store on which the caller decides readiness — build_app_context and
    index.cli._run call ensure_ready(); Scout.from_config does not. Reads the
    ALREADY-VALIDATED config.surreal.url (config._reject_url_userinfo rejected any
    inline credentials at load, R4/security-59 F1) — this factory never parses or
    handles credentials in the URL.
    """
```

- **Returns un-readied.** Matches all three sites (two ready, one does not). The factory
  never calls `ensure_ready()`; readiness stays the caller's decision. This is the (1)
  variance the ground-truth named, resolved toward "caller readies".
- **R4 pinned:** `build_store` reads `config.surreal.url` and passes it through untouched —
  no `urlparse`, no userinfo handling. The credential-in-URL rejection lives upstream in
  `config._reject_url_userinfo`; `build_store` inherits it for free. Contract pins that
  `build_store`'s body contains no URL-credential parsing (a regression guard).
- **R5 caller chain (server site):** post-fastmcp-3x, the write_store builds under the
  native `lifespan=` via `build_mcp_server`'s lifespan → `_eager_build_with_retry` →
  `build_app_context`. Cite THIS chain in the server-site mutation proof, not the deleted
  `_EagerStartupLifespan`.

### Why not broad
The broad option would also return a `SurrealConnection` bundle so the cred/db tuple stops
being re-resolved by the ~10 siblings. That is a REAL duplication (measured: `SurrealManifest`
and `SurrealCodeGraph` re-take `user`/`password`/`database` at both `scout.Scout.from_config`
and `index.cli._run`; `AppContext._await_live_connect` re-resolves the whole tuple to feed
`scout._open_command_connection`). But it widens the blast radius across ~10 backends and two
connection topologies for a packet sized 0.20–0.25 wu whose point is the `principal` table.
**NARROW pays down the exact duplication the packet names** (the 4th `SurrealStore` copy 49's
CLI would otherwise add) without the sprawl. The broad refactor is ledgered as a future item
with a concrete address: the re-resolvers above.

### Where `build_store` lives
**Recommended: `loremaster/store/surreal.py`, beside `SurrealStore`** (the natural home;
mirrors `make_embedder_from_config` living in `loremaster.embedding`). It imports the config
resolvers (`resolve_config_value`, `resolve_secret`) — the three call sites already import
them freely, so no cycle is expected. **Contract-author check:** confirm `config.py` does
not import `store.surreal` (no cycle); if it does, put `build_store` in a new tiny
`loremaster/store/factory.py` instead. Placement is cosmetic — the mutation-proof target is
what `build_store` OWNS, not where it sits.

### Mutation proof (the sharing proof)
Change what `build_store` resolves — e.g. the resolved `database` (or `dim`) — inside
`build_store` ONLY, and **every** caller's store pin must redden: `build_app_context`'s
`write_store`, `index.cli._run`'s `store`, `Scout.from_config`'s `store`. A caller that
kept its own inline construction would stay green — that green is the ROUTING-IS-NOT-SHARING
tell. Declare the expected-RED node ids from `pytest --collect-only` BEFORE the run
(`scripts/mutation_proof.py`, diffed both ways).

---

## 2. Fork 2 — DDL idiom: Variant A CONFIRMED

**Ruling: Variant A** (the `finding`/`task` idiom), exactly as the operator locked. The
mechanics, grounded in the live precedents:

- `_PRINCIPAL_FIELD_SPECS` — module-level `(name, type_expr, constraint)` tuple in
  `store/surreal_schema.py`, beside `_FINDING_FIELD_SPECS`.
- `_principal_statements() -> list[str]` — emits the SCHEMAFULL table + one `DEFINE FIELD`
  per spec + the two UNIQUE indexes. Clones `_finding_statements` structurally.
- `generate_principal_ddl() -> str` — the standalone slice, beside `generate_finding_ddl`.
- **Fold `_principal_statements()` into global `generate_ddl()`** (add the line after
  `_finding_statements()` / `_finding_counter_statements()`), exactly as `finding` and
  `task` are folded. This is what distinguishes Variant A (in global) from Variant B
  (`floor`/`lease`/`agent` — standalone only, NOT in global `generate_ddl`).
- `PrincipalStore.ensure_ready()` applies `generate_principal_ddl()` via
  `execute_transaction` (never `query()` — store law §3 validates statement[0] only).

### WHO creates the table, and WHEN (the point of the fold)
The fold makes the table exist in production the moment 48 ships, without 48 needing to wire
a `PrincipalStore` into `build_app_context`: the primary `write_store.ensure_ready()` applies
the full `generate_ddl()`, principal included. The **standalone** `generate_principal_ddl()`
is what the LIVE ROUND-TRIP test and 49's CLI use when they operate a `PrincipalStore` on its
OWN connection. This is precisely the `finding` pattern (in `generate_ddl` AND applied
standalone by `FindingLedger.ensure_ready`). Consequence, ruled: **48 need NOT wire
`PrincipalStore` into `build_app_context`** — the fold guarantees the table; wiring the store
in is deferred to its first consumer (39/49). (If the lead wants it live-and-wired now, that
is a cheap add; flagged, not blocking.)

### Per-slug now → Variant A is correct; the shared-DB future is a documented seam
Per-slug (fork-3): the store connects to `config.effective_surreal_database` =
`self.surreal.database or self.project.slug`. Folding into `generate_ddl()` puts `principal`
in the same per-slug DB as every other table — consistent, and an empty `principal` table on
projects that never use auth is harmless (same as `finding`/`task` today).

**The shared-DB future seam (documented, NOT built — YAGNI, one instance):** if principals
later move to a fixed SHARED database while everything else stays per-slug, the change is
bounded and known: (a) `build_store` gains a keyword `database: str | None = None`
(`database or config.effective_surreal_database`) — purely additive to today's signature; a
`PrincipalStore` is then pointed at the shared DB via that override; and (b) `principal` is
REMOVED from the global `generate_ddl()` fold (so per-slug stores stop creating an empty
copy) and created only by the shared-DB `PrincipalStore.ensure_ready()` — i.e. it demotes
from Variant-A-in-global to a standalone-only slice. Both halves are two-line changes. **Do
not build either now.** The re-open trigger is the shared-DB promotion itself (plan
Decisions §2: "a bounded migration").

---

## 3. Fork 3 — field set, closed domains, clauses

Store law binds (§1.1): **TABLE `IF NOT EXISTS`**, **FIELD `OVERWRITE`**, **INDEX
`IF NOT EXISTS`**; `ALTER` is a trap (§1.3). `principal` is a **NEW** table, so the §1.4
populated-table hazard does not apply at creation — required (non-`option`) fields are free
now. (Stated explicitly per the brief: the only §1.4 exposure is a *future* field added to a
populated `principal` table, which must then be `option<>`.)

### New constants (R3 — NEVER reuse the `agent` tuples)

```python
_PRINCIPAL_STATUS_ACTIVE = "active"
_PRINCIPAL_STATUS_SUSPENDED = "suspended"
_PRINCIPAL_STATUSES = (_PRINCIPAL_STATUS_ACTIVE, _PRINCIPAL_STATUS_SUSPENDED)

_PRINCIPAL_ROLE_MEMBER = "member"
_PRINCIPAL_ROLE_ADMIN = "admin"
_PRINCIPAL_ROLES = (_PRINCIPAL_ROLE_MEMBER, _PRINCIPAL_ROLE_ADMIN)
```

⚠ **The closed-domain `ASSERT`s DERIVE AT CALL TIME (the `_floor_measurement_statements`
idiom), NOT at import (the `finding` idiom).** There is deliberately **no** module-level
`_PRINCIPAL_STATUS_ALLOWED` / `_PRINCIPAL_ROLE_ALLOWED` join constant: a constant frozen at
import cannot move when the Leg-1 mutation pin monkeypatches the vocabulary tuple, so a
frozen build would **false-RED** that pin (a C-DEF trap for the builder — lead ruling A,
2026-08-20, contract-48b). The join is derived inside `_principal_statements()` from
`_PRINCIPAL_STATUSES` / `_PRINCIPAL_ROLES` (below), so mutating the tuple moves the emitted
ASSERT and the pin is mutation-provable. R3 is satisfied by the tuples being
principal-specific — the derivation site (call-time local vs import constant) is orthogonal.
The *simple* fields keep the module-constant `_PRINCIPAL_FIELD_SPECS` (the `finding` idiom is
fine there — no vocabulary to mutate); only `status`/`role` move to call-time. This is the
minimal hybrid, orthogonal to the Variant-A `generate_ddl()` fold.

The `agent` table (`_AGENT_FIELD_SPECS`) already carries `role` (a free non-empty string —
`builder`/`auditor`) and `status ∈ {active,idle,input_required,retired}` via
`_AGENT_STATUS_ALLOWED`. Principal's domains are DIFFERENT and get their OWN constants. The
`", ".join(f"'{v}'" for v in …)` derivation (never a hand-typed twin ASSERT) is the
`_floor_measurement_statements` idiom — **derived at call time, inside the emitter** (§below),
so the domain is named once and the DDL ASSERT is a *mutation-provable* derivation of it.

### The ruled `_PRINCIPAL_FIELD_SPECS` (the SIMPLE fields — `status`/`role` are NOT here)

```python
# The NON-DOMAIN fields — module-level source of truth (the `finding` idiom, fine here:
# these fields carry no closed vocabulary to mutate). status/role are emitted at CALL TIME
# in _principal_statements() from _PRINCIPAL_STATUSES/_PRINCIPAL_ROLES, so their ASSERTs are
# mutation-provable (see the constants note above).
_PRINCIPAL_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("email", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("subject", "option<string>", _NON_EMPTY_STRING_ASSERT),   # Model B: NONE until 39 fills it
    ("display_name", "option<string>", ""),
    ("expires_at", "option<datetime>", ""),
    ("created_at", "datetime", "DEFAULT time::now()"),
)
```

(`_CHUNK_STRING_TYPE == "string"`; `_NON_EMPTY_STRING_ASSERT ==
`"ASSERT string::len(string::trim($value)) > 0"` — both existing module constants.)
Field ORDER is DDL-irrelevant (`DEFINE FIELD` is order-independent); the emitter appends
`status`/`role` after these five. The offline pin checks each field's clause by name, not by
position.

Field-by-field, with the option-vs-required ruling stated (§1.4 requires it):

| field | type | clause | required? | why |
|---|---|---|---|---|
| `email` | `string` | non-empty ASSERT | **REQUIRED** | the human admission key; the address 49's CLI operates on. UNIQUE index (§below). |
| `subject` | `option<string>` | non-empty ASSERT (skipped on NONE) | **optional** | the runtime identity carrying `AccessToken.client_id` (R2). **Model B:** pre-created-by-email rows carry NONE until 39 fills it on first login (§4). UNIQUE index (plain, over `option<>`). ⚠ **Refinement of the lead's literal spec** (`("subject","option<string>","")`): I KEEP `_NON_EMPTY_STRING_ASSERT`. An `option<>` field's ASSERT is not evaluated when the value is NONE (live receipt: `_floor_measurement_statements`'s `non_adoption_cause` — an `option<string>` carrying a bare ASSERT in production, skipped on NONE), so it permits the pre-created NONE row while rejecting a garbage empty-string subject that would otherwise be matched by 39's `WHERE subject = ""`. If you want the bare `option<string>` with no ASSERT, drop the constraint — one line. |
| `display_name` | `option<string>` | — | optional | presentational only; no auth or identity role. Requiring it would force a value with no payoff. |
| `status` | `string` | `DEFAULT 'active' ASSERT …∈{active,suspended}` | REQUIRED (defaulted) | mirrors `finding.status` (DEFAULT + closed ASSERT). A fresh principal is `active`. |
| `expires_at` | `option<datetime>` | — | optional | a principal may never expire; absent → NONE. `datetime` binds as a Python tz-aware datetime (store law §2 — do not stringify). |
| `role` | `string` | `DEFAULT 'member' ASSERT …∈{member,admin}` | REQUIRED (defaulted) | **DEFAULT `member` is my ruling** (plan left it unspecified): least-privilege — a principal is a member unless explicitly elevated. `role → AccessToken.scopes` must stay translatable (R2), which `{member,admin}` is. |
| `created_at` | `datetime` | `DEFAULT time::now()` | REQUIRED (engine-stamped) | mirrors `finding.created_at`; the store OMITS it on write so the engine stamps it. |

### Indexes (both UNIQUE, `IF NOT EXISTS`)

```python
_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_email", ("email",))
_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_subject", ("subject",))
```

- `PRINCIPAL_TABLE = "principal"` — a new module constant beside `FINDING_TABLE` etc.
- **No status index.** Deliberate: `principal` is bounded by the number of humans (single /
  low-double-digit for the single-instance go-live), so `list()` full-scans ~10 rows for
  free. `finding`/`task` carry a status index only because they grow large. Adding a status
  index later is a free `IF NOT EXISTS` additive migration. **Re-open trigger:** principal
  count reaching the hundreds, or a hot `list(status=…)` path.

### `_principal_statements()` / `generate_principal_ddl()`

```python
def _principal_statements() -> list[str]:
    # status/role ASSERTs are derived HERE (call time) from the closed vocabularies — the
    # _floor_measurement_statements idiom — so a mutation of _PRINCIPAL_STATUSES /
    # _PRINCIPAL_ROLES moves the emitted ASSERT and the Leg-1 mutation pin can SEE it. A
    # module-level frozen join constant could not (C-DEF false-RED — lead ruling A).
    status_allowed = ", ".join(f"'{status}'" for status in _PRINCIPAL_STATUSES)
    role_allowed = ", ".join(f"'{role}'" for role in _PRINCIPAL_ROLES)
    domain_specs: tuple[tuple[str, str, str], ...] = (
        (
            "status",
            _CHUNK_STRING_TYPE,
            f"DEFAULT '{_PRINCIPAL_STATUS_ACTIVE}' ASSERT $value IN [{status_allowed}]",
        ),
        (
            "role",
            _CHUNK_STRING_TYPE,
            f"DEFAULT '{_PRINCIPAL_ROLE_MEMBER}' ASSERT $value IN [{role_allowed}]",
        ),
    )
    statements: list[str] = [_define_table(PRINCIPAL_TABLE)]
    statements += [
        _define_field(PRINCIPAL_TABLE, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in (*_PRINCIPAL_FIELD_SPECS, *domain_specs)
    ]
    statements.append(_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_email", ("email",)))
    statements.append(_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_subject", ("subject",)))
    return statements


def generate_principal_ddl() -> str:
    return ";\n".join(_principal_statements()) + ";\n"
```

---

## 4. Fork 4 — `subject` index: UNIQUE over `option<string>` (Model B)

**Ruling: a plain UNIQUE index on `subject`, and `subject` is `option<string>`.** This
supersedes the doc's original Model-A ruling — the operator resolved F1 to **Model B**
(2026-08-20): an admin pre-creates a principal by **email** before first login, and packet
39 fills the OAuth `subject` on first login.

### The anchor (R2)
`principal.subject` MUST carry the value `fastmcp.server.dependencies.get_access_token()`
surfaces as `AccessToken.client_id` (spike-proven runtime identity — `lore_recall("fastmcp
migration principal seam")`). Packet 39's admission does `WHERE subject = $client_id`; that
lookup must return **at most one** principal, which the UNIQUE index guarantees over every
non-NONE subject.

### The mechanics are PROBE-SETTLED, not reasoned (SurrealDB 3.2.4)
The UNIQUE-over-nullable question is no longer a design call — `scripts/probe_unique_nullable_48.py`
(exit 0, positive controls, VERIFIED by lead re-run):
- **multiple NONE** under a plain `option<string>` UNIQUE index = **ALLOWED** → any number of
  email-pre-created principals (subject=NONE) coexist. *This is the Model-B property a
  single-NONE fixture cannot see (§8).*
- **same non-NONE subject** = **REJECTED** on CREATE **and** on UPDATE → 39's fill-on-login
  path is UNIQUE-protected; a second principal can never claim a subject already bound.
- **filtered / partial UNIQUE** = **NOT SUPPORTED** (parse error) — and not needed; the plain
  UNIQUE over `option<>` already gives exactly the Model-B semantics.

So the index is the ordinary `_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_subject",
("subject",))` — no filtered/partial clause, unchanged from §3.

### No legitimate duplicate non-NONE subject
- Google OAuth: the `sub` claim (which `client_id` derives from) is globally unique and
  stable per Google account → one subject per person.
- API key: packet 39's already-designed mint is `client_id=f"api_key:{name}"`,
  `subject=name` (proposal §1C); the odoo-style collapse-all-keys-to-one-identity is
  explicitly REJECTED (§1C, #206) → one subject per key-name.

So UNIQUE never rejects a legitimate non-NONE write; it only catches a genuine identity
collision — while the multiple-NONE allowance is exactly what the pre-create flow needs.

### Why `option<string>` (Model B, straight to optional)
`subject` is unknown at pre-create time (an admin invites `alice@example.com` before Alice's
first Google login, when her `sub` — hence `client_id` — does not yet exist), so a
pre-created row MUST carry NONE. `email` stays the REQUIRED+UNIQUE admin key that addresses
such a row; `subject` is filled later by `set_subject` (§5). We go **straight to
`option<string>`** — the earlier Model-A "required→optional widening" argument is dropped;
F1 is resolved, not deferred.

---

## 5. Fork 5 — the CRUD surface (`PrincipalStore` + `Principal`)

**Home:** `loremaster/loremaster/principals.py` (new top-level module, mirroring
`findings.py` / `tasks.py`; the proposal §1B already names `-m loremaster.principals`). 49
adds the CLI (`main`/`build_parser`) and the `principal_key` table to this module later.

**Value object** — pydantic `BaseModel` mirroring `findings.Finding`:

```python
class Principal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str                       # str(RecordID) — round-trips (store law §2)
    email: str
    subject: str | None           # NONE until 39 fills it on first login (Model B)
    display_name: str | None
    status: str
    role: str
    expires_at: datetime | None
    created_at: datetime
```

`extra="forbid"` on the wire is the repo gate (CLAUDE.md); `frozen=True` matches the ledger
value-object idiom.

**Errors** — mirror `FindingLedgerError` / `FindingNotFoundError`:

```python
class PrincipalStoreError(RuntimeError): ...
class PrincipalNotFoundError(PrincipalStoreError): ...
```

**The class** — clones the `FindingLedger` owner idiom EXACTLY (no `dim`: non-vector table):

```python
class PrincipalStore:
    def __init__(self, *, url: str, namespace: str, database: str,
                 user: str, password: SecretStr) -> None: ...
    # cloned verbatim from FindingLedger — DO NOT re-invent:
    async def _ensure_connection(self) -> _SurrealConnection: ...   # bootstrap_session, DCL
    async def _drop_connection(self, connection) -> None: ...
    async def close(self) -> None: ...
    async def _query(self, statement: str, params: dict | None = None) -> Any:
        # delegates to store._txn.run_query — the ONE shared single-statement seam
        # (retry-on-conflict + self-heal, #120/#108). NEVER a hand-rolled query loop.
        ...
    async def ensure_ready(self) -> None:
        # execute_transaction(f"BEGIN;\n{generate_principal_ddl()}COMMIT;\n", {}, …)
        ...

    async def create(self, *, email: str, subject: str | None = None,
                     role: str | None = None, display_name: str | None = None,
                     expires_at: datetime | None = None) -> Principal: ...
    async def get_by_subject(self, subject: str) -> Principal | None: ...
    async def get_by_email(self, email: str) -> Principal | None: ...
    async def list(self) -> list[Principal]: ...
    async def set_status(self, *, email: str, status: str) -> Principal: ...
    async def set_subject(self, *, email: str, subject: str) -> Principal: ...  # 39 fill-on-login
```

### Method rulings

- **`create`** — a SINGLE `CREATE principal CONTENT $content RETURN AFTER` via `_query`
  (single statement; no counter/multi-statement, so no `execute_transaction` and no
  `_apply` helper needed — simpler than `FindingLedger`, correctly). **`subject` is OPTIONAL
  (Model B — email-only creation):** `$content` always carries `email`; it carries `subject`
  only when provided (the OAuth-direct path), and OMITS it when `None` so the column decodes
  to NONE (the pre-created-by-email row). It also OMITS `display_name`/`expires_at` when
  `None`, OMITS `created_at` (so `DEFAULT time::now()` fires), and OMITS `status` (defaults
  `active`) and `role` when `None` (defaults `member`). Use **CONTENT** (store law §2's
  general write idiom — binds the object opaque and lets omitted fields take their DDL
  DEFAULT / NONE). A duplicate `email`, or a duplicate **non-NONE** `subject`, is rejected by
  the UNIQUE backstop (two subject=NONE rows COEXIST — probe Q1); wrap that rejection into
  `PrincipalStoreError` (loud, never silent — Consumer Law). No `session`-style protected
  column exists here, but CONTENT is still the right idiom for the omit-to-default behavior.
- **`get_by_subject` / `get_by_email`** — the two lookups are SPLIT because they ride two
  distinct UNIQUE indexes and serve two distinct consumers (39 by subject, 49 by email).
  Each returns `Principal | None` (None = no match, not an error). ⚠ **Reads use EXPLICIT
  column projections**, NOT `SELECT *`: store law §2 — `SELECT *` OMITS a NONE-valued
  `option<>` column entirely (`KeyError`), while an explicit projection reads it back as
  `None`. So `SELECT id, email, subject, display_name, status, role, expires_at, created_at
  FROM principal WHERE subject = $subject`.
- **`list`** — `SELECT <explicit cols> FROM principal ORDER BY created_at` → `list[Principal]`
  (all principals; the tiny table full-scans for free). 49 filters client-side if it wants a
  status subset; no `status` param on 48's `list`.
- **`set_status`** — keyed on **email** (49's admin CLI verb is `suspend <email>` /
  `unsuspend <email>` — the human identity). `UPDATE principal SET status = $status WHERE
  email = $email RETURN AFTER` via `_query`; an empty return (email not found) raises
  `PrincipalNotFoundError`. Validate `status ∈ _PRINCIPAL_STATUSES` client-side for a clean
  error, with the DDL ASSERT as the backstop (defence in depth, both loud).
- **`set_subject`** (NEW FORK — **ruled YES**, ship it in 48) — the fill-on-login primitive
  packet 39 calls to bind a pre-created principal to its OAuth subject. It IS substrate CRUD
  the store owns and 39 consumes (exactly like `set_status`), and the UNIQUE backstop protects
  it (probe: a duplicate non-NONE subject is rejected on the UPDATE path too). Keyed on
  **email**: `UPDATE principal SET subject = $subject WHERE email = $email RETURN AFTER` via
  `_query`; empty return (email not found) → `PrincipalNotFoundError`; a UNIQUE rejection (the
  subject already belongs to ANOTHER principal) → `PrincipalStoreError` (loud). Mirrors
  `set_status` structurally (unconditional email-keyed UPDATE).
  ⚠ **The one thing 48 does NOT enforce — surfaced as a 39 policy, not built here:** this is an
  *unconditional* fill/overwrite; it does not structurally forbid re-pointing a principal that
  ALREADY has a (different) subject. The UNIQUE index catches subject-THEFT (two principals,
  one subject) but NOT a self re-point (row A's subject A→B when B is free). **39 owns that
  guard by ORCHESTRATION** — 39's admission checks `get_by_subject` first and only calls
  `set_subject` for a principal found by email whose subject is NONE; a principal found by
  email with a *different* non-NONE subject is an email-bound-to-another-identity conflict 39
  must handle, not silently overwrite. (Idempotent re-login is safe: setting a row's subject
  to its OWN current value is not a UNIQUE conflict.) If the operator instead wants the STORE
  to enforce fill-once, `set_subject` gains `AND subject IS NONE` in the WHERE — but that
  muddies the not-found-vs-already-set return and is better owned by 39; **recommend the
  unconditional primitive + 39 orchestration.** Flagged, not blocking (§7 F1b).

### One row→value mapping helper (DRY)
`create`/`get_by_subject`/`get_by_email`/`list`/`set_status`/`set_subject` all map a returned
row → `Principal` through ONE private `_row_to_principal(row)` helper that uses `row["…"]` for
the required columns (`id`/`email`/`status`/`role`/`created_at`) and `row.get("…")` for the
`option<>` ones — now **`subject`, `display_name`, `expires_at`** (subject joined the option
set under Model B) — the store-law §2 defence against a returned `RETURN AFTER`/`SELECT`
omitting a NONE column. One mapping, not six clones.

### DRY ledger (the §6-required "prove you looked" table)

| new symbol | searched | found | disposition |
|---|---|---|---|
| single-statement read/write seam | `findings.FindingLedger._query`, `store._txn.run_query` | the shared `run_query` seam exists | **REUSED `store._txn.run_query`** (via a `_query` clone) — NO new seam |
| DDL-apply seam | `FindingLedger.ensure_ready`, `store._txn.execute_transaction` | exists | **REUSED `execute_transaction`** |
| connection bootstrap | `store._txn.bootstrap_session` | the ONE shared bootstrap | **REUSED** (via a `_ensure_connection` clone) |
| retry/backoff | `_txn.retry_on_conflict` (rides `run_query`/`execute_transaction`) | exists | **REUSED transitively** — 48 hand-rolls NO retry |
| DDL helpers | `_define_table`/`_define_field`/`_unique_index` | exist | **REUSED** |
| value-object base | `findings.Finding(BaseModel)` | pydantic idiom | **REUSED the idiom** (new `Principal` model) |
| error base | `FindingLedgerError`/`FindingNotFoundError` | idiom | **REUSED the idiom** (new `PrincipalStoreError`/`PrincipalNotFoundError`) |

`create`/`set_status`/`set_subject`/`get_*`/`list` are new PRINCIPAL-SPECIFIC application
methods (no existing principal CRUD to reuse — this is the substrate 48 introduces), each
routing through the reused seams above. Prove routing-is-sharing by the fork-1 mutation
discipline applied to the seam: 48 introduces no policy (retry/classification) of its own.

---

## 6. Fork 6 — the module docstring standing-law clause

The `loremaster/loremaster/principals.py` MODULE docstring MUST carry a clause with these
four load-bearing statements (exact wording ruled; the builder may adjust prose but not
drop any of the four):

> `principal` is lore's **human-identity** vocabulary — the persistent record of a person
> who authenticates (Google OAuth `sub` / an API-key name), surfaced at runtime as
> `AccessToken.client_id` and stored in `principal.subject`. It is a THIRD, distinct
> identity vocabulary, and the one-column-one-identity-vocabulary law (the law near
> `server.py`'s `_TRACE_DECLARED_KEYS`, *"the same dishonesty as overloading `session` with
> a transport id"*) forbids conflating it with the other two:
>
> 1. **Ledger-actor strings** (`created_by` / `actor` / `owner` on `finding` / `task` /
>    `memory`) are free-form audit strings and are **NOT retro-fitted** to `principal`. A
>    finding's `created_by` is not a `principal` FK and must not become one here.
> 2. **The comms `agent` table** (`_AGENT_FIELD_SPECS`) is the fleet-coordination identity,
>    and it ALREADY carries columns named `role` and `status` with DIFFERENT domains —
>    `agent.role` is a free non-empty string (`builder`/`auditor`/…) and `agent.status ∈
>    {active, idle, input_required, retired}` (`_AGENT_STATUS_ALLOWED`). `principal.role ∈
>    {member, admin}` and `principal.status ∈ {active, suspended}` are NARROWER,
>    principal-specific closed domains with their OWN vocabulary tuples
>    (`_PRINCIPAL_ROLES` / `_PRINCIPAL_STATUSES`). The identical column NAMES
>    across two tables are a coincidence of English, not shared vocabulary — never wire
>    `principal.role`/`status` to the `agent` tuples.

Cite the law by its SYMBOL anchor (`_TRACE_DECLARED_KEYS`), not a bare line number (it
drifts). This clause is a served-prose surface (a rename/reshape-sweep target): the contract
should carry an offline pin that the docstring names both sibling vocabularies and the
principal-specific constants — a diagnosis without an instrument is how these prose surfaces
rot (CLAUDE.md "A DIAGNOSIS IS NOT AN INSTRUMENT").

---

## 7. Flags, escalations, and named re-open triggers

- **F1 — RESOLVED (operator, 2026-08-20) → Model B.** Admin pre-creates by email; 39 fills
  the OAuth subject on first login. `subject` is `option<string>` UNIQUE (§4), probe-settled
  on 3.2.4 (`scripts/probe_unique_nullable_48.py`, lead-verified). No longer an open flag.
- **F1b (NEW, ruled by me — not operator-level) — `set_subject` fill-once vs overwrite.**
  48 ships the *unconditional* email-keyed UPDATE primitive; the fill-once guard against
  re-pointing an already-subject'd principal lives in **39's orchestration** (check
  `get_by_subject` before calling; an email bound to a different non-NONE subject is a
  conflict 39 handles). Recommend the unconditional primitive + 39 orchestration; the STORE
  can enforce fill-once (`AND subject IS NONE`) if the operator prefers, at the cost of a
  muddier not-found-vs-already-set return (§5). One-line either way; flagged for deliberate
  choice, not blocking.
- **F2 — `role` DEFAULT `member`** is MY ruling (least-privilege; plan left it
  unspecified). If the operator wants no default (every creator names the role explicitly),
  drop the `DEFAULT 'member'` from the `role` spec — a one-line change. Flagged so the choice
  is deliberate.
- **F3 — no `status` index** is a deliberate YAGNI ruling. Re-open trigger: principal count
  in the hundreds, or a hot `list(status=…)` path.
- **F4 — shared-DB future** (§2) is a documented, un-built seam. Re-open trigger: the
  shared-DB promotion.
- **F5 — broad extraction** (~10 cred/db re-resolvers incl. `_await_live_connect`) is
  ledgered as a future refactor, deliberately out of 48.
- **F6 (contract-author sweep) — the `generate_ddl()` fold may collide with an existing
  exact-DDL or table-inventory pin.** If a test asserts the full `generate_ddl()` text or
  the exact set of tables/indexes, adding `principal` reddens it and it must be updated in
  the SAME wave (a rename/reshape-sweep item — grep the test tree for assertions over
  `generate_ddl` / a table-name inventory). Not a defect, a required co-edit.

---

## 8. Contract-author input checklist (what to pin)

**Half 1 — `build_store`:**
1. Three-site sharing MUTATION proof: change a `build_store`-resolved value → all three
   caller store pins redden; declare expected-RED ids from `--collect-only` first.
2. R4 regression pin: `build_store` does not parse/handle URL credentials (reads the
   already-validated `config.surreal.url`).
3. Un-readied contract: `build_store` never calls `ensure_ready()`; `Scout.from_config`
   stays un-readied, `build_app_context` / `index.cli._run` ready.
4. R5: cite the `build_mcp_server` lifespan → `_eager_build_with_retry` → `build_app_context`
   chain in the server-site proof (not the deleted `_EagerStartupLifespan`).

**Half 2 — `principal` (the three-legged store idiom):**
5. **Leg 1 (offline DDL pin)** — `test_principals_schema.py`, cloning
   `test_floor_calibration_schema.py`'s per-rule methods: table=IF NOT EXISTS, every
   field=OVERWRITE, no field-IF-NOT-EXISTS, both indexes=IF NOT EXISTS (never OVERWRITE), no
   ALTER; and the closed-domain derivation (mutate `_PRINCIPAL_STATUSES`/`_PRINCIPAL_ROLES`
   → the emitted ASSERT changes). Pin that `principal` is IN `generate_ddl()` (the fold).
6. **Leg 2 (live round-trip on `ws://127.0.0.1:18000`, NEVER `:18500`, NO skip marker)** —
   the Model-B property set:
   - **(d) create-WITH-subject** (OAuth-direct path) → read back by subject AND by email.
   - **(a) TWO email-only creates both `subject`=NONE both SUCCEED** (probe Q1 — the Model-B
     property a single-NONE fixture CANNOT see; this is the load-bearing pin) → each read back
     by email with `subject is None`.
   - **(b) same non-NONE `subject` REJECTED** on CREATE **and** on the `set_subject`/UPDATE
     fill (two pins — the UPDATE path is the one the probe caught and a CREATE-only pin
     misses).
   - **(c) `email` REQUIRED+UNIQUE unchanged** — duplicate `email` rejected; empty/missing
     `email` rejected (non-empty ASSERT + required).
   - closed-domain ASSERT reject on bad `status`/`role`; **POSITIVE CONTROL** — every valid
     status (`active`,`suspended`) and role (`member`,`admin`) accepted (an over-strict ASSERT
     fails this).
   - `option<>` omitted-column read pin (create with no `subject`/`display_name`/`expires_at`
     → read those back as `None`, not `KeyError`) — the store-law §2 hostile fixture; note
     `subject` is now in this set.
   - **empty-string `subject` REJECTED** (the retained non-empty ASSERT fires on a present-but-
     empty value) while **NONE is accepted** (ASSERT skipped on NONE) — the §3 refinement's
     positive+negative control. *(If the lead drops the ASSERT to a bare `option<string>`,
     delete this pin and say so.)*
7. **Leg 3 (dirty-store migration, #107-class)** —
   `TestSchemaMigrationAgainstAnExistingStore`: apply OLD DDL → insert a legacy principal row
   UNDER THE OLD DDL → apply NEW DDL → assert the new constraint took AND the legacy row
   survived + is still writable. (Write the legacy row under the OLD DDL — a row written after
   the full DDL sees no hazard.)
8. `set_status` not-found pin (unknown email → `PrincipalNotFoundError`, with a positive
   control that a known email DOES transition).
8b. **`set_subject` pins (Model B fill-on-login):** (i) the happy path — email-only create
    (`subject`=NONE) → `set_subject(email, sub)` → `get_by_subject(sub)` now finds it and
    `get_by_email` shows the filled subject; (ii) not-found — `set_subject` on an unknown
    email → `PrincipalNotFoundError` (with a positive control that a known email DOES fill);
    (iii) subject-theft — `set_subject` binding a subject already owned by ANOTHER principal
    → `PrincipalStoreError` (the UNIQUE backstop on the UPDATE path; this is pin (6b) from the
    store side); (iv) idempotent re-fill — `set_subject(email, sub)` on a row that already has
    exactly `sub` SUCCEEDS (setting a row to its own value is not a UNIQUE conflict).
9. Fork-6 docstring pin (names both sibling vocabularies + the principal-specific constants).
10. Mutation-prove every load-bearing pin (each DDL rule, each closed-domain ASSERT, each
    UNIQUE, the dirty-store migration) via `scripts/mutation_proof.py`; scratch copies via
    `./scripts/scratch_copy.sh` printing `loremaster.__file__`.

---

## Appendix — citations (symbols, HEAD `9195839`)

- Variant A precedent: `store.surreal_schema._finding_statements` /
  `generate_finding_ddl` (folded into `generate_ddl`); owner
  `findings.FindingLedger.ensure_ready` / `._query` / `._ensure_connection` / `.__init__`.
- Variant B contrast: `store.surreal_schema.generate_floor_calibration_ddl` (NOT in
  `generate_ddl`); owner `floor_calibration.store.FloorCalibrationStore.ensure_ready`.
- DDL helpers: `_define_table` (IF NOT EXISTS SCHEMAFULL), `_define_field` (OVERWRITE),
  `_unique_index`/`_plain_index` (IF NOT EXISTS); `_CHUNK_STRING_TYPE = "string"`;
  `_NON_EMPTY_STRING_ASSERT`.
- Collision (R3): `_AGENT_FIELD_SPECS`, `_AGENT_STATUS_ALLOWED`.
- Shared seams: `store._txn.run_query`, `store._txn.execute_transaction`,
  `store._txn.bootstrap_session`, `store._txn.retry_on_conflict`.
- build_store sites: `server.build_app_context` (write_store), `index.cli._run`,
  `scout.Scout.from_config`. Broad-only re-resolvers: `server` `AppContext._await_live_connect`
  → `scout._open_command_connection`; `SurrealManifest` / `SurrealCodeGraph` ctor calls.
- Ctor: `store.surreal.SurrealStore.__init__(*, url, namespace, database, dim, user,
  password, analyzer_name=DEFAULT_ANALYZER_NAME, entity_tables=())`.
- Config: `config.LoreConfig.effective_surreal_database` (= `surreal.database or
  project.slug`), `config.resolve_config_value`, `config.resolve_secret`,
  `config._reject_url_userinfo` (R4).
- Value/error idiom: `findings.Finding(BaseModel)` + `ConfigDict`;
  `FindingLedgerError`/`FindingNotFoundError`.
- Standing law: one-column-one-identity-vocabulary near `server._TRACE_DECLARED_KEYS`.
- Runtime identity (R2): `fastmcp.server.dependencies.get_access_token()` →
  `AccessToken.client_id`/`.scopes` (spike memory — `lore_recall("fastmcp migration
  principal seam get_access_token")`).
