"""P8b exit smoke test against the live lore MCP server (streamable-HTTP).

Lives OUTSIDE the lore repo (a scratchpad script, not a repo artifact). Run with::

    uv run python /path/to/smoke_p8b.py [--mechanics]

from the lore repo root (``/home/ejprice/PycharmProjects/lore``) so ``uv`` resolves
the workspace venv that already carries the ``mcp`` client package the project's
own eval harness uses (see ``docs/eval/connections_p8a.py``).

CONNECTION LAYER: modeled on the committed, PROVEN ``docs/eval/connections_p8a.py``
(P8a baseline instrument, verified live against this exact server) rather than
importing it, so this script stays self-contained. In particular it copies that
module's two hard-won lessons:

1. ``streamablehttp_client``'s async context yields a tuple whose length varies by
   SDK version/transport (a plain ``(read, write)`` 2-tuple, or a 3-tuple with a
   trailing session-id getter) -- unpacked defensively in :func:`connect`, exactly
   as ``MCPConnection.__aenter__`` does.
2. A tool result's ``content`` is ``list[mcp.types.TextContent]`` (pydantic
   objects), never directly JSON-parsable as a whole -- ``.text`` is extracted off
   each block and joined (see :func:`_joined_text`), the same fix
   ``evaluation_harness_p8a.py._serialize_tool_result`` had to add after the stock
   mcp-builder script's ``json.dumps(tool_result)`` broke on EVERY call.

AUTH: ``lore.yaml`` documents "No auth -> localhost mode" for this project (no
``auth`` block configured) and the repo's own ``.mcp.json`` points at
``http://127.0.0.1:9202/mcp`` with no headers -- so no bearer key is sent. If a
future redeploy adds auth, ``NO_AUTH_HEADERS`` is the one place to change.

TWO RUN MODES:

* ``--mechanics`` -- validates ONLY the connection + tools/list (without asserting
  the four new P8b tools are present -- the pre-redeploy container predates them)
  plus the one legacy-tool sanity call. Safe to run against the CURRENT live
  container before the P8b redeploy.
* (default, no flag) -- the FULL P8b exit assertion run: verify/read/diff/findings
  round-trips plus the dogfood finding-ledger filing. Run this AFTER the redeploy.

Unix-philosophy output: one ``PASS: ...`` line per check on success; any failure
prints full detail (the offending payload/response) and a non-zero exit.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult

# --------------------------------------------------------------------------
# Server + auth constants (see lore.yaml: server.host/port/path, no auth block)
# --------------------------------------------------------------------------
MCP_SERVER_URL = "http://127.0.0.1:9202/mcp"
NO_AUTH_HEADERS: dict[str, str] = {}

# --------------------------------------------------------------------------
# Expected tool surface (server.py @mcp.tool registrations, read 2026-07-04)
# --------------------------------------------------------------------------
NEW_P8B_TOOL_NAMES = frozenset(
    {"lore_verify", "lore_read", "lore_diff", "lore_findings"}
)
PRE_EXISTING_TOOL_NAMES = frozenset(
    {
        "lore_search",
        "lore_get_symbol",
        "lore_remember",
        "lore_recall",
        "lore_claim_task",
        "lore_tasks",
        # P8d Wave 3: lore_reindex + lore_index_status FOLD into ONE
        # lore_index(reconcile=False, tier=None) tool; the two old names no
        # longer publish.
        "lore_index",
        # P8d Wave 2: lore_what_imports / lore_blast_radius / lore_tests_for /
        # lore_references folded into lore_impact; no longer on the wire surface.
        "lore_dead_code",
        "lore_impact",
        "lore_map",
    }
)

# --------------------------------------------------------------------------
# lore_verify round-trip fixtures
# --------------------------------------------------------------------------
VERIFY_TRUE_QUALIFIED_NAME = "SymbolTool"
VERIFY_TRUE_FILE_PATH = "loremaster/symbols.py"
VERIFY_FALSE_SIGNATURE_FRAGMENT = "def nonexistent_method"
VERIFY_GARBAGE_QUALIFIED_NAME = "TotallyBogusSymbolThatDoesNotExist12345"

# --------------------------------------------------------------------------
# lore_read round-trip fixture
# --------------------------------------------------------------------------
READ_TIER = "lore"
READ_PATH = "loremaster/loremaster/symbols.py"
READ_LINE_START = 1
READ_LINE_END = 20

# --------------------------------------------------------------------------
# lore_diff — server.py's own "nothing recorded yet" sentinel (copied verbatim
# so the smoke script recognises a genuinely-empty ledger as PASS, not FAIL).
# --------------------------------------------------------------------------
NO_SNAPSHOTS_SENTINEL = "(no snapshots recorded yet)"

# --------------------------------------------------------------------------
# lore_findings — the DOGFOOD leg. This is a genuine, first-filed friction entry
# from this session (not test data) — content is verbatim, never altered.
# --------------------------------------------------------------------------
FINDING_KIND = "friction"
FINDING_AREA = "lore_tests_for"
FINDING_CATEGORY = "affordance_gap"
FINDING_CREATED_BY = "p8b-lead"
FINDING_SUBJECT = "tests_for returns empty for helpers exercised only indirectly"
FINDING_BODY = (
    "lore_tests_for('loremaster.search._sanitise_line') returns [] despite 19 "
    "passing tests in TestRenderSanitiser (test_search.py) exercising it every "
    "run — they drive it via the search-rendering pipeline rather than "
    "referencing the symbol directly, so the graph's reference heuristic finds "
    "no edge. Workaround: git show + grep for the covering test class. Feeds "
    "P8d: credit a helper's tests via containing-module/class co-location or an "
    "indirect call chain, not only direct reference edges. (First filed in "
    "FRICTION.md 2026-07-04 by warmup-1, commit c0132d0; re-filed here as the "
    "canonical row through the new surface.)"
)
FINDING_ACK_ACTOR = "p8b-lead"

# --------------------------------------------------------------------------
# Rendered-text parsing patterns (mirroring server.py's AppContext render
# helpers verbatim, so a shape drift there fails this script loudly).
# --------------------------------------------------------------------------
_REPORT_RENDER_PATTERN = re.compile(r"^reported finding #(\d+) \(id (\S+), status open\)$")
_FINDING_ROW_PATTERN = re.compile(
    r"^- \[#(?P<number>\d+) (?P<status>\w+)\] (?P<subject>.*?) "
    r"\(id (?P<id>\S+), kind (?P<kind>\S+), area (?P<area>\S+), "
    r"category (?P<category>\S+), by (?P<created_by>\S+)\)$"
)
_TRANSITION_RENDER_TEMPLATE = "finding #{number} transitioned to {status} by {actor}"
_SNAPSHOT_ROW_ID_PATTERN = re.compile(r"^- (\S+) ")
_FINDING_NUMBER_IN_ROW_PATTERN = re.compile(r"\[#(\d+) ")


class SmokeCheckFailed(AssertionError):
    """Raised by a check function with full diagnostic detail already in the message."""


@asynccontextmanager
async def connect(url: str) -> AsyncIterator[ClientSession]:
    """Open + initialize a streamable-HTTP MCP session against ``url``.

    Modeled on ``docs/eval/connections_p8a.py``'s ``MCPConnectionHTTP`` /
    ``MCPConnection.__aenter__``: ``streamablehttp_client``'s yielded tuple is
    unpacked defensively (2-tuple, or 3-tuple with a trailing session-id getter)
    rather than assuming one fixed shape.
    """
    async with streamablehttp_client(url=url, headers=NO_AUTH_HEADERS) as transport:
        # Widened to a variable-length tuple type so mypy doesn't narrow len() to the
        # installed SDK's fixed 3-tuple literal and mark the 2-tuple branch unreachable
        # -- the defensive length check must stay live across SDK versions at runtime.
        parts: tuple[Any, ...] = transport
        if len(parts) == 2:
            read, write = parts
        elif len(parts) == 3:
            read, write, _ = parts
        else:
            raise SmokeCheckFailed(f"unexpected streamablehttp_client transport tuple: {transport!r}")
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def _without_none(**kwargs: Any) -> dict[str, Any]:
    """Drop ``None``-valued kwargs so an omitted optional arg is truly ABSENT."""
    return {key: value for key, value in kwargs.items() if value is not None}


def _joined_text(result: CallToolResult) -> str:
    """Join every ``.text`` off a tool result's content blocks (P8a-9 fix, inlined).

    ``result.content`` is ``list[mcp.types.TextContent]`` — pydantic objects, not
    directly JSON-parsable as a list. A structured-output tool's pydantic model is
    serialized by FastMCP into a SINGLE TextContent whose ``.text`` IS the JSON;
    a plain-``str``-returning tool likewise gets one TextContent with the raw text.
    """
    parts = []
    for block in result.content:
        text = getattr(block, "text", None)
        parts.append(text if text is not None else str(block))
    return "\n".join(parts)


async def call_tool(session: ClientSession, name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Call ``name`` with ``arguments`` and return the RAW result (isError intact)."""
    return await session.call_tool(name, arguments=arguments)


