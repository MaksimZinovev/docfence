# Plan: Plan Status Gating via `docfence stamp`

Leverage the existing `statuses` field in plan type TOML. Update `docfence stamp` to also validate that `status` is `active` or `done` (not `draft`) before stamping. Planners set `status: draft` on scaffold, update to `active` when starting work, `done` when validation passes. This makes `stamp` a quality gate: a plan with unfilled sections can't be stamped because validation fails, and a draft plan can't be stamped because status is wrong.

**Files**: `docfence.py` `cmd_stamp()` (add status check), `.docfence/types/plan.toml` (already has `statuses`)

**Ref**: `docfence.py:cmd_stamp` already gates on zero errors — add `frontmatter["status"] not in ("active", "done")` as an additional blocker.