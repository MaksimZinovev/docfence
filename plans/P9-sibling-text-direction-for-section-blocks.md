---
id: P9
type: plan
status: draft
owner: maksim
depends_on: [P8]
last_validated: ~
---

# Move section-level spec blocks to top of section

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
  has_ynp_format: '^- \*\*[^*]+\*\*: (Yes|No|Possibly)\b'
```

## Context

```spec
type: plan
max_chars: 20000
banned_words: [might be, could be, seems like, I think, possibly, perhaps]
match:
  has_problem: '(problem|issue|bug|break|fail|cannot|does.not|unable)'
```

Section-level spec blocks currently sit at the end of each section. Since `sibling_text` is defined as "content immediately following the block" (loader.py), the validator sees empty text and all section-level match rules produce false positives (12 spurious errors on orient-startup-race.md). Moving spec blocks to the top of each section means `sibling_text` naturally contains the actual section content — no loader or validator code changes needed. (Source: loader.py L74, orient-startup-race.md validation producing 12 false match errors)

## Tools & Skills

```spec
type: plan
max_chars: 20000
banned_words: [N/A, n/a]
match:
  min_3_ynp: '^- \*\*[^*]+\*\*: (Yes|No|Possibly)\b'
```

- **grounded-planning**: Yes — this plan uses the plan format with docfence validation
- **verification-before-completion**: Yes — verify spec block placement works by re-validating orient plan
- **root-cause-tracing**: No — root cause already identified (sibling_text direction mismatch)
- **systematic-debugging**: No — bug is understood, fix is mechanical
- **cx/ck**: Yes — search for all documents with section-level spec blocks to inventory reformatting scope
- **skill-creator**: No — no skill creation involved
- **commit**: Possibly — if multi-file commit coordination needed

## Approach

```spec
type: plan
max_chars: 800
banned_words: [Q1:, Q2:, Q3:, **Q, Question:]
match:
  has_alternative: '(alternative|instead of|rather than|compared to|over:|vs[.])'
```

Move section-level spec blocks from end-of-section to top-of-section (immediately after the `##` heading). Since `sibling_text` already means "text after the block", this gives the validator the actual section content with zero code changes. The scaffold generator needs updating to place spec blocks before df-todo blocks instead of after. Existing plan documents need mechanical reformatting. An alternative — changing loader.py to reverse `sibling_text` direction for section-scope blocks — adds surprising semantics ("sometimes before, sometimes after") compared to a simple, consistent rule: spec block first, content follows.

## Out of Scope

```spec
type: plan
max_chars: 20000
banned_words: [Nothing., None., N/A, n/a, Not applicable]
match:
  has_justification: '^- \*\*[^*]+\*\*:'
  min_2_exclusions: '^- \*\*[^*]+\*\*:'
```

- **Changing `sibling_text` semantics in loader.py**: Top-of-section makes this unnecessary; consistent "text after block" semantics are clearer.
- **P8 (scope leak for required_sections/placeholders)**: Separate fix, should merge first to eliminate 45 errors and make the remaining 12 match errors visible.
- **Changing how document-level spec blocks work**: They already sit at top (after frontmatter) and work correctly — no change needed.

## Steps

```spec
type: plan
max_chars: 20000
banned_words: [**Step, **Task, **Phase]
match:
  has_step_evidence: '^- \[ \].*\(Source'
  min_3_steps: '^- \[( |x)\]'
```

- [ ] **Update scaffold generator to place spec blocks before df-todo blocks**: In `docfence.py`, change the scaffold rendering order for section-level spec blocks. Current order: `## Heading` → `[df-todo block]` → `[spec block]`. New order: `## Heading` → `[spec block]` → `[df-todo block]`.
  - Evidence: The scaffold generator in `docfence.py` renders sections by iterating `template_vars.sections`. The spec block and df-todo block are rendered per section. Swapping their order is a small change in the rendering logic. (Source: docfence.py scaffold generator)
  - Confidence: 0.90
  - Details: Find the section rendering loop and swap the order of spec block and df-todo block emission. The spec block should come first (after heading), then the df-todo block, then a blank line for content.

- [ ] **Reformat orient-startup-race.md**: Move each section's spec block from end-of-section to top-of-section (immediately after `## Heading`). This is a mechanical cut-paste per section — 5 spec blocks to move. Keep df-todo blocks (if any) after the spec block.
  - Evidence: orient-startup-race.md has 5 section-level spec blocks at lines L42, L54, L69, L109, L128 — all at section ends. Moving each to after its `##` heading is straightforward. (Source: orient-startup-race.md)
  - Confidence: 0.95
  - Details: For each section: cut the spec block from end, paste after `## Heading` line. No content changes needed.

- [ ] **Reformat P2 and P8 plans**: Same mechanical reformatting for the other 2 plan documents in pi-agent-config. P1, P3, P4 plans also if they have section-level spec blocks.
  - Evidence: P2-format-reference-validation-loop.md has section-level spec blocks that need moving. P8 (this file) has them too. (Source: pi-agent-config/plans/)
  - Confidence: 0.90

