"""Shared fakes for the finding #58 agent_loop() probe.

Not a pytest suite -- evaluation_harness_p8a.py has no test suite (per its
spawn brief / finding #58 diagnosis), so this is a scratch-dir receipt
script. It builds canned Anthropic-shaped responses and a canned MCP
connection so agent_loop() can run end-to-end with zero network/API calls,
then snapshots what it sends back to "Anthropic" (via the fake
messages.create) so the pre-fix and post-fix harness versions can be
byte-compared without needing agent_loop() to expose its internal
`messages` list.
"""

from __future__ import annotations

import copy


class FakeBlock:
    """Stands in for an anthropic SDK content block (ToolUseBlock/TextBlock)."""

    def __init__(self, type, **kwargs):
        self.type = type
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeUsage:
    def __init__(
        self,
        input_tokens=10,
        output_tokens=20,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    ):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens
        self.cache_read_input_tokens = cache_read_input_tokens


class FakeResponse:
    def __init__(self, content, stop_reason, usage=None):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = usage if usage is not None else FakeUsage()


class FakeMessagesEndpoint:
    """Stands in for `client.messages` -- `.create()` pops the next canned
    response and snapshots the `messages` kwarg it was called with.

    The snapshot MUST be a deep copy: agent_loop() holds one `messages` list
    and mutates it (via .append()) across the whole loop, so capturing the
    live reference would show every call's kwarg as the FINAL history
    instead of the history at call time.
    """

    def __init__(self, canned_responses):
        self._queue = list(canned_responses)
        self.calls = []

    def create(self, **kwargs):
        snapshot = dict(kwargs)
        snapshot["messages"] = copy.deepcopy(kwargs["messages"])
        self.calls.append(snapshot)
        return self._queue.pop(0)


class FakeClient:
    def __init__(self, canned_responses):
        self.messages = FakeMessagesEndpoint(canned_responses)


class FakeTextContent:
    """Stands in for mcp.types.TextContent (what MCPConnection.call_tool()
    returns per real MCP server -- see _serialize_tool_result's docstring)."""

    def __init__(self, text):
        self.type = "text"
        self.text = text


class FakeConnection:
    """Stands in for connections_p8a's MCPConnection -- records call order
    so the probe can assert every tool_use block actually got executed."""

    def __init__(self, tool_outputs):
        self._tool_outputs = tool_outputs
        self.call_log = []

    async def call_tool(self, name, tool_input):
        self.call_log.append([name, tool_input])
        return [FakeTextContent(self._tool_outputs[name])]


def serialize_messages(messages):
    """Turn one snapshot of agent_loop()'s `messages` history into a plain,
    JSON-diffable structure (dicts/lists/strs only)."""
    out = []
    for message in messages:
        content = message["content"]
        if isinstance(content, str):
            out.append({"role": message["role"], "content": content})
            continue
        blocks = []
        for block in content:
            if isinstance(block, dict):
                blocks.append(dict(block))
            else:
                entry = {"type": block.type}
                if hasattr(block, "id"):
                    entry["id"] = block.id
                if hasattr(block, "name"):
                    entry["name"] = block.name
                if hasattr(block, "input"):
                    entry["input"] = block.input
                if hasattr(block, "text"):
                    entry["text"] = block.text
                blocks.append(entry)
        out.append({"role": message["role"], "content": blocks})
    return out


def single_tool_scenario():
    """One tool_use block per turn -- the shape every prior run (P8a
    11-pair baseline, the 35-pair flip-eval) actually exercised. The fix
    must reproduce this shape byte-for-byte."""
    tool_use = FakeBlock(
        "tool_use", id="toolu_single_1", name="lore_search", input={"query": "foo"}
    )
    resp1 = FakeResponse(content=[tool_use], stop_reason="tool_use")
    final_text = FakeBlock("text", text="<response>42</response>")
    resp2 = FakeResponse(content=[final_text], stop_reason="end_turn")
    client = FakeClient([resp1, resp2])
    connection = FakeConnection({"lore_search": "search result text"})
    return client, connection


def parallel_tool_scenario():
    """Two tool_use blocks in ONE turn -- the shape that crashed the P8d'
    gate re-run at task 21/35 (finding #58)."""
    tool_use_a = FakeBlock(
        "tool_use", id="toolu_parallel_a", name="lore_search", input={"query": "foo"}
    )
    tool_use_b = FakeBlock(
        "tool_use",
        id="toolu_parallel_b",
        name="lore_read",
        input={"tier": "custom", "path": "x.py"},
    )
    resp1 = FakeResponse(content=[tool_use_a, tool_use_b], stop_reason="tool_use")
    final_text = FakeBlock("text", text="<response>done</response>")
    resp2 = FakeResponse(content=[final_text], stop_reason="end_turn")
    client = FakeClient([resp1, resp2])
    connection = FakeConnection(
        {"lore_search": "search result text", "lore_read": "read result text"}
    )
    return client, connection
