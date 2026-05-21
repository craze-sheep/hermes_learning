# Codex Code Review Checklist

Use this when delegating code review to Codex. Pass as context in the delegate_task call.

## Review Categories

### 1. Correctness
- [ ] Logic matches intent
- [ ] Edge cases handled (null, empty, boundary values)
- [ ] Error handling present and correct
- [ ] No off-by-one errors

### 2. Data Integrity
- [ ] Atomic writes for file operations (tmp + rename)
- [ ] Database transactions where needed
- [ ] No data loss on crash/signal
- [ ] Foreign key constraints enforced

### 3. Security
- [ ] Parameterized queries (no SQL injection)
- [ ] Input validation (Zod schemas)
- [ ] No credentials in logs/error messages
- [ ] Proper escaping of special characters

### 4. Performance
- [ ] No unnecessary I/O (e.g., saveDb on reads)
- [ ] Efficient queries (indexes, no full scans)
- [ ] Batch operations where possible
- [ ] No N+1 query patterns

### 5. Consistency
- [ ] Scripts match current architecture
- [ ] Backup includes all important files
- [ ] Documentation matches implementation
- [ ] Column/table names consistent across files

### 6. Robustness
- [ ] Graceful shutdown handlers
- [ ] Signal handling (SIGINT, SIGTERM)
- [ ] Uncaught exception handling
- [ ] Cleanup of orphan records

## Codex Delegation Pattern

```javascript
delegate_task({
  goal: "Review [files] for [specific concerns]",
  context: "Architecture: ...\nKnown issues: ...\nExpected behavior: ...",
  toolsets: ["terminal", "file"]
})
```

Tips:
- Always provide file paths and architecture context
- List specific concerns, not just "review this"
- Ask for severity ratings (critical/medium/low)
- Ask Codex to verify fixes by running tests
