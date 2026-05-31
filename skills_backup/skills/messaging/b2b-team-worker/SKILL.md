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

The tmux job system requires **wrapper markers** around the entire response. The full output structure is:

```
<<<B2B_RESPONSE:job_id>>>

MESSAGE:
[B2B-YYYYMMDD-HHMMSS][YourRole][REPORT]
@TeamSupervisor_bot
your report body here

HANDOFF_SUMMARY: <=300 Chinese characters for Supervisor

<<<B2B_DONE:job_id>>>
```

### Wrapper Markers (CRITICAL — causes rework if missed)

- `<<<B2B_RESPONSE:job_id>>>` — signals start of worker output. `job_id` is the **full job ID** from the task JSON's `job_id` field (e.g., `planner-20260531031721-0f3e95437b7847c6`).
- `<<<B2B_DONE:job_id>>>` — signals end of worker output. Same `job_id`.
- These markers MUST appear on their own lines, with nothing else on those lines.
- The MESSAGE and HANDOFF_SUMMARY go BETWEEN the two markers.
- Do NOT output anything after the DONE marker.

### MESSAGE Header

Every worker MESSAGE must start exactly:

```
[B2B-YYYYMMDD-HHMMSS][YourRole][REPORT]
@TeamSupervisor_bot
your report body here
```

- **Task ID** in the `[B2B-...]` header comes from `user_prompt` (the original assignment), NOT the `job_id` field. Extract it from the `[B2B-...][Supervisor][ASSIGN]` message.
- **Role** comes from the job JSON (`role` field)
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

### 0. Missing wrapper markers (causes immediate rework)
The tmux job dispatcher requires `<<<B2B_RESPONSE:job_id>>>` and `<<<B2B_DONE:job_id>>>` wrapping the entire output. Forgetting these causes the dispatcher to not recognize the response. The `job_id` is the FULL job_id from the JSON (e.g., `planner-20260531031721-0f3e95437b7847c6`), NOT the task ID from user_prompt. These are two different IDs — the wrapper uses `job_id`, the MESSAGE header uses the task ID.

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
- **Check if substantive output already exists** (e.g., report file written in a previous attempt). If it does, reuse it — don't redo the analysis. Only fix the Telegram-facing MESSAGE format.
- **Header kind MUST be exactly `[REPORT]`** — never `[完成]`, `[DONE]`, `[STATUS]`, or any other word. The outbound validator checks `found_kind.upper() != "REPORT"` and rejects anything else.

### 6. Telegram message length limit (causes "Message is too long" rejection)
Telegram has a ~4096 character limit for bot messages. Planner/Researcher responses with detailed tables, multi-section plans, and full command examples regularly exceed this. **After rejection, the Supervisor will ask you to re-output under 500 characters.** Prevention:
- Keep the Telegram-facing MESSAGE under 3000 characters (leave headroom for formatting)
- Move detailed plans, tables, and command blocks to a FILE artifact written to the working directory
- The MESSAGE should be a **summary** (what was decided, key numbers, next step), not the full plan
- If the plan is long, write `experiments/screening_plan.md` and reference it: "详见 experiments/screening_plan.md"
- When asked to re-output after length rejection: produce a **drastically** shortened version (500 chars), don't just trim 10%

### 7. Planner: produce deliverables from partial data, don't wait
When assigned to produce comparison tables or surveys and some upstream data is still pending (e.g., Researcher batches not yet complete), the Planner should:
- Fill in all completed items with full detail
- Mark pending items as "待分析" with explicit placeholder text
- Produce the deliverable NOW rather than waiting for 100% completion
- Include a clear "待补充" section listing what will be filled when upstream completes
This lets Supervisor see progress and avoids stalling the pipeline.

## Role-Specific Playbooks

### Planner: Experiment/Strategy Planning Checklist

When assigned a planning task (experiment design, screening strategy, execution plan):

1. **Read the context first** — check baseline metrics, existing experiment directories, PLAN.md, and any prior results before producing a plan.
2. **Write the full plan to a file** (e.g., `experiments/screening_plan.md`) — tables, commands, risk assessments, and multi-phase details go in the file, NOT in the Telegram MESSAGE.
3. **Keep the MESSAGE short** (~300-500 chars): what was planned, key numbers, file path, next step recommendation.
4. **Use `供 Supervisor 决策参考`** for recommendations about next steps — never name other workers.
5. **Mark unverified items** as `待执行/待验证` — don't claim tool results that haven't happened.

**Common Planner output structure:**
```
MESSAGE: 1-paragraph summary + file reference
FILE: experiments/screening_plan.md (full plan with tables, commands, criteria)
HANDOFF_SUMMARY: <=300 chars, what was decided + key deliverable
```

**Pitfall: embedding full plans in MESSAGE.** Telegram has a ~4096 char limit. Detailed plans with tables and commands easily exceed this. Always write to file first, reference in MESSAGE.

### Tester: Experiment/Code Verification Checklist

When assigned a verification or acceptance task with a checklist, follow this execution pattern:

