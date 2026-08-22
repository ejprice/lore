# REPORT-adversary-60-w2 — CONTRACT-ADVERSARY, packet 60 wave 2 (`lore-adm` keep CLI)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — one wrong build survives the whole contract (below).
- **state:** done — satisfiability + wrong-build sweep run empirically against a reference build in a provenance-asserted scratch copy.
- **P1 headline:** a **NO-OP `_cmd_set_rank`** (`return 0`, never calling `KeepStore.set_rank`) passes the ENTIRE CLI contract **40/40** — because the only legal rank (`contributor`) EQUALS the DEFAULT rank, so a set-rank that does nothing is indistinguishable from a correct one. `set-rank` is the sole write verb with NO error-path pin.
- **MISSING PIN (blocker):** `test_set_rank_with_an_unruled_rank_is_loud_and_nonzero` — `set-rank --rank <bogus>` must exit 1 + `lore-adm:` stderr. Mutation-proven: RED on the no-op build, GREEN (2/2, with positive control) on the reference build.
- **CONFIRMED SATISFIABLE:** reference CLI build → `test_keeps_cli.py` **40 passed / 0 failed**; full `test_keeps_cli.py + test_keeps_store.py` **83 passed / 0 failed** (ruff clean). Provenance: `loremaster.__file__ = /tmp/pkt60w2-adv/loremaster/loremaster/__init__.py`.
- **Wrong builds CAUGHT (contract is otherwise strong):** WB2 dm-`--name`-ignored ✓, WB3 non-teaching-dm-message ✓, WB4 per-type monoculture ✓, WB5 prints-nothing ✓, WB6 extra-line ✓, WB10 Q2b-wrap-reverted (D1 coupling) ✓.
- **Packages considered:** none — no new mechanism specified (the CLI reuses `argparse` + the wave-1 `KeepStore`).
- **Reuse ledger:** none — I introduced NO production symbol; my probes are scratch-only (a 2-test `TestAdversarySetRankErrorPath` in a scratch copy of the contract, pasted verbatim in §Instruments).
- **Graded:** `5b7180c` · HEAD-at-report `5b7180c` · SAME. The graded artifact is the WORKING-TREE contract (`loremaster/tests/test_keeps_cli.py` UNTRACKED + `loremaster/loremaster/principals.py` MODIFIED) on top of `5b7180c`; the Q2b wrap is committed (`e019477`).
- **decisions-needed:** the blocker pin routes back to CONTRACT (add it before builder). Two LOW residuals for the lead's call (§Residuals R1/R2) + one wave-1 store observation (R3).
- **receipts:** satisfiability → §Satisfiability; P1 wrong-build sweep → §P1; quantifier table → §P1b; reach table → §P1c; blocker mutation proof → §Blocker; residuals → §Residuals; probe source → §Instruments.

---

## Satisfiability (do-first, 0-failed against a known-correct reference build)

