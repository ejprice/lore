#!/usr/bin/env bash
# THROWAWAY spike runner for packet 01a — FINAL mechanism: uv + LOCKED dev-group versions.
# Ephemeral container from the deployed image, faithful deploy topology, /workspace :ro,
# artifact-not-mount provenance assertion, whole suite -n auto.
set -uo pipefail
REPO="/home/ejprice/PycharmProjects/lore"
OUT="${REPO}/scratchpad/01a_incontainer_run.txt"

podman run --rm --network=host \
  --userns=keep-id --user "$(id -u):$(id -g)" \
  -v "${REPO}":/workspace:ro \
  -e HOME=/tmp/h -e UV_CACHE_DIR=/tmp/uvcache -e PYTHONPYCACHEPREFIX=/tmp/pyc \
  localhost/lore:latest \
  sh -c '
set -u
mkdir -p /tmp/h /tmp/uvcache /tmp/ptc
cd /workspace
echo "### export LOCKED dev group ###"
uv export --frozen --only-group dev --no-hashes --no-emit-project -o /tmp/dev-reqs.txt || { echo "EXPORT FAILED"; exit 2; }
echo "### venv --system-site-packages (artifact stays importable) + uv pip install pinned ###"
python -m venv --system-site-packages /tmp/cv
uv pip install --quiet --python /tmp/cv/bin/python -r /tmp/dev-reqs.txt || { echo "INSTALL FAILED"; exit 3; }
PY=/tmp/cv/bin/python
echo "### provenance assertion (artifact, not /workspace) ###"
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
echo "### full suite, -n auto, cache redirected ###"
"$PY" -m pytest -o cache_dir=/tmp/ptc -n auto -q -rfE --no-header 2>&1
echo "### pytest exit: $? ###"
' > "${OUT}" 2>&1
echo "DONE exit=$? -> ${OUT}"
