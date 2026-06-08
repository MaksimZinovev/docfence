---
id: P10b
type: plan
status: draft
owner: maksim
depends_on: [P10]
last_validated: ~
---

# Fix Tools & Skills Enumeration: Correct Commands, Four Categories, SKILL.md Step

```spec
scope: document
type: plan
required_sections: [Context, Tools & Skills, Approach, Out of Scope, Steps, Files to Modify, Reuse, Evidence Pack, Verification, Bottom Line]
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
placeholders: ["```df-todo", "[REPLACE]"]
match:
  has_checklist: '^- \[( |x)\]'
  has_source: 'Source:'
  has_file_marker: "(CREATED|UPDATED|DELETED)"
  has_test: '# Test \d'
  has_out_of_scope: "^## Out of Scope"
  has_tools_and_skills: '^## Tools & Skills'
  has_ynp_format: '^- .+: (Yes|No|Possibly)\b'
```

## Context

```spec
type: plan
max_chars: 20000
banned_words: [might be, could be, seems like, I think, possibly, perhaps]
match:
  has_problem: '(problem|issue|bug|break|fail|cannot|does.not|unable)'
```

P10's original fill text fails to provide working enumeration commands — `pi --skills` and `pi --tools` don't exist ("Unknown option"), `pi list` shows npm packages (not tools Pi can use), `cat ~/.pi/agent/mcp.json` dumps the entire config file (too verbose), and `tree -L 1 -d ~/.pi/agent/extensions/` lists extension directories but does not reveal what tools Pi can actually leverage. The fill text cannot clearly define what qualifies as a valid entry or how to discover it. The intent of the Tools & Skills section is to ensure Pi leverages additional capabilities — skills, MCP servers, and contextually relevant CLI tools — rather than skipping them. The SKILL.md does not include an enumeration step for skills/tools before filling Tools & Skills. format.md has valid/invalid examples but cannot enumerate entries — there is no "How to enumerate" section with working commands. (Source: verified by running `pi --skills`, `pi --tools`, `pi list`, `mcporter list`, `ls ~/.pi/agent/skills/`)

## Tools & Skills

```spec
type: plan
max_chars: 20000
banned_words: [N/A, n/a]
match:
  min_3_ynp: '^- .+: (Yes|No|Possibly)\b'
```

- cx/ck: Yes — navigating codebase and searching references in plan files
- docfence (validate/new): Yes — validating scaffold and plan files after changes
- grounded-planning: Yes — this is a grounded plan
- github-cli: No — no PR creation needed for this change
- commit: Possibly — if changes span both repos

## Approach

```spec
type: plan
max_chars: 800
banned_words: [Q1:, Q2:, Q3:, **Q, Question:]
match:
  has_alternative: '(alternative|instead of|rather than|compared to|over:|vs[.])'
```

Fix the enumeration command references to use verified, working commands. Define four categories (Skills, MCP, Extensions, CLI) in fill text, format.md, and SKILL.md. Add an enumeration instruction inside the fill step of SKILL.md. An alternative — adding a match rule to validate entries against a known list — was rejected in P10 as brittle (regex can't check membership against a dynamic list). Instead, we rely on procedural enforcement via fill text guidance + SKILL.md instructions, which is the minimal, simplest approach.

## Out of Scope

```spec
type: plan
max_chars: 20000
banned_words: [Nothing., None., N/A, n/a, Not applicable]
match:
  has_justification: '^- .+:'
  min_2_exclusions: '^- .+:'
```

- Adding match rules for membership validation: Regex can't validate against a dynamic list. Procedural enforcement is sufficient.
- Changing the Y/N/P format: The format works; the fix is about what qualifies, not how it's formatted.
- Re-doing P10 steps already completed: fill text structure, banned_words for dismissive No, and format.md valid/invalid examples are done.
- Updating other plan files (P1–P9): Only P10b's target files change.

## Steps

```spec
type: plan
max_chars: 20000
banned_words: [**Step, **Task, **Phase]
match:
  has_step_evidence: '^- \[ \].*\(Source'
  min_3_steps: '^- \[( |x)\]'
