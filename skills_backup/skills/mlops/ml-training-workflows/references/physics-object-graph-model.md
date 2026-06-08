# PhysicsObjectGraphPredictor — Session Reference

Architecture designed for physics simulation video prediction with 8GB GPU constraint.
Built in `/home/lzy/project/slot-datamaking/model/ai_model/`.

## Architecture Summary

```
RGB frames + Object masks + Static attrs + Dynamic state + Force matrix
  ↓
[PhysicsObjectEncoder]  Dual-stream: CNN visual + MLP physics → fused tokens [B,T,N,D]
  ↓
[ForceAwareGNN]         2-layer GNN with force-vector edge features
  ↓
[TemporalGRU]           2-layer GRU: encode history → autoregressive decode future
  ↓
[MultiHeadDecoder]      State MLP + Collision pairwise MLP + Mask ConvT + RGB composite
```

## Key Design Choices

| Decision | Rationale |
|----------|-----------|
| GRU over Transformer | Physics is sequential; GRU has explicit recurrence, lower memory |
| Force matrix as edge features | Explicit physics signal — not just learned attention |
| Masked ROI pooling | Object-centric; more precise than bbox-based ROI pooling |
| RGB composite decoder | Foreground=appearance×mask + background; cheaper than full generation |
| Separate physics encoder | Explicit mass/friction/geometry encoding (inductive bias) |

## Data Format (Kubric + Blender + PyBullet)

Per-sample structure in `database/S{scene}/L{level}/{sample_id}/`:

```
video.json              # fps=12, num_frames=36, gravity=[0,0,-9.8], cameras
object_static.json      # list of objects: id, type, mass, radius, size, friction, restitution, static flag
dynamic/{frame}/
  {frame}.png           # 128×128 RGB
  object_segment/{id}.npz    # mask: uint8 [128,128], 0 or 1
  object_dynamicjson/{id}.json  # position[3], quaternion[4], velocity[3], angular_velocity[3], resultant_force[3]
  force_matrix.json     # {object_order: [1,2,...], force_matrix: 10×10 with [fx,fy,fz] or null}
```

### Attribute encoding (attr_dim=13 after unification)
```
[0:3]   size (3D)
[3:6]   lateralFriction, rollingFriction, spinningFriction
[6]     restitution
[7]     mass
[8]     static flag
[9:12]  object_type one-hot: sphere[1,0,0], cube[0,1,0], cylinder[0,0,1]
```

### TYPE_MAP Unification (2026-06-01 decision)

The dataset has 7 raw object_type strings but only 3 physical shapes in PyBullet:

| Raw type | PyBullet shape | static | Unified to |
|----------|---------------|--------|-----------|
| ground | kb.Cube | true | cube |
| sphere | kb.Sphere | false | sphere |
| cube | kb.Cube | false | cube |
| cylinder | kb.Cylinder | false | cylinder |
| wall | kb.Cube | true | cube |
| ramp | kb.Cube | true | cube |
| obstacle | kb.Cube | true | cube |

Code fix in `model/ai_model/dataset.py`:
```python
TYPE_MAP = {'sphere': 0, 'cube': 1, 'cylinder': 2}
NUM_TYPES = 3
TYPE_ALIAS = {'ground': 'cube', 'box': 'cube', 'wall': 'cube', 'ramp': 'cube', 'obstacle': 'cube'}
```

Config fix in `model/ai_model/config.py`:
```python
attr_dim: int = 13  # was 14
```

Old checkpoints incompatible — retrain from scratch.

**Fastest way to audit types: read generation scripts, not the database:**
```bash
for s in S1 S2 S3 S4 S5 S6 S7 S8; do
  script="task/task6-脚本编写/generate_${s,,}_dataset.py"
  echo "$s: $(grep -oP '(sphere|cube|cylinder|wall|ramp|obstacle)_spec\(' "$script" | sort | uniq -c)"
  echo "   LEVEL_TARGETS: $(grep 'LEVEL_TARGETS' "$script")"
done
```

Object counts per scene (from generation scripts):
- S1: sphere only (750 samples)
- S2: cube + sphere + cylinder (680 samples)
- S3: cube + sphere + cylinder + ramp (920 samples)
- S4: sphere + cube + cylinder + wall (1150 samples)
- S5: sphere + cylinder + cube (920 samples)
- S6: sphere + cube + cylinder (920 samples)
- S7: sphere + wall + cylinder + cube (1240 samples)
- S8: sphere + cube + wall + cylinder + obstacle (1680 samples)

max_objects=7 verified OK — actual max is 6 (2=100, 3=207, 4=69, 5=12, 6=12 samples).

### State encoding (state_dim=16)
```
[0:3]   position (world coords)
[3:7]   quaternion [w,x,y,z]
[7:10]  velocity (m/s)
[10:13] angular_velocity (rad/s)
[13:16] resultant_force (N)
```

### Normalization
```python
state_std[0:3] = 5.0     # position
state_std[3:7] = 1.0     # quaternion (no norm)
state_std[7:10] = 10.0   # velocity
state_std[10:13] = 5.0   # angular velocity
state_std[13:16] = 50.0  # force
force_std = [50, 50, 50]  # force matrix
```

### Normalization Audit (2026-06-01)

