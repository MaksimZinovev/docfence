# speccheck

## What & Why

A tiny CLI that validates markdown spec docs against rules embedded _inside the doc itself_. AI assistants drift — they sneak in TODOs, break links, forget required sections, blow past length limits. `speccheck` catches issues before they compound. Requires Python 3.9+, no external dependencies.

> **Note:** Always run from the project root directory — `speccheck.py` resolves `core/` and `.speccheck/types/` relative to CWD.

## Quick Start

```bash
chmod +x speccheck.py
python speccheck.py new feature > docs/my-feature.md   # scaffold a doc
python speccheck.py validate docs/my-feature.md          # validate one file
python speccheck.py validate docs/                       # validate all .md in folder
python speccheck.py stamp docs/my-feature.md             # timestamp if clean
python speccheck.py types                                # list available types
```

## How it Works

<details>
<summary>📄 Sample doc file (bad-feature.md)</summary>

```markdown
---
id: F-002
type: feature
status: brainstorm
owner:
depends_on: []
last_validated: ~
---

# Data Export Feature

```spec
scope: document
type: feature
required_sections: [Overview, Implementation]
max_chars: 500
banned_words: [TODO, TBD]
```

## Overview

We want to let users export their data. TODO: figure out formats.
This is TBD for now.

## Implementation

```spec
type: feature
max_chars: 200
banned_words: [TODO, TBD]
```

We will build background jobs. TODO add progress tracking.
```

</details>

```bash
$ python speccheck.py validate sample-docs/bad-feature.md
ERR  bad-feature.md:1 — frontmatter missing required field 'owner' for type 'feature'
ERR  bad-feature.md:1 — status 'brainstorm' not valid for type 'feature' (allowed: draft, active, frozen, done)
ERR  bad-feature.md:4 — banned word 'TODO' found in content
ERR  bad-feature.md:4 — banned word 'TBD' found in content
ERR  bad-feature.md:18 — banned word 'TODO' found in content

$ python speccheck.py validate sample-docs/good-feature.md    # all rules pass
✓  1 file(s) clean — 2026-05-17T06:08:31+00:00

$ python speccheck.py stamp sample-docs/good-feature.md        # writes timestamp into frontmatter
✓  stamped sample-docs/good-feature.md — 2026-05-17T06:57:07+00:00

$ python speccheck.py types        # custom types from .speccheck/types/ override built-ins
Available doc types (from .speccheck/types/ + built-ins):
  exploration
  feature
```

## Structure

```
my-project/
├── speccheck.py              # CLI entry point
├── core/
│   ├── loader.py             # parses .md → frontmatter + spec blocks
│   ├── rules.py              # built-in rule functions
│   ├── types.py              # loads type definitions
│   └── validator.py          # orchestrates everything
├── .speccheck/types/         # drop a .toml to add a new doc type
│   ├── feature.toml
│   └── exploration.toml
└── docs/
    └── my-feature.md
```

## Doc Types

Built-in: `story` `task` `feature` `design` `exploration` `research` `persona` `pov` `brainstorm` `roadmap` `flow` `wireframe` `prototype` `test` `brand` `handoff`

Custom types in `.speccheck/types/mytype.toml` override the built-in list:

```toml
name = "mytype"
statuses = ["draft", "active", "done"]
required_fields = ["id", "status", "owner"]
[defaults]
max_chars = 1500
banned_words = ["TODO", "TBD"]
```

## Spec Block Syntax

**Section-level** — rules apply to the text that follows the block:

````markdown
```spec
type: feature
max_chars: 800
banned_words: [TODO, TBD, placeholder]
validate: [file_exists]
```
Your content here...
````

**Document-wide** (`scope: document`) — rules apply to the whole file:

````markdown
```spec
scope: document
type: feature
required_sections: [Overview, Acceptance Criteria]
max_chars: 5000
banned_words: [TBD]
```
````

## All Rules

| field                     | example                         | what it checks                                 |
| ------------------------- | ------------------------------- | ---------------------------------------------- |
| `max_chars`               | `max_chars: 800`                | sibling text must be shorter                   |
| `banned_words`            | `banned_words: [TODO, TBD]`     | none of these appear in sibling text           |
| `validate: [file_exists]` |                                 | every line in sibling text is a real path      |
| `validate: [valid_url]`   |                                 | every `http` line in sibling text is reachable |
| `required_sections`       | `required_sections: [Overview]` | document-scope only; heading must exist        |

## Frontmatter Fields

```yaml
---
id: F-001
type: feature
status: draft
owner: human          # human or ai — lets you apply stricter checks to AI content
depends_on: [D-001]
last_validated: ~     # written by `speccheck stamp`
---
```

## Warnings vs Errors

- **ERR** — rule violation; `stamp` is blocked until fixed
- **WARN** — e.g. inherited defaults from type definition not declared explicitly; not a blocker

## Block IDs

Each spec block gets a `bid` (8-char sha256 of its sibling text) computed at parse time. If content changes between runs the bid changes — useful for your AI agent to detect drift in sections it wrote.