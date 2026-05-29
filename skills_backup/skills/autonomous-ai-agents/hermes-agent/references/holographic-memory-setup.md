# Holographic Memory Setup Across AI Tools

Shared memory database: `~/.hermes/memory_store.db` (SQLite)
MCP server: `~/.hermes/mcp-holographic/index.js`

## Architecture: Read-Write Separation

The holographic MCP exposes three tools with distinct permissions:

| Tool | Operations | Annotation | Why |
|------|-----------|------------|-----|
| `fact_query` | search, probe, related, reason, contradict, list | `readOnlyHint: true` | Codex can call without approval hooks |
| `fact_store` | add, update, remove | `destructiveHint: true` | Write operations need client approval |
| `fact_feedback` | helpful, unhelpful | `destructiveHint: true` | Independent feedback tool |

This split lets clients apply different approval policies — reads bypass PermissionRequest, writes may require user confirmation.

## Step 1: Add holographic MCP to each tool

### Claude Code (`~/.claude.json`)
```json
"mcpServers": {
  "holographic": {
    "type": "stdio",
    "command": "node",
    "args": ["/home/lzy/.hermes/mcp-holographic/index.js"]
  }
}
```

### Codex (`~/.codex/config.toml`)
```toml
[mcp_servers.holographic]
type = "stdio"
command = "node"
args = ["/home/lzy/.hermes/mcp-holographic/index.js"]
```

### OpenCode (`~/.config/opencode/opencode.json`)
```json
{
  "mcp": {
    "holographic": {
      "command": ["node", "/home/lzy/.hermes/mcp-holographic/index.js"],
      "enabled": true,
      "type": "local"
    }
  }
}
```

## Step 2: Add usage instructions

Without instructions, tools don't know WHEN to call `fact_store`. Copy `~/.hermes/AGENTS.md` to each tool's location:

| Tool | Instruction File |
|------|-----------------|
| Hermes | `~/.hermes/AGENTS.md` (canonical source) |
| Claude Code | `~/.claude/CLAUDE.md` (can be shorter, just holographic section) |
| Codex | `~/.codex/AGENTS.md` (full copy) |
| OpenCode | `~/.config/opencode/AGENTS.md` (full copy) |

## Step 3: Verify

```bash
# Check DB has data
python3 -c "import sqlite3; c=sqlite3.connect('$HOME/.hermes/memory_store.db'); print(c.execute('SELECT COUNT(*) FROM facts').fetchone()[0])"

# Check MCP server responds
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | timeout 5 node ~/.hermes/mcp-holographic/index.js
```

## Pitfall: MCP server ≠ usage instructions

Installing the holographic MCP server only makes the tools AVAILABLE. The tools still need instruction files (AGENTS.md/CLAUDE.md) to know:
- When to write (user says "记住", user corrects info, learns new fact)
- When to search (before answering user questions about past context)
- How to use fact_feedback (after using a fact to answer)

Without instructions, the tools will have the `fact_store` tool but never call it.

## Claude Code CLAUDE.md (minimal version)

```markdown
# Claude Code 全局指令

## 共享记忆系统（Holographic Memory）

你有 `holographic` MCP 服务器，连接到共享记忆数据库（~/.hermes/memory_store.db）。
Hermes、Codex、OpenCode 也使用同一个数据库。**读写分离**：

| 工具 | 用途 | 权限 |
|------|------|------|
| `fact_query` | 查询记忆 | 只读（search/probe/related/reason/contradict/list） |
| `fact_store` | 写入记忆 | 读写（add/update/remove） |
| `fact_feedback` | 反馈记忆质量 | 独立工具 |

### 何时使用

1. **用户说"记住"、"记一下"、"保存"** → `fact_store` add
2. **用户纠正错误信息** → `fact_store` update
3. **学到用户偏好/环境信息/项目信息** → `fact_store` add
4. **回答用户问题前** → 先 `fact_query` search
5. **使用记忆后** → `fact_feedback` helpful/unhelpful

### 只读查询 — fact_query

- 搜索：`fact_query(action="search", query="关键词")`
- 探查：`fact_query(action="probe", entity="实体名")`
- 关联：`fact_query(action="related", entity="实体名")`
- 推理：`fact_query(action="reason", entities=["实体1","实体2"])`
- 矛盾：`fact_query(action="contradict")`
- 列表：`fact_query(action="list")`

### 写入操作 — fact_store

- 添加：`fact_store(action="add", content="事实", category="类别", tags="标签")`
- 更新：`fact_store(action="update", fact_id=123, content="新内容")`
- 删除：`fact_store(action="remove", fact_id=123)`

### 反馈 — fact_feedback（独立工具）

- 有用：`fact_feedback(action="helpful", fact_id=123)`
- 过时：`fact_feedback(action="unhelpful", fact_id=123)`
```

