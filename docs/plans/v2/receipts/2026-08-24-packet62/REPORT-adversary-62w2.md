# REPORT-adversary-62w2 — packet 62 Wave 2 CONTRACT-ADVERSARY (anti-spoofing surface)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — §1.1 (FIELD `OVERWRITE`;
  INDEX `IF NOT EXISTS` never `OVERWRITE`), §1.4 (option<> on a POPULATED table; no DEFAULT rescue),
  §1.6 (dirty-store blind spot), §1.8 (UNIQUE over option<string> = multiple-NONE + unique-non-NONE),
  §2 (explicit projection reads NONE; `SELECT *` omits it). Cited, not re-transcribed.

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: spike-surreal test store `ws://127.0.0.1:18000` (systemd,
never :18500); `scripts/scratch_copy.sh` produced a provenance-asserted scratch copy at `/tmp/adv62w2a`;
lore tools loaded via `ToolSearch "+lore"`; registered on `lore_comms` (session `packet62`, role
`contract-adversary`); pytest/ruff ran. Role spec (`contract-adversary.md`) forbids spawning subagents
— I did the work directly. No impossibilities.

**Tree provenance receipt (#140):** `loremaster.__file__` = `/tmp/adv62w2a/loremaster/loremaster/__init__.py`
(verified by `scratch_copy.sh` AND re-printed live). Every pytest run below is `cd /tmp/adv62w2a && uv
run pytest`, grading the SCRATCH tree — never the original checkout.

---

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — two concrete missing pins (both cheap to fix; the mechanism's
  security pins are otherwise strong and every wrong build I could construct was caught).
- **Graded:** `6b180f0` (the wave-2 contract commit `test(62): wave-2 capability-mechanism contract (RED)`)
  · HEAD-at-report `6b180f0` · **SAME**. (Reference build authored in scratch off this HEAD.)
- **P1 headline:** 14 distinct SECURITY wrong-builds constructed — **binding-skip, forgery, mint-once,
  no-leak×2, no-cache×2, ESC-3, DRY both sides, injection, oracle, display-owner, stamp_owner
  location + fail-open, reach orphan/ghost/receding/blank — EVERY ONE was caught by the right pin
  for the right reason, each paired with a positive control.** The non-negotiable trio all fired:
  binding, no-leak, DRY-mutation. This is a strong contract.
- **MISSING PIN 1 — C-DEF (satisfiability BROKEN):** the 3 `TestTheCapabilityHashUniqueIndex` pins are
  **mutually unsatisfiable** — a correct `_unique_index` emission (`… FIELDS capability_hash UNIQUE`)
  cannot pass `_index_statement_over`'s `$`-anchored regex, while `_is_UNIQUE` requires the `UNIQUE`
  clause. NO build greens all three. Reference build proof: 60 passed / 3 failed, the 3 being exactly
  these; a one-char regex fix (`\s*$`→`\b`) greens them. **Fix in `test_agent_capability.py`.**
- **MISSING PIN 2 — the OWNERLESS-agent capability deny is unpinned (a cross-principal quantifier
  hole):** the binding + owner-active fixtures use ONLY owned agents. An ownerless agent
  (`register(owner_principal_id=None)` — a state the contract itself sanctions via
  `test_register_without_a_credential_is_ownerless_not_fabricated`) still mints a capability; a build
  treating a NONE owner as permissive in BOTH cond 3 and cond 4 (two plausible defensive idioms)
  resolves that capability under ANY foreign principal's token — reproduced live (`30b3735f…` returned
  under bob's token) — and passes the WHOLE contract (60/3, only the C-DEF pins fail). **Fix:** add
  `test_an_ownerless_agents_capability_is_denied`.
- **Satisfiability receipt:** reference (correct) build → **60 passed / 3 failed** on the 63 collected;
  the 3 failures are exactly the C-DEF index pins. So 49/52 declared-RED green cleanly; the 3 that
  don't are the C-DEF, not a builder error.
- **RED honesty:** 52 failed / 11 passed at HEAD `6b180f0`; the declared-RED set (after the 62w2b
  rename) EQUALS the actual RED-at-HEAD set exactly (52=52, zero diff either way — derived, §P7).
- **P-PKG:** no new mechanism specified — the contract pins REUSE (`sha512_hex`, `secrets.token_urlsafe`,
  `_define_field`/`_unique_index`, `AgentRegistry._query`, extracted `parse_credential`), mirroring the
  shipped `PrincipalKeyStore` credential pattern. `keep_with_trigger` (trigger: secret ever becomes
  low-entropy → KDF). No package swap warranted; my independent table found nothing the author missed.
- **Decisions-needed:** none — both findings are contract-author fixes, not operator forks. The 3 ESC
  rulings in the design are already operator-settled; the contract implements them faithfully.

---

## MISSING PIN 1 — C-DEF: the index-existence pins are mutually unsatisfiable (BLOCKER)

`test_agent_capability.py::_index_statement_over` (the helper the three index pins depend on):

```python
and re.search(rf"FIELDS\s+{field}\s*$", statement, re.IGNORECASE)   # <-- the $ anchor
```

A correct build emits the UNIQUE index through the shared `_unique_index` emitter, which appends
` UNIQUE` AFTER the field list. Verified live in the reference build:

```
EMITTED INDEX: DEFINE INDEX IF NOT EXISTS agent_capability_hash ON agent FIELDS capability_hash UNIQUE
```

The `$` anchor requires the statement to END at the field name (modulo whitespace). ` UNIQUE` follows,
so the regex NEVER matches a UNIQUE index. Isolated regex control (positive + negative):

```
pattern = 'FIELDS\\s+capability_hash\\s*$'
correct UNIQUE index matches _index_statement_over regex? -> False   # the correct build
plain index (owner_principal) positive control          ? -> True    # a plain index ends at the field
```

Consequence — the three pins cannot co-pass on ANY build:
- `test_the_capability_hash_index_is_emitted` → `assert _index_statement_over(...) is not None` → the
  regex returns None for a UNIQUE index → **stays RED on a correct build**.
- `test_the_capability_hash_index_is_UNIQUE` → to have `statement is not None` the regex must match
  (a statement with NO `UNIQUE` after the field), but then `"UNIQUE" in statement.upper()` is False.
  **Unsatisfiable both ways** — either the first assert fails (None) or the second (no UNIQUE).
- `test_the_capability_hash_index_is_IF_NOT_EXISTS_never_OVERWRITE` → same `assert statement is not
  None` guard → RED.

**Reference-build reproduction** (`cd /tmp/adv62w2a && uv run pytest … -q`):
```
3 failed, 60 passed in 11.34s
FAILED …TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_emitted
FAILED …TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_UNIQUE
FAILED …TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_IF_NOT_EXISTS_never_OVERWRITE
```
**Fix proof (positive control that the regex is the SOLE cause):** patching only `\s*$`→`\b` in the
scratch test copy, then re-running just those three pins:
```
loremaster/tests/test_agent_capability.py::TestTheCapabilityHashUniqueIndex   3 passed in 0.64s
```
So the reference build's index is textbook-correct; the contract's own helper cannot see it. This is the
C-DEF class verbatim (a declared-RED pin that cannot go green on the intended correct build) — a builder
would burn a cycle fighting an unsatisfiable pin. **The pin to change:** `_index_statement_over`'s pattern
to `FIELDS\s+{field}\b` (or `…(\s+UNIQUE)?\s*$`). The clause pins (`_is_UNIQUE`,
`_is_IF_NOT_EXISTS_never_OVERWRITE`) then work unchanged.

## MISSING PIN 2 — the ownerless-agent capability deny (cross-principal quantifier hole)

**The invariant should be ∀ agents (owned AND ownerless): "a capability is accepted only under the
OWNER's token; an agent with NO owner is accepted under NO token."** The contract's binding pin
(`test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token`) and the owner-active
pins (`test_a_suspended…`, `test_an_expired…`) all use an **owned** agent (`owner_bare=alice_bare`) —
a parameter-value monoculture on owner-presence. The ownerless door is unguarded.

The contract ITSELF creates the dangerous state: `test_register_without_a_credential_is_ownerless_not_
fabricated` pins that `register(owner_principal_id=None)` yields an ownerless agent — and the mint fires
unconditionally on create, so that ownerless agent HAS a valid `capability_hash`. Nothing pins that its
capability is unusable.

**Reproduction (live, scratch).** Wrong build: the two most-plausible "None is permissive" idioms —
`if owner_email is not None and owner_email != subject: deny` (cond 3) and `if owner_status is not None
and owner_status != active: deny` (cond 4). Adversary probe (`test_adv_ownerless_probe.py`, pasted
below) registers an ownerless agent, mints its capability, presents it under **bob's** token:
```
ADV-PROBE ownerless cap under bob's token -> '30b3735f39b85a7d9f42cbdf0adc4883'  (None=safe, agent-id=HOLE)
```
The ownerless agent RESOLVES under a foreign principal's token — a cross-principal spoof, the exact
confused-deputy class §3.2 exists to close. And the full contract still passes:
```
3 failed, 60 passed   # the 3 are the C-DEF index pins; every binding/mechanism pin GREEN
```
Positive control (clean reference build): the same probe returns `None` — a correct build closes it via
cond 3's `owner_email is None → deny`. So this is purely a MISSING PIN: the contract does not FORCE the
deny, it relies on the builder's cond-3/cond-4 being strict-on-NONE (incidental, not pinned).

**Severity: MEDIUM.** The single-mistake build (cond-3 None-permissive only) is incidentally caught by
cond 4 (an ownerless agent's `owner_principal.status` dereferences to NONE ≠ active → deny), so the
contract is NOT trivially broken — it takes the two-idiom build to open the hole. But both idioms are
individually idiomatic defensive Python, and the state is one the contract itself sanctions. The
fix is one cheap pin.

**The pin to add** (`test_agent_capability.py::TestVerifyCapabilityAdmission`):
```python
async def test_an_ownerless_agents_capability_is_denied(self, cap_env):
    # register OWNERLESS (owner_principal_id=None) — mint still fires -> a valid capability with no owner
    result = await cap_env.registry.register("free_worker", session="s2", role="worker",
                                             owner_principal_id=None)
    cap = result.capability
    assert cap, "ownerless register still mints a capability"
    # no owner -> no binding can be satisfied -> DENY under ANY principal's token (never a wildcard)
    assert await cap_env.verify_capability?(cap, _token(_EMAIL_ALICE)) is None
    assert await cap_env.verify_capability?(cap, _token(_EMAIL_BOB)) is None
```
(with a positive control that an OWNED agent's cap under its owner resolves — already present).

---

## P1 — wrong-build attack frontier (every attack caught, with positive controls)

Each row = a production wrong build applied in `/tmp/adv62w2a`, the named pin run, then reverted. All
RED-for-the-right-reason. "PC" = positive control that stayed/went green in the same run.

| # | wrong build (production defect) | pin that FIRED | PC |
|---|---|---|---|
| 1 | **verify SKIPS the binding** (cond 3 removed — accept any principal) | `test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token` (A-under-B resolved `7a9c…`) | A-under-A green |
| 2 | **forgery / name-match** (lookup by `name`, not the hash) | `test_a_forged_capability_without_the_secret_is_denied` | real secret green |
| 3 | **mint-once violation** (re-register rotates the secret) | `test_re_register_does_not_rotate_a_live_secret` | first-register green |
| 4 | **leak** (persist raw credential onto the row via `last_note`) | `test_the_raw_secret_is_never_persisted…` + `test_a_secret_shaped_value_never_appears_in_a_rendered_agent` | — |
| 5 | **leak** (hash threaded onto the `Agent` value object) | `test_the_agent_model_has_no_capability_or_hash_or_secret_field` | — |
| 6 | **no-cache violation** (memoise the positive verdict) | `test_a_retired_agents_capability_is_denied_next_call_no_cache` + `test_a_suspended_owning_principal_denies_the_capability` | live-accept green |
| 7 | **decorative expiry** (store `capability_expires_at`, never check) | `test_a_capability_whose_optional_expiry_is_in_the_past_is_denied` | future-expiry + no-expiry green |
| 8 | **DRY (agents side)** hand-roll parse (no shared import) | `test_agents_references_the_lorerunes_parse` + `test_breaking_the_shared_parse_denies_verify_capability` | principal-keys-side pin green |
| 9 | **shared-parse mutation** (`rpartition` — last colon) | `test_a_well_formed_credential_splits_on_the_first_colon` | — |
| 10 | **injection** (interpolate the presented string, not bind) | `test_an_injection_laden_credential_is_a_bound_param_not_interpolated` (query corrupted → RED) | — |
| 11 | **oracle** (raise on malformed, not uniform None) | `test_a_malformed_credential_denies_uniformly[×6]` | — |
| 12 | **display-owner arg** (`register(owner=…)`) | `test_register_exposes_no_display_owner_argument` | — |
| 13 | **stamp_owner in lorerunes** | `test_stamp_owner_exists_in_loremaster_not_lorerunes` (leg B) | — |
| 14 | **stamp_owner fail-OPEN** (fabricate a pair on non-verify) | `test_stamp_owner_fail_closes_on_an_absent_or_garbage_credential` + `…on_a_binding_mismatch` | valid-pair green |
| 15 | **reach orphan** (governed tool absent from adjudication) | `test_every_governed_tool_is_pending_owner_stamp_and_adjudicated` | non-empty + synthetic green |
| 16 | **reach ghost / RECEDING** (governed tool reclassified shared-read, entry lingers) | `test_every_governed_tool_is_pending_owner_stamp_and_adjudicated` | — |
| 17 | **reach blank trigger** | `test_every_governed_tool_is_pending_owner_stamp_and_adjudicated` (blank leg) | — |
| 18 | **§1.4 required-not-`option<>`** (`capability_hash: string`) | `test_the_capability_hash_field_is_option_string` + both dirty-store migration guards | — |

The non-negotiable trio (brief): **binding (row 1), no-leak (rows 4/5), DRY-mutation (row 8) — all
fired.** No wrong build I could construct passed the mechanism pins (the ownerless build of MISSING
PIN 2 is the sole exception, and it is a coverage gap, not a caught-then-passed mechanism).

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-failure-mode)

| invariant | classification | receipt |
|---|---|---|
| capability_hash DDL (option<>/OVERWRITE/UNIQUE-IF-NOT-EXISTS) | ∀ structural | rows 5–7… (offline pins); §1.4 discriminated (row 18) |
| capability_expires_at DDL | ∀ structural | offline pin green on ref |
| dirty-store migration (legacy survives + no write-poison) | ∀ over old/new slice | discriminated by required-not-option (row 18) |
| mint returns raw ONCE / stored = sha512(whole) | ∀ (create) | rows 3/4; sha512-of-whole pin green on ref |
| mint-once-on-create | ∀ (create vs re-register both fated) | row 3 |
| no-leak (row / Agent render / static model) | ∀ over rendered surfaces | rows 4,5 (three surfaces) |
| **binding: accept only under owner's token** | **GUARDED — owned agents only** | **MISSING PIN 2: ownerless door unguarded (reproduced)** |
| owner active + unexpired (cond 4) | GUARDED — owned agents only | same monoculture as binding (an ownerless agent's owner_status is the incidental backstop) |
| no-cache revocation (retire / suspend / expire) | ∀ over live-row re-check | row 6 (retire+suspend), row 7 (expire) |
| uniform-deny / no-oracle (malformed) | ∀ over 6 malformed shapes | row 11 |
| injection = bound param | ∀ over hostile string | row 10 |
| stamp_owner fail-closed | ∀ over absent/garbage/binding-mismatch | row 14 |
| parse_credential = ONE implementation | ∀ both consumers (identity + per-consumer mutation) | row 8 (+ principal-keys side proven independently) |
| reach: every governed tool routed-OR-adjudicated | ∀ over derived governed set | rows 15–17 |

One guarded row carries a surviving wrong build (MISSING PIN 2). Every other guarded row's failure mode
was killed by a pin (receipts above).

## P1c — REACH TABLE (the anti-injection reach pin, Fork 4 / R4.1)

Single instrument: `TestTheGovernedSurfaceReachPin` over `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` vs
`partition_tools_by_population`.

| axis | verdict | evidence |
|---|---|---|
| reach SET | the governed tools = live registry ∖ `_SHARED_READ_CORPUS_TOOLS` | derived each run via `_build_tools`→`partition_tools_by_population` |
| DERIVED vs hand-list | **DERIVED** (fail-closed default-governed); the adjudication dict is CHECKED against the derived set, never trusted blind | `governed == frozenset(adjudication)` |
| coverage a CHECKED variable | **YES** — reds when the derived set grows (orphan) OR the dict has a stale entry (ghost/receding) OR a blank trigger | rows 15/16/17 reproduced (orphan `lore_findings`; receding ghost; blank trigger) |
| effect vs proxy | observes the EFFECT (the derived governed set), not a proxy | pin re-derives from the live registry; `test_a_synthetic_new_governed_tool_would_red_the_coverage` proves a growing set reds it |
| anti-vacuity | `test_the_governed_set_is_non_empty` (green guard) fails-closed on empty | ran green on ref |
| ONE source / mutation | the derived set is the single source of truth; the dict is validated against it | — |

**This reach pin is SOUND** — a genuine "coverage as a checked variable," not a hidden constant. Legs
were EMPIRICAL (I mutated the adjudication set in-tree: orphan, ghost, receding, blank — each reddened
the pin). Forward note (NOT a 62 finding): the pin measures adjudication-completeness, not actual
routing; when 63/64 route a tool they must DELETE its entry AND add an independent per-tool routing pin
(the design already requires this) — a tool that is routed-but-still-adjudicated would not be flagged by
this pin alone. Correct for 62's "all pending" state.

## P2 — fixture discrimination (interrogated + PERTURBED)

Every load-bearing fixture discriminates a plausible wrong build (proven by the P1 wrong builds, not by
inspection):
- **binding — TWO principals A≠B:** discriminates (row 1). ⚠ but MONOCULTURE on owner-PRESENCE (owned
  only) → MISSING PIN 2.
- **no-leak — hostile secret-shaped value:** discriminates a persisted-raw build and a model-carried
  build across THREE surfaces (row 4/5).
- **injection — `x':secret'; DELETE agent; --`:** discriminates an interpolating build (row 10) with a
  table-survives positive control.
- **expiry — future-expiry positive control:** discriminates a decorative-expiry build (row 7); the
  no-expiry control fixes the "always-deny" false pass.
- **migration — OLD-slice→legacy-row→NEW-slice (dirty store):** discriminates required-not-option
  (row 18) — the pin no virgin-DB fixture can carry (§1.6).
- **reach — synthetic governed tool + orphan/ghost:** discriminates a hand-list masquerading as derived
  (rows 15–17).
- **DRY — reject-all monkeypatch of the CONSUMER module attr:** discriminates a private clone
  per-consumer (row 8; the agent-side hand-roll reddened only the agent-side pin, principal-keys stayed
  green — proving per-consumer isolation).

## P6 / P6b — corpses and removed-behavior

- **P6 (corpse sweep):** independently re-ran the bare-pattern grep for retired non-link prose over
  `loremaster/tests loremaster/loremaster docs/design/authorization-model*` (excluding owner_principal
  lines) → **0 hits**, and no test asserts the principal↔agent non-link. The contract author's item-6
  claim is CONFIRMED. So no green-because-it-asserts-the-corpse risk.
- **P6b (removed-behavior dual, I1–I5):** I1 (retire the non-link) is pinned by
  `test_the_module_docstring_acknowledges_the_owns_edge` (RED at HEAD); I2 (preserve the
  distinct-vocabulary law) is pinned by `test_the_distinct_vocabulary_law_is_preserved` (green guard —
  a build that nukes the standing-law block reds it). I3/I4/I5 are wave-1 / 63-64 / deploy concerns, out
  of the wave-2 mechanism (correctly). One independent check I ran that the contract does NOT need to
  add: `AccessToken.subject` is `principal.email` on BOTH the api-key AND OAuth mint paths
  (`token_verifier.py` lines 301/329 + 41/54, "the subject … name the PRINCIPAL (email)") — so the
  binding-on-email fixture (subject=email) is representative of BOTH served paths, NOT a hidden
  hosted-vs-local monoculture. Good.

## P7 — RED honesty (derived, not trusted)

At HEAD `6b180f0`, `cd <repo> && uv run pytest <the 3 files>`: **52 failed, 11 passed** (0 errors — the
`getattr`/try-import guards keep collection whole, so each pin reds at RUNTIME for its own reason, not an
import collapse). Mechanically diffed the report's declared-RED list (after the 62w2b
`exists_in_lorerunes`→`exists_in_loremaster_not_lorerunes` rename) against the actual RED-at-HEAD node
set:
```
actual RED-at-HEAD count: 52
declared-RED (62w2 report) count: 52
in ACTUAL-RED but NOT declared:  (empty)
declared but NOT actual-RED:     (empty)
```
Exact match, both directions. The declared-RED set the lead feeds to `mutation_proof.py` /
`pending_contracts.yaml` is accurate. (`test_a_synthetic_new_governed_tool_would_red_the_coverage` IS in
the 52 — RED at HEAD because `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` is absent, green once built; my
earlier by-eye count was wrong, corrected by the mechanical diff — re-derive every count, including one's
own.)

## P-PKG — package survey (independent, then diffed)

The contract specifies NO new mechanism; it PINS reuse. My independent table before reading the author's:
| mechanism the contract touches | package/source considered | READ | verdict |
|---|---|---|---|
| credential hash | `loremaster.index.records.sha512_hex` (existing) | its call sites in `principal_keys.verify`/`mint` | REUSED (never a `hashlib` clone — #102/#120) |
| secret entropy | stdlib `secrets.token_urlsafe(32)` | pkt-49 `principals._SECRET_ENTROPY_BYTES` precedent | REUSED |
| constant-time verify | `hmac.compare_digest` / `passlib` / `argon2` | `principal_keys.py` module docstring §WIRE FORMAT | `keep_with_trigger` — a UNIQUE-hash-index DB lookup over a preimage-resistant sha512 IS the constant-time check (256-bit high-entropy secret, NOT a password → a slow KDF is wrong here); trigger: the secret ever becomes low-entropy |
| DDL emit | `_define_field`/`_unique_index` (existing) | surreal_schema | REUSED |
| retry seam | `AgentRegistry._query`→`run_query` (existing) | agents.py | REUSED, mutation-pinned (row-for-#353) |
| wire parse | extracted `lorerunes.parse_credential` | principal_keys inline 519–525 | EXTRACTED + shared (mutation-pinned) |
Diff vs the author's `Packages considered: keep_with_trigger`: **identical**. No mechanism the author
marked reuse is actually a library swap I found; nothing marked `bespoke` (there is none). No P-PKG
finding.

---

## Reference (correct) build — the instrument, for reproduction

Authored in `/tmp/adv62w2a` off HEAD `6b180f0` (a scratch_copy.sh provenance-asserted copy). The edits
that take the contract to 60-pass/3-fail (the 3 = C-DEF), i.e. the satisfiability witness:
- `lorerunes/lorerunes/credential.py` — new `parse_credential(presented) -> (name, secret) | None`
  (`is_blank`→`partition(":")`→blank-half reject); re-exported in `lorerunes/__init__.py`.
- `loremaster/store/surreal_schema.py` — append `("capability_hash","option<string>","")` +
  `("capability_expires_at","option<datetime>","")` to `_AGENT_FIELD_SPECS`; `_unique_index(AGENT_TABLE,
  f"{AGENT_TABLE}_capability_hash", ("capability_hash",))` in `_agent_statements`.
- `loremaster/agents.py` — `AgentRegisterResult.capability: str|None=None`; `register`'s create branch
  mints `secrets.token_urlsafe(32)`, stores `capability_hash=sha512_hex(name:secret)`, stamps
  `owner_principal` from a new `owner_principal_id` kw, returns the raw credential once (re-register mints
  nothing); `verify_capability(presented, access_token)` mirroring `PrincipalKeyStore.verify` (one `now`,
  `parse_credential` reject, UNIQUE-hash SELECT dereferencing `owner_principal.{email,status,expires_at}`,
  four early denies + optional expiry, uniform None); imports the shared `parse_credential`.
- `loremaster/principal_keys.py` — `verify` re-routed through the shared `parse_credential`
  (`from lorerunes import is_blank, parse_credential`).
- `loremaster/owner_stamp.py` — new `stamp_owner(access_token, agent_capability, *, registry)`
  (fail-closed; routes owner_agent through `registry.verify_capability`), re-exported at
  `loremaster.stamp_owner`.
- `loremaster/server.py` — `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` (6 governed tools → triggers).
- `loremaster/principals.py` — module docstring acknowledges the `owns` edge (I1) while preserving the
  distinct-vocabulary law (I2).

The adversary probe for MISSING PIN 2 (`test_adv_ownerless_probe.py`, pasted verbatim so the claim is
re-runnable without the scratch tree):
```python
async def test_ownerless_capability_under_a_foreign_token(env):
    result = await env.registry.register("free_worker", session="s9", role="worker", owner_principal_id=None)
    cap = result.capability
    assert cap, "ownerless agent still mints a capability"
    resolved = await env.registry.verify_capability(cap, _token("bob@example.com"))
    assert resolved is None, f"CROSS-PRINCIPAL HOLE: ownerless resolved under a foreign token: {resolved!r}"
    # correct build -> None (safe); the two-idiom None-permissive build -> the ownerless agent id (HOLE).
```

Scratch tree `/tmp/adv62w2a` is disposable (scratch_copy.sh) and will be discarded; nothing committed —
this report is the durable record.

## VERDICT: CONTRACT INSUFFICIENT
Two missing pins, both contract-author fixes, neither an operator fork:
1. **C-DEF** — `_index_statement_over`'s `\s*$` regex makes the 3 UNIQUE-index pins unsatisfiable on a
   correct build; change to `\b`.
2. **Ownerless-capability deny** — add `test_an_ownerless_agents_capability_is_denied`; the binding
   invariant is ∀-over-agents but the fixtures only exercise owned agents, leaving a reproduced
   cross-principal door.
Every other security wrong build I could construct — 18 of them, including the non-negotiable binding /
no-leak / DRY-mutation trio — was caught for the right reason, each with a positive control. Fix the two
pins and this contract is strong.
