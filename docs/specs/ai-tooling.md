Pi's CLI surface is small but it shells out to *a lot* during agentic runs. Based on Pi's documented deps + the AI-coding-agent ecosystem it lives in, here's the curated whitelist (regex, case-insensitive):

```bash
brew list --formula --quiet 2>/dev/null \
  | xargs -I{} basename {} 2>/dev/null \
  | grep -iE '^(node|npm|pnpm|yarn|bun|corepack)$
|^python[0-9.]*$
|^(pip|pipx|uv|uvx|poetry|conda|mamba|micromamba)$
|^ruff$|^black$|^flake8$|^mypy$|^isort$|^pyright$|^basedpyright$
|^git$|^gh$|^glab$|^hub$
|^docker$|^podman$|^nerdctl$|^colima$
|^curl$|^wget$|^httpie$|^xh$
|^jq$|^yq$|^gron$|^dasel$|^fx$|^jql$
|^fzf$|^rg$|^ripgrep$|^fd$|^bat$|^eza$|^lsd$|^zoxide$|^autojump$
|^htop$|^btop$|^glances$|^bottom$
|^tldr$|^cheat$|^navi$|^browsh$|^http-prompt$
|^make$|^cmake$|^just$|^task$|^zig$|^go$|^rustc$|^cargo$|^swift$
|^ffmpeg$|^magick$|^imagemagick$|^exiftool$
|^sqlite3?$|^mysql$|^psql$|^redis-cli$|^mongosh$|^litecli$
|^aws$|^gcloud$|^az$|^doctl$|^fly$|^vercel$|^wrangler$|^netlify$|^supabase$
|^terraform$|^tofu$|^pulumi$|^ansible$|^vagrant$|^packer$
|^kubectl$|^helm$|^k9s$|^kustomize$|^kubectx$|^stern$
|^nix$|^direnv$|^mise$|^rtx$|^asdf$|^virtualenv$|^venv$
|^llm$|^ollama$|^openai$|^claude$|^gemini$|^aider$|^cody$|^cline$|^continue$|^msty$|^jan$
|^pi$|^pi-cli$
|^tmux$|^zellij$|^wezterm$|^alacritty$|^kitty$
|^lazygit$|^tig$|^delta$|^diff-so-fancy$
|^neovim$|^vim$|^helix$|^emacs$|^micro$|^nano$
|^obsidian$|^typora$|^marktext$
|^stow$|^chezmoi$|^mackup$|^backup-utils$|^restic$|^borg$|^rsync$|^rclone$
|^shellcheck$|^shfmt$|^actionlint$|^hadolint$|^tflint$|^markdownlint$|^yamllint$|^vale$|^alex$'
```

---

### How to use it

**Save as a script** (`~/bin/ai-tooling`):
```bash
#!/usr/bin/env zsh
# ai-tooling — list CLI tools most relevant for AI coding agents (Pi-focused)
brew list --formula --quiet 2>/dev/null \
  | xargs -I{} basename {} 2>/dev/null \
  | grep -iEF "$HOME/.config/ai-tooling.regex" \
  | sort -u
chmod +x ~/bin/ai-tooling
```

**Or one-liner** (pasteable):
```bash
brew list --formula --quiet | xargs -I{} basename {} | grep -ciE 'node|python|git|docker|jq|fzf|rg|fd|bat|curl|llm|ollama|aider|claude|pi'
# → prints COUNT of matching installed tools
```

**Or get the actual names**:
```bash
brew list --formula --quiet | xargs -I{} basename {} | grep -iE '^(node|python|git|docker|jq|fzf|rg|fd|bat|curl|llm|ollama|aider|claude|pi|uv)$' | sort -u
```

---

### Coverage notes (what I included for Pi specifically)

| Category | Why Pi needs them |
|----------|-------------------|
| `node`, `npm`, `pnpm`, `bun`, `corepack` | Pi's runtime + package installs |
| `python`, `uv`, `uvx`, `pipx`, `poetry` | MCP servers, Python tool execution, `uv` is Pi's default runner |
| `git`, `gh`, `delta`, `lazygit` | All agentic commits/PRs go through git |
| `docker`, `podman`, `colima` | Sandboxed code execution, containerized MCP |
| `jq`, `yq`, `dasel`, `fx` | Pi emits/edits JSON/YAML/TOML constantly |
| `fzf`, `rg`, `fd`, `bat`, `eza`, `zoxide` | Shell workflow primitives Pi assumes |
| `tldr`, `cheat`, `navi` | Pi looks up CLI flags via these |
| `shellcheck`, `actionlint`, `yamllint`, `vale` | Pi's own validation hooks |
| `mise`/`rtx`/`asdf`, `direnv` | Pi respects `.tool-versions` / `.envrc` |
| `tmux`, `zellij` | Pi's background task pane |
| `llm`, `ollama`, `claude`, `gemini`, `aider`, `cline`, `pi` | Competing/co-existing agents you'll pipe to |
| `chezmoi`, `stow`, `mackup` | Dotfile restoration across machines |

---
