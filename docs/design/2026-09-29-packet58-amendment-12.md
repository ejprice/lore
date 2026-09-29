# Packet 58 — Amendment 12: FK-r3-5 re-ruled at the STATE; F-A's domain; the r3 findings bucketed under the cap; r4's fold and base

**Author:** sidecar-64 (Fable 5.1 design sidecar) · **Date:** 2026-09-29 · **Task 25** · operator 2026-09-29:
RESUME 58; build order 63c-i-a → 58 → 64b-i.
**Amends:** am-9 §5 FK-r3-5 (the MINIMAL-verb domain — superseded), am-8 §3 item 2 (E3 dropped — erratum,
reinstated in a stronger form), am-10 §2 (the classifier's domain must fail CLOSED), am-8 §7 (the re-open clause —
discharged). **Does not reopen the contract:** 58 is past the cap (r1–r3 graded). r4 is a FOLD, ungraded (§3).
**Sources read:** `REPORT-adversary-58-r3.md@706a1bf` (§SUMMARY, §A F-A…F-H + §AM11, §P1b/§P1c, §DUAL, §RESIDUALS,
§VERDICT); `store/lease.py` (`_LOCK_CALL_ERRORS` :130; the four catch sites :645/:675/:710/:765; `_ensure_connection`
:315–:326); `test_reanchor_58_r3_cas_seam.py` (`CAS_SEAM_DRIVERS` :459, `discovered_drivers` :470, the population
pin, the identity leg's parametrisation); `test_findings_cas_seam_64b.py` (142 lines: ONE driver
`findings.py::_run_guarded`, one well-formedness test); `scripts/pending_contracts.yaml` rows `packet-58-contract`
(:71) and `packet-64b-i-contract` (:157); `pending_contract_gate.py` (`registered_paths` :716 — a union; the only
duplicate refusal is on gate IDS, :929); `REPORT-contract-63c-i-a-a28c.md` (decision (4), F-2/F-3/F-13/F-13a/F-15);
`REPORT-adversary-63c-i-a-a28c.md` §SAT (the shared-23); `REPORT-lead-63c.md` POST-ANCHOR v7. `lore_verify`:
`FindingLedger._run_guarded` = not_found at HEAD (the fact §4.3 rests on). grep is hook-blocked → awk/sed, said so.

## 0. Rulings in one screen

1. **FK-r3-5 re-ruled (F-B, the 4th instance).** The MINIMAL verb was a PATH; four rounds relocated the hidden
   constant (`_select*` → `try` node → `self._apply(` → the wrapper catch). The property moves to the STATE:
   **the store seam and the observed outcome.** ∀ entry ROOT × ∀ write index k: after the seam raises exhaustion,
   the seam receives NO further statement from that call and the caller observes the SAME instance (or a
   registered row's effect). Reach is a runtime-checked variable (the FIRED ledger == the derived domain, both
   ways). Erratum am-8 §3 item 2: E3 ("no read after") is reinstated, merged with E2 into `statements_after == 0`.
   §1.
