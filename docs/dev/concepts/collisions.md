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

### Manually (default)

The `⚠ collision` marker is shown and the user is expected to adjust the
pipeline — e.g. add a [`numbering`](../ops/numbering.md) step.

### Automatically (`auto_resolve_collisions: true`)

Pass `auto_resolve_collisions: true` in the request body to enable an
automatic post-pass:

```json
{
  "files": ["IMG_01.JPG", "img_01.jpg"],
  "pipeline": [{ "op": "case", "params": { "mode": "lower", "scope": "both" } }],
  "auto_resolve_collisions": true
}
```

Produces:

| idx | old            | new               |
|----:|----------------|-------------------|
| 0   | `IMG_01.JPG`   | `img_01.jpg`      |
| 1   | `img_01.jpg`   | `img_01 (2).jpg`  |

The post-pass runs *after* the pipeline, so it sees all new names at once and
appends `" (2)"`, `" (3)"`, … to later duplicates. Order is stable: the first
occurrence of each name keeps it.

Why this isn't a regular pipeline op: pipeline ops run per-file and can't see
siblings. The collision post-pass needs the whole batch.

### "Moving out of the way" is not a collision

If two rows `A → B` and `B → C` both rename, there's no real clash: by
end-of-run, `B` is free. Preview used to flag this as an external collision;
since the post-pass fix, it correctly shows no collision. (The two-phase
rename in `/api/apply` guarantees this is safe in practice, regardless of
ordering.)

## Why this is safe by construction

Even if a caller bypassed the preview UI and hit `/api/apply` directly with a
colliding pipeline, the server re-computes preview and refuses with HTTP 409.
The client preview is advisory; the server is authoritative.
