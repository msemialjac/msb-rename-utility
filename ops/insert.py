"""Insert a literal string at a position in the stem.

params:
  text: string to insert (required)
  at:   int position (0 = start, negative = from end, "end" = append to stem)
"""
from __future__ import annotations
import os


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    text = params.get("text", "")
    if not text:
        return name
    at = params.get("at", 0)
    stem, ext = os.path.splitext(name)

    if at == "end" or at is None:
        pos = len(stem)
    else:
        pos = int(at)
        if pos < 0:
            pos = max(0, len(stem) + pos)
        pos = min(pos, len(stem))

    return stem[:pos] + text + stem[pos:] + ext
