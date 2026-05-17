"""
Built-in validation rule functions.

Each rule receives (text, value, cfg) and returns a list of error strings.
text    — the sibling content the spec block applies to
value   — the rule's configured value from the spec block
cfg     — the full parsed spec block dict (for cross-rule context)
"""

import urllib.request
from pathlib import Path


def rule_max_chars(text: str, value: int, cfg: dict) -> list[str]:
    if len(text) > value:
        return [f"content is {len(text)} chars, limit is {value}"]
    return []


def rule_banned_words(text: str, value: list[str], cfg: dict) -> list[str]:
    errors = []
    lower = text.lower()
    for word in value:
        if word.lower() in lower:
            errors.append(f"banned word '{word}' found in content")
    return errors


def rule_validate(text: str, value: list[str], cfg: dict) -> list[str]:
    errors = []
    lines = [l.strip().lstrip("- ") for l in text.splitlines() if l.strip()]
    for rule_name in value:
        for line in lines:
            if not line:
                continue
            if rule_name == "file_exists":
                if not line.startswith("http") and not Path(line).exists():
                    errors.append(f"file not found: '{line}'")
            elif rule_name == "valid_url":
                if line.startswith("http"):
                    try:
                        urllib.request.urlopen(line, timeout=3)
                    except Exception:
                        errors.append(f"unreachable url: '{line}'")
    return errors


def rule_required_sections(text: str, value: list[str], cfg: dict) -> list[str]:
    """Document-wide rule: checks that required headings exist in the full doc."""
    errors = []
    for heading in value:
        pattern = heading.lower()
        if not any(pattern in line.lower() for line in text.splitlines()
                   if line.startswith("#")):
            errors.append(f"required section missing: '{heading}'")
    return errors


# Registry maps spec block field names to rule functions
RULES: dict[str, callable] = {
    "max_chars": rule_max_chars,
    "banned_words": rule_banned_words,
    "validate": rule_validate,
    "required_sections": rule_required_sections,
}
