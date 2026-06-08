# Slot-Datamaking Dataset Audit Findings

## Date: 2026-06-01

## Issue Found
Data had 7 object types but code TYPE_MAP only defined 4. "cube" was written as "box" in code, and "wall", "ramp", "obstacle" were missing from TYPE_MAP.

## Actual Types in Database (31880 files, ~123630 objects)

| Type | Count | PyBullet Shape | static |
|------|-------|---------------|--------|
| sphere | 53429 | kb.Sphere | false |
| ground | 31880 | kb.Cube | true |
| cube | 15026 | kb.Cube | false |
| wall | 5750 | kb.Cube | true |
| cylinder | 2905 | kb.Cylinder | false |
| ramp | 2640 | kb.Cube | true |

## Decision Made
Unified all kb.Cube types under "cube" in TYPE_MAP, with static flag distinguishing moving cubes from static obstacles.

## Files Modified

### Data files
- database/S8/L5/*/object_static.json (600 files): obstacle → wall
- database/S8/L5/*/video.json (600 files): metadata strings updated

### Scripts
- task/task6-脚本编写/generate_s8_dataset.py: obstacle_spec → blocking_wall_spec, variable renames
- task/task6-脚本编写/physics_label_utils.py: removed "obstacle" from wall_contact_sequence
- task/task6-脚本编写/validate_s8_no_dynamic_collision.py: removed "obstacle"
- task/task4-参数可用性与视觉呈现/generate_parameter_visual_checks.py: BodySpec("obstacle" → "wall")

### Documentation
- task/task3-数据集详细构成/type/S8_泛化样本/参数配置.md
- task/task7-数据集/S&L.md
- task/task3-数据集详细构成/物体属性文档/参数详解.md

## Verification
```bash
# Run check script
python database/checkout/check_replace_object_types.py  # dry-run
```

## Max Objects
max_objects=7 is correct. S8 Level 1 has 6 dynamic + 1 ground = 7 objects max.
