#!/usr/bin/env python3
"""
docfence — validate markdown spec docs with inline and type-level rules.

Usage examples:
  docfence validate notes/my-feature.md     # validate one file
  docfence validate docs/                   # validate all .md in folder
  docfence new feature                      # print a blank template
  docfence new feature --bare               # concise preview: frontmatter + headings only
  docfence types                            # list all known doc types
  docfence stamp docs/my-feature.md         # write last_validated timestamp
  docfence stamp --update-checksum doc.md   # also refresh spec_checksum
  docfence stamp --update-checksum --approved-by="username" doc.md

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

Type definitions live in .docfence/types/<name>.toml — drop a new file to add
a type without touching docfence core.
"""

import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.loader import load_doc
from core.types import TypeDef, load_types, resolve_type
from core.validator import validate_path, Issue

# Ensure Unicode glyphs (✗ ✓ ⚠ 💡) render on Windows consoles using a legacy
# codepage (e.g. cp1252). Safe no-op on POSIX / UTF-8 terminals.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        try:
            _reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


class InvalidDocTypeError(ValueError):
    """Raised when `docfence new` receives a flag-like token as the doc type."""


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


def _nearest_heading(doc, line_number: int) -> str | None:
    """Find the nearest H1/H2 heading above the given line."""
    if not doc or not doc.headings:
        return None
    heading_lines = sorted(doc.headings.keys())
    # find the last heading at or before line_number
    best = None
    for hl in heading_lines:
        if hl <= line_number:
            best = hl
        else:
            break
    return doc.headings[best] if best else None


def _render_tree(issues: list[Issue], target: Path, verbose: bool = False):
    """Render issues as a tree grouped by file, then source (frontmatter / spec block)."""
    files = list(target.rglob("*.md")) if target.is_dir() else [target]
    errors = [i for i in issues if i.level == "error"]
    warns = [i for i in issues if i.level == "warn"]
    hints = [i for i in issues if i.level == "hint"]
    passes = [i for i in issues if i.level == "pass"]

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
        file_warns = [i for i in file_issues if i.level in ("warn", "hint")]

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
        # In verbose mode, also track which blocks have no issues at all
        block_lines_with_issues = set()
        for i in file_issues:
            if i.line == 1 and i.rule in ("frontmatter", "status"):
                key = (
                    f"L1 frontmatter (type: {doc_type})"
                    if doc_type
                    else "L1 frontmatter"
                )
            else:
                block_lines_with_issues.add(i.line)
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

        # In verbose mode, add spec blocks that have no issues at all
        if verbose and doc:
            for blk in doc.blocks:
                if blk.line_number not in block_lines_with_issues:
                    parts = []
                    if blk.cfg.get("type"):
                        parts.append(f"type: {blk.cfg['type']}")
                    if blk.cfg.get("scope"):
                        parts.append(f"scope: {blk.cfg['scope']}")
                    scope = f" ({', '.join(parts)})" if parts else ""
                    key = f"L{blk.line_number} spec block{scope}"
                    # add a synthetic pass issue so the block shows up in the tree
                    source_groups.setdefault(
                        key,
                        [
                            Issue(
                                path=fpath,
                                line=blk.line_number,
                                level="pass",
                                rule="",
                                message="all rules passed",
                            )
                        ],
                    )

        pipe = " " if is_last_file else "│"

        src_entries = list(source_groups.items())
        for si, (src_label, src_issues) in enumerate(src_entries):
            is_last_src = si == len(src_entries) - 1
            src_branch = "└──" if is_last_src else "├──"
            lines.append(f"{pipe}   {src_branch} {src_label}")

            # In verbose mode, show nearest heading above this source
            if verbose and doc:
                src_line = src_issues[0].line if src_issues else 0
                heading = _nearest_heading(doc, src_line) if src_line > 1 else None
                if heading:
                    lines.append(f"{pipe}       {heading}")

            for ii, issue in enumerate(src_issues):
                is_last_issue = ii == len(src_issues) - 1
                i_branch = "└──" if is_last_issue else "├──"
                if issue.level == "error":
                    sym = c("✗", RED)
                elif issue.level == "pass":
                    sym = c("✓", GREEN)
                elif issue.level == "hint":
                    sym = c("💡", YELLOW)
                else:
                    sym = c("⚠", YELLOW)
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
    n_pass = len(passes)
    if n_err:
        parts.append(f"{c(str(n_err), RED, BOLD)} error{'s' if n_err != 1 else ''}")
    if n_warn:
        parts.append(f"{c(str(n_warn), YELLOW)} warning{'s' if n_warn != 1 else ''}")
    if hints:
        n_hints = len(hints)
        parts.append(f"{c(str(n_hints), YELLOW)} hint{'s' if n_hints != 1 else ''}")
    if verbose and n_pass:
        parts.append(f"{c(str(n_pass), GREEN)} passed")
    if not n_err and not n_warn and not verbose:
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


