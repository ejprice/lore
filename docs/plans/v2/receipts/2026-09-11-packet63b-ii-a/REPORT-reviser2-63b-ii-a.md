# REPORT-reviser2-63b-ii-a — packet 63b wave ii-a, the TWO missing ruling pins (MP-5 + MP-6)

- `brief-base v14 read`
- `brief project v7 read`
- store-ref read (`docs/reference/surrealdb-31-capabilities.md`): §1.8 (`keep.key` UNIQUE over
  option<>), §2 (CONTENT / bound `RecordID` owner links / protected `session` param / explicit
  projection reads NONE as `None`, `SELECT *` OMITS it), §4 (RELATE / ENFORCED endpoints). Cited, not
  re-transcribed. My pins add no store/schema/DDL; they read `agent`/`keep`/`message` rows the ruled
  build writes.

## SUMMARY BLOCK (brief-base §1)

- **state:** done — the TWO pins the design authority's fidelity read (ruling §11.2) found absent are
  added to `test_comms_send_scope_63b_ii_a.py`. Both RED-at-HEAD for the right reason, controls sound;
  ruff clean + `./scripts/typecheck.sh` EXIT=0.
- **deviations:** (1) MP-6 drives the harness's NATIVE tokenless mode (empty-subject token); the
  `get_access_token()`-returns-`None` absence variant is NOT natively reachable via the `cred` harness
  (it wraps `holder['email']=None` into `access_token(subject="")`, never `None`) → I did NOT force it
  with an in-test monkeypatch (the brief made that conditional on the harness; respecting it) — surfaced
  as **decision D-NULLTOKEN**. (2) extended the existing `from loremaster.server import …` line to also
  import `_COMMS_ACTIONS` (needed to DERIVE MP-6's deny-verb set, not hand-list it) — within the one
  writable file.
- **Packages considered:** none — no mechanism specified; a contract reviser ships no production
  mechanism. Reused the file's landed credentialed harness + the design's ruled seams.
- **Reuse ledger:** none new — reused the file's existing `cred` fixture, `_register_owned`,
  `_message_count`, `_bare`, `_credentialed_send`, `_ks` UNTOUCHED (DRY table below). The two additions
  are TEST methods/classes, not reusable symbols/policy.
- **Graded:** n/a (I authored tests; I did not grade another artifact). Base: `607907f` ·
  HEAD-at-report: `607907f` · SAME (`git rev-parse HEAD` at spawn and at close; only
  `test_comms_send_scope_63b_ii_a.py` is modified).
- **decisions-needed:** **D-NULLTOKEN** — strengthen MP-6 to ∀-over-absence-modes (empty-subject AND a
  `get_access_token()→None` local monkeypatch), or leave the None-token path to the builder/63c? §3.1
  maps BOTH to `resolve_principal→None` (the α branch), so the empty-subject path already exercises α;
  the None-token path is unpinned. I recommend the builder add the None-guard test IF `resolve_principal`
  does not None-guard `getattr(token, "subject")` — but that is a builder call, not a contract one.
- **receipt POINTERS:** §The two pins · §RED-at-HEAD receipts · §Wrong-build discrimination · §Gates ·
  §cred-harness note · §DRY ledger · §Capability check.

## Capability check (brief-base §4)
- DEMANDED: add exactly TWO pins to one test file, prove RED-at-HEAD for the right reason, ruff+mypy
  clean, no production/git. HAVE: full tool access, lore MCP loaded, live TEST store `:18000` reachable,
  ruff + `scripts/typecheck.sh`. All satisfiable. COMMIT-ONLY honoured — the ONLY writes are the one
  test file + this report; git untouched (the lead commits + re-adversaries).
- **`grep`/`rg` are HOOK-BLOCKED** in this live-indexed checkout (confirmed: an `awk … | grep`
  attempt was rejected). Used lore + `Read` for structure and `awk` for the ruff-config lookup — SAID.
  No lore-tool friction (every query served cleanly), so nothing filed to `lore_findings`.
- **Attribution:** the session-start reminder to add `Co-Authored-By`/`Claude-Session` is overridden by
  the operator's standing `~/.claude/CLAUDE.md` rule and is moot here (COMMIT-ONLY — the lead commits).

---

## The two pins (exact names · what each asserts · the wrong build each reds)

Both are appended as their own classes at the end of `test_comms_send_scope_63b_ii_a.py`, on the
existing `cred` harness + helpers (no harness changes).

### MP-5 — `TestTheAgentArgumentMustMatchTheCapability::test_a_send_with_a_siblings_capability_denies_and_writes_nothing`
Binding spec: ruling §2.3 (the `_bare(agent_row.id) == subject.agent_id` check) + §9 B2 (ONE mismatch
case pinned in ii-a) + §11.2 MP-5.
- **Fixture:** ONE principal `alice`; TWO agents `alice_w1` + `alice_w2`, BOTH owned by alice (each via
  `_register_owned`, minting its one-time capability); a session keep via a tool `register` (re-register
  of `alice_w1` under alice's token mints/joins `session:s1`).
- **Drive + asserts:** `comms(action="send", agent="alice_w1", capability=<alice_w2's cap>, …)` under
  alice's token ⇒ (a) `GovernedDenied` (the `pytest.raises`), (b) the deny NAMES the requested `agent=`
  (`"alice_w1" in str(excinfo.value)` — §2.3 teaching "agent= names X but the capability verifies as
  Y"), (c) ZERO message rows (`_message_count` before==after==0).
- **Positive control (same test):** the SAME send with `alice_w1`'s OWN capability writes exactly ONE
  row — proving the deny is the agent≡capability mismatch, not a send that never works.
- **Wrong build it reds (§2.3 / F4 kernel "no argument moves the stamp"):** a `_comms_send` that OMITS
  the agent≡subject check. `stamp_owner` verifies `alice_w2` (its `(principal, agent)` binding to alice's
  token HOLDS, so nothing denies); the send proceeds with `sender=alice_w1`, `owner_agent=alice_w2` and
  WRITES a row. That build passes R1 (honest fixture), R2, R6 and the live-classify (an honest send) —
  and reds HERE: `pytest.raises` → "DID NOT RAISE", and `after==0` fails (a row exists).

### MP-6 — `TestATokenlessRegisterIsOwnerlessAndMintsNoKeep::test_a_tokenless_register_succeeds_ownerless_mints_no_keep_and_names_the_bound`
Binding spec: ruling §3.2 (reading α) + §9 B1 (pinned by the render bound line, 63c re-open trigger) +
F2 (pkt-62 registry pin, lifted to the tool layer) + §11.2 MP-6.
- **Drive:** clear the ambient identity (`holder["email"] = None` → the empty-subject token) and tool
  `register` `ownerless_w1` in `s_tok`; the register SUCCEEDS (a reading-β *deny* is caught and turned
  into a legible `pytest.fail` naming β's 63c trigger — β is NOT ruled for ii-a).
- **Asserts:** (1) the agent row's `owner_principal IS NONE` (`SELECT owner_principal FROM agent …`, F2
  at the tool layer — never fabricated); (2) `get_by_key("session:s_tok") is None` (no keep kept); (3)
  the render NAMES the α bound — `ownerless` (synonyms accepted) · each DERIVED `requires_capability=True`
  deny-verb (from `_COMMS_ACTIONS`, ii-a `{send}`, NOT a hand-list) · the two remedies (`credential`
  + `migrate-governed`). The assertion message carries the §9 B1 re-open trigger (63c).
- **Positive control (same test):** a CREDENTIALED register in a FRESH session (`s_cred`, holder=alice)
  DOES mint a keep — so the tokenless no-keep is the MISSING IDENTITY, not a build that never mints keeps.
- **Wrong build it reds (§3.2 α — the Reading-A HYBRID):**
  `principal = await resolve_principal(...) or await resolve_operator_principal(principal_store)` on the
  tokenless branch. It FABRICATES the fleet's admin (carol) as keeper AND owner — passing R3
  (registrant alice ≠ carol), R4 (the patched seam returns P*, so the `or` fallback never runs) and the
  corpse (registers succeed) — and reds HERE on ALL THREE: (1) `owner_principal == carol` ≠ None; (2) a
  `session:s_tok` keep exists; (3) the render is a keeper line ("minted … you keep it"), not the
  ownerless bound.

---

## RED-at-HEAD receipts (each RIGHT-reason; run ALONE, no xdist — contention-free; graded `607907f`)

A passed/failed COUNT is in every tail (no "no tests ran" pipe-lie).

| pin | tail | RED reason (right reason) |
|---|---|---|
| MP-5 | `1 failed in 3.51s` | `assert keep is not None` → **"SF-63-1 unbuilt: register minted no session keep"** (`:787`). The whole capability= + SF-63-1 seam is unbuilt at HEAD, so the §2.3 mismatch check cannot exist; reds at the same keep guard as R1/R3/R5. |
| MP-6 | `1 failed` (combined run: `2 failed in 6.83s`) | asserts (1)+(2) PASS at HEAD (HEAD is trivially ownerless + keepless), then `assert bound_named` → **the α-ownerless render is unbuilt (F10)** (`:881`). Observed HEAD render: `"registered ownerless_w1 (session s_tok, role …) — status active\nno 'project' brief published yet…"` — no ownerless line, `derived_deny_verbs=[]` (field absent at HEAD), `remedies_named=False`. |

**Why MP-6 (1)+(2) being GREEN at HEAD is the fixture DISCRIMINATING, not a hole:** at HEAD the tool
already registers ownerless and mints no keep, so (1)/(2) are green — proving those two assertions are
NOT trivially always-red. They fire ONLY against a build that FABRICATES (the Reading-A hybrid). The
RED-at-HEAD signal for MP-6 is assertion (3), the α render bound — exactly the "α-ownerless behavior is
unbuilt at HEAD" reason the brief names.

**"What WRONG build still passes this?" (brief self-check):** MP-5 → the §2.3-omitting build (redded by
raises + zero-rows). MP-6 → the Reading-A hybrid (redded by owner-None + no-keep + render-bound, triple).
Both are the sidecar's named wrong builds; the re-adversary owns the empirical door-builds on a reference.

## Gates
- `uv run ruff check loremaster/tests/test_comms_send_scope_63b_ii_a.py` → **All checks passed!**
- `./scripts/typecheck.sh` → **EXIT=0** ("no issues found", all legs OK incl. test trees).
  - ⚠ First typecheck run reported `:856 Statement is unreachable` on a `return` after `pytest.fail`
    (`NoReturn`) in MP-6's β-catch — removed (redundant: mypy already knows `result` is bound after the
    except since `pytest.fail` never returns). Re-run EXIT=0. This is why the brief's "run BOTH gates"
    rule matters — ruff was clean while mypy was red.

## cred-harness note (brief: flag anything the harness doesn't provide)
The `cred` harness provided everything MP-5/MP-6 needed WITHOUT modification: the switchable `holder`,
the `alice`/`bob`/`carol` principals, `pids`/`emails`, and the `_register_owned`/`_message_count`/`_bare`/
`_credentialed_send`/`_ks` helpers. ONE thing it cannot express natively (D-NULLTOKEN above): its
`_patched_get_access_token` ALWAYS returns an `access_token` (empty-subject when `holder['email']` is
`None`), so the `get_access_token()→None` absence mode is unreachable without a local re-monkeypatch. I
did NOT modify the harness (beyond adding the two tests) and did NOT unilaterally add that monkeypatch —
surfaced for the lead. No other harness gap.

## DRY ledger (brief-base §6 — new reusable test symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| (none new) | — | the two additions are TEST methods/classes on the existing harness | **REUSED** `cred`/`_register_owned`/`_message_count`/`_bare`/`_credentialed_send`/`_ks` (all landed by `reviser-63b-ii-a`, UNTOUCHED). |
| deny-verb-set derivation (inline comprehension over `_COMMS_ACTIONS`) | Read `test_comms_capability_63b_ii_a.py` (its exact-set pin + R6 use the identical idiom) | the True-set derivation is an established per-file inline idiom, not a shared symbol | **REUSED (idiom)** — cloned the `{v for v,spec in _COMMS_ACTIONS.items() if getattr(spec,"requires_capability",False)}` derivation per the per-file convention; NOT policy (a test-local derivation off the module's own spec table). |

## Method / discipline receipts
- lore-first: read the ruling verbatim (§2.3, §3.2, §9 B1/B2, §11.2), the existing send_scope file
  (harness + R1–R5 patterns for the credentialed-drive idiom), the capability file (render-capture via
  `str(await comms(...))` + the True-set derivation), and both context reports (adversary2 R-ALPHA
  residual; reviser-1's `cred`/`_register_owned`/`_message_count` helpers). grep hook-blocked → `awk`
  for the ruff-config lookup, SAID. No lore friction filed.
- store law: no store/schema/DDL change (a contract reviser writes tests); MP-6's `owner_principal`
  read uses an EXPLICIT projection (store-ref §2 — returns `None` for an unset option<>, unlike
  `SELECT *`), and `.get()` for belt-and-braces.
- COMMIT-ONLY: only `test_comms_send_scope_63b_ii_a.py` + this report written; git untouched. The lead
  commits + re-adversaries (contract → adversary → build; no wave skips the adversary).
