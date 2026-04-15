"""msb_rename_utility — Flask micro-app.

Endpoints:
  GET  /             single-page UI
  POST /api/preview  compute new names + collision flags (no IO)
  POST /api/apply    rename files on disk with a two-phase swap-safe strategy
                     and a JSON undo-log sidecar written before any rename
  POST /api/undo     replay an undo-log in reverse
"""
from __future__ import annotations

import json
import os
import re
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from ops import run_pipeline

app = Flask(__name__)

UNDO_LOG_PREFIX = ".rename-undo-"
UNDO_LOG_SUFFIX = ".json"
# A forbidden-char set that's safe on every major filesystem we'd plausibly touch.
# We don't try to enforce a *specific* OS's rules — we just reject the universally bad.
_BAD_NAME_RE = re.compile(r"[/\x00]")


def _compute_rows(files: list[str], pipeline: list[dict]) -> tuple[list[dict], list[str], list[str]]:
    """Pure function: run the pipeline and annotate each row. Returns (rows, olds, news)."""
    bases = [Path(f).name for f in files]
    news = run_pipeline(bases, pipeline)
    new_counts = Counter(news)
    old_set = set(bases)

    rows = []
    for old, new in zip(bases, news):
        collides_self = new_counts[new] > 1
        collides_other = (new in old_set) and (new != old)
        rows.append({
            "old": old,
            "new": new,
            "unchanged": old == new,
            "collision": collides_self or collides_other,
        })
    return rows, bases, news


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/preview")
def api_preview():
    body = request.get_json(silent=True) or {}
    files = body.get("files") or []
    pipeline = body.get("pipeline") or []

    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        return jsonify(error="`files` must be a list of strings"), 400
    if not isinstance(pipeline, list):
        return jsonify(error="`pipeline` must be a list"), 400

    try:
        rows, _, _ = _compute_rows(files, pipeline)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(rows)


@app.post("/api/apply")
def api_apply():
    """Rename files on disk. All-or-nothing in spirit: we write the undo-log
    first, then rename via two-phase temp swap so collisions during the run
    are impossible. On any error mid-run, the undo-log already on disk can
    replay the partial work in reverse."""
    body = request.get_json(silent=True) or {}
    raw_dir = body.get("dir")
    files = body.get("files") or []
    pipeline = body.get("pipeline") or []

    if not isinstance(raw_dir, str) or not raw_dir:
        return jsonify(error="`dir` is required"), 400
    directory = Path(raw_dir).expanduser().resolve()
    if not directory.is_dir():
        return jsonify(error=f"not a directory: {directory}"), 400

    try:
        rows, olds, news = _compute_rows(files, pipeline)
    except ValueError as e:
        return jsonify(error=str(e)), 400

    # Hard refusals.
    if any(r["collision"] for r in rows):
        return jsonify(error="pipeline produces collisions — refusing to apply"), 409
    for new in news:
        if not new or _BAD_NAME_RE.search(new):
            return jsonify(error=f"invalid new name: {new!r}"), 400

    # Missing-source check (fast fail before touching anything).
    missing = [o for o in olds if not (directory / o).exists()]
    if missing:
        return jsonify(error=f"missing on disk: {missing}"), 404

    # Write undo-log sidecar FIRST so a crashed process is always recoverable.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    undo_path = directory / f"{UNDO_LOG_PREFIX}{stamp}{UNDO_LOG_SUFFIX}"
    plan = [{"from": o, "to": n} for o, n in zip(olds, news) if o != n]
    undo_path.write_text(json.dumps({
        "dir": str(directory),
        "created": stamp,
        "renames": plan,
    }, indent=2), encoding="utf-8")

    # Two-phase rename: old → temp, then temp → new. This makes swaps and
    # chains (a→b, b→c) safe regardless of ordering.
    run_id = uuid.uuid4().hex[:12]
    temps: list[tuple[Path, Path]] = []  # (temp_path, final_path)
    try:
        for i, (old, new) in enumerate(zip(olds, news)):
            if old == new:
                continue
            src = directory / old
            tmp = directory / f".__rename_{run_id}_{i}.tmp"
            src.rename(tmp)
            temps.append((tmp, directory / new))
        for tmp, final in temps:
            tmp.rename(final)
    except OSError as e:
        # Best-effort: leave temps where they are; undo-log on disk documents
        # intent, and the caller can inspect the directory.
        return jsonify(
            error=f"rename failed mid-run: {e}",
            undo_log=str(undo_path),
            hint="some files may be in .__rename_*.tmp state",
        ), 500

    return jsonify(applied=len(plan), undo_log=str(undo_path), rows=rows)


@app.post("/api/undo")
def api_undo():
    """Replay an undo-log in reverse. Expects {"undo_log": "/abs/path"}."""
    body = request.get_json(silent=True) or {}
    log_path = body.get("undo_log")
    if not isinstance(log_path, str) or not log_path:
        return jsonify(error="`undo_log` is required"), 400
    p = Path(log_path).expanduser().resolve()
    if not p.is_file():
        return jsonify(error=f"undo log not found: {p}"), 404

    data = json.loads(p.read_text(encoding="utf-8"))
    directory = Path(data["dir"]).resolve()
    if not directory.is_dir():
        return jsonify(error=f"original dir no longer exists: {directory}"), 400

    run_id = uuid.uuid4().hex[:12]
    temps: list[tuple[Path, Path]] = []
    # Reverse: each rename {from→to} becomes {to→from}. Two-phase again.
    try:
        for i, step in enumerate(reversed(data["renames"])):
            cur = directory / step["to"]
            tmp = directory / f".__undo_{run_id}_{i}.tmp"
            cur.rename(tmp)
            temps.append((tmp, directory / step["from"]))
        for tmp, final in temps:
            tmp.rename(final)
    except OSError as e:
        return jsonify(error=f"undo failed: {e}"), 500

    # Archive the log so it isn't accidentally replayed again.
    p.rename(p.with_suffix(p.suffix + ".done"))
    return jsonify(undone=len(data["renames"]))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5051, debug=True)
