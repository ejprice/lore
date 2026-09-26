# Packet 63c — ruling amendment 26 (sidecar-63c-2, 2026-09-26): a19b residual R-3 — a store with BOTH a message half-pair and a dangling sender

Rules `REPORT-contract-63c-i-a-a19b.md` §12 R-3 / §10 item 5. Directive: `REPORT-lead-63c.md@6c229bc`
(durable copy; this session's lore client is still down — said so). The answer goes into the builder's brief.

## Ruling — ONE refusal naming BOTH; deterministic order = the check order; a pin, not a bound
- **Shape:** the packet has ruled this combination three times already and always the same way — amendment 20
  §8.4 (unresolvable operator + owned-but-unscoped), amendment 24 door #1 (both agent half-pairs),
  amendment 25 (both message half-pairs): *a refusal that names one of two problems buys the operator two round
  trips.* The message leg's precondition serves ONE refusal carrying BOTH diagnoses, each with its own count
  and bounded ids (the ONE `_REFUSAL_ID_SAMPLE_SIZE`), byte-inert. The a19b reference already does this;
  the ruling makes it the contract, not a courtesy.
- **Order:** neither remedy blocks the other's diagnosis (unlike the unresolvable-operator case, where
  resolution is a precondition of classifying owners), so the order is immaterial to the OPERATOR — but the
  served text must be DETERMINISTIC to be pinnable and diff-stable. Rule: the diagnoses appear in the shared
  function's message-leg CHECK order — dangling senders first (a link fact about the row), then half-pairs
  (a column fact about the row) — and that order is stated once in the function's docstring, never restated
  in the test (the pin asserts both substrings present and the dangling one first, reading the order from
  nothing but the served text). No precedence: precedence is exactly the one-of-two the law forbids.
- **Pin or cold audit:** a PIN — it is the amendment-20 §8.4 / door-#1 shape (one seeded fixture carrying
  both conditions: one ghost-sender legacy message beside one owned-but-unscoped message and one sound
  legacy message; `refused=True`; both counts named; the sound row NOT stamped; `SELECT *` byte-identical on
  `message`). Authored by `contract-63c-i-a-a19b` if still live (one test, minutes); if it has retired, the
  cold audit lists it as a residual with this fixture shape and the i-b contract author lands it — either
  way the BUILDER builds "one refusal naming both, check order" now, from the brief, and the cold audit's
  served-English check reads the combined text against this ruling.
- **Not graded-by-adversary:** the a19b adversary is closed (amendment 24 §5); the pin is a fixture + a
  served-text assertion in the packet's established shape, the cold audit's instrument.

## §W
| # | item | owner |
|---|---|---|
| 1 | builder brief: message-leg refusal names BOTH (dangling first, then half-pairs), each counted + bounded; byte-inert | lead (builder) |
| 2 | the both-conditions pin (fixture shape above) | a19b author if live, else i-b contract via the cold audit's residual |
