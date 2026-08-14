# REPORT-contract-46-1 — packet 46 extension-discovery CONTRACT

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done-with-deviations** (RED contract + inert stub committed to writable set; satisfiability proven; ONE design fork escalated).
- deviation 1: a **DESIGN FORK** blocks the BUILDER (not this contract) — real discovery breaks 27 pre-existing tests; escalated to lead-46 (§FORK). Surfaced early (comms #4173) with a recommendation + measured breakage.
- deviation 2: pin-6 (registry-key vs `ext.name`) is a boundary the ruled design was SILENT on — I DECIDED to guard it (rationale §PIN6), citing the framework's own `Extension.name` docstring; flagged for lead/adversary review.
- Packages considered: `importlib.metadata` entry-points (the stdlib plugin-discovery mechanism) — READ wave-D arch §3 which explicitly DEFERS it ("entry-points deferred until an out-of-repo extension exists — named trigger"); verdict **keep_with_trigger** (static `dict` registry now; entry-points when the first off-repo extension exists). No other mechanism specified.
- Reuse ledger: 2 new production symbols + 3 new local test doubles, all dispositioned — see §DRY.
- Graded: n/a — this is a contract deliverable, not a verdict on another agent's artifact.
- **Store touch: NONE** (confirmed, not assumed — §STORE).
- decisions-needed: the §FORK reconciliation (lead-46 to rule/forward to operator). Pin-6 DECIDED (guard).
- receipt pointers: stub → `loremaster/loremaster/extension.py::EXTENSION_REGISTRY`, `loremaster/loremaster/server.py::LoreServer._discover_extensions` (+ its `__init__` call); contract → `loremaster/tests/test_extension_discovery.py`; RED/GREEN split → §PINS; satisfiability + reference instrument → §SAT; gate-delta → §GATE.

## Writable set touched (committed deliverable)
- `loremaster/loremaster/extension.py` — added `EXTENSION_REGISTRY: dict[str, type[Extension]] = {}` (stub home; ships EMPTY; live module global for test injection).
- `loremaster/loremaster/server.py` — added INERT `LoreServer._discover_extensions` + its call at the end of `__init__` (after `_apply_config_chunker_overrides`).
- `loremaster/tests/test_extension_discovery.py` — the RED contract (NEW; 9 pins).

The stub is INERT by design: it keeps EVERY existing suite green today, so the fork below is surfaced at exactly the moment before the builder implements real discovery — not after 27 tests turn red under them.

## PINS — status + "what WRONG build still passes this?"
Node ids from `--collect-only` (9 collected). Against the INERT STUB: **8 behavioral-RED + 1 GREEN**; against the reference build (§SAT): **9/9 GREEN**. Declared expected-RED set = all 9 EXCEPT `TestNoExtensionsIsByteIdenticalServing::test_empty_extensions_serves_only_the_builtins_byte_identical`.

| # | pin (class) | stub | wrong build it still catches |
|---|---|---|---|
| 1 | `TestUnknownExtensionNameFailsBootLoudly` (unknown-name loud fail + monoculture) | RED×2 | blind `raise` (no known set); a HAND-LISTED known set (the two probe names are un-hardcodable, both required); a message naming only ONE known ext. Includes a positive-control (a KNOWN key boots + composes). |
| 2 | `TestRegisteredExtensionIsDiscoveredAndComposed` (positive control) | RED×2 | a one-name special-case (only "fake") fails the `counter` param; discover-without-`register_extension` leaves `server.extensions` empty. Parametrised over 2 distinct classes (FakeExtension w/ config_model, CounterExtension w/o). |
| 3 | `TestNoExtensionsIsByteIdenticalServing` (regression / green-under-stub leg) | **GREEN** | a discovery that mis-fires on EMPTY extensions (phantom tool → surface grows, or reshaped `instructions`). Byte-exact vs `build_instructions(_ALL_BUILTIN_TOOL_NAMES, identity=None)`. |
| 4 | `TestDiscoveredCollisionComposesWithAllowlistUniverseGuard` (collision ∘ 45 guard) | RED×2 | discovery that never composes the ext (no collision reached); **harder leg** — a guard checking only the REGISTERED set: with `lore_search` DISABLED by a `tools:` allowlist, the disabled built-in's reserved name is claimable → no raise. |
| 5 | `TestR14ExtensionToolAnnotations` (R14 rider) | RED | annotations `None` (fails `is not None`); `readOnlyHint=True` (fails `is False`). Mutation-provable BOTH directions. |
| 6 | `TestRegistryKeyMustMatchExtensionName` (boundary — §PIN6) | RED | no guard ⇒ NO raise (silent wrong-slice validation); a guard that names only one side (both key AND actual name required in the message). |

Each test's docstring carries its expected-RED node id + the one-line mutation that reddens a finished build (CLAUDE.md mutation-proof law).

## PIN6 — the registry-key vs `ext.name` boundary (DECISION: guard it)
The ruled design (wave-D §3) is SILENT on what happens if a registry KEY ≠ the instantiated `ext.name`. This is a spec GAP the brief explicitly delegated to me to decide (not a two-readings-of-one-sentence fork). **DECISION: guard it — a mismatch fails boot loudly.**
Rationale (spec-consistent, not invented): the framework's own `Extension.name` docstring declares *"The extension's stable name; also its key in the `extensions:` config"* (`loremaster/loremaster/extension.py`). A key ≠ name violates that DOCUMENTED invariant. Left unguarded, `register_extension` → `_validate_extension_config` reads `config.extensions[ext.name]` (`LoreServer._validate_extension_config`), so a mismatched name validates the WRONG (usually absent `{}`) slice — the operator's real slice at `config.extensions[key]` is IGNORED and nobody is told (a Trust "false clear"). THREAT MODEL: the honest extension author who files their class under the wrong registry key; caught at boot rather than by a silent downstream misconfiguration. Cost: one comparison in the discovery loop; no change to `register_extension`. Flagged for adversary/lead review.

## STORE — no touch (confirmed, not assumed)
The discovery path is pure in-process composition: registry `dict` lookup → `cls()` → `register_extension`. `LoreServer.register_extension` and `LoreServer._validate_extension_config` (read at git 7908887) read ONLY `self._config` and mutate in-memory lists/dicts — no store client, no DDL, no DML. The injected test extensions are inert (construct + return literals). So packet 46 touches no store, schema, or DDL, and the store reference's OVERWRITE / `IF NOT EXISTS` decision rule (`docs/reference/surrealdb-31-capabilities.md`) does not apply. (`register_extension` at git 7908887 also has no store access; the twelfth ingest seam that WILL touch the store is packet 47, explicitly Scope-OUT here.)

## FORK — real discovery vs the pre-existing composition suite (ESCALATION to lead-46)
**Mechanism is SETTLED** (wave-D §3): hook `__init__`; each `config.extensions` key ⇒ registry lookup ⇒ instantiate ⇒ `register_extension`; unknown ⇒ loud boot fail. **NOT settled:** how the pre-existing composition suite coexists with live discovery.

Root cause (measured, git 7908887): `_extension_helpers.minimal_config`'s DEFAULT is `extensions={"fake": {"flavour": "vanilla"}}`. `test_server.py::config_path` writes `minimal_config()` to disk; ~27 tests build servers from it. Under real discovery, `from_config(config_path)` iterates `{"fake": …}`, looks "fake" up in the EMPTY production registry, and raises:
```
ValueError: unknown extension 'fake' named in the ``extensions:`` config; no such extension
is registered. Known extensions: (none registered). Register its class in
loremaster.extension.EXTENSION_REGISTRY, or remove the key.
```
The irreducible tension: `register_extension(FakeExtension())` REQUIRES `config.extensions["fake"]` present (else `_validate_extension_config` → `FakeConfigModel.model_validate({})` → ValidationError on required `flavour`), but that slice trips discovery against an empty registry; and injecting `EXTENSION_REGISTRY={"fake": FakeExtension}` makes discovery AUTO-register "fake", which (a) breaks the `server.extensions == []` bare assertions and (b) double-registers with the manual `.register_extension`. So the composition suite must MIGRATE (config split + registry injection + convert manual→discovery-driven), touching DO-NOT-TOUCH test files with multiple valid shapes → a design decision.

MEASURED breakage against the reference discovery (§SAT provenance):
- `test_server.py`: **26 failed / 27** (all `config_path`-based).
- `test_extension.py`: **1 failed** (`TestFieldIndexesCollectedByLoreServer::test_registered_extension_field_indexes_are_collected`, the sole `LoreServer(minimal_config())` default-slice site) / 34 passed (live-store classes deselected).
- `test_tool_allowlist.py`: **30/30 pass** — UNAFFECTED (its `_config` carries no `extensions` slice).
- `test_mcp_server.py`: structurally UNAFFECTED (its `_config` carries no `extensions` slice; a no-store structural class passed against the reference).

RESOLVABILITY PROBE (single variable, scratch): `minimal_config` default → `{}` alone turns test_server.py from 26→**17 failed** (fixes the 9 bare-server tests for free). The residual **~17** (+ test_extension.py's 1) are the manual-`register_extension`/explicit-slice tests, which need conversion to discovery-driven registration.

**RECOMMENDATION to lead-46** (forward to operator if it wants the ruling): (1) `minimal_config` default → `extensions={}` (fixes the bare half, zero edits to those tests); (2) keep `register_extension` as a first-class public MANUAL seam; (3) for the ~18 manual-register/slice tests, inject `EXTENSION_REGISTRY={"fake": FakeExtension}` per-module and convert them to assert discovery-driven registration (drop the redundant manual `.register_extension`, or keep the ones that specifically unit-test `register_extension`'s slice validation by injecting the registry so discovery, not the manual call, is the composition path). This matches production semantics (config drives discovery). My contract bakes in NO reconciliation — its 9 pins are self-contained via registry injection, so whatever lead/operator rules, the contract stands.

## SAT — satisfiability receipt (the C-DEF trap #133)
Reference discovery + R14 built in a provenance-asserted scratch copy (`./scripts/scratch_copy.sh`, #140). Provenance receipt:
```
loremaster.__file__ = /home/ejprice/PycharmProjects/scratch-pkt46-contract-46-1/loremaster/loremaster/__init__.py
```
(resolves INSIDE the scratch root — the reference build grades its OWN code, not the original tree.)

- **MY CONTRACT vs reference: `9 passed in 2.48s`** — the full contract is satisfiable against a known-correct build.
- Reference is ruff-clean and mypy-clean (scratch `typecheck.sh` = 191 = the adjudicated baseline; ZERO errors name `server.py`/`extension.py`) — no orphaned-import / mypy cleanups demanded.
- Pre-existing seam suites vs reference: allowlist 30/30, mcp_server (structural) pass — UNAFFECTED; test_server (26) + test_extension (1) break = the §FORK, NOT a contract defect.

**THE REFERENCE INSTRUMENT (pasted verbatim per brief-base §1 — the scratch is disposable).** Real `_discover_extensions` body (replaces the inert stub comment):
```python
        import loremaster.extension as extension_module

        registry = extension_module.EXTENSION_REGISTRY
        for key in self._config.extensions:
            cls = registry.get(key)
            if cls is None:
                known = ", ".join(sorted(registry)) or "(none registered)"
                raise ValueError(
                    f"unknown extension {key!r} named in the ``extensions:`` config; "
                    f"no such extension is registered. Known extensions: {known}. "
                    f"Register its class in loremaster.extension.EXTENSION_REGISTRY, "
                    f"or remove the key."
                )
            instance = cls()
            if instance.name != key:
                raise ValueError(
                    f"extension registry key {key!r} maps to a class whose name is "
                    f"{instance.name!r}; an extension's name IS its key in the "
                    f"``extensions:`` config, so register the class under "
                    f"{instance.name!r} (the mismatch would validate the wrong slice)."
                )
            self.register_extension(instance)
```
R14 (in `_register_extension_tools`, the `mcp.add_tool` call):
```python
        mcp.add_tool(
            wrapper,
            name=spec.name,
            description=spec.description,
            annotations=ToolAnnotations(readOnlyHint=False),
        )
```
This is a REFERENCE build for the satisfiability receipt ONLY — the committed deliverable is the RED contract + inert stub. The builder owns the real implementation (this is one correct shape) PLUS the §FORK reconciliation once ruled.

## GATE DELTA (committed deliverable = stub, on the REAL tree)
Baseline (branch, git 7908887): `typecheck.sh` RED **191** + full pytest RED **444**, both RED_ADJUDICATED (owner packet-39-pending-build). I prove ZERO-NEW delta:
- `uv run ruff check` on my 3 files → **All checks passed!** (exit 0).
- `scripts/typecheck.sh` → **191** error lines (== baseline); grep for `extension.py` / `server.py` / `test_extension_discovery.py` in the error set → **absent** (zero new mypy errors name my files).
- New contract vs the inert stub (`pytest -p no:randomly`): **`8 failed, 1 passed`** — the 8 behavioral-RED new-behavior pins + the 1 GREEN regression leg (the passed-COUNT is present; not a "no tests ran" false green).

## DRY ledger (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `EXTENSION_REGISTRY` (extension.py) | `lore_search "extension registry / discovery lookup"` + wave-D §3 | no existing registry; framework has "0 production register_extension call sites"; design MANDATES a static `dict[str, type[Extension]]` | **HAND-ROLLED** (new, design-mandated; entry-points DEFERRED per §Packages) |
| `LoreServer._discover_extensions` (server.py) | `lore_get_symbol` on server construction path + wave-D §3 | no existing config→extension discovery; design mandates a `__init__` helper | **HAND-ROLLED** (new mechanism) |
| `_AlphaProbeExtension` / `_BetaProbeExtension` / `_MisnamedExtension` (test-local) | reused shared doubles from `_extension_helpers` (`FakeExtension`/`CounterExtension`/`CollidingExtension`/`minimal_config`/`BUILTIN_COLLISION_NAME`) per brief | shared doubles cover the happy paths; NO shared double expresses a non-hardcodable probe name or a key≠name mismatch | **HAND-ROLLED**, defined LOCALLY (inline-double idiom, per `test_extension.py::_DuplicateBumpExtension`) — NOT added to shared `_extension_helpers` (discovery-specific) |

REUSED (no new symbol): `minimal_config`, `FakeExtension`, `CounterExtension`, `CollidingExtension`, `BUILTIN_COLLISION_NAME` (from `_extension_helpers`); `ToolsConfig`, `_ALL_BUILTIN_TOOL_NAMES`, `build_instructions`, `build_mcp_server`, `LoreServer` (from production).

## Tool honesty (brief-base §4)
lore MCP tools used first-choice for all structure lookups (`lore_get_symbol`/`lore_search`/`lore_read` for `LoreServer.__init__`, `register_extension`, `_validate_extension_config`, `_register_extension_tools`, `build_mcp_server`, `_register_tools`, `partition_tools_by_posture`, `LoreConfig`). Fallbacks to grep, SAID OUT LOUD: (a) the `minimal_config`/`register_extension` blast-radius sweep across the test tree — a cross-cutting multi-file textual map lore's symbol graph does not own; (b) the annotation-constant grep in server.py — a non-symbol textual seam. No lore weakness encountered (no friction to file).

## Scratch
`/home/ejprice/PycharmProjects/scratch-pkt46-contract-46-1` — a `scratch_copy.sh` scratch copy (NOT a git worktree; disposable by design). The reference instrument is pasted in §SAT, so nothing load-bearing lives only there. I attempted to remove it on close-out but `rm -rf` was denied by a sandbox guard — **operator/lead may safely `rm -rf` it.** It contains ONLY the reference build (real discovery + R14) + a single-variable resolvability probe (`minimal_config` default → `{}`); it can also be inspected before deletion if lead-46 wants to see the reference build in situ.
