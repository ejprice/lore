# REPORT-adj-152-rep-rest

brief-base v5 read

## SUMMARY BLOCK

- **state:** done-with-deviations
- **deviations:**
  - The brief's grep matched `_comms_fakes.py` (2 sites) — it is the comms cluster but the
    exclusion globs (`test_comms_*.py`, `*ledger*.py`) do not cover it. I adjudicated both and
    flagged the boundary (§6.1). Possible overlap with the comms adjudicator.
  - `test_retry_seam.py` (3 sites) is in my scope by the brief's grep but a prior agent
    (`REPORT-adj-152-retryseam.md`) already adjudicated that file. I adjudicated independently
    and did not read its verdict table before deciding. Overlap noted (§6.2).
- **decisions-needed:**
  - **DEFECT 1 (§5.1) — `test_render.py`'s BINDING SPEC is a `/tmp` session path.** Not
    dangling: *unrecoverable by construction*. Two more test modules chain off it. No durable
    address exists to repoint at. Needs an owner.
  - **DEFECT 2 (§5.2) — 3 LOAD-BEARING sites have NO durable address to repoint to.** Their
    authority (an open-contract-decision list, a mutation receipt, an accepted known bound)
    existed only in deleted scratch. Repointing is impossible; striking or re-deriving is the
    only honest move. Operator ruling wanted on which.
  - **DEFECT 3 (§5.3) — 4 measured numbers whose instruments are gone** (`7 of 119 budgets`,
    `715 passed`, `407 round-trips`, and an unstated wall-time). Flagged, not repointed.
  - **DEFECT 4 (§5.4) — an open obligation with no ledger row** (`test_impact.py:812`,
    "flagged for the team-lead as a writable-set gap"). Never filed as far as I can tell.
- **receipt pointers:** derivation §1 · resolvable/dangling split §2 · **63-row verdict table §4**
  · defects §5 · extension population §6 · the SOLVED pattern §3
- **result: 56 PROVENANCE · 5 LOAD-BEARING · 2 NOT-A-CITATION (grep false positives).**
  Leave-it ratio **56/61 = 91.8%** of real citations. No bulk rewrite proposed.

---

## 1. Derivation — I did not inherit the lead's counts

```
$ git grep -nE 'REPORT-[A-Za-z0-9._-]+\.md' -- 'loremaster/tests/*.py' \
    ':!loremaster/tests/test_comms_*.py' ':!loremaster/tests/*ledger*.py' | wc -l
63
```

63 sites (the brief estimated "roughly 66"). Per-file, derived from the grep, not a hand-list:

| file | sites | | file | sites |
|---|---|---|---|---|
| test_mcp_server.py | 11 | | test_render_mypy_layer.py | 2 |
| test_impact.py | 8 | | test_graph_surreal.py | 2 |
| test_map.py | 6 | | _comms_fakes.py | 2 |
| test_symbols.py | 4 | | test_text_hygiene.py | 1 |
| test_render_seam_pins.py | 4 | | test_surreal_store.py | 1 |
| test_agent_registry.py | 4 | | test_surreal_harness.py | 1 |
| test_retry_seam.py | 3 | | test_sanitise.py | 1 |
| test_render.py | 3 | | _surreal_fakes.py | 1 |
| test_workspace_status.py | 2 | | render_injection_scaffold.py | 1 |
| test_surreal_fakes.py | 2 | | test_shellout_seam_perimeter.py | 2 |
| test_search.py | 2 | | | |

The lead's hand-list matched the top five files exactly. It was right; I re-derived anyway.

## 2. The resolvable/dangling split — DERIVED

```
$ git grep -ohE 'REPORT-[A-Za-z0-9._-]+\.md' -- 'loremaster/tests/*.py' \
    ':!...test_comms_*.py' ':!...*ledger*.py' | sort -u   →  33 distinct names
$ git ls-files | grep -oE 'REPORT-[A-Za-z0-9._-]+\.md' | sort -u  →  13 distinct names
```

**Intersection: EMPTY. All 33 distinct cited names in my scope are DANGLING — zero in the
happy category.**

The 13 tracked reports are all recent-convention archives (`docs/plans/v2/receipts/2026-07-19-packet03/`
× 8, `docs/orchestration/receipts/2026-07-19-comms/` × 5). Nothing in the test tree cites any of
them. The archive convention post-dates every citation in my population — which is the whole story
of this finding in one line.

