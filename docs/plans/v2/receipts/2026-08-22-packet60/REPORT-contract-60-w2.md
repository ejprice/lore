# REPORT-contract-60-w2 — packet 60 wave 2 CONTRACT (the `lore-adm` keep CLI verbs)

brief-base v14 read
brief project v7 read

- **state:** done-with-deviations (contract + stubs landed; all gates green; 3 flags for the lead)
- **deviation 1:** `_dispatch_keep`'s catch tuple ADDS `SurrealStoreError` to the brief's stated
  set `{KeepStoreError, KeeperLockoutError, SurrealConnectionError, ValueError}` — reasoned below
  (§Deviations). Without it, a typo'd `--keep`/`--rank` crashes instead of exiting 1.
- **deviation 2:** the brief's LOAD-BEARING `safe_str` pin has NO bite in wave 2 — no keep verb
  renders stored free text (create-keep prints only the bare keep id; add/remove/set-rank are
  silent). Flagged, NOT faked into a decoration pin (§Flags F1).
- **Packages considered:** none — the CLI reuses the existing `argparse` framework + the wave-1
  `KeepStore`; no new mechanism specified.
- **Reuse ledger:** 1 new reusable symbol (`build_keep_store`), dispositioned HAND-ROLLED (the keep
  sibling of `build_principal_store`/`build_principal_key_store`); full table in §Reuse ledger.
- **Graded:** n/a — this is contract authoring, not an audit of another's artifact. All RED/GREEN
  receipts below are scoped to HEAD `ea03ea6` + the two uncommitted files (`principals.py`,
  `test_keeps_cli.py`).
- **decisions-needed:** (F1) accept `safe_str` as N/A for wave 2, or add a listing verb / echo?
  (F2) `dm --name` — forbid vs ignore (design says "forbids/ignores", ambiguous — left UNPINNED).
  (F3) Fork-A §A flag re-surfaced: keepership is a FIELD LINK not a `keeps` edge (already ruled;
  noted for continuity).
- **receipts:** RED/GREEN → §RED/GREEN; gate tails → §Gates; discrimination self-audit → §Fixtures;
  satisfiability → §Satisfiability; anti-patterns → §Anti-patterns.

---

## What wave 2 builds (the surface this contract pins)

Four FLAT subcommands added to the EXISTING `lore-adm` parser (`loremaster.principals:main`), routed
to the wave-1 `KeepStore` (committed `efccdc8`) through a distinct handler table + dispatch:

    create-keep --type {project,team,session,dm} [--name <label>] --keeper <email>   # prints the keep id
    add-household    --keep <id> --member <email>                                     # silent (idempotent)
    remove-household --keep <id> --member <email>                                     # silent; refuses the keeper
    set-rank         --keep <id> --member <email> --rank <rank>                       # silent (trivial today)

Plus `build_keep_store(config) -> KeepStore` (sibling of `build_principal_store`).

**Files touched:**
- `loremaster/tests/test_keeps_cli.py` — NEW, the contract (39 pins).
- `loremaster/loremaster/principals.py` — STUBS added: `build_keep_store` (raises), the four
  `_cmd_*` keep handlers (raise), `_KEEP_VERB_HANDLERS`, `_KeepVerbHandler` type, the parser entries,
  and the REAL `_dispatch_keep` + the `_dispatch` keep branch. `_KEEP_TYPES` imported from
  `surreal_schema`; `KeepStore` imported under `TYPE_CHECKING` (keeps.py imports this module — a
  top-level import is a cycle).

**DO-NOT-TOUCH respected:** `keeps.py`, the schema slice, and the 9 existing principal/key verbs'
behavior are untouched. `_dispatch` was minimally restructured (config-load moved above a new keep
branch) so `_require_config`'s missing-`--config` `SystemExit` still fires for every verb; the 9
existing handlers' signatures/bodies are byte-unchanged (a SEPARATE keep dispatch table + signature,
not a widening of the shared `_VerbHandler`).

## Placement decision (contract-phase, per design §6)

