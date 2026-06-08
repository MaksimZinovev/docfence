

---

### The one-liner

```bash
# Get all commands, subtract brew-managed ones, intersect with AI-tooling whitelist
comm -23 \
  <(echo -${PATH}//:/ - | xargs -n1 ls -1 2>/dev/null | sort -u) \
  <(brew list --formula --quiet 2>/dev/null | xargs -I{} basename {} | sort -u) \
  | grep -iE '^(node|npm|pnpm|yarn|bun|corepack|git|gh|jq|yq|rg|fd|bat|eza|curl|wget|llm|ollama|aider|claude|gemini|pi|tmux|fzf|zoxide|uv|uvx|docker|sqlite|redis-cli|aws|terraform|kubectl|helm|delta|neovim|vim)$'
```

---

### The cleaner script (zsh-native, faster)

```bash
#!/usr/bin/env zsh
# ~/bin/ai-tooling-orphan — list AI-coding-relevant CLIs NOT from brew

setopt local_options pipe_fail

# 1. All executables in $PATH (deduped, basename only)
all_cmds=$(echo -${PATH}//:/ - | xargs -n1 ls -1 2>/dev/null | awk -F/ '{print $NF}' | sort -u)

# 2. Brew-managed basenames
brew_cmds=$(brew list --formula --quiet 2>/dev/null | xargs -I{} basename {} 2>/dev/null | sort -u)

# 3. AI-tooling whitelist (case-insensitive, anchored)
whitelist='^(node|npm|pnpm|yarn|bun|corepack|git|gh|jq|yq|rg|fd|bat|eza|curl|wget|llm|ollama|aider|claude|gemini|pi|tmux|fzf|zoxide|uv|uvx|docker|sqlite3?|redis-cli|aws|terraform|kubectl|helm|delta|n?vim|vim|helix)$'

# 4. Tools that exist but aren't from brew
comm -23 <(echo "$all_cmds") <(echo "$brew_cmds") | grep -iE "$whitelist"
```

Save to `~/.pi/agent/skills/cli-tool-discovery/tool/`, `chmod +x` it.

---

### Why `comm -23` is the right primitive

| Step | What it does |
|------|--------------|
| `comm -23 A B` | Lines in **A but NOT in B** |
| A = `ls $PATH` | Ground truth of what's executable |
| B = `brew list` | What brew installed |
| Result | Orphans — installed but not via brew |

`comm` requires **sorted** input (hence `sort -u` on both sides) and is O(n) — much faster than nested `grep -v` loops on large PATHs.

---

### Provenance hints (where the orphans came from)

Once you have the orphan list, classify origins:

| Origin | Quick test |
|--------|------------|
| **`npm -g`** | `npm ls -g --depth=0 2>/dev/null \| grep -E "^\`[└├]" \| awk '{print $2}' \| cut -d@ -f1` |
| **`pipx`** | `ls ~/.local/bin/ 2>/dev/null` |
| **`uv tool install`** | `ls ~/.local/bin/ ~/.cargo/bin/ 2>/dev/null` (overlaps) |
| **Official installer (.pkg/.tar)** | `ls /usr/local/bin/ /opt/homebrew/bin/ 2>/dev/null` |
| **Cargo** | `ls ~/.cargo/bin/ 2>/dev/null` |
| **Go** | `ls ~/go/bin/ 2>/dev/null` |
| **Mac App Store CLI wrappers** | `mdfind "kMDItemContentType=public.unix-executable"` |

---

### Caveats to know

1. **Name collisions** — `comm` matches on basename. If brew installs `node@20` and you have `node` from elsewhere, both look like "node." Check with `which -a <tool>` for the actual resolution.
2. **Apple's built-ins** — `/usr/bin/python3`, `/usr/bin/git` ship with macOS. They show up in `ls $PATH` but are *not* brew-managed, so they appear as "orphans." Filter with: `grep -vE '^(python3|git|curl|jq|node|bash|zsh|sh)$' | xargs -I{} sh -c 'brew --prefix {} 2>/dev/null | grep -q . || echo {}'` — or just add Apple's tools to a separate "system" list.
3. **`brew --prefix <tool>`** is the **ground-truth test**: if it returns a path, brew owns it; if it errors, it's an orphan. Replace step 2 above with:
   ```bash
   brew_cmds=$(for c in $all_cmds; do brew --prefix "$c" &>/dev/null && echo "$c"; done)
   ```
   Slower (one `brew` call per command) but **100% accurate**.

---

### Other 

- Bake the **Apple-builtins** exclusion in (so `python3`, `git`, `curl`, `bash` don't pollute the orphan list)
- Add a **provenance column** (column 2 = `npm` / `pipx` / `uv` / `cargo` / `unknown`)
- Or generate a **zsh completion** so `ai-tooling-orphan <tool>` shows you the install origin on demand
