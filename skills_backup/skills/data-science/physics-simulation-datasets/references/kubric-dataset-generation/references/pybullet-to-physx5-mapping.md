# PyBullet → PhysX 5 (Isaac Lab) Parameter Mapping

Reference for migrating S1-S8 scene parameters from Kubric/PyBullet to Isaac Lab/PhysX 5.

## Material Parameters (RigidBodyMaterialCfg)

| PyBullet | PhysX 5 (Isaac Lab) | Notes |
|----------|---------------------|-------|
| `lateralFriction` | `static_friction` + `dynamic_friction` | PyBullet uses one value for both states. PhysX splits into μs (object at rest) and μd (object sliding). Set both to same value for PyBullet-equivalent behavior. |
| `rollingFriction` | ❌ No direct equivalent | PhysX has no native rolling resistance. Approximate via `angular_damping` on RigidBodyPropertiesCfg, or apply custom torque each step. **Major migration risk for S2/S7.** |
| `spinningFriction` | `torsional_patch_radius` (ContactPropertiesCfg) | Different mechanism — PhysX uses contact patch radius to approximate torsional friction. Not a 1:1 value mapping. |
| `restitution` | `restitution` | Direct equivalent. |

## Rigid Body Properties (RigidBodyPropertiesCfg)

| PyBullet | PhysX 5 (Isaac Lab) | Notes |
|----------|---------------------|-------|
| `mass` | `mass` | Direct. |
| `initial_position` | `position` | Direct. |
| `initial_quaternion` | `orientation` | ⚠️ Kubric uses **wxyz**, Isaac Lab defaults to **xyzw**. Must convert. |
| `initial_velocity` | `linear_velocity` | Direct. |
| `initial_angular_velocity` | `angular_velocity` | Direct. |
| `static=True` | `kinematic_enabled=True` | Direct equivalent. |
| `disableGravity` | `disable_gravity` | Direct. |

## Additional PhysX Parameters (no PyBullet equivalent)

| Parameter | Effect |
|-----------|--------|
| `linear_damping` | Air resistance equivalent |
| `angular_damping` | Can partially simulate rolling friction |
| `max_depenetration_velocity` | Prevents explosion on deep penetration |
| `solver_position_iteration_count` | Physics accuracy vs performance |
| `compliant_contact_stiffness` | Soft contact model |

## Geometry Primitives

| PyBullet | Isaac Lab | Notes |
|----------|-----------|-------|
| sphere(radius) | `SphereCfg(radius=)` | Direct. |
| cube(size) | `CuboidCfg(size=)` | Direct. |
| cylinder(radius, height) | `CylinderCfg(radius=, height=)` | Direct. |
| ramp (inclined plane) | No built-in primitive | Need USD mesh or rotated box. **S3 migration requires custom ramp mesh.** |

## Quaternion Convention

```python
# Kubric (PyBullet): [w, x, y, z]
quat_kubric = [1, 0, 0, 0]

# Isaac Lab (PhysX): [x, y, z, w] (default)
quat_isaac = [0, 0, 0, 1]

# Conversion
def kubric_to_isaac(q):
    return [q[1], q[2], q[3], q[0]]
```

## Official Hardware Requirements (Isaac Lab 2.0 / Isaac Sim 5.0)

Source: `isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html`

| Item | Official Minimum |
|------|-----------------|
| OS | Ubuntu 22.04 (Linux x64) or Windows 11 (x64) |
| RAM | 32 GB+ |
| GPU VRAM | 16 GB+ (more for rendering workflows) |
| Driver (Linux) | 580.65.06+ |
| Driver (Windows) | 580.88+ |

⚠️ **No specific GPU model required** — just 16GB+ VRAM. GTX series not explicitly excluded in docs but community consensus is RTX-only for RTX rendering features.
⚠️ **Ubuntu 24.04 not fully supported** for Isaac Sim source builds (needs GCC 11).
⚠️ **RTX 4060 (8GB) is below the 16GB minimum.** Headless simple scenes may work but rendering+physics will OOM.

## Isaac Lab Data Capture API

Isaac Lab can capture per-frame data via camera sensors (not a video generator — needs custom capture loop):

```python
camera = Camera(cfg=CameraCfg(width=640, height=480))
camera.update(dt)
rgb   = camera.data.output["rgb"]                    # (H, W, 4) RGBA
seg   = camera.data.output["semantic_segmentation"]  # instance/semantic seg
depth = camera.data.output["distance_to_camera"]     # depth map
norm  = camera.data.output["normals"]                # surface normals
bbox  = camera.data.output["bounding_box_2d"]        # 2D bounding boxes
```

Each `sim.step()` + `camera.update()` yields one frame as numpy array. Save as PNG or stitch to MP4.
Comparison: Kubric renders all frames after simulation; Isaac Lab captures frames during simulation (real-time).

## Installation (WSL2)

```bash
# pip install (simplest)
python3.11 -m venv ~/.venvs/isaacsim
source ~/.venvs/isaacsim/bin/activate
pip install isaacsim[all] --extra-index-url https://pypi.nvidia.com

# Isaac Lab
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab
./isaaclab.sh --install
```

Docker alternative: `nvcr.io/nvidia/isaac-sim:4.5.0`

## Key Differences from Kubric

| Aspect | Kubric | Isaac Lab |
|--------|--------|-----------|
| Rendering | Blender (Cycles/EEVEE) | Omniverse RTX (real-time ray tracing) |
| Physics | PyBullet (CPU) | PhysX 5 (GPU-accelerated) |
| Frame capture | `scene.render()` after all steps | `camera.update()` each step, immediate numpy array |
| Data pipeline | Built-in: scene → video | DIY: step + capture + stitch |
| Ramp primitive | Built-in | Need custom USD or rotated box |
