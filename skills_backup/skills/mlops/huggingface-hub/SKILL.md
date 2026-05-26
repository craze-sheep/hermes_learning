---
name: huggingface-hub
description: "HuggingFace hf CLI: search/download/upload models, datasets."
version: 1.0.0
author: Hugging Face
license: MIT
tags: [huggingface, hf, models, datasets, hub, mlops]
platforms: [linux, macos, windows]
---

# Hugging Face CLI (`hf`) Reference Guide

The `hf` command is the modern command-line interface for interacting with the Hugging Face Hub, providing tools to manage repositories, models, datasets, and Spaces.

> **IMPORTANT:** The `hf` command replaces the now deprecated `huggingface-cli` command.

## Quick Start
*   **Installation:** `curl -LsSf https://hf.co/cli/install.sh | bash -s`
*   **Help:** Use `hf --help` to view all available functions and real-world examples.
*   **Authentication:** Recommended via `HF_TOKEN` environment variable or the `--token` flag.

---

## Core Commands

### General Operations
*   `hf download REPO_ID`: Download files from the Hub.
*   `hf upload REPO_ID`: Upload files/folders (recommended for single-commit).
*   `hf upload-large-folder REPO_ID LOCAL_PATH`: Recommended for resumable uploads of large directories.
*   `hf sync`: Sync files between a local directory and a bucket.
*   `hf env` / `hf version`: View environment and version details.

### Authentication (`hf auth`)
*   `login` / `logout`: Manage sessions using tokens from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
*   `list` / `switch`: Manage and toggle between multiple stored access tokens.
*   `whoami`: Identify the currently logged-in account.

### Repository Management (`hf repos`)
*   `create` / `delete`: Create or permanently remove repositories.
*   `duplicate`: Clone a model, dataset, or Space to a new ID.
*   `move`: Transfer a repository between namespaces.
*   `branch` / `tag`: Manage Git-like references.
*   `delete-files`: Remove specific files using patterns.

---

## Specialized Hub Interactions

### Datasets & Models
*   **Datasets:** `hf datasets list`, `info`, and `parquet` (list parquet URLs).
*   **SQL Queries:** `hf datasets sql SQL` — Execute raw SQL via DuckDB against dataset parquet URLs.
*   **Models:** `hf models list` and `info`.
*   **Papers:** `hf papers list` — View daily papers.

### Discussions & Pull Requests (`hf discussions`)
*   Manage the lifecycle of Hub contributions: `list`, `create`, `info`, `comment`, `close`, `reopen`, and `rename`.
*   `diff`: View changes in a PR.
*   `merge`: Finalize pull requests.

### Infrastructure & Compute
*   **Endpoints:** Deploy and manage Inference Endpoints (`deploy`, `pause`, `resume`, `scale-to-zero`, `catalog`).
*   **Jobs:** Run compute tasks on HF infrastructure. Includes `hf jobs uv` for running Python scripts with inline dependencies and `stats` for resource monitoring.
*   **Spaces:** Manage interactive apps. Includes `dev-mode` and `hot-reload` for Python files without full restarts.

### Storage & Automation
*   **Buckets:** Full S3-like bucket management (`create`, `cp`, `mv`, `rm`, `sync`).
*   **Cache:** Manage local storage with `list`, `prune` (remove detached revisions), and `verify` (checksum checks).
*   **Webhooks:** Automate workflows by managing Hub webhooks (`create`, `watch`, `enable`/`disable`).
*   **Collections:** Organize Hub items into collections (`add-item`, `update`, `list`).

---

## China Mirror (hf-mirror.com)

When `huggingface.co` is blocked (GFW), use the domestic mirror:

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

Set this **before** any `hf` or Python `huggingface_hub` calls. Works for:
- `hf auth login` — login via mirror
- `hf upload` / `hf download` — all transfers
- Python API: `os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"` before importing

**Verification**: `curl -s https://hf-mirror.com` should return HTML (not timeout).

**Pitfall**: Without this env var, `hf auth login` fails with `SSL: UNEXPECTED_EOF_WHILE_READING` — the proxy CONNECT tunnel succeeds but TLS handshake to `huggingface.co` gets interfered with. The mirror avoids this entirely.

**Pitfall (proxy conflict)**: If `HTTP_PROXY`/`HTTPS_PROXY` are set (e.g. Clash at 127.0.0.1:7897), `httpx` inside `huggingface_hub` routes through the proxy even when `HF_ENDPOINT` points to the mirror. The proxy's MITM/interception breaks TLS → same SSL error.

**Fix — bash-level unset is REQUIRED**: Python-level `os.environ.pop()` alone does NOT work when running via Hermes `terminal()` because the wrapper uses `bash -lic` (login+interactive), which re-sources `~/.bashrc` and re-exports proxy vars AFTER the Python `os.environ.pop()` runs but BEFORE httpx reads them. Always unset at the bash level:
```bash
# CORRECT — bash-level unset, then run Python
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy
export PYTHONUNBUFFERED=1 HF_ENDPOINT=https://hf-mirror.com HF_TOKEN=hf_xxx
python upload_script.py

# WRONG — Python-level clearing alone doesn't work in bash -lic
python -c "import os; [os.environ.pop(k,None) for k in [...]]; from huggingface_hub import HfApi; ..."  
# ^ proxy still active because .bashrc re-exports before Python imports httpx
```
For standalone scripts (not via terminal()), Python-level clearing works because the shell isn't login+interactive. But for safety, always clear at both levels.

