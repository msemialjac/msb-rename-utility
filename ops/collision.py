"""Collision-resolution post-pass.

This is NOT a pipeline op — pipeline ops run per-file and can't see siblings.
This runs once on the full list of new names after the pipeline completes,
and appends " (2)", " (3)", ... to any name that already exists in the set.

It's triggered by a request flag (`auto_resolve_collisions: true`), not a
pipeline step. That keeps the per-file op signature pure.
"""
from __future__ import annotations

import os
import re

_SUFFIX_RE = re.compile(r" \((\d+)\)$")


def _next_unique(base: str, taken: set[str]) -> str:
    """Return the smallest suffixed variant of `base` not in `taken`.

    'report.pdf' becomes 'report (2).pdf', 'report (3).pdf', ...
    'report (2).pdf' (already suffixed) becomes 'report (3).pdf', ... — we
    start from the existing suffix + 1 rather than re-adding a suffix.
    """
    stem, ext = os.path.splitext(base)
    m = _SUFFIX_RE.search(stem)
    if m:
        stem_wo = stem[: m.start()]
        n = int(m.group(1)) + 1
    else:
        stem_wo = stem
        n = 2

    while True:
        candidate = f"{stem_wo} ({n}){ext}"
        if candidate not in taken:
            return candidate
        n += 1


def resolve(names: list[str]) -> list[str]:
    """Return a new list where no two entries are equal.

    Earlier entries keep their name; later duplicates get " (2)", " (3)", ....
    Order-stable.
    """
    taken: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in taken:
            out.append(n)
            taken.add(n)
        else:
            uniq = _next_unique(n, taken)
            out.append(uniq)
            taken.add(uniq)
    return out
