---
id: F-001
type: feature
status: active
owner: maksim
depends_on: []
last_validated: ~
---

# User Authentication API

```spec
scope: document
type: feature
required_sections: [Overview, API Design, Security]
max_chars: 5000
banned_words: [TODO, TBD, placeholder]
```

## Overview

We need a secure authentication API that supports JWT tokens and session-based auth for our REST API consumers.

## API Design

```spec
type: feature
max_chars: 1500
banned_words: [TODO, TBD, placeholder]
```

The auth endpoint will expose `POST /auth/login` and `POST /auth/refresh`. Tokens expire after 24 hours. Refresh tokens support sliding windows.

## Security

All tokens are signed with RS256. We rotate keys monthly. Rate limiting applies to all auth endpoints to prevent brute-force attacks.
