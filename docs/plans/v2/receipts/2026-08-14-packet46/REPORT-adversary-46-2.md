# REPORT-adversary-46-2 — packet 46 extension-discovery CONTRACT delta-adversary

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — revised 11-pin contract empirically re-graded by 24 wrong/reference builds in a provenance-asserted scratch copy.
- **VERDICT: CONTRACT SUFFICIENT.** Both adversary-46-1 findings are CLOSED — §FINDING-A (BLOCKER) for the entire PLAUSIBLE multi-key-drop family, §FINDING-B (leak) robustly across every plausible pollution form. The PIN1 fold did NOT weaken PIN1. SAT holds and the new pins do NOT over-constrain the loop shape.
- **P1 headline:** every PLAUSIBLE wrong build I threw is caught. The only survivors are TWO **adversarial-only** residuals that exploit fixture literals (`[:2]` cap; a case-transformed leak) — per this repo's own receding-reach STOP-rule these are documented-bound items, NOT plausible defects, so they do not gate the verdict.
- **§FINDING-A CLOSED:** `first_key_only` 2f, `next_iter` 4f, `break`/`return`_after_first 2f, `sorted_first` 2f, `reversed_first`/`sorted_desc_first` 1f (caught by the order-independent set-equality compose-leg). The 3 CORRECT alt-loops (`set`/`reversed`/`sorted` full iteration) all 11-pass — the pins don't false-RED a non-reference correct build. §FIND-A.
- **§FINDING-B CLOSED:** `leak_union`, `leak_union_key` (registry∪{key}), `leak_echo_clause`, `relabel_known` all redden PIN1. §FIND-B.
- **PIN1 fold un-weakened:** blind_raise/handlist_known/one_known/config_keys_known all still redden PIN1. §FOLD.
- **I7 live-read (both prior passes left it construction-inspection only):** now EMPIRICAL — `import_bound` reddens 9 pins. §I7.
- Residual R1 (`first_two` [:2] passes 11/11) + R2 (`leak_upper`/`relabel_known` anti-leak label+case coupling) — both **adversarial-only**, non-blocking; optional hardenings named. §RESID.
- Packages considered: none — no mechanism specified (I graded a TEST contract; the one library candidate, `importlib.metadata` entry-points, was surveyed by adversary-46-1 §P-PKG → `keep_with_trigger`, unchanged here).
- Graded: `7908887` (HEAD) + the packet-46 contract/stub/registry, which are UNCOMMITTED working-tree changes atop it · HEAD-at-report: `7908887` · SAME. Nothing my verdict rests on has moved.
- receipt pointers: SAT → §SAT; full family sweep → §SWEEP; tables → §P1B / §P1C; residuals → §RESID; harness → §INSTRUMENT.

## Graded / provenance
- `git rev-parse HEAD` = `7908887867abff25373d5edc6a5cbe327deade3e`; `7908887` is an ancestor of HEAD (SAME). The contract (`test_extension_discovery.py` at 11 nodes), the inert stub (`server.py`), and `EXTENSION_REGISTRY` (`extension.py`) are **uncommitted** working-tree changes — I graded the working tree (same base adversary-46-1 / contract-46-2 graded).
- Scratch copy: `/home/ejprice/PycharmProjects/scratch-adversary-46-2` (via `./scripts/scratch_copy.sh`; NOT a git worktree). Provenance receipt (finding #140):
  `loremaster.__file__ = /home/ejprice/PycharmProjects/scratch-adversary-46-2/loremaster/loremaster/__init__.py` — imports resolve INSIDE the copy; every wrong build graded its OWN code. The harness `_adv/mutate.py` is pasted verbatim in §INSTRUMENT so nothing load-bearing lives only in scratch. Lead/operator may `rm -rf` it (I could not — sandbox-denied, as all prior packet-46 agents reported).
- Node count independently reproduced: **11 collected** (`--collect-only`), matching contract-46-2's declared set.

---

## VERDICT: CONTRACT SUFFICIENT

I tried hard to break the revised contract with 24 builds — a superset of adversary-46-1's — and every PLAUSIBLE wrong build is caught. The revision's two added pins close both prior findings; the fold did not weaken PIN1; satisfiability holds against the reference AND three alternative correct loops. Two residual doors survive (`[:2]` cap; case-transformed leak) but both are **adversarial-only** — implausible builder mistakes that exploit the exact count/literal of a fixture — and the repo's own STOP-rule (`CLAUDE.md`, "The STOP-rule for a reach attack") governs: *when each round's fix only relocates the constant to a site the guard still doesn't cover and the surface is adversarial-only, accept a pinned bound with a named re-open trigger; do not run another round.* They are surfaced in §RESID with named, optional hardenings for the lead to rule on (scope is the operator's, not mine).

