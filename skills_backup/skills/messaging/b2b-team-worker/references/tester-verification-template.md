# Tester Verification Report Template

Use this template when Supervisor assigns a structured verification/acceptance task with a numbered checklist.

## Execution Order

1. Structural checks (dirs, file counts, file presence) — batch in one loop
2. Semantic checks (grep for specific code patterns at specified lines)
3. Syntax/lint checks (py_compile, eslint, etc.)
4. Write ACCEPTANCE_REPORT.md to working directory
5. Compose MESSAGE with table-format results

## Report Format

```markdown
# 实验构建验收报告

**任务 ID：** B2B-YYYYMMDD-HHMMSS（源自 B2B-YYYYMMDD-HHMMSS）
**验收人：** Tester
**验收时间：** YYYY-MM-DD HH:MM
**工作目录：** `/path/to/working/directory`

## 验收清单

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | ... | ✅ PASS / ❌ FAIL |
| 2 | ... | ✅ PASS / ❌ FAIL |

## 修复验证详情（如适用）

### expXXX — filename.py
- 行 NNN: description of fix verified

## 验收结论

**全部 N 项验收检查均通过，无遗漏、无异常。**
```

## Bash Patterns for Common Checks

```bash
BASE=/path/to/experiments

# Check 1: Directory existence
ls -d $BASE/exp* | sed 's|.*/||'

# Check 2: File count per subdirectory
for d in $BASE/exp*/model; do
  count=$(ls "$d"/*.py 2>/dev/null | wc -l)
  echo "$(basename $(dirname $d)): $count"
done

# Check 3: Required file presence
for d in $BASE/exp*; do
  name=$(basename $d)
  cfg=$([ -f "$d/config_override.py" ] && echo "Y" || echo "N")
  run=$([ -f "$d/run.sh" ] && echo "Y" || echo "N")
  echo "$name: cfg=$cfg run=$run"
done

# Check 4-6: Specific code patterns
grep -n "pattern" $BASE/exp*/target_file.py

# Check 7: Syntax validation
for f in $BASE/exp*/*.py $BASE/exp*/model/*.py; do
  [ -f "$f" ] || continue
  python3 -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>&1
done
```
