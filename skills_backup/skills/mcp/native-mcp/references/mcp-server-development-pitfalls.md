# MCP Server Development Pitfalls

Lessons from building the Holographic Memory MCP Server (`~/.hermes/mcp-holographic/`).

## sql.js Limitations

### No FTS5 Support
`sql.js` (WebAssembly SQLite) does **NOT** compile FTS5. Using `CREATE VIRTUAL TABLE ... USING fts5()` throws `no such module: fts5`.

**Solution**: Use `LIKE '%query%'` for text search. If FTS5 is critical, use `better-sqlite3` (native binding) instead of `sql.js`.

### No File Locking
`sql.js` loads the entire DB into memory. It does NOT support SQLite's file-level locking. If another process (e.g., Hermes Holographic plugin using native SQLite) writes to the same `.db` file, data corruption or last-write-wins can occur.

**Mitigation**: Atomic writes via `writeFileSync(tmp) + renameSync(tmp, db)` prevent half-written files. Worst case is a lost write, not corruption.

### In-Memory Only Operations
All `db.run()` / `db.exec()` operate on the in-memory copy. You must explicitly call `saveDb()` to persist. Forgetting to save after writes = data loss on restart.

**Pattern**: Always `saveDb()` after write operations (INSERT/UPDATE/DELETE). Read-only operations that update metadata (like `retrieval_count`) also need `saveDb()`.

## saveDb() Atomic Write Pattern

```javascript
import { writeFileSync, renameSync } from "fs";

function saveDb() {
  if (!db) return;
  try {
    const data = db.export();
    const buffer = Buffer.from(data);
    const tmpPath = DB_PATH + '.tmp';
    writeFileSync(tmpPath, buffer);
    renameSync(tmpPath, DB_PATH);  // atomic on POSIX
  } catch (err) {
    throw new Error(`Persistence failed (memory updated but not saved to disk): ${err.message}`);
  }
}
```

**Key**: Use synchronous `renameSync`, NOT async `import('fs').then(fs => fs.renameSync(...))`. Async rename may not complete before `process.exit()` in signal handlers.

## Graceful Shutdown

```javascript
process.on('SIGINT', () => { saveDb(); process.exit(0); });
process.on('SIGTERM', () => { saveDb(); process.exit(0); });
process.on('uncaughtException', (err) => { console.error(err); saveDb(); process.exit(1); });
process.on('unhandledRejection', (reason) => { console.error(reason); saveDb(); process.exit(1); });
```

**Note**: If `saveDb()` itself fails (e.g., disk full), the exception is uncaught and process exits anyway. This is acceptable — the alternative (infinite loop) is worse.

## Entity Extraction Anti-Patterns

### Don't extract all Chinese words
`/[\u4e00-\u9fa5]{2,}/g` matches every 2+ character Chinese substring. "用户的项目是 slot-datamaking" produces entities like "用户的项目是" (verb phrase, not entity).

**Better approach**: Match specific patterns like "XX系统/项目/工具/框架" or mixed Chinese-English terms.

### Don't extract all capitalized words
`/[A-Z][a-z]+/g` matches sentence-initial words like "The", "This", "When".

**Better approach**: Filter against a stop word list (60+ common English words).

## Cleanup Script: Cascade Deletion

When deleting facts, always clean `fact_entities` FIRST:

```sql
-- Wrong: orphaned records remain
DELETE FROM facts WHERE trust_score < 0.3;

-- Right: clean associations first
DELETE FROM fact_entities WHERE fact_id IN (
  SELECT fact_id FROM facts WHERE trust_score < 0.3 AND created_at < datetime('now', '-30 days')
);
DELETE FROM facts WHERE trust_score < 0.3 AND created_at < datetime('now', '-30 days');
```

## Backup: SQL Dump, Not Binary

Pushing `.db` files to Git causes repo bloat (binary files can't diff). Use:

```bash
sqlite3 memory_store.db ".dump" > memory_store.sql
```

Add `*.db` to `.gitignore`.

## MCP stdio Transport Notes

- Server runs as subprocess, communicates via stdin/stdout
- `console.error()` for debug output (stdout is reserved for MCP protocol)
- Server lifecycle tied to the client connection
- Each tool call is synchronous from the agent's perspective