Two cited names exist as UNTRACKED files in the working tree right now (`REPORT-blindreader-150.md`,
`REPORT-contract-151.md`). Untracked is not durable: repo law deletes them before the next image
build. I treated both as dangling. `test_surreal_harness.py:54` says so itself, correctly (§3).

## 3. THE SOLVED CASE — the pattern the other 62 sites should copy

`loremaster/tests/test_surreal_harness.py:51-60` already contains a **per-file anchor block** that
resolves its whole citation vocabulary:

> `HOW TO RESOLVE THE `blindreader-150 F*` / `audit-150 R*` CITATIONS IN THIS FILE.`
> `They are review-pass identifiers from finding #150's review wave, and the reports they name`
> `(REPORT-blindreader-150.md, REPORT-audit-150*.md) are UNTRACKED scratch files at the repo root`
> `that repo law requires be deleted before any image build — so the citations are not followable`
> `and were never meant to be. Their durable addresses are the ledger row #150 ... #151 ... and the`
> `wave's commits, in order: 6be78d6 RED · 0734d78 route · 20e7635 attribute/compose/release`

This is strictly better than repointing 60 individual citations: it costs one block per file,
names the dangle *as* a dangle (so no future reader wastes time hunting), and supplies the durable
rows and SHAs. **My recommendation for the PROVENANCE bulk is: do nothing to the citations, and
optionally add one such block per affected file.** That is the minimal-churn move repo law wants.

A second exemplar worth naming: `test_render_mypy_layer.py:32-38` cites a dead report's probes —
**and then says the fixtures were COMMITTED into `loremaster/tests/render_mypy_fixtures/`
"rather than left in the session-ephemeral scratchpad, so this pin is durable across sessions."**
The citation dangles; the artifact does not. That author solved the problem at authoring time.

## 4. THE VERDICT TABLE — every site, individually

Legend: **P** = PROVENANCE (leave it) · **LB** = LOAD-BEARING (repoint) · **N/A** = not a citation.
All named reports are DANGLING unless stated; per §2 that is *all* of them.

### test_mcp_server.py (11)

