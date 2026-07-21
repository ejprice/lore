"""Runs the finding #58 scenarios against ONE version of agent_loop().

Usage: <python> run_probe.py <harness_dir> <output_json_path>

`harness_dir` must contain evaluation_harness_p8a.py + connections_p8a.py
side by side (connections_p8a is a load-bearing import even though this
probe never calls create_connection() / opens a real MCP connection).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROBE_DIR))

from harness_common import (  # noqa: E402
    parallel_tool_scenario,
    serialize_messages,
    single_tool_scenario,
)


async def run(harness_dir: str, output_path: str) -> None:
    sys.path.insert(0, harness_dir)
    import evaluation_harness_p8a as harness  # noqa: PLC0415

    results = {}

    for scenario_name, build in (
        ("single", single_tool_scenario),
        ("parallel", parallel_tool_scenario),
    ):
        client, connection = build()
        response_text, tool_metrics, usage_metrics = await harness.agent_loop(
            client, "probe-model", "probe question", [], connection
        )
        results[scenario_name] = {
            "response_text": response_text,
            "tool_call_order": connection.call_log,
            "tool_metrics_counts": {
                name: metrics["count"] for name, metrics in tool_metrics.items()
            },
            "usage_metrics": usage_metrics,
            "api_calls_messages": [
                serialize_messages(call["messages"]) for call in client.messages.calls
            ],
        }

    Path(output_path).write_text(json.dumps(results, indent=2, default=str))
    print(f"wrote {output_path}")


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1], sys.argv[2]))
