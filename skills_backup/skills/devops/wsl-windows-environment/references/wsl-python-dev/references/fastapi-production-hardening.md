# FastAPI Production Hardening for API Gateways

Research-backed patterns from one-api, LiteLLM, OpenAI docs, and FastAPI best practices.

## httpx Singleton Client (Connection Pooling)

**NEVER create a new httpx.AsyncClient per request** — causes connection leaks and no pooling.

```python
# app/http_client.py
import httpx
from app.config import settings

http_client: httpx.AsyncClient | None = None

def init_http_client() -> httpx.AsyncClient:
    global http_client
    http_client = httpx.AsyncClient(
        proxy=settings.proxy_url,
        timeout=httpx.Timeout(
            connect=10.0,    # TCP connect
            read=300.0,      # 5 min — LLMs are slow
            write=10.0,      # send
            pool=5.0,        # waiting for pool slot
        ),
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=30,
        ),
        transport=httpx.AsyncHTTPTransport(retries=1),
    )
    return http_client

async def close_http_client() -> None:
    global http_client
    if http_client is not None:
        await http_client.aclose()
        http_client = None
```

Use in lifespan:
```python
@asynccontextmanager
async def lifespan(app):
    await init_db()
    init_http_client()  # startup
    yield
    await close_http_client()  # shutdown
```

## Security Headers Middleware

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response
```

## Request Size Limit

```python
MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MB

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        cl = request.headers.get("content-length")
        if cl and int(cl) > MAX_BODY_SIZE:
            return JSONResponse(status_code=413, content={"error": "Payload too large"})
        return await call_next(request)
```

## Health Checks (Liveness + Readiness)

```python
@app.get("/health", include_in_schema=False)
async def liveness():
    return {"status": "ok"}

@app.get("/health/ready", include_in_schema=False)
async def readiness():
    try:
        db = await get_db()
        await db.execute("SELECT 1")
        await db.close()
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
```

## Error Handling (Don't Leak Internals)

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"message": "Internal server error", "type": "server_error"}},
    )
```

## Production Config (Disable Docs)

```python
_is_prod = settings.log_level.upper() in ("WARNING", "ERROR")

app = FastAPI(
    title="Codex Relay" if not _is_prod else None,
    docs_url="/docs" if not _is_prod else None,
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)
```

## SSE Streaming: Responses API vs Chat Completions

**Critical difference:** Responses API does NOT use `[DONE]` sentinel. It ends with a `response.completed` event.

Responses API event format:
```
event: response.output_text.delta
data: {"type":"response.output_text.delta","delta":"Hello"}

event: response.completed
data: {"type":"response.completed","response":{"usage":{"input_tokens":10,"output_tokens":5}}}
```

Chat completions format (different):
```
data: {"choices":[{"delta":{"content":"Hello"}}]}
data: [DONE]
```

Forwarding strategy:
- Forward both `event:` and `data:` lines as-is
- Parse `data:` JSON only for usage extraction
- Handle `[DONE]` as fallback for chat completions compatibility
- Extract usage from `response.completed` event's `response.usage` field

## Middleware Stack Order

Register in this order (outermost first):
1. CORSMiddleware
2. SecurityHeadersMiddleware
3. RequestSizeLimitMiddleware
4. AccessLogMiddleware

## Graceful Shutdown

```python
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=settings.port,
    timeout_graceful_shutdown=30,  # wait 30s for in-flight requests
)
```

## Dependencies for Production

```
fastapi>=0.110.0
uvicorn>=0.27.0
httpx>=0.27.0
httpx-sse>=0.4.0
aiosqlite>=0.20.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

Optional: `cryptography` for AES-256-GCM encryption.
