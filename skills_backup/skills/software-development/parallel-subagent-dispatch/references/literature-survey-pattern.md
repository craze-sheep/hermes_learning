# Literature Survey with Subagents

Reusable workflow for large-scale literature research using parallel subagents.

## Workflow

1. **Phase 1: Analyze current model** (1 subagent or manual)
   - Read all existing code
   - Write `00_current_model_analysis.md`

2. **Phase 2: Research papers** (many subagents, 1 paper each)
   - Dispatch 3 subagents per batch (max_concurrent_children=3)
   - Each subagent: search → read → write note → 1 paper
   - Quality check after each batch
   - ~17 batches for 50 papers

3. **Phase 3: Write summary** (3 subagents in parallel)
   - Subagent 1: Paper list part 1 (directions 1-4)
   - Subagent 2: Paper list part 2 (directions 5-8)
   - Subagent 3: Comparison tables (architecture, loss, training)
   - Merge into single `01_literature_survey_summary.md`

4. **Phase 4: Write proposals** (2 subagents in parallel)
   - Subagent 1: Per-module optimization suggestions
   - Subagent 2: Priority ranking + iteration plan
   - Merge into single `02_optimization_proposals.md`

## Context Template for Paper Research Subagent

```
当前模型概览：[1-2 sentences about architecture]
与当前模型相关性：[why this paper matters]

目标：调研论文 "[Title]" ([Author], [Venue] [Year], arXiv:[ID])，撰写详细笔记。
写入 /path/to/papers/NNN_shortname.md

格式：基本信息、核心贡献、模型架构（Encoder/Decoder/交互/时序）、损失函数、关键设计选择、与当前模型对比、可借鉴的点、实验结果
```

Keep context under 200 words. Longer context causes interruptions.

## Pitfalls

- **Don't combine multiple papers in one subagent** — causes timeout
- **Don't give vague directions** ("research GNN papers") — give specific paper titles
- **Check arXiv IDs** — some are wrong in user prompts, verify first
- **Semantic Scholar has rate limits** (429) — subagent should handle gracefully
- **mcp_fetch_fetch often fails** on arxiv — subagent should use terminal + curl as fallback
