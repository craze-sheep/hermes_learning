---
name: implementation-verification-workflows
description: Use when checking implementation correctness against specs, coordinating independent AI/code reviews, generating similar code from templates, or reviewing project completion status before accepting work.
tags: [verification, spec, code-review, multi-agent, templates, project-review, compliance]
---

# Implementation Verification Workflows

Umbrella skill for accepting or rejecting implementation work: spec-vs-code verification, multi-agent review, template-derived code generation checks, and project completion/progress review.

## When to Use

- User asks whether code matches a design/spec/doc/config.
- User asks multiple agents or tools to review/check the same implementation.
- Generating multiple similar scripts from a working template and needing systematic verification.
- User asks project status/progress or whether a phase is complete.
- Before marking auto-generated or delegated implementation as done.

## Verification Pattern

1. **Extract the contract** — read the spec/design/config/source docs; build a checklist or matrix.
2. **Automate shallow checks** — counts, filenames, global parameters, imports, dictionary keys, syntax/compile.
3. **Inspect semantic logic** — formulas, edge cases, sampling strategies, constraints, integration paths.
4. **Use independent reviewers when risk is high** — same prompt, isolated agents, no cross-contamination.
5. **Cross-compare findings** — consensus/majority/solo findings instead of concatenating reports.
6. **Report with evidence** — PASS/FAIL tables, exact file paths, values from doc vs code, severity.
7. **Only mark done after final gate passes** — especially when the user explicitly requires a final reviewer.

## Template-Derived Code Generation

When creating N variants from one working script:

- Read the template and every target config first.
- Use mechanical transformations for names/IDs/constants, then inject target-specific logic.
- Verify each generated file with compile/lint and programmatic parameter checks.
- Watch for copy-paste bugs: incomplete view dictionaries, missing object type dispatch, wrong defaults, and stale function names.

## Design-Document Review Gate Pattern

Use this when the deliverable is a design document rather than code, but the user still requires staged review (for example: Hermes/OpenCode iteration, then Claude Code final approval).

1. **Draft from all governing context** — plan section, previous design docs, existing code/data interfaces, research notes, and repo inventory.
2. **Run the first-stage reviewer in review-only mode** with a self-contained prompt naming the target doc, governing plan section, cross-check files, review dimensions, and PASS/FAIL output schema.
3. **If the preferred reviewer is flaky or may be unavailable, run a `delegate_task` reviewer as fallback in parallel.** Treat it as equivalent to the first-stage reviewer, not as the final different-model gate.
4. **Patch the design doc from must-fix findings**. For architecture/module docs, high-value checks include:
   - first-version scope: explicit in/out list;
   - concrete resource budget: memory target, batch-size floor, model-size estimates, fallback configs;
   - future extension interfaces with explicit shapes/defaults;
   - complete shape tables including intermediate tensors, masks, edge features, and queries;
   - ambiguous data semantics: directionality, thresholds, normalized vs raw units;
   - mismatches with existing dataset/code: missing fields, unstable IDs, unused dimensions;
   - static/padded entity handling.
5. **Record the review loop inside the design doc** — reviewer verdict, must-fix summary, and what changed.
6. **Only after the first-stage loop is fixed, run the required final reviewer**. If final review passes with cheap non-blocking clarifications, patch them immediately.
7. **Update the governing plan/status file only after final PASS** with status, output file, conclusion, and iteration record.

## Multi-Agent Review Pattern

- Use one identical self-contained prompt per reviewer.
- Include exact paths, explicit checklist, and output schema.
- Run reviewers in parallel when possible.
- Categorize findings:
  - high confidence: multiple reviewers agree;
  - medium confidence: two agree or one has strong evidence;
  - low confidence: solo claims requiring manual verification.
- Do not let review tools modify files when the task is "check only".

## Project Progress Review Pattern

- Orient from README/docs, task directories, git status, code files, outputs, and validation artifacts.
- Distinguish plans/specs from actual deliverables.
- Classify each module as complete, in-progress, pending, or not started with evidence.
- Match the user's language and desired brevity.

## Code Implementation TDD + Review Gate Pattern

Use this when moving from approved design docs into implementation modules.

