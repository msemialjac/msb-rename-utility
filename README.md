# msb_rename_utility

Small Flask + vanilla-JS bulk file renamer. Clean-room-reimplemented engine
inspired by [Métamorphose 2](https://sourceforge.net/projects/file-folder-ren/)
and [A Better Rename Utility](https://www.publicspace.net/ABetterRenameUtility/).

> **Scaffold status** — preview-only. `/api/apply` is deliberately stubbed until
> the undo-log format is nailed down. 5 core ops so far: `case`, `replace`,
> `regex`, `insert`, `numbering`.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py                    # http://127.0.0.1:5051
```

Docs:
```bash
pip install mkdocs-material
mkdocs serve                     # http://127.0.0.1:8000
```

## Project layout

```
msb_rename_utility/
├── app.py                # Flask: / , /api/preview , /api/apply (stub)
├── ops/                  # one pure function per op
│   ├── __init__.py       # REGISTRY + run_pipeline()
│   ├── case.py
│   ├── replace.py
│   ├── regex.py
│   ├── insert.py
│   └── numbering.py
├── templates/index.html  # single page UI shell
├── static/
│   ├── app.js            # vanilla JS — pipeline builder + preview
│   └── style.css         # Tokyo Night, shared palette with disk-dashboard
├── docs/                 # MkDocs Material site
│   ├── index.md
│   ├── getting-started.md
│   ├── concepts/pipeline.md
│   └── ops/case.md       # exemplar page — all other op pages follow this shape
├── mkdocs.yml
└── requirements.txt
```

## Next steps (roadmap)

1. Wire `/api/apply` with a real undo-log (JSON sidecar).
2. Fill in remaining easy ops: pad/trim, remove-at-position, extension swap,
   date-from-mtime, collision auto-append `" (2)"`.
3. Metadata ops: EXIF (Pillow), MP3/FLAC (mutagen), video (ffprobe).
4. Port `docs/ops/case.md` template to the other 4 scaffolded ops.
5. "Try this rule" deep-links: encode pipeline JSON in the URL query string so
   docs pages can prefill the UI with a working example.

## License

MIT — the engine is a clean-room reimplementation, not a port, so no GPL
inheritance from Métamorphose 2.
