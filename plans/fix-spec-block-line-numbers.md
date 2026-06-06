# Minimal Focus Plan: Fix Spec Block Line Numbers

**Problem**: Spec block line numbers in validation output are wrong.

**Root cause**: `_extract_spec_blocks()` builds a `line_starts` map using body line numbers (relative to the text after frontmatter). When it returns `(raw_toml, sibling, ln)`, the line number `ln` is body-relative, not absolute. The caller never adds the frontmatter offset, so spec blocks are reported at wrong line numbers.

**Example**: Document-level spec block fence is at absolute line 12, but reported as `L4`. Section-level spec blocks at absolute lines 20, 33, 46 are reported as `L4, L17, L30` (body-relative).

## Fix

In `_extract_spec_blocks()` in `core/loader.py`, add `fm_offset` parameter and apply it to all returned line numbers:

```python
def _extract_spec_blocks(body: str, fm_offset: int = 0) -> list[tuple[str, str, int]]:
    ...
    for match in pattern.finditer(body):
        ...
        ln = line_starts.get(closest, 0) + fm_offset  # ← add offset
        results.append((raw_toml, sibling, ln))
```

In `load_doc()`, pass the frontmatter line count:

```python
fm, body = _parse_frontmatter(text)
raw_blocks = _extract_spec_blocks(body, fm_offset=len(fm))
```

## Verification

1. Load a scaffolded file, check `block.line_number` matches actual fence line
2. Run `docfence validate my-exploration.md` — spec block headers should show correct line numbers