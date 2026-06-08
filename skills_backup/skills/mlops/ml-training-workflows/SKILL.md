---
name: ml-training-workflows
description: End-to-end ML model development workflows — data exploration, PyTorch model design, training loop implementation, OOM handling, loss calibration, and checkpoint management. Use when building/training deep learning models from scratch or iterating on model architecture.
triggers:
  - building a new PyTorch model from scratch
  - training loop implementation
  - OOM handling and batch size tuning
  - loss function calibration
  - data pipeline design for custom datasets
  - model checkpoint saving/loading
  - analyzing training curves or TensorBoard logs
  - diagnosing overfitting, loss spikes, or convergence issues
---

# ML Training Workflows

## 1. Data Exploration First

Before writing any model code, always inspect the actual data:

```python
# Sample inspection script
import json, numpy as np, glob, os

# Check 2-3 samples from different scenes/splits
for sample_path in random_samples:
    with open(os.path.join(sample_path, 'metadata.json')) as f:
        meta = json.load(f)
    # Print: shapes, dtypes, value ranges, missing fields
    # Load one tensor, check shape/dtype/range
    # Verify file count matches expected
```

**Checklist before model design:**
- [ ] Shapes and dtypes of every input field
- [ ] Value ranges (min/max/mean) — informs normalization
- [ ] Missing/null fields and how they're encoded
- [ ] Sample counts per split
- [ ] One full forward pass of the data pipeline (load → collate → batch)

## 2. PyTorch Model Architecture Patterns

### Dual-stream encoder (visual + structured)

```python
class DualStreamEncoder(nn.Module):
    def __init__(self, ...):
        self.visual_branch = CNN(...)      # processes images
        self.structured_branch = MLP(...)  # processes tabular/physics features
        self.fusion = nn.Linear(vis_dim + struct_dim, fused_dim)

    def forward(self, images, structured):
        vis_feat = self.visual_branch(images)
        struct_feat = self.structured_branch(structured)
        return self.fusion(torch.cat([vis_feat, struct_feat], dim=-1))
```

### GNN with explicit edge features

```python
# For small N (≤10), dense is fine — no need for PyG sparse
class DenseGNNLayer(nn.Module):
    def __init__(self, node_dim, edge_dim, hidden_dim):
        self.message_fn = nn.Sequential(
            nn.Linear(node_dim * 2 + edge_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, node_dim),
        )
        self.update_fn = nn.GRUCell(node_dim, node_dim)

    def forward(self, nodes, edge_feat, valid_mask):
        # nodes: [B, N, D], edge_feat: [B, N, N, E]
        node_i = nodes.unsqueeze(2)  # [B, N, 1, D]
        node_j = nodes.unsqueeze(1)  # [B, 1, N, D]
        msg_input = cat(node_i, node_j, edge_feat)  # [B, N, N, 2D+E]
        messages = self.message_fn(msg_input)         # [B, N, N, D]
        messages = messages * valid_mask.unsqueeze(-1)  # mask invalid
        aggregated = messages.sum(dim=2) / valid_count  # [B, N, D]
        return self.update_fn(aggregated, nodes)  # GRU update
```

### GRU temporal prediction (vs Transformer)

```python
# Encode history → decode future autoregressively
class TemporalGRU(nn.Module):
    def __init__(self, dim, num_layers=2):
        self.gru = nn.GRU(dim, dim, num_layers, batch_first=True)

    def encode(self, history):  # [B, T_h, N, D]
        B, T, N, D = history.shape
        _, h_last = self.gru(history.reshape(B*N, T, D))
        return h_last  # [layers, B*N, D]

    def decode(self, first_token, h_init, T_p):
        outputs = []
        x = first_token  # [B*N, 1, D]
        h = h_init
        for _ in range(T_p):
            out, h = self.gru(x, h)
            outputs.append(out)
            x = out  # autoregressive
        return torch.cat(outputs, dim=1)  # [B*N, T_p, D]
```

## 3. OOM Auto-Retry Pattern

**Critical for 8GB GPUs.** Always implement this in training scripts:

