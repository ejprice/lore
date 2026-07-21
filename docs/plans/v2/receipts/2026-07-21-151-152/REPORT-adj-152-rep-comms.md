# REPORT-adj-152-rep-comms — citation adjudication, comms + ledger test files

brief-base v5 read

- **state:** done
- **deviations:** none to scope; I EDITED NOTHING (read-only, as briefed).
- **decisions-needed:**
  1. **DEFECT (loud): the RED-expectation prose in 2 files is STALE** — `test_comms_render_architecture.py:12-45` and `test_brief_ledger.py:1484-1492` declare themselves RED against clean production, but `subscribed_name_skew` / `auto_ack_at_register` / `_HEARTBEAT_SKEW_NAMES_CAP` all SHIPPED. §D1.
  2. **DEFECT: 5 measured numbers whose instrument is gone** (30/30, 40/40, 234 ms, 6.1×, 617/0). §D2. Recommend STRIKE, per the `_txn.py` 30.2% precedent.
  3. `test_task_ledger.py:1529` promises error texts are "asserted VERBATIM against" a `scratchpad/` design doc that does not exist — recover it or strike the sentence. §D3.
  4. ESCALATION: `report_path` fixtures (`task_ledger:1984/2057`) canonicalise the repo-root `REPORT-*.md` form — the data-model root of #152. §E1.
- **receipt pointers:** §A counts · §B per-site table (52 `.md` sites) · §C extension population (28 sites) · §D defects · §E escalations

---

## A. Derived counts — re-derived, not inherited

Sweep (bare, anchor-free, per repo law):

```
git grep -nE 'REPORT-[A-Za-z0-9._-]+\.md' -- 'loremaster/tests/test_comms_*.py' 'loremaster/tests/*ledger*.py'
```

