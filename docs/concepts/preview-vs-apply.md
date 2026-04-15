# Preview vs apply

The app has two endpoints that look similar but differ in one critical way: **preview
touches nothing, apply mutates disk.**

## Preview (`POST /api/preview`)

- Accepts `files` (list of basenames) and `pipeline`.
- Runs the pipeline in-memory and returns `[{old, new, unchanged, collision}]`.
- **No `dir` needed.** The endpoint doesn't know or care where the files live.
- Safe to call on every keystroke.

## Apply (`POST /api/apply`)

- Requires `dir` in addition to `files` and `pipeline`.
- **Re-runs preview server-side** — the UI's preview is hint, not promise.
- Refuses if any row has `collision: true`, any new name is empty / contains
  `/`, any file is missing on disk, or `dir` isn't a directory.
- Writes an undo-log JSON sidecar into `dir` **before** the first rename.
- Performs renames in two phases: old → `.__rename_<uuid>_<i>.tmp`, then tmp →
  new. This makes the intermediate state collision-free regardless of order.
- Returns `{applied, undo_log, rows}`.

## Why two endpoints instead of one

The same code path (`run_pipeline`) computes both. Splitting the endpoints
makes apply's safety gates explicit and makes preview cacheable / retriable
without side effects. If a single endpoint with a `dry_run` flag feels nicer,
consider it a layering choice — this project chose separation because the
safety story is simpler to audit.

## Undo

`POST /api/undo` takes the `undo_log` path the server returned, replays the
renames in reverse (also two-phase), and archives the log with a `.done`
suffix so it can't be replayed again by accident. If you lose the path, the
log is sitting in the target directory as `.rename-undo-<timestamp>.json`.