---

## §P1B — QUANTIFIER TABLE (per-invariant ∀-vs-guarded, with door-build receipts)

Empirical throughout: the oracle (the 11 real pins) exists at my phase; I scaffolded wrong builds in scratch and ran the real revised contract against them.

| # | invariant a caller assumes | class | receipt (door-build) | verdict |
|---|---|---|---|---|
| I1 | **every `config.extensions` key is composed, OR boot fails loudly** | **∀ over config keys** | `first_key_only`→2f, `next_iter`→4f, `break`/`return`_after_first→2f, `sorted_first`→2f, `reversed_first`/`sorted_desc_first`→1f (compose-leg alone, order-independent). The 3 correct alt-loops `set`/`reversed`/`sorted`(full)→11-pass. **`first_two`([:2])→11-pass** | **GUARDED for the plausible family** (first-only in all its shapes). Residual: an adversarial `[:k≥2]` cap → §RESID R1 |
| I2 | unknown key ⇒ loud fail naming the **registry-derived** known set, with the unknown key ABSENT from that set | guarded (key∉registry) + Trust Leg-1 | `blind_raise`/`handlist_known`/`one_known`/`config_keys_known`→PIN1 RED; `leak_union`/`leak_union_key`/`leak_echo_clause`/`relabel_known`→PIN1 RED (anti-leak leg) | **GUARDED** for every plausible leak form. Residual: a case-transformed leak (`leak_upper`→11-pass) → §RESID R2 |
| I3 | key ≠ instance.name ⇒ loud fail naming **both** | guarded (name mismatch) | `no_name_guard`→PIN6 RED; `name_guard_one_side`→PIN6 RED | GUARDED |
| I4 | empty `extensions` ⇒ byte-identical serving | guarded (empty) | `phantom_on_empty`→PIN3 RED (surface grows) | GUARDED |
| I5 | discovered colliding tool ⇒ raise **even when the built-in is disabled** | guarded (collision∘45 universe) | `registered_only`→PIN4 harder-leg RED; first leg still passes ⇒ BOTH legs load-bearing | GUARDED |
| I6 | extension tools publish `ToolAnnotations(readOnlyHint=False)` | ∀ over ext tools (ONE add_tool call site) | proven both directions by adversary-46-1 (`none`→`is not None` RED; `readonly_true`→`is False` RED); every build here pays R14 so PIN5 stays GREEN, isolating the discovery variable | GUARDED |
| I7 | registry read **LIVE at construction** (test-injectable) | ∀ | **NOW EMPIRICAL** (both prior passes = construction-inspection only): `import_bound` (registry bound at import) → **9 pins RED**, only PIN3/PIN5 green (they read no injected registry) | GUARDED (empirical) |

**Every guarded row carries a killing receipt. The two ∀-over-inputs residuals (I1 `[:2]`, I2 case-leak) are adversarial-only bounds, §RESID.**

---

## §P1C — REACH TABLE (per-instrument; the #291 / six-defeats class)

