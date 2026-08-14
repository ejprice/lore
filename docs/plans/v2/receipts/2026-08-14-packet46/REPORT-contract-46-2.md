# REPORT-contract-46-2 — packet 46 extension-discovery CONTRACT revision

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done-with-deviations** — the two adversary-specified pins added, satisfiability + RED-discrimination re-proven, gates zero-delta. Nothing else touched.
- **PIN added — §FINDING-A (BLOCKER):** new class `TestAllConfiguredExtensionsAreComposed` (2 nodes) — `test_every_configured_key_is_composed` (≥2 distinct keys ⇒ BOTH composed) + `test_an_unknown_key_after_a_valid_one_still_fails_boot` (valid-then-unknown ⇒ raises naming the non-first key). Closes the ∀-over-config-keys / small-N hole `first_key_only` walked through.
- **PIN added — §FINDING-B (MINOR):** anti-leak leg folded into existing PIN1 body (`known_clause = message.split("Known extensions:",1)[1]; assert unknown_key not in known_clause`). Catches the `known = sorted(registry ∪ config.extensions)` union-leak.
- **deviation 1:** FINDING-B is an assertion+comment ADDED INTO PIN1's body — technically a touch of an existing pin. It is the explicitly-assigned FINDING-B ("anti-leak **leg on** the unknown-name pin", reusing PIN1's `message`) and the brief's own "the anti-leak leg is part of PIN1 which is already RED" accounting hint; the general "don't touch the 9 pins' bodies" guard yields to that specific instruction. No existing assertion was altered/removed. Details §DEVIATION.
- Packages considered: none — no mechanism specified (tests only; stdlib `pytest`, reusing existing helpers).
- Reuse ledger: none — **0 new symbols**; both pins reuse `_inject_registry`/`_config`/`_extension_names`/`_AlphaProbeExtension`/`_BetaProbeExtension`/`_ALPHA_PROBE_NAME`/`_BETA_PROBE_NAME` (ONE-IMPLEMENTATION — no new doubles, no shared-helper additions).
- Graded: `7908887` (HEAD) + the packet-46 contract/stub which are UNCOMMITTED working-tree changes atop it · HEAD-at-report: `7908887` · SAME. My measurements rest on the working tree (same base adversary-46-1 graded); nothing my verdict rests on has moved.
- **Satisfiability:** full 11-pin contract vs §SAT reference build = **11 passed** in a provenance-asserted scratch (`loremaster.__file__` INSIDE the scratch root — §SAT).
- **RED-discrimination (declared-expected-RED from `--collect-only` FIRST):** `first_key_only` ⇒ **2 failed / 9 passed** (exactly the 2 FINDING-A legs); `leak` ⇒ **1 failed / 10 passed** (exactly PIN1 via the anti-leak leg). Both match the declared set BOTH ways. §DISCRIM.
- **RED-vs-inert-stub:** **10 failed / 1 passed** (was 8f/1p; +2 FINDING-A nodes; FINDING-B rides already-RED PIN1). §STUB.
- **Gate delta:** ruff `All checks passed!`; `typecheck.sh` = **191** (== baseline), **zero** errors name the file. §GATE.
- decisions-needed: none — the revision is exactly the adversary's two pins; deviation 1 disclosed, not a fork.
- receipt pointers: pins → `loremaster/tests/test_extension_discovery.py::TestAllConfiguredExtensionsAreComposed` (FINDING-A) + `::TestUnknownExtensionNameFailsBootLoudly::test_unknown_key_raises_naming_the_registry_derived_known_set` (FINDING-B anti-leak leg); receipts → §SAT / §DISCRIM / §STUB / §GATE; harness → §INSTRUMENT.

## Scope touched
- **`loremaster/tests/test_extension_discovery.py`** ONLY (the writable set). 9 nodes → 11 nodes.
  - FINDING-A: appended a new class `TestAllConfiguredExtensionsAreComposed` (PIN 7) at end of file — pure append, no existing pin displaced.
  - FINDING-B: inserted a 2-line anti-leak assertion (+ a 6-line explanatory comment naming the reddening mutation) into `TestUnknownExtensionNameFailsBootLoudly::test_unknown_key_raises_naming_the_registry_derived_known_set`, AFTER its existing `_BETA_PROBE_NAME in message` assertion. No existing assertion changed or removed.
