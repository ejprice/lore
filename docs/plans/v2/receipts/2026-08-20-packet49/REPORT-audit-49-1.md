# REPORT-audit-49-1 — COLD AUDIT of packet 49 (principal CLI + per-user API keys)

`brief-base v14 read` · `brief project v7 read`

## SUMMARY BLOCK

- **Capability check:** model = **claude-opus-4-8** (confirmed: `CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8`; cannot self-read, so this is the env receipt). All brief-demanded tools present (lore via ToolSearch, test store `ws://127.0.0.1:18000` reachable, gates runnable).
- **State:** done-with-deviations — one packet-49-caused blocker found (Finding A), one pre-existing orphan surfaced (Finding B).
- **VERDICT: NO-GO** — sole blocker is **Finding A**, a ONE-WORD prose regression: `principals.py:766` contains
  the literal `high-entropy token`, a banned CORPSE_PROSE phrase, turning the repo-wide P8d invariant
  `test_secret_leak_vectors.py::TestTheEntropyMachineryIsGone::test_no_PRODUCTION_prose_teaches_a_mechanism_it_does_not_run`
  from GREEN → RED_ORPHANED. Behavior, security surface, DDL, DRY, cascade, and all in-scope gates are GREEN
  and independently verified (29/29 live probes + mutation proof). Fix: reword to `high-entropy random token`
  (the phrasing `principal_keys.py` already uses safely) — then re-audit → GO.
- **Graded:** `4909bcd` · HEAD-at-report: `4909bcd` · SAME
- **Packages considered:** none — I am a read-only auditor; I specified/built no mechanism (probes are throwaway, pasted verbatim below).
- **Reuse ledger:** none — no new symbols introduced.
- Gate re-runs: pytest **775 passed** (6 suites, `-n auto`, 12.36s); ruff **clean**; mypy on the 5 packet-49 prod files **clean (exit 0)**; full typecheck RED is the pre-existing **#333 packet-39 auth-WIP** bound (0 packet-49 files in any error).
- receipt POINTERS: §Gates · §Probes · residual table at end.

---

## GATES (re-run by me, not trusted from the builder)

### pytest — 6 packet-49 suites, `uv run pytest -n auto`
```
775 passed, 1 warning in 12.36s
```
Suites: `test_principal_keys_schema.py` · `test_principal_keys_store.py` · `test_principals_cli.py` ·
`test_principals_store.py` · `test_retry_seam.py` · `test_comms_cli.py`.
The single warning is a benign `RuntimeWarning: coroutine '_empty_subscription' was never awaited`
inside `test_retry_seam.py`'s `contextlib.suppress(Exception)` — a test-side artefact, not a failure.
Real passed-COUNT present (775), so this is not a "no tests ran" false green.

### ruff — `uv run ruff check .`
```
All checks passed!   (exit 0)
```

### typecheck — `bash scripts/typecheck.sh`
Full runner exits 1. The RED is entirely the **packet-39 auth-WIP #333 bound**:
- `lorerunes` leg: 89 errors in 3 TEST files (`test_roster_parser`, `test_posture`,
  `test_email_normalisation`) — all `Module "lorerunes" has no attribute {RosterParse, parse_roster,
  normalize_email, Posture, is_admitted, SCOPE_READ/WRITE, …}` (unbuilt packet-39 symbols).
- `loremaster` leg: **102** errors in 8 TEST files (`test_auth*`, `test_permission_resolver_seam`,
  `test_hosted_readonly_posture`, `test_google_token_verifier`, `test_allowlist_roster`,
  `_auth_fixtures`) — all missing auth/posture symbols (`LoreTokenVerifier`, `GoogleOAuthConfig`,
  `resolve_posture`, `PostureConfigError`, `derive_edge_policy`, …).
- **grep of the whole typecheck log for any packet-49 file (`principal_keys.py`, `principals.py`,
  `surreal_schema.py`, `config.py`, `comms_cli.py`) → ZERO hits.**
- **Targeted `uv run mypy` on exactly the 5 packet-49 production files → `Success: no issues found
  in 5 source files` (exit 0).**

**Verdict on the gate: packet 49 adds ZERO new type errors.** The RED is the ruled/owned #333
packet-39 bound (CLAUDE.md: "packet 39's red typecheck is a ruled, owned bound doing its job").

---

## PROBES (adversarial — REFUTE targets)

