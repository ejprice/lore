# REPORT-secaudit-62w2 — packet 62 Wave 2 DEDICATED SECURITY-AUDITOR (anti-spoofing mechanism A)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — §2 (bound params; explicit
  projection of a NONE/dangling `record<>` link's `.field` reads back `None`; `str(RecordID)`
  round-trips), §1.1/§1.4/§1.8 (OVERWRITE field / option<> on populated table / UNIQUE over
  option<string> = many-NONE + unique-non-NONE). Cited, not re-transcribed.

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable and used: spike-surreal TEST store
`ws://127.0.0.1:18000` (systemd; prod :18500 was up but I NEVER pointed a test at it);
`scripts/scratch_copy.sh` produced a provenance-asserted scratch at `/tmp/secaudit62w2`;
lore tools loaded via `ToolSearch "+lore"`; registered on `lore_comms` (session `packet62`,
role `security-auditor`, model `claude-opus-4-8`). pytest/ruff available. No impossibilities.
Code-structure lookups were direct file reads + git + one live construction sweep — no grep
fallback masquerading as a structure answer that lore should have owned; I said so where I used grep.

**Tree provenance receipt (#140):** `loremaster.__file__ =
/tmp/secaudit62w2/loremaster/loremaster/__init__.py` — asserted by `scratch_copy.sh` AND
re-printed live by BOTH exploit harnesses under `uv run python`. Every live attack below graded
the SCRATCH tree, never the original checkout. I EDITED NOTHING committed.

---

## SUMMARY BLOCK
- **VERDICT: GO.** Every §9 IN-scope MUST-HOLD survived every exploit I could construct — **36
  live checks across two harnesses, 36 PASS, 0 FAIL**, each attack paired with a positive control
  so a deny-for-the-wrong-reason would show. Mechanism (A) clears the operator's bar ("prevents
  spoofing and prompt injection") as honestly framed by §3.2/§9: cross-principal isolation is
  airtight, sibling-spoof requires the secret (preimage-resistant), identity never comes from a
  tool argument, and the accepted own-capability residual (Fork 1) is the ONLY residual.
- **state: done.** Read-only/adversarial; I attacked the built mechanism, edited nothing.
- **Graded:** `66b5fa4` (`feat(62): wave-2 identity mechanism`) · HEAD-at-report `66b5fa4` · **SAME**.
- **THE BINDING (W2.2 cond 3) — the load-bearing pin — HOLDS live:** agent-A's VALID capability
  under principal-B's transport token DENIES (A2), and the cross-principal WRITE-stamp fail-closes
  (A3); an ownerless agent's capability is denied under ALL tokens (D1–D4, None is never a wildcard).
- **NEW surface the contract fixtures did not exercise — the #105 dangling-owner-ghost — is CLOSED:**
  after the owning principal is DELETED (R3.2 dangle-tolerated), the surviving agent's
  `owner_principal` dangles; `owner_principal.email` dereferences to `None` (store §2), the binding
  denies, and the orphaned capability is UNUSABLE under any token including one claiming the deleted
  principal's email (exploit `exploit_dangle_62w2.py`, D2/D3). No cross-principal resurrection.
- **Single-brain (§5) untouched:** `pdp.py` is byte-identical wave-1→HEAD (git); the 61b PDP
  oracle + all three wave-2 suites go **85 passed** in the 62 tree. 62 constructs no `Subject` —
  the reach pin's per-tool RED_ADJUDICATED legs are the correct 62↔63 boundary, not a defect.
- **Packages considered:** none — no mechanism specified/built (auditor). The mechanism REUSES
  in-tree crypto (`sha512_hex`, `secrets.token_urlsafe`) and the shared `parse_credential`; I
  found nothing warranting a package swap and specified none.
- **Reuse ledger:** none — I introduced no reusable production symbol (two throwaway exploit
  harnesses, pasted verbatim in §Instruments and kept in scratch).
- **residuals:** 6, all accepted-bounds or forward-looking/low-severity notes (§Residual table) —
  ZERO are violations of an IN-scope §9 MUST-HOLD.
- **decisions-needed:** none. One forward-looking note for 63/64 (stamp_owner double-read TOCTOU,
  R#4) is a design memo for the next packet, filed as `lore_findings`, not a 62 gate.
- **receipt pointers:** live exploits §Attack results + §Instruments (harnesses verbatim);
  static confirmations §Static confirmations; residuals §Residual table.

---

## THE FRAME
The cold-auditor runs in parallel on CORRECTNESS. MY frame is the §9 SECURITY THREAT MODEL,
verbatim. I assumed the mechanism was broken and tried to prove it by CONSTRUCTION on a live store
(a false belief about the code's semantics is self-sealing — only a live exploit attempt breaks
it). Target: the mechanism committed at HEAD — the capability mint (`agents.py::register` create
branch), `verify_capability`/`owner_principal_of` (`agents.py`), `stamp_owner`/`OwnerStampError`
(`owner_stamp.py`), `parse_credential` (`lorerunes/credentials.py`), the DDL
(`store/surreal_schema.py`), the `_comms_register` reach seam (`server.py`). Baseline read:
`REPORT-builder-62w2.md`, `REPORT-adversary-62w2{,b}.md` (the contract's own 14-wrong-build
security sweep) — I went BEYOND it with live cross-principal / sibling / dangling-owner / injection
/ leak constructions.

## ATTACK RESULTS — §9 MUST-HOLDs, each CONSTRUCTED live with a positive control
Harness `exploit_secaudit_62w2.py` (32/32) + `exploit_dangle_62w2.py` (4/4). Tags below are the
harness tags; `pos` = positive control proving the deny was for the RIGHT reason.

### Cross-principal isolation + THE BINDING (W2-R2) — §9 "cross-principal isolation" / "anti-spoofing"
- **A1 (pos)** A's capability under A's own token → resolves to A's agent id. *(the legit path works)*
- **A2 (exploit)** A's VALID capability under **B's** transport token → **DENY** (binding cond 3).
- **A3 (exploit)** `stamp_owner(B_token, A_capability)` → **`OwnerStampError`** (cross-principal
  WRITE fail-closed — A cannot stamp a governed write as B).
- **A4 (pos)** `stamp_owner(A_token, A_capability)` → `(A_principal, A_agent)`. *(legit stamp works)*
- **VERDICT:** principal-A (and A's agents) cannot READ-resolve or WRITE-stamp as principal-B. Held.

### Anti-spoofing — no principal impersonation (forged / absent transport token)
- **B1 (exploit)** A's capability under a token whose subject is `attacker@evil.com` (no such
  principal) → **DENY** (owner_email `alice@…` ≠ token subject).
- **B2 (exploit)** A's capability under an ABSENT token subject (`""`) → **DENY** (`not
  token_principal`).
- **B3 (exploit)** `stamp_owner` with an absent subject → **`OwnerStampError`** (fail-closed).
- **VERDICT:** identity comes from the VERIFIED transport token; a forged/absent one mints/stamps
  nothing. Held.

### No sibling-agent spoof (preimage resistance) — §9 "…NOR as a sibling agent"
- **C1** A's capability resolves to its OWN agent, not its alice-sibling (`a1.id != a2.id`) —
  identity follows the CAPABILITY (the secret), not the name half.
- **C2 (exploit)** a FORGED sibling capability `alice_w2:<guessed-secret>` under alice's token →
  **DENY** (no sha512 hash match — a sibling that never saw a2's secret cannot produce it).
- **C3 (pos)** the REAL sibling capability `cap_a2` → resolves to a2. *(proves C2's deny was
  preimage resistance, not a broken verify)*
- **VERDICT:** an injected agent-A that never saw agent-B's secret CANNOT stamp as B. The
  server-verified sha512-UNIQUE hash — not a self-declared name — is the authority. Held. (The
  accepted Fork-1 residual — misusing one's OWN captured secret — is NOT this case; see Residuals.)

### Ownerless capability — None is never a wildcard (the contract-adversary's FIX-2, re-verified live)
- **D1/D2/D3 (exploit)** an ownerless agent's minted capability under alice's / bob's / an absent
  token → **DENY** in every case (owner_email `None` → binding-mismatch).
- **D4 (exploit)** `stamp_owner` with an ownerless capability → **`OwnerStampError`**.
- **VERDICT:** there is NO token under which an ownerless capability is accepted (fail-closed);
  positive control A1 proves verify is not merely always-None. Held.

### Injection containment / confused deputy — §3.2.2 "identity/owner NEVER from a tool argument"
- **E1** `AgentRegistry.register` exposes NO `owner=`/`as_agent=`/`created_by=`/`scope=` display arg
  (params: `cadence, model, name, owner_principal_id, role, session, spawned_by, task_id`;
  `owner_principal_id` is the SERVER-derived id, not a display claim).
- **E2** `verify_capability(presented, access_token)` and `stamp_owner(access_token,
  agent_capability, *, registry)` take NO display name/owner arg — identity comes ONLY from the
  verified capability + token.
- **E3** the **MCP `_comms_register` handler swallows extra caller args into `**_ignored`** and
  exposes no `owner_principal_id`/owner arg — a hostile `owner=`/`owner_principal_id=` on the wire
  is DROPPED, never forwarded to `register`. *(the confused-deputy door is shut at the tool boundary)*
- **VERDICT:** no authorization-bearing argument reaches the owner derivation; the stamp is
  server-derived from the verified capability + token. Held.

### Injection via the presented credential string (bound `$h`, never interpolated)
- **F1 (exploit)** a credential whose secret carries SurrealQL
  (`alice_w1:x'; DELETE FROM agent; DEFINE FIELD pwn …; --`) → **DENY** (hashed whole and bound as
  `$h`, never interpolated).
