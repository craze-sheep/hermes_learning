---
name: wsl2-gpu-support
description: "Check and enable GPU support in WSL2 for CUDA, Blender, PyTorch, and other GPU workloads."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux]
metadata:
  hermes:
    tags: [wsl, gpu, cuda, blender, nvidia, rendering]
    related_skills: []
---

# WSL2 GPU Support

Enable and verify GPU access in Windows Subsystem for Linux 2.

## Prerequisites

- Windows 11 or recent Windows 10
- NVIDIA GPU with driver ≥ 525.60 (Windows side)
- WSL2 kernel updated: `wsl.exe --update`

## Critical Rule

**NEVER install Linux NVIDIA display drivers in WSL2.** Windows host driver maps `libcuda.so` into WSL automatically. Installing Linux drivers breaks the environment.

## Verification Checklist (Correct Order)

### 1. Confirm WSL2 (not WSL1)

```bash
wsl.exe -l -v
wsl.exe --status
uname -r  # Should show "microsoft" in version string
```

### 2. Check Windows-side GPU

```bash
powershell.exe -NoProfile -Command "Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion"
cmd.exe /c nvidia-smi
```

### 3. Check WSL2 GPU Virtualization Entry Point

```bash
ls -l /dev/dxg  # CRITICAL: WSL2 GPU virtualization device
ls -l /usr/lib/wsl/lib/libcuda.so.1  # CUDA runtime library
```

### 4. Check CUDA Runtime Visibility

```bash
/usr/lib/wsl/lib/nvidia-smi  # WSL-specific nvidia-smi path
ldconfig -p | grep -E 'libcuda|libnvidia-ml'
```

### 5. Check CUDA Toolkit (optional, for compilation)

```bash
nvcc --version
which nvcc
```

### 6. Program-level Verification

```bash
python3 -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

## Common Pitfalls

1. **`nvidia-smi` not in PATH** — Use `/usr/lib/wsl/lib/nvidia-smi` instead
2. **`nvidia-smi` shows "GPU access blocked by the operating system"** — Even when `/dev/dxg` and `libcuda.so.1` exist. This means WSL kernel needs updating: `wsl --shutdown && wsl --update` from Windows PowerShell.
3. **`/dev/dri/` doesn't exist** — Normal in WSL2. Check `/dev/dxg` instead
4. **`/proc/driver/nvidia/version` missing** — Normal in WSL2. Don't rely on it
5. **`lspci` shows no GPU** — Normal in WSL2. PCI devices don't expose directly
6. **Installing Linux NVIDIA driver** — NEVER do this. Breaks WSL2 GPU support
7. **Codex/Claude Code can't fix GPU issues** — Both run in sandboxes without system-level access. Only the user can run `wsl --update` and install packages via `sudo`.

## Docker GPU Access

### Step 1: Install NVIDIA Container Toolkit

```bash
# Add NVIDIA GPG key and repo
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# If apt-get fails to fetch from nvidia.github.io (timeout/handshake), use proxy:
sudo apt-get install -y \
  -o Acquire::http::Proxy="http://127.0.0.1:7897" \
  -o Acquire::https::Proxy="http://127.0.0.1:7897" \
  nvidia-container-toolkit

