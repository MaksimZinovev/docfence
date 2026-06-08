---
id: P10
type: plan
status: draft
owner: maksim
depends_on: [P8, P9]
last_validated: ~
---

# Improve Tools & Skills section: enforce Pi skill/tool enumeration, not file references

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
  has_file_marker: '(CREATED|UPDATED|DELETED)'
  has_test: '# Test \d'
  has_out_of_scope: '^## Out of Scope'
  has_tools_and_skills: '^## Tools & Skills'
  has_ynp_format: '^- \*\*[^*]+\*\*: (Yes|No|Possibly)\b'
```

## Context

```spec
type: plan
max_chars: 20000
banned_words: [might be, could be, seems like, I think, possibly, perhaps]
match:
  has_problem: '(problem|issue|bug|break|fail|cannot|does.not|unable)'
```

The Tools & Skills section in P8 was filled with file references (`validator.py`, `plan.toml type`, `orient-startup-race.md`) instead of actual Pi skills and tools. The fill text in plan.toml says "List top ~10 relevant tools/skills" but never defines what a "tool" or "skill" means — the planner assumes any relevant artifact counts. format.md doesn't clarify this either. The match rule `has_ynp_format` only checks bullet formatting, not whether items are actual skills/tools from the Pi ecosystem. This will recur every time a plan is written unless the type definition and skill instructions make the enumeration source explicit. (Source: P8 Tools & Skills section before annotation fix, plan.toml fill text L36)

## Tools & Skills

```spec
type: plan
max_chars: 20000
banned_words: [N/A, n/a]
match:
  min_3_ynp: '^- \*\*[^*]+\*\*: (Yes|No|Possibly)\b'
```

- **grounded-planning**: Yes — this plan modifies the plan type and planning skill
- **skill-creator**: Yes — updating SKILL.md for grounded-planning
- **verification-before-completion**: Yes — validate scaffold and existing plans after changes
- **cx/ck**: Possibly — if searching for other references to the fill text
- **systematic-debugging**: No — no investigation needed
- **root-cause-tracing**: No — root cause is clear (ambiguous fill text)
- **commit**: Possibly — multi-repo commit coordination

## Approach

```spec
type: plan
max_chars: 800
banned_words: [Q1:, Q2:, Q3:, **Q, Question:]
match:
  has_alternative: '(alternative|instead of|rather than|compared to|over:|vs[.])'
```

Make the enumeration source explicit in three places: (1) plan.toml fill text must state "Pi skills from `pi --skills` and tools from `pi --tools`", (2) format.md must document what counts as a valid entry, (3) SKILL.md must instruct the planner to run `pi --skills` and `pi --tools` before filling the section. An alternative — adding a match rule that validates entries against a known skill list — is brittle: skills change, and regex can't check membership against a dynamic list. Instead, the match rule stays format-only (Y/N/P structure) and the skill instructions enforce correctness procedurally.

## Out of Scope

```spec
type: plan
max_chars: 20000
banned_words: [Nothing., None., N/A, n/a, Not applicable]
match:
  has_justification: '^- \*\*[^*]+\*\*:'
  min_2_exclusions: '^- \*\*[^*]+\*\*:'
```

- **Adding a match rule for skill/tool membership**: Regex can't validate against a dynamic list. Procedural enforcement via SKILL.md is sufficient.
- **Changing Y/N/P format**: The format works; the problem is what items qualify, not how they're formatted.
- **Auto-generating Tools & Skills from `pi --skills` output**: Would be a future enhancement (script that scaffolds the section from actual skill tree), not this fix.
- **P8 and P9 fixes**: Separate plans.

## Steps

```spec
type: plan
max_chars: 20000
banned_words: [**Step, **Task, **Phase]
match:
  has_step_evidence: '^- \[ \].*\(Source'
  min_3_steps: '^- \[( |x)\]'
