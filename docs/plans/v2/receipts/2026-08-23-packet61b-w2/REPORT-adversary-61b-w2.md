# REPORT-adversary-61b-w2 — contract adversary, packet 61b-w2 (visible-Keeps resolver + coverage-as-checked-variable)

brief-base v14 read · brief project v7 read

## RE-GRADE (2026-08-23, delta only — verdict now SUFFICIENT)
The author landed all 3 findings (A bare-id pin, B whole-method born-wrap incl. resolution, C growth-pin
anti-vacuity); the contract is now **28 pins** (was 26). The lead ruled B **in scope, resolution-too**.
Re-graded ONLY the delta against my independent reference (whole-method wrap); the 12 prior wrong-builds
stand. Receipts §Re-grade. **NEW VERDICT: CONTRACT SUFFICIENT.** The original INSUFFICIENT verdict below
is SUPERSEDED and kept for the reasoning trail.

## SUMMARY BLOCK (re-grade)
- **VERDICT: CONTRACT SUFFICIENT.** Satisfiability **28/28** on my independent reference (whole-method
  born-wrap; `loremaster.__file__` inside scratch). All 3 delta pins DISCRIMINATE their wrong build:
  (A) a `keep:xyz`-prefixed return reds `test_returns_BARE_keep_ids_not_record_id_strings`; (B) a
  SELECT-only-wrap (resolution outside) reds `test_born_wrapped_RESOLUTION_rejection_becomes_KeepStoreError`
  — no raw `SurrealStoreError` escapes from EITHER resolution or SELECT into the authz path; (C) a
  forced-empty registry reds the growth pin on `assert live_names` (was vacuous-green). Growth pin still
  reds a synthetic unclassified tool; default-governed holds; boundary clean (0 `authorize`/
  `authorize_filter` in the H-a test — no Fork H-c over-reach). §Re-grade.

---

