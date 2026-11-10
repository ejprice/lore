"""The pytest-xdist worker-to-controller channel: both ends, once (parked-contracts ruling A11).

An xdist worker cannot print to the terminal and cannot change the controller's exit status. What it knows
reaches the controller only through ``config.workeroutput``, a ``dict[str, str]`` the worker fills and xdist
ships when the worker finishes; the controller reads it back as ``node.workeroutput`` in its
``pytest_testnodedown`` hook. Two repo plugins use that channel: ``loremaster/tests/conftest.py`` (the #486
leaked-test-database report) and ``scripts/_parked_contracts.py`` (the parked-deselection report). Each
spelling the two attribute reads itself would be two copies of the protocol, so both ends live here.

WHY ``lorerunes``: it is the one stdlib-only package every workspace member and the repo-root test tooling
can import (CLAUDE.md, ``lorerunes`` — THE HOME FOR SHARED CODE). The helper duck-types on the attribute
names, so it imports neither pytest nor xdist.

This module holds the channel's mechanics only. What a plugin ships, how it validates it, and what a missing
or corrupt value means are each plugin's own decisions.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

#: The attribute xdist puts on a worker's ``config`` and on the controller-side ``node``.
WORKEROUTPUT_ATTRIBUTE = "workeroutput"


def ship_to_controller(config: Any, values: Mapping[str, str]) -> bool:
    """Worker side: put ``values`` on the channel, if this process is an xdist worker.

    Args:
        config: The pytest ``Config`` of the running process.
        values: What to ship, key to text. Merged into the channel, so two plugins shipping under distinct
            keys never overwrite each other.

    Returns:
        ``True`` when this process is an xdist worker and the values were shipped; ``False`` when it owns
        the terminal itself (no xdist, or the controller), so the caller must report in-process.
    """
    channel = getattr(config, WORKEROUTPUT_ATTRIBUTE, None)
    if channel is None:
        return False
    channel.update(values)
    return True


def received_from_worker(node: Any) -> Mapping[str, str]:
    """Controller side: what a finished worker shipped.

    Args:
        node: The controller-side worker node xdist hands to ``pytest_testnodedown``.

    Returns:
        The worker's channel; empty when the worker shipped nothing or never produced one, so a caller's
        ``KeyError`` on its own key is how an absent report is detected.
    """
    return getattr(node, WORKEROUTPUT_ATTRIBUTE, None) or {}
