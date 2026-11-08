"""Contract for F6 — pytest-only adjudication in ``scripts/pending_contract_gate.py`` (packet SDK3 R6 F6;
§R3.7(c) of ``docs/plans/v2/sdk3-python-sdk-3-migration.md``; R27-4: BUILD STEP 0 of packet 66, the builder
implements it, these tests are contract surface).

**THE GAP (#579, measured 2026-11-08).** The registry REFUSES a file that carries pytest reds and no mypy
error ("names neither a missing symbol nor a code allowance"), and a registered file with no mypy error
self-destructs on the typecheck leg. So a contract-ahead packet whose RED@HEAD set is pytest-only (packet
66: 90 + rounds 3–6 nodes) cannot be owned, and every full currency run — any packet's close-out — reads
those reds RED_ORPHANED.

**THE SEMANTICS PINNED, §R3.7(c) verbatim** (pytest leg of ``--currency``):

1. a failing node id listed under a bound → ``RED_ADJUDICATED(owner, reopen_trigger)``;
2. a failing node id not listed → ``RED_ORPHANED`` (unchanged);
3. **self-destruct:** a listed node id that PASSES fails the gate ("adjudicated red ``<id>`` is green —
   delete it with the fix"), exactly like the typecheck leg's "produced NO mypy errors";
4. **stale:** a listed id that is not COLLECTED (renamed/deleted) fails the gate;
5. ids are written from ``pytest --collect-only -q`` (pytest escapes non-ASCII in parametrised ids), and a
   parametrised id is listed per parameter, never by prefix.

plus R27-4's two registry legs: ``--verify-registry`` (the registry's own validation) ADMITS a file entry
that carries ``red_nodeids`` only, and still REFUSES an entry with neither symbols, code allowances nor node
ids.

**THE SHAPE THESE TESTS ASSUME (FORK-R8-1 in the packet doc §ROUND 8).** ``red_nodeids`` is a field of each
FILE entry (``PendingFile``), beside ``missing_symbols`` / ``unsymboled_codes`` — RULING-6's "a
``red_nodeids``-only ``PendingFile``"; §R3.7(c) had written it on the bound. Node ids are matched against
the junit document's testcases, each derived as ``<file>::<classes after the module>::<name>`` (xunit1:
``file`` + dotted ``classname`` + ``name``). Two consequences are pinned because a correct F6 cannot do
without them:

* a node-listed file is adjudicated PER NODE — an unlisted red in it is orphaned (else ``red_nodeids`` would
  be the file-only matching the existing refusal forbids, re-entered through a new key);
* a file registered by symbols only keeps TODAY's file-level pytest adjudication (packet 58 owns its pytest
  reds that way; a universal per-node rule would orphan them overnight) — the control below;
* a ``red_nodeids``-only file does NOT self-destruct on the typecheck leg for having no mypy error (it never
  claimed one).

⚠ WHAT WRONG BUILD WOULD STILL PASS THIS? A build that admits every red in a node-listed file (killed by the
unlisted-red pin); one that never self-destructs (killed by the passing-node and not-collected pins); one
that matches by prefix (killed by the per-parameter pins); one that makes per-node matching universal
(killed by the symbol-only control); one that leaves the typecheck leg self-destructing a pytest-only file
(killed by the typecheck pin). RED at ``3374a6b`` by design: the registry rejects the unknown
``red_nodeids`` key."""

from __future__ import annotations

import os
import re
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pending_contract_gate import (  # noqa: E402
    GateCurrency,
    GateManifest,
    JUnitReportReader,
    MypyOutputReader,
    PendingContractGate,
    PendingContractRegistry,
    RegistryError,
    _currencies_for,
)
from test_pending_contract_gate import _mypy_output  # noqa: E402

_NODE_FILE = "loremaster/tests/test_f6_contract_ahead.py"
_SYMBOL_FILE = "lorerunes/tests/test_f6_symbols_only.py"
_UNREGISTERED_FILE = "loremaster/tests/test_f6_unregistered.py"

_LISTED_CLASS_NODE = f"{_NODE_FILE}::TestAContractAheadPin::test_red_until_the_build"
_LISTED_PARAM_NODE = f"{_NODE_FILE}::test_a_parametrised_pin[digit-led]"
_SIBLING_PARAM_NODE = f"{_NODE_FILE}::test_a_parametrised_pin[letter-led]"
_UNLISTED_NODE = f"{_NODE_FILE}::TestAContractAheadPin::test_a_new_regression"
#: pytest's own escaping of a non-ASCII parameter (``--collect-only -q`` prints it, and junit's ``name`` too).
_ESCAPED_NODE = f"{_NODE_FILE}::test_an_escaped_param[\\u2014]"

_BOUND_ID = "packet-66-sdk3-contract"
_TRIGGER = "the packet-66 build commit that pins surrealdb==3.0.0"