# Without proxy:
# sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
```

### Step 2: Configure Docker

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Step 3: Verify

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### Step 4: Use in containers

```bash
docker run --rm --gpus all <image>
# or for specific GPU:
docker run --rm --gpus '"device=0"' <image>
```

### Pitfalls

- **nvidia.github.io download times out** — WSL often needs proxy for GitHub-hosted repos. Pass `-o Acquire::http::Proxy=...` to apt or set `HTTPS_PROXY` env var before `apt-get install`.
- **Do NOT install `cuda`, `nvidia-driver-*`** — WSL only uses the Windows-side driver mapped through `/usr/lib/wsl/lib/`.
- **Docker build context too large** — Large project directories cause slow/hanging builds. Use `.dockerignore` with `**` (exclude all) then `!entrypoint.sh` (include only what's needed). Check with `du -sh` before building.
- **Long Docker builds hang with no output** — Legacy Docker builder buffers output. Use `docker build --progress=plain` or run in background with `terminal(background=true, notify_on_complete=true)`.

## Blender GPU Rendering

Blender Cycles supports CUDA/OptiX for GPU rendering. In WSL2:

1. Verify GPU visible: `/usr/lib/wsl/lib/nvidia-smi`
2. In Blender: Preferences → System → Cycles Render Devices → CUDA
3. In scene: Render Properties → Device → GPU Compute

### Critical: Blender Version vs GPU Architecture

Blender versions have hard limits on which GPU architectures they support:

| Blender | CUDA max arch | OptiX max arch | Example GPUs |
|---------|--------------|----------------|--------------|
| 2.93    | sm_86        | sm_86          | RTX 3090 ✓, RTX 4060 ✗ |
| 3.3     | sm_89        | sm_89          | RTX 4060 ✓ |
| 3.6     | sm_89        | sm_89          | RTX 4060 ✓ |
| 4.x     | sm_90        | sm_90          | RTX 5090 ✓ |

**RTX 4060 (Ada Lovelace, sm_89) requires Blender ≥ 3.3.**

Detection code:
```python
import bpy
cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
cycles_prefs.compute_device_type = 'CUDA'
cycles_prefs.get_devices()
for d in cycles_prefs.devices:
    print(f'{d.name} | type={d.type} | use={d.use}')
```

If only CPU appears (no GPU), the Blender build doesn't support your GPU architecture.

### Kubric kubruntu Image

`kubricdockerhub/kubruntu` ships Blender 2.93 (via `bpy` pip package). This means:
- **RTX 30 series and older**: GPU rendering works (if CUDA runtime is present)
- **RTX 40 series (Ada Lovelace)**: GPU NOT detected — need Blender ≥ 3.3
- The container lacks `libcudart.so` — only has WSL-mapped `libcuda.so`. Blender's CUDA backend needs the runtime library to enumerate devices.

Workaround for RTX 40: mount CUDA runtime from `nvidia/cuda` image:
```bash
# Extract libcudart from a CUDA image
docker run --rm -v /tmp/cuda-libs:/out nvidia/cuda:12.4.1-base-ubuntu22.04 \
  bash -c "cp /usr/local/cuda-12.4/targets/x86_64-linux/lib/libcudart.so.12 /out/"

# Mount into kubruntu
docker run --rm --gpus all \
  -v /tmp/cuda-libs:/cuda-libs \
  -e LD_LIBRARY_PATH=/cuda-libs \
  kubricdockerhub/kubruntu:latest python3 -c "..."
```

**But this alone won't fix Blender 2.93 — the version doesn't know sm_89 exists.** You need to upgrade the Blender binary inside the container or build a custom image with Blender 3.6+.

## WSL2 Memory & OOM Configuration

### .wslconfig

WSL2 memory is capped by Windows host allocation. Edit `C:\Users\<username>\.wslconfig`:

```ini
[wsl2]
memory=12GB
swap=8GB
```

Then `wsl --shutdown` and reopen.

**Rule of thumb**: Leave 3-4GB for Windows. On 16GB host, `memory=12GB` is safe.

### Diagnosing OOM Kills

When Docker containers die silently (especially with `--rm`), check:

```bash
dmesg -T | grep -i "oom\|kill" | tail -20
```

Look for `Out of memory: Killed process ... (python3)` with `task_memcg=...docker...scope`.

Memory pressure indicators:
```bash
free -h          # swap usage > 80% = danger
swapon --show    # confirm swap device and size
```

Common OOM scenario: Blender rendering + VSCode Server + multiple AI agents on 7.4GB WSL2.

### GPU Memory Check Inside Container

```bash
docker run --rm --gpus all <image> nvidia-smi
# Look at Memory-Usage line, not GPU-Util
```

## References

- NVIDIA CUDA on WSL User Guide: https://docs.nvidia.com/cuda/wsl-user-guide/
- Microsoft WSL CUDA: https://learn.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl
- Blender GPU Rendering: https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html
- Blender CUDA Compute Capabilities: https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html#supported-gpus
