"""Regex find/replace op.

params:
  pattern: Python re pattern (required)
  repl:    replacement (supports \\1 backrefs); default ""
  flags:   list of "i", "m", "s" (optional)
  scope:   "stem" | "name" (default "name")
"""
from __future__ import annotations
import os
import re


def _flags(flag_list: list[str]) -> int:
    mapping = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL}
    out = 0
    for f in flag_list or []:
        bit = mapping.get(f.lower())
        if bit is None:
            raise ValueError(f"unknown regex flag: {f!r}")
        out |= bit
    return out


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    pattern = params.get("pattern")
    if not pattern:
        return name
    repl = params.get("repl", "")
    scope = params.get("scope", "name")
    flags = _flags(params.get("flags", []))

    target, ext = (name, "") if scope == "name" else os.path.splitext(name)
    target = re.sub(pattern, repl, target, flags=flags)
    return target + ext
