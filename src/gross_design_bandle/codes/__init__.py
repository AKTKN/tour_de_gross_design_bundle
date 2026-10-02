"""BB definitions, immutable code data and explicit convention maps."""
from .bb import BBCodeSpec, CodeData, build_bb_code
from .reference_profiles import load_reference_code, small_debug_code

__all__ = ["BBCodeSpec", "CodeData", "build_bb_code", "load_reference_code", "small_debug_code"]
