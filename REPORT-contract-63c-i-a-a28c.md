brief-base v17 read · brief project v7 read

# REPORT-contract-63c-i-a-a28c — the LAST-round fold of the 63c-i-a contract (a28b → a28c): am-35 §W + am-34 + MP-1/2/4/5 + FK-r3-4

*Every claim here is scoped to the tree it names. "At HEAD" = `6bb95af` — HEAD moved to `706a1bf` during the fold, which adds only
`REPORT-adversary-58-r3.md` (`git diff --stat 6bb95af 706a1bf`: that one file; §FLAGS F-13a / F-15 read it) (branch `feat/surreal-unification`,
2026-09-27) unless dated otherwise; production 63c files are byte-identical `169925f` → HEAD (checked).*

## SUMMARY BLOCK
- **State: done-with-deviations.** a28c folds am-35 §W + am-34 + am-36 (FK-1 IN, FK-2..8) + MP-1/2/4/5 + FK-r3-4 into 12 test / support files + my registry entry; every new pin GENERATED with a completeness leg (§2).
- **Deviations** (§4): D-1 KD adapted · D-2 scanner folds 58 §HELD part 2 · D-5/D-11 DUAL edits in 58's committed `cas_seam` / `tiers` / `_exhaustion_fates` files + 63a's migrate pin (U-25…U-27, SAT-found) · D-8 NEW `_engine_shapes.py` · D-9 harness re-key §HELD · D-12 exact-set pin's first derivation was blind to `169925f`'s own readers — rewritten allowlist-the-safe, mutation-proven · D-13 whitespace-only refill of my prose, strict-proven.
- **Packages considered:** `surrealdb.errors.parse_query_error` + `ServerError.details` → replace_with_adapter; `KIND_TO_CLASS` → replace; untyped U / ASSERT / coercion / recursion text → bespoke (read live: `Internal` / `Validation`, `details: None`); stdlib `ast` + `_catch_sites` → replace; pydantic field info → replace (§Packages considered).
- **Odoo-20 portability:** n/a — not the Odoo tree.
- **Reuse ledger:** 11 rows of new test-support symbols, all dispositioned (§DRY LEDGER).
- **Graded:** `169925f` (production under contract; the reference = it + §A.5) · HEAD-at-report: `706a1bf` · DIFFERENT (HEAD is 103 commits ahead; production drift = `testing/loopback.py` only, not 63c; 706a1bf itself is docs-only).
- **SAT (§8):** REF-ONLY 3 → fixed → **0**; shared reds 413, reasons identical on both trees, all 58/64b-owned. **Mutation (§6):** 29/29 killed, 25 exact, 4 prediction misses adjudicated. **Concurrency (§7):** 20/20 consecutive × 26. **Currency (§9):** PASS on the final content — typecheck 64 / pytest 847 residuals, all owned, ruff GREEN, 0 RED_ORPHANED.
- **Decisions needed:** (1) FK-a28c-9 — text also decides for `kind: Validation` (recursion depth), my Reading A · (2) F-15 — a28b's pending-red exact sets mask a second door until the build: accept, or pin the expected-at-base set · (3) F-11 — a transactional parse error is served as `SurrealConnectionError` and drops the connection (pre-existing) · (4) for 58-r4: keep the `_comms_register` fates row deleted (F-13/13a), F-3's `install` flag, FK-6's one-line accessor change.
- **Pointers:** RED §RED · SAT §8 · mutations §6 + §A.9 · DUAL §5 (U-1…U-28 + sweeps) · builder constraints §BUILDER CONSTRAINTS item 1 (incl. the four-tester allowlist) · attack list §ATTACK LIST.

## §F FORKS — written BEFORE the pins that depend on them (brief: ambiguity → report first, one message, continue on the pick)

### FK-a28c-1 — echoed RETRY / CASCADE phrases move the served class; they live outside am-35 §2's enumerated classifier markers
**Measured 2026-09-27 on the test store (`surrealdb 3.2.4`), instrument `probe_a28c.py` (§A.1) run against HEAD's
`_txn` (= `169925f`):**
| host (the real rejection) | echoed value carries | `run_query` | `execute_transaction` |
|---|---|---|---|
| UNIQUE-index collision | `… This transaction can be retried` | `TxnContentionExhaustedError` after **2.09 s** of retries | `TxnContentionExhaustedError` (2.02 s) |
| coercion failure | same | `TxnContentionExhaustedError` (2.00 s) | same (2.01 s) |
| governed THROW | same | `TxnContentionExhaustedError` (2.03 s) | same |
| governed THROW | `… was not executed due to a failed transaction` / `… aborted due to a prior error` | `TxnGovernedConflictError` | **`TxnDomainRejectionError`** — `_domain_root_cause` skips the THROW text as cascade noise, the governed class is LOST |

A caller VALUE the engine echoes decides the served class — am-35 §2's property, verbatim — through two text
markers that are NOT in am-35's enumerated list: `_RETRYABLE_CONFLICT_MARKER` (read by the RETRY DECISION,
`is_retryable_conflict_error` / `_rollback_verdict`, BEFORE the classifier ever runs) and `_DOMAIN_CASCADE_MARKERS`
(read by the ROOT-CAUSE SELECTOR `_domain_root_cause`). **Measured too (`probe_conflict.py`, §A.2): on 3.2.4 BOTH are
TYPED on both paths** — the genuine retryable conflict is `kind: Query`, `details.kind: TransactionConflict` (sdk:
`QueryError`, same details); every cascade notice is `kind: Query`, `details.kind: NotExecuted`. So am-35's own rule
("typed wherever the engine types it") would close both doors.
- **Reading A (my pick):** the gated KB class pin's phrase domain = the CLASSIFIER's class markers (am-35 §2 item 3's
  enumeration: the U prefix, governed, ASSERT, coercion, recursion) + every live host's own engine text; the retry and
  cascade doors are a **pinned KNOWN BOUND** (pin-the-miss, GREEN today and on a correct am-35 build, RED the day the
  retry decision / root-cause selector is typed) with the re-open trigger named in the pin.
- **Reading B:** the gated domain is every text marker in `_txn` that decides the served class; the builder types the
  retry decision (`details.kind == "TransactionConflict"`) and the cascade selector (`details.kind == "NotExecuted"`).
