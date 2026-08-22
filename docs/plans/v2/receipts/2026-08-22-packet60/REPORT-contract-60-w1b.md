# REPORT-contract-60-w1b — packet 60 wave 1 CONTRACT REVISION (the one missing pin)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done. The adversary's single missing pin (attack 9 — the store-§2 `SELECT *`
  nameless-keep read-back) is CLOSED with **two** pins + a full mutation proof.
- **What I added (to `loremaster/tests/test_keeps_store.py` ONLY):**
  `TestGetKeep::test_get_keep_reads_back_a_NAMELESS_keep` and
  `TestListKeepsForKeeper::test_list_keeps_for_keeper_lists_a_NAMELESS_keep`. Nothing else
  touched (no schema, no stub, no other test file).
- **Capability check:** full — lore tools loaded (keyword form), spike TEST store
  `ws://127.0.0.1:18000` up, `scratch_copy.sh` provenance-asserted. All demands satisfiable.
- **Mutation proof (the load-bearing part):** in a provenance-asserted scratch copy
  (`loremaster.__file__ = /tmp/contract-60-w1b-scratch/loremaster/loremaster/__init__.py`)
  the reference build passes **154 passed** (adversary's 152 + my 2 new pins);
  mutating `get_keep`/`list_keeps_for_keeper` to attack-9's `SELECT *` + `row["name"]`
  bracket → **both new pins RED (`KeyError: 'name'`)** while the 3 named-keep controls
  stay **GREEN**; byte-exact restore (md5 match) → **both new pins GREEN**.
- **Gates (real repo @ `b9e6335`):** `ruff check test_keeps_store.py` clean · `typecheck.sh`
  GREEN (all members, loremaster 221 files incl. the edited test) · `test_keeps_store.py` at
  STUB = **22 failed / 6 passed** (both new pins RED-by-design; was 20/6 before my 2 pins).
- **Packages considered:** none — no mechanism specified (2 test methods reusing existing
  fixtures/helpers/constants; the scratch REFERENCE build reuses the shared `_txn` seams +
  installed `surrealdb`/`ulid`, and never lands).
- **Reuse ledger:** none — no new reusable production symbols. The two pins reuse the
  file's existing `keep_env` fixture, `_KEEPER_EMAIL`, `Keep`/`KeepStore` API.
- **Graded:** N/A — this is a contract revision (a RED pin + its proof), not a verdict on
  someone's artifact. Work at `b9e6335` (HEAD-at-report `b9e6335`, SAME). Note: the adversary
  graded at `f0ebbf4`; the tree has since advanced to `b9e6335` (the D-2 `test_blocks_edge.py`
  five→six ref fix the adversary flagged as already-clean/benign — now committed).
- **Decisions needed:** none.
- **Pointers:** §The two pins · §Mutation-proof receipts · §The mutation (verbatim instrument)
  · §Discrimination self-audit · §Honest-RED-at-stub.

---

## §The two pins (what closes attack 9)

The adversary proved (attack 9) that a `get_keep`/`list_keeps_for_keeper` reading `SELECT *`
+ bracket `row["name"]` **KeyErrors on every nameless `dm` keep** (`name=None` — Fork E; the
reason `name` is `option<>`), yet passes the store suite because **no test reads a `name=None`
keep back through a Keep-returning verb INDEPENDENTLY of `create_keep`'s own return**. Store
law §2 (cited, not re-transcribed): a `SELECT *` OMITS a NONE-valued `option<>` column, so
`row["col"]` raises; an explicit projection (or `.get`) reads it back as `None`.

Both pins read through the verb (a **FRESH store read**), never `create_keep`'s return, and
each pairs the nameless assertion with a **NAMED positive control** so it is not vacuously
about a verb that always returns `name=None`:

1. **`TestGetKeep::test_get_keep_reads_back_a_NAMELESS_keep`** — create a `dm` keep (nameless)
   and a `project` keep (named); `get_keep(nameless.id)` returns `Keep(name is None)` and does
   NOT raise; `get_keep(named.id)` returns the real name (control).
2. **`TestListKeepsForKeeper::test_list_keeps_for_keeper_lists_a_NAMELESS_keep`** — a keeper
   who keeps a nameless AND a named keep; `list_keeps_for_keeper(email)` returns the nameless
   keep with `name is None` and does NOT raise; the named keep in the SAME listing carries its
   name (control). A `SELECT *`+bracket read KeyErrors on the nameless row and takes the whole
   listing down.

Both mirror the file's existing `TestGetKeep`/`TestListKeepsForKeeper` idiom exactly.

---

## §Mutation-proof receipts

Scratch is `scratch_copy.sh`-made and **provenance-asserted** (finding #140):
`loremaster.__file__ = /tmp/contract-60-w1b-scratch/loremaster/loremaster/__init__.py`
(re-printed and asserted `startswith('/tmp/contract-60-w1b-scratch')` immediately BEFORE the
mutated run, so the mutation graded the scratch tree, not the repo).

Reference build = the contract's §Satisfiability plan verbatim (schema `_keep_statements`/
`_member_of_statements`/`generate_keep_ddl`; `KeepStore` CRUD with ULID id, keeper resolved via
the composed `PrincipalStore.get_by_email`, CREATE+RELATE in ONE `execute_transaction`,
`get_keep`/`list_keeps_for_keeper` with **explicit projection + `row.get("name")`**,
`create_keep` builds its return DIRECTLY — the attack-9 shape, so mutating the read verbs
leaves `create_keep` untouched).

| step | command (in scratch, live spike `:18000`) | result |
|---|---|---|
| **SATISFIABILITY** | `pytest -n auto test_keeps_store.py test_keeps_schema.py test_enforced_relations.py` | **`154 passed in 7.82s`** — reference build passes ALL keep tests incl. my 2 new pins (152 → 154). No C-DEF. |
| **MUTATE→RED** | mutate `get_keep`/`list_keeps_for_keeper` → `SELECT *` + `row["name"]`, run the 2 new pins + 3 controls | **`2 failed, 3 passed`** — both new pins `KeyError: 'name'` at `keeps.py:394` (the mutated bracket line); `test_get_keep_reads_back_a_created_keep` (named), `test_list_keeps_for_keeper_returns_their_keeps` (named), `test_create_keep_of_type_dm_produces_a_dm_keep` all **GREEN** |
| **RESTORE→GREEN** | `cp -a` restore (md5 `131b36e8…` == ref), run the 2 new pins | **`2 passed in 0.92s`** — byte-exact restore confirmed |

The named-keep controls staying GREEN under the mutation is the discriminating fact: the
wrong build is broken **specifically** for the always-nameless `dm` type, and
`create_keep(dm)`'s own return (which the original contract's `test_create_keep_of_type_dm`
asserts on) is UNAFFECTED — which is exactly why attack 9 survived the original contract, and
exactly what these two READ-path pins now close.

