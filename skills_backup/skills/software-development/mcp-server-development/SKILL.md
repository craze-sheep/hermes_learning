---
name: mcp-server-development
description: Build MCP servers to bridge AI tools with external systems — shared memory, databases, APIs.
triggers:
  - MCP server creation
  - shared memory across tools
  - bridge external systems to Claude Code/OpenCode/Codex
  - "让多个工具共享"
---

# MCP Server Development

Create MCP (Model Context Protocol) servers to share capabilities across AI tools.

## When to Use

- User wants multiple AI tools (Claude Code, OpenCode, Codex) to share data
- Need to bridge a Hermes plugin to other tools
- Need to expose database/API as tools

## Architecture

```
Claude Code ──┐
OpenCode ─────┼──→ MCP Server ──→ External System (DB, API, etc.)
Codex ────────┘
```

## Step-by-Step

### 1. Create Project

```bash
mkdir -p ~/.hermes/mcp-<name>
cd ~/.hermes/mcp-<name>
npm init -y
# Set "type": "module" in package.json for ES modules
npm install @modelcontextprotocol/sdk <dependencies>
```

### 2. Implement Server

```javascript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "server-name",
  version: "1.0.0",
});

// Define tools
server.tool("tool_name", "description", { /* zod schema */ }, async (params) => {
  // Implementation
  return { content: [{ type: "text", text: "result" }] };
});

// Start
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Server running on stdio");
}
main().catch(console.error);
```

### 3. Configure Tools

**Claude Code** (`~/.claude.json`):
```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",
      "command": "node",
      "args": ["/home/lzy/.hermes/mcp-<name>/index.js"]
    }
  }
}
```

**OpenCode** (`~/.config/opencode/opencode.json`):
```json
{
  "mcp": {
    "server-name": {
      "command": ["node", "/home/lzy/.hermes/mcp-<name>/index.js"],
      "enabled": true,
      "type": "local"
    }
  }
}
```

**Codex** (`~/.codex/config.toml`):
```toml
[mcp_servers.server-name]
type = "stdio"
command = "node"
args = ["/home/lzy/.hermes/mcp-<name>/index.js"]
```

### 4. Test

```bash
# Test initialization
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | timeout 5 node index.js

# Test tool call
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"tool_name","arguments":{...}}}' | timeout 5 node index.js
```

## Pitfalls

### ES Modules
- Set `"type": "module"` in package.json
- Use `import` not `require`
- Use `writeFileSync` not `fs.writeFile` for sync operations

### SQLite with sql.js
- sql.js is pure JS (WebAssembly), no compilation needed
- **sql.js does NOT support FTS5** — `CREATE VIRTUAL TABLE ... USING fts5(...)` throws `no such module: fts5`. Even reading existing FTS5 tables fails. This is a WASM build limitation. Use `LIKE` for search, or switch to `better-sqlite3` (native binding, supports FTS5).
- Must manually save database to file after writes: `const data = db.export(); writeFileSync(path, Buffer.from(data));`
- Default is in-memory database, must explicitly save to persist
- **saveDb() on read operations**: If a read operation updates metadata (e.g. `retrieval_count`), you MUST call saveDb() to persist those counters. Pure reads (list, probe without counters) don't need it.

### LIKE Search Pattern (sql.js)
```javascript
// Escape LIKE wildcards
function escapeLike(str) {
  return str.replace(/\\/g, '\\\\').replace(/%/g, '\\%').replace(/_/g, '\\_');
}
// Query with escaped input
db.run(`SELECT * FROM facts WHERE content LIKE ? ESCAPE '\\'`, [`%${escapeLike(query)}%`]);
```

### Backup Script Consistency (Critical)
When changing storage architecture (e.g., file-based → SQLite database), **immediately audit and update ALL dependent scripts**:
- Backup scripts (are they backing up the new DB file? Use SQL dump, not binary .db)
- Cleanup scripts (correct table/column names?)
- Monitoring scripts
- Cron jobs
- Don't wait for the user to catch inconsistencies — check proactively.

### Database Persistence
```javascript
// Save to file after every WRITE operation (not reads!)
// Use atomic write to prevent corruption on crash
function saveDb() {
  if (db) {
    const data = db.export();
    const buffer = Buffer.from(data);
    const tmpPath = DB_PATH + '.tmp';
    writeFileSync(tmpPath, buffer);
    renameSync(tmpPath, DB_PATH);  // atomic replace
  }
}
```
- Only call saveDb() after write operations (add, update, remove, feedback)
- Read operations that update metadata (e.g. `retrieval_count++` during search/probe) also need saveDb()
- Do NOT call saveDb() after pure reads with no side effects (list, contradict without counter updates)
- Use atomic write (tmp + rename) to prevent database corruption on crash

