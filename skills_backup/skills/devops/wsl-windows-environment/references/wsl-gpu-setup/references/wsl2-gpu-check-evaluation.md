# WSL2 GPU Check Evaluation (from Codex GPT-5.5)

## Original checks and their WSL2 reliability

| Command | Verdict | Notes |
|---------|---------|-------|
| `nvidia-smi` | Useful but limited | WSL version has reduced NVML; use `/usr/lib/wsl/lib/nvidia-smi` |
| `ls /dev/dri/` | Not core for CUDA | `/dev/dxg` is the WSL2 GPU virtualization entry |
| `cat /proc/driver/nvidia/version` | Unreliable | No Linux kernel driver by design |
| `lspci \| grep VGA` | Unreliable | PCI not exposed in WSL2 |
| `nvcc --version` | Compiler only | Doesn't prove GPU runtime works |
| `ls /usr/local/cuda/` | Directory only | Doesn't prove CUDA runs |
| `powershell Get-CimInstance` | Useful | Check Windows-side GPU |
| `cmd.exe /c nvidia-smi` | Useful | Check Windows NVIDIA driver |

## Recommended check order

1. `cat /proc/version` — confirm WSL2
2. `cmd.exe /c nvidia-smi` — Windows GPU + driver
3. `ls -l /dev/dxg` — WSL2 GPU virtualization
4. `/usr/lib/wsl/lib/nvidia-smi` — WSL CUDA runtime
5. `ldconfig -p | grep libcuda` — library visibility
6. Target program test (Blender, PyTorch, etc.)

## Blender GPU rendering

- Supports: CUDA, OptiX (NVIDIA), HIP (AMD), oneAPI (Intel), Metal (macOS)
- Configure: Preferences → System → Cycles Render Devices
- Per-scene: Render Properties → Device → GPU Compute
- RTX cards prefer OptiX for best performance

## Critical warnings

- Do NOT install Linux NVIDIA display drivers in WSL2
- Windows driver maps `libcuda.so` stubs into WSL automatically
- `nvidia-smi` in WSL2 is a limited-functionality version
- `wsl --update` from Windows PowerShell fixes most GPU access issues
