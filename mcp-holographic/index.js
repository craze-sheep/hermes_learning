#!/usr/bin/env node
/**
 * MCP Holographic Memory Server
 * 
 * 桥接 Hermes Holographic 记忆系统，让 Claude Code、OpenCode、Codex 都能访问
 * 使用与 Holographic 插件完全兼容的表结构
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import Database from "better-sqlite3";
import { existsSync } from "fs";
import { join } from "path";
import { homedir } from "os";

// 数据库路径（与 Holographic 插件一致）
const DB_PATH = join(homedir(), ".hermes", "memory_store.db");

let db = null;

// 初始化数据库（使用与 Holographic 兼容的表结构）
async function initDb() {
  if (db) return db;

  const isNewDb = !existsSync(DB_PATH);
  db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");

  if (isNewDb) {
    db.exec(`
      CREATE TABLE IF NOT EXISTS facts (
        fact_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        content         TEXT NOT NULL UNIQUE,
        category        TEXT DEFAULT 'general',
        tags            TEXT DEFAULT '',
        trust_score     REAL DEFAULT 0.5,
        retrieval_count INTEGER DEFAULT 0,
        helpful_count   INTEGER DEFAULT 0,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hrr_vector      BLOB
      );

      CREATE TABLE IF NOT EXISTS entities (
        entity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL UNIQUE,
        entity_type TEXT DEFAULT 'unknown',
        aliases     TEXT DEFAULT '',
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS fact_entities (
        fact_id   INTEGER REFERENCES facts(fact_id),
        entity_id INTEGER REFERENCES entities(entity_id),
        PRIMARY KEY (fact_id, entity_id)
      );
    `);
  }

  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_facts_trust ON facts(trust_score DESC);
    CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
    CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
  `);

  return db;
}

function all(database, sql, params = []) {
  return database.prepare(sql).all(params);
}

function get(database, sql, params = []) {
  return database.prepare(sql).get(params);
}

function run(database, sql, params = []) {
  return database.prepare(sql).run(params);
}

// 创建 MCP 服务器
const server = new McpServer({
  name: "holographic-memory",
  version: "1.0.0",
});

const FACT_QUERY_ACTIONS = ["search", "probe", "related", "reason", "contradict", "list"];
const FACT_QUERY_ACTION_SET = new Set(FACT_QUERY_ACTIONS);

const FACT_QUERY_SCHEMA = {
  action: z.enum(FACT_QUERY_ACTIONS),
  query: z.string().optional().describe("Search query (required for 'search')."),
  entity: z.string().optional().describe("Entity name for 'probe'/'related'."),
  entities: z.array(z.string()).optional().describe("Entity names for 'reason'."),
  min_trust: z.number().optional().describe("Minimum trust filter (default: 0.3)."),
  limit: z.number().optional().describe("Max results (default: 10)."),
};

const FACT_STORE_SCHEMA = {
  action: z.enum(["add", "search", "probe", "related", "reason", "contradict", "update", "remove", "list", "dedup", "merge"]),
  content: z.string().optional().describe("Fact content (required for 'add')."),
  query: z.string().optional().describe("Search query (required for legacy 'search'). Use fact_query for read-only queries."),
  entity: z.string().optional().describe("Entity name for legacy 'probe'/'related'. Use fact_query for read-only queries."),
  entities: z.array(z.string()).optional().describe("Entity names for legacy 'reason'. Use fact_query for read-only queries."),
  fact_id: z.number().optional().describe("Fact ID for 'update'/'remove'."),
  primary_id: z.number().optional().describe("Primary fact ID to keep for 'merge'."),
  secondary_id: z.number().optional().describe("Secondary fact ID to merge and remove for 'merge'."),
  category: z.enum(["user_pref", "project", "tool", "general"]).optional(),
  tags: z.string().optional().describe("Comma-separated tags."),
  trust_delta: z.number().optional().describe("Trust adjustment for 'update'."),
  auto_merge: z.boolean().optional().describe("For 'dedup', automatically merge duplicate candidates."),
  min_trust: z.number().optional().describe("Minimum trust filter (default: 0.3)."),
  limit: z.number().optional().describe("Max results (default: 10)."),
};

async function handleFactQuery(params, database = null) {
  const activeDb = database || await initDb();

  try {
    switch (params.action) {
      case "search": {
        if (!params.query) {
          return { content: [{ type: "text", text: "Error: query is required for 'search'" }], isError: true };
        }
        const limit = params.limit || 10;
        const minTrust = params.min_trust || 0.3;

        const rows = all(
          activeDb,
          `SELECT fact_id, content, category, tags, trust_score
           FROM facts
           WHERE content LIKE ? ESCAPE '\\' AND trust_score >= ?
           ORDER BY trust_score DESC
           LIMIT ?`,
          [`%${escapeLike(params.query)}%`, minTrust, limit]
        );

        if (rows.length === 0) {
          return { content: [{ type: "text", text: `No facts found matching "${params.query}"` }] };
        }

        const facts = rows.map(rowToFact);

        return {
          content: [{
            type: "text",
            text: `Found ${facts.length} facts:\n${facts.map(f => `[${f.id}] ${f.content} (trust: ${f.trust.toFixed(2)})`).join("\n")}`
          }]
        };
      }

      case "probe": {
        if (!params.entity) {
          return { content: [{ type: "text", text: "Error: entity is required for 'probe'" }], isError: true };
        }

        const rows = all(
          activeDb,
          `SELECT f.fact_id, f.content, f.category, f.tags, f.trust_score
           FROM facts f
           JOIN fact_entities fe ON f.fact_id = fe.fact_id
           JOIN entities e ON fe.entity_id = e.entity_id
           WHERE e.name LIKE ? ESCAPE '\\'
           ORDER BY f.trust_score DESC`,
          [`%${escapeLike(params.entity)}%`]
        );

        if (rows.length === 0) {
          return { content: [{ type: "text", text: `No facts found about "${params.entity}"` }] };
        }

        const facts = rows.map(rowToFact);

        return {
          content: [{
            type: "text",
            text: `All facts about "${params.entity}":\n${facts.map(f => `[${f.id}] ${f.content} (trust: ${f.trust.toFixed(2)})`).join("\n")}`
          }]
        };
      }

      case "list": {
        const limit = params.limit || 20;
        const minTrust = params.min_trust || 0.3;

        const rows = all(
          activeDb,
          `SELECT fact_id, content, category, tags, trust_score
           FROM facts
           WHERE trust_score >= ?
           ORDER BY updated_at DESC
           LIMIT ?`,
          [minTrust, limit]
        );

        if (rows.length === 0) {
          return { content: [{ type: "text", text: "No facts stored yet." }] };
        }

        const facts = rows.map(rowToFact);

        return {
          content: [{
            type: "text",
            text: `Stored facts (${facts.length}):\n${facts.map(f => `[${f.id}] ${f.content} (trust: ${f.trust.toFixed(2)})`).join("\n")}`
          }]
        };
      }

      case "related": {
        if (!params.entity) {
          return { content: [{ type: "text", text: "Error: entity is required for 'related'" }], isError: true };
        }

        const rows = all(
          activeDb,
          `SELECT DISTINCT e2.name
           FROM entities e1
           JOIN fact_entities fe1 ON e1.entity_id = fe1.entity_id
           JOIN fact_entities fe2 ON fe1.fact_id = fe2.fact_id
           JOIN entities e2 ON fe2.entity_id = e2.entity_id
           WHERE e1.name LIKE ? ESCAPE '\\' AND e2.name != e1.name
           LIMIT 20`,
          [`%${escapeLike(params.entity)}%`]
        );

        if (rows.length === 0) {
          return { content: [{ type: "text", text: `No related entities found for "${params.entity}"` }] };
        }

        const related = [...new Set(rows.map(row => row.name))];

        return {
          content: [{
            type: "text",
            text: `Entities related to "${params.entity}":\n${related.join(", ")}`
          }]
        };
      }

      case "reason": {
        if (!params.entities || params.entities.length < 2) {
          return { content: [{ type: "text", text: "Error: at least 2 entities required for 'reason'" }], isError: true };
        }

        const conditions = params.entities.map(() => "e.name LIKE ? ESCAPE '\\'").join(" OR ");
        const values = params.entities.map(e => `%${escapeLike(e)}%`);

        const rows = all(
          activeDb,
          `SELECT f.fact_id, f.content, f.trust_score
           FROM facts f
           JOIN fact_entities fe ON f.fact_id = fe.fact_id
           JOIN entities e ON fe.entity_id = e.entity_id
           WHERE ${conditions}
           GROUP BY f.fact_id
           HAVING COUNT(DISTINCT e.name) >= 2
           ORDER BY f.trust_score DESC
           LIMIT 10`,
          values
        );

        if (rows.length === 0) {
          return { content: [{ type: "text", text: `No facts connecting ${params.entities.join(" and ")}` }] };
        }

        const facts = rows.map(row => ({
          id: row.fact_id,
          content: row.content,
          trust: row.trust_score
        }));

        return {
          content: [{
            type: "text",
            text: `Facts connecting ${params.entities.join(", ")}:\n${facts.map(f => `[${f.id}] ${f.content} (trust: ${f.trust.toFixed(2)})`).join("\n")}`
          }]
        };
      }

      case "contradict": {
        const rows = all(
          activeDb,
          `SELECT fact_id, content, trust_score, retrieval_count, helpful_count
           FROM facts
           WHERE trust_score < 0.5
           ORDER BY trust_score ASC
           LIMIT 10`
        );

        const similarPairs = all(
          activeDb,
          `SELECT f1.fact_id AS id1, f1.content AS content1, f1.trust_score AS trust1,
                  f2.fact_id AS id2, f2.content AS content2, f2.trust_score AS trust2
           FROM fact_entities fe1
           JOIN fact_entities fe2 ON fe1.entity_id = fe2.entity_id AND fe1.fact_id < fe2.fact_id
           JOIN facts f1 ON fe1.fact_id = f1.fact_id
           JOIN facts f2 ON fe2.fact_id = f2.fact_id
           WHERE ABS(f1.trust_score - f2.trust_score) > 0.3
           GROUP BY f1.fact_id, f2.fact_id
           LIMIT 10`
        );

        let output = '';

        if (rows.length > 0) {
          const facts = rows.map(row => ({
            id: row.fact_id,
            content: row.content,
            trust: row.trust_score,
            retrieval_count: row.retrieval_count,
            helpful_count: row.helpful_count
          }));

          output += `Low-trust facts (may be outdated or inaccurate):\n${facts.map(f => `[${f.id}] ${f.content} (trust: ${f.trust.toFixed(2)}, retrieved: ${f.retrieval_count}, helpful: ${f.helpful_count})`).join("\n")}`;
        }

        if (similarPairs.length > 0) {
          output += '\n\nPotential contradictions (shared entity, different trust):\n';
          similarPairs.forEach(row => {
            output += `[${row.id1}] "${row.content1}" (trust: ${row.trust1.toFixed(2)}) vs [${row.id2}] "${row.content2}" (trust: ${row.trust2.toFixed(2)})\n`;
          });
        }

        if (!output) {
          return { content: [{ type: "text", text: "No contradictions found." }] };
        }

        return {
          content: [{
            type: "text",
            text: output
          }]
        };
      }

      default:
        return { content: [{ type: "text", text: `Unknown query action: ${params.action}` }], isError: true };
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true
    };
  }
}

// fact_query 工具（只读）
server.tool(
  "fact_query",
  "Read-only holographic memory queries. Use this for search/probe/related/reason/contradict/list operations; it never updates retrieval counters or persists database changes.",
  FACT_QUERY_SCHEMA,
  {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
  async (params) => {
    return handleFactQuery(params);
  }
);

// fact_store 工具
server.tool(
  "fact_store",
  "Deep structured memory writer. Prefer fact_query for read-only search/probe/related/reason/contradict/list operations. fact_store keeps legacy query actions for compatibility, but they are handled read-only and no longer update retrieval counters.\n\nWRITE ACTIONS:\n• add — Store a fact the user would expect you to remember.\n• update — Update content/category/tags/trust for a fact.\n• remove — Delete a fact.\n\nLEGACY READ ACTIONS:\n• search/probe/related/reason/contradict/list — supported for older clients; use fact_query instead.",
  FACT_STORE_SCHEMA,
  {
    readOnlyHint: false,
    destructiveHint: true,
    idempotentHint: false,
    openWorldHint: false,
  },
  async (params) => {
    const database = await initDb();
    
    try {
      if (FACT_QUERY_ACTION_SET.has(params.action)) {
        return handleFactQuery(params, database);
      }

      switch (params.action) {
        case "add": {
          if (!params.content) {
            return { content: [{ type: "text", text: "Error: content is required for 'add'" }], isError: true };
          }
          
          const existing = get(
            database,
            "SELECT fact_id FROM facts WHERE content = ?",
            [params.content]
          );
          
          if (existing) {
            return { content: [{ type: "text", text: `⚠️ Fact already exists with ID ${existing.fact_id}` }] };
          }

          const category = params.category || "general";
          const similarFact = findBestSimilarFact(database, params.content, category);
          if (similarFact && similarFact.similarity >= 0.6 && similarFact.trust > 0.3) {
            const oldContent = similarFact.content;
            const mergedTags = mergeTags(similarFact.tags, params.tags || "");

            run(
              database,
              `UPDATE facts SET
                 content = ?,
                 tags = ?,
                 trust_score = MIN(1, trust_score + 0.05),
                 updated_at = CURRENT_TIMESTAMP
               WHERE fact_id = ?`,
              [params.content, mergedTags, similarFact.id]
            );

            const entities = linkExtractedEntities(database, similarFact.id, params.content);
            return {
              content: [{
                type: "text",
                text: `✅ Merged into existing fact #${similarFact.id}: "${oldContent}" → "${params.content}"\n   Similarity: ${similarFact.similarity.toFixed(2)}\n   Entities: ${entities.length > 0 ? entities.join(", ") : "(none)"}`
              }]
            };
          }
          
          const insertInfo = run(
            database,
            "INSERT INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)",
            [params.content, category, params.tags || "", 0.5]
          );
          const newId = Number(insertInfo.lastInsertRowid);
          
          // 自动提取实体并关联
          const entities = linkExtractedEntities(database, newId, params.content);
          
          const similarHint = similarFact && similarFact.similarity >= 0.4
            ? `\n⚠️ Similar to #${similarFact.id} ("${similarFact.content}"), similarity=${similarFact.similarity.toFixed(2)}`
            : "";
          return {
            content: [{
              type: "text",
              text: `✅ Fact added with ID ${newId}: "${params.content}"\n   Entities: ${entities.length > 0 ? entities.join(", ") : "(none)"}${similarHint}`
            }]
          };
        }
        
        case "update": {
          if (!params.fact_id) {
            return { content: [{ type: "text", text: "Error: fact_id is required for 'update'" }], isError: true };
          }
          
          // 验证 fact_id 是否存在
          const updateCheck = get(database, "SELECT fact_id FROM facts WHERE fact_id = ?", [params.fact_id]);
          if (!updateCheck) {
            return { content: [{ type: "text", text: `Error: Fact ${params.fact_id} not found` }], isError: true };
          }
          
          // 构建动态 UPDATE 语句
          const updates = [];
          const values = [];
          
          if (params.content) {
            updates.push("content = ?");
            values.push(params.content);
          }
          if (params.category) {
            updates.push("category = ?");
            values.push(params.category);
          }
          if (params.tags) {
            updates.push("tags = ?");
            values.push(params.tags);
          }
          if (params.trust_delta) {
            updates.push("trust_score = MAX(0, MIN(1, trust_score + ?))");
            values.push(params.trust_delta);
          }
          
          if (updates.length === 0) {
            return { content: [{ type: "text", text: "No fields to update" }] };
          }
          
          updates.push("updated_at = CURRENT_TIMESTAMP");
          values.push(params.fact_id);
          
          run(
            database,
            `UPDATE facts SET ${updates.join(", ")} WHERE fact_id = ?`,
            values
          );
          
          return {
            content: [{
              type: "text",
              text: `✅ Fact ${params.fact_id} updated`
            }]
          };
        }
        
        case "remove": {
          if (!params.fact_id) {
            return { content: [{ type: "text", text: "Error: fact_id is required for 'remove'" }], isError: true };
          }
          
          // 验证 fact_id 是否存在
          const removeCheck = get(database, "SELECT fact_id FROM facts WHERE fact_id = ?", [params.fact_id]);
          if (!removeCheck) {
            return { content: [{ type: "text", text: `Error: Fact ${params.fact_id} not found` }], isError: true };
          }
          
          run(database, "DELETE FROM fact_entities WHERE fact_id = ?", [params.fact_id]);

          run(database, "DELETE FROM facts WHERE fact_id = ?", [params.fact_id]);
          
          // 清理孤立实体（没有关联任何 fact 的实体）
          run(
            database,
            "DELETE FROM entities WHERE entity_id NOT IN (SELECT DISTINCT entity_id FROM fact_entities)"
          );
          
          return {
            content: [{
              type: "text",
              text: `✅ Fact ${params.fact_id} removed`
            }]
          };
        }

        case "dedup": {
          if (params.auto_merge) {
            const merged = [];
            let guard = 0;

            while (guard++ < 100) {
              const candidates = findPotentialDuplicates(database, 0.6);
              if (candidates.length === 0) break;

              const best = candidates[0];
              const primaryId = best.factA.trust >= best.factB.trust ? best.factA.id : best.factB.id;
              const secondaryId = primaryId === best.factA.id ? best.factB.id : best.factA.id;
              const result = mergeFacts(database, primaryId, secondaryId);
              merged.push(`#${secondaryId} → #${primaryId} (similarity: ${best.similarity.toFixed(2)}) "${result.secondaryContent}" → "${result.primaryContent}"`);
            }

            if (merged.length === 0) {
              return { content: [{ type: "text", text: "No duplicate candidates found." }] };
            }

            return {
              content: [{
                type: "text",
                text: `✅ Auto-merged ${merged.length} duplicate pair(s):\n${merged.map(m => `- ${m}`).join("\n")}`
              }]
            };
          }

          const candidates = findPotentialDuplicates(database, 0.6);
          if (candidates.length === 0) {
            return { content: [{ type: "text", text: "No duplicate candidates found." }] };
          }

          const limit = params.limit || 20;
          const lines = candidates.slice(0, limit).map(pair =>
            `- #${pair.factA.id} ↔ #${pair.factB.id} (similarity: ${pair.similarity.toFixed(2)}) "${pair.factA.content}" ↔ "${pair.factB.content}"`
          );

          return {
            content: [{
              type: "text",
              text: `Found ${candidates.length} potential duplicate(s):\n${lines.join("\n")}\nMerge candidates listed above. Use fact_store merge action to merge.`
            }]
          };
        }

        case "merge": {
          if (!params.primary_id || !params.secondary_id) {
            return { content: [{ type: "text", text: "Error: primary_id and secondary_id are required for 'merge'" }], isError: true };
          }

          const result = mergeFacts(database, params.primary_id, params.secondary_id);
          return {
            content: [{
              type: "text",
              text: `✅ Merged #${params.secondary_id} into #${params.primary_id}\n   Content: "${result.primaryContent}"\n   Tags: ${result.tags || "(none)"}\n   Trust: ${result.trust.toFixed(2)}`
            }]
          };
        }
        
        default:
          return { content: [{ type: "text", text: `Unknown action: ${params.action}` }], isError: true };
      }
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true
      };
    }
  }
);

// fact_feedback 工具
server.tool(
  "fact_feedback",
  "Rate a fact after using it. Mark 'helpful' if accurate, 'unhelpful' if outdated. This trains the memory — good facts rise, bad facts sink.",
  {
    action: z.enum(["helpful", "unhelpful"]),
    fact_id: z.number().describe("The fact ID to rate."),
  },
  {
    readOnlyHint: false,
    destructiveHint: true,
    idempotentHint: false,
    openWorldHint: false,
  },
  async (params) => {
    const database = await initDb();
    
    try {
      // 验证 fact_id 是否存在
      const feedbackCheck = get(database, "SELECT fact_id FROM facts WHERE fact_id = ?", [params.fact_id]);
      if (!feedbackCheck) {
        return { content: [{ type: "text", text: `Error: Fact ${params.fact_id} not found` }], isError: true };
      }
      
      const delta = params.action === "helpful" ? 0.1 : -0.1;
      
      run(
        database,
        `UPDATE facts SET 
          trust_score = MAX(0, MIN(1, trust_score + ?)),
          helpful_count = helpful_count + ?,
          updated_at = CURRENT_TIMESTAMP
         WHERE fact_id = ?`,
        [delta, params.action === "helpful" ? 1 : 0, params.fact_id]
      );
      
      // 获取更新后的信任分数
      const result = get(database, "SELECT trust_score FROM facts WHERE fact_id = ?", [params.fact_id]);
      const newTrust = result?.trust_score || 0;
      
      return {
        content: [{
          type: "text",
          text: `✅ Fact ${params.fact_id} rated as ${params.action}. New trust: ${newTrust.toFixed(2)}`
        }]
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true
      };
    }
  }
);

// 辅助函数：转义 LIKE 通配符
function escapeLike(str) {
  return str.replace(/\\/g, '\\\\').replace(/%/g, '\\%').replace(/_/g, '\\_');
}

function tokenizeForSimilarity(text) {
  return (text || "")
    .toLowerCase()
    .match(/\w+|[\u4e00-\u9fff]/g) || [];
}

function computeSimilarity(textA, textB) {
  const tokensA = new Set(tokenizeForSimilarity(textA));
  const tokensB = new Set(tokenizeForSimilarity(textB));
  if (tokensA.size === 0 && tokensB.size === 0) return 1;
  if (tokensA.size === 0 || tokensB.size === 0) return 0;

  let intersection = 0;
  for (const token of tokensA) {
    if (tokensB.has(token)) intersection++;
  }

  const union = tokensA.size + tokensB.size - intersection;
  return union === 0 ? 0 : intersection / union;
}

function computeFactSimilarity(factA, factB) {
  const base = computeSimilarity(factA.content, factB.content);
  const categoryBonus = factA.category && factA.category === factB.category ? 0.1 : 0;
  return Math.min(1, base + categoryBonus);
}

function mergeTags(...tagStrings) {
  const merged = [];
  const seen = new Set();

  for (const tagString of tagStrings) {
    for (const rawTag of (tagString || "").split(",")) {
      const tag = rawTag.trim();
      if (!tag) continue;

      const key = tag.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      merged.push(tag);
    }
  }

  return merged.join(",");
}

function rowToFact(row) {
  return {
    id: row.fact_id,
    content: row.content,
    category: row.category,
    tags: row.tags,
    trust: row.trust_score,
    retrievalCount: row.retrieval_count || 0,
    helpfulCount: row.helpful_count || 0,
  };
}

function rowsToFacts(rows) {
  return rows.map(rowToFact);
}

function getAllFacts(database) {
  return rowsToFacts(all(
    database,
    `SELECT fact_id, content, category, tags, trust_score, retrieval_count, helpful_count
     FROM facts
     ORDER BY fact_id`
  ));
}

function getFactById(database, factId) {
  const row = get(
    database,
    `SELECT fact_id, content, category, tags, trust_score, retrieval_count, helpful_count
     FROM facts
     WHERE fact_id = ?`,
    [factId]
  );
  return row ? rowToFact(row) : null;
}

function contentExistsForOtherFact(database, content, factIdA, factIdB = null) {
  const result = get(
    database,
    `SELECT fact_id FROM facts
     WHERE content = ? AND fact_id != ? AND (? IS NULL OR fact_id != ?)
     LIMIT 1`,
    [content, factIdA, factIdB, factIdB]
  );
  return Boolean(result);
}

function findBestSimilarFact(database, content, category) {
  const facts = rowsToFacts(all(
    database,
    `SELECT fact_id, content, category, tags, trust_score, retrieval_count, helpful_count
     FROM facts
     WHERE category = ?`,
    [category]
  ));

  let best = null;
  for (const fact of facts) {
    const similarity = computeFactSimilarity(
      { content, category },
      { content: fact.content, category: fact.category }
    );

    if (!best || similarity > best.similarity) {
      best = { ...fact, similarity };
    }
  }

  return best;
}

function linkExtractedEntities(database, factId, content) {
  const entities = extractEntities(content);
  for (const entityName of entities) {
    run(
      database,
      "INSERT OR IGNORE INTO entities (name) VALUES (?)",
      [entityName]
    );

    const entity = get(
      database,
      "SELECT entity_id FROM entities WHERE name = ?",
      [entityName]
    );
    const entityId = entity?.entity_id;

    if (entityId) {
      run(
        database,
        "INSERT OR IGNORE INTO fact_entities (fact_id, entity_id) VALUES (?, ?)",
        [factId, entityId]
      );
    }
  }

  return entities;
}

function findPotentialDuplicates(database, threshold = 0.6) {
  const facts = getAllFacts(database);
  const candidates = [];

  for (let i = 0; i < facts.length; i++) {
    for (let j = i + 1; j < facts.length; j++) {
      const factA = facts[i];
      const factB = facts[j];
      const similarity = computeFactSimilarity(factA, factB);
      if (similarity >= threshold) {
        candidates.push({ factA, factB, similarity });
      }
    }
  }

  candidates.sort((a, b) => b.similarity - a.similarity);
  return candidates;
}

function mergeFacts(database, primaryId, secondaryId) {
  if (primaryId === secondaryId) {
    throw new Error("primary_id and secondary_id must be different");
  }

  const primary = getFactById(database, primaryId);
  const secondary = getFactById(database, secondaryId);
  if (!primary) throw new Error(`Fact ${primaryId} not found`);
  if (!secondary) throw new Error(`Fact ${secondaryId} not found`);

  let mergedContent = primary.content.length >= secondary.content.length ? primary.content : secondary.content;
  if (contentExistsForOtherFact(database, mergedContent, primaryId, secondaryId)) {
    mergedContent = primary.content;
  }

  const mergedTags = mergeTags(primary.tags, secondary.tags);
  const mergedTrust = Math.max(primary.trust, secondary.trust);
  const mergedRetrievalCount = primary.retrievalCount + secondary.retrievalCount;
  const mergedHelpfulCount = primary.helpfulCount + secondary.helpfulCount;

  const tx = database.transaction(() => {
    run(
      database,
      `INSERT OR IGNORE INTO fact_entities (fact_id, entity_id)
       SELECT ?, entity_id FROM fact_entities WHERE fact_id = ?`,
      [primaryId, secondaryId]
    );
    run(database, "DELETE FROM fact_entities WHERE fact_id = ?", [secondaryId]);
    run(database, "DELETE FROM facts WHERE fact_id = ?", [secondaryId]);
    run(
      database,
      `UPDATE facts SET
         content = ?,
         tags = ?,
         trust_score = ?,
         retrieval_count = ?,
         helpful_count = ?,
         updated_at = CURRENT_TIMESTAMP
       WHERE fact_id = ?`,
      [mergedContent, mergedTags, mergedTrust, mergedRetrievalCount, mergedHelpfulCount, primaryId]
    );
    linkExtractedEntities(database, primaryId, mergedContent);
    run(
      database,
      "DELETE FROM entities WHERE entity_id NOT IN (SELECT DISTINCT entity_id FROM fact_entities)"
    );
  });
  tx();

  return {
    primaryContent: mergedContent,
    secondaryContent: secondary.content,
    tags: mergedTags,
    trust: mergedTrust,
  };
}

// 辅助函数：从文本中提取实体
function extractEntities(text) {
  const entities = [];
  
  // 提取引号中的内容
  const quoted = text.match(/["「」『』「」]([^"「」『』「」]+)["「」『』「」]/g);
  if (quoted) {
    entities.push(...quoted.map(q => q.slice(1, -1)));
  }
  
  // 提取大写开头的词（可能是专有名词）
  const capitalized = text.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g);
  if (capitalized) {
    // 过滤掉常见英文停用词
    const englishStopWords = ['The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'How', 'What', 'Which', 'Who', 'Whom', 'Why', 'A', 'An', 'And', 'But', 'Or', 'For', 'Nor', 'So', 'Yet', 'Both', 'Either', 'Neither', 'Each', 'Every', 'All', 'Any', 'Few', 'More', 'Most', 'Other', 'Some', 'Such', 'No', 'Not', 'Only', 'Own', 'Same', 'Than', 'Too', 'Very', 'Just', 'Because', 'As', 'Until', 'While', 'Of', 'At', 'By', 'For', 'With', 'About', 'Against', 'Between', 'Through', 'During', 'Before', 'After', 'Above', 'Below', 'To', 'From', 'Up', 'Down', 'In', 'Out', 'On', 'Off', 'Over', 'Under', 'Again', 'Further', 'Then', 'Once'];
    entities.push(...capitalized.filter(w => !englishStopWords.includes(w)));
  }
  
  // 提取中文专有名词（保守策略，减少噪音）
  // 不再盲目提取所有中文词，只提取明确的实体模式
  // 1. 提取"XX系统"/"XX项目"/"XX工具"等明确实体
  const cnEntities = text.match(/[\u4e00-\u9fa5]{2,6}(?:系统|项目|工具|平台|服务|框架|库|数据库|服务器|配置|脚本|插件|扩展|模块|组件|接口|协议|语言|引擎|编辑器|浏览器|操作系统)/g);
  if (cnEntities) {
    entities.push(...cnEntities);
  }
  // 2. 提取中文中夹带英文专有名词的组合（如 "Holographic记忆系统"）
  const mixedEntities = text.match(/[\u4e00-\u9fa5]*[A-Z][a-zA-Z]+[\u4e00-\u9fa5]*/g);
  if (mixedEntities) {
    entities.push(...mixedEntities.filter(w => w.length >= 3));
  }
  
  return [...new Set(entities)]; // 去重
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.error("Received SIGINT, closing database...");
  db?.close();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.error("Received SIGTERM, closing database...");
  db?.close();
  process.exit(0);
});

process.on('uncaughtException', (err) => {
  console.error("Uncaught exception:", err);
  db?.close();
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error("Unhandled rejection:", reason);
  db?.close();
  process.exit(1);
});

// 启动服务器
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Holographic Memory MCP Server running on stdio");
}

main().catch(console.error);
