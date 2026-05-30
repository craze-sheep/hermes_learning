# Codex 共享记忆规则（Holographic Memory）

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

## 标签规范

- 使用英文小写
- 多个标签用逗号分隔
- 保持简洁（2-4 个标签）

## 自动写入触发条件

### 1. 用户明确指示
当用户说以下词语时，使用 `fact_store` add 保存：
- "记住..."
- "记一下..."
- "保存这个..."
- "记住了吗..."

### 2. 用户纠正信息
当用户纠正错误信息时，使用 `fact_store` update 保存正确信息：
- "不对，应该是..."
- "错了，正确的是..."
- "我之前说错了..."

### 3. 学到用户偏好
语言偏好（中文/英文）、回答风格（简洁/详细）、工具偏好、工作习惯。

### 4. 学到环境信息
操作系统、环境配置、安装的工具/版本、项目结构、技术栈、网络配置。

### 5. 学到项目信息
项目名称/描述、技术栈/依赖、重要配置/约定、当前进度/计划。

### 6. 完成重要配置
安装新工具、配置环境变量、修改配置文件、解决技术问题。

### 7. 会话结束前
总结本次会话的重要发现，保存新学到的环境/项目信息。

## 使用场景矩阵

| 用户问的问题 | 用哪个工具 | 动作 |
|-------------|-----------|------|
| "我的项目是什么？" | fact_query | search |
| "关于我的所有信息" | fact_query | probe |
| "X 和 Y 有什么关系？" | fact_query | reason |
| "检查记忆有没有矛盾" | fact_query | contradict |
| "列出所有记忆" | fact_query | list |
| "记住这个" | fact_store | add |
| "更新这条信息" | fact_store | update |
| "删掉这条" | fact_store | remove |
| "这个信息有用" | fact_feedback | helpful |
| "这个信息过时了" | fact_feedback | unhelpful |

## 查询规则

回答以下主题的问题前，先 `fact_query` search：
- 用户信息（名字、偏好、习惯）
- 项目信息（配置、进度、问题）
- 环境信息（工具、配置、限制）
- 历史信息（之前做过什么、学到什么）

## 反馈规则

使用记忆回答问题后，调用 `fact_feedback` 反馈：
- 准确有用 → `{"action":"helpful","fact_id":123}`
- 不准确/过时 → `{"action":"unhelpful","fact_id":123}`

## 注意事项

1. **不要重复保存** — 先 `fact_query` search 是否已存在
2. **保持简洁** — 事实描述要精炼
3. **及时更新** — 信息变化时 `fact_store` update
4. **正确反馈** — 使用后 `fact_feedback`
5. **隐私保护** — 不保存敏感信息（密码、token）
6. **定期清理** — 使用 `fact_query` contradict 检查矛盾
7. **信任评分** — 重要信息提高信任度，过时信息降低信任度

<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`codegraph_*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. Reads are sub-millisecond and return structural information grep cannot.

### When to prefer codegraph over native search

Use codegraph for **structural** questions — what calls what, what would break, where is X defined, what is X's signature. Use native grep/read only for **literal text** queries (string contents, comments, log messages) or after you already have a specific file open.

| Question | Tool |
|---|---|
| "Where is X defined?" / "Find symbol named X" | `codegraph_search` |
| "What calls function Y?" | `codegraph_callers` |
| "What does Y call?" | `codegraph_callees` |
| "How does X reach/become Y? / trace the flow from X to Y" | `codegraph_trace` (one call = the whole path, incl. callback/React/JSX dynamic hops) |
| "What would break if I changed Z?" | `codegraph_impact` |
| "Show me Y's signature / source / docstring" | `codegraph_node` |
| "Give me focused context for a task/area" | `codegraph_context` |
| "See several related symbols' source at once" | `codegraph_explore` |
| "What files exist under path/" | `codegraph_files` |
| "Is the index healthy?" | `codegraph_status` |

### Rules of thumb

- **Answer directly — don't delegate exploration.** For "how does X work" / architecture questions, answer with 2-3 codegraph calls: `codegraph_context` first, then ONE `codegraph_explore` for the source of the symbols it surfaces. For a specific **flow** ("how does X reach Y") start with `codegraph_trace` from→to — one call returns the whole path with dynamic hops bridged — then ONE `codegraph_explore` for the bodies; don't rebuild the path with `codegraph_search` + `codegraph_callers`. Codegraph IS the pre-built index, so spawning a separate file-reading sub-task/agent — or running a grep + read loop — repeats work codegraph already did and costs more for the same answer.
- **Trust codegraph results.** They come from a full AST parse. Do NOT re-verify them with grep — that's slower, less accurate, and wastes context.
- **Don't grep first** when looking up a symbol by name. `codegraph_search` is faster and returns kind + location + signature in one call.
- **Don't chain `codegraph_search` + `codegraph_node`** when you just want context — `codegraph_context` is one call.
- **Don't loop `codegraph_node` over many symbols** — one `codegraph_explore` call returns several symbols' source grouped in a single capped call, while each separate node/Read call re-reads the whole context and costs far more.
- **Index lag — check the staleness banner, don't guess a wait.** When a codegraph response starts with "⚠️ Some files referenced below were edited since the last index sync…", the listed files are pending re-index — Read those specific files for accurate content. Files NOT in that banner are fresh and codegraph is authoritative for them. `codegraph_status` also lists pending files under "Pending sync".

### If `.codegraph/` doesn't exist

The MCP server returns "not initialized." Ask the user: *"I notice this project doesn't have CodeGraph initialized. Want me to run `codegraph init -i` to build the index?"*
<!-- CODEGRAPH_END -->
