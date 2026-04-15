# `date_from_mtime` — prepend/append a date from file mtime

Stamps each filename with its own modification time. The date comes from the
filesystem, not the current clock.

## What it does

Reads each file's modification time (UTC), formats it with a `strftime`
string, and splices the result into the name as a prefix or suffix.

This op is the first to require **filesystem read access**. The request must
include a `dir`, which the server uses to `stat` each file *before* running
the pipeline. The mtimes are stashed in a per-run `ctx` that the op reads —
the op itself never touches disk.

## Parameters

| name       | type                     | default      | description                                      |
|------------|--------------------------|--------------|--------------------------------------------------|
| `format`   | strftime string          | `"%Y-%m-%d"` | Any Python `strftime` directive is allowed.      |
| `position` | `"prefix"` \| `"suffix"` | `"prefix"`   | Where to place the date relative to the stem.    |
| `sep`      | string                   | `"_"`        | Separator between date and stem.                 |

## Examples

=== "date prefix"

    ```json
    { "op": "date_from_mtime", "params": { "format": "%Y-%m-%d" } }
    ```

    File `photo.jpg` with mtime 2024-04-13 →
    `2024-04-13_photo.jpg`.

=== "sortable timestamp suffix"

    ```json
    {
      "op": "date_from_mtime",
      "params": { "format": "%Y%m%d-%H%M", "position": "suffix", "sep": "-" }
    }
    ```

    `note.txt` (mtime 2024-04-13 15:30 UTC) → `note-20240413-1530.txt`.

## Edge cases

- **Missing `dir`**: the request fails with HTTP 400 and a message pointing
  you at the `dir` field. Silent fallback would produce wrong dates.
- **File doesn't exist on disk**: mtime is recorded as `0.0` (epoch) so the
  formatter still runs; you'll see `1970-01-01`. Fix your input list rather
  than relying on this.
- **Timezone**: always UTC. Local-time stamps encourage ambiguity across
  systems; if you need local, format with `%Y-%m-%d` (date is identical in
  most time zones) or wait for a timezone param.

## See also

- [Concepts › Pipeline](../concepts/pipeline.md) — on how `ctx` is populated.
