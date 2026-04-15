"""Zero-pad numeric runs in the filename stem.

params:
  width: int (required) — target width for numeric runs
  scope: "stem" | "name" (default "stem")

Example: width=4 turns 'IMG_7.jpg' into 'IMG_0007.jpg'.
Every maximal run of digits in `scope` is independently padded.
"""
from __future__ import annotations
import os
import re

_DIGITS = re.compile(r"\d+")


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    width = int(params.get("width", 0))
    if width <= 0:
        return name
    scope = params.get("scope", "stem")

    target, ext = (name, "") if scope == "name" else os.path.splitext(name)
    target = _DIGITS.sub(lambda m: m.group(0).zfill(width), target)
    return target + ext