```

- [ ] Update plan.toml fill text for Tools & Skills section (Source: plan.toml `[template_vars.sections."Tools & Skills"].fill`)
  - Confidence: 0.95
  - Details: Change from `Audit from tree -L 1 -d ~/.pi/agent/skills/ .pi/skills/ (skills), tree -L 1 -d ~/.pi/agent/extensions/ .pi/extensions/ (extensions), pi list (MCP)` to three categories with working commands: (1) Skills — `ls -1 ~/.pi/agent/skills/ .pi/skills/ 2>/dev/null`, (2) MCP — `mcporter list` (concise, shows server names + tool counts), (3) CLI — `~/.pi/agent/skills/cli-tool-discovery/tool/ai-tooling` (hybrid brew+command-v script per ai-tooling.md spec, stored in skill folder). The purpose is ensuring Pi leverages available capabilities. Not `pi --skills`/`pi --tools` (don't exist), not `pi list` (npm packages), not `cat ~/.pi/agent/mcp.json` (dumps entire config), not `tree -L 1 -d ~/.pi/agent/extensions/` (directories, not tools).

- [ ] Update format.md: Add "How to enumerate" section with three categories + working commands, and add category labels to valid/invalid entries (Source: format.md Tools & Skills section)
  - Confidence: 0.90
  - Details: Add a section before Invalid entries: "### How to enumerate valid entries" with three bullet points: Skills (`ls -1 ~/.pi/agent/skills/ .pi/skills/`), MCP (`mcporter list`), CLI (`~/.pi/agent/skills/cli-tool-discovery/tool/ai-tooling`). Purpose: ensure Pi leverages all available capabilities. Add category labels to valid entries: `- cx (skill): Yes`, `- github (MCP): Yes`, `- jq (CLI): Yes`. Remove references to `pi --skills`, `pi --tools`, `pi list`, `cat ~/.pi/agent/mcp.json`, `tree -L 1 -d ~/.pi/agent/extensions/`.

- [ ] Update SKILL.md: Add enumeration sub-step inside fill step with three categories and working commands, update Hard Requirements (Source: SKILL.md Quick Reference, Workflow, and Hard Requirements sections)
  - Confidence: 0.95
  - Details: (a) Inside the fill step, add: "Before filling Tools & Skills, enumerate available capabilities: skills via `ls -1 ~/.pi/agent/skills/ .pi/skills/`, MCP via `mcporter list`, CLI via `~/.pi/agent/skills/cli-tool-discovery/tool/ai-tooling`. Three categories: Skills, MCP, CLI. Purpose: ensure Pi leverages all available capabilities." (b) Update Hard Requirements bullet: change `Enumerate from tree -L 1 -d ~/.pi/agent/skills/ .pi/skills/ (skills), tree -L 1 -d ~/.pi/agent/extensions/ .pi/extensions/ (extensions), pi list (MCP)` to the three-category version with working commands. Remove all references to `pi list`, `cat ~/.pi/agent/mcp.json`, `tree -L 1 -d ~/.pi/agent/extensions/`.

- [ ] Sync plan.toml from docfence to pi-agent-config repo (Source: `diff` shows both currently identical)
  - Confidence: 0.95
  - Details: `cp /Users/maksim/repos/docfence/.docfence/types/plan.toml /Users/maksim/repos/pi-agent-config/.docfence/types/plan.toml` — must happen after fill text update.

- [ ] Update Hard Requirements in SKILL.md: Fix enumeration bullet to three categories with correct commands (Source: SKILL.md Hard Requirements, current bullet uses wrong `pi list` and `tree extensions` commands)
  - Confidence: 0.95
  - Details: Change `Enumerate from tree -L 1 -d ~/.pi/agent/skills/ .pi/skills/ (skills), tree -L 1 -d ~/.pi/agent/extensions/ .pi/extensions/ (extensions), pi list (MCP)` to: Skills (`ls -1 ~/.pi/agent/skills/ .pi/skills/`), MCP (`mcporter list`), CLI (`~/.pi/agent/skills/cli-tool-discovery/tool/ai-tooling`). Remove all references to `pi list`, `cat ~/.pi/agent/mcp.json`, `tree -L 1 -d ~/.pi/agent/extensions/`.

- [x] Create hybrid `ai-tooling` script at `~/.pi/agent/skills/cli-tool-discovery/tool/ai-tooling` (Source: docs/specs/ai-tooling.md + docs/specs/ai-tooling-orphane.md)
  - Confidence: 1.0 (DONE)
  - Details: Created and tested. Uses PATH-scan + regex whitelist approach (from ai-tooling-orphane.md): scans all executables in `$PATH`, intersects with AI-tooling whitelist, deduplicates. Found 54 tools on this machine. Regex file at `ai-tooling.regex` kept as reference. Dedupes python version noise. No dependency on bash 4+ — works with macOS zsh.

## Files to Modify

```spec
type: plan
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
match:
  has_file_marker: '(CREATED|UPDATED|DELETED)'
