# Holographic Memory Setup Across AI Tools

Shared memory database: `~/.hermes/memory_store.db` (SQLite)
MCP server: `~/.hermes/mcp-holographic/index.js`

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
Hermes、Codex、OpenCode 也使用同一个数据库。

### 何时使用 fact_store

1. **用户说"记住"、"记一下"、"保存"** → `fact_store add`
2. **用户纠正错误信息** → `fact_store update`
3. **学到用户偏好/环境信息/项目信息** → `fact_store add`
4. **回答用户问题前** → 先 `fact_store search` 查询记忆
5. **使用记忆后** → `fact_feedback helpful/unhelpful`

### 常用操作

- 搜索：`fact_store(action="search", query="关键词")`
- 探查：`fact_store(action="probe", entity="实体名")`
- 添加：`fact_store(action="add", content="事实", category="user_pref|project|tool|general", tags="标签")`
- 更新：`fact_store(action="update", fact_id=123, content="新内容")`
- 反馈：`fact_feedback(action="helpful", fact_id=123)`
```
