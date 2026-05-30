# B2B Task Failure Modes Taxonomy

Extracted from real task audits. Each entry: symptom → root cause → detection → fix.

---

## 1. Silent Fallback Degradation

**Symptom**: Worker report contains "本地 fallback 输出" / "模型不可用：RuntimeError" but task continues as if work was completed.

**Root Cause**: `ai_team_b2b_service.py` catches ALL exceptions in `worker_reply()` and generates a fallback response that echoes the input back:
```python
except Exception as exc:
    summary = f"{role} 已完成本地 fallback 响应。..."
    visible = f"... 本地 fallback 输出：{summary}\n模型不可用：{type(exc).__name__}"
```
The fallback is indistinguishable from a real report at the protocol level — it has the correct `[REPORT]` header and passes outbound validation.

**Detection**: Search worker reports for strings: `本地 fallback`, `模型不可用`, `RuntimeError`, `fallback 响应`.

**Fix**: 
- Add a `fallback: true` field to the artifact metadata
- Supervisor should check for fallback markers and either retry or alert the user
- Consider making fallback reports use a different header like `[FALLBACK]` instead of `[REPORT]`

---

## 2. Tool-Capability Mismatch

**Symptom**: Worker produces generic/empty output because it cannot perform the required operations (search web, download files, run code).

**Root Cause**: Role configs define toolsets that don't match task requirements. Example: Planner has `skills=("brainstorming", "plan", "writing-plans")` with no web/browser tools, but Supervisor asks it to "validate paper availability and find PDF links."

**Detection**: 
- Compare worker's `RoleConfig.toolsets` against the task requirements in the ASSIGN message
- Check if worker output mentions "待执行/待验证" or describes what SHOULD be done rather than DOING it

**Fix**:
- Supervisor's system prompt should include tool capability awareness: "Don't assign Research-type tasks to Planner — it has no web access"
- Or: add web tools to Planner's config if it sometimes needs them

---

## 3. Template-as-Deliverable

**Symptom**: `files/` directory contains markdown files with placeholder text like `<论文缩写>`, `<全称>`, empty table cells. Looks complete on directory listing but is useless.

**Root Cause**: Workers with `plan` or `writing-plans` skills produce well-structured templates (which IS their job), but the system treats templates as final deliverables. No subsequent worker fills them in.

**Detection**: 
- Search files for regex patterns: `<[^>]+>`, `待填写`, `TODO`, `placeholder`
- Count empty table cells in `.md` files
- Check if templates reference files that don't exist

**Fix**:
- Distinguish "plan" artifacts from "deliverable" artifacts in the metadata
- Supervisor should verify that deliverables contain actual content, not just structure
- Add a "fill template" step after planning

---

## 4. Broken Handoff Chain

**Symptom**: Supervisor dispatches a worker (ASSIGN artifact exists) but no corresponding worker directory/report exists.

**Root Cause**: Worker bot never received the Telegram message (network issue, bot not polling, @mention broken) or worker crashed during processing.

**Detection**: 
- List all `supervisor/assign-*.md` files
- For each, check if corresponding `worker_name/*.md` report exists
- Check timestamps — large gaps (>30min) between ASSIGN and next action suggest timeout

**Fix**:
- Add timeout monitoring: if no worker report within N minutes, Supervisor should re-dispatch or alert
- Add health check pings before dispatching

---

## 5. Unbatched Dispatch

**Symptom**: Plan specifies batched execution (e.g., "4 batches × 5 papers") but Supervisor dispatches all work in a single ASSIGN.

**Root Cause**: Supervisor's decision prompt doesn't enforce the plan's batching strategy. The plan is written to `files/` but Supervisor doesn't re-read it when making dispatch decisions.

**Detection**:
- Read the plan document in `files/`
- Compare against actual ASSIGN messages — do they follow the batch schedule?
- Check if single dispatch would exceed worker's context window or timeout

**Fix**:
- Supervisor's system prompt should say: "If a plan exists in files/, follow its batching strategy"
- Or: encode batch boundaries in the task state machine

---

## 6. Hallucinated Metadata

**Symptom**: Paper titles, conference names, years, author names, or links are incorrect. Conference listed as institution name (e.g., "Meta" instead of "ICML").

**Root Cause**: Workers (especially Supervisor acting as Planner) generate lists from memory without verification. No tool call to arXiv/Semantic Scholar to confirm.

**Detection**:
- Check if venue names are actual conferences (NeurIPS, ICML, ICLR, CVPR, etc.) vs institution names (Meta, NVIDIA, DeepMind)
- Verify arXiv IDs are valid format
- Search for duplicate entries in paper lists

**Fix**:
- Research tasks MUST use web search tools to verify metadata
- Add a verification checklist: "Every paper entry must have: confirmed title, confirmed venue, working arXiv link"

---

## 7. Handoff Summary Overflow

**Symptom**: Handoff summaries exceed the 300-character limit specified in role prompts.

**Root Cause**: Multiple limits exist in the codebase:
- Supervisor prompt: "HANDOFF_SUMMARY: <=300 Chinese characters"
- `compact()` function: max 700 chars (worker output) or 220 chars (status card)
- These limits are inconsistent and not enforced at generation time

**Detection**: 
- Measure handoff_summary length in artifact files
- Check if `compact(text, 700)` was applied vs raw text

**Fix**:
- Unify the character limits across all prompts and code
- Enforce at parse time, not just generation time
- Consider using tokens instead of characters for multilingual text

---

## 8. Duplicate/Vague List Items

**Symptom**: Task lists contain duplicate entries (same paper twice) or vague items ("SORA相关论文" instead of a specific paper).

**Root Cause**: Lists generated from memory without dedup or specificity checks.

**Detection**:
- Check for exact or near-exact duplicates in any list
- Flag items containing words like: "相关", "等", "类似", "某" (vague markers in Chinese)

**Fix**:
- Add dedup pass before finalizing lists
- Require specific identifiers (full title, arXiv ID) for each item

---

## 9. Telegram Message Truncation

**Symptom**: Bot @usernames split across lines, breaking Telegram's mention parsing.

**Root Cause**: Message formatting doesn't account for line break insertion points near @mentions.

**Detection**: 
- Search for `@\w+_\w+\n\w+` patterns in Telegram messages
- Check if @mention is followed immediately by a newline

**Fix**:
- Ensure @mention + following text stays on same line
- Add post-processing to join broken mentions

---

## 10. Supervisor Echo Chamber

**Symptom**: Supervisor's ASSIGN message contains the full user task text + full previous worker report, creating extremely long messages with no information gain.

**Root Cause**: Supervisor's decision prompt includes all previous context verbatim. The model tends to repeat it rather than summarize.

**Detection**:
- Measure ASSIGN message length — anything >2000 chars is suspicious
- Check for repeated blocks between ASSIGN and previous REPORT

**Fix**:
- Supervisor prompt should explicitly say: "Summarize previous reports in 2-3 sentences. Do not repeat the full report."
- Consider truncating context before feeding to Supervisor's model call