```

- [ ] Update plan.toml fill text: `ls -1 ~/.pi/agent/skills/` (Skills), `mcporter list` (MCP), `cli-tool-discovery` skill (CLI) — NOT `pi --skills`, `pi --tools`, `pi list`, `cat ~/.pi/agent/mcp.json`, or `tree -L 1 -d ~/.pi/agent/extensions/` (Source: plan.toml fill text, command verification)
  - Confidence: 0.95
- `pi-agent-config/.docfence/types/plan.toml` — UPDATED: synced copy from docfence
- `pi-agent-config/skills/grounded-planning/references/format.md` — UPDATED: add "How to enumerate" section and category labels
- `pi-agent-config/skills/grounded-planning/SKILL.md` — UPDATED: add enumeration sub-step inside fill step, update Hard Requirements

## Reuse

```spec
type: plan
max_chars: 20000
banned_words: [None., N/A, Nothing to reuse, No reuse]
match:
  has_reuse_item: '^- .+:'
```

- Existing plan.toml structure: TOML fill text, banned_words, and match rules follow the same pattern — only the fill text content changes (Source: plan.toml)
- P10 completed steps: Fill text structure, banned_words, and format.md valid/invalid examples are already done — this plan only fixes the command references and adds four categories (Source: P10 plan, completed items)

## Evidence Pack

```spec
type: plan
max_chars: 20000
banned_words: [**Source**:, **Source:**]
match:
  has_evidence_claim: '^- Claim:'
  has_confidence: 'Confidence:'
