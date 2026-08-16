#!/usr/bin/env bash
#
# In-image conformance harness — finding #139 (the test environment is a FICTION).
#
# WHY THIS EXISTS
#   A green test suite on the DEV HOST proves the SOURCE is correct in the test
#   environment — never that the deployed ARTIFACT is correct in production. Both of
#   lore's worst outages lived in exactly that gap (#107 virgin-DB migration, #131
#   git-not-in-image). This harness runs the BAKED pytest, from the deployed image,
#   over the mounted test tree — so it tests the CAKE, not the recipe.
#
# WHAT IT DOES
#   1. Starts an ephemeral container from IMAGE with the deploy's own run topology
#      (--network=host, keep-id + host uid:gid, the repo mounted :ro at /workspace).
#   2. PROVENANCE GATE FIRST: runs conformance_provenance.py with the baked interpreter.
#      It ASSERTS every workspace member imports from the BAKED artifact (/app/... or
#      site-packages), NOT the /workspace mount. If a member grades the mount the gate
#      aborts non-zero and pytest never runs — a green suite over the mount is worse
#      than a red one (#139). Provenance-BEFORE-pytest is load-bearing.
#   3. Only then runs the baked pytest over /workspace, `-n auto`, cache redirected to a
#      writable tmp dir (the :ro mount forbids the default .pytest_cache at rootdir).
#      LORE_CONFORMANCE_IN_CONTAINER=1 drives the source-type meta-tests to opt out
#      (they need a writable uv project env the :ro mount cannot provide).
#   The container's exit code (the guard's, or pytest's) propagates out as ours.
#
# USAGE
#   ./conformance_run.sh [IMAGE]     # IMAGE defaults to localhost/lore:latest
#
# Quiet-on-success apart from the guard receipts + pytest summary; loud, and non-zero,
# on any failure.

set -euo pipefail

IMAGE="${1:-localhost/lore:latest}"

# This script lives at skills/lore-deploy/scripts/ — the repo root is three levels up.
# The whole repo is mounted so pytest sees every member's test tree.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"

podman run --rm --network=host \
    --userns=keep-id --user "$(id -u):$(id -g)" \
    -v "${REPO_ROOT}":/workspace:ro \
    -e HOME=/tmp/h \
    -e PYTHONPYCACHEPREFIX=/tmp/pyc \
    -e LORE_CONFORMANCE_IN_CONTAINER=1 \
    -e OPENBLAS_NUM_THREADS=1 \
    -e OMP_NUM_THREADS=1 \
    "${IMAGE}" \
    sh -c '
set -eu
mkdir -p /tmp/h /tmp/pyc /tmp/ptc
PY=/app/.venv/bin/python

echo "### conformance: provenance gate (baked artifact, not the /workspace mount) ###"
"$PY" /workspace/skills/lore-deploy/scripts/conformance_provenance.py --mount-root /workspace

echo "### conformance: baked suite over /workspace (-n auto) ###"
cd /workspace
exec "$PY" -m pytest -o cache_dir=/tmp/ptc -n auto -q --no-header
'
