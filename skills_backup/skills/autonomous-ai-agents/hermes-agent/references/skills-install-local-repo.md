# Installing Skills from a Local Git Clone

## Problem

`hermes skills install <local-path>` does NOT read local files — it parses
the path as a GitHub identifier and hits the GitHub API. Even absolute paths
like `/tmp/repo/skills/foo/SKILL.md` trigger the GitHub fetcher, resulting in:

```
Error: Could not fetch '/tmp/repo/skills/foo/SKILL.md' from any source.
Hint: GitHub API rate limit exhausted (unauthenticated: 60 requests/hour).
```

## Workaround: Direct File Copy

Skip `hermes skills install` entirely. Copy SKILL.md files directly into
`~/.hermes/skills/<category>/<skill-name>/SKILL.md`:

```bash
# Example: installing all skills from a cloned repo
REPO=/tmp/superpowers
SKILLS_DIR="$HOME/.hermes/skills/superpowers"
mkdir -p "$SKILLS_DIR"

for skill in $(ls "$REPO/skills/"); do
  src="$REPO/skills/$skill/SKILL.md"
  if [ -f "$src" ]; then
    mkdir -p "$SKILLS_DIR/$skill"
    cp "$src" "$SKILLS_DIR/$skill/SKILL.md"
    echo "[OK] $skill"
  fi
done
```

After copying, verify with `hermes skills list | grep <category>`.

## Notes

- The category directory name (e.g. `superpowers`) becomes the skill's
  `category` field in `hermes skills list`.
- Skills installed this way show as `source: local`, same as manually created
  skills. They are fully functional — auto-trigger, `/skill`, `skill_view`
  all work.
- If the repo needs a proxy to clone, set `HTTP_PROXY`/`HTTPS_PROXY` env vars
  before `git clone`, e.g.:
  ```bash
  git -c http.proxy=http://127.0.0.1:7897 clone --depth 1 https://github.com/org/repo.git /tmp/repo
  ```
- `hermes skills tap add <owner/repo>` registers the repo as a source but
  does NOT download skills. The actual install still uses `hermes skills install`
  which hits the same rate limit issue.
