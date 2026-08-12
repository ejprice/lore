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

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from _surreal_harness import (
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture
    run,
)
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
    "z" * 65,  # one over the 64-char cap
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

    def test_name_and_session_carry_the_verified_charset_assert(self) -> None:
        ddl = generate_agent_ddl()
        for field in ("name", "session"):
            statement = _field_statement(ddl, AGENT_TABLE, field)
            assert "TYPE string" in statement
            assert _IDENTIFIER_CHARSET_ASSERT_TEXT in statement

    def test_role_carries_the_non_empty_assert(self) -> None:
        ddl = generate_agent_ddl()
        role = _field_statement(ddl, AGENT_TABLE, "role")
        assert "TYPE string" in role
        assert _NON_EMPTY_STRING_ASSERT_TEXT in role

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


class TestAgentCharsetAssert:
    """The ``name``/``session`` charset ASSERT: hostile shapes rejected, real
    identifiers accepted (positive control alongside the negative one — an
    overly-strict ASSERT would silently pass the negative tests while
    breaking every real caller).
    """

    @pytest.mark.parametrize("field", ["name", "session"])
    @pytest.mark.parametrize("hostile_value", _HOSTILE_IDENTIFIERS)
    async def test_hostile_value_is_rejected(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        field: str,
        hostile_value: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        kwargs: dict[str, Any] = {"name": "fixer-b", "session": "wave7"}
        kwargs[field] = hostile_value
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_agent(
                connection,
                agent_id=uuid.uuid4().hex,
                name=kwargs["name"],
                session=kwargs["session"],
            )

    @pytest.mark.parametrize("field", ["name", "session"])
    @pytest.mark.parametrize("valid_value", _VALID_IDENTIFIERS)
    async def test_valid_value_is_accepted(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        field: str,
        valid_value: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        kwargs: dict[str, Any] = {"name": "fixer-b", "session": "wave7"}
        kwargs[field] = valid_value
        await _create_agent(
            connection,
            agent_id=uuid.uuid4().hex,
            name=kwargs["name"],
            session=kwargs["session"],
        )


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


class TestAgentRoleNonEmptyAssert:
    async def test_empty_role_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_agent(
                connection, agent_id=uuid.uuid4().hex, name="fixer-b", session="wave7", role=""
            )

    @pytest.mark.parametrize("whitespace_role", [" ", "   ", "\t"])
    async def test_whitespace_only_role_is_rejected(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        whitespace_role: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_agent(
                connection,
                agent_id=uuid.uuid4().hex,
                name="fixer-b",
                session="wave7",
                role=whitespace_role,
            )

    async def test_real_role_is_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await _create_agent(
            connection, agent_id=uuid.uuid4().hex, name="fixer-b", session="wave7", role="builder"
        )


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
        # Store idiom (repo CLAUDE.md / brief): str(RecordID) round-trips to
        # "table:id" — the shape a ledger's ``_bare_id`` helper depends on.
        connection, _env = admin_db
        await run(connection, generate_agent_ddl())
        await run(connection, generate_brief_ddl())
        agent_id = uuid.uuid4().hex
        brief_id = uuid.uuid4().hex
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        await _create_brief(connection, brief_id=brief_id, name="project", version=1)
        edge = _one(await _relate_briefed(connection, agent_id=agent_id, brief_id=brief_id))
        assert str(edge["in"]) == f"{AGENT_TABLE}:{agent_id}"
        assert str(edge["out"]) == f"{BRIEF_TABLE}:{brief_id}"

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
        assert str(row["id"]) == f"{AGENT_TABLE}:{agent_id}"

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
        assert str(row["id"]) == f"{BRIEF_TABLE}:{brief_id}"

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

    def test_grade_is_a_closed_two_value_domain(self) -> None:
        statement = _field_statement(generate_message_ddl(), _schema().MESSAGE_TABLE, "grade")
        assert "ASSERT" in statement
        assert "'signal'" in statement
        assert "'directive'" in statement

    def test_body_carries_a_length_bound_the_store_itself_enforces(self) -> None:
        """The app-level teaching reject is the primary guard; the schema ASSERT
        is the backstop that makes a bypassing writer fail LOUDLY rather than
        landing an unbounded body.
        """
        statement = _field_statement(generate_message_ddl(), _schema().MESSAGE_TABLE, "body")
        assert "ASSERT" in statement
        cap = _schema().MESSAGE_BODY_MAX_CHARS
        assert f"string::len($value) <= {cap}" in statement, (
            f"expected the body length bound (<= {cap}) in {statement!r}"
        )

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


class TestThePointerBoundsHaveTheirSTOREBackstop:
    """DD-3.c — enforce at BOTH layers, mirroring ``body`` exactly.

    THE WRONG BUILD THIS EXISTS FOR, named by the design's own adversary: a
    LEDGER-ONLY build. Every teaching reject passes, every surface pin passes,
    and any future writer that does not go through ``MessageLedger.send`` lands
    an unbounded row silently. ``body`` has carried a store ASSERT since packet
    03 for precisely that reason; the pointer class gets the same treatment or it
    does not have the same guarantee.

    Pins the EMITTED statement, never ``INFO FOR TABLE``'s echo — the engine
    NORMALISES what it echoes (``option<string>`` comes back as
    ``none | string``, a closure's ``|$r|`` as ``|$r: any|``), so an echo-diffing
    pin mismatches against a correct build. House idiom: assert what we send.
    """

    @staticmethod
    def _field(ddl: str, table: str, name: str) -> str:
        prefix = f"DEFINE FIELD OVERWRITE {name} ON {table} "
        matches = [text.strip() for text in ddl.split(";\n") if text.strip().startswith(prefix)]
        assert len(matches) == 1, (
            f"expected exactly ONE definition of {table}.{name}, got {matches!r}"
        )
        return matches[0]

    def test_refs_carries_its_COUNT_assert(self) -> None:
        statement = self._field(generate_message_ddl(), _schema().MESSAGE_TABLE, "refs")
        assert (
            f"ASSERT array::len($value) <= {_schema().MESSAGE_REFS_MAX_COUNT}" in statement
        ), (
            f"refs has no store-level COUNT backstop, so a writer that bypasses the ledger "
            f"stores a thousand-entry list silently: {statement!r}"
        )
        assert "DEFAULT []" in statement, (
            f"the composed `DEFAULT [] ASSERT …` clause lost its DEFAULT — a ref-less send "
            f"must still be able to omit the field: {statement!r}"
        )

    def test_the_ELEMENT_row_carries_the_per_entry_assert_AND_overwrite(self) -> None:
        """⚠ THE ELEMENT ROW MUST BE ``OVERWRITE``, and that is not style.

        ``DEFINE FIELD … TYPE array<T>`` IMPLICITLY DEFINES ``<field>.*``, so the
        element definition is ALWAYS a re-definition — a bare one raises *"The
        field 'refs.*' already exists"* and takes the whole DDL apply down. The
        house ``_define_field`` emits ``OVERWRITE`` for every field, which is
        what makes this work; this pin is what stops someone "tidying" the
        element row onto a different emitter.
        """
        statement = self._field(generate_message_ddl(), _schema().MESSAGE_TABLE, "refs[*]")
        assert (
            f"ASSERT string::len($value) <= {_schema().MESSAGE_POINTER_MAX_CHARS}" in statement
        ), (
            f"refs entries have no store-level LENGTH backstop — the per-entry bound is what "
            f"stops a 100KB payload riding one 'pointer': {statement!r}"
        )
        assert statement.startswith("DEFINE FIELD OVERWRITE refs[*] "), (
            f"the element row is not OVERWRITE. `TYPE array<T>` implicitly defines `<field>.*`, "
            f"so this is always a RE-definition and a bare DEFINE raises 'The field refs.* "
            f"already exists', failing the entire apply: {statement!r}"
        )

    @pytest.mark.parametrize("field_name", ["thread", "task_id"])
    def test_the_pointer_LABELS_carry_bare_length_asserts(self, field_name: str) -> None:
        """⚠ BARE — no ``$value = NONE OR`` guard. An ``option<>`` field's ASSERT
        is NOT evaluated when the value is absent (probed), so the guard is cruft
        that teaches the next author it is required. Pinned in both directions:
        the bound is present AND the guard is absent."""
        statement = self._field(generate_message_ddl(), _schema().MESSAGE_TABLE, field_name)
        assert (
            f"ASSERT string::len($value) <= {_schema().MESSAGE_POINTER_MAX_CHARS}" in statement
        ), f"{field_name} has no store-level pointer bound: {statement!r}"
        assert "NONE OR" not in statement, (
            f"{field_name} carries a NONE-guard the engine does not need — an option<> field's "
            f"ASSERT is not evaluated on an absent value, and the guard teaches the next author "
            f"a rule that does not exist: {statement!r}"
        )

    def test_the_ack_note_carries_the_BODY_cap_not_the_pointer_cap(self) -> None:
        """DD-3.f. A note is message-grade PROSE, so it takes the BODY constant —
        and the two constants must be DIFFERENT for this pin to have force."""
        assert _schema().MESSAGE_BODY_MAX_CHARS != _schema().MESSAGE_POINTER_MAX_CHARS, (
            "the body and pointer caps are equal, so this pin cannot tell which one the note "
            "took — re-derive it before trusting it"
        )
        statement = self._field(generate_message_ddl(), _schema().TO_RELATION, "ack_note")
        assert (
            f"ASSERT string::len($value) <= {_schema().MESSAGE_BODY_MAX_CHARS}" in statement
        ), f"the ack note has no store-level bound, or took the wrong one: {statement!r}"


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

    async def test_an_oversize_body_is_rejected_by_the_store_backstop(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_message_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_message(
                connection,
                session="wave7",
                seq=6,
                body="z" * (_schema().MESSAGE_BODY_MAX_CHARS + 1),
            )

    # --- WAVE 3 / C4: the LIVE leg DD-3.c's rider named ----------------------
    #
    # DD-3.c says enforce the pointer bounds "mirroring ``body`` EXACTLY", and
    # ``body``'s instrumentation has TWO parts: an offline DDL pin and the LIVE
    # behavioural pin directly above. The design wave shipped only the offline
    # half. That is not a live defect — the behaviour is correct today — it is a
    # missing INSTRUMENT, and the gap it leaves is precisely the one the
    # OVERWRITE clause exists to close: **pinning the emitted statement proves
    # the RECIPE; only a live write proves the CAKE.** An emission pin cannot see
    # a definition that emits perfectly and never lands on the engine.

    async def test_an_oversize_REF_ENTRY_is_rejected_by_the_store_backstop(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_message_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_message(
                connection,
                session="wave7",
                seq=20,
                refs=["r" * (_schema().MESSAGE_POINTER_MAX_CHARS + 1)],
            )

    async def test_an_over_COUNT_refs_list_is_rejected_by_the_store_backstop(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_message_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_message(
                connection,
                session="wave7",
                seq=21,
                refs=[f"r{index}" for index in range(_schema().MESSAGE_REFS_MAX_COUNT + 1)],
            )

    @pytest.mark.parametrize("field_name", ["thread", "task_id"])
    async def test_an_oversize_pointer_LABEL_is_rejected_by_the_store_backstop(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        field_name: str,
    ) -> None:
        connection, _env = admin_db
        await run(connection, generate_message_ddl())
        oversize = "t" * (_schema().MESSAGE_POINTER_MAX_CHARS + 1)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_message(
                connection, session="wave7", seq=22, **{field_name: oversize}
            )

    async def test_POSITIVE_CONTROL_a_legal_pointer_row_IS_accepted(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """Without this, every reject leg above is satisfied by a schema that
        refuses EVERYTHING — and the omitted-``task_id`` half additionally proves
        the bare (unguarded) ASSERT on an ``option<>`` field is not evaluated
        when the value is absent, i.e. that the missing NONE-guard is CORRECT
        rather than lucky."""
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


class TestThePointerBoundsMigrateADIRTYStore:
    """WAVE 3 / C4 — the §1.6 dirty-store leg DD-3.c's rider named explicitly:
    *"the message-slice dirty-store pin gains the narrowed-assert leg."*

    **A virgin-DB fixture cannot see this by construction**, and that is the
    whole point of the shape: on a fresh database the field does not exist, so
    any clause creates it WITH the bound and every test passes while no
    long-lived store ever gains it. The narrowing has to be applied to a store
    that ALREADY carries the old, unbounded definition — which is the only
    configuration where a silent no-op is distinguishable from a migration.

    Shape, exactly §1.6's: apply the OLD (unbounded) DDL -> write a row under it
    -> apply the NEW DDL -> assert the bound is LIVE **and** the old row
    survived. The BASELINE leg is what stops "the bound is live" from being true
    because it was always live.
    """

    @staticmethod
    def _old_message_ddl() -> str:
        """The message node as it stood BEFORE the pointer bounds — same fields,
        no ASSERTs on refs/thread/task_id."""
        table = _schema().MESSAGE_TABLE
        return (
            f"DEFINE TABLE IF NOT EXISTS {table} SCHEMAFULL;\n"
            f"DEFINE FIELD OVERWRITE seq ON {table} TYPE int;\n"
            f"DEFINE FIELD OVERWRITE session ON {table} TYPE string;\n"
            f"DEFINE FIELD OVERWRITE thread ON {table} TYPE string;\n"
            f"DEFINE FIELD OVERWRITE sender ON {table} TYPE record<{AGENT_TABLE}>;\n"
            f"DEFINE FIELD OVERWRITE grade ON {table} TYPE string;\n"
            f"DEFINE FIELD OVERWRITE body ON {table} TYPE string;\n"
            f"DEFINE FIELD OVERWRITE refs ON {table} TYPE array<string> DEFAULT [];\n"
            f"DEFINE FIELD OVERWRITE task_id ON {table} TYPE option<string>;\n"
            f"DEFINE FIELD OVERWRITE question ON {table} TYPE bool DEFAULT false;\n"
            f"DEFINE FIELD OVERWRITE created_at ON {table} TYPE datetime;\n"
        )

    async def _dirty_old_world(self, connection: SurrealConnection) -> str:
        """Old DDL + one row that the NEW bounds would refuse."""
        await run(connection, generate_agent_ddl())
        await run(connection, self._old_message_ddl())
        await _create_agent(
            connection,
            agent_id=_agent_record_id("wave7", "lead"),
            name="lead",
            session="wave7",
        )
        return await _create_message(
            connection,
            session="wave7",
            seq=90,
            refs=["r" * (_schema().MESSAGE_POINTER_MAX_CHARS + 5)],
        )

    async def test_BASELINE_the_old_world_really_accepts_an_oversize_pointer(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """Without this, "the bound is live after migrating" could be true
        because it was ALWAYS live — and the migration itself untested."""
        connection, _env = admin_db
        message_id = await self._dirty_old_world(connection)
        assert message_id, "the OLD definition was supposed to accept an oversize ref"

    async def test_the_bound_is_LIVE_after_applying_the_new_ddl_to_a_dirty_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """THE #107 SHAPE. A definition that emits perfectly and never LANDS is
        invisible to every offline pin — this is the leg that would catch it."""
        connection, _env = admin_db
        await self._dirty_old_world(connection)
        await run(connection, generate_message_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await _create_message(
                connection,
                session="wave7",
                seq=91,
                refs=["r" * (_schema().MESSAGE_POINTER_MAX_CHARS + 1)],
            )

    async def test_the_row_written_under_the_OLD_definition_SURVIVES(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """A narrowing converges the SCHEMA and never the DATA: the pre-existing
        row is left INTACT and readable, never rewritten and never dropped. (It
        is write-poisoned — any future UPDATE of it is refused — which is the
        accepted §1.4 consequence, and harmless here because message rows are
        never UPDATEd after create.)"""
        connection, _env = admin_db
        message_id = await self._dirty_old_world(connection)
        await run(connection, generate_message_ddl())
        rows = await run(
            connection,
            f"SELECT seq, refs FROM type::record('{_schema().MESSAGE_TABLE}', $id)",
            {"id": message_id},
        )
        surviving = _one(rows)
        assert surviving["seq"] == 90, "the pre-existing row did not survive the narrowing"
        assert len(surviving["refs"][0]) > _schema().MESSAGE_POINTER_MAX_CHARS, (
            "the surviving row's over-length ref was REWRITTEN — a narrowing must converge "
            "the schema without touching the data"
        )

    async def test_the_migration_is_idempotent_on_an_already_migrated_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """``ensure_ready`` re-applies this DDL on EVERY boot, so a second apply
        must be a clean no-op — the element row is the one that would raise here
        if it ever lost its ``OVERWRITE``."""
        connection, _env = admin_db
        await self._dirty_old_world(connection)
        await run(connection, generate_message_ddl())
        await run(connection, generate_message_ddl())
        message_id = await _create_message(
            connection, session="wave7", seq=92, refs=["docs/plans/v2/INDEX.md"]
        )
        assert message_id


class TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge:
    """WAVE 3 — the `to` HALF of the same rider, and the half that can actually
    hurt.

    DD-3.c's migration bullet said a later narrowing *"cannot write-poison
    (message rows are never UPDATEd)"*. **That is true of `message` and FALSE of
    `to`**, where DD-3.f puts `ack_note` — and the clause was STRUCK on
    2026-07-25 after the round-2 cold audit reproduced the consequence.

    Why `to` is different, and why it is worse than a per-row rejection:
    ``MessageLedger.drain`` UPDATEs `to` on EVERY call, in ONE guarded statement
    over the whole window. SurrealDB re-validates the WHOLE record on write, so a
    single legacy edge carrying an over-cap ``ack_note`` fails that statement —
    and because it is one statement over the window, **the agent cannot drain ANY
    of its inbox.** Total denial.

    Production exposure at this deploy is ZERO (`message`/`to` have never been
    deployed — that is the free window this wave used). This pin is not for
    today; it is so that the next narrowing of a `to` field meets the mechanism
    DELIBERATELY instead of rediscovering it from an outage. The sibling class
    above covers `message`, where the original reasoning happened to hold;
    shipping the instrument only for the table that cannot hurt us would repeat
    the exact rider-skipping this correction is about.
    """

    @staticmethod
    def _old_to_ddl() -> str:
        """The delivery edge as it stood BEFORE `ack_note` was bounded."""
        relation = _schema().TO_RELATION
        return (
            f"DEFINE TABLE OVERWRITE {relation} TYPE RELATION "
            f"IN {_schema().MESSAGE_TABLE} OUT {AGENT_TABLE} ENFORCED SCHEMAFULL;\n"
            f"DEFINE FIELD OVERWRITE session ON {relation} TYPE string;\n"
            f"DEFINE FIELD OVERWRITE created_at ON {relation} TYPE datetime;\n"
            f"DEFINE FIELD OVERWRITE seen_at ON {relation} TYPE option<datetime>;\n"
            f"DEFINE FIELD OVERWRITE acked_at ON {relation} TYPE option<datetime>;\n"
            f"DEFINE FIELD OVERWRITE ack_note ON {relation} TYPE option<string>;\n"
        )

    async def _dirty_edges(self, connection: SurrealConnection) -> str:
        """One POISONED edge (over-cap ack_note) and one CLEAN edge, both written
        under the OLD definition. Returns the recipient agent id."""
        await run(connection, generate_agent_ddl())
        await run(connection, f"DEFINE TABLE IF NOT EXISTS {_schema().MESSAGE_TABLE} SCHEMALESS")
        await run(connection, self._old_to_ddl())
        agent_id = _agent_record_id("wave7", "fixer-b")
        await _create_agent(connection, agent_id=agent_id, name="fixer-b", session="wave7")
        for index, note in enumerate(
            ["a legal note", "n" * (_schema().MESSAGE_BODY_MAX_CHARS + 1)]
        ):
            message_id = uuid.uuid4().hex
            await run(
                connection,
                f"CREATE type::record('{_schema().MESSAGE_TABLE}', $id) CONTENT $content",
                {"id": message_id, "content": {"body": f"m{index}"}},
            )
            await run(
                connection,
                f"RELATE $message->{_schema().TO_RELATION}->$agent SET "
                f"session = 'wave7', created_at = $now, ack_note = $note",
                {
                    "message": RecordID(_schema().MESSAGE_TABLE, message_id),
                    "agent": RecordID(AGENT_TABLE, agent_id),
                    "now": datetime.now(UTC),
                    "note": note,
                },
            )
        return agent_id

    async def test_BASELINE_the_old_definition_really_accepts_an_oversize_note(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        connection, _env = admin_db
        agent_id = await self._dirty_edges(connection)
        rows = await run(
            connection, f"SELECT count() FROM {_schema().TO_RELATION} GROUP ALL"
        )
        assert _one(rows)["count"] == 2, "the OLD definition was supposed to accept both edges"
        assert agent_id

    async def test_a_WHOLE_WINDOW_stamp_is_DENIED_by_ONE_legacy_edge(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """THE MECHANISM, reproduced: not a per-row rejection — TOTAL DENIAL.

        The drain's real shape is one guarded UPDATE over the whole window, and
        the engine re-validates the WHOLE record on write, so the poisoned edge
        takes the clean one down with it.
        """
        connection, _env = admin_db
        agent_id = await self._dirty_edges(connection)
        await run(connection, generate_message_ddl())
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await run(
                connection,
                f"UPDATE {_schema().TO_RELATION} SET seen_at = $now "
                f"WHERE out = $agent AND seen_at IS NONE",
                {"now": datetime.now(UTC), "agent": RecordID(AGENT_TABLE, agent_id)},
            )

    async def test_CONTROL_the_same_stamp_over_the_CLEAN_edge_alone_is_ACCEPTED(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """The discriminating control — without it the rejection above could be
        the statement, the schema, or the fixture rather than the poisoned edge.
        Same statement, same post-migration schema, scoped to the clean edge."""
        connection, _env = admin_db
        agent_id = await self._dirty_edges(connection)
        await run(connection, generate_message_ddl())
        clean = await run(
            connection,
            f"SELECT id FROM {_schema().TO_RELATION} WHERE out = $agent "
            f"AND ack_note = 'a legal note'",
            {"agent": RecordID(AGENT_TABLE, agent_id)},
        )
        assert clean, "fixture check: the clean edge must exist"
        await run(
            connection,
            f"UPDATE {_schema().TO_RELATION} SET seen_at = $now WHERE id = $edge",
            {"now": datetime.now(UTC), "edge": _one(clean)["id"]},
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
