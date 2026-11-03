"""Typed errors for MAMA ↔ `mama` integration.

Fail-closed philosophy: unknown upstream versions raise, they never guess.
"""

from __future__ import annotations

__all__ = [
    "IntegrationError",
    "UnsupportedRulesetError",
    "UnsupportedLedgerSchemaError",
    "LedgerValidationError",
    "AssessmentValidationError",
    "MappingValidationError",
]


class IntegrationError(Exception):
    """Base class for all mama-integrations errors."""


class UnsupportedRulesetError(IntegrationError):
    """The record's ruleset version is unknown or unsupported. Fail closed."""


class UnsupportedLedgerSchemaError(IntegrationError):
    """The ledger's schema version is unknown or unsupported. Fail closed."""


class LedgerValidationError(IntegrationError):
    """A ledger contract violates the upstream structural field rules."""

    def __init__(self, contract_id: str | None, problems: list[str]):
        self.contract_id = contract_id
        self.problems = problems
        who = f"contract {contract_id!r}" if contract_id else "ledger"
        super().__init__(f"invalid ledger: {who}: " + "; ".join(problems))


class AssessmentValidationError(IntegrationError):
    """An assessment record is structurally invalid."""


class MappingValidationError(IntegrationError):
    """A use-case mapping file is invalid."""
