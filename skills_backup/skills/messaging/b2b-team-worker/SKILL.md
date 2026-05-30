---
name: b2b-team-worker
description: "Telegram AI Team B2B worker contract rules. Load when receiving a task from Supervisor in a multi-agent Telegram group chat with roles (Planner/Researcher/Developer/Tester). Covers output format, forbidden patterns, and pitfalls that cause message rejection."
triggers:
  - "B2B task from Supervisor"
  - "Telegram AI Team worker assignment"
  - "[task_id][role][REPORT]"
  - "role_contract in job JSON"
  - "Supervisor ASSIGN message"
---

# B2B Team Worker Contract

When receiving a task as a **worker** (Planner/Researcher/Developer/Tester) in a Telegram AI Team B2B system, follow these rules strictly. Violations cause message rejection and rework.

## Output Format (MANDATORY)

Every worker MESSAGE must start exactly:

```
[B2B-YYYYMMDD-HHMMSS][YourRole][REPORT]
@TeamSupervisor_bot
your report body here
```

- Task ID comes from the job JSON (`job_id` field or extracted from `user_prompt`)
- Role comes from the job JSON (`role` field)
- Only `@TeamSupervisor_bot` may be mentioned — no other bots or workers

## Forbidden Patterns (INSTANT REJECTION)

These patterns cause the Telegram outbound filter to block your message:

| Pattern | Example | Why blocked |
|---------|---------|-------------|
| Wrong header | `[task][Planner][WORKING]` | Only REPORT allowed for workers |
| Wrong header | `[task][Planner][STATUS]` | Only REPORT allowed for workers |
| Wrong header | `[task][Planner][DONE]` | Only REPORT allowed for workers |
| Wrong header | `[task][Planner][ERROR]` | Only REPORT allowed for workers |
| Worker assignment | `下一步由 Researcher 执行` | Workers cannot assign other workers |
| Worker assignment | `请 Tester 继续` | Workers cannot assign other workers |
| Worker assignment | `负责人: Developer` | Workers cannot assign other workers |
| Direct @ of workers | `@other_bot please continue` | Can only @TeamSupervisor_bot |
| Managerial tone | `建议按批次调度Researcher` | Sounds like you're the manager |

## Allowed Patterns for Recommendations

Instead of assigning workers, describe **capability needs** for Supervisor to decide:

```
供 Supervisor 决策参考：后续需要论文获取能力（arXiv搜索+PDF下载），
以及深度论文分析能力（按模板填写7问分析）。
```

Key distinction:
- ❌ "下一步需要 Researcher 执行论文获取" (names a worker)
- ✅ "后续需要论文获取能力" (describes a capability)
- ❌ "建议按批次调度，每批5篇" (scheduling language)
- ✅ "可分4批×5篇执行" (describes a possible approach, not a command)

## Output Sections

The job prompt specifies exact output fields. Typically:

```
MESSAGE: [the Telegram-visible REPORT]
HANDOFF_SUMMARY: <=300 Chinese characters for Supervisor
```

Do NOT add unrelated chat, greetings, or meta commentary outside the requested schema.

## Artifact Rules

- Substantive results must be Markdown-archivable
- Code/config files use `FILE: relative/path.ext` with code block
- Paths must be relative (never `..`, absolute, or Windows drive prefixes)
- **When a real working directory is specified** in the job prompt, write substantive output THERE, not just in `artifacts/tasks/`

## Pitfalls Discovered

### 1. "描述能力需求" vs "安排工作"
The hardest line to walk. Training examples:

❌ "分4批执行，每批5篇。每批需要arXiv搜索+PDF下载+代码clone"
→ This reads as scheduling work for specific batches

✅ "后续环节需要论文获取能力（arXiv搜索+PDF下载+代码clone）、深度论文分析能力。执行粒度和批次划分供 Supervisor 决策。"
→ This describes WHAT capabilities are needed, leaves HOW to Supervisor

### 2. "Planner + Researcher 协作" in plan headers
Even internal document headers like `阶段3：汇总对比表（Planner + Researcher 协作）` assign roles. Use capability-neutral headers: `阶段3：汇总对比表`.

### 3. Supervisor username
The only allowed @ mention is the real Supervisor username from the job prompt. Usually `@TeamSupervisor_bot`. Never invent or guess.

### 4. Task ID preservation
Use the task ID from the original assignment (e.g., `B2B-20260531-000923`), not the planner's own job ID (e.g., `planner-20260531001007-xxx`). The task ID appears in the `[B2B-...][Supervisor][ASSIGN]` message.

### 5. Re-output after rejection
When asked to re-output due to contract violation:
- Fix ONLY the violation (usually wording)
- Keep all substantive content the same
- Don't re-plan from scratch
- Patch any internal documents that used forbidden patterns

## Skills That Complement This

- `literature-survey` — when the task involves paper research, load this skill for reference files and batch templates
- `plan` / `writing-plans` — for structuring implementation plans
- `brainstorming` — for ideation phases
