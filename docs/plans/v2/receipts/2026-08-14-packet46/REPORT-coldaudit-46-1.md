# REPORT-coldaudit-46-1 — packet 46 extension-discovery COLD AUDIT

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- verdict: **GO** — packet 46 (config-driven extension discovery + R14 rider) is ready to mark DONE. Every gate re-run independently; the frozen 11-pin contract implemented (not edited); 4 mutation proofs held in a provenance-asserted scratch; both Trust legs confirmed by live construction; removed-behavior inventory matches builder/Fable DUAL with nothing orphaned; store touch NONE; NO DEPLOY this packet (registry ships `{}`, discovery dark until packet 51).
- state: **done-with-deviations** (deviations are process/housekeeping, none block DONE).
- deviation 1: intermediate commit `543ed72` is NOT gate-green (leaves the pre-existing composition suite RED). Adjudicated **ACCEPTABLE** — inherent to a reshape where impl + test-migration are mutually dependent; one-concern-per-commit is satisfied; FINAL HEAD `89852b3` is green on every touched suite. Minor bisect-cleanliness cost only.
- deviation 2: my scratch `rm -rf /home/ejprice/scratch-coldaudit-46-1` is **sandbox-denied** (same class as builder-46-1 / contract-46-1). Housekeeping; lead may safely `rm -rf` it (disposable by `scratch_copy.sh` design; my instruments survive as the committed `scripts/mutation_proof.py` + the trust probe pasted verbatim in §TRUST).
- deviation 3: I did NOT re-run tests AT the intermediate `543ed72` (a checkout is a git-state mutation, forbidden by scope law) — I take the builder's fork-breakage characterization on faith for the intermediate state ONLY; the FINAL HEAD I verified in full.
- Packages considered: **none — no mechanism specified** (audit). Instruments used: committed `scripts/mutation_proof.py` + an inline trust probe pasted verbatim in §TRUST.
- Reuse ledger: **none** (read-only auditor; introduced no reusable symbols).
- Graded: `89852b3` · HEAD-at-report: `89852b3` · **SAME**.
- decisions-needed: **none** (deviation 1 is a recommend-accept, not a fork).
- receipt pointers: gates → §GATES; mutation proofs → §MUTATION; refute-frame read → §REFUTE; removed-behavior → §DUAL; trust → §TRUST; store → §STORE; deviations → §DEVIATIONS; residuals → §RESIDUALS.

---

## §GATES — every gate re-run independently, my own counts (HEAD `89852b3`)

| gate | command | result |
|---|---|---|
| ruff | `uv run ruff check .` | **All checks passed!** (GREEN) |
| typecheck | `./scripts/typecheck.sh` | RED, **102 errors in 8 files** — all AUTH files; **zero in packet-46 files** (see below) |
| currency | `uv run python scripts/pending_contract_gate.py --currency` | **PASS — every claimed gate GREEN or OWNED (zero RED_ORPHANED)** |

