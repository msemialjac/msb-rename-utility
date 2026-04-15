"""Strip leading/trailing characters from the stem.

params:
  chars: string — characters to strip (default whitespace)
  side:  "both" | "left" | "right"  (default "both")
"""
from __future__ import annotations
import os


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    chars = params.get("chars")  # None → whitespace
    side = params.get("side", "both")
    stem, ext = os.path.splitext(name)

    if side == "both":
        stem = stem.strip(chars) if chars else stem.strip()
    elif side == "left":
        stem = stem.lstrip(chars) if chars else stem.lstrip()
    elif side == "right":
        stem = stem.rstrip(chars) if chars else stem.rstrip()
    else:
        raise ValueError(f"unknown side: {side!r}")
    return stem + ext
