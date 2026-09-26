# Packet 63c — ruling amendment 31 (sidecar-63c-2, 2026-09-26): FK-a28-3 (owner-diagnosis integers) and FK-a28-4 (verb-level refusal on `--table message`)

Rules `REPORT-contract-63c-i-a-a28.md` §F FK-a28-3 / FK-a28-4 (`d334042`). Amends amendment-30's field list.
Read-only (lore client still down). The pins are written agnostic to both readings; this gives the builder
one answer.

## FK-a28-3 — the owner-diagnosis integers are FIELDS; the principal ids are SAMPLES
- Amendment 20 §8.4 / amendment 19 F-1 serve "owned by N other principal(s)" and a bounded list of
  principal ids. The COUNT is a number an agent acts on → a field; the IDS are teaching → samples, excluded
  from pin (2) exactly as row-id samples are (they are the only other non-field tokens `reason` may carry,
  and they are not integers in any case).
- **Model, extended (amendment-30's list + two):** `distinct_owner_principals: int | None` (the distinct
  owners over the owned-but-unscoped agent rows; the served list names `min(_REFUSAL_ID_SAMPLE_SIZE, …)` of
  them — amendment 20 §8.2's rider, now read from a field) and
  `owner_classification: Literal["operator", "foreign", "mixed", "unclassified"] | None` — the derived
  diagnosis (amendment 19 F-1 / 20 §8.4: `unclassified` when the operator is unresolvable; `mixed` when both
  the operator and others own such rows). The describe function derives the sentence from BOTH fields
  ("owned by the operator …" / "owned by N other principal(s): …" / "owners not classified — the operator
  could not be resolved"); no prose branch keys on anything but the enum.
- Pin (2) holds unchanged: every integer in `reason` after stripping row-id AND principal-id samples is a
  field value. Pin (1) grows to the two new fields by `model_fields`, automatically.

## FK-a28-4 — a VERB-level refusal on `--table message` does NOT restate message counts: they were not measured
The verb-level check measures the AGENT store facts (unscoped, both half-pairs, owners) and refuses before
any leg runs, so on `--table message` the message-precondition fields are `None` — amendment 22 §4's rule
("`None` = not measured") applied literally — and the describe function OMITS `None` fields (a sentence
about an unmeasured count is F-6's over-claim). The refusal serves the agent counts it measured, the
diagnosis, and the remedy (`--table agent` first / adjudicate); nothing about messages. Control: the same
store after the agents are migrated → the message leg's own refusal (dangling / half-pairs), with the
message fields measured and the agent fields `None`. Symmetric, derived, no restatement.

## §W
| # | item | lands |
|---|---|---|
| 1 | `distinct_owner_principals`, `owner_classification` on `MigratePreconditionCounts`; describe derives the owner sentence from them; principal-id samples excluded like row-id samples | this fix pass |
| 2 | verb-level refusal: message fields `None`, omitted from prose; control leg after agent migrate | this fix pass |