Design §6 left module layout to "the lead/contract author". The brief RULED it: flat verbs on the
existing `lore-adm` parser (not a `lore-adm keep …` subcommand group, not a second console entry).
I implemented that. Keep verbs use a **separate** `_KEEP_VERB_HANDLERS` dict with signature
`(args, keep_store)` — NOT the shared `(args, principal_store, key_store)` — because keep verbs route
through `KeepStore` (which COMPOSES its own `PrincipalStore` for email resolution) and need neither
the standalone principal store nor the key store. This adds ZERO churn to the 9 existing handlers.

## Store lifecycle (why `_dispatch_keep` readies a `PrincipalStore` first)

`KeepStore.ensure_ready()` applies the keep slice, whose `member_of` relation edge is
`ENFORCED IN principal OUT keep` — so the `principal` table must exist FIRST (wave-1 `keep_env`
fixture + the `KeepStore.ensure_ready` docstring, keeps.py). `KeepStore` composes a `PrincipalStore`
but does NOT ready it. So `_dispatch_keep` builds+readies a `PrincipalStore` before the keep slice.
This also makes an unknown-keeper create-keep resolve cleanly to `None` (→ `KeepStoreError` → exit 1)
instead of erroring on an absent table.

---

## RED / GREEN (at HEAD `ea03ea6` + the two uncommitted files)

`uv run pytest -n auto tests/test_keeps_cli.py` → **19 failed, 20 passed** (5.10s). All 19 REDs fail
BEHAVIOURALLY — the exception is `NotImplementedError` from the `build_keep_store` stub (58 traceback
mentions of `NotImplementedError`, tallied; zero collection/import errors). Never an ImportError.

**20 GREEN at stub (offline structural pins — the parser is real in the stub):**
- `TestKeepParserSurface` (18): every verb recognised [4], `--type` accepts every `_KEEP_TYPES`
  value [4], `--type` rejects an out-of-domain value [1], each verb's missing-required-arg →
  `SystemExit` [9].
- `TestBuildKeepStoreFactory::test_the_cli_routes_through_build_keep_store` [1] — AST scan finds the
  `build_keep_store` call in `_dispatch_keep`.
- `TestKeepVerbErrorPaths::test_a_keep_verb_without_config_is_a_loud_systemexit` [1] — shared
  `_require_config`.

**19 RED-by-design at stub (behavioural + factory pins — the builder greens them):**
- `TestBuildKeepStoreFactory::test_build_keep_store_resolves_config_coordinates` [1].
- `TestKeepCliCredsFree::…runs_with_no_anthropic_key_set` [1].
- `TestCreateKeepPrintsId` [2] — prints a resolvable id; the printed id feeds add-household.
- `TestKeepVerbsExecuteDirectly` [6] — add (at contributor); two distinct members; idempotent re-add;
  remove non-keeper; remove refuses keeper (exit 1 + stderr); set-rank runs.
- `TestCreateKeepPerTypeNameRule` [7] — without-name rejected [project, team]; without-name works
  [session, dm]; with-name works [project, team, session].
- `TestKeepVerbErrorPaths` [2] — unknown keeper → exit 1 + stderr; add-household to a nonexistent
  keep → exit 1 + stderr.

## Gates

- **ruff** (`uv run ruff check .`): `All checks passed!`
- **mypy** (`./scripts/typecheck.sh`): every member OK — `loremaster OK (222 source files)`,
  lorerunes/lorescribe/loresigil/skills/scripts/docs all OK, shellcheck OK. (Stubs are
  signature-complete, as in wave 1.)
- **existing suite** (`tests/test_principals_cli.py`): **45 passed** — my `principals.py` edits did
  not break the 9 existing verbs' contract.
- **retry-seam pin** (`tests/test_retry_seam.py`): **663 passed** — see §Anti-patterns.

---

## Fixtures-discriminate self-audit ("what WRONG build passes this?") — per load-bearing pin

- **create-keep prints a resolvable id.** Prints nothing → `len(lines)==1` reds. Prints the wrong id
  → `get_keep` returns None reds. Wrong type/name → type/name asserts red. Wrong keeper → `keeper_id
  in keeper.id` reds. ⚠ The `EXACTLY ONE LINE` assertion ALSO forbids create-keep echoing any extra
  (un-sanitised) free-text line beside the id — this is what closes the F1 gap structurally.
