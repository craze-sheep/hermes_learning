#!/usr/bin/env python3
"""Quick health check for physics simulation dataset directories.

Usage:
    python validate_dataset.py /path/to/database/S1 [S2 ...]
    python validate_dataset.py /path/to/database/S1/L1  # single level

Checks: file completeness, depth sanity, segment masks, physics plausibility.
Outputs a summary report with issue counts.
"""

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


DEPTH_MAX_REASONABLE = 100  # meters, for tabletop scenes
DEPTH_FAR_CLIP_SUSPECT = 1e6


def check_sample(sample_dir: Path, scene_id: str) -> list[str]:
    issues = []
    sid = sample_dir.name
    sample_label = f"{scene_id}/{sample_dir.parent.name}/{sid}"

    # --- Root files ---
    for f in [f"{sid}.mp4", f"{sid}.npz", "video.json", "object_static.json"]:
        if not (sample_dir / f).exists():
            issues.append(f"[MISSING] {sample_label}: {f}")

    # --- video.json ---
    vj_path = sample_dir / "video.json"
    if vj_path.exists():
        with open(vj_path) as f:
            vj = json.load(f)
        if vj.get("num_frames") != 36:
            issues.append(f"[META] {sample_label}: num_frames={vj.get('num_frames')}")
        cam = vj.get("cameras", [{}])[0]
        if cam.get("video_path") != f"{sid}.mp4":
            issues.append(f"[META] {sample_label}: video_path mismatch")
        if cam.get("depth_path") != f"{sid}.npz":
            issues.append(f"[META] {sample_label}: depth_path mismatch")

    # --- Depth ---
    npz_path = sample_dir / f"{sid}.npz"
    if npz_path.exists():
        d = np.load(npz_path)
        if "depth" in d:
            depth = d["depth"]
            if depth.ndim != 3:
                issues.append(f"[DEPTH] {sample_label}: ndim={depth.ndim}")
            if depth.dtype != np.float32:
                issues.append(f"[DEPTH] {sample_label}: dtype={depth.dtype}")
            if not np.isfinite(depth).all():
                issues.append(f"[DEPTH] {sample_label}: has NaN/Inf")
            if depth.max() > DEPTH_FAR_CLIP_SUSPECT:
                issues.append(f"[DEPTH] {sample_label}: max={depth.max():.2e} (far-clip bleed)")

    # --- object_static.json ---
    static_path = sample_dir / "object_static.json"
    if static_path.exists():
        with open(static_path) as f:
            statics = json.load(f)
        if not isinstance(statics, list) or len(statics) < 2:
            issues.append(f"[STATIC] {sample_label}: expected list with ≥2 objects")
        else:
            for o in statics:
                if o.get("object_id") != o.get("segmentation_id"):
                    issues.append(f"[STATIC] {sample_label}: object_id != seg_id")

    # --- Dynamic frames ---
    dyn_dir = sample_dir / "dynamic"
    if dyn_dir.exists():
        frame_dirs = sorted(dyn_dir.iterdir(), key=lambda p: int(p.name))
        if len(frame_dirs) != 36:
            issues.append(f"[FRAMES] {sample_label}: {len(frame_dirs)} frames (expected 36)")

        for fd in frame_dirs[:3]:  # spot-check first 3 frames
            fn = fd.name
            # PNG
            if not (fd / f"{fn}.png").exists():
                issues.append(f"[MISSING] {sample_label}/f{fn}: PNG")
            # force_matrix
            if not (fd / "force_matrix.json").exists():
                issues.append(f"[MISSING] {sample_label}/f{fn}: force_matrix.json")
            # segments
            seg_dir = fd / "object_segment"
            if seg_dir.exists():
                for npzf in seg_dir.glob("*.npz"):
                    s = np.load(npzf)
                    mask = s["mask"]
                    if mask.dtype != np.uint8 or set(np.unique(mask)) - {0, 1}:
                        issues.append(f"[SEG] {sample_label}/f{fn}/{npzf.name}: bad mask values")
            # dynamicjson
            dj_dir = fd / "object_dynamicjson"
            if dj_dir.exists():
                for jf in dj_dir.glob("*.json"):
                    with open(jf) as f:
                        d = json.load(f)
                    pos = d.get("position", [])
                    if any(np.isnan(v) or np.isinf(v) for v in pos):
                        issues.append(f"[PHYSICS] {sample_label}/f{fn}/{jf.name}: NaN/Inf in position")
    else:
        issues.append(f"[MISSING] {sample_label}: dynamic/ directory")

    return issues


def check_level(level_dir: Path, scene_id: str) -> dict:
    all_issues = []
    sample_count = 0
    depth_bad = 0

    for sid_dir in sorted(level_dir.iterdir(), key=lambda p: int(p.name) if p.name.isdigit() else 0):
        if not sid_dir.is_dir():
            continue
        sample_count += 1
        issues = check_sample(sid_dir, scene_id)
        all_issues.extend(issues)
        if any("[DEPTH]" in i and "far-clip" in i for i in issues):
            depth_bad += 1

    return {
        "level": level_dir.name,
        "samples": sample_count,
        "depth_bad": depth_bad,
        "issues": all_issues,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_dataset.py <path> [path2 ...]")
        sys.exit(1)

    total_issues = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"SKIP: {p} does not exist")
            continue

        scene_id = p.name  # e.g. S1, S2

        # Determine if this is a scene dir (has L* subdirs) or a level dir
        subdirs = [d for d in p.iterdir() if d.is_dir()]
        is_scene = any(d.name.startswith("L") for d in subdirs)

        if is_scene:
            print(f"\n{'='*50}")
            print(f"Scene: {scene_id}")
            print(f"{'='*50}")
            for level_dir in sorted(subdirs, key=lambda d: d.name):
                if not level_dir.name.startswith("L"):
                    continue
                result = check_level(level_dir, scene_id)
                issue_count = len(result["issues"])
                print(f"  {result['level']}: {result['samples']} samples, "
                      f"depth_bad={result['depth_bad']}, issues={issue_count}")
                for issue in result["issues"][:5]:
                    print(f"    {issue}")
                if issue_count > 5:
                    print(f"    ... and {issue_count - 5} more")
                total_issues.extend(result["issues"])
        else:
            # Single level
            result = check_level(p, scene_id)
            for issue in result["issues"]:
                print(issue)
            total_issues.extend(result["issues"])

    print(f"\n{'='*50}")
    print(f"Total issues: {len(total_issues)}")
    issue_types = Counter(i.split("]")[0] + "]" for i in total_issues)
    for itype, count in issue_types.most_common():
        print(f"  {itype}: {count}")


if __name__ == "__main__":
    main()
