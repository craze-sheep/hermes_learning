#!/usr/bin/env python3
"""Validate Kubric/Blender physics simulation dataset.

Usage:
    python validate_dataset.py /path/to/database/S1
    python validate_dataset.py /path/to/database/S1 --threshold 100 --check-overlay

Checks:
    1. File structure completeness
    2. Depth map sanity (range, inf/nan, far-plane artifacts)
    3. Segment mask integrity (shape, values, overlap, frame_num)
    4. Cross-field consistency (video.json vs npz dimensions)
    5. ID-correlated corruption patterns
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np


def validate_sample(sample_dir, threshold=100, verbose=False):
    """Validate a single sample directory. Returns list of issues."""
    issues = []
    sid = os.path.basename(sample_dir)

    # 1. Check required files
    npz_path = os.path.join(sample_dir, f"{sid}.npz")
    mp4_path = os.path.join(sample_dir, f"{sid}.mp4")
    vid_path = os.path.join(sample_dir, "video.json")
    static_path = os.path.join(sample_dir, "object_static.json")

    for path, name in [(npz_path, "depth npz"), (mp4_path, "mp4"),
                        (vid_path, "video.json"), (static_path, "object_static.json")]:
        if not os.path.exists(path):
            issues.append(f"MISSING: {name}")

    if not os.path.exists(npz_path):
        return issues

    # 2. Depth map
    try:
        d = np.load(npz_path)
        depth = d['depth']
        if np.isinf(depth).sum() > 0:
            issues.append(f"DEPTH_INF: {np.isinf(depth).sum()} inf pixels")
        if np.isnan(depth).sum() > 0:
            issues.append(f"DEPTH_NAN: {np.isnan(depth).sum()} nan pixels")
        if depth.max() > threshold:
            issues.append(f"DEPTH_CORRUPTED: max={depth.max():.2e}, "
                         f"corrupted_pixels={(depth > threshold).sum()}/{depth.size}")
    except Exception as e:
        issues.append(f"DEPTH_LOAD_ERROR: {e}")
        return issues

    # 3. video.json consistency
    if os.path.exists(vid_path):
        try:
            with open(vid_path) as f:
                vid = json.load(f)
            if vid.get('num_frames') != depth.shape[0]:
                issues.append(f"FRAME_MISMATCH: video.json says {vid['num_frames']}, "
                             f"depth has {depth.shape[0]}")
            res = vid.get('cameras', [{}])[0].get('resolution', [])
            if res and (res[0] != depth.shape[1] or res[1] != depth.shape[2]):
                issues.append(f"RESOLUTION_MISMATCH: video.json says {res}, "
                             f"depth is {depth.shape[1]}x{depth.shape[2]}")
        except Exception as e:
            issues.append(f"VIDEO_JSON_ERROR: {e}")

    # 4. Object static
    num_objects = 0
    if os.path.exists(static_path):
        try:
            with open(static_path) as f:
                static = json.load(f)
            num_objects = len(static)
        except Exception as e:
            issues.append(f"STATIC_JSON_ERROR: {e}")

    # 5. Check dynamic frames
    dyn_dir = os.path.join(sample_dir, "dynamic")
    if os.path.exists(dyn_dir):
        frames = sorted(os.listdir(dyn_dir), key=lambda x: int(x) if x.isdigit() else 0)
        if len(frames) != depth.shape[0]:
            issues.append(f"DYNAMIC_MISMATCH: {len(frames)} frame dirs vs "
                         f"{depth.shape[0]} depth frames")

        # Spot-check first and last frame
        for fidx in [frames[0], frames[-1]] if frames else []:
            seg_dir = os.path.join(dyn_dir, fidx, "object_segment")
            if os.path.exists(seg_dir):
                seg_files = os.listdir(seg_dir)
                if num_objects and len(seg_files) != num_objects:
                    issues.append(f"SEG_COUNT_MISMATCH: frame {fidx} has {len(seg_files)} "
                                 f"segments, expected {num_objects}")

                for sf in seg_files:
                    try:
                        seg = np.load(os.path.join(seg_dir, sf))
                        if seg['mask'].shape != (depth.shape[1], depth.shape[2]):
                            issues.append(f"SEG_SHAPE_MISMATCH: {sf} in frame {fidx}")
                        if set(np.unique(seg['mask'])) - {0, 1}:
                            issues.append(f"SEG_INVALID_VALUES: {sf} in frame {fidx}")
                        if int(seg['frame_num']) != int(fidx):
                            issues.append(f"SEG_FRAME_NUM_MISMATCH: {sf} says "
                                         f"frame_num={seg['frame_num']}, dir={fidx}")
                    except Exception as e:
                        issues.append(f"SEG_LOAD_ERROR: {sf} in frame {fidx}: {e}")

                # Check mask overlap
                if len(seg_files) >= 2:
                    masks = []
                    for sf in seg_files:
                        masks.append(np.load(os.path.join(seg_dir, sf))['mask'])
                    for i in range(len(masks)):
                        for j in range(i+1, len(masks)):
                            overlap = np.logical_and(masks[i], masks[j])
                            if overlap.sum() > 0:
                                issues.append(f"SEG_OVERLAP: objects {i} & {j} in frame {fidx}")

    return issues


def check_id_pattern(results):
    """Check for ID-correlated corruption patterns."""
    bad_ids = []
    good_ids = []
    for sid, issues in results.items():
        if any('DEPTH_CORRUPTED' in i for i in issues):
            bad_ids.append(int(sid))
        else:
            good_ids.append(int(sid))

    if not bad_ids:
        return None

    patterns = []
    # Check odd/even
    odd_bad = sum(1 for i in bad_ids if i % 2 == 1)
    even_bad = sum(1 for i in bad_ids if i % 2 == 0)
    if odd_bad == len(bad_ids) and even_bad == 0:
        patterns.append("ALL odd IDs corrupted, ALL even IDs normal")
    elif even_bad == len(bad_ids) and odd_bad == 0:
        patterns.append("ALL even IDs corrupted, ALL odd IDs normal")

    # Check mod 3
    for mod in range(2, 6):
        bad_mods = Counter(i % mod for i in bad_ids)
        good_mods = Counter(i % mod for i in good_ids)
        if len(good_mods) == 1:
            good_remainder = list(good_mods.keys())[0]
            patterns.append(f"Only id%{mod}=={good_remainder} samples are normal "
                          f"({len(good_ids)}/{len(good_ids)+len(bad_ids)})")

    return patterns if patterns else None


def main():
    parser = argparse.ArgumentParser(description="Validate Kubric physics simulation dataset")
    parser.add_argument("dataset_path", help="Path to scenario dir (e.g., database/S1)")
    parser.add_argument("--threshold", type=float, default=100,
                       help="Max reasonable depth in meters (default: 100)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    base = args.dataset_path
    if not os.path.isdir(base):
        print(f"Error: {base} is not a directory")
        sys.exit(1)

    all_results = {}
    stats = {'total': 0, 'ok': 0, 'issues': 0, 'depth_corrupted': 0}

    print(f"Validating: {base}")
    print("=" * 60)

    for lvl in sorted(os.listdir(base)):
        lvl_path = os.path.join(base, lvl)
        if not os.path.isdir(lvl_path):
            continue

        lvl_results = {}
        for sid in sorted(os.listdir(lvl_path), key=lambda x: int(x) if x.isdigit() else 0):
            sample_path = os.path.join(lvl_path, sid)
            if not os.path.isdir(sample_path):
                continue

            stats['total'] += 1
            issues = validate_sample(sample_path, threshold=args.threshold,
                                     verbose=args.verbose)
            all_results[sid] = issues
            lvl_results[sid] = issues

            if issues:
                stats['issues'] += 1
                if any('DEPTH_CORRUPTED' in i for i in issues):
                    stats['depth_corrupted'] += 1
                if args.verbose:
                    print(f"  {lvl}/{sid}: {', '.join(issues)}")
            else:
                stats['ok'] += 1

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"  Total samples:     {stats['total']}")
    print(f"  OK:                {stats['ok']} ({stats['ok']/max(stats['total'],1)*100:.1f}%)")
    print(f"  With issues:       {stats['issues']} ({stats['issues']/max(stats['total'],1)*100:.1f}%)")
    print(f"  Depth corrupted:   {stats['depth_corrupted']} ({stats['depth_corrupted']/max(stats['total'],1)*100:.1f}%)")

    # Check for ID patterns
    patterns = check_id_pattern(all_results)
    if patterns:
        print(f"\nID-CORRELATED PATTERNS DETECTED:")
        for p in patterns:
            print(f"  ! {p}")


if __name__ == "__main__":
    main()
