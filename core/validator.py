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

NON_RULE_KEYS = {
    "type",
    "scope",
    "bid",
    "status",
    "owner",
    "depends_on",
    "_parse_error",
}


@dataclass
class Issue:
    path: Path
    line: int
    level: str  # "error", "warn", or "hint"
    rule: str = ""  # e.g. "banned_words", "status", "frontmatter"
    message: str = ""
    context: str = ""  # e.g. "allowed: draft, active, frozen, done"

    def __str__(self):
        tag = (
            "ERR "
            if self.level == "error"
            else (
                "WARN"
                if self.level == "warn"
                else ("HINT" if self.level == "hint" else "PASS")
            )
        )
        return f"{tag} {self.path}:{self.line} — {self.message}"


def validate_doc(doc: ParsedDoc, types_dir: Path, verbose: bool = False) -> list[Issue]:
    registry = load_types(types_dir)
    issues: list[Issue] = []
    doc_type_name = doc.frontmatter.get("type", "")
    typedef = resolve_type(doc_type_name, registry) if doc_type_name else None

    # --- frontmatter checks ---
    if typedef:
        for field in typedef.required_fields:
            if field not in doc.frontmatter or doc.frontmatter[field] in (None, "", []):
                issues.append(
                    Issue(
                        doc.path,
                        1,
                        "error",
                        rule="frontmatter",
                        message=f"missing required field '{field}' for type '{typedef.name}'",
                    )
                )
            elif verbose:
                issues.append(
                    Issue(
                        doc.path,
                        1,
                        "pass",
                        rule="frontmatter",
                        message=f"required field '{field}' present",
                    )
                )
        status = doc.frontmatter.get("status", "")
        if status and status not in typedef.statuses:
            issues.append(
                Issue(
                    doc.path,
                    1,
                    "error",
                    rule="status",
                    message=f"'{status}' not valid for type '{typedef.name}'",
                    context=f"allowed: {', '.join(typedef.statuses)}",
                )
            )
        elif status and verbose:
            issues.append(
                Issue(
                    doc.path,
                    1,
                    "pass",
                    rule="status",
                    message=f"'{status}' is valid for type '{typedef.name}'",
                )
            )
    elif doc_type_name:
        issues.append(
            Issue(
                doc.path,
                1,
                "warn",
                rule="frontmatter",
                message=f"unknown type '{doc_type_name}' — no definition found in .docfence/types/",
            )
        )

    # --- spec_coverage: check each section in type definition has spec blocks with expected rules ---
    if typedef and "sections" in typedef.template_vars:
        type_sections = typedef.template_vars["sections"]
        # map section names to their spec blocks by finding nearest heading
        for sec_name, sec_cfg in type_sections.items():
            expected_rules = [k for k in sec_cfg if k != "fill"]
            # find the heading for this section in the document
            heading_line = None
            for ln, htext in doc.headings.items():
                # headings are like "## Section Name" — match the section name
                hname = htext.lstrip("#").strip()
                if hname == sec_name:
                    heading_line = ln
                    break
            if heading_line is None:
                # section heading not found — skip (required_sections rule catches this)
                continue
            # find the spec block closest after the heading, before next heading
            # allow a line-number tolerance because _extract_spec_blocks
            # uses approximate character-to-line mapping
            next_heading_line = min(
                (ln2 for ln2 in doc.headings if ln2 > heading_line),
                default=float("inf"),
            )
            best_block = None
            for block in doc.blocks:
                if block.scope == "document":
                    continue
                # spec block line may be before the heading due to
                # approximate line-number mapping in _extract_spec_blocks
                if block.line_number + 10 < heading_line:
                    continue
                if block.line_number >= next_heading_line + 10:
                    continue
                if best_block is None or block.line_number < best_block.line_number:
                    best_block = block
            if best_block is None:
                if expected_rules:
                    issues.append(
                        Issue(
                            doc.path,
                            heading_line,
                            "error",
                            rule="spec_coverage",
                            message=f"'{sec_name}' section has no spec block (expected rules: {', '.join(expected_rules)})",
                        )
                    )
                continue
            # check that the spec block contains all expected rule keys
            NON_META = {"type", "scope", "bid", "status", "owner", "depends_on"}
            block_rules = {k for k in best_block.cfg if k not in NON_META}
            missing = [k for k in expected_rules if k not in block_rules]
            extra = [
                k
                for k in block_rules
                if k not in expected_rules and k not in ("type", "scope")
            ]
            if missing:
                issues.append(
                    Issue(
                        doc.path,
                        best_block.line_number,
                        "error",
                        rule="spec_coverage",
                        message=f"'{sec_name}' section spec block missing rule(s): {', '.join(missing)} (expected: {', '.join(expected_rules)})",
                    )
                )
            if extra:
                issues.append(
                    Issue(
                        doc.path,
                        best_block.line_number,
                        "hint",
                        rule="spec_coverage",
                        message=f"'{sec_name}' section has extra rule(s) not in type definition: {', '.join(extra)}",
                    )
                )

    # --- spec_checksum: verify spec blocks haven't been modified or removed ---
    if doc.spec_checksum is not None and doc.frontmatter.get("spec_checksum"):
        stored = doc.frontmatter["spec_checksum"]
        computed = doc.spec_checksum
        if stored != computed:
            issues.append(
                Issue(
                    doc.path,
                    1,
                    "error",
                    rule="spec_checksum",
                    message=f"spec blocks modified or removed — expected {stored}, got {computed}. "
                    f"If you intentionally changed a spec block, run 'docfence stamp --update-checksum' to refresh it.",
                )
            )
    elif doc.blocks and not doc.frontmatter.get("spec_checksum"):
        # document has spec blocks but no checksum in frontmatter — hint to add one
        has_placeholders = any(
            i.rule == "placeholders" and i.level == "error" for i in issues
        )
        if not has_placeholders:
            issues.append(
                Issue(
                    doc.path,
                    1,
                    "hint",
                    rule="spec_checksum",
                    message="no spec_checksum in frontmatter — run 'docfence stamp --update-checksum' to add integrity check for spec blocks",
                )
            )

    # --- spec block checks ---
    for block in doc.blocks:
        if "_parse_error" in block.cfg:
            issues.append(
                Issue(
                    doc.path,
                    block.line_number,
                    "error",
                    rule="parse",
                    message=f"spec block parse error — {block.cfg['_parse_error']}",
                )
            )
            continue

        block_type_name = block.cfg.get("type", doc_type_name)
        block_typedef = (
            resolve_type(block_type_name, registry) if block_type_name else typedef
        )

        # merge defaults: explicit block rules win; defaults fill gaps with a warning
        defaults = block_typedef.defaults if block_typedef else {}
        effective_rules: dict = {}
        inherited: list[str] = []

        for rule_key in RULES:
            if rule_key in block.cfg:
                effective_rules[rule_key] = block.cfg[rule_key]
            elif rule_key in defaults:
                # match is document-scope only; don't inherit into section-level blocks
                if (
                    rule_key in ("match", "required_sections", "placeholders")
                    and block.scope != "document"
                ):
                    continue
                val = defaults[rule_key]
                # toml stores match as {label: pattern}; rule_match expects [{label: pattern}]
                if rule_key == "match" and isinstance(val, dict):
                    val = [{k: v} for k, v in val.items()]
                effective_rules[rule_key] = val
                inherited.append(rule_key)

        if inherited:
            issues.append(
                Issue(
                    doc.path,
                    block.line_number,
                    "warn",
                    rule="inherited",
                    message=f"uses inherited defaults for: {', '.join(inherited)} "
                    f"(from type '{block_type_name}') — consider making them explicit",
                )
            )

        # run rules
        block_match_errors = 0
        for rule_key, rule_value in effective_rules.items():
            fn = RULES.get(rule_key)
            if fn:
                errors = fn(block.sibling_text, rule_value, block.cfg)
                for msg in errors:
                    issues.append(
                        Issue(
                            doc.path,
                            block.line_number,
                            "error",
                            rule=rule_key,
                            message=msg,
                        )
                    )
                    if rule_key == "match":
                        block_match_errors += 1
                if not errors and verbose:
                    issues.append(
                        Issue(
                            doc.path,
                            block.line_number,
                            "pass",
                            rule=rule_key,
                            message=_pass_message(rule_key, rule_value),
                        )
                    )

    # --- post-block hints ---
    # only emit spec-placement hint if document has no placeholder issues
    # (otherwise empty sibling_text is expected for a fresh scaffold)
    has_placeholders = any(
        i.rule == "placeholders" and i.level == "error" for i in issues
    )
    if not has_placeholders:
        for block in doc.blocks:
            if block.scope == "document":
                continue
            match_errors = sum(
                1
                for i in issues
                if i.line == block.line_number
                and i.rule == "match"
                and i.level == "error"
            )
            if match_errors > 0 and len(block.sibling_text.strip()) < 20:
                issues.append(
                    Issue(
                        doc.path,
                        block.line_number,
                        "hint",
                        rule="spec-placement",
                        message="spec block has no content after it — move to top of section "
                        "so validation sees the section content. "
                        "See README: Section-level spec blocks",
                    )
                )

    return issues


