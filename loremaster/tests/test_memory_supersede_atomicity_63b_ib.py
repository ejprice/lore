"""Contract — packet 63b wave i-b: #441 SUPERSEDE ATOMICITY (RES-ATOM). Design
``docs/design/2026-09-03-packet63b-design.md`` §2 (§2.2 shape, §2.3 bounds, §2.4 riders i–vii).
Authored by ``contract-63b-i-b`` (Opus 4.8 contract author; CONTRACT TESTS ONLY — no production).

THE DEFECT AT HEAD ``b2f9b0e`` (design §2.1, ground-truthed via ``lore_get_symbol``):
``LocalMemoryBackend.remember`` runs the supersede-CLOSE (``governed.guarded_write`` — pre-read,
authorize, guarded ``UPDATE … RETURN AFTER``) in ITS OWN transaction, THEN the SQLite ledger
``record``, THEN the new-row UPSERT in a SECOND transaction. Two transactions ⇒ two crash windows:
a failure after the close leaves the predecessor CLOSED (``valid_until`` set, ``superseded_by`` →
a successor id that exists nowhere) with the successor lost or ledger-orphaned.

THE ROOT FIX THIS CONTRACT PINS (design §2.2 — 63-rulings §10.9-D realised):
  - ``governed.authorize_guarded(subject, action, *, table, row_id, audit, store) -> GuardedPlan``
    is the PYTHON leg split out of ``guarded_write`` (pre-read + authorize + RES-2 refuse); it
    MUTATES NOTHING and returns a frozen plan.
  - ``GuardedPlan.fragments(set_fragment) -> list[TxnFragment]`` carries the guarded mutation as a
    FRAGMENT with the conflict guard IN-STORE:
      ``LET $gw_hit = (UPDATE type::record('<t>', $gw_id) SET <set> WHERE (<guard>) RETURN AFTER)``
      ``IF array::len($gw_hit) = 0 { THROW "governed_conflict:<t>:<id>" }``
    ``THROW`` inside ``BEGIN…COMMIT`` aborts the WHOLE txn (store-ref §3 — spec
    ``statements/transaction/throw_error_handling.surql`` / ``control_flow/transaction/
    throw_without_return.surql`` / ``statements/if/control_flow.surql``); ``governed`` maps the
    ``governed_conflict:`` marker → :class:`~loremaster.governed.GovernedConflict` via the SEMANTIC
    root-cause selector ``_txn._domain_root_cause`` (store-ref §3 — never position).
  - ``guarded_write`` becomes ``authorize_guarded`` + ``fragments`` + execute (ONE implementation);
    its Python ``row_count == 0`` conflict branch is UNREACHABLE (the THROW fires first) and DELETED.
  - ``remember``'s order: ``authorize_guarded`` (deny-first, no effect) → ledger ``record`` (durable
    FIRST) → ONE ``execute_transaction`` of ``[*plan.fragments(close_set), upsert(new_row)]`` under
    ``write_guard("remember")`` → on ANY exception, COMPENSATE the ledger
    (``MemoryLedger.delete(memory_id)``) and re-raise.

REMOVED-BEHAVIOUR INVENTORY (the tdd Phase-0 dual, design §2.2 step 3): the Python
``row_count == 0 → GovernedConflict`` branch is DELETED — PRESERVED-WITH-PIN via the in-store THROW
(rider ii proves the THROW is the mechanism; the vanished-row conflict pin in
``test_governed_substrate_63a`` still stands via the guarded fragment). No behaviour is
dropped-silently: the conflict raise moves from Python into the store, and this contract pins that
the move happened (a build that keeps the Python branch but drops the THROW reds rider ii).

RED-AT-HEAD strategy (each RED for the RIGHT reason):
  - BEHAVIOURAL pins drive the EXISTING public ``remember`` end-to-end and assert the atomicity the
    OLD two-transaction structure VIOLATES (predecessor unchanged + ledger compensated on a
    successor-create failure); RED at HEAD is an ASSERTION failure on an observable old-build bug,
    GREEN on the reference build. The successor UPSERT is failed deterministically by a TARGETED
    schema ASSERT on ``note_text`` (the proven ``embedding = 'not-a-float'`` coerce-reject idiom of
    ``test_governed_substrate_63a``, moved to a sentinel the successor's note carries) — so the
    close's ``valid_until`` write is untouched and only the create fails, exactly the discriminating
    window.
  - NEW-API pins exercise ``governed.authorize_guarded`` / ``GuardedPlan`` directly with the §10.6
    ``store_handle(on_acquire=…)`` injection (deterministic, no race) — RED at HEAD because those
    symbols are UNBUILT (an ``AttributeError`` on an unbuilt seam, never a TypeError/parse error in
    THIS test; each such pin says so in its docstring).

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker
for an unreachable store — a LOUD failure, never a skip. pytest runs ``-n auto``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    MEMORY_TABLE,
    _memory_content,
    admin,
    apply_ddl,
    member,
    seed_memory_governed,
    store_handle,
)
from _surreal_harness import (
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.memory.ledger import MemoryLedger
from loremaster.memory.local import LocalMemoryBackend
from loremaster.store import surreal_schema
from loresigil.testing import FakeEmbedder

import lorerunes as pdp
from loremaster import governed

_DIM = 8

# A fixed admin governance Subject (mirrors the i-a rebuild battery's ``_GOV_SUBJECT``): an admin so
# ``scope="server"`` is grantable without wiring a keep household, and a self-owned supersede-close
# needs no audit sink. Distinct principal ids let a FOREIGN-owned predecessor be seeded for the
# bypass / deny-first legs.
_ADMIN = admin("gov_admin", "gov_agent")
_SERVER_SCOPE = "server"

# The sentinel a poisoned successor note carries. A per-test schema ASSERT on ``note_text`` rejects
# exactly this value, so the successor's CREATE (the UPSERT inside the composed txn) fails while the
# predecessor CLOSE (which sets only ``valid_until`` / ``superseded_by``) is untouched — the precise
# window that discriminates the OLD two-txn structure (close commits first) from the NEW atomic one.
_POISON_NOTE = "lore63bib_poison_sentinel_note_do_not_store"


async def _poison_note_text(connection: Any, url: str) -> None:
    """Install a targeted schema ASSERT so a successor note == ``_POISON_NOTE`` is REJECTED by the
    store (a domain rejection that rolls the whole ``BEGIN…COMMIT`` — the proven coerce/ASSERT idiom
    of ``test_governed_substrate_63a``). Applied AFTER the predecessor is seeded, so only the
    successor's UPSERT fails."""
    await run(
        connection,
        f"DEFINE FIELD OVERWRITE note_text ON TABLE {MEMORY_TABLE} "
        f"TYPE string ASSERT $value != '{_POISON_NOTE}'",
    )


