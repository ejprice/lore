"""Contract — packet 63b wave ii-a: the F5 MESSAGE / TO population registries. Design
``docs/design/2026-09-03-packet63b-design.md`` §1.5c-iii (the governed-population SET is DERIVED from
``surreal_schema``; a new population with no F5 case is a deny-by-default RED), §1.4 (label frames carry
effect predicates; the migrate frame is a four-leg exempt), §4.F (message becomes governed → the
population set grows to {memory, message, to}), §4.A/§4.B/§4.C (the send / drain / ack / migrate effect
predicates). Authored by ``contract-63b-ii-a`` (Opus 4.8 contract author — TESTS ONLY).

WHAT THIS FILE OWNS (the F5 case-registry DATA seam, per the ii-a writable set): the ``message`` and
``to`` allowlist DATA + effect predicates, and the population-growth + deny-by-default coverage pins
that make {memory, message, to} a CHECKED VARIABLE. The i-a MEMORY instrument
(``_governed_contract``'s detector, the guard hook) is UNTOUCHED — imported, never edited.

THE RED_ADJUDICATED(owner=63b-ii) PIN (design §5 / §1.9 item 2 / FLAG F-A): the i-a pin
``test_memory_enforcement_63b_ia.py::TestTheGovernedPopulationSetIsADerivedOutput::
test_the_derived_population_set_is_the_known_set`` (⚠ the ORIGINAL contract cited the non-existent
class ``TestTheDerivedPopulationSetIsExactlyMemory`` — corrected here by reviser-63b-ii-a) formerly
asserted ``governed_populations() == {memory}``. The granted F-A cross-file edit updated its known set to
``{memory, message, to}`` (RED_ADJUDICATED(owner=63b-ii), RED at HEAD until §4.F wires the emitter),
so it and the sibling pin here (``test_the_derived_population_set_grows_to_memory_message_to``) now
AGREE — both GREEN on the ii-a build (the old ``== {memory}`` CONTRADICTED this file's grown-set pin).
⚠ 63c-i-a r2 (amendment-2 A1): the i-a copy was DELETED (DUAL comment in place) and the known set is
now {agent, briefed, memory, message, to}, asserted ONCE, here — see that pin's docstring.

SCOPE SPLIT with ii-b (design §5): ii-a registers ALL ``to`` L1 sites (send RELATE + drain/ack UPDATE)
so deny-by-default is satisfied the moment ``to`` becomes a population, with the send/drain/ack effect
predicates from §1.4 (drain: {seen_at} only, before NONE; ack: ⊆ {acked_at, ack_note}, before NONE).
ii-b drives the LIVE drain/ack classification GREEN; ii-a proves the DATA + the LIVE SEND classification.

⚠ FLAG F-MIGRATE-GOLDEN (report §Decisions): the ``_migrate_message_owner`` exempt entry needs the exact
GOLDEN statement the builder executes, but the message migrate's statement shape (a single
``UPDATE message SET owner_agent = sender, owner_principal = sender.owner_principal, scope = $scope WHERE
owner_principal IS NONE`` vs a per-row/composed form) is a builder choice. The golden below is the
adjudicator's PROVISIONAL oracle (the single-UPDATE reading, matching the memory function-local pattern);
the effect predicate is robust regardless. Builder + adversary reconcile the exact golden — a leg-2 RED
means the statement drifted from this oracle, which is the pin working.

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker.
pytest runs ``-n auto``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    ObservedEffect,
    ObservedWrite,
    RowDelta,
    SchemaDelta,
    TreeMutationSite,
    TreeWriteAllowlistEntry,
    classify_tree_observed_write,
    credentialed_app_context,
    governed_populations,
    governed_table_raw_mutation_sites_in_tree,
    observe_governed_table_writes,
    register_owned,
)
from loremaster.store import surreal_schema

_MESSAGE_TABLE = surreal_schema.MESSAGE_TABLE  # "message"
_TO_RELATION = surreal_schema.TO_RELATION  # "to"
_MESSAGES_PY = "loremaster/loremaster/messages.py"
_PRINCIPALS_PY = "loremaster/loremaster/principals.py"


def _empty_schema() -> SchemaDelta:
    return SchemaDelta(added=frozenset(), removed=frozenset(), changed=frozenset())


# =========================================================================== #
# THE ADJUDICATED EFFECT PREDICATES (design §1.4 / §4.A / §4.B / §4.C) — each says what its frame is
# ALLOWED to do over the WHOLE ObservedEffect. Pure functions; unit-pinned below AND applied by the
# classifier via the allowlist entry. (The owner ≡ SUBJECT exact match is R1's separate behavioural
# pin ``test_a_credentialed_send_stamps_exactly_the_subjects_pair`` in test_comms_send_scope_63b_ii_a.py
# — these structural legs check the SHAPE of the change, incl. owner_agent==sender (R8), per the memory
# _effect_upsert precedent.)
# =========================================================================== #

_COL_OWNER_PRINCIPAL = "owner_principal"
_COL_OWNER_AGENT = "owner_agent"
_COL_SCOPE = "scope"
_COL_SENDER = "sender"  # R8 — the message row's own sender (RecordID(agent, sender.id)); owner_agent == this
_COL_SEEN_AT = "seen_at"
_COL_ACKED_AT = "acked_at"
_COL_ACK_NOTE = "ack_note"
_ACK_COLUMNS = frozenset({_COL_ACKED_AT, _COL_ACK_NOTE})


def _effect_send_message(effect: ObservedEffect) -> bool:
    """``send`` creates a governed ``message`` row: EVERY delta is a CREATE whose row carries a
    non-NONE owner pair AND scope, AND whose ``owner_agent`` IS the row's own ``sender`` (R8 — reviser).

    Design §4.A: the created message's ``(owner_principal, owner_agent)`` is the RESOLVED subject's
    pair and ``scope`` is the session keep. The ==SUBJECT owner EXACTNESS (the stamped pair equals the
    resolved Subject — Reading A / a hardcoded operator / any non-None owner would otherwise pass) is
    the BEHAVIOURAL pin ``test_a_credentialed_send_stamps_exactly_the_subjects_pair`` (R1) in
    ``test_comms_send_scope_63b_ii_a.py`` — a classifier sees ROWS, not tokens (stated bound B3). So the
    STRONGEST structural leg the classifier CAN run is: ``owner_agent == sender`` — the message CREATE
    writes ``sender: RecordID(agent, sender.id)`` and a correct send stamps ``owner_agent`` to the
    SUBJECT's agent, which IS the sender; both are on the row, so this leg REJECTS a build that stamps
    ``owner_agent`` to ANY agent but the sender. Schema unchanged. A create with a NONE owner/scope
    (the HEAD, unstamped) → REJECTED. ``SELECT *`` omits a NONE column, so an absent key reads as None."""
    if not effect.schema_delta.is_empty or not effect.row_deltas:
        return False
    for delta in effect.row_deltas:
        after = delta.after or {}
        if delta.kind != "created":
            return False
        if after.get(_COL_OWNER_PRINCIPAL) is None or after.get(_COL_OWNER_AGENT) is None:
            return False
        if after.get(_COL_SCOPE) is None:
            return False
        # R8 — the owner agent the classifier CAN see IS the row's own sender (the ==subject exactness
        # is R1's behavioural pin; a classifier sees rows, not tokens). Rejects any-agent-but-the-sender.
        if after.get(_COL_OWNER_AGENT) != after.get(_COL_SENDER):
            return False
    return True


def _effect_send_to(effect: ObservedEffect) -> bool:
    """``send`` RELATEs delivery edges: EVERY delta is a CREATE of a ``to`` row (design §4.B — the
    created ``to`` rows point at the just-created message; the in==message exactness is behavioural).
    Schema unchanged. A drain/ack UPDATE smuggled under the send label → REJECTED (not a create)."""
    if not effect.schema_delta.is_empty or not effect.row_deltas:
        return False
    return all(delta.kind == "created" for delta in effect.row_deltas)


def _effect_drain_to(effect: ObservedEffect) -> bool:
    """``drain`` CAS-stamps ``seen_at`` on the recipient's edges (design §4.B / §1.4): EVERY delta is
    an UPDATE whose ONLY changed column is ``seen_at`` and whose ``before.seen_at`` was None (a first
    stamp, never a re-stamp). A build that also touched a governed column, or re-stamped an already-seen
    edge, REJECTED. Schema unchanged."""
    if not effect.schema_delta.is_empty or not effect.row_deltas:
        return False
    for delta in effect.row_deltas:
        before = delta.before or {}
        if delta.kind != "updated" or delta.changed_columns != frozenset({_COL_SEEN_AT}):
            return False
        if before.get(_COL_SEEN_AT) is not None:
            return False
    return True


def _effect_ack_to(effect: ObservedEffect) -> bool:
    """``ack`` CAS-stamps ``acked_at`` (+ optional ``ack_note``) on the recipient's edges (design §4.B
    / §1.4): EVERY delta is an UPDATE whose changed columns ⊆ {acked_at, ack_note} and whose
    ``before.acked_at`` was None (a first ack, never a re-ack). Schema unchanged."""
    if not effect.schema_delta.is_empty or not effect.row_deltas:
        return False
    for delta in effect.row_deltas:
        before = delta.before or {}
        if delta.kind != "updated" or not (delta.changed_columns <= _ACK_COLUMNS):
            return False
        if not delta.changed_columns or before.get(_COL_ACKED_AT) is not None:
            return False
    return True


def _effect_migrate_message(effect: ObservedEffect) -> bool:
    """The ``_migrate_message_owner`` backfill (design §4.C): EVERY changed row is an UPDATE of a
    previously-UNOWNED/NONE-scope legacy message whose changed columns are EXACTLY
    {owner_agent, owner_principal, scope} — a golden edited to seize an already-owned message reds here
    (before.owner_* / before.scope was set). Schema unchanged. Robust to the exact statement shape."""
    if not effect.schema_delta.is_empty or not effect.row_deltas:
        return False
    expected = frozenset({_COL_OWNER_AGENT, _COL_OWNER_PRINCIPAL, _COL_SCOPE})
    for delta in effect.row_deltas:
        before = delta.before or {}
        if delta.kind != "updated" or delta.changed_columns != expected:
            return False
        if any(before.get(col) is not None for col in expected):
            return False
    return True


# The PROVISIONAL golden the builder must match (FLAG F-MIGRATE-GOLDEN). Function-local in
# ``_migrate_message_owner`` (§1.9 item 1 — never a module constant, which L1 orphans to <module>).
_MIGRATE_MESSAGE_GOLDEN = (
    f"UPDATE {_MESSAGE_TABLE} SET owner_agent = sender, owner_principal = sender.owner_principal, "
    f"scope = $scope WHERE owner_principal IS NONE"
)


# =========================================================================== #
# THE MESSAGE / TO ALLOWLISTS (design §1.4/§1.5 — the DATA seam ii-a owns). ii-b widens the drain/ack
# effect predicates behaviourally if needed; the L1 site coverage lives HERE so deny-by-default holds
# the moment §4.F makes message/to governed populations.
# =========================================================================== #

_SEND_MESSAGE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_MESSAGES_PY, "_send_fragment", "CREATE"),
    justification=(
        "send CREATEs the governed message node (design §4.A). The owner pair is the resolved Subject "
        "(R1's separate pin test_a_credentialed_send_stamps_exactly_the_subjects_pair; owner_agent IS "
        "the sender, R8), the scope is the session keep resolved via governed.resolve_write_scope."
    ),
    pin="test_a_labelled_send_message_create_classifies",
    frames=("send",),
    effect=_effect_send_message,
)
_MIGRATE_MESSAGE_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_PRINCIPALS_PY, "_migrate_message_owner", "UPDATE"),
    justification=(
        "the message-owner backfill (design §4.C / §1.4 statement-scoped exempt). Admin-CLI-only, NOT "
        "member-reachable → attributes via governed_exempt('migrate-governed', statement=…); touches "
        "ONLY unmigrated NONE-owner legacy messages; idempotent; R4 driver-routed."
    ),
    pin="test_the_migrate_message_site_is_registered_and_derived",
    frames=("_migrate_message_owner",),
    exempt_name="migrate-governed",
    statement=_MIGRATE_MESSAGE_GOLDEN,
    effect=_effect_migrate_message,
)
MESSAGE_TREE_ALLOWLIST: tuple[TreeWriteAllowlistEntry, ...] = (
    _SEND_MESSAGE_ENTRY,
    _MIGRATE_MESSAGE_ENTRY,
)

_SEND_TO_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_MESSAGES_PY, "_send_fragment", "RELATE"),
    justification="send RELATEs the delivery edges (design §4.B) — one CREATE per recipient edge.",
    pin="test_a_labelled_send_to_create_classifies",
    frames=("send",),
    effect=_effect_send_to,
)
_DRAIN_TO_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_MESSAGES_PY, "drain", "UPDATE"),
    justification=(
        "drain CAS-stamps seen_at on the recipient's own edges (design §4.B). ii-b drives the LIVE "
        "classification; ii-a registers the SITE + the §1.4 effect predicate so deny-by-default holds."
    ),
    pin="test_the_drain_effect_predicate_discriminates",
    frames=("drain",),
    effect=_effect_drain_to,
)
_ACK_TO_ENTRY = TreeWriteAllowlistEntry(
    site=TreeMutationSite(_MESSAGES_PY, "ack", "UPDATE"),
    justification=(
        "ack CAS-stamps acked_at/ack_note on the recipient's own edges (design §4.B). ii-b drives the "
        "LIVE classification; ii-a registers the SITE + the §1.4 effect predicate (deny-by-default)."
    ),
    pin="test_the_ack_effect_predicate_discriminates",
    frames=("ack",),
    effect=_effect_ack_to,
)
TO_TREE_ALLOWLIST: tuple[TreeWriteAllowlistEntry, ...] = (
    _SEND_TO_ENTRY,
    _DRAIN_TO_ENTRY,
    _ACK_TO_ENTRY,
)


# =========================================================================== #
# §1.5c-iii — THE POPULATION SET GROWS to {memory, message, to} (a CHECKED VARIABLE, an OUTPUT).
# =========================================================================== #


class TestTheGovernedPopulationSetGrows:
    """§4.F / §1.5c-iii — once ``_message_statements`` calls ``_governed_field_specs`` (the §4.F
    wiring), ``governed_populations()`` DERIVES {memory, message, to} (``to`` joins because its IN
    endpoint ``message`` is now governed). 63c-i-a r2: W1-1 grows it to {agent, briefed, memory,
    message, to} — the exact pin below is the ONE home of the known set."""

    def test_message_and_to_join_the_derived_population_set(self) -> None:
        """⚠ RED at HEAD — ``message`` and ``to`` are in the DERIVED population set once §4.F wires the
        governed emitter into ``_message_statements``. At HEAD ``_message_statements`` does not call
        ``_governed_field_specs`` → populations == {memory} → both assertions red (the §4.F wiring is
        the gate; the relation-endpoint derivation adds ``to`` for free)."""
        populations = governed_populations()
        assert _MESSAGE_TABLE in populations, (
            f"message is not a derived governed population — §4.F has not wired _governed_field_specs "
            f"into _message_statements. populations={sorted(populations)}"
        )
        assert _TO_RELATION in populations, (
            f"the `to` relation is not a derived governed population — its IN endpoint `message` is not "
            f"governed yet (§1.5c-iii relation-endpoint derivation). populations={sorted(populations)}"
        )

    def test_the_derived_population_set_grows_to_memory_message_to(self) -> None:
        """⚠ THE ONE known-set EXACT pin (deny-by-default over the SET: a SURPRISE population reds).

        63c-i-a r2 (amendment-2 A1 / §D item 3 / adversary MP-3 + MP-10) — the known set is now
        EXACTLY {agent, briefed, memory, message, to}. Its growth story, dated:
        * ii-a (§4.F): {memory} → {memory, message, to} (``to`` joins via its governed IN ``message``).
        * i-a (W1-1, ruling §2.1): ``_agent_statements`` calls ``_governed_field_specs`` → ``agent``
          joins; ``briefed`` (IN = ``agent``) JOINS BY DERIVATION — once the r2 resolver reads the
          ``from lorerunes import AGENT_TABLE as AGENT_TABLE`` re-export (the r1 resolver could not,
          which is why the adversary measured ``{agent, memory, message, to}`` on a correct build).
          ``briefed``'s F5 case (seeders, write verbs, labels, evidence) is OWED BY 63c-ii, beside its
          only writers (``brief_ack``'s RELATE and register's auto-ack RELATE, ruling §3.5) — exactly
          as ``to``'s landed with drain/ack. This docstring IS the adjudication point.
        * ``member_of(PRINCIPAL_TABLE, keep)`` stays OUT: neither endpoint is governed.
        The i-a file's duplicate exact pin was DELETED (DUAL comment there) — ONE home for the known
        set, so the next wave's edit cannot reach one copy and not the other. RED before the i-a
        build (the derivation yields {memory, message, to}). The test NAME keeps its ii-a spelling so
        existing citations resolve."""
        populations = governed_populations()
        known_set = frozenset(
            {
                surreal_schema.AGENT_TABLE,
                surreal_schema.BRIEFED_RELATION,
                _MESSAGE_TABLE,
                _TO_RELATION,
                "memory",
            }
        )
        assert populations == known_set, (
            f"the derived governed-population set is {sorted(populations)}, not the adjudicated known "
            f"set {{agent, briefed, memory, message, to}} — either the i-a W1-1 wiring is unbuilt "
            f"(agent/briefed absent), the resolver cannot read a re-exported endpoint (briefed absent "
            f"beside agent — amendment-2 A1), OR a SURPRISE population appeared (a new governed table "
            f"needs an F5 case and an adjudication line in this docstring; §1.5c-iii)"
        )

    def test_the_population_set_is_an_OUTPUT_not_a_hand_list(self) -> None:
        """CONTROL (design §1.9 item 2 mutation proof) — ``governed_populations`` is a real derivation:
        a SYNTHETIC ``surreal_schema`` source whose ``_message_statements`` calls ``_governed_field_specs``
        GROWS the output to include message + to; one WITHOUT it does not. GREEN at HEAD (the derivation
        mechanism is built); it REDDENS a build that hardcodes ``frozenset({'memory'})`` (which passes the
        value pins above on the real schema but cannot grow on a synthetic input)."""
        without = (
            "MESSAGE_TABLE = 'message'\nTO_RELATION = 'to'\nAGENT_TABLE = 'agent'\n"
            "def _governed_field_specs():\n    return ()\n"
            "def _memory_statements():\n    _governed_field_specs()\n    return []\n"
            "def _message_statements():\n    return []\n"
            "def _define_relation_table(name, in_t, out_t, enforced=True):\n    return ''\n"
        )
        with_message = without.replace(
            "def _message_statements():\n    return []\n",
            "def _message_statements():\n    _governed_field_specs()\n"
            "    _define_relation_table(TO_RELATION, MESSAGE_TABLE, AGENT_TABLE)\n    return []\n",
        )
        assert _MESSAGE_TABLE not in governed_populations(without), (
            "a synthetic schema whose _message_statements does NOT call _governed_field_specs must NOT "
            "yield message — the derivation is not keyed on the emitter caller (§1.9 item 2)"
        )
        grown = governed_populations(with_message)
        assert _MESSAGE_TABLE in grown and _TO_RELATION in grown, (
            f"a synthetic _message_statements that calls _governed_field_specs (+ a to relation over it) "
            f"must GROW the output to include message + to — the reach is not a checked variable "
            f"(a hardcoded frozenset would fail this). got {sorted(grown)}"
        )


# =========================================================================== #
# DENY-BY-DEFAULT — every DERIVED message/to L1 site ∈ its allowlist; the migrate-message site is a
# builder deliverable (RED-until-built coupling, the i-b _REPLAY_CLOSE_ENTRY precedent).
# =========================================================================== #


class TestEveryDerivedSiteIsAllowlisted:
    """§10.9-A L1 deny-by-default — a DERIVED raw mutation site with no allowlist entry is a RED. ii-a
    covers every ``message``/``to`` write site the tree derives (send/migrate for message; send/drain/
    ack for to)."""

    def test_every_derived_message_site_is_in_the_message_allowlist(self) -> None:
        """Deny-by-default over ``message`` sites. GREEN control at HEAD for the send site (derived +
        covered); the migrate site is not derived until piece-2's builder adds ``_migrate_message_owner``
        (checked by its own RED pin below). A SURPRISE message write site (unclassified) reds here."""
        derived = governed_table_raw_mutation_sites_in_tree(
            _MESSAGE_TABLE, table_const_hint="MESSAGE_TABLE"
        )
        allowlisted = {entry.site for entry in MESSAGE_TREE_ALLOWLIST if entry.l1_site}
        ghosts = derived - allowlisted
        assert not ghosts, (
            f"derived message write sites with NO allowlist entry (deny-by-default RED): {sorted(ghosts)}"
        )

    def test_every_derived_to_site_is_in_the_to_allowlist(self) -> None:
        """Deny-by-default over ``to`` sites. GREEN at HEAD (send RELATE + drain UPDATE + ack UPDATE are
        all derived AND registered). A SURPRISE ``to`` write (a new drain/rewire path) reds here — the
        instrument that makes ``to``'s write surface a checked variable the moment it is governed."""
        derived = governed_table_raw_mutation_sites_in_tree(_TO_RELATION, table_const_hint="TO_RELATION")
        allowlisted = {entry.site for entry in TO_TREE_ALLOWLIST if entry.l1_site}
        ghosts = derived - allowlisted
        assert not ghosts, (
            f"derived `to` write sites with NO allowlist entry (deny-by-default RED): {sorted(ghosts)}"
        )

    def test_the_send_sites_are_derived_and_covered(self) -> None:
        """CONTROL — the send message CREATE and the send ``to`` RELATE are BOTH derived at HEAD (the
        raw literals exist in ``_send_fragment``) and covered by the send entries. Anchors the
        deny-by-default pins so 'no ghosts' is not vacuously true over an empty derived set."""
        message_sites = governed_table_raw_mutation_sites_in_tree(
            _MESSAGE_TABLE, table_const_hint="MESSAGE_TABLE"
        )
        to_sites = governed_table_raw_mutation_sites_in_tree(_TO_RELATION, table_const_hint="TO_RELATION")
        assert _SEND_MESSAGE_ENTRY.site in message_sites, (
            f"the send message-CREATE site is not derived — _send_fragment's literal changed. "
            f"derived={sorted(message_sites)}"
        )
        assert _SEND_TO_ENTRY.site in to_sites, (
            f"the send to-RELATE site is not derived. derived={sorted(to_sites)}"
        )

    def test_the_migrate_message_site_is_registered_and_derived(self) -> None:
        """⚠ RED at HEAD (the coupling to piece 2 — the i-b ``_REPLAY_CLOSE_ENTRY`` precedent).
        ``_MIGRATE_MESSAGE_ENTRY`` is registered (this file's DATA — green), and its site MUST be
        L1-derived from ``principals.py`` (RED at HEAD: ``_migrate_message_owner`` is a piece-2 builder
        deliverable, so the derivation does not yet yield it → GREEN once the builder adds the message
        backfill UPDATE literal)."""
        assert _MIGRATE_MESSAGE_ENTRY in MESSAGE_TREE_ALLOWLIST, "the migrate-message entry is unregistered"
        derived = governed_table_raw_mutation_sites_in_tree(
            _MESSAGE_TABLE, table_const_hint="MESSAGE_TABLE"
        )
        assert _MIGRATE_MESSAGE_ENTRY.site in derived, (
            "the _migrate_message_owner UPDATE literal is NOT L1-derived — the piece-2 builder has not "
            f"added the message-owner backfill to principals.py yet (design §4.C). derived message "
            f"sites: {sorted(s for s in derived if s.function == '_migrate_message_owner')}"
        )


