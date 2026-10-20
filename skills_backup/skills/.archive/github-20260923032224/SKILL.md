---
name: github
description: "Complete GitHub workflow: auth, repos, issues, PRs, code review. Use gh CLI with curl fallback."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Git, gh-cli, Pull-Requests, Issues, Code-Review, Repositories, CI/CD]
---

# GitHub Workflow

Complete guide for working with GitHub from the terminal. Every section shows `gh` first, then `git` + `curl` fallback.

## Auth Detection (run first)

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

## 1. Authentication Setup

**gh CLI (preferred):**
```bash
gh auth login                          # interactive browser login
echo "$TOKEN" | gh auth login --with-token  # headless/token login
gh auth setup-git                      # configure git credentials through gh
gh auth status                         # verify
```

**Git-only (no gh):**
```bash
git config --global credential.helper store   # persist credentials
git config --global user.name "Name"
git config --global user.email "email@example.com"
# For SSH: ssh-keygen -t ed25519 && cat ~/.ssh/id_ed25519.pub  # add to github.com/settings/keys
```

**Extract token for API calls:**
```bash
export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
```

## 2. Repository Management

| Action | gh | curl |
|--------|-----|------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create | `gh repo create name --public --clone` | `curl -X POST /user/repos -d '{"name":"name"}'` |
| Fork | `gh repo fork o/r --clone` | `curl -X POST /repos/o/r/forks` |
| Info | `gh repo view o/r` | `curl GET /repos/o/r` |
| Edit | `gh repo edit --description "..."` | `curl -X PATCH /repos/o/r` |
| Release | `gh release create v1.0 --generate-notes` | `curl -X POST /repos/o/r/releases` |
| Secrets | `gh secret set KEY --body "val"` | `curl PUT /repos/o/r/actions/secrets/KEY` |
| Workflows | `gh workflow list` / `gh run list` | `curl GET /repos/o/r/actions/workflows` |

**Batch clone pitfall:** Expect 20-30% failure rate for academic repos. Use `--depth 1`, retry 2-3 times max.

## 3. Issues

```bash
# List/View
gh issue list --state open --label "bug"
gh issue view 42

# Create
gh issue create --title "..." --body "..." --label "bug" --assignee "user"

# Manage
gh issue edit 42 --add-label "priority:high"
gh issue edit 42 --add-assignee @me
gh issue comment 42 --body "Investigated — root cause found."
gh issue close 42 --reason "completed"

# Search
gh issue list --search "authentication error" --state all

# Bulk
gh issue list --label "wontfix" --json number --jq '.[].number' | xargs -I {} gh issue close {}
```

**curl fallback:** `GET/POST/PATCH /repos/{o}/{r}/issues[/N]`

## 4. PR Lifecycle

```bash
# Branch
git checkout main && git pull origin main
git checkout -b feat/description

# Commit (Conventional Commits: feat/fix/refactor/docs/test/ci/chore/perf)
git add -A && git commit -m "feat(scope): description"

# Push & Create PR
git push -u origin HEAD
gh pr create --title "feat: ..." --body "## Summary\n...\n\nCloses #42"

# CI Status
gh pr checks              # one-shot
gh pr checks --watch      # poll until done

# Auto-Fix CI Loop
gh run list --branch $(git branch --show-current) --limit 5
gh run view <ID> --log-failed
# → fix code → git push → re-check (up to 3 attempts)

# Merge
gh pr merge --squash --delete-branch
gh pr merge --auto --squash --delete-branch   # auto-merge when checks pass
```

**curl fallback for PR create:**
```bash
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d '{"title":"...","body":"...","head":"branch","base":"main"}'
```

## 5. Code Review

### Review Local Changes (pre-push)
```bash
git diff main...HEAD --stat             # scope
git diff main...HEAD                    # full diff
git diff main...HEAD | grep -n "print(\|console.log\|TODO\|FIXME\|debugger"
```

### Review a PR
```bash
gh pr view 123
gh pr diff 123
git fetch origin pull/123/head:pr-123 && git checkout pr-123  # local checkout
```

### Post Review
```bash
# Approve
gh pr review 123 --approve --body "LGTM!"

# Request changes
gh pr review 123 --request-changes --body "See inline comments."

# Inline comment via API
gh api repos/$OWNER/$REPO/pulls/123/comments \
  -f body="Use parameterized queries." -f path="src/auth.py" -f line=45 -f side="RIGHT" \
  -f commit_id="$(gh pr view 123 --json headRefOid --jq '.headRefOid')"
```

### Review Checklist
- **Correctness:** Edge cases, error paths, null handling
- **Security:** No hardcoded secrets, input validation, SQL injection, XSS
- **Quality:** Clear naming, DRY, single responsibility
- **Testing:** New paths tested, happy + error cases
- **Performance:** No N+1 queries, appropriate caching

## 6. Pre-Commit Review (Requesting Code Review)

Before pushing, run a quality gate:

### Security Scan
```bash
# Check for secrets in staged changes
git diff --staged | grep -in "password\|secret\|api_key\|token.*=\|private_key"

# Check for debug statements
git diff --staged | grep -n "print(\|console.log\|TODO\|FIXME\|debugger"

# Run linter if configured
ruff check . 2>&1 | head -30
# or: eslint, clippy, etc.
```

### Quality Gates
1. **Lint passes** — no new warnings
2. **Tests pass** — run targeted tests for changed files
3. **No secrets** — grep for credential patterns
4. **No debug leftovers** — print/console.log/TODO
5. **Type check passes** — mypy/pyright if configured

### Auto-Fix Pattern
```bash
# Auto-fix what's fixable
ruff check --fix .
# Then verify the fix didn't break anything
python -m pytest tests/ -x -q
```

### Review Output Template
```
## Pre-Commit Review
- ✅ Lint: clean
- ✅ Tests: 47 passed
- ⚠️ Security: found TODO on line 42 (not blocking)
- ✅ No secrets detected
- Ready to push? [Y/n]
```

## Quick Reference

| Task | gh command | curl endpoint |
|------|-----------|--------------|
| List issues | `gh issue list` | `GET /repos/{o}/{r}/issues` |
| Create issue | `gh issue create` | `POST /repos/{o}/{r}/issues` |
| Create PR | `gh pr create` | `POST /repos/{o}/{r}/pulls` |
| View PR diff | `gh pr diff N` | `GET /repos/{o}/{r}/pulls/N/files` |
| Review PR | `gh pr review N --approve` | `POST /repos/{o}/{r}/pulls/N/reviews` |
| Merge PR | `gh pr merge --squash` | `PUT /repos/{o}/{r}/pulls/N/merge` |
| Check CI | `gh pr checks` | `GET /repos/{o}/{r}/commits/{sha}/status` |
| Set secret | `gh secret set KEY` | `PUT /repos/{o}/{r}/actions/secrets/KEY` |
| Create release | `gh release create v1.0` | `POST /repos/{o}/{r}/releases` |
