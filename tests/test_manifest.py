"""Negative source-policy tests; these do not certify a future circuit manifest."""
import pytest
from gross_design_bandle.bench.manifest import validate_manifest


def test_algebra_only_allows_unresolved_sections():
    validate_manifest({"schema_version": 1, "mode": "algebra_only", "open_items": ["O1", "O2", "O3", "O4", "O5"], "observable": None})


@pytest.mark.parametrize("section", ["observable", "schedule", "fault_population", "decoder_mapping"])
def test_unknown_section_fields_fail_closed(section):
    with pytest.raises(ValueError, match=f"unknown {section} fields"):
        validate_manifest({"schema_version": 1, "mode": "paper_exact", section: {"guessed": "unknown"}})


def test_paper_exact_rejects_unresolved_definitions():
    with pytest.raises(ValueError, match="unresolved O1, O2, O3, O4, O5"):
        validate_manifest({"schema_version": 1, "mode": "paper_exact"})


def test_self_asserted_resolution_is_rejected():
    with pytest.raises(ValueError, match="retain O1--O5"):
        validate_manifest({"schema_version": 1, "mode": "paper_exact", "open_items": []})


def test_unknown_top_level_field_is_rejected():
    with pytest.raises(ValueError, match="unknown manifest fields"):
        validate_manifest({"schema_version": 1, "mode": "algebra_only", "observables": {}})


@pytest.mark.parametrize("section", ["observable", "schedule", "fault_population", "decoder_mapping"])
def test_unverified_profile_is_not_certified_in_algebra_mode(section):
    with pytest.raises(ValueError, match="algebra_only cannot certify"):
        validate_manifest({"schema_version": 1, "mode": "algebra_only", section: {"profile": "unknown"}})


@pytest.mark.parametrize("changes", [{"schema_version": True}, {"mode": "sampling"}, {"paper_version": "2506.03094v2"}, {"schedule": "unknown"}])
def test_invalid_types_versions_and_modes(changes):
    with pytest.raises(ValueError):
        validate_manifest({"schema_version": 1, "mode": "algebra_only", **changes})
