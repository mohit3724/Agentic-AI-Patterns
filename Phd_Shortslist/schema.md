# JSON Schemas

See `schema.md` for the classic project; this version uses the same schemas for
input student profiles and output shortlists. The most important invariants:

- `target_countries` in the output matches the input.
- Every recommendation has at least one evidence item.
- `tier` ∈ {"reach", "target", "safety"}.
- `country` for each supervisor is in `target_countries`.
