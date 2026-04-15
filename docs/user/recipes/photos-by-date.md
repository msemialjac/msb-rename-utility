# Rename photos by date taken

**You have:** a folder of `IMG_7421.JPG`, `IMG_7422.JPG`, … cluttering up
your photo archive.

**You want:** `2024-04-13_IMG_7421.JPG`, so everything sorts chronologically
and you can find that one picture from the trip.

## Try it

1. Open the app.
2. Paste [**this link**][link] into your address bar and hit enter — the
   pipeline prefills automatically.
3. Click **pick folder…**, choose the folder of photos.
4. Paste the folder's absolute path into the **Directory** field.
5. Click **preview**. You should see each file stamped with its date.
6. If it looks right, click **apply**.

[link]: http://127.0.0.1:5051/#p=eyJwaXBlbGluZSI6W3sib3AiOiJkYXRlX2Zyb21fbXRpbWUiLCJwYXJhbXMiOnsiZm9ybWF0IjoiJVktJW0tJWQiLCJwb3NpdGlvbiI6InByZWZpeCIsInNlcCI6Il8ifX1dLCJmaWxlcyI6IklNR183NDIxLkpQR1xuSU1HXzc0MjIuSlBHXG5JTUdfNzQyMy5KUEcifQ

## What the pipeline does

One step: **date_from_mtime** with format `%Y-%m-%d`, position `prefix`,
separator `_`. The server reads the file's modification time from disk and
sticks the date on the front.

## Common tweaks

- **Want the time too?** Change the format to `%Y-%m-%d_%H%M` — you'll get
  `2024-04-13_1530_IMG_7421.JPG`.
- **Want it as a suffix instead?** Switch `pos` to `suffix` — the date
  goes *before* the extension: `IMG_7421_2024-04-13.JPG`.
- **Photos sorted wrong?** The date comes from the file's *modification*
  time, which some systems reset when you copy files. True EXIF dates
  (from inside the JPEG) are a planned feature — not there yet.