# =========================================================================== #
# EFFECT-PREDICATE DISCRIMINATION (unit, GREEN DATA validation) — fixtures-must-discriminate: each
# predicate ACCEPTS its correct shape and REJECTS the wrong build it exists to catch.
# =========================================================================== #


def _created(row_id: str, **cols: Any) -> RowDelta:
    return RowDelta(id=row_id, kind="created", changed_columns=frozenset(cols), before=None, after=cols)


def _updated(row_id: str, changed: set[str], before: dict[str, Any], after: dict[str, Any]) -> RowDelta:
    return RowDelta(id=row_id, kind="updated", changed_columns=frozenset(changed), before=before, after=after)


def _effect(*deltas: RowDelta) -> ObservedEffect:
    return ObservedEffect(row_deltas=tuple(deltas), schema_delta=_empty_schema())


class TestTheEffectPredicatesDiscriminate:
    """Each predicate is interrogated with 'what WRONG build still passes this?' (CLAUDE.md
    FIXTURES-MUST-DISCRIMINATE). GREEN — they validate the DATA the classifier applies."""

    def test_send_message_accepts_a_stamped_create_and_rejects_an_unstamped_one(self) -> None:
        stamped = _created(
            "m1", owner_principal="principal:a", owner_agent="agent:x", scope="keep:k", sender="agent:x"
        )
        assert _effect_send_message(_effect(stamped)), "a fully-stamped message create must classify"
        unstamped = _created("m2", owner_agent="agent:x", scope="keep:k", sender="agent:x")
        assert not _effect_send_message(_effect(unstamped)), (
            "a message create with a NONE owner_principal (the HEAD/unstamped shape) must be REJECTED"
        )
        no_scope = _created("m3", owner_principal="principal:a", owner_agent="agent:x", sender="agent:x")
        assert not _effect_send_message(_effect(no_scope)), (
            "a message create with NONE scope must be REJECTED"
        )
        # R8 — the owner agent must BE the sender; a create stamping owner_agent to a DIFFERENT agent
        # than the sender is REJECTED (the ==subject exactness is R1's
        # test_a_credentialed_send_stamps_exactly_the_subjects_pair in test_comms_send_scope_63b_ii_a.py).
        wrong_owner = _created(
            "m4", owner_principal="principal:a", owner_agent="agent:other", scope="keep:k", sender="agent:x"
        )
        assert not _effect_send_message(_effect(wrong_owner)), (
            "a message create whose owner_agent is NOT the sender must be REJECTED (R8 — the owner "
            "agent IS the sender; a build stamping any agent but the sender reds here)"
        )

    def test_send_to_accepts_creates_and_rejects_an_update(self) -> None:
        assert _effect_send_to(_effect(_created("e1"), _created("e2"))), (
            "send's to-edge creates must classify"
        )
        an_update = _updated("e3", {"seen_at"}, {"seen_at": None}, {"seen_at": "t"})
        assert not _effect_send_to(_effect(an_update)), (
            "a drain/ack UPDATE smuggled under the send label must be REJECTED (send only CREATEs edges)"
        )

    def test_drain_accepts_a_first_seen_stamp_and_rejects_a_seizure_or_restamp(self) -> None:
        first = _updated("e1", {"seen_at"}, {"seen_at": None}, {"seen_at": "t"})
        assert _effect_drain_to(_effect(first)), "a first seen_at stamp must classify"
        seizure = _updated(
            "e2", {"seen_at", "scope"}, {"seen_at": None, "scope": "k"}, {"seen_at": "t", "scope": "z"}
        )
        assert not _effect_drain_to(_effect(seizure)), (
            "a drain that also touched a governed column must be REJECTED"
        )
        restamp = _updated("e3", {"seen_at"}, {"seen_at": "old"}, {"seen_at": "t"})
        assert not _effect_drain_to(_effect(restamp)), (
            "a re-stamp of an already-seen edge must be REJECTED"
        )

    def test_ack_accepts_a_first_ack_and_rejects_a_reack_or_foreign_column(self) -> None:
        first = _updated(
            "e1", {"acked_at", "ack_note"}, {"acked_at": None}, {"acked_at": "t", "ack_note": "n"}
        )
        assert _effect_ack_to(_effect(first)), "a first ack (acked_at + ack_note) must classify"
        reack = _updated("e2", {"acked_at"}, {"acked_at": "old"}, {"acked_at": "t"})
        assert not _effect_ack_to(_effect(reack)), "a re-ack of an already-acked edge must be REJECTED"
        foreign = _updated(
            "e3", {"acked_at", "seen_at"}, {"acked_at": None}, {"acked_at": "t", "seen_at": "t"}
        )
        assert not _effect_ack_to(_effect(foreign)), (
            "an ack that also touched seen_at must be REJECTED"
        )

    def test_migrate_message_accepts_a_legacy_backfill_and_rejects_a_seizure(self) -> None:
        legacy = _updated(
            "m1", {"owner_agent", "owner_principal", "scope"},
            {"owner_agent": None, "owner_principal": None, "scope": None},
            {"owner_agent": "agent:x", "owner_principal": "principal:a", "scope": "keep:proj"},
        )
        assert _effect_migrate_message(_effect(legacy)), "a legacy NONE→stamped backfill must classify"
        seizure = _updated(
            "m2", {"owner_agent", "owner_principal", "scope"},
            {"owner_agent": "agent:owned", "owner_principal": "principal:owned", "scope": "keep:owned"},
            {"owner_agent": "agent:x", "owner_principal": "principal:a", "scope": "keep:seized"},
        )
        assert not _effect_migrate_message(_effect(seizure)), (
            "a migrate that re-stamped an ALREADY-OWNED message (before.owner set) must be REJECTED — a "
            "golden edited to seize owned rows reds here (§4.C / §1.4 leg 3)"
        )