_MANIFEST_YAML = textwrap.dedent(
    """\
    version: 1
    gates:
      - id: typecheck
        description: "the canonical static-analysis runner"
        command: ["./scripts/typecheck.sh"]
        reader: typecheck_transcript
        adjudicated_by: pending-contracts
      - id: pytest
        description: "the suite"
        command: ["uv", "run", "pytest", "-q", "--junit-xml={junit_xml}"]
        reader: pytest_junit
        adjudicated_by: pending-contracts
    """
)


def _registry_yaml(node_ids: list[str], *, with_symbol_bound: bool = True) -> str:
    # SINGLE-quoted: YAML double quotes decode ``\u2014`` into the character; pytest ids keep the escape.
    listed = "\n".join(f"              - '{node_id}'" for node_id in node_ids)
    node_entry = f"""\
          - path: {_NODE_FILE}
            red_nodeids:
{listed}
"""
    symbol_bound = f"""\
      - id: packet-58-contract
        owner: "packet 58"
        reopen_trigger: "the packet-58 build"
        ruling: "R12 F19"
        rationale: "file-level owner of its pytest reds today"
        files:
          - path: {_SYMBOL_FILE}
            missing_symbols:
              - lorerunes.FixturePlaceholder
"""
    return (
        "version: 1\nbounds:\n"
        f"""\
      - id: {_BOUND_ID}
        owner: "the SDK3 builder (packet 66)"
        reopen_trigger: "{_TRIGGER}"
        ruling: "R22 rider 3 / R24 item 6 + R26-2"
        rationale: "contract-ahead pytest-only RED@HEAD"
        files:
{node_entry}"""
        + (symbol_bound if with_symbol_bound else "")
    )


def _gate(tmp_path: Path, node_ids: list[str], *, with_symbol_bound: bool = True) -> PendingContractGate:
    registry_path = tmp_path / "pending_contracts.yaml"
    registry_path.write_text(_registry_yaml(node_ids, with_symbol_bound=with_symbol_bound))
    tree = tmp_path / "tree"
    for relative in (_NODE_FILE, _SYMBOL_FILE):
        (tree / relative).parent.mkdir(parents=True, exist_ok=True)
        (tree / relative).write_text("# registered\n")
    return PendingContractGate(registry=PendingContractRegistry.load(registry_path), repo_root=tree)


def _manifest(tmp_path: Path) -> GateManifest:
    path = tmp_path / "gates.yaml"
    path.write_text(_MANIFEST_YAML)
    return GateManifest.load(path)


def _testcase(node_id: str, *, failed: bool) -> str:
    """One xunit1 testcase for ``node_id`` (``file``, dotted ``classname``, ``name``), as pytest writes it."""
    file, _, rest = node_id.partition("::")
    *classes, name = rest.split("::")
    module = file[: -len(".py")].replace("/", ".")
    classname = ".".join([module, *classes])
    body = "<failure message='pin'>boom</failure>" if failed else ""
    return f'<testcase classname="{classname}" name="{name}" file="{file}">{body}</testcase>'


def _junit(cases: list[tuple[str, bool]]) -> str:
    failures = sum(1 for _node, failed in cases if failed)
    body = "".join(_testcase(node, failed=failed) for node, failed in cases)
    return (
        '<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest" '
        f'tests="{len(cases)}" failures="{failures}" errors="0" skipped="0">{body}</testsuite></testsuites>'
    )


def _currency(tmp_path: Path, gate: PendingContractGate, gate_id: str, result: object) -> GateCurrency:
    currencies = _currencies_for(gate, _manifest(tmp_path), {gate_id: result})  # type: ignore[dict-item]
    (currency,) = [c for c in currencies if c.gate_id == gate_id]
    return currency


def _pytest_currency(
    tmp_path: Path, gate: PendingContractGate, cases: list[tuple[str, bool]]
) -> GateCurrency:
    return _currency(tmp_path, gate, "pytest", JUnitReportReader.read(_junit(cases)))


_ALL_LISTED_RED = [(_LISTED_CLASS_NODE, True), (_LISTED_PARAM_NODE, True), (_SIBLING_PARAM_NODE, False)]


# --------------------------------------------------------------------------------------------------------
# The registry legs (R27-4)
# --------------------------------------------------------------------------------------------------------


def test_the_registry_admits_a_file_that_carries_red_nodeids_only(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE])
    assert _NODE_FILE in gate.registry.registered_paths


def test_the_registry_still_refuses_an_entry_with_no_claim_at_all(tmp_path: Path) -> None:
    """``red_nodeids: []`` with no symbols and no codes is the file-only matching the refusal exists for. The
    message must be the CLAIM refusal — an unknown-key error (the schema at HEAD) is the wrong reason."""
    path = tmp_path / "loose.yaml"
    empty_claim = _registry_yaml([], with_symbol_bound=False).replace(
        "            red_nodeids:\n", "            red_nodeids: []\n"
    )
    path.write_text(empty_claim)
    with pytest.raises(RegistryError, match="neither"):
        PendingContractRegistry.load(path)


# --------------------------------------------------------------------------------------------------------
# (1)/(2): listed → adjudicated; unlisted → orphaned — PER NODE in a node-listed file
# --------------------------------------------------------------------------------------------------------


