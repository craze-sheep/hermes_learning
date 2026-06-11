# PyMuPDF OCR Fallback for Garbled Docling Output

When docling produces garbled Unicode output (random CJK characters, symbols like `౽౻౼`, `ਠ ਴`), use PyMuPDF's built-in OCR as a fallback.

## Detection

After docling converts a file, check the first 10 lines:
```python
with open(txt_path, 'r') as f:
    first_lines = ''.join(f.readlines()[:10])
# If you see random symbols instead of readable text, it's garbled
```

## PyMuPDF OCR Script

```python
import os, fitz

def convert_with_ocr(pdf_path, txt_path):
    """Convert PDF to text using PyMuPDF OCR (chi_sim+eng)."""
    doc = fitz.open(pdf_path)
    full_text = []
    for i, page in enumerate(doc):
        tp = page.get_textpage_ocr(language='chi_sim+eng', dpi=150, full=True)
        text = page.get_text(textpage=tp)
        full_text.append(text)
        if (i + 1) % 10 == 0:
            print(f"  Page {i+1}/{len(doc)}", flush=True)
    doc.close()
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(full_text))

# Batch usage
pdf_dir = "/path/to/pdfs"
txt_dir = "/path/to/txt_output"
os.makedirs(txt_dir, exist_ok=True)

for name in garbled_file_list:
    pdf_path = os.path.join(pdf_dir, name + ".pdf")
    txt_path = os.path.join(txt_dir, name + ".txt")
    print(f"Converting: {name}.pdf ...", flush=True)
    convert_with_ocr(pdf_path, txt_path)
    print(f"  Done: {name}.pdf", flush=True)
```

## Characteristics

- **Slower** than docling (each page requires OCR processing)
- **More reliable** for scanned CJK PDFs where docling's model fails
- **No GPU required** (uses CPU-based Tesseract via PyMuPDF)
- **Quality**: readable but not perfect — some characters may be misrecognized
- **Best for**: older exam papers, scanned documents with complex layouts

## When to Use

1. Run docling first (it's faster and usually better quality)
2. Check the first converted file's output
3. If garbled, switch ALL remaining files to PyMuPDF OCR
4. Don't mix — if docling fails on one file, it will likely fail on similar files from the same era/publisher
