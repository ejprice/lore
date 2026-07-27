#!/bin/bash
# E-3 hunt, take 2 — under a HARD FREEZE. Take 1 was invalid because a sibling
# agent mutated the subject mid-loop (24 runs collected 196, one collected 197,
# two died in collection). This adds the detector that would have caught that
# at the time, instead of afterwards.
#
# FREEZE PROOF, per iteration:
#   - git HEAD and `git status --porcelain` are captured before and after EVERY
#     run and compared. Any change aborts the loop rather than producing a number.
#   - the COLLECTED TEST COUNT is asserted identical to run 1's. A moving count
#     is exactly how take 1 lied, so it is a checked variable, not an assumption.
# Full per-run output is kept; the store's log window is captured on failure.
#
# USAGE:  scripts/contention_hunt.sh [ITERATIONS] [OUTPUT_DIR]
#   ITERATIONS  default 30. Twenty is this repo's floor for clearing a
#               concurrency test; thirty leaves margin.
#   OUTPUT_DIR  default `$(mktemp -d)`, printed on the first line so the run is
#               findable. Pass a path to keep the evidence somewhere durable.
#
# The repo root is derived from THIS SCRIPT'S OWN LOCATION, never hardcoded, so
# the instrument works in any worktree — including the sibling worktrees this
# defect was found in. (The first version of this file hardcoded one absolute
# worktree path and one session-specific /tmp path, which would have made it a
# script that only ever worked once, for one agent. A committed instrument that
# only its author can run is not an instrument.)
set -u
ITERS="${1:-30}"
WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${2:-$(mktemp -d -t contention-hunt-XXXXXX)}"
mkdir -p "$OUT"
TL="$OUT/00-timeline.txt"
echo "contention_hunt: repo=$WT  iterations=$ITERS  output=$OUT"

cd "$WT" || exit 1
HEAD0=$(git rev-parse HEAD)
DIRT0=$(git status --porcelain | md5sum | cut -d' ' -f1)
echo "FREEZE BASELINE  head=$HEAD0  worktree-hash=$DIRT0  $(date -Is)" > "$TL"

CONTRACT="loremaster/tests/test_floor_calibration_domain.py
loremaster/tests/test_floor_calibration_schema.py
loremaster/tests/test_floor_calibration_store.py
loremaster/tests/test_store_lease.py"

# Establish the post-full-suite condition the original failure's timing fitted.
echo "--- full suite (recreates the post-suite window) ---" >> "$TL"
uv run --no-sync pytest -n auto -q > "$OUT/00-fullsuite.txt" 2>&1
tail -2 "$OUT/00-fullsuite.txt" >> "$TL"

BASE_COLLECTED=""
fails=0
for i in $(seq 1 "$ITERS"); do
    RUN="$OUT/run-$(printf '%02d' "$i").txt"
    { echo "=== run $i start $(date -Is) ==="
      uv run --no-sync pytest -n auto -q --tb=long -rf $CONTRACT 2>&1
      echo "=== pytest exit: $? ==="; } > "$RUN" 2>&1

    # Freeze check — the detector take 1 lacked.
    H=$(git rev-parse HEAD); D=$(git status --porcelain | md5sum | cut -d' ' -f1)
    if [ "$H" != "$HEAD0" ] || [ "$D" != "$DIRT0" ]; then
        echo "ABORT at run $i: TREE MOVED (head=$H dirt=$D). Result discarded." >> "$TL"; exit 2
    fi

    N=$(grep -oE "[0-9]+ (passed|failed)" "$RUN" | awk '{s+=$1} END {print s}')
    [ -z "$BASE_COLLECTED" ] && BASE_COLLECTED="$N"
    if [ "$N" != "$BASE_COLLECTED" ]; then
        echo "ABORT at run $i: COLLECTED COUNT MOVED ($N vs $BASE_COLLECTED)." >> "$TL"; exit 3
    fi

    if grep -qE "^[0-9]+ failed|error" "$RUN"; then
        fails=$((fails + 1))
        echo "run $i: FAILED  $(grep -E '^[0-9]+ failed|^[0-9]+ error' "$RUN" | tail -1)  [collected=$N]" >> "$TL"
        podman logs --since 3m spike-surreal > "$OUT/run-$(printf '%02d' "$i")-storelog.txt" 2>&1
    else
        echo "run $i: green   $(grep -E '^[0-9]+ passed' "$RUN" | tail -1)  [collected=$N]" >> "$TL"
    fi
done
echo "TOTAL FAILING RUNS: $fails / $ITERS   (freeze held: head and worktree unchanged throughout)" >> "$TL"
echo "done $(date -Is)" >> "$TL"
