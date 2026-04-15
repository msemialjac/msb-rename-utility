# msb_rename_utility

A small Flask + vanilla-JS bulk file renamer, inspired by
[Better Rename Utility (BRU)](https://www.publicspace.net/ABetterRenameUtility/) and
[Métamorphose 2](https://sourceforge.net/projects/file-folder-ren/), **clean-room reimplemented**
so the code is free of copyleft obligations and free of legacy Python-2 baggage.

## Design in one paragraph

A rename run is a **pipeline**: a list of ops applied in order to each input filename.
Each op is a pure function `(name, idx, ctx, params) -> name`. The UI builds the
pipeline as JSON and POSTs it to `/api/preview`; the server returns old/new pairs
and a `collision` flag. Nothing is written to disk until `/api/apply` is called —
which in this scaffold is deliberately stubbed until the undo-log is implemented.

## Why another rename tool

- **Free**: MIT-licensed, no ads, no upgrade nags, no macOS-only lock-in.
- **Scriptable**: the pipeline is JSON, so the same config runs from CLI or web UI.
- **Auditable**: every op is a ~30-line pure function, documented one-to-one with
  its docs page. No hidden behavior.

## Sibling project

The visual language (Tokyo Night palette, card layout) mirrors
[`disk-dashboard`](https://github.com/…/disk-dashboard). The two apps are meant
to feel like a suite of single-purpose Flask tools.
