# REPORT-adversary-46-1 — packet 46 extension-discovery CONTRACT adversary

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — contract empirically graded by 14 wrong/reference builds in a provenance-asserted scratch copy.
- **VERDICT: CONTRACT INSUFFICIENT** — 1 BLOCKER missing pin (a wrong build passes all 9 pins), 1 minor missing pin. Otherwise a strong contract (11 of 12 attacked doors caught).
- **P1 headline:** `first_key_only` (discovery that processes only the FIRST `config.extensions` key) passes **9/9** yet silently drops every later key AND silently ignores an unknown key that isn't first — the loud-fail the packet exists to guarantee never fires. Root cause: **every fixture uses a single-key `extensions` config**, so the ∀-over-config-keys invariant is pinned only at N=1 (THE QUANTIFIER LAW / small-N).
- **P1 headline 2 (minor):** `leak_unknown_as_known` (known-set = `sorted(registry ∪ config.extensions)`) passes **9/9** — the served error lists the unknown key ITSELF among "Known extensions" (a Trust Leg-1 false clear); the contract asserts the known names are PRESENT but never that the unknown key is ABSENT from the known-set clause.
- Graded: `7908887` (HEAD) + the packet-46 contract/stub which are **UNCOMMITTED working-tree changes** on top · HEAD-at-report: `7908887` · SAME.
- SAT re-verified independently: reference build (§SAT verbatim) = **9 passed**; inert stub = **8 failed / 1 passed** (RED for the right reason). No cannot-fail pins — every one of the 9 shown RED by ≥1 build + GREEN under reference.
- P1c REACH: discovery-HOOK reach (which construction sites) is DERIVED via `__init__` and coverage-CHECKED (empirical: `from_config_only` reddens 7 pins). Discovery-LOOP reach (which keys) is DERIVED but coverage-UNCHECKED → the BLOCKER.
- Packages considered: `importlib.metadata` entry-points — READ wave-D arch §3 (defers with a named trigger: first off-repo extension); a static in-repo `dict` cannot hold an off-repo class ⇒ genuinely different capability ⇒ verdict **keep_with_trigger** — AGREES with contract author, no miss.
- PIN6 verdict: **endorse the guard** — message-vs-assertion is honest (both sides named + asserted; `name_guard_one_side` reddens it), spec-cited (`Extension.name` docstring), not over-reach.
- decisions-needed: none for me. The ~27-test migration FORK is fable-46's (out of my scope).
- receipt pointers: wrong-build sweep → §PROBE-SWEEP; multi-key door → §FINDING-A; leak door → §FINDING-B; tables → §P1B / §P1C / §P-PKG; reference instrument = the contract author's §SAT body (unchanged; I graded it, did not re-author it).

