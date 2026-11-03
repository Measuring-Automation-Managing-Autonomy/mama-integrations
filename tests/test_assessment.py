"""Assessment import tests: pass-through guarantee + fail-closed gates."""

import json
from pathlib import Path

import pytest

from mama_integrations.errors import (
    AssessmentValidationError,
    UnsupportedRulesetError,
)
from mama_integrations.ledger import load_ledger  # noqa: F401  (import sanity)
from mama_integrations.assessment import import_assessment

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def example_record():
    return json.loads((EXAMPLES / "assessment.example.json").read_text(encoding="utf-8"))


class TestPassThrough:
    def test_example_record_imports_unchanged(self):
        record = example_record()
        result = import_assessment(record)
        assert result == record

    def test_no_recomputation_of_safe_grant_level(self):
        """An 'inconsistent' record must import unchanged — checking min(D3,D4,D6)
        would be re-scoring, which MAMA never does (integration-contract rule 1)."""
        record = example_record()
        record["safe_grant_level"] = 5  # inconsistent with min(D3,D4,D6)=3 — upstream's problem, not ours
        result = import_assessment(record)
        assert result["safe_grant_level"] == 5

    def test_granted_level_null_is_the_submarine_line(self):
        record = example_record()
        record["granted_level"] = None
        assert import_assessment(record)["granted_level"] is None


class TestStructuralValidation:
    def test_missing_dimension_rejected(self):
        record = example_record()
        del record["scores"]["D6"]
        with pytest.raises(AssessmentValidationError, match="D6"):
            import_assessment(record)

    def test_unknown_dimension_rejected(self):
        record = example_record()
        record["scores"]["D7"] = 3
        with pytest.raises(AssessmentValidationError, match="unknown dimensions"):
            import_assessment(record)

    @pytest.mark.parametrize("value", [-1, 6, "3"])
    def test_out_of_range_score_rejected(self, value):
        record = example_record()
        record["scores"]["D3"] = value
        with pytest.raises(AssessmentValidationError, match="D3"):
            import_assessment(record)

    def test_non_string_note_rejected(self):
        record = example_record()
        record["notes"] = [42]
        with pytest.raises(AssessmentValidationError, match="notes"):
            import_assessment(record)

    def test_bool_score_rejected(self):
        record = example_record()
        record["scores"]["D3"] = True
        with pytest.raises(AssessmentValidationError):
            import_assessment(record)

    def test_unknown_fields_tolerated_with_warning(self):
        record = example_record()
        record["upstream_new_optional_field"] = {"x": 1}  # upstream MINOR metadata
        result = import_assessment(record)
        assert result["upstream_new_optional_field"] == {"x": 1}
        assert any("unknown fields" in w for w in result["_mama_import_warnings"])
