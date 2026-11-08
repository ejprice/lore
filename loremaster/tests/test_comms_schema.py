"""Contract tests for the PKT-28 C1 seam S1 schema slice — ``agent`` / ``brief`` /
``briefed`` — against the REAL SurrealDB server (spike-surreal, ``:18000``).

Scope (deliberately narrow — this is S1 of C1, the schema slice ONLY): the two
pure DDL generators ``generate_agent_ddl()`` / ``generate_brief_ddl()`` in
``loremaster.store.surreal_schema`` and their live behaviour once applied.
NOT in scope: the ``AgentRegistry``/``BriefLedger`` ledger classes
(``loremaster/loremaster/agents.py`` / ``briefs.py`` — a separate seam, S2),
the ``lore_comms`` dispatch tool, rendering, or ``CommsConfig`` — none of those
production modules exist yet and none is touched or stubbed here.

Binding spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` §0 (Identity &
schema slices) — the design-consultant doc is FINAL and authoritative; where it
disagrees with the garden plan's letter or the scout's seam map, the spec wins
(its own words: "Contract-writers turn THIS document into tests verbatim").
House pattern cloned throughout: ``_TASK_FIELD_SPECS`` -> ``generate_task_ddl``
(``surreal_schema.py:276,966``), the ``_define_relation_table`` edge idiom
(``surreal_schema.py:454``, used by ``refers``/``answers_to``), and this
project's OWN sibling contract file ``test_surreal_schema.py`` (offline
DDL-string pins + live behavioural pins against the real engine, both classes
of assertion, mirrored here).

Two build-time probes this spec calls for (§0, §BUILD-TIME PROBES) were run
LIVE against spike-surreal 3.1.5 this session (throwaway scripts, not
committed) before authoring the assertions below — both are load-bearing for
what this file pins as fact rather than assumption:

* **Charset ASSERT spelling.** ``ASSERT string::matches($value, '<pattern>')``
  IS accepted and enforces correctly on 3.1.5: a 65-char value is rejected, a
  64-char value accepted (the ``{0,63}`` boundary after the mandatory first
  char), a leading ``-``/``_`` rejected, an embedded newline/colon/quote/
  backslash rejected, an uppercase char rejected. The OPERATOR form
  (``$value =~ /pattern/``) is REJECTED by the 3.1.5 parser ("Unexpected token
  `~`, expected an expression") — the function form is the ONLY working
  spelling and is what every ASSERT below pins.
* **``option<object> FLEXIBLE`` spelling.** ``TYPE option<object> FLEXIBLE``
  (FLEXIBLE trailing, OUTSIDE the angle brackets) is accepted and round-trips a
  nested object / ``NONE`` cleanly. ``TYPE option<object FLEXIBLE>`` (FLEXIBLE
  INSIDE the brackets) is a parse error ("Unexpected token `FLEXIBLE` expected
  delimiter `>`"). Only the trailing form is used below.
* A THIRD shape was smoke-tested (not a spec-named probe, but load-bearing for
  how the live tests below are written): ``RELATE type::record(table, $id)->
  edge->type::record(table, $id) SET ...`` is a PARSE ERROR on 3.1.5
  (``type::record()`` cannot sit directly in a RELATE endpoint position — a
  different failure from the two probes above, not resolved by the CONTENT/SET
  form change described in the seam map). The working shape (cloned from
  ``graph_surreal.py``'s ``_edge_statement``/``_node_statements``, which
  already do exactly this) is ``RELATE $from->edge->$to SET ...`` with ``$from``
  /``$to`` bound as SDK ``RecordID`` objects, never a ``type::record()`` call at
  the RELATE position. Every ``briefed`` live test below uses this shape.

Expected until C1-S1 lands: collection ERROR in THIS FILE —
``ImportError: cannot import name 'generate_agent_ddl' from
'loremaster.store.surreal_schema'`` (the symbols do not exist yet).

The UNIQUE(in, out)-on-a-RELATION-edge mechanism itself (cascade-delete-then-
re-RELATE safety, SurrealDB bug #7061) was independently probed and verified
SAFE on this same 3.1.5 floor in a PRIOR session — see
``docs/reference/surrealdb-31-capabilities.md`` §4 (UNIQUE-on-relation is legal
and the #7061 cascade hazard is settled ABSENT, with the probe transcript).
This file's own
``TestBriefedUniqueInOutIndex`` re-proves the UNIQUE rejection itself (a
plain, cheap, in-suite assertion) but does not re-run that cascade probe —
out of S1's scope per the design doc (§BUILD-TIME PROBES: "the full cascade
probe stays C2's").
"""

from __future__ import annotations

import ast
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, get_args

import pytest
import pytest_asyncio
from _governed_contract import (
    build_principal_and_keep_stores,
    derive_member_source_roots,
    frozen_asserted_message_ddl,
    frozen_asserted_to_ack_note_ddl,
    governed_table_raw_mutation_sites,
    member,
    seed_message_legacy,
    session_keep_id_for,
    unbounded_to_ack_note_ddl,
)
from _surreal_harness import (
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.agents import AGENT_STATUSES, AgentRegistry, AgentStatus
from loremaster.messages import MessageLedger
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    ANSWERS_TO_RELATION,
    BRIEF_COUNTER_TABLE,
    BRIEF_TABLE,
    BRIEFED_RELATION,
    CODE_NODE_TABLE,
    NAME_TABLE,
    REFERS_RELATION,
    generate_agent_ddl,
    generate_brief_ddl,
    generate_graph_ddl,
)
from render_injection_scaffold import _INJECTION_THREAT_CHARS, _ROW_FORGE_PAYLOAD
from sdk3_shape_fakes import bare_record_key, digit_led_record_key, same_record
from surrealdb import RecordID

# --------------------------------------------------------------------------- #
# LAZY access to packet 03's schema additions.
#
# ⚠ CALL-TIME IMPORTS ON PURPOSE. ``_schema().MESSAGE_TABLE`` / ``_schema().TO_RELATION`` /
# ``_schema().MESSAGE_SEQUENCE_NAME`` / ``generate_message_ddl`` do not exist until packet
# 03 lands. A module-level import of them makes this file UNCOLLECTABLE at clean
# HEAD — deleting its ~180 PRE-EXISTING pins from the run — rather than RED.
# Those are different states, and the uncollectable one is the dangerous one
# (see the same note in test_message_ledger.py; finding #133).
# --------------------------------------------------------------------------- #


def _schema() -> Any:
    """``surreal_schema``'s packet-03 additions, read at CALL time."""
    import loremaster.store.surreal_schema

    return loremaster.store.surreal_schema


def generate_message_ddl() -> str:
    """The packet-03 DDL generator, resolved at CALL time (see above)."""
    return str(_schema().generate_message_ddl())


def _messages() -> Any:
    """``loremaster.messages`` (the ledger + its grade vocabulary), read at CALL
    time — the same lazy idiom as :func:`_schema`, so this file stays COLLECTABLE
    at a HEAD that has not yet shipped a symbol P-G2/P2-m reference (never a
    module-level import of a governance surface still under construction)."""
    import loremaster.messages

    return loremaster.messages

# --- local contract constants -------------------------------------------------
#
# Kept as LOCAL test constants, never imported from a not-yet-implemented
# production module — the SAME house idiom test_surreal_schema.py uses for
# ``COMMAND_STATUSES`` ("kept as LOCAL test constants ... since this IS the
# contract under test, not an existing convention to read"). The charset
# pattern mirrors design-doc §0 / §4's not-yet-built ``agents.py
# .AGENT_NAME_PATTERN``; the id formulas mirror §0's "pin this exactly" lines
# verbatim.

# The charset ASSERT pattern (design doc §0) — verified live, see module
# docstring. Both ``agent.name``/``agent.session`` and ``brief.name`` share it.
_IDENTIFIER_CHARSET_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"
_IDENTIFIER_CHARSET_ASSERT_TEXT = f"string::matches($value, '{_IDENTIFIER_CHARSET_PATTERN}')"

# The trim-non-empty ASSERT text (surreal_schema.py's ``_NON_EMPTY_STRING_ASSERT``
# constant, verbatim) — used by ``role``/``brief.body``/``brief.created_by``.
_NON_EMPTY_STRING_ASSERT_TEXT = "string::len(string::trim($value)) > 0"

_AGENT_STATUS_ACTIVE = "active"
_AGENT_STATUS_IDLE = "idle"
_AGENT_STATUS_INPUT_REQUIRED = "input_required"
_AGENT_STATUS_RETIRED = "retired"
_AGENT_STATUSES = (
    _AGENT_STATUS_ACTIVE,
    _AGENT_STATUS_IDLE,
    _AGENT_STATUS_INPUT_REQUIRED,
    _AGENT_STATUS_RETIRED,
)
# MUST NEVER be a legal stored value — derived at render time only (design doc
# §0/§3). A test below pins that storing it is rejected exactly like any other
# out-of-domain value.
_AGENT_STATUS_ORPHANED = "orphaned"

# The ``briefed.via`` vocabulary, kept as this file's OWN literals (never
# imported from production — an imported tuple would make every "the vocabulary
# is X" assertion track whatever production happens to say). v7 (finding #98)
# widened it to THREE: ``publish`` is the author's self-ack, written by
# ``BriefLedger.publish`` in the same transaction as the brief row.
_BRIEFED_VIA_REGISTER = "register"
_BRIEFED_VIA_EXPLICIT = "explicit"
_BRIEFED_VIA_PUBLISH = "publish"
_BRIEFED_VIA_VALUES = (_BRIEFED_VIA_REGISTER, _BRIEFED_VIA_EXPLICIT, _BRIEFED_VIA_PUBLISH)

# Realistic well-formed identifiers (positive control — an overly-strict ASSERT
# would silently pass every negative test below while rejecting real callers;
# mirrors ``test_command_accepts_each_valid_status``'s positive/negative pairing).
_VALID_IDENTIFIERS = ("fixer-b", "fixer_b2", "a", "wave7", "z" * 64)

# Hostile identifier shapes — the real injection classes the charset ASSERT is
# load-bearing against (design doc §0: derived ids get inlined as LITERALS into
# C3's LIVE WHERE clauses, so the store-level ASSERT is defense-in-depth for a
# guard the app layer is also expected to enforce). Live-verified against
# spike-surreal 3.1.5 (see module docstring) — every one of these IS rejected.
_HOSTILE_IDENTIFIERS = (
    "",  # empty
    " ",  # whitespace only
    "Fixer-B",  # uppercase
    "fixer b",  # embedded space
    "-fixer",  # leading hyphen
    "_fixer",  # leading underscore
    "fixer:b",  # colon
    "fixer'b",  # quote
    'fixer"b',  # double quote
    "fixer\\b",  # backslash
    "fixer\nb",  # embedded newline
    "fixer-b\n",  # TRAILING newline — finding #210's class: Python's ``$`` matches before a trailing
    # "\n", so a ``.match``-based decision accepts it (63c-i-a r2, amendment-2 A4 / adversary WB11). ONE
    # corpus: the register MOVE pins parametrise over THIS tuple (test_agent_registry.py), never a
    # narrower local copy.
    "z" * 65,  # one over the 64-char cap
    # r4a (amendment-8 KB-1): the DOTTED twin — a drift adversary-r2 N1c (at the home) and adversary-r4 G2
    # (a reworded private disjunct at the SKIP gate) BOTH built; every corpus-parametrised pin now carries
    # it. Appended LAST so every pre-existing index-derived param id (``hostile-NN-…``) is unchanged.
    "fixer.b",
)

#: r4a (amendment-9 MP-R4-3): the LEGAL side of the ONE corpus — the identity language's boundary points,
#: so a private NARROWING conjunct at any decision site (adversary-r4 G1: ``or len(attribution) > 32``)
#: dies on the witness that carries its axis. Parameter-value monoculture on the legal side is the same
#: defect as on the hostile side (two ≤7-char witnesses let G1 pass 2905/0), and it gets the same cure.
#: The cap itself (``"a" * 64``) is the witness that kills G1; ``_HOSTILE_IDENTIFIERS`` holds cap+1.
#: r4b (amendment-11 G3 — fixture growth): the TRAILING-separator axis (``"a-"``, ``"a_"`` — adversary-r4a
#: G3, a private ``or attribution.endswith(("-", "_"))`` at the SKIP gate, passed the full suite because
#: ``"a_b"``/``"a-b"`` put the separator in the MIDDLE) and the ALL-DIGIT axis (``"00"``). Appended LAST so
#: every pre-existing param id is unchanged.
#: r4b-fix (amendment 13 §G4 — the derive trigger FIRED on adversary-r4b G4, a SKIP gate narrowing on
#: DOUBLED separators ``--`` / ``__``): this tuple stays a HAND-LIST of NAMED boundary witnesses — read as
#: documentation, and as the cheap store legs of the accept-control (a store leg per generated example is the
#: wrong cost). It is NOT the ∀. The ∀ over the legal side is the GENERATED leg at the SKIP gate
#: (``test_agent_registry.py::TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::
#: test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language``): its witnesses
#: come from ``hypothesis.strategies.from_regex(lorerunes.AGENT_NAME_PATTERN, fullmatch=True)`` — the ONE
#: pattern object — so the generator's sample space is the language; ``target`` steers the sample up the
#: length axis; the other axes are covered probabilistically at 200 examples.
#: r4b-fix2 (amendment 16 G5 — ERRATUM, DUAL: *"every axis … is in its sample space by construction"* is
#: DELETED; space ≠ sample — 200 derandomized draws maxed at 27 characters and never reached the cap, so a
#: SKIP gate narrowing on 28–63-char names survived the full suite, adversary-r4b-fix G5). A pin certifies
#: only what it DID draw; the ``"a" * 64`` cap witness below stays the deterministic control.
_LEGAL_IDENTIFIER_WITNESSES = (
    "a",  # length 1 (the floor)
    "0z",  # digit-leading
    "a_b",  # underscore
    "a-b",  # hyphen
    "a" * 64,  # AT the 64-char cap (the ceiling — G1's axis)
    "a-",  # TRAILING hyphen (r4b, amendment-11 G3)
    "a_",  # TRAILING underscore (r4b, amendment-11 G3)
    "00",  # ALL-DIGIT (r4b, amendment-11 G3)
)


def _agent_record_id(session: str, name: str) -> str:
    """The deterministic ``agent`` record-id component (design doc §0, pinned
    verbatim): ``uuid.uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}").hex``.

    Computed here as an independent ORACLE (never imported from ``agents.py``,
    which does not exist yet) — the SAME pattern ``test_records.py``/
    ``test_memory_backend.py`` use to pin a uuid5 formula without importing the
    production mint.
    """
    return uuid.uuid5(uuid.NAMESPACE_URL, f"lore://agent/{session}/{name}").hex


def _brief_record_id(name: str, version: int) -> str:
    """The deterministic ``brief`` record-id component (design doc §0, pinned
    verbatim): ``uuid.uuid5(NAMESPACE_URL, f"lore://brief/{name}/{version}").hex``.
    """
    return uuid.uuid5(uuid.NAMESPACE_URL, f"lore://brief/{name}/{version}").hex


# --- DDL-string inspection helpers (local copies — test_surreal_schema.py's
# own docstring shows these as file-local pure helpers; no cross-file import
# precedent exists in this suite) ---------------------------------------------


# Field declarations are matched KEYWORD-AGNOSTICALLY: the field name is simply the
# last token before ``ON``. A closed alternation over today's two guard keywords
# (``IF NOT EXISTS`` / ``OVERWRITE``) would go blind again the next time the guard
# changes — which is exactly how ``test_in_and_out_are_never_hand_declared`` below
# rotted into a vacuous pass (finding #107).
_DEFINE_FIELD_RE = re.compile(r"^DEFINE FIELD\b.*?(?P<field>\S+)\s+ON\s+(?P<table>\S+)\b")


def _statements(ddl: str) -> list[str]:
    """The generated DDL split into individual, stripped statements."""
    return [statement.strip() for statement in ddl.split(";\n") if statement.strip()]


def _declared_fields(ddl: str, table: str) -> set[str]:
    """Every field name HAND-DECLARED on ``table`` by a ``DEFINE FIELD`` statement.

    Parsed structurally and keyword-agnostically (see :data:`_DEFINE_FIELD_RE`), so
    a pin asserting the ABSENCE of a declaration cannot be silently defeated by a
    change to the guard keyword.
    """
    declared = set()
    for statement in _statements(ddl):
        match = _DEFINE_FIELD_RE.match(statement)
        if match and match.group("table") == table:
            declared.add(match.group("field"))
    return declared


def _field_statement(ddl: str, table: str, field: str) -> str:
    """Return the single ``DEFINE FIELD ... ON <table> ...`` statement for
    ``field`` on ``table``, isolated so a per-field assertion can't be fooled
    by a substring match against some OTHER field or table.

    The served guard keyword is asserted here — ``DEFINE FIELD OVERWRITE``
    (finding #107) — so a regression to the no-op ``IF NOT EXISTS`` form cannot pass.
    The failure message is DERIVED from what was actually found, so that regression
    reads as what it IS instead of as a missing field.

    Raises:
        AssertionError: No matching ``DEFINE FIELD`` statement was found.
    """
    marker = f"DEFINE FIELD OVERWRITE {field} ON {table} "
    served: str | None = None
    for statement in _statements(ddl):
        if statement.startswith(marker):
            return statement
        match = _DEFINE_FIELD_RE.match(statement)
        if match and match.group("field") == field and match.group("table") == table:
            served = statement
    if served is not None:
        raise AssertionError(
            f"{table}.{field} is declared, but NOT with the required "
            f"`DEFINE FIELD OVERWRITE` guard (finding #107 — `IF NOT EXISTS` is a "
            f"NO-OP on a field that already exists, so a changed definition never "
            f"reaches a deployed store; this is what broke `brief_publish` 100% in "
            f"production while every test stayed green). Served: {served!r}"
        )
    raise AssertionError(f"no DEFINE FIELD statement found for {table}.{field} in generated DDL")


def _index_statements(ddl: str, table: str, *, fields_pattern: str) -> list[str]:
    """All ``DEFINE INDEX ... ON <table> ...`` statements whose ``FIELDS``
    clause matches ``fields_pattern`` (a regex fragment).
    """
    return [
        statement
        for statement in ddl.split(";\n")
        if statement.strip().startswith("DEFINE INDEX IF NOT EXISTS")
        and f"ON {table} " in statement
        and re.search(rf"FIELDS\s+{fields_pattern}", statement)
    ]


def _one(result: Any) -> dict[str, Any]:
    """Narrow a ``SELECT``'s list result to its single row."""
    assert isinstance(result, list) and len(result) == 1, f"expected one row, got {result!r}"
    row = result[0]
    assert isinstance(row, dict)
    return row


# --- live-store row builders ---------------------------------------------------


async def _create_agent(
    connection: SurrealConnection,
    *,
    agent_id: str,
    name: str,
    session: str,
    role: str = "builder",
    status: str = _AGENT_STATUS_ACTIVE,
    model: str | None = None,
    spawned_by: str | None = None,
    task_id: str | None = None,
    checkpoint: dict[str, Any] | None = None,
    last_note: str | None = None,
    registered_at: datetime | None = None,
    heartbeat_at: datetime | None = None,
) -> Any:
    """CREATE a full ``agent`` row via CONTENT (never ``SET session=`` — the
    engine rejects a top-level bound ``$session`` param outright since
    ``session`` is a SurrealDB PROTECTED variable name; see
    ``TestSessionProtectedVariable``).

    ``registered_at``/``heartbeat_at`` default to "now" here ONLY as a test
    convenience — the schema itself carries NO ``DEFAULT`` on either (design
    decision: plain, non-option, app-stamped datetimes, mirroring
    ``task.created_at`` — see ``TestAgentTimestampsAreAppStamped``).
    """
    now = datetime.now(UTC)
    content: dict[str, Any] = {
        "name": name,
        "session": session,
        "role": role,
        "status": status,
        "registered_at": registered_at if registered_at is not None else now,
        "heartbeat_at": heartbeat_at if heartbeat_at is not None else now,
    }
    if model is not None:
        content["model"] = model
    if spawned_by is not None:
        content["spawned_by"] = spawned_by
    if task_id is not None:
        content["task_id"] = task_id
    if checkpoint is not None:
        content["checkpoint"] = checkpoint
    if last_note is not None:
        content["last_note"] = last_note
    return await run(
        connection,
        f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT $content",
        {"id": agent_id, "content": content},
    )


async def _create_brief(
    connection: SurrealConnection,
    *,
    brief_id: str,
    name: str,
    version: int,
    body: str = "standing law",
    created_by: str = "lead",
    note: str | None = None,
    created_at: datetime | None = None,
) -> Any:
    """CREATE a full ``brief`` row via CONTENT.

    Omits ``created_at`` from the CONTENT dict entirely when ``None`` (never an
    explicit NONE) so the schema's own ``DEFAULT time::now()`` is exercised —
    mirrors ``_create_snapshot``'s git-metadata-omission idiom in
    ``test_surreal_schema.py``.
    """
    content: dict[str, Any] = {
        "name": name,
        "version": version,
        "body": body,
        "created_by": created_by,
    }
    if note is not None:
        content["note"] = note
    if created_at is not None:
        content["created_at"] = created_at
    return await run(
        connection,
        f"CREATE type::record('{BRIEF_TABLE}', $id) CONTENT $content",
        {"id": brief_id, "content": content},
    )


async def _relate_briefed(
    connection: SurrealConnection,
    *,
    agent_id: str,
    brief_id: str,
    via: str = _BRIEFED_VIA_REGISTER,
    at: datetime | None = None,
) -> Any:
    """RELATE one ``agent->briefed->brief`` edge.

    ``$from``/``$to`` are bound as SDK ``RecordID`` objects, NOT
    ``type::record()`` calls at the RELATE position — the latter is a 3.1.5
    PARSE ERROR (see module docstring); this is the working shape cloned from
    ``graph_surreal.py``'s ``_edge_statement``.
    """
    return await run(
        connection,
        f"RELATE $from->{BRIEFED_RELATION}->$to SET via = $via, at = $at",
        {
            "from": RecordID(AGENT_TABLE, agent_id),
            "to": RecordID(BRIEF_TABLE, brief_id),
            "via": via,
            "at": at if at is not None else datetime.now(UTC),
        },
    )


