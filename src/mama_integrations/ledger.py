"""Autonomy Ledger import/export (upstream `mama`, schema 2).

Structural validation + strict pass-through. This module implements the
upstream field rules from ``docs/ledger-format.md`` (v2) — required fields,
level range, non-empty guardrail/telemetry/trigger lists, date ordering,
status enum. It does **not** compute ledger health: coverage/staleness/expiry
analysis remains upstream (`ledger_health`); MAMA displays, it does not judge.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from mama_integrations.errors import (
    LedgerValidationError,
    UnsupportedLedgerSchemaError,
)
from mama_integrations.versions import classify_ledger_schema

__all__ = ["LedgerImportResult", "load_ledger", "export_ledger"]

CONTRACT_REQUIRED_FIELDS = (
    "id",
    "unit",
    "domain",
    "level",
    "scope",
    "guardrails",
    "telemetry",
    "revocation_triggers",
    "grantor",
    "horizon",
    "last_review",
    "status",
)
CONTRACT_OPTIONAL_FIELDS = ("review_cadence_days", "escalation", "notes")
STATUS_VALUES = ("active", "expired", "revoked", "draft")

# Level range is structural (0-5 integers) on both the current and retired
# scales. Interpreting what a level *means* is upstream's business, never ours.
LEVEL_MIN, LEVEL_MAX = 0, 5


@dataclass
class LedgerImportResult:
    """Validated ledger contents plus import provenance."""

    schema_version: int | None
    contracts: list[dict]
    warnings: list[str] = field(default_factory=list)
    source: str | None = None

    @property
    def contract_ids(self) -> set[str]:
        return {c["id"] for c in self.contracts}


def _validate_iso_date(contract_id: str, field_name: str, value: object) -> _dt.date:
    # YAML parses unquoted ISO dates (e.g. `horizon: 2025-12-31`) into
    # datetime.date objects; quoted ones arrive as strings. Accept both.
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, str):
        try:
            return _dt.date.fromisoformat(value)
        except ValueError as exc:
            raise LedgerValidationError(
                contract_id, [f"{field_name} {value!r} is not an ISO date: {exc}"]
            ) from None
    raise LedgerValidationError(
        contract_id, [f"{field_name} must be an ISO date, got {type(value).__name__}"]
    )


def _validate_contract(raw: object, index: int) -> dict:
    if not isinstance(raw, dict):
        raise LedgerValidationError(None, [f"contracts[{index}] is not a mapping"])
    cid = raw.get("id")
    problems: list[str] = []

    if not isinstance(cid, str) or not cid:
        problems.append("id must be a non-empty string")

    for name in CONTRACT_REQUIRED_FIELDS:
        if name not in raw:
            problems.append(f"missing required field {name!r}")

    if problems:  # report missing fields before type-checking them
        raise LedgerValidationError(cid if isinstance(cid, str) else None, problems)

    if not isinstance(raw["level"], int) or isinstance(raw["level"], bool):
        problems.append("level must be an integer")
    elif not LEVEL_MIN <= raw["level"] <= LEVEL_MAX:
        problems.append(f"level must be in {LEVEL_MIN}..{LEVEL_MAX}, got {raw['level']}")

    for name in ("guardrails", "telemetry", "revocation_triggers"):
        value = raw[name]
        if not isinstance(value, list) or not value:
            problems.append(f"{name} must be a non-empty list — a contract without them is not a contract")
        elif not all(isinstance(item, str) and item.strip() for item in value):
            problems.append(f"{name} entries must be non-empty strings")

    for name in ("scope", "grantor", "status"):
        if not isinstance(raw[name], str) or not raw[name].strip():
            problems.append(f"{name} must be a non-empty string")

    if raw["status"] not in STATUS_VALUES:
        problems.append(f"status must be one of {STATUS_VALUES}, got {raw['status']!r}")

    horizon = _validate_iso_date(cid, "horizon", raw["horizon"])
    last_review = _validate_iso_date(cid, "last_review", raw["last_review"])
    if last_review > horizon:
        problems.append(f"last_review {raw['last_review']} is after horizon {raw['horizon']}")

    if "review_cadence_days" in raw and (
        not isinstance(raw["review_cadence_days"], int)
        or isinstance(raw["review_cadence_days"], bool)
        or raw["review_cadence_days"] <= 0
    ):
        problems.append("review_cadence_days must be a positive integer")

    unknown = set(raw) - set(CONTRACT_REQUIRED_FIELDS) - set(CONTRACT_OPTIONAL_FIELDS)
    if unknown:
        problems.append(f"unknown fields {sorted(unknown)} — upstream schema 2 does not define them")

    if problems:
        raise LedgerValidationError(cid, problems)
    return dict(raw)


def load_ledger(path: str | Path) -> LedgerImportResult:
    """Load and validate an upstream Autonomy Ledger file.

    Version gate (see versions.py / compatibility.md):
      - ``schema: 2`` → supported;
      - ``schema: 1`` → retired scale: imports with a loud warning;
      - absent        → pre-versioning file: imports with a warning;
      - anything else → raises UnsupportedLedgerSchemaError (fail closed).

    Raises:
        UnsupportedLedgerSchemaError: unknown schema version.
        LedgerValidationError: contract violates upstream structural rules.
        ValueError: the file is not parseable YAML or has wrong top level.
    """
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"{path}: ledger must be a YAML mapping with a top-level 'contracts' key")

    schema = data.get("schema")
    if schema is not None and (not isinstance(schema, int) or isinstance(schema, bool)):
        raise UnsupportedLedgerSchemaError(
            f"{path}: 'schema' must be an integer, got {schema!r}"
        )

    warnings: list[str] = []
    kind = classify_ledger_schema(schema)
    if kind == "pre-versioning":
        warnings.append(
            "pre-versioning ledger: no 'schema' field. Upstream treats this as the "
            "current schema; MAMA records the ambiguity — re-save with 'schema: 2'."
        )
    elif kind == "retired":
        warnings.append(
            "RETIRED SCALE: ledger declares schema 1 (upstream v1.x, 0-4 levels, "
            "retired). Values are imported raw and MUST be re-baselined against the "
            "v2 scale before any comparison — see upstream docs/migration-v1-to-v2.md."
        )
    elif kind == "unsupported":
        raise UnsupportedLedgerSchemaError(
            f"{path}: ledger schema {schema!r} is not supported by "
            f"mama-integrations. Supported schema: 2 (retired: 1). Fail-closed per "
            f"integration-contract rule 3 — do not guess. Check for an adapter update."
        )

    contracts_raw = data.get("contracts")
    if not isinstance(contracts_raw, list):
        raise LedgerValidationError(None, [f"{path}: top-level 'contracts' must be a list"])

    contracts = [_validate_contract(raw, i) for i, raw in enumerate(contracts_raw)]

    ids = [c["id"] for c in contracts]
    duplicates = sorted({cid for cid in ids if ids.count(cid) > 1})
    if duplicates:
        raise LedgerValidationError(None, [f"duplicate contract ids: {duplicates}"])

    return LedgerImportResult(
        schema_version=schema, contracts=contracts, warnings=warnings, source=str(path)
    )


def export_ledger(contracts: list[dict], path: str | Path, *, schema: int = 2) -> None:
    """Write contracts as an upstream-format ledger file.

    Contracts are validated with the same rules as import before writing, so
    an exported ledger always round-trips through upstream tooling. Only
    schema 2 is exported; exporting retired-scale files is refused.
    """
    if schema != 2:
        raise UnsupportedLedgerSchemaError(
            f"export supports schema 2 only (got {schema!r}) — never emit retired formats"
        )
    validated = [_validate_contract(raw, i) for i, raw in enumerate(contracts)]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            {"schema": schema, "contracts": validated},
            fh,
            sort_keys=False,
            allow_unicode=True,
        )