---

## §The mutation (verbatim instrument — the scratch tree is disposable by design)

The reference build is large and lives only in the scratch tree (`/tmp/contract-60-w1b-scratch`,
a disposable `scratch_copy.sh` copy — NOT a git worktree; my `rm -rf` was guardrail-denied, so
the lead may reap it, 580M in `/tmp`); the MUTATION that demonstrates the pins is three one-line
edits, pasted here so the claim is re-runnable against any correct reference build:

```
# get_keep:  explicit projection  ->  SELECT *
-  f"SELECT {_KEEP_READ_PROJECTION} FROM type::record('{KEEP_TABLE}', $id)"
+  f"SELECT * FROM type::record('{KEEP_TABLE}', $id)"

# list_keeps_for_keeper:  explicit projection  ->  SELECT *
-  f"SELECT {_KEEP_READ_PROJECTION} FROM {KEEP_TABLE} WHERE keeper = type::record('{PRINCIPAL_TABLE}', $pid)"
+  f"SELECT * FROM {KEEP_TABLE} WHERE keeper = type::record('{PRINCIPAL_TABLE}', $pid)"

# _row_to_keep (shared by both):  .get(None-safe)  ->  bracket
-  name=self._optional_str(row.get("name")),
+  name=row["name"],                    # KeyError on a SELECT * nameless row (store §2)
```

