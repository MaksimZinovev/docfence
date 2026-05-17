"""
Parses a markdown file into:
  - frontmatter dict (YAML between --- delimiters)
  - a list of SpecBlock dataclasses
"""

import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path


def _parse_kv(text: str) -> dict:
    """Parse simple 'key: value' lines into a dict. Shared by frontmatter and spec blocks."""
    data: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            v = [i.strip().strip('"').strip("'") for i in inner.split(",") if i.strip()] if inner else []
        elif v == "~":
            v = None
        elif v.isdigit():
            v = int(v)
        data[k.strip()] = v
    return data


@dataclass
class SpecBlock:
    cfg: dict                    # parsed TOML from inside the ```spec block
    sibling_text: str            # content immediately following the block
    scope: str                   # "document" or "section"
    bid: str                     # sha256[:8] of sibling_text at parse time
    line_number: int
    inherited_rules: list[str] = field(default_factory=list)  # rules from type defaults


@dataclass
class ParsedDoc:
    path: Path
    frontmatter: dict
    full_text: str               # full raw markdown (for document-scope rules)
    blocks: list[SpecBlock]


def _sha8(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract frontmatter between --- delimiters. Returns (data, body)."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}, text
    return _parse_kv(match.group(1)), text[match.end():]


def _extract_spec_blocks(body: str) -> list[tuple[str, str, int]]:
    """Returns list of (raw_toml, sibling_text, line_number)."""
    results = []
    pattern = re.compile(r"```spec\n(.*?)```", re.DOTALL)
    lines = body.split("\n")
    line_starts = {}
    pos = 0
    for i, line in enumerate(lines):
        line_starts[pos] = i + 1
        pos += len(line) + 1

    for match in pattern.finditer(body):
        raw_toml = match.group(1)
        after = body[match.end():]
        next_block = re.search(r"```spec", after)
        sibling = after[: next_block.start()] if next_block else after
        sibling = sibling.strip()

        # find closest line number
        closest = max((p for p in line_starts if p <= match.start()), default=0)
        ln = line_starts.get(closest, 0)
        results.append((raw_toml, sibling, ln))
    return results


def load_doc(path: Path) -> ParsedDoc | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    frontmatter, body = _parse_frontmatter(text)
    raw_blocks = _extract_spec_blocks(body)
    blocks: list[SpecBlock] = []

    for raw_toml, sibling, ln in raw_blocks:
        try:
            cfg = _parse_kv(raw_toml)
        except Exception as e:
            cfg = {"_parse_error": str(e)}
        scope = cfg.get("scope", "section")
        if scope == "document":
            # strip all spec blocks from full text so their contents don't self-trigger rules
            effective_sibling = re.sub(r"```spec\n.*?```", "", text, flags=re.DOTALL).strip()
        else:
            effective_sibling = sibling
        blocks.append(SpecBlock(
            cfg=cfg,
            sibling_text=effective_sibling,
            scope=scope,
            bid=_sha8(effective_sibling),
            line_number=ln,
        ))

    return ParsedDoc(path=path, frontmatter=frontmatter, full_text=text, blocks=blocks)