All store probes ran against the **TEST store `ws://127.0.0.1:18000`** (never `:18500`), each on a fresh
`unique_database()`, reaped after. The probe instrument is pasted VERBATIM at the end (brief-base §1) and
prints PASS/FAIL per check with positive controls. **Result: 29/29 checks PASS.**

### REFUTE 1 — DDL / #131 (the DEPLOY path). PASS.
- Offline: `generate_ddl(dim=256)` EMITS `DEFINE TABLE IF NOT EXISTS principal_key` + both UNIQUE indexes
  (`principal_key_hash`, `principal_key_principal_name`), with `principal` defined BEFORE `principal_key`
  (idx 8736 < 9597). Clauses match store-law §1.1: TABLE/INDEX `IF NOT EXISTS`, FIELD `OVERWRITE`.
- Live (PRIMARY path): applied the FULL `generate_ddl` to a virgin DB → `INFO FOR DB` shows `principal_key`;
  `INFO FOR TABLE principal_key` shows both UNIQUE indexes and `principal TYPE record<principal>`.
  A build that folded into the slice but not `generate_ddl` would fail here — it does not.

### REFUTE 2 — DDL / #107 (dirty-store migration). PASS.
- Applied OLD schema (`generate_principal_ddl()` — principal, NO principal_key) → `CREATE principal` row →
  applied NEW schema (full `generate_ddl`). Result: `principal_key` table CREATED on the dirty store AND
  the pre-existing principal row SURVIVED (`{'email':'legacy@example.com','display_name':'Legacy Admin'}`),
  both UNIQUE indexes present. The `IF NOT EXISTS` table + `OVERWRITE` fields behave per §1.1/§1.4.

### REFUTE 3 — verify(): the load-bearing served surface. PASS (all sub-parts).
- **(a) NO cache / R12:** minted `laptop:secretA` → verify ALLOWS (returns owner `alice`); `revoke` →
  verify(**same presented cred**) → `None` on the very next call. No TTL/residual window.
- **(c) all FOUR conditions, each isolated (quantifier-law):** cond1 revoked→deny; cond2 key-expired
  (live principal)→deny; cond3 principal-suspended (live key)→deny, and `unsuspend` re-ALLOWS; cond4
  principal-expired (live key)→deny. Each fired with the other three passing.
- **(b) uniform deny / no oracle:** 7 distinct failure modes (revoked, key-expired, suspended,
  principal-expired, no-such-key, `""`, `nocolon`) ALL return the identical `None`; the reason is logged
  DEBUG-only (`principal.key.verify.denied` extra=`reason`, a fixed token — never the credential), never
  returned, never raised. Confirmed by code read of `verify` + `_deny`.
- **(d) no name-existence timing oracle:** `verify` returns `self._deny("no-such-key")` on an empty hash
  lookup BEFORE the second (`get_by_email`) query — so the 2nd query fires ONLY on a hash HIT, and a hash
  hit requires the correct secret (lookup is by `sha512_hex(<whole credential>)`). No name-only oracle.
- **(e) hashes the WHOLE `<name>:<secret>`:** `verify` computes `sha512_hex(presented)` on the whole
  string; the mint stores `sha512_hex(f"{name}:{secret}")`. A build hashing only the secret/name would
  deny a real key — the probe's live ALLOW proves the whole-string hash.
- **Positive control:** a fully-live credential ALLOWS and returns the correct owner + `key_name`.

### REFUTE 4 — never-stored-raw. PASS.
- Minted a key whose raw secret was a unique sentinel; `SELECT * FROM principal_key` over the whole table →
  the raw secret substring and the wire `name:secret` are ABSENT. **Positive control:** the
  `sha512_hex` value IS present (the probe can see stored content).

### REFUTE 5 — key shown once. PASS.
- Only `_cmd_mint_key` prints the raw credential (`print(credential)`, one line). Every other `print()` in
  `principals.py` renders sanitised metadata (list rows, delete audit line, key rows) or a stderr error.
  No verb re-emits a raw secret; the secret is unrecoverable after mint (never stored raw — REFUTE 4).

