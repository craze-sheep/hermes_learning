---
name: batch-script-generation
description: Generate multiple similar scripts from a template + configuration docs. Used when you have one working script and need to create N variants with scene-specific logic.
tags: [code-generation, template, batch, python]
triggers:
  - "仿照/按照已有代码写N个类似的脚本"
  - "generate multiple similar scripts"
  - "batch code generation from template"
---

# Batch Script Generation from Template

Generate multiple similar Python scripts by transforming a template script and injecting scene-specific configuration.

## Pattern

1. **Read template** — the existing working script (e.g., `generate_s1_dataset.py`)
2. **Read configs** — parameter docs for each variant (e.g., `task3/.../S2_*/参数配置.md`)
3. **Transform template** — string replacement for common fields, then inject scene-specific logic
4. **Verify** — `python3 -m py_compile` + programmatic parameter checks

## Step-by-step

### 1. Base transformations (string replacement)
```python
code = template.replace('SCENE_ID = 1', 'SCENE_ID = 2')
code = code.replace('S1:', 'S2:')
code = code.replace('build_s1_stratified_level_configs', 'build_s2_stratified_level_configs')
# ... etc for LEVEL_TARGETS, ground size, friction defaults, error messages
```

### 2. Add scene-specific functions
Insert new helper functions (e.g., `ramp_spec`, `wall_spec`) at the right position:
```python
insert_pos = code.find('def with_ids(')
code = code[:insert_pos] + new_functions + code[insert_pos:]
```

### 3. Replace level configuration function
The main scene-specific logic goes in `build_sX_stratified_level_configs()`:
- Extract old function boundaries
- Replace with new implementation based on config docs

### 4. Update build_asset for new object types
If new object types are needed (ramp, wall, obstacle), add to the type check:
```python
if spec.object_type in {"cube", "ground", "ramp", "wall"}:
```

### 5. Verify
```bash
python3 -m py_compile generate_sX_dataset.py
```

Programmatic checks:
- SCENE_ID correct
- LEVEL_TARGETS match config docs
- Function names correct
- VIEWS dict contains all required perspectives
- All required object types supported

## Pitfalls

- **delegate_task timeout**: For large batch jobs (7+ scripts), `delegate_task` often times out at 600s. Use `execute_code` with direct file I/O instead — it's faster and more reliable.
- **VIEWS dict incomplete**: When adding new camera perspectives (back, right, top), must add them to BOTH the `VIEWS` dict AND the `--views` default list.
- **Missing object types in build_asset**: New object types (cylinder, ramp, wall) must be added to the type dispatch in `build_asset()`, or rendering fails at runtime.
- **Quaternion for ramps**: Rotation around y-axis for incline: `quat = (cos(θ/2), 0, sin(θ/2), 0)` in Kubric [w,x,y,z] format.
- **Ground size varies per scene**: S2 uses 8x6, S3 uses 4x4, S4 uses 10x5, S7/S8 use 9x6. Don't keep the template default.
- **Friction defaults vary**: S1/S2 ground has friction, S4-S8 ground is frictionless (0.0). Check each config doc.
- **Kubric has NO native Cylinder class**: `kb.Cylinder()` does NOT exist in Kubric. Only `kb.Cube` and `kb.Sphere` are available. To simulate cylinders, use `kb.Cube` with appropriate scale, or use `FileBasedObject` with a cylinder mesh. The `build_asset()` function must handle this.
- **Output directory may differ from --output_root**: Docker volume mounts and script args may cause output to go to a different directory (e.g., `database/` instead of `task7-数据集/`). Always check actual output location with `find . -name "*.mp4" -newer <script>`.
- **Docker container monitoring**: Use `docker logs <container> --tail N` to check progress. Container name changes each run. Use `docker ps` to get current container.
- **Custom GPU Docker image**: User has a `kubric-gpu` Docker image (built from `kubric-docker/Dockerfile`) with Blender 3.6 + CUDA support. Use `--gpus all` flag to enable GPU rendering. Check GPU status with `/usr/lib/wsl/lib/nvidia-smi` inside container.
- **Output directory mismatch**: Docker volume mounts may cause output to go to `database/` instead of the script's `--output_root`. Always verify actual output path with `find . -name "*.mp4" -newer <script>` after a few samples.
- **Code review workflow**: Use `multi-agent-review` skill for comprehensive
  spec-vs-code verification. Launch Hermes + Claude Code + Codex in parallel
  with identical prompts, then cross-compare findings. Each catches different
  issues — the intersection is high-confidence.

## Verification checklist

After generating all scripts — see also `multi-agent-review` skill and its
`references/spec-compliance-checklist.md` for the full methodology:

1. `py_compile` all files
2. Check SCENE_ID matches filename
3. Check LEVEL_TARGETS sum matches config doc totals
4. Check VIEWS dict has all perspectives used in default list
5. Check build_asset supports all object types used in levels
6. Check function name matches `build_sX_stratified_level_configs`
7. **Color/material pools are actually varied** — not hardcoded to one color
8. **Level count matches doc** — count `if/elif level_id ==` vs doc section headers
9. **VIEWS dict syntax** — check closing braces aren't nesting keys (common copy-paste bug)
10. **Derived labels** — check if spec requires post-processing labels (often missed)
11. **Quaternion composition** — if spec says `ramp_quat * lying_quat`, verify multiplication is done
