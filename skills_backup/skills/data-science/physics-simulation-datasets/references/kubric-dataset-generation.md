---
name: kubric-dataset-generation
description: "Generate physics simulation video datasets using Kubric + PyBullet + Blender in Docker. Covers S1-S8 scene types, parameter configs, GPU rendering, and multi-container orchestration."
version: 1.0.0
tags: [kubric, pybullet, blender, dataset, physics-simulation, docker, gpu]
---

# Kubric Dataset Generation

Generate physics simulation video datasets using Kubric framework with PyBullet physics engine and Blender renderer, running inside Docker containers.

## Architecture

```
Parameter Config (task3) → Script (task6) → Docker (kubric-gpu) → Output (database/S{n}/)
```

- **Config source**: `task/task3-数据集详细构成/type/S{n}_场景名/参数配置.md`
- **Script source**: `task/task6-脚本编写/generate_s{n}_dataset.py`
- **Output**: `database/S{n}/L{level}/{sample_id}/`

## Scene Types (S1-S8)

| Scene | Name | Levels | Views | Key Physics |
|-------|------|--------|-------|-------------|
| S1 | 落体 | 7 | 2 (front, top) | Free fall, projectile |
| S2 | 水平滑动 | 7 | 3 (front, top, left) | Friction, sliding |
| S3 | 斜面滑动 | 9 | 3 (front, top, left) | Incline, ramp physics |
| S4 | 墙面反弹 | 9 | 2 (front, top) | Wall bounce, restitution |
| S5 | 球撞球 | 9 | 5 (front, back, left, right, top) | Ball-ball collision |
| S6 | 球撞方块 | 9 | 5 (front, back, left, right, top) | Ball-cube collision |
| S7 | 三物体连锁 | 12 | 5 | Chain collision |
| S8 | 泛化样本 | 14 | 5 | Negative samples, no collision |

## Docker Run Command Template

```bash
docker run -d --gpus all \
  --name s{n}_dataset \
  --user $(id -u):$(id -g) \
  -e KUBRIC_USE_GPU=True \
  -e KUBRIC_GPU_BACKEND=OPTIX \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "/home/lzy/project/slot-datamaking:/workspace" \
  -v "/home/lzy/project/slot-datamaking/kubric:/kubric" \
  -w /workspace \
  kubric-gpu \
  task/task6-脚本编写/generate_s{n}_dataset.py --levels {levels}
```

## Isaac Lab Migration

User is exploring migration from Kubric/PyBullet to Isaac Lab (PhysX 5 + RTX rendering). Key references:
- `references/pybullet-to-physx5-mapping.md` — detailed parameter mapping
- `references/slotformer-isaac-lab-notes.md` — SlotFormer pipeline (128×128 resolution, 2 core models), Isaac Lab hardware requirements (16GB VRAM min), PhysX 5 config classes

Migration risks: rollingFriction has no PhysX equivalent (affects S2/S7), ramp primitive not built-in (affects S3), quaternion convention differs (wxyz vs xyzw). Current dataset (31,880 videos, S1-S8) is complete and working on Kubric. User's RTX 4060 8GB is below Isaac Lab's 16GB VRAM minimum.

## Key Environment Variables

- `KUBRIC_USE_GPU=True` — Enable GPU rendering
- `KUBRIC_GPU_BACKEND=OPTIX` — Use OptiX backend (fallback: `CUDA`)
- `PYTHONDONTWRITEBYTECODE=1` — Prevent `__pycache__` conflicts between parallel containers

## Parallel Execution

- Different S scenes can run in parallel (write to different output dirs)
- Each container needs unique `--name`
- **CPU is the bottleneck, not GPU** — PyBullet physics is CPU-intensive; Blender rendering at 128x128 is lightweight. On RTX 4060 8GB: GPU shows 0% utilization, ~42MiB VRAM. S1 container uses ~188% CPU (~2 cores) and ~1.8GB RAM. Multiple containers share the GPU trivially.
- GPU memory barely used (~42MiB per Blender instance at 128x128, negligible at any resolution due to CPU fallback in WSL2 Docker)
- GPU memory barely used (~116MB per Blender instance at 128x128)
- Each container uses ~1-2GB RAM and 1-7 CPU cores depending on scene complexity
- Monitor with `docker logs -f s{n}_dataset`
- **Docker containers load scripts at startup** — modifying host scripts while containers are running does NOT affect them. Changes take effect on next container start.

### Queue Scheduler for S5-S8

When running multiple scenes with limited slots, use a queue scheduler:
- Script: `~/.hermes/scripts/scene_scheduler.sh`
- Queue file: `~/.hermes/scripts/scene_queue.txt` (one task per line: `name scene levels_args`)
- Cron: every 30 minutes via Hermes cronjob (`no_agent=true`, `script=bash .../scene_scheduler.sh`)
- Logic: count `_dataset` containers, if <2 start next from queue, skip if container name already exists
- Self-destruct: when queue empties, script removes its own cronjob + deletes itself + deletes queue file. See `references/self-destructing-cronjob.md` for the pattern.
- Cronjob ID is hardcoded in the script — update if recreated.
- Lock: `flock` prevents concurrent execution