| instrument | SET it covers | reach DERIVED or hand-list? | coverage a CHECKED variable? | effect or proxy? | legs |
|---|---|---|---|---|---|
| **discovery HOOK** (which construction sites discover) | `LoreServer.__init__` (all 4 prod sites route through it) | DERIVED — every pin constructs via bare `LoreServer(config)` = `__init__` | **YES** — adversary-46-1's `from_config_only` reddened 7 pins; unchanged here | effect (`server.extensions`, `list_tools`) | EMPIRICAL (inherited, spot re-verified via SAT) |
| **discovery LOOP** (which config keys processed) | `self._config.extensions` (iterated) | DERIVED (iterates the dict) | **YES for the plausible family** — the compose-leg's order-independent set-equality reddens EVERY first-only shape (7 builds); the unknown-after-valid leg reddens forward/ascending first-only. **NOT checked past N=2** (a `[:k≥2]` cap slips) | effect | **EMPIRICAL** → residual R1 |
| **unknown-key known-set** (what the teaching error names) | `registry.keys()` | DERIVED (`", ".join(sorted(registry))`) | **YES now** — the anti-leak leg reddens registry∪config, registry∪{key}, echo-clause, and relabel forms. NOT checked against a case/whitespace transform of the key | effect (message string) — see label-coupling note R2 | **EMPIRICAL** → residual R2 |
| **collision guard** (names an ext tool may not claim) | `_ALL_BUILTIN_TOOL_NAMES ∪ registered` | DERIVED (packet 45; relied-on) | **YES** — `registered_only`→PIN4 harder-leg RED | effect (`build_mcp_server` raise) | EMPIRICAL |
| **name-mismatch guard** | per-key `instance.name == key` | DERIVED | **YES** — `no_name_guard` + `name_guard_one_side` both redden PIN6 | effect (raise) | EMPIRICAL |
| **live-read** (registry read at call time) | `extension.EXTENSION_REGISTRY` module attr | DERIVED (attribute read) | **YES now (this pass)** — `import_bound` reddens 9 pins | effect | **EMPIRICAL (upgraded from construction-inspection)** |

Legs said out loud: HOOK/LOOP/known-set/collision/name-guard/live-read = **empirical wrong-builds**. Nothing in this table is construction-inspection-only anymore — I ran the I7 leg both prior passes deferred. The two coverage caveats (LOOP past N=2; known-set under a key transform) are the two adversarial-only residuals, not un-run legs.

---

