# Packet 58 — ruling amendment 10 (sidecar-64, 2026-09-26): FK-r3-7 — the swallow rule's premise was over-quantified (erratum on am-9 §3); the PROPERTY is "exhaustion is never a FALSE CLEAR", enforced by a FATE classifier: PASSTHROUGH and TRANSLATE-to-a-fault derived, NAMED-ISOLATION registered; the domain is Reading (i); none of the 7 swallows is a defect; the registry lives in a cross-packet home

Rules `REPORT-contract-58-r3.md` §FORKS FK-r3-7 per lead-63c-2's Task 20. Amends am-9 §3 (its premise
*"a correct build is never RED under it"* was stated, not measured — the r3 author measured 26 store-class
sites at HEAD under Reading (ii) and 57 under Reading (i), all outside 58). Facts read: the 7 "swallow"
bodies (`server._resolve_or_acknowledge_many`, `indexer._index_chunks` / `_commit_batch_file` /
`_resolve_all_extension_edges`, `briefs._release_version`, `floor_calibration/store._fence_verdict`,
`principals._dispatch_report_unmigrated`), the 2 task translations (`transitive_blockers`,
`_reject_unusable_blockers`), one `_ensure_connection` (tasks — the F4 wrap, docstring: *"the wrap lives
here, at the seam, not in the shared helper"*), and the classes (`TxnContentionExhaustedError`: a
write-write conflict that outlived the retry budget; `SurrealConnectionError`: could not reach/auth).

## 0. Rulings in one screen

