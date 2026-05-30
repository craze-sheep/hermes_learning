# Documentation Quality Review Methodology

Module-by-module audit of project documentation (README, 项目说明, API docs, user guides). Unlike design-doc review (which checks a spec before implementation), this checks the DOCUMENTATION ITSELF for quality, completeness, and actionability.

## When to Use

- User asks to "review", "audit", "审查", or "check" a documentation file
- Evaluating a README, project guide, API reference, or setup doc
- Not about code diffs or bug investigation — this is doc quality assessment

## Step 1: Identify Document Structure

Read the full document and identify its logical modules/sections. Typical project README modules:

1. Project overview / goals
2. Current status / version
3. Architecture / design decisions
4. Directory structure / artifacts
5. Configuration (env vars, config files)
6. Setup / installation
7. Usage / commands
8. Testing
9. Limitations / known issues
10. Contributing / changelog

## Step 2: Define Evaluation Dimensions

Apply the SAME dimensions to EVERY module for consistency:

| Dimension | What to Check |
|-----------|---------------|
| **Completeness** | Are all necessary pieces present? Missing env vars, deps, system requirements? |
| **Accuracy** | Are technical details correct? Do commands match actual scripts? |
| **Consistency** | Do different sections agree? Same terms, same values, same paths? |
| **Maintainability** | Is there version info, update dates, changelog? Can someone else update this? |
| **Security** | Are secrets handled properly? Access controls documented? Sensitive info exposed? |
| **Operability** | Can a reader actually DO something with this? Are commands runnable as-is? |

## Step 3: Module-by-Module Review

For EACH module, produce a structured block:

```
#### [Module Name]
✅ Strengths:
- [What's good]

⚠️ Issues:
- [What's missing or wrong]

Suggestion:
- [Concrete improvement with example]
```

Severity levels:
- ✅ Strength — works well, note it
- ⚠️ Issue — missing, wrong, inconsistent, or unclear
- (no emoji) Suggestion — could be better but not broken

## Step 4: Cross-Module Consistency Check

After individual modules, check for SYSTEMIC issues:

- Terminology drift (same concept named differently in different sections)
- Contradictions (one section says X, another says Y)
- Missing cross-references (section A assumes knowledge from section B but doesn't link)
- Duplicated information (same fact stated in multiple places, potentially differently)

## Step 5: Scoring

Rate each dimension on a 1-10 scale:

| Dimension | Score | Notes |
|-----------|-------|-------|
| Completeness | X/10 | [brief justification] |
| Accuracy | X/10 | [brief justification] |
| Consistency | X/10 | [brief justification] |
| Maintainability | X/10 | [brief justification] |
| Security | X/10 | [brief justification] |
| Operability | X/10 | [brief justification] |
| **Overall** | **X/10** | |

## Step 6: Priority-Ranked Recommendations

Group improvements into three tiers:

**High Priority (must fix):**
- Items that would cause setup failure, security issues, or user confusion
- Example: missing env var that's required for the service to start

**Medium Priority (should fix):**
- Items that reduce usability or maintainability
- Example: missing architecture diagram, inconsistent terminology

**Low Priority (nice to have):**
- Items that improve polish but aren't blocking
- Example: adding a table of contents, changelog, contributing guide

## Output Format

```markdown
## [Document Name] Review Report

**Review Date:** YYYY-MM-DD
**Review Method:** Module-by-module audit with 6-dimension evaluation

### Module Reviews
[Step 3 output for each module]

### Overall Assessment
[Step 4 cross-module findings]

### Scoring
[Step 5 table]

### Recommendations
[Step 6 priority-ranked list]

### Summary
[1-2 paragraph overall verdict]
```

## Pitfalls

- Don't just list what's missing — also note what's GOOD (✅ strengths). Balanced reviews are more actionable.
- Scoring is subjective; justify each score with specific evidence from the document.
- "Missing" is not always an issue — some docs intentionally omit certain sections. Note when omission seems deliberate vs accidental.
- For non-English documents, review in the document's language. Don't force English terminology.
- When the document references external files (config templates, scripts), check if those files actually exist in the project if possible.
