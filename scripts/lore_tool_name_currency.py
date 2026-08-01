#!/usr/bin/env python3
"""Derive which lore tool names taught by the global agent instructions are DEAD.

WHY THIS EXISTS
---------------
A ``lore_*`` name written into instructions that agents are told to paste verbatim is a
served surface: an agent learns the tool contract from it. When the tool set is renamed,
those names become corpses, and no gate in any repo can see it — the files live in
``~/.claude/``, outside every project. Finding #292 asked for exactly this: *"prefer a
DERIVED check over another hand-audit of agent files."*

THE DERIVATION (not a hand-list)
--------------------------------
Truth comes from the RUNNING server over MCP ``tools/list`` — never from a constant in
this file, never from a doc. Candidate names come from a BARE, anchor-free scan of the
instruction files, because prose mentions carry no structural anchor (``lore_``-prefixed
patterns miss ``blast_radius``/``tests_for``, which is how this defect stayed invisible).

BOUNDS, stated so this script does not over-claim about itself:
  * It reports names it can RECOGNISE as lore-tool references. A retired concept renamed
    beyond recognition is invisible to it, so a clean run is not proof of currency.
  * ``RETIRED_VOCABULARY`` is a decoder for the *known* rename, not the definition of
    correctness. Its job is to explain a hit, never to bound the search.
  * Legitimate non-lore homonyms exist (``odoo_read_file`` is a real odoo-code tool), so
    every hit is reported with its file:line for INDIVIDUAL adjudication. This script
    produces a worklist requiring judgement, never a verdict.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

CLAUDE_HOME = Path.home() / ".claude"
DEFAULT_SERVER_URL = "http://127.0.0.1:9202/mcp"

# Files that teach agents which lore tools to reach for. Derived by the property
# "instruction surfaces an agent is told to read or paste verbatim", not by taste.
INSTRUCTION_GLOBS = ("CLAUDE.md", "skills/**/*.md", "agents/*.md", "orchestration/*.md")

# Decoder for the known rename. Explains a hit; never bounds the search.
RETIRED_VOCABULARY = {
    "search_code": "lore_search",
    "what_imports": "lore_impact",
    "blast_radius": "lore_impact",
    "tests_for": "lore_impact (its covering-tests view)",
    "read_file": "lore_read",
    "save_memory": "lore_remember",
    "recall_memory": "lore_recall",
}

# ⚠ THESE PATTERNS ARE DELIBERATELY UNANCHORED, AND THAT COST ONE FALSE CLEAR TO LEARN.
# The first draft used `\b` and a "only scan lines mentioning lore" gate. Both failed on
# the exact file that motivated the script:
#   * `\blore_` CANNOT match `lore_search_code` inside `mcp__lore_<slug>__lore_search_code`
#     — `_` is a word character, so there is no word boundary before `lore`.
#   * the "lore" -in-line gate dropped `- `search_code` — semantic code/doc search`, a bare
#     prose line teaching a dead name with the word "lore" nowhere on it.
# It reported a clean CLAUDE.md while nine corpses sat in it. That is the repo's own
# instrument lesson (an anchored pattern misses exactly the prose sites gates cannot see),
# so: NO anchors, and over-report by design. A false positive costs one human glance; a
# false clear is the failure mode this whole script exists to prevent.
_LORE_PREFIXED = re.compile(r"lore_[a-z]+(?:_[a-z]+)*")
_BARE_VOCAB = re.compile(r"(" + "|".join(map(re.escape, RETIRED_VOCABULARY)) + r")")

# Tokens the unanchored scan produces that are not tool references at all: the MCP server
# slug, and this script's own name. Named explicitly so each exemption is visible and
# auditable, rather than hidden inside the pattern where nobody can see what was excluded.
_NOT_TOOL_NAMES = frozenset({"lore_lore", "lore_tool_name_currency"})

# A line may legitimately name a retired tool — a decoder teaching `search_code`->`lore_search`
# must SAY `search_code`. Such a line carries this marker, so the exemption is explicit, visible
# at the site, and greppable. This is an allowlist of SAFE lines, never a pattern that guesses
# intent: repo CLAUDE.md's instrument lesson is that enumerating the forbidden always loses.
_TEACHES_RETIRED_NAMES = "lore-tool-currency: teaches-retired-names"


@dataclass(frozen=True)
class Hit:
    """One recognised lore-tool reference awaiting adjudication."""

    path: Path
    line_no: int
    token: str
    line: str

    def render(self, served: frozenset[str]) -> str:
        """Render this hit with its verdict, or None-verdict when it is served."""
        if self.token.startswith("lore_"):
            verdict = "OK    " if self.token in served else "CORPSE"
            hint = "" if self.token in served else f"  -> {_nearest(self.token, served)}"
        else:
            verdict = "CORPSE"
            hint = f"  -> {RETIRED_VOCABULARY[self.token]}"
        rel = self.path.relative_to(CLAUDE_HOME)
        return f"  {verdict}  {rel}:{self.line_no}  {self.token}{hint}"


def _nearest(token: str, served: frozenset[str]) -> str:
    """Best-effort mapping for a dead lore_-prefixed name."""
    bare = token.removeprefix("lore_")
    if bare in RETIRED_VOCABULARY:
        return RETIRED_VOCABULARY[bare]
    return "no served equivalent found — adjudicate by hand"


def served_tool_names(url: str) -> frozenset[str]:
    """Ask the RUNNING server what it actually serves. The only source of truth here."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "tool-name-currency", "version": "1"},
        },
    }
    request = urllib.request.Request(url, json.dumps(init).encode(), headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        session_id = response.headers.get("mcp-session-id")
        response.read()
    if not session_id:
        raise RuntimeError(f"{url} returned no mcp-session-id; is this an MCP endpoint?")

    headers["mcp-session-id"] = session_id
    notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    urllib.request.urlopen(
        urllib.request.Request(url, json.dumps(notify).encode(), headers), timeout=10
    ).read()

    listing = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    with urllib.request.urlopen(
        urllib.request.Request(url, json.dumps(listing).encode(), headers), timeout=30
    ) as response:
        payload = response.read().decode()

    for raw_line in payload.splitlines():
        line = raw_line.removeprefix("data: ").strip()
        if line.startswith("{"):
            document = json.loads(line)
            if "result" in document:
                return frozenset(t["name"] for t in document["result"]["tools"])
    raise RuntimeError(f"no tools/list result in response from {url}")


def scan_instructions() -> list[Hit]:
    """Bare, anchor-free scan of every instruction surface under ~/.claude."""
    hits: list[Hit] = []
    seen: set[Path] = set()
    for pattern in INSTRUCTION_GLOBS:
        for path in sorted(CLAUDE_HOME.glob(pattern)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            for line_no, line in enumerate(
                path.read_text(errors="replace").splitlines(), 1
            ):
                if _TEACHES_RETIRED_NAMES in line:
                    continue
                tokens = set(_LORE_PREFIXED.findall(line)) - _NOT_TOOL_NAMES
                # Bare vocabulary is scanned on EVERY line — no "is this line about lore"
                # gate, because the corpses live in prose that never says "lore".
                # `odoo_read_file` is a real odoo-code tool and the one known homonym, so
                # it is excluded by its own prefix rather than by guessing at the topic.
                tokens |= {
                    m for m in _BARE_VOCAB.findall(line) if f"odoo_{m}" not in line
                }
                for token in sorted(tokens):
                    hits.append(Hit(path, line_no, token, line.strip()))
    return hits


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SERVER_URL
    try:
        served = served_tool_names(url)
    except Exception as error:  # noqa: BLE001 — a loud failure IS the contract here
        print(f"FAILED to read the served tool set from {url}: {error}", file=sys.stderr)
        print(
            "REFUSING to render a verdict I cannot substantiate — a currency check "
            "against an unreachable server would be a false clear.",
            file=sys.stderr,
        )
        return 2

    hits = scan_instructions()
    corpses = [
        h for h in hits if not (h.token.startswith("lore_") and h.token in served)
    ]

    print(f"served tool set ({len(served)}) from {url}:")
    print("  " + "  ".join(sorted(served)))
    print()
    print(f"recognised lore-tool references in {CLAUDE_HOME}: {len(hits)}")
    print(f"of which DEAD (name not served): {len(corpses)}")
    print()
    for hit in hits:
        print(hit.render(served))

    if corpses:
        print()
        print(
            "Each CORPSE above is an instruction teaching an agent a tool name that "
            "does not exist. Adjudicate individually — do NOT classify wholesale."
        )
    return 1 if corpses else 0


if __name__ == "__main__":
    raise SystemExit(main())
