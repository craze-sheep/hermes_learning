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

### Mode A: Quick Evaluation (few papers, parallel)

For evaluating against 3-5 reference approaches, use parallel delegation:

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

### Mode B: Deep Literature Survey (10+ papers, sequential)

For comprehensive literature surveys (e.g., 50 papers with code-level optimization suggestions), use a **sequential** approach — it produces much higher quality results than parallel delegation.

**Critical rule: Read ALL model code FIRST, then write paper notes.**

Without understanding the codebase deeply, paper notes become generic "可借鉴的点" that don't connect to actual code. The user will notice and call it out.

**Step 1: Read the entire model codebase (mandatory first step)**
- Read EVERY .py file in the model directory using `terminal cat` (not read_file — it may report "unchanged" from prior context compaction)
- Understand: data flow, each module's input/output shapes, loss function details, training loop
- Write down: key design choices, obvious weaknesses, dimension mismatches
- This step is NOT skippable. Generic paper notes without code context are worthless.

**Step 2: Write paper notes one by one (NOT in parallel via subagents)**
- For each paper, write a structured `notes.md` in the paper's folder
- Every "可借鉴的点" must map to: specific file path + specific function + concrete code snippet
- Use the 8-section template (see below)
- Write 2-3 papers per turn, not more — quality requires attention

**Why NOT to use subagents for this:**
- Subagents with complex multi-step tasks (search paper → download PDF → clone code → read → write notes) keep getting interrupted or timing out (600s limit)
- Subagents cannot maintain context across papers — each paper's suggestions should reference patterns from other papers
- Subagents produce generic notes because they lack the codebase context from Step 1
- Exception: subagents CAN be used for simple, single-responsibility tasks (e.g., "download these 5 PDFs")

**Step 3: Update summary reports only AFTER all papers are done**
- `01_literature_survey_summary.md` — paper list table + per-module comparison tables
- `02_optimization_proposals.md` — prioritized optimization suggestions with code snippets

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

## LLM Benchmarking with lm-evaluation-harness

Evaluate LLMs across 60+ academic benchmarks (MMLU, GSM8K, HumanEval, TruthfulQA, HellaSwag). Industry standard used by EleutherAI, HuggingFace, and major labs.

### Quick Start
```bash
pip install lm-eval

# Standard benchmark evaluation
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag \
  --device cuda:0 --batch_size 8

# vLLM backend (5-10x faster)
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=2 \
  --tasks mmlu --batch_size auto
```

### Core Benchmarks
| Benchmark | What it measures | Time (7B, A100) |
|-----------|-----------------|-----------------|
| MMLU | 57 subjects, multiple choice | ~2 hours |
| GSM8K | Grade school math | ~5 minutes |
| HellaSwag | Common sense reasoning | ~10 minutes |
| HumanEval | Python code generation | ~20 minutes |
| TruthfulQA | Truthfulness | ~15 minutes |
| ARC | Science questions | ~10 minutes |

### Track Training Progress
```bash
# Evaluate checkpoint
lm_eval --model hf \
  --model_args pretrained=checkpoints/step-1000 \
  --tasks gsm8k,hellaswag --num_fewshot 0 \
  --output_path results/step-1000.json
```

### Compare Models
```bash
# Evaluate multiple models
for model in llama-2-7b llama-2-13b mistral-7b; do
  lm_eval --model hf --model_args pretrained=$model \
    --tasks mmlu,gsm8k --num_fewshot 5 \
    --output_path results/$model.json
done
```

### Common Issues
- **OOM:** Reduce `--batch_size 1` or use quantization (`load_in_8bit=True`)
- **Slow:** Use vLLM backend or reduce `--num_fewshot 0`
- **Different results:** Check fewshot count (most papers use 5-shot)

**Detailed references:** See `references/lm-eval-benchmarks.md`, `references/lm-eval-custom-tasks.md`, `references/lm-eval-api-evaluation.md`, `references/lm-eval-distributed.md`.

## Support Files

- `references/literature-survey-template.md` — 8-section template for paper notes with code-level suggestions
- `references/example-model-analysis.md` — Example of the depth expected when analyzing a model codebase before writing paper notes

## Pitfalls

- **Don't just copy architectures blindly.** Learn the *ideas* behind mainstream approaches, adapt to the project's constraints (GPU memory, data format, existing tests).
- **CodeGraph needs initialization.** If `codegraph` fails with "not initialized", fall back to `search_files` + `read_file`. Don't retry CodeGraph.
- **Don't read entire repos.** Reference repos can be huge. Focus on core module files (attention.py, models.py, etc.), not tests/utils/configs.
- **Always check existing tests.** Optimization suggestions must not break existing test coverage. Note which tests need updating.
- **Plan-first when user requests it.** If user asks to "先写计划", write a plan document first with MCP/skill annotations per step, then execute.
- **Parallel delegation is essential for Mode A.** Module analysis, reference comparison, and literature search are independent — run them concurrently.
- **Context7 has limited coverage.** Not all libraries are indexed. Fall back to reading local repo files when Context7 returns empty results.
- **Web fetch may fail.** arXiv/Google Scholar may block automated fetches. Fall back to existing knowledge base and local papers.md.
- **read_file may report "unchanged" after context compaction.** Use `terminal cat` instead when you need to re-read code files that were read in a prior context window.
- **Subagents fail on complex multi-step tasks.** Tasks like "search → download → read → analyze → write" consistently time out (600s). Break into: (1) search/download in main session, (2) write notes in main session. Only delegate simple single-responsibility tasks.
- **User will notice generic suggestions.** If you write "可以考虑用 attention 机制" without mapping to their specific code, they will ask "你真的都熟悉吗". Always connect to actual file paths and class names.
- **Quality over speed is the default for deep research.** When given the choice, users prefer 50 papers done well over 50 papers done fast. Don't rush — write 2-3 papers per turn with full code-level detail.
- **PDF downloads from arXiv often fail in batch scripts.** arXiv rate-limits or blocks bulk downloads. About 60-70% success rate in batch. Download PDFs one at a time with delays, or skip and focus on notes.md quality (which is what actually matters for optimization suggestions).
- **arxiv URL format**: Use `https://arxiv.org/pdf/XXXX.XXXXX` without version number — it auto-redirects to latest. Adding version numbers like `v2` sometimes helps but often doesn't. The plain ID format is more reliable.
- **WSL network for git clone is extremely slow.** GitHub cloning from WSL consistently times out or takes 5+ minutes per repo. Batch clone scripts with `wait` produce no output for minutes. Workaround: clone sequentially with 120s timeout, accept ~30-50% failure rate. Most important code can be read from GitHub web via `mcp_fetch_fetch` instead.
- **50-paper survey takes a full session.** Writing 50 notes.md with 8 chapters each + code-level suggestions + 3 summary reports = ~4-6 hours of continuous work. Plan accordingly. Do NOT try to cram into a single turn — write 3-5 papers per turn.
- **User says "我只看结果" (I only look at results):** This means stop asking clarifying questions and just produce the deliverable. Make reasonable defaults and execute. The user will correct if needed.
