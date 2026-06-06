# Alternative A: Plan Doc Type — Existing Rules Only

## Background

The planner agent produces plans that omit required sections (Context, Approach, Files to Modify, Reuse), skips `- [ ]` checklists (uses bold headers instead), and leaves out runnable verification commands. The model ignores instructions to read format files (SKILL.md, format.md). Telling it to follow a format doesn't work — enforce it structurally instead.

**Direction**: Create a `plan` doc type in DocFence that encodes the agreed format as validation rules. The planner scaffolds a plan template, fills it, then runs `docfence validate` — if validation fails, the planner must fix the issues before the plan is done. No code changes to DocFence itself.

## What This Covers

| Format requirement | Rule | Coverage |
|---|---|---|
| All sections present | `required_sections` | ✅ Full — missing section = error |
| No unfilled placeholders | `placeholders` | ✅ Full — leftover `df-todo` = error |
| No `[REPLACE]` text | `banned_words` | ✅ Full — literal match |
| Checklist steps exist | `match` per section | ⚠️ Partial — checks ≥1 match, not ALL items |
| Verification blocks exist | `match` per section | ⚠️ Partial — checks existence, not completeness |
| Evidence claims exist | `match` per section | ⚠️ Partial — spot check only |

## Changes

### 1. Create `.docfence/types/plan.toml`

```toml
name = "plan"
statuses = ["draft", "active", "frozen", "done"]
required_fields = ["id", "status", "owner"]

[defaults]
max_chars = 15000
banned_words = ["TODO", "TBD", "[REPLACE]"]
required_sections = [
    "Context",
    "Approach",
    "Steps",
    "Files to Modify",
    "Evidence Pack",
    "Verification",
    "Bottom Line",
    "Document Map",
]

[template_vars]
id = "PLAN-001"
title = "Plan Title"
owner = "human"

[template_vars.sections.Context]
fill = "[REPLACE] Why this change is needed — what problem does it solve?"

[template_vars.sections.Approach]
fill = "[REPLACE] Recommended approach and rationale — why this direction over alternatives?"

[template_vars.sections.Steps]
fill = "[REPLACE] Implementation steps as checklist items — delete this block and use - [ ] format"

[template_vars.sections."Files to Modify"]
fill = "[REPLACE] List of files to create, update, or delete — delete this block and write your list"

[template_vars.sections."Evidence Pack"]
fill = "[REPLACE] Claims with Source, Confidence, Implication — delete this block and follow Evidence Pack format"

[template_vars.sections.Verification]
fill = "[REPLACE] How to verify the change works — delete this block and write ### Test N blocks with commands"

[template_vars.sections."Bottom Line"]
fill = "[REPLACE] Per-step confidence, key risk, gaps, recommendation — delete this block and write your summary"

[template_vars.sections."Document Map"]
fill = "[REPLACE] File tree with CREATED/UPDATED/REFERENCED/DELETED markers — delete this block and write your map"
```

### 2. Section-level spec blocks need `match` rules

The scaffold generator produces per-section spec blocks. For the `plan` type, these blocks need `match` rules to enforce format patterns. Since section-level spec blocks in the scaffold inherit from `defaults`, we need to add `match` to either the type defaults or the section-level template.

**Option**: Add `match` to `defaults` in `plan.toml` so every section-level spec block inherits it:

```toml
[defaults]
# ... existing fields ...
match = [
    { step_checklist = "^- \\[\\]" },
    { test_block = "^### Test" },
    { evidence_claim = "\\*\\*Claim\\*\\*|\\*\\*Source\\*\\*" },
]
```

**Problem**: `match` is applied to sibling text of every section block. The `step_checklist` pattern would only make sense under `## Steps`, not under `## Context`. Two options:

- **Lenient**: Include `match` in defaults — every section is checked for all patterns. A section without the pattern reports a warning (not an error if the rule is advisory).
- **Targeted**: Don't put `match` in defaults. Instead, modify the scaffold generator to allow per-section overrides in `template_vars.sections.*.spec` — but this requires a code change (falls into Alternative B territory).

**For Alternative A**, go lenient: put `match` in defaults. Sections that legitimately lack the pattern will get `match` warnings, which is acceptable — the planner sees them and can ignore false positives for sections where the pattern doesn't apply. The critical enforcement (section presence, no placeholders) is handled by `required_sections` and `placeholders`.

### 3. Update planner prompt template

Add to `~/.pi/agent/prompts/planner.md` and `~/.pi/agent/agents/planner.md`:

```
## Plan format enforcement

1. Start every plan by running: `docfence new plan --output plans/<kebab-name>.md --set title="<title>" --set owner="<owner>"`
2. Research and fill the scaffolded sections — delete each ```df-todo block and replace with content
3. After writing, run: `docfence validate plans/<kebab-name>.md`
4. Fix any errors before declaring the plan complete
5. Re-validate until clean
```

### 4. Verify it works

```bash
# Scaffold a plan
docfence new plan --output /tmp/test-plan.md --set title="Test Plan"

# Validate the scaffold (should show placeholder errors + banned word [REPLACE])
docfence validate /tmp/test-plan.md

# Fill some sections, re-validate
# Confirm required_sections catches missing sections
# Confirm placeholders catches unfilled df-todo blocks
# Confirm banned_words catches [REPLACE]
```

## What This Does NOT Cover

- Can't enforce ALL list items are `- [ ]` (only checks ≥1 exists)
- Can't enforce verification blocks contain actual commands
- Can't enforce every Evidence Pack claim has Source/Confidence fields
- These gaps are addressed by Alternative B (`structure` rule)

## Files to Create/Modify

| File | Change |
|---|---|
| `.docfence/types/plan.toml` | New — type definition with required_sections, match, banned_words, template_vars |
| `~/.pi/agent/prompts/planner.md` | Add docfence enforcement instructions |
| `~/.pi/agent/agents/planner.md` | Add docfence enforcement instructions |