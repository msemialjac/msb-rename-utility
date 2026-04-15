"""Sequential numbering op.

params:
  start: int (default 1)
  step:  int (default 1)
  pad:   int width for zero-padding (default 0 = no padding)
  position: "prefix" | "suffix"   where to place the number in the stem (default "suffix")
  sep: separator between stem and number (default "_")
"""
from __future__ import annotations
import os


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    start = int(params.get("start", 1))
    step = int(params.get("step", 1))
    pad = int(params.get("pad", 0))
    position = params.get("position", "suffix")
    sep = params.get("sep", "_")

    n = start + idx * step
    num = str(n).zfill(pad) if pad > 0 else str(n)

    stem, ext = os.path.splitext(name)
    if position == "prefix":
        return f"{num}{sep}{stem}{ext}"
    if position == "suffix":
        return f"{stem}{sep}{num}{ext}"
    raise ValueError(f"unknown position: {position!r}")