# =========================================================================== #
# CLASSIFIER — deny-by-default over the new shapes (unit, GREEN): an unlabelled write is UNCLASSIFIED;
# a labelled-clean write classifies; a labelled write whose effect FAILS its predicate does NOT (the
# label leg RUNS the predicate — §1.4).
# =========================================================================== #


class TestClassificationOfMessageWrites:
    """§1.2/§1.4 over the message/to shapes — the F5 root property (an unattributed governed write is
    denied; a label does not launder an off-predicate effect) holds for send/drain/ack."""

    def test_an_unlabelled_message_create_is_unclassified(self) -> None:
        stamped = _created(
            "m1", owner_principal="principal:a", owner_agent="agent:x", scope="keep:k", sender="agent:x"
        )
        write = ObservedWrite(label=None, effect=_effect(stamped))
        assert not classify_tree_observed_write(write, MESSAGE_TREE_ALLOWLIST), (
            "an UNLABELLED message create classified — deny-by-default is not firing (§1.2)"
        )

    def test_a_labelled_send_message_create_classifies(self) -> None:
        stamped = _created(
            "m1", owner_principal="principal:a", owner_agent="agent:x", scope="keep:k", sender="agent:x"
        )
        write = ObservedWrite(label="send", effect=_effect(stamped))
        assert classify_tree_observed_write(write, MESSAGE_TREE_ALLOWLIST), (
            "a clean stamped send message create under the `send` label did NOT classify (§4.A)"
        )

    def test_a_labelled_send_with_an_unstamped_effect_is_unclassified(self) -> None:
        """The label leg RUNS the effect predicate (§1.4): a `send`-labelled message create with a NONE
        owner (the HEAD shape) does NOT classify — the label does not launder an unstamped write."""
        unstamped = _created("m1", owner_agent="agent:x", scope="keep:k", sender="agent:x")
        write = ObservedWrite(label="send", effect=_effect(unstamped))
        assert not classify_tree_observed_write(write, MESSAGE_TREE_ALLOWLIST), (
            "a `send`-labelled but UNSTAMPED message create classified — the label leg does not run the "
            "effect predicate (§1.4 / MISSING PIN #1 re-widened)"
        )

    def test_a_labelled_send_to_create_classifies(self) -> None:
        write = ObservedWrite(label="send", effect=_effect(_created("e1"), _created("e2")))
        assert classify_tree_observed_write(write, TO_TREE_ALLOWLIST), (
            "a clean send to-edge create under the `send` label did NOT classify (§4.B)"
        )

    def test_the_drain_effect_predicate_discriminates(self) -> None:
        """A `drain`-labelled first-seen stamp classifies; a seizure under the same label does not."""
        first = _updated("e1", {"seen_at"}, {"seen_at": None}, {"seen_at": "t"})
        assert classify_tree_observed_write(
            ObservedWrite(label="drain", effect=_effect(first)), TO_TREE_ALLOWLIST
        )
        seizure = _updated(
            "e2", {"seen_at", "owner_principal"}, {"seen_at": None}, {"seen_at": "t", "owner_principal": "p"}
        )
        assert not classify_tree_observed_write(
            ObservedWrite(label="drain", effect=_effect(seizure)), TO_TREE_ALLOWLIST
        ), "a `drain`-labelled seizure classified — the label laundered an off-predicate effect (§1.4)"

    def test_the_ack_effect_predicate_discriminates(self) -> None:
        first = _updated("e1", {"acked_at"}, {"acked_at": None}, {"acked_at": "t"})
        assert classify_tree_observed_write(
            ObservedWrite(label="ack", effect=_effect(first)), TO_TREE_ALLOWLIST
        )
        reack = _updated("e2", {"acked_at"}, {"acked_at": "old"}, {"acked_at": "t"})
        assert not classify_tree_observed_write(
            ObservedWrite(label="ack", effect=_effect(reack)), TO_TREE_ALLOWLIST
        ), "an `ack`-labelled re-ack classified — the label laundered an off-predicate effect (§1.4)"


