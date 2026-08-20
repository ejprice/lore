# REPORT — adversary-49-1 (packet 49 CONTRACT ADVERSARY)

`brief-base v14 read` · `brief project v7 read`

**CAPABILITY CHECK (first, per brief-base §4):** brief demands = read the 4 packet-49
test files + design + spec + store-ref, lore tools, comms/task ledgers, build wrong AND
correct implementations in a scratch copy (`scratch_copy.sh`), run scoped pytest against
spike-surreal `:18000`, produce a findings list. All satisfiable and exercised — no gap.
**Model:** the brief asserts `claude-opus-4-8`; I cannot self-read my model, but the session
env corroborates (`CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8`). Proceeded on that basis.
Role spec `~/.claude/agents/contract-adversary.md` READ and EXECUTED (P0/P1/P1b/P1c/P2/P6b).
**I do not spawn subagents; did the work directly.**

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 headline:** 18/19 wrong builds CAUGHT. **1 wrong build WAVED THROUGH** (FINDING 4:
  `list-keys` renders the key NAME verbatim — no `TestRenderSafety` fixture exercises
  `list-keys`, so a forged phantom key row / ANSI-bidi terminal injection ships green).
- **Satisfiability (C-DEF):** my correct reference build canNOT reach 0-failed against the
  contract AS WRITTEN — **4 pins are RED on a correct build** = **3 blocking CONTRACT
  DEFECTS** (FINDINGS 1–3). Only after correcting those 3 does the reference go **107
  passed / 0 failed**.
- **FINDING 1 (C-DEF BLOCKER):** `TestPerPrincipalIdentity206` + `TestUniformDenyNoOracle`
  reuse an IDENTICAL `(name, secret)` across two principals → identical wire → identical
  `sha512` → `UNIQUE(hash)` collision at mint. Both pins RED on a correct build; the builder
  cannot make #206 (THE defect the packet exists to avoid) green without dropping
  `UNIQUE(hash)` (fails pin 10). Trapped.
- **FINDING 2 (C-DEF BLOCKER + zero-reach guard):** pin 14's regex `record<principal>\b`
  never matches `record<principal>;` (a `\b` after `>` is impossible before `;`), so
  `found == set()` ALWAYS → pin permanently RED on a correct build AND can never detect a
  new link (its whole purpose). Reach = zero.
- **FINDING 3 (C-DEF BLOCKER):** `test_add`'s "empty before" assertion reads a table that
  does not exist yet; SurrealDB 3.2.4 RAISES `NotFoundError` on `SELECT email FROM principal`
  on a virgin DB → the assertion errors before `main` is ever called, on ANY build.
- **FINDING 4 (MISSING PIN):** no hostile fixture for the `list-keys` key-name render
  (design §F8 / pin 19 require the key `name` laundered). Verbatim AND private-clone builds
  ship green. Positive control pasted below.
- **FINDING 5 (CONTRACT/HARNESS DEFECT):** the 8 CLI e2e pins call `main()` synchronously
  from `async def` tests, but design §F6 mandates the `index/cli.py` idiom (`asyncio.run`
  in `main`) — which raises `RuntimeError: asyncio.run() cannot be called from a running
  event loop`. A faithful builder's `main` fails all 8 pins on an INFRASTRUCTURE error, not
  a behavioural one.
- **Quantifier table (P1b):** the 4 verify-deny conditions are each ∀ (independent fixture;
  dropping each reddens ONLY its own pin). See §P1b.
- **Reach table (P1c):** FINDING 2 is a zero-reach guard; pin 17c is existence-only (R2);
  pin 19 AST scan passes on ANY single sanitise call (R3). See §P1c.
- **Residuals:** R1 pin-2 store-level leak probe is architecturally vacuous · R2 pin-17c
  proves `_query` EXISTS, not that it is USED/rides `run_query` · R3 pin-19 AST scan reach ·
  R4 no timing-oracle pin (acceptable, structural).
