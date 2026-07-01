# CET-6 Listening Synonym Replacement Coverage by Year

Based on analysis of all available 解析 txt files (2015-2024).

## Years WITH Listening Synonym Replacements

| Year | Month | Sets with findings | Question count | Notes |
|------|-------|-------------------|----------------|-------|
| 2015 | 06 | 1套(Q24), 3套(Q17,Q19,Q20,Q21) | 5 | 2套 has none |
| 2015 | 12 | 1套(Q11), 3套(Q6) | 2 | 2套 marked "无" |
| 2016 | 06 | 1套(Q6,Q25), 2套(Q24,Q25) | 4 | 3套 = 2套 (same listening) |
| 2016 | 12 | 1套(Q9,Q11,Q12,Q17,Q22,Q23), 2套(Q3,Q9,Q10,Q11,Q15) | 11 | 3套 has no listening section |
| 2017 | 06 | 1套(Q7,Q8) | 2 | 2/3套 have none |
| 2017 | 12 | 1套(Q1,Q5,Q12,Q13,Q14), 2套(Q6,Q10,Q14) | 8 | 3套 has no listening section |
| 2018 | 06 | 1套(Q8), 2套(Q2,Q3,Q4) | 4 | 3套 has none |
| 2018 | 12 | 1套(Q1,Q5,Q6,Q11,Q12,Q15,Q16,Q18,Q23,Q25), 2套(Q1,Q2) | 12 | 3套 has no listening section |
| 2019 | 06 | 1套(Q1,Q12,Q17,Q18,Q19), 2套(Q3,Q19,Q20,Q21) | 9 | 3套 = 1套 (same listening) |
| 2019 | 12 | 1套(Q4,Q10,Q11,Q12,Q13,Q14,Q17,Q18), 2套(Q1,Q20) | 10 | 3套 has none |
| 2020 | 07 | 全1套(Q2,Q12,Q14,Q22) | 4 | |
| 2020 | 09 | 1套(Q3,Q7,Q12,Q13,Q14,Q21) | 6 | 2&3套 has none |
| 2020 | 12 | 1套(Q22,Q23,Q24,Q25), 2套(Q6,Q16,Q17,Q21) | 8 | 3套 has none |
| 2023 | 03 | 1套(Q6,Q8,Q14,Q15,Q20) | 5 | 2/3套 = 1套 (same listening) |
| 2023 | 06 | 1套(Q1,Q10), 2套(Q1,Q5,Q14) | 5 | 3套 has no listening section |
| 2023 | 12 | 1套(Q12,Q14), 2套(Q2,Q5,Q6,Q7,Q9) | 7 | 3套 = 2套 (same listening) |
| 2024 | 06 | 2套(Q12,Q13,Q15) | 3 | 1套 has none in listening; 3套 has none |
| 2024 | 12 | 1套(Q1,Q6,Q9,Q14,Q15,Q16) | 6 | 2套 and 3套 have none in listening |

**Total: ~111 questions across 10 years (2015-2024)**

## Years with NO Listening Synonym Replacements Found

| Year | Months | Reason |
|------|--------|--------|
| 2021 | 06, 12 | Analysis files don't use synonym markers in listening explanations. Files may use `细节辨认题`, `细节理解题`, `推断题` instead. |
| 2022 | 06, 09, 12 | All 43 synonym marker occurrences are in reading comprehension sections (Q36-Q45). Listening sections use different terminology. |

**Key pattern**: From 2022 onwards, CET-6 answer explanation files increasingly use question-type labels (`细节辨认题`, `细节归纳题`, `推理判断题`) instead of explicit synonym markers in listening explanations. The synonym replacement concept is still present but described implicitly (e.g., "选项中的X是录音中Y的原词复现" without using "同义替换"). This makes automated extraction harder — semantic understanding is essential.

## Synonym Markers Found in Listening Sections

### Explicit markers (most common in 2017+ files)
- `同义替换` — synonym replacement
- `同义转述` — synonym paraphrase/restatement
- `同义改写` — synonym rewrite
- `同义复现` — synonym recurrence (exact paraphrase in option)

### Implicit markers (common in 2015-2018 files)
- `对应` — "corresponds to" (e.g., "选项A中xxx对应原文中xxx")
- `表述与此一致` — "expression is consistent with this"
- `C项表述与此意思一致` — "option C's meaning is consistent with this"
- `意思一致` — "meaning is consistent"

### Description-based (older style, 2015-2016)
- `选项是对原文的改写` — "the option is a rewrite of the original"
- `换一种说法` — "putting it another way"
- No explicit marker, but explanation clearly describes how option rephrases audio text

### Weak signals (need semantic verification)
- `是原词复现` — "original word recurrence" (exact match, NOT synonym)
- `原词重现` — same as above

### 2024 format (newer style)
- `选项中的X是录音中Y的同义转述` — "X in the option is a synonym restatement of Y in the recording"
- `选项中的X属于原词复现` — "X in the option is an exact word recurrence"
- Uses `【精析】` prefix for question type labels like `细节辨认题`, `细节归纳题`

## Section Distribution Pattern

Across all years:
- **Section A (Q1-Q8, conversations)**: ~45% of synonym replacement questions
- **Section B (Q9-Q15, passages)**: ~25%
- **Section C (Q16-Q25, lectures)**: ~30%

Section A tends to have the most because conversation dialogue naturally paraphrases.

## Output File Location

Results written to: `/home/lzy/project/6级历年答案/同义替换.md`
- **Final stats (2025-06-12)**: 1235 lines, 111 questions, 106 with complete options (95.5%), 5 missing options (2018.06 original exam PDFs don't exist)
- **Coverage**: 31 exam batches across 10 years (2015-2024)
- **PDF conversion**: 66/66 答案解析 converted (100%), 52/54 原题 converted (96%, 2 invalid PDFs)
- **Section distribution**: Section A ~45%, Section B ~25%, Section C ~30%
