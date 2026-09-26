# Packet 63c — ruling amendment 29 (sidecar-63c-2, 2026-09-26): cold-audit RS-5 (the concurrent same-name loser) and F-8

Rules `REPORT-coldaudit-63c-i-a-2.md` (`8ae642f`) RS-5 and F-8. Directive: the lead's Task 29. Read/awk only
(lore client still down). The audit CONFIRMED amendment 28 by execution (its F-2 = my F-1: 8-way concurrency
strands the whole session in up to 11/20 rounds, HEAD 0/20; its F-1 = my F-2, the leak) — the recipes ran.

## RS-5 — a CONSUMER-LAW defect on the register path; FIX NOW, in this fix pass, with the ≥8-way pin
- **The fact:** two concurrent FIRST registers of the same `(session, name, role)` race on the CREATE of one
  uuid5 id; the loser is served a raw `TxnDomainRejectionError` — an engine error for a call that is LEGAL
  and, sequentially, IDEMPOTENT (the second identical register is `re_registered=True`). 55/20 rounds at
  HEAD too: pre-existing, and the audit is right that amendment 28 leaves it unaddressed (no compensation
  is correct; no TEACHING is not).
- **Ruling:** the registry's CREATE, on the store's unique-id rejection, RE-READS the row and takes the
  registry's own re-register path — ONE implementation: the same branch a sequential second call takes,
  never a second copy of the idempotency logic and never a handler-level retry. The loser is served exactly
  what the sequential loser is served: the registry's result (`re_registered=True`) for an identical
  `(name, session, role)`, or the registry's own identity-conflict TEACHING if the winner's role/`spawned_by`
  differ (that is `preflight`'s decision, reached by the same re-read). A raw engine error never reaches a
  consumer for a legal call — CONSUMER LAW; the fake already documents the CAS window this closes.
- **Why now and not i-b:** the fix pass has the register path open and the 8-way rig built (RS-2's P5
  shape); the change is the registry's CREATE branch catching ONE classified store rejection and falling
  through to code that already exists. **Pin (the concurrency law):** the P5 rig, ∀ rounds, ∀ callers: every
  caller receives a registry result or a registry teaching, never `TxnDomainRejectionError`; the loser's
  `re_registered` is True on an identical role; ONE agent row; 20 consecutive greens to clear, plus the P2
  sequential leg as the deterministic twin. Rides the narrow delta with amendment 28's two pins.
- **Named decision point if it is not one branch:** if the driver's classification of the unique-id
  conflict is not already a typed rejection the registry can catch by class (never by message text —
  routing is not sharing), the fix-pass builder STOPS and says so; the item then goes to i-b's contract
  with this shape, and the raw error is a lead-recorded bound until then (pre-existing, 55/20).

## F-8 — no objection; fold it in
Each half's count is asserted INSIDE its own clause (the span between that clause's noun and the next
clause boundary, read from the served text), never as `len(ids) in stated` over the whole reason. The
audit's P3 receipt (11 / 12 attributed correctly) is the control; a swapped-count build reds. Same shape
for amendment 26's three-clause refusal (RS-1's fixture).

## §W
| # | item | lands |
|---|---|---|
| 1 | RS-5: registry CREATE-conflict → re-read → the existing re-register path; P5 ∀-callers pin, 20× greens + P2 leg | this fix pass (stop-and-route to i-b if not one classified branch) |
| 2 | F-8: per-clause count attribution in the door-#2 and amendment-26 pins | this fix pass (contract) |
