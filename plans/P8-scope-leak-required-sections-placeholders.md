---
id: P8
type: plan
status: draft
owner: maksim
depends_on: []
last_validated: ~
---

# Fix scope leak: block `required_sections` and `placeholders` from inheriting at section scope

```spec
scope: document
type: plan
required_sections: [Context, Tools & Skills, Approach, Out of Scope, Steps, Files to Modify, Reuse, Evidence Pack, Verification, Bottom Line]
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
placeholders: ["```df-todo", "[REPLACE]"]
match:
  has_checklist: '^- \[( |x)\]'
  has_source: 'Source:'
  has_file_marker: '(CREATED|UPDATED|DELETED)'
  has_test: '# Test \d'
  has_out_of_scope: '^## Out of Scope'
  has_tools_and_skills: '^## Tools & Skills'
  has_ynp_format: '^- .+: (Yes|No|Possibly)\b'
```

## Context

```spec
type: plan
max_chars: 20000
banned_words: [might be, could be, seems like, I think, possibly, perhaps]
match:
  has_problem: '(problem|issue|bug|break|fail|cannot|does.not|unable)'
```

Section-level spec blocks inherit `required_sections` and `placeholders` from type defaults, causing nonsensical errors like "required section missing: Context" *inside* the Context section itself. This is the same scope leak that was fixed for `match` (validator.py already blocks `match` inheritance at section scope), but `required_sections` and `placeholders` were missed. Running `docfence validate` on orient-startup-race.md produces 45 spurious `required_sections` errors — all from section-level spec blocks inheriting a document-level rule. (Source: validator.py L84-88 — only `match` is filtered by scope)

## Tools & Skills

```spec
type: plan
max_chars: 20000
banned_words: [N/A, n/a]
match:
  min_3_ynp: '^- .+: (Yes|No|Possibly)\b'
```

- grounded-planning: Yes — this plan uses the plan format and docfence validation loop
- root-cause-tracing: Yes — used to identify scope leak as root cause of 45 false errors
- verification-before-completion: Yes — verify fix against orient-startup-race.md before declaring done
- systematic-debugging: No — root cause already identified, no further investigation needed
- skill-creator: No — no skill creation involved
- cx/ck: Yes — search for other rule keys that may also leak at section scope
- mcp: github-cli: Possibly — if commit/pr workflow needed

## Approach

```spec
type: plan
max_chars: 800
banned_words: [Q1:, Q2:, Q3:, **Q, Question:]
match:
  has_alternative: '(alternative|instead of|rather than|compared to|over:|vs[.])'
```

Extend the existing scope filter in validator.py to block `required_sections` and `placeholders` from inheriting into section-level spec blocks, exactly like `match` is already blocked. The fix is 2 lines added to the existing scope check. An alternative — splitting defaults into `[defaults.document]` and `[defaults.section]` in the TOML format — is a larger change that should be a separate enhancement (H5 in SKILL.md).

## Out of Scope

```spec
type: plan
max_chars: 20000
banned_words: [Nothing., None., N/A, n/a, Not applicable]
match:
  has_justification: '^- .+:'
  min_2_exclusions: '^- .+:'
```

- Splitting `[defaults]` into `[defaults.document]` and `[defaults.section]`: Separate enhancement per H5 heuristic; this fix doesn't block it.
- Changing how section-level spec blocks get typed: Current auto-detection (inherit type from frontmatter) works fine.
- Fixing Bug 2 (sibling_text direction): Separate plan (P9).

## Steps

```spec
type: plan
max_chars: 20000
banned_words: [**Step, **Task, **Phase]
match:
  has_step_evidence: '^- \[ \].*\(Source'
  min_3_steps: '^- \[( |x)\]'
