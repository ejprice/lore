"""Contract — packet 63b wave i-b: the F5-ALLOWLIST DATA REGISTRATION for #441/#436's new memory
mutation shapes. Design ``docs/design/2026-09-03-packet63b-design.md`` §5.1 Q2 (i-a → i-b dependency).
Authored by ``contract-63b-i-b`` (Opus 4.8 contract author; CONTRACT TESTS ONLY — no production).

i-b registers its NEW memory mutation shapes into i-a's LANDED F5 instrument — the allowlist DATA
(``test_memory_enforcement_63b_ia.MEMORY_TREE_ALLOWLIST`` + its effect predicates), NEVER the
instrument itself (``_governed_contract``'s detector / ``_sdk_guard``'s hook — a change THERE is a
STOP-and-flag to the lead). Two DATA changes were made in the i-a module (in this wave's writable set,
per §5.1) and this module PINS that a WRONG build reds the F5 coverage/classify:

  (1) ``_effect_upsert`` WIDENED (design §5.1 Q2 ii): #441 composes the supersede-close into the SAME
      transaction as the new-row create, so the ``remember``/``_replay_record`` observed write now
      carries a created row AND an updated predecessor. The predicate CLASSIFIES it iff every delta is
      a create OR a close (changed columns ⊆ {valid_until, superseded_by}); a governed-column SEIZURE
      composed beside the create → UNCLASSIFIED. (The #441 composed close in ``remember`` is BUILT by
      ``GuardedPlan.fragments`` with a dynamic ``type::record('{table}', …)`` name → NOT L1-derived;
      L2 sees its EFFECT under ``remember``'s label — so it needs no L1 site, only the widened effect.)

  (2) ``_REPLAY_CLOSE_ENTRY`` ADDED (design §5.1 Q2 / §3.2): #436's ``_replay_record`` composes a
      predecessor-close ``UPDATE type::record('{MEMORY_TABLE}', $p) …`` — a NEW raw L1 site in
      ``_replay_record`` — into the replay transaction. deny-by-default requires its OWN site-backed
      allowlist entry, a sibling of ``_UPSERT_ENTRY`` on the ``_replay_record`` frame.

★RED-AT-b2f9b0e COUPLING★: the ``_replay_record`` close literal is a builder deliverable (#436), so at
HEAD ``_REPLAY_CLOSE_ENTRY``'s site is NOT L1-derived. That reds (a) the i-a ghost pin
(``test_every_derived_site_is_in_a_site_backed_entry_and_no_ghost``) and (b)
``test_the_replay_close_site_is_registered_and_derived`` HERE — both GREEN once the builder adds the
#436 close literal. The integration pin below reds at HEAD because ``remember``'s supersede close is a
SEPARATE ``guarded_write`` observed write at HEAD, not composed under ``remember`` (design §2.2).

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker.
pytest runs ``-n auto``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest_asyncio
from _governed_contract import (
    MEMORY_TABLE,
    ObservedEffect,
    ObservedWrite,
    RowDelta,
    SchemaDelta,
    admin,
    classify_tree_observed_write,
    governed_table_raw_mutation_sites_in_tree,
    observe_governed_table_writes,
)
from _surreal_harness import connect_admin, drop_database, make_env, unique_database
from loremaster.memory.ledger import MemoryLedger
from loremaster.memory.local import LocalMemoryBackend
from loresigil.testing import FakeEmbedder

# The DATA under test (imported from the i-a module — this is where the F5 allowlist DATA lives, §5.1).
from test_memory_enforcement_63b_ia import (  # noqa: E402
    _REPLAY_CLOSE_ENTRY,
    MEMORY_TREE_ALLOWLIST,
    _effect_upsert,
)

_DIM = 8
_SERVER_SCOPE = "server"
_ADMIN = admin("gov_admin_f5", "gov_agent_f5")


# --------------------------------------------------------------------------- #
# Constructed-effect helpers (design §1.2 ObservedEffect / RowDelta).
# --------------------------------------------------------------------------- #


def _empty_schema() -> SchemaDelta:
    return SchemaDelta(added=frozenset(), removed=frozenset(), changed=frozenset())


def _effect(*row_deltas: RowDelta) -> ObservedEffect:
    return ObservedEffect(row_deltas=tuple(row_deltas), schema_delta=_empty_schema())


def _created(row_id: str) -> RowDelta:
    """A CREATE of a governed memory row (owner stamped) — the new-row half of a supersede."""
    after = {"owner_principal": "principal:gov_admin_f5", "owner_agent": "agent:gov_agent_f5",
             "scope": _SERVER_SCOPE, "note_text": "successor", "valid_from": "t", "created_at": "t"}
    return RowDelta(id=row_id, kind="created", changed_columns=frozenset(after), before=None, after=after)


def _close(row_id: str) -> RowDelta:
    """A predecessor CLOSE — the composed supersede's close half (valid_until + superseded_by only)."""
    before = {"valid_until": None, "superseded_by": None}
    after = {"valid_until": "t", "superseded_by": "succ_id"}
    return RowDelta(
        id=row_id, kind="updated",
        changed_columns=frozenset({"valid_until", "superseded_by"}), before=before, after=after,
    )


