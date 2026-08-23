brief-base v14 read
brief project v7 read

# REPORT — builder-61a-w2 (#400, the shared engine-rejection wrap seam)

## SUMMARY BLOCK
- **State:** done
- **Deviations:** none.
- **Packages considered:** none — the mechanism is an INTERNAL DRY extraction (a contextmanager
  built from `contextlib`); no external library evaluated. (stdlib `contextlib.contextmanager` IS
  the package doing the job for Layer 1 — not hand-rolled `__enter__`/`__exit__`.)
- **Reuse ledger:** 2 new symbols, both dispositioned (see DRY LEDGER). No new POLICY clone —
  the whole point is REMOVING duplication.
- **Graded:** n/a (builder, not a verdict-rendering pass). Built at HEAD `fb68427`.
- **Decisions-needed:** none.
- **Receipt pointers:** Layer 1 `lorerunes/lorerunes/engine_rejection.py::reclassify`; Layer 2
  `loremaster/loremaster/store/_txn.py::wrap_store_rejection`; 9 routed sites in
  `principals.py`/`keeps.py`/`principal_keys.py`; contract 76/76 GREEN; typecheck 0; ruff clean.

## WHAT WAS BUILT (the ruled TWO-LAYER seam, D2)

### Layer 1 — `lorerunes.reclassify` (NEW stdlib-only module)
`lorerunes/lorerunes/engine_rejection.py` — a `@contextlib.contextmanager` parameterised over the
exception CLASSES it receives (`*, passthrough, catch, make_error`, all keyword-only):
```
try: yield
except passthrough: raise            # FIRST — passthrough SUBCLASSES catch
except catch as error: raise make_error() from error
```
Imports ONLY stdlib (`contextlib`, `collections.abc`) — no sibling. Re-exported from
`lorerunes/__init__.py` and added to `__all__` (alphabetical, after `normalize_email`).

### Layer 2 — `loremaster.store._txn.wrap_store_rejection(domain_error, context)`
The ONE surreal-taxonomy binding. Returns `reclassify(passthrough=(SurrealConnectionError,
TxnContentionExhaustedError), catch=(SurrealStoreError,), make_error=lambda: domain_error(context))`.
Added `from lorerunes import reclassify` + `from contextlib import AbstractContextManager` to `_txn`.
The taxonomy is named in exactly this one place.

### The 9 routed sites (routed-set = 9, addendum-4)
Each site's explicit `try/except (Conn,Contention): raise; except SurrealStoreError as e: raise
<Domain>(...) from e` replaced by `with wrap_store_rejection(<Domain>, <context>): <awaited call(s)>`.
Behaviour byte-identical: transport propagates, store-error wraps as the domain error with `from`,
the same context in the message.

| # | module | method | domain error |
|---|--------|--------|--------------|
| 1 | principals.py | `PrincipalStore.create` | PrincipalStoreError |
| 2 | principals.py | `PrincipalStore.set_subject` | PrincipalStoreError |
| 3 | principal_keys.py | `PrincipalKeyStore.mint` | PrincipalKeyStoreError |
| 4 | keeps.py | `KeepStore.create_keep` | KeepStoreError |
| 5 | keeps.py | `KeepStore.add_household_member` | KeepStoreError |
| 6 | keeps.py | `KeepStore.remove_household_member` | KeepStoreError |
| 7 | keeps.py | `KeepStore.set_rank` | KeepStoreError |
| 8 | keeps.py | `KeepStore.set_keeper` | KeepStoreError |
| 9 | keeps.py | `KeepStore.delete_keep` | KeepStoreError |

**Behaviour preservation (the DUAL):** all three domain-error families (`KeepStoreError`,
`PrincipalStoreError`, `PrincipalKeyStoreError`) subclass `RuntimeError`, **not**
`SurrealStoreError` (verified: `keeps.py:154/158/162`, `principals.py:207/211`,
`principal_keys.py:173`). So the deliberate refusals raised INSIDE the `with` block
(`KeepNotFoundError`, `KeeperLockoutError`, `PrincipalNotFoundError`, ghost-email `KeepStoreError`)
are NOT in `catch=(SurrealStoreError,)` and pass through the seam untouched — exactly as they
passed through the old `except SurrealStoreError` clause. The trailing `if <row> is None:` guards
stay OUTSIDE the `with`, unchanged.

### Orphaned imports removed (the extraction leaves them unused — ruff-confirmed)
- `keeps.py`: dropped `SurrealStoreError` (its only executable uses were the 6 removed `except`
  clauses; docstrings still reference it as prose, which ruff ignores).
- `principal_keys.py`: dropped `SurrealStoreError` (only use was the one removed `except`).
- `principals.py`: KEPT all `_txn` imports — `SurrealStoreError` still used at
  `principals.py:_read_datetime` (a real `raise SurrealStoreError(...)`), `SurrealConnectionError`
  / `TxnContentionExhaustedError` / `_CONNECTION_ERRORS` still used in `_ensure_connection` +
  the CLI dispatch. Added `wrap_store_rejection` to all three import blocks.

## GATE RECEIPTS

### Contract (both RED-contract files) — GREEN
```
uv run python -m pytest lorerunes/tests/test_engine_rejection.py \
    loremaster/tests/test_engine_rejection_seam.py -n auto
