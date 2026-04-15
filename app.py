"""msb_rename_utility — Flask micro-app.

Preview-only scaffold. /api/apply is deliberately stubbed until the pipeline
schema and undo-log format are nailed down.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from ops import run_pipeline

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/preview")
def api_preview():
    """Body: {"files": ["a.txt", ...], "pipeline": [{"op": "...", "params": {...}}]}.

    Returns [{old, new, collision, unchanged}]. `collision` is true when the
    new name duplicates another new name *or* an input name not owned by this
    row — i.e. the rename would clobber something.
    """
    body = request.get_json(silent=True) or {}
    files = body.get("files") or []
    pipeline = body.get("pipeline") or []

    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        return jsonify(error="`files` must be a list of strings"), 400
    if not isinstance(pipeline, list):
        return jsonify(error="`pipeline` must be a list"), 400

    # Only the filename portion is mangled; directory stays untouched.
    bases = [Path(f).name for f in files]
    try:
        new_bases = run_pipeline(bases, pipeline)
    except ValueError as e:
        return jsonify(error=str(e)), 400

    # Collision detection: count duplicates among the new names, and flag any
    # new name that matches an *existing* input name owned by a different row.
    new_counts = Counter(new_bases)
    old_set = set(bases)

    rows = []
    for i, (old, new) in enumerate(zip(bases, new_bases)):
        collides_self = new_counts[new] > 1
        collides_other = (new in old_set) and (new != old)
        rows.append({
            "old": old,
            "new": new,
            "unchanged": old == new,
            "collision": collides_self or collides_other,
        })
    return jsonify(rows)


@app.post("/api/apply")
def api_apply():
    """Stubbed. Will: re-preview, verify no collisions, rename on disk,
    write undo-log JSON alongside. Deliberately refused until that lands."""
    return jsonify(error="apply endpoint not yet implemented — preview-only scaffold"), 501


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5051, debug=True)
