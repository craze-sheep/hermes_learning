---
title: Physics Prediction Framework Comparison (2025)
updated: 2026-05-26
context: slot-datamaking project — 31,880 samples, 8 physics scenes, 7 modalities
---

## Dataset Structure (Kubric-style physics simulation)

```
database/
├── S{1-8}/                    # 8 scenes (free_fall, friction, incline, bounce, collision, etc.)
│   └── L{1-N}/               # levels per scene (varying physics parameters)
│       └── {sample_id}/      # 200-600 samples per level
│           ├── {id}.mp4       # RGB video, 128x128, 12fps, 36 frames
│           ├── {id}.npz       # depth maps: (36, 128, 128) float32
│           ├── object_static.json    # per-object: type, size, mass, friction
│           ├── video.json            # metadata: gravity, fps, physics_hz(240), camera params
│           └── dynamic/
│               └── {frame}/
│                   ├── {frame}.png           # RGB frame
│                   ├── force_matrix.json     # inter-object 3D forces (10x10 matrix)
│                   ├── object_segment/{id}.npz  # per-object mask: (128,128) uint8
│                   └── object_dynamicjson/{id}.json  # position, quaternion, velocity, ang_vel, resultant_force
```

Object types: ground, cube, sphere. Max 7 objects/scene (S8). Total ~12,000 samples across S1-S8.

## Top Relevant Papers/Frameworks (ranked by relevance)

### Tier 1: Most Relevant (2025-2026)

| Paper | Date | Key Idea | Code | Fit |
|-------|------|----------|------|-----|
| **SlotPi** | 2025.06 | Physics-informed slot attention with Hamiltonian principles | Not yet open (arxiv:2506.10778) | ★★★★★ |
| **Obj-Centric Diffusion for Physics** | 2025.07 | Diffusion + object-centric for physical reasoning | arxiv:2507.04920 | ★★★★ |
| **Learning Physical Dynamics for Obj-Centric Prediction** | 2024.03 | Unsupervised object-centric physical dynamics | arxiv:2403.10079 | ★★★★ |
| **Phantom** | 2026.04 | Physics-infused video generation, joint visual+physical | arxiv:2604.08503 | ★★★ |

### Tier 2: Strong Related Work

| Paper | Date | Key Idea | Code | Fit |
|-------|------|----------|------|-----|
| **PhysTwin** | ICCV 2025 | Physics-informed reconstruction from video | github:Jianghanxiao/PhysTwin ★409 | ★★★ |
| **PhysGen** | ECCV 2024 | Rigid-body physics-grounded video generation | github:stevenlsw/physgen ★349 | ★★★ |
| **Grounding GNS with Sensors** | 2023 | GNS + real sensor observations | arxiv:2302.11864 | ★★★ |
| **Face Interaction GNN for Rigid Dynamics** | 2022 | GNN for rigid-body collisions via face interactions | arxiv:2212.03574 | ★★★ |
| **IRIS** | 2026 | Benchmark for inverse physics from monocular video | arxiv:2603.16432 | ★★ |

### Tier 3: Foundation Components

| Component | Recommendation | Stars |
|-----------|---------------|-------|
| Visual encoder | DINOv2 (facebookresearch/dinov2) | 10k+ |
| Segmentation | SAM2 (facebookresearch/sam2) — but prefer GT masks | 13k+ |
| Depth | Depth Anything V2 — but prefer GT depth | 5k+ |
| GNN library | PyTorch Geometric (pyg) | 20k+ |
| Differentiable physics | Taichi / Brax / NVIDIA Warp | varies |

## Why SAVi+GNS+Transformer Is Suboptimal

Problems with the naive hybrid approach:
1. SAVi is JAX-only → hard to extend in PyTorch projects
2. SAVi only uses RGB → wastes depth, physics state, force matrix
3. GNS is particle-based → doesn't understand rigid bodies (sphere/cube)
4. Three separate models → no end-to-end training, information loss at interfaces
5. Force matrix and object attributes are completely unused

Data utilization: ~30% with SAVi+GNS vs 100% with modified SlotFormer.

## Recommended: Extend SlotFormer (not build from scratch)

If you have a working SlotFormer (ICLR 2023, github:pairlab/SlotFormer):
- It already handles slot extraction + temporal prediction
- Add physics state as slot conditioning (Phase 2, ~200 lines)
- Add GNN with force matrix as edge weights (Phase 3, ~300 lines)
- Add depth encoder/decoder (Phase 4, ~150 lines)
- Total: ~650 lines of modifications vs weeks of reimplementing SAVi+GNS

Key modification points in SlotFormer codebase:
- `slotformer/video_prediction/models/slotformer.py` → SlotRollouter class
- `slotformer/base_slots/models/` → StoSAVi slot encoder
- Add new: GNN interaction layer (use PyG), depth encoder, physics decoder

## Alternative: GNS-PyTorch as Physics Backbone

If physics state prediction is the primary goal (not video generation):
- github:zhouxian/GNS-PyTorch ★20 — PyTorch GNS implementation
- Nodes = objects with (visual_feat, physics_state, attributes)
- Edges = force vectors from force_matrix.json
- Predict next-step physics states, then render video as secondary task
