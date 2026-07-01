---
name: sequential-document-analysis
description: "Extract structured information from batches of documents by reading each file with AI semantic understanding (not grep/regex). Write results incrementally as you go."
tags: [document-analysis, extraction, batch-processing, semantic-understanding, read-file]
triggers:
  - Extracting structured data from many similar documents (exam papers, reports, contracts)
  - User explicitly requires "read each file" or "AI understanding" or "don't use grep"
  - Finding patterns that require context/nuance (not simple keyword matching)
  - Processing exam answer files to find specific question types
---

# Sequential Document Analysis

## Core Principle

When extracting structured information from batches of documents where **context matters** (e.g., distinguishing "同义替换" in a listening question vs. a reading question), you MUST:

1. **Read each file with `read_file`** — never use grep/regex/scripts to batch-search
2. **Use AI semantic understanding** — judge based on context, not keyword presence
3. **Write results incrementally** — append to the output file after processing each source file, don't accumulate in memory

**THE USER WILL REMIND YOU IF YOU FORGET #3.** Multiple times in past sessions, users have had to say "写入文件啊，咋不写啊" and "你咋不写入同义替换.md" because the agent kept reading files without writing. After processing EACH file, immediately write/append findings. No exceptions.

## Why Not Grep?

- Grep finds keyword occurrences but cannot distinguish context (e.g., "同义替换" in a listening question vs. a reading comprehension question)
- Grep misses paraphrased mentions (e.g., "同义转述", "同义表述", "同义改写", "同义复现")
- Grep cannot extract structured fields (question number, section, original text, answer) from surrounding context

## Workflow

```
For each source file:
  1. read_file(path, offset, limit) — read in chunks if large
  2. AI understands the structure (sections, question numbers, explanations)
  3. AI identifies target items based on semantic criteria
  4. AI extracts structured fields for each item
  5. write_file/patch → append findings to output file IMMEDIATELY
  6. Move to next file
```

### Pre-Scan Triage (for 20+ files)
Before reading every file, use `search_files` with `output_mode="count"` to rank files by keyword density. This tells you which files are worth reading first and which can be deprioritized. This is NOT extraction — it's triage. You still need semantic reading for extraction.

### Parallel Delegation (for 20+ files)
When there are many files to process, use `delegate_task` with batch mode (up to 3 parallel subagents). Each subagent handles a subset of files. Combine results afterward. Beware API rate limits — if subagents fail with HTTP 429, fall back to sequential.

### Background Processing
For long-running preprocessing (e.g., PDF→txt conversion), use `terminal(background=true, notify_on_complete=true)` with **heredoc format** for Python scripts:
```bash
python3 << 'PYEOF'
# script content
PYEOF
```
Inline `-c` with complex multi-line scripts can cause silent hangs. Heredoc avoids quoting/escaping issues.

### Critical: Write As You Go

**NEVER accumulate findings in memory across multiple files.** After processing each source file, immediately write/append results to the output file. Reasons:
- Sessions can be interrupted (user sends new message, /stop, timeout)
- Long sessions may lose context window — earlier findings get forgotten
- User can see progress in real-time by checking the output file
- If a later file fails, earlier results are preserved

### Handling Large Files

When a file exceeds `read_file`'s line limit:
```python
# Read in chunks
offset = 1
while True:
    result = read_file(path, offset=offset, limit=500)
    # Process this chunk
    if offset + 500 >= result['total_lines']:
        break
    offset += 500
```

Or use `read_file` with `offset` and `limit` to target specific sections if you know the structure (e.g., "listening section starts around line 50").

## File Name Mapping

When processing pairs of files (e.g., answer explanations + original exam papers), file names often don't match exactly:
- `2015.06英语六级考试第1套解析.txt` → `2015年06月六级真题（第1套）.txt`
- `2016年12月六级（第1套）答案及解析.txt` → `2016.12六级第1套试题.txt`

Build a mapping table at the start by listing both directories and fuzzy-matching, or hard-code known mappings. Don't assume a simple regex transform works.

## Output Format

Use a consistent Markdown structure:
```markdown
# Title

## Year + Set Number

### Q<N>（Section X · Type）
- **Field 1**: value
- **Field 2**: value
- ...

---

## Next Year + Set
```

## Pitfalls

