#!/usr/bin/env bash
# Recreate both lore containers on the freshly-built :latest, from their captured
# CreateCommands, then boot-smoke each. Run ONLY after conform against :latest is GREEN.
set -uo pipefail
D="/home/ejprice/PycharmProjects/lore/scratchpad/deploy"

recreate() {
  local name="$1"
  echo "=== recreate ${name} ==="
  mapfile -t argv < <(jq -r '.[]' "${D}/${name}.createcmd.json")
  podman stop "${name}" >/dev/null 2>&1 || true
  podman rm "${name}"   >/dev/null 2>&1 || true
  "${argv[@]}"   # podman run -d --name ... localhost/lore:latest (now the NEW image)
  echo "  launched ${name} on $(podman inspect "${name}" --format '{{.Image}}' | cut -c1-12)"
}

smoke() {
  local name="$1" port="$2" timeout="$3"
  echo "=== boot-smoke ${name} (port ${port}, up to ${timeout}s) ==="
  local i=0
  while [ "$i" -lt "$timeout" ]; do
    if python3 -c "import socket,sys; s=socket.socket(); s.settimeout(1)
try: s.connect(('127.0.0.1',${port})); print('bound'); sys.exit(0)
except Exception: sys.exit(1)" 2>/dev/null; then
      echo "  ${name}: port ${port} ACCEPTING after ${i}s"
      podman ps --filter "name=${name}" --format '  {{.Names}} {{.Status}}'
      echo "  --- last serving log lines ---"
      podman logs --tail 6 "${name}" 2>&1 | sed 's/^/    /'
      return 0
    fi
    # fail fast if the container died
    if ! podman ps --filter "name=${name}" --filter status=running -q | grep -q .; then
      echo "  ${name}: CONTAINER NOT RUNNING — crash? logs:"
      podman logs --tail 20 "${name}" 2>&1 | sed 's/^/    /'
      return 1
    fi
    sleep 5; i=$((i+5))
  done
  echo "  ${name}: TIMEOUT — port ${port} never bound in ${timeout}s"; return 1
}

recreate lore-lore
recreate lore-demand_intelligence
echo
smoke lore-demand_intelligence 9201 60   || { echo "DI SMOKE FAILED"; exit 1; }
smoke lore-lore 9202 240                 || { echo "LORE SMOKE FAILED"; exit 1; }
echo "=== BOTH RECREATED + SMOKED GREEN ==="