- **DO-NOT-TOUCH honoured:** production stub (`server.py`/`extension.py`) unchanged in the main tree (still `M` from contract-46-1; I made no edit); the other 8 pins' bodies unchanged; no other test file; no store/schema.

## §DEVIATION — FINDING-B folds into PIN1 (the one tension in the brief)
The brief says both "do not touch the 9 existing pins' bodies" AND (in the ADD section) "§FINDING-B — anti-leak **leg on** the unknown-name pin", plus (in RED-vs-stub) "the anti-leak leg **is part of PIN1** which is already RED, so account precisely". These pull opposite ways for FINDING-B only.

Two readings that produce different code (surfaced per brief-base §2):
- **Reading A (chosen):** add the anti-leak assertion INTO PIN1's `test_unknown_key_raises_...` body, reusing its `message`. Matches the adversary's verbatim paste (which references `message`, a local that exists only inside that test), the "part of PIN1" hint, and the "account precisely — no new node" accounting. Result: PIN1 node stays 1 node, gains the leg; RED-vs-stub stays +0 for FINDING-B (10f/1p, not 11f/1p).
- **Reading B (rejected):** a SEPARATE new anti-leak test method. This would add an 11th→12th node and change RED-vs-stub to 11f/1p — contradicting the brief's explicit "part of PIN1 which is already RED" accounting. Ruled out by the brief's own count.

I chose A and disclose it prominently. It touches PIN1's body only by ADDING (no existing assertion altered), which is the assigned FINDING-B work, not an unrelated edit.

