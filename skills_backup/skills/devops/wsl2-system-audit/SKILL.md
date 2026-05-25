---
name: wsl2-system-audit
description: "Comprehensive WSL2 system audit — check wsl.conf, .wslconfig, systemd services, Docker, GPU, ports, proxy, memory, locale, cron, and report issues with severity levels."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux]
metadata:
  hermes:
    tags: [wsl, systemd, docker, audit, system-check, configuration]
    related_skills: [wsl2-gpu-support, kubric-gpu-docker]
---

# WSL2 System Audit

Perform a comprehensive health check of a WSL2 environment. Produces a structured report with severity levels (✅ normal / ⚠️ issue / 💡 optimization).

## When to Use

- User asks "check my WSL config" / "全面检查" / "system audit"
- After major configuration changes to verify nothing broke
- Before scaling workloads (more Docker containers, new services)
- Periodic health checks

## Audit Checklist (Run in Order)

### 1. System Identity

```bash
cat /etc/os-release | head -5
nproc
cat /proc/meminfo | grep MemTotal
```

### 2. WSL Configuration Files

```bash
cat /etc/wsl.conf
cat /mnt/c/Users/<winuser>/.wslconfig
```

Check for:
- `systemd=true` in wsl.conf (needed for systemctl)
- `networkingMode=mirrored` in .wslconfig (enables localhost from Windows)
- `memory=` and `swap=` in .wslconfig — compare with actual `free -h`

### 3. Systemd Services

```bash
# Enabled services
systemctl list-unit-files --state=enabled --type=service --no-pager

# Failed services
systemctl list-units --state=failed --no-pager

# Key service statuses
systemctl is-enabled docker.service
systemctl is-active docker.service
```

Report: services that are enabled but shouldn't be (cloud-init, landscape-client in WSL are usually noise).

### 4. Port Usage

```bash
ss -tlnp | grep LISTEN | sort -t: -k2 -n
```

Check for:
- Port conflicts (two services on same port)
- Unexpected listeners
- Key ports: 2222 (hermes-gateway), Docker ports

### 5. GPU Status

```bash
/usr/lib/wsl/lib/nvidia-smi --query-gpu=name,memory.total,memory.used,temperature.gpu,utilization.gpu --format=csv,noheader
```

For deep GPU diagnostics, refer to `wsl2-gpu-support` skill.

### 6. Docker Health

```bash
docker info --format '{{.ServerVersion}} | containers={{.Containers}} running={{.ContainersRunning}} images={{.Images}}'
docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}\t{{.Ports}}"
docker ps -a --filter "status=exited" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker system df
```

Report: stopped containers, unused images, disk usage.

### 7. Resource Usage

```bash
free -h
df -h /
swapon --show
```

Report: memory pressure, disk usage, swap activity.

### 7b. Inotify Watches (critical for VS Code / IDE extensions)

> Quick script: `scripts/inotify-breakdown.sh` — run `bash scripts/inotify-breakdown.sh` for instant per-process breakdown.

```bash
# Limit
cat /proc/sys/fs/inotify/max_user_watches

# Per-process breakdown — find WHO is consuming watches
# (the simple grep -c inotify approach is unreliable; use fdinfo parsing)
for pid in $(ls /proc/ 2>/dev/null | grep -E '^[0-9]+$'); do
  fds=$(ls -la /proc/$pid/fd 2>/dev/null | grep inotify | awk '{print $9}')
  if [ -n "$fds" ]; then
    for fd in $fds; do
      count=$(grep -c '^inotify wd:' /proc/$pid/fdinfo/$fd 2>/dev/null || echo 0)
      if [ "$count" -gt 0 ]; then
        cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' | cut -c1-80)
        echo "pid=$pid fd=$fd watches=$count cmd=$cmd"
      fi
    done
  fi
done 2>/dev/null | sort -t= -k3 -rn
```

If any single process uses >80% of limit, report as ⚠️ **critical**. VS Code Server (node process) is the #1 offender — it can easily consume 400K+ watches on large workspaces.

Fix (pick one or both):

1. **VS Code watcherExclude** (best — reduce watches at source):
   Edit `/home/<user>/.vscode-server/data/Machine/settings.json`:
   ```json
   {
     "files.watcherExclude": {
       "/home/<user>/project/**": true
     }
   }
   ```
   Requires `Ctrl+Shift+P → Reload Window`. Effect is dramatic (438K → 1 in testing).

2. **Raise system limit** (brute force):
   ```bash
   sudo sysctl fs.inotify.max_user_watches=2097152
   echo 'fs.inotify.max_user_watches=2097152' | sudo tee -a /etc/sysctl.conf
   ```

### 8. Network & Proxy

```bash
env | grep -i proxy
cat /etc/resolv.conf | grep -v "^#"
cat /etc/nsswitch.conf | grep hosts
```

Check: proxy points to running service, DNS resolves, nsswitch has `files dns`.

### 9. Startup Scripts

