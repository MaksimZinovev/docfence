---
id: P11
type: plan
status: draft
owner: maksim
depends_on: []
last_validated: ~
---

# Spec Checksum Integrity

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

AI agents filling scaffolded docfence documents sometimes delete spec blocks (validation rules) instead of only deleting df-todo placeholders. The document then passes validation — not because content is correct, but because the rules checking it were silently removed. This issue was confirmed in a previous session where the agent admitted to "removing per-section spec codeblocks that were in the scaffold." A secondary issue: `plan.toml` has a typo (`segments` instead of `sections`) in `[template_vars.segments."Files to Modify"]`, causing that section's scaffold config to be silently ignored. Spec reference: docs/specs/spec-checksum.md.

## Tools & Skills

```spec
type: plan
max_chars: 20000
banned_words: [N/A, n/a, grep sufficient, small codebase, simple enough, overkill for]
match:
  min_3_ynp: '^- .+: (Yes|No|Possibly)\b'
  has_cx: '\bcx\b.*\(Skills\).*: Yes\b'
  has_ck: '\bck\b.*\(Skills\).*: Yes\b'
  has_gh: '\bgh\b.*\(CLI\).*: Yes\b'
  has_deepwiki: 'deepwiki.*\(MCP\).*: Yes\b'
```

- docfence (Skills): Yes — validating plans and testing scaffold/validate round-trips
- grounded-planning (Skills): Yes — writing this plan using the grounded-planning skill
- cx (Skills): Yes — tracing code structure across docfence modules
- ck (Skills): Yes — indexing codebase for quick lookups
- gh (CLI): Yes — committing changes
- deepwiki (MCP): Yes — could use for researching Python hashlib/hmac patterns if needed
- python3 (CLI): Yes — running docfence directly for validation testing
- jq (CLI): Possibly — if we need to inspect TOML structure, though Python tomllib is sufficient

## Approach

```spec
type: plan
max_chars: 800
banned_words: [Q1:, Q2:, Q3:, **Q, Question:]
match:
  has_alternative: '(alternative|instead of|rather than|compared to|over:|vs[.])'
```

Implement SHA-256 checksum in frontmatter rather than HMAC or a companion file. SHA checksum stored in frontmatter is simpler (1/10 complexity vs 3/10 for HMAC), catches accidental spec block deletion and mutation, and the threat model is cooperative-but-confused agents — not adversarial ones. The spec_coverage check (exact rule key match per section) is the primary defense; checksum is a second layer. HMAC can be added later if needed. The `segments` → `sections` typo in plan.toml is a one-line fix included in scope. Rather than building a separate `check-scaffold` subcommand, we integrate both checks into `validate_doc()` where type definitions are already available.

## Out of Scope

```spec
type: plan
max_chars: 20000
banned_words: [Nothing., None., N/A, n/a, Not applicable]
match:
  has_justification: '^- .+:'
  min_2_exclusions: '^- .+:'
```

- HMAC signing: deferred to future iteration; SHA checksum addresses accidental deletion, which is the primary threat (Source: docs/specs/spec-checksum.md HMAC Overhead section)
- `docfence check-scaffold` subcommand: redundant with spec_coverage + checksum checks in `validate`; not needed as a separate command
- Fixing existing plan files: authors fix their own plans; this plan only adds the detection/prevention mechanism (Source: user direction from prior session)
- df-todo `protect_spec` field: deferred; spec_coverage + checksum provide sufficient protection for now
- Test suite: out of scope for this iteration; docfence has no test framework yet and adding one is a separate concern

## Steps

```spec
type: plan
max_chars: 20000
banned_words: [**Step, **Task, **Phase]
match:
  has_step_evidence: '^- \[ \].*\(Source'
  min_3_steps: '^- \[( |x)\]'
```

- [ ] Fix `segments` → `sections` typo in `.docfence/types/plan.toml` line 86 (Source: core/loader.py `_generate_scaffold` reads `template_vars.sections`; plan.toml has `segments` instead)
  - Confidence: 1.0
  - Details: Change `[template_vars.segments."Files to Modify"]` to `[template_vars.sections."Files to Modify"]`. This makes the fill text and match rules for Files to Modify actually take effect during scaffolding.
- [ ] Add `spec_checksum` computation in `core/loader.py` (Source: docs/specs/spec-checksum.md Step 1; core/loader.py `_sha8` and `_extract_spec_blocks`)
  - Confidence: 0.9
  - Details: Add function `_compute_spec_checksum(blocks: list[SpecBlock]) -> str` that concatenates all spec block raw TOML content in order and returns `hashlib.sha256(...).hexdigest()[:8]`. Modify `load_doc()` to compute and store checksum on `ParsedDoc`. Also store the raw spec block TOML strings on `SpecBlock` (currently discarded after `_parse_kv`) so the checksum can be recomputed later during validation.
- [ ] Add `spec_coverage` check in `core/validator.py` `validate_doc()` (Source: core/validator.py:28-70 frontmatter check pattern; core/types.py `TypeDef.template_vars`)
  - Confidence: 0.85
  - Details: After frontmatter checks, if `typedef` has `template_vars.sections`, iterate each section name. For each section, find the corresponding spec block in the document (match by section heading position). Check that the spec block's cfg contains every rule key defined in `template_vars.sections.<Name>`. Missing rule keys → error. Extra rule keys → info/hint. Missing entire spec block → error with expected rules listed.
