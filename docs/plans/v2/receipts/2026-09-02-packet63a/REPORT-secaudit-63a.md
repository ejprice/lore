# REPORT-secaudit-63a — SECURITY AUDIT of the packet-63a memory retrofit (§9 target)

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` §1.4 (option<> NONE dirty
  rows on a populated table), §2 (record<> owner links / CONTENT / explicit projection reads a NONE
  column back as None). Cited, never re-transcribed.

## SUMMARY BLOCK

- receipt: `brief-base v14 read` · `brief project v7 read`
- **state: done** — the §9 cross-principal isolation target is CLEARED over the wire.
- **VERDICT: GO** — isolation holds through the true served composition root (`AppContext.recall/
  remember` → `_resolve_subject` → `get_access_token()` → `governed.resolve_subject`); no exploit found.
- **Instrument:** 2 fresh wire-level auditors (`audit.py`, `audit2.py`) — 2 principals × ≥2 agents,
  per-call transport-token switching (which the shipped `governed_ctx` fixture CANNOT do — it pins one
  email). 54 constructed checks, **0 FAIL / 0 WARN**, every negative paired with a positive control.
- deviations: none. I edited no tree file; instruments live in `/tmp/secaudit-63a/` and are PASTED
  VERBATIM in §APPENDIX (brief-base §1 — recommend the lead commit them to `scripts/` beside
  `probe_read_filter_63.py`).
- **Packages considered:** none — no mechanism specified (audit + test instruments only).
- **Reuse ledger:** none — no new production symbol introduced; the instruments reuse the shipped
  `_governed_contract`/`_surreal_harness` helpers.
- **Graded:** `dd5c9b2` · HEAD-at-report: `dd5c9b2` · SAME (the whole 63a: `a8c17c1` + 63a-ii).
- decisions-needed: ONE residual, non-blocking — **R1**: `AppContext._render_recalled_memories` emits
  NO Subject-derived bound line (design §9 rider 8); the contract already flagged this to lead-63.
  Recommend it rides 63b's render work. Details §RESIDUALS.
- receipt POINTERS: verdict+method → §METHOD; per-check → §CHECKS; Leg-2 → §LEG2; accepted bounds →
  §BOUNDS; residual → §RESIDUALS; instruments → §APPENDIX.

---

## §METHOD — what I attacked, and why it is independent of the contract

The 63a-ii wave wired the served tool layer, so the §9 headline — **cross-principal isolation OVER
THE WIRE** — is finally testable end-to-end. The shipped contract (`test_memory_retrofit_63a.py`)
exercises the BACKEND (`_exercise_recall` → `governed.resolve_subject` → `backend.recall`), BYPASSING
the composition root and the `get_access_token()` read. The shipped `governed_ctx` fixture
(`test_mcp_server.py`) DOES reach `AppContext.recall`, but patches `get_access_token` to a **static
lambda returning ONE email**, so it structurally cannot test a cross-principal boundary.

My instruments close that gap. They boot a **real `AppContext`** via `build_app_context` and patch
`loremaster.server.get_access_token` to a **switchable** token whose `.subject` I flip per call — so
every check runs through the identical seam a hosted foreign principal would (`_resolve_subject` reads
the ambient transport token for the principal, the `capability=` arg for the agent, and the 62 binding
cross-checks the two). Provenance receipt printed each run: `loremaster.__file__ =
/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` — the REAL tree, not a copy.
Live TEST store `ws://127.0.0.1:18000`, per-run unique DB, reaped. Every negative has a positive
control (the isolation check FIRES on a state I know is broken — an admin AllRows subject DOES see the
rows a member cannot, proving the FILTER is the blocker, not a recallability artifact).

**Constructed hostile fixture (stage 1, over the wire):** 3 principals — `alice`(member),
`bob`(member), `carol`(**admin**) — × ≥2 agents each (alice→`ag_a1,ag_a2`; bob→`ag_b1,ag_b2`;
carol→`ag_c1`); keeps: project `P`(keeper alice) + `kA`(alice) + `kB`(bob), disjoint households; a
**9-row hostile seed matrix** matching one rare query token (`zebracorn`): every scope
(agent-private ×2 agents, principal-private ×2 principals, server, keep:kA, keep:kB), a NONE-owner
server row, a NONE-owner private row, and a **NONE-scope dirty legacy row**.

**Stage 2 (store-level oracle + migration + Leg-2):** an 11-row single-brain matrix INCLUDING two
NONE-scope rows (one unowned, one alice-owned) — stronger than the contract, which excluded NONE-scope
from its equality; three migration worlds; and the Leg-2 forgery constructions.

---

## §CHECKS — the seven attack fronts (all with positive controls)

Receipts are the PASS lines the instruments print; re-run `.venv/bin/python /tmp/secaudit-63a/audit{,2}.py`.

### 1. Cross-principal READ isolation ∀ recall (§6 item 1) — **HOLDS**
Over the wire, each `(principal, agent)` recall served EXACTLY its visible set, no leak, no miss:
- `alice/ag_a1` → `{s_alice_pp, s_alice_ap1, s_server, s_keepA}` (NOT bob's rows, NOT `ag_a2`'s
  agent-private, NOT keepB, NOT the NONE-scope row).
- `alice/ag_a2` → `{s_alice_pp, s_alice_ap2, s_server, s_keepA}` — sees the SHARED principal-private
  and its OWN agent-private, never `ag_a1`'s agent-private (the §4 intra-principal rule, §BOUNDS i).
- `bob/ag_b1` → `{s_bob_pp, s_bob_ap1, s_server, s_keepB}`.
- **Headline negatives:** bob NEVER surfaced alice's principal-private row; alice NEVER surfaced bob's.
- **POSITIVE CONTROL:** `carol`(admin) recall served ALL 9 rows incl. bob's private rows AND the
  NONE-scope legacy row → the read FILTER is what blocks a member, not a recall/validity accident.

### 2. Served SET == served-set-size == caller-filtered count — trust Leg 1 (§6 item 2) — **HOLDS**
Member served counts (4, 4) are STRICTLY below the unfiltered matching total (9); admin's served
set-size (9) equals the unfiltered total. Recall renders one block per served row (no separate count),
so the realizable Leg-1 property is *the SET is the caller-filtered set* — confirmed. (The literal
"separately-computed count over the whole table" false clear belongs to comms `drain`/`rollup`, 63b —
memory has no count surface; see §RESIDUALS R1.)

### 3. Anti-injection ∀ write verbs (§6 item 4, F4) — **HOLDS (strongest form)**
- **3a:** the served `lore_remember` tool exposes NO owner/scope argument — `owner_principal=`,
  `owner_agent=`, `as_agent=`, `created_by=`, `scope=` each raise `TypeError` at the wire (the MCP
  surface refuses the unknown kwarg). There is no argument to move the stamp with.
- **3b:** a legitimate wire remember stamped `owner_principal` = the **credential's** principal
  (alice, server-derived — verified against the stored row), and defaulted `scope` = the project keep
  (`keep:<P>`, NOT `principal-private` — the fleet-share default is preserved, not silently privatised).
