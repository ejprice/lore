# Packet 63c — ruling amendment 19 (sidecar-63c-2, 2026-09-25): the contract-blind read — BR-F-2 scope, BR-F-4 locus, the prose MINORs

Rules `REPORT-blindreader-63c-i-a.md` (`8fe09d0`) decisions D-1..D-3. Directive: `REPORT-lead-63c.md@8fe09d0`
(durable copy; this session's lore client is still down — `Read`/`awk`, said so). Amends ruling §6 (Q5) by
lifting one precondition. The cold audit runs in parallel; the lead merges both into ONE fix wave. HEAD at
ruling: `8fe09d0`.

## D-1 — YES, in 63c-i-a's scope: BR-F-2 is a BUILD DEFECT, and the precondition is VERB-level
- **Why in scope (three receipts, all mine):** ruling §6 names the attack the row precondition exists to
  survive — *"seed one foreign-owned agent → the verb refuses ALL tables and writes nothing"* (line 580) — as
  the reason for the precondition; the agent leg's own docstring at HEAD says *"`scope IS NONE` is THE
  unmigrated predicate ∀ governed tables"*; and ruling §6 also says `_owner_count` "stays as the §2.6
  agent-first precondition the MESSAGE leg reads" — a sentence that was true when both predicates were
  owner-keyed and became false the moment i-a re-keyed the agent leg. The wave that changes a predicate's
  MEANING sweeps its consumers (the rename/reshape law; the reader's §2e is that sweep, run after the fact).
  It is not a later wave's; it is the DUAL i-a owed.
- **Ruling — the §2.1 multi-principal refusal is a STORE fact, so it is checked ONCE, in `migrate_governed`,
  before ANY table's leg:** an owned-but-unscoped agent means the grandfather rule (every legacy row → the
  operator / the project keep) is wrong for the whole store — memory rows widened into the project keep are
  wrong there too, not only messages — so `--table agent|memory|message|brief` each refuse with the SAME
  teaching, byte-identical store. That is the honest reading of "refuses ALL tables and writes nothing", and
  it retires my own "a precondition with no mechanism behind it is ceremony" for `brief`: the mechanism is
  the store's single-principal invariant, which every leg's stamp assumes. The agent-first ORDER precondition
  (unmigrated agents → the message leg refuses) stays the message leg's, keyed on the SAME shared predicate
  (`scope IS NONE`), never on `owner_principal IS NONE`.
- **ONE implementation:** one function (`_agent_migration_preconditions(store)` or the like) returning the
  unscoped count and the bounded owned-but-unscoped sample; the verb-level check and the message leg's order
  guard both CALL it; `_owner_count`'s agent use is retired (its message-row use may stay, docstring fixed —
  F-5). Sharing proven by MUTATION: perturb the shared predicate → the verb-level refusal and the order guard
  move together.
- **Pins (contract, before the builder fix):** (1) seed ONE owned-but-unscoped agent → each of the four
  `--table` values refuses, same reason text, `SELECT *` byte-identical on every governed table (the #470
  attack, verbatim, ∀ tables); (2) the message order guard on a store with an ownerless UNSCOPED agent →
  refused (re-keyed from owner to scope; the existing ii-a pin's fixture may already be owner-NONE AND
  scope-NONE, in which case it discriminates nothing — the fixture must carry an OWNED-but-unscoped agent
  for the F-2 door and an ownerless-scoped agent as the control that the order guard does NOT fire once
  migrated); (3) the mutation leg above.
