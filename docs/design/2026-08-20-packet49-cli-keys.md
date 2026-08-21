# Packet 49 — Principal management CLI (1B) + per-user API keys (1C): design + rulings

`brief-base v14 read` · `brief project v7 read`

**Author:** `fable-design-49` (design sidecar, model fable) · **Date:** 2026-08-20
**Task ledger:** `6e4f6016998d46fabf6bcdcf6d0477a4` (claimed → in_progress)
**Spec (work order):** `docs/design/2026-08-01-multi-user-lore-proposal.md` §Part 1B + §Part 1C
**Packet:** `docs/plans/v2/49-principal-cli-keys.md`
**Consumer of this design:** the packet-49 contract author, then the adversary/builder/cold-audit chain.

---

## Summary block (read this first)

- **State:** done — 7 forks ruled; **operator rulings applied 2026-08-20** (F4 `<name>:<secret>` CONFIRMED; the dry-run/`--execute` paradigm STRUCK entirely — every verb executes directly, only `list`/`list-keys` are reads). Two forward-dependency FLAGS on packet 39 (§F3/§F4 identity mint) and a PIN-THE-MISS bound (§F2 cascade forward-scope) remain surfaced for awareness.
- **New store surface (49 owns):** a `principal_key` table + `PrincipalKeyStore` in a new module `loremaster/loremaster/principal_keys.py`; three new `PrincipalStore` methods (`set_expires`, `delete`); the CLI in `principals.py`.
- **49 does NOT touch:** `auth.py`'s `ApiKeyVerifier` / `build_api_key_verifier` / `BearerAuthMiddleware` — that is packet 39's kept surface (§4 of the pkt-39 design). The wire-level middleware wiring is packet 39's, explicitly out of 49's scope.
- **DRY reuse (proven-shareable, cite these):** `lorerunes.blankness.is_blank` (reject-empty; mutation-proven shared, pkt42 #222) · `loremaster.index.records.sha512_hex` (the key hash) · **`loremaster.sanitise.sanitise_line`/`safe_str`** (CLI render of stored free text — F8, finding #34) · the `loremaster.store._txn` seams (`bootstrap_session`/`run_query`/`execute_transaction` — NO new retry/query policy, #102/#120) · `surreal_schema` emitter idiom · `snapshot_gc.py` CLI idiom (not its dry-run) · `index/cli.py` `build_parser()`/`main(argv)->int` house idiom.
- **Packages considered:** `secrets.token_urlsafe` (secret generation — stdlib, `keep`); `hashlib` via the existing `sha512_hex` wrapper (`replace` the would-be hand-roll); `argparse` (stdlib CLI — house idiom); `cachetools`/TTL **rejected** by R12 (revocation must beat any cache — no residual window).

---

## The identity picture (read before the forks — every ruling rests on it)

Three distinct identity vocabularies exist and must never be conflated (spec §1A standing law; `principals.py` module docstring; `server.py:7577-7581`):

1. **Ledger-actor strings** (`finding.created_by`, `task.owner`, `memory.*`) — free audit strings, **never** retro-fitted to `principal`.
2. **The comms `agent` table** — fleet coordination identity (`agent.role`/`status` are DIFFERENT closed domains from `principal.role`/`status` — a coincidence of English).
3. **`principal`** — the HUMAN vocabulary. `principal.subject` (`option<string>` UNIQUE) is the runtime OAuth identity that packet 39 matches via `get_by_subject(client_id)` on the **OAuth** path.

**The load-bearing consequence for keys (this is why #206 is avoidable):** a `principal_key` belongs to exactly one `principal`, and a `principal` may hold **many** keys (one-to-many). So the authenticated IDENTITY of an api-key request is the **principal**, resolved via the key→principal link — NOT the key's label, and NOT a constant. `principal.subject` is NOT used on the api-key path (it is the OAuth-login binding; an api-key-only principal may have `subject = NONE` forever). `verify()` resolves the principal directly from the presented key, so no `get_by_subject` lookup is needed on the key path.

**Forward-dependency FLAG (packet 39, not 49):** packet 39 §4's api-key branch was written for the *static* `ApiKeyVerifier`, where the returned `name` IS the identity. For 49's DB keys the identity is the **principal**, so when 39 (or a follow-on packet) wires 49's `verify`, it must mint from the principal identity (recommend `subject = principal.email`, `client_id = f"api_key:{principal.email}"`), **not** from the key label. 49 returns the full `Principal` precisely so 39 can do this. 49 does not change 39's code — this is a note for whoever wires the two together.

---

## F1 — `--expires` semantics [RULED by sidecar]

**Two readings that produce different code.** Spec §1B lists `--expires` among the "verbs" but writes it with a `--` prefix (unlike the bare `add`/`list`/`delete`/`suspend`/`unsuspend`), which reads as an OPTION, while listing it beside verbs reads as a management operation. `PrincipalStore.create()` already accepts `expires_at`, but there is **no** `set_expires` method today.
- **Reading A** — `--expires` is only an OPTION on `add` (set expiry at creation). No new store method.
- **Reading B** — `--expires` is a standalone verb that CHANGES expiry on an existing principal. Needs a NEW `PrincipalStore.set_expires`.
- **Reading C** — both.

**RULING: C (both).** An admin adjusting a contractor's access window after creation is a first-class need (Fork 2 in the spec names expiry as a richer substitute for R12's flat roster — expiry is a *managed* attribute, not a create-only one). So:
- `add … [--expires <ISO8601>]` — optional; omitted ⇒ `expires_at = NONE` (never expires). Uses the EXISTING `create(expires_at=…)`; **no new store method**.
- a standalone verb **`set-expiry`** `--email <e> (--at <ISO8601> | --clear)` — changes expiry on an existing principal. Needs a **new** `PrincipalStore.set_expires(*, email: str, expires_at: datetime | None) -> Principal`.

**Store method spec (`set_expires`)** — clone `set_status`'s shape exactly (`principals.py::PrincipalStore.set_status`): keyed on `email` (the human key); an unknown email is a typed `PrincipalNotFoundError` (never a silent no-op on an empty UPDATE result); rides `_query` (no new policy). `--clear` sets `expires_at = NONE`; `--at <ts>` binds a **Python datetime** (store law §2 — never stringified; `option<datetime>` column). ⚠ Setting an `option<datetime>` back to NONE is `SET expires_at = NONE` (not omission — an UPDATE omitting the column leaves it unchanged); pin both the set-a-value and the clear-to-NONE paths.

Citations: spec §1B verbs line; `principals.py::set_status` (the clone target); store-ref §2 (`option<datetime>` / datetimes-as-Python-datetimes).

---

## F2 — `delete` verb: linkage shape + hard-delete-vs-suspend + cascade [RULED by sidecar]

**`PrincipalStore` has no `delete` today. It must be added.** Two sub-forks.

### (a) Linkage shape — record link + explicit cascade, NOT a RELATION edge. [RULED]

Store-ref §1A / §4: `record<t>` links do **not** auto-clean on target delete; RELATION edges **do** self-delete. So the choice is between (i) `principal_key.principal: record<principal>` + an explicit children-first cascade, and (ii) a RELATION edge that self-deletes.

**RULING: (i) a required `record<principal>` link + explicit children-first cascade.** Reasons:
- `principal_key` is a **NODE** table with its own columns (hash, name, timestamps) that is *owned by* a principal — the `snapshot_entry → snapshot` shape, not a graph traversal relationship. Node-with-owner-link is the correct model; edges are for graph walks.
- The `snapshot_gc.py` precedent already demonstrates exactly this cascade (`_delete_snapshots`: "children first — record links do not auto-clean"), so we reuse a proven, tested idiom rather than introducing lore's first data-owning RELATION table.
- **`record<principal>` is REQUIRED (not `option<>`)** — §1.4's "new field on a POPULATED table must be `option<>`" does NOT apply: `principal_key` is a brand-new, empty table, so its owner column can be required. Every key has an owner at mint. (⚠ `record<t>` does not itself enforce existence — §4 — but the mint path always binds a just-verified principal id, and the cascade removes children before the parent, so no dangling arises from our own operations.)

### (b) Hard delete vs suspend — they are DISTINCT verbs, keep them distinct. [RULED]

The spec §1B lists `delete` AND `suspend`/`unsuspend` as separate verbs. **RULING:**
- **`delete`** = HARD delete: `DELETE principal_key WHERE principal = $pid` (children first), THEN delete the `principal` row. Permanent, irreversible. Executes directly when run (no dry-run / no `--execute` — operator ruling 2026-08-20; silent-on-success, loud-on-failure; a clear one-line result naming the principal and the N keys removed).
- **`suspend`/`unsuspend`** = the reversible `status` toggle (already `set_status`), rows retained; verify denies a suspended principal's keys (see F3a).

New store method: `PrincipalStore.delete(*, email: str) -> None` (or `-> Principal` of the deleted row for the audit/output line). Keyed on email; unknown email ⇒ `PrincipalNotFoundError`; the DELETE-children + DELETE-parent runs inside ONE `execute_transaction` (`BEGIN … COMMIT`) so a half-cascade can't leave orphaned keys — reuse `execute_transaction` (validates every statement's status; the SDK's plain `query()` checks only `statement[0]` — see `PrincipalStore.ensure_ready`). Note the delete spans two tables (`principal_key` then `principal`) — this is the first `PrincipalStore` write that touches the key table, so `PrincipalStore.delete` needs the `PRINCIPAL_KEY_TABLE` name (import from `surreal_schema`); it does NOT need a `PrincipalKeyStore` instance (it issues the child DELETE directly on its own connection, inside the same txn).

**⚠ PIN THE MISS — forward-scope of the cascade (named re-open trigger).** Today the ONLY `record<principal>` link is `principal_key` (ledger actors are free strings; `agent` is unrelated — §1A). When packet 3A lands `memory.owner: option<record<principal>>`, deleting a principal will leave **dangling `memory.owner` links** (record links don't auto-clean). So: **the delete cascade covers `principal_key` ONLY, by construction of what links to `principal` at 2026-08-20.** Add a test/comment that asserts this bound and names the re-open trigger: *"when any NEW `record<principal>` link is added (packet 3A's `memory.owner` first), this cascade MUST be revisited."* This is the store-ref §4 dangling-edge hazard applied forward.

Citations: store-ref §1A/§4 (record links don't auto-clean; edges do); `snapshot_gc.py::_delete_snapshots` (cascade precedent); `principals.py::ensure_ready` (execute_transaction rationale); spec §1A (only `principal_key` links to `principal`).

---

## F3 — `verify(presented)` behavior, resolution, and typed result [RULED by sidecar]

The load-bearing served surface. On EVERY call (no cache — R12 restored ruling, no residual window; pkt-39 §3-R12): hash → resolve → re-check.

### (a) Does verify also deny when the OWNING principal is suspended / expired? — YES. [RULED]

**RULING: verify denies unless ALL of these hold, re-evaluated every call:**
1. `key.revoked_at IS NONE`
2. `key.expires_at IS NONE OR key.expires_at > now`
3. `principal.status == 'active'` (NOT suspended)
4. `principal.expires_at IS NONE OR principal.expires_at > now`

Reason (Consumer/Trust Law, verbatim intent): authenticating a **suspended or expired human** is a trust failure — the whole point of `suspend`/expiry is to lock someone out, and a valid key must not be a bypass. R12's "revocation beats the cache" generalises to "the current admission state beats the cache": the roster/status is re-checked on every verification, cache hits included, no residual window (pkt-39 §3-R12). `now` is a single tz-aware UTC `datetime` captured once per call (the fleet-comparable anchor idiom; `PrincipalStore._to_aware_utc`).

**Server-side observability, NOT a caller oracle:** evaluate the four conditions in Python and LOG the specific denial reason (laundered — never the key value), but return a **uniform** deny (`None`) to the caller. Distinguishing "no such key" from "revoked" to the caller would be an oracle; the log is where the reason lives.

### (b) What does verify RETURN to packet 39? — the principal + the key name, NOT the AccessToken. [RULED]

**RULING:** verify returns the resolved `Principal` object and the key's `name`. It does NOT construct an `AccessToken` (that is 39's mint, from `mcp.server.auth.provider`). Returning the full `Principal` (not just a string) gives 39 the identity (`email`), the `role` (for future 3B admin checks), and status — everything the mint and any downstream permission resolver needs.

### (c) Typed result shape. [RULED]

```python
class KeyVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    principal: Principal          # the resolved owner (from principals.py)
    key_name: str                 # the label of the key that authenticated (audit)

async def verify(self, presented: str) -> KeyVerification | None: ...
```
`None` on ANY failure (blank input, malformed, no-match, revoked, key-expired, principal-suspended, principal-expired). A frozen pydantic model matches the `Principal` / repo value-object idiom (`extra="forbid"`, `frozen=True`).

### Resolution query — single link-deref query preferred; two-query fallback; PROBE it.

Preferred (one hot-path round-trip): a single `SELECT` on `principal_key WHERE hash = $h` that **dereferences the record link** for the principal fields — e.g. `SELECT name, revoked_at, expires_at, principal.id AS p_id, principal.email AS p_email, principal.subject AS p_subject, principal.display_name AS p_display, principal.status AS p_status, principal.role AS p_role, principal.expires_at AS p_expires, principal.created_at AS p_created FROM principal_key WHERE hash = $h`. Then map `p_*` → `Principal` and evaluate the four conditions in Python.

⚠ **Two builder obligations here:**
- **PROBE the link-deref projection against the 3.2.4 test store** (`ws://127.0.0.1:18000`) before relying on it — record-link field access in a projection is a store-behaviour question, and store-ref order applies (§2/§4 first, then probe). If unsupported/awkward, fall back to **two queries** (fetch the key row by hash → resolve the principal by id), which is simpler and lets the principal mapping be reused directly.
- **Do NOT clone `PrincipalStore._row_to_principal`.** The two stores must map a principal row the SAME way (ONE-IMPLEMENTATION). Either (preferred) promote the row→`Principal` mapping to a shared function both stores call, or have `PrincipalKeyStore` resolve the principal by delegating to a `PrincipalStore` lookup. Prove the sharing by mutation (change the mapper; both stores' pins redden). A private second mapper is a #102-class clone.

Citations: pkt-39 §3-R12 (no residual window, re-check every verification); Consumer/Trust Law (repo CLAUDE.md); store-ref §2 (explicit projection; `option<>` reads back None; probe-before-trust) / §4 (record links); `principals.py::_row_to_principal` / `_to_aware_utc`.

---

## F4 — Key wire format, hash, and secret generator [RULED by sidecar → OPERATOR-CONFIRMED 2026-08-20]

**Two readings that produce different code.**
- **Reading A** — `<name>:<secret>` (odoo-code's split-on-first-colon shape). The spec §1C ✅-Adopt list literally names "split on the first colon".
- **Reading B** — an opaque `lore_<random>` token, hashed whole, looked up by hash; the name lives only as a row column (never on the wire). Modern token pattern (GitHub PAT / Stripe): no name-enumeration surface, no per-name wire coupling.

**RULING: A — `<name>:<secret>`, faithfully adopting the odoo-code validation shape** (sidecar ruling, **OPERATOR-CONFIRMED 2026-08-20** — the opaque-token refinement below was considered and DECLINED; build Reading A). Exact mechanics:

- **CLI prints, ONCE at mint, exactly one line:** `<name>:<secret>` where `secret = secrets.token_urlsafe(32)` (256 bits of entropy; stdlib `secrets`). The CLI shows it once and never again (store law: never stored raw).
- **Hash (stored):** `hash = sha512_hex(f"{name}:{secret}")` — SHA-512 hex of the WHOLE presented string, odoo-code's exact `sha512(f"{login}:{api_key}")` shape (`_validate_odoo_api_key:468`). **Reuse `loremaster.index.records.sha512_hex`** (a pure, tested sha512-hex helper — do NOT hand-roll `hashlib.sha512(...).hexdigest()`; that clone is the packages/ONE-IMPLEMENTATION violation). `hash` is UNIQUE-indexed.
- **verify(presented):** (1) reject blank via `lorerunes.blankness.is_blank(presented)` → deny; (2) split on the **first** colon → `(name, secret)`; if `is_blank(name)` or `is_blank(secret)` → deny (terminal failure, exactly odoo-code `auth.py:187-188`); (3) `h = sha512_hex(presented)`; (4) `SELECT … FROM principal_key WHERE hash = $h` (UNIQUE hash index → O(1), **uniform timing** over a preimage-resistant digest — no name-existence oracle); (5) no row → deny; (6) the four re-checks (F3a) → deny/allow.
- **Why SHA-512 and not bcrypt/argon2 (preempt the security-audit false-positive):** the secret is a **256-bit high-entropy random** token, so a fast unsalted content hash is correct and standard (this is NOT password hashing, which needs slow salted KDFs precisely because passwords are low-entropy). This matches odoo-code and the GitHub/Stripe hashed-token pattern. State this in the module docstring.
- **Constant-time:** provided by the **uniform hash-index lookup**, not by an in-memory compare. 49's DB path does NOT use `hmac.compare_digest` (there is no in-memory secret comparison — the DB equality on the digest is the check). ⚠ Do not let the contract demand `compare_digest` on 49's path — that pin would be testing a mechanism this design deliberately does not use (see F5).

**Identity, restated (the #206 fix):** the wire `name` is the key's label, used for lookup-adjacent audit only; the authenticated identity is the **principal** resolved via the link. `verify` returns `(principal, key_name)`; 39 mints per-**principal** (recommend `subject = principal.email`), never a constant, never per-key — so distinct keyholders get distinct identities (#206 closed) and the same human's multiple keys collapse to one identity (correct).

**Refinement considered and DECLINED by the operator (2026-08-20):** Reading B (opaque token, name off the wire) is strictly better on the security axis (no name-enumeration surface, no per-name wire coupling, and the name still exists as a row column). The colon-split in odoo-code was structurally motivated by its *delegation to Odoo* (the login must be sent to Odoo); lore stores its own keys and resolves the principal via the link, so that motivation does not transfer — I surfaced this as an overridable refinement. The operator confirmed Reading A; **build `<name>:<secret>`, not the opaque token.** (The invariants that would have been common to both — never-store-raw, revoked/expired/suspended → deny, blank → deny — remain the pin set regardless, so nothing is lost by the choice.)

Citations: spec §1C ✅-Adopt; `pp-odoo/mcp/src/code_mcp/auth.py::_validate_odoo_api_key:468` + `:187-188` (split/terminal); `loremaster.index.records.sha512_hex`; `lorerunes.blankness.is_blank`; `secrets.token_urlsafe`.

---

## F5 — DRY vs the kept static `ApiKeyVerifier` [RULED by sidecar — no 39-surface touch, so no escalation]

49's hashed-DB `verify` and `auth.py`'s raw-in-memory `ApiKeyVerifier.verify` are **DIFFERENT MECHANISMS** (DB-backed hashed lookup with revocation/expiry re-check, vs. a rotatable in-memory set of raw secrets compared constant-time). They are NOT two copies of one policy — so the DRY law does not demand merging them.

**What is genuinely shared, and where it lives:**
- **Reject-blank/empty** — the ONE shared predicate. It already lives in `lorerunes.blankness.is_blank` (moved to lorerunes in pkt42 #222; mutation-proven shared across `resolve_secret` and loresigil's validator). **49 REUSES it** for the wire token and both split halves. No new predicate.
- **SecretStr holding** — a pydantic idiom, not shared *policy*. `PrincipalKeyStore` holds its DB password as `SecretStr` (like `PrincipalStore`); the presented key is transient and never stored raw.

**What is NOT shared (state this explicitly so no pin demands it):** the constant-time `hmac.compare_digest` raw-secret comparison is `ApiKeyVerifier`'s mechanism for its *in-memory raw* keys. 49 has no in-memory secret compare (it hashes + index-looks-up), so `compare_digest` does not appear on 49's path and must not be pinned there.

**EXPLICIT, per the brief:** **packet 49 does NOT modify, replace, wrap, or re-home `ApiKeyVerifier` / `build_api_key_verifier` / `BearerAuthMiddleware` / `OriginValidationMiddleware`.** Those are packet 39's kept surface (pkt-39 §4: "Keep `ApiKeyVerifier` untouched"). If a sharing opportunity appeared to require touching 39's surface, that WOULD be an escalation — but it does not (the only shared thing is already in `lorerunes`). [RULED, no escalation.]

DRY LEDGER the contract/builder must produce (per brief-base §6): rows for every new reusable symbol — `PrincipalKeyStore`, `KeyVerification`, `PrincipalKey` value object, the DDL emitters, `set_expires`, `delete`, the CLI verbs — each with the lore query run and disposition (REUSED `is_blank`/`sha512_hex`/`_txn` seams/`build_store` accessors, or HAND-ROLLED with a reason).

Citations: repo CLAUDE.md "ONE IMPLEMENTATION"/brief-base §6; `lorerunes.blankness.is_blank` (+ pkt42 #222 mutation proof at `docs/plans/v2/receipts/2026-07-26-packet42/REPORT-audit-pkt42-review.md`); `auth.py::ApiKeyVerifier`; pkt-39 §4 ("Keep `ApiKeyVerifier` untouched").

---

## F6 — CLI module: one CLI, in `principals.py` [RULED by sidecar]

**RULING: ONE CLI covering BOTH principal verbs and key verbs, living in `loremaster/loremaster/principals.py` (lib + CLI in the one module).**

> ⚠ **INVOCATION SUPERSEDED (operator, 2026-08-20 — POST-close-out):** the CLI is invoked
> via the **`lore-adm` console script** (`[project.scripts] lore-adm = "loremaster.principals:main"`
> in `loremaster/pyproject.toml`), NOT `python -m loremaster.principals`. The reasoning below
> for keeping the CLI IN `principals.py` STILL HOLDS (the entry point targets
> `loremaster.principals:main`, and the `__main__` guard is kept so `-m` remains a harmless
> fallback); only the operator-facing invocation changed — `podman exec lore-<slug> lore-adm …`.

- **Why in `principals.py` (not a new sibling, not a package):** the packet fixes the invocation at `-m loremaster.principals`, and `principals.py` is a MODULE (not a package), so `-m loremaster.principals` runs *that module's* `__main__` guard directly. Putting the CLI in a sibling `principals_cli.py` would force `-m loremaster.principals_cli` (violates the fixed invocation); converting `principals` into a package (`principals/__main__.py`) is a rename/move on a module packet 48 *just* shipped — churn and risk for no behavioural gain. So the CLI (`build_parser()` + `main(argv)->int` + the `__main__` guard) is appended to `principals.py` after `PrincipalStore`, with the guard **LAST**.
- **House idiom to copy:** `index/cli.py` — `build_parser() -> argparse.ArgumentParser` (separately testable), `prog="loremaster.principals"`, `main(argv: list[str] | None = None) -> int`, non-zero exit on failure; env-var **NAMES** via `resolve_config_value`/`resolve_secret` (never values); loud-on-failure/silent-on-success. `snapshot_gc.py` is the async + `SurrealConnectionError`-laundering template — copy its argparse/async/env-var-NAMES/loud-on-failure shape but **NOT** its dry-run/`--execute` gating (struck by the operator, below).
- **The CLI constructs `PrincipalStore` + `PrincipalKeyStore` from config** (both need connection coordinates: `config.surreal.{url,namespace,user_env,password_env}`, `config.effective_surreal_database`). ⚠ `build_store(config)` returns a full `SurrealStore` (chunk/memory/etc.), which is NOT what the CLI needs — the CLI needs the two identity stores, which apply only their own DDL slices at `ensure_ready`. **DRY note:** the coordinate-reading recipe (`resolve_config_value(config.surreal.user_env)` etc.) is the same one `build_store` encapsulates; to avoid a 2nd clone of it, add thin sibling factories next to `build_store` — `build_principal_store(config)` and `build_principal_key_store(config)` — each reading the SAME `config` accessors. Contract author: treat these as new reusable symbols (DRY-ledger rows), and pin that they read the same accessors `build_store` does.

**Registration check (the claim in the brief is CORRECT):** a new module `principal_keys.py` inside the already-registered `loremaster` package is **COPY-covered** by the Containerfile (the whole package dir is copied) and is **NOT a new workspace member.** `scripts/registration_sites.py` derives registration sites as "places where ≥2 member names co-occur"; a new module names zero members, so it yields no new site. **Builder: RUN `./scripts/registration_sites.py` (the check-not-a-list per CLAUDE.md), expecting exit 0 / no new site** — do not hand-edit any member list.

**⚠ `__main__`-guard-last is enforced PER FILE** (`test_server_entrypoint.py` scans `server.py`; `test_scout.py:439` scans `scout.py` — there is NO global scan). So **`principals.py` needs its OWN `test_main_guard_is_last_top_level_statement` pin** — clone the `test_server_entrypoint.py` shape against `loremaster.principals.__file__`. (Pin-checklist item.)

**Dry-run / `--execute` gating — STRUCK BY THE OPERATOR (2026-08-20).** Operator ruling, verbatim: *"Gate none. I hate that paradigm."* This **OVERRIDES both** an earlier sidecar ruling here (which had gated the destructive verbs) **and** spec §1B's "only list is safe by default". The paradigm is removed in full:
- **There is NO `--execute` flag anywhere, and NO dry-run mode.** Every verb performs its effect directly the moment it is run — the plain Unix idiom: silent-on-success, loud-on-failure, non-zero exit on error.
- `list` / `list-keys` are the only reads (they never mutate). `add`, `delete`, `suspend`, `unsuspend`, `set-expiry`, `mint-key`, `revoke-key` all execute their effect immediately when invoked.
- There is **no "gated set" constant** — that concept is gone. `mint-key` generates and prints the secret exactly once, as its normal (only) behaviour.
- Consequence for the snapshot_gc template: keep its argparse/async/env-var-NAMES/`SurrealConnectionError`-laundering/loud-on-failure shape; **drop** its `--execute`/`is_total_wipe`/dry-run scaffolding entirely.

Citations: **operator ruling 2026-08-20 (lore_comms #5064, directive)** — overrides packet scope IN and spec §1B on gating; spec §1B (still governs `-m loremaster.principals` + the house idiom); `index/cli.py::build_parser`/`main`; `snapshot_gc.py` (idiom only, not its gating); `test_server_entrypoint.py:32`; `scripts/registration_sites.py`.

---

## F7 — `PrincipalKeyStore` + `principal_key` DDL: layout + schema [RULED by sidecar]

### Module layout. [RULED]

- New module **`loremaster/loremaster/principal_keys.py`** with `PrincipalKeyStore`, cloning the `PrincipalStore`/`FindingLedger` connection-owner idiom **verbatim** — one lazily-opened signed-in WS connection, double-checked-locking `_ensure_connection`, self-heal via `_drop_connection`, `_query` delegating to the shared `run_query`, `ensure_ready` applying its DDL slice via `execute_transaction`. **NO retry/classification/query policy of its own** (#102/#120) — the `_query` seam is auto-discovered by `test_retry_seam.py`'s scan, so the shared retry pins prove the sharing by mutation. Value object `PrincipalKey(BaseModel, extra="forbid", frozen=True)`.
- **In `surreal_schema.py`:** `PRINCIPAL_KEY_TABLE = "principal_key"`, `_PRINCIPAL_KEY_FIELD_SPECS`, `_principal_key_statements()`, `generate_principal_key_ddl()` — mirroring the `_principal_statements()`/`generate_principal_ddl()` precedent (`surreal_schema.py:1377-1419`, `:1813-1832`). **Fold `_principal_key_statements()` into `generate_ddl` immediately AFTER `_principal_statements()`** (`:1711`) so the primary `write_store.ensure_ready()` creates the table on ship, and expose `generate_principal_key_ddl()` for `PrincipalKeyStore.ensure_ready`.
  - ⚠ **Ordering:** `principal_key.principal` is `record<principal>`, so the `principal` table must be defined first. `_principal_statements()` already precedes it in `generate_ddl`, and `PrincipalKeyStore.ensure_ready` must apply the principal slice OR run after `PrincipalStore.ensure_ready` (a `record<t>` field-def does not *require* the target table to pre-exist at DDL time — unlike a RELATION `IN`/`OUT` edge — but keep the ordered application to match the `briefed`→`agent` precedent and avoid surprises; PROBE if in doubt).

### `principal_key` schema. [RULED]

| column | type | clause | option? | why |
|---|---|---|---|---|
| `hash` | string | `_NON_EMPTY_STRING_ASSERT` | **required** | SHA-512 hex of `<name>:<secret>`; UNIQUE-indexed; the credential check |
| `name` | string | `_NON_EMPTY_STRING_ASSERT` | **required** | the key label (packet doc's "label"); part of `UNIQUE(principal, name)` |
| `principal` | `record<principal>` | (link) | **required** | the owner; new empty table ⇒ non-`option` (F2a) |
| `created_at` | datetime | `DEFAULT time::now()` | **required** | engine-stamped mint time |
| `expires_at` | `option<datetime>` | (none) | **option** | optional key expiry; NONE = never |
| `revoked_at` | `option<datetime>` | (none) | **option** | NONE until revoked; `WHERE revoked_at IS NONE` is the "active" predicate (the `to.seen_at`/`acked_at` idiom — a DEFAULT would make every key look already-stamped) |

- **Indexes:** `UNIQUE(hash)` (the lookup + dedup backstop) and **`UNIQUE(principal, name)`** — see below.
- **Migration clauses (§1.1):** TABLE `IF NOT EXISTS`, FIELD `OVERWRITE`, INDEX `IF NOT EXISTS` — all via the existing `_define_table`/`_define_field`/`_unique_index` helpers. `ALTER` is a trap (§1.3). (§1.8 is N/A — no UNIQUE over an `option<>` column here; both UNIQUE indexes are over required columns.)
- **CONTENT write:** create a key via `CREATE principal_key CONTENT $content RETURN AFTER` (the `PrincipalStore.create` idiom). ⚠ The `record<principal>` value must be bound as a **RecordID** (store-ref §2/§4 — `str(RecordID)` handling; a bare string may not coerce to a link). PROBE the exact CONTENT shape for a `record<>` column against the test store (this is the one store-behaviour question in the schema; confirm before building on it). `created_at` self-stamps; `expires_at`/`revoked_at` omitted ⇒ NONE.

### Is a key's `name` UNIQUE table-wide or per-principal? — PER-PRINCIPAL. [RULED]

**RULING: `UNIQUE(principal, name)`** (per-principal). Two different humans may each name a key `laptop`; global uniqueness would force every human to invent globally-unique labels (poor UX and an information leak about others' key names). `revoke-key --email <e> --name <n>` targets within a principal, so per-principal uniqueness makes revoke deterministic while allowing label reuse across principals. Lookup at verify is by `hash` (globally unique), so per-principal name uniqueness costs nothing on the hot path. (`DEFINE INDEX … FIELDS principal, name UNIQUE` — a record-link column is indexable.)

### `PrincipalKeyStore` public surface (recommended).

```
PrincipalKeyStore(*, url, namespace, database, user, password):
    async ensure_ready() -> None                      # applies generate_principal_key_ddl()
    async mint(*, principal_id|email, name, secret_hash, expires_at=None) -> PrincipalKey
    async list_for(*, email) -> list[PrincipalKey]     # a principal's keys (revoked shown, flagged)
    async revoke(*, email, name) -> PrincipalKey       # sets revoked_at = time::now(); unknown ⇒ NotFound
    async verify(presented) -> KeyVerification | None   # F3/F4
    async close() -> None
Exceptions: PrincipalKeyStoreError(RuntimeError); PrincipalKeyNotFoundError(PrincipalKeyStoreError)
```
- `mint` takes the ALREADY-hashed secret (the CLI generates the secret + calls `sha512_hex`; the store never sees the raw secret except transiently in `verify`'s input — and even there only to hash it). Revoking is `SET revoked_at = time::now() WHERE principal = $pid AND name = $name` (idempotent-ish; a second revoke is a no-op or re-stamps — pick one and pin it). `list_for`/`revoke` resolve the principal id from email (reuse `PrincipalStore.get_by_email` or a shared lookup — do not clone).

Citations: `principals.py` (owner idiom, `_row_to_principal`, CONTENT create, execute_transaction); `surreal_schema.py:1377-1419`/`:1711`/`:1813-1832` (emitter + fold-in precedent); store-ref §1.1/§1.3/§1.8/§2/§4/§5; `_TO_FIELD_SPECS` (`surreal_schema.py:719-728`, the `seen_at`/`acked_at` `option<datetime>`-so-`IS NONE`-is-live idiom).

---

## F8 — CLI render of stored free text: launder it (lead-surfaced 2026-08-20) [RULED by sidecar: YES]

The `list` / `list-keys` verbs render STORED FREE TEXT — principal `email` and `display_name`, key `name`. The repo P8d law: *"Any NEW render of stored free text routes through the shared sanitiser seam … its tests MUST include a hostile fixture (newlines + a row-shaped forgery line + backtick runs)."*

**Reading that would produce different code:** does a TERMINAL-facing render (an admin via `podman exec`, not an MCP surface an LLM reads) warrant the seam, or is it out of the law's LLM-consumer scope?

**RULING: YES — route every rendered free-text field through the shared seam. This is not a close call, and here is why (the seam itself settles it):**
- The canonical seam is **`loremaster.sanitise.sanitise_line`** (finding #34 promoted it out of `search.py`; `loremaster.search._sanitise_line` is now an alias) and its `safe_str(value)` companion (handles `str | None` — right for the optional `display_name`). Read its docstring: it collapses **C0/C1 controls, `\n`, TAB, the ANSI/OSC `ESC` introducer, DEL, bidi override/isolate/mark, zero-width, and line/paragraph separators** to a single space. It is **explicitly designed to defeat terminal-framing** ("cannot break the … line it sits on, escape a fence, or smuggle a hidden/reordered payload"; "in a bidi-aware terminal/UI"). So the seam is NOT MCP-only — it is exactly the launder a terminal render needs.
- **The threat model, written down (per the repo's "a gate needs a threat model" law):** the harm is real even for a terminal admin — a `display_name`/`name` with an embedded newline forges a **fake `list` row** (mis-attributing identity/role); an ANSI/OSC run hijacks the admin's terminal (cursor/color/OSC-52 clipboard); a bidi run visually spoofs an email (Trojan-Source). And the **provenance is trending untrusted**: `email`/`display_name` are admin-typed TODAY, but packet 39's OAuth fill and any future self-service make them **user-chosen** — the render-side launder is the provenance-independent fix (the reason the law is render-side, not write-side). Note `email` and key `name` carry only `_NON_EMPTY_STRING_ASSERT` (non-empty — NOT newline/ANSI-free), so the store does not stop hostile values; the render must.
- **Cost is near-zero and ONE-IMPLEMENTATION demands it:** the seam already exists and is tree-wide; a CLI-private launder would be a clone. "Rigor-vs-speed on serving surfaces resolves toward RIGOR" (Trust Doctrine) closes it.

**Scope of the launder (be precise so the builder doesn't over- or under-apply):**
- **Sanitise:** `email`, `display_name`, key `name` (the free-text fields). Route through `sanitise_line` / `safe_str`.
- **Safe by construction (no launder needed, but `safe_str` is a harmless no-op if applied uniformly):** `status`/`role` (closed-domain, DDL-ASSERT-validated) and datetimes (`created_at`/`expires_at`/`revoked_at`, engine-typed, rendered via `isoformat`).
- **The CLI needs the LINE sanitiser, NOT the backtick-FENCE machinery.** `render_fenced`/`fence_width` wrap **multi-line MCP bodies** in a markdown fence; a terminal does not interpret backticks and the CLI renders only single-line identity fields. Do not wrap CLI output in markdown fences — apply `sanitise_line` to each field.
- **A `--json` mode** (if `list`/`list-keys` provide one) is forgery-safe by construction via the **stdlib `json` encoder** (control chars escaped, strings quoted) — that is its launder; the human/table mode uses `sanitise_line`.

**Defense-in-depth NOTE (flag, not a mandate):** the CLI could also validate `email` format on `add` (reject newlines/controls at write time). That is additive hardening, not the law-required fix — the render-side launder is robust regardless of how a value was written (OAuth fill, future self-service), so pin the render; write-validation is optional.

Citations: repo CLAUDE.md P8d "rendered stored free text" law + Trust Doctrine; `loremaster/loremaster/sanitise.py::sanitise_line`/`safe_str`/`SafeLine` (finding #34); `_NON_EMPTY_STRING_ASSERT` (`surreal_schema.py:370`).

---

## PIN CHECKLIST — what the contract author MUST satisfy

**The packet exit pins (from `49-principal-cli-keys.md`), made concrete:**

1. **Revoked key denied on the NEXT verification** — mint a key, `verify` ⇒ allow; `revoke`; `verify` again ⇒ deny. No cache/TTL anywhere (R12). Mutation proof: break the `revoked_at IS NONE` check → this pin reddens. ⚠ FIXTURE-DISCRIMINATE: assert the SAME presented key that was allowed pre-revoke is denied post-revoke (not a fresh key).
2. **Key never stored raw** — a constructed-leak probe: after `mint`, scan the stored `principal_key` row (all columns) and assert the raw `secret` substring appears NOWHERE; only the sha512 hex is present. POSITIVE CONTROL: assert the row DOES contain the `sha512_hex(presented)` value (so the probe can actually see stored content).
3. **Every verb executes directly — no dry-run, no `--execute` anywhere** (operator ruling 2026-08-20). (a) `build_parser` exposes NO `--execute` flag on any verb (assert it: parsing `--execute` is an unrecognised-argument error). (b) Each destructive verb executes its effect on invocation: `delete <email>` removes the principal + its keys; `suspend <email>` sets status=suspended; `revoke-key <email> <name>` stamps `revoked_at` — each asserted by reading store state AFTER the single invocation (no second "execute" step). (c) `mint-key` prints the secret **EXACTLY ONCE** (one secret line on stdout; a second `mint-key` mints a NEW key, it does not re-print the old secret — the raw secret is unrecoverable after mint). CONTROL for (b): `list`/`list-keys` leave state byte-identical (so the "state changed" probe demonstrably distinguishes a mutating verb from a read).

**Consumer/Trust-Law pins (the served surface):**

4. **Suspended principal's key denied** — mint key for principal P (allow); `suspend` P; `verify` ⇒ deny; `unsuspend`; `verify` ⇒ allow again. (The F3a trust property.) Mutation: drop the `status == active` check → red.
5. **Expired principal denied** and **expired key denied** — SEPARATE pins, DIFFERENT fixtures: (a) principal `expires_at` in the past ⇒ deny even with a live key; (b) key `expires_at` in the past ⇒ deny even with a live principal. A short-past-expiry fixture for each. (QUANTIFIER-LAW: pin the deny property for EACH of the four conditions independently — do not let one fixture satisfy the ∀ vacuously.)
6. **Verify returns the PRINCIPAL, per-principal identity (#206 guard)** — two DISTINCT principals each with a key: `verify` returns DISTINCT principals; and ONE principal with TWO keys: `verify` on either returns the SAME principal. (This is the #206 collapse guard — the exact defect the packet exists to avoid.) ⚠ FIXTURE-DISCRIMINATE: a build that returned a constant/per-key identity must FAIL this — so the fixture MUST have ≥2 principals AND ≥1 principal with ≥2 keys (monoculture of one principal / one key each passes a broken build).
7. **Blank / malformed key denied** — `verify("")`, `verify("   ")`, `verify(":secret")`, `verify("name:")`, `verify("nocolon")` all ⇒ deny (terminal, via `is_blank` + split validation). Mutation: replace `is_blank` body → callers redden (proves the shared predicate is really used).
8. **Uniform deny (no oracle)** — "no such key", "revoked", "expired", "suspended" all return the SAME `None` to the caller; the DENIAL REASON appears only in a laundered log, never in the return or an exception message reaching the caller. (Trust: the response names its bound; it does not leak which condition failed.)

**Schema / migration pins:**

9. **`generate_principal_key_ddl()` is idempotent** — apply twice, no raise, no row wipe (TABLE/INDEX `IF NOT EXISTS`, FIELD `OVERWRITE`).
10. **`UNIQUE(principal, name)` per-principal** — two principals may share a name; the SAME (principal, name) twice is rejected. And **`UNIQUE(hash)`** — a duplicate hash is rejected (backstop).
11. **`option<datetime>` NONE round-trips** — a key with no `expires_at`/`revoked_at` reads back `None` (explicit projection; store-ref §2 `option<>` KeyError trap — the reader lists columns, never `SELECT *`).
12. **DDL folded into `generate_ddl`** — assert `principal_key` DDL appears in the full `generate_ddl(dim=…)` output (not only the slice) — a build that folds it into the slice but forgets `generate_ddl` would leave the primary store without the table (#131-class: virgin-DB fixtures pass; a real deploy fails). Mutation: remove the `+= _principal_key_statements()` line → red.

**Cascade / delete pins:**

13. **`delete` cascades keys** — a principal with N keys: after `delete` (executes directly — no `--execute`), both the principal row AND all N `principal_key` rows are gone (no orphans — record links don't auto-clean, §4). And the delete is ONE transaction (a mid-cascade failure leaves neither half committed).
14. **PIN THE MISS — cascade forward-scope** — a test/comment asserting the cascade covers `principal_key` ONLY, with the named re-open trigger ("revisit when packet 3A adds `memory.owner: record<principal>`"). Goes RED-by-intent the day a new `record<principal>` link is added without revisiting.

**Structure / house-law pins:**

15. **`__main__`-guard-last for `principals.py`** — its OWN AST pin (clone `test_server_entrypoint.py:32` against `loremaster.principals.__file__`); there is no global scan.
16. **`build_parser()` separately testable** — parse each verb's args without running; `prog == "loremaster.principals"`; unknown verb / missing required arg ⇒ non-zero exit.
17. **Sharing proven by mutation** — (a) mutate `is_blank` → 49's verify + the other callers redden; (b) mutate the shared principal-row→`Principal` mapper → BOTH stores redden (no cloned mapper, F3); (c) `_query` is discovered by `test_retry_seam.py`'s scan (no private retry policy).
18. **Env-var indirection** — the CLI carries env-var NAMES (`--user-env`/`--password-env` via `resolve_config_value`/`resolve_secret`), never values; the password is a `SecretStr` to the SDK seam; no secret is ever printed (except the one-time minted key line).
19. **CLI render of stored free text is laundered (P8d rendered-free-text law — F8).** Every free-text field `list`/`list-keys` renders — principal `email`/`display_name`, key `name` — routes through the shared `loremaster.sanitise.sanitise_line` / `safe_str` seam (NOT a CLI-private launder). Prove the sharing by **mutation**: break `sanitise_line`'s body → the CLI render pins redden ALONGSIDE the other seam callers (ONE IMPLEMENTATION — a private copy would stay green). **HOSTILE FIXTURE (mandatory):** a principal `display_name` AND a key `name` each containing embedded newlines + a **row-shaped forgery line** (e.g. `evil\n  attacker@x.com   admin   active`) + **backtick runs**; assert the rendered output (a) contains EXACTLY the expected record/row count — the forgery produces NO second row; (b) renders the hostile value as ONE collapsed line with control/`\n`/ANSI-ESC/bidi/zero-width chars neutralised to spaces; (c) if a `--json` mode exists, it emits via the stdlib `json` encoder (control chars escaped by construction). ⚠ Single-line-only fixtures are the documented way this class stays green — the fixture MUST be multi-line + row-shaped. NOTE: pin the LINE sanitiser (`sanitise_line`), NOT the markdown backtick-FENCE machinery (`render_fenced`/`fence_width`) — the CLI renders single-line identity fields, not multi-line MCP bodies.

**Satisfiability receipt** (C-DEF class): the adversary's reference build goes 0-failed against this contract, INCLUDING after any lint-demanded cleanup — before any builder sees it.

---

## Escalations & flags (for operator awareness — none blocks the packet)

- **F4 wire format — RESOLVED by operator 2026-08-20:** `<name>:<secret>` CONFIRMED; the opaque-token refinement was considered and DECLINED. Build Reading A.
- **Dry-run / `--execute` — STRUCK by operator 2026-08-20** (*"Gate none. I hate that paradigm."*): no dry-run, no `--execute`, every verb executes directly; only `list`/`list-keys` are reads. ⚠ **Ripple for the lead:** the packet doc `docs/plans/v2/49-principal-cli-keys.md` still carries `strict dry-run unless --execute` in **Scope IN** and `CLI dry-run mutates nothing` in **Exit** — both are now superseded by this ruling and should be updated (that file is outside this doc's writable set — flagging, not editing).
- **Forward-dependency on packet 39** — 39's api-key-branch mint (§4) must, when it consumes 49's `verify`, mint per-**principal** (`subject = principal.email`), not per-key-name. 49 returns the `Principal` to enable this; 49 changes no 39 code.
- **PIN-THE-MISS (F2)** — the delete cascade is scoped to `principal_key` by construction as of 2026-08-20; packet 3A's `memory.owner` is the named re-open trigger.

**Packages considered:** `secrets.token_urlsafe` — `keep` (stdlib, correct for high-entropy key generation; read: stdlib signature). `hashlib` — `replace` with the existing `loremaster.index.records.sha512_hex` wrapper (read: its source, `records.py:108`). `argparse` — `keep` (stdlib; the house CLI idiom). `cachetools`/TTL — **rejected** by R12 (revocation must beat any cache; read: pkt-39 §3-R12). Password KDFs (`bcrypt`/`argon2`) — **not applicable** (the secret is high-entropy random, not a password; read: odoo-code `_validate_odoo_api_key` uses unsalted sha512 for the same reason).
**Reuse ledger:** 5 external reuses dispositioned (`is_blank`, `sha512_hex`, `sanitise_line`/`safe_str`, `_txn` seams, `build_store` accessors); all new symbols routed through the existing owner/emitter idioms.
