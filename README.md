# docfence

**Validate markdown specs from the inside out.**

```bash
██████╗  ██████╗  ██████╗███████╗███████╗███╗   ██╗ ██████╗███████╗
██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝████╗  ██║██╔════╝██╔════╝
██║  ██║██║   ██║██║     █████╗  █████╗  ██╔██╗ ██║██║     █████╗
██║  ██║██║   ██║██║     ██╔══╝  ██╔══╝  ██║╚██╗██║██║     ██╔══╝
██████╔╝╚██████╔╝╚██████╗██║     ███████╗██║ ╚████║╚██████╗███████╗
╚═════╝  ╚═════╝  ╚═════╝╚═╝     ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
```

[What](#what) • [Install](#install) • [Quick Start](#quick-start) • [Usage](#usage) • [Rules](#all-rules) • [Types](#doc-types)

---

## What

A tiny CLI that validates markdown spec docs against rules embedded directly
in the document. No external dependencies. Drop it in your project and your AI
agent can use it immediately.

## Why

AI assistants drift. They sneak in TODOs, break links, forget required
sections, and blow past length limits. `docfence` lets you define the rules
_inside the doc itself_ — per section or for the whole document — and catch
issues before they compound.

## Install

```bash
pip install -e .
```

After that, `docfence` is available globally — run it from any folder.

## Quick Start

```bash
# scaffold a new doc
docfence new feature > docs/my-feature.md

# validate one file
docfence validate docs/my-feature.md

# validate a whole folder
docfence validate docs/

# stamp a clean file with a timestamp
docfence stamp docs/my-feature.md

# list available types
docfence types
```

> **Note:** `docfence` looks for `.docfence/types/` relative to the target
> path. Run `validate` from your project root so type definitions are found.

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
$ docfence validate sample-docs/
#              ↑ run on a folder to validate all .md files inside

sample-docs/                                   									# ← folder root
├── ✗ bad-feature.md                           									# ✗ = has errors (stamp blocked)
│   ├── L1 frontmatter (type: feature)         									# ← L1 = line 1; frontmatter checks come from the type definition
│   │   ├── ✗ frontmatter: missing required field 'owner'       # 'owner' is required_fields in the type .toml
│   │   └── ✗ status: 'brainstorm' not valid → allowed: draft, active, frozen, done  # status must be in type's statuses list
│   ├── L4 spec block (type: feature, scope: document)           # ← L4 = line 4; scope: document = rules apply to whole file
│   │   ├── ✗ banned_words: 'TODO' found in content              # banned_words rule caught 'TODO' in the document body
│   │   └── ✗ banned_words: 'TBD' found in content               # same rule, second hit — each banned word is a separate issue
│   └── L18 spec block (type: feature)         # ← no scope = section-level; rules only apply to text after this fence
│       └── ✗ banned_words: 'TODO' found in content
├── ✓ exploration-auth.md                       # ✓ = clean, no issues found
├── ✓ good-feature.md
└── ⚠ test-match.md                           # ⚠ = warnings only (non-blocking)
    └── L18 spec block (type: feature)
        └── ⚠ inherited: uses inherited defaults for banned_words  # rule wasn't set in the block; fell back to type defaults

4 files  5 errors  1 warning                    # ← summary: errors block stamp, warnings are advisory
```

## Usage

```shell
docfence validate <file|folder>         # validate one file or all .md in folder
docfence validate <file|folder> --verbose  # show passing checks + section headings
docfence new <type>                       # print a blank template to stdout
docfence types                             # list all available types
docfence stamp <file>                      # write last_validated timestamp (only if clean)
```

## Verbose Mode

Pass `--verbose` to see passing checks and section headings. → [VERBOSE.md](VERBOSE.md)

## Doc Types

Built-in fallback: `story` `task` `feature` `design` `exploration` `research`
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

## Spec Block Syntax

Place ` ```spec ``` ` fences in your markdown to embed validation rules inline.

**Section-level** — rules apply to the text that follows the block:

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

**Document-wide** — rules apply to the whole file (put near the top):

````markdown
```spec
scope: document
type: feature
required_sections: [Overview, Acceptance Criteria]
max_chars: 5000
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

Each `label: pattern` entry must match at least one line. Use `(?i)` for
case-insensitive matching. Errors reference the label, not the raw regex.

## Warnings vs Errors

- **✗ ERR** — rule violation; `stamp` is blocked until fixed
- **⚠ WARN** — inherited defaults or unknown type; worth reviewing, not a blocker

## Block IDs

Each spec block gets a `bid` (8-char sha256 of its sibling text). If content
changes between runs, the bid changes — useful for AI agents to detect drift.
