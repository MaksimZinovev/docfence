# Minimal Focus Plan: Optional `hint` Field for df-todo Blocks

**Parent plan**: `plans/scaffold-df-todo.md`
**Scope**: Add an optional `hint` field to df-todo blocks and `template_vars.sections.*` for richer author guidance without bloating the `fill` string.

## Problem

The `fill` field does double duty: action instruction (`[REPLACE]...`) plus content guidance (`What was decided and why...`). For a "Decision" section, an example would significantly help the author — but adding it to `fill` creates an unreadably long string. There's no structured way to provide richer per-section guidance.

## Evidence

- **Claim**: Current df-todo block has exactly two fields: `name` and `fill`. No other fields are defined.
  **Source**: `docs/specs/scaffold-sample.md`; `plans/scaffold-df-todo.md` Step 7
  **Confidence**: 1.0

- **Claim**: `template_vars.sections.*` currently supports only `fill`. Extending with `hint` follows the same sub-table pattern used for `fill` and `max_chars`.
  **Source**: `plans/scaffold-df-todo.md` Step 3; `plans/per-section-max-chars.md` Step 1
  **Confidence**: 1.0

- **Claim**: `_parse_kv()` strips `#` comment lines from spec block text. A `hint` field in a df-todo block would be parsed as a normal key/value pair — no conflicts.
  **Source**: `core/loader.py:13` — `_parse_kv()`
  **Confidence**: 1.0

## Plan

### Step 1: Add `hint` to `template_vars.sections.*` in type TOML

```toml
[template_vars.sections.Decision]
fill = "[REPLACE] What was decided and why — delete this block and write your content"
hint = "Example: 'We chose SQLite over LevelDB because read latency matters more than write throughput for our read-heavy workload.'"

[template_vars.sections.Open Questions]
fill = "[REPLACE] List unresolved questions — delete this block and write your content"
hint = "Format: one bullet per question, e.g. '- What is the migration rollback plan?'"
```

`hint` is optional. Sections without it render a 2-field df-todo block (name + fill). Sections with it render a 3-field block.

### Step 2: Update `_generate_scaffold()` to conditionally emit `hint`

When building each section's df-todo block:

```python
lines = [f'name = "{section_name}"', f'fill = "{fill_text}"']
if hint_text := section_cfg.get("hint"):
    lines.append(f'hint = "{hint_text}"')
```

No change to the spec block or validation.

### Step 3: df-todo block output with hint

```markdown
## Decision

```df-todo
name = "decision"
fill = "[REPLACE] What was decided and why — delete this block and write your content"
hint = "Example: 'We chose SQLite over LevelDB because read latency matters more than write throughput.'"
```

```spec
type: exploration
max_chars: 2000
banned_words: [TODO, TBD]
placeholders: ["```df-todo"]
```
```

### Step 4: No validator changes

The `rule_placeholders` searches for the ````df-todo` fence pattern — it doesn't parse or validate the fields inside. Adding `hint` is purely an author-facing feature. No impact on validation logic.

## Verification

1. Add `hint` to `[template_vars.sections.Decision]` in exploration.toml
2. Run `docfence new exploration` → Decision section df-todo block shows `hint` field
3. Run `docfence new exploration` (other sections without `hint`) → their df-todo blocks have only `name` + `fill`

## Risk

- **Risk**: `hint` values contain quotes or special characters that break TOML parsing or the df-todo block formatting.
  **Mitigation**: Use TOML multi-line strings or escaping for complex hints. The generator should escape double quotes in hint values (`"` → `\"`).

- **Risk**: Authors copy the hint example verbatim instead of writing their own content, leading to repetitive docs.
  **Mitigation**: Hints are labeled "Example:" or "Format:" — they're clearly sample patterns, not templates to fill. The `banned_words` rule can catch exact hint text if it becomes a problem.

## Dependency on parent plan

Depends on Steps 3–4 (TypeDef `template_vars` + `_generate_scaffold()`) from `plans/scaffold-df-todo.md`.