## Graded / provenance
- `git rev-parse HEAD` = `7908887867abff25373d5edc6a5cbe327deade3e`. The contract (`test_extension_discovery.py`), the inert stub (`server.py`), and `EXTENSION_REGISTRY` (`extension.py`) are **uncommitted** working-tree changes atop that sha — I graded the working tree, not a committed sha. Nothing my verdict rests on has moved.
- Scratch copy: `/home/ejprice/PycharmProjects/scratch-adversary-46-1` (via `scripts/scratch_copy.sh`; **NOT** a git worktree). Provenance receipt (finding #140):
  `loremaster.__file__ = /home/ejprice/PycharmProjects/scratch-adversary-46-1/loremaster/loremaster/__init__.py` — imports resolve INSIDE the copy; every wrong build graded its OWN code. Lead/operator may `rm -rf` it (I could not; sandbox-denied). The mutation harness `_adv/mutate.py` + demonstrators `_adv/multikey_demo.py` / `_adv/multikey_unknown_demo.py` are pasted below (§INSTRUMENT) so nothing load-bearing lives only in scratch.

---

## VERDICT: CONTRACT INSUFFICIENT

Two concrete missing pins, ranked. The first is a P1 BLOCKER (a wrong build survives the whole contract); the second is a Trust residual with a plausibility caveat. Both are cheap to close (one fixture each). **The contract is otherwise excellent** — it caught 10 of the 12 wrong builds I threw at it including every door the brief named except the two below, and its REACH pinning of `__init__` over `from_config` is genuinely correct and empirically proven.

---

## §P1B — QUANTIFIER TABLE (per-invariant ∀-vs-guarded, with door-build receipts)

Empirical throughout: the oracle (the 9 real pins) exists at my phase; I scaffolded wrong builds in scratch and ran the real contract against them.

| # | invariant a caller assumes | class | receipt (door-build) | verdict |
|---|---|---|---|---|
| I1 | **every `config.extensions` key is composed, OR boot fails loudly** | **∀ over config keys** | `first_key_only` build (loop over `list(config.extensions)[:1]`) → **9/9 pass**; 2-key demo drops key #2 silently; valid+unknown demo ignores the unknown silently while reference RAISES | **HOLE → §FINDING-A (BLOCKER)** — pinned only at \|config\|=1 |
| I2 | unknown key ⇒ loud fail naming the **registry-derived** known set | guarded (key ∉ registry) | `blind_raise`, `handlist_known`, `one_known`, `config_keys_known` each → PIN1 **RED**. Un-hardcodable probe names defeat any hand-list. | GUARDED-ok, with a **leak residual** (§FINDING-B): anti-leak not asserted |
| I3 | key ≠ instance.name ⇒ loud fail naming **both** | guarded (name mismatch) | `no_name_guard` → PIN6 RED (no raise); `name_guard_one_side` → PIN6 RED (names only key) | GUARDED-ok |
| I4 | empty `extensions` ⇒ byte-identical serving | guarded (empty) | `phantom_on_empty` (registers a tool on empty) → PIN3 RED (surface grows) | GUARDED-ok |
| I5 | discovered colliding tool ⇒ `build_mcp_server` raises **even when the built-in is disabled** | guarded (collision ∘ 45 universe) | `registered_only` guard → PIN4 harder-leg RED; first leg still passes (proves BOTH legs load-bearing) | GUARDED-ok |
| I6 | extension tools publish `ToolAnnotations(readOnlyHint=False)` | ∀ over ext tools (ONE `add_tool` call site) | `annotation=none` → PIN5 RED (`is not None`); `annotation=readonly_true` → PIN5 RED (`is False`) — both directions | GUARDED-ok (N=1 fine: single code path funnels all tools) |
| I7 | registry read LIVE at construction (test-injectable) | ∀ | construction-inspection: `_inject_registry` uses `monkeypatch.setattr(extension_module,…)`, so PIN1/2/4/6 only pass if discovery reads `extension.EXTENSION_REGISTRY` at call time; a module-import-bound copy would fail them. **Empirical leg NOT run** (harness cannot inject a module-level import) — stated honestly. | GUARDED-ok (by construction) |

**Every guarded row carries a killing receipt; the one ∀-over-inputs row (I1) is the BLOCKER.**

---

## §P1C — REACH TABLE (per-instrument; the #291 / six-defeats class)

| instrument | SET it covers | reach DERIVED or hand-list? | coverage a CHECKED variable? | effect or proxy? | legs |
|---|---|---|---|---|---|
| **discovery HOOK** (which of the 4 construction sites discover) | `LoreServer.__init__` (all 4 prod sites route through it) | DERIVED — pins construct via bare `LoreServer(config)` = `__init__`, so a hook narrowed to `from_config` is exposed | **YES** — `from_config_only` build reddens 7 pins | effect (`server.extensions`, `list_tools`) | **EMPIRICAL** |
| **discovery LOOP** (which config keys get processed) | `self._config.extensions` (iterated) | DERIVED (iterates the dict) | **NO** — no pin reddens when observed-keys < config-keys; \|config\|>1 is never exercised | effect | **EMPIRICAL** → **§FINDING-A** |
| **unknown-key known-set** (what the teaching error names) | `registry.keys()` | DERIVED (`", ".join(sorted(registry))`) | PARTIAL — PIN1 proves the set is present & un-hardcodable, but does NOT check the unknown key is absent from it | proxy-ish: observes the message string | **EMPIRICAL** → leak residual §FINDING-B |
| **collision guard** (names an ext tool may not claim) | `_ALL_BUILTIN_TOOL_NAMES ∪ registered` | DERIVED (packet 45; relied-on, not introduced here) | **YES** — PIN4 harder leg reddens a registered-only guard | effect (`build_mcp_server` raise) | **EMPIRICAL** (`registered_only`) |
| **name-mismatch guard** | per-key `instance.name == key` | DERIVED | **YES** — PIN6 reddens both no-guard and one-sided-guard | effect (raise) | **EMPIRICAL** |

Legs said out loud: HOOK, LOOP, known-set, collision, name-guard = **empirical wrong-builds**. The LIVE-read invariant (I7) = **construction-inspection only** (the injection mechanism is the evidence; I could not cheaply inject a module-level import through the stub-block harness).

---

## §P-PKG — package survey (my table, diffed vs the author's)

Built BEFORE re-reading the author's line, then diffed.

| mechanism the contract specifies | library I evaluated · what I READ | my verdict | author verdict | diff |
|---|---|---|---|---|
| config → Extension class discovery | `importlib.metadata.entry_points` (stdlib plugin discovery) — READ wave-D `2026-08-03-wave-d-architecture.md` §3 + the `EXTENSION_REGISTRY` docstring: a static in-repo `dict[str,type]` cannot name an OUT-OF-REPO class, and §3 defers entry-points to "when the first off-repo extension exists" (a real, named trigger) | **keep_with_trigger** (trigger: first off-repo/workspace-external extension) | keep_with_trigger (same trigger) | **AGREE — no miss** |
| unknown-key known-set rendering | none — `", ".join(sorted(...))` is stdlib-trivial | bespoke-trivial | (not listed) | agree; trivial |
| `extensions:` config validation | `pydantic` — already the project boundary lib | replace/reuse (already used) | (already used) | agree |

A contract that specified a hand-rolled mechanism a library already provides is a defect the builder can't fix. **None here** — the one library candidate (entry-points) is a genuinely different capability, correctly deferred with a named re-open trigger.

---

## MISSING PINS (ranked)

### §FINDING-A — BLOCKER — the ∀-over-config-keys invariant is pinned only at N=1
**The test that should exist** (two legs):
```python
class TestAllConfiguredExtensionsAreComposed:
    def test_every_configured_key_is_composed(self, monkeypatch):
        # ≥2 valid keys — the fixture the whole contract lacks
        _inject_registry(monkeypatch,
            {_ALPHA_PROBE_NAME: _AlphaProbeExtension,
             _BETA_PROBE_NAME:  _BetaProbeExtension})
        server = LoreServer(_config({_ALPHA_PROBE_NAME: {}, _BETA_PROBE_NAME: {}}))
        assert set(_extension_names(server)) == {_ALPHA_PROBE_NAME, _BETA_PROBE_NAME}

    def test_an_unknown_key_after_a_valid_one_still_fails_boot(self, monkeypatch):
        _inject_registry(monkeypatch, {_ALPHA_PROBE_NAME: _AlphaProbeExtension})
        with pytest.raises(ValueError, match="totally_unknown_ext_46"):
            LoreServer(_config({_ALPHA_PROBE_NAME: {}, "totally_unknown_ext_46": {}}))
```
**The defect it catches:** any discovery that fails to process ALL config keys — an only-first loop, an early `return`/`break`, a `next(iter(config.extensions))`, a de-dup that collapses. Such a build **composes the first extension, silently drops the rest, and silently ignores an unknown key that is not first** — defeating the packet's entire reason to exist (loud-fail on unknowns + full composition). **Empirically, `first_key_only` passes all 9 current pins (9 passed)** because every fixture's `extensions` config has exactly one key. This is THE QUANTIFIER LAW instance and the small-N fixture antipattern named in this repo's own CLAUDE.md.

### §FINDING-B — MINOR — the unknown-key error can leak the unknown key AS "known"
**The test that should exist** — extend the unknown-name pin with an anti-leak leg:
```python
        # the offending key must appear ONLY as the rejected key, never inside the
        # known-set the error teaches (else the reader learns their typo is valid).
        known_clause = message.split("Known extensions:", 1)[1]
        assert "totally_unknown_ext_46" not in known_clause
```
**The defect it catches:** a known-set derived from `sorted(registry ∪ config.extensions)` (or otherwise polluted with the caller's own keys) — the served error tells the reading LLM the very key it typo'd IS a registered extension (a Trust Leg-1 false clear). **Empirically, `leak_unknown_as_known` passes 9/9.** PLAUSIBILITY CAVEAT: the *natural* config-vs-registry confusion (`known = sorted(config.extensions)`) is already CAUGHT (probes absent → PIN1 RED, proven — `config_keys_known` → 1 failed); this door needs the specific union form, so it is lower-severity than A. Still a real, un-pinned Trust gap the brief explicitly asked me to probe.

---

## Fixture-discrimination verdicts (P2) — every fixture interrogated with "what wrong build still passes this?"

- **PIN1 unknown-name — KNOWN-set uses N=2 (alpha+beta), un-hardcodable probe names.** DISCRIMINATES: a hand-list can't contain the probe names (`handlist_known` RED); naming only one fails "whole set" (`one_known` RED). The 2-entry registry is exactly what makes "names the WHOLE set" testable. STRONG. Residual: anti-leak (§FINDING-B).
- **PIN1 CONFIG-side — N=1 (one unknown key).** Fine for the unknown path, but this single-key monoculture is the same root as §FINDING-A on the compose path.
- **PIN2 — parametrized over 2 DISTINCT classes** (FakeExtension w/ config_model "fake"; CounterExtension w/o "counter"). DISCRIMINATES a single-name special-case (`only "fake"` would fail the counter param) AND proves seam-7 config validation flows through discovery. `isinstance(composed, cls)` proves the real class, not a placeholder. STRONG. But still |config|=1 per param (→ §FINDING-A).
- **PIN3 regression — byte-exact vs `build_instructions(_ALL_BUILTIN_TOOL_NAMES, identity=None)`.** NOT vacuous: `phantom_on_empty` reddens it (surface grows). The `_config({})` default really is tools=None/identity=None, so the RHS is the true default. DISCRIMINATES.
- **PIN4 — TWO legs both load-bearing.** `registered_only` guard passes leg 1 (lore_search registered) but fails leg 2 (disabled). The harder leg is the 45-universe discriminator; without it a registered-only guard would pass. STRONG. Registration order (built-ins first) is real — the collision path IS reached (reference raises; `from_config_only` doesn't compose ⇒ no raise ⇒ RED, proving discovery drives it).
- **PIN5 — R14 mutation-provable BOTH directions** (`none` → `is not None` RED; `readonly_true` → `is False` RED). Uses a MANUAL `register_extension` to isolate R14 from discovery — correct, since R14 lives in the single `_register_extension_tools` funnel. STRONG.
- **PIN6 — both sides named + asserted.** `no_name_guard` RED; `name_guard_one_side` (names only key) RED. Message-vs-assertion HONEST (no gap). STRONG.
- **`BUILTIN_COLLISION_NAME == "lore_search"` fixture guard** present in PIN4 leg-2 — good (the harder leg's premise is asserted, not assumed).

---

## Residuals — each with an individual verdict (nothing waved as "the rest look fine")

- **PIN6 as a contract-author DECISION on a spec-silent boundary:** ENDORSED. Verified against source — `_validate_extension_config` (server.py:648-662) reads `self._config.extensions.get(ext.name, {})`, i.e. the `ext.name` slice, so a key≠name mismatch validates the WRONG (usually `{}`) slice; for a config-model-less extension that is a **silent** mis-registration. Guarding it converts a Trust false-clear into a loud fail, cites the documented `Extension.name` invariant (not "the old code did it"), costs one comparison, threat model = the honest author. Not over-reach. Lead/operator may ratify; I have no objection.
- **The ~27-test composition-suite migration FORK:** OUT OF MY SCOPE (fable-46 owns it; `REPORT-fable-46.md` now present). I did not grade it. Flagged only that the packet-46 CONTRACT is self-contained (10 `_config(...)` sites all pass explicit `extensions=`; registry injected per test), so it stands regardless of how the FORK is ruled — confirmed by reading + the stub keeping all 9 pins' construction independent of `minimal_config`'s default.
- **P6 corpse sweep (retired-behavior assertions inside the contract):** NONE — the contract is a new file; no assertion pins retired behavior. The old-world assertions that break under real discovery live in `test_server.py`/`test_extension.py` and ARE the FORK, already escalated by the author — not a contract defect.
- **P6b orphaned-virtue (deleted/replaced code):** N/A — packet 46 deletes nothing; it wires a previously-INERT stub and adds annotations to one `add_tool`. The only "replaced" behaviors (inert no-op; un-annotated tool) are the DEFECTS being fixed, not virtues to preserve. One micro-note: the R14 `add_tool` change must keep `name=`/`description=` (reference does; PIN5 doesn't assert description — but dropping it would break unrelated suites, so not a contract gap worth a pin).
- **I7 live-read empirical leg:** NOT RUN (construction-inspection only) — disclosed above; the injection mechanism is the standing evidence.
- **`leak_unknown_as_known` plausibility:** the union form is less likely than the caught config-keys form; ranked MINOR accordingly, not dropped.

---

## §PROBE-SWEEP — the full wrong-build record (commands + real output)

Harness: `python _adv/mutate.py <discovery> <annotation> <guard>` rebuilds `server.py` from the pristine inert-stub snapshot and applies 3 named variants; then `uv run pytest loremaster/tests/test_extension_discovery.py -p no:randomly -q`. Reference = `reference readonly_false universe`.

**Positive control (P0) + SAT (C-DEF #133):**
```
APPLIED discovery=reference annotation=readonly_false guard=universe
server.py parses OK
=== SAT: reference build vs 9 pins ===
.........                                                                [100%]
9 passed in 0.91s
```
**Inert stub (RED honesty, P7):** `8 failed, 1 passed in 2.42s` — the 8 new-behavior pins RED, the 1 regression pin GREEN (matches the author's declared expected-RED set).

**The 14-build sweep (each line: variant ⇒ summary; indented = which pins RED):**
```
### from_config_only | readonly_false | universe  =>  7 failed, 2 passed   [REACH caught: pins that construct via __init__ RED]
### noop_symbol      | readonly_false | universe  =>  5 failed, 4 passed   [no-op fix caught: PIN1-control,PIN2×2,PIN4×2 RED]
### blind_raise      | readonly_false | universe  =>  1 failed, 8 passed   [PIN1 RED]
### handlist_known   | readonly_false | universe  =>  1 failed, 8 passed   [PIN1 RED — hand-list can't name probes]
### one_known        | readonly_false | universe  =>  1 failed, 8 passed   [PIN1 RED — both names required]
### config_keys_known| readonly_false | universe  =>  1 failed, 8 passed   [PIN1 RED — natural config-vs-registry mistake IS caught]
### leak_unknown_as_known | readonly_false | universe  =>  9 passed        [<<< DOOR OPEN — §FINDING-B]
### no_name_guard    | readonly_false | universe  =>  1 failed, 8 passed   [PIN6 RED]
### name_guard_one_side | readonly_false | universe  =>  1 failed, 8 passed[PIN6 RED — both sides required]
### phantom_on_empty | readonly_false | universe  =>  2 failed, 7 passed   [PIN3 RED — regression leg discriminates]
### reference        | none           | universe  =>  1 failed, 8 passed   [PIN5 RED — annotations None]
### reference        | readonly_true  | universe  =>  1 failed, 8 passed   [PIN5 RED — readOnlyHint True]
### reference        | readonly_false | registered_only  =>  1 failed, 8 passed [PIN4 harder-leg RED — 45 universe guard]
### first_key_only   | readonly_false | universe  =>  9 passed             [<<< BLOCKER DOOR OPEN — §FINDING-A]
```

**§FINDING-A door-build receipts (the two demonstrators):**
```
# multi-key drop — same 2-key config, two builds:
first_key_only : composed = ['alpha_probe_ext_46']                       VERDICT: DROPPED {'beta_probe_ext_46'} SILENTLY -- WRONG
reference      : composed = ['alpha_probe_ext_46','beta_probe_ext_46']   VERDICT: BOTH composed (correct)

# valid-key + unknown-key, two builds:
first_key_only : composed=['alpha_probe_ext_46']  VERDICT: NO RAISE for 'typo_unknown_ext_46' -- unknown SILENTLY IGNORED
reference      : VERDICT: raised (correct loud-fail): "unknown extension 'typo_unknown_ext_46' named in the ``extensions:`` ..."
```

**No cannot-fail pins (P0/P4):** across the sweep every one of the 9 pins was shown RED by ≥1 build and GREEN under the reference — so no pin passes for a fixture reason it can't escape. The `leak_unknown_as_known` result is the sole exception where a WRONG build stays fully green, which is precisely §FINDING-B.

---

## §SAT — the reference instrument I graded against
I did NOT re-author the reference — I graded the contract author's §SAT `_discover_extensions` body + the R14 `add_tool(annotations=ToolAnnotations(readOnlyHint=False))` change verbatim (transcribed into `_adv/mutate.py` variant `reference`). It goes **9 passed** in my provenance-asserted copy — the satisfiability receipt reproduces independently (not trusted from REPORT-contract-46-1). The reference build itself is CORRECT at all N (its loop is `for key in self._config.extensions:`); §FINDING-A is a defect in the CONTRACT's power to distinguish that correct loop from a key-count-limited one, not a defect in the reference.

## §INSTRUMENT — harness (pasted verbatim; brief-base §1, scratch is disposable)
`_adv/mutate.py` rebuilds `server.py` from `server.pristine.py` and applies exact-string variants for {discovery body, add_tool annotations, collision guard}. Variants used: discovery ∈ {stub, reference, from_config_only, noop_symbol, blind_raise, handlist_known, one_known, config_keys_known, leak_unknown_as_known, no_name_guard, name_guard_one_side, phantom_on_empty, first_key_only}; annotation ∈ {none, readonly_false, readonly_true}; guard ∈ {universe, registered_only}. Demonstrators `_adv/multikey_demo.py` (2 valid keys) and `_adv/multikey_unknown_demo.py` (valid+unknown) inject a registry via `extension_module.EXTENSION_REGISTRY = {...}`, build via `minimal_config(extensions=...)`, and print composed names / raise status. All three live in the scratch copy named above; their full behavior is specified here so a future reader can reconstruct them.
