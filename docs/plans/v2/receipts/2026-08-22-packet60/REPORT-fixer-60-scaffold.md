# REPORT-fixer-60-scaffold

brief-base v14 read
brief project v7 read

## SUMMARY
- **State:** done-with-deviations — fixed the ONE dropped stale site the brief named (`_enforced_relations_scaffold.py:92-95`) AND a SECOND genuinely-stale site of the same class in the same file (`:123-128`), surfaced by the mandated bare-anchor-free residual sweep and fixed under the brief's "fix it if it's in these 3 files" clause.
- **Deviations:** fixed 2 sites, not 1 — the 2nd (`:123-128`, the `member_of` KNOWN_RELATION_EDGES annotation) was present-tense-false (*"makes … RED until the builder emits it"*) and in my writable file; fixed per brief authority. Both readings recorded in §DECISION.
- **Capability check:** brief fully satisfiable with the tools I had (Read/Edit/Bash + lore + ruff + pytest against the live spike-surreal test store). No gaps.
- Packages considered: none — no mechanism specified (comment-only edits).
- Reuse ledger: none — no new symbols.
- **Graded:** N/A — this is a fix report, not a verdict on another artifact. Base HEAD at edit: `b9e6335` (uncommitted wave-1 tree on `feat/surreal-unification`).
- Decisions-needed: none — both stale sites fixed in-file within granted scope.
- Receipt pointers: ground-truth §GROUND-TRUTH; before→after §FIXES; full sweep table §RESIDUAL-SWEEP; gate tails §VERIFY.

## GROUND-TRUTH (why the comments were false)
Confirmed on the ACTUAL on-disk uncommitted tree (not just the index), via `sed` over `surreal_schema.py` ~2030-2112:
- `generate_keep_ddl()` returns `";\n".join(_keep_statements() + _member_of_statements()) + ";\n"` — real DDL, NOT `""`.
- `_member_of_statements()` emits `_define_relation_table(MEMBER_OF_RELATION, PRINCIPAL_TABLE, KEEP_TABLE, enforced=True)` → a real `member_of TYPE RELATION IN principal OUT keep ENFORCED` table, plus its fields + UNIQUE(in, out) index. NOT `[]`.
- `_keep_statements()` emits the `keep` table + fields + keeper index. NOT `[]`.
- Therefore `test_the_relation_edge_set_is_EXACTLY_the_six_known_edges` is GREEN (68 passed, §VERIFY), NOT "RED until the builder emits it".

So the two claims fixed below — (1) *"`generate_keep_ddl` STUBS to `""` … emits no relation table yet"* and (2) *"makes …six_known_edges RED until the builder emits it"* — are both present-tense FALSE.

## FIXES (before → after)

### FIX 1 — `_enforced_relations_scaffold.py:92-95` (the brief's named site, dropped by fixer-60-prose)
BEFORE:
```
    # here so the ∀ ENFORCED / OVERWRITE / IN-OUT pins sweep ``member_of`` the moment
    # the builder emits it. ⚠ RED-by-design until then: ``generate_keep_ddl`` STUBS to
    # ``""`` (contract-60-w1), so it emits no relation table yet.
```
AFTER (the edit fixer-60-prose derived, verbatim from the brief):
```
    # here so the ∀ ENFORCED / OVERWRITE / IN-OUT pins sweep ``member_of``.
    # ``generate_keep_ddl`` emits the real slice (contract-60-w1, greened wave-1),
    # including the ``member_of`` RELATION table.
```

### FIX 2 — `_enforced_relations_scaffold.py:123-128` (SECOND stale site, found by the defensive sweep)
The `member_of` annotation on `KNOWN_RELATION_EDGES` was written at contract-time (2026-08-22, before emission) in PRESENT tense and never updated when the wave-1 builder greened it. The `blocks` precedent immediately above (lines 116-121) is the repo's established idiom for this exact comment class once the edge lands: PAST-tensed main verb + a current-state note (*"what **made** … RED until the builder **landed** it … the pin now reads `_six_known_edges`"*). I mirrored it, past-tensing ONLY the transient factual claim and leaving the timeless design-purpose sentence (*"That reddening IS the deliberate declaration …"*) as-is, exactly like the `blocks` block.

