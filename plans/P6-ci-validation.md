# Plan: CI Integration for Plan Validation

Add a GitHub Actions workflow (or git hook) that runs `docfence validate plans/*.md` on PRs. Plans that don't pass validation block the PR. No code changes to DocFence — just a workflow file. This makes plan format enforcement structural: even if the planner agent skips self-validation, CI catches it.

**Files**: `.github/workflows/validate-plans.yml` (new workflow), `.docfence/types/plan.toml` (from Alternative A)

**Ref**: `docfence.py:cmd_validate` — exit code 1 on errors makes it CI-friendly. Use `git diff --name-only --diff-filter=ACM 'plans/*.md'` to only validate changed plans.