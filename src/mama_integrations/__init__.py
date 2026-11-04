"""mama-integrations — version-pinned MAMA ↔ `mama` import/export adapters.

MAMA (Measuring Automation & Measuring Autonomy) consumes the lowercase
`mama` (measuring and managing autonomy) method's versioned outputs through
this package. Upstream outputs are **passed through exactly as issued**;
this package validates structure and versions only — it contains no scoring
logic and never recomputes levels, dimension scores, or weakest-link values.

Canonical homes:
  - This package: https://github.com/Measuring-Automation-Managing-Autonomy/mama-integrations
  - Upstream `mama` method: https://github.com/emmanuel-a-otchere/measuring-and-managing-autonomy
"""

from mama_integrations.assessment import import_assessment
from mama_integrations.errors import (
    AssessmentValidationError,
    IntegrationError,
    LedgerValidationError,
    MappingValidationError,
    UnsupportedLedgerSchemaError,
    UnsupportedRulesetError,
)
from mama_integrations.ledger import LedgerImportResult, export_ledger, load_ledger
from mama_integrations.mapping import MappingImportResult, check_linkage, load_mappings
from mama_integrations.versions import (
    SUPPORTED_LEDGER_SCHEMA,
    SUPPORTED_RULESET_VERSION,
    classify_ledger_schema,
    classify_ruleset_version,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "SUPPORTED_RULESET_VERSION",
    "SUPPORTED_LEDGER_SCHEMA",
    "classify_ruleset_version",
    "classify_ledger_schema",
    "load_ledger",
    "export_ledger",
    "LedgerImportResult",
    "import_assessment",
    "load_mappings",
    "check_linkage",
    "MappingImportResult",
    "IntegrationError",
    "UnsupportedRulesetError",
    "UnsupportedLedgerSchemaError",
    "LedgerValidationError",
    "AssessmentValidationError",
    "MappingValidationError",
]
