# Dataset Train/Test Split Scripts

## split_train_test.py

Generates `train.txt` and `test.txt` inside `database/` with absolute paths.
Per-level 80/20 split with fixed seed for reproducibility.

```python
import os, random

DB_ROOT = os.path.dirname(os.path.abspath(__file__))
TRAIN_RATIO = 0.8
SEED = 42
random.seed(SEED)

train_paths, test_paths, stats = [], [], []

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
            key=int)
        n = len(samples)
        if n == 0:
            continue
        random.shuffle(samples)
        split_idx = int(n * TRAIN_RATIO)
        for s in samples[:split_idx]:
            train_paths.append(os.path.join(level_dir, s))
        for s in samples[split_idx:]:
            test_paths.append(os.path.join(level_dir, s))
        stats.append((scene, level, n, split_idx, n - split_idx))

with open(os.path.join(DB_ROOT, "train.txt"), "w") as f:
    f.write("\n".join(train_paths) + "\n")
with open(os.path.join(DB_ROOT, "test.txt"), "w") as f:
    f.write("\n".join(test_paths) + "\n")
```

## make_split_dirs.py

Creates symlinked `train/` and `test/` directories at project root,
preserving the `S{scene}/L{level}/{sample_id}/` hierarchy.

```python
import os, shutil

BASE = "/path/to/project"  # project root, NOT database/
DB = os.path.join(BASE, "database")

for split in ["train", "test"]:
    split_dir = os.path.join(BASE, split)
    if os.path.exists(split_dir):
        shutil.rmtree(split_dir)
    with open(os.path.join(DB, f"{split}.txt")) as f:
        paths = [l.strip() for l in f if l.strip()]
    for src in paths:
        rel = os.path.relpath(src, DB)  # S1/L1/67
        dst = os.path.join(split_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.symlink(src, dst)
```

## Verification

```bash
# Count symlinks per level (DO NOT use ls -d */)
for s in S1 S2 ...; do
  for l in train/$s/L*/; do
    train=$(find "$l" -maxdepth 1 -type l | wc -l)
    test=$(find "test/$s/$(basename $l)" -maxdepth 1 -type l | wc -l)
    # verify ratio
  done
done
```

Pitfall: `ls -d "$dir"*/` does not reliably count symlinked directories.
Always use `find "$dir" -maxdepth 1 -type l | wc -l`.