Built the reference CLI in `./scripts/scratch_copy.sh /tmp/pkt60w2-adv` (provenance-asserting, #140). The
copy's own gate passed and I re-printed the receipt:

```
scratch copy READY: /tmp/pkt60w2-adv
  loremaster  -> /tmp/pkt60w2-adv/loremaster/loremaster/__init__.py
PROVENANCE loremaster.__file__ = /tmp/pkt60w2-adv/loremaster/loremaster/__init__.py
```

Reference build (the 5 stubs greened per REPORT-contract-60-w2b §Satisfiability):
- `build_keep_store` — lazy `from loremaster.keeps import KeepStore`; `return KeepStore(url=…, namespace=…, database=config.effective_surreal_database, user=resolve_config_value(...), password=resolve_secret(...))` (mirror `build_principal_store`).
- `_cmd_create_keep` — per-`type` `--name` rule: `project`/`team` require (`raise ValueError`), `dm` with a name rejects (`raise ValueError("--name is not valid for --type dm …")`), else `create_keep(...)` + `print(keep.id)`.
- `_cmd_add_household` / `_cmd_remove_household` / `_cmd_set_rank` — one-line delegations to the matching `KeepStore` method, `return 0`.

Results (spike TEST store `ws://127.0.0.1:18000`, per-test unique DB):

```
cd /tmp/pkt60w2-adv/loremaster && uv run pytest -n auto tests/test_keeps_cli.py
  64 workers [40 items] ........................................  40 passed in 5.87s
uv run ruff check loremaster/loremaster/principals.py            All checks passed!
# full store+CLI on the restored reference (excl. my probe class):
uv run pytest -n auto tests/test_keeps_cli.py tests/test_keeps_store.py -k "not TestAdversarySetRankErrorPath"
  64 workers [83 items] ...........................................................................  83 passed in 6.64s
```

The contract is SATISFIABLE together, and ruff-clean. The 83 matches REPORT-contract-60-w2b's number
(spot-check: the committed Q2b store wrap holds).

---

## P1 — build wrong implementations, see what the contract waves through

Each wrong build was patched into the scratch reference and run against the REAL contract. Every
negative is paired with the reference build passing (the positive control = the 40/0 above).

| # | wrong build | contract's response | verdict |
|---|---|---|---|
| **WB1** | `_cmd_set_rank` is a NO-OP (`return 0`, never calls `set_rank`) | **40 passed / 0 failed — SURVIVES** | **BLOCKER (§Blocker)** |
| WB2 | `_cmd_create_keep` IGNORES `--name` for `dm` (creates keep, rc 0) | `test_create_keep_dm_with_a_name_is_rejected` RED (`assert 0 == 1`) | caught ✓ |
| WB3 | dm reject with a NON-teaching message (`"invalid option combination"`) | same test RED on `"name" in lowered` (`'name' in 'lore-adm: invalid option combination'` false) | caught ✓ |
| WB4 | per-type monoculture — only `project` requires `--name` (not `team`) | `test_create_keep_without_name_is_rejected_for_name_requiring_types[team]` RED (`assert 0 != 0`) | caught ✓ |
| WB5 | `create-keep` prints NOTHING | `test_create_keep_prints_a_resolvable_keep_id` RED (`len 0 != 1`) + `test_the_printed_keep_id_feeds_add_household` RED | caught ✓ |
| WB6 | `create-keep` prints an EXTRA line beside the id | `test_create_keep_prints_a_resolvable_keep_id` RED (`assert 2 == 1`) | caught ✓ |
| WB10 | Q2b wrap REVERTED in `keeps.add_household_member` (leak raw `SurrealStoreError`) | `test_add_household_to_a_nonexistent_keep_is_loud_and_nonzero` RED (raw `SurrealStoreError` escapes `_dispatch_keep`'s catch → CLI crash) | caught ✓ (D1↔Q2b coupling REAL) |

**The one that survives is WB1.** Everything else the contract catches, discriminatingly.

### Brief items answered without a separate build (reasoned, grounded in the runs above)

- **Item 1 (parser-level dm reject, exit 2):** the dm pin asserts `rc == 1` (dispatch-level). A build
  rejecting at the parser (SystemExit 2) either raises out of `main().parse_args` or out of the handler
  → `_run_cli` re-raises → the test ERRORS (red). `rc == 1` (not `rc != 0`) is the right, tight assertion.
- **Item 6 (creds-free):** `test_the_keep_cli_runs_with_no_anthropic_key_set` PASSED on the reference
  (part of 40/0). A build using `load_config` (eager Anthropic key) would raise on the deleted
  `_ANTHROPIC_ENV` var at config-load → keep never created → pin RED. Config-load lives in the REAL
  (non-builder) `_dispatch`; the pin nonetheless guards it. Not separately built — the discrimination
  is structural and the config-load site is not builder territory.
- **Item 9 (NO over-reach):** confirmed — the contract pins NO listing verb, NO `safe_str` decoration
  (create-keep prints only the bare ULID id; the F1 "N/A" was accepted by the lead and the
  EXACTLY-ONE-LINE pin closes the free-text smuggling gap structurally — WB6 proves it), and NO
  DM 2-member cap (packet 63). No pin-over-a-nonexistent-surface defect found.

---

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-known-failure-mode)

| invariant | classification | receipt |
|---|---|---|
| per-`type` `--name` rule holds ∀ type ∈ {project, team, session, dm} | ∀-over-the-4-types (8 cells all pinned) | WB4 door-build: a `project`-only monoculture is caught by `[team]`. project WITHOUT→reject, team WITHOUT→reject, session/dm WITHOUT→ok, project/team/session WITH→ok, dm WITH→reject — every cell has a pin. Bound: the ∀ is over the *hand-listed 4 names*, not derived from `_KEEP_TYPES` (§P1c R1). |
| create-keep prints exactly the resolvable id (nothing more, nothing less) | ∀ (len==1 + resolves + right type/name/keeper) | WB5 (nothing) and WB6 (extra line) both RED; positive control `test_the_printed_keep_id_feeds_add_household`. |
| every WRITE verb is LOUD on a store/domain rejection | **GUARDED — hole on `set-rank`** | create-keep (unknown keeper) ✓, add-household (ghost keep) ✓, remove-household (keeper lockout) ✓. **set-rank has NO error-path pin** → the guarded door WB1 walks through. This is the blocker: the invariant is stated for the debugged verbs, not ∀ over the four write verbs. |
| add-household is idempotent (re-add ⇒ one edge) | ∀ (≥2 distinct members + re-add) | `test_add_household_two_different_members_both_land` (keeper+2=3) is the small-N control so `len()`≠naive-1; a 2nd-edge build reds `member_edges==1`. (Real bite is on KeepStore, already GREEN; at the CLI it proves the handler delegates.) |
| remove-household removes the named member, refuses the keeper | ∀ both ways | non-keeper removal + positive control (keeper untouched); keeper refusal (rc 1 + keeper still present). |
| the keep CLI resolves creds-free (no Anthropic key) | ∀ (reaches store with key unset) | reference PASS; a `load_config` build reds. |

---

## P1c — REACH TABLE (guards/scans the contract introduces or relies on)

Legs run: **empirical** where the guard is in-tree and mutable (routing AST pin, per-type coverage);
**construction-inspection** for the store-wrap coupling (verified via WB10 instead).

| instrument | reach DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|
| `test_the_cli_routes_through_build_keep_store` (AST scan for a CALL to `build_keep_store`) | hand-checks ONE symbol name is called | n/a (single symbol) | effect (a real `ast.Call` walk) | **ADEQUATE, non-blocking.** It only proves `build_keep_store` is called *somewhere* (in the REAL `_dispatch_keep`), NOT that no handler hand-rolls `KeepStore(...)`. But the 4 handlers receive only `(args, keep_store)` — **no `config`/coords** — so a hand-rolled `KeepStore(...)` at a handler is structurally un-buildable. The reach gap is unreachable through the real entry point (P3). |
| per-`type` `--name` rule coverage (parametrized cells) | **hand-list** `["project","team"]` / `["session","dm"]` / `["project","team","session"]` — NOT derived from `_KEEP_TYPES` | **NO** — a NEW `_KEEP_TYPES` member joins the DERIVED `test_create_keep_accepts_every_schema_type` (parse) but its NAME-policy stays unpinned | effect | **LOW residual R1.** Bound: a new keep type = a schema change = a new packet/contract; the name-policy per type is a design decision not derivable from `_KEEP_TYPES` alone. Recommended (not blocker) pin in R1. |
| Q2b store-wrap → CLI catch (`_dispatch_keep` catches `KeepStoreError`, not raw `SurrealStoreError`) | the CLI relies on the committed wrap covering EVERY KeepStore write path | checked in `test_keeps_store.py` (the DERIVED write-path coverage pin, per w2b) | effect (WB10: reverting the wrap makes the CLI crash) | **SOUND.** The CLI's ghost-keep pin genuinely depends on the wrap (WB10 RED). The store-side reach (all 4 write paths wrap) is the store contract's job, already committed + verified. |

No routing-not-sharing / two-sources-of-truth defect: `build_keep_store` is the single construction seam,
called once in the real `_dispatch_keep`; handlers cannot fork it (no coords).

---

## Blocker — MISSING PIN (mutation-proven both directions)

**The wrong build:** `_cmd_set_rank` greened as a no-op —

```python
async def _cmd_set_rank(args, keep_store):
    return 0   # never calls KeepStore.set_rank
```

**Why it survives:** the only legal rank is `contributor`, which is ALSO the DEFAULT rank written by
`add_household_member`. So `test_set_rank_to_contributor_runs` asserts `member_edges[0].rank ==
_KEEP_RANK_CONTRIBUTOR` — TRUE from the default, whether or not `set_rank` ever ran. There is no
error-path pin for set-rank (unlike every other write verb). Result: **40 passed / 0 failed** on the
no-op build.

**The pin that should exist** (add to `test_keeps_cli.py`; the CLI-level twin of the store's
`test_set_rank_wraps_an_unruled_rank_engine_rejection`, mirroring `test_add_household_to_a_nonexistent_keep`):

```python
class TestAdversarySetRankErrorPath:
    async def test_set_rank_with_an_unruled_rank_is_loud_and_nonzero(self, cli_env, capsys):
        await _add(cli_env, _KEEPER); await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="rank")
        await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        capsys.readouterr()
        rc = await _run_cli(cli_env.argv("set-rank", "--keep", keep_id, "--member", _MEMBER, "--rank", "overlord"))
        assert rc == 1, "set-rank with an unruled rank must be a loud non-zero exit (KeepStoreError laundered)"
        assert capsys.readouterr().err.startswith(f"{p_module._CLI_PROG}:")
```

**Mutation proof (real output):**

```
# vs the NO-OP build:
FAILED …TestAdversarySetRankErrorPath::test_set_rank_with_an_unruled_rank_is_loud_and_nonzero
E   AssertionError: set-rank with an unruled rank must be a loud non-zero exit …
E   assert 0 == 1
1 failed, 1 passed          # positive control (legal rank → rc 0) passes
# vs the REFERENCE build:
2 passed in 5.08s           # both the reject pin AND the positive control green
```

The pin discriminates (RED on the no-op) AND is satisfiable (GREEN on the reference), and it restores
the loud-on-failure symmetry every other write verb already has. The positive control is the
already-present `test_set_rank_to_contributor_runs` (legal rank → rc 0), so only the negative pin is
missing. **This is a wave-2 CLI pin** (set-rank verb → exit 1 + stderr), not a store pin.

---

## Fixture-discrimination verdicts (P2)

- **≥2 members / named+dm pair / per-type both ways — GOOD.** `test_add_household_two_different_members_both_land` (keeper+2=3 distinct) defeats the `len()`≡`sum()` small-N trap; the per-type tests use a DIFFERENT `--type` per parametrize case (no monoculture) — WB4 empirically proved the coverage bites `team`, not just `project`.
- **The one non-discriminating fixture is the set-rank fixture** — `test_set_rank_to_contributor_runs` cannot tell a correct set-rank from a no-op, BY NATURE of the trivial 1-value domain (legal == default). That is the blocker above; the fix is a negative pin, not a fixture change.
- No arithmetic-alignment or parameter-monoculture trap found elsewhere.

---

## Residuals (each an INDIVIDUAL verdict)

- **R1 (LOW, reach) — per-type name-policy coverage is a hand-list, not derived from `_KEEP_TYPES`.** If a
  5th keep type is ever added to `_KEEP_TYPES`, `test_create_keep_accepts_every_schema_type` (derived)
  parse-accepts it, but NO pin asserts its `--name` policy (require/allow/forbid). Recommended
  (non-blocking) hardening: a pin asserting every `_KEEP_TYPES` value appears in the test's own
  name-policy map, failing CLOSED when the domain grows — the coverage-as-checked-variable form. Bound:
  a new type is a schema change (a future packet with its own contract), so this is defensive, not a
  live hole. Lead's call.
- **R2 (LOW, consistency) — the project/team-WITHOUT-`--name` reject does not assert a TEACHING stderr,
  and asserts `rc != 0` (not `rc == 1`).** The dm-WITH-`--name` pin asserts both `rc == 1` and a teaching
  `name`/`dm` message; the symmetric project/team reject asserts only `rc != 0` + no-keep. A build
  rejecting project/team with an empty/cryptic message passes (the `lore-adm:` prefix is structurally
  guaranteed by `_dispatch_keep`, but the *teaching quality* is unpinned). Not a surviving-wrong-build
  today (no natural exit-2 build for an app-layer rule), so LOW. Recommend tightening to match the dm
  pin for symmetry.
- **R3 (observation, wave-1 store scope — NOT a wave-2 CLI pin) — `remove-household` on a GHOST keep
  silently succeeds (rc 0).** `add-household` to a ghost keep is LOUD (ENFORCED refuses the RELATE,
  pinned), but `remove_household_member`'s `DELETE … WHERE` on a non-existent keep is a no-op (store ref
  §2) → returns `None` → rc 0. A typo'd `--keep` on remove is a silent success. This is wave-1
  `KeepStore` behavior (already shipped `efccdc8`), out of this contract's writable set — surfaced for
  the lead/operator, not pinned here. (Analogous to idempotent-add's benign no-op, so possibly
  intended; flagging per scope law, not asserting a defect.)

