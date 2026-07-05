# P13 — docfence validate: actionable guidance (stub)

- Problem: `docfence validate` reports issues but gives agents little actionable help to fix them.
- Example: `banned_words` does a case-insensitive substring match, so prose mentioning `df-todo` trips the `TODO` ban with no hint why; `placeholders` trips on literal fence strings inside bash comments; `has_deepwiki` forces `: Yes` even when the repo isn't indexed.
- Goal: make each error/hint point at the offending substring, explain the match, and suggest a concrete fix or an honest way to satisfy the rule.
- Out of scope (for now): full redesign of rule diagnostics — details to be added in a later session.
- Source example: P12 plan validation blockers (this repo, plans/P12-new-bare-preview.md).
