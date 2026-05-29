# Holographic Memory Backup & Maintenance

## Backup to GitHub

Script: `~/.hermes/scripts/backup_to_github.sh`
Repo: `https://github.com/craze-sheep/hermes_learning.git`

### What gets backed up
- Config files (`*.yaml`, `*.json`, `*.toml`)
- Skills directory (`~/.hermes/skills/`)
- MCP holographic server source (index.js, package.json — NOT node_modules)
- `memory_store.db` → exported as `memory_store.sql` (SQL dump, not binary)
- AGENTS.md
- Cron config

### Critical dependency: sqlite3
The script uses `sqlite3` CLI to dump the database. **If sqlite3 is not installed, the database is silently skipped** — the backup "succeeds" but memory data is NOT included.

```bash
sudo apt install sqlite3  # Required for memory backup
```

Verify: `sqlite3 --version`

### Schedule
- System crontab: `0 3 * * *` (daily 3am)
- Hermes cron job `memory-backup-github` (ID: `198e7e841282`) as fallback

### Pitfall: System crontab misses runs
If the computer is off/sleeping at 3am, the backup is skipped with no catch-up.
**Solution**: Use Hermes cron (auto-catches missed runs on startup).

## Monthly Cleanup

Script: `~/.hermes/scripts/cleanup_memory.sh`
Schedule: Hermes cron `memory-cleanup-monthly` (1st of month, 4am)

### What it does
1. Backs up DB to `memory_store.db.backup.<timestamp>`
2. Deletes facts with `trust_score < 0.3` AND `created_at > 30 days`
3. Deletes facts with `trust_score < 0.5` AND `created_at > 90 days`
4. Cleans orphaned `fact_entities` and `entities`
5. Logs to `~/.hermes/logs/memory_cleanup.log`

## Weekly Curator (Skills Only)

System crontab: `0 2 * * 0 hermes curator run`
This reviews **skills**, NOT memory facts. It prunes/consolidates stale skills.

## Dedup/Merge Gap

The MCP holographic server (`~/.hermes/mcp-holographic/index.js`) supports:
- `dedup` action — find/merge duplicate facts (Jaccard similarity)
- `merge` action — manually merge two facts by ID

**But** Hermes's `fact_store` tool wrapper (`plugins/memory/holographic/__init__.py`) does NOT expose these actions. Calling `fact_store(action="dedup")` returns "Unknown action".

Claude Code / Codex / OpenCode (direct MCP clients) CAN use dedup/merge.
Hermes cannot — it goes through the wrapper which filters actions.

### Workaround
To run dedup from Hermes, use terminal to call the MCP server directly, or use `delegate_task` to have Claude Code do it.

## Verify backup is working

```bash
# Check if memory_store.sql exists in GitHub repo
cd /tmp && git clone https://github.com/craze-sheep/hermes_learning.git check 2>/dev/null
ls -la check/memory_store.sql && echo "✅ Memory backup exists" || echo "❌ Memory NOT backed up"
rm -rf check

# Check sqlite3 is installed
sqlite3 --version
```
