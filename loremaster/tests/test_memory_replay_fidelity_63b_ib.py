"""Contract — packet 63b wave i-b: #436 (replay drops governance) + #453 (rebuild REVIVES retired
memories). Design ``docs/design/2026-09-03-packet63b-design.md`` §3.1 (the class is WIDER than the
three stamps) + §3.2 (stamp on replay FROM the ledger; the fidelity PROPERTY). Authored by
``contract-63b-i-b`` (Opus 4.8 contract author; CONTRACT TESTS ONLY — no production).

THE DEFECT AT HEAD ``b2f9b0e`` (design §3.1, ground-truthed via ``lore_get_symbol``):
``rebuild_embeddings`` DROPS the ``memory`` table (``_recreate_memory_table``) and REPLAYS every row
from the durable ledger (``restore_from_ledger`` → ``_replay_record``). But:
  - ``_ledger_metadata`` stamps only ``kind/importance/labels/source/expires_at/supersedes`` — it
    carries NO ``owner_principal/owner_agent/scope/created_at/valid_until/superseded_by``;
  - ``_replay_record`` → ``_build_content(now=datetime.now())`` stamps NOTHING governed and sets
    ``valid_from = created_at = now`` (the rebuild instant);
  - the ``MemoryLedger`` has NO ``retire`` verb, so ``invalidate`` and the supersede-close are never
    recorded in the ledger AT ALL.
So a rebuild LOSES, for every row, its owner pair + scope + original ``created_at``/``valid_from``,
AND REVIVES every invalidated / superseded memory (#453 — the wider class §3.1 names).

THE ROOT FIX THIS CONTRACT PINS (design §3.2):
  - the ledger metadata gains ``owner_principal/owner_agent/scope/created_at`` at ``record`` time and
    ``valid_until/superseded_by`` via a NEW ``MemoryLedger.retire`` verb (``invalidate`` + the
    supersede path call it AFTER the store commit); ``MemoryLedger.delete`` is the #441 compensation;
  - ``_replay_record`` reconstructs FAITHFULLY: ``_build_content`` takes the stamps as parameters —
    owner pair, scope, ``created_at``/``valid_from`` from the ledger, ``valid_until``/``superseded_by``
    when present — so a rebuild is a byte-identical round trip;
  - LEGACY ledger rows (pre-63b, no governance keys) replay as NONE/NONE owner, NONE scope —
    FAIL-CLOSED (member-invisible by the 61 predicate), the named legacy fallback.

REMOVED-BEHAVIOUR ADJUDICATION (the P8d dual, design §3.1): ``_replay_record``'s OLD behaviour
(re-stamp ``created_at``/``valid_from`` to now, drop every governed/lifecycle stamp) was the #436/#453
BUG — adjudicated OLD-BUG, NOT re-pinned in its old form; this contract pins the CORRECTED behaviour.

RED-AT-HEAD strategy (behavioural, each RED for the RIGHT reason): drive the EXISTING public
``remember`` / ``invalidate`` / ``rebuild_embeddings`` end-to-end over a DIRTY store spanning every
lifecycle state, snapshot the governed + lifecycle columns, rebuild, re-snapshot, and assert
byte-identical. At HEAD the snapshot DIFFERS (owner/scope/created_at lost, valid_until revived) — a
per-COLUMN diff so a build that drops ANY one stamp reds naming that column (design §3.2 mutation
proof). New ledger verbs (``retire``/``delete``) are asserted present (RED-until-built).

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker.
pytest runs ``-n auto``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest_asyncio
from _governed_contract import MEMORY_TABLE, admin
from _surreal_harness import (
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.memory.ledger import MemoryLedger
from loremaster.memory.local import LocalMemoryBackend
from loresigil.testing import FakeEmbedder

_DIM = 8
_SERVER_SCOPE = "server"

# TWO admin governance Subjects — DISTINCT (principal, agent) pairs so the fidelity fixture carries
# OWNER DIVERSITY (a build that hardcodes one owner on replay fails on the other — fixtures must
# discriminate). Both are admins so ``scope="server"`` is grantable and a cross-owner (bypass) close
# is authorised.
_ADMIN_A = admin("gov_admin_a", "gov_agent_a")
_ADMIN_B = admin("gov_admin_b", "gov_agent_b")

# The governance + lifecycle columns a faithful rebuild MUST round-trip (design §3.2 snapshot).
_STAMP_COLUMNS = (
    "owner_principal",
    "owner_agent",
    "scope",
    "valid_from",
    "valid_until",
    "superseded_by",
    "created_at",
)


async def _no_chunks(_keys: Any) -> set[str]:
    return set()


def _build_ledger_backend(env: Any, ledger: MemoryLedger) -> LocalMemoryBackend:
    return LocalMemoryBackend(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=_DIM,
        user=env.user,
        password=env.password,
        embedder=FakeEmbedder(dim=_DIM),
        existing_chunks=_no_chunks,
        ledger=ledger,
    )


@pytest_asyncio.fixture()
async def dirty_world() -> Any:
    """A ledger-backed backend + admin connection, with the memory table + audit table ready. The
    test body builds the DIRTY store (every lifecycle state) through the backend so every row is BOTH
    in the store (snapshottable) AND in the ledger (replayable). Reaped on exit."""
    env = make_env(database=unique_database(), dim=_DIM)
    ledger = MemoryLedger(str(Path(env.database + ".memory.db")))
    backend = _build_ledger_backend(env, ledger)
    await backend.ensure_ready()
    await backend.audit_store.ensure_ready()
    connection = await connect_admin(env)
    try:
        yield backend, ledger, connection, env
    finally:
        await connection.close()
        await backend.close()
        ledger.close()
        await drop_database(env)
        Path(env.database + ".memory.db").unlink(missing_ok=True)


async def _snapshot_stamps(connection: Any) -> dict[str, dict[str, Any]]:
    """Snapshot every memory row's governance + lifecycle columns, keyed by bare id, normalised to
    strings so a RecordID / datetime compares stably across the drop→replay round trip."""
    rows = await run(
        connection,
        "SELECT id, owner_principal, owner_agent, scope, valid_from, valid_until, "
        f"superseded_by, created_at FROM {MEMORY_TABLE}",
    )
    snapshot: dict[str, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        row_id = str(row["id"]).split(":", 1)[-1]
        snapshot[row_id] = {
            column: (None if row.get(column) is None else str(row.get(column)))
            for column in _STAMP_COLUMNS
        }
    return snapshot


def _diff_snapshots(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[str]:
    """Per-row, per-COLUMN diff (design §3.2: 'the diff reds naming the column'). Returns a human
    list of every row/column that changed across the rebuild — empty ⟺ byte-identical."""
    changes: list[str] = []
    if set(before) != set(after):
        changes.append(f"row-set changed: lost={set(before) - set(after)} gained={set(after) - set(before)}")
    for row_id in sorted(set(before) & set(after)):
        for column in _STAMP_COLUMNS:
            if before[row_id][column] != after[row_id][column]:
                changes.append(
                    f"{row_id}.{column}: {before[row_id][column]!r} -> {after[row_id][column]!r}"
                )
    return changes


async def _seed_dirty_lifecycle(backend: LocalMemoryBackend) -> dict[str, str]:
    """Create the FULL lifecycle spectrum through the backend (design §3.2's dirty store): a live
    owned row, a SUPERSEDED pair, an INVALIDATED row, and an admin-BYPASS-closed foreign row — every
    row owned by a real Subject and recorded in the ledger. Returns the ids by role."""
    live = await backend.remember("a live owned note", kind="fact", subject=_ADMIN_A, scope=_SERVER_SCOPE)
    pred = await backend.remember("a predecessor note", kind="fact", subject=_ADMIN_A, scope=_SERVER_SCOPE)
    succ = await backend.remember(
        "a successor note", kind="fact", subject=_ADMIN_A, scope=_SERVER_SCOPE, supersedes=pred
    )
    invalid = await backend.remember(
        "a soon-invalid note", kind="fact", subject=_ADMIN_B, scope=_SERVER_SCOPE
    )
    await backend.invalidate(invalid, subject=_ADMIN_B)  # self-close, no audit
    foreign = await backend.remember("a foreign note", kind="fact", subject=_ADMIN_B, scope=_SERVER_SCOPE)
    await backend.invalidate(foreign, subject=_ADMIN_A)  # admin-A BYPASS-closes admin-B's row (audited)
    return {"live": live, "pred": pred, "succ": succ, "invalid": invalid, "foreign": foreign}


# =========================================================================== #
# §3.2 — THE FIDELITY PROPERTY (the QUANTIFIER LAW: ∀ lifecycle states, forced by fixture).
# =========================================================================== #


class TestRebuildIsFaithfulAcrossEveryLifecycleState:
    """§3.2 fidelity PROPERTY (trust-doctrine, constructed): a rebuild is a byte-identical round trip
    of every governance + lifecycle stamp, over a DIRTY store spanning every lifecycle state."""

    async def test_rebuild_preserves_every_governance_and_lifecycle_stamp(
        self, dirty_world: Any
    ) -> None:
        """⚠ RED at HEAD (design §3.2). Snapshot the governed + lifecycle columns of a dirty store,
        run ``rebuild_embeddings``, re-snapshot: BYTE-IDENTICAL. At HEAD the ledger carries none of
        these stamps and ``_replay_record`` re-stamps ``created_at``/``valid_from`` to the rebuild
        instant and drops owner/scope/valid_until — so the diff is non-empty, and the failure NAMES
        each changed row+column (design §3.2 mutation proof: dropping ANY one stamp reds its column).
        ANTI-VACUITY: the dirty store has ≥5 rows spanning 4 lifecycle states + 2 distinct owners."""
        backend, _ledger, connection, _env = dirty_world
        ids = await _seed_dirty_lifecycle(backend)
        before = await _snapshot_stamps(connection)
        assert len(before) >= 5, f"the dirty store is too thin to discriminate — {len(before)} rows"
        await backend.rebuild_embeddings()
        after = await _snapshot_stamps(connection)
        changes = _diff_snapshots(before, after)
        assert not changes, (
            "rebuild_embeddings did NOT round-trip the governance + lifecycle stamps (design §3.2) — "
            f"the ledger does not carry them and/or _replay_record re-stamps them. seeded ids={ids}. "
            f"CHANGED (row.column: before -> after):\n" + "\n".join(changes)
        )

    async def test_the_dirty_store_carries_owner_diversity(self, dirty_world: Any) -> None:
        """FIXTURES-MUST-DISCRIMINATE guard: the dirty store has ≥2 DISTINCT owner principals, so
        ``test_rebuild_preserves…`` cannot pass with a build that hardcodes a single owner on replay.
        Green at HEAD and on the build — it protects the property above, it is not itself the #436 pin."""
        backend, _ledger, connection, _env = dirty_world
        await _seed_dirty_lifecycle(backend)
        snapshot = await _snapshot_stamps(connection)
        owners = {row["owner_principal"] for row in snapshot.values() if row["owner_principal"] is not None}
        assert len(owners) >= 2, (
            f"the dirty store carries only {len(owners)} distinct owner principal(s) — a single-owner "
            "fixture cannot discriminate a build that hardcodes the owner on replay"
        )


# =========================================================================== #
# #453 — a rebuild must NOT REVIVE a retired / superseded memory (design §3.1 the wider class).
# =========================================================================== #


class TestRebuildDoesNotReviveRetiredMemories:
    """#453 — the specific revive-on-rebuild defect §3.1 names, pinned on its own so a regression is
    unambiguous. An invalidated row and a superseded predecessor STAY closed after a rebuild."""

    async def test_an_invalidated_memory_stays_retired_after_rebuild(self, dirty_world: Any) -> None:
        """⚠ RED at HEAD (#453). Invalidate a memory (``valid_until`` set), rebuild, and assert it is
        STILL retired. At HEAD the close is never recorded in the ledger, so the rebuild replays the
        row as LIVE (``valid_until`` NONE) — a retired memory RESURRECTED, invisible to no one → reds."""
        backend, _ledger, connection, _env = dirty_world
        memory_id = await backend.remember(
            "a note to retire", kind="fact", subject=_ADMIN_A, scope=_SERVER_SCOPE
        )
        await backend.invalidate(memory_id, subject=_ADMIN_A)
        before = await run(
            connection,
            f"SELECT valid_until FROM type::record('{MEMORY_TABLE}', $rid)", {"rid": memory_id},
        )
        assert before and before[0].get("valid_until") is not None, "setup: the memory must be retired first"
        await backend.rebuild_embeddings()
        after = await run(
            connection,
            f"SELECT valid_until FROM type::record('{MEMORY_TABLE}', $rid)", {"rid": memory_id},
        )
        assert after and after[0].get("valid_until") is not None, (
            "rebuild_embeddings REVIVED a retired memory (valid_until went back to NONE) — the ledger "
            "does not record closes and _replay_record replays it as live (#453 / design §3.1)"
        )

    async def test_a_superseded_predecessor_stays_closed_after_rebuild(self, dirty_world: Any) -> None:
        """⚠ RED at HEAD (#453). Supersede a memory, rebuild, assert the predecessor is STILL closed
        AND still points at its successor. At HEAD the supersede-close is not in the ledger, so the
        rebuild revives the predecessor as live with no successor link → reds."""
        backend, _ledger, connection, _env = dirty_world
        pred = await backend.remember("pred to supersede", kind="fact", subject=_ADMIN_A, scope=_SERVER_SCOPE)
        succ = await backend.remember(
            "succ that supersedes", kind="fact", subject=_ADMIN_A, scope=_SERVER_SCOPE, supersedes=pred
        )
        await backend.rebuild_embeddings()
        after = await run(
            connection,
            f"SELECT valid_until, superseded_by FROM type::record('{MEMORY_TABLE}', $rid)", {"rid": pred},
        )
        assert after and after[0].get("valid_until") is not None, (
            "rebuild_embeddings REVIVED a superseded predecessor (valid_until went back to NONE) — #453"
        )
        assert after and str(after[0].get("superseded_by")) == succ, (
            "the revived predecessor lost its successor link (superseded_by) — got "
            f"{after[0].get('superseded_by')!r}"
        )


# =========================================================================== #
# #436 — the LEDGER carries governance + lifecycle (the durable source of the reconstruction).
# =========================================================================== #


class TestTheLedgerCarriesGovernanceAndLifecycle:
    """#436 — the ledger is the durable source but at HEAD does not carry the state the store needs
    to be reconstructed. This pins that the ledger metadata + the new ``retire``/``delete`` verbs
    carry it (the mechanism the fidelity property rests on)."""

    def _metadata_for(self, ledger: MemoryLedger, memory_id: str) -> dict[str, Any]:
        for record in ledger.all_records():
            if record.memory_id == memory_id:
                return record.metadata
        raise AssertionError(f"no ledger row for {memory_id!r}")

    async def test_remember_records_owner_scope_and_created_at_in_the_ledger(
        self, dirty_world: Any
    ) -> None:
        """⚠ RED at HEAD (design §3.2). A ``remember`` writes ``owner_principal``/``owner_agent``/
        ``scope``/``created_at`` into the durable ledger row's metadata (so a rebuild can restore
        them). At HEAD ``_ledger_metadata`` stamps none of these → the keys are absent → reds."""
        backend, ledger, _connection, _env = dirty_world
        memory_id = await backend.remember(
            "a governed ledger note", kind="fact", subject=_ADMIN_A, scope=_SERVER_SCOPE
        )
        metadata = self._metadata_for(ledger, memory_id)
        missing = [
            key for key in ("owner_principal", "owner_agent", "scope", "created_at")
            if metadata.get(key) in (None, "")
        ]
        assert not missing, (
            f"the ledger metadata is missing governance/lifecycle keys {missing} — a rebuild cannot "
            f"restore what the durable source never carried (design §3.2 / #436). metadata={metadata!r}"
        )
        assert str(metadata.get("owner_principal")) == "gov_admin_a", (
            f"the ledger recorded the WRONG owner_principal — got {metadata.get('owner_principal')!r}"
        )
        assert metadata.get("scope") == _SERVER_SCOPE, (
            f"the ledger recorded the WRONG scope — got {metadata.get('scope')!r}"
        )

    async def test_invalidate_retires_the_ledger_row(self, dirty_world: Any) -> None:
        """⚠ RED at HEAD (design §3.2). ``invalidate`` records the close in the ledger via
        ``MemoryLedger.retire`` (``valid_until`` set, ``superseded_by`` NONE) — so a rebuild does not
        revive it. At HEAD there is NO ``retire`` verb and ``invalidate`` never touches the ledger →
        the ledger metadata carries no ``valid_until`` → reds (RED-until-built: the verb is a builder
        deliverable, so the pin also names its absence)."""
        backend, ledger, _connection, _env = dirty_world
        assert hasattr(MemoryLedger, "retire"), (
            "MemoryLedger.retire is UNBUILT — the close-durability verb is a builder deliverable "
            "(design §3.2); RED-until-built"
        )
        memory_id = await backend.remember("retire-me", kind="fact", subject=_ADMIN_A, scope=_SERVER_SCOPE)
        await backend.invalidate(memory_id, subject=_ADMIN_A)
        metadata = self._metadata_for(ledger, memory_id)
        assert metadata.get("valid_until") not in (None, ""), (
            "invalidate did not record the close in the ledger (no valid_until in metadata) — a rebuild "
            f"will revive the retired memory (design §3.2 / #453). metadata={metadata!r}"
        )

    def test_the_ledger_gains_the_retire_and_delete_verbs(self) -> None:
        """⚠ RED-until-built (design §3.2 / §2.2). ``MemoryLedger`` gains ``retire`` (close durability,
        #436/#453) and ``delete`` (the #441 supersede compensation). Both are builder deliverables;
        this names their absence unambiguously so the RED is not mistaken for a behavioural miss."""
        assert hasattr(MemoryLedger, "retire"), "MemoryLedger.retire is UNBUILT (design §3.2)"
        assert hasattr(MemoryLedger, "delete"), (
            "MemoryLedger.delete is UNBUILT (design §2.2 step 4, #441 compensation)"
        )


# =========================================================================== #
# §3.2 — LEGACY ledger rows (pre-63b, no governance keys) replay FAIL-CLOSED (NONE/NONE, NONE scope).
# =========================================================================== #


class TestLegacyLedgerRowsReplayFailClosed:
    """§3.2 named legacy fallback — a pre-63b ledger row (no governance keys) replays with a NONE
    owner pair and NONE scope (member-invisible by the 61 predicate; admin migrates it later). This
    is the ONE exception to the byte-identical fidelity property."""

    async def test_a_legacy_ledger_row_replays_with_no_owner_and_no_scope(self, dirty_world: Any) -> None:
        """A ledger row lacking the governance keys (a pre-63b write) replays into the store with a
        NONE owner pair and NONE scope — never a GUESSED owner. Green at HEAD (which stamps nothing)
        and on the build (which fails closed); it PROTECTS the fidelity property from a build that
        would 'helpfully' backfill a legacy row with a wrong owner (that would red HERE)."""
        backend, ledger, connection, _env = dirty_world
        # A legacy write: only the pre-63b metadata keys, NO governance keys.
        ledger.record(
            memory_id="00000000-0000-5000-8000-000000000abc",
            text="a legacy pre-63b note",
            metadata={"kind": "fact", "importance": 0.5, "labels": [],
                      "source": {"kind": "test", "trust": "experiential"}, "expires_at": None,
                      "supersedes": None},
            refs_stamp="",
        )
        await backend.rebuild_embeddings()
        rows = await run(
            connection,
            "SELECT owner_principal, owner_agent, scope FROM "
            "type::record('memory', '00000000-0000-5000-8000-000000000abc')",
        )
        assert rows, "the legacy ledger row was not replayed into the store at all"
        row = rows[0]
        assert row.get("owner_principal") is None and row.get("owner_agent") is None, (
            f"a legacy ledger row replayed with a GUESSED owner (must be NONE/NONE, fail-closed) — got "
            f"principal={row.get('owner_principal')!r} agent={row.get('owner_agent')!r}"
        )
        assert row.get("scope") is None, (
            "a legacy ledger row replayed with a scope (must be NONE, member-invisible) — got "
            f"{row.get('scope')!r}"
        )
