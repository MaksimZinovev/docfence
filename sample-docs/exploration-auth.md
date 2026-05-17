---
id: E-001
type: exploration
status: draft
owner: maksim
depends_on: [F-001]
last_validated: 2026-05-17T06:57:07+00:00
---

# Auth Provider Comparison

```spec
scope: document
type: exploration
required_sections: [Background, Decision, Open Questions]
max_chars: 5000
banned_words: [TODO, TBD]
```

## Background

We need to evaluate whether to build auth in-house or use a third-party provider like Auth0, Clerk, or Firebase Auth. Cost, flexibility, and compliance are the main factors.

## Decision

We'll go with building in-house using JWT + RS256. It gives us full control over the auth flow and avoids vendor lock-in.

## Open Questions

- What about passkey / WebAuthn support?
- Should we support social login providers?
