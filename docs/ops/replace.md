# `replace` — literal find/replace

Literal (non-regex) substring replacement. Use [`regex`](regex.md) when you need
patterns, groups, or anchors.

## What it does

Replaces every occurrence of `find` in the filename with `with`. Optionally
case-insensitive. Optionally scoped to just the stem (leaving the extension
alone).

## Parameters

| name             | type              | default | description                                     |
|------------------|-------------------|---------|-------------------------------------------------|
| `find`           | string            | `""`    | Literal substring to match. Empty → no-op.      |
| `with`           | string            | `""`    | Replacement text. Empty string deletes matches. |
| `case_sensitive` | bool              | `true`  | When `false`, matches regardless of case.       |
| `scope`          | `"name"` \| `"stem"` | `"name"`| `"stem"` protects the extension from changes.   |

## Examples

=== "strip a prefix"

    ```json
    { "op": "replace", "params": { "find": "IMG_", "with": "" } }
    ```

    | before           | after       |
    |------------------|-------------|
    | `IMG_0001.JPG`   | `0001.JPG`  |
    | `vacation.txt`   | `vacation.txt` (unchanged) |

=== "rename a word, case-insensitive"

    ```json
    { "op": "replace", "params": { "find": "draft", "with": "final", "case_sensitive": false } }
    ```

    | before                | after                |
    |-----------------------|----------------------|
    | `Draft_report.pdf`    | `final_report.pdf`   |
    | `DRAFT-notes.md`      | `final-notes.md`     |

=== "protect the extension"

    ```json
    { "op": "replace", "params": { "find": "photo", "with": "X", "scope": "stem" } }
    ```

    | before              | after              |
    |---------------------|--------------------|
    | `photo.photo`       | `X.photo`          |

## Edge cases

- **Empty `find`**: returns the filename unchanged (we don't expand empty-match
  insertion-between-every-char — that's a regex concern, not literal replace).
- **Overlapping matches**: resolved left-to-right, like Python's `str.replace`.
- **Case-insensitive**: implemented without regex so `find` can contain regex
  metacharacters (`.`, `*`, `(`, etc.) without escaping.

## See also

- [`regex`](regex.md) — for patterns and backreferences.
- [`case`](case.md) — if you only need to change letter case.
