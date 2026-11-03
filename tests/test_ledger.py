"""Ledger import/export tests: schema gate + structural validation + round-trip."""

from pathlib import Path

import pytest
import yaml

from mama_integrations.errors import (
    LedgerValidationError,
    UnsupportedLedgerSchemaError,
)
from mama_integrations.ledger import export_ledger, load_ledger

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def write_ledger(tmp_path, payload):
    path = tmp_path / "ledger.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def valid_contract(cid="test-domain-v1", level=3):
    return {
        "id": cid,
        "unit": "team-x",
        "domain": "test-domain",
        "level": level,
        "scope": "Something bounded and consequential.",
        "guardrails": ["Gate A mandatory"],
        "telemetry": ["Dashboard shared with grantor"],
        "revocation_triggers": ["Error budget burn > 50% in a week"],
        "grantor": "director-x",
        "horizon": "2027-06-30",
        "last_review": "2026-10-01",
        "review_cadence_days": 90,
        "status": "active",
        "notes": "Synthetic test contract.",
    }


class TestSchemaGate:
    def test_example_ledger_imports_clean(self):
        result = load_ledger(EXAMPLES / "upstream-ledger.example.yaml")
        assert result.schema_version == 2
        assert result.warnings == []
        assert result.contract_ids == {"ap-invoice-approvals-v1", "network-config-changes-v1"}

    def test_schema_1_warns_and_imports_raw(self, tmp_path):
        contract = valid_contract(level=2)  # retired-scale value, imported raw
        result = load_ledger(write_ledger(tmp_path, {"schema": 1, "contracts": [contract]}))
        assert result.schema_version == 1
        assert any("RETIRED SCALE" in w for w in result.warnings)
        assert result.contracts[0]["level"] == 2  # raw, never re-mapped

    def test_missing_schema_warns(self, tmp_path):
        result = load_ledger(write_ledger(tmp_path, {"contracts": [valid_contract()]}))
        assert result.schema_version is None
        assert any("pre-versioning" in w for w in result.warnings)

    @pytest.mark.parametrize("schema", [3, 7, 0])
    def test_unknown_schema_fails_closed(self, tmp_path, schema):
        with pytest.raises(UnsupportedLedgerSchemaError):
            load_ledger(write_ledger(tmp_path, {"schema": schema, "contracts": [valid_contract()]}))

    def test_non_integer_schema_fails_closed(self, tmp_path):
        with pytest.raises(UnsupportedLedgerSchemaError):
            load_ledger(write_ledger(tmp_path, {"schema": "two", "contracts": [valid_contract()]}))


class TestContractValidation:
    def test_missing_required_field_rejected(self, tmp_path):
        contract = valid_contract()
        del contract["guardrails"]
        with pytest.raises(LedgerValidationError, match="guardrails"):
            load_ledger(write_ledger(tmp_path, {"schema": 2, "contracts": [contract]}))

    def test_empty_guardrails_rejected(self, tmp_path):
        contract = valid_contract()
        contract["guardrails"] = []
        with pytest.raises(LedgerValidationError, match="not a contract"):
            load_ledger(write_ledger(tmp_path, {"schema": 2, "contracts": [contract]}))

    @pytest.mark.parametrize("level", [-1, 6, "3", 3.5])
    def test_bad_level_rejected(self, tmp_path, level):
        contract = valid_contract(level=level)
        with pytest.raises(LedgerValidationError, match="level"):
            load_ledger(write_ledger(tmp_path, {"schema": 2, "contracts": [contract]}))

    def test_last_review_after_horizon_rejected(self, tmp_path):
        contract = valid_contract()
        contract["horizon"] = "2026-01-01"
        with pytest.raises(LedgerValidationError, match="after horizon"):
            load_ledger(write_ledger(tmp_path, {"schema": 2, "contracts": [contract]}))

    def test_bad_status_rejected(self, tmp_path):
        contract = valid_contract()
        contract["status"] = "pending-ish"
        with pytest.raises(LedgerValidationError, match="status"):
            load_ledger(write_ledger(tmp_path, {"schema": 2, "contracts": [contract]}))

    def test_unknown_field_rejected(self, tmp_path):
        contract = valid_contract()
        contract["auto_score"] = 5  # looks like MAMA inventing a score — must fail
        with pytest.raises(LedgerValidationError, match="unknown fields"):
            load_ledger(write_ledger(tmp_path, {"schema": 2, "contracts": [contract]}))

    def test_duplicate_ids_rejected(self, tmp_path):
        contracts = [valid_contract(), valid_contract()]
        with pytest.raises(LedgerValidationError, match="duplicate"):
            load_ledger(write_ledger(tmp_path, {"schema": 2, "contracts": contracts}))


class TestExportRoundTrip:
    def test_round_trip_preserves_contracts(self, tmp_path):
        source = load_ledger(EXAMPLES / "upstream-ledger.example.yaml")
        out = tmp_path / "exported.yaml"
        export_ledger(source.contracts, out)
        reloaded = load_ledger(out)
        assert reloaded.schema_version == 2
        assert reloaded.contracts == source.contracts

    def test_export_refuses_retired_schema(self, tmp_path):
        with pytest.raises(UnsupportedLedgerSchemaError):
            export_ledger([valid_contract()], tmp_path / "x.yaml", schema=1)