76 passed in 6.50s          # 20 lorerunes + 56 seam = 76, matching the brief's reference-build count
```

### typecheck — 0
```
./scripts/typecheck.sh
… lorerunes OK / lorescribe OK / loresigil OK / loremaster OK (226 src) / skills OK / scripts OK
```

### ruff — clean
```
uv run ruff check .
All checks passed!
```

### Full loremaster suite — 0 failed
```
uv run python -m pytest loremaster/tests -n auto -q
8466 passed, 50 skipped, 3 xfailed, 8 warnings in 269.69s (0:04:29)     # EXIT=0
```
Ran `-n auto` (I am the only agent on the store — no concurrent load, so the #405 store-contention
flake did not require a solo re-run). Zero failures; the 231 behaviour-preservation pins + the rest
all green.

### registration_sites.py — no new WORKSPACE MEMBER; symbol registration done per contract
`./scripts/registration_sites.py` — this work adds two FUNCTIONS to existing members (`lorerunes`,
`loremaster`), not a new workspace member, so no member-registration site needs updating. The 22
STALE co-occurrence lines it reports are all PRE-EXISTING (docs/tests where 3-of-4 member names
co-occur) — NONE is in a file I touched and NONE references `reclassify`/`wrap_store_rejection`.
The two new symbols are registered the way the contract pins require:
- `reclassify` → `lorerunes/__init__.py` re-export + `__all__` (pin
  `TestPackageReExport::test_reclassify_is_re_exported_and_listed_in_dunder_all` GREEN).
- `wrap_store_rejection` → module-level in `loremaster.store._txn`, importable (loader
  `_load_wrap_store` + the Layer-2 mutation pins GREEN).

## MUTATION PROOFS (real tree — `cp -a` backup at `/tmp/w2_mutbak/`, byte-exact restore each)

Provenance receipt (mutations were on the REAL tree, not a scratch copy):
`loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`,
`lorerunes.__file__ = /home/ejprice/PycharmProjects/lore/lorerunes/lorerunes/__init__.py`.

| # | mutation | pins that RED (the SHARING discriminator) | result | restore |
|---|----------|-------------------------------------------|--------|---------|
| a | `reclassify` (Layer 1): drop the `except passthrough: raise` (naive catch-all translates transport) | seam `test_transport_faults_propagate_untouched` — **all 9 sites × 2 transports = 18** + lorerunes `TestPassthroughIsReRaisedFirst` (4) | **22 failed** | `diff -q` → byte-exact |
| b | `_txn.wrap_store_rejection` (Layer 2): drop `TxnContentionExhaustedError` from `passthrough` | seam `test_transport_faults_propagate_untouched[*-contention]` — **all 9 sites' contention** red; **all 9 connection GREEN** | **9 failed, 9 passed** | `diff -q` → byte-exact |
| c | `keeps.delete_keep`: revert to a PRIVATE hand-rolled `try/except` copy (not routed) | reach `test_no_full_idiom_wrap_appears_outside_the_seam`; coverage `test_the_routed_set_equals_the_{invocation_map,known_wrapping_verbs}[keep]`; sharing `test_dropping_LAYER{1,2}..._moves_every_routed_path[keep-delete_keep]` | **5 failed, 20 passed** | `diff -q` → byte-exact |

Interpretation: (a) proves the CONTROL-FLOW is one shared thing across all 9 (a Layer-1 change moves
every site); (b) proves the TAXONOMY is one shared thing across all 9 (a Layer-2 change moves exactly
the contention leg of every site, and NOT the connection leg — a precise, non-vacuous discriminator);
(c) proves ROUTING-IS-NOT-SHARING is caught four ways (the shape-reach guard, both coverage pins, and
BOTH mutation pins fail a private copy). After all three restores the contract re-ran **76 passed** and
`ruff` on the five touched files is clean — the byte-exact restore is verified functionally, not only
by `diff`.

## DRY LEDGER (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `lorerunes.reclassify` | `lore_search "exception reclassification / engine rejection wrap contextmanager"` (+ read of `_txn.py` + the 9 sites) | the 9 hand-rolled `except (Conn,Contention): raise; except SurrealStoreError: raise <Domain> from e` clones — the duplication #400 names; no existing shared helper | **HAND-ROLLED** — this IS the extraction that removes the 9 clones; charter home is stdlib-only `lorerunes` (D2 Layer 1). No prior shared symbol existed. |
| `_txn.wrap_store_rejection` | read of `_txn.py` (owns `SurrealStoreError`/`SurrealConnectionError`/`TxnContentionExhaustedError` + the classification helpers `is_connection_error`/`retry_on_conflict`) | `_txn` is the ONE home of the surreal error taxonomy; no existing binder of it to a contextmanager | **HAND-ROLLED** — the ruled Layer-2 taxonomy binding (D2); delegates control flow to `reclassify` (no clone). Lives with the taxonomy it binds. |

`lorerunes` imports no sibling — confirmed by the contract's `TestTheNewModuleImportsNoSibling` +
the repo-wide `test_secret_typing` rglob purity pin (both GREEN in the 76).

## FILES TOUCHED
- `lorerunes/lorerunes/engine_rejection.py` (NEW — Layer 1)
- `lorerunes/lorerunes/__init__.py` (re-export + `__all__`)
- `loremaster/loremaster/store/_txn.py` (Layer 2 + 2 imports)
- `loremaster/loremaster/principals.py` (2 sites + import)
- `loremaster/loremaster/keeps.py` (6 sites + import, dropped orphaned `SurrealStoreError`)
- `loremaster/loremaster/principal_keys.py` (1 site + import, dropped orphaned `SurrealStoreError`)
- `REPORT-builder-61a-w2.md` (this file)

Not committed (the lead commits after a cold audit). The RED-contract test files were NOT edited.