# =========================================================================== #
# LIVE — the SEND classification GREEN (design §5 ii-a: "F5 registries GREEN for send"). Drive a REAL
# send through the server and observe the message CREATE. RED at HEAD (send is unlabelled + unstamped →
# observed but UNCLASSIFIED). GREEN on the build (labelled `send` + stamped → classified).
# =========================================================================== #

@pytest_asyncio.fixture()
async def cred(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AsyncIterator[dict[str, Any]]:
    """A REAL CREDENTIALED AppContext — a CALLER of the shared ``credentialed_app_context`` (§11.3
    F-DUP: the private per-file credentialed harness CONVERGED onto the ONE lifted home) + ONE ``alice``
    member principal. The credentialed harness the LIVE send classification drives, so a CORRECT build's
    send RESOLVES its subject (rather than DENYING a tokenless call) and writes a properly-owned message
    row the F5 observer captures + classifies. Reaped by the shared home (NEVER :18500). SHARING is
    provable BY MUTATION (§11.3): change the shared harness's token shape and this file's credentialed
    identity flips with it — the F-DUP mutation pin."""
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=8
    ) as world:
        yield {
            "ctx": world["ctx"],
            "holder": world["holder"],
            "alice_email": world["emails"]["alice"],
            "alice_pid": world["pids"]["alice"],
        }


