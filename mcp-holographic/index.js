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
import initSqlJs from "sql.js";
import { readFileSync, writeFileSync, existsSync, renameSync } from "fs";
import { join } from "path";
import { homedir } from "os";

// 数据库路径（与 Holographic 插件一致）
const DB_PATH = join(homedir(), ".hermes", "memory_store.db");

let db = null;

// 初始化数据库（使用与 Holographic 兼容的表结构）
async function initDb() {
  if (db) return db;
  
  const SQL = await initSqlJs();
  
  if (existsSync(DB_PATH)) {
    const buffer = readFileSync(DB_PATH);
    db = new SQL.Database(buffer);
  } else {
    // 创建新数据库（与 Holographic 表结构完全一致）
    db = new SQL.Database();
    
    // facts 表
    db.run(`
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
      )
    `);
    
    // entities 表
    db.run(`
      CREATE TABLE IF NOT EXISTS entities (
        entity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL UNIQUE,
        entity_type TEXT DEFAULT 'unknown',
        aliases     TEXT DEFAULT '',
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // fact_entities 关联表
    db.run(`
      CREATE TABLE IF NOT EXISTS fact_entities (
        fact_id   INTEGER REFERENCES facts(fact_id),
        entity_id INTEGER REFERENCES entities(entity_id),
        PRIMARY KEY (fact_id, entity_id)
      )
    `);
    
    // 索引
    db.run(`CREATE INDEX IF NOT EXISTS idx_facts_trust ON facts(trust_score DESC)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)`);
    db.run(`CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)`);
  }
  
  return db;
}

// 保存数据库到文件（原子写入），失败时抛出异常供调用方处理
function saveDb() {
  if (!db) return;
  try {
    const data = db.export();
    const buffer = Buffer.from(data);
    const tmpPath = DB_PATH + '.tmp';
    writeFileSync(tmpPath, buffer);
    // 原子替换：rename 是原子操作
    renameSync(tmpPath, DB_PATH);
  } catch (err) {
    throw new Error(`Persistence failed (memory updated but not saved to disk): ${err.message}`);
  }
}


// 创建 MCP 服务器
const server = new McpServer({
  name: "holographic-memory",
  version: "1.0.0",
});

// fact_store 工具
server.tool(
  "fact_store",
  "Deep structured memory with algebraic reasoning. Use alongside the memory tool — memory for always-on context, fact_store for deep recall and compositional queries.\n\nACTIONS (simple → powerful):\n• add — Store a fact the user would expect you to remember.\n• search — Keyword lookup ('editor config', 'deploy process').\n• probe — Entity recall: ALL facts about a person/thing.\n• related — What connects to an entity? Structural adjacency.\n• reason — Compositional: facts connected to MULTIPLE entities simultaneously.\n• contradict — Memory hygiene: find facts making conflicting claims.\n• update/remove/list — CRUD operations.\n\nIMPORTANT: Before answering questions about the user, ALWAYS probe or reason first.",
  {
    action: z.enum(["add", "search", "probe", "related", "reason", "contradict", "update", "remove", "list"]),
    content: z.string().optional().describe("Fact content (required for 'add')."),
    query: z.string().optional().describe("Search query (required for 'search')."),
    entity: z.string().optional().describe("Entity name for 'probe'/'related'."),
    entities: z.array(z.string()).optional().describe("Entity names for 'reason'."),
    fact_id: z.number().optional().describe("Fact ID for 'update'/'remove'."),
    category: z.enum(["user_pref", "project", "tool", "general"]).optional(),
    tags: z.string().optional().describe("Comma-separated tags."),
    trust_delta: z.number().optional().describe("Trust adjustment for 'update'."),
    min_trust: z.number().optional().describe("Minimum trust filter (default: 0.3)."),
    limit: z.number().optional().describe("Max results (default: 10)."),
  },
  async (params) => {
    const database = await initDb();
    
    try {
      switch (params.action) {
        case "add": {
          if (!params.content) {
            return { content: [{ type: "text", text: "Error: content is required for 'add'" }], isError: true };
          }
          
          // 检查是否已存在
          const existing = database.exec(
            "SELECT fact_id FROM facts WHERE content = ?",
            [params.content]
          );
          
          if (existing.length > 0 && existing[0].values.length > 0) {
            return { content: [{ type: "text", text: `⚠️ Fact already exists with ID ${existing[0].values[0][0]}` }] };
          }
          
          database.run(
            "INSERT INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)",
            [params.content, params.category || "general", params.tags || "", 0.5]
          );
          
          // 获取新插入的 ID
          const idResult = database.exec("SELECT last_insert_rowid() as id");
          const newId = idResult[0]?.values[0][0];
          
          // 自动提取实体并关联
          const entities = extractEntities(params.content);
          for (const entityName of entities) {
            // 创建实体（如果不存在）
            database.run(
              "INSERT OR IGNORE INTO entities (name) VALUES (?)",
              [entityName]
            );
            
            // 获取实体 ID
            const entityResult = database.exec(
              "SELECT entity_id FROM entities WHERE name = ?",
              [entityName]
            );
            const entityId = entityResult[0]?.values[0][0];
            
            // 关联事实和实体
            if (entityId) {
              database.run(
                "INSERT OR IGNORE INTO fact_entities (fact_id, entity_id) VALUES (?, ?)",
                [newId, entityId]
              );
            }
          }
          

          
          saveDb();
          return {
            content: [{
              type: "text",
              text: `✅ Fact added with ID ${newId}: "${params.content}"\n   Entities: ${entities.length > 0 ? entities.join(", ") : "(none)"}`
            }]
          };
        }
        
        case "search": {
          if (!params.query) {
            return { content: [{ type: "text", text: "Error: query is required for 'search'" }], isError: true };
          }
          const limit = params.limit || 10;
          const minTrust = params.min_trust || 0.3;
          
          // 使用 LIKE 搜索（sql.js 不支持 FTS5）
          const results = database.exec(
            `SELECT fact_id, content, category, tags, trust_score
             FROM facts
             WHERE content LIKE ? ESCAPE '\\' AND trust_score >= ?
             ORDER BY trust_score DESC
             LIMIT ?`,
            [`%${escapeLike(params.query)}%`, minTrust, limit]
          );
          
          if (results.length === 0 || results[0].values.length === 0) {
            return { content: [{ type: "text", text: `No facts found matching "${params.query}"` }] };
          }
          
          const facts = results[0].values.map(row => ({
            id: row[0],
            content: row[1],
            category: row[2],
            tags: row[3],
            trust: row[4]
          }));
          
          // 更新 retrieval_count
          for (const fact of facts) {
            database.run(
              "UPDATE facts SET retrieval_count = retrieval_count + 1 WHERE fact_id = ?",
              [fact.id]
            );
          }
          saveDb();
          
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
          
          const results = database.exec(
            `SELECT f.fact_id, f.content, f.category, f.tags, f.trust_score
             FROM facts f
             JOIN fact_entities fe ON f.fact_id = fe.fact_id
             JOIN entities e ON fe.entity_id = e.entity_id
             WHERE e.name LIKE ? ESCAPE '\\'
             ORDER BY f.trust_score DESC`,
            [`%${escapeLike(params.entity)}%`]
          );
          
          if (results.length === 0 || results[0].values.length === 0) {
            return { content: [{ type: "text", text: `No facts found about "${params.entity}"` }] };
          }
          
          const facts = results[0].values.map(row => ({
            id: row[0],
            content: row[1],
            category: row[2],
            tags: row[3],
            trust: row[4]
          }));
          
          // 更新 retrieval_count
          for (const fact of facts) {
            database.run(
              "UPDATE facts SET retrieval_count = retrieval_count + 1 WHERE fact_id = ?",
              [fact.id]
            );
          }
          saveDb();
          
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
          
          const results = database.exec(
            `SELECT fact_id, content, category, tags, trust_score
             FROM facts
             WHERE trust_score >= ?
             ORDER BY updated_at DESC
             LIMIT ?`,
            [minTrust, limit]
          );
          
          if (results.length === 0 || results[0].values.length === 0) {
            return { content: [{ type: "text", text: "No facts stored yet." }] };
          }
          
          const facts = results[0].values.map(row => ({
            id: row[0],
            content: row[1],
            category: row[2],
            tags: row[3],
            trust: row[4]
          }));
          
          return {
            content: [{
              type: "text",
              text: `Stored facts (${facts.length}):\n${facts.map(f => `[${f.id}] ${f.content} (trust: ${f.trust.toFixed(2)})`).join("\n")}`
            }]
          };
        }
        
        case "update": {
          if (!params.fact_id) {
            return { content: [{ type: "text", text: "Error: fact_id is required for 'update'" }], isError: true };
          }
          
          // 验证 fact_id 是否存在
          const updateCheck = database.exec("SELECT fact_id FROM facts WHERE fact_id = ?", [params.fact_id]);
          if (updateCheck.length === 0 || updateCheck[0].values.length === 0) {
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
          
          database.run(
            `UPDATE facts SET ${updates.join(", ")} WHERE fact_id = ?`,
            values
          );
          
          saveDb();
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
          const removeCheck = database.exec("SELECT fact_id FROM facts WHERE fact_id = ?", [params.fact_id]);
          if (removeCheck.length === 0 || removeCheck[0].values.length === 0) {
            return { content: [{ type: "text", text: `Error: Fact ${params.fact_id} not found` }], isError: true };
          }
          
          database.run("DELETE FROM fact_entities WHERE fact_id = ?", [params.fact_id]);

          database.run("DELETE FROM facts WHERE fact_id = ?", [params.fact_id]);
          
          // 清理孤立实体（没有关联任何 fact 的实体）
          database.run(
            "DELETE FROM entities WHERE entity_id NOT IN (SELECT DISTINCT entity_id FROM fact_entities)"
          );
          
          saveDb();
          return {
            content: [{
              type: "text",
              text: `✅ Fact ${params.fact_id} removed`
            }]
          };
        }
        
        case "related": {
          if (!params.entity) {
            return { content: [{ type: "text", text: "Error: entity is required for 'related'" }], isError: true };
          }
          
          // 查找与实体相关的其他实体
          const results = database.exec(
            `SELECT DISTINCT e2.name, fe1.fact_id
             FROM entities e1
             JOIN fact_entities fe1 ON e1.entity_id = fe1.entity_id
             JOIN fact_entities fe2 ON fe1.fact_id = fe2.fact_id
             JOIN entities e2 ON fe2.entity_id = e2.entity_id
             WHERE e1.name LIKE ? ESCAPE '\\' AND e2.name != e1.name
             LIMIT 20`,
            [`%${escapeLike(params.entity)}%`]
          );
          
          if (results.length === 0 || results[0].values.length === 0) {
            return { content: [{ type: "text", text: `No related entities found for "${params.entity}"` }] };
          }
          
          const related = [...new Set(results[0].values.map(row => row[0]))];
          const factIds = [...new Set(results[0].values.map(row => row[1]))];
          
          // 更新 retrieval_count
          for (const fid of factIds) {
            database.run(
              "UPDATE facts SET retrieval_count = retrieval_count + 1 WHERE fact_id = ?",
              [fid]
            );
          }
          saveDb();
          
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
          
          // 查找连接多个实体的事实（使用 LIKE 模糊匹配）
          const conditions = params.entities.map(() => "e.name LIKE ? ESCAPE '\\'").join(" OR ");
          const values = params.entities.map(e => `%${escapeLike(e)}%`);
          
          const results = database.exec(
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
          
          if (results.length === 0 || results[0].values.length === 0) {
            return { content: [{ type: "text", text: `No facts connecting ${params.entities.join(" and ")}` }] };
          }
          
          const facts = results[0].values.map(row => ({
            id: row[0],
            content: row[1],
            trust: row[2]
          }));
          
          // 更新 retrieval_count
          for (const fact of facts) {
            database.run(
              "UPDATE facts SET retrieval_count = retrieval_count + 1 WHERE fact_id = ?",
              [fact.id]
            );
          }
          saveDb();
          
          return {
            content: [{
              type: "text",
              text: `Facts connecting ${params.entities.join(", ")}:\n${facts.map(f => `[${f.id}] ${f.content} (trust: ${f.trust.toFixed(2)})`).join("\n")}`
            }]
          };
        }
        
        case "contradict": {
          // 查找可能矛盾的事实：
          // 1. 低信任度的事实
          // 2. 共享实体但信任度差异大的事实对
          const results = database.exec(
            `SELECT fact_id, content, trust_score, retrieval_count, helpful_count
             FROM facts
             WHERE trust_score < 0.5
             ORDER BY trust_score ASC
             LIMIT 10`
          );
          
          // 查找共享实体但信任度差异大的事实对
          const similarPairs = database.exec(
            `SELECT f1.fact_id, f1.content, f1.trust_score,
                    f2.fact_id, f2.content, f2.trust_score
             FROM fact_entities fe1
             JOIN fact_entities fe2 ON fe1.entity_id = fe2.entity_id AND fe1.fact_id < fe2.fact_id
             JOIN facts f1 ON fe1.fact_id = f1.fact_id
             JOIN facts f2 ON fe2.fact_id = f2.fact_id
             WHERE ABS(f1.trust_score - f2.trust_score) > 0.3
             GROUP BY f1.fact_id, f2.fact_id
             LIMIT 10`
          );
          
          let output = '';
          
          if (results.length > 0 && results[0].values.length > 0) {
            const facts = results[0].values.map(row => ({
              id: row[0],
              content: row[1],
              trust: row[2],
              retrieval_count: row[3],
              helpful_count: row[4]
            }));
            
            output += `Low-trust facts (may be outdated or inaccurate):\n${facts.map(f => `[${f.id}] ${f.content} (trust: ${f.trust.toFixed(2)}, retrieved: ${f.retrieval_count}, helpful: ${f.helpful_count})`).join("\n")}`;
          }
          
          if (similarPairs.length > 0 && similarPairs[0].values.length > 0) {
            output += '\n\nPotential contradictions (shared entity, different trust):\n';
            similarPairs[0].values.forEach(row => {
              output += `[${row[0]}] "${row[1]}" (trust: ${row[2].toFixed(2)}) vs [${row[3]}] "${row[4]}" (trust: ${row[5].toFixed(2)})\n`;
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
  async (params) => {
    const database = await initDb();
    
    try {
      // 验证 fact_id 是否存在
      const feedbackCheck = database.exec("SELECT fact_id FROM facts WHERE fact_id = ?", [params.fact_id]);
      if (feedbackCheck.length === 0 || feedbackCheck[0].values.length === 0) {
        return { content: [{ type: "text", text: `Error: Fact ${params.fact_id} not found` }], isError: true };
      }
      
      const delta = params.action === "helpful" ? 0.1 : -0.1;
      
      database.run(
        `UPDATE facts SET 
          trust_score = MAX(0, MIN(1, trust_score + ?)),
          helpful_count = helpful_count + ?,
          updated_at = CURRENT_TIMESTAMP
         WHERE fact_id = ?`,
        [delta, params.action === "helpful" ? 1 : 0, params.fact_id]
      );
      
      // 获取更新后的信任分数
      const result = database.exec("SELECT trust_score FROM facts WHERE fact_id = ?", [params.fact_id]);
      const newTrust = result[0]?.values[0][0] || 0;
      
      saveDb();
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

// Graceful shutdown - 保存数据库后退出
process.on('SIGINT', () => {
  console.error("Received SIGINT, saving database...");
  saveDb();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.error("Received SIGTERM, saving database...");
  saveDb();
  process.exit(0);
});

process.on('uncaughtException', (err) => {
  console.error("Uncaught exception:", err);
  saveDb();
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error("Unhandled rejection:", reason);
  saveDb();
  process.exit(1);
});

// 启动服务器
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Holographic Memory MCP Server running on stdio");
}

main().catch(console.error);
