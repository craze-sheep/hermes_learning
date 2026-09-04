---
name: chinese-platform-research
description: "Research Chinese platforms (小红书, 知乎, 微博, etc.) when direct access is blocked by anti-bot detection. Fallback strategies using Baidu search, Jina reader, and GitHub API."
triggers:
  - user asks to search/research on 小红书, 知乎, 微博, or other Chinese platforms
  - CDP browser access to Chinese sites fails with IP risk or CAPTCHA
  - need to find Chinese-language content on technical topics
---

# Chinese Platform Research

## Problem
Chinese social media platforms (小红书, 知乎, 微博, etc.) have aggressive anti-bot detection:
- **小红书**: Blocks CDP access with IP risk detection (error code 300012), requires login for search results
- **知乎**: Triggers CAPTCHA verification for automated access
- **Bing/DuckDuckGo Chinese search**: Often triggers CAPTCHA, unreliable

## Strategy: Baidu + Jina Reader

**Primary approach**: Use Baidu search with Jina reader to extract content.

```bash
# General search
curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=关键词" | head -500

# Site-specific search (when you know the platform)
curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=关键词+site:xiaohongshu.com" | head -500

# Platform name in query (broader results)
curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=关键词+小红书" | head -500
```

**Why this works**:
- Baidu has good indexing of Chinese platform content
- Jina reader extracts text content efficiently
- Avoids direct platform access and its anti-bot measures

## Strategy: GitHub API for Technical Topics

For technical topics (like "号池搭建"), GitHub often has relevant open-source projects with detailed documentation.

```bash
# Search repositories
curl -s "https://api.github.com/search/repositories?q=关键词&per_page=5"

# Get specific repo README
curl -s "https://r.jina.ai/https://github.com/owner/repo"
```

## Pitfalls

### Search Engine CAPTCHAs
- **Bing**: Triggers CAPTCHA for Chinese queries from server IPs
- **DuckDuckGo**: Same issue, less reliable for Chinese content
- **Baidu**: Most stable for Chinese content search

### Content Quality
- Baidu results may contain ads - filter for organic results
- Small Red Book content is often image-heavy - text search may miss key info
- Gray-area topics (号池, 搭建) may have content removed due to platform censorship

### CDP Proxy Issues
- CDP proxy may timeout if browser authorization popup wasn't clicked
- Even with CDP working, Chinese platforms may still block based on IP

## Example: Researching "GPT号池搭建"

1. Try direct CDP access to 小红书 → fails with IP risk
2. Fall back to Baidu search:
   ```bash
   curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=GPT号池搭建" | head -400
   ```
3. Extract relevant links and summaries from results
4. For technical details, search GitHub:
   ```bash
   curl -s "https://api.github.com/search/repositories?q=GPT号池&per_page=5"
   ```
5. Access specific repositories for detailed documentation

## When to Use This Skill

- User asks to research something on 小红书, 知乎, or other Chinese platforms
- Direct browser access to Chinese sites fails
- Need Chinese-language technical content
- Looking for open-source projects related to Chinese tech ecosystem

## References

- See `references/baidu-search-patterns.md` for advanced Baidu query syntax
- See `references/github-api-search.md` for GitHub search techniques