### LIKE Queries with sql.js
- sql.js LIKE needs explicit `ESCAPE '\\\\'` clause for `%` and `_` escaping
- Pattern: `WHERE col LIKE ? ESCAPE '\\\\'` with `%${escapeLike(query)}%`
- `escapeLike(str)` should escape `\\` first, then `%` and `_`
- **Prefer FTS5 MATCH over LIKE** — FTS5 is much faster for full-text search. Use LIKE only as fallback when FTS5 is unavailable.

### Backup Script Consistency (Critical)
When changing storage architecture (e.g., file-based → SQLite database), **immediately audit and update ALL dependent scripts**:
- Backup scripts (are they backing up the new DB file?)
- Cleanup scripts (correct table/column names?)
- Monitoring scripts
- Cron jobs
- Don't wait for the user to catch inconsistencies — check proactively.

### Graceful Shutdown & Error Handling
- Always add signal handlers to save database before exit:
```javascript
process.on('SIGINT', () => { saveDb(); process.exit(0); });
process.on('SIGTERM', () => { saveDb(); process.exit(0); });
process.on('uncaughtException', (err) => { console.error(err); saveDb(); process.exit(1); });
process.on('unhandledRejection', (reason) => { console.error(reason); saveDb(); process.exit(1); });
```

### Entity Extraction (for knowledge graph tools)
- Simple regex-based: quoted text, capitalized words, Chinese nouns (2+ chars)
- **Must filter stop words** — otherwise "The", "This", "可以", "已经" become entities
- English stop words (60+): articles, prepositions, conjunctions, pronouns
- Chinese stop words (100+): verbs, adjectives, adverbs, common function words
- For production: consider LLM-based extraction or jieba segmentation

### Dynamic UPDATE Construction
When updating multiple optional fields, build SQL dynamically:
```javascript
const updates = [];
const values = [];
if (params.content) { updates.push("content = ?"); values.push(params.content); }
if (params.category) { updates.push("category = ?"); values.push(params.category); }
if (params.trust_delta) { updates.push("trust_score = MAX(0, MIN(1, trust_score + ?))"); values.push(params.trust_delta); }
if (updates.length === 0) return { content: [{ type: "text", text: "No fields to update" }] };
updates.push("updated_at = CURRENT_TIMESTAMP");
values.push(id);
db.run(`UPDATE table SET ${updates.join(", ")} WHERE id = ?`, values);
```

### Contradict Detection (Knowledge Graph)
For detecting conflicting facts, use shared entities rather than matching tags:
```sql
SELECT f1.fact_id, f1.content, f1.trust_score,
       f2.fact_id, f2.content, f2.trust_score
FROM fact_entities fe1
JOIN fact_entities fe2 ON fe1.entity_id = fe2.entity_id AND fe1.fact_id < fe2.fact_id
JOIN facts f1 ON fe1.fact_id = f1.fact_id
JOIN facts f2 ON fe2.fact_id = f2.fact_id
WHERE ABS(f1.trust_score - f2.trust_score) > 0.3
GROUP BY f1.fact_id, f2.fact_id
LIMIT 10
```
This finds facts about the same entity with divergent trust scores — potential contradictions.

### Package Installation Timeouts
- npm install can timeout on slow connections
- Use timeout=300 for install commands
- If better-sqlite3 fails (needs compilation), use sql.js instead

### Input Validation
- Always check if referenced IDs exist before update/delete/feedback operations
- Return `isError: true` for missing resources

## Example: Holographic Memory Server

See `~/.hermes/mcp-holographic/index.js` for a complete example that:
- Bridges Hermes Holographic memory to all AI tools
- Uses sql.js for SQLite without compilation
- Implements 9 operations (add, search, probe, related, reason, contradict, update, remove, list)
- Auto-extracts entities from text
- Persists database to file after writes

## Config Locations

| Tool | Config Path |
|------|-------------|
| Claude Code | `~/.claude.json` (mcpServers) |
| OpenCode | `~/.config/opencode/opencode.json` (mcp) |
| Codex | `~/.codex/config.toml` (mcp_servers) |
