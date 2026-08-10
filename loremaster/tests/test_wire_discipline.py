"""R16 part 2 — THE WIRE-ONLY INVARIANT over the posture test modules.

Design ``docs/design/2026-07-31-packet39-google-oauth.md`` §17 (R16).

------------------------------------------------------------------------------
THE DEFECT CLASS THIS EXISTS TO KILL

``FastMCP.__init__`` calls ``_setup_handlers``, which registers the **bound** method
(``self.list_tools``, ``self.call_tool``, …) with the low-level server. **Anything
installed on the server afterwards as an instance attribute is live in-process and DEAD
ON THE WIRE.** Three wrong builds exploited exactly that, in three consecutive waves,
each passing every pin the previous wave had just written:

* **WB30** — ``mcp.call_tool = _guarded``
* **WB48** — the guard placed after ``super().call_tool`` (the body ran, then refused)
* **WB93** — ``mcp.list_tools = _scoped_list_tools`` (hosted ``tools/list`` on the wire
  returned all fifteen tools, six of them mutating; the correct build returns nine)

Every fix pinned the route that had just been broken. **This module kills the class
instead of the door**, by making the discipline mechanical rather than remembered: no
posture assertion may prove its claim through an in-process handler call, because such a
call cannot distinguish a live guard from one that is dead on the wire.

⚠ IT IS A TEST, INSIDE ``testpaths``, ON PURPOSE. *A guard nobody runs is a hope with a
filename* — this repo has two receipts of exactly that, both instruments that sat outside
``testpaths`` while instrumenting the class they were victims of.

------------------------------------------------------------------------------
WHY EVERY SET HERE IS DERIVED

* The **handler set** comes from AST-parsing the installed SDK's ``_setup_handlers``
  (:func:`_auth_fixtures.sdk_bound_handler_names`) — the SAME derivation R16 part 1's
  structural pin consumes. One derivation, two instruments. A hand-list would be the next
  name-list, which is the artifact this repo has the most receipts against, and it would
  miss the eighth handler an SDK upgrade binds.
* The **module set** comes from a filesystem glob, not a hand-list, so a posture module
  added tomorrow is governed the day it lands.
* The **call check is RECEIVER-BLIND**: it flags ``<anything>.call_tool(...)``, not just
  ``mcp.call_tool(...)``. Packet 01's lesson, paid for six times — *when you catch
  yourself enumerating what is forbidden, you have already lost; a gate keyed on a
  receiver NAME falls to a different receiver name.*

------------------------------------------------------------------------------
STATED BOUNDS — this gate does not overstate its reach

1. It governs modules matching the posture glob. **A posture CLAIM proven in-process
   inside a module that evades that naming pattern is invisible to it** (design §17 names
   this residual too).
2. It catches DIRECT calls and imports of the known in-process helpers. A posture module
   that reached in-process through a helper defined *in itself* under a different name
   would evade the import check — though not the receiver-blind call check, since the
   helper's own body lives in the same module and is parsed too.
3. In-process calls stay legitimate everywhere else: ``test_mcp_server.py``'s
   registration-surface pins and ``test_permission_resolver_seam.py``'s seam pins are
   about in-process dispatch as a SUBJECT, not as a shortcut.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from _auth_fixtures import sdk_bound_handler_names

# The posture-test modules, DERIVED from the filesystem rather than listed. A module added
# tomorrow whose name marks it a posture test is governed the day it lands.
POSTURE_MODULE_GLOB = "test_*posture*.py"

TESTS_DIRECTORY = Path(__file__).parent

# The module that supplies the sanctioned IN-PROCESS helpers. A posture module importing
# from it is reaching for the shortcut this invariant exists to remove.
IN_PROCESS_HELPER_NAMES = frozenset({"call_and_capture", "as_principal"})

# Refusal-EFFECT helper modules (finding #295/#346) are brought UNDER this same wire-discipline
# scan, so the receiver-blind check mechanically forbids any ``<anything>.call_tool(...)`` in them —
# the D-WB2 in-process door — and governs packet 39's future consumers of the shared refusal helper.
# They are NOT posture TEST modules (they carry no ``posture`` in their name), so they are named by
# ROLE and unioned in BY EXISTENCE: a named-but-absent helper is simply not scanned, never a hard
# error. A new refusal-effect helper is brought under the scan by adding its filename here.
REFUSAL_EFFECT_HELPER_MODULE_NAMES = frozenset({"_refusal_effect.py"})


def refusal_effect_helper_modules() -> list[Path]:
    """The refusal-effect helper modules present on disk (finding #346 — the R16 reach extension)."""
    return sorted(
        path
        for name in REFUSAL_EFFECT_HELPER_MODULE_NAMES
        if (path := TESTS_DIRECTORY / name).exists()
    )


def posture_modules() -> list[Path]:
    """Every module UNDER the wire-discipline scan: the posture test modules (glob-derived) PLUS the
    refusal-effect helper modules (finding #346 R16 reach), so R16's receiver-blind check governs
    the shared refusal helper — and every posture pin packet 39 builds on it — too."""
    return sorted(
        [*TESTS_DIRECTORY.glob(POSTURE_MODULE_GLOB), *refusal_effect_helper_modules()]
    )


def test_the_posture_module_set_is_not_empty() -> None:
    """ANTI-VACUITY: a glob that matches nothing is a broken instrument, not a clean tree.

    Without this, deleting or renaming the posture module would silently turn every
    assertion below into a ∀ over the empty set — the failure mode of a gate reads as a
    pass, which is the direction that always costs.
    """
    modules = posture_modules()
    assert modules, (
        f"no test module matched {POSTURE_MODULE_GLOB!r} in {TESTS_DIRECTORY}. The "
        f"wire-only invariant is now vacuous: either the posture module was renamed out "
        f"of the pattern (fix the pattern) or deleted (delete this guard deliberately)."
    )


def test_the_handler_derivation_is_not_empty() -> None:
    """ANTI-VACUITY for the other derived set — the SDK's own bound-handler names."""
    handlers = sdk_bound_handler_names()
    assert handlers, "the SDK handler derivation is empty; both R16 instruments are vacuous"
    # The three routes that have actually been exploited must be in the derived set. This
    # is not a hand-list standing in for the derivation — it is a check that the
    # derivation still SEES the routes we have receipts for.
    for exploited in ("call_tool", "list_tools"):
        assert exploited in handlers, (
            f"the derivation lost {exploited!r} — a route with a WRONG-BUILD receipt "
            f"against it. The parse of FastMCP._setup_handlers has drifted."
        )


@pytest.mark.parametrize(
    "module_path", posture_modules(), ids=lambda path: path.name
)
def test_no_posture_assertion_calls_a_handler_in_process(module_path: Path) -> None:
    """∀ posture module: no call to any SDK-bound handler name, on ANY receiver.

    RECEIVER-BLIND by construction. ``mcp.call_tool(...)``, ``self.mcp.list_tools(...)``
    and ``server.call_tool(...)`` are all the same defect, and a gate keyed on the
    receiver name falls to the first author who picks a different variable.
    """
    handlers = sdk_bound_handler_names()
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))

    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        if isinstance(callee, ast.Attribute) and callee.attr in handlers:
            receiver = ast.unparse(callee.value)
            offenders.append(f"{module_path.name}:{node.lineno}: {receiver}.{callee.attr}(...)")

    assert not offenders, (
        "a posture module proves its claim through an IN-PROCESS handler call:\n  "
        + "\n  ".join(offenders)
        + "\n\nAn in-process call cannot tell a live guard from one that is dead on the "
        "wire — WB30 (call_tool), WB48 (dispatch order) and WB93 (list_tools) each passed "
        "every in-process pin while the served surface was unguarded. Drive the assertion "
        "through `_auth_fixtures.wire_session` instead."
    )


