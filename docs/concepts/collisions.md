# Collisions

A **collision** is any situation where applying the pipeline would cause one
rename to clobber another file. Apply refuses to run if *any* row has
`collision: true`.

## What counts as a collision

The preview endpoint flags a row as `collision: true` when either is true:

1. **Self-collision**: two or more input files produce the same `new` name.
2. **External collision**: a row's `new` name equals the *old* name of a
   different file in the input set — i.e. the rename would land on a file
   that's about to be renamed itself.

## What *isn't* flagged (yet)

- A new name that collides with a file **already on disk** but **not in the
  input set** — we don't scan the directory at preview time (preview doesn't
  receive `dir`). Apply's safety is limited to the input set. A future
  enhancement is to pass `dir` optionally to preview for a deep check.

## How collisions are resolved

They aren't, automatically. The user is shown the `⚠ collision` marker and
expected to fix the pipeline (add a [`numbering`](../ops/numbering.md) step,
insert a stem suffix, etc.). A future op `collision_auto_append` could add
`" (2)"`, `" (3)"`, … to collided rows — BRU has this; we don't yet.

## Why this is safe by construction

Even if a caller bypassed the preview UI and hit `/api/apply` directly with a
colliding pipeline, the server re-computes preview and refuses with HTTP 409.
The client preview is advisory; the server is authoritative.