- **per-type `--name` rule.** A build that IGNORES the rule (always creates) → `[project,team]
  without-name` reds on BOTH rc!=0 and "no keep created". A build that REQUIRES name for all types →
  `[session,dm] without-name` reds (helper asserts rc==0). The `with-name works` control ensures the
  rejection is about the MISSING name, not the type. Uses a DIFFERENT `--type` per case (project /
  team / session / dm), so no single-value monoculture.
- **add-household adds / idempotent.** `two_different_members` (keeper+2=3 distinct) is the small-N
  control so `len()` ≠ the naive "store only writes one edge": a build that no-ops add reds (member
  absent, count wrong); a re-add that wrote a 2nd edge → `member_edges==1` reds; a re-add that raised
  → rc!=0 reds.
- **remove refuses the keeper.** A build that removed the keeper → `keeper still present` reds. A
  build that exited 0 → `rc==1` reds. Positive control: `remove non-keeper` proves a legal removal
  succeeds (so the refusal isn't "remove never works").
- **error paths.** Unknown keeper and ghost keep both assert `rc==1` AND a `lore-adm:` stderr prefix
  — a build that crashes (uncaught) errors instead of returning 1 (reds); a build that swallows the
  error → rc!=1 reds. The ghost-keep pin specifically forces catching the ENFORCED store rejection.
- **creds-free.** A build using `load_config` (eager Anthropic) → `KeyError` on the unset var → rc!=0
  reds. Behavioural (reaches the store) so not vacuous.
- **factory coordinates.** A build resolving the wrong database/accessor reds. **AST routing.** A
  build hand-rolling `KeepStore(...)` at the call site (no `build_keep_store` call) reds.

## Satisfiability plan (for the adversary's 0-failed reference build)

A minimal correct CLI impl discharges all 39 pins:
1. `build_keep_store(config)` — lazy `from loremaster.keeps import KeepStore`; `return KeepStore(url=
   config.surreal.url, namespace=config.surreal.namespace, database=config.effective_surreal_database,
   user=resolve_config_value(config.surreal.user_env), password=resolve_secret(config.surreal.password_env))`
   (mirror `build_principal_key_store` verbatim).
2. `_cmd_create_keep` — if `args.type in {"project","team"}` and `args.name is None`: `raise
   ValueError(...)` (laundered by `_dispatch_keep` → rc 1); else `keep = await keep_store.create_keep(
   keeper_email=args.keeper, type=args.type, name=args.name)`; `print(keep.id)`; `return 0`.
3. `_cmd_add_household` / `_cmd_remove_household` / `_cmd_set_rank` — one-line delegations to the
   matching `KeepStore` method, `return 0`.
4. **`_dispatch_keep` is ALREADY correct in the stub** (readies principal→keep, catches
   `{KeepStoreError, SurrealStoreError, SurrealConnectionError, ValueError}`) — the builder greens
   only `build_keep_store` + the four handler bodies. The catch tuple is load-bearing for the
   ghost-keep pin; leaving it intact is part of satisfiability.

I verified each pin against this reference design by hand (§Fixtures) and against the wave-1 store
contract's proven behaviors (nameless-keep round-trip, ENFORCED-refuses-ghost-endpoint, idempotent
add, keeper-lockout). The wave-1 suite (`tests/test_keeps_store.py`) already GREEN on those behaviors
is the corroboration that KeepStore's half holds.

## Anti-patterns (adversary + cold-audit hunt list) — confirmed clear

- **No retry-seam gap.** The CLI makes NO direct SDK call — the only `AsyncSurreal`/`.signin` sites in
  `principals.py` are the pre-existing wave-48 `PrincipalStore._ensure_connection` (lines 277/280);
  my additions route through `KeepStore`/`PrincipalStore` objects whose SDK use lives in their own
  `_query`/`_ensure_connection` (already registered). `build_keep_store` only constructs. No new
  store, no new `_query` method → `test_retry_seam.py` needs no new registration and stays **663
  passed**.
