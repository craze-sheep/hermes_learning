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

### Attribute encoding (attr_dim=14)
```
[0:3]   size (3D)
[3:6]   lateralFriction, rollingFriction, spinningFriction
[6]     restitution
[7]     mass
[8]     static flag
[9:13]  object_type one-hot (ground/sphere/box/cylinder)
```

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
