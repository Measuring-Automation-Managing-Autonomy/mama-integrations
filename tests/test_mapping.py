"""Mapping-file tests: linkage validation + orphan detection."""

from pathlib import Path

import pytest
import yaml

from mama_integrations.errors import MappingValidationError
from mama_integrations.ledger import load_ledger
from mama_integrations.mapping import check_linkage, load_mappings

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def write_mappings(tmp_path, mappings):
    path = tmp_path / "mapping.yaml"
    path.write_text(yaml.safe_dump({"mappings": mappings}, sort_keys=False), encoding="utf-8")
    return path


def valid_mapping(contract="ap-invoice-approvals-v1"):
    return {
        "mama_use_case_id": "usecase-ap-invoices",
        "project_id": "proj-2026-014",
        "mama_unit": "finance-ops",
        "mama_domain": "invoice-approval",
        "mama_contract_id": contract,
        "ruleset_version": "2.0.0",
        "ledger_schema": 2,
        "linked_at": "2026-11-04",
        "note": "Synthetic linkage.",
    }


class TestMappingValidation:
    def test_example_mappings_load(self):
        result = load_mappings(EXAMPLES / "usecase-mapping.example.yaml")
        assert len(result.mappings) == 2
        assert "usecase-ap-invoices" in result.use_case_ids

    def test_missing_required_field_rejected(self, tmp_path):
        mapping = valid_mapping()
        del mapping["mama_domain"]
        with pytest.raises(MappingValidationError, match="mama_domain"):
            load_mappings(write_mappings(tmp_path, [mapping]))

    @pytest.mark.parametrize("version", ["1.9.9", "3.0.0", "oops"])
    def test_unsupported_ruleset_in_linkage_fails_closed(self, tmp_path, version):
        mapping = valid_mapping()
        mapping["ruleset_version"] = version
        with pytest.raises(MappingValidationError, match="ruleset_version"):
            load_mappings(write_mappings(tmp_path, [mapping]))

    def test_retired_ledger_schema_rejected(self, tmp_path):
        mapping = valid_mapping()
        mapping["ledger_schema"] = 1
        with pytest.raises(MappingValidationError, match="re-baseline"):
            load_mappings(write_mappings(tmp_path, [mapping]))

    def test_unknown_field_rejected(self, tmp_path):
        mapping = valid_mapping()
        mapping["blended_score"] = 88  # a composite would violate ADR-003 — structurally rejected
        with pytest.raises(MappingValidationError, match="unknown fields"):
            load_mappings(write_mappings(tmp_path, [mapping]))


class TestLinkageCheck:
    def test_orphans_detected_both_ways(self, tmp_path):
        ledger = load_ledger(EXAMPLES / "upstream-ledger.example.yaml")
        mappings = load_mappings(
            write_mappings(
                tmp_path,
                [valid_mapping(contract="ap-invoice-approvals-v1"), valid_mapping(contract="ghost-contract-v1")],
            )
        )
        report = check_linkage(mappings, ledger)
        assert report["unmatched_mappings"] == ["ghost-contract-v1"]
        assert report["unmapped_contracts"] == ["network-config-changes-v1"]

    def test_full_linkage_is_clean(self, tmp_path):
        ledger = load_ledger(EXAMPLES / "upstream-ledger.example.yaml")
        mappings = load_mappings(
            write_mappings(
                tmp_path,
                [
                    valid_mapping("ap-invoice-approvals-v1"),
                    valid_mapping("network-config-changes-v1"),
                ],
            )
        )
        report = check_linkage(mappings, ledger)
        assert report["unmatched_mappings"] == []