# A generous wall-clock skew allowance for a ``DEFAULT time::now()`` sanity
# bound — mirrors test_surreal_schema.py's ``_CLOCK_SKEW_ALLOWANCE``.
_CLOCK_SKEW_ALLOWANCE = timedelta(seconds=30)


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


# ===========================================================================
# Offline (pure, no server) DDL-string pins
# ===========================================================================


class TestAgentDdlOffline:
    """``generate_agent_ddl()`` — pure string-level pins on the generator's own
    output (no server needed).
    """

    def test_table_is_schemafull_and_idempotent_declaration(self) -> None:
        ddl = generate_agent_ddl()
        assert f"DEFINE TABLE IF NOT EXISTS {AGENT_TABLE} SCHEMAFULL" in ddl

    # 63c-i-a DUAL (ruling §9 item 6) — DELETED-WITH-REPLACEMENT: the agent name/session charset
    # DDL-text pin and the role non-empty DDL-text pin certified the OLD asserted world. Q3 DROPs
    # those three store ASSERTs (→ "") and MOVEs their predicate into ``AgentRegistry.register``
    # (AGENT_NAME_PATTERN.fullmatch on name/session, ``is_blank`` on role — TEACHING, before store
    # I/O). Keeping them would trap the builder between this file (ASSERT present) and the new
    # ``TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate``[agent] pin (ASSERT absent) —
    # the MP-7 corpse-certifier / C-DEF class. REPLACEMENTS: P2 [agent] (∀ name/session/role carry
    # NO ASSERT); the register MOVE pins in test_agent_registry.py (the writer refuses, teaching).
    # ``status`` is KEPT (§4.2), so its two domain pins below STAY.

    def test_status_domain_is_exactly_the_four_agent_statuses(self) -> None:
        ddl = generate_agent_ddl()
        status = _field_statement(ddl, AGENT_TABLE, "status")
        assert "TYPE string" in status
        assert "ASSERT" in status
        for value in _AGENT_STATUSES:
            assert f"'{value}'" in status

    def test_status_domain_excludes_orphaned(self) -> None:
        # 'orphaned' is DERIVED at render time and must NEVER be a storable
        # value (design doc §0/§3) — pinned as its OWN assertion, not folded
        # into the positive-domain test above, so a future edit that widens
        # the ASSERT to include it fails loudly and specifically here.
        ddl = generate_agent_ddl()
        status = _field_statement(ddl, AGENT_TABLE, "status")
        assert f"'{_AGENT_STATUS_ORPHANED}'" not in status

    def test_status_assert_is_KEPT_after_q3(self) -> None:
        """63c-i-a §4.2 KEEP guard. ``status`` is the ONE agent birth ASSERT Q3 KEEPS (reader-
        aligned: a junk status RAISES in ``_row_to_agent`` decoding ``AgentStatus``, so
        ``fleet``/``roster`` deny the WHOLE roster on one junk row). GREEN at HEAD AND after the
        build; RED the day the ``status`` ASSERT is dropped alongside name/session/role (which it
        must NOT be — its violation set == the reader's rejection set). The P2 [agent] exemption
        ``{status}`` non-vacuity leg is the parametrised twin of this guard."""
        status = _field_statement(generate_agent_ddl(), AGENT_TABLE, "status")
        assert "ASSERT" in status, (
            f"agent.status must KEEP its store ASSERT (§4.2 — the ONE reader-aligned agent "
            f"constraint; a junk status is a total roster-decode denial): {status!r}"
        )

    def test_status_ddl_vocabulary_aligns_with_the_reader_literal(self) -> None:
        """P-A2 (63c-i-a §4.3, the P-G2 twin, the ALIGNMENT pin). ``status``'s store ASSERT is
        KEPT because its violation set is EXACTLY the reader's rejection set — this proves that
        ONE-source claim BY MUTATION: the set inside the emitted ASSERT == ``AGENT_STATUSES`` ==
        ``set(get_args(AgentStatus))``.

        Mutation proof (declared): add a status to ``_AGENT_STATUS_ALLOWED``/``AGENT_STATUSES``
        only → the DDL set moves but the ``Literal`` does not (or vice-versa) → this pin RED. The
        three surfaces are ONE vocabulary or the KEEP's reader-alignment rests on a fiction."""
        status = _field_statement(generate_agent_ddl(), AGENT_TABLE, "status")
        match = re.search(r"ASSERT \$value IN \[([^\]]*)\]", status)
        assert match, f"could not parse the status ASSERT's IN-set from {status!r}"
        ddl_statuses = set(re.findall(r"'([^']*)'", match.group(1)))
        assert ddl_statuses, "the status ASSERT's IN-set parsed EMPTY — a vacuous alignment pin"
        constant_statuses = set(AGENT_STATUSES)
        literal_statuses = set(get_args(AgentStatus))
        assert ddl_statuses == constant_statuses == literal_statuses, (
            f"the agent status vocabulary DRIFTED across its three surfaces — DDL ASSERT "
            f"{sorted(ddl_statuses)}, AGENT_STATUSES {sorted(constant_statuses)}, Literal "
            f"{sorted(literal_statuses)}. They MUST be one source (§4.2): the store ASSERT rejects "
            f"exactly the values the reader's AgentStatus decode rejects, or the reader-alignment "
            f"the KEEP rests on is a fiction."
        )

    def test_optional_string_fields_are_option_string(self) -> None:
        ddl = generate_agent_ddl()
        for field in ("model", "spawned_by", "task_id", "last_note"):
            assert "option<string>" in _field_statement(ddl, AGENT_TABLE, field)

    def test_declared_cadence_is_option_string_with_no_assert(self) -> None:
        # W1a (packet 06a, #360/#257/#304). The NEW cadence self-declaration
        # field. Store reference §1.4: a NEW field on the production-POPULATED
        # ``agent`` table MUST be ``option<>`` with NO ASSERT — a required or
        # asserted field write-poisons every existing row's next UPDATE
        # (``Expected string but found NONE``), and a DEFAULT does not rescue an
        # already-present row. This mirrors the ``status_set_at`` (#304) precedent
        # EXACTLY (see ``test_optional_string_fields_are_option_string`` above and
        # ``_AGENT_FIELD_SPECS``'s ``("status_set_at", "option<datetime>", "")``).
        # ``_field_statement`` already fails unless the clause is
        # ``DEFINE FIELD OVERWRITE`` (finding #107), so this pin also carries the
        # OVERWRITE guard — a regression to ``IF NOT EXISTS`` reddens here.
        statement = _field_statement(generate_agent_ddl(), AGENT_TABLE, "declared_cadence")
        assert "option<string>" in statement, (
            "declared_cadence must be option<string> — store reference §1.4: a NEW "
            "field on the POPULATED agent table must be option<> or it write-poisons "
            f"every existing row's next UPDATE. Served: {statement!r}"
        )
        assert "ASSERT" not in statement, (
            "declared_cadence must carry NO ASSERT (store reference §1.4): an asserted "
            "field on a populated table poisons legacy rows on their next UPDATE, and a "
            "cadence is free-form agent text validated (if at all) at the app layer, "
            f"never by a store ASSERT. Served: {statement!r}"
        )

    def test_checkpoint_is_option_object_flexible(self) -> None:
        # The exact spelling verified live against 3.1.5 (module docstring):
        # FLEXIBLE trailing OUTSIDE the angle brackets.
        ddl = generate_agent_ddl()
        checkpoint = _field_statement(ddl, AGENT_TABLE, "checkpoint")
        assert "option<object>" in checkpoint
        assert "FLEXIBLE" in checkpoint
        assert "option<object FLEXIBLE>" not in checkpoint

    def test_registered_at_and_heartbeat_at_are_plain_app_stamped_datetimes(self) -> None:
        # Design decision (not stated explicitly by the spec, which is silent
        # on DEFAULT for these two — resolved by analogy to task.created_at /
        # task.claimed_at, the ledger-stamped idiom, since register/heartbeat
        # always explicitly supply both): NO DEFAULT. Live-verified in
        # TestAgentTimestampsAreAppStamped that a CREATE omitting either is
        # rejected, confirming this is exercised, not just declared.
        ddl = generate_agent_ddl()
        for field in ("registered_at", "heartbeat_at"):
            statement = _field_statement(ddl, AGENT_TABLE, field)
            assert "TYPE datetime" in statement
            assert "DEFAULT" not in statement

    def test_session_status_index_is_defined_and_non_unique(self) -> None:
        ddl = generate_agent_ddl()
        matches = _index_statements(ddl, AGENT_TABLE, fields_pattern=r"session,\s*status")
        assert matches, "expected a DEFINE INDEX on agent.(session, status)"
        assert not any("UNIQUE" in statement for statement in matches)

    def test_name_index_is_defined_and_non_unique(self) -> None:
        # Design doc §0 D7: a non-unique index on `name` alone, beyond the
        # plan's (session, status) — the §0.3 bare-name resolution SELECT
        # needs it or every comms call table-scans.
        ddl = generate_agent_ddl()
        matches = _index_statements(ddl, AGENT_TABLE, fields_pattern=r"name\b")
        assert matches, "expected a DEFINE INDEX on agent.name"
        assert not any("UNIQUE" in statement for statement in matches)


class TestBriefDdlOffline:
    """``generate_brief_ddl()`` — the ``brief`` node's pure string-level pins."""

    def test_table_is_schemafull(self) -> None:
        ddl = generate_brief_ddl()
        assert f"DEFINE TABLE IF NOT EXISTS {BRIEF_TABLE} SCHEMAFULL" in ddl

    def test_name_carries_the_verified_charset_assert(self) -> None:
        # "same class as agent.name" (design doc §0) — the identical pattern,
        # not a brief-specific one.
        ddl = generate_brief_ddl()
        name = _field_statement(ddl, BRIEF_TABLE, "name")
        assert _IDENTIFIER_CHARSET_ASSERT_TEXT in name

    def test_version_is_a_plain_int(self) -> None:
        ddl = generate_brief_ddl()
        assert "TYPE int" in _field_statement(ddl, BRIEF_TABLE, "version")

    def test_body_and_created_by_carry_the_non_empty_assert(self) -> None:
        ddl = generate_brief_ddl()
        for field in ("body", "created_by"):
            statement = _field_statement(ddl, BRIEF_TABLE, field)
            assert _NON_EMPTY_STRING_ASSERT_TEXT in statement

    def test_note_is_option_string(self) -> None:
        ddl = generate_brief_ddl()
        assert "option<string>" in _field_statement(ddl, BRIEF_TABLE, "note")

    def test_created_at_self_stamps_via_default_time_now(self) -> None:
        # "DEFAULT time::now() (findings idiom)" — design doc §0, explicit.
        ddl = generate_brief_ddl()
        created_at = _field_statement(ddl, BRIEF_TABLE, "created_at")
        assert "TYPE datetime" in created_at
        assert "DEFAULT" in created_at and "time::now()" in created_at

    def test_unique_name_version_index_is_defined(self) -> None:
        ddl = generate_brief_ddl()
        matches = _index_statements(ddl, BRIEF_TABLE, fields_pattern=r"name,\s*version")
        assert matches, "expected a DEFINE INDEX on brief.(name, version)"
        assert any("UNIQUE" in statement for statement in matches)


class TestBriefedDdlOffline:
    """``generate_brief_ddl()`` — the ``briefed`` edge's pure string-level pins.

    ``briefed`` ships from the SAME generator as ``brief`` (``BriefLedger``
    owns both tables — design doc §0/§Tool surface), mirroring how
    ``generate_finding_ddl()`` bundles ``finding`` + ``finding_counter``.
    """

    def test_table_is_a_schemafull_relation(self) -> None:
        """⚠ REWRITTEN by packet 03's relation-table policy flip (operator-ruled
        2026-07-19). This pin previously asserted the byte-exact OLD literal
        ``DEFINE TABLE IF NOT EXISTS briefed TYPE RELATION SCHEMAFULL`` — i.e. it
        CERTIFIED THE OLD WORLD, and would have gone red on a correct build,
        trapping the builder between this file and the new policy pins. Caught by
        grepping the test tree for assertions pinning the retired string (repo
        law: "tests written before a semantic change certify the OLD world").
        The endpoint-typing and OVERWRITE assertions now live in
        ``TestRelationTablePolicyFlip``; this pin keeps only what it always
        meant — briefed is a SCHEMAFULL relation table.
        """
        ddl = generate_brief_ddl()
        matches = [
            statement
            for statement in _statements(ddl)
            if statement.startswith("DEFINE TABLE")
            and f" {BRIEFED_RELATION} " in statement
            and "TYPE RELATION" in statement
        ]
        assert matches, f"no relation DEFINE TABLE for {BRIEFED_RELATION}"
        assert "SCHEMAFULL" in matches[0], matches[0]

    def test_via_domain_is_exactly_register_explicit_and_publish(self) -> None:
        """v7 (finding #98): the ASSERT's domain is the closed THREE-value set
        ``[register, explicit, publish]`` — ``publish`` is the author's
        self-ack, written by ``BriefLedger.publish`` in the same transaction as
        the brief row (design doc §0/§5.1 step 2).

        EXACT-SET, on the quoted literals parsed out of the served DDL. The
        retired version of this test asserted only that each of ITS OWN
        (two-word) constants APPEARED in the ASSERT — a SUBSET check, which is
        structurally incapable of failing when the domain must GAIN a word, and
        equally incapable of catching one it must never have. It did not go red
        for #98. A vocabulary pin that cannot fail a wrong vocabulary is not a
        pin.
        """
        ddl = generate_brief_ddl()
        via = _field_statement(ddl, BRIEFED_RELATION, "via")
        assert "TYPE string" in via
        quoted = re.findall(r"'([^']*)'", via)
        assert set(quoted) == {"register", "explicit", "publish"}, (
            f"the briefed.via ASSERT domain must be EXACTLY [register, explicit, publish] "
            f"(v7/finding #98 — publish() self-acks its author, §5.1 step 2; without "
            f"'publish' that RELATE is rejected and rolls the whole publish back). "
            f"Served domain: {quoted!r}"
        )
        assert set(quoted) == set(_BRIEFED_VIA_VALUES), (
            "this file's own vocabulary copy must agree with the served ASSERT"
        )

    def test_at_is_a_datetime_field(self) -> None:
        ddl = generate_brief_ddl()
        at = _field_statement(ddl, BRIEFED_RELATION, "at")
        assert "TYPE datetime" in at

    def test_in_and_out_are_never_hand_declared(self) -> None:
        """``TYPE RELATION`` auto-defines ``in``/``out``; the generator must never
        hand-declare them (``refers``/``answers_to`` don't either —
        surreal_schema.py:454's own docstring).

        REPAIRED (finding #107). The retired form was a pair of NEGATIVE substring
        assertions against the literal ``DEFINE FIELD IF NOT EXISTS in ON …``. When
        ``_define_field`` flipped to ``OVERWRITE``, the searched-for string could no
        longer appear in ANY DDL — so both assertions became unconditionally true and
        the pin passed VACUOUSLY, forever, structurally unable to detect the one
        thing it exists to detect. It did not go red; it went blind, which is worse:
        a pin that fails is a signal, a pin that quietly stops testing is decoration
        everybody still trusts.

        So the absence is now established STRUCTURALLY — parse the declared field
        names off the DDL and check membership — never by searching for a string that
        embeds today's guard keyword. And the parse is CONTROLLED (below), because an
        assertion of ABSENCE is only worth as much as the instrument's demonstrated
        ability to see PRESENCE.
        """
        ddl = generate_brief_ddl()
        declared = _declared_fields(ddl, BRIEFED_RELATION)

        # CONTROL — prove the instrument can SEE a hand-declared field on this exact
        # table before trusting its silence about `in`/`out`. Without this, a parser
        # that matched nothing would yield an empty set, and `"in" not in set()` is
        # trivially True: the pin would pass for the WRONG REASON, which is precisely
        # the failure mode being repaired. `via` and `at` ARE hand-declared here (the
        # two tests directly above assert their types), so they must be visible.
        assert {"via", "at"} <= declared, (
            f"instrument is blind: the DDL parser found {declared!r} on "
            f"{BRIEFED_RELATION}, which does not include the `via`/`at` fields the "
            f"generator demonstrably declares. Until it can see those, its silence "
            f"about `in`/`out` proves NOTHING. Fix the parser, not this assertion."
        )

        assert not ({"in", "out"} & declared), (
            f"{BRIEFED_RELATION} is a TYPE RELATION table — SurrealDB defines its "
            f"`in`/`out` endpoint columns itself. Hand-declaring them fights the "
            f"engine's own definition. Hand-declared: "
            f"{sorted({'in', 'out'} & declared)}"
        )

    def test_unique_in_out_index_is_defined(self) -> None:
        ddl = generate_brief_ddl()
        matches = _index_statements(ddl, BRIEFED_RELATION, fields_pattern=r"in,\s*out")
        assert matches, "expected a DEFINE INDEX on briefed.(in, out)"
        assert any("UNIQUE" in statement for statement in matches)


# ===========================================================================
# Live behavioural pins against the real server
# ===========================================================================


class TestSchemaAppliesAndIsIdempotent:
    """Both DDL slices apply cleanly to the live engine and are idempotent."""

    async def test_both_slices_apply_and_create_every_table(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_brief_ddl())
        info = await run(connection, "INFO FOR DB")
        tables = set(info.get("tables", {}))
        assert {AGENT_TABLE, BRIEF_TABLE, BRIEFED_RELATION} <= tables

    async def test_both_slices_are_idempotent(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        agent_ddl = generate_agent_ddl()
        brief_ddl = generate_brief_ddl()
        await run(connection, agent_ddl)
        await run(connection, brief_ddl)
        # Second application, EITHER order — must be a safe no-op (IF NOT
        # EXISTS semantics) and the schema must still be usable afterwards.
        await run(connection, agent_ddl)
        await run(connection, brief_ddl)

        agent_id = _agent_record_id("wave7", "idem-probe")
        await _create_agent(connection, agent_id=agent_id, name="idem-probe", session="wave7")
        row = _one(
            await run(connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id})
        )
        assert row["name"] == "idem-probe"


# 63c-i-a DUAL (ruling §9 item 6) — the agent ``TestAgentCharsetAssert`` (a LIVE store-rejection
# pin: it applied ``generate_agent_ddl()`` and asserted the STORE rejects a hostile ``name``/
# ``session``) is INVERTED across the contract, not kept here. After Q3 DROPs the agent
# name/session charset ASSERT, a RAW ``_create_agent`` of a hostile identifier SUCCEEDS (the store
# no longer rejects it) — so this pin would go RED on the correct build (a corpse). Its two virtues
# are PRESERVED-WITH-PIN elsewhere: (1) the store now ACCEPTS the dropped-ASSERT shape via the raw
# seeder — the DD-3.c Leg A drop-lands pin in test_agent_governance_63c_i_a.py; (2) a hostile
# identifier is REFUSED by the WRITER, teaching, before store I/O — the register MOVE pins in
# test_agent_registry.py. ``TestBriefCharsetAssert`` below is UNTOUCHED (brief.name's drop is 63c-ii).


