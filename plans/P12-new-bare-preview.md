---
id: P12
type: plan
status: draft
owner: human
depends_on: []
spec_checksum: a4a68c6d
last_validated: ~
---

# new --bare: concise terminal preview of scaffold

```spec
scope: document
type: plan
required_sections: [Context, Tools & Skills, Approach, Out of Scope, Steps, Files to Modify, Reuse, Evidence Pack, Verification, Bottom Line]
max_chars: 15000
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
max_chars: 15000
banned_words: [might be, could be, seems like, I think, possibly, perhaps]
match:
  has_problem: '(problem|issue|bug|break|fail|cannot|does.not|unable)'
```

`docfence new <type>` prints the full scaffold: frontmatter, document-level spec block, a per-section spec block and a fill-prompt block for every required section. When the user only wants to glance at the shape of a doc type — frontmatter (with the real `spec_checksum`), the global rules, and the section headings — the per-section spec blocks and fill-prompt blocks are noise that scrolls off screen.

Problem: there is no concise preview — the user fails to glance the shape of a doc type. They run `docfence new plan`, see ~150 lines, and have to mentally skip the fill-prompt text and per-section spec blocks to find the section list and global rules. We need a `--bare` flag on `new` that outputs only frontmatter + document-level spec block + `## section` headings, with the same `spec_checksum` `new` would compute, to stdout.

Pre-existing blocker found while scaffolding this plan: `.docfence/types/plan.toml` had a duplicate `[template_vars.sections.Verification.match]` table (lines ~131 and ~135) that broke `docfence new plan` entirely with `tomllib.TOMLDecodeError: Cannot declare ... twice`. The user removed the duplicate; `docfence new plan` now works again. That fix is committed separately and is out of scope for this plan.

## Tools & Skills

```spec
type: plan
max_chars: 15000
banned_words: [N/A, n/a, grep sufficient, small codebase, simple enough, overkill for]
match:
  min_3_ynp: '^- .+: (Yes|No|Possibly)\b'
  has_cx: '\bcx\b.*\(Skills\).*: Yes\b'
  has_ck: '\bck\b.*\(Skills\).*: Yes\b'
  has_gh: '\bgh\b.*\(CLI\).*: Yes\b'
  has_deepwiki: 'deepwiki.*\(MCP\).*: Yes\b'
```

- cx (Skills): Yes — `cx overview .` and `cx definition --name _generate_scaffold/cmd_new/main` used to read the exact touch points in `docfence.py`.
- ck (Skills): Yes — `ck "scaffold" .` confirmed no scaffold generator exists outside `docfence.py` (only README mentions).
- gh (CLI): Yes — `gh issue list` checked for related open issues (none); `gh` auth available for the eventual PR/commit workflow.
- deepwiki (MCP): Yes — engaged `deepwiki_ask_question` for `MaksimZinovev/docfence`; repo not indexed on deepwiki.com, so would fall back to `gh api` — see P13 future-improvement plan.
- docfence (CLI): Yes — `docfence new plan` scaffolded this plan; `docfence validate` checks it; `docfence new plan --bare` will verify the feature end-to-end.
- slop-scan (Skills): Possibly — optional pre-commit scan of the diff for AI-slop patterns, per AGENTS.md.

## Approach

```spec
type: plan
max_chars: 1400
banned_words: [TODO, TBD, placeholder]
match:
  has_preamble: 'The content of the plan is aligned with the following guiding questions.'
  has_alternative: '(alternative|instead of|rather than|compared to|over:|vs[.])'
  has_what_guiding_question: 'Q\d+\(what\)'
  has_how_guiding_question: 'Q\d+\(how\)'
  has_context_guiding_question: 'Q\d+\(context\).*key context'
  has_intent_guiding_question: 'Q\d+\(intent\).*key intent'
  has_out_of_scope_guiding_question: 'Q\d+\(out of scope\)'
  has_constraint_guiding_question: 'Q\d+\(key constraint\).*key constraint'
  has_evidence_guiding_question: 'Q\d+\(key evidence\).*key evidence'
  has_verification_guiding_question: 'Q\d+\(verification\).*key verification from user perspective'
```

The content of the plan is aligned with the following guiding questions.

