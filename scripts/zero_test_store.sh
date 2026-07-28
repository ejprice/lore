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
readonly SECRETS_ENV="/home/ejprice/docker/mcp/lore-secrets/lore.env"
# _surreal_harness.DEFAULT_USER / DEFAULT_PASS -- the credentials the whole suite signs in with.
# These are TEST-store credentials for a store we deliberately do not care about; production
# rejects them (measured, finding #240 investigation).
readonly HARNESS_USER="root"
readonly HARNESS_PASS="spikeroot"

force=0
[[ "${1:-}" == "--force" ]] && force=1

# Refuse to run against anything but the test unit. Cheap, and the failure it prevents is
# catastrophic and unrecoverable.
if ! systemctl --user cat "${UNIT}" 2>/dev/null | grep -q "127.0.0.1:${TEST_PORT}"; then
    echo "REFUSING: ${UNIT} does not bind 127.0.0.1:${TEST_PORT}." >&2
    echo "This script zeroes the TEST store only. :${PROD_PORT} is PRODUCTION." >&2
    exit 1
fi

# THE GUARD. A live suite is minting and reaping databases in this store right now; wiping it
# mid-run destroys that session's work and produces failures nobody can explain later.
#
# ⚠ THIS GUARD WAS `pgrep -f "bin/pytest"` AND IT WAS WRONG (caught on its first real run,
# 2026-07-27). `pgrep -f` matches the whole COMMAND LINE, so it fired on: a sibling session's
# watcher (`bash -c while pgrep -f "bin/pytest -n auto -q" ...`), and on shell wrappers that
# merely MENTION pytest -- including the very command checking it. Result: the script exited 0,
# silently, having done NOTHING, and the liveness check below still passed because the store had
# never gone down. A guard keyed on a SUBSTRING OF A NAME, defeated by a string that is not the
# thing -- the repo's own six-times-over instrument lesson (CLAUDE.md, "the forbidden set is
# unbounded").
#
# The fix is not a cleverer pattern; that is the same trap. MEASURE THE ACTUAL HAZARD: is anything
# CONNECTED to the store? A suite that could lose work necessarily holds a socket.
connections=$(ss -tn state established "( sport = :${TEST_PORT} or dport = :${TEST_PORT} )" \
              2>/dev/null | tail -n +2 | wc -l)
if (( ! force )) && (( connections > 0 )); then
    exit 0
fi

systemctl --user stop "${UNIT}"

# Remove the RocksDB directory only -- not the parent, which the quadlet bind-mounts and which
# must survive for the container to start.
rm -rf "${STORE_DB}"

# ⚠ ASSERT THE REMOVAL LANDED. This is the line whose absence made the original failure silent:
# every later step (restart, liveness) succeeds just as happily over a store that was never
# touched. Ask of any multi-step verification: "if step N silently no-opped, would step N+1 still
# print something that reads as success?" Here it did.
if [[ -e "${STORE_DB}" ]]; then
    echo "FAILED: ${STORE_DB} still exists after rm -rf. The store was NOT zeroed." >&2
    systemctl --user start "${UNIT}"
    exit 1
fi

systemctl --user start "${UNIT}"

# Prove the store came back. Without this the script would report success for a store that
# failed to restart -- a green measurement after a failed setup looks exactly like the thing
# you hoped for.
#
# ⚠ LIVENESS IS NECESSARY, NOT SUFFICIENT: a store that never got wiped also accepts connections.
# That is why the removal is ASSERTED above rather than inferred from this check passing. This
# loop answers "did it come back?", never "did it get zeroed?" -- two different questions that
# the original version conflated, which is exactly how it reported success for a no-op.
up=0
for _ in {1..30}; do
    if timeout 1 bash -c "</dev/tcp/127.0.0.1/${TEST_PORT}" 2>/dev/null; then
        up=1
        break
    fi
    sleep 1
done

if (( ! up )); then
    echo "FAILED: ${UNIT} did not accept connections on :${TEST_PORT} within 30s after zeroing." >&2
    echo "The store directory WAS removed. Check: systemctl --user status ${UNIT}" >&2
    exit 1
fi

# ⚠ RE-PROVISION THE HARNESS ROOT USER. Without this the script is a FOOTGUN: it leaves a
# perfectly healthy store that the entire test suite cannot authenticate against.
#
# MEASURED 2026-07-27, on this script's first real run. A fresh store bootstraps ONLY the user in
# SURREAL_USER (the container log says so verbatim: "no root users were found. The root user
# 'lore' will be created"). But `_surreal_harness.DEFAULT_USER`/`DEFAULT_PASS` are `root` /
# `spikeroot` -- a user that existed only because it had once been DEFINEd INTO the old store and
# PERSISTED there. Zeroing removed it, and every test then failed to sign in.
#
# That is the exact assumption finding #246 flagged as unverified ("whether anything depends on
# store persistence -- the one thing that would break"). It was not a test. It was the credentials
# every test uses.
if [[ -r "${SECRETS_ENV}" ]]; then
    (
        set -a; . "${SECRETS_ENV}"; set +a
        curl -fsS -u "${SURREAL_USER}:${SURREAL_PASS}" -X POST \
             -H "Accept: application/json" -H "surreal-ns: main" -H "surreal-db: main" \
             --data-binary "DEFINE USER IF NOT EXISTS ${HARNESS_USER} ON ROOT PASSWORD '${HARNESS_PASS}' ROLES OWNER;" \
             "http://127.0.0.1:${TEST_PORT}/sql" >/dev/null
    ) || {
        echo "FAILED: store was zeroed and restarted, but re-provisioning the harness root user" >&2
        echo "('${HARNESS_USER}') failed. The suite will NOT authenticate until this is fixed." >&2
        exit 1
    }
else
    echo "FAILED: cannot read ${SECRETS_ENV}, so the harness root user was NOT re-provisioned." >&2
    echo "The store is zeroed and running, but the suite will NOT authenticate." >&2
    exit 1
fi

# ASSERT the re-provisioning actually took -- same law as the removal assert above. A DEFINE that
# silently no-ops leaves a store that looks fine and fails every test.
if ! curl -fsS -u "${HARNESS_USER}:${HARNESS_PASS}" -X POST \
        -H "Accept: application/json" -H "surreal-ns: main" -H "surreal-db: main" \
        --data-binary "INFO FOR ROOT;" "http://127.0.0.1:${TEST_PORT}/sql" >/dev/null; then
    echo "FAILED: harness user '${HARNESS_USER}' still cannot authenticate after re-provisioning." >&2
    exit 1
fi

exit 0
