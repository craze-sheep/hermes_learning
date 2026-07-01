# Scrapling Web Scraping Notes

## Installation
```bash
pip install scrapling curl_cffi playwright browserforge patchright msgspec
```

All 7 packages are required - Scrapling has deep dependency chain.

## Fetcher types
- `Fetcher` - basic HTTP requests (blocked by many Chinese sites)
- `StealthyFetcher` - uses patchright (stealth Playwright), best for anti-bot sites
- `DynamicFetcher` - for JS-rendered pages

## Working with Chinese exam sites

### cet6.koolearn.com (新东方在线)
- Status: Works with StealthyFetcher
- Content: CET-4/6 exam answers, translations, listening scripts
- URL pattern: `https://cet6.koolearn.com/YYYYMMDD/NNNNNN.html`
- Caveat: Recent exams may show "更新中" (still updating) - reading sections often published last

### kekenet.com (可可英语)
- Status: Blocked by SSRF protection (redirects to 127.0.0.1)
- Workaround: None found; use local PDFs instead

### hjenglish.com (沪江英语)
- Status: Blocked by SSRF protection
- Workaround: None found

## Anti-pattern: robots.txt with mcp_fetch_fetch
Standard fetch tools are blocked by robots.txt on Baidu, Google, DuckDuckGo. Scrapling StealthyFetcher bypasses this.