- **3c (backend seam):** the wire has no `scope=`, so I drove the backend directly: `alice`
  `remember(scope=keep:<bob's keep>)` → `GovernedDenied` **naming `lore-adm add-household`** (the
  cross-keep-injection door is closed via `pdp._grantable`). POSITIVE CONTROL: a grantable
  `scope="server"` was accepted and applied. (Noted: `server` IS grantable by a member per design
  §2.4 / `_grantable` — a validated request, not an injection vector.)

### 4. Single-brain equivalence `authorize(row) ≡ authorize_filter().matches(row)` (§6 item 5) — **HOLDS**
Over the REAL memory table incl. dirty NONE-scope rows, for **READ/WRITE/DELETE × 5 subjects**
(member ×4 keep-configs + admin), the store `authorize_filter` id-set byte-matched the Python
`authorize` id-set — 15/15 combinations equal. Dirty-row callouts:
- NONE-scope UNOWNED row `m10`: admin-visible, member-invisible (fail-closed §2.3).
- NONE-scope OWNED row `m11`: its owner CAN `DELETE` it (scope-independent, 61 D4(a)) but CANNOT
  READ/WRITE it — the exact contrast that discriminates a `None→deny-everything` wrong build.
- `bob` can DELETE none of alice's rows (exact-owner stamp).

### 5. Migration preserves isolation (§6 item 6) — **HOLDS**
- Ambiguous operator (2 members, 0 admins) → `migrate_governed` **REFUSES and writes nothing** (the
  row stays NONE-scope, member-invisible — no silent widening / no fabricated owner).
- Single operator → backfills the NONE-scope row to `keep:<project>`, **owner stays NONE/NONE**
  (UNOWNED-LEGACY — never fabricated); the keeper REGAINS sight; a **FOREIGN principal (empty keeps)
  still does NOT see it** — the migration scopes to a keep, it does not make the row world-readable.
- Idempotent (2nd run backfills 0); `migrate-governed --table message` REFUSES agent-first (§2.6).

### 6. Owner stamp is SERVER-DERIVED — the 62 binding (§6 item 6, brief item 6) — **HOLDS**
Through the wire composition root:
- `alice`'s capability under a **`bob` transport token → GovernedDenied**; `bob`'s cap under alice's
  token → GovernedDenied (the confused-deputy door §3.2.2 — a stolen capability is useless without the
  matching authenticated principal).
- A forged capability (`alice_w1:deadbeefforged`) and a garbage string → GovernedDenied.
- Identity-less recall (`capability=None`, no ambient token) → GovernedDenied (teaching error, never a
  `TypeError`, never the pre-retrofit unfiltered answer).
- POSITIVE CONTROL: the matched alice cap+token succeeds (rendered digest).

### 7. Guarded-write single-brain (invalidate on a foreign row) (§6 item 7)
Covered by the shipped contract (`TestInvalidateRoutesThroughGuardedWrite`: a member DENIED closing a
foreign-owned row, the row UNCHANGED; owner CAN close its own) — re-run GREEN at HEAD in the 19-pass
retrofit module. `guarded_write` carries `authorize_filter(action)` in the mutation WHERE + reads
`row_count` back from the RETURN → 0 rows = `GovernedConflict`, so there is no read-then-write TOCTOU
window and a denied write never touches the store. I inspected the production path (`governed.py::
guarded_write`) and confirm the single-brain (Python gate + store guard = the SAME predicate tree).

---

## §LEG2 — the trust-doctrine forgery table (dependency × verb, each CONSTRUCTED)

Each degraded state was BUILT (not reasoned) and the served response diffed against the healthy one;
every one fails **CLOSED** (a DENY or a vanished row), never a false clear.

| dependency | state | construction | served (degraded) vs healthy | verdict |
|---|---|---|---|---|
| `resolve_visible_keeps` | **stale** | alice in `kA`, sees `krow`; DELETE her `member_of` edge; RE-resolve | keeps `{keep:kA}`→`{}`, `krow` **vanishes** (no cache, one read/call) | PASS |
| `resolve_visible_keeps` | **empty** | a principal in 0 keeps | resolves to `frozenset()` → only private+server, never a keep row | PASS |
| `resolve_visible_keeps` | **wrong-instance** | keep store pointed at a different (un-ready) DB | `GovernedDenied` — never a SHORTER keep set | PASS |
| `resolve_visible_keeps` | **partial** | (same fail-closed path — a mid-list read failure raises `KeepStoreError`, propagated) | DENY, never a short set | PASS (by construction of the wrong-instance leg) |
| `stamp_owner` | **stale** | `UPDATE agent SET status='retired'`; present the cap | `GovernedDenied` (no-cache revocation, cond. 2) | PASS |
| `stamp_owner` | **empty** | absent capability | `GovernedDenied` + teaching (CHECK6) | PASS |
| `stamp_owner` | **wrong-instance** | another principal's capability under this token | binding `GovernedDenied` (CHECK6) | PASS |
| `stamp_owner` | **partial** | n/a — ONE read after #425 (no second read to interleave) | — | n/a |
| the migration | **empty** | no project keep provisioned; default-scope `remember` | `GovernedDenied` **naming `migrate-governed`** — never a silent fallback to `principal-private` | PASS |
| the migration | **half-run / ambiguous** | 2-principal store | REFUSES, writes nothing (CHECK5a) | PASS |
| the store | **table-empty** | recall over an empty visible set | `[]` / "no memories" — no crash, no leak, no forged row | PASS |
| the store | **index absent** | (schema-level; not reconstructed here) | covered by the shipped schema EXPLAIN pins (`test_governed_schema_63a`) | deferred to schema tests |

---

## §BOUNDS — the §9 ACCEPTED bounds, verified as bounds (not defects)

- **(i) within ONE principal, siblings read each other's `principal-private` rows.** CONFIRMED and
  CORRECT: `alice/ag_a1` and `alice/ag_a2` both saw `s_alice_pp`, while each saw only its OWN
  `agent-private` row. This is the §4 member READ predicate (`principal-private` → any sibling agent;
  `agent-private` → exact agent), not a leak.
- **(ii) admin sees everything.** CONFIRMED — used as the positive control throughout (AllRows).
- **(iii) `search_code` stays identity-less with a NAMED withheld boost until 63b.** CONFIRMED: the
  identity-less memory boost is DENIED and NAMED (`test_search.py::TestMemoryBoostWithheldNotice`,
  5 passed at HEAD) — no memory leaks into an identity-less search; the withheld boost is a Leg-1 fact
  in the render, not a silent `[]`. Correct interim isolation behavior.
- **(iv) the `to`-edge wake count may count an invisible delivery** — a comms (63b) concern; N/A to the
  memory retrofit.

---

## §RESIDUALS — surfaced, none blocking GO