1. **Keep TDD mechanical and module-scoped** — write focused tests first for the module contract: output keys, tensor/file shapes, masks/padding, gradient flow, edge cases, and integration handoff fields. Run the module test and see it fail before implementing when practical.
2. **Implement the smallest module that satisfies the tests** — avoid training scripts, utility layers, or future features that belong to a later phase unless the current spec requires them.
3. **Add integration wrapper tests after unit modules pass** — verify end-to-end output keys/shapes, valid-mask propagation, no future leakage, and deterministic behavior where relevant.
4. **Run a full targeted suite before review** — all tests for the implemented phase, not just the last file touched.
5. **Use independent code review before marking done** — ask reviewers to check spec conformance, shapes, masks, padding, leakage, static-object handling, normalization, and trainability. If an external reviewer times out or is unavailable, use a subagent fallback and record that explicitly.
6. **Evaluate review findings technically, then patch** — do not blindly accept every suggestion. Fix real blockers, record non-blocking clarifications in docs/status, and add regression tests for discovered edge cases.
7. **Update the governing plan/status file only after tests and review-fix loop pass** — include actual produced files, test command/result, review fixes, and any intentionally deferred scope.

High-value edge cases observed in physics/video tensor modules:

- Transformer attention with an all-invalid key-padding mask can produce NaNs; guard all-invalid batches by temporarily unmasking a dummy token internally, then zero final outputs with the original validity mask.
- Distinguish real resource-budget configs from tiny unit-test configs; name them separately (for example `minimal_12gb()` vs `tiny_test()`) to avoid misleading future agents.
- Reviewers often flag normalized-vs-raw semantics; explicitly document whether a feature is for model input only or for threshold/label construction.

## Task Tracking with Shared Markdown File (分工.md Pattern)

When working on multi-task projects with multiple AI agents, use a shared markdown file to track completion status and review results.

**Pattern:**
```
1. Hermes + OpenCode collaborate on subtask
   - Design docs, implementation, iteration
   
2. Claude Code reviews
   - Different model catches blind spots
   - Reviews design quality, implementation correctness
   
3. If review fails:
   - Hermes + OpenCode fix based on feedback
   - Record fix reasons and iteration history
   - Claude Code re-reviews
   
4. If review passes:
   - Claude Code marks task as ✅ in 分工.md
   - Records final review conclusion
   - Move to next task
   
5. Repeat until all tasks complete
```

**File Structure:**
```markdown
# Project Task Division

## Task Dependencies
[Dependency graph]

## Task Execution Flow
[Mermaid or text diagram]

---

## T1: [Task Name]
**Goal**: [Description]
**Output**: [Files to produce]
**Status**: ✅ 已完成 / ⬜ 待完成

**Iteration History:**
- [Date]: [What happened]
- [Date]: [Review result]

---

## T2: [Task Name]
...
```

**Key Rules:**
- Only the reviewing agent (Claude Code) marks tasks as ✅
- Each task records: design decisions, iteration history, review results
- Review results include: what was found, what was fixed, what remains
- Next task starts only after current task passes review

**Benefits:**
- Clear progress visibility
- Audit trail of decisions and changes
- Different-model review catches same-model blind spots
- Structured handoff between agents

**Example (from physics video prediction project):**
```
T1 论文调研 ──→ T2 代码收集 ──→ T3 数据加载器 ──→ T4 架构设计
                                                  ├─→ T5 输入模块
                                                  ├─→ T6 交互模块
                                                  └─→ T7 时序模块
```
Each task has dependencies, and Claude Code reviews before marking complete.

## Pitfalls

- Global parameter checks do not prove per-level or per-feature compliance.
- Regex counts can miss alternate syntax; verify extraction against actual file formats.
- Claude/Codex/OpenCode reviews are not authoritative alone; cross-compare and verify evidence.
- Large review prompts can overflow context; batch files and keep prompts structured.
- "只检查不修改" means no edits and no cleanup execution.
- A file existing is not proof of completion; read content and inspect artifacts.

## Support Files

Absorbed skills are preserved under `references/` by original name, including detailed review prompts, checklists, and project-specific examples.

- `references/slot-datamaking-t4-design-review.md` — concrete design-doc review case: architecture doc drafted from dataset/research artifacts, OpenCode/subagent first-stage review, Claude Code final gate, and high-value fixes to capture.
- `references/slot-datamaking-t5-t10-review-implementation.md` — concrete module-design and TDD implementation case: physics/video tensor modules, multi-agent review gates, all-invalid Transformer mask guard, normalized-vs-raw label semantics, and config naming pitfalls.
- `references/ml-conda-gpu-env-selection.md` — ML verification environment checklist: create/use the requested conda env, check WSL GPU visibility, install CUDA PyTorch when appropriate, and verify `torch.cuda.is_available()` inside the target env before trusting test results.
- `references/physics-video-eval-inference-review.md` — review checklist for physics/video evaluation and inference modules: scene-level metric aggregation, collision mask/force-label consistency, device handling, checkpoint formats, and visualization coverage.
