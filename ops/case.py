"""Case conversion op.

params:
  mode: "lower" | "upper" | "title" | "sentence"
  scope: "stem" | "ext" | "both"   (default "stem")
"""
from __future__ import annotations
import os


def _convert(s: str, mode: str) -> str:
    if mode == "lower":    return s.lower()
    if mode == "upper":    return s.upper()
    if mode == "title":    return s.title()
    if mode == "sentence": return s[:1].upper() + s[1:].lower() if s else s
    raise ValueError(f"unknown case mode: {mode!r}")


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    mode = params.get("mode", "lower")
    scope = params.get("scope", "stem")
    stem, ext = os.path.splitext(name)
    if scope == "stem": stem = _convert(stem, mode)
    elif scope == "ext": ext = _convert(ext, mode)
    elif scope == "both":
        stem = _convert(stem, mode)
        ext = _convert(ext, mode)
    else:
        raise ValueError(f"unknown scope: {scope!r}")
    return stem + ext
