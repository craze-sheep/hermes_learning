# sql.js Limitations & Migration Paths

## What is sql.js?

sql.js is a WebAssembly (WASM) build of SQLite. It runs entirely in JavaScript/Node.js without native compilation, making it portable and easy to install. However, the WASM build is compiled with a subset of SQLite features.

## Known Limitations

### ❌ No FTS5 (Full-Text Search)

**Critical**: The WASM build does NOT include the FTS5 extension.

```js
// This WILL throw "no such module: fts5"
db.run("CREATE VIRTUAL TABLE fts USING fts5(content)");
```

Even reading from FTS5 tables created by native SQLite fails. The entire FTS5 module is absent from the WASM binary.

**Workaround**: Use `LIKE '%query%'` with proper escaping. For better performance, switch to `better-sqlite3`.

### ❌ No SQLite Encryption Extension (SEE/SQLCipher)

sql.js does not support encrypted databases.

### ⚠️ No File Locking

sql.js loads the entire database into memory. There is no file-level locking, so concurrent access from multiple processes (e.g., native SQLite + sql.js) can corrupt data.

**Workaround**: Ensure only one process writes to the database at a time.

### ⚠️ Full Database in Memory

Every `initDb()` call reads the entire .db file into WASM memory. For large databases (>100MB), this causes high memory usage and slow startup.

### ⚠️ Manual Persistence

Unlike native SQLite, sql.js does not auto-save. You must explicitly call `db.export()` + `writeFileSync()` after every write operation.

## Migration to better-sqlite3

If you need FTS5, file locking, or better performance:

```bash
npm install better-sqlite3
```

```js
import Database from 'better-sqlite3';
const db = new Database(DB_PATH);  // native SQLite, all features available
db.pragma('journal_mode = WAL');   // better concurrency
```

**Trade-offs**:
- ✅ FTS5, JSON1, R*Tree extensions
- ✅ File locking (WAL mode)
- ✅ Direct file access (no in-memory copy)
- ❌ Requires native compilation (node-gyp, Python, C++ compiler)
- ❌ May fail in restricted environments (Docker without build tools, some CI)

## Decision Matrix

| Requirement | sql.js | better-sqlite3 |
|------------|--------|----------------|
| Zero native deps | ✅ | ❌ |
| FTS5 search | ❌ | ✅ |
| File locking | ❌ | ✅ |
| Large DBs (>100MB) | ❌ | ✅ |
| Browser compatible | ✅ | ❌ |
| WASM/Edge runtime | ✅ | ❌ |