```

- [ ] **Update plan.toml fill text for Tools & Skills section**: Change from generic "tools/skills" to explicit "Pi skills and tools". Current: `"[REPLACE] List top ~10 relevant tools/skills: **name**: Yes / No (why not needed) / Possibly (when you'd use it). Minimum 3 entries. No N/A."` — New: `"[REPLACE] List Pi skills from pi --skills and tools from pi --tools: **skill-name**: Yes / No (reason) / Possibly (when). Minimum 3 entries. No N/A. No file references. No dismissive 'No' — justify by task scope."`
  - Evidence: The current fill text never defines "tools/skills" as Pi ecosystem items — planner fills with whatever seems relevant, including file paths. Also, "No" reasons like "codebase is small" are dismissive — they say "I didn't think about it" rather than "it's categorically irrelevant to this task's scope." (Source: plan.toml fill text, P8 annotation feedback: "this is not an excuse")
  - Confidence: 0.95
  - Details: The fill text now requires: (a) enumeration source = Pi skills/tools, (b) no file references, (c) "No" justifications must reference task scope/nature, not codebase size or convenience.

- [ ] **Add `file_references` to banned_words for Tools & Skills section**: Add patterns that catch file-path entries like `validator.py`, `plan.toml type`, `orient-startup-race.md`. These are never valid skill/tool names.
  - Evidence: P8 had entries like `**validator.py**: Yes` and `**plan.toml type**: Yes` — these are files, not skills. (Source: P8 annotation feedback)
  - Confidence: 0.85
  - Details: Add to `[template_vars.sections."Tools & Skills".banned_words]`: entries like `.py`, `.toml`, `.md`, `.json` — but be careful not to ban legitimate skill names that might contain dots. Better approach: add a note in fill text that says "No file references" and rely on procedural enforcement, since banning `.py` etc. would also catch `mcp: github-cli` style entries if we're not careful.

- [ ] **Add dismissive "No" patterns to banned_words for Tools & Skills section**: Ban phrases that indicate the author didn't think about the skill: "small codebase", "simple enough", "grep sufficient", "not needed for small", "overkill for". These are excuses, not justifications.
  - Evidence: P8 had "cx/ck: No — codebase is small, known files, grep sufficient" — the "No" was dismissive, not grounded in task scope. A proper "No" would be: "cx/ck: No — scope is a single-line validation filter change with no code search needed." (Source: P8 annotation feedback)
  - Confidence: 0.85
  - Details: Add to `[template_vars.sections."Tools & Skills".banned_words]`: `grep sufficient`, `small codebase`, `simple enough`, `overkill for`. These patterns specifically flag laziness, not legitimate scope-based decisions.

- [ ] **Update format.md: document what counts as a valid Tools & Skills entry and valid "No" justification**: Add a clarifying section explaining that (a) "tools" means Pi tools, "skills" means Pi skills — files go in Files to Modify, not here; (b) "No" justifications must reference the task's scope/nature, not codebase size or convenience. Include examples of good vs bad "No" reasons.
  - Evidence: format.md currently doesn't define what qualifies as a tool or skill, and doesn't distinguish dismissive from grounded "No" justifications. (Source: format.md)
  - Confidence: 0.90
  - Details: Add a table. Bad "No": "cx: No — codebase is small, grep sufficient" (dismissive — about the codebase, not the task). Good "No": "cx: No — scope is a single-line regex change, no code search needed" (grounded — about the task's nature).

- [ ] **Update SKILL.md for grounded-planning: add skill enumeration step**: In the planning workflow, add a step between "read format.md" and "scaffold" that says: "Run `pi --skills` and `pi --tools` to enumerate available skills/tools before filling Tools & Skills section. Only list items from these sources."
  - Evidence: SKILL.md currently doesn't mention where to find valid skills/tools. The planner has no way to know the enumeration source. (Source: pi-agent-config/skills/grounded-planning/SKILL.md)
  - Confidence: 0.90
  - Details: Add to Step 5 (scaffold first) or create a new step: "Before filling Tools & Skills, enumerate available Pi skills and tools: run `pi --skills` and `pi --tools`. Only list items that appear in these outputs or are direct MCP tools."

- [ ] **Sync plan.toml changes to pi-agent-config repo**: Copy the updated plan.toml from docfence repo to pi-agent-config/.docfence/types/plan.toml.
  - Evidence: Both repos must stay in sync per established convention. (Source: previous session work)
  - Confidence: 0.95
  - Details: `cp /Users/maksim/repos/docfence/.docfence/types/plan.toml /Users/maksim/repos/pi-agent-config/.docfence/types/plan.toml`

## Files to Modify

```spec
type: plan
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
match:
  has_file_marker: '(CREATED|UPDATED|DELETED)'
```

- `docfence/.docfence/types/plan.toml` — UPDATED: change Tools & Skills fill text to reference Pi skills/tools explicitly; add banned words for file references and dismissive "No" patterns
- `pi-agent-config/.docfence/types/plan.toml` — UPDATED: synced copy of above
- `pi-agent-config/skills/grounded-planning/references/format.md` — UPDATED: add valid/invalid entry examples for Tools & Skills section
- `pi-agent-config/skills/grounded-planning/SKILL.md` — UPDATED: add skill enumeration step before filling Tools & Skills

## Reuse

```spec
type: plan
max_chars: 20000
banned_words: [None., N/A, Nothing to reuse, No reuse]
match:
  has_reuse_item: '^- \*\*[^*]+\*\*:'
