"""COLD exit-audit probe: dump the full 14-tool surface + instructions + token cost.

Builds the MCP server in-process (no live Surreal needed for list_tools) and
writes a JSON dump of every tool's schema/annotations plus the instructions
block and a voyage-tokenizer cost measurement.
"""
import asyncio
import json
import os
from pathlib import Path

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-probe-not-real")
os.environ.setdefault("LORE_TEI_KEY", "probe")
os.environ.setdefault("SURREAL_USER", "root")
os.environ.setdefault("SURREAL_PASS", "root")

from loremaster.config import LoreConfig
from loremaster.server import LoreServer, build_mcp_server, TOKEN_BUDGET_CALIBRATION
from loresigil.tokens import VoyageTokenCounter

_DIM = 2048


def _config() -> LoreConfig:
    payload = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": "probe", "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": "ws://127.0.0.1:18500/rpc",
            "namespace": "probe",
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": [
            {"tier": "custom", "watch": "live", "path": "/tmp/probe_live", "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {"enabled": False, "observer": "inotify", "debounce_ms": 1500, "reconcile_interval_s": 600},
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
    }
    return LoreConfig.model_validate(payload)


async def main() -> None:
    Path("/tmp/probe_live").mkdir(exist_ok=True)
    mcp = build_mcp_server(LoreServer(_config()))
    instructions = mcp.instructions or ""
    tools = await mcp.list_tools()

    counter = VoyageTokenCounter()

    dump = {"instructions": instructions, "tools": {}}
    # token accounting
    instr_voyage = counter.count(instructions)
    schema_texts = []
    for t in sorted(tools, key=lambda x: x.name):
        ann = t.annotations
        ann_d = None
        if ann is not None:
            ann_d = {
                "readOnlyHint": getattr(ann, "readOnlyHint", None),
                "destructiveHint": getattr(ann, "destructiveHint", None),
                "idempotentHint": getattr(ann, "idempotentHint", None),
                "openWorldHint": getattr(ann, "openWorldHint", None),
                "title": getattr(ann, "title", None),
            }
        entry = {
            "description": t.description or "",
            "inputSchema": t.inputSchema,
            "outputSchema": t.outputSchema,
            "annotations": ann_d,
        }
        dump["tools"][t.name] = entry
        # cost text = description + all param descriptions
        schema_texts.append(t.description or "")
        props = (t.inputSchema or {}).get("properties", {})
        for pname, pspec in props.items():
            schema_texts.append(pname)
            if isinstance(pspec, dict) and pspec.get("description"):
                schema_texts.append(pspec["description"])

    schema_blob = "\n".join(schema_texts)
    schema_voyage = counter.count(schema_blob)
    desc_only_voyage = counter.count("\n".join(t.description or "" for t in tools))

    cal = TOKEN_BUDGET_CALIBRATION
    dump["token_cost"] = {
        "calibration": cal,
        "instructions_voyage": instr_voyage,
        "instructions_claude_equiv": round(instr_voyage * cal),
        "schema_blob_voyage": schema_voyage,
        "schema_blob_claude_equiv": round(schema_voyage * cal),
        "descriptions_only_voyage": desc_only_voyage,
        "descriptions_only_claude_equiv": round(desc_only_voyage * cal),
        "total_surface_voyage": instr_voyage + schema_voyage,
        "total_surface_claude_equiv": round((instr_voyage + schema_voyage) * cal),
    }
    dump["tool_names_sorted"] = sorted(dump["tools"].keys())
    dump["tool_count"] = len(dump["tools"])

    out = Path("/home/ejprice/PycharmProjects/lore/scratchpad/surface_dump.json")
    out.write_text(json.dumps(dump, indent=2, default=str), encoding="utf-8")
    print(f"tools={dump['tool_count']}")
    print("names:", dump["tool_names_sorted"])
    print(json.dumps(dump["token_cost"], indent=2))


asyncio.run(main())