| population | count |
|---|---|
| `.md`-literal sites, single-line grep (the brief's pattern) | **50** |
| `.md`-literal sites, **line-wrapped** — invisible to that grep | **+2** |
| **`.md`-literal TOTAL** | **52** |
| Extension population (report-shaped, no `.md`) | **28** |
| **TOTAL ADJUDICATED** | **80** |

Per file (`.md` literal): `test_comms_tool.py` 19 · `test_brief_ledger.py` 8 · `test_comms_schema.py` 5 · `test_task_ledger.py` 5 · `test_message_ledger.py` 4 · `test_comms_promise_registry.py` 4 · `test_comms_render_architecture.py` 4 · `test_comms_wiring.py` 2 · `test_comms_fleet_grouping.py` 1 · **`test_memory_ledger.py` 0** (clean — verified, exit 1 on `git grep -c REPORT`).

⚠ **GREP-BLINDNESS FINDING — the brief's own pattern misses 2 of 19 sites in the largest file.**
`test_comms_tool.py:2926` and `:3540` cite `REPORT-c1c-contract-adversary-96.md` **wrapped across a
line break** (`REPORT-c1c-contract-` / `adversary-96.md`). A single-line regex cannot see them. This
is the *anchored-pattern* lesson in a new coat: the anchor here is the LINE, not a prefix. **Any
future sweep of this class must run a second, line-joined pass.** I found these only via the
vocabulary sweep (`adversary`), which is how the brief predicted extension sites would surface.

### Resolvable / dangling split (derived)

53 distinct report names are cited across `loremaster/tests/*.py`; 13 `REPORT-*.md` are tracked.
**In MY scope, 5 `.md` sites + 2 extension sites resolve** — all packet-03, all under
`docs/plans/v2/receipts/2026-07-19-packet03/`. I verified each **section** cited actually exists:

| site | cites | tracked at | section verified |
|---|---|---|---|
| `test_comms_tool.py:3907` | `REPORT-contract-pkt03.md §UPDATE 5eb445b` | `docs/plans/v2/receipts/2026-07-19-packet03/` | ✅ line 361 |
| `test_comms_schema.py:1594` | `REPORT-probe-pkt03-store.md` probes 2/3/5 | same | ✅ file present |
| `test_comms_schema.py:1969` | `REPORT-audit-edge-preflight.md` | same | ✅ file present |
| `test_comms_schema.py:2273` | `REPORT-audit-edge-preflight.md §Q5` | same | ✅ line 177 |
| `test_message_ledger.py:21` | `REPORT-probe-pkt03-store.md §"CONSEQUENCES FOR THE BUILD"` | same | ✅ line 421 |
| `test_message_ledger.py:188` | `REPORT-recon-pkt03 §F.4` *(no `.md`)* | same | ✅ line 453 |
| `test_message_ledger.py:1375` | `REPORT-recon-pkt03 §F.4` *(no `.md`)* | same | ✅ line 453 |

**This is the happy category the brief predicted, and it is the model.** The packet-03 wave archived
its receipts *before* the reports were deleted; every one of its citations still resolves,
section-exactly. The 03 convention is the fix for the other 54 names, applied prospectively.

### Verdict tally

| | count |
|---|---|
| TRACKED — resolve today, leave alone | 7 |
| **NOT A CITATION** — fixture data, grep false positive | 5 |
| Dangling · **PROVENANCE** → LEAVE IT | 63 |
| Dangling · **LOAD-BEARING** → REPOINT | **5** |

**5 repoints / 68 dangling = 7.4% — i.e. 92.6% leave-it**, above the 87.5% precedent. This is an
adjudication, not a bulk rewrite wearing one.

---

## B. Per-site verdicts — `.md`-literal population (52)

Every site gets its own line. No collapsing, no ditto.

### `test_comms_tool.py` (19)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| 5 | `REPORT-c1-contract-surface.md` | DANGLING | PROVENANCE | The STOP-and-flag rule is stated in full; the report is a second pointer beside "this module's own flags below". |
| 13 | `REPORT-c1-contract-surface.md` | DANGLING | PROVENANCE | "three of the four need no edit" is a closed historical statement about authoring time; nothing a reader must check today. |
| 27 | `REPORT-c1-contract-surface.md` "for the RED tail" | DANGLING | PROVENANCE | The RED expectation is spelled out completely in the preceding sentence (ImportError naming the module, not a fixture typo). The tail is a receipt, not the rule. |
| 187 | `REPORT-c1-contract-ledgers.md`'s "Exact public API surface" | DANGLING | PROVENANCE | Substance inline (plain-`str` pydantic, no charset validators) plus a verbatim spec §10 quote — a durable address already present. |
| 256 | `REPORT-c1-contract-surface.md`'s "contract decisions" | DANGLING | PROVENANCE | The testing-strategy decision and its full rationale are inline; only the out-of-scope flag lives in the report, and it is settled. |
| 318 | `REPORT-c1c-contract-adversary-96.md §P1` | DANGLING | PROVENANCE | The `len` ≡ `sum` small-N mechanism is stated completely inline. |
| 704 | `REPORT-c1-contract-ledgers.md` decision #4 | DANGLING | PROVENANCE | The decision's content is stated ("carries no roster … the SERVER enriches it"). |
| 707 | `REPORT-c1b-contract-9495.md` finding #95 | DANGLING | PROVENANCE | Finding **#95** is itself a durable address and the label rationale is inline. |
| 758 | `REPORT-c1-audit-adversary.md` P2 #2 | DANGLING | PROVENANCE | Mechanism inline (session filter, cross-session leak). ⚠ carries "643 tests green" — see §D2(f), low. |
| 841 | `REPORT-c1-audit-fixwave.md` v4 F1 BLOCKER | DANGLING | PROVENANCE | Mechanism inline **and** the durable design-doc §5.3 v4 is already cited beside it. |
| 1523 | `REPORT-c1d-audit-979899.md §DEFECT` | DANGLING | PROVENANCE | The eighth §5.3 instance is described in full — the docstring is longer than the finding would be. |
| 1622 | `REPORT-c1e-contract-eighth.md` | DANGLING | PROVENANCE | The reason for the coherence-property framing ("survives any rewording") is in the same sentence. |
| 1984 | `REPORT-c1b-contract-9495.md` finding #94 | DANGLING | PROVENANCE | **#94** durable; regression-guard rationale inline. |
| 2053 | `REPORT-c1-audit-adversary.md §P2` | DANGLING | PROVENANCE | The "#94 would survive its own fix" story is told completely inline. |
| 2568 | `REPORT-c1-builder-d1d2.md`'s "disclosed deviation" | DANGLING | PROVENANCE | **Closest call in this file.** The operative constraint a future engineer must not break — *"no `len()`-derived fallback path may exist in production"* — is fully inline. The report adds only that it was a disclosed deviation. LEAVE. |
| 2871 | `REPORT-c1c-contract-adversary-96.md §P1/§MISSING PINS #1` | DANGLING | PROVENANCE | Mechanism inline, including why both cap-boundary fixtures were blind. |
| **2926** | `REPORT-c1c-contract-adversary-96.md §MISSING PINS #2` ⚠ line-wrapped | DANGLING | PROVENANCE | Mechanism inline; the DEVIATION at :2941 explains itself and cites durable design doc §0.3. |
| **3540** | `REPORT-c1c-contract-adversary-96.md §MISSING PINS #3` ⚠ line-wrapped | DANGLING | PROVENANCE | Mechanism inline (the `{session}` slot never rendered under the hostile battery). |
| 3907 | `REPORT-contract-pkt03.md §UPDATE 5eb445b` | **TRACKED** | LEAVE | Resolves; §verified. Genuinely load-bearing (the packet-03 vs 03a pytest selectors) **and it works**. Optional polish only: prefix the archive path. |

### `test_brief_ledger.py` (8)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| **9** | `REPORT-c1-contract-ledgers.md` — "*contract decisions … are recorded in* X — *this docstring does not re-transcribe it*" | DANGLING | **LOAD-BEARING** | See §B1 below — the sentence makes an explicit promise that the substance lives elsewhere, and elsewhere is gone. Two readings recorded. |
| 722 | `REPORT-c1-contract-d1d2-b.md` | DANGLING | PROVENANCE | The decision AND its whole reasoning chain (import cycle, riskier redesign, LOW defect) follow inline. |
| 984 | `REPORT-c1-audit-fixwave.md` F3 | DANGLING | PROVENANCE | Mechanism inline. The numbers here (107/417/1007) are **re-derivable — the `_query_count` instrument is in this very file.** Materially unlike §D2. |
| 1077 | `REPORT-c1b-contract-9495.md` finding #94 | DANGLING | PROVENANCE | **#94** durable; the pinned public API is transcribed inline. |
| 1217 | `REPORT-c1b-contract-9495.md` finding #94 | DANGLING | PROVENANCE (citation) | ⚠ carries "**234 ms** at limit=200" — a wall-clock number no in-tree instrument can reproduce. See §D2(c). |
| 1308 | `REPORT-c1-audit-adversary.md` P2 #4 | DANGLING | PROVENANCE | Substance inline (205 vs the 200 cap; why 205 is hardcoded not imported). |
| 1484 | `REPORT-pkt02-contract.md` "validated reference impl" | DANGLING | **PROVENANCE — but see §D1** | Do **not** repoint: the surrounding RED-expectation claim is STALE (`subscribed_name_skew` shipped at `briefs.py:1093`). Repointing would launder a false claim. |
| 1654 | `REPORT-pkt02-coldaudit.md §"Phase 2 probe #1"` | DANGLING | PROVENANCE | The invariant and its mechanism (direct record access vs `id IN $ids` TableScan) are stated in full. ⚠ "6.1× at 11× rows" — §D2(d). |

#### §B1 — `test_brief_ledger.py:9`, the one site that admits two readings

> Current: *"Where this file's contract decisions are genuinely open in the spec, they are recorded in
> ``REPORT-c1-contract-ledgers.md`` — the spec is executed verbatim everywhere it speaks; this
> docstring does not re-transcribe it."*

**Reading 1 (PROVENANCE).** Every decision that actually matters downstream *is* separately restated
with full substance at its use site — I verified all three: decision #4 at `test_comms_tool.py:704`,
decisions #5/#6 at `test_comms_wiring.py:266`, the d1d2-b decision at `test_brief_ledger.py:722`. So
the module-docstring pointer is redundant, and deleting the address changes nothing a reader needs.

**Reading 2 (LOAD-BEARING) — the one I would pick.** This sentence differs from every other site in
my scope: it *explicitly declines to state the substance* and names a file as its home. A reader is
not merely under-informed, they are **actively misdirected** to a file that does not exist, and the
clause "this docstring does not re-transcribe it" tells them not to look locally. That is the
`#107` shape in miniature — a pointer whose target is absent, where the prose asserts the target is
authoritative.

Proposed MINIMAL repoint (address only; surrounding prose untouched):

```
-are genuinely open in the spec, they are recorded in
-``REPORT-c1-contract-ledgers.md`` — the spec is executed verbatim everywhere
+are genuinely open in the spec, they are recorded at their USE SITES — decision
+#4 at ``test_comms_tool.py::test_unknown_agent_error_is_enriched_with_a_capped_
+non_retired_roster``, decisions #5/#6 at ``test_comms_wiring.py::
+TestSchemaIsActuallyAppliedNotJustConstructed`` — the spec is executed verbatim everywhere
 it speaks; this docstring does not re-transcribe it.
```

This is the only repoint I propose that is longer than a swapped token; I flag that explicitly. If
the operator prefers strict minimality, the alternative is to strike the address and leave *"they
are recorded at their use sites"* — losing the map but keeping the truth.

### `test_comms_schema.py` (5)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| **59** | `REPORT-probe-7061-c1.md` **"at the repo root"** | DANGLING | **LOAD-BEARING** | See §B2 — a SAFETY claim this file explicitly declines to re-prove, whose sole authority is an absent file, with a location clause that is now literally false. |
| 1532 | `REPORT-c1-audit-final.md` D3 | DANGLING | PROVENANCE | The gap is described exhaustively inline (subset-check green even with the declaration deleted; SCHEMALESS auto-create). |
| 1594 | `REPORT-probe-pkt03-store.md` probes 2/3/5 | **TRACKED** | LEAVE | Resolves. Note this comment block is the repo's best-practice exemplar: every store fact CITED to `docs/reference/…` §§, not re-derived. |
| 1969 | `REPORT-audit-edge-preflight.md` | **TRACKED** | LEAVE | Resolves. Carries the 101,479-row pre-flight audit — a load-bearing number with a live, tracked instrument. Correct by construction. |
| 2273 | `REPORT-audit-edge-preflight.md §Q5` | **TRACKED** | LEAVE | Resolves; §Q5 verified at line 177. |

#### §B2 — `test_comms_schema.py:59`, the cleanest repoint in the corpus

> Current: *"The UNIQUE(in, out)-on-a-RELATION-edge mechanism itself (cascade-delete-then-re-RELATE
> safety, SurrealDB bug #7061) was independently probed and verified SAFE on this same 3.1.5 floor
> in a PRIOR session — see ``REPORT-probe-7061-c1.md`` at the repo root."*

The file then says it does **not** re-run that cascade probe. So the safety of a shipped schema
mechanism rests entirely on a citation that (a) dangles and (b) asserts a repo-root location that
repo law guarantees is empty. That is load-bearing by any reading.

**The durable address already exists and this file's own sibling comment cites it** — at `:1594`:
*"§4 (UNIQUE-on-relation is legal and the #7061 cascade hazard is settled ABSENT)"*. One block of
this file points at a ghost for a fact the next block points at `docs/reference/`.

```
-SAFE on this same 3.1.5 floor in a PRIOR session — see
-``REPORT-probe-7061-c1.md`` at the repo root. This file's own
+SAFE on this same 3.1.5 floor in a PRIOR session — see
+``docs/reference/surrealdb-31-capabilities.md`` §4 (UNIQUE-on-relation is legal;
+the #7061 cascade hazard is settled ABSENT). This file's own
```

### `test_comms_promise_registry.py` (4)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| 50 | `REPORT-pkt02-contract.md §E` "original sizing split" | DANGLING | PROVENANCE | Pure historical sizing provenance; nothing about the guard's behaviour depends on it. |
| 516 | `REPORT-pkt02a-builder.md` "Design B2" | DANGLING | PROVENANCE | B2 is described in full inline (parallel `_PROMISE_PROOFS` map, `set(…) == set(…)` checked invariant, minimal blast radius). |
| 1915 | `REPORT-pkt02a-finalwave.md`'s attack table | DANGLING | PROVENANCE | The two shapes that broke the first attempt are **named inline and ARE the parametrised fixtures** — the code is the receipt. |
| **2232** | `REPORT-pkt02a-finalwave.md §F, ledgered as its own item` | DANGLING | **LOAD-BEARING** | See §B3 — this is a **NAMED RE-OPEN TRIGGER on a KNOWN BOUND**, the exact artifact repo law says must never be silently inheritable. |

#### §B3 — `test_comms_promise_registry.py:2232`, and I found the ledger row

Repo law: *"Every bound carries a NAMED RE-OPEN TRIGGER … A bound that is pinned is a bound the next
engineer meets DELIBERATELY."* This pin's trigger currently points at a deleted report **and** at an
unnamed "ledgered as its own item" — so the one artifact designed to be followed cannot be.

**I queried the ledger and the item exists:** `lore_findings action=query status=open` returns
**#143 — "Promise-proof markers: mechanize 'marker must not survive a SIBLING-BRANCH render of the
same helper'"** (area `test_comms_promise_registry`, by `lead-pkt02a`). That is a verbatim match for
the instrument shape this trigger describes. Repoint:

```
-proof "marker must not survive a SIBLING-BRANCH render of the SAME helper" check lands (the instrument shape proposed in
-REPORT-pkt02a-finalwave.md §F, ledgered as its own item), this bound is CLOSED —
+proof "marker must not survive a SIBLING-BRANCH render of the SAME helper" check lands (the instrument shape
+ledgered as finding #143), this bound is CLOSED —
```

Strictly minimal, and it upgrades the trigger from unfollowable to one-tool-call followable.

### `test_comms_render_architecture.py` (4)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| 12 | `REPORT-pkt02-contract.md §D` | DANGLING | PROVENANCE | Both durable addresses are **already inline** — `fixed-by-4c2efbf` (SHA) and `test_caplog_isolation.py` (in-tree). Model citation. |
| 40 | `REPORT-pkt02-contract.md` "RED-for-right-reason table + satisfiability receipts" | DANGLING | **PROVENANCE — but see §D1** | Do **not** repoint. The RED expectation this heads is STALE: `auto_ack_at_register` (5 hits) and `_HEARTBEAT_SKEW_NAMES_CAP` (4 hits) are in `server.py` today. Repointing would launder a false claim. |
| 495 | `REPORT-pkt02-adversary.md §"surviving wrong builds"` | DANGLING | PROVENANCE | Both wrong builds are named inline with their exact mutations. ⚠ "617/0" — §D2(e). |
| 660 | `REPORT-pkt02-contract.md §C` removed-behavior inventory | DANGLING | PROVENANCE | **The DUAL-law adjudication verdict and its reason are stated inline** — "DROPPED-DELIBERATELY, test-only affordance, no production caller". The law is satisfied *here*, not in the report. |

### `test_comms_wiring.py` (2)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| 266 | `REPORT-c1-contract-ledgers.md` decisions #5/#6 | DANGLING | PROVENANCE | Substance inline — "a value the LEDGER layer deliberately does not validate" is the whole content of #5/#6. |
| 501 | `REPORT-c1d-audit-979899.md §DEFECT` | DANGLING | PROVENANCE | Full mechanism inline, plus the monoculture analysis. Nothing to follow. |

### `test_comms_fleet_grouping.py` (1)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| 29 | `REPORT-c1-contract-fixwave.md` | DANGLING | PROVENANCE | The whole bound is inline: no spec literal exists · the grammar is a *proposal* · the operator may override. ⚠ Cosmetic: "THIS report's proposed contract" now names nothing — a reader can't tell whose proposal it was. Not worth a repoint; noted for the operator. |

### `test_message_ledger.py` (4)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| 21 | `REPORT-probe-pkt03-store.md §"CONSEQUENCES FOR THE BUILD"` | **TRACKED** | LEAVE | Resolves; §verified at line 421. |
| 179 | `BODY_SIGNAL = "wave 3 landed green; receipts in REPORT-fixer-b.md"` | — | **NOT A CITATION** | Fixture **body text**. A message payload, not an authority claim. Grep false positive. |
| 374 | `refs=["REPORT-fixer-b.md"]` | — | **NOT A CITATION** | Fixture **argument**. |
| 382 | `assert result.message.refs == ["REPORT-fixer-b.md"]` | — | **NOT A CITATION** | The assertion on the same fixture. |

### `test_task_ledger.py` (5)

| line | citation | status | verdict | why |
|---|---|---|---|---|
| 1204 | `REPORT-fix-audit.md findings #1/#2` | DANGLING | PROVENANCE | Both edges named inline (same-target transition race; provenance lost-update). |
| 1235 | `REPORT-fix-audit.md finding 1, **reproduced live 30/30**` | DANGLING | PROVENANCE (citation) | ⚠ **DEFECT in the number** — §D2(a). |
| 1308 | `REPORT-fix-audit.md finding 2, **reproduced live 40/40**` | DANGLING | PROVENANCE (citation) | ⚠ **DEFECT in the number** — §D2(b). |
| 1984 | `report_path="REPORT-comms-c0-contract.md"` | — | **NOT A CITATION** | Fixture value for the `report_path` column. But see **§E1** — it is worth an operator ruling anyway. |
| 2057 | `report_path="REPORT-comms-c0-contract.md"` ×2 | — | **NOT A CITATION** | Same fixture, re-SELECT leg. See §E1. |

---

## C. Extension population (28) — report-shaped citations the `.md` pattern cannot see

**How I found these:** a vocabulary sweep for `blindreader|audit-102|audit-fix-1|dry-[0-9]|scratchpad/|adversary|coldaudit|fixwave|probe-[0-9]`, then subtracting every line the `.md` pattern already matched. This is the move the brief flagged as productive, and it doubled the visible corpus in `test_message_ledger.py`.

### C1 — `test_message_ledger.py`: 9 bare `W<n>` labels — **NOT dangling, UNADDRESSED**

The nine `KILLS the adversary's W<n>` docstrings name a wrong-build label with no address at all.
**I traced the target: it is TRACKED** — `docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md`, whose W1–W11 table sits at lines 68–77 and matches every label.

| line | label | verdict | why |
|---|---|---|---|
| 396 | `KILLS the adversary's W5` | PROVENANCE | Docstring states the mechanism (leaked `message:` prefix round-trips through every equality assertion). |
| 561 | `KILLS the adversary's W8` | PROVENANCE | Full dedupe-by-`name`-vs-`id` reasoning inline. |
| 600 | `KILLS the adversary's W9` + `W10` | PROVENANCE | Both wrong builds parenthesised inline with their exact drop behaviour. |
| 971 | `KILLS the adversary's W2` | PROVENANCE | The 6/2/cap-5 fixture arithmetic and all three distinct wrong answers are inline. |
| 1240 | `⚠ The adversary wondered whether this is a spec GAP` | PROVENANCE | The question is *answered* inline ("It is not — both the param and the column are in the approved design"). |
| 1655 | `KILLS the adversary's W3` | PROVENANCE | Parameter-monoculture reasoning inline. |
| 1699 | `(the adversary's W1)` | PROVENANCE | The orthogonality reason is the sentence itself. |
| 1755 | `KILLS the adversary's W1` | PROVENANCE | The #94 shape is spelled out inline. |
| 1889 | `KILLS the adversary's W4` | PROVENANCE | `asked_at` read-time-fabrication reasoning inline. |

**ONE optional edit makes all nine resolvable at near-zero churn** — the finding's own "anchor once
per file" suggestion, and here the anchor target is *tracked*, so it is durable:

```
+# ``W<n>`` labels below name wrong builds from
+# ``docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md`` (table §W1–W11).
```
Placed once near the module docstring's existing source list (~line 21). I recommend it; it is not
required by either verdict.

### C2 — remaining extension sites

| file:line | citation | status | verdict | why |
|---|---|---|---|---|
| `test_brief_ledger.py:1492` | `see REPORT §FOLLOW-UP` | DANGLING | PROVENANCE | A bare `REPORT` with no name at all — unresolvable even in principle. But it flags an ordering/cap concern that §9.2 already owns, and the sentence states the substance ("ORDER + CAP are RENDER concerns"). Nothing to repoint *to*. |
| `test_message_ledger.py:188` | `REPORT-recon-pkt03 §F.4` | **TRACKED** | LEAVE | Resolves (missing only `.md`). §F.4 verified at line 453 — and it is a *correction to a brief's premise*, exactly the knowledge worth keeping. |
| `test_message_ledger.py:1375` | `REPORT-recon-pkt03 §F.4` | **TRACKED** | LEAVE | Same, second occurrence. |
| `test_comms_tool.py:783` | `adversary P2 finding #3` | DANGLING | PROVENANCE | Empty-roster branch behaviour stated inline. |
| `test_comms_tool.py:795` | `adversary P2 finding #5` | DANGLING | PROVENANCE | The label/set agreement pin is described inline. |
| `test_comms_tool.py:1117` | `BLOCKER pin (contract-adversary §1)` | DANGLING | PROVENANCE | The self-ack wiring requirement is stated in full. |
| `test_comms_tool.py:1124` | `passed the ENTIRE pre-adversary contract (832 passed, 0 failed)` | DANGLING | PROVENANCE | ⚠ historical count, §D2(f), low. |
| `test_comms_tool.py:1536` | `pre-adversary contract. Finding #98…` | DANGLING | PROVENANCE | **#98** is durable and carries the monoculture closure. |
| `test_comms_tool.py:2125` | `adversary P2 finding #4: MEASURED at limit=200` | DANGLING | PROVENANCE | limit=200 is `_MAX_FLEET_LIMIT`, an in-tree constant — re-derivable. |
| `test_comms_tool.py:2386` | `Contract-adversary §2` | DANGLING | PROVENANCE | "the bound is a caller/SHAPE error" — the claim is the sentence. |
| `test_comms_tool.py:2520` | `contract-adversary §1` | DANGLING | PROVENANCE | Parametrised-over-brief-NAME rationale inline. |
| `test_comms_wiring.py:480` | `contract-adversary §1` | DANGLING | PROVENANCE | Same rationale, E2E leg. |
| `test_comms_schema.py:1811` | `⚠ RESIDUAL 7.4 (adversary)` | DANGLING | PROVENANCE | Read in full: the residual's entire content is inline — *"a NONEXISTENT one is rejected by `ENFORCED` before endpoint TYPING is ever consulted — so the test would pass for a neighbouring reason"*. Self-contained; a model comment. |
| `test_comms_schema.py:2269` | `⚠⚠ MAJOR-4 (adversary)` | DANGLING | PROVENANCE | The whole wrong-table analysis is inline and its *durable* half (`REPORT-audit-edge-preflight.md §Q5`) is TRACKED and cited four lines down. |
| `test_comms_schema.py:2393` | `The adversary's own first write-poisoning probe failed exactly this way (§8.2)` | DANGLING | PROVENANCE | The failure mode is described completely ("poisoning on BOTH arms because its control was broken for a DIFFERENT reason"). §8.2 names a section of a gone report, but nothing follows from it. |
| `test_comms_render_architecture.py:480` | `the adversary-found gap` | DANGLING | PROVENANCE | Unaddressed but the gap is the docstring's whole subject. |
| **`test_task_ledger.py:1425`** | `scratchpad/contract-v5/capture_engine.py` | **DANGLING** | **LOAD-BEARING** | §C3 below. Verified: `scratchpad/contract-v5/` does not exist; `git ls-files scratchpad/` is empty (the whole dir is untracked). |
| **`test_task_ledger.py:1529`** | `scratchpad/PKT-06-build-design.md` | **DANGLING** | **LOAD-BEARING** | §C4 below — and the surrounding sentence's claim is now uncheckable. |
| `test_task_ledger.py:2078` | `the cold adversary … built wb-string-gate … scored 545 passed` | DANGLING | PROVENANCE | No address at all, but **finding #102** is named in the first line and the mechanism is exhaustive. ⚠ "545 passed" — §D2(f), low. |

#### §C3 — `test_task_ledger.py:1425`: the engine-string capture provenance

> `# LIVE-CAPTURED ASSERT text (SurrealDB 3.1.5, spike-surreal, 2026-07-13,`
> `# scratchpad/contract-v5/capture_engine.py). The engine says "must conform to";`
> `# it has NEVER said "assertion". The previous, hand-typed value here contained the`
> `# word "assert" … which is exactly why the ASSERT class looked alive for this repo's`
> `# entire life while never once firing in production (audit B2). Fixture and code shared one imagination.`

This is load-bearing on the repo's own terms: it is the provenance for a **live-captured engine
string** whose hand-typed predecessor caused an entire error class to look alive while never firing.
A future engineer on a new SurrealDB floor must re-capture it, and the capture tool is gone.

**But the FACT is independently corroborated in a tracked, canonical home.** I verified
`docs/reference/surrealdb-31-capabilities.md` §6.1 (line 488) carries a live probe transcript with
the exact wording: `CREATE via='publish' : RAISED -> Found 'publish' for field \`via\` … must conform to: …`.

```
-# LIVE-CAPTURED ASSERT text (SurrealDB 3.1.5, spike-surreal, 2026-07-13,
-# scratchpad/contract-v5/capture_engine.py). The engine says "must conform to";
+# LIVE-CAPTURED ASSERT text (SurrealDB 3.1.5, spike-surreal, 2026-07-13; the same
+# wording is transcribed in docs/reference/surrealdb-31-capabilities.md §6.1).
+# The engine says "must conform to";
```

The script's absence stops mattering once the string has a durable corroborating home. **Escalation:**
if `capture_engine.py` still exists anywhere on disk, committing it under
`docs/plans/v2/receipts/` would be strictly better than this repoint — operator's call.

#### §C4 — `test_task_ledger.py:1529`: a promise that can no longer be kept

> `# The design source (comms-c0-designer, resolved contract):`
> `#   scratchpad/PKT-06-build-design.md`
> `# Every error text below is asserted VERBATIM against that document — it is`
> `# the contract, not a paraphrase.`

**This is worse than a dangling citation and I am flagging it as a DEFECT (§D3).** The sentence
does not merely cite — it asserts that a set of error-string assertions are *verbatim transcriptions
of an authoritative document*. That document is unreachable, so **no one can ever check the claim
again**, and a future engineer changing an error string cannot tell whether they are diverging from
a contract or editing free prose. There is no durable address to repoint to; the design doc is not
in `docs/`, not in `docs/plans/v2/receipts/`, and `scratchpad/` is untracked.

**Recommendation (operator's call, two options):**
1. **Recover** — if `scratchpad/PKT-06-build-design.md` exists on disk, commit it to
   `docs/plans/v2/receipts/` and repoint. *(Preferred: it preserves the contract.)*
2. **Strike the claim** — replace "asserted VERBATIM against that document — it is the contract, not
   a paraphrase" with "asserted VERBATIM as pinned here — these literals ARE the contract", making
   the tests self-authoritative and the sentence true again.

I did not check whether the file exists on disk, because `scratchpad/` is outside my read scope's
intent and the answer changes which option is right — that is an operator decision, not mine.

---

## D. DEFECTS — flagged loudly and separately, NOT repointed

### D1 — ⚠⚠ STALE RED-EXPECTATION PROSE IN TWO FILES (highest-severity finding in this report)

Two modules declare themselves the RED half of a TDD cycle **against production symbols that have
since shipped**. Verified against the tree:

| claimed missing | actually present |
|---|---|
| `BriefLedger.subscribed_name_skew` — *"has no `subscribed_name_skew` yet, so the call raises `AttributeError`"* (`test_brief_ledger.py:1484-1491`) | `loremaster/loremaster/briefs.py:1093: async def subscribed_name_skew(` |
| `auto_ack_at_register` — *"a NEW keyword … that today's shipped signature does not accept"* (`test_comms_render_architecture.py:18-20`) | `server.py`, **5 occurrences** |
| `_HEARTBEAT_SKEW_NAMES_CAP` — *"a clean tree — which has no `_HEARTBEAT_SKEW_NAMES_CAP` symbol"* (`test_comms_render_architecture.py:487-488`) | `server.py`, **4 occurrences** |

This is precisely the class repo CLAUDE.md names: *"compressed doc claims contradicting the
implementation"* and *"prose that describes behaviour must be DERIVED from the behaviour, not
re-stated beside it."* A reader of `test_comms_render_architecture.py` today is told the whole module
is expected RED; it is green, and the deleted reports that held the RED tails cannot correct them.

**This is why I refused to repoint `test_brief_ledger.py:1484` and `test_comms_render_architecture.py:40`.**
Both cite satisfiability receipts — repo law makes those load-bearing, and my instinct was REPOINT.
But repointing a citation whose surrounding claim is false **launders the false claim**: it converts
"stale prose with a broken pointer" into "stale prose with a durable pointer", which reads as
verified. The brief's rule is explicit and I followed it.

**Recommended fix (outside my writable set — flagging, not editing):** the RED-expectation blocks in
both files should be re-tensed to past ("was RED at authoring against …; shipped in packet 02") or
struck. That is a prose edit on ~4 blocks, and it is a *separate wave* from #152.

### D2 — Inherited numbers whose instrument is gone

Precedent: the operator ruled the unreproducible `30.2%` in `_txn.py` **STRUCK**, not repointed —
*"an inherited number whose instrument is absent is a rumor; precision is not a reason to keep it."*
Applying the same test, and distinguishing honestly between re-derivable and not:

| # | site | number | re-derivable in-tree? | recommendation |
|---|---|---|---|---|
| a | `test_task_ledger.py:1235` | "reproduced live **30/30**" | **NO** — measures the OLD buggy build's failure rate; that build is gone | **STRIKE.** The qualitative claim ("the CURRENT bug instead returns TWO `Task` successes") stands alone and the pin below proves it. |
| b | `test_task_ledger.py:1308` | "reproduced live **40/40**" | **NO** — same shape | **STRIKE**, same reasoning. |
| c | `test_brief_ledger.py:1217` | "407 round-trips / **234 ms** at limit=200" | round-trips YES (`_query_count` is in this file); **234 ms NO** — no in-tree instrument measures wall-clock | **STRIKE "/ 234 ms" only.** Keep 407. |
| d | `test_brief_ledger.py:1654` | "**6.1×** leaf-elapsed at 11× rows" | **NO** — the test pins the query PLAN, not the ratio | **Operator's call.** Weaker case than (a)/(b): it justifies *why* the plan is pinned rather than asserting a defect rate. I lean KEEP-with-caveat over strike. |
| e | `test_comms_render_architecture.py:495` | "passed the FULL render contract **617/0**" | **NO** — the suite has since changed shape (≈6079 collected today) | Low. Clearly labelled historical. Lean KEEP. |
| f | `tool:758` "643 tests green" · `tool:1124` "832 passed, 0 failed" · `task_ledger:2078` "545 passed" | — | **NO** — all pre-date the current suite shape | Low, same class as (e). Flagged for completeness per "every residual gets an individual verdict"; I recommend no action. |

**I am not confident (a)–(c) should be struck without an operator ruling** — the `30.2%` precedent is
close but that number sat in *production* prose, and these sit in *test* docstrings explaining why a
concurrency pin exists. A reproduction rate arguably *is* the rationale ("this was not flaky, it was
30/30"). I would strike them anyway, because an unverifiable 30/30 invites exactly the false
confidence the precedent condemns — but I flag the disagreement rather than acting on it.

### D3 — `test_task_ledger.py:1529` asserts an uncheckable verbatim-contract claim

Detailed in §C4. Distinct from D2: not a bad number, a **promise of an authority that no longer
exists**, on a set of error-string assertions. Needs a ruling (recover vs. strike).

---

## E. Escalations — things I noticed, per scope law

### E1 — ⚠ The `report_path` fixtures canonicalise the very convention #152 condemns

`test_task_ledger.py:1984` and `:2057` use `report_path="REPORT-comms-c0-contract.md"` — a repo-root
`REPORT-*.md` name — as the exemplar value for the `TaskLedger.report_path` **column**. These are not
citations, so they earn no verdict. But they are arguably **#152's root at the data-model level**:
the ledger has a first-class field for "where this task's receipts live", and its only documentation
by example points at the form repo law requires deleted before every image build.

**Question for the operator:** should the `report_path` fixtures (and, more importantly, the fleet
convention they teach) model the durable `docs/plans/v2/receipts/<date>-<packet>/REPORT-<name>.md`
form that packet 03 actually used and that resolves today? That would make the ledger's own field
teach the fix rather than the defect. **I did not touch it** — it is a design decision well outside
a citation adjudication, and it would change what agents write into a live production column.

### E2 — The `.md`-pattern grep is blind to line-wrapped citations (§A)

2 of 19 sites in the largest file were invisible to the brief's regex. **Any wave that acts on #152
across the other adjudicators' scopes should re-run with a line-joined pass** — otherwise the
per-scope counts are systematically low, in the same direction and for the same structural reason
the finding's own "~30 vs 61" caution describes.

### E3 — The tracked-vs-dangling split is a convention boundary, not an accident

All 7 resolvable sites are packet-03; all 68 dangling ones predate it. The packet-03 wave archived
its receipts under `docs/plans/v2/receipts/2026-07-19-packet03/` **before** deleting the root
reports, and every one of its citations — including section anchors (§Q5, §F.4, §UPDATE 5eb445b,
§"CONSEQUENCES FOR THE BUILD") — resolves exactly. **The convention works; it simply started too
late.** The durable fix for this finding class is to make that archive step mandatory at wave close,
not to repoint 68 historical citations.

### E4 — Basename-only addressing is fragile but currently sound

The 5 tracked `.md` citations name a bare basename (`REPORT-probe-pkt03-store.md`), not a path. They
resolve today only because each basename is unique in the tree. Cheap hardening: prefix the archive
path. Not a defect; not worth a wave on its own; worth folding into any edit that touches those
lines.

---

## F. What I did not do

- **I edited nothing.** Read-only throughout; this report is my only written file.
- I did not stage, commit, or touch git state.
- I did not run the test suite (brief did not ask; verification law §3).
- **Tool honesty (brief-base §4):** I used `git grep` rather than lore for the sweeps. This is a
  sanctioned fallback under repo CLAUDE.md — case (b), *non-symbol textual seams (prose in string
  literals and comments)* — and case (a), *exhaustiveness where one missed site matters*. lore's
  symbol graph cannot see comment prose. I used `lore_findings` for the ledger queries (§B3, and the
  #152 pull), which is what it is for.
