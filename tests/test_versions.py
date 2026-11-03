"""Version-gate tests: supported, retired, and fail-closed behavior."""

import pytest

from mama_integrations.errors import UnsupportedRulesetError
from mama_integrations.versions import (
    SUPPORTED_RULESET_VERSION,
    classify_ledger_schema,
    classify_ruleset_version,
    parse_ruleset_version,
)


class TestRulesetVersions:
    def test_baseline_version_supported(self):
        assert classify_ruleset_version("2.0.0") == "supported"

    @pytest.mark.parametrize("version", ["2.0.1", "2.1.0", "2.9.9"])
    def test_same_major_supported(self, version):
        assert classify_ruleset_version(version) == "supported"

    def test_retired_major_classified(self):
        assert classify_ruleset_version("1.4.2") == "retired"

    @pytest.mark.parametrize("version", ["3.0.0", "10.2.3"])
    def test_unknown_major_fails_closed(self, version):
        assert classify_ruleset_version(version) == "unsupported"

    @pytest.mark.parametrize("version", ["banana", "2.0", "v2.0.0", "", "2.0.0.1"])
    def test_malformed_version_raises(self, version):
        with pytest.raises(ValueError):
            parse_ruleset_version(version)

    def test_non_string_version_raises(self):
        with pytest.raises(ValueError):
            parse_ruleset_version(2.0)  # type: ignore[arg-type]

    def test_baseline_constant_matches_policy(self):
        assert SUPPORTED_RULESET_VERSION == "2.0.0"


class TestLedgerSchemas:
    def test_schema_2_supported(self):
        assert classify_ledger_schema(2) == "supported"

    def test_schema_1_retired(self):
        assert classify_ledger_schema(1) == "retired"

    def test_absent_schema_is_pre_versioning(self):
        assert classify_ledger_schema(None) == "pre-versioning"

    @pytest.mark.parametrize("schema", [0, 3, 99, -1])
    def test_unknown_schema_fails_closed(self, schema):
        assert classify_ledger_schema(schema) == "unsupported"


class TestImportGates:
    def _record(self, version="2.0.0"):
        return {
            "ruleset_version": version,
            "scores": {"D1": 4, "D2": 3, "D3": 4, "D4": 3, "D5": 4, "D6": 3},
            "safe_grant_level": 3,
            "granted_level": 2,
            "notes": ["headroom: safe level exceeds granted level by 1"],
            "recommended_move": "hold: stable at the current level; re-review next horizon",
        }

    def test_v2_record_imports(self):
        from mama_integrations import import_assessment

        assert import_assessment(self._record()) == self._record()

    @pytest.mark.parametrize("version", ["1.9.9", "3.0.0", "2", "not-semver"])
    def test_non_supported_rulesets_fail_closed(self, version):
        from mama_integrations import import_assessment

        with pytest.raises(UnsupportedRulesetError):
            import_assessment(self._record(version))

    def test_missing_ruleset_fails_closed(self):
        from mama_integrations import import_assessment

        record = self._record()
        del record["ruleset_version"]
        with pytest.raises(UnsupportedRulesetError):
            import_assessment(record)