| Q | ruling |
|---|---|
| **the property (lift first)** | am-9 §3 stated *"closure ∋ exhaustion without passthrough → RED"* — a rule derived on guarded-CAS handlers (#102: exhaustion re-read and served as a lost race) and quantified over every catch site. **The property #102 actually names: *exhausted contention is never served as a FALSE CLEAR — never a success, a domain verdict, an empty answer or a silent skip.*** Passthrough is one honest fate, not the only one. **ERRATUM (am-9 §3, quantifier law):** the premise was true of the rule's origin set and false of the tree. |
| **(1) Reading** | **(i) — closure ∋ exhaustion, whatever the spelling.** `except Exception` swallows exhaustion exactly as `except SurrealStoreError` does; exempting the wider net keys the instrument on the class NAME the site wrote (the instrument lesson). The 31 extra sites cost one classified row each; the classifier makes most rows automatic (§2). |
| **(2) translation** | **A legitimate typed re-raise, under two conditions:** the target is a FAULT class (an exact allowlist — never a domain-verdict class such as `IllegalTransitionError`/`*NotFoundError`/`UnknownBlockerError`, which is #102's lie by construction) and it is chained `from` the exhaustion with a message naming the fate + recovery. All 19 pass both today. A consumer acting on `SurrealConnectionError("… bootstrap exhausted its retry budget")` without checking retries or aborts — it cannot be wrong in a way the response did not name. |
| **(3) the 7 swallows** | **None is a defect.** Each names its fate: served (`FAILED — store contention, safe to retry`, excluded from `N of M`), recorded (`_mark_file_failed` + WARNING `exc_info`), returned (`scopes_failed`), logged best-effort compensation (`_release_version`), declined classification with the ORIGINAL error propagating (`_fence_verdict`), CLI stderr + exit 1. Owners per row (§3). One SIBLING flagged, not a defect: the indexer's `failed` reason does not distinguish retryable exhaustion from a permanent cap overflow — a bound with a trigger. |
| **(4) home** | **Cross-packet.** The registry is a repo-level invariant (`loremaster/tests/test_exhaustion_fates.py` + its `_exhaustion_fates.py` rows, under `testpaths`), LANDED by 58's build (58 built the instrument), OWNED per row by the site's component. Not 58's to carry; 58's to deliver. |

## 1. The property, stated so it can be asked

*"If exhausted contention reaches THIS catch site, what does the caller (or the record) see — and could it
mistake that for a healthy outcome?"* Three honest fates, one forbidden:
- **PASSTHROUGH** — re-raised unchanged (the guarded-CAS doors' `except TxnContentionExhaustedError: raise`).
- **TRANSLATE** — `raise <FaultClass>(...) from error`. Honest iff `<FaultClass>` ∈ `FAULT_CLASSES` (§2) and
  the site is not a CAS handler (a CAS handler that translates exhaustion into anything is the #102 door —
  those sites are governed by the partition, not by this rule).
- **NAMED-ISOLATION** — the unit of work (an item, a file, a scope, a compensation, a CLI run) is recorded or
  served as FAILED/retryable, excluded from every success count, and the failure is logged at ≥ WARNING or
  rendered in the served outcome.
- **FORBIDDEN: SILENT** — a success-shaped return, a domain verdict (`NotFound`, `IllegalTransition`, a lost
  `ClaimResult`), an empty answer, an unlogged `continue`/`pass`, a `suppress` with no record.

## 2. The instrument — a FATE classifier, allowlist-the-safe, both ways

- **Domain (Reading (i)):** every catch site in the production tree — `Try`/`TryStar` handlers and
  `With(contextlib.suppress)` items (am-9's ONE walker, ONE resolver) — whose caught closure ∋
  `TxnContentionExhaustedError`, with no clause above it catching that class. Bare `except:` counts.
- **Derived automatically (no row needed):**
  - PASSTHROUGH: the handler's every exit is `raise` / `raise <the caught name>`;
  - TRANSLATE: every exit is `raise <C>(...) from <the caught name>` with `C` resolved BY IMPORT to a member
    of `FAULT_CLASSES` — an EXACT allowlist: `SurrealConnectionError`, `SurrealStoreError`, and each ledger's
    fault base (`TaskLedgerError`, `FindingLedgerError`, `BriefLedgerError`, `PrincipalStoreError`,
    `AgentRegistryError`, `KeepStoreError`, `MemoryBackendError` — the author derives the exact list from
    the modules' base fault classes and pins it exact). A translation to any other class → RED by name (the
    door: exhaustion → a domain verdict). `from` REQUIRED (a translation that drops the chain hides the cause
    from the log — RED).
- **Registered (a row REQUIRED, deny-by-default, exact both ways):** every other site. Row =
  `(file::function, classification, owner, evidence)` with classification ∈ {`named-isolation-served`,
  `named-isolation-recorded`, `best-effort-compensation`, `cli-exit`, `lifecycle-catch-all`} and `evidence`
  = the AST predicate that PROVES the fate where one exists (a logger call ≥ WARNING with `exc_info`, a
  `print(..., file=sys.stderr)`, an append to a named outcome list, a `return` of a `*_failed` marker) —
  the F5 `effect` idiom. A registered site whose evidence no longer holds → RED "the fate changed";
  an unregistered OTHER site → RED by name; a registered site that became PASSTHROUGH/TRANSLATE → RED
  "delete the row". Positive controls: synthetic `except SurrealStoreError: pass`, `suppress(SurrealStoreError)`,
  `raise IllegalTransitionError(...) from error`, a translation without `from`.
- **Why the premise now holds:** a correct build never reds unless it adds an OTHER site without its row — and
  the row IS the adjudication (CLAUDE.md "a bound that is pinned is a bound the next engineer meets
  DELIBERATELY"). That friction is the mechanism, not a shape constraint: PASSTHROUGH and TRANSLATE are free.
- **The runtime ∀ at the driver seam (am-8 §3) is unchanged and remains the PROOF for CAS verbs;** this
  classifier is the reviewer-visible half that reaches code no test drives.

## 3. The seven, adjudicated (each row a verdict; no "the rest are X")

| site | fate | evidence | defect? | owner |
|---|---|---|---|---|
| `server.py::_resolve_or_acknowledge_many` | named-isolation-served | the per-item line `FAILED — store contention, safe to retry this item`; `success_count` excludes it; header `N of M` | **NO** — the served render names exactly the retryable fate; the batch verb's contract is best-effort | comms/findings dispatcher (64b touches it; the row moves with the merge into per-item `authorize_guarded`) |
| `index/indexer.py::_index_chunks` | named-isolation-recorded | `logger.warning("index.file.store_failed", exc_info=True)` + `_mark_file_failed(reason=_FAILED_STORE_REASON)`; last-good retained | **NO** — the file is recorded `failed`; the sweep continues. **SIBLING (bound):** `_FAILED_STORE_REASON` is ONE reason for exhaustion AND for a permanent cap overflow; if the sweep's retry policy ever branches on the reason, a transient exhaustion is a permanently-`failed` file. Pin the bound; trigger: *"the day the reconcile retry policy reads `reason`"* | indexer (11c's neighbourhood) |
| `index/indexer.py::_commit_batch_file` | named-isolation-recorded | same as above (the batch twin) | **NO** — same sibling | indexer |
| `index/indexer.py::_resolve_all_extension_edges` | named-isolation-recorded | WARNING `exc_info` + `scopes_failed` → `IndexSummary.scopes_failed` | **NO** | indexer |
| `briefs.py::_release_version` | best-effort-compensation | WARNING `brief.publish.version_not_released`; runs only on a path whose caller is ABOUT TO RAISE the real rejection; worst case a skipped version number | **NO** — masking the original rejection would be the defect; this preserves it | briefs |
| `floor_calibration/store.py::_fence_verdict` | named-isolation-recorded (declined classification) | WARNING `fence.unconfirmable`; RETURNS the ORIGINAL error for the caller to raise; never `FenceLostError` on unobtained evidence | **NO** — E2's rider working exactly as ruled | floor_calibration |
| `principals.py::_dispatch_report_unmigrated` | cli-exit | `print(f"{_CLI_PROG}: {error}", file=sys.stderr)`; `return 1` | **NO** — Unix silent-on-success/loud-on-failure | principals (63c) |

The 19 TRANSLATE sites pass §2 automatically (`SurrealConnectionError` ×17 with *"exhausted its retry
budget"* in the text; `TaskLedgerError` ×2 naming *"REJECTED by the store … retry"*). **Flagged, not ruled
(outside 58; filed):** the 17 `_ensure_connection` wraps are 17 hand-rolled copies of ONE policy (close the
half-open socket, translate to `SurrealConnectionError`) — the #102/#120 clone class; the deliberate part
(scout needs the RAW exhaustion) is one caller's choice, not a reason for sixteen copies elsewhere.

## 4. Reading (i)'s extra 31 sites — how the author lands them without a third round

Each is classified by the SAME classifier: those ending in `raise`/`raise ... from` a fault class pass;
the rest get a row. The lifecycle points (shutdown, watchers, the scout loop) are `lifecycle-catch-all`
rows whose evidence is a logger call ≥ WARNING with `exc_info` (the shape every honest catch-all already
has); a lifecycle site with NO log line is the one real hole this reading can find — reported by name, and
its fix is one line in its owner's module (not 58's). Per-row verdicts in the contract report; the banned
output is the wholesale sentence.

## 5. Discipline
- Erratum class, named: a premise asserted without measurement (am-3's "no library", am-7 §4's RS-5 row,
  am-9 §3's premise — three today). The askable form I failed to ask: *"does this claim hold on every site
  this rule TOUCHES, or only the ones I DERIVED it on?"* (CLAUDE.md, THE RIDER's DD-3.c form).
- Loop status (for the operator): 58 at r3; FK-r3-7 is a NEW property (the fate rule), ruled once with its
  instrument; not a repeat. No code/tests/store touched; this doc only; no attribution trailer.
