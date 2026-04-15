# Zero-pad episode numbers

**You have:** TV-show files named `mystuff.s1e1.mkv`, `mystuff.s1e2.mkv`,
`mystuff.s1e10.mkv`. They sort wrong: `e10` shows up between `e1` and `e2`.

**You want:** `mystuff.s01e01.mkv`, `mystuff.s01e02.mkv`,
`mystuff.s01e10.mkv` — every number two digits wide, so they sort right.

## Try it

1. Open the app.
2. Click [**this link**][link] — the pipeline prefills.
3. Click **pick folder…** and pick your show's folder, or paste filenames
   manually.
4. Paste the folder path into **Directory**, click **preview**, then
   **apply**.

[link]: http://127.0.0.1:5051/#p=eyJwaXBlbGluZSI6W3sib3AiOiJwYWQiLCJwYXJhbXMiOnsid2lkdGgiOjIsInNjb3BlIjoic3RlbSJ9fV0sImZpbGVzIjoibXlzdHVmZi5zMWUxLm1rdlxubXlzdHVmZi5zMWUyLm1rdlxubXlzdHVmZi5zMWUxMC5ta3YifQ

## What the pipeline does

One step: **pad** with width 2. Every run of digits in the filename gets
zero-padded to at least two characters. Runs already wider (like `10`)
stay as they are.

## Common tweaks

- **Three-digit years or long series?** Change width to `3` or `4`.
- **Don't want to pad the season too?** `pad` hits *every* digit run. If
  you only want the episode padded, you'd need a **regex** step instead
  — ask in an issue if you need that recipe.
