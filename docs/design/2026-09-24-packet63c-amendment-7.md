# Packet 63c — ruling amendment 7 (sidecar-63c-2, 2026-09-24): r4 FORK-D — the text-twin pin's key also matches `config.SLUG_PATTERN`

Amends amendment-6 STOP-rule §2 (`3327770`). Rules `REPORT-contract-63c-i-a-r4.md` §FORKS FORK-D
(uncommitted on disk; the reviser holds its commit for this ruling). Directive: `REPORT-lead-63c.md@6a34c0a`
(durable copy; this session's lore client is still down — `Read`/`awk`/one `uv run python` probe, said so).

## The fact, and my erratum that produced the fork
- Amendment-6 said the key text `[a-z0-9][a-z0-9_` *"occurs in exactly ONE string constant in the workspace"*
  and reported a four-member sweep. That sweep was run with the FULL class text `[a-z0-9][a-z0-9_-]`; the pin
  was then keyed on the PREFIX so it would also catch the drifted-dot twin. **I swept with one key and pinned
  another.** Re-swept 2026-09-24 with the pinned key over every production member: `agents.py`
  (`AGENT_NAME_PATTERN`, moves in i-a) · `surreal_schema.py` (`_IDENTIFIER_CHARSET_PATTERN`, the builder's
  one-line rebind) · **`config.py:97` `SLUG_PATTERN = r"^[a-z0-9][a-z0-9_]*$"`** — the project-SLUG rule,
  consumed by the pydantic `SlugStr` constraint, no hyphen, unbounded: a DIFFERENT policy over a different
  language. The literal reading of amendment-6 reds a correct build; the reviser was right to stop.
- Askable form, for the next pin I write: *"did I sweep with the EXACT key the pin will use?"* A sweep is
  evidence only for the key it ran.

## Ruling — reading (a): keep the key, allowlist the safe BY EVIDENCE
- **(a) is CLAUDE.md's own prescription, verbatim:** *"Every exemption in a deny-by-default safe-set must be
  evidence-backed (a live probe proving it cannot conflict), never 'it writes no row'."* The safe set is
  (i) the ONE `AGENT_NAME_PATTERN = re.compile(<const>)` definition in `lorerunes`, and (ii) `config.SLUG_PATTERN`,
  exempted by **(file, binding name, EXACT text)** and carrying an **evidence leg the pin COMPUTES live, in
  BOTH directions** — never a prose claim: it rejects a legal agent identifier (`fixer-b`; agent ✓ / slug ✗) AND
  it accepts a string the agent rule rejects (65 × `a`; slug ✓ / agent ✗). Measured 2026-09-24 with a live
  `re` probe: exactly those two results; the pattern texts differ. Two languages that differ in both
  directions are two policies, and two policies are allowed two patterns.
- **Re-open trigger, stated in the pin:** any change to `SLUG_PATTERN`'s text stops the exact-text exemption
  matching → RED → re-adjudicate. If the re-adjudication finds the two languages have CONVERGED (the evidence
  leg fails in either direction), that is not a new exemption — it is a design fork: one language with two
  spellings goes to `lorerunes` as ONE predicate (the `is_blank` precedent). The pin's failure text says so.
- **(b) rejected:** lengthening the key so the class must continue past `_` lets an honest paste that DROPS the
  hyphen (`[a-z0-9][a-z0-9_]{0,63}`) escape — that is a narrower gate than the threat model amendment-6 wrote
  into the instrument (the honest engineer who pastes the regex), traded away to avoid writing one
  evidence-backed exemption. The wrong trade.
- **(c) rejected:** editing `SLUG_PATTERN` is an ungranted production change to an unrelated policy, and wrong
  on the merits — slugs and agent names are different things by operator directive (2026-07-03, task #32).
- `scripts/c3_wrongbuild_driver.py`'s hit is outside the scan's reach by design (`include_scripts=False`, as
  r3's AST scan) and is a wrong-build fixture string — correct, no exemption needed; the reviser's read stands.

## Classification
GATING, unchanged from amendment-6 §W item 1 — the reviser's provisional build IS the ruling; commit it. The
evidence leg and the exact-text exemption are riders of the same pin, not a second pin.

## §E
- Erratum against amendment-6 §"swept up": the "exactly ONE string constant" claim was false for the key
  as pinned; corrected here. The swept-up builder one-liner (`_IDENTIFIER_CHARSET_PATTERN =
  AGENT_NAME_PATTERN.pattern`) stands.
