# Packet 64 — ruling amendment 5 (sidecar-64, 2026-09-26): the standalone `lore-adm delete-keep` is NOT covered by amendment 1 — ruled into 64d-ii, sharing ONE disposition engine with the principal delete

Rules the lead's Task 9 (63c amendment 28 §E, `eb75f57`, routes the class beneath F-1 to 64).
Amends `…packet64-amendment-1.md` §4 (the `keep` row) and §7 (64d-ii's scope). Facts: `KeepStore.
delete_keep(keep_id)` (read this session) DELETEs the keep node after a check-first `get_keep`; its
`member_of` edges auto-cascade (store-ref §4, probed); its docstring carries the forward boundary
verbatim — *"when 63/64 add `scope='keep:<id>'` governed rows, `delete_keep` MUST revisit whether it
cascades or orphans them"*. A row's `scope` is a STRING (`keep:<id>`), not a record link (63-rulings
§4.1) — nothing cascades it, nothing dangles visibly; after the keep dies the row's scope matches no
member's `ScopeInKeeps` (the household edges are gone), so it is ADMIN-ONLY by construction (63-rulings
§2.3's fail-closed direction) — an ORPHAN that reads as a clean store to every member.

## Verdict: REFUTED — amendment 1 §4's `keep` row governs keeps kept by THE PRINCIPAL BEING DELETED only

The `--delete-obj` refusal (*"other household members OR rows scoped to it owned by ANOTHER
principal"*), the `--archive-obj` keep archive and the `--change-owner` `set_keeper` all run INSIDE
`PrincipalStore.delete`. `KeepStore.delete_keep` — reachable through `lore-adm delete-keep` and named by
`PrincipalHasKeepsError`'s own remedy text (*"delete the keep (lore-adm delete-keep) first"*) — has no
disposition, no pre-check and no audit. So the class 63c amendment 28 §E names is LIVE the moment any
governed table carries keep-scoped rows (memory and message already do at HEAD): `delete-keep` on a
populated keep orphans them silently.

## Ruling — `delete-keep` takes the SAME required choice; both verbs drive ONE disposition engine

- **Verb:** `lore-adm delete-keep --keep <id> (--delete-obj | --archive-obj | --change-scope
  <keep:id>)`. The option is REQUIRED iff the keep has ≥ 1 governed row scoped to it (any owner, any
  table of the derived governed set); a keep with ZERO scoped rows deletes as today (member_of cascade)
  and its receipt says `rows: 0`. No option with rows present ⇒ the byte-inert refusal that IS the
  preview: per-table scoped-row counts, the household size, and each option's consequence.
- **Dispositions (the amendment-1 semantics, keyed by SCOPE instead of OWNER):**
  - `--delete-obj` — DELETE every row scoped to the keep, whoever owns it (an admin act; ONE audit row
    per table, `action=DELETE`, `old_value={"scope": "keep:<id>", "count": N, "row_ids": <first K>}`),
    with the SAME per-table refusals amendment 1 §4 rules (a task with a surviving dependent OUTSIDE the
    population; a finding with a surviving successor outside it; an agent row is never deleted —
    retired+archived); then the keep node (member_of cascade).
  - `--archive-obj` — `keep.archived_at` (amendment 1 §4's keep archive): the keep node SURVIVES
    (hidden, frozen — `unarchive --table keep` restores), `member_of` survives with it, every scoped
    row is hidden by construction (`resolve_visible_keeps` excludes archived keeps) and requestable by
    its household with `include_archived`. Nothing is deleted; the verb's name notwithstanding, this is
    the retained-but-hidden outcome the operator named.
  - `--change-scope <keep:id>` — SET_SCOPE every scoped row to the target keep (ONE predicate UPDATE per
    table — `UPDATE <t> SET scope = $to WHERE scope = $from` — under `governed_exempt("delete-keep:
    change-scope", …)`, ONE audit row per table `action=SET_SCOPE`), then delete the source keep. Target
    validation BEFORE any write: exists, NOT archived, ≠ the source; the receipt names the target keep's
    household size (rows may become visible to a different household — the admin's judgement, served).
- **ONE ENGINE (the design point — ROUTING IS NOT SHARING):** 64d-ii builds `governed.dispose_population
  (population: RowPredicate, disposition, *, target, store, audit) -> DisposeReceipt` where
  `RowPredicate` is exactly one of `OwnedBy(principal_id)` (the principal delete) or `ScopedTo(keep_id)`
  (the keep delete) — the per-table pre-checks, the statement shapes, the audit rows, the receipts and
  the refusal-preview are written ONCE and parametrised by the predicate; the two CLI verbs are callers.
  `--change-owner` (owner-keyed) and `--change-scope` (scope-keyed) are the two TRANSFER shapes of one
  engine, never two copies. Proven by MUTATION: perturb one per-table refusal (e.g. drop the task-
  dependent check) → BOTH verbs' pins red.
- **`delete_keep` itself:** stays the store primitive (check-first, born-wrapped) and gains ONE guard:
  it REFUSES (typed, teaching, naming the count and `lore-adm delete-keep --…`) when any governed row is
  scoped to the keep — so a caller that bypasses the CLI (the #404 class: a future non-CLI caller)
  cannot orphan silently; the CLI's disposition path calls it LAST, after the rows are gone or moved.
  The docstring's forward boundary is discharged and rewritten.

## Pins — and pin it like this
1. **Refute-then-fix:** at HEAD, seed a keep with one scoped memory row, `delete_keep` → the row's scope
   names a dead keep and a member of the (now empty) household cannot read it while admin can — the
   orphan CONSTRUCTED (the pin's RED-at-HEAD reason); after 64d-ii, the same call REFUSES with the
   count.
2. Each disposition ∀ governed tables with a row in EACH, scoped to the keep, owned by TWO principals:
   delete-obj → rows gone, one audit row per table, keep gone, member_of gone; archive-obj → keep
   archived, rows hidden to members, requestable with the flag, nothing deleted; change-scope → rows
   carry the target scope, visible to the target's household, source keep gone; receipts = stamped rows.
3. The per-table refusals under `--delete-obj` for the SCOPE population (a dependent outside the keep;
   a successor outside it) — the same fixtures as amendment 1 §4, re-keyed by scope.
4. `--change-scope` target validation × {missing, archived, self} → refused, nothing written; the
   zero-rows keep deletes with no option and `rows: 0`.
5. The engine's mutation (one refusal dropped → both verbs red); an AST pin that `PrincipalStore.delete`
   and `_cmd_delete_keep` both CALL `dispose_population` and neither carries a per-table statement of
   its own.
6. `delete_keep`'s guard: a direct call on a populated keep refuses; on an empty keep proceeds.

## #488 annotation (done with this amendment)
The orphan class beneath F-1 (63c am-28 §E) is `delete-keep`'s, not the principal delete's; routed to
64d-ii by this amendment; #488's own subject (am-25 × orphaning) stays MOOT.

## Discipline
- 64d-ii sizing grows by ≈0.03 (one engine, two callers, one guard). Not MAJOR (the operator's OF-3
  family applied to the sibling verb the principal verb already names as its remedy).
- No code/tests/store touched; this doc only; no attribution trailer.
