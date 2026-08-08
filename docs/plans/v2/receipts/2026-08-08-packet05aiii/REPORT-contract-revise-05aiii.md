# REPORT-contract-revise-05aiii — fold the two Fable rulings into the 05a-iii RED contract

brief-base v10 read
brief project v7 read

## Summary block
- **State:** done. Folded both ruled forks + the D8 nudge into the committed RED contract (770de57). Added **2 new CLI pins** (`TestDefaultCoordinateResolution`) + a minimal `_resolve_coordinate` stub seam; added the **#304 property-keying rider** as an inherited docstring note (Ruling 1); **confirmed D8** honesty (Ruling 3, no assertion change). No existing pin weakened; no production code greened.
- **Deviations (disclosed):**
  1. Added a `_ResolvedCoordinate` NamedTuple + `_resolve_coordinate(args, *, config_path=None)` stub SEAM to `comms_cli.py` — the contract needs a resolution seam to pin as a pure-resolution assertion (rider 2's "assert the resolved coordinate"). Minimal; `main` behaviour unchanged (C-counts stays RED).
  2. `test_comms_cli.py` now imports `_CANONICAL_CONFIG` from `test_config` (cross-test-module import is an existing idiom — `test_comms_status_age` already imports from `test_comms_schema`) — ONE IMPLEMENTATION for the valid-config shape, not a hand-rolled second copy.
- **Packages considered:** none — no external mechanism specified. The pinned default-resolution REUSES in-house `loremaster.config` (`SurrealConfig` + `effective_surreal_database` + `model_validate`), read at `config.py` — the ONE-IMPLEMENTATION (reuse-not-clone) half of the rule, never a hand-roll.
- **Graded:** authored + verified against `770de57` · HEAD-at-report `770de57` · SAME. (Verdict rendered on: my 2 new pins' behaviour; the rider-3 claim about `load_config`; D8's discrimination — all measured this session, spike-surreal `:18000`, `:18500` never touched.)
- **Decisions-needed (surfaced, none silently resolved):**
  1. **Config DISCOVERY for the production no-override path** is builder latitude — the ruling pinned the RESOLVER, not HOW `main` finds `lore.yaml` with no `--config`. Recommend consistency with lore's index CLI `--config` idiom (`test_cli.py`). NOT a blocking fork; flagged for the builder brief.
  2. The `_resolve_coordinate` seam shape (`config_path` param; `_ResolvedCoordinate(url,namespace,database)`) is a minimal contract commitment; the LOAD-BEARING property is "default reads the config coordinate + needs no Anthropic key." Note for the adversary/builder, not a fork.
- **Receipt pointers:** rulings folded §What changed · discrimination §Discriminating interrogations · rider-3 §Rider-3 verification · Ruling-1 instrument §Ruling 1 · gate counts §Gate counts · satisfiability+controls §Satisfiability receipt (script verbatim).

---

## Ground-truth reads (this session, `770de57`, lore-first)
- `loremaster/config.py`: `LoreConfig.anthropic: AnthropicConfig` is **REQUIRED** (no default, `LoreConfig` body — a `lore.yaml` with no `anthropic:` fails `model_validate`); `load_config` resolves `config.anthropic.api_key_env` **EAGERLY** via `resolve_secret` and re-raises a `ValueError` when the env var is unset (`load_config` try/except). `LoreConfig.model_validate` is the documented boot seam that **does NOT touch the environment** (`load_config` docstring). `SurrealConfig` resolves `url`/`namespace`/`database`(None→slug), creds by env-var NAME; `effective_surreal_database` = `surreal.database or project.slug`.
- `loremaster/agents.py`: the auto-flip lives in `AgentRegistry.touch` — an explicit `status` wins; a bare heartbeat flips `idle`→`active`; `input_required`/`active` stay. `AGENT_STATUSES` is the closed four-value domain; `_render_comms_fleet_row` (server.py) renders the `{status}` cell via `sanitise_line(row.status)` — the #304 latch.

## What changed (the two rulings + the D8 nudge, folded)

### Ruling 2 — comms_cli default = REUSE the server's `SurrealConfig` (2 new pins + stub seam)
- `loremaster/loremaster/comms_cli.py`: added `_ResolvedCoordinate(url, namespace, database)` + `_resolve_coordinate(args, *, config_path=None)`. Explicit `--url` wins; the DEFAULT path is documented to load the surreal block via the SHARED `SurrealConfig`+`effective_surreal_database` **env-free** (`model_validate` / surreal-only), **never `load_config`** (rider 3). STUB: explicit path returns the args coordinate; default path returns an EMPTY coordinate so the pins fail behaviourally. `main` unchanged.
- `loremaster/tests/test_comms_cli.py` `TestDefaultCoordinateResolution`:
  - **C-default-resolution** `test_no_override_resolves_the_config_surreal_coordinate` — RED. Fixture config points surreal at `:18000` (a fixture value; NO connection opened — never a live prod store, rider 2); asserts `resolved == (fixture url, ns, db)`.
  - **C-anthropic-independence** `test_default_resolution_does_not_require_an_anthropic_key` — RED. Fixture's `anthropic.api_key_env` names a GUARANTEED-UNSET var (`delenv`); asserts resolution still yields the surreal coordinate (rider 3).
  - Riders folded: (b) the no-hardcoded-`:18500` AST guard `test_source_never_hardcodes_the_production_coordinate` SURVIVES (verified GREEN over the modified `comms_cli.py`); every other CLI test keeps the explicit `--url` override to `:18000`.
- Module docstring: the open ESCALATION note → RESOLVED (ruling folded + the two new pins named).

### Ruling 1 — #304 age scope = input_required-only (RATIFIED) + property-keying rider (docstring note)
- `loremaster/tests/test_comms_status_age.py`: module FORK note → RESOLVED. Added the **rider as a class docstring on `TestFleetAgesTheDeclaration`** (inherited by the builder brief via the D7 pin): the build keys the age-render on the PROPERTY "this status LATCHES (wins over the idle→active auto-flip)", NOT a bare `== "input_required"` literal; NAMED RE-OPEN TRIGGER stated. No behavioural pin changed.

### Ruling 3 — D8 NONE-render honesty (CONFIRMED, no change)
- Added a confirmation docstring to `test_none_status_set_at_renders_unknown_not_a_fabricated_zero` naming the honest shape (`declared: unknown` / age-since-hb). The load-bearing `legacy_cell != fresh_cell` discrimination (NONE ≠ a just-declared 0s) already reddens the fabricate-zero trap; wording stays builder latitude. No assertion change.

## Ruling 1 — instrument choice (docstring note, and WHY not a new structural guard)
I chose the **docstring note** and added **no new structural tripwire**, for two reasons:
1. **A render-side structural guard is impossible at a single-member latch set.** Today `input_required` is the only status that wins over the auto-flip, so a property-keyed render and a `== "input_required"` render are behaviourally IDENTICAL for every current input — undiscriminable. The only render-side "guard" would be banning the literal, which is itself the enumerate-the-forbidden antipattern (a property-keyed build may legitimately reference `"input_required"` while COMPUTING the latch set).
2. **The named re-open trigger is ALREADY mechanical — adding one duplicates existing pins (ONE IMPLEMENTATION).** The trigger ("any status other than `input_required` made to win over the auto-flip") is guarded by `test_agent_registry.py::TestAgentStatusesConstant.test_agent_statuses_is_the_closed_four_value_domain` (reds on ANY new status → forces the "does it latch?" review) + `test_agent_registry.py::TestIdleAutoFlip` (`test_input_required_agent_does_not_auto_flip` + `test_idle_agent_auto_flips_to_active_with_no_explicit_status` pin the current winner-set). A newly-introduced latching status trips BOTH. So the trigger is not a hope; the docstring note points the builder at it.

This is the ruling's "(c)'s door documented not built" — input_required-only built, the latching-subset generalisation documented with a mechanical trigger.

## Rider-3 verification (which case is true — measured against config.py)
**Case: `load_config` DOES hard-require the Anthropic key → the pin is warranted.** Two independent reasons at `config.py`: (i) `LoreConfig.anthropic` is a REQUIRED field (a `lore.yaml` with no `anthropic:` block fails `model_validate`); (ii) `load_config` calls `resolve_secret(config.anthropic.api_key_env)` EAGERLY and re-raises `ValueError` when the var is unset. A creds-free read-only CLI routed through `load_config` would therefore fail boot in a stripped-env idle-gate hook. The fix the ruling names — load the surreal block WITHOUT the eager key — is satisfied by env-free `LoreConfig.model_validate` (or a surreal-only parse), and the RESOLUTION stays the shared `SurrealConfig`. C-anthropic-independence pins exactly this, and the control below shows a `load_config` build reddens it (`ValueError`).

## Discriminating interrogations ("what WRONG build still passes this?")
- **C-default-resolution** — a build that ignores config and hardcodes a default coordinate (e.g. `SURREAL_DEFAULT_URL` `:8000`) returns a url ≠ the fixture's `:18000` → RED (control below: `wrong_hardcoded` REDs it). A build that requires `--url` (no default) returns an empty/None coordinate → RED. Mutation-provable: change the fixture url/db and the assertion follows. The anthropic key is SET here so this pin turns ONLY on coordinate-reading (a different DB value from the sibling pin — FIXTURES-MUST-DISCRIMINATE).
- **C-anthropic-independence** — a build that routes the default path through `load_config` raises `ValueError` on the unset key → RED (control below: `wrong_loadconfig` REDs it with `RAISED:ValueError`). A correct `model_validate`/surreal-only build greens. The var is a dedicated guaranteed-unset name + `delenv`, so the pin is robust regardless of the host's real `ANTHROPIC_API_KEY` (conftest sets that different var).

## Satisfiability receipt (0-failed against a known-correct build + positive controls)
A throwaway reference-resolver script (NOT the tracked tree; production stays a stub — the builder writes it after the adversary) proves satisfiability AND that each pin discriminates against the exact wrong build Ruling 2 named. Result:
```
== CORRECT build (env-free model_validate) — expect BOTH GREEN ==
  GREEN  C-default-resolution  (result=True)
  GREEN  C-anthropic-independence  (result=True)
== WRONG: hardcoded default coordinate — expect C-default-resolution RED ==
  RED    C-default-resolution  (result=False)
== WRONG: load_config (eager anthropic key) — expect C-anthropic-independence RED ==
  RED    C-anthropic-independence  (result='RAISED:ValueError')
```
The instrument, verbatim (per brief-base §1 — an instrument establishing a load-bearing claim is a deliverable):
```python
# /tmp/satisfiability_05aiii.py — run: uv run python /tmp/satisfiability_05aiii.py
import argparse, copy, os, tempfile
from pathlib import Path
import yaml
from loremaster import comms_cli
from loremaster.config import LoreConfig, load_config

_CANONICAL = {
    "schema_version": 1,
    "project": {"slug": "demand_intelligence", "root": "."},
    "anthropic": {"api_key_env": "ANTHROPIC_API_KEY", "yardstick_model": "claude-sonnet-5"},
    "embedding": {"backend": "tei", "base_url": "http://tei.example:8080", "endpoint": "/embed",
        "model": "voyageai/voyage-4-nano", "dim": 2048, "truncate": False, "max_input_tokens": 8192,
        "max_batch_texts": 32, "concurrency": 2, "connect_timeout_s": 5, "api_key_env": "LORE_TEI_KEY",
        "tokenizer": "voyage-4-nano"},
    "roots": [{"tier": "custom", "watch": "live", "path": "/tmp", "include": ["**/*.py"]}],
    "include": [], "exclude_dirs": [".git"], "exclude_globs": [],
    "chunkers": {".py": {"chunker": "python_ast"}},
    "watcher": {"enabled": True, "observer": "inotify", "debounce_ms": 1500, "reconcile_interval_s": 600},
    "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201}}
_FIXTURE_URL = "ws://127.0.0.1:18000/rpc"

def _write_cfg(tmp, *, database, anthropic_key_env):
    payload = copy.deepcopy(_CANONICAL)
    payload["anthropic"] = {"api_key_env": anthropic_key_env}
    payload["surreal"] = {"url": _FIXTURE_URL, "namespace": "lore", "database": database,
        "user_env": "SURREAL_USER", "password_env": "SURREAL_PASS"}
    p = tmp / "lore.yaml"; p.write_text(yaml.safe_dump(payload), encoding="utf-8"); return p

def correct(args, *, config_path=None):
    if args.url is not None:
        return comms_cli._ResolvedCoordinate(args.url, args.namespace, args.database)
    config = LoreConfig.model_validate(yaml.safe_load(Path(config_path).read_text()))
    return comms_cli._ResolvedCoordinate(config.surreal.url, config.surreal.namespace, config.effective_surreal_database)

def wrong_hardcoded(args, *, config_path=None):
    if args.url is not None:
        return comms_cli._ResolvedCoordinate(args.url, args.namespace, args.database)
    return comms_cli._ResolvedCoordinate("ws://127.0.0.1:8000/rpc", "lore", "wrong_slug")

def wrong_loadconfig(args, *, config_path=None):
    if args.url is not None:
        return comms_cli._ResolvedCoordinate(args.url, args.namespace, args.database)
    config = load_config(config_path)  # eager anthropic key resolution
    return comms_cli._ResolvedCoordinate(config.surreal.url, config.surreal.namespace, config.effective_surreal_database)

def _args(): return comms_cli._build_parser().parse_args(["pending", "--agent", "x"])

def pin_default_resolution(resolver):
    os.environ["COMMS_CLI_TEST_ANTHROPIC_KEY"] = "dummy-unused"
    with tempfile.TemporaryDirectory() as d:
        cfg = _write_cfg(Path(d), database="cli_default_probe", anthropic_key_env="COMMS_CLI_TEST_ANTHROPIC_KEY")
        r = resolver(_args(), config_path=cfg)
        return r.url == _FIXTURE_URL and r.namespace == "lore" and r.database == "cli_default_probe"

def pin_anthropic_independence(resolver):
    os.environ.pop("COMMS_CLI_TEST_ANTHROPIC_KEY_DEFINITELY_UNSET", None)
    with tempfile.TemporaryDirectory() as d:
        cfg = _write_cfg(Path(d), database="cli_credfree_probe", anthropic_key_env="COMMS_CLI_TEST_ANTHROPIC_KEY_DEFINITELY_UNSET")
        try:
            r = resolver(_args(), config_path=cfg)
        except Exception as exc:
            return f"RAISED:{type(exc).__name__}"
        return r.url == _FIXTURE_URL

def v(name, ok): print(f"  {'GREEN' if ok is True else 'RED  '}  {name}  (result={ok!r})")
print("== CORRECT build (env-free model_validate) — expect BOTH GREEN ==")
v("C-default-resolution", pin_default_resolution(correct)); v("C-anthropic-independence", pin_anthropic_independence(correct))
print("== WRONG: hardcoded default coordinate — expect C-default-resolution RED =="); v("C-default-resolution", pin_default_resolution(wrong_hardcoded))
print("== WRONG: load_config (eager anthropic key) — expect C-anthropic-independence RED =="); v("C-anthropic-independence", pin_anthropic_independence(wrong_loadconfig))
```

## Gate counts (failing-FILE classification — ZERO new non-auth failures)
- **ruff** `uv run ruff check` on the 3 touched files: **All checks passed** (exit 0).
- **mypy** `./scripts/typecheck.sh`: **ZERO errors in any touched file** (grep over `comms_cli.py` / `test_comms_cli.py` / `test_comms_status_age.py` returned none). Total **191** errors = the untouched auth-WIP `#333` baseline (RED_ADJUDICATED per `scripts/gates.yaml`, owned — not orphaned). Zero added.
- **pytest** the 2 touched files (`-n auto`, spike-surreal `:18000`): **7 failed / 10 passed / 0 error**. Failures classify:
  - `test_comms_cli.py`: my **2 new pins** (behavioural `AssertionError`: `None == 'ws://127.0.0.1:18000/rpc'`, RED-for-the-right-reason — setup/parse/seam-call all succeed) + the pre-existing **C-counts** RED (stub returns 2). The 6 pre-existing green pins (C-cmd×3, C-readonly-runtime, C-readonly-source, C-coordinate-safety) STILL PASS over the modified source.
  - `test_comms_status_age.py`: the pre-existing **D5/D6/D7/D8** RED pins (I added only docstrings — no assertion changed; the D4/D9a/D9b/D10 greens are unchanged).
- **Collection**: `--collect-only` over the whole tests dir → **7815 tests collected, 0 collection errors** (the cross-module import introduced none). `test_config.py` (the file I import `_CANONICAL_CONFIG` from) → **86 passed**, unaffected.
- **Failing-FILE classification:** the ONLY files carrying failures attributable to this revision are the 2 touched test files, all failures intended (2 new behavioural-RED pins + the packet's pre-existing RED pins). No existing non-auth file gained a failure; the `#333` auth-WIP baseline (mypy + pytest) is untouched.

## Writable set touched
`loremaster/loremaster/comms_cli.py` (stub seam), `loremaster/tests/test_comms_cli.py` (2 new pins + fixture helper + folded docstring), `loremaster/tests/test_comms_status_age.py` (Ruling-1 rider docstring + Ruling-3 D8 confirmation + folded module note). No other file edited; `test_config._CANONICAL_CONFIG` is imported (read), not modified.
