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
``REPORT-probe-7061-c1.md`` at the repo root. This file's own
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
    BRIEF_COUNTER_TABLE,
    BRIEF_TABLE,
    BRIEFED_RELATION,
    generate_agent_ddl,
    generate_brief_ddl,
)
from render_injection_scaffold import _INJECTION_THREAT_CHARS, _ROW_FORGE_PAYLOAD
from surrealdb import RecordID

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


def _field_statement(ddl: str, table: str, field: str) -> str:
    """Return the single ``DEFINE FIELD ... ON <table> ...`` statement for
    ``field`` on ``table``, isolated so a per-field assertion can't be fooled
    by a substring match against some OTHER field or table.

    Raises:
        AssertionError: No matching ``DEFINE FIELD`` statement was found.
    """
    marker = f"DEFINE FIELD IF NOT EXISTS {field} ON {table} "
    for statement in ddl.split(";\n"):
        if statement.strip().startswith(marker):
            return statement
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
        ddl = generate_brief_ddl()
        assert f"DEFINE TABLE IF NOT EXISTS {BRIEFED_RELATION} TYPE RELATION SCHEMAFULL" in ddl

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
        # TYPE RELATION auto-defines in/out; refers/answers_to never hand-
        # declare them either (surreal_schema.py:454's own docstring).
        ddl = generate_brief_ddl()
        assert f"DEFINE FIELD IF NOT EXISTS in ON {BRIEFED_RELATION} " not in ddl
        assert f"DEFINE FIELD IF NOT EXISTS out ON {BRIEFED_RELATION} " not in ddl

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
