"""Read-only comms CLI (packet 05a-iii) — the idle-gate hook bridge.

Reports a registered agent's PENDING state — unread messages, unacked directives,
and brief-ack skew — via DIRECT SurrealDB ``SELECT``s against the CONFIGURED store
coordinate, so a ``TeammateIdle`` hook can gate on real fleet state inside its ~10s
budget without spinning up the full MCP server.

Two invariants are load-bearing and are pinned in ``test_comms_cli.py``:

* **READ-ONLY BY CONSTRUCTION.** This module issues ``SELECT`` only — never
  ``CREATE`` / ``UPDATE`` / ``DELETE`` / ``RELATE`` / ``UPSERT`` / ``INSERT``. A
  hook that could mutate the fleet ledger while merely *checking* it is a footgun;
  the allowlist is SELECT, and the forbidden set is asserted absent from this
  source.
* **STORE COORDINATE COMES FROM CONFIG, NEVER HARDCODED.** The production store
  coordinate (``:18500``) must NEVER appear as a literal here — the coordinate is
  resolved from config/env exactly like the rest of lore, so a dev/test invocation
  reads the dev/test store and a production invocation reads production, without a
  code change. A hardcoded coordinate would pin every invocation to one store.

Unix philosophy: SILENT on success (the counts line only), LOUD on failure.

⚠ STUB (RED contract, packet 05a-iii): the ``pending`` command does NOT yet read
the store. It exits LOUD-and-non-zero so ``test_comms_cli.py``'s count pins stay
RED, while the read-only + store-coordinate-safety invariants above are GREEN from
the first commit (they are properties of what this file does NOT contain). The
builder wires the three SELECT-only reads against the configured coordinate and
renders ``unread=<n> unacked=<n> skew=<n>`` on stdout.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m loremaster.comms_cli",
        description="Read-only pending-traffic reporter for the comms subsystem.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    pending = subcommands.add_parser(
        "pending",
        help="report an agent's unread / unacked-directive / brief-skew counts",
    )
    pending.add_argument(
        "--agent",
        required=True,
        help="the registered agent name whose pending state to report",
    )
    # Explicit store-coordinate OVERRIDES. Each defaults to None ⇒ resolve from
    # lore config (the builder wires that default-resolution; its exact shape is an
    # escalated fork — see test_comms_cli.py). The overrides exist so a hook (and
    # the contract's integration pin) can target a specific store/database
    # deterministically. ⚠ A production coordinate is passed HERE, never hardcoded.
    pending.add_argument("--url", default=None, help="store RPC URL override")
    pending.add_argument("--namespace", default=None, help="store namespace override")
    pending.add_argument("--database", default=None, help="store database override")
    pending.add_argument("--user", default=None, help="store user override")
    pending.add_argument("--password", default=None, help="store password override")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code (0 = success, non-zero = failure)."""
    args = _build_parser().parse_args(argv)
    if args.command == "pending":
        # STUB: no store read yet — the builder replaces this with three
        # SELECT-only reads (unread ``to`` edges / unacked directive edges /
        # brief-ack skew) against the CONFIGURED coordinate, printing
        # ``unread=<n> unacked=<n> skew=<n>`` to stdout.
        print(
            "comms_cli 'pending' is not yet implemented (packet 05a-iii stub)",
            file=sys.stderr,
        )
        return 2
    return 2


if __name__ == "__main__":  # pragma: no cover - exercised via `python -m` subprocess
    sys.exit(main())
