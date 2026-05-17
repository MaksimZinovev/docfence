# speccheck

## What

A tiny CLI that validates markdown spec docs against rules embedded directly
in the document. No external dependencies beyond Python 3.12. Drop it in your
project and your AI agent can use it immediately.

## Why

AI assistants drift. They sneak in TODOs, break links, forget required
sections, and blow past length limits. `speccheck` lets you define the rules
*inside the doc itself* — per section or for the whole document — and catch
issues before they compound.

## Quick Start

```bash
chmod +x speccheck.py

# scaffold a new doc
python speccheck.py new feature > docs/my-feature.md

# validate one file
python speccheck.py validate docs/my-feature.md

# validate a whole folder
python speccheck.py validate docs/

# stamp a clean file with a timestamp
python speccheck.py stamp docs/my-feature.md

# list available types
python speccheck.py types
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
├── .speccheck/
│   └── types/                # drop a .toml here to define a new doc type
│       ├── feature.toml
│       ├── exploration.toml
│       └── research.toml
└── docs/
    ├── exploration/
    │   └── E-001-market-research.md
    ├── design/
    │   └── D-001-user-flow.md
    └── tasks/
        └── T-001-auth.md
```

## Usage

```
speccheck validate <file|folder>   validate one file or all .md in folder
speccheck new <type>               print a blank template to stdout
speccheck types                    list all available types
speccheck stamp <file>             write last_validated timestamp (only if clean)
```

## Doc Types

Built-in: `story` `task` `feature` `design` `exploration` `research`
`persona` `pov` `brainstorm` `roadmap` `flow` `wireframe` `prototype`
`test` `brand` `handoff`

**Adding a new type** — create `.speccheck/types/mytype.toml`:

```toml
name = "mytype"
statuses = ["draft", "active", "done"]
required_fields = ["id", "status", "owner"]

[defaults]
max_chars = 1500
banned_words = ["TODO", "TBD"]
```

No core changes needed. `speccheck types` will pick it up automatically.

## Spec Block Syntax

Place ` ```spec ``` ` fences in your markdown to embed validation rules inline.

**Section-level block** — rules apply to the text that follows the block:

````markdown
```spec
type: feature
max_chars: 800
banned_words: [TODO, TBD, placeholder]
validate: [file_exists]
```

Your content here...
- src/auth/login.py
````

**Document-wide block** — rules apply to the whole file (put near the top):

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

| field | example | what it checks |
|---|---|---|
| `max_chars` | `max_chars: 800` | sibling text must be shorter |
| `banned_words` | `banned_words: [TODO, TBD]` | none of these appear in sibling text |
| `validate: [file_exists]` | | every line in sibling text is a real path |
| `validate: [valid_url]` | | every `http` line in sibling text is reachable |
| `required_sections` | `required_sections: [Overview]` | document-scope only; heading must exist |

## Frontmatter Fields

Every doc should start with:

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
- **WARN** — e.g. a spec block inherits rules from the type definition instead
  of declaring them explicitly; worth reviewing but not a blocker

## Block IDs

Each spec block gets a `bid` (8-char sha256 of its sibling text) computed at
parse time. If content changes between runs the bid changes — useful for your
AI agent to detect drift in sections it wrote.
