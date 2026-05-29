# Import Mismatch Recovery Pattern

## Real Example from 2026-05-28 Refactor

After dispatching 3 parallel subagents to update admin routes, store layers, and
the main app, the app failed to import:

```
ImportError: cannot import name 'list_all_keys' from 'app.store.apikey'
```

**Root cause:** Subagent A rewrote `app/routers/admin/apikey.py` using function
names `list_all_keys`, `update_key`, `delete_key`. Subagent B rewrote
`app/store/apikey.py` exporting `list_api_keys`, `update_api_key`, `delete_api_key`.

Both subagents succeeded independently. Together they broke.

## Fix Steps

```bash
# 1. Identify the mismatch
python -c "from app.main import app"
# ImportError: cannot import name 'list_all_keys'

# 2. Find the stale references
grep -rn "list_all_keys\|update_key\|delete_key" app/routers/admin/apikey.py

# 3. Fix with patch (not full rewrite)
patch(path="app/routers/admin/apikey.py",
      old_string="from app.store.apikey import create_api_key, get_key_by_id, list_all_keys, update_key, delete_key",
      new_string="from app.store.apikey import create_api_key, get_key_by_id, list_api_keys, update_api_key, delete_api_key")

# 4. Fix function calls in the body too
patch(path="app/routers/admin/apikey.py",
      old_string="await list_all_keys(",
      new_string="await list_api_keys(")

# 5. Verify
python -c "from app.main import app; print(f'Routes: {len(app.routes)}')"
pytest tests/ -q

# 6. Commit
git add app/routers/admin/apikey.py && git commit -m "fix: resolve import mismatches in admin routes"
```

## Prevention

When dispatching parallel subagents, include the **current function signatures**
in each subagent's context so they use the right names:

```python
context="""
CURRENT STORE API (app/store/apikey.py):
- create_api_key(user_id, name, rate_limit_rpm, rate_limit_tpm, models, expires_at) -> dict
- get_key_by_hash(key_hash) -> Optional[dict]
- get_key_by_id(key_id) -> Optional[dict]
- list_api_keys(user_id=None) -> list[dict]
- update_api_key(key_id, **kwargs) -> bool
- delete_api_key(key_id) -> bool
- update_last_used(key_id) -> None
"""
```
