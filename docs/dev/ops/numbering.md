# `numbering` — sequential numbers

Assigns a sequential number to each file based on its position in the input
list (`idx`). Commonly used as the last step of a pipeline, after names have
been normalized.

## What it does

For each file, computes `n = start + idx * step`, optionally zero-pads it to
`pad` digits, then places it before or after the stem, separated by `sep`.
The extension is preserved.

## Parameters

| name       | type                          | default    | description                                |
|------------|-------------------------------|------------|--------------------------------------------|
| `start`    | int                           | `1`        | Number assigned to the first input file.   |
| `step`     | int                           | `1`        | Delta between consecutive files.           |
| `pad`      | int                           | `0`        | Zero-pad width. `0` = no padding.          |
| `position` | `"suffix"` \| `"prefix"`      | `"suffix"` | Where to place the number relative to stem.|
| `sep`      | string                        | `"_"`      | Separator between stem and number.         |

## Examples

=== "zero-padded suffix"

    ```json
    { "op": "numbering", "params": { "start": 1, "pad": 3 } }
    ```

    | idx | before       | after          |
    |----:|--------------|----------------|
    | 0   | `photo.jpg`  | `photo_001.jpg` |
    | 1   | `cover.jpg`  | `cover_002.jpg` |
    | 2   | `back.jpg`   | `back_003.jpg`  |

=== "prefix with custom separator"

    ```json
    { "op": "numbering", "params": { "start": 10, "pad": 2, "position": "prefix", "sep": "-" } }
    ```

    | idx | before       | after             |
    |----:|--------------|-------------------|
    | 0   | `photo.jpg`  | `10-photo.jpg`    |
    | 1   | `cover.jpg`  | `11-cover.jpg`    |

=== "step by 10 (gap-leaving)"

    ```json
    { "op": "numbering", "params": { "start": 10, "step": 10, "pad": 3 } }
    ```

    | idx | after           |
    |----:|-----------------|
    | 0   | `a_010.jpg`     |
    | 1   | `a_020.jpg`     |
    | 2   | `a_030.jpg`     |

## Edge cases

- **`idx` is pre-sort**: the zero-based position in the input list as received.
  If you want numbering in a specific order (alphabetical, by mtime), sort on
  the client side before sending the list to `/api/preview`.
- **`pad` too small**: if the computed number exceeds `pad` digits, it's
  rendered at its natural width — we never truncate numbers. `pad=2` with
  `start=99` yields `99`, `100`, `101`, …
- **Negative `step`**: allowed. `start=100, step=-1` counts down.

## See also

- [Concepts › Pipeline](../concepts/pipeline.md) — on why `idx` is per-file,
  not per-op.