def require_no_tool_error(result: CallToolResult, check_name: str) -> None:
    """Raise loudly if the server reported this call as a tool-level error."""
    if result.isError:
        raise SmokeCheckFailed(f"{check_name}: tool call returned isError=True: {_joined_text(result)}")


def parse_json_result(result: CallToolResult, check_name: str) -> Any:
    """Require no tool error, then JSON-decode the joined text content."""
    require_no_tool_error(result, check_name)
    text = _joined_text(result)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SmokeCheckFailed(f"{check_name}: could not parse JSON from tool text: {text!r}") from exc


def parse_finding_rows(rendered: str) -> list[dict[str, str]]:
    """Parse every ``- [#N status] subject (id ..., kind ..., area ..., ...)`` row."""
    rows = []
    for line in rendered.splitlines():
        match = _FINDING_ROW_PATTERN.match(line)
        if match is None:
            raise SmokeCheckFailed(f"finding row does not match the expected render shape: {line!r}")
        rows.append(match.groupdict())
    return rows


def parse_finding_detail(rendered: str) -> dict[str, str]:
    """Parse a SINGLE finding's ``get``/``chain_head`` detail render.

    P8d Wave 4a (finding #38, hardened by audit-w4a finding #1): unlike
    ``query``'s summarised rows, ``get``/``chain_head`` render the row, then a
    ``body:`` label followed by the body VERBATIM inside a backtick fence
    (sized to survive any backtick run embedded in the body itself, mirroring
    ``search.py``'s own source-body fence), then the single-line
    ``created_at:``/``provenance:`` trailers. Only the FIRST line is the
    finding-row shape ``parse_finding_rows`` expects; the fenced body is never
    re-parsed as a row or a trailer (that would raise on a hostile body
    engineered to contain a row-shaped or trailer-shaped line).
    """
    lines = rendered.splitlines()
    if not lines:
        raise SmokeCheckFailed("finding detail render is empty")
    row_match = _FINDING_ROW_PATTERN.match(lines[0])
    if row_match is None:
        raise SmokeCheckFailed(f"finding detail: row line does not match expected shape: {lines[0]!r}")
    if len(lines) < 2 or lines[1] != "body:":
        raise SmokeCheckFailed(f"finding detail: no 'body:' label line found in: {rendered!r}")
    if len(lines) < 3 or not lines[2] or set(lines[2]) != {"`"}:
        raise SmokeCheckFailed(f"finding detail: no opening body fence found in: {rendered!r}")
    fence = lines[2]
    try:
        close_index = lines.index(fence, 3)
    except ValueError as exc:
        raise SmokeCheckFailed(
            f"finding detail: no matching closing body fence found in: {rendered!r}"
        ) from exc
    trailer_lines = lines[close_index + 1 :]
    if not any(line.startswith("created_at: ") for line in trailer_lines):
        raise SmokeCheckFailed(f"finding detail: no 'created_at:' line found in: {rendered!r}")
    if not any(line.startswith("provenance: ") for line in trailer_lines):
        raise SmokeCheckFailed(f"finding detail: no 'provenance:' line found in: {rendered!r}")
    return row_match.groupdict()


