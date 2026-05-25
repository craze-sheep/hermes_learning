# Serial Upload Pattern for Large Datasets to Hugging Face

## Problem
Parallel `upload_folder` calls OOM-kill on systems with <16GB RAM. Even 6 processes at ~300MB each = 1.8GB overhead, plus the actual data buffering.

## Solution: Serial Upload with Progress Tracking

```python
#!/usr/bin/env python3
"""Serial upload S1-SN to Hugging Face (no OOM, with retry + resume)."""
import os, sys, time

# Clear proxy (required for China users)
# NOTE: This alone is NOT sufficient when running via terminal(background=true)
# because bash -lic re-sources .bashrc. Always also unset at bash level (see below).
for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
          "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"]:
    os.environ.pop(k, None)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import HfApi, login

token = os.environ.get("HF_TOKEN") or input("HF Token: ").strip()
login(token=token, add_to_git_credential=False)

api = HfApi()
DB = "/path/to/database"
USERNAME = "your-username"
SCENES = range(1, 9)
MAX_RETRIES = 3
DONE_FILE = "/tmp/hf_upload_done.txt"

# Load completed uploads
done = set()
if os.path.exists(DONE_FILE):
    with open(DONE_FILE) as f:
        done = {int(x.strip()) for x in f if x.strip().isdigit()}

for s in SCENES:
    if s in done:
        print(f"[skip] S{s} already uploaded")
        continue

    repo_id = f"{USERNAME}/dataset-name-s{s}"
    src = f"{DB}/S{s}"

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n[{attempt}/{MAX_RETRIES}] Uploading S{s} -> {repo_id}")
        try:
            api.upload_folder(
                repo_id=repo_id,
                folder_path=src,
                repo_type="dataset",
                path_in_repo=f"S{s}",
            )
            print(f"OK S{s}")
            with open(DONE_FILE, "a") as f:
                f.write(f"{s}\n")
            break
        except Exception as e:
            print(f"FAIL S{s}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(attempt * 30)

print("\nDone!")
```

## Key Design Decisions

1. **Progress file** (`/tmp/hf_upload_done.txt`): Records completed scene numbers. Script skips them on restart. Survives script crash but not WSL restart (it's in /tmp).

2. **Retry with backoff**: 30s, 60s, 90s between retries. Network blips recover automatically.

3. **No parallelism**: One upload at a time. HF's `upload_folder` already handles chunking internally.

4. **HF_ENDPOINT + proxy clear**: Must happen before `from huggingface_hub import`. The import triggers httpx client init which reads env vars.

## Running as Background Process

```bash
# WRONG — stdout buffered, no output visible
python upload_serial.py &

# WRONG — proxy not cleared at bash level, httpx still uses it
export PYTHONUNBUFFERED=1 HF_TOKEN=xxx && python upload_serial.py

# RIGHT — bash-level proxy unset + unbuffered + background
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy
export PYTHONUNBUFFERED=1 HF_TOKEN=xxx
python upload_serial.py

# Or with Hermes terminal tool:
terminal(
  command="unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy && export PYTHONUNBUFFERED=1 HF_TOKEN=xxx && python upload_serial.py",
  background=true, notify_on_complete=true
)
```

**Why bash-level unset is required**: Hermes `terminal()` wraps commands in `bash -lic` (login+interactive). This causes `~/.bashrc` to be sourced, which often re-exports proxy vars (e.g. `export HTTPS_PROXY=http://127.0.0.1:7897`). Even if the Python script does `os.environ.pop("HTTPS_PROXY")`, the bash wrapper re-sets it from `.bashrc` before Python even starts. The `unset` at bash level clears it after `.bashrc` sourcing.

## upload_folder Behavior

`api.upload_folder()` first **lists all local files** and **computes SHA256 for each**, then compares with the remote repo. For large directories (100K+ files), this hashing phase can take 5-10 minutes before any data transfer begins. During this phase:
- CPU active (hashing)
- Memory growing (file metadata in memory)
- Network 0 KB/s (no transfer yet)
- Process state: `D (disk sleep)` or `R (running)`

This is normal. Don't kill the process thinking it's stuck.

**BUT**: With 100K+ files, the hashing can cause the connection to go CLOSE-WAIT (dead). If after 10+ minutes there's still 0 KB/s network AND the TCP connection shows CLOSE-WAIT, the connection is dead — kill the process and switch to the tar-based approach. See `references/tar-upload-pattern.md`.

## Resumability

HF's `upload_folder` is inherently resumable — files already in the repo are skipped (compared by path + LFS hash). So even without the done-file, re-running uploads the same scene is safe; it just wastes time listing/checking existing files.

The done-file optimization skips entire scenes that completed, saving the listing overhead.

## Memory Usage

Serial upload: ~80-100MB per process. Safe on any system with 2GB+ free RAM.
