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
