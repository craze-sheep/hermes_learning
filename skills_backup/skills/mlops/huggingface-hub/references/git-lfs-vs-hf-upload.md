# git-lfs vs hf upload: Speed Comparison and Diagnostic Flow

## Observed Speed Data (WSL2 + Clash proxy at 127.0.0.1:7897)

| File | Method | Size | Speed | Time | Notes |
|------|--------|------|-------|------|-------|
| S1.tar.gz | git-lfs | 1.23 GB | ~2-3 MB/s initially, degraded | ~18 min | First upload, not yet throttled |
| S2.tar.gz | git-lfs | 2.26 GB | ~67 KB/s | Would take 9+ hours | Throttled after S1 |
| S2.tar.gz | hf upload | 2.26 GB | ~1.38 MB/s | ~28 min | Switched mid-upload |

**Speed ratio: hf upload is ~20x faster than throttled git-lfs.**

## Why git-lfs Slows Down

1. **Single-stream transfer** — git-lfs sends one chunk at a time, no parallelism
2. **Proxy overhead** — each chunk goes through TLS proxy, adding per-chunk latency
3. **HuggingFace rate limiting** — after large uploads, the LFS endpoint throttles
4. **Send queue backpressure** — check with `ss -tnp | grep git-lfs`, queue > 100KB = backed up

## Why hf upload is Faster

- Multi-part upload: splits large files into chunks, uploads in parallel
- Resumable: can continue from where it left off
- HTTP API direct: no git protocol overhead

## Diagnostic Flow

```
Step 1: Is git-lfs slow?
  → tail -3 .hf_upload_state/*.lfs-progress.log
  → If speed < 100 KB/s, proceed to Step 2

Step 2: Is it the network or git-lfs?
  → curl -o /dev/null -w '%{speed_download}' \
      https://speed.cloudflare.com/__down?bytes=5000000 \
      -x http://127.0.0.1:7897
  → If proxy speed > 1 MB/s, the network is fine → problem is git-lfs

Step 3: Check git-lfs connection state
  → PID=$(pgrep -f 'git-lfs pre-push')
  → ss -tnp | grep $PID
  → ESTAB + large send queue = backpressure (slow but alive)
  → CLOSE-WAIT = dead socket (stuck)

Step 4: Switch to hf upload
  → kill the parent upload script process
  → hf upload <repo_id> <local_file> <path_in_repo> --type dataset
  → hf upload uses HTTP API, bypasses git-lfs entirely
```

## When to Use Which

| Scenario | Use |
|----------|-----|
| Behind proxy (China, corporate, WSL2) | `hf upload` — always |
| Direct internet, small files (< 100MB) | Either works fine |
| Direct internet, large files (> 1GB) | `hf upload` — more reliable |
| Need git history / versioning | git-lfs (but use `hf upload` for initial bulk) |
| Resumable uploads | `hf upload` — built-in resume |