def _seizing_close(row_id: str) -> RowDelta:
    """A close that ALSO SEIZES a governed column (``scope``) — the wrong build the widening catches."""
    before = {"valid_until": None, "superseded_by": None, "scope": "keep:victim"}
    after = {"valid_until": "t", "superseded_by": "succ_id", "scope": "keep:attacker"}
    return RowDelta(
        id=row_id, kind="updated",
        changed_columns=frozenset({"valid_until", "superseded_by", "scope"}), before=before, after=after,
    )


# =========================================================================== #
# (2) — the #436 replay-close L1 SITE is REGISTERED and (once built) DERIVED.
# =========================================================================== #


class TestTheReplayCloseSiteIsRegistered:
    """§5.1 Q2 — the #436 ``_replay_record`` predecessor-close is a NEW derived L1 site with its own
    site-backed allowlist entry (deny-by-default). This is the ghost-coupling from i-b's side."""

    def test_the_replay_close_site_is_registered_and_derived(self) -> None:
        """⚠ RED at HEAD (§5.1 Q2, the ghost coupling). ``_REPLAY_CLOSE_ENTRY`` is REGISTERED in the
        allowlist (this contract's DATA change — green), and its site MUST be L1-derived from the tree
        (RED at HEAD: the #436 close literal in ``_replay_record`` is a builder deliverable, so the
        derivation does not yet yield it — GREEN once the builder composes the close). This is the
        i-b-side witness of the same coupling the i-a ghost pin carries."""
        assert _REPLAY_CLOSE_ENTRY in MEMORY_TREE_ALLOWLIST, (
            "the #436 replay-close entry is not registered in MEMORY_TREE_ALLOWLIST (§5.1 Q2)"
        )
        assert _REPLAY_CLOSE_ENTRY.l1_site, (
            "the replay-close entry must be a SITE-backed L1 entry (a raw literal), not a label frame "
            "— it derives from a real UPDATE literal in _replay_record"
        )
        derived = governed_table_raw_mutation_sites_in_tree(MEMORY_TABLE)
        assert _REPLAY_CLOSE_ENTRY.site in derived, (
            "the #436 replay-close UPDATE literal is NOT L1-derived from _replay_record — the builder "
            f"has not composed the predecessor-close into the replay transaction yet (design §3.2 / "
            f"§5.1 Q2). derived _replay_record sites: "
            f"{sorted(s for s in derived if s.function == '_replay_record')}"
        )

    def test_the_replay_close_site_is_in_exactly_one_entry(self) -> None:
        """deny-by-default: the replay-close site is claimed by EXACTLY ONE allowlist entry (never two,
        never zero once derived). Green — protects the registration from a duplicate/omitted entry."""
        owners = [e for e in MEMORY_TREE_ALLOWLIST if e.l1_site and e.site == _REPLAY_CLOSE_ENTRY.site]
        assert len(owners) == 1, (
            f"the replay-close site is claimed by {len(owners)} allowlist entries (must be exactly ONE "
            f"— deny-by-default): {[e.pin for e in owners]}"
        )


