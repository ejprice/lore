# REPORT-adversary-48a — Contract adversary, packet 48 Wave 48-A (`build_store` extraction)

`brief-base v14 read` · `brief project v7 read`

## DELTA RE-CHECK — revision r2 (2026-08-20, contract HEAD `57c0a3d`, file untracked)

**VERDICT (r2): CONTRACT SUFFICIENT.** The author's r2 (REPORT-contract-48a.md §"Revision r2")
fixed both r1 findings; I re-verified EMPIRICALLY in the same scratch tree
(`loremaster.__file__ = /tmp/adv48a/loremaster/loremaster/__init__.py`), all four legs the lead
named:

1. **Satisfiability = 11 passed / 0 failed** against a CORRECT `build_store` carrying the
   design's **ruled docstring VERBATIM** (the prose that literally names
   `config._reject_url_userinfo` and says "never parses or handles credentials in the URL"). The
   new AST-based R4 pin does NOT redden on that docstring, nor on the legitimate
   `config.surreal.password_env`/`user_env` accesses (they are AST attrs `password_env`/`user_env`,
   never `password`/`username`). MP-1 is genuinely fixed — and by the *right* instrument: AST
   structure, not a source-text substring (the CLAUDE.md instrument-lesson).
2. **MP-1 not over-weakened (positive controls both RED):** `urlsplit(config.surreal.url).username`
   → R4 pin RED; `urlparse(config.surreal.url).password` (the lead's exact example) → R4 pin RED.
   Real URL-credential parsing is still caught (banned Call `urlparse`/`urlsplit`/`_reject_url_userinfo`,
   banned Attribute `username`/`password`/`userinfo`).
3. **MP-2 CLOSED:** a `namespace="lore_test"`-hardcoding build → **4 resolution pins RED**; a
   `dim=2048`-hardcoding build → **4 resolution pins RED** (both SURVIVED in r1; the distinctive
   sentinels `_SENTINEL_NAMESPACE="contract48_ns_sentinel"` / `_SENTINEL_DIM=1493` /
   `_SENTINEL_URL` now discriminate).
4. **No new gap:** routing-2/3 (scout inline) → scout structural pin RED; readied/async → un-readied
   pin + cascade RED; swapped-creds → 4 resolution pins RED. All prior wrong builds still caught.
   RED-now shape unchanged (author's 9 failed / 2 passed reproduced in r1). The **mutation proof
   now HOLDS (exit 0)** on the r2 contract (declared-4 fire exactly, structural stay green,
   R4 no longer an undeclared red — in r1 it failed exit 4 solely because of the C-DEF).

**One residual, UNCHANGED and explicitly NON-BLOCKING (same as r1 R3):** a *contrived* build that
strips inline creds with plain string ops (`partition`/`rpartition`, no `urlparse`/`urlsplit`/
banned attr) survives (11 passed) — no code-structure pin, substring OR AST, can catch arbitrary
string manipulation. This is not a NEW gap (in r1 it was "caught" only by the spurious `.password`,
i.e. by the C-DEF bug itself); the realistic regression surface is fully covered. I do not block
on it. `Packages considered:` unchanged — none (internal extraction).

`Graded (r2): 57c0a3da7fabb89a2a5dae107177b4dcb3b31fe3 · HEAD-at-report:
57c0a3da7fabb89a2a5dae107177b4dcb3b31fe3 · SAME` (contract file UNTRACKED at this HEAD; read from
disk). Message to lead-48: §1 micro-format, VERDICT SUFFICIENT.

---

## SUMMARY BLOCK (r1 — historical; superseded by the r2 delta re-check above)
- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 headline (a wrong build survives + a C-DEF):** ① **C-DEF / STOP** — the R4 pin
  `test_build_store_body_has_no_url_credential_parsing` reddens on a *known-CORRECT* build,
  because its forbidden token `".password"` is a **substring of the required
  `config.surreal.password_env`**. Satisfiability against the correct reference build =
  **1 failed / 10 passed** (should be 0 failed). ② **A wrong build survives** — a `build_store`
  that hardcodes `namespace="lore_test"` (or `dim=2048`) passes the ENTIRE contract once the
  C-DEF is fixed (**11 passed**), because those fixture values are non-distinctive
  (FIXTURES-MUST-DISCRIMINATE).
- **Everything else discriminates:** every genuine wrong build (routing-2/3, readied/async,
  hardcoded-db, swapped-creds, wrong-dim-field, structural-only satisfier, no-route) is caught
  by some pin; structural and resolution pins are genuinely complementary; the declared
  mutation-proof set of 4 is mechanically correct.
- **Graded:** `9195839f6dc9e54321656d18a5f983bc62aa7d01` · HEAD-at-report:
  `9195839f6dc9e54321656d18a5f983bc62aa7d01` · **SAME** (contract file is UNTRACKED at this HEAD;
  read from disk).
- **Scratch provenance receipt (finding #140):** `loremaster.__file__ =`
  `/tmp/adv48a/loremaster/loremaster/__init__.py` (built by `scripts/scratch_copy.sh`,
  provenance-asserted). Every build below ran in that scratch tree.
- **Packages considered:** none — the contract specifies no mechanism (an internal factory
  extraction of an existing recipe; credential resolution reuses `config.resolve_config_value`
  / `resolve_secret`). I concur with the author's `none`. My own survey found no library that
  applies. Diff = empty.
- **decisions-needed:** none for me — the two missing pins below are the author's to fix
  (contract stays INSUFFICIENT until then). Fixes are demonstrated one-liners.

## Message to lead-48
`STATE: blocked:contract-insufficient · REPORT: REPORT-adversary-48a.md · 48-A build_store: C-DEF (R4 token '.password' ⊂ '.password_env' reddens correct build, 1-failed/10-passed) + fixture monoculture (namespace/dim hardcode survives). 2 demonstrated one-line fixes. NOT ready for builder.`

---

## Missing pins (what the author must fix — each with the build it fails to catch)

### MP-1 — C-DEF (BLOCKER, STOP): the R4 forbidden-token list false-positives on every correct build
`test_build_store_body_has_no_url_credential_parsing` asserts none of
`("urlparse", "urlsplit", "userinfo", ".username", ".password", "_reject_url_userinfo")`
appears in `inspect.getsource(build_store)`. But a correct `build_store`, following design §1
verbatim, resolves the password via `resolve_secret(config.surreal.password_env)` — and
`".password"` is a **substring of `".password_env"`**. So the pin reddens on the reference
build.

- **The build it wrongly reddens:** the CORRECT `build_store` (design §1 signature, resolving
  creds internally). Observed `AssertionError: … found '.password'. … '.password' is contained
  here: ig.surreal.password_env)` — reproduced below (§"Satisfiability receipt").
- **Consequences, all measured:**
  1. Satisfiability = **1 failed / 10 passed** on a known-correct build (a C-DEF — the contract
     ships a pin the builder cannot make green without contorting the code, e.g.
     `getattr(config.surreal, "password_env")`, which defeats the pin's purpose).
  2. It breaks the author's OWN mutation-proof receipt: running `scripts/mutation_proof.py`
     with the declared-4 set against the correct build **FAILS (exit 4)** — R4 is an
     undeclared constant red (§"Mutation proof").
  3. It provides **zero R4 discrimination**: it is red on *every* build that references
     `password_env` (i.e. every valid one), so it can never distinguish an R4 violation from a
     correct build.
- **Demonstrated fix (one line):** drop `".password"` from the token tuple. Keeping
  `urlparse`/`urlsplit`/`userinfo`/`.username`/`_reject_url_userinfo` is safe — none is a
  substring of any correct `build_store`'s source (`user_env` does NOT contain `.username`).
  With `".password"` removed: correct build → **11 passed / 0 failed**, and the mutation proof
  → **PROOF HELD** (exit 0). Both reproduced below.
- **Deeper (per CLAUDE.md "when you enumerate the FORBIDDEN set you have already lost"):** even
  after the fix the pin is a forbidden-token ENUMERATION observing a PROXY (source text). It
  still cannot catch a build that strips inline credentials with plain string ops
  (`partition`/`rpartition`) — my `r4_strip_dodge` build carries no forbidden token yet strips
  `user:pass@` from the URL, and would pass a fixed R4 (§WB4b). This is contrived for the narrow
  extraction (the realistic regression is copying `urlsplit`/`_reject_url_userinfo`, which the
  kept tokens catch), so I do NOT block on it — but the durable form is an EFFECT pin: assert
  `build_store` passes `config.surreal.url` through byte-identical (the resolution pin's
  `store._url == config.surreal.url` already half-covers this; a url-with-userinfo fixture can't
  be built because config rejects it upstream — the R4 upstream anchor #10 — so the effect pin's
  reach is inherently bounded, which is itself the argument for keeping R4 minimal and honest
  rather than elaborate and wrong).

### MP-2 — Fixture monoculture: a hardcoded `namespace`/`dim` build survives the whole contract
`_assert_store_resolved` checks all six resolved values, but the fixture's `namespace`
(`_SURREAL_TEST_NAMESPACE = "lore_test"`) and `dim` (`_DIM = 2048`) are **non-distinctive
constants**. A `build_store` that hardcodes `namespace="lore_test"` (or `dim=2048`) instead of
resolving it passes **11/11** (measured, §WB3d + dim-hardcode). The `database` leg (unique
per-test uuid slug) and the `user`/`password` legs (distinctive sentinels) are strong; the
`namespace`, `dim` and `url` legs are decoration for the hardcode case — they cannot tell a
build that RESOLVES the value from one that HARDCODES the fixture's value.

- **The build it fails to catch:** `build_store(config)` that returns
  `SurrealStore(..., namespace="lore_test", ...)` (or `dim=2048`), ignoring `config`.
- **Fix:** make the fixture's `namespace` distinctive (a sentinel or per-test uuid, like the
  creds/db already are) and `_DIM` a distinctive value threaded consistently into
  `FakeEmbedder(dim=…)` (the probe gate requires embedder-dim == config-dim, so pick any
  distinctive value and use it in both places — e.g. `_DIM = 1731`). The `url` leg is the same
  class but hardcoding `surreal_url()` is implausible; distinctive namespace+dim is the pin that
  matters. **The law is explicit** (CLAUDE.md): "If the code can branch on a value, at least one
  pin must use a DIFFERENT value" — here every pin uses the same value per field, and two of
  those values are guessable defaults.

---

## P1b — QUANTIFIER TABLE (every invariant classified; every guarded row carries a receipt)

| # | Invariant | ∀-over-inputs / guarded | Receipt |
|---|---|---|---|
| INV1 | `build_store` resolves url/ns/db/dim/user/pass from config | **Split.** db/user/pass legs ∀ (distinctive values, cannot hardcode-pass). ns/dim/url legs **guarded-by-monoculture** — pass a value == fixture. | WB3a (db) / WB3b (creds) / WB3c (dim via wrong FIELD) all RED → strong legs fire. **WB3d (ns hardcode) + dim=2048 hardcode SURVIVE (11 passed)** → the monoculture hole (MP-2). |
| INV2 | `build_store` returns UN-READIED (sync, `_connection is None`) | **∀** over the readied/unreadied axis (iscoroutinefunction + `_connection`). | WB2 (async self-readying) → `test_build_store_returns_unreadied_store` RED. |
| INV3 | `build_store` parses no URL credentials (R4) | **Guarded — by a forbidden-token list (the wrong guard).** False-positives on the correct build (MP-1); misses a string-op strip. | Correct build RED (C-DEF); WB4 (urlsplit) RED for the right token; WB4b (partition strip) RED only via the spurious `.password`. |
| INV4 | Each of the 3 callers routes its store through `build_store` (no inline `SurrealStore(`) | **∀ over the 3 sites** — three independent structural pins. | WB1 (scout kept inline) → scout structural pin RED, other two green (routing-2/3 caught). WB6a (nothing routed) → all 3 RED. WB5 (calls build_store AND inline) → build_app_context structural RED. |
| INV5 | Readiness variance preserved: server+cli ready, scout does not | **∀** — behavioral (sentinel fires for the two readied, must NOT fire for scout). | WB2 (build_store readies) → scout's `…is_resolved_and_unreadied` RED (variance broken). |

No invariant is left un-classified; the two `guarded` rows (INV1-partial, INV3) carry the
surviving-wrong-build receipts that make them MISSING PINS (MP-2, MP-1).

## P1c — REACH TABLE (every guard the contract introduces / relies on)

| Guard | Reach: DERIVED vs hand-list | Coverage a checked variable? | Effect vs proxy | One-source / mutation | Verdict |
|---|---|---|---|---|---|
| `_direct_call_names` (AST routing scan) | DERIVED — `ast.walk` over the caller's OWN `inspect.getsource` (not a name list) | 3 sites each get their OWN explicit pin; no auto-growth, but the site set (3) is fixed and complete for this packet | PROXY (source AST) — deliberately the STATIC catch, paired with the resolution EFFECT pins | n/a (no shared policy) | OK, with one bound: it sees **direct** Call names only. A build that constructs `SurrealStore` **transitively** (via a helper the caller calls) would pass — shallow reach. Contrived here; noted. |
| R4 forbidden-token grep | **HAND-LIST** (6 literal tokens) — the classic hidden-constant / forbidden-enumeration | NOT checked — token set is hardcoded; a benign token that collides (`.password`) or a hostile idiom it omits (`.partition`) is silently in/out of reach | **PROXY** (source text), never the effect (url passed verbatim) | n/a | **MISSING (MP-1).** This reach failure IS the C-DEF: an unbounded forbidden-set that already contains a false positive and a known gap. |
| `ensure_ready` capture patch (class-level `SurrealStore.ensure_ready`) | DERIVED — patches the class, fires for whichever `SurrealStore` is readied | Captures the FIRST readied `SurrealStore`; for both readied callers that is the intended store (verified — no other `SurrealStore` readies earlier) | **EFFECT** — records the actual constructed store, aborts before any socket (offline) | n/a | OK. Genuinely observes the store the caller built, not a proxy. |

Legs run: `_direct_call_names` and the capture patch were exercised empirically (every WB run
routes through them). The R4 grep was exercised empirically (correct build + WB4/WB4b). No
construction-inspection-only rows.

## Fixture-discrimination verdicts (PERTURB + control)

| Fixture value | Distinctive? | Verdict |
|---|---|---|
| `database` = per-test `test_<uuid4>` slug (via `effective_surreal_database`, no `surreal.database`) | **YES** (unique) | STRONG — cannot hardcode-pass; the mutation-proof anchor. Control: WB3a (hardcode) RED. |
| `user` = `"contract48-user-sentinel"`, `password` = `"contract48-pass-sentinel"` | **YES** (sentinels) | STRONG — control: WB3b (swap) RED. |
| `namespace` = `"lore_test"` | **NO** (constant) | **WEAK (MP-2)** — perturbation: a build hardcoding `"lore_test"` SURVIVES 11/11. Control: a build mis-resolving ns to a *different* field (WB-analogous) would be caught, but a literal-match escapes. |
| `dim` = `2048` | **NO** (guessable default) | **WEAK (MP-2)** — perturbation: `dim=2048` hardcode SURVIVES 11/11. Control: WB3c (dim from wrong FIELD, 8192) RED — so the leg discriminates a wrong *field* but not a matching *literal*. |
| `url` = `surreal_url()` | NO (constant) | Same class as namespace/dim, but hardcoding it is implausible; not pushed. |

Positive control for the whole harness: on a CORRECT build with the C-DEF token removed, the
contract is **11 passed / 0 failed** (§Satisfiability) — the probe can see right-from-wrong.

## RED honesty (P7), corpse sweep (P6/P6b), standing guards (P4)

- **RED-now honesty:** the as-shipped contract at `9195839` against a tree with **no**
  `build_store` and inline callers = **9 failed / 2 passed** — matches the author's declared
  RED-now state exactly (6 factory-gated `pytest.fail` + 3 structural `AssertionError`; the 2
  standing guards green). Reproduced (§WB6b). The 9 reds are for the right reason (factory
  absent / inline construction), not import/collection errors.
- **P6 corpse sweep (contract file):** `test_build_store.py` is a NEW file; no pin asserts the
  OLD inline world as a passing expectation — the inline construction is asserted ABSENT
  (structural pins), which is the new world. No corpse.
- **P6b orphaned-virtue inventory (the extraction REPLACES inline construction at 3 sites):**
  independent enumeration of the inline blocks' observable behavior — (a) construct
  `SurrealStore` with the 6 resolved values, (b) ctor-only / un-readied, (c) `analyzer_name` /
  `entity_tables` left at ctor defaults, (d) **server site ALSO calls
  `write_store.register_entity_tables(...)` AFTER construction.** (a)+(b)+(c) are preserved and
  pinned (resolution + un-readied pins). **(d) is NOT pinned** — see residual R1. The
  extraction is byte-faithful on the store construction; the only unpinned removed-behavior is
  the post-construction entity-table registration, which lives in `build_app_context`, not
  `build_store`.
- **Standing guards (P4):** #11 `test_eager_startup_lifespan_symbol_stays_deleted` reddens when
  `_EagerStartupLifespan` is resurrected (verified — appended `_EagerStartupLifespan = object`
  → RED). #10 `test_config_load_rejects_inline_url_credentials` is green for the right reason (a
  `ws://user:pass@…` url genuinely raises `ValidationError` at load). Both are real pins, not
  decoration.

## Residuals (each individually verdicted)

- **R1 — server-site `register_entity_tables` unpinned (removed-behavior inventory item).** The
  narrow extraction leaves `write_store.register_entity_tables(...)` in `build_app_context`
  (correct — not `build_store`'s job). The contract has no pin that this call survives the
  routing edit. **Verdict: note, not blocking** — it is out of `build_store`'s scope, and the
  entity-table wiring is covered by `test_ingest_entity_seam` / `test_server_chunker_wiring`.
  Flag for the builder: keep the `register_entity_tables` call after `write_store = build_store(config)`.
- **R2 — existing wiring tests are routing-compatible (no defect).** `test_comms_wiring.py`
  (`TestWriteStackUnwindIncludesCommsLedgers`) and `test_mcp_server.py:798` monkeypatch
  `store_module.SurrealStore` (= `loremaster.store.surreal.SurrealStore`) with a `_TrackedStore`
  and assert `len(opened) == 2`. Because `build_store` will live in `store.surreal` and
  reference the module-global `SurrealStore`, the patch STILL intercepts after routing — so
  these tests survive the change. **Verdict: no defect; a reason to keep `build_store` in
  `store.surreal.py`** (design §1 / author F2 already rule this).
- **R3 — `_direct_call_names` sees direct calls only (shallow reach).** A build constructing
  `SurrealStore` via an indirect helper would pass the structural pin. **Verdict: contrived for
  this packet; note.** The resolution+mutation pins catch the realistic mis-resolution regardless.
- **R4 — author F1 (chain wording) is not a contract defect.** #11 asserts
  `build_mcp_server`/`_eager_build_with_retry`/`build_app_context` exist (all present) and
  `_EagerStartupLifespan` absent; the immediate caller `_eager_build_or_operator_safe_error` is
  not pinned, which is fine (the pin's job is the deleted symbol + the terminal builder).
  **Verdict: no defect.**

---

## Full probe record (commands + real output)

All runs in the provenance-verified scratch tree `/tmp/adv48a`
(`loremaster.__file__ = /tmp/adv48a/loremaster/loremaster/__init__.py`). Builds applied by a
reproducible exactly-once-checked patcher (`/tmp/adv_apply.py`, pasted at the end so the
measurement is re-runnable per brief-base §1 — a scratch instrument is a deliverable).

### Satisfiability receipt (the required 0-failed proof — it FAILS as shipped)

Correct `build_store` (design §1 recipe) + all 3 sites routed, full contract:

```
$ python /tmp/adv_apply.py correct        # add build_store + route server,cli,scout
$ uv run pytest loremaster/tests/test_build_store.py -p no:xdist -q
..F........
FAILED test_build_store_body_has_no_url_credential_parsing
  AssertionError: build_store must not parse/handle URL credentials; found '.password'.
    '.password' is contained here: ig.surreal.password_env)
1 failed, 10 passed in 2.78s
```

With the C-DEF token `".password"` removed from the R4 tuple (P2 scratch-copy edit of the
contract), the SAME correct build:

```
$ uv run pytest loremaster/tests/test_build_store.py -p no:xdist -q
...........
11 passed in 1.05s
```

→ the C-DEF token is the SOLE blocker; the rest of the contract is satisfiable.

### Wrong-build matrix (R4 pin is a constant red as shipped — subtract it)

| Build | routed | reds (minus constant R4) | caught by | verdict |
|---|---|---|---|---|
| WB1 routing 2/3 (scout inline) | server,cli | `scout_from_config_routes_store_through_build_store` | structural pin | CAUGHT |
| WB2 readied/async factory | all 3 | `returns_unreadied`, `resolves_all_six`, both readied-caller pins, scout-unreadied | un-readied + cascade | CAUGHT |
| WB3a hardcoded database | all 3 | 4 resolution pins | resolution (db leg) | CAUGHT |
| WB3b user/password swapped | all 3 | 4 resolution pins | resolution (cred legs) | CAUGHT |
| WB3c dim from wrong FIELD (8192) | all 3 | 4 resolution pins | resolution (dim leg) | CAUGHT |
| **WB3d namespace hardcoded "lore_test"** | all 3 | **none** | — | **SURVIVES (11 passed on fixed contract)** — MP-2 |
| **dim hardcoded 2048 (=_DIM)** | all 3 | **none** | — | **SURVIVES (11 passed on fixed contract)** — MP-2 |
| WB4 r4 urlsplit reparse | all 3 | (only R4) | R4 token `urlsplit` | caught, but R4 is broken |
| WB4b r4 string-op strip (no forbidden token) | all 3 | (only R4, via spurious `.password`) | — | would ESCAPE a fixed R4 (contrived) |
| WB5 structural-only satisfier (calls build_store + inline SurrealStore) | cli,scout + injected call | `build_app_context_routes_write_store_through_build_store` | structural (resolution PASSES) | CAUGHT — complementarity proven |
| WB6a correct build_store, nothing routed | none | 3 structural pins | structural | CAUGHT |
| WB6b build_store absent, nothing routed | none | 9 failed / 2 passed | RED-now baseline | matches author |

### Mutation proof (declared-4, mutate `build_store`'s resolved `database`)

As shipped (R4 red): `scripts/mutation_proof.py … --expect-red <the 4> -- uv run pytest …`

```
PROOF FAILED — the observed RED set is not the declared one.
  WENT RED but was NOT DECLARED:
    + …::test_build_store_body_has_no_url_credential_parsing
  declared: [build_app_context…, resolves_all_six, index_cli…, scout…unreadied]
  observed: [build_app_context…, body_has_no_url_credential_parsing, resolves_all_six, index_cli…, scout…unreadied]
MUTATION_PROOF_EXIT=4
```

The 4 declared pins DID redden and the structural pins #7-9 stayed green (both-ways diff clean);
the ONLY discrepancy is R4 as an undeclared constant red. With `".password"` removed:

```
PROOF HELD — the declared RED set fired EXACTLY: [build_app_context…, resolves_all_six, index_cli…, scout…unreadied]
MUTATION_PROOF_EXIT=0
```

→ the author's declared-RED set of 4 is **mechanically correct**; it is only *unrunnable* until
the C-DEF is fixed.

### Standing-guard mutation checks (P4)

```
# resurrect the deleted symbol -> #11 reddens
$ printf '\n_EagerStartupLifespan = object\n' >> server.py
$ uv run pytest …::test_eager_startup_lifespan_symbol_stays_deleted -q  -> 1 failed
# restored -> #10 + #11 both green (for the right reason)
$ uv run pytest …::test_eager_startup_lifespan_symbol_stays_deleted …::test_config_load_rejects_inline_url_credentials -q  -> 2 passed
```

### The scratch instrument (re-runnable; brief-base §1)

`/tmp/adv_apply.py` — applies each build variant to `/tmp/adv48a` with exactly-once anchor
assertions (the #194 lesson). Variants: `correct`, `readied`, `misresolve_db`, `swap_creds`,
`misresolve_dim`, `misresolve_ns`, `r4_parse`, `r4_strip_dodge`, `none`; routing subset via a
comma list (`-` = route nothing). Key anchors: server write_store block, cli `store =` block,
scout `store =` block (each replaced with `… = build_store(config)`), plus the three
`SurrealStore` imports augmented with `build_store`. Full source is in the scratch tree; it is
disposable, so the load-bearing facts it produced are the pasted receipts above, not the tool.
```

---

_Adversary posture held: I built ten+ wrong implementations and a correct reference, ran the
real contract against each, and produced the satisfiability + mutation receipts. The contract is
strong on the hard part (three-site routing-is-not-sharing, readiness variance, credential
resolution via distinctive db/creds) and fails on two fixable things: a forbidden-token that
collides with a required reference (STOP), and two non-distinctive fixture values._
