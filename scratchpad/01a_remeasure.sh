#!/usr/bin/env bash
# RE-MEASURE against the locked-deps image (localhost/lore:01a): pytest is BAKED,
# so no run-time install — run the baked runner against the mounted tests, with the
# provenance assertion gating.
set -uo pipefail
REPO="/home/ejprice/PycharmProjects/lore"
IMG="${1:-localhost/lore:01a}"
OUT="${REPO}/scratchpad/01a_remeasure_run.txt"

podman run --rm --network=host \
  --userns=keep-id --user "$(id -u):$(id -g)" \
  -v "${REPO}":/workspace:ro \
  -e HOME=/tmp/h -e PYTHONPYCACHEPREFIX=/tmp/pyc \
  "${IMG}" \
  sh -c '
set -u
mkdir -p /tmp/h /tmp/pyc /tmp/ptc
PY=/app/.venv/bin/python
echo "### provenance assertion (baked artifact, not /workspace) ###"
"$PY" - <<PYEOF
import sys, loremaster, loresigil, lorescribe
bad=[]
for m in (loremaster, loresigil, lorescribe):
    f = getattr(m, "__file__", None)
    print(f"{m.__name__:<11} -> {f}")
    if f is None or f.startswith("/workspace"):
        bad.append(m.__name__)
if bad:
    print("PROVENANCE FAIL:", bad); sys.exit(4)
print("PROVENANCE OK  pytest=" + __import__("pytest").__version__)
PYEOF
[ $? -ne 0 ] && { echo "ABORT: provenance failed"; exit 4; }
echo "### full suite (baked pytest), -n auto, cache redirected ###"
cd /workspace
"$PY" -m pytest -o cache_dir=/tmp/ptc -n auto -q -rfE --no-header 2>&1
echo "### pytest exit: $? ###"
' > "${OUT}" 2>&1
echo "DONE exit=$? -> ${OUT}"
