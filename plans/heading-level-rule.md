# Plan: `heading_level` Rule

Add a `heading_level` rule to `core/rules.py` that enforces required sections appear at the correct heading depth. Value is a list of `"H2 Context"`, `"H3 Test"`, etc. The rule checks that each named heading exists in the text at the specified level. Catches the planner writing `## Grounded Plan` instead of `## Steps`, or `**Step N**:` instead of `- [ ]` items under `## Steps`.

**Files**: `core/rules.py` (add rule), `RULES` dict (register), `.docfence/types/plan.toml` (add `heading_level = ["H2 Context", "H2 Approach", "H2 Steps", "H2 Files to Modify", "H2 Evidence Pack", "H2 Verification", "H2 Bottom Line", "H2 Document Map"]`)

**Ref**: real plan `plans/trim-header-chrome.md` — has `## Grounded Plan` instead of `## Steps`, no `## Context`, no `## Approach`.