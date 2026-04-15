# Share links

Click **share link** in the toolbar to copy a URL containing the current
pipeline (and optionally the filenames) as a base64-encoded hash. Open that
URL in any browser to restore the setup.

## Why a hash, not a query string

The `#…` portion of a URL never reaches the server — no request logs, no
referer leakage. Safe to paste into chat or a bug report. The app reads
`location.hash` on load and rehydrates the UI.

## What's shared

- ✅ The pipeline (ops + params)
- ✅ The filenames textarea, if non-empty
- ❌ The `dir` field — it's a local path; sharing it could leak personal
  directory structure and wouldn't be useful on another machine anyway.

## Format

```
#p=<urlsafe-b64 of JSON {pipeline, files?}>
```

Example payload before encoding:

```json
{
  "pipeline": [
    { "op": "case",      "params": { "mode": "lower", "scope": "both" } },
    { "op": "numbering", "params": { "start": 1, "pad": 3, "sep": "_" } }
  ],
  "files": "IMG_1.JPG\nIMG_2.JPG"
}
```

## In documentation

Recipe pages can include **Try this** links that prefill the UI. Construct
the URL once, paste it into the docs — readers can click it and see a
working example instantly. (Recipe pages with live examples are a planned
addition — the codec and round-trip are already tested.)