Key design decisions:
- `read` queue head first, then `sed -i '1d'` to remove — avoid reading while modifying the file
- `grep -x` for exact container name match (not substring)
- `docker run` output goes to log file, not stdout
- One container per invocation (break after start), next one on next cron tick

## Checking Progress

```bash
# Container status
docker ps

# Task progress
docker logs s{n}_dataset --tail 5

# GPU usage
/usr/lib/wsl/lib/nvidia-smi
```

## Pitfalls

8. **Resolution affects rendering time exponentially** — The `--resolution` parameter (default: 128) controls output image/video dimensions. Higher resolutions are dramatically slower:
   - 128×128 — baseline speed, ~1-2 min per sample
   - 480×480 — ~8x slower than 128
   - 720×720 — ~15-30x slower than 128. On RTX 4060 (16 cores), S1 (800 samples, L1-L5=100, L6-L7=150) takes ~33 hours
   - Also increases output file sizes proportionally (mp4, npz, png frames)
   - GPU memory usage also increases with resolution
   - When regenerating at higher resolution, use `--output_root` to avoid overwriting existing 128p data

8c. **GPU is essentially idle during Kubric runs** — PyBullet physics simulation is 100% CPU. Blender rendering at 128×128 is so light that GPU utilization stays at 0% with only ~42MiB VRAM. This is NOT a bug — it means:
   - Multiple containers can run in parallel without GPU contention
   - CPU cores (not GPU) are the real bottleneck
   - Checking GPU utilization is not useful for monitoring progress; use `docker stats` for CPU% instead
   - Even at 720×720, GPU usage remains minimal because Blender's CPU fallback is being used (OPTIX often silently falls back to CPU in WSL2 Docker — see `kubric-gpu-docker` skill)

8b. **Kubric API — copy existing patterns, don't guess** — When writing new Kubric scripts, ALWAYS read existing S1-S8 scripts first and copy the exact API patterns. Kubric's Python API differs from standard conventions:
   - `kb.Sphere(scale=R)` — NOT `radius=R`
   - `kb.Cube(scale=(x/2, y/2, z/2))` — scale is half-extents, NOT full dimensions
   - No `background_friction` / `background_restitution` kwargs on objects — these raise `KeyError`
   - `simulator.run(frame_start=0, frame_end=N-1)` — NOT `run(duration=..., dynamic_objects=...)`
   - Physics properties (friction, restitution) set via `simulator._physics_client.changeDynamics(body_id, -1, lateralFriction=..., ...)` AFTER simulator creates the bodies
   - `imageio_ffmpeg` is NOT installed in `kubricdockerhub/kubruntu` — use `ffmpeg` CLI for video assembly
   - `imageio.get_writer()` will fail with `ImportError: imageio_ffmpeg` — save frames as PNG first, then `ffmpeg -framerate FPS -i frames/%04d.png -c:v libx264 -pix_fmt yuv420p video.mp4`
   - Blender rendering at 480×480 is ~8x slower than 128×128 — use `samples_per_pixel=4` for demos, `32` for production

9. **Don't assume view count** — Each scene has different view configs. Check the parameter config doc, not assumptions. S1=2 views, S2=3 views, S5-S8=5 views.

2. **Don't modify parameters without asking** — User is very protective of existing data and parameters. Always confirm before modifying script arguments, view configs, or level selections. NEVER run with `--overwrite` on existing data without explicit permission. Use `--output_root` to redirect test outputs to a separate directory instead.

2b. **Use `--output_root` for test runs** — When testing new resolutions or parameters, ALWAYS use `--output_root <new_dir>` to avoid touching existing data. Example: `--output_root database1l`. Never assume it's OK to overwrite `database/` data.

2e. **Default `--output_root` is `database1`, NOT `database`** — The script's `--output_root` defaults to `database1`, so running without this flag writes to `database1/S{n}/`, NOT `database/S{n}/`. The original data lives in `database/`. If the user wants to regenerate into `database/`, they must explicitly pass `--output_root database`. Always check which directory the user intends before launching.

2c. **Read existing run commands first** — The user maintains run commands at `task/task7-数据集/运行命令.md`. Read this file before constructing Docker commands. Use the exact same Docker image, volume mounts, and env vars. Don't use `kubricdockerhub/kubruntu` when `kubric-gpu` is specified.

2d. **Copy existing scripts, don't write from scratch** — When creating new Kubric scripts, ALWAYS read existing S1-S8 scripts first and copy the exact patterns. The user explicitly said "抄都抄不明白吗" (can't even copy properly?) when I kept making API mistakes by writing from memory. The correct approach: read the existing script, extract the relevant functions, adapt minimally.