- [ ] Add `spec_checksum` validation in `core/validator.py` `validate_doc()` (Source: docs/specs/spec-checksum.md Steps 2-3; core/validator.py frontmatter check pattern)
  - Confidence: 0.9
  - Details: After spec block checks, if frontmatter has `spec_checksum`, recompute checksum from current spec blocks and compare. Mismatch → error with expected vs actual and hint message. If no `spec_checksum` in frontmatter, emit a hint suggesting to run `docfence stamp` to add one.
- [ ] Update `_generate_scaffold` in `docfence.py` to write `spec_checksum` into frontmatter (Source: docfence.py:290-340 scaffold generation; core/loader.py checksum computation)
  - Confidence: 0.9
  - Details: After generating all spec blocks, compute the SHA-256 checksum of their raw TOML content and write it as `spec_checksum: <hex>` in the frontmatter. This ensures every new scaffold starts with a valid checksum.
- [ ] Update `cmd_stamp` in `docfence.py` to support `--update-checksum` flag (Source: docfence.py:370-385 stamp command; docs/specs/spec-checksum.md Con 1)
  - Confidence: 0.85
  - Details: Add `--update-checksum` flag to `cmd_stamp`. When set, recompute spec block checksum and update `spec_checksum` in frontmatter alongside `last_validated`. Without the flag, stamp only updates `last_validated` (existing behavior). Update CLI arg parsing in `main()`.
- [ ] Update SKILL.md H11 wording to reference `stamp --update-checksum` (Source: skills/docfence/SKILL.md H11 already committed)
  - Confidence: 1.0
  - Details: Add a note to H11's DO list: "If you intentionally change a spec block, run `docfence stamp --update-checksum` afterward" (already partially there from prior commit — verify it's complete).

## Files to Modify

