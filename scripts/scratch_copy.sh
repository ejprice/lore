#!/usr/bin/env bash
#
# Make a scratch copy of this repo that ACTUALLY RUNS ITS OWN CODE — finding #140.
#
# WHY THIS EXISTS
#   A `cp -a` copy of this repo NEVER RUNS ITS OWN PRODUCTION CODE:
#     * `.venv` carries editable installs (`_editable_impl_loremaster.pth` &c.) whose
#       contents are ABSOLUTE ORIGINAL PATHS.  Copy the `.venv` and `import loremaster`
#       inside the copy resolves to the ORIGINAL checkout.
#     * `cp -a` preserves mtimes, so the copied `__pycache__` is reused and its bytecode
#       carries the ORIGINAL `co_filename` — even tracebacks name the original file.
#   A mutation proof or reference build made in such a copy is grading the tree it was
#   supposed to be isolated from, and NOTHING TELLS YOU.  The copy looks isolated,
#   `git diff` shows your mutation, the tests run — they are just not running your code.
#
# WHAT IT DOES
#   1. rsync the repo to DEST, EXCLUDING the poison sources (`.venv`, `__pycache__`) and
#      the derived caches (`.mypy_cache`, `.pytest_cache`, `.ruff_cache`) whose contents
#      are keyed on the ORIGINAL absolute paths.  `.git` is KEPT — agents run
#      `git diff` / `git status` in copies.
#   2. `uv sync --all-packages` in the copy.  MEASURED, not assumed: plain `uv sync` does
#      NOT install the workspace members at all — `import loremaster` then silently
#      succeeds as an implicit NAMESPACE PACKAGE with `__file__ is None`, and no
#      production code is loaded.  `--all-packages` mints editable `.pth` files naming
#      the COPY's own paths.
#   3. ASSERTS THE PROVENANCE AND FAILS LOUD (scripts/scratch_provenance.py, run with the
#      COPY's interpreter): every workspace member must import from INSIDE DEST.  A tool
#      that handed back a poisoned copy silently would launder the exact defect it exists
#      to prevent — so a failed assertion is a non-zero exit, never a warning.
#
# USAGE
#   ./scripts/scratch_copy.sh /abs/path/to/scratch/copy       # copy + install + verify
#   ./scripts/scratch_copy.sh --force /abs/path/existing      # replace an existing DEST
#   ./scripts/scratch_copy.sh --verify-only /abs/path/to/dir  # re-verify a copy you have
#
# Quiet on success apart from the receipt the caller needs (the path + where each member
# actually resolved).  Loud, and non-zero, on anything else.

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PROVENANCE_GUARD="${REPO_ROOT}/scripts/scratch_provenance.py"

usage() {
    cat <<'EOF'
usage: scratch_copy.sh [--force] [--verify-only] <ABSOLUTE-DEST>

  <ABSOLUTE-DEST>   where the scratch copy lives; must be an absolute path OUTSIDE the repo
  --force           replace an existing DEST (default: refuse to touch it)
  --verify-only     do not copy or install; only assert an existing DEST's provenance
EOF
}

# Assert that the tree at $1 imports every workspace member from INSIDE itself.
# The guard's CODE comes from the original repo (a copy must not be allowed to grade
# itself), but it runs under the COPY's interpreter — so what it observes is exactly
# what the copy will run.
verify_provenance() {
    local target="${1%/}"
    local interpreter="${target}/.venv/bin/python"

    if [[ ! -x "${interpreter}" ]]; then
        echo "scratch_copy: no interpreter at ${interpreter} — this tree has no .venv." >&2
        echo "scratch_copy: run without --verify-only, or 'uv sync --all-packages' inside it." >&2
        return 1
    fi

    ( cd -- "${target}" && "${interpreter}" "${PROVENANCE_GUARD}" "${target}" )
}

force=0
verify_only=0
dest=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force) force=1; shift ;;
        --verify-only) verify_only=1; shift ;;
        -h|--help) usage; exit 0 ;;
        -*) echo "scratch_copy: unknown option: $1" >&2; usage >&2; exit 2 ;;
        *)
            if [[ -n "${dest}" ]]; then
                echo "scratch_copy: unexpected extra argument: $1" >&2
                exit 2
            fi
            dest="$1"; shift ;;
    esac
done

if [[ -z "${dest}" ]]; then
    echo "scratch_copy: DEST is required" >&2
    usage >&2
    exit 2
fi

