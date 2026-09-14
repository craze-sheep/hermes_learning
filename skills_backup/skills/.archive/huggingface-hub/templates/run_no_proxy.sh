#!/usr/bin/env bash
# Run a Python script with a completely clean environment (no proxy vars).
# Usage: bash run_upload.sh
#
# Why: Hermes terminal() uses 'bash -lic' which re-sources ~/.bashrc,
# re-exporting proxy vars even after 'unset'. 'env -i' starts fresh.

exec env -i \
  HOME="$HOME" \
  PATH="$PATH" \
  USER="$USER" \
  LANG="$LANG" \
  TERM="$TERM" \
  PYTHONUNBUFFERED=1 \
  HF_TOKEN="${HF_TOKEN:-YOUR_TOKEN_HERE}" \
  HF_ENDPOINT=https://hf-mirror.com \
  python3 "$@"
