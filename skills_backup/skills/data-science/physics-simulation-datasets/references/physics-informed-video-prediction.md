---
name: physics-informed-video-prediction
description: Design and implement physics-informed video prediction models that utilize multi-modal data (RGB, depth, segmentation masks, physics states, force matrices, object attributes). Covers dataset investigation, framework selection, architecture design, and phased implementation.
tags: [physics, video-prediction, multi-modal, slot-attention, gnn, object-centric, rigid-body, kubric]
---

# Physics-Informed Video Prediction

When to load: user has a multi-modal physics simulation dataset and wants to build/train a model that predicts future video frames using physics knowledge. Also load for: framework research for physics datasets, extending visual models with physics branches, designing multi-task losses for physics+vision.

## 1. Dataset Investigation Methodology

Before choosing a framework, thoroughly investigate the dataset's modalities:

```python
import numpy as np
import json, os

# Check npz structure
npz = np.load('path/to/sample.npz')
for k in npz.files:
    print(f'{k}: shape={npz[k].shape}, dtype={npz[k].dtype}')

# Check JSON metadata (object attributes, force matrices, physics params)
with open('object_static.json') as f:
    objs = json.load(f)
    # Identify: object_type, size/radius, mass, friction properties

# Check dynamic states per frame
with open('object_dynamicjson/obj.json') as f:
    dyn = json.load(f)
    # Identify: position, quaternion, velocity, angular_velocity, resultant_force

# Check force matrix structure
with open('force_matrix.json') as f:
    fm = json.load(f)
    # Identify: object_order, force_matrix dimensions, null vs non-null entries
```

Catalog ALL modalities before framework selection. Most models only use 1-2 modalities — identify which are wasted.

## 2. Framework Selection Matrix

Compare frameworks by data utilization rate:

| Modality | SAVi | GNS | SlotFormer | PhyDNet | SlotPi | PhysGen |
|----------|------|-----|------------|---------|--------|---------|
| RGB video | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Depth | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Segmentation mask | ⚠️ learned | ❌ | ⚠️ learned | ❌ | ⚠️ | ❌ |
| Object attributes | ❌ | ⚠️ | ❌ | ❌ | ❌ | ✅ |
| Physics state | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Force matrix | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |

Key principle: No single existing framework uses all modalities. The best approach is usually to EXTEND an existing model with additional branches, not to find one model that does everything.

## 3. Architecture Patterns

### Pattern A: SlotFormer + Physics Branches (Recommended for most cases)

When you already have a working slot-based video prediction model:

```
Input Processing:
├── RGB → DINOv2/ViT → visual features (using GT masks for ROI)
├── Depth → Depth Encoder (CNN) → depth features per object
├── Physics State → State Encoder (MLP) → state features per object
├── Object Attributes → Embedding → attribute features per object
└── Force Matrix → Edge features for GNN

Core:
├── Slot Encoder (modified to accept physics+depth conditioning)
├── GNN Interaction Layer (nodes=slots, edges=force vectors)
├── Temporal Predictor (Transformer/S6 with physics-aware attention)
└── Multi-head Decoders (RGB, depth, mask, physics state)
```

### Pattern B: GNN-First (When physics state is primary)

When the main goal is physics state prediction:

```
Nodes = objects with (visual_feat, physics_state, attributes)
Edges = force vectors + relative positions
GNN → predict next physics state
Decoder → render RGB + depth from predicted state
```

### Pattern C: Diffusion + Physics Conditioning (When generation quality matters)

```
Conditioning: physics state history + object attributes
Diffusion model generates future frames
Physics loss constrains generated dynamics to be physically plausible
```

## 4. Phased Implementation

Always implement incrementally. Each phase should produce a working model:

1. **Baseline**: Visual-only model (e.g., SlotFormer on RGB + GT masks)
   - Verify: slot quality + video prediction metrics

2. **+Physics State**: Concat physics state to slot features
   - Add Physics State Decoder as auxiliary loss
   - Highest ROI — makes model "understand" 3D motion
   - ~200 lines of code

3. **+Force Matrix GNN**: Add GNN layer between slots
   - Nodes = slot + physics state + attribute embedding
   - Edges = force vectors from force_matrix.json
   - Teaches model inter-object interactions
   - ~300 lines of code

4. **+Depth**: Add depth encoder/decoder branches
   - Depth features concat to slot features
   - Depth reconstruction as auxiliary loss
   - ~150 lines of code

5. **Multi-task Joint Training**:
   ```
   Loss = λ1*RGB_recon + λ2*Depth_recon + λ3*Mask_CE
        + λ4*Physics_L2 + λ5*Force_L2 + λ6*Perceptual
   ```

## 5. Pitfalls

- **Don't build from scratch when you can extend**: If you have a working SlotFormer/SAVi, add branches instead of reimplementing SAVi+GNS from scratch. Saves weeks of work.
- **JAX/TF/PyTorch mixing**: SAVi is JAX, GNS is TF. If your project is PyTorch, prefer PyTorch ports (GNS-PyTorch, SlotFormer) to avoid multi-framework headaches.
- **Force matrix sparsity**: Many entries are null or zero. Handle gracefully — use zero for null, mask out ground-ground interactions.
- **Physics state normalization**: Position/velocity can have very different scales across scenarios. Normalize per-scene or use LayerNorm.
- **GT mask vs learned segmentation**: If you have GT masks, use them for ROI pooling instead of learning segmentation. This is free information.
- **Depth map quality**: Check for extreme values (e.g., 1e10 for sky/background). Mask or clamp before feeding to encoder.
- **Object count variation**: Scenes may have 1-7 objects. Use padding + attention masks, or process per-object and aggregate.
- **Mask loss magnitude at 128×128**: Raw BCE+Dice on full-res masks is ~40K-60K. Must use weight ~0.001 or downsample to 32×32 before computing loss. See `ml-training-workflows/references/physics-object-graph-model.md` for calibration data.
- **Collision label generation**: From `force_matrix.json`, compute `||F_ij|| > threshold` (in un-normalized space). Use Focal BCE since collision events are rare (~5-10% of pairs).
- **Force matrix format**: 10×10 fixed slots, `object_order` gives valid indices. Null = unused slot, `[0,0,0]` = valid but no contact. Compress to N×N before feeding to model.

## 6. Key References

See `references/` directory for:
- Framework comparison with arXiv links and code availability
- Specific architecture modifications for SlotFormer
- Dataset structure examples (Kubric-style physics simulation data)
