# 02 — Comms: render architecture (#104 step-0) · formerly PKT-28 phase C2a
size ~0.40 wu (measured; operator SPLIT 2026-07-19 — promise-instrument HARDENING → 02a) · wave C · depends: — (C1 deployed) · **NEXT after packet 01**

> **OPERATOR SPLIT (2026-07-19):** the contract author measured the real work at ~3–4× the
> original 0.20 estimate. Ruling: packet 02 KEEPS all render work (#104 typed applicability +
> the one-accessor standing-brief ROLE + #103 heartbeat-skew generalization incl. the REAL
> `subscribed_name_skew` store method + the three §9.4 tails + the `brief v`→`project v` fleet
> cell rename) + #100 + #101 + the promise-string completeness-guard CORE (classify every comms
> render literal; default-FAIL) — this half delivers the exit smoke. The promise instrument's
> ADVANCED HARDENING (full §9.7 per-entry executable-predicate emission proofs + the `safe_str`
> literal-text coverage closure `_SAFE_STR_LITERAL_RESIDUAL`) moves to **`02a-comms-promise-instrument-hardening.md`** — not smoke-critical.
law: read `comms-subsystem.md` FIRST (data model, tool surface, rulings, honest limits,
roster) + DESIGN-LAW §8/§5/§1 · design source: ~/.claude/plans/one-of-claude-codes-nifty-garden.md · DEPLOY: yes (both)

## Mission
The ruled STEP 0 of the message-graph work — **before any new comms surface is built**:
kill the root cause of all ten C1 render-honesty instances (#104: 'project' is a ROLE
bound to a NAME, re-hardcoded at 7 handler sites and then described GENERICALLY by the
renders), plus the three deferred C1 residues.

## Scope IN
- **#104** — name the ROLE via ONE accessor; renders take TYPED applicability
  (`auto_ack_at_register: bool`), never a name they compare; kill the fixture
  monoculture (`_brief()` must not default the parameter the code branches on — every
  call site chooses). Full analysis + step-0 plan: finding #104's body.
- **#103** — the skew line promises "surfaces at their next heartbeat" but heartbeat
  only reads the 'project' brief (spec v8 ALREADY RULED — implement, don't re-design).
- **#100** — `created_by` on AppContext.comms splits identity (test-only affordance);
  unify author and acting agent.
- **#101** — the three log-capture tests leaking global logging state under xdist.

## Scope OUT
- Any message/to/blocks schema or verb (packets 03–04). Any new render not required by
  #104's refactor.

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
`lore_findings` → #100 #101 #103 #104 open; read #104's body (it carries the C2 step-0
plan); spec at v8; suite green at HEAD.

## Exit
Full gates + cold audit (render surface) + deploy BOTH + smoke on the live wire (skew
line truthful for a non-'project' brief); findings resolved with notes; INDEX row + Log.