# ---------------------------------------------------------------------------
# Check 1 — connection + tools/list
# ---------------------------------------------------------------------------
async def check_tools(session: ClientSession, *, mechanics: bool) -> None:
    """Assert (full mode) or report (mechanics mode) the tool surface."""
    response = await session.list_tools()
    tool_names = {tool.name for tool in response.tools}
    print(f"PASS: connected + tools/list ({len(tool_names)} tools total)")

    new_present = sorted(NEW_P8B_TOOL_NAMES & tool_names)
    new_missing = sorted(NEW_P8B_TOOL_NAMES - tool_names)
    legacy_present = sorted(PRE_EXISTING_TOOL_NAMES & tool_names)
    legacy_missing = sorted(PRE_EXISTING_TOOL_NAMES - tool_names)

    if mechanics:
        print(f"  [mechanics] new P8b tools found ({len(new_present)}/4): {new_present}")
        if new_missing:
            print(f"  [mechanics] new P8b tools NOT YET present (expected pre-redeploy): {new_missing}")
        print(f"  [mechanics] pre-existing tools found: {len(legacy_present)}/{len(PRE_EXISTING_TOOL_NAMES)}")
        if legacy_missing:
            print(f"  [mechanics] pre-existing tools MISSING (unexpected!): {legacy_missing}")
        print(f"  [mechanics] full tool set: {sorted(tool_names)}")
        return

    if new_missing:
        raise SmokeCheckFailed(
            f"missing new P8b tool(s): {new_missing}; full tool set was: {sorted(tool_names)}"
        )
    print(f"PASS: all 4 new P8b tools present: {sorted(NEW_P8B_TOOL_NAMES)}")

    if legacy_missing:
        raise SmokeCheckFailed(
            f"missing pre-existing tool(s): {legacy_missing}; full tool set was: {sorted(tool_names)}"
        )
    print(f"PASS: all {len(PRE_EXISTING_TOOL_NAMES)} pre-existing tools still present")


