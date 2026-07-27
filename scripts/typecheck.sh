#!/usr/bin/env bash
#
# Canonical type-check for the lore workspace.
#
# Why per-member, not a single combined invocation:
#   Each workspace member (lorerunes, lorescribe, loresigil, loremaster) owns its own
#   ``tests/`` directory.  Under mypy's ``explicit_package_bases`` mode (set in
#   pyproject.toml so the members resolve each other's sources), EVERY member's
#   ``tests/`` dir maps to the SAME ``tests.*`` module namespace.  Passing the
#   members to ONE ``mypy`` invocation therefore trips a spurious
#   "Duplicate module named tests.conftest" error before any real checking runs.
#
#   Issuing one invocation PER member keeps a single ``tests/`` in scope at a
#   time, so there is no collision AND every member's src + tests are actually
#   type-checked (no ``exclude`` hiding the test trees — a regression in any
#   ``<member>/tests`` is caught here).
#
# Exit non-zero if ANY member fails; print a per-member pass/fail line.

set -uo pipefail

# Anchor to the repo root, whatever directory the caller invoked us from.
#
# The member arguments below are RELATIVE paths.  Run from anywhere but the repo
# root they resolve to nothing, and mypy answers "Cannot read file 'lorescribe'"
# — ONE error per member.  The exit code stays 1 (so a gate keyed on
# exit status is safe), but the OUTPUT lies: the real error count never appears,
# and a grep asking "are there errors in MY files?" comes back empty and reads as
# a pass.  Measured 2026-07-20: 3 errors reported from ``loremaster/`` vs the true
# 55 from the root.  It produced a false all-clear for two separate readers in one
# session before anyone noticed, so cwd is no longer allowed to change the verdict.
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.."

MEMBERS=(lorerunes lorescribe loresigil loremaster)
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