2. **F-A ruled.** The fate classifier's resolver evaluates each handler expression IN ITS MODULE, flattens
   tuples/starred elements, and **fails CLOSED** (an unresolvable handler is RED by name). The 12 exposed sites:
   lease ×4 = `named-isolation-served` rows with evidence by EFFECT (not a #102 door; fail-safe for leadership);
   inbox_awaiter ×4 + scout ×4 = HOLES → the operator's `UNLOGGED_SITES` with owner + trigger, and ONE finding
   for the owners' one-line fixes. §2.
3. **Every r3 finding bucketed (§3): NEW PROPERTY = 0.** F-B is the re-ruled enforcement point of an
   already-pinned property; the rest are instrument REACH defects (pinned-property new cases) or generator
   hygiene. **r4 needs NO delta grade** — the lead's default stands. The build's cold audit re-runs the
   adversary's seven wrong builds + kill probes (pasted verbatim in §INSTRUMENTS) as its mutation set: that is the
   adversary's re-grade without a contract round.
4. **r4 fold list (§4):** am-11 ×5 (as the adversary verified them, (a)–(e)); a28c's three 58 items
   (`install(observe_shell=)`, the `_comms_register` row STAYS deleted, D-5's `listed_handlers` hunk is the base);
   the `findings.py::_run_guarded` cas_seam red is **64b-i's, not 58's** — it moves to `packet-64b-i-contract`'s
   file list (one path may sit in two rows; the gate refuses duplicate IDS only).
5. **r4's author starts NOW on HEAD (`ad6e8ce`+)** — a contract author edits no production file, so 63c-i-a's
   build (production + the D-9 harness patch, in a scratch copy) cannot collide with it. ONE named re-base step
   when 63c-i-a commits: re-run the targeted SAT set and `git apply --check` on §HELD parts 1/3 (part 2 is
   superseded by a28c's scanner at HEAD). §5.

## 1. FK-r3-5 re-ruled — the property at the STATE (supersedes am-9 §5; erratum am-8 §3 item 2)

**Why the ruling, not the contract, was wrong.** am-9 §5 kept the runtime ∀ on MINIMAL verbs and handed every
wrapper to "the whole-tree swallow rule" — a STATIC rule that derives PASSTHROUGH from exit SHAPES. F-B shows the
two halves have a seam between them exactly where #102 lives: a wrapper whose handler awaits a re-read and raises
a verdict from the helper (W-IMPLICIT), or rebinds the name (W-REBIND), is PASSTHROUGH to the AST and never
driven at runtime. Each round's fix relocated the hidden constant one level (the STOP-rule's tell, CLAUDE.md
"instrument lesson"). The askable form: *"if exhausted contention is raised at THIS write, what does the seam see
next, and what does the caller get?"* Both are observable at the state without naming any path.

**THE PROPERTY (one, for the whole exhaustion family):**

> ∀ root R ∈ ROOTS, ∀ verb v ∈ R's verbs, ∀ write index k ∈ WRITES(R, v): when the seam raises
> `TxnContentionExhaustedError` at write k of the call,
> (1) **`statements_after == 0`** — the seam receives NO further statement from that call: no re-read, no retry,
> no compensation (E2 ∪ E3, observed at the STORE seam over every statement, not at one method);
> (2) the caller observes **the SAME instance** (PASSTHROUGH) — or, for a site with a REGISTERED fate row, exactly
> that row's effect: an admitted fault class raised `from` it (am-10/am-11 TRANSLATE) or a named-isolation
> effect (a ≥ WARNING record carrying the error AND the served/library failure value), in which case (1) is
> relaxed to exactly the row's declared compensation statements;
> never a verdict, never a success shape, never an unchained exception.

- **ROOTS — derived, not listed:** the roots of the reverse call graph above every CAS verb (`derive_cas_verbs`
  already computes the verbs; the reverse walk to callers with no callers is the same walker, one more seed). At
  HEAD that yields three kinds, each with a derived verb axis: (a) **served doors** — `AppContext.tasks` /
  `findings` / `comms` / `claim_task` × their spec-dict verbs (the same domain source 64 am-11 §1 rules for the
  foreign-param sweep — one derivation, two consumers); (b) **boot** — `_reanchor_stragglers` via the startup
  heal; (c) **the lease lock's four library calls** (`get`/`create`/`update`/`release_if_held`, §2). A CAS verb
  with no root is dead code → RED by name. The population pin becomes: `{(R, v)} == fired` both ways.
- **WRITES(R, v) — measured, not assumed (F-D):** run the call once UNARMED and count the seam's writes; then
  arm each k ∈ 1..n. The heal's n ≥ 2 by fixture (a population spanning ≥ 2 chunks — F-E's `2·fit+1` scale
  gives it); every single-transaction verb has n = 1 and the pin says so (a verb whose n grows silently gains a
  leg, never loses coverage).
- **FIRED ledger (F-NOOP):** a session-scoped set of `(R, v, k)` whose injection FIRED, recorded by the seam
  itself, asserted `== {(R, v, k)}` at session end. A driver that declares and never fires is RED by name. The
  per-verb `CAS_SEAM_DRIVERS` dicts stay as WORLD SETUP (the owner still seeds the row/race), but the unit of
  coverage is the fired triple, not the dict entry.
- **Outcome discrimination, so the four r3 survivors die by construction:** W-TUPLE (success shape) fails (2);
  W-IMPLICIT (re-read then verdict) fails (1) before it can lie; W-REBIND fails (2) — identity, not chain
  (`__context__` is set on ANY raise inside a handler, so "chained to the exhaustion" is NOT the test; identity
  or an ADMITTED fault class `from` it is); W-RETRY-RERAISE fails (1) — the retried write is a statement after.
  F-C's "row byte-identical after the call" is the redundant half of (1) and is asserted too (cheap, and it
  catches a compensation the seam did not see — e.g. a second connection).
