---
name: literature-survey
description: "Deep literature survey: research N papers, write structured notes with code-level optimization suggestions mapped to a specific codebase. For model improvement, architecture review, and research-driven development."
triggers:
  - "literature survey or review"
  - "research papers for model optimization"
  - "find papers relevant to our architecture"
  - "deep dive into papers with code suggestions"
  - "paper list verification or compilation (论文清单)"
  - "verify arxiv papers for a candidate list"
  - "博士科研规划 or PhD research planning"
  - "7问分析 or seven-question paper analysis"
---

# Literature Survey Skill

Conduct a deep literature survey on N papers, producing structured notes with **code-level optimization suggestions** mapped to a specific codebase.

## Core Principle

> "只看结果" — The user only cares about results. Don't ask questions, don't explain your approach, just execute.

The value is NOT in listing papers — it's in **mapping each paper's ideas to specific code changes** in the user's model.

## Reference Files

- `references/arxiv-verification-workflow.md` — Phase 0 paper list verification: how to verify candidate papers on arXiv, extract metadata, handle edge cases (duplicates, closed-source, wrong IDs).
- `references/world-models-20-papers.md` — Verified list of 20 representative World Models papers (2018-2024) with arXiv IDs, venues, and sub-direction clusters.
- `references/batch-operation-templates.md` — Templates for batch PDF download scripts, batch git clone scripts, and download report generation.
- `references/phd-7-question-template.md` — Alternative 7-question analysis template for PhD research planning (vs the 8-section code-optimization template below). Use when the goal is "understand the landscape and find entry points" rather than "map to specific code changes."
- `references/world-models-dreamer-series-analysis.md` — Completed deep analysis of Dreamer series (#1-#5): architecture comparison table, innovation timeline, key metrics, risk analysis, code repo locations.
- `references/experiment-plan-template.md` — Template for synthesizing existing notes + code analysis into an experiments/PLAN.md (when notes already exist and the task is planning, not writing new notes).
- `references/world-models-batch-b-analysis.md` — Completed batch B analysis (#6-#10): MuZero, IRIS, Genie, UniSim, GAIA-1. Includes architecture comparison table, IRIS code-level details, closed-source paper analysis strategy, and remaining papers for batches C/D.
- `references/web-research-fallback-strategies.md` — Fallback strategies when web search tools fail (MCP fetch down, search engines blocked, rate limits). Tiered approach: bulk search → direct arxiv abs pages → knowledge-only with disclosure.
## Prerequisites

Before writing any notes, you MUST:
1. **Read ALL model code** — every `.py` file in the model directory
2. Understand the full architecture: encoder, interaction, temporal, decoder, loss
3. Know the config, hyperparameters, and training loop
4. Identify specific weaknesses/gaps in the current model

Without this, your "suggestions" will be generic and useless.

## Per-Paper Note Structure (8 sections, STRICT)

> **Alternative:** For PhD research planning (选题/开题), use the 7-question template in `references/phd-7-question-template.md` instead. It focuses on landscape understanding, risk analysis, and entry points rather than code-level mapping.

Every `notes.md` must have ALL 8 sections:

```markdown
# Paper Title

## 基本信息
- 作者：
- 年份：
- 会议/期刊：
- 论文链接：
- 代码链接：
- PDF：filename.pdf（已下载/需下载）

## 核心贡献
- （3-5 条，每条一句话）

## 模型架构
- Encoder：
- Decoder：
- 交互模块：
- 时序模块：
- （如有代码，标注关键实现细节）

## 损失函数
- （列出所有损失项，公式简述）

## 关键设计选择
- （为什么这样设计，与其他方案对比）

## 与当前模型的对比
- 相似之处：
- 不同之处：

## 可借鉴的点
- （**必须映射到具体代码文件和函数**，说明怎么改、改哪里）

## 实验结果（关键指标）
- （数据集、指标、与 baseline 对比）
```

### The Critical Section: 可借鉴的点

This is where 90% of the value lives. Each point MUST include:
- **映射位置**：`path/to/file.py` → `ClassName` or `function_name`
- **当前问题**：what's wrong with the current code
- **具体改进**：actual code snippet showing the change
- **预期收益**：quantified improvement expected
- **实现难度**：低/中/高

Bad (generic):
> "可以用注意力机制改进聚合"

Good (specific):
```python
# 映射位置：model/ai_model/interaction.py → GNNSingleLayer
# 当前：mean 聚合，所有邻居权重相同
# 改为：
class AttentionAggregation(nn.Module):
    def __init__(self, node_dim):
        self.attn = nn.Sequential(nn.Linear(node_dim * 2, 1), nn.LeakyReLU(0.2))
    def forward(self, messages, node_feat, valid_mask):
        attn_scores = self.attn(torch.cat([node_i, node_j], dim=-1))
        attn_weights = F.softmax(attn_scores.masked_fill(~mask, float('-inf')), dim=-1)
        return (messages * attn_weights).sum(dim=3)
# 预期：碰撞预测 F1 +5-10%
# 实现难度：低
```

## Workflow

### Phase 0: Verify Candidate Paper List (when applicable)

If you receive a **candidate paper list** (from user or Supervisor), verify before deep analysis:
1. Load each paper's arXiv page to confirm ID, authors, year, conference
2. Use arXiv search for papers with unknown IDs
3. Deduplicate entries, handle closed-source papers, note missing code repos
4. Compile verified list into structured Markdown (see `references/arxiv-verification-workflow.md` for details)

### Phase 1: Understand the Codebase (MUST do first)
```
1. Read ALL model .py files
2. Write 00_current_model_analysis.md with:
   - Architecture summary
   - Each module's design choices
   - Identified weaknesses
3. This analysis becomes the lens through which you evaluate every paper
```

### Phase 2: Research Papers
```
For each paper:
1. Download PDF (arxiv direct URL)
2. Clone code repo if available (see network tips below)
3. Read and understand the paper
4. Write notes.md with all 8 sections
5. Focus especially on "可借鉴的点" mapped to actual code
```

### Phase 3: Summary Reports
```
1. 01_literature_survey_summary.md — paper list by direction, tables
2. 02_optimization_proposals.md — prioritized list of specific code changes
   - P0 (immediate): easy wins, high impact
   - P1 (short-term): moderate effort, high impact  
   - P2 (medium-term): high effort, transformative
```

## PDF Verification Workflow

When verifying a paper library (checking that downloaded PDFs are correct):

**First:** Check for PDF content mismatches — see `references/pdf-content-mismatch-detection.md` for known bad PDFs and detection method. A PDF can be a valid PDF file but contain the WRONG paper.

### Step 1: Identify bad PDFs
```bash
# Check file is actual PDF (not HTML error page)
head -c 5 file.pdf | grep -q "%PDF" && echo "OK" || echo "BAD"
# Check file size (PDFs should be > 50KB, HTML error pages are ~10KB)
stat -c%s file.pdf
```

Common bad-PDF signatures:
- `10703 bytes` — arxiv HTML "Page Not Found" page
- `< 100 bytes` — empty or redirect
- Starts with `<!DOCTYPE` or `<h1>` — HTML, not PDF

### Step 2: Delete bad PDFs, download correct ones

### Download with proxy (WSL)

When `curl` times out on arxiv (common in China), use Python urllib with proxy:
```python
import urllib.request, os
proxy = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'})
opener = urllib.request.build_opener(proxy)
req = urllib.request.Request(f"https://arxiv.org/pdf/{arxiv_id}")
req.add_header('User-Agent', 'Mozilla/5.0')
data = opener.open(req, timeout=60).read()
with open(dest, 'wb') as f: f.write(data)
```

**Key pitfall:** arxiv URL versioning — `arxiv.org/pdf/XXXX.XXXXXv3` may 404. Use `arxiv.org/pdf/XXXX.XXXXX` (no version) for latest.

### Step 3: Verify downloaded PDFs
```python
with open(dest, 'rb') as f: header = f.read(5)
is_pdf = header == b'%PDF-'
```

## Notes.md Rewrite Workflow (for existing paper libraries)

When user says "核查论文和代码，重写 notes.md":

1. **Scan** all paper dirs for: PDF validity, code existence, notes.md line count
2. **Categorize** by quality: detailed (≥150 lines), OK (100-149), needs rewrite (<100)
3. **Batch dispatch** via `delegate_task` — 3 papers per batch, each subagent:
   - Runs `pdftotext -layout` on the PDF → reads extracted text
   - Lists and reads key `.py` files in the `code/` directory
   - Reads existing `notes.md`
   - Rewrites with all 8 sections (especially 代码实现细节)
4. **Report** summary: how many done, which have PDF issues, which need further work

**User correction chain (CRITICAL):**
- User: "写之前论文也要读啊" → NEVER write notes from memory, always read PDF first
- User: "代码也要读啊" → NEVER skip code reading, always browse code/ directory

**Subagent goal template for batch rewrite:**
```
Read the <PAPER_NAME> paper PDF and code, then rewrite notes.md in Chinese.

Steps:
1. Extract PDF: `pdftotext -layout <pdf_path> /tmp/<name>_text.txt` then read it
2. Browse code: <code_dir>/ - read key Python files
3. Read existing notes.md
4. Rewrite notes.md in Chinese with all required sections
```
The subagent MUST explicitly include "Extract PDF text" and "read key code files" as steps — otherwise it will skip them.

**Venue verification during rewrite:**
When rewriting notes, also verify each paper's venue (顶会/顶刊). Non-top-venue papers (arXiv preprints, workshops, small conferences) should be flagged in the summary report. Common non-top patterns:
- "arXiv preprint" — never formally published
- "Workshop @ <conference>" — workshop, not main conference
- "3DV" / "WACV" — second-tier venues
- PDF content mismatch — PDF is a different paper than expected (check title vs directory name)
## Network Tips (WSL/GitHub/Proxy)

Based on experience with slow WSL network:

### arxiv PDF Downloads
- Direct URLs work: `https://arxiv.org/pdf/XXXX.XXXXX` (no version suffix)
- **curl often fails** in China even with proxy — use Python urllib with proxy (see PDF Verification section above)
- **Python urllib with proxy is the most reliable method** (tested 2026-05-31: downloaded 8 PDFs successfully when curl timed out)
- `mcp_fetch` can access arxiv for metadata but can't download binary PDFs
- Check file starts with `%PDF-` and size > 50KB to verify success
- Batch downloads sequentially (parallel causes incomplete reads/timeouts)
- **arxiv versioned URLs 404**: `arxiv.org/pdf/XXXX.XXXXXv3` often fails. Always use `arxiv.org/pdf/XXXX.XXXXX` (no version)

### GitHub Clone
- GitHub is often slow/unreachable from WSL
- Try multiple URL variants:
  - `https://github.com/user/repo.git`
  - `https://github.com/user/repo` (no .git)
  - Mirror repos (e.g., lucidrains reimplementations)
- Use `git clone --depth 1` (shallow clone)
- 120s timeout per repo
- If a repo fails 3 times, skip it — notes don't depend on actual code
- Some repos are private/deepmind-internal — no workaround

### Script Pattern
```bash
# Sequential download with verification
download() {
    [ ! -f "$2" ] && curl -sL --connect-timeout 20 --max-time 90 -o "$2" "$1"
    [ -s "$2" ] && [ $(stat -c%s "$2") -gt 5000 ] && echo "OK: $2" || { rm -f "$2"; echo "FAIL: $2"; }
}
```

## Subagent Strategy

**For the core 8-section literature survey: do it yourself.** Subagents get interrupted on long tasks and produce generic results. Read the codebase and write notes yourself.

**For paper library verification/rewrite (核查已有 notes.md): use parallel batches.** When the task is "verify and rewrite existing notes.md for N papers":
1. Use `delegate_task` with batches of 3 tasks (max concurrent for most users)
2. Each subagent: extract PDF via `pdftotext`, browse code dir, read existing notes, rewrite
3. User will correct you if you skip reading — **"写之前论文也要读啊"** and **"代码也要读啊"** mean you MUST read PDF + code before writing, not just rewrite from memory
4. The subagent goal must explicitly include: "Extract PDF text, read key code files, THEN rewrite notes.md"

**Anti-pattern:** Trying to rewrite notes without reading the PDF. The user will catch you.

## Multi-Batch Progress Tracking

When the Supervisor assigns papers in batches (e.g., batch A #1-#5, batch B #6-#10):
1. Maintain a progress table in your report showing completed/pending papers
2. For each completed batch, create a reference file in `references/` with architecture comparison tables and code-level details
3. Track remaining papers for future batches (C, D, etc.)
4. In the HANDOFF_SUMMARY, always include current progress (e.g., "10/20篇") and next batch recommendation
5. Use the same analysis template and format as previous batches for consistency

## Reading Existing Notes + Synthesizing Optimization Plans

When the task is "read existing notes.md files and produce an optimization plan" (NOT writing new notes), follow this workflow:

1. **Read summary files first** — literature_survey_summary.md, optimization_proposals.md, ROADMAP.md (if they exist)
2. **Read ALL model code** — every .py file in the model directory (same as Phase 1)
3. **Read EVERY notes.md** — do NOT skip any, do NOT rely on summaries alone. Each notes.md has unique details not captured in summaries
4. **Check what's already implemented** — before proposing an experiment, verify the code doesn't already have it (e.g., "add SSIM loss" when loss.py already has `_ssim_loss`). This is the #1 mistake
5. **Write experiments/PLAN.md** with:
   - Architecture evaluation (advantages, bottlenecks, whether to do a major overhaul)
   - Literature summary table (per-paper: core idea, relevance to code, key implementation points)
   - Prioritized experiment list: incremental optimizations first, then architectural alternatives
   - Each experiment: what files to change, what to change, expected improvement, risk, verification method
   - Diff from existing ROADMAP.md (what's already done, what's new, what's removed)

**Critical pitfall: Proposing experiments for features already implemented.** Always grep/read the actual code before adding an experiment to the plan. Config flags like `use_amp=True`, `use_temporal_attention=True`, `use_uncertainty_weighting=True` mean those features exist.

## Pitfalls

1. **Generic suggestions** — "可以用 Transformer 替代" is useless. Must specify which file, which class, what code to write.
2. **Skipping code reading** — If you don't read the model code first, every suggestion will be disconnected from reality.
3. **Parallel downloads** — In slow networks, parallel downloads cause timeouts. Go sequential.
4. **Relying on subagent quality** — Subagents produce shallow notes. Do it yourself for quality.
5. **Missing the "可借鉴的点" section** — This is the entire point of the survey. Every paper needs 3-5 specific code changes.
6. **Skipping arXiv verification** — Candidate paper lists often have wrong arXiv IDs or duplicate entries. Always verify by loading each arXiv page before proceeding to deep analysis.
7. **No terminal available** — If the agent lacks a terminal/shell tool, create download/clone scripts as files and report them as "待执行" with clear manual execution instructions. Never claim downloads happened if they didn't.
8. **PDF extraction fallback** — When pdftotext/pymupdf cannot be executed (no terminal), use already-downloaded code repositories + training knowledge to supplement analysis. Clearly note in the report that PDF direct extraction was not performed. Code-level analysis (reading .py files via read_file) is always available and provides concrete architectural details that paper-only analysis misses.
9. **Closed-source papers without code repos** — Papers from DeepMind, Google, Wayve often don't release code. For these: (a) rely on architecture diagrams and method descriptions in the paper, (b) compare to similar open-source papers you DO have code for, (c) note specific claims that cannot be verified, (d) focus on high-level design patterns rather than implementation details. Don't claim code-level analysis when no code exists.

10. **Research task without web tools (CLI mode)** — When the task is "去网上找相关论文调研" (find papers online) but you lack terminal/web_search/web_extract/browser tools, you cannot perform live web research. Fallback: write the report from training knowledge with clear disclosure: (a) list specific papers you know about with titles, authors, years, (b) add a prominent "⚠️ 局限性声明" section stating the report is based on training knowledge, not live search, and paper citations may have inaccuracies, (c) provide recommended search keywords for the user to verify and extend. NEVER pretend you searched the web when you didn't. The report structure should still cover the research question thoroughly — the limitation is in source verification, not in the depth of analysis.

11. **Search engines blocked but browser available** — When you have browser tools but search engines are blocked (Google Scholar IP ban, Bing returning wrong-language results, Semantic Scholar rate-limited), the reliable fallback is **direct arxiv.org/abs/<paper_id> page access**. Strategy: (a) use your training knowledge to identify the most relevant papers by arXiv ID, (b) navigate to each `https://arxiv.org/abs/<id>` page to verify title, authors, year, venue, and abstract, (c) mark verified papers as "✅已验证" in the report, (d) mark unverified papers (from training knowledge only) with a disclosure note. This hybrid approach — knowledge-driven + targeted verification — produces a credible report even when bulk search is unavailable. Direct arxiv abs pages are NOT blocked by arxiv's robots.txt (unlike /search pages).

## Verification

After completing the survey, verify:
```
1. papers/ has N folders, each with notes.md
2. Each notes.md has all 8 sections
3. Each "可借鉴的点" maps to specific code files
4. 01_literature_survey_summary.md has complete tables
5. 02_optimization_proposals.md has prioritized recommendations with code snippets
```
