"""Contract — packet 63a-iv: the #439 DEDUP × OWNERSHIP owner-fold (design §10.9-B) — RED before
the 63a-iv build. Authored by ``contract-63a-iv`` (Opus 4.8 contract author — tests ONLY).

SPEC: ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §10.9-B (fold the EXACT owner pair
into ``derive_memory_id`` so a content collision across DIFFERENT owners is UNREPRESENTABLE —
allowlist-the-safe applied to IDENTITY; guard-the-collision alone is REJECTED). The three seizure
constructions here are PROMOTED verbatim-in-intent from cold-audit-63a-iii §REPRO
(``TestCandidateA_*``), FLIPPED from "the attacker wins" (green at HEAD) to "the create-path mints a
DISTINCT id and leaves the foreign row UNCHANGED" (green only on the owner-folded build).

WHY the id-derivation and not a WHERE-guard (store-ref §2, cited): ``UPSERT <id> … WHERE`` on an
existing id whose WHERE fails is a SILENT NO-OP (cannot create) — the §2 degradation shape. So the
unrepresentability comes from the DERIVATION: different owners ⇒ different id ⇒ no collision, never a
guarded overwrite. Removing the owner fold ⇒ the ids collide again ⇒ every seizure construction goes
green-for-the-attacker ⇒ these pins red (the mutation proof, §MUTATION in the report).

RED-at-HEAD mechanics (HEAD ``f77ac24``):
- The three seizure pins + the positive control run through the SHIPPED ``backend.remember`` (built),
  so they COLLECT and RUN at HEAD; at HEAD ``derive_memory_id(text, refs_stamp)`` folds NO owner, the
  ids collide, and the create-UPSERT SEIZES the foreign row → ``bob_id == alice_id`` and the row is
  mutated → the "distinct id" / "row unchanged" assertions FAIL (RED-for-the-right-reason).
- ``test_derive_memory_id_folds_the_owner_pair`` calls ``derive_memory_id`` by the ruled owner
  keywords; at HEAD that signature is unbuilt → TypeError → RED (the ``retrofit_world``-raises-at-HEAD
  idiom this test tree already uses for unbuilt builder deliverables).

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped on exit.
"""

from __future__ import annotations

from typing import Any

import pytest
from _surreal_harness import run
from loremaster.memory.backend import derive_memory_id, derive_refs_stamp

# SHIPPED retrofit fixtures/helpers, reused VERBATIM (the §REPRO import set — ONE world-builder, no
# clone). pytest resolves the imported fixtures in this module's namespace (the §REPRO precedent).
from test_memory_retrofit_63a import (  # noqa: F401  (fixtures used by name)
    _EMAIL_ALICE,
    _EMAIL_BOB,
    _exercise_invalidate,
    _exercise_remember,
    _minted_credential,
    _one,
    alice_capability,
    bob_capability,
    retrofit_world,
)

from loremaster import governed

# The ruled owner-fold keywords (design §10.9-B). The uuid5 STRING field ORDER is the builder's
# choice; the PARAM NAMES are the contract (descriptive-consistent-naming law) — the fold lives in
# derive_memory_id and folds BOTH the owner principal AND the owner agent.
_OWNER_PRINCIPAL_KW = "owner_principal"
_OWNER_AGENT_KW = "owner_agent"


def _bare_s(value: Any) -> str:
    """Bare id of a str OR a RecordID (the admin SELECT returns RecordID objects) — §REPRO helper."""
    text = str(value)
    return text.partition(":")[2] or text


async def _read_governed(admin_conn: Any, memory_id: str) -> dict[str, Any]:
    """The governed columns of one memory row, read as admin (§REPRO helper)."""
    row: dict[str, Any] = _one(
        await run(
            admin_conn,
            "SELECT owner_principal, owner_agent, scope, valid_until, importance "
            "FROM type::record('memory', $id)",
            {"id": _bare_s(memory_id)},
        )
    )
    return row


# --------------------------------------------------------------------------- #
# 10.9-B — the create-path seizure is UNREPRESENTABLE: a non-owner re-remembering a foreign row's
# exact (text, refs) mints a DISTINCT id and leaves the foreign row UNCHANGED. (§REPRO, flipped.)
# --------------------------------------------------------------------------- #


