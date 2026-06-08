---
name: cet-exam-pdf-extraction
description: Extract structured content (word banks, passages, questions) from Chinese CET-4/6 exam PDFs using pymupdf. Handles format variations across years and publishers.
tags: [pdf, cet, exam, english, china, extraction, pymupdf]
triggers:
  - 用户要求从PDF中提取四六级/CET考试内容
  - 提取选词填空、阅读理解、听力等考试部分
  - 处理六级/四级真题PDF文件
---

# CET Exam PDF Extraction

## When to use
- Extracting word banks (选词填空 Section A), passages, questions, or answers from CET-4/6 exam PDFs
- Processing exam PDFs stored locally (common path: `题库/01六级历年真题及答案解析+听力音频/`)

## Prerequisites
```bash
pip install pymupdf
```

## Directory structure pattern
CET exam PDFs typically follow this structure:
```
<year>年<month>月CET6题+解+音频/
├── 01、真题PDF版（推荐使用）/
│   ├── <year>.<month>六级真题第1套.pdf
│   ├── <year>.<month>六级真题第2套.pdf
│   └── <year>.<month>六级真题第3套.pdf
├── 02、真题word版/
├── 03、答案解析/
└── 04、听力音频/
```

## Key extraction pattern: Section A word bank (选词填空)

### Step 1: Find Section A location
The reading comprehension Section A can appear in two formats:

**Format A** (2021 style): `Section A` appears BEFORE `Reading Comprehension`
```
Section A\s+Reading Comprehension
```

**Format B** (2022+ style): `Reading Comprehension` appears BEFORE `Section A`
```
Reading Comprehension.*?Section A
```

Use `re.DOTALL` flag for both patterns.

### Step 2: Extract word list
After locating Section A, find the word bank using this regex:
```python
word_pattern = r'([A-O0]\)[\'"]*\s*(\w+))'
```

**Critical notes:**
- The letter `O` may be OCR'd as `0` (zero) — pattern handles both
- Some PDFs have `K)' secondary` (extra apostrophe) — pattern handles this
- Words may span across pages — extract from full document text, not single page

### Step 3: Filter and deduplicate
```python
words = []
for full_match, word in matches:
    if len(word) > 2:  # Skip short fragments
        words.append(word)

# Deduplicate while preserving order
unique_words = []
for word in words:
    if word not in unique_words:
        unique_words.append(word)

return unique_words[:15]  # Section A always has 15 words
```

## Pitfalls

### P1: Third test suite may share content with second suite
Many CET exams have 3 test suites, but the 3rd suite's reading section is often IDENTICAL to the 2nd suite. The PDF may say:
```
本套阅读词汇理解与第2套内容完全一样，因此在本套真题中不再重复出现。
```
When this happens, mark it as "(与第2套相同)" rather than reporting extraction failure.

### P2: First-pass regex may match listening section options
The listening section also uses A) B) C) D) format. If your extraction returns words like "Pour", "Network", "Prepare" (listening option fragments), you're matching the WRONG section. Solution: always search starting from `Reading Comprehension.*?Section A`, not from the beginning of the document.

### P3: Some PDFs have only 1 page for 3rd suite
The 3rd suite PDF may be a stub with only writing + translation (no reading section). Check `len(doc)` — if it's 1 page, skip it.

### P4: OCR artifacts in word list
Common OCR errors in word banks:
- `K)' secondary` → should extract `secondary`
- `0) threshold` → the `0` is actually `O`
- `· J) safeguarded` → extra bullet point before letter

## Full extraction script template

```python
import pymupdf
import os
import re

def extract_section_a_words(pdf_path):
    """Extract 15 word bank words from CET Section A cloze test."""
    try:
        doc = pymupdf.open(pdf_path)
        full_text = ""
        for i in range(len(doc)):
            page = doc[i]
            full_text += page.get_text() + "\n"
        
        # Find Section A in Reading Comprehension
        patterns = [
            r'Reading Comprehension.*?Section A',
            r'Section A\s+Reading Comprehension',
        ]
        
        section_a_pos = None
        for pattern in patterns:
            match = re.search(pattern, full_text, re.DOTALL)
            if match:
                section_a_pos = match.end()
                break
        
        if not section_a_pos:
            return None
        
        section_a_text = full_text[section_a_pos:]
        
        # Extract words
        word_pattern = r'([A-O0]\)[\'"]*\s*(\w+))'
        matches = re.findall(word_pattern, section_a_text)
        
        words = []
        for full_match, word in matches:
            if len(word) > 2:
                words.append(word)
        
        # Deduplicate
        unique_words = []
        for word in words:
            if word not in unique_words:
                unique_words.append(word)
        
        return unique_words[:15]
    except Exception as e:
        return None

# Batch processing
def batch_extract(base_dir, years_dirs):
    results = {}
    for year, dir_name in years_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        pdf_dir = os.path.join(dir_path, "01、真题PDF版（推荐使用）")
        if not os.path.exists(pdf_dir):
            pdf_dir = dir_path
        
        pdf_files = sorted([f for f in os.listdir(pdf_dir) if f.endswith('.pdf')])
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            words = extract_section_a_words(pdf_path)
            if words:
                # Determine suite number
                if '第1套' in pdf_file:
                    suite = '第1套'
                elif '第2套' in pdf_file:
                    suite = '第2套'
                elif '第3套' in pdf_file:
                    suite = '第3套'
                else:
                    suite = '未知'
                key = f"{year} {suite}"
                results[key] = words
    return results
```

## Web fallback: Scrapling for missing years
When local PDFs are missing (e.g., 2025 exams), try Scrapling:
```bash
pip install scrapling curl_cffi playwright browserforge patchright msgspec
```

Use `StealthyFetcher` for sites with anti-bot protection:
```python
from scrapling import StealthyFetcher
fetcher = StealthyFetcher(auto_match=False)
page = fetcher.fetch(url)
text = page.get_all_text()
```

**Known working site:** `cet6.koolearn.com` (新东方在线) — has CET exam content but may be "更新中" (still updating) for recent exams.

**Known blocked sites:** `kekenet.com`, `hjenglish.com` — have SSRF protection that blocks Scrapling.

## Output format
Write results to a markdown file organized by year and suite:
```markdown
## 2024年06月

### 第1套
word1, word2, word3, ..., word15

### 第2套
word1, word2, word3, ..., word15

### 第3套
（与第2套相同）
```

## Support files
- `scripts/extract_cet_words.py` — ready-to-run extraction script (single PDF or batch mode)
- `references/scrapling-notes.md` — notes on using Scrapling for web fallback when PDFs are missing