1. **Extract the checklist** from the Supervisor's ASSIGN message — each numbered item becomes a discrete check.
2. **Run all structural checks first** (directory existence, file counts, file presence) in a single terminal command with a loop. Don't check one directory at a time.
3. **Run content/semantic checks** (specific code patterns, class definitions, return types) with targeted grep on the exact file and line range mentioned.
4. **Run syntax/lint checks last** (py_compile, eslint, etc.) — these are slowest and only worth running if structural checks pass.
5. **Produce a table-format report** with #, check item, and PASS/FAIL result for each item.
6. **Write the acceptance report** to the working directory as `ACCEPTANCE_REPORT.md` (or similar) — don't just output it in the MESSAGE.

Verification script template — adapt to the specific checklist:

```bash
BASE=/path/to/working/directory

# Structural checks
for d in $BASE/exp*/; do
  name=$(basename $d)
  # count files, check presence of required files, etc.
done

# Semantic checks
grep -n "pattern" $BASE/exp*/target_file.py

# Syntax checks
for f in $BASE/exp*/*.py; do
  python3 -c "import py_compile; py_compile.compile('$f', doraise=True)"
done
```

Key pitfalls:
- **Don't fabricate results.** If a tool/MCP call wasn't actually executed, mark it "待执行/待验证".
- **Report must include the task ID** and `@TeamSupervisor_bot` in the MESSAGE header.
- **Acceptance report file should be written to the real working directory**, not just artifacts/.

See `references/tester-verification-template.md` for a reusable verification report template and common bash patterns for structural/semantic/syntax checks.

### Developer: ML Training Execution Checklist

When assigned a Developer task involving ML model training, experiment execution, or code modification in a Python/PyTorch project:

1. **Never modify source code directly** — always copy to a working directory first (e.g., `experiments/baseline/model/`). Verify with `diff` that source is untouched after the task.
2. **Check for FP16/AMP compatibility** before training — common overflow values that break in half precision:
   - `-1e9` in `masked_fill` → use `-1e4` (FP16 max ≈ 65504, so -1e9 overflows)
   - Large negative constants in attention masks, loss functions, etc.
3. **Adjust `__file__`-relative paths** when copying code to nested directories — if `train.py` computes `_project_root = os.path.dirname(os.path.dirname(_this_dir))` assuming 2 levels, and you copy to `experiments/baseline/model/`, you need extra `os.path.dirname()` calls.
4. **Run smoke test first** (`--mode smoke`, 3 steps) before full training — catches import errors, path issues, and data loading failures cheaply.
5. **Record metrics to JSON** in the working directory — include train/val loss per epoch, environment info, bugfixes applied, and checkpoint paths.
6. **Apply fixes to copies only** — use `sed -i` or `patch` on the experiment copy, not the source. Document all fixes in the metrics JSON.

**Common execution pattern:**
```bash
cd /path/to/experiments
# For each experiment:
PYTHONPATH="$(pwd)/$exp/model:$PYTHONPATH" conda run -n model python $exp/model/train.py --mode smoke
```

**Pitfall: `diff source copy` with `&&` chaining.** If you run `diff a b && diff c d`, the second diff never runs when the first returns exit code 1 (files differ). Use `;` or separate commands when you need both diffs regardless.

**Pitfall: random initialization variance.** Multiple baseline runs produce different metrics (e.g., best_val_loss 0.4936 vs 0.5451) due to random weight initialization and data shuffling. This is normal — don't flag it as an error. For reproducibility, set `torch.manual_seed()`.

See `references/ml-training-execution.md` for PyTorch AMP pitfalls, conda run gotchas, path adjustment recipes, and metrics JSON templates.

### Researcher: Fact-Checking & Verification Checklist

When assigned a fact-checking or verification task (e.g., "核实以下信息的真实性"):

1. **Search for the project/resource first** — don't assume the user's repo path, URL, or project name is correct. AI-generated content often gets org names wrong.
2. **Extract primary source content** — README, INSTALL.md, official docs. Use browser JS to extract and search README text: `document.querySelector('article.markdown-body').innerText`.
3. **Verify each claim independently** — search for specific feature names, config keys, and functionality in the actual source. Mark each as ✅/❌/⚠️.
4. **Compare claimed vs actual configuration** — users (especially AI) fabricate plausible-looking config examples. Always check the real config format from INSTALL.md or source code.
5. **Write a comparison table report** with clear verdicts and evidence for each claim.
6. **Disclose what couldn't be verified** — mark as ⚠️待验证, not as debunked.

See `references/researcher-github-fact-check.md` for the full GitHub project verification workflow (API search → README extraction → config comparison → feature verification).

## Skills That Complement This

- `b2b-supervisor-executor` — the Supervisor-side counterpart. Covers reading job JSON, dispatching, and DONE reporting format.
- `literature-survey` — when the task involves paper research, load this skill for reference files and batch templates
- `plan` / `writing-plans` — for structuring implementation plans
- `brainstorming` — for ideation phases
