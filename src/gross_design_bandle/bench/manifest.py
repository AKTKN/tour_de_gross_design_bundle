"""Phase-00 declaration validator, not a circuit or sampling authorization.

Only algebra-only development is currently admitted. Paper-exact configuration
cannot be established by declaring the unresolved source definitions resolved.
"""

OPEN_PAPER_ITEMS = ("O1", "O2", "O3", "O4", "O5")
SECTION_FIELDS = {
    "observable": {"profile", "generators", "evidence_sha256"},
    "schedule": {"profile", "shift_representative", "gate_lowering", "boundaries", "evidence_sha256"},
    "fault_population": {"profile", "admission_policy", "multiplicity_policy", "column_policy", "evidence_sha256"},
    "decoder_mapping": {"profile", "source_commit", "parameter_mapping", "prior_policy", "evidence_sha256"},
}


def validate_manifest(manifest: dict) -> None:
    """Reject unknown keys/values and fail closed on paper-exact requests.

    Algebra-only manifests must omit physical/benchmark sections or set them to
    null. Their presence as objects is checked for unknown keys before rejection.
    This deliberately does not certify any future profile or arbitrary evidence
    hash supplied by a caller.
    """
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    allowed = {"schema_version", "mode", "paper_version", "open_items", *SECTION_FIELDS}
    unknown = set(manifest) - allowed
    if unknown:
        raise ValueError(f"unknown manifest fields: {sorted(unknown)}")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError("schema_version must be integer 1")
    if manifest.get("mode") not in ("algebra_only", "paper_exact"):
        raise ValueError("unknown mode")
    if manifest.get("paper_version", "2506.03094v1") != "2506.03094v1":
        raise ValueError("unknown paper_version")
    if "open_items" in manifest:
        items = manifest["open_items"]
        if not isinstance(items, list) or any(not isinstance(x, str) for x in items):
            raise ValueError("open_items must be a list of source item IDs")
        if len(set(items)) != len(items) or set(items) != set(OPEN_PAPER_ITEMS):
            raise ValueError("open_items must retain O1--O5; declarations cannot resolve them")
    for section, fields in SECTION_FIELDS.items():
        value = manifest.get(section)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise ValueError(f"{section} must be null or an object")
        unknown = set(value) - fields
        if unknown:
            raise ValueError(f"unknown {section} fields: {sorted(unknown)}")
    if manifest["mode"] == "paper_exact":
        raise ValueError("paper_exact blocked by unresolved O1, O2, O3, O4, O5")
    if any(manifest.get(section) is not None for section in SECTION_FIELDS):
        raise ValueError("algebra_only cannot certify observable, schedule, fault_population or decoder_mapping profiles")
