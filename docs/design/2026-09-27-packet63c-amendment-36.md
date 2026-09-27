# Packet 63c — ruling amendment 36 (sidecar-63c-2, 2026-09-27): the a28c forks — FK-a28c-1 ruled IN (am-35 §2 completed over EVERY engine-text reader in `_txn`, exact set, typed-first); FK-a28c-2…8

Rules lead Task 37 over `REPORT-contract-63c-i-a-a28c.md` §F (uncommitted at repo root, 00:30) FK-a28c-1…8.
Lore client still `ECONNREFUSED` → `lore_verify` unavailable; every name below was verified by reading
`loremaster/loremaster/store/_txn.py` (`is_retryable_conflict_error` → `_is_retryable_conflict_text` reads
`str(error)`; `_rollback_verdict` / `_domain_root_cause` → `_is_domain_cascade_notice` read `str(failed.raw_result)`;
the marker constants `_RETRYABLE_CONFLICT_MARKER`, `_DOMAIN_CASCADE_MARKERS`, the `_ERROR_CLASS_*` markers) and by
`awk` over `loremaster/tests/*.py` (15 marker references in 4 files: `test_surreal_store.py` 5, `test_surreal_harness.py`
5, `test_retry_seam.py` 3, `test_txn_contention.py` 2 — the DUAL cost the author names). The engine facts are the
author's live probes (§A.1/§A.2, 3.2.4): retryable conflict = `kind: Query, details.kind: TransactionConflict` on
both paths; every cascade notice = `details.kind: NotExecuted`; a caller value echoing `can be retried` costs ~2 s of
engine retries and serves `TxnContentionExhaustedError` for a domain rejection; an echoed cascade phrase loses the
governed class on the transactional path.

## §1 FK-a28c-1 — lifted: it IS MP-3's class, on the two text readers am-35 §2 did not enumerate

**The lift.** MP-3's property (am-35 §2): *the served class is a function of the engine's rejection KIND, never of a
caller value the text echoes.* I stated it over "the ONE classifier" and enumerated `_classify_engine_error`'s
markers. But the served class is decided by THREE text readers in `_txn`, two of them UPSTREAM of the classifier:
the RETRY DECISION (`_is_retryable_conflict_text`, consulted by `is_retryable_conflict_error` on `run_query` and by
`_rollback_verdict` on the transactional path — it decides contention-vs-domain before any classifier runs) and the
ROOT-CAUSE SELECTOR (`_is_domain_cascade_notice`, which decides WHICH failed statement is classified). Same class,
different reader. **Erratum (mine, am-35 §2 item 3):** "∀ text markers in the classifier" quantified over one
function; the property is over every place `_txn` turns engine text into a decision — the quantifier law, on the
ruling that had just invoked it.

**Ruling: Reading B — INTO a28c, as the COMPLETION of am-35 §2, not a new item.** Three reasons, then the
STOP-rule accounting the lead asked for.
1. **The engine types both signals (measured).** `TransactionConflict` and `NotExecuted` are `details.kind` values
   on both paths; am-35 §2 item 1 already makes `_failed_statements` keep the per-statement dict and parse it with
   `parse_query_error`, so the typed kind is IN HAND at every one of the three readers after that change. Reading A
   would keep two text tests beside typed data the same function already holds — the FK-ADV-1/FK-ADV-3 class
   ("the driver erases a typed engine classification the SDK provides"), a third time, knowingly.
