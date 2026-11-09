"""conform-sdk3-66 step-5 probe: drive the served lore tools over the MCP streamable-HTTP endpoint.

Runs inside the conformance image (the baked ``mcp`` client) against a conform66 server bound on
127.0.0.1:<port> whose config points at the minted prod-copy DB on the TEST store (:18000).

For every call it records: tool, arguments, wall-clock latency, isError, and the served text.
It writes one JSON line per call to ``--out`` and prints a short head per call to stdout.

The lore_tasks rollup cursor walk: bootstrap (no ``since``), then follow each ``next cursor`` until a
page serves no rows or the step cap is hit; every served row's identity line is collected per page so
a re-served row (the same identity on two pages) is detectable, and every cursor is checked against
the nine-digit fractional-second form.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# A cursor in the nine-digit form: ISO-8601 with exactly nine fractional-second digits + an offset.
NINE_DIGIT_CURSOR = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{9}(?:Z|[+-]\d{2}:\d{2})")
# Any ISO-ish cursor following the words "next cursor" (form-agnostic, so a wrong form is still captured).
NEXT_CURSOR = re.compile(r"next cursor\W{0,20}([0-9T:.\-+Z]{19,40})", re.IGNORECASE)
HEAD_CHARS = 600
ROLLUP_STEP_CAP = 12
ROLLUP_PAGE_LIMIT = 20


class ToolProbe:
    """Calls served tools, timing each, and appends a JSON record per call."""

    def __init__(self, session: ClientSession, out_path: Path) -> None:
        self.session = session
        self.out_path = out_path
        self.records: list[dict] = []

    async def call(self, tool: str, arguments: dict) -> str:
        """Call one tool; record latency + served text; return the text."""
        started = time.perf_counter()
        result = await self.session.call_tool(tool, arguments)
        latency_s = time.perf_counter() - started
        text = "\n".join(getattr(block, "text", "") for block in result.content)
        record = {
            "tool": tool,
            "arguments": arguments,
            "latency_s": round(latency_s, 3),
            "is_error": bool(result.isError),
            "text": text,
        }
        self.records.append(record)
        with self.out_path.open("a") as handle:
            handle.write(json.dumps(record) + "\n")
        print(f"=== {tool} {json.dumps(arguments)} · {latency_s:.3f}s · isError={result.isError}")
        print(text[:HEAD_CHARS])
        return text


CURSOR_PAGED_LEGS = ("tasks transitioned", "findings filed", "reports registered")


def extract_rows(text: str) -> list[str]:
    """Return the ``- …`` row lines of the three cursor-paged legs only, prefixed by their leg.

    The message / fleet-health / brief-skew sections that follow are NOT read by the next cursor
    (server.py ``_rollup`` R44 note), so a row repeated there is not a re-serve and is excluded.
    """
    rows: list[str] = []
    leg: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        header = next((name for name in CURSOR_PAGED_LEGS if stripped.startswith(name)), None)
        if header is not None:
            leg = header
            continue
        if leg is not None and stripped.startswith("- "):
            rows.append(f"{leg} | {stripped}")
        elif not stripped.startswith("- "):
            leg = None
    return rows


async def rollup_walk(probe: ToolProbe) -> dict:
    """Walk lore_tasks rollup by its served cursor; report re-served rows + cursor forms."""
    since: str | None = None
    seen: dict[str, int] = {}
    reserved: list[tuple[int, str]] = []
    cursors: list[str] = []
    for step in range(ROLLUP_STEP_CAP):
        arguments: dict = {"action": "rollup", "limit": ROLLUP_PAGE_LIMIT}
        if since is not None:
            arguments["since"] = since
        text = await probe.call("lore_tasks", arguments)
        rows = extract_rows(text)
        for row in rows:
            if row in seen:
                reserved.append((step, row))
            seen[row] = step
        match = NEXT_CURSOR.search(text)
        if not match:
            break
        cursor = match.group(1)
        cursors.append(cursor)
        if cursor == since or not rows:
            break
        since = cursor
    return {
        "steps": len(cursors),
        "rows_seen": len(seen),
        "reserved_rows": reserved,
        "cursors": cursors,
        "cursors_nine_digit": [bool(NINE_DIGIT_CURSOR.fullmatch(c)) for c in cursors],
    }


async def main() -> None:
    """Connect, list tools, and run the step-5 battery."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--peek-agent", required=True, help="an EXISTING identity to drain with peek=True")
    parser.add_argument("--peek-session", required=True)
    parser.add_argument("--finding", required=True, type=int)
    args = parser.parse_args()
    async with streamablehttp_client(args.url, timeout=120, sse_read_timeout=600) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS", sorted(tool.name for tool in tools.tools))
            probe = ToolProbe(session, args.out)
            walk = await rollup_walk(probe)
            print("ROLLUP_WALK", json.dumps(walk))
            await probe.call("lore_findings", {"action": "query", "limit": 5})
            await probe.call("lore_findings", {"action": "get", "id_or_number": args.finding})
            await probe.call("lore_comms", {"action": "fleet", "agent": args.peek_agent, "limit": 10})
            await probe.call(
                "lore_comms",
                {"action": "drain", "agent": args.peek_agent, "session": args.peek_session, "peek": True, "limit": 5},
            )
            await probe.call("lore_recall", {"query": "surreal stores systemd ports", "k": 3})
            await probe.call("lore_search", {"query": "where the rollup cursor is minted", "k": 4})
            slowest = max(probe.records, key=lambda record: record["latency_s"])
            print("SLOWEST", slowest["tool"], json.dumps(slowest["arguments"]), slowest["latency_s"])


if __name__ == "__main__":
    asyncio.run(main())
