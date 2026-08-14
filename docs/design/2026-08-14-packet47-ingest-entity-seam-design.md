# Packet 47 — the twelfth seam: extension ingest entity-fragment (RULED DESIGN)

**Status: RULED (operator, 2026-08-14) + adversary-hardened (R2).** Author: `fable-design-47`
(design sidecar, self-attacked before shipping — §9; Opus adversary folded — see the R2 revision log).
**Operator rulings 2026-08-14:** (1) **SPLIT 47/47a CONFIRMED**; (2) **transactionality Reading B
RATIFIED** (§Q2.2); (3) **phase-2 edge resolution is FULL-SWEEP-ONLY** — D&D uses NO incremental file
watcher, so the incremental/watcher edge-resolution path is a **PINNED NON-FEATURE** (§Q3.2), which
dissolves adversary F1 by construction (every re-crawl re-resolves ALL edges against ALL current nodes
— the same mechanism that enforces edition supersession). This doc remains the design INPUT for the
47a contract; the adversary still runs on the contract built from it (standing law). Scope: the
**FRAMEWORK SEAM ONLY** — NOT the dnd domain. The dnd schema (51), the machine-tier reader (52a),
and the real cross-edition resolver / supersession function (52b) are scope-OUT; this design proves
the generic seams with a **minimal fake-domain fixture extension** (§8), exactly as packet 46 proved
discovery with a fake registry.

**Ruled input:** `docs/design/2026-08-03-wave-d-architecture.md` §4 (the three seams · the composition
point · claimed-file-skips-chunking · all-four-purge-sites · `xt_<name>_` namespacing · two-phase
edges · the ensure_ready-rides-write_stack ordering pin). Store law: `docs/reference/
surrealdb-31-capabilities.md` (cited by section, never re-transcribed). Corruption-direction evidence:
`docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-graph-scout-1.md` §6.1 (via wave-d).

> **Citations are by SYMBOL, not line number** (brief-base §1) — every server/indexer line number
> in the ruled input was stale at authoring time; the symbols below were re-grounded live against
> the index at this doc's authoring. Where a bare line appears it is dated and marked
> *"at authoring"*.

---

## R2 revision log (2026-08-14 — folding the Opus adversary pass)

