# Minimal Focus Plan: Frontmatter Stub Detection

**Parent plan**: `plans/scaffold-df-todo.md`
**Scope**: Detect placeholder-like values in YAML frontmatter and report them as error-level issues.

## Problem

When `docfence new exploration` scaffolds a file, frontmatter gets default values like `owner: human` or `id: EXPLORATION-001`. These pass validation because they're non-empty (satisfying `required_fields`), but they're clearly stubs — the author hasn't customized them. The `placeholders` rule only catches ` ```df-todo ` blocks in the body, so frontmatter stubs go undetected.

## Evidence

- **Claim**: Frontmatter validation in `validate_doc()` only checks `required_fields` (non-empty presence) and `status` (allowed values). No check compares field values against known stub strings.
  **Source**: `core/validator.py:49` — frontmatter checks block
  **Confidence**: 1.0

- **Claim**: `TypeDef` has no field for declaring stub values. The scaffold generator hardcodes `owner: human` and `id: EXPLORATION-001` as defaults.
  **Source**: `core/types.py:12` — TypeDef dataclass; `docfence.py:258` — `_template()`
  **Confidence**: 1.0

- **Claim**: `rule_banned_words` only operates on `block.sibling_text`, not on frontmatter dict values.
  **Source**: `core/rules.py:21` — `rule_banned_words(text, value, cfg)`
  **Confidence**: 1.0

## Plan

### Step 1: Add `stubs` field to TypeDef + parse from TOML

Add `stubs: dict = field(default_factory=dict)` to `TypeDef`. In `load_types()`, parse `[stubs]` from TOML:

```toml
[stubs]
owner = "human"
id = "EXPLORATION-001"
```

This declares which frontmatter values are known stubs for a given type. Single source of truth alongside `template_vars`.

### Step 2: Add `rule_frontmatter_stubs` function to `core/rules.py`

```python
def rule_frontmatter_stubs(frontmatter: dict, stubs: dict, cfg: dict) -> list[str]:
    errors = []
    for field, stub_value in stubs.items():
        if frontmatter.get(field) == stub_value:
            errors.append(f"frontmatter field '{field}' still has stub value '{stub_value}' — replace with actual value")
    return errors
```

This is NOT a standard `RULES` entry — it takes `frontmatter` (dict) not `text` (str), so it can't use the spec-block execution path. It runs directly in `validate_doc()`.

### Step 3: Wire stub check into `validate_doc()`

In the frontmatter checks section of `validate_doc()`, after `required_fields` and `status` checks:

```python
if typedef and typedef.stubs:
    stub_errors = rule_frontmatter_stubs(doc.frontmatter, typedef.stubs, {})
    for msg in stub_errors:
        issues.append(Issue(doc.path, 1, "error", rule="stub", message=msg))
```

### Step 4: Add `[stubs]` to type TOML files

```toml
# .docfence/types/exploration.toml
[stubs]
owner = "human"
id = "EXPLORATION-001"
```

### Step 5: Update `_generate_scaffold()` to use `stubs` values as frontmatter defaults

The scaffold generator already uses `template_vars` for frontmatter values. Ensure `stubs` values match `template_vars` defaults — if `stubs.owner = "human"`, then `template_vars.owner = "human"`. The `[stubs]` section is the authoritative list of values the validator will flag.

## Verification

1. Scaffold a file: `docfence new exploration --output test.md`
2. Validate: `docfence validate test.md` → should report **stub errors** for `owner` and `id`
3. Edit frontmatter: change `owner: alice`, `id: EXP-042`
4. Validate again → stub errors gone

## Risk

- **Risk**: Stub values overlap with legitimate content (e.g., someone named "Human").
  **Mitigation**: Stubs are type-specific and declared in TOML — project maintainers control them. Use distinctive defaults like `"<owner>"` if name collisions are a concern.

## Dependency on parent plan

This plan depends on Step 3 (TypeDef `template_vars`) from `plans/scaffold-df-todo.md` being completed first, since `stubs` follows the same TypeDef extension pattern.