if [[ "${dest}" != /* ]]; then
    echo "scratch_copy: DEST must be an ABSOLUTE path (got '${dest}')." >&2
    echo "scratch_copy: a relative scratch path is ambiguous across agent contexts (#72)." >&2
    exit 2
fi

dest="${dest%/}"

if [[ -z "${dest}" ]]; then
    echo "scratch_copy: DEST must not be '/'." >&2
    exit 2
fi

# A copy INSIDE the repo gets indexed by lore, re-copied into the next copy, and picked up
# by the gates (#72).  Refuse it — including DEST == the repo itself, which would have this
# tool rsync the repo over itself.
case "${dest}/" in
    "${REPO_ROOT}/"*)
        echo "scratch_copy: DEST must live OUTSIDE the repo (${REPO_ROOT})." >&2
        echo "scratch_copy: a copy inside the repo gets indexed, gated, and re-copied (#72)." >&2
        exit 2 ;;
esac

# ...and DEST must not CONTAIN the repo either.  `--force` rsyncs with --delete, so a DEST
# of $HOME (or any ancestor) would delete everything in it that is not in the repo.  There
# is no legitimate scratch copy at an ancestor of the source.
case "${REPO_ROOT}/" in
    "${dest}/"*)
        echo "scratch_copy: DEST (${dest}) CONTAINS the repo — refusing." >&2
        echo "scratch_copy: --force rsyncs with --delete; this would destroy everything under it." >&2
        exit 2 ;;
esac

if [[ "${verify_only}" -eq 1 ]]; then
    if [[ ! -d "${dest}" ]]; then
        echo "scratch_copy: ${dest} does not exist — nothing to verify." >&2
        exit 2
    fi
    if ! receipt="$(verify_provenance "${dest}")"; then
        echo "scratch_copy: PROVENANCE CHECK FAILED for ${dest} — this copy must not be trusted." >&2
        exit 1
    fi
    echo "scratch copy VERIFIED: ${dest}"
    echo "${receipt}"
    exit 0
fi

if [[ -e "${dest}" && "${force}" -ne 1 ]]; then
    echo "scratch_copy: ${dest} already exists — refusing to overwrite it." >&2
    echo "scratch_copy: pass --force to replace its contents, or choose a fresh DEST." >&2
    exit 2
fi

mkdir -p -- "${dest}"

# rsync's --exclude PROTECTS an excluded path in DEST from --delete — so a stale, poisoned
# `.venv` already sitting in DEST would SURVIVE a --force rebuild.  (`uv sync` was measured
# to rewrite its editable .pth in that case, but the copy's honesty must not rest on a bet
# about uv's repair behaviour.)  Remove it: the copy's venv is always minted fresh.
if [[ -e "${dest}/.venv" ]]; then
    rm -rf -- "${dest}/.venv"
fi

# `.venv/` and `__pycache__/` are the two poison sources (see the header).  The three
# derived caches are excluded for the same reason one level down: their contents are keyed
# on the ORIGINAL absolute paths, and they regenerate for free.  `scratchpad/` is untracked
# session debris.  Everything else — including `.git` — is copied.
rsync -a --delete \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='.mypy_cache/' \
    --exclude='.pytest_cache/' \
    --exclude='.ruff_cache/' \
    --exclude='scratchpad/' \
    -- "${REPO_ROOT}/" "${dest}/"

# --all-packages, NOT a bare `uv sync`: a bare sync installs the dev group only, leaving the
# workspace members uninstalled and `import loremaster` resolving to an empty namespace
# package.  Measured on this repo, not assumed.
( cd -- "${dest}" && uv sync --all-packages --quiet )

if ! receipt="$(verify_provenance "${dest}")"; then
    echo "scratch_copy: PROVENANCE CHECK FAILED after building ${dest}." >&2
    echo "scratch_copy: the copy exists but MUST NOT BE TRUSTED. Check PYTHONPATH / VIRTUAL_ENV:" >&2
    echo "scratch_copy:   PYTHONPATH=${PYTHONPATH:-<unset>}  VIRTUAL_ENV=${VIRTUAL_ENV:-<unset>}" >&2
    echo "scratch_copy: either naming the original tree poisons every run inside the copy." >&2
    exit 1
fi

echo "scratch copy READY: ${dest}"
echo "  imports resolve INSIDE the copy:"
echo "${receipt}"
echo "  work in it with:  cd ${dest} && uv run pytest ..."
echo "  re-verify with:   ${REPO_ROOT}/scripts/scratch_copy.sh --verify-only ${dest}"
