"""msb_rename_utility — Flask micro-app.

Endpoints:
  GET  /             single-page UI
  POST /api/preview  compute new names + collision flags (no writes)
  POST /api/apply    rename files on disk with a two-phase swap-safe strategy
                     and a JSON undo-log sidecar written before any rename
  POST /api/undo     replay an undo-log in reverse (verifies log filename
                     matches UNDO_LOG_PREFIX to prevent crafted-log abuse)
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
from ops import collision as collision_resolve

app = Flask(__name__)

UNDO_LOG_PREFIX = ".rename-undo-"
UNDO_LOG_SUFFIX = ".json"
# Reject names containing path separators or NUL. The input-filename sanity
# check additionally rejects anything that isn't already a basename, because
# silently stripping a directory component would let a caller rename a file
# they didn't name.
_BAD_NAME_RE = re.compile(r"[/\x00]")
_PATH_SEP_RE = re.compile(r"[/\\]")


def _compute_rows(
    files: list[str],
    pipeline: list[dict],
    auto_resolve: bool = False,
    directory: Path | None = None,
    metadata: dict[str, tuple[bool, float]] | None = None,
) -> tuple[list[dict], list[str], list[str]]:
    """Run the pipeline and annotate each row. Returns (rows, olds, news).

    `metadata`, if supplied, is a pre-fetched map `basename -> (exists, mtime)`
    so the caller can do a single filesystem scan and share it between the
    `ctx` population here and the existence/collision checks in `/api/apply`.
    When not supplied and `directory` is given, we stat on demand.
    """
    bases = [Path(f).name for f in files]

    ctx: dict = {}
    if directory is not None and directory.is_dir():
        if metadata is None:
            metadata = {}
            for b in bases:
                p = directory / b
                metadata[b] = (p.exists(), p.stat().st_mtime if p.exists() else 0.0)
        ctx["mtimes"] = [metadata.get(b, (False, 0.0))[1] for b in bases]

    news = run_pipeline(bases, pipeline, ctx=ctx)
    if auto_resolve:
        news = collision_resolve.resolve(news)
    new_counts = Counter(news)
    # External-in-batch collision: only counts against inputs NOT being moved.
    stationary_olds = {o for o, n in zip(bases, news) if o == n}

    rows = []
    for old, new in zip(bases, news):
        collides_self = new_counts[new] > 1
        collides_other = (new in stationary_olds) and (new != old)
        rows.append({
            "old": old,
            "new": new,
            "unchanged": old == new,
            "collision": collides_self or collides_other,
        })
    return rows, bases, news


def _validate_basenames(files: list[str]) -> str | None:
    """Return an error message if any entry contains a path separator; else None.

    We refuse to silently `.name`-strip directory components because a caller
    sending "../etc/passwd" and receiving "passwd" back would be operating on
    a different file than they think.
    """
    for f in files:
        if _PATH_SEP_RE.search(f):
            return f"filenames must be basenames (got {f!r})"
    return None


def _scan_directory(directory: Path, bases: list[str]) -> dict[str, tuple[bool, float]]:
    """Single-pass stat for all basenames. Returns `{name: (exists, mtime)}`."""
    out: dict[str, tuple[bool, float]] = {}
    for b in bases:
        p = directory / b
        if p.exists():
            out[b] = (True, p.stat().st_mtime)
        else:
            out[b] = (False, 0.0)
    return out


def _parse_dir(raw: object) -> Path | None:
    """Resolve a user-supplied dir. `expanduser()` removed deliberately —
    `~` resolved relative to the server process isn't what a remote caller
    means, and removing it narrows the path-traversal surface."""
    if not isinstance(raw, str) or not raw:
        return None
    return Path(raw).resolve()


@app.route("/")
def index():
    # `DOCS_URL` env var lets a deployment point the toolbar link at a hosted
    # docs site (e.g. GitHub Pages). Default is the local mkdocs dev server.
    docs_url = os.environ.get("DOCS_URL", "http://127.0.0.1:8000/")
    return render_template("index.html", docs_url=docs_url)


@app.post("/api/preview")
def api_preview():
    body = request.get_json(silent=True) or {}
    files = body.get("files") or []
    pipeline = body.get("pipeline") or []

    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        return jsonify(error="`files` must be a list of strings"), 400
    if not isinstance(pipeline, list):
        return jsonify(error="`pipeline` must be a list"), 400
    err = _validate_basenames(files)
    if err:
        return jsonify(error=err), 400

    auto_resolve = bool(body.get("auto_resolve_collisions", False))
    directory = _parse_dir(body.get("dir"))
    try:
        rows, _, _ = _compute_rows(
            files, pipeline, auto_resolve=auto_resolve, directory=directory
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(rows)


@app.post("/api/apply")
def api_apply():
    """Rename files on disk. Safety ordering:
      1. Validate request shape and basenames.
      2. Validate directory exists.
      3. Single-pass stat of all inputs (shared with ctx population).
      4. Run pipeline and detect in-batch collisions.
      5. Reject if any new name clashes with an existing file on disk that
         isn't itself being moved out of the way.
      6. Write undo-log sidecar (unique filename with UUID — no timestamp
         collisions between rapid successive calls).
      7. Two-phase rename. On mid-run OSError, roll back the phase-1 temps
         we successfully moved, then return 500.
    """
    body = request.get_json(silent=True) or {}
    files = body.get("files") or []
    pipeline = body.get("pipeline") or []
    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        return jsonify(error="`files` must be a list of strings"), 400
    if not isinstance(pipeline, list):
        return jsonify(error="`pipeline` must be a list"), 400
    err = _validate_basenames(files)
    if err:
        return jsonify(error=err), 400

    directory = _parse_dir(body.get("dir"))
    if directory is None:
        return jsonify(error="`dir` is required"), 400
    if not directory.is_dir():
        return jsonify(error=f"not a directory: {directory}"), 400

    bases = [Path(f).name for f in files]
    metadata = _scan_directory(directory, bases)

    auto_resolve = bool(body.get("auto_resolve_collisions", False))
    try:
        rows, olds, news = _compute_rows(
            files, pipeline, auto_resolve=auto_resolve,
            directory=directory, metadata=metadata,
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400

    # Hard refusals.
    if any(r["collision"] for r in rows):
        return jsonify(error="pipeline produces collisions — refusing to apply"), 409
    for new in news:
        if not new or _BAD_NAME_RE.search(new):
            return jsonify(error=f"invalid new name: {new!r}"), 400

    # Missing-source check (reuses the already-done stat).
    missing = [o for o in olds if not metadata.get(o, (False, 0.0))[0]]
    if missing:
        return jsonify(error=f"missing on disk: {missing}"), 404

    # External-on-disk clobber: refuse if a new name matches a file in `dir`
    # that isn't itself being renamed. This needs a fresh stat for names not
    # already covered by `metadata`.
    moving_olds = {o for o, n in zip(olds, news) if o != n}
    for old, new in zip(olds, news):
        if old == new:
            continue
        if new in moving_olds:
            continue  # will be freed during the run
        if new in metadata and metadata[new][0]:
            return jsonify(error=f"would clobber existing file: {new!r}"), 409
        if new not in metadata and (directory / new).exists():
            return jsonify(error=f"would clobber existing file: {new!r}"), 409

    # Unique undo-log filename. Timestamps are only second-precision; two
    # rapid calls would otherwise silently overwrite the first log and
    # destroy recovery information. UUID suffix guarantees uniqueness.
    run_id = uuid.uuid4().hex[:12]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    undo_path = directory / f"{UNDO_LOG_PREFIX}{stamp}-{run_id}{UNDO_LOG_SUFFIX}"
    plan = [{"from": o, "to": n} for o, n in zip(olds, news) if o != n]
    undo_path.write_text(json.dumps({
        "dir": str(directory),
        "created": stamp,
        "run_id": run_id,
        "renames": plan,
    }, indent=2), encoding="utf-8")

    # Two-phase rename, each step tracked so we can roll back on failure.
    # phase1: list of (original_old_name, tmp_path, final_path) we moved into tmp.
    # phase2: list of final paths we already moved to their final name.
    phase1: list[tuple[str, Path, Path]] = []
    phase2: list[Path] = []
    moves = [(o, n) for o, n in zip(olds, news) if o != n]
    try:
        for i, (old, new) in enumerate(moves):
            src = directory / old
            tmp = directory / f".__rename_{run_id}_{i}.tmp"
            src.rename(tmp)
            phase1.append((old, tmp, directory / new))
        for _old, tmp, final in phase1:
            tmp.rename(final)
            phase2.append(final)
    except OSError as e:
        rollback_errors = _rollback_apply(phase1, phase2, directory)
        # The undo-log described the intended plan, not the rolled-back state.
        # Remove it so a later /api/undo can't replay against restored files.
        try:
            undo_path.unlink(missing_ok=True)
        except OSError:
            pass
        msg = f"rename failed mid-run: {e}"
        if rollback_errors:
            msg += f" · rollback partial: {'; '.join(rollback_errors)}"
        return jsonify(error=msg), 500

    return jsonify(applied=len(plan), undo_log=str(undo_path), rows=rows)


def _rollback_apply(
    phase1: list[tuple[str, Path, Path]],
    phase2: list[Path],
    directory: Path,
) -> list[str]:
    """Reverse phase-1/phase-2 renames. Returns human-readable error strings."""
    errors: list[str] = []
    # Undo phase-2 first: any file that reached its final name goes back to
    # its temp name so the phase-1 rollback step can treat it uniformly.
    final_set = set(phase2)
    for old, tmp, final in phase1:
        if final in final_set:
            try:
                final.rename(tmp)
            except OSError as e:
                errors.append(f"rollback phase-2 {final.name}: {e}")
    # Undo phase-1: every tmp goes back to its original source name.
    for old, tmp, _final in phase1:
        try:
            if tmp.exists():
                tmp.rename(directory / old)
        except OSError as e:
            errors.append(f"rollback phase-1 {tmp.name}: {e}")
    return errors


@app.post("/api/undo")
def api_undo():
    """Replay an undo-log in reverse.

    Safety: the referenced file must be named `.rename-undo-*.json` (our own
    prefix) to prevent a caller from pointing at an arbitrary JSON file that
    happens to look plan-shaped. The log's `dir` is also validated and the
    JSON shape is checked before any filesystem mutation.
    """
    body = request.get_json(silent=True) or {}
    log_path = body.get("undo_log")
    if not isinstance(log_path, str) or not log_path:
        return jsonify(error="`undo_log` is required"), 400
    p = Path(log_path).resolve()
    if not p.is_file():
        return jsonify(error=f"undo log not found: {p}"), 404
    if not p.name.startswith(UNDO_LOG_PREFIX) or not p.name.endswith(UNDO_LOG_SUFFIX):
        return jsonify(error=f"not a valid undo-log filename: {p.name}"), 400

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return jsonify(error=f"undo log is not valid JSON: {e}"), 400
    if not isinstance(data, dict):
        return jsonify(error="undo log must be a JSON object"), 400
    renames = data.get("renames")
    raw_dir = data.get("dir")
    if not isinstance(renames, list) or not isinstance(raw_dir, str):
        return jsonify(error="undo log missing `renames` list or `dir` string"), 400
    for step in renames:
        if not (isinstance(step, dict)
                and isinstance(step.get("from"), str)
                and isinstance(step.get("to"), str)):
            return jsonify(error="every rename entry must be {from, to} strings"), 400

    directory = Path(raw_dir).resolve()
    if not directory.is_dir():
        return jsonify(error=f"original dir no longer exists: {directory}"), 400

    run_id = uuid.uuid4().hex[:12]
    completed: list[tuple[Path, str]] = []  # (tmp_path, original_to_name)
    try:
        for i, step in enumerate(reversed(renames)):
            cur = directory / step["to"]
            tmp = directory / f".__undo_{run_id}_{i}.tmp"
            cur.rename(tmp)
            completed.append((tmp, step["to"]))
        # Phase 2: temps → original `from` names.
        for (tmp, _), step in zip(completed, list(reversed(renames))):
            tmp.rename(directory / step["from"])
    except OSError as e:
        rollback_errors: list[str] = []
        # Put temps back to their `to` names so the user's state matches the
        # post-apply state (not a weird hybrid).
        for (tmp, to_name) in completed:
            try:
                if tmp.exists():
                    tmp.rename(directory / to_name)
            except OSError as rb_e:
                rollback_errors.append(str(rb_e))
        msg = f"undo failed: {e}"
        if rollback_errors:
            msg += f" · rollback partial: {'; '.join(rollback_errors)}"
        return jsonify(error=msg), 500

    # Archive the log so a double-replay is rejected by the 404 check above.
    p.rename(p.with_suffix(p.suffix + ".done"))
    return jsonify(undone=len(renames))


if __name__ == "__main__":
    # `debug=True` exposes Werkzeug's interactive REPL at /__debugger__ —
    # arbitrary code execution if the PIN is obtained. Off by default;
    # opt-in via env var for local iteration.
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="127.0.0.1", port=5051, debug=debug)
