# REPORT-secaudit-63b-iii — packet 63b wave iii security audit (comms message family, over the wire)

brief-base v14 read
brief project v7 read
lead-base — N/A (I am an auditor, not a wave lead)

## Summary block (brief-base §1)

- **state:** DONE. **VERDICT: GO** (47/47 wire checks pass; no confirmed leak/forgery/spoof of the
  message-family read boundary). 2 residuals surfaced (R-1 accepted bound, R-2 = 63c-scope finding #467).
- **role:** dedicated SECURITY-AUDITOR for 63b wave iii — REPORT-ONLY, I edited no code/tests, committed nothing.
- **Graded:** `766cd91` · HEAD-at-report: `766cd91` · SAME (0 behind). 63b-ii-b CLOSED at this sha.
- **deviations:** none.
- **Capability check (brief-base §4):** lore loaded via `ToolSearch +lore` (20 tools) — FIRST choice,
  used for every symbol read. Text-search binaries (`grep`/`rg`/`find` with `-name`) are HOOK-BLOCKED on
  this live-indexed main checkout; every textual sweep is lore + `Read` + `awk` over an explicit file
  list (said so where used — the `_COMMS_ACTIONS` table read via `awk`, the def-line listing of
  `_governed_contract.py` via `awk`). Test store `ws://127.0.0.1:18000` used (throwaway per-run DB,
  reaped); production `:18500` NEVER touched. Probes run under `uv run` (the system python has the #140
  empty-namespace poison; `uv run` resolves the real tree — provenance asserted every run).
- **Packages considered:** none — no mechanism specified (this is an audit).
- **Reuse ledger:** none — 0 new production symbols (report-only). The wire harness is the SHARED
  `credentialed_app_context` (`test_wire_isolation_63a.py` idiom), reused, not cloned.
- **decisions-needed:** none block the GO. For 63c: close finding #467 (agent-registry surface) before
  the pkt-65 hosted cutover (63-rulings §1.1 already requires 63c before 65).
- **receipt pointers:** §METHOD (wire path) · §EXPLOITS (47-check table, 3 stages) · §RESIDUALS (R-1/R-2)
  · §VERDICT · §PROBES (4 instruments pasted verbatim in the appendix) · lore finding **#467**.

## Target (from the brief + design §5 + 63-rulings §6)

The now-governed comms READ surface at HEAD `766cd91`: `lore_comms` drain / ack / await / story +
`lore_tasks rollup`'s message leg — all resolve a Subject and FILTER by the ONE shared
`governed.read_filter` (= `authorize_filter(subject, READ, message).to_surql()`). Plus the ii-a write
side: `send` (capability-required, stamps owner) + register (mints the session keep, SF-63-1).

**The §6 IN-scope properties I must break (over the WIRE, on the REAL tables, F3 fixture):**
1. Cross-principal read isolation ∀ read verbs (drain/ack/await/story/rollup).
2. The served COUNT is over the served SET (no existence leak).
3. Session admission keeper-gated for a FOREIGN principal (SF-63-1) — the headline.
4. Anti-injection ∀ write verbs; the agent≡capability binding (§4.D).
5. Single-brain on DIRTY rows.
6. Migration cannot widen visibility (precondition).
7. The guarded write has no TOCTOU.

Plus the Leg-2 forgery table (63-rulings §6) — each row constructed, not reasoned.

---

## Discipline note
Every negative result (DENY/filtered) PAIRS with a positive control (the legitimate call succeeds) AND,
where applicable, a differently-broken control (rejected for a DIFFERENT reason). A GO states what was
attacked. A CONFIRMED cross-principal leak/forgery/spoof is a NO-GO with a reproduction.

---

## METHOD (the wire path attacked)

The isolation boundary of every governed comms READ is ONE splice —
`governed.read_filter(subject, MESSAGE_TABLE)` == `authorize_filter(subject, READ, message).to_surql()`
— confirmed present in ALL four read paths at HEAD (`lore_get_symbol`, read at `766cd91`):
`MessageLedger.drain`/`_filter_visible_rows`, `MessageLedger.ack`/`_resolve_message_ids`,
`MessageLedger.messages_for_task` (story), `MessageLedger.message_activity_since` (rollup leg). The
`Subject` behind that filter is built at ONE composition root `AppContext._resolve_subject` →
`governed.resolve_subject` (capability→owner-agent via `stamp_owner` WITH the 62 binding; token→principal
via `resolve_principal`; keeps via `resolve_visible_keeps`); the tool layer additionally enforces §4.D
(`agent_row.id != subject.agent_id → GovernedDenied`) in `_comms_drain`/`_comms_ack`/`_comms_story`/
`_comms_send`. `register` mints the session keep and gates a FOREIGN principal (SF-63-1) in `_comms_register`.

I attacked this OVER THE WIRE: a REAL booted `AppContext` (the shared `credentialed_app_context` harness)
with a per-call SWITCHABLE ambient transport token (`get_access_token` patched to the acting principal),
real `PrincipalStore`/`KeepStore`/`AgentRegistry`/`MessageLedger` on a throwaway per-run DB on
`ws://127.0.0.1:18000` (reaped; NEVER :18500). Capabilities minted through the real registry
(`register_owned`); messages created through the real `ctx.comms(action="send")` and (for
harder-to-reach dirty states) raw seeds via a signed-in admin connection. F3 world: **alice + bob member
principals with DISJOINT households + an admin principal (AllRows positive control), ≥2 agents each, one
shared session string exercised in the SF-63-1 leg.** Provenance asserted every run:
`loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (real tree,
not an empty namespace package — the #140 poison check). Probes pasted verbatim in §PROBES.

## EXPLOITS — the table (each attack → wire call → result → positive control)

Legend: **DENY** = `governed.GovernedDenied` raised; **filtered** = the read returned without the target
row; every negative pairs with a positive control proving the probe can SEE the thing it is denying.

### STAGE 1 — read isolation · THE BINDING · forgery · SF-63-1 (23/23, 0 leaks)

| # | attack (over the wire) | result | positive control |
|---|---|---|---|
| A1 | alice `story` on bob's task_id (bob's message: session-keep, principal-private, agent-private scopes) | **filtered** — 0 of bob's 3 bodies in alice's arc | bob stories his own task → sees `bob-secret-body`; admin (AllRows) → sees it |
| A2 | alice `rollup` (capability'd) message leg | **filtered** — bob's thread `bsess` absent from render | admin rollup → `bsess` present (probe discriminating) |
| A2b | Leg-1 count: `message_activity_since` count vs served set, per wire-resolved Subject | alice `total==rows==0`; bob/admin `total==rows==3` incl. `bob-secret-body` | count == served set for every caller (§6 item 2) |
| B1 | THE BINDING — alice_w1's cap under BOB's token (`drain`) | **DENY** ("capability did not verify") | alice_w1's cap under alice's token → drains |
| B2 | §4.D sibling — `agent=alice_w1` + alice_w2's cap | **DENY** ("names an identity the cap did not prove") | `agent=alice_w2` + alice_w2's cap → drains |
| B3 | §4.D foreign — `agent=alice_w1` + bob's cap, alice token | **DENY** | (diagonal control below) |
| B4 | full 2×2 agent×cap matrix on drain (alice token) | **only agent==cap succeeds**; all off-diagonal DENY | diagonal legs succeed |
| C1 | absent capability (`capability=None`) on `drain` | **DENY** | — |
| C2 | garbage cap (forged-agent-name form AND pure-garbage form) | **DENY**, and deny text **byte-identical** across both (no existence oracle) | real cap → drains |
| D1 | SF-63-1 — bob (foreign) `register` into alice's kept session `shared7` | **DENY**; names session+`household` remedy; does **NOT** leak keeper email/id/"alice"; **0** agent rows written (#97) | — |
| D2 | alice's own 2nd agent `register` into `shared7` | **succeeds** (auto-householded keeper) | — |
| D3 | bob `register` into `shared7` AFTER `add-household(bob)` | **succeeds** | proves D1 was the household gate, not a blanket refusal |

All 23 stage-1 checks PASS. No cross-principal leak, forgery, or spoof in this stage.

### STAGE 2 — drain/ack isolation on DIRTY delivery edges · invisible-seq ack · register→send battery (13/13, 0 leaks)

The dirty state (an invisible bob-owned message addressed to alice_w1 by a `to` edge) is CONSTRUCTED
via an admin seed — SF-63-1 prevents it in normal operation; the read filter must still hold on it.

| # | attack (over the wire) | result | positive control |
|---|---|---|---|
| E1 | alice `drain(peek)` with 1 visible + 1 invisible (bob principal-private) edge | **filtered** — serves only `VISIBLE-to-alice` | (E2 controls) |
| E2 | alice `drain` (non-peek) stamps only what it serves | visible edge `seen_at` set; **bob's invisible edge `seen_at` stays None** (§4.3 neither served nor stamped) | the visible edge IS stamped |
| E3 | alice `ack([invisible seq])` (resolves through the read filter) | **`unknown_message`**, bob's edge `acked_at` stays None (never a false `already_acked`) | ack the visible seq → `acked` |
| E4 | alice `drain(since=-1)` (crafted recovery cursor over all seqs) | **filtered** — cannot recover bob's invisible message | — |
| G1 | `register` capability mint-once | re-register returns `capability=None` | first register minted it |
| G2 | `send` with `capability=None` | **DENY** | — |
| G3 | register→send→drain end-to-end + credential-leak scan | works; raw capability appears in NO fleet/drain render | — |

### STAGE 3 — Leg-2 forgery table: stamp_owner + resolve_visible_keeps dependency rows (9/9, 0 leaks)

| # | dependency × state | result | positive control |
|---|---|---|---|
| L1 | `stamp_owner` STALE — a **RETIRED** agent's capability (`verify_capability` condition 2, NO CACHE) | **DENY** (`OwnerStampError` at the seam; the wire drain also denied) | active cap verifies → owner agent; active cap drains |
| L2 | `resolve_visible_keeps` STALE — a keep the caller **LEFT** (no cache) | after `remove_household`, bob's keep-scoped message **vanishes on alice's NEXT call** | pre-add: invisible; after `add_household`: **visible** (keep sharing works — probe discriminating) |
| L3 | `resolve_visible_keeps` EMPTY — a **member of 0 keeps** | cannot read the keep-scoped message; the render **NAMES the bound** `visible via 0 keep(s)` (never a silent "no messages") | — |

### STAGE 2b — the `await` read verb (bounded; routes through the same filtered `message_ledger.drain`)

| # | attack | result | positive control |
|---|---|---|---|
| AW1 | alice `await` with 1 visible + 1 invisible edge | serves `VIS-await`, filters `INV-await-bob` | (render carries the scope bound) |
| AW2 | §4.D — alice names bob_w1 in `await` with alice's cap | **DENY** | — |

**Grand total: 47 wire-level checks, all PASS**, plus 3 characterization NOTES (below). No CONFIRMED
cross-principal leak, forgery, or spoof on the governed comms MESSAGE-family READ surface.

## RESIDUALS (read forward — none gates the GO; each has an owner + re-open trigger)

**R-1 · ACCEPTED BOUND (design bound iv / ii-b §4.B) — the drain/await served COUNT is over the
recipient's EDGE set, not the visible set.** With a constructed invisible delivery in alice's window,
`total_pending=2` / `directive_pending=1` count the edge she cannot read; the drain render says
`peeked 1 of 2 pending … +1 more unread`. This does NOT leak bob's message CONTENT (no body/sender/
thread in the render for the invisible one) — only the EXISTENCE of a delivery edge addressed to alice.
The scope bound line (`visible via 1 keep(s)`) heads the render, which is the ruling's stated honesty
mechanism. Reachable only in a DEGRADED state (post-send re-scope, a legacy NONE-scope edge, or an
admin-seeded cross-principal edge) that SF-63-1 prevents in normal operation. **Verdict: honest accepted
bound, not a leak** (measured render pasted in §PROBES / dbg_drainrender). Re-open trigger: a render
change that surfaces the invisible edge's grade/sender, or a decision to make the count Leg-1-strict.

**R-2 · 63c-SCOPE (SF-63-2) — the AGENT-registry surface is un-identity-gated and runs BEFORE the
message-verb §4.D check.** Filed as **lore finding #467**. Two measured behaviours:
- **Touch-before-deny:** `AppContext.comms` runs `agent_registry.touch(agent, session)` for every
  registration-requiring action BEFORE the handler's §4.D capability check, so a caller with a valid
  capability for its OWN agent, by NAMING a foreign agent, STILL stamps that foreign agent's
  `heartbeat_at` (measured moving on alice's DENIED drain naming bob_w1). Cross-principal write to
  liveness metadata; the message read itself is denied.
- **Existence oracle / cross-session roster disclosure:** naming a nonexistent agent in a foreign
  session → `UnknownAgentError` enriched with THAT session's roster; naming an existing foreign agent →
  `GovernedDenied`. A caller can probe agent existence and read a foreign session's roster via the error.

Both are reachable TODAY via the already-ungoverned `heartbeat`/`fleet` verbs, so they are NOT new
capabilities the 63b message retrofit granted — they are the AGENT population being ungoverned until
63c. Severity LOW (liveness metadata / roster names, not message content). **Owner: 63c (SF-63-2).
Re-open trigger (hard): the pkt-65 hosted cutover** — a hosted foreign principal reaching the roster/
liveness surface is an incomplete §9 (63-rulings §1.1: 63c MUST precede 65). Recommendation in #467:
gate/relocate the touch and session-scope the UnknownAgent enrichment when 63c governs the roster.

## SCOPE NOTES (out of this wave, confirmed as such)
- §6 item 6 (the migration cannot widen visibility — the `_migrate_agent_owner` single-principal
  precondition) is a WRITE/migrate concern owned by ii-a; not re-attacked here. The READ side does not
  widen visibility (proven above — a NONE/foreign scope is member-invisible).
- §6 item 7 (guarded-write TOCTOU → `GovernedConflict`) is a WRITE-path concern (send/memory guarded
  writes) owned by ii-a / i-b; send has NO caller-facing owner=/scope= argument (the `comms()`
  signature carries neither — the owner pair is server-derived from the verified Subject, the scope from
  the session keep), so there is no read-surface injection vector, which is what wave iii owns.

## VERDICT: **GO**

I attacked the cross-principal boundary of the now-governed comms MESSAGE family HARD, over the MCP wire,
on the REAL `message`/`to` tables on the test store, with an F3 world (alice + bob member principals,
DISJOINT households, an admin AllRows control, ≥2 agents each, one shared session string). Across **47
discriminating checks** (each negative paired with a positive control, several with a differently-broken
control), I could NOT leak, forge, or spoof the message-read boundary:

- **Cross-principal read isolation HOLDS ∀ read verbs** (drain, ack, story, await, rollup) — alice never
  saw bob's session-keep / principal-private / agent-private messages; bob and the admin control DID
  (the probe is discriminating, not a false clear where nobody sees the content).
- **The served COUNT is over the served SET** for the rollup message leg (Leg 1); the drain/await edge
  count is the ruled accepted bound iv, honestly labelled with the scope line.
- **SF-63-1 HOLDS** — a foreign principal cannot register into a kept session; the DENY names the
  session + remedy and does NOT leak the keeper's identity; no agent row is written; the keeper's own
  agents join, and a foreign one joins only after `add-household`.
- **THE BINDING + §4.D HOLD** — A-cap-under-B-token, sibling-cap, and foreign-cap all DENY; only
  `agent == the capability's proven agent` acts; forged/absent/garbage capabilities DENY uniformly with
  NO existence oracle.
- **No-cache revocation HOLDS** — a retired capability and a left-keep membership both stop working on
  the very next call.

The two residuals (R-2, finding #467) are on the AGENT-registry surface that 63c/SF-63-2 explicitly
owns and are NOT message-read leaks; R-1 is a ruled accepted bound. **None is a CONFIRMED
leak/forgery/spoof of the 63b message-family read boundary, so none opens a fix wave. GO.**

## PROBES (verbatim — the load-bearing instruments; report-only, so pasted not committed)

Provenance asserted every run: `loremaster.__file__` resolves to
`/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (real tree, not an empty
namespace package — #140 poison check). Run under `uv run` from the repo root against
`ws://127.0.0.1:18000` (throwaway per-run DB, reaped; NEVER :18500). The scripts import the shared
credentialed wire harness from `loremaster/tests/_governed_contract.py` (`credentialed_app_context`,
`register_owned`, `seed_message_legacy`) — the SAME harness `test_wire_isolation_63a.py` uses, extended
here to the comms MESSAGE verbs the 63a wire gate does not cover.

See the four instrument files pasted below: `secaudit_63b_iii_probe.py` (stage 1),
`secaudit_63b_iii_probe2.py` (stage 2), `secaudit_63b_iii_probe3.py` (stage 3 / Leg-2), and
`probe3_await.py` (the await verb). [PASTED VERBATIM — see the appendix at the end of this file.]


---

# APPENDIX — the probe instruments, verbatim (brief-base §1: instruments establishing a load-bearing claim survive)

## secaudit_63b_iii_probe.py

```python
"""secaudit-63b-iii — WIRE-LEVEL cross-principal security probe for the governed comms MESSAGE family.

REPORT-ONLY audit instrument (packet 63b wave iii). Drives the REAL ``AppContext`` FastMCP handlers
(``ctx.comms(...)`` / ``ctx._rollup(...)``) over a per-call SWITCHABLE ambient transport token
(``credentialed_app_context``, the shared wire harness) against the REAL ``message``/``to`` schema on
the TEST store ``ws://127.0.0.1:18000`` (a throwaway per-run DB, reaped; NEVER :18500).

Every negative (DENY / filtered / empty) PAIRS with a POSITIVE control (the legitimate call succeeds)
and, where apt, a DIFFERENTLY-BROKEN control (rejected for a DIFFERENT reason). Prints a PASS/FAIL line
per check; exits non-zero if ANY check fails (a leak/forgery/spoof that slipped through).

Provenance: prints ``loremaster.__file__`` (the #140 poison check — this MUST resolve inside the real
source tree, never an empty namespace package).
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))  # (nothing here; helpers come from tests/)
_REPO = Path("/home/ejprice/PycharmProjects/lore")
sys.path.insert(0, str(_REPO / "loremaster" / "tests"))

import loremaster  # noqa: E402

print(f"[provenance] loremaster.__file__ = {loremaster.__file__}")
assert loremaster.__file__ and "PycharmProjects/lore/loremaster" in loremaster.__file__, (
    "POISONED: loremaster does not resolve to the real source tree — aborting (would test nothing)"
)

import pytest  # noqa: E402
from _governed_contract import (  # noqa: E402
    credentialed_app_context,
    register_owned,
    seed_message_legacy,
)
from surrealdb import RecordID  # noqa: E402

from loremaster import governed  # noqa: E402
from lorerunes.pdp import keep_scope  # noqa: E402

_RESULTS: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    _RESULTS.append((ok, label))
    mark = "PASS" if ok else "**FAIL**"
    line = f"[{mark}] {label}"
    if detail:
        line += f"  — {detail}"
    print(line)


class _Boom(Exception):
    pass


async def _denies(coro: Any, *, why: str) -> tuple[bool, str]:
    """Return (True, message) iff the awaitable raises GovernedDenied; else (False, <what happened>)."""
    try:
        result = await coro
    except governed.GovernedDenied as error:
        return True, str(error)
    except Exception as error:  # a DIFFERENT exception is NOT the deny we wanted
        return False, f"raised {type(error).__name__}: {error}"
    return False, f"NO RAISE (returned {result!r})"


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


async def main(monkeypatch: Any, tmp_path: Path) -> None:
    # F3 world: alice + bob member principals (DISJOINT households) + an ADMIN principal (AllRows
    # positive control). ≥2 agents each. ONE shared session STRING is exercised in the SF-63-1 leg.
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member", "bob": "member", "adminp": "admin"}
    ) as world:
        ctx = world["ctx"]
        holder = world["holder"]
        pids = world["pids"]
        emails = world["emails"]
        admin_conn = world["admin_conn"]
        ks = ctx._keep_store  # noqa: SLF001

        # ---- capabilities (minted directly on the registry — the tool render does not return them) ----
        holder["email"] = emails["alice"]
        alice_w1_cap, alice_w1_id = await register_owned(
            ctx, "alice_w1", owner_principal_id=pids["alice"], session="asess"
        )
        alice_w2_cap, alice_w2_id = await register_owned(
            ctx, "alice_w2", owner_principal_id=pids["alice"], session="asess"
        )
        holder["email"] = emails["bob"]
        bob_w1_cap, bob_w1_id = await register_owned(
            ctx, "bob_w1", owner_principal_id=pids["bob"], session="bsess"
        )
        bob_w2_cap, bob_w2_id = await register_owned(
            ctx, "bob_w2", owner_principal_id=pids["bob"], session="bsess"
        )
        holder["email"] = emails["adminp"]
        admin_cap, admin_id = await register_owned(
            ctx, "admin_a1", owner_principal_id=pids["adminp"], session="asess", role="auditor"
        )

        # ---- session keeps: alice keeps 'asess', bob keeps 'bsess' (DISJOINT households) ----
        # get_or_create_keyed auto-households the keeper (Fork D). admin registered into 'asess' so it
        # is NOT the keeper — its AllRows visibility comes from role=admin, not from a keep.
        await ks.get_or_create_keyed(
            key="session:asess", type="session", keeper_email=emails["alice"], name="asess"
        )
        await ks.get_or_create_keyed(
            key="session:bsess", type="session", keeper_email=emails["bob"], name="bsess"
        )

        # =================================================================== #
        # SECTION A — CROSS-PRINCIPAL READ ISOLATION (the headline)
        # =================================================================== #
        # A real anchor task (tasks are UNGOVERNED until 64 — visible to everyone; only the MESSAGE arc
        # is read-filtered). bob anchors his messages to it.
        holder["email"] = emails["bob"]
        t_bob = await ctx.task_ledger.create_task("bob task", "arc", created_by="bob_w1")
        # bob SENDS a message to bob_w2 in bob's session (scope = keep:bsess), anchored to t_bob.
        await ctx.comms(
            action="send", agent="bob_w1", session="bsess", capability=bob_w1_cap,
            to=["bob_w2"], body="bob-secret-body", grade="signal", task_id=t_bob,
        )
        # Also SEED (raw) two harder-scoped bob messages anchored to t_bob:
        #   principal-private (owner_principal=bob) and agent-private (owner_agent=bob_w1).
        await seed_message_legacy(
            admin_conn, sender_id=bob_w1_id, session="bsess", seq=900, task_id=t_bob,
            scope="principal-private", owner_principal=RecordID("principal", pids["bob"]),
            owner_agent=RecordID("agent", bob_w1_id), body="bob-pp-secret",
        )
        await seed_message_legacy(
            admin_conn, sender_id=bob_w1_id, session="bsess", seq=901, task_id=t_bob,
            scope="agent-private", owner_principal=RecordID("principal", pids["bob"]),
            owner_agent=RecordID("agent", bob_w1_id), body="bob-ap-secret",
        )

        # A1 — alice STORY on bob's task_id → must NOT contain bob's secret bodies.
        holder["email"] = emails["alice"]
        a_story_bob = str(
            await ctx.comms(
                action="story", agent="alice_w1", session="asess", capability=alice_w1_cap,
                task_id=t_bob,
            )
        )
        leaked = [
            s for s in ("bob-secret-body", "bob-pp-secret", "bob-ap-secret")
            if s in a_story_bob
        ]
        check(not leaked, "A1 story: alice cannot read bob's messages via story",
              f"leaked={leaked!r}" if leaked else "0 bob bodies in alice's story of bob's task")

        # A1 positive control — bob stories his own task and SEES his message (proves the probe can see).
        holder["email"] = emails["bob"]
        bob_story = str(
            await ctx.comms(
                action="story", agent="bob_w1", session="bsess", capability=bob_w1_cap, task_id=t_bob,
            )
        )
        check("bob-secret-body" in bob_story, "A1 control: bob sees his OWN message via story",
              "bob-secret-body present" if "bob-secret-body" in bob_story else "control BROKE — probe blind")

        # A1 positive control — admin (AllRows) sees bob's message via story.
        holder["email"] = emails["adminp"]
        admin_story = str(
            await ctx.comms(
                action="story", agent="admin_a1", session="asess", capability=admin_cap, task_id=t_bob,
            )
        )
        check("bob-secret-body" in admin_story, "A1 control: admin (AllRows) sees bob's message",
              "present" if "bob-secret-body" in admin_story else "control BROKE")

        # A2 — rollup message leg (WIRE): the render shows message METADATA (sender/thread/grade), not
        # the body — so the leak marker is bob's thread 'bsess'. alice's rollup must NOT show it; admin's
        # (AllRows control) MUST, proving the probe is DISCRIMINATING (not a false clear where nobody
        # sees it).
        from datetime import UTC, datetime  # noqa: PLC0415

        _EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
        holder["email"] = emails["alice"]
        alice_rollup = str(await ctx._rollup(since=None, limit=50, capability=alice_w1_cap))  # noqa: SLF001
        check("bsess" not in alice_rollup,
              "A2 rollup(wire): alice's rollup message leg does not leak bob's thread/metadata",
              "no 'bsess' in alice's rollup" if "bsess" not in alice_rollup else "LEAK: bob's thread present")
        holder["email"] = emails["adminp"]
        admin_rollup = str(await ctx._rollup(since=None, limit=50, capability=admin_cap))  # noqa: SLF001
        check("bsess" in admin_rollup, "A2 control: admin's rollup message leg DOES surface bob's message",
              "'bsess' present for admin — probe is discriminating" if "bsess" in admin_rollup else "control BROKE")

        # A2b — LEG-1 COUNT property (§6 item 2): the served count is over the served SET. Resolve the
        # REAL wire Subject for each caller and read message_activity_since (count + rows the render derives from).
        holder["email"] = emails["alice"]
        alice_subj = await ctx._resolve_subject(alice_w1_cap)  # noqa: SLF001
        a_win = await ctx.message_ledger.message_activity_since(_EPOCH, limit=50, subject=alice_subj)
        holder["email"] = emails["bob"]
        bob_subj = await ctx._resolve_subject(bob_w1_cap)  # noqa: SLF001
        b_win = await ctx.message_ledger.message_activity_since(_EPOCH, limit=50, subject=bob_subj)
        holder["email"] = emails["adminp"]
        adm_subj = await ctx._resolve_subject(admin_cap)  # noqa: SLF001
        m_win = await ctx.message_ledger.message_activity_since(_EPOCH, limit=50, subject=adm_subj)
        a_bodies = [m.body for m in a_win.rows]
        check(a_win.total == 0 and a_win.total == len(a_win.rows) and not a_bodies,
              "A2b LEG-1: alice's rollup count==served set==0 (no bob messages, count matches rows)",
              f"alice total={a_win.total} rows={len(a_win.rows)} bodies={a_bodies!r}")
        check(b_win.total == len(b_win.rows) and "bob-secret-body" in [m.body for m in b_win.rows],
              "A2b control: bob's own count==served set and includes his sent message",
              f"bob total={b_win.total} rows={len(b_win.rows)}")
        check(m_win.total == len(m_win.rows) and "bob-secret-body" in [m.body for m in m_win.rows],
              "A2b control: admin's (AllRows) count==served set and includes bob's message",
              f"admin total={m_win.total} rows={len(m_win.rows)}")

        # =================================================================== #
        # SECTION B — THE BINDING / §4.D agent≡capability matrix
        # =================================================================== #
        # B1 — THE BINDING: alice_w1's capability under BOB's token → DENY (agent.owner_principal != token principal).
        holder["email"] = emails["bob"]
        ok, msg = await _denies(
            ctx.comms(action="drain", agent="alice_w1", session="asess", capability=alice_w1_cap),
            why="A-cap under B-token",
        )
        check(ok, "B1 THE BINDING: alice's cap under bob's token DENIES", (msg[:90] if ok else msg))
        # B1 positive control — alice_w1's cap under ALICE's token drains fine.
        holder["email"] = emails["alice"]
        try:
            await ctx.comms(action="drain", agent="alice_w1", session="asess", capability=alice_w1_cap)
            check(True, "B1 control: alice's cap under alice's token SUCCEEDS", "drain returned")
        except Exception as error:  # noqa: BLE001
            check(False, "B1 control: alice's cap under alice's token SUCCEEDS", f"raised {error!r}")

        # B2 — sibling: alice_w1 NAMED but alice_w2's cap presented → §4.D DENY (agent≡subject mismatch).
        holder["email"] = emails["alice"]
        ok, msg = await _denies(
            ctx.comms(action="drain", agent="alice_w1", session="asess", capability=alice_w2_cap),
            why="sibling cap mismatch",
        )
        check(ok, "B2 §4.D: alice_w1 named with alice_w2's cap DENIES (sibling)", (msg[:90] if ok else msg))
        # B2 positive control — alice_w2 named with alice_w2's cap succeeds.
        try:
            await ctx.comms(action="drain", agent="alice_w2", session="asess", capability=alice_w2_cap)
            check(True, "B2 control: alice_w2 named with its OWN cap SUCCEEDS", "drain returned")
        except Exception as error:  # noqa: BLE001
            check(False, "B2 control: alice_w2 named with its OWN cap SUCCEEDS", f"raised {error!r}")

        # B3 — foreign cap under own token: alice_w1 named, BOB's cap presented, ALICE token → DENY.
        holder["email"] = emails["alice"]
        ok, msg = await _denies(
            ctx.comms(action="drain", agent="alice_w1", session="asess", capability=bob_w1_cap),
            why="foreign cap",
        )
        check(ok, "B3 §4.D: alice_w1 named with bob's cap DENIES", (msg[:90] if ok else msg))

        # B4 — the FULL 2x2 agent x cap matrix on drain (alice token): only the diagonal (agent==cap) works.
        holder["email"] = emails["alice"]
        matrix_ok = True
        matrix_detail: list[str] = []
        for name, expect_ok, cap in [
            ("alice_w1", True, alice_w1_cap),
            ("alice_w1", False, alice_w2_cap),
            ("alice_w2", False, alice_w1_cap),
            ("alice_w2", True, alice_w2_cap),
        ]:
            try:
                await ctx.comms(action="drain", agent=name, session="asess", capability=cap)
                got_ok = True
            except governed.GovernedDenied:
                got_ok = False
            except Exception as error:  # noqa: BLE001
                got_ok = None
                matrix_detail.append(f"{name}/{'own' if cap in (alice_w1_cap if name=='alice_w1' else alice_w2_cap) else 'sib'}={error!r}")
            if got_ok is not expect_ok:
                matrix_ok = False
                matrix_detail.append(f"{name} expected_ok={expect_ok} got={got_ok}")
        check(matrix_ok, "B4 §4.D 2x2 matrix: only agent==cap succeeds within a principal",
              "; ".join(matrix_detail) if matrix_detail else "diagonal only")

        # =================================================================== #
        # SECTION C — FORGERY / SPOOFING (uniform DENY, no oracle)
        # =================================================================== #
        holder["email"] = emails["alice"]
        # C1 — absent capability (None) on a governed read → DENY.
        ok_absent, msg_absent = await _denies(
            ctx.comms(action="drain", agent="alice_w1", session="asess", capability=None),
            why="absent cap",
        )
        check(ok_absent, "C1 absent capability DENIES", (msg_absent[:90] if ok_absent else msg_absent))
        # C2 — garbage capability strings → DENY, and the message is UNIFORM (no existence oracle):
        #   garbage for an EXISTING agent name vs a NONEXISTENT agent name → same class of deny text.
        ok_g1, m_g1 = await _denies(
            ctx.comms(action="drain", agent="alice_w1", session="asess", capability="alice_w1:deadbeef"),
            why="garbage cap, existing agent",
        )
        ok_g2, m_g2 = await _denies(
            ctx.comms(action="drain", agent="alice_w1", session="asess", capability="totally:garbage"),
            why="garbage cap 2",
        )
        check(ok_g1 and ok_g2, "C2 garbage capability DENIES (both forms)",
              f"g1={ok_g1} g2={ok_g2}")
        check(ok_g1 and ok_g2 and (m_g1 == m_g2),
              "C2 no-oracle: garbage-cap deny text is UNIFORM across forged-name vs garbage",
              "identical deny text" if m_g1 == m_g2 else f"DIFFERENT:\n   g1={m_g1!r}\n   g2={m_g2!r}")

        # =================================================================== #
        # SECTION D — SF-63-1 SESSION-KEEP HOUSEHOLD (the comms headline)
        # =================================================================== #
        # alice keeps a FRESH shared session 'shared7' via the REAL register wire.
        holder["email"] = emails["alice"]
        await ctx.comms(action="register", agent="alice_s1", session="shared7", role="builder")
        keep = await ks.get_by_key("session:shared7")
        check(keep is not None, "D setup: alice's register minted the session keep 'shared7'",
              f"keep={keep.id if keep else None}")

        # D1 — a FOREIGN principal (bob) registering into alice's kept session → DENY, naming the
        #      session + remedy but NOT the keeper's identity/email; and NO agent row written (#97).
        holder["email"] = emails["bob"]
        ok_d1, msg_d1 = await _denies(
            ctx.comms(action="register", agent="bob_s1", session="shared7", role="builder"),
            why="foreign register",
        )
        leak_keeper = (emails["alice"] in msg_d1) or (pids["alice"] in msg_d1) or ("alice" in msg_d1)
        names_remedy = ("shared7" in msg_d1) and ("household" in msg_d1.lower())
        check(ok_d1, "D1 SF-63-1: foreign principal register into kept session DENIES",
              (msg_d1[:110] if ok_d1 else msg_d1))
        check(ok_d1 and names_remedy and not leak_keeper,
              "D1 SF-63-1: deny names session+remedy, does NOT leak the keeper's identity",
              f"names_remedy={names_remedy} leaks_keeper={leak_keeper}")
        # side-effect check: the DENIED register wrote NO agent row for bob_s1.
        rows = await ctx.agent_registry._query(  # noqa: SLF001
            "SELECT count() FROM agent WHERE name = $n GROUP ALL", {"n": "bob_s1"}
        )
        n_bob_s1 = rows[0]["count"] if isinstance(rows, list) and rows else 0
        check(n_bob_s1 == 0, "D1 SF-63-1: denied foreign register wrote NO agent row (#97)",
              f"bob_s1 rows={n_bob_s1}")

        # D2 positive control — alice's OWN second agent joins 'shared7' fine.
        holder["email"] = emails["alice"]
        try:
            await ctx.comms(action="register", agent="alice_s2", session="shared7", role="builder")
            check(True, "D2 control: alice's own 2nd agent joins the kept session", "register ok")
        except Exception as error:  # noqa: BLE001
            check(False, "D2 control: alice's own 2nd agent joins the kept session", f"raised {error!r}")

        # D3 positive control — after add-household(bob), bob registers into 'shared7' fine.
        await ks.add_household_member(keep_id=_bare(keep.id), member_email=emails["bob"])
        holder["email"] = emails["bob"]
        try:
            await ctx.comms(action="register", agent="bob_s1", session="shared7", role="builder")
            check(True, "D3 control: after add-household, bob registers into the shared session", "ok")
        except Exception as error:  # noqa: BLE001
            check(False, "D3 control: after add-household, bob registers into the shared session",
                  f"raised {error!r}")

    # ------------------------------------------------------------------ #
    n_fail = sum(1 for ok, _ in _RESULTS if not ok)
    print(f"\n===== STAGE 1 RESULT: {len(_RESULTS) - n_fail}/{len(_RESULTS)} passed, {n_fail} FAILED =====")
    if n_fail:
        for ok, label in _RESULTS:
            if not ok:
                print(f"  FAILED: {label}")
    sys.exit(1 if n_fail else 0)


def _run() -> None:
    mp = pytest.MonkeyPatch()
    tmp = Path("/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/027cbaf6-5998-40d8-bf1a-7ab83a7a49ee/scratchpad/secaudit_tmp")
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        asyncio.run(main(mp, tmp))
    finally:
        mp.undo()


if __name__ == "__main__":
    try:
        _run()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)

```

## secaudit_63b_iii_probe2.py

```python
"""secaudit-63b-iii — STAGE 2: drain/ack read isolation on DIRTY delivery edges, the invisible-seq ack,
the served-count nuance, the touch-before-deny side effect, the existence oracle, since= recovery, and
the register->send wire battery. Same wire harness / provenance discipline as stage 1.
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO = Path("/home/ejprice/PycharmProjects/lore")
sys.path.insert(0, str(_REPO / "loremaster" / "tests"))

import loremaster  # noqa: E402

print(f"[provenance] loremaster.__file__ = {loremaster.__file__}")
assert loremaster.__file__ and "PycharmProjects/lore/loremaster" in loremaster.__file__, "POISONED"

import pytest  # noqa: E402
from _governed_contract import (  # noqa: E402
    credentialed_app_context,
    register_owned,
    seed_message_legacy,
)
from loremaster.agents import AgentRegistryError  # noqa: E402
from surrealdb import RecordID  # noqa: E402

from loremaster import governed  # noqa: E402

_RESULTS: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    _RESULTS.append((ok, label))
    print(f"[{'PASS' if ok else '**FAIL**'}] {label}" + (f"  — {detail}" if detail else ""))


def note(label: str, detail: str) -> None:
    """A measurement recorded WITHOUT a pass/fail (accepted-bound characterization)."""
    print(f"[NOTE] {label}  — {detail}")


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


_TO = "to"
_MSG = "message"
_AG = "agent"


async def _relate_edge(conn: Any, *, message_id: str, agent_bare: str, session: str) -> None:
    from _surreal_harness import run

    await run(
        conn,
        f"RELATE $m->{_TO}->$a SET session = $s, created_at = $now",
        {"m": RecordID(_MSG, message_id), "a": RecordID(_AG, agent_bare), "s": session,
         "now": datetime.now(UTC)},
    )


async def _seen_at(conn: Any, *, agent_bare: str, message_id: str) -> Any:
    from _surreal_harness import run

    rows = await run(
        conn,
        f"SELECT seen_at, acked_at FROM {_TO} WHERE out = $a AND in = $m",
        {"a": RecordID(_AG, agent_bare), "m": RecordID(_MSG, message_id)},
    )
    return rows[0] if isinstance(rows, list) and rows else None


async def main(monkeypatch: Any, tmp_path: Path) -> None:
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}
    ) as world:
        ctx = world["ctx"]
        holder = world["holder"]
        pids = world["pids"]
        emails = world["emails"]
        conn = world["admin_conn"]
        ks = ctx._keep_store  # noqa: SLF001

        holder["email"] = emails["alice"]
        alice_w1_cap, alice_w1_id = await register_owned(
            ctx, "alice_w1", owner_principal_id=pids["alice"], session="asess"
        )
        holder["email"] = emails["bob"]
        bob_w1_cap, bob_w1_id = await register_owned(
            ctx, "bob_w1", owner_principal_id=pids["bob"], session="bsess"
        )
        await ks.get_or_create_keyed(
            key="session:asess", type="session", keeper_email=emails["alice"], name="asess"
        )

        # ============ E — DRAIN read isolation on a DIRTY edge (constructed) ============ #
        # A VISIBLE message (server scope) addressed to alice_w1, and an INVISIBLE one (bob's
        # principal-private) ALSO addressed to alice_w1 by a `to` edge. In normal operation SF-63-1
        # prevents bob addressing alice; this is the DEGRADED/dirty state the read filter must still hold on.
        vis_id = await seed_message_legacy(
            conn, sender_id=alice_w1_id, session="asess", seq=10, scope="server", body="VISIBLE-to-alice",
        )
        await _relate_edge(conn, message_id=vis_id, agent_bare=alice_w1_id, session="asess")
        inv_id = await seed_message_legacy(
            conn, sender_id=bob_w1_id, session="bsess", seq=11, scope="principal-private",
            owner_principal=RecordID("principal", pids["bob"]), owner_agent=RecordID("agent", bob_w1_id),
            grade="directive", body="INVISIBLE-bob-directive",
        )
        await _relate_edge(conn, message_id=inv_id, agent_bare=alice_w1_id, session="asess")

        # E1 — alice PEEK drain: serves ONLY the visible message; never bob's invisible one.
        holder["email"] = emails["alice"]
        subj = await ctx._resolve_subject(alice_w1_cap)  # noqa: SLF001
        peek = await ctx.message_ledger.drain(agent_id=alice_w1_id, limit=50, peek=True, subject=subj)
        peek_bodies = [e.body for e in peek.entries]
        check("VISIBLE-to-alice" in peek_bodies and "INVISIBLE-bob-directive" not in peek_bodies,
              "E1 drain(peek): serves the visible message, filters bob's invisible one",
              f"served bodies={peek_bodies!r}")

        # E1b — the served-COUNT nuance (accepted bound iv): total_pending / directive_pending are
        # WHOLE-edge counts over the recipient's OWN edges, NOT read-filtered. Characterize, don't grade.
        note("E1b count-nuance (accepted bound iv / §4.B)",
             f"served entries={len(peek.entries)} (1 visible); total_pending={peek.total_pending} "
             f"directive_pending={peek.directive_pending} — these count alice's edges (incl. the "
             f"invisible directive), labelled 'pending deliveries', not 'messages you can read'")

        # E2 — NON-peek drain STAMPS only the served (visible) edge; bob's invisible edge stays UNSEEN.
        drained = await ctx.message_ledger.drain(agent_id=alice_w1_id, limit=50, peek=False, subject=subj)
        d_bodies = [e.body for e in drained.entries]
        vis_state = await _seen_at(conn, agent_bare=alice_w1_id, message_id=vis_id)
        inv_state = await _seen_at(conn, agent_bare=alice_w1_id, message_id=inv_id)
        check("INVISIBLE-bob-directive" not in d_bodies, "E2 drain: bob's invisible message never served",
              f"served={d_bodies!r}")
        check(vis_state and vis_state.get("seen_at") is not None,
              "E2 drain: the VISIBLE edge IS stamped (positive control)", f"vis seen_at set")
        check(inv_state and inv_state.get("seen_at") is None,
              "E2 drain: bob's INVISIBLE edge is NOT stamped (§4.3 neither served nor stamped)",
              f"inv seen_at={inv_state.get('seen_at') if inv_state else None}")

        # E3 — ACK of the INVISIBLE seq resolves THROUGH the read filter → unknown_message, stamps nothing.
        ack = await ctx.message_ledger.ack(agent_id=alice_w1_id, seqs=[11], subject=subj)
        outcomes = {e.seq: e.outcome for e in ack.entries}
        inv_state_after = await _seen_at(conn, agent_bare=alice_w1_id, message_id=inv_id)
        check(str(outcomes.get(11)) == "unknown_message" or "unknown" in str(outcomes.get(11)),
              "E3 ack(invisible seq): fate is unknown_message (never a false already_acked)",
              f"outcomes={outcomes}")
        check(inv_state_after and inv_state_after.get("acked_at") is None,
              "E3 ack(invisible seq): nothing stamped on bob's edge",
              f"inv acked_at={inv_state_after.get('acked_at') if inv_state_after else None}")

        # E3 positive control — ack the VISIBLE seq resolves + acks.
        ack_vis = await ctx.message_ledger.ack(agent_id=alice_w1_id, seqs=[10], subject=subj)
        vis_out = {e.seq: e.outcome for e in ack_vis.entries}
        check("acked" in str(vis_out.get(10)), "E3 control: ack the VISIBLE seq → acked",
              f"outcome={vis_out.get(10)}")

        # E4 — since= recovery cursor cannot recover an invisible message: alice drains since=-1 (all seqs)
        #      → bob's invisible message still filtered.
        recov = await ctx.message_ledger.drain(agent_id=alice_w1_id, limit=50, since=-1, subject=subj)
        r_bodies = [e.body for e in recov.entries]
        check("INVISIBLE-bob-directive" not in r_bodies,
              "E4 since= recovery: crafted cursor cannot recover bob's invisible message",
              f"recovered bodies={r_bodies!r}")

        # ============ F — TOUCH-BEFORE-DENY side effect + EXISTENCE ORACLE ============ #
        # F1 — alice (VALID cap for alice_w1) calls a governed READ NAMING bob_w1 in bob's session.
        #      comms() runs agent_registry.touch(bob_w1) BEFORE the handler's §4.D deny. Measure whether
        #      bob_w1's heartbeat_at is stamped (a cross-principal liveness WRITE surviving the retrofit).
        before = await ctx.agent_registry._query(  # noqa: SLF001
            "SELECT heartbeat_at, status FROM agent WHERE name = $n AND session = $s",
            {"n": "bob_w1", "s": "bsess"},
        )
        hb_before = before[0].get("heartbeat_at") if isinstance(before, list) and before else None
        await asyncio.sleep(0.05)
        denied = False
        try:
            await ctx.comms(action="drain", agent="bob_w1", session="bsess", capability=alice_w1_cap)
        except governed.GovernedDenied:
            denied = True
        after = await ctx.agent_registry._query(  # noqa: SLF001
            "SELECT heartbeat_at, status FROM agent WHERE name = $n AND session = $s",
            {"n": "bob_w1", "s": "bsess"},
        )
        hb_after = after[0].get("heartbeat_at") if isinstance(after, list) and after else None
        touched = hb_before != hb_after
        check(denied, "F1: alice naming bob_w1 in a governed drain is DENIED (§4.D read-blocked)",
              "read denied" if denied else "NOT denied — LEAK")
        # This is NOT a message-read leak; it is a cross-principal write on the (63c-governed) AGENT row.
        if touched:
            note("F1 SIDE-EFFECT (touch-before-deny)",
                 f"alice's DENIED drain STILL stamped bob_w1's heartbeat_at ({hb_before} -> {hb_after}) — "
                 f"comms() touches the NAMED agent before the §4.D capability check. Agent liveness is "
                 f"63c-governed (SF-63-2); heartbeat is already un-gated at HEAD, so this is a KNOWN "
                 f"63c-scope gap, not a 63b message-read regression.")
        else:
            note("F1 SIDE-EFFECT", "no heartbeat change observed (touch may not have stamped)")

        # F2 — EXISTENCE ORACLE: naming a NONEXISTENT agent vs an EXISTING foreign agent gives different
        #      errors (UnknownAgentError-enriched vs §4.D GovernedDenied). Characterize the leak + scope.
        err_existing = None
        try:
            await ctx.comms(action="drain", agent="bob_w1", session="bsess", capability=alice_w1_cap)
        except Exception as e:  # noqa: BLE001
            err_existing = type(e).__name__
        err_ghost = None
        ghost_msg = ""
        try:
            await ctx.comms(action="drain", agent="ghost_zzz", session="bsess", capability=alice_w1_cap)
        except Exception as e:  # noqa: BLE001
            err_ghost = type(e).__name__
            ghost_msg = str(e)
        leaks_roster = ("bob_w1" in ghost_msg)
        note("F2 EXISTENCE-ORACLE",
             f"existing foreign agent -> {err_existing}; nonexistent -> {err_ghost}; "
             f"nonexistent-in-foreign-session error leaks that session's roster (bob_w1 present)={leaks_roster}. "
             f"Both are the AGENT-registry surface (fleet/heartbeat un-gated until 63c/SF-63-2); the "
             f"MESSAGE content is denied either way.")

        # ============ G — register->send wire battery (R2) ============ #
        # G1 — register mints the capability ONCE; a re-register does NOT re-mint (mint-once).
        holder["email"] = emails["alice"]
        again = await ctx.agent_registry.register(
            "alice_w1", session="asess", role="builder", owner_principal_id=pids["alice"]
        )
        check(again.capability is None, "G1 register: capability minted ONCE (re-register re-mints nothing)",
              f"re-register capability={again.capability!r}")

        # G2 — a wire client WITHOUT the capability cannot send or drain (uniform DENY).
        ok_send = False
        try:
            await ctx.comms(action="send", agent="alice_w1", session="asess", capability=None,
                            to=["alice_w1"], body="x", grade="signal")
        except governed.GovernedDenied:
            ok_send = True
        except Exception:  # noqa: BLE001
            ok_send = False
        check(ok_send, "G2 register->send: a send WITHOUT the capability DENIES", "")

        # G3 — the credentialed path works end to end (register -> send -> drain), and the raw credential
        #      does NOT appear in the drain / fleet rendered surfaces (a credential leak would be fatal).
        holder["email"] = emails["bob"]
        await ks.get_or_create_keyed(key="session:bsess", type="session", keeper_email=emails["bob"], name="bsess")
        await ctx.comms(action="register", agent="bob_w2", session="bsess", role="builder")
        bob_w2_cap, _ = await register_owned(ctx, "bob_w3", owner_principal_id=pids["bob"], session="bsess")
        e2e_ok = True
        try:
            await ctx.comms(action="send", agent="bob_w1", session="bsess", capability=bob_w1_cap,
                            to=["bob_w3"], body="hello-w3", grade="signal")
            fleet_render = str(await ctx.comms(action="fleet", agent="bob_w1", session="bsess"))
            drain_render = str(await ctx.comms(action="drain", agent="bob_w3", session="bsess",
                                               capability=bob_w2_cap))
        except Exception as error:  # noqa: BLE001
            e2e_ok = False
            fleet_render = drain_render = f"<raised {error!r}>"
        check(e2e_ok, "G3 register->send->drain: the credentialed path works end to end", "")
        cred_leak = (bob_w1_cap in fleet_render) or (bob_w1_cap in drain_render) or (bob_w2_cap in drain_render)
        check(not cred_leak, "G3 register->send: the raw capability appears in NO other rendered surface",
              "no capability substring in fleet/drain renders" if not cred_leak else "CREDENTIAL LEAK")

    n_fail = sum(1 for ok, _ in _RESULTS if not ok)
    print(f"\n===== STAGE 2 RESULT: {len(_RESULTS) - n_fail}/{len(_RESULTS)} passed, {n_fail} FAILED =====")
    for ok, label in _RESULTS:
        if not ok:
            print(f"  FAILED: {label}")
    sys.exit(1 if n_fail else 0)


def _run() -> None:
    mp = pytest.MonkeyPatch()
    tmp = Path("/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/027cbaf6-5998-40d8-bf1a-7ab83a7a49ee/scratchpad/secaudit_tmp2")
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        asyncio.run(main(mp, tmp))
    finally:
        mp.undo()


if __name__ == "__main__":
    try:
        _run()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)

```

## secaudit_63b_iii_probe3.py

```python
"""secaudit-63b-iii — STAGE 3: the Leg-2 forgery table's load-bearing dependency rows.

- stamp_owner STALE  → a RETIRED agent's capability DENIES (condition 2; NO-CACHE revocation).
- resolve_visible_keeps STALE → a keep the caller LEFT drops its rows on the NEXT call (NO CACHE).
- resolve_visible_keeps EMPTY → a member of 0 keeps sees no keep-scoped row and the render NAMES the
  bound ("visible via 0 keep(s)"), never a silent "no messages".
Each with a POSITIVE control. Same wire harness / provenance discipline.
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from pathlib import Path
from typing import Any

_REPO = Path("/home/ejprice/PycharmProjects/lore")
sys.path.insert(0, str(_REPO / "loremaster" / "tests"))

import loremaster  # noqa: E402

print(f"[provenance] loremaster.__file__ = {loremaster.__file__}")
assert loremaster.__file__ and "PycharmProjects/lore/loremaster" in loremaster.__file__, "POISONED"

import pytest  # noqa: E402
from _governed_contract import access_token, credentialed_app_context, register_owned  # noqa: E402
from _surreal_harness import run as srun  # noqa: E402
from surrealdb import RecordID  # noqa: E402

from loremaster import governed  # noqa: E402
from loremaster.owner_stamp import OwnerStampError, stamp_owner  # noqa: E402

_RESULTS: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    _RESULTS.append((ok, label))
    print(f"[{'PASS' if ok else '**FAIL**'}] {label}" + (f"  — {detail}" if detail else ""))


async def _denies(coro: Any) -> tuple[bool, str]:
    try:
        r = await coro
    except governed.GovernedDenied as e:
        return True, str(e)
    except Exception as e:  # noqa: BLE001
        return False, f"raised {type(e).__name__}: {e}"
    return False, f"NO RAISE ({r!r})"


def _bare(v: Any) -> str:
    t = str(getattr(v, "id", v))
    return t.split(":", 1)[-1] if ":" in t else t


async def main(monkeypatch: Any, tmp_path: Path) -> None:
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member", "bob": "member", "carol": "member"}
    ) as world:
        ctx = world["ctx"]
        holder = world["holder"]
        pids = world["pids"]
        emails = world["emails"]
        conn = world["admin_conn"]
        ks = ctx._keep_store  # noqa: SLF001

        holder["email"] = emails["alice"]
        alice_cap, alice_id = await register_owned(ctx, "alice_w1", owner_principal_id=pids["alice"], session="asess")
        holder["email"] = emails["bob"]
        bob_cap, bob_id = await register_owned(ctx, "bob_w1", owner_principal_id=pids["bob"], session="bsess")
        bob_cap2, bob_id2 = await register_owned(ctx, "bob_w2", owner_principal_id=pids["bob"], session="bsess")
        holder["email"] = emails["carol"]
        carol_cap, carol_id = await register_owned(ctx, "carol_w1", owner_principal_id=pids["carol"], session="csess")
        # keeps: alice keeps asess, bob keeps bsess. carol has NO keep (member of 0 keeps).
        await ks.get_or_create_keyed(key="session:asess", type="session", keeper_email=emails["alice"], name="asess")
        bob_keep = await ks.get_or_create_keyed(key="session:bsess", type="session", keeper_email=emails["bob"], name="bsess")
        bob_keep_bare = _bare(bob_keep.id)

        # bob sends a keep:bsess-scoped message anchored to a real task.
        holder["email"] = emails["bob"]
        t = await ctx.task_ledger.create_task("bob keep task", "arc", created_by="bob_w1")
        await ctx.comms(action="send", agent="bob_w1", session="bsess", capability=bob_cap,
                        to=["bob_w2"], body="bob-keep-secret", grade="signal", task_id=t)

        async def alice_story() -> str:
            holder["email"] = emails["alice"]
            return str(await ctx.comms(action="story", agent="alice_w1", session="asess",
                                       capability=alice_cap, task_id=t))

        # ============ L1 — stamp_owner STALE: retired capability DENIES (no-cache) ============ #
        # positive control: alice's active cap drains.
        holder["email"] = emails["alice"]
        try:
            await ctx.comms(action="drain", agent="alice_w1", session="asess", capability=alice_cap)
            ctrl_ok = True
        except Exception as e:  # noqa: BLE001
            ctrl_ok = False
        check(ctrl_ok, "L1 control: alice's ACTIVE capability drains", "")
        # positive control on the BINDING seam directly: an active cap verifies (owner pair returned).
        tok_alice = access_token(subject=emails["alice"])
        pair_active = await stamp_owner(tok_alice, alice_cap, registry=ctx.agent_registry)
        check(pair_active[1] == alice_id, "L1 control: stamp_owner verifies alice's ACTIVE cap → owner agent",
              f"owner_agent={pair_active[1]}")
        # RETIRE alice_w1 (raw status update — directly exercises verify_capability condition 2).
        await srun(conn, "UPDATE $a SET status = 'retired'", {"a": RecordID("agent", alice_id)})
        # (a) the BINDING seam (verify_capability condition 2, NO CACHE) fails-closed on a retired agent.
        seam_denied = False
        try:
            await stamp_owner(tok_alice, alice_cap, registry=ctx.agent_registry)
        except OwnerStampError:
            seam_denied = True
        check(seam_denied,
              "L1 stamp_owner STALE: verify_capability DENIES a RETIRED agent's cap (no-cache condition 2)",
              "OwnerStampError (fail-closed)" if seam_denied else "cap STILL verified after retire — LEAK")
        # (b) the wire drain call is ALSO denied for a retired agent (touch's RetiredAgentError OR the
        #     handler's GovernedDenied — either way the call fails; a retired identity cannot READ).
        wire_denied = False
        try:
            await ctx.comms(action="drain", agent="alice_w1", session="asess", capability=alice_cap)
        except Exception:  # noqa: BLE001
            wire_denied = True
        check(wire_denied, "L1 wire: a retired agent's drain call is denied (no read for a retired identity)", "")
        # restore alice_w1 active for later use
        await srun(conn, "UPDATE $a SET status = 'active'", {"a": RecordID("agent", alice_id)})

        # ============ L2 — resolve_visible_keeps STALE: a keep the caller LEFT drops its rows ============ #
        # (a) BEFORE add-household: alice cannot read bob's keep:bsess message.
        s0 = await alice_story()
        check("bob-keep-secret" not in s0,
              "L2 pre: alice (not householded) cannot read bob's keep-scoped message", "")
        # (b) add alice to bob's bsess household → alice CAN read it (positive control: keep sharing works).
        await ks.add_household_member(keep_id=bob_keep_bare, member_email=emails["alice"])
        s1 = await alice_story()
        check("bob-keep-secret" in s1,
              "L2 control: after add-household, alice reads bob's keep-scoped message (sharing works)",
              "present" if "bob-keep-secret" in s1 else "control BROKE — probe blind to keep sharing")
        # (c) REMOVE alice from the household → her NEXT call no longer sees it (NO CACHE).
        await ks.remove_household_member(keep_id=bob_keep_bare, member_email=emails["alice"])
        s2 = await alice_story()
        check("bob-keep-secret" not in s2,
              "L2 resolve_visible_keeps STALE: a LEFT keep's rows vanish on the NEXT call (no cache)",
              "gone after removal" if "bob-keep-secret" not in s2 else "STILL VISIBLE — cache/revocation LEAK")

        # ============ L3 — resolve_visible_keeps EMPTY: member of 0 keeps names the bound ============ #
        holder["email"] = emails["carol"]
        carol_story = str(await ctx.comms(action="story", agent="carol_w1", session="csess",
                                          capability=carol_cap, task_id=t))
        check("bob-keep-secret" not in carol_story,
              "L3 empty: a member of 0 keeps cannot read bob's keep-scoped message", "")
        # The Subject-scope bound line is served and NAMES 0 keeps (never a silent 'no messages').
        check("visible via 0 keep(s)" in carol_story,
              "L3 empty: the render NAMES the bound ('visible via 0 keep(s)'), never a silent empty",
              "bound line present" if "visible via 0 keep(s)" in carol_story else f"MISSING bound line:\n{carol_story}")

    n_fail = sum(1 for ok, _ in _RESULTS if not ok)
    print(f"\n===== STAGE 3 RESULT: {len(_RESULTS) - n_fail}/{len(_RESULTS)} passed, {n_fail} FAILED =====")
    for ok, label in _RESULTS:
        if not ok:
            print(f"  FAILED: {label}")
    sys.exit(1 if n_fail else 0)


def _go() -> None:
    mp = pytest.MonkeyPatch()
    tmp = Path("/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/027cbaf6-5998-40d8-bf1a-7ab83a7a49ee/scratchpad/secaudit_tmp3")
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        asyncio.run(main(mp, tmp))
    finally:
        mp.undo()


if __name__ == "__main__":
    try:
        _go()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)

```

## probe3_await.py

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path("/home/ejprice/PycharmProjects/lore/loremaster/tests")))
import asyncio, pytest
from datetime import UTC, datetime
from _governed_contract import credentialed_app_context, register_owned, seed_message_legacy
from _surreal_harness import run as srun
from surrealdb import RecordID
from loremaster import governed
async def rel(conn, mid, ab, s):
    await srun(conn, "RELATE $m->to->$a SET session=$s, created_at=$now",
              {"m":RecordID("message",mid),"a":RecordID("agent",ab),"s":s,"now":datetime.now(UTC)})
