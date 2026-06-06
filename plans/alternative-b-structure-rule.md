# Alternative B: `structure` Rule — Strict Format Enforcement

## Background

Alternative A uses existing DocFence rules (`required_sections`, `match`, `placeholders`, `banned_words`) to enforce the plan format. It catches missing sections and leftover placeholders, but `match` only verifies that a pattern *exists somewhere* in the text — it can't enforce that *every* list item uses `- [ ]` format, or that *every* `### Test` block contains a command.

This gap means a planner can write `**Step 1:**` headers instead of `- [ ]` checklists and still pass validation. The `structure` rule closes this gap by enforcing patterns across all items in a section, not just spotting one match.

**Direction**: Add a `structure` rule to DocFence that checks structural patterns like "every list item must match X" or "every heading of type Y must contain Z". This builds on Alternative A — the `plan` doc type is still needed, but format enforcement becomes strict instead of lenient.

## What `structure` Does

The `structure` rule takes a list of structural constraints. Each constraint has a `scope` (which lines to apply to) and a `pattern` (what those lines must match). Lines that fall within the scope but don't match the pattern are reported as errors.

```toml
# In a section-level spec block:
structure:
  - scope: "list_items"     # lines starting with "- "
    pattern: "^- \\[\\]"    # must start with "- [ ]"
    message: "list items must use checkbox format (- [ ])"
  - scope: "code_blocks"    # lines inside ``` fences
    pattern: "\\$|>"         # must contain a shell prompt or command
    message: "verification blocks must contain runnable commands"
  - scope: "subheadings"    # lines starting with "### "
    pattern: "^### Test"     # must be a test block
    message: "subheadings under Verification must be ### Test blocks"
