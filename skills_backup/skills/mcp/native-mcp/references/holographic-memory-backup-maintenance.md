# Holographic Memory Backup & Maintenance

## Architecture

- **Database**: `~/.hermes/memory_store.db` (SQLite, WAL mode)
- **MCP Server**: `~/.hermes/mcp-holographic/index.js` (Node.js, better-sqlite3)
- **Tools**: `fact_query` (read-only), `fact_store` (read-write), `fact_feedback` (quality signals)

## fact_store Actions

### Actions available from Hermes

| Action | Description |
|--------|-------------|
| add | Store a fact. Auto-merges via Jaccard similarity (threshold 0.6, same category) |
| update | Update content/category/tags/trust for a fact |
| remove | Delete a fact + clean orphan entities |
| search | Keyword lookup (legacy, prefer fact_query) |
| probe | Entity recall (legacy, prefer fact_query) |
| related | Entity graph adjacency (legacy, prefer fact_query) |
| reason | Multi-entity intersection (legacy, prefer fact_query) |
| contradict | Find low-trust and conflicting facts (legacy, prefer fact_query) |
| list | List recent facts (legacy, prefer fact_query) |

### Actions in MCP server code but NOT exposed by Hermes wrapper

| Action | Description | Why blocked |
|--------|-------------|-------------|
| dedup | Batch scan for duplicates (Jaccard ≥ 0.6), optional auto_merge | Hermes wrapper at `plugins/memory/holographic/__init__.py` doesn't include these in its action dispatch |
| merge | Merge two facts by primary_id + secondary_id | Same |

**Workaround**: Claude Code/Codex connected directly to the MCP server CAN use dedup/merge. From Hermes, you'd need to patch the wrapper or call the MCP server directly via terminal.

## Backup to GitHub

### Script Location
`~/.hermes/scripts/backup_to_github.sh`

### What Gets Backed Up
- Config files (config.yaml, *.json, *.toml)
- Skills directory
- MCP holographic server source (index.js, package.json only — not node_modules)
- AGENTS.md
- Cron configuration
- **memory_store.db → exported as memory_store.sql** (SQL dump, not binary)

### Critical Dependency: sqlite3

The backup script uses `sqlite3` CLI to dump the database:

```bash
sqlite3 ~/.hermes/memory_store.db ".dump" > memory_store.sql
```

**Pitfall: sqlite3 is NOT installed by default on WSL.** The script has a guard:

```bash
if command -v sqlite3 &>/dev/null; then
    sqlite3 "$HERMES_DIR/memory_store.db" ".dump" > ./memory_store.sql
else
    echo "  ⚠️ sqlite3 未安装，跳过数据库备份（避免推送二进制文件）"
fi
```

The script reports overall "✅ 备份成功" even when the memory database export is skipped. This means you can have backups running for weeks thinking everything is fine, while the actual memory data was never backed up.

**Fix:**
```bash
sudo apt install sqlite3
```

### Scheduling: Hermes Cron vs System Crontab

The original setup uses system crontab:
```
0 3 * * * /home/lzy/.hermes/scripts/backup_to_github.sh >> ~/.hermes/logs/backup.log 2>&1
```

**Problem**: System crontab runs only if the machine is on at the scheduled time. If the computer is off/sleeping at 3am, the backup is skipped with no catch-up.

**Solution: Use Hermes cron instead.** Hermes cron jobs are managed by the gateway and can be configured to catch up on missed runs. Create with:

```python
cronjob(action='create', name='memory-backup-github',
        schedule='0 3 * * *',
        prompt='执行记忆备份脚本：bash /home/lzy/.hermes/scripts/backup_to_github.sh',
        deliver='local', enabled_toolsets=['terminal'])
```

### Verifying Backup Health

Check the backup log:
```bash
tail -20 ~/.hermes/logs/backup.log
```

Look for:
- `✅ 备份 memory_store.db (SQL dump)` — memory is being backed up
- `⚠️ sqlite3 未安装` — memory is NOT being backed up
- `❌ git push 失败` — network/auth issue

Check the GitHub repo directly:
```bash
cd /tmp && git clone https://github.com/craze-sheep/hermes_learning.git backup_check
ls -la backup_check/memory_store.sql  # Should exist and be recent
```

## Monthly Cleanup

Script: `~/.hermes/scripts/cleanup_memory.sh`

Runs via Hermes cron on the 1st of each month at 4am. Cleans up:
- Low-trust facts (trust < 0.3, older than 30 days)
- Expired facts (trust < 0.5, older than 90 days)
- Orphaned entities and fact_entities

**Note**: This script does NOT do dedup/merge — only deletion of stale data.

## Manual Backup/Restore

### Hermes Built-in Backup
```bash
hermes backup                    # Full backup to ~/hermes-backup-<timestamp>.zip
hermes backup --quick            # Quick snapshot (config, state.db, .env, auth, cron)
hermes import <zipfile>          # Restore from backup
```

### Manual SQLite Backup
```bash
# Export
sqlite3 ~/.hermes/memory_store.db ".dump" > memory_backup.sql

# Restore (careful — overwrites existing)
sqlite3 ~/.hermes/memory_store.db < memory_backup.sql
```

## Three Memory Systems

| System | Storage | Scope | Use Case |
|--------|---------|-------|----------|
| Built-in (MEMORY.md/USER.md) | Markdown files | Per-agent | Agent personality, session notes |
| Holographic (memory_store.db) | SQLite via MCP | Shared across all tools | User facts, project info, preferences |
| MCP Memory Server | Separate SQLite | Per-server tool | Entity graphs (if configured) |

User can choose to use only holographic and disable built-in:
- Delete MEMORY.md and USER.md
- Claude Code: set `autoMemoryEnabled: false` in settings.json
- All tools share holographic via the MCP server

## Pitfalls

1. **sqlite3 not installed** — memory_store.db export silently skipped, backup "succeeds" without memory data
2. **Binary .db files in git** — .gitignore should exclude `*.db` to prevent repo bloat (the script handles this)
3. **WAL mode** — memory_store.db uses Write-Ahead Logging. The .db-wal file contains uncommitted data. The sqlite3 `.dump` command reads through WAL correctly, but raw file copy may miss recent writes.
4. **dedup/merge not available from Hermes** — MCP server supports them, but the Hermes wrapper doesn't expose them. Only Claude Code/Codex direct MCP connections can use these actions.