```

- [ ] Add `required_sections` and `placeholders` to the scope filter in validator.py: In the `for rule_key in RULES` loop (L79-91), extend the existing `match` scope check to also filter `required_sections` and `placeholders`. Change `if rule_key == "match" and block.scope != "document":` to `if rule_key in ("match", "required_sections", "placeholders") and block.scope != "document":`.
  - Evidence: The scope filter already exists for `match` at L84-88. Adding 2 more keys to the check is minimal and consistent. (Source: validator.py L84-88)
  - Confidence: 0.95
  - Details: The exact change is `if rule_key in ("match", "required_sections", "placeholders") and block.scope != "document": continue`. The `inherited` list should also skip these keys at section scope.

- [ ] Validate orient-startup-race.md and confirm 0 `required_sections` errors at section scope: Run `docfence validate` on the plan file. The 45 `required_sections` errors on section-level blocks should disappear. Only document-level spec block errors (if any) should remain.
  - Evidence: orient-startup-race.md has 5 section-level spec blocks each producing 8-9 `required_sections` errors = 45 total. Removing inheritance eliminates all of them. (Source: validation output from this session)
  - Confidence: 0.90
  - Details: `cd /Users/maksim/repos/pi-agent-config && python -m docfence validate plans/orient-startup-race.md`

- [ ] Verify document-level `required_sections` still works: Ensure the document-level spec block (L25, `scope: document`) still correctly validates all 10 required sections.
  - Evidence: The scope filter only blocks inheritance at section scope. Document-level blocks with explicit `required_sections` in cfg are unaffected. (Source: validator.py L80-81 — explicit block rules win over defaults)
  - Confidence: 0.95

## Files to Modify

```spec
type: plan
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
match:
  has_file_marker: '(CREATED|UPDATED|DELETED)'
```

- `docfence/core/validator.py` — UPDATED: extend scope filter from `match`-only to include `required_sections` and `placeholders` at L84

## Reuse

```spec
type: plan
max_chars: 20000
banned_words: [None., N/A, Nothing to reuse, No reuse]
match:
  has_reuse_item: '^- .+:'
```

- Existing scope filter pattern: The `match` scope filter at L84-88 is the exact pattern to extend — no new code structure needed. (Source: validator.py L84-88)
- orient-startup-race.md as test fixture: Already exists, already demonstrates the bug, will validate the fix.

## Evidence Pack

```spec
type: plan
max_chars: 20000
banned_words: [**Source**:, **Source:**]
match:
  has_evidence_claim: '^- Claim:'
  has_confidence: 'Confidence:'
```

- Claim: `required_sections` and `placeholders` inherit into section-level spec blocks, producing 45 spurious errors on orient-startup-race.md.
  Source: validator.py L79-91 — the inheritance loop has no scope filter for these two keys, only for `match`
  Confidence: 0.95
  Implication: Adding them to the existing scope filter eliminates all 45 errors with a 2-word change.

- Claim: Document-level blocks are unaffected because they have `scope: document` and pass the scope check.
  Source: validator.py L84 — `block.scope != "document"` already handles this
  Confidence: 0.95
  Implication: No risk of regressions to document-level validation.

- Claim: The fix is exactly 2 words changed: `"match"` → `("match", "required_sections", "placeholders")` and `rule_key ==` → `rule_key in`.
  Source: validator.py L84
  Confidence: 1.0
  Implication: Minimal change, easy to review, low regression risk.

## Verification

```bash
# Test 1: Confirm the bug exists before fix
cd /Users/maksim/repos/pi-agent-config && python -m docfence validate plans/orient-startup-race.md 2>&1 | grep "required_sections" | wc -l
# Expected: 45 (or similar large number)

# Test 2: Fix validator.py, then re-validate
cd /Users/maksim/repos/docfence && python -m docfence validate /Users/maksim/repos/pi-agent-config/plans/orient-startup-race.md 2>&1 | grep "required_sections"
# Expected: 0 section-level required_sections errors

# Test 3: Confirm document-level required_sections still works
cd /Users/maksim/repos/docfence && python -m docfence validate /Users/maksim/repos/pi-agent-config/plans/orient-startup-race.md 2>&1 | grep "L25.*required_sections"
# Expected: no errors at L25 (document-level block) since all 10 sections exist
```

## Bottom Line

- Per-step confidence: 0.93 (average)
- Key risk: None — the fix extends an existing, tested pattern by 2 words.
- Gap: The `placeholders` inheritance at section scope is less visible in current output (warnings, not errors) but should be blocked for consistency.
- Recommendation: proceed — 2-word change, 45 errors eliminated.