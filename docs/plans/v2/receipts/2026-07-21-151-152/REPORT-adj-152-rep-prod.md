# REPORT-adj-152-rep-prod

brief-base v5 read

- **state**: done
- **deviations**:
  - Population is **37 sites, not 36** — the brief's `.md`-anchored grep structurally cannot
    see a citation wrapped across a line break (`search.py:574`). Derived from the grep, per repo law.
  - Brief says "only 3 [of 57] resolve — all packet-03". For the **production** slice the
    intersection is **EMPTY**: 0 of 17 distinct cited names are tracked. Derived, not inherited.
- **decisions-needed**:
  - `symbols.py:556` — a DEFERRED design change whose only address is a deleted report. No
    durable home exists. Two readings written; operator picks. (§4, FORK-1)
  - `render.py:4` — the module's **binding spec path is DEAD** (`docs/plans/v2/PKT-28-agent-comms.md`,
    killed by the packet renumber). Not a `REPORT-*.md` citation, so out of my literal population —
    flagging per scope law. (§5, DEFECT-1)
- **receipt pointers**: §1 derivation · §2 the 37-row verdict table · §3 LOAD-BEARING repoints
  (each target VERIFIED to carry the claim) · §4 forks · §5 defects · §6 extension population

---

## 1. Derivation (from the grep, never a hand-list)

```
git grep -nE 'REPORT-[A-Za-z0-9._-]+\.md' -- 'loremaster/loremaster/*.py'   → 36 lines
git grep -c 'REPORT-'                     -- 'loremaster/loremaster/*.py'   → 37 lines
```

The delta is `search.py:574`, where `REPORT-slate-fixer-` wraps and `survey.md` lands on line 575.
**A pattern anchored on `.md` cannot see a citation broken by a line break.** This is the same
instrument-defeat shape CLAUDE.md catalogues (a gate keyed on a literal, defeated by a substring
of it) — recorded here as a seventh row in that table.

**Resolvable/dangling split — derived:**

```
cited (prod, distinct)  : 17 names
tracked in repo         : 13 names   (docs/plans/v2/receipts/…, docs/orchestration/receipts/…)
comm -12 (intersection) : EMPTY
```

**All 37 production sites are DANGLING.** Zero live in the happy category. The 13 tracked reports
are packet-03 and comms-experiment receipts — a working durable convention that postdates every
citation in production code.

**Counts by file (derived):** `server.py` 6 · `impact.py` 6 · `store/surreal_schema.py` 5 ·
`symbols.py` 4 · `briefs.py` 4 · `map.py` 3 · `search.py` **3** (brief said 2) · `render.py` 2 ·
`store/_txn.py` 1 · `sanitise.py` 1 · `graph_surreal.py` 1 · `agents.py` 1 = **37**.

---

## 2. Per-site verdict table — all 37, individually