# =========================================================================== #
# FIXTURES
# =========================================================================== #


@pytest_asyncio.fixture()
async def supersede_world() -> Any:
    """A ledger-backed :class:`LocalMemoryBackend` on a fresh DB + an admin governance Subject +
    the admin connection (for seeding foreign rows / installing the poison ASSERT / snapshotting).
    The ledger is REQUIRED (#441 compensation is a ledger ``delete``). Reaped on exit."""
    env = make_env(database=unique_database(), dim=_DIM)
    ledger = MemoryLedger(str(Path(env.database + ".memory.db")))
    backend = LocalMemoryBackend(
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
    await backend.ensure_ready()
    # The audit table exists for the bypass-audit leg (rider v); ensure_ready on a fresh AuditStore
    # over the same DB is idempotent DDL (backend.audit_store returns a fresh instance each access).
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


@pytest_asyncio.fixture()
async def governed_db() -> Any:
    """A fresh DB carrying the ``memory`` table (governed DDL) + the admin connection + a test
    :func:`store_handle` — the substrate for the NEW-API unit pins that exercise
    ``governed.authorize_guarded`` / ``GuardedPlan`` directly with the §10.6 acquire-injection.
    Reaped on exit."""
    env = make_env(database=unique_database(), dim=_DIM)
    connection = await connect_admin(env)
    await apply_ddl(connection, surreal_schema.generate_memory_ddl(dim=_DIM), url=env.url)
    try:
        yield connection, env
    finally:
        await connection.close()
        await drop_database(env)


async def _no_chunks(_keys: Any) -> set[str]:
    return set()


async def _memory_row(connection: Any, row_id: str) -> dict[str, Any] | None:
    """The governed + lifecycle columns of one memory row (None if it does not exist)."""
    rows = await run(
        connection,
        "SELECT id, valid_until, superseded_by, owner_principal, owner_agent, scope "
        f"FROM type::record('{MEMORY_TABLE}', $rid)",
        {"rid": row_id},
    )
    return rows[0] if isinstance(rows, list) and rows else None


def _ledger_has(ledger: MemoryLedger, memory_id: str) -> bool:
    """True iff the durable ledger carries a row for ``memory_id`` (the compensation observable)."""
    return any(record.memory_id == memory_id for record in ledger.all_records())


# =========================================================================== #
# §2.4 rider i + iii — ATOMICITY + LEDGER COMPENSATION, behavioural, via the public ``remember``.
# The discriminating scenario: force the SUCCESSOR CREATE (the UPSERT) to fail, and assert the
# predecessor is UNCHANGED and the ledger carries NO orphan. At HEAD the close commits in its OWN
# txn BEFORE the failing upsert, so the predecessor is left closed and the ledger orphaned — RED.
# =========================================================================== #


class TestSupersedeIsAtomicUnderSuccessorFailure:
    """§2.4 rider i (predecessor unchanged / successor absent on failure) + rider iii (ledger
    compensation), proven behaviourally against the OLD build's observable two-transaction bug."""

    async def test_a_failed_successor_create_leaves_the_predecessor_open(
        self, supersede_world: Any
    ) -> None:
        """⚠ RED at HEAD. A supersede whose SUCCESSOR create fails must leave the predecessor
        OPEN (``valid_until`` / ``superseded_by`` still NONE) — the close and the create are ONE
        transaction, so a failed create rolls the close back.

        At HEAD the supersede-close commits in its OWN transaction BEFORE the new-row UPSERT, so
        when the UPSERT fails the predecessor is left CLOSED with ``superseded_by`` pointing at a
        successor that exists nowhere (design §2.1) → this reds. POSITIVE CONTROL in the sibling
        test proves a CLEAN supersede DOES close the predecessor, so this is not a
        never-closes-anything false pass."""
        backend, _ledger, connection, env = supersede_world
        predecessor_id = await backend.remember(
            "predecessor note alpha", kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE
        )
        await _poison_note_text(connection, env.url)
        with pytest.raises(Exception):  # noqa: B017,PT011 - a store domain rejection on the create
            await backend.remember(
                _POISON_NOTE, kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE,
                supersedes=predecessor_id,
            )
        row = await _memory_row(connection, predecessor_id)
        assert row is not None, "the predecessor vanished — the seed/lookup is wrong, not the SUT"
        assert row.get("valid_until") is None and row.get("superseded_by") is None, (
            "a FAILED successor create left the predecessor CLOSED (valid_until/superseded_by set) "
            f"— the close committed in a SEPARATE transaction before the create (design §2.1, the "
            f"#441 defect); the two must be ONE atomic transaction. got {row!r}"
        )

    async def test_a_failed_successor_create_compensates_the_ledger(
        self, supersede_world: Any
    ) -> None:
        """⚠ RED at HEAD (§2.4 rider iii). A supersede whose successor create fails must leave NO
        ledger row for the successor id — the ledger write (durable FIRST) is COMPENSATED
        (``MemoryLedger.delete``) when the composed transaction raises.

        At HEAD the ledger ``record`` runs BEFORE the failing UPSERT and there is NO compensation,
        so the successor id is left ORPHANED in the durable ledger → a later rebuild would revive a
        memory whose store row never landed → this reds."""
        backend, ledger, connection, env = supersede_world
        predecessor_id = await backend.remember(
            "predecessor note bravo", kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE
        )
        before_ids = {record.memory_id for record in ledger.all_records()}
        await _poison_note_text(connection, env.url)
        with pytest.raises(Exception):  # noqa: B017,PT011 - a store domain rejection on the create
            await backend.remember(
                _POISON_NOTE, kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE,
                supersedes=predecessor_id,
            )
        after_ids = {record.memory_id for record in ledger.all_records()}
        assert after_ids == before_ids, (
            "a FAILED successor create left a NEW ledger row (an orphan the next rebuild would "
            f"revive) — the ledger write was not compensated on the failed composed transaction "
            f"(design §2.2 step 4 / §2.4 rider iii). new ids: {after_ids - before_ids}"
        )

    async def test_a_clean_supersede_closes_the_predecessor_and_keeps_the_successor(
        self, supersede_world: Any
    ) -> None:
        """POSITIVE CONTROL (design §2.4 rider i positive control): with NO poison, a supersede
        CLOSES the predecessor (``superseded_by`` → the successor id) AND lands the successor AND
        keeps its ledger row — both rows reach their final state in one transaction. Green at HEAD
        and on the reference build; it discriminates the failure legs above from a build that
        simply never closes/creates anything."""
        backend, ledger, connection, _env = supersede_world
        predecessor_id = await backend.remember(
            "predecessor note charlie", kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE
        )
        successor_id = await backend.remember(
            "successor note charlie", kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE,
            supersedes=predecessor_id,
        )
        predecessor = await _memory_row(connection, predecessor_id)
        successor = await _memory_row(connection, successor_id)
        assert predecessor is not None and successor is not None
        assert predecessor.get("valid_until") is not None, "a clean supersede must CLOSE the predecessor"
        assert str(predecessor.get("superseded_by")) == successor_id, (
            f"the closed predecessor must point at the successor id; got {predecessor.get('superseded_by')!r}"
        )
        assert _ledger_has(ledger, successor_id), (
            "the successor's durable ledger row must survive a clean supersede"
        )


# =========================================================================== #
# §2.4 rider v — the AUDIT rides the SAME composed transaction (extended to the supersede path).
# An admin BYPASS supersede of a FOREIGN row is audited; a REJECTED one appends ZERO. At HEAD the
# close commits (with its audit) in a separate txn before the failing create, so a rejected create
# still leaves the audit row — RED.
# =========================================================================== #


class TestSupersedeAuditRidesTheComposedTransaction:
    """§2.4 rider v — audit atomicity on the composed supersede path (63-rulings §10.6 rider ii,
    extended). A landed admin-bypass supersede appends exactly +1 audit row; a rejected one 0."""

    async def _audit_count(self, connection: Any) -> int:
        rows = await run(connection, "SELECT count() FROM audit GROUP ALL")
        return int(rows[0]["count"]) if isinstance(rows, list) and rows else 0

    async def test_a_rejected_admin_bypass_supersede_appends_no_audit_row(
        self, supersede_world: Any
    ) -> None:
        """⚠ RED at HEAD (§2.4 rider v). An admin superseding a FOREIGN-owned predecessor is an
        audited BYPASS; when the successor CREATE is rejected, the audit row must NOT survive — it
        rides the SAME composed transaction and rolls back with it.

        At HEAD the bypass close (with its composed audit) commits in a SEPARATE transaction before
        the failing create, so the audit row is LEFT BEHIND for a supersede that never completed →
        this reds. POSITIVE CONTROL: a clean bypass supersede appends exactly +1."""
        backend, _ledger, connection, env = supersede_world
        await seed_memory_governed(
            connection, row_id="foreign_pred", dim=_DIM, owner_principal="bob", owner_agent="ag_b1",
            scope="agent-private", note_text="a foreign predecessor",
        )
        before = await self._audit_count(connection)
        await _poison_note_text(connection, env.url)
        with pytest.raises(Exception):  # noqa: B017,PT011 - a store domain rejection on the create
            await backend.remember(
                _POISON_NOTE, kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE,
                supersedes="foreign_pred",
            )
        after = await self._audit_count(connection)
        assert after == before, (
            f"a REJECTED admin-bypass supersede left an audit row (before={before} after={after}) — "
            f"the audit did NOT ride the successor create's transaction (design §2.4 rider v); at "
            f"HEAD the close+audit commit separately before the create fails"
        )

    async def test_a_clean_admin_bypass_supersede_appends_exactly_one_audit_row(
        self, supersede_world: Any
    ) -> None:
        """POSITIVE CONTROL for rider v: a CLEAN admin-bypass supersede of a foreign predecessor
        appends exactly +1 audit row (the bypass close is audited). Proves the ZERO leg above is not
        a never-audits-anything false pass."""
        backend, _ledger, connection, _env = supersede_world
        await seed_memory_governed(
            connection, row_id="foreign_pred2", dim=_DIM, owner_principal="bob", owner_agent="ag_b1",
            scope="agent-private", note_text="another foreign predecessor",
        )
        before = await self._audit_count(connection)
        await backend.remember(
            "a clean bypass successor", kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE,
            supersedes="foreign_pred2",
        )
        after = await self._audit_count(connection)
        assert after == before + 1, (
            f"a clean admin-bypass supersede must append exactly one audit row; before={before} after={after}"
        )


# =========================================================================== #
# §2.4 rider i + ii + iv — the NEW COMPOSED API, exercised directly (deterministic acquire
# injection). RED at HEAD: ``governed.authorize_guarded`` / ``GuardedPlan`` are UNBUILT (an
# AttributeError on an unbuilt seam — never a TypeError in this test). Each test names the seam.
# =========================================================================== #


def _require_new_api() -> None:
    """Fail with a clear message if the NEW #441 composed API is unbuilt (RED-at-HEAD, for the
    RIGHT reason — the seam is a builder deliverable, design §2.2)."""
    assert hasattr(governed, "authorize_guarded"), (
        "governed.authorize_guarded is UNBUILT — the #441 composed supersede API (design §2.2) is a "
        "builder deliverable; this pin is RED-until-built"
    )


class TestTheComposedConflictGuardIsInStore:
    """§2.4 rider i (in-store conflict on the composed path) + rider ii (the THROW is the
    mechanism). The conflict guard is ``LET $gw_hit = (UPDATE … RETURN AFTER); IF array::len($gw_hit)
    = 0 { THROW … }`` composed WITH the successor UPSERT, so a predecessor that moves between the
    plan's pre-read and the composed transaction rolls the WHOLE transaction back."""

    async def test_authorize_guarded_pre_reads_without_mutating(self, governed_db: Any) -> None:
        """⚠ RED-until-built (§2.2 step 1). ``authorize_guarded`` is the PYTHON leg: it pre-reads +
        authorizes and MUTATES NOTHING, returning a frozen ``GuardedPlan``. Proven by snapshotting
        the row before/after and asserting no change, and that ≥1 acquire went through the injected
        handle (it really reached the store)."""
        _require_new_api()
        connection, env = governed_db
        await seed_memory_governed(
            connection, row_id="ag_row", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        handle, calls = store_handle(connection, url=env.url)
        alice = member("alice", "ag_a1", frozenset())
        before = await _memory_row(connection, "ag_row")
        plan = await governed.authorize_guarded(
            alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="ag_row", audit=None, store=handle,
        )
        after = await _memory_row(connection, "ag_row")
        assert before == after, "authorize_guarded MUTATED the row — the Python leg must have NO effect"
        assert calls["acquire"] >= 1, "authorize_guarded did not reach the store off the injected handle"
        assert plan is not None and hasattr(plan, "fragments"), (
            "authorize_guarded must return a GuardedPlan carrying .fragments(set_fragment) (design §2.2)"
        )

    async def test_the_guarded_plan_fragment_carries_the_in_store_throw(self, governed_db: Any) -> None:
        """⚠ RED-until-built (§2.4 rider ii — the THROW IS the mechanism). ``GuardedPlan.fragments``
        must emit the ``IF array::len($gw_hit) = 0 { THROW "governed_conflict:…" }`` guard beside the
        ``LET $gw_hit = (UPDATE … RETURN AFTER)`` — a build that drops it lets a zero-match close
        pass silently and the successor land beside an un-closed predecessor (rider ii)."""
        _require_new_api()
        connection, env = governed_db
        await seed_memory_governed(
            connection, row_id="frag_row", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        handle, _calls = store_handle(connection, url=env.url)
        alice = member("alice", "ag_a1", frozenset())
        plan = await governed.authorize_guarded(
            alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="frag_row", audit=None, store=handle,
        )
        fragments = plan.fragments("note_text = 'x'")
        statements = " ".join(
            statement for fragment in fragments for statement in fragment.statements
        )
        assert "$gw_hit" in statements and "RETURN AFTER" in statements, (
            "the guarded mutation must LET $gw_hit = (UPDATE … RETURN AFTER) so the conflict guard "
            f"can count its rows (design §2.2 step 2). got: {statements!r}"
        )
        assert "THROW" in statements and "governed_conflict:" in statements, (
            "the fragment must carry the IN-STORE conflict guard "
            "IF array::len($gw_hit) = 0 THROW 'governed_conflict:...' — the THROW is the mechanism "
            f"(design §2.4 rider ii). got: {statements!r}"
        )

    async def test_a_rescope_on_the_composed_transaction_conflicts_and_rolls_back(
        self, governed_db: Any
    ) -> None:
        """⚠ RED-until-built (§2.4 rider i, the composed path). A re-scope landing BETWEEN
        ``authorize_guarded``'s pre-read (acquire #1) and the composed transaction (acquire #2) moves
        the predecessor out of alice's WRITE reach → the composed close matches ZERO rows → the
        in-store THROW aborts the WHOLE transaction → :class:`GovernedConflict`, the successor UPSERT
        does NOT land, and the predecessor is UNCHANGED. POSITIVE CONTROL: no re-scope → both the
        close and the successor land in ONE transaction. Deterministic (the acquire wrap), no race."""
        _require_new_api()
        from loremaster.store._txn import execute_transaction

        connection, env = governed_db
        await seed_memory_governed(
            connection, row_id="race_pred", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        alice = member("alice", "ag_a1", frozenset())

        async def _rescope_on_second_acquire(acquire_number: int) -> None:
            if acquire_number == 2:
                await run(
                    connection,
                    f"UPDATE type::record('{MEMORY_TABLE}', 'race_pred') "
                    "SET owner_agent = type::record('agent', 'ag_b1')",
                )

        handle, _calls = store_handle(connection, url=env.url, on_acquire=_rescope_on_second_acquire)
        plan = await governed.authorize_guarded(
            alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="race_pred", audit=None, store=handle,
        )
        # Compose the guarded CLOSE fragment with a successor CREATE, exactly as ``remember`` will.
        successor = _successor_fragment("race_succ")
        close = plan.fragments("valid_until = time::now(), superseded_by = 'race_succ'")
        statement_text, params = _compose_all([*close, successor])
        # The in-store THROW aborts the WHOLE composed transaction (any raise). NOTE (finding #456,
        # §2.2 Reading A): `governed` maps this to GovernedConflict, but `execute_transaction` (the
        # STORE layer) raises SurrealStoreError — it CANNOT import `governed` (a layering fact), so the
        # GovernedConflict TYPE is asserted at the `remember`/`guarded_write` layer, NOT here. What is
        # asserted HERE is the type-INDEPENDENT ROLLBACK (the atomicity property) + that the conflict
        # is DETECTABLE (the classified `governed_conflict` marker reaches the caller — Reading A).
        with pytest.raises(Exception) as conflict:  # noqa: PT011 - classified below
            await execute_transaction(
                statement_text, params, acquire=handle.acquire, drop=handle.drop, url=handle.url,
            )
        assert "governed_conflict" in str(conflict.value), (
            "the composed conflict did not surface the `governed_conflict` marker to the caller — "
            "`governed` cannot map it to GovernedConflict (finding #456 / §2.2 Reading A needs a `_txn` "
            f"classification, outside i-b's writable set). got: {conflict.value!r}"
        )
        # The successor UPSERT was rolled back WITH the conflicting close (whole-transaction abort).
        assert await _memory_row(connection, "race_succ") is None, (
            "the successor row LANDED beside a conflicting close — the THROW did not abort the whole "
            "composed transaction (design §2.4 rider i/ii)"
        )
        predecessor = await _memory_row(connection, "race_pred")
        assert predecessor is not None and predecessor.get("valid_until") is None, (
            "the predecessor was CLOSED despite the conflict — the close must roll back with the txn"
        )

    async def test_the_composed_path_lands_both_rows_without_a_rescope(self, governed_db: Any) -> None:
        """POSITIVE CONTROL for rider i: with NO re-scope, the composed transaction closes the
        predecessor AND lands the successor — both in ONE transaction. RED-until-built (the composed
        API is unbuilt); on the reference build it is GREEN and proves the conflict leg above is not
        a can-never-land false pass."""
        _require_new_api()
        from loremaster.store._txn import execute_transaction

        connection, env = governed_db
        await seed_memory_governed(
            connection, row_id="ok_pred", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        alice = member("alice", "ag_a1", frozenset())
        handle, _calls = store_handle(connection, url=env.url)
        plan = await governed.authorize_guarded(
            alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="ok_pred", audit=None, store=handle,
        )
        successor = _successor_fragment("ok_succ")
        close = plan.fragments("valid_until = time::now(), superseded_by = 'ok_succ'")
        statement_text, params = _compose_all([*close, successor])
        await execute_transaction(
            statement_text, params, acquire=handle.acquire, drop=handle.drop, url=handle.url,
        )
        predecessor = await _memory_row(connection, "ok_pred")
        assert predecessor is not None and predecessor.get("valid_until") is not None, (
            "the composed transaction did not close the predecessor"
        )
        assert await _memory_row(connection, "ok_succ") is not None, (
            "the composed transaction did not land the successor"
        )


class TestAuthorizeGuardedIsDenyFirst:
    """§2.4 rider iv — ``authorize_guarded`` denies a FOREIGN supersede BEFORE any durable effect."""

    async def test_a_member_superseding_a_foreign_row_denies_with_zero_effect(
        self, governed_db: Any
    ) -> None:
        """⚠ RED-until-built (§2.4 rider iv). A member superseding a FOREIGN-owned row is DENIED by
        ``authorize_guarded`` (deny-first) and NOTHING mutates — no store effect (before == after).
        RED at HEAD because ``authorize_guarded`` is unbuilt; on the reference build the deny fires
        before the plan is ever handed a set fragment."""
        _require_new_api()
        connection, env = governed_db
        await seed_memory_governed(
            connection, row_id="bob_row", dim=_DIM, owner_principal="bob", owner_agent="ag_b1",
            scope="agent-private", note_text="bob owns this",
        )
        handle, _calls = store_handle(connection, url=env.url)
        alice = member("alice", "ag_a1", frozenset())
        before = await _memory_row(connection, "bob_row")
        with pytest.raises(governed.GovernedDenied):
            await governed.authorize_guarded(
                alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="bob_row", audit=None, store=handle,
            )
        after = await _memory_row(connection, "bob_row")
        assert before == after, (
            "a denied authorize_guarded mutated the row — deny-first must have ZERO effect"
        )


# =========================================================================== #
# §2.4 rider vi — ONE IMPLEMENTATION. ``remember``'s supersede-close AND ``invalidate`` BOTH route
# through the shared ``governed.authorize_guarded`` (via ``guarded_write`` = authorize_guarded +
# fragments + execute). Pinned STRUCTURALLY (both reference the shared seam) — the mutation proof
# (change the deny predicate → both red) is the adversary's / builder's, run against the reference
# build; here we red at HEAD because the shared seam is unbuilt (no site references it yet).
# =========================================================================== #


class TestSupersedeAndInvalidateShareOneImplementation:
    """§2.4 rider vi — the supersede-close and ``invalidate`` are ONE implementation."""

    def test_both_close_paths_route_through_authorize_guarded(self) -> None:
        """⚠ RED-until-built (§2.4 rider vi). ``guarded_write`` must be defined as
        ``authorize_guarded`` + ``GuardedPlan.fragments`` + execute (ONE implementation), so BOTH
        ``invalidate`` and the supersede-close reach the store through the SAME authorization seam. A
        build that keeps two hand-rolled close paths (or never introduces ``authorize_guarded``) reds
        this. Structural: ``guarded_write``'s source must reference ``authorize_guarded`` and
        ``fragments``; the deny-predicate mutation proof is the adversary's/builder's job."""
        import inspect

        assert hasattr(governed, "authorize_guarded"), (
            "governed.authorize_guarded is UNBUILT — guarded_write cannot yet be its composition "
            "(design §2.2 step 3); RED-until-built"
        )
        source = inspect.getsource(governed.guarded_write)
        assert "authorize_guarded" in source and "fragments" in source, (
            "guarded_write is not the composition authorize_guarded + GuardedPlan.fragments + execute "
            "— the supersede-close and invalidate must share ONE authorization implementation "
            "(design §2.2 step 3 / §2.4 rider vi)"
        )
        # The Python `if row_count == 0: raise GovernedConflict` branch is DELETED (the THROW fires
        # in-store). Target the CONDITIONAL (a code-shaped phrase that will not appear in a docstring
        # explaining the removal), not any prose mention of `row_count == 0`.
        assert "if row_count == 0" not in source, (
            "guarded_write still carries the Python `if row_count == 0 → GovernedConflict` branch — it "
            "is UNREACHABLE once the in-store THROW fires and must be DELETED (design §2.2 step 3, "
            "removed-behaviour inventory: preserved-with-pin via the THROW)"
        )


# --------------------------------------------------------------------------- #
# Composition helpers — build a successor UPSERT fragment + compose fragments the way ``remember``
# will, so the NEW-API pins exercise the SAME ``compose`` seam production uses.
# --------------------------------------------------------------------------- #


def _successor_fragment(row_id: str) -> Any:
    """A successor-CREATE ``TxnFragment`` (a valid SCHEMAFULL governed memory row via the shared
    :func:`_memory_content`) to compose beside the guarded close — the successor half of the atomic
    supersede. It simply must LAND (positive control) or NOT (conflict); its content is the required
    column set, so the reference-build positive control is not a masked schema-reject."""
    from loremaster.store._txn import TxnFragment

    content = _memory_content(_DIM, f"successor {row_id}")
    content["scope"] = "agent-private"
    id_param = f"succ_id_{row_id}"
    content_param = f"succ_content_{row_id}"
    return TxnFragment(
        statements=[f"UPSERT type::record('{MEMORY_TABLE}', ${id_param}) CONTENT ${content_param}"],
        params={id_param: row_id, content_param: content},
    )


def _compose_all(fragments: list[Any]) -> tuple[str, dict[str, Any]]:
    """Compose fragments into ONE ``BEGIN…COMMIT`` via the production ``compose`` seam."""
    from loremaster.store._txn import compose

    return compose(*fragments)