```spec
type: plan
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
match:
  has_file_entry: '^- `[^`]+` — (CREATED|UPDATED|DELETED)'
```

- `.docfence/types/plan.toml` — UPDATED: fix `segments` → `sections` typo on line 86
- `core/loader.py` — UPDATED: add `_compute_spec_checksum()`, store raw TOML on SpecBlock, add `spec_checksum` field to ParsedDoc
- `core/validator.py` — UPDATED: add spec_coverage check and spec_checksum validation in `validate_doc()`
- `docfence.py` — UPDATED: update `_generate_scaffold` to write `spec_checksum` in frontmatter; update `cmd_stamp` to support `--update-checksum`; update `main()` arg parsing
- `skills/docfence/SKILL.md` — UPDATED: verify H11 references `stamp --update-checksum`

## Reuse

```spec
type: plan
max_chars: 20000
banned_words: [None., N/A, Nothing to reuse, No reuse]
match:
  has_reuse_item: '^- .+:'
```

- `_sha8()` in core/loader.py: already computes SHA-256 hashes — reuse the same hashlib approach for spec checksum (8-char hex digest)
- frontmatter check pattern in validate_doc: the existing frontmatter validation loop (lines 28-70) is the exact pattern for iterating type definition requirements — replicate for spec_coverage
- `_parse_kv()` and `_extract_spec_blocks()`: already parse spec blocks — extend to also store raw TOML strings needed for checksum
- `_generate_scaffold()`: already generates frontmatter — extend to add `spec_checksum` field
- `cmd_stamp()`: already modifies frontmatter — extend to also update `spec_checksum`

## Evidence Pack

```spec
type: plan
max_chars: 20000
banned_words: [**Source**:, **Source:**]
match:
  has_evidence_claim: '^- Claim:'
  has_confidence: 'Confidence:'
```

- Claim: `_generate_scaffold` reads `template_vars.sections` (not `segments`) to build per-section spec blocks
  Source: docfence.py:318-340
  Confidence: 1.0
  Implication: The `segments` typo in plan.toml causes the Files to Modify section config to be silently ignored during scaffolding

- Claim: `validate_doc()` already has a frontmatter check loop that iterates type definition requirements — this is the pattern to replicate for spec_coverage
  Source: core/validator.py:28-70
  Confidence: 1.0
  Implication: spec_coverage check can follow the same structure: iterate typedef.template_vars.sections, find matching spec blocks, compare rule keys

- Claim: `_sha8()` already uses `hashlib.sha256` for block IDs — extending it for spec checksum uses the same stdlib dependency
  Source: core/loader.py:65
  Confidence: 1.0
  Implication: No new dependencies needed for SHA-256 checksum; `hashlib` is already imported

- Claim: Python stdlib `hmac` module is available but not currently imported; if HMAC is added later, it's a one-line import
  Source: `python3 -c "import hmac"` succeeded
  Confidence: 1.0
  Implication: HMAC upgrade path is straightforward but out of scope for this iteration

- Claim: `SpecBlock` dataclass stores `cfg` (parsed dict) but discards the raw TOML string after parsing — checksum needs the raw content
  Source: core/loader.py:94-108 `_extract_spec_blocks` returns raw TOML but `load_doc` only passes parsed `cfg` to SpecBlock
  Confidence: 0.95
  Implication: Need to add a `raw_toml: str` field to `SpecBlock` and pass it through from `_extract_spec_blocks`

- Claim: plan.toml has `[template_vars.segments."Files to Modify"]` on line 86 — should be `sections` not `segments`
  Source: .docfence/types/plan.toml:86
  Confidence: 1.0
  Implication: This typo means the Files to Modify section scaffold config (fill text, match rules) is never read during scaffold generation

### Gaps
- No existing test suite to validate changes against — verification will rely on manual `docfence validate` and `docfence new` commands
- spec_coverage section matching (heading → spec block) needs heuristics for ambiguous cases (e.g., two sections with similar names) — may need refinement after testing

## Verification

```spec
type: plan
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
match:
  has_verify_command: '^```bash'
  has_expected: '# Expected:'
  min_2_tests: '# Test \d'
```

```bash
# Test 1: Typo fix — scaffold includes Files to Modify section config
docfence new plan --output /tmp/test-plan.md
cat /tmp/test-plan.md | grep -A2 "Files to Modify"
# Expected: Shows section with spec block and df-todo, with fill text and match rules from plan.toml

# Test 2: New scaffold has spec_checksum in frontmatter
head -10 /tmp/test-plan.md | grep spec_checksum
# Expected: Line like "spec_checksum: <8-char-hex>"

# Test 3: Validate fresh scaffold — checksum matches
docfence validate /tmp/test-plan.md
# Expected: No spec_checksum errors (other errors like unfilled blocks are expected on fresh scaffold)

# Test 4: Remove a spec block, validate — checksum mismatch detected
# Delete the Approach spec block from the scaffold, then validate
sed -i'' '/```spec/,/```/d' /tmp/test-plan.md  # remove first spec block
docfence validate /tmp/test-plan.md 2>&1 | grep spec_checksum
# Expected: Error message about spec_checksum mismatch

# Test 5: spec_coverage detects missing rule keys
# Remove match rules from a section spec block, validate
# Expected: Error listing missing rule keys from type definition

# Test 6: stamp --update-checksum refreshes checksum
docfence stamp --update-checksum /tmp/test-plan.md
# Expected: Success message, frontmatter spec_checksum updated

# Test 7: Validate an existing plan file (P10b)
docfence validate plans/P10b-fix-enumeration-commands.md 2>&1
# Expected: Reports missing spec blocks for sections that lack them (spec_coverage check)
```

## Bottom Line

```spec
type: plan
max_chars: 20000
banned_words: [TODO, TBD, placeholder]
match:
  has_recommendation: 'Recommendation:'
```

- Step 1 confidence: 1.0 (typo fix, verified)
- Step 2 confidence: 0.9 (checksum computation, straightforward hashlib)
- Step 3 confidence: 0.85 (spec_coverage requires heading-to-spec-block matching heuristic)
- Step 4 confidence: 0.9 (checksum validation, mirrors frontmatter check pattern)
- Step 5 confidence: 0.9 (scaffold frontmatter update, well-understood code path)
- Step 6 confidence: 0.85 (stamp flag extension, minor arg parsing)
- Step 7 confidence: 1.0 (SKILL.md text update)
- Average: 0.91
- Key risk: spec_coverage section-to-spec-block matching — section headings in markdown need to be matched to their nearest spec block; edge cases with same-named headings or missing headings may produce false positives
- Gaps: No automated test suite; heading-to-spec-block matching heuristic needs real-world testing
- Recommendation: proceed — all changes are incremental and reversible, with manual verification sufficient given the lack of a test framework

## Implementation Highlights

All 7 steps completed. Commit `d87c971`.

**Branch note:** Implementation was committed directly to `main` (commits `6275cc5`–`6fb0f17`). Should have been on a feature branch. Move to branch before further work. Typo fix, spec_checksum in loader/validator/scaffold, spec_coverage in validator, stamp --update-checksum, SKILL.md H11.

**Extra changes beyond plan:**
- `_extract_headings` skips fenced code blocks — `# Test 1:` in ```bash no longer detected as headings
- Heading-to-spec-block matching uses ±10 line tolerance (approximate line numbers from parser)
- `SpecBlock` dataclass gained `raw_toml` field — checksum needs original TOML
- `stamp --approved-by` flag + `_log_checksum_update()` writes `.docfence/checksum.log`
- Iron law banner on `--update-checksum` — agents must never run without user permission
- `spec_checksum` hint suppressed when document has unfilled placeholders
- Extra rule keys (inherited defaults) reported as hints, not errors
**Review fixes (post-review):**
- Blocker fix: `cmd_stamp` fallback now uses `last_validated` anchor when `depends_on` is missing; guards against `None` checksum value
- Guard added: stale `spec_checksum` with zero spec blocks now raises error (not silently ignored)
- `from __future__ import annotations` added to loader.py for Python 3.9 compat
- `SpecBlock.raw_toml` and other fields given defaults for forward compatibility