2. **The surface is honest-agent-reachable, not adversarial-only.** Agents FILE ENGINE ERRORS INTO FREE TEXT — a
   finding body or memory note quoting *"…this transaction can be retried"* is routine fleet behaviour. If such a
   row fails a store ASSERT, the driver retries a domain rejection for ~2 s and serves contention-exhausted; a
   compensation gate keyed on `TxnGovernedConflictError` silently misses a governed conflict whose THROW sits behind
   an echoed cascade phrase. That is a misclassification on the shared seam every one of the eleven `_query` seams
   rides (#102/#120), with the fix in hand.
3. **The domain is FINITE and now exact.** `_txn` reads engine text for a decision in exactly three functions.
   Typing them leaves text only where the engine types nothing (`kind: Internal`: the U prefix, ASSERT, coercion,
   recursion-depth) — and of those only U moves the CLASS; ASSERT/coercion/recursion move a teaching LABEL on the
   base class, a low-stakes bound stated in §1.2.

**The STOP-rule, explicitly.** *Is the reach receding one level per round?* The finding relocates the class from the
classifier to its two upstream readers — the receding SHAPE — but into a domain that is finite, enumerated by
derivation and closed by an exact-set pin (§1.2 pin 3), on a surface honest agents reach. The STOP-rule accepts a
bound when a surface is ADVERSARIAL-ONLY and each fix merely relocates a hidden constant; neither holds here. I
count this as the FOURTH arrival of the class and am-35 §0's letter says "fourth strike → bound". I override the
letter for the substance, flagged in §E: a28c is still the last ROUND (this widens the round the author is folding
by one item, before grading); after a28c, ANY further echoed-value instance is a bound by rule — and §1.2 pin 3 makes
one unrepresentable inside `_txn`. **Loop cost:** 13 revisions + a28c; no a28d.

### §1.1 Mechanics (all in `_txn`)
- **ONE parse per failed statement.** `_failed_statements` keeps the dict (am-35 §2 item 1) and parses it ONCE with
  `surrealdb.errors.parse_query_error`; `_FailedStatement` carries the typed `ServerError` (kind + details) beside
  the raw text (text = EVIDENCE for the server-side log only, never a decision input).
- **Retry decision, typed:** `_is_retryable_conflict(...)` / `is_retryable_conflict_error(...)` decide
  `details.kind == "TransactionConflict"` (a named constant `_RETRYABLE_CONFLICT_KIND`), on both paths — the
  `run_query` exception is the SDK's typed `QueryError` with the same details. `_RETRYABLE_CONFLICT_MARKER` is
  DELETED (retired-name sweep, bare pattern).
- **Root-cause selector, typed:** `_is_domain_cascade_notice` decides `details.kind == "NotExecuted"`
  (`_CASCADE_KIND`); `_DOMAIN_CASCADE_MARKERS` DELETED. The degenerate "every entry is cascade" fallback stays.
- **Classifier, typed-first (am-35 §2 unchanged, sharpened):** R by `AlreadyExistsError.record_id`; the governed
  THROW by its typed kind (the builder measures the THROW's `details.kind` — `Thrown` is the SDK's name — AND our
  OWN authored `governed_conflict:` prefix at the start of the thrown message; our prefix is our protocol, not
  engine-text classification); text ONLY for `kind: Internal`, the U prefix first, then ASSERT / coercion /
  recursion as LABEL choices on the base class.
- **The store is forward-only at 3.2.4 (MEMORY.md)** — no legacy-engine text fallback is kept; a kind the SDK does
  not know (`_resolve_kind` → `ServerError`) classifies as `unspecified rejection`, loud.

### §1.2 Pins (GATING, a28c)
1. **KB widened over the WHOLE reader set (the class pin):** ∀ decision inputs {retry, cascade, unique, governed,
   assert, coercion} × ∀ live host shapes × both paths — the phrase injected as the echoed caller value moves
   NOTHING: the served class, the retry count (exactly ONE attempt for a domain rejection — a `retry_on_conflict`
   spy), the selected root cause, the elapsed time bound (no 2 s). The author's §A.1 table is the fixture list.
2. **DUAL re-key of the 15 marker pins:** every pin that mutates `_RETRYABLE_CONFLICT_MARKER` / the cascade
   markers to prove detection MOVES now mutates the typed-kind constants (`_RETRYABLE_CONFLICT_KIND`,
   `_CASCADE_KIND`) — same pin shape, one name each; a pin that faked the marker in TEXT to construct a conflict
   is re-keyed to construct the typed dict/exception (say so per pin in the DUAL table). The property those pins
   guard — the ONE detection authority, proven by mutation, on both paths — is PRESERVED; only the thing mutated
   changes.
3. **The exact set of engine-text readers (completeness — what makes a fifth arrival unrepresentable):** derive
   every function in `_txn` that calls `str(...)` on an SDK error / a `raw_result` / a `ServerError.message` and
   tests the result with `in` / `startswith` / a regex; the allowlist is exactly `{_classify_engine_error}` (the U
   prefix and the three `Internal` labels), and inside it the text branch is reachable ONLY when `kind ==
   "Internal"` (a positive control: a synthetic typed kind with hostile text never reaches the text branch). A new
   text reader reds by name.
4. **Pin-the-miss (the stated bound):** among `kind: Internal` texts, an echoed value can move the teaching LABEL
   between ASSERT / coercion / recursion (never the class, never the retry) — pinned as the KNOWN BOUND with the
   trigger *"the engine types any of these three kinds"*; the U prefix test is anchored at position 0 (am-35).

## §2 FK-a28c-2…8 — rulings
| fork | ruling |
|---|---|
| **2** (validator vs the Literal swap) | **A, confirmed.** The swap target is the NEXT LEGAL member by construction; `"empty"` has no swap case and "adds no sentence" is pinned directly with the stems proven non-vacuous. **Erratum (mine, am-34 §2):** I ruled a validator and, in the same section, a perturbation the validator forbids — the right hand did not read the left. |
| **3** (one read, which shape) | **Both legs, confirmed** — (A) minimal shape: exactly one driver call and it is `INFO FOR DB`; (B) realistic shape: `INFO FOR DB` once, no statement names the target, no leg call. "Exactly one" in am-34 §4 was stated over the shape I derived it on (quantifier law, small). |
| **4** (`table_defined` on an unread store) | **`bool \| None`** — `None` on the invalid-table refusal (zero I/O: nothing was measured); `False`/`True` where `INFO FOR DB` ran. am-34's `bool` corrected; the render derives "not read" from `None` exactly as the counts model does. Pin the `None` cell too. |
| **5** (the F-4 quantifier's wording) | **"Every clause exhaustion REACHES", confirmed** — per `try`, the first clause whose caught classes admit `TxnContentionExhaustedError` (Tuple element, subclass, superclass, bare `except:`), anywhere in a listed door's function, must be a bare `raise`; the door handler itself is not "reached" by exhaustion when a guard clause precedes it. That is what am-35 §3 meant; the author's measured GREEN-at-HEAD / RED-on-S8 is the receipt. DUAL row D-6 stands. |
| **6** (per-handler key vs 58-r3's frame-keyed rows) | **A, confirmed** — ONE accessor (`_handler_function`) owned by the scanner; 58's `listed_handlers()` maps through it (a one-line, disclosed deviation D-5); drivers keyed by function, exact sets keyed by handler. The key FORMAT lives in one place (ONE IMPLEMENTATION); the lead tells sidecar-64/58's owner. |
| **7** (the one-scanner pin's property) | **The two derived legs, confirmed** — (i) catch-clause scanners (walks `ast` AND inspects handlers AND names a store-error class) → allowlist the CAS-domain function; (ii) resolvers (evaluates an `except` expression in a module namespace) → allowlist `_catch_sites.resolved_by_import`; each with a positive control. am-34 §5's single property over-matched two envelope-literal scanners — a hand-property, corrected by derivation. |
| **8** (leg-level "(N principals, M admins)") | **Fields, ∀ populations — the parenthetical in am-34 §3 was the quantifier law again.** Operator resolution happens through ONE resolver (`_operator_unresolved`'s caller) wherever the verb performs it — precondition OR leg — and feeds the SAME two fields on the ONE result model; `None` iff NO resolution ran on that call. Pin (2) holds over the leg-level refusals too; no carve-out anywhere. If the legs and the precondition resolve separately today, the fold makes them ONE call whose answer is carried on the preconditions object (routing is not sharing). |

## §W
| # | item | gate |
|---|---|---|
| 1 | typed retry decision + typed cascade selector; ONE parse per failed statement; the two text markers deleted; KB over the whole reader set; the 15 pins re-keyed by DUAL; the exact-set text-reader pin; the `Internal`-label bound | GATING (a28c) |
| 2 | FK-2 next-legal-member swap; FK-3 both legs; FK-4 `bool \| None`; FK-5 "reaches"; FK-6 one accessor; FK-7 two legs; FK-8 fields ∀ populations | GATING (a28c, as the author's picks ± the corrections above) |

## §E — operator-visible
- **I overrode the letter of my own am-35 §0 ("fourth strike → bound").** Reason: the STOP-rule's substance is
  receding reach on an ADVERSARIAL-ONLY surface; this surface is reached by honest agents quoting engine text, the
  typed fix is measured and in hand, and the reader domain is finite and pinned exact. It does NOT add a contract
  round; it widens a28c by one item before grading. If you prefer the letter, the bound is the author's Reading A
  (pin-the-miss on both readers, trigger "the retry decision / root-cause selector is typed") and the 2 s
  misclassification ships on the shared seam.
- **Blast radius:** the shared retry seam every store caller rides; 15 test pins re-keyed by DUAL, no behaviour
  change on any genuine conflict (the typed kind and the text agree on 3.2.4 — measured by the author).
- Errata this amendment (mine): am-35 §2 item 3 (reader set), am-34 §2 (validator vs swap), am-34 §3 (leg-level
  resolution), am-34 §4 (`bool`, "exactly one"), am-34 §5 (the hand-property). Four of five are the quantifier law.
