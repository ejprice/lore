# Packet 63c — ruling amendment 10 (sidecar-63c-2, 2026-09-25): r4a reading R-A and candidates C-1…C-5

Rules `REPORT-contract-63c-i-a-r4a.md` (`bf77fb9`) §FORKS R-A and §CANDIDATES C-1…C-5. Directive:
`REPORT-lead-63c.md@a8b84bc` (durable copy; this session's lore client is still down — `Read`/`awk`, said
so). The narrow adversary delta on `e80a854..bf77fb9` runs in parallel; nothing here changes what it grades.
HEAD at ruling: `a8b84bc`.

**Where a closure lands, stated once:** r4a is closed and under its delta. So every closure below is tagged
with ONE of: **r4b-if-any** (rides an r4b addendum ONLY if the running delta returns a missing pin that needs
one — no addendum is opened for these alone) · **i-b** (the 63c-i-b contract, whose adversary grades it) ·
**ii** (the 63c-ii contract). Each has a named owner and a named decision point, per the deferral law.

## R-A — reading (ii): a module-top import from `lorerunes` OR one of its submodules. ACCEPTED as built
The property is "the guard cannot outlive its premise": an UNGUARDED module-top import cannot skip anything,
whichever module of the package it names. Reading (i) would red an honest builder importing from the defining
submodule — a false positive on correct code, the switched-off-scanner class. The negative control
`[submodule-top-import-and-an-unrelated-try]` is the pin. No change.

## C-1 — ONE legal corpus: fold by UNION, in 63c-ii
`_VALID_IDENTIFIERS` (`test_comms_schema.py`, the brief store-ASSERT accept leg) and
`test_pattern_accepts_legal_names`' local list fold into `_LEGAL_IDENTIFIER_WITNESSES` by UNION — every value
either list carried joins the corpus (`fixer_b2`, `audit-c2`, `scout_d`, `wave7`, `fixer-b`, `z`×64 beside
`a`×64), deduplicated by the boundary property each witnesses, so no pin loses a witness. Owner: the **63c-ii
contract author** — ii is the wave that re-keys the brief accept leg (its ASSERT drops) and parametrises
`BriefLedger.publish`'s MOVE pins over the shared corpora, which is the moment the three lists are in one
hand. "Whichever wave next touches those pins" is not a decision point; ii is.

## C-2 — RS1's other axis (a DIFFERENT KEEP): unreachable through the tool by construction; one registry-seam row, i-b
- **Measured:** `_comms_register` mints the keep with `get_or_create_keyed(key=f"session:{session}", …)` — the
  keep is a deterministic function of the SESSION, and the agent id is `(session, name)`, so a re-register of
  the same agent always carries THE same keep. `(alice, K) → (alice, K2)` cannot be produced by any tool call;
  only a direct registry caller with a synthetic keep id can. Not a live door; a construction-only one.
- **Ruling:** ruling §2.2 row 2 covers it ("`scope` UNTOUCHED"); the writer is `register`, so the row is a
  registry-seam sequence `(alice, K) → (alice, K2)` with the absolute expectation (`scope = keep:K`, row byte-
  identical). Lands **r4b-if-any**, else as the first mint-once row of the **i-b** contract (i-b re-touches
  `register` for the dispatcher work and its adversary grades it). Until then its docstring home is the RS1
  pin's, as a stated axis.

