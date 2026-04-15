# File pickers

Two small buttons above the filenames textarea:

- **pick files…** — multi-file picker; fills the textarea with basenames.
- **pick folder…** — folder picker (Chromium only); fills the textarea with
  basenames of every file in the chosen folder.

## The `dir` field is **not** auto-filled

Browsers deliberately hide absolute filesystem paths from JavaScript (to
prevent fingerprinting and local-path leakage). The pickers give us
filenames and a *relative* folder name, but never the absolute path where
those files live.

Consequence: to use `/api/apply`, you still have to type or paste the
directory into the `dir` field manually. The picker is a convenience for
the filenames list, not an escape hatch around the path restriction.

## Browser support

- **pick files…**: every browser.
- **pick folder…**: uses `<input webkitdirectory>`. Works in Chromium
  (Chrome, Edge, Opera, Brave). Firefox has partial support; Safari support
  is best-effort. Everywhere it's unsupported, the button falls back to a
  single-file picker.

## Why no automated test

This feature lives entirely in the browser's file-picker dialog — an OS
modal, not DOM. Automating it requires Playwright / a real browser driver
and is out of scope for the pytest suite. Covered manually: pick a folder,
verify the textarea populates and `/api/preview` returns sensible rows.
