# Plan: Scaffold Markdown with Jinja2-Style Placeholders

## Goal

Replace the hardcoded `_template()` dump with a proper scaffolding system that generates
Markdown files using **Jinja2-style `{{ placeholder }}` syntax**, includes **one-line
fill instructions** inside each placeholder, and wires unfilled placeholders into
docfence validation as **error-level issues**. All existing rules (banned_words,
required_sections, max_chars, match, validate) are embedded in the scaffolded file
via spec blocks so the document is immediately validate-able.

---

## 1. Template files

### 1.1 Bundled templates (package)

Create `templates/` at project root with one `.j2` file per built-in doc type.
Each template uses `{{ placeholder }}` syntax and includes a hint comment.

**`templates/feature.j2`** (example):

```markdown
---
id: {{ id | default("FEATURE-001") }}
type: {{ type }}
status: {{ status | default("draft") }}
owner: {{ owner | default("<your-name>") }}
depends_on: []
last_validated: ~
---

# {{ title | default("Feature Title") }}

<!-- Fill in: a short human-readable title for this feature -->

```spec
scope: document
type: {{ type }}
required_sections: [Overview]
max_chars: {{ max_chars | default(3000) }}
banned_words: {{ banned_words | default(["TODO", "TBD", "placeholder"]) }}
```

## Overview

<!-- Fill in: 1--3 paragraphs describing the feature -->

```spec
type: {{ type }}
max_chars: {{ max_chars | default(1000) }}
banned_words: {{ banned_words | default(["TODO", "TBD", "placeholder"]) }}
```

{{ overview | default("") }}
```

### 1.2 User overrides (`.docfence/templates/`)

Same `.j2` format. Users drop files into `.docfence/templates/<name>.j2`.
At scaffold time, the lookup order is:

1. `.docfence/templates/<type>.j2` (user override)
2. `<package>/templates/<type>.j2` (bundled default)

If neither exists, fall back to the current `_template()` behaviour.

### 1.3 TypeDef TOML additions

Add optional keys to `.docfence/types/*.toml`:

```toml
[template_vars]
id = "FEATURE-001"
title = "Feature Title"
overview = ""
```

These feed default values into the Jinja2 render context, so users don't
have to pass `--set` for every field.

---

## 2. CLI changes (`docfence.py`)

### 2.1 New subcommand signature

```
docfence new <type> [--template <name>] [--set key=value ...] [--output <path>]
```

| Flag | Purpose |
|------|---------|
| `<type>` | doc type (existing behaviour) |
| `--template <name>` | use a specific template file (skip type→filename mapping) |
| `--set key=value` | override / fill template variables (repeatable) |
| `--output <path>` | write to file instead of stdout |

### 2.2 Implementation (`cmd_new` refactor)

```python
def cmd_new(doc_type: str, template_name: str | None = None,
            overrides: dict | None = None, output: str | None = None):
    # 1. Locate template (.docfence/templates/ → bundled → fallback)
    # 2. Load TypeDef → merge template_vars as render context
    # 3. Apply --set overrides on top
    # 4. Render with Jinja2 (use Jinja2's native env with undefined=DebugUndefined)
    # 5. Write to --output path or stdout
```

Dependency: add `jinja2` to requirements. (Lightweight, std in Python tooling.)

### 2.3 Argument parsing in `main()`

Replace the raw `match args` block with `argparse` subcommands so `--set`,
`--template`, `--output` are properly parsed. This is a minimal change — only
the `new` subcommand gains extra flags; all other subcommands keep positional args.

---

## 3. Placeholder validation rule

### 3.1 New rule: `rule_placeholders`

File: `core/rules.py`

```python
def rule_placeholders(text: str, value: list[str], cfg: dict) -> list[str]:
    """Detect unfilled {{ ... }} placeholders in content.
    
    value: list of regex patterns to match (default: [r'\{\{\s*\w+.*?\}\}'])
    """
    errors = []
    for pattern in value:
        matches = re.findall(pattern, text)
        for m in matches:
            errors.append(f"unfilled placeholder '{m.strip()}' found")
    return errors
```

Register it:

```python
RULES["placeholders"] = rule_placeholders
```

### 3.2 Default pattern in type configs

Add `placeholders` to type defaults so it's enforced automatically:

```toml
[defaults]
placeholders = ["\\{\\{\\s*\\w+.*?\\}\\}"]
```

Or more conservatively, hardcode a sensible default pattern when the rule
is invoked without an explicit value (like we do for other defaults via
TypeDef).

### 3.3 Include in scaffolded file

The document-level spec block in every template includes:

````
```spec
scope: document
type: {{ type }}
...
placeholders: [{{ '{{' }}\\s*\\w+.*?{{ '}}' }}]
```
````

So a freshly scaffolded file with unfilled `{{ }}` tokens will fail validation
with a clear error message. Once the author replaces every placeholder,
the rule passes.

---

## 4. Validation instructions embedded in scaffolded output

Every placeholder gets an inline HTML comment above it:

```markdown
<!-- Fill in: brief instruction for what goes here -->
{{ owner | default("<your-name>") }}
```

For section bodies, a comment at the top of the section:

```markdown
## Decision
<!-- Fill in: Describe the decision made and rationale -->
{{ decision | default("") }}
```

These are **not** checked by the validator (HTML comments are outside sibling text
for spec blocks) — they exist purely as author guidance.

---

## 5. File-by-file change summary

| File | Change |
|------|--------|
| `templates/*.j2` | **New** — bundled Jinja2 templates (feature, exploration, story, adr, etc.) |
| `core/rules.py` | Add `rule_placeholders` fn + register in `RULES` dict |
| `core/types.py` | Add `template_vars: dict` field to `TypeDef` + parse from TOML |
| `docfence.py` | Refactor `cmd_new` → accepts `--template`, `--set`, `--output`; add `_resolve_template()`, `_render_template()` helpers; update `main()` parser |
| `.docfence/types/*.toml` | Add `[template_vars]` section + `placeholders` default |
| `requirements.txt` / `pyproject.toml` | Add `jinja2` dependency |
| `_template()` | **Remove** — replaced by template files + renderer |

---

## 6. Out of scope (future work)

- `docfence template list` / `docfence template show` commands (low priority)
- Template validation (schema for .j2 files)
- Interactive prompting (fill placeholders via CLI prompts)
- Converting `{{ }}` placeholders to a `rule_match` variant (separate rule is clearer)

---

## 7. Risk / mitigations

| Risk | Mitigation |
|------|-----------|
| Jinja2 not installed | Pin `jinja2>=3.1` in deps; fail with clear message if missing |
| Escaping `{{ }}` inside spec block's `placeholders` value is fiddly | Use Jinja2 raw blocks `{% raw %}...{% endraw %}` or string concatenation for the regex pattern |
| Breaking existing `docfence new <type>` | Keep as drop-in: `docfence new feature` still works; new flags are optional |
| User templates with invalid Jinja2 syntax | Catch `TemplateSyntaxError` and print helpful message with file path |