---
name: kubric-gpu-docker
description: Run Kubric physics simulation with GPU rendering in Docker on WSL2. Covers Blender 3.6 + CUDA, OpenEXR ABI conflict fix, Blender --python argv handling.
trigger:
  - kubric docker gpu rendering blender dataset generation
  - kubric blender 3.6 RTX 4060 Ada Lovelace
  - OpenEXR segfault kubric blender
  - blender background python kubric
tags: [kubric, blender, docker, gpu, rendering, cuda, wsl2]
---

# Kubric GPU Rendering in Docker

Run Kubric (Blender-based physics simulation) with GPU rendering in Docker on WSL2.

## Version Compatibility Matrix

| Blender | CUDA | RTX 4060 (sm_89) | Kubric API Compatible |
|---------|------|-------------------|-----------------------|
| 2.93    | 11.0 | ❌ No              | ✅ Yes (kubruntu)     |
| 3.0-3.6 | 12.1 | ✅ Yes             | ✅ Yes                |
| 4.0+    | 12.2+| ✅ Yes             | ❌ No (API breaks)    |

**Must use Blender 3.6 LTS** — only version supporting Ada Lovelace + kubric API.

## Blender 4.0+ Breaking Changes (do NOT use with kubric)

- `bpy.ops.import_scene.obj()` → `bpy.ops.wm.obj_import()`
- Principled BSDF: `Specular` → `Specular IOR Level`, `Transmission` → `Transmission Weight`, `Emission` → `Emission Color`
- `blender_obj.data.use_auto_smooth` removed in 4.1

## Critical Pitfall: OpenEXR pip Package

**DO NOT `pip install OpenEXR`** inside Blender 3.6 env. The pip package (3.4.x) statically links `Iex_3_1` symbols, conflicting with Blender 3.6's `Iex_3_0` → segfault:

```
OpenEXR.cpython-310-x86_64-linux-gnu.so: undefined symbol: _ZN7Iex_3_113throwErrnoExcERKSs
# crash: kubric/renderer/blender_utils.py get_render_layers_from_exr
```

**Fix**: Patch `kubric/renderer/blender_utils.py` — see `references/openexr-bpy-fallback.md`.

## Dockerfile Pattern

```dockerfile
FROM nvidia/cuda:12.2.0-base-ubuntu22.04
# Blender system deps + Blender 3.6.15 + pip deps (NO OpenEXR)
```

Use `.dockerignore` with `**` + `!entrypoint.sh` to avoid huge build context.

## Blender --python argv

```bash
blender --background --python script.py -- --levels 1
# sys.argv includes Blender's own args before --
```

Fix: `blender_argv_fix.py` imported before argparse. See `references/blender-argv-fix.md`.

## Kubric GPU

```bash
export KUBRIC_USE_GPU=True  # kubric/renderer/blender.py line 128
```

## WSL2 Memory

Blender + PyBullet peak ~2-3GB. Need ≥12GB memory + 4GB swap via `.wslconfig`.

## Critical Pitfall: Renderer Reuse Causes Depth Corruption

When a single `Blender` renderer instance is reused across multiple views (switching `scene.camera`), the depth pass does not properly reset. Result:

- **S1 (2 views: front, top)**: All odd IDs (front, 1st render) have corrupted depth (~1e10 values). All even IDs (top, 2nd render) are fine. 50% data loss.
- **S2 (3 views: front, top, left)**: Only the 2nd render (top) has correct depth. 67% data loss.

**Fix**: Create a new `Blender` renderer instance inside the view loop, and `unlink_renderer()` + `gc.collect()` after each view. All S1-S8 scripts already have this fix applied.

**Verification**: `depth.max() > 1e6` indicates corruption. Normal range is scene-dependent (typically 5-10m for kubric scenes).

## Critical Pitfall: Kubric Object Constructor API

Kubric `PhysicalObject` subclasses (Sphere, Cube, Cylinder) have specific constructor signatures. Getting them wrong causes silent failures (objects not rendering, not moving, or crashing).

**Sphere:**
```python
# CORRECT — scale is the radius (single float)
sphere = kb.Sphere(name="s", position=(x, y, z), scale=0.22, mass=1.0, velocity=(0,0,0), material=...)

# WRONG — radius= is NOT a valid kwarg
sphere = kb.Sphere(radius=0.22)  # KeyError: unknown trait
```

**Cube:**
```python
# CORRECT — scale is (half_x, half_y, half_z), size/2
size = (8.0, 6.0, 0.08)
cube = kb.Cube(name="g", position=(...), scale=tuple(v/2 for v in size), static=True, material=...)

# WRONG — background_friction/restitution are NOT constructor kwargs
cube = kb.Cube(background_friction=0.5)  # KeyError: unknown trait
```

