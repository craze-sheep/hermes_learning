#!/usr/bin/env python3
"""Split a hierarchical dataset (S{scene}/L{level}/{sample_id}/) into train/test.

Key design:
  - Stratified: each level gets its own 80/20 split (no level is over/under-represented)
  - Reproducible: fixed seed
  - Outputs: train.txt, test.txt (absolute paths, one per line) + split_stats.txt

Adapt DB_ROOT, TRAIN_RATIO, SEED for your project.
"""

import os
import random

DB_ROOT = os.path.dirname(os.path.abspath(__file__))
TRAIN_RATIO = 0.8
SEED = 42

random.seed(SEED)

train_paths = []
test_paths = []
stats = []

for scene in sorted(os.listdir(DB_ROOT)):
    scene_dir = os.path.join(DB_ROOT, scene)
    if not os.path.isdir(scene_dir) or not scene.startswith("S"):
        continue
    for level in sorted(os.listdir(scene_dir), key=lambda x: int(x[1:])):
        level_dir = os.path.join(scene_dir, level)
        if not os.path.isdir(level_dir) or not level.startswith("L"):
            continue
        samples = sorted(
            [d for d in os.listdir(level_dir)
             if os.path.isdir(os.path.join(level_dir, d)) and d.isdigit()],
            key=int,
        )
        n = len(samples)
        if n == 0:
            continue
        random.shuffle(samples)
        split_idx = int(n * TRAIN_RATIO)
        train = samples[:split_idx]
        test = samples[split_idx:]
        for s in train:
            train_paths.append(os.path.join(level_dir, s))
        for s in test:
            test_paths.append(os.path.join(level_dir, s))
        stats.append((scene, level, n, len(train), len(test)))

with open(os.path.join(DB_ROOT, "train.txt"), "w") as f:
    f.write("\n".join(train_paths) + "\n")
with open(os.path.join(DB_ROOT, "test.txt"), "w") as f:
    f.write("\n".join(test_paths) + "\n")
with open(os.path.join(DB_ROOT, "split_stats.txt"), "w") as f:
    f.write(f"{'scene':<6} {'level':<6} {'total':>6} {'train':>6} {'test':>6}\n")
    f.write("-" * 36 + "\n")
    for scene, level, n, nt, nv in stats:
        f.write(f"{scene:<6} {level:<6} {n:>6} {nt:>6} {nv:>6}\n")
    f.write("-" * 36 + "\n")
    f.write(f"{'TOTAL':<12} {len(train_paths)+len(test_paths):>6} "
            f"{len(train_paths):>6} {len(test_paths):>6}\n")

print(f"Done. train: {len(train_paths)}, test: {len(test_paths)}")