# ---------------------------------------------------------------------------
# Check 2 — lore_verify round-trips
# ---------------------------------------------------------------------------
async def check_verify_confirmed(session: ClientSession) -> None:
    """A known-true claim confirms."""
    arguments = _without_none(
        qualified_name=VERIFY_TRUE_QUALIFIED_NAME,
        expected_file_path=VERIFY_TRUE_FILE_PATH,
    )
    result = await call_tool(session, "lore_verify", arguments)
    payload = parse_json_result(result, "lore_verify (confirmed)")
    if payload.get("status") != "confirmed":
        raise SmokeCheckFailed(f"lore_verify confirmed case: expected status=confirmed, got: {payload}")
    print(
        f"PASS: lore_verify(qualified_name={VERIFY_TRUE_QUALIFIED_NAME!r}, "
        f"expected_file_path={VERIFY_TRUE_FILE_PATH!r}) -> confirmed"
    )


async def check_verify_mismatch(session: ClientSession) -> None:
    """A false signature claim on the same symbol mismatches, naming the actual header."""
    arguments = _without_none(
        qualified_name=VERIFY_TRUE_QUALIFIED_NAME,
        expected_signature_fragment=VERIFY_FALSE_SIGNATURE_FRAGMENT,
    )
    result = await call_tool(session, "lore_verify", arguments)
    payload = parse_json_result(result, "lore_verify (mismatch)")
    if payload.get("status") != "mismatch":
        raise SmokeCheckFailed(f"lore_verify mismatch case: expected status=mismatch, got: {payload}")
    mismatches = payload.get("mismatches") or []
    if not mismatches:
        raise SmokeCheckFailed(f"lore_verify mismatch case: status=mismatch but mismatches=[]: {payload}")
    actual_header = mismatches[0].get("actual", "")
    print(
        f"PASS: lore_verify(qualified_name={VERIFY_TRUE_QUALIFIED_NAME!r}, "
        f"expected_signature_fragment={VERIFY_FALSE_SIGNATURE_FRAGMENT!r}) -> mismatch "
        f"(actual header: {actual_header!r})"
    )


