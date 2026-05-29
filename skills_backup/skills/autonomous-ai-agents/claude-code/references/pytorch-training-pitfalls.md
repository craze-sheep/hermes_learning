# PyTorch Training Pitfalls (Real Bugs Found in Production)

## 1. sigmoid(0) = 0.5 Leak for Invalid Tokens

**Problem**: Zeroing out logits for invalid/padding objects and then applying sigmoid:
```python
mask_logits = mask_logits * valid_mask.float()  # sets invalid to 0
mask_prob = torch.sigmoid(mask_logits)           # sigmoid(0) = 0.5, NOT 0!
```
The 0.5 probability leaks into downstream compositing (e.g., RGB synthesis from masks).

**Fix**: Use large negative value for sigmoid to 0:
```python
invalid = ~valid_mask.unsqueeze(-1)
mask_logits = mask_logits.masked_fill(invalid, -10.0)  # sigmoid(-10) approx 0.0000454
mask_prob = torch.sigmoid(mask_logits)
```

**Found in**: decoder.py mask head, RGB decoder compositing.

## 2. GroupNorm Divisibility

**Problem**: `nn.GroupNorm(num_groups, num_channels)` requires `num_channels % num_groups == 0`. When model configs change channel counts (e.g., `base_channels=24` to `24//2=12`), `GroupNorm(8, 12)` fails.

**Fix**: Dynamic group count selection:
```python
def _best_group(channels, preferred=8):
    if channels <= 0: return 1
    for g in range(min(preferred, channels), 0, -1):
        if channels % g == 0: return g
    return 1

nn.GroupNorm(_best_group(channels), channels)
```

**Found in**: decoder.py mask decoder and RGB background decoder.

## 3. valid_mask Must Flow Through All Compositing

**Problem**: Decoder accepts `valid_mask` parameter but never uses it in forward pass. Padding objects contribute to output synthesis.

**Fix**: Apply valid_mask at every point where per-object tensors are aggregated:
```python
# Before summing over objects
mask_prob_valid = mask_prob * valid_mask.view(B, 1, N, 1, 1).float()
composited = (appearance * mask_prob_valid).sum(dim=2)
```

**Found in**: RGBDecoder.forward - valid_mask was accepted but ignored.

## 4. Static-Static Pair Exclusion in Collision Loss

**Problem**: Collision pair_mask only excludes self-edges and padding. Static objects (ground, walls, ramps) never collide with each other, but their pairs dilute the loss.

**Fix**: Get static_flag from obj_attrs (index 8) and mask:
```python
static_flag = (obj_attrs[..., 8] > 0.5)  # [B, N]
static_pair = static_flag.unsqueeze(1) & static_flag.unsqueeze(2)  # [B, N, N]
pair_mask = pair_mask * (~static_pair).float()
```

**Found in**: decoder.py MultiHeadDecoder.forward.

## 5. Dead nn.Module Submodules (input_proj Never Called)

**Problem**: Define `self.input_proj = nn.Linear(...)` in `__init__` but forget to call it in `forward`. Works when input_dim == hidden_dim (identity), crashes when they differ.

**Fix**: Always verify every `nn.Module` in `__init__` is called in `forward`.

**Found in**: temporal.py TemporalGRU - input_proj defined but never used.

## 6. deterministic scene_id with hashlib

**Problem**: `hash(string)` is randomized per Python process (PYTHONHASHSEED). Cross-run reproducibility broken.

**Fix**: Use hashlib:
```python
import hashlib
scene_id = int(hashlib.md5(scene.encode()).hexdigest()[:8], 16) % num_buckets
```

**Found in**: dataset.py __getitem__.
