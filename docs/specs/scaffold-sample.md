# Sample Type Configuration

This is the TOML file that lives at `.docfence/types/exploration.toml`.
It drives both validation rules AND scaffold generation for the `exploration` doc type.

```toml
name = "exploration"
statuses = ["draft", "active", "frozen", "done"]
required_fields = ["id", "status", "owner"]

[defaults]
max_chars = 5000
banned_words = ["TODO", "TBD"]
required_sections = ["Background", "Decision", "Open Questions"]

[template_vars]
id = "EXPLORATION-001"
title = "Exploration Title"
owner = "human"

[template_vars.sections.Background]
fill = "[REPLACE] Why this exploration is needed — delete this block and write your content"

[template_vars.sections.Decision]
fill = "[REPLACE] What was decided and why, including alternatives considered — delete this block and write your content"

[template_vars.sections."Open Questions"]
fill = "[REPLACE] List unresolved questions or items needing further investigation — delete this block and write your content"
```

**Note**: `placeholders` is NOT in `[defaults]` — it's a document-scope-only rule.
The scaffold generator adds `placeholders: ["```df-todo"]` to the document-level spec block explicitly.

---

# Sample Scaffolded Output

This is the Markdown file produced by `docfence new exploration`.

## Default output (no overrides)

````markdown
---
id: EXPLORATION-001
type: exploration
status: draft
owner: human
depends_on: []
last_validated: ~
---

# Exploration Title

```spec
scope: document
type: exploration
required_sections: [Background, Decision, Open Questions]
max_chars: 5000
banned_words: [TODO, TBD]
placeholders: ["```df-todo"]
```

## Background

```df-todo
name = "background"
fill = "[REPLACE] Why this exploration is needed — delete this block and write your content"
```

```spec
type: exploration
max_chars: 5000
banned_words: [TODO, TBD]
```

## Decision

```df-todo
name = "decision"
fill = "[REPLACE] What was decided and why, including alternatives considered — delete this block and write your content"
```

```spec
type: exploration
max_chars: 5000
banned_words: [TODO, TBD]
```

## Open Questions

```df-todo
name = "open-questions"
fill = "[REPLACE] List unresolved questions or items needing further investigation — delete this block and write your content"
```

```spec
type: exploration
max_chars: 5000
banned_words: [TODO, TBD]
```
````

## With overrides

```bash
docfence new exploration --output docs/exp-001.md --set owner=alice --set title="Database Migration Strategy"
```

````markdown
---
id: EXPLORATION-001
type: exploration
status: draft
owner: alice
depends_on: []
last_validated: ~
---

# Database Migration Strategy

```spec
scope: document
type: exploration
required_sections: [Background, Decision, Open Questions]
max_chars: 5000
banned_words: [TODO, TBD]
placeholders: ["```df-todo"]
```

## Background

```df-todo
name = "background"
fill = "[REPLACE] Why this exploration is needed — delete this block and write your content"
```

```spec
type: exploration
max_chars: 5000
banned_words: [TODO, TBD]
```

## Decision

```df-todo
name = "decision"
fill = "[REPLACE] What was decided and why, including alternatives considered — delete this block and write your content"
```

```spec
type: exploration
max_chars: 5000
banned_words: [TODO, TBD]
```

## Open Questions

```df-todo
name = "open-questions"
fill = "[REPLACE] List unresolved questions or items needing further investigation — delete this block and write your content"
```

```spec
type: exploration
max_chars: 5000
banned_words: [TODO, TBD]
```
````

---

# Author workflow

1. Run `docfence new exploration --output docs/exp-001.md`
2. Run `docfence validate docs/exp-001.md` → **3 placeholder errors** (one per `df-todo` block) + `banned_words` false positive on "df-todo" fence name (clears when df-todo blocks are removed)
3. For each section: delete the ` ```df-todo ` block, write content below the ` ```spec ` block
4. Run `docfence validate docs/exp-001.md` → **clean** (no placeholders, section rules pass)

---

# Key design decisions in implementation

- **`placeholders` is document-scope only**: Not in type TOML `[defaults]`; scaffold generator adds it explicitly to the document-level spec block. This prevents section-level spec blocks from inheriting it and flagging df-todo blocks in other sections' sibling text.
- **Section-level spec blocks inherit `max_chars` from type defaults**: Currently uses the same value as document-level (5000). Per-section max_chars is a future enhancement (see `plans/per-section-max-chars.md`).
- **Spec block regex fix**: Closing fence must be on its own line (`\n\`\`\`\s*\n`) to prevent false matches on three backticks inside spec block values like `placeholders: ["\`\`\`df-todo"]`.