def test_listed_failing_nodes_are_RED_ADJUDICATED_naming_the_owner_and_the_trigger(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    currency = _pytest_currency(tmp_path, gate, _ALL_LISTED_RED)
    assert currency.verdict == "RED_ADJUDICATED" and currency.ok, currency.orphans
    assert any(_BOUND_ID in owner and _TRIGGER in owner for owner in currency.owners), currency.owners


def test_an_unlisted_failing_node_in_a_node_listed_file_is_RED_ORPHANED(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    currency = _pytest_currency(tmp_path, gate, [*_ALL_LISTED_RED, (_UNLISTED_NODE, True)])
    assert currency.verdict == "RED_ORPHANED" and not currency.ok
    assert any("test_a_new_regression" in orphan for orphan in currency.orphans), currency.orphans


def test_a_failing_node_outside_the_registry_is_RED_ORPHANED(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    stranger = f"{_UNREGISTERED_FILE}::test_unrelated"
    currency = _pytest_currency(tmp_path, gate, [*_ALL_LISTED_RED, (stranger, True)])
    assert currency.verdict == "RED_ORPHANED"
    assert any(_UNREGISTERED_FILE in orphan for orphan in currency.orphans), currency.orphans


def test_CONTROL_a_symbols_only_file_keeps_file_level_pytest_adjudication(tmp_path: Path) -> None:
    """Per-node matching is for node-listed files only: packet 58's file-level ownership is unchanged."""
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    symbol_red = f"{_SYMBOL_FILE}::test_any_packet_58_red"
    currency = _pytest_currency(tmp_path, gate, [*_ALL_LISTED_RED, (symbol_red, True)])
    assert currency.verdict == "RED_ADJUDICATED" and currency.ok, currency.orphans


# --------------------------------------------------------------------------------------------------------
# (3) self-destruct on PASS · (4) stale when NOT COLLECTED
# --------------------------------------------------------------------------------------------------------


def test_a_listed_node_that_PASSES_fails_the_gate_and_says_delete_it(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    currency = _pytest_currency(
        tmp_path,
        gate,
        [(_LISTED_CLASS_NODE, True), (_LISTED_PARAM_NODE, False), (_SIBLING_PARAM_NODE, False)],
    )
    assert not currency.ok
    assert any(
        _LISTED_PARAM_NODE in orphan and "green" in orphan.lower() and "delete" in orphan.lower()
        for orphan in currency.orphans
    ), currency.orphans


def test_a_listed_node_that_is_NOT_COLLECTED_fails_the_gate(tmp_path: Path) -> None:
    renamed = f"{_NODE_FILE}::TestAContractAheadPin::test_renamed_away"
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE, renamed])
    currency = _pytest_currency(tmp_path, gate, _ALL_LISTED_RED)
    assert not currency.ok
    assert any("test_renamed_away" in orphan for orphan in currency.orphans), currency.orphans


# --------------------------------------------------------------------------------------------------------
# (5) per parameter, exact — never by prefix; escaped ids match as --collect-only prints them
# --------------------------------------------------------------------------------------------------------


def test_a_parametrised_id_admits_ONLY_its_own_parameter(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    currency = _pytest_currency(
        tmp_path, gate, [(_LISTED_CLASS_NODE, True), (_LISTED_PARAM_NODE, True), (_SIBLING_PARAM_NODE, True)]
    )
    assert currency.verdict == "RED_ORPHANED"
    assert any("[letter-led]" in orphan for orphan in currency.orphans), currency.orphans


def test_a_listed_PREFIX_admits_no_parameter_and_is_itself_stale(tmp_path: Path) -> None:
    prefix = f"{_NODE_FILE}::test_a_parametrised_pin"
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, prefix])
    currency = _pytest_currency(tmp_path, gate, _ALL_LISTED_RED)
    assert not currency.ok
    assert any("[digit-led]" in orphan for orphan in currency.orphans), (
        f"a prefix admitted a parametrised red: {currency.orphans}"
    )
    stale_prefix = re.compile(re.escape(prefix) + r"(?!\[)")
    assert any(stale_prefix.search(orphan) for orphan in currency.orphans), (
        f"the prefix id itself (collected nowhere) is not reported stale: {currency.orphans}"
    )


def test_an_escaped_parametrised_id_matches_exactly_as_collect_only_prints_it(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE, _ESCAPED_NODE])
    currency = _pytest_currency(tmp_path, gate, [*_ALL_LISTED_RED, (_ESCAPED_NODE, True)])
    assert currency.verdict == "RED_ADJUDICATED" and currency.ok, currency.orphans


# --------------------------------------------------------------------------------------------------------
# The typecheck leg must not self-destruct a pytest-only entry
# --------------------------------------------------------------------------------------------------------


def test_a_red_nodeids_only_file_does_not_self_destruct_on_the_typecheck_leg(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE], with_symbol_bound=False)
    currency = _currency(tmp_path, gate, "typecheck", MypyOutputReader.read(_mypy_output([])))
    assert currency.ok, (
        f"a file that claims only pytest node ids was self-destructed on the typecheck leg for having no "
        f"mypy "
        f"error: {currency.orphans}"
    )
