# GitHub Backup for Hermes Config

Automated daily backup of `~/.hermes/` to a private GitHub repository.

## Setup

### 1. Create a private GitHub repo
```bash
# On GitHub, create a PRIVATE repository (e.g., hermes_backup)
# NEVER use public — it contains auth.json, API keys, etc.
```

### 2. Generate a fine-grained personal access token
- Go to https://github.com/settings/tokens?type=beta
- Repository access: Only select repositories → pick your backup repo
- Permissions: Contents → Read and write
- Generate and copy the token

### 3. Configure git credentials
```bash
git config --global user.name "your-username"
git config --global user.email "your-email@example.com"
git config --global credential.helper store
echo "https://USERNAME:TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
```

### 4. Create backup script
Save to `~/.hermes/scripts/backup_to_github.sh`:
```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/tmp/hermes_backup"
REPO_URL="https://github.com/USER/REPO.git"
HERMES_DIR="$HOME/.hermes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Use git pull for incremental updates (faster than clone each time)
if [ -d "$BACKUP_DIR/.git" ]; then
    cd "$BACKUP_DIR"
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || {
        echo "❌ git pull failed, skipping"
        exit 1
    }
else
    rm -rf "$BACKUP_DIR"
    git clone "$REPO_URL" "$BACKUP_DIR" 2>/dev/null || {
        echo "❌ git clone failed"
        exit 1
    }
fi

cd "$BACKUP_DIR" || exit 1

# Copy config and skills
cp -r "$HERMES_DIR"/config* . 2>/dev/null || true
cp -r "$HERMES_DIR"/*.yaml . 2>/dev/null || true
cp -r "$HERMES_DIR"/*.json . 2>/dev/null || true
cp -r "$HERMES_DIR"/*.toml . 2>/dev/null || true
[ -d "$HERMES_DIR/skills" ] && cp -r "$HERMES_DIR/skills" ./skills_backup

# Holographic memory — dump as SQL to avoid binary bloat
# REQUIRES: sudo apt install sqlite3
if [ -f "$HERMES_DIR/memory_store.db" ] && command -v sqlite3 &>/dev/null; then
    sqlite3 "$HERMES_DIR/memory_store.db" ".dump" > ./memory_store.sql
    echo "  ✅ memory_store.db (SQL dump)"
elif [ -f "$HERMES_DIR/memory_store.db" ]; then
    echo "  ⚠️ sqlite3 not installed, skipping database backup"
fi

# AGENTS.md
[ -f "$HERMES_DIR/AGENTS.md" ] && cp "$HERMES_DIR/AGENTS.md" ./AGENTS.md

# MCP Holographic server (source only, skip node_modules)
if [ -d "$HERMES_DIR/mcp-holographic" ]; then
    mkdir -p ./mcp-holographic
    cp "$HERMES_DIR/mcp-holographic"/{index.js,package.json,README.md} ./mcp-holographic/ 2>/dev/null || true
fi

[ -d "$HERMES_DIR/cron" ] && cp -r "$HERMES_DIR/cron" ./cron_backup

# Ensure .gitignore excludes binary DB files
if ! grep -q "memory_store.db" .gitignore 2>/dev/null; then
    echo "memory_store.db" >> .gitignore
    echo "*.db" >> .gitignore
fi

cat > backup_info.md << EOF
# Hermes Backup
- Time: $(date)
- Source: $(hostname)
EOF

git add -A
if git diff --cached --quiet; then
    echo "ℹ️ No changes, skipping commit"
    exit 0
fi

git commit -m "🔄 Backup $TIMESTAMP" || exit 1
git push origin main 2>/dev/null && echo "✅ Backup: $TIMESTAMP" || {
    git push origin master 2>/dev/null && echo "✅ Backup: $TIMESTAMP" || echo "❌ Push failed"
}

rm -rf "$BACKUP_DIR"
```

### 5. Set up crontab
```bash
chmod +x ~/.hermes/scripts/backup_to_github.sh
mkdir -p ~/.hermes/logs
(crontab -l 2>/dev/null; echo "0 3 * * * $HOME/.hermes/scripts/backup_to_github.sh >> $HOME/.hermes/logs/backup.log 2>&1") | crontab -
```

## Pitfalls

1. **Branch naming** — Default branch may be `master` not `main`. Check with `git branch` after first clone. Rename with `git branch -m main` if needed.

2. **Token permissions** — 403 errors mean the token lacks write access. Ensure Contents = Read and write (not just Read).

3. **WSL TLS issues** — Some WSL environments have TLS handshake failures with GitHub. If `git push` fails with `gnutls_handshake() failed`, try setting `GIT_SSL_NO_VERIFY=1` (less secure) or configuring git to use OpenSSL.

4. **Public repo** — NEVER back up to a public repo. The backup contains auth.json, API keys, and credentials.

5. **Credential storage** — `~/.git-credentials` contains your token in plaintext. Set permissions `chmod 600`.

6. **Architecture drift** — When you change Hermes's storage architecture (e.g., switching from file-based memory to SQLite/Holographic), audit ALL scripts that reference the old storage. Common casualties:
   - Backup scripts still copying deleted directories
   - Cron jobs referencing old paths
   - Documentation listing stale file locations
   - MCP configs pointing to moved/deleted files
   **Rule: after any storage migration, search all scripts and configs for the old path before considering the migration done.**

7. **sqlite3 dependency** — The backup script uses `sqlite3` CLI to dump `memory_store.db` as SQL (avoids pushing binary files that bloat the repo). If `sqlite3` is not installed, the database backup is silently skipped with a warning. Install with `sudo apt install sqlite3` on Debian/Ubuntu.

8. **WSL crontab unreliability** — WSL instances are ephemeral; they start on-demand and stop when idle. Cron jobs scheduled via `crontab -e` will NOT run if WSL is sleeping/shutdown at the scheduled time. For reliable daily backup, consider:
   - Use Hermes cron jobs (`hermes cron create`) which persist across WSL restarts
   - Use Windows Task Scheduler to invoke `wsl.exe bash ~/.hermes/scripts/backup_to_github.sh`
   - Run the backup manually when needed: `bash ~/.hermes/scripts/backup_to_github.sh`

9. **Alternative: `hermes backup`** — Hermes has a built-in backup command that creates a zip archive of your entire `~/.hermes/` directory (config, skills, sessions, data). Use `hermes backup -o ~/hermes-backup.zip` for a full backup, or `hermes backup --quick` for a fast snapshot of critical state files only. Restore with `hermes import <zipfile>`. This is simpler than the GitHub script but doesn't provide version history.