```python
def find_working_batch_size(config, make_model, make_data, device):
    """Halve batch_size on OOM. If bs=1 still OOM, shrink model."""
    bs = config.batch_size
    model_shrunk = False

    while bs >= 1:
        try:
            model = make_model(config).to(device)
            batch = make_data(bs)
            loss = model(batch).sum()
            loss.backward()
            return bs, config, model_shrunk  # success
        except RuntimeError as e:
            if 'out of memory' not in str(e).lower():
                raise
            del model; gc.collect(); torch.cuda.empty_cache()
            if bs > 1:
                bs //= 2
            elif not model_shrunk:
                config = shrink_model(config)  # halve hidden dims
                model_shrunk = True
            else:
                raise RuntimeError("Cannot fit in GPU memory")
```

**Model shrinking priority order:**
1. Reduce `history_length` / `predict_length`
2. Halve hidden dims (token_dim, gru_hidden, gnn_hidden)
3. Remove a layer (gnn_layers, gru_num_layers)
4. Halve CNN channels
5. Reduce image resolution

## 4. Loss Calibration Pitfalls

### ⚠️ Pixel-wise losses dominate at high resolution

**Problem:** BCE on 128×128 masks → per-element loss ~0.7, total ~0.7 × 128² × N_objects ≈ 40K-60K.
Other losses (state, collision) are ~1-10. Mask loss at weight=1.0 drowns everything.

**Diagnosis:** If `total_loss` is dominated by one term (>99%), the loss weights are wrong.

**Fix options (in order of preference):**
1. Set mask_weight very low (0.001-0.01) — quick fix
2. Downsample masks to 32×32 before computing loss — reduces by 16×
3. Use focal loss instead of BCE — handles class imbalance
4. Normalize loss by number of positive pixels

```python
# Downsample mask loss approach
mask_tgt_ds = F.adaptive_avg_pool2d(mask_tgt.reshape(B*Tp*N, 1, H, W), 32)
mask_pred_ds = F.adaptive_avg_pool2d(mask_pred.reshape(B*Tp*N, 1, H, W), 32)
mask_loss = F.binary_cross_entropy_with_logits(mask_pred_ds, mask_tgt_ds)
```

### Loss weight calibration checklist

After first training run, print weighted contributions:
```python
print(f"  rgb={rgb_loss*rgb_weight:.2f}  "
      f"state={state_loss*state_weight:.2f}  "
      f"coll={coll_loss*collision_weight:.2f}  "
      f"mask={mask_loss*mask_weight:.2f}")
# All should be within 1-2 orders of magnitude of each other
```

### ⚠️ Dice loss instability with very few objects

When mask predictions are near-zero (early training or padding objects), Dice loss can spike:
```python
# Safe Dice with epsilon
intersection = (pred * tgt * mask).sum()
union = ((pred + tgt) * mask).sum()
dice = 1 - (2 * intersection + 1e-6) / (union + 1e-6)
```
Always multiply by `valid_mask` to exclude padding objects from the denominator.

## 5. Python Import Collision Pattern

**Problem:** When `ai_model/config.py` and `model/config.py` both exist, `from config import X` finds the wrong one depending on `sys.path` order.

**Solution:** Use `importlib.util.spec_from_file_location` to load parent module by path:

```python
import importlib.util

def load_parent_module(module_name, parent_dir):
    """Load a module from parent directory by file path."""
    path = os.path.join(parent_dir, f'{module_name}.py')
    spec = importlib.util.spec_from_file_location(f'_parent_{module_name}', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Usage:
_parent = load_parent_module('dataset', os.path.dirname(this_dir))
PhysicsVideoDataset = _parent.PhysicsVideoDataset
```

**sys.path ordering for sub-packages:**
```python
# Insert model/ first, then ai_model/ on top (higher priority)
sys.path.insert(0, model_dir)    # lower priority
sys.path.insert(0, this_dir)     # higher priority (last insert wins)
```

## 6. GroupNorm Divisibility Helper

**Pitfall:** `nn.GroupNorm(num_groups, num_channels)` requires `num_channels % num_groups == 0`.
When model dims are halved for OOM, channels like 12 don't divide by 8.

```python
def _best_group(channels: int, preferred: int = 8) -> int:
    """Find largest divisor of channels that is <= preferred."""
    if channels <= 0:
        return 1
    for g in range(min(preferred, channels), 0, -1):
        if channels % g == 0:
            return g
    return 1

# Use everywhere:
nn.GroupNorm(_best_group(channels), channels)
```

