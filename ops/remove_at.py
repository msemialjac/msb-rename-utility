"""Remove a range of characters from the stem.

params:
  start: int — start position (negative = from end)
  count: int — how many characters to remove (>= 0; 0 = no-op)
"""
from __future__ import annotations
import os


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    count = int(params.get("count", 0))
    if count <= 0:
        return name
    start = int(params.get("start", 0))
    stem, ext = os.path.splitext(name)

    if start < 0:
        start = max(0, len(stem) + start)
    start = min(start, len(stem))
    end = min(start + count, len(stem))
    return stem[:start] + stem[end:] + ext
