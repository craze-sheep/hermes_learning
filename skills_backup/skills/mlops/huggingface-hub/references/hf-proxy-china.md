# Hugging Face Proxy/Mirror Troubleshooting in China

## Symptom
`hf auth login` or Python `huggingface_hub` calls fail with:
```
httpcore.ConnectError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol
```

Or upload runs at ~160KB/s instead of expected ~1.2MB/s (proxy throttling).

## Root Cause
Clash/proxy at `127.0.0.1:7897` intercepts HTTPS via CONNECT tunnel but breaks TLS handshake to `huggingface.co`. Setting `HF_ENDPOINT=https://hf-mirror.com` alone is NOT enough — `httpx` still routes through the proxy because it reads `HTTP_PROXY`/`HTTPS_PROXY` env vars.

## Fix (ranked by reliability)

### 1. `env -i` wrapper script (MOST RELIABLE)
Completely strips ALL env vars, then sets only what's needed. Immune to `.bashrc` re-exports:
```bash
#!/bin/bash
exec env -i \
  HOME="$HOME" PATH="$PATH" USER="$USER" LANG="$LANG" \
  PYTHONUNBUFFERED=1 \
  HF_TOKEN="$HF_TOKEN" \
  HF_ENDPOINT=https://hf-mirror.com \
  python3 upload_script.py
```
Run with: `bash run_upload.sh`

### 2. Bash-level `unset` (reliable for direct shell)
```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy
export PYTHONUNBUFFERED=1 HF_ENDPOINT=https://hf-mirror.com HF_TOKEN=hf_xxx
python upload_script.py
```
Works when typing directly in terminal. Does NOT work via Hermes `terminal()` because the wrapper uses `bash -lic` which re-sources `~/.bashrc` and re-exports proxy vars AFTER the unset.

### 3. Python-level `os.environ.pop()` (UNRELIABLE)
```python
import os
for k in ["HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","ALL_PROXY","all_proxy"]:
    os.environ.pop(k, None)
os.environ["no_proxy"] = "*"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
```
**WARNING**: Does NOT work when running via Hermes `terminal()` — bash re-sets the vars before Python imports httpx. Only works in standalone scripts where the shell isn't login+interactive.

## Verification
```bash
# Check proxy is actually cleared in the Python process
PYPID=$(pgrep -f "python.*upload" | head -1)
cat /proc/$PYPID/environ | tr '\0' '\n' | grep -i proxy
# Should output nothing (or only no_proxy=*)

# Mirror reachable without proxy?
curl -s --max-time 10 https://hf-mirror.com  # should return HTML
```

## Speed Impact
- With proxy (127.0.0.1:7897) → hf-mirror.com: ~160 KB/s (proxy intercepts + throttles)
- Without proxy → hf-mirror.com: ~1.2 MB/s (direct connection, 8x faster)

## Notes
- `hf-mirror.com` is a community mirror, may occasionally be down
- `HF_TOKEN` env var works with the mirror for non-interactive auth
- After clearing proxy, verify with `/proc/PID/environ` — don't trust the shell env alone
