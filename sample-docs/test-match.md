---
id: M-001
type: feature
status: draft
owner: maksim
depends_on: []
last_validated: ~
---

# Market Research

```spec
scope: document
type: feature
required_sections: [Overview, Data]
max_chars: 5000
banned_words: [TODO, TBD]
```

## Overview

Users prefer mobile-first experiences for all daily tasks and need better dashboards.

## Data

```spec
type: feature
max_chars: 1000
match:
  data_point: "^- .{30,}$"
  source_link: "Source: https?://.+"
```

- Users increasingly prefer mobile-first experiences for all daily tasks
- Source: https://example.com/research/2024