def _generate_scaffold(
    doc_type: str,
    type_def: TypeDef | None,
    overrides: dict | None = None,
    bare: bool = False,
) -> str:
    """Generate a scaffolded document from a TypeDef.

    Sections come from template_vars.sections (falling back to required_sections).
    df-todo blocks carry name and fill fields from template_vars.
    Spec blocks carry explicit rules from defaults.

    When bare=True, only the frontmatter and document-level spec block are
    rendered. The spec_checksum is still computed from the full spec-block set
    so it matches a normal scaffold of the same type.
    """
    overrides = overrides or {}
    defaults = type_def.defaults if type_def else {}
    tv = type_def.template_vars if type_def else {}

    # --- frontmatter ---
    fm_id = overrides.get("id") or tv.get("id", f"{doc_type[0].upper()}-001")
    fm_title = overrides.get("title") or tv.get("title", "Title")
    fm_owner = overrides.get("owner") or tv.get("owner", "human")
    fm_status = overrides.get("status") or tv.get("status", "draft")

    # --- document-level spec block ---
    doc_rules: dict[str, object] = {"scope": "document", "type": doc_type}
    for key in (
        "required_sections",
        "max_chars",
        "banned_words",
        "placeholders",
        "match",
    ):
        if key in defaults:
            doc_rules[key] = defaults[key]
    if "placeholders" not in doc_rules:
        doc_rules["placeholders"] = ["```df-todo"]
    doc_spec_lines = ["```spec"]
    for k, v in doc_rules.items():
        doc_spec_lines.append(_format_spec_kv(k, v))
    doc_spec_lines.append("```")
    doc_spec = "\n".join(doc_spec_lines)

    # --- sections ---
    sections_cfg = tv.get("sections", {})
    required = defaults.get("required_sections", ["Overview"])
    section_names = list(sections_cfg.keys()) if sections_cfg else list(required)

    section_blocks = []
    for name in section_names:
        sec_cfg = sections_cfg.get(name, {})

        if bare:
            section_blocks.append(f"## {name}")
            continue

        fill = sec_cfg.get(
            "fill",
            "[REPLACE] Write your content — delete this block and write your content",
        )
        slug = name.lower().replace(" ", "-")

        # df-todo block
        todo = f'```df-todo\nname = "{slug}"\nfill = "{fill}"\n```'

        # section spec block — per-section rules override defaults;
        # match is included only when explicitly defined in section config
        sec_rules: dict[str, object] = {"type": doc_type}
        for key in ("max_chars", "banned_words"):
            # per-section override wins, then fall back to type default
            if key in sec_cfg:
                sec_rules[key] = sec_cfg[key]
            elif key in defaults:
                sec_rules[key] = defaults[key]
        # per-section match rules — only when explicitly defined in section config
        if "match" in sec_cfg:
            sec_rules["match"] = sec_cfg["match"]
        sec_spec_lines = ["```spec"]
        for k, v in sec_rules.items():
            sec_spec_lines.append(_format_spec_kv(k, v))
        sec_spec_lines.append("```")
        sec_spec = "\n".join(sec_spec_lines)

        section_blocks.append(f"## {name}\n\n{sec_spec}\n\n{todo}")

    sections = "\n\n".join(section_blocks)

    # --- spec checksum ---
    # collect all spec block raw TOML content and compute SHA-256[:8] checksum

    all_raw_tomls = []
    # document-level spec block
    all_raw_tomls.append("\n".join(doc_spec_lines[1:-1]))  # strip fences
    # section-level spec blocks
    for name in section_names:
        sec_cfg = sections_cfg.get(name, {})
        sec_rules: dict[str, object] = {"type": doc_type}
        for key in ("max_chars", "banned_words"):
            if key in sec_cfg:
                sec_rules[key] = sec_cfg[key]
            elif key in defaults:
                sec_rules[key] = defaults[key]
        if "match" in sec_cfg:
            sec_rules["match"] = sec_cfg["match"]
        raw_lines = []
        for k, v in sec_rules.items():
            raw_lines.append(_format_spec_kv(k, v))
        all_raw_tomls.append("\n".join(raw_lines))

    combined = "\n".join(all_raw_tomls)
    spec_checksum = hashlib.sha256(combined.encode()).hexdigest()[:8]

    frontmatter_and_doc_spec = (
        f"---\n"
        f"id: {fm_id}\n"
        f"type: {doc_type}\n"
        f"status: {fm_status}\n"
        f"owner: {fm_owner}\n"
        f"depends_on: []\n"
        f"spec_checksum: {spec_checksum}\n"
        f"last_validated: ~\n"
        f"---\n\n"
        f"# {fm_title}\n\n"
        f"{doc_spec}\n"
    )

    if bare:
        return (
            f"# Concise scaffold preview for type: {doc_type} — use "
            f"`docfence new {doc_type}` for full template\n\n"
            f"{frontmatter_and_doc_spec}"
        )

    return frontmatter_and_doc_spec + f"\n{sections}\n"