BEFORE:
```
#: BEFORE the edge exists, exactly like ``blocks`` before it — which is what makes
#: ``test_the_relation_edge_set_is_EXACTLY_the_six_known_edges`` RED until the builder
#: emits it in ``surreal_schema::_member_of_statements``. That reddening IS the
```
AFTER:
```
#: BEFORE the edge existed, exactly like ``blocks`` before it — which is what made
#: ``test_the_relation_edge_set_is_EXACTLY_the_six_known_edges`` RED until the wave-1
#: builder emitted it in ``surreal_schema::_member_of_statements``. That reddening IS the
```
(word-level: `exists`→`existed`; `makes`→`made`; `the builder emits it`→`the wave-1 builder emitted it`.)

## DECISION — was FIX 2 in scope, and is it genuinely stale? (ambiguity recorded per brief-base §2)
Two readings of `:123-128` that would produce different action:
- **Reading A (stale → fix):** the present-tense *"makes …six_known_edges RED until the builder emits it in `surreal_schema::_member_of_statements`"* tells a header-less-chunk reader (the LLM consumer, per the consumer law) that the builder has NOT emitted `member_of` and the pin is currently red. That is FALSE now.
- **Reading B (generic mechanism → leave):** read as timeless narration of why adding an edge name reddens the exact-set pin.

**I picked A** because (1) ground truth: the edge IS emitted and the pin IS green; (2) the `blocks` block directly above uses PAST tense for the identical construct and explicitly marks the current state, establishing the in-file convention that this comment is reframed once the edge lands; (3) rename-sweep law: a present-tense claim in a durable comment is read as current by a retriever that cannot see it is dated. It is in a writable file, so per the brief ("fix it if it's in these 3 files") I fixed rather than flagged.

## RESIDUAL-SWEEP (every hit, individual verdict — "all remaining hits are X" is banned)
Bare, anchor-free greps across the 3 wave-1 files: the brief's pattern list (`STUB`, `emit []`, `emits []`, `emits no`, `emits NOTHING`, `RED-by-design`, `RED STUB`, `NotImplementedError`, `Do NOT "fix"`, `Do NOT implement`) PLUS a defensive pass (`\bRED\b`, `until the`, `before the edge`, `emits ""`, `not yet`, `the moment`, `no relation table`, `does not exist`, `stub`) — because the brief's list keys on `RED STUB`/`RED-by-design` and would MISS a bare-`RED` present-tense claim (which is exactly how FIX 2 hid).

Pattern-list hits with NO matches: `emit []`, `emits []`, `emits no`, `emits NOTHING`, `RED-by-design`, `Do NOT "fix"`, `Do NOT implement`, `emits ""` — the stub-era phrasings are all gone.

