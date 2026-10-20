# Example: Model Code Analysis (PhysicsObjectGraphPredictor)

This is an example of the depth expected when analyzing a model codebase BEFORE writing paper notes.

## Architecture Summary

```
Input: rgb[B,T,3,128,128], mask[B,T,N,128,128], obj_attrs[B,N,14], dyn_state[B,T,N,16], force_matrix[B,T,N,N,3]
    ↓
Encoder (encoder.py):
  - VisualEncoder: 4-layer CNN (32→64→128→128), stride=2, GroupNorm+GELU
    - Total stride: 16x (128→8)
    - Output: [B,T,128,8,8]
  - MaskedROIPooler: masked average pooling with GT masks → [B,T,N,128]
  - PhysicsEncoder: attr_net(14→64) + state_net(16→64) → fusion(128→128)
  - Fusion: concat visual+physics → Linear(256→128) + LayerNorm + GELU
    ↓
Interaction (interaction.py):
  - ForceAwareEdgeNetwork: edge_input(14d) = force_ij(3)+force_ji(3)+rel_pos(3)+rel_vel(3)+dist(1)+force_mag(1)
    → MLP(14→64→64) → edge_feat [B,T,N,N,64]
  - GNNSingleLayer × 2:
    - message_fn: MLP(node_i||node_j||edge → hidden → node_dim)
    - aggregation: mean over valid neighbors
    - update: GRUCell(node_dim, node_dim)
    ↓
Temporal (temporal.py):
  - TemporalGRU: 2-layer GRU, hidden_dim=128
    - encode_history: GRU over [Th, N, D] → h_last [B,N,2,128]
    - decode_future: autoregressive, each step feeds output back as input
    ↓
Decoder (decoder.py):
  - StateHead: MLP(128→256→256→16)
  - CollisionHead: MLP(node_i||node_j|||diff| → 64→1)
  - MaskHead: Linear → reshape to 8×8 → 4x ConvTranspose2d (32→16→8→4→1)
  - RGBDecoder: appearance_head(128→128→3, sigmoid) + bg_decoder(4x ConvTranspose2d)
    - Composite: Σ(mask_i × color_i) + bg × (1 - total_mask)
    ↓
Loss (loss.py):
  - RGB: L1 + 0.5×MSE
  - State: SmoothL1 with per-component weights (pos=1.0, quat/vel=0.5, angvel/force=0.25)
  - Collision: Focal BCE (γ=2.0)
  - Mask: BCE + Dice
  - Total: 1.0×rgb + 0.5×state + 0.5×collision + 0.3×mask
```

## Key Weaknesses Identified

1. **Visual encoder too weak** — 4-layer CNN, no pretrained features, only ~0.5M params
2. **GNN uses mean aggregation** — all neighbors weighted equally, can't distinguish important vs unimportant
3. **No residual connections in GNN** — 2 layers without skip connections
4. **GRU temporal with no attention** — long-range dependencies decay
5. **Autoregressive decoding** — error accumulation on long horizons
6. **RGB decoder too simple** — 3-dim color per object, no spatial appearance
7. **No perceptual loss** — only pixel-level L1/MSE, no SSIM or LPIPS
8. **No scheduled sampling** — train-test discrepancy in autoregressive mode
9. **Uses GT mask for ROI pooling** — can't handle real-world scenes without annotations
10. **Manual loss weights** — rgb=1.0, state=0.5, collision=0.5, mask=0.3 need tuning
11. **No energy conservation** — physics consistency not enforced
12. **No curriculum learning** — all samples treated equally regardless of complexity

## Dimension Flow (Critical for Paper Notes)

When writing paper notes, you MUST reference actual dimensions:
- fused_dim = 128 (object token dimension)
- gnn_edge_dim = 64 (edge feature dimension)
- gru_hidden_dim = 128 (temporal hidden dimension)
- state_dim = 16 (pos[3]+quat[4]+vel[3]+angvel[3]+force[3])
- attr_dim = 14 (size[3]+friction[4]+mass[1]+restitution[1]+static[1]+type[4])
- max_objects = 7
- image_size = 128
- history_length = 12, predict_length = 12
