# ML Conda/GPU Environment Selection

Session-derived checklist for ML/model implementation verification when tests depend on PyTorch or CUDA.

## Durable lessons

- Do not assume an existing similarly named conda environment is the right one. If the user or project specifies an environment name, create/use that exact environment for subsequent verification commands.
- Before installing PyTorch, check GPU visibility in WSL/Linux:
  - `nvidia-smi` if available
  - WSL fallback: `/usr/lib/wsl/lib/nvidia-smi`
- If a GPU is present, install a CUDA-enabled PyTorch build rather than CPU-only packages.
- After installing, verify the runtime inside the target environment, not in base:
  - `conda run -n <env> python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"`
- Only after runtime verification should test commands be considered authoritative.

## User correction signal

If the user asks why a different env is being used or says to use/create a specific env (for example “自己新建一个名为model的conda环境跑”), stop current installs/tests if needed and switch immediately. Avoid explaining at length; execute the environment correction, verify GPU/runtime, then continue the urgent implementation work.

## Known-good pattern used here

```bash
conda create -y -n model python=3.10 pytest numpy
# For WSL GPU discovery when nvidia-smi is not on PATH:
/usr/lib/wsl/lib/nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
# Install CUDA PyTorch wheel inside the target env when conda resolution gives CPU builds:
conda run -n model python -m pip install --upgrade --force-reinstall \
  torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# Verify:
conda run -n model python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
```

Use this as a verification/setup pattern, not as a permanent claim about a machine: CUDA version, driver, and environment name may differ by project/user.

## Common AMP/FP16 Training Failures

When running training with AMP (automatic mixed precision, the default for modern GPU training), watch for these issues:

1. **`masked_fill` with `-1e9` overflows FP16.** Error: `RuntimeError: value cannot be converted to type at::Half without overflow`. Fix: use `-1e4` instead. Scan codebase with `search_files` for `-1e9` or `-1e10`.

2. **`GradScaler` / `autocast` deprecation warnings.** PyTorch 2.x deprecates `torch.cuda.amp.GradScaler()` → `torch.amp.GradScaler('cuda')` and `torch.cuda.amp.autocast()` → `torch.amp.autocast('cuda')`. These are FutureWarnings, not errors — training still works. Don't fix these unless the task explicitly asks for warning cleanup.

3. **Batch size auto-tuning.** Many training scripts auto-tune batch size to fit VRAM. If training OOMs, check if the script has a `find_working_config` or similar function. The tuned batch size may differ from the default.

4. **First-run error vs. subsequent success.** If training fails on first run but the error is environment-related (FP16 overflow, missing dependency), fix the source code and re-run. Don't assume the fix didn't work — re-run and check the full output including epoch metrics.
