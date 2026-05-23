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

## Key Environment Variables

- `KUBRIC_USE_GPU=True` — Enable GPU rendering
- `KUBRIC_GPU_BACKEND=OPTIX` — Use OptiX backend (fallback: `CUDA`)
- `PYTHONDONTWRITEBYTECODE=1` — Prevent `__pycache__` conflicts between parallel containers

## Parallel Execution

- Different S scenes can run in parallel (write to different output dirs)
- Each container needs unique `--name`
- **CPU is the bottleneck, not GPU** — PyBullet physics is CPU-intensive; Blender rendering at 128x128 is lightweight
- On RTX 4060 8GB + 16 CPU cores: 2-3 containers can run in parallel
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

1. **Don't assume view count** — Each scene has different view configs. Check the parameter config doc, not assumptions. S1=2 views, S2=3 views, S5-S8=5 views.

2. **Don't modify parameters without asking** — User is sensitive about parameter changes. Always confirm before modifying script arguments, view configs, or level selections.

3. **OPTIX fallback** — If `KUBRIC_GPU_BACKEND=OPTIX` errors, change to `KUBRIC_GPU_BACKEND=CUDA`.

4. **Container name conflicts** — If same-name container exists, either `docker rm` the stopped one or use a new name.

5. **__pycache__ conflicts** — Always set `PYTHONDONTWRITEBYTECODE=1` when running multiple containers that share script directories.

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

### Depth Map Behavior

Blender's depth pass returns ~1e10 meters for background/sky pixels. This is Kubric's documented sentinel value (`blender_utils.py:324`). Foreground depth is typically 5-16m. Use `depth < 1e9` to filter. Background pixel ratio: ~63% for perspective cameras with small scenes. See `dataset-validation` or `physics-sim-dataset-validation` skills for detailed validation.
