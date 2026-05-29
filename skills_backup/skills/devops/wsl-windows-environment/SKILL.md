---
name: wsl-windows-environment
description: Use when auditing, configuring, troubleshooting, or developing in WSL2/Windows interop environments, including GPU/CUDA, Docker, Python/conda, Windows GUI apps, WSLg, ports, proxy, memory, and systemd.
tags: [wsl, windows, gpu, cuda, docker, python, conda, systemd, wslg, interop]
---

# WSL Windows Environment

Umbrella skill for WSL2 + Windows host operations: environment audits, GPU/CUDA/Docker setup, Python development, Windows GUI app management from WSL, WSLg rendering, ports, proxy, systemd, memory, and filesystem interop.

## When to Use

- User asks to check or fix WSL config, systemd, Docker, GPU, ports, proxy, memory, or WSLg.
- Running/installing Windows `.exe` GUI apps from WSL or translating Windows paths.
- Setting up Python/conda projects inside WSL.
- Diagnosing CUDA/PyTorch/Blender/Docker GPU visibility.
- Troubleshooting GUI invisibility, Mesa/ZINK/D3D12, or shared-memory WSLg issues.

## Core Audit Order

1. System identity: `/etc/os-release`, kernel, CPU, memory.
2. WSL config: `/etc/wsl.conf`, Windows `%USERPROFILE%\.wslconfig`, systemd, memory/swap, mirrored networking.
3. Services and ports: `systemctl`, Docker status, `ss -tlnp`.
4. GPU: `/dev/dxg`, `/usr/lib/wsl/lib/nvidia-smi`, CUDA libs, PyTorch/Blender/Docker checks.
5. Resources: `free -h`, `df -h`, swap, OOM logs.
6. Network/proxy/DNS: env proxy, `/etc/resolv.conf`, Windows proxy reachability.
7. WSLg/GUI: `/mnt/wslg`, `/dev/dxg`, Mesa drivers, weston log, display variables.
8. Project/runtime specifics: conda env, pip, port binding, Windows process state.

## High-Value Rules

- **WSL crontab is unreliable for scheduled tasks** — WSL instances are not persistent; they start on-demand and stop when idle. Cron jobs scheduled via `crontab -e` will NOT run if WSL is sleeping/shutdown at the scheduled time. For reliable scheduling, prefer Hermes cron jobs (`hermes cron create`) which persist across WSL restarts, or use Windows Task Scheduler to invoke WSL commands.
- Never install Linux NVIDIA display drivers inside WSL2; Windows host driver supplies CUDA through WSL.
- Use `/usr/lib/wsl/lib/nvidia-smi`, not bare `nvidia-smi`, when PATH is uncertain.
- For Docker GPU, install/configure NVIDIA Container Toolkit and test with `docker run --rm --gpus all ... nvidia-smi`.
- In WSL, translate paths: `C:\Users\...` → `/mnt/c/Users/...`, `D:\` → `/mnt/d/`.
- Launch Windows GUI apps via PowerShell with an explicit Windows working directory; avoid inheriting WSL UNC paths.
- Use conda for Python project isolation; source `conda.sh` before `conda activate`.
- For pip commands in CJK-path projects, run from `/tmp` or another ASCII path to avoid terminal watchdog/path issues.
- For quick server restarts, check ports and TIME_WAIT; bind to `127.0.0.1` or choose a new port when needed.
- WSLg shared-memory corruption is fixed by Windows `wsl --shutdown`, not by app-level GL flags.

## Common Commands

```bash
# WSL/GPU basics
uname -r
cat /etc/wsl.conf
/usr/lib/wsl/lib/nvidia-smi
ls -l /dev/dxg /usr/lib/wsl/lib/libcuda.so.1

# Docker
systemctl is-active docker.service
docker ps
docker system df

# Resources
free -h
df -h /
dmesg -T | grep -i 'oom\|kill' | tail -20

# Ports
ss -tlnp | grep LISTEN

# Windows GUI process
powershell.exe -Command "Set-Location 'D:\\App'; Start-Process '.\\App.exe' -WorkingDirectory 'D:\\App'"
tasklist.exe | grep -i app
```

## Support Files

Absorbed narrow skills are preserved in `references/` by original name. Load them for detailed checklists, command recipes, and case-specific troubleshooting.
