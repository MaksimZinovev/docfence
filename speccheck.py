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

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.loader import load_doc
from core.types import load_types
from core.validator import validate_path, Issue

# ── colors ───────────────────────────────────────────────────────────────────

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BOLD = "\033[1m"
RESET = "\033[0m"

_use_color = sys.stdout.isatty()


def c(text: str, *codes: str) -> str:
    if not _use_color:
        return text
    return "".join(codes) + text + RESET


# ── tree renderer ─────────────────────────────────────────────────────────────


def _render_tree(issues: list[Issue], target: Path):
    """Render issues as a tree grouped by file, then source (frontmatter / spec block)."""
    files = list(target.rglob("*.md")) if target.is_dir() else [target]
    errors = [i for i in issues if i.level == "error"]
    warns = [i for i in issues if i.level == "warn"]

    # group issues by file
    by_file: dict[Path, list[Issue]] = {}
    for i in issues:
        by_file.setdefault(i.path, []).append(i)

    # find the common parent to display as root
    if target.is_dir():
        prefix = target.name + "/"
    else:
        prefix = str(target.parent.name) + "/" if target.parent else ""

    # collect file order: validated files that have no issues too
    ordered_files = []
    for f in sorted(files):
        ordered_files.append(f)

    lines = []
    if prefix:
        lines.append(prefix)

    for idx, fpath in enumerate(ordered_files):
        is_last_file = idx == len(ordered_files) - 1
        file_issues = by_file.get(fpath, [])
        file_errors = [i for i in file_issues if i.level == "error"]
        file_warns = [i for i in file_issues if i.level == "warn"]

        if file_errors:
            tag = c("✗", RED, BOLD)
        elif file_warns:
            tag = c("⚠", YELLOW)
        else:
            tag = c("✓", GREEN)

        branch = "└──" if is_last_file else "├──"
        fname = fpath.name if target.is_dir() else fpath.name
        lines.append(f"{branch} {tag} {fname}")

        if not file_issues:
            continue

        # group issues by source (frontmatter vs block line)
        source_groups: dict[str, list[Issue]] = {}
        doc = load_doc(fpath)
        doc_type = doc.frontmatter.get("type", "") if doc else ""
        for i in file_issues:
            if i.line == 1 and i.rule in ("frontmatter", "status"):
                key = (
                    f"L1 frontmatter (type: {doc_type})"
                    if doc_type
                    else "L1 frontmatter"
                )
            else:
                scope = ""
                for blk in doc.blocks if doc else []:
                    if blk.line_number == i.line:
                        parts = []
                        if blk.cfg.get("type"):
                            parts.append(f"type: {blk.cfg['type']}")
                        if blk.cfg.get("scope"):
                            parts.append(f"scope: {blk.cfg['scope']}")
                        scope = f" ({', '.join(parts)})" if parts else ""
                        break
                key = f"L{i.line} spec block{scope}"
            source_groups.setdefault(key, []).append(i)

        pipe = " " if is_last_file else "│"

        src_entries = list(source_groups.items())
        for si, (src_label, src_issues) in enumerate(src_entries):
            is_last_src = si == len(src_entries) - 1
            src_branch = "└──" if is_last_src else "├──"
            lines.append(f"{pipe}   {src_branch} {src_label}")

            for ii, issue in enumerate(src_issues):
                is_last_issue = ii == len(src_issues) - 1
                i_branch = "└──" if is_last_issue else "├──"
                sym = c("✗", RED) if issue.level == "error" else c("⚠", YELLOW)
                text = f"{issue.rule}: {issue.message}" if issue.rule else issue.message
                if issue.context:
                    text += f" → {issue.context}"
                lines.append(f"{pipe}       {i_branch} {sym} {text}")

    lines.append("")
    # summary
    n_files = len(ordered_files)
    n_err = len(errors)
    n_warn = len(warns)
    parts = [f"{n_files} file{'s' if n_files != 1 else ''}"]
    if n_err:
        parts.append(f"{c(str(n_err), RED, BOLD)} error{'s' if n_err != 1 else ''}")
    if n_warn:
        parts.append(f"{c(str(n_warn), YELLOW)} warning{'s' if n_warn != 1 else ''}")
    if not n_err and not n_warn:
        parts.append(c("clean", GREEN))
    lines.append("  ".join(parts))

    print("\n".join(lines))


# ── templates ────────────────────────────────────────────────────────────────


def _load_types_list(start: Path) -> list[str]:
    registry = load_types(start)
    return (
        sorted(registry.keys())
        if registry
        else [
            "story",
            "task",
            "feature",
            "design",
            "exploration",
            "research",
            "persona",
            "pov",
            "brainstorm",
            "roadmap",
            "flow",
            "wireframe",
            "prototype",
            "test",
            "brand",
            "handoff",
        ]
    )


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
    _render_tree(issues, p)
    errors = [i for i in issues if i.level == "error"]
    if errors:
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