def _pass_message(rule_key: str, rule_value) -> str:
    """Generate a human-readable message for a passing rule."""
    if rule_key == "max_chars":
        return f"content within {rule_value} char limit"
    if rule_key == "banned_words":
        words = (
            ", ".join(rule_value) if isinstance(rule_value, list) else str(rule_value)
        )
        return f"no banned words found ({words})"
    if rule_key == "required_sections":
        sections = (
            ", ".join(rule_value) if isinstance(rule_value, list) else str(rule_value)
        )
        return f"all required sections present ({sections})"
    if rule_key == "validate":
        checks = (
            ", ".join(rule_value) if isinstance(rule_value, list) else str(rule_value)
        )
        return f"all {checks} checks passed"
    if rule_key == "match":
        labels = []
        if isinstance(rule_value, list):
            for entry in rule_value:
                if isinstance(entry, dict):
                    labels.extend(entry.keys())
        return (
            f"all patterns matched ({', '.join(labels)})"
            if labels
            else "all patterns matched"
        )
    return "passed"


def validate_path(target: Path, verbose: bool = False) -> list[Issue]:
    from core.loader import load_doc

    files = list(target.rglob("*.md")) if target.is_dir() else [target]
    all_issues: list[Issue] = []
    types_dir = target if target.is_dir() else target.parent
    for f in files:
        doc = load_doc(f)
        if doc:
            all_issues.extend(validate_doc(doc, types_dir, verbose=verbose))
    return all_issues