```

- **Existing `has_ynp_format` match rule**: Correctly validates Y/N/P structure — no change needed. The fix is about what items qualify, not format. (Source: plan.toml match rules)
- **Existing banned_words mechanism**: Can add file-extension patterns to catch file references in the section. (Source: plan.toml section-level banned_words)
- **P8 annotation feedback**: The corrected Tools & Skills section in P8 (after user fix) serves as a reference example of what a valid entry list looks like. (Source: P8 Tools & Skills after fix)

## Evidence Pack

```spec
type: plan
max_chars: 20000
banned_words: [**Source**:, **Source:**]
match:
  has_evidence_claim: '^- \*\*Claim\*:'
  has_confidence: '\*\*Confidence\*\*:'
```

- **Claim**: The root cause is ambiguous fill text — "tools/skills" is undefined, so the planner fills with whatever seems relevant including file references.
  Source: plan.toml fill text: `[REPLACE] List top ~10 relevant tools/skills` — no definition of what qualifies
  **Confidence**: 0.95
  **Implication**: Making the enumeration source explicit in fill text + format.md + SKILL.md eliminates the ambiguity.

- **Claim**: Procedural enforcement (SKILL.md instruction + explicit fill text) is sufficient; a match rule for membership validation is impractical.
  Source: The skill set is dynamic (changes as skills are installed/removed); regex can't validate membership against a dynamic list
  **Confidence**: 0.90
  **Implication**: Don't try to solve this with match rules — solve it with clear instructions.

- **Claim**: Banning file extensions (.py, .md, .toml) in Tools & Skills banned_words is risky because some MCP tools or CLI tools might contain dots in their names.
  Source: MCP tool names like `mcp: github-cli` don't contain file extensions, but hypothetical future tools might
  **Confidence**: 0.70
  **Implication**: Safer to add "No file references" to fill text and rely on procedural enforcement than to risk false positives from pattern-based banning.

- **Claim**: Dismissive "No" justifications ("codebase is small, grep sufficient") are a different failure mode from file references — they indicate the author didn't assess the skill's relevance to the task scope.
  Source: P8 annotation: "this is not an excuse" — the user flagged that "codebase is small" says nothing about whether cx/ck is relevant to the task
  **Confidence**: 0.95
  **Implication**: Banned_words can catch the most common dismissive patterns ("grep sufficient", "small codebase"), but fill text guidance ("No dismissive No — justify by task scope") is needed for the long tail.

### Gaps

- Haven't validated that `pi --skills` and `pi --tools` are reliable commands that always produce a usable skill/tool list. Should verify before committing to this approach.
- The fill text change won't retroactively fix existing plans — only P8 was manually corrected via annotation.

## Verification

```bash
# Test 1: Generate fresh scaffold and check Tools & Skills fill text
cd /Users/maksim/repos/docfence && python -m docfence new plan 2>&1 | grep -A2 "Tools & Skills"
# Expected: fill text mentions "pi --skills" and "pi --tools", says "No file references"

# Test 2: Validate P8 plan after regenerating scaffold (if regenerated)
cd /Users/maksim/repos/docfence && python -m docfence validate plans/P8-scope-leak-required-sections-placeholders.md 2>&1 | grep "Tools"
# Expected: no validation errors specifically about Tools & Skills format

# Test 3: Verify format.md documents valid/invalid examples
grep -c "pi --skills\|pi --tools" /Users/maksim/repos/pi-agent-config/skills/grounded-planning/references/format.md
# Expected: at least 2 matches (both commands mentioned)

# Test 4: Verify SKILL.md mentions skill enumeration step
grep -c "pi --skills\|pi --tools" /Users/maksim/repos/pi-agent-config/skills/grounded-planning/SKILL.md
# Expected: at least 1 match

# Test 5: Confirm both plan.toml files are in sync
diff /Users/maksim/repos/docfence/.docfence/types/plan.toml /Users/maksim/repos/pi-agent-config/.docfence/types/plan.toml
# Expected: no differences
```

## Bottom Line

- **Per-step confidence**: 0.91 (average)
- **Key risk**: `pi --skills` / `pi --tools` might not be stable/guaranteed commands — need to verify.
- **Gap**: Procedural enforcement (fill text + SKILL.md) won't catch all mistakes at validation time — only at authoring time. Banned words catch common dismissive patterns but not novel ones.
- **Recommendation**: proceed — low-code fix (text/banned_words changes in 4 files), addresses two root causes: ambiguous enumeration source and dismissive "No" justifications.