## Pitfall: memory_enabled ≠ file injection

Setting `memory_enabled: false` and `disabled_toolsets: ["memory"]` in config.yaml only disables the **memory tool** (the ability to read/write MEMORY.md/USER.md). The MEMORY.md and USER.md files in `~/.hermes/memories/` are **still injected into the system prompt** as context.

To fully remove old memory from the prompt:
1. Migrate all facts from MEMORY.md/USER.md to holographic DB (compare, add missing)
2. Backup old files (`mv MEMORY.md MEMORY.md.bak`)
3. Delete or empty the files
4. Verify with a new session that the prompt no longer contains old memory content

## Pitfall: Instruction file sync

When adding new MCP tools (e.g., `fact_query` for read-write separation), you MUST update ALL FOUR instruction files:

| File | Tool |
|------|------|
| `~/.hermes/AGENTS.md` | Hermes |
| `~/.claude/CLAUDE.md` | Claude Code |
| `~/.codex/AGENTS.md` | Codex |
| `~/.config/opencode/AGENTS.md` | OpenCode |

If you only update one, the other tools will still reference the old tool names and call patterns.

## Pitfall: Residual MCP entries after removal

When removing MCP servers (e.g., old `memory` or `time`), config files may retain stale entries even after you think you've removed them. **Always verify after cleanup:**

```bash
# Claude Code — check for stale MCP servers
python3 -c "import json; d=json.load(open('$HOME/.claude.json')); print(list(d.get('mcpServers',{}).keys()))"

# Codex — check for stale [mcp_servers.xxx] sections
grep '\[mcp_servers\.' ~/.codex/config.toml

# OpenCode — check MCP list
python3 -c "import json; d=json.load(open('$HOME/.config/opencode/opencode.json')); print(list(d.get('mcp',{}).keys()))"
```

Known issue: Claude Code's `~/.claude.json` can retain `memory` and `time` MCP servers after removal. Codex's `config.toml` can retain `[mcp_servers.memory]` sections. These stale entries don't cause errors but waste startup time and may confuse future audits. Use `grep` or `python3 -c` to verify cleanup is complete.

## Migration workflow (old memory → holographic)

When consolidating from file-based memory (MEMORY.md/USER.md) to holographic DB:

1. `fact_store(action="list", limit=100, min_trust=0)` — see what's already in DB
2. Read old MEMORY.md and USER.md
3. Compare content — identify facts in old files but NOT in DB
4. `fact_store(action="add", ...)` for each missing fact
5. `fact_store(action="update", ...)` for facts that need more detail
6. Backup old files: `mv MEMORY.md MEMORY.md.bak`
7. Delete: `rm MEMORY.md.bak` (after confirming new session works)

## Pitfall: Codex sandbox blocks fact_store writes

`fact_store` (destructiveHint) and `fact_feedback` (destructiveHint) are blocked by Codex's `workspace-write` sandbox mode — the MCP tool call gets "user cancelled". `fact_query` (readOnlyHint) works fine.

**Implication**: Codex can only READ from holographic memory. Write operations must go through Hermes or Claude Code. This is by design — Codex's sandbox prevents destructive MCP operations.

If you need Codex to write facts, use `delegate_task` to have Hermes do the write on Codex's behalf.

## Backup & Maintenance

See `references/holographic-memory-backup-maintenance.md` for:
- Daily backup to GitHub (script + sqlite3 dependency)
- Monthly cleanup of low-trust/expired facts
- Dedup/merge gap (MCP server supports it, Hermes wrapper doesn't)