class TestTheLiveSendClassifiesUnderF5:
    """design §5 ii-a — a REAL CREDENTIALED send's governed message write is OBSERVED and CLASSIFIED
    under ``MESSAGE_TREE_ALLOWLIST``. RED at HEAD: send accepts no ``capability=`` (the §4.D seam is
    unbuilt), and even were it accepted it sets no ``write_guard('send')`` label and stamps no
    owner/scope → the observed message create is label=None + unstamped → UNCLASSIFIED. Driven
    CREDENTIALED (reviser): a tokenless send on a CORRECT build DENIES (no message row → the anti-vacuity
    would spuriously fail), so the harness presents a real token + capability and the send classifies
    for the RIGHT reason — a properly-owned, `send`-labelled row whose owner_agent IS the sender (R8)."""

    async def test_a_real_send_message_write_is_observed_and_classifies(
        self, cred: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD — drive a CREDENTIALED ``comms(action='send', capability=…)`` under the F5
        observer on ``message``; the observed message CREATE must CLASSIFY (label `send`; the effect
        predicate holds — non-NONE owner pair + scope + owner_agent==sender, R8). At HEAD ``comms`` does
        not accept ``capability=`` (§4.D unbuilt) → a legible ``pytest.fail`` RED; on a partial build
        the create is label=None/unstamped → unclassified → reds. ANTI-VACUITY: the send genuinely
        created a governed message row (the observed set is non-empty)."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["alice_email"]
        # A CREDENTIALED sender owned by alice (its capability minted off the registry) + a recipient.
        sender_cap, _sender_agent = await register_owned(
            ctx, "sender_x", owner_principal_id=cred["alice_pid"], session="s1"
        )
        await ctx.comms(action="register", agent="recip_x", session="s1", role="builder")
        with observe_governed_table_writes(_MESSAGE_TABLE) as observed:
            try:
                await ctx.comms(
                    action="send", agent="sender_x", session="s1", to=["recip_x"],
                    body="a governed send", grade="signal", capability=sender_cap,
                )
            except TypeError as error:  # HEAD: `comms` has no `capability=` param (§4.D seam unbuilt)
                pytest.fail(
                    f"AppContext.comms does not accept capability= — the §4.D seam is unbuilt, so a "
                    f"credentialed send cannot even be issued (RED-at-HEAD for the right reason): {error}"
                )
        creates = [
            w for w in observed
            if w.effect is not None and any(d.kind == "created" for d in w.effect.row_deltas)
        ]
        assert creates, (
            "the credentialed send created NO observed message row — the F5 observer saw nothing "
            "(anti-vacuity). On a correct build a credentialed send WRITES a governed message row"
        )
        unclassified = [w for w in creates if not classify_tree_observed_write(w, MESSAGE_TREE_ALLOWLIST)]
        assert not unclassified, (
            "the live send's message CREATE did NOT classify under MESSAGE_TREE_ALLOWLIST — send is "
            "unlabelled (no write_guard('send')) and/or unstamped (NONE owner/scope, or owner_agent ≠ "
            "sender), so the governed write is unattributed (design §4.A / §5 ii-a; R8). labels="
            f"{[w.label for w in creates]}"
        )
