# Changelog — mama-integrations

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); semver. Every release declares supported upstream `mama` versions (see [compatibility.md](compatibility.md)).

## [0.1.1] — 2026-11-05

### Fixed

- `contracts/assessment-import.schema.json`: the `scores` object declared
  `additionalProperties: false` with no named properties, which rejects
  every valid upstream record (D1–D6 treated as "additional"). The six
  dimension properties are now declared (integer 0–5 each); `required` and
  the `D[1-6]` propertyNames guard are unchanged. Found by the
  mama-conformance fixture suite.

## [0.1.0] — 2026-11-04

### Added (initial scaffold, CR MAMA-ORG-CR-001)

- Version-gated importers:
  - `load_ledger()` — upstream Autonomy Ledger (YAML), schema 2 supported; schema 1 → retired-scale warning; missing `schema` → pre-versioning warning; unknown schema → fail closed
  - `import_assessment()` — upstream `autonomy-score --json` records; ruleset-version gate; strict pass-through (no recomputation)
  - `load_mappings()` / `check_linkage()` — MAMA use-case ↔ `mama` unit/domain/contract linkage
- `export_ledger()` — schema-2 ledger writer
- Interface JSON Schemas in `contracts/` (assessment, ledger, use-case mapping)
- Synthetic examples and a pytest suite covering fail-closed behavior
- Compatibility matrix and support policy

### Supported upstream versions

- Ruleset `2.0.0` (MAJOR 2) — supported; `1.*` retired (warn); `≥3` unsupported (fail closed)
- Ledger schema `2` — supported; `1` retired (warn); absent = pre-versioning (warn); `≥3` unsupported (fail closed)

[0.1.0]: https://github.com/Measuring-Automation-Managing-Autonomy/mama-integrations/releases/tag/v0.1.0
