# Verbose Mode

```bash
$ docfence validate sample-docs/ --verbose               # ← add --verbose to see full picture
sample-docs/
├── ✗ bad-feature.md
│   └── L18 spec block (type: feature)
│       # Data Export Feature                            # ← nearest H1/H2 heading above this block
│       ├── ✓ max_chars: content within 200 char limit   # ← passing check (green ✓)
│       └── ✗ banned_words: banned word 'TODO' found in content
├── ✓ good-feature.md                                    # ← now expanded, shows all blocks
│   └── L18 spec block (type: feature)
│       # User Authentication API                        # ← heading shown only in verbose
│       ├── ✓ max_chars: content within 1500 char limit
│       └── ✓ banned_words: no banned words found (TODO, TBD, placeholder)

4 files  5 errors  1 warning  31 passed                  # ← summary includes passed count
```