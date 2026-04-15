# `trim` — strip leading/trailing characters

Removes characters from the edges of the stem. The extension is untouched.

## What it does

Equivalent to Python's `str.strip` / `lstrip` / `rstrip` applied to the stem.
Default strips whitespace.

## Parameters

| name    | type                            | default | description                          |
|---------|---------------------------------|---------|--------------------------------------|
| `chars` | string                          | `""` (= whitespace) | Characters to strip, any order. |
| `side`  | `"both"` \| `"left"` \| `"right"` | `"both"` | Which edge to strip.             |

## Examples

=== "strip whitespace"

    ```json
    { "op": "trim", "params": {} }
    ```

    | before          | after         |
    |-----------------|---------------|
    | `  notes  .txt` | `notes.txt`   |

=== "strip underscores"

    ```json
    { "op": "trim", "params": { "chars": "_" } }
    ```

    | before            | after       |
    |-------------------|-------------|
    | `__draft__.md`    | `draft.md`  |

=== "strip leading dots only"

    ```json
    { "op": "trim", "params": { "chars": ".", "side": "left" } }
    ```

    | before           | after          |
    |------------------|----------------|
    | `..hidden.txt`   | `hidden.txt`   |

## Edge cases

- **Empty `chars`**: strips Python's default whitespace set (`" \t\n\r…"`).
- **Multi-char `chars`**: treated as a *set* of chars, not a substring. `"ab"`
  strips any `a` or `b` from the edges (matches `str.strip` semantics).