- **Graded: c45e9a7 · HEAD-at-report: c45e9a7 · SAME (0 behind).**
- **Packages considered:** `secrets.token_urlsafe` keep · `hashlib`→`loremaster.index.records.sha512_hex` replace (reused in ref) · `argparse` keep · `cachetools`/TTL rejected by R12 (my WB3 proves the contract catches a cache) · `concurrent.futures` (stdlib, reference-only, surfaces FINDING 5). My table DIFFED vs the author's: no discrepancy — no library-replaceable mechanism marked bespoke.
- **Reuse ledger:** none — I authored no shipped symbols (adversary produces a findings list; the reference build lives only in `/tmp/adv49-scratch`, disposable, and its key excerpts are pasted below).
- **pointers:** wrong-build instrument pasted §APPENDIX-A · list-keys control test pasted §APPENDIX-B · reference-build key excerpts §APPENDIX-C · scratch provenance line §PROVENANCE.

## The ONE message to lead

`STATE: done · REPORT: REPORT-adversary-49-1.md · CONTRACT INSUFFICIENT — 3 C-DEF blockers (UNIQUE(hash) fixture collision · record<principal>\b zero-reach regex · empty-DB SELECT raises), 1 missing pin (list-keys key-name render), 1 harness defect (sync main() in async tests vs asyncio.run idiom)`

---

## PROVENANCE (brief-base §6 / #140 — prove which tree)

All wrong/correct builds ran in a `scratch_copy.sh`-minted copy, provenance asserted:

```
scratch copy READY: /tmp/adv49-scratch   (scratch_copy.sh, exit 0)
loremaster.__file__ = /tmp/adv49-scratch/loremaster/loremaster/__init__.py
```

Live store: spike-surreal `ws://127.0.0.1:18000` (systemd `active`; NEVER `:18500`). Scoped
STRICTLY to the four packet-49 files — the branch's ~446 pre-existing packet-39 RED is out
of scope and never conflated.

---

## SATISFIABILITY RECEIPT (C-DEF class — the required leg)

I built the CORRECT reference implementation (I had to, to grade the contract): the
`principal_key` schema slice + fold, `PrincipalKeyStore` (`ensure_ready`/`mint`/`list_for`/
`revoke`/`verify`/`_query` + connection idiom), `PrincipalStore.set_expires`/`delete`, and
the CLI (`build_parser` 9 verbs + `main` + `build_principal_store`/`build_principal_key_store`).
Key excerpts are pasted in §APPENDIX-C (the reference is the satisfiability instrument).

**Against the contract AS WRITTEN, the reference is 4-failed / 103-passed** — all 4 failures
are CONTRACT DEFECTS, not reference bugs (each fixed by editing the FIXTURE/regex, never the
code):

```
FAILED test_principal_keys_schema.py::TestTheCascadeForwardScopeIsPinned::test_principal_key_is_the_ONLY_record_principal_link   (FINDING 2)
FAILED test_principal_keys_store.py::TestPerPrincipalIdentity206::test_distinct_principals_and_one_principal_two_keys            (FINDING 1)
FAILED test_principal_keys_store.py::TestUniformDenyNoOracle::test_every_denial_mode_returns_the_same_None                       (FINDING 1)
FAILED test_principals_cli.py::TestVerbsExecuteDirectly::test_add_creates_a_principal_on_invocation                             (FINDING 3)
4 failed, 103 passed in 6.26s
```

**After applying the 3 minimal contract corrections (FINDINGS 1–3), the reference is
0-failed** — proving the reference is correct and the 4 failures were the contract's:

```
107 passed in 6.41s
```