```

### Scope Types

| Scope | Matches lines that... | Example use |
|---|---|---|
| `list_items` | Start with `- ` | Checklist format enforcement |
| `subheadings` | Start with `### ` under the current section | Verification test blocks |
| `code_blocks` | Inside ``` fences under the current section | Commands in verification |
| `all` | Every non-blank line | Catch-all pattern |

### Error Output

```
L20 spec block (type: plan)
  ✗ structure: 3 list items don't match checklist format (- [ ])
  ✗ structure: 1 subheading not a test block (### Test N)
```

## Changes

### 1. Add `rule_structure` to `core/rules.py`

```python
def rule_structure(text: str, value: list[dict], cfg: dict) -> list[str]:
    """Enforce structural patterns on scoped subsets of text.

    value is a list of constraints, each with:
      scope: "list_items" | "subheadings" | "code_blocks" | "all"
      pattern: regex that each scoped line must match
      message: human-readable error (optional)
    """
    errors = []
    lines = text.splitlines()
    for constraint in value:
        scope = constraint.get("scope", "all")
        pattern = constraint.get("pattern", "")
        message = constraint.get("message", f"structure rule violated: {scope} must match /{pattern}/")

        compiled = re.compile(pattern)

        # Extract the scoped lines
        scoped = _extract_scope(lines, scope)

        # Check each scoped line matches the pattern
        violations = [line for line in scoped if not compiled.search(line)]
        if violations:
            count = len(violations)
            errors.append(f"{count} {scope} don't match: {message}")
    return errors


def _extract_scope(lines: list[str], scope: str) -> list[str]:
    """Extract lines matching a structural scope."""
    if scope == "list_items":
        return [l for l in lines if l.lstrip().startswith("- ") and not l.lstrip().startswith("- [")]
    elif scope == "subheadings":
        return [l for l in lines if l.lstrip().startswith("### ")]
    elif scope == "code_blocks":
        # Extract lines inside ``` fences
        inside = False
        block_lines = []
        for l in lines:
            if l.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                block_lines.append(l)
        return block_lines
    elif scope == "all":
        return [l for l in lines if l.strip()]
    return []
```

**Wait** — re-reading the requirement more carefully. `structure` with `scope: "list_items"` should catch lines that ARE list items (start with `- `) but DON'T match the pattern. The implementation above has the scope extraction and the pattern check merged. Let me simplify:

```python
def rule_structure(text: str, value: list[dict], cfg: dict) -> list[str]:
    """Enforce structural patterns on scoped subsets of text."""
    errors = []
    lines = text.splitlines()

    for constraint in value:
        scope = constraint.get("scope", "all")
        pattern = constraint.get("pattern", "")
        message = constraint.get("message", f"structure: {scope} must match /{pattern}/")

        compiled = re.compile(pattern)
        scoped_lines = _extract_scope(lines, scope)

        # Lines in scope that DON'T match the pattern
        violations = [l for l in scoped_lines if not compiled.search(l)]
        if violations:
            errors.append(f"{len(violations)} {message}")

    return errors


def _extract_scope(lines: list[str], scope: str) -> list[str]:
    """Return lines that fall within a structural scope."""
    if scope == "list_items":
        # Lines starting with "- " (already list items)
        return [l for l in lines if l.lstrip().startswith("- ")]
    elif scope == "subheadings":
        return [l for l in lines if l.lstrip().startswith("### ")]
    elif scope == "code_blocks":
        inside = False
        result = []
        for l in lines:
            if l.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                result.append(l)
        return result
    else:  # "all"
        return [l for l in lines if l.strip()]
```

**Key insight**: `_extract_scope("list_items")` returns lines starting with `- `. The `pattern: "^- \\[\\]"` then checks that each of those lines also starts with `- [ ]`. If a line starts with `- ` but NOT `- [ ]`, it's a violation. This correctly enforces "all list items must be checkboxes."

For `scope: "subheadings"`, it returns `### ` lines, and `pattern: "^### Test"` requires each to be a test heading.

### 2. Register in `RULES` dict

```python
RULES: dict[str, callable] = {
    "max_chars": rule_max_chars,
    "banned_words": rule_banned_words,
    "validate": rule_validate,
    "required_sections": rule_required_sections,
    "match": rule_match,
    "placeholders": rule_placeholders,
    "structure": rule_structure,  # NEW
}
```

### 3. Update `.docfence/types/plan.toml`

Same as Alternative A, plus add `structure` to section-level defaults:

```toml
[defaults]
max_chars = 15000
banned_words = ["TODO", "TBD", "[REPLACE]"]
required_sections = [
    "Context", "Approach", "Steps", "Files to Modify",
    "Evidence Pack", "Verification", "Bottom Line", "Document Map",
]
match = [
    { step_checklist = "^- \\[\\]" },
    { test_block = "^### Test" },
]
structure = [
    { scope = "list_items", pattern = "^- \\[\\]", message = "list items must use checkbox format (- [ ])" },
]
```

**Note**: `structure` and `match` overlap here — `match` checks that ≥1 `- [ ]` exists (lenient), `structure` checks that ALL list items are `- [ ]` (strict). Both are useful: `match` in sections without list items (like Context) provides a gentle nudge; `structure` provides hard enforcement in sections with lists.

### 4. Add tests for `rule_structure`

Create `tests/test_structure.py`:

```python
from core.rules import rule_structure

def test_checklist_format():
    text = "- [ ] Step one\n- [ ] Step two\n- Step three"
    errors = rule_structure(text, [
        {"scope": "list_items", "pattern": "^- \\[\\]", "message": "must use checkbox format"}
    ], {})
    assert len(errors) == 1
    assert "1 must use checkbox format" in errors[0]

def test_all_list_items_pass():
    text = "- [ ] Step one\n- [ ] Step two"
    errors = rule_structure(text, [
        {"scope": "list_items", "pattern": "^- \\[\\]", "message": "must use checkbox format"}
    ], {})
    assert errors == []

def test_subheadings_scope():
    text = "### Test 1\n### Test 2\n### Random heading"
    errors = rule_structure(text, [
        {"scope": "subheadings", "pattern": "^### Test", "message": "must be test blocks"}
    ], {})
    assert len(errors) == 1  ### Random heading fails

def test_code_blocks_scope():
    text = "```\ncd /tmp\nls\nnot a command outside\n```"
    errors = rule_structure(text, [
        {"scope": "code_blocks", "pattern": "\\$|>", "message": "must contain commands"}
    ], {})
    assert len(errors) >= 1
```

## What This Adds Over Alternative A

| Feature | Alternative A | Alternative B |
|---|---|---|
| Missing sections | ✅ `required_sections` | ✅ Same |
| Leftover placeholders | ✅ `placeholders` | ✅ Same |
| Banned words | ✅ `banned_words` | ✅ Same |
| Pattern exists (≥1 match) | ✅ `match` | ✅ Same |
| ALL list items are `- [ ]` | ❌ | ✅ `structure` |
| ALL subheadings are test blocks | ❌ | ✅ `structure` |
| Code blocks contain commands | ❌ | ✅ `structure` |

## Files to Create/Modify

| File | Change |
|---|---|
| `core/rules.py` | Add `rule_structure` + `_extract_scope` + register in `RULES` |
| `.docfence/types/plan.toml` | New — type definition with `structure` constraints |
| `tests/test_structure.py` | New — unit tests for the structure rule |
| `~/.pi/agent/prompts/planner.md` | Add docfence enforcement instructions |
| `~/.pi/agent/agents/planner.md` | Add docfence enforcement instructions |

## Risk

The `structure` rule is more complex than existing rules. The `scope` extraction logic needs careful testing, especially for `code_blocks` (tracking fence open/close state). But the implementation is ~40 lines of Python, and the rule follows the same `(text, value, cfg) → list[str]` contract as all other rules.