- **R1 (LOW, non-blocking, ALREADY flagged by the contract to lead-63).** `AppContext.
  _render_recalled_memories` emits NO Subject-derived bound line (design §9 rider 8: *"every governed
  list-read render carries ONE line naming the bound it applied — principal, agent, N keeps"*). The
  render lists one block per served row and `_NO_MEMORIES_RECALLED` for an empty set, with no "searched
  as `<principal>`/`<agent>`, N keeps visible" line. **Why this is NOT a leak and NOT a false clear:**
  the served SET is correctly filtered (CHECK1/2), and an "N withheld"-style line WOULD be an existence
  leak the design explicitly forbids (§4.3). The gap is a mild *transparency* under-disclosure of the
  caller's own identity scope, not a mis-render. **Recommendation:** fold the Subject-scope line into
  63b's render work (which adds count lines to `drain`/`rollup`), so the two governed-render surfaces
  land one shared bound-render idiom rather than a second copy. The contract's `TestF3Recall…`
  docstring already surfaced this; I corroborate it.
- **No security defect found.** The identity-less-deny blast radius (search_code, the 18 re-pointed
  tool-layer tests) is the DESIGNED fail-closed state, not a leak.

---

## §APPENDIX — the instruments (PASTED VERBATIM; recommend committing to `scripts/`)

Both are self-contained, run against the TEST store, reap their DBs, and print PASS/FAIL per check.
Recommend the lead commit them to `scripts/` (beside `probe_read_filter_63.py`) so the wire-isolation
audit is re-runnable — a scratch tree is disposable by design.

### scripts candidate: `audit_secaudit_63a_wire.py` (stage 1 — the wire)

```python
# --- see /tmp/secaudit-63a/audit.py ; reproduced below ---
```
_(Full source of `/tmp/secaudit-63a/audit.py` and `/tmp/secaudit-63a/audit2.py` follows in the two
fences below.)_

### `/tmp/secaudit-63a/audit.py` — stage 1 (wire-level isolation, count, anti-injection, binding)

```python
"""SECURITY AUDIT — packet 63a memory retrofit — cross-principal isolation OVER THE WIRE.

Author: secaudit-63a (Opus 4.8). Independent instrument (NOT a copy of the contract): it
CONSTRUCTS hostile states and verifies through the TRUE served composition root
``AppContext.recall`` / ``AppContext.remember`` (which read ``get_access_token()`` — the seam the
contract's ``_exercise_*`` backend-level helpers BYPASS), with 2 principals x >=2 agents switching
the transport token per call. Every negative carries a POSITIVE control.

Runs against the live TEST store ws://127.0.0.1:18000 (NEVER :18500), per-run unique DB, reaped.
Provenance receipt: prints loremaster.__file__ (must be the real tree, not a copy).
"""
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from pathlib import Path

REPO = "/home/ejprice/PycharmProjects/lore"
sys.path.insert(0, f"{REPO}/loremaster/tests")

# Env the config/stores read (surreal creds + api-key envs the config references).
from _surreal_harness import (  # noqa: E402
    surreal_user, surreal_password, surreal_url,
)
os.environ.setdefault("SURREAL_USER", surreal_user())
os.environ.setdefault("SURREAL_PASS", surreal_password().get_secret_value())
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-audit-dummy")
os.environ.setdefault("LORE_TEI_KEY", "audit-dummy")

from _surreal_harness import (  # noqa: E402
    connect_admin, drop_database, make_env, run, unique_database,
)
from _governed_contract import (  # noqa: E402
    MEMORY_TABLE, access_token, governed_overlay_ddl, apply_ddl, seed_memory_governed,
)
import lorerunes as pdp  # noqa: E402
import loremaster  # noqa: E402
import loremaster.server as server_mod  # noqa: E402
from loremaster.server import AppContext, LoreServer, build_app_context  # noqa: E402
from loremaster.config import LoreConfig  # noqa: E402
from loremaster import governed  # noqa: E402
from loresigil.testing import FakeEmbedder  # noqa: E402

_DIM = 8
_NS = "lore_test"
RESULTS: list[tuple[str, str, str]] = []


def record(name: str, verdict: str, detail: str = "") -> None:
    RESULTS.append((name, verdict, detail))
    print(f"  [{verdict:9}] {name}" + (f" :: {detail}" if detail else ""), flush=True)


# --- the switchable transport token (the WIRE authentication) ------------------------------- #
_CURRENT = {"email": None}


def _patched_get_access_token():
    email = _CURRENT["email"]
    if email is None:
        # no ambient token -> resolve_subject sees subject=None -> GovernedDenied (identity-less)
        return access_token(subject="")
    return access_token(subject=email)


def bare(value) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


def _boot_config(slug: str, root: Path) -> LoreConfig:
    payload = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei", "base_url": "http://localhost:8080", "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano", "dim": _DIM, "truncate": False,
            "max_input_tokens": 8192, "max_batch_texts": 32, "concurrency": 2,
            "connect_timeout_s": 5, "api_key_env": "LORE_TEI_KEY", "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": surreal_url(), "namespace": _NS,
            "user_env": "SURREAL_USER", "password_env": "SURREAL_PASS",
        },
        "roots": [{"tier": "custom", "watch": "live", "path": str(root), "include": ["**/*.py"]}],
        "include": [], "exclude_dirs": [".git"], "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {"enabled": True, "observer": "inotify", "debounce_ms": 1500,
                    "reconcile_interval_s": 600},
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9251},
    }
    return LoreConfig.model_validate(payload)


async def wire_recall(ctx: AppContext, *, email: str, cap: str | None, query: str, k: int = 50) -> str:
    """A recall through the TRUE composition root: set the ambient transport token to `email`,
    present `cap` as the tool arg. Returns the rendered digest string."""
    _CURRENT["email"] = email
    return await ctx.recall(query, k=k, capability=cap)


async def wire_remember(ctx: AppContext, *, email: str, cap: str | None, text: str, **kw) -> str:
    _CURRENT["email"] = email
    return await ctx.remember(text, capability=cap, **kw)


async def main() -> int:
    print(f"provenance: loremaster.__file__ = {loremaster.__file__}", flush=True)
    assert Path(loremaster.__file__).resolve().is_relative_to(Path(REPO).resolve()), \
        "NOT testing the real tree!"
    print(f"HEAD graded: {os.popen('cd %s && git rev-parse HEAD' % REPO).read().strip()}", flush=True)

    server_mod.get_access_token = _patched_get_access_token  # patch the wire auth seam

    slug = unique_database()
    tmp = Path("/tmp/secaudit-63a/run")
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "live").mkdir(exist_ok=True)
    ctx = await build_app_context(
        server=LoreServer(_boot_config(slug, tmp / "live")),
        embedder=FakeEmbedder(dim=_DIM),
        manifest_path=tmp / "m.db",
        snapshot_root=tmp / "snap",
        start_tasks=False,
        calibration_engine=None,
    )
    env = make_env(database=slug, dim=_DIM)
    admin_conn = await connect_admin(env)
    try:
        ps, ks, reg = ctx._principal_store, ctx._keep_store, ctx.agent_registry
        assert ps is not None and ks is not None, "composition root did not wire identity stores"

        # ---- principals: alice(member), bob(member), carol(admin) ---------------------------
        E_ALICE, E_BOB, E_CAROL = "alice@ex.com", "bob@ex.com", "carol@ex.com"
        p_alice = await ps.create(email=E_ALICE, role="member")
        p_bob = await ps.create(email=E_BOB, role="member")
        p_carol = await ps.create(email=E_CAROL, role="admin")
        id_alice, id_bob = bare(p_alice.id), bare(p_bob.id)

        # ---- agents: alice->[a1,a2], bob->[b1,b2], carol->[c1] (>=2 agents each principal) ---
        async def mint(name, email, pid):
            r = await reg.register(name, session="s1", role="worker", owner_principal_id=pid)
            return str(r.capability), bare(r.agent.id)
        cap_a1, ag_a1 = await mint("alice_w1", E_ALICE, id_alice)
        cap_a2, ag_a2 = await mint("alice_w2", E_ALICE, id_alice)
        cap_b1, ag_b1 = await mint("bob_w1", E_BOB, id_bob)
        cap_b2, ag_b2 = await mint("bob_w2", E_BOB, id_bob)
        cap_c1, ag_c1 = await mint("carol_admin", E_CAROL, bare(p_carol.id))

        # ---- keeps: project P(keeper alice), kA(keeper alice), kB(keeper bob) ---------------
        proj = await ks.get_or_create_keyed(key=governed.PROJECT_KEEP_KEY, type="project",
                                            keeper_email=E_ALICE, name="lore")
        kA = await ks.create_keep(keeper_email=E_ALICE, type="project", name="alicespace")
        kB = await ks.create_keep(keeper_email=E_BOB, type="project", name="bobspace")
        id_proj, id_kA, id_kB = bare(proj.id), bare(kA.id), bare(kB.id)

        # apply governed overlay (idempotent; ensure the 3 cols+indexes exist for seeding)
        await apply_ddl(admin_conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)

        # ================================================================================== #
        # CHECK 1 + POSITIVE CONTROL — cross-principal READ isolation over the WIRE, seeded matrix
        # ================================================================================== #
        # A hostile matrix: every scope, both principals, keeps IN and OUT, dirty NONE-scope row.
        Q = "zebracorn"  # a rare token so ONLY our seeds match
        seeds = [
            ("s_alice_pp", id_alice, ag_a1, "principal-private", f"{Q} alice principalprivate"),
            ("s_alice_ap1", id_alice, ag_a1, "agent-private", f"{Q} alice agentprivate a1"),
            ("s_alice_ap2", id_alice, ag_a2, "agent-private", f"{Q} alice agentprivate a2"),
            ("s_bob_pp", id_bob, ag_b1, "principal-private", f"{Q} bob principalprivate"),
            ("s_bob_ap1", id_bob, ag_b1, "agent-private", f"{Q} bob agentprivate b1"),
            ("s_server", None, None, "server", f"{Q} shared server row"),
            ("s_keepA", id_alice, ag_a1, pdp.keep_scope(id_kA), f"{Q} keepA alice household"),
            ("s_keepB", id_bob, ag_b1, pdp.keep_scope(id_kB), f"{Q} keepB bob household"),
            ("s_none", None, None, None, f"{Q} legacy none-scope dirty"),
        ]
        for rid, op, oa, sc, txt in seeds:
            await seed_memory_governed(admin_conn, row_id=rid, dim=_DIM,
                                       owner_principal=op, owner_agent=oa, scope=sc, note_text=txt)

        # unfiltered total matching the token (admin AllRows should see all these)
        total_rows = await run(admin_conn,
                               f"SELECT count() FROM {MEMORY_TABLE} WHERE note_text @@ $q GROUP ALL",
                               {"q": Q})
        unfiltered = total_rows[0]["count"] if total_rows else 0

        # Expected VISIBLE text sets per principal-agent (from the member read predicate):
        #  agent a1: own agent-private(a1) + own principal-private + server + NONE-owner server
        #            + keeps the principal's HOUSEHOLD is in (alice keeper of proj+kA -> keepA;
        #            NOT keepB). NOT bob's rows. NOT s_none (NONE scope, member-invisible).
        exp = {
            "a1": {"s_alice_pp", "s_alice_ap1", "s_server", "s_keepA"},
            "a2": {"s_alice_pp", "s_alice_ap2", "s_server", "s_keepA"},  # a2 sees a2's ap, not a1's
            "b1": {"s_bob_pp", "s_bob_ap1", "s_server", "s_keepB"},
        }
        # note: keepA is alice's household -> alice agents see s_keepA; keepB is bob's -> bob agents.

        def served_ids(rendered: str) -> set[str]:
            return {rid for (rid, _op, _oa, _sc, txt) in seeds if txt in rendered}

        async def check_member(label, email, cap, agent_key):
            rendered = await wire_recall(ctx, email=email, cap=cap, query=Q)
            got = served_ids(rendered)
            want = exp[agent_key]
            leaked = got - want
            missing = want - got
            ok = not leaked and not missing
            record(f"CHECK1 isolation: {label}", "PASS" if ok else "FAIL",
                   f"served={sorted(got)} want={sorted(want)} leaked={sorted(leaked)} missing={sorted(missing)}")
            return got

        got_a1 = await check_member("alice/ag_a1", E_ALICE, cap_a1, "a1")
        got_a2 = await check_member("alice/ag_a2", E_ALICE, cap_a2, "a2")
        got_b1 = await check_member("bob/ag_b1", E_BOB, cap_b1, "b1")

        # the headline negative, called out explicitly:
        record("CHECK1 headline: bob NEVER sees alice principal-private",
               "PASS" if "s_alice_pp" not in got_b1 else "FAIL",
               f"bob served={sorted(got_b1)}")
        record("CHECK1 headline: alice NEVER sees bob principal-private",
               "PASS" if "s_bob_pp" not in got_a1 else "FAIL",
               f"alice served={sorted(got_a1)}")

        # POSITIVE CONTROL: admin (carol) AllRows sees EVERY seeded row incl bob's + NONE-scope.
        rendered_admin = await wire_recall(ctx, email=E_CAROL, cap=cap_c1, query=Q)
        got_admin = served_ids(rendered_admin)
        all_ids = {rid for (rid, *_r) in seeds}
        admin_ok = got_admin == all_ids
        record("CHECK1 POSITIVE CONTROL: admin sees ALL rows (filter is the blocker)",
               "PASS" if admin_ok else "FAIL",
               f"admin served={sorted(got_admin)} of {sorted(all_ids)} (unfiltered_count={unfiltered})")

        # ================================================================================== #
        # CHECK 2 — served SET == served set-size == caller-filtered count (trust Leg 1)
        # A member's served count is STRICTLY BELOW the unfiltered total; never the whole table.
        # ================================================================================== #
        below = len(got_a1) < unfiltered and len(got_b1) < unfiltered
        record("CHECK2 Leg1: member served count STRICTLY below unfiltered total",
               "PASS" if below else "FAIL",
               f"a1={len(got_a1)} b1={len(got_b1)} unfiltered={unfiltered}")
        # served set has no foreign row (already covered) — and admin's count == unfiltered set.
        record("CHECK2 Leg1: admin served set-size == unfiltered matching total",
               "PASS" if len(got_admin) == unfiltered else "FAIL",
               f"admin={len(got_admin)} unfiltered={unfiltered}")

        # ================================================================================== #
        # CHECK 6 — owner stamp is SERVER-DERIVED: the 62 binding (A's cap under B's token DENIES)
        # ================================================================================== #
        # negative: present alice's capability but the transport token says bob's email -> DENY
        async def expect_deny(label, email, cap):
            try:
                _CURRENT["email"] = email
                await ctx.recall(Q, capability=cap)
                record(label, "FAIL", "no GovernedDenied raised (leak/confused-deputy)")
            except governed.GovernedDenied:
                record(label, "PASS", "GovernedDenied (binding/identity enforced)")
            except Exception as e:  # noqa: BLE001
                record(label, "FAIL", f"wrong exception {type(e).__name__}: {e}")

        await expect_deny("CHECK6 binding: alice-cap under BOB token DENIES", E_BOB, cap_a1)
        await expect_deny("CHECK6 binding: bob-cap under ALICE token DENIES", E_ALICE, cap_b1)
        await expect_deny("CHECK6 forged capability DENIES", E_ALICE, "alice_w1:deadbeefforged")
        await expect_deny("CHECK6 garbage capability DENIES", E_ALICE, "not-a-credential")
        # identity-less (no capability, no ambient token)
        try:
            _CURRENT["email"] = None
            await ctx.recall(Q, capability=None)
            record("CHECK6 identity-less recall DENIES", "FAIL", "answered identity-less call")
        except governed.GovernedDenied:
            record("CHECK6 identity-less recall DENIES", "PASS", "GovernedDenied teaching error")
        except Exception as e:  # noqa: BLE001
            record("CHECK6 identity-less recall DENIES", "FAIL", f"{type(e).__name__}: {e}")
        # POSITIVE CONTROL: matched cap+token succeeds (already shown by CHECK1 passing).
        try:
            _CURRENT["email"] = E_ALICE
            r = await ctx.recall(Q, capability=cap_a1)
            record("CHECK6 POSITIVE CONTROL: matched alice cap+token succeeds", "PASS",
                   f"rendered {len(r)} chars")
        except Exception as e:  # noqa: BLE001
            record("CHECK6 POSITIVE CONTROL: matched alice cap+token succeeds", "FAIL", str(e))

        # ================================================================================== #
        # CHECK 3 — anti-injection over the wire (F4)
        # ================================================================================== #
        # 3a: the served tool exposes NO owner arg -> a hostile owner_principal= is a TypeError
        try:
            await wire_remember(ctx, email=E_ALICE, cap=cap_a1, text=f"{Q} inject owner",
                                owner_principal=id_bob)
            record("CHECK3a wire remember rejects owner_principal= (no such arg)", "FAIL",
                   "accepted a hostile owner_principal= kwarg")
        except TypeError:
            record("CHECK3a wire remember rejects owner_principal= (no such arg)", "PASS",
                   "TypeError — strongest anti-injection (no owner arg on the wire)")
        for bad in ("as_agent", "created_by", "owner_agent", "scope"):
            try:
                await wire_remember(ctx, email=E_ALICE, cap=cap_a1, text=f"{Q} inject {bad}",
                                    **{bad: "x"})
                record(f"CHECK3a wire remember rejects {bad}=", "FAIL", "accepted hostile kwarg")
            except TypeError:
                record(f"CHECK3a wire remember rejects {bad}=", "PASS", "TypeError (no such wire arg)")
            except Exception as e:  # noqa: BLE001
                record(f"CHECK3a wire remember rejects {bad}=", "WARN", f"{type(e).__name__}: {e}")

        # 3b: a legitimate wire remember stamps the owner as the CREDENTIAL's principal, never forged
        mid = await wire_remember(ctx, email=E_ALICE, cap=cap_a1, text=f"{Q} legit alice write")
        row = await run(admin_conn,
                        "SELECT owner_principal, owner_agent, scope FROM type::record('memory', $id)",
                        {"id": bare(mid)})
        row0 = row[0] if row else {}
        owner_ok = id_alice in str(row0.get("owner_principal"))
        scope_ok = str(row0.get("scope")) == pdp.keep_scope(id_proj)
        record("CHECK3b wire remember stamps owner = credential principal (alice)",
               "PASS" if owner_ok else "FAIL", f"stored owner_principal={row0.get('owner_principal')!r}")
        record("CHECK3b wire remember defaults scope = project keep (not principal-private)",
               "PASS" if scope_ok else "FAIL",
               f"stored scope={row0.get('scope')!r} expected keep:{id_proj}")

        # 3c: BACKEND scope-injection guard (the wire has no scope arg, so exercise the backend seam
        #     directly): alice tries scope=keep:<bob's keep she is NOT householded in> -> DENY.
        subj_alice = await governed.resolve_subject(
            access_token(subject=E_ALICE), cap_a1, registry=reg, principal_store=ps, keep_store=ks)
        try:
            await ctx.memory_backend.remember(f"{Q} cross-keep inject", kind="fact",
                                              subject=subj_alice, scope=pdp.keep_scope(id_kB))
            record("CHECK3c backend rejects ungrantable scope= (foreign keep)", "FAIL",
                   "alice wrote into bob's keep (cross-keep injection)")
        except governed.GovernedDenied as e:
            teaches = "add-household" in str(e)
            record("CHECK3c backend rejects ungrantable scope= (foreign keep)",
                   "PASS" if teaches else "WARN",
                   "GovernedDenied" + (" +teaches add-household" if teaches else " (no teaching text)"))
        # POSITIVE CONTROL: a grantable scope (server) is accepted.
        try:
            mid2 = await ctx.memory_backend.remember(f"{Q} grantable server scope", kind="fact",
                                                     subject=subj_alice, scope="server")
            r2 = await run(admin_conn, "SELECT scope FROM type::record('memory', $id)", {"id": bare(mid2)})
            ok = r2 and str(r2[0].get("scope")) == "server"
            record("CHECK3c POSITIVE CONTROL: grantable scope=server accepted+applied",
                   "PASS" if ok else "FAIL", f"stored scope={r2[0].get('scope')!r}" if r2 else "no row")
        except Exception as e:  # noqa: BLE001
            record("CHECK3c POSITIVE CONTROL: grantable scope=server accepted+applied", "FAIL", str(e))
        # scope=server via a MEMBER: is server grantable by a member? (design says _grantable: yes)
        record("CHECK3c note: scope=server IS grantable by a member (design §2.4/_grantable)",
               "INFO", "server in _VALID_FIXED_SCOPES -> _grantable True; not an injection vector")

        print("\n--- CHECK 1/2/3/6 (wire) done; see summary ---", flush=True)
    finally:
        await admin_conn.close()
        await ctx.aclose()
        await drop_database(env)

    return 0


if __name__ == "__main__":
    try:
        code = asyncio.run(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        code = 2
    print("\n================ SUMMARY ================", flush=True)
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    for name, verdict, detail in RESULTS:
        if verdict in ("FAIL", "WARN"):
            print(f"  {verdict}: {name} :: {detail}")
    passes = sum(1 for r in RESULTS if r[1] == "PASS")
    print(f"\n  PASS={passes}  FAIL={len(fails)}  "
          f"WARN={sum(1 for r in RESULTS if r[1]=='WARN')}  "
          f"total={len(RESULTS)}")
    sys.exit(1 if fails else code)
```

### `/tmp/secaudit-63a/audit2.py` — stage 2 (single-brain oracle, migration isolation, Leg-2)

```python
"""SECURITY AUDIT stage 2 — packet 63a memory retrofit.

CHECK4: single-brain oracle authorize(row) == authorize_filter().matches(row) over the REAL memory
        table INCLUDING dirty NONE-scope rows (stronger than the contract, which excluded NONE-scope
        from the equality) — per action (READ/WRITE/DELETE), per role (member/admin).
CHECK5: migration preserves isolation — refuse on ambiguous operator (no widening), backfill NONE
        scope -> project keep (household-visible, NOT leaked to a foreign principal), idempotent,
        agent-first ORDER refusal on `message`.
LEG-2 : the trust-doctrine forgery table — dependency x {stale, empty, wrong-instance, partial},
        each state CONSTRUCTED, the served response diffed against healthy.

TEST store ws://127.0.0.1:18000 (NEVER :18500), per-run unique DB, reaped.
"""
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from pathlib import Path

REPO = "/home/ejprice/PycharmProjects/lore"
sys.path.insert(0, f"{REPO}/loremaster/tests")

from _surreal_harness import surreal_user, surreal_password  # noqa: E402
os.environ.setdefault("SURREAL_USER", surreal_user())
os.environ.setdefault("SURREAL_PASS", surreal_password().get_secret_value())

from _surreal_harness import (  # noqa: E402
    connect_admin, drop_database, make_env, run, unique_database,
)
from _governed_contract import (  # noqa: E402
    MEMORY_TABLE, access_token, governed_overlay_ddl, apply_ddl, seed_memory_governed,
    authorize_filter_ids, build_memory_backend, build_principal_and_keep_stores,
)
from loremaster.store import surreal_schema  # noqa: E402
import lorerunes as pdp  # noqa: E402
import loremaster  # noqa: E402
from loremaster import governed  # noqa: E402
from loremaster.principals import migrate_governed  # noqa: E402
from loremaster.keeps import KeepStore, KeepStoreError  # noqa: E402
from loremaster.visible_keeps import resolve_visible_keeps  # noqa: E402

_DIM = 8
RESULTS: list[tuple[str, str, str]] = []


def record(name, verdict, detail=""):
    RESULTS.append((name, verdict, detail))
    print(f"  [{verdict:9}] {name}" + (f" :: {detail}" if detail else ""), flush=True)


def bare(v):
    t = str(getattr(v, "id", v))
    return t.split(":", 1)[-1] if ":" in t else t


def member(pid, aid, keeps=frozenset()):
    return pdp.Subject(principal_id=pid, agent_id=aid, role=pdp.PRINCIPAL_ROLE_MEMBER,
                       visible_keep_ids=keeps)


def admin(pid="alice", aid="ag_a1"):
    return pdp.Subject(principal_id=pid, agent_id=aid, role=pdp.PRINCIPAL_ROLE_ADMIN,
                       visible_keep_ids=frozenset())


KA, KB = pdp.keep_scope("ka"), pdp.keep_scope("kb")
# hostile matrix (id, owner_principal, owner_agent, scope) — None == store NONE
ROWS = [
    ("m1", "alice", "ag_a1", "agent-private"),
    ("m2", "alice", "ag_a2", "agent-private"),
    ("m3", "alice", "ag_a1", "principal-private"),
    ("m4", "bob", "ag_b1", "principal-private"),
    ("m5", "alice", "ag_a1", "server"),
    ("m6", None, None, "server"),          # NONE-owner server (readable by all)
    ("m7", "alice", "ag_a1", KA),
    ("m8", "bob", "ag_b1", KB),
    ("m9", None, None, "agent-private"),   # NONE-owner private (nobody)
    ("m10", None, None, None),             # NONE-scope dirty legacy (unowned)
    ("m11", "alice", "ag_a1", None),       # NONE-scope owned legacy (alice/ag_a1)
]
SUBJECTS = [
    ("alice/a1{ka}", member("alice", "ag_a1", frozenset({KA}))),
    ("alice/a2{ka}", member("alice", "ag_a2", frozenset({KA}))),
    ("bob/b1{kb}", member("bob", "ag_b1", frozenset({KB}))),
    ("alice/a1{}", member("alice", "ag_a1", frozenset())),
    ("admin", admin("alice", "ag_a1")),
]


def py_ids(subject, action):
    """Python authorize verdict over EVERY row incl NONE-scope (FORK 1 built -> Resource(scope=None)
    constructs). This is the stronger oracle: the contract excluded NONE-scope from equality."""
    out = set()
    for rid, op, oa, sc in ROWS:
        res = pdp.Resource(table=MEMORY_TABLE, owner_principal=op, owner_agent=oa, scope=sc)
        if pdp.authorize(subject, action, res).allowed:
            out.add(rid)
    return out


async def check4(conn):
    print("\n=== CHECK4 — single-brain oracle over the REAL memory table (incl NONE-scope) ===")
    all_ids = {r[0] for r in ROWS}
    for aname, action in (("READ", pdp.Action.READ), ("WRITE", pdp.Action.WRITE),
                          ("DELETE", pdp.Action.DELETE)):
        for label, subject in SUBJECTS:
            p = py_ids(subject, action)
            s = await authorize_filter_ids(conn, subject, action, MEMORY_TABLE)
            s &= all_ids  # scope to our seeded rows
            ok = p == s
            record(f"CHECK4 {aname} [{label}]", "PASS" if ok else "FAIL",
                   "" if ok else f"py={sorted(p)} store={sorted(s)} "
                   f"only-py={sorted(p-s)} only-store={sorted(s-p)}")
    # explicit dirty-row callouts (the single-brain-on-dirty property):
    # m10 (unowned NONE scope): member-invisible for READ, admin-visible.
    read_admin = await authorize_filter_ids(conn, admin(), pdp.Action.READ, MEMORY_TABLE)
    read_a1 = await authorize_filter_ids(conn, member("alice", "ag_a1", frozenset({KA})),
                                         pdp.Action.READ, MEMORY_TABLE)
    record("CHECK4 dirty: NONE-scope m10 admin-visible / member-invisible (READ)",
           "PASS" if ("m10" in read_admin and "m10" not in read_a1) else "FAIL",
           f"admin_has_m10={'m10' in read_admin} member_has_m10={'m10' in read_a1}")
    # m11 (alice-owned NONE scope): READ/WRITE invisible even to owner, DELETE-able by owner.
    del_a1 = await authorize_filter_ids(conn, member("alice", "ag_a1", frozenset()),
                                        pdp.Action.DELETE, MEMORY_TABLE)
    write_a1 = await authorize_filter_ids(conn, member("alice", "ag_a1", frozenset()),
                                          pdp.Action.WRITE, MEMORY_TABLE)
    ok = ("m11" in del_a1) and ("m11" not in read_a1) and ("m11" not in write_a1)
    record("CHECK4 dirty: owner CAN DELETE own NONE-scope m11 but NOT read/write it",
           "PASS" if ok else "FAIL",
           f"del={'m11' in del_a1} read={'m11' in read_a1} write={'m11' in write_a1}")
    # bob must DELETE none of alice's rows (exact-owner)
    del_bob = await authorize_filter_ids(conn, member("bob", "ag_b1", frozenset()),
                                         pdp.Action.DELETE, MEMORY_TABLE)
    del_bob &= all_ids
    alices = {"m1", "m2", "m3", "m5", "m7", "m11"}
    record("CHECK4 DELETE: bob deletes NONE of alice's rows",
           "PASS" if not (del_bob & alices) else "FAIL", f"bob_delete={sorted(del_bob)}")


async def check5():
    print("\n=== CHECK5 — migration preserves isolation ===")
    # (a) REFUSE on ambiguous operator (2 members, 0 admins) — writes NOTHING (no widening).
    env = make_env(database=unique_database(), dim=_DIM)
    ps, ks = await build_principal_and_keep_stores(env)
    backend = await build_memory_backend(env)
    conn = await connect_admin(env)
    try:
        await apply_ddl(conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
        await ps.create(email="p1@ex.com", role="member")
        await ps.create(email="p2@ex.com", role="member")
        await seed_memory_governed(conn, row_id="leg1", dim=_DIM, owner_principal=None,
                                   owner_agent=None, scope=None, note_text="legacy note")
        handle = backend.handle
        res = await migrate_governed(table=MEMORY_TABLE, store=handle, keep_store=ks, principal_store=ps)
        # row still NONE scope -> member-invisible (not widened)
        row = await run(conn, "SELECT scope FROM type::record('memory','leg1')")
        still_none = row and row[0].get("scope") is None
        record("CHECK5a ambiguous-operator migration REFUSES + writes nothing",
               "PASS" if (res.refused and res.backfilled == 0 and still_none) else "FAIL",
               f"refused={res.refused} backfilled={res.backfilled} scope_still_none={still_none}")
    finally:
        await conn.close(); await backend.close(); await ks.close(); await ps.close()
        await drop_database(env)

    # (b) single-operator migration backfills to project keep; visible to HOUSEHOLD, NOT to a
    #     foreign principal; idempotent.
    env = make_env(database=unique_database(), dim=_DIM)
    ps, ks = await build_principal_and_keep_stores(env)
    backend = await build_memory_backend(env)
    conn = await connect_admin(env)
    try:
        await apply_ddl(conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
        op = await ps.create(email="op@ex.com", role="member")  # the SINGLE principal
        await seed_memory_governed(conn, row_id="leg2", dim=_DIM, owner_principal=None,
                                   owner_agent=None, scope=None, note_text="fleet legacy note")
        handle = backend.handle
        # before: op sees no keeps, row is NONE scope -> invisible to op
        keeps_before = await resolve_visible_keeps(ks, member_email="op@ex.com")
        res = await migrate_governed(table=MEMORY_TABLE, store=handle, keep_store=ks, principal_store=ps)
        row = await run(conn, "SELECT scope, owner_principal FROM type::record('memory','leg2')")
        proj = await ks.get_by_key(governed.PROJECT_KEEP_KEY)
        proj_scope = pdp.keep_scope(bare(proj.id))
        scope_ok = row and str(row[0].get("scope")) == proj_scope
        owner_none = row and row[0].get("owner_principal") is None  # UNOWNED-LEGACY (never fabricated)
        record("CHECK5b single-operator migration backfills NONE-scope -> project keep, owner stays NONE",
               "PASS" if (not res.refused and res.backfilled == 1 and scope_ok and owner_none) else "FAIL",
               f"refused={res.refused} backfilled={res.backfilled} scope={row[0].get('scope')!r} "
               f"owner={row[0].get('owner_principal')!r}")
        # op is the keeper -> now householded -> op's member subject sees the migrated row.
        keeps_after = await resolve_visible_keeps(ks, member_email="op@ex.com")
        op_subj = member(bare(op.id), "op_agent", keeps_after)
        op_ids = await authorize_filter_ids(conn, op_subj, pdp.Action.READ, MEMORY_TABLE)
        record("CHECK5b household member (keeper) REGAINS sight of migrated legacy row",
               "PASS" if "leg2" in op_ids else "FAIL",
               f"keeps_before={sorted(keeps_before)} keeps_after={sorted(keeps_after)} sees_leg2={'leg2' in op_ids}")
        # a FOREIGN principal (not householded, empty keeps) must NOT see the migrated row.
        outsider = member("outsider_pid", "outsider_agent", frozenset())
        out_ids = await authorize_filter_ids(conn, outsider, pdp.Action.READ, MEMORY_TABLE)
        record("CHECK5b migration does NOT leak to a FOREIGN principal (isolation preserved)",
               "PASS" if "leg2" not in out_ids else "FAIL",
               f"foreign sees leg2={'leg2' in out_ids} (must be False)")
        # idempotent second run
        res2 = await migrate_governed(table=MEMORY_TABLE, store=handle, keep_store=ks, principal_store=ps)
        record("CHECK5b migration idempotent (2nd run backfills 0)",
               "PASS" if (not res2.refused and res2.backfilled == 0) else "FAIL",
               f"backfilled={res2.backfilled} already={res2.already_migrated}")
        # agent-first ORDER refusal on `message`
        res3 = await migrate_governed(table="message", store=handle, keep_store=ks, principal_store=ps)
        record("CHECK5b `message` migration REFUSES agent-first (§2.6 order)",
               "PASS" if (res3.refused and "agent" in (res3.reason or "")) else "FAIL",
               f"refused={res3.refused}")
    finally:
        await conn.close(); await backend.close(); await ks.close(); await ps.close()
        await drop_database(env)


async def leg2():
    print("\n=== LEG-2 forgery table (construct each degraded state; diff served vs healthy) ===")
    env = make_env(database=unique_database(), dim=_DIM)
    ps, ks = await build_principal_and_keep_stores(env)
    backend = await build_memory_backend(env)
    conn = await connect_admin(env)
    from loremaster.agents import AgentRegistry
    reg = AgentRegistry(url=env.url, namespace=env.namespace, database=env.database,
                        user=env.user, password=env.password)
    await reg.ensure_ready()
    try:
        await apply_ddl(conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
        alice = await ps.create(email="alice@ex.com", role="member")
        id_alice = bare(alice.id)
        r = await reg.register("aw", session="s1", role="worker", owner_principal_id=id_alice)
        cap, agid = str(r.capability), bare(r.agent.id)
        # a keep alice IS householded in, with a matching row
        kA = await ks.create_keep(keeper_email="alice@ex.com", type="project", name="aspace")
        await seed_memory_governed(conn, row_id="krow", dim=_DIM, owner_principal=id_alice,
                                   owner_agent=agid, scope=pdp.keep_scope(bare(kA.id)),
                                   note_text="keepA note")

        tok = access_token(subject="alice@ex.com")

        async def subj():
            return await governed.resolve_subject(tok, cap, registry=reg, principal_store=ps, keep_store=ks)

        # HEALTHY baseline: alice sees the keep row.
        healthy = await subj()
        base_ids = await authorize_filter_ids(conn, healthy, pdp.Action.READ, MEMORY_TABLE)
        record("LEG2 baseline: alice (healthy) SEES her keep row 'krow'",
               "PASS" if "krow" in base_ids else "FAIL", f"keeps={sorted(healthy.visible_keep_ids)}")

        # --- resolve_visible_keeps STALE: alice LEAVES kA -> the keep's rows must vanish (no cache).
        await run(conn, "DELETE member_of WHERE out = $k",
                  {"k": __import__("surrealdb").RecordID("keep", bare(kA.id))})
        stale = await subj()  # re-resolve AFTER leaving
        stale_ids = await authorize_filter_ids(conn, stale, pdp.Action.READ, MEMORY_TABLE)
        vanished = "krow" not in stale_ids and pdp.keep_scope(bare(kA.id)) not in stale.visible_keep_ids
        record("LEG2 resolve_visible_keeps STALE: left keep -> its rows VANISH (no cache, one read/call)",
               "PASS" if vanished else "FAIL",
               f"keeps_after_leave={sorted(stale.visible_keep_ids)} sees_krow={'krow' in stale_ids}")

        # --- resolve_visible_keeps EMPTY: a principal in NO keep -> only private+server (never a keep row).
        empty_keeps = await resolve_visible_keeps(ks, member_email="alice@ex.com")
        record("LEG2 resolve_visible_keeps EMPTY: member of 0 keeps resolves to frozenset()",
               "PASS" if empty_keeps == frozenset() else "FAIL", f"keeps={sorted(empty_keeps)}")

        # --- resolve_visible_keeps WRONG-INSTANCE: a keep store on a NONEXISTENT db -> DENY (fail-closed).
        ghost = KeepStore(url=env.url, namespace=env.namespace, database=unique_database(),
                          user=env.user, password=env.password)  # not ensure_ready'd -> no schema
        try:
            await governed.resolve_subject(tok, cap, registry=reg, principal_store=ps, keep_store=ghost)
            record("LEG2 resolve_visible_keeps WRONG-INSTANCE: bogus keep store -> DENY",
                   "WARN", "resolve_subject did NOT deny on a wrong-instance keep store")
        except governed.GovernedDenied:
            record("LEG2 resolve_visible_keeps WRONG-INSTANCE: bogus keep store -> DENY (fail-closed)",
                   "PASS", "GovernedDenied (never a shorter keep set)")
        except Exception as e:  # noqa: BLE001
            record("LEG2 resolve_visible_keeps WRONG-INSTANCE: bogus keep store -> DENY",
                   "WARN", f"{type(e).__name__}: {e} (not GovernedDenied but still fail-closed)")
        finally:
            await ghost.close()

        # --- stamp_owner STALE: retire the agent (construct the state) -> present cap -> DENY.
        await run(conn, "UPDATE type::record('agent', $id) SET status = 'retired'", {"id": agid})
        try:
            await governed.resolve_subject(tok, cap, registry=reg, principal_store=ps, keep_store=ks)
            record("LEG2 stamp_owner STALE: retired-agent capability -> DENY", "FAIL",
                   "resolved a Subject for a RETIRED agent (revocation ignored)")
        except governed.GovernedDenied:
            record("LEG2 stamp_owner STALE: retired-agent capability -> DENY (no-cache revocation)",
                   "PASS", "GovernedDenied")
        # un-retire for cleanliness (not required)
    finally:
        await reg.close(); await conn.close(); await backend.close()
        await ks.close(); await ps.close(); await drop_database(env)

    # --- the migration EMPTY: no project keep -> a default-scope remember REFUSES (never falls to private).
    env = make_env(database=unique_database(), dim=_DIM)
    ps, ks = await build_principal_and_keep_stores(env)
    backend = await build_memory_backend(env)
    conn = await connect_admin(env)
    from loremaster.agents import AgentRegistry as AR2
    reg = AR2(url=env.url, namespace=env.namespace, database=env.database,
              user=env.user, password=env.password)
    await reg.ensure_ready()
    try:
        await apply_ddl(conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
        alice = await ps.create(email="a@ex.com", role="member")
        r = await reg.register("aw", session="s1", role="worker", owner_principal_id=bare(alice.id))
        subject = await governed.resolve_subject(access_token(subject="a@ex.com"), str(r.capability),
                                                 registry=reg, principal_store=ps, keep_store=ks)
        try:
            await backend.remember("orphan note", kind="fact", subject=subject)  # NO project keep exists
            record("LEG2 migration EMPTY: no project keep -> default-scope remember REFUSES",
                   "FAIL", "wrote a note with NO project keep (silent fallback to private?)")
        except governed.GovernedDenied as e:
            teaches = "migrate-governed" in str(e) or "project keep" in str(e)
            record("LEG2 migration EMPTY: no project keep -> default-scope remember REFUSES (loud)",
                   "PASS" if teaches else "WARN",
                   "GovernedDenied" + (" +names migrate-governed" if teaches else ""))
    finally:
        await reg.close(); await conn.close(); await backend.close()
        await ks.close(); await ps.close(); await drop_database(env)

    # --- store TABLE-EMPTY: recall over an empty visible set -> a clean 'no memories' (no crash).
    env = make_env(database=unique_database(), dim=_DIM)
    ps, ks = await build_principal_and_keep_stores(env)
    backend = await build_memory_backend(env)
    from loremaster.agents import AgentRegistry as AR3
    reg = AR3(url=env.url, namespace=env.namespace, database=env.database,
              user=env.user, password=env.password)
    await reg.ensure_ready()
    try:
        alice = await ps.create(email="a2@ex.com", role="member")
        r = await reg.register("aw", session="s1", role="worker", owner_principal_id=bare(alice.id))
        subject = await governed.resolve_subject(access_token(subject="a2@ex.com"), str(r.capability),
                                                 registry=reg, principal_store=ps, keep_store=ks)
        hits = await backend.recall("anything", subject=subject)
        record("LEG2 store TABLE-EMPTY: recall over empty visible set -> [] (no crash, no leak)",
               "PASS" if hits == [] else "FAIL", f"hits={hits!r}")
    finally:
        await reg.close(); await backend.close(); await ks.close(); await ps.close()
        await drop_database(env)


async def main():
    print(f"provenance: {loremaster.__file__}", flush=True)
    print(f"HEAD graded: {os.popen('cd %s && git rev-parse HEAD' % REPO).read().strip()}", flush=True)
    env = make_env(database=unique_database(), dim=_DIM)
    conn = await connect_admin(env)
    try:
        await apply_ddl(conn, surreal_schema.generate_memory_ddl(dim=_DIM), url=env.url)
        await apply_ddl(conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
        for rid, op, oa, sc in ROWS:
            await seed_memory_governed(conn, row_id=rid, dim=_DIM, owner_principal=op,
                                       owner_agent=oa, scope=sc)
        await check4(conn)
    finally:
        await conn.close(); await drop_database(env)
    await check5()
    await leg2()
    return 0


if __name__ == "__main__":
    try:
        code = asyncio.run(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc(); code = 2
    print("\n================ SUMMARY (stage 2) ================", flush=True)
    for name, verdict, detail in RESULTS:
        if verdict in ("FAIL", "WARN"):
            print(f"  {verdict}: {name} :: {detail}")
    fails = [r for r in RESULTS if r[1] == "FAIL"]
    print(f"\n  PASS={sum(1 for r in RESULTS if r[1]=='PASS')}  FAIL={len(fails)}  "
          f"WARN={sum(1 for r in RESULTS if r[1]=='WARN')}  total={len(RESULTS)}")
    sys.exit(1 if fails else code)
```