# =========================================================================== #
# (1) — the WIDENED ``_effect_upsert`` classifies the composed close and rejects a seizure.
# =========================================================================== #


class TestTheWidenedUpsertEffectPredicate:
    """§5.1 Q2 ii — the widened ``_effect_upsert`` accepts the #441 composed supersede shape (create +
    predecessor close) and REJECTS a governed-column seizure smuggled beside the create. These pin the
    DATA change; a build that reverts the widening (accepts a seizing update) reds the rejection leg."""

    def test_the_widened_effect_accepts_a_create_plus_close(self) -> None:
        """A composed supersede write — one created row + one predecessor close (valid_until +
        superseded_by only) — CLASSIFIES under the widened predicate (design §5.1 Q2 ii)."""
        assert _effect_upsert(_effect(_created("succ"), _close("pred"))), (
            "the widened _effect_upsert rejected a LEGITIMATE composed supersede (create + close) — it "
            "must accept a created row beside a predecessor close touching only {valid_until, superseded_by}"
        )

    def test_the_widened_effect_rejects_a_close_that_seizes_a_governed_column(self) -> None:
        """A composed write whose 'close' ALSO changes a GOVERNED column (``scope``) is UNCLASSIFIED —
        the exact wrong build the widening exists to catch (a seizure composed beside the create). A
        build that reverts to the coarse ``all(kind in {created, updated})`` would ACCEPT this → reds."""
        assert not _effect_upsert(_effect(_created("succ"), _seizing_close("pred"))), (
            "the widened _effect_upsert ACCEPTED a composed close that SEIZED a governed column (scope) "
            "— the coarse predicate is back; an updated row must touch ONLY {valid_until, superseded_by}"
        )

    def test_the_widened_effect_rejects_a_deleted_row(self) -> None:
        """A create/replay frame never DELETES; a deleted row in the observed effect is UNCLASSIFIED."""
        deleted = RowDelta(id="x", kind="deleted", changed_columns=frozenset(), before={"a": 1}, after=None)
        assert not _effect_upsert(_effect(_created("succ"), deleted)), (
            "the widened _effect_upsert accepted a DELETED row under the create/replay frame"
        )


# =========================================================================== #
# deny-by-default — an UNLABELLED composed close is UNCLASSIFIED (the F5 root property holds for the
# new shape); a LABELLED one classifies; a labelled SEIZURE does not.
# =========================================================================== #


class TestTheComposedCloseIsClassifiedOnlyWhenLabelledAndClean:
    """§1.2/§1.4 over the i-b shape — a composed supersede write classifies iff it carries the
    ``remember`` (or ``_replay_record``) label AND its effect passes the widened predicate."""

    def test_an_unlabelled_composed_close_is_unclassified(self) -> None:
        """An observed composed-close write carrying NO write_guard label is UNCLASSIFIED (deny-by-
        default) — the F5 root property (an unattributed governed mutation is denied) holds for the
        NEW composed shape, not just the single-row writes."""
        write = ObservedWrite(label=None, effect=_effect(_created("succ"), _close("pred")))
        assert not classify_tree_observed_write(write, MEMORY_TREE_ALLOWLIST), (
            "an UNLABELLED composed supersede write CLASSIFIED — deny-by-default is not firing on the "
            "new composed shape (§1.2 / design §5.1 Q2)"
        )

    def test_a_labelled_clean_composed_close_classifies(self) -> None:
        """POSITIVE CONTROL: the SAME composed-close effect under the ``remember`` label CLASSIFIES —
        so the unlabelled-reject leg above is not a can-never-classify false pass."""
        write = ObservedWrite(label="remember", effect=_effect(_created("succ"), _close("pred")))
        assert classify_tree_observed_write(write, MEMORY_TREE_ALLOWLIST), (
            "a labelled clean composed supersede did NOT classify — the widened effect + remember frame "
            "must accept it (design §5.1 Q2 ii)"
        )

    def test_a_labelled_seizing_composed_close_is_unclassified(self) -> None:
        """A composed write under the ``remember`` label whose close SEIZES a governed column is
        UNCLASSIFIED — the label does not launder an off-predicate effect (§1.4 the label leg RUNS the
        effect predicate). Also holds for the ``_replay_record`` frame (both share the widened predicate)."""
        for label in ("remember", "_replay_record"):
            write = ObservedWrite(label=label, effect=_effect(_created("succ"), _seizing_close("pred")))
            assert not classify_tree_observed_write(write, MEMORY_TREE_ALLOWLIST), (
                f"a labelled ({label}) composed write that SEIZED a governed column CLASSIFIED — the "
                "label laundered an off-predicate effect (§1.4 the label leg must run the effect predicate)"
            )


