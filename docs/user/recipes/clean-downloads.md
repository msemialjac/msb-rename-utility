# Clean up a messy download folder

**You have:** `Report  final (2).PDF`, `Notes (1).TXT`, `budget  draft.XLSX`
— a downloads folder that went through too many "save as" dialogs.

**You want:** `report final.pdf`, `notes.txt`, `budget draft.xlsx`.

## Try it

1. Open the app.
2. Click [**this link**][link] — four steps prefill.
3. Pick the folder, paste its path into **Directory**, preview, apply.

[link]: http://127.0.0.1:5051/#p=eyJwaXBlbGluZSI6W3sib3AiOiJyZWdleCIsInBhcmFtcyI6eyJwYXR0ZXJuIjoiIFxcKFxcZCtcXCkoPz1cXC5bXi5dKyQpIiwicmVwbCI6IiIsImZsYWdzIjpbXX19LHsib3AiOiJyZXBsYWNlIiwicGFyYW1zIjp7ImZpbmQiOiIgICIsIndpdGgiOiIgIiwiY2FzZV9zZW5zaXRpdmUiOnRydWUsInNjb3BlIjoibmFtZSJ9fSx7Im9wIjoidHJpbSIsInBhcmFtcyI6eyJjaGFycyI6IiAiLCJzaWRlIjoiYm90aCJ9fSx7Im9wIjoiY2FzZSIsInBhcmFtcyI6eyJtb2RlIjoibG93ZXIiLCJzY29wZSI6ImV4dCJ9fV0sImZpbGVzIjoiUmVwb3J0ICBmaW5hbCAoMikuUERGXG5Ob3RlcyAoMSkuVFhUXG5idWRnZXQgIGRyYWZ0LlhMU1gifQ

## What the pipeline does

Four steps stacked, applied in order to every file:

1. **regex** — strip trailing ` (1)`, ` (2)`, … before the extension.
2. **replace** — collapse any double spaces to single spaces.
3. **trim** — remove leading/trailing spaces left over.
4. **case** — lowercase the extension only (so `.PDF` → `.pdf`).

## Common tweaks

- **Want the stem lowercased too?** Add a second `+ case` step with
  `scope: stem`.
- **Different "duplicate" markers?** If your system uses ` - Copy` or
  ` copy` instead of ` (2)`, tweak the regex pattern. See
  [the regex reference](../../dev/ops/regex.md).
