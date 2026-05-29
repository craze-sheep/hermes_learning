---
name: ml-model-evaluation
description: "Evaluate ML model architectures against mainstream approaches — read codebase, compare with reference repos, search latest papers, write structured optimization suggestions with ablation experiments."
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [ML, research, model-evaluation, architecture-analysis, optimization, deep-learning]
---

# ML Model Evaluation & Optimization Analysis

Evaluate an ML model's architecture design and implementation against mainstream approaches from literature and open-source repos. Produce structured optimization suggestions with prioritized recommendations.

## When to Use

- User asks to evaluate/review/analyze an ML model's design
- User wants to compare their model with state-of-the-art approaches
- User asks for optimization suggestions on a model architecture
- User wants to identify gaps between their implementation and best practices

## Workflow

### Phase 1: Context Gathering (parallel)

Read these in parallel via `delegate_task` with 3 subtasks:

**Subtask A — Model Code Analysis**
- Read all model source files (encoder, decoder, loss, config, main model)
- Read design docs if available
- Map the data flow: input shapes → each module → output shapes
- Identify architectural choices and their rationale

**Subtask B — Reference Repo Analysis**
- Read reference implementations in the project's `repos/` directory
- Focus on: core module files, attention mechanisms, loss functions
- Extract reusable patterns and implementation tricks
- Note which patterns are directly applicable vs need adaptation

**Subtask C — Literature Search**
- Search arXiv/Context7/web for latest papers (last 2 years)
- Use `mcp_context7_resolve_library_id` + `mcp_context7_query_docs` for library docs
- Use `mcp_fetch_fetch` for arXiv paper details
- Extract: core innovations, relevance to the project, implementation feasibility

### Phase 2: Structured Comparison

For each module, produce a comparison table:

| Aspect | Current Approach | Mainstream Approach A | Mainstream Approach B |
|--------|-----------------|----------------------|----------------------|
| Architecture | ... | ... | ... |
| Strengths | ... | ... | ... |
| Weaknesses | ... | ... | ... |
| Applicability | ✅/⚠️/❌ | ... | ... |

### Phase 3: Optimization Recommendations

Structure recommendations as:
1. **Highest Priority** — minimal code change (1-5 lines), maximum expected gain
2. **High Priority** — small changes (10-30 lines), clear benefits
3. **Medium Priority** — needs ablation experiments to validate
4. **Low Priority** — major architecture changes, deferred to later versions

Each recommendation must include:
- What to change and where (file + approximate lines)
- Code snippet showing the change
- Reference paper/repo that inspired it
- Expected impact

### Phase 4: Ablation Experiments

Design ablation experiments to validate optimization priorities:
- What to remove/disable
- What it validates
- Expected outcome

## MCP Tools Usage

| Tool | Use For |
|------|---------|
| `mcp_codegraph_*` | Code structure analysis (callers, callees, impact) |
| `mcp_context7_resolve_library_id` | Find library documentation |
| `mcp_context7_query_docs` | Query specific API/architecture docs |
| `mcp_fetch_fetch` | Fetch arXiv papers, blog posts |
| `mcp_sequential_thinking` | Multi-step reasoning about tradeoffs |

## Output Format

Write to `<project>/优化建议.md` (or user-specified path) with:

```
# Model Name — Optimization Suggestions

## 一、Architecture Diagnosis
(current pipeline summary, core issues)

## 二、Module-by-Module Analysis
(for each module: current vs mainstream, optimization suggestions with code)

## 三、Latest Research Inspirations
(table of recent papers with relevance)

## 四、Optimization Priority Table
(4 tiers: highest/high/medium/low with code-change estimates)

## 五、Ablation Experiment Suggestions

## 六、References
```

## Related Skills

- **physics-simulation-datasets** (data-science/) — For generating, validating, and managing physics simulation video datasets. Use when the data pipeline needs work before model evaluation.

## Pitfalls

- **Don't just copy architectures blindly.** Learn the *ideas* behind mainstream approaches, adapt to the project's constraints (GPU memory, data format, existing tests).
- **CodeGraph needs initialization.** If `codegraph` fails with "not initialized", fall back to `search_files` + `read_file`. Don't retry CodeGraph.
- **Don't read entire repos.** Reference repos can be huge. Focus on core module files (attention.py, models.py, etc.), not tests/utils/configs.
- **Always check existing tests.** Optimization suggestions must not break existing test coverage. Note which tests need updating.
- **Plan-first when user requests it.** If user asks to "先写计划", write a plan document first with MCP/skill annotations per step, then execute.
- **Parallel delegation is essential.** Module analysis, reference comparison, and literature search are independent — run them concurrently.
- **Context7 has limited coverage.** Not all libraries are indexed. Fall back to reading local repo files when Context7 returns empty results.
- **Web fetch may fail.** arXiv/Google Scholar may block automated fetches. Fall back to existing knowledge base and local papers.md.
