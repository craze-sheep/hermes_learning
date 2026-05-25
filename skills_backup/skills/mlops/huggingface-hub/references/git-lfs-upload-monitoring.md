# Git-LFS Upload Monitoring for HuggingFace

When uploading large files to HuggingFace via `git push` + git-lfs (as opposed to `hf upload` or Python API), use these patterns to monitor progress and diagnose issues.

> **⚠️ Prefer `hf upload` over git-lfs.** In proxy environments (China, WSL2, corporate), `hf upload` is ~20x faster than git-lfs. If you're seeing < 100 KB/s on git-lfs, kill it and switch to `hf upload`. See `git-lfs-vs-hf-upload.md` for speed data and diagnostic flow.

## State File Locations

A well-structured upload script typically maintains state in a `.hf_upload_state/` directory:

| File | Purpose |
|------|---------|
| `completed.txt` | One slot name per line; grep -Fxq to check if done |
| `<SLOT>.lfs-progress.log` | Real-time git-lfs transfer progress |
| `credentials` | Temp credential file (cleaned up on exit via trap) |

## Checking Progress

```bash
# 1. Which slots completed?
cat .hf_upload_state/completed.txt

# 2. Current git-lfs transfer progress
tail -3 .hf_upload_state/*.lfs-progress.log

# 3. Is the process still running?
ps aux | grep -E 'upload_to_hf|git.*push|git.*lfs' | grep -v grep

# 4. Tar files created so far
ls -lh tars/
```

### Reading the Progress Line

```
upload 1/1 881688576/1315708052 S1.tar.gz
         ^   ^         ^
         |   |         total bytes
         |   bytes transferred so far
         file index / total files
```

Progress % = bytes_so_far / total_bytes * 100

## Diagnosing Slow Uploads

When upload speed seems abnormally slow:

```bash
# Check the git-lfs process's network connections
PID=<git-lfs-pid>
ss -tnp | grep $PID

# Key indicators:
# - Send queue (2nd column) > 100KB → network backpressure
# - rem_address shows proxy (127.0.0.1:7897) → traffic routed through proxy
# - Connection state ESTAB → alive; CLOSE-WAIT → dead socket
```

Common causes of slow git-lfs uploads through proxy:
1. **Proxy bandwidth saturation** — other traffic using the same proxy
2. **HuggingFace rate limiting** — especially after multiple large uploads
3. **Proxy TLS interception** — MITM adding overhead to each chunk
4. **WSL2 networking overhead** — NAT translation layer adds latency

## Git-LFS Configuration for Reliability

Key git config settings for large file uploads:

```bash
git config lfs.activitytimeout 600    # seconds before LFS considers transfer dead
git config lfs.dialtimeout 60         # connection timeout
git config lfs.tlstimeout 60          # TLS handshake timeout
git config lfs.transfer.maxretries 8  # retry count on failure
git config lfs.transfer.maxretrydelay 60  # max delay between retries
git config http.lowSpeedLimit 1000    # bytes/s threshold
git config http.lowSpeedTime 600      # seconds below threshold before abort
```

## Proxy Setup for Git

When behind a proxy (common in China for HuggingFace access):

```bash
# Set proxy env vars (git-lfs reads these)
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897

# Or use git-specific proxy
git config http.proxy http://127.0.0.1:7897
```

## Upload Script Architecture

A robust git-lfs upload script follows this pattern:

```
for each slot in [S1..S8]:
    1. Check completed.txt → skip if done
    2. Create tar.gz from source directory (reuse if exists)
    3. git clone --depth=1 the HF repo (with LFS, credential helper)
    4. Hard-link or copy tar into repo dir
    5. git add + commit
    6. git push (triggers LFS upload)
    7. Mark completed on success
    8. Retry up to N times with exponential backoff
    9. Clean up work directory
```

Key design choices:
- **Hard-link tar** into repo dir (saves disk; falls back to cp --reflink)
- **GIT_LFS_SKIP_SMUDGE=1** on clone (don't download existing LFS files)
- **Credential file** with umask 077 + trap cleanup on EXIT
- **Per-attempt work directories** to avoid git state corruption on retry
