# arXiv Paper Verification Workflow

When given a **candidate paper list** (e.g., from a Supervisor or user), the first step before deep analysis is verifying each paper's metadata. This is "Phase 0" of a literature survey.

## Workflow

1. **For each candidate paper**, navigate to `https://arxiv.org/abs/<ID>` if the ID is known
2. **If ID is unknown**, use arXiv search: `https://arxiv.org/search/?query=<title+keywords>&searchtype=all`
3. **Extract and verify**:
   - Full paper title
   - All authors
   - Year submitted / year published
   - Conference/journal (from Comments field on arXiv)
   - arXiv ID and PDF link
   - Code repo link (check Comments field, or search GitHub)
4. **Handle edge cases**:
   - Duplicate entries in candidate list → replace with another representative paper
   - Papers without formal publication (e.g., blog-only like Sora) → note as "无正式论文" and provide alternatives
   - Wrong arXiv ID in candidate list → search by title to find correct ID
   - Workshop papers → note as workshop, not main conference

## arXiv Page Structure

Key fields on `https://arxiv.org/abs/<ID>`:
- **Title**: in `<h1>` heading
- **Authors**: listed below title
- **Comments**: often contains conference info (e.g., "Published at ICLR 2021")
- **Subjects**: category (cs.LG, cs.AI, cs.CV, etc.)
- **PDF link**: `https://arxiv.org/pdf/<ID>`
- **Related DOI**: for published versions (Nature, etc.)

## Search Tips

- Use **paper title** as primary search query
- Add **author name** or **conference name** for disambiguation
- Search with **quoted phrases** for exact matches
- The arXiv Comments field often reveals the actual conference venue

## Output Format

Compile verified papers into a structured Markdown file with:
1. **Summary table** (one row per paper with key columns)
2. **Detailed per-paper sections** (full metadata)
3. **Sub-direction classification** (group by research theme)
4. **PDF download link table** (for batch downloading)
5. **Code repo table** (with language and official/unofficial status)
6. **Verification status checklist**

## Pitfalls

1. **Assuming arXiv IDs are correct** — Candidate lists from users may have wrong IDs. Always verify by loading the arXiv page.
2. **Missing conference info** — Not all papers list their conference on arXiv. Check the Comments field carefully.
3. **Duplicate entries** — Users may list the same paper twice under different names (e.g., "DayDreamer" appearing twice). Deduplicate and replace.
4. **Closed-source papers** — Some papers (e.g., Sora, GAIA-1) have no public code. Note this explicitly.
5. **Non-official code repos** — Mark repos as "非官方复现" when they're community reimplementations, not author-released code.
6. **Batch parallel downloads** — arXiv PDFs should be downloaded sequentially (not parallel) to avoid timeouts in slow networks.