## §SAT — satisfiability, independently reproduced (not inherited)
```
APPLIED variant=reference + R14 paid; server.py written & parses OK
...........                                                              [100%]
11 passed in 0.90s
```
The revised 11-pin contract is satisfiable against the §SAT reference build (contract-46-1's verbatim `_discover_extensions` full-iteration loop + R14). I did NOT trust contract-46-2's "11 passed" — I reproduced it in my own provenance-asserted copy.

**Stronger C-DEF leg — the pins don't over-constrain the loop shape.** Three DIFFERENT correct loops (`set(config.extensions)`, `reversed(...)`, `sorted(...)` — full iteration, order/dedup-neutral) each go **11 passed**. So the new PIN7 legs pass every correct implementation, not just the one reference — no false-RED trap for a builder who writes `for key in sorted(...)` or `.items()`.

## §FIND-A — the multi-key-drop family (the BLOCKER, re-attacked in full)
Every line: `variant => summary  RED:{nodes}`. `stub` = the committed inert stub (10f/1p, matching contract-46-2).
```
### stub                 => 10 failed, 1 passed        RED:{10 behavioural pins; only test_empty_extensions...byte_identical GREEN}
### first_key_only  [:1] => 2 failed, 9 passed         RED:{every_configured_key_is_composed, unknown_key_after_a_valid_one}
### next_iter            => 4 failed, 7 passed         RED:{compose, unknown-after-valid, empty-byte-identical, r14}  (also crashes on empty: next(iter({})) → StopIteration)
### break_after_first    => 2 failed, 9 passed         RED:{compose, unknown-after-valid}
### return_after_first   => 2 failed, 9 passed         RED:{compose, unknown-after-valid}
### sorted_first         => 2 failed, 9 passed         RED:{compose, unknown-after-valid}
### reversed_first       => 1 failed, 10 passed        RED:{compose}            (compose-leg catches it; unknown-leg passes because reversed order hits the unknown key first → raises)
### sorted_desc_first    => 1 failed, 10 passed        RED:{compose}            (same — set-equality is order-independent, so whichever single key survives, {it} ≠ {alpha,beta})
### first_two       [:2] => 11 passed                  RED:{}   <<< SLIPS — adversarial-only cap residual R1
--- correct alternative loops (SHOULD pass = correct, not slips) ---
### set_iter             => 11 passed                  (full iteration, unordered — behaviourally correct)
### reversed_full        => 11 passed                  (correct)
### sorted_full          => 11 passed                  (correct)
```
**Verdict: §FINDING-A CLOSED for the plausible family.** The compose-leg's order-independent set-equality (`set(names) == {alpha,beta}`) reddens EVERY first-only shape regardless of iteration order — I verified forward, reversed, sorted-asc and sorted-desc. The order-dependence the brief flagged is REAL but harmless: it only affects the *unknown-after-valid* leg (which needs the unknown key not-first to fire), and the compose-leg is the backstop that catches every order. The one survivor, `first_two`, is R1.

## §FIND-B — the leak / known-set-pollution family (re-attacked in full)
```
### leak_union       (", ".join(sorted(set(registry) | set(self._config.extensions))))  => 1 failed  RED:{unknown_key_raises...}
### leak_union_key   (", ".join(sorted(set(registry) | {key})))                          => 1 failed  RED:{unknown_key_raises...}
### leak_echo_clause (correct known-set + an extra clause echoing config keys AFTER "Known extensions:") => 1 failed  RED:{unknown_key_raises...}
### relabel_known    (correct, non-leaking known-set under a DIFFERENT label)             => 1 failed  RED:{unknown_key_raises...}  (via IndexError — see R2)
### leak_upper       (", ".join(sorted(set(registry) | {k.upper() for k in config})))    => 11 passed  <<< SLIPS — case-transformed leak, residual R2
```
**Verdict: §FINDING-B CLOSED for every plausible leak form.** The anti-leak leg (`message.split("Known extensions:",1)[1]`; assert the unknown key absent) reddens the union form, the registry∪{key} form, a leak placed in any clause *after* the split point, AND a correct-set-different-label build. It is strictly SAFE — it never lets a same-cased leak through, in any clause. The one survivor, `leak_upper`, is R2.

## §FOLD — the PIN1 fold did NOT weaken PIN1
FINDING-B was folded as an added assertion into PIN1's body. Adding an assertion can only make a pin STRICTER (verified by construction), and the four original PIN1-reddening builds all still redden it:
```
### blind_raise       => 2 failed  RED:{unknown_key_raises..., unknown_key_after_a_valid_one}   (PIN1 RED — 2nd assertion "alpha in message" fails BEFORE the split; PIN7b independently requires the unknown key be NAMED)
### handlist_known    => 1 failed  RED:{unknown_key_raises...}
### one_known         => 1 failed  RED:{unknown_key_raises...}
### config_keys_known => 1 failed  RED:{unknown_key_raises...}   (the natural config-vs-registry mistake still caught)
```
Bonus finding: `blind_raise` ALSO reddens the new `test_an_unknown_key_after_a_valid_one_still_fails_boot` — its `pytest.raises(ValueError, match="totally_unknown_ext_46")` independently forces the unknown key to be NAMED, a second guard on the same Trust property.

## §I7 — live-read invariant, now empirical (the leg both prior passes skipped)
```
### import_bound  => 9 failed, 2 passed   RED:{control, PIN2×2, PIN4×2, PIN6, PIN7×2, PIN1}
```
A build that binds the registry NAME at import (`from loremaster.extension import EXTENSION_REGISTRY`) does NOT see `monkeypatch.setattr(extension_module, "EXTENSION_REGISTRY", {...})`, so every registry-injecting pin reddens. Only PIN3 (empty config, no registry read) and PIN5 (manual `register_extension`, bypasses discovery) stay green — correctly. adversary-46-1 marked this construction-inspection-only; it is now an empirical wrong-build. This is a plausible builder mistake (importing the name directly) and it is GUARDED.

## §RESID — residuals, each with an individual verdict (nothing waved as "the rest look fine")

- **R1 — `first_two` ([:2]) passes 11/11 — adversarial-only cap.** The compose-leg pins ∀-over-config-keys at |config|=2; a loop capped `[:k]` for any k≥2 walks it. **Plausibility: LOW.** `[:1]`/`next(iter())`/`break`-after-first are plausible ("grab the first extension") and ALL caught; there is no domain reason for a builder to cap at exactly 2 (the "2" is a fixture artifact). Per the repo's receding-reach STOP-rule, N=1→N=2 killed the plausible family; demanding N=3 only moves the bound to `[:3]`. **Recommendation (optional, lead's call):** a one-line note on `TestAllConfiguredExtensionsAreComposed` naming the bound ("∀-over-config-keys is pinned for |config|≤2; a `[:k≥2]` cap is adversarial-only and un-closable by a static fixture — re-open if a real extension count exceeds 2 and drop-past-cap becomes plausible"). NOT a blocker; do not bump N and re-run the round.

