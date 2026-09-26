# Packet 63c — ruling amendment 28 (sidecar-63c-2, 2026-09-26): DESIGN — the register path's race compensation (F-1 BLOCKER) and preflight-before-gate leak (F-2)

Design escalation (second fix wave on one gate). Rules `REPORT-blindreader-63c-i-a-2.md` §F-1 / §F-2
(`8e7aa2b`). Directive: the lead's Task 28. Read/awk only (lore client still down); every code fact below
was read at HEAD `server.py::_comms_register` (lines 6681–6840), `keeps.py::delete_keep` and
`minted_by_this_call`. Amends amendment-22 §1.2, amendment-24 door #4b, and the a19b pins built on them.

## F-1 — CONFIRMED by reading. The compensation is wrong BY DESIGN, not by a corner: delete it
- **The walk holds at HEAD:** `register` calls `preflight` itself, so X's post-mint `register` reads X''s row
  (role differs) → `AgentIdentityConflictError` → the `except _AgentRegistryError` branch → `minted_session_keep`
  is True → `delete_keep(K)`. `delete_keep` cascades `member_of` only and — by its own 63/64 FORWARD-BOUNDARY
  docstring — does nothing about rows scoped `keep:K`. X' is scoped to a keep that no longer exists; the
  next mint is a fresh ULID; X' is stranded permanently.
- **The reader's quantifier point is exactly right, and it is mine:** the branch fires only on a refusal
  AFTER the mint, i.e. on the race; the only principal-bearing winner of that race must pass SF-63-1 on the
  keep X just minted, whose sole household member is X's principal — so the winner is the SAME principal and
  necessarily FOUND K. "Created by this call" was derived over "keeps I found" and stated over "keeps nobody
  else uses". Every principal-bearing trigger of the branch strands the winner; the only winner it does not
  strand is a tokenless one, which mints nothing.
- **And the harm the branch was built against does not exist on that path:** #485's harm is a stray keeper
  blocking a DIFFERENT principal. After the race, K is kept by the caller's principal AND holds that
  principal's successfully registered agent — the keep is legitimately that principal's session keep, and a
  later different principal is denied exactly as it would be had X' registered alone. Nothing to compensate.
- **Ruling:** NO compensation. The `except _AgentRegistryError` compensation branch is DELETED; the registry's
  refusal propagates unchanged (the race serves the registry's own teaching — KP4's property, now by
  construction); `minted_by_this_call` and the created-only plumbing are dead and go. The `guarded
  delete` alternative is rejected: it keeps a delete on a path where a delete is never correct, and it puts
  a scoped-row count in front of `delete_keep` that belongs INSIDE `delete_keep` (see §E).
