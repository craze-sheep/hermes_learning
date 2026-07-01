# Extracting Structured Content from Exam PDFs

## pymupdf Regex Patterns for Chinese English Exams

### CET-4/CET-6 Section A Word Bank (选词填空)

CET-6 Section A provides 15 words labeled A) through O). Words may span multiple pages and be split by "Section B" headers.

```python
import pymupdf
import re

def extract_section_a_words(pdf_path):
    doc = pymupdf.open(pdf_path)
    full_text = "\n".join(page.get_text() for page in doc)
    
    # Find Section A — header ordering varies across PDFs
    for pattern in [
        r'Reading Comprehension.*?Section A',
        r'Section A\s+Reading Comprehension',
    ]:
        match = re.search(pattern, full_text, re.DOTALL)
        if match:
            section_text = full_text[match.end():]
            break
    else:
        return None
    
    # Extract words — O) sometimes rendered as 0), some PDFs add stray quotes
    word_pattern = r'[A-O0]\)[\'"]*\s*(\w+)'
    matches = re.findall(word_pattern, section_text)
    
    unique_words = []
    for word in matches:
        if len(word) > 2 and word not in unique_words:
            unique_words.append(word)
    return unique_words[:15]
```

### Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| "O)" not matched | OCR renders as "0)" | Include `0` in char class: `[A-O0]` |
| Missing words (e.g. K, O) | Word list split across pages with "Section B" in between | Search entire section text, not just first page |
| Typos in PDF text | OCR/conversion artifacts (e.g. "word bankf ollowing") | Don't rely on exact string matching for section delimiters |
| False positives from Section B/C | Same regex matches answer choices | Deduplicate and cap at 15; scope to text after "word bank" instruction |
| Header order varies | "Part III Section A Reading Comprehension" vs "Part III Reading Comprehension Section A" | Try multiple search patterns |
| Stray quotes after letter | Some PDFs have `K)' word` | Include `\'"` in pattern: `[\'"]*\s*` |

### Batch Processing Directory of Exam PDFs

```python
import os

base_dir = "/path/to/exams"
for year_dir in sorted(os.listdir(base_dir)):
    # Typical Chinese exam dir structure: year/01、真题PDF版/xxx第1套.pdf
    for subdir in os.listdir(os.path.join(base_dir, year_dir)):
        if "真题" in subdir and "PDF" in subdir:
            pdf_dir = os.path.join(base_dir, year_dir, subdir)
            break
    else:
        continue
    
    pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf') and '第1套' in f]
    if pdfs:
        words = extract_section_a_words(os.path.join(pdf_dir, pdfs[0]))
        print(f"{year_dir}: {', '.join(words)}")
```

## Real-World Directory Structure Patterns (CET-6)

Chinese exam PDF collections from Baidu Pan / educational sites follow inconsistent naming. Key patterns from actual CET-6 collections:

### Typical Layout

```
根目录/
├── 1990年-2018年真题资料【合集】/
│   ├── 2015年06月CET6题+解+音频/
│   │   ├── 01、真题PDF版（推荐使用）/
│   │   ├── 02、真题Word版/
│   │   ├── 03、答案解析/
│   │   └── 04、听力音频/
│   └── ...
├── 2019年06月CET6题+解+音频/
│   ├── 01、真题PDF版（推荐使用）/
│   ├── 02、答案解析/
│   └── ...
└── 2024年12月CET6题+解+音频【新】/
    ├── 01、真题PDF版（推荐使用）/
    ├── 02、答案解析/
    └── 03、听力音频/
```

### Subdirectory Naming Variations

The "真题PDF" folder name is NOT consistent across years:

| Variant | Example Year |
|---------|-------------|
| `01、真题PDF版（推荐使用）` | Most years |
| `01、真题PDF版（推荐打印）` | 2016年06月 |
| `01、真题PDF版（推荐打印版）` | Some older years |

**Always match with glob/startswith**, not exact string:
```python
for subdir in os.listdir(year_path):
    if subdir.startswith("01") and "真题" in subdir and "PDF" in subdir:
        pdf_dir = os.path.join(year_path, subdir)
```

### Other Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| Empty 0-byte PDFs after copy | WSL memory pressure during large batch copies from /mnt/d/ | Verify file sizes after copy: `find . -name "*.pdf" -size 0` |
| Some years have no subdirectories | 2020年07月 (COVID special session) has files directly in year folder, no `01、真题PDF版` wrapper | Check both `year/01*/*.pdf` and `year/*.pdf` |
| Answer PDFs mixed with exam PDFs | Answer files (解析) in `02、答案解析/` have similar names | Filter: exam PDFs contain "真题", answer PDFs contain "解析" or "答案" |
| 2020年07月 only 1 exam set | COVID延期, only 1 set administered | Don't expect 3 sets for every year |
| Word版 (.docx) alongside PDF | Some years have `02、真题Word版/` | Filter by `.pdf` extension when you only want PDFs |
