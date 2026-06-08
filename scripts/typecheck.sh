#!/usr/bin/env bash
#
# Canonical type-check for the lore workspace.
#
# Why per-member, not a single combined invocation:
#   Each workspace member (lorescribe, loresigil, loremaster) owns its own
#   ``tests/`` directory.  Under mypy's ``explicit_package_bases`` mode (set in
#   pyproject.toml so the members resolve each other's sources), all three
#   ``tests/`` dirs map to the SAME ``tests.*`` module namespace.  Passing all
#   three members to ONE ``mypy`` invocation therefore trips a spurious
#   "Duplicate module named tests.conftest" error before any real checking runs.
#
#   Issuing one invocation PER member keeps a single ``tests/`` in scope at a
#   time, so there is no collision AND every member's src + tests are actually
#   type-checked (no ``exclude`` hiding the test trees — a regression in any
#   ``<member>/tests`` is caught here).
#
# Exit non-zero if ANY member fails; print a per-member pass/fail line.

set -uo pipefail

MEMBERS=(lorescribe loresigil loremaster)
status=0

for member in "${MEMBERS[@]}"; do
    if uv run mypy "${member}"; then
        echo "typecheck: ${member} OK"
    else
        echo "typecheck: ${member} FAILED" >&2
        status=1
    fi
done

if [[ "${status}" -ne 0 ]]; then
    echo "typecheck: one or more members failed" >&2
fi

exit "${status}"
