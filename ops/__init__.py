"""Rename-operation registry.

Each op is a pure function: (name: str, idx: int, ctx: dict, params: dict) -> str
- `name`   current filename (stem + ext as a single string, no directory)
- `idx`    zero-based position in the input list
- `ctx`    shared per-run dict (mtimes, counters, etc.) populated by the Flask
           layer when it has filesystem access
- `params` user-supplied params for this op
Return the new name. Never touch disk. Never mutate inputs.
"""

from __future__ import annotations

from . import case, replace, regex, insert, numbering
from . import pad, trim, remove_at, change_ext

REGISTRY = {
    "case":       case.apply,
    "replace":    replace.apply,
    "regex":      regex.apply,
    "insert":     insert.apply,
    "numbering":  numbering.apply,
    "pad":        pad.apply,
    "trim":       trim.apply,
    "remove_at":  remove_at.apply,
    "change_ext": change_ext.apply,
}


def run_pipeline(names: list[str], pipeline: list[dict], ctx: dict | None = None) -> list[str]:
    """Apply pipeline ops sequentially to each name. Returns new names.

    `ctx` is shared across all files in the batch. The caller can pre-populate
    it with filesystem-derived metadata (e.g. `ctx['mtimes']`) so ops that
    need it can read without touching disk themselves.
    """
    ctx = ctx if ctx is not None else {}
    out = list(names)
    for idx, name in enumerate(out):
        for step in pipeline:
            op = REGISTRY.get(step.get("op"))
            if op is None:
                raise ValueError(f"unknown op: {step.get('op')!r}")
            name = op(name, idx, ctx, step.get("params") or {})
        out[idx] = name
    return out
