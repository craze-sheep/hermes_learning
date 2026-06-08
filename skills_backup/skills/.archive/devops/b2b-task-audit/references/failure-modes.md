# B2B Task Failure Modes Taxonomy

Extracted from real task audits. Each entry: symptom → root cause → detection → fix.

---

## 1. Silent Fallback Degradation

**Symptom**: Worker report contains "本地 fallback 输出" / "模型不可用：RuntimeError" but task continues as if work was completed.

**Root Cause**: `ai_team_b2b_service.py` catches ALL exceptions in `worker_reply()` and generates a fallback response that echoes the input back.

**Detection**: Search worker reports for strings: `本地 fallback`, `模型不可用`, `RuntimeError`, `fallback 响应`.

**Fix**: Add a `fallback: true` field to artifact metadata. Supervisor should check for fallback markers.

---

## 2. Tool-Capability Mismatch

**Symptom**: Worker produces generic/empty output because it cannot perform the required operations.

**Root Cause**: Role configs define toolsets that don't match task requirements.

**Detection**: Compare worker's `RoleConfig.toolsets` against task requirements.

**Fix**: Supervisor's system prompt should include tool capability awareness.

---

## 3. Template-as-Deliverable

**Symptom**: `files/` directory contains markdown files with placeholder text.

**Root Cause**: Workers produce well-structured templates but system treats them as final deliverables.

**Detection**: Search files for regex patterns: `<[^>]+>`, `待填写`, `TODO`.

**Fix**: Distinguish "plan" artifacts from "deliverable" artifacts.

---

## 4. Broken Handoff Chain

**Symptom**: Supervisor dispatches a worker but no corresponding report exists.

**Root Cause**: Worker bot never received the Telegram message or crashed during processing.

**Detection**: Check if corresponding worker report exists after each ASSIGN.

**Fix**: Add timeout monitoring and health check pings.

---

## 5. Unbatched Dispatch

**Symptom**: Plan specifies batched execution but Supervisor dispatches all work in a single ASSIGN.

**Root Cause**: Supervisor's decision prompt doesn't enforce the plan's batching strategy.

**Detection**: Compare plan against actual ASSIGN messages.

**Fix**: Supervisor should re-read plan when making dispatch decisions.

---

## 6. Hallucinated Metadata

**Symptom**: Paper titles, conference names, years, author names, or links are incorrect.

**Root Cause**: Workers generate lists from memory without verification.

**Detection**: Check if venue names are actual conferences vs institution names.

**Fix**: Research tasks MUST use web search tools to verify metadata.

---

## 7. Handoff Summary Overflow

**Symptom**: Handoff summaries exceed the 300-character limit.

**Root Cause**: Multiple inconsistent limits exist in the codebase.

**Detection**: Measure handoff_summary length in artifact files.

**Fix**: Unify character limits and enforce at parse time.

---

## 8. Duplicate/Vague List Items

**Symptom**: Task lists contain duplicate entries or vague items.

**Root Cause**: Lists generated from memory without dedup or specificity checks.

**Detection**: Check for exact or near-exact duplicates.

**Fix**: Add dedup pass and require specific identifiers.

---

## 9. Telegram Message Truncation

**Symptom**: Bot @usernames split across lines, breaking Telegram's mention parsing.

**Root Cause**: Message formatting doesn't account for line break insertion points near @mentions.

**Detection**: Search for `@\w+_\w+\n\w+` patterns.

**Fix**: Ensure @mention + following text stays on same line.

---

## 10. Premature DONE

**Symptom**: Task state shows `completed: true` but the actual user goal is not fulfilled.

**Root Cause**: Supervisor LLM outputs `TARGET_ROLE: DONE` after receiving a partial worker report.

**Detection**: Check `state.json` — if `completed: true` but `turns` is small, suspect premature DONE.

**Fix**: Add guard: if incoming is a worker REPORT and more subtasks remain, refuse DONE.

**Example (2026-05-31)**: Task B2B-20260531-031623 — Researcher completed R1 (5 papers), Supervisor marked DONE, R2 never dispatched.

---

## 11. Supervisor Echo Chamber

**Symptom**: Supervisor's ASSIGN message contains full user task text + full previous worker report.

**Root Cause**: Supervisor's decision prompt includes all previous context verbatim.

**Detection**: Measure ASSIGN message length — >2000 chars is suspicious.

**Fix**: Supervisor prompt should say "Summarize previous reports in 2-3 sentences."

---

## 12. Telegram Message Too Long (NEW)

**Symptom**: Worker or Planner report rejected by Telegram with "BadRequest: Message is too long".

**Root Cause**: Worker generated a report exceeding Telegram's ~4000 char message limit. The B2B system tries to send it as a Telegram message and fails.

**Detection**: Check for "BadRequest" or "Message is too long" errors in tmux logs.

**Fix**: 
- Write detailed requirements/reports to files, reference in short messages
- Keep @ messages under 500 chars
- Pattern: `@worker_bot 读取 <path> 并执行。简述：<one-line>`

---

## 13. Supervisor Does Worker's Job (NEW)

**Symptom**: Supervisor fixes code bugs, runs scripts, or produces deliverables directly instead of dispatching workers.

**Root Cause**: Supervisor LLM decides to "just fix it quickly" rather than dispatching. Often triggered by impatience or blocked state.

**Detection**: Check Supervisor artifact files for code patches, file writes, or terminal commands — these should be in Developer artifacts.

**Fix**:
- Supervisor prompt: "If you have workers available, dispatch — don't do the work yourself"
- Exception: Only when no workers are available (e.g., Telegram not configured)
- When workers are available, even simple fixes should be dispatched

---

## 14. Honest Status Reporting Failure (NEW)

**Symptom**: Supervisor claims "optimization complete" when only code/plans were created. User asks "真的优化了吗" and the answer is no.

**Root Cause**: Supervisor conflates "infrastructure created" with "work done". Plans and code are intermediate artifacts, not final results.

**Detection**: Check if deliverables include actual execution results (metrics, trained models) or just plans/code.

**Fix**:
- Distinguish: planning → code → smoke test → full training → verified
- Only claim "done" when execution results exist
- Be honest: "We created experiment code but haven't run training yet"

---

## 15. File-Based Communication Not Used (NEW)

**Symptom**: Long instructions in @ messages get truncated or rejected. Workers receive incomplete requirements.

**Root Cause**: Supervisor puts all requirements inline in the @ message instead of writing to a file.

**Detection**: Check if ASSIGN messages exceed 500 chars. Check if workers report confusion about requirements.

**Fix**:
- Write detailed requirements to `experiments/requirements.md` or `artifacts/tasks/<task_id>/files/requirements.md`
- @ message: `@worker 读取 <path> 并执行`
- This also helps when Planner's analysis is too long for Telegram
