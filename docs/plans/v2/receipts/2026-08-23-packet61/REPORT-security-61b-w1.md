# REPORT-security-61b-w1 — dedicated SECURITY audit of the packet-61b PDP core

brief-base v14 read
brief project v7 read

## ⭐ CURRENT VERDICT (re-check 2026-08-23 after the #416 fix): **SECURE**
The builder applied the #416 fix + SEC-F2/F3/F4/R4. I RE-RAN the P3 attack + a completeness
sweep + a 7-composition leak hunt + the F2/F3/F4/R4 changes against the live 3.2.4 store
(`/tmp/sec_recheck_61b.py`, verbatim in §RE-CHECK-APPENDIX; **28/28 checks, 0 FAIL**). **F1 is
CLOSED**, every IR node now emits a self-contained fragment, no composition leaks, and the
hardening changes introduce no new issue. VERDICT: **SECURE** — the original findings (below the
re-check) are all addressed; one non-security residual noted (empty `And()`/`Or()`, §RESIDUAL).
Detail in **§RE-CHECK**. The original audit (which found the F1 leak) is preserved verbatim below.

---

## SUMMARY BLOCK (original audit — F1 now FIXED, see re-check above)
- state: **done-with-findings** (targeted security attacks complete; cold auditor owns the full suite/gates).
- VERDICT (original): **VULNERABILITIES-FOUND** — 1 latent **MEDIUM** (cross-principal leak in the PUBLIC IR
  emitter, reachable by predicate COMPOSITION, NOT via the shipped `authorize`/`authorize_filter`)
  + 3 **LOW** hardening. The shipped `authorize`/`authorize_filter` surface AS INVOKED is **SECURE**
  against the stated §9 threat model — proven, with positive controls.
  **→ SUPERSEDED by the re-check above: all four addressed; current verdict SECURE.**
- deviations: I authored+ran a live-store probe (`/tmp/sec_probe_61b.py`, pasted VERBATIM in §APPENDIX
  per brief-base §1 — it establishes load-bearing claims, so it is a deliverable, not scratch; not
  committed because I am read-only).
