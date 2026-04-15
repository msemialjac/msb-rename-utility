# `insert` — put a literal string at a position in the stem

Inserts `text` at a character position inside the stem. The extension is
always preserved.

## What it does

Inserts `text` at index `at` within the stem. `at` may be:

- a non-negative integer → position from the start (`0` = prepend)
- a negative integer → position from the end (`-1` = before last char)
- the string `"end"` → append to the stem (before the dot-extension)

## Parameters

| name   | type                     | default | description                     |
|--------|--------------------------|---------|---------------------------------|
| `text` | string                   | `""`    | The text to insert. Empty → no-op. |
| `at`   | int \| `"end"`           | `0`     | Position within the stem.        |

## Examples

=== "prepend"

    ```json
    { "op": "insert", "params": { "text": "2024_", "at": 0 } }
    ```

    | before           | after              |
    |------------------|--------------------|
    | `photo.jpg`      | `2024_photo.jpg`   |

=== "append to stem (extension preserved)"

    ```json
    { "op": "insert", "params": { "text": "_edited", "at": "end" } }
    ```

    | before           | after               |
    |------------------|---------------------|
    | `photo.jpg`      | `photo_edited.jpg`  |
    | `archive.tar.gz` | `archive.tar_edited.gz` (last dot is the ext separator) |

=== "negative index"

    ```json
    { "op": "insert", "params": { "text": "-", "at": -2 } }
    ```

    | before           | after            |
    |------------------|------------------|
    | `photo.jpg`      | `pho-to.jpg`     |

## Edge cases

- **Index past end**: clamped to the stem length (`at=999` on a 5-char stem
  acts like `"end"`).
- **Negative past start**: clamped to `0`.
- **No stem**: inserting into a name like `.gitignore` (empty stem) puts the
  text before the dot, e.g. `"X" + ".gitignore"` → `"X.gitignore"`.
