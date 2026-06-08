---
name: docfence
description: Type definition authoring skill. Use when creating or modifying .docfence/types/*.toml files, scaffold generation rules, or validation patterns.
---

# Docfence Type Authoring

## Overview

Type definitions (`.docfence/types/*.toml`) are code that writes code — they generate scaffolds and validate documents. They need the same rigor as production code: tests, review, and traceability.

## 10 Meta-Heuristics

Distilled from real failures during the plan doctype authoring. Apply to any type — plan, feature, exploration, or future types.

---

### H1: Fill-Template Consistency → Mandatory Review Checklist

**Failure:** Fill said "Tree of files" but template showed flat bullet list. Two surfaces describing the same thing drifted silently.

**DO:**
- ✅ Compare fill text structural keywords (tree, list, table, checklist, prose) against the template/example format before committing
- ✅ Flag any mismatch — if fill says "tree", template must render a tree

**DON'T:**
- ❌ Write fill text and template in isolation
- ❌ Update one without checking the other

---

### H2: Rule-Text Alignment → Replace Quantifiers with Rule References

**Failure:** Approach fill said "Max ~10 lines" but max_chars was 800 (could be 3 long lines or 12 short ones). The quantifier lied.

**DO:**
- ✅ Let rules carry the numbers: "Size limited per section rules" or "(800 char limit)"
- ✅ If fill text says "Minimum N items", there must be a match rule that enforces ≥N

**DON'T:**
- ❌ Put "~N lines" in fill text without a corresponding max_chars grounded in that number
- ❌ Use vague quantifiers that contradict actual limits

---

### H3: User Intent Fidelity → Diff-Before-Commit

**Failure:** User said "Include end-user testing where possible". I wrote "Include end-user testing". Lost the qualifier "where possible". Also lost "tree format" — user chose it, I switched to flat list.

**Workflow:**
1. Record user's exact phrasing from interviews, feedback, and annotations
2. Before committing fill text changes, compare against the source of truth
3. If anything was paraphrased or removed, flag it explicitly
4. Get explicit approval for any deviation

**DO:**
- ✅ Preserve exact phrasing from user feedback — qualifiers like "where possible" are not noise
- ✅ Show diffs of user-specified content before committing

**DON'T:**
- ❌ Silently remove qualifiers or format choices the user specified
- ❌ Assume your paraphrase is equivalent to the user's exact words

---

### H4: Self-Contamination → df-todo Blocks Are Validation-Exempt

**Failure:** Context banned_words includes "possibly", and the fill text contained "possibly" from instruction text. Scaffold validation flagged its own instructions.

**DO:**
- ✅ Treat df-todo blocks as instruction space — exempt from content validation (banned_words, match, placeholders)
- ✅ Rephrase fill text to avoid banned words when possible (e.g., "State the issue concisely" instead of "What problem does this possibly solve?")
- ✅ If a banned word must appear in fill text, that's expected — the validator should skip df-todo blocks

**DON'T:**
- ❌ Validate df-todo fill text against the same content rules as the document
- ❌ Leave self-contamination as a "known issue" without addressing it

---

### H5: Scope Leak → Two Separate Defaults Blocks

**Failure:** Section-level spec blocks inherited `required_sections` and `match` from type defaults, causing "required section missing: Context" errors INSIDE the Context section.

**Rule:** Document-level rules (required_sections, global match, placeholders) should never flow into section-level blocks. Split `[defaults]` into `[defaults.document]` and `[defaults.section]`.

**DO:**
- ✅ Put required_sections, document-level match, and placeholders in document scope
- ✅ Put max_chars and banned_words in section scope (can be inherited)
- ✅ Let section-level overrides add their own match/banned_words explicitly

**DON'T:**
- ❌ Inherit document-level rules at section scope
- ❌ Use a single `[defaults]` block without scope distinction for cross-scope rules

---

### H6: Escaping Consistency → Single-Quote Regex + Test Fixtures

**Failure:** Double-quoted regex `"^\\["` became `^\\[` (literal backslash+bracket) after `_parse_kv` stripped once. Single-quoted `'^\['` gave the correct regex.

**DO:**
- ✅ Use single quotes for all regex in TOML type definitions
- ✅ Create named patterns (`.docfence/patterns.toml`) with centralized definitions
- ✅ Write test fixtures for each pattern: one passing document, one failing document
- ✅ Run `docfence type test <type>` before deploying new patterns

**DON'T:**
- ❌ Use double-quoted regex in TOML (double-escaping trap)
- ❌ Write match patterns without a test proving they work

---

### H7: Structural Counting → Extend Match with Optional `min` Field

**Failure:** `min_3_ynp` and `min_3_steps` patterns only check existence (≥1 line), not cardinality (≥3). The names promise a count they can't deliver.

**Chosen approach:** Extend match dict with optional `min` field. Existing string patterns keep working. Dict patterns add `{pattern = '...', min = 3}` for counting. Minimal engine change, backward compatible.

```toml
# Current (lying name — only checks ≥1):
min_3_steps = '^- \\[( |x)\\]'

# After (honest name + counting):
has_steps = '^- \\[( |x)\\]'
min_3_steps = {pattern = '^- \\[( |x)\\]', min = 3}
```

**DO:**
- ✅ Name existence rules honestly: `has_step` not `min_3_steps`
- ✅ Use dict syntax `{pattern, min}` when you need cardinality
- ✅ Add counting to `rule_match` engine: count lines matching pattern, compare to `min`

**DON'T:**
- ❌ Name a rule `min_N_*` if it can't count to N
- ❌ Assume match rules enforce cardinality — they only check existence

---

### H8: Backward Compatibility → Classify and Migrate

**Failure:** Changing `has_test` from `'^### Test'` to `'# Test \d'` was safe by luck — it widened the pattern. A narrowing change (like `has_source: 'Source:'` → `'\*\*Source\*\*:'`) would break existing documents silently.

**Chosen approach:** Before deploying any rule change, classify it. Widening (more permissive) is safe. Narrowing (more restrictive) requires: list affected docs, migrate them, then deploy. Use dual patterns during transition.

**Classification test:**
- **Widening:** New pattern matches everything old pattern matched, plus more. Safe to deploy.
- **Narrowing:** New pattern excludes some inputs the old pattern accepted. Must migrate existing docs first.

**Transition syntax for narrowing changes:**
```toml
# Accept both old and new during transition:
has_test = ['^### Test', '# Test \\d']
# After all docs migrated:
# has_test = '# Test \\d'
```

**DO:**
- ✅ Classify every pattern change as widening or narrowing
- ✅ Widening → deploy immediately
- ✅ Narrowing → list affected docs, migrate, deploy
- ✅ Use list syntax for transition periods

**DON'T:**
- ❌ Deploy narrowing changes without checking existing documents
- ❌ Assume backward compatibility by luck — test it

---

### H9: Fail-Mode Clarity → Collapse Repetitive Errors

**Failure:** Running `docfence validate` on a fresh scaffold produced 20+ errors (10 placeholder blocks, banned words in fill text, missing match patterns). Important signal was lost in noise.

**Chosen approach:** Group identical rule violations into one line with count. Show first + last location. Instead of 10 separate "unfilled placeholder" errors, show 1 line: `✗ placeholders: 10 unfilled blocks (L28–L115)`.

```bash
# Before (noisy — 20+ lines):
✗ placeholders: unfilled placeholder block (L28)
✗ placeholders: unfilled placeholder block (L35)
✗ placeholders: unfilled placeholder block (L52)
... × 7 more
✗ match: 'has_test' not found
✗ banned_words: 'TODO' found (L4)

# After (compact — 3 lines):
✗ placeholders: 10 unfilled blocks (L28–L115)
✗ match: 'has_test' not found
✗ banned_words: 'TODO' found (L4)
```

**Implementation:** In `validator.py`, group issues by `(rule, message_template)`. If count > 1, collapse to single line with count and line range.

**DO:**
- ✅ Collapse identical violations into one line with count
- ✅ Show first and last line number for collapsed violations
- ✅ Keep unique violations (different messages) as separate lines

**DON'T:**
- ❌ Show 10 identical errors when 1 line with `(×10)` conveys the same information
- ❌ Lose the line numbers entirely — show range for collapsed groups

---

### H10: Type Authoring Protocol → Test Fixtures Alongside Types

**Failure:** The root cause of most failures in this session: no enforced workflow. Fill text written from memory, patterns changed without testing, user phrasing silently dropped.

**Chosen approach:** Start with minimal test fixtures alongside type definitions. Every type.toml gets a `<type>.tests.toml` with pass/fail example documents. Extend later with more automation.

```toml
# plan.tests.toml (alongside plan.toml)
[[test]]
name = "minimal_valid"
content = """---
type: plan
---
## Context
Bug found.
## Verification
```bash
true  # Test 1: passes
# Expected: exit 0
```
"""
expected_pass = true

[[test]]
name = "missing_checklist"
content = """---
type: plan
---
## Context
No steps here.
"""
expected_pass = false
expected_errors = ["has_checklist"]
```

**Workflow:**
1. Write/modify type.toml
2. Run `docfence type test <type>` — validates test fixtures pass/fail correctly
3. Generate scaffold: `docfence new <type>`
4. Human review: compare fill text to user's exact requirements (H3)
5. Commit with message referencing decisions

**Start minimal.** One passing test and one failing test per important rule. Extend when rules break.

**DO:**
- ✅ Write at least 2 test fixtures per type: one passing, one failing
- ✅ Run test fixtures before committing type changes
- ✅ Use human review for fill text vs user intent (H3 catches what tests can't)

**DON'T:**
- ❌ Write fill text from memory — use user's exact words
- ❌ Change patterns without testing against existing documents
- ❌ Skip scaffold-and-validate before declaring done