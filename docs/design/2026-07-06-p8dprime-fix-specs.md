# P8d′ fix specs — findings #53 / #52 / #54

**Author:** designer-p8dprime (design-only agent, 2026-07-06)
**Tree analyzed:** `feat/surreal-unification` @ d3ea4d9, plus 13faa6a
(`fix(search): tier-only filter misses teach tiers, not paths (#54 partial)`) which
landed mid-analysis — every file:line below re-verified against 13faa6a.
**Evidence base:** docs/plans/v2/receipts/2026-07-04-p8a/p8d-flip-eval-raw.md (35 transcripts),
docs/plans/v2/receipts/2026-07-04-p8a/2026-07-04-p8a-baseline.md (per-task baseline table),
findings #52/#53/#54
(full bodies via `lore_findings get`), live repro calls against the deployed
(defective) MCP, and direct source reads. Live tool output was used to REPRODUCE
only, never trusted (resume-doc degraded-surface warnings applied).
**Address note (added 2026-07-29):** every `docs/eval/…` evidence path this document cited
was archived to `docs/plans/v2/receipts/2026-07-04-p8a/` at `439b55d` (packet 44). The paths
above and in §3.1 are updated; **the bytes are unchanged** (all six moved as 100%-similarity
`git mv` renames), so every number derived from them below stands unaltered.

These specs are written to be handed to sonnet builders verbatim. Every design
decision is made here; an open question in a spec is a spec defect — flag it to the
lead, do not resolve it unilaterally.

**Shared file overlap (lead sequencing note):** SPEC 1 and SPEC 2 both touch
`graph_surreal.py`, `_surreal_fakes.py`, `test_graph_surreal.py`. Run SPEC 1's
builder first (the heavy hitter), SPEC 2's second on the updated tree. SPEC 3's
tweaks are independent of both except tweak T6 (touches `impact.py`, after SPEC 2).

---

## SPEC 1 — #53: `lore_impact` false "dead / 0 refs" on from-imported modules

### 1.1 Defect statement (reproduced live this session)

`lore_impact("loresigil.factory", depth=1)` at HEAD serves:

```
verdict: dead (heuristic)
0 prod / 0 test references
tests: 1 (loresigil.tests.test_factory)
consumers: (none)
```

while `loremaster/loremaster/embedding.py` genuinely does
`from loresigil.factory import make_embedder, ...`. The graph HAS the edges —
`lore_map(focus="loresigil.factory")` reaches `loremaster.…embedding` as sole
non-test consumer, and pre-flip `lore_what_imports` served the same edges.

### 1.2 Where the path loses the from-import edges (receipts)