| file:line | matched | verdict | why |
|---|---|---|---|
| keeps.py:3 | STUB / stub | historical-origin-note-OK | *"Introduced as the STUB half … — and GREENED by the wave-1 builder. Every CRUD verb below is now fully implemented"* — past origin + present greened. |
| keeps.py:6 | NotImplementedError | historical-origin-note-OK | Same sentence: *"with every CRUD verb raising NotImplementedError — and GREENED"* — describes the retired stub state. |
| keeps.py:203 | not yet | unrelated-accurate | `self._connection = None` lifecycle comment (*"None means 'not yet connected / closed'"*) — nothing to do with the slice. |
| surreal_schema.py:135 | RED stubs / stub | historical-origin-note-OK | pkt49: *"(introduced as RED stubs by contract-49-1 …) are now fully built and folded into generate_ddl."* |
| surreal_schema.py:1837 | the moment | unrelated-accurate | pkt48 design rationale (*"creates the table the moment packet 48 ships"*) — not an emptiness claim. |
| surreal_schema.py:1855 | RED STUBS | historical-origin-note-OK | pkt49: *"Introduced as RED STUBS … — and GREENED … The slice now built:"* |
| surreal_schema.py:1957 | RED STUBS | historical-origin-note-OK | pkt60: *"Introduced as RED STUBS by contract-60-w1 … — and GREENED … The two assemblers + generate_keep_ddl now emit the real slice, folded into generate_ddl."* |
| surreal_schema.py:2108 | the moment | accurate | pkt60 fold design-rationale (*"creates the tables the moment packet 60 ships"*) — describes WHY keep/member_of fold into generate_ddl, not that they are empty. |
| surreal_schema.py:2255 | RED | accurate | pkt11ia corpse-sweep pin design (*"a comment naming the corpse makes that pin RED"*) — describes a live pin's mechanism; fixer-60-prose independently confirmed not-stale. |
| _enforced_relations_scaffold.py:99-109 | does not exist / (RED-adjacent) | accurate | pkt04b-1: *"does not export a BLOCKS_RELATION constant yet … The day the constant exists, this literal may be replaced by the import."* VERIFIED: imports (lines 47-72) carry `MEMBER_OF_RELATION` but NOT `BLOCKS_RELATION`; `BLOCKS_RELATION_NAME = "blocks"` is still a literal (line 110). The constant genuinely does not exist → claim true. |
| _enforced_relations_scaffold.py:103 | RED | accurate | *"UNCOLLECTABLE rather than RED (finding #133 …)"* — design-rationale contrasting two states; timeless. |
| _enforced_relations_scaffold.py:116-121 | RED / before the edge / until the | accurate | pkt04b-1 `blocks` block: *"was ADDED … BEFORE the edge exists, which is what **made** … RED until the builder **landed** it (`member_of`, packet 60, is the latest such addition — the pin now reads `_six_known_edges`)."* PAST-tensed main verb + explicit current-state marker → correct. Out of pkt60 scope AND not stale; left untouched. |
| _enforced_relations_scaffold.py:121,128 | RED | accurate | Section-title reference (*"WHAT THIS CONTRACT TURNS RED IN FILES IT DOES NOT OWN"*) — a real §heading, timeless. |
| _enforced_relations_scaffold.py:123-128 | RED / before the edge / until the | **stale → FIXED (FIX 2)** | Present-tense *"makes … RED until the builder emits it"* — false now; reframed to past tense matching the `blocks` idiom. |
| _enforced_relations_scaffold.py:252 | does not exist | accurate | `ghost_id` docstring (*"an identity that genuinely does not exist"*) — describes a deliberately-absent test id; correct. |

**Confirmed:** ZERO present-tense claims that a greened function/emitter is empty/unimplemented remain in the 3 files.
(The case-insensitive `red` probe also matched dozens of substring artifacts — `sha**red**`, `requi**red**`, `c**red**entials`, `**red**uced`, `**reg**iste**red** ⟶ registe**red**` — all in `keeps.py`/`surreal_schema.py`; none is a word-boundary `RED`. Re-run with `\bRED\b` (case-sensitive) yields exactly the 9 genuine candidates enumerated above.)

## VERIFY (receipts)
- **ruff** `loremaster/tests/_enforced_relations_scaffold.py` → `All checks passed!` (exit 0).
- **pytest -n auto** `loremaster/tests/test_enforced_relations.py` → `68 passed in 5.91s` (64 workers, 68 items, live spike-surreal test store `ws://127.0.0.1:18000`). Collection intact.
- **git status --short** → the only file I EDITED is `loremaster/tests/_enforced_relations_scaffold.py` (already `M` from wave-1 before I touched it, per fixer-60-prose). The other `M`/`??` entries are pre-existing wave-1 work I did not touch. My report `REPORT-fixer-60-scaffold.md` is my only other write.
- I did NOT commit (per brief; lead commits).
