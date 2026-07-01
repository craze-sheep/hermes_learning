#!/usr/bin/env python3
"""
CET-6 Section A Word Bank Extractor
Extracts 15 cloze test word bank words from CET-6 exam PDFs.

Usage:
    python3 extract_cet_words.py <pdf_path>
    python3 extract_cet_words.py --batch <base_dir>
"""

import pymupdf
import os
import re
import sys


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

        # Extract words (handles O/0 confusion, extra apostrophes)
        word_pattern = r'([A-O0]\)[\'"]*\s*(\w+))'
        matches = re.findall(word_pattern, section_a_text)

        words = []
        for full_match, word in matches:
            if len(word) > 2:
                words.append(word)

        # Deduplicate while preserving order
        unique_words = []
        for word in words:
            if word not in unique_words:
                unique_words.append(word)

        return unique_words[:15]
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}", file=sys.stderr)
        return None


def batch_extract(base_dir):
    """Extract words from all CET-6 PDFs in a directory tree."""
    years_dirs = [
        ("2021年06月", "2021年06月CET6题+解+音频"),
        ("2021年12月", "2021年12月CET6题+解+音频"),
        ("2022年06月", "2022年06月CET6题+解+音频"),
        ("2022年12月", "2022年12月CET6题+解+音频"),
        ("2023年06月", "2023年06月CET6题+解+音频"),
        ("2023年12月", "2023年12月CET6题+解+音频"),
        ("2024年06月", "2024年06月CET6题+解+音频"),
        ("2024年12月", "2024年12月CET6题+解+音频【新】"),
    ]

    results = {}
    for year, dir_name in years_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if not os.path.exists(dir_path):
            continue

        pdf_dir = os.path.join(dir_path, "01、真题PDF版（推荐使用）")
        if not os.path.exists(pdf_dir):
            pdf_dir = dir_path

        pdf_files = sorted([f for f in os.listdir(pdf_dir) if f.endswith('.pdf')])
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            words = extract_section_a_words(pdf_path)
            if words:
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
                print(f"{key}: {', '.join(words)}")
            else:
                print(f"{pdf_file}: No words extracted", file=sys.stderr)

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_cet_words.py <pdf_path>")
        print("       python3 extract_cet_words.py --batch <base_dir>")
        sys.exit(1)

    if sys.argv[1] == "--batch":
        base_dir = sys.argv[2] if len(sys.argv) > 2 else "."
        batch_extract(base_dir)
    else:
        words = extract_section_a_words(sys.argv[1])
        if words:
            print(", ".join(words))
        else:
            print("No words found", file=sys.stderr)
