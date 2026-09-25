# Packet 63c — ruling amendment 8 (sidecar-63c-2, 2026-09-24): r4 FORK-E and the candidate KNOWN BOUNDS KB-1…KB-5

Rules `REPORT-contract-63c-i-a-r4.md` (`e80a854`) §FORKS FORK-E and §"Candidate KNOWN BOUNDS". Directive:
`REPORT-lead-63c.md@ba8b4c9` (durable copy; this session's lore client is still down — `Read`/`awk`, said so).
Amends amendment-6 R-3's wording. HEAD at ruling: `ba8b4c9`. The r4 adversary is running in parallel on
`39935f6..e80a854`; nothing here changes what it grades.

## How these rulings sit with the STOP-rule (amendment-6 §5), so the lead does not have to re-derive it
The STOP-rule bounds contract→adversary ROUNDS on the identity class: no new INSTRUMENT, no r5. It does not
forbid fixture rows, corpus entries, or controls that enlarge pins already graded. Three of the five candidates
below close as exactly that — **an r4 addendum commit (`r4a`)**: one corpus entry, one negative control, one
parity row. Owner: the r4 author if still live, else the next contract-capable agent the lead spawns — never
the builder (builder ≠ grader). It needs no adversary round of its own: the running r4 delta grades the
instruments, and the cold audit re-runs every gate over the addendum. The other two are not bounds at all
(one is the pin doing its job; one is a stated reach parameter) and get docstring text only.

## FORK-E — reading (i) was meant; no new pin
"The FULL count on a separate line" in amendment-6 R-3 meant *asserted separately from the id sample* — an
independent assertion so the reader loses nothing at any bound — not a `\n` in the served text. Reading (ii)
would be a new production-shape requirement no ruling states, and both reference builds put count and ids on
one line. Erratum against my wording: "line" should have read "assertion". The r4 pin
(`re.search(rf"\b{trap_count}\s+(?:agent\s+)?rows?\b", reason)` beside `len(named) == min(bound, count)`) is
the ruling.

## KB-1 — CLOSE: one corpus entry, `"fixer.b"` (dot)
The dotted twin is not a hypothetical: the adversary constructed it twice (N1c at the home, X1 at the SKIP
gate) and both were behaviourally different TODAY. A drift the adversary can build twice belongs in THE ONE
corpus, not in a trigger clause. Cost is 1–2 ids per corpus-parametrised pin — the corpus exists precisely so
that growth is one line. r4a.

## KB-2 — PINNED KNOWN BOUND: the reworded / runtime-assembled class
Already the instrument's stated threat model (amendment-6 §1: the honest engineer who PASTES the regex; a
reworded `[0-9a-z]` or an assembled `"[a-z0-9]" + …` is adversarial-only and not a defect of the gate). The
law's form is a test that asserts the hole and REDs the day someone closes it: a NEGATIVE synthetic control —
a module carrying the reworded class must NOT red the scan — with the message *"KNOWN BOUND — threat model:
honest paste (amendment-6 §1); if you closed it deliberately, delete this control and say so."* If r4's
negative controls already carry a reworded-class case, that control IS the pin and gains the message; else
one control in r4a. Trigger, verbatim from #138: the threat model changes — untrusted contributors or a hosted
deployment (packet 39 consults it).

## KB-3 — ACCEPTED, stated in the instrument (a reach parameter, not a hole)
`include_scripts=False` is the same reach r3's AST scan and #124's coverage pin run at; `scripts/` holds gates,
deploy tooling and wrong-build fixtures, none of which decides identity legality. The bound is self-revealing:
flipping the flag without adjudicating `c3_wrongbuild_driver.py` reds the scan on that fixture string, so it
cannot be "closed" silently. One sentence in the scan's docstring names the parameter and the trigger: *a
`scripts/` module that imports `lorerunes.is_legal_identifier` or `AGENT_NAME_PATTERN` to decide, at which point
the scan's reach grows to `scripts/`.* No pin beyond the existing reach anti-vacuity.

## KB-4 — NOT a bound: the red on a docstring quoting the rule is the pin doing P8d's job
A docstring that QUOTES the charset is a second SPELLING of the rule in served/read prose — exactly the
natural-language corpse class (3 of 4 P8d defects; "prose that describes behaviour must be DERIVED from the
behaviour, not re-stated beside it"). The next rule change leaves it false with every gate green. So the pin
is RIGHT to red it, and the failure text is the teaching: *"reference the constant (`lorerunes.AGENT_NAME_PATTERN`
/ `.pattern` derived into served text), never quote its text."* None exists today (SAT unaffected); the first
such red is an honest engineer being taught the house rule, not a false positive. No change; the failure
text is amended to say the above rather than "state the rule in words".

## KB-5 — CLOSE: one parity row
A stamped row re-registered with a DIFFERENT consistent pair is a fourth sequence on the same door THE
QUANTIFIER LAW already made us pin ∀ inputs (MP-E → MP-5). The real writer is pinned mint-once on it (r2's
`test_re_register_does_not_restamp_the_governed_triple_mint_once`); the fake is not, and a fake that
re-stamps would let every fake-driven tool test observe an owner change the writer never makes. One row,
outcome class + three stamps, real vs fake. r4a.

## §W — r4a addendum
| # | item | class |
|---|---|---|
| 1 | KB-1: `"fixer.b"` joins `_HOSTILE_IDENTIFIERS` | fixture growth |
| 2 | KB-2: reworded-class negative control with the KNOWN BOUND message (or the message on the existing one) | pinned bound |
| 3 | KB-5: fourth parity sequence (different consistent pair) | fixture row |
| 4 | KB-3 docstring sentence; KB-4 failure-text wording | PROSE |
| — | FORK-E: (i) stands | none |

r4a lands before the builder is spawned if the r4 author is still live (minutes); otherwise it lands before
the cold audit and the builder proceeds on `e80a854` — none of the three rows changes what the builder builds.

## §E
- Erratum: amendment-6 R-3 "on a separate line" → "as a separate assertion".
- The r4 author's builder-brief rows (rebind `_IDENTIFIER_CHARSET_PATTERN`; delete the fake's guard or import
  at module top; delete both `pending_contracts.yaml` entries with the build; the sample-size docstring states
  WHY) are consistent with amendments 5–7 and stand.
