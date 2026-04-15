# Getting started

## Install & run

```bash
git clone <repo> && cd msb_rename_utility
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5051>.

## Your first rename

1. Paste filenames into the textarea — one per line.
2. Click **+ case**, set `mode = lower`, `scope = both`.
3. Click **preview**. You'll see old/new pairs.
4. `apply` is not wired yet (scaffold) — for now the tool is preview-only.

## Docs build

```bash
pip install mkdocs-material
mkdocs serve    # live preview at http://127.0.0.1:8000
mkdocs build    # static site into ./site/
```
