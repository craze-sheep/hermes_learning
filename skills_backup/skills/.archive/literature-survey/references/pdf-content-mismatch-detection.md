# PDF Content Mismatch Detection

## Problem

Downloaded PDFs may contain the WRONG paper. This happens when:
- arxiv ID collision (different papers share similar IDs)
- Download URL redirected to a different paper
- File was manually placed with wrong name

## Known Mismatches (detected 2026-05-31)

| Directory | Expected Paper | Actual Content | arXiv ID Issue |
|-----------|---------------|----------------|----------------|
| 033_ssim | SSIM (Wang 2004) | ENNS: Variable Selection paper | Wrong PDF placed |
| 035_fvd | FVD (Unterthiner 2018) | Kundt's tube physics paper | ID collision |
| 012_iodine | IODINE (Greff 2019) | Particle dynamics software | Should be 1903.00450, not 1906.10963 |
| 048_ocvp | OCVP | XAIxArts workshop paper | PDF/code mismatch |
| 049_curriculum_learning | Curriculum Learning (Bengio 2009) | Differential geometry paper | Wrong PDF placed |
| 028_e3d_lstm | E3D-LSTM (Wang 2019) | Superconductor physics paper | arXiv ID collision |

## Detection Method

1. **Extract first page text** and compare with expected title:
   ```bash
   pdftotext -l 1 paper.pdf - | head -5
   ```

2. **Check arXiv metadata** via mcp_fetch:
   ```
   mcp_fetch("https://arxiv.org/abs/<arxiv_id>")
   ```
   Compare the title on the arxiv page with the directory name.

3. **Cross-reference with code repo README** — the README usually has the correct paper title and arxiv link.

## When to Flag

During notes.md rewrite, if the PDF content doesn't match the directory name:
- Add a warning at the top of notes.md: "⚠️ PDF 内容与论文不匹配"
- Write notes based on: (1) code analysis, (2) arxiv abstract via mcp_fetch, (3) known paper content
- Mark in the summary report as needing PDF re-download

## Correct arXiv IDs for Problematic Papers

| Paper | Correct arXiv ID | Notes |
|-------|-----------------|-------|
| IODINE | 1903.00450 | NOT 1906.10963 |
| FVD | 1812.01717 | Published at NeurIPS 2018 Workshop |
| Curriculum Learning | 0912.1881 | Bengio et al., ICML 2009 |
| SSIM | No arXiv | Published in IEEE TIP 2004, Vol 13 No 4 |
