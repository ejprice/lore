# REPORT-coldaudit-62w2 — packet 62 wave 2 COLD AUDIT (the per-agent capability / anti-spoofing mechanism)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — VERDICT **GO**.
- receipt: fresh-context REFUTE cold audit. Every gate re-run by ME (not relayed); the load-bearing
  dirty-store migration proven LIVE on 3.2.4; 6 mutation proofs re-discriminated in a
  provenance-asserted scratch copy with a positive-control baseline; removed-behavior dual adjudicated.
- **Graded: 66b5fa4 · HEAD-at-report: 66b5fa4 · SAME.** (Build committed at HEAD; lore index at
  `git_ref 66b5fa4`.)
- Packages considered: none — no new mechanism specified by an auditor (I verify, I do not build).
  The build itself adds no external dependency (stdlib `secrets`/`hashlib`-via-`sha512_hex`,
  `str.partition`); confirmed by reading the diff.
- Reuse ledger: none — the auditor introduced no new symbol (scratch probes only, pasted verbatim §Instruments).
- Graded verdict: **GO** — every gate passes on MY re-run, the mutation proofs discriminate, the
  removed-behavior dual holds (no dropped edge), the dirty-store migration holds LIVE on 3.2.4.
- deviations from the builder's numbers: **ONE** — the builder's blast count **1452** does not
  reproduce against the exact 16 files its report names; MY independent count is **1388/0** for those
  16 files (1452 = 1388 + the 64 contract tests folded in). 0 failures either way — a REPORTING
  discrepancy, not a defect (§Gate re-run, R1).
- decisions-needed: none blocking. 2 residuals for the lead (create-only owner-stamp confirmation
  already flagged by the builder; one security-lane hand-off) — §Residuals.
- receipt pointers: gates §Gate re-run; live migration §Live dirty-store migration (probe verbatim);
  mutation proofs §Mutation proofs (harness verbatim); removed-behavior §Removed-behavior dual;
  structural correctness §Correctness frontier.

## Capability check (tool honesty)
Brief demanded: re-run gates (`uv run pytest -n auto`, `scripts/typecheck.sh`, `ruff`), a live store
at `ws://127.0.0.1:18000`, `scripts/scratch_copy.sh`, lore tools, read-only diff audit. All available
and used. The lore MCP tools loaded via `ToolSearch "+lore"`; `lore_impact`/`lore_index` used for the
`agent_of` consumer set + index-currency check (index at HEAD `66b5fa4`, last_sweep 45s — fresh, no
reconcile needed). One grep fallback SAID OUT LOUD: the old-deny-label sweep and the parse edge-case
enumeration are non-symbol textual seams (string literals / prose), the legitimate grep case (3) — not
a structure question lore owns. Edited nothing committed (scratch + this report only).

