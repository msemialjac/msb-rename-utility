"""Literal find/replace op.

params:
  find:  string to match (literal, no regex)
  with:  replacement (default "")
  case_sensitive: bool (default True)
  scope: "stem" | "name" (default "name") — "stem" excludes extension
"""
from __future__ import annotations
import os


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    find = params.get("find", "")
    repl = params.get("with", "")
    if not find:
        return name
    cs = params.get("case_sensitive", True)
    scope = params.get("scope", "name")

    target, ext = (name, "") if scope == "name" else os.path.splitext(name)

    if cs:
        target = target.replace(find, repl)
    else:
        # case-insensitive literal replace without regex
        low_t, low_f = target.lower(), find.lower()
        out, i = [], 0
        while i < len(target):
            if low_t.startswith(low_f, i):
                out.append(repl)
                i += len(find)
            else:
                out.append(target[i])
                i += 1
        target = "".join(out)

    return target + ext
