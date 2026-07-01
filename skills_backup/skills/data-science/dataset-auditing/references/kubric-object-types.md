# Kubric/PyBullet Object Type Mapping

## Dataset Object Types (6 types)

| Type | static | PyBullet | Instances | Scenes |
|------|--------|----------|-----------|--------|
| ground | true | kb.Cube | 31880 | S1-S8 |
| sphere | false | kb.Sphere | 53429 | S1,S4-S8 |
| cube | false | kb.Cube | 15026 | S2,S3,S6,S8 |
| wall | true | kb.Cube | 5750 | S4,S7,S8 |
| cylinder | false | kb.Cylinder | 2905 | S2-S8 |
| ramp | true | kb.Cube | 2640 | S3 |

## PyBullet Shape Mapping

In Kubric's `build_asset()` function:

```python
if spec.object_type == "sphere":
    return kb.Sphere(scale=spec.radius, **kwargs)
if spec.object_type in {"cube", "ground", "wall"}:
    scale = tuple(v / 2.0 for v in spec.size)
    return kb.Cube(scale=scale, **kwargs)
if spec.object_type == "cylinder":
    return kb.Cylinder(scale=(spec.radius, spec.radius, spec.height / 2.0), **kwargs)
```

## Geometry Parameters by Type

| Type | radius | size | height |
|------|--------|------|--------|
| ground | null | [(4,4,0.08), (8,6,0.08), (9,6,0.08), (10,5,0.08), (16,6,0.08)] | null |
| sphere | [0.18, 0.22, 0.28] | null | null |
| cube | null | [(0.18,0.18,0.18), (0.24,0.24,0.24), (0.30,0.30,0.30)] | null |
| cylinder | [0.16, 0.20, 0.24] | null | [0.22, 0.28, 0.34] |
| ramp | null | [(2.4, 1.0, 0.12)] | null |
| wall | null | [(0.1, 5.0, 1.2)] | null |

## Model TYPE_MAP (unified)

For the ML model, all kb.Cube types can be unified:

```python
TYPE_MAP = {'sphere': 0, 'cube': 1, 'cylinder': 2}
NUM_TYPES = 3
TYPE_ALIAS = {
    'ground': 'cube', 'box': 'cube',
    'wall': 'cube', 'ramp': 'cube', 'obstacle': 'cube',
}
# attr_dim: 3(size) + 4(friction) + 1(mass) + 1(restitution) + 1(static) + 3(type) = 13
```

Model distinguishes static vs dynamic objects via the `static` flag.

## Deprecated Types

- `box`: was alias for `cube`, no longer used
- `obstacle`: was alias for `wall`, merged into `wall` type
