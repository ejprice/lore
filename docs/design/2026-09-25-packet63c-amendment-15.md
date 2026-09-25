# Packet 63c — ruling amendment 15 (sidecar-63c-2, 2026-09-25): FORK F5-REACH — FXt on the uncollapsed helper

Amends amendment-13 §KB-FXt and amendment-11 §MP-A1's obfuscation bound. Rules
`REPORT-contract-63c-i-a-r4b-fix.md` §FORK F5-REACH (working tree; instrument `fxt_probe.py` in its §A).
Directive: `REPORT-lead-63c.md@76c35a5` (durable copy; this session's lore client is still down — `Read`/`awk`,
said so). HEAD at ruling: `76c35a5`.

## The measurement, accepted; the diagnosis, accepted; and the lesson it re-teaches me
Clause (iv) — "the predicate's `Name` is not inside any `ast.Try`" — finds 0 violations on FXt built on the
UNCOLLAPSED helper (the shape amendment 12 lets the builder keep) and 1 on the collapsed one. On U the `try`
wraps a local ALIAS of the helper's return; the `Name` sits outside every `try`. Following the alias is a
binding tracker — packet 01's v2, which regressed. The fix author is right that this is a design problem.
And it is the instrument lesson's own last line, which I skipped in amendments 11 and 13: *"when even
allowlisting the safe fails, stop looking at CODE — enforce the property at RUNTIME."* The property here was
always a runtime one — *the shared decision's outcome IS the fake's outcome* — and I wrote two static twins
for it.

## Ruling — (b): the EFFECT leg, alias-blind and receiver-blind; the static clauses stay as teaching twins
- **The leg:** through `patch_shared_object_everywhere` (reused; `expect_in` the `lorerunes` home), THE shared
  predicate is replaced by a stub that RAISES a sentinel; a fake `register` of a LEGAL identity must
  PROPAGATE that sentinel. No `except` may swallow the shared decision, whatever it wraps and whatever the
  handler spells. Kills FXt on both shapes and every FXt variant that names nothing. Both honest shapes stay
  green (the exception propagates through an alias exactly as through a direct call). At HEAD, the same
  early-return control as the effect pin above it.
- **It is wider than FXt, and that is the point:** a fake that never CONSULTS the shared predicate for a
  legal-looking value (a private pre-check that short-circuits; an obfuscated-name lookup that then falls back)
  does not raise either → RED. The r4/r4a effect pin observes silent SKIPS on hostile input; this leg observes
  that the shared decision is REACHED and TRUSTED on legal input. Together they are the two halves of "routing
  is not sharing" at the fake, observed rather than inferred.
- **Consequence for amendment-11's obfuscation KNOWN BOUND:** CLOSED by this leg — an obfuscated string
  constant still reads the patched module attribute, finds the stub, raises, and is caught if swallowed. The
  negative control that asserted the static allowlist stays quiet on an obfuscated name STAYS, re-labelled: it
  now documents the STATIC instrument's reach ("the allowlist cannot see this spelling; the effect leg does"),
  not a hole. Its KNOWN-BOUND message goes.
- **The static clauses (the two-shape allowlist, clause (iv)) STAY** as implemented and proven on C: they are
  the teaching twins that tell a builder WHICH line broke the shape, and they kill the honest-paste spellings
  at collection time. Their docstrings say: *"static reach — the effect leg is the ∀"*. Neither is a gate the
  effect leg needs; neither may be deleted believing the other covers it.
- **(a) rejected:** a pinned bound for a hole a one-function leg closes, on the very shape the builder is
  told it MAY keep, would pin the miss on the DEFAULT path. **(c) rejected** as amendment 12 already did.
- **Threat model, restated for the leg:** receiver-blind by construction, so the honest-engineer model is no
  longer needed for this family; what remains outside it is a fake that re-implements the decision without
  ever importing `lorerunes` at all — and that build reds the r3/r4 SHARING pins first (residual 3's line).

## §W
| # | item | change |
|---|---|---|
| 5 (amended) | FXt: effect leg (raising stub via the shared patcher; legal register must propagate) + HEAD early-return control; clause (iv) and the allowlist kept as static twins with "the effect leg is the ∀" docstrings; obfuscation control re-labelled, bound message removed | new pin → the already-required narrow delta |

## §E
- Erratum against amendments 11 and 13: a runtime property was given static instruments twice; the fifth
  relocation of the fake-guard family was inside code STRUCTURE (an alias), which no shape clause sees and
  every effect leg does. The askable form from the instrument lesson, which I should have asked at amendment
  11: *"is the property I am pinning a fact about the CODE's shape, or about what the code DOES?"* — a "does"
  property gets a runtime leg first and static twins for teaching, not the reverse.
