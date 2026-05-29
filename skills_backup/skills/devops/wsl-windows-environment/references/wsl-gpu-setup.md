---
name: wsl-gpu-setup
description: Check and configure GPU/CUDA in WSL2 for Docker workloads. Correct WSL2-specific checks that differ from bare Linux.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [wsl, gpu, cuda, docker, nvidia]
---

# WSL2 GPU/CUDA Setup

WSL2 GPU support works differently from bare Linux. Many standard Linux GPU checks are **unreliable or misleading** in WSL2.

## Key Principle

WSL2 uses Windows NVIDIA drivers mapped into Linux. **Do NOT install Linux NVIDIA display drivers** — they will break the environment. The CUDA runtime comes from `/usr/lib/wsl/lib/`.

## Correct WSL2 GPU Checks

### ✅ Reliable checks (use these)

```bash
# 1. Confirm WSL2 (not WSL1)
cat /proc/version  # should say "microsoft-standard-WSL2"

# 2. GPU virtualization entry point
ls -l /dev/dxg

# 3. CUDA runtime library
ls -l /usr/lib/wsl/lib/libcuda.so.1

# 4. nvidia-smi (WSL-specific path)
/usr/lib/wsl/lib/nvidia-smi

# 5. CUDA libraries visible to linker
ldconfig -p | grep -E 'libcuda|libnvidia-ml'
```

### ❌ Unreliable in WSL2 (do NOT use as pass/fail)

| Command | Why it fails in WSL2 |
|---------|---------------------|
| `nvidia-smi` (bare) | May not be in PATH; use `/usr/lib/wsl/lib/nvidia-smi` |
| `lspci \| grep VGA` | PCI devices not exposed like bare Linux |
| `cat /proc/driver/nvidia/version` | No Linux kernel driver installed (by design) |
| `ls /dev/dri/` | Related to WSLg graphics, not CUDA |
| `nvcc --version` | Only shows compiler, not runtime availability |

## Docker GPU Access

### Prerequisites
1. Windows NVIDIA driver ≥ 525.60
2. WSL2 kernel updated (`wsl --update` from Windows)
3. `/dev/dxg` exists in WSL
4. `/usr/lib/wsl/lib/nvidia-smi` works

### Install NVIDIA Container Toolkit

```bash
# Add NVIDIA repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Verify Docker GPU

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

## Troubleshooting

### "GPU access blocked by the operating system"
- WSL kernel needs update: run `wsl --shutdown && wsl --update` from Windows PowerShell
- Check Windows NVIDIA driver version

### Docker containers not using GPU
- Verify `--gpus all` flag on `docker run`
- Check `docker info --format '{{json .Runtimes}}'` shows nvidia runtime
- Install NVIDIA Container Toolkit if missing

## Pitfalls

1. **Never install `cuda`, `cuda-drivers`, `nvidia-driver-*` in WSL2** — Windows driver maps everything needed
2. **`nvidia-smi` in WSL2 has limited NVML support** — some queries will fail, this is normal
3. **`/dev/dxg` disappearing** usually means WSL needs restart or update
4. **PyBullet is CPU-only** — GPU won't help physics simulation, only Blender rendering