class TestCreateCollisionAcrossOwnersIsUnrepresentable:
    """#439 root — the owner-folded id makes a cross-owner content collision impossible, so the
    create-UPSERT can never land on a foreign-owned row. Promotes cold-audit §REPRO ``TestCandidateA_*``."""

    async def test_a_non_owner_reremember_mints_a_distinct_id_and_does_not_seize_or_rescope(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any  # noqa: F811
    ) -> None:
        """§REPRO construction 1 (cross-principal seizure + re-scope), FLIPPED. ⚠ RED at HEAD: today
        the ids collide and bob's create-UPSERT seizes+re-scopes alice's row. On the owner-folded
        build bob's id is DISTINCT and alice's row is UNTOUCHED. CONTROL: bob's guarded invalidate
        DENIES (the guarded door already works — proves the pin sees a live isolation boundary)."""
        backend, principal_store, _keep, admin_conn, _env, _project_keep = retrofit_world
        alice = await principal_store.get_by_email(_EMAIL_ALICE)
        bob = await principal_store.get_by_email(_EMAIL_BOB)
        alice_pid = _bare_s(alice.id)
        bob_pid = _bare_s(bob.id)
        colliding_text = "owner-fold collision text — same for alice and bob"

        alice_id = await _exercise_remember(
            backend, text=colliding_text, capability=alice_capability
        )
        before = await _read_governed(admin_conn, alice_id)
        assert _bare_s(before["owner_principal"]) == alice_pid, "setup: alice must own her note"
        alice_scope = before["scope"]

        # CONTROL: the GUARDED door denies bob (isolation boundary is live).
        with pytest.raises(governed.GovernedDenied):
            await _exercise_invalidate(backend, memory_id=alice_id, capability=bob_capability)
        control = await _read_governed(admin_conn, alice_id)
        assert _bare_s(control["owner_principal"]) == alice_pid, "guarded door leaked"

        # THE FIX: bob re-remembering the identical text (with a private scope) mints a DISTINCT id,
        # never a collision — so alice's row is UNCHANGED (owner, scope, validity all preserved).
        bob_id = await _exercise_remember(
            backend, text=colliding_text, capability=bob_capability, scope="principal-private"
        )
        assert _bare_s(bob_id) != _bare_s(alice_id), (
            "the create-path id COLLIDED across owners — the owner fold is missing (#439): "
            f"bob_id {bob_id!r} == alice_id {alice_id!r}"
        )
        after = await _read_governed(admin_conn, alice_id)
        assert _bare_s(after["owner_principal"]) == alice_pid, (
            f"alice's row was SEIZED — owner now {after['owner_principal']!r} (was {alice_pid!r})"
        )
        assert after["scope"] == alice_scope, (
            f"alice's row was RE-SCOPED — scope now {after['scope']!r} (was {alice_scope!r})"
        )
        assert after["valid_until"] is None, "alice's row was retired by the collision"
        # bob's OWN new row carries bob's ownership + the private scope he requested.
        bob_row = await _read_governed(admin_conn, bob_id)
        assert _bare_s(bob_row["owner_principal"]) == bob_pid
        assert bob_row["scope"] == "principal-private"

    async def test_a_sibling_agent_reremember_mints_a_distinct_id_and_does_not_seize(
        self, retrofit_world: Any, alice_capability: Any  # noqa: F811
    ) -> None:
        """§REPRO construction 2 (intra-principal sibling seizure — LIVE TODAY), FLIPPED. worker_2 is
        a SECOND agent of the SAME principal: it cannot ``guarded_write`` worker_1's private note
        (CONTROL: invalidate DENIES) and, on the owner-folded build, CANNOT seize it via re-remember
        either — the owner AGENT is folded, so a different agent mints a DISTINCT id. ⚠ RED at HEAD:
        today owner_agent is not folded, the ids collide, worker_2 seizes worker_1's row."""
        backend, principal_store, _keep, admin_conn, _env, _project_keep = retrofit_world
        alice = await principal_store.get_by_email(_EMAIL_ALICE)
        alice_pid = _bare_s(alice.id)
        text = "alice principal-private note only worker_1 may write"

        worker1_id = await _exercise_remember(
            backend, text=text, capability=alice_capability, scope="principal-private"
        )
        owner_agent_1 = _bare_s((await _read_governed(admin_conn, worker1_id))["owner_agent"])

        async with _minted_credential(
            retrofit_world, email=_EMAIL_ALICE, agent_name="alice_worker_2"
        ) as worker2:
            # CONTROL: a sibling agent cannot guarded_write another agent's private note.
            with pytest.raises(governed.GovernedDenied):
                await _exercise_invalidate(backend, memory_id=worker1_id, capability=worker2)
            # THE FIX: the sibling's re-remember mints a DISTINCT id (owner_agent folded).
            worker2_id = await _exercise_remember(
                backend, text=text, capability=worker2, scope="principal-private"
            )
            assert _bare_s(worker2_id) != _bare_s(worker1_id), (
                "intra-principal collision — owner_agent NOT folded (#439 construction 2, LIVE): "
                f"worker2_id {worker2_id!r} == worker1_id {worker1_id!r}"
            )
        after = await _read_governed(admin_conn, worker1_id)
        assert _bare_s(after["owner_principal"]) == alice_pid
        assert _bare_s(after["owner_agent"]) == owner_agent_1, (
            f"worker_1's row was re-owned to the sibling agent (owner_agent now {after['owner_agent']!r})"
        )

    async def test_a_non_owner_reremember_does_not_revive_a_retired_foreign_note(
        self, retrofit_world: Any, alice_capability: Any, bob_capability: Any  # noqa: F811
    ) -> None:
        """§REPRO construction 3 (revive a retired foreign note), FLIPPED. alice retires her own note
        (valid_until set); bob re-remembers the identical text. ⚠ RED at HEAD: today the collision
        resets valid_until → bob un-retires alice's note. On the owner-folded build bob's id is
        DISTINCT → alice's note stays retired."""
        backend, _principal_store, _keep, admin_conn, _env, _project_keep = retrofit_world
        text = "alice note alice will retire then a non-owner must not revive"

        alice_id = await _exercise_remember(backend, text=text, capability=alice_capability)
        await _exercise_invalidate(backend, memory_id=alice_id, capability=alice_capability)
        retired = await _read_governed(admin_conn, alice_id)
        assert retired["valid_until"] is not None, "setup: alice's note must be retired"

        bob_id = await _exercise_remember(backend, text=text, capability=bob_capability)
        assert _bare_s(bob_id) != _bare_s(alice_id), (
            f"revive-collision: bob_id {bob_id!r} == alice_id {alice_id!r} (owner fold missing)"
        )
        after = await _read_governed(admin_conn, alice_id)
        assert after["valid_until"] is not None, "bob's re-remember REVIVED alice's retired note"