@pytest.mark.parametrize(
    "module_path", posture_modules(), ids=lambda path: path.name
)
def test_no_posture_module_imports_the_in_process_helpers(module_path: Path) -> None:
    """∀ posture module: the in-process shortcut is not imported either.

    Closes the indirection door the call check alone would leave open — a helper defined
    in ``_auth_fixtures`` whose body makes the in-process call would otherwise let a
    posture module launder the very thing this invariant forbids.
    """
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in IN_PROCESS_HELPER_NAMES:
                    imported.append(f"{module_path.name}:{node.lineno}: {alias.name}")

    assert not imported, (
        "a posture module imports an IN-PROCESS dispatch helper:\n  "
        + "\n  ".join(imported)
        + "\n\nThose helpers exist for modules where in-process dispatch is the SUBJECT "
        "(the permission-resolver seam), never as a shortcut for a posture claim."
    )


def test_the_invariant_would_CATCH_an_in_process_posture_call() -> None:
    """⚑ THE POSITIVE CONTROL — the instrument must be shown FIRING, not just passing.

    A gate that has never been observed to reject anything is indistinguishable from one
    that cannot. This synthesises the exact source WB93's author would have written and
    proves the AST check flags it — including through a receiver the check was never told
    about, which is the property a receiver-name list would not have.
    """
    handlers = sdk_bound_handler_names()
    hostile_source = (
        "async def test_a_hosted_principal_sees_only_read_tools(mcp):\n"
        "    visible = {tool.name for tool in await some_other_name.list_tools()}\n"
        "    assert visible == READ_ONLY\n"
    )
    tree = ast.parse(hostile_source)

    flagged = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in handlers
    ]
    assert flagged == ["list_tools"], (
        f"the AST check did not flag an in-process handler call on an unfamiliar "
        f"receiver; it is receiver-KEYED rather than receiver-blind, and the next author "
        f"who names their variable differently walks straight through. Flagged: {flagged}"
    )


def test_the_invariant_does_not_flag_a_wire_driven_assertion() -> None:
    """The NEGATIVE control: a gate that flags everything is a gate that gets deleted.

    The sanctioned wire spelling must pass cleanly, or the invariant is a false positive
    generator — and a gate that refuses honest code is a gate somebody switches off.
    """
    handlers = sdk_bound_handler_names()
    honest_source = (
        "async def test_a_hosted_principal_sees_only_read_tools(tmp_path):\n"
        "    async with wire_session(tmp_path, posture='hosted', principal='google') as wire:\n"
        "        served = await wire.served_tool_names()\n"
        "        body = await wire.call('lore_remember')\n"
        "    assert served == READ_ONLY\n"
    )
    tree = ast.parse(honest_source)

    flagged = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in handlers
    ]
    assert flagged == [], f"the wire spelling was wrongly flagged: {flagged}"
