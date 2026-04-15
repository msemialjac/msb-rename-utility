# `regex` — pattern find/replace

Python `re.sub` over the filename. Supports groups and backreferences.

## What it does

Applies `re.sub(pattern, repl, target, flags=...)` to the filename (or stem).
`repl` supports Python's `\1`, `\g<name>`, etc.

## Parameters

| name      | type                  | default  | description                                            |
|-----------|-----------------------|----------|--------------------------------------------------------|
| `pattern` | string (Python regex) | `""`     | Empty → no-op. Compile errors return HTTP 400.         |
| `repl`    | string                | `""`     | Replacement. Supports `\1`, `\2`, `\g<name>`.          |
| `flags`   | list of chars         | `[]`     | Any of `"i"` (ignorecase), `"m"` (multiline), `"s"` (dotall). |
| `scope`   | `"name"` \| `"stem"`  | `"name"` | Whether the extension participates in the match.       |

## Examples

=== "rename by capture group"

    ```json
    { "op": "regex", "params": { "pattern": "IMG_(\\d+)", "repl": "photo_\\1" } }
    ```

    | before           | after          |
    |------------------|----------------|
    | `IMG_0001.JPG`   | `photo_0001.JPG` |
    | `IMG_42-edit.png`| `photo_42-edit.png` |

=== "strip trailing ' (1)' / ' (2)' duplicates"

    ```json
    { "op": "regex", "params": { "pattern": " \\(\\d+\\)(?=\\.[^.]+$)", "repl": "", "scope": "name" } }
    ```

    | before                     | after                |
    |----------------------------|----------------------|
    | `report (1).pdf`           | `report.pdf`         |
    | `notes (12).txt`           | `notes.txt`          |
    | `vacation.txt`             | `vacation.txt`       |

=== "extract date from mixed prefix (case-insensitive)"

    ```json
    {
      "op": "regex",
      "params": {
        "pattern": "^(IMG|DSC)_(\\d{4})(\\d{2})(\\d{2}).*",
        "repl":    "\\2-\\3-\\4",
        "flags":   ["i"]
      }
    }
    ```

    | before                | after         |
    |-----------------------|---------------|
    | `img_20240413_9.jpg`  | `2024-04-13.jpg` (if `scope="stem"`; otherwise the ext is also rewritten) |

## Edge cases

- **Invalid pattern**: the server returns HTTP 400 with the `re.error` message.
- **Empty `pattern`**: no-op (we don't want empty-match insertion semantics).
- **Partial matches**: `re.sub` replaces *all* non-overlapping matches by default.
  Use `^...$` anchors if you need "exactly the whole name."
- **BRU-flavor regex**: BRU uses its own PCRE-ish dialect. This op is Python
  `re` — document differences rather than emulate. Most common BRU patterns
  work unchanged; PCRE-only features (e.g. recursion `(?R)`, possessive
  quantifiers `*+`) do not.

## See also

- [`replace`](replace.md) — if you don't need patterns, prefer literal replace.
