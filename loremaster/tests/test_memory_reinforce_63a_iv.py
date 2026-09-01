"""Contract — packet 63a-iv: F-B (``_reinforce``) — design §10.9-C. Authored by ``contract-63a-iv``.

§10.9-C RULES ``_reinforce`` an ACCEPTED read-side-effect on a NON-governed column, allowlisted with
TWO pins (so the acceptance cannot silently drift into an isolation hole):
  (i)  the bump set ≡ the SERVED (post-filter recall) set — a row the caller CANNOT READ is never
       bumped. Holds by construction today (``recall`` calls ``_reinforce(memories)`` on the
       post-``read_filter`` list); pinned so a refactor to reinforce PRE-filter candidates reds.
  (ii) the ``_reinforce`` statement touches ONLY ``importance`` — a statement-shape pin; the day it
       grows a second column it LEAVES the allowlist and must route through ``guarded_write``.

Both pins are GREEN at HEAD (they pin the CURRENTLY-CORRECT, allowlist-justified behaviour as an
invariant — §10.9-C ACCEPTS ``_reinforce`` as-is); each is a discriminator with a stated wrong build.

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any, cast

from _surreal_harness import run
from loremaster.memory.backend import RecalledMemory
from loremaster.memory.local import LocalMemoryBackend
from loresigil.testing import FakeEmbedder
from pydantic import SecretStr
from test_memory_retrofit_63a import (  # noqa: F401 (fixtures used by name)
    _EMAIL_ALICE,
    _exercise_recall,
    _exercise_remember,
    _one,
    alice_capability,
    bob_capability,
    retrofit_world,
)

# The memory columns (local.py module constants, cited by value — the statement-shape pin).
_IMPORTANCE_COL = "importance"
_ISOLATION_COLS = ("owner_principal", "owner_agent", "scope")
_VALIDITY_COL = "valid_until"


def _bare_s(value: Any) -> str:
    text = str(value)
    return text.partition(":")[2] or text


async def _importance(admin_conn: Any, memory_id: str) -> float:
    row = _one(
        await run(
            admin_conn,
            "SELECT importance FROM type::record('memory', $id)",
            {"id": _bare_s(memory_id)},
        )
    )
    return float(row["importance"])


class TestReinforceBumpsOnlyTheServedSet:
    """§10.9-C (i) — a row the caller CANNOT READ is NEVER reinforced. The bump set is the SERVED
    (post-``read_filter``) recall set, not the pre-filter candidate set."""

    async def test_a_recall_never_bumps_a_row_the_caller_cannot_read(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any  # noqa: F811
    ) -> None:
        """⚠ GREEN at HEAD (reinforce runs on the post-filter set) — REDDENS a refactor that
        reinforces the PRE-filter candidate set (bumping a row the caller may not see). alice's
        principal-private note matches bob's query but is NOT read-visible to bob (a different
        principal), so bob's recall must leave its importance UNTOUCHED. POSITIVE CONTROL below proves
        reinforcement is LIVE (so a 'not bumped' here means 'unreadable', not 'reinforce is off')."""
        backend, _principal_store, _keep, admin_conn, _env, _project_keep = retrofit_world
        marker = "reinforce isolation marker topic quebec private"
        alice_id = await _exercise_remember(
            backend, text=marker, capability=alice_capability, scope="principal-private"
        )
        before = await _importance(admin_conn, alice_id)
        bob_hits = await _exercise_recall(backend, query=marker, capability=bob_capability)
        assert all(_bare_s(h.id) != _bare_s(alice_id) for h in bob_hits), (
            "bob's served recall set INCLUDED alice's principal-private note — read isolation leaked "
            "(the reinforce pin's premise)"
        )
        after = await _importance(admin_conn, alice_id)
        assert after == before, (
            f"bob's recall BUMPED alice's unreadable private row's importance "
            f"({before} -> {after}) — reinforce ran on the PRE-filter candidate set (§10.9-C (i))"
        )

    async def test_a_recall_does_reinforce_a_row_the_caller_can_read(
        self, retrofit_world: Any, alice_capability: Any  # noqa: F811
    ) -> None:
        """POSITIVE CONTROL (C1 law — a negative result needs a positive control): the OWNER recalling
        its OWN readable note DOES bump its importance, proving reinforcement is live. Without this,
        the negative pin above could pass because reinforcement is simply broken/off."""
        backend, _principal_store, _keep, admin_conn, _env, _project_keep = retrofit_world
        marker = "reinforce liveness marker topic romeo readable"
        alice_id = await _exercise_remember(backend, text=marker, capability=alice_capability)
        before = await _importance(admin_conn, alice_id)
        hits = await _exercise_recall(backend, query=marker, capability=alice_capability)
        assert any(_bare_s(h.id) == _bare_s(alice_id) for h in hits), "setup: alice must recall her own note"
        after = await _importance(admin_conn, alice_id)
        assert after > before, (
            f"the owner's recall did NOT reinforce its own readable row ({before} -> {after}) — "
            "reinforcement is off, so the isolation pin above would be vacuous"
        )


async def _capture_reinforce_statements() -> list[str]:
    """The RESOLVED SurrealQL statement(s) ``_reinforce`` emits, captured by wrapping ``_query`` on a
    real backend instance (no store: ``__init__`` is lazy; ``_query`` is intercepted). Capturing the
    RESOLVED string (``SET importance = …``, not the ``{_COL_IMPORTANCE}`` source token) is what makes
    the pin NON-VACUOUS — a source regex misses the interpolated constant (a false pass, C1)."""
    async def _no_chunks(_keys: Sequence[str]) -> set[str]:
        return set()  # unused by _reinforce

    backend = LocalMemoryBackend(
        url="ws://127.0.0.1:18000",
        namespace="ns",
        database="db",
        dim=8,
        user="u",
        password=SecretStr("p"),
        embedder=FakeEmbedder(dim=8),
        existing_chunks=_no_chunks,
    )
    captured: list[str] = []

    async def _fake_query(statement: str, params: dict[str, Any] | None = None) -> Any:
        captured.append(statement)
        return None

    backend._query = _fake_query  # type: ignore[method-assign]
    # a fake recalled row — _reinforce reads only ``.id`` (cast to satisfy the typed signature).
    await backend._reinforce([cast(RecalledMemory, SimpleNamespace(id="deadbeef"))])
    return captured


class TestReinforceStatementTouchesOnlyImportance:
    """§10.9-C (ii) — the ``_reinforce`` UPDATE sets ONLY ``importance`` (a NON-governed column). A
    second column in that SET grows it out of the allowlist and MUST route through ``guarded_write``.
    Statement-shape pin over the RESOLVED runtime statement (not the source — the source's
    ``{_COL_IMPORTANCE}`` interpolation makes a source regex vacuous); mutation-provable — add
    ``, scope = …`` to the SET and this reds."""

    async def test_the_reinforce_update_sets_only_the_importance_column(self) -> None:
        """⚠ GREEN at HEAD — REDDENS a build whose ``_reinforce`` SET names any column besides
        ``importance`` (an isolation column especially)."""
        statements = await _capture_reinforce_statements()
        assert statements, "reinforce emitted NO statement for one recalled row — the pin is vacuous"
        mutating = [s for s in statements if " SET " in s]
        assert mutating, f"reinforce emitted no ` SET ` mutation: {statements!r}"
        assigned: set[str] = set()
        for statement in mutating:
            set_body = statement.split(" SET ", 1)[1]
            # column identifiers on the LHS of an '=' (function calls like math::min sit on the RHS).
            assigned |= set(re.findall(r"([a-z_][a-z_0-9]*)\s*=", set_body))
        assert assigned, f"the SET body parsed to NO assigned column (vacuous): {mutating!r}"
        forbidden = assigned & set(_ISOLATION_COLS + (_VALIDITY_COL,))
        assert not forbidden, (
            f"_reinforce's SET assigns a GOVERNED/validity column {sorted(forbidden)} — it left the "
            f"non-governed-column allowlist (§10.9-C (ii)) and must route through guarded_write"
        )
        assert assigned == {_IMPORTANCE_COL}, (
            f"_reinforce's SET assigns columns other than 'importance': {sorted(assigned)} — a second "
            f"column leaves the allowlist (§10.9-C (ii)); route it through guarded_write or re-adjudicate"
        )