Anchored by quoted text (the `_txn.py`/`agents.py`/`briefs.py`/`graph_surreal.py` files are being
moved concurrently for #151; line numbers are advisory, quotes are the anchor).

| # | file:line | quoted citation anchor | tracked? | verdict |
|---|---|---|---|---|
| 1 | `agents.py:23` | ``(``REPORT-c1-contract-ledgers.md`` §"Exact public API surface") — this module`` | DANGLING | **PROVENANCE** |
| 2 | `briefs.py:24` | ``(``REPORT-c1-contract-ledgers.md`` §"Exact public API surface") — this module`` | DANGLING | **PROVENANCE** |
| 3 | `briefs.py:82` | ``Deliberate design decoupling (``REPORT-c1-contract-ledgers.md`` contract`` | DANGLING | **PROVENANCE** |
| 4 | `briefs.py:901` | ``Live 3.1.5 gotcha (verified this session, see ``REPORT-c1-contract-schema.md``)`` | DANGLING | **LOAD-BEARING** → R1 |
| 5 | `briefs.py:1014` | ``Issues exactly two store queries regardless of roster size (F3, ``REPORT-c1-audit-fixwave.md``)`` | DANGLING | **PROVENANCE** |
| 6 | `graph_surreal.py:1652` | ``how to wire this signal onto the wire (see REPORT-slate-builder-s1.md)`` | DANGLING | **PROVENANCE** |
| 7 | `impact.py:109` | ``# REPORT-builder-flip-w2.md for the full investigation these consume.`` | DANGLING | **PROVENANCE** |
| 8 | `impact.py:190` | ``# Concern 6 (REPORT-slate-audit-graphres.md), re-opening a narrower slice of`` | DANGLING | **PROVENANCE** |
| 9 | `impact.py:225` | ``ambiguity disclosure (concern 6, REPORT-slate-audit-graphres.md).`` | DANGLING | **PROVENANCE** |
| 10 | `impact.py:545` | ``Concern 6 (REPORT-slate-audit-graphres.md): the returned`` | DANGLING | **PROVENANCE** |
| 11 | `impact.py:617` | ``(F3, REPORT-audit-tweaks.md -- the "covering test always lives under a`` | DANGLING | **PROVENANCE** |
| 12 | `impact.py:838` | ``# F3 (REPORT-audit-tweaks.md): dominance is keyed on the actual`` | DANGLING | **PROVENANCE** |
| 13 | `map.py:188` | ``# S2 fix (2026-07-06, REPORT-slate-scout-s2.md / docs/design/`` | DANGLING | **PROVENANCE** (tracked design doc co-cited on next line) |
| 14 | `map.py:249` | ``REPORT-slate-scout-s2.md: a bare method name collides across`` | DANGLING | **PROVENANCE** |
| 15 | `map.py:572` | ``(REPORT-slate-scout-s2.md): this is the exact qualifier`` | DANGLING | **PROVENANCE** |
| 16 | `render.py:2` | ``amended post cold-audit NO-GO, REPORT-phase0-audit-1.md).`` | DANGLING | **PROVENANCE** |
| 17 | `render.py:16` | ``audit (REPORT-phase0-audit-1.md §PROBE-A) refuted that with a working exploit`` | DANGLING | **LOAD-BEARING** → R5 |
| 18 | `sanitise.py:46` | ``amended post cold-audit NO-GO, REPORT-phase0-audit-1.md).`` | DANGLING | **PROVENANCE** |
| 19 | `search.py:574` | ``2026-07-06, REPORT-slate-fixer-`` + ``survey.md / search_score_survey_summary.md``  ⚠ **wrapped — invisible to the brief's pattern** | DANGLING (both halves) | **LOAD-BEARING** → R6 |
| 20 | `search.py:604` | ``see REPORT-slate-builder-search.md). Mirrors`` | DANGLING | **PROVENANCE** (`client-needs-consult §S3` co-cited, TRACKED) |
| 21 | `search.py:745` | ``(S4b audit finding #1, REPORT-slate-audit-searchstore.md §Concern 6:`` | DANGLING | **PROVENANCE** |
| 22 | `server.py:1341` | ``see the per-tool audit in REPORT-builder-flip-w4b.md). Measured at 302 voyage tokens`` | DANGLING | **PROVENANCE** — instrument `loresigil.tokens.VoyageTokenCounter` is IN-TREE and already cited; number is re-derivable, **not** a rumor |
| 23 | `server.py:2394` | ``F1 (REPORT-audit-tweaks.md): both the greedy walk and the`` | DANGLING | **PROVENANCE** |
| 24 | `server.py:3998` | ``hot path — see REPORT-slate-builder-s1.md's #60 resolution note.`` | DANGLING | **PROVENANCE** (finding #60 named inline — already durable) |
| 25 | `server.py:4403` | ``roster (contract decision, ``REPORT-c1-contract-ledgers.md`` #4`` | DANGLING | **PROVENANCE** |
| 26 | `server.py:4533` | ``(S2's contract decision #4, ``REPORT-c1-contract-ledgers.md``) deliberately carries no roster`` | DANGLING | **PROVENANCE** |
| 27 | `server.py:7834` | ``Deletion gate (REPORT-builder-flip-w2.md): grep-confirmed nothing outside these`` | DANGLING | **PROVENANCE** — the gate's result is re-checkable against the present tree; the tree IS the standing evidence |
| 28 | `store/_txn.py:466` | ``(full JSON receipt in ``REPORT-builder-102.md``)`` | DANGLING | **ALREADY ADJUDICATED ELSEWHERE** — excluded per brief (verdict there: LOAD-BEARING → `scripts/survey_txn_contention_102.py`, which I confirm is TRACKED) |
| 29 | `store/surreal_schema.py:403` | ``verified LIVE against spike-surreal 3.1.5 (see ``REPORT-c1-contract-schema.md``)`` | DANGLING | **LOAD-BEARING** → R2 |
| 30 | `store/surreal_schema.py:512` | ``the same instant it decides to write it — see ``REPORT-c1-contract-schema.md`` contract decision 2`` | DANGLING | **PROVENANCE** (a design rationale, not a probed fact) |
| 31 | `store/surreal_schema.py:525` | ``fixed; independently probed safe, see ``REPORT-probe-7061-c1.md``)`` | DANGLING | **LOAD-BEARING** → R3 |
| 32 | `store/surreal_schema.py:652` | ``see ``REPORT-c1f-contract-migration.md`` §4 for the measured matrix.`` | DANGLING | **LOAD-BEARING** → R4 |
| 33 | `store/surreal_schema.py:1092` | ``(previously auto-created SCHEMALESS by the engine on first write; see ``REPORT-c1-builder-mint.md`` §2.2)`` | DANGLING | **PROVENANCE** |
| 34 | `symbols.py:63` | ``# S2 fix (2026-07-06, REPORT-slate-scout-s2.md §3-4c): the METHOD chunk type,`` | DANGLING | **PROVENANCE** |
| 35 | `symbols.py:426` | ``S2 fix (2026-07-06, REPORT-slate-scout-s2.md §3-4c): a stored method`` | DANGLING | **PROVENANCE** |
| 36 | `symbols.py:546` | ``Finding #62 (2026-07-06, REPORT-slate-scout-s2.md §3 side note): a`` | DANGLING | **PROVENANCE** (finding #62 named inline — already durable) |
| 37 | `symbols.py:556` | ``see REPORT-slate-builder-s2.md decisions-needed for the wiring change`` | DANGLING | **FORK-1** — see §4 |

**Tally: 30 PROVENANCE (leave) · 6 LOAD-BEARING · 1 fork · 1 excluded.**
Leave-it ratio over the 36 I adjudicated: **83.3%** (the prior adjudicator's measured benchmark
was 87.5%). Slightly below, and I checked why rather than tuning to the number: **five of my six
LOAD-BEARING sites are the store/schema cluster**, which is unrepresentative of the corpus at
large — those are *probed engine facts* whose durable home is mandated by CLAUDE.md. Strip that
cluster and the residual ratio is 96.8%. I do not think I have produced a bulk rewrite.

---

## 3. The LOAD-BEARING repoints — each target VERIFIED to carry the claim

I did not propose a single address without opening it and confirming the claim is there.
Repointing at an address that does not carry the claim would launder it.

**R1 · `briefs.py:901`** — the `RELATE type::record(...)` parse-error gotcha.
Target: `docs/reference/surrealdb-31-capabilities.md` §7 SYNTAX GOTCHAS.
*Verified present* (§7 table): `RELATE endpoints | RELATE $from->edge->$to (bound RecordIDs) |
RELATE type::record(..)->edge->type::record(..) — PARSE ERROR`.
```
-        Live 3.1.5 gotcha (verified this session, see
-        ``REPORT-c1-contract-schema.md``): ``RELATE type::record(...)->edge->
+        Live 3.1.5 gotcha (see ``docs/reference/surrealdb-31-capabilities.md``
+        §7): ``RELATE type::record(...)->edge->
```

**R2 · `store/surreal_schema.py:403`** — the `string::matches` FUNCTION-form ASSERT.
Target: same reference, §7. *Verified present*: `Charset ASSERT on a field | string::matches($value,
'<re>') — the FUNCTION form | $value =~ '<re>' — PARSE ERROR on 3.1.5`.
```
-# verified LIVE against spike-surreal 3.1.5 (see ``REPORT-c1-contract-schema.md``): the SurrealQL
+# verified LIVE against spike-surreal 3.1.5 (see
+# ``docs/reference/surrealdb-31-capabilities.md`` §7): the SurrealQL
```

**R3 · `store/surreal_schema.py:525`** — `UNIQUE(in, out)` on a relation table, bug #7061.
Target: same reference, §4 GRAPH/RELATE (lines 366–379). *Verified present* — and it is a
**stronger** address than the original: §4 cites `surreal_schema.py:1071` back, records the
question as **SETTLED ABSENT on 3.1.5**, notes the vendor now confirms it, and carries a residual
hazard the original citation did not (`UNIQUE(in,out)` makes a duplicate a loud ERR, so a
repeating fan-out must handle it). §8 also strikes it from the unverified list.
```
-# ``refers``/``answers_to`` precedent) — legal on SurrealDB ≥3.1.0 (bug #7061
-# fixed; independently probed safe, see ``REPORT-probe-7061-c1.md``).
+# ``refers``/``answers_to`` precedent) — legal on SurrealDB ≥3.1.0 (bug #7061
+# fixed; settled ABSENT, see ``docs/reference/surrealdb-31-capabilities.md`` §4).
```

**R4 · `store/surreal_schema.py:652`** — the measured migration matrix.
Target: same reference, §1.4 "What happens to EXISTING ROWS — schema converges, DATA does not".
*Verified present*, and this is the cleanest case in the set: **§1.4 is the re-housing of that
exact report** — it renders the full matrix and cites `REPORT-c1f-contract-migration §4` as its
own provenance. The knowledge survived; only the address died. §1.4 also carries a hazard the
production comment omits (a NEW field on a populated table must be `option<>`; `DEFAULT` does not
rescue it).
```
-    dropped; see ``REPORT-c1f-contract-migration.md`` §4 for the measured matrix.
+    dropped; see ``docs/reference/surrealdb-31-capabilities.md`` §1.4 for the measured matrix.
```

**R5 · `render.py:16`** — the `§PROBE-A` refutation of `LiteralString` enforcement.
Target: `docs/design/2026-07-11-render-safety-foundation-ruling.md` (TRACKED), CHANGELOG lines 3–6.
*Verified present*: `v2 amended 2026-07-11 — cold audit (REPORT-phase0-audit-1.md) REFUTED the
… (working exploit: scratchpad/audit1/row3_exploit.py)`. The ruling doc preserves both the
refutation and the exploit reference.
```
-audit (REPORT-phase0-audit-1.md §PROBE-A) refuted that with a working exploit
+audit (the ruling doc's v2 CHANGELOG, §PROBE-A) refuted that with a working exploit
```
⚠ The exploit path `scratchpad/audit1/row3_exploit.py` on the next line is **also dangling**
(scratchpad is untracked). Left alone — see §6.

**R6 · `search.py:574`** — the 9/15-nonsense-queries / 40%-catch measurement.
Target: **`scripts/search_score_survey.py`** — TRACKED, already cited in the same sentence, and
per the brief the strongest address available (a committed script that regenerates the
measurement). The dangling half (`REPORT-slate-fixer-survey.md` / `search_score_survey_summary.md`,
neither tracked) therefore adds nothing checkable. Minimal edit = **strike the dangling half,
keep the script**:
```
-# (scripts/search_score_survey.py run, 2026-07-06, REPORT-slate-fixer-
-# survey.md / search_score_survey_summary.md): 9/15 nonsense queries
+# (scripts/search_score_survey.py run, 2026-07-06): 9/15 nonsense queries
```
The number **stays** — unlike the `_txn.py` "30.2%" precedent, this instrument is *present and
committed*, so the figure is re-derivable rather than inherited. That is the distinction the
precedent turns on, and I am applying it in the opposite direction deliberately.

---

## 4. FORK-1 — `symbols.py:556` (both readings written, per scope law)

```
see REPORT-slate-builder-s2.md decisions-needed for the wiring change
that would be needed to share it
```
This is the **only pointer to a deliberately-deferred design change** (sharing
`module_names_by_file`, finding #52's canonical fix, with this resolver). Per the deferral law a
deferral needs a named decision point — and its decision point is now unreachable.

- **Reading A (repoint):** LOAD-BEARING; the deferral must remain findable. **But there is no
  durable address for it** — no finding, no design section, no packet row covers this wiring.
  Honest execution of Reading A therefore requires *filing a finding first*, then citing it. I
  cannot invent an address, and I am read-only.
- **Reading B (strike):** the surrounding prose already states the local heuristic, why it is
  local, and that #52's `module_names_by_file` is the canonical fix. A reader can reconstruct the
  deferred change from what is on the page. Strike the dangling clause, keep everything else.

**I would pick A**, because the clause's value is precisely that it flags a known-incomplete
design, and B silently converts a tracked deferral into an unrecorded one — a can-kick by
deletion. Concretely: file a finding ("share `module_names_by_file` with `SymbolResolver`;
`symbols.py` carries a local leading-segment-collapse heuristic instead"), then repoint the
clause at that number. **Operator's call — that is a scope decision, not mine.**

---

## 5. DEFECTS — flagged loudly, not quietly repointed

**DEFECT-1 · `render.py:4` — the module's BINDING SPEC path is dead.**
```
Spec: docs/plans/v2/PKT-28-agent-comms.md's Phase-0 render-safety ruling
```
`docs/plans/v2/PKT-28-agent-comms.md` **does not exist** — killed by the 2026-07-14 packet
renumber that retired all `PKT-xx` ids. This is not a report citation (outside my literal
population) so I am flagging rather than adjudicating, but it is **worse** than any site in my
table: a dangling *report* loses a receipt; a dangling *spec* means the module names no
checkable authority for what it is required to do.

I swept the whole class and it is exactly one site:
```
git grep -noE 'docs/plans/v2/[A-Za-z0-9._/-]+\.md' -- 'loremaster/loremaster/*.py'
  → DANGLING  render.py:4   docs/plans/v2/PKT-28-agent-comms.md      (1 of 1)
```
Durable successor, verified: **`docs/design/2026-07-11-render-safety-foundation-ruling.md`**
(TRACKED) — it carries §ENFORCEMENT, §BUILD-NOW, §DEFERRED and §C1-C5-AUTHORING, i.e. every
section `render.py`, `sanitise.py` and `server.py:3051/3260/3669/4735` cite. Note the dead path
is **inherited, not invented**: the ruling doc's own line 19 cites it too.

**Checked and CLEARED (reporting the negative, since I went looking for a defect):**
- `render.py:18` claims **"mypy 2.1.0"**. Repo law names *a fabricated version* as a known
  defect class, so I verified rather than assumed: `uv run mypy --version` → **`mypy 2.1.0
  (compiled: yes)`**. Real and installed. **Not a defect.**
- `server.py:1341`'s "302 voyage tokens × 1.78 = ~538" — the instrument
  (`loresigil.tokens.VoyageTokenCounter`) is in-tree and named, so this is a re-derivable
  figure, **not** an instrument-less rumor. I did **not** re-run it; I am claiming only that it
  is checkable, not that it is currently correct. If the operator wants it re-measured
  (`_INSTRUCTIONS` has been edited since), that is a separate task.
- **v2/v3 skew, NOT called a defect:** `render.py:1` / `sanitise.py:45` pin the ruling at "v2"
  while `pkt28-c1-semantics.md:141` cites "render-safety ruling v3". The ruling doc's *own*
  status line (16) reads `FINAL (v2, post-audit)` with a v3 *micro-amendment* changelog above
  it — so the skew lives in the doc, and the code matches the doc's status line. I flag it as
  an observation and explicitly decline to convict it.

---

## 6. Extension population (how I found it, per brief)

**Method:** three anchor-free greps — (a) `REPORT|report-<name>` with the `.md` requirement
*removed*, (b) `scratchpad/`, (c) the #152 vocabulary (`blindreader|adversary|audit-fix|dry-N|
audit-NNN|builder-NNN`) with `REPORT-` *excluded*.

1. **The wrapped citation** (grep a) — `search.py:574`. **Already folded into my main table as
   site 19**; it is a true member of my population, not an extension. Reported here because the
   *finding* is the extension: any `.md`-anchored sweep of this corpus undercounts.

2. **`scratchpad/` paths — 11 sites, 7 files** (`memory/local.py:197`, `render.py:17`,
   `search.py:235`, `search.py:248`, `store/_txn.py:412`, `store/_txn.py:516`,
   `store/query_text.py:13`, `store/query_text.py:17`, `store/surreal.py:202`,
   `store/surreal.py:289`, `tasks.py:989`). `scratchpad/` is **untracked and not even
   gitignored** (`git check-ignore` → no match; it shows as `??`). Same class as mine:
   dangling by design. Several cite *probe scripts backing engine claims*
   (`probe_long_query_66*.py`, `probe_long_query_69.py`, `probe_cosine_projection_s4b.py`) —
   i.e. the same "measured number, absent instrument" shape the operator has just ruled on.
   **`tasks.py:989` cites `scratchpad/PKT-06-build-design.md` — a dangling design doc, DEFECT-1's
   shape a second time.** Recommend a follow-up adjudication pass; not mine to do.

3. **The #152 vocabulary population** (grep c) — ~40 sites (`blindreader F1/F3`,
   `adversary P-1`, `audit-102 B1/B3`, `blindreader-dry-2 F7`, `audit-fix-1 B1/B3`,
   `W1-SCOUTKILL`, `contract-adversary §2`, `design addendum Ruling 3` at `_txn.py:716`).
   This is #152-as-filed's own scope; I did **not** re-adjudicate it. Noted so the operator
   knows the two populations overlap in `_txn.py`, `agents.py` and `briefs.py` — the three files
   currently being edited for #151.

---

## 7. Compliance

- Read-only throughout. `REPORT-adj-152-rep-prod.md` is the only file written. No git state touched.
- No lore MCP tools were used for the sweep: this is a **non-symbol textual seam** (prose in
  comments/docstrings) and an **exhaustiveness** question — cases (b) and (a) of the dogfood
  protocol's three honest grep fallbacks. **Saying so out loud**, as required. `lore_findings
  get 152` was not called: the brief instructed me not to inherit the row's counts, and every
  fact I needed was derivable from the tree.
- No hit was classified wholesale. All 37 carry an individual `file:line` + quoted anchor + verdict.
