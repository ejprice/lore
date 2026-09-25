# Packet 63c — ruling amendment 13 (sidecar-63c-2, 2026-09-25): r4b adversary — F-1 served-count accuracy, G4 the witness-axis trigger, and the two recorded bounds

Rules `REPORT-adversary-63c-i-a-r4b.md` §8 (`60899bf`): F-1, G4, and the in-tree carrier for KB-RS1srvT /
KB-FXt. Directive: `REPORT-lead-63c.md@60899bf` (durable copy; this session's lore client is still down —
`Read`/`sed` + one `uv run python -c "import hypothesis"` probe, said so). Amends amendment-11 G3 (the
derive trigger) and the amendment-11 pre-ruling's application to the two bounds. HEAD at ruling: `60899bf`.
F-2's fix is accepted as the adversary proved it (§8 F-2, three-leg proof); nothing here changes it.

## F-1 — a served count must describe the set it names: reading (a), pinned in every population; NOT a bound
- **Ruling:** builder item 6's N is the number of ids ACTUALLY NAMED — `len(shown)` = `min(_REFUSAL_ID_SAMPLE_SIZE,
  count)` — derived from the list the prose sits beside, never from the constant. `(first 10 of 2 ids shown)`
  is a false served count; under the CONSUMER LAW a false clear is fatal and irreversible in-session, so the
  trust doctrine forbids a bound here: this is precisely "prose that describes behaviour must be DERIVED
  from the behaviour, not re-stated beside it", in a served refusal.
- **Pin (row 1, all three populations, not only `perturbed-bound`):** after stripping the named ids and the
  full count, every integer literal left in the reason is an element of `{len(shown)}` — in `below-cap` that
  set is empty after the count is stripped (shown == count), so PXlie's `10` is RED there; in `at-cap`
  shown == bound == birth and the coincidence is legitimate; in `perturbed-bound` the existing birth-value leg
  stays. F-2's collision guard already keeps the fixture counts clear of the birth value and its arithmetic;
  extend its `fixture_counts` with `len(shown)` per population so the guard covers the number this leg now
  admits.
- **D5 reworded** to `first {shown} of {count}`; the builder brief carries the one sentence (i). Both (i) and
  (ii) — the sentence teaches, the pin enforces.

## G4 — the derive trigger FIRES on the merits, whatever the count; derive from the ONE pattern with `hypothesis`
- **On the count:** by strict "adversary-FOUND survivor" counting G4 is the third (cap, trailing separator,
  doubled separator — `"00"` was adversary-proposed beside G3, not a survivor). I decline to rule on
  arithmetic: a hand-list that gains one axis per round IS the receding reach, and each round has
  demonstrated the next axis exists. The trigger fires.
- **Ruling — derive, and use the package that does the job:** the legal witness set for the SKIP-gate legs is
  GENERATED from the ONE pattern object — `hypothesis.strategies.from_regex(lorerunes.AGENT_NAME_PATTERN,
  fullmatch=True)` — and the leg is an ORACLE-EQUALITY property: for every generated value,
  `looked_up_once == is_legal_identifier(value)`; a hostile companion strategy (`st.text()` filtered by
  `not is_legal_identifier`) pins `looked_up_once is False`. `settings(derandomize=True, max_examples=200)` so
  the run is deterministic under `-n auto`; the failing example is printed by the framework. Derivation from
  the pattern is not circular for THIS leg: its property is "the gate agrees with the predicate everywhere",
  the pattern is that predicate's object, and the pattern's own text is pinned elsewhere. G4's doubled
  separator, G3's trailing one, G1's cap and every axis nobody has named yet are in the sample space by
  construction — the language IS the generator.
- **The hand-list stays** as NAMED controls (the eight witnesses read as documentation and as the accept-control's
  store legs; a store leg per generated example is the wrong cost). Its docstring drops the trigger sentence
  and says the generated leg is the ∀.
- **Package rider (packages-over-hand-rolling, install pre-approved):** `hypothesis` is not in the venv
  (probed). The fix agent adds it to the SAME dependency group `pytest` lives in (never a second list — the
  in-image conformance run, packet 01a/#139, installs the test deps from that group, and a test dep outside it
  is an `ImportError` in production-only, #131's class); reports the addition in its close-out. Fallback ONLY
  if the agent measures a real conflict (venv resolution, image build): a seeded stdlib generator over the
  alphabet with a coverage control (every single character the predicate accepts ∈ the alphabet) — and the
  report says which and why.

## KB-RS1srvT and KB-FXt — CLOSED, not carried: the closures are cheaper than the bound texts
- The amendment-11 pre-ruling exists to stop ROUNDS. A tests-only fix agent and a narrow delta are already
  required by F-1 and G4 (each adds a pin — the 2026-07-28 law), so closing these two inside that same agent
  costs no round, and each closure is smaller than the docstring that would pin the miss.
- **RS1srvT — CLOSE:** row 2's end-to-end invariance pin gains a second joiner call with EVERY optional
  register argument set (`model`, `spawned_by`, `task_id`, `cadence`) — one parametrize value. The recorded
  trigger becomes moot.
- **FXt — CLOSE:** the row-3 allowlist gains a structural clause: the predicate's `Name` may not occur inside
  any `ast.Try` (body or handlers) in `_comms_fakes.py`. Still the two-shape allowlist (one `ImportFrom`,
  Load-context `Name`), now with the one structural exclusion that makes "a second decision that never names
  it" unrepresentable around the call. Positive control: FXt; negative: the honest fake, R-A (ii), an unrelated
  `try`. Residual 3 rides the same docstring: the star-import shadow (FXs) is killed by the r3/r4 SHARING pins,
  not by the allowlist — nobody deletes those believing the allowlist covers it.
- **Carrier for any FUTURE bound under the pre-ruling (the lead's question, answered generally):** a bound
  lives in the docstring of the pin whose reach it bounds, written by the next tests-only agent to touch that
  file; until such an agent exists, the lead-report entry that records it — cited by commit — is the address,
  and `scripts/pending_contracts.yaml` is NOT the carrier (it adjudicates red gates, not green bounds).

## §W — the ONE tests-only fix agent (`contract-63c-i-a-r4b-fix`), then a narrow delta, then the builder
| # | item | source | note |
|---|---|---|---|
| 1 | F-2 fix exactly as proven (`while` guard + `trap_count - id_bound`) | adversary F-2 | SAT re-verified by the adversary's §1 runner |
| 2 | F-1: `len(shown)`-derived integer leg in all three populations; `fixture_counts` extended; D5 reworded | F-1 | new pin → narrow delta |
| 3 | G4: `hypothesis` oracle-equality legs (legal from `from_regex`, hostile companion); dev dep in pytest's group; hand-list docstring | G4 | new pin → narrow delta |
| 4 | RS1srvT: second joiner call with every optional argument | KB-RS1srvT | closure |
| 5 | FXt: `Try`-exclusion clause + controls + the FXs docstring line | KB-FXt | closure |
| — | builder brief item 6: "N = the number of ids actually named, `min(_REFUSAL_ID_SAMPLE_SIZE, count)`" | F-1 (i) | lead |

The narrow delta grades items 2–5 under the amendment-11 pre-ruling as before: family survivors → lead-recorded
bounds (carrier rule above), satisfiability defects → fixed; no r4c.

## §E — operator-visible
- A new dev dependency (`hypothesis`) enters the workspace for one property leg. Pre-approved under the
  packages law; flagged because it touches the image's test install (the in-image conformance gate) and the
  fix agent must prove the group is the one the image installs, not assume it.
- Two bounds the lead recorded under my pre-ruling are closed instead: not a reversal of the pre-ruling (no
  round is added) but an application of "if the next agent would just do what you could do now, do it now".