## §SAT — satisfiability receipt (C-DEF #133; re-proven, not inherited)
Scratch copy: `/home/ejprice/PycharmProjects/scratch-contract-46-2` (via `./scripts/scratch_copy.sh`; **NOT** a git worktree). Provenance (finding #140):
```
loremaster.__file__ = /home/ejprice/PycharmProjects/scratch-contract-46-2/loremaster/loremaster/__init__.py
```
imports resolve INSIDE the copy — the reference build grades its OWN code, not the original tree.

Reference build = the §SAT `_discover_extensions` body from REPORT-contract-46-1 (loops over EVERY `config.extensions` key) + the R14 `add_tool(annotations=ToolAnnotations(readOnlyHint=False))` change, transcribed verbatim into `_adv/mutate.py` variant `reference` (§INSTRUMENT). Full 11-pin contract:
```
APPLIED discovery=reference + R14; server.py written
server.py parses OK
...........                                                              [100%]
11 passed in 2.32s
```
The revised contract is satisfiable against a known-correct build — every pin (the original 9 + my 2 new legs) is GREEN under the reference. No cannot-fail pin: each of my 2 new legs is shown RED by its target wrong build below AND GREEN here.

Lead/operator may `rm -rf` the scratch (I could not — sandbox-denied, as contract-46-1/adversary-46-1 also reported). Nothing load-bearing lives only there: the harness is pasted in §INSTRUMENT.

## §DISCRIM — new-pin RED discrimination (declared-expected-RED FIRST)
**Declared expected-RED, taken from `--collect-only` BEFORE any run** (the mutation-proof-declares-expected-RED law — the 2 new node ids are fixed before any result exists):
- new nodes: `TestAllConfiguredExtensionsAreComposed::test_every_configured_key_is_composed`, `TestAllConfiguredExtensionsAreComposed::test_an_unknown_key_after_a_valid_one_still_fails_boot`.
- FINDING-B rides the existing node `TestUnknownExtensionNameFailsBootLoudly::test_unknown_key_raises_naming_the_registry_derived_known_set`.
- Declared-RED vs `first_key_only` = **exactly the 2 FINDING-A nodes** (other 9 GREEN).
- Declared-RED vs `leak` = **exactly the PIN1 node** (other 10 GREEN).

**Wrong build 1 — `first_key_only`** (`for key in list(self._config.extensions)[:1]:` — the §FINDING-A door that passed 9/9 against the original contract):
```
APPLIED discovery=first_key_only + R14; server.py written
FAILED ...TestAllConfiguredExtensionsAreComposed::test_every_configured_key_is_composed
FAILED ...TestAllConfiguredExtensionsAreComposed::test_an_unknown_key_after_a_valid_one_still_fails_boot
2 failed, 9 passed in 0.95s
```
Observed-RED == declared-RED, both directions (no unexpected red; no declared-red-stayed-green). Both FINDING-A legs discriminate; the OTHER 9 stay as-is (9 passed — the exact set the adversary reported passing 9/9). BLOCKER closed.

**Wrong build 2 — `leak`** (`known = ", ".join(sorted(set(registry) | set(self._config.extensions)))` on the correct loop — the §FINDING-B union-leak that passed 9/9 against the original):
```
APPLIED discovery=leak + R14; server.py written
FAILED ...TestUnknownExtensionNameFailsBootLoudly::test_unknown_key_raises_naming_the_registry_derived_known_set
1 failed, 10 passed in 0.96s
```
Observed-RED == declared-RED. The anti-leak leg reddens PIN1 (the unknown key `totally_unknown_ext_46` now appears inside the "Known extensions:" clause); PIN1's original 3 assertions still hold (the unknown key IS "in message"), so ONLY the new leg fires — proving the leg, not a pre-existing assertion, catches the union-leak. My 2 FINDING-A legs stay GREEN (the leak build has the correct loop). MINOR closed.

A new pin that cannot be shown RED against its target wrong build is not a pin — both are shown RED against theirs and GREEN under the reference.

## §STUB — RED-vs-inert-stub (committed inert stub, main tree)
```
10 failed, 1 passed in 0.96s
```
The 10 RED = the 8 original behavioural pins + my 2 new FINDING-A legs; the 1 GREEN = `TestNoExtensionsIsByteIdenticalServing::test_empty_extensions_serves_only_the_builtins_byte_identical` (the regression floor). Accounting vs the pre-revision 8f/1p: +2 from FINDING-A (both RED against the no-op stub — no compose, no raise); FINDING-B adds **0** to the count because it rides PIN1, which was already RED (the inert stub does not raise, so `pytest.raises` fails before the anti-leak assertion is reached). Exactly the brief's predicted "account precisely".

## §GATE — gate delta (zero-new vs #333, not full-green)
- `uv run ruff check loremaster/tests/test_extension_discovery.py` → `All checks passed!` (exit 0).
- `./scripts/typecheck.sh` → **191** `error:` lines (== the RED_ADJUDICATED baseline, owner packet-39-pending-build); grep of the error set for `test_extension_discovery.py` / `server.py` / `extension.py` → **empty** (zero new mypy errors name any file I touched). The typecheck suite still fails overall on the adjudicated packet-39 baseline — I prove ZERO-NEW delta, not full-green, per the currency rule.

## Tool honesty (brief-base §4)
lore MCP tools used first-choice (registered on `lore_comms`; read the stub via targeted `Read` after locating symbols with `grep -n` on the concrete file — a non-symbol textual-anchor lookup for exact-string mutation, SAID OUT LOUD, which the symbol graph does not own). No lore weakness encountered → no friction filed.

## §INSTRUMENT — mutate harness (pasted verbatim; scratch is disposable)
`_adv/mutate.py` in the scratch rebuilds `server.py` from a pristine inert-stub snapshot (`server.pristine.py`) and applies one discovery variant, ALWAYS paying R14 (so PIN5 stays GREEN in every build). Variants differ only in the loop line and the known-set line:
- `reference`  — `for key in self._config.extensions:` + `known = ", ".join(sorted(registry)) or "(none registered)"`
- `first_key_only` — `for key in list(self._config.extensions)[:1]:` + reference known-set (§FINDING-A target)
- `leak` — reference loop + `known = ", ".join(sorted(set(registry) | set(self._config.extensions)))` (§FINDING-B target)

The discovery body it writes is the §SAT reference (registry `dict` lookup → unknown-key `ValueError` naming the derived known-set → `instance.name != key` mismatch `ValueError` → `register_extension`); R14 rewrites the inert `mcp.add_tool(wrapper, name=spec.name, description=spec.description)` to pass `annotations=ToolAnnotations(readOnlyHint=False)`. Full source lives at `/home/ejprice/PycharmProjects/scratch-contract-46-2/_adv/mutate.py`; its exact anchors and variant strings are reproduced above so a future reader can reconstruct it after the scratch is reaped.
