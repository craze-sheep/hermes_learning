# FastAPI API Gateway Reference

## Proven Architecture (Codex Relay)

Tested pattern for building API relay/gateway with FastAPI:

### File Map (20 files, ~1500 LOC)

```
app/
├── main.py              # FastAPI app, lifespan, router registration, uvicorn CLI
├── config.py            # dataclass(frozen=True) + dotenv, singleton settings
├── database.py          # aiosqlite, get_db() async context, init_db() with schema
├── models/schemas.py    # All Pydantic models in one file (Create/Update/Response per entity)
├── middleware/
│   ├── auth.py          # Bearer token → SHA256 → DB lookup (FastAPI Depends)
│   ├── admin_auth.py    # Fixed admin key comparison (FastAPI Depends)
│   └── logger.py        # AccessLogMiddleware (BaseHTTPMiddleware)
├── proxy/
│   ├── router.py        # Route lookup by model + user_group
│   ├── circuit_breaker.py  # Per-provider state machine (closed/open/half-open)
│   └── forwarder.py     # httpx forward, SSE streaming via event_generator()
├── store/
│   ├── user.py          # async CRUD, each func opens+closes own connection
│   ├── apikey.py        # generate_api_key() → (plaintext, sha256_hash)
│   ├── provider.py      # AES-256-GCM encrypt/decrypt for upstream keys
│   ├── route.py         # find_route() with JOIN on providers
│   └── usage.py         # create + query + dashboard_summary()
└── routers/
    ├── models.py        # GET /v1/models
    ├── responses.py     # POST /v1/responses → forwarder
    └── admin/
        ├── user.py      # CRUD /admin/users
        ├── apikey.py    # CRUD /admin/apikeys (plaintext key returned once)
        ├── provider.py  # CRUD /admin/providers + /test endpoint
        ├── route.py     # CRUD /admin/routes
        └── usage.py     # GET /admin/usage + /admin/dashboard
```

### Key Design Decisions

1. **Store layer = stateless functions** (not classes). Each function opens its own aiosqlite connection and closes it in `finally`. Simpler than connection pooling for SQLite.

2. **Auth as Depends()** — FastAPI's dependency injection. Two separate dependencies: `verify_api_key` (for Codex API) and `verify_admin_key` (for admin). Clean separation.

3. **SSE streaming** — use `httpx.AsyncClient.stream()` + `StreamingResponse` with `media_type="text/event-stream"`. Forward line-by-line, detect `[DONE]` sentinel.

4. **Circuit breaker** — in-memory dict keyed by provider_id. No persistence needed (resets on restart, which is fine).

5. **Config** — `dataclass(frozen=True)` + `python-dotenv` is lighter than pydantic BaseSettings for simple configs. Singleton `settings` instance.

6. **Static files** — mount with `StaticFiles(html=True)` LAST (it's a catch-all). Only mount if directory exists.

7. **Database path** — resolve relative to project root (`Path(__file__).parent.parent / db_path`). Ensure parent dir exists.

### Startup Sequence

```python
@asynccontextmanager
async def lifespan(app):
    await init_db()  # Create tables
    yield
    # Cleanup
```

### Testing Without Full Stack

```bash
# Health check
curl http://127.0.0.1:8080/health

# Create test data via admin API
curl -X POST http://127.0.0.1:8080/admin/users \
  -H "Authorization: Bearer $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","role":"admin"}'

# Create API key (returns plaintext once)
curl -X POST http://127.0.0.1:8080/admin/apikeys \
  -H "Authorization: Bearer $ADMIN_KEY" \
  -d '{"user_id":1,"name":"test"}'
# Save the "key" field!

# Test authenticated endpoint
curl http://127.0.0.1:8080/v1/models \
  -H "Authorization: Bearer <full-key>"
```

### Dependencies

```
fastapi>=0.110.0
uvicorn>=0.27.0
httpx>=0.27.0
httpx-sse>=0.4.0
aiosqlite>=0.20.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

Optional: `cryptography` for AES-256-GCM (falls back to base64 obfuscation without it).