class TestBriefCharsetAssert:
    """``brief.name`` shares the SAME charset ASSERT class as ``agent.name``."""

    @pytest.mark.parametrize("hostile_value", _HOSTILE_IDENTIFIERS)
    async def test_hostile_name_is_rejected(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        hostile_value: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_brief(
                connection, brief_id=uuid.uuid4().hex, name=hostile_value, version=1
            )

    @pytest.mark.parametrize("valid_value", _VALID_IDENTIFIERS)
    async def test_valid_name_is_accepted(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        valid_value: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        await _create_brief(connection, brief_id=uuid.uuid4().hex, name=valid_value, version=1)


class TestAgentStatusAssert:
    """The ``status`` domain: the four legal values accepted, everything else
    (including 'orphaned') rejected.
    """

    @pytest.mark.parametrize("status", _AGENT_STATUSES)
    async def test_each_valid_status_is_accepted(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        status: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await _create_agent(
            connection, agent_id=uuid.uuid4().hex, name="fixer-b", session="wave7", status=status
        )

    @pytest.mark.parametrize("bogus_status", [_AGENT_STATUS_ORPHANED, "bogus", "ACTIVE", ""])
    async def test_out_of_domain_status_is_rejected(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        bogus_status: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_agent(
                connection,
                agent_id=uuid.uuid4().hex,
                name="fixer-b",
                session="wave7",
                status=bogus_status,
            )


# 63c-i-a r2 DUAL (amendment-2 §D item 1 / adversary MP-1 — a sibling corpse r1's DUAL missed) —
# ``TestAgentRoleNonEmptyAssert`` is DELETED-WITH-REPLACEMENT. It applied ``generate_agent_ddl()`` and
# asserted the STORE rejects a blank/whitespace ``role`` (4 pins) plus a real-role positive control.
# Q3 DROPs the role non-empty ASSERT (ruling §4.2), so on every correct build the raw CREATE of a
# blank role SUCCEEDS and the four rejection pins go RED (measured: adversary §2 row 1). Virtues and
# their replacements: (1) "a blank/whitespace role never lands via the writer" → the register MOVE
# pins ``test_agent_registry.py::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::
# test_register_refuses_a_blank_role_before_any_store_write`` (``is_blank``-routed, teaching, zero
# rows) + ``…::test_the_blank_role_rule_is_the_SHARED_is_blank``; (2) "the store now ACCEPTS a
# legacy blank role" → ``test_agent_governance_63c_i_a.py::TestTheAgentAssertsDropFromADirtyStore63cIA::
# test_the_assert_DROPS_and_the_value_survives_byte_intact[role]``; (3) "a real role is accepted" →
# ``…::test_register_accepts_a_valid_identifier_positive_control`` (role="builder" on every param).


class TestBriefBodyAndCreatedByNonEmptyAssert:
    async def test_empty_body_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_brief(
                connection, brief_id=uuid.uuid4().hex, name="project", version=1, body="  "
            )

    async def test_empty_created_by_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_brief(
                connection, brief_id=uuid.uuid4().hex, name="project", version=1, created_by=""
            )


class TestBriefUniqueNameVersionIndex:
    """The UNIQUE(name, version) backstop — isolated from id-collision (each
    attempt below uses a DIFFERENT explicit id) so this pins the INDEX
    itself, not just "the deterministic id formula happens to collide".
    """

    async def test_duplicate_name_version_with_different_ids_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        await _create_brief(connection, brief_id=uuid.uuid4().hex, name="project", version=1)
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE-index violation surface
            await _create_brief(connection, brief_id=uuid.uuid4().hex, name="project", version=1)

    async def test_same_name_different_version_is_allowed(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        await _create_brief(connection, brief_id=uuid.uuid4().hex, name="project", version=1)
        await _create_brief(connection, brief_id=uuid.uuid4().hex, name="project", version=2)

    async def test_different_name_same_version_is_allowed(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        await _create_brief(connection, brief_id=uuid.uuid4().hex, name="project", version=1)
        await _create_brief(connection, brief_id=uuid.uuid4().hex, name="base", version=1)


class TestBriefedUniqueInOutIndex:
    """The UNIQUE(in, out) backstop on the ``briefed`` edge — the schema-level
    re-proof (not the cascade-delete probe, which is a prior/C2 concern; see
    module docstring) that a second RELATE of the SAME (agent, brief) pair is
    rejected, while a genuinely different pair succeeds.
    """

    async def test_duplicate_relate_of_the_same_pair_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_brief_ddl())
        agent_id = uuid.uuid4().hex
        brief_id = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        await _relate_briefed(connection, agent_id=agent_id, brief_id=brief_id, via="register")
        with pytest.raises(Exception):  # noqa: B017 - engine UNIQUE-index violation surface
            await _relate_briefed(connection, agent_id=agent_id, brief_id=brief_id, via="explicit")

    async def test_same_agent_different_brief_is_allowed(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_brief_ddl())
        agent_id = uuid.uuid4().hex
        brief_v1 = uuid.uuid4().hex
        brief_v2 = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        await _create_brief(connection, brief_id=brief_v1, name="project", version=1)
        await _create_brief(connection, brief_id=brief_v2, name="project", version=2)
        await _relate_briefed(connection, agent_id=agent_id, brief_id=brief_v1)
        await _relate_briefed(connection, agent_id=agent_id, brief_id=brief_v2)

    async def test_different_agent_same_brief_is_allowed(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_brief_ddl())
        agent_a = uuid.uuid4().hex
        agent_b = uuid.uuid4().hex
        brief_id = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_a, name="fixer-b", session="wave7")
        await _create_agent(connection, agent_id=agent_b, name="audit-c", session="wave7")
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        await _relate_briefed(connection, agent_id=agent_a, brief_id=brief_id)
        await _relate_briefed(connection, agent_id=agent_b, brief_id=brief_id)

    async def test_relate_endpoint_ids_round_trip_via_str_of_record_id(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # The RELATE endpoints come back as THE records related — compared by PARTS (R15 / MP-C 3c). The old
        # idiom "str(RecordID) is 'table:id'" holds on SDK 2.0 only: SDK 3.0 renders a digit-led key
        # 'table:⟨id⟩', so a test-side text compare is C9's class. FIXED digit-led ids make that
        # deterministic (a uuid4 hex is digit-led on ~62% of runs).
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_brief_ddl())
        agent_id = digit_led_record_key("comms-schema/briefed-endpoint/agent")
        brief_id = digit_led_record_key("comms-schema/briefed-endpoint/brief")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        edge = _one(await _relate_briefed(connection, agent_id=agent_id, brief_id=brief_id))
        assert same_record(edge["in"], f"{AGENT_TABLE}:{agent_id}")
        assert same_record(edge["out"], f"{BRIEF_TABLE}:{brief_id}")

    @pytest.mark.parametrize("legal_via", ["register", "explicit", "publish"])
    async def test_every_legal_via_is_accepted_by_the_live_assert(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        legal_via: str,
    ) -> None:
        """v7 (finding #98) — the LIVE half of the vocabulary pin: the applied
        ASSERT must actually admit all three words. ``publish`` is the one that
        matters: production's publish transaction RELATEs the author's self-ack
        with it, and a schema that still ASSERTs the retired two-value set
        rejects that statement — which, because the RELATE rides the SAME
        transaction as the brief CREATE (§5.1 step 2), silently rolls back the
        whole publish. A DDL-string pin alone would not catch a stale APPLIED
        schema; this drives the engine.
        """
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_brief_ddl())
        agent_id = uuid.uuid4().hex
        brief_id = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        edge = _one(
            await _relate_briefed(connection, agent_id=agent_id, brief_id=brief_id, via=legal_via)
        )
        assert edge["via"] == legal_via

    @pytest.mark.parametrize("bogus_via", ["bogus", "REGISTER", "", "PUBLISH", "publishing", "pub"])
    async def test_out_of_domain_via_is_rejected(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        bogus_via: str,
    ) -> None:
        """The ASSERT stays a CLOSED set after v7 widened it to three words.
        ``PUBLISH``/``publishing``/``pub`` are the adversarial neighbours of the
        newly-legal ``publish``: they catch a builder who relaxes the ASSERT into
        a substring/prefix/case-insensitive check instead of adding one literal
        to the ``IN [...]`` list.
        """
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_brief_ddl())
        agent_id = uuid.uuid4().hex
        brief_id = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _relate_briefed(connection, agent_id=agent_id, brief_id=brief_id, via=bogus_via)


class TestAgentIdDerivation:
    """The uuid5 id formula (design doc §0, "pin this exactly") — deterministic
    off pure Python, and its live consequence: CREATE-twice at the same id
    fails, UPSERT-twice is the idempotent-re-register mechanism the schema
    actually supports.
    """

    def test_formula_is_deterministic_for_the_same_session_and_name(self) -> None:
        assert _agent_record_id("wave7", "fixer-b") == _agent_record_id("wave7", "fixer-b")

    def test_formula_differs_for_different_inputs(self) -> None:
        base = _agent_record_id("wave7", "fixer-b")
        assert base != _agent_record_id("wave8", "fixer-b")  # different session
        assert base != _agent_record_id("wave7", "fixer-c")  # different name

    async def test_derived_id_round_trips_as_a_live_record_id(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = _agent_record_id("wave7", "fixer-b")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        assert same_record(row["id"], f"{AGENT_TABLE}:{agent_id}")

    async def test_recreate_at_the_same_derived_id_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # Documents WHY idempotent re-register needs UPSERT, not CREATE: a bare
        # CREATE at an id that already exists is an "already exists" rejection
        # (live-verified: AlreadyExistsError), never a silent overwrite.
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = _agent_record_id("wave7", "fixer-b")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        with pytest.raises(Exception):  # noqa: B017 - engine AlreadyExists surface
            await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")

    async def test_upsert_at_the_same_derived_id_is_idempotent(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = _agent_record_id("wave7", "fixer-b")
        content_first: dict[str, Any] = {
            "name": "fixer-b",
            "session": "wave7",
            "role": "builder",
            "status": _AGENT_STATUS_ACTIVE,
            "registered_at": datetime.now(UTC),
            "heartbeat_at": datetime.now(UTC),
        }
        content_second = {**content_first, "status": _AGENT_STATUS_IDLE}
        await run(
            connection,
            f"UPSERT type::record('{AGENT_TABLE}', $id) CONTENT $content",
            {"id": agent_id, "content": content_first},
        )
        await run(
            connection,
            f"UPSERT type::record('{AGENT_TABLE}', $id) CONTENT $content",
            {"id": agent_id, "content": content_second},
        )
        count_row = _one(await run(connection, f"SELECT count() FROM {AGENT_TABLE} GROUP ALL"))
        assert count_row["count"] == 1
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        assert row["status"] == _AGENT_STATUS_IDLE


class TestBriefIdDerivation:
    """The mirror of ``TestAgentIdDerivation`` for ``brief`` — uuid5 over
    ``(name, version)`` (design doc §0), the retry-safety property behind the
    publish mint's "re-CREATE cleanly after a rollback" claim (§5.1).
    """

    def test_formula_is_deterministic_for_the_same_name_and_version(self) -> None:
        assert _brief_record_id("project", 1) == _brief_record_id("project", 1)

    def test_formula_differs_for_different_inputs(self) -> None:
        base = _brief_record_id("project", 1)
        assert base != _brief_record_id("project", 2)
        assert base != _brief_record_id("base", 1)

    async def test_derived_id_round_trips_as_a_live_record_id(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        brief_id = _brief_record_id("project", 1)
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": BRIEF_TABLE, "id": brief_id}
            )
        )
        assert same_record(row["id"], f"{BRIEF_TABLE}:{brief_id}")

    async def test_recreate_at_the_same_derived_id_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # A retried publish attempt at the SAME (name, version) after a
        # rollback re-CREATEs cleanly ONLY if the prior attempt never
        # committed; a genuine duplicate is rejected — this is the id-
        # collision leg (contrast with TestBriefUniqueNameVersionIndex, which
        # isolates the INDEX backstop using DIFFERENT explicit ids).
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        brief_id = _brief_record_id("project", 1)
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        with pytest.raises(Exception):  # noqa: B017 - engine AlreadyExists surface
            await _create_brief(connection, brief_id=brief_id, name="project", version=1)


class TestAgentTimestampsAreAppStamped:
    """``registered_at``/``heartbeat_at`` carry NO ``DEFAULT`` — a CREATE that
    omits either is rejected, proving the design decision
    (``TestAgentDdlOffline.test_registered_at_and_heartbeat_at_are_plain_app_stamped_datetimes``)
    is actually load-bearing and not just declared.
    """

    async def test_missing_registered_at_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine required-field rejection surface
            await run(
                connection,
                f"CREATE {AGENT_TABLE} CONTENT $content",
                {
                    "content": {
                        "name": "fixer-b",
                        "session": "wave7",
                        "role": "builder",
                        "status": _AGENT_STATUS_ACTIVE,
                        "heartbeat_at": datetime.now(UTC),
                    }
                },
            )

    async def test_missing_heartbeat_at_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine required-field rejection surface
            await run(
                connection,
                f"CREATE {AGENT_TABLE} CONTENT $content",
                {
                    "content": {
                        "name": "fixer-b",
                        "session": "wave7",
                        "role": "builder",
                        "status": _AGENT_STATUS_ACTIVE,
                        "registered_at": datetime.now(UTC),
                    }
                },
            )


class TestCheckpointFlexibleRoundTrip:
    async def test_nested_object_round_trips_intact(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        checkpoint = {
            "phase": "red",
            "cursor": {"attempt": 2, "notes": ["a", "b"]},
            "flags": [True, False],
        }
        agent_id = uuid.uuid4().hex
        await _create_agent(
            connection, agent_id=agent_id, name="fixer-b", session="wave7", checkpoint=checkpoint
        )
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        assert row["checkpoint"] == checkpoint

    async def test_omitted_checkpoint_reads_back_none(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        assert row.get("checkpoint") is None

    async def test_explicit_none_reads_back_none(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = uuid.uuid4().hex
        await run(
            connection,
            f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT $content",
            {
                "id": agent_id,
                "content": {
                    "name": "fixer-b",
                    "session": "wave7",
                    "role": "builder",
                    "status": _AGENT_STATUS_ACTIVE,
                    "checkpoint": None,
                    "registered_at": datetime.now(UTC),
                    "heartbeat_at": datetime.now(UTC),
                },
            },
        )
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        assert row.get("checkpoint") is None


class TestAgentFullRoundTrip:
    async def test_every_field_populated_round_trips(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = uuid.uuid4().hex
        registered_at = datetime(2026, 7, 11, 10, 0, 0, tzinfo=UTC)
        heartbeat_at = datetime(2026, 7, 12, 1, 0, 0, tzinfo=UTC)
        await _create_agent(
            connection,
            agent_id=agent_id,
            name="fixer-b",
            session="wave7",
            role="builder",
            status=_AGENT_STATUS_INPUT_REQUIRED,
            model="claude-sonnet-5",
            spawned_by="lead",
            task_id="t-4f2a1c",
            checkpoint={"phase": "red"},
            last_note="blocked on operator answer",
            registered_at=registered_at,
            heartbeat_at=heartbeat_at,
        )
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        assert row["name"] == "fixer-b"
        assert row["session"] == "wave7"
        assert row["role"] == "builder"
        assert row["status"] == _AGENT_STATUS_INPUT_REQUIRED
        assert row["model"] == "claude-sonnet-5"
        assert row["spawned_by"] == "lead"
        assert row["task_id"] == "t-4f2a1c"
        assert row["checkpoint"] == {"phase": "red"}
        assert row["last_note"] == "blocked on operator answer"
        assert _as_utc(row["registered_at"]) == registered_at
        assert _as_utc(row["heartbeat_at"]) == heartbeat_at

    async def test_optional_fields_default_to_none_when_omitted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        for field in ("model", "spawned_by", "task_id", "checkpoint", "last_note"):
            assert row.get(field) is None

    async def test_undeclared_field_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        # Proves ``agent`` is a REAL SCHEMAFULL table, not a bare placeholder.
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection surface
            await run(
                connection,
                f"CREATE {AGENT_TABLE} CONTENT $content",
                {
                    "content": {
                        "name": "fixer-b",
                        "session": "wave7",
                        "role": "builder",
                        "status": _AGENT_STATUS_ACTIVE,
                        "registered_at": datetime.now(UTC),
                        "heartbeat_at": datetime.now(UTC),
                        "rogue_field": "not in the schema",
                    }
                },
            )


class TestBriefFullRoundTrip:
    async def test_every_field_populated_round_trips(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        brief_id = uuid.uuid4().hex
        created_at = datetime(2026, 7, 11, 9, 0, 0, tzinfo=UTC)
        await _create_brief(
            connection,
            brief_id=brief_id,
            name="project",
            version=5,
            body="# Standing law\n\nRegister before anything else.",
            created_by="lead",
            note="initial cut",
            created_at=created_at,
        )
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": BRIEF_TABLE, "id": brief_id}
            )
        )
        assert row["name"] == "project"
        assert row["version"] == 5
        assert row["body"] == "# Standing law\n\nRegister before anything else."
        assert row["created_by"] == "lead"
        assert row["note"] == "initial cut"
        assert _as_utc(row["created_at"]) == created_at

    async def test_note_defaults_to_none_when_omitted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        brief_id = uuid.uuid4().hex
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": BRIEF_TABLE, "id": brief_id}
            )
        )
        assert row.get("note") is None

    async def test_created_at_is_auto_populated_when_omitted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        brief_id = uuid.uuid4().hex
        before = datetime.now(UTC)
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        after = datetime.now(UTC)
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": BRIEF_TABLE, "id": brief_id}
            )
        )
        created_at = row["created_at"]
        assert isinstance(created_at, datetime)
        assert before - _CLOCK_SKEW_ALLOWANCE <= _as_utc(created_at) <= after + _CLOCK_SKEW_ALLOWANCE

    async def test_undeclared_field_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine SCHEMAFULL rejection surface
            await run(
                connection,
                f"CREATE {BRIEF_TABLE} CONTENT $content",
                {
                    "content": {
                        "name": "project",
                        "version": 1,
                        "body": "standing law",
                        "created_by": "lead",
                        "rogue_field": "not in the schema",
                    }
                },
            )


class TestSessionProtectedVariable:
    """``session`` is a SurrealDB PROTECTED variable name: a top-level bound
    ``$session`` param is rejected outright regardless of table; CONTENT with
    ``session`` as an object KEY is legal (repo CLAUDE.md store idiom).
    """

    async def test_session_as_a_top_level_set_param_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        with pytest.raises(Exception):  # noqa: B017 - protected-variable rejection surface
            await run(
                connection,
                f"CREATE {AGENT_TABLE} SET name = $name, session = $session, role = $role, "
                "status = 'active', registered_at = time::now(), heartbeat_at = time::now()",
                {"name": "fixer-b", "session": "wave7", "role": "builder"},
            )

    async def test_session_as_a_content_object_key_succeeds(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        assert row["session"] == "wave7"


class TestMissingProjectionReadsNone:
    async def test_unrequested_option_field_is_absent_from_a_subset_select(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        agent_id = uuid.uuid4().hex
        await _create_agent(
            connection, agent_id=agent_id, name="fixer-b", session="wave7", model="claude-sonnet-5"
        )
        row = _one(
            await run(
                connection,
                "SELECT name FROM type::record($t, $id)",
                {"t": AGENT_TABLE, "id": agent_id},
            )
        )
        assert row["name"] == "fixer-b"
        # Never a KeyError — a projection that didn't ask for `model` reads
        # back as absent, safe via .get().
        assert row.get("model") is None


class TestBriefBodyHostileRoundTrip:
    """Storage-layer hostile-fixture requirement (brief-base §3): a hostile
    ``brief.body`` (control chars + a row-shaped forgery payload) is stored
    and read back BYTE-IDENTICAL, unsanitised — design doc §5.2/§9: bodies are
    "stored RAW and round-trip verbatim (render via render_fenced ONLY)".
    Sanitisation is the RENDER layer's job (a separate C1 seam, out of S1's
    scope); this test pins that STORAGE does not mangle the raw bytes it must
    later be sanitised FROM.
    """

    @pytest.mark.parametrize("threat_char", _INJECTION_THREAT_CHARS)
    async def test_hostile_char_plus_row_forge_payload_round_trips_verbatim(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        threat_char: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        hostile_body = f"standing law{threat_char}{_ROW_FORGE_PAYLOAD}"
        brief_id = uuid.uuid4().hex
        await _create_brief(connection, brief_id=brief_id, name="project", version=1, body=hostile_body)
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": BRIEF_TABLE, "id": brief_id}
            )
        )
        assert row["body"] == hostile_body


class TestAgentLastNoteHostileRoundTrip:
    """``last_note`` carries no charset restriction (free text, design doc §0)
    — the same storage-layer hostile-fixture requirement as brief.body.
    """

    @pytest.mark.parametrize("threat_char", _INJECTION_THREAT_CHARS)
    async def test_hostile_char_plus_row_forge_payload_round_trips_verbatim(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        threat_char: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        hostile_note = f"blocked{threat_char}{_ROW_FORGE_PAYLOAD}"
        agent_id = uuid.uuid4().hex
        await _create_agent(
            connection, agent_id=agent_id, name="fixer-b", session="wave7", last_note=hostile_note
        )
        row = _one(
            await run(
                connection, "SELECT * FROM type::record($t, $id)", {"t": AGENT_TABLE, "id": agent_id}
            )
        )
        assert row["last_note"] == hostile_note


class TestBriefCounterDdlOffline:
    """``generate_brief_ddl()`` — the ``brief_counter`` mint table's pure
    string-level pin (audit-confirmed gap, ``REPORT-c1-audit-final.md`` D3):
    ``_brief_counter_statements()`` IS wired into ``generate_brief_ddl()``,
    but no test asserted the emitted DDL actually carries it — the live
    ``TestSchemaAppliesAndIsIdempotent.test_both_slices_apply_and_create_every_table``
    check is a SUBSET check (``<=``) and stays green even with the
    declaration deleted outright, since SurrealDB auto-creates the table
    SCHEMALESS on first write. This is a direct ``in ddl`` membership check —
    the same idiom ``test_surreal_schema.py``'s sibling
    ``test_finding_counter_table_backs_the_number_mint`` already uses for
    ``finding_counter`` — so removing the declaration fails HERE, not just
    behaviourally-indistinguishably at the live layer.
    """

    def test_table_backs_the_per_name_mint(self) -> None:
        ddl = generate_brief_ddl()
        assert f"DEFINE TABLE IF NOT EXISTS {BRIEF_COUNTER_TABLE} SCHEMAFULL" in ddl
        # The mint's own ``next ?? 0`` coalesce (``briefs.py._mint_version``)
        # depends on this exact type/default pairing.
        next_field = _field_statement(ddl, BRIEF_COUNTER_TABLE, "next")
        assert "TYPE int" in next_field
        assert "DEFAULT" in next_field and "0" in next_field


class TestBriefCounterPerNamePartition:
    """Live: bumping the mint counter for two DIFFERENT brief names touches
    two DIFFERENT rows with independent sequences — the per-name partition
    design doc §5.1 relies on (``brief_counter:alpha`` never contends with
    ``brief_counter:beta``). Issues the exact bump statement
    ``BriefLedger._mint_version`` uses (``briefs.py``), not a re-invented
    query shape.
    """

    async def test_two_names_mint_independent_sequences(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_brief_ddl())
        bump = (
            f"UPSERT type::record('{BRIEF_COUNTER_TABLE}', $name) "
            "SET next = (next ?? 0) + 1 RETURN AFTER"
        )
        alpha_first = _one(await run(connection, bump, {"name": "alpha"}))
        alpha_second = _one(await run(connection, bump, {"name": "alpha"}))
        beta_first = _one(await run(connection, bump, {"name": "beta"}))
        assert alpha_first["next"] == 1
        assert alpha_second["next"] == 2
        # `beta`'s row starts fresh at 1 — unaffected by `alpha`'s two prior
        # bumps, proving the two names never share a counter row.
        assert beta_first["next"] == 1
        assert str(alpha_first["id"]) != str(beta_first["id"])


# ===========================================================================
# PACKET 03 (the durable core — TEST-ONLY, no deploy) — the ``message`` node
# + the ``to`` delivery edge + the native
# ``DEFINE SEQUENCE`` that mints ``message.seq``.
#
# Every store fact asserted here is CITED, never re-derived:
# ``docs/reference/surrealdb-31-capabilities.md`` §1.1 (the SEQUENCE row of the
# DDL decision rule, and why INDEX/TABLE/SEQUENCE stay ``IF NOT EXISTS`` while
# FIELD is ``OVERWRITE``), §4 (UNIQUE-on-relation is legal and the #7061
# cascade hazard is settled ABSENT), §5 (``sequence::nextval``; gaps are real),
# plus ``REPORT-probe-pkt03-store.md`` probes 2/3/5.
# ===========================================================================


class TestMessageDdlOffline:
    """``generate_message_ddl()`` — pure string-level pins (no server needed)."""

    def test_defines_the_message_node_table_schemafull(self) -> None:
        assert f"DEFINE TABLE IF NOT EXISTS {_schema().MESSAGE_TABLE} SCHEMAFULL" in _statements(
            generate_message_ddl()
        )

    def test_defines_the_to_edge_as_a_typed_relation_table(self) -> None:
        """Probe 5d: without ``TYPE RELATION`` the engine auto-creates the edge
        table as ``TYPE ANY``, SILENTLY discarding the ``IN``/``OUT`` type
        constraint — which store reference §4 records as the ONLY endpoint
        validation the engine offers. A missing DDL entry does not fail loudly;
        it downgrades the guard.
        """
        statements = _statements(generate_message_ddl())
        relation = [
            statement
            for statement in statements
            if statement.startswith("DEFINE TABLE")
            and f" {_schema().TO_RELATION} " in statement
            and "TYPE RELATION" in statement
        ]
        assert relation, f"no DEFINE TABLE for the {_schema().TO_RELATION} edge"
        # OPERATOR-RULED 2026-07-19: the statement is named VERBATIM in Scope IN.
        # Every clause is load-bearing and each was measured, not assumed:
        #   OVERWRITE  — ``IF NOT EXISTS`` is a MEASURED SILENT NO-OP for a
        #                changed relation clause (probe Q2). It returns OK, the
        #                stored definition is unchanged, and a ghost RELATE still
        #                succeeds. #107's shape — and WORSE, because on a virgin
        #                DB the table does not exist, so IF NOT EXISTS creates it
        #                WITH the guard and every test passes while no long-lived
        #                store ever gains it.
        #   IN/OUT     — the house helper emits NEITHER today, so every shipped
        #                relation table is untyped. Without them there is no
        #                endpoint typing at all.
        #   ENFORCED   — validates BOTH endpoints against existing records, and
        #                is the ONLY thing that closes the ``INSERT RELATION``
        #                door (probe UNASKED-1) — a door no app-level check on
        #                ``send`` can reach, because it is not on that path.
        expected = (
            f"DEFINE TABLE OVERWRITE {_schema().TO_RELATION} TYPE RELATION "
            f"IN {_schema().MESSAGE_TABLE} OUT {AGENT_TABLE} ENFORCED SCHEMAFULL"
        )
        assert relation[0] == expected, (
            f"the delivery edge's DEFINE TABLE must be exactly:\n  {expected}\nserved:\n  "
            f"{relation[0]}\nEach clause was probed; see this test's own comment for which "
            f"failure each one prevents."
        )

    @pytest.mark.parametrize(
        ("field", "type_fragment"),
        [
            ("seq", "int"),
            ("session", "string"),
            ("thread", "string"),
            ("sender", f"record<{AGENT_TABLE}>"),
            ("grade", "string"),
            ("body", "string"),
            ("refs", "array"),
            ("task_id", "option<string>"),
            ("created_at", "datetime"),
        ],
    )
    def test_message_field_is_declared_with_the_overwrite_guard(
        self, field: str, type_fragment: str
    ) -> None:
        statement = _field_statement(generate_message_ddl(), _schema().MESSAGE_TABLE, field)
        assert type_fragment in statement, f"{field}: expected {type_fragment!r} in {statement!r}"

    def test_grade_ddl_is_a_closed_two_value_domain(self) -> None:
        """P-G2 (63b-ii-b §13.3, the ALIGNMENT pin). ``grade``'s store ASSERT is
        KEPT (R19: its violation set is EXACTLY the reader's rejection set — a
        junk grade cannot be decoded into ``InboxEntry.grade: MessageGrade``, so
        the store guard is reader-aligned, not a duplicated length cap). This pin
        proves the ONE-source claim §13.1 rests on BY MUTATION: the set inside the
        emitted ASSERT == ``MESSAGE_GRADES`` == ``set(get_args(MessageGrade))``.

        Mutation proof (declared): append a grade to ``_MESSAGE_GRADES`` → the DDL
        set and the frozenset move together, the ``Literal`` does NOT → this pin
        RED. That is "prove sharing by mutation" for the vocabulary's single
        source; a lenient decode (dropping the ASSERT and widening the Literal)
        would silently mis-grade a directive, worse than the loud store refusal.
        """
        statement = _field_statement(generate_message_ddl(), _schema().MESSAGE_TABLE, "grade")
        assert "ASSERT" in statement, (
            f"the grade ASSERT is GONE — R19 (63b-ii-b §13) KEEPS it: a store that can hold a "
            f"grade its reader cannot decode is a total drain-decode denial from one row. "
            f"served: {statement!r}"
        )
        assert "'signal'" in statement
        assert "'directive'" in statement
        # P-G2: the three vocabulary surfaces are ONE source, proven by equality.
        match = re.search(r"ASSERT \$value IN \[([^\]]*)\]", statement)
        assert match, f"could not parse the grade ASSERT's IN-set from {statement!r}"
        ddl_grades = set(re.findall(r"'([^']*)'", match.group(1)))
        assert ddl_grades, "the grade ASSERT's IN-set parsed EMPTY — a vacuous alignment pin"
        message_grades = set(_messages().MESSAGE_GRADES)
        literal_grades = set(get_args(_messages().MessageGrade))
        assert ddl_grades == message_grades == literal_grades, (
            f"the grade vocabulary DRIFTED across its three surfaces — DDL ASSERT "
            f"{sorted(ddl_grades)}, MESSAGE_GRADES {sorted(message_grades)}, "
            f"Literal {sorted(literal_grades)}. They MUST be one source (§13.1): the store "
            f"ASSERT rejects exactly the values the reader's Literal decode rejects, or the "
            f"reader-alignment R19 rests on is a fiction."
        )

    # MP-7 (sidecar §14.0) — ``test_body_carries_a_length_bound_the_store_itself_enforces`` DELETED
    # here as a CORPSE CERTIFIER / C-DEF: it asserted ``body``'s store ASSERT (the OLD world) and
    # CANNOT pass the correct build — W9 (§13.3) DROPS ``body``'s length ASSERT, so it trapped the
    # builder between P2-m (which demands NO ASSERT) and this pin (which demanded one), every gate
    # green. Its replacement already exists: ``TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate``
    # is the inverse ∀ (no field carries a legacy-violable constraint) and D-M2 pins the APP cap
    # (``MessageLedger`` teaching reject) that replaces the store backstop.

    @pytest.mark.parametrize("field", ["seen_at", "acked_at"])
    def test_the_cas_stamp_columns_are_option_datetime(self, field: str) -> None:
        """Consequence #10: the stamps MUST be ``option<datetime>`` so
        ``WHERE ... IS NONE`` is a real write-once guard. A non-option column
        with a DEFAULT would make every edge look already-stamped.
        """
        statement = _field_statement(generate_message_ddl(), _schema().TO_RELATION, field)
        assert "option<datetime>" in statement, statement

    def test_the_to_edge_never_hand_declares_in_or_out(self) -> None:
        declared = _declared_fields(generate_message_ddl(), _schema().TO_RELATION)
        assert not ({"in", "out"} & declared), (
            f"{_schema().TO_RELATION} is a TYPE RELATION table — SurrealDB defines its in/out "
            f"endpoint columns itself; hand-declaring them fights the engine"
        )

    def test_unique_in_out_index_is_defined_on_the_to_edge(self) -> None:
        """Probe 2: UNIQUE(in, out) is SAFE on 3.1.5 (endpoint deletion cascades
        the edge AND cleans the index entry; the #7061 hazard is settled ABSENT)
        and gives one delivery edge per message-recipient pair.
        """
        matches = _index_statements(
            generate_message_ddl(), _schema().TO_RELATION, fields_pattern=r"in,\s*out"
        )
        assert matches, f"expected a DEFINE INDEX on {_schema().TO_RELATION}.(in, out)"
        assert any("UNIQUE" in statement for statement in matches)

    def test_a_drain_index_on_out_and_seen_at_exists(self) -> None:
        """"Unread" = my unstamped to-edges. Without an index the drain SELECT
        table-scans every delivery edge in the store on every comms call.
        """
        matches = _index_statements(
            generate_message_ddl(), _schema().TO_RELATION, fields_pattern=r"out,\s*seen_at"
        )
        assert matches, (
            f"expected a DEFINE INDEX on {_schema().TO_RELATION}.(out, seen_at) for the drain SELECT"
        )

    # ----------------------------------------------------------------------- #
    # The two ``message`` hot-path indexes — packet 03b (E-S6, lead-directed
    # 2026-07-24). Design authority: ``03a-2-consume-path-design-rulings.md`` R3
    # part (1), carried into ``03b-design-rulings-r2.md`` B10 row 3 as OPEN work.
    #
    # THE DEPLOY WINDOW, and why these two lines ship with 03b or cost forever: a
    # NEW index on a POPULATED table BUILDS, blocking, at the first
    # ``ensure_ready`` that carries it (store reference §1.5). Production carries
    # ZERO ``message``/``to`` rows today — packets 03/03a-1/03a-2 are test-only, and
    # this DDL is applied ONLY by ``MessageLedger.ensure_ready``, which nothing in
    # the deployed server instantiates until 03b's dispatcher exists. So an index
    # shipped WITH 03b builds over an empty table for free, exactly once; the same
    # line shipped by any later packet builds over months of accumulated rows at
    # every deployed store's next boot. **The cheap window closes at 03b's deploy,
    # permanently.**
    #
    # The ``IF NOT EXISTS`` guard kind is NOT re-asserted here: R3 records that
    # ``test_every_field_uses_the_overwrite_guard_and_every_object_uses_if_not_
    # exists`` (below) already covers every object in this slice automatically,
    # and ``_index_statements`` only matches statements carrying it. Two copies of
    # one invariant is two copies to drift.
    # ----------------------------------------------------------------------- #

    def test_the_seq_index_is_defined_PLAIN_on_the_message_table(self) -> None:
        """R3(1): ``message_seq`` over ``(seq)`` serves ``ack``'s seq resolution.

        Without it, ``_resolve_message_ids``' ``WHERE seq IN $seqs`` table-scans
        every message ever sent, on every ack. PLAIN, not UNIQUE: R3 records the
        non-UNIQUE choice as a deliberate, strikeable divergence from the approved
        design with a named re-open trigger, so a UNIQUE index here would be a
        silent semantics change (it would reject a second row per seq rather than
        merely failing to speed a read).

        The ``FIELDS`` pattern is END-ANCHORED so it means "these fields EXACTLY":
        measured in
        ``test_the_index_field_patterns_discriminate_single_from_composite``, it
        matches NEITHER ``FIELDS seq, thread`` nor ``FIELDS thread, seq`` — an
        index whose fields are a superset serves a different query shape and must
        not green this pin.
        """
        ddl = generate_message_ddl()
        table = _schema().MESSAGE_TABLE
        matches = _index_statements(ddl, table, fields_pattern=r"seq$")
        assert matches, (
            f"expected a DEFINE INDEX on {table}.(seq) — R3(1) names it "
            f"`{table}_seq` and it must land BEFORE 03b's deploy, in its own "
            f"one-concern commit, while the table is still empty."
        )
        assert len(matches) == 1, f"expected exactly one (seq) index, got {matches!r}"
        assert f"DEFINE INDEX IF NOT EXISTS {table}_seq ON {table} " in matches[0].strip(), (
            f"the index name is R3-ruled as `{table}_seq` (the name is what an "
            f"`INFO FOR TABLE` introspection and any later ALTER/REMOVE keys on); "
            f"served: {matches[0].strip()!r}"
        )
        assert "UNIQUE" not in matches[0], (
            f"the (seq) index must be PLAIN, not UNIQUE — R3 rules the divergence "
            f"deliberately; served: {matches[0].strip()!r}"
        )

    def test_the_sender_question_index_is_defined_SENDER_FIRST(self) -> None:
        """R3(1): ``message_sender_question`` over ``(sender, question)``.

        Serves the questions read (``WHERE question = true AND sender = $agent``),
        which R4 requires to run FIRST. **Field ORDER is load-bearing:** sender is
        the selective prefix (one agent's rows), while ``question`` is a boolean
        that halves the table at best — so ``(question, sender)`` is a different,
        far worse index for this query. The reversed-order leg below is the pin
        that tells the two apart; an unordered "both columns are mentioned" check
        would wave the bad one through.
        """
        ddl = generate_message_ddl()
        table = _schema().MESSAGE_TABLE
        matches = _index_statements(ddl, table, fields_pattern=r"sender,\s*question$")
        assert matches, (
            f"expected a DEFINE INDEX on {table}.(sender, question) for the "
            f"questions read — R3(1) names it `{table}_sender_question`."
        )
        assert len(matches) == 1, f"expected exactly one (sender, question) index, got {matches!r}"
        assert (
            f"DEFINE INDEX IF NOT EXISTS {table}_sender_question ON {table} " in matches[0].strip()
        ), f"the index name is R3-ruled as `{table}_sender_question`; served: {matches[0].strip()!r}"
        assert "UNIQUE" not in matches[0], (
            f"many messages share a (sender, question) pair; a UNIQUE index would "
            f"reject the second one. Served: {matches[0].strip()!r}"
        )
        assert not _index_statements(ddl, table, fields_pattern=r"question,\s*sender$"), (
            "the index is declared (question, sender) — the reversed prefix. Sender "
            "is the SELECTIVE column; leading with a boolean makes the index nearly "
            "useless for the questions read it exists to serve."
        )

    def test_the_index_field_patterns_discriminate_single_from_composite(self) -> None:
        """THE CONTROL for the two pins above: their ``FIELDS`` patterns discriminate.

        Both lean on an END-ANCHORED pattern to mean "these fields EXACTLY". A
        pattern that matched any SUPERSET would let each pin be satisfied by a
        neighbouring index — passing for a fixture reason rather than because the
        index it names exists. Both directions of superset are checked, because
        only one of them (the leading-prefix case) is intuitively excluded.

        The fixtures are built HERE rather than read from the production DDL, so
        this control keeps testing the INSTRUMENT even after the two indexes land
        (a control that starts depending on the thing it certifies stops being a
        control).

        Measured while writing this: ``FIELDS\\s+seq$`` does NOT match
        ``FIELDS thread, seq`` — ``re.search`` needs ``FIELDS`` + whitespace +
        ``seq`` + end-of-line contiguously, and ``FIELDS`` occurs once. The first
        draft of this control asserted the OPPOSITE as a "documented bound" of the
        shared idiom; the assertion failed, and the false claim went with it.
        """
        table = _schema().MESSAGE_TABLE

        def statement(name: str, fields: str) -> str:
            return f"DEFINE INDEX IF NOT EXISTS {name} ON {table} FIELDS {fields};\n"

        # POSITIVE: each pattern sees the exact clause it is written for.
        assert _index_statements(statement("probe", "seq"), table, fields_pattern=r"seq$")
        assert _index_statements(
            statement("probe", "sender, question"), table, fields_pattern=r"sender,\s*question$"
        )
        # NEGATIVE, both superset directions: a wider index serves a different
        # query shape and must never satisfy an exact-fields pin.
        for fields in ("thread, seq", "seq, thread"):
            assert not _index_statements(statement("wider", fields), table, fields_pattern=r"seq$"), (
                f"`FIELDS {fields}` satisfied the exact single-column (seq) pattern; the "
                f"(seq) pin could then be green with only a composite index present."
            )
        for fields in ("sender, question, thread", "thread, sender, question"):
            assert not _index_statements(
                statement("wider", fields), table, fields_pattern=r"sender,\s*question$"
            ), f"`FIELDS {fields}` satisfied the exact (sender, question) pattern."
        # NEGATIVE: the reversed composite, which the SENDER_FIRST pin's own final
        # leg relies on being distinguishable.
        assert not _index_statements(
            statement("reversed", "question, sender"), table, fields_pattern=r"sender,\s*question$"
        )

    def test_the_sequence_is_defined_IF_NOT_EXISTS(self) -> None:
        """Store reference §1.1's SEQUENCE row (settled by this packet's own
        probe 3 leg D): a BARE ``DEFINE SEQUENCE`` RAISES *"the sequence
        already exists"* — and ``ensure_ready()`` re-applies the DDL at EVERY
        boot, so a bare DEFINE is a boot-time crash, the same failure mode
        §1.1 cites for flipping INDEX to OVERWRITE.
        """
        statements = _statements(generate_message_ddl())
        matching = [
            statement
            for statement in statements
            if statement.startswith("DEFINE SEQUENCE") and _schema().MESSAGE_SEQUENCE_NAME in statement
        ]
        assert matching, f"no DEFINE SEQUENCE for {_schema().MESSAGE_SEQUENCE_NAME!r}"
        assert matching[0].startswith("DEFINE SEQUENCE IF NOT EXISTS"), (
            f"the sequence must be IF NOT EXISTS (a bare DEFINE raises on re-apply and a "
            f"boot-time crash is the result); served: {matching[0]!r}"
        )

    def test_every_field_uses_the_overwrite_guard_and_every_object_uses_if_not_exists(
        self,
    ) -> None:
        """The #107 decision rule, asserted structurally over the WHOLE slice so
        a field added later cannot quietly arrive with ``IF NOT EXISTS``.
        """
        # ⚠ SUPERSEDES this pin's own first version (contract UPDATE 5eb445b):
        # it originally asserted IF NOT EXISTS for EVERY ``DEFINE TABLE``, which
        # the relation-table policy flip makes wrong for edges. The rule is now
        # per-OBJECT-KIND, and each branch carries the failure it prevents:
        #   FIELD           OVERWRITE      — #107: INE never migrates a changed field
        #   RELATION TABLE  OVERWRITE      — probe Q2: INE never migrates a changed
        #                                    relation clause, silently
        #   NODE TABLE      IF NOT EXISTS  — our node table clauses never change
        #   INDEX           IF NOT EXISTS  — OVERWRITE REBUILDS; a boot-time crash
        #   SEQUENCE        IF NOT EXISTS  — a bare DEFINE RAISES on re-apply
        for statement in _statements(generate_message_ddl()):
            if statement.startswith("DEFINE FIELD"):
                assert statement.startswith("DEFINE FIELD OVERWRITE "), statement
            elif statement.startswith("DEFINE TABLE") and "TYPE RELATION" in statement:
                assert statement.startswith("DEFINE TABLE OVERWRITE "), (
                    f"a RELATION table must be OVERWRITE — IF NOT EXISTS is a measured "
                    f"silent no-op for a changed relation clause: {statement!r}"
                )
            elif statement.startswith(("DEFINE TABLE", "DEFINE INDEX", "DEFINE SEQUENCE")):
                assert "IF NOT EXISTS" in statement, statement


class TestTheMessageStoreCarriesNoAssertALegacyRowCanViolate:
    """63b-ii-b §12/§13 (D-M11, renamed from ``TestThePointerBoundsHaveTheirSTOREBackstop``).

    ⚠ SUPERSESSION (§12.9 R18 / §5 D3): the store no longer backstops the four
    LENGTH bounds on ``message`` (thread · body · refs count · refs[*] · task_id)
    NOR the ``to.ack_note`` bound. **Neither table keeps "both layers"** — the app
    cap in ``MessageLedger.send`` / ``.ack`` is the ONE implementation of each
    length policy (ONE IMPLEMENTATION, #102). ``grade`` is the SOLE exception the
    store still asserts (R19, §13.1): its violation set is EXACTLY the reader's
    rejection set (``InboxEntry.grade: MessageGrade`` — a junk grade cannot decode),
    so it is a reader-aligned domain guard, not a duplicated length cap.

    WHY the length ASSERTs were DROPPED, not kept: ``message`` is UPDATE-able (the
    §4.C cutover migrate re-validates every legacy row in ONE statement) and ``to``
    is UPDATE-HOT (drain stamps it in one statement over the window) — a store
    constraint either table carries is DD-3.c, a legacy row that violates it
    refusing the whole statement (total inbox denial on ``to``; a refused cutover on
    ``message``). Cite §3.4 (``to``) and §12.4 (``message``) for the ∀ invariant,
    pinned in ``TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate`` below.

    What SURVIVES here: the two NON-assert virtues (``refs`` keeps ``DEFAULT []``;
    ``refs[*]`` keeps ``OVERWRITE`` — a bare re-definition of an implicit array
    element path raises, AND on ``:18500`` the OVERWRITE is what drops the stored
    ASSERT, Leg A's live twin). The four deleted length legs and the ``ack_note``
    leg are named in the commit message (the rename-sweep law), replaced by the ∀
    pin + Leg A/B.

    Pins the EMITTED statement, never ``INFO FOR TABLE``'s echo — the engine
    NORMALISES what it echoes (``option<string>`` comes back as
    ``none | string``), so an echo-diffing pin mismatches a correct build. House
    idiom: assert what we send.
    """

    @staticmethod
    def _field(ddl: str, table: str, name: str) -> str:
        prefix = f"DEFINE FIELD OVERWRITE {name} ON {table} "
        matches = [text.strip() for text in ddl.split(";\n") if text.strip().startswith(prefix)]
        assert len(matches) == 1, (
            f"expected exactly ONE definition of {table}.{name}, got {matches!r}"
        )
        return matches[0]

    def test_refs_still_carries_its_DEFAULT_but_no_COUNT_assert(self) -> None:
        """D-M3 SPLIT: the COUNT-ASSERT half is DELETED (``TestNoGovernedTable…``'s
        P2-m asserts the inverse ∀ — no ASSERT on any emitted ``message`` field but
        the exempted ``grade``); the ``DEFAULT []`` half is KEPT — a ref-less send
        must still omit the field, and a DEFAULT is not a violation source
        (store-ref §1.4)."""
        statement = self._field(generate_message_ddl(), _schema().MESSAGE_TABLE, "refs")
        assert "DEFAULT []" in statement, (
            f"the `refs` DEFAULT [] is GONE — a ref-less send must still be able to omit the "
            f"field (a spec row that keeps its type must keep its DEFAULT): {statement!r}"
        )
        assert "ASSERT" not in statement, (
            f"`refs` still carries a store ASSERT — 63b-ii-b §12.3 DROPS the count bound: the "
            f"app cap `_reject_oversize_pointers` is the ONE implementation, and a store ASSERT "
            f"on this UPDATE-able table is DD-3.c (a legacy over-count row refuses the whole 65 "
            f"cutover migrate). served: {statement!r}"
        )

    def test_the_ELEMENT_row_stays_OVERWRITE_and_carries_no_assert(self) -> None:
        """D-M4 SPLIT: the per-entry ASSERT half is DELETED (``TestNoGovernedTable…``'s
        P2-m asserts the inverse ∀); the ``OVERWRITE`` half is KEPT and gains a
        SECOND reason.

        Reason (i), unchanged: ``TYPE array<T>`` IMPLICITLY defines ``<field>.*``,
        so the element definition is ALWAYS a re-definition — a bare ``DEFINE``
        raises *"The field 'refs.*' already exists"* and takes the whole apply down.
        Reason (ii), NEW (§12.3 refs[*] row): the stored ``refs[*]`` definition on
        the long-lived store CARRIES the ASSERT today; only an emitted ``OVERWRITE
        refs[*] … TYPE string`` with no clause DROPS it (store-ref §1.2). Deleting
        the spec ROW would leave that ASSERT in the store FOREVER (#107 from the
        other side) — Leg A (``TestTheMessageAssertsAreDroppedFromADIRTYStore``) is
        this pin's live twin.
        """
        statement = self._field(generate_message_ddl(), _schema().MESSAGE_TABLE, "refs[*]")
        assert statement.startswith("DEFINE FIELD OVERWRITE refs[*] "), (
            f"the element row is not OVERWRITE. `TYPE array<T>` implicitly defines `<field>.*`, "
            f"so this is always a RE-definition: a bare DEFINE raises 'The field refs.* already "
            f"exists' (reason i), AND only an OVERWRITE re-lands the clause-free definition that "
            f"drops the stored ASSERT on :18500 (reason ii): {statement!r}"
        )
        assert "ASSERT" not in statement, (
            f"`refs[*]` still carries a store ASSERT — §12.3 DROPS the per-entry length bound "
            f"(kept only as the app cap `_reject_oversize_pointers`); the ROW stays (reasons "
            f"i/ii above) but its constraint becomes `\"\"`: {statement!r}"
        )

    # D-M5 (63b-ii-b §12.5): ``test_the_pointer_LABELS_carry_bare_length_asserts``
    # [thread, task_id] DELETED-WITH-REPLACEMENT — both halves are moot with no
    # ASSERT, and P2-m covers the inverse ∀. The NONE-guard lesson (an option<>
    # ASSERT is not evaluated on NONE) survives in ``_reject_oversize_pointers``'s
    # ``value is not None`` leg, pinned by the app-cap positive control.
    #
    # D3 / W3 (§5 / §12.3): ``test_the_ack_note_carries_the_BODY_cap_not_the_pointer_cap``
    # DELETED-WITH-REPLACEMENT — it certifies the corpse (the emitted ``to`` statement
    # CONTAINS the ASSERT that §3 DROPS). Replaced by P2 (∀ fields of ``to`` carry no
    # constraint) in ``TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate``.


class TestThreadIsREQUIREDAndNonOptional:
    """DD-2.b — the SILENT dependency of ``awaiting_answer``'s bounded read.

    That read was narrowed to ``WHERE … in.thread IN $threads AND in.seq > $min``
    and documented as a semantics-identical SUPERSET. It is one **only because
    every message HAS a thread**: SurrealQL's ``IN`` does not match a stored NONE,
    so an ``option<string>`` thread would make answers on a thread-less message
    invisible to the derivation, and the asker would read "waiting" forever.

    That is the SAFE direction of error, which is exactly why it needs a pin
    rather than a comment — nothing would ever fail loudly, the superset claim
    would quietly become false, and the only symptom is an agent that never stops
    waiting. Mutation: flip the spec entry to ``option<string>`` -> RED here.
    """

    def test_the_thread_spec_is_a_required_string(self) -> None:
        specs = dict(
            (name, type_expr) for name, type_expr, _constraint in _schema()._MESSAGE_FIELD_SPECS
        )
        assert "thread" in specs, "the message slice no longer declares `thread` at all"
        assert specs["thread"] == "string", (
            f"message.thread is declared {specs['thread']!r}. `awaiting_answer`'s bounded "
            f"deliveries read is a semantics-identical superset ONLY while every message has a "
            f"thread — an option<> thread is silently dropped by the IN clause and the asker "
            f"waits forever, with nothing failing loudly to say so (DD-2.b)"
        )

    def test_the_EMITTED_ddl_declares_thread_non_optional(self) -> None:
        """Belt and braces at the layer that actually ships: the spec tuple is
        the source, the emitted statement is what the engine sees."""
        statements = [line.strip() for line in generate_message_ddl().split(";\n")]
        thread = [
            text
            for text in statements
            if text.startswith(f"DEFINE FIELD OVERWRITE thread ON {_schema().MESSAGE_TABLE} ")
        ]
        assert len(thread) == 1, f"expected exactly one thread field statement: {thread!r}"
        assert " TYPE string" in thread[0], thread[0]
        assert "option" not in thread[0], (
            f"the emitted thread definition is optional: {thread[0]!r}"
        )


def _overwrite_field_statements(ddl: str, table: str) -> dict[str, str]:
    """Every ``DEFINE FIELD OVERWRITE <f> ON <table> …`` statement, keyed by field.

    Keyword-agnostic on the FIELD token (via :data:`_DEFINE_FIELD_RE`, so ``refs[*]``
    resolves) but REQUIRES the ``OVERWRITE`` guard — the house emitter uses it for
    every field, and a regression to ``IF NOT EXISTS`` is a different pin's subject
    (``_field_statement``). Used by the ∀ constraint pins below to DERIVE the field
    set from the emitted DDL (INSTRUMENT 0: the reach is the emitter's own output,
    not a hand list), so a field added later is covered with no edit.
    """
    fields: dict[str, str] = {}
    for statement in _statements(ddl):
        if not statement.startswith("DEFINE FIELD OVERWRITE "):
            continue
        match = _DEFINE_FIELD_RE.match(statement)
        if match and match.group("table") == table:
            fields[match.group("field")] = statement
    return fields


# The per-table constraint spec the ∀ pin below is parametrized over — ONE pin, not
# two clones (P2 for ``to``, P2-m for ``message``; §12.4 / §13.3 RECOMMENDED shape).
# Each entry: (table-accessor, birth set, birth-DEFAULT set, reader-aligned ASSERT
# exemptions, non-vacuity floor). The birth set is the fields present at the table's
# BIRTH (always populated on every legacy row, so a constraint on them is not a
# poison source); every field OUTSIDE it was added post-birth and MUST be option<>.
# The exemptions are reader-aligned ASSERTs kept DELIBERATELY (§13.1): a field whose
# store-violation set == its reader-rejection set (only ``grade`` today) — a JUDGEMENT,
# so it is a hand constant, kept honest by the non-vacuity leg (an exempted field MUST
# carry an ASSERT) + P-G2 (the ASSERT must equal the reader's set).
class _ConstraintSpec:
    """A governed table's ∀-no-constraint spec (§3.4 P2 / §12.4 P2-m / §13.3 / 63c-i-a §4.3).

    ⚠ 63c-i-a §4.3 STRUCTURAL EXTENSION: the spec gained ``make_ddl`` — the per-table REAL emitter.
    ``to``/``message`` share ``generate_message_ddl`` (``to`` is a RELATION defined in the message
    DDL); ``agent`` supplies ``generate_agent_ddl``. Before this, the ∀ pin HARD-CODED
    ``generate_message_ddl()``, so a third table's fields could not be derived over its OWN emitter
    (INSTRUMENT-0: the reach must be each table's own output, never a hand-copied statement list).

    ⚠ r2 (amendment-2 §D item 11 / sidecar F1 + F10, adversary R4): ``make_ddl`` and the new ``hazard``
    carry NO DEFAULT (CLAUDE.md: a fixture factory must not default a parameter the code branches
    on — the r1 ``make_ddl=generate_message_ddl`` default meant a forgotten emitter silently derived
    over the MESSAGE DDL). ``hazard`` is the per-table prose slot the ∀-no-ASSERT failure message
    interpolates: WHICH writer re-validates the row (the UPDATE-hot mechanism), WHICH writer is the
    ONE implementation of the dropped rule, and WHERE the dirty-store pin lives. r1 served the
    MESSAGE prose (``drain stamps to…``, ``MessageLedger``) for EVERY table — a builder re-adding an
    agent ASSERT was sent to the wrong writer and the wrong pin (the rider §4.3 named and r1 dropped)."""

    def __init__(
        self,
        table_attr: str,
        *,
        birth: frozenset[str],
        birth_defaults: frozenset[str],
        exemptions: frozenset[str],
        floor: frozenset[str],
        make_ddl: Callable[[], str],
        hazard: str,
    ) -> None:
        self.table_attr = table_attr
        self.birth = birth
        self.birth_defaults = birth_defaults
        self.exemptions = exemptions
        self.floor = floor
        self.make_ddl = make_ddl
        self.hazard = hazard


_TO_CONSTRAINT_SPEC = _ConstraintSpec(
    "TO_RELATION",
    make_ddl=generate_message_ddl,  # ``to`` is a RELATION defined in the message DDL.
    hazard=(
        "`to` is UPDATE-hot: `drain` stamps the delivery edges in ONE statement over the window, so a "
        "legacy edge violating this ASSERT refuses the WHOLE drain (total inbox denial). The app cap in "
        "`MessageLedger.ack` is the ONE implementation; the dirty-store pin is "
        "test_comms_schema.py::TestALegacyOverCapNoteCannotDenyADrain (63b-ii-b §3.4)"
    ),
    # birth (df59f76 birth of ``to``): every field populated at RELATE time.
    birth=frozenset({"session", "created_at", "seen_at", "acked_at", "ack_note"}),
    birth_defaults=frozenset(),  # ``to`` carries NO DEFAULT (a seen_at DEFAULT would
    # make every edge look stamped — the spec's own comment / design ruling 4).
    exemptions=frozenset(),  # ``to`` has NO reader-aligned constraint — ack_note is
    # ``str | None`` on the reader (§13.1's own worked example: not reader-aligned).
    floor=frozenset({"ack_note"}),  # the field DD-3.c is about — a derivation that
    # loses it must RED, not pass.
)
_MESSAGE_CONSTRAINT_SPEC = _ConstraintSpec(
    "MESSAGE_TABLE",
    make_ddl=generate_message_ddl,
    hazard=(
        "`message` is UPDATE-able whole-window: the §4.C cutover migrate re-validates every legacy "
        "`message` row in ONE statement, so a legacy violator refuses the whole 65 cutover. The app cap "
        "in `MessageLedger.send` is the ONE implementation; the dirty-store pin is "
        "test_comms_schema.py::TestTheMessageAssertsAreDroppedFromADIRTYStore (63b-ii-b §12.4)"
    ),
    # birth = df59f76 fields + the 1a6010f ``refs[*]`` element row. Written at birth,
    # populated on every legacy row.
    birth=frozenset(
        {
            "seq",
            "session",
            "thread",
            "sender",
            "grade",
            "body",
            "refs",
            "refs[*]",
            "task_id",
            "question",
            "created_at",
        }
    ),
    birth_defaults=frozenset({"refs", "question"}),  # a post-birth DEFAULT falsely
    # promises to rescue legacy rows (store-ref §1.4: it does not).
    exemptions=frozenset({"grade"}),  # R19 (§13.1): grade's violation set == the
    # reader's Literal-decode rejection set → reader-aligned, kept deliberately.
    floor=frozenset({"body", "refs[*]", "owner_principal"}),  # a derivation that
    # misses the element row or the governed overlay must RED.
)
_AGENT_CONSTRAINT_SPEC = _ConstraintSpec(
    "AGENT_TABLE",
    make_ddl=generate_agent_ddl,  # 63c-i-a §4.3 — derive over agent's OWN emitter, not message's.
    hazard=(
        "`agent` is UPDATE-hot per agent (`AgentRegistry.touch` — every heartbeat — re-validates the "
        "WHOLE row) and UPDATE-able whole-window (the `migrate-governed --table agent` cutover backfill "
        "re-validates every legacy agent in ONE statement), so a legacy agent violating this ASSERT can "
        "never heartbeat again and refuses the whole cutover. The identity rules live in "
        "`AgentRegistry.register` (the ONE implementation — `lorerunes.is_legal_identifier` / "
        "`lorerunes.is_blank`); the dirty-store pins are test_agent_governance_63c_i_a.py "
        "(Leg A / Leg B / the heartbeat leg, 63c ruling §4.4)"
    ),
    # birth = the PKT-28 C1 birth field set, GIT-DERIVED (`git log -S _AGENT_FIELD_SPECS` →
    # cfb36d2, the birth commit; the fields present on every legacy agent row), NOT the ruling's
    # candidate table (INSTRUMENT-0: derive from history, do not trust a prose list).
    birth=frozenset(
        {
            "name",
            "session",
            "role",
            "model",
            "status",
            "spawned_by",
            "task_id",
            "checkpoint",
            "last_note",
            "registered_at",
            "heartbeat_at",
        }
    ),
    birth_defaults=frozenset(),  # agent carries NO birth DEFAULT (a status DEFAULT would make a
    # never-touched row look declared; birth stamps status='active' explicitly at register).
    exemptions=frozenset({"status"}),  # §4.2 KEEP: status' store-violation set == the reader's
    # AgentStatus-Literal decode rejection set (a junk status RAISES in _row_to_agent → total roster
    # denial), so it is reader-aligned and KEPT — the ONLY agent ASSERT that survives Q3.
    floor=frozenset({"name", "status", "owner_principal", "scope"}),  # a derivation that loses a
    # birth identity column, the KEPT status, or the governed overlay must RED (non-vacuity).
)


def _constraint_violation_message(
    spec: _ConstraintSpec, table: str, field: str, statement: str
) -> str:
    """The ∀-no-ASSERT RED for ``table.field`` — ONE template, the table's OWN ``hazard`` prose
    interpolated (r2 / sidecar F1: never another table's writer, never a second copy of the text)."""
    return (
        f"`{table}.{field}` carries a store ASSERT — DD-3.c: {spec.hazard}. A legacy row violating "
        f"this ASSERT refuses the WHOLE statement that re-validates it. Adding one DELIBERATELY? you "
        f"owe (a) a heal that runs BEFORE the first UPDATE and (b) the dirty-store pin named above "
        f"inverted — then delete this exemption-free rule for the field and say so. served: "
        f"{statement!r}"
    )


def _assert_no_violable_constraint(spec: _ConstraintSpec, ddl: str) -> None:
    """The P2 ∀-no-constraint check over ``ddl`` for ``spec``'s table (the body the parametrized pin
    runs over the REAL emitter; lifted so the served failure MESSAGE is itself pinnable — r2 §D
    item 11's content leg drives it on a synthetic violating DDL)."""
    table = getattr(_schema(), spec.table_attr)
    # 63c-i-a §4.3: derive over the SPEC's OWN emitter (agent → generate_agent_ddl), never the
    # hard-coded message emitter — a third table's fields must come from its own output.
    fields = _overwrite_field_statements(ddl, table)
    assert fields, (
        f"derived NO emitted `DEFINE FIELD OVERWRITE … ON {table}` statements — a "
        f"derivation that finds nothing MUST red, not pass (INSTRUMENT-0 non-vacuity)"
    )
    assert spec.floor <= set(fields), (
        f"the derived {table} field set {sorted(fields)} is missing the non-vacuity floor "
        f"{sorted(spec.floor)} — the emitter or the parser regressed; a vacuous ∀ pin "
        f"passes for a fixture reason (INSTRUMENT-0)"
    )
    # exemption non-vacuity: a reader-aligned exemption over a field with NO ASSERT
    # is a STALE exemption (the ASSERT it excuses is gone) — RED.
    for exempt in spec.exemptions:
        assert exempt in fields, (
            f"the exemption set names `{exempt}`, which the emitter does not declare on "
            f"{table} — a stale exemption"
        )
        assert "ASSERT" in fields[exempt], (
            f"`{table}.{exempt}` is EXEMPT from the no-ASSERT rule (reader-aligned, §13.1) "
            f"but carries NO ASSERT — a stale exemption. Either the reader-aligned guard "
            f"was dropped (R19 regression: `grade` must keep it) or the exemption is dead. "
            f"served: {fields[exempt]!r}"
        )
    for field, statement in sorted(fields.items()):
        has_assert = "ASSERT" in statement
        if field in spec.exemptions:
            continue  # its ASSERT is required, checked above (non-vacuity).
        assert not has_assert, _constraint_violation_message(spec, table, field, statement)
        if "DEFAULT" in statement:
            assert field in spec.birth_defaults, (
                f"`{table}.{field}` carries a DEFAULT but is not in the birth-DEFAULT set "
                f"{sorted(spec.birth_defaults)} — a POST-BIRTH DEFAULT falsely promises to "
                f"rescue legacy rows (store-ref §1.4: a DEFAULT applies at CREATE, never to "
                f"an existing row's missing value): {statement!r}"
            )
        if field not in spec.birth:
            type_part = statement.split(" TYPE ", 1)[1]
            assert type_part.startswith("option<"), (
                f"`{table}.{field}` was added AFTER the table's birth but is not "
                f"`option<>` — a required post-birth field on a POPULATED table poisons "
                f"every legacy row's next UPDATE (store-ref §1.4). served: {statement!r}"
            )


class TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate:
    """P2 (``to``, §3.4) ∪ P2-m (``message``, §12.4/§13.3) — ONE parametrized pin.

    THE INVARIANT (the quantifier law): a governed, UPDATE-hot/-able table carries
    **no constraint a legacy row can violate**, stated ∀ EMITTED fields, not the one
    field the ruling was derived on. ``to`` is UPDATE-hot (``drain`` stamps it in one
    statement over the window → a legacy over-cap ``ack_note`` edge denies the WHOLE
    drain: total inbox denial). ``message`` is UPDATE-able (the §4.C cutover migrate
    re-validates every legacy row in one statement → a legacy violator refuses the
    whole 65 cutover). Either way a store constraint is a loaded gun; the app cap in
    the ONE writer (``MessageLedger.send``/``.ack``) is the ONE implementation.

    Per field, ∀: no ``ASSERT`` (except the reader-aligned EXEMPTION set — ``grade``
    only, R19); ``DEFAULT`` only on the birth-DEFAULT set (a post-birth DEFAULT does
    NOT rescue legacy rows, store-ref §1.4); every POST-BIRTH field is ``option<>``
    (a required post-birth field poisons every legacy row's next UPDATE).

    This is a FIX pin at HEAD (HEAD emits the length/ack_note ASSERTs → RED) that
    becomes the INVARIANT guard after the builder's W1/W9 drop (GREEN, RED the day a
    constraint returns). Its failure message carries the DD-3.c bound and the widen/
    heal/narrow obligation.

    Mutation proof (declared, from ``--collect-only``): re-add ANY dropped ASSERT to
    ``_TO_FIELD_SPECS``/``_MESSAGE_FIELD_SPECS``/``_AGENT_FIELD_SPECS`` → RED for that
    table; add a spec row ``("x", "string", "")`` → RED (non-option post-birth); add
    ``("y", "option<string>", "DEFAULT 'z'")`` → RED (post-birth DEFAULT); drop
    ``grade``'s / ``status``'s ASSERT → the message / agent exemption non-vacuity leg RED;
    restore → GREEN.

    ⚠ 63c-i-a: the ``[agent]`` row is a FIX pin RED before the i-a build — HEAD emits the
    ``name``/``session`` charset ASSERTs + the ``role`` non-empty ASSERT (Q3 DROPs all three,
    MOVEing them into ``AgentRegistry.register``) AND lacks ``owner_agent``/``scope`` (the floor's
    ``scope`` is absent → the non-vacuity floor reds before the ∀ check even runs). After the build:
    GREEN, RED the day an agent constraint returns or the governed overlay regresses. ``status`` is
    the ONE exempted (KEPT) agent ASSERT — its non-vacuity leg is the KEEP guard.
    """

    @pytest.mark.parametrize(
        "spec",
        [
            pytest.param(_TO_CONSTRAINT_SPEC, id="to"),
            pytest.param(_MESSAGE_CONSTRAINT_SPEC, id="message"),
            pytest.param(_AGENT_CONSTRAINT_SPEC, id="agent"),
        ],
    )
    def test_no_field_carries_a_constraint_a_legacy_row_can_violate(
        self, spec: _ConstraintSpec
    ) -> None:
        _assert_no_violable_constraint(spec, spec.make_ddl())


# (spec, the field the synthetic DDL violates, tokens the served RED MUST carry, tokens it must NOT)
_HAZARD_CONTENT_CASES: tuple[tuple[_ConstraintSpec, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        _AGENT_CONSTRAINT_SPEC,
        "role",
        (
            "AgentRegistry.register",
            "AgentRegistry.touch",
            "heartbeat",
            "migrate-governed --table agent",
            "test_agent_governance_63c_i_a.py",
        ),
        ("MessageLedger", "drain"),
    ),
    (
        _TO_CONSTRAINT_SPEC,
        "ack_note",
        ("drain", "MessageLedger.ack", "TestALegacyOverCapNoteCannotDenyADrain"),
        ("AgentRegistry", "heartbeat"),
    ),
    (
        _MESSAGE_CONSTRAINT_SPEC,
        "body",
        ("MessageLedger.send", "cutover", "TestTheMessageAssertsAreDroppedFromADIRTYStore"),
        ("AgentRegistry", "heartbeat"),
    ),
)


def _synthetic_violating_ddl(spec: _ConstraintSpec, violating_field: str) -> str:
    """A minimal DDL for ``spec``'s table that passes every OTHER leg of the ∀ check (floor present,
    exemptions ASSERTed, post-birth fields ``option<>``) and puts ONE store ASSERT on
    ``violating_field`` — so the ONLY RED the check can raise is the served ∀-no-ASSERT message."""
    table = getattr(_schema(), spec.table_attr)
    statements = []
    for field in sorted(spec.floor | spec.exemptions | {violating_field}):
        type_expr = "string" if field in spec.birth else "option<string>"
        clause = ""
        if field in spec.exemptions:
            clause = " ASSERT $value != 'exempt-probe'"
        if field == violating_field:
            clause = " ASSERT string::len($value) < 10"
        statements.append(f"DEFINE FIELD OVERWRITE {field} ON {table} TYPE {type_expr}{clause}")
    return ";\n".join(statements) + ";"


class TestTheConstraintREDNamesTheTablesOwnWriter63cIA:
    """r2 (amendment-2 §D item 11 / sidecar F1 — THE RIDER §4.3 named and r1 dropped): the P2 ∀ RED is
    the text a builder who re-adds a constraint reads FIRST, so it must name THAT table's writer, its
    UPDATE-hot mechanism and its dirty-store pin — never another table's. Drives the SAME check the
    parametrized pin runs (``_assert_no_violable_constraint``) over a synthetic DDL whose ONLY defect
    is one store ASSERT, and pins the SERVED message's content. GREEN before AND after the i-a build
    (prose-only; independent of the emitter). Mutation proof: swap the ``to`` and ``agent`` hazard
    strings → the ``[agent]`` AND ``[to]`` legs RED (each names the other table's writer)."""

    @pytest.mark.parametrize(
        ("spec", "violating_field", "required", "forbidden"),
        [pytest.param(*case, id=case[0].table_attr) for case in _HAZARD_CONTENT_CASES],
    )
    def test_the_served_red_names_this_tables_writer_and_pin(
        self,
        spec: _ConstraintSpec,
        violating_field: str,
        required: tuple[str, ...],
        forbidden: tuple[str, ...],
    ) -> None:
        with pytest.raises(AssertionError) as exc_info:
            _assert_no_violable_constraint(spec, _synthetic_violating_ddl(spec, violating_field))
        served = str(exc_info.value)
        table = getattr(_schema(), spec.table_attr)
        assert f"`{table}.{violating_field}` carries a store ASSERT" in served, (
            f"the synthetic DDL's ONLY defect is a store ASSERT on {table}.{violating_field}, but the "
            f"check raised a DIFFERENT red (the fixture did not isolate the ∀-no-ASSERT leg): {served!r}"
        )
        missing = [token for token in required if token not in served]
        assert not missing, (
            f"the {table} ∀-no-ASSERT RED does not name {missing} — a builder who re-adds a {table} "
            f"constraint must be told THIS table's writer, UPDATE-hot mechanism and dirty-store pin "
            f"(ruling §4.3 rider; sidecar F1). served: {served!r}"
        )
        leaked = [token for token in forbidden if token in served]
        assert not leaked, (
            f"the {table} ∀-no-ASSERT RED names ANOTHER table's writer/mechanism {leaked} — the r1 "
            f"message served message-only prose for every table (sidecar F1). served: {served!r}"
        )


class TestMessageSchemaLive:
    """Live behavioural pins against the real engine (spike-surreal :18000)."""

    async def test_the_slice_applies_and_creates_every_object(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_message_ddl())
        info = await run(connection, "INFO FOR DB")
        assert {_schema().MESSAGE_TABLE, _schema().TO_RELATION} <= set(info.get("tables", {}))
        assert _schema().MESSAGE_SEQUENCE_NAME in set(info.get("sequences", {}))

    async def test_both_message_hot_path_indexes_actually_LAND_on_the_engine(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """E-S6 (packet 03b): the two R3(1) indexes exist ON THE ENGINE, not just
        in the emitted string.

        WHY a live leg and not only the offline pins: applying this slice sends a
        MULTI-statement query, and the SDK inspects only the FIRST statement's
        status (store reference §6.5) — so a later ``DEFINE INDEX`` the engine
        REJECTS is swallowed, and the sibling apply pin above still passes because
        its subject (the tables) was created by an earlier statement. Pinning the
        source proves the recipe; only the running engine proves the cake.

        Also the one place the (seq) INDEX and the ``message_seq`` SEQUENCE are
        proven to coexist: R3 gives both objects the SAME name. Probed
        2026-07-24 on 3.2.1 in both definition orders — accepted, coexisting, and
        idempotent on re-apply — but a name shared across two object kinds is
        exactly the kind of fact an engine upgrade can revoke, so it is pinned
        rather than remembered.
        """
        connection, _env = admin_db
        table = _schema().MESSAGE_TABLE
        await run(connection, generate_agent_ddl())
        await run(connection, generate_message_ddl())
        info = await run(connection, f"INFO FOR TABLE {table}")
        declared = set(info.get("indexes", {}))
        # POSITIVE CONTROL: the introspection sees the edge indexes that already
        # ship, so a missing name below is a real absence and not a blind read.
        edge_info = await run(connection, f"INFO FOR TABLE {_schema().TO_RELATION}")
        assert {f"{_schema().TO_RELATION}_in_out"} <= set(edge_info.get("indexes", {})), (
            f"the index introspection cannot see the committed edge indexes "
            f"({sorted(edge_info.get('indexes', {}))!r}) — it proves nothing below."
        )
        assert {f"{table}_seq", f"{table}_sender_question"} <= declared, (
            f"the message hot-path indexes are missing from the LIVE table; declared: "
            f"{sorted(declared)!r}. An index the engine rejected is silently swallowed by "
            f"a multi-statement apply, so the offline string pins alone cannot see this."
        )
        # The sequence of the same name is a DIFFERENT object kind and must survive
        # alongside the index (both orders probed; this is the pinned half).
        db_info = await run(connection, "INFO FOR DB")
        assert _schema().MESSAGE_SEQUENCE_NAME in set(db_info.get("sequences", {})), (
            f"the `{_schema().MESSAGE_SEQUENCE_NAME}` SEQUENCE did not survive alongside the "
            f"index of the same name — every message id and delivery edge depends on it."
        )

    async def test_the_slice_is_idempotent(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """Probe 3 leg D's catastrophic case, pinned: re-applying the slice must
        neither raise nor RESET the counter. A re-issued number would silently
        collide every message id and delivery edge in a long-lived store.
        """
        connection, _env = admin_db
        ddl = generate_message_ddl()
        await run(connection, generate_agent_ddl())
        await run(connection, ddl)
        first = await run(connection, f'RETURN sequence::nextval("{_schema().MESSAGE_SEQUENCE_NAME}")')
        await run(connection, ddl)
        second = await run(connection, f'RETURN sequence::nextval("{_schema().MESSAGE_SEQUENCE_NAME}")')
        assert int(second) > int(first), (
            f"re-applying the slice rewound the sequence ({first} -> {second})"
        )

    async def test_the_typed_relation_rejects_a_wrong_TABLE_endpoint(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """Probe 5d: ``TYPE RELATION IN message OUT agent`` DOES reject a
        wrong-table endpoint by field coercion — the only endpoint validation
        the engine offers, and the reason ``TYPE ANY`` (what an undeclared edge
        table auto-creates as) is not acceptable.
        """
        connection, env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_message_ddl())
        message_id = await _create_message(connection, session="wave7", seq=1)
        # ⚠ RESIDUAL 7.4 (adversary): this endpoint must be an EXISTING record of
        # the WRONG table. A NONEXISTENT one is rejected by ``ENFORCED`` before
        # endpoint TYPING is ever consulted — so the test would pass for a
        # neighbouring reason and silently stop testing its own subject.
        brief_id = _brief_record_id("project", 1)
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        with pytest.raises(Exception):  # noqa: B017 - engine coercion error surface
            await run(
                connection,
                f"RELATE $from->{_schema().TO_RELATION}->$to SET session = $edge_session, created_at = $at",
                {
                    "from": RecordID(_schema().MESSAGE_TABLE, message_id),
                    "to": RecordID(BRIEF_TABLE, brief_id),
                    "edge_session": "wave7",
                    "at": datetime.now(UTC),
                },
            )
        assert env is not None

    async def test_a_duplicate_recipient_edge_is_a_LOUD_error(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """Probe 2's positive control, in-suite: the UNIQUE index genuinely
        enforces, which is what makes "dedupe before the RELATE loop" a
        requirement rather than a preference — and what makes the ledger's own
        dedupe pin meaningful.
        """
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_message_ddl())
        agent_id = _agent_record_id("wave7", "fixer-b")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        message_id = await _create_message(connection, session="wave7", seq=2)
        await _relate_to(connection, message_id=message_id, agent_id=agent_id)
        with pytest.raises(Exception):  # noqa: B017 - UNIQUE index violation surface
            await _relate_to(connection, message_id=message_id, agent_id=agent_id)

    async def test_a_DIFFERENT_recipient_on_the_same_message_is_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """The NEGATIVE control for the pin above — an over-broad index (say,
        UNIQUE on ``in`` alone) would pass the duplicate test while breaking
        every multi-recipient send.
        """
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_message_ddl())
        message_id = await _create_message(connection, session="wave7", seq=3)
        for name in ("fixer-b", "audit-c"):
            agent_id = _agent_record_id("wave7", name)
            await _create_agent(connection, agent_id=agent_id, name=name, session="wave7")
            await _relate_to(connection, message_id=message_id, agent_id=agent_id)
        rows = await run(connection, f"SELECT count() FROM {_schema().TO_RELATION} GROUP ALL")
        assert _one(rows)["count"] == 2

    async def test_an_out_of_domain_grade_is_rejected_by_the_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """KEPT (63b-ii-b §13.3 D-M6, re-dated 2026-09-11): now certifies R19 — the
        grade ASSERT is the SOLE store constraint that SURVIVES the DD-3.c drop,
        because a junk grade is a row the reader (``InboxEntry.grade: MessageGrade``,
        a ``Literal``) could never decode. This live rejection is that guard's cake
        (the offline P-G2 pin proves the recipe / the one-source alignment). The
        four LENGTH live rejections in this class DELETE-with-replacement (D-M6) —
        their bounds move to the app cap, and Leg A asserts the inverse (dropped)
        live property. ``test_both_legal_grades_are_accepted`` stays as this pin's
        positive control (an over-strict ASSERT would pass here while breaking every
        real send)."""
        connection, _env = admin_db
        await run(connection, generate_message_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_message(connection, session="wave7", seq=4, grade="urgent")

    @pytest.mark.parametrize("grade", ["signal", "directive"])
    async def test_both_legal_grades_are_accepted(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        grade: str,
    ) -> None:
        """POSITIVE CONTROL: an over-strict ASSERT would pass the rejection test
        above while breaking every real send.
        """
        connection, _env = admin_db
        await run(connection, generate_message_ddl())
        await _create_message(connection, session="wave7", seq=5, grade=grade)

    # --- D-M6 (63b-ii-b §12.5 / §13.3): the FOUR length live rejections DELETED --
    #
    # ``test_an_oversize_body_is_rejected_by_the_store_backstop``,
    # ``test_an_oversize_REF_ENTRY_is_rejected_by_the_store_backstop``,
    # ``test_an_over_COUNT_refs_list_is_rejected_by_the_store_backstop`` and
    # ``test_an_oversize_pointer_LABEL_is_rejected_by_the_store_backstop``[thread,
    # task_id] all certified the CORPSE (the store rejecting a length violator) —
    # the rename-sweep law. §12.3 DROPS all four length ASSERTs; their bounds move
    # to the app cap (``test_message_ledger.py``, D-M2, ∀ error classes) and Leg A
    # (``TestTheMessageAssertsAreDroppedFromADIRTYStore``) asserts the INVERSE live
    # property on a dirty store. Named here so the deletion is visible (the
    # rename-sweep law: "all remaining hits are X" is banned). The GRADE rejection
    # above is KEPT (R19), and the two KEPT positive controls
    # (``test_both_legal_grades_are_accepted`` / the pointer-row one below) stand as
    # Leg A's fixture-liveness controls (a legal row still lands).

    async def test_POSITIVE_CONTROL_a_legal_pointer_row_IS_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """KEPT (D-M6): a legal pointer row still LANDS after the slice applies —
        Leg A's fixture-liveness control (a migrated store that refused everything
        would pass Leg A's "accepted after migrating" assertions for the wrong
        reason). ⚠ Prose re-dated 2026-09-11: the old ``option<>``-NONE-guard claim
        is GONE — §12.3 dropped ``task_id``'s ASSERT, so there is no store ASSERT
        left on ``task_id`` for an omitted value to skip; the NONE-guard lesson now
        lives in ``_reject_oversize_pointers``' ``value is not None`` leg (app cap,
        pinned in ``test_message_ledger.py``)."""
        connection, _env = admin_db
        await run(connection, generate_message_ddl())
        message_id = await _create_message(
            connection,
            session="wave7",
            seq=23,
            refs=["docs/plans/v2/INDEX.md", "r" * _schema().MESSAGE_POINTER_MAX_CHARS],
            thread="q:gate-status",
        )
        assert message_id


async def _create_message(
    connection: SurrealConnection,
    *,
    session: str,
    seq: int,
    grade: str = "signal",
    body: str = "a body",
    sender_id: str | None = None,
    refs: list[str] | None = None,
    thread: str | None = None,
    task_id: str | None = None,
) -> str:
    """CREATE one ``message`` row and return its bare record id.

    ``CONTENT`` (never ``SET session = $session``) — ``session`` is a PROTECTED
    variable name on 3.1.5 (store reference §2).
    """
    message_id = uuid.uuid4().hex
    resolved_sender = sender_id if sender_id is not None else _agent_record_id(session, "lead")
    await run(
        connection,
        f"CREATE type::record('{_schema().MESSAGE_TABLE}', $id) CONTENT $content",
        {
            "id": message_id,
            "content": {
                "seq": seq,
                "session": session,
                "thread": thread if thread is not None else session,
                "sender": RecordID(AGENT_TABLE, resolved_sender),
                "grade": grade,
                "body": body,
                "refs": refs if refs is not None else [],
                "task_id": task_id,
                "created_at": datetime.now(UTC),
            },
        },
    )
    return message_id


async def _relate_to(
    connection: SurrealConnection, *, message_id: str, agent_id: str
) -> Any:
    """RELATE one ``message->to->agent`` delivery edge.

    Endpoints are bound as SDK ``RecordID`` objects — a bare ``str`` is
    rejected LOUDLY (*"Cannot execute RELATE statement where property 'in'
    is..."*) and ``type::record(..)`` in endpoint position is a PARSE ERROR
    (store reference §7).
    """
    return await run(
        connection,
        # ``$session`` is a PROTECTED variable name on 3.1.5 (store reference
        # §2) — binding it is rejected even at a RELATE ``SET``. The COLUMN is
        # still ``session``; only the PARAM must be spelled differently. The
        # production fan-out inherits this constraint verbatim.
        f"RELATE $from->{_schema().TO_RELATION}->$to SET session = $edge_session, created_at = $at",
        {
            "from": RecordID(_schema().MESSAGE_TABLE, message_id),
            "to": RecordID(AGENT_TABLE, agent_id),
            "edge_session": "wave7",
            "at": datetime.now(UTC),
        },
    )


# ===========================================================================
# packet 03 — the RELATION-TABLE POLICY FLIP (operator-ruled 2026-07-19, a
# deliberate scope EXPANSION) and the `ENFORCED` backstop.
#
# `_define_relation_table` today emits `DEFINE TABLE IF NOT EXISTS <n> TYPE
# RELATION SCHEMAFULL` — no `IN`, no `OUT`, no `ENFORCED`, and on the clause
# that cannot migrate. Consequence, measured: EVERY shipped relation table
# (`briefed`, `refers`, `answers_to`) carries NO endpoint typing at all.
#
# ⚠ THE MECHANISM IS THE RISK, NOT THE DATA. The pre-flight audit
# (`REPORT-audit-edge-preflight.md`) read BOTH production databases and all
# 101,479 edge rows: perfectly endpoint-homogeneous, zero would be poisoned,
# zero ghosts. What can still go wrong is the MIGRATION — and a virgin-DB
# fixture cannot see it by construction (§1.6). Hence the dirty-store pin below.
# ===========================================================================


class TestRelationTablePolicyFlip:
    """The helper's own contract, asserted through its three shipped callers.

    Pinned via the GENERATORS rather than by reading the private helper, so a
    build that "fixes" `_define_relation_table` while forgetting to pass the
    endpoint tables at a call site still fails.
    """

    @staticmethod
    def _relation_statement(ddl: str, table: str) -> str:
        matches = [
            statement
            for statement in _statements(ddl)
            if statement.startswith(("DEFINE TABLE OVERWRITE ", "DEFINE TABLE IF NOT EXISTS "))
            and f" {table} " in statement
            and "TYPE RELATION" in statement
        ]
        assert matches, f"no relation DEFINE TABLE found for {table!r}"
        return matches[0]

    def test_briefed_declares_its_endpoint_tables(self) -> None:
        """`briefed` is `agent->briefed->brief`. It has shipped UNTYPED since C1
        — this is the flip reaching an EXISTING table, which is exactly the case
        the migration hazard applies to.
        """
        statement = self._relation_statement(generate_brief_ddl(), BRIEFED_RELATION)
        assert f"TYPE RELATION IN {AGENT_TABLE} OUT {BRIEF_TABLE}" in statement, statement

    def test_briefed_uses_the_overwrite_guard(self) -> None:
        statement = self._relation_statement(generate_brief_ddl(), BRIEFED_RELATION)
        assert statement.startswith("DEFINE TABLE OVERWRITE "), (
            f"a relation table on IF NOT EXISTS can never migrate its clause — the flip "
            f"would return OK and change nothing on every existing store: {statement!r}"
        )

    def test_every_relation_table_in_every_comms_generator_is_typed(self) -> None:
        """The ∀ form. A per-table hand-list is exactly the enumerate-the-known
        instrument the repo's six-defeats table forbids — this quantifies over
        whatever the generators actually emit, so a relation table added
        tomorrow is covered the day it is written.
        """
        for ddl in (
            generate_agent_ddl(),
            generate_brief_ddl(),
            generate_message_ddl(),
            generate_graph_ddl(),  # refers / answers_to — the flip reaches them too
        ):
            for statement in _statements(ddl):
                if "TYPE RELATION" not in statement:
                    continue
                assert re.search(r"TYPE RELATION IN \w+ OUT \w+", statement), (
                    f"an UNTYPED relation table — it accepts an endpoint of ANY table, "
                    f"silently: {statement!r}"
                )
                assert statement.startswith("DEFINE TABLE OVERWRITE "), statement


class TestEnforcedIsLiveOnTheDeliveryEdge:
    """`ENFORCED` validates BOTH endpoints against EXISTING records — the guard
    probe 1 proved the engine otherwise does not offer.

    It is a BACKSTOP, never a replacement for the ledger's own recipient check:
    it reports ONE bad recipient per attempt, as untyped prose, only AFTER the
    write is attempted and the transaction aborted, and it cannot see ghosts
    already stored. Both layers are pinned (ruling 8).
    """

    @staticmethod
    async def _ready(connection: SurrealConnection) -> str:
        await run(connection, generate_agent_ddl())
        await run(connection, generate_message_ddl())
        agent_id = _agent_record_id("wave7", "fixer-b")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        return agent_id

    async def test_CONTROL_a_real_endpoint_pair_is_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """THE POSITIVE CONTROL, first and deliberately: an over-strict guard
        that rejected EVERYTHING would pass every rejection pin below while
        breaking every real send. Probe 1's own first run reported the exact
        opposite of the truth for want of this leg.
        """
        connection, _env = admin_db
        agent_id = await self._ready(connection)
        message_id = await _create_message(connection, session="wave7", seq=1)
        await _relate_to(connection, message_id=message_id, agent_id=agent_id)
        rows = await run(connection, f"SELECT count() FROM {_schema().TO_RELATION} GROUP ALL")
        assert _one(rows)["count"] == 1

    async def test_a_ghost_OUT_endpoint_is_REJECTED(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """`out` is the CALLER-SUPPLIED half of a `message->to->agent` fan-out —
        the dangerous one. Without `ENFORCED` this silently writes a permanent
        delivery receipt for an agent who does not exist.
        """
        connection, _env = admin_db
        await self._ready(connection)
        message_id = await _create_message(connection, session="wave7", seq=2)
        with pytest.raises(Exception):  # noqa: B017 - engine ENFORCED rejection surface
            await _relate_to(connection, message_id=message_id, agent_id="a-ghost-that-never-was")

    async def test_a_ghost_IN_endpoint_is_REJECTED(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        agent_id = await self._ready(connection)
        with pytest.raises(Exception):  # noqa: B017 - engine ENFORCED rejection surface
            await _relate_to(connection, message_id="m-ghost-that-never-was", agent_id=agent_id)

    async def test_no_dangling_edge_survives_a_rejected_relate(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """The OUTCOME property, not just the raise: an exception that still
        left a row would satisfy `pytest.raises` and defeat the whole point.
        """
        connection, _env = admin_db
        await self._ready(connection)
        message_id = await _create_message(connection, session="wave7", seq=3)
        with pytest.raises(Exception):  # noqa: B017 - engine ENFORCED rejection surface
            await _relate_to(connection, message_id=message_id, agent_id="a-ghost-that-never-was")
        rows = await run(connection, f"SELECT count() FROM {_schema().TO_RELATION} GROUP ALL")
        assert rows == [] or _one(rows)["count"] == 0

    async def test_ENFORCED_closes_the_INSERT_RELATION_door(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """The door NO application check can reach (probe UNASKED-1). An app
        guard protects the code path it sits on; `ENFORCED` protects the TABLE,
        including every write path nobody has written yet.

        Measured: `CREATE`/`INSERT INTO`/`UPSERT` are all closed by `TYPE
        RELATION` alone — `INSERT RELATION` is closed by `ENFORCED` and by
        nothing else.
        """
        connection, _env = admin_db
        await self._ready(connection)
        message_id = await _create_message(connection, session="wave7", seq=4)
        with pytest.raises(Exception):  # noqa: B017 - engine ENFORCED rejection surface
            await run(
                connection,
                f"INSERT RELATION INTO {_schema().TO_RELATION} $payload",
                {
                    "payload": {
                        "in": RecordID(_schema().MESSAGE_TABLE, message_id),
                        "out": RecordID(AGENT_TABLE, "a-ghost-that-never-was"),
                        "session": "wave7",
                        "created_at": datetime.now(UTC),
                    }
                },
            )

    async def test_CONTROL_INSERT_RELATION_is_legal_with_real_endpoints(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """Proves the rejection above is the CLAUSE and not the VERB — without
        it, "INSERT RELATION raised" could simply mean the verb is unsupported.
        """
        connection, _env = admin_db
        agent_id = await self._ready(connection)
        message_id = await _create_message(connection, session="wave7", seq=5)
        await run(
            connection,
            f"INSERT RELATION INTO {_schema().TO_RELATION} $payload",
            {
                "payload": {
                    "in": RecordID(_schema().MESSAGE_TABLE, message_id),
                    "out": RecordID(AGENT_TABLE, agent_id),
                    "session": "wave7",
                    "created_at": datetime.now(UTC),
                }
            },
        )
        rows = await run(connection, f"SELECT count() FROM {_schema().TO_RELATION} GROUP ALL")
        assert _one(rows)["count"] == 1


# The SIX violator shapes the ii-b DROP is measured against (§12.6 Leg A / §13.3). FIVE are LENGTH
# bounds that DROP (their rows become ACCEPTED after the current emitter re-lands them clause-free);
# ``grade`` is the reader-aligned domain guard that STAYS (R19 — a junk grade the reader cannot decode).
_MESSAGE_LENGTH_VIOLATOR_SHAPES = ("body", "thread", "refs_count", "refs_entry", "task_id")
_MESSAGE_GRADE_VIOLATOR_SHAPE = "grade"


class TestTheMessageAssertsAreDroppedFromADIRTYStore:
    """P1-m Leg A (63b-ii-b §12.6 / §13.3) — INVERTED from ``TestThePointerBoundsMigrateADIRTYStore``.

    THE #107 DIRECTION: the DROP must LAND on a store that ALREADY carries the ASSERTed definitions
    (production's shape at :18500). A definition that emits perfectly and never LANDS is invisible to
    every offline pin (P2-m); this live leg proves the ``OVERWRITE`` re-lands the CLAUSE-FREE field on
    a DIRTY store. Its twin — the DD-3.c direction (the real migrate SURVIVES legacy violators) — is
    Leg B (``test_message_migrate_dirty_store_63b_ii_b``). Each is blind exactly where the other is
    strong (the trust doctrine's two-leg shape, at test scale).

    §13.3: the FOUR length ASSERTs DROP (five violator SHAPES — body/thread/refs-count/refs-entry/
    task_id — become ACCEPTED, values byte-intact); ``grade='urgent'`` STAYS REJECTED (R19 keeps the
    grade ASSERT). BASELINE (positive control): under the FROZEN asserted DDL every shape is refused —
    without it, "accepted after migrating" could be true because the shape was never refused.

    Mutation proof (declared, from ``--collect-only``): re-add ONE length ASSERT (say ``body``) →
    exactly the ``body`` accept-parametrization RED with the engine's *"must conform to"* text, the
    other four length shapes GREEN, and P2-m RED; restore → GREEN. Per-shape discrimination is what
    the parametrization buys — a build that drops four of five is caught on the fifth, BY NAME.
    """

    @staticmethod
    async def _apply_asserted_old_world(connection: SurrealConnection) -> None:
        """agent DDL + the FROZEN asserted ``message`` DDL — production's shape before the ii-b drop.
        The frozen DDL is the SHARED ``frozen_asserted_message_ddl`` (ONE IMPLEMENTATION: Leg B's
        C-control uses the SAME capture, so the two files cannot drift about production's shape)."""
        await run(connection, generate_agent_ddl())
        await run(connection, frozen_asserted_message_ddl())

    @staticmethod
    def _violator_overrides(shape: str) -> dict[str, Any]:
        """The seed-override for one violator shape (sizes DERIVED from the caps, so they track the
        constant)."""
        pointer = _schema().MESSAGE_POINTER_MAX_CHARS
        body_cap = _schema().MESSAGE_BODY_MAX_CHARS
        refs_cap = _schema().MESSAGE_REFS_MAX_COUNT
        return {
            "body": {"body": "z" * (body_cap + 1)},
            "thread": {"thread": "t" * (pointer + 1)},
            "refs_count": {"refs": [f"r{index}" for index in range(refs_cap + 1)]},
            "refs_entry": {"refs": ["r" * (pointer + 1)]},
            "task_id": {"task_id": "t" * (pointer + 1)},
            "grade": {"grade": "urgent"},
        }[shape]

    @staticmethod
    def _assert_value_byte_intact(row: dict[str, Any], shape: str) -> None:
        """A migration converges the SCHEMA, never the DATA (store-ref §1.4): the over-cap value the
        DROP now admits must survive byte-intact (this ruling adds no heal)."""
        pointer = _schema().MESSAGE_POINTER_MAX_CHARS
        body_cap = _schema().MESSAGE_BODY_MAX_CHARS
        refs_cap = _schema().MESSAGE_REFS_MAX_COUNT
        if shape == "body":
            assert len(row["body"]) == body_cap + 1, row
        elif shape == "thread":
            assert len(row["thread"]) == pointer + 1, row
        elif shape == "refs_count":
            assert len(row["refs"]) == refs_cap + 1, row
        elif shape == "refs_entry":
            assert len(row["refs"][0]) == pointer + 1, row
        elif shape == "task_id":
            assert len(row["task_id"]) == pointer + 1, row
        else:  # pragma: no cover - the parametrization only passes length shapes here
            raise AssertionError(f"no byte-intact check for shape {shape!r}")

    async def test_the_frozen_old_world_is_a_faithful_asserted_capture(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """CONTROL — the FROZEN old world (``frozen_asserted_message_ddl()``, the 0566587 capture) is a
        faithful ASSERTED world: its OWN text carries all four length/grade ASSERT literals. This is the
        control the BASELINE / grade-STAYS / clean-row legs REST ON — if the frozen capture ever lost an
        ASSERT, "refused under the asserted DDL" would be vacuous, and every drop-leg would be measuring
        nothing.

        ⚠ A frozen fact is verified against WHAT IT FROZE (0566587), NEVER against the LIVE emitter.
        The former shape — asserting each literal appears in ``generate_message_ddl()`` — was a C-DEF
        (adversary Finding 1): the ii-b build is DESIGNED to drop three of these four length ASSERTs
        from the emitter (W9 / §13.3), so on the correct build the emitter no longer carries them and
        the pin RED-trapped the builder with every production gate green. Self-consistency of the frozen
        constant is GREEN at HEAD AND after the build (the constant is immutable) — it is the drop's
        BEFORE-picture, not a demand that the emitter keep the asserts (that is Leg A's job)."""
        del admin_db  # offline control (no engine)
        frozen = frozen_asserted_message_ddl()
        for assert_literal in (
            "ASSERT string::len($value) <= 4000",
            "ASSERT string::len($value) <= 256",
            "ASSERT array::len($value) <= 20",
            "ASSERT $value IN ['signal', 'directive']",
        ):
            assert assert_literal in frozen, (
                f"the FROZEN 0566587 asserted old world is MISSING {assert_literal!r} — the capture in "
                f"frozen_asserted_message_ddl() has rotted, so the BASELINE 'refused under the asserted "
                f"DDL' legs it backstops are vacuous. Re-capture the frozen DDL from 0566587."
            )

    @pytest.mark.parametrize("shape", (*_MESSAGE_LENGTH_VIOLATOR_SHAPES, _MESSAGE_GRADE_VIOLATOR_SHAPE))
    async def test_BASELINE_the_asserted_old_world_refuses_every_violator(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        shape: str,
    ) -> None:
        """Positive control: under the FROZEN asserted DDL, EACH of the six violator shapes is REJECTED
        by the engine — without it, "accepted after migrating" could be true because the shape was
        never refused. GREEN at HEAD and after the build (the frozen world is unchanged)."""
        connection, _env = admin_db
        await self._apply_asserted_old_world(connection)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await seed_message_legacy(
                connection, sender_id="lead", session="wave7", seq=1, **self._violator_overrides(shape)
            )

    async def test_CONTROL_a_clean_row_lands_under_the_asserted_old_world(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """Fixture-liveness control (§12.6 step 1): a CLEAN legacy row IS accepted under the asserted
        DDL — proving the table is live and the BASELINE rejections above are the ASSERTs, not a dead
        table refusing everything."""
        connection, _env = admin_db
        await self._apply_asserted_old_world(connection)
        message_id = await seed_message_legacy(
            connection, sender_id="lead", session="wave7", seq=2, body="a clean body"
        )
        assert message_id

    @pytest.mark.parametrize("shape", _MESSAGE_LENGTH_VIOLATOR_SHAPES)
    async def test_the_length_assert_DROPS_and_the_value_survives_byte_intact(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        shape: str,
    ) -> None:
        """⚠ RED at HEAD (the #107 direction) — apply the frozen asserted DDL, then re-apply the
        CURRENT ``generate_message_ddl()``; under the ii-b ruling it re-lands ``{shape}`` CLAUSE-FREE
        (``OVERWRITE`` = full replace, drops the omitted ASSERT — store-ref §1.2), so a formerly-refused
        length violator is now ACCEPTED and its over-cap value survives byte-intact (store-ref §1.4: a
        migration converges schema, never data). At HEAD the emitter STILL emits the length ASSERT →
        the seed RAISES → RED for the right reason (the OVERWRITE did not drop it). An emitter that
        regressed to ``IF NOT EXISTS`` (the #107 no-op) also reds here."""
        connection, _env = admin_db
        await self._apply_asserted_old_world(connection)
        await run(connection, generate_message_ddl())
        try:
            message_id = await seed_message_legacy(
                connection, sender_id="lead", session="wave7", seq=3, **self._violator_overrides(shape)
            )
        except Exception as error:  # noqa: BLE001 - RED-at-HEAD surface (the ASSERT still lands)
            pytest.fail(
                f"RED-at-HEAD (right reason): the {shape!r} length ASSERT is STILL on the store after "
                f"re-applying generate_message_ddl() — the ii-b OVERWRITE drop has not landed on the "
                f"dirty store (§12.6 Leg A / #107 direction). engine: {error}"
            )
        row = _one(
            await run(
                connection,
                f"SELECT body, thread, refs, task_id FROM "
                f"type::record('{_schema().MESSAGE_TABLE}', $id)",
                {"id": message_id},
            )
        )
        self._assert_value_byte_intact(row, shape)

    async def test_the_grade_assert_STAYS_after_migrating_a_dirty_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """R19 (§13.3) — the grade ASSERT is the SOLE store constraint that SURVIVES the drop: a junk
        ``grade`` is a row the reader (``InboxEntry.grade: MessageGrade``) could never decode. After
        re-applying the current emitter, ``grade='urgent'`` is STILL REJECTED. GREEN at HEAD AND after
        the build (grade kept throughout); a build that DROPS grade's ASSERT (the R19 wrong build) reds
        here (the seed would be accepted)."""
        connection, _env = admin_db
        await self._apply_asserted_old_world(connection)
        await run(connection, generate_message_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface (grade domain)
            await seed_message_legacy(
                connection, sender_id="lead", session="wave7", seq=4, grade="urgent"
            )

    async def test_the_migration_is_idempotent_on_an_already_migrated_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """KEPT (§12.6 step 5) — ``ensure_ready`` re-applies the DDL on EVERY boot, so a second apply
        must be a clean no-op; the ``refs[*]`` element row is the one that would RAISE here if it ever
        lost its ``OVERWRITE`` (a bare re-definition of an implicit array element path)."""
        connection, _env = admin_db
        await self._apply_asserted_old_world(connection)
        await run(connection, generate_message_ddl())
        await run(connection, generate_message_ddl())
        message_id = await seed_message_legacy(
            connection, sender_id="lead", session="wave7", seq=5, refs=["docs/plans/v2/INDEX.md"]
        )
        assert message_id


class TestTheSingleWriterFloorPerTable:
    """P3 (63b-ii-b §12.7 / §3.4) — the per-table single-writer FLOOR: exactly ONE production writer
    per governed message write, over the DERIVED production-member reach (INSTRUMENT-0: a new writer in
    ANY member file reds — reach is a CHECKED VARIABLE, not a hand list of files).

    | write | allowlist (EXACT) |
    |---|---|
    | ``to.ack_note`` in a SET/CONTENT | ``{MessageLedger.ack}`` |
    | ``message`` CREATE | ``{MessageLedger._send_fragment}`` |
    | ``message`` UPDATE/UPSERT/INSERT | ``{principals._migrate_message_owner}`` |

    THREAT MODEL (a gate needs one, CLAUDE.md): the HONEST developer who adds a SECOND production writer
    of a governed message column WITHOUT the ledger's app caps — a new CREATE outside ``_send_fragment``,
    or a new UPDATE path inheriting DD-3.c (the day this grows a second entry, §12.4 re-open trigger (i)
    has fired and the author owes the heal + inverted Leg B). NOT a hostile author (``"ack_" + "note"``,
    a table-name variable — #138's shape, ledgered, not paid for in false positives). This is the STATIC
    FLOOR; the ∀ instrument is F5's effect predicate (ii-a), whose reach is the battery's executed
    frames. ⚠ D-M8 (§13.3): the reader-decode invariant is STORE-guarded (grade ASSERT kept, R19), so
    this floor carries NO D-M8 statement — grade is closed at the store, not by this scan.

    The site derivation REUSES ``governed_table_raw_mutation_sites`` (the F5 registration derivation) for
    the table-level CREATE/UPDATE rows rather than a second regex (ONE IMPLEMENTATION); the ``ack_note``
    COLUMN row needs a column-aware scan (a SET/CONTENT literal mentioning ``ack_note``), since the
    table-level ``to`` derivation also carries ``drain``'s ``seen_at`` UPDATE.

    GREEN at HEAD (the writers ARE exactly the allowlist); RED the day a second site lands. Non-vacuity:
    each scan MUST find its known site (a scan that finds nothing is broken)."""

    @staticmethod
    def _production_sources() -> list[str]:
        """Every production-member ``.py`` source — the DERIVED reach (a new writer in ANY member file
        is in scope), NOT a hand list of the three modules the allowlist happens to name today."""
        return [
            path.read_text(encoding="utf-8")
            for root in derive_member_source_roots()
            for path in root.rglob("*.py")
        ]

    @staticmethod
    def _table_verb_writers(
        sources: list[str], table: str, verbs: set[str], *, table_const_hint: str
    ) -> set[str]:
        # ⚠ ``table_const_hint`` is load-bearing: the derivation matches the literal table name OR the
        # interpolated module CONSTANT ``{<hint>}``. The DEFAULT hint is ``MEMORY_TABLE``, so calling it
        # for ``message`` without the correct hint matches every MEMORY writer via ``{MEMORY_TABLE}`` —
        # measured 2026-09-11 (a false-positive that pulled _upsert_fragment/_reinforce into the set).
        writers: set[str] = set()
        for source in sources:
            for site in governed_table_raw_mutation_sites(source, table, table_const_hint=table_const_hint):
                if site.verb in verbs:
                    writers.add(site.function)
        return writers

    @staticmethod
    def _ack_note_set_writers(sources: list[str]) -> set[str]:
        """Enclosing functions whose source contains a mutation literal that WRITES ``ack_note`` (a
        ``SET``/``CONTENT`` clause naming it) — the column-specific floor. A SELECT projection of
        ``ack_note`` (drain's read) carries no ``SET``/``CONTENT`` and is excluded."""
        writers: set[str] = set()
        for source in sources:
            tree = ast.parse(source)
            owner: dict[int, str] = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for child in ast.walk(node):
                        owner[id(child)] = node.name
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Constant, ast.JoinedStr)):
                    continue
                segment = ast.get_source_segment(source, node) or ""
                if "ack_note" in segment and ("SET" in segment or "CONTENT" in segment):
                    function = owner.get(id(node))
                    if function is not None:
                        writers.add(function)
        return writers

    def test_the_message_CREATE_writer_is_exactly_send_fragment(self) -> None:
        writers = self._table_verb_writers(
            self._production_sources(), _schema().MESSAGE_TABLE, {"CREATE"}, table_const_hint="MESSAGE_TABLE"
        )
        assert writers == {"_send_fragment"}, (
            f"the production writers of a raw `message` CREATE are {sorted(writers)}, not exactly "
            f"{{_send_fragment}} — a second CREATE site bypasses the ledger's send caps (P3, §12.7). "
            f"If deliberate, route it through MessageLedger.send or extend the allowlist WITH a reason."
        )

    def test_the_message_UPDATE_writer_is_exactly_migrate_message_owner(self) -> None:
        writers = self._table_verb_writers(
            self._production_sources(),
            _schema().MESSAGE_TABLE,
            {"UPDATE", "UPSERT", "INSERT"},
            table_const_hint="MESSAGE_TABLE",
        )
        assert writers == {"_migrate_message_owner"}, (
            f"the production writers of a raw `message` UPDATE/UPSERT/INSERT are {sorted(writers)}, not "
            f"exactly {{_migrate_message_owner}} — a new `message` UPDATE path inherits DD-3.c (§12.4 "
            f"re-open trigger (i): it owes the heal + inverted Leg B). If deliberate, extend the "
            f"allowlist WITH a reason and the owed instruments."
        )

    def test_the_to_ack_note_writer_is_exactly_ack(self) -> None:
        writers = self._ack_note_set_writers(self._production_sources())
        assert writers == {"ack"}, (
            f"the production writers of `to.ack_note` (a SET/CONTENT naming it) are {sorted(writers)}, "
            f"not exactly {{ack}} — a second writer lands an unbounded/ungoverned note bypassing "
            f"MessageLedger.ack's `_reject_oversize_note` cap (P3, §3.4/§12.7)."
        )


_LEGAL_NOTE = "a legal note"


class TestALegacyOverCapNoteCannotDenyADrain:
    """P1 (63b-ii-b §6 / §5 D4) — INVERTED from ``TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge``.

    THE `to` HALF of DD-3.c, and the half that can actually hurt: ``drain`` UPDATEs `to` on EVERY call
    in ONE statement over the whole window, and SurrealDB re-validates the WHOLE record on write — so a
    single legacy edge carrying an over-cap ``ack_note`` would fail that statement and the agent could
    not drain ANY of its inbox (TOTAL DENIAL, measured — probe 63b-ii-b §3). This pin ASSERTS THE FIX:
    under the ii-b ruling (``to.ack_note`` ASSERT dropped) a dirty over-cap edge is served + stamped,
    and its over-cap value survives byte-intact.

    Driven through the REAL ``MessageLedger.drain`` in the §4.B one-txn shape (ROUTING IS NOT SHARING —
    a hand-typed copy of drain's UPDATE could drift from drain), with the dirty edge VISIBLE to the
    draining Subject (else it is excluded by the read_filter and the pin passes for C4's false-clear
    reason — the assertion in the main pin FORCES visibility: BOTH seqs must be served AND stamped).

    RED at HEAD: the ii-b drain takes NO Subject/read_filter argument (§4.B unbuilt) → the call raises
    TypeError → a legible RED. On the ii-b build the ASSERT is gone and the one-txn drain serves +
    stamps both edges. Mutation proof (declared, from ``--collect-only``): re-add the ASSERT to
    ``_TO_FIELD_SPECS`` → this pin RED with the engine's ``ack_note … must conform to`` text (the
    whole-window UPDATE aborts); restore → GREEN. That is "RED the day the hazard reopens", demonstrated.
    """

    @pytest_asyncio.fixture()
    async def dirty_to_world(self) -> Any:
        """A store carrying REAL governed (server-scope, member-visible) message rows and TWO delivery
        edges to ONE recipient — both ``seen_at`` NONE, one with an over-cap ``ack_note``, one clean —
        written under the DOWNGRADED (unbounded) ``to.ack_note`` world, then the CURRENT emitter
        re-lands the schema (store-ref §1.4 trap: the edges are written UNDER the old definition). The
        message rows are REAL (not a SCHEMALESS stand-in) because the ii-b drain reads them through the
        read_filter. Yields ``(ledger, recipient_bare, subject, connection, env)``. Reaped (NEVER
        :18500)."""
        env = make_env(database=unique_database(), dim=8)
        principal_store, keep_store = await build_principal_and_keep_stores(env)
        connection = await connect_admin(env)
        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user,
            password=env.password,
        )
        ledger = MessageLedger(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user,
            password=env.password,
        )
        try:
            # 1. REAL agent + message + `to` DDL, then DOWNGRADE `to.ack_note` to unbounded (the
            #    "before it was bounded" world) — the edges' over-cap note is written under THIS. The
            #    SHARED capture (ONE IMPLEMENTATION with probe_drain_read_63b_ii_b's dirty-edge seeding).
            await run(connection, generate_agent_ddl())
            await run(connection, generate_message_ddl())
            await run(connection, unbounded_to_ack_note_ddl())
            # 2. one member principal + one recipient agent owned by it (a governed member Subject).
            await principal_store.create(email="recip@example.com", role="member")
            principal = (await principal_store.list())[0]
            principal_bare = bare_record_key(principal.id)
            recipient = (
                await registry.register(
                    "recip",
                    session="wave7",
                    role="builder",
                    owner_principal_id=principal_bare,
                    session_keep_id=await session_keep_id_for(
                        keep_store, principal_store, owner_principal_id=principal_bare, session="wave7"
                    ),  # r2 (A3): the owner travels WITH THE session keep
                )
            ).agent
            recipient_bare = bare_record_key(recipient.id)
            # 3. TWO REAL server-scope messages (member-visible) + 4. their delivery edges, one over-cap
            #    ack_note, one clean, both seen_at NONE — RELATEd under the downgraded (unbounded) note.
            cap = _schema().MESSAGE_BODY_MAX_CHARS
            for seq, note in enumerate((_LEGAL_NOTE, "n" * (cap + 1))):
                message_id = await seed_message_legacy(
                    connection, sender_id=recipient_bare, session="wave7", seq=seq, scope="server"
                )
                await run(
                    connection,
                    f"RELATE $message->{_schema().TO_RELATION}->$agent SET "
                    f"session = 'wave7', created_at = $now, ack_note = $note",
                    {
                        "message": RecordID(_schema().MESSAGE_TABLE, message_id),
                        "agent": RecordID(AGENT_TABLE, recipient_bare),
                        "now": datetime.now(UTC),
                        "note": note,
                    },
                )
            # 5. MIGRATE: re-apply the CURRENT emitter (re-lands `to.ack_note` — asserted at HEAD, so the
            #    over-cap edge is write-poisoned; clause-free after the ii-b build, so it is not).
            await run(connection, generate_message_ddl())
            subject = member(principal_bare, recipient_bare, frozenset())
            yield ledger, recipient_bare, subject, connection, env
        finally:
            await ledger.close()
            await registry.close()
            await connection.close()
            await keep_store.close()
            await principal_store.close()
            await drop_database(env)

    @staticmethod
    async def _drain(ledger: Any, agent_id: str, subject: Any, *, peek: bool = False) -> Any:
        """Call the REAL ii-b ``MessageLedger.drain`` with the Subject/read_filter arg. RED-at-HEAD
        surface: at HEAD ``drain`` has no ``subject`` kwarg → TypeError → a legible ``pytest.fail``
        (the §4.B one-txn read-governance is unbuilt), never a bare crash."""
        try:
            return await ledger.drain(agent_id=agent_id, limit=10, peek=peek, subject=subject)
        except TypeError as error:
            pytest.fail(
                "RED-at-HEAD (right reason): MessageLedger.drain does not accept a `subject` argument — "
                "the ii-b §4.B one-txn read-governance (drain resolves + filters by the Subject) is "
                f"unbuilt. engine/py: {error}"
            )

    def test_the_ack_note_old_worlds_are_faithful_captures(self) -> None:
        """CONTROL — the two HAND-CAPTURED ``to.ack_note`` old worlds are what they claim: the FROZEN
        deployed one (``frozen_asserted_to_ack_note_ddl()``) carries the literal 4000-char ASSERT, and the
        pre-bound one (``unbounded_to_ack_note_ddl()``) carries NO ASSERT. The probe's C0 (the drain must
        ABORT under the deployed bound) and this class's downgraded world (an over-cap edge must be
        WRITABLE) rest on these — a frozen capture that lost its ASSERT makes C0 vacuous; an unbounded
        one that gained one makes the BASELINE seed fail for a fixture reason.

        ⚠ Self-consistency ONLY — NEVER a comparison to the live emitter (see
        ``TestTheMessageAssertsAreDroppedFromADIRTYStore.test_the_frozen_old_world_is_a_faithful_asserted_capture``
        for why: the emitter is DESIGNED to change; the capture is what production FROZE). Both name the
        ``ack_note`` field ON the delivery edge, so neither can silently re-target another table."""
        target = f"DEFINE FIELD OVERWRITE ack_note ON {_schema().TO_RELATION} "
        frozen = frozen_asserted_to_ack_note_ddl()
        assert frozen.startswith(target), f"the frozen capture no longer defines to.ack_note: {frozen!r}"
        assert "ASSERT string::len($value) <= 4000" in frozen, (
            f"the FROZEN deployed to.ack_note capture is MISSING its 4000-char ASSERT — "
            f"frozen_asserted_to_ack_note_ddl() has rotted, so the probe's C0 'drain ABORTS under the "
            f"deployed bound' control is vacuous. Re-capture it from store reference §0a. Got: {frozen!r}"
        )
        unbounded = unbounded_to_ack_note_ddl()
        assert unbounded.startswith(target), (
            f"the unbounded capture no longer defines to.ack_note: {unbounded!r}"
        )
        assert "ASSERT" not in unbounded, (
            f"the PRE-BOUND to.ack_note capture carries an ASSERT — the dirty over-cap edge could not be "
            f"written under it, so the DD-3.c legs would fail at seeding, not at the hazard: {unbounded!r}"
        )

    async def test_BASELINE_the_downgraded_world_accepts_both_edges(
        self, dirty_to_world: Any
    ) -> None:
        """Positive control: the downgraded (unbounded) world accepted BOTH edges (over-cap + clean) —
        without it "served after the fix" could be true because the over-cap edge was never created.
        GREEN throughout (the over-cap edge survives the migrate, write-poisoned but READABLE)."""
        _ledger, recipient_bare, _subject, connection, _env = dirty_to_world
        rows = await run(
            connection,
            f"SELECT count() FROM {_schema().TO_RELATION} WHERE out = $agent GROUP ALL",
            {"agent": RecordID(AGENT_TABLE, recipient_bare)},
        )
        assert _one(rows)["count"] == 2, "the downgraded world was supposed to accept BOTH edges"

    async def test_a_dirty_over_cap_note_edge_is_SERVED_and_STAMPED_not_denied(
        self, dirty_to_world: Any
    ) -> None:
        """⚠ RED at HEAD (via the missing Subject arg) — the load-bearing pin. Drive the REAL ii-b
        drain over the dirty window: it RETURNS (no aborted txn), serves BOTH messages, STAMPS both
        edges (``stamped_seqs`` == both seqs — which forces both VISIBLE and stamped; a dirty edge
        masked by C4 would be missing), the read-back shows both ``seen_at IS NOT NONE``, and the
        over-cap ``ack_note`` value SURVIVES unchanged (a migration converges schema, never data —
        store-ref §1.4). Under a wrong build that keeps/re-adds the ``to.ack_note`` ASSERT the
        whole-window UPDATE aborts and NOTHING is served or stamped (the measured total denial)."""
        ledger, recipient_bare, subject, connection, _env = dirty_to_world
        result = await self._drain(ledger, recipient_bare, subject)
        assert sorted(result.stamped_seqs) == [0, 1], (
            f"the drain did not STAMP both edges — a dirty over-cap ack_note edge denied the whole "
            f"window (DD-3.c), or the dirty edge was invisible (C4 false clear). "
            f"stamped={result.stamped_seqs!r}"
        )
        assert sorted(entry.seq for entry in result.entries) == [0, 1], (
            f"the drain did not SERVE both messages: {[e.seq for e in result.entries]!r}"
        )
        stamped = await run(
            connection,
            f"SELECT seen_at, ack_note FROM {_schema().TO_RELATION} WHERE out = $agent",
            {"agent": RecordID(AGENT_TABLE, recipient_bare)},
        )
        rows = stamped if isinstance(stamped, list) else []
        assert rows and all(row.get("seen_at") is not None for row in rows), (
            f"a delivery edge was left UNSTAMPED after the drain: {rows!r}"
        )
        over_cap = [row for row in rows if row.get("ack_note") not in (None, _LEGAL_NOTE)]
        assert over_cap and all(
            len(row["ack_note"]) == _schema().MESSAGE_BODY_MAX_CHARS + 1 for row in over_cap
        ), (
            f"the over-cap ack_note value did not survive byte-intact — a migration converges the "
            f"schema without touching the data (store-ref §1.4), and this ruling adds no heal: {over_cap!r}"
        )

    async def test_CONTROL_an_already_seen_edge_is_outside_the_drain_window(
        self, dirty_to_world: Any
    ) -> None:
        """C-control (§6 step 6) — the drain's window predicate is ``seen_at IS NONE``: an edge already
        stamped is OUTSIDE the window and is NOT re-stamped. Pre-stamp the CLEAN edge, then drain: it
        serves + stamps ONLY the still-unseen (over-cap) edge — proving the window predicate is drain's
        real one, and that the dirty edge is served even when it is the ONLY one in the window (the
        sharpest DD-3.c case). RED at HEAD via the missing Subject arg."""
        ledger, recipient_bare, subject, connection, _env = dirty_to_world
        # pre-stamp the CLEAN edge (seq 0) out of the window.
        clean = await run(
            connection,
            f"SELECT id FROM {_schema().TO_RELATION} WHERE out = $agent AND ack_note = $note",
            {"agent": RecordID(AGENT_TABLE, recipient_bare), "note": _LEGAL_NOTE},
        )
        assert clean, "fixture check: the clean edge must exist"
        await run(
            connection,
            f"UPDATE {_schema().TO_RELATION} SET seen_at = $now WHERE id = $edge",
            {"now": datetime.now(UTC), "edge": _one(clean)["id"]},
        )
        result = await self._drain(ledger, recipient_bare, subject)
        assert sorted(result.stamped_seqs) == [1], (
            f"the drain re-stamped an already-seen edge or missed the dirty over-cap edge (which is now "
            f"the ONLY one in the window — the sharpest DD-3.c case): stamped={result.stamped_seqs!r}"
        )


class TestRelationFlipAgainstAnExistingStore:
    """⚠⚠ THE PIN THE WHOLE FLIP HANGS ON — the §1.6
    `TestSchemaMigrationAgainstAnExistingStore` shape, because **a virgin-DB
    fixture proves NOTHING here by construction.**

    Measured (probe Q2): `DEFINE TABLE IF NOT EXISTS ... ENFORCED` against an
    existing relation table returns **OK**, leaves the stored definition
    **unchanged**, and a ghost RELATE still **succeeds**. That is #107 verbatim
    — and worse in one specific way: on a FRESH database the table does not
    exist, so `IF NOT EXISTS` creates it WITH the guard and **every test
    passes** while no long-lived store ever gains it. The suite would certify a
    guard that production does not have.

    So the shape is mandatory and is exactly §1.6's: apply the OLD DDL → write a
    row under it → apply the NEW DDL → assert the guard is LIVE **and** the old
    row survived.
    """

    @staticmethod
    def _old_ddl() -> str:
        relation = _schema().TO_RELATION
        return (
            f"DEFINE TABLE IF NOT EXISTS {relation} TYPE RELATION SCHEMAFULL;\n"
            f"DEFINE FIELD OVERWRITE session ON {relation} TYPE string;\n"
            f"DEFINE FIELD OVERWRITE created_at ON {relation} TYPE datetime;\n"
        )

    async def _old_world(self, connection: SurrealConnection) -> tuple[str, str]:
        await run(connection, generate_agent_ddl())
        await run(connection, f"DEFINE TABLE IF NOT EXISTS {_schema().MESSAGE_TABLE} SCHEMALESS")
        await run(connection, self._old_ddl())
        agent_id = _agent_record_id("wave7", "fixer-b")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        message_id = uuid.uuid4().hex
        await run(
            connection,
            f"CREATE type::record('{_schema().MESSAGE_TABLE}', $id) CONTENT $content",
            {"id": message_id, "content": {"body": "written under the OLD definition"}},
        )
        await _relate_to(connection, message_id=message_id, agent_id=agent_id)
        return message_id, agent_id

    async def test_BASELINE_the_old_world_really_is_unguarded(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """Without this, "the guard is live after migrating" could be true
        because it was ALWAYS live, and the migration would be untested.
        """
        connection, _env = admin_db
        message_id, _agent_id = await self._old_world(connection)
        await _relate_to(connection, message_id=message_id, agent_id="a-ghost-under-the-old-ddl")
        rows = await run(connection, f"SELECT count() FROM {_schema().TO_RELATION} GROUP ALL")
        assert _one(rows)["count"] == 2, "the OLD definition was supposed to accept a ghost"

    async def test_the_guard_is_LIVE_after_applying_the_new_ddl_to_a_dirty_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await self._old_world(connection)
        await run(connection, generate_message_ddl())
        # ⚠ INSTRUMENT NOTE: ``INFO FOR TABLE`` carries fields/indexes/events —
        # NOT the table's own DEFINE statement. The stored table definition
        # lives in ``INFO FOR DB``'s ``tables`` map (the same place
        # test_graph_surreal.py reads it). Reading the wrong one made this pin
        # fail on a CORRECT build; a probe needs its instrument checked too.
        info = (await run(connection, "INFO FOR DB")).get("tables", {}).get(_schema().TO_RELATION, "")
        # Instrument #1: the STORED definition actually changed.
        assert "ENFORCED" in str(info), (
            f"the new DDL applied to an EXISTING table and the stored definition did NOT "
            f"gain the guard — the silent-no-op migration, shipped: {info!r}"
        )
        # Instrument #2 (independent of introspection): a ghost is now refused.
        fresh_message = await _create_message(connection, session="wave7", seq=99)
        with pytest.raises(Exception):  # noqa: B017 - engine ENFORCED rejection surface
            await _relate_to(
                connection, message_id=fresh_message, agent_id="a-ghost-after-migration"
            )

    async def test_the_row_written_under_the_OLD_definition_SURVIVES(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """§1.6's second half, and the half a migration pin usually forgets: the
        schema converging must not poison existing DATA. The pre-flight audit
        says all 101,479 production edge rows are endpoint-homogeneous, so this
        must hold — and "must hold" is a claim until it is executed.
        """
        connection, _env = admin_db
        await self._old_world(connection)
        relation = _schema().TO_RELATION
        before = _one(await run(connection, f"SELECT count() FROM {relation} GROUP ALL"))["count"]
        await run(connection, generate_message_ddl())
        after = await run(connection, f"SELECT count() FROM {_schema().TO_RELATION} GROUP ALL")
        assert _one(after)["count"] == before, "the migration DROPPED an existing edge row"
        readable = await run(connection, f"SELECT in, out, session FROM {_schema().TO_RELATION}")
        assert readable and all(row.get("session") == "wave7" for row in readable), (
            f"an edge written under the OLD definition is no longer readable intact: {readable!r}"
        )

    async def test_the_migration_is_idempotent_on_an_already_migrated_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """`ensure_ready()` re-applies the DDL at EVERY boot. `OVERWRITE` is a
        FULL REPLACE, so the second application must land the same definition
        rather than drift, and must not disturb the rows.
        """
        connection, _env = admin_db
        await self._old_world(connection)
        await run(connection, generate_message_ddl())
        first = str((await run(connection, "INFO FOR DB")).get("tables", {}).get(_schema().TO_RELATION))
        await run(connection, generate_message_ddl())
        second = str((await run(connection, "INFO FOR DB")).get("tables", {}).get(_schema().TO_RELATION))
        assert first == second, "re-applying the slice DRIFTED the stored definition"


class TestTheFlipAgainstTheTablesThatACTUALLYEXISTInProduction:
    """⚠⚠ MAJOR-4 (adversary) — THE INSTRUMENT WAS AIMED AT THE WRONG TABLE.

    ``TestRelationFlipAgainstAnExistingStore`` above is a good pin, and it
    covers ``to`` — a table that **does not exist in either production
    database** (`REPORT-audit-edge-preflight.md` §Q5: packet 03 is genuinely
    greenfield there). On a table that does not exist, `IF NOT EXISTS` would
    have worked anyway. So the ONE instrument capable of seeing the
    silent-no-op class was pointed at the single case where the no-op cannot
    hurt us, and away from the three where it can.

    The tables the flip actually ships against — and their live row counts from
    the pre-flight audit — are ``briefed``, ``refers`` and ``answers_to``:
    **101,479 rows across two production databases.**

    Two things are pinned here, and the second is the one a migration pin
    usually forgets:

    1. **The flip LANDS** on each of them when applied to a store where the
       table already exists under the OLD, untyped definition.
    2. **The narrowing's documented hazard is PINNED, not assumed.** Typing a
       populated edge WRITE-POISONS any row whose endpoint is of a
       now-forbidden table: readable, traversable, but any future UPDATE is
       rejected (store reference §1.4 — the schema converges, the DATA does
       not). The pre-flight audit found production homogeneous TODAY, so
       nothing would be poisoned — but **that is a fact about data at a point
       in time, not a guarded invariant.** Pinning the BEHAVIOUR means the next
       engineer meets this deliberately instead of from an incident.
    """

    # (generator, relation table, in-table, out-table) — the three that ship.
    _SHIPPED_EDGES = (
        ("generate_brief_ddl", BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE),
        ("generate_graph_ddl", REFERS_RELATION, CODE_NODE_TABLE, NAME_TABLE),
        ("generate_graph_ddl", ANSWERS_TO_RELATION, CODE_NODE_TABLE, NAME_TABLE),
    )

    @staticmethod
    def _ddl_for(generator_name: str) -> str:
        return {
            "generate_brief_ddl": generate_brief_ddl,
            "generate_graph_ddl": generate_graph_ddl,
        }[generator_name]()

    @pytest.mark.parametrize(
        ("generator_name", "relation", "in_table", "out_table"),
        _SHIPPED_EDGES,
        ids=[edge[1] for edge in _SHIPPED_EDGES],
    )
    async def test_the_flip_LANDS_on_an_existing_untyped_relation_table(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        generator_name: str,
        relation: str,
        in_table: str,
        out_table: str,
    ) -> None:
        connection, _env = admin_db
        # THE OLD WORLD: the untyped definition every production store carries.
        await run(connection, f"DEFINE TABLE IF NOT EXISTS {relation} TYPE RELATION SCHEMAFULL")
        before = (await run(connection, "INFO FOR DB")).get("tables", {}).get(relation, "")
        assert "IN " not in str(before), (
            f"BASELINE: {relation} was supposed to start UNTYPED — otherwise this pin "
            f"proves nothing about migrating: {before!r}"
        )
        await run(connection, self._ddl_for(generator_name))
        after = str((await run(connection, "INFO FOR DB")).get("tables", {}).get(relation, ""))
        assert f"IN {in_table} OUT {out_table}" in after, (
            f"the flip applied to an EXISTING {relation} table and the stored definition "
            f"did NOT gain its endpoint typing — the silent no-op, shipped against "
            f"101,479 live rows: {after!r}"
        )

    async def test_a_HETEROGENEOUS_row_is_write_poisoned_not_dropped(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """The narrowing's DOCUMENTED outcome, executed rather than trusted
        (store reference §1.4). An edge whose endpoint is of a now-forbidden
        table survives READABLE and is never silently dropped — but any future
        write to it is rejected LOUDLY.

        This is the hazard the pre-flight audit cleared for TODAY's data. Pinned
        so that "production is homogeneous" stops being an unguarded premise.
        """
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, f"DEFINE TABLE IF NOT EXISTS {BRIEFED_RELATION} TYPE RELATION SCHEMAFULL")
        await run(connection, f"DEFINE FIELD OVERWRITE via ON {BRIEFED_RELATION} TYPE string")
        await run(connection, f"DEFINE FIELD OVERWRITE at ON {BRIEFED_RELATION} TYPE datetime")
        agent_id = _agent_record_id("wave7", "fixer-b")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        # A FORBIDDEN endpoint under the new definition: agent->briefed->AGENT.
        # Legal under the old untyped table; a heterogeneous row by construction.
        other_id = _agent_record_id("wave7", "audit-c")
        await _create_agent(connection, agent_id=other_id, name="audit-c", session="wave7")
        await run(
            connection,
            f"RELATE $from->{BRIEFED_RELATION}->$to SET via = $via, at = $at",
            {
                "from": RecordID(AGENT_TABLE, agent_id),
                "to": RecordID(AGENT_TABLE, other_id),
                "via": "register",
                "at": datetime.now(UTC),
            },
        )
        await run(connection, generate_brief_ddl())

        rows = await run(connection, f"SELECT via FROM {BRIEFED_RELATION}")
        assert rows and rows[0].get("via") == "register", (
            f"the heterogeneous row was DROPPED or became unreadable by the migration — "
            f"the documented outcome is write-poisoned, never lost: {rows!r}"
        )
        with pytest.raises(Exception):  # noqa: B017 - engine coercion error surface
            await run(
                connection,
                f"UPDATE {BRIEFED_RELATION} SET via = $via",
                {"via": "explicit"},
            )

    async def test_CONTROL_a_HOMOGENEOUS_row_stays_fully_writable(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """THE CONTROL that makes the pin above a finding rather than a guess.

        Without it, "the UPDATE raised" could be caused by anything — a missing
        field, an unrelated ASSERT, a typo in the statement. The adversary's own
        first write-poisoning probe failed exactly this way (§8.2): it showed
        poisoning on BOTH arms because its control was broken for a DIFFERENT
        reason, and the attribution was unsound until a single variable was
        isolated. Here the ONLY difference from the pin above is the endpoint's
        TABLE.

        This is also the pin that proves the pre-flight audit's verdict is
        actionable: production's rows are all of this shape, and this shape
        migrates cleanly.
        """
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, f"DEFINE TABLE IF NOT EXISTS {BRIEFED_RELATION} TYPE RELATION SCHEMAFULL")
        await run(connection, f"DEFINE FIELD OVERWRITE via ON {BRIEFED_RELATION} TYPE string")
        await run(connection, f"DEFINE FIELD OVERWRITE at ON {BRIEFED_RELATION} TYPE datetime")
        agent_id = _agent_record_id("wave7", "fixer-b")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        brief_id = _brief_record_id("project", 1)
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        await run(
            connection,
            f"RELATE $from->{BRIEFED_RELATION}->$to SET via = $via, at = $at",
            {
                "from": RecordID(AGENT_TABLE, agent_id),
                "to": RecordID(BRIEF_TABLE, brief_id),
                "via": "register",
                "at": datetime.now(UTC),
            },
        )
        await run(connection, generate_brief_ddl())
        # The ONLY variable vs the pin above is the endpoint table. This row is
        # of the shape production actually holds — it must stay WRITABLE.
        await run(
            connection, f"UPDATE {BRIEFED_RELATION} SET via = $via", {"via": "explicit"}
        )
        rows = await run(connection, f"SELECT via FROM {BRIEFED_RELATION}")
        assert rows and rows[0].get("via") == "explicit"