### REFUTE 6 — rendered stored free text laundered (P8d / F8). PASS.
- `_render_principal_line`/`_render_key_line` route `email`/`display_name`/key `name` through the SHARED
  `loremaster.sanitise.safe_str`. Fed `'evil\n  attacker@x.com   admin   active\x1b[31m```'` → output is a
  SINGLE line, newline collapsed to spaces (no phantom row), ANSI `ESC` stripped (inert `[31m` text
  remains, harmless). The packet's OWN hostile-fixture pin exists (`test_principals_cli.py:601-606`,
  pinning `sanitise_line`/`safe_str`).

### REFUTE 7 — no --execute / creds-free / __main__-guard-last. PASS.
- `--execute`/`dry-run` appear ONLY in explanatory PROSE (module comment + `build_parser` docstring, both
  documenting the deliberate ABSENCE). No `add_argument` names them. Parser REJECTS `--execute`
  (`unrecognized arguments: --execute`, SystemExit 2).
- Creds-free: the CLI loads via `load_surreal_only_config` (env-free `model_validate`, no eager Anthropic
  key); `test_principals_cli.py` (in the green 775) runs without an Anthropic key.
- `__main__`-guard-last: the `if __name__ == "__main__"` block is the LAST top-level AST node of
  `principals.py`; its own pin is `test_principals_cli.py:301 test_main_guard_is_the_last_top_level_statement`.

### REFUTE 8 — cascade (delete). PASS.
- A principal with 3 keys → `delete()` removes the principal AND all 3 `principal_key` rows (returns
  cascaded=3), leaving ZERO orphans (record links don't auto-clean, §4). The two DELETEs (children first,
  then parent) run in ONE `execute_transaction` (`BEGIN…COMMIT`, every statement's status checked) — code
  read confirms atomicity; the probe confirms no orphaned/dangling `principal_key` rows post-delete.

### REFUTE 9 — DRY reality. PASS (3 legs, one mutation-proven).
- **`_row_to_principal` shared, not cloned — MUTATION-PROVEN.** `cp -a` backup → forced a wrong `email` in
  `PrincipalStore._row_to_principal` → BOTH suites reddened: `test_principals_store.py` (5) AND
  `test_principal_keys_store.py` (2: `test_verify_returns_the_owning_principal_and_key_name`,
  `test_distinct_principals_and_one_principal_two_keys`). So `verify` routes through the shared mapper (via
  `get_by_email`) — NOT a private copy wearing the shared name. Restored byte-exact (md5
  `a1f83ca486dc35d0625d3c662bd60294`, `git diff` empty).
- **config-loader promotion real (contract-blind diff pass).** There were TWO private `_load_surreal_config`
  copies — `comms_cli.py` (at base) and `principals.py` (added in `b6fc654`) — both DELETED in `4909bcd`
  and replaced by `config.load_surreal_only_config`. Body is byte-identical
  (`yaml.safe_load(...); LoreConfig.model_validate(raw)`); the only delta is the param widened `Path` →
  `str | Path` (`Path(config_path)` accepts both). Same yaml load, same creds-free validate, same error
  shapes (`ValidationError` / `FileNotFoundError`). **No removed behavior.**
- **`_query` rides shared `run_query`.** `test_retry_seam.py` registers `PrincipalKeyStore` in both
  `_SEAM_REJECTION_EVENTS` (`principal.key.query.rejected`) and `_SEAM_REJECTION_NOUNS`
  (`principal key query`) per #353; 58 principal retry-seam tests pass. No private retry/classification.

### REFUTE 10 — natural-language surfaces. **ONE DEFECT (Finding A).**
- Full CORPSE_PROSE sweep of all 5 packet-49 prod files → exactly ONE hit: `principals.py:766`
  `high-entropy token`. `principal_keys.py` correctly wrote `high-entropy random token` (NOT a substring of
  the banned literal), so the builder knew the constraint in one file and missed it in the other.
- Retired lore tool names (`what_imports`/`blast_radius`) appear at `surreal_schema.py:915,1649` — these are
  OUTSIDE packet-49's diff hunks (pre-existing prose, not packet-49's).

---

## FINDINGS

### Finding A — BLOCKER (packet-49-caused). Corpse prose "high-entropy token" in `principals.py:766`. [lore finding #392]
- **What:** `principals.py:766` (the `_SECRET_ENTROPY_BYTES` comment) reads *"…the high-entropy token a
  fast unsalted content hash is correct for…"*. `high-entropy token` is one of
  `test_secret_leak_vectors.py::TestTheEntropyMachineryIsGone.CORPSE_PROSE`
  `["Shannon entropy", "high-entropy token", "entropy threshold", "catch-all backstop"]` — literals that
  named a DELETED log-scrubbing entropy heuristic (packet 42, `logging_setup.py`). The invariant
  `test_no_PRODUCTION_prose_teaches_a_mechanism_it_does_not_run` bans them, by bare substring, in EVERY
  workspace production source (no deletion-marker exemption on the production leg).
