# REPORT-contract-63a-4 — §10.5 RESHAPE: `_exercise_*` resolves capability→Subject, backend takes `subject=`

- `brief-base v14 read`
- `brief project v7 read`
- store reference: `docs/reference/surrealdb-31-capabilities.md` — NOT consulted for a store/schema/DDL
  change (this is a pure TEST-SEAM reshape; it touches no store, schema, DDL, or production code).

## SUMMARY BLOCK
- Receipt: `brief-base v14 read` · `brief project v7 read`
- **State: done-with-deviations** — the §10.5 Reading-A reshape landed; all 4 gates green; RED count
  UNCHANGED at 54F/15P/11E as designed. TWO out-of-writable-set consistency FLAGS surfaced (no
  operator ruling required); no new DESIGN fork.
- Deviations:
  - Typed `_exercise_*` / `_subject_from_capability` `capability` param as `Any` (not `_Credential`)
    — the pins annotate the injected fixture value `alice_capability: str` (test bodies, outside my
    writable set); typing the seam param `_Credential` red the typecheck at 15 call sites. `Any`
    matches the old seam's `backend: Any` idiom and keeps every edit inside the granted symbol set.
    Details §TYPECHECK.
  - The `AgentRegistry` is now kept OPEN for the test's duration (old `_mint_capability` closed it
    immediately after minting) — `resolve_subject` verifies the capability against a LIVE registry.
    A behavioural lifecycle change in the capability fixtures; disclosed for the adversary. §SEAM.
- **Packages considered:** none — no production mechanism specified. The one lifecycle helper uses
  stdlib `contextlib.asynccontextmanager` to share the registry-open/close scope across the two
  capability fixtures rather than duplicating `try/finally` in each (stdlib, no dependency).
- **Reuse ledger:** 3 new test-local symbols, all dispositioned (§DRY).
- Graded: N/A — I am the contract AUTHOR revising the seam, not rendering a verdict on another
  artifact.
- **Decisions-needed:** none — §10.5 CLARIFICATION ruled the reshape's SHAPE in 5 explicit points; I
  executed them verbatim. TWO consistency flags (§FLAGS) carry exact edits for lead-63; neither is a
  fork (each has one clear fix), both outside my symbol-scoped writable set.
- Receipt POINTERS: the seam before/after → §SEAM; the typecheck tension + fix → §TYPECHECK; the
  unchanged-count proof → §COUNT; satisfiability notes for the re-grade → §REGRADE; the two flags →
  §FLAGS; DRY → §DRY; gate tails → §GATES.

---

## §SEAM — the identity seam, before → after (all in `test_memory_retrofit_63a.py`)

The defect (contract-63a-3 §FORK, then design §10.5 CLARIFICATION 2026-08-29): the `_exercise_*`
seam called `backend.<verb>(…, capability=…)` (inherited pre-§10.5). §10.5 Reading A (CONFIRMED,
Reading B REJECTED) rules the **BACKEND takes a typed `subject=` and NEVER a capability string**
(capability lives at the TOOL layer; the backend must not read the environment). On a §10.5-compliant
build the whole `retrofit_world` suite would `TypeError` — a latent suite-wide C-DEF the adversary's
satisfiability bound did not cover.

**BEFORE** (`631701e`) — the three seam functions each called the backend with `capability=`:
```python
async def _exercise_remember(backend, *, text, capability, **kwargs):
    return await backend.remember(text, kind="fact", capability=capability, **kwargs)
async def _exercise_recall(backend, *, query, capability):
    return await backend.recall(query, capability=capability)
async def _exercise_invalidate(backend, *, memory_id, capability):
    return await backend.invalidate(memory_id, capability=capability)
```
and the capability fixtures returned a bare `str` token via `_mint_capability`, which opened an
`AgentRegistry`, minted, and **closed it immediately**.

