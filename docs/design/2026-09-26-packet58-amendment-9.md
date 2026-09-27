# Packet 58 — ruling amendment 9 (sidecar-64, 2026-09-26): the r3 contract's six forks — `claim_task` is NOT listed (erratum on am-7 §2 / am-4), the SWALLOW rule is whole-tree and form-blind while the exact sets stay in the re-read domain, RS-5's tier is a table row not a rollback leg (erratum on am-7 §4), the discovered driver registry, the MINIMAL CAS verb, per-entry `blocker_id`; F-r3-1 built in r4, F-r3-3 = `pytest-timeout`

Rules `REPORT-contract-58-r3.md` §FORKS FK-r3-1…6 and §FLAGS F-r3-1/-3 per lead-63c-2's Task 19 Part B.
Aligned with sidecar-63c-2's FK-a28b-4 position (the partition landed in 63c-i-a at `e039c64` per lead
#17087): am-7 §0 row 2's "ONE set first, partition as 58's delta" is SUPERSEDED by that directive — same
partition, different wave; 58's delta shrinks accordingly (§7). Facts: a28b's `_TYPED_CAS_CATCHES =
{agents.py::register, keeps.py::get_or_create_keyed}` with a comment "58's §HELD delta adds
`tasks.py::claim_task`"; a28b's derived re-read = an awaited same-class method carrying a `SELECT` literal
INSIDE the handler; `_log_rollback` is called only from `_run_verified_transaction` (never from `run_query`).

## 0. Rulings in one screen

| fork | ruling |
|---|---|
| **FK-r3-1** | **Reading A.** The re-read DOMAIN governs the exact sets; a ruled `claim_task` (typed catch, owner read AFTER the `try`) has no re-reading handler → NOT in `_TYPED_CAS_CATCHES`. **ERRATUM, mine:** am-4's `_TYPED_CAS_CATCHES` entry for claim and am-7 §2's claim row were written BEFORE am-7 §1 settled the domain and contradict it. a28b's "58 adds claim_task" comment → a DUAL note saying why not. Claim's exhaustion safety = the driver-seam runtime ∀ (am-8 §3, identity) + r2's catches-the-TYPE pin. §1 |
| **FK-r3-2** | **Reading A.** RS-5's CREATE rides `run_query`, which has no transaction and logs no rollback. **ERRATUM, mine (am-7 §4):** "a UNIQUE violation on RS-5 → exactly one WARNING" was derived on the txn path and stated over both (quantifier law). The keeps leg is the real 8-way WARNING race; RS-5 has a tier ROW + producibility through keeps, no behavioural leg. `run_query`'s own rejection logging is 63c's surface — flagged, not ruled. §2 |
| **FK-r3-3** | **Reading A, generalised into the SWALLOW RULE:** ONE catch-site walker over `Try` / `TryStar` / `With(contextlib.suppress)`, ONE resolver; the exact sets are re-read-domain members only; but ∀ catch sites in the WHOLE production tree, form-blind: caught closure ∋ `TxnContentionExhaustedError` with no passthrough `raise` → RED by `file::function`. A correct build is never RED under it (it never swallows), so it has none of F5/F8's fragility. §3 |
| **FK-r3-4** | **Reading A.** Drivers are DISCOVERED (module-level `CAS_SEAM_DRIVERS` in any test module); the coverage pin is per listed handler and per static CAS verb; un-driven → RED by name; the owner adds the driver in its OWN module. The three reds (record_measurement, keeps, RS-5) are the lead's routing (am-7 §3 item 2), owned under `packet-58-contract` until routed. 64b declares its own entry for `findings.py::_run_guarded` (64 am-8 §4). §4 |
| **FK-r3-5** | **Reading A — MINIMAL.** A CAS verb reaches the shell AND the driver, and no direct callee does both. Rider: a swallow in a WRAPPER above a minimal verb is outside the runtime ∀'s reach BY DESIGN and is caught by the whole-tree swallow rule (§3) — the two legs are complementary, so stated. §5 |
| **FK-r3-6** | **CONFIRMED.** Both unresolvable records (phantom, cycle) carry `blocker_id` = the entry; per row, the records' `blocker_id` set == the row's unresolvable entries. §5 |
| **F-r3-1** | **Build it in r4** as a GENERATED allowlist-the-safe pin: each marker literal `_txn` classifies appears (a) in `_txn` and (b) only as the PREFIX of a THROW-message constant elsewhere; any other production comparison against it → RED. am-6's mechanism claim has no instrument today; a rule without one is a hope. §6 |
| **F-r3-3** | **`pytest-timeout`** (packages law, pre-approved dev dependency): the harness gains a per-test default; the F4 cyclic legs carry a tight `@pytest.mark.timeout`. The value is the lead's; the mechanism is ruled. §6 |

## 1. FK-r3-1 — claim is not listed; why the domain wins

- The exact sets are an INDEX of handlers the scanner can see and classify; a name in a set that no correct
  build produces reds every correct build (the SAT fragility F5/F8 were about, in a new costume). Under am-7
  §1 a handler is in the index iff it re-reads; the ruled claim does not (am-3 §3, am-5's rejected inline
  re-read). Listing it would require either a domain that admits non-re-reading swallows (then every typed
  `except X: pass` in the tree joins the index — an unbounded name-list) or a claim that re-reads inline
  (rejected). Reading A.
- What still certifies claim: (i) the driver-seam injection asserts the injected instance reaches the
  caller (`is`) — a swallow or a reinterpretation fails identity; (ii) r2's behavioural pin that the catch
  is the TYPE (`TxnClaimLostError`) never the text; (iii) the static swallow rule (§3) — a `except
  SurrealStoreError:` claim would red by name without being in any set.
