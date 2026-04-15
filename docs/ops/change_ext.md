# `change_ext` — change or add the file extension

Swaps the file extension. Optionally restricted to files whose current
extension matches a specific value.

## Parameters

| name      | type   | default | description                                               |
|-----------|--------|---------|-----------------------------------------------------------|
| `to`      | string | `""`    | New extension (with or without leading dot). `""` removes.|
| `only_if` | string | unset   | If set, only change when current ext matches (case-insensitive). |

## Examples

=== "normalize JPEG → jpg"

    ```json
    { "op": "change_ext", "params": { "to": "jpg", "only_if": "jpeg" } }
    ```

    | before          | after           |
    |-----------------|-----------------|
    | `photo.JPEG`    | `photo.jpg`     |
    | `photo.jpeg`    | `photo.jpg`     |
    | `photo.PNG`     | `photo.PNG`     |

=== "add an extension to an extensionless file"

    ```json
    { "op": "change_ext", "params": { "to": "md" } }
    ```

    | before      | after          |
    |-------------|----------------|
    | `README`    | `README.md`    |
    | `notes.txt` | `notes.md`     |

=== "remove extension entirely"

    ```json
    { "op": "change_ext", "params": { "to": "" } }
    ```

    | before         | after       |
    |----------------|-------------|
    | `backup.bak`   | `backup`    |

## Edge cases

- **Leading dot optional**: `"jpg"` and `".jpg"` behave identically.
- **`only_if` case-insensitive**: `"jpeg"` matches `.JPEG`, `.Jpeg`, etc.
- **`only_if` = `""`**: treated as unset (UI sends empty strings for blank
  fields; we don't want that to mean "match files with no extension" by
  accident).