- **F-3 (TOCTOU) rides the same fix:** the agent UPDATE gains `AND owner_principal IS NONE` — a self-guarding
  write at no cost — and the exempt-token golden is updated by the contract author in the same revision (it
  is the contract's own pin of the executed statement; changing it deliberately is what the pin is for).

## D-2 — BR-F-4 is BEHAVIOUR, not prose: refuse BEFORE the keep mint, routed through the shared predicate
- The side effect is not a wording problem: a blank-role credentialed register mints the session keep and
  makes the caller its KEEPER, after which a different principal's register into that session is DENIED by
  SF-63-1. That is #97's "a rejected write has no side effect" violated with a served consequence for a
  third party. So the handler refuses a blank role BEFORE `get_or_create_keyed`, by calling
  `lorerunes.is_blank` — the tool's REFUSE policy over the ONE decision, exactly the shape
  `_validate_comms_charset` already has for name/session (which are therefore already gated before the mint).
  The registry keeps its own check for direct callers; two consumers, one predicate, proven by the existing
  shared-decision mutation pin gaining the handler leg.
- **Pin:** a blank-role credentialed register through `AppContext.comms(action="register")` → the teaching
  refusal, keep table byte-identical (no keep minted, no keeper claimed), no agent row; controls: a hostile
  name through the tool also mints no keep (pins the existing order); a valid register mints exactly one.
  The prose "nothing was written" then stays TRUE, which is the point: fix the behaviour and the sentence
  becomes derivable.

## D-3 — the prose MINORs ride the SAME fix wave, with a pin wherever the text is served
- **F-1 (served diagnosis):** derive it. The refusal's id read also selects `owner_principal`; the reason
  states whether the offending owners are the operator (*"owned by the operator — registered by a
  pkt-62–63b image; see amendment-1 E3"*) or other principals (named, bounded) — never the fixed phrase
  "multi-principal or half-applied". Pin: the R-Q5-1 fixture gains an operator-owned trap population and
  the served text is asserted per population. (E3's narrowing of the precondition itself stays deferred as
  ruled — measure-then-tune — but the DIAGNOSIS must not lie on the day the trigger fires.)
- **F-9 (the restated gloss):** DROP the English gloss in both refusals; each states `must match
  {AGENT_NAME_PATTERN.pattern}` (derived, includes the cap) with the value fenced. The consumer is an LLM; a
  regex is a rule it reads. Pin: the rule statement served by the registry refusal and by the server refusal
  is byte-identical (one rule, one spelling — the served-prose form of ONE IMPLEMENTATION).
- **F-8 (a refuted threat model re-taught in `lorerunes/identifiers.py`):** replace with #219's corrected
  rationale (bound parameters; render-safety; the trailing-newline twin; the cheap gate). Prose; no pin —
  but the cold audit's served-English check lists it so the class is counted.
- **F-5:** docstring; rides F-2's retirement of `_owner_count`'s agent use.
- **F-7 (U+001C–U+001F narrowing under `is_blank`):** accepted as a NOTE; recorded in the DUAL as
  "dropped-deliberately: `is_blank` is the ONE blankness rule (#222)"; 63c-ii aligns `brief.body`'s trim-based
  ASSERT to the same answer, so "what is blank" has one answer across tables after ii.

## §W — the ONE fix wave (the lead merges the cold audit's rows in)
| # | item | class |
|---|---|---|
| 1 | verb-level §2.1 precondition (ONE function; agent-leg + order-guard share it); ∀-tables refusal pin; order-guard re-key + discriminating fixture; mutation leg | contract pins → **narrow adversary** → builder fix |
| 2 | F-3 `AND owner_principal IS NONE` + golden update | same revision |
| 3 | F-4 handler refuses blank role before the keep mint via `is_blank`; keep-byte-identical pin; handler leg on the shared-decision pin | same revision |
| 4 | F-1 derived diagnosis + operator-owned population pin | same revision |
| 5 | F-9 gloss dropped; served-rule byte-identity pin | same revision |
| 6 | F-8, F-5 prose; F-7 DUAL line | builder fix, no pin |
| → | builder fix pass → cold audit re-run (the artifact, not the recipe) | — |

**Why the adversary IS warranted here, after amendment 16 declined a sixth round:** these are PRODUCTION
behaviour pins on a migration that widens visibility and on a register path with a third-party side effect
— security-adjacent, served — not a footer gate's sampling. Rigor-to-importance cuts the other way.

## §E — operator-visible
- Ruling §6's "ceremony" sentence for `brief` is retracted: the multi-principal precondition is store-level
  and verb-level. It does not change what a single-principal store experiences (every leg proceeds exactly
  as before); it changes only that a multi-principal store is refused everywhere instead of on one table.
- My own erratum count for this packet is now long enough to name its shape once: every one was a claim
  derived on one member (one table, one seam, one build, one sample) and stated over the set. The blind
  reader's §2e found the same shape in the build. The instrument that catches it is the one the reader ran —
  an inventory of what the OLD code meant to every consumer, written before reading the tests.