- **Residual, named as a bound with its closer:** the tokenless-winner race (credentialed X refused after
  minting K because a TOKENLESS X' created the row) leaves K with X's principal as keeper and no scoped
  agent — #485's shape, narrowed to a race window that exists only while tokenless registers are admitted.
  Q2 β (63c-i-b) denies tokenless registers; the bound closes there by construction. Trigger before β: a
  keep found with a keeper and zero scoped rows after a refused register.
- **DUAL for the a19b pins:** KP1's VIRTUE (the concurrent winner's keep survives) is now the design's
  property and STAYS as the pin, re-keyed to assert the winner's `scope` resolves to a live keep; the
  created-only pin, the appended-remedy-line pin (door #4b) and the failed-delete pin are DELETED with
  rows "the mechanism they pinned is removed (amendment 28)". Door #4b's "a keep left behind" trigger is
  moot: nothing deletes.
- **Construction recipe (for the cold audit or a probe — executes F-1 on the current build, RED; on the
  fix, GREEN):** one principal P, session `s`, name `a`. Wrap the wired `keep_store.get_or_create_keyed` so
  that on its FIRST call, after the real mint returns K, it runs a complete second handler call
  `comms(register, a, s, role="auditor")` inline (X' — finds K, passes the gate, CREATEs the row scoped
  `keep:K`), then returns K to the first call (X, `role="builder"`). Assert: X raises
  `AgentIdentityConflictError` naming the role; `get_keep(K)` still resolves; X''s row `scope == keep:K`;
  a third register by P into `s` FINDS K (no fresh ULID). On the current build the second assertion fails
  (K deleted) — that is F-1 reproduced.

## F-2 — CONFIRMED by reading. Restore the §6 stance by ORDER; no new disclosure posture is decided here
- At HEAD the order is resolve principal → `preflight` (6734) → mint (6751) → visibility gate (6765). A
  foreign credentialed principal probing `(session, name)` receives the registry's refusal — existence,
  retirement, `role`, `spawned_by` — for a session it cannot join. Before this wave SF-63-1 denied first,
  naming only the session and the remedy (63-rulings §6, quoted in the handler's own comment). My
  amendment-22 §1 ordered "preflight BEFORE the mint" and never asked what preflight discloses to a caller
  the gate would have stopped: the same one-property fix that ignores its neighbour.
- **Ruling — ORDER:** resolve principal → **read-only SF-63-1 gate** (`get_by_key("session:<s>")`; if a keep
  EXISTS and the caller is not householded in it → `GovernedDenied`, the §6 text, ZERO registry reads) →
  `preflight` → `get_or_create_keyed` (the mint) → the existing post-mint visibility re-check (kept, for the
  keep-minted-meanwhile race) → `register`. Both properties hold: no store side effect on a preflight
  refusal (#485), and no agent fact served past the gate (§6).
- **Residual, named:** if ANOTHER principal mints the keep between the read-only gate and the mint,
  preflight has already run against a session that, at gate time, had no keeper — whose agent rows are
  therefore ownerless legacy rows or the E3 population (bounded, measured empty). Stated in the docstring;
  no pin.
- **Not an operator posture question:** this restores the disclosure stance the 63-rulings already fixed;
  it decides nothing new. The reader's bound — a tokenless transport already leaks the same facts — is
  the pre-β world, closed by Q2 β at i-b; the ORDER fix closes the token-required transport NOW. Flagged
  §E so the operator sees it, not for a decision.
- **Construction recipe:** alice keeps `s` with agent `a` (role builder) and a retired agent `r`; carol
  (credentialed, foreign, not householded) calls `register(a, s, role="scout")` and `register(r, s, …)`.
  Current build: `AgentIdentityConflictError` naming `builder` / `RetiredAgentError` — the leak. Fix:
  `GovernedDenied` with the SF-63-1 text, byte-identical for both names and for a NONEXISTENT name (no
  existence oracle), and a spy on the registry's row read counting ZERO. Controls: bob (householded)
  re-registering his own agent proceeds; alice's own conflict still teaches the role.

## Process — this IS the second-fix-wave trigger, so the shape is ruled, not patched
- Both are ORDER changes plus a deletion — no new mechanism. They land in the cold audit's fix pass (the
  audit is grading the same patch and may name both; its receipts are the ones to cite). Two contract pins
  (the two recipes) + the DUAL deletions get a NARROW adversary delta: amendment 24 §5 closed the a19b
  round, but a BLOCKER-class design change on a security seam is where rigor-to-importance points the other
  way, and two pins are cheap. Then the cold-audit re-run.
- The builder brief carries: delete the compensation branch and `minted_by_this_call`; insert the read-only
  gate before `preflight`; keep the post-mint re-check; the docstring's ORDER paragraph rewritten to name
  BOTH properties and BOTH residuals.

## §E — operator-visible
- **F-1's root, one level down, is not this packet's:** `delete_keep` cascades `member_of` and orphans
  scoped governed rows — its own docstring's forward-boundary note, now with a first live path. That belongs
  to packet 64's owner-deletion wave (sidecar-64's #488 is, by its description, this exact class): a keep
  delete with scoped rows must refuse, cascade, or re-scope — ruled there, not here. This amendment removes
  the only 63c path that called it on a live keep.
- **F-2 decides no posture:** it restores 63-rulings §6 on token-required transports now; β (i-b) closes
  the tokenless twin. If the operator wants a different disclosure stance, that is a 63-rulings change.
- **Erratum, mine (amendments 22 §1.2, 24 door #4b):** I designed a compensation for a race whose only
  principal-bearing winner is the compensation's own victim, and an ORDER that solved one property by
  breaking its neighbour. Both are the quantifier law; both were catchable by the recipe above, which is
  five lines and which I did not write when I ruled the mechanism.
