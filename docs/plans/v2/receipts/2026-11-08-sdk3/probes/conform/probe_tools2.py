"""conform-sdk3-66 step-5 probe #2 (governed reads + a COMPLETE rollup walk), over MCP streamable-HTTP.

1. Registers a throwaway identity on the prod COPY (the only write; the DB is minted and reaped) and keeps the
   served ``<name>:<secret>`` capability in memory ONLY: every text this script prints or saves is redacted.
2. Calls lore_comms drain, lore_recall and a capability-bearing lore_tasks rollup with that capability.
3. Walks lore_tasks rollup from the epoch to exhaustion (page limit 20) and checks, per cursor-paged leg, that the
   DISTINCT ids served over the whole walk equal the leg total the FIRST page declares ("showing n of TOTAL") —
   i.e. no row is SKIPPED — and that every cursor is in nine-digit form and never moves backwards.
4. Repeats lore_search to separate first-call warmup from steady-state latency.
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

NINE_DIGIT_CURSOR = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{9}Z")
NEXT_CURSOR = re.compile(r"^next cursor: (\S+)$", re.MULTILINE)
TASK_ID = re.compile(r"^- \[[^\]]+\] .*\(id ([0-9a-f]{32}), owner ", re.MULTILINE)
FINDING_NUMBER = re.compile(r"^- \[#(\d+) ", re.MULTILINE)
LEG_TOTAL = re.compile(r"^(tasks transitioned|findings filed) \((?:showing \d+ of (\d+)|(\d+))", re.MULTILINE)
PAGE_LIMIT = 20
STEP_CAP = 400
HEAD_CHARS = 700


class RedactingProbe:
    """Times tool calls and records them with the capability secret redacted."""

    def __init__(self, session: ClientSession, out_path: Path) -> None:
        self.session = session
        self.out_path = out_path
        self.secret: str | None = None
        self.records: list[dict] = []

    def redact(self, text: str) -> str:
        """Replace the capability token wherever it appears."""
        return text.replace(self.secret, "<capability-redacted>") if self.secret else text

    async def call(self, tool: str, arguments: dict, *, quiet: bool = False) -> str:
        """Call a tool; return the RAW text; record and print the redacted text."""
        started = time.perf_counter()
        result = await self.session.call_tool(tool, arguments)
        latency_s = time.perf_counter() - started
        text = "\n".join(getattr(block, "text", "") for block in result.content)
        shown_args = {k: ("<capability-redacted>" if k == "capability" else v) for k, v in arguments.items()}
        record = {"tool": tool, "arguments": shown_args, "latency_s": round(latency_s, 3),
                  "is_error": bool(result.isError), "text": self.redact(text)}
        self.records.append(record)
        with self.out_path.open("a") as handle:
            handle.write(json.dumps(record) + "\n")
        if not quiet:
            print(f"=== {tool} {json.dumps(shown_args)} · {latency_s:.3f}s · isError={result.isError}")
            print(self.redact(text)[:HEAD_CHARS])
        return text


async def complete_walk(probe: RedactingProbe) -> dict:
    """Walk the rollup from the epoch until the cursor stops advancing; check for skipped rows."""
    since: str | None = None
    declared: dict[str, int] = {}
    served_tasks: set[str] = set()
    served_findings: set[int] = set()
    cursors: list[str] = []
    pages = 0
    rows_served = 0
    for _ in range(STEP_CAP):
        arguments: dict = {"action": "rollup", "limit": PAGE_LIMIT}
        if since is not None:
            arguments["since"] = since
        text = await probe.call("lore_tasks", arguments, quiet=True)
        pages += 1
        if not declared:
            for leg, of_total, plain_total in LEG_TOTAL.findall(text):
                declared[leg] = int(of_total or plain_total)
        tasks = TASK_ID.findall(text)
        findings = [int(n) for n in FINDING_NUMBER.findall(text)]
        rows_served += len(tasks) + len(findings)
        served_tasks.update(tasks)
        served_findings.update(findings)
        match = NEXT_CURSOR.search(text)
        if not match:
            break
        cursor = match.group(1)
        cursors.append(cursor)
        if cursor == since:
            break
        since = cursor
    monotonic = all(a < b for a, b in zip(cursors, cursors[1:]))
    return {
        "pages": pages,
        "rows_served_total": rows_served,
        "declared_leg_totals_at_epoch": declared,
        "distinct_tasks_served": len(served_tasks),
        "distinct_findings_served": len(served_findings),
        "cursor_count": len(cursors),
        "all_cursors_nine_digit": all(NINE_DIGIT_CURSOR.fullmatch(c) for c in cursors),
        "cursors_strictly_increasing_until_final": monotonic or (len(cursors) >= 2 and cursors[-1] == cursors[-2]
                                                                 and all(a < b for a, b in zip(cursors[:-1], cursors[1:-1]))),
        "first_cursor": cursors[0] if cursors else None,
        "last_cursor": cursors[-1] if cursors else None,
        "hit_step_cap": pages >= STEP_CAP,
    }


async def main() -> None:
    """Run probe #2."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    async with streamablehttp_client(args.url, timeout=120, sse_read_timeout=600) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            probe = RedactingProbe(session, args.out)
            text = await probe.call(
                "lore_comms",
                {"action": "register", "agent": "conform66-probe", "role": "conformance-probe",
                 "session": "conform66-copy", "cadence": "≤30m"},
                quiet=True,
            )
            token = re.search(r"conform66-probe:[A-Za-z0-9_\-.~+/=]+", text)
            probe.secret = token.group(0) if token else None
            print("=== lore_comms register · capability minted:", probe.secret is not None)
            print(probe.redact(text)[:HEAD_CHARS])
            capability = {"capability": probe.secret} if probe.secret else {}
            await probe.call("lore_comms", {"action": "drain", "agent": "conform66-probe", "peek": True, **capability})
            await probe.call("lore_comms", {"action": "fleet", "agent": "conform66-probe", "limit": 5})
            await probe.call("lore_recall", {"query": "surreal stores systemd ports", "k": 3, **capability})
            await probe.call("lore_tasks", {"action": "rollup", "limit": 5, **capability})
            walk = await complete_walk(probe)
            print("COMPLETE_WALK", json.dumps(walk))
            for query in ("where the rollup cursor is minted", "where the rollup cursor is minted",
                          "the restore driver's import endpoint guard"):
                await probe.call("lore_search", {"query": query, "k": 4})
            slowest = max(probe.records, key=lambda record: record["latency_s"])
            print("SLOWEST", slowest["tool"], json.dumps(slowest["arguments"]), slowest["latency_s"])


if __name__ == "__main__":
    asyncio.run(main())
