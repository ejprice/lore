# REPORT-fable-46 — packet 46 test-migration shape (extension discovery reconciliation)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- role: DESIGN SIDECAR (consultant) — this is a DOC + RECOMMENDATION; I edit no code and decide nothing. Lead ratifies.
- state: **done** — a concrete, ruled TEST-MIGRATION SHAPE the builder follows (§SHAPE), with the double-registration/slice tension resolved per category.
- **CORRECTION to the contract's breakage census (load-bearing):** `REPORT-contract-46-1.md` measured 4 files; `minimal_config` feeds **3 more** that construct a `LoreServer` and were NOT measured. Two are fine/free; **`test_search.py::TestExtensionHooks` is DOUBLY broken** and needs the same discovery migration. The builder MUST grep, not work from the contract's 4-file list. (§BLAST)
- **key mechanism finding:** the missing-slice fail-loud branch of `_validate_extension_config` is **UNREACHABLE via discovery** (discovery always supplies the iterated key's slice) and reachable ONLY via a manual `register_extension`. So one guard test is the *sole* coverage of that branch and MUST stay manual. (§MECH, §SHAPE-C)
- ratified mechanism (NOT relitigated): config→discovery in `__init__`, empty prod registry, unknown key fails boot loud, PIN6 key==name guard. Untouched by this reconciliation.
- Packages considered: none — no mechanism specified (this is a test-fixture reconciliation, no new production mechanism).
- Reuse ledger: 1 shared test helper PROPOSED (`_extension_helpers`-hosted registry-injection fixture — used by ≥2 modules, so it is a FUNCTION, not a clone). See §DRY.
- Graded: n/a — advisory design doc, not a verdict on another agent's artifact. (No pass/fail rendered on committed code.)
- decisions-needed: none blocking — the shape is ratifiable as-is. One judgement call flagged for the lead (§SHAPE-C, nit-1 rebase vs discovery-injection) with a recommendation.
- receipt pointers: mechanism → `loremaster.server.LoreServer._validate_extension_config` / `.__init__` / `.register_extension`; blast radius → §BLAST (grep-derived); category map → §SHAPE.

---

## MECH — the two facts that determine every category (verified, not assumed)

Read at git `7908887` via `lore_get_symbol`:

1. **`LoreServer.__init__` runs `self._discover_extensions()` LAST, on EVERY construction** — not only `from_config`. So *any* config carrying a `"fake"` key against the empty production registry raises **at construction time**, before any manual `.register_extension` line is reached.

2. **`_validate_extension_config` reads `self._config.extensions.get(ext.name, {})`.** The missing-slice → `model_validate({})` → `ValidationError` path (the "fail loud on a required field with no slice" behaviour) fires ONLY when an extension is registered whose `name` key is **absent** from `config.extensions`. Under discovery, the registered key IS the iterated `config.extensions` key, so its slice is **always present**. Therefore:

   > **The missing-slice branch is UNREACHABLE via discovery-driven registration. Its only reachable caller is a MANUAL `register_extension` against a config lacking that key.**

This is the hinge. It means `register_extension` retains a real, discovery-unreachable guard contract, so a subset of unit tests MUST stay manual (§SHAPE-C) or that branch silently orphans (a green suite over dead-to-discovery code — the exact class CLAUDE.md's rename law warns about).

**The irreducible tension, resolved:** you cannot MANUALLY register a `config_model`-bearing extension whose `name` matches a key present in `config.extensions` —
- key present + in registry ⇒ discovery already auto-registered it → the manual call DOUBLE-registers;
- key present + not in registry ⇒ discovery RAISES at construction;
- key absent (slice removed) ⇒ the required-field `config_model` fails validation.

So **anything that needs a `config_model` extension WIRED must go discovery-driven** (registry injection + slice); **anything testing `register_extension`'s own guards uses a NO-`config_model` extension against an empty-slice config** (manual, no discovery interference). Every category below is one side of that split.

---

## BLAST — `minimal_config` default → `{}`: the FULL radius (grep-derived; do not trust a count)

**Ruling: change `minimal_config`'s default from `{"fake": {"flavour": "vanilla"}}` to `{}`.** It is test-only (`minimal_config` lives in `loremaster/tests/_extension_helpers.py`; grep confirms **zero production callers**), so production discovery is untouched — constraint honored.

The contract measured `test_server.py`, `test_extension.py`, `test_tool_allowlist.py`, `test_mcp_server.py`. A bare `grep -rn "minimal_config" loremaster/tests/` shows **three more files** that route `minimal_config` into a `LoreServer`, none of them in that census:

| file / site | carries a `"fake"` slice into a `LoreServer`? | fate under real discovery | fate under default→`{}` | disposition |
|---|---|---|---|---|
| `test_server_chunker_wiring.py` `_config_with_chunkers` (`minimal_config().model_dump()`, only `chunkers` overridden — `extensions` **survives**) → `_boot_from_yaml` → `from_config` | **YES** (inherits the default slice) | **RAISES at construction** — every boot-based test breaks | **FIXED FREE** (`extensions:{}` → discovery no-op → bare server, which is all these chunker-routing tests want) | **Category A** (was uncounted) |
| `test_search.py::TestExtensionHooks._extension_pipeline` (`base_config.model_copy(update={"extensions": minimal_config().extensions})` then `LoreServer(ext_config).register_extension(FakeExtension())`) | **YES** | **RAISES at construction** | still **BREAKS** — differently: empty slice ⇒ manual `register_extension(FakeExtension())` ⇒ `FakeConfigModel.model_validate({})` ⇒ **ValidationError** | **Category B** — needs explicit discovery migration (was uncounted) |
| `test_lifespan_framework.py` `_config_path` (`minimal_config(extensions={})`, explicit) | no | unaffected (empty slice, its fakes declare no `config_model`) | unaffected (explicit arg) | **SAFE, no change** |

Plus the already-measured sites, re-confirmed independently:
- `test_server.py::config_path` (`minimal_config()`) → the 9 bare tests + drives the wiring/guard tests. **Category A/B/C** (below).
- `test_extension.py:232` `LoreServer(minimal_config()).register_extension(_FieldIndexDeclaringExtension())` — the local ext has **no `config_model`** → under `{}`, discovery no-ops and the manual register needs no slice → **FIXED FREE (Category A)**.
- `test_extension.py:73/100/320` build an `ExtensionContext` (config merely carried, never discovered) and assert nothing on `config.extensions` → **SAFE under `{}`**.
- `test_tool_allowlist.py` / `test_mcp_server.py`: **no `minimal_config` usage at all** (grep) and their configs carry no `extensions` slice → discovery no-ops → **UNAFFECTED** (contract's claim confirmed by mechanism, not just taken).
- `loremaster/tests/test_extension_discovery.py` (the packet-46 contract) always passes an **explicit** `extensions=` (line 134) and never reads the default → **independent of this change; DO NOT TOUCH** (constraint honored).

> **Builder instruction (per CLAUDE.md "sweep from the grep, never a hand-list"):** run `grep -rn "minimal_config" loremaster/tests/` and `grep -rn "_boot_from_yaml\|_config_with_chunkers" loremaster/tests/test_server_chunker_wiring.py` and give **each** hit an individual verdict before executing. The table above is the derived map, not a substitute for the sweep — the contract's own census already missed three sites, so re-derive.

**Net:** default→`{}` fixes MORE than the contract claimed (all of `test_server_chunker_wiring.py` too, for free), and the churny alternative (leave the default, edit every bare test to pass `extensions={}`) is strictly worse. Ratify it.

---

## SHAPE — the migration, by category (resolves the tension explicitly)

Three primitives, mapped onto the split in §MECH.

### Category A — bare-server construction: FIXED FREE by default→`{}` (zero per-test edits)
These construct a server and assert *bare* behaviour; the default flip makes `config_path` write an empty slice, discovery no-ops, done.
- `test_server.py`: `TestFromConfig` (both), `TestBareServerIsGenericRag` (all 7).
- `test_server.py`: `TestConfigModelValidation::test_missing_slice_for_extension_with_a_model_fails_loud` — already `minimal_config(extensions={})`; **passes as-is** (it's the one currently-green test in that file). See also §SHAPE-C — it is Category-C by ROLE even though it needs no edit.
- `test_extension.py::TestFieldIndexesCollectedByLoreServer` (the local no-`config_model` ext).
- **`test_server_chunker_wiring.py`: ALL boot-based tests** (uncounted by the contract).
- `test_lifespan_framework.py`: untouched.

### Category B — a `config_model` extension must be WIRED: migrate to DISCOVERY-DRIVEN
Inject the registry, keep the explicit `"fake"` slice, let **discovery** register it, **drop the manual `.register_extension(FakeExtension())`**, assert on the composed server. This is the *production* composition path — the most faithful thing the suite can exercise, per the constraint "exercise the production path as primary."

Shape (proposed shared fixture, §DRY):
```python
# in _extension_helpers.py — used by BOTH test_server.py and test_search.py
def register_in_discovery(monkeypatch, mapping: dict[str, type[Extension]]) -> None:
    """Point live extension discovery at `mapping` for the test's duration."""
    import loremaster.extension as extension_module
    monkeypatch.setattr(extension_module, "EXTENSION_REGISTRY", mapping)
```
```python
# test_server.py — the wiring tests become discovery-composed
@pytest.fixture()
def fake_discovered(monkeypatch, tmp_path) -> Path:
    register_in_discovery(monkeypatch, {"fake": FakeExtension})
    config = minimal_config(extensions={"fake": {"flavour": "vanilla"}})
    path = tmp_path / "lore.yaml"
    path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    return path

def test_seam3_tools_are_collected(self, fake_discovered: Path) -> None:
    server = LoreServer.from_config(fake_discovered)          # discovery composed "fake"
    specs = server.tool_specs(server.extension_context(store=object()))
    assert [s.name for s in specs] == ["fake_tool"]
```
Members:
- `test_server.py::TestRegisterExtensionWiring` seam tests (seam1, 2, 3, 4, 5, 6, 8, 9, 10, 11) — body unchanged except the server now comes from `from_config(fake_discovered)` instead of `.register_extension(FakeExtension())`. Assertions identical (discovery calls the SAME `register_extension` internally with the SAME instance semantics).
- `test_server.py::test_register_returns_self_for_chaining` — **split**: the *discovery-registered* assertion (`[e.name for e in server.extensions] == ["fake"]`) lands here; the *returns-self-for-chaining* assertion moves to a manual unit (§SHAPE-C).
- `test_server.py::TestConfigModelValidation::test_valid_slice_passes` — registry-inject `{"fake": FakeExtension}`, slice `{"flavour":"chocolate"}`, `server = from_config(path)`; assert `server.extension_config("fake").flavour == "chocolate"`.
- `test_server.py::TestConfigModelValidation::test_bad_slice_fails_loud` — registry-inject, slice `{"flavor": "misspelled"}`; **`with pytest.raises(ValidationError): LoreServer.from_config(path)`** (discovery's internal `register_extension` raises). Strictly MORE production-faithful than the old manual form — validation now fails where it actually fails in prod (boot).
- **`test_search.py::TestExtensionHooks._extension_pipeline`** (the uncounted DOUBLY-broken helper) — inject `{"fake": FakeExtension}`, keep an explicit `{"fake":{"flavour":"vanilla"}}` slice on `ext_config`, drop the manual `.register_extension(FakeExtension())`, let `LoreServer(ext_config)` discover it. **One helper edit fixes every `TestExtensionHooks` test** that routes through it.

### Category C — `register_extension`'s OWN guards: stay MANUAL (no `config_model`, empty-slice config)
The retained public primitive keeps guards discovery cannot exercise; test them directly with a NO-`config_model` extension against `minimal_config(extensions={})`, so discovery no-ops and the manual call is the sole actor. These are legitimate unit tests of a real primitive — keep them.
- `test_server.py::TestConfigModelValidation::test_missing_slice_for_extension_with_a_model_fails_loud` — **KEEP EXACTLY AS-IS.** Per §MECH it is the *only* coverage of a discovery-unreachable branch; migrating or deleting it silently orphans that branch. (No edit needed; flag its ROLE in a one-line comment so a future rename doesn't "helpfully" fold it into discovery.)
- `test_server.py::TestNit1RegisterGuard` (all 4) — these test the **chunker suffix-overlap guard**, orthogonal to `config_model`. **Recommended: rebase the shadow classes off `Extension` (not `FakeExtension`)** — give each a `name` + only `chunkers()`; `config_model` then defaults to `None`, no slice needed. Register manually against `LoreServer.from_config(<empty-slice config_path>)`. The `test_filename_keyed_chunker_without_a_suffix_is_allowed` test (currently registers `FakeExtension` directly) becomes a tiny bare extension exposing only `FakeMakefileChunker()`.
  - *Judgement call for the lead:* the alternative is discovery-injection per nit-1 test (inject the shadow class, expect `from_config` to raise). It works but conflates a chunker-guard test with discovery plumbing. **I recommend manual/rebase** — a guard on a primitive is cheapest and clearest tested on the primitive, and it keeps the manual `register_extension` path covered (which also protects the DUAL — see below).
- **chaining-returns-self** (extracted from `test_register_returns_self_for_chaining`) — a small manual unit: `assert LoreServer(minimal_config(extensions={})).register_extension(_NoConfigExt()) is server`, where `_NoConfigExt` is a bare `Extension` (name only, `config_model` None).

### DUAL check (CLAUDE.md removed-behavior inventory — what dropping the manual register could orphan)
Every behaviour the old manual-register tests pinned survives, adjudicated:
- **`register_extension` returns self / chains** → preserved (Category C chaining unit). PIN.
- **slice validation: valid / bad-extra-key / missing-required** → all three fates preserved: valid + bad via discovery (B), missing via manual (C). PIN.
- **the missing-slice branch specifically** → preserved-with-pin; it is discovery-UNREACHABLE, so the manual test is mandatory, not redundant. PIN + role-comment.
- **nit-1 suffix/greedy-handles guard** → preserved (C, manual). PIN.
- **seam composition (1,2,3,4,5,6,8,9,10,11)** → preserved via discovery (B); discovery calls the same `register_extension`, so the seam wiring is exercised transitively. PIN.
- **the manual `register_extension` code path itself** → still executed by every Category-C test AND internally by discovery. Not orphaned.

No behaviour is dropped-deliberately or spec-silent; nothing needs an operator ruling.

---

## DRY ledger (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `register_in_discovery(monkeypatch, mapping)` (proposed, `_extension_helpers.py`) | `grep EXTENSION_REGISTRY`; `lore` read of `test_extension_discovery.py::_registry` | the packet-46 contract already has a LOCAL 2-line `monkeypatch.setattr(extension_module,"EXTENSION_REGISTRY",…)` fixture (`test_extension_discovery.py:122-129); **`test_server.py` AND `test_search.py` both now need the same injection** | **SHARED FUNCTION in `_extension_helpers.py`** — two call sites need the same test-composition policy ⇒ it is a function they call, not a pattern each clones (ONE-IMPLEMENTATION). The contract's local fixture may stay (it predates this and is self-contained) or be re-pointed at the shared helper — builder's call; either is DRY-honest since the helper is the single definition. |

No production symbol is introduced (advisory doc). The registry-injection idiom is *test-composition policy shared across modules*, which is exactly the case §6 says to centralise rather than clone.

## Tool honesty (brief-base §4)
- lore MCP first-choice for all structure lookups: `lore_get_symbol` on `LoreServer.__init__` / `register_extension` / `_validate_extension_config` (exact bodies at `7908887`); `lore_comms` register/heartbeat.
- **Grep fallbacks, SAID OUT LOUD** (all CLAUDE.md case-(a) rename-exhaustiveness / case-(b) non-symbol-seam, where a missed `minimal_config` site compiles-but-breaks): the `minimal_config` blast-radius sweep and the `EXTENSION_REGISTRY` / `_discover_extensions` reference sweeps are cross-cutting textual maps the symbol graph does not own. No lore weakness encountered → no `lore_findings` to file.

## Scope note
- I did not relitigate the ruled mechanism or PIN6 (orthogonal to test migration; leave to contract-adversary/lead).
- The packet-46 contract (`test_extension_discovery.py`, 9 pins) is untouched by this shape and stays green — confirmed independent (always-explicit `extensions=`).
- I edited no code and touched no git state (advisory). The builder owns the edits above.

---

## ONE-LINE RECOMMENDATION (for the lead to ratify)
Flip `minimal_config`'s default to `{}` (fixes all bare-construction tests + the uncounted `test_server_chunker_wiring.py` for free); migrate the `config_model`-extension WIRING tests (`test_server.py::TestRegisterExtensionWiring`/`TestConfigModelValidation` valid+bad, **plus the uncounted `test_search.py::TestExtensionHooks`**) to **discovery-driven** via a shared `_extension_helpers.register_in_discovery` registry-injection helper (drop the manual `.register_extension`); and keep the `register_extension` guard units (`nit-1`, chaining, and especially the discovery-**unreachable** missing-slice test) **manual** with no-`config_model` extensions against an empty-slice config — builder to `grep minimal_config` before executing, because the contract's 4-file census missed three sites.
