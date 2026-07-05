# P14 — docfence validate: automatically compare checksum of plan against checksum of template guidance (stub)

- Problem: `docfence validate` compares checksum of generated plan against computed checksum. However it does not compare checksum to source of truth - existing template toml file. If agent silently updated checksum in frontmatter of generated plan, then the drift will not be caught.
- Example: 
- Goal: 
- Out of scope (for now): 
