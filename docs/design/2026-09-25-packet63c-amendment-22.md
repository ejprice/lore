# Packet 63c — ruling amendment 22 (sidecar-63c-2, 2026-09-25): a19 adversary — #485 in i-a (∀ refusals), F-1 governed set, F-2 half-pairs, F-3 honest receipts

Rules `REPORT-adversary-63c-i-a-a19.md` §7 / §9 (`69bf002`) and the lead's Task 22. Directive:
`REPORT-lead-63c.md@69bf002` (durable copy; this session's lore client is still down — `Read`/`sed`, said
so). Amends amendment-19 D-1/D-2 and amendment-21 CD-2. MP-1…MP-5 land in the a19a addendum as the
adversary's own kills (K1, K2, K3, PD2-as-pin, the prose-skeleton golden — its K4 denylist is correctly NOT
the pin). HEAD at ruling: `69bf002`.

## 1. #485 — YES, i-a: D-2's class stated over ONE refusal, now ruled ∀ registry refusals
- **The defect, accepted as reproduced:** any registry refusal AFTER the keep mint (role / `spawned_by`
  write-once conflict, `RetiredAgentError`, the provenance pair — not only blank role) leaves the caller as
  keeper of `session:<s>` and DENIES the next principal (SF-63-1). D-2 derived "before the mint" on the blank
  role and stated it over "a rejected register" — the QUANTIFIER LAW, mine, one more time. "Live" at branch
  HEAD only (the deployed image predates it; deploy is pkt 65) — a tree defect, not a production one; i-a's
  because it is the register path i-a is already rewriting.
- **Ruling — shape (ONE implementation, no copied decision):**
  1. The registry factors every refusal it can raise WITHOUT a write into ONE method — `preflight(name,
     session, role, spawned_by, owner_principal_id, session_keep_id?)` — that reads the existing row (by id;
     the same read `register` performs) and raises exactly what `register` would raise: identity, blank
     role, the pair, role/`spawned_by` conflict, retired. `register` CALLS `preflight` as its own first step,
     so there is one decision, not a handler copy of it (#102). The handler calls `preflight` BEFORE
     `get_or_create_keyed`, then mints, then `register`.
  2. The residual is the CONCURRENT race (a conflicting register between preflight and register). It is
     compensated, not ignored: on a registry refusal after the mint, the handler deletes the keep IFF this
     call CREATED it (`get_or_create_keyed` reports created-vs-found; the builder derives that from its
     return, adding the flag if absent), never a keep it merely found. Compensation is the fallback for the
     race only — amendment 19 D-2's order stands as the primary path, which is what K3's zero-call spy pins.
     The race window and the compensation are named in the docstring as the bound; re-open trigger: a
     failed compensation observed (a keep left behind after a refused register).
- **The ∀-refusals pin, DERIVED, never a hand-list:** the set of refusal classes is derived from the registry
  itself — every concrete subclass of `AgentRegistryError` defined in `agents.py` (plus the base for the
  teaching refusals). The pin asserts coverage as a CHECKED VARIABLE: for each derived class there is a
  driven fixture through `AppContext.comms(action="register")` on the credentialed harness that raises it —
  a class with no fixture reds the pin with the class's name (a new refusal added tomorrow cannot arrive
  unpinned). For each fixture: zero `get_or_create_keyed` calls (K3's spy) for every preflight-refusable
  class; keep table byte-identical; the next principal's register into that session SUCCEEDS; the served
  refusal is the registry's own teaching. Control: a valid register mints exactly one keep.
- **Classification:** a19a addendum → narrow adversary (production register path, third-party consequence)
  → builder fix → cold-audit re-run. Same wave.

## 2. F-1 — Reading A: "valid" = the GOVERNED table set; amendment 21 CD-2's "supported set" is corrected
`brief` is governed and named in D-1's explicit list, so on a multi-principal store `--table brief` still meets
the §2.1 refusal (SAME teaching, byte-inert), and on a clean store its existing "brief lands 63c-ii" teaching.
Only a name OUTSIDE the governed set gets the zero-read "not supported". The governed set is the production
constant the five-set resolver pin already cross-checks (nodes only). Erratum: amendment 21 wrote "the supported
set"; the four `∀[brief]` pins are right and stand.

## 3. F-2 — an ownerless-but-SCOPED agent is a HALF-PAIR, and a half-pair is a half-applied store: refused at verb level
- A3 makes the pair all-or-nothing at the writer; the migrate stamps both columns in one statement. So an
  agent row with exactly one of `owner_principal` / `scope` set can only be a raw seed or a half-applied prior
  run — the same population the §2.1 precondition already refuses on the OTHER half. Ruling: the verb-level
  precondition refuses BOTH half-pairs, diagnosed "half-applied" (never "multi-principal"; F-1's derived
  diagnosis distinguishes). Consequence: the message leg can never meet an ownerless-scoped sender, so it never
  stamps a NONE owner — pinned as a post-migrate invariant (∀ stamped messages, `owner_principal IS NOT NONE`).
- **My erratum (amendment 19 D-1, pin 2):** I named "an ownerless-SCOPED agent" as the CONTROL that the
  order guard does not fire once migrated. That state is one the invariant forbids; the control is a FULLY
  migrated agent (both columns set). The a19 contract's D-1 control population is re-keyed accordingly — a
  fixture built on a forbidden state discriminates nothing (FIXTURES MUST DISCRIMINATE, by me, on my own pin).

## 4. F-3 — refusal receipts serve only what was MEASURED
`scanned` / `already_migrated` on a verb-level refusal are not zero — they were never measured (the verb
refused before any target-table scan). Zero is a served count that describes no set (CONSUMER LAW). Ruling: on
a refusal those fields are `None` ("not measured — refused before the scan" in the render) and the refusal's
receipt carries the counts the precondition DID measure (unscoped agents; offending rows, bounded). If the
receipt model's consumers make `Optional` too wide for this wave, the builder surfaces it — the fallback is
NOT zero; it is an explicit `refused_before_scan` field with the render deriving the "not measured" line from
it. Pin: a verb-level refusal's receipt serves no target-table count it did not measure.

## §W — the a19a addendum, in order
| # | item | source |
|---|---|---|
| 1 | K1, K2 (reverse-direction sharing with twin baselines) · K3 (zero-mint spy) · PD2 as a pin · prose-skeleton golden | MP-1…MP-5 |
| 2 | #485: `preflight` ONE method, handler order, created-only compensation for the race; the DERIVED ∀-refusal-classes pin with coverage as a checked variable | §1 |
| 3 | F-1: governed-set validity; `∀[brief]` pins stand; amendment-21 CD-2 corrected | §2 |
| 4 | F-2: both half-pairs refused at verb level; post-migrate no-NONE-owner invariant; D-1 control re-keyed to a fully migrated agent | §3 |
| 5 | F-3: `None` receipts on refusal + the precondition's own counts; pin | §4 |
| 6 | amendment-20 R1/R2 riders (principal-count perturbation; both-conditions refusal) | am-20 |
| → | narrow adversary → builder fix → cold-audit re-run | — |

## §E — operator-visible
- #485 is a tree-only defect (deployed image predates it); it lands in i-a with an adversary because the
  consequence is a third party denied by a keep it never asked for. #486 (an unrelated once-in-three red) is
  the operator's row, untouched here.
- Two errata of mine (D-2's "a rejected register"; D-1's forbidden-state control) are the same shape as
  every earlier one; the derived ∀-refusals pin is the first instrument in this packet whose reach is a
  checked variable over the REGISTRY's own class set rather than my enumeration of it.