The astroid derivation records a `from <module> import <symbol>` edge with
**dst = the resolved SYMBOL fqn** (`loresigil.factory.make_embedder`), never the
bare module name. This is documented design: `graph_surreal.py:1040-1046`
(what_imports docstring) and `index/indexer.py:735-736` ("unifying a node's name
with the `imports`-edge `dst` strings").

- `impact.py:287` — `summary = await self._graph.references(target)` is the ONLY
  source of counts and depth-1 consumers.
- `graph_surreal.py:1318-1327` — `references()` builds its dst match set as
  `{name, bare(name)}` (plus the bare-name bridge, gated to `name == bare` — never
  fires for a dotted module target).
- `graph_surreal.py:1329-1338` — the refers query
  `WHERE kind IN $kinds AND out IN $names` therefore never matches an edge whose
  dst is `loresigil.factory.make_embedder`. **This is the loss site.**
- `impact.py:294-296` — `direct_consumers` derives from the (empty)
  `summary.referencing` → `[]`.
- `impact.py:313` — `verdict = dead` because `production_references == 0`.
- Why not-found does NOT fire (and mustn't): `impact.py:454` probes
  `blast_radius(target, 1, 1)`; `_reverse_neighbours` HAS the module-prefix arm
  (`graph_surreal.py:1193-1211`) so the probe is truthy.

The engine method with the correct semantics already exists: `what_imports()`'s
**module-prefix arm** at `graph_surreal.py:1070-1081` —
`_names_with_value_prefix([f"{target}."])` (a trailing-dot-anchored, index-pushed
range query, ledger #30) unioned into an **imports-only** refers query.
`references()` simply lacks that arm.

Confirmed asymmetry (live receipt this session): `lore_dead_code` does **not**
false-negative `loresigil.factory` — its module verdict rolls up symbol-level
references (`graph.py::_liveness_sources`), and the from-import edges DO exist at
symbol dst level. The defect is confined to `references()`'s dst-matching, i.e. to
`lore_impact` (and any other `references()` caller — see blast radius, §1.6).

### 1.3 Fix contract

**Change ONE seam: `SurrealCodeGraph.references()` gains the same imports-only,
trailing-dot-anchored module-prefix arm `what_imports()` already has. Mirror, do
not re-implement differently.** Additionally extend `tests_for()` with the same
arm (§1.3.3). `impact.py` itself changes NOT AT ALL.

#### 1.3.1 `references()` (graph_surreal.py:1282)

After the existing `name_ids_by_key` construction (~line 1327), add:

1. `prefix_name_ids = await self._names_with_value_prefix([f"{name}{_QUALIFIER_SEPARATOR}"])`
2. If non-empty, run a SECOND refers query selecting the same projection as the
   main query (`_EDGE_IN`, `_COL_SRC_FILE_PATH`) with
   `WHERE {_COL_KIND} = $kind AND {_EDGE_OUT} IN $names`, `kind = EDGE_IMPORTS`
   (imports-ONLY — mirroring what_imports:1082-1092; a `calls`/`inherits` edge to a
   symbol under the prefix is a reference to the SYMBOL, not the module).
3. Feed those rows through the SAME classification loop (production/test split by
   `_is_test_path(src_file_path)`, self-reference exclusion via
   `source_qname in target_names`, dedupe via `referencing_ids[str(source_id)]`).
   The existing loop body is reused verbatim — extract it or extend the `rows`
   list before the loop; builder's choice of mechanics, identical semantics.

**Why the arm is UNGATED (no "is this a module?" pre-check), and why that is safe:**
the `kind = imports` filter is itself the module-ness gate. An imports-kind edge
whose dst lies strictly under `<target>.` can only come from an import statement,
and Python can only import from a module path — so for a genuine class/function
target no such edge exists. This is the exact argument `what_imports` already
documents ("strictly ADDITIVE and harmless for a symbol target",
graph_surreal.py:1044-1046) and pins
(`test_symbol_target_lookup_is_unaffected_by_the_module_target_fix`,
test_graph_surreal.py:1043). The only overlap case — a module whose dotted name a
symbol also carries — unions both profiles, consistent with the existing
bare-name-union philosophy (impact.py:143-148). Cost: one index-pushed range query
plus at most one extra refers query per `references()` call.

**Semantics note to carry into the docstring (package targets):** the prefix arm
gives Kùzu-parity semantics — for a PACKAGE target (`loresigil`), an import of any
symbol resolved under `loresigil.` counts as a reference to the package, exactly
as `what_imports` already behaves. Self-references remain excluded (a source whose
composite qname equals the target never counts).

#### 1.3.2 New behavior for module targets (the contract impact inherits for free)

For a module M with importers:

- `production_references` / `test_references`: distinct source qnames from the
  union of the base arm (plain `import M` edges, dst = M) and the prefix arm
  (`from M import x` edges, dst = M.x), split by source file path. Sources are the
  importing MODULE nodes (imports live at module level), whose qualified names are
  canonical node identity (live receipt: consumers render as `loremaster.diff`,
  `loremaster.tasks`, … — see SPEC 2 §2.2 for the identity proof).
- `direct_consumers` (depth 1): the production-side referencing node names —
  falls out of `_production_consumer_names` unchanged.
- `verdict`: `live` iff production_references > 0 — falls out of impact.py:313
  unchanged.
- `covering_tests`: see §1.3.3.
- depth>1 rollups: unchanged mechanics (blast_radius already had the arm).

#### 1.3.3 `tests_for()` (graph_surreal.py:1214)

Add the SAME imports-only prefix arm to arm (1) of `tests_for`: alongside the
existing `name_ids` refers query, also collect `(src_tier, src_file_path)` pairs
from an imports-only refers query over `_names_with_value_prefix([f"{symbol_or_file}."])`,
filtered to test paths, merged into the same `test_pairs` set. Rationale: a test
file that `from M import x`-imports module M covers M; today it is reached only if
the `test_x ↔ x` name heuristic happens to fire (live repro: `test_factory` was
found by name-luck, not by reference). Additive-only: dedupe is by node id in the
existing `related` dict.

#### 1.3.4 Exact render for the pinned repro (post-fix, live server)

```
impact: loresigil.factory
verdict: live
1 prod / <T> test references
tests: <M> (…, loresigil.tests.test_factory, …)
consumers: loremaster.embedding
caveat: <unchanged _CAVEAT_TEXT>
```

No render-shape change of any kind: no new lines, no new caveat text, no changed
templates in `impact.py::_render`. `<T>`/`<M>` are measured at build time from the
fixture/live corpus, never guessed; the spec pins **prod == 1** and
**consumers == ["loremaster.embedding"]** exactly (that is pair 9's ground truth:
"exactly one NON-TEST module"), and `loresigil.tests.test_factory ∈ covering_tests`.

### 1.4 What does NOT change — and how the builder proves it

1. **Symbol-target behavior is byte-stable.** Proof obligations:
   - `test_impact.py`, `test_graph_surreal.py`, `test_search.py`, `test_map.py`
     run green **with zero edits** (the builder pastes passed-count tails). Any
     edit these files "need" is a red flag to report, not make.
   - New pin (mirroring test_graph_surreal.py:1043's idiom): in a corpus where a
     module has BOTH from-import importers and a separately-referenced symbol,
     `references(<symbol fqn>)` returns counts/sets identical to the literal
     expectation written before the fix (author the test against the PRE-fix
     engine, show it green pre-fix if practical, keep it green post-fix).
2. **`what_imports`, `blast_radius`, `_reverse_neighbours`, `dead_code`,
   `_reference_source_index` untouched.** dead_code regression guard: the module
   roll-up already counts from-imports (asymmetry receipt §1.2) — assert
   `loresigil-factory`-shaped fixture module is absent from dead_code output in
   the new test corpus.
3. **impact.py untouched** (no code change; its docstring already describes
   `references` correctly).
4. **Render templates untouched** (the AST text-hygiene invariant and the
   exact-set/served-text pins in test_mcp_server.py must stay green — run them).

### 1.5 Test contract (contract-first; RED receipts required in the report)

New class `TestReferencesModuleTarget` in `test_graph_surreal.py`, mirroring the
existing `TestWhatImportsModuleTarget` (test_graph_surreal.py:970-1057) corpus
idioms against the spike-surreal harness, plus a `TestTestsForModuleTarget`:

1. **Cross-package from-import (the loresigil.factory repro shape):** package
   `rlib/` (with `__init__.py`) containing `factory.py`; separate top-level
   `consumer.py` doing `from rlib.factory import make_widget`. Assert
   `references("rlib.factory")` → production_references == 1, referencing
   contains the consumer module node; impact-level: verdict "live".
2. **Same-package from-import:** `rlib/user.py` doing
   `from rlib.factory import make_widget` → counted, source qname is
   `rlib.user`, not excluded.
3. **Sibling-stem no-leak (mirror :1022):** modules `pkg/a.py` and `pkg/ab.py`
   with an importer of `pkg.ab`'s symbol — `references("pkg.a")` gains nothing
   (trailing-dot anchor).
4. **Plain-import regression pin:** `import rlib.factory` (base arm) still counts
   exactly once alongside a from-import from the same source (dedupe by source).
5. **Symbol-target byte-stability pin** (§1.4.1).
6. **Self-reference exclusion:** the target module's own composite qname never
   appears among its referencing sources.
7. **tests_for module target:** a test file (`tests/test_widget_use.py`, name NOT
   matching the module stem — defeat the name heuristic deliberately) that
   from-imports `rlib.factory` appears in `tests_for("rlib.factory")`.
8. **Engine-level (test_impact.py, fake graph):** module target renders
   live/counts/consumers through `ImpactEngine.impact` unchanged render shape.
   ⚠ The fake (`_surreal_fakes.py`) must gain the SAME prefix-arm semantics in
   its in-memory `references`/`tests_for` walks — adversarial-double law: fix the
   double to the real contract first so the engine test can go RED honestly.

Post-deploy live receipt (lead's step, record in gate notes):
`lore_impact("loresigil.factory")` → `live`, `1 prod`, consumers exactly
`loremaster.embedding`.

### 1.6 Blast radius of the changed seam

`references()` production callers (grep receipt, whole repo):
- `impact.py:287` — the intended fix consumer.
- `search.py:649` (`_enrichment_lines`) — **provably unaffected in behavior
  class**: enrichment targets are filtered to signature-carrying hits
  (functions/methods, search.py:630-636), so `references()` is never called with
  a module name there; for symbol names the arm is a no-op (§1.3.1). Also
  fail-soft by design. `test_search.py` green-unmodified is the receipt.

`tests_for()` production callers: `impact.py:362`, `search.py:650` — same
argument, same receipts.

### 1.7 Writable set (builder)

- `loremaster/loremaster/graph_surreal.py` (`references`, `tests_for`, their
  docstrings)
- `loremaster/tests/test_graph_surreal.py` (new test classes)
- `loremaster/tests/test_impact.py` (module-target engine test)
- `loremaster/tests/_surreal_fakes.py` (mirror the arm in the fake walks)
- `REPORT-<builder-name>.md`

Do-not-touch: `impact.py`, `map.py`, `search.py`, `server.py`, everything else.
Gates: scoped pytest (the four test files above), `uv run ruff check .`,
`scripts/typecheck.sh`. Never the full suite.

---

## SPEC 2 — #52: canonical map labels (`loremaster.loremaster.X` → `loremaster.X`)

### 2.1 The critical question, answered with receipts

**The doubled name is NOT graph-node identity. It IS the MapEngine's internal
pipeline key AND its rendered label, re-derived per call from file paths — plus
two sibling render sites (impact depth>1 rollups, the server's changed_since
resolver). Nothing doubled is persisted; no store migration is involved.**

Identity receipts (all from this session):
- Live `lore_impact` consumers render `loremaster.diff`, `loremaster.findings`,
  `loremaster.graph_surreal`, `loremaster.tasks`, `loremaster.memory.local` —
  canonical, single package segment. These are graph-node qualified names.
- Live `lore_dead_code` rows: every `qualified_name` canonical
  (`loremaster.auth.ApiKeyVerifier.remove_key`, …).
- Source: the indexer passes the TRUE importable name into node construction —
  `index/indexer.py:742` and `:884` (`_importable_module_name`), consumed at
  `graph_surreal.py:861` (`module_name if module_name is not None else …`), with
  the doubled-member-dir fix implemented in
  `graph.py::importable_module_name` (:344-386). Design intent stated verbatim at
  indexer.py:874-878: *"a workspace-member file `loremaster/loremaster/config.py`
  becomes the importable `loremaster.config`, not the doubled
  `loremaster.loremaster.config`."*

Doubled-derivation sites (the divergence from that intent):
- `map.py:498` — `_extract_module_graph`: `module = self._graph.module_qualified_name(node.file_path)`
  keys the WHOLE pipeline: vertex set, `out_edges`, `symbols_by_module`,
  `module_is_test`, `symbol_owners`, the §SB-1 focus whole-string match
  (map.py:342-343), the changed_since intersection (map.py:393), and the label.
- `map.py:566` — `_resolve_focus_personalization`, same derivation.
- `impact.py:396` and `:422` — depth>1 module rollup labels (same doubled class).
- `server.py:2763` — `_resolve_changed_modules` derives changed-module names with
  the same path-join, deliberately matching map's (doubled) keys today.

### 2.2 The hidden second symptom this fix also closes (builder must expect it)

Because map keys ≠ node identity, `map.py:515`
(`if importer_module in out_edges`) **silently drops production-package import
edges**: `what_imports()` returns importer nodes whose `qualified_name` is
canonical (`loremaster.diff`), which is never a key in the doubled `out_edges`
dict. Additionally `what_imports(<doubled key>)` at map.py:512 can't use its
module-prefix arm (nothing is resolved under `loremaster.loremaster.…`), so
from-import edges never reach the map at all. Live receipt: the unfocused default
map pins most production modules at the uniform teleport floor (rank 0.0044) —
the production import graph is largely invisible to PageRank today.

**Consequence: fixing the key restores real edges and CHANGES RANK VALUES.** That
is a correction, not a regression — but every rank-derived receipt (evaluation.xml
pairs 12/13) must be re-derived live post-fix (§2.6). This is why the fix is
"identity-consistent keys", not "canonicalize at print time": a print-time-only fix
would leave the edge-drop defect in place and leave `focus=<canonical name>`
(the exact string the tool's own §7a trailer teaches, post-fix) unresolvable.
Scope stays engine-internal — genuinely small — because node identity already IS
canonical; nothing outside the four derivation sites moves.

### 2.3 Canonical form, precisely

**The module label ≡ the module NODE's qualified_name (node identity).** That
identity is already:
- importable path relative to the package root for real packages
  (`loremaster/loremaster/embedding.py` → `loremaster.embedding`;
  `__init__.py` collapses: `loremaster/loremaster/calibration/__init__.py` →
  `loremaster.calibration`);
- the full tier-relative path join for NON-importable files — no `__init__.py`
  anywhere in the chain (graph.py:356-359 fallback):
  `skills/lore-deploy/scripts/lore_deploy.py` → `skills.lore-deploy.scripts.lore_deploy`,
  `loremaster/tests/test_map.py` → `loremaster.tests.test_map`. Path-derived is
  the honest label there; **no new policy is invented — the policy IS "label
  equals node identity"**.
- Non-Python files: no graph nodes → never labeled by map/impact. The
  changed_since resolver may see them (diff FileRefs); they take the defensive
  fallback (below) and can never match a rendered module — benign, documented.
- Defensive fallback everywhere: a file with no module node in the mapping labels
  as `CodeGraph.module_qualified_name(file_path)` (today's behavior), so a
  half-purged store can't KeyError.

### 2.4 Mechanism (all four sites)

1. **`map.py::_extract_module_graph`** — in its existing single pass over
   `all_nodes()`, first collect
   `module_name_by_file: dict[tuple[str, str], str]` from `kind == KIND_MODULE`
   nodes keyed `(node.tier, node.file_path)` (GraphNode carries `tier`; the fake
   constructs it at _surreal_fakes.py:1300-1308 — builder verifies the real
   `_row_to_node` decodes it too, graph_surreal.py:582), then attribute EVERY
   node via mapping-lookup-with-fallback. Zero extra queries. Return/thread the
   mapping so `map()` can hand it to `_resolve_focus_personalization`
   (extraction at map.py:325 already runs BEFORE focus resolution at :330 —
   thread as a parameter; `_resolve_focus_personalization` replaces its :566
   derivation with the same lookup+fallback).
2. **New public engine read method** on `SurrealCodeGraph` (+ the fake):
   `async def module_names_by_file(self) -> dict[tuple[str, str], str]` — one
   `SELECT {_COL_TIER}, {_COL_FILE_PATH}, {_COL_QUALIFIED_NAME} FROM {CODE_NODE_TABLE}
   WHERE {_COL_KIND} = $module_kind` (columns exist: graph_surreal.py:150-154).
   Docstring: names its two consumers and the fallback contract.
3. **`impact.py::_module_rollups` (:384) and `_transitive_only_modules` (:405)** —
   fetch `module_names_by_file()` ONCE per `impact()` call **only when
   depth > 1** (the depth-1 path pays nothing), thread it to both helpers,
   attribute via lookup+fallback instead of `module_qualified_name(node.file_path)`.
4. **`server.py::_resolve_changed_modules` (:2740-2765)** — fetch
   `module_names_by_file()` once, map each `FileRef` (`tier` + `file_path`,
   diff.py:208-214) through lookup+fallback. A REMOVED .py file's nodes are
   purged so it misses the mapping → fallback name → cannot match a rendered
   module — equivalent to today (its module isn't in the vertex set either);
   document in the docstring, do not special-case.
5. **Prose sweep (NL-surface law):** update the docstrings that teach the old
   derivation — `MapEntry.module` (map.py:195-197), `ModuleRollup.module`
   (impact.py:177), `_resolve_changed_modules` (server.py:2746-2747), and the
   `module_qualified_name` mentions in map.py/impact.py section comments. Sweep
   grep (bare, anchor-free): `module_qualified_name` over `loremaster/` — every
   residual hit gets a file:line + one-word verdict in the builder report
   ("all remaining hits are X" is banned output).

### 2.5 What changes / what must not

Changes (accepted, by design):
- Map labels and internal keys become canonical (`loremaster.server`).
- `focus=` accepts canonical module names (and the §7a/§3 trailers now print
  strings that round-trip as focus values — assert this).
- Map edge sets grow (restored production edges; what_imports' prefix arm becomes
  effective under canonical keys) → rank VALUES move corpus-wide.
- impact depth>1 rollup labels become canonical.
- `[changed]` tagging keys become canonical on both sides simultaneously
  (map keys + resolver output) — no split-brain window because both read the
  same new method/mapping in the same commit.

Must NOT change (proof = named tests green unmodified):
- Test segregation, elision lines, symbol caps, auto-invert, budget invariant,
  determinism order (test_map.py's fixtures are FLAT paths — canonical ≡
  path-derived there, so its behavior pins hold; grep receipt: zero doubled-name
  pins exist in test_map.py).
- `get_symbol`'s deliberate ACCEPTANCE of doubled INPUT forms
  (test_symbols.py:279-370) — a different subsystem (chunk-store resolution),
  untouched; those tests green unmodified.
- Graph node identity, indexer naming, `references`/`what_imports`/`blast_radius`
  semantics (beyond SPEC 1's arm).

### 2.6 Every pin that moves

| Pin | Where | Disposition |
|---|---|---|
| Pair 13 question parenthetical *"(its rendered label may repeat the top-level package directory name)"* + answer `loremaster.loremaster.server` | loremaster/evaluation.xml:100-103 | **Re-amend back to canonical**: drop the parenthetical, answer → `loremaster.server`. NOTE EXPLICITLY: this REVERSES eval-runner-1's 2026-07-06 amendment (xml:84-99, which baked the doubled label in as graded truth); rewrite that receipt comment. The numeric claims ("clears 0.25", "ties near 0.07") were measured on the broken-edge graph — RE-DERIVE live post-deploy and reword thresholds if the values moved. |
| Pair 12 receipt ranks (lore_deploy 0.0195 top) | loremaster/evaluation.xml:72-82 | Ground truth is rank-derived → RE-DERIVE the top-ranked module live post-deploy; answer may change once production edges count. (Wording amendment for its tests=true ambiguity is SPEC 3 §3.4 — do both edits in one pass.) |
| test_map.py behavior pins | loremaster/tests/test_map.py | None move (flat-path fixtures). Builder runs the file green UNMODIFIED and reports the tail; any "needed" edit is a flag. |
| test_impact.py rollup pins | loremaster/tests/test_impact.py | None move (pkg.* fixtures). Same green-unmodified receipt. NEW test: doubled-layout corpus rollup labels canonical. |
| test_graph_wiring.py / test_mcp_server.py | — | Grep sweep `loremaster\.loremaster` (bare pattern) over the whole test tree: known hits are test_graph.py:628, test_symbols.py:279/308/339/370, test_logging_setup.py:203 — all pin OTHER features (importable_module_name unit tests, get_symbol doubled-input resolution, logger names); verdict each individually in the report; none should need edits. |

New tests (contract-first, RED receipts):
1. **Doubled-layout map test (test_map.py):** tmp corpus `outer/outer/mod.py`
   + `outer/outer/__init__.py` (+ a consumer importing `from outer.mod import f`)
   built through the real indexer path so module_name is importable. Assert:
   entry label is `outer.mod` (never `outer.outer.mod`); `focus="outer.mod"`
   resolves and lifts its own cap; the consumer edge registers (rank(outer.mod) >
   the uniform floor of an edge-free sibling).
2. **Trailer round-trip:** the §7a trailer's `focus=<module>` string, fed back as
   `focus`, resolves (SB-1 under canonical keys).
3. **Fallback:** a node whose file has no module node labels via
   `module_qualified_name` (construct with the fake).
4. **Rollup labels (test_impact.py):** depth>1 rollup over the doubled-layout
   corpus renders `outer.mod`-style modules.
5. **`module_names_by_file()` contract (test_graph_surreal.py):** returns exactly
   the module-kind nodes keyed (tier, file_path); empty store → empty dict.
6. **changed_since canonical (test_graph_wiring.py or test_map.py, wherever the
   existing changed_since tests live):** the `[changed]` tag lands on a canonical
   module key end-to-end through the resolver.

### 2.7 Writable set (builder)

- `loremaster/loremaster/map.py`, `loremaster/loremaster/impact.py`,
  `loremaster/loremaster/graph_surreal.py` (new read method only),
  `loremaster/loremaster/server.py` (`_resolve_changed_modules` only)
- `loremaster/tests/test_map.py`, `test_impact.py`, `test_graph_surreal.py`,
  `_surreal_fakes.py` (mirror `module_names_by_file`), and the file that hosts the
  changed_since wiring tests
- `loremaster/evaluation.xml` — pairs 12/13 + their receipt comments ONLY, and
  ONLY at the post-deploy re-derivation step (lead-sequenced; needs the live
  fixed server)
- `REPORT-<builder-name>.md`

Do-not-touch: indexer, graph.py naming helpers, search.py, symbols.py, the frozen
pairs 1-11. Gates: scoped pytest + ruff + typecheck.sh; never the full suite.

---

## SPEC 3 — #54: the turn-cost regression — analysis + targeted tweaks

### 3.1 Per-task turn-cost delta table (gate: frozen pairs 1-11)

Baseline = docs/plans/v2/receipts/2026-07-04-p8a/2026-07-04-p8a-baseline.md run 3
(11/11 · 5.45 · 1447.1).
Flip = docs/plans/v2/receipts/2026-07-04-p8a/p8d-flip-eval-raw.md tasks 1-11
(10/11 · 9.64 · 2051.8; sums
re-verified from the raw per-task numbers: 106 calls, 22,570 output tokens).

| # | Baseline calls (mix) | Flip calls (mix) | Δcalls | Δout-tok | Attributed cause(s) — from the transcripts |
|---|---|---|---|---|---|
| 1 | 4 (search×3, read×1) | 6 (search×3, read, get_symbol, verify) | +2 | +487 | New-tool rigor (verify+get_symbol adoption); elision notices flagged in feedback |
| 2 | 2 (search×1, get_symbol×1) | 5 (search×3, get_symbol, read) | +3 | +738 | Memory noise: transcript — first search "mostly memory hits"; budget elision → re-query |
| 3 | 11 | 10 | −1 | −273 | Improved (found the answer partly via the committed baseline doc) |
| 4 | 6 | 11 (search×6, read×2, get_symbol×2, verify) | +5 | +321 | Path filter-miss retries ("indexer.py", "loremaster/index/indexer.py" both rejected — feedback names it); +verify |
| 5 | 11 | 9 | −2 | −218 | Improved |
| 6 | 7 | 14 (search×9, read×4, get_symbol) | +7 | +583 | Memory noise (calibration memories crowding, per feedback); nested-path (`loresigil/loresigil`) confusion |
| 7 | 3 | 6 (search×4, get_symbol, read) | +3 | +538 | Memory noise (feedback: "initial searches returned memory entries") |
| 8 | 8 | 19 (search×14, read×3, recall×2) | +11 | +1599 | Worst case: memory/doc wandering + rejected `path="docs/design"` prefix filter + elision loops |
| 9 | 3 (search, **what_imports**, read) | 10 (search×5, impact, read×2, map×2) | +7 | +1245 | **#53**: impact lied ("dead, 0 refs") → multi-call recovery; **#52** doubled label then broke the answer; tier-arm miss rendered path wording (fixed at 13faa6a) |
| 10 | 2 (search, **tests_for**) | 11 (search×7, impact, read×2, get_symbol) | +9 | +1331 | Folded one-call verb lost: 7 searches before discovering impact's covering-tests view; 277-entry covering list slowed extraction |
| 11 | 3 | 5 (search×4, read) | +2 | +301 | +1 search; memory hits actually helped here |
| Σ | 60 | 106 | **+46** | **+6652** | |

Cause attribution over the +46 calls: memory-noise/elision re-query loops ≈ +20-24
(T2/6/7/8/11 + fractions); #53-recovery + lost one-call verbs ≈ +16 (T9+T10);
path/tier filter-miss retries ≈ +4 (T4, T8); new-verify/get_symbol rigor ≈ +3
(T1/T4); improvements −3 (T3/T5). Model feedback sections independently corroborate:
memory-noise complaints in 9 of 11 gate tasks; elision-notice complaints in 8;
path-exactness complaints in 5.

### 3.2 Root cause of the accuracy miss (gate) — already covered

Task 9 = tool defect (#53 compounded by #52), fixed by SPECs 1+2. Pair 9 is frozen
and needs no amendment — post-fix, `lore_impact("loresigil.factory")` answers it
in one call with the canonical consumer name.

### 3.3 Root cause of the 3 non-gate misses (forward set, 31/35; the fourth miss is task 31)

| Task | Miss | Classification | Amendment (pairs 12-35 are amendable) |
|---|---|---|---|
| 12 | answered `loremaster/tests/_surreal_harness.py` (ran tests=true, max budget) vs GT `skills/lore-deploy/scripts/lore_deploy.py` | **Pair defect** (view ambiguity: "the entire indexed repository" invited tests=true; GT was derived from the default production view). Secondary: model error (question said "application source AND deployment/tooling scripts", not tests) | Reword: "…ranking every module by the map's DEFAULT production view (test infrastructure excluded from the rendering)…". ⚠ GT additionally invalidated by SPEC 2's edge restoration — re-derive the top module live post-deploy before re-freezing (SPEC 2 §2.6). |
| 21 | substantively correct sentence ("…the correct name … is `LocalMemoryBackend` …") graded ❌ by exact/strict match | **Pair defect** (answer format unpinned for a strict grader) | Append: "Answer with just the class name." |
| 31 | answered `_dir_is_excluded` vs GT `_dir_excluded` | **Pair defect**: two defensible predicate methods exist — `_dir_is_excluded` (the observer-side delegate, watcher.py:155-164) and `_dir_excluded` (the LiveWatcher method actually wired as `is_dir_excluded=self._dir_excluded`, receipt at xml:263-265). The model traced BOTH and chose the lower delegate | Disambiguate: "…via one dedicated predicate method defined on the LiveWatcher class itself (the method the watcher wires into its observer as the exclusion predicate) — not the observer-side delegate that receives it." |

### 3.4 Targeted tweak list (description/teach/render only), ranked by expected value

Savings estimates are against the +4.19 avg-calls / +605 avg-tokens gap; they are
directional (transcript-derived), to be settled by the gate re-run.

| # | Tweak | Layer | Files (writable set) | Expected saving | Status |
|---|---|---|---|---|---|
| T1 | Tier-only filter miss teaches configured tiers, not path wording | render | server.py | ~−0.2 avg calls (T9-class) | **ALREADY LANDED — 13faa6a.** Verify baked at redeploy; do not re-spec |
| T2 | `lore_impact` description names its folded one-call verbs and module capability: add, early, "…for a MODULE target it lists the modules that import it (the former what_imports), and for any target its covering tests (the former tests_for)" — so "who imports X" / "what tests cover X" route to impact FIRST | description | server.py (impact description string), test_mcp_server.py (hygiene pins re-run; ⚠ the AST text-hygiene invariant + no-dead-tool-names pin: phrase as "the former …" ONLY if the retired-name scan permits historical mentions — if the pin rejects the literal retired names, use "module importers in one call / covering tests in one call" phrasing instead; both variants pre-approved here) | ~−1.3 avg calls (T9→~3, T10→~2-3, jointly with SPEC 1) | Ready |
| T3 | Search render: segregate memory hits into a trailing `memories:` block, code hits first, memory hits capped (3) with their own counted elision notice; memory bodies keep routing through the shared sanitiser seam (repo law) with a hostile fixture | render | search.py, server.py (render seam), test_search.py | −0.8 to −1.5 avg calls (T2/6/7/8 class) | Ready |
| T4 | Elision-notice enrichment: name the top elided hit (identity + score) and a concrete "raise budget to ~N to see all K" hint | render | search.py (notice builder), test_search.py (erratum: builder lives in server.py, tested in test_mcp_server.py) | −0.3 to −0.5 avg calls | Ready |
| T5 | `path` param description sharpens to lead with the miss-shape: "EXACT indexed file path (e.g. 'loremaster/loremaster/server.py') — never a directory, basename, or prefix" | description | server.py, test_mcp_server.py | small, free (T4/T8/T23/T25/T33 class) | Ready |
| T6 | Covering-tests render rolls up by FILE when one file dominates: `tests: 277 across 1 file (loremaster.tests.test_mcp_server)` — structured field stays full (finding #39 precedent) | render | impact.py (_render tests line), test_impact.py | token-side mainly (T10/T17 feedback); ~−100 avg tok | Ready (after SPEC 2 lands — impact.py overlap) |
| T7 | Raise lore_search default budget 1100 → ~1600 (8/11 gate tasks hit elision at 1100) | schema default | server.py | ~−0.5 avg calls but +input tokens per call; net ambiguous | **OPERATOR-DECISION** (schema-visible default change) |
| T8 | `memories=` include/exclude parameter on lore_search | schema addition | server.py | overlaps T3 | **OPERATOR-DECISION** (schema/surface change; T3 may make it moot) |
| T9 | Re-expose what_imports/tests_for as standalone tools | surface re-expansion | — | — | **NOT RECOMMENDED**; SPEC 1 + T2 cover the need. OPERATOR-DECISION if the re-run still misses the efficiency legs |
| — | lore_verify adoption cost (~+3 calls total across the gate) | — | — | — | **No change recommended**: verify-style checks are what kept T21/T22-class answers honest; trimming it trades accuracy for calls |

Expected combined effect (SPEC 1 + SPEC 2 + T2-T6): −3.5 to −4.5 avg calls
(9.64 → ~5.2-6.1) and −500 to −700 avg output tokens (2052 → ~1350-1550), i.e.
inside the gate's ≤-baseline exit on both efficiency legs, with pair 9 restored →
11/11 reachable. The efficiency legs are NOT reachable by description/render
tweaks alone: T9+T10 carry 16 of the 46 extra calls and need SPEC 1.

### 3.5 Gate re-run prerequisites (lead-owned, restated from the resume doc — not spec'd here)

- Fix the committed harness's own import line (`from connections import …` vs the
  vendored `connections_p8a.py` — latent since 45c0b08) as a one-line commit, or
  stage byte-identical with sha256 receipts as eval-runner-1 did.
- Rebuild image + recreate BOTH containers (baked image; restart is insufficient),
  re-derive pair 12/13 ground truths live (SPEC 2 §2.6), THEN run the 11-pair gate
  with the pinned model `claude-sonnet-4-5-20250929`.

---

## Appendix A — new finding filed during this design pass

Filed as a findings-ledger row (area lore_map, by designer-p8dprime): the doubled
map key does not merely mislabel — it silently DROPS production import edges at
map.py:515 (importer identity is canonical; keys are doubled) and blinds
what_imports' prefix arm at map.py:512, so the default map's production ranks
mostly sit at the teleport floor (live receipt: rank 0.0044 uniform across most
production modules). SPEC 2 §2.2 carries the fix; the finding exists so the class
is ledgered even if scope shifts.

## Appendix B — tool-honesty note (brief-base §4)

lore tools were used for: findings bodies (#52/#53/#54), both live defect repros,
the module-identity receipts (impact consumers, dead_code names), and the
unfocused-map rank floor receipt. Grep/Read fallbacks were used — and are declared
here — for: (a) consumer-set exhaustiveness of `references()`/`what_imports`/
`module_qualified_name` (rename-class exhaustiveness where one missed site
compiles-but-breaks), (b) test-pin sweeps for retired/doubled names (non-symbol
textual seams), (c) reading exact implementation spans in a repo whose live index
serves a container image, mid-P8d′, with known defects under study. These are the
three sanctioned fallback cases; no friction row filed for them beyond Appendix A.
