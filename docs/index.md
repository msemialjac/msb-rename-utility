# msb_rename_utility

A small Flask + vanilla-JS bulk file renamer, inspired by
[Better Rename Utility (BRU)](https://www.publicspace.net/ABetterRenameUtility/) and
[Métamorphose 2](https://sourceforge.net/projects/file-folder-ren/), **clean-room
reimplemented** — MIT-licensed, no copyleft inheritance, modern Python 3.

## Two docs, pick your starting point

<div class="grid cards" markdown>

-   :material-account: **User Guide**

    ---

    Task-first recipes for people renaming their files. No coding
    required — click a recipe, the web UI prefills, preview what'll happen,
    apply if it looks right.

    [→ Open the User Guide](user/index.md)

-   :material-code-braces: **Developer Reference**

    ---

    Every operation's parameters, the pipeline JSON schema, collision rules,
    undo-log format, `ctx` plumbing. Written for people extending the tool
    or calling the HTTP API directly.

    [→ Open the Developer Reference](dev/getting-started.md)

</div>

## What it does, in one screen

You give it a list of filenames and a **pipeline** — an ordered list of
operations like "lowercase everything, strip the `IMG_` prefix, append a
three-digit sequence number". It shows you a preview of every old → new
rename, flags anything that would collide, and only touches disk when you
hit **apply**. Every apply writes an undo-log sidecar so you can reverse it.

## Sibling project

The visual language (Tokyo Night palette, card layout) mirrors
[`disk-dashboard`](https://github.com/msemialjac/disk-dashboard). The two
apps are meant to feel like a suite of single-purpose Flask tools.
