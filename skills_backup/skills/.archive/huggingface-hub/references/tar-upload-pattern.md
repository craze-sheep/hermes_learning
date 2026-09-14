# Tar-Based Upload Pattern for Datasets with Many Files

## Problem

`upload_folder` computes SHA256 for every local file before starting transfer. With 350K+ files (e.g., 1600 samples × 220 files/sample), the hashing phase:
- Takes 5-10+ minutes
- Can cause the HF connection to go CLOSE-WAIT (dead socket)
- Process appears stuck: 0 KB/s network, `D (disk sleep)` state, no output

## Solution: Tar + Upload File

Replace thousands of small files with a few large tar.gz archives, then upload each with `api.upload_file`.

### Step 1: Tar per logical unit (e.g., per level)

```python
import tarfile, os

def make_tar(src_dir, tar_path):
    """Pack a directory into .tar.gz"""
    if os.path.exists(tar_path):
        return  # already packed
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(src_dir, arcname=os.path.basename(src_dir))
```

Each tar replaces ~44K-132K files with one 50-200MB file.

### Step 2: Upload individual tar files

```python
from huggingface_hub import HfApi

api = HfApi()
api.upload_file(
    path_or_fileobj="/path/to/S1_L1.tar.gz",
    path_in_repo="S1_L1.tar.gz",
    repo_id="username/dataset",
    repo_type="dataset",
)
```

### Step 3: Parallel pack + upload (production pattern)

Use threading to pack the next level while uploading the current one:

```python
import threading, queue

upload_queue = queue.Queue()

def packer(scene_num, levels):
    """Pack all levels for a scene, enqueue each for upload."""
    for level in levels:
        tar_path = f"{tar_dir}/S{scene_num}_{level}.tar.gz"
        if not os.path.exists(tar_path):
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(src, arcname=f"S{scene_num}/{level}")
        upload_queue.put((scene_num, f"S{scene_num}/{level}", tar_path))
    upload_queue.put((scene_num, None, None))  # sentinel: scene done

def uploader():
    """Upload tar files from queue, one at a time."""
    finished = set()
    while len(finished) < 8:  # adjust total scenes
        s_num, tar_key, tar_path = upload_queue.get()
        if tar_key is None:
            finished.add(s_num)
            continue
        api.upload_file(
            path_or_fileobj=tar_path,
            path_in_repo=os.path.basename(tar_path),
            repo_id=f"username/dataset-s{s_num}",
            repo_type="dataset",
        )
        # Mark done
        with open(done_file, "a") as f:
            f.write(f"{tar_key}\n")

# Launch: one uploader thread, one packer thread per scene
uploader_thread = threading.Thread(target=uploader, daemon=True)
uploader_thread.start()
for s, levels in all_tasks:
    threading.Thread(target=packer, args=(s, levels), daemon=True).start()
```

## Choosing Tar Granularity

**Per-scene (e.g., S1.tar.gz)** — one tar per repo:
- Fewer, larger files (8 files total for S1-S8)
- Simpler progress tracking (one `done` entry per scene)
- S1 1600 samples → ~1.2GB tar; S8 8400 samples → ~6GB tar
- Recommended when you want simplicity

**Per-level (e.g., S1_L1.tar.gz)** — one tar per level per repo:
- More files (~60 total) but each smaller (50-200MB)
- Finer-grained resume (can retry individual levels)
- Better for debugging (can inspect one level without downloading whole scene)

**Rule of thumb**: If each scene fits in a single tar < 5GB, go per-scene. Otherwise per-level.

## Speed Expectations

- **hf-mirror.com**: ~1.2-2.0 MB/s (observed 2026-05-25, varies by time of day)
- **huggingface.co direct** (via proxy): varies, can be faster
- **100GB dataset**: ~15-25 hours at mirror speed
- **Per-tar upload**: 150MB tar at 1.5MB/s ≈ 2 minutes; 1.2GB tar at 2MB/s ≈ 10 minutes

## Recommended: Sequential Pack-Upload-Delete

The parallel pack approach (8 scenes at once) causes disk I/O contention. Simpler and more reliable:

```python
for s in range(1, 9):
    for level in levels:
        # 1. Pack
        tar_path = f"tars/S{s}_{level}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(src_dir, arcname=f"S{s}/{level}")

        # 2. Upload
        api.upload_file(
            path_or_fileobj=tar_path,
            path_in_repo=os.path.basename(tar_path),
            repo_id=f"username/dataset-s{s}",
            repo_type="dataset",
        )

        # 3. Delete tar to save disk
        os.remove(tar_path)

        # 4. Record progress
        with open(done_file, "a") as f:
            f.write(f"S{s}/{level}\n")
```

This uses minimal disk (only 1 tar at a time) and is easy to debug.

## File Size Recommendations

- **tar.gz**: Good compression for text/JSON/NPZ data. 50-200MB per tar is ideal.
- **tar (uncompressed)**: Faster to create, larger upload. Use if CPU is the bottleneck.
- **Avoid**: Very large single files (>5GB) — HF has per-file size limits and upload_file may fail.

## Progress Tracking

