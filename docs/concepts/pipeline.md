# Pipeline model

A rename run is a **list of ops applied in order** to each filename independently.

```text
for each filename:
    for each op in pipeline:
        filename = op(filename, idx, ctx, params)
```

- `idx` is the zero-based position of the file in the original input list.
  Numbering ops use this to assign sequence numbers.
- `ctx` is a per-run dict shared across all ops and all files. The Flask
  layer populates it with filesystem-derived metadata before the pipeline
  runs (currently `ctx['mtimes']`, populated when the request includes a
  valid `dir`). Ops that need disk reads consult `ctx` rather than touching
  disk themselves — this keeps ops pure and trivially unit-testable.
- Ops never touch disk. They transform strings. This makes them trivially
  unit-testable and makes **preview** literally the same code path as apply.

## JSON shape

```json
{
  "files": ["IMG_0001.JPG", "IMG_0002.JPG"],
  "pipeline": [
    { "op": "case",      "params": { "mode": "lower", "scope": "both" } },
    { "op": "numbering", "params": { "start": 1, "pad": 3, "sep": "_" } }
  ]
}
```

## Why a pipeline instead of one big operation?

BRU and Métamorphose both went this route for the same reason: rename intents
are compositional. "Lowercase the extension **and** strip a prefix **and**
append a sequence number" is three small, well-defined steps rather than one
parameter-bloated mega-op. Every op stays ~30 lines, one docs page, one
set of examples.
