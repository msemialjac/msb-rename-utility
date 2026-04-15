# File pickers

Two buttons above the filenames textarea:

- **pick files…** — select one or more individual files.
- **pick folder…** — select a whole folder; fills the textarea with every
  file's name.

## Two implementations, picked per browser

| Browser                   | API used                                 | Dialog label        | Buffers file bodies? |
|---------------------------|------------------------------------------|---------------------|----------------------|
| Chrome / Edge / Opera     | [File System Access API][fs-api]         | "Select folder"     | No — names only      |
| Firefox / Safari          | `<input type="file" webkitdirectory>`    | "Upload" (browser native) | References held, bytes only on explicit read |

[fs-api]: https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API

The File System Access path only enumerates names — we never call
`.getFile()`, so no bytes are read. The `<input>` fallback does hold `File`
objects in memory; the browser labels its own dialog "Upload" even though
the site never uploads anything (historical wording, because file inputs
were originally for form submissions).

In both cases, **no data leaves the browser**. Everything we read is
`entry.name` or `file.name` — strings. The server only sees what you
explicitly send via preview/apply.

## The `dir` field is **not** auto-filled

Browsers hide absolute filesystem paths from JavaScript, regardless of
which API is used. To use `/api/apply` you still type the directory
manually in the `dir` field. The picker's only job is to save you from
typing filenames.

## Why no automated test

Both picker dialogs are native OS modals, not DOM. Testing them requires
Playwright / a real browser driver. The logic that *consumes* the pick
result (splitting paths, deduping, filling the textarea) is small enough
that manual verification covers it; if it grows, we'll extract it and add
Jest or Vitest.