Use a done file (`/tmp/hf_upload_tar_done.txt`) recording completed `S{n}/{level}` keys. On restart, skip already-done entries. Survives script crash but not WSL restart.

## Full Production Script Pattern

Key features for a production tar-upload script:
- Sequential pack-upload-delete (one level at a time, minimal disk usage)
- `flush=True` on all print statements for real-time output
- Progress file with `S{n}/{level}` granularity (`/tmp/hf_upload_done.txt`)
- Retry with 15s/30s backoff per tar file
- `os.remove(tar_path)` after successful upload to save disk

### Complete Working Script

```python
#!/usr/bin/env python3
"""Pack one, upload one — sequential tar upload to Hugging Face."""
import os, sys, time, tarfile

# Clear proxy (Python-level; ALSO use env -i wrapper for Hermes terminal)
for k in ["HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","ALL_PROXY","all_proxy"]:
    os.environ.pop(k, None)
os.environ["no_proxy"] = "*"
os.environ["NO_PROXY"] = "*"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import HfApi, login
token = os.environ.get("HF_TOKEN") or input("HF Token: ").strip()
login(token=token, add_to_git_credential=False)

api = HfApi()
db = "/path/to/data"
tar_dir = "/path/to/tars"
username = "your-username"
MAX_RETRIES = 3
os.makedirs(tar_dir, exist_ok=True)

done_file = "/tmp/hf_upload_done.txt"
done = set()
if os.path.exists(done_file):
    with open(done_file) as f:
        done = {line.strip() for line in f if line.strip()}

for s in range(1, 9):
    s_dir = f"{db}/S{s}"
    levels = sorted([d for d in os.listdir(s_dir)
                     if os.path.isdir(os.path.join(s_dir, d)) and d.startswith("L")],
                    key=lambda x: int(x[1:]))
    repo_id = f"{username}/dataset-s{s}"

    for level in levels:
        tar_key = f"S{s}/{level}"
        if tar_key in done:
            print(f"[skip] {tar_key}", flush=True)
            continue

        tar_name = f"S{s}_{level}.tar.gz"
        tar_path = f"{tar_dir}/{tar_name}"

        # Pack
        if not os.path.exists(tar_path):
            print(f"[pack] {tar_name} ...", end=" ", flush=True)
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(f"{s_dir}/{level}", arcname=f"S{s}/{level}")
            size_mb = os.path.getsize(tar_path) / 1024 / 1024
            print(f"OK ({size_mb:.0f}MB)", flush=True)

        # Upload with retry
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"[upload {attempt}/{MAX_RETRIES}] {tar_name} ...", end=" ", flush=True)
            try:
                api.upload_file(
                    path_or_fileobj=tar_path,
                    path_in_repo=tar_name,
                    repo_id=repo_id,
                    repo_type="dataset",
                )
                print("OK", flush=True)
                with open(done_file, "a") as f:
                    f.write(f"{tar_key}\n")
                os.remove(tar_path)  # save disk
                break
            except Exception as e:
                print(f"FAIL: {e}", flush=True)
                if attempt < MAX_RETRIES:
                    time.sleep(attempt * 15)

print("\nDone!", flush=True)
```

**Run with proxy-free wrapper** (critical for Hermes terminal):
```bash
bash templates/run_no_proxy.sh upload_serial.py
```

## Cleaning Up HF Files (Strategy Switch)

When switching upload strategies (e.g., per-level tars → per-scene tars), delete old files first:

```python
from huggingface_hub import HfApi
api = HfApi()
# List current files
files = [f.rfilename for f in api.list_repo_tree(repo_id="user/dataset", repo_type="dataset")]
# Delete specific files
api.delete_file("S1_L1.tar.gz", repo_id="user/dataset-s1", repo_type="dataset")
```

**Pitfall**: Don't leave orphaned files from a previous strategy. Users downloading the dataset will get confused by mixed granularities.

## Shell Script Alternative (Bash)

For environments where Python overhead matters, a pure-bash wrapper works:

```bash
#!/usr/bin/env bash
set -euo pipefail
export HF_ENDPOINT=https://hf-mirror.com HF_TOKEN="${HF_TOKEN:-your_token}"

for s in 1 2 3 4 5 6 7 8; do
    tar_file="tars/S${s}.tar.gz"
    repo="username/dataset-s${s}"
    
    # Pack
    tar czf "$tar_file" -C "$DB" "S${s}"
    
    # Upload (inline Python for just the upload call)
    python3 -c "
import os
for k in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy','ALL_PROXY','all_proxy']:
    os.environ.pop(k, None)
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from huggingface_hub import HfApi, login
login(token=os.environ['HF_TOKEN'], add_to_git_credential=False)
HfApi().upload_file(path_or_fileobj='$tar_file', path_in_repo='S${s}.tar.gz', repo_id='$repo', repo_type='dataset')
"
    
    # Cleanup
    echo "S${s}" >> /tmp/hf_upload_done.txt
    rm -f "$tar_file"
done
```

Run with: `env -i HOME="$HOME" PATH="$PATH" ... bash script.sh`
