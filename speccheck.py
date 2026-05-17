#!/usr/bin/env python3
"""
speccheck — validate markdown spec docs with inline and type-level rules.

Usage examples:
  speccheck validate notes/my-feature.md     # validate one file
  speccheck validate docs/                   # validate all .md in folder
  speccheck new feature                      # print a blank template
  speccheck types                            # list all known doc types
  speccheck stamp docs/my-feature.md         # write last_validated timestamp

Spec block syntax (place inside ```spec ... ``` fences in your .md):

  ```spec
  type: feature
  status: draft
  owner: human
  max_chars: 800
  banned_words: [TODO, TBD, placeholder]
  validate: [file_exists, valid_url]
  ```

Document-wide spec block (applies rules to the whole file):

  ```spec
  scope: document
  type: exploration
  required_sections: [Background, Decision, Open Questions]
  max_chars: 5000
  ```

Type definitions live in .speccheck/types/<name>.toml — drop a new file to add
a type without touching speccheck core.
"""

import sys
import re
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from core.loader import load_doc
from core.types import load_types
from core.validator import validate_path, Issue

# ── templates ────────────────────────────────────────────────────────────────

def _load_types_list(start: Path) -> list[str]:
    registry = load_types(start)
    return sorted(registry.keys()) if registry else [
        "story", "task", "feature", "design", "exploration",
        "research", "persona", "pov", "brainstorm", "roadmap",
        "flow", "wireframe", "prototype", "test", "brand", "handoff",
    ]

def _template(doc_type: str) -> str:
    return f"""\
---
id: {doc_type[0].upper()}-001
type: {doc_type}
status: draft
owner: human
depends_on: []
last_validated: ~
---

# Title

```spec
scope: document
type: {doc_type}
required_sections: [Overview]
max_chars: 3000
banned_words: [TODO, TBD, placeholder]
```

## Overview

```spec
type: {doc_type}
max_chars: 1000
banned_words: [TODO, TBD, placeholder]
```

Your content here.
"""

# ── commands ─────────────────────────────────────────────────────────────────

def cmd_validate(target: str):
    p = Path(target)
    if not p.exists():
        print(f"ERR  path not found: {target}")
        sys.exit(1)
    issues = validate_path(p)
    errors = [i for i in issues if i.level == "error"]
    warns  = [i for i in issues if i.level == "warn"]
    for i in warns:
        print(i)
    for i in errors:
        print(i)
    if not issues:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        files = list(p.rglob("*.md")) if p.is_dir() else [p]
        print(f"✓  {len(files)} file(s) clean — {ts}")
    elif not errors:
        print(f"✓  {len(warns)} warning(s), no errors")
    else:
        sys.exit(1)


def cmd_new(doc_type: str):
    known = _load_types_list(Path.cwd())
    if doc_type not in known:
        print(f"Unknown type '{doc_type}'. Run: speccheck types")
        sys.exit(1)
    print(_template(doc_type))


def cmd_types():
    known = _load_types_list(Path.cwd())
    print("Available doc types (from .speccheck/types/ + built-ins):\n")
    for t in known:
        print(f"  {t}")


def cmd_stamp(target: str):
    p = Path(target)
    if not p.exists():
        print(f"ERR  file not found: {target}")
        sys.exit(1)
    issues = validate_path(p)
    errors = [i for i in issues if i.level == "error"]
    if errors:
        print("Cannot stamp — errors must be resolved first:")
        for e in errors:
            print(e)
        sys.exit(1)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    text = p.read_text()
    text = re.sub(r"last_validated:.*", f"last_validated: {ts}", text)
    p.write_text(text)
    print(f"✓  stamped {p} — {ts}")


# ── entry ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    match args:
        case ["validate", target]:
            cmd_validate(target)
        case ["new", doc_type]:
            cmd_new(doc_type)
        case ["types"]:
            cmd_types()
        case ["stamp", target]:
            cmd_stamp(target)
        case _:
            print(__doc__)

if __name__ == "__main__":
    main()
