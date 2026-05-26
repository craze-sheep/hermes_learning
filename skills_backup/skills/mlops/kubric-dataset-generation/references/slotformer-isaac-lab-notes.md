# SlotFormer + Isaac Lab Migration Notes

## SlotFormer Pipeline

Two core models:
1. **SAVi/STEVE** — Slot encoder-decoder: video → encoder → slots → decoder → reconstructed image
2. **SlotFormer** — Slot-space video predictor: slot sequence(t=1..T) → Transformer → future slots(t=T+1..T+K)

Downstream heads (Aloe, Readout, Classifier) are lightweight, not independent models.

### Resolution

All datasets use **128×128**. Sources:
- `scripts/data_preproc/clevrer_video2frames.py:17` — `RESIZE = (128, 128)`
- `scripts/data_preproc/physion_video2frames.py:8` — `RESIZE = (128, 128)`
- `slotformer/physion_vqa/configs/readout_physion_params.py:38` — `resolution = (128, 128)`
- `slotformer/video_prediction/configs/slotformer_physion_params.py:36` — `resolution = (128, 128)`

Original dataset resolutions (before SlotFormer resize):
- CLEVRER: 480×320
- Physion: 640×480
- PHYRE: 256×256

### Training Pipeline per Dataset

| Step | Physion | CLEVRER | PHYRE |
|------|---------|---------|-------|
| 1. Tokenizer | dVAE | — | — |
| 2. Slot extractor | STEVE | SAVi | SAVi |
| 3. Slot predictor | SlotFormer | SlotFormer | SlotFormer |
| 4. Downstream | Readout (VQA) | Aloe (VQA) | Classifier (Planning) |

## Isaac Lab (PhysX 5) Migration

### Official Hardware Requirements

Source: `isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html`

- OS: Ubuntu 22.04 (Linux x64) or Windows 11 (x64)
- RAM: 32GB+
- GPU VRAM: 16GB+ (rendering may need more)
- Driver: Linux 580.65.06+, Windows 580.88
- Ubuntu 24.04 NOT fully supported
- **No GTX support, no mobile GPU support** (community consensus, not explicitly stated in docs)

User's current hardware (RTX 4060 Laptop, 8GB VRAM) is **below the 16GB minimum**.

### PyBullet → PhysX 5 Parameter Mapping

| PyBullet | PhysX 5 (Isaac Lab) | Notes |
|----------|---------------------|-------|
| `lateralFriction` | `static_friction` + `dynamic_friction` | PyBullet uses one value for both |
| `rollingFriction` | ❌ No direct equivalent | Use `angular_damping` or custom torque |
| `spinningFriction` | `torsional_patch_radius` | Different mechanism, similar effect |
| `restitution` | `restitution` ✅ | Same |
| `mass` | `mass` ✅ | Same |
| `initial_position` | `position` ✅ | Same |
| `initial_quaternion` | `orientation` ⚠️ | Kubric=**wxyz**, Isaac Lab=**xyzw** |
| `initial_velocity` | `linear_velocity` ✅ | Same |
| `initial_angular_velocity` | `angular_velocity` ✅ | Same |
| `static` | `kinematic_enabled` ✅ | Same concept |

### Key Gaps

- **rollingFriction**: No PhysX equivalent. Critical for S2 (ball sliding) and S7 (cylinder rolling). Workaround: `angular_damping` or per-step custom resistance torque.
- **Ramp primitive**: Not built-in. Need custom USD mesh or rotated box.
- **Quaternion convention**: Must convert wxyz ↔ xyzw.

### Per-Frame Data Capture

Isaac Lab can capture per-frame data via camera sensors (unlike Kubric which renders all frames at once after simulation):

```python
camera.update(dt)
rgb = camera.data.output["rgb"]               # (H, W, 4) RGBA
seg = camera.data.output["semantic_segmentation"]
depth = camera.data.output["distance_to_camera"]
norm = camera.data.output["normals"]
```

Each `sim.step()` + `camera.update()` produces current frame data immediately. This is fundamentally different from Kubric's "simulate all → render all" pipeline. Isaac Lab renders in real-time.

### Isaac Lab Config Classes

```python
# Material properties
RigidBodyMaterialCfg(
    static_friction=0.5,
    dynamic_friction=0.5,
    restitution=0.0,
    friction_combine_mode="average",  # average/min/multiply/max
    restitution_combine_mode="average",
)

# Rigid body properties
RigidBodyPropertiesCfg(
    linear_damping=0.0,
    angular_damping=0.0,
    disable_gravity=False,
    max_depenetration_velocity=5.0,
    solver_position_iteration_count=4,
)

# Contact properties
ContactPropertiesCfg(
    rest_offset=0.0,
    torsional_patch_radius=0.0,  # approximates spinning friction
    min_torsional_patch_radius=0.0,
)
```
