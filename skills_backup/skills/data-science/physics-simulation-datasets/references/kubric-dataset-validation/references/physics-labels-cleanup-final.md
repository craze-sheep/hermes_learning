# S1-S8 physics_labels.json Cleanup — Final Status

**Date**: May 2026  
**Action**: Removed `physics_labels.json` generation from ALL scripts (S1-S8)

## Changes per file

| File | Import removed | write_json removed | Notes |
|------|:-:|:-:|-------|
| generate_s1_dataset.py | ✅ | ✅ | |
| generate_s2_dataset.py | ✅ | ✅ | |
| generate_s3_dataset.py | ✅ | ✅ | |
| generate_s4_dataset.py | ✅ | ✅ | |
| generate_s5_dataset.py | ✅ | ✅ | |
| generate_s6_dataset.py | ✅ | ✅ | |
| generate_s7_dataset.py | ✅ | ✅ | |
| generate_s8_dataset.py | ❌ (kept) | ✅ | Import kept for negative sample filtering |

## S8 Filtering Dependency

S8 uses `compute_physics_labels()` internally to filter invalid negative samples:
```python
labels = compute_physics_labels(sample, frame_states, force_payloads, FPS)
if not labels.get("no_dynamic_collision", False):
    raise FilteredNegativeSample(...)
```
The import and function call MUST remain. Only the `write_json` line was removed.

## Why Other Code Cannot Be Deleted

Functions that look "physics-label related" but serve other outputs:
- `simulate_and_keyframe()` → returns `frame_states` (used by `object_dynamicjson`) and `force_payloads` (used by `force_matrix.json` and `resultant force`)
- `zero_force_matrix()`, `add_force()`, `average_force_matrix()` → build force data for `force_matrix.json`
- `level_name`, `subtask`, `main_variable` → written into `video.json`

## Rationale for Causal Learning

Pre-computed summary labels (stop_frame, travel_distance, is_static_at_end) are **outcomes**. Using them as model input causes label leakage — the model can shortcut causal reasoning. The model should learn from:
- Visual input: mp4, depth, segmentation masks
- Static properties: mass, friction, size, shape, color, restitution (from `object_static.json`)
- Dynamic trajectories: per-frame position, velocity, angular_velocity (from `object_dynamicjson`)
- Forces: per-frame force matrices (from `force_matrix.json`)
- Environment: gravity, fps, camera params (from `video.json`)

## Verification

All 8 scripts pass `ast.parse()` syntax check after modifications.
Docker containers started AFTER the modification correctly omit physics_labels.json from output.
Running containers are NOT affected by script changes (scripts loaded into memory at startup).
