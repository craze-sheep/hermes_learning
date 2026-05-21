# Holographic Memory MCP Bridge

Reference implementation: `~/.hermes/mcp-holographic/index.js`

## Purpose
Bridges Hermes Holographic memory (SQLite-based knowledge graph) to Claude Code, OpenCode, Codex via MCP protocol. All tools share one database.

## Database Schema (compatible with Holographic plugin)

```sql
CREATE TABLE facts (
  fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
  content TEXT NOT NULL UNIQUE,
  category TEXT DEFAULT 'general',
  tags TEXT DEFAULT '',
  trust_score REAL DEFAULT 0.5,
  retrieval_count INTEGER DEFAULT 0,
  helpful_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  hrr_vector BLOB
);

CREATE TABLE entities (
  entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,  -- MUST be UNIQUE for INSERT OR IGNORE
  entity_type TEXT DEFAULT 'unknown',
  aliases TEXT DEFAULT '',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fact_entities (
  fact_id INTEGER REFERENCES facts(fact_id),
  entity_id INTEGER REFERENCES entities(entity_id),
  PRIMARY KEY (fact_id, entity_id)
);

CREATE INDEX idx_facts_trust ON facts(trust_score DESC);
CREATE INDEX idx_facts_category ON facts(category);
CREATE INDEX idx_entities_name ON entities(name);
```

## Tools Exposed

1. `fact_store` — 9 actions: add, search, probe, related, reason, contradict, update, remove, list
2. `fact_feedback` — Rate facts as helpful/unhelpful (adjusts trust_score)

## Key Design Decisions

- **No FTS5** — sql.js doesn't support it; use LIKE with ESCAPE clause
- **Entity auto-extraction** — Extracts entities from fact content on add
- **Orphan cleanup** — DELETE entities with no remaining facts after remove
- **Retrieval tracking** — Increments retrieval_count on search, probe, related, reason, contradict
- **Trust system** — Default 0.5, +0.1 for helpful, -0.1 for unhelpful

## Bugs Found & Fixed During Development

1. `fact_feedback` missing `saveDb()` — feedback data was lost
2. `entities.name` missing UNIQUE — INSERT OR IGNORE didn't work
3. `update`/`remove`/`feedback` not checking fact_id existence
4. `contradict` misleading name — renamed semantic to "low trust facts"
5. Missing graceful shutdown handlers
6. LIKE queries missing ESCAPE clause
7. `retrieval_count` only updated on search/probe, not related/reason/contradict