**Typecheck zero-new-delta (NOT full-green — packet 39's typecheck is RED_ADJUDICATED):**
The 102 errors group entirely into auth-posture test files:
`test_auth_composition.py` (41), `test_permission_resolver_seam.py` (21),
`test_hosted_readonly_posture.py` (13), `test_allowlist_roster.py` (10),
`test_google_token_verifier.py` (7), `test_auth.py` (7), `_auth_fixtures.py` (4),
`test_auth_identity_seam.py` (3). Every one references symbols packet 39's build will CREATE
(`resolve_posture`, `PostureConfigError`, `derive_edge_policy`, `Posture`, `SCOPE_READ`).
**None of packet 46's files appear in the error set** — grepped `server.py`, `extension.py`,
`_extension_helpers.py`, `test_server.py`, `test_search.py`, `test_server_chunker_wiring.py`,
`test_extension.py`: all ABSENT. Packet 46 introduced ZERO new typecheck errors.

**Re-derived the "191 baseline" number (brief cited 191; I measured 102 raw errors).**
Reconciled, NOT a contradiction: the currency gate reports `typecheck RED_ADJUDICATED — 191
residual(s), owned by packet-39-pending-build`. The **191 is the manifest's adjudicated-residual
allowlist size**; **102 is the count of errors my run actually produced**, all a subset of that
owned allowlist (packet-39 files self-destruct from the allowlist as its build lands, so the live
count is ≤ the allowlist). The invariant that matters — ADJUDICATION, not greenness — holds:
currency PASS, zero RED_ORPHANED. (pytest leg likewise `RED_ADJUDICATED — 444 residual(s)`, owned
by packet-39-pending-build.)

**Touched suites, each with a passed-COUNT (`-n auto`, my runs):**

| suite | count |
|---|---|
| `test_extension_discovery.py` (frozen contract) | **11 passed** |
| `test_server.py` | 28 passed |
| `test_extension.py` | 47 passed |
| `test_server_chunker_wiring.py` | 21 passed |
| (above three run together) | **96 passed** |
| `test_tool_allowlist.py` + `test_lifespan_framework.py` | **36 passed** (30+6) |
| `test_search.py::TestExtensionHooks` (migrated) | **3 passed** |
| `test_mcp_server.py` (structural/AST registration + dead-name + instructions pins) | **669 passed** |

All GREEN. No failing test anywhere in the scoped set. (Did NOT run the full suite — verification
law; the cold audit re-runs the scoped set + gates, and currency covers orphan status.)

---

## §MUTATION — 4 proofs re-run independently in a PROVENANCE-ASSERTED scratch (#140)

Scratch built with `./scripts/scratch_copy.sh /home/ejprice/scratch-coldaudit-46-1` (provenance
asserted non-zero-on-poison by the tool). Independent receipt printed from inside the scratch:

```
LOREMASTER __file__: /home/ejprice/scratch-coldaudit-46-1/loremaster/loremaster/__init__.py
```

Instrument = the committed `scripts/mutation_proof.py` (both-way declared-vs-observed RED diff).
Declared RED sets taken from `pytest --collect-only` BEFORE each run (not transcribed from output).
Both mutation anchors verified unique (`grep -c` = 1) in the scratch before mutating.

| # | mutation (anchor → replacement) | declared RED | result |
|---|---|---|---|
| 1 | `for key in self._config.extensions:` → `for key in []:` (**inert**) | 9 discovery-dependent pins (PIN 1×2, PIN 2×2, PIN 4×2, PIN 6, PIN 7×2); PIN 3 empty + PIN 5 manual-register stay GREEN | **PROOF HELD** — 9 failed / 2 passed, restored byte-exact |
| 2 | `… ` → `for key in list(self._config.extensions)[:1]:` (**first_key_only**) | PIN 7's two ∀-over-config-keys legs only | **PROOF HELD** — 2 failed / 9 passed, restored |
| 3 | `annotations=ToolAnnotations(readOnlyHint=False),` → `` (**R14 none**) | PIN 5 (`test_extension_tool_publishes_readonly_hint_false`) — `is not None` leg (line 388) | **PROOF HELD** — 1 failed / 10 passed, restored |
| 4 | `…readOnlyHint=False),` → `…readOnlyHint=True),` (**R14 true**) | PIN 5 — `readOnlyHint is False` leg (line 392) | **PROOF HELD** — 1 failed / 10 passed, restored |

All four: `PROOF HELD — the declared RED set fired EXACTLY`, restore md5 identical
(`cb1bc9a8639776722051c44cc8c798a1`) across every run. Green control on the restored scratch:
`11 passed`; `diff` of scratch `server.py` vs the real tree = IDENTICAL (clean restore).

**Brief's named checks all satisfied:** the ∀-over-config-keys pins redden (mutations 1 & 2), the
unknown-name pin reddens (mutation 1), the boots-with-extension pin reddens (mutation 1). A pin I
could not show RED against a broken build: none — every load-bearing pin was shown RED.

---

## §REFUTE — full-diff read (`git show 543ed72` / `89852b3`) with a refute frame

`_discover_extensions` (server.py, called LAST in `__init__` at line 405, after
`_build_default_registry()` + `_apply_config_chunker_overrides()`):
- **Iterates EVERY key** — `for key in self._config.extensions:` — no `[:1]`, `break`, `return`,
  or `next(iter(...))`. ✓ (mutation 2 proves the ∀ pin catches a first-key-only loop.)
- **Reads the registry LIVE off the module object** — `import loremaster.extension as
  extension_module; registry = extension_module.EXTENSION_REGISTRY`. Not an import-bound name, so a
  `monkeypatch.setattr(extension_module, "EXTENSION_REGISTRY", …)` is honored. ✓ (every injecting
  pin passes.)
- **Unknown-key error DERIVES the known set** — `known = ", ".join(sorted(registry)) or "(none
  registered)"`, message carries the exact literal `Known extensions: {known}`. It does NOT leak the
  unknown key into the known clause (the key appears only as the rejected `{key!r}` earlier). ✓
  (§TRUST Leg 1 constructs this live.)
- **Name-mismatch guard names BOTH sides** — raises `ValueError` citing `{key!r}` (registry key)
  AND `{instance.name!r}` (actual). ✓ (PIN 6.)
- **Order** — registry-membership check → instantiate → `instance.name == key` check →
  `register_extension`. Correct: unknown fails before instantiation; mismatch fails before
  registration (so the wrong-slice validation never runs silently).
- **R14** — the extension `mcp.add_tool(...)` now passes `annotations=ToolAnnotations(
  readOnlyHint=False)` (`ToolAnnotations` already imported at server.py:79). ✓
- **`EXTENSION_REGISTRY` stays `{}`** — `extension.py:393` UNCHANGED (extension.py touched by
  neither commit). Discovery is dark in production. ✓

No refutation found. Discovery is correct.

---

## §DUAL — independent removed-behavior enumeration (done BEFORE reading builder/Fable DUAL)

From the migration diff (`89852b3`) alone I enumerated what was deleted/replaced, then verified live
coverage for each, THEN compared to builder §DUAL + Fable §DUAL. **My list matched theirs; nothing in
my enumeration lacks coverage.**

| removed/replaced behaviour | fate | live coverage (verified) |
|---|---|---|
| `minimal_config()` default `{"fake":…}` → `{}` | **required change** | flip prevents bare callers boot-failing under live discovery (empty-registry unknown-key raise); the fake slice is now supplied explicitly by `fake_discovered` / `register_in_discovery` where a test wants it wired |
| `register_extension` returns-self / chains | preserved-with-pin | `test_server.py::test_register_returns_self_for_chaining` (manual `_NoConfigExtension`) — line 232 `assert … is server` |
| slice validation — VALID | preserved-with-pin | `test_valid_slice_passes` (discovery-driven, boot) |
| slice validation — BAD (extra key) | preserved-with-pin | `test_bad_slice_fails_loud` (discovery, raises at BOOT where prod raises) |
| slice validation — MISSING required (discovery-UNREACHABLE) | preserved-with-pin | `test_missing_slice_for_extension_with_a_model_fails_loud` — **KEPT MANUAL + ROLE comment** (test_server.py:387–392); confirmed it is the SOLE coverage of that branch and a fold-into-discovery would silently orphan it |
| nit-1 chunker-overlap guard (raise / greedy-refused / basename-allowed) | preserved-with-pin | `TestNit1RegisterGuard` (test_server.py:441/474/499/537) — shadow doubles rebased off bare `Extension` |
| seams 1–11 wiring | preserved-with-pin | `TestRegisterExtensionWiring` via `fake_discovered` (discovery calls `register_extension` internally with the same instance) |
| `test_search.py::TestExtensionHooks` (format-override + augment) | preserved-with-pin | 3 tests, now discovery-driven |
| test_extension.py bare `minimal_config()` callers (73/100/232/320) | SAFE | 73/100/320 carry config as an opaque `ExtensionContext` handle (extensions value never asserted); 232's `_FieldIndexDeclaringExtension` has NO config_model (slice irrelevant) — all pass under `{}` |

**Corpse-assertion sweep** (tests certifying the OLD default): `grep flavour.*vanilla` in the
untouched files = none; `grep "extensions =="` → `test_server.py:134 assert server.extensions == []`
(bare-server; correct and STRONGER under the new default) and `test_config.py:270 config.extensions
== {}` (production config-parse pin; correct). No test still asserts the retired
`{"fake":{"flavour":"vanilla"}}` default. Nothing dropped-deliberately / old-bug / spec-silent.

**One-implementation check:** `register_in_discovery` is a single shared helper in
`_extension_helpers.py` imported by BOTH `test_server.py` and `test_search.py` (not a cloned
pattern). ✓

---

## §TRUST — both legs confirmed by LIVE CONSTRUCTION (Consumer Law), not by trusting the pins

Instrument (inline probe, pasted verbatim so the claim is re-runnable), run against the real tree
read-only:

```python
import loremaster.extension as extension_module
from loremaster.extension import Extension
from loremaster.server import LoreServer, build_mcp_server
from _extension_helpers import minimal_config   # PYTHONPATH=loremaster/tests

class AlphaExt(Extension):
    @property
    def name(self) -> str: return "alpha_probe"
class BetaExt(Extension):
    @property
    def name(self) -> str: return "beta_probe"

# LEG 1 — unknown-key error names the REAL registry-derived known set, no leak
extension_module.EXTENSION_REGISTRY = {"alpha_probe": AlphaExt, "beta_probe": BetaExt}
try:
    LoreServer(minimal_config(extensions={"typo_xyz": {}}))
except ValueError as e:
    msg = str(e); known = msg.split("Known extensions:", 1)[1]
    # alpha_probe/beta_probe in known clause == True; typo_xyz in known clause == False

# LEG 2 FORGERY — EMPTY production registry + config naming an ext => LOUD, not a silent no-op
extension_module.EXTENSION_REGISTRY = {}
LoreServer(minimal_config(extensions={}))          # healthy: [] extensions, boots
LoreServer(minimal_config(extensions={"dnd": {}})) # broken:  MUST raise, not serve identical
```

Observed:
- **Leg 1** — message: `unknown extension 'typo_xyz' … Known extensions: alpha_probe, beta_probe.
  Register its class …`. Known-clause names `alpha_probe` = True, `beta_probe` = True, LEAKS
  `typo_xyz` = **False**, unknown key named as rejected = True. The served surface teaches the
  reader (an LLM) the REAL known set derived from the registry — not a hand-list, not the typo.
- **Leg 2 forgery** — healthy (empty registry, empty config) → `extensions == []`, boots. Broken
  (empty registry, config names `dnd`) → **RAISES** `unknown extension 'dnd' …`, known clause
  `(none registered)`. The broken state does NOT serve byte-identically to the healthy state ⇒
  **no false clear.** Because the registry ships `{}`, ANY `extensions:` block written today fails
  boot LOUDLY (there is no real extension until packet 51) — the intended "dark until a real
  extension lands", failing safe.
- **Positive control** — empty registry + empty config boots byte-clean (bare RAG).

---

## §STORE — store touch = NONE (structural + empirical)

- Structural: commit `543ed72` touches `server.py` ONLY; `89852b3` touches `_extension_helpers.py`
  / `test_search.py` / `test_server.py` ONLY. No store, schema, DDL, or `extension.py` file is
  touched by either commit.
- Behavioural: `_discover_extensions` → `registry.get` + `cls()` + `register_extension`
  (validate slice, register chunkers, extend spec lists, append) — none read/write the store; the
  store is entered only inside the lifespan. Every gate/probe above ran WITHOUT the SurrealDB
  harness and succeeded, which is itself proof discovery + `build_mcp_server` + `list_tools` touch
  no store. Store reference (`docs/reference/surrealdb-31-capabilities.md`) consulted; no
  store/schema/DDL decision applies.

---

## §DEVIATIONS — adjudicated

- **(a) Two commits; intermediate `543ed72` not gate-green.** ADJUDICATED **ACCEPTABLE, not a
  defect.** One-concern-per-commit IS satisfied (commit 1 = production code change; commit 2 = test
  reconciliation). Real discovery necessarily breaks the pre-existing composition suite, and the
  migration is only coherent once discovery is live — the two are mutually dependent, so no single
  atomic step makes both green without merging code + test into one commit. FINAL HEAD `89852b3` is
  green on every touched suite (verified). Cost is bisect-cleanliness only; pre-production repo,
  NO DEPLOY. Recommendation: accept as-is (or squash the pair at a future merge if bisectability is
  wanted). Not a blocker.
- **(b) scratch `rm -rf` sandbox-denied.** Housekeeping. My scratch at
  `/home/ejprice/scratch-coldaudit-46-1` (and the builder's `scratch-pkt46-builder`) can be removed
  by the lead. Nothing load-bearing lives there. Not a blocker.

---

## §RESIDUALS — individual verdict per item (read this table, not just the summary)

| # | residual | verdict |
|---|---|---|
| R1 | Brief cited "191 baseline"; raw typecheck shows 102 errors | **Reconciled, informational.** 191 = manifest adjudicated-residual allowlist; 102 = live errors ⊆ allowlist; currency PASS zero-orphans; none in pkt-46 files. No action. |
| R2 | Intermediate commit `543ed72` RED | **Accept** (deviation a). Not a blocker; optional squash at merge. |
| R3 | scratch dirs undeletable (sandbox) | **Housekeeping.** Lead may `rm -rf`. Not a blocker. |
| R4 | Intermediate-commit test state not independently re-run (checkout forbidden) | **Bound stated.** Final HEAD verified in full; intermediate state taken from builder characterization only. Not a blocker. |
| R5 | R14 premise "all 15 built-ins carry annotations" not independently re-verified | **Out of pkt-46 scope, pre-existing.** `test_mcp_server.py` (669 green) carries the built-in annotation pins. PIN 5 proves the EXTENSION tool's posture, both directions. No action. |

---

## VERDICT: **GO**

Packet 46 is ready to mark DONE. The frozen 11-pin contract is satisfied by implementation (contract
untouched); all four mutations reddened exactly their declared pins in a provenance-asserted scratch;
both Trust legs pass by live construction (unknown-key teaches the real derived set with no leak;
empty-registry + a named extension fails LOUDLY, no false clear); the removed-behavior inventory is
complete with every item preserved-with-pin and the discovery-unreachable missing-slice branch kept
manually pinned; store touch is NONE; ruff clean; typecheck zero-new-delta; currency PASS. No blocker.
NO DEPLOY this packet (discovery ships dark; `EXTENSION_REGISTRY == {}`).