**Valid kwargs for all PhysicalObject subclasses:**
- `name`, `position`, `quaternion`, `velocity`, `angular_velocity`
- `static` (bool, default False), `mass` (float, default 1.0)
- `friction` (float, default 0.5), `restitution` (float, default 0.5)
- `material` (kb.PrincipledBSDFMaterial), `segmentation_id` (int)

**Setting physics properties (friction/restitution per-object):**
Must be done via PyBullet `changeDynamics` AFTER simulator creates bodies:
```python
simulator = PyBullet(scene, scratch / "pybullet")
body_id = asset.linked_objects.get(simulator)
if body_id is not None:
    simulator._physics_client.changeDynamics(
        body_id, -1,
        lateralFriction=0.5, rollingFriction=0.01,
        spinningFriction=0.005, restitution=0.3,
    )
```

## Critical Pitfall: Renderer Must Be Created AFTER Simulation

The Kubric pipeline has a strict ordering requirement:

```
1. Build scene + add objects
2. Create PyBullet simulator + run simulation  ← keyframes stored on assets
3. Create Blender renderer                     ← renderer observers register here
4. replay_scene_keyframes(scene)               ← replays keyframes into Blender
5. renderer.render()                           ← Blender animates using keyframes
```

**If renderer is created BEFORE simulation**, the keyframe_insert calls during simulation don't trigger Blender's observer system → all frames render the same (final) position → objects appear static.

**replay_scene_keyframes function (copy from S1):**
```python
def replay_scene_keyframes(scene) -> None:
    for asset in scene.assets:
        keyframes = getattr(asset, "keyframes", None)
        if not keyframes:
            continue
        for member, frame_values in list(keyframes.items()):
            original = getattr(asset, member)
            try:
                for frame, value in sorted(list(frame_values.items())):
                    setattr(asset, member, value)
                    asset.keyframe_insert(member, frame)
            finally:
                setattr(asset, member, original)
```

## Critical Pitfall: Two Docker Images, Different Purposes

| Image | GPU | Use case | Video output |
|-------|-----|----------|-------------|
| `kubric-gpu` | ✅ `--gpus all` | Production dataset generation | Direct mp4 via imageio |
| `kubricdockerhub/kubruntu` | ❌ CPU only | Testing / debugging | No imageio-ffmpeg; save PNGs + ffmpeg |

When using `kubricdockerhub/kubruntu`, `imageio.get_writer(mp4)` fails with `No module named 'imageio_ffmpeg'`. Workaround: save frames as PNG, assemble with `ffmpeg` externally.

## Critical Pitfall: OPTIX Silent Fallback to CPU in WSL2 Docker

When running `kubric-gpu` with `KUBRIC_GPU_BACKEND=OPTIX` in WSL2 Docker, OPTIX may silently fail and Blender falls back to CPU rendering. Symptoms:

- `nvidia-smi` shows **0% GPU utilization** and **42MiB VRAM** (no rendering happening on GPU)
- Container runs for much longer than expected
- `docker exec <container> nvidia-smi` shows GPU is accessible but unused

This happens because WSL2's GPU passthrough doesn't fully support OPTIX in Docker containers. The container CAN see the GPU (nvidia-smi works), but Blender's OPTIX backend can't initialize it.

**Impact**: Rendering still works (CPU fallback), but is significantly slower:
- 128×128: fast enough that CPU fallback is barely noticeable
- 480×480: ~8x slower than GPU, but manageable
- 720×720: very slow with CPU, but completes

**Detection**: Check GPU utilization during rendering:
```bash
/usr/lib/wsl/lib/nvidia-smi  # Look for GPU-Util > 0% and memory usage > 100MiB
```

**Workarounds**:
1. Accept CPU rendering for 128×128 production data (fast enough)
2. For higher resolutions, use `--samples_per_pixel 4` instead of default 32
3. Run on bare metal Windows or Linux for true GPU rendering
4. Try `KUBRIC_GPU_BACKEND=CUDA` instead of OPTIX (may or may not help)

## Dataset Validation Checklist