def _format_spec_kv(key: str, value) -> str:
    """Format a spec block key-value pair."""
    if isinstance(value, list):
        if key == "placeholders":
            items = ", ".join(f'"{v}"' for v in value)
        else:
            items = ", ".join(str(v) for v in value)
        return f"{key}: [{items}]"
    if isinstance(value, dict):
        # Render dict as sub-block (e.g. match: rules)
        # Always single-quote values; escape any inner single quotes
        lines = [f"{key}:"]
        for k, v in value.items():
            escaped = str(v).replace("'", "\\'")
            lines.append(f"  {k}: '{escaped}'")
        return "\n".join(lines)
    return f"{key}: {value}"


# ── commands ─────────────────────────────────────────────────────────────────


def cmd_validate(target: str, verbose: bool = False):
    p = Path(target)
    if not p.exists():
        print(f"ERR  path not found: {target}")
        sys.exit(1)
    issues = validate_path(p, verbose=verbose)
    _render_tree(issues, p, verbose=verbose)
    errors = [i for i in issues if i.level == "error"]
    if errors:
        sys.exit(1)


def cmd_new(
    doc_type: str,
    output: Path | None = None,
    overrides: dict | None = None,
    bare: bool = False,
):
    if doc_type.startswith("--"):
        raise InvalidDocTypeError(
            f"'{doc_type}' looks like a flag, not a doc type — flags go after the type.\n\n"
            "Examples:\n"
            "  docfence new plan --bare\n"
            "  docfence new feature --bare --output docs/my-feature.md\n"
            '  docfence new plan --bare --set title="My Plan"\n\n'
            "Run `docfence types` to see available types."
        )

    registry = load_types(Path.cwd())
    type_def = resolve_type(doc_type, registry) if registry else None

    content = _generate_scaffold(doc_type, type_def, overrides, bare=bare)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content)
        print(f"Created {output}")
    else:
        print(content, end="")


def cmd_types():
    known = _load_types_list(Path.cwd())
    print("Available doc types (from .docfence/types/ + built-ins):\n")
    for t in known:
        print(f"  {t}")


def _log_checksum_update(
    filepath: Path,
    old_checksum: str,
    new_checksum: str,
    timestamp: str,
    approved_by: str = "",
) -> None:
    """Append a checksum update entry to .docfence/checksum.log."""
    doc = load_doc(filepath)
    doc_id = doc.frontmatter.get("id", "(unknown)") if doc else "(unknown)"

    # best-effort git commit hash
    git_commit = "(none)"
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            git_commit = result.stdout.strip()
    except Exception:
        pass

    # find .docfence directory
    docfence_dir = filepath.parent / ".docfence"
    if not docfence_dir.is_dir():
        # walk up to find it
        for parent in filepath.parents:
            candidate = parent / ".docfence"
            if candidate.is_dir():
                docfence_dir = candidate
                break
    docfence_dir.mkdir(parents=True, exist_ok=True)
    log_path = docfence_dir / "checksum.log"

    entry = (
        f"{timestamp} | {filepath.name} | id={doc_id} | "
        f"{old_checksum} → {new_checksum} | git={git_commit}"
    )
    if approved_by:
        entry += f" | approved_by={approved_by}"
    entry += "\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def cmd_stamp(target: str, update_checksum: bool = False, approved_by: str = ""):
    p = Path(target)
    if not p.exists():
        print(f"ERR  file not found: {target}")
        sys.exit(1)
    if update_checksum:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  ⚠️  spec_checksum UPDATE — IRON LAW CHECK                     ║
