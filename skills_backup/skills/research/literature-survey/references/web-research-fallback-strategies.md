# Web Research Fallback Strategies

When conducting online literature research, various failure modes can block access. This reference documents proven fallback strategies.

## Failure Modes and Responses

### 1. MCP fetch server unreachable
- **Symptom**: `MCP server 'fetch' is unreachable after 3 consecutive failures`
- **Fallback**: Use browser_navigate instead. Browser can render pages that fetch MCP cannot reach.
- **Note**: After 3+ consecutive MCP fetch failures, the tool enters a ~60s cooldown. Don't retry immediately.

### 2. arXiv /search page blocked by robots.txt
- **Symptom**: arXiv robots.txt disallows `/search`, `/find`, `/form` for all bots
- **Fallback**: Direct `https://arxiv.org/abs/<paper_id>` pages ARE accessible. Use known paper IDs to verify individually.
- **Verified**: arxiv.org/abs/ pages work reliably from browser (tested with 1502.03167, 1909.13231, 1911.08731, 2007.01434, 2012.07421, 1902.10811).

### 3. Google Scholar IP ban
- **Symptom**: Scholar shows "unusual traffic" or captcha page
- **Fallback**: Use Bing, Semantic Scholar API, or direct arxiv pages.
- **Note**: Google Scholar bans are IP-level and persistent within a session.

### 4. Semantic Scholar API rate limiting
- **Symptom**: `Too Many Requests. Please wait and try again`
- **Fallback**: Browser access to individual paper pages, or use the Semantic Scholar web interface instead of API.
- **Wait**: ~60s cooldown before retry.

### 5. Bing returning wrong-language results
- **Symptom**: Bing CN returns Chinese results even with English query + `setlang=en&mkt=en-US`
- **Fallback**: Add explicit English keywords, try `?cc=us&setlang=en-us`, or switch to "国际版" button on the page.
- **Note**: Bing may redirect to cn.bing.com regardless of language settings.

### 6. Google Scholar completely blocked (IP)
- **Symptom**: Page shows IP address and error message
- **Fallback**: Use Semantic Scholar website (not API), direct arxiv pages, or DBLP.

## Recommended Research Strategy (Tiered)

### Tier 1: Bulk search (preferred)
- Semantic Scholar API: `api.semanticscholar.org/graph/v1/paper/search?query=...&limit=10&fields=title,authors,year,abstract,venue`
- Google Scholar via browser
- arXiv search (if accessible)

### Tier 2: Targeted verification (fallback when Tier 1 fails)
- Identify candidate papers from training knowledge
- Verify each via `https://arxiv.org/abs/<paper_id>`
- Note which papers were verified vs. knowledge-only

### Tier 3: Knowledge-only (last resort)
- Write report from training knowledge with explicit disclosure
- Recommend search terms for user to verify independently
- Never claim papers were "found" or "searched" — say "基于训练知识引用"

## Key Insight

**Direct arxiv abs pages bypass robots.txt restrictions.** The robots.txt blocks `/search`, `/find`, `/form` but explicitly allows `/abs`, `/pdf`, `/html`. This is the single most reliable fallback for paper verification.
