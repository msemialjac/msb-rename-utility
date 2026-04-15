# `pad` — zero-pad numeric runs

Zero-pads every maximal run of digits in the filename to a fixed width.

## What it does

Finds each continuous run of `0-9` and left-pads it with zeros to `width`
characters. Runs already ≥ `width` wide are left alone. Multiple runs in one
name are padded independently.

## Parameters

| name    | type                  | default  | description                              |
|---------|-----------------------|----------|------------------------------------------|
| `width` | int                   | `0`      | Target width. `0` → no-op.               |
| `scope` | `"stem"` \| `"name"`  | `"stem"` | `"name"` also pads digits in the ext.    |

## Examples

=== "simple"

    ```json
    { "op": "pad", "params": { "width": 4 } }
    ```

    | before          | after             |
    |-----------------|-------------------|
    | `IMG_7.jpg`     | `IMG_0007.jpg`    |
    | `IMG_10000.jpg` | `IMG_10000.jpg` (already wider) |

=== "multiple runs"

    ```json
    { "op": "pad", "params": { "width": 3 } }
    ```

    | before           | after               |
    |------------------|---------------------|
    | `s1e2.mkv`       | `s001e002.mkv`      |
    | `2024-4-13.txt`  | `2024-004-013.txt`  |

## Edge cases

- **No digits**: the name is returned unchanged.
- **`width: 0`**: no-op (explicit opt-out).
- **`scope: "name"`**: digits *inside* the extension are also padded. Rarely
  what you want; default is `"stem"`.
