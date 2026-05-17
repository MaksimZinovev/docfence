# Docfence

**Validate markdown specs from the inside out.**

```bash
██████╗  ██████╗  ██████╗███████╗███████╗███╗   ██╗ ██████╗███████╗
██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝████╗  ██║██╔════╝██╔════╝
██║  ██║██║   ██║██║     █████╗  █████╗  ██╔██╗ ██║██║     █████╗  
██║  ██║██║   ██║██║     ██╔══╝  ██╔══╝  ██║╚██╗██║██║     ██╔══╝  
██████╔╝╚██████╔╝╚██████╗██║     ███████╗██║ ╚████║╚██████╗███████╗
╚═════╝  ╚═════╝  ╚═════╝╚═╝     ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
```

[What](#what) • [Quick Start](#quick-start) • [Usage](#usage) • [Rules](#all-rules) • [Types](#doc-types) • [Structure](#structure)

---

## What

A tiny CLI that validates markdown spec docs against rules embedded directly
in the document. Requires Python 3.9+ (uses `list[str]` type hints). No external
dependencies. Drop it in your project and your AI agent can use it immediately.

## Why

AI assistants drift. They sneak in TODOs, break links, forget required
sections, and blow past length limits. `docfence` lets you define the rules
_inside the doc itself_ — per section or for the whole document — and catch
issues before they compound.

## Quick Start

```bash
chmod +x docfence.py

# scaffold a new doc
python docfence.py new feature > docs/my-feature.md

# validate one file
python docfence.py validate docs/my-feature.md

# validate a whole folder
python docfence.py validate docs/

# stamp a clean file with a timestamp
python docfence.py stamp docs/my-feature.md

# list available types
python docfence.py types
```

> **Note:** Always run from the project root directory. `docfence.py` resolves
> `core/` and `.docfence/types/` relative to the working directory.

## How it Works

<details>
<summary>📄 See sample doc — bad-feature.md (has errors)</summary>

````markdown
---
id: F-002
type: feature
status: brainstorm
owner:
depends_on: []
last_validated: ~
---

```spec
scope: document
type: feature
required_sections: [Overview, Implementation]
max_chars: 500
banned_words: [TODO, TBD]
```

We want to let users export data. TODO: figure out formats. TBD for now.

```spec
type: feature
max_chars: 200
banned_words: [TODO, TBD]
```

We will build background jobs. TODO add progress tracking.
````

</details>

```bash
$ python docfence.py validate sample-docs/

sample-docs/
├── ✗ bad-feature.md
│   ├── L1 frontmatter (type: feature)
│   │   ├── ✗ frontmatter: missing required field 'owner'
│   │   └── ✗ status: 'brainstorm' not valid → allowed: draft, active, frozen, done
│   ├── L4 spec block (type: feature, scope: document)
│   │   ├── ✗ banned_words: 'TODO' found in content
│   │   └── ✗ banned_words: 'TBD' found in content
│   └── L18 spec block (type: feature)
│       └── ✗ banned_words: 'TODO' found in content
├── ✓ exploration-auth.md
├── ✓ good-feature.md
└── ⚠ test-match.md
    └── L18 spec block (type: feature)
        └── ⚠ inherited: uses inherited defaults for banned_words

4 files  5 errors  1 warning
```

## Structure

```shell
my-project/
├── docfence.py              # CLI entry point
├── core/
│   ├── loader.py             # parses .md → frontmatter + spec blocks
│   ├── rules.py              # built-in rule functions
│   ├── types.py              # loads type definitions
│   └── validator.py          # orchestrates everything
├── .docfence/
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

```shell
docfence validate <file|folder>     # validate one file or all .md in folder
docfence new <type>                 # print a blank template to stdout
docfence types                      # list all available types
docfence stamp <file>               # write last_validated timestamp (only if clean)
```

## Doc Types

Built-in: `story` `task` `feature` `design` `exploration` `research`
`persona` `pov` `brainstorm` `roadmap` `flow` `wireframe` `prototype`
`test` `brand` `handoff`

**Adding a new type** — create `.docfence/types/mytype.toml`:

```toml
name = "mytype"
statuses = ["draft", "active", "done"]
required_fields = ["id", "status", "owner"]

[defaults]
max_chars = 1500
banned_words = ["TODO", "TBD"]
```

No core changes needed. `docfence types` will pick it up automatically.
When custom types exist, built-in fallback types are hidden — only your
`.docfence/types/` definitions are listed.

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

| field                     | example                              | what it checks                                 |
| ------------------------- | ------------------------------------ | ---------------------------------------------- |
| `max_chars`               | `max_chars: 800`                     | sibling text must be shorter                   |
| `banned_words`            | `banned_words: [TODO, TBD]`          | none of these appear in sibling text           |
| `match`                   | `match:` + indented `label: "regex"` | at least one line matches each named pattern   |
| `validate: [file_exists]` |                                      | every line in sibling text is a real path      |
| `validate: [valid_url]`   |                                      | every `http` line in sibling text is reachable |
| `required_sections`       | `required_sections: [Overview]`      | document-scope only; heading must exist        |

**`match` example:**

````markdown
```spec
type: feature
max_chars: 1000
match:
  data_point: "^\\- .{30,}$"
  source_link: "Source: https?://.+"
```
````

Each `label: pattern` entry must match at least one line in the sibling text.
Use `(?i)` prefix for case-insensitive matching. Errors reference the label,
making them readable in AI agent output.

## Frontmatter Fields

Every doc should start with:

```yaml
---
id: F-001
type: feature
status: draft
owner: human # human or ai — lets you apply stricter checks to AI content
depends_on: [D-001]
last_validated: ~ # written by `docfence stamp`
---
```

## Warnings vs Errors

- **✗ ERR** — rule violation; `stamp` is blocked until fixed
- **⚠ WARN** — e.g. a spec block inherits rules from the type definition instead
  of declaring them explicitly; worth reviewing but not a blocker

## Block IDs

Each spec block gets a `bid` (8-char sha256 of its sibling text) computed at
parse time. If content changes between runs the bid changes — useful for your
AI agent to detect drift in sections it wrote.
