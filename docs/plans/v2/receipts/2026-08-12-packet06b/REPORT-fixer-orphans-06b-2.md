brief-base v13 read
brief project v7 read

# REPORT — fixer-orphans-06b-2 (packet 06b — apply the two remaining rulings, prove currency clean)

## SUMMARY BLOCK
- **State:** done-with-deviations. B2 applied + mutation-proven; FORK-2 doc pin applied; all 7 target pins GREEN; currency pytest-leg **0 RED_ORPHANED**.
- **Deviation 1 (load-bearing — needs a lead nod):** the brief's/prior-report's dedicated-control predicate `assert not _leaks(rendered)` is **VACUOUS for this vector** (MEASURED). `_leaks` keys on `FORGERY_MARKER` PROSE, which a charset-gated parseable cadence can NEVER carry — so it returns `False` even on a render where the raw newline SURVIVES. I made `loremaster.sanitise.CONTROL_CHAR_PATTERN` the load-bearing assertion (kept `_leaks` as a documented-secondary belt). This is a strengthening that makes the exemption honest, not a weakening. §B2-CONTROL + §MUTATION-PROOF.
- **Deviation 2 (minor strengthening):** hostile fixture is `"≤1m\r\n "` (brief said `"≤1m\n"`) — a superset packing newline (#210) + CR + U+2028, so `CONTROL_CHAR_PATTERN` is load-bearing beyond the single `\n`. Written as escapes (no literal separator in the source).
- **Packages considered:** none — no mechanism specified (test-only pins + one inherited 1-token prod edit).
- **Reuse ledger (DRY):** 1 new data structure (`_PARSE_GATED_DOOR_FIELDS`, HAND-ROLLED distinct from `_SERVED_SAFE_FIELDS` by brief mandate); control REUSED `CONTROL_CHAR_PATTERN` / `_leaks` / `_app` / `Agent.model_construct`. Table in §DRY-LEDGER.
- **Graded:** not an audit — builder report. Base sha at report: `3e38a5a` (HEAD; the 6 inherited fixes + my B2/FORK-2 are uncommitted in the tree — the lead commits).
- **Decisions needed:** (1) confirm Deviation 1 (`_leaks`→`CONTROL_CHAR_PATTERN` as the discriminator) — I proceeded because `_leaks` is measurably vacuous and shipping it would be a false-clear rug-sweep (a #345 NO-GO); non-blocking to currency, which is already 0 RED_ORPHANED.
- Receipt pointers: B2 code §B2-CHANGES; control §B2-CONTROL; mutation+vacuity proof §MUTATION-PROOF; FORK-2 §FORK-2; 7-pins §7-PINS; no-regression §NO-REGRESSION; gates §GATES; currency §CURRENCY; diff §DIFF.

---

## INHERITED (verified present via `git diff`, KEPT, not redone)
The 6 mechanical fixes from `REPORT-fixer-orphans-06b.md` are in the tree, byte-matching that report:
- `server.py`: `_CADENCE_RE.match` → `.fullmatch` (in `_parse_cadence_seconds`).
- `_surreal_harness.py`: docstring `53→54` importers AND `35→37` callers.
- `test_agent_registry.py`: `"declared_cadence"` added to the `Agent` exact-set field pin.
- `test_retry_seam.py`: 2 brief-body fixtures bumped to `"a standing wave instruction"` (≥3 words).

---

## B2 — `_PARSE_GATED_DOOR_FIELDS` (finding #368) — GREEN

### §B2-CHANGES (`test_render_slot_inventory.py`)
1. **New exemption dict `_PARSE_GATED_DOOR_FIELDS`**, DISTINCT from `_SERVED_SAFE_FIELDS` (so the mis-park pin `TestNoServedSafeFieldIsAManifestDoor` is untouched — a door here is CORRECT, a door there is the #345 defect). One entry, `declared_cadence`, with the evidence-backed reason (manifest DOOR whose only driven render is parse-gated by `_parse_cadence_seconds(...) is not None` → forge token cannot parse → un-observable via a token BY CONSTRUCTION; residual whitespace/newline vector #210 CONTAINED by `render_attributed`) + re-open trigger (overdue verdict renders `declared_cadence` outside the parse gate, OR the charset widens to admit a printable forgery char).
2. **Leg-1 main pin** (`test_every_served_field_is_driven_with_content_or_justified_safe`): the offender loop now skips `field in _PARSE_GATED_DOOR_FIELDS` alongside `observed` / `_SERVED_SAFE_FIELDS`.
3. **Leg 2 UNCHANGED** — `declared_cadence` still routes through `render_attributed` at `_render_comms_fleet_row:7352`, so it is already `contained=True` and Leg 2 (`test_every_uncontained_served_field_is_justified`) still requires it (I did NOT add it to any Leg-2 skip).

Baseline before my edit (contract-first): the B2 pin was RED with exactly one offender —
`_render_comms_fleet_row:7352 serves 'declared_cadence' — a DOOR served but NEVER observed with content`.

### §B2-CONTROL — the DEDICATED discriminating control
`TestEveryServedSlotIsDrivenWithContentOrJustifiedSafe::test_the_overdue_cadence_slot_neutralises_a_hostile_parseable_declared_cadence` (mirrors the `task_id` control). Builds an `Agent` with `declared_cadence="≤1m\r\n "` (parses to 60s), renders `_render_comms_fleet_row(..., heartbeat_age_s=600)` so the overdue branch fires, and asserts:
- `"overdue" in rendered` — the gated slot is actually exercised (non-vacuity);
- **`not CONTROL_CHAR_PATTERN.search(rendered)`** — the LOAD-BEARING check: no line-fracturing char from the hostile cadence survives into the served row;
- `not _leaks(rendered)` — documented-secondary belt (marker-blind here, kept for the re-open-trigger world where the charset widens to admit a printable char).

**Why `CONTROL_CHAR_PATTERN`, not `_leaks` (Deviation 1, MEASURED).** A parseable cadence is confined to `^[≤<~=\s]*\d+\s*[smhd]\s*$` — the ONLY forgery it can carry is line-fracturing WHITESPACE, never `FORGERY_MARKER` prose. So `_leaks` (which strips delimited regions and scans for the marker) is structurally blind to this vector. The engine that neutralises a whitespace/newline forgery is `sanitise_line` (via `render_attributed`), whose exact class is `CONTROL_CHAR_PATTERN` — so that IS the discriminator.

### §MUTATION-PROOF (scratch, provenance-asserted — #140)
`scripts/scratch_copy.sh /tmp/lore-scratch-06b2-2646630` — provenance receipt:
```
loremaster.__file__ = /tmp/lore-scratch-06b2-2646630/loremaster/loremaster/__init__.py
```
Control GREEN at scratch baseline (2 passed). Two mutations of the `_render_comms_fleet_row` overdue branch:

- **Mutation A (brief-literal: bypass `render_attributed` → raw value):** `cadence=render_attributed(row.declared_cadence)` → `cadence=row.declared_cadence`. Control → **RED** via `render_line`'s runtime control-char guard (`RenderSafetyError: value for 'cadence' is not a SafeLine…`). Proves removing containment breaks the render — the guard is a hard backstop.
- **Mutation B (manual bypass: raw cadence survives into output):** overdue branch returns a manual f-string interpolating raw `row.declared_cadence`. Control → **RED** via **the `CONTROL_CHAR_PATTERN` assert firing directly** on `\r\n ` (`re.Match span=(40,43)`), rendered bytes:
  `'- agent-x [active] overdue (declared ≤1m\r\n , silent 10m) · role ```release-bot```'`.
- **Vacuity proof (same leaked bytes):** `CONTROL_CHAR_PATTERN.search(...) -> True` (my assert fires) but **`_leaks(...) -> False`** (misses the real leak). This is the receipt that `_leaks` alone would have been a **false clear**, and `CONTROL_CHAR_PATTERN` is the true discriminator.
- **Restore → GREEN** (`scratch_copy.sh --verify-only` re-verified provenance; control 1 passed).

Verdict: the exemption's control mutation-provably **DISCRIMINATES** → GO, not the vacuous-exemption NO-GO the brief's STOP-trigger guards against.

---

## FORK-2 — the truthful doc pin (GREEN)
Kept the inherited `.fullmatch` (satisfies #210 intent). Added `TestParseCadenceSecondsToleratesTrailingWhitespace` in `test_mcp_server.py` (the cadence-semantics home; `_parse_cadence_seconds` had NO prior direct test). It pins:
- `_parse_cadence_seconds("≤2m") == 120` (base);
- `_parse_cadence_seconds("≤2m\n") == 120` (**trailing newline TOLERATED**, parses identically — tolerant parser #360 W1c; `.fullmatch` ≡ `.match` because the pattern ends in `\s*$` and `\s` absorbs `\n`; render safety is `render_attributed`'s job, #210 residual contained);
- `_parse_cadence_seconds("junk") is None` (positive control — the parser is NOT accept-all).
Comment explicitly says **do NOT tighten the anchor**. I did NOT touch the server-side anchor.

---

## §7-PINS — all 7 original target pins GREEN
`7 passed, 4 skipped in 19.68s` (the 4 skips are non-selected params of the A2 parametrized method; 0 failed):
- A1 `test_anchored_pattern_seam.py::TestNoAnchoredPatternValidatedWithMatch::test_every_anchored_match_use_is_allowlisted`
- A2 `test_ast_reach_helpers.py::TestSharingProvenByMutation::test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped`
- B1 `test_agent_registry.py::TestNoForwardCompatFieldsOnAgent::test_agent_field_set_is_exactly_the_c1_slice`
- B2 `test_render_slot_inventory.py::…::test_every_served_field_is_driven_with_content_or_justified_safe`
- B3a `test_retry_seam.py::TestBriefMintSharesTheDriver::test_exhausted_contention_on_the_CREATE_still_burns_no_version`
- B3b `test_retry_seam.py::TestEveryCallerRunsTheSameRetryPolicy::test_the_brief_mint_obeys_them_too_end_to_end`
- B4 `test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts`

## §NO-REGRESSION
- Touched + related files (`-n auto`): `test_render_slot_inventory` + `test_link5_render_containment` + `test_agent_registry` + `test_retry_seam` + `test_surreal_harness` + `test_anchored_pattern_seam` + `test_ast_reach_helpers` → **1025 passed, 4 skipped, 1 warning** (26.63s). The warning is a pre-existing `RuntimeWarning: coroutine '_empty_subscription' was never awaited` in `test_retry_seam.py:3216`, unrelated to my changes.
- `test_mcp_server.py -k "cadence or overdue or Fleet …"` (incl. the new FORK-2 class): **13 passed** (18.80s).
- `test_render_slot_inventory.py` full: **16 passed** (7.08s).

## §GATES
- `uv run ruff check .` → **All checks passed!**
- `scripts/typecheck.sh` → **191 errors total = exactly the #333 baseline (RED_ADJUDICATED)**, and **ZERO in my touched files** (`test_render_slot_inventory.py`, `test_mcp_server.py`) → ZERO-NEW confirmed.

## §CURRENCY (load-bearing close-out receipt)
`uv run python scripts/pending_contract_gate.py --currency` → **CURRENCY: PASS**; pytest leg has **0 RED_ORPHANED** (the 7 orphan pins are now GREEN and dropped out of the orphan set; the remaining pytest residuals are the pre-existing packet-39 adjudicated bound, NOT orphans). Verdict tail:
```
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 191 residual(s), owned by: packet-39-pending-build (…trigger: operator decision #296, or packet 39's build start…)
  ruff         GREEN
  pytest       RED_ADJUDICATED — 444 residual(s), owned by: packet-39-pending-build (…trigger: operator decision #296, or packet 39's build start…)
CURRENCY   : PASS — every claimed gate is GREEN or OWNED
  (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
```
No `RED_ORPHANED` bucket appears anywhere in the run (grepped) — the currency PASS is exactly "0 RED_ORPHANED".

## §DRY-LEDGER
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_PARSE_GATED_DOOR_FIELDS` (module allowlist) | read `_SERVED_SAFE_FIELDS` in the same file (the existing exemption seam) | an evidence-backed allowlist keyed by field name, guarded by the mis-park pin | **HAND-ROLLED (distinct by mandate)** — brief requires it SEPARATE from `_SERVED_SAFE_FIELDS` so `TestNoServedSafeFieldIsAManifestDoor` stays untouched (a door is legal here, illegal there); same `dict[str, tuple[str, str]]` shape for consistency |
| control's leak/line-fracture predicate | inspected `loremaster.sanitise.CONTROL_CHAR_PATTERN` + `test_link5._leaks` | `CONTROL_CHAR_PATTERN` = the exact line-fracturing char class `sanitise_line` collapses | **REUSED `loremaster.sanitise.CONTROL_CHAR_PATTERN`** (not a hand-rolled `"\n" not in ...`, which would miss CR/U+2028); `_leaks` reused as documented-secondary |

## §DIFF
```
 loremaster/loremaster/server.py                |   2 +-
 loremaster/tests/_surreal_harness.py           |   4 +-
 loremaster/tests/test_agent_registry.py        |   6 ++
 loremaster/tests/test_mcp_server.py            |  34 ++++++++
 loremaster/tests/test_render_slot_inventory.py | 113 ++++++++++++++++++++++++-
 loremaster/tests/test_retry_seam.py            |   4 +-
 6 files changed, 157 insertions(+), 6 deletions(-)
```

## Discipline / receipts
- Commit-only: NO git add/commit/revert (the lead commits; rides the next deploy).
- Store: tests hit `spike-surreal :18000` throwaway `unique_database()` only; `:18500` never touched.
- Scratch `/tmp/lore-scratch-06b2-2646630` used for the mutation proof (provenance-asserted, `loremaster.__file__` printed; server.py restored to clean git state inside it, no work of value). ⚠ Could NOT auto-remove it — `rm -rf` is sandbox-blocked here (auto-denied, no human). It is a disposable `/tmp` scratch (NOT a git worktree); safe to `rm -rf` at any time.
- ⚠ Minor record hygiene: the `lore_findings annotate` on #368 has a trailing tool-serialization artifact (stray `</note>…rm…` text) from a malformed tool call; the note's SUBSTANCE (applied-fix + `_leaks`-vacuity correction) is complete and correct.
