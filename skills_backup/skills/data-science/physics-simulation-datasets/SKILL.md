---
name: physics-simulation-datasets
description: Use when generating, validating, repairing, or modeling Kubric/Blender/PyBullet physics simulation video datasets, including Docker/GPU setup, batch script generation, output QA, and downstream physics-informed video prediction.
tags: [physics, simulation, dataset, kubric, blender, pybullet, docker, validation, video-prediction]
---

# Physics Simulation Datasets

Umbrella workflow for physics simulation video datasets: design specs → generator scripts → Kubric/Blender/PyBullet Docker runs → output validation → repair/patching → downstream video prediction/modeling.

## When to Use

- User is working with Kubric/Blender/PyBullet datasets, S1-S8 scenes, or SlotFormer-style physical videos.
- Need to generate, resume, patch, or monitor dataset production containers.
- Need to validate depth maps, segment masks, dynamic JSON, force matrices, cross-view consistency, or file completeness.
- Need to turn one working script into many spec-driven variants.
- Need to design a physics-informed video prediction model using RGB/depth/masks/object states/forces.

## Lifecycle Map

1. **Spec and script generation** — read source specs first; copy existing working scripts instead of writing Kubric API calls from memory.
2. **Containerized execution** — run `kubric-gpu` with the project volume mounts and Blender entrypoint script path, not `python3 script.py`.
3. **Monitoring and recovery** — monitor `docker logs`, per-level mp4 counts, CPU/memory, and OOM signals; use narrow patch scripts for missing samples.
4. **Validation gate** — run phased file/JSON/npz/cross-view checks before calling data ready.
5. **Modeling** — catalog all modalities before selecting or extending a model; prefer extending an existing visual/object-centric model with physics/depth branches.

## Generation and Docker Rules

- Read existing run commands and generator scripts before constructing commands.
- Use `--output_root` for tests; never overwrite existing data without explicit user approval.
- Do **not** combine Docker `--restart unless-stopped` with generator `--overwrite`.
- `kubric-gpu` entrypoint expects the script path directly:
  ```bash
  docker run -d --gpus all --name s3_dataset \
    --user $(id -u):$(id -g) \
    -e KUBRIC_USE_GPU=True -e KUBRIC_GPU_BACKEND=OPTIX -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$PWD:/workspace" -v "$PWD/kubric:/kubric" -w /workspace \
    kubric-gpu task/task6-脚本编写/generate_s3_dataset.py --levels 1 2 3
  ```
- CPU is usually the bottleneck; Blender GPU utilization may be near zero in WSL2 Docker due to OPTIX fallback.
- For batch variants, transform a proven template, inject scene-specific functions, then verify via `py_compile` and parameter checks.

## Validation Gate

Validate in phases:

1. **File completeness** — expected root files plus `dynamic/{1..36}/` contents; file names are `{sample_id}.mp4` and `{sample_id}.npz`, not `1.mp4` for every directory.
2. **Metadata** — `video.json` frame/resolution/camera consistency; `object_static.json` actual keys (`object_type`, `radius`, `size`, `height`, `segmentation_id`).
3. **Depth** — shape/dtype/finite values; background sentinel around `1e10` is expected for perspective sky/background, so filter foreground with `depth < 1e9`.
4. **Segmentation** — binary masks, no overlap, `visible_area == mask.sum()`, object IDs match metadata.
5. **Physics plausibility** — no NaN/Inf, static objects stay static, dynamic trajectories match scenario intent, no unexplained ground penetration.
6. **Cross-view consistency** — consecutive IDs in the same physical event should share object/static/dynamic physics while camera-dependent render products differ.
7. **Root-cause zero masks** — classify as fallen/off-ground, out of FOV (handle orthographic top cameras), occluded, or embedded geometry; do not leave large unknown buckets.

## Known Pitfalls to Preserve

- **TYPE_MAP must match actual `object_type` values in `object_static.json`.** Always verify with:
  ```bash
  find database/ -name "object_static.json" | head -20 | xargs grep -h "object_type" | sort | uniq -c
  ```
  The slot-datamaking dataset has 7 types (ground, sphere, cube, cylinder, wall, ramp, obstacle) but the model code defined only 4 with wrong names (`box` instead of `cube`). This silently zeroed out one-hot encodings for most objects. When adding new object types, also update `attr_dim`, `NUM_TYPES`, and any downstream consumers of the type one-hot.

  **Fastest way to audit types: read the generation scripts, not the database.** Scanning `database/` with grep is slow (thousands of JSON files). Instead:
  ```bash
  for s in S1 S2 S3 S4 S5 S6 S7 S8; do
    script="task/task6-脚本编写/generate_${s,,}_dataset.py"
    echo "$s: $(grep -oP '(sphere|cube|cylinder|wall|ramp|obstacle)_spec\(' "$script" | sort | uniq -c | sort -rn | tr '\n' ' ')"
    echo "   LEVEL_TARGETS: $(grep 'LEVEL_TARGETS' "$script")"
  done
  ```
  Each `_spec(` call = 1 dynamic object per sample config. Wall/ramp/obstacle are static scene elements (always present in that level). Multiply by LEVEL_TARGETS to get total object instances.

  **Recommended 3-type unification (2026-06-01 decision):** Since ground, wall, ramp, obstacle are ALL `kb.Cube` in PyBullet (just different sizes and static=true), unify them:
  ```python
  TYPE_MAP = {'sphere': 0, 'cube': 1, 'cylinder': 2}
  NUM_TYPES = 3
  TYPE_ALIAS = {'ground': 'cube', 'box': 'cube', 'wall': 'cube', 'ramp': 'cube', 'obstacle': 'cube'}
  ```
  This reduces attr_dim from 14→13. The model distinguishes "stage elements" from "moving objects" via the `static` flag (attr index 8), not the type one-hot.