- **The static half stays** (am-10's classifier, whole tree, fail-closed per §2) as the reviewer-visible backstop
  for roots no test drives (scout / inbox_awaiter lifecycle). It is no longer load-bearing for CAS verbs: the
  runtime ∀ reaches every wrapper from the root down.
- **Rider (same sentence):** the identity leg asserts reach as a checked variable — the number of `(R, v, k)`
  legs executed equals the derived count, and a leg whose injection did not fire is a failure named
  `(R, v, k)`, never a skip.

**Erratum am-8 §3 item 2.** "A read that still re-raises the same instance tells no lie" was true of the read
and false of the DOOR: the read is where the lie is decided, and forbidding the door at the state costs one
counter, while fixturing every lie costs a round per lie (F-B is that round). E3 returns, merged with E2.

## 2. F-A — the classifier fails CLOSED; the 12 sites adjudicated

- **Instrument (am-10 §2 erratum):** `_catch_sites.caught_classes` evaluates the handler expression in its
  module namespace (a Name, an Attribute, a Tuple — nested — a Starred element), flattens to classes, and any
  element that does not resolve to a class is **RED by name** (`file::function::<expr>`), never dropped. The
  same resolver serves a28c's `test_retry_seam` scanner (folded §HELD part 2, at HEAD) — so r4's fix may surface
  tuple-catching sites in 63c-i-a's exact-set pins. Rider: r4 reports the MEMBER diff of those pins before/after
  the resolver fix (am-37 F-15's rider 1 already says the audit reads members, not colour); every new member is
  adjudicated by 63c-i-a's owner. Positive control: a synthetic `except _T:` with `_T` an unbound name → RED.
- **The 51 `_CONNECTION_ERRORS` / `_SDK_AWAIT_BOUNDARY_ERRORS*` sites** become DERIVED once visible: each is
  `raise SurrealConnectionError(...) from error` (an admitted fault) — TRANSLATE, no row (#512's clone class,
  unchanged by this ruling). r4 asserts the derived count ≥ the adversary's 51 as a non-vacuity floor.
- **The lease's four (R-3) — RULED: `named-isolation-served`, one row each, evidence by EFFECT.** Facts: the
  election library's interface is a bool per tick (`create`/`update`/`release_if_held`) or `(bool, record)`
  (`get`); each site logs `lease.lock.<op>_failed` at WARNING with the error, then serves the library's own
  failure value; the library's `retry_period` loop tries again next tick. **It is not a #102 door:** nothing
  re-reads inside the handler and nothing retries the seam — the tick is the election PROTOCOL, and `False` is
  the fail-SAFE verdict (a candidate that cannot prove its write never claims leadership; a leader that cannot
  renew loses the lease by time, which is the protocol's own visible effect via its stop callback). A raise would
  end maintenance for the process's lifetime (the docstring's stated reason). What the trust doctrine requires is
  that the record be distinguishable from a genuine lost race **in the log**: rider — the WARNING's `extra`
  gains `error_class: type(error).__name__` (one line ×4 in `store/lease.py`; production outside 58's ledgers —
  the lead decides whether 58's build carries it or the lease owner does; the row's evidence names it either
  way). Rows' evidence at runtime under §1: injection at the lock's store → the WARNING record naming the class,
  the failure value, `statements_after == 0`, and — the docstring's own claim, now pinned — a failed `get` never
  proceeds to `create` in that tick.
- **The eight HOLES (R-4):** `inbox_awaiter.py::{await_inbox, _establish_live, _consume_live, _safe_kill}`,
  `scout.py::{run ×2, _consume_live, _safe_kill}` — swallowed unlogged or at DEBUG. Under am-10 §1 a lifecycle
  catch is honest only at ≥ WARNING (the am-11 §3 watcher precedent: one-line fix, owner's). Interim so r4 is
  green on a correct build: they enter the operator's `UNLOGGED_SITES` (R-12's pinned list) with owner and the
  re-open trigger "the owner's one-line WARNING lands → delete the entry"; the classifier reds an `UNLOGGED_SITES`
  entry whose site is no longer a hole. ONE finding filed for the eight (§6).
- **The census:** REGISTERED_FATES / UNLOGGED_SITES are exact both ways over the fail-closed domain; the
  "74 sites" prose is replaced by the derived count (a number in prose is the #102 count defect).

## 3. Every r3 finding, bucketed under the cap (58: r1–r3 graded; rule 5 applies)

| finding | bucket | chokepoint / disposition | r4 |
|---|---|---|---|
| **F-B** (wrapper catches; 4th instance) | RULING re-ruled (§1) — same property, enforcement moved to the state; NOT a new property | the seam ledger (`statements_after`) + root-driven identity + FIRED reach | fold: the SEAM instrument is rewritten per §1 |
| **F-A** (tuple-constant handlers invisible) | PINNED-PROPERTY NEW CASE (Q12's domain; instrument reach) | `_catch_sites.caught_classes` fails closed (§2) | fold + the 12 sites per §2 |
| **F-NOOP** (declared ≠ driven) | PINNED NEW CASE (am-8 §3 item 3 reach) | the FIRED ledger == derived `(R, v, k)` (§1) | fold |
| **F-D** (first-write-only injection) | PINNED NEW CASE (hidden constant k = 1) | k over measured WRITES(R, v) (§1) | fold |
| **F-C** (E2 dual loss) | PINNED NEW CASE | `statements_after == 0` + row byte-identical (§1) | fold |
| **F-E** (CONV never reaches a second FULL chunk) | TEST HYGIENE (generator scale) | `SCALES` gains `2·fit+1`, `expected_chunks = ceil(rows/fit)` — generated ∀ shapes; BC-r3-1 (`constrained_batches`) stands | fold |
| **F-G** (bad-entry position monoculture) | TEST HYGIENE (generator ingredient) | `ROW_COMPOSITIONS × {bad first, bad last, bad middle}` | fold |
| **F-F** (substring evidence) | PINNED NEW CASE (evidence proxy) | where the site is under a root (§1): evidence by runtime EFFECT; elsewhere: predicates resolved BY IMPORT to the marker object, with a silent synthetic per predicate as the negative control | fold |
| **F-H** (logger-name filter) + R-6 | TEST HYGIENE (filter reach) | caplog at the ROOT, every record; the keeps UNIQUE leg takes the same filter | fold |
| §AM11 (a)–(e) | fold items (spec moved after the graded commit) | as verified by the adversary | fold |
| R-2 (corpse docstring) | TEST HYGIENE | point `test_reanchor_58_r2_rulings.py:590` at SEAM + a28b's typed set | fold |
| R-3 (lease) | RULED §2 | rows + `error_class` rider | fold (+ lead's scope call on lease.py) |
| R-4 (8 holes) | owners' fixes; interim pinned bound | `UNLOGGED_SITES` entries + finding | fold |
| R-5 / F-15 | 63c's (am-37: accepted residual #517) | — | none |
| R-7 (ordinal-keyed rows) | TEST HYGIENE | key rows per SITE: `file::function::<caught expression>` | fold |
| R-8 | 63c's (am-34 §5) | — | none |
| R-13 (scanner collision) | resolved by HEAD: a28c's per-handler scanner is committed; §HELD part 2 is superseded | r4 regenerates against HEAD | fold |
| **SECURITY DOOR** | none — no finding touches an auth/tenant boundary | — | — |
| **NEW PROPERTY** | **none** | — | **no delta grade** |

**Why no delta grade is safe here, not merely permitted:** the seven surviving wrong builds and every kill probe
are pasted verbatim in the adversary's §INSTRUMENTS (`builds3.py`, `test_adv58r3_probes.py`, `q_f3.py`,
`tuple_probe.py`, `reach_probe.py`, `evidence_probe.py`). The BUILD's cold audit runs them as its mutation set on
the r4 tree: every W-* build must go RED on r4's pins. That is a stronger check than a fourth grade of the
contract text, at zero contract-loop cost. If any W-* survives r4 at the audit, that is a STOP naming the pin,
not a round.

## 4. The r4 fold list (each with its rebase fact)

1. **am-11 (58) ×5** — (a) delete the `_count_live_total` row; (b) retire `raises-chained`; (c) `FAULT_CLASS_NAMES`
   += `_ProbeUnavailableError`, `ProbeGateError`, exact BOTH ways against the translating sites; (d) row 47 →
   `re-raise-unchained` with a REQUIRED `reason`; (e) the positive control: an unadmitted chained translate into
   a verdict is RED by name — the am11 probe's `derived_fate: None | raises-chained holds: True` is the
   before-state to invert.
2. **a28c's 58 items (decision (4)):** `DriverSeamInjection.install(monkeypatch, *, observe_shell: bool = True)`
   (F-3: a driver for a handler that does not ride the shell installs with `observe_shell=False`; a28c's
   `_arm_the_driver_seams` then stops reaching `_seam_wrapper`) · the `server.py::_comms_register` fates row
   STAYS DELETED (F-13/F-13a: it registers a site no correct 63c build has; the fates pin's red at base is
   `packet-63c-i-a-a28-contract`'s) · `listed_handlers()` keeps a28c's D-5 hunk (per-handler keys through
   `index._handler_function`) — r4 rebases onto it, never re-derives the key format.
3. **The `findings.py::_run_guarded` cas_seam red (adversary-a28c's shared-23 flag) — CONFIRMED NOT 58's.**
   Mechanism (read, not inferred): 58's `discovered_drivers()` imports 64b's `test_findings_cas_seam_64b.CAS_SEAM_DRIVERS`
   = `{"findings.py::_run_guarded": …}`; the population pin's `member in static` leg reds because
   `FindingLedger._run_guarded` does not exist until 64b-i's build (`lore_verify` not_found). Under 63c-i-a →
   58 → 64b-i, 58's build cannot green it, and `packet-58-contract` self-destructs at 58's build ("every file
   below stops erroring") — leaving that red RED_ORPHANED at 58's close-out. **Ruling:** `packet-64b-i-contract`'s
   `files:` gains `loremaster/tests/test_reanchor_58_r3_cas_seam.py` with `missing_symbols:
   [loremaster.findings.FindingLedger._run_guarded]` (leg-4 liveness self-destructs it at 64b-i's build). The gate
   permits one path in two rows (`registered_paths` is a union; only duplicate IDS are refused — awk-verified).
   Under §1 the population unit becomes `(R, v)`; 64b's entry re-keys to `lore_findings::<verbs that ride
   _run_guarded>` in the 64b pin pass (G2) — the registry row above covers the interval.
4. **§HELD:** part 2 is SUPERSEDED (a28c folded it; the per-handler scanner is at HEAD) — r4 deletes it from
   its §HELD and re-checks parts 1 and 3 with `git apply --check` on HEAD and again after 63c-i-a commits.
5. The §1/§2 instruments (this amendment) and §3's hygiene rows.

## 5. r4's SAT base and start

- **Base for authoring: HEAD now (`ad6e8ce`+).** A contract author edits test/support files and a §HELD patch;
  63c-i-a's builder edits production in a HEAD-reset scratch copy and hands back a patch (lead report). The
  intersection is empty by construction, so **r4 starts now.**
- **Base for the SAT receipt: HEAD + 63c-i-a's committed build.** Until it lands, r4's targeted SAT adjudicates
  63c-owned reds by the set-diff both adversaries used (base-only / ref-only / shared, every id owned by a
  registry row). **ONE named re-base step when 63c-i-a commits:** re-run the targeted set (r4's files + the
  `lore_impact` covering tests of `_txn`, `tasks`, `findings`, `briefs`, `keeps`, `lease` + the structural pins)
  and re-check §HELD parts 1/3. If 63c-i-a's build changes a fact §1/§2 rest on (`_txn`'s class set, the D-9
  harness forge, the a28c scanner's key format), r4's reference re-derives from HEAD — never from a28c's report.
- **What r4 must NOT do:** run the full suite or the currency gate (once per packet, at the BUILD's cold audit);
  re-add the `_comms_register` row; carry §HELD part 2; replay the adversary's builds (that is the cold audit's
  job, §3).

## 6. Surfaced, not ruled

- **Finding filed:** the eight lifecycle holes (inbox_awaiter ×4, scout ×4) — owners' one-line WARNING fixes;
  interim `UNLOGGED_SITES` entries with triggers (§2).
- **Lead's scope call:** whether 58's build carries the four-line `error_class` log extra in `store/lease.py`
  (11-i-a's file) or it routes to the lease owner. Recommendation: 58's build — it is the row's evidence and
  four lines.
- **Loop status (operator):** 58 at r3 graded (rounds 1–3, ~3 adversary runs + 3 author runs); r4 is a FOLD
  with no grade; the next instrument is the BUILD's cold audit. The CAS-population property struck four times
  across r1–r3; this amendment moves its enforcement to the state so a fifth instance is a cold-audit STOP,
  never a round.

No code/tests/store touched; this doc only; no attribution trailer.
