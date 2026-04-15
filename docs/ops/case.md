# `case` — change letter case

Changes the letter case of the filename. This is the **exemplar op page**: every
other op page uses exactly this structure (What / Parameters / Examples / Edge cases).

## What it does

Applies one of four case transforms (`lower`, `upper`, `title`, `sentence`) to
either the stem, the extension, or both. The dot separating stem and extension
is never touched.

## Parameters

| name    | type                                        | default  | description                                  |
|---------|---------------------------------------------|----------|----------------------------------------------|
| `mode`  | `"lower"` \| `"upper"` \| `"title"` \| `"sentence"` | `"lower"`| How to transform the targeted text.          |
| `scope` | `"stem"` \| `"ext"` \| `"both"`             | `"stem"` | Which part of the filename to transform.     |

`sentence` capitalizes only the first character and lowercases the rest —
`"hello WORLD"` → `"Hello world"`.

## Examples

=== "lower stem"

    ```json
    { "op": "case", "params": { "mode": "lower", "scope": "stem" } }
    ```

    | before           | after            |
    |------------------|------------------|
    | `IMG_0001.JPG`   | `img_0001.JPG`   |
    | `Vacation.TXT`   | `vacation.TXT`   |

=== "lower both"

    ```json
    { "op": "case", "params": { "mode": "lower", "scope": "both" } }
    ```

    | before           | after            |
    |------------------|------------------|
    | `IMG_0001.JPG`   | `img_0001.jpg`   |

=== "title stem"

    ```json
    { "op": "case", "params": { "mode": "title", "scope": "stem" } }
    ```

    | before                    | after                     |
    |---------------------------|---------------------------|
    | `my vacation notes.txt`   | `My Vacation Notes.txt`   |

## Edge cases

- **No extension**: `scope: "ext"` with a name like `README` is a no-op — the
  empty extension is transformed to the empty string.
- **Multiple dots**: only the *last* dot separates stem from extension, so
  `archive.tar.gz` → stem `archive.tar`, ext `.gz`. `title` stem would yield
  `Archive.Tar.gz` (yes, the inner dot gets capitalized by `str.title()` — this
  is Python's behavior and documented as such).
- **Unicode**: `"ß".upper()` is `"SS"` in Python, which grows the filename by one
  character. This is a Unicode fact, not a bug — the op faithfully reflects it.

## See also

- [`replace`](replace.md) — if you want to change casing of only part of the name.
- [Concepts › Pipeline](../concepts/pipeline.md) — how `case` combines with other ops.