| line | citation | verdict | note |
|---|---|---|---|
| 1099 | `(REPORT-audit-w1.md F1/F4/F5)` | **P** | The defect is stated in full inline (`lore_read`'s not-found text taught the dead `search_code`). |
| 1102 | `(REPORT-audit-w2.md F1)` | **P** | Same block; both instances named with their exact dead-name strings. |
| 2431 | `confirmed by the deletion-gate grep in REPORT-builder-flip-w2.md that nothing outside their own wrapper + these tests called them` | **P** | Close call. It IS the receipt for an exhaustiveness claim — but the claim justifies *removed* tests, not a live pin, and the surviving coverage is named inline (`test_graph_surreal.py`'s `TestBlastRadius`/`TestTestsFor`/`TestReferences`). A reader can re-derive with `lore_impact`. Leave it. |
| 3560 | `REPORT-slate-fixer-63.md §3 / finding #65 proved` | **P** | **Durable address already present** (`finding #65`) in the same clause. |
| 4824 | `S7 (audit gap, REPORT-slate-audit-server.md §C2)` | **P** | Mechanism inline down to `server.py:1931-1935` and the exact fixture scores. |
| 4971 | `F1 (REPORT-audit-tweaks.md)` | **P** | Class invariant stated in full. ⚠ carries a measured `7 of 119 budgets` + a dead `scratchpad/probe_budget.py` — see §5.3. |
| 6992 | `report_path="REPORT-x.md"` | **N/A** | **Not a citation.** A test fixture VALUE passed to `task_ledger.transition`. Grep false positive. |
| 6996 | `f"- task {task_id} by me: shipped it (report REPORT-x.md)"` | **N/A** | **Not a citation.** The assertion string for the same fixture. Grep false positive. |
| 7589 | `PKT-06 cold-audit Probe 2, REPORT-comms-c0-audit.md` | **P** | The registry mechanism + its known blind spot are both stated inline. |
| 7897 | `(SF-3, REPORT-polish-audit.md)` | **P** | Reason inline: pinned to `ValueError` + two no-write postconditions. |
| 7912 | `SF-3 (REPORT-polish-audit.md): narrowed from a bare pytest.raises(Exception)` | **P** | The narrowing and its reason are both spelled out on the next four lines. |

### test_impact.py (8)

| line | citation | verdict | note |
|---|---|---|---|
| 352 | `concern 6 (REPORT-slate-audit-graphres.md)` | **P** | Explains a dataclass default; the override contract is stated inline. |
| 563 | `(see REPORT-slate-fixer-63.md §2)` | **P** | **Durable address already present** — the comment opens `Finding #63:`. |
| 812 | `See REPORT-polish-contract.md — against the in-memory graph double this bridge already holds` | **P** | Reasoning (why the FALLBACK route is not pinned) is fully inline. ⚠ but the same docstring carries an unfiled obligation — see §5.4. |
| 907 | `SF-2 (REPORT-polish-audit.md): this test was VACUOUS under its old name/assertion` | **P** | The vacuity is proven inline (`depth == 1` ⇒ `module_rollups` empty by construction). |
| 934 | `See REPORT-builder-flip-w2.md for the full live-repro receipts.` | **P** | Closest call in this file — it explicitly promises RECEIPTS at a dead address. Kept as P because the very next lines name the exact repro target (`loremaster.search._sanitise_line`, 7 production sites), the exact tools (`lore_impact`/`lore_references`), and the durable rows (#19/#1/#2/#39/#30). Re-derivable. |
| 1296 | `F3 (REPORT-audit-tweaks.md)` | **P** | The `(tier, file_path)`-vs-module-label collision is explained in full. |
| 1372 | `REPORT-slate-fixer-63.md §3 proved that gate is actively WRONG` | **P** | **Durable addresses present** (`#30/#43/#65`) and the wrong-gate mechanism is stated inline with the live collision named. |
| 1470 | `concern 6 (REPORT-slate-audit-graphres.md, ledger task ad3e4211801f47dfb62cac6ec65126f0)` | **P** | **Carries a ledger task id** — already a durable address. |

### test_map.py (6)

| line | citation | verdict | note |
|---|---|---|---|
| 757 | `the §2/§3 pin contradiction flagged in REPORT-polish-green.md's ⛔ block` | **P** | Names `docs/design/2026-07-04-map-test-segregation.md` — **verified TRACKED** — and states the ruling inline. |
| 921 | `SB-1 (REPORT-polish-audit.md)` | **P** | The advertised string and §5's requirement are quoted inline. |
| 1040 | `SB-1 (REPORT-polish-audit.md)` | **P** | The trailer's exact text and §7b's promise are quoted inline. |
| 1277 | `docs/design/2026-07-06-client-needs-consult.md Synthesis S2 / REPORT-slate-scout-s2.md` | **P** | The design doc is **verified TRACKED**; root cause + fix stated over 12 lines with `graph.py:436-441`. |
| 1297 | `exactly the live collision REPORT-slate-scout-s2.md reproduced` | **P** | The collision is named inline (`AppContext`/`_enforce_search_budget`). |
| 1353 | `(REPORT-slate-scout-s2.md §1-§2)` | **P** | Supports an assertion whose reason is in the comment above it. |

### test_symbols.py (4)

| line | citation | verdict | note |
|---|---|---|---|
| 657 | `S2 fix (2026-07-06, REPORT-slate-scout-s2.md §3-4c)` | **P** | Root cause + hostile fixture described in full. |
| 971 | `Finding #62 (2026-07-06, REPORT-slate-scout-s2.md §3 side note)` | **P** | **`#62` already present.** |
| 1032 | `Finding #62 (canonical upgrade, 2026-07-06, REPORT-slate-builder-s2.md` | **P** | **`#62` already present.** |
| 1033 | `decisions-needed / REPORT-slate-scout-s2.md side note)` | **P** | Continuation of 1032; same durable anchor. |

### test_render_seam_pins.py (4)

| line | citation | verdict | note |
|---|---|---|---|
| 48 | `R1 residual (REPORT-phase0-audit-1.md §RESIDUALS)` | **P** | The alias-evasion mechanism and its fix are stated in full. |
| 135 | `R1 residual hardening (... §RESIDUALS, re-verify follow-up)` | **P** | Includes the explicitly-NOT-caught shape (`_r = render_line`) inline. |
| 382 | `R1 residual self-test (... §RESIDUALS, re-verify follow-up)` | **P** | "EXPECTED RED against the pre-R1 scanner" is correctly qualified as historical. |
| 430 | `**R1 residual, and its accepted narrower gap (REPORT-phase0-audit-1.md §RESIDUALS):**` | **LB** | **This is a KNOWN BOUND acceptance.** Repo law: a bound must carry rationale + a named re-open trigger, or it "cannot be silently inherited, and cannot be silently fixed". The mechanism is inline, but the *authority for accepting the gap* is the dead report — and its parent spec is a `/tmp` path (§5.1). **No durable address exists.** See §5.2. |

### test_render.py (3)

| line | citation | verdict | note |
|---|---|---|---|
| 6 | `Cold audit: REPORT-phase0-audit-1.md.` | **P** | Bare provenance line. ⚠ the same docstring's `Spec:` is a `/tmp` path — **DEFECT 1, §5.1**, a separate and worse problem than this citation. |
| 296 | `R2 residual (REPORT-phase0-audit-1.md §RESIDUALS, re-verify follow-up)` | **P** | The `"\n"`-only gap and the full codepoint list are stated inline. |
| 350 | `Verbatim-shape reproduction of REPORT-phase0-audit-1.md's residual chain fixture (scratchpad/audit1/residual/comms_render.py)` | **P** | The fixture shape is described completely inline AND the test *is* the reproduction. ⚠ the cited `scratchpad/` receipt is gone — §5.3. |

### test_render_mypy_layer.py (2)

| line | citation | verdict | note |
|---|---|---|---|
| 2 | `cold audit REPORT-phase0-audit-1.md §REMEDIATION item 4` | **P** | The finding is restated over the next 25 lines, including the refuted claim and the re-open trigger ("if a future mypy ships PEP 675 enforcement, row 3's assertions will start FAILING loudly — that failure is the intended signal"). A model docstring. |
| 32 | `the cold audit's own probes (REPORT-phase0-audit-1.md §PROBE-A, scratchpad/audit1/row{0-4}_*.py)` | **P** | **The happy case.** The fixtures were COMMITTED in-tree and the docstring says why. The dead address names only the historical source. See §3. |

### test_agent_registry.py (4)

| line | citation | verdict | note |
|---|---|---|---|
| 9 | `Where this file's contract decisions are genuinely open in the spec, they are recorded in ``REPORT-c1-contract-ledgers.md``` | **LB** | **The record of every silently-chosen spec ambiguity in a contract file, at a dead address.** Repo law: "Spec ambiguity is a defect, not a judgment call" — the list of what was chosen is exactly what must survive. Nothing inline substitutes. The binding spec `docs/design/2026-07-12-pkt28-c1-semantics.md` is **TRACKED** but by construction does not hold the *open* decisions. **No durable address exists.** §5.2. |
| 704 | `see REPORT-c1-contract-d1d2-b.md's live-vs-synthetic split` | **P** | The split is stated inline (>200-agent live fixture slow; over-cap arithmetic pinned in `test_comms_tool.py` — a live in-tree address). |
| 765 | `F2 (REPORT-c1-audit-fixwave.md, BLOCKER)` | **P** | The gap and the wrong build are described in full. ⚠ carries `715 passed` — a measured number whose instrument is gone (§5.3), though illustrative rather than served. |
| 777 | `see ``REPORT-c1-contract-f123.md`` for the mutation receipt proving it goes RED the moment ``members`` is capped ...; a pin that cannot be shown failing is not a pin.` | **LB** | **The single clearest case in the corpus.** The docstring invokes repo law ("a pin that cannot be demonstrated failing is not a pin") and then points its proof at a dead address. The mutation proof is now unverifiable — so by the file's own stated standard this is not a pin. §5.2. |

### test_workspace_status.py (2)

| line | citation | verdict | note |
|---|---|---|---|
| 31 | `Design decisions taken here, and why (raised in REPORT-pkt01-contract-1.md):` | **P** | Textbook PROVENANCE: a numbered list follows giving every decision AND its reason, each with its own pin named. The report would add nothing. |
| 878 | `The ruling this class pins (reasoning in REPORT-pkt01-contract-1.md)` | **P** | The full reasoning follows in the same docstring (verbatim-serve; sanitising would be its own lie; the wire is JSON; the future-render guard is the type system). |

### test_surreal_fakes.py (2) · _surreal_fakes.py (1)

| line | citation | verdict | note |
|---|---|---|---|
| test_surreal_fakes.py:1423 | `REPORT-slate-builder-impactres.md decisions-needed #2` | **P** | The fidelity gap (fake defaulted `bare_fallback_used`/`_candidates`) is stated exactly. |
| test_surreal_fakes.py:1654 | `the gap REPORT-slate-builder-impactres.md's decisions-needed #2 flagged` | **P** | Restates the gap in full in the same sentence. |
| _surreal_fakes.py:1495 | `` `REPORT-slate-builder-impactres.md` decisions-needed #2 `` | **P** | Same gap, again stated in full, plus the mirrored production method named. |

### test_shellout_seam_perimeter.py (2)

| line | citation | verdict | note |
|---|---|---|---|
| 6 | `the cold re-audit (``REPORT-pkt01-audit-1.md``, ``# FINAL RE-AUDIT (exec seam)`` §2) found **five evasion doors**` | **P** | All five doors are enumerated, adjudicated and pinned *in this file*, under an explicit threat model, with finding **#138** named and a re-open trigger. Best-in-corpus documentation. |
| 36 | `(re-derived below and in ``REPORT-pkt01-contract-5.md``: across all 78 shipped modules ...)` | **P** | **Says "re-derived BELOW"** — the instrument is in this file, so the measured `78 modules` is live, not inherited. This is how a measured number should be cited. |

### test_search.py (2)

| line | citation | verdict | note |
|---|---|---|---|
| 2044 | `S4b audit finding #6/#5 (REPORT-slate-audit-searchstore.md)` | **P** | Repo law cited by name, `search.py:418` named, hostile-fixture requirement stated inline. |
| 2231 | `(S4b audit finding #1, REPORT-slate-audit-searchstore.md §Concern 6)` | **P** | Names **`scripts/search_score_survey.py`** — a committed script, the strongest address available — as the consumer. |

### test_graph_surreal.py (2)

| line | citation | verdict | note |
|---|---|---|---|
| 1991 | `wiring the counted-elision signal onto the ``lore_dead_code`` MCP tool itself is a server.py change out of this method's writable set (see REPORT-slate-builder-s1.md's #60 resolution note)` | **LB** | **A DEFERRED OBLIGATION whose ruling lives only at a dead address.** Nothing inline says what #60 resolved to or when the wiring lands. **Cheap fix — the durable address is already in the sentence.** See §5.2 for the exact edit. |
| 3398 | `THE BUG (live-reproduced, REPORT-slate-fixer-63.md SS2-3, finding #65)` | **P** | **`#65` already present**; the bug is described over 12 lines with the live repro named. |

### test_surreal_store.py (1)

| line | citation | verdict | note |
|---|---|---|---|
| 1302 | `The EXACT reported failure shape (REPORT-slate-builder-search.md §New Finding)` | **P** | The shape is pinned mechanically on the next line (`assert len(_REPORTED_SHAPE_LONG_QUERY) >= 340`) — the constraint is executable, not prose. |

### test_surreal_harness.py (1)

| line | citation | verdict | note |
|---|---|---|---|
| 54 | `the reports they name (``REPORT-blindreader-150.md``, ``REPORT-audit-150*.md``) are UNTRACKED ...` | **P — already resolved** | This citation exists *to declare the dangle* and supply durable replacements (#150, #151, three commit SHAs). **Do not touch it. Copy it.** See §3. |

### test_sanitise.py (1) · test_text_hygiene.py (1) · render_injection_scaffold.py (1)

| line | citation | verdict | note |
|---|---|---|---|
| test_sanitise.py:27 | `mirrors REPORT-comms-c0-audit.md's reproduced byte-perfect forgery` | **P** | The forgery literal is on the next two lines (`_ROW_FORGE_INPUT`/`_EXPECTED`) — the fixture IS the receipt. |
| test_text_hygiene.py:14 | `(see REPORT-builder-hygiene-ast.md for the fix inventory)` | **P** | Both defects are named in full inline, and the sentence itself says the module "is the invariant ... not just a record of the fix". |
| render_injection_scaffold.py:4 | `PKT-06 cold-audit Probe 2, REPORT-comms-c0-audit.md` | **P** | Pure extraction provenance; the scaffold's contents and consumers are listed inline. |

### test_retry_seam.py (3) — overlaps `REPORT-adj-152-retryseam.md`, adjudicated independently

| line | citation | verdict | note |
|---|---|---|---|
| 3783 | `Provenance, so nobody has to trust me: REPORT-blindreader-dry-1.md ... found F1, F2, F3, F4` | **P** | Self-describes as provenance. Each of F1–F4 is pinned below with its own full mechanism. The sentence's promise of external verification is void, but nothing actionable is lost. |
| 3786 | `REPORT-audit-dry-2.md (the cold REFUTE audit) found the broken instrument repaired in section 5 above` | **P** | Points at an in-file section (`section 5 above`) for the substance. |
| 7353 | `The mutation proof for the property itself is therefore owed AFTER the signature change, and is recorded as such in REPORT-contract-151.md.` | **LB** | **An OWED obligation with a named decision point recorded only at a dead address.** Deferral law requires the decision point survive. **Cheap fix — `#151` is the durable row and is already the subject.** §5.2. |

### _comms_fakes.py (2) — cluster-boundary, see §6.1

| line | citation | verdict | note |
|---|---|---|---|
| 36 | `see ``REPORT-c1-hardener.md`` for the reintroduced-TOCTOU proof` | **P** | Borderline (it points at a *proof*), but the losing mechanism is stated in the same sentence: a mint that reads max-of-rows then yields before writing loses updates in that window. |
| 676 | `(finding #94, REPORT-c1b-contract-9495.md)` | **P** | **`#94` already present.** ⚠ carries `407 store round-trips at limit=200` — §5.3. |

---

## 5. DEFECTS — flagged loudly, NOT quietly repointed

### 5.1 DEFECT 1 — `test_render.py`'s binding spec is a `/tmp` session path

`loremaster/tests/test_render.py:2-5`:

```
Spec: /tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bed98428-ca59-4bfb-83cc-2e9eec6f4724/
scratchpad/phase0-render-safety-ruling.md (v2, post-audit) — §ENFORCEMENT (the
failure matrix), §BUILD-NOW items 1-3/9, §C1-C5-AUTHORING, §D1.4.
```

This is **worse than a dangling report citation**. A deleted repo-root report at least had a
knowable name and a git history. A per-session `/tmp` UUID path is unrecoverable *by construction*
and was never even in the repo's filesystem.

Verified: `git ls-files | grep -i 'render-safety-ruling'` → **empty**. `git ls-files | grep -c '^scratchpad/'` → **0**.

**Blast radius — three modules chain off this one ruling:**
- `test_render.py:2` (`Spec:` — the whole module's work order)
- `test_render_seam_pins.py:4` — `scratchpad/phase0-render-safety-ruling.md — §ENFORCEMENT failure-matrix row 6`
- `test_render_mypy_layer.py:1` — `ruling v2 §BUILD-NOW item 9`
- plus `test_render_seam_pins.py:424` — `(ruling §REMEDIATION item 1)`

Every `§`-reference in the render-safety cluster resolves to nothing. The failure matrix that
defines *which rows mypy must catch* has no surviving address. I did not attempt a repoint —
there is nothing to point at. **This needs an operator ruling: reconstruct the ruling from the
tests (they encode most of it), or strike the spec references and declare the tests
self-describing.**

### 5.2 DEFECT 2 — the 5 LOAD-BEARING sites: 2 are cheap, 3 have no durable address

**The 2 cheap ones — durable address already in the sentence, drop the dead name:**

| site | current | proposed replacement (minimal) |
|---|---|---|
| `test_graph_surreal.py:1991` | `(see REPORT-slate-builder-s1.md's #60 resolution note)` | `(see finding #60's resolution note)` |
| `test_retry_seam.py:7353` | `and is recorded as such in REPORT-contract-151.md.` | `and is recorded as such against finding #151.` |

Both are pure address swaps: no surrounding prose changes, and both targets are live ledger rows.
I recommend executing these two.

**The 3 with NO durable address — repointing is impossible, and faking one would launder the loss:**

| site | what the citation is the authority for | why no address exists |
|---|---|---|
| `test_agent_registry.py:9` | the list of contract decisions left OPEN in the spec | the spec (`docs/design/2026-07-12-pkt28-c1-semantics.md`) is tracked but by definition does not contain what it left open; no finding row was ever filed |
| `test_agent_registry.py:777` | the mutation receipt proving the pin goes RED when `members` is capped | the receipt was in the deleted report; nothing re-ran it |
| `test_render_seam_pins.py:430` | the ACCEPTANCE of a known bound (re-assigned-name evasion) | its parent ruling is the `/tmp` path of §5.1 |

For these three, the only honest moves are **(a) re-derive** — re-run the mutation proof and record
it in-tree, re-enumerate the open decisions into a finding row, file the known bound as a finding
per repo law's "WHEN YOU CANNOT CLOSE A HOLE, PIN IT" — or **(b) strike the claim**, following the
operator's `30.2%` precedent: a claim whose instrument is absent is a rumor, and asserting an
unverifiable mutation proof is worse than asserting nothing.

**My recommendation: (a) for `test_agent_registry.py:777`** — re-running one mutation proof is
minutes of work and the pin is genuinely load-bearing (it guards `brief_get` coverage and
`brief_publish` skew). **(a) for `test_render_seam_pins.py:430`** — file the bound as a finding
with a re-open trigger; repo law explicitly demands this shape. **Operator ruling wanted on
`test_agent_registry.py:9`**, where re-deriving means re-reading a spec against a 1000-line
contract and I cannot scope that from here.

**I did not repoint any of the three.** Per my brief: quietly repointing an unverifiable claim
launders it.

### 5.3 DEFECT 3 — measured numbers whose instruments are gone

Four inherited figures in my population. None is a *served constant* (the dangerous class), so I am
flagging rather than demanding strikes — but repo law is explicit that a figure you didn't measure
is a rumor.

| site | number | instrument | status |
|---|---|---|---|
| `test_mcp_server.py:4971-4980` | `7 of 119 budgets dangled` | `scratchpad/probe_budget.py` | **gone** — `scratchpad/` is 100% untracked |
| `test_agent_registry.py:765` | `left the WHOLE SUITE GREEN (715 passed)` | the deleted audit's run | **gone**; also now certainly stale (suite is ~6079 collected) |
| `test_agent_registry.py:783` | *"see the report for the measured wall time"* | dead report | **gone — and the number is not even stated**, so the sentence is a pure dead pointer. Recommend striking the clause. |
| `_comms_fakes.py:676` | `measured 407 store round-trips at limit=200` | `REPORT-c1b-contract-9495.md` | **gone** |

Contrast `test_shellout_seam_perimeter.py:36`, which cites `78 shipped modules` and says
**"re-derived below"** — the instrument runs in the file. That is the correct shape.

**Broader flag, outside my population but found while sweeping:** `git ls-files | grep -c '^scratchpad/'`
returns **0**, yet the test tree cites `scratchpad/` paths at **33 sites** (§6.3). Every probe
receipt in the test tree is unrecoverable. A prior adjudicator (`REPORT-adj-152-retryseam.md`)
independently reported the same class as its DEFECT B. **Two adjudicators converging on this
suggests it is a bigger problem than the report citations that prompted #152.**

### 5.4 DEFECT 4 — an open obligation that appears never to have been filed

`test_impact.py:812-817` ends: *"the LIVE friction lives in the REAL `graph_surreal.tests_for`
(which looks up only literal bare/FQN name-ids, never `answers_to`) and its RED reproduction
belongs in `test_graph_surreal.py` — **flagged for the team-lead as a writable-set gap**."*

That is a known defect handed forward in a docstring, with no ledger row, no finding number, and no
named decision point. Repo law: *"'Documented' ≠ 'dealt with'"* and *"a deferral without a decision
point is a can-kick."* I could not find a corresponding finding. **Recommend filing one** (or
confirming it was folded into an existing row) — this is a real behaviour gap, not a citation
problem.

---

## 6. EXTENSION POPULATIONS — what the `REPORT-*.md` pattern cannot see

I ran four additional sweeps beyond the brief's pattern. How I found each is stated.

### 6.1 Cluster-boundary ambiguity (raised, not resolved)

The brief scopes me to "ALL TEST FILES EXCEPT the comms/ledger cluster", but its exclusion globs
(`test_comms_*.py`, `*ledger*.py`) do not match **`_comms_fakes.py`** — which is unambiguously the
comms cluster. Two readings:

1. *Follow the globs* → `_comms_fakes.py` is mine (what the grep produced).
2. *Follow the prose* → it belongs to the comms adjudicator.

**I adjudicated it (2 sites, both PROVENANCE) rather than dropping it** — a double-adjudicated site
is cheap, an unadjudicated one is the failure this finding exists about. Flagging for de-dup.

Same shape for `test_retry_seam.py`: in my grep, but `REPORT-adj-152-retryseam.md` already owns it.
I adjudicated its 3 sites without reading that report's table first, so our verdicts are
independent — **worth diffing**, since independent enumerations that agree are evidence and ones
that disagree are a finding.

### 6.2 Line-WRAPPED `REPORT-*.md` citations — MISSED BY MY OWN PRIMARY PATTERN

Found by grepping for bare `REPORT-` and subtracting the full-pattern matches. **The literal
population is undercounted because comment reflow splits the filename across two lines**, so
`REPORT-[A-Za-z0-9._-]+\.md` never matches:

| site | citation | verdict |
|---|---|---|
| `test_mcp_server.py:3496-3497` | `the P6-impact-green FRICTION note, REPORT-impact-`<br>`green-3.md` | **P** — mechanism fully inline (astroid resolution silently disabled when `project_roots` is empty, with the exact attribute `SurrealCodeGraph._resolution_enabled`) |
| `test_surreal_store.py:1197-1198` | `finding #66 was discovered from (REPORT-`<br>`slate-builder-search.md §New Finding)` | **P** — **`#66` already present**; the ~245/~340-char bisection is stated inline and pinned by an executable `>= 340` assert |

Neither name is tracked (`git ls-files | grep -iE 'impact-green|slate-builder-search'` → empty).

**This generalises: any sweep of this class using a single-line regex undercounts.** The production
sweep behind #152's filed count has the same exposure — I would re-derive it with a
newline-tolerant pattern before trusting the 61.

### 6.3 `scratchpad/` receipt citations — 33 sites, ALL unrecoverable

Found by `git grep -nE 'scratchpad/'` over my scope. **33 sites**, against a `scratchpad/`
directory with **zero tracked files**. Leaders: `test_retry_seam.py` (7), `test_surreal_store.py` (7),
`test_render*.py` (6), `test_findings.py` (3), `test_memory_backend.py` (2), `test_mcp_server.py` (3).

These are cited as *live probe receipts and capture instruments* — `capture_engine.py`,
`probe_bootstrap.py`, `measure_distinct.py`, `probe_long_query_69.py`, `probe_budget.py` — i.e. the
instruments behind measured claims. **This is a strictly worse class than the report citations**
(a report is prose you can live without; a probe is the only thing that can re-derive a number)
and it is larger in my scope than the wrapped-literal population. I did not adjudicate these — out
of my population — but per scope law I am surfacing all 33 as a class. §5.3 has the four that
intersect my sites.

### 6.4 Bare agent-name / section-label citations — large, not enumerated

`git grep -nE '(blindreader|audit-102|audit-fix|adversary|slate-…|dry-[0-9]|…)'` minus the `.md`
matches returns **well over 100 sites** in my scope, heavily concentrated in `test_retry_seam.py`
(~60) and `test_surreal_harness.py` (~15) — both already owned by other adjudicators, and
`test_surreal_harness.py` has already **solved** its instance with the §3 anchor block.

I did not enumerate the remainder site-by-site: it is a different population from my assignment and
enumerating it properly is its own wave. Two observations worth having:

- Many `adversary` hits are **not citations at all** — e.g. `# A port with nothing listening — the
  "server is down" adversary` appears in 6 files as a *description of a test fixture*. A
  vocabulary-keyed sweep over this population will produce heavy false positives; #152's own filed
  pattern (`blindreader|audit-102|audit-fix-1|adversary`) has this exposure, so **the filed
  production count of 61 may be inflated** in the opposite direction from §6.2's undercount. Both
  errors are present at once; neither cancels the other.
- The genuinely load-bearing ones in this class cluster in the same places as mine: owed mutation
  proofs, accepted bounds, and "the adversary built W-x and it passed N/N" claims.

**One concrete extension site inside my own files** (found via 6.4, reported per brief):
`test_agent_registry.py:783` — *"see the report for the measured wall time"* — a dead pointer with
no report name and no number. Covered in §5.3; recommend striking the clause.

---

## 7. What I did NOT do

- **I edited nothing.** `REPORT-adj-152-rep-rest.md` is my only written file. No git state touched.
- I did not run any test. No claim in this report depends on a test outcome.
- I did not read `REPORT-adj-152-retryseam.md`'s verdict table before adjudicating the three
  overlapping sites (I read only its summary block, to learn the overlap existed).
- I did not repoint the 3 no-durable-address LOAD-BEARING sites, on purpose (§5.2).

## 8. Tool honesty

lore's tools were used for the finding pull (`lore_findings action=get id_or_number=152`).
**Everything else in this report is grep**, said out loud per §4 of the base protocol — correctly
so under this repo's dogfood protocol, which names grep as honest for exactly these cases:
rename/citation **exhaustiveness** where one missed site matters (§6.2 proves the point — a
regex subtlety, not a semantic one, was hiding sites), and **non-symbol textual seams** (prose in
string literals and comments, which the code graph does not model). No lore weakness was routed
around, so nothing is owed to `lore_findings`.
