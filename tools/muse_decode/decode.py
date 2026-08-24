"""P1 decoder: `.mu` container → event stream (IR Work)."""

from __future__ import annotations

import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
from muse_ir.model import Work  # noqa: E402


class DecodeError(Exception):
    pass


def decode(container_path: str):
    """Decode a `.mu` container (zip: manifest.json + roll.bin) → Work."""
    if not os.path.exists(container_path):
        raise DecodeError(f"container not found: {container_path}")
    try:
        with zipfile.ZipFile(container_path) as zf:
            names = zf.namelist()
            if "manifest.json" not in names or "roll.bin" not in names:
                raise DecodeError("container missing manifest.json or roll.bin")
            manifest_data = zf.read("manifest.json")
            roll_data = zf.read("roll.bin")
    except zipfile.BadZipFile as e:
        raise DecodeError(f"bad zip container: {e}") from e

    # decode the S2 pack
    try:
        from muse_roll import decode as roll_decode
        work = roll_decode(roll_data)
    except Exception as e:
        raise DecodeError(f"roll decode failed: {e}") from e
    return work
