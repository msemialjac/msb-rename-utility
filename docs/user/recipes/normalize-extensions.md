# Normalize extensions (`.JPEG` → `.jpg`)

**You have:** a camera folder with `photo1.JPEG`, `photo2.jpeg`,
`photo3.JPG`, `photo4.png` — a mess of casing and spellings.

**You want:** everything standardized to `.jpg`, except PNGs which should
stay as PNGs.

## Try it

Click [**this link**][link], pick the folder, preview, apply.

[link]: http://127.0.0.1:5051/#p=eyJwaXBlbGluZSI6W3sib3AiOiJjaGFuZ2VfZXh0IiwicGFyYW1zIjp7InRvIjoianBnIiwib25seV9pZiI6ImpwZWcifX1dLCJmaWxlcyI6InBob3RvMS5KUEVHXG5waG90bzIuanBlZ1xucGhvdG8zLkpQR1xucGhvdG80LnBuZyJ9

## What the pipeline does

One step: **change_ext** with `to: jpg` and `only_if: jpeg`. The `only_if`
match is case-insensitive, so it catches both `.JPEG` and `.jpeg`.
`.JPG` and `.png` don't match `jpeg`, so they're left alone.

Want to *also* lowercase the existing `.JPG` entries? Add a second step:

1. **change_ext** to `jpg`, only_if `JPG` (to normalize case).

Or use a `case` step with `scope: ext` to lowercase every extension
unconditionally.

## Common tweaks

- **Different target format?** Change `to` to whatever you want — `png`,
  `webp`, `heic`.
- **Leave specific originals alone?** Add a second step earlier in the
  pipeline that moves them out of scope, or just don't include them in the
  files list.
