# Physics video eval/inference implementation review notes

Session-derived checklist for `slot-datamaking`-style physics video prediction projects. Use under the broader implementation verification workflow when implementing evaluation or inference utilities for tensor video models.

## Evaluation metrics: blockers to check

- Do not aggregate scene metrics by copying a batch-level metric to every sample in the batch. If batches can mix scenes, compute video/state metrics per sample first, then group by `scene_id`.
- For collision metrics, aggregate TP/FP/FN counts and compute precision/recall/F1 from counts. Do not average per-batch F1 unless that is explicitly requested.
- Match training-loss collision masks during evaluation. If training filters static-static pairs, evaluation must apply the same dynamic-pair mask:
  ```python
  dynamic = valid_mask & (~static_flag)
  pair_mask = pair_mask & (dynamic[:, None, :, None] | dynamic[:, None, None, :])
  ```
- Collision labels must use original or denormalized force, not normalized model features:
  ```python
  force_raw = force_tgt * force_std + force_mean
  label = torch.linalg.norm(force_raw, dim=-1) > threshold
  ```
- Prefer reading `force_mean/std` from `dataloader.dataset` when available; otherwise require explicit parameters or documented defaults.
- Avoid batch-average bias: final short batches should not count the same as full batches unless intentionally macro-averaging.
- For PSNR, compute from aggregated/global MSE or handle `inf` carefully; one perfect batch should not make the whole run `inf`.
- Empty masks and static-only batches should return finite zero metrics, not NaNs.

## Device and environment checks

- Use the user-requested conda environment for verification. If the user names an env such as `model`, do not keep using an older project env.
- In WSL, `nvidia-smi` may live at `/usr/lib/wsl/lib/nvidia-smi` even if it is not on PATH. Use it to confirm GPU visibility before deciding CPU-only installs.
- For CUDA PyTorch in a conda env, verify inside that exact env:
  ```bash
  conda run -n <env> python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
  ```
- If conda channel resolution installs CPU PyTorch despite `pytorch-cuda`, a pip reinstall from the CUDA wheel index can fix the env:
  ```bash
  conda run -n <env> python -m pip install --upgrade --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```
  Treat this as a setup fix, not as a durable claim that conda is broken.

## Inference utilities: blockers to check

- Resolve `history_length` and `predict_length` from `model.config` by default. If callers pass explicit lengths that disagree with model config, raise a clear error rather than slicing targets silently.
- `run_inference` metrics should expose the same value-range, force-normalization, collision-threshold, and logit-threshold parameters as evaluation utilities, so T11/T12 metrics do not drift.
- If `device` is passed explicitly, move both model and batch tensors to that device. If no device is passed, infer from model parameters; handle parameterless mock models.
- Checkpoint loading should support common formats (`model_state_dict`, `state_dict`, raw state dict), strip `module.` prefixes, and raise `ValueError` for ambiguous full-training checkpoints with no model-state key.
- If `torch.load(weights_only=False)` is needed to load a config dataclass, state clearly that checkpoints must be trusted.

## Visualization checks

- “Physical state curves” should cover more than position when state includes velocity/force. At minimum for this project, plot `x,y,z`, `vx,vy,vz`, and `fx,fy,fz` (`state[0:3]`, `state[7:10]`, `state[13:16]`).
- Collision confusion visualizations should accept the same `force_mean/std`, force threshold, and logit threshold as collision metrics.
- If no valid object exists for a state-curve visualization, raise a clear error or render an explicit “no valid object” image; do not silently plot padding object 0.

## Tests worth adding

- Mixed-scene batch where scene 0 has MSE 0 and scene 1 has MSE 1; assert grouped scene metrics differ.
- Static-static collision false positive should be filtered out in evaluation/inference metrics.
- Empty pair mask and static-only objects should produce finite zero collision/state metrics.
- Checkpoint with `module.`-prefixed keys loads successfully.
- Mismatched `history_length`/`predict_length` between run-inference arguments and model config raises `ValueError`.
- Visualization functions create non-empty image files for frame comparison, state curves, and collision confusion.