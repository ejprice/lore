# REPORT — instrument0 (INSTRUMENT 0: the contract-adversary REACH ATTACK + CLAUDE.md law line)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- **state:** done
- **Capability check:** brief fully satisfiable with my toolset (Read/Edit/Bash/lore_comms + lore deferred tools loaded). No impossible demands. No tests to run (INSTRUMENT 0 is prose/law by design — design doc §5: "not a code cycle").
- **deviations:** none.
- **Packages considered:** none — no mechanism specified (this is prose/law: an agent-definition probe and a CLAUDE.md law line; no library surface).
- **Graded:** N/A — this report renders no verdict on another artifact. Work done at HEAD `641f758` (`feat/surreal-unification`); the design doc I executed was speced against `74694dc`, an ancestor — no INSTRUMENT-0-relevant drift (the adversary agent + CLAUDE.md instrument-lesson section are unchanged between them).
- **decisions-needed:** ONE flag for the lead (below): `contract-adversary.md` is GLOBAL tooling — this change affects every project's TDD. Kept self-contained; confirm before treating as landed.
- **What I changed (2 files, additive only):**
  1. `~/.claude/agents/contract-adversary.md` — added probe **P1c — THE REACH ATTACK** (after P1b), a Verdict clause, and a Report SUMMARY-BLOCK line. **FOLLOW-UP (leg 5, lead-directed):** extended P1c with a fifth axis — routing-not-sharing / two-sources-of-truth / prove-by-mutation (#102/#120). See the "FOLLOW-UP" section at the bottom for the leg-5 diff.
  2. `CLAUDE.md` (repo) — added ONE askable-question law line to the "instrument lesson (six defeats, one shape)" section.
- **receipt POINTERS:** P1c probe → `contract-adversary.md:120` (now 5 legs); Verdict clause → `:283`; summary-block reach-table line → `:307`; CLAUDE.md law line → `CLAUDE.md:540` (in "The instrument lesson" §, after the six-defeats table). Full leg-5 diffs → "FOLLOW-UP" section below.

---

## ⚠ FLAG TO LEAD — global tooling change (as instructed)

`~/.claude/agents/contract-adversary.md` is the **reusable contract-adversary agent used by every project's TDD cycle**, not a lore-repo file. This wave adds a new mandatory probe to it. I kept the addition a **self-contained REACH ATTACK section** (probe P1c, its own Verdict requirement, its own summary-block line) so it reads as one coherent unit and does not entangle the existing probes. **This is a global change — surface it to the operator for confirmation before treating it as landed.** It is also not under git (`~/.claude` is not a repo), so there is no commit for the lead to make there; the lore-repo `CLAUDE.md` edit IS a normal tracked change the lead commits at the boundary.

---

## What INSTRUMENT 0 is, and why prose not code

From the design doc (`docs/plans/v2/design/2026-08-09-defect-class-prevention.md` §3, "INSTRUMENT 0 — SETTLED"): the class recurs because a builder/contract author writes a guard and never asks what it fails to run over — **and no pass in the pipeline asks them.** There is deliberately NO single meta-SCANNER (§3 grouping decision: "building one would be the seventh defeated instrument" — reach hides in structurally unrelated surfaces, so "find every hand-list" is not an AST-expressible property). The one thing that generalises the *class* rather than the eight instances is a **mandatory question installed into the pipeline stage whose whole job is "what would this contract wave through?"** — the `contract-adversary`. Per CLAUDE.md law ("A DIAGNOSIS IS NOT AN INSTRUMENT" + "THE LEVER: write laws as QUESTIONS"), the additions are phrased as **askable questions**, and the CLAUDE.md law line names its **mechanical home** (the adversary) so it is not merely a hope.

Acceptance frame honored (per brief, operator 2026-08-09): priority is (1) don't repeat past mistakes, (2) don't widen gaps, (3) trust/honesty to agents. P1c's four questions are exactly the four the brief names — SET / DERIVED-vs-hand-list / coverage-as-checked-variable / EFFECT-vs-proxy — and the probe states its own honest bound (a reasoning pass with empirical legs; can miss; belt-and-braces with the per-surface mechanical pins), which is the trust-doctrine self-check, not an over-claim.

---

## EXACT DIFFS

### File 1 — `~/.claude/agents/contract-adversary.md` (GLOBAL; not git-tracked)

**Edit 1a — new probe P1c, inserted immediately after P1b (the QUANTIFIER ATTACK), before P2.** P1c is a structural sibling of P1b: P1b produces a per-INVARIANT table (∀ vs guarded), P1c produces a per-INSTRUMENT table (reach DERIVED vs hand-list / coverage checked / effect vs proxy). Full inserted text:

```markdown
**P1c — THE REACH ATTACK: for every guard/gate/scan/probe/sweep the contract introduces or
relies on, is its REACH a CHECKED variable or a hidden constant?**
A guard certifies only the sites it actually EXECUTES over. When its reach — the SET of sites
it covers — is written as a name, a prefix, or a hand-list instead of DERIVED from a property
of production truth, the sites it misses are exempt *silently and forever*, and no gate can see
the gap because the gate IS the thing with the blind spot. (Provenance: eight instances of ONE
class, each hiding the reach in a different disguise — a hardcoded driver param that left a
free-text slot un-exercised; a name-prefix discovery whose self-audit keyed on the SAME prefix;
an omittable hand-list of "the gates"; a mutating-tool set hand-maintained beside the production
annotations it drifted from; a derivation written twice, free to disagree; a comparison baseline
with no anti-vacuity, so a baseline that measured NOTHING read as "everything passed"; a refusal
pin observing a proxy, so a guard placed AFTER the mutating body passed green; a malformed-input
matrix missing the trailing-newline case for a field it interpolates.) For EVERY guard / gate /
scan / sweep / fixture-population the contract introduces or leans on, answer these four, per
instrument:
1. **What is the SET of sites this guard is supposed to cover?** Name it — the fields, the tools,
   the call sites, the branches, the modules.
2. **Is that set DERIVED from a property of production truth** (AST shape, registered annotations,
   function identity, the canonical manifest) — **or is it a name / prefix / hand-list?** A
   hand-list and a derived set are both just Python; the difference is whether a NEW site joins
   the set without anyone editing the guard.
3. **Is COVERAGE a CHECKED variable** — is there a pin that goes RED when the derived set GROWS
   but the observed set does not? `observed == derived`, failing CLOSED on empty (a scan that
   reaches zero sites is broken, not clean), with the safe exclusions ALLOWLISTED by
   evidence-backed reason + a re-open trigger — never denied by a forbidden-list.
4. **Does it observe the EFFECT or a PROXY?** Would this pin still pass if the guard ran AFTER the
   thing it guards (a mutating body that runs, THEN refuses — byte-identical at every proxy
   observation point), or against a baseline that measured nothing?

Empirical wherever the guard is in-tree, not an essay — the oracle exists at your phase, so build
the wrong version in scratch: ADD a site to the derived population and show the coverage pin
reddens (a pin that stays green is a hand-list wearing a derived name — a **BLOCKER**); MOVE the
guard AFTER the body it guards and show the pin still passes (proxy observation — a **BLOCKER**);
collect zero into the baseline and show the comparison still reads success (missing anti-vacuity —
a **BLOCKER**). Pair every negative with a positive control (P0). Your output is a **PER-INSTRUMENT
TABLE**: each guard classified DERIVED + coverage-checked + effect-observed (safe), or, on any of
the three, a MISSING PIN with its reproduction — reported exactly like the P1b quantifier misses.
Honest bound, stated not glossed: this is a reasoning pass with EMPIRICAL LEGS where the guard
exists in-tree. A guard the contract INTRODUCES gets the wrong-build treatment; one it merely
RELIES on gets the four questions answered by construction-inspection. A reasoning pass can miss —
which is why the classes it guards also carry their own mechanical invariants (belt and braces).
**Say which legs you ran.** The author's own copy, to run before you see it: *"What is the set of
sites this guard covers, where is that set DERIVED, and does a test FAIL when the derived set grows
but the observed set does not? — and would this pin still read as success if the guard ran AFTER
the thing it guards, or against a baseline that measured nothing?"*
```

**Edit 1b — new Verdict clause, inserted between the P1b-quantifier-table requirement and the P-PKG-diff requirement.** Full inserted text:

```markdown
- **SUFFICIENT also requires the P1c reach table.** A verdict that has not classified every
  guard / gate / scan the contract introduces or relies on (reach DERIVED vs hand-list, coverage
  a checked variable vs not, effect vs proxy), with a reproduction on every MISSING-PIN row, is
  treated as INSUFFICIENT — same rule as the receipt-free SUFFICIENT above. A contract that stands
  up a guard whose reach is a hidden constant ships a blind spot the builder cannot see and the
  cold audit checks the code against, not the contract behind it.
```

**Edit 1c — new Report SUMMARY-BLOCK line, inserted after the QUANTIFIER TABLE line, before the MISSING PINS line.** Full inserted text:

```markdown
- the **REACH TABLE** (P1c): every guard/scan classified reach-DERIVED vs hand-list,
  coverage-checked vs not, effect vs proxy — every MISSING-PIN row with its reproduction,
  and which legs were empirical vs construction-inspection
```

### File 2 — `CLAUDE.md` (repo, git-tracked — lead commits)

**Edit 2 — ONE askable-question law line added to the "instrument lesson (six defeats, one shape)" section**, immediately after the closing paragraph of that section (the `6.2%–34.4%` paragraph), before the `## Every artifact gets an adversary` heading. `git diff` output:

```diff
@@ -537,6 +537,21 @@
 runs, 16-way; a range, not a point — audit-fix-1 A4 / blindreader-dry-2 F4 caught this section's
 own earlier "13%" as a fourth, unreproducible value alongside two production comments' "16.2%").

+**THE ASKABLE FORM, so this lesson installs itself instead of being re-learned a seventh time
+(INSTRUMENT 0, lore #344/#345, 2026-08-09).** All six defeats are ONE class — *a guard certifies
+only the sites it EXECUTES over, and its reach is written as a hidden constant instead of a
+checked variable.* Before shipping ANY guard / gate / scan / sweep, ask it of your own instrument:
+***"What is the SET of sites this guard covers, is that set DERIVED from production truth or a
+name/prefix/hand-list, and does a test go RED when the derived set GROWS but the observed set does
+not? — and would this pin still read as success if the guard ran AFTER the thing it guards, or
+against a baseline that measured nothing?"*** A reach that is a hidden constant is the seventh
+defeat waiting to happen. This is a QUESTION, not a property to remember (per THE LEVER), and it
+has a MECHANICAL home so it is not only a hope: the **`contract-adversary` now forces it
+per-instrument (its REACH ATTACK, P1c)** — a contract that stands up a guard whose reach is a
+hand-list, or whose coverage is not a checked variable, or that observes a proxy, cannot pass the
+adversary, so instance #9 of the class is caught at CONTRACT time rather than by the next agent
+who trips over it.
+
 ## Every artifact gets an adversary — not just the code (PKT-28 C1, 2026-07-12)
```

---

## Design-fidelity notes (what I preserved from the spec, and the two small judgments I made)

- **Faithful to design doc §3 INSTRUMENT 0:** the four questions are verbatim the doc's `(1)…(4)` (SET / DERIVED-vs-name-prefix-hand-list / coverage-as-checked-variable / EFFECT-vs-PROXY). The doc's "reported exactly like the existing quantifier-attack misses" is preserved literally in both P1c and the Verdict clause.
- **Placement judgment (P1c after P1b):** the doc did not mandate a probe id or position. I chose `P1c`, adjacent to P1b, because the two are structural twins (per-invariant table vs per-instrument table) and both are load-bearing on the SUFFICIENT verdict — a reader who understands P1b's discipline reads P1c as the same discipline aimed at the contract's own guards. This is a naming/ordering choice, not a semantic one; nothing in the doc it contradicts.
- **Empirical-legs framing (my addition within the doc's intent):** the doc says INSTRUMENT 0 "IS answerable by a reasoning pass with a checklist, which is exactly what the adversary is" and calls the honest boundary explicitly. I extended this with concrete empirical legs (add-a-site / move-the-guard-after / zero-baseline) because the adversary's entire ethos is "build it wrong and see what passes" (P1), and those three legs are the wrong-builds that correspond to the doc's own three failure shapes (#345 coverage, #295 proxy, #290 baseline). I kept the doc's honesty bound intact ("a reasoning pass can miss… belt and braces") and added "say which legs you ran" so a SUFFICIENT verdict can't silently claim empirical rigor it didn't perform — the trust-doctrine self-check applied to the adversary itself.
- **CLAUDE.md law line is a QUESTION with a mechanical home (per THE LEVER + "A DIAGNOSIS IS NOT AN INSTRUMENT"):** the line is phrased as the exact question an author asks itself, and it explicitly names the `contract-adversary` REACH ATTACK as where the rule is mechanically forced — closing the "we wrote the law and skipped the instrument" failure mode the section above it warns against.

## What this does NOT claim (trust-doctrine self-check)
- INSTRUMENT 0 is a **reasoning pass** — it can miss; that is stated in P1c itself and is why the design's eight per-surface instances also get their own mechanical pins (belt and braces, operator's packet-01 ruling). I did not dress it up as a scanner.
- I did not touch, reorder, or reword any existing probe (P-PKG/P1/P1b/P2/P3/P4/P5/P6/P6b/P7/P0) or any other CLAUDE.md section — additive only, per brief.
- No tests were written or run (none owed for this instrument). No git state mutated.

---

## FOLLOW-UP — leg 5 (routing-not-sharing / two-sources-of-truth / prove-by-mutation) — lead-directed, operator-confirmed 2026-08-09

The DRY review (design doc §7, now the operator's #1 priority) forces a FIFTH axis on the P1c REACH ATTACK: an instrument can DERIVE its site-set correctly, check coverage, and observe the effect — and STILL leave two sources of truth for one policy (routing-not-sharing, #102/#120), a class no gate that only checks the call site can see. **All edits `~/.claude/agents/contract-adversary.md`, additive-only. `CLAUDE.md` was NOT touched by this follow-up.** Kept operator-confirmed decision: P1c stays GLOBAL.

**5a — new numbered leg (5), inserted after leg 4, and the list intro count `four → five`:**
```markdown
5. **Does this instrument leave TWO sources of truth for one POLICY, and is its sharing proven by
   MUTATION?** Change the shared thing (constant, predicate, parser, marker) — does EVERY caller's
   pin redden in one run? A guard that ROUTES to a shared driver while hand-rolling the DECISION
   underneath it (routing-not-sharing, #102/#120) passes every gate that only checks the CALL SITE
   — so the adversary demands the MUTATION PROOF, never the call site. Empirical leg where the
   guard is in-tree: mutate the shared thing in a scratch copy; a caller whose pin stays GREEN is a
   private copy wearing the shared name — a **BLOCKER**, named by `file:line`.
```

**5b — PER-INSTRUMENT TABLE classification tuple gains the fourth axis** (`three → four`):
`each guard classified DERIVED + coverage-checked + effect-observed + one-source-proven-by-mutation (safe), or, on any of the four, a MISSING PIN…`

**5c — Verdict clause (`:283`) now requires the fourth axis:** the reach-table row must carry `reach DERIVED vs hand-list, coverage a checked variable vs not, effect vs proxy, and ONE source of truth proven by MUTATION vs two-sources / routing-not-sharing`, with the added consequence sentence that a call-site-only gate misses a routing-not-sharing guard until a mutation reddens every caller.

**5d — Report SUMMARY-BLOCK reach-table line (`:307`) names the fourth axis** (`…effect vs proxy, and one-source-proven-by-mutation vs routing-not-sharing…`).

**5e — the author's-own-copy self-check gains the leg-5 question** (`…and if I mutate the one shared thing this guard trusts, does EVERY caller's pin redden, or is one of them a private copy wearing the shared name?`).

**Consistency note (disclosed, not silent):** the lead named two edits (leg 5 in the list + the verdict clause). I also updated three dependent surfaces — the table-tuple (5b), the summary-block line (5d), and the author's-own-copy (5e) — because leaving them stale would make the render self-contradict: the verdict would demand a fourth axis the table couldn't hold and the summary block didn't name, and the self-check would omit the very leg it exists to install. This is "THE RIDER IS PART OF THE RULING" applied to my own edit — every surface describing the reach table now names all four axes. Verified consistent by grep across all five surfaces (list intro `these five`, leg 5, table tuple `on any of the four`, verdict clause, summary block, self-check).

**Faithful to the lead's wording:** leg 5's text is the lead's verbatim phrasing, adapted into the numbered-item format (bold lead question) consistent with legs 1–4, with the empirical leg kept inline (the lead bundled it that way; the other legs' empirical instructions live in the "Empirical wherever" paragraph, but bundling leg 5 keeps the DRY axis self-contained since it is orthogonal to the coverage/effect axis). `#102/#120` provenance preserved.
