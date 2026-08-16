# REPORT-sweep-59 — packages / ONE-IMPLEMENTATION doctrine consistency sweep

brief-base v14 read
brief project v7 read

**Model attestation:** `claude-opus-4-8` (opus48-worker pin) — receipt: env
`CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8` (read live this run, not inherited from brief text).

**CAPABILITY CHECK (brief-base §4).** Mission is a report-only doc-consistency sweep across 7
standing-law files. I have Read (all 7 files readable), the lore MCP tools (loaded via
`ToolSearch "+lore"`), lore_comms/lore_tasks (registered + task claimed→in_progress), and Write
to `REPORT-sweep-59.md`. No code execution, no store, no deploy needed. **No capability gap — the
brief is fully satisfiable.** One brief pointer inaccuracy surfaced (see O1) — it did not block.

---

## SUMMARY BLOCK

- **State:** done.
- **Deviations:** (1) the `lorerunes` section the brief located in `~/.claude/CLAUDE.md` is
  actually in the **lore project** `CLAUDE.md:461` — I reviewed it there (O1). (2) The global
  ONE-IMPLEMENTATION doctrine text lives in `~/.claude/CLAUDE.md`; its lore-specific twin +
  lorerunes live in the lore repo `CLAUDE.md` — both reviewed.
- **Packages considered:** none — no mechanism specified (this is a doc-audit, not a build).
- **Reuse ledger:** none — introduced no reusable symbol (report-only).
- **Graded:** subject is 7 static law files read at 2026-08-15. In-repo file = lore
  `CLAUDE.md` (last touched `83dba44`, unchanged at HEAD) · HEAD-at-report:
  `faa68b2` · SAME. The other 6 files are under `~/.claude/` which is **not a git work tree**
  (verified) — no sha applies; cited by heading anchor + line, dated 2026-08-15.
- **Findings:** 2 CONTRADICTIONS · 3 INCONSISTENCIES · 2 GAPS · 4 observations · staleness: clean.
- **Decisions-needed (operator):** whether to unify the package-survey verdict vocabulary
  (C1 — the highest-value, mechanically-consequential fix); the rest are surgical text edits with
  exact replacements below.
- **Receipt pointers:** contradictions → §CONTRADICTIONS; inconsistencies → §INCONSISTENCIES;
  gaps → §GAPS; scope-honesty → §OBSERVATIONS; per-finding exact edits → §DETAIL.

---

## Files reviewed (exact anchors)

| # | file | doctrine surface reviewed |
|---|---|---|
| 1a | `~/.claude/CLAUDE.md` | §"Packages over hand-rolling — the two-sided rule" (L180) · §"ONE IMPLEMENTATION — the in-house half" (L221–258) |
| 1b | lore repo `CLAUDE.md` | §"ONE IMPLEMENTATION — a pattern to clone is a defect" (L425) · §"`lorerunes` — THE HOME FOR SHARED CODE" (L461) |
| 2 | `~/.claude/orchestration/brief-base.md` | §1 `Packages considered:` line (L67–87) · §6 One implementation / DRY (L274–319) |
| 3 | `~/.claude/agents/package-scout.md` | whole file; disposition discipline (L64–74), report (L126–144) |
| 4 | `~/.claude/agents/tdd-contract.md` | PACKAGE SURVEY clause (L50–100) |
| 5 | `~/.claude/agents/contract-adversary.md` | P-PKG probe (L69–92) |
| 6 | `~/.claude/orchestration/lead-base.md` | reuse-artifact check-before-commit (L25–27) |
| 7 | `~/.claude/agents/odoo-reuse-scout.md` | whole file; verdict vocabulary (L69–81) |

The verdict/disposition vocabulary each file mandates, side by side (the spine of C1 & G1):

| file | closed verdict set it uses |
|---|---|
| brief-base §1 | `replace` · `replace_with_adapter` · `keep_with_trigger` · `bespoke` |
| tdd-contract PACKAGE SURVEY | `replace` · `replace_with_adapter` · `keep_with_trigger` · `bespoke` |
| contract-adversary P-PKG | `replace` · `keep_with_trigger` · `bespoke` (same set, used inline) |
| lead-base check | keys on the token `bespoke` |
| **package-scout** | **`REPLACE` · `REPLACE-WITH-ADAPTER` · `KEEP + RE-OPEN TRIGGER` · `GENUINELY BESPOKE`** |
| DRY ledger (brief-base §6, internal axis) | `REUSED <sym>` · `HAND-ROLLED` (no `EXTENDED`) |
| odoo-reuse-scout (internal axis) | `reuse <X>` · `extend <X>` · `new code justified` |