```bash
cat /usr/local/sbin/wsl-startup.sh  # or wherever wsl.conf boot command points
```

Check for redundancy with systemd-managed services (e.g., manual `dockerd` when `docker.service` is enabled).

### 10. Cron Jobs

```bash
crontab -l
sudo crontab -l  # root
```

### 11. Hermes Agent Status

```bash
hermes --version
hermes status
```

### 12. Locale & Shell

```bash
locale
grep -n "proxy\|PROXY\|alias\|export\|PATH" ~/.bashrc | head -20
```

### 13. WSLg / GUI Applications

```bash
# WSLg infrastructure
ls -la /mnt/wslg/
ls -la /mnt/wslg/.X11-unix/
ls -la $XDG_RUNTIME_DIR/wayland* 2>/dev/null || echo "no wayland socket"

# GPU/DRI devices
ls -la /dev/dri/ 2>/dev/null || echo "no /dev/dri"
ls -la /dev/dxg 2>/dev/null || echo "no /dev/dxg"

# Mesa drivers
ls /usr/lib/x86_64-linux-gnu/dri/ | grep -E "d3d12|swrast|llvmpipe"

# Display environment
echo "DISPLAY=$DISPLAY"
echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY"
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"

# Weston compositor log (check for errors)
tail -30 /mnt/wslg/weston.log 2>/dev/null || echo "no weston log"

# Test basic X11 connectivity
timeout 3 xeyes 2>/dev/null && echo "X11 OK" || echo "X11 test app failed"
```

Check for:
- `/dev/dri` missing but `/dev/dxg` present → WSLg uses D3D12, not Vulkan
- `MESA: error: ZINK: failed to choose pdev` in app output → Mesa defaulting to ZINK instead of d3d12
- `rdp_allocate_shared_memory: Failed to open "/mnt/shared_memory/{...}"` in weston.log → **shared memory corruption** (see below)
- No `Xwayland` or `Weston` processes → WSLg compositor not running

### 14. Windows Mount

```bash
ls /mnt/c/Users/ >/dev/null 2>&1 && echo "C: OK" || echo "C: FAIL"
```

## Report Format

Use this structure (user prefers Chinese):

```
═══════════════════════════════════════
         WSL 配置检查报告
═══════════════════════════════════════

【系统】OS | CPU | Memory | GPU

═══════════════════════════════════════
 正常项 ✅
═══════════════════════════════════════
  ✅ [item]

═══════════════════════════════════════
 问题 ⚠️
═══════════════════════════════════════
  ⚠️ [严重度] 描述
     详情 → 建议

═══════════════════════════════════════
 优化建议 💡
═══════════════════════════════════════
  💡 描述 → 建议

═══════════════════════════════════════
 总结
═══════════════════════════════════════
  严重问题: N | 低优先级: N | 优化: N
```

## Common Findings & Fixes

### Startup Script Redundancy
`wsl-startup.sh` manually starts `dockerd` but `docker.service` is systemd-managed. The `pgrep` check prevents double-start, but the script is dead code. Remove or repurpose.

### Stopped Docker Containers
`docker container prune` cleans exited containers. Safe — doesn't affect images or running containers.

### Unused Large Images
Check if base images (e.g., `kubricdockerhub/kubruntu` 6GB) are still needed after building custom images from them. `docker rmi` frees disk.

### Hermes Agent Behind
`hermes update` pulls latest. Check for breaking changes first.

### 36+ Enabled Systemd Services in WSL
Many are Ubuntu defaults (cloud-init, landscape, apport). Usually harmless but add boot time. Disable unneeded ones with `systemctl disable <service>`.

### Inotify Watch Exhaustion (ENOSPC)
**Symptom:** VS Code extensions (Claude Code, Copilot, etc.) fail with "Subprocess initialization did not complete within 60000ms". Extension logs show `ENOSPC: no space left on device, watch '/path/to/file'`.

**Root cause:** `fs.inotify.max_user_watches` exhausted (default 524288). The #1 consumer is VS Code Server's file watcher — a single node process can hold 400K+ watches on large workspaces. Other consumers: Docker, OpenAI ChatGPT extension, xdg-desktop-portal.

**Diagnostic path:** Extension timeout → check extension log at `~/.vscode-server/data/logs/<session>/exthost*/Anthropic.claude-code/Claude VSCode.log` → look for `ENOSPC` → run per-process inotify breakdown (see section 7b) → identify culprit.

**Fix (VS Code watcherExclude — preferred):**
```json
// ~/.vscode-server/data/Machine/settings.json
{
  "files.watcherExclude": {
    "/home/<user>/project/**": true
  }
}
```
Then `Ctrl+Shift+P → Reload Window`. In testing, VS Code Server went from 438,926 watches → 1.

**Verify the fix:** Reload Window, then run `bash scripts/inotify-breakdown.sh` — the VS Code node process should drop to single-digit watches. If still high, the exclude path may not match (check with `ps aux | grep node` to see the exact working directory).

