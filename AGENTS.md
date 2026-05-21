# Hermes Agent 自动记忆规则

## 概述

当 Claude Code、OpenCode、Codex 学到重要信息时，自动保存到共享记忆数据库。
所有工具通过 MCP 服务器（holographic）访问同一个数据库。

## 支持的操作

### 1. 添加事实 — add
```json
{"action": "add", "content": "事实描述", "category": "类别", "tags": "标签1,标签2"}
```

### 2. 搜索事实 — search
```json
{"action": "search", "query": "关键词", "min_trust": 0.3, "limit": 10}
```

### 3. 探查实体 — probe
查询某实体的所有已知事实：
```json
{"action": "probe", "entity": "实体名称"}
```

### 4. 关联查询 — related
查询与某实体相关的其他实体：
```json
{"action": "related", "entity": "实体名称"}
```

### 5. 组合推理 — reason
查询多个实体的交集事实：
```json
{"action": "reason", "entities": ["实体1", "实体2"]}
```

### 6. 矛盾检测 — contradict
检查记忆中的冲突信息：
```json
{"action": "contradict"}
```

### 7. 更新事实 — update
```json
{"action": "update", "fact_id": 123, "content": "新描述", "category": "类别", "tags": "标签"}
```

### 8. 删除事实 — remove
```json
{"action": "remove", "fact_id": 123}
```

### 9. 列出全部 — list
```json
{"action": "list", "min_trust": 0.3, "limit": 20}
```

### 10. 反馈事实 — fact_feedback（独立工具）
> **注意：`fact_feedback` 是独立的 MCP 工具，不是 `fact_store` 的 action。**
> 调用方式：使用 `fact_feedback` 工具，传入 `action` 和 `fact_id` 参数。
```json
// 调用 fact_feedback 工具（不是 fact_store）
{"action": "helpful", "fact_id": 123}
{"action": "unhelpful", "fact_id": 123}
```

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

## 自动写入触发条件

### 1. 用户明确指示
当用户说以下词语时，使用 `fact_store` 工具保存：
- "记住..."
- "记一下..."
- "保存这个..."
- "记住了吗..."

### 2. 用户纠正信息
当用户纠正错误信息时，自动保存正确信息：
- 用户说"不对，应该是..."
- 用户说"错了，正确的是..."
- 用户说"我之前说错了..."

### 3. 学到用户偏好
当发现以下信息时，自动保存：
- 语言偏好（中文/英文）
- 回答风格（简洁/详细）
- 工具偏好（VSCode/终端）
- 工作习惯（时间、频率）

### 4. 学到环境信息
当发现以下信息时，自动保存：
- 操作系统、环境配置
- 安装的工具、版本
- 项目结构、技术栈
- 网络、代理配置

### 5. 学到项目信息
当发现以下信息时，自动保存：
- 项目名称、描述
- 技术栈、依赖
- 重要配置、约定
- 当前进度、计划

### 6. 完成重要配置
当完成以下操作时，自动保存：
- 安装新工具
- 配置环境变量
- 修改配置文件
- 解决技术问题

### 7. 会话结束前
- 总结本次会话的重要发现
- 保存新学到的环境/项目信息

## 使用场景矩阵

| 用户问的问题 | 应该用的动作 |
|-------------|-------------|
| "我的项目是什么？" | search |
| "关于我的所有信息" | probe |
| "X 和 Y 有什么关系？" | reason |
| "检查记忆有没有矛盾" | contradict |
| "删掉这条" | remove |
| "列出所有记忆" | list |
| "更新这条信息" | update |
| "这个信息有用" | fact_feedback helpful |
| "这个信息过时了" | fact_feedback unhelpful |

## 写入格式

```json
{
  "action": "add",
  "content": "事实描述",
  "category": "类别",
  "tags": "标签1,标签2"
}
```

### 类别说明
| 类别 | 说明 | 示例 |
|------|------|------|
| user_pref | 用户偏好 | "用户喜欢简洁回答" |
| project | 项目信息 | "项目使用 React + TypeScript" |
| tool | 工具配置 | "Claude Code 使用 mimo-v2.5-pro" |
| general | 一般信息 | "用户使用 WSL 环境" |

### 标签规范
- 使用英文小写
- 多个标签用逗号分隔
- 保持简洁（2-4 个标签）

## 查询规则

### 回答用户问题前
在回答关于以下主题的问题前，先查询记忆：
- 用户信息（名字、偏好、习惯）
- 项目信息（配置、进度、问题）
- 环境信息（工具、配置、限制）
- 历史信息（之前做过什么、学到什么）

### 查询方式
```json
{"action": "search", "query": "关键词"}
```

## 更新规则

### 信息变化时
当发现信息变化时，使用 `update` 更新：
```json
{"action": "update", "fact_id": 123, "content": "新的描述"}
```

### 信息过时时
当发现信息过时时，降低信任度：
```json
{"action": "update", "fact_id": 123, "trust_delta": -0.2}
```

## 反馈规则

### 使用记忆后（调用独立工具 fact_feedback）
使用记忆回答问题后，调用 `fact_feedback` 工具反馈是否有用：
```json
// 调用 fact_feedback 工具（不是 fact_store 的 action）
{"action": "helpful", "fact_id": 123}
```

### 信息不准确时（调用独立工具 fact_feedback）
发现记忆不准确时，调用 `fact_feedback` 工具反馈并更新：
```json
// 调用 fact_feedback 工具（不是 fact_store 的 action）
{"action": "unhelpful", "fact_id": 123}
```

## 示例

### 示例 1：用户纠正
```
用户：我的项目不是 React，是 Vue
Claude Code：
1. 调用 fact_store search "项目"
2. 找到错误的事实
3. 调用 fact_store update 更新
4. 回答用户
```

### 示例 2：学到偏好
```
用户：回答简洁点
Claude Code：
1. 调用 fact_store add
2. content: "用户喜欢简洁回答"
3. category: "user_pref"
4. tags: "style,preference"
```

### 示例 3：查询后回答
```
用户：我的项目是什么？
Claude Code：
1. 调用 fact_store search "项目"
2. 找到相关事实
3. 回答用户
4. 调用 fact_feedback 工具（独立工具，不是 fact_store 的 action）
```

### 示例 4：实体查询
```
用户：关于 Hermes 的所有信息
Claude Code：
1. 调用 fact_store probe entity="Hermes"
2. 返回所有相关事实
3. 回答用户
```

### 示例 5：组合推理
```
用户：WSL 和 Claude Code 有什么关系？
Claude Code：
1. 调用 fact_store reason entities=["WSL", "Claude Code"]
2. 返回交集事实
3. 回答用户
```

## 注意事项

1. **不要重复保存** — 先查询是否已存在
2. **保持简洁** — 事实描述要精炼
3. **及时更新** — 信息变化时更新
4. **正确反馈** — 使用后反馈是否有用
5. **隐私保护** — 不保存敏感信息（密码、token）
6. **定期清理** — 使用 contradict 检查矛盾信息
7. **信任评分** — 重要信息提高信任度，过时信息降低信任度