- **R2 — the anti-leak leg couples to the exact literal `"Known extensions:"` and to the exact-case unknown key.** Two faces, both adversarial-only:
  1. `relabel_known` (correct, non-leaking known-set under a different label) reddens PIN1 via **IndexError** on `message.split("Known extensions:",1)[1]`, not via the intended teaching assertion. Strictly SAFE (a relabel can't hide a leak — it still reddens), but the pin silently pins the label beyond its anti-leak intent, and the failure surfaces as a confusing IndexError. **Recommendation:** add `assert "Known extensions:" in message` BEFORE the split — converts the IndexError into a clean, intentional assertion and makes the label-pin explicit.
  2. `leak_upper` (unknown key leaked UPPERCASED into the known-set) passes 11/11 — the anti-leak assertion checks the lowercase literal, so a case/whitespace-transformed leak slips. **Plausibility: LOW** (no honest builder uppercases keys in a served list). **Recommendation (optional):** a case-insensitive containment check. NOT a blocker.
  - Both R2 faces are the SAME class as R1: an example-based pin keyed on a specific literal is walkable by an adversarial build exploiting that literal. Acceptable as a documented bound.

- **PIN5 R14 isolation:** every build here pays R14 (annotated add_tool), so PIN5 is GREEN throughout and the discovery variable is isolated — I did NOT re-mutate the R14 direction (adversary-46-1 proved it both ways). Disclosed, not skipped.

- **The ~27-test composition-suite migration FORK:** OUT OF MY SCOPE (fable-46 owns it). I did not grade it. The packet-46 contract remains self-contained (registry injected per test; every `_config(...)` passes explicit `extensions=`), so it stands regardless of the FORK ruling — re-confirmed: all 11 pins construct via bare `LoreServer(config)` with an injected registry, none depend on `minimal_config`'s default slice.

- **P6 corpse-sweep / P6b orphaned-virtue:** unchanged from adversary-46-1 — the contract is a NEW file (no retired-behavior assertions); packet 46 deletes nothing (wires an inert stub + annotates one add_tool). N/A.

## §INSTRUMENT — mutate harness (pasted verbatim; brief-base §1, scratch is disposable)
`_adv/mutate.py` rebuilds `server.py` from a pristine inert-stub snapshot (`_adv/server.pristine.py`) and injects one discovery variant, ALWAYS paying R14 (so PIN5 stays green, isolating the discovery variable). Body builder `_body(iter_expr, known_expr, terminate="", extra_echo="")` parametrizes: the for-loop iterable, the known-set expression, an optional trailing `break`/`return`, and an optional extra message clause. Special variants mutate code OUTSIDE the body: `import_bound` injects a module-level `from loremaster.extension import EXTENSION_REGISTRY as _IMPORT_BOUND_REGISTRY` and reads it; `registered_only` drops the `_ALL_BUILTIN_TOOL_NAMES` half of the collision guard; `no_name_guard`/`name_guard_one_side` mutate the mismatch block; `phantom_on_empty` registers an inline `_Phantom(extension_module.Extension)` when `config.extensions` is empty.

Variant → loop / known-set:
- `reference` — `for key in self._config.extensions:` + `", ".join(sorted(registry)) or "(none registered)"`
- FINDING-A family — iterables: `list(...)[:1]`, `[next(iter(...))]`, `...[:2]`, `list(reversed(list(...)))[:1]`, `sorted(...)[:1]`, `sorted(..., reverse=True)[:1]`, and `break`/`return` after the first register; correct controls `set(...)`, `reversed(...)`, `sorted(...)` full.
- FINDING-B family — known-set: `sorted(set(registry) | set(config.extensions))`, `sorted(set(registry) | {key})`, `sorted(set(registry) | {k.upper() for k})`, an echo clause, and a `"Known extensions:"→"Registered set:"` relabel.
- PIN1 regression — `blind_raise` (generic message), `handlist_known` (`["fake","counter"]`), `one_known` (first registry key only), `config_keys_known` (`sorted(config.extensions)`).

Runner (each): `uv run python _adv/mutate.py <variant>` then `uv run pytest loremaster/tests/test_extension_discovery.py -p no:randomly -q`. Full source lives at `/home/ejprice/PycharmProjects/scratch-adversary-46-2/_adv/mutate.py`; the exact anchors and variant strings above let a future reader reconstruct it after the scratch is reaped.