After generating data, check:
1. Depth: `np.load(f)['depth']` — no values > 1e6 (unless perspective camera background)
2. Segment masks: non-overlapping, correct object count per frame
3. visible_area in dynamicjson matches mask pixel count
4. Dynamic objects actually move (position changes between frame 1 and 36)
5. Static objects don't move
6. Frame count = 36 for all samples
7. All file types present per sample (mp4, npz, video.json, object_static.json, dynamic/*)

## Critical Pitfall: Docker Run Command Format

The `kubric-gpu` image uses `/entrypoint.sh` which invokes Blender's `--python` flag. **Do NOT prefix the script path with `python3`** — the entrypoint passes arguments directly to `blender --background --python <script>`.

**Wrong** (will fail with "Python file /workspace/python3 could not be opened"):
```bash
docker run ... kubric-gpu python3 /workspace/scripts/generate_s3_dataset.py --levels 1 2 3
```

**Correct** (use script path relative to -w workdir):
```bash
docker run -d --gpus all \
  --name s3_dataset \
  --user $(id -u):$(id -g) \
  -e KUBRIC_USE_GPU=True \
  -e KUBRIC_GPU_BACKEND=OPTIX \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "/home/lzy/project/slot-datamaking:/workspace" \
  -v "/home/lzy/project/slot-datamaking/kubric:/kubric" \
  -w /workspace \
  kubric-gpu \
  task/task6-脚本编写/generate_s3_dataset.py --levels 1 2 3 4 5 6 7 8 9
```

The script path is relative to `-w /workspace`. The entrypoint.sh handles Python invocation via Blender.

## Docker Build Best Practices

- `.dockerignore` with `**` + `!entrypoint.sh` — avoids multi-GB build context
- Run long builds with `terminal(background=true, notify_on_complete=true)`
- First build downloads ~259MB Blender + ~200MB pip packages; subsequent builds use cache
- Build command: `cd kubric-docker && docker build -t kubric-gpu .`

## Workflow Preferences

- **Comprehensive analysis first**: Before attempting fixes, check ALL constraints (versions, compatibility, ABI). Don't try one-by-one.
- **Delegate long tasks**: Use subagents for builds, research, multi-file changes.
- **Check progress**: Don't blindly wait on long commands — poll periodically.
- **Investigate failures**: Always find root cause, don't just retry.

## Critical Pitfall: --restart + --overwrite = Infinite Loop

**NEVER combine `docker --restart unless-stopped` with `--overwrite` in dataset generation.**

When a script with `--overwrite` finishes, the container exits. The restart policy restarts it, and `--overwrite` causes it to re-run from scratch, overwriting all completed data. This creates an infinite loop that wastes compute and corrupts good data.

**Safe patterns:**
- `--restart unless-stopped` WITHOUT `--overwrite` — for crash recovery on first run
- `--overwrite` WITHOUT `--restart` — for intentional regeneration
- Neither — for one-shot runs where you manually manage lifecycle

**If you need crash recovery with --overwrite**, write a wrapper script that detects existing complete samples and skips them, rather than using Docker restart policy.

**Removing restart from running containers:**
```bash
docker update --restart=no <container_name>
```

## Running Multiple Containers Simultaneously

When running S1 + S2 (or more) in parallel, CPU is the bottleneck:

| Metric | One container | Two containers |
|--------|--------------|----------------|
| CPU | ~900% (9 cores) | ~1600% (16 cores, near max) |
| Memory | ~600MB | ~1.2GB |
| GPU | 0% (CPU rendering) | 0% |

**RTX 4060 Laptop + 16 cores + 9.7GB RAM**: can run 2 containers, but they compete for CPU. Each runs ~40% slower than solo. Monitor with:

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**Rule of thumb**: if total CPU% > 1500% on 16 cores, one container is being starved. Stop the less important one.

## Script Default Output Directory

The generate scripts default to `--output_root database1`, NOT `database/`. New 720p data goes to `database1/S{n}/`, separate from the original 128p data in `database/S{n}/`. Check the script's argparse defaults if unsure.

## Monitoring Dataset Generation Progress

When containers are running, get specific progress — not just "up 21 minutes":

```bash
# 1. Current activity (what's being generated right now)
docker logs --tail 5 <container> 2>&1

# 2. Per-level completion (count videos vs dirs)
for level in 1 2 3 4 5 6 7 8; do
  dir="/path/to/database/S{n}/L${level}"
  if [ -d "$dir" ]; then
    videos=$(ls "$dir"/*/*.mp4 2>/dev/null | wc -l)
    dirs=$(ls -d "$dir"/*/ 2>/dev/null | wc -l)
    echo "L${level}: ${videos} videos, ${dirs} dirs"
  else
    echo "L${level}: not started"
  fi
done

# 3. Resource usage (CPU is the bottleneck for PyBullet, not GPU)
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**Key signals:**
- `docker logs` shows "Generating S{n}/L{m} physical X as video dirs Y-Z" — X is current physical sample
- Each physical sample generates 3-5 videos (views). Total dirs = physical_samples × views_per_sample
- If videos < dirs, generation is in progress for that level
- CPU > 100% is normal (PyBullet is CPU-intensive, multi-threaded)
- Memory typically 400-600MB per container (not the bottleneck)
