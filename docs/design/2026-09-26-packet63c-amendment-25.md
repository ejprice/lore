# Packet 63c — ruling amendment 25 (sidecar-63c-2, 2026-09-26): FK-a19b-1 — message half-pairs, both halves; CD-1's pin re-keyed

Rules `REPORT-contract-63c-i-a-a19b.md` §F FK-a19b-1 (working tree). Directive: `REPORT-lead-63c.md@170a189`
(durable copy; this session's lore client is still down — `Read`/`awk`, said so). Amends amendment-21 CD-1's
pin and confirms amendment-24 §2 door #2. The lead is compacting: its successor relays this to
`contract-63c-i-a-a19b` (ledger directive + native wake; a fresh agent if a19b has retired).

## Ruling — Reading A: BOTH halves are refused; the CD-1 pin is re-keyed by DUAL
- **The contradiction is mine:** amendment 21 CD-1 wrote a pin under which a scoped-but-ownerless message
  "counts as migrated" and proceeds; amendment 22 §3 then ruled that a row with exactly ONE of the pair set is a
  half-applied store, and amendment 24 §2 applied that to messages "symmetric with agents". Two rulings, one
  population, opposite verdicts — the same one-member-stated-∀ shape, across two of my own documents.
  Consistency wins on the merits: a message with `scope` set and `owner_principal` NONE is a state no writer
  produces (measured by the author from `_comms_send`: the governed send stamps both; the legacy path writes
  all three NONE; a tokenless send is denied before any write) and that OWNED-BY-LINK's premise does not
  hold for — the message table's half-pair, exactly as amendment 22 §3 defined it for agents.
- **So:** the message leg's precondition refuses (i) owned-but-unscoped AND (ii) scoped-but-ownerless
  message rows, ONE refusal naming each half with its own count and bounded ids (amendment-24 door #1's
  shape), "half-applied", byte-inert. Expected empty in production, like E3; testable on the seed.
- **The CD-1 pin, re-keyed in place with its DUAL row written:** the virtue "never re-stamped" SURVIVES as
  byte-inertness under the refusal (the seeded `m_scoped` row is untouched — because nothing is stamped, not
  because the WHERE skipped it); the leg "counts as migrated" is DROPPED with the reason "the population is
  forbidden by the half-pair rule (amendment 22 §3 / 24 §2)". CD-1's scope-keyed self-guarding WHERE
  (`scope IS NONE AND owner_principal IS NONE`) STAYS as ruled — it is the write's own guard, and the refusal
  in front of it does not make a self-guarding statement redundant (defence at the write is what survives a
  narrowed precondition — E3's trigger — the day it fires). The redirect test the author names (shared
  preconditions redirected so the refusal cannot fire) is the leg that proves the WHERE still guards.
- **Reading B rejected:** "both halves" cannot mean "the refusal half and the `backfilled` half" — the
  sentence says "symmetric with agents", and agents have two half-pairs.
- **D2 authored, graded by the cold audit:** confirmed as amendment-24 §5 already provides for rows the
  adversary only probed the absence of; SP2 was print-only, so D2's pin (SP2's fixture + the redirect) is the
  author's, and the cold-audit re-run grades it.

## §W — a19b
| # | item |
|---|---|
| 1 | door #2 half (ii): scoped-but-ownerless message rows refused in the SAME refusal as half (i), each half counted and bounded |
| 2 | CD-1 pin re-keyed: byte-inert under refusal; "counts as migrated" dropped with its DUAL reason; the WHERE stays; redirect leg proves the WHERE |
| 3 | D2 authored; cold audit grades it |

## §E
- Erratum against amendment 21 CD-1 (a pin requiring a forbidden population to proceed). The general form,
  once more and for the file: *when a later ruling changes what a STATE means, sweep every earlier pin that
  seeds that state — pins are consumers of meaning too.*
