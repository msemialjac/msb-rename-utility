# User Guide

Short, task-first recipes. Pick the one that matches what you want to do,
open the app in your browser, click the recipe's **Try it** link — the UI
prefills, you preview, you apply.

## Running the app

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5051>. The page has:

- A **files** textarea — one filename per line. Use **pick folder…** to fill
  it from any folder on your computer.
- A **pipeline** area — click `+ case`, `+ replace`, etc., to add steps.
- **preview** — shows what would happen, never touches your files.
- **apply** — actually renames on disk. You have to type the folder path
  into **Directory** first (browsers don't give websites your local paths).
- **undo last** — reverses the most recent apply using the undo-log the
  server wrote into your folder.

## Recipes

- [Rename photos by date taken](recipes/photos-by-date.md)
- [Zero-pad episode numbers](recipes/pad-episodes.md)
- [Clean up a messy download folder](recipes/clean-downloads.md)
- [Normalize extensions (`.JPEG` → `.jpg`)](recipes/normalize-extensions.md)

## Things to know

- **Nothing is uploaded.** When you click **pick folder…**, the browser
  reads only filenames. No file contents leave your computer.
- **Apply requires the directory path.** Browsers hide local paths from
  websites, so the picker can fill the files list but you paste the
  directory into the **Directory** field yourself.
- **Every apply is reversible.** A file called
  `.rename-undo-<timestamp>.json` appears in the folder; click **undo
  last** in the toolbar or keep the file for later.
- **Preview is free, apply is careful.** The server re-runs preview before
  applying and refuses if anything looks wrong (collisions, missing files,
  illegal names).

Curious *how* any of it works? Head over to the
[Developer Reference](../dev/getting-started.md).