## Dataset Upload Workflow (Large Datasets)

For 100GB+ datasets, split into sub-datasets per logical unit (e.g., per scene):

```python
# create_repos.py — one-shot repo creation
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # if in China
from huggingface_hub import HfApi

api = HfApi()
for i in range(1, 9):
    api.create_repo(
        repo_id=f"USERNAME/dataset-name-part{i}",
        repo_type="dataset",
        private=False,
        exist_ok=True,
    )
```

Then upload each part:
```bash
for i in 1 2 3 4 5 6 7 8; do
  hf upload USERNAME/dataset-name-part${i} /path/to/data/part${i}/ --repo-type dataset
done
```

**Pitfall**: `huggingface-cli` is deprecated. Use `hf` CLI instead. Python API (`HfApi`) is unaffected.

**Pitfall (parallel upload OOM)**: Running multiple `upload_folder` processes in parallel consumes ~150-700MB each. On 9.7GB RAM (WSL2), 6+ parallel uploads WILL get OOM-killed (exit code 137). **Always use serial uploads for large datasets.** See `references/serial-upload-pattern.md` for a production-tested script with progress tracking and retry.

**Pitfall (Python stdout buffering)**: When running upload scripts as background processes (`terminal background=true`), Python buffers stdout and no output appears until the buffer flushes. Fix: set `PYTHONUNBUFFERED=1` in the environment, or use `python -u` flag. Example: `export PYTHONUNBUFFERED=1 && python upload_serial.py`.

**Pitfall (too many small files — upload_folder timeout)**: `upload_folder` lists ALL local files and computes SHA256 for each BEFORE starting any transfer. With 100K+ files this hashing phase takes 5-10+ minutes and the HF connection can go CLOSE-WAIT (dead socket) — the process appears stuck with 0 KB/s network and no output. **Solution: tar the files first, then upload individual tar files with `upload_file`.** Each tar replaces thousands of small files with one large file. See `references/tar-upload-pattern.md` for a production-tested script with progress tracking and retry.

**Pitfall (git-lfs upload crawling through proxy)**: If `git-lfs` upload is stuck at < 100 KB/s while `curl` speed test through the same proxy shows > 1 MB/s, the bottleneck is git-lfs's single-stream protocol, not your network. **Don't wait — kill the git-lfs process and switch to `hf upload`.** Diagnostic steps: (1) `curl -o /dev/null -w '%{speed_download}' https://speed.cloudflare.com/__down?bytes=5000000 -x http://127.0.0.1:7897` to test proxy speed, (2) `ss -tnp | grep git-lfs` to check send queue and connection state, (3) if proxy speed is fine but git-lfs is slow, switch to `hf upload` immediately. See `references/git-lfs-vs-hf-upload.md` for the full diagnostic flow and speed comparison data.

**Pitfall (proxy not clearing in Hermes terminal)**: `bash -lic` re-sources `~/.bashrc` which re-exports proxy vars. Neither `unset` nor `env -u` nor Python `os.environ.pop()` reliably fixes this. Use the `env -i` wrapper template: `templates/run_no_proxy.sh`. See `references/hf-proxy-china.md` for the full ranked fix list.

**Pitfall (diagnosing stuck hf upload)**: If `hf upload` has been running for hours on a file that should take minutes, it's likely stuck on proxy-induced SSL failure. Diagnostic checklist:
1. `ps -p PID -o pid,cmd,%cpu,etime` — check runtime; hours for a few GB = stuck
2. `cat /proc/PID/status | grep State` — stuck processes show `S (sleeping)` not `R (running)`
3. `ls .hf_upload_state/*.uploaded` — no new marker = no progress
4. `cat /proc/PID/environ | tr '\0' '\n' | grep -i proxy` — if proxy vars present, that's the cause
Fix: `kill PID`, clear proxy at bash level, re-run upload script (markers ensure completed slots are skipped).

**Pitfall (hf-mirror.com mid-transfer stalls)**: Even with proxy cleared, `hf upload` to hf-mirror.com can stall mid-transfer (e.g., stuck at 97% with speed dropping from ~15 MB/s to ~100 KB/s). This is different from the proxy-induced SSL stall — the upload starts fine but hf-mirror's server closes the connection partway through. Observed pattern: S3 (2.4 GB) uploaded fine at 15 MB/s, then S4 (2.1 GB) stalled at 97% for hours. The process shows `S (sleeping)` state and the `.uploaded` marker never appears.

**Diagnosis**: Check `Process Files` progress bar — if it's at 90%+ but speed has dropped to KB/s, it's a mid-transfer stall, not a proxy issue.

