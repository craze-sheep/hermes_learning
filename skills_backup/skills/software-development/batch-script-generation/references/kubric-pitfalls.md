# Kubric Pitfalls for Dataset Generation

## Object Types Available

Kubric ONLY has these physical object types:
- `kb.Sphere` - scale = radius (uniform)
- `kb.Cube` - scale = (half_x, half_y, half_z)
- `kb.FileBasedObject` - load from .glb/.obj file

**NO `kb.Cylinder` exists.** Attempting to use it causes `AttributeError`.

## Simulating Cylinder

Option 1: Use Cube with appropriate scale (simpler, less accurate):
```python
# In build_asset():
if spec.object_type == "cylinder":
    assert spec.radius is not None and spec.height is not None
    # Approximate as cube
    scale = (spec.radius, spec.radius, spec.height / 2.0)
    return kb.Cube(scale=scale, **kwargs)
```

Option 2: Use FileBasedObject with cylinder mesh (accurate):
```python
if spec.object_type == "cylinder":
    return kb.FileBasedObject(
        simulation_filename="path/to/cylinder.obj",
        scale=(spec.radius, spec.radius, spec.height / 2.0),
        **kwargs
    )
```

## Quaternion Format

Kubric uses **WXYZ** format: `(w, x, y, z)`
PyBullet uses **XYZW** format: `(x, y, z, w)`

Conversion:
```python
def wxyz2xyzw(wxyz):
    w, x, y, z = wxyz
    return x, y, z, w

def xyzw2wxyz(xyzw):
    x, y, z, w = xyzw
    return w, x, y, z
```

## Ramp Rotation

For a ramp inclined at angle θ around y-axis:
```python
half_angle = incline_angle / 2.0
quat = (math.cos(half_angle), 0.0, math.sin(half_angle), 0.0)  # WXYZ
```

## Physics Parameters

PyBullet's `changeDynamics()` accepts:
- `lateralFriction` - sliding friction
- `rollingFriction` - rolling resistance
- `spinningFriction` - spinning resistance  
- `restitution` - bounciness (0-1)
- `mass` - in kg (0 for static)

## Contact Points

```python
contacts = physics_client.getContactPoints()
# Each contact: (unused, bodyA, bodyB, unused, unused, unused, 
#                unused, normalOnB, unused, normalForce, ...)
# Index 7: normal_on_b (tuple of 3)
# Index 9: normal_force (float)
```

## Ground Object

Ground is typically a static Cube:
```python
ground = kb.Cube(
    scale=(4.0, 3.0, 0.04),  # half-sizes
    position=(0, 0, -0.04),
    static=True,
    mass=0,
    segmentation_id=1
)
```

## Common Mistakes

1. **Forgetting mass=0 for static objects**: PyBullet treats mass=0 as static
2. **Wrong quaternion format**: Kubric=WXYZ, PyBullet=XYZW
3. **Scale is half-size for Cube**: `scale=(0.5, 0.5, 0.5)` creates 1x1x1 cube
4. **Sphere scale must be uniform**: `scale=(r, r, r)` not `scale=(r, 0, 0)`
5. **VIEWS dict nesting bug**: Copy-pasting VIEWS dicts can nest keys inside
   each other due to missing closing braces. Python won't error — the nested
   key silently becomes a value of the outer dict. Always verify VIEWS has
   the correct top-level keys after editing.
6. **Quaternion composition for lying orientations**: `lying_quat = ramp_quat * base_quat`
   requires actual quaternion multiplication. Simply using `ramp_quat` for all
   orientations is wrong — the lying rotation must be composed with the ramp rotation.
7. **Color hardcoding**: Spec says `color: [brown, gray]` but code hardcodes `color_name="brown"`.
   The color pool must be sampled, not fixed.