## SUMMARY BLOCK (original — SUPERSEDED)
- **VERDICT: CONTRACT INSUFFICIENT (marginal — 2 cheap missing pins + 1 scope ruling).** The contract is STRONG: every behaviorally-wrong build I could construct is caught end-to-end, and the H-a growth-pin reach is genuinely a checked variable. The INSUFFICIENT is for two low-severity completeness gaps the author can close in ~3 lines + one born-wrap SCOPE question for the lead. No incorrect/insecure build ships through the full 26-pin set.
- **P1 headline — did any wrong build survive?** NO behaviorally-wrong build survived. I built **12 wrong implementations** (Fork F ×6, resolver ×2, H-a ×4) in a provenance-asserted scratch and ran the REAL contract; each was caught by the intended pin(s). Receipts §P1.
- **Satisfiability:** an INDEPENDENT reference build (not the author's) greens **26/26** declared nodes; `loremaster.__file__ = /var/tmp/scratch-adv-61bw2/loremaster/loremaster/__init__.py` (#140 closed). §Satisfiability.
- **MISSING PINS (both LOW-severity, author-writable):**
  - **A — Fork F return-form unpinned:** a build returning `keep:xyz` (str(RecordID)) instead of the RULED **bare** id passes all 10 `TestListKeepsForMember` pins (they all `_record_id_part()` first). Downstream-guarded by the resolver's double-prefix pin, so no bad authz ships at 61 — but the ruled unit contract ("bare keep ids") is unpinned, exposing a future direct consumer (pkt 62/63). Pin: assert returned ids are bare.
  - **C — growth-pin anti-vacuity:** `test_every_live_tool_is_reviewed_into_a_population` lacks `assert live_names` — vacuous-GREEN on an empty registry (reach-law P1c axis-3: "a scan that reaches zero sites is broken, not clean"). Caught today by two sibling pins, so no production build survives; still a reach-law deviation. Pin: add `assert live_names`.
- **FLAG B (born-wrap SCOPE — lead ruling):** the 3 D1 born-wrapped pins inject only at `keeps.run_query`, so they cover the `member_of` SELECT but NOT the composed `PrincipalStore.get_by_email` resolution read. **Empirically confirmed:** a raw `SurrealStoreError` from resolution ESCAPES `list_keeps_for_member` unwrapped into the authz path — the exact D1 rationale ("no raw engine error into authz"), via the resolution door. Ledgered #406 read-gap class, low reachability, fix is a PrincipalStore change out of w2 scope. Decision §Flag-B.
- **Quantifier table** §P1b · **Reach table** §P1c · every guarded row carries a receipt.
- **Boundary check (brief pt 5):** NO pin routes a governed verb through `authorize`/`authorize_filter`; H-c correctly deferred to 63. No 63-leak. §Boundary.
- **P0 self-control:** my first WB-H3 was a botched perturbation (`.replace(...,1)` hit a production `"lore_verify"` in the 10k-line server.py, not my allowlist) — it "survived" my broken detector but was actually caught by the ghost-entry pin; redone correctly, growth pin reds. Disclosed §P1/H-a.
- **Packages considered:** none — no mechanism specified (contract grades tests; reference impl REUSES `wrap_store_rejection`, `lorerunes.pdp.keep_scope`, mirrors `partition_tools_by_posture`).
- **Graded:** `1048138` · HEAD-at-report `1048138` · SAME. (Wave UNCOMMITTED; the 3 test files + the doc are the graded artifacts.)
- **decisions-needed:** (1) add pins A + C (recommended); (2) rule Flag B (born-wrap SELECT-only vs resolution too).

---

## Satisfiability (C-DEF) — an INDEPENDENT reference greens all 26
I built my own reference (NOT the author's scratch) in `./scripts/scratch_copy.sh /var/tmp/scratch-adv-61bw2`:
- `KeepStore.list_keeps_for_member` (born-wrapped, plain-table leading-column read — body pasted §Instruments)
- `loremaster/loremaster/visible_keeps.py::resolve_visible_keeps` (REUSES `keep_scope`)
- `loremaster.server.{_SHARED_READ_CORPUS_TOOLS(9), _REVIEWED_GOVERNED_TOOLS(6), partition_tools_by_population}` (default-governed)

```
PROVENANCE loremaster.__file__ = /var/tmp/scratch-adv-61bw2/loremaster/loremaster/__init__.py
26 passed in 7.09s
```
So the EXPLAIN pin's operator strings ("IndexScan" for `WHERE in=$p`, "TableScan" for `WHERE out=$k`) are CORRECT on the live 3.2.4 store — the pin greened, which independently validates finding #413 / store-ref §2 on the `member_of` edge (I did not rely on the author's word). Live registry = **15 tools** (9 corpus + 6 coordination), enumerated store-free via `_build_tools`.

## RED honesty (P7)
The 26 nodes are RED at HEAD because the production symbols are genuinely absent (verified by reading: `keeps.py` ends at `list_keeps_for_keeper` line 848; no `visible_keeps.py`; `server.py` has no `partition_tools_by_population`) — `AttributeError` / `ModuleNotFoundError` / `ImportError`, not typos. The reference build had to CREATE each symbol to green them → RED-for-the-right-reason confirmed.

## P1 — wrong builds (all caught by the intended pin)
Scratch driver restores the correct reference between variants; each row ran the REAL contract tests.

| # | Wrong build | Caught by (RED) |
|---|---|---|
| WB-F1 | `list_keeps_for_member` reads **keeper direction** (`keep WHERE keeper=$p`) | `test_returns_every_keep_whose_household_the_member_is_in` (+seam+EXPLAIN) |
| WB-F2 | **arrow traversal** (`$member->member_of->keep`) | `test_routes_through_the_shared__query_seam…` (`->` present) |
| WB-F3 | **trailing column** (`WHERE out=$member`) | `test_the_methods_member_of_read_IndexScans…` (TableScan) |
| WB-F4 | **unwrapped** (mirror clone — no wrap) | `test_born_wrapped_engine_rejection_becomes_KeepStoreError` |
| WB-F5 | **catch-all** wrap (no transport pass-through) | `test_born_wrapped_propagates_transport_faults_untouched[connection]`+`[contention]` |
| WB-F6 | unknown email → `[]` (swallow) | `test_an_unknown_member_email_raises_KeepStoreError` |
| WB-R1 | resolver **hand-rolls `f"keep:{k}"`** | `test_mutating_the_shared_prefix_moves_the_resolver_output` |
| WB-R2 | resolver **double-prefixes** (`keep_scope(f"keep:{k}")`) | `test_every_scope_is_a_valid_non_double_prefixed_keep_scope` (+2) |
| WB-H1 | **fail-open** (default → shared_read) | `test_an_unknown_tool_is_governed_by_default…` + `…defaults_governed` |
| WB-H2 | everything **governed** (∅, all) | `test_the_corpus_reads_are_shared_read` |
| WB-H4 | everything **shared_read** (whole-surface exemption) | `…coordination_tools_are_governed` + `…does_not_exempt_the_whole_surface` (+2) |
| WB-H3 | **reach**: drop `lore_verify` from allowlist (live but unreviewed) | `test_every_live_tool_is_reviewed_into_a_population` (GROWTH PIN) |

**P1c reach — empirical:** WB-H3 is the load-bearing reach proof. Removing `lore_verify` from ONLY the appended `_SHARED_READ_CORPUS_TOOLS` (leaving it live) reds the growth pin → the growth pin's reach is DERIVED from the live registry and is a CHECKED VARIABLE, not a hidden constant. The reverse drift (a tool removed from the live registry but left in a reviewed set) is caught by `test_neither_reviewed_set_has_ghost_entries` — proven accidentally when my first WB-H3 hit a production `"lore_verify"` and the ghost pin fired.

## P1b — QUANTIFIER TABLE
| Invariant | ∀-over-inputs / guarded | Receipt |
|---|---|---|
| Fork F: returns all member's keeps | ∀ (subset, ≥2 small-N) | WB-F1 reds |
| Fork F: excludes non-member keeps / no cross-member bleed | ∀ (discrimination + positive control) | reference greens; keeper-build reds |
| Fork F: unknown email → KeepStoreError | guarded(unresolvable email) | WB-F6 reds |
| Fork F: plain-table leading `in`, no arrow (seam capture) | ∀ over the issued statement | WB-F2 reds |
| Fork F: EXPLAIN IndexScan + trailing-TableScan control | structural, non-vacuous (control sees a TableScan) | WB-F3 reds |
| Fork F: born-wrap SELECT rejection → KeepStoreError | guarded(SurrealStoreError **from the SELECT seam only**) | WB-F4 reds; **Flag B: NOT ∀ over the method's engine rejections — resolution read leaks** |
| Fork F: transport faults pass through | discriminator(conn/contention) | WB-F5 reds both params |
| Resolver: frozenset of single-prefixed keep:<id> | ∀ | WB-R2 reds |
| Resolver: routes through shared keep_scope | ∀ (prove-by-mutation of KEEP_SCOPE_PREFIX) | WB-R1 reds |
| Resolver: member-of-none → frozenset() / unknown → KeepStoreError | guarded(specific inputs) | reference greens |
| Resolver: end-to-end authz (in allowed, out denied, server allowed) | ∀ (both fates + positive control) | reference greens; over/under-broad resolver reds |
| H-a: totality union==live ∧ disjoint | ∀ over live registry (anti-vacuity `assert live_names`) | overlap/partial build reds |
| H-a: default = governed | ∀ over unreviewed tools | WB-H1 reds |
| H-a: growth pin — every live tool reviewed | ∀ over live registry (reach-checked) | WB-H3 reds — **Finding C: no own anti-vacuity (empty→vacuous-green), sibling-covered** |
| H-a: corpus→shared_read / coordination→governed | representative discrimination (different values per bucket) | WB-H2 / WB-H4 red |
| H-a: allowlist ≠ whole surface / no ghosts / disjoint / one-home | ∀ / structural | WB-H4 reds; ghost pin reds on drift |

Only ONE row is "guarded" in a way that leaves a hole: the born-wrap (Flag B). Every other guarded row's failure mode is either the exact intended input or is discriminated.

## P1c — REACH TABLE (per instrument)
| Instrument | Reach DERIVED? | Coverage a checked variable? | Effect vs proxy | One-source / mutation | Verdict |
|---|---|---|---|---|---|
| `partition_tools_by_population` (runtime) | YES — `governed = live(tools) − allowlist`, over the passed `tools` | YES — synth tool grows live & defaults governed (WB-H1) | effect (real `list_tools()`) | references ONLY `_SHARED_READ_CORPUS_TOOLS` at runtime; `_REVIEWED_GOVERNED_TOOLS` is review-only (can't be fail-open) | SAFE |
| growth pin `test_every_live_tool_is_reviewed…` | YES — `_build_tools`→`build_mcp_server` live surface | YES empirically (WB-H3 reds) — **but no fail-closed-on-empty (Finding C)** | effect | reviewed = 2 hand-lists, self-correcting via this pin (design D2 acknowledges) | MOSTLY SAFE (add anti-vacuity) |
| ghost-entry pin | YES — `reviewed − live` | YES (removed-but-in-set reds) | effect | — | SAFE |
| totality pin | YES — live surface | anti-vacuity present | effect | — | SAFE |
| `_derive_keepstore_write_paths` (RELIED-ON, existing) | YES — AST of keeps.py (public async def w/ mutating literal) | YES — `_WRITE_PATHS == coverage map`; read verbs excluded (positive control) | effect | `list_keeps_for_member` correctly EXCLUDED — pin still passes with the new read (verified) | SAFE |

Legs run: EMPIRICAL for every INTRODUCED guard (built the wrong version in scratch, watched the pin red); construction-inspection corroborated by the reference greening. The one instrument the contract only RELIES on (`_derive_keepstore_write_paths`) I re-ran against the new method — still green, no misclassification.

## Boundary (brief pt 5)
`test_tool_population_61b.py` only CLASSIFIES (`partition_tools_by_population -> (shared_read, governed)`); no pin calls `authorize`/`authorize_filter` on any verb. Fork H-c (per-governed-verb routing) is correctly DEFERRED to 63 with a named trigger. No over-reach of 63 into 61. ✓

## Fixture discrimination (P2)
- `_REPRESENTATIVE_SHARED_READ`/`_GOVERNED` use DIFFERENT values per bucket (lore_search/get_symbol vs lore_comms/findings) → an "everything one way" build reds the OTHER bucket (WB-H2/H4 both confirmed).
- Fork F results pins use ≥2 keeps (small-N discrimination) — a single-keep build reds `test_returns…`.
- **Non-discriminating fixture found (Finding A):** the 10 Fork F pins cannot tell a bare-return build from a prefixed-return build — both pass (empirically: prefixed build → `10 passed`). The resolver's double-prefix pin discriminates end-to-end (`3 failed` with the naive resolver), so behavior is guarded; the UNIT contract is not.

## Flag B — born-wrap SCOPE (needs a lead ruling)
`_resolve_principal_id → PrincipalStore.get_by_email` runs `SELECT … FROM principal WHERE email=$email` via `self._query` and does NOT wrap (confirmed by reading `principals.py:487`). In the reference (and any faithful build), `_resolve_principal_id` is OUTSIDE the born-wrap block, so:
```
RESULT: RAW SurrealStoreError ESCAPED into caller (born-wrap does NOT cover resolution read) -- Finding B CONFIRMED
```
(probe injected `SurrealStoreError` at `principals.run_query`, left `keeps.run_query` intact.) The 3 D1 pins inject at `keeps.run_query` only, so they structurally cannot see this. This is the ledgered **#406 read-gap** (get_by_email/list_keeps_for_keeper/get_keep/list_household all leak) — consistent with the whole store, low reachability (a plain SELECT rarely raises a domain `SurrealStoreError`; transport/contention handled by the retry driver). **Ruling needed:** is D1's "no raw engine error into authz" meant to cover resolution?
- If YES → `get_by_email` must wrap (a PrincipalStore change, OUT of w2's writable set) + a born-wrap pin injecting at the `principals`-module seam. Recommend routing to the #406 consumer-law-hardening wave, not w2.
- If NO → the contract/ruling should STATE the born-wrap is SELECT-scoped and the resolution leak is the ledgered #406 gap, so a future reader doesn't over-trust `list_keeps_for_member` as fully born-wrapped.

## Missing pins (concrete, author-writable)
- **A** — in `TestListKeepsForMember`, add to (e.g.) `test_returns_every_keep_whose_household_the_member_is_in`:
  `assert all(KeepStore._record_id_part(kid) == kid for kid in keep_ids), "list_keeps_for_member must return BARE ids (design Fork F), not str(RecordID)"`. **Catches:** a `keep:xyz`-returning build (ruled "bare"), which a future direct consumer (62/63) mishandles.
- **C** — in `test_every_live_tool_is_reviewed_into_a_population`, add `assert live_names, "the live registry is empty — the growth pin is vacuous"` (mirrors the totality pin's guard). **Catches:** a broken `_build_tools`/registry returning empty reading GREEN (reach-law fail-closed-on-empty).

## Corpse sweep (P6)
The contract adds `list_keeps_for_member` to the EXISTING `_KEEPSTORE_READ_METHODS` and to nothing in `_WRITE_PATHS` (it is SELECT-only; the AST mutating-literal scan excludes it). Verified: `test_the_derived_write_path_set_matches_the_coverage_map` still `1 passed` with the new method present — no drift, no corpse. No other retired-behaviour assertion touched.

## Instruments (pasted for reproducibility — /var/tmp is not durable)
Reference `list_keeps_for_member` (appended to `KeepStore`):
```python
async def list_keeps_for_member(self, *, member_email: str) -> list[str]:
    member_id = await self._resolve_principal_id(member_email)
    with wrap_store_rejection(KeepStoreError, f"list keeps for member {member_email!r}"):
        rows = PrincipalStore._as_rows(
            await self._query(
                f"SELECT out FROM {MEMBER_OF_RELATION} WHERE in = $member",
                {"member": RecordID(PRINCIPAL_TABLE, member_id)},
            )
        )
    return [self._record_id_part(str(row["out"])) for row in rows]
```
Reference `resolve_visible_keeps`:
```python
async def resolve_visible_keeps(keep_store, *, member_email) -> frozenset[str]:
    keep_ids = await keep_store.list_keeps_for_member(member_email=member_email)
    return frozenset(keep_scope(keep_id) for keep_id in keep_ids)
```
Reference registry: `partition_tools_by_population(tools)` → `shared_read = {t.name for t in tools if t.name in _SHARED_READ_CORPUS_TOOLS}`, `governed = the rest` (default-governed). `_SHARED_READ_CORPUS_TOOLS` = the 9 corpus reads; `_REVIEWED_GOVERNED_TOOLS` = the 6 coordination tools (review marker only).
Flag-B probe: inject `SurrealStoreError` at `loremaster.principals.run_query`, leave `keeps.run_query` intact, call `list_keeps_for_member` for a seeded email → raw error escapes (§Flag-B output).
Wrong-build driver, per-variant bodies, and the Flag-B probe are the ones pasted above; each variant restores the reference between runs and asserts the target node is in the FAILED set.

## Re-grade — receipts (delta only)
Independent reference updated to WHOLE-METHOD born-wrap (`with wrap_store_rejection(...): member_id = await self._resolve_principal_id(...); rows = ... SELECT ...`); contract test files refreshed from HEAD `1048138`.
```
PROVENANCE /var/tmp/scratch-adv-61bw2/loremaster/loremaster/__init__.py
28 passed in 6.42s          # full delta set (TestListKeepsForMember 12 + resolver 6 + H-a 10)
```
Delta wrong-builds (each reds the intended pin):
| Delta | Wrong build | Pin that REDS |
|---|---|---|
| A | `list_keeps_for_member` returns `str(row["out"])` (`keep:xyz`) | `test_returns_BARE_keep_ids_not_record_id_strings` (`1 failed`) |
| B | SELECT-only wrap (resolution OUTSIDE the wrap) | `test_born_wrapped_RESOLUTION_rejection_becomes_KeepStoreError` (`1 failed`) |
| C | `_live_tool_names` → `frozenset()` (broken registry enumeration) | growth pin `assert live_names` → `AssertionError: the live tool registry is EMPTY …` |

Confirmed unchanged: growth pin still reds a synthetic unclassified tool + default-governed holds (`3 passed` on reference; both directions proven by the standing WB-H1/WB-H3). Boundary: `grep -c "authorize\b\|authorize_filter" test_tool_population_61b.py` → **0** (no Fork H-c verb-routing over-reach). B's whole-method wrap does not regress the unknown-email pin (`_resolve_principal_id` raises `KeepStoreError`, which `wrap_store_rejection` — catch=`SurrealStoreError` only — passes through untouched; verified in the 28/28).

## VERDICT
**CONTRACT SUFFICIENT** (re-grade, 2026-08-23). All 3 findings landed and each new pin discriminates its wrong build; satisfiability 28/28 on an independent whole-method-wrap reference; the H-a reach is a genuinely checked variable (growth-pin reds a live-unreviewed tool, now non-vacuous); no Fork H-c over-reach. Builder may be released.

---
### (superseded) original verdict
**CONTRACT INSUFFICIENT** — a strong contract with 2 cheap, concrete missing pins (A bare-return; C growth-pin anti-vacuity) and 1 scope ruling (B born-wrap resolution read). Every behaviorally-wrong build I constructed is caught; the H-a reach is genuinely a checked variable; satisfiability is 26/26 on an independent build. Close A+C and rule B and the contract is airtight. The severity is LOW throughout — no incorrect or insecure build ships through the full 26-pin set today.
