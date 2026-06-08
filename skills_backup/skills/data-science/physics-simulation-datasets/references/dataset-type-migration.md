# Dataset Object Type Migration Pattern

When object_type labels in `object_static.json` don't match the spec, batch-fix both data and scripts.

## obstacle → wall Migration (2026-06-01)

**Problem:** `obstacle` type in S8/L5 data (600 samples) was not in the design spec. Both obstacle and wall are `kb.Cube` in PyBullet — same physical shape, just different sizes.

**Data fix** — batch sed on all JSON files:
```bash
cd database/S8/L5
for d in */; do
  f="$d/object_static.json"
  [ -f "$f" ] && sed -i 's/"object_type": "obstacle"/"object_type": "wall"/g' "$f"
done
```

**Script fixes** — all files referencing the old type:
1. `generate_s8_dataset.py`: Change `obstacle_spec()` function to output `object_type="wall"`, update metadata strings (`blocked_by_wall`), remove `"obstacle"` from `build_asset()` type set
2. `physics_label_utils.py`: Remove `"obstacle"` from `wall_contact_sequence` filter set
3. `validate_s8_no_dynamic_collision.py`: Remove `"obstacle"` from collision shape type set
4. `generate_parameter_visual_checks.py`: Change `BodySpec("obstacle", ...)` to `BodySpec("wall", ...)`

**Doc fixes:**
- `task/task3-数据集详细构成/type/S8_泛化样本/参数配置.md`
- `task/task7-数据集/S&L.md`

**Verification:**
```bash
grep -rn "obstacle" task/task6-脚本编写/*.py  # should only show function name + local var names
grep -rn "obstacle" database/  # should return 0 matches
```

## General Migration Checklist

When relabeling any object_type:
1. Batch sed the JSON files in `database/`
2. Update the `_spec()` function in the generator script
3. Update `build_asset()` type set
4. Update `physics_label_utils.py` filter sets
5. Update validation scripts
6. Update documentation (参数配置.md, S&L.md)
7. Delete dataset cache: `rm -f model/ai_model/dataset_cache_*.pkl`
8. If attr_dim changes, update config.py and retrain from scratch