**AFTER** — the seam plays the TOOL-LAYER role exactly as §10.5 CLARIFICATION shape point 1 rules:
- New `_Credential` frozen dataclass bundles what the ONE production constructor needs — `email`
  (the access-token subject), `token` (the raw capability, 62's register mint), and the live
  `registry` / `principal_store` / `keep_store` — because a pin's call site may pass only
  `capability=` (call sites are pins; unchangeable).
- New `_subject_from_capability(capability)` — the ONE place capability→Subject is resolved, shared
  by all three verbs (ONE IMPLEMENTATION): it calls the **REAL** production constructor
  `governed.resolve_subject(access_token(subject=capability.email), capability.token,
  registry=…, principal_store=…, keep_store=…)`. **No test-side `Subject(...)`** (forbidden by shape
  point 1 — it would make the routing observation a fixture, not the production seam; R-a.2's spirit).
- Each `_exercise_*` resolves the subject then calls `backend.<verb>(…, subject=subject)`:
  `remember(text, kind="fact", subject=subject, **kwargs)` · `recall(query, subject=subject)` ·
  `invalidate(memory_id, subject=subject)`. `**kwargs` is retained on `remember` so `scope=` (shape
  point 3 — the one wire arg that legitimately crosses beside `subject=`, a PDP-validated request)
  AND F4's hostile `owner_principal=`/`as_agent=`/`created_by=` fuzz (shape point 4) still reach the
  backend.
- `_mint_capability` → `_minted_credential` (`@asynccontextmanager`, shared by both fixtures): opens
  the `AgentRegistry`, `ensure_ready`, `register`, **yields the `_Credential` (registry stays OPEN)**,
  closes the registry on teardown. The two fixtures became `yield` fixtures wrapping it.

**Shape points honoured (§10.5 CLARIFICATION, 5 points):** (1) tool-layer role via real
`resolve_subject`, no test-side `Subject(...)` — DONE; (2) backend-level identity-less pins
(`backend.recall("anything")` etc. in `TestIdentityLessCallsDeny`) UNTOUCHED, still expect
`GovernedDenied` from `subject=None` — the tool-level twin (`TestIdentityLessToolLayerCallsDeny`) is a
separate pin I did not touch — DONE; (3) `scope=` still flows to the backend via `**kwargs` — DONE;
(4) the F4 pin body (a pin, outside my set) is untouched; `_exercise_remember` keeps `**kwargs` so the
hostile arg still reaches the backend where it hits a `TypeError` or is ignored — the pin's EFFECT
assertion is preserved (I did not turn it into a swallow) — DONE (see §REGRADE for the Reading-A
nuance); (5) writable set = `_exercise_*` + the capability fixtures only; PINS not added/removed;
production code / `lorerunes/pdp.py` / the design doc untouched — DONE.

---

## §TYPECHECK — the one tension and its scope-respecting fix

Typing `_exercise_*`'s `capability` param as `_Credential` produced **15 mypy errors** — the pins
annotate the injected fixture value `alice_capability: str` / `bob_capability: str` in their OWN
method signatures (test bodies, outside my writable set), and mypy resolves a fixture value from the
test-parameter annotation (no pytest plugin links a fixture return to a test param by name), so it saw
`str` flowing into a `_Credential` slot at all 15 `_exercise_*` call sites.

Fix: type the seam's `capability` param `Any` (exactly as the old seam typed `backend: Any`).
`_Credential` remains the runtime container (constructed in `_minted_credential`, consumed via
attribute access in `_subject_from_capability`); the pins keep their `: str` annotations (untouched);
typecheck is clean. This is the minimal change that keeps every edit inside the granted symbols.

Consequence (a FLAG, §FLAGS): the pins' `alice_capability: str` / `bob_capability: str` annotations
are now inaccurate (the fixtures yield `_Credential`). Harmless — never type-checked against the
fixture, and the seam accepts `Any` — but a consistency follow-up if lead-63 wants the annotations
corrected to `_Credential` (a test-body edit, outside my set).

---

## §COUNT — RED count UNCHANGED (54F / 15P / 11E), and WHY

`pytest -n auto` over the 7 `test_*_63a.py` modules → **54 failed / 15 passed / 11 errors** — byte-for
the baseline count the brief names for `631701e` / contract-63a-3 §DELTA. The reshape is INVISIBLE at
HEAD because the fixture chain dies BEFORE any reshaped code runs: `retrofit_world` raises
`NotImplementedError: KeepStore.get_or_create_keyed CAS mint (SF-63-4)` at `keeps.py:543` during
fixture SETUP (the PIN-1 builder-stub), and the capability fixtures + `_exercise_*` are downstream of
it. Verified directly on two of the 11 errored tests — the traceback is the `get_or_create_keyed`
setup error at `keeps.py:543`, **not** any frame in `_minted_credential` / `_subject_from_capability`
/ `_exercise_*`. So the reshape neither moved a test between buckets nor introduced a new error.

The reshape's VALUE is on the CORRECT build (it removes the C-DEF: the seam now matches §10.5 Reading
A instead of the rejected `capability=`-at-the-backend shape). That is what the adversary's re-grade
satisfiability receipt proves — see §REGRADE.

---

## §REGRADE — notes for the adversary's re-grade (the reshaped baseline)

The reshape CHANGES the adversary-graded baseline; the seam must be re-graded before the builder
builds to it (§10.5 shape point 5 sequencing). Three notes:

1. **Correct-build satisfiability of the `retrofit_world` suite now depends on THREE builder
   deliverables, not one:** (a) `KeepStore.get_or_create_keyed` (PIN 1, fixture setup), (b)
   `governed.resolve_subject` (the tool-layer Subject constructor — stub at HEAD), (c)
   `LocalMemoryBackend.remember/recall/invalidate` accepting `subject: Subject | None = None`. A
   re-grade reference build must implement all three for the suite to reach 0-error. (At HEAD all
   three are stubs; only (a) is HIT because it is first in the fixture chain.)
2. **The backend-level F4 pin resolves via the `TypeError` branch on a Reading-A build.**
   `test_a_hostile_owner_argument_does_not_move_the_stamp` passes `owner_principal=<bob>` through
   `**kwargs` → `backend.remember(…, subject=subject, owner_principal=<bob>)`. Under §10.5 the backend
   takes a typed `Subject` and no owner arg, so the kwarg is a `TypeError` → the pin's
   `except TypeError: return` (the "strongest anti-injection", accepted) branch. Its EFFECT assertion
   is therefore likely unreachable at the backend on a correct build — **expected per shape point 4**
   ("at the backend a hostile kwarg is merely a TypeError and proves nothing"); the real F4 guard is
   the TOOL-surface input-schema pin (rider ii / 62). I preserved `**kwargs` so the pin still
   exercises the door; I did not weaken it beyond what §10.5's layering inherently implies.
3. **`backend.<verb>(subject=…)` typechecks only because `backend: Any`** (the seam's long-standing
   idiom). The correct-build backend signature the reshape targets is `subject: Subject | None = None`
   (shape point 2). mypy does not verify the kwarg name against the (stub) backend — the pins prove it
   at runtime on a built backend.

---

## §FLAGS — two out-of-writable-set consistency edits (exact text; not forks)

Both are natural-language / annotation surfaces that the reshape leaves inconsistent with §10.5. Each
has ONE clear fix; neither is a design fork. Surfaced per brief-base §2 (flag with the exact edit, do
not edit outside the granted symbols).

**FLAG 1 — the module docstring's FORK-5 paragraph teaches the REJECTED Reading B.** Lines 10–15 of
`test_memory_retrofit_63a.py` still say *"The design's stated shape is `capability=`"* — a P8d-class
stale surface (prose teaching a retired approach). Exact replacement for that paragraph:
```
⚠ FORK 5 (design §10.5, CONFIRMED 2026-08-29 — REPORT-contract-63a-4.md): identity flows into the
retrofitted recall/remember/invalidate as a typed ``subject=`` at the BACKEND, resolved from a
``capability`` at the TOOL layer (Reading A; Reading B — the backend accepting a capability string —
is REJECTED, it makes the backend read the environment). Following the 62 ``_call_stamp_owner``
precedent, the tool-layer resolution is ISOLATED in ``_exercise_recall`` / ``_exercise_remember`` /
``_exercise_invalidate`` (via ``_subject_from_capability``) so the ruling stayed a one-function-family
edit and traps no build. The pins assert OBSERVABLE behaviour (isolation, owner stamp, default scope,
identity-less DENY), never the wiring.
```

**FLAG 2 — the pins' fixture-param annotations are now inaccurate.** The test-body signatures annotate
`alice_capability: str` / `bob_capability: str`, but the fixtures now yield `_Credential`. Harmless
(never type-checked against the fixture; the seam accepts `Any`), and outside my writable set (test
bodies / pins). If corrected, the exact edits are `alice_capability: str` → `alice_capability: Any`
(or `_Credential`) and likewise for `bob_capability`, at every pin signature that requests them.

---

## §DRY — reuse ledger (3 new test-local symbols)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_subject_from_capability` | `lore_search("test helper resolve capability to Subject credential carrier email token registry for governed backend")` | only my own new helper (watcher-indexed) — no pre-existing capability→Subject carrier; the sole production symbol is `governed.resolve_subject` | **REUSED** `governed.resolve_subject` — the helper is the 3-verb DRY point that wraps the ONE production constructor (shape point 1); the wrapper itself is 5-line test-local convenience |
| `_minted_credential` | (replaces the file-local `_mint_capability`, grep-confirmed used nowhere else in the tree) | the sibling `_mint_capability` register-mint idiom in the same file | **EXTENDED** `_mint_capability` — same `registry.register` mint, now an `@asynccontextmanager` that packages the `_Credential` and keeps the registry OPEN for the test (a lifecycle superset, not a fork) |
| `_Credential` (frozen dataclass) | (same search as row 1) | no existing credential/subject carrier in the test tree | **HAND-ROLLED** — test-local trivia: a typed record bundling `email`/`token`/`registry`/`principal_store`/`keep_store` so the (unchangeable) call sites can pass only `capability=`. Not shared production policy — a container, not a mechanism |

`_mint_capability`/`alice_capability`/`bob_capability` are used ONLY in `test_memory_retrofit_63a.py`
(grep over `loremaster/tests/` returned nothing else) — so reshaping them touches no other module.

---

## §GATES — receipts (tails)

- `uv run ruff check .` → `All checks passed!` (exit 0).
- `bash scripts/typecheck.sh` → all members OK incl. `loremaster` (249 source files: no issues),
  shellcheck OK — every leg passed (exit 0). The `resolve_subject` call + `subject=` kwarg typecheck.
- 7 × `test_*_63a.py` (`-n auto`) → **54 failed / 15 passed / 11 errors** in 10.39s (RED contract,
  UNCHANGED from baseline; §COUNT reconciles it — all 11 errors are the `get_or_create_keyed` setup
  stub at `keeps.py:543`).
- 60/61/62 regression sweep (`-n auto`, 12 modules: keeps store/schema/cli · principals
  store/schema/cli · agent-capability + reach + seams · pdp-oracle-61b · tool-population-61b ·
  memory-cutover) → **378 passed** in 18.91s. Test-only change; no shipped behaviour touched. (Count
  differs from contract-63a-3's 392 only because I selected a marginally different 12-module set;
  both green, 0 failures.)

There are 0 failing tests unrelated to our present scope in the sweeps I ran.