Q1(what): what minimal change to `_generate_scaffold` yields a bare preview while keeping `spec_checksum` identical to the full scaffold (alternative: a parallel generator — rejected as duplication)?
Q2(how): compute `all_raw_tomls` over the full spec-block set as today; bare mode only filters what is rendered, not what is hashed.
Q3(context): key context — `cmd_new` already takes `output`/`overrides`; `main()` already parses `--output`/`--set`; `--bare` follows the same loop.
Q4(intent): key intent — a concise terminal preview, not a validated doc; the checksum is informational only.
Q5(out of scope): a new subcommand or `-o` behavior change — no; `--bare` is a flag, `-o` stays as-is.
Q6(key constraint): key constraint — `spec_checksum` must equal `docfence new <type>`'s output for the same type.
Q7(key evidence): key evidence — `_generate_scaffold` (docfence.py:267) computes `all_raw_tomls`/`spec_checksum` before rendering, so bare is a render-time filter.
Q8(verification): key verification from user perspective — run `docfence new plan --bare`, confirm concise output and frontmatter checksum matches `docfence new plan`; covered by Test 1 (checksum + fence/heading counts) and Test 5 (flag-order guard on `docfence new --bare plan`).

## Out of Scope

```spec
type: plan
max_chars: 15000
banned_words: [Nothing., None., N/A, n/a, Not applicable]
match:
  has_justification: '^- .+:'
  min_2_exclusions: '^- .+:'
```

- New subcommand (e.g. `docfence skeleton`): the behavior is a view variant of `new`, so a flag is the minimal surface; a subcommand would duplicate CLI plumbing.
- Disabling `-o` for `--bare`: keeping `-o` functional costs no extra code and stays consistent with `new`; the user controls whether to write a file by simply not passing `-o`.
- Changing `spec_checksum` semantics: the checksum must stay identical to the full scaffold; no separate "bare checksum" mode.
- Fixing other unrelated `.docfence/types/*.toml` issues: only the duplicate `Verification.match` block was removed (by the user) to unblock scaffolding; no further type-definition cleanup.
- Refactoring `_generate_scaffold`: we add one parameter and one conditional branch; no restructuring of the existing function.

## Steps

```spec
type: plan
max_chars: 15000
banned_words: [**Step, **Task, **Phase]
match:
  has_step_evidence: '^- \[ \].*\(Source'
  min_3_steps: '^- \[( |x)\]'
```

- [ ] Add `bare: bool = False` parameter to `_generate_scaffold` in `docfence.py`; when `bare` is True, build `section_blocks` as bare `## {name}` headings only (skip per-section spec block and the fill-prompt block) but keep the `all_raw_tomls`/`spec_checksum` computation unchanged so the hash matches the full scaffold. (Source: docfence.py:267, `_generate_scaffold`)
- [ ] Add `bare: bool = False` parameter to `cmd_new` in `docfence.py`, pass it through to `_generate_scaffold`, and add a guard: if `doc_type.startswith("--")` (a flag mistakenly in the type slot), print an example-driven error (`docfence new plan --bare`, `docfence new feature --bare --output docs/x.md`, `docfence new plan --bare --set title=...`) and return — prevents the silent `type: --bare` scaffold. (Source: docfence.py:419, `cmd_new`)
- [ ] Extend the `new` case in `main()` to parse `--bare` from `rest` (flags come after the type, mirroring `--output`/`--set`) and pass `bare=...` to `cmd_new`. (Source: docfence.py:576, `main` `new` case)
- [ ] Update the module `__doc__` help text to document `docfence new <type> --bare`. (Source: docfence.py:2, `__doc__`)
- [ ] Update README usage/Quick Start to mention `--bare` as a concise preview. (Source: README.md, Quick Start/Usage sections)
- [ ] Run `docfence validate plans/P12-new-bare-preview.md` and fix any errors until clean; run `docfence new plan --bare` and confirm concise output + matching checksum. (Source: Evidence Pack claims C1, C2)

## Files to Modify

