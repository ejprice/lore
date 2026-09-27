brief-base v17 read · brief project v7 read

# REPORT — adversary-58-r3 (contract-adversary, NARROW DELTA: packet 58 contract r3 @ `7130508`)

## SUMMARY BLOCK
- `brief-base v17 read` · `brief project v7 read` · **State: done-with-deviations** — D-MEM: host RAM pressure from other sessions; the 15 GB tree watchdog killed 3 runs, each re-run clean at `-n 2` (R-11) · D-SPEC: am-11 (`0ed6705`) landed mid-run and was relayed (#17103) — graded as §AM11 fold items.
- **VERDICT: CONTRACT INSUFFICIENT** — MISSING PIN ×9 (F-A HIGH · F-B HIGH · F-NOOP MED-HIGH · F-D · F-E · F-G · F-C (DUAL) · F-F · F-H) of which NEW DOOR ×2 (F-A: 12 exhaustion-catching production sites invisible at HEAD; F-B: #102 through a wrapper) · SAT DEFECT ×0 · §AM11 fold items ×5 · the rest NOT A DEFECT (§RESIDUALS).
- **P1 headline — YES, 7 wrong builds pass the whole contract (0 reds beyond the reference's 8 owned-elsewhere reds over 1466+ tests):** W-TUPLE (a tuple-constant swallow serving success) · W-IMPLICIT and W-REBIND (#102's lost-race verdict for exhaustion, through `resolve`/`wontfix`) · W-NOOP-DRIVERS (no-op owner drivers turn SEAM fully green) · W-HEAL2 (heal chunk ≥ 2 swallows exhaustion) · W-F4-PREFIX (half-heals + counts a row whose bad entry is not first) · W-F3-ROOT (claim-loss WARNINGs on the root logger). Two more die only by ACCIDENT: W-PACK-OBO (only the hand probe PC, 49 rows past its threshold — §P2) and W-RETRY-RERAISE (a control-leg fixture reuse). Every one has a kill probe GREEN on my reference and RED on the build.
- **⚠ 4th instance of a routed property (am-8 §7):** F-B is the CAS-population property's 4th instance (r1 `_select*` → r2 `try` shape → r2/r3 `self._apply` shape → r3 wrapper catch reached by neither the MINIMAL-verb runtime ∀ nor the exit-SHAPE static rule) ⇒ **re-open am-9 FK-r3-5 (+ its §5 rider), not the contract.** F-E (heal convergence) is NOT a 4th instance — its build dies on the committed bytes — but the ruled scale ingredient (am-8 §2 `{fit−1, fit, fit+1}`) is what leaves it to a hand fixture: a sidecar item.
- **Predecessor kill table: 16/16 KILLED on the committed bytes** (N1–N5, F4b, N17, N19, N19b, W6a–d, N20, F6, F7); r2's two SAT shapes (F5 `suppress`, F8 extract-method) are now 0 new reds — closed. **§AST re-run: 12 EQUAL + 1 ruled re-key over 13 functions** (the author's "13 of 14" is a miscount; controls OK). **RED@HEAD reproduced: 80 of 108**, right reasons.
- **SAT (my OWN am-7/8/9 reference, independent of the author's `my_ref_r3.py`): full suite `339 failed, 12145 passed, 63 skipped, 3 xfailed`; HEAD baseline over the 15 red files `351 failed, 1690 passed`; shared 335 · fixed 16 · SAT-only 4 = a28b's class-DERIVED keeps pin extended by 58's four new classes (63c-i-a's unbuilt narrowing) ⇒ 0 attributable to 58.** §HELD `git apply --check` part 1/3/2 OK on `224c74e` and on the shared WIP tree; collisions: a28c's per-handler scanner re-key (certain, on `_discover_cas_handlers`) and 64b r2's discovered-driver module (F-NOOP's live instance).
- **Quantifier table (§P1b):** 16 invariants — 7 GUARDED with a surviving door (Q1 scale, Q2 position, Q5 logger name, Q10 minimal/first-write/in-file, Q11 declaration, Q12 spelling + exit shape, Q13 substrings), the rest ∀ with the door-build killed, or construction-inspected bounds (Q6, Q14–Q16). **Reach table (§P1c):** 10 instruments — 7 MISSING PIN rows (resolver fails OPEN, exit-shape hand-list, evidence substrings, one-write injection, declared-not-run coverage, CONV scale/position, RU logger-name filter), all with empirical legs; TIERS drop-one legs ARE the one-table mutation proof (W6b killed).
- **Packages considered:** `more_itertools.constrained_batches` 11.1.0 (installed source READ: greedy close, strict `ValueError`, and a lazy GENERATOR — BC-r3-1's materialise rider is load-bearing) → replace (agree) · `networkx` 3.6.1 `ancestors` for the closure → keep (trivial) · `ast`/`astroid` 4.1.2 for the catch walker → bespoke (agree; the defect is a missing flatten, not a missing library) · `pytest-timeout` → replace (ruled, not installed) — **P-PKG diff: 0 misses.**
- **Odoo-20 portability:** n/a — no Odoo seam touched (my enumeration: 0; author: n/a).
- **Reuse ledger:** none — no production symbol; scratch references + test instruments only (pasted §INSTRUMENTS).
- **Graded: `7130508` · HEAD-at-report: `6bb95af` · DIFFERENT (22 ahead, docs only** — `git diff --stat 7130508 6bb95af -- loremaster lorerunes lorescribe loresigil scripts pyproject.toml uv.lock` is empty; spec moved: 58 am-11 graded as fold items; 63c am-35/36 forecast as collisions, R-13).
- **Decisions needed:** (1) sidecar: re-open am-9 FK-r3-5 — drive every caller that adds its own catch (Reading B, at the STATE) vs allowlist-the-safe PASSTHROUGH (F-B) · (2) sidecar: widen am-8 §2's scale ingredient to `2·fit+1` (F-E) · (3) lease owner: `create/update/release_if_held` serve "did not win" for exhaustion (R-3) · (4) lead: do not route FK-r3-4's drivers until F-NOOP's pin exists (a no-op driver greens them) · (5) lead: a28b's red door pins mask new doors until 63c-i-a's build (R-5).
- **Loop cost (CLAUDE.md Fix-the-CLASS rule 5):** 58 contract at round 3 → an r4 is needed; this grade ≈ 3.5 h wall-clock (23:30 → 03:00), ~45 harness runs (32 builds incl. controls and P2 legs, 3 watchdog-killed attempts, probes, RED@HEAD, SAT, baseline), dominated by host-RAM waits.
- **Receipts:** §REF · §AST · §P-PKG · §A (F-A … F-H, §AM11) · MISSING PINS · §PRIOR · §P2 · §P7 · §DUAL · §HELD · §P1b · §P1c · §SAT · §RESIDUALS · §INSTRUMENTS.

## §0 Capability check / setup (2026-09-26/27)
- Idle-gate contract written: `/tmp/claude-idle-gate-lore/297217bd-cb03-409c-ac95-0eb7ca9bf74b-adversary-58-r3.contract` = `{"artifact": "REPORT-adversary-58-r3.md"}`.
- lore: `ToolSearch "+lore"` loaded 15 tools; registered `adversary-58-r3` (session `63c-20260924`, role adversary, cadence ≤20m).
- grep/rg are hook-blocked (#473): every textual sweep here is `awk`/`sed` or a Python `ast` walk — a fallback, said out loud. `scripts/` is outside lore's graph (#507).
- Required first read: `docs/reference/surrealdb-31-capabilities.md` (header, §3 incl. #497/#501).
- Scratch trees via `./scripts/scratch_copy.sh` only (provenance printed, below). No worktrees, no `git stash`, no tracked file edited.
- Nothing the brief demands is out of reach. The brief's "commit ONLY your report" overrides brief-base §2's "never commit" (spawn brief > base; not a role-boundary transfer).

## §REF — MY independent reference of am-7 / am-8 / am-9 (2026-09-27)
- **Tree `scratch/ref`** (`scratch_copy.sh` copy; `loremaster.__file__ = …/scratchpad/ref/loremaster/loremaster/__init__.py`) = HEAD `7294b3f` (code = `7130508`) + §HELD part 1 (`dbba9753`, from `5a43aeb:REPORT-contract-58.md` 173–557) + part 3 (`15f38e31`, from `c42eeaf:REPORT-contract-58-r2.md` 177–195) + **part 2 (`986f87df`, extracted from `7130508:REPORT-contract-58-r3.md` §HELD — md5 = the recorded value)** + adversary-58-r2's ref6 (`build_ref58.py 5915c12e` + `my_ref.py de2d2801` + `my_ref_am6.py 2176fb8e`, each md5-verified; result `tasks.py 12917da9` · `_txn.py 8c748e4f` · `findings.py 48d8fd7a` = the recorded values, byte-exact) + **my own am-7/am-8/am-9 deltas `my_ref_r3a.py` (md5 `e6b135c5`, pasted §INSTRUMENTS), written WITHOUT reading contract-58-r3's `my_ref_r3.py`** → `tasks.py 1d1e5acf` · `_txn.py b8da2092`.
- My deltas: three typed 58 classes in `_txn` produced by the ONE classifier from their markers; `_ROLLBACK_LOG_TIERS` keyed by CLASS; `_log_rollback` receives the classified class (exhaustion/unknown → ERROR); the packer IS `constrained_batches(built, cap, get_len=weight, strict=True)`, materialised into a list before any apply, `ValueError` → `StragglerHealPackerError` naming row + weight; F4: `break` → `continue` so every unresolvable ENTRY warns and the row is skipped whole.
- **The 58 scope on it** (`scope58.txt`: the 16 `packet-58-contract` files + `test_retry_seam` + `test_exhaustion_fates` + `test_supersede_render_58` + `test_surreal_store`), `-n 4`, 15 GB tree watchdog: **`8 failed, 1457 passed, 1 skipped, 1 warning in 427.20s`**. The 8 are EXACTLY the author's 8 owned-elsewhere reds (§SAT): `SEAM` ×3 (FK-r3-4 rows `agents.py::register`, `floor_calibration/store.py::record_measurement`, `keeps.py::get_or_create_keyed`) · `TIERS` ×3 (`TxnUniqueViolationError` — 63c-i-a's am-33 class does not exist) · `RS` ×2 (a28b's own door/typed enumerations). **Two independently written references now satisfy r3's 58-owned pins with zero attributable reds.**
- **P0 positive control for my probes** (`test_adv58r3_probes.py`, pasted §INSTRUMENTS) on this reference: `4 failed, 13 passed in 51.93s` — every RUNTIME probe (Q-SCALE, Q-WRAP ×3, Q-HEAL2, Q-DRIVEN ×7) GREEN on a correct build; the 4 reds are the classifier-UNIT probes (Q-EXIT, Q-REBIND, Q-TUPLE ×2), which red against the contract's own instrument regardless of build — that is the defect they name (their in-file CONTROL `test_CONTROL_a_logged_reraise_is_still_a_passthrough` is GREEN, so the harness sees a passthrough when there is one).

## §AST — the 13 landed probes re-run on the COMMITTED blobs, with controls (2026-09-27)
- Instrument: contract-58-r2's `ast_receipt.py`, extracted from `c42eeaf:REPORT-contract-58-r2.md` §INSTRUMENTS, md5 `880d05f7` (= recorded). Adversary files from `821be62` §INSTRUMENTS (md5s = recorded). Landed files from `git show 7130508:…`, never the working tree.
```
EQUAL     r3p.py::_levels / test_PA1_… / test_PA2_… / test_PB_… / test_PC_… / test_PD1_… / test_PD2_… / test_PE_…   (8)
EQUAL     r3a6.py::_rollback_levels / test_P6_each_ruled_tier_and_the_deny_by_default / test_P6_E11_… / test_P6_E11_through_the_boot_heal   (4)
DIFFERENT r3a6.py::test_P6_mutation_dropping_ONE_table_entry_moves_ONLY_that_tier
controls OK: re-wrap EQUAL (_levels); one-token mutation DIFFERENT (test_PA1_…)                 [probes]
controls OK: re-wrap EQUAL (test_PE_…); one-token mutation DIFFERENT (test_PE_…)                 [probes_e]
controls OK: re-wrap EQUAL (_rollback_levels); one-token mutation DIFFERENT (test_P6_each_…)     [am6]
```
- My own second comparator (an `ast.unparse` round-trip, independent of `ast.dump`): `equal 12 different 1` — the same one. Its whole diff is ONE line: `table.pop('cas_lost:')` → `table.pop(getattr(_txn, 'TxnCasLostError'))` — exactly D-AM7KEY (am-7 §4's class key).
- **Verdict: CONFIRMED in substance, MISCOUNTED in prose (P4, LOW).** The instrument compares **13** functions, not 14: **12 EQUAL + 1 ruled re-key**. The author's report says *"13 of 14 landed AST-EQUAL"* (summary block and §AST) and the brief repeats *"13/14 EQUAL"*; both lists the author pasted contain 13 lines. No function is missing — the count is simply wrong. (A count restated beside a claim rather than derived from the run: CLAUDE.md "scaffolding that can lie".)

## §P-PKG — my own package table FIRST, then the diff against the author's (2026-09-27)
**Mine (built before re-reading the author's §Packages considered):**
| mechanism the contract specifies or relies on | library | what I READ | verdict |
|---|---|---|---|
| heal packer (BC-r3-1) | `more_itertools.constrained_batches` 11.1.0 | the INSTALLED source (`inspect.getsource`): signature `(iterable, max_size, max_count=None, get_len=len, strict=True)`; `reached_size = item_len + batch_size > max_size` → yield then append; `strict and item_len > max_size` → `ValueError`. **It is a GENERATOR** — a builder who iterates it and applies each batch as it is yielded changes the store before a later monster row raises, so BC-r3-1's "MATERIALIZED before any apply" is load-bearing (my N19b builds exactly that; §PRIOR). My reference uses it; the r3 scope is green on it. | **replace** (agree) |
| call-graph reachability (`_reanchor_58_support.cas_verbs_in::_closure`) | `networkx` 3.6.1 (installed, already a production dependency of `tasks.py`) | `inspect.signature(networkx.descendants)` = `(G, source, *, backend=None, **backend_kwargs)`; `nx.ancestors` is the reverse | a 6-line fixpoint over a dict is what `nx.ancestors` does; the graph CONSTRUCTION (name-keyed, seam by identity) is bespoke either way → **keep** (test instrument, trivial), not a finding |
| catch-site walk, caught-class resolution, handler exit analysis (`_catch_sites`, `derived_fate`) | stdlib `ast`; `astroid` 4.1.2 installed (inference); `libcst` NOT installed | `astroid` can infer a Name bound to a module-level Tuple of classes to the tuple's ClassDefs — i.e. the exact case the resolver misses (§A F-A) — but the resolver already imports the module and `eval`s the expression, which ALSO yields the tuple; the gap is that the code does not FLATTEN it, not a missing library. No installed package computes "every exit of an except-handler, including exceptions raised by awaited calls". | **bespoke** (agree), with the §A F-A/F-B fixes |
| driver-seam injection / frame attribution | stdlib `sys._getframe` / `inspect`, the `_sdk_guard` idiom | read `DriverSeamInjection` | **keep** (agree) |
| per-test timeout (BC-r3-8, am-9 F-r3-3) | `pytest-timeout` — NOT installed at HEAD | ruled; not in this commit by design (an unregistered `timeout` mark is a no-op) | **replace** (agree; the builder/lead's) |
**Diff against the author's line:** identical verdicts on every row both tables share. The author's table omits the `ast`/`astroid` row for the catch-site walker (it names `ast` generically under "everything else"). **No P-PKG finding.**

## §P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` (my enumeration: 0 Odoo seams in the r3 files or fixtures; the author's line says the same).

## §HEAD-MOVED (derived 2026-09-27)
- `Graded: 7130508`; my trees were built on HEAD `7294b3f` (docs-only past `7130508`). During the run HEAD moved to **`224c74e`**: `0ed6705` **packet-58 amendment 11** + `224c74e` sidecar entry — **docs only** (`git diff --stat 7294b3f 224c74e -- loremaster lorerunes lorescribe loresigil scripts pyproject.toml uv.lock` is empty). No byte my verdict rests on moved.
- **am-11 RULES the "pending, don't grade" item** (am-10 §2 vs §4) — §2 governs, the OPPOSITE of the author's D-AM10 pick — and names five pins "inverted (for adversary-58-r3)". I record them in §A as SPEC-MOVED rows (F-SPEC11); they are not defects of r3 as written against am-10, and they are not optional for r4.

## §A — MISSING PINS / NEW DOORS / SAT (each: class · CLASS / SIBLINGS · the test that should exist · receipt VERBATIM)
Instruments: `wb3.py` + `builds3.py` (wrong-build driver, declare-then-diff; every anchor exactly-once, every edited file asserted CHANGED, tree restored + md5-verified after every run, including a failed one) over `scratch/wb` (a `scratch_copy.sh` copy of `scratch/ref`; `loremaster.__file__ = …/scratchpad/wb/loremaster/loremaster/__init__.py`, asserted by the driver before any build), and `test_adv58r3_probes.py` (the kill probes); all pasted §INSTRUMENTS. **"SURVIVES" = ZERO contract reds beyond the reference's 8 owned-elsewhere reds (`baseline_reds.txt`, from §REF's run) while the named probe is RED.** Scope for a survival claim = the whole `scope58.txt` (1466+ tests) + the probe file.

### F-A — NEW DOOR / MISSING PIN (HIGH): the fate classifier's DOMAIN silently drops every handler that names a TUPLE CONSTANT — 12 exhaustion-catching production sites are invisible at HEAD, and a new silent swallow spelled that way survives the whole contract
- **CLASS:** am-10 §2 DOMAIN (Reading (i), *"closure ∋ exhaustion, whatever the spelling"*) — ∀ catch sites, the caught set is what PYTHON catches: a class, or a (nested) tuple of classes, a starred element splicing a tuple. Source of truth = the handler expression evaluated in its module. `_catch_sites.caught_classes` evaluates each element and keeps it only `if inspect.isclass(value)` — a Name bound to a TUPLE (`except _CONNECTION_ERRORS:`, `except _LOCK_CALL_ERRORS as error:`) resolves to a tuple, is discarded, the site's `caught == ()`, and it falls OUT of the domain with no signal. The shared resolver is also §HELD part 2's (test_retry_seam imports it), so the a28b guarded-CAS index is blind the same way.
- **Measured at HEAD** (`reach_probe.py` / `tuple_probe.py`, pasted §INSTRUMENTS; `loremaster.__file__` = the main checkout, HEAD `7294b3f`): `sites total: 237` · **`(1) UNRESOLVED handler types: 63`** (51 × `_CONNECTION_ERRORS` / `_SDK_AWAIT_BOUNDARY_ERRORS[_WITH_CONTENTION]` / `_LOCK_CALL_ERRORS` tuple constants; `OwnerStampError` / `KeepStoreError` in `governed.py::resolve_subject`, `GovernedDenied` in `search.py::_recall_memory`, `GetSymbolError` / `StoreReadError` in `server.py` — names not bound at module level) · `(1b) PARTIALLY resolved tuples: 5` (a starred `*_CONNECTION_ERRORS` element is dropped) · **`invisible exhaustion-catching sites: 12`**, each individually:
  | site | body (what exhaustion becomes) | provisional fate (owner rules) |
  |---|---|---|
  | `inbox_awaiter.py::await_inbox:165` | `connection = None …` → falls through to the poll loop (best-effort LIVE, documented) | named-isolation (the drain is authoritative) — needs a ROW |
  | `inbox_awaiter.py::_establish_live:241` | `return (None, None)` | lifecycle — needs a row (no log: a HOLE) |
  | `inbox_awaiter.py::_consume_live:268` | bare `return` | lifecycle — HOLE |
  | `inbox_awaiter.py::_safe_kill:308` | `pass` | close-path — HOLE |
  | `scout.py::run:486` | `logger.debug(…connect_failed, exc_info=True)`; backoff; `continue` | lifecycle at DEBUG — HOLE (am-10 §1's shape) |
  | `scout.py::run:495` | `logger.debug(…socket_dropped…)`; drop; backoff | lifecycle at DEBUG — HOLE |
  | `scout.py::_consume_live:584` | `logger.debug(…live_unavailable…)` | lifecycle at DEBUG — HOLE |
  | `scout.py::_safe_kill:612` | `logger.debug(…already_closed)` | close-path — HOLE |
  | `store/lease.py::get:645` | WARNING + `return (False, _lock_unavailable(…))` | named-isolation-served — row |
  | `store/lease.py::create:675` | WARNING + `return False` — "this tick did not win" | ⚠ a lost-race VERDICT shape served for exhaustion (fail-safe for leadership: not claiming it) — owner ruling |
  | `store/lease.py::update:710` | WARNING + `return False` (the CAS: "did not win") | ⚠ same — owner ruling |
  | `store/lease.py::release_if_held:765` | WARNING + `return False` | ⚠ same — owner ruling |
  ⇒ **the §FATES census is short**: *"74 domain sites"* is at least **86**; `REGISTERED_FATES` is not "exact both ways" over the ruled domain; `UNLOGGED_SITES` misses ≥ 7 holes; and three lease sites serve a lost-race verdict for exhaustion without ANY instrument ever asking.
- **Wrong build W-TUPLE** (`builds3.py`): `findings.py` gains `_RESOLVE_TOLERATED = (SurrealStoreError,)` and `resolve` becomes `try: return await self._transition(…) except _RESOLVE_TOLERATED: return await self.get(id_or_number)` — exhausted contention SERVED AS A SUCCESS (the current row). **Receipt:** `W-TUPLE_resolve_swallows_via_a_tuple_constant_and_serves_the_row · 13 failed, 1469 passed, 1 skipped, 1 warning in 479.21s (0:07:59) · NEW contract reds (beyond the 8 baseline): 0 [] · probe reds: [Q-EXIT, Q-REBIND, Q-TUPLE ×2, TestQWrapExhaustionThroughAWrapper::…[resolve]]` → **SURVIVES**.
- **P0 control W-TUPLE-c** (the SAME swallow, spelled `except (SurrealStoreError,):`): `KILLED as declared · 1 failed, 15 passed in 4.85s · red: test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_non_derived_site_has_a_row_and_every_row_a_site` — the classifier sees the literal spelling and not the constant: the defect is the spelling key, nothing else.
- **The test that should exist:** `TestQTupleDomain` (pasted): (1) every production handler's `except` expression, evaluated in its module and FLATTENED (nested tuples, starred elements), resolves to classes only — an unresolvable one is RED by name, never a silent drop — and equals `site.caught`; (2) every site whose flattened set can catch `TxnContentionExhaustedError` (unshielded) is `in_domain`. RED at HEAD (63 unresolved / 12 invisible), by construction GREEN once `caught_classes` flattens and fails closed. The 12 then need rows (their owners'), which is the point.
- **SIBLINGS TRIED:** tuple constant (12 real sites); starred tuple element (5 real partial sites); function-local / unbound names (5 real sites, none exhaustion-catching today); the same blind spot in test_retry_seam's guarded-CAS index via the shared resolver (construction: §HELD part 2 imports `_catch_sites.caught_classes`). **SIBLINGS NOT TRIED:** a class-valued ATTRIBUTE of an instance (`except self._errors:`); exception groups caught via `except*` with a tuple constant (the walker handles `TryStar`, the resolver flaw is the same); swallowing FORMS with no catch site at all (`asyncio.gather(…, return_exceptions=True)`, an `__exit__` returning truthy, `return` in `finally`) — measured **0** in production today (`reach_probe.py` (2a)–(2c)), so a bound to PIN, not a live door.

### F-B — NEW DOOR / MISSING PIN (HIGH) — ⚠ a 4th INSTANCE of the routed CAS-population property (am-8 §7 → re-opens the RULING, am-9 FK-r3-5 + §5 rider): #102's own lie through a WRAPPER — the fate classifier derives it PASSTHROUGH, the runtime ∀ never drives it
- **CLASS:** *∀ handlers that exhausted contention can reach, on EVERY path out of the handler, the caller receives the exhaustion (or a fault) — never a verdict.* am-9 FK-r3-5 ruled the runtime ∀ drives MINIMAL verbs only, and its §5 rider hands every WRAPPER above them to *"the whole-tree swallow rule"* — now am-10's fate classifier. That classifier's `derived_fate` grants PASSTHROUGH when the handler's LAST statement is a `raise` and every exit STATEMENT (`Raise`/`Return`/`Continue`/`Break`, `_exits`) is an unchanged re-raise. Two paths out of a handler are not exit statements, and `_exits` cannot see them: **(i) an exception raised by an AWAITED CALL in the handler body** (the re-read helper that raises the verdict), and **(ii) `raise <name>` after the caught name was REBOUND** (`error = IllegalTransitionError(…); raise error` passes the `exc.id == handler.name` test). Both are hand-listed exit SHAPES — the instrument lesson (a guard keyed on the shape an author happened to write).
- **Wrong build W-IMPLICIT** (`findings.py::resolve`): `try: return await self._transition(…) except SurrealStoreError: await self._raise_if_already_terminal(id_or_number); raise` + a helper that re-reads (`self.get`) and raises `IllegalTransitionError("finding N is already resolved (lost a race)")` — the #102 door verbatim (exhaustion → re-read → lost-race verdict). **Receipt:** `W-IMPLICIT_resolve_rereads_through_a_helper_then_reraises · 13 failed, 1471 passed, 1 skipped, 1 warning in 480.35s · NEW contract reds (beyond the 8 baseline): 0 []`; the probe: `E AssertionError: findings.py::resolve: exhausted contention was REINTERPRETED — the caller received IllegalTransitionError(finding 1 is already resolved (lost a race)) instead of the injected TxnContentionExhaustedError instance.` → **SURVIVES**.
- **Wrong build W-REBIND** (`findings.py::wontfix`): `except SurrealStoreError as error: error = IllegalTransitionError("wontfix lost a concurrent race"); raise error`. **Receipt:** `· 13 failed, 1471 passed, 1 skipped, 1 warning in 484.34s · NEW contract reds: 0 []`; probe: `findings.py::wontfix: exhausted contention was REINTERPRETED — the caller received IllegalTransitionError(wontfix lost a concurrent race)` → **SURVIVES**.
- **P0 controls:** W-IMPLICIT-c (the SAME verdict raised INSIDE the handler) → `KILLED as declared · 1 failed, 15 passed · red: test_exhaustion_fates.py::…test_every_non_derived_site_has_a_row_and_every_row_a_site` — the classifier sees the site; only the exit shape fools it. In the probe file, `test_CONTROL_a_logged_reraise_is_still_a_passthrough` is GREEN (a legitimate log-then-raise stays derived), and `Q-WRAP[acknowledge]` is GREEN on every build (the unmutated wrapper passes identity), so the runtime probe sees the difference and nothing else.
- **Why the contract cannot see it:** SEAM drives `_transition` through `acknowledge` only; `resolve`/`wontfix` are never driven (minimal-verb ruling); TIERS's `lost-finding-transition` trigger uses `wontfix` with a REAL race (no exhaustion), where `IllegalTransitionError` is the correct verdict either way; a28b's re-read index needs a handler that awaits a same-class method whose OWN body carries a `SELECT` literal — `_raise_if_already_terminal` calls `self.get`, so it is not a "re-read" either.
- **The tests that should exist:** (1) `TestQWrapExhaustionThroughAWrapper` (pasted) — GENERATED: for every caller of a derived minimal CAS verb that has its own catch site whose closure ∋ exhaustion (the call graph already has both halves), drive the injection THROUGH the caller under a concurrent move and assert identity; (2) `TestQExitAndRebind` (pasted) — classifier units: an awaited call before the trailing `raise` is NOT a derived passthrough; a `raise <name>` after `<name>` was assigned is NOT a passthrough. The honest static form is allowlist-the-safe: PASSTHROUGH iff every statement before the re-raise is in a SAFE set (logger calls; `add_note`; assignments to locals never raised) — anything else needs a row.
- **The routing (CLAUDE.md *Fix the CLASS* rule 5; am-8 §7):** rounds r1 (`_select*`), r2 (`try` node), r2→r3 (`self._apply(` shape), and now r3 (the wrapper catch, reached by neither the MINIMAL-verb runtime ∀ nor the exit-shape static rule) are four instances of ONE property — *every door where exhausted contention can be reinterpreted is covered*. **This re-opens am-9 FK-r3-5 (Reading A MINIMAL + the §5 static rider), not the contract.** The two candidate rulings, for the sidecar: (a) FK-r3-5 Reading B — drive every caller that adds a catch (the population is already derivable from the same call graph: callers of minimal verbs with an in-domain catch site); (b) keep MINIMAL, and replace the §5 rider's static rule with allowlist-the-safe PASSTHROUGH (above). (a) is at the STATE; (b) is another shape key.
- **SIBLINGS TRIED:** implicit exit via an awaited helper (survives); rebinding (survives); tuple-constant swallow in the same wrapper (F-A's W-TUPLE — survives); the verdict raised inline (killed — control). **SIBLINGS NOT TRIED:** `raise error.with_traceback(None)` after `error.args = (…)` (mutate-then-reraise the SAME instance — identity HOLDS at runtime, the message lies; attack item 12's pure form); a `yield` of a value before the `raise` in an async-generator handler; a nested `try` inside the handler whose inner bare `raise` re-raises the INNER (verdict) exception (walked by `_exits` as a passthrough `raise` — same class, construction-inspected).

### F-NOOP — MISSING PIN (MEDIUM-HIGH, reach/proxy): the CAS population pin counts a driver as coverage when it is DECLARED — a discovered driver is never RUN; three no-op owner drivers turn SEAM fully green with nothing injected
- **CLASS:** am-8 §3 item 3 — *"coverage is a CHECKED VARIABLE derived at RUNTIME … every observed store-writing entry point is driven with the injection at least once"*. `discovered_drivers()` imports every test module's `CAS_SEAM_DRIVERS`, and `TestTheCASPopulationIsDrivenBothWays` checks only `member in drivers`; `TestExhaustedContentionReachesTheCallerAsTheSAMEInstance` is parametrised over **THIS file's** `CAS_SEAM_DRIVERS` only. So for every discovered driver — exactly FK-r3-4's routed owners (keeps, RS-5, floor_calibration) and 64b's `_run_guarded` — the effect (an injection that FIRED under the verb and reached the caller) is never observed. P1c Q4: a PROXY (a dict entry), not the effect.
- **Wrong build W-NOOP-DRIVERS** (a test-tree edit an owner could make while "adding their driver"): `loremaster/tests/test_adv58r3_owner_drivers.py` declaring `CAS_SEAM_DRIVERS = {"agents.py::register": _noop, "keeps.py::get_or_create_keyed": _noop, "floor_calibration/store.py::record_measurement": _noop}` with `async def _noop(env, ledger, seam): return None`. **Receipt:** `W-NOOP-DRIVERS_owner_registry_declares_drivers_that_never_run · 7 failed, 35 passed in 58.32s · NEW contract reds (beyond the 8 baseline): 0 []` — **and the three baseline SEAM reds are GONE**: SEAM is fully GREEN with nothing driven. Probe reds: exactly `TestQDrivenMeansRun::…[agents.py::register]`, `…[floor_calibration/store.py::record_measurement]`, `…[keeps.py::get_or_create_keyed]` (+ the 4 build-independent classifier probes) → **SURVIVES**.
- **Positive control:** on my reference (no owner module), `TestQDrivenMeansRun` is parametrised over the 7 in-file drivers and is GREEN ×7 (§REF P0 run) — the probe sees a real injection.
- **The test that should exist:** `TestQDrivenMeansRun::test_every_DISCOVERED_driver_fires_its_injection_under_its_verb` (pasted) — parametrise the identity leg over `discovered_drivers()` (not the module's own dict), asserting `verb in seam.flagged_stack` AND the identity outcome. Better still, at the STATE: a session-scoped ledger of verbs whose injection FIRED, with a final `observed == static` assertion (the runtime coverage am-8 §3 item 3 literally rules).
- **LIVE INSTANCE, cross-packet (observed 2026-09-27 in the SHARED working tree, contract-64b-r2's UNCOMMITTED WIP `loremaster/tests/test_findings_cas_seam_64b.py`, 110 lines):** it declares `CAS_SEAM_DRIVERS = {"findings.py::_run_guarded": _drive_finding_run_guarded}` and contains **no test function at all** (awk for `class |def test_|parametrize` → 0 hits). Under 58's committed SEAM that driver satisfies the population pin and is **never executed**. Its docstring says §HELD Part B item **G12 MOVES 58's `findings.py::_transition` / `annotate` drivers into that module** — at which point 58's identity leg (parametrised over its OWN dict) stops running them too: the two findings CAS verbs go from driven to declared. Not 64b's defect — 58's instrument invites it; the pin above closes it for every owner at once.
- **SIBLINGS TRIED:** a no-op driver (survives). **NOT TRIED:** a driver that arms the WRONG verb (attack item 7 — same door, the in-file identity leg's `verb in flagged_stack` would catch it only for in-file drivers); a driver that returns before arming.

### F-D — MISSING PIN (MEDIUM, reach): the driver-seam injection fires on the FIRST armed write only — a heal that swallows exhausted contention on chunk ≥ 2 survives (attack item 5)
- **CLASS:** am-8 §3 item 1 × am-3 §2 — *∀ writes a CAS verb makes, exhausted contention reaches the caller unread*. The injection's reach inside a verb is a hidden constant: `_should_fire` returns `False` once `self.injected is not None`, and every driver's population puts the verb through ONE armed write (the heal driver seeds ONE straggler → one chunk; RU's `test_every_heal_door_after_the_backfill_RAISES` also uses a one-straggler world). The heal is the one multi-write CAS verb (a chunk per transaction); chunk k ≥ 2 is never faulted by any pin.
- **Wrong build W-HEAL2** (`tasks.py`): module-level `_HEAL_ISOLATED = (TxnDomainRejectionError, SurrealStoreError)`; the chunk handler becomes `except _HEAL_ISOLATED as error: if chunk_index == 0 and not isinstance(error, TxnDomainRejectionError): raise; logger.warning(_HEAL_CHUNK_REJECTED_EVENT, …); continue` — chunk 0 propagates, every later chunk's exhaustion is WARNED and skipped, the boot completes and COUNTS only what it healed. **Receipt:** `W-HEAL2_later_heal_chunks_swallow_exhaustion_via_a_tuple · 13 failed, 1471 passed, 1 skipped, 1 warning in 456.21s (0:07:36) · NEW contract reds (beyond the 8 baseline): 0 []` · probe red `TestQHealSecondChunk::test_exhaustion_on_the_SECOND_heal_chunk_reaches_the_boot_as_the_SAME_instance` → **SURVIVES**. (It rides F-A's tuple spelling to stay out of the fate classifier; spelled as a literal tuple, `test_exhaustion_fates` would red it by name — so F-A's fix narrows this door but does not close the runtime reach gap: any spelling the static rule derives as PASSTHROUGH/TRANSLATE — F-B's shapes — reopens it.)
- **Positive control:** `TestQHealSecondChunk` is GREEN on my reference (§REF P0 run) — the probe injects at the second heal transaction, the reference propagates the SAME instance.
- **The test that should exist:** `TestQHealSecondChunk` (pasted), GENERATED properly: for every multi-write verb (today: the heal), a population spanning ≥ 2 writes, the injection armed on write k for each k in {1, 2, last}, identity asserted each time.
- **SIBLINGS TRIED:** the heal's second chunk (survives). **NOT TRIED:** a verb whose first write is not its CAS (attack item 5's literal form — construction-inspected: no production CAS verb issues an `execute_transaction` before its CAS today; `transition` / `supersede_task` / `claim_task` / findings `_transition` / `annotate` each send ONE transaction, the brief ack arms by statement predicate), a `create_many`-style batched verb (not a CAS verb today).

### F-E — MISSING PIN (MEDIUM) — the heal-convergence CLASS (am-8 §2): the GENERATED sweep never reaches a SECOND FULL chunk; a packer that forgets to count the row that opens chunk 2 is killed only by the adversary's hand instance PC, by a 49-row margin
- **CLASS:** am-8 §2's property — *∀ straggler populations, one boot heals all, every sent transaction ≤ cap* — generated over SHAPES × scale `{fit−1, fit, fit+1}`. At `fit+1` chunk 2 holds ONE row, so any packer defect that only manifests once a chunk is OPENED BY A CARRIED ROW and then FILLED (≥ 2·fit+1 rows) is outside the generated domain in every class; the two MIXED populations total ≈ 1.5 caps (2 chunks, the second half-full). The ruling itself fixed `{cap−1, cap, cap+1}`, so the sweep is faithful to am-8 §2 — the gap is in the ruled scale ingredient.
- **Wrong build W-PACK-OBO** (`tasks.py`): a hand-rolled greedy packer whose close-branch does `chunks.append(current); current, used = [entry], 0; continue` — the row that opens the next chunk is carried but not COUNTED (a classic off-by-one; not the ruled `constrained_batches`, which BC-r3-1 requires — but the contract cannot demand a library, so the PROPERTY pin must hold regardless). **Receipt:** `W-PACK-OBO_hand_rolled_packer_forgets_the_carried_row · 14 failed, 1470 passed, 1 skipped · NEW contract reds (beyond the 8 baseline): 1 ['test_reanchor_58_r3_probes.py::test_PC_stragglers_naming_TWO_superseded_blockers_at_scale_heal_in_ONE_boot']` — `E SurrealStoreError: composed transaction has 5008 statements, exceeding the hard cap of 5000` → **KILLED — but ONLY by PC**, the landed hand instance (1300 two-blocker rows, weight 8 ⇒ fit 625 ⇒ 1300 ≥ 2·625+1). Every one of CONV's 30 generated shape legs and 2 mixes stayed GREEN on it. Probe `TestQScaleThreeChunks` (e1 class, 2·fit+1 = 2501 rows) also reds: `composed transaction has 5004 statements`.
- **P2 perturbation (PC's count → {1250 = 2·fit, 1251 = 2·fit+1}), wrong build + reference control:** result in the §P2 table below.
- **Why this matters for the routing:** CLAUDE.md *Fix the CLASS* rule 3 — *hand-written cases are extra examples on top of a generated sweep, never the sweep itself*. Here the only thing between this defect and a boot that fails on every restart (the N3 outage shape: compose refuses, the heal re-builds the same chunk) is one hand fixture's count. This is the heal-sizing property's domain (am-8 §2 scale) — **a 4th instance of the heal-convergence property by the am-8 §7 test? I rule NO on the evidence, and say why:** the build DIES on the committed contract; what is missing is the generated pin's reach, and the fix is one ingredient value (`2·fit+1`, i.e. "a chunk opened by a carried row and filled"), not a new ruling. **Say so to the operator anyway**, because the ingredient list was ruled (am-8 §2) and only the sidecar can widen it.
- **The test that should exist:** `CONV.SCALES` gains `"2fit+1": fit + 1 + fit` (three chunks, the second FULL) for every shape — or the generic form: scale ∈ {fit−1, fit, fit+1, 2·fit+1} with `expected_chunks = ceil(rows / fit)`. `TestQScaleThreeChunks` (pasted) is its e1 instance; GREEN on my reference (§REF).
- **SIBLINGS TRIED:** OBO on the carried row (killed by PC only). **NOT TRIED:** a packer that resets correctly but whose FIXED per-chunk part grows with the chunk index (attack item 2 — by construction my reference's chunk = its rows' fragments + ONE `_relate_fragment` whose statements are one per pair, so its fixed part is 0; not measured separately); first-fit-decreasing / balanced packers (correct and convergent, but RED on the mixed test's greedy-closure bound — a SAT constraint the ruling makes deliberately: am-8 §1 rules the greedy `constrained_batches`, NOT A DEFECT).

### F-G — MISSING PIN (MEDIUM, P2 position monoculture): "the ROW is the unit" is pinned only with the unresolvable entry FIRST — a heal that re-anchors the healable PREFIX before the first bad entry survives
- **CLASS:** am-8 §4 F4 / am-3 §5 — *∀ rows with ≥ 1 unresolvable entry, the row is skipped WHOLE (byte-identical), UNCOUNTED, one WARNING per unresolvable entry* — ∀ POSITIONS of the bad entry. Every mixed fixture in the contract names the unresolvable entry first: CONV `blocked_by=bad + healable`, PD1 `[pblocker, hblocker]`, PD2 `[first, hblocker]`, am-9 §5 `[phantom, cyclic, healable]`. POSITION is not an ingredient of the generated composition sweep.
- **Wrong build W-F4-PREFIX** (`tasks.py`): when a row has an unresolvable entry, keep the resolvable entries BEFORE the first bad one (`good_prefix`), and if that prefix is non-empty, heal and COUNT the row on it; all the per-entry WARNINGs are still emitted. With the bad entry first the prefix is empty → identical to a correct build. **Receipt:** `W-F4-PREFIX_heals_the_healable_prefix_before_the_first_bad_entry · 14 failed, 1470 passed, 1 skipped, 1 warning in 589.25s (0:09:49) · NEW contract reds (beyond the 8 baseline): 0 []`; probe: `E AssertionError: a row with an unresolvable phantom entry AFTER a healable one was half-healed: ['a9921db52bd245759814d90b36902462', 'qf4phabad00000000000000000000000']` (and `[cyclic]` likewise) → **SURVIVES**. The half-healed row is rewritten under a WARNING that says it was skipped, and `count` over-claims — am-8 §4's own stated reason for whole-row.
- **Positive control:** `TestQF4Position` GREEN on the reference build (the unmutated heal) — receipt: the W-RETRY-RERAISE-F run (whole scope58 + the probe file, heal untouched) lists no `TestQF4Position` red (§A F-C).
- **The test that should exist:** CONV's `ROW_COMPOSITIONS` crossed with a POSITION ingredient `{bad first, bad last}` (for `bad_plus_healable`) — `TestQF4Position` (pasted) is its two-leg instance.
- **SIBLINGS TRIED:** healable-then-phantom, healable-then-cyclic (both survive). **NOT TRIED:** bad in the middle of three entries; two bad entries around a healable one (`[P, H, C]`) — same class, the position ingredient covers them.

### F-C — DUAL LOSS (MEDIUM-LOW): r2's *"the ledger never retries the CAS"* (E2) is claimed PRESERVED by identity; it is not — a retry-then-reraise-the-original build passes identity
- **CLASS:** the deleted instrument's E2 (`seam_calls_after == 0`), author R3-D2 (3). A ledger that catches the injected exhaustion, RE-SENDS its CAS (which COMMITS — the injection fires once), and then re-raises the ORIGINAL instance satisfies `reached is self.injected`. The caller is told *"exhausted contention, nothing committed"* while the write landed — the inverse of a false clear (a false FAILURE), and exactly what the driver-owns-retries rule (#102) forbids.
- **Wrong build W-RETRY-RERAISE** (`tasks.py::transition`): `except TxnContentionExhaustedError as exhausted: await self._apply([…same fragment…]); raise exhausted`. **Receipt:** `14 failed, 1470 passed … · NEW contract reds: 1 [test_reanchor_58_r3_cas_seam.py::TestExhaustedContentionReachesTheCallerAsTheSAMEInstance::…[tasks.py::transition]]` — **KILLED, but for a FIXTURE reason:** the failing line is the CONTROL leg's `assert hook.fired` (`test_reanchor_58_r3_cas_seam.py:293`) — the identity leg PASSED; the retry had already moved the SAME task to `blocked`, so the control's `transition(task_id, STATUS_BLOCKED)` failed its legality pre-check before `_apply` and the racer hook never ran. The kill depends on the driver reusing one task across its two legs.
- **Sibling W-RETRY-RERAISE-F** (`findings.py::_transition`, where SEAM's control leg uses a DIFFERENT edge, so the retried commit does not trip it): **KILLED** — `16 failed, 1468 passed … in 690.54s · NEW contract reds: 1 ['test_retry_seam.py::TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::test_the_transactional_doors_never_re_read_after_exhaustion[findings.py::_transition]']` — by 63c-i-a a28b's committed runtime door pin, not by anything in 58's r3. So E2 survives in the tree **for the doors a28b lists and exercises that way**, and is gone for everything else SEAM drives: `tasks.py::transition`'s identical retry survived every E2-shaped check (its only red was the fixture accident above). (Q-F4's positive control is in this run: `TestQF4Position` GREEN ×2 with the heal untouched.)
- **The test that should exist:** in `expect_the_SAME_instance`, after identity: the armed seam saw NO further call from the verb's frame (the E2 counter, re-homed to the driver seam), and the row the verb targeted is byte-identical to before the call (nothing committed). Probe: `Q-EXIT` catches the static half (an awaited call before the re-raise).

### F-F — MISSING PIN (LOW-MEDIUM, proxy): 8 registered fate rows rest on TEXT-ONLY evidence that a silent, success-shaped handler satisfies by accident (attack item 14)
- **CLASS:** am-10 §2 — a registered row's evidence must PROVE the fate (the F5 `effect` idiom). `_marks_failed` = any call whose NAME contains `fail` or any arg whose unparse contains `FAILED`; `_appends_failed` = any `.append` on a receiver whose text contains `failed`; `_returns_named_outcome` = any `return` whose text contains `fail`/`unavailable`/`error` or is `1`. Substrings of the SPELLING, not effects.
- **Receipt** (`evidence_probe.py`, pasted §INSTRUMENTS; run in `loremaster/tests`, 2026-09-27): rows whose evidence is text-only — `calibration/engine.py::_count_live_total#0 ('raises-chained',)` · `index/indexer.py::_walk_and_index#0 ('marks-failed',)` · `index/indexer.py::_walk_collect_tier#0 ('marks-failed',)` · `index/indexer.py::index_file#0 ('marks-failed',)` · `search.py::_enrichment_lines#0 ('returns-named-outcome',)` · `server.py::_resolve_or_acknowledge_many#0 ('appends-failed',)` · `testing/loopback.py::_loud_teardown#0 ('adds-note',)` · `testing/loopback.py::_run#0 ('records-on-self',)`. Three SILENT synthetic handlers each satisfy one: `except SurrealStoreError: return {'errors': []}` → `returns-named-outcome=True`; `… await self._maybe_failover(); return None` → `marks-failed=True`; `… failed_items.append(item); return True` (a list nobody reads) → `appends-failed=True`.
- **What wrong change survives:** any edit to one of those 8 sites that makes it success-shaped while keeping the substring (e.g. `_enrichment_lines` returning a render that still contains the word "error") keeps its row GREEN — *"the fate changed"* is not seen. (Not built against the real sites: construction-inspected via the predicates above; each predicate's accidental satisfaction is the executed receipt.)
- **The test that should exist:** evidence predicates resolved BY IMPORT to the marker OBJECT the fate names (e.g. `marks-failed` ⇔ a call whose argument IS `_FAILED_STORE_REASON` / a `…FAILED` constant resolved in the module; `returns-named-outcome` ⇔ the returned expression resolves to a named failure constant or a typed failure object), with a synthetic silent handler per predicate as the NEGATIVE control (each must NOT satisfy).
- **SIBLINGS TRIED:** 3 predicates, 3 silent shapes. **NOT TRIED:** `adds-note` (a note on an exception that is then swallowed), `records-on-self` (a stored exception nobody reads) — same class, construction-inspected.
- Attack item 13 (ordinal swap within a registered function): construction-inspected, **NOT A DEFECT as a swap** — rows are checked per ordinal, so swapping two rows' sites reds unless both evidence sets hold on both sites (then the swap is semantically nil). The keying's real bound is the NEIGHBOUR of a28b's S7/S8 finding: a NEW silent site added to a registered function while an old one there becomes PASSTHROUGH keeps the COUNT, and the new site inherits the old row (a HOLE row's empty evidence holds on anything). Pinned as a residual (R-7), not built.

### F-H — MISSING PIN (LOW): "a routine claim loss is not an alarm" is filtered by logger NAME — seven WARNINGs per race on the ROOT logger pass the whole contract
- **CLASS:** am-8 §0 row (2) — *"a routine loss is not an alarm … from ANY lore logger"*; RU and PB filter `r.name.startswith("loremaster")`. The property is about what LORE CODE emits during a routine loss; the filter is a name prefix (a hand-set reach), so a record on the root logger (`logging.warning(...)`, a plausible slip for a module without a `logger`) is outside it. The ruling's own words ("pin filter = `loremaster`") fixed the prefix, so this is LOW and partly a ruling-scope question.
- **Wrong build W-F3-ROOT** (`tasks.py::claim_task`): the typed catch's `pass` → `logging.warning("task claim lost: %s", task_id)`. **Receipt:** `W-F3-ROOT_claim_loss_WARNED_on_the_ROOT_logger · 3 failed, 53 passed in 88.36s · NEW contract reds (beyond the 8 baseline): 0 []` over R3P + RU + SEAM (the 3 reds are SEAM's baseline) → **SURVIVES**. Kill probe `q_f3.py` (`test_Q_F3_an_8_way_claim_race_raises_no_alarm_from_ANY_logger`, pasted): on the wrong build `1 failed in 1.72s` — `AssertionError: [('root', 'WARNING', 'task claim lost: b544ccb7…'), …]`; **P0 control on the reference: `1 passed in 2.00s`** (no record ≥ WARNING from ANY logger during a real 8-way race — so the stricter filter is SAT-safe on a correct build).
- **The test that should exist:** PB/RU with the filter widened to every record captured during the race (`caplog` at the ROOT, any name), as `q_f3.py` does.
- **SIBLINGS TRIED:** root logger (survives). **NOT TRIED:** `warnings.warn` (a different channel, not a log record); `print(file=sys.stderr)`.

### §AM11 fold items (F-SPEC11) — SPEC MOVED after the graded commit (am-11 `0ed6705`, docs-only, landed 2026-09-27 during this run; relayed by lead #17103, acked): five pins am-11 inverts, none carried by `7130508` — **r4 fold items, not new classes** (per #17103)
Each verified against the committed bytes:
1. **(a) row 7 (`calibration/engine.py::_count_live_total` L395, evidence `raises-chained`) must be DELETED** — it is a translate to `_ProbeUnavailableError`, which am-11 ADMITS; at `7130508` it is a registered row (`_exhaustion_fates.REGISTERED_FATES["calibration/engine.py::_count_live_total"][0]`, read above).
2. **(b) `raises-chained` retired** — present in `EVIDENCE` at `7130508`.
3. **(c) `FAULT_CLASS_NAMES` gains `_ProbeUnavailableError` + `ProbeGateError`, exact BOTH ways** (an admitted class with no translating site → RED) — at `7130508` the list has 8 entries and only `len(faults) == len(FAULT_CLASS_NAMES)` + a name-word heuristic; there is NO both-ways pin against the translating sites.
4. **(d) row 47 re-classified `re-raise-unchained` with a REQUIRED `reason`** — `Fate` has no `reason` field and `CLASSIFICATIONS` has no such member at `7130508`.
5. **(e) the positive control: a synthetic `raise IllegalTransitionError(...) from error` → RED** — at `7130508` `TestTheClassifierDiscriminates` asserts `translates_to_a_verdict` → `derived_fate is None` (row-DUE), and `_raises_chained` holds on it, so a row can adjudicate it: the exact door am-11 §2 closes. Construction-proven from the committed test's own expectation.
- **Receipt for (e)** (`am11_probe.py`, pasted; run on `scratch/head`): `derived_fate: None | raises-chained holds: True | evidence_holds(('raises-chained',)) failing = []` — at `7130508` an UNADMITTED chained translate into a VERDICT is row-DUE, and a row citing `raises-chained` would HOLD: it does **not** red by name.
- **The lead's FIX-THE-CLASS question (#17103) — "is FAULT_CLASSES derived plus pinned exact, and does an unadmitted chained translate red by name?"** At `7130508`: **(1) not derived, not exact** — `FAULT_CLASS_NAMES` is a hand-list of 8 checked only by `len(faults) == len(FAULT_CLASS_NAMES)` and a class-NAME word filter (`illegaltransition/notfound/unknown/lost/conflict`) — a verdict class named without those words (a hypothetical `AlreadyAckedError` or `StaleRevisionError`) would pass it; there is no both-ways pin against the translating sites. am-11 rightly makes ADMISSION a judgement (the D-AM10-FAULTS derivation was measured wrong), so "derived" can only mean the admission ROW's `catchers` field (am-11 §2: derived by the classifier's own walker) and the both-ways pin (an admitted class with no translating site → RED). **(2) no** — receipt above. **The class-lens finding am-11 does not see:** am-11 §2's `catchers` derivation uses THE walker and THE resolver — so it inherits **F-A**: an admitted fault class caught by `except _SOME_TUPLE:` (the tuple-constant handlers at HEAD are mostly the `_CONNECTION_ERRORS` / SDK-boundary / lease fault handlers — §A F-A's table) is missing from its `catchers`, and am-11's named re-open step (the domain generalised to *closure ∋ any admitted fault class*) would be blind to the same handlers. Fix F-A once, in the ONE resolver, before the admission rows are generated.

## MISSING PINS — the tests that should exist (each: the test · the defect it catches · CLASS)
1. **Q-TUPLE** (`TestQTupleDomain`) — every `except` expression, evaluated and FLATTENED in its module, resolves to classes (unresolvable → RED by name), equals `site.caught`, and every site that can catch exhaustion is `in_domain` · catches: 12 invisible exhaustion-catching sites at HEAD and W-TUPLE's silent swallow · CLASS: the fate domain is what Python catches, whatever the spelling (am-10 Reading (i)). **[F-A, HIGH]**
2. **Q-WRAP (generated)** — for every caller of a derived minimal CAS verb that has its own in-domain catch site, drive the injection THROUGH the caller under a concurrent move; identity · catches: W-IMPLICIT, W-REBIND, W-TUPLE (#102 through `resolve`/`wontfix`) · CLASS: every door where exhausted contention can be reinterpreted is covered — **4th instance of the CAS-population property ⇒ re-open am-9 FK-r3-5**. **[F-B, HIGH]**
3. **Q-EXIT / Q-REBIND** — `derived_fate` grants PASSTHROUGH only when every statement before the re-raise is in an allowlisted SAFE set (logger calls, `add_note`), and never for `raise <name>` after `<name>` is assigned · catches: W-IMPLICIT / W-REBIND statically, W-RETRY-RERAISE's awaited retry. **[F-B]**
4. **Q-DRIVEN** — the identity leg parametrised over `discovered_drivers()` (or a session ledger of FIRED injections, `observed == static`) · catches: W-NOOP-DRIVERS (SEAM fully green with nothing injected) and the live 64b r2 driver module with no test · CLASS: coverage is the EFFECT, not a declaration (am-8 §3 item 3). **[F-NOOP, MEDIUM-HIGH]**
5. **Q-HEAL2 (generated over write position)** — for every multi-write verb, inject at write k ∈ {1, 2, last} · catches: W-HEAL2 (chunk ≥ 2 swallowed) · CLASS: ∀ writes of a CAS verb, not the first. **[F-D, MEDIUM]**
6. **Q-SCALE** — CONV scale ingredient gains `2·fit+1` (a chunk opened by a carried row and FILLED) · catches: W-PACK-OBO in every class (today killed only by PC's 1300, 49 rows above threshold — §P2) · CLASS: am-8 §2 heal convergence ∀ scale. **[F-E, MEDIUM]**
7. **Q-F4-ORDER** — CONV F4 compositions × entry POSITION `{bad first, bad last}` · catches: W-F4-PREFIX (half-healed + counted row) · CLASS: the row is the unit ∀ positions. **[F-G, MEDIUM]**
8. **E2 re-homed** — after identity, the armed seam saw no further call from the verb's frame and the target row is byte-identical · catches: W-RETRY-RERAISE on `tasks.py::transition` (killed today only by a control-leg fixture accident) · CLASS: the driver owns retries (#102) — the deleted file's E2, adjudicated "preserved by identity" in error. **[F-C, MEDIUM-LOW, DUAL]**
9. **Evidence by effect** — evidence predicates resolved by import to the marker OBJECT, each with a silent synthetic negative control · catches: a registered site turned success-shaped while keeping a substring · CLASS: a fate is proven by an effect, not a spelling. **[F-F, LOW-MEDIUM]**
10. **Q-F3 (any logger)** — no record ≥ WARNING from ANY logger during a routine 8-way claim race · catches: W-F3-ROOT (7 root-logger WARNINGs per race) · CLASS: a routine loss is not an alarm, whatever logger name. **[F-H, LOW]**
11. **am-11 (a)–(e)** — row 7 deleted, `raises-chained` retired, `FAULT_CLASS_NAMES` + 2 admissions exact both ways, row 47 `re-raise-unchained` + `reason`, the verdict-translation control RED. **[F-SPEC11 — spec moved after the graded commit]**

## §PRIOR — the predecessor kill table: every adversary-58-r2 survivor and SAT shape, re-run on the COMMITTED bytes (2026-09-27)
Each re-expressed over MY reference's text where the r2 anchor named ref6's hand-rolled packer / prefix table (same semantics, same named defect); `wb3.py` over `scratch/wb`; "new reds" = beyond the reference's 8 owned-elsewhere reds. The r2 contract author refused to replay these (brief-base §2 — correctly); this is the grader's re-grade.
| r2 id (§A) | build | tail | new reds (the killing pins) | verdict |
|---|---|---|---|---|
| F2 · N1 | WARNING only for the transition CAS (reanchor/heal classes dropped from the table) | `9 failed, 18 passed` | PA2; TIERS drop-one legs; TIERS per-class legs; TIERS keys == typed classes | **KILLED** |
| F3 · N2 | claim loss WARNED by `loremaster.tasks` | `2 failed, 32 passed` | RU `test_an_8_way_race_logs_NO_warning…`; PB | **KILLED** |
| F1 · N3 | packer prices every row like a one-blocker row | `14 failed, 37 passed` | CONV shape legs ×10, mixed ×2, F10; PC | **KILLED** (by the generated sweep — r3's class pin works for N3) |
| F4 · N4 | phantom skips only its ENTRY | `2 failed, 49 passed` | CONV `[bad_plus_healable-phantom]`; PD1 | **KILLED** |
| F4 · N5 | cyclic skips only its ENTRY | `2 failed, 49 passed` | CONV `[bad_plus_healable-cyclic]`; PD2 | **KILLED** |
| F4 (FK-r3-6) | one WARNING per ROW (`break` restored) | `1 failed, 43 passed` | CONV `[two_bad-cyclic]` | **KILLED** — by ONE leg (the build restores `break` in the CYCLIC branch only — its anchor; the `[two_bad-cyclic]` leg is the pin that sees it) |
| F11 · N17 | heal hand-rolls its RELATEs | `1 failed, 5 passed` | REL `…composes_only_RELATEs_the_fragment…` | **KILLED** |
| F10 · N19 | over-cap row skipped silently | `2 failed, 49 passed` | CONV F10; PE | **KILLED** |
| F10 (lazy) · N19b | `constrained_batches` consumed LAZILY, monster sorted LAST (earlier batches applied first) | `1 failed, 43 passed` | CONV F10 (the companion rows) | **KILLED** — by the companion-row leg alone (PE has no companion) |
| F9 · W6a | an unprefixed app THROW → WARNING | `10 failed, 19 passed` | R3A6 `[an_unprefixed_app_throw]`; drop-one legs | **KILLED** |
| F9 · W6b | a SECOND tier table beside the ruled one | `9 failed, 20 passed` | R3A6 mutation leg (D-AM7KEY re-key); TIERS drop-one ×5 | **KILLED** |
| F9 · W6c | dedupe collapses only X copies | `2 failed, 7 passed` | R3A6 `test_P6_E11_…` ×2 | **KILLED** |
| F9 · W6d | governed conflict left at ERROR | `10 failed, 10 passed` | TIERS drop-one / per-class / keys | **KILLED** |
| F8 · N20 | a NEW helper-applied CAS verb swallowing every store error | `7 failed, 705 passed` | SEAM population `[tasks.py::assign_task]`; FATES registry | **KILLED** (graph derives it; fates sees the site) |
| F6 | a new UNGUARDED re-reading door in `messages.py` | `6 failed, 705 passed` | FATES registry **only** | **KILLED** — ⚠ only by the fate classifier: a28b's door-enumeration pin is RED at HEAD + §HELD (owned by 63c-i-a until its build), so a NEW door cannot make it redder — it is MASKED (R-5) |
| F7 | `floor_calibration` fence guard dropped | `8 failed, 703 passed` | FATES registry; RS `…transactional_doors_never_re_read_after…`; RS `…every_door_guards_the_typed_error_ABOVE…` | **KILLED** |
| F5 (SAT shape) | CORRECT claim via `contextlib.suppress(TxnClaimLostError)` | `8 failed, 1457 passed, 1 skipped in 531.61s` (whole scope58) | **0** (the 8 = baseline) | **SAT-SAFE** — r2's F5 fragility is closed (am-8 §3 / BC-r2-3 deleted) |
| F8 (SAT shape) | CORRECT heal chunk apply extracted into a helper | `8 failed, 1457 passed, 1 skipped in 554.31s` (whole scope58) | **0** | **SAT-SAFE** — r2's F8 fragility is closed |
**16/16 r2 survivors KILLED on the committed bytes.** (F5/F8 are correct-build SAT shapes, not survivors.)

## §P2 — fixture perturbation, with the correct-build control leg (2026-09-27)
| fixture | perturbation | wrong build | reference (control) | verdict |
|---|---|---|---|---|
| PC (`test_PC_…`, 1300 two-blocker rows; e2-distinct weight 8 ⇒ fit 625) | count → **1250** (= 2·fit) | W-PACK-OBO: **PASSES** (`1 failed, 1 passed` — the passing leg) | passes | PC is BLIND at 2·fit |
| same | count → **1251** (= 2·fit + 1) | W-PACK-OBO: **RED** — `SurrealStoreError: composed transaction has 5008 statements, exceeding the hard cap of 5000` | passes (`P2-CONTROL_PC_perturbed_on_the_REFERENCE · 2 passed in 36.80s`) | discriminates only past 2·fit |
⇒ The ONLY pin in the contract that kills W-PACK-OBO does so because its hand-picked count (1300) sits 49 rows above the threshold where the defect first bites. Instrument: `test_adv58r3_perturb.py` (PC's body copied, count parametrised; pasted §INSTRUMENTS). The CONV generated legs never reach the threshold in any class (§A F-E).
- CONV's own fixtures, construction-inspected for the other two P2 axes: **small-N** — none (the sweep MEASURES fit per class and seeds hundreds–thousands of rows); **parameter-value monoculture** — `head_present`/`heads`/`entries` are all varied; the monoculture that survives is entry POSITION in F4 (§A F-G); **arithmetic alignment** — fit is derived, so the dangerous branch (chunk boundary) is reached by construction at fit+1; the second-FULL-chunk branch is the one never reached (F-E).

## §P7 — RED@HEAD re-derived (2026-09-27, clean `scratch/head` = HEAD `224c74e`, code = `7130508`; no §HELD, no build)
- The six r3 contract files (`test_reanchor_58_r3_{am6,cas_seam,convergence,probes,relate,tiers}.py`): `108 tests collected`; **80 `FAILED` lines** (per file: am6 8 · cas_seam 6 · convergence 42 · probes 6 · relate 2 · tiers 16) ⇒ 28 passed — **= the author's `80 failed, 28 passed`, reproduced.** (My run used `-qq`, which drops pytest's own count line; the count is the FAILED lines + the `--co` total — stated so the receipt is not mistaken for a tail.)
- Right reasons, sampled over tiers/relate/am6 with `--tb=line`: `AttributeError: module 'loremaster.store._txn' has no attribute '_ROLLBACK_LOG_TIERS'` ×9 · `… expected 1 × WARNING; got ['ERROR']` (the transition / supersede / finding / governed legs) · `… claim-race-8-way: expected 7 × DEBUG; got []` · `the heal never composed a chunk carrying its note` · `DID NOT RAISE TaskLedgerError` (no R1 guard) · REL `drivers for no derived verb (stale): ['_reanchor_stragglers']` / `composed NO RELATE`. SEAM's 6: the 3 FK-r3-4 rows, `tasks.py::_reanchor_stragglers` + `tasks.py::claim_task` stale (no shell at HEAD), the heal identity leg. Every red is the build's absence, none an import/fixture/path error.
- `test_exhaustion_fates.py` at HEAD (`scratch/head`): **`16 passed in 4.66s`** — GREEN, as am-10 rules (and blind to F-A's 12 sites, which is why).

## §SAT — my OWN independent reference, FULL suite, one tree both ways, every red adjudicated against a HEAD baseline (2026-09-27)
- **Tree A (`scratch/ref`)** = HEAD `7294b3f` (code = `7130508`) + §HELD 1/3/2 + ref6 + `my_ref_r3a.py` (§REF), `loremaster.__file__` inside the copy (printed first line of the log). Runner `sat.sh` (waits for ≥ 22 GB; `-n 8`; run.sh's 15 GB process-TREE watchdog; attempt 1 completed, rc=1):
  **`339 failed, 12145 passed, 63 skipped, 3 xfailed, 11 warnings in 1444.20s (0:24:04)`**.
- **Tree B (`scratch/head`)** = clean HEAD `224c74e` (code = `7130508`; no §HELD, no reference), the SAME 15 files that carry any red on A, `-n 8`: **`351 failed, 1690 passed, 1 skipped, 4 warnings in 805.11s (0:13:25)`**.
- **Set diff (`comm` over the FAILED node ids):** shared **335** · base-only **16** · SAT-only **4**. Each class, individually:
  - **shared 335** — `test_comms_footer` 76 · `test_mcp_server` 28 · `test_findings_{enforcement 4, governance 24, identity 22, migrate 26, schema 17}_64b` · `test_governed_substrate_64b` 26 → **packet-64b-i-contract** (and 64b r2 in flight) · `test_fixwave_a28_63c_i_a` 76 · `a28b` 24 · `a19a` 2 · `a19b` 2 · `test_retry_seam` 2 (a28b's own door / typed enumerations) → **packet-63c-i-a-a28-contract** · `test_reanchor_58_r3_cas_seam` 3 (FK-r3-4 rows: `agents.py::register`, `keeps.py::get_or_create_keyed`, `floor_calibration/store.py::record_measurement` — the lead's routing) · `test_reanchor_58_r3_tiers` 3 (`TxnUniqueViolationError` — 63c-i-a am-33's class, unbuilt). UNRELATED or owned elsewhere; identical on both trees. (`test_mcp_server`'s set is identical with and without §HELD part 1's D7 hunk.)
  - **base-only 16** — `test_reanchor_58_r3_tiers` 13 + `test_reanchor_58_r3_cas_seam` 3: 58's own RED@HEAD pins that my reference turns GREEN (the fixed set).
  - **SAT-only 4** — `test_fixwave_a28b_63c_i_a.py::TestKeepsCasDecidesFromTheOneClass63cIAa28b::test_am32_1_2_keeps_returns_the_winner_iff_the_unique_violation_class_and_a_winner[{TxnCasLostError, TxnClaimLostError, TxnHealChunkError, TxnReanchorStragglerError}-winner-landed]`. **Adjudicated: 63c-i-a's, not 58's.** That pin DERIVES its parameters from the `TxnDomainRejectionError` subclasses, and its docstring says it is *"RED at `169925f` on every non-conflict DOMAIN class × winner-landed (keeps catches the broad `SurrealStoreError`…)"*. On tree B the same pin is red for the 5 classes HEAD defines (`SurrealStoreError`, `TxnDomainRejectionError`, `TxnEnvelopeViolationError`, `TxnGovernedConflictError`, `TxnParamCollisionError`); my reference adds 58's four classes, the derivation grows, and the four new legs are red for the identical reason (keeps not yet narrowed by 63c-i-a's build). They go green with 63c-i-a's build, which is serial BEFORE 58. Flag for the lead's currency partition: these four node ids are NEW, in an already-owned file.
  ⇒ **0 reds attributable to the 58 contract, §HELD, or my reference.** The author's `278 failed … 0 attributable` is on a different base (a28b's working copy, pre-`e039c64`); the two measurements agree on the verdict, and my 8 in-scope reds are exactly the author's 8.
- **The two correct-build SAT SHAPES r2 flagged** (F5 `suppress` claim; F8 extract-method heal), each over the whole scope58 on tree `wb`: `8 failed, 1457 passed` both — **0 new reds** (the 8 = baseline) — am-8 §3's "no instrument may dictate the shape" holds on the committed bytes.

## §HELD — `git apply --check` on the current HEAD, and the collisions with the two in-flight folds
- **Extraction:** part 2 extracted from `7130508:REPORT-contract-58-r3.md` (the fence after `**Part 2, VERBATIM**`) → md5 **`986f87dff6eb7b30c2f3d42b26dca8af`** = the recorded value; part 1 (`dbba9753`) and part 3 (`15f38e31`) from their committed reports, md5 = recorded.
- **On a CLEAN HEAD copy:** `7294b3f` → `part1/part3/part2 check OK`; re-checked on **`224c74e`** (am-11 landed) → `part1 --check OK on 224c74e` · `part3 --check OK on 224c74e` · `part2 --check OK on 224c74e`. (HEAD `f61ebe6` at report time adds one lead-report docs file; code unchanged.)
- **On the SHARED working tree** (HEAD + 64b r2's uncommitted WIP incl. `test_mcp_server.py`, `_surreal_harness.py`, `test_findings_cas_seam_64b.py`, a `scripts/pending_contracts.yaml` edit; + #486's WIP): `part1/part3/part2 shared-tree check rc=0` ×3 — no TEXTUAL collision today.
- **Collisions named (not measured — the folds are not written yet):**
  - **63c-i-a a28c** (next fold of `test_retry_seam.py`, per `REPORT-lead-63c.md` and `REPORT-adversary-63c-i-a-a28b.md`): its MP-4 (S7/S8 — *"a second CAS handler in an already-listed function collapses onto its scan key"*) re-keys `_discover_cas_handlers` PER HANDLER. §HELD part 2 rewrites the SAME function (split into `_cas_handlers_in` per module, `try*` walk) and `_caught_classes` → a **certain hunk collision** on `_discover_cas_handlers` and the §8c header; part 2 must be regenerated by `held_part2.py` after a28c, as the author's re-verification step 1 says. **And F-A lands in the same function:** the shared resolver's tuple blind spot is a28c's scanner's blind spot too — whoever lands second must carry the flatten-and-fail-closed fix into ONE resolver, not two.
  - **64b r2** (in flight): (a) part 1's D7 hunk in `test_mcp_server.py` applies today on the WIP (checked above) — re-check after 64b commits; (b) 64b's `test_findings_cas_seam_64b.py` declares a DISCOVERED driver with no test that runs it and plans to MOVE 58's two findings drivers into it (G12) — the live form of F-NOOP (§A); (c) BC-r3-7 (`_run_guarded` re-key of SEAM's findings drivers) is still owed by whoever lands second.

## §P1b — QUANTIFIER TABLE (every invariant r3 adds or re-keys; ∀-over-inputs vs guarded; receipt on every row)
| # | invariant (file) | class | receipt |
|---|---|---|---|
| Q1 | heal CONVERGES ∀ populations (CONV) | **GUARDED by scale ≤ fit+1** (ruled domain) | W-PACK-OBO: CONV 30+2 legs GREEN; killed only by the hand instance PC (§A F-E); P2 pair §P2 |
| Q2 | the row is the unit ∀ compositions (CONV F4, PD1/PD2, am-9 §5) | **GUARDED by entry POSITION** (every fixture names the bad entry FIRST) | W-F4-PREFIX (§P1 table) |
| Q3 | ONE WARNING per unresolvable ENTRY, `blocker_id` each (CONV) | ∀ over compositions | F4b (break restored) — §P1 table |
| Q4 | an over-cap row fails LOUD, nothing changes (CONV F10, PE) | ∀ (monster position varied by the companion rows) | N19 / N19b (lazy generator, monster sorted LAST) — §P1 table |
| Q5 | a routine claim loss is not an alarm (RU widened, PB) | **GUARDED by logger NAME prefix `loremaster`** | W-F3-ROOT (root logger) — §P1 table |
| Q6 | tier table keyed by CLASS == typed classes `_txn` defines (TIERS) | ∀ over `_txn`'s subclasses, oracle = ruled names | construction: a class defined outside `_txn` cannot be classified by `_txn` and its name is missing from the table → `test_every_ruled_class_has_its_ruled_tier` reds (attack item 8 — NOT A DEFECT) |
| Q7 | each class rolls back at its tier (TIERS, 8 legs) | ∀ over the trigger registry (== ruled classes) | N1 / W6a / W6b / W6d — §P1 table |
| Q8 | engine refusal / exhaustion at ERROR (TIERS) | ∀ (deny-by-default) | W6a (unprefixed THROW → WARNING) — §P1 table |
| Q9 | every composed RELATE from `_relate_fragment` (REL) | ∀ over DERIVED RELATE verbs | N17 — §P1 table |
| Q10 | exhausted contention reaches the caller as the SAME instance (SEAM) | **GUARDED ×3**: by MINIMAL verb (wrappers never driven), by the FIRST armed write, by the in-file registry | W-IMPLICIT / W-REBIND / W-TUPLE survive (F-B, F-A); W-HEAL2 survives (F-D); W-RETRY-RERAISE killed by a fixture accident (F-C) |
| Q11 | STATIC ⊆ DRIVEN ⊆ STATIC (SEAM population) | **GUARDED by DECLARATION** (proxy) | W-NOOP-DRIVERS survives (F-NOOP) |
| Q12 | ∀ catch sites with closure ∋ exhaustion: derived or registered (FATES) | **GUARDED by the resolver's spelling** (a class or a literal tuple) and the exit STATEMENT shapes | W-TUPLE survives (F-A, 12 real invisible sites); W-IMPLICIT / W-REBIND survive (F-B); controls W-TUPLE-c / W-IMPLICIT-c killed |
| Q13 | a registered row's evidence HOLDS (FATES) | **GUARDED by substring predicates** | F-F (3 silent synthetics satisfy them) |
| Q14 | UNLOGGED holes exact; fault allowlist exact (FATES) | hand-lists, both-ways on the rows only | F-A (≥ 7 holes invisible), F-SPEC11 (c) |
| Q15 | indexer SIBLING bound (FATES) | a pinned KNOWN BOUND with a trigger proxy | construction-inspected; its proxy is a NAME/VALUE occurrence scan (stated bound in its docstring) — NOT A DEFECT |
| Q16 | §HELD part 2: ONE resolver by identity; `try*` seen; catch forms seen | ∀ over the forms the walker enumerates (`Try`, `TryStar`, `suppress`) | the shared resolver carries F-A's blind spot into test_retry_seam (construction); non-catch swallow forms (`gather(return_exceptions=True)`, truthy `__exit__`, `return` in `finally`) measured **0** in production (`reach_probe.py`) — a bound to pin, not a live door |

## §P1c — REACH TABLE (every guard / scan r3 introduces or relies on)
| instrument | reach DERIVED vs hand-list | coverage a CHECKED variable? | EFFECT vs proxy | ONE source, proven by MUTATION? | legs |
|---|---|---|---|---|---|
| `_catch_sites` walker + `caught_classes` (FATES domain; §HELD part 2's resolver) | derived from the AST + module namespace — **but the value filter `inspect.isclass` silently drops tuple constants / starred elements / unbound names (63 handlers, 12 exhaustion-catching)** | **NO** — an unresolvable handler leaves the domain with no signal (fails OPEN, not closed) | proxy (source) | the resolver is shared by identity (§HELD part 2 imports it; the author's M23) — the blind spot is therefore shared too | EMPIRICAL (`tuple_probe.py`; W-TUPLE / W-TUPLE-c) → **MISSING PIN F-A** |
| `derived_fate` / `_exits` (PASSTHROUGH / TRANSLATE) | a HAND-LIST of exit statement kinds (`Raise`/`Return`/`Continue`/`Break`) | n/a | proxy (source) — an exception raised by an awaited call, or a rebound name, is invisible | — | EMPIRICAL (W-IMPLICIT, W-REBIND, Q-EXIT, Q-REBIND; control W-IMPLICIT-c) → **MISSING PIN F-B** |
| EVIDENCE predicates | substrings of the spelling | n/a | proxy | — | EMPIRICAL on synthetics (`evidence_probe.py`) → **F-F** |
| `SEAM.DriverSeamInjection` identity | seam bindings DERIVED by identity (non-vacuity asserted) | per verb: ONE armed write | EFFECT | — | EMPIRICAL: W-HEAL2 (2nd chunk) survives → **F-D** |
| `SEAM` population pin + `discovered_drivers` | DERIVED (graph ∪ listed ∪ AST-discovered registries) | **NO** — a discovered driver is counted, never run | **PROXY (a dict entry)** | — | EMPIRICAL: W-NOOP-DRIVERS survives → **F-NOOP**; live instance in 64b r2's WIP |
| `derive_cas_verbs` / `cas_verbs_in` (call graph) | DERIVED over the whole tree; same-MODULE call paths only (am-8 §3's wording) | synthetic discriminators + production non-vacuity (author's) | proxy, cross-checked by runtime attribution ⊆ graph | N20 (a new helper-applied verb) — §P1 table | EMPIRICAL (N20) + construction (cross-module apply helper = a graph blind spot the runtime attribution sees only if DRIVEN) |
| `CONV` shape × scale sweep | DERIVED product of the ruled ingredients | ingredient non-vacuity asserted (author's) | EFFECT (compose spy, columns, edges, INFO) | — | EMPIRICAL: W-PACK-OBO passes all 32 generated legs (killed by hand PC only) → **F-E**; position ingredient missing → W-F4-PREFIX |
| `TIERS` completeness + legs + drop-one mutations | DERIVED (`__subclasses__` in `_txn`) vs ruled oracle | both ways | EFFECT (caplog on the real driver) | **YES** — the generated drop-one legs ARE the mutation proof of ONE table (W6b's second table is what they kill; §P1 table) | EMPIRICAL (N1, W6a, W6b, W6d) |
| `REL` | DERIVED (same walker, seed `_relate_fragment`) | registry == derived both ways | EFFECT (compose ∩ fragment spy) | shares the walker with `derive_cas_verbs` by construction (one function, two seeds) | EMPIRICAL (N17) |
| RU / PB loud filter | **name PREFIX `loremaster`** | n/a | EFFECT (caplog) | — | EMPIRICAL (W-F3-ROOT) |

## §DUAL — P6b for the DELETED `test_reanchor_58_r2_cas_runtime.py` (R3-D2) and for everything re-keyed
**Stage 1 — my enumeration from the deleted source ALONE** (`git show 7130508^:loremaster/tests/test_reanchor_58_r2_cas_runtime.py`, before re-reading §DUAL R3-D2):
| # | observable behaviour of the deleted instrument |
|---|---|
| E1 | injects `TxnContentionExhaustedError` at the verb's OWN seam (`_apply`, or `_query` for the brief RELATE) on the ledger INSTANCE under test; the caller must raise that TYPE |
| E2 | `seam_calls_after == 0` — after the injection the verb's CAS seam is called ZERO more times (*"the LEDGER retried (the driver owns retries; #102)"*) |
| E3 | `reads_after == 0` — ZERO `_query` reads after the injection |
| E4 | `fired` — the injection must fire (the verb reached its CAS seam) |
| E5 | per verb, a REAL lost-race CONTROL with the ruled verdict (claim `ClaimResult(claimed=False)` + racer owner; transition/supersede/finding `IllegalTransitionError`; annotate `FindingNotFoundError`; brief `already_acked`; heal isolated-chunk WARNING ×1) |
| E6 | the brief-ack leg arms only the RELATE statement (`matches`) and asserts `reads_after == 0` on the same `_query` seam |
| E7 | DRIVERS == `derive_cas_verbs` both ways |
| E8 | listed handlers ⊆ DRIVERS; DRIVERS ⊆ the statically classified set |
**Stage 2 — DIFF against the author's R3-D2 (1)–(6):**
| mine | author | verdict |
|---|---|---|
| E1 | (2) RE-HOMED to the driver seam; identity replaces type | ✅ grounded — identity is STRICTER than type |
| **E2** | (3) *"PRESERVED by identity (a retry that then succeeds returns normally → SWALLOWED; one that fails differently → REINTERPRETED)"* | ❌ **the adjudication is FALSE for one shape** — a ledger that catches the injected instance, RETRIES the CAS (it COMMITS: the injection fires once), then `raise`s the ORIGINAL instance passes identity. E2 would have caught it (`seam_calls_after == 1`). → **§A F-C** (wrong build W-RETRY-RERAISE, result below) |
| E3 | (4) DROPPED DELIBERATELY (am-8 §3 item 2 rules identity) | ✅ grounded — a read that still re-raises the same instance tells no lie; consistent with am-10 |
| E4 | carried (`the injection never fired` asserts in `expect_the_SAME_instance`) | ✅ |
| E5 | (5) PRESERVED verbatim in behaviour (7 drivers) | ✅ read each driver: all seven controls present (claim racer-owner, 3 × `IllegalTransitionError`, `FindingNotFoundError`, `already_acked`, heal `…chunk_rejected` count 1) |
| E6 | folded into identity (the RELATE `matches` predicate is kept) | ✅ |
| E7 | (1) PRESERVED-WITH-PIN, widened to graph ∪ listed ∪ discovered | ⚠ widened in SET, weakened in EFFECT: a DISCOVERED member counts as driven when DECLARED, not when run → **§A F-NOOP** |
| E8 | (6) listed ⊆ driven kept; driven ⊆ classified DROPPED (am-8 §3) | ✅ grounded |
| — | author's inventory items I could not ground | none — every author row maps to one of E1–E8 |

**Re-keyed items (R3-D1, R3-D3, R3-D7, D-AM7KEY), each checked on the committed bytes:**
- R3-D1 (b) — the named briefs door is PRESERVED: `briefs.py::_relate_briefed` is a key of SEAM's `CAS_SEAM_DRIVERS`, and in `test_retry_seam._GUARDED_CAS_DOORS` on the §HELD tree ✅. (a)/(c) dropped deliberately per am-8 §3 ✅.
- R3-D3 — RU's loud filter widened to `loremaster` ✅ (diff read); the widening is by logger NAME prefix — a lore module logging on the ROOT logger is outside it (W-F3-ROOT, §A).
- R3-D7 / D-AM7KEY — the ONE-line re-key (`table.pop('cas_lost:')` → `table.pop(getattr(_txn, 'TxnCasLostError'))`) ✅ (§AST).
- **P6 corpse sweep** (bare, anchor-free; awk over `git ls-files -co` of the §HELD-applied tree for `SHELL_LEDGER_MODULES`, `SINGLE_STATEMENT_CAS_DOORS`, `APPLY_SEAM`, `_GUARDED_CAS_RE_READ`, `cas_runtime`, `BC-r2-3`, `BC-r2-9`, `reads_after`, `seam_calls_after`, `pop('cas_lost`), every hit individually:
  - `_reanchor_58_support.py:497` / `:498` — `SHELL_LEDGER_MODULES` / `SINGLE_STATEMENT_CAS_DOORS` in the R3-D1 DUAL comment that retires them → LEGIT.
  - `test_reanchor_58_r3_cas_seam.py:8` / `:274` — names the deleted file as what SEAM replaces → LEGIT.
  - **`test_reanchor_58_r2_rulings.py:590` — CORPSE (LOW, prose):** `TestTheClaimLostHierarchy`'s docstring says *"the runtime ∀ is ``test_reanchor_58_r2_cas_runtime.py``"* (deleted by this commit) and *"the typed EXACT SET … are the §HELD re-key of ``test_retry_seam.py``"* (r2's part 2 was WITHDRAWN; the typed set is a28b's). A reader following it lands on a file that does not exist. Fix: point at `test_reanchor_58_r3_cas_seam.py` and a28b's `_TYPED_CAS_CATCHES`.
  - `test_retry_seam.py` §8c `_select` mentions (post-§HELD lines 6788/6794) — the DUAL prose naming the retired key → LEGIT.
  - every other pattern → 0 hits.

## §RESIDUALS — every item, individual verdict
| # | item | verdict |
|---|---|---|
| R-1 | §AST prose: *"13 of 14 landed AST-EQUAL"* — the instrument compares 13 functions: 12 EQUAL + 1 ruled re-key | **P4 miscount (LOW)** — substance confirmed; fix the number |
| R-2 | `test_reanchor_58_r2_rulings.py:590` docstring points at the DELETED `test_reanchor_58_r2_cas_runtime.py` and the withdrawn r2 §HELD re-key | **CORPSE prose (LOW)** — §DUAL P6 |
| R-3 | `store/lease.py::create/update/release_if_held` serve `False` ("this tick did not win" — a lost-race shape) for exhausted contention, WARNING-logged; invisible to every instrument (F-A) | **OWNER RULING needed** (lease); fail-safe for leadership, but it is a verdict for exhaustion |
| R-4 | 7+ lifecycle/close HOLES invisible to the fate classifier (`inbox_awaiter` ×4, `scout.run` ×2 at DEBUG, `scout._consume_live`/`_safe_kill` at DEBUG) | **owners' one-line fixes** once F-A makes them visible; route like am-11 §3's |
| R-5 | a28b's door-enumeration exact-set pins are RED at HEAD + §HELD (owned by 63c-i-a until its build), so a NEW unguarded door cannot make them redder — F6's door was caught ONLY by the fate classifier | **MASKING bound (MEDIUM, cross-packet)** — until 63c-i-a's build lands, the static door index is blind to new doors; the lead should not read a28b's red as coverage |
| R-6 | attack item 11 — the keeps UNIQUE leg reads only `store.transaction.rolled_back`; an ERROR from another logger during the race passes | **NOT GRADED EMPIRICALLY** — `TxnUniqueViolationError` does not exist until 63c-i-a's build; same class as F-H (filter by a record NAME) — fold into F-H's widened filter |
| R-7 | fate rows keyed `file::function` + ordinal: a NEW silent site added to a registered function while an old one there becomes PASSTHROUGH keeps the count and inherits the old row (a HOLE row's empty evidence holds on anything) | **bound, construction-inspected** — the neighbour of a28b's S7/S8 (scan key collision); pin per SITE (e.g. key + the handler's caught expression), not per count |
| R-8 | attack item 9 (the one-resolver pin keyed on `ast.Expression(`) | **NOT 58's** — 63c-i-a owns it (63c am-34 §5; D-AM34) |
| R-9 | attack items 3 (a non-greedy packer meeting the order-free closure bound) and 4 (cross-task guard/send attribution) | **NOT A DEFECT** — balanced/FFD packers are convergent but RED on the mixed test's greedy bound, which am-8 §1 rules deliberately; no production CAS module uses `gather`/`create_task`/`TaskGroup` (awk over `tasks/findings/briefs/keeps/agents/floor_calibration`: 0 hits beyond the `create_task` method name) |
| R-10 | the call graph is SAME-MODULE only (am-8 §3's wording): a CAS verb applying through a helper in ANOTHER module is not derived; runtime attribution sees it only when driven | **bound, construction-inspected** — the fate classifier is the backstop for its catch; not built |
| R-11 | host memory pressure (other lore SATs + an odoo suite): the 15 GB watchdog killed W-F4-PREFIX twice and F4b once | **deviation, disclosed** — each re-run completed clean at `-n 2`; no verdict rests on a killed run |
| R-12 | the brief's "pending, don't grade" items: am-10 §2 vs §4 (**now RULED by am-11**, graded as §AM11 fold items); FK-r3-4's three undriven rows (→ 63c-i-a a28c); BC-r3-8's timeout number (lead); the 8 `UNLOGGED_SITES` (operator) | **listed, not graded** — except F-NOOP, which makes FK-r3-4's routing unsafe as written (a routed no-op driver greens the pin) |
| R-13 | 63c am-35/am-36 (`d463dba`, `547f63d`, docs, landed during this run): a28c re-keys the scanner PER HANDLER and types every engine-text reader in `_txn` | **collision forecast** — §HELD part 2 (scanner) and BC-r3-3's `_txn` classes/table both touch what a28c touches; whichever lands second regenerates (`held_part2.py`) and re-checks `_classify_engine_error`'s marker order |
| R-14 | lore dogfood: code-structure reads in this run were `awk`/`sed`/Python `ast` over SCRATCH trees and the main checkout (lore indexes the main checkout only; the hook blocks grep there) | **fallback, said out loud** — no lore weakness met, nothing to file |

## §INSTRUMENTS — pasted VERBATIM (brief-base §1: my scratch root is session-local, so every instrument a claim rests on is here)
- `run.sh` = adversary-58-r2's, byte-identical (md5 `781d16b798ab2f70f143fa147ac41e4e`; cite `821be62:REPORT-adversary-58-r2.md` §INSTRUMENTS) — not re-pasted. `scratch_copy.sh` is the repo's.

### `my_ref_r3a.py` (md5 `e6b135c53b482f8a54e704e155501f84`)
````python
#!/usr/bin/env python3
"""adversary-58-r3: MY OWN am-7 / am-8 / am-9 reference deltas over ref6 (adversary-58-r2's reference).

Written WITHOUT reading contract-58-r3's `my_ref_r3.py`.  Usage: my_ref_r3a.py <scratch-root>.
  _txn  (am-7 §4): three typed 58 classes produced by the ONE classifier from their markers; the tier table
        keyed by CLASS; `_log_rollback` receives the classified class (exhaustion / unknown -> ERROR).
  tasks (am-8 §1): the packer IS `more_itertools.constrained_batches(strict=True)` over items built ONCE,
        materialized before any apply, ValueError -> StragglerHealPackerError naming row + weight.
  tasks (am-8 §4 F4 / am-9 §5): a row with any unresolvable entry is skipped WHOLE, one WARNING per
        unresolvable ENTRY (no break), each carrying task_id + blocker_id.
Every anchor asserted exactly once (a drifted base fails loud).
"""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TASKS = ROOT / "loremaster/loremaster/tasks.py"
TXN = ROOT / "loremaster/loremaster/store/_txn.py"


def sub(src: str, old: str, new: str) -> str:
    count = src.count(old)
    assert count == 1, f"anchor occurs {count}x: {old[:90]!r}"
    return src.replace(old, new)


txn = TXN.read_text()
# --- the three 58 classes (am-6 markers -> am-7 classes) ---------------------------------------------
txn = sub(
    txn,
    "class RetryableConflictSignal(Exception):\n",
    '''class TxnCasLostError(TxnDomainRejectionError):
    """A ledger's guarded CAS matched zero rows and THREW ``cas_lost:`` (packet 58 am-6/am-7): a lost race."""


class TxnReanchorStragglerError(TxnDomainRejectionError):
    """A supersede's R1 straggler guard THREW ``reanchor_straggler:`` (packet 58 am-6/am-7)."""


class TxnHealChunkError(TxnDomainRejectionError):
    """A boot-heal chunk's guard THREW ``heal_chunk:`` (packet 58 am-6/am-7)."""


class RetryableConflictSignal(Exception):
''',
)
txn = sub(
    txn,
    '_ERROR_CLASS_UNSPECIFIED = "unspecified rejection"\n',
    '_ERROR_CLASS_CAS_LOST = "compare-and-set lost — a concurrent writer moved the row first"\n'
    '_ERROR_CLASS_REANCHOR_STRAGGLER = "re-anchor straggler — a dependent appeared after the read; retry"\n'
    '_ERROR_CLASS_HEAL_CHUNK = "heal chunk rejected — a straggler moved during the boot heal"\n'
    '_ERROR_CLASS_UNSPECIFIED = "unspecified rejection"\n',
)
txn = sub(
    txn,
    "    if CLAIM_LOST_MARKER in lowered:\n        return _ERROR_CLASS_CLAIM_LOST\n",
    "    if CLAIM_LOST_MARKER in lowered:\n        return _ERROR_CLASS_CLAIM_LOST\n"
    "    if _CAS_LOST_MARKER in lowered:\n        return _ERROR_CLASS_CAS_LOST\n"
    "    if _REANCHOR_STRAGGLER_MARKER in lowered:\n        return _ERROR_CLASS_REANCHOR_STRAGGLER\n"
    "    if _HEAL_CHUNK_MARKER in lowered:\n        return _ERROR_CLASS_HEAL_CHUNK\n",
)
txn = sub(
    txn,
    "    if error_class == _ERROR_CLASS_CLAIM_LOST:\n        return TxnClaimLostError(message)\n",
    "    if error_class == _ERROR_CLASS_CLAIM_LOST:\n        return TxnClaimLostError(message)\n"
    "    if error_class == _ERROR_CLASS_CAS_LOST:\n        return TxnCasLostError(message)\n"
    "    if error_class == _ERROR_CLASS_REANCHOR_STRAGGLER:\n        return TxnReanchorStragglerError(message)\n"
    "    if error_class == _ERROR_CLASS_HEAL_CHUNK:\n        return TxnHealChunkError(message)\n",
)
txn = sub(
    txn,
    """_ROLLBACK_LOG_TIERS: dict[str, int] = {
    CLAIM_LOST_MARKER: logging.DEBUG,
    _GOVERNED_CONFLICT_MARKER: logging.WARNING,
    _CAS_LOST_MARKER: logging.WARNING,
    _REANCHOR_STRAGGLER_MARKER: logging.WARNING,
    _HEAL_CHUNK_MARKER: logging.WARNING,
}
""",
    """_ROLLBACK_LOG_TIERS: dict[type[TxnDomainRejectionError], int] = {
    TxnClaimLostError: logging.DEBUG,
    TxnGovernedConflictError: logging.WARNING,
    TxnCasLostError: logging.WARNING,
    TxnReanchorStragglerError: logging.WARNING,
    TxnHealChunkError: logging.WARNING,
}
""",
)
txn = sub(
    txn,
    """    failed_statements: list[_FailedStatement],
) -> None:
    \"\"\"Log the FULL engine detail""",
    """    failed_statements: list[_FailedStatement],
    classified: type[BaseException] | None = None,
) -> None:
    \"\"\"Log the FULL engine detail""",
)
txn = sub(
    txn,
    """    text = str(root_cause.raw_result).lower()
    thrown = text[len(_THROW_RESULT_PREFIX):].strip() if text.startswith(_THROW_RESULT_PREFIX) else ""
    level = next(
        (tier for prefix, tier in _ROLLBACK_LOG_TIERS.items() if thrown.startswith(prefix)), logging.ERROR
    )
""",
    """    level = _ROLLBACK_LOG_TIERS.get(classified, logging.ERROR) if classified is not None else logging.ERROR
""",
)
txn = sub(
    txn,
    """            error_class = _classify_engine_error(root_cause.raw_result)
            _log_rollback(root_cause, statement_count, failed_statements)
            raise _domain_rejection_error(
                error_class,
                f"SurrealDB transaction failed and was rolled back: statement "
                f"{root_cause.index + 1} of {statement_count} was rejected "
                f"({error_class}); {_SERVER_LOG_HINT}",
            )
""",
    """            error_class = _classify_engine_error(root_cause.raw_result)
            rejection = _domain_rejection_error(
                error_class,
                f"SurrealDB transaction failed and was rolled back: statement "
                f"{root_cause.index + 1} of {statement_count} was rejected "
                f"({error_class}); {_SERVER_LOG_HINT}",
            )
            _log_rollback(root_cause, statement_count, failed_statements, type(rejection))
            raise rejection
""",
)
TXN.write_text(txn)

src = TASKS.read_text()
src = sub(src, "import networkx\n", "import networkx\nfrom more_itertools import constrained_batches\n")
# --- F4: the row is the unit; one WARNING per unresolvable ENTRY (no break) --------------------------
src = sub(
    src,
    """                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    break
""",
    """                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    continue
""",
)
src = sub(
    src,
    """                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
                    break
""",
    """                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
                    continue
""",
)
# --- the packer IS constrained_batches(strict=True), materialized before any apply ------------------
src = sub(
    src,
    """        chunks: list[list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]]] = []
        current: list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]] = []
        used = 0
        for entry in built:
            if entry[3] > cap:
                raise StragglerHealPackerError(
                    f"straggler {render_attributed(entry[0])} alone composes {entry[3]} statements, over the "
                    f"{cap}-statement transaction cap — the heal cannot pack it"
                )
            if current and used + entry[3] > cap:
                chunks.append(current)
                current, used = [], 0
            current.append(entry)
            used += entry[3]
        if current:
            chunks.append(current)
""",
    """        try:
            chunks = [list(batch) for batch in constrained_batches(built, cap, get_len=lambda e: e[3], strict=True)]
        except ValueError as error:
            monster = next(entry for entry in built if entry[3] > cap)
            raise StragglerHealPackerError(
                f"straggler {render_attributed(monster[0])} alone composes {monster[3]} statements, over the "
                f"{cap}-statement transaction cap — the heal cannot pack it"
            ) from error
""",
)
TASKS.write_text(src)
print("adversary-58-r3 am-7/am-8/am-9 deltas applied")
````

### `test_adv58r3_probes.py` (md5 `4f5f16a0bf4877a0816fc104c805c04c`)
````python
"""adversary-58-r3 kill probes — the tests that SHOULD exist (each GREEN on a correct build; RED on the named
wrong build).  Graded against packet 58 contract r3 @ 7130508; scoped to HEAD 7294b3f + §HELD 1/3/2 + my
reference (ref6 + my_ref_r3a.py), 2026-09-27.

* Q-SCALE   (am-8 §2 CLASS, heal convergence): a pure population of 2·fit+1 rows (THREE chunks) heals in one
             boot — the r3 sweep stops at fit+1 (two chunks), where a packer that forgets to count the row
             that opens chunk 2 cannot be seen.
* Q-WRAP    (am-9 §5 rider → am-10): a WRAPPER's own catch above a minimal CAS verb must pass exhausted
             contention through UNREAD — driven at runtime through `resolve` (never driven by the contract).
* Q-EXIT    (am-10 §2, classifier unit): a handler whose body AWAITS a call before its trailing `raise` is not
             a derived PASSTHROUGH (the call may raise a verdict of its own — #102's re-read, by another door).
* Q-REBIND  (am-10 §2, classifier unit): `raise <the caught name>` after the name was REBOUND is not a
             passthrough.
* Q-TUPLE   (am-10 §2 DOMAIN, Reading (i) "whatever the spelling"): a handler whose `except` names a TUPLE
             CONSTANT (`except _LOCK_CALL_ERRORS:`) is in the domain; the resolver must flatten it (Python
             allows a tuple, nested tuples, and a starred element) and an unresolvable type must RED, never
             silently leave the domain.
* Q-DRIVEN  (am-8 §3 item 3 / FK-r3-4): a discovered driver must be RUN — its injection must FIRE under its
             verb; a registry entry alone (a no-op driver) is a proxy, not coverage.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import logging
import types
from typing import Any

import pytest
from _catch_sites import CatchSite, catch_sites_in, production_catch_sites
from _reanchor_58_support import ApplyHook, ledger58
from _surreal_harness import SurrealEnv
from loremaster.store._txn import TxnContentionExhaustedError
from loremaster.tasks import TaskLedger

import test_exhaustion_fates as fates
import test_reanchor_58_r3_convergence as conv

__all__ = ["ledger58"]


# --------------------------------------------------------------------------- Q-SCALE
class TestQScaleThreeChunks:
    async def test_a_population_of_two_fits_plus_one_heals_in_ONE_boot_in_three_chunks(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        shape = conv.Shape(1, "distinct", False)
        fixed, weight = await conv.measure_weight(ledger, env, shape, "qs", caplog)
        fit = (conv.CAP - fixed) // weight
        rows = 2 * fit + 1
        population = await conv.seed_population(ledger, shape, rows, "qsp")
        spy = await conv._boot_spied(env, caplog)
        sent = conv._heal_chunks(spy)
        assert len(sent) == 3 and all(size <= conv.CAP for size in sent), (fit, sent)
        await conv._assert_converged(ledger, env, population, spy, caplog, where="Q-SCALE 2·fit+1")


# --------------------------------------------------------------------------- Q-WRAP
async def _finding_ledger(env: SurrealEnv) -> Any:
    from loremaster.findings import FindingLedger

    findings = FindingLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await findings.ensure_ready()
    return findings


class TestQWrapExhaustionThroughAWrapper:
    @pytest.mark.parametrize("wrapper", ["resolve", "wontfix", "acknowledge"])
    async def test_exhaustion_under_a_concurrent_move_reaches_the_wrapper_caller_as_the_SAME_instance(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch, wrapper: str
    ) -> None:
        import test_reanchor_58_r3_cas_seam as seam_module

        _ledger, env = ledger58
        findings = await _finding_ledger(env)
        racer = await _finding_ledger(env)
        seam = seam_module.DriverSeamInjection()
        seam.install(monkeypatch)
        try:
            number = int(
                (await findings.report("q-wrap", "b", area="adv58r3", category="test", created_by="r")).number
            )

            async def _racer_moves_it_first() -> None:
                seam.disarm()
                await racer.resolve(number, "racer-adv58r3")
                seam.arm("findings.py::_transition")

            hook = ApplyHook(findings, _racer_moves_it_first)
            seam.arm("findings.py::_transition")
            seam.disarm()  # re-armed by the hook, AFTER the racer's own write, so OUR write is the injected one
            with hook.installed():
                await seam.expect_the_SAME_instance(
                    f"findings.py::{wrapper}", lambda: getattr(findings, wrapper)(number, "actor-adv58r3")
                )
            assert hook.fired
        finally:
            await findings.close()
            await racer.close()


# --------------------------------------------------------------------------- Q-EXIT / Q-REBIND (classifier units)
_SYNTH = """
from loremaster.store._txn import SurrealStoreError
from loremaster.tasks import IllegalTransitionError


class Ledger:
    async def re_reads_then_reraises(self):
        try:
            await self.work()
        except SurrealStoreError:
            await self._raise_if_moved()
            raise

    async def rebinds_then_reraises(self):
        try:
            await self.work()
        except SurrealStoreError as error:
            error = IllegalTransitionError("a lost race")
            raise error

    async def logs_then_reraises(self):
        try:
            await self.work()
        except SurrealStoreError:
            logger.warning("x", exc_info=True)
            raise
"""


def _synth_sites() -> dict[str, CatchSite]:
    module = types.ModuleType("adv58r3_synth")
    exec(compile(_SYNTH, "<adv58r3>", "exec"), vars(module))  # noqa: S102
    return {site.key.split("::")[1]: site for site in catch_sites_in("s.py", ast.parse(_SYNTH), module)}


class TestQExitAndRebind:
    def test_CONTROL_a_logged_reraise_is_still_a_passthrough(self) -> None:
        assert fates.derived_fate(_synth_sites()["logs_then_reraises"]) == "passthrough"

    def test_Q_EXIT_an_awaited_call_before_the_reraise_is_not_a_derived_passthrough(self) -> None:
        assert fates.derived_fate(_synth_sites()["re_reads_then_reraises"]) is None

    def test_Q_REBIND_raising_a_rebound_caught_name_is_not_a_passthrough(self) -> None:
        assert fates.derived_fate(_synth_sites()["rebinds_then_reraises"]) is None


# --------------------------------------------------------------------------- Q-TUPLE
def _flattened(expression: ast.expr, module: Any) -> list[object] | None:
    """Python's own semantics for an `except` expression: a class, or a (nested) tuple of classes; a starred
    element splices a tuple.  None = unresolvable."""
    if isinstance(expression, ast.Tuple):
        out: list[object] = []
        for element in expression.elts:
            inner = _flattened(element.value if isinstance(element, ast.Starred) else element, module)
            if inner is None:
                return None
            out += inner
        return out
    try:
        value = eval(compile(ast.Expression(expression), "<q-tuple>", "eval"), vars(module))  # noqa: S307
    except Exception:  # noqa: BLE001
        return None
    if isinstance(value, tuple):
        flat: list[object] = []
        for item in value:
            flat += list(item) if isinstance(item, tuple) else [item]
        return flat
    return [value]


class TestQTupleDomain:
    def test_every_handler_type_resolves_to_classes_and_the_walker_sees_ALL_of_them(self) -> None:
        unresolved, narrowed = [], []
        for site in production_catch_sites():
            if site.handler is None or site.handler.type is None:
                continue
            full = _flattened(site.handler.type, site.module)
            if full is None or not all(inspect.isclass(value) for value in full):
                unresolved.append(f"{site.key}:{site.lineno} except {ast.unparse(site.handler.type)}")
            elif set(full) != set(site.caught):
                narrowed.append(f"{site.key}:{site.lineno} except {ast.unparse(site.handler.type)}")
        assert not unresolved and not narrowed, {"unresolved": unresolved, "narrowed": narrowed}

    def test_every_site_that_CAN_catch_exhaustion_is_in_the_classifier_domain(self) -> None:
        invisible = []
        for site in production_catch_sites():
            if site.handler is None or site.handler.type is None:
                continue
            full = _flattened(site.handler.type, site.module) or []
            catches = any(inspect.isclass(v) and issubclass(TxnContentionExhaustedError, v) for v in full)
            shielded = any(issubclass(TxnContentionExhaustedError, cls) for cls in site.earlier)
            if catches and not shielded and not fates.in_domain(site):
                invisible.append(f"{site.key}:{site.lineno} except {ast.unparse(site.handler.type)}")
        assert not invisible, invisible


# --------------------------------------------------------------------------- Q-DRIVEN
class TestQDrivenMeansRun:
    @pytest.mark.parametrize("verb", sorted(__import__("test_reanchor_58_r3_cas_seam").discovered_drivers()))
    async def test_every_DISCOVERED_driver_fires_its_injection_under_its_verb(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch, verb: str
    ) -> None:
        import test_reanchor_58_r3_cas_seam as seam_module

        ledger, env = ledger58
        seam = seam_module.DriverSeamInjection()
        seam.install(monkeypatch)
        await seam_module.discovered_drivers()[verb](env, ledger, seam)
        assert verb in seam.flagged_stack, f"{verb}: its registered driver never fired an injection under it"


_UNUSED: tuple[object, ...] = (logging, importlib)


# --------------------------------------------------------------------------- Q-HEAL2
class TestQHealSecondChunk:
    async def test_exhaustion_on_the_SECOND_heal_chunk_reaches_the_boot_as_the_SAME_instance(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """am-3 §2 / am-8 §3: every store fault on ANY heal chunk propagates — the contract injects only the
        FIRST armed call (one straggler, one chunk), so a heal that swallows on chunk ≥ 2 is unseen."""
        import test_reanchor_58_r3_cas_seam as seam_module

        ledger, env = ledger58
        shape = conv.Shape(1, "distinct", False)
        fixed, weight = await conv.measure_weight(ledger, env, shape, "qh", caplog)
        fit = (conv.CAP - fixed) // weight
        await conv.seed_population(ledger, shape, fit + 1, "qhp")
        seam = seam_module.DriverSeamInjection()
        seam.install(monkeypatch)
        heal_sends = {"n": 0}

        def _second(_call: dict[str, Any]) -> bool:
            heal_sends["n"] += 1
            return heal_sends["n"] == 2

        booted = seam_module.new_ledger(env)
        seam.arm("tasks.py::_reanchor_stragglers", matches=_second)
        try:
            await seam.expect_the_SAME_instance("tasks.py::_reanchor_stragglers", booted.ensure_ready)
        finally:
            await booted.close()
        assert heal_sends["n"] >= 2


# --------------------------------------------------------------------------- Q-F4-ORDER
class TestQF4Position:
    @pytest.mark.parametrize("kind", ["phantom", "cyclic"])
    async def test_a_row_naming_its_HEALABLE_entry_BEFORE_the_unresolvable_one_is_skipped_WHOLE(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, kind: str
    ) -> None:
        """am-8 §4 F4 ∀ POSITIONS: every r3/r2 mixed fixture names the unresolvable entry FIRST; the row is the
        unit wherever the bad entry sits."""
        from _reanchor_58_support import boot, column, create, raw_relate, raw_seed_row, snapshot

        ledger, env = ledger58
        bad = await conv._seed_bad_entry(ledger, kind, f"qf4{kind[:3]}")
        head = await create(ledger, "a real head")
        healable = conv._pad(f"qf4{kind[:3]}h")
        await raw_seed_row(ledger, healable, blocked_by=[], superseded_by=head)
        row = conv._pad(f"qf4{kind[:3]}row")
        await raw_seed_row(ledger, row, blocked_by=[healable, bad])
        for blocker in (healable, bad):
            await raw_relate(ledger, blocker, row)
        before = [entry for entry in (await snapshot(ledger))[0] if row in entry]
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            await boot(env)
        assert [entry for entry in (await snapshot(ledger))[0] if row in entry] == before, (
            f"a row with an unresolvable {kind} entry AFTER a healable one was half-healed: "
            f"{await column(ledger, row)}"
        )
        recorded = [r for r in caplog.records if r.getMessage() == conv.BAD_EVENT[kind]]
        assert [str(getattr(r, "blocker_id", None)) for r in recorded] == [bad]
        heal = conv._heal_records(caplog)
        assert not heal or getattr(heal[0], "count", 0) == 0, [getattr(r, "count", None) for r in heal]
````

### `test_adv58r3_perturb.py` (md5 `5235483eefd70fe321004f8e140a0c35`)
````python
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from _reanchor_58_support import (
    CREATOR,
    DESCRIPTION,
    HEAL_CHAIN_CYCLE_EVENT,
    HEAL_EVENT,
    HEAL_PHANTOM_HEAD_EVENT,
    ROLLBACK_EVENT,
    ApplyHook,
    ComposeSpy,
    all_columns,
    boot,
    column,
    create,
    ledger58,
    new_ledger,
    raw,
    raw_relate,
    raw_seed_row,
    snapshot,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import IllegalTransitionError, TaskLedger, TaskLedgerError
from surrealdb import RecordID



@pytest.mark.parametrize("count", [1250, 1251])
async def test_PC_P2_perturbed_count(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, count: int
) -> None:
    ledger, env = ledger58
    head_a, head_b = await create(ledger, "head A"), await create(ledger, "head B")
    legacy_a, legacy_b = "pcleg" + "a" * 27, "pcleg" + "b" * 27
    await raw_seed_row(ledger, legacy_a, blocked_by=[], superseded_by=head_a)
    await raw_seed_row(ledger, legacy_b, blocked_by=[], superseded_by=head_b)
    # P2 PERTURBATION of PC: 1300 -> {2*fit, 2*fit+1} for the e2-distinct class (fit = 625, weight 8)
    now = datetime.now(UTC)
    ids = [f"pcrow{index:05d}" for index in range(count)]
    rows = [
        {
            "id": RecordID(TASK_TABLE, task_id),
            **TaskLedger._new_task_content(f"row {task_id}", DESCRIPTION, [legacy_a, legacy_b], CREATOR, now),
        }  # noqa: SLF001
        for task_id in ids
    ]
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows})
    edges = [
        {"in": RecordID(TASK_TABLE, b), "out": RecordID(TASK_TABLE, t)}
        for t in ids
        for b in (legacy_a, legacy_b)
    ]
    await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges})
    spy = ComposeSpy()
    caplog.clear()
    with spy.installed(), caplog.at_level(logging.DEBUG):
        await boot(
            env
        )  # a packer that under-counts a two-blocker row composes > cap: compose refuses, the BOOT fails
    columns = await all_columns(ledger)
    assert all(columns[t] == [head_a, head_b] for t in ids)
    heal = [r for r in caplog.records if r.getMessage() == HEAL_EVENT]
    assert len(heal) == 1 and getattr(heal[0], "count", None) == count
    assert all(len(s) <= _txn.TXN_STATEMENT_HARD_CAP for s, _p in spy.heal_calls())
__all__ = ["ledger58"]
````

### `reach_probe.py` (md5 `44aff1aa877cc49f43085b1d36a6265e`)
````python
"""reach_probe.py — adversary-58-r3: measure the fate classifier's REACH over production at the running tree.

Run from loremaster/tests (so _catch_sites / _logging_fixtures import):  python reach_probe.py
(1) handlers whose `except` expression does NOT resolve in the module namespace (e.g. a function-local import)
    -> `caught == ()` -> silently OUT of the domain;
(2) exception-swallowing forms with NO catch site: gather(..., return_exceptions=True), `__exit__`/`__aexit__`
    that can return truthy, `return`/`break`/`continue` inside `finally`.
"""
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from _catch_sites import production_catch_sites  # noqa: E402
import loremaster  # noqa: E402

print("loremaster.__file__ =", loremaster.__file__)
sites = production_catch_sites()
print("sites total:", len(sites))
unresolved = [
    (s.key, s.lineno, ast.unparse(s.handler.type))
    for s in sites
    if s.handler is not None and s.handler.type is not None and not s.caught
]
partial = []
for s in sites:
    if s.handler is None or s.handler.type is None:
        continue
    elts = s.handler.type.elts if isinstance(s.handler.type, ast.Tuple) else [s.handler.type]
    if s.caught and len(s.caught) < len(elts):
        partial.append((s.key, s.lineno, ast.unparse(s.handler.type)))
print(f"(1) UNRESOLVED handler types: {len(unresolved)}")
for row in unresolved:
    print("   ", row)
print(f"(1b) PARTIALLY resolved tuples: {len(partial)}")
for row in partial:
    print("   ", row)

root = Path(loremaster.__file__).parent
gathers, exits, finallies = [], [], []
for path in sorted(root.rglob("*.py")):
    tree = ast.parse(path.read_text())
    rel = path.relative_to(root).as_posix()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and any(
            k.arg == "return_exceptions" and not (isinstance(k.value, ast.Constant) and k.value.value is False)
            for k in node.keywords
        ):
            gathers.append((rel, node.lineno, ast.unparse(node)[:90]))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ("__exit__", "__aexit__"):
            rets = [r for r in ast.walk(node) if isinstance(r, ast.Return) and r.value is not None
                    and not (isinstance(r.value, ast.Constant) and r.value.value in (None, False))]
            if rets:
                exits.append((rel, node.lineno, [ast.unparse(r) for r in rets]))
        if isinstance(node, (ast.Try, ast.TryStar)) and node.finalbody:
            for inner in ast.walk(ast.Module(body=node.finalbody, type_ignores=[])):
                if isinstance(inner, (ast.Return, ast.Break, ast.Continue)):
                    finallies.append((rel, inner.lineno, ast.unparse(inner)))
print(f"(2a) return_exceptions=<truthy> calls: {len(gathers)}")
for row in gathers:
    print("   ", row)
print(f"(2b) __exit__/__aexit__ that can return truthy: {len(exits)}")
for row in exits:
    print("   ", row)
print(f"(2c) return/break/continue inside finally: {len(finallies)}")
for row in finallies:
    print("   ", row)
````

### `tuple_probe.py` (md5 `baaabfc92e749ef3129aa1e2d2a14ea4`)
````python
"""tuple_probe.py — for every handler whose type is a Name/Attribute bound to a TUPLE (or a Tuple with a
Starred element), resolve the tuple's members and report whether exhausted contention is caught."""
import ast, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from _catch_sites import production_catch_sites, resolved_by_import
from loremaster.store._txn import TxnContentionExhaustedError as EX
def members(expr, module):
    if isinstance(expr, ast.Tuple):
        out = []
        for e in expr.elts:
            out += members(e.value if isinstance(e, ast.Starred) else e, module)
        return out
    v = resolved_by_import(expr, module)
    if isinstance(v, tuple):
        return list(v)
    return [v]
hits = 0
for s in production_catch_sites():
    h = s.handler
    if h is None or h.type is None:
        continue
    t = h.type
    if s.caught and not any(isinstance(e, ast.Starred) for e in getattr(t, "elts", [])):
        continue
    ms = [m for m in members(t, s.module) if isinstance(m, type)]
    catches = any(issubclass(EX, m) for m in ms)
    shielded = any(issubclass(EX, c) for c in s.earlier)
    if catches:
        hits += 1
        body = ast.unparse(ast.Module(body=h.body, type_ignores=[])).replace("\n", " | ")[:150]
        print(f"EXHAUSTION-CATCHING, INVISIBLE: {s.key}:{s.lineno} except {ast.unparse(t)} shielded={shielded} members={[m.__name__ for m in ms]}\n      body: {body}")
print("invisible exhaustion-catching sites:", hits)
````

### `evidence_probe.py` (md5 `af1d67d955e0f980c2be5d18cf100087`)
````python
"""evidence_probe.py — adversary-58-r3 item 14: which registered rows rest on TEXT-ONLY evidence, and can a
SILENT (success-shaped) handler satisfy those predicates by accident?  Run from loremaster/tests."""
import ast, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from _exhaustion_fates import REGISTERED_FATES
import test_exhaustion_fates as T
text_only = {"marks-failed", "appends-failed", "returns-named-outcome", "adds-note", "records-on-self", "raises-chained"}
for key, fates in REGISTERED_FATES.items():
    for index, fate in enumerate(fates):
        if fate.evidence and set(fate.evidence) <= text_only:
            print("TEXT-ONLY evidence row:", key, index, fate.classification, fate.evidence)
src = '''
async def f(self):
    try:
        await work()
    except SurrealStoreError:
        return {"errors": []}
async def g(self):
    try:
        await work()
    except SurrealStoreError:
        await self._maybe_failover()
        return None
async def h(self, done):
    try:
        await work()
    except SurrealStoreError:
        done.append(item)  # the failed_items list is never read
        failed_items.append(item)
        return True
'''
for handler in [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ExceptHandler)]:
    shown = ast.unparse(handler).replace("\n", " | ")[:80]
    print(f"SILENT synthetic: {shown!r}: returns-named-outcome={T._returns_named_outcome(handler)} "
          f"marks-failed={T._marks_failed(handler)} appends-failed={T._appends_failed(handler)}")
````

### `reeval.py` (md5 `cbe48911cbbb12ea52230e62c36f731a`)
````python
"""Re-evaluate every wrong-build log against the reference BASELINE (the 8 owned-elsewhere reds)."""
import re, runpy, sys
from pathlib import Path
S = Path(__file__).resolve().parent
B = runpy.run_path(str(S / "builds3.py"))["B"]
baseline = set((S / "baseline_reds.txt").read_text().split())
for name in sys.argv[1:]:
    text = (S / "wbout" / f"{name}.log").read_text()
    reds = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+?)(?: - |$)", text, re.M)))
    tail = [l for l in text.splitlines() if re.search(r"\d+ (passed|failed)", l)][-1:]
    contract = [r for r in reds if "test_adv58r3_" not in r and r not in baseline]
    probes = [r.split("::", 1)[1] for r in reds if "test_adv58r3_" in r]
    spec = B[name]
    missing = [d for d in spec["declared"] if not any(d in r for r in reds)]
    print(f"{name}\n   tail: {tail[0].strip() if tail else '?'}\n   NEW contract reds (beyond the 8 baseline): {len(contract)} {contract[:6]}\n   probe reds: {probes}\n   declared-but-green: {missing}")
````

### `scoperun.sh` (md5 `b6d11d7e5c4686da6b717522bcb5bf53`)
````bash
#!/usr/bin/env bash
# scoperun.sh <tree> <log> [extra pytest args] — the 58 scope on <tree>, waiting for >=21 GB free first.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/95318392-e065-4e77-b7ca-8f96d000c029/scratchpad
tree=$1; log=$2; shift 2
until [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -ge 18 ]; do sleep 15; done
$S/run.sh "$tree" "$log" -n 4 --tb=line -rfE $(cat $S/scope58.txt) "$@"
````

### `sat.sh` (md5 `4e0da53b31eaff58837b3b334e066a06`)
````bash
#!/usr/bin/env bash
# adversary-58-r3 SAT: FULL suite on scratch/ref (HEAD + §HELD 1/3/2 + ref6 + my_ref_r3a), my probe file not
# present in that tree.  Waits for >= 22 GB free; retries (<= 4) when run.sh's 15 GB watchdog fires (exit 98).
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/95318392-e065-4e77-b7ca-8f96d000c029/scratchpad
for attempt in 1 2 3 4; do
  until [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -ge 22 ]; do sleep 20; done
  $S/run.sh $S/ref $S/sat_full_$attempt.log -n 8 --tb=line -rfE
  rc=$?; echo "attempt $attempt rc=$rc" >> $S/sat_attempts.log
  [ $rc -ne 98 ] && break
done
````

### `scope58.txt` (md5 `79da9e85f3e3dd7d0f0f69bbfcbcf6b6`)
````text
loremaster/tests/test_supersede_reanchor_58.py
loremaster/tests/test_task_guarded_shell_58.py
loremaster/tests/test_task_claimable_partition_58.py
loremaster/tests/test_reanchor_58_r2_probes.py
loremaster/tests/test_reanchor_58_r2_scale.py
loremaster/tests/test_reanchor_58_r2_am2.py
loremaster/tests/test_reanchor_58_r2_rulings.py
loremaster/tests/test_reanchor_58_r3_am6.py
loremaster/tests/test_reanchor_58_r3_cas_seam.py
loremaster/tests/test_reanchor_58_r3_convergence.py
loremaster/tests/test_reanchor_58_r3_probes.py
loremaster/tests/test_reanchor_58_r3_relate.py
loremaster/tests/test_reanchor_58_r3_tiers.py
loremaster/tests/test_blocks_edge.py
loremaster/tests/test_task_read_surface.py
scripts/test_forgery_door_sweep.py
loremaster/tests/test_retry_seam.py
loremaster/tests/test_exhaustion_fates.py
loremaster/tests/test_supersede_render_58.py
loremaster/tests/test_surreal_store.py
````

### `baseline_reds.txt` (md5 `9f3320e429161ffee228248f30de0185`)
````text
loremaster/tests/test_reanchor_58_r3_cas_seam.py::TestTheCASPopulationIsDrivenBothWays::test_every_static_CAS_member_has_a_driver_and_every_driver_a_static_member[agents.py::register]
loremaster/tests/test_reanchor_58_r3_cas_seam.py::TestTheCASPopulationIsDrivenBothWays::test_every_static_CAS_member_has_a_driver_and_every_driver_a_static_member[floor_calibration/store.py::record_measurement]
loremaster/tests/test_reanchor_58_r3_cas_seam.py::TestTheCASPopulationIsDrivenBothWays::test_every_static_CAS_member_has_a_driver_and_every_driver_a_static_member[keeps.py::get_or_create_keyed]
loremaster/tests/test_reanchor_58_r3_tiers.py::TestDroppingOneKeyMovesOnlyThatTier::test_dropping_a_key_sends_its_trigger_to_ERROR_and_leaves_a_sibling_alone[TxnUniqueViolationError]
loremaster/tests/test_reanchor_58_r3_tiers.py::TestEachClassRollsBackAtItsTier::test_the_real_trigger_rolls_back_at_the_ruled_tier[TxnUniqueViolationError-keeps-unique-race]
loremaster/tests/test_reanchor_58_r3_tiers.py::TestTheTierTableIsKeyedByCLASSAndComplete::test_every_ruled_class_has_its_ruled_tier
loremaster/tests/test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set
loremaster/tests/test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_typed_catch_enumeration_matches_the_canonical_set_and_the_partition_is_complete
````

### `q_f3.py` (md5 `210275dec608536967ef322167943dae`)
````python
"""adversary-58-r3 Q-F3: a routine claim loss raises NO record >= WARNING from ANY logger (root included)."""
from __future__ import annotations

import asyncio
import logging

import pytest
from _reanchor_58_support import create, ledger58, new_ledger
from _surreal_harness import SurrealEnv
from loremaster.tasks import TaskLedger

__all__ = ["ledger58"]


async def test_Q_F3_an_8_way_claim_race_raises_no_alarm_from_ANY_logger(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    task_id = await create(ledger, "contended")
    racers = [new_ledger(env) for _ in range(8)]
    try:
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            results = await asyncio.gather(*(r.claim_task(task_id, f"q{i}") for i, r in enumerate(racers)))
        assert sum(result.claimed for result in results) == 1
        loud = [(r.name, r.levelname, r.getMessage()) for r in caplog.records if r.levelno >= logging.WARNING]
        assert not loud, loud
    finally:
        for racer in racers:
            await racer.close()
````

### `wb3.py` (md5 `b1f6498a598fe7d6d21598d7e8c9de44`)
````python
#!/usr/bin/env python3
"""adversary-58-r3 wrong-build driver — declare-then-diff, both ways (#194: the mutation must LAND).

Usage: wb3.py <build> [<build> ...]      (builds defined in builds3.py; each names its files + mode)

Tree = scratch/wb (a scratch_copy.sh copy of scratch/ref = HEAD 7294b3f + §HELD 1/3/2 + ref6 + my_ref_r3a,
committed in the COPY's own git).  Per build: `git checkout -- .` + reference md5 re-asserted; every anchor
asserted to occur EXACTLY once; every edited file asserted CHANGED; the named files run under run.sh's 15 GB
process-TREE watchdog (waits for >= 18 GB free first); reds diffed against the declaration; tree restored and
md5-verified (also after a killed run).  Modes:
  survive   ZERO reds in the contract files AND every declared PROBE id red  -> a MISSING PIN
  killed    every declared contract id red (extra reds listed)               -> the contract kills it
  observe   record reds (a CORRECT-build shape: any contract red is a SAT finding)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import runpy
import subprocess
import sys
import time
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
ROOT = SCRATCH / "wb"
OUT = SCRATCH / "wbout"
REF_MD5 = {
    "loremaster/loremaster/tasks.py": "1d1e5acfc2400db64b633ec7b2795b5a",
    "loremaster/loremaster/store/_txn.py": "b8da20926e635c6919023391c34c8ea0",
    "loremaster/loremaster/findings.py": "48d8fd7a477fe00c501a943ae5e619d3",
}
PROBE_PREFIX = "loremaster/tests/test_adv58r3_"


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


PROBE_SRC = SCRATCH / "probes/test_adv58r3_probes.py"


def restore() -> None:
    subprocess.run(["git", "checkout", "-q", "--", "."], cwd=ROOT, check=True)
    for extra in (ROOT / "loremaster/tests").glob("test_adv58r3_owner_*.py"):
        extra.unlink()
    (ROOT / "loremaster/tests/test_adv58r3_probes.py").write_bytes(PROBE_SRC.read_bytes())
    for rel, digest in REF_MD5.items():
        assert md5(ROOT / rel) == digest, f"reference not restored for {rel}"


def run(name: str, spec: dict) -> dict:
    restore()
    touched: dict[str, str] = {}
    try:
        _apply_edits(name, spec, touched)
    except BaseException:
        restore()
        raise
    log = OUT / f"{name}.log"
    try:
        for attempt in range(4):
            while int(open("/proc/meminfo").read().split("MemAvailable:")[1].split()[0]) < 20 * 1048576:
                time.sleep(15)
            proc = subprocess.run(
                [str(SCRATCH / "run.sh"), str(ROOT), str(log), "-n", str(spec.get("workers", 2)), "--tb=line",
                 "-rfE", *spec["files"], *spec.get("args", [])],
                cwd=ROOT, env={**os.environ, "RUN_TIMEOUT": str(spec.get("timeout", 2400))},
            )
            if proc.returncode != 98:
                break
            print(f"  {name}: watchdog fired (attempt {attempt + 1})", flush=True)
    finally:
        restore()
    return _verdict(name, spec, log, proc)


def _apply_edits(name: str, spec: dict, touched: dict[str, str]) -> None:
    for rel, old, new in spec["edits"]:
        path = ROOT / rel
        text = path.read_text()
        count = text.count(old)
        assert count == 1, f"{name}: anchor occurs {count}x in {rel}: {old[:80]!r}"
        touched.setdefault(rel, md5(path))
        path.write_text(text.replace(old, new))
    for rel, before in touched.items():
        assert md5(ROOT / rel) != before, f"{name}: {rel} unchanged — the mutation did not land"
    for rel, content in spec.get("creates", {}).items():
        assert not (ROOT / rel).exists(), rel
        (ROOT / rel).write_text(content)


def _verdict(name: str, spec: dict, log: Path, proc: subprocess.CompletedProcess) -> dict:
    text = log.read_text() if log.exists() else ""
    reds = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+?)(?: - |$)", text, re.M)))
    tail = [line for line in text.splitlines() if re.search(r"\d+ (passed|failed)", line)][-1:] or [
        f"rc={proc.returncode}"]
    baseline = set((SCRATCH / "baseline_reds.txt").read_text().split())
    contract = [r for r in reds if not r.startswith(PROBE_PREFIX) and r not in baseline]
    probes = [r for r in reds if r.startswith(PROBE_PREFIX)]
    declared = spec["declared"]
    missing = [d for d in declared if not any(d in r for r in reds)]
    mode = spec["mode"]
    if proc.returncode in (97, 98):
        verdict = f"NO VERDICT rc={proc.returncode}"
    elif mode == "survive":
        verdict = ("SURVIVES the contract (probe red)" if not contract and not missing
                   else f"KILLED by contract ({len(contract)})" if contract else f"probe GREEN: {missing}")
    elif mode == "killed":
        verdict = "KILLED as declared" if not missing else f"MISMATCH — declared stayed GREEN: {missing}"
    else:
        verdict = f"OBSERVED {len(contract)} contract red(s)"
    return {"build": name, "mode": mode, "tail": tail[0].strip(), "verdict": verdict,
            "contract_reds": contract, "probe_reds": probes, "missing": missing}


def main() -> None:
    builds = runpy.run_path(str(SCRATCH / "builds3.py"))["B"]
    OUT.mkdir(exist_ok=True)
    loremaster_file = subprocess.run(
        [str(ROOT / ".venv/bin/python"), "-c", "import loremaster; print(loremaster.__file__)"],
        capture_output=True, text=True, cwd=ROOT).stdout.strip()
    assert loremaster_file.startswith(str(ROOT)), f"PROVENANCE: {loremaster_file}"
    print("loremaster.__file__ =", loremaster_file, flush=True)
    for name in sys.argv[1:]:
        result = run(name, builds[name])
        with (OUT / "results.jsonl").open("a") as handle:
            handle.write(json.dumps(result) + "\n")
        print(f"{name:<58} {result['verdict']:<40} {result['tail']}", flush=True)
        for red in result["contract_reds"][:12]:
            print(f"    red: {red}", flush=True)


if __name__ == "__main__":
    main()
````

### `builds3.py` (md5 `6220e7122313c6ca9f1b4e67bfa1aef0`)
````python
"""adversary-58-r3 wrong builds over MY reference (scratch/wb).  B[name] = {mode, declared, files, edits}.

Part A re-expresses every adversary-58-r2 survivor (§A F1–F11, W6a–d, N20, F6, F7) and its two SAT shapes
(F5 suppress claim, F8 extract-method heal) over my am-7/am-8 reference; Part B holds the NEW r3 builds."""

T = "loremaster/loremaster/tasks.py"
X = "loremaster/loremaster/store/_txn.py"
F = "loremaster/loremaster/findings.py"
M = "loremaster/loremaster/messages.py"
FC = "loremaster/loremaster/floor_calibration/store.py"
SRV = "loremaster/loremaster/server.py"

TESTS = "loremaster/tests/"
CONV = TESTS + "test_reanchor_58_r3_convergence.py"
R3P = TESTS + "test_reanchor_58_r3_probes.py"
R3A6 = TESTS + "test_reanchor_58_r3_am6.py"
TIERS = TESTS + "test_reanchor_58_r3_tiers.py"
REL = TESTS + "test_reanchor_58_r3_relate.py"
SEAM = TESTS + "test_reanchor_58_r3_cas_seam.py"
FATES = TESTS + "test_exhaustion_fates.py"
RU = TESTS + "test_reanchor_58_r2_rulings.py"
RS = TESTS + "test_retry_seam.py"
SCOPE = [line.strip() for line in open(
    "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/95318392-e065-4e77-b7ca-8f96d000c029/scratchpad/"
    "scope58.txt").read().splitlines() if line.strip()]
PROBES = TESTS + "test_adv58r3_probes.py"

B: dict[str, dict] = {}


def build(name, mode, declared, files, *edits, **extra):
    B[name] = {"mode": mode, "declared": declared, "files": files, "edits": list(edits), **extra}


LEVEL_LINE = "    level = _ROLLBACK_LOG_TIERS.get(classified, logging.ERROR) if classified is not None else logging.ERROR\n"
HEAL_TRY = """            try:
                await self._apply([f for f in fragments if f.statements])
            except TxnDomainRejectionError:
                logger.warning(
                    _HEAL_CHUNK_REJECTED_EVENT,
                    extra={
                        "database": self._database, "chunk": chunk_index,
                        "rows": [entry[0] for entry in chunk],
                    },
                )
                continue
            healed += len(chunk)
"""

# ============================ PART A — r2's survivors, re-expressed =====================================
build("REF_control_no_edit", "observe", [], [CONV, R3P, TIERS, R3A6, REL, SEAM, FATES])

build("N1_WARNING_only_for_the_transition_CAS", "killed", ["test_PA2_", "TxnReanchorStragglerError", "TxnHealChunkError"],
      [TIERS, R3P],
      (X, "    TxnReanchorStragglerError: logging.WARNING,\n    TxnHealChunkError: logging.WARNING,\n", ""))
build("N2_claim_loss_WARNED_by_the_ledger", "killed", ["test_PB_", "test_an_8_way_race_logs_NO_warning"], [R3P, RU],
      (T, "            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict\n",
       "            logger.warning(\"task.claim.lost\", extra={\"task_id\": task_id, \"owner\": owner})\n"))
build("N3_packer_prices_every_row_like_a_one_blocker_row", "killed", ["test_PC_", "TestOneBootHealsEveryShape"],
      [CONV, R3P],
      (T, "        cap = _txn_module.TXN_STATEMENT_HARD_CAP\n        try:\n",
       "        cap = _txn_module.TXN_STATEMENT_HARD_CAP\n"
       "        unit = self._composed_statement_count([\n"
       "            TxnFragment(statements=[f\"DELETE {BLOCKS_RELATION} WHERE in = $u_in AND out = $u_out\"], params={}),\n"
       "            *self._reanchor_fragments([(\"u\", \"o\", \"h\")], actor=_HEAL_ACTOR, at=at, prefix=\"unit\"),\n"
       "            self._relate_fragment([(\"h\", \"u\")]),\n"
       "        ])\n"
       "        built = [(e[0], e[1], e[2], unit) for e in built]\n"
       "        try:\n"))
build("N4_phantom_head_skips_only_its_ENTRY", "killed", ["test_PD1_", "TestAnUnresolvableRowIsSkippedWHOLE"],
      [CONV, R3P],
      (T, """                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
                    continue
            if skip:
                continue
""", """                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    olds = [o for o in olds if o != old]
                    continue
            if skip or not olds:
                continue
"""))
build("N5_cyclic_chain_skips_only_its_ENTRY", "killed", ["test_PD2_", "TestAnUnresolvableRowIsSkippedWHOLE"],
      [CONV, R3P],
      (T, """                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    continue
""", """                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    olds = [o for o in olds if o != old]
                    continue
"""),
      (T, "            if skip:\n                continue\n", "            if skip or not olds:\n                continue\n"))
build("F4b_one_WARNING_per_ROW_not_per_ENTRY_break_restored", "killed", ["TestAnUnresolvableRowIsSkippedWHOLE"], [CONV],
      (T, """                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    continue
""", """                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    break
"""))
build("N17_heal_hand_rolls_its_RELATEs", "killed", ["TestEveryComposedRELATECameFromTheSharedFragment"], [REL],
      (T, "            fragments.append(self._relate_fragment([pair for entry in chunk for pair in entry[2]]))\n",
       "            pairs_here = [pair for entry in chunk for pair in entry[2]]\n"
       "            fragments.append(TxnFragment(\n"
       "                statements=[f\"RELATE $hr{i}_a->{BLOCKS_RELATION}->$hr{i}_b\" for i in range(len(pairs_here))],\n"
       "                params={k: v for i, (a, b) in enumerate(pairs_here) for k, v in\n"
       "                        ((f\"hr{i}_a\", RecordID(TASK_TABLE, a)), (f\"hr{i}_b\", RecordID(TASK_TABLE, b)))},\n"
       "            ))\n"))
build("N19_over_cap_row_skipped_silently", "killed", ["test_PE_", "TestARowOverTheCapFailsTheBootLOUD"], [CONV, R3P],
      (T, "        cap = _txn_module.TXN_STATEMENT_HARD_CAP\n        try:\n",
       "        cap = _txn_module.TXN_STATEMENT_HARD_CAP\n        built = [e for e in built if e[3] <= cap]\n        try:\n"))
build("N19b_packer_applies_lazily_monster_last", "killed", ["TestARowOverTheCapFailsTheBootLOUD"], [CONV],
      (T, "            chunks = [list(batch) for batch in constrained_batches(built, cap, get_len=lambda e: e[3], strict=True)]\n",
       "            chunks = (list(batch) for batch in constrained_batches(sorted(built, key=lambda e: e[3]), cap, get_len=lambda e: e[3], strict=True))\n"),
      (T, "            ) from error\n        healed = 0\n        for chunk_index, chunk in enumerate(chunks):\n",
       "            ) from error\n        healed = 0\n        n_chunks = 0\n        try:\n          for chunk_index, chunk in enumerate(chunks):\n            n_chunks += 1\n"),
      (T, "            healed += len(chunk)\n        if healed:\n            logger.info(\n                _HEAL_EVENT, extra={\"database\": self._database, \"count\": healed, \"chunks\": len(chunks)}\n",
       "            healed += len(chunk)\n        except ValueError as error:\n            raise StragglerHealPackerError(f\"a straggler alone composes {max(e[3] for e in built)} statements over the cap\") from error\n        if healed:\n            logger.info(\n                _HEAL_EVENT, extra={\"database\": self._database, \"count\": healed, \"chunks\": n_chunks}\n"))
build("W6a_unrecognised_app_throw_defaults_to_WARNING", "killed", ["an_unprefixed_app_throw"], [R3A6, TIERS],
      (X, LEVEL_LINE,
       "    level = _ROLLBACK_LOG_TIERS.get(classified, logging.ERROR) if classified is not None else logging.ERROR\n"
       "    if level == logging.ERROR and str(root_cause.raw_result).lower().startswith(_THROW_RESULT_PREFIX) "
       "and not _is_retryable_conflict_text(str(root_cause.raw_result)):\n        level = logging.WARNING\n"))
build("W6b_a_SECOND_tier_table_beside_the_ruled_one", "killed", ["TestDroppingOneKeyMovesOnlyThatTier"], [TIERS, R3A6],
      (X, LEVEL_LINE,
       "    _private = {TxnClaimLostError: logging.DEBUG, TxnGovernedConflictError: logging.WARNING, TxnCasLostError: "
       "logging.WARNING, TxnReanchorStragglerError: logging.WARNING, TxnHealChunkError: logging.WARNING}\n"
       "    level = _private.get(classified, logging.ERROR) if classified is not None else logging.ERROR\n"))
build("W6d_governed_conflict_left_at_ERROR", "killed", ["TxnGovernedConflictError"], [TIERS],
      (X, "    TxnGovernedConflictError: logging.WARNING,\n", ""))
build("N20_helper_applied_NEW_verb_swallows_exhaustion", "killed", ["TestTheCASPopulationIsDrivenBothWays"],
      [SEAM, FATES, RS],
      (T, "    async def _reanchor_stragglers(self) -> None:\n", '''    async def assign_task(self, task_id: str, owner: str) -> bool:
        """N20: a 57-shaped NEW CAS verb — shell fragment built here, applied through a helper."""
        fragment = self._guarded_append_fragment(
            task_id, event=None, set_parts=["owner = $asg_owner"], params={"asg_owner": owner},
            where_conjuncts=["owner IS NONE"], throw_message="cas_lost: assign lost", namespace="asg",
        )
        return await self._commit_assign([fragment], task_id)

    async def _commit_assign(self, fragments: list[TxnFragment], task_id: str) -> bool:
        try:
            await self._apply(fragments)
        except SurrealStoreError:  # UNGUARDED: exhausted contention is re-read and served as "lost"
            return await self._select_row(task_id) is None
        return True

    async def _reanchor_stragglers(self) -> None:
'''))
build("F6_new_unguarded_re_reading_door_in_messages", "killed", ["test_retry_seam", "test_exhaustion_fates"],
      [RS, FATES, SEAM],
      (M, "    async def _apply(", '''    async def _adv58r2_door(self, row_id: str) -> bool:
        """adversary-58-r2 REACH probe: an UNGUARDED guarded-CAS door — a rollback handler that re-reads."""
        try:
            await self._apply([])
        except SurrealStoreError:
            return await self._read_back_seq(row_id) is not None
        return True

    async def _apply('''))
build("F7_floor_calibration_fence_guard_dropped", "killed", ["test_exhaustion_fates", "test_retry_seam"],
      [RS, FATES, SEAM],
      (FC, "        except (SurrealConnectionError, TxnContentionExhaustedError):\n            # NEITHER is a fence verdict",
       "        except SurrealConnectionError:\n            # NEITHER is a fence verdict"))
build("F8_CORRECT_heal_chunk_apply_in_a_helper", "observe", [], SCOPE,
      (T, HEAL_TRY, """            if await self._apply_heal_chunk(chunk_index, [entry[0] for entry in chunk], fragments):
                healed += len(chunk)
"""),
      (T, "    @staticmethod\n    def _supersede_fragment(", '''    async def _apply_heal_chunk(self, chunk_index: int, rows: list[str], fragments: list[TxnFragment]) -> bool:
        """Apply ONE heal chunk; a DOMAIN rejection is isolated + WARNING (am-3 §2); a store fault raises."""
        try:
            await self._apply([f for f in fragments if f.statements])
        except TxnDomainRejectionError:
            logger.warning(
                _HEAL_CHUNK_REJECTED_EVENT,
                extra={"database": self._database, "chunk": chunk_index, "rows": rows},
            )
            return False
        return True

    @staticmethod
    def _supersede_fragment('''))
build("F5_CORRECT_claim_catches_the_type_via_suppress", "observe", [], SCOPE,
      (T, """        try:
            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
        except TxnClaimLostError:
            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict
""", """        with contextlib.suppress(TxnClaimLostError):  # a routine loss (am-3 §3) — typed; the owner read decides
            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
"""),
      (T, "import asyncio\n", "import asyncio\nimport contextlib\n"))

# ============================ PART B — NEW r3 builds =====================================================
from pathlib import Path as _P  # noqa: E402
_XONLY = __import__("runpy").run_path(str(_P(__file__).parent / "inst/wb6.py").replace("wb6.py", "wb6.py"), run_name="x") if False else None
build("W6c_dedupe_collapses_only_X_copies", "killed", ["test_P6_E11_"], [R3A6],
      (T, """                        f"{_COL_BLOCKED_BY} = array::distinct(array::map({_COL_BLOCKED_BY}, "
                        f"|$b| IF $b = ${old_param} THEN ${new_param} ELSE $b END))"
""", """                        f"{_COL_BLOCKED_BY} = array::filter(array::map(array::map({_COL_BLOCKED_BY}, "
                        f"|$b| IF $b = ${old_param} THEN ${new_param} ELSE $b END), |$v, $i| IF $v = ${new_param} "
                        f"AND $i != array::find_index(array::map({_COL_BLOCKED_BY}, |$b| IF $b = ${old_param} "
                        f"THEN ${new_param} ELSE $b END), ${new_param}) THEN NONE ELSE $v END), |$v| $v != NONE)"
"""))

PACK_NEW = """        chunks: list[list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]]] = []
        current: list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]] = []
        used = 0
        for entry in built:
            if entry[3] > cap:
                raise StragglerHealPackerError(
                    f"straggler {render_attributed(entry[0])} alone composes {entry[3]} statements, over the "
                    f"{cap}-statement transaction cap — the heal cannot pack it"
                )
            if current and used + entry[3] > cap:
                chunks.append(current)
                current, used = [entry], 0  # the row that opens the next chunk is carried but NOT counted
                continue
            current.append(entry)
            used += entry[3]
        if current:
            chunks.append(current)
"""
PACK_OLD = """        try:
            chunks = [list(batch) for batch in constrained_batches(built, cap, get_len=lambda e: e[3], strict=True)]
        except ValueError as error:
            monster = next(entry for entry in built if entry[3] > cap)
            raise StragglerHealPackerError(
                f"straggler {render_attributed(monster[0])} alone composes {monster[3]} statements, over the "
                f"{cap}-statement transaction cap — the heal cannot pack it"
            ) from error
"""
build("W-PACK-OBO_hand_rolled_packer_forgets_the_carried_row", "survive", ["test_adv58r3_probes.py::TestQScaleThreeChunks"],
      SCOPE + [PROBES], (T, PACK_OLD, PACK_NEW))

build("W-IMPLICIT_resolve_rereads_through_a_helper_then_reraises", "survive",
      ["TestQWrapExhaustionThroughAWrapper::test_exhaustion_under_a_concurrent_move_reaches_the_wrapper_caller_as_the_SAME_instance[resolve]",
       "TestQExitAndRebind::test_Q_EXIT"],
      SCOPE + [PROBES],
      (F, "        return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)\n",
       """        try:
            return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)
        except SurrealStoreError:
            await self._raise_if_already_terminal(id_or_number)
            raise

    async def _raise_if_already_terminal(self, id_or_number: int | str) -> None:
        \"\"\"A store error on resolve: if the finding is already terminal, a concurrent resolver won — say so.\"\"\"
        current = await self.get(id_or_number)
        if current.status in (STATUS_RESOLVED, STATUS_WONTFIX):
            raise IllegalTransitionError(f"finding {current.number} is already {current.status} (lost a race)")
"""))
build("W-IMPLICIT-c_CONTROL_the_same_verdict_raised_INSIDE_the_handler", "killed", ["test_exhaustion_fates"], [FATES],
      (F, "        return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)\n",
       """        try:
            return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)
        except SurrealStoreError:
            current = await self.get(id_or_number)
            if current.status in (STATUS_RESOLVED, STATUS_WONTFIX):
                raise IllegalTransitionError(f"finding {current.number} is already {current.status} (lost a race)")
            raise
"""))
build("W-REBIND_wontfix_rebinds_the_caught_name_to_a_verdict", "survive",
      ["TestQWrapExhaustionThroughAWrapper::test_exhaustion_under_a_concurrent_move_reaches_the_wrapper_caller_as_the_SAME_instance[wontfix]",
       "TestQExitAndRebind::test_Q_REBIND"],
      SCOPE + [PROBES],
      (F, "        return await self._transition(id_or_number, STATUS_WONTFIX, actor, note)\n",
       """        try:
            return await self._transition(id_or_number, STATUS_WONTFIX, actor, note)
        except SurrealStoreError as error:
            error = IllegalTransitionError("wontfix lost a concurrent race")  # noqa: PLW2901
            raise error
"""))
build("W-TUPLE_resolve_swallows_via_a_tuple_constant_and_serves_the_row", "survive",
      ["TestQWrapExhaustionThroughAWrapper::test_exhaustion_under_a_concurrent_move_reaches_the_wrapper_caller_as_the_SAME_instance[resolve]"],
      SCOPE + [PROBES],
      (F, "        return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)\n",
       """        try:
            return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)
        except _RESOLVE_TOLERATED:
            return await self.get(id_or_number)  # the store is authoritative: serve what it holds
"""),
      (F, "\nclass FindingLedger:", "\n_RESOLVE_TOLERATED = (SurrealStoreError,)\n\n\nclass FindingLedger:"))
build("W-TUPLE-c_CONTROL_the_same_swallow_with_a_literal_tuple", "killed", ["test_exhaustion_fates"], [FATES],
      (F, "        return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)\n",
       """        try:
            return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)
        except (SurrealStoreError,):
            return await self.get(id_or_number)  # the store is authoritative: serve what it holds
"""))
build("W-RETRY-RERAISE_transition_retries_then_reraises_the_original", "survive",
      ["TestQExitAndRebind::test_Q_EXIT"], SCOPE + [PROBES],
      (T, """            await self._apply(
                [
                    self._transition_fragment(
                        task_id, status, current, event, release, summary, report_path
                    )
                ]
            )
""", """            try:
                await self._apply(
                    [self._transition_fragment(task_id, status, current, event, release, summary, report_path)]
                )
            except TxnContentionExhaustedError as exhausted:
                await self._apply(
                    [self._transition_fragment(task_id, status, current, event, release, summary, report_path)]
                )
                raise exhausted
"""))
build("W-HEAL2_later_heal_chunks_swallow_exhaustion_via_a_tuple", "survive",
      ["TestQHealSecondChunk"], SCOPE + [PROBES],
      (T, """            except TxnDomainRejectionError:
                logger.warning(
                    _HEAL_CHUNK_REJECTED_EVENT,""", """            except _HEAL_ISOLATED as error:
                if chunk_index == 0 and not isinstance(error, TxnDomainRejectionError):
                    raise
                logger.warning(
                    _HEAL_CHUNK_REJECTED_EVENT,"""),
      (T, "class StragglerHealPackerError(TaskLedgerError):",
       "_HEAL_ISOLATED = (TxnDomainRejectionError, SurrealStoreError)\n\n\nclass StragglerHealPackerError(TaskLedgerError):"))
build("W-NOOP-DRIVERS_owner_registry_declares_drivers_that_never_run", "survive",
      ["TestQDrivenMeansRun"], [SEAM, PROBES],
      creates={"loremaster/tests/test_adv58r3_owner_drivers.py": '''"""adversary-58-r3 W-NOOP-DRIVERS: an owner module declaring drivers that never inject."""


async def _noop(env, ledger, seam):
    return None


CAS_SEAM_DRIVERS = {
    "agents.py::register": _noop,
    "keeps.py::get_or_create_keyed": _noop,
    "floor_calibration/store.py::record_measurement": _noop,
}
'''})
build("W-F4-PREFIX_heals_the_healable_prefix_before_the_first_bad_entry", "survive",
      ["TestQF4Position"], SCOPE + [PROBES],
      (T, "            if skip:\n                continue\n            final = list(columns)\n",
       """            if skip:
                good_prefix: list[str] = []
                for candidate in olds:
                    if heads[candidate][1] or heads[candidate][0] not in existing:
                        break
                    good_prefix.append(candidate)
                if not good_prefix:
                    continue
                olds = good_prefix  # heal what resolves before the first unresolvable entry
            final = list(columns)
"""))
build("W-F3-ROOT_claim_loss_WARNED_on_the_ROOT_logger", "survive", ["test_PB_"], [R3P, RU, SEAM],
      (T, "            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict\n",
       "            logging.warning(\"task claim lost: %s\", task_id)  # an alarm, from lore code, on the root logger\n"))
build("W-RETRY-RERAISE-F_finding_transition_retries_then_reraises_the_original", "survive",
      ["TestQExitAndRebind::test_Q_EXIT"], SCOPE + [PROBES],
      (F, """            await self._apply([self._transition_fragment(finding_id, target, current, event)])
        except SurrealConnectionError:
""", """            await self._apply([self._transition_fragment(finding_id, target, current, event)])
        except TxnContentionExhaustedError as exhausted:
            await self._apply([self._transition_fragment(finding_id, target, current, event)])
            raise exhausted
        except SurrealConnectionError:
"""))
_PERTURB = open("/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/95318392-e065-4e77-b7ca-8f96d000c029/scratchpad/probes/test_adv58r3_perturb.py").read()
build("P2-CONTROL_PC_perturbed_on_the_REFERENCE", "observe", [], [TESTS + "test_adv58r3_owner_perturb.py"],
      creates={"loremaster/tests/test_adv58r3_owner_perturb.py": _PERTURB})
build("P2-PACK-OBO_PC_perturbed_on_the_wrong_build", "observe", [], [TESTS + "test_adv58r3_owner_perturb.py"],
      (T, PACK_OLD, PACK_NEW), creates={"loremaster/tests/test_adv58r3_owner_perturb.py": _PERTURB})
_QF3 = open("/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/95318392-e065-4e77-b7ca-8f96d000c029/scratchpad/probes/q_f3.py").read()
build("QF3-CONTROL_on_the_REFERENCE", "observe", [], [TESTS + "test_adv58r3_owner_qf3.py"],
      creates={"loremaster/tests/test_adv58r3_owner_qf3.py": _QF3})
build("QF3-on-W-F3-ROOT", "observe", [], [TESTS + "test_adv58r3_owner_qf3.py"],
      (T, "            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict\n",
       "            logging.warning(\"task claim lost: %s\", task_id)  # an alarm, from lore code, on the root logger\n"),
      creates={"loremaster/tests/test_adv58r3_owner_qf3.py": _QF3})
````

### `am11_probe.py` (md5 `2b1dd0ee29448e806c1579f7e5336fe7`)
````python
"""am11_probe.py — adversary-58-r3: at 7130508, is an UNADMITTED chained translate RED by name, or row-able?"""
import ast, sys, types
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import test_exhaustion_fates as T
from _catch_sites import catch_sites_in
src = T._SYNTHETIC
module = types.ModuleType("am11")
exec(compile(src, "<am11>", "exec"), vars(module))
site = [s for s in catch_sites_in("synthetic.py", ast.parse(src), module) if s.key.endswith("translates_to_a_verdict")][0]
print("derived_fate:", T.derived_fate(site), "| raises-chained holds:", T.EVIDENCE["raises-chained"](site.handler),
      "| evidence_holds(('raises-chained',)) failing =", T.evidence_holds(site, ("raises-chained",)))
````

## VERDICT
**CONTRACT INSUFFICIENT.** Graded `7130508` (HEAD-at-report `6bb95af`, docs-only ahead). Seven wrong builds pass every r3 pin (and every r2 pin still in the tree) with zero reds beyond the reference's eight owned-elsewhere reds; two more die only by accident. Each has a kill probe that is GREEN on my independent reference and RED on the build. The missing pins, by class:
- **MISSING PIN / NEW DOOR (HIGH) — F-A:** the fate classifier's resolver drops tuple-constant handlers (12 real exhaustion-catching sites at HEAD are invisible; W-TUPLE survives) → `TestQTupleDomain`.
- **MISSING PIN / NEW DOOR (HIGH) — F-B, the 4th instance of the CAS-population property → re-open am-9 FK-r3-5:** wrapper catches reinterpret exhaustion through an awaited helper or a rebound name, and both instruments pass them (W-IMPLICIT, W-REBIND) → `TestQWrapExhaustionThroughAWrapper` (generated) + `TestQExitAndRebind`.
- **MISSING PIN (MEDIUM-HIGH) — F-NOOP:** discovered drivers are counted, never run (W-NOOP-DRIVERS; live in 64b r2's WIP) → `TestQDrivenMeansRun`.
- **MISSING PIN (MEDIUM) — F-D, F-E, F-G:** first-write-only injection (W-HEAL2) → `TestQHealSecondChunk`; scale stops at fit+1 (W-PACK-OBO, held only by PC) → `TestQScaleThreeChunks`; F4 position monoculture (W-F4-PREFIX) → `TestQF4Position`.
- **DUAL LOSS (MEDIUM-LOW) — F-C:** E2 ("the ledger never retries") is not preserved by identity (W-RETRY-RERAISE on `transition`) → the E2 counter re-homed to the driver seam.
- **MISSING PIN (LOW-MEDIUM / LOW) — F-F, F-H:** substring evidence; logger-NAME alarm filter (W-F3-ROOT) → evidence by effect; `q_f3.py`.
- **§AM11 fold items ×5** (spec moved after the graded commit).
- **SAT: 0 attributable** on an independent reference; §HELD applies on HEAD; the predecessor's 16 survivors are all KILLED; RED@HEAD reproduced.