---

## CONTRADICTIONS  ⚠ worst class — two files prescribing different rules for the same situation

### C1 — Package-survey VERDICT VOCABULARY diverges at the delegation seam
**Class: contradiction (mechanically consequential).**

`brief-base §1` (L86–87) and `tdd-contract` (L93–100) both instruct an author to **delegate a
>~4-mechanism survey to `package-scout` and CITE ITS TABLE**. But `package-scout` emits a
**different verdict vocabulary** than every file that consumes it:

- package-scout: `REPLACE` / `REPLACE-WITH-ADAPTER` / `KEEP + RE-OPEN TRIGGER` / `GENUINELY BESPOKE`
- everyone else (brief-base §1, tdd-contract, contract-adversary, lead-base): `replace` /
  `replace_with_adapter` / `keep_with_trigger` / `bespoke`.

Why this is a real defect, not cosmetics:
1. The consumer must copy the scout's verdicts into its own `Packages considered:` line, which
   must use the snake_case closed set. The translation is **undocumented and lossy**:
   `GENUINELY BESPOKE → bespoke` survives a substring check by luck, but
   `KEEP + RE-OPEN TRIGGER` shares **no token** with `keep_with_trigger`.
2. `lead-base` (L27) does a **mechanical, token-keyed** check — *"a `bespoke` verdict with an
   EMPTY read-column."* A cited scout table that reads `KEEP + RE-OPEN TRIGGER` / `GENUINELY
   BESPOKE` is invisible to a grep for `keep_with_trigger` / `bespoke`. This is exactly the
   "enumerate the forbidden and lose to a spelling" class the global CLAUDE.md meta-lesson (L250)
   warns about — reproduced inside the packages doctrine itself.

**Recommended edit — `package-scout.md`, §"The disposition discipline" (L64–74).** Rename the
verdict TOKENS to the shared closed set; keep the glosses. Exact replacement:

> A found hand-roll is **not** automatically a defect. Every candidate gets exactly one verdict,
> **drawn from the SAME closed set the consumer's `Packages considered:` line, the tdd-contract
> PACKAGE SURVEY, and the lead's commit check use** — so a consumer can cite your table verbatim
> and the lead's mechanical check finds the token it expects:
>
> - **`replace`** — the library does the job. Name the swap's risk and **the control that would
>   prove it** (an equality/oracle test where one is possible).
> - **`replace_with_adapter`** — the library does the *hard* part; a small bespoke adapter covers
>   a genuine gap. Name the gap, size the adapter.
> - **`keep_with_trigger`** — a library exists, but churning proven, guarded code is the worse
>   trade. **This is a legitimate verdict, not a cop-out.** Name the re-open condition that flips it.
> - **`bespoke`** — nothing does this; it is domain logic. Say what you READ to conclude it.

(Also update the SUMMARY-BLOCK bullet at L134 — *"the ranked verdict table — candidate · library
(+version) · verdict · cost-if-wrong"* — to read *"verdict (closed set: replace ·
replace_with_adapter · keep_with_trigger · bespoke)"*.)

---

### C2 — "ESCALATE" carries OPPOSITE valence across files for the same situation
**Class: contradiction (reconcilable, but the wording actively collides).**

Situation: *two call sites / workspace members need the same shared POLICY.*

- `brief-base §6` (L294–296) and global `CLAUDE.md` ONE-IMPLEMENTATION (L245–247) prescribe the
  terminal action **"ESCALATE it — do not quietly write the second copy."** Escalation is the
  *correct move*.
- lore `CLAUDE.md` lorerunes (L479–481) prescribes **"it goes in `lorerunes` — not cloned, not
  'escalated' into a fork."** Here "escalate" names the *failure mode*.

A lore subagent has **both** in context simultaneously (both CLAUDE.md files + brief-base
auto-load). It reads *"ESCALATE it"* (the mandated action) next to *"not 'escalated' into a
fork"* (the forbidden action) — for the identical situation. Reconcilable by a careful reader
(escalate the *design decision*; its *resolution* is lorerunes), but nothing in either file says
so, and the bare word points two ways. brief-base §6, being project-agnostic, correctly cannot
name lorerunes — so the connective tissue is simply absent.

**Recommended edit A — `brief-base.md` §6 (L294–296).** Make "escalate" resolve to a home:

> - **You may not quietly write copy #2. Duplication is a DESIGN decision — ESCALATE it**
>   (report file first, then one message). If the existing thing *almost* fits, say so and
>   propose extending it; do not fork it. **Escalation resolves the design question of WHERE the
>   shared thing lives; where a project designates a shared home for cross-caller policy (its
>   CLAUDE.md names it), the answer is that home — never a second copy and never a fork in a new
>   place.**

**Recommended edit B — lore `CLAUDE.md` lorerunes first bullet (L479–481).** Name brief-base §6
as compatible:

> - **If two members need the same POLICY, it goes in `lorerunes`.** This IS the resolution of
>   brief-base §6's *"escalate, don't write copy #2"*: you escalate the design decision, and the
>   answer is `lorerunes` — not a clone, and not an "escalation" that quietly resolves into a
>   *fork* (a second copy in a new place is still copy #2). Policy = validation predicates, error
>   classification, retry/backoff budgets, sanitisation, normalisation, formatting rules.
>   Anything whose *rules must agree everywhere*.

---

## INCONSISTENCIES

### I1 — "doc section" blessed as a valid READ, but a doc-only read is rejected for a `bespoke` verdict
**Class: inconsistency (and it under-cuts the lore #107 law).**

- `brief-base §1` (L70): a valid read is *"an installed signature, source you opened, **a doc
  section** — never an expectation."*
- `tdd-contract` (L75): *"Cite the installed signature, the source you read, **or the doc
  section**."*
- `package-scout` (L138): *"installed signature, source file, **doc section** — cite it."*
- **`contract-adversary` P-PKG (L79–81): a `bespoke` verdict whose read-column *"cites a doc
  rather than an installed signature is a missing pin."*** i.e. a doc citation is explicitly
  **insufficient** to justify a "package can't do it" verdict.

The three author-side files bless a doc-only read for *any* verdict; the adversary rejects it for
the `bespoke`/limitation case. And the adversary is right by this repo's own law: lore
`CLAUDE.md` §"READ THE DEPENDENCY'S DOCS — THEN VERIFY THEM" (the #107 outage) — *"vendor prose…
CAN lie → treat a hit as a lead to VERIFY, never as final."* The author-side files are
under-strict relative to both the adversary and #107.

**Recommended edit — add the #107 caveat to all three author-side read-columns.** Minimal form,
applied to `brief-base §1` (L70) and mirrored verbatim into `tdd-contract` L75 and
`package-scout` L138:

> …what you **READ** to decide (an installed signature, source you opened, a doc section — never
> an expectation). **⚠ For a `bespoke` / "the package can't do this" verdict specifically, a doc
> citation ALONE is insufficient — vendor docs can be false (the #107 class). Read the installed
> signature or source, or probe live, before asserting a limitation.**

### I2 — the two ONE-IMPLEMENTATION doctrine copies have DRIFTED (the doctrine's own failure mode, live)
**Class: inconsistency (self-referential).**

The ONE-IMPLEMENTATION rule is stated **in full in two places** — global `CLAUDE.md` L221–258 and
lore `CLAUDE.md` L425–459 — rather than stated once and pointed-at. Per the doctrine's own rule
(*"duplicating policy is how a fix reaches one copy and not the other,"* L227–228), the copies have
**already diverged**:

- **`ROUTING IS NOT SHARING`** is in the lore copy (L449) and in brief-base §6 (L301) — but
  **absent from the global copy** (which ends at L258 on the allowlist-the-safe meta-lesson).
- The **allowlist-the-safe meta-lesson** (global L249–258) is **not** in the lore
  ONE-IMPLEMENTATION section (it lives separately in that file's "instrument lesson" table, L532).

So each copy carries a load-bearing clause the other lacks. An agent reading only the global
statement never learns routing-not-sharing — the single subtlest way DRY fails (a green gate over
a dead mechanism, measured in #102's own fix, lore `CLAUDE.md` L449–455).

**Recommended edit — add the routing-not-sharing bullet to global `CLAUDE.md` ONE-IMPLEMENTATION,
after L247** (the "Duplication is a DESIGN decision… escalate" bullet):

> - **ROUTING IS NOT SHARING.** A caller that calls the shared function but hand-rolls the
>   *decision* underneath it — its own error-classification, its own retry predicate — is a
>   private copy wearing the shared name, and it passes every gate that only checks the call site.
>   If you route to a shared seam, use its classification too. (Measured: eleven seams all routed
>   through one driver, each matching `"Resource busy"` locally — 839/0 green — and all silently
>   stopped retrying under a reworded engine message. lore #102/#120.)

(Optional structural fix, operator's call: make the lore copy OPEN with *"the cross-project
statement is the global CLAUDE.md ONE-IMPLEMENTATION; below are the lore #102 receipts + the
lorerunes resolution"* so the principle is stated once and the project file adds only receipts —
this is the doctrine applied to itself.)

### I3 — global "retries/backoff → `tenacity`" is a flat endorsement of a library with a measured semantic trap
**Class: inconsistency (minor).**

Global `CLAUDE.md` L218: *"retries/backoff → `tenacity`, not a hand-written loop."* But three
other files carry the measured gotcha that `tenacity` ships the **wrong jitter class** under a
plausible name: `wait_exponential_jitter` is EQUAL jitter, `wait_random_exponential` is full
jitter — *"a project had already rejected the former by name in its own tests"* (package-scout
L86–88, tdd-contract L87–89, contract-adversary L83–84). The flat endorsement contradicts the
doctrine's own "check the CLASS, not just the name" instrument.

**Recommended edit — global `CLAUDE.md` L217–218**, append a parenthetical:

> …retries/backoff → `tenacity`, not a hand-written loop **(but check the jitter CLASS, not the
> name: `wait_random_exponential` is full jitter; `wait_exponential_jitter` is equal jitter, which
> a lore project rejects by name)**;

---

## GAPS  (the doctrine implies it; no file states it)

### G1 — the internal DRY-ledger axis has no `EXTENDED` disposition (the twin of `replace_with_adapter`)
**Class: gap.**

The EXTERNAL package axis has a three-way middle: `replace` / **`replace_with_adapter`** /
`bespoke`. The INTERNAL reuse axis (DRY ledger, brief-base §6 L281) offers only **`REUSED` /
`HAND-ROLLED`** — no middle for *"the existing helper almost fit, I widened it."* Yet brief-base
§6 itself (L295–296) recognises that path in prose (*"If the existing thing almost fits… propose
extending it; do not fork it"*), and `odoo-reuse-scout` emits exactly that verdict (`extend <X>`,
L80) with **no clean DRY-ledger disposition to map it to**. So an agent who extends a helper must
mis-file it as either REUSED (untrue — code changed) or HAND-ROLLED (untrue — reused the base).

**Recommended edit — `brief-base.md` §6 (L281), the DRY-ledger disposition set:**

> …disposition being exactly **REUSED `<existing.symbol>`** (cited) · **EXTENDED
> `<existing.symbol>`** (the existing thing almost fit; you widened it in place rather than
> forking — cite it and say what you added) · **HAND-ROLLED** (with a concrete reason the
> candidate you found does not fit; *"nothing found"* is valid ONLY with the query that proves you
> searched).

(Consequential mirror: `lead-base` L26 DRY-LEDGER check already accepts "a dispositioned row" — it
needs no change, but the operator may want to note `EXTENDED` there too for symmetry with the
`Packages considered:` bullet.)

### G2 — "delete the hand-rolled twin (never maintain both)" is never operationalized for an acted-on `replace`
**Class: gap.**

The two-sided rule's worked example (global `CLAUDE.md` L208) mandates, when a package REPLACES a
hand-roll: *"**delete the hand-rolled twin** (never maintain both)."* But neither `brief-base §1`
nor the `lead-base` commit check (L27) verifies it. A builder can add the package call, leave the
old hand-roll in the tree, disposition it `replace`, and pass every gate — shipping exactly the
"maintain both" state the rule forbids. No file closes this.

**Recommended edit — `lead-base.md`, the `Packages considered:` check bullet (L27), append a
third failure condition:**

> …or a missing dependency HAND-ROLLED around instead of ESCALATED for install authorization;
> **or a `replace` verdict acted on that LEFT the hand-rolled original in the tree — the two-sided
> rule is *delete the hand-rolled twin, never maintain both*; the report must show the deletion.**

---

## OBSERVATIONS  (scope-honesty flags — not doctrine defects, surfaced per brief-base §2)

- **O1 — brief pointer inaccuracy (heads-up, not a defect).** The brief lists the `lorerunes`
  section under file #1 `~/.claude/CLAUDE.md`. It is actually in the **lore project**
  `CLAUDE.md:461`. The **placement is correct** — lorerunes (loremaster/loresigil/lorescribe
  workspace members) is lore-specific and belongs in the project file, never the global one. No
  edit needed; flagged so the operator knows the doctrine is where it should be and the brief's
  file map was slightly off. Effectively I reviewed **8** file-regions across 7+1 files.

- **O2 — `package-scout` report format is bespoke** (its own SUMMARY BLOCK, L130–144; no
  reference to brief-base §1's receipt line or block). If it is ever spawned under the base
  protocol, its `Packages considered:` line is degenerate (a scout SPECIFIES no mechanism — its
  entire output IS a package survey). Low priority; note only if package-scout is folded into the
  standard spawn-brief protocol.

- **O3 — `odoo-reuse-scout` `extend <X>` verdict** (L80) has no DRY-ledger home — folded into G1.

- **O4 — the ONE-IMPLEMENTATION doctrine mildly violates its own "write it once" rule** by being
  stated in full in two CLAUDE.md files rather than principle-in-global + receipts-in-project.
  This is the *cause* of I2's drift, not a separate defect — resolved by I2's optional structural
  edit.

---

## STALENESS — clean bill (stated explicitly, honestly)

No retired name / tool / mechanism found in the packages-or-DRY doctrine sections of any of the 7
files. Specifics checked and current as of their cited dates:
- lore tool references (brief-base §6 "indexed code tool §4"; DRY-ledger "lore query run") — no
  retired `search_code`/`what_imports`/`tests_for` names; all generic or current.
- The `tools:`-key frontmatter notes on package-scout / tdd-contract / contract-adversary
  (2026-08-01, lore #292/#294/#298/#299) — current, and their re-open trigger (#299 server-name
  standardisation) is named.
- `odoo-reuse-scout` odoo-code MCP tool names — current; matches global `CLAUDE.md` L388 ("odoo is
  not yet on lore").
- lorerunes `./scripts/registration_sites.py` reference — current (derivation-over-list, matches
  the file's own instrument lesson).

---

## DETAIL — priority-ordered worklist for the operator

| # | file · anchor | class | one-line fix |
|---|---|---|---|
| **C1** | `package-scout.md` §disposition discipline L64–74 (+ L134) | **contradiction** | rename verdict tokens to the shared closed set `replace/replace_with_adapter/keep_with_trigger/bespoke` |
| **C2** | `brief-base.md` §6 L294–296 **and** lore `CLAUDE.md` lorerunes L479–481 | **contradiction** | reconcile "escalate" valence: escalation RESOLVES into the project's shared home (lorerunes), never a fork |
| **I1** | `brief-base.md` §1 L70; `tdd-contract.md` L75; `package-scout.md` L138 | inconsistency | a doc-only read is insufficient for a `bespoke` verdict — require installed signature/source/probe (#107 law) |
| **I2** | global `CLAUDE.md` ONE-IMPLEMENTATION after L247 | inconsistency | add the missing `ROUTING IS NOT SHARING` bullet (drifted out of the global copy) |
| **G1** | `brief-base.md` §6 L281 | gap | add `EXTENDED <sym>` disposition to the DRY ledger (internal twin of `replace_with_adapter`) |
| **G2** | `lead-base.md` L27 | gap | check that an acted-on `replace` DELETED the hand-rolled twin ("never maintain both") |
| **I3** | global `CLAUDE.md` L217–218 | inconsistency (minor) | add "check the jitter CLASS not the name" caveat to the flat `tenacity` endorsement |

Exact replacement text for every row is in the §CONTRADICTIONS / §INCONSISTENCIES / §GAPS bodies
above. All 7 files are global standing law — **report-only; no edits made** (writable set was
`REPORT-sweep-59.md` alone). The operator applies whichever edits it rules in.