class TestSameAgentDedupIsPreserved:
    """POSITIVE CONTROL / anti-over-fix (design §10.9-B — "the taught contract's actual purpose is
    preserved exactly"). GREEN at HEAD and on the build. Discriminates against an over-fix that folds
    a nonce/timestamp and breaks dedup for EVERYONE: the SAME (principal, agent) re-saving its OWN
    identical text MUST still dedup in place (same id)."""

    async def test_the_same_agent_reremembering_its_own_text_dedups_in_place(
        self, retrofit_world: Any, alice_capability: Any  # noqa: F811
    ) -> None:
        backend, _principal_store, _keep, admin_conn, _env, _project_keep = retrofit_world
        text = "alice re-saves her own identical note twice"
        first_id = await _exercise_remember(backend, text=text, capability=alice_capability)
        i0 = float((await _read_governed(admin_conn, first_id))["importance"])
        second_id = await _exercise_remember(backend, text=text, capability=alice_capability)
        assert _bare_s(second_id) == _bare_s(first_id), (
            "the same agent's identical re-save did NOT dedup — the owner fold OVER-fixed (a "
            f"nonce/timestamp folded in): first {first_id!r} != second {second_id!r}"
        )
        # count() proves it is ONE row, not two colliding on distinct ids.
        rows = await run(admin_conn, "SELECT count() FROM memory GROUP ALL", {})
        assert _one(rows)["count"] == 1, "the same-agent re-save created a SECOND row (dedup broken)"
        _ = i0  # importance read only asserts the row was readable; dedup is the property under test


class TestDeriveMemoryIdFoldsTheOwnerPair:
    """§10.9-B SHAPE pin (unit, order-agnostic, ∀ owner-pairs — the quantifier law, forced with ≥2
    distinct principals AND ≥2 distinct agents). ⚠ RED at HEAD: ``derive_memory_id(text, refs_stamp)``
    takes no owner keywords → TypeError. The uuid5 STRING field order is the builder's choice; this
    pin asserts only that BOTH owner components are folded (a change to either axis changes the id)
    WHILE (text, refs_stamp) remain part of the dedup basis."""

    @staticmethod
    def _mid(text: str, refs_stamp: str, principal: str, agent: str) -> str:
        return derive_memory_id(
            text,
            refs_stamp,
            **{_OWNER_PRINCIPAL_KW: principal, _OWNER_AGENT_KW: agent},
        )

    def test_the_owner_pair_and_the_content_all_fold_into_the_id(self) -> None:
        refs = derive_refs_stamp([])
        text = "owner-fold shape probe"
        base = self._mid(text, refs, "principal_a", "agent_1")
        # determinism: same (text, refs, owner pair) ⇒ same id (the dedup contract preserved).
        assert base == self._mid(text, refs, "principal_a", "agent_1")
        # ∀ owner-pairs — ≥2 distinct principals: a different principal ⇒ a DISTINCT id.
        assert base != self._mid(text, refs, "principal_b", "agent_1"), "owner_principal not folded"
        # ∀ owner-pairs — ≥2 distinct agents: a different agent ⇒ a DISTINCT id.
        assert base != self._mid(text, refs, "principal_a", "agent_2"), "owner_agent not folded"
        # the existing dedup basis SURVIVES the fold: text and refs_stamp still vary the id
        # (refs_stamp is a plain str at this seam, so two distinct stamps must diverge the id).
        assert base != self._mid("different text", refs, "principal_a", "agent_1"), "text dropped"
        assert base != self._mid(text, "distinct-refs", "principal_a", "agent_1"), "refs_stamp dropped"
