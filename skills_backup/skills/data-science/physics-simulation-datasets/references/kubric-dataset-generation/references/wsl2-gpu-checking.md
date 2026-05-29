# WSL2 GPU Checking — Correct Methodology

## Problem

Standard Linux GPU checks (`lspci`, `/proc/driver/nvidia/version`, `/dev/dri/`) are **unreliable or non-functional in WSL2**. WSL2 uses a virtualized GPU model where Windows drivers map into WSL.

## Correct Check Order

### 1. Confirm WSL2 (not WSL1)
```bash
uname -r  # Should show "microsoft-standard-WSL2"
cat /proc/version
```

### 2. Check Windows GPU (from WSL)
```bash
cmd.exe /c nvidia-smi
powershell.exe -NoProfile -Command "Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion"
```

### 3. Check WSL2 GPU Virtualization Entry Point
```bash
ls -l /dev/dxg  # CRITICAL — WSL2 GPU device, NOT /dev/dri/
```

### 4. Check CUDA Runtime Libraries
```bash
ls -l /usr/lib/wsl/lib/libcuda.so.1
ls -l /usr/lib/wsl/lib/nvidia-smi
ldconfig -p | grep -E 'libcuda|libnvidia-ml'
```

### 5. Run nvidia-smi (WSL version)
```bash
/usr/lib/wsl/lib/nvidia-smi  # Use full path, not bare nvidia-smi
```

### 6. Verify with actual program
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# Or Docker:
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

## What NOT to Use as Primary Checks

| Command | Why it fails in WSL2 |
|---------|---------------------|
| `lspci` | PCI devices not exposed in WSL2 virtualization |
| `/proc/driver/nvidia/version` | No Linux NVIDIA kernel driver installed (by design) |
| `/dev/dri/` | Related to WSLg graphics/Mesa, not CUDA |
| `nvcc --version` | Only shows compiler, not GPU availability |

## Key Rules

1. **NEVER install Linux NVIDIA display drivers in WSL2** — Windows driver maps `libcuda.so` into WSL via `/usr/lib/wsl/lib/`. Installing Linux drivers breaks this.

2. **`/dev/dxg` is the key device** — This is WSL2's GPU virtualization entry point, not `/dev/dri/`.

3. **`nvidia-smi` has limited functionality in WSL2** — Some NVML queries are unsupported. Use `/usr/lib/wsl/lib/nvidia-smi` for full path.

4. **Docker GPU requires `--gpus all`** — And NVIDIA Container Toolkit must be installed.

## Enabling GPU in WSL2 (if not working)

### Step 1: Update WSL (Windows PowerShell, admin)
```powershell
wsl --shutdown
wsl --update
```

### Step 2: Verify GPU access in WSL
```bash
/usr/lib/wsl/lib/nvidia-smi
```

### Step 3: Install NVIDIA Container Toolkit (if Docker needed)
```bash
sudo apt-get update
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Step 4: Verify Docker GPU
```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

## References

- NVIDIA CUDA on WSL User Guide: https://docs.nvidia.com/cuda/wsl-user-guide/
- Microsoft WSL CUDA: https://learn.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl
- NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
