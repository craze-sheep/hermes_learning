# FastAPI Middleware Review Patterns

## Common Issues in FastAPI API Gateways

### 1. Content-Length Header Parsing
Always wrap `int(content_length)` in try/except. Malformed headers cause ValueError:
```python
# BAD — crashes on "Content-Length: abc"
if content_length and int(content_length) > MAX:

# GOOD — returns 400 on malformed header
if content_length:
    try:
        if int(content_length) > MAX:
            return JSONResponse(status_code=413, ...)
    except ValueError:
        return JSONResponse(status_code=400, ...)
```

### 2. Streaming Error Leaks
Never forward raw upstream error bytes to clients. Sanitize:
```python
# BAD — leaks upstream internals
yield f"data: {error_body.decode()}\n\n"

# GOOD — generic error message
yield 'data: {"error": {"message": "Upstream error", "type": "server_error"}}\n\n'
```

### 3. httpx Client Lifecycle
Never create `httpx.AsyncClient()` per request (connection leak). Use singleton:
```python
# At startup
client = httpx.AsyncClient(timeout=..., limits=...)
# In handlers
resp = await client.post(url, ...)
# At shutdown
await client.aclose()
```

### 4. CORS with Credentials
`allow_origins=["*"]` + `allow_credentials=True` is invalid per CORS spec. Either:
- Use `["*"]` without credentials, OR
- Specify exact origins with credentials

### 5. Exception Handler Ordering
Register handlers from most specific to least specific:
1. `RequestValidationError` (422)
2. `StarletteHTTPException` (4xx/5xx)
3. `Exception` (catch-all 500)

### 6. Health Check DB Connections
Readiness probes that open new DB connections on every call can exhaust pools under high-frequency polling. Consider caching the result briefly (e.g., 5s TTL).

### 7. Production Detection
Don't use `log_level` to detect production mode. Use an explicit `APP_ENV` or `ENV` variable.

## SSE / Streaming Review Checklist
- [ ] Content-Type: text/event-stream
- [ ] Cache-Control: no-cache
- [ ] Connection: keep-alive
- [ ] X-Accel-Buffering: no (for nginx)
- [ ] Client disconnect handling (context cancellation)
- [ ] Error events don't leak upstream details
- [ ] Proper event format forwarding (event: + data: lines)