async def main(mp, tmp):
    fails=[]
    async with credentialed_app_context(mp, tmp, principals={"alice":"member","bob":"member"}) as w:
        ctx=w["ctx"]; h=w["holder"]; pids=w["pids"]; em=w["emails"]; conn=w["admin_conn"]; ks=ctx._keep_store
        h["email"]=em["alice"]
        acap,aid=await register_owned(ctx,"alice_w1",owner_principal_id=pids["alice"],session="asess")
        h["email"]=em["bob"]
        bcap,bid=await register_owned(ctx,"bob_w1",owner_principal_id=pids["bob"],session="bsess")
        await ks.get_or_create_keyed(key="session:asess",type="session",keeper_email=em["alice"],name="asess")
        vis=await seed_message_legacy(conn,sender_id=aid,session="asess",seq=10,scope="server",body="VIS-await")
        await rel(conn,vis,aid,"asess")
        inv=await seed_message_legacy(conn,sender_id=bid,session="bsess",seq=11,scope="principal-private",
            owner_principal=RecordID("principal",pids["bob"]),owner_agent=RecordID("agent",bid),body="INV-await-bob")
        await rel(conn,inv,aid,"asess")
        h["email"]=em["alice"]
        # bounded: a visible edge pends, so await returns immediately (snapshot-first)
        r=str(await asyncio.wait_for(ctx.comms(action="await",agent="alice_w1",session="asess",capability=acap), timeout=70))
        ok = ("VIS-await" in r) and ("INV-await-bob" not in r)
        print(f"[{'PASS' if ok else '**FAIL**'}] AWAIT isolation: serves visible, filters bob's invisible")
        if not ok: fails.append("await-iso"); print("   RENDER:\n"+r)
        # §4.D on await: alice naming bob_w1 with alice's cap denies
        try:
            await asyncio.wait_for(ctx.comms(action="await",agent="bob_w1",session="bsess",capability=acap), timeout=70)
            print("[**FAIL**] AWAIT §4.D: naming bob_w1 was NOT denied"); fails.append("await-4d")
        except governed.GovernedDenied:
            print("[PASS] AWAIT §4.D: alice naming bob_w1 (alice cap) DENIES")
    print(f"\n===== AWAIT PROBE: {'ALL PASS' if not fails else 'FAILED '+str(fails)} =====")
    sys.exit(1 if fails else 0)
def _go():
    mp=pytest.MonkeyPatch(); tmp=Path("/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/027cbaf6-5998-40d8-bf1a-7ab83a7a49ee/scratchpad/awaittmp"); tmp.mkdir(parents=True,exist_ok=True)
    try: asyncio.run(main(mp,tmp))
    finally: mp.undo()
_go()

```