The 3 corrections (positive control that the fix is in the CONTRACT, not the code):
1. FINDING 1 — `TestPerPrincipalIdentity206.b_key1` and `TestUniformDenyNoOracle.suspended`
   use a DISTINCT secret (so their wire string ≠ another key's).
2. FINDING 2 — drop the trailing `\b` in `_RECORD_PRINCIPAL`.
3. FINDING 3 — `_principal_emails` returns `set()` when the table does not exist yet.

---

## FINDINGS (missing / broken pins — each with a reproduction)

### FINDING 1 — C-DEF BLOCKER: two pins collide on `UNIQUE(hash)` (unsatisfiable)

**The test that is broken:** `test_principal_keys_store.py::TestPerPrincipalIdentity206::test_distinct_principals_and_one_principal_two_keys` and `::TestUniformDenyNoOracle::test_every_denial_mode_returns_the_same_None`.

**The defect:** `_hash_for(name, secret) = sha512_hex(f"{name}:{secret}")` (design §F4). The
#206 fixture mints `a_key1 = (A, "laptop", _SECRET)` **and** `b_key1 = (B, "laptop", _SECRET)`
— identical wire `"laptop:<_SECRET>"` → identical `sha512` → the second mint violates
`UNIQUE(hash)` (pin 10, design §F7, REQUIRED). Same in uniform-deny: `revoked = (A, laptop,
_SECRET)` and `suspended = (B, laptop, _SECRET)` collide. A correct build (which MUST have
`UNIQUE(hash)`) raises at fixture setup:

```
surrealdb.errors.InternalError: Database index `principal_key_hash` already contains
'cfafd611...274c1', with record `principal_key:barod3j1jckkajq2n3lf`
```

**Why it matters:** #206 is *the exact defect the packet exists to avoid*, and its pin
canNOT be made green on a correct build. The builder is trapped between #206 (needs the two
keys to mint) and pin 10 (rejects the duplicate hash). This must be caught BEFORE a builder
starts — it is precisely the C-DEF the satisfiability receipt exists for.

**The fix:** give the second principal's key a DISTINCT secret (the #206 property needs two
principals each with A key, never identical credentials). Proven: with `b_key1`/`suspended`
on distinct secrets, both pins pass on the reference build (part of the 107-passed run).

### FINDING 2 — C-DEF BLOCKER + zero-reach guard: pin 14's regex never matches

**The test:** `test_principal_keys_schema.py::TestTheCascadeForwardScopeIsPinned::test_principal_key_is_the_ONLY_record_principal_link` (pin 14, the cascade-forward-scope PIN THE MISS).

**The defect:** `_RECORD_PRINCIPAL = re.compile(r"...TYPE\s+record<principal>\b", re.I)`. In
the emitted DDL the field is `...TYPE record<principal>;` — `>` (a non-word char) is followed
by `;` (a non-word char), so the trailing `\b` (which requires a word/non-word transition)
can NEVER match. Empirical probe against the reference DDL:

```
FIELD LINE: 'DEFINE FIELD OVERWRITE principal ON principal_key TYPE record<principal>'
regex matches in full DDL: []          # <-- ZERO matches
substring 'record<principal>' count: 1
context: 'record<principal>;\nDEFINE FIEL'
```

So `found == set()` ALWAYS → `found == expected` (expected `{('principal','principal_key')}`)
fails on any correct build.

**Two harms:** (a) C-DEF — permanently RED on a correct build; (b) **zero-reach guard** —
the pin's PURPOSE is to redden when a NEW `record<principal>` link is added (packet 3A's
`memory.owner`). With a regex that matches nothing, adding a link leaves `found` still `set()`
→ the guard can NEVER fire for its intended trigger. "A scan that reaches zero sites is
broken, not clean" (P1c).

**The fix:** drop the trailing `\b` (or use `record<principal>(?![\w<])`). Proven: with `\b`
dropped, the pin matches `{('principal','principal_key')}` and passes on the reference
(part of the 107-passed run).

### FINDING 3 — C-DEF BLOCKER: `test_add` reads a not-yet-created table

**The test:** `test_principals_cli.py::TestVerbsExecuteDirectly::test_add_creates_a_principal_on_invocation`, line `assert await _principal_emails(cli_env.env) == set()  # empty before`.

**The defect:** `_principal_emails` runs `SELECT email FROM principal` on a fresh unique DB —
BEFORE `main` (which creates the table) is ever called. The `cli_env` fixture never applies
schema first. SurrealDB 3.2.4 RAISES on a SELECT from a non-existent table (direct probe
against the live store):

```
SELECT on fresh DB RAISED: NotFoundError The table 'principal' does not exist
```

So the assertion errors before `main`, on ANY build. (Only `test_add` hits it — the other
CLI e2e tests call `main("add")` first, which creates the table.)

