## Rejection Case 4: Wrong Header Kind (2026-05-31)

**Original rejected MESSAGE excerpt:**

```
[B2B-20260531-131141][Developer][完成]
@TeamSupervisor_bot

已完成对项目的只读代码审查...
```

**Rejection reason:** "worker 群消息只能使用 [B2B-20260531-131141][Developer][REPORT] 作为开头，不能使用 [B2B-20260531-131141][Developer][完成]。"

**Root cause:** Used `[完成]` (Chinese for "completed") instead of the required `[REPORT]` kind. The outbound validator does `found_kind.upper() != "REPORT"` — only the exact word `REPORT` (case-insensitive) passes.

**Fixed version:**

```
[B2B-20260531-131141][Developer][REPORT]
@TeamSupervisor_bot

已完成对项目的只读代码审查...
```

**Key fix:** Changed `[完成]` → `[REPORT]`. Only `[REPORT]` is valid for worker messages. All other kinds (WORKING, STATUS, ASSIGN, DONE, ERROR, or any Chinese equivalent) are rejected.

**Additional lesson:** The substantive analysis report was already written to `artifacts/tasks/.../files/project-analysis-report.md` in the first attempt. On retry, the report file was still on disk — only the Telegram MESSAGE header needed fixing. Don't redo work that's already saved; just fix the format.

---

## Rejection Case 5: Message Too Long (2026-05-31)

**Scenario:** Planner produced a detailed experiment screening strategy with tables, execution commands, risk assessments, and multi-phase plans — all inline in the Telegram MESSAGE.

**Rejection reason:** `BadRequest: Message is too long` — Telegram enforces ~4096 character limit for bot messages. The full plan exceeded this.

**Supervisor response:** "上条回复因太长被 Telegram 拒绝。请精简输出，控制在 500 字以内。"

**Root cause:** Planner treated the Telegram MESSAGE as the primary deliverable and embedded the entire plan inline. The role contract (planner.md) says to produce Markdown-archivable output, but doesn't warn about Telegram's character limit.

**Fixed approach:**
1. Write the full plan to a file (e.g., `experiments/screening_plan.md`)
2. Keep the Telegram MESSAGE as a short summary (~300-500 chars):
   - What was planned (1 sentence)
   - Key numbers (baseline, targets)
   - Deliverable file path
   - Next step recommendation

**Example shortened MESSAGE:**
```
[B2B-20260531-201926][Planner][REPORT]
@TeamSupervisor_bot

筛选策略已产出：阶段1 smoke test(3步)筛无报错+loss下降，阶段2 候选完整训练(50步)对比baseline(0.5451)。
建议先筛5个低风险实验。详见 experiments/screening_plan.md

HANDOFF_SUMMARY: 筛选策略：smoke test→候选完整训练→对比baseline。详见文件。
```

**Key lesson:** The MESSAGE is a **notification**, not the deliverable. The deliverable goes in a file. If the plan is more than ~2000 chars, it MUST go in a file with only a summary in the MESSAGE.
