#!/usr/bin/env bash
#
# tree_fingerprint.sh — fingerprint the working tree, so a gate result is a claim
# about a TREE and not just a number (finding #192).
#
# WHY THIS EXISTS. A suite count says "6605 passed". It does NOT say WHICH tree
# passed. In a shared checkout with several agents working at once, a file can
# change seconds before a run ends and the count is still printed, green and
# unfalsifiable. Capture this BEFORE and AFTER a run and diff the two: an empty
# diff turns "the gates passed" into "the gates passed on a tree that provably
# did not move under them".
#
#     ./scripts/tree_fingerprint.sh > /tmp/before.txt
#     uv run pytest -n auto -q
#     ./scripts/tree_fingerprint.sh > /tmp/after.txt
#     diff /tmp/before.txt /tmp/after.txt && echo "tree held"
#
# WHAT IT EMITS, and why it is three things rather than one:
#
#   HEAD              a commit landed (a sibling committing mid-run)
#   STATUS_LINES + the listing   an UNTRACKED file appeared, or a tracked one was
#                     edited but not committed
#   TRACKED_TREE_MD5  DETECTION over the whole tracked tree — a CLOSED set.
#                     Index blobs PLUS the unstaged diff, because index blobs
#                     alone miss an uncommitted edit (see the note at the line
#                     that computes it).
#   the per-file MD5s DIAGNOSIS: which file moved
#
# DETECT ON THE CLOSED SET, DIAGNOSE WITH THE LIST. The per-file hashes alone are
# a NAME LIST, and the set of files a sibling might touch is unbounded — an edit
# to a file nobody predicted is invisible to them. TRACKED_TREE_MD5 covers every
# tracked file, so it is the only complete detector here; the named files exist
# to tell you WHICH one moved once it has.
#
# ⚠ BOUNDS, stated because a fingerprint that quietly misses a case is WORSE than
# none — it converts "unproven" into "proven":
#
#   * It covers TRACKED files only. A brand-new untracked file does not move the
#     tree hash; it moves STATUS_LINES.
#   * A sibling who commits mid-run moves HEAD, and may leave the tree hash and
#     status count unchanged.
#   * Therefore all three lines are load-bearing and NONE alone is sufficient.
#   * It fingerprints the TREE, not the environment: an installed-dependency or
#     interpreter change is out of scope and invisible here.
#
# READING A DIFF (the interpretation is the point, not the bytes):
#
#   status ↑, tree hash same, HEAD same   an untracked sibling artifact appeared.
#                                         BENIGN — the code under test did not move.
#   tree hash changed, HEAD moved         a commit landed. Check whether it touched
#                                         code under test; a docs-only commit is benign.
#   tree hash changed, HEAD UNCHANGED     ⚠ AN UNCOMMITTED EDIT TO A TRACKED FILE,
#                                         mid-run. THIS is the shape that spoils a
#                                         receipt. Re-run.
#
# Read-only by construction: it runs `git rev-parse`, `git status`, `git ls-files`
# and `md5sum`, and writes nothing. `scripts/test_tree_fingerprint.py` pins that.

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    sed -n '2,60p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
fi

echo "HEAD=$(git rev-parse --short HEAD)"
echo "STATUS_LINES=$(git status --short | wc -l | tr -d ' ')"
git status --short | sed 's/^/  /'
# ⚠ `git ls-files -s` ALONE IS NOT ENOUGH, and this was caught by this helper's
# own control rather than by reasoning: it reports the INDEX blob for each
# tracked file, so an UNCOMMITTED edit to a tracked file does not move it — which
# is precisely the one shape that spoils a gate receipt. Adding `git diff`
# (worktree-vs-index) completes it: index blobs pin the staged content, the diff
# pins everything not yet staged, and together they determine the working-tree
# content of every tracked file. Still a CLOSED set, still no name list.
echo "TRACKED_TREE_MD5=$({ git ls-files -s; git diff; } | md5sum | cut -d' ' -f1)"

# DIAGNOSIS ONLY — never the detector. Any path given on the command line is
# hashed and named, so a caller can say which files it cares about WITHOUT that
# list being what decides whether the tree moved.
for path in "$@"; do
    if [[ -f "$path" ]]; then
        echo "  $(md5sum "$path")"
    else
        echo "  MISSING  $path"
    fi
done