- **Reproduction:**
  `uv run pytest -q "loremaster/tests/test_secret_leak_vectors.py::TestTheEntropyMachineryIsGone::test_no_PRODUCTION_prose_teaches_a_mechanism_it_does_not_run"`
  → `AssertionError: … ['loremaster/principals.py: high-entropy token']`.
- **Causation (proven):** the phrase was ABSENT at the packet-49 base (`git show 075a1bd~1:…/principals.py`
  → 0 hits) and PRESENT at HEAD (1 hit). The scanning test was NOT modified by packet 49. The offenders
  list is a SINGLE packet-49 file, so the pin was GREEN before packet 49 and packet 49 turned it RED.
- **Why the builder's gate missed it:** `test_secret_leak_vectors.py` is not in packet 49's scoped suite —
  this is exactly the P8d "natural-language surface whose consistency with code no *scoped* gate checks"
  class the cold audit exists to catch.
- **Impact:** turns the full-suite `pytest` gate to **RED_ORPHANED** (the currency check FAILS). Per repo
  law "red-with-nobody's-name-on-it is the disease", a wave cannot close clean with a self-introduced
  orphan.
- **Fix (recommended, one word):** reword `principals.py:766` to `the high-entropy random token` —
  the exact safe phrasing `principal_keys.py:21-23` already uses; semantically identical, drops the banned
  substring. (Alternative — adjudicate/narrow the pin to allow a legitimate `secrets.token_urlsafe`
  description — is a riskier change to a P8d invariant and is NOT recommended.)

### Finding B — PRE-EXISTING orphan (NOT packet-49-caused; packet 49 nudged it). Harness docstring count stale.
- **What:** `_surreal_harness.py` docstring says *"56 test files import this harness"*; 61 actually do.
  `test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts`
  fails `assert 56 == 61`.
- **Causation:** at the packet-49 base the docstring already said 56 while 58 files imported it
  (61 − 3 packet-49-new importers: `test_principal_keys_schema.py`, `test_principal_keys_store.py`,
  `test_principals_cli.py`) → **already RED before packet 49** (58 ≠ 56). Packet 49 added 3 importers
  without bumping the docstring, widening the drift 56→(58)→61.
- **Surfaced per scope law (not silently dropped).** Decision for the operator: either bump the harness
  docstring count as part of closing packet 49 (a one-number edit, cheap, and packet 49 did add 3
  importers), or treat it as a separate pre-existing cleanup. It is NOT in packet 49's writable set and I
  did not edit it. `_surreal_harness.py` was not touched by packet 49.

### Residuals (informational — non-blocking, no action required for GO)
| # | file:symbol | note | severity |
|---|---|---|---|
| A | `loremaster/loremaster/principals.py:766` | **BLOCKER** — corpse prose `high-entropy token` → RED_ORPHANED pin (Finding A) | blocking |
| B | `loremaster/tests/_surreal_harness.py` docstring | pre-existing orphan: says 56 importers, 61 actual; packet 49 added 3 (Finding B) | pre-existing / operator-decision |
| R1 | `principals.py::PrincipalStore.delete` | the key-COUNT read is taken OUTSIDE the cascade txn (comment discloses the tiny window). The cascade DELETE is `WHERE principal=$pid` (removes ALL keys regardless), so no orphan can arise — only the reported audit *number* could be stale under a concurrent mint. Acceptable for an admin op; disclosed. | info |
| R2 | `principals.py` `add` verb | the CLI cannot set `--role`/`--subject` on `add` (role defaults `member`, subject filled by pkt 39) — per design, but means an ADMIN principal cannot be minted through this CLI yet. Flag for operator awareness. | info |
| R3 | `principal_keys.py::_record_id_part` vs `principals.py::delete` inline `partition(":")[2]` | two tiny copies of "extract the id part of a `str(RecordID)`" — trivia-level duplication (not policy), both handle the no-colon case; could share one helper. | info (nit) |
| R4 | `principal_keys.py::verify` | two round-trips per successful verify (hash SELECT that derefs `owner_email`, then `get_by_email`). The design's sanctioned two-query fallback (chosen to reuse `_row_to_principal`); correct, minor extra hot-path query. | info |