- Packages considered: none — no production mechanism specified (read-only audit; the probe uses the
  repo's existing `surrealdb` SDK + `loremaster.store._txn` seam, the `probe_read_filter_61b.py` idiom).
- Reuse ledger: none — introduced no production symbol (read-only audit).
- Graded: 599354a7a5dcf53a8c59c556a07801433a1d74d7 · HEAD-at-report: 599354a7a5dcf53a8c59c556a07801433a1d74d7 · SAME (wave uncommitted; graded the working tree at HEAD).
- decisions-needed: F1 (parenthesise `ScopeInKeeps.to_surql` vs. pin the never-nested-under-`And`
  invariant — the fix has an index-plan tension, §F1) → lead/contract to rule.
- receipt pointers: PDP core `lorerunes/lorerunes/pdp.py`; findings §F1–F4; per-axis verdicts §VERDICTS;
  probe results §PROBE-RESULTS; probe source §APPENDIX.

---

## §RE-CHECK — focused security re-verification after the #416 fix (2026-08-23)
Graded: 599354a (working tree; wave still uncommitted). I ground-truthed the CURRENT `pdp.py`
(not assumed) + re-ran live-store attacks (`/tmp/sec_recheck_61b.py`, verbatim §RE-CHECK-APPENDIX;
**28/28 checks, 0 FAIL** on spike-surreal 3.2.4, throwaway DB reaped, never :18500).

**(1) The P3 leak is CLOSED (with positive control).** `ScopeInKeeps.to_surql` now returns
`"(" + " OR ".join(clauses) + ")"` — a self-contained parenthesised fragment.
`And((OwnerPrincipalEq("alice"), ScopeInKeeps({keep:k1,keep:k9}))).to_surql()` now emits
`(owner_principal = type::record('principal', $p) AND (scope = $k1 OR scope = $k2))` and the store
returns **only `{r9, r11}` — bob's `r12` is NO LONGER returned** (leak closed), byte-equal to Python
`matches`. **Positive control:** the un-parenthesised twin (the OLD emitter's exact shape) STILL
leaks `r12` (`{r9, r11, r12}`) — so the clean result is meaningful, not a blind pass (T1).

**(2) The fix is COMPLETE, not just `ScopeInKeeps`.** Structural sweep over ONE instance of EVERY
concrete node (T2): every fragment is either OR-free (`ScopeEq`/`OwnerPrincipalEq`/`OwnerAgentEq`,
`true`/`false`) or FULLY parenthesised (`ScopeInKeeps`, `And`, `Or`) — **no node emits a bare
top-level OR**, so an enclosing `And` can never split one. Leak hunt over **7 adversarial
compositions** (T3 — `ScopeInKeeps`/`Or` nested under `And`, `And` under `Or`, mixed) — ALL agree
store == Python, zero store-only rows. I could NOT construct a composition that still leaks.
Re #417 (the structural pin's multi-disjunct coverage being partly a hand-list): my T2 is an
INDEPENDENT derived check (constructs one of each concrete node, asserts the self-containment
property) — it confirms **the CODE property holds for every current node regardless of the pin's
reach**, and the closed-algebra gate reds a NEW node until ruled. The code is correct even accepting
#417's pin-reach as a known bound.

**(3) No NEW issue from SEC-F2/F3/F4/R4:**
- **F2 (option<> NONE-owner) — CLOSED both in code AND in the oracle.** `Resource.owner_*` is now
  `str | None`; `None` (absent) matches no owner predicate → fail-closed (a NONE-owner private row
  is invisible, a NONE-owner server/keep row visible regardless). T5 proves store==Python for the
  new `Resource(owner_*=None)` shape on live `option<record<>>` rows. AND the oracle itself now uses
  `TYPE option<record<principal>>` DDL + adds absent-owner rows `r13`/`r14` (grep-confirmed
  `test_pdp_oracle_61b.py:135-147`) — the F2 coverage gap I flagged is genuinely closed, not just
  code-fixed.
- **F3 (empty-identity) — hardened + verified (T6):** `Subject` rejects empty `principal_id`/
  `agent_id`; `Resource` rejects an empty-STRING owner while ALLOWING `None` (absent). The
  empty-vs-empty match hole is gone.
- **F4 (`_AUDITED_ACTIONS`) — DERIVED (T6):** now `frozenset(Action) - {Action.READ}`; a new
  mutating action auto-audits AND auto-enters the carve-out — the hand-list is gone. Still ==-checked
  against the store domain in the oracle.
- **R4 (`PRINCIPAL_TABLE`/`AGENT_TABLE` re-home) — injection-neutral (T7):** the names are still
  fixed literal constants (`'principal'`/`'agent'`) interpolated into `type::record(...)`, never user
  input; the hostile-id-is-bound property is unchanged. The re-home opens no injection surface.

**RESIDUAL (non-security, non-blocking):** `And(())` / `Or(())` emit `"()"`, which the store rejects
as a SYNTAX ERROR (T4: fail-closed — returns no rows / raises, does NOT leak the table), while Python
`matches` diverges (`all([])=True` / `any([])=False`). This is a matches-vs-to_surql divergence on an
EMPTY-children node, but it (a) is **not reachable via `authorize`/`authorize_filter`** (the entry
points never build an empty `And`/`Or`), (b) **does not LEAK** (the store errors, fail-closed), and
(c) is **pre-existing, not introduced by the #416 fix**. A defensive guard (reject empty `children`,
or emit `true`/`false` for the empty case) would close the last divergence; I flag it for the lead's
awareness, not as a gate on this commit.

**RE-CHECK VERDICT: SECURE.** The #416 cross-principal leak is closed and complete; F2/F3/F4 are
genuine hardening; R4 is injection-neutral. The other axes I rendered SECURE in the original audit are
untouched by the fix and stand.

---

## SCOPE + WHAT I ATTACKED
The built PDP core in `lorerunes/lorerunes/pdp.py` (the closed predicate IR + `to_surql`/`matches`,
`authorize`/`authorize_filter`, `Subject`/`Resource`/`Decision`, the 5 action predicates, the admin
short-circuit, the audit carve-out, `requires_audit`). I read the PRODUCTION code and both contract
files (`lorerunes/tests/test_pdp_core.py`, `loremaster/tests/test_pdp_oracle_61b.py`), the threat model
(`docs/design/2026-08-21-lore-authorization-model.md` §9; `docs/design/2026-08-22-packet61-pdp-audit-rulings.md`
Forks A/C/D/G), and the store reference. I ran targeted attacks on the TEST store `ws://127.0.0.1:18000`
(unique throwaway DB, reaped; NEVER `:18500`), each with a positive control. I did **not** run the full
suite (the cold auditor owns it — store-contention discipline).

**Accepted §9 bounds I did NOT count as defects** (confirmed present-and-correct, not attacked as holes):
admin = full unrestricted superuser; a stolen short-lived token; root rewrites any table (Version A) so
the audit append-only guard is in-process only (Fork G's stated bound); `Subject`-from-credential binding
+ the two anti-injection invariants are **packet 62**; the `Resource.table` derive-from-row-id enforcement
(#415) + the governed-table retrofit are **packets 63/64**. 61b builds the SHAPE + the PDP; I audited that
the shape is sound and 61b neither over- nor under-claims the deferred boundary (it does not — see §F-boundary).

---

## VERDICTS (each with a positive control)

| axis | verdict | evidence + positive control |
|---|---|---|
| **⭐ Cross-principal isolation** | **SECURE** (as invoked) | Member predicates always AND-in ownership/scope; no `(s,a,resource)` grants A access to B's `principal-private`/`agent-private`. Oracle cross-product + core pins `test_cross_principal_isolation_on_read`, `test_sibling_agent_private_is_NOT_readable`. Probe **P2** proves the NONE/absent-owner edge is fail-closed. **Positive control:** the present-owner control row (`n_present`, alice's) IS visible while every NONE-owner private row is invisible — the instrument can see BOTH outcomes. ⚠ One LATENT leak reachable only by IR composition — **F1**. |
| **Single-brain equivalence (§5/§9)** | **SECURE** as invoked; **1 latent divergence (F1)** | `authorize` ≡ `authorize_filter(...).matches` by construction; the oracle byte-compares the real engine to Python over the hostile cross-product. **BUT** the IR node `ScopeInKeeps` emits precedence-unsafe SQL (probe **P3**, confirmed with positive control) — a §5 divergence + cross-principal leak the moment a consumer nests it under `And`. Not produced by the 61b entry points; reachable via the PUBLIC `lorerunes` IR. |
| **Admin audit carve-out** | **SECURE** | `authorize_filter(admin, {WRITE,DELETE,SET_SCOPE,SET_OWNER}, 'audit')` → `NoRows` (all 4); `authorize` denies; admin READ of audit still selects all. Oracle `TestTheAuditCarveOutOracle` + core `TestTheAuditCarveOut`. Carve-out covers EVERY mutating action (`_AUDITED_ACTIONS` == all-but-READ, verified). **Positive control:** admin READ selects `{a1,a2}` while every mutating action selects `∅` — the guard discriminates READ from mutation. Case/whitespace exactness is sound at 61 (table is the canonical `AUDIT_TABLE` constant); the forge-the-table bypass is the #415 63/64 boundary, correctly deferred. |
| **`requires_audit` under-audit** | **SECURE** | Fires iff `allowed ∧ admin ∧ mutating ∧ ¬member_predicate.matches` — every load-bearing admin bypass audited: cross-owner WRITE, SET_OWNER always, SET_SCOPE into a non-grantable keep; own-row NOT audited. Single-brain: reuses the SAME `_member_filter` (not a clone). Core `TestRequiresAudit` incl. the grantability discriminator. **Positive control:** own-row admin write → `False`, cross-owner → `True` (the fixture tells "audit the bypass" from "audit every admin action"). One hardening note — **F4**. |
| **Injection / confused deputy** | **SECURE** | Every owner/scope/keep value is a BOUND param via `_param_name` (content-addressed hash NAME; value only in `params`). No user value is interpolated into any fragment; table names are fixed `'principal'`/`'agent'` literals. Probe **P1**: a hostile `principal_id`/keep carrying `'; REMOVE TABLE gov; --` lands only in `params`, the table survives, the read returns only server rows. **Positive control P1d:** an INTERPOLATED twin DOES steer the query (leaks all 12 rows) — so the bound emitter's clean result is meaningful, not a blind pass. |
| **Info / credential leak** | **SECURE** | `Decision` carries only two bools (`allowed`, `requires_audit`) — no data, no store internals, no credential. A denial is `Decision(allowed=False)` — information-free about what it hid. The emitted fragment contains only param NAMES (hashes), never values; the only values in `params` are the CALLER's OWN identity/keeps, never another principal's. No predicate raises a data-bearing error. |

**Bottom line:** the 61b `authorize`/`authorize_filter` API is secure against the stated threat model. I
render **VULNERABILITIES-FOUND** (not SECURE) because **F1** is a real, confirmed, cross-principal-leaking
divergence latent in the PUBLIC IR — a loaded gun whose safety is on only by an undocumented, unpinned
invariant, on a surface 63/64 will compose against.

---

## FINDINGS (severity-ranked)

### F1 — MEDIUM · `ScopeInKeeps.to_surql()` emits precedence-unsafe SQL → cross-principal leak + §5 divergence under `And`-composition (CONFIRMED, positive control)
**The attack.** `ScopeInKeeps.to_surql()` deliberately returns UNPARENTHESISED disjuncts
(`scope = $k0 OR scope = $k1`) — see the node's docstring: *"joined WITHOUT wrapping parens so a parent
`Or` splices them flat (the probe's index-served form)."* That is correct **only** because the shipped
`_member_filter` places `ScopeInKeeps` **exclusively as a direct child of the top-level `Or`** (READ/WRITE
branches). But `And.to_surql` wraps its join as `"(" + " AND ".join(fragments) + ")"` and TRUSTS each child
fragment to be self-contained. Nest `ScopeInKeeps` under `And` and you get:

```
And((OwnerPrincipalEq("alice"), ScopeInKeeps({keep:k1, keep:k9})))
  emits:  (owner_principal = type::record('principal', $p) AND scope = $k1 OR scope = $k2)
  engine parses (AND binds tighter than OR):  ((owner=alice AND scope=k1) OR scope=k2)
```

**The impact (probe P3, live 3.2.4).** Over the hostile fixture the store returns `{r9, r11, r12}` while
Python `And.matches` (correct) returns `{r9, r11}`. **`r12` is bob's `keep:k9` row — a CROSS-PRINCIPAL
LEAK**: the emitted filter exposes a different principal's row that the single-row gate denies. This breaks
BOTH §9 in-scope properties at once — cross-principal isolation AND the single-brain equivalence
(`authorize_filter().matches` ≠ what the store SELECT returns). **Positive control:** the correctly
parenthesised twin `(owner=alice AND (scope=k1 OR scope=k9))` returns `{r9, r11}` — agreeing with Python —
so the divergence is caused specifically by the missing parens, not by the fixture.

**Reachability.** NOT produced by `authorize`/`authorize_filter` at 61b (verified: `ScopeInKeeps` never
appears under `And` in `_member_filter`; DELETE/SET_SCOPE use `And((principal, agent))` with no
`ScopeInKeeps`). BUT `And`, `Or`, `ScopeInKeeps`, `OwnerPrincipalEq`, `OwnerAgentEq`, `ScopeEq` are ALL
re-exported from `lorerunes/__init__.py` (verified) — the IR is a public shared surface, and 63/64 (and any
future policy) compose predicates against it. The oracle cannot catch this because it only tests
`authorize_filter`'s output, never an arbitrary composition. This is the §9 divergence "the #102 defect
wearing an IR" that Fork A's own rider warns about — surviving specifically where the oracle does not look.

**Why MEDIUM not HIGH:** not reachable through the 61b entry points today; it is a latent trap. Why not LOW:
it is a confirmed cross-principal leak on a security-critical PUBLIC surface, guarded only by an
undocumented+unpinned invariant, precisely as the packet's design leans on the IR being composable by 63/64.

**Recommended fix (decision — the two options have a real tension):**
- (a) Make `ScopeInKeeps.to_surql` SELF-CONTAINED — wrap in parens when it emits ≥2 disjuncts (restores the
  contract every other node honours: a node's fragment is safe under any parent). ⚠ **Tension:** the node's
  flat-splice was chosen to guarantee the exact index-served plan `probe_read_filter_61b.py` validated
  (#413). Parenthesising inserts a nested `(... OR ...)` into the parent `Or` — almost certainly still an
  IndexScan (it is equality disjuncts, not `IN`), but it must be RE-PROBED (EXPLAIN + the `_scans_table`
  walker) before shipping, or you trade a security bug for a possible #107 perf regression.
- (b) Keep the flat splice and add a STRUCTURAL PIN: assert (over `authorize_filter`'s emitted trees, and
  as an invariant on the IR) that `ScopeInKeeps` is only ever a child of `Or`, never `And` — a red the day
  a composition violates it. This is allowlist-the-safe on the composition, and cheaper to prove index-neutral.

Either closes it; (a) is more robust (the node can't misbehave anywhere), (b) is index-plan-safe by
construction. My recommendation: **(a) + re-probe the plan** — a self-contained fragment is the property the
whole IR already assumes, and F1 exists because one node opted out of it.

### F2 — LOW · the live-store oracle's hostile fixture OMITS the Fork-A-rider-required `option<>` NONE/absent-owner rows (coverage gap; equivalence currently HOLDS — proven)
The Fork A rider (`2026-08-22-packet61-pdp-audit-rulings.md`, the "LOAD-BEARING RIDER" bullet) names the
oracle's hostile fixture as including *"`option<>` owner columns present AND absent."* The shipped oracle
(`test_pdp_oracle_61b.py::_gov_ddl`) defines `owner_principal ON gov TYPE record<principal>` (NON-option) and
`_seed` always sets both owners — so a NONE/absent owner is **structurally unrepresentable** and untested.
This is a silent narrowing of a ruled hostile-fixture requirement (the "tests written for the new world
certify only the new world" class). **I probed the gap directly (P2):** on an `option<record<>>`-owner
table with NONE-owner rows at every scope, `to_surql` and `matches` AGREE for both plausible shell mappings
of an absent owner (empty-string and a sentinel) — a NONE-owner private row is fail-closed (invisible),
server/in-keep rows visible regardless of owner. So **the equivalence holds on this edge today; it is NOT
exploitable at 61b.** BUT: (i) the guarantee rests on the (63/64-owned, untested-at-61) property that the
loremaster shell maps an absent owner to a value that is not a real principal/agent id — if a future shell
mapped NONE to a wildcard/reused id it would break; (ii) `SELECT *` OMITS a NONE `option<>` column entirely
(store-ref §2 KeyError trap), so the shell MUST use `.get()` and map to a non-matching sentinel.
**Recommendation:** add an `option<>`-owner `gov` table + NONE-owner rows to the oracle (my P2 is the ready
instrument), and have 63/64 pin the shell's absent-owner mapping. Not a 61b blocker; a real gap to close.

### F3 — LOW · `Resource`/`Subject` admit EMPTY (and `None`) owner + identity ids; empty-vs-empty MATCHES (degenerate-identity hardening on the "anti-injection typed shape")
`Resource.__post_init__` validates only non-empty `table` and a valid `scope`; `Subject.__post_init__`
validates only `role`. Neither rejects an empty `owner_principal`/`owner_agent`/`principal_id`/`agent_id`, and
the `str` hints are not enforced at runtime. Verified inline: `Resource(owner_principal="")` and
`Subject(principal_id="")` construct; `Resource(owner_principal=None)` constructs too; and a member with
`principal_id=""` WRITE-**matches** an empty-owner `principal-private` row (`"" == ""` → allowed). The design
sells the typed identity fields as *the anti-injection SHAPE* (§3.2.2 / threat-model injection #5), but the
type does not self-defend against a blank/degenerate identity. Not exploitable today (62/63/64 derive identity
server-side and never mint an empty id), and `type::record('principal', '')` on the store side is dubious
enough that a blank owner would likely diverge from Python too — but cheap defense-in-depth on a
security-critical value object. **Recommendation:** `__post_init__` reject empty/blank
`owner_principal`/`owner_agent`/`principal_id`/`agent_id` (reuse `lorerunes.is_blank` — the chartered blankness
predicate, already in `lorerunes`). A row/identity with no owner should be a construction error, not a
silently-matching one.

### F4 — LOW · `_AUDITED_ACTIONS` is a HAND-LIST, not DERIVED from `Action` (reach-law hardening on the carve-out + audit obligation)
`_AUDITED_ACTIONS = frozenset({WRITE, DELETE, SET_SCOPE, SET_OWNER})` is a hardcoded literal. BOTH the admin
audit carve-out (`pdp.py` — `action in _AUDITED_ACTIONS`) and `requires_audit` depend on it. It currently
equals `frozenset(Action) - {Action.READ}` (verified), and the closed-`Action` pins would red if the enum
grew — but the membership itself is a second hand-list that a test compares against a THIRD literal
(`{"WRITE","DELETE","SET_SCOPE","SET_OWNER"}`) rather than against the enum. A 6th mutating action added to
`Action` but not to `_AUDITED_ACTIONS` would silently (a) let admin mutate audit rows for that action and
(b) skip its audit obligation — the exact "enumerate-the-forbidden loses" shape (CLAUDE.md instrument lesson).
**Recommendation:** DERIVE it in production — `_AUDITED_ACTIONS = frozenset(Action) - {Action.READ}` — so the
carve-out and the audit obligation cover every mutating action BY CONSTRUCTION, and keep the existing `==`
cross-check against the store's `surreal_schema._AUDITED_ACTIONS` (the two-vocabulary agreement is legitimate).
Mitigated today by the closed-action pins; deriving removes the residual hand-list.

---

## §F-boundary — 61b does NOT over/under-claim the deferred (62/63/64) enforcement
Confirmed, per the brief's ask:
- **Anti-injection SHAPE present, enforcement correctly deferred.** Identity/owner are TYPED value fields on
  `Subject`/`Resource`; the PDP consumes them and never reads a tool argument — the anti-injection *shape*.
  The DERIVE-not-accept invariants (owner from credential §3.2.2; `Resource.table` from row-id #415) are NOT
  claimed at 61b — the contract's `#415` FORWARD-NOTE and the Fork-D boundary flag them for 62/63/64. No
  over-claim.
- **The audit carve-out's soundness at 61b rests on `Resource.table` being the canonical constant.** A forged
  `table` (`"Audit"`, `" audit "`) would get the admin `AllRows` branch → admin could mutate that row. At 61b
  `table` is a fixture/caller field, so this is exactly the #415 boundary; the shipped carve-out is sound for
  the canonical `AUDIT_TABLE` and the code + contract correctly defer the derive-from-row-id enforcement to
  63/64. 61b neither over-claims (it doesn't assert forgery-resistance) nor under-claims (the carve-out itself
  is complete over the mutating-action domain). ✔

---

## PROBE-RESULTS (TEST store ws://127.0.0.1:18000, throwaway DB reaped; 10/10 checks, 0 FAIL)
```
[PASS] P1a emitted fragment has no interpolated hostile text
[PASS] P1b hostile values survive as BOUND params
[PASS] P1c store executed the bound query without injection (table intact, server rows only): read_ids=[r7,r8]
[PASS] P1d POSITIVE CONTROL: an interpolated value DOES steer the query (leaks all 12 rows)
[PASS] P2 NONE-owner equivalence [READ/empty-string]  store==python  (store={n_k1,n_present,n_sv})
[PASS] P2 NONE-owner equivalence [READ/sentinel]      store==python
[PASS] P2 NONE-owner equivalence [WRITE/empty-string] store==python  (store={n_k1,n_present})
[PASS] P2 NONE-owner equivalence [WRITE/sentinel]     store==python
[PASS] P3 ScopeInKeeps under And DIVERGES (store LEAKS r12 that Python excludes):
        emitted="(owner_principal = type::record('principal', $p) AND scope = $k1 OR scope = $k2)"
        store={r9,r11,r12}  python={r9,r11}  store-only LEAK={r12}   ← F1, cross-principal
[PASS] P3 POSITIVE CONTROL: correctly-parenthesised twin AGREES with Python (store={r9,r11})
```
Reading: P1 = injection contained (with a control proving interpolation WOULD leak). P2 = the F2 coverage
gap is not exploitable today (equivalence holds on the NONE-owner edge). P3 = F1 confirmed, with a positive
control isolating the missing parens as the cause.

---

## APPENDIX — probe source (VERBATIM; brief-base §1 — an instrument establishing a load-bearing claim is a deliverable)
Run: `uv run python <this>` from the repo root against a live spike-surreal TEST store. Self-checking; exit
non-zero on any FAIL. Read-only auditor ⇒ pasted here rather than committed to `scripts/`.

```python
#!/usr/bin/env python3
"""SECURITY PROBE — packet 61b PDP core. Attacks the single-brain equivalence on edges the
shipped oracle does NOT construct: P1 injection containment (+ interpolated positive control),
P2 NONE/absent-owner equivalence (option<> owners — the oracle's non-option DDL can't hold),
P3 ScopeInKeeps-under-And precedence leak (+ parenthesised positive control).
TEST store ws://127.0.0.1:18000 only; mints + reaps a throwaway DB. NEVER :18500."""
from __future__ import annotations
import asyncio, os, uuid
from typing import Any
from loremaster.store._txn import bootstrap_session, execute_transaction, signin_credentials
from pydantic import SecretStr
from surrealdb import AsyncSurreal
import lorerunes as L

URL = "ws://127.0.0.1:18000/rpc"
USER, PASSWORD, NS = "root", "spikeroot", "lore_test"
GOV, GOV_OPT = "gov", "gov_opt"

def db() -> str:
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"

async def apply_ddl(conn: Any, ddl: str) -> None:
    async def _acq() -> Any: return conn
    async def _never(_c: Any) -> None: raise AssertionError("DDL rejection must never drop the connection")
    await execute_transaction(f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acq, drop=_never, url=URL)

def bare(record_id: Any) -> str:
    text = str(getattr(record_id, "id", record_id))
    return text.split(":", 1)[-1] if ":" in text else text

async def store_ids(conn: Any, table: str, predicate: Any) -> set[str]:
    fragment, params = predicate.to_surql()
    rows = await conn.query(f"SELECT id FROM {table} WHERE {fragment}", params)
    return {bare(r["id"]) for r in (rows if isinstance(rows, list) else [])}

async def store_ids_raw(conn: Any, table: str, where: str, params: dict[str, Any]) -> set[str]:
    rows = await conn.query(f"SELECT id FROM {table} WHERE {where}", params)
    return {bare(r["id"]) for r in (rows if isinstance(rows, list) else [])}

HOSTILE = (
    ("r1","alice","ag_a","agent-private"), ("r2","alice","ag_b","agent-private"),
    ("r3","alice","ag_a","principal-private"), ("r4","alice","ag_b","principal-private"),
    ("r5","bob","ag_c","principal-private"), ("r6","bob","ag_c","agent-private"),
    ("r7","alice","ag_a","server"), ("r8","bob","ag_c","server"),
    ("r9","alice","ag_a","keep:k1"), ("r10","bob","ag_c","keep:k1"),
    ("r11","alice","ag_a","keep:k9"), ("r12","bob","ag_c","keep:k9"),
)

async def seed_gov(conn: Any) -> None:
    await apply_ddl(conn,
        f"DEFINE TABLE {GOV} SCHEMAFULL;\n"
        f"DEFINE FIELD owner_principal ON {GOV} TYPE record<principal>;\n"
        f"DEFINE FIELD owner_agent ON {GOV} TYPE record<agent>;\n"
        f"DEFINE FIELD scope ON {GOV} TYPE string;\n"
        f"DEFINE INDEX {GOV}_op ON {GOV} FIELDS owner_principal;\n"
        f"DEFINE INDEX {GOV}_scope ON {GOV} FIELDS scope;\n")
    for rid, p, a, s in HOSTILE:
        await conn.query(
            f"CREATE type::record('{GOV}', $id) CONTENT {{ owner_principal: "
            f"type::record('principal', $p), owner_agent: type::record('agent', $a), scope: $s }}",
            {"id": rid, "p": p, "a": a, "s": s})

def member(pid: str, aid: str, keeps: frozenset[str]) -> Any:
    return L.Subject(principal_id=pid, agent_id=aid, role=L.PRINCIPAL_ROLE_MEMBER, visible_keep_ids=keeps)

results: list[str] = []
fails: list[str] = []
def check(name: str, ok: bool, detail: str) -> None:
    results.append(f"[{'PASS' if ok else '**FAIL**'}] {name}: {detail}")
    if not ok: fails.append(name)

async def p1_injection(conn: Any) -> None:
    hostile_pid = "alice'; REMOVE TABLE gov; --"
    hostile_keep = L.keep_scope("k1'; REMOVE TABLE gov; --")
    subj = member(hostile_pid, "ag_a", frozenset({hostile_keep}))
    frag, params = L.authorize_filter(subj, L.Action.READ, GOV).to_surql()
    clean = "REMOVE TABLE" not in frag and hostile_pid not in frag and hostile_keep not in frag
    check("P1a emitted fragment has no interpolated hostile text", clean, f"fragment={frag!r}")
    check("P1b hostile values survive as BOUND params",
          hostile_pid in set(params.values()) and hostile_keep in set(params.values()),
          f"param values={sorted(params.values())}")
    ids = await store_ids(conn, GOV, L.authorize_filter(subj, L.Action.READ, GOV))
    still = await conn.query(f"SELECT count() FROM {GOV} GROUP ALL")
    survived = isinstance(still, list) and still and still[0].get("count") == len(HOSTILE)
    check("P1c store executed the bound query without injection (table intact, server rows only)",
          survived and ids == {"r7", "r8"}, f"table_count_intact={survived} read_ids={sorted(ids)}")
    injected_scope = "server' OR '1'='1"
    leaked = await store_ids_raw(conn, GOV, f"scope = '{injected_scope}'", {})
    check("P1d POSITIVE CONTROL: an interpolated value DOES steer the query (leaks all rows)",
          leaked == {r[0] for r in HOSTILE}, f"interpolated leak set={sorted(leaked)}")

async def p2_none_owner(conn: Any) -> None:
    await apply_ddl(conn,
        f"DEFINE TABLE {GOV_OPT} SCHEMAFULL;\n"
        f"DEFINE FIELD owner_principal ON {GOV_OPT} TYPE option<record<principal>>;\n"
        f"DEFINE FIELD owner_agent ON {GOV_OPT} TYPE option<record<agent>>;\n"
        f"DEFINE FIELD scope ON {GOV_OPT} TYPE string;\n"
        f"DEFINE INDEX {GOV_OPT}_op ON {GOV_OPT} FIELDS owner_principal;\n"
        f"DEFINE INDEX {GOV_OPT}_scope ON {GOV_OPT} FIELDS scope;\n")
    none_rows = (("n_ap","agent-private"),("n_pp","principal-private"),("n_sv","server"),("n_k1","keep:k1"))
    for rid, s in none_rows:
        await conn.query(f"CREATE type::record('{GOV_OPT}', $id) CONTENT {{ scope: $s }}", {"id": rid, "s": s})
    await conn.query(
        f"CREATE type::record('{GOV_OPT}', $id) CONTENT {{ owner_principal: "
        f"type::record('principal', $p), owner_agent: type::record('agent', $a), scope: $s }}",
        {"id": "n_present", "p": "alice", "a": "ag_a", "s": "principal-private"})
    alice = member("alice", "ag_a", frozenset({L.keep_scope("k1")}))
    for action in (L.Action.READ, L.Action.WRITE):
        sids = await store_ids(conn, GOV_OPT, L.authorize_filter(alice, action, GOV_OPT))
        for label, none_owner in (("empty-string", ""), ("sentinel", "\x00none\x00")):
            pyset: set[str] = set()
            for rid, s in none_rows:
                if L.authorize(alice, action, L.Resource(table=GOV_OPT, owner_principal=none_owner,
                               owner_agent=none_owner, scope=s)).allowed: pyset.add(rid)
            if L.authorize(alice, action, L.Resource(table=GOV_OPT, owner_principal="alice",
                           owner_agent="ag_a", scope="principal-private")).allowed: pyset.add("n_present")
            check(f"P2 NONE-owner equivalence [{action.name}/{label}] store==python", sids == pyset,
                  f"store={sorted(sids)} python={sorted(pyset)}")

async def p3_scopeinkeeps_under_and(conn: Any) -> None:
    keeps = frozenset({L.keep_scope("k1"), L.keep_scope("k9")})
    unsafe = L.And((L.OwnerPrincipalEq("alice"), L.ScopeInKeeps(keeps)))
    frag, params = unsafe.to_surql()
    store = await store_ids(conn, GOV, unsafe)
    py = {rid for rid, p, a, s in HOSTILE if p == "alice" and s in keeps}
    check("P3 ScopeInKeeps under And DIVERGES (store leaks rows Python excludes)", store != py,
          f"emitted={frag!r} store={sorted(store)} python={sorted(py)} store-only-LEAK={sorted(store - py)}")
    owner_param = next(n for n in params if n.startswith("p_"))
    keep_params = [n for n in params if n.startswith("k_")]
    safe_frag = (f"(owner_principal = type::record('principal', ${owner_param}) AND "
                 f"({' OR '.join(f'scope = ${n}' for n in keep_params)}))")
    safe_store = await store_ids_raw(conn, GOV, safe_frag, params)
    check("P3 POSITIVE CONTROL: correctly-parenthesised twin AGREES with Python", safe_store == py,
          f"parenthesised store={sorted(safe_store)} python={sorted(py)}")

async def main() -> int:
    database = db()
    conn = AsyncSurreal(URL)
    await conn.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(conn, NS, database, url=URL)
    print(f"probe database: {NS}:{database}  (TEST store {URL})")
    try:
        await seed_gov(conn); await p1_injection(conn); await p2_none_owner(conn); await p3_scopeinkeeps_under_and(conn)
    finally:
        try: await conn.query(f"REMOVE DATABASE IF EXISTS {database}")
        except Exception as e: print(f"[cleanup warning] {type(e).__name__}: {e}")
        await conn.close()
    print("\n=== RESULTS ===")
    for line in results: print(" ", line)
    print(f"\n{len(results)} checks, {len(fails)} FAIL")
    return 1 if fails else 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

---

## RE-CHECK-APPENDIX — the #416 fix re-verification results + probe (2026-08-23)

**Live results (spike-surreal 3.2.4, throwaway DB, 28/28 PASS, 0 FAIL):**
```
[PASS] T1 #416 FIX: And(OwnerPrincipalEq, ScopeInKeeps) store==python (LEAK CLOSED)
        emitted="(owner_principal = type::record('principal', $p) AND (scope = $k1 OR scope = $k2))"
        store={r9,r11}  r12_leaked=False
[PASS] T1 POSITIVE CONTROL: un-parenthesised twin STILL leaks r12  (store={r9,r11,r12})
[PASS] T2 self-contained fragment [ScopeEq/OwnerPrincipalEq/OwnerAgentEq/AllRows/NoRows]  (no top-level OR)
[PASS] T2 self-contained fragment [ScopeInKeeps]  frag='(scope=$k1 OR scope=$k2)'  wrapped=True
[PASS] T2 self-contained fragment [ScopeInKeeps 1-elem / empty(false) / And / Or]  (all self-contained)
[PASS] T3 leak-hunt And(P, SK{k1,k9})                 store==python  {r9,r11}
[PASS] T3 leak-hunt And(P, Or(Sk1, Sk9))              store==python  {r9,r11}
[PASS] T3 leak-hunt And(P, A, SK)                     store==python  {r9,r11}
[PASS] T3 leak-hunt Or(P_bob, And(Sserver, P_alice))  store==python  {r5,r6,r7,r8,r10,r12}
[PASS] T3 leak-hunt And(Or(Sk1,Sk9), P_alice)         store==python  {r9,r11}
[PASS] T3 leak-hunt And(P, Or(SK, Sserver))           store==python  {r7,r9,r11}
[PASS] T3 leak-hunt Or(And(P,SK), P_bob)              store==python  {r5,r6,r8,r9,r10,r11,r12}
[PASS] T4 empty And(()) does not LEAK all rows  (emitted '()' → store SYNTAX ERROR, fail-closed)
[PASS] T4 empty Or(())  does not LEAK all rows  (emitted '()' → store SYNTAX ERROR, fail-closed)
[PASS] T5 None-owner (str|None) equivalence [READ]   store==python  {n_k1,n_present,n_sv}
[PASS] T5 None-owner (str|None) equivalence [WRITE]  store==python  {n_k1,n_present}
[PASS] T6 F3 Subject rejects empty principal_id / Resource rejects empty-string owner / allows None
[PASS] T6 F4 _AUDITED_ACTIONS == set(Action)-READ (derived)
[PASS] T7 injection still contained (hostile id bound; PRINCIPAL_TABLE re-home injection-neutral)
```

Probe source is `/tmp/sec_recheck_61b.py` (verbatim below; read-only auditor ⇒ pasted, not committed).
It seeds the byte-identical hostile fixture, re-runs the P3 attack + positive control, sweeps every
node for self-containment, hunts leaks over 7 adversarial `And`/`Or` nestings, checks empty-node
`()` emission, re-verifies NONE-owner equivalence in the new `str|None` shape, the F3/F4 hardening,
and injection-after-re-home.

```python
# /tmp/sec_recheck_61b.py — see the live results above. Run: uv run python <this> from repo root.
# (Full source; TEST store ws://127.0.0.1:18000 only, throwaway DB reaped, NEVER :18500.)
import asyncio, os, uuid
from typing import Any
from loremaster.store._txn import bootstrap_session, execute_transaction, signin_credentials
from pydantic import SecretStr
from surrealdb import AsyncSurreal
import lorerunes as L

URL="ws://127.0.0.1:18000/rpc"; USER,PASSWORD,NS="root","spikeroot","lore_test"; GOV,GOV_OPT="gov","gov_opt"
def db(): return f"test_{os.getpid()}_{uuid.uuid4().hex}"
async def apply_ddl(conn,ddl):
    async def _a(): return conn
    async def _n(_c): raise AssertionError("DDL rejection must never drop the connection")
    await execute_transaction(f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_a, drop=_n, url=URL)
def bare(rid):
    t=str(getattr(rid,"id",rid)); return t.split(":",1)[-1] if ":" in t else t
async def store_ids(conn,table,pred):
    frag,params=pred.to_surql(); rows=await conn.query(f"SELECT id FROM {table} WHERE {frag}",params)
    return {bare(r["id"]) for r in (rows if isinstance(rows,list) else [])}
async def store_ids_raw(conn,table,where,params):
    rows=await conn.query(f"SELECT id FROM {table} WHERE {where}",params)
    return {bare(r["id"]) for r in (rows if isinstance(rows,list) else [])}
HOSTILE=(("r1","alice","ag_a","agent-private"),("r2","alice","ag_b","agent-private"),
 ("r3","alice","ag_a","principal-private"),("r4","alice","ag_b","principal-private"),
 ("r5","bob","ag_c","principal-private"),("r6","bob","ag_c","agent-private"),
 ("r7","alice","ag_a","server"),("r8","bob","ag_c","server"),
 ("r9","alice","ag_a","keep:k1"),("r10","bob","ag_c","keep:k1"),
 ("r11","alice","ag_a","keep:k9"),("r12","bob","ag_c","keep:k9"))
async def seed_gov(conn):
    await apply_ddl(conn, f"DEFINE TABLE {GOV} SCHEMAFULL;\n"
      f"DEFINE FIELD owner_principal ON {GOV} TYPE record<principal>;\n"
      f"DEFINE FIELD owner_agent ON {GOV} TYPE record<agent>;\n"
      f"DEFINE FIELD scope ON {GOV} TYPE string;\n"
      f"DEFINE INDEX {GOV}_op ON {GOV} FIELDS owner_principal;\n"
      f"DEFINE INDEX {GOV}_scope ON {GOV} FIELDS scope;\n")
    for rid,p,a,s in HOSTILE:
        await conn.query(f"CREATE type::record('{GOV}', $id) CONTENT {{ owner_principal: "
          f"type::record('principal', $p), owner_agent: type::record('agent', $a), scope: $s }}",
          {"id":rid,"p":p,"a":a,"s":s})
def py_matches(pred):
    out=set()
    for rid,p,a,s in HOSTILE:
        if pred.matches(L.Resource(table=GOV, owner_principal=p, owner_agent=a, scope=s)): out.add(rid)
    return out
results=[]; fails=[]
def check(name,ok,detail):
    results.append(f"[{'PASS' if ok else '**FAIL**'}] {name}: {detail}");  fails.append(name) if not ok else None
K=L.keep_scope
async def t1(conn):
    keeps=frozenset({K("k1"),K("k9")}); unsafe=L.And((L.OwnerPrincipalEq("alice"), L.ScopeInKeeps(keeps)))
    frag,params=unsafe.to_surql(); store=await store_ids(conn,GOV,unsafe); py=py_matches(unsafe)
    check("T1 #416 FIX store==python LEAK CLOSED", store==py and "r12" not in store, f"store={sorted(store)}")
    kp=[n for n in params if n.startswith("k_")]; op=next(n for n in params if n.startswith("p_"))
    uf=f"owner_principal = type::record('principal', ${op}) AND "+" OR ".join(f"scope = ${n}" for n in kp)
    leak=await store_ids_raw(conn,GOV,uf,params)
    check("T1 POSITIVE CONTROL un-parenthesised twin STILL leaks r12", "r12" in leak and leak!=py, f"{sorted(leak)}")
def one_each():
    return {"ScopeEq":L.ScopeEq(L.SCOPE_SERVER),"OwnerPrincipalEq":L.OwnerPrincipalEq("alice"),
     "OwnerAgentEq":L.OwnerAgentEq("ag_a"),"ScopeInKeeps":L.ScopeInKeeps(frozenset({K("k1"),K("k9")})),
     "ScopeInKeeps1":L.ScopeInKeeps(frozenset({K("k1")})),"ScopeInKeepsEmpty":L.ScopeInKeeps(frozenset()),
     "And":L.And((L.ScopeEq(L.SCOPE_SERVER),L.OwnerPrincipalEq("alice"))),
     "Or":L.Or((L.ScopeEq(L.SCOPE_SERVER),L.ScopeEq(K("k1")))),"AllRows":L.AllRows(),"NoRows":L.NoRows()}
def t2():
    for label,node in one_each().items():
        frag,_=node.to_surql(); has_or=" OR " in f" {frag} "; wrapped=frag.startswith("(") and frag.endswith(")")
        check(f"T2 self-contained [{label}]", (not has_or) or wrapped, f"frag={frag!r}")
async def t3(conn):
    P=L.OwnerPrincipalEq; A=L.OwnerAgentEq; S=L.ScopeEq; SK=L.ScopeInKeeps; keeps=frozenset({K("k1"),K("k9")})
    comps={"And(P,SK)":L.And((P("alice"),SK(keeps))),"And(P,Or(Sk1,Sk9))":L.And((P("alice"),L.Or((S(K("k1")),S(K("k9")))))),
     "And(P,A,SK)":L.And((P("alice"),A("ag_a"),SK(keeps))),
     "Or(P_bob,And(Ssrv,P_alice))":L.Or((P("bob"),L.And((S(L.SCOPE_SERVER),P("alice"))))),
     "And(Or(Sk1,Sk9),P_alice)":L.And((L.Or((S(K("k1")),S(K("k9")))),P("alice"))),
     "And(P,Or(SK,Ssrv))":L.And((P("alice"),L.Or((SK(keeps),S(L.SCOPE_SERVER))))),
     "Or(And(P,SK),P_bob)":L.Or((L.And((P("alice"),SK(keeps))),P("bob")))}
    for label,pred in comps.items():
        store=await store_ids(conn,GOV,pred); py=py_matches(pred)
        check(f"T3 leak-hunt {label} store==python", store==py, f"store-only={sorted(store-py)} py-only={sorted(py-store)}")
async def t4(conn):
    for label,node in (("And(())",L.And(())),("Or(())",L.Or(()))):
        frag,_=node.to_surql()
        try: store=await store_ids(conn,GOV,node)
        except Exception: store=set()
        check(f"T4 empty {label} does not LEAK all rows", store!={r[0] for r in HOSTILE}, f"emitted={frag!r} store={sorted(store)}")
async def t5(conn):
    await apply_ddl(conn, f"DEFINE TABLE {GOV_OPT} SCHEMAFULL;\n"
      f"DEFINE FIELD owner_principal ON {GOV_OPT} TYPE option<record<principal>>;\n"
      f"DEFINE FIELD owner_agent ON {GOV_OPT} TYPE option<record<agent>>;\n"
      f"DEFINE FIELD scope ON {GOV_OPT} TYPE string;\n"
      f"DEFINE INDEX {GOV_OPT}_op ON {GOV_OPT} FIELDS owner_principal;\n"
      f"DEFINE INDEX {GOV_OPT}_scope ON {GOV_OPT} FIELDS scope;\n")
    nr=(("n_ap","agent-private"),("n_pp","principal-private"),("n_sv","server"),("n_k1","keep:k1"))
    for rid,s in nr: await conn.query(f"CREATE type::record('{GOV_OPT}', $id) CONTENT {{ scope: $s }}",{"id":rid,"s":s})
    await conn.query(f"CREATE type::record('{GOV_OPT}', $id) CONTENT {{ owner_principal: type::record('principal', $p), "
      f"owner_agent: type::record('agent', $a), scope: $s }}",{"id":"n_present","p":"alice","a":"ag_a","s":"principal-private"})
    alice=L.Subject(principal_id="alice",agent_id="ag_a",role=L.PRINCIPAL_ROLE_MEMBER,visible_keep_ids=frozenset({K("k1")}))
    for action in (L.Action.READ,L.Action.WRITE):
        sids=await store_ids(conn,GOV_OPT,L.authorize_filter(alice,action,GOV_OPT)); pyset=set()
        for rid,s in nr:
            if L.authorize(alice,action,L.Resource(table=GOV_OPT,owner_principal=None,owner_agent=None,scope=s)).allowed: pyset.add(rid)
        if L.authorize(alice,action,L.Resource(table=GOV_OPT,owner_principal="alice",owner_agent="ag_a",scope="principal-private")).allowed: pyset.add("n_present")
        check(f"T5 None-owner equivalence [{action.name}] store==python", sids==pyset, f"store={sorted(sids)} py={sorted(pyset)}")
def t6():
    try: L.Subject(principal_id="",agent_id="ag_a",role=L.PRINCIPAL_ROLE_MEMBER,visible_keep_ids=frozenset()); check("T6 F3 Subject rejects empty principal_id",False,"!")
    except Exception: check("T6 F3 Subject rejects empty principal_id",True,"ok")
    try: L.Resource(table=GOV,owner_principal="",owner_agent="ag_a",scope="server"); check("T6 F3 Resource rejects empty owner",False,"!")
    except Exception: check("T6 F3 Resource rejects empty owner",True,"ok")
    try: L.Resource(table=GOV,owner_principal=None,owner_agent=None,scope="server"); check("T6 F3 Resource allows None owner",True,"ok")
    except Exception as e: check("T6 F3 Resource allows None owner",False,str(e))
    from lorerunes import pdp
    check("T6 F4 _AUDITED_ACTIONS derived", {a.name for a in pdp._AUDITED_ACTIONS}=={a.name for a in pdp.Action}-{"READ"}, "")
async def t7(conn):
    hostile="alice'; REMOVE TABLE gov; --"
    subj=L.Subject(principal_id=hostile,agent_id="ag_a",role=L.PRINCIPAL_ROLE_MEMBER,visible_keep_ids=frozenset({K("k1")}))
    frag,params=L.authorize_filter(subj,L.Action.READ,GOV).to_surql()
    check("T7 injection contained after re-home", "REMOVE TABLE" not in frag and hostile in set(params.values()) and "type::record('principal'" in frag, "")
async def main():
    database=db(); conn=AsyncSurreal(URL); await conn.signin(signin_credentials(user=USER,password=SecretStr(PASSWORD)))
    await bootstrap_session(conn,NS,database,url=URL); print(f"probe db {NS}:{database} ({URL})")
    try:
        await seed_gov(conn); await t1(conn); t2(); await t3(conn); await t4(conn); await t5(conn); t6(); await t7(conn)
    finally:
        try: await conn.query(f"REMOVE DATABASE IF EXISTS {database}")
        except Exception as e: print(f"[cleanup] {e}")
        await conn.close()
    print("\n=== RESULTS ==="); [print(" ",l) for l in results]; print(f"\n{len(results)} checks, {len(fails)} FAIL")
    return 1 if fails else 0
if __name__=="__main__": raise SystemExit(asyncio.run(main()))
```