- **PyBullet object creation is non-obvious.** In `build_asset()` (generate scripts), the mapping is:
  ```python
  if spec.object_type in {"cube", "ground", "wall"}:
      return kb.Cube(scale=tuple(v/2 for v in spec.size), **kwargs)
  if spec.object_type == "sphere":
      return kb.Sphere(scale=spec.radius, **kwargs)
  if spec.object_type == "cylinder":
      return kb.Cylinder(scale=(r, r, h/2), **kwargs)
  ```
  So ground, wall, and obstacle are ALL `kb.Cube` (box shapes) — relabeling wall/obstacle as cube is physically correct since they're all rectangular rigid bodies differing only in size and static flag.
- Blender/Kubric background depth sentinel: `~1e10` is not automatically corruption.
- Reusing one renderer across views can corrupt depth; create/unlink a renderer per view when this appears.
- Kubric object constructors are non-obvious: `kb.Sphere(scale=radius)`, `kb.Cube(scale=half_extents)`; unsupported kwargs raise trait errors.
- Kubric has version/image-specific behavior around cylinders and video encoding; copy patterns from working scripts.
- OOM kills can leave empty directories, especially with `--rm`; check `dmesg -T`.
- Orthographic top view sees a bounded world-space square, not a perspective frustum.
- Embedded objects can be visible in RGB but all-zero in segmentation because the segmentation pass assigns the front-most surface.
- User may request analysis-only; in that mode, diagnose and report only.

## Downstream Modeling Pattern

Before architecture decisions, inspect every modality (`npz`, `object_static.json`, `object_dynamicjson`, `force_matrix.json`, masks, RGB). Existing models rarely use all modalities; usually extend a working object-centric video model:

- RGB/masks → visual slot features
- depth → depth encoder/auxiliary decoder
- object attributes + physical state → MLP conditioning
- force matrix → sparse edge features/GNN layer
- multi-task losses → RGB/depth/mask/physics/force consistency

## Dataset Train/Test Splitting

When splitting the dataset for training:

1. **Output location** — create `train/` and `test/` at the **project root** (e.g. `slot-datamaking/train/`), NOT inside `database/`. The database directory stays pristine.
2. **Use symlinks, not copies** — symlink each sample directory from `database/S{scene}/L{level}/{sample_id}` into `train/S{scene}/L{level}/{sample_id}`. Preserves directory hierarchy, zero extra disk, data access is transparent to all code.
3. **Split per level** — iterate each `S*/L*/` directory independently, shuffle samples with a fixed seed, split at the desired ratio (typically 80/20). Every level must maintain the exact ratio.
4. **Verification pitfall** — `ls -d "$dir"*/` does NOT reliably count symlinked directories. Always use `find "$dir" -maxdepth 1 -type l | wc -l` for accurate symlink counts.
5. **Also produce text lists** — write `train.txt` and `test.txt` inside `database/` with one absolute path per line, for scripts that prefer flat path lists over directory traversal.

```python
# Core splitting logic
import os, random
random.seed(42)
for scene_dir in sorted(scene_dirs):
    for level_dir in sorted(level_dirs):
        samples = [d for d in os.listdir(level_dir) if d.isdigit()]
        random.shuffle(samples)
        split_idx = int(len(samples) * 0.8)
        # symlink train[:split_idx] -> train/S/L/sample
        # symlink train[split_idx:] -> test/S/L/sample
```

## Related Skills

- **ml-model-evaluation** (research/) — For evaluating existing model architectures against mainstream approaches and writing optimization suggestions. Use when the model code already exists and needs architectural review.
- **ml-training-workflows** (mlops/) — For implementing training loops, OOM handling, loss calibration. Its `references/physics-object-graph-model.md` has a complete working example (PhysicsObjectGraphPredictor) trained on this dataset format.

## Support Files

Older narrow skills absorbed into this umbrella are preserved under `references/` with their original names. Load those file for detailed historical commands, scripts, and project-specific case studies.