- **Why A:** am-35 §W names the classifier and its two raise sites; the retry decision + root-cause selector are the
  SHARED retry seam every one of the eleven seams rides (#102/#120), whose existing pins mutate
  `_RETRYABLE_CONFLICT_MARKER` and expect detection to move — widening it in the round am-35 §0 declares the LAST
  would put the builder between a new gate and ~a dozen existing required-green pins. **Recommendation to the
  sidecar: rule B as its own small item (the typed signals exist, measured) — it is a real defect: a hostile value
  buys 2 s of engine retries per call and serves contention-exhausted for a domain rejection.** Escalated.

### FK-a28c-2 — am-34 §2's model validator vs a28's by-annotation pin (1) Literal swap
am-34 §2 makes contradictory `(owned_but_unscoped_agents, distinct_owner_principals, owner_classification)` triples
UNCONSTRUCTIBLE (a model validator), and in the same breath says pin (1) "swaps a Literal to ANOTHER member — for
`empty` the swap must ADD the owner sentence". Pin (1) perturbs THROUGH the model's constructor (a subclass with a
`before` validator), so the inherited invariant validator REFUSES every swap that crosses the empty/non-empty line:
`"empty"` (count 0) → any other member raises, and `"unclassified"` → the next member in order (`"empty"`, count 3)
raises. Two readings: (A, my pick) the swap target is the NEXT LEGAL member — derived by constructing (the first member
after the current one, cyclically, that the model accepts beside the population's other served fields); a population
with no legal alternative (`"empty"`) has no swap case, and am-34's "empty adds no sentence" is pinned DIRECTLY
(an `"empty"` reason carries none of the ruled owner-sentence stems, the stems themselves proven non-vacuous against
every non-empty population's served reason); (B) pin (1) bypasses the validator (`model_construct`) — rejected: the
production path never bypasses it, so the perturbation would serve a state the build cannot serve.

### FK-a28c-3 — F-5 "exactly ONE store read (INFO FOR DB)" on which store shape
am-34 §4: "Pin, generated over `tables × {undefined}`: the typed answer, AND exactly ONE store read (INFO FOR DB)".
With the target undefined but `agent` DEFINED, the verb's precondition legitimately reads the agent facts (am-32 §2),
so "exactly one" is false there for `--table memory|message`. Two readings: (A) one read TOTAL, on a store where every
read the precondition would gate is also off; (B) no statement touches the undefined table and the LEG adds no read.
**Pick: both, as two generated legs** — (A) on the minimal shape (the target undefined AND `agent` undefined: exactly
one driver call, and it is `INFO FOR DB`), (B) on the realistic shape (only the target undefined: `INFO FOR DB`
exactly once, no statement names the target table, no leg call after the precondition's). Both are satisfied by the
build am-34 describes; a build that probes the table or mints the project keep first reds both.

### FK-a28c-4 — `MigrateGovernedResult.table_defined: bool` on a result that never read `INFO FOR DB`
The invalid-`--table` refusal reads nothing (a19a: zero store I/O), so `table_defined` there describes no
measurement — `True` or `False` is a served claim about an unread fact (the consumer law; am-32 §2.1's "None iff not
read" is ruled for the COUNTS model, not this field). am-34 rules `bool`. **Pick: pin the ruled `bool` only where it
IS measured** (the undefined cells: `False`; defined proceeding cells: `True`); the invalid-table value is NOT pinned
and is surfaced here for a ruling (`bool | None` would be the consumer-law-consistent shape).

### FK-a28c-5 — am-35 §3's restored F-4 quantifier: "every `except` clause whose caught closure contains exhaustion … must be a bare `raise`"
Literally, the DOOR handler itself (`except SurrealStoreError`) "contains exhaustion" in its caught closure and is not a
bare raise — the sentence would red every correct build. "The OLD pin's quantifier" (d334042) quantified over clauses
NAMING exhaustion, anywhere in the door's function. **Pick: every clause exhaustion REACHES** — per `try`, the first
clause whose caught classes admit `TxnContentionExhaustedError` (a Tuple element, a named subclass, a superclass or a
bare `except:` alike, resolved by import) — anywhere in a listed door's FUNCTION, must contain only a bare `raise`.
Measured at HEAD (§A.3, `f4_measure.py`): every reached clause in all six door functions IS a bare raise (GREEN), and
S8 (a second `try` whose exhaustion clause re-reads and returns) is reached → RED. Strictly wider than the old pin
(names ⊂ reached) — DUAL row D-6 below.

### FK-a28c-6 — the per-HANDLER key (am-35 §3) vs packet 58-r3's COMMITTED, frame-keyed CAS population pin
`test_reanchor_58_r3_cas_seam.py::listed_handlers()` (committed `7130508`) reads the exact sets' KEYS and pairs
them with drivers and call-graph verbs keyed `"<file>::<function>"` (the runtime instrument is frame-keyed by
nature). Re-keying the exact sets per handler (`file::function::<n>`) therefore REDS 58's own currently-green
population rows (every listed 58 door gains a `::1` twin with no driver, and its function-keyed driver goes "stale").
Readings: (A, my pick) the scanner owns the key FORMAT, so it exports ONE accessor (`_handler_function`) and 58's
`listed_handlers()` maps through it — a one-line edit to 58's committed file, a regression my in-scope change directly
causes (brief-base §2 exception), **disclosed as deviation D-5**; the 63c drivers are then keyed by FUNCTION, as every
58 driver is. (B) leave 58's file alone and key the 63c drivers per handler — 58's own rows stay red until 58-r4.
A leaves the fleet greener and keeps the key format in one place.

### FK-a28c-7 — am-34 §5's "exactly one scanner function": which candidate property
am-34 §5 derives candidates as "every test-tree function whose body both walks `ast` over production files AND names a
class from `_txn`'s `SurrealStoreError` tree". At HEAD (§A.4, `cand.py`) that property yields FOUR functions, two of
which scan statement LITERALS for the envelope instrument (`_bare_query_multi_statement_literals_in`,
`test_the_offline_leg_shares_the_txn_predicate_by_mutation` — they name `TxnEnvelopeViolationError`, never a catch
clause) — so the literal pin reds a correct build. 58 am-7 §3 item 4 (its origin) says "exactly ONE function in the
test tree resolves caught classes by import". **Pick: the two derived legs together** — (i) catch-clause scanners: a
function that walks `ast` AND inspects catch clauses (`ExceptHandler` / `Try` / `TryStar` / `.handlers` / the
`_catch_sites` walker) AND names a `SurrealStoreError`-tree class → allowlist exactly the CAS-domain function; (ii)
resolvers: a function that evaluates an `except` expression in a module namespace (`eval(compile(ast.Expression…)))`)
→ allowlist exactly `_catch_sites.resolved_by_import`. Each leg has a positive control (a synthetic second scanner /
resolver in a scratch module is seen).

### FK-a28c-8 — the LEG-level unresolved-operator refusals keep "(N principals, M admins)" as non-field integers
am-34 §3 makes `total_principals` / `admin_principals` fields, "`None` iff operator resolution was not attempted (it
runs only when the owned-but-unscoped set is non-empty)" — i.e. the PRECONDITION's resolution. The memory / agent /
message LEGS also resolve the operator and serve `_operator_unresolved`'s "(N principals, M admins)" on a proceeding
store with an ambiguous operator; those integers are no field. **Pick: the parenthetical, literally** (fields = the
precondition's resolution; pin (2) holds ∀ its populations, the unclassified carve-out removed). Surfaced: by am-34's
own rule ("measured integers an agent acts on … are fields") the leg sentences are the same class — a sidecar item.

### RULED 2026-09-27 by amendment 36 (`547f63d`, relayed by lead directive #17117, acked)
FK-a28c-1 → **Reading B, IN a28c** (typed retry decision + typed cascade selector, ONE parse per failed statement,
both text markers deleted, KB over the whole reader set, the marker pins re-keyed by DUAL, an exact-set pin over
`_txn`'s text readers, the Internal-label bound) · FK-2 A · FK-3 both legs · FK-4 → **`table_defined: bool | None`**
(`None` on the unread refusal) · FK-5 "reaches" · FK-6 one accessor (D-5 stands) · FK-7 the two derived legs · FK-8 →
**the operator counts are FIELDS for every population, through ONE resolver** (precondition OR leg). Everything
below is written to am-36; my picks that am-36 reversed (FK-1, FK-4, FK-8) are superseded where they appear above.

### FK-a28c-9 (NEW, raised by folding am-36) — the recursion-depth rejection is NOT `kind: Internal`
am-36 §1.1: *"text ONLY for `kind: Internal`: the U prefix, ASSERT, coercion, recursion-depth"*. **Measured
2026-09-27 on 3.2.4 (`probe_kinds.py`, §A.2b): the recursion-depth parse error is `kind: Validation`** —
`ValidationError`, `details: null`, "Parse error: Exceeded expression recursion depth limit …" on the `query()` path,
and an RPC-level `error` (`kind: Validation`) on the `query_raw` path. A build that follows the letter (text only for
`Internal`) loses #66's "query too complex" teaching label on `run_query` — and the existing #66 pin
(`test_surreal_store.py` `… == _ERROR_CLASS_QUERY_TOO_COMPLEX`) feeds the classifier that engine text. Readings:
(A, my pick) the text branch is reachable ONLY for the kinds whose engine typing does not decide the label —
measured: `Internal` (U, ASSERT, coercion) and `Validation` (recursion depth); the exact-set pin's positive control
iterates EVERY OTHER SDK kind; (B) the letter — the recursion label is lost. A keeps the property (text never
decides where the engine types) and the #66 teaching. **Side observation (pre-existing, not 63c's):** on the
transactional path that RPC-level Validation error is raised by `check_response_for_error` inside
`_txn_query_raw`, whose `except (*_CONNECTION_ERRORS, KeyError)` catches it as a SurrealError and serves
`SurrealConnectionError` + drops the healthy connection — a parse error reported as transport. Surfaced, not pinned
(outside am-36 §W).

## §0 Capability check (brief-base §4) + the brief's own conflicts
- **brief-base v17 read in full; brief project v7 acked on register.** lore registered (`contract-63c-i-a-a28c` /
  `63c-20260924` / contract / `≤20m`); heartbeats per milestone; ONE signal on thread `63c` (#17115, the forks).
- **ROLE BOUNDARY:** no forbidden transfer in the brief. I did NOT replay the adversary's wrong builds; every
  mutation below is my own (§6). No `BRIEF CONFLICT`.
- brief-base §2 "never commit" vs the brief's ONE commit: the brief wins (precedence) — stated.
- **lore tools:** `lore_search`/`lore_get_symbol` were NOT used for code structure — every structural read was
  `awk`/`sed`/`Read` over the files the rulings name (the adversary and am-35 did the same; grep/rg are hook-blocked,
  #473; `scripts/` is not in the graph, #507). Fallback SAID here. The DRY-ledger look-ups DID use `lore_search`: two answered after >120 s, one was aborted
  after 300 s of silence — filed as finding **#516**.
- Required first read: `docs/reference/surrealdb-31-capabilities.md` — §3 (statement[0]-only validation: every
  setup statement in my pins is one per call) and §5 (≥8-way + 20 consecutive) are what my pins lean on. Every
  store touch ran on the TEST store `ws://127.0.0.1:18000` (`surrealdb 3.2.4`); `:18500` never touched; the TEI
  embedder never called (FakeEmbedder harness).
- **Trees (scratch, `scripts/scratch_copy.sh`, then `git reset --hard HEAD && git clean -fd` in each copy — the main
  tree carries #486's and 64b-r2's uncommitted work, which my trees exclude):**
  `base` = HEAD `6bb95af` (production byte-identical to `169925f` except `testing/loopback.py` — #466's committed
  loopback fix, not 63c; `git diff --stat 169925f -- loremaster/loremaster` names that one file) + my contract files
  (the eight committed here + the §HELD harness patch);
  `ref` = the same + my reference build. `loremaster.__file__` (scratch_copy's own assertion):
  `…/scratchpad/ref/loremaster/loremaster/__init__.py` and `…/scratchpad/base/loremaster/loremaster/__init__.py`.
- **Reference build (a SAT / mutation HOST, not a spec):** the a28 author's `reference_fix.patch` (extracted from
  `REPORT-contract-63c-i-a-a28.md` §A.3, md5 `0abdf6d8…` = its stated md5) + the a28b author's interdiff (§A.2 of
  `REPORT-contract-63c-i-a-a28b.md`; my extraction's md5 differs from the stated one by fence handling — CONTROLLED by
  running the five a28b-era contract files on the result: **924 passed**, the adversary's exact SAT-1 count) + my
  FOUR deltas, in order — `myref_a28c_txn.py` (am-35 §2), `myref_a28c_migrate.py` (am-34 + am-35 §4),
  `myref_a28c_am36.py` (am-36 §1: typed retry / cascade decisions, ONE parse, typed-first classifier) and
  `myref_a28c_fk8.py` (am-36 FK-4 + FK-8) — all verbatim in §A. A reference is a SAT / mutation HOST, never a spec.

## §1 Required-green enumeration (written BEFORE the pins; re-checked by §8 SAT)
A correct a28c build keeps GREEN:
1. **Single-principal stores unchanged** — the a28/a19a clean-store legs, the gating pin's `both-defined` cells, the
   success legs: they proceed and serve MEASURED counts (now `owner_classification == "empty"`; the operator counts
   are the measured principal / admin totals, because the legs resolve the operator — am-36 FK-8; `None` only where
   no resolution ran on the call).
2. **The existing contract as amended** — a19 / a19a / a19b / a28 (DUAL rows §5) / a28b / `test_retry_seam.py`
   (scanner DUAL rows §5) / `test_agent_governance_63c_i_a.py` / `test_agent_registry.py` / `test_keeps_store.py` /
   `test_surreal_store.py` (the anchored governed test is required-green-safe: of the 31 `governed_conflict:` lines in the
   test tree (§A.6), the three FORGED engine texts (`test_surreal_store.py`'s two governed rollbacks + my
   `_HOSTILE_TEXTS["governed"]`) all carry the engine's `An error occurred: ` THROW prefix; every other is a LIVE `THROW` the engine wraps itself, prose, or a leak-absence assert) — on BOTH helper shapes (`_governed_world` for the migrate half, `credentialed_app_context` for
   the register half; every new pin uses one of the two, never a third).
3. **B13 — a multi-keep member is ALLOWED**: a principal householded in THIS keep who also keeps and/or belongs to
   other keeps proceeds, in both mint orders (C2 class pin, 8 proceed cells; KC ×4).
4. **The driver's other classes unchanged**: `TxnGovernedConflictError` for a real governed THROW (KB-widened governed
   host); an ASSERT / coercion rejection EXACTLY the base class (KB-widened, a28b (a)(b) controls); transport /
   exhausted contention unchanged (a28b K4, keeps twin passthrough, the three CAS identity legs).
5. **The retry / cascade machinery on every GENUINE conflict and rollback (am-36):** `test_retry_seam.py`,
   `test_surreal_store.py`, `test_txn_contention.py`, `test_scout.py`, `test_comms_await.py` and (with the §HELD
   patch) `test_surreal_harness.py` stay green — the typed kind and the engine text agree on every genuine shape on
   3.2.4 (measured), so no behaviour on a real conflict changes; only the fixtures that FORGED a text-only shape are
   re-keyed (§5 U-15…U-22).
6. **Packet 58's committed pins**: `test_reanchor_58_r3_cas_seam.py`'s population pin keeps every row it had green
   (the D-5 accessor maps the per-handler keys back to frame keys) and now ALSO passes the three 63c rows it
   routed here (FK-r3-4) — measured green at `169925f` too (§8).
Receipts: §8.

## §2 Per-item table (am-35 §W, then am-34 §W, then the adversary's MPs, then the lead routing)
File **C** = `test_fixwave_a28c_63c_i_a.py` (NEW), **B** = `test_fixwave_a28_63c_i_a.py`, **RS** = `test_retry_seam.py`,
**58** = `test_reanchor_58_r3_cas_seam.py` (one-line D-5).
| item | pin(s) | generated over (source of truth) · completeness | wrong build killed (§6) |
|---|---|---|---|
| am-35 §1 pin 1 — C2 class pin (STRIKE 3 of 3 in its docstring) | C `TestTheGateIsTheVisibilitySeam63cIAa28c::test_am35_1_1_the_register_proceeds_iff_THIS_keep_is_visible[<set>-<order>]` (16) | the relation DOMAIN generated as `{member,keeper}×{this,other}` minus the minting keeper-of-THIS → powerset (8) × both mint orders × every `a28._FOREIGN_PROBES` kind; verdict DERIVED (`member-of-this ∈ S`); the fixture checks the seam's own answer == the keeps the relations reach · `test_am35_1_3_…constructible…` (the domain is the store's public verbs; 2^3 sets) | MG2 (B13, `min(visible)`): 3 class cells + KC ×2, EXACT |
| am-35 §1 pin 2 — the seam pin, by MUTATION | C `test_am35_1_2_the_gate_READS_the_seam[hide…/show…]` | THE seam mutated at every binding BY IDENTITY (`patch_shared_object_everywhere`, expect_in `loremaster.visible_keeps`); landing asserted (#194); HIDE also requires ZERO registry queries (denied AT the gate) | MG1 (a private `list_keeps_for_member` copy in the gate) |
| am-35 §1 pin 3 — domain completeness | C `test_am35_1_3_every_relation_is_constructible_through_the_stores_public_verbs` | `KeepStore` verbs by role, signature-checked | (a vanished verb) |
| am-35 §1 pin 4 / MP-5 — KE | C `test_KE_every_registry_store_call_rides_the_one_seam` (AST-equal) | allowlist-the-safe over `agents.py`'s AST; fails closed on 0 calls | — (adversary B15; not replayed) |
| MP-2 — KC | C `TestKCAMultiKeepMemberIsNotForeign` (AST-equal) | the instance the product contains | MG2 ×2 |
| am-35 §2 item 1 — R typed on the txn path (FK-ADV-3) | C `test_am35_2_1_the_class_iff_the_sdk_says_the_record_id_is_taken_on_execute_transaction[<kind>-<wording>]` (10) | the SDK's own `AlreadyExistsError` detail kinds (a28b `_sdk_already_exists_kinds`, derived from the SDK source) × {engine, other-kind} wording, through a forged per-statement dict | MA5 (txn path classifies raw text) |
| am-35 §2 item 1 — the record TEXT pair deleted | C `test_am35_2_1_the_record_TEXT_pair_is_deleted…[run_query/execute_transaction]` | both raise sites, untyped record wording | MA4 |
| am-35 §2 items 2–3 — U anchored + first; every marker; KB widened | C `TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am35_2_3_an_echoed_phrase_never_moves_the_hosts_class[<host>-<phrase>-<path>]` — **SUPERSEDED by the am-36 row below** (renamed `test_am36_1_2_an_echoed_phrase_moves_nothing`, same class; the old id no longer exists) + `…_every_classifier_label_is_hosted_or_exempt_with_a_reason` + `…_the_phrase_domain_is_derived_and_non_vacuous` | HOSTS: every live echoing rejection shape (5); PHRASES: every host's OWN engine text captured live + every `*_MARKER` / `*_MARKERS` / `*_MARKER_PAIRS` constant in `vars(_txn)` (bounded markers excluded, FK-a28c-1); expected class from the HOST; completeness vs every `_ERROR_CLASS_*` label | MA1 (U substring), MA2 (governed unanchored), MA3 (U checked last), MA4, MA5 |
| MP-3 — KB instance | C `TestKBTheClassIgnoresEchoedValues` (AST-equal) | the adversary's four hostile values | MA1, MA3, MA4 |
| am-35 §2 item 4 / MP-1 — KA | C `TestKATheOneClassifierDecidesTheTextShape` (AST-equal) | both raise sites | — (adversary B1; not replayed) |
| am-35 §2 item 4 / R-8 — the `_domain_rejection_error` mutation | C `test_am35_2_4_mutating_the_mapping_helper_moves_every_identity_leg[<situation>-<path>]` (4) | every identity situation in `a28b._SITUATIONS` × both sites; control + landing asserted | MA6 (a typed branch building the class directly) |
| am-35 §2 item 5 — pin-the-miss | C `test_am35_2_5_KNOWN_BOUND_every_live_shape_opens_with_its_engine_noun[<shape>-<sdk/txn>]` (12) + `…_a_unique_index_collision_is_untyped_on_the_transactional_path` | the live shapes × both paths; strike count in the message | (an engine upgrade) |
| am-36 §1.2 pin 1 — KB over the WHOLE reader set (FK-a28c-1 ruled IN) | C `test_am36_1_2_an_echoed_phrase_moves_nothing[<host>-<phrase>-<path>]` (collected: **170 at base** = 5 hosts × 17 phrases × 2 paths, **130 on the reference** = 5 × 13 × 2 — the four text markers the build DELETES leave the derived domain; the engine's own conflict + cascade texts stay in it) + `…_the_phrase_domain_is_derived_and_non_vacuous` | PHRASES += the engine's own conflict + cascade texts (`_engine_shapes`, measured); asserts class + exactly ONE attempt (a spy on THE driver `retry_on_conflict`) + elapsed < ½ the retry deadline + the same `statement N of M` root cause as a plain value on the txn path | R2-MR1 (retry decision reads text), R2-MR2 (cascade selector reads text), R2-MA1…MA5 |
| am-36 §1.2 pin 3 — the exact set of engine-text readers | C `TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c` (exact set + a synthetic positive control + the SDK-kind non-vacuity + 30 generated cells) | DERIVED from `_txn`'s AST, ALLOWLIST-THE-SAFE (D-12): EVERY function performing any membership / prefix / suffix / search / `re` test, whatever it tests and wherever the `str()` happened; the four legitimate testers allowlisted, each with its reason, exactly ONE of them (`_classify_engine_error`) an engine-text reader; the positive control runs THROUGH the derivation on synthetic source (a `str(error)` reader, a `text: str`-parameter helper — `169925f`'s own shape —, a prefix reader, a `re` reader, a method; not a typed `==` decision nor a caller that only stringifies); the typed-kind control iterates EVERY SDK kind (`surrealdb.errors.KIND_TO_CLASS`) outside {Internal, Validation, Thrown} × every untyped label's words (FK-a28c-9) | R2c-MR1 (retry reads text), R2c-MR2 (a prefix-anchored cascade reader — structural only), R2c-MR3 (`169925f`'s shape: a `text: str` helper, the `str()` in its caller — invisible to the FIRST derivation), R2-MA2 (text decides for a typed kind) |
| am-36 §1.2 pin 4 — the Internal-label bound | C `TestTheInternalLabelBound63cIAa28c` (pin-the-miss + the untyped premise) | order-agnostic (open iff one direction moves the label) | (the day the engine types ASSERT / coercion) |
| am-36 §1.1 — the typed-cascade engine premise | C `test_am36_1_1_KNOWN_BOUND_every_cascade_notice_is_typed_NotExecuted` | the live COMMIT cascade | (an engine change) |
| am-36 §1.2 pin 2 — the marker pins re-keyed by DUAL | RS `TestDetectionFollowsTheOneSharedMarker` & co. mutate `_RETRYABLE_CONFLICT_KIND`; every forged response in RS / `test_surreal_store.py` / `test_txn_contention.py` (and the §HELD harness) carries the engine's typed fields, built in ONE place (`_engine_shapes.py`, NEW) | the forged shapes derive their kind from the MEASURED engine text (`typed_err_entry`) | R2-MR1 (the detection pins red when detection reads text again) |
| am-35 §3 — the scanner keyed per HANDLER; MP-4 / KD | RS `_cas_handlers_in` (per-handler key on THE ONE walker `_catch_sites.catch_sites_in`), `_handler_function`; the two exact sets re-keyed `::1`; `TestTheIndexIsKeyedPerHandler63cIAa28c::test_KD_every_domain_handler_is_its_own_entry` (adapted, §4) + `…two_domain_handlers_in_one_function_are_two_entries` (S7/S8/S4 synthetic) | the whole production tree (THE ONE walker + resolver, folded from 58 §HELD part 2); KD counts with the ONE predicate into a LIST | MS1 (S8), MS3 (S7) |
| am-35 §3 — F-4 scope restored (DUAL D6) | RS `test_the_transactional_doors_never_re_read_after_exhaustion[<door>]` (re-keyed: every clause exhaustion REACHES in the door's FUNCTION) + `…_the_F4_quantifier_sees_every_try_of_the_function` | the canonical doors × every `try` of the function (FK-a28c-5) | MS1 |
| am-35 §3 — R-2 (inline `SELECT` re-read) | RS `_is_domain_handler` (`_issues_a_read(handler)`) + the synthetic S4 leg | — | MS2 |
| am-35 §3 — S1–S3 bound stated | RS §8c header + `_discover_cas_handlers` docstring (pointer: 58 am-10, `test_exhaustion_fates.py`) | not re-pinned (brief item 5) | — |
| am-35 §4 / R-4 — derived read tags | B `_RULED_FIELD_SPEC` gains the ruled read tag per field; the shape pin checks it; the gating pin and its completeness leg read the TAGS (`_read_tag`); `_read_of` deleted | `model_fields` × `json_schema_extra["read"]`; untagged/unknown-tag field reds by name; each gated read owns ≥1 field | MM5 (a wrong tag) |
| am-34 §2 — `"empty"` + the validator | B `_OWNER_CLASSIFICATIONS` + `"empty"`; P_message / RS-1 / clean-memory / message-leg / success expectations → `"empty"`; C `TestTheOwnerTripleIsConsistentByConstruction63cIAa28c` (54 generated triples + non-vacuity) + `TestEmptyContributesNoOwnerSentence63cIAa28c` (stems proven non-vacuous against every classified population) | the enum (from the RULED spec) × {None,0,>0}² | MM1 (no validator), MM8 (empty adds a sentence) |
| am-34 §2 — pin (1)'s swap vs the validator | B `_perturbed_value(model, field, data)` swaps to the next LEGAL member (FK-a28c-2) | derived by construction | (MB4-class builds via the swap) |
| am-34 §3 + am-36 FK-8 — the operator counts are FIELDS for EVERY population (precondition OR leg), no carve-out | B `total_principals`, `admin_principals` (tag `operator`) in every population; `_UNCLASSIFIED_POPULATION` merged into `_POPULATIONS`; NEW `P_leg_unresolved` (a leg-level unresolved operator — pin (1) and pin (2) run on it); "stated" for the two counts DERIVED from the ruled resolution rule over the two fields (`_operator_counts_describe_an_unresolved_operator`); the gating pin's operator read OBSERVED (a spy on the principal listing the resolver performs); the success / clean-memory expectations measured (the legs resolve) | `model_fields`; the populations; the resolution rule | R2-MM3 (counts measured without a resolution), R2-MM4 (a leg's sentence not from the fields) |
| am-34 §4 — F-5 (+ am-36 FK-4) | C `TestAnUndefinedTargetTableIsATypedAnswer63cIAa28c` (defined_tables shape + 6 generated cells + the CLI render ×2 + `test_am36_FK4_table_defined_is_None_when_INFO_FOR_DB_never_ran[<name>]` ×28); B's gating pin re-keyed (never raises; `table_defined` == target defined) | `{agent,memory,message}` × {minimal, realistic} (FK-a28c-3); a driver spy on every binding of the three driver seams; the invalid names DERIVED from the emitted schema (a19a `_invalid_table_names`) | R2-MM6 (branch deleted), R2-MM6b (True on the unread refusal), R2-MM7 (render keyed on counts) |
| am-34 §5 — "exactly one scanner function" | RS `TestThereIsExactlyOneCatchScanner63cIAa28c` (2) | every tree THE ONE parser reaches (`include_scripts/tests/testpaths`); allowlist {`_catch_sites.catch_sites_in`} and {`_catch_sites.resolved_by_import`} (FK-a28c-7); synthetic positive control | MT1 (a second scanner in the test tree) |
| lead routing FK-r3-4 — 3 CAS drivers | C `CAS_SEAM_DRIVERS` {`agents.py::register`, `keeps.py::get_or_create_keyed`, `floor_calibration/store.py::record_measurement`} + `TestThe63cCasHandlersPropagateExhaustionAsTheSameInstance63cIAa28c` (runs them: 58's own injecting wrapper via THE shared sweep; identity leg + a REAL-loss control each) + a both-ways completeness vs the 63c-owned listed handlers | the exact sets (through `_handler_function`) | MC3 (RS-5 translates exhaustion) |

## §3 AST receipts — the landed kill probes vs the adversary's §A.5 (with a control)
Instrument `ast_receipt.py` (§A.10): the probe file extracted from the COMMITTED `REPORT-adversary-63c-i-a-a28b.md`
§A.5 (md5 `7d48312500dc1269352e0eeb9155da10` = the report's stated md5), every top-level def / class / assignment
compared by `ast.dump` (docstrings stripped, no positions) against the same name in C, then RS:
- **EQUAL (C):** `TestKATheOneClassifierDecidesTheTextShape`, `_HOSTILE_SETUP`, `_HOSTILE`,
  `TestKBTheClassIgnoresEchoedValues`, `_NOT_FOREIGN_PLUS`, `TestKCAMultiKeepMemberIsNotForeign`, `_SEAM_CALLEES`,
  `_SEAM_OWNERS`, `test_KE_every_registry_store_call_rides_the_one_seam`. (C imports `_txn` as `from
  loremaster.store import _txn` — the same bound name, so the bodies are AST-identical; ruff's PLR0402 forbade the
  alias spelling.)
- **DIFF (declared, §4 D-1):** KD — `_domain_handler_count` and `test_KD_…` landed ADAPTED in RS (as a method of
  `TestTheIndexIsKeyedPerHandler63cIAa28c`, counting with THE index's own walker + predicate).
- **CONTROL:** one Compare operator of the landed KC flipped in memory (`--control`) → `DIFF
  TestKCAMultiKeepMemberIsNotForeign` — the instrument sees a change.
- Lint-clean rewraps of the landed probes: `ruff format` only (AST-invariant); the `# noqa: F811` on each
  `admin_db` parameter moved onto that parameter's own line (comments are not AST).

## §4 DEVIATIONS
- **D-1 KD adapted, not AST-equal.** The adversary's `_domain_handler_count` re-derived the domain predicate inline
  (its own `Try` walk, its own re-read test). Landing it verbatim would (a) put a SECOND copy of the domain
  predicate in the test tree — which drifts the moment R-2 widens the predicate (the verbatim KD does not see an
  inline `SELECT` re-read, so it would red a correct build the first time one lands), and (b) be a second catch
  scanner, which am-34 §5's own pin must then red. The landed KD counts with THE index's walker
  (`_catch_sites.catch_sites_in`) and THE ONE predicate (`_is_domain_handler`) into a LIST, so it asserts exactly
  what MP-4 names — no key collapses two handlers. Kill re-proven: the synthetic S7/S8 pin
  (`…two_domain_handlers_in_one_function_are_two_entries`) and MS1/MS3 (§6). ⚠ Its `>= 8` floor (verbatim) reds at
  `169925f` (7 domain handlers: RS-5's typed catch is unbuilt) — the RED reason is the domain's, stated.
- **D-2 the scanner FOLDS 58-r3 §HELD part 2's compatible half** (brief COLLISIONS: "fold the compatible parts"):
  the index imports THE ONE resolver (`_catch_sites.caught_classes`) and walks THE ONE walker
  (`catch_sites_in` — `try*` handlers included), and is split into `_production_module_trees` /
  `_is_domain_handler` / `_cas_handlers_in` / `_handler_function`. What 58-r4 must still re-derive: §FLAGS F-1.
- **D-3 KB widened is GENERATED on phrases the engine authors, not only on hand-picked hostile values** — the
  adversary's four KB legs land verbatim beside it (the instance); the class pin derives its phrase domain from
  each host's own live text + every driver marker constant, so the builder's marker NAMES are irrelevant and a new
  marker joins unedited.
- **D-4 the forged `MigrateGovernedResult` in the CLI render pin is built through an `Any` alias** — the ruled
  `table_defined=` keyword would otherwise add a SECOND mypy line per file (a `call-arg` form the registry's symbol
  matcher does not key on); the static ownership stays the ONE `TYPE_CHECKING` reference (instance form, like a28's).
- **D-5 a one-line edit to packet 58's COMMITTED `test_reanchor_58_r3_cas_seam.py::listed_handlers()`** (brief-base §2
  exception: a regression my in-scope change directly causes). The per-handler re-key would otherwise red every 58
  listed-door row that is green today (their frame-keyed drivers go "stale", a `::1` twin has no driver). The edit
  maps each exact-set key through the scanner's OWN accessor `_handler_function` (the key format is read back in
  ONE place). Measured at `169925f`: 58's population pin reds on exactly its own two rows (`tasks.py::claim_task`,
  `tasks.py::_reanchor_stragglers` — STALE until 58's build) and nothing else (§8).
- **D-6 the three CAS drivers run through 58's injecting wrapper WITHOUT `DriverSeamInjection.install`** —
  `install()` asserts that some class holds 58's shell `_guarded_append_fragment`, unbuilt until 58's build, and
  none of the three 63c handlers rides that shell. `_arm_the_driver_seams` wraps every binding of each driver seam
  with 58's OWN `_seam_wrapper` through THE shared by-identity sweep (`patch_shared_object_everywhere`) — reuse,
  never a copy; the writer-attribution half (58's) is not run. §FLAGS F-3 names the one-flag API that would remove
  the private-method reach.
- **D-8 NEW support module `loremaster/tests/_engine_shapes.py`** (am-36 §1.2 pin 2's re-key): the brief lists no new
  support module, but am-36's DUAL re-key touches every forged conflict / cascade response in four files, and doing
  it per file would be four private copies of the engine's shapes (ONE IMPLEMENTATION). It imports nothing unbuilt,
  so every file stays collectable at `169925f`. The blast radius was MEASURED, not taken from am-36's "15 marker
  pins": 349 failed + 2 collection errors across the store / retry / harness suites on the am-36 reference before
  the re-key (§A.7), 0 after.
- **D-9 `test_surreal_harness.py`'s re-key is §HELD** (#486's uncommitted work owns the file): patch
  `held_harness.patch` (md5 `7343bf288709b5674761c78e07b98d0a`, verbatim §A.8) — `git apply --check` OK on HEAD AND
  on #486's working copy; 56/56 green on the reference with it applied. ⚠ #486's copy carries a THIRD
  `_RETRYABLE_CONFLICT_MARKER` mutation site the HEAD-based patch cannot see — whoever lands §HELD after #486
  commits re-keys it the same way (§FLAGS F-10).
- **D-10 the two `_FailedStatement(typed=…)` constructions in `test_surreal_store.py` go through an `Any` alias**
  and the file carries ONE `TYPE_CHECKING` reference (`_txn._RETRYABLE_CONFLICT_KIND`) — the #461 shape (one mypy
  line per ruled symbol, the registry owns the file's pending reds); a `call-arg` line would be a second form the
  registry does not key on.
- **D-11 THREE files outside the brief's named set carry DUAL re-keys** (U-25 `test_governed_migration_63a.py`,
  U-26 packet 58's `test_reanchor_58_r3_tiers.py`, U-27 packet 58's `_exhaustion_fates.py` +
  `test_exhaustion_fates.py`). All are in my writable set (`loremaster/tests/**`, committed, nobody's uncommitted
  work — `git status` clean on each before the edit). Each is a pin a CORRECT build of the rulings I folded reds
  (the SAT's ref-only set, §8), so leaving them would ship a contract no builder can satisfy (the C-DEF class).
  None changes a property; each changes a world or a forged shape so the property can still be exercised.
  U-26 / U-27 touch packet 58's files: F-13.
- **D-12 THE EXACT-SET PIN'S FIRST DERIVATION WAS BLIND TO `169925f`'s OWN READERS — found by the §RED adjudication,
  not by a grader.** It keyed on "a function that calls `str(...)` AND tests text". `169925f` spells both of its
  text readers as helpers taking a `text: str` PARAMETER (`_is_retryable_conflict_text`, `_is_domain_cascade_notice`)
  with the `str()` in the caller, so neither matched. The pin read GREEN at `169925f` while its own docstring said
  RED. The positive control could not catch it either, because it re-implemented the check inline instead of
  running the derivation. **Rewritten as allowlist-the-safe** (the forbidden spellings are unbounded; `_txn` holds
  four testers): every function with ANY membership / prefix / suffix / search / `re` test is derived, and each must
  be allowlisted with a reason. The positive control now runs the derivation itself, on synthetic source that
  includes `169925f`'s exact shape. **Receipts:** at base it reds naming BOTH readers; on the reference it is green;
  and R2c-MR3 (that shape re-introduced into the reference) reds it plus the ten KB cells, exactly as declared (§6).
  INSTRUMENT-0's question, answered late: the reach was a hidden constant ("same function"), and no test went red
  when the derived set missed a reader it should have seen.
- **D-13 A whitespace-only REFILL of my own prose** (comments + docstrings). My earlier rewrap tool had stranded
  1–2-word fragments mid-paragraph in ~140 places across my files. Tool `refill.py` (§A.10) refilled only paragraphs
  holding such a fragment whose fragment line is MINE (git diff vs HEAD), and it wrote a file only if its AST (str
  constants whitespace-normalised) and comment word stream were unchanged. **It had a bug**: docstring line numbers
  were computed once and went stale after the first refill in a file, and on `test_fixwave_a28_63c_i_a.py` the
  result did not parse, so it refused and wrote nothing. Fixed (re-derive after every refill, refuse on a parse
  failure). The proof was then STRENGTHENED, because normalising every str constant could hide a whitespace change
  inside a non-docstring string (a synthetic-source fixture): `strict_eq.py` (§A.10) compares every non-docstring
  constant EXACTLY. **All 12 files EQUAL** to their pre-refill backups, and its positive control (one extra space
  inside a non-docstring string) reads DIFFERENT. HEAD-owned paragraphs, including 58's §HELD anchor regions, were
  touched only where one of my own fragments sat inside them. The remaining detector hits are natural paragraph
  endings and split f-string fragments (identical concatenated text), each read. **Line numbers in §5's sweep tables
  were measured BEFORE this refill.** The hit content is unchanged; cite by symbol.
- **D-7 58's instrument is imported under `TYPE_CHECKING` + a local import** — a module-level import is CIRCULAR
  (58's collection-time `discovered_drivers` imports THIS module to read `CAS_SEAM_DRIVERS`, and found it
  half-initialised: measured, one red on my first reference run, §8).

## §5 DUAL — every pin deleted, re-keyed or re-worded (each carries an in-place comment) + the D6 correction
| # | site | old → new | virtue | verdict |
|---|---|---|---|---|
| U-1 | B `_RULED_FIELD_SPEC` | 8 names → annotation ⇒ 10 names → (annotation, read tag); `Literal` + `"empty"` | "the model carries exactly the ruled fields" | PRESERVED, WIDENED (am-34 §2/§3, am-35 §4) |
| U-2 | B `_OWNER_SENTENCE_STATES_N` | bool (states `distinct`) ⇒ `_OWNER_SENTENCE_STATES` (member → the count fields its sentence states) | "the prose states exactly the ruled counts" | PRESERVED, WIDENED (unclassified states the two operator counts; empty none) |
| U-3 | B `_perturbed_value` | next member ⇒ the next LEGAL member (`(model, field, data)`) | "a Literal swap moves the owner sentence" | PRESERVED; never crosses the validator (FK-a28c-2) — `"empty"`'s rule pinned directly in C |
| U-4 | B `_UNCLASSIFIED_POPULATION` | excluded from pin (2) ⇒ merged into `_POPULATIONS` | "every integer in a refusal is a field value" | PRESERVED, WIDENED — am-34 §3's hole is GONE |
| U-5 | B P_message / `_RS1_COUNTS` / `[clean-memory-proceeds]` / message-leg / success | `owner_classification: None` ⇒ `"empty"` + operator counts `None` | "None = not read" | PRESERVED — `None` keeps ONE meaning (am-34 §2) |
| U-6 | B `_read_of` + its completeness pin | NAME-SUFFIX (vacuous) ⇒ `_read_tag` (the field's own `json_schema_extra`); untagged / unknown tag reds | "each field's None-ness follows its read" | PRESERVED, STRENGTHENED (adversary-a28b R-4) |
| U-7 | B gating pin | `field != "owner_classification"` exemption + trailing `is None` ⇒ deleted; gated like every field | same | PRESERVED, WIDENED (adversary §AM34 row 2) |
| U-8 | B gating pin | `except SurrealStoreError: assert table in removed` ⇒ `table_defined is (table not in removed)`, never a raise | "an undefined target is no precondition failure" | RE-KEYED to the typed answer (am-34 §4) |
| U-9 | RS `_caught_classes` | private resolver ⇒ THE ONE resolver from `_catch_sites` | "names resolve by import" | PRESERVED (58 D-AM10; bare `except:` → `BaseException`, still outside the store domain) |
| U-10 | RS `_discover_cas_handlers` | `file::function` ⇒ `file::function::<n>` on THE ONE walker; exact sets `::1` | "every guarded CAS door is known" | PRESERVED, WIDENED (am-35 §3 / MP-4) |
| U-11 | RS F-4 `test_the_transactional_doors_never_re_read_after_exhaustion` | a28b "earlier clauses of the door's OWN try" ⇒ every clause exhaustion REACHES in ANY try of the door's FUNCTION | "a guard must re-raise, never re-read" | **RESTORED** — the D6 correction below |
| U-12 | RS the re-read definition | same-class `SELECT` method ⇒ + a `SELECT` literal in the handler's own body | "a re-read is a re-read" | WIDENED (R-2) |
| U-13 | RS §8c header prose | "`except SurrealStoreError` whose body RE-READS state (`await self._select…`)" ⇒ the derived domain, the per-handler key, the partition, the stated bounds | — | prose only (corpse — adversary-58-r2 F6's class) |
| U-14 | 58 `listed_handlers()` | read the exact-set keys ⇒ maps them through `_handler_function` | "every listed handler has a driver" | PRESERVED (D-5) |
| U-15 | RS §7 header "HONEST LIMIT … SurrealDB 3.1.5 exposes no structured conflict signal … a text marker is FORCED" | ⇒ a DUAL paragraph: FALSE on 3.2.4 (measured typed `TransactionConflict`); detection reads the kind | — | prose (corpse, measured false) |
| U-16 | RS `_LIVE_CONFLICT_DETAILS = {"kind": "NotExecuted"}` (a 3.1.5-era capture) | ⇒ `{"kind": RETRYABLE_CONFLICT_KIND}` (3.2.4) + `_CASCADE_DETAILS` | "the fake is the engine's shape" | PRESERVED, re-measured |
| U-17 | RS `_mutate_shared_marker` moved `_RETRYABLE_CONFLICT_MARKER` (text) | ⇒ moves `_RETRYABLE_CONFLICT_KIND`; the mutated conflict carries `_MUTATED_CONFLICT_KIND`; `_ConflictingConnection.conflict_kind` beside `conflict_text` | "ONE detection authority, proven by MOVING it, both directions" (am-36 §1.2 pin 2) | PRESERVED — only the thing moved changed |
| U-18 | RS `_conflict_rollback_response` (text-only entries) | ⇒ typed entries (cascade `NotExecuted`, the COMMIT the conflict kind) | "the live rollback shape" | PRESERVED (the engine never sends a text-only ERR) |
| U-19 | RS tripwire `_MARKER_NAME = "_RETRYABLE_CONFLICT_MARKER"`, `_MARKER_TEXT = "can be retried"` | ⇒ `_RETRYABLE_CONFLICT_KIND` / `"TransactionConflict"` | "no caller outside `_txn` names the detection authority" | PRESERVED, re-keyed |
| U-20 | `test_surreal_store.py` `_CONFLICT_ENGINE_TEXT` (built from the deleted marker); `_rolled_back_response` (text-only); the governed / retry `_FailedStatement` pair of `test_a_governed_conflict_rollback_is_a_domain_rejection_never_retried`; block-comment item 3 | ⇒ `_engine_shapes.CONFLICT_WORDS`; `typed_err_entry`; the pair carries the ONE parse (`typed=`); prose | "the verdict routes a governed THROW to the domain branch; a retryable conflict IS a conflict" | PRESERVED |
| U-21 | `test_txn_contention.py` `_CONFLICT_ENGINE_TEXT`, `_rolled_back_response` | ⇒ as U-20 | the #102 contention pins | PRESERVED |
| U-22 | `test_surreal_harness.py` (§HELD) `_conflict_error`, two marker mutations, the comment | ⇒ `typed_conflict_error`; `_RETRYABLE_CONFLICT_KIND`; prose | "the harness retry policy IS the seam's" | PRESERVED (§HELD, D-9) |
| U-23 | C `TestTheRetryAndCascadeDoorsAreAKnownBound63cIAa28c` (my own earlier pin-the-miss, never committed) | ⇒ DELETED: am-36 rules the doors CLOSED — KB widened asserts them shut, the text-reader exact set makes a fifth reader unrepresentable | — | dropped deliberately (am-36 §1) |
| U-24 | a28b `_raise_through(path, statement, connection, env)` | ⇒ + `params: dict | None = None` (default: none, every existing call unchanged) | — | EXTENDED (DRY: my `_raise_with` twin deleted) |
| U-25 | `test_governed_migration_63a.py::test_migrate_message_before_agent_refuses` — its world had NO `message` table, so on a correct build the am-34 §4 typed answer (`table_defined=False`, `refused=False`, ONE read) fires before the agent-first check and the pin reds (FOUND BY THE SAT: ref-only) | ⇒ the fixture applies the production `generate_message_ddl()` and seeds ONE legacy message from the NONE-owner agent (the row that would read a NONE `sender.owner_principal`) | "§2.6 agent-first ORDER: `--table message` before `agent` REFUSES and writes nothing" (the pin's own docstring) | PRESERVED — the property is unchanged; the world is now one where the ORDER can matter (am-34 §4 cited, not "the old code did it") |
| U-26 | packet 58's `test_reanchor_58_r3_tiers.py::test_exhausted_contention_rolls_back_at_ERROR` forged a TEXT-ONLY conflict (`status: ERR` + the retry words, no `kind`) — under am-36's typed retry decision it is not a conflict, so nothing retries and nothing exhausts (FOUND BY THE SAT: ref-only) | ⇒ the forged entry is built by `_engine_shapes.typed_err_entry` (same text + `Query` / `TransactionConflict`) | "exhausted contention rolls back at ERROR" (58-r3's tier pin) | PRESERVED — the forgery now has the engine's shape (a text-only ERR is a shape 3.2.4 never sends) |
| U-27 | packet 58's `_exhaustion_fates.REGISTERED_FATES` row `server.py::_comms_register` (COMPENSATION, "comms (server)", `logs>=warning`) — it registers the `except Exception` around the compensating `delete_keep`, a site no correct 63c build has (am-32 K5/K6), so the both-ways pin reds it as STALE (FOUND BY THE SAT: ref-only) | ⇒ row DELETED with an in-place DUAL comment; `test_exhaustion_fates.py` gains the runtime-inert `TYPE_CHECKING` reference (`TxnUniqueViolationError`) and a registry `files` row, so its RED at `169925f` (the site still there, now unregistered) is owned by `packet-63c-i-a-a28-contract` | "every catch site exhaustion reaches is derived or registered, and every row names a live site" (58 am-10) | PRESERVED — the fate registry stays exact over the RULED build; the row's owner is 63c's register ("comms (server)") |
| U-28 | `test_retry_seam.py` module docstring: the 3.1.5 "LIVE ERROR SHAPES" table + the NOTE "the only CONFLICT-SPECIFIC signal … is the engine's retry advice in the message text … the same marker the transactional path already keys on" (found by the am-36 sweep below, MISSED by U-15) | ⇒ a DUAL paragraph: the table is kept as dated history, the NOTE is marked false on 3.2.4, the ONE signal is the typed kind | — | prose (teaching a retired design) |
No pin was DELETED. No production-behaviour pin was weakened. **U-25…U-27 were found by the §8 SAT, not by my
sweeps** (the SAT is the instrument that saw them — §8), and U-28 by the am-36 corpse sweep below: my own U-15
fixed one stale paragraph in the same file and missed this one.

**THE D6 CORRECTION (am-35 §3, the a28b author's erratum, repaired here).** a28b's DUAL row U-9 said the F-4 re-key
was *"PRESERVED-with-pin, WIDENED … the four old doors still checked"*. That was an OVER-CLAIM: it widened the pin
over doors and Tuple guards but NARROWED it from "every exhaustion clause anywhere in the door's FUNCTION"
(`d334042`) to "the earlier clauses of the door's OWN `try`" — so adversary-a28b's S8 (a second `try` in
`findings.annotate` whose exhaustion clause re-reads and RETURNS a row, a #102 false clear) passed a28b while the
OLD pin caught it (the adversary's §A.9 receipt). **The honest a28b row is "WIDENED on two axes, NARROWED on one — a
DUAL loss".** a28c restores the function scope on the widened key (U-11): the quantifier is every clause exhaustion
REACHES in the door's function (FK-a28c-5), which is ⊇ the old pin's "every clause naming exhaustion" on every axis
(names ⊂ reached; tuples, superclasses and bare catches included) — and MS1 (S8) reds it (§6).

### P6 corpse sweep — bare, anchor-free patterns over `loremaster/tests/*.py` (awk)
Patterns: `_OWNER_SENTENCE_STATES_N`, `_UNCLASSIFIED_POPULATION`, `_read_of`, `` await self._select `` (measured
2026-09-27 on the working tree). Every hit, individually:
| hit | verdict |
|---|---|
| B:1296 `_OWNER_SENTENCE_STATES`'s DUAL comment naming `_OWNER_SENTENCE_STATES_N` | current (DUAL) |
| B:1570 the P_unclassified DUAL comment naming `_UNCLASSIFIED_POPULATION` | current (DUAL) |
| B:1269 `_RULED_FIELD_SPEC` comment "its vacuous `_read_of` are gone" | current (DUAL) |
| B:1941 `_GATED_READS` comment "(`_read_of`)" | current (DUAL) |
| `test_findings_governance_64b.py:743` `test_one_read_of_the_row_before_the_transaction` | unrelated (substring of a 64b test name) |
| `test_pdp_oracle_61b.py:621` `test_admin_read_of_audit_selects_all_rows` | unrelated (substring of a 61b test name) |
| `test_fixwave_a19b_63c_i_a.py:203` `row = await self._select_row(...)` | unrelated (a fake registry's own read) |
| RS:6797 the §8c header's DUAL quote "`await self._select…`" | current (DUAL) |
**am-36 corpse sweep** — bare patterns `_RETRYABLE_CONFLICT_MARKER`, `_DOMAIN_CASCADE_MARKERS`,
`_CASCADE_NOT_EXECUTED_MARKER`, `_CASCADE_COMMIT_ABORTED_MARKER`, `_is_domain_cascade_notice`,
`_is_retryable_conflict_text` over `loremaster/tests/*.py` + `lorerunes/tests/*.py` (main tree, 2026-09-27), and
engine-text phrases `can be retried|not executed due|cannot commit|transactionconflict|notexecuted` (case-folded)
for every FORGED shape. Every hit, individually:
| hit | verdict |
|---|---|
| C:811/813 docstring naming `_is_retryable_conflict_text` / `_is_domain_cascade_notice` | current (names the RED@`169925f` reason) |
| RS:296, RS:3673 | current (DUAL comments) |
| RS:112–133 the 3.1.5 table + NOTE | FIXED (U-28) |
| RS:310–312, 381, 390, 400 | current (typed forged shapes, DUAL-commented) |
| RS:1776, RS:9558 | current (dated measurement / audit history; the text they quote is true) |
| `test_surreal_store.py:2419–2421` item-3 comment | current (DUAL; re-wrapped — it carried an orphaned `# read the` line from my own earlier edit) |
| `test_surreal_store.py:2478`, `:2483–2492`, `:2591–2598`, `:2936–2944`, `:3399` | current (DUAL constant / measured engine text in comments) |
| `test_surreal_store.py:958–959` docstring ("a `can be retried` rollback IS a conflict … GREEN at HEAD") | FIXED — re-worded to the typed kind; "GREEN at HEAD" was FALSE (the test is RED at `169925f`, registry-owned) |
| `test_surreal_store.py:4089` `_RETRYABLE_CONFLICT_MARKER in str(...)` | current — synthetic SOURCE inside a string, a tripwire's negative control ("a raw-marker match is not a LABEL"); the name is arbitrary sample text |
| `test_txn_contention.py:101`, `:105`, `:110` | current (DUAL comment; constants routed through `typed_err_entry`) |
| `test_reanchor_58_r3_tiers.py:429` text-only forged conflict | FIXED (U-26) |
| `_surreal_harness.py:780` teardown docstring quoting the engine's retry words | current (true engine text; classification is "the seam's") — #486's WIP file, not edited |
| `test_surreal_harness.py` (HEAD) `:107` comment, `:1401`, `:1434` marker mutations | §HELD patch (D-9) re-keys all three |
| `test_surreal_harness.py` (HEAD) `:1642` `"_RETRYABLE_CONFLICT_MARKER"` in `test_the_retired_policy_constants_are_gone` | current — an ABSENCE pin (the harness must never declare it); still true and still wanted |
| `test_surreal_harness.py` (#486 WIP) `:1557` a THIRD marker mutation | §FLAGS F-10 (#486's uncommitted work; re-key when landing §HELD) |
| `test_floor_calibration_store.py:356`, `test_store_lease.py:1364` `"can be retried" not in <production source>` | current (no-hand-rolled-marker pins; stronger under am-36) |
| `_engine_shapes.py` 7–60, C:259/430/441/456–461/688/696–737/829–830 | current (the shared shapes / the a28c pins themselves) |

No assertion pins a retired name or the retired `file::function` index key (the remaining `file::function` strings
are driver / frame keys, function-keyed by design, and the synthetic `_handler_function` expectations).

## §6 Mutation proofs (declare-then-diff, BOTH ways — `scripts/mutation_proof.py` run in the REFERENCE copy, #509 content backups + byte-exact restore)
**Instrument:** `mut/drive_a28c.py` (§A.9) drives each entry of a DECLARED json through `scripts/mutation_proof.py
--file … --anchor-file … --replacement-file … --expect-red <id>…` under `guarded.sh` (15 GB watchdog, process-tree
kill by PID). Every declared id was taken from `--collect-only` BEFORE the run (collecting names tests without
running them), and the json carries its `declared_at` stamp. Before each mutation the driver copies the target file
to `<name>.backup`. After each one it `cmp`s the file against that backup and prints `restored_byte_exact` (True on
every row below). `loremaster.__file__` = `…/scratchpad/ref/loremaster/loremaster/__init__.py`, from
`scratch_copy.sh`'s own provenance assertion.

**Run 1 (declared `2026-09-27T01:03:04-04:00`; `declared_a28c.json` rewritten 01:12:27 by `declared_a28c_addendum.py`, the MG1 / MG1b re-declaration, before either of those entries ran; pre-am-36) — SUPERSEDED.** am-36 changed the reference (typed retry and cascade
decisions, one parse per statement), so the batch was STOPPED mid-run. MA1–MA6, MS1–MS3, MC3 and MM1 had held
exactly. MG1 was REFUSED by the tool (the anchor matched both gate sites, so it was re-declared as MG1 / MG1b).
MG2 held with 2 extra kills (RS-2 / RS-5), recorded as a prediction miss. The SIGKILL that stopped the batch left MM3
applied in `ref`, and it was restored from `MM3-….backup` (`cmp` = identical). No run-1 verdict is carried forward:
every mutation was re-declared and re-run as run 2 on the final reference.

**Run 2 (declared `2026-09-27T01:38:55-04:00`, final reference) + run 2b (declared `2026-09-27T01:58:58-04:00`).**
**Every one of the 25 mutations was KILLED** (≥1 declared pin red). **21 held EXACTLY** (observed RED set ==
declared). **4 differ from the declaration. Each is adjudicated below, and none is a pin gap.**
| mutation (the WRONG build) | file | declared | observed | diff (+unexpected / −declared-stayed-green) | verdict |
|---|---|---|---|---|---|
| R2-MA1 U tested as a substring, not a prefix | `_txn.py` | 10 | 10 | +0/−0 | HELD |
| R2-MA2 governed prefix tested for EVERY kind, unanchored | `_txn.py` | 20 | 19 | +0/−1 | KILLED — see (a) |
| R2-MA3 U checked after ASSERT / coercion | `_txn.py` | 10 | 10 | +0/−0 | HELD |
| R2-MA4 the record TEXT pair kept | `_txn.py` | 8 | 8 | +0/−0 | HELD |
| R2-MA5 the txn path classifies the raw text | `_txn.py` | 17 | 17 | +0/−0 | HELD |
| R2-MA6 the typed branch bypasses `_domain_rejection_error` | `_txn.py` | 1 | 1 | +0/−0 | HELD |
| R2-MR1 the retry decision reads the text marker again | `_txn.py` | 44 | 44 | +0/−0 | HELD |
| R2-MR2 the cascade selector reads text, PREFIX-anchored | `_txn.py` | 11 | 1 | +0/−10 | KILLED — see (b) |
| R2-MR2b the cascade selector reads text, SUBSTRING (base's shape) | `_txn.py` | 11 | 11 | +0/−0 | HELD |
| R2-MG1 pre-gate reads a private visibility copy | `server.py` | 2 | 2 | +0/−0 | HELD |
| R2-MG1b post-mint recheck reads a private visibility copy | `server.py` | 1 | 1 | +0/−0 | HELD |
| R2-MG2 post-mint recheck keyed on the PRIMARY keep (B13) | `server.py` | 7 | 7 | +0/−0 | HELD |
| R2-MG2b pre-gate keyed on the PRIMARY keep (B13) | `server.py` | 7 | 5 | +0/−2 | KILLED — see (c) |
| R2-MS1 S8: a second `try` in an annotate handler | `findings.py` | 2 | 2 | +0/−0 | HELD |
| R2-MS2 S4: an inline `SELECT` re-read door | `findings.py` | 1 | 1 | +0/−0 | HELD |
| R2-MS3 S7: a re-reading exhaustion clause in RS-5 | `agents.py` | 2 | 2 | +0/−0 | HELD |
| R2-MC3 RS-5 translates exhaustion | `agents.py` | 1 | 1 | +0/−0 | HELD |
| R2-MM1 the owner-triple validator removed | `governed.py` | 48 | 48 | +0/−0 | HELD |
| R2-MM3 operator counts measured without a resolution | `principals.py` | 6 | 6 | +0/−0 | HELD |
| R2-MM4 a leg's unresolved sentence not derived from the fields | `principals.py` | 2 | 2 | +0/−0 | HELD |
| R2-MM6 the F-5 branch deleted | `principals.py` | 10 | 10 | +0/−0 | HELD |
| R2-MM6b `table_defined=True` on the unread refusal | `principals.py` | 28 | 28 | +0/−0 | HELD |
| R2-MM7 the CLI render keyed on counts | `principals.py` | 1 | 1 | +0/−0 | HELD |
| R2-MM8 `"empty"` adds an owner sentence | `principals.py` | 2 | 5 | +3/−0 | KILLED — see (d) |
| R2-MT1 a second catch scanner | `_catch_sites.py` | 1 | 1 | +0/−0 | HELD |

- **(a) R2-MA2, `[AlreadyExists-governed]` declared, stayed green.** The am-36 classifier's typed `AlreadyExists`
  branch returns BEFORE the text branch, so the mutated governed test never sees that kind. My prediction was wrong
  and the cell is not vacuous: a build that orders the text branch before the typed branch reddens it. The other 19
  declared ids fired.
- **(b) R2-MR2 — the prefix-anchored text selector is effect-INVISIBLE, and the structural pin is what catches it.**
  An echoed value sits INSIDE the host's text, never at position 0, so a `startswith` selector is never fooled and
  the ten KB cascade cells rightly stay green. Only `test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier`
  can see such a reader, and it did, BY NAME. That is exactly why am-36 §1.2 pin 3 exists: an effect-neutral text
  reader is the next echoed-value defect waiting for a looser spelling. **R2-MR2b** then proves the EFFECT leg: the
  substring selector (base's shape) reddens all ten `execute_transaction` cascade cells plus the exact-set pin,
  exactly as declared.
- **(c) R2-MG2b, RS-2 / RS-5 declared, stayed green.** The pre-gate B13 mutation denies only a MULTI-keep member at
  the read-only pre-registry gate. The RS-2 / RS-5 racers are single-keep principals, so they never reach it (the
  POST-MINT variant R2-MG2 is the one that kills RS-2 / RS-5, as declared). The five C2 / KC cells fired. My
  prediction was wrong; this is not a gap.
- **(d) R2-MM8, +3 unexpected.** The anchor sits in the refusal composer, where ANY non-empty `parts` list refuses.
  Adding an `"empty"` sentence therefore also refuses the clean message leg, which three a28 success / leg pins catch.
  Both declared ids fired. The extra kills are a second, louder symptom of the same wrong build.

**Run 2c (declared `2026-09-27T03:11:26-04:00`, after D-12 rewrote the exact-set pin's derivation) — every mutation
that pin must see, re-proved on the final test file:**
| mutation | declared | observed | diff | verdict |
|---|---|---|---|---|
| R2c-MR1 the retry decision reads text | 44 | 44 | +0/−0 | HELD |
| R2c-MR2 prefix-anchored cascade reader (RE-DECLARED as the exact-set pin only — run 2's adjudicated behaviour (b); a revised prediction, stated as one) | 1 | 1 | +0/−0 | HELD |
| R2c-MR2b substring cascade reader | 11 | 11 | +0/−0 | HELD |
| **R2c-MR3 `169925f`'s exact shape** — `_is_domain_cascade_notice` stringifies and calls a module-level `_is_cascade_text(text: str)` that runs the substring test (the first derivation saw NEITHER function) | 11 (the exact-set pin + the 10 txn cascade KB cells) | 11 | +0/−0 | **HELD** — the D-12 gap is closed and mutation-proven |
All four restored byte-exact (`_txn.py` md5 `e1b8436e46f4dfa73409df2ddcb2e33e` after each).
**Totals: 29 mutations, all KILLED. 25 held exactly; 4 run-2 prediction misses, each adjudicated (a)–(d).**

## §7 Concurrency — 20 CONSECUTIVE greens on the final reference (store-ref §5)
Instrument `conc20_a28c.sh` (§A.10). It makes 20 SERIAL invocations and stops at the FIRST non-green one (a red is a
STOP). Each invocation runs a28b's concurrency set (RS-2: 20 rounds × 8-way incl. the R-1 post-mint leg; RS-5 handler
+ registry, 20 × 8; the keeps REAL unique-key 8-way) + ALL of `test_txn_contention.py` (the #102 live 16-way
contention pins, whose retry DECISION am-36 changed), under `quiet_run.sh` + `guarded.sh` (no watchdog event). The
passed-count is checked on every run (26 collected, from `--collect-only`, before the run):
```
run 1: exit=0 :: 26 passed in 12.77s      run 11: exit=0 :: 26 passed in 12.16s
run 2: exit=0 :: 26 passed in 12.18s      run 12: exit=0 :: 26 passed in 12.49s
run 3: exit=0 :: 26 passed in 12.66s      run 13: exit=0 :: 26 passed in 11.30s
run 4: exit=0 :: 26 passed in 12.15s      run 14: exit=0 :: 26 passed in 10.96s
run 5: exit=0 :: 26 passed in 12.11s      run 15: exit=0 :: 26 passed in 11.48s
run 6: exit=0 :: 26 passed in 13.28s      run 16: exit=0 :: 26 passed in 11.13s
run 7: exit=0 :: 26 passed in 13.16s      run 17: exit=0 :: 26 passed in 11.28s
run 8: exit=0 :: 26 passed in 11.77s      run 18: exit=0 :: 26 passed in 11.43s
run 9: exit=0 :: 26 passed in 12.11s      run 19: exit=0 :: 26 passed in 10.68s
run 10: exit=0 :: 26 passed in 11.90s     run 20: exit=0 :: 26 passed in 10.08s
ALL 20 CONSECUTIVE GREEN
```
Ran 03:01–03:05 on the reference, whose test files were then byte-identical to the committed ones except for the
later whitespace-only refill (D-13, `strict_eq` EQUAL) and the D-12 derivation, which runs in none of these 26 tests.
No new a28c pin is a concurrency pin: C2 / KC / F-5 / CAS identity legs are sequential or injected.

## §8 SAT — the full suite on ONE test tree, both ways (base = `169925f` production, ref = the reference build)
**Trees:** `base` = HEAD `6bb95af` (production = `169925f` except #466's `testing/loopback.py`, §0) + my test tree;
`ref` = the same test tree + the reference build (§0, §A.5). **Identical test trees**: `sync.sh` (§A.10) copies
every contract file into both, and `cmp` confirmed both before each run. The §HELD harness patch rode both SAT
trees; it is reverted in the currency tree (§9). Runner: `pytest -p no:cacheprovider -q -n 12 --tb=no -rfE` (the
fleet cap — other lore suites were live), under `quiet_run.sh` (waits for ≥24 GB MemAvailable on 3 consecutive
checks) + `guarded.sh` (15 GB watchdog; process-tree kill by PID). Neither watchdog fired on any run below.
| run | collected result (pytest's own tail) |
|---|---|
| base, full suite (`sat2_base.log`, 2026-09-27 ~02:00) | **847 failed, 11997 passed, 63 skipped, 3 xfailed** in 1095.69s |
| ref, full suite (`sat2_ref.log`, ~02:10) | **416 failed, 12392 passed, 63 skipped, 3 xfailed** in 1019.96s |

**Both-way diff** (`sat_compare2.py`, §A.10). Ids come from pytest's own `FAILED` / `ERROR` summary lines, split at
the first `" - "`. The script now ASSERTS that every summary line is accounted for: its first version filtered on a
`loremaster/` path and silently dropped the three `scripts/test_forgery_door_sweep.py` reds. It was fixed, and the
diff re-run, before any number below was taken.
- **red on BOTH: 413** — reason text compared id-by-id after normalising addresses, db names and timings:
  **identical on all 413.** So the reference changed none of them. By file: 58's family (`test_supersede_reanchor_58`
  44, `test_reanchor_58_r3_convergence` 42, `…_r2_rulings` 27, `…_r3_tiers` 16, `test_task_guarded_shell_58` 15,
  `…_r2_probes` 12, `…_r3_am6` 8, `…_r3_probes` 6, `test_task_claimable_partition_58` 5, `…_r3_cas_seam` 3 — its two
  stale `tasks.py` driver rows + one injection row, 58's own, `…_r2_am2` 3, `…_r2_scale` 2, `…_r3_relate` 2,
  `test_blocks_edge` 1, `test_task_read_surface` 1); 64b's family (`test_comms_footer` 76, `test_mcp_server` 28,
  `test_governed_substrate_64b` 26, `test_findings_migrate_64b` 26, `…_governance_64b` 24, `…_identity_64b` 22,
  `…_schema_64b` 17, `…_enforcement_64b` 4); `scripts/test_forgery_door_sweep.py` 3. **Every one is owned** by
  `packet-58-contract` / `packet-64b-i-contract` (the currency gate's partition, §9 — no RED_ORPHANED).
- **red at base, green on ref: 434** — the contract's ruled reds (a28c 247 · a28 87 · RS 69 · a28b 24 · harness 2
  (§HELD) · a19a 2 · a19b 2 · store 1); every one's reason is in §RED.
- **REF-ONLY (red on the reference, i.e. a pin a CORRECT build fails): 3 → FIXED → 0.**
  `test_governed_migration_63a.py::…::test_migrate_message_before_agent_refuses` (U-25),
  `test_reanchor_58_r3_tiers.py::…::test_exhausted_contention_rolls_back_at_ERROR` (U-26),
  `test_exhaustion_fates.py::…::test_every_non_derived_site_has_a_row_and_every_row_a_site` (U-27). **Receipt of
  the fix, on both trees, on the final files:** those three files → base **17 failed / 29 passed**, ref **16 failed /
  30 passed**. Diff: shared 16 (58's tiers reds, reasons identical), base-only 1 (the fates pin, now RED at `169925f`
  for the ruled reason and owned), **REF-ONLY 0**. The two files whose only later edits were docstrings / comments
  (`test_retry_seam.py`, `test_surreal_store.py`) on ref → **864 passed, 0 failed**.
- **FINAL both-trees run, after D-12 and D-13** (every file I touched + a19a/a19b + the retry-dependent suites
  `test_scout.py` / `test_comms_await.py` / `test_surreal_harness.py`; `final_{base,ref}.log`): base **453 failed /
  1260 passed**, ref **19 failed / 1658 passed** (the collected totals differ by exactly the a28c phrase-domain cells,
  §2, and by the harness: HEAD's copy in base, §HELD's in ref). Diff: base-only 434 (a28c 248 · a28 87 · RS 69 · a28b
  24 · a19a 2 · a19b 2 · store 1 · fates 1), shared 19 (58's tiers 16 + cas_seam 3, its own), **REF-ONLY 0**.
- **63c-attributable reds on the reference: 0.**

## §9 CURRENCY (`scripts/pending_contract_gate.py --currency`, no `-n` forwarded)
**Tree: `base` set to EXACTLY HEAD `6bb95af` + this commit's content** — my twelve test / support files byte-equal
to the main tree (`cmp`), the §HELD harness patch REVERTED to HEAD, and `scripts/pending_contracts.yaml` =
HEAD's file with ONLY my entry swapped in (the main tree's copy also carries 64b-r2's uncommitted hunk, which is
not mine to commit). Why not the main tree: it carries #486's and 64b-r2's uncommitted work, whose reds would be
attributed to this commit. Run under `quiet_run.sh` + `guarded.sh`. FIRST run 2026-09-27 02:41 (before D-12 / D-13); RE-RUN 03:27 on the
FINAL content (the tree re-synced, `cmp`-checked; same registry blob), which is the receipt:
```
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 64 residual(s), owned by: packet-58-contract … packet-63c-i-a-a28-contract … packet-64b-i-contract
  ruff         GREEN
  pytest       RED_ADJUDICATED — 847 residual(s), owned by: packet-58-contract … packet-63c-i-a-a28-contract … packet-64b-i-contract
CURRENCY   : PASS — every claimed gate is GREEN or OWNED
```
(The owner lines are 2.2 KB each, abbreviated here to the three owner ids the gate names.) **847 = the base SAT's
847 − the 2 harness reds (the §HELD patch is not in this tree) + the 1 fates pin (U-27, red at `169925f` by
ruling) + the 1 exact-set pin (D-12: now red at `169925f`, as its docstring says)** — the count reconciles (the first
run read 846, before D-12). The registry entry itself (`packet-63c-i-a-a28-contract`) gains `table_defined`
and `_RETRYABLE_CONFLICT_KIND` in its trigger, am-34/35/36 in its ruling, and three `files` rows:
`test_fixwave_a28c_63c_i_a.py` (`TxnUniqueViolationError`, `MigrateGovernedResult.table_defined`),
`test_surreal_store.py` (`_txn._RETRYABLE_CONFLICT_KIND`) and `test_exhaustion_fates.py`
(`TxnUniqueViolationError`). `--verify-registry` passes on it.

## §RED — at `169925f` (base), with reasons
**Contract files run** (`red_base.log`, 2026-09-27): `a28c`, `a28`, `a28b`, `a19a`, `a19b`, `test_retry_seam.py`,
`test_reanchor_58_r3_cas_seam.py`, `test_surreal_store.py`, `test_txn_contention.py`, `test_scout.py`,
`test_comms_await.py`, `test_surreal_harness.py` (+§HELD) → **437 failed / 1230 passed** (291.71s). Every red is in
a registry-owned file (`packet-63c-i-a-a28-contract`; `test_reanchor_58_r3_cas_seam.py` → `packet-58-contract`) or
is the §HELD harness pair. Reasons, by exception type (every non-assertion red read individually):
| file (reds) | reason at `169925f` |
|---|---|
| a28c (247 in that run; **248 after D-12**) | the ruled behaviour absent. KB whole-reader set 107: the echoed phrase moves the class / retries / shifts the root cause. KB 4 + KA 2. The text-reader class 24 = 24 of its 30 typed-kind cells (a typed error of a non-text kind is labelled by its text); the 6 green cells are exactly the `unique-prefix` ones (`169925f` has no UNIQUE label to mis-assign), and the class's three non-cell pins were green in that run (a `comm` of the red ids against `--collect-only`). **The exact-set pin was GREEN at base in that run: the D-12 defect.** After D-12 it reds, naming `_is_retryable_conflict_text` + `_is_domain_cascade_notice`. The C2 visibility cells 9 (a legal member denied / a stranger admitted). The owner-triple validator 54 (missing). `"empty"` renders owner prose 3. F-5 37: 6 undefined-table legs RAISE `TxnDomainRejectionError … governed scope count rejected`; 28 FK-4 cells serve a `table_defined` the refusal never read ("read nothing, yet served …"); the preconditions' `defined_tables` shape 1; the CLI render ×2, a `TypeError` on the unbuilt field (registry-owned static ref). The mapping helper 4 and the typed-txn record shape 2. The agents CAS driver's control leg meets an `unspecified rejection` 1 |
| a28 (87) | the typed-counts pins 42 (`TestTheMeasuredCountsAreTypedFields63cIAa28`, incl. the am-34 / FK-8 operator-count fields and `"empty"`, over every population); `table_defined` / gating (19, incl. `MigratePreconditionCounts does not exist`); wrong-shaped dependency does not fail closed (16); RS-5 / RS-2 race legs (5); message / foreign / backfill legs (5) — all a28/a28b-era ruled reasons, now with the a28c re-keys |
| RS (69) | the detection pins move `_RETRYABLE_CONFLICT_KIND`, which does not exist (33 + 32 bootstrap); the per-handler index (1), the F-4 reached-clause rewrite (2), the scout claim seam (1) |
| a28b (24) | as a28b's own §RED: C2 3, K1 1 + K6 1 (`AgentIdentityConflictError` — the gate falls through to the registry), K3 1 (`_UnbuiltUniqueViolationError`, a28b's stub), K5 3 (compensation fires), K7 1 (`unspecified rejection` on the race), K8 1, keeps CAS 5, driver typing 4 + 2, K9 domain 1, R2 created-only flag 1 |
| a19a (2), a19b (2) | a28's carried ruled reds (a28b report §2 row "19a EXECUTES golden + runtime property; 19b KP2/KP3 … yes (a28, unchanged)") |
| store (1) | `_FailedStatement(typed=…)` is a `TypeError` — the ruled carrier, registry-owned static ref (D-10) |
| 58 cas_seam (3) | 58's OWN two stale `tasks.py` driver rows + the `_reanchor_stragglers` injection row (`packet-58-contract`); the three 63c rows FK-r3-4 routed here are GREEN |
| harness (2) | the §HELD patch's re-keyed mutations move `_RETRYABLE_CONFLICT_KIND`, which does not exist — present only because the scratch trees carry §HELD |
**Final state at `169925f`** (the final both-trees run, §8): **453 red** = the 434 contract reds (a28c now 248, the fates pin
included) + 58's own 19 in its two files (tiers 16, cas_seam 3). **Added after the first run by the
SAT fixes:** `test_exhaustion_fates.py` (1) — `server.py::_comms_register` is an
unregistered SILENT site at `169925f` (U-27; owned). `test_governed_migration_63a.py` and
`test_reanchor_58_r3_tiers.py`'s re-keyed pin are GREEN at `169925f` (their properties hold there too).
**Typecheck at base** (the currency run's typecheck leg): 64 residuals, all owned. My lines are the #461 static refs
in `test_retry_seam.py`, `a28`, `a28b`, `a28c`, `test_surreal_store.py` and now `test_exhaustion_fates.py`, each
naming a ruled, unbuilt symbol.

## §P1c — REACH (every guard / scan / generated pin this fold introduces or relies on; INSTRUMENT-0's question asked of each)
| instrument | the set it must cover | reach DERIVED or hand-list? | coverage a CHECKED variable? | effect or proxy? | bound (stated) |
|---|---|---|---|---|---|
| KB widened (C) | ∀ echoing rejection × ∀ phrase × both raise sites | PHRASES derived (each host's live text + `vars(_txn)` markers); HOSTS a table of live shapes | the hosts are checked against every `_ERROR_CLASS_*` label (hosted ∪ reasoned-exempt == the labels — a new label reds by name) | EFFECT (the raised class) | a new echoing rejection kind that maps to an existing label is only covered if one of the five hosts produces it; the retry / cascade markers are the FK-a28c-1 bound (pinned) |
| typed-txn (C) | every `AlreadyExistsError` detail kind on the txn path | DERIVED from the SDK source (`a28b._sdk_already_exists_kinds`) | yes (a28b's non-vacuity leg) | EFFECT | the forged dict is the engine's shape (measured, §A.1); a real per-statement dict with no `kind` is the untyped path (pinned by the deletion leg) |
| mapping-helper mutation (C) | every identity situation × both raise sites | DERIVED from `a28b._SITUATIONS` (identity-taken rows) | landing asserted (the patched helper was called) | EFFECT | a raise site that never calls ANY helper for the base class too is still caught (the class survives) |
| C2 product (C) | ∀ caller relation sets × mint orders × probe kinds | the relation domain GENERATED (`{member,keeper}×{this,other}` minus the minting relation); probes from `a28._FOREIGN_PROBES` | the fixture asserts the seam's own answer == the keeps the relations reach; `2^3` sets asserted | EFFECT (class, text, zero registry queries) | a visibility edge other than `member_of` enters through the seam (pin 2), never this table |
| the seam pin (C) | every binding of `resolve_visible_keeps` | identity sweep (`patch_shared_object_everywhere`, expect_in the home) | landing asserted; hide leg asserts zero registry queries | EFFECT | the sweep's own bound: module-level bindings only |
| KE (C) | every store call in `agents.py` | AST allowlist-the-safe | fails closed on 0 calls | STRUCTURAL | reads via another store object — am-32's named bound |
| the per-handler index (RS) | every domain handler in the production tree | THE ONE walker + resolver (`_catch_sites`) over the whole tree; THE ONE predicate | KD: the dict size == the LIST count (a collapsed key reds) | STRUCTURAL | S1–S3 (superclass / tuple-valued / bare) → 58's fate classifier; a helper outside the class / a literal-less `SELECT` → 58's driver-seam runtime leg |
| F-4 restored (RS) | every clause exhaustion reaches in a canonical door's function | canonical doors (exact set, both ways) × THE ONE walker | the synthetic S8 control reds; the guarded door control does not | STRUCTURAL | as above |
| one-scanner (RS) | every function in every tree THE ONE parser reaches | DERIVED properties (finds catch handlers ∧ reasons about store errors; evaluates an `except` expression) | the synthetic positive control (a second walker + resolver ARE seen, a `logger.handlers` reader is NOT) | STRUCTURAL | a scanner that spells the class tree without naming it or a resolver, or resolves without `eval` |
| F-5 driver spy (C) | every store read the verb issues | every binding of the three driver seams, by identity | `INFO FOR DB` exactly once asserted (the spy is not blind) | EFFECT (statements issued) | a raw `connection.query` bypassing the driver (R4 forbids it) |
| the three CAS drivers (C) | every 63c-owned listed handler | the exact sets through `_handler_function` | both ways (`test_FK_r3_4_every_63c_listed_handler_has_a_driver_here`) + 58's population pin | EFFECT (the same instance) | a re-read that then re-raises preserves identity by design (58's semantics) — F-4 / the exact sets are that layer |
| the validator pin (C) | ∀ owner triples | the enum DERIVED from the ruled spec × {None,0,>0}² | non-vacuity: legal AND illegal per member | EFFECT (construction) | — |
| the "empty" pin (C) | every population served `"empty"` | DERIVED from `_POPULATIONS` + RS-1 | the stems proven non-vacuous on every classified population | EFFECT (served text) | a stem-free owner sentence for `"empty"` would pass (stems = am-31's ruled openings) |
| the read tags (B) | every field | the model's own `json_schema_extra` | untagged / unknown tag reds; every read owns ≥1 field | EFFECT (served None-ness) | — |
| KB over the WHOLE reader set (C, am-36) | ∀ phrase × host × path: class, attempts, elapsed, root cause | phrases DERIVED (host texts live + the engine's decision texts + `vars(_txn)` markers) | the attempt spy is THE driver (`retry_on_conflict`), counted per attempt | EFFECT | a decision reader outside `_txn` (the eleven `_query` seams call `run_query`, so they inherit it) |
| engine-text readers exact set (C, am-36) | every function / method in `_txn` performing ANY membership / prefix / suffix / search / `re` test | DERIVED from the AST — the whole tester population, never "a stringified value" (D-12: that first key was blind to `169925f`'s own `text: str` helpers, and the pin read GREEN at base against its own docstring) | allowlist of FOUR, each with a reason; unlisted ⇒ red BY NAME; the classifier's absence ⇒ red (non-vacuity); the positive control runs the derivation itself on synthetic source; SDK kinds derived from `KIND_TO_CLASS` | STRUCTURAL + EFFECT (the classifier on typed input) | a text test hidden INSIDE one of the three non-engine allowlisted testers, or at module level (runs once, at import — cannot decide per error): stated in the pin's header; the KB whole-reader pin sees its EFFECT |
| the Internal-label bound (C) | ASSERT ↔ coercion labels | the two live hosts | order-agnostic | EFFECT | it IS a bound — reds when the engine types them |

## §FLAGS — collisions (brief) and things outside my writable set
- **F-1 packet 58-r3 §HELD part 2 (`test_retry_seam.py`, md5 `986f87dff6eb7b30c2f3d42b26dca8af` — extracted from
  `REPORT-contract-58-r3.md`, md5 matches):** `git apply --check` on HEAD `90d908f` (re-checked on `6bb95af`, whose tests are unchanged there) → **OK**; on my committed file →
  **FAILS** (`patch failed: loremaster/tests/test_retry_seam.py:6783`), because I folded its compatible half (D-2) in
  the same region. **What 58-r4 must re-derive, exactly:** (a) DROP its resolver import, its `_parents_of` copy, its
  `_production_module_trees`, the `try*` walk and the `_cas_handlers_in` split — all landed here (the index walks
  `_catch_sites.catch_sites_in`, which already yields `try*` handlers); (b) its `from _catch_sites import
  suppress_calls as _suppress_calls` + `test_this_index_resolves_through_THE_ONE_resolver`: still applicable
  (`_caught_classes is _catch_sites.caught_classes` holds on my file); (c) `_SYNTHETIC_CATCH_FORMS` +
  `test_try_STAR_handlers_join_the_domain_and_the_partition`: RE-KEY the expected set to per-handler keys
  (`synthetic.py::star_door::1`, …) — `_cas_handlers_in(key, tree, module)` keeps its name, signature and 4-tuple
  values; (d) the `_TYPED_CAS_CATCHES` comment's DUAL (FK-r3-1: `claim_task` is NOT in the domain) — the sentence it
  rewrites is still in my file, untouched; (e) the §8c header: mine now carries the domain / key / partition /
  bounds prose; 58-r4 adds its FATE-RULE paragraph beside it (my header already points S1–S3 at
  `test_exhaustion_fates.py`). Order: 63c-i-a's BUILD lands before 58's (58 am-7 §0 row 2 — unchanged).
- **F-2 packet 58-r3's committed `test_reanchor_58_r3_cas_seam.py`** — D-5 edited ONE function (`listed_handlers`).
  If 58-r4 is revising that file, it rebases onto this commit (a 7-line hunk).
- **F-3 packet 58's `DriverSeamInjection.install`** asserts a shell holder before it wraps the driver seams, so a
  driver for a handler that never rides the shell cannot use it until 58's build. Suggested for 58-r4 (not made):
  `install(monkeypatch, *, observe_shell: bool = True)`; my `_arm_the_driver_seams` would then call it and stop
  reaching `_seam_wrapper` (a private method) — D-6.
- **F-4 packet 58's NEW THROW markers** (`claim_lost:`, `cas_lost:`, `reanchor_straggler:`, `heal_chunk:` — 58's
  build): the KB-widened phrase domain derives EVERY `*_MARKER` constant in `_txn`, so the day 58 lands them they
  join the gated domain, and am-35 §2 item 3 ("∀ text markers — anchored or checked last") binds them: a 58 marker
  checked position-free BEFORE the anchored U / governed tests would red my pin for the right reason. The 58 builder
  must anchor its app-THROW prefixes at the engine's `An error occurred: ` exactly like the governed marker. Lead:
  please route to 58-r4 / its builder.
- **F-5 FK-a28c-1** — RULED IN by am-36 and folded (the bound pin became the gated KB + the text-reader exact set).
- **F-6 64b-r2 and #486** — untouched: I edited none of `test_mcp_server.py`, the 64b files, `_surreal_harness.py`,
  `conftest.py` or the ~23 #486 files. `scripts/pending_contracts.yaml` carries 64b-r2's uncommitted hunk in the
  working copy; I staged ONLY my entry (HEAD + my entry, §9).
- **F-7 #514 (a teammate's staged index poisons `scratch_copy.sh` copies)**: both my copies were `git reset --hard
  HEAD && git clean -fd` after `scratch_copy.sh`, and `git status` in each was checked clean before my files were
  synced in (§0). am-35 §4's note stands: the instrument should do it itself.
- **F-8 am-35 §6 (64's F5 L2b universal scope leg, rider iv)**: "63c's populations run under it on the reference
  BEFORE it lands" — that is the 64 author's delta, not a pin of mine; noted so the 63c builder knows a 64 leg will
  observe the agent / message writes its migrate verb lands.
- **F-10 #486's working copy of `test_surreal_harness.py` has a THIRD `_RETRYABLE_CONFLICT_MARKER` mutation site** (its
  ~l.1557, absent from HEAD). My §HELD patch applies there, but that third site stays text-keyed: whoever lands
  §HELD after #486 commits re-keys it to `_RETRYABLE_CONFLICT_KIND` exactly like the other two.
- **F-11 (pre-existing, not 63c's; surfaced by FK-a28c-9's probe)**: on `execute_transaction` a PARSE error arrives as
  an RPC-level `error` (`kind: Validation`), is raised by `check_response_for_error` inside `_txn_query_raw`, and is
  caught by its `except (*_CONNECTION_ERRORS, KeyError)` (a `SurrealError`) → served as `SurrealConnectionError` and the
  healthy connection is dropped: a parse error reported as transport. Not pinned (outside am-36 §W) — a ruling item.
- **F-12 am-36's "15 marker pins in 4 files" undercounts the DUAL surface**: the measured blast radius of typing the
  decisions was every forged conflict / cascade in those files (349 failed + 2 collection errors on the am-36
  reference before the re-key, §A.7). Folded completely here (D-8); recorded so the count is not inherited.
- **F-13 A LATENT 58 ↔ 63c COLLISION, found by the SAT (not by any sweep): 58-r3's fate registry
  (`7130508`, committed 2026-09-26 23:10) registered `server.py::_comms_register` as a COMPENSATION fate —
  certifying the one catch site 63c's am-32 build DELETES (a28b K5/K6).** a28b's SAT (`e039c64`, 21:53) predates
  the registry, so no earlier satisfiability run could see it. Fixed here as U-27 (the row's owner is 63c's
  register). **For 58-r4:** the fates pin is now RED at `169925f` (owned by `packet-63c-i-a-a28-contract`) and goes
  green when 63c's build lands. 58's §HELD must not re-add the row. And a 58 builder running the fates pin before
  63c lands meets that owned red, not a 58 defect.
- **F-13a (same collision, the 58 side, read 2026-09-27 from `REPORT-adversary-58-r3.md`, committed `706a1bf` during
  this fold):** adversary-58-r3 finds `REGISTERED_FATES` short (its §FATES census, lines ~86 / ~154) and routes an
  am-11 re-cut of it. **58-r4 will edit `_exhaustion_fates.py` AFTER this commit deletes the `server.py::_comms_register`
  row; the row must stay deleted** (it registers a site no correct 63c build has). The two edits touch different rows.
- **F-15 A MASKING BOUND ON 63c's OWN pins, named by adversary-58-r3 R-5 (not in my worklist — raised, not decided):**
  a28b's door-enumeration exact-set pins are RED at HEAD (owned by `packet-63c-i-a-a28-contract` until the build),
  so a NEW unguarded re-reading door cannot make them any redder; its F6 door was caught ONLY by 58's fate
  classifier. Until 63c's build lands, a pending-red exact-set pin is deaf to a SECOND defect in its own domain.
  That is the #461 shape's general bound: an owned red masks further reds in the same test. It closes with the
  build. **Decision for the lead / sidecar:** accept it as the ordinary pending-contract window, or require the
  per-handler exact-set pins to assert the EXPECTED-at-base set, so a door beyond it reds even before the build.
- **F-14 The satisfiability run is what found U-25…U-27**, and each is the C-DEF class (a pin RED on a correct build).
  The lesson for whoever runs the NEXT fold: a28b's SAT was clean, and three pins a later commit added or a ruling
  re-scoped still went red on this fold's reference. **The SAT has to be re-run against the CURRENT HEAD's full test
  tree, never inherited from the previous round's receipt.**
- **F-9 my reference build's own mypy line** (`principals.py`: a `str | None` passed as the Literal) is a reference
  artefact (not a deliverable); the builder types it.

## §BUILDER CONSTRAINTS (every name / placement / order the pins require; a28b §10 items 1–8 carried unless moved here)
1. **`loremaster.store._txn`** (am-35 §2 + am-36 §1) — **ONE parse per failed statement**: `_failed_statements`
   parses each per-statement ERR ONCE with `surrealdb.errors.parse_query_error` and `_FailedStatement` carries the
   typed error in a DEFAULTED field named **`typed`** (the pins construct `_FailedStatement(index=…, raw_result=…,
   typed=…)`; existing two-argument constructions keep working) — **the shape change** am-35 §E names; the raw text
   rides beside it as server-log EVIDENCE only. **The retry decision is typed**: `details.kind == "TransactionConflict"`
   held in a module constant **`_RETRYABLE_CONFLICT_KIND`** (the detection pins mutate it by that name), on both paths
   (`is_retryable_conflict_error` for the `run_query` exception; the per-statement scan for the transactional path).
   **The root-cause selector is typed**: `details.kind == "NotExecuted"` (the degenerate all-cascade fallback stays).
   **`_RETRYABLE_CONFLICT_MARKER` and the cascade text markers are DELETED** (bare-pattern retired-name sweep). **The
   classifier is typed-first**: the record shape by `isinstance(e, AlreadyExistsError) and e.record_id is not None`
   (any other `AlreadyExistsError` → not the class); the typed conflict kind → its label; the governed THROW by kind
   `Thrown` + OUR prefix at the start of the thrown text (`An error occurred: governed_conflict:` — **the lead's
   rider: re-read the THROW wrapping live**); TEXT only for `kind: Internal` (the U prefix `Database index \``
   at position 0 FIRST, then ASSERT, coercion) and `kind: Validation` (recursion depth — FK-a28c-9); every other
   typed kind → `unspecified rejection`; a bare-text input keeps the text ladder (existing callers pass strings).
   **The record text pair is DELETED.** EVERY raise builds through `_domain_rejection_error`. Exactly ONE function in
   `_txn` may test engine text (`_classify_engine_error` — the exact-set pin), and **no NEW function in `_txn` may
   perform a membership / prefix / suffix / search / `re` test at all**: the pin's allowlist is the four testers
   `_txn` holds today (`_classify_engine_error`, `_assert_envelope_integrity`, `compose`, `is_connection_error`).
   Typed decisions compare the kind with `==` (the reference does: `_detail_kind(failed.typed) == _CASCADE_KIND`); a
   builder who needs a fifth tester ESCALATES for an allowlist row — never re-spells a decision to dodge the pin. **Order vs 58's §HELD:** 63c-i-a lands
   first; 58's part 3 keys its tiers on the classes; 58's new THROW markers (F-4) anchor at the engine's prefix
   too. **Apply the §HELD harness patch in the build wave** (D-9).
2. **The SF-63-1 gate** is exactly `keep_scope(session_keep_bare) in await resolve_visible_keeps(keep_store,
   member_email=principal.email)`, reached through a binding the identity sweep can rebind (the current call-time
   `from loremaster.visible_keeps import resolve_visible_keeps` works); nothing else decides (no `min`, no keeper-only
   read, no private `list_keeps_for_member` copy); preflight AFTER the gate (a28's ORDER, unchanged).
3. **`loremaster.governed.MigratePreconditionCounts`** — the 8 a28b fields + `total_principals`, `admin_principals`
   appended, in `_RULED_FIELD_SPEC` order; each `Field(default=None, json_schema_extra={"read": <tag>})` with the
   ruled tag (agent ×5 incl. `distinct_owner_principals` + `owner_classification`, message ×3, operator ×2); the
   classification `Literal["operator", "foreign", "mixed", "unclassified", "empty"] | None`; a pydantic
   `model_validator` enforcing am-34 §2's triple (a contradiction raises → `ValidationError`); `extra="forbid"`
   kept. **`MigrateGovernedResult.table_defined: bool | None`** (am-36 FK-4): `None` on the zero-I/O invalid-table
   refusal, `True` / `False` wherever `INFO FOR DB` ran.
4. **`loremaster.principals`** — classification `"empty"` whenever the agent read ran and found no
   owned-but-unscoped row; **operator resolution happens through ONE resolver per call** (am-36 FK-8: the
   precondition's AND every leg's), its `(total, admins)` feed `total_principals` / `admin_principals` on the ONE
   counts model whenever ANY resolution ran on that call (`None` iff none ran); EVERY unresolved-operator sentence —
   the verb's UNCLASSIFIED one and each leg's — derives "(N principals, M admins)" from those two FIELDS (the counts
   model is constructed ONCE with them before the sentence is rendered: pin (1) perturbs through the constructor); `AgentMigrationPreconditions.defined_tables` from the ONE `INFO FOR DB`; an undefined
   `--table` target among {agent, memory, message} answers `table_defined=False`, `scanned=0`, `backfilled=0`,
   `refused=False` BEFORE any leg read (no operator resolution, no keep mint, no count); the CLI prints *"… the
   `<table>` table is not defined in this store — nothing to migrate"* iff `table_defined` is `False`, exit 0.
   `"empty"` contributes no owner sentence (no "owned by", no "classif…").
5. **The scanner-visible production** — RS-5 and keeps stay SAFE-BY-TYPE (typed catches, a28b); `record_measurement`'s
   tuple guard stays; any NEW domain handler (a catch of a store-error subclass that re-reads — a same-class `SELECT`
   method or an inline `SELECT`) needs its own exact-set entry, keyed per handler.
6. **The three CAS handlers** propagate exhausted contention as the SAME instance (no translation, no swallow).

## §ATTACK LIST — for the narrow adversary delta (where I would look first; not graded by me)
1. **KB widened's HOST table** — a sixth echoing rejection shape (a `DEFINE`-time error echoing a value? a relation
   `IN/OUT` unique edge?) that maps to an existing label: is it outside all five hosts?
2. **KB over the whole reader set (am-36)** — would a build that types ONLY the retry decision (not the root-cause
   selector) be told apart on every host? (By my reading, yes: the governed host × a cascade phrase × txn cell
   loses its class under a text-reading selector — R2-MR2 is the mutation that tests it.)
3. **The C2 fixture's relations built through `create_keep`** — does a keeper-of-OTHER built by `ctx.comms(register)`
   (a28b's `_shape_carol`) differ from one built by `create_keep` for any gate?
4. **The seam pin's HIDE leg** — a gate that reads the seam AND a private copy (AND-ed) passes hide; does SHOW catch
   it? (By my reading, yes: the private copy denies the stranger.)
5. **F-5's `realistic` leg** — it forbids naming the undefined table and a second `INFO FOR DB`, not every extra read:
   is an operator-resolution read before the typed answer a real defect it misses?
6. **The "empty" stems** — a stem-free owner sentence for `"empty"` (e.g. "no owners to report") passes: sufficient?
7. **One-scanner derivation** — a walker that reads catch handlers via `ast.NodeVisitor.visit_ExceptHandler`
   (a method NAME, no `ast.ExceptHandler` attribute read) and names no store class.
8. **Pin (1)'s legal-swap** — does moving to the next LEGAL member ever make a generated case vacuous (a swap that
   changes no sentence)?
9. **The text-reader derivation** (am-36 pin 3, rewritten D-12) — it now keys on EVERY membership / prefix / search
   / `re` test in `_txn`. Remaining doors I can name: a `match` statement with string-literal cases on the text, `==`
   against a full engine sentence, `.split()`/indexing then `==`, and a test hidden inside one of the three
   non-engine allowlisted testers. Is any a plausible HONEST spelling, or adversarial-only (bound)?
10. **`_engine_shapes.typed_err_entry`'s text → kind mapping** — a forged fixture whose text the mapping files under
    the wrong kind would make a pin green for a fixture reason: check every call site's text against the measured
    pairs (§A.1 / §A.2).
11. **FK-8's observed resolution** (the gating pin spies `PrincipalStore.list`) — a build that resolves without
    listing (a cached resolution across calls) would read as "no resolution" and pass `None` counts.

## §DRY LEDGER (brief-base §6 — every NEW reusable symbol; all test-support, no production symbol)
lore_search was run for the three helper shapes most likely to exist already (2026-09-27 ~01:08); two answered after
>120 s, one was aborted by the client after 300 s of silence — filed as finding **#516**. The remaining look-ups were
`awk` over `loremaster/tests/*.py` — the fallback SAID here.
| new symbol | query run | what it returned | disposition |
|---|---|---|---|
| `_engine_shapes.typed_err_entry` / `typed_conflict_error` / `RETRYABLE_CONFLICT_KIND` / `CASCADE_KIND` / `CONFLICT_WORDS` / `CASCADE_OPENINGS` / `THROW_OPENING` (NEW module) | lore_search "fake connection whose query_raw returns a forged per-statement ERR response" | `test_surreal_store._TxnRollbackFakeConnection` (a scripted CONNECTION, not a shape builder); awk: three private text-only shape builders (`test_surreal_store._rolled_back_response`, `test_txn_contention._rolled_back_response`, `test_retry_seam._conflict_rollback_response`) and two private conflict-error builders (`test_retry_seam._conflict_error`, the harness's) | HAND-ROLLED as THE shared home; the store / contention builders now ROUTE their per-entry shape through `typed_err_entry`, the harness's conflict error through `typed_conflict_error`, and the retry-seam fixtures take their kinds from its constants. ⚠ Partial: `_conflict_rollback_response` still assembles its own entries because the detection pins need a caller-chosen (MUTATED) conflict kind that a text→kind mapping cannot express — stated, not hidden (attack list 10) |
| `_raise_through(…, params=None)` (a28b) | lore_search "helper that runs a statement through run_query or execute_transaction and returns the raised exception" | `test_fixwave_a28b_63c_i_a._raise_through` (no params) | EXTENDED `a28b._raise_through` (a defaulted `params`); my `_raise_with` twin DELETED |
| `_execute_transaction_raises` (C) | (same query as the first row) | `_TxnRollbackFakeConnection` | REUSED `test_surreal_store._TxnRollbackFakeConnection` (my `_ForgedTxnConnection` twin DELETED); imported at use (collection stays decoupled) |
| `_count_attempts` (C) | awk `setattr(.*retry_on_conflict` | `test_retry_seam`'s driver spy (records DRIVER ENTRIES, not attempts); a28b's keeps twin counts create calls | HAND-ROLLED — counts ATTEMPTS inside THE driver (one wrapper, the ONE driver); no existing helper counts attempts |
| `_spy_driver_statements` (C) | lore_search "record every driver statement by wrapping run_query and execute_transaction bindings" — ABORTED (#516); awk | 58's `DriverSeamInjection` (injects, does not record statements); `patch_shared_object_everywhere` | HAND-ROLLED on REUSED `patch_shared_object_everywhere` (the ONE by-identity sweep) |
| `_arm_the_driver_seams` (C) | read `test_reanchor_58_r3_cas_seam.DriverSeamInjection` | `install()` (asserts a shell holder — D-6) | REUSED 58's `_seam_wrapper` + `patch_shared_object_everywhere`; never a copy (F-3 names the flag that would remove the private reach) |
| `_give_carol`, `_relation_set_id`, `_RELATIONS`, `_RELATION_SETS`, `_RELATION_VERBS` (C) | read a28b `_shape_carol` | builds relations via `register` (keeper) + store verbs; one relation at a time | HAND-ROLLED — am-35 §1 rules relation SETS built through the store's public verbs; a28b's `_shape_carol` stays for KC (AST-equal) |
| `_the_triple_is_legal`, `_TRIPLES`, `_populations_classified_as`, `_OWNER_SENTENCE_STEMS` (C) | read a28's am-30/31 plumbing | `_literal_members`, `_POPULATIONS` | HAND-ROLLED on REUSED `a28._literal_members` / `a28._POPULATIONS` |
| `_text_testers_in`, `_engine_text_readers`, `_ENGINE_TEXT_READER`, `_TEXT_TEST_ALLOWLIST`, `_SEARCH_METHODS`, `_TEXT_DECIDED_KINDS`, `_sdk_kinds`, `_HOSTILE_TEXTS` (C) | awk over the test tree for an AST text-reader / membership-test scan | none (58's `_catch_sites` walks catch clauses, not text tests) | HAND-ROLLED (am-36 §1.2 pin 3's own derivation, rewritten D-12; takes a TREE so the positive control runs it) |
| `_read_tag`, `_count_principal_listings`, `_operator_counts_describe_an_unresolved_operator`, `_OPERATOR_COUNTS`, `_OWNER_SENTENCE_STATES` (B) | read a28 `_read_of`, `_OWNER_SENTENCE_STATES_N` | the name-suffix partition; the bool table | EXTENDED in place (DUAL rows U-2, U-6); `_count_principal_listings` HAND-ROLLED (no principal spy existed) |
| `_production_module_trees`, `_is_domain_handler`, `_cas_handlers_in`, `_handler_function`, `_admits_exhaustion`, `_exhaustion_reached_clauses`, `_domain_handler_count`, `_synthetic_handler_module`, `_scanner_candidates` (RS) | read 58-r3 §HELD part 2 + `_catch_sites` | `_catch_sites.catch_sites_in` / `caught_classes` / `_parents_of` (THE walker + resolver) | REUSED the walker / resolver / `_parents_of` by import (D-2); the rest are the index's own parts (58's split names kept so its §HELD re-derives cleanly) |

## Packages considered
| mechanism the contract specifies / pins | library evaluated | what I READ / RAN | verdict |
|---|---|---|---|
| R typed on the txn path; the retry decision and the cascade selector typed (am-35 §2 item 1, am-36 §1.1) | `surrealdb` 2.0.0 `errors.parse_query_error` + `ServerError.details` | the installed `parse_query_error` source (`KIND_TO_CLASS`, the double-wrap workaround) + LIVE probes §A.1 (R-txn `AlreadyExists/Record`), §A.2 (`TransactionConflict` on both paths; `NotExecuted` on every cascade) | `replace_with_adapter` (the reference parses ONCE and reads `details.kind`) |
| the SDK kind domain for the text-reader positive control | `surrealdb.errors.KIND_TO_CLASS` | installed module (9 kinds) | `replace` (derived, not hand-listed) |
| U / ASSERT / coercion / recursion text | same | LIVE: U / ASSERT / coercion arrive `kind: Internal`, `details: None`; recursion `kind: Validation` (§A.2b) | `bespoke` text forced (the engine types nothing distinguishing) — pinned as the stated bounds |
| scanner: catch-site walk + caught-class resolution | stdlib `ast` + THE ONE walker / resolver (`_catch_sites`) | read `_catch_sites.py` (58-r3, committed) | `replace` — the private copy is gone (D-2) |
| perturbation by annotation / read tags | pydantic `model_fields[…].json_schema_extra`, `typing.get_args` | installed pydantic 2 field info | `replace` (used) |
| spies (driver seams, the visibility seam) | `pytest.MonkeyPatch` + THE shared `patch_shared_object_everywhere` | `_governed_contract.py` | `replace` (reused) |

## §A INSTRUMENTS — verbatim (a scratch path is unrecoverable by construction, so the CONTENT is the receipt)
Every instrument this report cites, with its md5 at commit time. Scratch root: this session's scratchpad (named
only so a reader knows the files were never in the repo; cite them by §A number).

### §A.1 `probe_a28c.py` — the FK-a28c-1 echo probe (run against HEAD's `_txn` = `169925f`, test store :18000)
md5 `15d06139c592e1eb1f54b81609fd1ef2`, 71 lines
````python
"""probe_a28c.py <tree> — contract-63c-i-a-a28c live probe (TEST store :18000 only; throwaway db, removed).
(1) every host shape's engine text on BOTH paths (sdk query / query_raw in BEGIN..COMMIT): prefix + typed fields;
(2) echoed-phrase doors at the driver: each (host, phrase) run through <tree>'s _txn.run_query and
    _txn.execute_transaction; prints the raised class and elapsed time."""
import asyncio, json, logging, sys, time, uuid
sys.path.insert(0, sys.argv[1] + "/loremaster")
from surrealdb import AsyncSurreal
from surrealdb.errors import parse_query_error
import loremaster.store._txn as T
print("TXN FILE", T.__file__)
URL = "ws://127.0.0.1:18000/rpc"
SETUP = ["DEFINE TABLE hx SCHEMAFULL", "DEFINE FIELD s ON hx TYPE string ASSERT string::len($value) < 60",
         "DEFINE FIELD k ON hx TYPE option<string>", "DEFINE FIELD n ON hx TYPE option<int>",
         "DEFINE INDEX hx_k ON hx FIELDS k UNIQUE", "CREATE hx:seed SET s = 'ok', k = 'taken'"]
HOSTS = {  # host -> template with {v} = the echoed value
    "U": "CREATE hx SET s = 'ok', k = {v}",           # needs k taken: v must equal an existing k -> seeded per phrase
    "A": "CREATE hx SET s = {v}",                      # assert: value too long -> echoed
    "C": "CREATE hx SET s = 'ok', n = {v}",            # coercion: string into option<int>
    "G": "THROW 'governed_conflict:hx:' + {v}",        # governed THROW carrying a suffix
    "R": "CREATE hx:⟨{raw}⟩ SET s = 'ok'",             # record id collision (seeded)
}
async def main():
    assert ":18000" in URL
    db = f"a28c_probe_{uuid.uuid4().hex[:8]}"
    c = AsyncSurreal(URL); await c.connect(); await c.signin({"username": "root", "password": "spikeroot"})
    await c.query("DEFINE NAMESPACE IF NOT EXISTS a28cns"); await c.use("a28cns", db)
    await c.query(f"DEFINE DATABASE IF NOT EXISTS {db}"); await c.use("a28cns", db)
    for s in SETUP: await c.query(s)
    async def acquire(): return c
    async def drop(_): return None
    plain = "zz" + "q" * 70
    print("== (1) shapes, plain value")
    for h, tpl in HOSTS.items():
        raw = "seedr"
        if h == "R": await c.query("CREATE hx:seedr SET s = 'ok'")
        if h == "U": stmt = tpl.format(v="'taken'")
        else: stmt = tpl.format(v=f"'{plain}'", raw=raw)
        try:
            await c.query(stmt); print(h, "sdk: NO ERROR")
        except Exception as e:
            print(h, "sdk:", type(e).__name__, getattr(e, "kind", None), json.dumps(getattr(e, "details", None)), "|", str(e)[:150])
        r = await c.query_raw(f"BEGIN;\n{stmt};\nCOMMIT;", {})
        for i, x in enumerate(r.get("result") or []):
            if x.get("status") == "ERR":
                print(h, f"txn[{i}]", x.get("kind"), json.dumps(x.get("details")), "|", str(x.get("result"))[:150])
    print("== (2) echoed phrases through the driver")
    phrases = {"retry": "x This transaction can be retried", "cascade": "x was not executed due to a failed transaction",
               "commit-abort": "x aborted due to a prior error", "governed": "governed_conflict:x",
               "unique": "Database index `z` already contains 1", "record": "Database record `hx:q` already exists",
               "assert": "x must conform to y", "coerce": "x coerce y", "recursion": "x recursion depth y"}
    for h in ("U", "A", "C", "G"):
        for name, p in phrases.items():
            v = p
            if h == "U":
                await c.query(f"CREATE hx SET s = 'ok', k = $v", {"v": v})  # seed the taken value
            stmt = HOSTS[h].format(v="$v")
            out = []
            for path in ("run_query", "execute_transaction"):
                t0 = time.monotonic()
                try:
                    if path == "run_query":
                        await T.run_query(acquire=acquire, drop=drop, url=URL, noun="p", label="p.rejected", statement=stmt, params={"v": v}, logger=logging.getLogger("p"))
                    else:
                        await T.execute_transaction(f"BEGIN;\n{stmt};\nCOMMIT;", {"v": v}, acquire=acquire, drop=drop, url=URL)
                    out.append(f"{path}=NO-ERROR")
                except BaseException as e:
                    out.append(f"{path}={type(e).__name__}({time.monotonic()-t0:.2f}s)")
            print(f"host={h} phrase={name}: " + "  ".join(out))
    await c.query(f"REMOVE DATABASE {db}"); await c.close()
logging.disable(logging.CRITICAL)
asyncio.run(main())
````

### §A.2 `probe_conflict.py` — the typed-conflict / typed-cascade probe (3.2.4, both paths)
md5 `afa8504ba47610d7b6e9cf8d3eacd43a`, 36 lines
````python
"""probe_conflict.py — the GENUINE retryable write-write conflict's shape on 3.2.x (TEST store :18000 only):
16 concurrent connections each run BEGIN; UPDATE c:one SET n += 1; COMMIT via query_raw (txn path) and a bare
UPDATE via query() (sdk path); prints every distinct ERR (kind, details, text) seen. Throwaway db, removed."""
import asyncio, json, uuid
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"
async def conn(db):
    c = AsyncSurreal(URL); await c.connect(); await c.signin({"username": "root", "password": "spikeroot"})
    await c.use("a28cns", db); return c
async def main():
    db = f"a28c_conflict_{uuid.uuid4().hex[:8]}"
    c0 = AsyncSurreal(URL); await c0.connect(); await c0.signin({"username": "root", "password": "spikeroot"})
    await c0.query("DEFINE NAMESPACE IF NOT EXISTS a28cns"); await c0.use("a28cns", db)
    await c0.query(f"DEFINE DATABASE IF NOT EXISTS {db}"); await c0.use("a28cns", db)
    await c0.query("CREATE c:one SET n = 0")
    conns = [await conn(db) for _ in range(16)]
    seen = {}
    async def txn(c):
        r = await c.query_raw("BEGIN;\nUPDATE c:one SET n += 1;\nLET $x = (SELECT * FROM c);\nUPDATE c:one SET n += 1;\nCOMMIT;", {})
        for x in r.get("result") or []:
            if x.get("status") == "ERR":
                seen.setdefault(("txn", x.get("kind"), json.dumps(x.get("details")), str(x.get("result"))[:120]), 0)
                seen[("txn", x.get("kind"), json.dumps(x.get("details")), str(x.get("result"))[:120])] += 1
    async def sdk(c):
        try: await c.query("UPDATE c:one SET n += 1")
        except Exception as e:
            k = ("sdk", type(e).__name__ + ":" + str(getattr(e, "kind", None)), json.dumps(getattr(e, "details", None)), str(e)[:120])
            seen[k] = seen.get(k, 0) + 1
    for _ in range(20):
        await asyncio.gather(*(txn(c) for c in conns))
        await asyncio.gather(*(sdk(c) for c in conns))
    for k, n in sorted(seen.items()): print(n, k)
    if not seen: print("NO CONFLICT OBSERVED")
    await c0.query(f"REMOVE DATABASE {db}")
    for c in conns + [c0]: await c.close()
asyncio.run(main())
````

### §A.2b `probe_kinds.py` — the untyped-kinds probe (U / ASSERT / coercion `Internal`, recursion `Validation` — FK-a28c-9)
md5 `09312dde899b48ac06db7a98cbc8dacd`, 23 lines
````python
"""probe_kinds.py — the SDK kind of every rejection the classifier labels (TEST store :18000; throwaway db):
the recursion-depth parse error (#66), plus a SCHEMAFULL unknown-field and a type error, on both paths."""
import asyncio, json, uuid
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"
async def main():
    db = f"a28c_kinds_{uuid.uuid4().hex[:8]}"
    c = AsyncSurreal(URL); await c.connect(); await c.signin({"username": "root", "password": "spikeroot"})
    await c.query("DEFINE NAMESPACE IF NOT EXISTS a28cns"); await c.use("a28cns", db)
    await c.query(f"DEFINE DATABASE IF NOT EXISTS {db}"); await c.use("a28cns", db)
    deep = "RETURN " + " OR ".join(["true"] * 5000)
    for name, stmt in {"recursion": deep, "deep-parens": "RETURN " + "(" * 3000 + "1" + ")" * 3000}.items():
        try:
            await c.query(stmt); print(name, "sdk: NO ERROR")
        except Exception as e:
            print(name, "sdk:", type(e).__name__, getattr(e, "kind", None), json.dumps(getattr(e, "details", None)), "|", str(e)[:140])
        try:
            r = await c.query_raw(f"BEGIN;\n{stmt};\nCOMMIT;", {})
            print(name, "raw:", json.dumps(r)[:300])
        except Exception as e:
            print(name, "raw raised:", type(e).__name__, getattr(e, "kind", None), json.dumps(getattr(e, "details", None)), "|", str(e)[:140])
    await c.query(f"REMOVE DATABASE {db}"); await c.close()
asyncio.run(main())
````

### §A.3 `f4_measure.py` — the FK-a28c-5 reached-clause measurement over the six door functions
md5 `8ae5591d365a71e53dd462ce27263ee4`, 20 lines
````python
"""f4_measure.py — for every canonical door's FUNCTION, every except clause that can catch exhausted contention
(issubclass(TCE, c) for some caught c), per try: is it the FIRST such clause in its try (reached), what it catches,
and whether its body is a bare raise. Also counts domain handlers per function (the per-handler key's domain)."""
import ast, sys
sys.path[:0] = ["loremaster/tests"]
import test_retry_seam as rs
from _catch_sites import catch_sites_in
from loremaster.store._txn import TxnContentionExhaustedError as TCE, SurrealStoreError
doors = rs._GUARDED_CAS_DOORS
for door in sorted(doors) + sorted(rs._TYPED_CAS_CATCHES):
    f, fn = door.split("::")
    mod = rs._module_of(f); tree = ast.parse((rs._PACKAGE_ROOT / f).read_text())
    sites = [s for s in catch_sites_in(f, tree, mod) if s.key == door and s.handler is not None]
    print(door)
    for s in sites:
        catches = any(issubclass(TCE, c) for c in s.caught)
        reached = catches and not any(issubclass(TCE, c) for c in s.earlier)
        body = [st for st in s.handler.body if not isinstance(st, ast.Pass)]
        bare = all(isinstance(st, ast.Raise) and st.exc is None for st in body)
        print(f"   line {s.lineno} {s.form} caught={[c.__name__ for c in s.caught]} catches_TCE={catches} reached={reached} bare_raise={bare}")
````

### §A.4 `cand.py` — the FK-a28c-7 one-scanner candidate property (first form)
md5 `0560722767385405b723062497c9307b`, 17 lines
````python
import ast, pathlib, sys
sys.path[:0] = ["loremaster/tests"]
import loremaster.store._txn as t
names = {n for n, v in vars(t).items() if isinstance(v, type) and issubclass(v, t.SurrealStoreError)}
walk_calls = {"walk", "parse", "iter_child_nodes", "NodeVisitor", "NodeTransformer"}
roots = [pathlib.Path("loremaster/tests"), pathlib.Path("lorerunes/tests"), pathlib.Path("scripts")]
for root in roots:
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts: continue
        try: tree = ast.parse(path.read_text())
        except Exception: continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
            walks = any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "ast" and n.attr in walk_calls for n in ast.walk(fn))
            named = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id in names} | {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute) and n.attr in names}
            if walks and named:
                print(f"{path}::{fn.name}", sorted(named))
````

### §A.4b `cand2.py` — the FK-a28c-7 candidate property as landed
md5 `cc4af7cb93da30930c1cb50254a26959`, 22 lines
````python
"""cand2.py — two candidate properties over the test roots (pyproject testpaths): (i) a function that FINDS catch
handlers itself (isinstance vs ast.Try/TryStar/ExceptHandler, or reads `.handlers`), with/without naming a
store-error-tree class; (ii) a function that EVALUATES an except expression in a module namespace (eval+compile)."""
import ast, pathlib, sys, tomllib
sys.path[:0] = ["loremaster/tests"]
import loremaster.store._txn as t
names = {n for n, v in vars(t).items() if isinstance(v, type) and issubclass(v, t.SurrealStoreError)}
roots = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["tool"]["pytest"]["ini_options"]["testpaths"]
CATCH = {"Try", "TryStar", "ExceptHandler"}
for root in roots:
    for path in sorted(pathlib.Path(root).rglob("*.py")):
        if "__pycache__" in path.parts: continue
        try: tree = ast.parse(path.read_text())
        except Exception: continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)): continue
            body = [n for stmt in fn.body for n in ast.walk(stmt)]
            finds = any(isinstance(n, ast.Attribute) and ((isinstance(n.value, ast.Name) and n.value.id == "ast" and n.attr in CATCH) or n.attr == "handlers") for n in body)
            named = {n.id for n in body if isinstance(n, ast.Name) and n.id in names} | {n.attr for n in body if isinstance(n, ast.Attribute) and n.attr in names}
            evals = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "eval" for n in body) and any(isinstance(n, ast.Attribute) and n.attr == "Expression" for n in body)
            if finds: print("FINDS", "STORE" if named else "     ", f"{path}::{fn.name}", sorted(named))
            if evals: print("EVALS", f"{path}::{fn.name}")
````

### §A.5a `myref_a28c_txn.py` — reference delta 1 (am-35 §2) — a SAT / mutation HOST, never a spec
md5 `d95da5add8920a6cd3b713b3d420f40f`, 51 lines
````python
"""myref_a28c_txn.py <tree>: contract-63c-i-a-a28c's reference delta for amendment 35 §2 over the a28b reference
(a SAT / mutation HOST, NOT a spec): R typed on BOTH paths (the txn path keeps the per-statement dict and reads
surrealdb.errors.parse_query_error), the record text pair DELETED, U a position-0 prefix test checked FIRST (after
the typed branch), the governed marker anchored to the engine's THROW prefix, ASSERT / coercion / recursion LAST.
Exact-once anchors; fails loud on a miss."""
import pathlib, sys
root = pathlib.Path(sys.argv[1])
def sub(path, old, new, count=1):
    p = root / path; text = p.read_text()
    assert text.count(old) == count, (path, old[:90], text.count(old)); p.write_text(text.replace(old, new))
T = "loremaster/loremaster/store/_txn.py"
sub(T, "from surrealdb.errors import AlreadyExistsError, ErrorKind, ServerError, SurrealError",
       "from surrealdb.errors import AlreadyExistsError, ErrorKind, ServerError, SurrealError, parse_query_error")
sub(T, '''_UNIQUE_VIOLATION_MARKERS = (("database record", "already exists"), ("database index", "already contains"))''',
'''# amendment 35 §2: the ONE untyped identity shape (a UNIQUE-index collision; the record shape is TYPED on both
# paths) is a PREFIX test at position 0 of the engine-authored text — every echoed value comes after it.
_UNIQUE_INDEX_MARKER = "database index `"
# amendment 35 §2 item 3: the governed marker, anchored at the engine-authored START of the THROW text (measured
# 3.2.4: the engine wraps a THROW as "An error occurred: <thrown>").
_ENGINE_THROW_PREFIX = "an error occurred: "''')
sub(T, '''    if _GOVERNED_CONFLICT_MARKER in lowered:
        return _ERROR_CLASS_GOVERNED_CONFLICT
    if any(all(part in lowered for part in marker) for marker in _UNIQUE_VIOLATION_MARKERS):
        return _ERROR_CLASS_UNIQUE_VIOLATION
''', '''    if lowered.startswith(_UNIQUE_INDEX_MARKER):
        return _ERROR_CLASS_UNIQUE_VIOLATION
    if lowered.startswith(_ENGINE_THROW_PREFIX + _GOVERNED_CONFLICT_MARKER):
        return _ERROR_CLASS_GOVERNED_CONFLICT
''')
sub(T, '''    index: int
    raw_result: Any
''', '''    index: int
    raw_result: Any
    raw_statement: Any = None
''')
sub(T, '''        _FailedStatement(index=index, raw_result=statement_result.get("result"))''',
'''        _FailedStatement(index=index, raw_result=statement_result.get("result"), raw_statement=statement_result)''')
sub(T, '''            error_class = _classify_engine_error(root_cause.raw_result)
            _log_rollback(''', '''            error_class = _classify_engine_error(_typed_root_cause(root_cause))
            _log_rollback(''')
sub(T, '''def _is_retryable_conflict(failed_statements: list[_FailedStatement]) -> bool:''',
'''def _typed_root_cause(failed: _FailedStatement) -> object:
    """The SDK's TYPED error for a per-statement ERR (amendment 35 §2 item 1) — ``parse_query_error`` over the
    whole dict when it carries a ``kind`` — else the raw text."""
    if isinstance(failed.raw_statement, dict) and failed.raw_statement.get("kind"):
        return parse_query_error(failed.raw_statement)
    return failed.raw_result


def _is_retryable_conflict(failed_statements: list[_FailedStatement]) -> bool:''')
print("myref_a28c_txn ok")
````

### §A.5b `myref_a28c_migrate.py` — reference delta 2 (am-34 + am-35 §4)
md5 `6515728a99ad410d9aa918e3e329ff08`, 133 lines
````python
"""myref_a28c_migrate.py <tree>: contract-63c-i-a-a28c's reference delta for amendment 34 (+ amendment 35 §4 R-4) over
the a28b reference's migrate half (a SAT / mutation HOST, NOT a spec): "empty" + the invariant model validator,
total_principals / admin_principals (None iff the precondition's operator resolution was not attempted), a read tag
per field, the unclassified sentence derived from the fields, F-5 (defined_tables on the preconditions,
table_defined on the result, the leg checks it before any read; the CLI render derives the sentence from it).
Exact-once anchors; fails loud on a miss."""
import pathlib, sys
root = pathlib.Path(sys.argv[1])
def sub(path, old, new, count=1):
    p = root / path; text = p.read_text()
    assert text.count(old) == count, (path, old[:90], text.count(old)); p.write_text(text.replace(old, new))
G = "loremaster/loremaster/governed.py"; P = "loremaster/loremaster/principals.py"
sub(G, "from pydantic import BaseModel, ConfigDict", "from pydantic import BaseModel, ConfigDict, Field, model_validator")
sub(G, '''    unscoped_agents: int | None = None
    owned_but_unscoped_agents: int | None = None
    scoped_but_ownerless_agents: int | None = None
    dangling_sender_messages: int | None = None
    owned_but_unscoped_messages: int | None = None
    scoped_but_ownerless_messages: int | None = None
    distinct_owner_principals: int | None = None
    owner_classification: Literal["operator", "foreign", "mixed", "unclassified"] | None = None
''', '''    unscoped_agents: int | None = Field(default=None, json_schema_extra={"read": "agent"})
    owned_but_unscoped_agents: int | None = Field(default=None, json_schema_extra={"read": "agent"})
    scoped_but_ownerless_agents: int | None = Field(default=None, json_schema_extra={"read": "agent"})
    dangling_sender_messages: int | None = Field(default=None, json_schema_extra={"read": "message"})
    owned_but_unscoped_messages: int | None = Field(default=None, json_schema_extra={"read": "message"})
    scoped_but_ownerless_messages: int | None = Field(default=None, json_schema_extra={"read": "message"})
    distinct_owner_principals: int | None = Field(default=None, json_schema_extra={"read": "agent"})
    owner_classification: Literal["operator", "foreign", "mixed", "unclassified", "empty"] | None = Field(
        default=None, json_schema_extra={"read": "agent"}
    )
    total_principals: int | None = Field(default=None, json_schema_extra={"read": "operator"})
    admin_principals: int | None = Field(default=None, json_schema_extra={"read": "operator"})

    @model_validator(mode="after")
    def _one_meaning_per_state(self) -> "MigratePreconditionCounts":
        """amendment 34 §2: the owner triple is consistent by construction."""
        owned, distinct, classification = (
            self.owned_but_unscoped_agents, self.distinct_owner_principals, self.owner_classification
        )
        if classification is None or owned is None or distinct is None:
            legal = classification is None and owned is None and distinct is None
        elif classification == "empty":
            legal = owned == 0 and distinct == 0
        else:
            legal = owned > 0 and distinct > 0
        if not legal:
            raise ValueError(f"contradictory owner triple: {owned=} {distinct=} {classification=}")
        return self
''')
sub(G, '''    reason: str | None = None
    preconditions: MigratePreconditionCounts | None = None


@dataclass(frozen=True)
class LegacyMapping:''', '''    reason: str | None = None
    preconditions: MigratePreconditionCounts | None = None
    table_defined: bool = True


@dataclass(frozen=True)
class LegacyMapping:''')
# principals: counts
sub(P, '''    owners = {str(owner) for _row_id, owner in preconditions.owned_unscoped}
    classification: str | None = None
    if agent and owners:
        operator = await resolve_operator_principal(principal_store)
        if operator is None:''', '''    owners = {str(owner) for _row_id, owner in preconditions.owned_unscoped}
    classification: str | None = "empty" if agent else None
    total_principals: int | None = None
    admin_principals: int | None = None
    if agent and owners:
        listed = await principal_store.list()
        total_principals = len(listed)
        admin_principals = sum(1 for principal in listed if principal.role == _ROLE_ADMIN)
        operator = await resolve_operator_principal(principal_store)
        if operator is None:''')
sub(P, '''        distinct_owner_principals=len(owners) if agent else None,
        owner_classification=classification,
    )''', '''        distinct_owner_principals=len(owners) if agent else None,
        owner_classification=classification,
        total_principals=total_principals,
        admin_principals=admin_principals,
    )''')
sub(P, '''    if preconditions.owned_unscoped:
        operator = await resolve_operator_principal(principal_store)
        if operator is None:
            parts.append(
                await _operator_unresolved(principal_store, purpose="to classify the rows below") + "."
            )''', '''    if preconditions.owned_unscoped:
        operator = await resolve_operator_principal(principal_store)
        if counts.owner_classification == "unclassified":
            parts.append(
                f"cannot resolve THE operator principal to classify the rows below ({counts.total_principals} "
                f"principals, {counts.admin_principals} admins) — provision a single operator principal (or a "
                "single admin) before migrating."
            )''')
# F-5: defined tables on the preconditions; the verb answers an undefined target before any leg read
sub(P, '''    unscoped_count: int
    owned_unscoped: tuple[tuple[Any, Any], ...]
    ownerless_scoped: tuple[Any, ...]
    agent_facts_read: bool = False''', '''    unscoped_count: int
    owned_unscoped: tuple[tuple[Any, Any], ...]
    ownerless_scoped: tuple[Any, ...]
    defined_tables: frozenset[str] = frozenset()
    agent_facts_read: bool = False''')
sub(P, '''    return AgentMigrationPreconditions(
        agent_facts_read=AGENT_TABLE in defined,''', '''    return AgentMigrationPreconditions(
        defined_tables=frozenset(defined),
        agent_facts_read=AGENT_TABLE in defined,''')
sub(P, '''    if refusal is not None:
        result = _refused(table, refusal)
    elif table == MEMORY_TABLE:''', '''    if refusal is not None:
        result = _refused(table, refusal)
    elif table in (MEMORY_TABLE, AGENT_TABLE, MESSAGE_TABLE) and table not in preconditions.defined_tables:
        from loremaster.governed import MigrateGovernedResult

        result = MigrateGovernedResult(
            table=table, scanned=0, backfilled=0, already_migrated=0, refused=False, table_defined=False
        )
    elif table == MEMORY_TABLE:''')
sub(P, '''            return 1
        print(
            f"migrate-governed --table {result.table}: scanned={result.scanned} "''', '''            return 1
        if not result.table_defined:
            print(
                f"migrate-governed --table {result.table}: the `{result.table}` table is not defined in this "
                "store — nothing to migrate"
            )
            return 0
        print(
            f"migrate-governed --table {result.table}: scanned={result.scanned} "''')
print("myref_a28c_migrate ok")
````

### §A.5c `myref_a28c_am36.py` — reference delta 3 (am-36 §1: typed retry / cascade, ONE parse, typed-first classifier)
md5 `5d2b3448d2de89cba086f0c08200f544`, 119 lines
````python
"""myref_a28c_am36.py <tree>: contract-63c-i-a-a28c's reference delta for amendment 36 §1 over myref_a28c_txn.py (a
SAT / mutation HOST, NOT a spec): ONE parse per failed statement (the typed ServerError rides _FailedStatement), the
retry decision typed (details.kind == TransactionConflict, both paths), the root-cause selector typed (NotExecuted),
both text markers DELETED, the classifier typed-first — text only where the engine's kind does not decide the label
(Internal: U prefix, ASSERT, coercion; Validation: recursion depth — FK-a28c-9); a bare-text input keeps the text
ladder (legacy callers). Exact-once anchors; fails loud."""
import pathlib, sys, re
root = pathlib.Path(sys.argv[1])
T = "loremaster/loremaster/store/_txn.py"
def sub(old, new, count=1):
    p = root / T; text = p.read_text()
    assert text.count(old) == count, (old[:90], text.count(old)); p.write_text(text.replace(old, new))
sub('_RETRYABLE_CONFLICT_MARKER = "can be retried"\n',
    '# amendment 36 §1.1: the retryable write-write conflict is TYPED on both paths (3.2.4, measured: kind Query,\n'
    '# details.kind TransactionConflict) — the decision reads the kind, never the text.\n'
    '_RETRYABLE_CONFLICT_KIND = "TransactionConflict"\n')
sub('''_CASCADE_NOT_EXECUTED_MARKER = "was not executed due to"
_CASCADE_COMMIT_ABORTED_MARKER = "aborted due to a prior error"
_DOMAIN_CASCADE_MARKERS = (_CASCADE_NOT_EXECUTED_MARKER, _CASCADE_COMMIT_ABORTED_MARKER)
''', '''# amendment 36 §1.1: every cascade notice (a never-executed statement, the refused COMMIT) is TYPED
# (details.kind NotExecuted, measured 3.2.4) — the selector reads the kind, never the text.
_CASCADE_KIND = "NotExecuted"
''')
# the classifier: typed-first
sub('''    if isinstance(raw_result, AlreadyExistsError):
        # Typed beats text (amendment 32 §1.1 item 3): the SDK's own discriminator decides.
        return _ERROR_CLASS_UNIQUE_VIOLATION if raw_result.record_id is not None else _ERROR_CLASS_UNSPECIFIED
    text = str(raw_result)
    if _is_retryable_conflict_text(text):
        return _ERROR_CLASS_RETRYABLE_CONFLICT
    lowered = text.lower()
    if lowered.startswith(_UNIQUE_INDEX_MARKER):
        return _ERROR_CLASS_UNIQUE_VIOLATION
    if lowered.startswith(_ENGINE_THROW_PREFIX + _GOVERNED_CONFLICT_MARKER):
        return _ERROR_CLASS_GOVERNED_CONFLICT
    if _ASSERT_VIOLATION_MARKER in lowered:
        return _ERROR_CLASS_ASSERT_VIOLATION
    if _FIELD_COERCION_MARKER in lowered:
        return _ERROR_CLASS_FIELD_COERCION
    if _QUERY_RECURSION_DEPTH_MARKER in lowered:
        return _ERROR_CLASS_QUERY_TOO_COMPLEX
    return _ERROR_CLASS_UNSPECIFIED
''', '''    if isinstance(raw_result, AlreadyExistsError):
        # Typed beats text (amendment 32 §1.1 item 3): the SDK's own discriminator decides.
        return _ERROR_CLASS_UNIQUE_VIOLATION if raw_result.record_id is not None else _ERROR_CLASS_UNSPECIFIED
    if _is_retryable_conflict_kind(raw_result):
        return _ERROR_CLASS_RETRYABLE_CONFLICT
    kind = raw_result.kind if isinstance(raw_result, ServerError) else None
    lowered = str(raw_result).lower()
    if kind == "Thrown" or kind is None:
        if lowered.startswith(_ENGINE_THROW_PREFIX + _GOVERNED_CONFLICT_MARKER):
            return _ERROR_CLASS_GOVERNED_CONFLICT
    if kind not in (None, "Internal", "Validation"):
        return _ERROR_CLASS_UNSPECIFIED
    if kind in (None, "Internal"):
        if lowered.startswith(_UNIQUE_INDEX_MARKER):
            return _ERROR_CLASS_UNIQUE_VIOLATION
        if _ASSERT_VIOLATION_MARKER in lowered:
            return _ERROR_CLASS_ASSERT_VIOLATION
        if _FIELD_COERCION_MARKER in lowered:
            return _ERROR_CLASS_FIELD_COERCION
    if kind in (None, "Validation") and _QUERY_RECURSION_DEPTH_MARKER in lowered:
        return _ERROR_CLASS_QUERY_TOO_COMPLEX
    return _ERROR_CLASS_UNSPECIFIED
''')
# the retry decision
p = root / T; text = p.read_text()
m = re.search(r'\ndef _is_retryable_conflict_text\(text: str\) -> bool:.*?\n    return _RETRYABLE_CONFLICT_MARKER in text\n', text, re.S)
assert m
text = text[:m.start()] + '''
def _detail_kind(error: object) -> str | None:
    """``details.kind`` of a typed SDK error (``None`` for anything untyped)."""
    details = getattr(error, "details", None)
    kind = details.get("kind") if isinstance(details, dict) else None
    return kind if isinstance(kind, str) else None


def _is_retryable_conflict_kind(error: object) -> bool:
    """THE ONE retryable-conflict authority (amendment 36): the engine's TYPED ``TransactionConflict``."""
    return isinstance(error, ServerError) and _detail_kind(error) == _RETRYABLE_CONFLICT_KIND
''' + text[m.end():]
p.write_text(text)
sub('''    return _is_retryable_conflict_text(str(error))
''', '''    return _is_retryable_conflict_kind(error)
''')
sub('''            if _is_retryable_conflict_text(str(failed.raw_result))
''', '''            if _is_retryable_conflict_kind(failed.typed)
''')
sub('''        text = str(failed.raw_result)
        if text and not _is_domain_cascade_notice(text):
            return failed
''', '''        if not _is_domain_cascade_notice(failed):
            return failed
''')
sub('''def _is_domain_cascade_notice(text: str) -> bool:''', '''def _is_domain_cascade_notice(failed: _FailedStatement) -> bool:''')
sub('''    return any(marker in text for marker in _DOMAIN_CASCADE_MARKERS)
''', '''    return _detail_kind(failed.typed) == _CASCADE_KIND
''')
sub('''    raw_statement: Any = None
''', '''    typed: Any = None
''')
sub('''        _FailedStatement(index=index, raw_result=statement_result.get("result"), raw_statement=statement_result)''',
    '''        _FailedStatement(
            index=index,
            raw_result=statement_result.get("result"),
            typed=parse_query_error(statement_result) if statement_result.get("kind") else None,
        )''')
p = root / T; text = p.read_text()
m = re.search(r'\ndef _typed_root_cause\(failed: _FailedStatement\) -> object:.*?\n    return failed\.raw_result\n', text, re.S)
assert m
text = text[:m.start()] + '''
def _typed_root_cause(failed: _FailedStatement) -> object:
    """The ONE parse's typed error for a per-statement ERR, else the raw text (amendment 36: parsed once)."""
    return failed.typed if failed.typed is not None else failed.raw_result
''' + text[m.end():]
p.write_text(text)
sub('''    return any(_is_retryable_conflict_text(str(failed.raw_result)) for failed in failed_statements)''',
    '''    return any(_is_retryable_conflict_kind(failed.typed) for failed in failed_statements)''')
print("am36 ok")
````

### §A.5d `myref_a28c_fk8.py` — reference delta 4 (am-36 FK-4 + FK-8)
md5 `d0f3320b55bc119359bd9ea6a06295ca`, 87 lines
````python
"""myref_a28c_fk8.py <tree>: reference delta for amendment 36 FK-4 + FK-8 over myref_a28c_migrate.py (a SAT HOST, not
a spec): ONE per-call operator resolution (a ContextVar record every resolve_operator_principal call fills), the
operator counts carried on the ONE counts model whenever ANY resolution ran (precondition or leg), a leg's
unresolved-operator refusal rendered FROM that model; table_defined None on the zero-I/O invalid-table refusal."""
import pathlib, sys
root = pathlib.Path(sys.argv[1]); P = root / "loremaster/loremaster/principals.py"; G = root / "loremaster/loremaster/governed.py"
def sub(p, old, new, count=1):
    text = p.read_text(); assert text.count(old) == count, (old[:90], text.count(old)); p.write_text(text.replace(old, new))
sub(G, "    table_defined: bool = True\n", "    table_defined: bool | None = True\n")
sub(P, '''async def resolve_operator_principal(principal_store: PrincipalStore) -> Principal | None:''', '''import contextvars as _contextvars

#: a28c reference (amendment 36 FK-8): THE per-call resolution record — every resolution fills it.
_OPERATOR_RESOLUTION: _contextvars.ContextVar[dict[str, int] | None] = _contextvars.ContextVar(
    "_operator_resolution", default=None
)


class _UnresolvedPurpose(str):
    """A leg's unresolved-operator refusal, rendered by the verb FROM the counts model (amendment 36 FK-8)."""


def _operator_unresolved_sentence(counts: Any, purpose: str) -> str:
    return (
        f"cannot resolve THE operator principal {purpose} ({counts.total_principals} principals, "
        f"{counts.admin_principals} admins) — provision a single operator principal (or a single admin) before "
        "migrating"
    )


async def resolve_operator_principal(principal_store: PrincipalStore) -> Principal | None:''')
sub(P, '''    principals = await principal_store.list()
    admins = [principal for principal in principals if principal.role == _ROLE_ADMIN]
    if len(admins) == 1:
        return admins[0]''', '''    principals = await principal_store.list()
    admins = [principal for principal in principals if principal.role == _ROLE_ADMIN]
    record = _OPERATOR_RESOLUTION.get()
    if record is not None:
        record["total"], record["admins"] = len(principals), len(admins)
    if len(admins) == 1:
        return admins[0]''')
sub(P, '''async def _operator_unresolved(principal_store: PrincipalStore, *, purpose: str) -> str:''', '''async def _operator_unresolved(principal_store: PrincipalStore, *, purpose: str) -> str:
    if _OPERATOR_RESOLUTION.get() is not None:
        return _UnresolvedPurpose(purpose)
    return await _operator_unresolved_legacy(principal_store, purpose=purpose)


async def _operator_unresolved_legacy(principal_store: PrincipalStore, *, purpose: str) -> str:''')
sub(P, '''    if agent and owners:
        listed = await principal_store.list()
        total_principals = len(listed)
        admin_principals = sum(1 for principal in listed if principal.role == _ROLE_ADMIN)
        operator = await resolve_operator_principal(principal_store)''', '''    if agent and owners:
        operator = await resolve_operator_principal(principal_store)
        record = _OPERATOR_RESOLUTION.get() or {}
        total_principals, admin_principals = record.get("total"), record.get("admins")''')
sub(P, '''    if table not in _MIGRATE_VALID_TABLES:
        return _not_supported(table, store_was_read=False)
    preconditions = await _agent_migration_preconditions(store, table=table)''', '''    if table not in _MIGRATE_VALID_TABLES:
        return dataclasses.replace(_not_supported(table, store_was_read=False), table_defined=None)
    token = _OPERATOR_RESOLUTION.set({})
    try:
        return await _migrate_governed_resolved(
            table=table, store=store, keep_store=keep_store, principal_store=principal_store
        )
    finally:
        _OPERATOR_RESOLUTION.reset(token)


async def _migrate_governed_resolved(
    *, table: str, store: StoreHandle, keep_store: KeepStore, principal_store: PrincipalStore
) -> MigrateGovernedResult:
    preconditions = await _agent_migration_preconditions(store, table=table)''')
sub(P, '''    else:
        result = _not_supported(table, store_was_read=True)
    return dataclasses.replace(result, preconditions=counts)''', '''    else:
        result = _not_supported(table, store_was_read=True)
    record = _OPERATOR_RESOLUTION.get() or {}
    if "total" in record and counts.total_principals is None:
        from loremaster.governed import MigratePreconditionCounts

        counts = MigratePreconditionCounts(
            **{**counts.model_dump(), "total_principals": record["total"], "admin_principals": record["admins"]}
        )
    if isinstance(result.reason, _UnresolvedPurpose):
        result = dataclasses.replace(result, reason=_operator_unresolved_sentence(counts, str(result.reason)))
    return dataclasses.replace(result, preconditions=counts)''')
print("fk8 ok")
````

### §A.8 `held_harness.patch` — §HELD — `test_surreal_harness.py`'s am-36 re-key (D-9), `git apply --check` OK on HEAD and on #486's copy
md5 `7343bf288709b5674761c78e07b98d0a`, 52 lines
````diff
--- a/loremaster/tests/test_surreal_harness.py	2026-09-27 01:24:56.543076320 -0400
+++ b/loremaster/tests/test_surreal_harness.py	2026-09-27 01:25:10.744447708 -0400
@@ -87,6 +87,7 @@
 
 import _surreal_harness
 import pytest
+from _engine_shapes import typed_conflict_error
 from _surreal_harness import SurrealEnv
 from loremaster.store import _txn as txn_module
 from pydantic import SecretStr
@@ -104,8 +105,10 @@
 )
 
 # The exact live message reported in the bug (surrealdb.errors.QueryError, kind "Query").
-# Its retryable-conflict marker is the seam's ``_txn._RETRYABLE_CONFLICT_MARKER``
-# ("can be retried") — the ONE authority; the harness no longer declares a copy.
+# ⚠ DUAL (63c-i-a contract a28c, amendment 36): detection reads the engine's TYPED kind now — the seam's
+# ``_txn._RETRYABLE_CONFLICT_KIND`` (``details.kind == "TransactionConflict"``, measured 3.2.4) is the ONE
+# authority (was the text marker ``_RETRYABLE_CONFLICT_MARKER``, deleted); the conflict is built in ONE place,
+# ``_engine_shapes.typed_conflict_error``.
 _CONFLICT_MESSAGE = "Transaction conflict: Resource busy. This transaction can be retried"
 
 # A same-shaped ``QueryError`` that is emphatically NOT the retryable conflict —
@@ -183,7 +186,7 @@
 
 
 def _conflict_error() -> QueryError:
-    return QueryError("Query", _CONFLICT_MESSAGE)
+    return typed_conflict_error(_CONFLICT_MESSAGE)
 
 
 def _non_retryable_error() -> QueryError:
@@ -1397,8 +1400,8 @@
         await _surreal_harness.drop_database(_FAKE_ENV)
         assert control.query_calls == 2, "the control leg did not retry; the pin is blind"
 
-        # MUTATION: the seam no longer recognises the engine's prose as a conflict.
-        monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_MARKER", "a marker no engine emits")
+        # MUTATION: the seam no longer recognises the engine's conflict KIND (a28c DUAL: was its prose).
+        monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_KIND", "AKindNoEngineEmits")
 
         mutated = _FakeConnection(query_outcomes=[_conflict_error(), None])
         _patch_connection(monkeypatch, mutated)
@@ -1431,7 +1434,7 @@
             "the control leg did not retry; the pin is blind"
         )
 
-        monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_MARKER", "a marker no engine emits")
+        monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_KIND", "AKindNoEngineEmits")
 
         mutated = _FakeConnection(
             statement_outcomes={
````

### §A.9 `drive_a28c.py` — the mutation driver (declare-then-diff through `scripts/mutation_proof.py`)
md5 `1a3a7aa320d20ce7fcb73909a72f9206`, 33 lines
````python
"""drive_a28c.py [names...]: run each DECLARED mutation (declared_a28c.json) in the REFERENCE copy through
scripts/mutation_proof.py (exact-once anchor, both-way diff vs the declared set, content restore), under the 15 GB
host watchdog; ALSO a content backup + cmp after every run (#509: mutation_proof does not restore on SIGKILL)."""
import json, pathlib, shutil, subprocess, sys, filecmp
S = pathlib.Path(__file__).resolve().parents[1]; REF = S / "ref"; HERE = pathlib.Path(__file__).parent
spec = json.loads((HERE / (__import__("os").environ.get("DECLARED", "declared_a28c.json"))).read_text())["mutations"]
names = sys.argv[1:] or list(spec)
for name in names:
    m = spec[name]; target = REF / m["file"]; backup = HERE / f"{name}.backup"
    shutil.copy2(target, backup)
    anchor, replacement = m["anchor"], m["replacement"]
    if "post_anchor" in m:  # MA3: move the U check to just before the final return (ONE contiguous anchor)
        text = target.read_text(); start = text.index(anchor); end = text.index(m["post_anchor"], start)
        anchor = text[start:end + len("    return _ERROR_CLASS_UNSPECIFIED\n")]
        body = anchor[len(m["anchor"]):]
        replacement = body.replace("    return _ERROR_CLASS_UNSPECIFIED\n", m["anchor"] + "    return _ERROR_CLASS_UNSPECIFIED\n")
    (HERE / f"{name}.anchor").write_text(anchor); (HERE / f"{name}.replacement").write_text(replacement)
    command = [str(S / "guarded.sh"), str(REF), str(HERE / f"{name}.log"), "--", "env", "COLUMNS=4000",
               str(REF / ".venv/bin/python"), str(REF / "scripts/mutation_proof.py"), "--file", m["file"],
               "--anchor-file", str(HERE / f"{name}.anchor"), "--replacement-file", str(HERE / f"{name}.replacement")]
    for node in m["declared"]:
        command += ["--expect-red", node]
    command += ["--", str(REF / ".venv/bin/python"), "-m", "pytest", "-p", "no:cacheprovider", "-q", "-n", "8",
                "--tb=no", "-rfE", *m["targets"]]
    rc = subprocess.run(command).returncode
    restored = filecmp.cmp(target, backup, shallow=False)
    if not restored:
        shutil.copy2(backup, target)
    tail = (HERE / f"{name}.log").read_text().splitlines()[-6:]
    print(f"{name}: exit={rc} restored_byte_exact={restored}{'' if restored else ' (RESTORED FROM CONTENT)'}")
    for line in tail:
        print("    " + line[:220])
    sys.stdout.flush()
````

### §A.9b `declared_a28c_run2.py` — run 2's DECLARATION generator — every anchor, replacement and declared-RED id (ids from `--collect-only`)
md5 `91b0ef1af9348987f5a7302ffd0ba3c4`, 214 lines
````python
"""declared_a28c_run2.py — contract-63c-i-a-a28c's DECLARED mutation set, RUN 2: my OWN wrong builds (never the
adversary's) over the FINAL contract (am-35 + am-34 + am-36) and the FINAL reference (myref_a28c_txn + _migrate +
_am36 + _fk8). RED sets declared BY RULE over the `--collect-only` ids (collected_ref2.txt), frozen to
declared_a28c_run2.json with its timestamp BEFORE any run. Run 1 (superseded by am-36) is recorded in the report."""
import datetime
import itertools
import json
import pathlib

HERE = pathlib.Path(__file__).parent
IDS = [line.strip() for line in (HERE.parent / "collected_ref2.txt").read_text().splitlines() if "::" in line]
A28C = "loremaster/tests/test_fixwave_a28c_63c_i_a.py"
A28 = "loremaster/tests/test_fixwave_a28_63c_i_a.py"
A28B = "loremaster/tests/test_fixwave_a28b_63c_i_a.py"
RS = "loremaster/tests/test_retry_seam.py"
RS_T = [f"{RS}::{c}" for c in ("TestNoGuardedCasHandlerReinterpretsExhaustedContention",
        "TestEveryGuardedCasDoorPropagatesExhaustionUNREAD", "TestTheIndexIsKeyedPerHandler63cIAa28c",
        "TestThereIsExactlyOneCatchScanner63cIAa28c")]
CAS_T = [f"{A28C}::TestThe63cCasHandlersPropagateExhaustionAsTheSameInstance63cIAa28c"]
DETECT = f"{RS}::TestDetectionFollowsTheOneSharedMarker"
TXN = "loremaster/loremaster/store/_txn.py"; SERVER = "loremaster/loremaster/server.py"
FIND = "loremaster/loremaster/findings.py"; AGENTS = "loremaster/loremaster/agents.py"
PRIN = "loremaster/loremaster/principals.py"; GOV = "loremaster/loremaster/governed.py"
ECHO = f"{A28C}::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing"
KB = f"{A28C}::TestKBTheClassIgnoresEchoedValues::test_KB_a_hostile_echoed_value_never_moves_the_class"
READERS = f"{A28C}::TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c"
TYPED = f"{A28C}::TestTheRecordShapeIsTypedOnTheTransactionalPath63cIAa28c"
MAP = f"{A28C}::TestTheOneMappingHelperBuildsTheClassEverywhere63cIAa28c::test_am35_2_4_mutating_the_mapping_helper_moves_every_identity_leg"
GATE = f"{A28C}::TestTheGateIsTheVisibilitySeam63cIAa28c"
KC = f"{A28C}::TestKCAMultiKeepMemberIsNotForeign::test_KC_householded_here_plus_another_relation_proceeds"
GATING = f"{A28}::TestAFieldIsNoneIffItsReadWasGatedOff63cIAa28b::test_am32_a_field_is_None_iff_its_read_was_gated_off"
MEAS = f"{A28}::TestTheMeasuredCountsAreTypedFields63cIAa28"
FIELDOFF = f"{A28}::TestAFieldIsNoneIffItsReadWasGatedOff63cIAa28b"
F5 = f"{A28C}::TestAnUndefinedTargetTableIsATypedAnswer63cIAa28c"
EMPTY = f"{A28C}::TestEmptyContributesNoOwnerSentence63cIAa28c::test_am34_2_an_empty_classification_adds_no_owner_sentence"
TRIPLE = f"{A28C}::TestTheOwnerTripleIsConsistentByConstruction63cIAa28c::test_am34_2_the_model_refuses_every_contradictory_triple"
PATHS = ("run_query", "execute_transaction")
HOSTS = ("assert-violation", "coercion-failure", "governed-throw", "record-id-collision", "unique-index-collision")


def only(ids):
    missing = [i for i in ids if i not in IDS]
    assert not missing, f"declared ids not collected: {missing}"
    return sorted(set(ids))


def phrases():
    return sorted({i[len(ECHO) + 1:-1].split("-", 2)[-1].rsplit("-", 1)[0] for i in IDS if i.startswith(ECHO + "[")
                   for _ in [0]})


def echo(hosts, phrase_filter, paths=PATHS):
    out = []
    for i in IDS:
        if not i.startswith(ECHO + "["):
            continue
        inner = i[len(ECHO) + 1:-1]
        host = next(h for h in HOSTS if inner.startswith(h + "-"))
        rest = inner[len(host) + 1:]
        phrase, path = rest.rsplit("-", 1)
        if host in hosts and phrase_filter(phrase) and path in paths:
            out.append(i)
    return out


def ids_in(prefix):
    return [i for i in IDS if i.startswith(prefix + "::") or i.startswith(prefix + "[")]


def legal(o, d, c):
    if c is None or o is None or d is None:
        return c is None and o is None and d is None
    if c == "empty":
        return o == 0 and d == 0
    return o > 0 and d > 0


ILLEGAL = [f"{TRIPLE}[owned{o}-distinct{d}-{c}]" for o, d, c in itertools.product(
    (None, 0, 3), (None, 0, 2), (None, "operator", "foreign", "mixed", "unclassified", "empty")) if not legal(o, d, c)]
NON_TEXT_KINDS = ("AlreadyExists", "Configuration", "NotAllowed", "NotFound", "Query", "Serialization")
PRE = ("                visible = await resolve_visible_keeps(keep_store, member_email=principal.email)\n"
       "                if keep_scope(existing_bare) not in visible:\n")
POST = ("            visible = await resolve_visible_keeps(keep_store, member_email=principal.email)\n"
        "            if keep_scope(session_keep_bare) not in visible:\n")
B13_CELLS = [f"{GATE}::test_am35_1_1_the_register_proceeds_iff_THIS_keep_is_visible[{s}-other-keep-first]" for s in
             ("keeper-of-other+member-of-this", "member-of-other+member-of-this",
              "keeper-of-other+member-of-other+member-of-this")] + [
    f"{KC}[{e}-other-keep-first]" for e in ("keeper-of-another-keep", "householded-in-another-keep")]
# run 1 OBSERVED these two extra kills of the post-mint B13 (the race registrants keep several sessions) — declared
# here WITH that provenance (a set informed by a prior run is stated as such, never presented as a blind prediction).
B13_RACES = [f"{A28}::TestTheRaceNeverStrandsAScope63cIAa28::test_RS2_eight_way_registers_never_strand_a_scope",
             f"{A28}::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error"]
M = {}
M["R2-MA1-U-substring-not-prefix"] = dict(file=TXN, anchor="        if lowered.startswith(_UNIQUE_INDEX_MARKER):\n",
    replacement="        if _UNIQUE_INDEX_MARKER in lowered:\n", targets=[A28C, A28B],
    declared=only(echo(("assert-violation", "coercion-failure"), lambda p: p in ("host-unique-index-collision", "marker_UNIQUE_INDEX_MARKER"))
                  + [f"{KB}[assert-echoes-index-words-{q}]" for q in PATHS]))
M["R2-MA2-governed-for-every-kind-unanchored"] = dict(file=TXN,
    anchor='    if kind == "Thrown" or kind is None:\n        if lowered.startswith(_ENGINE_THROW_PREFIX + _GOVERNED_CONFLICT_MARKER):\n',
    replacement="    if True:\n        if _GOVERNED_CONFLICT_MARKER in lowered:\n", targets=[A28C, A28B],
    declared=only(echo(("assert-violation", "coercion-failure", "unique-index-collision"), lambda p: p in ("host-governed-throw", "marker_GOVERNED_CONFLICT_MARKER"))
                  + [f"{KB}[unique-echoes-governed-marker-{q}]" for q in PATHS]
                  + [f"{READERS}::test_am36_1_2_3_a_typed_kind_never_reaches_the_text_branch[{k}-governed]" for k in NON_TEXT_KINDS]))
M["R2-MA3-U-checked-after-assert-and-coercion"] = dict(file=TXN,
    anchor="        if lowered.startswith(_UNIQUE_INDEX_MARKER):\n            return _ERROR_CLASS_UNIQUE_VIOLATION\n        if _ASSERT_VIOLATION_MARKER in lowered:\n            return _ERROR_CLASS_ASSERT_VIOLATION\n        if _FIELD_COERCION_MARKER in lowered:\n            return _ERROR_CLASS_FIELD_COERCION\n",
    replacement="        if _ASSERT_VIOLATION_MARKER in lowered:\n            return _ERROR_CLASS_ASSERT_VIOLATION\n        if _FIELD_COERCION_MARKER in lowered:\n            return _ERROR_CLASS_FIELD_COERCION\n        if lowered.startswith(_UNIQUE_INDEX_MARKER):\n            return _ERROR_CLASS_UNIQUE_VIOLATION\n",
    targets=[A28C, A28B],
    declared=only(echo(("unique-index-collision",), lambda p: p in ("marker_ASSERT_VIOLATION_MARKER", "marker_FIELD_COERCION_MARKER", "host-assert-violation", "host-coercion-failure"))
                  + [f"{KB}[unique-echoes-assert-words-{q}]" for q in PATHS]))
M["R2-MA4-record-text-pair-kept"] = dict(file=TXN,
    anchor="        if lowered.startswith(_UNIQUE_INDEX_MARKER):\n            return _ERROR_CLASS_UNIQUE_VIOLATION\n",
    replacement='        if lowered.startswith(_UNIQUE_INDEX_MARKER):\n            return _ERROR_CLASS_UNIQUE_VIOLATION\n        if "database record" in lowered and "already exists" in lowered:\n            return _ERROR_CLASS_UNIQUE_VIOLATION\n',
    targets=[A28C, A28B],
    declared=only(echo(("assert-violation", "coercion-failure"), lambda p: p == "host-record-id-collision")
                  + [f"{TYPED}::test_am35_2_1_the_record_TEXT_pair_is_deleted_an_untyped_record_wording_is_not_the_class[{q}]" for q in PATHS]
                  + [f"{KB}[coerce-echoes-record-words-{q}]" for q in PATHS]))
M["R2-MA5-txn-path-classifies-raw-text"] = dict(file=TXN,
    anchor="            error_class = _classify_engine_error(_typed_root_cause(root_cause))\n",
    replacement="            error_class = _classify_engine_error(root_cause.raw_result)\n", targets=[A28C, A28B],
    declared=only([f"{TYPED}::test_am35_2_1_the_class_iff_the_sdk_says_the_record_id_is_taken_on_execute_transaction[Record-{w}]" for w in ("engine-wording", "reworded")]
                  + echo(("record-id-collision",), lambda p: True, ("execute_transaction",))
                  + [f"{A28B}::TestTheDriverTypesAnIdentityTakenRejection63cIAa28b::test_am32_1_3_ab_every_raise_site_types_exactly_the_identity_taken_rejection[record-id-collision-execute_transaction]",
                     f"{MAP}[record-id-collision-execute_transaction]"]))
M["R2-MA6-typed-branch-bypasses-helper"] = dict(file=TXN,
    anchor="            error_class = _classify_engine_error(error)\n            logger.error(\n",
    replacement='            if isinstance(error, AlreadyExistsError) and error.record_id is not None:\n                raise TxnUniqueViolationError("typed, built directly") from error\n            error_class = _classify_engine_error(error)\n            logger.error(\n',
    targets=[A28C, A28B], declared=only([f"{MAP}[record-id-collision-run_query]"]))
M["R2-MR1-retry-decision-reads-text"] = dict(file=TXN,
    anchor="    return isinstance(error, ServerError) and _detail_kind(error) == _RETRYABLE_CONFLICT_KIND\n",
    replacement='    return "can be retried" in str(error)\n', targets=[A28C, DETECT],
    declared=only(echo(HOSTS, lambda p: p == "engine-conflict-commit")
                  + [f"{READERS}::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier"]
                  + [i for i in IDS if i.startswith(DETECT + "::")]))
M["R2-MR2-cascade-selector-reads-text"] = dict(file=TXN,
    anchor="    return _detail_kind(failed.typed) == _CASCADE_KIND\n",
    replacement='    return str(failed.raw_result).startswith(("The query was not executed due to", "Cannot COMMIT: the transaction was aborted"))\n',
    targets=[A28C],
    declared=only(echo(HOSTS, lambda p: p in ("engine-cascade-0", "engine-cascade-1"), ("execute_transaction",))
                  + [f"{READERS}::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier"]))
M["R2-MG1-pre-gate-private-visibility"] = dict(file=SERVER, anchor=PRE,
    replacement="                visible = frozenset(\n                    keep_scope(keep)\n                    for keep in await keep_store.list_keeps_for_member(member_email=principal.email)\n                )\n                if keep_scope(existing_bare) not in visible:\n",
    targets=[A28C, A28B, A28],
    declared=only([f"{GATE}::test_am35_1_2_the_gate_READS_the_seam[{leg}]" for leg in ("hide-this-keep-from-a-member", "show-this-keep-to-a-stranger")]))
M["R2-MG1b-post-mint-private-visibility"] = dict(file=SERVER, anchor=POST,
    replacement="            visible = frozenset(\n                keep_scope(keep) for keep in await keep_store.list_keeps_for_member(member_email=principal.email)\n            )\n            if keep_scope(session_keep_bare) not in visible:\n",
    targets=[A28C, A28B, A28],
    declared=only([f"{GATE}::test_am35_1_2_the_gate_READS_the_seam[show-this-keep-to-a-stranger]"]))
M["R2-MG2-post-mint-primary-keep-B13"] = dict(file=SERVER, anchor="            if keep_scope(session_keep_bare) not in visible:\n",
    replacement="            if not visible or keep_scope(session_keep_bare) != min(visible):\n", targets=[A28C, A28B, A28],
    declared=only(B13_CELLS + B13_RACES))
M["R2-MG2b-pre-gate-primary-keep-B13"] = dict(file=SERVER, anchor="                if keep_scope(existing_bare) not in visible:\n",
    replacement="                if not visible or keep_scope(existing_bare) != min(visible):\n", targets=[A28C, A28B, A28],
    declared=only(B13_CELLS + B13_RACES))
M["R2-MS1-S8-second-try-in-annotate"] = dict(file=FIND,
    anchor='                ) from error\n            raise\n        updated = await self._select_row_by_id(finding_id)\n        if updated is None:\n            raise FindingNotFoundError(f"no finding with id {finding_id!r}")\n        return self._row_to_finding(updated)\n',
    replacement='                ) from error\n            raise\n        try:\n            await self._apply([self._guarded_append_fragment(finding_id, event)])\n        except TxnContentionExhaustedError:\n            fresh_after = await self._select_row_by_id(finding_id)\n            return self._row_to_finding(fresh_after)\n        updated = await self._select_row_by_id(finding_id)\n        if updated is None:\n            raise FindingNotFoundError(f"no finding with id {finding_id!r}")\n        return self._row_to_finding(updated)\n',
    targets=RS_T + CAS_T,
    declared=only([f"{RS}::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set",
                   f"{RS}::TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::test_the_transactional_doors_never_re_read_after_exhaustion[findings.py::annotate::1]"]))
M["R2-MS2-S4-inline-select-door"] = dict(file=FIND,
    anchor="        if _TABLE_SEPARATOR in text:\n            return text.split(_TABLE_SEPARATOR, 1)[1]\n        return text\n",
    replacement='        if _TABLE_SEPARATOR in text:\n            return text.split(_TABLE_SEPARATOR, 1)[1]\n        return text\n\n\nclass _S4InlineReRead:\n    async def probe(self) -> Any:\n        try:\n            await self._apply()\n        except SurrealStoreError:\n            return await self._query("SELECT * FROM finding WHERE id = $id")\n',
    targets=RS_T + CAS_T,
    declared=only([f"{RS}::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set"]))
M["R2-MS3-S7-rereading-exhaustion-clause-in-RS5"] = dict(file=AGENTS,
    anchor="            except TxnUniqueViolationError:\n                # amendment 29 RS-5",
    replacement="            except TxnContentionExhaustedError:\n                await self._select_row(agent_id)\n                raise\n            except TxnUniqueViolationError:\n                # amendment 29 RS-5",
    targets=RS_T + CAS_T,
    declared=only([f"{RS}::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set",
                   f"{RS}::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_typed_catch_enumeration_matches_the_canonical_set_and_the_partition_is_complete"]))
M["R2-MC3-RS5-translates-exhaustion"] = dict(file=AGENTS,
    anchor="            except TxnUniqueViolationError:\n                # amendment 29 RS-5",
    replacement='            except TxnContentionExhaustedError as contention:\n                raise AgentRegistryError("contention") from contention\n            except TxnUniqueViolationError:\n                # amendment 29 RS-5',
    targets=RS_T + CAS_T,
    declared=only([f"{A28C}::TestThe63cCasHandlersPropagateExhaustionAsTheSameInstance63cIAa28c::test_FK_r3_4_the_injected_instance_reaches_the_caller_and_a_real_loss_is_the_ruled_verdict[agents.py::register]"]))
M["R2-MM1-no-invariant-validator"] = dict(file=GOV,
    anchor='        if not legal:\n            raise ValueError(f"contradictory owner triple: {owned=} {distinct=} {classification=}")\n',
    replacement="", targets=[A28C], declared=only(ILLEGAL))
M["R2-MM3-operator-counts-always-measured"] = dict(file=PRIN,
    anchor='    if agent and owners:\n        operator = await resolve_operator_principal(principal_store)\n        record = _OPERATOR_RESOLUTION.get() or {}\n        total_principals, admin_principals = record.get("total"), record.get("admins")\n',
    replacement='    if agent:\n        _listed = await principal_store.list()\n        total_principals = len(_listed)\n        admin_principals = sum(1 for principal in _listed if principal.role == _ROLE_ADMIN)\n    if agent and owners:\n        operator = await resolve_operator_principal(principal_store)\n        record = _OPERATOR_RESOLUTION.get() or {}\n        total_principals, admin_principals = record.get("total"), record.get("admins")\n',
    targets=[A28, A28C],
    declared=only([f"{MEAS}::test_am30_the_served_fields_are_the_measured_counts[P_message]"]
                  + [f"{MEAS}::test_am30_pin1_perturbing_a_field_moves_the_reason[{f}-P_message]" for f in
                     ("unscoped_agents", "dangling_sender_messages", "owned_but_unscoped_messages", "scoped_but_ownerless_messages")]
                  + [f"{FIELDOFF}::test_am32_the_message_leg_refusal_serves_measured_agent_zeros"]))
M["R2-MM4-leg-unresolved-sentence-not-from-fields"] = dict(file=PRIN,
    anchor="        result = dataclasses.replace(result, reason=_operator_unresolved_sentence(counts, str(result.reason)))\n",
    replacement="        result = dataclasses.replace(\n            result, reason=await _operator_unresolved_legacy(principal_store, purpose=str(result.reason))\n        )\n",
    targets=[A28, A28C],
    declared=only([f"{MEAS}::test_am30_pin1_perturbing_a_field_moves_the_reason[{f}-P_leg_unresolved]" for f in ("total_principals", "admin_principals")]))
M["R2-MM6-F5-branch-deleted"] = dict(file=PRIN,
    anchor="    elif table in (MEMORY_TABLE, AGENT_TABLE, MESSAGE_TABLE) and table not in preconditions.defined_tables:\n        from loremaster.governed import MigrateGovernedResult\n\n        result = MigrateGovernedResult(\n            table=table, scanned=0, backfilled=0, already_migrated=0, refused=False, table_defined=False\n        )\n",
    replacement="", targets=[A28, A28C],
    declared=only([f"{F5}::test_am34_4_an_undefined_target_answers_table_defined_False_after_ONE_probe[{t}-{s}]" for t in ("agent", "memory", "message") for s in ("minimal", "realistic")]
                  + [f"{GATING}[{t}-{s}]" for t, s in (("agent", "message-only"), ("agent", "neither-defined"), ("message", "agent-only"), ("message", "neither-defined"))]))
M["R2-MM6b-table-defined-True-on-the-unread-refusal"] = dict(file=PRIN,
    anchor="        return dataclasses.replace(_not_supported(table, store_was_read=False), table_defined=None)\n",
    replacement="        return _not_supported(table, store_was_read=False)\n", targets=[A28C],
    declared=only([i for i in IDS if i.startswith(f"{F5}::test_am36_FK4_table_defined_is_None_when_INFO_FOR_DB_never_ran[")]))
M["R2-MM7-render-keyed-on-counts"] = dict(file=PRIN, anchor="        if not result.table_defined:\n",
    replacement="        if result.scanned == 0 and result.backfilled == 0:\n", targets=[A28C],
    declared=only([f"{F5}::test_am34_4_the_cli_render_derives_the_sentence_from_the_typed_field[True]"]))
M["R2-MM8-empty-adds-an-owner-sentence"] = dict(file=PRIN, anchor="    parts: list[str] = []\n    if counts.dangling_sender_messages:\n",
    replacement='    parts: list[str] = []\n    if counts.owner_classification == "empty":\n        parts.append("Owned by nobody — nothing to classify.")\n    if counts.dangling_sender_messages:\n',
    targets=[A28, A28C], declared=only([f"{EMPTY}[{p}]" for p in ("P_message", "RS-1")]))
M["R2-MT1-a-second-catch-scanner"] = dict(file="loremaster/tests/_catch_sites.py", anchor="def production_catch_sites() -> list[CatchSite]:\n",
    replacement="def _second_scanner(tree: ast.AST) -> list[Any]:\n    from loremaster.store._txn import SurrealStoreError\n\n    return [(node.handlers, SurrealStoreError) for node in ast.walk(tree) if isinstance(node, ast.Try)]\n\n\ndef production_catch_sites() -> list[CatchSite]:\n",
    targets=RS_T, declared=only([f"{RS}::TestThereIsExactlyOneCatchScanner63cIAa28c::test_am34_5_exactly_one_walker_and_one_resolver_in_the_tree"]))

if __name__ == "__main__":
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    (HERE / "declared_a28c_run2.json").write_text(json.dumps({"declared_at": stamp, "mutations": M}, indent=1))
    print(stamp, {k: len(v["declared"]) for k, v in M.items()})
````

### §A.9c `declared_a28c_run2b.json` — run 2b's declaration
md5 `941974179e0e1ac5a5d6107b4cbf646f`, 25 lines
````json
{
 "declared_at": "2026-09-27T01:58:58-04:00",
 "mutations": {
  "R2-MR2b-cascade-selector-substring": {
   "file": "loremaster/loremaster/store/_txn.py",
   "anchor": "    return _detail_kind(failed.typed) == _CASCADE_KIND\n",
   "replacement": "    return any(opening in str(failed.raw_result) for opening in (\"The query was not executed due to\", \"Cannot COMMIT: the transaction was aborted\"))\n",
   "targets": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py"
   ],
   "declared": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[assert-violation-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[assert-violation-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[coercion-failure-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[coercion-failure-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[governed-throw-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[governed-throw-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[record-id-collision-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[record-id-collision-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[unique-index-collision-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[unique-index-collision-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier"
   ]
  }
 }
}
````

### §A.9d `declared_a28c_run2c.json` — run 2c's declaration (the D-12 re-proofs + R2c-MR3)
md5 `1a3de5f04c6080a64272de36078a7335`, 112 lines
````json
{
 "declared_at": "2026-09-27T03:11:26-04:00",
 "mutations": {
  "R2c-MR1-retry-decision-reads-text": {
   "file": "loremaster/loremaster/store/_txn.py",
   "anchor": "    return isinstance(error, ServerError) and _detail_kind(error) == _RETRYABLE_CONFLICT_KIND\n",
   "replacement": "    return \"can be retried\" in str(error)\n",
   "targets": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker"
   ],
   "declared": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[assert-violation-engine-conflict-commit-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[assert-violation-engine-conflict-commit-run_query]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[coercion-failure-engine-conflict-commit-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[coercion-failure-engine-conflict-commit-run_query]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[governed-throw-engine-conflict-commit-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[governed-throw-engine-conflict-commit-run_query]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[record-id-collision-engine-conflict-commit-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[record-id-collision-engine-conflict-commit-run_query]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[unique-index-collision-engine-conflict-commit-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[unique-index-collision-engine-conflict-commit-run_query]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[AgentRegistry]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[BriefLedger]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[DiffEngine]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[FindingLedger]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[FloorCalibrationStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[KeepStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[LocalMemoryBackend]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[MessageLedger]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[PrincipalKeyStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[PrincipalStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[SnapshotStamper]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[SurrealCodeGraph]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[SurrealLeaseStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[SurrealManifest]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[SurrealStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_new_marker_starts_being_a_conflict[TaskLedger]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[AgentRegistry]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[BriefLedger]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[DiffEngine]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[FindingLedger]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[FloorCalibrationStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[KeepStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[LocalMemoryBackend]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[MessageLedger]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[PrincipalKeyStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[PrincipalStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[SnapshotStamper]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[SurrealCodeGraph]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[SurrealLeaseStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[SurrealManifest]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[SurrealStore]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_old_text_stops_being_a_conflict[TaskLedger]",
    "loremaster/tests/test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker::test_the_transactional_caller_follows_the_marker_too"
   ]
  },
  "R2c-MR2-cascade-selector-reads-text-prefix": {
   "file": "loremaster/loremaster/store/_txn.py",
   "anchor": "    return _detail_kind(failed.typed) == _CASCADE_KIND\n",
   "replacement": "    return str(failed.raw_result).startswith((\"The query was not executed due to\", \"Cannot COMMIT: the transaction was aborted\"))\n",
   "targets": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py"
   ],
   "declared": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier"
   ]
  },
  "R2c-MR2b-cascade-selector-substring": {
   "file": "loremaster/loremaster/store/_txn.py",
   "anchor": "    return _detail_kind(failed.typed) == _CASCADE_KIND\n",
   "replacement": "    return any(opening in str(failed.raw_result) for opening in (\"The query was not executed due to\", \"Cannot COMMIT: the transaction was aborted\"))\n",
   "targets": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py"
   ],
   "declared": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[assert-violation-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[assert-violation-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[coercion-failure-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[coercion-failure-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[governed-throw-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[governed-throw-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[record-id-collision-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[record-id-collision-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[unique-index-collision-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[unique-index-collision-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier"
   ]
  },
  "R2c-MR3-cascade-text-helper-base-shape": {
   "file": "loremaster/loremaster/store/_txn.py",
   "anchor": "def _is_domain_cascade_notice(failed: _FailedStatement) -> bool:\n    \"\"\"Whether ``text`` is rollback NOISE (a non-execution or COMMIT-abort\n    notice) rather than a substantive engine rejection \u2014 see\n    :data:`_DOMAIN_CASCADE_MARKERS`.\n    \"\"\"\n    return _detail_kind(failed.typed) == _CASCADE_KIND\n",
   "replacement": "def _is_domain_cascade_notice(failed: _FailedStatement) -> bool:\n    \"\"\"Whether ``text`` is rollback NOISE (a non-execution or COMMIT-abort\n    notice) rather than a substantive engine rejection \u2014 see\n    :data:`_DOMAIN_CASCADE_MARKERS`.\n    \"\"\"\n    return _is_cascade_text(str(failed.raw_result))\n\n\ndef _is_cascade_text(text: str) -> bool:\n    return any(opening in text for opening in (\"The query was not executed due to\", \"Cannot COMMIT: the transaction was aborted\"))\n",
   "targets": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py"
   ],
   "declared": [
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[assert-violation-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[assert-violation-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[coercion-failure-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[coercion-failure-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[governed-throw-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[governed-throw-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[record-id-collision-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[record-id-collision-engine-cascade-1-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[unique-index-collision-engine-cascade-0-execute_transaction]",
    "loremaster/tests/test_fixwave_a28c_63c_i_a.py::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c::test_am36_1_2_an_echoed_phrase_moves_nothing[unique-index-collision-engine-cascade-1-execute_transaction]"
   ]
  }
 }
}
````

### §A.10a `ast_receipt.py` — the §3 AST-equality receipt for the adversary's kill probes
md5 `00f3f27992ad46ea3e4b1f5f777c27e3`, 27 lines
````python
"""ast_receipt.py <probe-file> <landed-file> [--control]: every top-level def / class / assignment NAMED in the
adversary's kill-probe file that the contract LANDED, compared by ast.dump (docstrings stripped, no positions).
--control mutates the landed KC (first Compare op → NotEq) to prove the instrument can see a change."""
import ast, sys
def strip(node):
    for n in ast.walk(node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
    return ast.dump(node, include_attributes=False)
def named(tree):
    out = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): out[n.name] = n
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                if isinstance(t, ast.Name): out[t.id] = n
    return out
probe = named(ast.parse(open(sys.argv[1]).read())); landed = named(ast.parse(open(sys.argv[2]).read()))
if "--control" in sys.argv:
    kc = landed["TestKCAMultiKeepMemberIsNotForeign"]
    next(n for n in ast.walk(kc) if isinstance(n, ast.Compare)).ops[0] = ast.NotEq()
for name in sorted(probe):
    if name in ("_class_name",) or name not in landed: 
        print(f"{'NOT LANDED' if name not in landed else 'EQUAL'} {name}" if name not in landed else "", end="")
        if name not in landed: print()
        continue
    print(("EQUAL " if strip(probe[name]) == strip(landed[name]) else "DIFF  ") + name)
````

### §A.10b `sync.sh` — copies the contract files into both scratch trees
md5 `282e5ce50526ba9029c290b822eecd64`, 8 lines
````bash
#!/usr/bin/env bash
# sync.sh: copy MY contract files (main tree) into both scratch copies (base = 169925f production, ref = reference),
# plus the §HELD harness re-key (test_surreal_harness.py from held/b — HEAD content + the held patch).
set -euo pipefail
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/7f90d234-286c-41e2-9fa2-be04af4a6e1f/scratchpad
M=/home/ejprice/PycharmProjects/lore
FILES="loremaster/tests/_engine_shapes.py loremaster/tests/test_fixwave_a28c_63c_i_a.py loremaster/tests/test_fixwave_a28_63c_i_a.py loremaster/tests/test_fixwave_a28b_63c_i_a.py loremaster/tests/test_retry_seam.py loremaster/tests/test_surreal_store.py loremaster/tests/test_txn_contention.py loremaster/tests/test_reanchor_58_r3_cas_seam.py loremaster/tests/test_governed_migration_63a.py loremaster/tests/test_reanchor_58_r3_tiers.py loremaster/tests/_exhaustion_fates.py loremaster/tests/test_exhaustion_fates.py"
for t in base ref; do for f in $FILES; do cp "$M/$f" "$S/$t/$f"; done; cp "$S/held/b/loremaster/tests/test_surreal_harness.py" "$S/$t/loremaster/tests/test_surreal_harness.py"; done
````

### §A.10c `guarded.sh` — 15 GB MemAvailable watchdog, process-tree kill by PID
md5 `44afe87cb28499856ba98768339b40c2`, 22 lines
````bash
#!/usr/bin/env bash
# guarded.sh <dir> <logfile> -- <command...>: run <command> in <dir>; every 8 s, if host MemAvailable < ${FLOOR_GB:-15} GB,
# kill the command's WHOLE process tree by PID (descendants first) — never a pattern. Watchdog events → <logfile>.watchdog.
# Exit = the command's exit, or 137 when the watchdog fired.
set -u
dir=$1; log=$2; shift 3
cd "$dir" || exit 2
"$@" >"$log" 2>&1 &
pid=$!
tree() { local p=$1; echo "$p"; for c in $(pgrep -P "$p"); do tree "$c"; done; }
fired=0
while kill -0 "$pid" 2>/dev/null; do
  avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  if [ "$avail_kb" -lt $(( ${FLOOR_GB:-15} * 1024 * 1024 )) ]; then
    pids=$(tree "$pid" | tac)
    echo "$(date -Is) MemAvailable=${avail_kb}kB < ${FLOOR_GB:-15}GB — killing tree: $pids" >>"$log.watchdog"
    kill -TERM $pids 2>/dev/null; sleep 3; kill -KILL $pids 2>/dev/null; fired=1; break
  fi
  sleep 8
done
wait "$pid"; rc=$?
[ "$fired" = 1 ] && exit 137 || exit $rc
````

### §A.10d `quiet_run.sh` — waits for a quiet host; retries only on the watchdog's 137
md5 `b84deb5e92bfe38167a83f5c9ae222f5`, 18 lines
````bash
#!/usr/bin/env bash
# quiet_run.sh <attempts> -- <command...>: before each attempt WAIT FOR QUIET (host MemAvailable >= ${QUIET_GB:-22} GB on 3
# consecutive 20 s checks); run the command; retry ONLY on exit 137 (the guarded.sh watchdog). Logs waits to stderr.
set -u
attempts=$1; shift 2
for try in $(seq 1 "$attempts"); do
  ok=0
  while [ "$ok" -lt 3 ]; do
    avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
    if [ "$avail" -ge "${QUIET_GB:-22}" ]; then ok=$((ok+1)); else ok=0; fi
    [ "$ok" -lt 3 ] && sleep 20
  done
  echo "$(date -Is) attempt $try: quiet (${avail} GB)" >&2
  "$@"; rc=$?
  [ "$rc" != 137 ] && exit "$rc"
  echo "$(date -Is) attempt $try: watchdog kill (137) — waiting for quiet again" >&2
done
exit 137
````

### §A.10e `sat_compare2.py` — the both-way SAT diff (asserts every summary line is accounted for)
md5 `97d6b36d8c5217e6e2a12e48cbce45c8`, 18 lines
````python
"""sat_compare2.py base.log ref.log — red ids (FAILED/ERROR summary lines, id = text before the first ' - ') both ways."""
import sys, collections
def reds(p):
    out = set()
    for line in open(p, errors="replace"):
        for tag in ("FAILED ", "ERROR "):
            if line.startswith(tag):  # EVERY summary line — a path filter here once dropped scripts/ reds
                out.add(line[len(tag):].split(" - ", 1)[0].strip())
    return out
b, r = reds(sys.argv[1]), reds(sys.argv[2])
for p_, s_ in ((sys.argv[1], b), (sys.argv[2], r)):
    n_lines = sum(1 for l in open(p_, errors="replace") if l.startswith(("FAILED ", "ERROR ")))
    assert n_lines == len(s_), (p_, n_lines, len(s_))  # every summary line accounted for, no silent drop
print(f"base red {len(b)} · ref red {len(r)} · shared {len(b & r)} · base-only (fixed) {len(b - r)} · REF-ONLY {len(r - b)}")
for label, s in (("REF-ONLY", r - b), ("BASE-ONLY", b - r), ("SHARED", b & r)):
    c = collections.Counter(i.split("::")[0] for i in s)
    print(f"--- {label} by file"); [print(f"  {n:4d} {f}") for f, n in c.most_common()]
for i in sorted(r - b): print("REF-ONLY", i)
````

### §A.10f `conc20_a28c.sh` — the 20-consecutive concurrency driver
md5 `cc18fd08a7eaa3bff20566260cc31720`, 27 lines
````bash
#!/usr/bin/env bash
# conc20_a28c.sh <tree> <n>: <n> consecutive, SERIAL invocations of the concurrency pins in <tree> (store-ref §5:
# a concurrency pin is cleared only by 20 consecutive greens). Each invocation = a28b's set (RS-2 20 rounds x
# 8-way incl. the R-1 post-mint leg; RS-5 handler + registry 20 x 8; the keeps REAL unique-key 8-way) + the whole
# #102 contention file (live 16-way contention; am-36 changed the retry DECISION those pins exercise).
# Stops at the FIRST non-green invocation (a red is a STOP, never "flaky"). One line per run with the counts.
set -uo pipefail
tree=$1; n=$2; expected=$3
cd "$tree" || exit 2
ids=(
  "loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_RS2_eight_way_registers_never_strand_a_scope"
  "loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28"
  "loremaster/tests/test_fixwave_a28b_63c_i_a.py::TestKeepsCasDecidesFromTheOneClass63cIAa28b::test_am32_1_2_the_REAL_unique_key_conflict_converges_eight_way"
  "loremaster/tests/test_txn_contention.py"
)
for run in $(seq 1 "$n"); do
  out=$(.venv/bin/python -m pytest -q -p no:cacheprovider -n 4 -rfE "${ids[@]}" 2>&1)
  code=$?
  tail_line=$(printf '%s\n' "$out" | tail -1)
  echo "run $run: exit=$code :: $tail_line"
  if [ "$code" -ne 0 ] || ! printf '%s' "$tail_line" | awk -v e="$expected passed" 'index($0, e) && !/failed|error/ {ok=1} END {exit !ok}'; then
    printf '%s\n' "$out" | tail -40
    echo "STOP at run $run"
    exit 1
  fi
done
echo "ALL $n CONSECUTIVE GREEN"
````

### §A.10g `orphans.py` — the broken-wrap detector (D-13)
md5 `f3c270a738ee76c9fc8a032d33e8b8b5`, 31 lines
````python
"""orphans.py <files>: a comment / docstring line of <=2 words squeezed between two longer lines of the same
prefix — the signature of a broken re-wrap (a line split mid-sentence, the tail stranded). Only lines in the
working-tree diff vs HEAD are reported (pre-existing prose is not mine)."""
import re, subprocess, sys
for path in sys.argv[1:]:
    diff = subprocess.run(["git", "diff", "-U0", "HEAD", "--", path], capture_output=True, text=True).stdout
    added = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.M):
        start, count = int(m.group(1)), int(m.group(2) or 1)
        added.update(range(start, start + count))
    if not diff and subprocess.run(["git", "ls-files", "--error-unmatch", path], capture_output=True).returncode:
        added = None  # untracked: every line is mine
    lines = open(path).read().split("\n")
    def prefix(l):
        m = re.match(r"^(\s*(?:#:?\s*)?)", l); return m.group(1)
    for i in range(1, len(lines) - 1):
        n = i + 1
        if added is not None and n not in added:
            continue
        cur, prev, nxt = lines[i], lines[i - 1], lines[i + 1]
        body = cur.strip().lstrip("#:").strip()
        if not body or len(body.split()) > 2 or body.startswith(("```", '"""', ")", "]", "}", "-", "|")):
            continue
        if prefix(cur) != prefix(prev) or len(prev.rstrip()) < 95:
            continue
        if not nxt.strip() or prefix(nxt) != prefix(cur):
            continue
        is_comment = cur.lstrip().startswith("#")
        if not is_comment and (cur.strip().endswith((",", "(", ")")) or "=" in cur or cur.strip().startswith(("return", "assert", "await", "if ", "for "))):
            continue
        print(f"{path}:{n}: {cur.strip()[:60]!r}   (prev ends: …{prev.rstrip()[-40:]!r})")
````

### §A.10h `refill.py` — the whitespace-only paragraph refill (D-13), self-proving
md5 `7bd11e77c2baf32f6161e43cc244c1a3`, 93 lines
````python
"""refill.py <files>: refill every comment / docstring PARAGRAPH that holds a broken-wrap orphan, where every
line of the paragraph is one of MY added lines (git diff vs HEAD; an untracked file is all mine). Width 110.
Paragraph = contiguous lines with the same prefix (``# `` / ``#: `` / docstring indent) and no structure
(blank, bullet, table, fence, rule). Proves itself: the module's AST with every str constant's whitespace
collapsed, and the comment WORD stream, are identical before and after — else the file is NOT written."""
import ast, io, re, subprocess, sys, textwrap, tokenize
WIDTH = 110
def added_lines(path):
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", path], capture_output=True).returncode == 0
    if not tracked:
        return None
    diff = subprocess.run(["git", "diff", "-U0", "HEAD", "--", path], capture_output=True, text=True).stdout
    out = set()
    for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.M):
        s, c = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        out.update(range(s, s + c))
    return out
def norm_ast(src):
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            n.value = " ".join(n.value.split())
    return ast.dump(tree)
def comment_words(src):
    words = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            words += tok.string.lstrip("#:").split()
    return words
def docstring_lines(src):
    """1-based line numbers inside docstrings (module / class / function)."""
    tree = ast.parse(src); lines = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body:
            first = n.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                lines.update(range(first.lineno, first.end_lineno + 1))
    return lines
STRUCT = re.compile(r"^\s*(?:#:?\s*)?(?:[-*•|]|\d+[.)]\s|```|={3,}|-{3,}|\(\w\)\s|[A-Z][A-Za-z ]+:\s*$)")
def prefix_of(line, in_doc):
    if line.lstrip().startswith("#"):
        m = re.match(r"^(\s*#:?\s?)", line); return ("c", m.group(1))
    if in_doc:
        return ("d", re.match(r"^(\s*)", line).group(1))
    return None
def is_orphan(lines, i, kind_prefix, in_doc):
    cur = lines[i]; body = cur.strip().lstrip("#:").strip()
    if not body or len(body.split()) > 2: return False
    if i == 0 or i + 1 >= len(lines): return False
    return len(lines[i - 1].rstrip()) >= 95 and prefix_of(lines[i - 1], in_doc) == kind_prefix
MIXED = "--mixed" in sys.argv  # also refill a paragraph that holds ≥1 of MY lines (a HEAD docstring I edited)
for path in [a for a in sys.argv[1:] if a != "--mixed"]:
    src = open(path).read(); lines = src.split("\n")
    mine = added_lines(path); docs = docstring_lines(src)
    def ok(n): return mine is None or n in mine
    done = 0; skipped = []; i = 0
    stale = False
    while i < len(lines):
        if stale:
            try:
                docs = docstring_lines("\n".join(lines))  # RE-DERIVED: a refill moved every later line
            except SyntaxError as error:
                print(f"{path}: REFUSED — intermediate text does not parse ({error})"); break
            stale = False
        n = i + 1; in_doc = n in docs; kp = prefix_of(lines[i], in_doc)
        if kp is None or not is_orphan(lines, i, kp, in_doc) or STRUCT.match(lines[i]):
            i += 1; continue
        a = i
        while a - 1 >= 0 and prefix_of(lines[a - 1], (a) in docs) == kp and lines[a - 1].strip().lstrip("#:").strip() and not STRUCT.match(lines[a - 1]) and not (kp[0] == "d" and lines[a - 1].rstrip().endswith('"""') and a - 1 != i and lines[a-1].strip() != '"""'  and lines[a-1].strip().count('"""') == 1 and not lines[a-1].strip().startswith('"""')):
            a -= 1
        b = i
        while b + 1 < len(lines) and prefix_of(lines[b + 1], (b + 2) in docs) == kp and lines[b + 1].strip().lstrip("#:").strip() and not STRUCT.match(lines[b + 1]):
            b += 1
            if kp[0] == "d" and lines[b].rstrip().endswith('"""'):
                break
        if not ok(n) or not (any if MIXED else all)(ok(k + 1) for k in range(a, b + 1)):
            skipped.append(n); i = b + 1; continue
        if kp[0] == "d" and (not all((k + 1) in docs for k in range(a, b + 1))):
            skipped.append(n); i = b + 1; continue
        text = " ".join(lines[k].strip()[len(kp[1].strip()):].strip() if kp[0] == "c" else lines[k].strip() for k in range(a, b + 1))
        pre = kp[1] if kp[0] == "d" else (kp[1] if kp[1].endswith(" ") else kp[1] + " ")
        new = textwrap.wrap(text, width=WIDTH, initial_indent=pre, subsequent_indent=pre, break_long_words=False, break_on_hyphens=False)
        lines[a:b + 1] = new; done += 1; i = a + len(new); stale = True
    out = "\n".join(lines)
    try:
        ast.parse(out)
    except SyntaxError as error:
        print(f"{path}: REFUSED — result does not parse ({error})"); continue
    if out != src:
        if norm_ast(out) != norm_ast(src) or comment_words(out) != comment_words(src):
            print(f"{path}: REFUSED — the refill changed more than whitespace"); continue
        open(path, "w").write(out)
    print(f"{path}: refilled {done} paragraph(s); skipped (not all mine / mixed) at lines {skipped}")
````

### §A.10i `strict_eq.py` — the strict whitespace-only proof (D-13)
md5 `1d5d7112891829c6aa7b0087f2b88687`, 17 lines
````python
"""strict_eq.py <before> <after>: identical AST with ONLY docstrings whitespace-normalised (every other str
constant compared EXACTLY) and an identical comment word stream. Exit 1 on any difference."""
import ast, io, sys, tokenize
def dump(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                first.value.value = " ".join(first.value.value.split())
    return ast.dump(tree)
def words(src):
    return [w for tok in tokenize.generate_tokens(io.StringIO(src).readline) if tok.type == tokenize.COMMENT
            for w in tok.string.lstrip("#:").split()]
before, after = open(sys.argv[1]).read(), open(sys.argv[2]).read()
ok = dump(before) == dump(after) and words(before) == words(after)
print(("EQUAL " if ok else "DIFFERENT ") + sys.argv[2]); sys.exit(0 if ok else 1)
````

### §A.10j `probe_text_tests.py` — the D-12 probe: every membership / prefix / search test in `_txn`, both trees
md5 `4ebb3dcb811d7ad93fd12297df9b683f`, 18 lines
````python
"""probe_text_tests.py <_txn.py>: every function with a membership / prefix / regex test, and what it tests."""
import ast, sys
tree = ast.parse(open(sys.argv[1]).read())
for fn in ast.walk(tree):
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    params = {a.arg: (ast.unparse(a.annotation) if a.annotation else None) for a in fn.args.args + fn.args.kwonlyargs}
    hits = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops):
            hits.append(("in", ast.unparse(n)[:110]))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and (
            n.func.attr in {"startswith", "endswith", "find", "index", "count", "partition"}
            or (isinstance(n.func.value, ast.Name) and n.func.value.id == "re")):
            hits.append((n.func.attr, ast.unparse(n)[:110]))
    if hits:
        print(f"{fn.name}  params={params}")
        for h in hits: print("    ", h)
````

### §A.6 the governed-literal read (§1 item 2)
`awk '/governed_conflict:/' loremaster/tests/*.py` over the main tree, 2026-09-27: **31** lines; the THREE forged
engine texts (`test_surreal_store.py` ×2, a28c `_HOSTILE_TEXTS["governed"]`) carry `An error occurred: `; the other
28 are LIVE `THROW` statements (the engine wraps them itself), prose, or leak-absence asserts, each read.

### §A.7 the am-36 blast radius (D-8 / F-12)
The am-36 reference (§A.5c) applied BEFORE any re-key, run over `test_retry_seam.py`, `test_surreal_store.py`,
`test_txn_contention.py`, `test_surreal_harness.py`, `test_scout.py`, `test_comms_await.py`: **349 failed, 457
passed, 2 errors** — both errors ImportErrors at collection (`test_surreal_store.py`, `test_txn_contention.py`
imported the deleted `_RETRYABLE_CONFLICT_MARKER` at module level).
After the `_engine_shapes` re-key: 0 (§8, the final both-trees run). am-36 had estimated "15 marker pins in 4
files" — the difference is every FORGED conflict / cascade fixture, which the kind now decides. The SAT then found
one more forged conflict OUTSIDE those suites (U-26, 58's tiers file).

### §A.11 `adv_kill_probes.py`
Extracted from the COMMITTED `REPORT-adversary-63c-i-a-a28b.md` §A.5 — not reproduced (it is already tracked);
md5 `7d48312500dc1269352e0eeb9155da10` = that report's stated md5.
