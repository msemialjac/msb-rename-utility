# `remove_at` — delete a range of characters from the stem

Removes `count` characters starting at `start` from the stem. Extension preserved.

## Parameters

| name    | type | default | description                                       |
|---------|------|---------|---------------------------------------------------|
| `start` | int  | `0`     | Start position. Negative → from end.              |
| `count` | int  | `0`     | Number of characters to remove. `0` → no-op.      |

## Examples

=== "strip 4-char prefix"

    ```json
    { "op": "remove_at", "params": { "start": 0, "count": 4 } }
    ```

    | before             | after       |
    |--------------------|-------------|
    | `IMG_vacation.jpg` | `vacation.jpg` |

=== "remove from the end"

    ```json
    { "op": "remove_at", "params": { "start": -5, "count": 5 } }
    ```

    | before                | after              |
    |-----------------------|--------------------|
    | `vacation_copy.txt`   | `vacation_.txt`    |

## Edge cases

- **Range past end**: clamped to the stem length. No error.
- **`count: 0`**: no-op (explicit opt-out).
- **Prefer `replace` for known strings**: this op is positional; if you know
  the literal prefix, [`replace`](replace.md) is safer across heterogeneous
  input.
