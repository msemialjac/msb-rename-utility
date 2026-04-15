"""Change or add the file extension.

params:
  to:      string — new extension (with or without leading '.'); "" removes extension
  only_if: optional string — only change if current ext (without dot, case-insensitive)
           matches this value. Useful for "turn .JPEG into .jpg but leave .PNG alone".
"""
from __future__ import annotations
import os


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    new_ext = params.get("to", "")
    if new_ext and not new_ext.startswith("."):
        new_ext = "." + new_ext

    stem, ext = os.path.splitext(name)
    only_if = params.get("only_if") or None  # UI may send "" → treat as unset
    if only_if is not None:
        current = ext.lstrip(".").lower()
        if current != only_if.lstrip(".").lower():
            return name
    return stem + new_ext
