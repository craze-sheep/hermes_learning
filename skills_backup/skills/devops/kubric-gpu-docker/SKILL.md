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

## Dataset Validation Checklist

After generating data, check:
1. Depth: `np.load(f)['depth']` — no values > 1e6 (unless perspective camera background)
2. Segment masks: non-overlapping, correct object count per frame
3. visible_area in dynamicjson matches mask pixel count
4. Dynamic objects actually move (position changes between frame 1 and 36)
5. Static objects don't move
6. Frame count = 36 for all samples
7. All file types present per sample (mp4, npz, video.json, object_static.json, dynamic/*)

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
