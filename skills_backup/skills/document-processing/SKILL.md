---
name: document-processing
description: "Process documents: PDF extraction (OCR, text, tables), PDF editing, batch document analysis, exam paper extraction."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Documents, PDF, OCR, Extraction, Analysis, Editing, Batch-Processing]
---

# Document Processing

Extract text from PDFs and scans, edit PDF content, analyze document batches, and process exam papers.

## 1. PDF Text Extraction

### pymupdf (fastest, no OCR)
```python
import pymupdf
doc = pymupdf.open("file.pdf")
for page in doc:
    text = page.get_text()          # plain text
    text = page.get_text("dict")    # structured (blocks, spans, fonts)
```

### marker-pdf (OCR + structure)
```bash
pip install marker-pdf
marker_single input.pdf --output_dir output/  # converts to markdown
```

### pdftotext (CLI, lightweight)
```bash
pdftotext -layout file.pdf output.txt    # preserve layout
pdftotext -table file.pdf output.txt     # table extraction
```

### Scanned PDFs (need OCR)
```bash
# Tesseract OCR
sudo apt install tesseract-ocr
pip install pytesseract Pillow

# For Chinese/English mixed docs
marker_single input.pdf --output_dir output/ --langs en,zh
```

## 2. PDF Editing (nano-pdf)

Edit PDF text/typos via natural language commands:
```bash
nano-pdf edit "fix typo on page 3: 'teh' → 'the'" input.pdf output.pdf
```

## 3. Batch Document Analysis

For processing many documents with structured extraction:

### Sequential Analysis Pipeline
1. **Extract** text from each document (PDF, scan, image)
2. **Parse** structured fields (dates, names, amounts, addresses)
3. **Validate** against expected schema
4. **Aggregate** results into summary report

### Pattern: Parallel extraction with sequential validation
```python
# Extract in parallel (CPU-bound)
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor() as pool:
    results = list(pool.map(extract_text, pdf_paths))

# Validate sequentially (needs context)
for result in results:
    validate_fields(result)
    aggregate_stats(result)
```

## 4. Exam Paper Extraction (CET-specific)

For Chinese exam papers (CET-4/6, TOEFL, IELTS):

### Extraction Pipeline
1. **Identify sections:** Listening, Reading, Writing, Translation
2. **Extract question banks:** Multiple choice options, answer keys
3. **Parse passages:** Reading comprehension texts
4. **Structure output:** JSON/CSV with section, question number, content

### Tips for exam papers
- Use `marker-pdf` for complex layouts (columns, images mixed with text)
- Fall back to `pdftotext -layout` for simple single-column papers
- Answer keys are usually in a separate PDF or appendix
- Watch for: page headers/footers contaminating question text

## Choosing the Right Tool

| Need | Tool | Notes |
|------|------|-------|
| Quick text extraction | pymupdf | Fastest, no OCR |
| Scanned documents | marker-pdf | OCR + markdown output |
| CLI extraction | pdftotext | Lightweight, layout-aware |
| Edit PDF text | nano-pdf | Natural language commands |
| Batch processing | Sequential pipeline | Parallel extract, sequential validate |
| Exam papers | marker-pdf + custom parser | Complex layouts |

## Pitfalls

- **pymupdf can't do OCR** — for scanned PDFs, use marker-pdf or tesseract
- **pdftotext layout mode** — `-layout` preserves visual layout but may break structured parsing
- **marker-pdf is slow** — takes 10-30 seconds per page; use pymupdf for simple text PDFs
- **Chinese text extraction** — ensure correct language pack is installed for OCR tools
- **Large PDFs** — process page-by-page, don't load entire document into memory
- **PDF with images** — text in images requires OCR; text layer may be empty
