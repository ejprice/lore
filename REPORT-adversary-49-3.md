# REPORT — adversary-49-3 (packet 49 CONTRACT ADVERSARY, r3 NARROW re-grade)

`brief-base v14 read` · `brief project v7 read`

**CAPABILITY CHECK (brief-base §4):** every demand met — read `brief-base.md`, the role spec
`~/.claude/agents/contract-adversary.md`, the r3 diff (`4d3e483`), and the r1/r2 adversary
reports; lore tools loaded (`ToolSearch "+lore"`); comms/task ledgers reachable; built the
CORRECT r3 reference + 6 wrong builds in a `scratch_copy.sh` copy; ran the FULL gate (4 pkt-49
files + full `test_retry_seam.py`) + targeted discrimination/regression pins against
spike-surreal `:18000`. No gap.
**Model:** I cannot self-read my model, but the harness sets `CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8`
in this process's env (a real receipt, not just self-report) — consistent with the brief's assertion.
Reported as **claude-opus-4-8**.
Role spec READ + EXECUTED as a NARROW subset per the brief: **P0 (controls) + P1/P2
(satisfiability + new-pin discrimination) + P4 (reproduce r2's claims) + a P6-style regression
spot-check.** I did NOT re-run the full 13-wrong-build sweep (r1/r2 already did; brief scoped me
to the ONE thing r2 could not prove + the new pins). **I do not spawn subagents; did the work
directly.**

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT SUFFICIENT.** The r3 map registration CLOSES adversary-49-2's sole blocker
  (FINDING 1): a CORRECT reference build is now **0-failed on the FULL gate** the builder actually
  runs — the receipt r2 could not produce.
- **P1 headline — FULL-GATE SATISFIABILITY (the load-bearing result):** my CORRECT r3 reference
  (`PrincipalKeyStore._query` with EXACTLY `noun="principal key query"`,
  `label="principal.key.query.rejected"`, matching the r3 maps) runs **762 passed / 0 failed**
  across all 4 packet-49 files AND the full `test_retry_seam.py` (32+30+41+25+634 = 762; no
  skips/xfails/errors hidden). r2's blocker — a correct build failing ≥2 retry-seam pins — is GONE.
- **P2 — NEW-PIN DISCRIMINATION (the registration is not a rubber stamp):** a wrong `_query`
  label/noun, or a missing map entry, is CAUGHT — table in §DISCRIMINATION. The canonical strings
  are REQUIRED, not decorative.
- **REGRESSION SPOT-CHECK:** the r3 change (maps + docstrings only) did NOT weaken the r1/r2 pins —
  #206 constant-identity, verbatim `list-keys`, and revoked-key-ignored verify are all STILL
  CAUGHT — table in §REGRESSION.
- **P0 controls:** every target pin PASSES on the correct build (positive control) and FAILS under
  its mutation — so each "CAUGHT" is a real discrimination, not a probe firing for the wrong reason.
- **Note (not a finding):** the r3 author chose `label="principal.key.query.rejected"` /
  `noun="principal key query"` (dotted/spaced, mirroring `PrincipalStore`'s `principal.query.rejected`
  / `principal query`) — NOT adversary-49-2's *suggested* `principal_key.query.rejected` /
  `principal_key query`. The r3 choice is the more consistent one and is internally coherent (maps +
  docstring + my reference all agree); the divergence from the r2 suggestion is a BETTER call, not a
  defect. Called out so the builder uses the r3 strings, not the r2 report's.
- **Graded: 4d3e483 · HEAD-at-report: 4d3e483 · SAME (0 behind).**
- **Packages considered:** none — no NEW mechanism specified; my reference REUSES the existing
  in-tree seams (`loremaster.store._txn.run_query/execute_transaction/bootstrap_session/
  signin_credentials`, `loremaster.index.records.sha512_hex`, `lorerunes.is_blank`,
  `loremaster.sanitise.{sanitise_line,safe_str}`, `secrets`, `argparse`). `Packages considered:
  none — no NEW mechanism specified`.
- **Reuse ledger:** none — I authored no shipped symbols. The reference build + mutator + driver
  live only in `/tmp` (disposable); all three are PASTED VERBATIM in §APPENDICES so the measurement
  is re-runnable (brief-base §1).
- **pointers:** satisfiability §SATISFIABILITY · discrimination §DISCRIMINATION · regression
  §REGRESSION · HEAD-stub grounding §HEAD-STUB · reference-build delta §APPENDIX-A · mutator
  §APPENDIX-B · driver §APPENDIX-C.

## The ONE message to lead

`STATE: done · REPORT: REPORT-adversary-49-3.md · CONTRACT SUFFICIENT — r3 map registration CLOSES r2's blocker: correct reference is 762 passed / 0 failed on the FULL gate (4 pkt-49 files + full test_retry_seam.py). New registration pins DISCRIMINATE (wrong label/noun + missing map entry all CAUGHT); r1/r2 pins survive r3 (206/list-keys/revoked still CAUGHT). Builder must use r3's strings noun="principal key query" / label="principal.key.query.rejected" (NOT r2 report's underscore variant). Spawn builder on 762/0.`

---

## PROVENANCE (brief-base §6 / #140 — prove which tree)

All builds ran in a fresh `scratch_copy.sh`-minted copy of HEAD `4d3e483`, provenance ASSERTED:

```
$ ./scripts/scratch_copy.sh /tmp/adv49_3_ref   (exit 0)
loremaster.__file__ = /tmp/adv49_3_ref/loremaster/loremaster/__init__.py   (INSIDE scratch, re-checked post-build)
```

Live store: spike-surreal `ws://127.0.0.1:18000` (systemd `active`; NEVER `:18500`).

---

## SATISFIABILITY RECEIPT (Task 1 — the load-bearing one r2 could not prove)

**What r2 could not prove and why:** adversary-49-2 graded d09f0d6 INSUFFICIENT because its FINDING 1
showed a CORRECT build was 0-failed only under 4-file scoping — on the FULL gate (which the builder
must keep green) it failed ≥2 `test_retry_seam.py` pins, because that file's hand-written
`_SEAM_REJECTION_EVENTS` / `_SEAM_REJECTION_NOUNS` maps had no `PrincipalKeyStore` entry, yet pin-17c
forces `PrincipalKeyStore._query` to be DISCOVERED by `_discover_query_seams()`, pulling it into every
parametrization there. r3 (`4d3e483`) registers the two map entries (mirroring 48-B's `PrincipalStore`,
#353) and specifies the exact strings in the `_query` stub docstring + pin-17c.

**My CORRECT r3 reference** builds the packet-49 implementation onto the scratch stubs (emitter slice
folded into `generate_ddl`; `PrincipalKeyStore.ensure_ready/mint/list_for/revoke/verify` + the shared
`_query` seam; `PrincipalStore.set_expires/delete`; the 9-verb CLI rendering through the shared
sanitiser; `main` via `asyncio.run`). The ONE r3-critical detail: `_query` calls `run_query` with
**`noun="principal key query"`, `label="principal.key.query.rejected"`** — the exact strings the r3
maps register (built code, `principal_keys.py:373`). Full delta vs the r2 reference in §APPENDIX-A.

**FULL GATE — 4 packet-49 files + the FULL `test_retry_seam.py`, 0 failed:**

```
$ cd /tmp/adv49_3_ref && uv run pytest \
    loremaster/tests/test_principal_keys_schema.py \
    loremaster/tests/test_principal_keys_store.py \
    loremaster/tests/test_principals_cli.py \
    loremaster/tests/test_principals_store.py \
    loremaster/tests/test_retry_seam.py \
    -q -n auto -p no:cacheprovider
  762 passed, 1 warning in 12.68s        # PYTEST_EXIT=0
loremaster.__file__ = /tmp/adv49_3_ref/loremaster/loremaster/__init__.py
```

Per-file collection reconciles the 762 exactly (correct build, `--collect-only`):

| file | collected |
|---|---|
| test_principal_keys_schema.py | 32 |
| test_principal_keys_store.py | 30 |
| test_principals_cli.py | 41 |
| test_principals_store.py | 25 |
| test_retry_seam.py | 634 |
| **total** | **762** |

No `skip` / `xfail` / `xpass` / `error` in the log (grepped). The 1 warning is a pre-existing benign
`RuntimeWarning` (`_empty_subscription` coroutine never awaited, `test_retry_seam.py:3216`), NOT a
failure. **A CORRECT build is 0-failed on the gate the builder runs — r2's blocker is CLOSED.**

Note: this run used the FULL `test_principals_store.py` (25 tests, incl. the unchanged 48-B tests),
not r2's `TestSetExpires`+`TestDelete` scoping — the brief asked for the full 4 files. All pass.

---

## DISCRIMINATION (Task 2 — the registration is REQUIRED, not a rubber stamp)

Each row: restore correct reference → apply ONE mutation → run the target pin → classify. The
POSITIVE CONTROL leg (correct build) shows every target pin PASSES, so a CAUGHT is a real
discrimination, not a probe firing for the wrong reason (P0). Mutator §APPENDIX-B, driver §APPENDIX-C.

| positive control (correct build) | pin | result |
|---|---|---|
| CTRL-attrib | `test_the_exhaustion_record_names_the_seam...[PrincipalKeyStore]` | **1 passed** |
| CTRL-mapevent | `test_every_seam_still_logs_its_OWN_canonical_rejection_event` | **1 passed** |

| wrong build | pin | result + RIGHT-reason receipt |
|---|---|---|
| **WBlabel** — `_query` uses `label="principal_key.rejected"` (≠ map) | attribution `[PrincipalKeyStore]` | **CAUGHT** — `AssertionError` @7093: `assert 'principal_key.rejected' == 'principal.key.query.rejected'` ("must carry the seam's OWN canonical rejection event") |
| **WBlabel** (same) | `test_every_seam_still_logs...` | **CAUGHT** (1 failed) — observed event ≠ canonical map value |
| **WBnoun** — `_query` uses `noun="principal keys"` (≠ map) | `test_every_seam_still_logs...` | **CAUGHT** — `AssertionError` @6245 "a seam's raised-message NOUN changed" (observed `principal keys` vs canonical `principal key query`) |
| **WBmapdrop** — `_query` correct but the `PrincipalKeyStore` map entry REMOVED (= r2's exact state) | attribution `[PrincipalKeyStore]` | **CAUGHT** — `KeyError: 'PrincipalKeyStore'` @7091 (`_SEAM_REJECTION_EVENTS[seam.__name__]`) — **reproduces r2 FINDING 1 verbatim** |
| **WBmapdrop** (same) | `test_every_seam_still_logs...` | **CAUGHT** (1 failed) — set/noun mismatch |

**Verdict:** the canonical strings `label="principal.key.query.rejected"` / `noun="principal key query"`
are REQUIRED — a wrong label is caught by the attribution pin (@7093), a wrong noun by the
noun-mapping pin (@6245), and a MISSING map entry by both (@7091 KeyError + @6290 set-mismatch). The
registration pin is discriminating, and WBmapdrop confirms the r3 map entry is load-bearing: delete it
and the exact r2 blocker returns.

## REGRESSION (Task 3 — r3 did not weaken the r1/r2 pins)

r3 touched only the retry-seam maps + three docstrings — no assertion in the packet-49 contract
changed. Spot-check of 3 previously-caught wrong builds confirms they are STILL caught:

| positive control (correct build) | pin | result |
|---|---|---|
| CTRL-206 | `TestPerPrincipalIdentity206` | **1 passed** |
| CTRL-listkeys | `test_hostile_key_name_does_not_forge_a_row_in_list_keys` | **1 passed** |
| CTRL-revoked | `test_revoked_key_is_denied_on_the_next_verify` | **1 passed** |

| wrong build | pin | result |
|---|---|---|
| **WB206** — verify resolves a CONSTANT `get_by_email("alice@…")` (#206 collapse) | `TestPerPrincipalIdentity206` | **CAUGHT** (1 failed) |
| **WBF4a** — `list-keys` prints `k.name` VERBATIM (no `sanitise_line`) | `test_hostile_key_name_does_not_forge_a_row_in_list_keys` | **CAUGHT** (1 failed) |
| **WBrevoked** — verify drops the `revoked_at` deny (revoked key still verifies) | `test_revoked_key_is_denied_on_the_next_verify` | **CAUGHT** (1 failed) |

All three r1/r2 pins survive r3 intact.

## HEAD-STUB — grounding the "604 passed / 1 RED" claim (re-derive inherited numbers)

The r3 commit claims `test_retry_seam.py = 604 passed / 1 RED` at the stub. Re-measured against the
REAL HEAD `4d3e483` (read-only, no mutation):

```
$ uv run pytest loremaster/tests/test_retry_seam.py -q -n auto -p no:cacheprovider
  1 failed, 604 passed, 1 warning in 11.31s        # EXIT=1
  FAILED ...::test_every_seam_still_logs_its_OWN_canonical_rejection_event
    AssertionError: a seam's raised-message NOUN changed  (test_retry_seam.py:6245)
```

Confirmed **604/1**. The single RED is the noun-mapping assert (@6245, which fires before the
event/logger asserts): at the stub `PrincipalKeyStore` has no `_query`, so `_discover_query_seams()`
does not surface it, yet the r3 map now carries a `PrincipalKeyStore` entry — so `observed_nouns`
(14 seams) ≠ `_SEAM_REJECTION_NOUNS` (15 entries). That is the deliberate "the builder must add
`_query`" signal. My reference build adds `_query` (→ 15 discovered seams), closing exactly that gap:
the retry-seam collection grows 605→634 (≈29 seam-parametrized functions each gain a
`[PrincipalKeyStore]` param) and every one passes in the 762/0. **The number reconciles both ways.**

## NARROW-SCOPE NOTE (P1b / P1c / P-PKG)

Per the brief this was a NARROW pass (P0 controls + P1 satisfiability + P2 new-pin discrimination +
P4 claim-reproduction + a regression spot-check). The full P1b quantifier table, P1c reach table, and
P-PKG survey were produced by adversary-49-1 (r1) and adversary-49-2 (r2) over the whole 4-file
contract and are unaffected by r3 (which changed only the maps + docstrings, no production logic and
no packet-49 assertion). I confirmed the ONE reach question r3 bears on — the new registration guard's
reach and discrimination — empirically above (§DISCRIMINATION): the guard's population is DERIVED from
`_discover_query_seams()` (an AST scan), coverage is a checked variable (the `observed.keys() ==
_SEAM_REJECTION_EVENTS.keys()` set-comparison reddens when the derived seam set and the hand-written
map disagree in EITHER direction — WBmapdrop proves it), and the canonical values are effect-observed
(the emitted label/noun, not a call-site proxy — WBlabel/WBnoun prove it). No new reach hole.

## RESIDUALS

- **R-a (unchanged from r2, non-blocking): PLR0911 on `verify`.** A faithful uniform-deny `verify`
  has ~10 returns; PLR0911 (threshold 6) is enabled repo-wide. r3 converted this into DOCUMENTED
  BUILDER GUIDANCE (a docstring note in the verify stub: collapse the deny-returns OR a scoped
  `# noqa`, do not distort logic). NOT a contract defect — the contract pins deny BEHAVIOUR, not
  return-count. I did NOT re-run the ruff leg (r3 changed no production logic vs r2, only docstrings,
  so the lint situation is identical to r2's already-adjudicated finding); flagged honestly as an
  un-re-run bound. The builder must apply the documented resolution.
- **NOTE (not a finding, repeated from SUMMARY for the builder): use the r3 strings.** The builder
  must implement `_query` with `noun="principal key query"` / `label="principal.key.query.rejected"`
  (the r3 maps + docstrings), NOT adversary-49-2's *suggested* underscore variant
  `principal_key.query.rejected` / `principal_key query`. My 762/0 reference used the r3 strings;
  the r2 suggestion would fail the attribution pin (@7093) exactly as WBlabel does.

---

## VERDICT

**CONTRACT SUFFICIENT.**

The r3 map registration (`4d3e483`, #353) CLOSES adversary-49-2's sole blocker. The load-bearing
receipt r2 could not produce now exists: a CORRECT reference build — with `PrincipalKeyStore._query`
carrying the exact canonical strings the r3 maps register — is **762 passed / 0 failed** across all 4
packet-49 files AND the full `test_retry_seam.py`, which is the gate the builder actually runs. No new
pin is RED on a correct build (no C-DEF). The new registration is DISCRIMINATING, not a rubber stamp:
a wrong label, a wrong noun, or a missing map entry are each CAUGHT for the right reason, with the
missing-entry case reproducing r2's exact failure. The r3 change did not weaken the r1/r2 pins
(#206 / verbatim `list-keys` / revoked-ignored verify all still CAUGHT). Every probe carries a passing
positive control, so no CAUGHT is a probe firing for the wrong reason.

The lead may spawn the builder on this contract. The one thing the builder MUST get right — and which
the contract now teaches in three places (the two maps, the `_query` stub docstring, and pin-17c) — is
the canonical `noun="principal key query"` / `label="principal.key.query.rejected"`.

**Graded: 4d3e483 · HEAD-at-report: 4d3e483 · SAME (0 behind).**

---

## APPENDIX-A — the r3 reference-build delta (vs adversary-49-2's APPENDIX-A)

I reused adversary-49-2's reference-build script (`/tmp/adv49_2_build_reference.py`, pasted in full in
that report's APPENDIX-A) VERBATIM except for ONE load-bearing line — the `_query` seam's canonical
strings, changed to match the r3 maps:

```diff
# principal_keys.py, inside PrincipalKeyStore._query -> run_query(...)
-            noun="principal_key query", label="principal_key.query.rejected",
+            noun="principal key query", label="principal.key.query.rejected",
```

The full r3 script lives at `/tmp/adv49_3_build_reference.py` (disposable scratch); it is
adversary-49-2's script with that single substitution + the default ROOT flipped to `/tmp/adv49_3_ref`.
Applied to the fresh scratch copy of HEAD `4d3e483`; built `_query` verified at `principal_keys.py:373`:
`noun="principal key query", label="principal.key.query.rejected"`.

## APPENDIX-B — the r3 wrong-build mutator (`/tmp/adv49_3_mutate.py`)

Reads the CORRECT reference from `/tmp/adv49_3_snap`, applies ONE named mutation into `/tmp/adv49_3_ref`.
The 6 mutations (exact-string replaces; a missing anchor is a LOUD `SystemExit`):

```python
# Task 2 (discrimination):
WBlabel   : principal_keys.py  label="principal.key.query.rejected" -> label="principal_key.rejected"
WBnoun    : principal_keys.py  noun="principal key query"           -> noun="principal keys"
WBmapdrop : tests/test_retry_seam.py  DELETE both '"PrincipalKeyStore": ...' map entries
            (_query left correct — reproduces r2 FINDING 1's exact state)
# Task 3 (regression):
WB206     : principal_keys.py  get_by_email(str(key_row["p_email"])) -> get_by_email("alice@example.com")
WBF4a     : principals.py      print(f"{sanitise_line(k.name)}\t{flag}") -> print(f"{k.name}\t{flag}")
WBrevoked : principal_keys.py  DELETE the revoked_at deny block (revoked key still verifies)
```

## APPENDIX-C — the driver (`/tmp/adv49_3_driver.sh`)

Runs a POSITIVE-CONTROL leg (correct build → every target pin passes), then each WB (restore → mutate →
run target pin → classify CAUGHT vs WAVED-THROUGH → restore). Final result (all controls PASS, all 6
wrong builds CAUGHT):

```
CTRL: attrib=pass mapevent=pass 206=pass listkeys=pass revoked=pass
WBlabel:   attrib=FAILED  mapevent=FAILED
WBnoun:    mapnoun=FAILED
WBmapdrop: mapevent=FAILED  attrib=FAILED (KeyError 'PrincipalKeyStore')
WB206:     FAILED
WBF4a:     FAILED
WBrevoked: FAILED
```

Store: spike-surreal `ws://127.0.0.1:18000`. Provenance re-asserted post-build:
`loremaster.__file__ = /tmp/adv49_3_ref/loremaster/loremaster/__init__.py`.