An independent Opus-4.8 adversary (`docs/plans/v2/receipts/2026-08-14-packet47/REPORT-opus-adversary-47.md`, graded at HEAD `5770439`, store ref
read in full, symbols live) returned **SHIP-WITH-FIXES, 8 findings**. **All eight ACCEPTED** (each
re-verified against source by the author before folding — the three code-fact findings F3/F4/F5 were
confirmed live, not taken on the adversary's word). One residual (R3) was REDUCED to a non-issue on the
adversary's reasoning. Disposition:

| # | sev | finding (one line) | disposition | where folded |
|---|---|---|---|---|
| F1 | HIGH | per-`source_book` scope cannot restore a CROSS-BOOK edge on an incremental path; "both directions covered / A-full correct everywhere" is FALSE | **ACCEPT** — full-sweep is the ONLY correct path for cross-book edges | §Q3.2 rewritten · §Q3.3 · R2 reframed · §Q6 cross-book fixture |
| F2 | HIGH | one unresolvable endpoint aborts the WHOLE scope's purge+RELATE (DD-3.c denial) | **ACCEPT** — resolve-or-drop is now a REQUIREMENT of `resolve_edges` + a pin | §Q3.1 · §Q5 · §Q6 partial-resolvability fixture |
| F3 | MED | `server.registry` is the `ChunkerRegistry`, NOT the extension list — the Indexer is unwired for `claims()` | **ACCEPT** (confirmed live: `LoreServer.registry`→`ChunkerRegistry`; extensions are `server._extensions`) | §Q1.2 rewritten · §8 |
| F4 | MED | ingest backends leak on block-2 (startup/sweep) failure + normal shutdown; ExtensionContext built too late | **ACCEPT** (confirmed: two teardown blocks; AppContext.aclose hardcoded list omits them) | §Q4 rewritten |
| F5 | MED | the derived-reach pin is STILL a 3-method-name hand-list; §7's caller list is 2 sites short (5 real) | **ACCEPT** — tier-entity-purge moves INSIDE `delete_by_tier` (the sink) | §7 rewritten |
| F6 | MED | fixture `UNIQUE(source_book, slug)` is trailing-slug → TableScans; the idiom is lookup-key-LEADING | **ACCEPT** — `UNIQUE(slug, source_book)`; §2 citation corrected | §Q6 (DDL) |
| F7 | LOW | phase-2 partial-failure loop semantics unspecified (false-clear risk) | **ACCEPT** — per-scope isolate + loud, pinned | §Q3.1 · §Q6 |
| F8 | LOW | §Q6 DDL sketches put `OVERWRITE`/`IF NOT EXISTS` TRAILING (parse error) | **ACCEPT** — leading-clause form | §Q6 |
| R3 | — | `Extension.name` charset (my own residual) | **REDUCED to non-issue** — claim-exclusivity means no two extensions ever compose into one transaction, so a cross-extension `xt_` collision is architecturally impossible; only intra-extension self-collision remains, which `compose` catches loudly | §Q1.3 |

**Split recommendation UNCHANGED (still SPLIT):** every finding adds pins or wiring (cross-book fixture,
resolve-or-drop pin, the Indexer extension-list param + 4-site thread, block-2 teardown + its pin, the
in-`delete_by_tier` purge, phase-2 partial-failure pin) — the build only grew. See §8.

Sections below are the REVISED text; the R2 changes are marked `[R2: Fn]` inline where they land.

---

## 0. The shape in one paragraph

An extension contributes a per-file **ingest fragment** — typed entity records + intra-file purge —
that the indexer composes into the SAME per-file `SurrealStore.apply(fragments)` transaction as the
file's other producers, so the entity rows and the manifest row commit-or-roll-back together. A
**claimed** file skips chunking/embedding (manifest row `n_chunks=0`); it is otherwise a normal file
on a normal static tier, reusing the whole lifecycle (manifest, watcher, reconcile, tier-purge).
**Cross-file `ENFORCED` edges cannot ride phase 1** (a `RELATE` fails unless both endpoint nodes
already exist — store ref §4), so edges are **two-phase**: phase 1 writes NODES atomic with the file;
phase 2 resolves EDGES per `source_book` scope, purge-then-`RELATE` in one transaction, triggered at
a sweep's clean completion point. Purge-by-scope is the mitigation for the measured re-ingest
corruption (DELETE+CREATE silently loses edges; UPDATE silently keeps stale ones — §Q3).

The precedent this clones is `SurrealCodeGraph.build_file_graph_fragment` / `.purge_file_fragment`
(`graph_surreal.py`) — PURE builders, every value a bound param namespaced under a prefix, purge-then-write
inside one fragment. The ONE place it CANNOT be cloned is the dangling-edge trick: the graph avoids
dangling by `UPSERT`ing shared *name records* in-fragment so an edge target always exists — that does
**not** transfer to `ENFORCED` entity edges whose endpoints are real nodes in *other files*. That gap
is the entire reason edges are two-phase.

---

## Q1 — FRAGMENT SHAPE (the phase-1 seams, composition, namespacing, gating)

### Q1.1 The seam methods (Extension ABC — the framework's 12th seam)

`loremaster.extension.Extension` today is an ABC with a required `name` and **eleven inert-default
seams** (`Extension` docstring; `chunkers`…`classify_detail`). The 12th seam — **ingest** — adds the
following methods, each with a safe inert default so a zero-ingest extension (and a zero-extension
server) is byte-unchanged:

```python
# -- seam 12: ingest (entity records + two-phase edges) ---------------------

def claims(self, tier: str, path: str) -> bool:
    """Does this extension own the ingest of (tier, path)? Default: False.

    PURE + cheap (suffix/tier test) — called for every pending file. A claimed
    file skips chunking/embedding and is ingested via entity_fragment instead.
    """
    return False

def entity_fragment(
    self, tier: str, path: str, text: str, ctx: ExtensionContext
) -> TxnFragment | None:
    """Build this file's phase-1 NODE fragment (purge-then-create), or None.

    A PURE builder on the build_file_graph_fragment precedent: parse `text`
    (never a socket touch), emit a self-contained DELETE-this-file's-prior-
    entity-nodes + CREATE-new-nodes fragment, NO BEGIN/COMMIT, every value a
    bound param namespaced under f"xt_{self.name}_". NODES ONLY — cross-file
    ENFORCED edges are phase 2 (resolve_edges). Default: None.
    """
    return None

def entity_purge_fragment(
    self, tier: str, path: str
) -> TxnFragment | None:
    """Build the standalone purge of one file's entity slice, or None.

    The composable counterpart to entity_fragment's internal purge, for the
    DELETE sites (a removed file) — mirrors purge_file_fragment. Default: None.
    """
    return None

async def resolve_edges(
    self, ctx: ExtensionContext, changed_scopes: set[str] | None
) -> list[TxnFragment]:
    """Phase 2: resolve cross-file edges per source_book scope.

    READS committed phase-1 nodes to resolve each edge's endpoints, then returns
    ONE purge-then-RELATE TxnFragment PER scope (purge the scope's prior edges,
    re-RELATE the resolved set — the corruption mitigation, §Q3). The framework
    calls this ONLY with changed_scopes=None (every scope this extension owns, at
    full-sweep completion — the ONLY trigger, RULED 2026-08-14, §Q3.2). The `set`
    form is RESERVED for the pinned non-feature (live per-file re-resolution) and
    is never passed today. The INDEXER applies the returned fragments via
    SurrealStore.apply (ONE IMPLEMENTATION — never a private query path).
    Default: [] (no edges).
    """
    return []

def ingest_backends(self, ctx: ExtensionContext) -> list[IngestBackend]:
    """Contribute the domain store(s) that must be readied BEFORE any fragment
    build — the DDL/lifecycle collaborators (phase 0). Default: [].

    Each IngestBackend is a structural protocol: `async ensure_ready()` (applies
    the domain schema DDL — store law §1.1) and `async close()`. build_app_context
    readies each on the write_stack_readied rail like code_graph, so a partial-
    ready failure unwinds (§Q4). The extension retains the reference for its
    entity_fragment/resolve_edges seams to read through.
    """
    return []
```

`IngestBackend` is a `typing.Protocol` (structural — `ensure_ready`/`close`), not a base class, so an
extension's `DnDStore` (packet 51, "own connection, execute_transaction") satisfies it without
inheritance — the same duck-typed shape `code_graph`/`manifest`/the ledgers already present to
`write_stack_readied`.

> **Naming note — this is ONE seam (ingest), five methods.** The `Extension` docstring's "eleven
> seams" becomes "twelve"; the twelfth is the ingest capability, realised as this method cluster
> (phases 0/1/2). Update the docstring count and the seam-numbering comment — a stale "eleven" is the
> natural-language-surface-no-gate-checks class (CLAUDE.md rename-sweep law); pin it (§8 test list).

### Q1.2 Composition — where `entity_fragment` joins the per-file transaction

`Indexer._compose_file_fragments` (`loremaster/index/indexer.py`) builds the ordered producer list
`[replace_file_fragment, (file_text_fragment?), manifest.replace_fragment, (graph_fragment?)]` and
hands it to `SurrealStore.apply`, which composes all producers into ONE `BEGIN…COMMIT` on the store's
own connection (`compose` + `execute_transaction`). `_graph_fragment` is the exact gating precedent:
it returns `None` when no graph is wired OR the path is not `.py`, else the pure
`build_file_graph_fragment`.

The entity path mirrors this precisely. Add a sibling `_entity_fragment(tier, path, source, ctx)`
helper and a claimed-file branch in `_compose_file_fragments`:

- **Gate (mirror `_graph_fragment`'s None-gate) — `[R2: F3]` the Indexer must be given the EXTENSION
  LIST; it does NOT already hold it.** ⚠ **Correction (confirmed live at `5770439`):** `LoreServer.registry`
  (`server.py:573`) is a `@property → ChunkerRegistry` (the composed *chunker* registry), and
  `Indexer.__init__` (`indexer.py:391`) types its `registry: ChunkerRegistry` param — so `self._registry`
  holds **chunkers, not `Extension` objects**, and iterating it yields chunkers with no `claims()`
  method. The extension list lives at `server._extensions: list[Extension]` (`server.py:380`, appended
  by `register_extension` at `:627`, exposed as the `LoreServer.extensions` property at `:571`). The
  first-draft claim "the Indexer already holds `registry=server.registry` (extensions)" was **wrong**.
  - **Fix:** the `Indexer` gains a NEW constructor parameter — the extension list (or a
    claims-dispatching accessor), e.g. `extensions: Sequence[Extension] = ()`. It is threaded through
    **all four production construction sites** (wave-d §3), every one of which routes through
    `Indexer.__init__`: `build_app_context` (`server.py`, passes `server.extensions`), `index/cli.py`,
    `scout.py`, `comms_consumer_eval.py`. A site that omits the param defaults to `()` (backward-compatible:
    no ingest). Pin: the four sites are enumerated by a DERIVED scan (the `registration_sites.py` idiom /
    a call-site AST scan), never a hand-list, so a fifth construction site that omits the extensions is
    caught (the CLAUDE.md reach law — the same class as F5).
  - **Gate logic (unchanged):** `_entity_fragment` asks each extension in the injected list
    `claims(tier, path)`; **at most one** may return `True` for a `(tier, path)` — two claimants is a
    LOUD build-time error naming both. If exactly one claims, call its
    `entity_fragment(tier, path, source, ctx)` and return that fragment (or `None`).
- **Claimed ⇒ skip chunking (wave-d §4):** when a file is claimed, `_compose_file_fragments` builds
  `records=[]`/`vectors=[]`, so `replace_file_fragment(tier, path, [])` composes a **bare DELETE**
  that purges any prior chunk points (correct — a file that used to be chunked and is now claimed loses
  its stale chunks), and the manifest row is written with `n_chunks=0`. The composed set for a claimed
  file is:

  ```
  [ replace_file_fragment(tier, path, [])   # bare DELETE — purges any prior chunks (st_)
  , file_text_fragment(tier, path, source)  # OPTIONAL, see Q1.4 (ft_)
  , manifest.replace_fragment(..., n_chunks=0, state=INDEXED)   # (mf_)
  , entity_fragment(tier, path, source, ctx) # purge-then-create NODES (xt_<name>_)
  ]
  ```

  The chunking/embedding pipeline upstream (`_collect_sweep_pending` / the realtime embed) must ALSO
  skip a claimed file so it never produces chunk records or an embed batch (the machine tier is never
  embedded). The claim test is the single decision point — chunk-skip and entity-compose both key off
  the SAME `claims()` result, computed once per file.

- **`_commit_batch_file`** (the batch pass-two per-file apply, `indexer.py`) composes the identical
  producer set for its files — it gains the identical claimed-file branch. This is the second
  compose site the wave-d §4 "four purge sites" names, and it is a WRITE site, not only a purge site.

### Q1.3 Param namespacing + the compose collision registry

The five existing producer prefixes are named constants: `CHUNK_FRAGMENT_PARAM_PREFIX = "st_"`
(`store/surreal.py`), `FILE_TEXT_FRAGMENT_PARAM_PREFIX = "ft_"` (same), `MANIFEST_FRAGMENT_PARAM_PREFIX
= "mf_"` (`index/surreal_manifest.py`), `GRAPH_FRAGMENT_PARAM_PREFIX = "gr_"` (`graph_surreal.py`),
`_SNAPSHOT_FRAGMENT_PARAM_PREFIX = "sn_"` (`index/snapshots.py`).

**There is NO central prefix allowlist to extend.** `compose` (`store/_txn.py`) detects collisions
**dynamically**: if two fragments bind the same param name it raises `TxnParamCollisionError` (fail-LOUD,
never a silent overwrite). So the ruled input's phrase "claimed in compose's collision registry beside
`st_/ft_/mf_/gr_`" is satisfied by CONVENTION + a namespacing PIN, not by editing `compose`:

- The entity fragment namespaces every param under `f"xt_{ext.name}_"`. Because `ext.name` is the
  extension's stable key in the `extensions:` config, two DIFFERENT extensions cannot collide, and
  `xt_` is distinct from the five existing prefixes.
- **Pin (mirror `TestFragmentParamNamespacing` / `test_graph_build_fragment_params_are_graph_namespaced`):**
  every key of an `entity_fragment` / `entity_purge_fragment` output starts with `f"xt_{ext.name}_"`.
- **`[R2: F3/R3]` The cross-extension `xt_` collision is ARCHITECTURALLY IMPOSSIBLE — not merely
  fail-loud.** Claim-exclusivity (§Q1.2, at most one `claims()` per file) plus per-scope-SEPARATE
  phase-2 applies (§Q3.1) mean **no two extensions ever contribute params to the SAME `compose()`
  call** — phase-1 composes one file (one claimant's `xt_<name>_` params + the fixed `st_/ft_/mf_`
  producers), and each phase-2 `store.apply` carries one extension's one scope. So a
  cross-extension prefix collision cannot arise. The ONLY residual is an **intra-extension
  self-collision** (one extension's own two params colliding after prefixing), which `compose` catches
  LOUDLY (`TxnParamCollisionError`, `_txn.py`) — a builder bug, surfaced at build time, never a silent
  drop. **Therefore an `Extension.name` charset constraint is OPTIONAL defensive hygiene, not a
  correctness requirement** — the earlier "two adversarially-named extensions crash at boot" concern is
  unreachable given the architecture. (Superseded my own residual R3.)

### Q1.4 Multi-node-type + edges; the `file_text` question

The realism the fixture must exercise (dnd rulings §2 — seven families need monster/feature/subclass/
condition/item nodes, NOT spell-only): `entity_fragment` emits **multiple node types** and the phase-2
`resolve_edges` emits **cross-entity edges**. The fixture (§8) uses ≥2 node kinds + ≥1 `ENFORCED`
relation edge to keep the general shape honest (a spell-only single-table fixture is the small-N
non-discrimination trap CLAUDE.md warns of).

**`file_text` for a claimed file (minor open choice, recommend WRITE):** storing the raw source as
`file_text` lets `lore_read` serve the machine-tier file's bytes with provenance and keeps the manifest
row's shape uniform. It is orthogonal to the entity rows. **Recommendation:** write `file_text` for
claimed files too (subject to the existing size cap `_file_text_within_cap`); it costs one fragment and
buys provenance. Non-blocking — the operator/contract may drop it. (The transactionality pin does NOT
depend on it; the manifest row is the atomicity witness, §Q2.)

---

## Q2 — TRANSACTIONALITY (+ the flagged spec ambiguity)

### Q2.1 The guarantee

`SurrealStore.apply` composes all of a file's producer fragments into ONE connection-scoped
`BEGIN…COMMIT` and runs it through `execute_transaction`, which verifies EVERY statement's status
(never the SDK's statement[0]-only `query()` — store ref §3) and self-heals a transport drop. So for a
claimed file: **the chunk-purge DELETE, the (optional) file_text, the manifest row, and the entity
nodes commit or roll back together.** A rejected entity statement rolls the WHOLE transaction back —
the manifest row is NOT written, so the file is never recorded `INDEXED`, and a re-index retries it
cleanly. This is the same atomicity the graph slice already rides (`apply` docstring; `_graph_fragment`
docstring: "as atomic as the vector index").

### Q2.2 ⚠ THE SPEC AMBIGUITY — flagged and settled per the brief

**The conflict (the lead found it; I confirm it):**
- The **packet file** `docs/plans/v2/47-ingest-entity-seam.md` (2026-08-02, PRE-transmute) Exit line
  pins: *"entity write fails ⇒ chunk write rolled back — constructed, with a positive control."*
- **wave-d §4** (2026-08-03 reframe) rules a **claimed file SKIPS chunking** — so chunks and entities
  never coexist in one file's transaction. **The literal "chunk write rolled back" pin is
  unrepresentable:** there are no chunk records for a claimed file to roll back.

**Both readings, written out (brief-base §2 — pick with the alternative on the record):**
- *Reading A (literal, pre-reframe):* a file is both chunked AND entity-bearing; entity failure rolls
  back the chunks. **Rejected** — contradicts the ruled input (wave-d §4) and the transmute
  architecture, where prose (`output/`, chunked) and machine (`output-graph/**/*.jsonl`, claimed) are
  SEPARATE file trees (wave-d §1 R-A, §9 packet 54). A file is prose XOR machine; claimed XOR chunked.
  No file is both. I could find no case in the ruled corpus split where one wanted both.
- *Reading B (faithful, post-reframe) — RECOMMENDED:* **entity write fails ⇒ the file's manifest row
  (and file_text, and the chunk-purge DELETE) roll back together; nothing is recorded `INDEXED`.**
  **Positive control:** a clean ingest commits the entity node rows AND the manifest `INDEXED` row
  atomically (both present after `apply`; neither present after a forced entity-statement failure).

**RULED (operator, 2026-08-14): Reading B RATIFIED.** The atomicity WITNESS is the manifest row, not a
chunk row. If a future extension ever wants a file both chunked and entity-bearing, the composition
already supports it (don't gate chunk-skip on `claims()`) — but the ruled input forbids it here, so it
is out of scope and unpinned.

### Q2.3 The quantifier: atomicity holds across EVERY producer, and its BOUND

The guarantee is ∀ producers of a claimed file — but ONLY within phase 1. **Phase 2 is a SEPARATE
transaction** (different time — sweep completion), by necessity (`ENFORCED` needs committed endpoints).
So the honest statement is: *phase-1 (nodes + manifest + purge) is atomic; phase-2 (per-scope
purge+RELATE) is atomic; the two are NOT atomic with each other.* Between them, entity nodes exist with
no cross-file edges — a reader querying edges in that window under-reports. **Named bound (§Q3.3).**

**Mutation proof (the contract's load-bearing pin):** force an `entity_fragment` statement to fail
(e.g. an ASSERT violation) → assert BOTH (a) no entity node rows for the file AND (b) no manifest
`INDEXED` row; positive control: the un-mutated build commits BOTH. Prove the mutation LANDED (CLAUDE.md
#194 — declare the expected-RED node ids before the run, diff both ways). ⚠ The dirty-store leg (§Q3.4)
is a SEPARATE, mandatory pin — a virgin-DB atomicity pin cannot see the migration hazard.

**`[R2: frontier-2 refinement]` Assert "no INDEXED row", NOT "no manifest row".** The
`_commit_batch_file` / realtime fault-isolation path CATCHES `SurrealStoreError` and writes a manifest
**`FAILED`** row (per-file fault isolation) — so a manifest row MAY exist after a rejected apply; the
correct witness is that it is not `INDEXED`. And "re-indexes next pass" is optimistic for an UNCHANGED
`FAILED` file — the mtime+size fast-path may skip it (inherited indexer behavior, not this seam's to
fix); the reconcile/divergence heal is the recovery path. The pin asserts the ATOMICITY (no `INDEXED`
row + no entity rows on failure; both on success), not the retry timing.

**`[R2: frontier-1 conjunction pin]`** A separate pin asserts a claimed file yields BOTH
`n_chunks=0` (chunk-skip took) AND entity rows present (ingest happened) — the CONJUNCTION. Two wrong
builds each satisfy one leg: a build that skips chunking but forgets to compose entities passes a
"chunks absent" test; a build that composes entities but forgets the chunk-skip passes an "entities
present" test. Only the conjunction pin (n_chunks=0 ∧ entity rows present, in the SAME manifest/apply)
rejects both.

---

## Q3 — CROSS-FILE EDGE RESOLUTION TIMING (the hardest question, two-phase edges)

### Q3.0 Why two-phase at all (the store-law forcing function)

An `ENFORCED` relation edge disallows a `RELATE` unless BOTH endpoints already exist (store ref §4:
*"the `ENFORCED` clause … disallow a `RELATE` … unless it points to existing data"*, both endpoints,
probed). A cross-file edge (a spell in file A, its class in file B) has an endpoint in another file
that may not be ingested yet when A is processed. The graph's dangling-avoidance trick — `UPSERT` the
target *name record* in the same fragment — does NOT transfer, because entity endpoints are real typed
nodes, not name records, and inventing a placeholder node to satisfy `ENFORCED` would reintroduce the
ghost the clause exists to forbid. **Therefore NODES are phase 1 (atomic per file); EDGES are phase 2
(after all of a scope's nodes are committed).** Without `ENFORCED` a dangling `RELATE` writes a silent
ghost recipient (store ref §4, #105) — so the edges MUST be `ENFORCED`, which forces the phasing.

### Q3.1 Phase-2 TRIGGER — full-sweep path (settled: use the clean completion point)

`Indexer._sweep_two_pass` has a clean completion point: after `_summarize(outcomes, …)` builds the
`IndexSummary` and (for a rebuild) the fingerprint/status is stamped, **before `return result`**. At
that point every pending file's phase-1 nodes are committed. **The indexer calls, for each registered
ingesting extension, `fragments = await ext.resolve_edges(ctx, changed_scopes=None)` and applies each
returned fragment via `self._store.apply([fragment])`** (one scope = one atomic purge+RELATE txn). This
is the natural end-of-sweep hook wave-d §4 points at ("the full-sweep path has a clean completion point;
USE IT").

- **NOT `on_startup`** (seam 9): it runs after the Indexer is constructed and only at server boot, not
  at each sweep — it would never re-resolve edges after an incremental change and would run before the
  first sweep's nodes exist. wave-d §4 explicitly rules it out for the DDL ordering; it is equally wrong
  for edge timing.
- **Endpoint resolution READ:** `resolve_edges` reads committed phase-1 nodes to resolve each edge's
  `(target_kind, target_name/slug)` to a node RecordID (a LOOKUP, not a parse — the machine tier
  carries resolved targets; the real supersession function is 52b, scope-OUT — the fixture resolves by
  exact slug). It reads through the extension's own ingest backend connection (or `ctx.store`), then
  returns fragments the INDEXER applies (ONE IMPLEMENTATION — the write always rides
  `store.apply`/`execute_transaction`, never a private path).

- **`[R2: F2]` RESOLVE-OR-DROP IS A REQUIREMENT of `resolve_edges`, not an aspiration.** A scope's
  phase-2 fragment is ONE `DELETE …WHERE source_book=$scope; RELATE …N edges…` composed into ONE
  `store.apply` (`compose`→`execute_transaction`). Store ref §3/§4: within one `BEGIN…COMMIT`, a single
  `RELATE` to a non-existent endpoint (`ENFORCED` rejects it AFTER the write is attempted, aborting the
  whole txn) rolls back the DELETE too — so **one unresolvable reference denies the ENTIRE book's edge
  update** (the DD-3.c total-denial shape CLAUDE.md flags). Therefore `resolve_edges` MUST **drop or
  tombstone an intent whose endpoint does not resolve BEFORE building the `RELATE`** — never pass an
  unresolved endpoint through to the fragment. This matches 52b's real semantics (a dangling reference
  becomes a renderable tombstone, wave-d §7), and it is why the app-level resolve step and `ENFORCED`
  are both kept (store ref §4 "Shape to ship"): the resolve step keeps the txn from aborting; `ENFORCED`
  is the backstop against a resolution bug. **Pin (§Q6):** a scope with one resolvable + one
  UNRESOLVABLE intent commits the resolvable edge and drops/tombstones the unresolvable one — NEVER a
  whole-scope abort.

- **`[R2: F7]` Phase-2 LOOP error semantics (per-scope isolation, LOUD, never swallowed).** The
  indexer applies each scope's fragment in a SEPARATE `store.apply`. A failure of scope *k*'s apply must
  **isolate to that scope** (mirroring the indexer's existing per-file chunker fault-isolation): scopes
  already committed stay committed, the remaining scopes are still attempted, and the failure is
  **surfaced LOUDLY** — recorded in the `IndexSummary` as a per-scope edge-resolution failure (a
  `scopes_failed` count/list), never logged-and-forgotten. A swallowed partial resolution is a false
  clear (a dirty store carrying a prior version's edges for the un-run scopes looks "healthy"). **Pin
  (§Q6):** force scope 2's apply to fail → assert scope 1 committed, scope 3 still attempted, AND the
  failure is reported in the summary (not swallowed). NOTE the F4 interaction: a failure that
  PROPAGATES out of the initial-sweep phase-2 triggers `build_app_context`'s block-2 teardown (§Q4) —
  which is exactly why the block-2 teardown MUST close the ingest backends. Per-scope isolation keeps a
  single bad book from failing the whole sweep; the loud summary keeps it from being a silent clear.

### Q3.2 `[RULED 2026-08-14 — FULL-SWEEP-ONLY]` Phase-2 edge resolution has ONE trigger; the incremental path is a PINNED NON-FEATURE

**Operator ruling (2026-08-14): phase-2 edge resolution runs ONLY at full-sweep completion (§Q3.1).
D&D uses NO incremental file watcher — the machine tier is re-ingested by FULL re-crawls only. So the
incremental/watcher edge-resolution path is NOT BUILT; it is a pinned NON-FEATURE.** This supersedes the
r2 analysis below (kept as the WHY) and **dissolves adversary F1 by construction.**

**Why this is correct, not merely convenient — F1 dissolved.** F1 (r2) proved that a per-`source_book`
INCREMENTAL re-resolution silently drops cross-book edges: a cross-book edge `spell(book A) →
class(book B)` carries ONE scope but is cascade-vulnerable to node changes in BOTH books (store ref
§2/§4: deleting either endpoint node cascades the edge away silently; graph-scout §6.1 measured it), so
re-ingesting only book B never restores the A-scoped edge. **The ruling removes the incremental path
entirely.** A full-sweep re-resolution re-resolves EVERY scope against ALL current nodes in one pass —
so a cross-book edge is always re-pointed at the current node set, with no window in which one book's
re-ingest leaves another book's edge dangling. wave-d §8's *"dnd re-scrapes are FULL re-crawls"* is
therefore load-bearing for **CORRECTNESS**, not performance: the production ingest path IS the only
correct path, and it is the only path.

**This is ALSO the edition-supersession enforcement mechanism.** Because every full re-crawl re-resolves
all edges against all current nodes via the resolver (52b, which prefers the newest edition — wave-d
§7), **each crawl re-points every edge at the newest-edition node for its slug.** "Newer wins" is not a
separate pass; it is what full-sweep re-resolution DOES. (The precedence key + how `resolve` picks is
the subject of the companion proposal `docs/design/2026-08-14-edition-precedence-mechanism.md`.)

**What the watcher path DOES and does NOT do (the precise seam behavior):**
- **On a file DELETE** (`watcher._purge` / `reconcile._purge_file`): purge that file's entity NODES via
  `entity_purge_fragment`. Node deletion cascade-deletes that file's edges (store ref §2/§4) — a
  correct, immediate removal. It does **NOT** re-resolve any other book's edges.
- **On a single-file watched CHANGE:** phase-1 re-writes that file's nodes atomically (purge + recreate).
  **Edges are NOT re-resolved on the watch event** — they re-resolve only at the next full-sweep
  completion. (For the dnd instance this never arises: re-crawls are full sweeps, not single-file
  watches.)
- **`resolve_edges` is called ONLY with `changed_scopes=None`** (the full-sweep completion, §Q3.1). The
  `changed_scopes` parameter is retained in the seam signature for the future non-feature, but the
  framework never passes a non-`None` value; a pin asserts the indexer's only call site uses `None`.

> **PINNED NON-FEATURE:** *incremental (per-file, on-watch) cross-file edge re-resolution is NOT built.*
> Edges re-resolve only at full-sweep completion. A single-file watched change re-writes that file's
> nodes but leaves its cross-file edges to the next full sweep. **Re-open trigger:** a future extension
> wants LIVE per-file edge resolution (a claimed tier watched with single-file edits, not wholesale
> re-crawls). Closing it then needs reverse-dependency re-resolution (an index of "books whose edges
> point into book X") — deliberately NOT built now. This is a pinned bound (CLAUDE.md "pin the miss"),
> so a future engineer meets it deliberately, with its rationale attached.

**The cross-book fixture (§Q6) is KEPT, reframed to the ruling:** it now pins that **full-sweep
re-resolution correctly re-points a cross-book edge at a newly-added newer-edition node** (add a newer
book carrying a superseding node for the slug; run a full sweep; assert the edge now points at the new
node, not the stale one) — the positive proof that "newer wins" is enforced by the full-sweep resolver,
and that a re-crawl never orphans a cross-book edge.

### Q3.3 The purge-then-RELATE law + the phase gap bound

Re-ingest corruption is MEASURED in both directions (graph scout §6.1, via wave-d §4): **DELETE+CREATE
silently LOSES edges; UPDATE silently KEEPS stale ones** (store ref §2 corroborates: `UPDATE` of a
relation edge's `in`/`out` is a SILENT NO-OP). The only correct re-ingest is **purge-by-scope +
re-RELATE in ONE transaction**: each edge carries a `source_book` (scope) field; phase-2 for scope S is
`DELETE <edge> WHERE source_book = $scope; RELATE …` composed into one `store.apply` txn. Node deletion
ALSO cascades its edges automatically (store ref §2/§4 vendor: an edge self-deletes when an endpoint is
gone) — a backstop, not the mechanism; the explicit scope purge is what makes a CHANGED (not deleted)
edge target converge.

**Named bound — the phase-1↔phase-2 window (§Q2.3) `[R2: F7/frontier-3 refinement]`:** between a
scope's phase-1 node commit and its phase-2 edge commit, a reader querying edges under-reports.
⚠ Two honesty refinements over the first draft: (a) the window is **NOT "seconds"** — for a large
corpus a full re-crawl's phase-1 (walk + chunk-skip + node writes across every file) runs for
**minutes** before phase-2 fires at completion; and (b) DURING phase-1 the edge set is not a clean
"nodes with no edges" but a **PARTIALLY-CASCADED, inconsistent set** (each node purge/recreate cascades
its edges progressively). So the bound is: *edges are only guaranteed consistent AFTER the sweep's
phase-2 completes; a mid-index read sees an inconsistent, under-reporting edge set for up to the
sweep's duration.* **If a future live consumer reads edges DURING indexing, record a per-scope
`edges_resolved` marker so the reader can distinguish "not yet resolved" from "no edge"** — deferred to
52a/52b as the re-open trigger (the dark tier + full-recrawl model makes it non-load-bearing now).

### Q3.4 ⚠ THE `ENFORCED` DIRTY-STORE FALSE CLEAR (the #107 shape — mandatory pin)

`DEFINE TABLE … TYPE RELATION … ENFORCED` on an EXISTING edge table with `IF NOT EXISTS` is a **SILENT
NO-OP** — the `ENFORCED` never lands on a live store (store ref §1.1 TABLE(RELATION) row + §4 migration
row: *"`IF NOT EXISTS` is a SILENT NO-OP … `OVERWRITE` is the only clause that lands it"*, probed). This
is #107's exact shape and **invisible to every virgin-DB test** (store ref §1.6). Therefore:

- **Relation edge tables use `DEFINE TABLE OVERWRITE … TYPE RELATION … ENFORCED`** (store ref §1.1);
  plain tables/indexes/analyzers stay `IF NOT EXISTS`; fields use `OVERWRITE` (§1.1). `OVERWRITE` on a
  relation table is safe — preserves fields/indexes/rows, does not rebuild (§1.5 probe + positive
  control).
- **Mandatory dirty-store migration pin** (`TestSchemaMigrationAgainstAnExistingStore` pattern, store
  ref §1.6): apply OLD DDL (edge WITHOUT `ENFORCED`) → `RELATE` a **dangling** edge (succeeds, no
  guard) → apply NEW DDL (edge WITH `ENFORCED` via `OVERWRITE`) → assert (a) `ENFORCED` now REJECTS a
  NEW dangling `RELATE` (the guard took) AND (b) the pre-existing dangling row SURVIVED (store ref §4:
  pre-existing dangling edges are entirely unaffected — cleanup is a separate migration). The virgin-DB
  ingest pins CANNOT see this; it is the false-clear that renders identical bytes to a healthy schema.

---

## Q4 — ORDERING RAIL (the domain store's ensure_ready rides `write_stack_readied`)

`build_app_context` (`server.py`, ~:9086 at authoring) builds a Surreal WRITE-STACK ready guard:
`write_stack_readied: list[Any] = []` inside a `try`; each collaborator is `construct → await
X.ensure_ready() → write_stack_readied.append(X)`; on `BaseException` it closes the readied list
**newest-first** (`for backend in reversed(write_stack_readied): await backend.close()`) and re-raises.
`code_graph = SurrealCodeGraph(...); await code_graph.ensure_ready(); write_stack_readied.append(code_graph)`
sits in this rail (~:9122–9132); the `Indexer(..., code_graph=code_graph)` is constructed AFTER the
rail (~:9258).

**`[R2: F4]` `build_app_context` has TWO teardown blocks — the ingest backends must be covered by BOTH,
and by normal shutdown. My first draft covered only block 1.** Confirmed live at `5770439`:
- **Block 1 — the write-stack ready guard** (`write_stack_readied` list, `except BaseException` at
  ~:9250 closing the list **newest-first** at ~:9255). This is where the ingest backend is readied.
- **Block 2 — the startup-hooks/initial-sweep guard** (`try` at ~:9393 → `except BaseException` at
  ~:9490, closing a **HARDCODED handle list** at ~:9502–9519 — `memory_backend, task_ledger,
  finding_ledger, agent_registry, brief_ledger, snapshot_stamper, diff_engine, manifest, code_graph,
  write_store`). It does **not** iterate `write_stack_readied` and names **no ingest backend**.
- **Normal shutdown — `AppContext.aclose`** (~:8580–8598) closes the same hardcoded set; no ingest
  backend either.

**Why block 2 matters here specifically:** phase-2 `resolve_edges` runs inside the INITIAL
`watcher.run_sweep()` (~:9447) — i.e. **inside block 2** (§Q3.1). A phase-2 failure (or any failing
startup hook / a watcher that won't start) triggers block 2's teardown, which closes everything EXCEPT
the ingest backends → **a leaked domain-store connection on the startup-failure path.** A block-1-only
unwind pin cannot see this (it fault-injects the backend's OWN `ensure_ready`, which fails in block 1).

**Wiring (exact, corrected):**
1. **Build the `ExtensionContext` EARLY — right after `code_graph` is readied, before the ingest loop.**
   ⚠ My first draft's `ingest_ctx = <the ExtensionContext build_app_context already assembles>` was
   FALSE at that point: `extension_ctx` is currently built at ~:9280, AFTER block 1 AND after the
   `Indexer`. Its inputs (`write_store, embedder, config, count_tokens, manifest`) are all ready by the
   `code_graph` point (~:9132), so construct it there and REUSE the one object for the ingest loop,
   `run_startup_hooks` (~:9394), and the search pipeline (~:9293, which already carries it).
2. **The extension list is `server.extensions`, NOT `server.registry` (F3).**

   ```python
   # right after code_graph is readied (~:9132), INSIDE block 1's try:
   extension_ctx = ExtensionContext(store=write_store, embedder=embedder, config=config,
                                    count_tokens=<counter>, manifest=manifest)  # built ONCE, reused
   ingest_backends: list[Any] = []
   for ext in server.extensions:                    # the Extension objects (server._extensions)
       for backend in ext.ingest_backends(extension_ctx):
           await backend.ensure_ready()             # domain schema DDL (§Q3.4)
           write_stack_readied.append(backend)      # block-1 unwind covers it
           ingest_backends.append(backend)
   ```
3. **Pass `ingest_backends` (or the whole extension list + a close accessor) into `AppContext`** so its
   `aclose` closes them, AND **add them to block-2's teardown** (the hardcoded list, or convert block 2
   to also close `ingest_backends`). Ordering: `write_store → manifest → code_graph → extension_ctx →
   ingest_backends → (Indexer built) → (block 2)`.

- **Ordering pin (mirror `code_graph`):** the domain store's `ensure_ready` precedes any
  `entity_fragment` build (a fragment references tables the DDL defined); a pin asserts an ingest
  backend is in `write_stack_readied` before the `Indexer` is constructed.
- **Unwind pin — BOTH blocks + normal close (the F4 rider):**
  (a) block 1: fault-inject the backend's `ensure_ready` → every EARLIER collaborator `.close()`d,
  typed error re-raises (mirror `test_ready_guard_closes_earlier_backends_on_a_mid_ready_failure` /
  `TestWriteStackUnwindIncludesCommsLedgers`); **(b) block 2 (the pin my first draft MISSED): fault-inject
  a failing phase-2 apply during the INITIAL sweep → assert the ingest backend was `.close()`d** (not
  leaked); (c) normal shutdown: `AppContext.aclose` closes the ingest backend. This is the "rider is
  part of the ruling" gap the adversary caught — the pin must test the block that does NOT already
  unwind, not only the one that does.

---

## Q5 — ONE IMPLEMENTATION (the shared driver, ENFORCED, dangling hazard)

- **Every entity write rides `SurrealStore.apply` → `compose` → `execute_transaction`** — phase 1
  (composed with the file's other producers) and phase 2 (the indexer applies `resolve_edges`'
  returned fragments via `self._store.apply`). NO extension may open a private query path for its
  ingest writes. `execute_transaction` is the ONE seam that checks every statement and self-heals
  (store ref §3); a private `query()` path would reintroduce the statement[0]-only silent-partial-apply
  bug. The domain store's OWN connection is used only for phase-2 READS (endpoint resolution) and 53's
  domain-tool reads — never for the ingest writes.
- **Prove sharing by MUTATION (CLAUDE.md #102/#120 — routing ≠ sharing):** the contract must move a
  shared thing (e.g. the `TXN_STATEMENT_HARD_CAP`, or force `compose` to raise) and show the entity
  path reddens with the rest — proving the entity fragments actually flow through `compose`, not a
  look-alike. A build that hand-rolls a parallel writer would pass a happy-path test but fail the
  mutation.
- **`RELATE` uses the bound-RecordID form** `RELATE $from->edge->$to SET …` (store ref §4 — the
  `type::record(..)->edge->..` form and bare-`str` endpoints are parse/loud errors). The edge name is
  inlined (cannot be bound). Endpoints are bound `RecordID`s resolved from committed nodes.
- **`ENFORCED` guards BOTH endpoints** and is the declarative anti-dangling guard (store ref §4); the
  app-level resolve step (which only RELATEs endpoints it just read as existing) is the ergonomic
  layer, not a replacement — both, per store ref §4 "Shape to ship". `UNIQUE(in, out)` on the edge is
  legal on our floor (store ref §4) — a fan-out that may repeat an endpoint DEDUPES before the RELATE
  loop (the UNIQUE index is a backstop, not a de-duplicator).

---

## Q6 — THE FIXTURE / TEST EXTENSION (the fake domain that proves the seam)

A minimal in-test fake-domain extension (the packet-46-fake-registry analog), injected via
`monkeypatch.setattr(loremaster.extension, "EXTENSION_REGISTRY", {"fake": FakeIngestExtension})`,
exercises every seam on **spike-surreal `ws://127.0.0.1:18000`** (TEST store — NEVER `:18500`).

**`FakeIngestExtension` (name = `"fake"`):**
- `claims(tier, path)` → `path.endswith(".fake")` (or a dedicated fixture tier).
- `entity_fragment` → parses a trivial line format (e.g. `node <kind> <slug> <name>` and
  `edge <src_slug> <dst_slug>` lines) into ≥2 node kinds + edge intents; emits purge-this-file's-nodes
  + `CREATE` node rows; params under `xt_fake_`. **NODES only.**
- `entity_purge_fragment` → the standalone per-file node purge.
- `resolve_edges(ctx, changed_scopes)` → reads committed nodes, resolves edge intents by exact slug,
  returns per-`source_book` purge+RELATE fragments. **`[R2: F2]` an intent whose slug does NOT resolve
  is DROPPED (or tombstoned) BEFORE the `RELATE` — never emitted as a `RELATE` to a missing endpoint**
  (which would abort the whole scope's txn). The fixture explicitly specifies this behavior for an
  unresolvable slug (the first draft left it unspecified — F2).
- `ingest_backends(ctx)` → `[FakeDomainStore(...)]`.

**`FakeDomainStore` (clones the `SurrealCodeGraph`/`FloorCalibrationStore` shape — own connection,
`execute_transaction`, `ensure_ready`/`close`):** its DDL, under store law `[R2: F8 — clauses are
LEADING, immediately after `DEFINE TABLE`; a trailing clause is a parse error, store ref §1.1/§4 BNF]`:
- `fake_node`: **`DEFINE TABLE IF NOT EXISTS fake_node TYPE NORMAL SCHEMAFULL`** (plain table, §1.1);
  composite id `[source_book, slug]`; fields `slug/name/kind/tier/file_path/source_book` via
  `DEFINE FIELD OVERWRITE … ON fake_node …` (§1.1). **`[R2: F6]` the lookup index is SLUG-LEADING:
  `DEFINE INDEX IF NOT EXISTS fake_node_slug ON fake_node FIELDS slug, source_book UNIQUE`** — the
  lookup key (`slug`) is the LEADING column so a slug-only predicate IndexScans; composite indexes are
  leading-column-only (store ref §2, whose idiom is `UNIQUE(name, source_book)` — the NAME/slug leads).
  My first draft's `UNIQUE(source_book, slug)` was inverted: `source_book` leading → a `slug`-only
  lookup TableScans, and it cannot serve 52b's book-agnostic slug resolution (prefer 5.5 → alias → 5.0,
  which needs ALL rows for a slug across books). The composite RECORD ID stays `[source_book, slug]`
  (that is the id, independent of the index column order).
- `fake_link`: **`DEFINE TABLE OVERWRITE fake_link TYPE RELATION IN fake_node OUT fake_node ENFORCED
  SCHEMAFULL`** (relation table — §1.1: `OVERWRITE` is the ONLY clause that lands `ENFORCED`);
  `DEFINE FIELD OVERWRITE source_book ON fake_link …`; `DEFINE INDEX IF NOT EXISTS fake_link_uniq ON
  fake_link FIELDS in, out UNIQUE` (§4 — `UNIQUE(in,out)` legal on our floor).
- DDL applied inside one `BEGIN…COMMIT` via `execute_transaction` (every statement checked — §3), the
  `SurrealCodeGraph.ensure_ready` pattern exactly.

**The dirty-store migration case (the #107-invisible pin, §Q3.4):** apply an OLD `fake_link` DDL WITHOUT
`ENFORCED` → `RELATE` a dangling edge (succeeds) → apply the NEW `ENFORCED` DDL (via `OVERWRITE`) →
assert the guard now rejects a fresh dangling `RELATE` AND the old dangling row survives. This is the
one pin no virgin-DB fixture can produce.

**The corruption-direction pin (§Q3.3):** ingest a scope with an edge A→B; re-ingest with the edge
changed to A→C; assert after phase-2 that ONLY A→C exists (A→B purged) — the UPDATE-keeps-stale and
DELETE-loses-edges directions both fail this if purge-by-scope is wrong.

**`[RULED — F1 dissolved]` The CROSS-BOOK edge fixture (full-sweep supersession).** Build a genuine
cross-book edge: a node in `source_book="A"`, a node in `source_book="B"`, and an edge whose `out` node
lives in a DIFFERENT `source_book` than the edge's OWN `source_book` (e.g. edge declared by A carrying
`source_book="A"`, `out=node(B)`). Two legs, both on the FULL-SWEEP path (the only path — §Q3.2):
- **Re-crawl re-points, never orphans:** re-ingest via a FULL sweep after adding a NEWER book B′
  carrying a superseding node for B's slug → assert the cross-book edge now points at the **newer**
  node (edition supersession enforced by full-sweep re-resolution, §Q3.2 / the precedence proposal), and
  that the edge is present (never silently dropped by the re-crawl). This is the positive proof that
  "newer wins" is a property of full-sweep re-resolution, not a separate pass.
- **The pinned non-feature:** re-ingest book B by a SINGLE-FILE watched change (NOT a full sweep) →
  assert the cross-book edge is NOT re-resolved until the next full sweep (the pinned bound, §Q3.2 — a
  build that silently adds incremental cross-book re-resolution must delete this pin and say so;
  CLAUDE.md pin-the-miss law). All the first-draft fixture edges were INTRA-book, so no build's
  cross-book behavior was ever tested — the small-N/monoculture blindness CLAUDE.md warns of.

**`[R2: F2]` The partial-resolvability fixture (resolve-or-drop, no whole-scope abort).** A scope with
ONE resolvable + ONE unresolvable edge intent → assert the resolvable edge COMMITS and the unresolvable
intent is DROPPED/tombstoned, NEVER a whole-scope abort (which store ref §3/§4 would produce if the
unresolvable RELATE were emitted). Positive control: a scope with two resolvable intents commits both.

**`[R2: F7]` The phase-2 partial-failure fixture (loud, isolated).** Force scope 2's `store.apply` to
fail → assert scope 1 stayed committed, scope 3 was still attempted, and the failure is surfaced in the
`IndexSummary` (a `scopes_failed` signal), never swallowed.

**`[R2: frontier-1]` The conjunction fixture** (§Q2.3): a claimed file yields `n_chunks=0` AND entity
rows present, in the same apply — rejecting both one-legged wrong builds.

**The purge-coverage pin (§7 — the reach-attack survivor):** the tier entity purge lives INSIDE
`delete_by_tier` (the sink), not a hand-list of purge sites. See §7 `[R2: F5]`.

---

## 7. The reach-attack: purge coverage must be a DERIVED set, and the "four sites" is already wrong

wave-d §4 names "all FOUR purge sites" (indexer per-file · `_commit_batch_file` · watcher `_purge` ·
reconcile). Grounding them live: the graph slice is purged at **`reconcile._purge_file`** and
**`watcher._purge`** (both call `code_graph.purge_file_fragment`), and RE-purged in-fragment on the
re-index/`_commit_batch_file` paths (the fragment's own internal DELETE). **But there is a FIFTH site
the "four" list omits: `SurrealStore.delete_by_tier`** — the tier-wide purge used by rebuild
(`_purge_tier_for_rebuild`, `_rebuild_all`, the reconcile tier purge). It deletes CHUNK rows by tier; it
does **not** touch the entity tables. The mission statement's own words — *"purge-by-scope rides the
existing `replace_file`/**delete-by-tier** semantics"* — require that a tier purge ALSO purges that
tier's entity rows (and, by node-delete cascade, their edges). A "four-site" pin would silently exempt
`delete_by_tier`, leaving orphan entities after a tier rebuild.

**⚠ `[R2: F5]` MY FIRST DRAFT COMMITTED THE VERY ANTIPATTERN IT CITED.** The adversary caught it, and
it is correct: my "derived-reach pin" keyed on *"every call site of `code_graph.purge_file_fragment` /
`delete_file_graph` / `delete_by_tier`"* — **a hand-list of THREE receiver names**, exactly the shape
CLAUDE.md's instrument table records as defeated ("3 method names → the other 30"; "2 receiver names →
six other doors"). A slice-removal that routes through none of those three names escapes the "derived"
set — and `delete_by_tier` ITSELF is a raw `DELETE {CHUNK_TABLE} WHERE tier = $tier` (surreal.py), so
slice-removal already happens with no "purge" method at all. Worse, **my enumeration of `delete_by_tier`
callers was itself wrong**: I named three; live `lore_impact` at `5770439` shows **FIVE** prod callers —
`_index_static_tier`, `_prepare_static_tier_for_collect`, `_purge_tier_for_rebuild`,
`_rebuild_all_realtime`, `reconcile_store_divergence` — and the two I MISSED (`_index_static_tier`,
`_prepare_static_tier_for_collect`) are the STATIC-TIER paths, exactly where a claimed machine-tier file
is processed. The reach-attack landed on my own instrument.

**The correct fix — put the entity purge at the SINK, so there is no reach to enumerate:**

- **The property (derive from the DATA operation, not the API surface):** *the operation is "remove or
  replace a claimed tier's chunk-or-manifest rows"; wherever that happens, the tier's entity rows are
  removed in the same operation.*
- **Tier purge: co-locate the entity purge INSIDE `SurrealStore.delete_by_tier`** (or a sibling that
  `delete_by_tier` and any future tier-wipe both call) — ONE IMPLEMENTATION. All **5** callers are then
  covered without naming any of them, and a 6th caller added tomorrow inherits it for free. This is the
  strongest form of the reach law: the guard is not a scan over call sites, it is a property of the sink
  every call site must pass through. (The design leaves "a `delete_entities_by_tier` analog" behind —
  R2 picks the IN-FUNCTION form, per the adversary.) Atomicity note: the entity-tier-purge is a
  SEPARATE statement/txn from the chunk `DELETE` (`delete_by_tier` runs a single-statement `_query`);
  for a wholesale rebuild they need NOT be atomic with each other (the tier is being wiped and
  rebuilt) — state that explicitly so no one over-engineers a cross-table tier-purge transaction.
- **Per-file purge:** the two standalone DELETE sites (`watcher._purge`, `reconcile._purge_file`) call
  `entity_purge_fragment` alongside the existing `code_graph.purge_file_fragment`; the re-index/batch
  paths purge in-fragment via `entity_fragment`'s internal DELETE. A residual per-file reach scan is
  still useful as a BACKSTOP, but it is keyed on the property ("a per-file slice DELETE co-occurs with
  an entity-slice DELETE"), and the load-bearing coverage is the sink, not the scan.
- **Banned:** `assert len(purge_sites) == N` for any literal N — the first draft's `== 4` (and its
  wrong "4"/"3" counts) is the disease, not the cure.

---

## 8. Production surfaces + test burden (for split pricing)

**Production surfaces touched** `[R2: updated for F3/F4/F5]`:
1. `Extension` ABC — +5 seam methods (`claims`, `entity_fragment`, `entity_purge_fragment`,
   `resolve_edges`, `ingest_backends`) + `IngestBackend` Protocol + the "eleven→twelve" docstring/count
   fix. (`extension.py`)
2. `Indexer` — a NEW `extensions` constructor param (F3; the extension LIST, not the ChunkerRegistry),
   threaded through **all four construction sites** (`build_app_context`, `index/cli.py`, `scout.py`,
   `comms_consumer_eval.py`); `_compose_file_fragments` claimed-file branch + a new `_entity_fragment`
   helper; the upstream chunk-skip gate on `claims()`. (`index/indexer.py` + 4 sites)
3. `Indexer._commit_batch_file` — the batch pass-two per-file compose gains the identical branch.
4. `Indexer._sweep_two_pass` completion — the phase-2 `resolve_edges(changed_scopes=None)` trigger +
   per-scope applier with F7 loud isolation.
5. The watcher/reconcile per-file handlers — `entity_purge_fragment` at the DELETE sites ONLY (node
   purge; edges cascade). **NO incremental edge re-resolution** (RULED non-feature — §Q3.2; edges
   re-resolve only at full-sweep completion). (`index/watcher.py`, `index/reconcile.py`)
6. `SurrealStore.delete_by_tier` — the tier entity purge co-located INSIDE it (F5 — the sink, covering
   all 5 callers). (`store/surreal.py`)
7. `build_app_context` — build the `ExtensionContext` EARLY (after `code_graph`); the phase-0
   ingest-backend ready loop on `write_stack_readied` (block 1); **add ingest backends to block-2
   teardown AND `AppContext`/`aclose` (F4)**; pass `server.extensions` + the ExtensionContext into the
   Indexer. (`server.py`)
8. Registry claim-exclusivity (at most one `claims()` per file, else loud error). (`Extension.name`
   charset is now OPTIONAL hygiene, not required — R3 reduced.)

**Test/fixture burden:** the `FakeIngestExtension` + `FakeDomainStore` fixture (a whole fake domain +
its slug-leading DDL); the contract for all five seams (inert defaults + overridden); the
transactionality mutation proof + the conjunction pin (§Q2.3); the `ENFORCED` dirty-store migration pin
(§Q3.4); the corruption-direction stale-edge pin (§Q3.3); **the CROSS-BOOK edge pin (F1)**; **the
partial-resolvability resolve-or-drop pin (F2)**; **the phase-2 partial-failure loud pin (F7)**; the
two-phase edge pins; the ordering-rail unwind pins for BOTH teardown blocks + normal close (F4); the
`xt_fake_` namespacing pin (≥2 names); the sink-based purge coverage (F5). Most run against
spike-surreal `:18000`.

### SPLIT RECOMMENDATION: **SPLIT** into 47 (design) / 47a (build)

The packet priced ~0.15 "design + build, split at kickoff if the design prices it over 0.25." It does,
and the R2 adversary pass RAISED the build (the F1 cross-book fixture, F2/F7 error-path pins, the F3
four-site Indexer thread, the F4 two-block teardown, the F5 in-`delete_by_tier` purge).
- **Design (47, this doc + adversary, now folded):** ~0.15.
- **Build (47a):** ~0.32–0.38 — 7 production files (+4 Indexer construction sites), a genuinely novel
  two-phase `ENFORCED` edge lifecycle whose cross-book correctness rests on the full-sweep path (F1), a
  fake-domain fixture WITH its own slug-leading DDL, dirty-store migration case, cross-book edge, and
  partial-resolvability legs, and ~13 load-bearing pins several needing spike-surreal + mutation proofs.
- **Total ~0.47–0.53 ≫ 0.25 → SPLIT (unchanged, reinforced).** One-line rationale: *the two-phase
  `ENFORCED` edge lifecycle plus a from-scratch fake-domain store with dirty-store + cross-book +
  partial-failure pins is a build packet in its own right, not a design-doc tail.*

---

## 9. SELF-ATTACK (survivors folded in; residuals for the adversary)

*"What WRONG build satisfies this design + a plausible contract and still fixes nothing?"* — each is a
required pin, cross-referenced to where it now lives:

1. **Manifest written OUTSIDE the transaction** (separate `apply`) — atomicity lost, happy-path green.
   → §Q2.3 mutation pin (force entity failure → manifest row ABSENT) + §Q5 "one `apply`" / prove-by-
   mutation.
2. **Claimed file skips chunking but composes NO entities** — "chunks absent" test passes, no entities
   land. → §Q6 POSITIVE assertion (entity rows PRESENT after apply), not merely "chunks absent".
3. **Phase-2 RELATE without `ENFORCED`** — dangling ghost written silently; happy-path (endpoints exist)
   green. → §Q3.4 `ENFORCED`-rejects-dangling positive control.
4. **Re-RELATE without purge-by-scope** (UPDATE-keeps-stale / DELETE-loses direction) — unchanged-edge
   re-ingest green. → §Q3.3 corruption-direction pin (change an edge target; assert ONLY the new edge).
5. **`ENFORCED` migrated with `IF NOT EXISTS`** — silent no-op on a dirty store (#107). → §Q3.4
   dirty-store migration pin (the one pin no virgin-DB fixture can produce — store ref §1.6).
6. **Purge coverage keyed on a method-name hand-list** — `delete_by_tier` (and any raw-DELETE tier
   wipe) silently exempt. → `[R2: F5]` §7 now puts the entity purge INSIDE `delete_by_tier` (the sink,
   all 5 callers) — no reach to enumerate.
7. **Namespacing pin uses a single-value fixture** — a build that namespaces only when `name=="fake"`
   passes. → §Q1.3 pin must use ≥2 extension names / a name ≠ the value the code could branch on
   (CLAUDE.md parameter-monoculture).
8. **`[R2: F1]` Cross-book edge build** — a build that handles only intra-book scope passes the whole
   (all-intra-book) first-draft fixture. → §Q6 cross-book edge pin.
9. **`[R2: F2]` Pass-unresolved-to-RELATE build** — a happy-path fixture (all endpoints resolve) is
   green while production denies whole scopes. → §Q6 partial-resolvability pin.

**Residual risks handed to the contract-adversary (NOT closed here) `[R2: updated]`:**
- **R1 — the phase-1↔phase-2 window** (§Q2.3/§Q3.3): a reader querying edges mid-index under-reports
  (window = the sweep's duration, MINUTES for a large corpus — F7 refinement). Named bound; the
  `edges_resolved` marker deferred to 52a/52b (dark tier). *Is the bound acceptable, or must 47 record
  the marker now?* — operator/adversary call.
- **R2 `[RULED 2026-08-14 — CLOSED]` — phase-2 is FULL-SWEEP-ONLY; incremental is a PINNED NON-FEATURE**
  (§Q3.2). The operator ruled it: D&D uses no incremental file watcher, so the incremental edge-
  resolution path is NOT built — which dissolves F1 by construction (every full re-crawl re-resolves ALL
  edges against ALL current nodes, so no cross-book edge is ever orphaned, and "newer wins" falls out of
  the same pass). No open question; the pinned non-feature carries a re-open trigger (a future extension
  wanting live per-file edge resolution).
- **R3 `[R2: REDUCED to non-issue]` — `Extension.name` charset** (§Q1.3): a cross-extension `xt_`
  collision is ARCHITECTURALLY IMPOSSIBLE (claim-exclusivity + per-scope-separate applies → no two
  extensions ever share a `compose()`); only intra-extension self-collision remains, caught loudly by
  `compose`. Charset constraint is optional hygiene. No open question.
- **R4 — `file_text` for claimed files** (§Q1.4): recommend WRITE (provenance); non-blocking.
- **R5 — claim exclusivity** (§Q1.2): at most one `claims()` per file, else loud error. Confirm no
  two-claimant silent-precedence path.
- **R6 — reach of the "prove by mutation" for ONE IMPLEMENTATION** (§Q5): the mutation must reach the
  ENTITY path specifically, not only the chunk/graph paths that already flow through `compose`.
- **R7 `[R2: F2/F7]` — phase-2 error semantics**: resolve-or-drop before RELATE (F2) + per-scope loud
  isolation (F7) are now specified + pinned. Adversary to confirm no swallowed-partial path survives.

---

## 10. Store-law citations used (by section, per the docs-first law)

`surrealdb-31-capabilities.md`: §1.1 (DDL decision rule; TABLE RELATION = `OVERWRITE`) · §1.5 (`DEFINE
TABLE OVERWRITE` safe, does not rebuild; positive control) · §1.6 (virgin-DB blind spot; the migration
pin pattern) · §2 (`UPDATE` of an edge endpoint is a silent no-op; edge self-delete on endpoint delete;
`UNIQUE`-array element-path; slug lookup) · §3 (`execute_transaction` checks every statement; never
`query()`) · §4 (`RELATE` bound-RecordID form; the dangling-edge hazard #105; `ENFORCED` guards both
endpoints, `OVERWRITE`-to-migrate, pre-existing danglers unaffected; `UNIQUE(in,out)` legal; dedupe
before RELATE). All CITED, never re-transcribed.
