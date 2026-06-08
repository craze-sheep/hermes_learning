---
name: dataset-auditing
description: Audit dataset consistency against code definitions — find type mismatches, missing labels, schema differences, and fix across all related files (scripts, data, docs).
triggers:
  - "check if data matches code"
  - "audit dataset types"
  - "data type mismatch"
  - "verify data consistency"
  - "fix data labels"
---

# Dataset Auditing

Workflow for finding and fixing inconsistencies between dataset files and code definitions.

## When to Use
- User asks to verify data types/labels match code
- Training shows unexpected behavior (e.g., features always zero)
- Adding new data that might not match existing schema
- After data generation scripts change

## Audit Workflow

### Step 1: Discover Actual Data Types
```bash
# Find all unique object_type values in database
find database/ -name "object_static.json" -exec grep -h "object_type" {} \; | sort | uniq -c | sort -rn

# Or faster: sample from each scene
for s in S1 S2 S3 S4 S5 S6 S7 S8; do
  find database/$s -name "object_static.json" -maxdepth 3 | head -5 | xargs grep -h "object_type" | sort -u
done
```

### Step 2: Compare Against Code Definitions
```bash
# Find TYPE_MAP or similar definitions
grep -rn "TYPE_MAP\|object_type" model/ --include="*.py"

# Check what types scripts actually generate
for s in s1 s2 s3 s4 s5 s6 s7 s8; do
  script="task/task6-脚本编写/generate_${s}_dataset.py"
  grep -oP 'object_type="[^"]*"' "$script" | sort -u
done
```

### Step 3: Identify Mismatches
Common issues:
- Code uses different name than data (e.g., "box" vs "cube")
- Types exist in data but missing from TYPE_MAP
- Types defined in code but never generated
- Schema differences (different JSON keys)

### Step 4: Verify JSON Schema Consistency
```python
# Check if all types have same JSON structure
import json, glob
for f in glob.glob('database/S*/L1/*/object_static.json'):
    data = json.load(open(f))
    for o in data:
        print(o['object_type'], sorted(o.keys()))
```

### Step 5: Fix Across ALL Related Files
When fixing type mismatches, update ALL of these:

1. **Data files** (object_static.json, video.json)
   ```bash
   # Batch replace in data files
   for d in database/S8/L5/*/; do
     f="$d/object_static.json"
     [ -f "$f" ] && sed -i 's/"old_type"/"new_type"/g' "$f"
   done
   ```

2. **Generation scripts** (generate_*_dataset.py)
   - Update TYPE_MAP
   - Rename spec functions if needed
   - Update metadata strings in make_cfg()

3. **Utility scripts** (physics_label_utils.py, validate_*.py)
   - Update type sets in conditionals

4. **Documentation** (*.md files in task/)
   - Update parameter docs
   - Update scene descriptions

5. **Verification scripts** (check_replace_object_types.py)
   - Add new replacement rules

### Step 6: Run Verification Script
```bash
# If exists, run the check script
python database/checkout/check_replace_object_types.py  # dry-run
python database/checkout/check_replace_object_types.py --apply  # apply
```

## Pitfalls
- **Don't forget video.json**: Contains metadata with type names in level_name, subtask, main_variable fields
- **Check all scenes**: Type might only appear in specific scenes (e.g., obstacle only in S8/L5)
- **Rename functions too**: If renaming a type, also rename the spec function (e.g., obstacle_spec → blocking_wall_spec)
- **Variable names**: Local variable names (obstacle_sizes, etc.) should also be renamed for consistency
- **max_objects verification**: After adding/removing types, verify max_objects is still correct by checking generation scripts

## User Preferences (lzy)
- Always include relevant file paths in responses
- When making changes, update ALL related files (scripts, data, docs)
- Be concise - output content for user to write, don't over-explain
- Verify changes after making them
- Use Chinese for explanations when user writes in Chinese