---

## Instruments (the probe source, pasted verbatim — brief-base §1)

My only built instrument is the blocker's proposed pin + its positive control, added to a SCRATCH copy
of the contract (`/tmp/pkt60w2-adv/loremaster/tests/test_keeps_cli.py`), never the repo tree:

```python
class TestAdversarySetRankErrorPath:
    async def test_set_rank_with_an_unruled_rank_is_loud_and_nonzero(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="rank")
        await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        capsys.readouterr()
        rc = await _run_cli(
            cli_env.argv("set-rank", "--keep", keep_id, "--member", _MEMBER, "--rank", "overlord")
        )
        assert rc == 1, "set-rank with an unruled rank must be a loud non-zero exit (KeepStoreError laundered)"
        err = capsys.readouterr().err
        assert err.startswith(f"{p_module._CLI_PROG}:"), (
            f"the store rejection must be laundered to a `lore-adm:` stderr line: {err!r}"
        )

    async def test_set_rank_with_the_legal_rank_still_succeeds(
        self, cli_env: _CliEnv, capsys: pytest.CaptureFixture[str]
    ) -> None:
        await _add(cli_env, _KEEPER)
        await _add(cli_env, _MEMBER)
        keep_id = await _create_keep(cli_env, capsys, keep_type="project", keeper=_KEEPER, name="rank2")
        await _run_cli(cli_env.argv("add-household", "--keep", keep_id, "--member", _MEMBER))
        rc = await _run_cli(
            cli_env.argv("set-rank", "--keep", keep_id, "--member", _MEMBER, "--rank", _KEEP_RANK_CONTRIBUTOR)
        )
        assert rc == 0
```

