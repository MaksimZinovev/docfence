# Grounded Plan: Scaffold Markdown with df-todo Placeholder Blocks

## Evidence Pack

- **Claim**: Current `_template()` is a single hardcoded f-string that only interpolates `doc_type`. It generates a generic frontmatter + spec block structure with "Your content here." as the only body placeholder.
  **Source**: `docfence.py:258` — `cx definition --name _template`
  **Confidence**: 1.0
  **Implication**: Replacement is straightforward — the function has 2 callers (`cmd_new` + referenced by itself). No other code depends on the template format string.

- **Claim**: `_extract_spec_blocks()` uses regex `r"```spec\n(.*?)```"` to find spec blocks. For each block, sibling text is everything from the block's end to the next spec block's start (or EOF). Document-scoped blocks get the full text with spec blocks stripped.
  **Source**: `core/loader.py:114` — `cx definition --name _extract_spec_blocks`
  **Confidence**: 1.0
  **Implication**: When a `df-todo` fenced block sits ABOVE a section-level ```spec block, it falls into the gap between the PREVIOUS spec block and the current one. The document-scope spec block (which strips only ```spec fences) still sees df-todo in its sibling text. Section-scope spec blocks see only content after themselves — df-todo is NOT in their sibling text. This is the desired behavior.

- **Claim**: `load_doc()` calculates `effective_sibling` for scope=document as `_SPEC_BLOCK_RE.sub("", text).strip()`. This strips only ```spec fences, leaving ```df-todo blocks intact.
  **Source**: `core/loader.py:139` — `cx definition --name load_doc`
  **Confidence**: 1.0
  **Implication**: A `placeholders` rule on the document-scope spec block will find all ```df-todo blocks in the full text. Section-level rules won't see them. Author workflow (remove df-todo → write content) doesn't disturb section-level validation.

- **Claim**: `_parse_kv()` parses key/value TOML-like syntax from spec block text. It handles scalars, inline lists, sub-blocks, and quoted strings. It strips `#` comment lines.
  **Source**: `core/loader.py:13` — `cx definition --name _parse_kv`
  **Confidence**: 1.0
  **Implication**: If we later extract ```df-todo blocks (for IDE tooling, auto-fill), we can reuse `_parse_kv` to parse their `name`, `fill`, `action`, `require`, `hint` fields. Same parser, different block type. No new parsing code needed.

- **Claim**: `RULES` dict maps rule names to callables: `max_chars`, `banned_words`, `validate`, `required_sections`, `match`. Each function takes `(text, value, cfg)` and returns `list[str]` errors.
  **Source**: `core/rules.py:92` — `cx definition --name RULES`
  **Confidence**: 1.0
  **Implication**: Adding `rule_placeholders` follows the exact same signature. Register as `RULES["placeholders"] = rule_placeholders`. No structural changes needed.

- **Claim**: `TypeDef` dataclass has fields: `name`, `statuses`, `required_fields`, `defaults`, `source`. No `template_vars` field exists yet. Type TOML files (exploration.toml, feature.toml) define `defaults` with `max_chars`, `banned_words`, `required_sections`.
  **Source**: `core/types.py:12` — cx definitions; `.docfence/types/*.toml`
  **Confidence**: 1.0
  **Implication**: Adding `template_vars` to TypeDef requires: (1) new field with `field(default_factory=dict)`, (2) parse `[template_vars]` section from TOML, (3) use in cmd_new as render context for frontmatter and per-section scaffold generation.

- **Claim**: `validate_doc()` merges rule values: block-level explicit rules win; type-level defaults fill gaps. Inherited defaults produce a "warn" level issue. The `NON_RULE_KEYS` set excludes `type`, `scope`, `bid`, `status`, `owner`, `depends_on`, `_parse_error` from rule processing.
  **Source**: `core/validator.py:49` — `cx definition --name validate_doc`; `core/validator.py:20` — `cx definition --name NON_RULE_KEYS`
  **Confidence**: 1.0
  **Implication**: Adding `placeholders` to type defaults works automatically — it follows the same merge path as `max_chars` and `banned_words`. If a spec block explicitly declares `placeholders: [...]`, it wins. Otherwise, type defaults fill the gap.

- **Claim**: CLI uses raw `match args` in `main()`. Subcommands: `validate`, `new`, `types`, `stamp`. The `new` subcommand currently takes exactly one positional arg (`doc_type`).
  **Source**: `docfence.py:343` — `cx definition --name main`
  **Confidence**: 1.0
  **Implication**: Adding `--output <path>` and `--set key=value` flags requires either: (A) manual arg parsing after `match`, or (B) switching to `argparse`. Option A is simpler for minimal changes; option B is more extensible.

- **Claim**: Project has no runtime dependencies (pyproject.toml lists only `setuptools` for build). Jinja2 is locally installed but NOT a declared dependency.
  **Source**: `pyproject.toml`; `pip list | grep jinja2`
  **Confidence**: 1.0
  **Implication**: No new runtime dependencies needed — we're NOT using template engine, just string generation and TOML-like parsing (already built in via `_parse_kv` and `tomllib`).

### Gaps

- **Exact df-todo block extraction for tooling**: Currently only spec blocks are extracted. For the `placeholders` rule, simple regex matching suffices. For future IDE support / auto-fill, we'd need `_extract_todo_blocks()` — but that's out of scope for this plan.
- **Frontmatter placeholder mechanism**: Fenced blocks can't go inside YAML frontmatter. Required fields like `owner` that need filling must be handled separately (pre-rendered from CLI args / type vars, or validated by existing `required_fields` check).
- **match rule in scaffold**: The `match` rule requires type-specific pattern definitions. Neither exploration.toml nor feature.toml currently define match patterns. The scaffold will include match only when type defaults define it.

### Sources Used
- `docfence.py` — `_template`, `cmd_new`, `main`, `_load_types_list`
- `core/loader.py` — `_extract_spec_blocks`, `load_doc`, `_parse_kv`, `SpecBlock`, `ParsedDoc`
- `core/rules.py` — `RULES`, all rule functions
- `core/types.py` — `TypeDef`, `load_types`
- `core/validator.py` — `validate_doc`, `validate_path`, `Issue`, `NON_RULE_KEYS`
- `.docfence/types/exploration.toml`, `.docfence/types/feature.toml`
- `pyproject.toml`

---

## Grounded Plan: Scaffold with df-todo Placeholder Blocks

**Goal**: Enhance `docfence new` to generate richer scaffolded Markdown files with structured ` ```df-todo ` placeholder blocks (TOML format), inline fill instructions, and spec-block validation rules derived from type defaults. Add a `rule_placeholders` that detects unfilled `df-todo` blocks and reports them as error-level issues.

**Uncertainty Level**: low — all code patterns are local, well-understood, and follow existing conventions.

**Evidence Sources Used**: codebase (cx definitions + file reads)

### Phase 1: Add `rule_placeholders` validation rule

**Step 1**: Add `rule_placeholders` function to `core/rules.py`
- **Evidence**: RULES dict pattern — each rule is `fn(text, value, cfg) -> list[str]` (Source: `core/rules.py:92`)
- **Confidence**: 1.0
- **Details**: Function searches `text` for any of the regex patterns in `value` (a list of pattern strings). For each match, returns an error message like `"unfilled placeholder block 'df-todo' found — delete it and replace with content"`. Register in `RULES["placeholders"] = rule_placeholders`.

**Step 2**: Add `placeholders` default to type TOML files
- **Evidence**: Type TOML files define `[defaults]` with rule keys (Source: `.docfence/types/exploration.toml`)
- **Confidence**: 1.0
- **Details**: Add `placeholders = ["```df-todo"]` to the `[defaults]` section of each existing type TOML. This means every type automatically inherits placeholder detection. The pattern ````df-todo` is a literal string search, not regex — the `rule_placeholders` implementation should do `re.escape(pattern)` before compiling, or use plain string search for simplicity.

### Phase 2: Enhance `cmd_new` scaffold generator

**Step 3**: Add `template_vars` field to `TypeDef` and parse from TOML
- **Evidence**: TypeDef dataclass, load_types() parses TOML (Source: `core/types.py:12`, `core/types.py:34`)
- **Confidence**: 1.0
- **Details**: Add `template_vars: dict = field(default_factory=dict)` to TypeDef. In `load_types()`, parse `[template_vars]` from TOML if present:
  ```toml
  [template_vars]
  id = "EXPLORATION-001"
  title = "Exploration Title"

  [template_vars.sections.Background]
  fill = "[REPLACE] Why this exploration is needed — delete this block and write your content"

  [template_vars.sections.Decision]
  fill = "[REPLACE] What was decided and why — delete this block and write your content"

  [template_vars.sections.Open Questions]
  fill = "[REPLACE] List unresolved questions or items needing investigation — delete this block and write your content"
  ```
  This is the **single source of truth** for section structure AND per-section placeholder instructions.
  The scaffold generator reads `template_vars.sections` to build both the headings and the `fill` text
  inside each `df-todo` block. No instruction text is hardcoded in the generator — it all comes from the type TOML.

**Step 4**: Replace `_template()` with `_generate_scaffold()`
- **Evidence**: Current `_template()` is a single f-string (Source: `docfence.py:258`)
- **Confidence**: 1.0
- **Details**: New function takes `doc_type: str, type_def: TypeDef | None, output: Path | None, overrides: dict` and produces a full scaffolded document:
  1. **Frontmatter**: Pre-rendered from `type_def.template_vars` merged with `overrides`. No placeholders in frontmatter — every field has a concrete value (e.g., `owner: human` if not provided via `--set`).
  2. **Document-level spec block**: Explicit rule entries from `type_def.defaults` (hybrid: template lists them, defaults fill gaps). Always includes `placeholders: ["```df-todo"]`.
  3. **Sections**: For each section in `type_def.template_vars.sections` (falling back to `type_def.defaults.required_sections`), generate:
     - `## Section Name` heading
     - ` ```df-todo ` block ABOVE the spec block with `name` and `fill` fields only. **No `require`**, **no `action`** — the `[REPLACE]` prefix in `fill` already communicates the required operation. The `fill` value comes from `template_vars.sections.<Name>.fill` (single source of truth).
     - ` ```spec ` block with type-relevant rules from defaults
  4. Write to `output` path or stdout.

**Step 5**: Update `cmd_new()` to use the new generator and CLI flags
- **Evidence**: Current `cmd_new` is 4 lines (Source: `docfence.py:306`)
- **Confidence**: 1.0
- **Details**:
  - New signature: `cmd_new(doc_type, output=None, overrides=None)`
  - Load TypeDef via `load_types()`, resolve the type
  - Call `_generate_scaffold(doc_type, type_def, output, overrides)`
  - If `output` given, write file; otherwise print to stdout
  - CLI parsing in `main()`: add cases for `["new", doc_type, "--output", path]` etc.

### Phase 3: CLI arg parsing

**Step 6**: Extend `main()` to handle `--output` and `--set` flags on the `new` subcommand
- **Evidence**: Current `match args` pattern (Source: `docfence.py:343`)
- **Confidence**: 0.85
- **Details**: Add manual parsing after matching `["new", ...]`:
  - Pop `--output` and its following arg from the remaining args
  - Pop `--set` key=value pairs from the remaining args
  - First remaining positional is `doc_type`
  - Keep `match args` structure for other subcommands (no argparse migration needed for this scope)
  - If this feels fragile, switch to argparse — but for 2 flags, manual parsing is proportionate.

### Phase 4: Scaffolded output format — concrete template

**Step 7**: Define the canonical scaffold output for `exploration` type
- **Evidence**: exploration.toml defines required_sections=[Background, Decision, Open Questions], max_chars=5000, banned_words=[TODO, TBD] (Source: `.docfence/types/exploration.toml`)
- **Confidence**: 1.0
- **Details**: Generated output:

  ````markdown
  ---
  id: EXPLORATION-001
  type: exploration
  status: draft
  owner: human
  depends_on: []
  last_validated: ~
  ---

  # Exploration Title

  ```spec
  scope: document
  type: exploration
  required_sections: [Background, Decision, Open Questions]
  max_chars: 5000
  banned_words: [TODO, TBD]
  placeholders: ["```df-todo"]
  ```

  ## Background

  ```df-todo
  name = "background"
  fill = "[REPLACE] Why this exploration is needed — delete this block and write your content"
  ```

  ```spec
  type: exploration
  max_chars: 1500
  banned_words: [TODO, TBD]
  placeholders: ["```df-todo"]
  ```

  ## Decision

  ```df-todo
  name = "decision"
  fill = "[REPLACE] What was decided and why — delete this block and write your content"
  ```

  ```spec
  type: exploration
  max_chars: 1500
  banned_words: [TODO, TBD]
  placeholders: ["```df-todo"]
  ```

  ## Open Questions

  ```df-todo
  name = "open-questions"
  fill = "[REPLACE] List unresolved questions or items needing further investigation — delete this block and write your content"
  ```

  ```spec
  type: exploration
  max_chars: 1000
  banned_words: [TODO, TBD]
  placeholders: ["```df-todo"]
  ```
  ````

### Decision Points

- **df-todo ABOVE spec block**: Chosen for three reasons:
  1. **Author reading flow**: Instruction (what to write) comes before rules (how it'll be validated). Natural top-down reading.
  2. **Clean validation separation**: `_extract_spec_blocks()` extracts ```spec blocks and calculates sibling text as everything AFTER each spec block until the next. A df-todo block ABOVE a section's spec block sits in the gap between the PREVIOUS spec block and the current one. This means:
     - **Document-scope** spec block (`scope: document`) strips only ```spec fences from full text → df-todo text IS visible → `placeholders` rule catches all unfilled df-todo blocks.
     - **Section-scope** spec blocks see only content AFTER themselves → df-todo is NOT in their sibling text → no df-todo artifacts pollute section-level rule checks (max_chars, banned_words, etc.).
  3. **Replacement is safe**: When the author deletes a df-todo block and writes content below the spec block, the section-level sibling text changes from empty → actual content (correct). The document-level sibling text loses the df-todo pattern → placeholders rule passes (correct). No spec block is disturbed. (Evidence: `_extract_spec_blocks` in `core/loader.py:114`, `load_doc` in `core/loader.py:139`)

  **Step-by-step validation flow after scaffold generation:**
  1. `docfence validate` runs on the fresh scaffold.
  2. Document-scope spec block scans full text → finds ````df-todo` → `rule_placeholders` reports **error** for each.
  3. Section-scope spec blocks scan their sibling text (empty) → `rule_max_chars` passes, `rule_required_sections` checks headings (present) → **pass**.
  4. Author deletes df-todo block, writes content below spec block.
  5. `docfence validate` runs again.
  6. Document-scope spec block scans full text → no ````df-todo` found → `rule_placeholders` **passes**.
  7. Section-scope spec blocks scan sibling text (now has content) → `rule_max_chars`, `rule_banned_words`, etc. validate normally.
- **No `action` field**: The `[REPLACE]` prefix in `fill` already communicates the required operation — delete the block and write content. Adding `action = "remove"` would be redundant. If machine-readable action markers are needed in the future, they can be added as an optional field then.
- **Frontmatter pre-rendered**: Fenced blocks can't exist inside YAML. Required frontmatter fields get values from `template_vars` or `--set` overrides. Missing overrides fall back to type defaults or generic stubs (`owner: human`).
- **No `require` in df-todo blocks**: Validation constraints (min length, char limits, etc.) belong exclusively in ```spec blocks. The df-todo block is author guidance only — `name` identifies the slot, `fill` tells the author what to write, `action` signals the required operation. Duplicating constraints creates maintenance burden and confusion about which source is authoritative.
- **Hybrid spec blocks**: Template (generator) explicitly includes rules from `type_def.defaults`. If a future TOML adds a rule not in the scaffold's spec block, `validate_doc` fills the gap with an "inherited" warning. Best of both worlds.
- **No template engine**: String generation from TypeDef is sufficient for current needs. If Jinja2 templates are added later, the ` ```df-todo ` block convention remains valid — template output and placeholder blocks are orthogonal.

### Risks & Mitigations

- **Risk**: `rule_placeholders` pattern ````df-todo` could false-match in prose or code examples discussing the tool.
  **Mitigation**: The pattern is specific (fenced code block opening). Content inside markdown code spans (inline `code`) does NOT match. If false positives occur, the pattern can be tightened to `r"```\s*df-todo"` or require a newline after.

- **Risk**: `--set key=value` CLI parsing is manual and may not handle edge cases (spaces in values, etc.).
  **Mitigation**: Start simple — values with spaces must be quoted: `--set "title=My Long Title"`. Document the format. If it proves error-prone, migrate to argparse.

- **Risk**: `template_vars` sections in type TOML files may not match `required_sections` or other defaults, causing inconsistent scaffold output.
  **Mitigation**: `_generate_scaffold()` derives sections from `required_sections` (already in defaults) first; `template_vars.sections` overrides only when explicitly set. Single source of truth.

### Verification Checkpoint

- **After Phase 1**: Run `docfence validate` on an existing doc with a manually added ` ```df-todo ` block. Should report error: "unfilled placeholder block 'df-todo' found — delete it and replace with content".
- **After Phase 2**: Run `docfence new exploration`. Should output scaffold with df-todo blocks, spec blocks with all 5 rule types, and pre-rendered frontmatter.
- **After Phase 3**: Run `docfence new exploration --output test.md --set owner=alice`. Should write file with `owner: alice` in frontmatter.
- **After Phase 4**: Validate generated file with `docfence validate test.md`. Should show placeholder errors for every unfilled df-todo block.

---

## Bottom Line

- **Per-step confidence**: 0.96
- **Key risk**: `rule_placeholders` false positives on ````df-todo` pattern in prose — mitigated by specific fenced-block regex
- **Gaps**: Future `df-todo` block extraction for IDE tooling / auto-fill; no frontmatter placeholder mechanism (handled by required_fields validation instead)
- **Recommendation**: Proceed — all patterns are locally verifiable, no external dependencies, and the changes follow existing code conventions precisely.

---

## Future Notes (out of scope, for reference)

- **Jinja2 templates**: If added later, ` ```df-todo ` blocks remain valid in template output. Templates would control section structure / frontmatter; df-todo blocks control author guidance. Orthogonal features.
- **df-todo block extraction**: Add `_extract_todo_blocks()` to `core/loader.py` reusing the same `_extract_spec_blocks` pattern but matching ` ```df-todo `. Parse with `_parse_kv`. Enables IDE plugins, auto-fill tools, batch placeholder reports.
- **Open tag extension**: Self-contained df-todo can be extended to `<df-todo>...<example>...</df-todo>` XML format if richer instructions are needed later. The fenced-block format provides a smooth migration path: extracted content → rendered as XML tags.