**The fix:** make `_principal_emails` tolerant of a missing table (return `set()`), OR have
`cli_env` pre-create the schema, OR drop the pre-`main` assertion. Proven: with the tolerant
helper the pin passes on the reference (part of the 107-passed run).

### FINDING 4 — MISSING PIN: no hostile fixture for the `list-keys` key-name render

**The wrong build that PASSES the whole contract:** `list-keys` renders `key.name` VERBATIM
(no sanitiser) — or through a PRIVATE clone. Every `TestRenderSafety` pin (behavioural
hostile, AST source-scan, mutation-proof) exercises `list` / `display_name` ONLY; none render
`list-keys`. Design §F8 and pin 19 EXPLICITLY name the key `name` as a field that must be
laundered ("principal email/display_name, key name"). Wrong-build result:

```
[>>> WAVED THROUGH (MISSING PIN) <<<] WB10c list-keys key-name verbatim (pin19 reach)
      3 passed in 0.84s        # all TestRenderSafety pins green with the key name verbatim
```

**Positive control (§APPENDIX-B), reference vs verbatim:**

```
CONTROL on REFERENCE (sanitised):  1 passed          # forged row neutralised
CONTROL on WB10c (verbatim):       1 failed
  assert 'phantom-key   revoked-but-shown-active' not in
    ['laptop', 'phantom-key   revoked-but-shown-active', '``` `\tactive']   # forged row shipped
```

**The pin the author must add:** a `list-keys` hostile-key-name fixture (behavioural forged
row + mutation-proof of the shared seam), mirroring `TestRenderSafety` but for `list-keys`.
Paste §APPENDIX-B verbatim as the starting point. Related reach gap (R3): pin 19's AST
source-scan `test_the_render_path_routes_through_the_shared_sanitiser_seam` passes on ANY
single `sanitise_line`/`safe_str` call in the file — so a build sanitising `list-keys` but
not `list` (or vice versa) passes the AST scan; only the per-render mutation-proof
discriminates, and it only covers `list`.

### FINDING 5 — CONTRACT/HARNESS DEFECT: sync `main()` in async tests vs the mandated idiom

**The tests:** all 8 `TestVerbsExecuteDirectly` / `TestRenderSafety` / `TestCredsFree` CLI
e2e pins are `async def` and call `p_module.main(...)` SYNCHRONOUSLY.