async def check_verify_not_found(session: ClientSession) -> None:
    """A garbage name is a plain not_found RESULT — never a tool error."""
    arguments = _without_none(qualified_name=VERIFY_GARBAGE_QUALIFIED_NAME)
    result = await call_tool(session, "lore_verify", arguments)
    require_no_tool_error(result, "lore_verify (not_found)")
    payload = json.loads(_joined_text(result))
    if payload.get("status") != "not_found":
        raise SmokeCheckFailed(f"lore_verify garbage-name case: expected status=not_found, got: {payload}")
    print(
        f"PASS: lore_verify(qualified_name={VERIFY_GARBAGE_QUALIFIED_NAME!r}) -> not_found "
        f"(isError=False — a plain result, not a tool error)"
    )


# ---------------------------------------------------------------------------
# Check 3 — lore_read round-trip
# ---------------------------------------------------------------------------
async def check_read(session: ClientSession) -> None:
    """Read a known span; assert structure (provenance header, non-empty text)."""
    arguments = {
        "tier": READ_TIER,
        "path": READ_PATH,
        "line_start": READ_LINE_START,
        "line_end": READ_LINE_END,
    }
    result = await call_tool(session, "lore_read", arguments)
    payload = parse_json_result(result, "lore_read")

    required_fields = ("tier", "path", "line_start", "line_end", "text", "stale", "integrity_verified")
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        raise SmokeCheckFailed(f"lore_read: response missing field(s) {missing_fields}: {payload}")
    if not payload["text"].strip():
        raise SmokeCheckFailed(f"lore_read: text is empty: {payload}")

    # StoreFileSpan.header is a plain @property (not serialized in the JSON body) —
    # reconstruct it from the returned fields per the documented
    # "[SOURCE:{tier}:{path}:{line_start}-{line_end}]" template (store_read.py).
    provenance_header = (
        f"[SOURCE:{payload['tier']}:{payload['path']}:{payload['line_start']}-{payload['line_end']}]"
    )
    print(
        f"PASS: lore_read(tier={READ_TIER!r}, path={READ_PATH!r}, "
        f"lines {READ_LINE_START}-{READ_LINE_END}) -> {provenance_header}, "
        f"non-empty text ({len(payload['text'])} chars), stale={payload['stale']}, "
        f"integrity_verified={payload['integrity_verified']}"
    )