All wrong-build patches (WB1–WB10) were transient edits to `/tmp/pkt60w2-adv/…/principals.py` (and, for
WB10, `…/keeps.py`), each restored after its run; the final scratch state is the clean reference build.

---

## Store-law grounding (cited)

- `docs/reference/surrealdb-31-capabilities.md` §2 (DML): `DELETE … WHERE` of a non-matching row is a
  no-op (grounds R3); `CONTENT` write of an omitted `option<>` column decodes to NONE (grounds the
  nameless-keep round-trip create-keep relies on). §1.1: `member_of` is `OVERWRITE … ENFORCED` — the
  ghost-endpoint refusal WB10/`test_add_household_to_a_nonexistent_keep` leans on.
- Error hierarchy (via REPORT-contract-60-w2b §Store-law): `SurrealConnectionError` /
  `TxnContentionExhaustedError` subclass `SurrealStoreError`, so the Q2b wrap re-raises them FIRST —
  the reason WB10 (leak raw) crashes the CLI while the correct wrap exits 1.

## Task / comms

- Task `debc047b2b8942749c5e76f4c9f9faa6` claimed + in_progress (→ done on close).
- Registered on `lore_comms` as `adversary-60-w2` (session pkt60, role adversary).
- **Scratch `/tmp/pkt60w2-adv` NOT removed — `rm -rf` guardrail-DENIED** (identical to
  REPORT-contract-60-w2b's experience, 1 attempt). It is a disposable `scripts/scratch_copy.sh` rsync
  copy in `/tmp` (NOT a git worktree); final state is the clean reference build. Reclaim with
  `./scripts/scratch_copy.sh --force /tmp/pkt60w2-adv` or an operator `rm -rf`. Flagged so it is not
  silently abandoned.
