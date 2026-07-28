# 43 — DERIVATION-SOURCE UNIFICATION (then the code-graph `ENFORCED` flip)
size ~0.20 wu (design pass first) · wave L · depends: — (independent) · **DEPLOY: yes** (the
indexer's write path changes)
law: `docs/reference/surrealdb-31-capabilities.md` §4 FIRST · repo CLAUDE.md ONE IMPLEMENTATION,
THE QUANTIFIER LAW, the routing rule (a DESIGN problem never reaches a builder)

## Provenance — why this packet exists
Split out of packet 04 by **operator ruling 2026-07-26**, when 04a's contract author settled a
condition packet 04's store probe had flagged but could not answer.

**The measured finding (`REPORT-contract-04a-enforced.md` §4.D2, committed `48537c3`):**
`{edge.src} ⊆ {node.qualified_name}` — the property the `refers`/`answers_to` `ENFORCED` flip
rests on — **holds for all 56 production modules and 8 deliberately adversarial source shapes,
and is NOT STRUCTURAL.** The two halves read *different inputs*:
- `_derive_nodes` reads **the chunk set the caller supplies**.
- `_derive_edges`' reference half **re-reads the file off disk**, deliberately fresh
  (`_resolve` → `evict_resolved_file`, because astroid caches a module by name).

`Indexer.index_file(tier, path, source)` takes `source` from its caller, **so a save landing
between the watcher's read and the derivation's read makes the two disagree.** MEASURED: with a
divergent chunk set over a live source, `build_file_graph_fragment` emits `refers` RELATEs whose
`src` `code_node` **no statement in the fragment ever creates**.

**Today that is an invisible dangling edge. After the `ENFORCED` flip it is a rejected RELATE that
aborts the transaction** — and the graph slice rides the SAME `store.apply` as the chunk /
`file_text` / manifest fragments (`Indexer._index_chunks`), so the file is isolated `failed`
(last-good retained, one WARNING) and **its chunks never update**. Self-healing under a save-race;
**permanent under any deterministic divergence.**

⚠ **The operator was offered the two local fixes (mint the missing node / drop the orphan edge)
and ruled for the ROOT fix instead: make both derivations read ONE source.** This packet is that
ruling.

## Why this is a DESIGN pass before it is a build
`_derive_edges` re-reads deliberately, and **the reason is load-bearing** (`graph.py`, the
`evict_resolved_file` call site documents it: astroid caches a module by name). Unifying the two
reads without first establishing *what that freshness protects against* risks reintroducing the
staleness bug it was written to prevent — trading a rare divergence for a common one.

**This is a property to INVENT, not a spec to IMPLEMENT.** Per the roster routing rule it does NOT
go to a builder with "work out the general form": an Opus author designs it and **adversarially
attacks its own design** before any builder sees it, or it escalates to the operator as a fork.

## Scope IN
1. **DESIGN PASS (first, and gated).** Answer, with receipts, before any code:
   - **Why does `_derive_edges` re-read?** Read `evict_resolved_file`'s call site and its history.
     What breaks if it stops? Name the failure it prevents; do not paraphrase the comment.
   - **Which source is CORRECT to unify on** — the caller-supplied `source`/chunk set, or a single
     fresh read shared by both halves? They are not symmetric: one risks staleness, the other
     risks disagreeing with what the caller believes it indexed.
   - **What does astroid's module-name cache do** to whichever answer wins? The eviction exists
     because of it.
   - **Deliverable:** a design doc + a recommendation. The operator rules; the author decides
     nothing.
2. **BUILD the unification**, once ruled.
3. **THEN the code-graph `ENFORCED` flip** — `refers` + `answers_to` gain `enforced=True`
   (`_refers_statements`, `_answers_to_statements`). Inherited from packet 04's ruled scope; it
   was blocked ONLY on this correctness issue. Store facts are already measured — see below.
4. **The ∀ pin, inherited from 04a's contract.** `test_a_DIVERGENT_chunk_set_still_yields_a_self_
   consistent_fragment` — *"never RELATE from an endpoint no earlier statement of the SAME fragment
   created"*, **statement-ORDERED** (the check is at RELATE time, per-record; order IS the
   contract). ⚠ Pin the ∀ property, **never** "our 56 modules are clean" — an invariant conditioned
   on the inputs that happened to be tested is THE QUANTIFIER LAW violated.
5. **#248 (slotted 2026-07-27; same seams and provenance — the D-d parse):** SEVEN hand-rolled
   `_bare_id` copies package-wide, each with its own private `_TABLE_SEPARATOR` — the parse D-d
   proved easy to get wrong (130 red pins). Consolidate to ONE implementation while in these
   seams, with a per-site mutation proof (change the separator/mint → every caller's pin must
   redden; a caller that stays green is a private copy wearing the shared name). ⚠ SEPARABLE:
   if this pushes the packet past the sizing law at kickoff, it SPLITS OUT with its own row —
   never silently dropped.

## Scope OUT
- The `briefed` flip, the app-level unknown-agent check, `blocks`, fleet columns, `_comms_footer`,
  #219 — all packet 04a/04b.
- Any widening of what the indexer indexes. This packet changes WHICH SOURCE two derivations read;
  it is not an indexer feature.

## Entry check
- **FIRST READ** `docs/reference/surrealdb-31-capabilities.md` (§4 GRAPH/RELATE at minimum).
- Packet 04's probe + contract receipts, `docs/plans/v2/receipts/2026-07-26-packet04/` — the store
  facts are ALREADY MEASURED on 3.2.1. **Do NOT re-probe:** `ENFORCED` resolves endpoints created
  earlier in the SAME uncommitted transaction (both controls held); `IF NOT EXISTS` is a silent
  no-op and `OVERWRITE` lands the flip preserving rows/fields/index/enforcement; a dangling edge
  still reads as a FIRST-CLASS member of the identity traversal on 3.2.1.
- ⚠ **Re-derive the 56/8 corpus result before relying on it** — it is a fact about the tree on
  2026-07-26, and this packet exists precisely because it is not a property.

## Exit
Design doc ruled → gates green (`pytest -n auto` with a passed-COUNT, `scripts/typecheck.sh`,
ruff) → cold REFUTE audit → deploy BOTH (rebuild + recreate, never restart) → the ∀ pin
mutation-proven (break the fragment builder, watch it go RED, restore) → INDEX row + Log →
ledger row done.
⚠ **A deploy here touches the INDEXER's write path** — the hottest path in the system. The smoke
must index a real file and prove the graph slice still lands, not merely that the container boots.