# ---------------------------------------------------------------------------
# Check 4 — lore_diff round-trips
# ---------------------------------------------------------------------------
async def check_diff(session: ClientSession) -> None:
    """List snapshots; if any exist, diff since the newest against live 'now'."""
    list_result = await call_tool(session, "lore_diff", {})
    require_no_tool_error(list_result, "lore_diff (list mode)")
    listing_text = _joined_text(list_result).strip()
    if not listing_text:
        raise SmokeCheckFailed("lore_diff list mode: rendered text is empty")

    if listing_text == NO_SNAPSHOTS_SENTINEL:
        print("PASS: lore_diff() list mode -> 0 snapshots recorded (structure honored, count 0)")
        return

    all_lines = listing_text.splitlines()
    # P8d Wave 4a (finding #8): a trailing "(showing N of M — raise limit for
    # more)" line is appended (never "- "-prefixed) when more snapshots exist
    # than were shown — an honest pagination notice, not a malformed row.
    pagination_trailer = [line for line in all_lines if line.startswith("(showing ")]
    rows = [line for line in all_lines if line not in pagination_trailer]
    malformed_rows = [row for row in rows if not row.startswith("- ")]
    if malformed_rows:
        raise SmokeCheckFailed(f"lore_diff list mode: row(s) not '- '-prefixed: {malformed_rows}")
    newest_row = rows[0]
    print(f"PASS: lore_diff() list mode -> {len(rows)} snapshot row(s); newest: {newest_row}")
    if pagination_trailer:
        print(f"  pagination: {pagination_trailer[0]}")

    newest_id_match = _SNAPSHOT_ROW_ID_PATTERN.match(newest_row)
    if newest_id_match is None:
        raise SmokeCheckFailed(f"lore_diff list mode: could not extract a snapshot id from: {newest_row!r}")
    newest_snapshot_id = newest_id_match.group(1)

    diff_result = await call_tool(session, "lore_diff", {"since": newest_snapshot_id})
    require_no_tool_error(diff_result, f"lore_diff(since={newest_snapshot_id!r})")
    diff_text = _joined_text(diff_result).strip()
    diff_lines = diff_text.splitlines()
    if len(diff_lines) < 2 or not diff_lines[1].startswith("files:"):
        raise SmokeCheckFailed(
            f"lore_diff(since={newest_snapshot_id!r}): expected a 'files: ...' counts line "
            f"as line 2 of the render, got: {diff_text!r}"
        )
    print(f"PASS: lore_diff(since={newest_snapshot_id!r}) -> rendered without error")
    print(f"  counts: {diff_lines[1]}")


