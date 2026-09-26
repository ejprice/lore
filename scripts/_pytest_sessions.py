"""The shared home of the pytest-fleet detector and the worker-count policy (lore #503).

Two scripts need the same answer to *"is another pytest session live on this box?"*:
``concurrent_wire_acceptance`` (which refuses to measure under contention) and
``pending_contract_gate`` (whose pytest gate sizes its xdist worker count from it). Per the
ONE IMPLEMENTATION law, that answer is a function both import — never a pattern each clones.
It lives here rather than in either script because ``concurrent_wire_acceptance`` already
imports ``pending_contract_gate``, so the gate importing the driver would be a cycle.

⚠ KNOWN BOUND (#506): the detector matches ANY process whose argv mentions ``pytest`` — an
unrelated project's session, or a shell whose command text says pytest, counts too. For the
worker policy that errs in the safe direction (the cap applies); it is ledgered, not fixed here.
"""

from __future__ import annotations

from pathlib import Path

# Where the kernel exposes one directory per live process.
PROC_ROOT = Path("/proc")

# The argv substring that marks a process as a pytest session.
PYTEST_ARGV_MARKER = "pytest"

# The xdist worker count when another pytest session is live on the box (operator ruling
# 2026-09-26, item 3; the MEMORY.md fleet rule: cap a FULL suite at -n 12 — RAM, not ports).
FLEET_CAPPED_PYTEST_WORKERS = "12"
# The xdist worker count when this is the only pytest session on the box (CLAUDE.md's measured
# 9.6x for -n auto on this box).
SOLO_PYTEST_WORKERS = "auto"


def other_pytest_sessions(*, proc_root: Path = PROC_ROOT, own_pids: set[int]) -> list[tuple[int, str]]:
    """List the live pytest sessions other than the caller's own processes.

    Args:
        proc_root: The ``/proc``-shaped tree to scan (one ``<pid>/cmdline`` per process).
        own_pids: Pids that never count as "another" session (the caller and its parent).

    Returns:
        ``(pid, cmdline)`` for every live process whose argv mentions pytest, excluding
        ``own_pids``, ordered by pid directory name. An xdist worker (execnet's bootstrap argv
        never names pytest) or a non-test process is not a session.
    """
    sessions: list[tuple[int, str]] = []
    for entry in sorted(proc_root.iterdir(), key=lambda path: path.name):
        if not entry.name.isdigit() or int(entry.name) in own_pids:
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:  # the process exited between the listing and the read
            continue
        argv = [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
        if any(PYTEST_ARGV_MARKER in part for part in argv):
            sessions.append((int(entry.name), " ".join(argv)))
    return sessions


def pytest_worker_count(*, proc_root: Path = PROC_ROOT, own_pids: set[int]) -> str:
    """Choose the xdist ``-n`` value for a pytest run, from who else is running.

    Consults :func:`other_pytest_sessions` through this module's global at call time, exactly
    once, so replacing the shared detector changes the answer.

    Args:
        proc_root: The ``/proc``-shaped tree the detector scans.
        own_pids: Pids that never count as "another" session.

    Returns:
        ``FLEET_CAPPED_PYTEST_WORKERS`` if any other pytest session is live, else
        ``SOLO_PYTEST_WORKERS``. No division by session count and no refusal (ruling item 4).
    """
    if other_pytest_sessions(proc_root=proc_root, own_pids=own_pids):
        return FLEET_CAPPED_PYTEST_WORKERS
    return SOLO_PYTEST_WORKERS