**What IS normalized:** RGB (→ [-1,1]), dyn_state (per-component std), force_matrix (÷50)
**What is NOT normalized:** obj_attrs (14-dim: size, friction, mass, restitution, type one-hot)
**Scale source:** Hardcoded in `_compute_norm_stats()` — NOT computed from data

**Issues found:**
1. `obj_attrs` has no normalization — mass spans 0 (static) to ~10 (heavy objects),
   size varies by object type. MLP receives mixed-scale features.
2. State normalization stds are rough estimates, not data-derived. If actual velocity
   range is [-20, 20] but std=10.0, the normalized range is [-2, 2] — acceptable but
   not optimal.
3. Energy conservation loss denormalizes velocity via `vel_scale=10.0` (loss.py:160).
   This must match the dataset's `state_std[7:10] = 10.0`. If either changes, the
   other must follow.
4. Energy loss uses `mass` from obj_attrs (unnormalized) with `vel` (denormalized) —
   this is correct since mass is in physical units. But if mass were normalized,
   the energy calculation would need adjustment.

**Recommendation:** Run a data stats pass and replace hardcoded scales.

## Parameter Counts vs GPU Fit

| Config | fused_dim | Params | Peak GPU (bs=2) |
|--------|-----------|--------|-----------------|
| tiny | 32 | 132K | ~138 MB |
| medium | 64 | 364K | ~205 MB |
| small_8gb | 96 | 848K | (not tested end-to-end) |

## Edge Feature Construction (14-dim input)

```
edge_ij = [force_ij(3), force_ji(3), rel_pos(3), rel_vel(3), dist(1), force_mag(1)]
→ MLP → edge_dim
```

Where `rel_pos = pos_i - pos_j`, extracted from state vector indices [0:3] and [7:10].

## Loss Weight Calibration Results

After 50 steps on real data (22K samples, 3 objects, 6+6 frames):

| Loss | Raw value | Weight | Contribution |
|------|-----------|--------|-------------|
| state | 0.12 | 1.0 | 0.12 |
| collision | 0.03 | 1.0 | 0.03 |
| rgb | 0.45 | 1.0 | 0.45 |
| mask | 60,000 | 0.001 | 60.0 |

**Convergence (50 steps):**
- state: 6.55 → 0.12 (↓98%)
- collision: 0.90 → 0.03 (↓97%)
- rgb: 1.23 → 0.45 (↓64%)

## Files

```
model/ai_model/
├── config.py          # AIModelConfig dataclass
├── encoder.py         # PhysicsObjectEncoder (VisualEncoder + PhysicsEncoder + MaskedROIPooler)
├── interaction.py     # ForceAwareGNN (ForceAwareEdgeNetwork + GNNSingleLayer)
├── temporal.py        # TemporalGRU
├── decoder.py         # MultiHeadDecoder (StateHead + CollisionHead + MaskHead + RGBDecoder)
├── loss.py            # PhysicsLoss (RGB + state + collision + mask)
├── model.py           # PhysicsObjectGraphPredictor (end-to-end)
├── data_adapter.py    # Wraps baseline PhysicsVideoDataset via importlib
├── train.py           # Training with OOM auto-retry
└── checkpoints/
    ├── balanced_train.pt
    └── best.pt
```

## Training Commands

```bash
conda run -n model python model/ai_model/train.py --mode smoke   # 3 steps
conda run -n model python model/ai_model/train.py --mode small   # 20 steps
conda run -n model python model/ai_model/train.py --mode train --epochs 5
```

## Training Run Log (2026-05-31 → ongoing)

Config: fused_dim=96, gru=96, gnn=96, history=12, predict=12, max_obj=7
GPU: RTX 4060 Laptop (8GB), batch=16, AMP=True
Data: 25504 train / 6376 val samples
Params: 1,058,910

**5-epoch results (training still in progress for epochs 6-10):**

| Loss | Train Start | Train End | Val Start | Val End | Status |
|------|------------|-----------|-----------|---------|--------|
| Total | 1.28 | -9.95 | -3.53 | -10.22 | OK |
| RGB | 0.63 | 0.007 | 0.007 | 0.004 | OK |
| SSIM | 0.44 | 0.013 | 0.012 | 0.008 | OK |
| LPIPS | 0.0 | 0.0 | 0.0 | 0.0 | ⚠ weight=0 |
| Physics State | 0.053 | 0.002 | 0.003 | 0.002 | OK |
| Collision Class | 0.26 | 0.0003 | 0.00001 | ~0 | OK |
| Collision Effect | 0.081 | 0.002 | 0.0 | 0.0 | OK |
| Seg Mask | 1.55 | 0.044 | 0.047 | 0.024 | ⚠ slight val ↑ |
| Energy Conserv | 1.63 | 0.030 | 0.002 | 0.006 | ⚠ overfitting + oscillation |

**Key findings:**
- Energy conservation loss has CV=1.87 (most unstable), spikes getting worse per epoch
  - Epoch 2: max spike 0.092, >0.05 = 9.8%, >0.1 = 0.0%
  - Epoch 5: max spike 0.585, >0.05 = 18.3%, >0.1 = 17.1%
  - Root cause: KE = 0.5*m*v² amplifies velocity errors via squaring
  - Mitigation options: Huber loss, weight decay, gradient clipping on physics loss
- LPIPS loss disabled (weight=0.0) — intentional or oversight?
- Seg mask validation loss slight uptick at epoch 5 (0.0240 → 0.0241)
- Overall convergence good, model learning across all active losses
