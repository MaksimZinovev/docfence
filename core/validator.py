"""
Orchestrates validation of a ParsedDoc.

For each spec block:
  1. Resolve the doc type from frontmatter or block cfg
  2. Merge type defaults with explicit block rules
  3. Warn if any rule is inherited (not explicitly set in the block)
  4. Run each applicable rule function
  5. Check required frontmatter fields for the type
  6. Verify status is valid for the type
"""

from dataclasses import dataclass
from pathlib import Path

from core.loader import ParsedDoc
from core.rules import RULES
from core.types import load_types, resolve_type

NON_RULE_KEYS = {"type", "scope", "bid", "status", "owner", "depends_on", "_parse_error"}


@dataclass
class Issue:
    path: Path
    line: int
    level: str   # "error" or "warn"
    rule: str = ""     # e.g. "banned_words", "status", "frontmatter"
    message: str = ""
    context: str = ""  # e.g. "allowed: draft, active, frozen, done"

    def __str__(self):
        tag = "ERR " if self.level == "error" else "WARN"
        return f"{tag} {self.path}:{self.line} — {self.message}"


def validate_doc(doc: ParsedDoc, types_dir: Path) -> list[Issue]:
    registry = load_types(types_dir)
    issues: list[Issue] = []
    doc_type_name = doc.frontmatter.get("type", "")
    typedef = resolve_type(doc_type_name, registry) if doc_type_name else None

    # --- frontmatter checks ---
    if typedef:
        for field in typedef.required_fields:
            if field not in doc.frontmatter or doc.frontmatter[field] in (None, "", []):
                issues.append(Issue(doc.path, 1, "error", rule="frontmatter",
                    message=f"missing required field '{field}' for type '{typedef.name}'"))
        status = doc.frontmatter.get("status", "")
        if status and status not in typedef.statuses:
            issues.append(Issue(doc.path, 1, "error", rule="status",
                message=f"'{status}' not valid for type '{typedef.name}'",
                context=f"allowed: {', '.join(typedef.statuses)}"))
    elif doc_type_name:
        issues.append(Issue(doc.path, 1, "warn", rule="frontmatter",
            message=f"unknown type '{doc_type_name}' — no definition found in .speccheck/types/"))

    # --- spec block checks ---
    for block in doc.blocks:
        if "_parse_error" in block.cfg:
            issues.append(Issue(doc.path, block.line_number, "error", rule="parse",
                message=f"spec block parse error — {block.cfg['_parse_error']}"))
            continue

        block_type_name = block.cfg.get("type", doc_type_name)
        block_typedef = resolve_type(block_type_name, registry) if block_type_name else typedef

        # merge defaults: explicit block rules win; defaults fill gaps with a warning
        defaults = block_typedef.defaults if block_typedef else {}
        effective_rules: dict = {}
        inherited: list[str] = []

        for rule_key in RULES:
            if rule_key in block.cfg:
                effective_rules[rule_key] = block.cfg[rule_key]
            elif rule_key in defaults:
                effective_rules[rule_key] = defaults[rule_key]
                inherited.append(rule_key)

        if inherited:
            issues.append(Issue(doc.path, block.line_number, "warn", rule="inherited",
                message=f"uses inherited defaults for: {', '.join(inherited)} "
                f"(from type '{block_type_name}') — consider making them explicit"))

        # run rules
        for rule_key, rule_value in effective_rules.items():
            fn = RULES.get(rule_key)
            if fn:
                for msg in fn(block.sibling_text, rule_value, block.cfg):
                    issues.append(Issue(doc.path, block.line_number, "error", rule=rule_key,
                        message=msg))

    return issues


def validate_path(target: Path) -> list[Issue]:
    from core.loader import load_doc
    files = list(target.rglob("*.md")) if target.is_dir() else [target]
    all_issues: list[Issue] = []
    types_dir = target if target.is_dir() else target.parent
    for f in files:
        doc = load_doc(f)
        if doc:
            all_issues.extend(validate_doc(doc, types_dir))
    return all_issues