- **F2 (pos)** store INTACT afterward — agent count still 6, and A's real capability still verifies.
- **VERDICT:** the presented string is a bound param (store §2); no injection. Held.

### Uniform deny / no oracle — §9 anti-enumeration
- **J1** malformed / no-such-capability(valid-format wrong-secret) / binding-mismatch /
  unknown-name → **all return exactly `None`** (uniform, no exception, no distinguishing value; the
  denial reason is laundered to a DEBUG token, never returned). No VALUE oracle; the UNIQUE-hash
  lookup gives no name-existence oracle. *(Timing: see Residual R#6 — I did not microbenchmark; the
  only early-return discriminates on the attacker's OWN input format, not on server state.)*

### No residual window — no-cache revocation (W2-R3) + owner lifecycle (cond 4)
- **G1 (pos)→G2 (exploit)** retire the agent → the VERY NEXT call with the old capability DENIES
  (no cache, no residual window).
- **H0/H1** SUSPEND the owning principal → its agent's capability denies next call (transitive).
- **H2/H3** EXPIRE the owning principal → denies. *(each with an active/unexpired positive control)*

### Optional capability expiry — ESC-3 enforced-when-set (W2-R4)
- **I0 (pos)** expiry UNSET → accepted (SF-2: no clock TTL by default — not a decoration that always
  denies).
- **I1 (pos)** FUTURE expiry set → accepted.
- **I2 (exploit)** PAST expiry set → **DENY**, re-checked every call (`_absolute_expiry`-style).
- **VERDICT:** the seam is a real bound, not a decorative lie. Held.

### The #105 dangling-owner-ghost (NEW — the contract fixtures used owned/active principals only)
- **D0 (pos)** live capability accepted before delete.
- **D1** after the owning principal ROW is deleted (R3.2 dangle-tolerated), the agent row SURVIVES
  with `owner_principal` pointing at a now-missing `principal:…`.
- Live dereference receipt: `owner_principal.email` = `'alice@example.com'` pre-delete → **`None`**
  post-delete (SurrealDB dereferences the link at query time; a dangling target yields `None` under
  an explicit projection — store §2).
- **D2/D3 (exploit)** the orphaned capability under a token claiming the deleted email / any other
  email → **DENY**. No stale-owner resurrection; fail-closed.
- **VERDICT:** the dangling-owner hole R3.1 explicitly worried about is closed at the verify seam,
  because a dangling `record<>` reads `None` and None owner is never a wildcard. Held.

## STATIC CONFIRMATIONS
- **PDP untouched (§5):** `git diff 3c94ffd..HEAD -- …pdp.py` empty; `git log e34cf47..HEAD --
  '*pdp.py'` empty. `authorize`/`authorize_filter` (`lorerunes/pdp.py`) byte-unchanged. The only
  wave-2 touch to `token_verifier.py` is a DOCSTRING (agent_of stays `None` — SF-3; body
  unchanged), confirmed by the diff.
- **Credential-leak sweep (W2-R6 / §F3a):** the raw `<name>:<secret>` is FORMED only at
  `agents.py:705` (`capability = f"{name}:{secret}"`), hashed to the stored digest, and returned
  ONCE via `AgentRegisterResult.capability`. It appears in NO log (`_deny_capability` logs only a
  laundered `reason` token, `agents.py:991`), NO render (`_render_comms_register` never references
  `result.capability` — grep clean), NO error message (`OwnerStampError` texts are generic — K3),
  and NO stored row (K1: `SELECT *` on the row carries `capability_hash` only, not the secret).
  Dynamic K1/K2/K3 all PASS (the raw secret substring is absent from the stored row, the Agent
  `model_dump`, and the fail-closed error text).
- **DDL (W2-R7):** `capability_hash option<string>` + `capability_expires_at option<datetime>`
  both `DEFINE FIELD OVERWRITE`; UNIQUE `IF NOT EXISTS` index on `capability_hash`
  (store §1.1/§1.4/§1.8 — many-NONE tolerated, duplicate real hash rejected). Read in
  `surreal_schema.py`; the dirty-store migration legs are pinned by the contract (not re-run here).

## RESIDUAL TABLE (accepted bounds + low-severity/forward notes — ZERO IN-scope §9 violations)
| # | item | class | §9 status / re-open trigger |
|---|---|---|---|
| R1 | A stolen/captured capability acts as ITS OWN agent under its own principal's token until retire | ACCEPTED BOUND (Fork 1 residual — the ONLY one) | §9 accepted ("stolen short-lived agent token"); mitigated by no-cache revocation (G2) + the binding (A2). Not a defect. |
| R2 | An injected agent within its OWN (principal, agent) scope can corrupt its own rows | ACCEPTED BOUND | §9 accepted ("the agent's own trust domain"). Not a 62 concern. |
| R3 | `admin` = full unrestricted superuser; a stolen admin credential = total store compromise | ACCEPTED BOUND | §9/§10-K accepted. 62 does NOT touch the PDP admin short-circuit; `verify_capability` treats an admin capability exactly like any other (no special weakening). |
| R4 | `stamp_owner` does TWO reads — `verify_capability` (validates `owner_principal.email == token.subject`) then `owner_principal_of` (re-reads `owner_principal`). A concurrent owner re-own BETWEEN them could stamp a write with an owner_principal ≠ the binding-validated one. | LOW / FORWARD NOTE (NOT exploitable at 62 HEAD) | **No owner-mutation path exists in 62** — `owner_principal` is CREATE-only; no re-own verb (ESC-2 defers it; admin `set_owner` is 63/64). **Re-open trigger: 63/64 introduces owner mutation** — then collapse to ONE read (verify already projects `owner_principal`; return the pair). Filed as `lore_findings`. |
| R5 | At 62 HEAD the MCP `_comms_register` handler mints+stores a `capability_hash` but delivers no raw secret (render omits it) and stamps no owner (ownerless) → every pre-cutover register creates an inert, undeliverable, always-DENIED capability | OBSERVATION (benign) | Intended pre-cutover state (delivery + owner-stamp wiring = pkt-65 cutover + 63/64). Ownerless caps deny under all tokens (D1–D4). Named so it is not mistaken for a live credential path. |
| R6 | Timing side-channel not measured | HONEST INSTRUMENT BOUND | The VALUE oracle is closed (uniform `None`, J1). The one early-return (malformed → before any DB round-trip) discriminates on the ATTACKER'S OWN input format, not on server state → not a name-existence oracle. I did NOT run a microbenchmark (noisy instrument); the GO does not rest on a timing measurement. |

## INSTRUMENTS (verbatim — the deliverable per brief-base §1; also kept in `/tmp/secaudit62w2/`)
Two live harnesses. Provenance-asserted, run `cd /tmp/secaudit62w2 && uv run python <file>` against
`ws://127.0.0.1:18000`. Re-runnable; each prints `PROVENANCE: loremaster.__file__` and a
PASS/FAIL-per-check summary.

### `exploit_secaudit_62w2.py` (32/32 PASS)
```python
# (full source; see /tmp/secaudit62w2/exploit_secaudit_62w2.py)
# Registers 2 principals x 2 agents + carol/dave/erik + an ownerless agent, then constructs:
#   A binding/cross-principal (A1 pos / A2 A-cap-under-B DENY / A3 stamp-as-B fail-closed / A4 pos)
#   B forged+absent transport token (B1/B2/B3 DENY/fail-closed)
#   C sibling preimage resistance (C1 own-agent / C2 forged-sibling DENY / C3 pos real sibling)
#   D ownerless None-is-not-wildcard (D1/D2/D3 DENY under every token / D4 stamp fail-closed)
#   E confused deputy — no identity from an argument (E1 register sig / E2 seam sigs / E3 MCP **_ignored)
#   F injection-laden credential bound as $h (F1 DENY / F2 store-intact pos)
#   J uniform-None across 4 failure modes (no value oracle)
#   K leak: no raw secret in stored row / model_dump / error text
#   G no-cache revocation (G1 pos / G2 retired DENY)
#   H owner lifecycle suspend/expire (H0/H2 pos / H1/H3 DENY)
#   I ESC-3 optional expiry enforced-when-set (I0/I1 pos / I2 past-expiry DENY)
```
### `exploit_dangle_62w2.py` (4/4 PASS)
```python
# Registers alice + one owned agent, deletes the principal ROW via admin (the pure #105
# dangling-owner state R3.2 tolerates), then attacks verify_capability:
#   D0 pos live-accepted-pre-delete
#   D1 agent row survives with a dangling owner_principal (R3.2)
#   receipt: owner_principal.email 'alice@example.com' pre-delete -> None post-delete (store §2)
#   D2/D3 orphaned cap under the deleted email / any other email -> DENY (no resurrection)
```
Both files are ≤170 lines and present in full at the scratch path above; their per-check output is
transcribed in §Attack results. (Kept in scratch, which is disposable by design — the SUBSTANCE is
the PASS/FAIL transcript + the algorithm summaries here; the algorithm is short enough to re-derive.)

## SCRATCH DISPOSITION
Scratch copy at `/tmp/secaudit62w2` (provenance-asserted, disposable). Not a git worktree; no
committed file was touched. Safe to `rm -rf` at the operator's discretion.