1. **Don't use grep/regex for semantic extraction** — user will correct you. Scripts miss context, nuance, and edge cases. Always read with AI understanding.
2. **Don't forget to write results incrementally** — user will ask "why aren't you writing to the file?" after you've been reading multiple files without outputting anything.
3. **Don't mix up file structure** — some files have listening sections in Part II, others in Part III. Read the structure first before assuming layout.
4. **Some files share content** — e.g., "第3套" exam may share listening content with "第2套" (just different option order). Check for "特别说明" notes and skip duplicates.
5. **PDF conversion quality varies** — some converted files may be garbled. Check the first few lines of each converted file before reading. If garbled, re-convert with a different tool (PyMuPDF OCR fallback). **Critical: verify the FIRST converted file's quality before processing the rest of the batch.** Don't blindly convert 50 files only to discover they're all garbled.
6. **Session interruption recovery** — if the session is interrupted, check the output file to see how far you got, then resume from the next unprocessed source file.
7. **Don't get stuck reading without writing** — if you've read 3+ files without writing to the output file, STOP reading and write what you have. The user will get frustrated if they see you reading file after file with no output. Write partial results, then continue.
8. **Verify subagent results** — when using parallel delegation, subagent summaries are self-reports. A subagent may include items from the wrong section (e.g., reading comprehension results mixed with listening results). Cross-check a sample of results against the source files before writing to the final output.
9. **Distinguish section boundaries** — when analyzing structured documents (exams, reports), verify which section a result belongs to. Question numbers alone aren't sufficient — check the Part/Section headers to confirm whether an item is from the target section.
10. **Subagent API rate limits** — when dispatching 3 parallel subagents, 2 out of 3 may fail with HTTP 429 (too many requests). Each subagent makes multiple API calls (read_file, search_files), and the combined rate can exceed limits. Mitigations:
    - Reduce to 2 parallel subagents instead of 3
    - Give subagents fewer files each (6-8 instead of 12+)
    - If a subagent fails with HTTP 429, process its files manually in the parent session
    - Check subagent `exit_reason`: `completed` = reliable, `max_iterations` = may have incomplete results
11. **Subagent context isolation** — subagents have NO memory of the parent conversation. You MUST pass all relevant info via the `context` field: file paths, which files are already covered, section boundaries, what constitutes a valid match vs. false positive, and output format. The more specific the context, the better the results.
12. **Combined triage + extraction pattern** — for 30+ files, use a two-phase approach:
    - Phase 1: `search_files` with `output_mode="count"` to rank files by keyword density (triage, NOT extraction)
    - Phase 2: `delegate_task` to process high-count files in parallel batches
    - Phase 3: Manual `read_file` for files with 0 keyword hits but where implicit markers might exist
    - This is more efficient than reading every file sequentially, while still ensuring semantic understanding
13. **Patch tool fails on non-unique context** — when the markdown file has many structurally similar entries (e.g., 50+ questions with identical formatting), the `patch` tool's fuzzy matching can't find a unique match. Error: `Found N matches for old_string`. **Fix**: use `execute_code` with programmatic string replacement instead:
    ```python
    with open("output.md", "r") as f:
        content = f.read()
    content = content.replace(old_text, new_text, 1)  # replace first occurrence only
    with open("output.md", "w") as f:
        f.write(content)
    ```
    Use enough surrounding context in `old_text` to make it unique within the file. Test with `content.count(old_text)` first — if count > 1, add more context.

14. **`execute_code` read_file caching** — `read_file` from `hermes_tools` returns `{"status": "unchanged", "content_returned": False}` when the file hasn't changed since last read. The result dict has no `"content"` key, causing `KeyError`. **Fix**: read the file directly with Python's `open()` instead of going through the cached `read_file`:
    ```python
    with open("path/to/file.md", "r") as f:
        content = f.read()
    ```

15. **CRITICAL: `execute_code` read_file line number corruption** — when using `execute_code` with `from hermes_tools import read_file, write_file`, the `read_file` returns content with line number prefixes like `"123|content"`. If you process this content and write it back with `write_file` WITHOUT stripping the prefixes, the file gets permanently corrupted with embedded line numbers (e.g., `"123|# Title"` instead of `"# Title"`). **Fix**: always strip line prefixes before writing:
    ```python
    import re
    content = re.sub(r'^\d+\|(\d+\|)?', '', raw_content, flags=re.MULTILINE)
    ```
    Or better: use `terminal()` with `cat`/`sed` for file manipulation in `execute_code`, and reserve `write_file` for clean content you generate yourself. If corruption already happened, run the regex cleanup on the file.
