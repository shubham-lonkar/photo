# Photo Portfolio

Source for [shubham-lonkar.github.io/photo](https://shubham-lonkar.github.io/photo/), migrated from Wix. It's a static site hosted on GitHub Pages: plain HTML, CSS and a little JavaScript, with no framework and no build step on GitHub's side. It shares its look with [shubham-lonkar.github.io](https://shubham-lonkar.github.io/), including the dark/light toggle (the choice carries over between the two sites).

## Repo structure

```
index.html              the whole page; the gallery block between the markers is generated
photos.json             gallery order, alt text and camera captions, one entry per photo
assets/photos/          resized copies of each photo (800, 1600, 2400 px on the long edge, WebP)
assets/css/style.css    colors, layout, gallery and full-screen viewer styles
assets/js/main.js       theme toggle, back-to-top button, full-screen viewer
assets/images/          headshot
scripts/build.py        resizes originals and regenerates the gallery markup
originals/              full-resolution files; git-ignored and never published
```

## Adding photos

Requires Python 3 with Pillow (`pip install pillow`).

1. Drop the full-resolution export into `originals/`.
2. Run `python scripts/build.py` from the repo root. It:
   - makes the three web sizes in `assets/photos/` (rotated upright, converted to sRGB, metadata stripped);
   - appends the photo to `photos.json` with camera, lens and exposure read from its EXIF;
   - rewrites the gallery in `index.html`.
3. Open `photos.json`, write a short `alt` description for the new photo, and move its entry if you want it somewhere other than the end. Rerun the script.
4. Preview with `python -m http.server` and open <http://localhost:8000>, then commit and push.

To remove a photo, delete its entry from `photos.json` and rerun; the script lists the leftover files in `assets/photos/` that are safe to delete. To reorder, move entries in `photos.json` and rerun.

Captions only show what the EXIF contained. Edit `camera`, `lens` or `exposure` in `photos.json` to fix or fill them in; the script never overwrites existing values.

## Deploying

Any push to `main` goes live within a minute or two (Settings → Pages → Deploy from a branch → `main` / root). The `.nojekyll` file tells GitHub Pages to serve the files as they are, without running Jekyll.
