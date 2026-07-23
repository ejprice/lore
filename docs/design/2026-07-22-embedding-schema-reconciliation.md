# Embedding-schema reconciliation: diff-driven, not full-rebuild

**Status:** DESIGN PROPOSAL — awaiting operator ruling. Supersedes [#168], folds in [#169],
adopts [#170]. Author: surreal-321-migration-lead (Opus), 2026-07-22. Finalized by the Fable
design sidecar 2026-07-22: Q1–Q6 are all DECIDED (§12); the operator reviews the whole design;
§13 carries the residual flags. Two defects in the v1 proposal were found and corrected during
finalization — they are labeled D1/D2 in §11.

## 1. Problem

As of 2026-07-22, `embedding_schema_fingerprint` (`loremaster.index.schema`) hashes ALL
schema-relevant config — the embedder fields **and the entire `chunkers` map** — into one opaque
SHA-256, stored in `meta` as `embedding_schema_fingerprint`. On boot, if stored ≠ computed,
`rebuild_all` re-embeds the **entire corpus**.

The fingerprint answers exactly **one bit**: *"did anything change?"* It cannot answer *"WHAT
changed, and what is the minimal correct reaction?"* So every change — however narrow — costs a
full rebuild.

**Lived 2026-07-22 ([#167]/[#168]):** adding `.mdx → markdown` and `.surql → text` chunker
mappings for two new vendor tiers flipped the fingerprint and triggered a full **2764-file /
~17k-chunk** re-embed — even though nothing about how the existing `.py`/`.md` files chunk or
embed changed. The re-embed then died twice on transient TEI failures ([#169]) and had to be
reconciled by hand-stamping the fingerprint. **Under the design below, that change would have
been a zero-embed reconcile** — which is the whole point.

Cost priority (operator ruling, 2026-07-22, in [#168]): *"TEI is relatively free. Voyage cloud is
not."* Embedding — the TEI/cloud call — is the expensive unit; chunking is CPU we own. The design
therefore scopes EMBEDS to real diffs and treats re-CHUNKING as cheap.

## 2. Goal / non-goals

**Goal.** Store the STRUCTURED schema in SurrealDB. On boot, DIFF stored-vs-config and reconcile
only the diff with the minimal correct action per change — and inside each re-chunked file,
re-embed only the CHUNKS that actually changed (§5).

**Non-goals.** Not changing the embedder or the vector store. Not weakening correctness: an
**unrecognized** diff still falls back to a full re-embed (fail-safe toward correctness — §8).
Not closing the chunker-CODE-change blind spot — that is pinned as a known bound (§10).

## 3. The stored schema

Replace the opaque fingerprint blob with a STRUCTURED, versioned `embedding_schema` blob — the
one source of truth for diffing — grouping fields by **what a change to them invalidates**:

```json
{
  "schema_version": 2,
  "embedder":  { "backend", "model", "dim", "endpoint",
                 "query_prompt_name", "document_prompt_name" },
  "chunking":  { "max_input_tokens", "tokenizer", "truncate" },
  "chunkers":  {
    "python_ast": { "version": 1, "bindings": { ".py": {} } },
    "markdown":   { "version": 1, "bindings": { ".md": {}, ".mdx": {} } },
    "text":       { "version": 1, "bindings": { ".surql": {}, ".txt": {} } }
  }
}
```

- **Key-centric chunkers component (Q4, §6).** Keyed by chunker KEY, not extension. `bindings` is
  the EFFECTIVE routing surface for that key — the union of config overrides
  (`LoreConfig.chunkers`, whose per-extension config dicts ride here verbatim) and
  code-registered default suffixes, as the live registry resolves them. A predicate chunker (one
  that claims files via `Chunker.handles`, e.g. a future `Dockerfile` chunker) appears with
  `"predicate": true` plus any suffix bindings it also owns — its claimed FILE SET is code, not
  config, and is reconciled by the routing sweep (§6), never derived from this blob.
- **`version` (Q3, §10).** A per-chunker behavior epoch declared by the chunker itself
  (`Chunker.version`, an int class attribute on the lorescribe base, default 1). Bumping it is
  the proportionate escape hatch for a chunker whose CODE changed behavior.
- **Derived fingerprint (Q1 — ruled).** The legacy `embedding_schema_fingerprint` meta key
  remains as a DERIVED fast-path gate — sha256 of the canonical-JSON blob — recomputed FROM the
  blob, never stored independently of it. Match ⇒ skip the diff entirely (the every-boot cheap
  path); mismatch ⇒ run the diff. One source of truth; the fingerprint is a cache of it.

## 4. The change classes (the core model)

Every schema-relevant field falls into exactly one class, keyed on **what a change invalidates**:

| Class | Fields | A change invalidates | Minimal action |
|---|---|---|---|
| **Vector identity** | `embedder.*` (model, dim, backend, endpoint, prompt names) | EVERY vector (same text → different vector) | **REEMBED_ALL**: re-chunk + re-embed everything, NO vector reuse |
| **Chunk boundaries** | `chunking.*` (max_input_tokens, tokenizer, truncate) | chunk BOUNDARIES (files may split differently) | **RECHUNK_ALL**: re-chunk every file (CPU), embed only hash-diffs (§5) |
| **Chunker map / version** | `chunkers.*` (bindings, per-binding config, `version`) | only files ROUTED through the changed key/binding | **routing sweep** (§6): per-file re-route + scoped RECHUNK with §5 reuse |
| **Anything else** | a new/unknown field, an unparseable blob | unknown | **REEMBED_ALL** (fail-safe, §8) |

Actions collapse to the widest (`REEMBED_ALL` > `RECHUNK_ALL` > scoped) — never a narrower
action AND its superset.

Two corrections to this table's v1 (receipts in §11, D1/D2):

- **REEMBED_ALL re-chunks too.** v1 said "re-embed all chunks — no re-chunk; boundaries are
  unchanged". That is IMPOSSIBLE: the embed input (`Chunk.embedding_text`) is **not persisted**
  ([#170] — the chunk row's `content_hash` is the FILE sha512 per `records.py`, `ident_text` is a
  divergent identity rendering, and the [#170] hash added by this design cannot reconstruct
  text). So a vector-identity change re-chunks every file purely to RECOVER the embed inputs —
  CPU-only, boundaries and identities stable — then embeds all of them (no reuse: the
  text→vector function itself changed).
- **A chunker-map ADD is NOT a no-op.** v1 said an added binding needs nothing because "new files
  are picked up by the normal reconcile walk". False for files already walked: an unclaimed file
  is committed as a **zero-chunk `indexed` row** precisely so the walk never re-reads it
  (`Indexer._index_chunks` docstring), and the mtime/sha fast-path (`Indexer.index_file`) then
  skips it forever. A newly-added chunker that claims such files would never run. The routing
  sweep (§6) closes this: the stored `chunker_key` (None) vs the new resolution (the added key)
  is a per-file mismatch → re-chunk. For an extension genuinely absent from the corpus, the sweep
  finds zero mismatches — the [#168] invariant (add a `.xyz` chunker with no `.xyz` files ⇒ ZERO
  embeds) holds by construction.

## 5. The chunk-level diff (Q2 — content-addressed vector reuse)

**The enabler is [#170] (Q6 — ruled): persist `embedding_text_sha512 = sha512(Chunk.embedding_text)`
on every chunk row**, computed at index time inside `Indexer._index_chunks` from the REAL
`embedding_text` (`metadata_header + "\n" + source_text`, `lorescribe.models.Chunk`) — never
reconstructed from `ident_text` (the reconstruction is exactly what handed [#167]'s verification
a false 0.98). DDL: an additive field via `DEFINE FIELD OVERWRITE` — the field-migration decision
rule in `docs/reference/surrealdb-31-capabilities.md` (cited, not restated; `IF NOT EXISTS` on an
existing field is the [#107] silent no-op).

**The per-file RECHUNK algorithm** (one file, under any scoped or RECHUNK_ALL action):

1. Re-chunk the file's source through the registry (CPU only, no embed).
2. For each fresh chunk compute `h = sha512(chunk.embedding_text)`.
3. Read the stored `(embedding_text_sha512, vector)` pairs for `(tier, file_path)` (one new
   store read, §13.4).
4. **Multiset match on the hash**: a fresh chunk whose `h` equals a stored chunk's hash REUSES
   that stored vector (no embed call); every miss goes to the embedder, batched. Duplicate hashes
   are matched by count; reusing one stored vector for two byte-identical fresh chunks is sound
   (same input ⇒ same vector).
5. Commit through the existing per-file atomic replace (`SurrealStore.replace_file` /
   upsert-new-before-purge with `delete_points` on stale ids): rows are rewritten wholesale
   (rows are cheap; line numbers/ordinals may shift), vectors are reused or fresh, old chunks are
   purged by the same idiom that already keeps per-file updates orphan-free.

**Soundness.** vector = f(embedding_text; vector-identity fields). The reuse path is reachable
ONLY from RECHUNK actions, which exist ONLY when the diff's vector-identity component is
unchanged (dominance, §4) — so byte-equal input ⟹ equal vector. Determinism receipt: [#167]'s
gold-standard verification measured cosine(stored, fresh-re-embed) = 1.000000 across all three
tiers with a determinism control = 1.000000 (2026-07-22, TEI voyage-4-nano). A false "unchanged"
requires a sha512 collision; there is no weaker heuristic anywhere in the diff.

**SPLIT/MERGE — the hard case, stressed:**

- **Split** A → A1+A2: neither new hash matches A's → BOTH embedded; A's row purged by the
  replace. Correct — both texts are genuinely new embed inputs.
- **Merge** A+B → C: C misses → embedded; A and B purged.
- **Boundary nudge**: both adjacent chunks change text → both embedded; every untouched sibling
  hash-hits → reused. A `max_input_tokens` change thus re-embeds ONLY files with chunks near the
  cap — everyone else re-chunks to byte-identical texts and embeds nothing. (This retires v1's
  open Q2: the "conservative RECHUNK_ALL, optimize later" fork is moot — re-chunking is the cheap
  half, and the hash scopes the expensive half with no per-file max-token record needed.)
- **Header drift**: a chunk whose `source_text` is untouched but whose Section breadcrumb changed
  (a heading above it reworded) has a DIFFERENT `embedding_text` → hash miss → re-embedded.
  Correct and load-bearing: the header is part of the embed input, and any identity/ordinal-based
  "unchanged" heuristic would wrongly keep the stale vector — the reason the diff keys on the
  [#170] hash and on nothing else.
- **Unhashed stored rows** (pre-migration, or a failed backfill): no match possible → the whole
  file embeds. Fail-safe degradation; converges as rows gain hashes.
- **Scope**: reuse looks only within the same `(tier, file_path)`. Cross-file reuse (renames,
  copied files) is deliberately NOT taken: renames are the normal reconcile's domain, and
  per-file scope keeps the vector read bounded. Ledger it as a later optimization if measured to
  matter.

## 6. Routing reconciliation (Q4 — DECIDED: per-file assignment against the registry)

**DECISION: the chunker-map class is diffed by CHUNKER KEY, and the affected file-set is resolved
by the REGISTRY'S OWN ROUTING — concretely, by comparing each file's STORED routing assignment
against a fresh resolution, per file, on every sweep.** "Extension" never appears in the
reconciler; it is just the common case inside the resolver.

**The shared resolver must be BUILT — it does not exist.** As of 2026-07-22,
`ChunkerRegistry.dispatch_file` INLINES the three-tier selection (config override for the suffix >
first registered `handles()` predicate excluding the suffix-owner > default suffix map > None) and
immediately chunks. Extract it — do not add a sibling:
`ChunkerRegistry.resolve(path) -> RoutingDecision {key: str | None, via: override|predicate|suffix|none}`,
with `dispatch_file` = `resolve` + chunk. ONE implementation (the [#102] law): the reconciler
calls `resolve`; it never re-derives suffix matching, `_normalise_extension`, or precedence.
Mutation proof required at contract time: perturb the precedence inside `resolve` in a scratch
build → dispatch behavior AND reconcile scope must shift TOGETHER; a reconciler that stays green
is a private copy wearing the shared name.

**Constraint to pin: the resolver is PATH-PURE.** `Chunker.handles(path)` takes the path only
(true of the base contract as of 2026-07-22) — which is what makes resolution free of I/O. A
future content-sniffing chunker would break this; that is a design escalation, and a pin should
make it one (a test asserting `resolve` performs no file reads).

**The routing sweep** — rides EVERY sweep walk (boot and periodic), not only on a fingerprint
flip, because resolution is path-pure dict/predicate work (~milliseconds for the 2,766-file
corpus measured 2026-07-22) and because ONLY a live re-resolution catches code-level routing
changes (a new or changed predicate, a changed default registration) that no stored-config diff
can see. Per walked file, compare `resolve(path).key` against the stored `FileRow.chunker_key`
(§7):

| Comparison | Meaning | Action |
|---|---|---|
| stored == fresh, key's `version`/binding-config unchanged | routing stable | nothing (schema-wise) |
| stored == fresh, key's `version` or matched binding-config CHANGED in the blob diff | same route, new behavior declared | RECHUNK(file) with §5 reuse |
| stored ≠ fresh, fresh non-None | re-routed — incl. an ADD claiming a previously-unclaimed zero-chunk file (§4-D1) | RECHUNK(file) with §5 reuse |
| stored ≠ fresh, fresh None | binding removed | **DROP**: `delete_by_file`, row becomes zero-chunk with `chunker_key = None` (mirrors today's unclaimed-file row, so the walk stays fast-path-able) |

This converges PER FILE with no global stamp: a crash mid-sweep leaves converged rows converged,
and the next sweep re-detects only the rest.

**Rejected alternative — per-EXTENSION diff of the config map** (v1 §4): it cannot see
name/predicate-keyed chunkers (the odoo manifest/csv chunkers to come), cannot see code-registered
default-map changes, diverges from the real three-tier precedence, would re-derive extension
normalisation (copy #2 of `_normalise_extension`), and — decisive — it inherits D1: an ADD it
classifies as NOOP strands already-walked zero-chunk files forever. For today's extension-only
config the sweep is behavior-identical to the per-extension diff, so this is a pure
correctness/generality win at equal cost.

## 7. The reconciliation executor (folds in [#169])

**The executor IS the sweep walk — not a sibling of it.** `rebuild_all` /
`_rebuild_all_realtime` RETIRE. One walk (`Indexer._walk_and_index` extended) serves initial
indexing, periodic reconcile, watcher-triggered sweeps, and schema reconciliation. This dissolves
[#169]'s central tell — "two embed paths wrapping the same embedder with different tolerance" —
by DELETING the weaker path rather than hardening it (the ONE-IMPLEMENTATION law applied to a
pipeline). The old rebuild's restart-from-zero shape came from its unconditional
purge-then-rewalk (each tier's rows deleted up front, so no progress survives a crash); the
executor purges nothing up front.

**Per-file state (the checkpoint).** `FileRow` gains two additive fields:

- `chunker_key: str | None` — the registry key that produced this row's chunks (None =
  walked-but-unclaimed). Written by `_index_chunks` on every commit.
- `schema_fingerprint: str | None` — the derived fingerprint (§3) the row was last indexed
  under. Written by `_index_chunks` on every commit.

Both ride the existing per-file composed transaction (`_index_chunks` → `replace_file`), so
per-file atomicity is inherited, not rebuilt. DDL: additive fields, `DEFINE FIELD OVERWRITE`
(store reference, as in §5).

**The pending predicate** (pure, per walked file) — a file needs work iff any of:

- **P1** `row.schema_fingerprint != current_derived_fingerprint` — a schema action has not yet
  been applied to it;
- **P2** routing mismatch (§6);
- **P3** the normal content-freshness triggers (mtime+size, then sha512) — today's reconcile,
  unchanged.

**The per-file action for a pending file** is derived from the DIFF, not from a global mode:
vector-identity change → re-chunk + embed all (no reuse); boundary change, in-scope chunker
change, or P2 → re-chunk + §5 hash-scoped embed; P1 with a diff that touches nothing this file
routes through (e.g. a pure binding ADD with no affected files) → **RESTAMP only** (write
`schema_fingerprint`; zero chunk work; implementable as a bulk UPDATE when the whole action set
is empty). Every commit stamps `schema_fingerprint = current` + `chunker_key = resolved`.

**Resume for free.** The per-file stamps ARE the checkpoint: a crash leaves completed rows
carrying the current fingerprint; the next sweep re-derives the diff (the stored blob is still
the OLD one — see stamping below) and P1 excludes the finished rows. A further config change
before convergence composes correctly: rows stamped with the intermediate fingerprint still fail
P1 against the newest → pending again. No separate progress ledger exists to drift.

**Retry (transient tolerance).** Embed failures classified transient (the TEI `status: null`
connection case that killed both [#167] attempts) are retried with bounded exponential backoff +
jitter AT THE EMBED CALL, in the one shared embed wrapper the walk uses — one implementation of
the policy, shared by every path (there is only one path left). On exhaustion the FILE is marked
failed and the walk CONTINUES (the same per-file isolation `index_file` already applies to
chunker exceptions) — one flaky batch never kills a sweep. Failed files keep their old
`schema_fingerprint` → still pending → retried on the next sweep with fresh backoff.

**Terminal states — never an unowned `failed`.** At sweep end:

- zero pending → **stamp the `embedding_schema` blob + derived fingerprint** (the crash-safety
  contract, unchanged from today: the global stamp is written LAST, only on full success);
- pending/failed remain → do NOT stamp; write `schema_reconcile_status =
  {state: "degraded", pending, failed, next_retry_at}` — an owned, self-retrying state (the
  periodic reconcile is the retry path), replacing [#167]'s dead `{state: failed}` that sat
  orphaned for ≥1h.

**Progress honesty.** `done`/`total` derive from the manifest's pending count — the SAME
population the walk visits. ([#167]'s stall shape: `total` counted all roots while static tiers
were version-stamp-skipped, so `done 355/2766` could never complete. Deriving both numbers from
one population makes that class unrepresentable.)

**Static tiers.** A pending static file is read from the materialized snapshot (in-container
after [#165]); per-tier VERSION stamps stay orthogonal (they gate tier CONTENT, not embedding
schema). The `_index_static_tier` skip logic (FP-05 three-way) gains one condition: a static tier
with schema-pending rows is WALKED from its existing snapshot (no re-acquire — the tier version
is unchanged) even when its version stamp matches.

**Concurrency.** The reconcile sweep holds the same single-writer serialization the rebuild holds
today (the startup path holds the watcher's writer lock). A live watcher event between sweeps
writes through `_index_chunks`, which now always stamps `schema_fingerprint` + `chunker_key` —
every writer converges rows toward the current schema; no writer can produce an unstamped row.

## 8. Fail-safe principle

The diff optimization applies ONLY to changes classifiable into §4. Anything else — a new schema
field, an unrecognized value shape, an unknown `schema_version`, a stored blob that fails to
parse — routes to `REEMBED_ALL`, executed by the §7 executor (so even the fail-safe is resilient
and resumable). The design never *under*-reconciles: worst case it degrades to today's behavior
(full rebuild), never to a stale index.

## 9. Migration (from fingerprint-only) — validated against the [#167] hand-stamp

First boot under the new design finds no structured blob:

1. Compute the **LEGACY-SHAPE** fingerprint — the exact epoch-2 `embedding_schema_fingerprint`
   payload, kept frozen INSIDE the bridge only (the new blob hashes differently; comparing the
   new derivation against the old stamp would spuriously mismatch on every migration).
2. **MATCH** against the stored legacy stamp → the corpus is converged: write the structured blob
   + new derived fingerprint; bulk-backfill `FileRow.schema_fingerprint = current` and
   `chunker_key = resolve(path)` (CPU-only); schedule the one-time chunk-hash backfill (below).
   **Zero embeds.** — Checked against the exact state the [#167] close-out hand-stamped
   (meta `embedding_schema_fingerprint = f6e2ee34…` == the legacy-computed config fingerprint;
   `schema_rebuild_status` → idle): the bridge takes THIS branch, so the first boot after deploy
   performs no embed work. The hand-stamp becomes the automatic path. Pin it: a migration test
   whose fixture is those exact meta values, asserting zero embed calls.
3. **MISMATCH** → no structured prior to diff against → one-time `REEMBED_ALL`, but executed by
   the §7 executor (per-file stamps, retries, resume) — the fallback full rebuild is no longer
   the [#167] die-from-zero shape. Then all future changes are diff-driven.

**Chunk-hash backfill (one-time, CPU-only, rides a sweep):** re-chunk each file; where the fresh
chunk multiset matches the stored rows (by identity + `source_text`), stamp each row's
`embedding_text_sha512` with the sha512 of the FRESH `embedding_text` — re-derived through the
real chunker, the [#167] gold-standard method, never reconstructed from `ident_text` ([#170]'s
false 0.98). Where it does NOT match, the stored chunks are provably stale under current
code+config → re-index that file (fail-safe; the expected divergent set is zero — the live corpus
re-chunked byte-identically at the [#167] verification, cosine 1.000000 across all three tiers,
2026-07-22). Honest bound: the stamped hash attests what the CURRENT chunker derives, which
equals what was embedded historically only because chunking is deterministic and the corpus was
verified converged; any silent pre-migration drift belongs to the §10 bound.

## 10. The chunker-CODE-change blind spot (Q3 — DECIDED: pin the bound, epoch hatches, no hashing)

**The bound:** a chunker's IMPLEMENTATION changes behavior while its key and bindings do not
(`markdown` upgraded; `.md → markdown` unchanged) → the schema diff sees nothing → stale chunks
under new logic. Today's fingerprint has the identical hole (it hashes chunker CONFIG, not CODE).
This design tracks chunker *identity and declared version*, not *implementation* — and must not
pretend otherwise.

**DECISION: pin it as a KNOWN BOUND** (per "WHEN YOU CANNOT CLOSE A HOLE, PIN IT", [#137]-style),
with TWO named escape hatches, proportionate then global:

1. **`Chunker.version`** — an int class attribute on the lorescribe `Chunker` base (default 1),
   carried per key into the §3 blob. An author who changes chunking BEHAVIOR bumps it → the diff
   sees a version REPLACE for that key → re-chunks exactly that key's files, and §5 re-embeds
   only the chunks whose output actually changed. A behavior-neutral refactor ships without a
   bump at zero cost. Precedent receipt: `EMBEDDING_SCHEMA_VERSION` epoch 2 exists precisely
   because a chunker-code change (python_ast composed-sizing, per the epoch history in
   `loremaster.index.schema`, read 2026-07-22) forced a GLOBAL rebuild; under this design the
   same change is `python_ast.version += 1` → `.py` files re-chunk, only genuinely-changed chunks
   re-embed.
2. **`EMBEDDING_SCHEMA_VERSION`** — retained as the global sledgehammer for changes to the
   canonical embedding-text format itself (its documented purpose). Bump → fingerprint flips →
   `REEMBED_ALL`.

**The pin (the instrument, shipped with the law):** a repo test asserting the §3 blob's
`chunkers` component derives from declared identity/version/bindings ONLY — no source, bytecode,
or package-version hash — going RED the day someone closes the bound, with a message naming this
section and the re-open trigger. **Named re-open trigger:** a [#167]-class incident caused by an
UNBUMPED chunker behavior change reaching production stale chunks — that is empirical evidence
the manual-bump contract failed, and the trade gets re-decided then, deliberately.

**REJECTED: chunker-implementation hashing** (source / bytecode / dependency-closure). It lies in
both directions: over-inclusive (a comment edit or refactor flips it → unnecessary mass
re-chunks — [#168]'s disease at higher frequency) and under-inclusive (behavior lives in helper
functions, base classes, the tokenizer library, dependency versions — outside any boundable hash
surface). Bounding the closure of code a chunker's OUTPUT depends on is the [#137] shape: not
closable without demanding the whole transitive world, and an instrument that is wrong in both
directions teaches false confidence. Also rejected: hashing the lorescribe package version —
flips on every release regardless of chunker behavior, pure over-breadth. The honest statement is
that the bound is open, pinned, and priced: an unbumped behavior change is invisible BY
DECLARATION, and the escape hatch costs one integer.

## 11. Adversarial self-critique (the design attacking itself)

**Defects found IN THE V1 PROPOSAL during finalization** (the adversary leg working — both are
corrected above):

- **D1 — "ADD → NOOP" was wrong.** v1 §4 claimed a new binding needs nothing because the normal
  walk picks up new files. Receipts: `Indexer._index_chunks` commits an unclaimed file as a
  zero-chunk `indexed` row "so a directory walk never re-reads it", and `Indexer.index_file`'s
  sha-match fast-path skips it thereafter. A chunker added for files ALREADY WALKED unclaimed
  would never run — a permanent stale miss, in the design meant to end stale misses. Fixed by the
  §6 routing sweep (stored `chunker_key=None` ≠ fresh resolution). The narrow [#168] receipt
  case (extension absent from the corpus) still costs zero embeds.
- **D2 — REEMBED_ALL "no re-chunk" was impossible.** The embed input is not persisted ([#170]);
  a hash cannot reconstruct text. Corrected: re-chunk (CPU) to recover inputs; no reuse.

**Standing risks, each with its disposition:**

- **The resolver could be re-derived instead of extracted** — the exact [#102] clone shape. §6
  mandates extraction from `dispatch_file` + a mutation proof (perturb precedence → dispatch and
  reconcile must shift together).
- **Path-purity of `handles`** is load-bearing for the sweep's cost and I/O-freedom; a future
  content-sniffing chunker breaks it silently. Pinned (§6): `resolve` performs no file reads.
- **The frozen legacy-shape fingerprint in the bridge** (§9) is a copy that could drift from what
  epoch-2 production actually stamped. Pinned: the migration fixture uses the EXACT [#167]
  hand-stamped meta values (`f6e2ee34…`, idle status) and asserts the zero-embed branch.
- **Reuse under a vector-identity change would serve stale vectors** — structurally unreachable
  (dominance, §4/§5), and pinned anyway: change `model` in a fixture, assert ZERO reused vectors.
- **Blob parse failure / unknown field** → `REEMBED_ALL` (§8), never a crash-loop and never a
  silent skip.
- **Watcher-vs-sweep write races**: inherited single-writer lock, plus both writers stamp rows
  identically (§7) — no writer can leave a row un-stamped.
- **Vector-read cost of reuse**: hash-hits read stored vectors from the store — bounded per file,
  trivial against an embed call; a skip-write micro-optimisation (identical row + hash ⇒ no
  rewrite) is left to implementation.
- **Fixture-discrimination demands for the contract phase** (what wrong build would pass?): the
  `.xyz`-add zero-embed pin ([#168]'s invariant); the D1 pin (an ADD claiming an existing
  zero-chunk row gets indexed); a split/merge EXACT-COUNT pin (a file where exactly K chunks
  change → exactly K embed calls, counted at the embedder seam — a ≥-assertion would pass a
  reuse-free build); a kill-mid-sweep resume pin (embeds-after-restart strictly < total — a
  restart-from-zero build must go RED); the [#169] transient-injection pin (inject one failing
  batch, assert the sweep converges); the §6 resolver mutation pin; per repo law, concurrency
  pins at ≥8-way where contention applies, and no fixture value monoculture (at least one
  non-default chunker key, one predicate chunker, one static tier in the fixtures).
- **Validation against [#167]:** the triggering change (two ADDed bindings for new-tier
  extensions) reconciles as: fingerprint flips → diff → chunker-map ADDs → routing sweep finds
  zero re-routed files in the pre-existing tier → bulk RESTAMP + blob stamp. Zero embeds, zero
  TEI exposure, nothing to die mid-flight. The design would have entirely prevented the incident
  that motivated it — and had the fail-safe fired instead, the §7 executor would have survived
  the TEI flake that killed both real attempts.

## 12. Decisions log (all questions CLOSED at design level)

1. **Q1 — legacy fingerprint (operator-ruled):** kept, DERIVED from the blob (§3). One source of
   truth; the fingerprint is a cache.
2. **Q2 — chunk-boundary changes (operator-ruled, mechanism specified here):** re-chunk affected
   files (CPU), re-embed ONLY hash-diffed chunks via content-addressed reuse (§5). The v1
   "conservative RECHUNK_ALL vs bounded later" fork is retired — the bounded version is the
   shipped version and needs no new per-file record beyond [#170]'s hash.
3. **Q3 — chunker-code blind spot (DECIDED by the design sidecar):** pin as a KNOWN BOUND with
   two epoch hatches — per-chunker `Chunker.version` (proportionate) and
   `EMBEDDING_SCHEMA_VERSION` (global); implementation hashing REJECTED as wrong in both
   directions (§10).
4. **Q4 — per-extension vs per-key (DECIDED by the design sidecar):** diff by chunker KEY;
   affected files resolved per-file by the registry's own routing via an EXTRACTED shared
   `ChunkerRegistry.resolve` (§6); per-extension diff rejected (misses predicate/name-keyed
   chunkers and code-level routing changes, and inherits D1).
5. **Q5 — packet placement (operator-ruled):** its own packet, superseding [#168] and [#169].
6. **Q6 — [#170] synergy (operator-ruled):** adopted; the per-chunk `embedding_text_sha512` is
   stored on the chunk row and is the ONLY key the chunk diff matches on (§5).

## 13. Residual flags for the operator (new, surfaced by finalization)

1. **Cloud cost gate.** The executor knows its embed bill up front (the pending-chunk count).
   On a PAID embedder (Voyage cloud), should a config threshold pause a large reconcile in an
   owned `awaiting_confirmation` state instead of auto-spending? The §8 fail-safe `REEMBED_ALL`
   is the residual surprise-bill path this would close. *Recommendation: yes, as a small
   follow-on — default unlimited on TEI/self-hosted; not load-bearing for this packet.*
2. **`Chunker.version` is a lorescribe base-class addition** — a cross-package contract change
   (every chunker inherits default 1; no per-chunker edits needed at introduction). Flagged as
   scope, not risk.
3. **Served-surface rename:** `schema_rebuild_status` → `schema_reconcile_status` and the retirement
   of `rebuild_all` change what `lore_index`/`index_status` render. Rename law applies (bare-grep
   sweeps for the retired names, incl. prose; the P8d class). *Recommendation: hard cutover with
   sweep, no alias — the old key names a mechanism that no longer exists, and an alias would be
   prose teaching a retired name.*
4. **One new store read** — `(embedding_text_sha512, vector)` pairs by `(tier, file_path)` —
   additive store surface, follows the store reference's idioms.

## 14. What this changes in the codebase (orientation, not a spec)

- `loremaster/index/schema.py`: structured `embedding_schema()` producer + `diff(stored,
  current) → action classes`; `embedding_schema_fingerprint` becomes a derived helper over the
  blob; the frozen legacy-shape payload moves into the migration bridge.
- `lorescribe/registry.py`: EXTRACT `ChunkerRegistry.resolve(path) → RoutingDecision` from
  `dispatch_file` (§6). `lorescribe/base.py`: `Chunker.version` (§10).
- `loremaster/index/manifest.py` (`FileRow`) + the manifest DDL: additive `chunker_key`,
  `schema_fingerprint` (§7). Chunk-row DDL: additive `embedding_text_sha512` (§5). All via
  `DEFINE FIELD OVERWRITE` per `docs/reference/surrealdb-31-capabilities.md`.
- `loremaster/index/indexer.py`: `_index_chunks` stamps the new per-file fields + computes the
  chunk hash; `_walk_and_index` gains the pending predicate + routing sweep + per-file action
  dispatch; `rebuild_all` / `_rebuild_all_realtime` retire; the embed call gains the one shared
  transient-retry wrapper (§7); `_index_static_tier`'s skip gains the schema-pending condition.
- `loremaster/store/surreal.py`: one new read (§13.4); `delete_by_file` / `replace_file` /
  `delete_points` reused as-is.
- `loremaster/server.py` startup (`build_app_context` → the schema check): fingerprint fast-path →
  diff → dispatch the executor; the migration bridge (§9) runs where the absent-blob case lands.
- `meta`: `embedding_schema` (new structured blob) + `embedding_schema_fingerprint` (now derived)
  + `schema_reconcile_status` (replaces `schema_rebuild_status`).
