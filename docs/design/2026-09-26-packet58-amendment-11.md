# Packet 58 — ruling amendment 11 (sidecar-64, 2026-09-26): am-10 §2 governs a TRANSLATE — a translation's honesty is a property of the TARGET CLASS, so it is adjudicated by ADMISSION to `FAULT_CLASSES`, never by a site row; `raises-chained` is retired as evidence; an UNCHAINED raise (`from None`) is the one shape that registers, with a reason; two errata on am-10 (§4's "the rest", the `MemoryBackendError` name)

Rules `REPORT-contract-58-r3.md` (`7130508`) D-AM10 / D-AM10-FAULTS / §FATES per lead-63c-2's Task 21.
Facts: `calibration/engine._count_live_total` raises `_ProbeUnavailableError(str(exc)) from exc` (a
module-private `RuntimeError` subclass whose docstring says *"a retryable condition"*; its only catcher is
the probe loop's bounded backoff); `server.run_probe_gate` raises `ProbeGateError(...) from exc` after
`logger.error` (refuse-to-start); `server._eager_build_or_operator_safe_error` raises
`RuntimeError(_EAGER_BUILD_FAILED_MESSAGE) from None` after `logger.error(exc_info=exc)` — the chain is
suppressed DELIBERATELY so a credentialed cause cannot ride uvicorn's unredacted traceback (security-59
F4); `watcher._OverflowAwareInotify.read_events` returns `[]` at DEBUG under `except Exception`.

## 0. Ruling in one screen

| Q | ruling |
|---|---|
| **the property (lift first)** | am-10 §1: exhaustion is never a FALSE CLEAR. For a TRANSLATE, whether the fate is a false clear is decided by **what the TARGET CLASS means to its catchers** — a FAULT ("the operation did not complete": retry / abort / refuse / log) or a VERDICT ("a fact about data": not found, illegal edge, lost race, already acked). That is a property of the CLASS, not of the SITE. A site-level evidence predicate (`raises-chained`) sees the same bytes for `raise _ProbeUnavailableError(...) from exc` and `raise IllegalTransitionError(...) from error`; it cannot adjudicate. |
| **§2 vs §4** | **§2 governs.** A chained translation to a class ∉ `FAULT_CLASSES` is RED by name; the remedy is **ADMISSION of the class** (one adjudicated row in the exact allowlist: name, module, the catcher(s) and why they treat it as a fault), never a site row. **ERRATUM (am-10 §4):** *"the rest get a row"* meant sites that are neither PASSTHROUGH nor TRANSLATE; a chained translate to an un-admitted class is a FAILED TRANSLATE, not "the rest". |
| **the condition the lead asked for** | A non-admitted chained translate may NEVER register. The ONE raise shape that registers is the **UNCHAINED** raise (`raise C(...) from None`, or a raise with no `from`): it is not a TRANSLATE by the classifier (the chain is the derivation's evidence), so it is OTHER → a row with classification `re-raise-unchained`, evidence `logs>=warning` ∧ `logs-exc_info` (the cause MUST reach the log if it may not reach the traceback), and a REQUIRED `reason` field. The only reason known today: the redaction boundary (security-59 F4). |
| **admissions now** | `_ProbeUnavailableError` (retryable outage; catcher = the probe loop's backoff) and `ProbeGateError` (refuse-to-start) are ADMITTED. `RuntimeError` bare is NOT admitted (its exact-class catchers are process boundaries, but admitting the root of half the exception tree as a translate target is the widened door the D-AM10-FAULTS derivation was rightly rejected for). |
| **pins inverted (for adversary-58-r3)** | (a) every §FATES row whose evidence is `raises-chained` is DELETED — at `7130508` that is row 7 (`calibration/engine.py::_count_live_total` L395), which becomes a derived TRANSLATE; the author regenerates, never hand-edits; (b) the `raises-chained` predicate is RETIRED; (c) `FAULT_CLASS_NAMES` gains the two admissions, exact both ways; (d) row 47 (`_eager_build_or_operator_safe_error`) is re-classified `re-raise-unchained` with `reason="security-59 F4: credentialed cause must not ride the traceback"`; (e) a positive control: a synthetic `raise IllegalTransitionError(...) from error` → RED (it was registrable under §4 — the exact door §2 exists to close). |
| **ERRATUM (am-10 §2, mine)** | `MemoryBackendError` does not exist (D-AM10-FAULTS measured it). I named a class without `lore_verify` — the anti-hallucination check that exists for exactly this. The allowlist is the author's derived-and-verified exact set (8 + the 2 admissions); the D-AM10-FAULTS rejection of "every direct `RuntimeError` subclass" is CORRECT (it admits `UnknownRowError`, a verdict) — admission stays by adjudication. |

## 1. Why admission, not a row — the askable form

*"If a catcher of this class acted on it WITHOUT CHECKING, could it be wrong in a way the class name did
not say?"* For a fault class the answer is no: the catcher retries, aborts, refuses or logs — every one
of those is correct whether the cause was a dead socket or exhausted contention. For a verdict class the
answer is yes: the catcher renders a fact ("illegal edge from `open`", "no finding #N") that is FALSE when
the cause was exhaustion. The admission row records that answer once per class; a site row would have to
re-derive it per site, and the evidence predicates cannot.

## 2. The allowlist as the registry for translation targets

- `FAULT_CLASS_NAMES`: exact, both ways (an admitted class with no translating site → RED "delete the
  admission"; a translating site to an un-admitted class → RED by name). Each entry carries `module`,
  `catchers` (derived by the classifier's own walker: every `except` whose closure ∋ the class) and a
  one-line `why_fault`. The author derives the current 8 + 2 and verifies each name (`lore_verify`).
- **Re-open trigger / next step (not r3's):** the classifier's DOMAIN can generalise from *closure ∋
  `TxnContentionExhaustedError`* to *closure ∋ any admitted fault class* — then an admitted class caught
  and served as a verdict downstream reds by the SAME instrument. Right-sized out of r3; named here so the
  admission criterion has a mechanical home when someone needs it.

## 3. The pinned HOLE rows — surfaced, not re-ruled (the lead routes; none is 58's file)

- **`index/watcher.py::read_events` — a DEFECT by the property, not a bound.** `except Exception →
  logger.debug → return []` serves a degraded read as "no events" (am-10 §1's forbidden shape). The design
  names the reconcile backstop, which is why it is not an outage; it is still a false clear at the read.
  Fix: `logger.warning("watcher.read_events.degraded", exc_info=True)` — one line; the `[]` stays (the
  thread must not die). Owner: watcher. The HOLE row reds "delete the row" when it lands.
- The seven `suppress`/`pass` sites around CLOSE/cancel on already-failing or shutting-down paths
  (`server.aclose` ×2, `build_app_context` ×3, `scout.start`/`aclose`, `_count_live_total`'s `finally`): a
  failed close is invisible. Each fix is one WARNING line in its owner's module; pinned as holes until
  then — exactly what am-10 §4 predicted this reading would find. `scout.run` ×2 (signal-handler
  registration): narrow the tuple or log — owner's call.

## 4. Discipline
- Third erratum class this session: a NAME asserted without `lore_verify` (am-3 cited a non-existent
  `governed_node_tables`; am-10 a non-existent `MemoryBackendError`). Standing self-rule from here: every
  class/symbol a ruling names is `lore_verify`'d before the doc is written.
- Loop status (for the operator): 58 at r3 under adversary grade; this ruling inverts five pins (§0) and
  no property. No code/tests/store touched; this doc only; no attribution trailer.
