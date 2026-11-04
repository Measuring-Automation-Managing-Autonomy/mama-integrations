# mama-integrations

**MAMA** (Measuring Automation & Measuring Autonomy) — version-pinned import/export adapters connecting MAMA use cases to the upstream **`mama`** (measuring and managing autonomy) method's assessments and ledgers.

**Status:** `draft` (v0.1.0) · **License:** Apache-2.0 · **Maintainer:** see [MAINTAINERS.md](MAINTAINERS.md)

> **First reference:** MAMA (Measuring Automation & Measuring Autonomy) uses the `mama` (measuring and managing autonomy) method for its autonomy-governance component. The `mama` method's canonical home is [`emmanuel-a-otchere/measuring-and-managing-autonomy`](https://github.com/emmanuel-a-otchere/measuring-and-managing-autonomy).

## What this repo is — and is not

| It **is** | It is **not** |
|---|---|
| A version-gated importer for upstream `mama` assessment records (`autonomy-score --json`) and Autonomy Ledger files (`schema: 2`) | A reimplementation of `mama` scoring — never. No weakest-link, no level logic, no dimension semantics |
| A pass-through display layer: outputs are stored and shown **exactly as issued**, with `ruleset_version` / `schema` recorded alongside | A fork or vendored copy of upstream code |
| A linkage layer: MAMA use-case IDs ↔ `mama` units/domains/contracts | A composite-score factory — automation metrics and autonomy outputs are never merged (ADR-003) |
| Fail-closed: unknown upstream versions raise clear errors naming what is supported | A silent upgrader of records between incompatible rulesets |

The governing contract: [`mama-framework/integration-contract.md`](https://github.com/Measuring-Automation-Managing-Autonomy/mama-framework/blob/main/integration-contract.md).

## Supported upstream versions

| Upstream `mama` release | Ruleset | Ledger schema | Support |
|---|---|---|---|
| v2.0.0 (2026-11-03) | `2.0.0` | `2` | ✅ supported (this adapter's baseline) |
| v2.x (any MINOR/PATCH) | `2.*.*` | `2` | ✅ comparable per upstream policy |
| v1.x | `1.*.*` | `1` (or absent) | ⚠️ retired scale — imports **warn loudly**, values are on the retired 0–4 scale, re-baseline per upstream migration guidance |
| unknown / future MAJOR | `≥3.0.0` | `≥3` | ❌ **fail closed** with a clear error; never guess |

Full policy and update procedure: [compatibility.md](compatibility.md).

## Install & use

```bash
pip install mama-integrations   # runtime dep: pyyaml only
```

```python
from mama_integrations import load_ledger, import_assessment, load_mappings

# 1. Import an upstream ledger (YAML, schema 2) — validated, passed through
result = load_ledger("ledger.yaml")
print(result.meta.schema_version, result.warnings)   # 2, []
for contract in result.contracts:
    print(contract["id"], contract["level"])          # level exactly as upstream issued it

# 2. Import an assessment record (autonomy-score --json output)
assessment = import_assessment(json.loads(scorecard_json))
print(assessment["safe_grant_level"])                 # as issued — never recomputed here

# 3. Link MAMA use cases to `mama` domains
mappings = load_mappings("usecase-mapping.yaml")
orphans = check_linkage(mappings, result)             # report unmatched ids both ways
```

Examples with synthetic data: [`examples/`](examples/). Interface schemas (the published file contracts): [`contracts/`](contracts/).

## Repository layout

```
src/mama_integrations/
  versions.py     # supported upstream versions & fail-closed policy
  ledger.py       # ledger import/export + structural validation
  assessment.py   # assessment-record import + pass-through
  mapping.py      # MAMA use-case ↔ `mama` domain linkage
  errors.py       # typed errors (fail-closed behavior)
contracts/        # JSON Schemas defining the file interfaces
examples/         # synthetic sample files
tests/            # pytest suite incl. fail-closed behavior tests
```

## Development

```bash
git clone https://github.com/Measuring-Automation-Managing-Autonomy/mama-integrations
cd mama-integrations
python -m pip install -e ".[dev]"
python -m pytest
```

CI runs the test suite and validates the JSON Schemas in `contracts/` on every push.

## License

[Apache-2.0](LICENSE). Upstream `mama` is MIT-licensed and remains at its own home; this package consumes its versioned *outputs* only. See the [license policy](https://github.com/Measuring-Automation-Managing-Autonomy/.github/blob/main/LICENSE-POLICY.md).