**The defect:** design §F6 mandates *"House idiom to copy: `index/cli.py` — `main(argv) ->
int`"*, and `index/cli.py::main` / `comms_cli.py::main` both do `return asyncio.run(...)`. A
builder faithfully cloning that idiom produces a `main` that, called from inside the tests'
running event loop, raises:

```
RuntimeError: asyncio.run() cannot be called from a running event loop
FAILED tests/test_principals_cli.py::TestVerbsExecuteDirectly::test_suspend_sets_status_on_invocation
```

(measured — I mutated the reference `main` to the plain `asyncio.run` house idiom and ran a
CLI e2e pin.) All 8 CLI e2e pins fail on an INFRASTRUCTURE error, not a behavioural one. To
pass, `main` must be loop-aware (thread-offload) — which is NOT the idiom §F6 tells the
builder to copy, and which a builder is unlikely to discover from a `RuntimeError`.

**The fix:** either (a) the CLI e2e pins invoke `main` off-loop — `await
asyncio.to_thread(p_module.main, cli_env.argv(...))` — so the mandated `asyncio.run` idiom
works; or (b) the contract explicitly pins, and the design explicitly requires, a loop-aware
`main`, so the builder is told. As written, the contract silently contradicts its own
design's idiom instruction.

---

## P1b — QUANTIFIER TABLE (the 4 verify-deny conditions + the served invariants)

Each of the four deny conditions is ∀-over-inputs (an INDEPENDENT fixture forces exactly that
condition; dropping the condition reddens ONLY its own pin) — verified empirically by
dropping each check in the reference and running its isolated pin:

| invariant | ∀ or guarded | receipt (drop the check → its own pin reddens) |
|---|---|---|
| key.revoked_at IS NONE | ∀ | WB2a → `test_revoked_key_is_denied_on_the_next_verify` FAILED |
| key.expires_at check | ∀ | WB2b → `test_expired_key_is_denied_principal_fine` FAILED |
| principal.status == active | ∀ | WB2c → `test_suspended_principal_denies_a_live_key` FAILED |
| principal.expires_at check | ∀ | WB2d → `test_expired_principal_denies_a_live_key` FAILED |
| revocation beats cache (R12) | ∀ | WB3 (in-memory cache) → `test_revoked_key_is_denied_on_the_next_verify` FAILED |
| per-principal identity (#206) | ∀ (≥2 principals, 1 w/ 2 keys) | WB1 (constant identity) → `TestPerPrincipalIdentity206` FAILED **(once FINDING 1 fixed)** |
| uniform deny / no oracle | guarded (5 enumerated modes) | WB4a (reason-raise) → `test_every_denial_mode...` FAILED **(once FINDING 1 fixed)** |
| raw secret never logged | ∀ | WB4b (log secret) → `test_the_raw_secret_never_appears_in_a_log_record` FAILED |
| hash the WHOLE `name:secret` | ∀ | WBx2 (hash only secret) → happy-path + `test_verify_hashes_the_WHOLE_wire_string` FAILED |
| set-expiry clears via explicit SET NONE | ∀ | WBx1 (clear-by-omission) → `test_set_expires_clears_to_none_via_explicit_SET` FAILED |

The all-clear positive control (`test_all_clear_key_is_allowed_the_positive_control`) makes
the deny pins non-vacuous. **No vacuous-∀ hole found among the deny conditions.** The only
∀ concern is the uniform-deny "no oracle" invariant, which is a hand-enumeration of 5 denial
modes (adequate for the modes named; a 6th mode would need its own fixture).

## P1c — REACH TABLE (every guard/scan the contract introduces or relies on)

| guard / scan | reach DERIVED vs hand-list | coverage a checked var? | effect vs proxy | one-source (mutation-proven)? | verdict |
|---|---|---|---|---|---|
| pin 14 `_RECORD_PRINCIPAL` regex over `generate_ddl` | derived (full DDL) BUT regex matches **zero** sites | no — always `set()`, cannot grow | effect | n/a | **BROKEN — FINDING 2 (zero reach)** |
| `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters` | mutation of `_define_field` | yes (mutation) | effect | yes | SAFE (only mutates `_define_field`, not `_define_table`/`_unique_index` — clause pins backstop those) |
| `test_source_contains_no_execute_flag_or_dry_run` (AST) | `principals.py` (single file) | yes over the file | effect (string presence) | one source | SAFE (CLI is single-module) |
| `test_no_verb_accepts_an_execute_flag` / `test_every_verb_is_recognised` | `_ALL_VERBS` hand-list (9) | partial — a verb absent from BOTH parser and `_ALL_VERBS` is unchecked | effect | n/a | ACCEPTABLE (design fixes 9 verbs; source-scan backstops `--execute`) |
| `test_main_guard_is_the_last_top_level_statement` (AST) | `principals.py` | yes | effect | n/a | SAFE (per-file, design-correct) |
| `test_the_cli_module_routes_through_both_factories` (AST) | 2 factory names in `principals.py` | checks call EXISTS, not that `main` uses it (dead call passes) | proxy-ish | n/a | ACCEPTABLE (behavioural e2e proves wiring) |
| `test_the_cli_does_not_call_load_config` (AST) | `principals.py` | yes | effect | n/a | SAFE (behavioural creds-free pin backstops) |
| pin 17c `_query` seam existence | `PrincipalKeyStore._query` exists + is coroutine | **no** — does NOT prove `_query` is USED or rides `run_query` | proxy (existence, not routing) | delegated to out-of-scope `test_retry_seam.py` | **R2 — existence-only** |
| pin 19 AST `test_the_render_path_routes_through_the_shared_sanitiser_seam` | ANY `sanitise_line`/`safe_str` call in the file | **no** — one call anywhere passes | proxy | mutation-proof covers `list` only | **R3 — reach gap (feeds FINDING 4)** |

Legs run: FINDING 2 empirical (regex probe + reference run); pin-17c and pin-19-AST by
construction-inspection + the FINDING-4 wrong-build; all others by the wrong-build battery.

## P2 — FIXTURE DISCRIMINATION

- **#206 fixture (2 principals, 1 with 2 keys) DISCRIMINATES:** WB1 (constant identity) is
  CAUGHT — a monoculture (1 principal / 1 key) would NOT catch it, so the multi-principal
  shape is load-bearing and correctly chosen. (The fixture is nonetheless BROKEN by FINDING 1;
  discrimination is proven once the secret collision is fixed.)
- **Deny-condition fixtures DISCRIMINATE:** each of WB2a–d reddens ONLY its own pin (§P1b) —
  no single fixture satisfies the ∀ vacuously; the all-clear control proves a deny is
  attributable to its condition.
- **`test_set_expires_clears_to_none_via_explicit_SET` DISCRIMINATES:** WBx1 (clear-by-omission)
  CAUGHT.
- **Pin 2 leak-probe is architecturally VACUOUS at the store level (R1):** `mint()` receives
  only `secret_hash` — the store NEVER holds the raw secret, so the negative ("raw absent")
  cannot be falsified by any store-level build. Its value is the positive control + SCHEMAFULL
  (which rejects an undeclared `secret` column). A CLI-path leak (mint-key passing the raw as
  the hash) is caught INDIRECTLY by `test_mint_key_prints_the_secret_exactly_once_and_it_verifies`
  (verify would fail), but no in-scope pin reads the stored row after a CLI `mint-key` to
  confirm the hash (not raw) was stored. Suggest a CLI-path row-inspection leak probe.

## P6b — DELETED/REPLACED CODE

**N/A — the packet is purely ADDITIVE.** Independent enumeration of the diff: a new module
(`principal_keys.py`), new methods (`PrincipalStore.set_expires`/`delete`), a new table
(`principal_key` + emitters), a new CLI. The stubs being replaced have NO behaviour (each
`raise NotImplementedError`); there are no orphaned virtues of deleted code to preserve. No
corpse-sweep hit (P6). Confirmed against `docs/design/2026-08-20-packet49-cli-keys.md`
(additive scope) and the stub files at `c45e9a7`.

## P4 — AUTHOR-CLAIM CHECK

The contract author's `REPORT-contract-49-1.md` §Graded reads *"none (I authored)"* and it
did NOT run a reference/satisfiability build. The design's PIN CHECKLIST §Satisfiability
delegates that to the adversary — which is exactly where FINDINGS 1–3 (and the pins-red-on-
correct-build class) live and were caught. The author's PIN COVERAGE table's *intended*
mutations reproduce (WB1/WB2/WB4/WB6/WB7/WB8/WB9/WB10 all caught as the table predicts); the
gaps are the fixtures/regex/harness the table does not model.

---

## APPENDIX-A — the P1 wrong-build instrument (verbatim; run at `/tmp/adv49_wb.py`)

Applies each mutation to a `.ref`-backed reference build, runs the target pin(s) against the
(corrected) contract, and reports CAUGHT vs WAVED-THROUGH. Full battery result:

```
[CAUGHT] WB1 constant-identity (#206, pin6)
[CAUGHT] WB2a drop revoked-check (pin1)        [CAUGHT] WB2b drop key-expires-check (pin5a)
[CAUGHT] WB2c drop principal-status-check (pin4) [CAUGHT] WB2d drop principal-expires-check (pin5b)
[CAUGHT] WB3 in-memory cache (pin1 R12)         [CAUGHT] WB4a reason-raise on revoked (pin8)
[CAUGHT] WB4b log raw secret (pin8)             [CAUGHT] WB6 not folded into generate_ddl (pin12)
[CAUGHT] WB7a delete drops child cascade (pin13) [CAUGHT] WB7b delete via two _query, not one txn (pin13)
[CAUGHT] WB8a private blank check, not is_blank (pin17a)
[CAUGHT] WB8b private principal mapper, not _row_to_principal (pin17b)
[CAUGHT] WB9 CLI uses load_config (creds pin)   [CAUGHT] WB10a list renders verbatim (pin19)
[CAUGHT] WB10b private sanitiser clone in list (pin19)  # caught by mutation-proof
[>>> WAVED THROUGH (MISSING PIN) <<<] WB10c list-keys key-name verbatim (pin19 reach)
plus: [CAUGHT] WBx1 set_expires clear-by-omission ; [CAUGHT] WBx2 verify hashes only the secret
```

Each mutation is an exact-string patch (see the script). Representative examples — WB1
(constant identity, verify): replace the principal resolution with
`Principal(id="principal:CONST", email="collapsed@example.com", status="active", role="member", ...)`.
WB2a–d: delete the corresponding `if ...: return None` deny block. WB3: memoise the verify
result in a per-instance dict keyed by the presented credential. WB7b: replace the single
`execute_transaction("BEGIN; DELETE child; DELETE parent; COMMIT")` with two separate
`self._query("DELETE ...")` calls. WB10c: `print(f"{sanitise_line(key.name)}\t{flag}")` →
`print(f"{key.name}\t{flag}")`.

## APPENDIX-B — the FINDING-4 pin the author must add (verbatim positive control)

```python
"""adversary-49-1 POSITIVE CONTROL for FINDING 4 (the missing list-keys hostile pin)."""
_FORGED_KEY_ROW = "phantom-key   revoked-but-shown-active"
_HOSTILE_KEY_NAME = f"laptop\n{_FORGED_KEY_ROW}\n``` `"

async def test_hostile_key_name_does_not_forge_a_row_in_list_keys(cli_env, capsys):
    p_module.main(cli_env.argv("add", "--email", _EMAIL))
    p_module.main(cli_env.argv("mint-key", "--email", _EMAIL, "--name", _HOSTILE_KEY_NAME))
    capsys.readouterr()  # drain the mint secret line
    rc = p_module.main(cli_env.argv("list-keys", "--email", _EMAIL))
    assert rc == 0
    output_lines = [ln.strip() for ln in capsys.readouterr().out.splitlines()]
    assert _FORGED_KEY_ROW not in output_lines, (
        "the hostile key NAME's survived newline forged a standalone phantom key row in "
        "`list-keys` output — the key name must route through the shared sanitiser seam"
    )
```
Behaviour: RED on a `list-keys`-verbatim build, GREEN on the reference (sanitised). Add a
mutation-proof twin (patch `loremaster.sanitise.sanitise_line`; require the marker in
`list-keys` output) to also catch a private clone.

## APPENDIX-C — reference-build key excerpts (the satisfiability instrument)

`principal_key` schema slice folded into `generate_ddl` immediately after
`_principal_statements()`:

```python
_PRINCIPAL_KEY_FIELD_SPECS = (
    ("hash", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("name", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("principal", f"record<{PRINCIPAL_TABLE}>", ""),
    ("created_at", "datetime", "DEFAULT time::now()"),
    ("expires_at", "option<datetime>", ""),
    ("revoked_at", "option<datetime>", ""),
)
def _principal_key_statements():
    s = [_define_table(PRINCIPAL_KEY_TABLE)]
    s += [_define_field(PRINCIPAL_KEY_TABLE, n, t, constraint=c) for n, t, c in _PRINCIPAL_KEY_FIELD_SPECS]
    s.append(_unique_index(PRINCIPAL_KEY_TABLE, f"{PRINCIPAL_KEY_TABLE}_hash", ("hash",)))
    s.append(_unique_index(PRINCIPAL_KEY_TABLE, f"{PRINCIPAL_KEY_TABLE}_principal_name", ("principal", "name")))
    return s
# in generate_ddl: statements += _principal_statements(); statements += _principal_key_statements()
```

`PrincipalKeyStore.verify` (the four re-checks; routes blank through the shared `is_blank`,
maps the principal through `PrincipalStore.get_by_email` → `_row_to_principal`; no cache):

```python
async def verify(self, presented):
    if is_blank(presented): return None
    if ":" not in presented: return None
    name, secret = presented.split(":", 1)
    if is_blank(name) or is_blank(secret): return None
    digest = sha512_hex(presented)
    key_rows = self._as_rows(await self._query(
        f"SELECT name, revoked_at, expires_at, principal.email AS p_email "
        f"FROM {PRINCIPAL_KEY_TABLE} WHERE hash = $h", {"h": digest}))
    if not key_rows: return None
    key_row = key_rows[0]; now = datetime.now(UTC)
    if PrincipalStore._to_aware_utc(key_row.get("revoked_at")) is not None: return None
    ke = PrincipalStore._to_aware_utc(key_row.get("expires_at"))
    if ke is not None and ke <= now: return None
    principal = await self._principals.get_by_email(str(key_row["p_email"]))
    if principal is None: return None
    if principal.status != "active": return None
    if principal.expires_at is not None and principal.expires_at <= now: return None
    return KeyVerification(principal=principal, key_name=str(key_row["name"]))
```

`PrincipalStore.delete` (children-first cascade in ONE `execute_transaction`, returns N):

```python
async def delete(self, *, email):
    principal = await self.get_by_email(email)
    if principal is None: raise PrincipalNotFoundError(...)
    rid = principal.id.split(":", 1)[1]
    count = self._as_rows(await self._query(
        f"SELECT count() FROM {PRINCIPAL_KEY_TABLE} WHERE principal = type::record('{PRINCIPAL_TABLE}', $pid) GROUP ALL", {"pid": rid}))
    removed = int(count[0].get("count", 0)) if count else 0
    await execute_transaction("BEGIN;\n"
        f"DELETE {PRINCIPAL_KEY_TABLE} WHERE principal = type::record('{PRINCIPAL_TABLE}', $pid);\n"
        f"DELETE {PRINCIPAL_TABLE} WHERE {_COL_EMAIL} = $email;\nCOMMIT;\n",
        {"pid": rid, "email": email}, acquire=self._ensure_connection, drop=self._drop_connection, url=self._url)
    return removed
```

CLI `_dispatch` readies BOTH stores (delete's cascade + `_db_snapshot` read `principal_key`),
`list`/`list-keys` route free text through `sanitise_line`/`safe_str`, `mint-key` prints
`<name>:<secret>` once; `main` is LOOP-AWARE (thread-offload — the FINDING-5 workaround the
mandated `asyncio.run` idiom needs to survive being called from the async tests); config is
loaded via `LoreConfig.model_validate` (never `load_config`, creds-free).

---

## VERDICT

**CONTRACT INSUFFICIENT.** Concrete pins the author must fix, in priority order:

1. **FINDING 1** — de-collide the #206 + uniform-deny fixtures (distinct secrets). *Blocker:
   the packet's headline pin is unsatisfiable on a correct build.*
2. **FINDING 2** — drop the `\b` in `_RECORD_PRINCIPAL`. *Blocker + the PIN THE MISS guard
   is non-functional (zero reach).*
3. **FINDING 3** — make `_principal_emails` tolerate a missing table (or pre-create schema in
   `cli_env`). *Blocker: `test_add` errors before `main` on any build.*
4. **FINDING 5** — invoke `main` off-loop in the CLI e2e pins (`asyncio.to_thread`) OR pin a
   loop-aware `main`. *The design-mandated `asyncio.run` idiom fails all 8 CLI e2e pins.*
5. **FINDING 4** — add a `list-keys` hostile-key-name pin (§APPENDIX-B) + a mutation-proof
   twin. *A real terminal-forgery vector ships green.*
6. Residuals to consider: R1 (CLI-path leak probe), R2 (in-scope proof that `_query` is USED),
   R3 (pin-19 AST scan reach — subsumed by FINDING 4's fix).

The contract is otherwise STRONG: 18/19 wrong builds caught, the four deny conditions are
each ∀-pinned with a positive control, sharing is mutation-proven for `is_blank` /
`_row_to_principal`, the DDL routes through the shared emitters by mutation, and the
`#131`/fold, cascade/one-txn, and creds-free properties all discriminate. The defects are
concentrated in three fixtures, one regex, and the async-vs-sync `main` harness — every one
findable only by BUILDING against it, which is why the satisfiability leg exists.