║                                                                  ║
║  Updating the spec checksum REWRITES the tamper-evidence seal.   ║
║  This must NEVER be done without EXPLICIT USER PERMISSION.      ║
║                                                                  ║
║  If you are an AI agent: ASK THE USER before proceeding.         ║
║  If the user did not explicitly request this: STOP NOW.          ║
║                                                                  ║
║  Did the user explicitly approve this checksum update?           ║
╚══════════════════════════════════════════════════════════════════╝
""")
    issues = validate_path(p)
    if update_checksum:
        # when updating checksum, only block on non-checksum errors
        errors = [i for i in issues if i.level == "error" and i.rule != "spec_checksum"]
    else:
        errors = [i for i in issues if i.level == "error"]
    if errors:
        print("Cannot stamp — errors must be resolved first:")
        for e in errors:
            print(e)
        sys.exit(1)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    text = p.read_text()
    text = re.sub(r"last_validated:.*", f"last_validated: {ts}", text)
    if update_checksum:
        doc = load_doc(p)
        old_checksum = (
            doc.frontmatter.get("spec_checksum", "(none)") if doc else "(none)"
        )
        new_checksum = doc.spec_checksum if doc else None
        if doc and doc.spec_checksum:
            text = re.sub(
                r"spec_checksum:.*",
                f"spec_checksum: {doc.spec_checksum}",
                text,
            )
            print(f"✓  updated spec_checksum: {doc.spec_checksum}")
        elif doc and doc.blocks and new_checksum:
            # no checksum existed yet — add it after last_validated or depends_on
            if re.search(r"depends_on:", text):
                text = re.sub(
                    r"(depends_on: .*)",
                    f"\\1\nspec_checksum: {new_checksum}",
                    text,
                )
            else:
                text = re.sub(
                    r"(last_validated: .*)",
                    f"\\1\nspec_checksum: {new_checksum}",
                    text,
                )
            print(f"✓  added spec_checksum: {new_checksum}")
        # log the checksum change
        if new_checksum:
            _log_checksum_update(
                p, old_checksum, new_checksum, ts, approved_by=approved_by
            )
    p.write_text(text)
    print(f"✓  stamped {p} — {ts}")


# ── entry ─────────────────────────────────────────────────────────────────────


def main():
    args = sys.argv[1:]
    match args[:2]:
        case ["validate", target]:
            rest = args[2:]
            verbose = "--verbose" in rest
            cmd_validate(target, verbose=verbose)
        case ["new", doc_type]:
            rest = args[2:]
            output = None
            overrides = {}
            bare = False
            i = 0
            while i < len(rest):
                if rest[i] == "--bare":
                    bare = True
                    i += 1
                elif rest[i] == "--output" and i + 1 < len(rest):
                    output = Path(rest[i + 1])
                    i += 2
                elif rest[i] == "--set" and i + 1 < len(rest):
                    # --set key=value (next arg is the key=value pair)
                    kv = rest[i + 1].split("=", 1)
                    if len(kv) == 2:
                        overrides[kv[0]] = kv[1]
                    i += 2
                elif rest[i].startswith("--set="):
                    # --set=key=value (inline)
                    kv = rest[i].removeprefix("--set=").split("=", 1)
                    if len(kv) == 2:
                        overrides[kv[0]] = kv[1]
                    i += 1
                else:
                    i += 1
            try:
                cmd_new(doc_type, output=output, overrides=overrides or None, bare=bare)
            except InvalidDocTypeError as e:
                print(e)
                sys.exit(1)
        case ["types"]:
            cmd_types()
        case ["stamp", target]:
            rest = args[2:]
            update_checksum = "--update-checksum" in rest
            approved_by = ""
            for i, arg in enumerate(rest):
                if arg == "--approved-by" and i + 1 < len(rest):
                    approved_by = rest[i + 1]
                elif arg.startswith("--approved-by="):
                    approved_by = arg.removeprefix("--approved-by=")
            cmd_stamp(target, update_checksum=update_checksum, approved_by=approved_by)
        case _:
            print(__doc__)


if __name__ == "__main__":
    main()