# ---------------------------------------------------------------------------
# Check 5 — lore_findings: the dogfood leg
# ---------------------------------------------------------------------------
async def check_findings(session: ClientSession) -> None:
    """File the project's real first finding through the new surface, then round-trip it.

    STOPS at 'acknowledge' — this is a genuine, still-open friction finding; it is
    never resolved or wontfixed by this script.
    """
    report_arguments = {
        "action": "report",
        "kind": FINDING_KIND,
        "area": FINDING_AREA,
        "category": FINDING_CATEGORY,
        "created_by": FINDING_CREATED_BY,
        "subject": FINDING_SUBJECT,
        "body": FINDING_BODY,
    }
    report_result = await call_tool(session, "lore_findings", report_arguments)
    require_no_tool_error(report_result, "lore_findings (report)")
    report_text = _joined_text(report_result).strip()
    report_match = _REPORT_RENDER_PATTERN.match(report_text)
    if report_match is None:
        raise SmokeCheckFailed(f"lore_findings report: unexpected render: {report_text!r}")
    finding_number = int(report_match.group(1))
    finding_id = report_match.group(2)
    print(
        f"PASS: lore_findings(action='report', subject={FINDING_SUBJECT!r}) -> "
        f"finding #{finding_number} (id {finding_id}), status open"
    )

    query_result = await call_tool(session, "lore_findings", {"action": "query", "status": "open"})
    require_no_tool_error(query_result, "lore_findings (query status=open)")
    query_text = _joined_text(query_result).strip()
    query_rows = parse_finding_rows(query_text)
    query_numbers = [int(row["number"]) for row in query_rows]
    if query_numbers != sorted(query_numbers):
        raise SmokeCheckFailed(
            f"lore_findings query status=open: rows not ordered ascending: {query_numbers}"
        )
    if finding_number not in query_numbers:
        raise SmokeCheckFailed(
            f"lore_findings query status=open: finding #{finding_number} not among returned "
            f"rows: {query_text!r}"
        )
    print(
        f"PASS: lore_findings(action='query', status='open') -> finding #{finding_number} present, "
        f"ordered ascending among {len(query_numbers)} open finding(s)"
    )

    get_result = await call_tool(
        session, "lore_findings", {"action": "get", "id_or_number": finding_number}
    )
    require_no_tool_error(get_result, "lore_findings (get)")
    get_text = _joined_text(get_result).strip()
    # P8d Wave 4a (finding #38): get renders the row PLUS body/provenance detail.
    get_row = parse_finding_detail(get_text)
    if int(get_row["number"]) != finding_number:
        raise SmokeCheckFailed(f"lore_findings get #{finding_number}: unexpected render: {get_text!r}")
    if get_row["subject"] != FINDING_SUBJECT:
        raise SmokeCheckFailed(
            f"lore_findings get #{finding_number}: subject mismatch, got {get_row['subject']!r}"
        )
    if FINDING_BODY not in get_text:
        raise SmokeCheckFailed(
            f"lore_findings get #{finding_number}: body not rendered verbatim: {get_text!r}"
        )
    print(f"PASS: lore_findings(action='get', id_or_number={finding_number}) -> same finding + body")

    chain_result = await call_tool(
        session, "lore_findings", {"action": "chain_head", "id_or_number": finding_number}
    )
    require_no_tool_error(chain_result, "lore_findings (chain_head)")
    chain_text = _joined_text(chain_result).strip()
    forked = "(chain FORKED" in chain_text
    chain_main_text = chain_text.split("\n(chain FORKED", 1)[0]
    chain_row = parse_finding_detail(chain_main_text)
    if int(chain_row["number"]) != finding_number:
        raise SmokeCheckFailed(
            f"lore_findings chain_head #{finding_number}: unexpected render: {chain_text!r}"
        )
    if forked:
        raise SmokeCheckFailed(
            f"lore_findings chain_head #{finding_number}: unexpectedly forked on a fresh "
            f"finding: {chain_text!r}"
        )
    print(f"PASS: lore_findings(action='chain_head', id_or_number={finding_number}) -> itself, forked False")

    ack_result = await call_tool(
        session,
        "lore_findings",
        {"action": "acknowledge", "id_or_number": finding_number, "actor": FINDING_ACK_ACTOR},
    )
    require_no_tool_error(ack_result, "lore_findings (acknowledge)")
    ack_text = _joined_text(ack_result).strip()
    expected_ack_text = _TRANSITION_RENDER_TEMPLATE.format(
        number=finding_number, status="acknowledged", actor=FINDING_ACK_ACTOR
    )
    if ack_text != expected_ack_text:
        raise SmokeCheckFailed(
            f"lore_findings acknowledge #{finding_number}: expected {expected_ack_text!r}, got {ack_text!r}"
        )
    print(
        f"PASS: lore_findings(action='acknowledge', id_or_number={finding_number}, "
        f"actor={FINDING_ACK_ACTOR!r}) -> status acknowledged "
        f"(STOPPING HERE — genuinely open finding, never resolved/wontfixed by this script)"
    )


# ---------------------------------------------------------------------------
# Check 6 — one legacy-tool sanity call
# ---------------------------------------------------------------------------
async def check_legacy_index_status(session: ClientSession) -> None:
    """lore_index (pre-existing tool, P8d Wave 3 merge) still parses as a healthy object."""
    result = await call_tool(session, "lore_index", {})
    payload = parse_json_result(result, "lore_index")
    if not isinstance(payload, dict) or not payload:
        raise SmokeCheckFailed(f"lore_index: expected a non-empty JSON object, got: {payload!r}")
    print(f"PASS: lore_index() parses -> {json.dumps(payload, sort_keys=True)}")