Reference correct shape (what the builder must produce): explicit projection listing `name`,
and `.get("name")` (or `row["name"]` under an explicit projection — the projection makes the
key present as `None`). Any build combining `SELECT *` with bracket `row["name"]` reddens both
pins.

---

## §Discrimination self-audit — "what WRONG build still passes my new pins?"

- **A build that special-cases `create_keep`'s return but reads back wrongly** → CAUGHT. My
  pins assert on the object returned by `get_keep`/`list_keeps_for_keeper` (a fresh store
  read), never on `create_keep`'s return. Proven: under the mutation `create_keep(dm)` stayed
  GREEN while my pins went RED.
- **A build returning `name=""` (empty) instead of `None` for a nameless keep** → CAUGHT by
  `assert fetched.name is None` (`"" is not None`).
- **A build that silently DROPS the nameless keep from the list** (e.g. `except KeyError:
  continue`) → CAUGHT by `assert nameless.id in by_id`.
- **A build using `SELECT *` + `row.get("name")`** → PASSES — but this is behaviourally
  CORRECT (`name=None` round-trips), not a wrong build. No false negative.
- **`get_keep` correct but `list` wrong (or vice-versa)** → each verb has its OWN pin, so a
  one-verb regression is caught by its own pin.

The only builds that pass both pins are ones where BOTH read verbs round-trip `name=None`
faithfully — which is the property the pins exist to force.

---

## §Honest-RED-at-stub

At the shipped stub, `create_keep` raises `NotImplementedError`, so both new pins fail
BEHAVIOURALLY (an uncaught `NotImplementedError` from `create_keep`, at `keeps.py:370`) —
never an ImportError or collection error. The atomicity pins' `assert not
isinstance(caught.value, NotImplementedError)` guard is NOT needed here: those pins wrap an
EXPECTED store rejection in `pytest.raises(Exception)` (which would otherwise SWALLOW a stub's
`NotImplementedError` into a false GREEN). My pins wrap NOTHING in `pytest.raises` — they
expect a SUCCESSFUL read — so any `NotImplementedError` propagates and reddens them
correctly, exactly as the file's existing `test_get_keep_reads_back_a_created_keep` behaves at
stub. Real-repo receipt: `test_keeps_store.py` at stub = **22 failed / 6 passed**, both new
pins among the RED, none failing on ImportError/collection.

---

## §Gate receipts (real repo @ `b9e6335`)

- **`ruff check loremaster/tests/test_keeps_store.py`:** `All checks passed!`
- **`scripts/typecheck.sh`:** GREEN — `loremaster OK` (221 src files incl. the edited test),
  lorerunes/lorescribe/loresigil/skills/docs-eval/scripts all OK, shellcheck OK. (Additive test
  methods; no new types — the brief's "expect still GREEN" holds.)
- **`pytest -n auto test_keeps_store.py` at STUB:** `22 failed, 6 passed` (RED-by-design; both
  new pins RED behaviourally via `create_keep`'s `NotImplementedError`).
- **Scratch (reference build, `:18000`):** satisfiability `154 passed`; mutate `2 failed, 3
  passed` (KeyError on both new pins, controls green); restore `2 passed` (md5-exact).

## §HANDOFF
Task `39f036a684de453e914b37625655e7bb` → done. One-shot: I retire and exit. A focused
adversary re-pass follows; once these two nameless-keep read-back pins are confirmed I expect
the contract SUFFICIENT (the adversary's own closing line: "Once the nameless-keep read-back
pin lands, I expect this contract to be SUFFICIENT"). The lead commits the full contract with
the build once green — I do NOT commit.
