#!/bin/bash
PID=1712899
LOG=/home/ejprice/PycharmProjects/lore/scratchpad/eval-runner-3/run.log
MAXWAIT=3600
elapsed=0
while ps -p "$PID" > /dev/null 2>&1; do
  sleep 20
  elapsed=$((elapsed+20))
  if [ "$elapsed" -ge "$MAXWAIT" ]; then
    echo "WATCHDOG: exceeded ${MAXWAIT}s, still running, giving up wait"
    break
  fi
done
echo "DONE: pid $PID exited (or watchdog timeout) after ${elapsed}s"
tail -n 30 "$LOG"