# ---------------------------------------------------------------------------
# Check 7 — P8c: lore_index carries the boot token-calibration section
# ---------------------------------------------------------------------------
# The FIVE serving states CalibrationEngine.status()['state'] can report (copied
# verbatim from loremaster.calibration.engine STATE_* so a vocabulary drift there
# fails this script loudly). The deployed exit criterion: lore_index visibly
# shows the calibration state (cached / measured / cached_retrying, and
# drift_adopted under synthetic drift), so the state string must surface verbatim.
# P8d Wave 3 (finding #4): integrity_failed is the 5th state — an integrity
# mismatch is no longer indistinguishable from never-probed ``cached``.
CALIBRATION_STATES = frozenset(
    {"cached", "measured", "drift_adopted", "cached_retrying", "integrity_failed"}
)


async def check_index_status_calibration(session: ClientSession) -> None:
    """lore_index carries a calibration section with a valid state + constants."""
    result = await call_tool(session, "lore_index", {})
    payload = parse_json_result(result, "lore_index (calibration)")
    calibration = payload.get("calibration")
    if not isinstance(calibration, dict):
        raise SmokeCheckFailed(
            f"lore_index: expected a 'calibration' section (a dict), got: {calibration!r} "
            f"— the P8c calibration engine must be wired + started at boot"
        )
    state = calibration.get("state")
    if state not in CALIBRATION_STATES:
        raise SmokeCheckFailed(
            f"lore_index calibration.state {state!r} is not one of the "
            f"serving states {sorted(CALIBRATION_STATES)}"
        )
    for field in ("served_constant", "committed_constant"):
        if not isinstance(calibration.get(field), (int, float)):
            raise SmokeCheckFailed(
                f"lore_index calibration.{field} must be a number, got: "
                f"{calibration.get(field)!r}"
            )
    print(
        f"PASS: lore_index() carries calibration -> state={state!r}, "
        f"served={calibration['served_constant']}, committed={calibration['committed_constant']}, "
        f"model={calibration.get('model')!r}"
    )


# ---------------------------------------------------------------------------
# Run modes
# ---------------------------------------------------------------------------
async def run_mechanics_check() -> None:
    """--mechanics: connection + tools/list (no new-tool assertion) + checks 6-7 only.

    The P8c calibration section (check 7) is a READ-ONLY ``lore_index_status`` probe
    with no finding-filing side effects, so it belongs in the mechanics path too —
    without it the default mode was silently weaker (a server missing the calibration
    section passed mechanics), the gap flagged by REPORT-auditor-wiring-1 F2.
    """
    async with connect(MCP_SERVER_URL) as session:
        await check_tools(session, mechanics=True)
        await check_legacy_index_status(session)
        await check_index_status_calibration(session)


async def run_full_smoke() -> None:
    """Default: the full P8b exit assertion run (post-redeploy)."""
    async with connect(MCP_SERVER_URL) as session:
        await check_tools(session, mechanics=False)
        await check_verify_confirmed(session)
        await check_verify_mismatch(session)
        await check_verify_not_found(session)
        await check_read(session)
        await check_diff(session)
        await check_findings(session)
        await check_legacy_index_status(session)
        await check_index_status_calibration(session)


def main() -> int:
    """Entry point: run one of the two modes, exit 0 all-pass / 1 any-fail."""
    parser = argparse.ArgumentParser(
        description=(
            "P8b exit smoke against the live lore MCP server "
            f"({MCP_SERVER_URL}). Default mode runs the full assertion set "
            "(post-redeploy); --mechanics validates only the connection + "
            "tools/list + one legacy call (safe pre-redeploy)."
        )
    )
    parser.add_argument(
        "--mechanics",
        action="store_true",
        help="Run only the connection/tools-list mechanics check (no new-tool assertions).",
    )
    args = parser.parse_args()

    try:
        if args.mechanics:
            asyncio.run(run_mechanics_check())
        else:
            asyncio.run(run_full_smoke())
    except Exception as exc:  # noqa: BLE001 - top-level: surface EVERYTHING, loudly
        print(f"\nFAIL: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
