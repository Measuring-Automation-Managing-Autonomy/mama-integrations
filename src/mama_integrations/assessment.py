"""Assessment-record import (upstream `autonomy-score --json` output).

Strict pass-through with structural validation. The record's fields —
scores, safe_grant_level, granted_level, notes, recommended_move — are
stored and displayed **exactly as issued**. This module never recomputes,
"sanity-checks", or repairs upstream values; asserting ``min(D3, D4, D6)``
against the issued safe_grant_level would be re-scoring, and is deliberately
not done here.
"""

from __future__ import annotations

from mama_integrations.errors import (
    AssessmentValidationError,
    UnsupportedRulesetError,
)
from mama_integrations.versions import (
    SUPPORTED_RULESET_VERSION,
    classify_ruleset_version,
)

__all__ = ["ASSESSMENT_FIELDS", "import_assessment"]

DIMENSIONS = ("D1", "D2", "D3", "D4", "D5", "D6")
SCORE_MIN, SCORE_MAX = 0, 5
LEVEL_MIN, LEVEL_MAX = 0, 5

#: The upstream record fields MAMA stores verbatim, plus its provenance.
ASSESSMENT_FIELDS = (
    "ruleset_version",
    "scores",
    "safe_grant_level",
    "granted_level",
    "notes",
    "recommended_move",
)


def _validate_level(name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise AssessmentValidationError(f"{name} must be an integer, got {value!r}")
    if not LEVEL_MIN <= value <= LEVEL_MAX:
        raise AssessmentValidationError(f"{name} must be in {LEVEL_MIN}..{LEVEL_MAX}, got {value}")


def import_assessment(record: dict) -> dict:
    """Validate and return an upstream assessment record unchanged.

    Version gate: ``ruleset_version`` must parse as semver with supported
    MAJOR (2). Retired MAJOR 1 and unknown MAJORs fail closed — a retired-
    scale record cannot be imported silently into a v2 world.

    Returns:
        The same mapping, unmodified (pass-through guarantee).

    Raises:
        UnsupportedRulesetError: unknown/retired/malformed ruleset version.
        AssessmentValidationError: structurally invalid record.
    """
    if not isinstance(record, dict):
        raise AssessmentValidationError("assessment record must be a JSON object")

    version = record.get("ruleset_version")
    if version is None:
        raise UnsupportedRulesetError(
            "assessment record is missing 'ruleset_version' — a record that cannot "
            "declare its rules cannot be imported (fail-closed)"
        )
    try:
        kind = classify_ruleset_version(version)
    except ValueError as exc:
        raise UnsupportedRulesetError(str(exc)) from None
    if kind == "retired":
        raise UnsupportedRulesetError(
            f"ruleset_version {version!r} is the retired v1.x scale. Importing it "
            "into v2 records would mix scales — re-score with the current ruleset "
            "(see upstream docs/migration-v1-to-v2.md)."
        )
    if kind == "unsupported":
        raise UnsupportedRulesetError(
            f"ruleset_version {version!r} is not supported. Supported MAJOR: 2 "
            f"(baselined on {SUPPORTED_RULESET_VERSION}). Fail-closed per "
            "integration-contract rule 3 — check for an adapter update."
        )

    scores = record.get("scores")
    if not isinstance(scores, dict):
        raise AssessmentValidationError("'scores' must be an object keyed D1..D6")
    missing = [d for d in DIMENSIONS if d not in scores]
    if missing:
        raise AssessmentValidationError(f"'scores' is missing dimensions: {missing}")
    extra = [k for k in scores if k not in DIMENSIONS]
    if extra:
        raise AssessmentValidationError(f"'scores' has unknown dimensions: {extra}")
    for dim in DIMENSIONS:
        value = scores[dim]
        if not isinstance(value, int) or isinstance(value, bool):
            raise AssessmentValidationError(f"scores[{dim}] must be an integer, got {value!r}")
        if not SCORE_MIN <= value <= SCORE_MAX:
            raise AssessmentValidationError(
                f"scores[{dim}] must be in {SCORE_MIN}..{SCORE_MAX}, got {value}"
            )

    _validate_level("safe_grant_level", record.get("safe_grant_level"))

    granted = record.get("granted_level")
    if granted is not None:
        _validate_level("granted_level", granted)

    notes = record.get("notes")
    if not isinstance(notes, list) or not all(isinstance(n, str) for n in notes):
        raise AssessmentValidationError("'notes' must be a list of strings")

    move = record.get("recommended_move")
    if not isinstance(move, str) or not move.strip():
        raise AssessmentValidationError("'recommended_move' must be a non-empty string")

    unknown = set(record) - set(ASSESSMENT_FIELDS)
    if unknown:
        # Upstream MINOR versions may add optional metadata; tolerate it, but
        # the caller must know the record is not a vanilla v2.0.0 shape.
        # (Fields are still passed through untouched.)
        record = dict(record)
        record.setdefault("_mama_import_warnings", []).append(
            f"unknown fields tolerated (upstream MINOR metadata?): {sorted(unknown)}"
        )
        return record

    return record