**Fix (raise limit — fallback):**
```bash
sudo sysctl fs.inotify.max_user_watches=2097152
echo 'fs.inotify.max_user_watches=2097152' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```
Then restart the VS Code extension (Ctrl+Shift+P → "Claude: Restart" or equivalent).

**Pitfall:** The VS Code settings.json at `~/.vscode-server/data/Machine/settings.json` may not exist — create it if needed. Project-level `.vscode/settings.json` also works but only for that project.

**Pitfall — `files.exclude` vs `watcherExclude`:** These are separate VS Code settings with different effects. `watcherExclude` stops file monitoring (saves inotify watches). `files.exclude` hides files/directories from the Explorer panel (visual only, doesn't affect inotify). A directory can be excluded from watching but still visible in Explorer, or hidden from Explorer but still watched. When debugging "I can't see my directory in VS Code", check BOTH settings — especially project-level `.vscode/settings.json` which may have `files.exclude` set from an earlier configuration. Common symptom: user adds `watcherExclude` to fix inotify, then can't find their `database/` folder — it was already hidden by a pre-existing `files.exclude` entry.

### WSLg Shared Memory Corruption (GUI apps invisible)

**Symptom:** GUI app launches (process runs, logs say "主窗口已显示") but no window appears on Windows desktop. `xdotool search --name ""` finds zero windows.

**Diagnostic path:**
1. Check `/mnt/wslg/weston.log` for repeated `rdp_allocate_shared_memory: Failed to open "/mnt/shared_memory/{...}" with error: Input/output error`
2. Check Mesa errors: `MESA: error: ZINK: failed to choose pdev` → means Mesa can't find a GPU renderer
3. Check `/dev/dri` (should NOT exist in WSLg — it uses D3D12 via `/dev/dxg`)
4. Confirm `/dev/dxg` exists (D3D12 device for WSLg)

**Root cause:** WSLg's shared memory channel between the Linux guest and Windows host (via RDP/FreeRDP) gets corrupted. The Weston compositor receives window creation requests but can't allocate shared memory for the framebuffer, so content never reaches the Windows display.

**This is NOT an app-specific or rendering issue** — it affects ALL GUI apps equally.

**Fix:**
```powershell
# From Windows PowerShell (not WSL)
wsl --shutdown
```
Then reopen WSL. All WSLg infrastructure (Weston, Xwayland, shared memory) restarts fresh.

**Pitfall:** Trying rendering workarounds (`LIBGL_ALWAYS_SOFTWARE=1`, `MESA_LOADER_DRIVER_OVERRIDE=d3d12`, `GALLIUM_DRIVER=llvmpipe`, `WEBKIT_DISABLE_COMPOSITING_MODE=1`) will NOT help — the issue is in the WSLg compositor's shared memory, not in the app's GL context. Always check weston.log first.

### Proxy Dependency
All proxies point to Windows-side proxy (e.g., Clash on 127.0.0.1:7897). In mirrored mode this works, but if Windows proxy isn't running, all network requests fail silently with timeout.

### Mesa ZINK vs D3D12 Rendering Failure

**Symptom:** App logs show `MESA: error: ZINK: failed to choose pdev` and `libEGL warning: egl: failed to create dri2 screen`. App may start but render a blank/invisible window.

**Root cause:** Mesa defaults to ZINK (OpenGL over Vulkan) which requires `/dev/dri` and a Vulkan device. WSLg provides D3D12 via `/dev/dxg` instead. Mesa doesn't auto-detect this.

**Diagnostic:**
```bash
ls /usr/lib/x86_64-linux-gnu/dri/ | grep d3d12  # should show d3d12_dri.so
ls /dev/dxg  # should exist
ls /dev/dri  # should NOT exist (normal for WSLg)
```

**Fix (per-app):**
```bash
export MESA_LOADER_DRIVER_OVERRIDE=d3d12
export GALLIUM_DRIVER=d3d12
# Then run the app
```

**Fix (system-wide):** Add to `~/.bashrc` or `~/.profile`:
```bash
export MESA_LOADER_DRIVER_OVERRIDE=d3d12
```

**Pitfall:** If `d3d12_dri.so` is missing, install `mesa-utils` or update mesa packages. The `swrast_dri.so` / `kms_swrast_dri.so` drivers exist as fallback but are extremely slow.

### DISPLAY/WAYLAND Hardcoded in .bashrc
WSLg auto-sets these. Manual export may interfere. Check if WSLg is active before hardcoding.

## Pitfalls

1. **Don't change .wslconfig without `wsl --shutdown`** — Changes only take effect after full WSL restart
2. **Don't install Linux NVIDIA drivers** — See wsl2-gpu-support skill
3. **Don't disable cloud-init if using WSLg** — Some WSL features depend on it
4. **`nvidia-smi` vs `/usr/lib/wsl/lib/nvidia-smi`** — Always use the full path in WSL2
5. **Memory in .wslconfig vs actual** — WSL reports slightly less than configured (kernel overhead)