## C-3 — the end-to-end register door for a householded joiner: REAL, and it is 63c-i-b's
- **Measured (read, not run):** the tool's only pre-registry gate is SF-63-1 — a principal NOT householded in
  the session keep is denied. A HOUSEHOLDED joiner (bob, admitted to alice's session keep) calling
  `lore_comms register` with alice's agent name reaches `registry.register(…, owner_principal_id=bob)` on the
  RE-register path. After r4a, ownership survives (RS1: owner stays alice) — but the re-register SUCCEEDS for
  bob: `status` resets to `active`, `heartbeat_at` bumps, `model`/`task_id`/`cadence` take bob's values. Ruling
  §5 considered the NON-householded case (line: "a second, non-householded principal — SF-63-1 denies that
  register"); the householded case is a gap in the ruling, not in r4a. Nothing at HEAD production carries it
  (no principals on agents in the running image); post-i-a it is a within-household liveness forgery through
  the one verb the identity-first dispatcher (Q4a) does not cover, because `register` is the verb that MINTS
  the capability the dispatcher checks.
- **Ruling (design, mine to make; flagged §E):** a re-register is a SELF-write. On the re-register path, an
  existing row whose `owner_principal` is not NONE and is not the caller's principal is REFUSED before any
  write — the existing identity-conflict teaching applies verbatim (*"names are never reused; register a
  fresh name"*), naming no owner (no oracle), ZERO agent-table mutations (#467-1's ORDER property), no
  capability served. An OWNERLESS existing row (α / legacy) stays re-registerable by any householded principal
  (the survivor virtue) until `migrate-governed` stamps it to the operator — after which only the operator's
  principal re-registers the legacy fleet, which is the correct reading of "the pre-65 fleet is the operator's
  household".
- **Pin shape, for the i-b contract:** end-to-end through `AppContext.comms` (`register`), a householded
  joiner re-registering another principal's agent → the conflict teaching, row byte-identical (`SELECT *`),
  no capability; controls: the OWNER re-registering their own agent → `re_registered=True`; the joiner
  registering a FRESH name in the shared session → created, owner = joiner. Plus the registry-seam twin (the
  refusal lives in `register`, so a direct caller meets it too). The security-auditor's #467 wire battery
  gains this row. Owner: **i-b** contract author; decision point: i-b's contract, before its adversary.
- **Why not r4a/r4b:** it is a new served DENIAL on a verb, i.e. serving/security — the split ruled i-a = agent
  DATA, i-b = serving/security (ruling §7, Q4). Pinning it in i-a's contract would move a production behaviour
  across the wave boundary the operator adopted.

## C-4 — the PX2 detector's phrase bound: ACCEPTED as stated
The birth-value leg (no integer equal to the constant's birth value after stripping ids and count) is the ∀
half and is what kills PX2; the phrase leg (`first N` / `N … shown` / `showing N`) is a convenience with a
stated bound. Correctly pinned in the docstring; no change.

## C-5 — the shape/effect pins' reach is ONE file: a stated reach now, widened at the natural trigger
- The safe shape is cheap to state ∀ the test tree: no `Try` wraps a `lorerunes*` import anywhere under
  `loremaster/tests`, and every test module naming `is_legal_identifier` imports it at module top. That
  widening rides **r4b-if-any**; otherwise it lands with **i-b**, which is the wave that will add test
  doubles for the identity-first dispatcher — the exact moment a second double could adopt the predicate,
  i.e. the trigger. Until then the one-file reach is a KNOWN reach stated in both pins' docstrings (the r4a
  author already did this), with that trigger named.

## §W — routing table
| # | item | lands | owner |
|---|---|---|---|
| R-A | reading (ii) | no change | — |
| C-1 | legal corpora fold by UNION | ii | ii contract author |
| C-2 | different-keep mint-once row (registry seam) | r4b-if-any, else i-b | r4b/i-b contract author |
| C-3 | householded-joiner re-register REFUSED (self-write); end-to-end + seam pins; #467 battery row | i-b | i-b contract author + security-auditor |
| C-4 | phrase bound | accepted | — |
| C-5 | shape/effect reach widened to the test tree | r4b-if-any, else i-b | as C-2 |

If the running delta returns SUFFICIENT, nothing here re-opens r4a: the builder proceeds on `bf77fb9`.

## §E — operator-visible
- **C-3 adds a served denial to `lore_comms register`** (a householded joiner may not re-register another
  principal's agent). It is the ownership model's own consequence and lands in i-b with its own adversary and
  the security auditor's battery; flagged because it changes a verb's behaviour for a legitimate-looking
  caller. Not judged MAJOR — the alternative (a within-household liveness forgery on a teammate's agent) is
  the #467 class the packet exists to close.
- The ruling itself (§5) had the gap: it reasoned the non-householded case and stopped. Same quantifier miss
  as the packet's others — derived on the door I analysed, stated over the set.
