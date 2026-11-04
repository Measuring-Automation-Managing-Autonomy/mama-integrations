# Compatibility Matrix — upstream `mama`

**Status:** draft (adapter v0.1.0) · **Upstream canonical home:** [`emmanuel-a-otchere/measuring-and-managing-autonomy`](https://github.com/emmanuel-a-otchere/measuring-and-managing-autonomy)

This file is the human-readable authority for which upstream `mama` versions this adapter supports. It must agree with `src/mama_integrations/versions.py` (CI-checked).

## Matrix

| Upstream release | RULESET_VERSION | Ledger `schema` | Level scale | MAMA adapter behavior |
|---|---|---|---|---|
| **v2.0.0** (2026-11-03) — this adapter's baseline | `2.0.0` | `2` | L0 Submarine Line; L1–L5; dimensions 0–5; weakest link `min(D3,D4,D6)` | ✅ **supported** — import, validate structure, pass through as issued |
| v2.x future MINOR/PATCH | `2.*.*` | `2` | unchanged semantics (per upstream versioning policy: additive/clarification only within a MAJOR) | ✅ supported — comparable within MAJOR 2 |
| v1.x (retired) | `1.*.*` | `1` or absent | retired 0–4 scale | ⚠️ **warn + import raw** — values are on the retired scale; MAMA must not interpret them against v2 levels; re-baseline per upstream `docs/migration-v1-to-v2.md` |
| pre-versioning files | (unknown) | absent | unknown | ⚠️ **warn** (upstream treats absent `schema` as current; MAMA records the ambiguity) |
| future MAJOR | `≥3.0.0` | `≥3` | unknown | ❌ **fail closed** — `UnsupportedRulesetError` / `UnsupportedLedgerSchemaError` naming supported versions; no guessing, no silent import |

## Policy

1. **Fail closed.** Unknown upstream versions produce errors with the supported list — never a best-effort parse. An import that cannot declare its version semantics is not imported.
2. **Comparability follows upstream.** Within MAJOR 2, upstream guarantees score comparability (PATCH/MINOR rules). MAMA inherits that; we add no comparability claims of our own. Cross-MAJOR comparison requires upstream migration guidance + a MAMA ADR.
3. **Retired ≠ rejected.** Schema-1/retired-scale files import with a prominent warning so teams can inventory their legacy grants — but every downstream view must carry the retired-scale label.
4. **MAJOR support is a deliberate act.** Supporting upstream MAJOR n+1 requires: upstream migration note published, this matrix updated, `versions.py` updated, tests proving both the new acceptance and the new fail-closed boundary, and an ADR.
5. **Pass-through always.** No row in this matrix authorizes recalculation of scores, levels, or weakest-link outputs. Display is as issued, with the version recorded.

## Known upstream interfaces (v2.0.0)

- **Assessment record** — `autonomy-score --json`: `ruleset_version`, `scores` (D1–D6, 0–5), `safe_grant_level`, `granted_level` (int or null), `notes[]`, `recommended_move`. Schema: [`contracts/assessment-import.schema.json`](contracts/assessment-import.schema.json).
- **Autonomy Ledger** — YAML, top-level `schema: 2`, `contracts[]` with `id`, `unit`, `domain`, `level` (0–5), `scope`, `guardrails[]` (non-empty), `telemetry[]` (non-empty), `revocation_triggers[]` (non-empty), `escalation`, `grantor`, `horizon`, `last_review` (≤ horizon), `review_cadence_days`, `status` (`active|expired|revoked|draft`), `notes`. Schema: [`contracts/ledger-import.schema.json`](contracts/ledger-import.schema.json).
- **Linkage file** — MAMA-side mapping of use cases to `mama` units/domains/contracts: [`contracts/usecase-mapping.schema.json`](contracts/usecase-mapping.schema.json).

## Verification

CI asserts: schema-2 imports succeed; schema-1 and absent-schema imports warn; schema-3 and ruleset-3.0.0 imports fail closed; assessment records pass through byte-identical fields. Run `python -m pytest`.
