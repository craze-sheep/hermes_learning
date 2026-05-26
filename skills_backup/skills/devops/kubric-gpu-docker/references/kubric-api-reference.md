# Kubric API Quick Reference

## Object Creation

```python
import kubric as kb

# Sphere — scale = radius (single float)
sphere = kb.Sphere(
    name="sphere", position=(0, 0, 2.0), scale=0.22,
    velocity=(0, 0, 0), mass=1.0, static=False,
    friction=0.5, restitution=0.5,
    material=kb.PrincipledBSDFMaterial(color=(0.88, 0.1, 0.08, 1.0), roughness=0.55),
    segmentation_id=2,
)

# Cube — scale = (half_x, half_y, half_z)
size = (8.0, 6.0, 0.08)
ground = kb.Cube(
    name="ground", position=(0, 0, -size[2]/2),
    scale=tuple(v/2 for v in size),
    static=True, segmentation_id=1,
)

# Cylinder — scale = (radius, radius, half_height)
cylinder = kb.Cylinder(
    name="cyl", position=(0, 0, 0.17), scale=(0.16, 0.16, 0.11),
    mass=1.0, segmentation_id=3,
)
```

## Scene Setup

```python
scene = kb.Scene(resolution=(480, 480))
scene.frame_start = 0
scene.frame_end = 35          # 36 frames total (0-indexed)
scene.frame_rate = 12          # FPS
scene.step_rate = 240          # physics Hz
scene.gravity = (0, 0, -9.8)
scene.background = (0.03, 0.035, 0.04, 1.0)
scene.ambient_illumination = (0.08, 0.08, 0.08, 1.0)
```

## Camera

```python
# Perspective
cam = kb.PerspectiveCamera(
    name="camera_front", position=(0, -7.5, 3.2),
    look_at=(0, 0, 0.35), focal_length=35, sensor_width=32,
)

# Orthographic
cam = kb.OrthographicCamera(
    name="camera_top", position=(0, -0.01, 8.0),
    look_at=(0, 0, 0), orthographic_scale=5.0,
)
```

## Light

```python
scene += kb.DirectionalLight(
    name="sun", position=(-3, -4, 7),
    look_at=(0, 0, 0.5), intensity=2.6,
)
```

## Material

```python
mat = kb.PrincipledBSDFMaterial(color=(0.88, 0.1, 0.08, 1.0), roughness=0.55)
```

## Physics Properties via changeDynamics

After `simulator = PyBullet(scene, scratch_dir)`:

```python
client = simulator._physics_client
body_id = asset.linked_objects.get(simulator)
client.changeDynamics(body_id, -1,
    lateralFriction=0.5,      # sliding friction
    rollingFriction=0.01,      # rolling resistance
    spinningFriction=0.005,    # spin friction
    restitution=0.3,           # bounciness
    mass=1.0,                  # 0.0 for static
)
```

## Render Pipeline

```python
# 1. Simulate
simulator = PyBullet(scene, scratch / "pybullet")
simulator.run(frame_start=0, frame_end=35)

# 2. Create renderer AFTER simulation
renderer = Blender(scene, scratch / "blender",
    adaptive_sampling=True, use_denoising=True, samples_per_pixel=32)

# 3. Replay keyframes
for asset in scene.assets:
    keyframes = getattr(asset, "keyframes", None)
    if not keyframes: continue
    for member, frame_values in list(keyframes.items()):
        original = getattr(asset, member)
        try:
            for frame, value in sorted(list(frame_values.items())):
                setattr(asset, member, value)
                asset.keyframe_insert(member, frame)
        finally:
            setattr(asset, member, original)

# 4. Render
frames = renderer.render(return_layers=("rgba", "depth", "segmentation"))
```

## Resolution Reference

| Dataset | Original | SlotFormer training |
|---------|----------|-------------------|
| CLEVRER | 480×320 | 128×128 |
| Physion | 640×480 | 128×128 |
| PHYRE | 256×256 | 128×128 |

SlotFormer standard: **128×128** for all training.