## 7. PyTorch AMP Version Compatibility

```python
# PyTorch >= 2.0 (preferred):
from torch.amp import autocast, GradScaler
with autocast('cuda'):  # device_type as positional arg
    ...

# PyTorch < 2.0 (legacy, still works but deprecated):
from torch.cuda.amp import autocast, GradScaler
with autocast():  # no device_type arg
    ...

# Safe compatibility wrapper:
try:
    from torch.amp import autocast, GradScaler
    def make_autocast():
        return autocast('cuda')
except ImportError:
    from torch.cuda.amp import autocast, GradScaler
    def make_autocast():
        return autocast()
```

## 8. Training Script Template

```python
"""Minimal training script structure."""
import argparse, gc, json, os, time
import torch
from torch.cuda.amp import GradScaler, autocast

def train(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 1. Config
    config = load_config(args.mode)

    # 2. Auto-find batch size
    batch_size, config, shrunk = find_working_batch_size(config, device)

    # 3. Build model
    model = build_model(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.lr)
    scaler = GradScaler() if config.use_amp else None

    # 4. Data
    train_loader = make_loader(config, 'train', batch_size)
    val_loader = make_loader(config, 'val', batch_size)

    # 5. Training loop
    for epoch in range(config.epochs):
        model.train()
        for step, batch in enumerate(train_loader):
            batch = to_device(batch, device)
            optimizer.zero_grad(set_to_none=True)
            if scaler:
                with autocast():
                    loss = compute_loss(model, batch)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                loss = compute_loss(model, batch)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

        # 6. Validate
        val_loss = validate(model, val_loader, device)

        # 7. Checkpoint
        save_checkpoint(model, optimizer, epoch, val_loss, ckpt_dir)

    # 8. Summary
    print(f"Device: {device}, Batch: {batch_size}, Shrunk: {shrunk}")
    print(f"Best val: {best_val:.4f}, Checkpoints: {ckpt_dir}")
```

## 9. Checkpoint Best Practices

```python
# Save everything needed to resume
torch.save({
    'epoch': epoch,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'scheduler_state_dict': scheduler.state_dict(),
    'loss': loss_value,
    'config': config,  # dataclass or dict
}, path)

# Load with flexible key detection
ckpt = torch.load(path, map_location=device)
if 'model_state_dict' in ckpt:
    model.load_state_dict(ckpt['model_state_dict'])
elif 'state_dict' in ckpt:
    model.load_state_dict(ckpt['state_dict'])
else:
    model.load_state_dict(ckpt)  # raw state dict
```

## 10. Post-Training Curve Diagnostics

After a training run, analyze TensorBoard event files to detect overfitting, spikes, plateaus, and loss imbalance. The workflow:

1. Extract scalars with `tbparse` (not the heavy TensorBoard server)
2. Generate train-vs-val comparison plots
3. Run automated diagnostics: overfitting (val ↑), spikes (>3σ), plateaus (tail flat), NaN/Inf
4. Per-epoch CV analysis to detect worsening oscillation
5. Cross-metric comparison to find the bottleneck loss

**Full methodology:** `references/training-curve-diagnostics.md`
**Ready-to-run script:** `scripts/analyze_tb_curves.py <tb_logdir>`

```bash
# Quick usage
python ~/.hermes/skills/mlops/ml-training-workflows/scripts/analyze_tb_curves.py ./runs/my_run
```

## 10b. Model Architecture Exploration with CodeGraph

For projects with `.codegraph/` initialized, use CodeGraph MCP tools to understand architecture:

```bash
# Initialize (once per project)
cd /path/to/model && codegraph init && codegraph index
```

Then query via MCP tools:
- `codegraph_context` — "how does the encoder work" (returns entry points + related symbols + code)
- `codegraph_trace` — trace call path between two symbols (e.g., encoder → loss)
- `codegraph_explore` — batch-inspect multiple related symbols in one call
- `codegraph_impact` — "what breaks if I change X"

Best used for learning a new codebase before making changes.

## 11. Experiment Isolation: Copy Before Modifying

