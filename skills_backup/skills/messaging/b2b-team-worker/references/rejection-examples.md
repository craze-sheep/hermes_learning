# B2B Worker Contract — Rejection Examples from Real Sessions

## Rejection Case 1: Worker Assignment Language (2026-05-31)

**Original rejected MESSAGE excerpt:**

```
[B2B-20260531-000923][Planner][REPORT]
@TeamSupervisor_bot

规划完成。已产出完整规划文档...

供 Supervisor 决策参考：下一步需要 Researcher 执行论文获取和逐篇分析。
建议按批次调度，每批5篇。
```

**Rejection reason:** "worker REPORT 正文不能直接安排、指挥或指定其他 worker"

**Fixed version:**

```
供 Supervisor 决策参考：后续环节需要论文获取能力（arXiv搜索+PDF下载+代码clone）、
深度论文分析能力（按7问模板填写）、跨论文横向对比能力、质量审查能力。
建议分4批×5篇执行。
```

**Key fix:** Replaced "Researcher 执行" with capability descriptions. Changed "建议按批次调度" to "可分...执行" (descriptive, not prescriptive).

## Rejection Case 2: Internal Document Headers (same session)

**Original (in plan document):**
```markdown
### 阶段 1：论文获取（Researcher 执行）
### 阶段 2：逐篇分析（Researcher 执行）
### 阶段 3：汇总对比表（Planner + Researcher 协作）
### 阶段 4：质量审查（Tester 执行）
```

**Fixed version:**
```markdown
### 阶段 1：论文获取
### 阶段 2：逐篇分析
### 阶段 3：汇总对比表
### 阶段 4：质量审查
```

**Lesson:** Even internal Markdown documents should not assign workers by name. Use capability-neutral descriptions.

## Rejection Case 3: Scheduling Language (same session)

**Original:**
```markdown
## 七、分批调度建议（供 Supervisor 决策参考）

后续执行环节需要的能力：

1. **Researcher — 论文获取批次：** 分4批，每批5篇。每批需要：arXiv/Semantic Scholar搜索 + PDF下载 + GitHub代码clone
2. **Researcher — 逐篇分析批次：** 可与论文获取并行，每批处理5篇，需要深度阅读论文PDF并填写7问模板
```

**Fixed version:**
```markdown
## 七、执行能力需求（供 Supervisor 决策参考）

后续环节需要以下能力：

1. **论文获取能力：** 需要 arXiv/Semantic Scholar 搜索 + PDF下载 + GitHub代码clone。可分4批×5篇。
2. **论文分析能力：** 需要深度阅读论文PDF并按7问模板填写结构化分析。可与论文获取并行。
```

**Key fix:** Removed "Researcher —" prefix from each capability. Changed from "调度建议" to "能力需求".
