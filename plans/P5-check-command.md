# Plan: `docfence check` — Fast Lightweight Validation

Add a `check` command that runs only cheap rules (`required_sections`, `placeholders`, `banned_words`, `heading_level`) and skips expensive ones (`match`, `validate`, `structure`). Planners run `docfence check` after each section fill for fast feedback (~instant vs. regex-heavy `match` on large docs). Full `docfence validate` runs once at the end. Implementation: add `--check` flag to `cmd_validate`, filter `RULES` to a `CHECK_RULES` allowlist.

**Files**: `docfence.py` (`main()` add `check` subcommand, `cmd_validate()` accept `fast` param), `core/validator.py` (pass rule filter to `validate_doc`)

**Ref**: `core/rules.py` — cheap rules are `required_sections`, `placeholders`, `banned_words`, `heading_level`. Expensive: `match`, `validate`, `structure`.