```

- Claim: `pi --skills` and `pi --tools` do not exist as Pi CLI commands — they return "Unknown option".
  Source: Running `pi --skills` and `pi --tools` this session — both returned "Error: Unknown option: --skills" / "Error: Unknown option: --tools"
  Confidence: 1.0
  Implication: P10's original plan premise was wrong. Must use `tree`, `cat mcp.json`, and project-context commands instead.

- Claim: The verified enumeration commands are: `ls -1 ~/.pi/agent/skills/ .pi/skills/` (30 skills), `mcporter list` (6 MCP servers with tool counts), and `~/.pi/agent/skills/cli-tool-discovery/tool/ai-tooling` (hybrid brew+command-v CLI tool discovery script per ai-tooling.md spec). `pi --skills`/`pi --tools` don't exist. `pi list` lists npm packages, not tools Pi can use. `cat ~/.pi/agent/mcp.json` dumps the entire config (too verbose). `tree -L 1 -d ~/.pi/agent/extensions/` lists directories but doesn't reveal tools Pi can leverage.
  Source: Command verification this session; docs/specs/ai-tooling.md + docs/specs/ai-tooling-orphane.md specs
  Confidence: 1.0
  Implication: Use `ls -1 ~/.pi/agent/skills/`, `mcporter list`, and the `ai-tooling` script as the three enumeration sources. The ai-tooling script uses the orphane.md approach: PATH-scan all executables, intersect with the AI-tooling whitelist — catches both brew-managed and orphan tools (fnm, conda, manual installs). Tested: finds 54 tools on this machine.

- Claim: `pi list` lists npm packages (pi-lens, pi-mcp-adapter, pi-interview, etc.), not tools Pi can use for planning.
  Source: Running `pi list` this session
  Confidence: 1.0
  Implication: Remove `pi list (MCP)` from fill text — it does not enumerate usable tools. Use `mcporter list` for MCP instead.

- Claim: Both plan.toml files (docfence and pi-agent-config) are currently identical.
  Source: `diff` between the two files shows no differences
  Confidence: 1.0
  Implication: Sync step is straightforward — copy from docfence to pi-agent-config after changes.

### Gaps

- The `ai-tooling` script uses the orphane.md approach (PATH-scan + regex whitelist intersection) rather than brew list + command-v fallback. This catches all tools in PATH regardless of how they were installed — no false negatives from non-brew installs. It won't find tools not in PATH (e.g., downloaded binaries in ~/bin without PATH entry).
- `mcporter list` depends on MCP server availability — may show offline servers (Playwright was offline during verification). Fill text should note this.
- The `ai-tooling.regex` file is kept as reference alongside the script, but the script embeds the regex inline to avoid `grep -iEF` issues with external regex files.

## Verification

```bash
# Test 1: Scaffold a new plan and check Tools & Skills fill text references
cd /Users/maksim/repos/docfence && python -m docfence new plan --output /tmp/test-p10b.md 2>&1
grep "Tools & Skills" /tmp/test-p10b.md -A2
# Expected: fill text mentions ls skills, mcporter list, CLI project context — NOT pi --skills, pi --tools, pi list, cat mcp.json, or tree extensions

# Test 2: Validate P10 plan still passes
cd /Users/maksim/repos/docfence && python -m docfence validate plans/P10-tools-skills-enumeration-source.md 2>&1
# Expected: no new validation errors (P10b plan must also pass after creation)

# Test 3: Check format.md has "How to enumerate" section with three categories and ai-tooling reference
grep -c "How to enumerate\|mcporter list\|cli-tool-discovery\|ai-tooling\|ls -1.*skills" /Users/maksim/repos/pi-agent-config/skills/grounded-planning/references/format.md
# Expected: at least 4 matches (section header + Skills cmd + MCP cmd + CLI reference)

# Test 4: Check SKILL.md has enumeration commands in the fill step and Hard Requirements
grep -c "ls -1 ~/.pi/agent/skills/\|mcporter list\|ai-tooling" /Users/maksim/repos/pi-agent-config/skills/grounded-planning/SKILL.md
# Expected: at least 3 matches (fill step + Hard Requirements + ai-tooling reference)
# Also verify NO references to removed commands
grep -c "pi list\|cat ~/.pi/agent/mcp.json\|tree -L 1 -d ~/.pi/agent/extensions" /Users/maksim/repos/pi-agent-config/skills/grounded-planning/SKILL.md
# Expected: 0

# Test 5: Confirm the ai-tooling script works
~/.pi/agent/skills/cli-tool-discovery/tool/ai-tooling 2>&1 | head -20
# Expected: list of installed CLI tools matching the regex pattern (e.g., node, python3, git, jq, gh, etc.)

# Test 5: Confirm both plan.toml files are in sync
diff /Users/maksim/repos/docfence/.docfence/types/plan.toml /Users/maksim/repos/pi-agent-config/.docfence/types/plan.toml
# Expected: no differences

# Test 6: Validate P10b plan itself
cd /Users/maksim/repos/docfence && python -m docfence validate plans/P10b-fix-enumeration-commands.md 2>&1
# Expected: clean validation
```

## Bottom Line

- Per-step confidence: 0.94 (average; ai-tooling script step at 1.0 since it's done)
- Key risk: `mcporter list` may show offline servers; `ai-tooling` whitelist may miss very new/niche tools not in the curated regex
- Gaps: `ai-tooling` covers ~100 curated tool names from the spec; extremely niche tools not in the whitelist won't appear but could be added
- Recommendation: proceed — 5 remaining text changes across 4 files; ai-tooling script is already created and tested