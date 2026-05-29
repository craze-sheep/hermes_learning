#!/usr/bin/env bash
# WSL2 Quick System Audit — run all checks in one shot
# Usage: bash quick-audit.sh
set -euo pipefail

echo "=== System ==="
cat /etc/os-release | head -3
echo "CPU: $(nproc) cores"
echo "Memory: $(free -h | awk '/Mem:/{print $2}')"
echo ""

echo "=== WSL Config ==="
echo "--- wsl.conf ---"
cat /etc/wsl.conf 2>/dev/null || echo "[not found]"
echo ""
echo "--- .wslconfig ---"
WINUSER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r' || echo "unknown")
cat "/mnt/c/Users/${WINUSER}/.wslconfig" 2>/dev/null || echo "[not found]"
echo ""

echo "=== GPU ==="
/usr/lib/wsl/lib/nvidia-smi --query-gpu=name,memory.total,memory.used,temperature.gpu,utilization.gpu --format=csv,noheader 2>&1 || echo "[GPU not available]"
echo ""

echo "=== Docker ==="
docker info --format 'Version: {{.ServerVersion}} | Containers: {{.Containers}} ({{.ContainersRunning}} running) | Images: {{.Images}}' 2>&1 || echo "[Docker not running]"
echo ""
echo "Running:"
docker ps --format "  {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null
echo "Stopped:"
docker ps -a --filter "status=exited" --format "  {{.Names}}\t{{.Status}}" 2>/dev/null
echo ""
docker system df 2>/dev/null
echo ""

echo "=== Ports ==="
ss -tlnp 2>/dev/null | grep LISTEN | awk '{print $4}' | sort -t: -k2 -n
echo ""

echo "=== Resources ==="
free -h
echo ""
df -h / | tail -1
echo ""
swapon --show 2>/dev/null || echo "No swap"
echo ""

echo "=== Services ==="
echo "Failed:"
systemctl list-units --state=failed --no-pager 2>/dev/null | grep -v "^$" | head -5 || echo "  None"
echo ""
echo "Key services:"
for svc in docker hermes-gateway ssh; do
  STATUS=$(systemctl is-active "${svc}.service" 2>/dev/null || echo "not-found")
  ENABLED=$(systemctl is-enabled "${svc}.service" 2>/dev/null || echo "not-found")
  echo "  ${svc}: active=${STATUS} enabled=${ENABLED}"
done
echo ""

echo "=== Proxy ==="
env | grep -i "^[a-z]*_proxy=" 2>/dev/null | head -5 || echo "No proxy set"
echo ""

echo "=== Cron ==="
crontab -l 2>/dev/null || echo "No user crontab"
echo ""

echo "=== Hermes ==="
hermes --version 2>/dev/null || echo "[Hermes not installed]"
echo ""

echo "=== Windows Mount ==="
ls /mnt/c/Users/ >/dev/null 2>&1 && echo "C: OK" || echo "C: FAIL"