## What I graded
The wave-2 build committed at HEAD `66b5fa4` ("feat(62): wave-2 identity mechanism"): the 10 files in
that commit (`agents.py`, `owner_stamp.py` [new], `principal_keys.py`, `principals.py`, `server.py`,
`store/surreal_schema.py`, `token_verifier.py`, `loremaster/__init__.py`, `lorerunes/credentials.py`
[new], `lorerunes/__init__.py`), against the spec (`docs/design/2026-08-24-packet62-agent-identity-rulings.md`
v5 WAVE-2 ADDENDUM) and the 3 contract files. Frame: CORRECTNESS + the removed-behavior dual + the
store/migration (the §9 threat model is the dedicated security-auditor's lane — not duplicated here).

## Gate re-run (MY passed-COUNTs, real tree @ 66b5fa4)
| gate | builder claimed | MY re-run | verdict |
|---|---|---|---|
| 3 wave-2 contract files | 64/0 | **64 passed / 0** in 8.31s | ✅ matches |
| lorerunes | 170/0 | **170 passed / 0** in 4.19s | ✅ matches |
| blast (the 16 files its report NAMES) | 1452/0 | **1388 passed / 0** in 41.90s | ⚠ count differs, 0 fail |
| `scripts/typecheck.sh` (7 legs) | Success / 0 mypy | **Success, 0 mypy errors** (all 7 legs + shellcheck) | ✅ matches |
| `uv run ruff check .` | clean | **All checks passed!** | ✅ matches |

**R1 — the blast discrepancy, run to ground (the "'I verified it' is a claim about a SCOPE" law).**
`pytest --collect-only` over the exact 16 files the builder's §Gates lists = **1388 tests collected**,
and my run passes all 1388 with 0 failed / 0 skipped / 0 deselected. `1452 − 1388 = 64` = the contract
count. So the builder folded the 3 contract files into the "blast" invocation (19 files) and reported
the combined total as "blast 1452". **It is a mis-scoped report line, not a test failure** — the
critical fact (0 regressions anywhere, PrincipalKeyStore included) is unchanged. Specifically the
`parse_credential` extraction's regression target `test_principal_keys_store.py` = **30 tests, all
green** (independently: 0 regression).

## Removed-behavior dual (the `parse_credential` extraction is a DELETE/REPLACE — P8d)
The inline `PrincipalKeyStore.verify` parse (`principal_keys.py:519–525` pre-`66b5fa4`) was replaced by
a call to the shared `lorerunes.parse_credential`. I enumerated the OLD inline logic and adjudicated
every branch/edge against the extracted predicate:

| OLD inline behaviour | extracted `parse_credential` | verdict |
|---|---|---|
| `is_blank(presented)` → deny | `if is_blank(presented): return None` | **preserved** (byte-exact) |
| `partition(":")`, `not separator` → deny | `if not separator: return None` (FIRST colon) | **preserved** |
| `is_blank(name) or is_blank(secret)` → deny | same, `return None` | **preserved** |
| well-formed → proceed with (name, secret) | `return name, secret` | **preserved** |
| deny REASON labels `malformed-no-colon` / `malformed-blank-half` | collapsed to one `malformed-credential` | **dropped-deliberately** (see below) |

Edge cases I checked by construction (`::`, trailing `:`, leading `:`, `a:b:c` name-with-colon-secret,
whitespace-surrounded half): **every one maps to the identical fate** old vs new — first-colon split
keeps the secret's tail, blank-half rejected, whitespace-real bytes NOT blank. **No dropped edge.**

The deny-label collapse: the reason is a **laundered DEBUG-only label** (`_deny(...)` logs `extra=
{"reason": ...}`, never surfaced to the caller; `verify` returns a uniform `None`). Grep of the WHOLE
repo (`.py` + `.md`) for `malformed-no-colon` / `malformed-blank-half` → **one hit, in an ARCHIVED
receipt** (`docs/plans/v2/receipts/2026-08-21-packet39-recut/REPORT-cold-audit-39-w23.md`), a dated
historical record, NOT a live consumer. No test asserts the old labels. Collapse is safe.

**Sharing proven by MUTATION, not routing** (§Mutation proofs, proof b): breaking the ONE
`lorerunes/credentials.py::parse_credential` source reds BOTH `PrincipalKeyStore.verify` AND
`verify_capability` happy-paths — a shared source, not two clones wearing one name. The identity pins
(`principal_keys.parse_credential is lorerunes.parse_credential` AND `agents.parse_credential is
lorerunes.parse_credential`) + the per-consumer routing mutations (with a positive control at
seams:240) close ROUTING-IS-NOT-SHARING.

**Critical no-NameError check:** the new `verify` discards the parse tuple (`if parse_credential(...)
is None`); I confirmed the subsequent code uses `sha512_hex(presented)` (WHOLE string) for the hash
lookup and `row[_COL_NAME]` for the key name — it never references the parsed `name`/`secret`, so the
discard is safe (`principal_keys.py:538–552`).

## Live dirty-store migration (#107/#131 blind spot — proven on the REAL 3.2.4 store)
A green virgin-DB suite cannot see a "new field on a POPULATED table" defect. I built a DIRTY agent
store BY HAND on `spike-surreal ws://127.0.0.1:18000` (NEVER :18500) — independent of the contract
fixture — and proved the field-add migrates. Probe **PASSED, all positive controls fired**
(`/tmp/ca62w2_dirty_store_probe.py`, verbatim §Instruments; DB `lore_test/test_3568_…`):

- OLD slice (capability stripped) applied → **2 legacy agent rows** written UNDER it (no capability field).
- FULL `generate_agent_ddl()` applied over the populated table (field-add `OVERWRITE` + UNIQUE index
  `IF NOT EXISTS`) → **clean**, no crash despite multiple NONE `capability_hash` rows (§1.8).
- legacy rows **survive**; `capability_hash` / `capability_expires_at` / `owner_principal` read back
  **None** (explicit projection, store §2).
- **NO WRITE-POISON**: `UPDATE … SET last_note` on a legacy row **succeeds** — the `option<>` vs
  required discriminator (a required `capability_hash` would raise `Expected string but found NONE`).
- POSITIVE CONTROL 1: a **duplicate real** `capability_hash` is **REJECTED** (`InternalError`) — the
  UNIQUE index enforces.
- POSITIVE CONTROL 2: a 3rd NONE-capability row is **accepted** (count=3 coexist) — §1.8 holds.
- `capability_expires_at` is a real settable `datetime` column (ESC-3 seam is not decorative).

DDL clause rule is correct against store §1.1/§1.4: `capability_hash` `option<string>` via
`_define_field` ⇒ `DEFINE FIELD OVERWRITE`; `capability_expires_at` `option<datetime>` same; the index
is `_unique_index` ⇒ `IF NOT EXISTS` (NEVER `OVERWRITE` an index). The contract's own migration pins
(`test_agent_capability.py:348/369`) correctly write the legacy row UNDER the old DDL then migrate —
they do NOT fall into the store §1.4 "legacy row written after the DDL" trap.

## Mutation proofs (re-run independently in a provenance-asserted scratch copy)
Scratch: `scripts/scratch_copy.sh /tmp/scratch-ca62w2` — **`loremaster.__file__ =
/tmp/scratch-ca62w2/loremaster/loremaster/__init__.py`** (INSIDE scratch; #140 provenance verified).
Positive-control baseline: the 8 target pins run GREEN on the clean scratch BEFORE any mutation.
Harness `/tmp/ca62w2_mutation_proofs.py` (verbatim §Instruments): each edit LANDING-asserted (#194),
the pin must RUN (ran=1/2, never "no tests ran") and go RED, then restore → GREEN. **All 6
discriminated:**

| # | break (scratch) | pin | result |
|---|---|---|---|
| a-i | binding cond-3 → `if False:` | `test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token` | ran=1, **RED**→restored GREEN |
| a-ii | cond-3 AND cond-4 None-permissive | `test_an_ownerless_agents_capability_is_denied` | ran=1, **RED**→GREEN |
| b | SHARED `lorerunes` parse → always None | BOTH `…resolves_the_agent` + `…verify_returns_the_owning_principal_and_key_name` | ran=2, **BOTH RED**→GREEN |
| c | retired-check → `if False:` | `test_a_retired_agents_capability_is_denied_next_call_no_cache` | ran=1, **RED**→GREEN |
| d | re-register returns a rotated capability | `test_re_register_does_not_rotate_a_live_secret` | ran=1, **RED**→GREEN |
| e-ii | leak capability into `last_note` (rendered col) | `test_a_secret_shaped_value_never_appears_in_a_rendered_agent` | ran=1, **RED**→GREEN |

Notes:
- **a-ii confirms the builder's defense-in-depth claim**: an ownerless agent is denied by BOTH cond-3
  (NONE owner_email) AND cond-4 (NONE owner_status ≠ active), so BOTH must be made permissive to red
  the pin — a single-condition skip does NOT open the ownerless door. Reproduced, as the builder measured.
- **c / "no-cache"**: the retired-check break is my RED discriminator for the revocation leg; the
  "no cache" property itself is STRUCTURAL and I verified it by reading — `verify_capability` issues a
  fresh `await self._query(...)` on every call with NO memoisation / instance cache (`agents.py:911–938`).
- **e-i** (`test_the_agent_model_has_no_capability_or_hash_or_secret_field`) is a static guard; GREEN in
  the baseline and structural (`Agent.model_fields` carries no `capability`/`capability_hash`/`secret`).

## Correctness frontier (my lane — findings)
1. **`extra="forbid"` × new columns — the dangerous case, HANDLED.** `Agent` is `extra="forbid"` and the
   agent row gained 3 columns. If `_row_to_agent` splatted the row, EVERY read would crash (or leak the
   hash). It does NOT: it maps column-by-column via `row.get(_COL_X)` (`agents.py:_row_to_agent`), so the
   new columns never reach the model — from `SELECT *` (fleet/get_agent) OR an explicit projection. Both
   the legacy-read (column absent) and the populated-hash case are safe. This is also why the no-leak pin
   holds structurally.
2. **`agent_of` stays None + nothing depends on it.** `lore_impact` at HEAD: `agent_of` = **0 production
   references** / 6 test. The diff changed only its docstring; the body (`claims = access_token.claims;
   …`) is unchanged. Verified a real agentless token reads None (contract `test_agent_of_returns_none_for_
   an_agentless_token`, GREEN). No consumer relies on it being populated.
3. **The binding compares two EMAILS, correctly.** `access_token.subject` = `principal.email` in BOTH
   mint paths (`token_verifier.py:310` api-key, `:338` Google), and cond-3 compares it to
   `owner_principal.email` (the same normalised email off the same principal record). Semantically sound,
   fail-closed on NONE/empty either side (`agents.py:940`).
4. **Atomic mint.** `capability_hash = sha512_hex(capability)` is in the SAME `CREATE … CONTENT` as the
   row (`agents.py:714–723`) — a failed create leaves no half-minted row. Raw secret returned ONCE,
   never persisted. Confirmed the mint fires on `agent_registry.register` ONLY (server.py:6532), NOT on
   the unrelated tool/chunker `self._registry.register` (a different object).
5. **Re-register preserves owner + secret (no silent late-stamp).** The re-register UPDATE
   (`agents.py:787–806`) touches status/heartbeat/model/task_id/spawned_by/cadence/status_set_at only —
   NOT `owner_principal` and NOT `capability_hash`. An ownerless agent STAYS ownerless; an owned agent
   keeps its owner; the live secret is not rotated. Matches spec W2.3 mint-once-on-create.
6. **No F3a leak pre-cutover.** The register tool renders `result.agent` only (`_render_comms_register`,
   server.py:6558) — never `result.capability` — and calls `register` WITHOUT `owner_principal_id`. So at
   HEAD the mechanism is genuinely UNSERVED: a capability is minted (hash stored) but neither delivered
   nor rendered. Correct commit-only state.
7. **Reach seam is INSTRUMENT-0 compliant.** `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` keys are checked
   EQUAL to the governed set DERIVED from `partition_tools_by_population` over the live registry (not a
   hand-list); the anti-vacuity pin guards the empty-set case; the grown-set discriminator proves a new
   governed tool reds the coverage (fail-closed default to `governed`). This is the reach law done right.
8. **Query plan sanity.** `verify_capability` WHERE `capability_hash = $h` is the UNIQUE-index probe
   ($h is a BOUND param — no injection); the `owner_principal.email/.status/.expires_at` are record-LINK
   dereferences (not a graph traversal — store §4's "traversal never uses an index" caveat does not
   apply). Legacy NONE-hash rows never match a real `$h` (confirmed live in the migration probe).

## Residuals (non-blocking)
- **create-only owner-stamp** (builder flag 2): CORRECT for wave 2 — contract-sufficient, mint-once
  aligned (spec W2.3), and correctly FLAGGED for operator confirmation rather than silently decided. Not
  a defect. The lead should carry the builder's "confirm at 63/64 cutover" question forward.
- **`stamp_owner` does 2 store reads** (`verify_capability` then `owner_principal_of`). Functionally
  correct (the binding already proved ownership; unserved pre-cutover). A candidate one-query fold when
  63/64 wires it. Not a defect.
- **Security-lane hand-off (NOT my frame — for the dedicated security-auditor):** when pkt-63/64/65
  wires capability DELIVERY (the register tool surfacing `.capability` to the caller + the fleet-brief
  capture), confirm the delivery channel does not log/render the raw secret. Pre-cutover there is no such
  surface (finding 6). Flagged so it is not lost across the 62→63 boundary.
- **Blast-count report line (R1):** the builder's "blast 1452/0" should read "blast 1388/0 (16 files) +
  contract 64/0". A number to correct in the record, not a failure.

## Instruments (verbatim — brief-base §1: an instrument establishing a load-bearing claim is a deliverable)

### `/tmp/ca62w2_dirty_store_probe.py` — live 3.2.4 dirty-store migration
```python
"""COLD-AUDIT independent live dirty-store migration probe — packet 62 wave 2.
Constructs a DIRTY agent store BY HAND on ws://127.0.0.1:18000 (NEVER :18500) and proves the
capability_hash/capability_expires_at field-add migrates without poisoning pre-existing rows, and
the UNIQUE index builds over a populated table carrying multiple NONE rows (store §1.4/§1.6/§1.8).
Self-checking: exits 0 ONLY if every assertion + control holds."""
from __future__ import annotations
import asyncio, sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
TESTS = Path("/home/ejprice/PycharmProjects/lore/loremaster/tests"); sys.path.insert(0, str(TESTS))
from _surreal_harness import connect_admin, make_env, run, unique_database
from loremaster.index.records import sha512_hex
from loremaster.store import surreal_schema
AGENT = surreal_schema.AGENT_TABLE; PRODUCTION_DIM = 512
def old_agent_ddl() -> str:
    kept = [s for s in surreal_schema._agent_statements() if "capability" not in s.lower()]
    return ";\n".join(kept) + ";\n"
def legacy_content(name: str) -> dict[str, object]:
    now = datetime.now(UTC)
    return {"name": name, "session": "old_sess", "role": "worker", "status": "active",
            "registered_at": now, "heartbeat_at": now}
async def main() -> int:
    fails: list[str] = []
    def check(cond, msg):
        (fails.append(msg) or print(f"  FAIL: {msg}")) if not cond else print(f"  ok:   {msg}")
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM); admin = await connect_admin(env)
    try:
        print(f"[probe] db={env.namespace}/{env.database} @ {env.url}")
        old_ddl = old_agent_ddl(); check("capability" not in old_ddl.lower(), "OLD slice has no capability_* statement")
        await run(admin, old_ddl)
        for rid, nm in (("legacy_a","legacy_agent_a"),("legacy_b","legacy_agent_b")):
            await run(admin, f"CREATE type::record('{AGENT}', '{rid}') CONTENT $c", {"c": legacy_content(nm)})
        await run(admin, surreal_schema.generate_agent_ddl())
        print("  ok:   full agent DDL (field-add + UNIQUE index) applied over 2 populated rows")
        rows = await run(admin, f"SELECT name, capability_hash, capability_expires_at, owner_principal FROM type::record('{AGENT}', 'legacy_a')")
        check(bool(rows) and rows[0]["name"]=="legacy_agent_a", "legacy_a survives migration")
        check(rows[0].get("capability_hash") is None, "legacy_a.capability_hash reads None")
        check(rows[0].get("capability_expires_at") is None, "legacy_a.capability_expires_at reads None")
        check(rows[0].get("owner_principal") is None, "legacy_a.owner_principal reads None (ownerless)")
        await run(admin, f"UPDATE type::record('{AGENT}', 'legacy_b') SET last_note = $n", {"n":"touched"})
        rows = await run(admin, f"SELECT last_note FROM type::record('{AGENT}', 'legacy_b')")
        check(bool(rows) and rows[0].get("last_note")=="touched", "legacy_b UPDATE not write-poisoned")
        real_hash = sha512_hex("newagent:supersecret-xyz")
        await run(admin, f"CREATE type::record('{AGENT}', 'newagent') CONTENT $c", {"c": {**legacy_content("newagent"), "capability_hash": real_hash}})
        rows = await run(admin, f"SELECT capability_hash FROM type::record('{AGENT}', 'newagent')")
        check(bool(rows) and rows[0].get("capability_hash")==real_hash, "new agent real hash stored + coexists")
        dup_rejected = False
        try:
            await run(admin, f"CREATE type::record('{AGENT}', 'dupagent') CONTENT $c", {"c": {**legacy_content("dupagent"), "capability_hash": real_hash}})
        except Exception as exc:
            dup_rejected = True; print(f"  ok:   duplicate real hash rejected ({type(exc).__name__})")
        check(dup_rejected, "UNIQUE index rejects a DUPLICATE real capability_hash (index enforcing)")
        await run(admin, f"CREATE type::record('{AGENT}', 'legacy_c') CONTENT $c", {"c": legacy_content("legacy_agent_c")})
        rows = await run(admin, f"SELECT count() FROM {AGENT} WHERE capability_hash IS NONE GROUP ALL")
        none_count = rows[0]["count"] if rows else 0
        check(none_count>=3, f"multiple NONE capability_hash rows coexist under UNIQUE (count={none_count})")
    finally:
        try:
            future = datetime.now(UTC) + timedelta(days=1)
            await run(admin, f"UPDATE type::record('{AGENT}', 'newagent') SET capability_expires_at = $t", {"t": future})
            rows = await run(admin, f"SELECT capability_expires_at FROM type::record('{AGENT}', 'newagent')")
            print(f"  ok:   capability_expires_at settable -> {rows[0].get('capability_expires_at')!r}")
        except Exception as exc:
            print(f"  note: expiry-set probe raised {exc!r}")
        await admin.close()
    if fails: print(f"\nPROBE FAILED — {len(fails)}: {fails}"); return 1
    print("\nPROBE PASSED — dirty-store migration holds on live 3.2.4 (all controls fired)"); return 0
if __name__ == "__main__": raise SystemExit(asyncio.run(main()))
```
Result: **PROBE PASSED** — all 12 checks + 2 positive controls fired (dup rejected `InternalError`,
NONE count=3), exit 0.

### `/tmp/ca62w2_mutation_proofs.py` — the 6 mutation proofs
(Harness: for each mutation, land the edit (old MUST be present), run the pin, assert it RAN and went
RED, restore; positive-control baseline = 8 pins GREEN on the clean scratch. Full source retained at
`/tmp/ca62w2_mutation_proofs.py`; the mutations are the table in §Mutation proofs — each a single
landing-asserted `str.replace`, run under `cwd=/tmp/scratch-ca62w2`.)
Result: **ALL 6 DISCRIMINATED** — each pin RED on its break (ran=1 or 2, never "no tests ran"), GREEN
on restore; exit 0.

## Verdict
**GO.** Every gate passes on my independent re-run (contract 64/0, lorerunes 170/0, blast 1388/0,
typecheck 0 mypy, ruff clean — 0 failures across the entire set). The `parse_credential` removed-behavior
dual holds byte-exact with no dropped edge. The dirty-store migration holds LIVE on 3.2.4 with all
positive controls firing. All 6 load-bearing security pins discriminate independently. The
`extra="forbid"` × new-column hazard, `agent_of`-stays-None, atomic mint, re-register owner preservation,
no-leak, and the INSTRUMENT-0 reach seam are all correct. Residuals are non-blocking (one report-number
correction, one already-flagged operator confirmation, one 63/64 security hand-off). Nothing found that
blocks the wave-2 commit.

## Artifacts
- Scratch copy `/tmp/scratch-ca62w2` (provenance-verified, restored byte-exact after the mutation proofs).
- Probes `/tmp/ca62w2_dirty_store_probe.py`, `/tmp/ca62w2_mutation_proofs.py` (verbatim above / retained).
- Gate log `/tmp/coldaudit-62w2-gates.log`. Edited nothing committed.