- **Stub-comment minimality (finding #398).** Every stub carries a short `STUB (contract-60-w2)`
  docstring that describes ONLY what the builder will do (future tense) — none ASSERTS a false claim
  about the current code. ⚠ **Builder must reframe/remove the four `STUB (contract-60-w2)` docstrings
  + `build_keep_store`'s** when greening (retire the "STUB"/"the builder greens" prose), exactly the
  #398 discipline. They are deliberately easy to correct (no stale structural claims to unwind).
- **No `--execute`/dry-run trace.** My additions introduce no such string; `test_principals_cli.py`'s
  `test_source_contains_no_execute_flag_or_dry_run` (which scans all of `principals.py`, now including
  my code) stays green — not duplicated here.
- **Fixtures discriminate** — §Fixtures above (≥2 members, named+dm pair, per-type both ways,
  keeper-lockout both ways, DIFFERENT `--type` per case).

## Deviations (disclosed)

**D1 — `_dispatch_keep` catches `SurrealStoreError` (beyond the brief's stated catch set).** The
brief said "mirror `_dispatch`'s catch" with `{KeepStoreError, KeeperLockoutError, SurrealConnectionError,
ValueError}`. But `_dispatch` catches `PrincipalStoreError`, and `PrincipalStore.create`/`set_subject`
WRAP engine rejections as `PrincipalStoreError`. **`KeepStore` does NOT wrap** — a bad type / ghost
endpoint / bad rank surfaces as raw `SurrealStoreError` (see wave-1 `test_a_REJECTED_create_keep…`
which catches a bare `Exception`, not `KeepStoreError`). So faithfully mirroring `_dispatch`'s
loud-on-failure INTENT for a non-wrapping store requires catching `SurrealStoreError`; otherwise a
common operator error — a typo'd `--keep` refused by ENFORCED, a wrong `--rank` refused by the ASSERT
— crashes the CLI instead of exiting 1. The `add-household to a nonexistent keep` pin enforces this.
This is a design decision within contract-author scope; flagged for a clean countermand.

## Flags / decisions-needed

**F1 — `safe_str` on echoed free text has NO bite in wave 2 (brief LOAD-BEARING pin, surface
mismatch).** The four verbs are silent-on-success EXCEPT create-keep, which prints the BARE keep id
(a ULID — not free text; the mint-key-prints-credential precedent, one line). No verb renders stored
free text (name/email) on the success path; there is no `list-household`/`list-keeps` verb in wave 2.
So the P8d "rendered stored free text" law simply does not apply — and the `EXACTLY ONE LINE` pin
structurally forbids create-keep smuggling an un-sanitised line beside the id. I did NOT write a
`safe_str` hostile-fixture pin, because a pin over a surface that doesn't echo free text is
decoration (banned). **Options for the lead:** (a) accept `safe_str` as N/A for wave 2 (my
recommendation — the law re-applies the moment a listing verb lands, with its own hostile-fixture
pins then); (b) add a `list-household`/`list-keeps` verb now (scope add — operator's call); (c) have
create-keep echo a sanitised confirmation (violates unix-silence + complicates the "print the id"
pin). This is a brief-vs-surface mismatch, surfaced rather than silently dropped (RIDER-IS-PART-OF-
THE-RULING discipline).

**F2 — `dm --name` behavior is genuinely ambiguous, left UNPINNED.** Design Fork B / the brief say
"forbids/ignores it for dm" — two readings that produce different code (reject a `dm --name` vs
silently drop it and store `name=None`). The brief's REQUIRED per-type pins are only "dm WITHOUT
`--name` works" (pinned) and "project WITHOUT `--name` rejected" (pinned). `dm WITH --name` is not
required and is ambiguous, so I did NOT pin it either way (pinning would over-constrain toward one
unruled reading). The reference build may do either. **Recommendation:** ignore-and-store-None (a
`dm` keep is defined by its 2 members; a stray `--name` is harmless), but this is the lead's/operator's
ruling. Picking silently is the defect; picking with the alternative written down is not.

**F3 — Fork-A continuity note (not a new fork).** Keepership is a `keep.keeper` FIELD LINK, not a
`keeps` edge (design §A, already ruled by the sidecar with a countermand condition). The contract's
`keep.keeper_id`-is-the-creator pin reflects that ruling; noted only so a reader of this report sees
the §A divergence is intentional, not an oversight.

## Task / comms

- Task `68597fc8025d4065bdf6b79f83d82bb0` claimed + in_progress (→ done on close).
- Registered on `lore_comms` as `contract-60-w2` (session pkt60, role contract).