- [ ] **Validate orient-startup-race.md: confirm 0 section-level match errors**: After reformatting, run `docfence validate`. The 12 match errors should all resolve because `sibling_text` now contains the actual section content.
  - Evidence: Tools & Skills has 6 Y/N/P entries matching `min_3_ynp`. Approach has "alternative" matching `has_alternative`. Out of Scope has 4 items with bold-colon format. Steps has 5 checklist items. (Source: orient-startup-race.md content)
  - Confidence: 0.90
  - Details: `cd /Users/maksim/repos/pi-agent-config && python -m docfence validate plans/orient-startup-race.md`

- [ ] **Generate fresh scaffold and verify spec block placement**: Run `docfence new plan` and confirm that section-level spec blocks appear immediately after `##` headings, before df-todo blocks.
  - Evidence: The scaffold generator change (step 1) should produce the new ordering. (Source: docfence.py scaffold generator)
  - Confidence: 0.90
  - Details: `cd /Users/maksim/repos/docfence && python -m docfence new plan` and inspect output.

## Files to Modify

```spec
type: plan
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
match:
  has_file_marker: '(CREATED|UPDATED|DELETED)'
```

- `docfence/docfence.py` — UPDATED: swap spec block and df-todo block rendering order in scaffold generator
- `pi-agent-config/plans/orient-startup-race.md` — UPDATED: move 5 section-level spec blocks from end to top of sections
- `pi-agent-config/plans/P2-format-reference-validation-loop.md` — UPDATED: move section-level spec blocks to top of sections
- `docfence/plans/P8-scope-leak-required-sections-placeholders.md` — UPDATED: move section-level spec blocks to top of sections
- `docfence/plans/P9-sibling-text-direction-for-section-blocks.md` — UPDATED: move section-level spec blocks to top of sections (this file)

## Reuse

```spec
type: plan
max_chars: 20000
banned_words: [None., N/A, Nothing to reuse, No reuse]
match:
  has_reuse_item: '^- \*\*[^*]+\*\*:'
```

- **Existing `sibling_text` semantics**: No change needed — "text after block" already works when spec block is at top of section. (Source: loader.py L74)
- **orient-startup-race.md as test fixture**: Already demonstrates the bug with 12 false match errors; same file validates the fix after reformatting.
- **Scaffold generator existing structure**: The rendering loop already emits spec blocks and df-todo blocks per section — just need to swap their order.

## Evidence Pack

```spec
type: plan
max_chars: 20000
banned_words: [**Source**:, **Source:**]
match:
  has_evidence_claim: '^- \*\*Claim\*:'
  has_confidence: '\*\*Confidence\*\*:'
```

- **Claim**: Moving spec blocks to top-of-section makes `sibling_text` contain the actual section content, fixing all 12 false-positive match errors.
  Source: loader.py L74 — sibling_text is "content immediately following the block"; if spec block is at top, section content follows it
  **Confidence**: 0.95
  **Implication**: Zero code changes to loader.py or validator.py. Only scaffold generator and document reformatting.

- **Claim**: Top-of-section is semantically consistent with document-level spec blocks, which already sit at top (after frontmatter).
  Source: All existing plan documents — document-level spec block is always the first block after frontmatter, before any content
  **Confidence**: 1.0
  **Implication**: No confusing "sometimes before, sometimes after" semantics for `sibling_text`.

- **Claim**: The reformatting affects ~9 documents total (5 in pi-agent-config, 4+ in docfence), all mechanical cut-paste operations.
  Source: docfence/plans/ and pi-agent-config/plans/ inventories
  **Confidence**: 0.85
  **Implication**: 30 minutes of mechanical editing. Low risk, easy to verify.

### Gaps

- Haven't checked P1, P3, P4 plans for section-level spec blocks — they may not have them (predate the plan type definition).
- df-todo blocks currently precede spec blocks in scaffolds; after this change, spec blocks precede df-todo blocks. Need to verify that df-todo text doesn't pollute `sibling_text` validation (it shouldn't — df-todo blocks are fenced).

## Verification

```bash
# Test 1: Confirm 12 section-level match errors exist before reformatting
cd /Users/maksim/repos/pi-agent-config && python -m docfence validate plans/orient-startup-race.md 2>&1 | grep "match:" | wc -l
# Expected: 12

# Test 2: After reformatting, re-validate — match errors should be gone
cd /Users/maksim/repos/pi-agent-config && python -m docfence validate plans/orient-startup-race.md 2>&1 | grep "match:"
# Expected: 0 section-level match errors

# Test 3: Generate fresh scaffold and verify spec blocks are at top of sections
cd /Users/maksim/repos/docfence && python -m docfence new plan 2>&1 | head -60
# Expected: each section starts with ## Heading, then spec block, then df-todo block

# Test 4: Verify document-level spec blocks still work unchanged
cd /Users/maksim/repos/pi-agent-config && python -m docfence validate plans/P2-format-reference-validation-loop.md 2>&1
# Expected: same results as before (no regressions)

# Test 5: Verify section content validates correctly — banned_words in Context
# Test manually: add a banned word like "possibly" in a Context section with spec block at top
# Expected: docfence catches the banned word (proving sibling_text now contains section content)
```

## Bottom Line

- **Per-step confidence**: 0.91 (average)
- **Key risk**: df-todo blocks between spec block and content may affect `sibling_text` — need to verify they're excluded (they should be since they're fenced blocks).
- **Gap**: Haven't inventoried all existing plan documents for section-level spec blocks.
- **Recommendation**: proceed — zero code changes to validation engine, consistent semantics, mechanical document reformatting.