3. **OPTIX fallback** — If `KUBRIC_GPU_BACKEND=OPTIX` errors, change to `KUBRIC_GPU_BACKEND=CUDA`.

4. **Container name conflicts** — If same-name container exists, either `docker rm` the stopped one or use a new name.

5. **__pycache__ conflicts** — Always set `PYTHONDONTWRITEBYTECODE=1` when running multiple containers that share script directories.

6. **NEVER combine `--restart` with `--overwrite`** — `--restart unless-stopped` + `--overwrite` creates an infinite loop: script finishes → container exits → restart policy relaunches → `--overwrite` re-runs from scratch → wastes compute and corrupts good data. Use one or the other:
   - `--restart unless-stopped` WITHOUT `--overwrite` — for crash recovery on first run
   - `--overwrite` WITHOUT `--restart` — for intentional regeneration
   - Neither — for one-shot runs

7. **Don't blindly restart completed containers** — If a container finished and you `docker start` it with `--overwrite`, it will re-run from scratch. Always check if data is complete before restarting.

### Patching Missing or Corrupt Samples

When individual samples are missing or empty (e.g., interrupted `--overwrite` run), write a small recovery script instead of re-running the full scene script:

1. **Identify the physical sample index**: sample_id ÷ views_per_sample → which physical sample it is
2. **Write a narrow script** in `task/task6-脚本编写/` that imports the original generator, calls `take_samples()` with the same seed, selects the target physical sample, and calls `generate_physical_sample()` with only the missing views
3. **Key requirement**: the script must add `_SCRIPT_DIR` to `sys.path` before importing the original module — Codex often forgets this
4. **Verify**: check `video.json` `cameras.view_name` confirms correct view, compare `dynamic/1/object_dynamicjson/` positions across patched and existing samples to confirm same physical configuration

Example: `generate_s3_l3_17_18.py` patched S3/L3 samples 17 (top) and 18 (left) by importing `generate_s3_dataset` and rendering only those two views of physical sample 6.

## Output Structure

```
database/S{n}/L{level}/{sample_id}/
├── {sample_id}.mp4          # Video
├── {sample_id}.npz          # Depth data (float32, meters)
├── video.json               # Video metadata
├── object_static.json       # Static object properties
├── dynamic/
│   └── {frame_num}/
│       ├── {frame_num}.png  # Frame image
│       ├── force_matrix.json
│       ├── object_dynamicjson/
│       │   └── {object_id}.json
│       └── object_segment/
│           └── {object_id}.npz
└── _scratch/                # Temporary (can delete)
```

**Note**: `physics_labels.json` was removed from ALL S1-S8 scripts (import + write_json lines deleted). It was a summary of per-frame data (travel_distance, stop_frame, contact_pair_sequence, etc.) that's redundant with the raw trajectory data. For causal learning, models should learn from raw trajectories, not pre-computed outcomes — pre-computed labels risk leaking causal information. S8's `no_dynamic_collision` filtering still works internally (compute_physics_labels import kept for that purpose only, no file written). The utility file `physics_label_utils.py` is preserved for potential offline evaluation use.

## Dataset Completion Status (2025-05-26)

S1-S8 all complete. Total: **31,880 videos**.

| Scene | Videos | Status |
|-------|--------|--------|
| S1 | 1,600 | ✅ |
| S2 | 2,040 | ✅ |
| S3 | 2,640 | ✅ |
| S4 | 2,200 | ✅ |
| S5 | 4,400 | ✅ |
| S6 | 4,400 | ✅ |
| S7 | 6,200 | ✅ |
| S8 | 8,400 | ✅ |

### HF Upload Pipeline

Upload script: `upload_to_hf.sh` in project root. Uses git-lfs with pipeline pattern:
- Packs tar.gz files sequentially (pigz -1 for speed)
- Uploads each tar to `craze-sheep/slot-datamaking-{s1..s8}` repos
- Pipeline: pack S(n+1) while uploading S(n)
- State tracking: `.hf_upload_state/completed.txt`
- Progress: `.hf_upload_state/{slot}.lfs-progress.log`
- Tars: `tars/{S1..S8}.tar.gz`
- Proxy: `http://127.0.0.1:7897` (configurable via `HF_GIT_PROXY`)

Monitoring:
```bash
# Check completed slots
cat .hf_upload_state/completed.txt

# Check tar packing progress
ls -lh tars/

# Check upload progress
tail -1 .hf_upload_state/*.lfs-progress.log

# Check process tree
pstree -p $(pgrep -f upload_to_hf.sh | head -1)
```

### Depth Map Behavior

Blender's depth pass returns ~1e10 meters for background/sky pixels. This is Kubric's documented sentinel value (`blender_utils.py:324`). Foreground depth is typically 5-16m. Use `depth < 1e9` to filter. Background pixel ratio: ~63% for perspective cameras with small scenes. See `dataset-validation` or `physics-sim-dataset-validation` skills for detailed validation.
