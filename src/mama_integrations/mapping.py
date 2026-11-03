"""MAMA use-case ↔ `mama` unit/domain/contract linkage.

The mapping file is MAMA-side glue: it joins stable MAMA use-case IDs to the
upstream `mama` artifacts they govern. It carries identifiers and versions
only — never a merged identity, never a score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from mama_integrations.errors import MappingValidationError
from mama_integrations.ledger import LedgerImportResult
from mama_integrations.versions import (
    SUPPORTED_RULESET_VERSION,
    classify_ledger_schema,
    classify_ruleset_version,
)

__all__ = ["MappingImportResult", "MAPPING_REQUIRED_FIELDS", "load_mappings", "check_linkage"]

MAPPING_REQUIRED_FIELDS = (
    "mama_use_case_id",
    "mama_unit",
    "mama_domain",
    "mama_contract_id",
    "ruleset_version",
    "ledger_schema",
)
MAPPING_OPTIONAL_FIELDS = ("project_id", "linked_at", "note")


@dataclass
class MappingImportResult:
    mappings: list[dict]
    warnings: list[str] = field(default_factory=list)
    source: str | None = None

    @property
    def contract_ids(self) -> set[str]:
        return {m["mama_contract_id"] for m in self.mappings}

    @property
    def use_case_ids(self) -> set[str]:
        return {m["mama_use_case_id"] for m in self.mappings}


def _validate_mapping(raw: object, index: int) -> dict:
    if not isinstance(raw, dict):
        raise MappingValidationError(f"mappings[{index}] is not a mapping")
    missing = [name for name in MAPPING_REQUIRED_FIELDS if name not in raw]
    if missing:
        raise MappingValidationError(f"mappings[{index}] missing required fields: {missing}")

    for name in ("mama_use_case_id", "mama_unit", "mama_domain", "mama_contract_id"):
        if not isinstance(raw[name], str) or not raw[name].strip():
            raise MappingValidationError(f"mappings[{index}]: {name} must be a non-empty string")

    version = raw["ruleset_version"]
    try:
        kind = classify_ruleset_version(version)
    except ValueError as exc:
        raise MappingValidationError(f"mappings[{index}]: {exc}") from None
    if kind != "supported":
        raise MappingValidationError(
            f"mappings[{index}]: ruleset_version {version!r} is {kind!r} — linkage "
            "records must reference supported upstream versions (fail-closed)"
        )

    schema = raw["ledger_schema"]
    if not isinstance(schema, int) or isinstance(schema, bool):
        raise MappingValidationError(f"mappings[{index}]: ledger_schema must be an integer")
    schema_kind = classify_ledger_schema(schema)
    if schema_kind == "retired":
        raise MappingValidationError(
            f"mappings[{index}]: ledger_schema 1 is the retired format — re-baseline "
            "the linked contracts on the v2 scale before linking"
        )
    if schema_kind != "supported":
        raise MappingValidationError(
            f"mappings[{index}]: ledger_schema {schema!r} is not supported (supported: 2)"
        )

    unknown = set(raw) - set(MAPPING_REQUIRED_FIELDS) - set(MAPPING_OPTIONAL_FIELDS)
    if unknown:
        raise MappingValidationError(f"mappings[{index}]: unknown fields {sorted(unknown)}")
    return dict(raw)


def load_mappings(path: str | Path) -> MappingImportResult:
    """Load and validate a use-case mapping file (YAML).

    Raises:
        MappingValidationError: any mapping row is invalid or references a
            retired/unsupported upstream version.
        ValueError: the file is not parseable YAML or has wrong top level.
    """
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or not isinstance(data.get("mappings"), list):
        raise ValueError(f"{path}: mapping file must be a YAML mapping with a 'mappings' list")

    mappings = [_validate_mapping(raw, i) for i, raw in enumerate(data["mappings"])]

    warnings: list[str] = []
    seen = set()
    for m in mappings:
        key = (m["mama_use_case_id"], m["mama_contract_id"])
        if key in seen:
            warnings.append(f"duplicate linkage {key} — keep one, or version the contract id")
        seen.add(key)
        if m["ruleset_version"] != SUPPORTED_RULESET_VERSION:
            warnings.append(
                f"linkage {key}: ruleset {m['ruleset_version']} differs from the "
                f"adapter baseline {SUPPORTED_RULESET_VERSION} (comparable within MAJOR 2)"
            )

    return MappingImportResult(mappings=mappings, warnings=warnings, source=str(path))


def check_linkage(
    mappings: MappingImportResult, ledger: LedgerImportResult
) -> dict[str, list[str]]:
    """Cross-check mapping rows against an imported ledger.

    Returns a report of orphans:
      - ``unmatched_mappings``: rows pointing at contracts missing from the ledger (an error condition for callers),
      - ``unmapped_contracts``: ledger contracts no use case links to (informational — not every contract must be linked),
      - ``warnings``: mapping-file warnings.
    """
    ledger_ids = ledger.contract_ids
    mapped = {m["mama_contract_id"] for m in mappings.mappings}
    return {
        "unmatched_mappings": sorted(mapped - ledger_ids),
        "unmapped_contracts": sorted(ledger_ids - mapped),
        "warnings": list(mappings.warnings) + list(ledger.warnings),
    }
