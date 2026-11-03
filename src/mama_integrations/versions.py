"""Supported upstream `mama` versions and the fail-closed policy.

This module is the machine-readable twin of ``compatibility.md`` — CI checks
that they agree in spirit: the SUPPORTED_* constants below must match the
matrix table there. Never add a version here without updating that file (and
vice versa), and never support an upstream MAJOR without an ADR.

Policy (see compatibility.md):
  - Supported: ruleset MAJOR 2 (any MINOR/PATCH), ledger schema 2.
  - Retired (warn + import raw, values on the retired scale): ruleset MAJOR 1,
    ledger schema 1.
  - Pre-versioning (warn): ledger file with no ``schema`` field.
  - Unknown (fail closed): any other ruleset or schema version.
"""

from __future__ import annotations

import re

__all__ = [
    "SUPPORTED_RULESET_MAJOR",
    "SUPPORTED_RULESET_VERSION",
    "SUPPORTED_LEDGER_SCHEMA",
    "RETIRED_RULESET_MAJOR",
    "RETIRED_LEDGER_SCHEMA",
    "SEMVER_RE",
    "parse_ruleset_version",
    "classify_ruleset_version",
    "classify_ledger_schema",
]

#: The upstream release this adapter was baselined against.
SUPPORTED_RULESET_VERSION = "2.0.0"
SUPPORTED_RULESET_MAJOR = 2

#: Retired upstream scale (v1.x: 0-4 levels). Import with loud warnings only.
RETIRED_RULESET_MAJOR = 1

SUPPORTED_LEDGER_SCHEMA = 2
RETIRED_LEDGER_SCHEMA = 1

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_ruleset_version(version: str) -> tuple[int, int, int]:
    """Parse a semver string; raise ValueError on malformed input."""
    if not isinstance(version, str):
        raise ValueError(f"ruleset_version must be a string, got {type(version).__name__}")
    match = SEMVER_RE.match(version.strip())
    if not match:
        raise ValueError(
            f"ruleset_version {version!r} is not MAJOR.MINOR.PATCH semver"
        )
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def classify_ruleset_version(version: str) -> str:
    """Classify a ruleset version against the support policy.

    Returns one of: ``"supported"``, ``"retired"``, ``"unsupported"``.
    Malformed versions raise ``ValueError`` (fail closed).
    """
    major, _minor, _patch = parse_ruleset_version(version)
    if major == SUPPORTED_RULESET_MAJOR:
        return "supported"
    if major == RETIRED_RULESET_MAJOR:
        return "retired"
    return "unsupported"


def classify_ledger_schema(schema: int | None) -> str:
    """Classify a ledger ``schema`` value.

    ``None`` means the field is absent (a pre-versioning file). Returns
    ``"supported"``, ``"retired"``, ``"pre-versioning"``, or ``"unsupported"``.
    """
    if schema is None:
        return "pre-versioning"
    if schema == SUPPORTED_LEDGER_SCHEMA:
        return "supported"
    if schema == RETIRED_LEDGER_SCHEMA:
        return "retired"
    return "unsupported"