---

## CONCLUSION

**GO/NO-GO: NO-GO**, on a single, precisely-located, one-word prose regression (**Finding A**). The packet's
BEHAVIOR is correct and independently proven — 775 scoped tests + 29/29 live adversarial probes + a mutation
proof of the load-bearing DRY claim + a contract-blind diff pass of the config-loader promotion; ruff clean;
packet-49 files mypy-clean; the full-typecheck RED is the adjudicated #333 packet-39 bound. The ONLY thing
between this packet and a clean deploy is rewording `principals.py:766` `high-entropy token` →
`high-entropy random token` (and, at the operator's discretion, bumping the harness docstring count for
Finding B). After the one-word fix + a re-run of `test_secret_leak_vectors.py`, this flips to **GO**.

**Graded: `4909bcd` · HEAD-at-report: `4909bcd` · SAME.**

---

## Gate re-run tails (receipts)
- `pytest -n auto` (6 packet-49 suites): `775 passed, 1 warning in 12.36s`
- `ruff check .`: `All checks passed!` (exit 0)
- targeted `mypy` (5 packet-49 prod files): `Success: no issues found in 5 source files` (exit 0)
- `pending_contract_gate.py --currency`: `typecheck RED_ADJUDICATED (packet-39-pending-build)` · `ruff GREEN`
  · `pytest RED_ORPHANED — 2 residuals` (Finding A packet-49-caused; Finding B pre-existing)
- store probe (`ws://127.0.0.1:18000`): `29/29 checks passed`

---

## APPENDIX — the probe instrument (verbatim, per brief-base §1)

Run from repo root: `uv run python <this-file>`. Uses the test harness (`loremaster/tests/_surreal_harness.py`),
mints a `unique_database()` per probe on `ws://127.0.0.1:18000`, reaps it after. Every negative is paired
with a positive control.