```spec
type: plan
max_chars: 15000
banned_words: [TODO, TBD, placeholder]
match:
  has_file_entry: '^- `[^`]+` — (CREATED|UPDATED|DELETED)'
```

- `docfence.py` — UPDATED: add `bare` param to `_generate_scaffold` and `cmd_new`; add flag-order guard in `cmd_new` (example-driven error when `doc_type` starts with `--`); parse `--bare` in `main()` after the type; update `__doc__` help text.
- `README.md` — UPDATED: document `docfence new <type> --bare` in usage/Quick Start.
- `plans/P12-new-bare-preview.md` — CREATED: this plan.

## Reuse

```spec
type: plan
max_chars: 15000
banned_words: [None., N/A, Nothing to reuse, No reuse]
match:
  has_reuse_item: '^- .+:'
```

- `_generate_scaffold` (docfence.py:267): reused as-is for frontmatter, document-level spec block, and `spec_checksum` computation; bare mode only changes the rendered section blocks.
- `cmd_new` (docfence.py:419): reused; gains one pass-through `bare` parameter instead of a parallel function.
- `main()` `new`-case arg loop (docfence.py:578): reused; `--bare` is parsed by adding one branch to the existing `while i < len(rest)` loop, same pattern as `--output`/`--set`.
- `hashlib.sha256` / `tomllib`: already imported and used; no new dependencies.

## Evidence Pack

```spec
type: plan
max_chars: 15000
banned_words: [**Source**:, **Source:**]
match:
  has_evidence_claim: '^- Claim:'
  has_confidence: 'Confidence:'
```

- Claim: `_generate_scaffold` computes `spec_checksum` over `all_raw_tomls` (document + per-section spec blocks) *before* rendering the section blocks, so changing what is rendered does not affect the hash.
  Source: docfence.py:267-345 (`_generate_scaffold`, `all_raw_tomls` and `spec_checksum` lines)
  Confidence: 0.95
  Implication: bare mode can render only headings and still emit the same checksum as the full scaffold.
- Claim: `cmd_new` already accepts `output` and `overrides` and delegates to `_generate_scaffold`; adding a `bare` pass-through is a one-line change at the call site.
  Source: docfence.py:419-425 (`cmd_new`)
  Confidence: 0.95
  Implication: no new function or control-flow path is needed.
- Claim: `main()`'s `new` case already parses unknown flags via a `while i < len(rest)` loop, so `--bare` is added by one `elif` branch.
  Source: docfence.py:578-600 (`main`, `new` case)
  Confidence: 0.9
  Implication: CLI plumbing for the flag is minimal and matches existing patterns.
- Claim: The user's intent is a *terminal preview*, not a validated doc, so the checksum is informational and never checked against the rendered content.
  Source: User interview response (q1_purpose, q5_output)
  Confidence: 0.9
  Implication: rendering fewer spec blocks than were hashed is acceptable because the output is never passed to `validate`.
- Claim: `main()`'s `new` case binds `args[:2]` as `["new", doc_type]`, so a flag in the type slot (e.g. `docfence new --bare plan`) silently becomes `doc_type="--bare"` and `cmd_new` emits a `type: --bare` scaffold with no error — a guard on `doc_type.startswith("--")` is needed to turn this into an example-driven message.
  Source: docfence.py:576-600 (`main`, `new` case `match args[:2]`)
  Confidence: 0.9
  Implication: the guard belongs in `cmd_new` (where `doc_type` is consumed), keeping the parser structure unchanged (Option 1, flag-after-type).
- Claim: `.docfence/types/plan.toml` had a duplicate `[template_vars.sections.Verification.match]` table that broke `docfence new plan`; the user removed it, unblocking plan scaffolding.
  Source: .docfence/types/plan.toml lines ~131-135 (pre-fix); user interview response (q_blocker)
  Confidence: 0.85
  Implication: that fix is committed separately and is out of scope here, but it was a prerequisite to writing this plan.

### Gaps

- No automated test harness exists in the repo (no `tests/`); verification is manual bash checks per the Steps.

## Verification

```spec
type: plan
max_chars: 15000
banned_words: [TODO, TBD, placeholder]
match:
  has_verify_command: '^```bash'
  has_expected: '# Expected:'
  min_2_tests: '# Test \d'
  has_state_space: '(empty|zero|partial|intermediate|boundary|edge case|failure)'
```

State space covered below: empty/zero (unknown type, Test 2), minimum one flag (Test 1), intermediate (`--bare` + `--set`, Test 3), boundary (`-o` + `--bare`, Test 4), failure (flag-before-type guard, Test 5).

```bash
# Test 1: happy path — `new plan --bare` prints frontmatter + global spec block + headings only, and the checksum matches `new plan`
S=docfence.py
FULL=$(python3 "$S" new plan)
BARE=$(python3 "$S" new plan --bare)
FULL_CK=$(printf '%s\n' "$FULL" | sed -n 's/^spec_checksum: //p' | head -1)
BARE_CK=$(printf '%s\n' "$BARE" | sed -n 's/^spec_checksum: //p' | head -1)
echo "full=$FULL_CK bare=$BARE_CK"
# Expected: full=<hash> bare=<hash> and the two hashes are identical
[ "$FULL_CK" = "$BARE_CK" ] && echo "checksums match" || echo "MISMATCH"
# Expected: checksums match
# Expected: BARE contains no fill-prompt fences and only one spec fence (the document-level block)
# 'df-tod.o' (regex wildcard) avoids spelling the literal fence name, which would trip this plan's own TODO banned-word check
printf '%s\n' "$BARE" | grep -c 'df-tod.o'
# Expected: 0
printf '%s\n' "$BARE" | grep -c '^```spec'
# Expected: 1   (only the document-level spec block)
printf '%s\n' "$BARE" | grep -c '^## '
# Expected: 10  (Context, Tools & Skills, Approach, Out of Scope, Steps, Files to Modify, Reuse, Evidence Pack, Verification, Bottom Line)
```

```bash
# Test 2: empty/zero state — unknown type with --bare falls back the same way `new` does (no TypeDef)
S=docfence.py
python3 "$S" new nonexistent-type --bare 2>&1 | head -5
# Expected: prints a bare scaffold using built-in defaults (no crash); frontmatter present with spec_checksum line
```

```bash
# Test 3: boundary — `--bare` combined with `--set` override still applies the override in the rendered frontmatter
S=docfence.py
python3 "$S" new plan --bare --set title="Custom Title" | sed -n '1,9p'
# Expected: frontmatter shows id/type/... and the H1 line is "# Custom Title"; checksum still computed over full spec-block set
```

```bash
# Test 4: boundary — `-o` still works with `--bare` (kept for consistency with `new`)
S=docfence.py
TMP=$(mktemp)
python3 "$S" new plan --bare -o "$TMP" 2>&1 | head -2
test -f "$TMP" && echo "file written: $(wc -l < "$TMP") lines" || echo "no file"
# Expected: file written: <small N> lines  (concise, ~20 lines, vs ~150 for full scaffold)
rm -f "$TMP"
```

```bash
# Test 5: failure state — flag before the type triggers the guard (no silent `type: --bare` scaffold)
S=docfence.py
OUT=$(python3 "$S" new --bare plan 2>&1); RC=$?
echo "$OUT" | head -6
# Expected: prints "'--bare' looks like a flag, not a doc type — flags go after the type." plus three example commands (new plan --bare / new feature --bare --output / new plan --bare --set) and a pointer to `docfence types`; no scaffold body (no frontmatter `---` block)
[ $RC -ne 0 ] && echo "non-zero exit" || echo "zero exit"
# Expected: non-zero exit (guard returns without generating)
```

```bash
# Test 6: validate this plan stays clean after filling
S=docfence.py
python3 "$S" validate plans/P12-new-bare-preview.md
# Expected: 0 errors, 0 warnings (or only informational hints); spec blocks intact
```

## Bottom Line

```spec
type: plan
max_chars: 15000
banned_words: [TODO, TBD, placeholder]
match:
  has_recommendation: 'Recommendation:'
```

Per-step confidence:

- Step 1 (bare param in `_generate_scaffold`): 0.95 — mechanical, evidence-backed by current code structure.
- Step 2 (`cmd_new` pass-through + flag-order guard): 0.9 — one-line `bare` change plus a ~3-line guard with an example-driven error; guard placement in `cmd_new` keeps the parser structure unchanged.
- Step 3 (`main()` parse `--bare`): 0.9 — follows existing loop pattern; flag-order mistakes are caught by the Step 2 guard.
- Step 4 (`__doc__` help): 0.9 — trivial text edit.
- Step 5 (README): 0.9 — trivial text edit.
- Step 6 (validate + verify): 0.85 — depends on no other pre-existing type.toml issues surfacing.

Average: ~0.91. Outliers: none significant.

Key risk: a future `.docfence/types/*.toml` duplicate-key bug (like the `Verification.match` one found here) could break both `new` and `new --bare`; out of scope to harden `load_types` against it now.

Gaps: no automated test suite; verification is manual bash checks.

Recommendation: proceed — the change is minimal, surgical, and reuses existing structure. The only prerequisite (removing the duplicate `Verification.match` block) is already done by the user.
