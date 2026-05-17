Yes. The current `RULES` dict is already halfway there — it's a registry of `name → function`. The missing piece is a way to register functions from outside `rules.py` without editing it.

Three layers of extensibility, from simple to full:

---

**Layer 1 — Python plugin files in `.docfence/rules/`**

Drop a `.py` file in `.docfence/rules/`, docfence loads it at startup and calls a `register(rules: dict)` function if it exists:

```python
# .docfence/rules/section_check.py

import re

def rule_section(text, value, cfg):
    ...

def register(rules: dict):
    rules["section"] = rule_section
```

No core changes to add a rule. Your agent can write and drop plugin files. Works with stdlib only.

---

**Layer 2 — Rule discovery by convention**

Any function named `rule_*` in a plugin file gets auto-registered under its suffix — `rule_section` → `"section"`. No `register()` boilerplate needed:

```python
# .docfence/rules/my_rules.py

def rule_section(text, value, cfg): ...
def rule_min_chars(text, value, cfg): ...
# both auto-registered
```

Simpler to write, slightly more magic.

---

**Layer 3 — Type-local rules (most self-contained)**

A type definition can reference a rule file path directly:

```toml
# research.toml
[rules]
section = ".docfence/rules/section_check.py::rule_section"
```

The rule travels with the type, not globally. Best for rules that only make sense for one doc type.

---

**My recommendation for your setup:** Layer 1 + Layer 2 combined — auto-discover `rule_*` functions but also allow an explicit `register()` for rules that need a custom name. Layer 3 is useful later when your type definitions get richer.
