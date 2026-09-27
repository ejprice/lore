# Packet 64 — ruling amendment 10 (sidecar-64, 2026-09-27): am-9 errata — FK-r2-10 the close-out bound is NOT expressible (the registry adjudicates mypy claims per file; a pytest-only red in a mypy-clean file is #461's class) so the alias rewrite is SEQUENCED INSIDE the build wave and no bound is minted; FK-r2-11 `LegacyMapping` has no instances, so the disposition is derived from the migrate leg's SET clause ALONE and the materialised table is a 63c design item

Rules `REPORT-contract-64b-r2.md` §FORKS FK-r2-10/11 per lead-63c-2's Task 23. Facts read at HEAD:
`scripts/pending_contract_gate.py` — `PendingFile(path, missing_symbols, unsymboled_codes)` with the
registry validator *"names neither a missing symbol nor a code allowance — that degenerates to file-only
matching"*; `partition_pytest` adjudicates by `outcome.file in registry.registered_paths`; leg 2
(`transcript_self_destruct_findings`) fails a registered file that *"produced NO mypy errors"*; leg 4
(`_compute_liveness`) fails a registered symbol that resolves. `governed.LegacyMapping` (`lore_verify`
confirmed, `governed.py`) is a frozen dataclass `(table, disposition)` whose docstring carries the four
dispositions; ZERO instances anywhere in `loremaster/`, `lorerunes/`, `scripts/` (awk over the tree;
`principals.py:1201` and the 64b test files mention the disposition names in prose only).

## 0. Rulings in one screen

| fork | ruling |
|---|---|
| **FK-r2-10** | **ERRATUM (am-9 FK-r2-6): no `packet-64b-i-closeout` bound — it cannot exist.** A bound is a set of MYPY claims per file; the alias pin's post-build red is a PYTEST red in a mypy-clean file, which is exactly #461's ledgered class (*"the gate cannot register a contract-ahead file that is typecheck-CLEAN"*, → packet 09b). Rule: (1) the author's isolation is CONFIRMED — the alias pin lives alone in `test_findings_closeout_64b.py`, its failure message naming the close-out agent and the trigger; (2) the close-out (rewrite every `Any` reach-around as a typed call, delete `packet-64b-i-contract`) is a SEQUENCED STEP OF THE BUILD WAVE, done by a contract-author-class agent between the builder's commit and the wave's currency run, so the pin is red only between two commits of one wave and never meets a gate; (3) the registry extension (a pytest-only bound kind) is 09b's under #461 — NOT built in 64b; the author REMOVES the held entry text from §HELD Part B and annotates #461 with this instance. The synthetic-mypy-marker alternative stays rejected (a second source of truth). §1 |
| **FK-r2-11** | **ERRATUM (am-9 FK-r2-4): there is no `LegacyMapping` table to cross-check against.** Rule the author's ALTERNATIVE: the disposition is derived from the migrate leg's SET clause ALONE (stamps no `owner_*` column ⟺ UNOWNED-LEGACY), complete over `_migrate_legs()` (every leg classified, both ways); the per-table intent pins (kickoff §2 rider (iii) for finding/task; 63b-ia's `_MIGRATE_GOLDEN` for memory) are the intent check. A materialised `governed.LEGACY_MAPPINGS` would be a NEW source of truth in a 63c-owned module against 63c am-1 N2's *"a docstring row, not a table row"* — a design question for sidecar-63c-2, FILED, not ruled here; if 63c materialises it, the agreement pin is one line added later. The author's pick (RED-until-built `LEGACY_MAPPINGS`) is REJECTED for r2. §2 |

## 1. FK-r2-10 — why sequencing, not a bound

- The registry's unit of adjudication is a mypy claim (`missing_symbols` / `unsymboled_codes`) scoped to a
  file; pytest reds are adjudicated only as a SIDE EFFECT of the file being registered for a mypy claim.
  A file with no mypy claim cannot be registered (the validator refuses "file-only matching"), and a
  registered file whose claims discharge self-destructs. So the design space for a post-build pytest-only
  red is: extend the registry (09b's, #461), or never let the red reach a gate. The second costs nothing
  and is the correct shape anyway: *"delete the bound WITH the build"* (contract §11 item 15) already
  makes the close-out part of the build wave; the alias rewrite is the same step.
- Wave sequence, binding on the lead's 64b-i build brief: builder commit (production + `pyproject`) →
  close-out commit by a contract-author-class agent (typed calls replace every reach-around; the alias
  pin flips green; `packet-64b-i-contract` deleted; `--currency` run) → cold audit. The alias pin's red
  between the two commits is intra-wave and unadjudicated BY DESIGN — the same status as any test between
  a RED commit and its GREEN commit. Rider: the wave report's currency receipt is taken AFTER the close-out
  commit (a currency run between the two commits would report an orphan and would be right to).
- The class, named for #461: *a behavioural pin that is RED with every symbol present* has no home in the
  registry. 64b's alias pin is one instance; 58's convergence sweep and any served-string pin are others.
  Annotated on #461, owner 09b, trigger unchanged.

## 2. FK-r2-11 — one derivation, and where intent lives

- am-9 wrote "cross-check against `LegacyMapping`'s STRING-UNRESOLVABLE rows" on the strength of a class
  that `lore_verify` confirms EXISTS — and that `lore_impact` would have shown has NO consumers and no
  instances. The self-rule sharpens: when a ruling depends on DATA existing (rows, instances, entries), verify
  the consumers, not only the symbol.
- With one derivation the completeness pin is: `{leg ∈ _migrate_legs() | SET stamps no owner_*}` ==
  `UNOWNED_LEGACY_TABLES` (the sweep's domain) — a leg that gains an owner stamp leaves the set, a new leg
  with none joins it, both RED by name. Intent per table stays where 63b/63c/64 put it: the goldens
  themselves (a memory golden that started stamping `owner_principal` reds 63b-ia's leg-2 pin; a finding
  golden that stopped carrying `owner_principal IS NONE` reds the kickoff §2 rider (iii) pin).
- The materialisation question, stated for sidecar-63c-2: the dispositions are prose in a docstring; the
  ONLY code that knows a table's disposition is its migrate leg. Whether that is acceptable (N2's position)
  or whether `LEGACY_MAPPINGS` should exist as the derivation's twin is 63c's design call; 64b's pins
  compose with either answer.

## 3. Discipline
- Two more am-9 errata, both the mechanism-from-memory class 58 am-11 §4 / 64 am-9 §5 already named: a
  bound ruled without reading the registry's schema; a cross-check ruled against a table with no rows. The
  self-rule now reads: *read the seam AND its data before ruling how it is used.*
- Loop status (for the operator): 64b-i at contract r2; both forks are errata of my own am-9, not
  contract defects; neither inverts a pin the adversary has graded. No code/tests/store touched; this doc
  only; no attribution trailer.
