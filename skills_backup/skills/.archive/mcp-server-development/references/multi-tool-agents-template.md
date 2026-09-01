# Multi-Tool AGENTS.md Template

When setting up shared MCP memory across multiple AI tools, each tool needs an instruction file explaining how to use the memory. This template ensures consistency.

## File Locations

| Tool | File | Format |
|------|------|--------|
| Hermes | `~/.hermes/AGENTS.md` | Markdown |
| Claude Code | `~/.claude/CLAUDE.md` | Markdown |
| Codex | `~/.codex/AGENTS.md` | Markdown |
| OpenCode | `~/.config/opencode/AGENTS.md` | Markdown |

## Template (Read-Write Separated)

```markdown
# [Tool Name] 共享记忆规则（Holographic Memory）

## 概述

Hermes、Claude Code、Codex、OpenCode 共享同一个记忆数据库（~/.hermes/memory_store.db）。
通过 holographic MCP 服务器访问，**读写分离**：

| 工具 | 用途 | 权限 |
|------|------|------|
| `fact_query` | 查询记忆 | 只读（search/probe/related/reason/contradict/list） |
| `fact_store` | 写入记忆 | 读写（add/update/remove） |
| `fact_feedback` | 反馈记忆质量 | 独立工具 |

## 何时使用

1. **用户说"记住"、"记一下"、"保存"** → `fact_store` add
2. **用户纠正错误信息** → `fact_store` update
3. **学到用户偏好/环境信息/项目信息** → `fact_store` add
4. **回答用户问题前** → 先 `fact_query` search
5. **使用记忆后** → `fact_feedback` helpful/unhelpful

## 只读查询 — fact_query

| 操作 | 说明 | 示例 |
|------|------|------|
| search | 关键词搜索 | `{"action":"search","query":"WSL"}` |
| probe | 查询实体所有事实 | `{"action":"probe","entity":"Claude Code"}` |
| related | 查询相关实体 | `{"action":"related","entity":"Hermes"}` |
| reason | 多实体交集推理 | `{"action":"reason","entities":["WSL","Docker"]}` |
| contradict | 检测矛盾信息 | `{"action":"contradict"}` |
| list | 列出全部事实 | `{"action":"list","limit":20}` |

## 写入操作 — fact_store

| 操作 | 说明 | 示例 |
|------|------|------|
| add | 添加新事实 | `{"action":"add","content":"用户喜欢简洁回答","category":"user_pref","tags":"style"}` |
| update | 更新已有事实 | `{"action":"update","fact_id":123,"content":"新描述"}` |
| remove | 删除事实 | `{"action":"remove","fact_id":123}` |

## 反馈 — fact_feedback（独立工具）

| 操作 | 说明 |
|------|------|
| helpful | 记忆准确有用 |
| unhelpful | 记忆不准确/过时 |

## 参数说明

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| content | string | 事实描述 | - |
| query | string | 搜索关键词 | - |
| entity | string | 实体名称 | - |
| entities | string[] | 实体名称数组 | - |
| fact_id | number | 事实 ID | - |
| category | string | 类别（user_pref/project/tool/general） | general |
| tags | string | 标签（逗号分隔） | - |
| min_trust | number | 最低信任度 | 0.3 |
| limit | number | 最大返回数量 | 10 |
| trust_delta | number | 信任度调整值 | - |

## 类别说明

| 类别 | 说明 | 示例 |
|------|------|------|
| user_pref | 用户偏好 | "用户喜欢简洁回答" |
| project | 项目信息 | "项目使用 Kubric 物理仿真" |
| tool | 工具配置 | "Codex 使用 GPT-5.5" |
| general | 一般信息 | "用户使用 WSL 环境" |

## 自动写入触发条件

1. 用户明确指示（"记住"、"记一下"、"保存"）
2. 用户纠正错误信息
3. 学到用户偏好/环境信息/项目信息
4. 完成重要配置
5. 会话结束前

## 使用场景矩阵

| 用户问的问题 | 用哪个工具 | 动作 |
|-------------|-----------|------|
| "我的项目是什么？" | fact_query | search |
| "关于我的所有信息" | fact_query | probe |
| "X 和 Y 有什么关系？" | fact_query | reason |
| "记住这个" | fact_store | add |
| "更新这条信息" | fact_store | update |
| "这个信息有用" | fact_feedback | helpful |

## 注意事项

1. 先 `fact_query` search 再添加，避免重复
2. 事实描述要精炼
3. 不保存密码/token等敏感信息
4. 信息过时时用 `fact_store` update 更新
```

## Customization

- **Language**: Adapt to user's language (Chinese/English)
- **Verbosity**: Claude Code version can be shorter (just key operations), Codex/OpenCode/Hermes get full version
- **Categories**: Adjust category examples to match user's domain
- **Triggers**: Add domain-specific triggers (e.g., "学到项目信息" for project work)

## Deployment Checklist

1. Write instruction files to all 4 locations
2. Verify MCP server is configured in all 4 tool configs
3. Test `fact_query` from each tool (read-only should work everywhere)
4. Test `fact_store` from Hermes (always works, no sandbox)
5. For Codex: verify `readOnlyHint: true` on fact_query tool
6. Delete old memory files (`~/.hermes/memories/MEMORY.md`, `~/.hermes/memories/USER.md`) to prevent prompt injection
