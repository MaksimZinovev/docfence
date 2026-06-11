"""
Parses a markdown file into:
  - frontmatter dict (YAML between --- delimiters)
  - a list of SpecBlock dataclasses
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path


def _parse_kv(text: str) -> dict:
    """
    Parse 'key: value' lines into a dict.
    Supports:
      - scalar:     key: value
      - inline list: key: [a, b, c]
      - sub-block:  key:\n  subkey: value   → key = {subkey: value, ...}
    """
    data: dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" not in stripped:
            i += 1
            continue
        k, _, v = stripped.partition(":")
        k = k.strip()
        v = v.strip()

        if v == "":
            # possible sub-block: collect indented lines that follow
            sub_lines = []
            while i + 1 < len(lines) and lines[i + 1].startswith("  "):
                i += 1
                sub_lines.append(lines[i].strip())
            if sub_lines:
                # parse each "  label: pattern" into a list of {label, pattern} dicts
                pairs = []
                for sl in sub_lines:
                    if ":" in sl:
                        sk, _, sv = sl.partition(":")
                        sv = sv.strip().strip('"').strip("'")
                        pairs.append({sk.strip(): sv})
                data[k] = pairs
            else:
                data[k] = None
        elif v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            data[k] = (
                [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
                if inner
                else []
            )
        elif v == "~":
            data[k] = None
        elif v.isdigit():
            data[k] = int(v)
        else:
            data[k] = v
        i += 1
    return data


@dataclass
class SpecBlock:
    cfg: dict  # parsed TOML from inside the ```spec block
    raw_toml: str = ""  # raw TOML content of the spec block (for checksum computation)
    sibling_text: str = ""  # content immediately following the block
    scope: str = ""  # "document" or "section"
    bid: str = ""  # sha256[:8] of sibling_text at parse time
    line_number: int = 0
    inherited_rules: list[str] = field(default_factory=list)  # rules from type defaults


@dataclass
class ParsedDoc:
    path: Path
    frontmatter: dict
    full_text: str  # full raw markdown (for document-scope rules)
    blocks: list[SpecBlock]
    headings: dict[int, str] = field(
        default_factory=dict
    )  # line_number → heading text (H1, H2)
    spec_checksum: str | None = None  # SHA-256[:8] of all spec blocks' raw TOML


def _compute_spec_checksum(blocks: list[SpecBlock]) -> str:
    """Compute SHA-256[:8] checksum from all spec blocks' raw TOML content."""
    combined = "\n".join(block.raw_toml for block in blocks)
    return hashlib.sha256(combined.encode()).hexdigest()[:8]


def _sha8(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract frontmatter between --- delimiters. Returns (data, body)."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}, text
    return _parse_kv(match.group(1)), text[match.end() :]


def _extract_headings(text: str) -> dict[int, str]:
    """Extract H1/H2 headings with their line numbers, skipping fenced code blocks."""
    headings: dict[int, str] = {}
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # track fenced code blocks (```, ~~~, and variants)
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith(("# ", "## ")):
            headings[i] = stripped
    return headings


def _extract_spec_blocks(body: str) -> list[tuple[str, str, int]]:
    """Returns list of (raw_toml, sibling_text, line_number)."""
    results = []
    pattern = re.compile(r"```spec\n(.*?)\n```\s*\n", re.DOTALL)
    lines = body.split("\n")
    line_starts = {}
    pos = 0
    for i, line in enumerate(lines):
        line_starts[pos] = i + 1
        pos += len(line) + 1

    for match in pattern.finditer(body):
        raw_toml = match.group(1)
        after = body[match.end() :]
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
    headings = _extract_headings(text)
    raw_blocks = _extract_spec_blocks(body)
    blocks: list[SpecBlock] = []

    _SPEC_BLOCK_RE = re.compile(r"```spec\n.*?\n```\s*", re.DOTALL)
    _DF_TODO_RE = re.compile(r"```df-todo\n.*?\n```\s*", re.DOTALL)

    for raw_toml, sibling, ln in raw_blocks:
        try:
            cfg = _parse_kv(raw_toml)
        except Exception as e:
            cfg = {"_parse_error": str(e)}
        scope = cfg.get("scope", "section")
        if scope == "document":
            # strip all spec blocks from full text so their contents don't self-trigger rules
            effective_sibling = _SPEC_BLOCK_RE.sub("", text).strip()
        else:
            # strip any nested spec block fences from sibling text
            effective_sibling = _SPEC_BLOCK_RE.sub("", sibling).strip()
            effective_sibling = _DF_TODO_RE.sub("", effective_sibling).strip()
        blocks.append(
            SpecBlock(
                cfg=cfg,
                raw_toml=raw_toml,
                sibling_text=effective_sibling,
                scope=scope,
                bid=_sha8(effective_sibling),
                line_number=ln,
            )
        )

    spec_checksum = _compute_spec_checksum(blocks) if blocks else None

    return ParsedDoc(
        path=path,
        frontmatter=frontmatter,
        full_text=text,
        blocks=blocks,
        headings=headings,
        spec_checksum=spec_checksum,
    )
