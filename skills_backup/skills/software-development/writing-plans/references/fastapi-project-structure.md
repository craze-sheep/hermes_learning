# FastAPI Project Structure Reference

Standard layout for a FastAPI API gateway / relay service.

## Directory Structure

```
project-root/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, router registration, uvicorn CLI
│   ├── config.py             # Settings via python-dotenv (dataclass or pydantic BaseSettings)
│   ├── database.py           # aiosqlite connection + schema init (WAL mode)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic request/response schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── models.py         # Business logic endpoints
│   │   └── admin/
│   │       ├── __init__.py
│   │       ├── user.py       # /admin/users CRUD
│   │       ├── apikey.py     # /admin/apikeys CRUD
│   │       ├── provider.py   # /admin/providers CRUD + test
│   │       ├── route.py      # /admin/routes CRUD
│   │       └── usage.py      # /admin/usage + /admin/dashboard
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py           # Bearer token auth (FastAPI Depends)
│   │   ├── admin_auth.py     # Admin key auth
│   │   ├── rate_limit.py     # Token bucket RPM/TPM
│   │   └── logger.py         # Access log middleware (BaseHTTPMiddleware)
│   ├── proxy/
│   │   ├── __init__.py
│   │   ├── router.py         # Upstream provider selection
│   │   ├── circuit_breaker.py # Per-provider circuit breaker
│   │   └── forwarder.py      # HTTP proxy (httpx, streaming via httpx-sse)
│   ├── store/
│   │   ├── __init__.py
│   │   ├── user.py           # Async CRUD (aiosqlite)
│   │   ├── apikey.py         # CRUD + key generation (SHA256 hash)
│   │   ├── provider.py       # CRUD + AES encryption for upstream keys
│   │   ├── route.py          # CRUD + route lookup
│   │   └── usage.py          # Write + query + dashboard aggregation
│   └── static/
│       └── index.html        # Single-file SPA (Alpine.js + TailwindCSS CDN)
├── .env                      # Runtime config (gitignored)
├── .env.example              # Template
├── .gitignore
├── requirements.txt
├── docs/
│   └── specs/
└── README.md
```

## Key Patterns

### Config Loading
```python
# app/config.py
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
```

### Database (aiosqlite)
```python
async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db
```

### Auth Middleware (FastAPI Depends)
```python
from fastapi.security import HTTPBearer
_security = HTTPBearer(auto_error=False)

async def verify_api_key(credentials=Depends(_security)):
    token = credentials.credentials
    key_hash = hashlib.sha256(token.encode()).hexdigest()
    key_info = await get_key_by_hash(key_hash)
    if not key_info: raise HTTPException(401, "Invalid API key")
    return key_info
```

### App Lifespan (startup/shutdown)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # startup
    yield
    # shutdown
app = FastAPI(lifespan=lifespan)
```

### Static Files (go:embed equivalent)
```python
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
```
Must be registered LAST (catch-all).

### SSE Streaming (httpx)
```python
async with client.stream("POST", url, headers=headers, json=body) as resp:
    async for line in resp.aiter_lines():
        if line.startswith("data: "):
            yield f"{line}\n\n"
```

## Startup Command
```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate <env>
python -m app.main
# Or: uvicorn app.main:app --host 0.0.0.0 --port 8080
```