```python
"""Cold-audit probe for packet 49 — run against the TEST store ws://127.0.0.1:18000."""
from __future__ import annotations
import asyncio, sys
from datetime import UTC, datetime, timedelta
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import connect_admin, drop_database, make_env, unique_database
from loremaster.index.records import sha512_hex
from loremaster.principal_keys import KeyVerification, PrincipalKeyStore
from loremaster.principals import PrincipalNotFoundError, PrincipalStore
from loremaster.store import surreal_schema
PRODUCTION_DIM = 2048
RESULTS: list[tuple[str, bool, str]] = []

def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail)); print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

def stores_for(env):
    ps = PrincipalStore(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    ks = PrincipalKeyStore(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    return ps, ks

async def probe_131_and_107():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM); conn = await connect_admin(env)
    try:
        full_ddl = surreal_schema.generate_ddl(dim=PRODUCTION_DIM)
        await conn.query(f"BEGIN;\n{full_ddl}COMMIT;\n")
        info = await conn.query("INFO FOR DB"); tables = info.get("tables", {}) if isinstance(info, dict) else {}
        check("P1 #131: principal_key present after PRIMARY generate_ddl", "principal_key" in tables)
        tinfo = await conn.query("INFO FOR TABLE principal_key"); idxs = tinfo.get("indexes", {}) if isinstance(tinfo, dict) else {}
        check("P1 #131: UNIQUE(hash) index present", "principal_key_hash" in idxs, str(list(idxs)))
        check("P1 #131: UNIQUE(principal,name) index present", "principal_key_principal_name" in idxs)
        fields = tinfo.get("fields", {}) if isinstance(tinfo, dict) else {}
        check("P1 #131: principal is record<principal> link", any("record<principal>" in str(v) for v in fields.values()))
    finally:
        await drop_database(env); await conn.close()
    env2 = make_env(database=unique_database(), dim=PRODUCTION_DIM); conn2 = await connect_admin(env2)
    try:
        await conn2.query(f"BEGIN;\n{surreal_schema.generate_principal_ddl()}COMMIT;\n")
        info_old = await conn2.query("INFO FOR DB"); t_old = info_old.get("tables", {}) if isinstance(info_old, dict) else {}
        check("P2 #107: OLD schema has principal, NOT principal_key", "principal" in t_old and "principal_key" not in t_old)
        await conn2.query("CREATE principal CONTENT { email: $e, display_name: $d } RETURN AFTER", {"e": "legacy@example.com", "d": "Legacy Admin"})
        await conn2.query(f"BEGIN;\n{surreal_schema.generate_ddl(dim=PRODUCTION_DIM)}COMMIT;\n")
        info_new = await conn2.query("INFO FOR DB"); t_new = info_new.get("tables", {}) if isinstance(info_new, dict) else {}
        check("P2 #107: principal_key CREATED by migration onto dirty store", "principal_key" in t_new)
        rows = await conn2.query("SELECT email, display_name FROM principal WHERE email = $e", {"e": "legacy@example.com"})
        check("P2 #107: pre-existing principal row SURVIVED", isinstance(rows, list) and len(rows) == 1 and rows[0].get("email") == "legacy@example.com", str(rows))
        pinfo = await conn2.query("INFO FOR TABLE principal_key"); pidx = pinfo.get("indexes", {}) if isinstance(pinfo, dict) else {}
        check("P2 #107: migrated principal_key has both UNIQUE indexes", "principal_key_hash" in pidx and "principal_key_principal_name" in pidx)
    finally:
        await drop_database(env2); await conn2.close()

async def probe_verify():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM); ps, ks = stores_for(env); conn = await connect_admin(env)
    try:
        await ps.ensure_ready(); await ks.ensure_ready()
        now = datetime.now(UTC); past = now - timedelta(days=1)
        await ps.create(email="alice@x.com", display_name="Alice")
        await ks.mint(email="alice@x.com", name="laptop", secret_hash=sha512_hex("laptop:secretA"))
        v = await ks.verify("laptop:secretA")
        check("P3 control: live cred ALLOWS + returns owner", isinstance(v, KeyVerification) and v.principal.email == "alice@x.com" and v.key_name == "laptop")
        await ks.revoke(email="alice@x.com", name="laptop"); v_rev = await ks.verify("laptop:secretA")
        check("P3 cond1: REVOKED denied on next call (same cred)", v_rev is None)
        await ps.create(email="bob@x.com", display_name="Bob")
        await ks.mint(email="bob@x.com", name="ci", secret_hash=sha512_hex("ci:secretB"), expires_at=past)
        v_kexp = await ks.verify("ci:secretB"); check("P3 cond2: EXPIRED key denied", v_kexp is None)
        await ps.create(email="carol@x.com", display_name="Carol")
        await ks.mint(email="carol@x.com", name="phone", secret_hash=sha512_hex("phone:secretC"))
        v_pre = await ks.verify("phone:secretC"); await ps.set_status(email="carol@x.com", status="suspended")
        v_susp = await ks.verify("phone:secretC")
        check("P3 cond3: SUSPENDED denied; allowed before", isinstance(v_pre, KeyVerification) and v_susp is None)
        await ps.set_status(email="carol@x.com", status="active"); v_re = await ks.verify("phone:secretC")
        check("P3 cond3b: UNSUSPEND re-allows", isinstance(v_re, KeyVerification))
        await ps.create(email="dave@x.com", display_name="Dave", expires_at=past)
        await ks.mint(email="dave@x.com", name="tablet", secret_hash=sha512_hex("tablet:secretD"))
        check("P3 cond4: EXPIRED principal denied", (await ks.verify("tablet:secretD")) is None)
        outs = {m: await ks.verify(m) for m in ["", "   ", ":secret", "name:", "nocolon", "  :  "]}
        check("P3 blank/malformed all denied", all(o is None for o in outs.values()))
        v_nsk = await ks.verify("ghost:nonexistent"); check("P3 no-such-key denied", v_nsk is None)
        check("P3 UNIFORM deny (no oracle)", all(x is None for x in [v_rev, v_kexp, v_susp, v_nsk, outs[""], outs["nocolon"]]))
        va = await ks.verify("phone:secretC")
        await ps.create(email="eve@x.com", display_name="Eve"); await ks.mint(email="eve@x.com", name="laptop", secret_hash=sha512_hex("laptop:secretE"))
        ve = await ks.verify("laptop:secretE")
        check("P3 #206: distinct principals → distinct identities", va.principal.email == "carol@x.com" and ve.principal.email == "eve@x.com")
        await ks.mint(email="eve@x.com", name="second", secret_hash=sha512_hex("second:secretE2"))
        ve1 = await ks.verify("laptop:secretE"); ve2 = await ks.verify("second:secretE2")
        check("P3 #206: one principal's two keys → SAME identity", ve1.principal.id == ve2.principal.id and ve1.key_name != ve2.key_name)
        raw = "RAWSECRET-ZZZ-should-never-be-stored-123"
        await ps.create(email="frank@x.com", display_name="Frank"); await ks.mint(email="frank@x.com", name="fk", secret_hash=sha512_hex(f"fk:{raw}"))
        blob = repr(await conn.query("SELECT * FROM principal_key"))
        check("P4 never-stored-raw: raw secret absent", (raw not in blob) and (f"fk:{raw}" not in blob))
        check("P4 control: the sha512 HASH is present", sha512_hex(f"fk:{raw}") in blob)
    finally:
        await ps.close(); await ks.close(); await drop_database(env); await conn.close()

async def probe_cascade_and_unique():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM); ps, ks = stores_for(env); conn = await connect_admin(env)
    try:
        await ps.ensure_ready(); await ks.ensure_ready()
        await ps.create(email="idem@x.com", display_name="Idem"); await ks.mint(email="idem@x.com", name="k1", secret_hash=sha512_hex("k1:s1"))
        await ks.ensure_ready(); check("P7 idempotent ensure_ready: row survives", len(await ks.list_for(email="idem@x.com")) == 1)
        await ps.create(email="gone@x.com", display_name="Gone")
        for i in range(3): await ks.mint(email="gone@x.com", name=f"k{i}", secret_hash=sha512_hex(f"k{i}:secret{i}"))
        check("P5 cascade: delete returns count 3", (await ps.delete(email="gone@x.com")) == 3)
        check("P5 cascade: principal removed", (await ps.get_by_email("gone@x.com")) is None)
        dangling = await conn.query("SELECT id FROM principal_key WHERE principal.email = NONE OR principal = NONE")
        check("P5 cascade: NO orphaned key rows", isinstance(dangling, list) and len(dangling) == 0, str(dangling))
        await ps.create(email="uniq@x.com", display_name="Uniq"); await ks.mint(email="uniq@x.com", name="a", secret_hash=sha512_hex("shared:hash"))
        dh = False
        try: await ks.mint(email="uniq@x.com", name="b", secret_hash=sha512_hex("shared:hash"))
        except Exception as e: dh = "PrincipalKeyStoreError" in type(e).__name__
        check("P6 UNIQUE(hash): duplicate rejected LOUD", dh)
        await ks.mint(email="uniq@x.com", name="laptop", secret_hash=sha512_hex("laptop:u1")); dn = False
        try: await ks.mint(email="uniq@x.com", name="laptop", secret_hash=sha512_hex("laptop:u2"))
        except Exception as e: dn = "PrincipalKeyStoreError" in type(e).__name__
        check("P6 UNIQUE(principal,name): same name twice rejected", dn)
        await ps.create(email="uniq2@x.com", display_name="Uniq2"); ok = True
        try: await ks.mint(email="uniq2@x.com", name="laptop", secret_hash=sha512_hex("laptop:other"))
        except Exception: ok = False
        check("P6 UNIQUE(principal,name): same name across principals allowed", ok)
        nf = 0
        for coro in (ks.mint(email="ghost@x.com", name="z", secret_hash=sha512_hex("z:z")), ks.revoke(email="ghost@x.com", name="z"), ks.list_for(email="ghost@x.com")):
            try: await coro
            except PrincipalNotFoundError: nf += 1
            except Exception: pass
        check("P6 unknown-email mint/revoke/list raise NotFound", nf == 3, f"{nf}/3")
    finally:
        await ps.close(); await ks.close(); await drop_database(env); await conn.close()

async def main():
    await probe_131_and_107(); await probe_verify(); await probe_cascade_and_unique()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    for n, ok, d in RESULTS:
        if not ok: print(f"  FAILED: {n} — {d}")
    print(f"{passed}/{len(RESULTS)} checks passed"); return 0 if passed == len(RESULTS) else 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```
_(Full run output: `29/29 checks passed`. Note: the pasted form is the de-verbosed twin of `/tmp/audit49_probe.py`
used in the run; the run's per-check detail strings are quoted inline under each REFUTE section above.)_
