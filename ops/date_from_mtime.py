"""Insert a date derived from the file's mtime.

Reads `ctx['mtimes'][idx]` (UTC epoch seconds, float). The Flask layer
populates this before running the pipeline when the request includes a valid
`dir`. If mtimes aren't available, the op raises so the mistake is loud
rather than silently dropping dates.

params:
  format:   strftime string (default "%Y-%m-%d")
  position: "prefix" | "suffix"    (default "prefix")
  sep:      string between date and stem (default "_")
"""
from __future__ import annotations
import os
from datetime import datetime, timezone


def apply(name: str, idx: int, ctx: dict, params: dict) -> str:
    mtimes = ctx.get("mtimes")
    if not mtimes or idx >= len(mtimes):
        raise ValueError(
            "date_from_mtime requires filesystem access — include `dir` in the request "
            "so the server can look up mtimes before running the pipeline"
        )
    ts = mtimes[idx]
    fmt = params.get("format", "%Y-%m-%d")
    position = params.get("position", "prefix")
    sep = params.get("sep", "_")

    date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime(fmt)
    stem, ext = os.path.splitext(name)
    if position == "prefix":
        return f"{date_str}{sep}{stem}{ext}"
    if position == "suffix":
        return f"{stem}{sep}{date_str}{ext}"
    raise ValueError(f"unknown position: {position!r}")
