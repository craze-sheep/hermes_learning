#!/bin/bash
# Per-process inotify watch breakdown
# Shows which processes are consuming the most inotify watches
# Usage: bash scripts/inotify-breakdown.sh [top_n]

TOP=${1:-15}
LIMIT=$(cat /proc/sys/fs/inotify/max_user_watches)

echo "inotify watches limit: $LIMIT"
echo ""

RESULTS=""
TOTAL=0

for pid in $(ls /proc/ 2>/dev/null | grep -E '^[0-9]+$'); do
  fds=$(ls -la /proc/$pid/fd 2>/dev/null | grep inotify | awk '{print $9}')
  if [ -n "$fds" ]; then
    for fd in $fds; do
      count=$(grep -c '^inotify wd:' /proc/$pid/fdinfo/$fd 2>/dev/null || echo 0)
      if [ "$count" -gt 0 ]; then
        cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' | cut -c1-80)
        RESULTS="${RESULTS}pid=$pid fd=$fd watches=$count cmd=$cmd\n"
        TOTAL=$((TOTAL + count))
      fi
    done
  fi
done 2>/dev/null

echo -e "$RESULTS" | sort -t= -k3 -rn | head -$TOP
echo ""
PCT=$((TOTAL * 100 / LIMIT))
echo "Total: $TOTAL / $LIMIT ($PCT%)"
if [ "$PCT" -ge 80 ]; then
  echo "⚠️  CRITICAL: >80% used — expect ENOSPC errors soon"
elif [ "$PCT" -ge 50 ]; then
  echo "⚠️  WARNING: >50% used"
else
  echo "✅ OK"
fi