**Mitigation options** (none are perfect):
1. Kill and retry — may stall again at a different percentage
2. Use `upload-large-folder` instead of `upload_file` — has built-in resumable chunked uploads
3. Split large tars into smaller chunks (< 1 GB each) — less likely to stall
4. Upload during off-peak hours (hf-mirror may have less traffic)
5. Fall back to `git clone` + `git lfs` + `git push` through proxy to huggingface.co directly (slower but more reliable)

## Git-LFS Upload Monitoring

When uploading via `git push` + git-lfs (not `hf upload`), see `references/git-lfs-upload-monitoring.md` for progress monitoring, slow-upload diagnosis (proxy, rate limiting, send queue analysis via `ss -tnp`), and a robust upload script architecture pattern.

## Choosing upload strategy
- < 10K files → `upload_folder` works fine
- 10K-100K files → `upload_folder` may work but hashing is slow; consider tar
- 100K+ files → **must tar first**, `upload_folder` will timeout
- For tar approach: use `upload_file` per tar, NOT `upload_folder` on the tar directory (avoids re-listing)

### git-lfs vs hf upload — ALWAYS prefer `hf upload`

`hf upload` uses HTTP API with multi-part parallel uploads. `git-lfs` uses a single-stream transfer that is dramatically slower through proxies:

| Method | Speed through proxy (127.0.0.1:7897) | Notes |
|--------|--------------------------------------|-------|
| `hf upload` | ~1.4 MB/s | Multi-part, resumable |
| `git push` + git-lfs | ~67 KB/s | Single-stream, easily throttled |

**hf upload is 20x faster than git-lfs in proxy environments.** If a git-lfs upload is crawling (< 100 KB/s), kill it and switch to `hf upload` — the time saved far outweighs the sunk cost.

**Decision rule:** If you're behind a proxy (China, corporate VPN, WSL2), never use git-lfs for large files. Use `hf upload` directly.

### Speed-first tar compression (pigz -1)

When creating tar.gz files for upload, speed matters more than compression ratio — you're going to upload them anyway, and the upload speed is the real bottleneck. Use `pigz -1` (lowest compression level) with streaming pipe and atomic write:

```bash
# Streaming pipe + atomic write
tmp_file="${tar_file}.tmp.$$"
rm -f "$tmp_file"
tar -C "$DB_DIR" -cf - "$slot" | pigz -1 > "$tmp_file"
mv "$tmp_file" "$tar_file"
```

Key points:
- `pigz -1` = fastest compression, ~3-5x faster than default gzip -6, files only ~10-15% larger
- Streaming pipe (`tar -cf - | pigz`) avoids intermediate files, uses less disk
- Atomic write (`tmp.$$` then `mv`) prevents partial/corrupt tar.gz files on crash
- Check `[[ -s "$tar_file" ]]` to skip already-packed slots
- Fallback: `tar -czf` if pigz not installed

For parallel packing (multiple slots at once), use `&` + `wait` with concurrency limit:
```bash
MAX_JOBS=4
for s in S1 S2 S3 S4 S5 S6 S7 S8; do
  [[ -s "tars/${s}.tar.gz" ]] && continue
  (
    tmp="tars/${s}.tar.gz.tmp.$$"
    tar -C database/ -cf - "$s" | pigz -1 > "$tmp"
    mv "$tmp" "tars/${s}.tar.gz"
  ) &
  # throttle: wait when at max parallel jobs
  while (( $(jobs -r | wc -l) >= MAX_JOBS )); do sleep 1; done
done
wait
```

### Parallel packing + uploading pattern

When uploading multiple large datasets (e.g., S1-S8 each as a tar.gz), run packing and uploading as **two independent processes** coordinated via filesystem:

```bash
# Process 1: pack tar files (can be parallel with pigz -1, see above)
for s in S3 S4 S5 S6 S7 S8; do
  [[ -s "tars/${s}.tar.gz" ]] && continue
  tar -C database/ -cf - "$s" | pigz -1 > "tars/${s}.tar.gz.tmp.$$"
  mv "tars/${s}.tar.gz.tmp.$$" "tars/${s}.tar.gz"
done

# Process 2: upload as each tar becomes available (independent process)
for s in S3 S4 S5 S6 S7 S8; do
  while [[ ! -s "tars/${s}.tar.gz" ]]; do sleep 10; done  # wait for pack
  hf upload "user/repo-${s,,}" "tars/${s}.tar.gz" "/${s}.tar.gz" --type dataset
done
```

**Key:** The two loops are independent processes. The upload loop polls for tar file existence. This way packing and uploading overlap — while S3 uploads, S4 is being packed.

**Pitfall:** Don't include already-handled slots in the upload loop "with a marker file" — just start the loop from the next slot. Cleaner code, no marker file management needed.

## Advanced Usage & Tips

### Global Flags
*   `--format json`: Produces machine-readable output for automation.
*   `-q` / `--quiet`: Limits output to IDs only.

### Extensions & Skills
*   **Extensions:** Extend CLI functionality via GitHub repositories using `hf extensions install REPO_ID`.
*   **Skills:** Manage AI assistant skills with `hf skills add`.