# =========================================================================== #
# INTEGRATION — a #441 composed supersede is ONE observed write under the ``remember`` label (create +
# close), not two writes. RED at HEAD: the supersede-close is a SEPARATE ``guarded_write`` write.
# =========================================================================== #


async def _no_chunks(_keys: Any) -> set[str]:
    return set()


@pytest_asyncio.fixture()
async def ledger_backend() -> Any:
    """A ledger-backed backend + admin subject for the composed-supersede observation (design §5.1)."""
    env = make_env(database=unique_database(), dim=_DIM)
    ledger = MemoryLedger(str(Path(env.database + ".memory.db")))
    backend = LocalMemoryBackend(
        url=env.url, namespace=env.namespace, database=env.database, dim=_DIM,
        user=env.user, password=env.password, embedder=FakeEmbedder(dim=_DIM),
        existing_chunks=_no_chunks, ledger=ledger,
    )
    await backend.ensure_ready()
    await backend.audit_store.ensure_ready()
    connection = await connect_admin(env)
    try:
        yield backend, connection, env
    finally:
        await connection.close()
        await backend.close()
        ledger.close()
        await drop_database(env)
        Path(env.database + ".memory.db").unlink(missing_ok=True)


class TestAComposedSupersedeIsOneObservedWriteUnderRemember:
    """§2.2 / §5.1 — the #441 composed supersede is ONE observed write under the ``remember`` label
    carrying BOTH a created row and a predecessor close; at HEAD the close is a SEPARATE
    ``guarded_write`` observed write (two transactions), so this reds."""

    async def test_the_supersede_close_is_composed_under_the_remember_label(
        self, ledger_backend: Any
    ) -> None:
        """⚠ RED at HEAD (design §2.2 / §5.1 Q2 ii). Observe a supersede: there must be a ``remember``
        write whose effect carries BOTH a created row AND an updated predecessor-close, and NO separate
        ``guarded_write`` close observed for the supersede. At HEAD the close runs in its own
        ``guarded_write`` transaction BEFORE the create, so there is a ``guarded_write`` write and the
        ``remember`` write has NO close delta → reds."""
        backend, _connection, _env = ledger_backend
        predecessor = await backend.remember(
            "pred for composed observation", kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE
        )
        with observe_governed_table_writes(MEMORY_TABLE) as observed:
            await backend.remember(
                "succ for composed observation", kind="fact", subject=_ADMIN, scope=_SERVER_SCOPE,
                supersedes=predecessor,
            )
        writes = [w for w in observed if w.effect is not None and not w.effect.is_empty]
        remember_writes = [w for w in writes if w.label == "remember"]
        guarded_writes = [w for w in writes if w.label == "guarded_write"]
        # The composed supersede is ONE remember write carrying a created row AND a predecessor close.
        composed = [
            w for w in remember_writes
            if any(d.kind == "created" for d in w.effect.row_deltas)
            and any(d.kind == "updated" for d in w.effect.row_deltas)
        ]
        assert composed, (
            "no single `remember`-labelled write carried BOTH a created row and a predecessor close — "
            "the supersede close was not composed into the create's transaction (design §2.2). "
            f"remember writes' deltas: {[[d.kind for d in w.effect.row_deltas] for w in remember_writes]}; "
            f"guarded_write writes: {len(guarded_writes)}"
        )
        assert not guarded_writes, (
            "the supersede close ran as a SEPARATE `guarded_write` transaction (two transactions, the "
            "#441 defect) — it must be composed under the `remember` label. "
            f"guarded_write writes: {len(guarded_writes)}"
        )
