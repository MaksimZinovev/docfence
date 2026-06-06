# Minimal Focus Plan: Per-Section max_chars from template_vars

**Parent plan**: `plans/scaffold-df-todo.md`
**Scope**: Allow type TOML to declare per-section `max_chars` so the scaffold generator doesn't hardcode the distribution.

## Problem

The type TOML defines `max_chars = 5000` as a document-level default. But the scaffold generator needs per-section limits (e.g., Background=1500, Decision=1500, Open Questions=1000). Currently this distribution is implicit in the generator code — not declared anywhere. If a type has 5 required sections, the generator must somehow split 5000 across 5, and the author can't control the breakdown.

## Evidence

- **Claim**: `rule_max_chars` operates on `block.sibling_text`, which is per-section content. The document-level spec block has `scope: document` and its `max_chars` applies to the full text. Section-level spec blocks each need their own `max_chars`.
  **Source**: `core/rules.py:15` — `rule_max_chars(text, value, cfg)`; `core/loader.py:139` — scope=document gets full text
  **Confidence**: 1.0

- **Claim**: `_generate_scaffold()` (from parent plan Step 4) iterates over `template_vars.sections` and emits a ` ```spec ` block per section. The `max_chars` for each section spec block is currently undefined in the TOML — the generator would hardcode it.
  **Source**: `plans/scaffold-df-todo.md` — Step 4 details
  **Confidence**: 1.0

- **Claim**: `template_vars.sections` already supports sub-tables with `fill`. Extending with `max_chars` follows the same pattern.
  **Source**: `plans/scaffold-df-todo.md` — Step 3; `docs/specs/scaffold-sample.md`
  **Confidence**: 1.0

## Plan

### Step 1: Add `max_chars` to `template_vars.sections.*` in type TOML

```toml
[template_vars.sections.Background]
fill = "[REPLACE] Why this exploration is needed — delete this block and write your content"
max_chars = 1500

[template_vars.sections.Decision]
fill = "[REPLACE] What was decided and why — delete this block and write your content"
max_chars = 2000

[template_vars.sections.Open Questions]
fill = "[REPLACE] List unresolved questions — delete this block and write your content"
max_chars = 1000
```

### Step 2: Update `_generate_scaffold()` to read per-section `max_chars`

When emitting each section's ` ```spec ` block, read `section_cfg.max_chars` from `template_vars.sections.<Name>`. If present, use it. If absent, fall back to a proportional share of the document-level `max_chars` from `defaults`.

Fallback formula: `section_max = (doc_max_chars // num_sections) - spec_block_overhead` where `spec_block_overhead ≈ 200` chars accounts for spec block syntax.

### Step 3: No changes to validator or rules

The validator already reads `max_chars` from spec block `cfg`. The scaffold generator just needs to write the correct value into each section's spec block. No validator changes required.

### Step 4: Update scaffold sample

```spec
# Section spec block output for Decision (max_chars from TOML):
```spec
type: exploration
max_chars: 2000
banned_words: [TODO, TBD]
placeholders: ["```df-todo"]
```
```

## Verification

1. Edit exploration.toml to add `max_chars = 2000` under `[template_vars.sections.Decision]`
2. Run `docfence new exploration` → Decision section's spec block should show `max_chars: 2000`
3. Run `docfence new feature` (no per-section max_chars) → sections get proportional fallback from document-level default

## Risk

- **Risk**: Per-section `max_chars` values exceed the document-level `max_chars` total, making the doc impossible to validate (each section passes, but total exceeds doc limit).
  **Mitigation**: `_generate_scaffold()` should warn (not error) if sum of per-section limits exceeds document-level `max_chars`. This is a lint-on-config, not a runtime check.

## Dependency on parent plan

Depends on Steps 3–4 (TypeDef `template_vars` + `_generate_scaffold()`) from `plans/scaffold-df-todo.md`.