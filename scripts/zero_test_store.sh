#!/usr/bin/env bash
# Zero the TEST SurrealDB store (spike-surreal, :18000). Finding #246.
#
# WHY THIS EXISTS, and why it is a script and not a reaper:
#   Test databases are minted per test (`test_<pid>_<uuid4>`) and reaped in a `finally`. That
#   reap does not survive SIGKILL, so every hard-killed run leaves orphans behind -- 555 of them
#   had accumulated by 2026-07-26 (#240).
#
#   The instinct is to fix the EXIT path: catch SIGTERM, reap harder. That approach is
#   structurally capped, because SIGKILL is uncatchable (#243, measured, superseded).
#
#   CLEANUP ON START IS ROBUST TO ANY DEATH; CLEANUP ON EXIT IS ONLY AS ROBUST AS THE EXIT PATH.
#   So this never asks how the previous run died. It does not inspect, classify, age out, or
#   check pid-liveness -- 291 of the observed orphans carried no pid at all, which is why
#   pid-liveness was rejected as a safety predicate on merit. It just zeroes the lot.
#
#   That is safe ONLY because we do not care a whit about the test database (operator,
#   2026-07-26). If this store ever holds something worth keeping -- a shared fixture corpus, a
#   golden dataset, a benchmark baseline -- this script is WRONG and #246 is void.
#
# WHAT IT DELIBERATELY DOES NOT DO:
#   * It does NOT touch production (`lore-surreal`, :18500). It names only the test unit.
#   * It does NOT switch the store to SurrealDB's `memory` backend, which would be simpler
#     still. Production runs RocksDB, and this repo's two worst outages (#107, #131) both lived
#     in the gap between the test and production environments. Do not buy tidiness with a new
#     test/prod divergence.
#
# THE ONE REAL HAZARD is a concurrent run: zeroing mid-suite destroys another session's work,
# and two sessions were live against :18000 on 2026-07-26. Hence the guard below -- it is the
# difference between a timer that is safe to schedule and one that eventually eats a live run.
#
# Usage:  scripts/zero_test_store.sh [--force]
#   --force  skip the running-pytest guard (you are certain nothing is running)
# Exit:   0 zeroed, or skipped because a run is in flight (Unix philosophy: silent on success)
#         1 something went wrong -- loud, with the reason
set -euo pipefail

readonly UNIT="spike-surreal.service"
readonly STORE_DIR="${HOME}/.local/state/lore/spike-surreal-data"
readonly STORE_DB="${STORE_DIR}/store.db"
readonly TEST_PORT=18000
readonly PROD_PORT=18500

force=0
[[ "${1:-}" == "--force" ]] && force=1

# Refuse to run against anything but the test unit. Cheap, and the failure it prevents is
# catastrophic and unrecoverable.
if ! systemctl --user cat "${UNIT}" 2>/dev/null | grep -q "127.0.0.1:${TEST_PORT}"; then
    echo "REFUSING: ${UNIT} does not bind 127.0.0.1:${TEST_PORT}." >&2
    echo "This script zeroes the TEST store only. :${PROD_PORT} is PRODUCTION." >&2
    exit 1
fi

# The guard. A live suite is minting and reaping databases in this store right now; wiping it
# mid-run destroys that session's work and produces failures nobody can explain later.
if (( ! force )) && pgrep -f "bin/pytest" >/dev/null 2>&1; then
    exit 0
fi

systemctl --user stop "${UNIT}"

# Remove the RocksDB directory only -- not the parent, which the quadlet bind-mounts and which
# must survive for the container to start.
rm -rf "${STORE_DB}"

systemctl --user start "${UNIT}"

# Prove the store came back. Without this the script would report success for a store that
# failed to restart -- a green measurement after a failed setup looks exactly like the thing
# you hoped for.
for _ in {1..30}; do
    if timeout 1 bash -c "</dev/tcp/127.0.0.1/${TEST_PORT}" 2>/dev/null; then
        exit 0
    fi
    sleep 1
done

echo "FAILED: ${UNIT} did not accept connections on :${TEST_PORT} within 30s after zeroing." >&2
echo "The store directory WAS removed. Check: systemctl --user status ${UNIT}" >&2
exit 1
