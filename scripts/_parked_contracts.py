"""Parked contract reds are DESELECTED by a default pytest run (lead task 7f68cbcf, operator 2026-11-09).

The rulings are in ``docs/design/2026-11-09-parked-contracts-rulings.md``.

``scripts/pending_contracts.yaml`` lists, per bound, the node ids a contract-ahead packet is designed to fail
(``bounds[].files[].red_nodeids``). Until the build lands, every agent running the suite would see them red.
This plugin deselects them, by EXACT node-id membership, unless their bound is ``active: true`` or the run
passes ``--run-parked`` (the currency gate does, so it still observes every registered red).

The plugin is registered by the repo-root ``conftest.py`` under :data:`PARKED_CONTRACTS_PLUGIN_NAME`, so a
tool that MEASURES the tree passes ``-p no:lore-parked-contracts`` (ruling A7).

THE REGISTRY is read through :class:`pending_contract_gate.PendingContractRegistry` and nothing else (S8):
the parked set is its ``parked_node_owners`` method. A registry that is absent, unreadable or invalid
deselects nothing and costs one warning line (S5); the plugin never forces an exit status.

XDIST: workers collect, the controller owns the terminal. A worker ships its report through the shared
``lorerunes.worker_output`` channel and the controller prints the FIRST report it receives (every worker
collects the same items, so summing would multiply the count).

This module imports nothing heavy at import time: ``gated_ground`` and ``concurrent_wire_acceptance`` import
it only for the plugin name.
"""

from __future__ import annotations

import contextlib
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from lorerunes.worker_output import received_from_worker, ship_to_controller

#: The name the plugin registers under; ``-p no:<name>`` disables it (ruling A7).
PARKED_CONTRACTS_PLUGIN_NAME = "lore-parked-contracts"
#: The opt-in flag (S3).
RUN_PARKED_OPTION = "--run-parked"
#: The registry's place relative to the run's rootdir (ruling D1).
REGISTRY_RELATIVE_PATH = Path("scripts") / "pending_contracts.yaml"
#: ``workeroutput`` key a worker's parked-deselection report crosses back under.
WORKEROUTPUT_KEY = "lore_parked_contracts_report"

_SCRIPTS_DIRECTORY = Path(__file__).resolve().parent
_COUNT_FIELD = "count"
_ENTRIES_FIELD = "entries"
_WARNING_FIELD = "warning"


@contextlib.contextmanager
def _scripts_importable() -> Iterator[None]:
    """Put ``scripts/`` on ``sys.path`` for the gate's sibling imports, then restore it."""
    sys.path.insert(0, str(_SCRIPTS_DIRECTORY))
    try:
        yield
    finally:
        sys.path.remove(str(_SCRIPTS_DIRECTORY))


def add_run_parked_option(parser: pytest.Parser) -> None:
    """Register ``--run-parked`` (S3)."""
    parser.addoption(
        RUN_PARKED_OPTION,
        action="store_true",
        default=False,
        help="run the contract reds parked in scripts/pending_contracts.yaml (default: deselect them)",
    )


class ParkedContractsPlugin:
    """Deselect every parked node at collection; report once on the terminal."""

    def __init__(self, config: pytest.Config) -> None:
        """Remember the config and start with nothing to report."""
        self._config = config
        # What the terminal prints: a report dict (count / entries / warning) from this process's own
        # collection, or the first worker's.
        self._report: dict[str, Any] | None = None

    def _registry_path(self) -> Path:
        """The registry of THIS run's rootdir (ruling D1), never the working directory's."""
        return self._config.rootpath / REGISTRY_RELATIVE_PATH

    def _owners_or_warning(self) -> tuple[dict[str, tuple[str, ...]], str | None]:
        """Read the parked set through the gate's registry model (S8).

        Returns:
            The node-to-owning-bounds map and ``None``; or an empty map and ONE line naming the problem (S5).
        """
        with _scripts_importable():
            from pending_contract_gate import PendingContractRegistry, RegistryError
        try:
            registry = PendingContractRegistry.load(self._registry_path())
        except RegistryError as error:
            # pydantic's message is multi-line; the warning must be ONE line.
            return {}, f"parked contracts: nothing deselected, {' '.join(str(error).split())}"
        return registry.parked_node_owners(), None

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, config: pytest.Config, items: list[pytest.Item]) -> None:
        """Deselect the parked nodes still in ``items``; runs last, so it counts only the nodes it removes."""
        if config.getoption("run_parked"):
            return
        owners, warning = self._owners_or_warning()
        parked = [item for item in items if item.nodeid in owners]
        if parked:
            parked_ids = {id(item) for item in parked}
            items[:] = [item for item in items if id(item) not in parked_ids]
            config.hook.pytest_deselected(items=parked)
        # Involvement is read from the DESELECTED items only (D3).
        entries = sorted({bound_id for item in parked for bound_id in owners[item.nodeid]})
        report = {_COUNT_FIELD: len(parked), _ENTRIES_FIELD: entries, _WARNING_FIELD: warning}
        if not ship_to_controller(config, {WORKEROUTPUT_KEY: json.dumps(report)}):
            self._report = report

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: Any, error: Any) -> None:
        """xdist controller: keep the first worker's report; the others describe the same collection."""
        shipped = received_from_worker(node).get(WORKEROUTPUT_KEY)
        if shipped is not None and self._report is None:
            self._report = json.loads(shipped)

    def pytest_terminal_summary(self, terminalreporter: pytest.TerminalReporter) -> None:
        """Print the S2 line, or the S5 warning, once."""
        if self._report is None:
            return
        if self._report[_WARNING_FIELD]:
            terminalreporter.write_line(self._report[_WARNING_FIELD])
        elif self._report[_COUNT_FIELD]:
            terminalreporter.write_line(
                f"parked contracts: {self._report[_COUNT_FIELD]} test(s) deselected "
                f"(entries: {', '.join(self._report[_ENTRIES_FIELD])}); pass {RUN_PARKED_OPTION} to run them"
            )


def register_plugin(config: pytest.Config) -> None:
    """Register the plugin under its opt-out name; a blocked name (``-p no:...``) registers nothing."""
    config.pluginmanager.register(ParkedContractsPlugin(config), name=PARKED_CONTRACTS_PLUGIN_NAME)