- **Erratum record:** am-4 §"The reach question" (`_TYPED_CAS_CATCHES` gains `claim_task`) and am-7 §2
  ("`tasks.py::claim_task` → `_TYPED_CAS_CATCHES`") are WITHDRAWN. The class: a membership stated before its
  domain was defined; the domain, once defined, excludes it. 58's §HELD rewrites a28b's comment as a DUAL
  note citing this section.

## 2. FK-r3-2 — a rollback tier needs a rollback

- `_log_rollback` runs where a transaction rolls back. RS-5's agent CREATE rides `run_query` (a28b measured
  it: the record-id collision arrives via the SDK `query()` path) — no `BEGIN`, no rollback, no record at
  any tier. am-7 §4's row "RS-5 → exactly one WARNING" cannot be true on that path; it was derived on the
  keeps txn path. Reading A: the tier TABLE keeps the class row (`TxnUniqueViolationError` → WARNING) with
  producibility through the keeps 8-way race (a real rollback, every record at WARNING); no RS-5
  behavioural leg in 58.
- **Flag for 63c (not ruled here):** whether `run_query`'s rejection log (its `label=` line) should tier by
  the SAME class table — consistency across the two driver entry points is a 63c-owned question; the
  askable form: *"does a class have two loudness policies depending on which driver door raised it?"*

## 3. FK-r3-3 — the swallow rule, whole tree, form-blind

- ONE walker yields every catch site: `ast.Try` handlers, `ast.TryStar` handlers, and a `With` item whose
  context expression resolves BY IMPORT to `contextlib.suppress` (the classes are its call args); ONE
  resolver `_caught_classes` maps each caught expression (Name / Attribute / Tuple / bare) to the class
  closure. Two consumers:
  1. **the exact sets** — members of the re-read domain only (unchanged partition: door iff closure ∋
     exhaustion, else typed);
  2. **the swallow rule** — ∀ sites in the whole production tree, regardless of re-read: closure ∋
     `TxnContentionExhaustedError` AND the site does not re-raise it unchanged (a `suppress` never can; a
     handler must carry the passthrough `except TxnContentionExhaustedError: raise` ABOVE it) → RED by
     `file::function`. Measured at HEAD: 0 store-class `suppress` sites; discriminators are synthetic.
- Why this is not a receding reach: the SAFE set is stated (typed catches whose closure excludes exhaustion;
  doors carrying the passthrough); everything else is named. And the property's ∀ lives at the driver seam
  anyway (am-8 §3) — the static rule is the reviewer-visible half that also reaches code no test drives.

## 4. FK-r3-4 — discovered drivers

- The registry is a CONVENTION name (`CAS_SEAM_DRIVERS`, module-level, in any test module), found by an AST
  scan of the test tree then imported. A misspelled or missing registry is LOUD: the coverage pin is
  parametrised per handler and per derived CAS verb, so an un-driven one reds BY NAME — the discovery
  cannot fail silently. Owners: `floor_calibration` (record_measurement's fence tests), keeps and RS-5 (63c),
  `findings.py::_run_guarded` (64b — am-8 §4). The lead routes; until routed the three reds sit under
  `packet-58-contract` with the routing named as the trigger (§CURRENCY), which is an adjudicated red, not
  an orphan.

## 5. FK-r3-5 · FK-r3-6

- **Minimal verb:** confirmed. The transitive wording admitted every public wrapper and `ensure_ready`;
  the minimal form keeps F8's extracted helper and N20's helper-applied verb IN and drops wrappers. Rider,
  stated so it is not lost: the runtime ∀ drives MINIMAL verbs; a wrapper that adds its own catch above one
  (e.g. `acknowledge` wrapping `_transition` in `except SurrealStoreError: return None`) is outside that
  reach and is caught ONLY by §3's whole-tree swallow rule — which is why §3 is whole-tree.
- **`blocker_id`:** confirmed per am-8 §4 (one record per unresolvable ENTRY, the row skipped whole). Pin:
  a row with entries {phantom P, cyclic C, healable H} → two records `{P, C}`, zero rewrites, `count`
  excludes the row; CONTROL: `{H}` alone → healed, no record.

## 6. F-r3-1 · F-r3-3

- **F-r3-1:** the generated pin — derive the marker vocabulary FROM `_txn`'s classifier (never a hand-list),
  then ∀ markers: production occurrences are exactly {the classifier, THROW-message constants whose text
  STARTS with the marker}; a comparison, `in`, `startswith` or slice against a marker anywhere else → RED
  naming `file:line`. Positive control: a synthetic module comparing `"claim_lost:" in str(error)`. r4.
- **F-r3-3:** `pytest-timeout` as a declared dev dependency (`uv add --dev`), a generous suite default in
  `pyproject.toml` (the lead names the number from the measured slowest test), `timeout_method = signal`
  (a sync chain-follow on the main thread is exactly what SIGALRM interrupts; xdist workers each run their
  own), and `@pytest.mark.timeout(<tight>)` on the F4 cyclic legs so a hang is a RED with a name, never a
  stalled lane. Report in the close-out what was added and why (the packages law's receipt).

## 7. Sequencing, restated after #17087

- 63c-i-a landed the partitioned scanner (`e039c64`). 58's §HELD delta is now: the catch-form walker + ONE
  resolver (§3), the swallow rule, the runtime↔static cross-check, the DUAL note on a28b's claim comment,
  the corpse prose. NOT the partition, NOT the two moves (landed).
- Loop status (for the operator): 58 at round 3; r3 continues on its picks, all six CONFIRMED here (two of
  them by correcting my own earlier rows). No new property; nothing here re-opens a ruling.
- No code/tests/store touched; this doc only; no attribution trailer.
