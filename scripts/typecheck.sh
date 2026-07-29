#!/usr/bin/env bash
#
# Canonical STATIC-ANALYSIS gate for the lore workspace: one mypy iteration per
# typecheck root, plus one shellcheck leg over every tracked ``.sh``.
#
# WHY THE SHELL LEG LIVES HERE rather than in its own runner (packet 44, 2026-07-29).
# The repo had SEVEN committed ``.sh`` files and no shell gate of any kind — including
# this file, the canonical gate itself, and ``scratch_copy.sh``, which CLAUDE.md orders
# every mutating agent to use. A second runner would have been an eighth ``.sh`` that
# nothing runs, i.e. a fresh instance of the class packet 44 exists to close: *a guard
# nobody runs is a hope with a filename*, and both of packet 03b's instruments were
# victims of exactly that. There is one command this repo's law names as a commit gate,
# and it is this one, so the leg rides it. The first thing it caught was a real defect in
# this very file — see the ``|| exit`` on the ``cd`` below.
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
#
# ⚠ AND THE GUARD THE PARAGRAPH ABOVE FORGOT TO WRITE (SC2164, found by this file's own
# new shellcheck leg, 2026-07-29). An unguarded ``cd`` that FAILS leaves the shell in the
# caller's directory and the script runs on regardless — producing the *exact* lying
# output the paragraph above spends nine lines describing, from the one direction it did
# not defend. The prose knew; nothing enforced it. So: ``|| exit 1``.
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.." || exit 1

# ``MEMBERS`` IS A LIST OF TYPECHECK ROOTS, NOT OF WORKSPACE MEMBERS — the name is
# historical and two of the entries are not members at all. Read it as "every tree mypy
# must cover".
#
# * ``skills`` is the deploy skill's script tree (ruling R9, packet 42). It was ungated
#   ground in every other respect WHEN R9 WAS WRITTEN, and packet 42 audits a resolver
#   that LIVES there: an AST pin covered its SHAPE, nothing covered its TYPES. (Packet 44
#   closed the other half on 2026-07-29 — ``skills/lore-deploy/{scripts,tests}`` are now
#   ``testpaths`` entries — so the tree is no longer ungated on either axis.)
# * ``docs/eval`` is the deploy smoke — ``smoke_p8b.py``, the instrument that caught #107
#   and #131, each time as the only thing looking — plus that smoke's own suite (#238 put
#   those tests in ``testpaths``; this is the other half, #261).
#
# Every entry is its own iteration, never merged into one ``mypy`` call (see the header).
MEMBERS=(lorerunes lorescribe loresigil loremaster skills docs/eval)

# Per-root MYPYPATH additions. A root absent from this map runs with the ``mypy_path``
# declared in ``pyproject.toml`` and nothing more.
#
# ⚠ WHY THIS IS LEG-SCOPED AND NOT A GLOBAL ``[tool.mypy] mypy_path`` ENTRY (#261).
# ``docs/eval/test_smoke_p8b.py`` does ``import smoke_p8b``, which resolves at runtime
# (pytest's rootdir-relative collection) but not for mypy, which reports 7 spurious
# ``import-not-found``/follow-on errors — measured 2026-07-29 at ``5a850c3``, and 0 with
# the env var. Putting ``docs/eval`` on the GLOBAL path would fix those 7 and manufacture
# a worse failure: a stray ``import smoke_p8b`` inside ``loremaster`` would then
# type-check clean here and ``ImportError`` in the deployed image — a mypy-made false
# clear of exactly the #131 shape. So the resolution exists in the leg that needs it and
# nowhere else.
#
# ⚠ FOR THE HAND-RUNNER: a bare ``uv run mypy docs/eval`` still shows those 7. The
# invocation that matches this gate is ``MYPYPATH=docs/eval uv run mypy docs/eval``.
declare -A MEMBER_MYPYPATH=(
    [docs/eval]="docs/eval"
)

status=0

for member in "${MEMBERS[@]}"; do
    extra_path="${MEMBER_MYPYPATH[${member}]:-}"
    if [[ -n "${extra_path}" ]]; then
        leg=(env "MYPYPATH=${extra_path}" uv run mypy "${member}")
    else
        leg=(uv run mypy "${member}")
    fi
    if "${leg[@]}"; then
        echo "typecheck: ${member} OK"
    else
        echo "typecheck: ${member} FAILED" >&2
        status=1
    fi
done

# ---------------------------------------------------------------------------
# THE SHELL LEG — every tracked ``.sh``, DERIVED, never listed
# ---------------------------------------------------------------------------
#
# The file set comes from ``git ls-files '*.sh'`` because a hardcoded list is the one
# artifact this repo has the most receipts against: CLAUDE.md's registration-site
# enumeration was WRONG FOUR TIMES, every time while the law about it was being written.
# A derived set covers the eighth shell script nobody has added yet.
#
# ⚠ ANTI-VACUITY. An empty file set is a FAILURE, and the count is printed on success so
# a silently SHRINKING set is visible too. A broken ``git ls-files`` — wrong cwd, not a
# repo, a glob that stops matching — must never read as a clean tree.
#
# ⚠⚠ AND THE HONEST VERSION OF WHY, because the first draft of this comment asserted the
# wrong reason and a measurement caught it (2026-07-29). It claimed ``shellcheck`` with no
# file arguments "reads stdin and exits 0", making an empty set a silent green. **That is
# false**: measured, it prints its usage summary and exits **3**, so the ``elif`` below
# would take the FAILED branch and the gate would go red anyway. The guard stays for two
# reasons that survive the correction, and they are better ones:
#   1. It DIAGNOSES. Without it the operator reads "shellcheck FAILED" and goes hunting for
#      shell defects that do not exist, when the real fault is that the file enumeration
#      broke. A gate that misattributes its own failure costs a session.
#   2. It makes the invariant OURS. "Empty set is not a pass" would otherwise be a
#      property of a third-party tool's argument handling, which is free to change under
#      us. This is the same reason the mypy legs do not lean on exit codes alone.
# The correction is left in place rather than tidied away: this file is a gate, and a gate
# whose comments assert unverified behaviour of its own dependency is the #107 shape.
shell_files=()
while IFS= read -r -d '' tracked_shell_file; do
    shell_files+=("${tracked_shell_file}")
done < <(git ls-files -z '*.sh')

if [[ "${#shell_files[@]}" -eq 0 ]]; then
    echo "typecheck: shellcheck ABORTED — \`git ls-files '*.sh'\` matched nothing. This is a" >&2
    echo "           BROKEN INSTRUMENT, not a clean tree: do not read it as a pass." >&2
    status=1
elif uv run shellcheck "${shell_files[@]}"; then
    echo "typecheck: shellcheck OK (${#shell_files[@]} tracked .sh)"
else
    echo "typecheck: shellcheck FAILED" >&2
    status=1
fi

if [[ "${status}" -ne 0 ]]; then
    echo "typecheck: one or more legs failed" >&2
fi

exit "${status}"