**User preference (strong):** Never modify source model code (`ai_model/`, `src/model/`, etc.) when running experiments. Always copy to a working directory first.

```bash
# WRONG: modifies source
cd model && python ai_model/train.py --mode small

# RIGHT: copy, fix, run from copy
cp -r ai_model experiments/baseline/model
# apply fixes to experiments/baseline/model/ only
python experiments/baseline/model/train.py --mode small
```

**Workflow:**
1. Copy source to `experiments/<name>/model/`
2. Apply all modifications (bug fixes, config changes) to the COPY
3. Run training from the copy
4. Verify with `diff ai_model/ experiments/<name>/model/` — only intentional changes should appear
5. Source code remains pristine for other experiments

**Why:** Multiple experiments may run in parallel or sequentially. Modifying source creates cross-contamination between experiments and makes it impossible to diff experiment vs baseline.

## 12. Pitfall: `__file__` Path Breakage When Copying Code

**Problem:** Training scripts commonly compute paths relative to `__file__`:
```python
_this_dir = os.path.dirname(os.path.abspath(__file__))    # ai_model/
_model_dir = os.path.dirname(_this_dir)                    # model/
_project_root = os.path.dirname(_model_dir)                # project root (where database/ lives)
```

When you copy `ai_model/train.py` to `experiments/baseline/model/train.py`, the depth changes:
```
Original:  ai_model/train.py               → 2 levels to project root
Copy:      experiments/baseline/model/train.py → 4 levels to project root
```

The script will look for `database/` at the wrong path and fail with:
```
ValueError: num_samples should be a positive integer value, but got num_samples=0
```
(because the dataset scan finds 0 files at the wrong location)

**Fix:** Adjust the `__file__`-relative path calculation in the copy:
```python
# Original (2 levels from ai_model/):
_project_root = os.path.dirname(_model_dir)

# Adjusted (4 levels from experiments/baseline/model/):
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_model_dir)))
```

**Systematic approach:** After copying, count the directory depth difference and add the right number of extra `os.path.dirname()` calls. Then verify:
```python
assert os.path.exists(os.path.join(_project_root, 'database')), f"Wrong root: {_project_root}"
```

**Other affected patterns:** Any code using `__file__` to locate sibling directories (data/, checkpoints/, configs/) will have the same issue.

> See also: `references/multi-experiment-baseline-workflow.md` for the full pattern of running baseline + N experiments with copy-based isolation.

## 13. Data Pipeline for Custom Datasets

### Scanning with pickle cache

For datasets with many files (30K+), scanning is slow. Cache the scan result:

```python
import pickle, hashlib

def scan_with_cache(root_dir, scan_fn, cache_dir='.'):
    dir_hash = hashlib.md5(root_dir.encode()).hexdigest()[:8]
    cache_path = os.path.join(cache_dir, f'scan_cache_{dir_hash}.pkl')

    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            cache = pickle.load(f)
        if cache.get('root_dir') == root_dir:
            return cache['samples']

    samples = scan_fn(root_dir)
    with open(cache_path, 'wb') as f:
        pickle.dump({'samples': samples, 'root_dir': root_dir}, f)
    return samples
```

### Train/test splitting (stratified by category)

When the dataset has a hierarchy (scene/level/sample), split **within each level** so every physics phenomenon is represented in both sets. Use a fixed seed for reproducibility, and output a stats table alongside the split files.

```python
# Core loop: for each level, shuffle and split
random.seed(42)
for level_dir in all_levels:
    samples = sorted(os.listdir(level_dir))
    random.shuffle(samples)
    split_idx = int(len(samples) * 0.8)
    train.extend(samples[:split_idx])
    test.extend(samples[split_idx:])
```

**Outputs:** `train.txt` + `test.txt` (absolute paths, one per line) + `split_stats.txt` (per-level counts).

> See `templates/split_train_test.py` for a complete ready-to-use script.

### Sliding window for temporal data

```python
# 36 frames, need windows of 24 frames (12 history + 12 predict)
# stride=6 gives overlapping windows
if len(frames) >= total_length:
    if split == 'train':
        start = random.randint(0, len(frames) - total_length)
    else:
        start = 0
    selected = frames[start:start + total_length]
else:
    selected = frames + [frames[-1]] * (total_length - len(frames))
```
