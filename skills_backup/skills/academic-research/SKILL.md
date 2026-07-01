---
name: academic-research
description: "Academic research: literature surveys, paper writing pipeline, arXiv search. For model improvement, architecture review, and publication."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Academic, Literature-Survey, Paper-Writing, arXiv, NeurIPS, ICML, ML]
---

# Academic Research

Literature surveys, paper writing, and arXiv search for ML/AI research.

## 1. Literature Survey

Deep literature survey: research N papers, write structured notes with **code-level optimization suggestions** mapped to a specific codebase.

### Core Principle
> The value is NOT in listing papers — it's in **mapping each paper's ideas to specific code changes** in the user's model.

### Prerequisites
Before writing any notes, you MUST:
1. **Read ALL model code** — every `.py` file in the model directory
2. Understand the full architecture: encoder, interaction, temporal, decoder, loss
3. Identify specific weaknesses/gaps in the current model

### Per-Paper Note Structure (8 sections)
1. **基本信息** — authors, year, venue, links
2. **核心贡献** — 3-5 key contributions
3. **模型架构** — encoder, decoder, interaction, temporal modules
4. **损失函数** — all loss terms with formulas
5. **关键设计选择** — design rationale, comparison with alternatives
6. **与当前模型的对比** — similarities and differences
7. **可借鉴的点** — **MUST map to specific code files and functions** with code snippets
8. **实验结果** — datasets, metrics, baseline comparisons

### The Critical Section: 可借鉴的点
Each point MUST include:
- **映射位置：** `path/to/file.py` → `ClassName` or `function_name`
- **当前问题：** what's wrong with the current code
- **具体改进：** actual code snippet showing the change
- **预期收益：** quantified improvement expected
- **实现难度：** 低/中/高

### Workflow
1. **Phase 0:** Verify candidate paper list (arXiv IDs, authors, venues)
2. **Phase 1:** Read ALL model code (mandatory first step)
3. **Phase 2:** Research papers one by one, write notes.md with all 8 sections
4. **Phase 3:** Write summary reports (literature_survey_summary.md, optimization_proposals.md)

### Pitfalls
- **Generic suggestions are useless** — must specify which file, which class, what code
- **Skipping code reading** — every suggestion will be disconnected from reality
- **Parallel downloads fail** in slow networks — go sequential
- **NEVER guess arXiv IDs** — search by exact title instead (~100% accuracy vs ~20% for guessing)

## 2. Paper Writing Pipeline

End-to-end pipeline for producing publication-ready ML/AI research papers targeting **NeurIPS, ICML, ICLR, ACL, AAAI, and COLM**.

### Pipeline Stages
1. **Experiment Design** — define hypotheses, metrics, baselines
2. **Execution** — run experiments with proper ablation
3. **Analysis** — statistical significance, error analysis
4. **Writing** — LaTeX paper with proper structure
5. **Review** — internal review, revision
6. **Submission** — format check, supplementary materials

### Paper Structure
```
Abstract (150-250 words)
1. Introduction (motivation, contribution, paper outline)
2. Related Work (categorize, compare, position)
3. Method (architecture, loss, training details)
4. Experiments (setup, results, ablation, analysis)
5. Conclusion (summary, limitations, future work)
References
Appendix (proofs, additional experiments, details)
```

### Key Rules
- **Every claim needs evidence** — experimental result, citation, or proof
- **Ablation studies are mandatory** — show each component's contribution
- **Statistical significance** — report confidence intervals, run multiple seeds
- **Reproducibility** — detailed hyperparameters, code availability statement

## 3. arXiv Search

### Search by keyword
```
https://arxiv.org/search/?query=%22Exact+Paper+Title%22&searchtype=all
```

### Direct paper access
```
https://arxiv.org/abs/<paper_id>    # metadata + abstract
https://arxiv.org/pdf/<paper_id>    # PDF (no version suffix for latest)
```

### Tips
- Use exact title search for verification (near 100% accuracy)
- arXiv IDs: `XXXX.XXXXX` format (no version suffix)
- PDF downloads: use Python urllib with proxy for reliability
- Rate limiting: MCP fetch limits after ~10-12 rapid calls

## Related Skills
- `ml-model-evaluation` — architecture evaluation against literature
- `literature-survey` — detailed workflow in archive (references/)
- `research-paper-writing` — full pipeline in archive (references/)

## Archived Detailed References
The following detailed references are available in the archive:
- `~/.hermes/skills/.archive/literature-survey/references/` — 11 reference files including arxiv verification, batch operations, PhD templates
- `~/.hermes/skills/.archive/research-paper-writing/references/` — 54 reference files covering LaTeX, citations, statistical analysis, conference-specific formatting
