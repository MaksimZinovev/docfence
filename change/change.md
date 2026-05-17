# CLI Output: Tree Format

## Target

```
$ docfence validate sample-docs/
sample-docs/
├── ✓ good-feature.md
├── ⚠ test-match.md
│   └── L18 spec block (type: feature)
│       └── ⚠ inherited: banned_words from type 'feature'
└── ✗ bad-feature.md
    ├── L1 frontmatter (type: feature)
    │   ├── ✗ missing required field 'owner'
    │   └── ✗ status 'brainstorm' not valid → allowed: draft, active, frozen, done
    ├── L4 spec block (type: feature, scope: document)
    │   ├── ✗ banned_words: 'TODO' found in content
    │   └── ✗ banned_words: 'TBD' found in content
    └── L18 spec block (type: feature)
        └── ✗ banned_words: 'TODO' found in content

3 files  6 errors  1 warning
```

## Changes

### 1. `Issue` — add `rule` + `context` (defaults keep existing `__str__` working)

```python
@dataclass
class Issue:
    path: Path
    line: int
    level: str
    rule: str = ""
    message: str = ""
    context: str = ""
```

`__str__` unchanged. Tree renderer reads the new fields directly.

### 2. `validator.py` — pass `rule` and `context` when creating Issues

Only the call sites change. Example:

```python
Issues.append(Issue(..., rule="frontmatter", message=f"missing required field '{field}'"))
Issues.append(Issue(..., rule="status", message=f"'{status}' not valid", context=f"allowed: {', '.join(typedef.statuses)}"))
# per-rule loop:
Issues.append(Issue(..., rule=rule_key, message=msg))
```

### 3. `docfence.py` — `cmd_validate` renders tree instead of line-by-line

- Group issues by file, then by source (frontmatter / spec block)
- Print `├──`/`└──`/`│` tree
- `✓`/`⚠`/`✗` prefix per file, colored (red/yellow/green, `--no-color` to disable)
- Footer: `{N} files  {E} errors  {W} warnings`
