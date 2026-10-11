"""Resize photos for the web and regenerate the gallery in index.html.

Usage, from the repo root:

    python scripts/build.py            # process new/changed originals, rebuild gallery
    python scripts/build.py --force    # re-resize every original

- Any image in originals/ that isn't in photos.json yet is appended to it, with
  camera, lens and exposure filled in from its EXIF metadata.
- photos.json controls gallery order, alt text and captions. Edit it freely;
  the script never overwrites fields that are already there.
- The markup between the gallery markers in index.html is rewritten from
  photos.json on every run.
"""

import html
import io
import json
import re
import sys
from pathlib import Path

from PIL import ExifTags, Image, ImageCms, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ORIGINALS = ROOT / "originals"
OUT = ROOT / "assets" / "photos"
DATA = ROOT / "photos.json"
INDEX = ROOT / "index.html"

SIZES = (800, 1600, 2400)  # long edge, px
GRID_SIZES = SIZES[:2]  # the 2400 copy is only used in the full-screen viewer
QUALITY = 82
ROW_HEIGHT = 240  # keep in sync with --row-h in assets/css/style.css
EAGER = 4  # first N thumbnails skip lazy-loading
EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
START, END = "<!-- gallery:start -->", "<!-- gallery:end -->"

CAMERA_NAMES = {"ILCE-6000": "Sony α6000"}
SRGB = ImageCms.createProfile("sRGB")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def out_path(pid, size):
    return OUT / f"{pid}-{size}.webp"


def camera_name(make, model):
    if not model:
        return ""
    model = model.strip()
    if model in CAMERA_NAMES:
        return CAMERA_NAMES[model]
    make = (make or "").strip().split(" ")[0].title()
    return model if model.lower().startswith(make.lower()) else f"{make} {model}".strip()


def lens_name(lens):
    if not lens:
        return ""
    lens = lens.strip()
    sigma = re.match(r"(.+?)\s*\|\s*(Art|Contemporary|Sports)\b", lens)
    if sigma:
        return f"Sigma {sigma[1]} {sigma[2]}"
    return re.sub(r"^(EF-S|EF-M|EF|RF)(?=\d)", r"\1 ", lens)


def exif_fields(path):
    with Image.open(path) as im:
        exif = im.getexif()
    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    tags.update({ExifTags.TAGS.get(k, k): v for k, v in exif.get_ifd(ExifTags.IFD.Exif).items()})

    parts = []
    if tags.get("FocalLength"):
        parts.append(f"{float(tags['FocalLength']):g}mm")
    if tags.get("FNumber"):
        parts.append(f"f/{float(tags['FNumber']):g}")
    if tags.get("ExposureTime"):
        t = float(tags["ExposureTime"])
        parts.append(f"1/{round(1 / t)}s" if t < 1 else f"{t:g}s")
    iso = tags.get("ISOSpeedRatings")
    if isinstance(iso, tuple):
        iso = iso[0] if iso else None
    if iso:
        parts.append(f"ISO {iso}")

    return {
        "camera": camera_name(tags.get("Make"), tags.get("Model")),
        "lens": lens_name(tags.get("LensModel")),
        "exposure": " · ".join(parts),
    }


def is_stale(src, pid):
    mtime = src.stat().st_mtime
    return any(not out_path(pid, s).exists() or out_path(pid, s).stat().st_mtime < mtime for s in SIZES)


def resize(src, pid):
    with Image.open(src) as im:
        icc = im.info.get("icc_profile")
        im = ImageOps.exif_transpose(im)
        if icc:
            try:
                im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), SRGB, outputMode="RGB")
            except ImageCms.PyCMSError:
                pass
        im = im.convert("RGB")
        OUT.mkdir(parents=True, exist_ok=True)
        for size in SIZES:
            copy = im.copy()
            copy.thumbnail((size, size), Image.LANCZOS)
            copy.save(out_path(pid, size), "WEBP", quality=QUALITY, method=6)


def srcset(pid, sizes):
    entries = []
    for s in sizes:
        with Image.open(out_path(pid, s)) as im:
            entries.append(f"assets/photos/{pid}-{s}.webp {im.width}w")
    return ", ".join(entries)


def gallery_item(i, photo):
    pid = photo["id"]
    for s in SIZES:
        if not out_path(pid, s).exists():
            sys.exit(f"Missing {out_path(pid, s).relative_to(ROOT)}. Put the original in originals/ and rerun.")
    with Image.open(out_path(pid, SIZES[0])) as im:
        w, h = im.size
    with Image.open(out_path(pid, SIZES[-1])) as im:
        ratio = im.width / im.height
    # Phones show roughly one photo per row; on wider screens rows stretch items
    # a little past their base width, hence the 1.25.
    sizes = f"(max-width: 600px) 100vw, {round(ratio * ROW_HEIGHT * 1.25)}px"
    loading = 'fetchpriority="high"' if i == 0 else ('loading="eager"' if i < EAGER else 'loading="lazy"')
    a = lambda v: html.escape(v or "", quote=True)
    return (
        f'      <a class="gallery-item" href="assets/photos/{pid}-{SIZES[-1]}.webp" style="--r: {ratio:.4f}"'
        f' data-srcset="{srcset(pid, SIZES)}" data-camera="{a(photo.get("camera"))}"'
        f' data-lens="{a(photo.get("lens"))}" data-exposure="{a(photo.get("exposure"))}">\n'
        f'        <img src="assets/photos/{pid}-{SIZES[0]}.webp" srcset="{srcset(pid, GRID_SIZES)}" sizes="{sizes}"'
        f' width="{w}" height="{h}" alt="{a(photo.get("alt"))}" {loading} decoding="async">\n'
        f"      </a>"
    )


def write_gallery(photos):
    page = INDEX.read_text("utf-8")
    if START not in page or END not in page:
        sys.exit(f"index.html is missing the {START} / {END} markers.")
    items = "\n".join(gallery_item(i, p) for i, p in enumerate(photos))
    page = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _: f"{START}\n{items}\n      {END}",
        page,
        flags=re.S,
    )
    INDEX.write_text(page, "utf-8", newline="\n")


def main():
    force = "--force" in sys.argv[1:]
    photos = json.loads(DATA.read_text("utf-8")) if DATA.exists() else []
    known = {p["id"] for p in photos}

    for src in sorted(ORIGINALS.iterdir()) if ORIGINALS.exists() else []:
        if src.suffix.lower() not in EXTS:
            continue
        pid = slug(src.stem)
        if pid not in known:
            photos.append({"id": pid, "alt": "", **exif_fields(src)})
            known.add(pid)
            print(f"added    {pid}")
        if force or is_stale(src, pid):
            resize(src, pid)
            print(f"resized  {pid}")

    DATA.write_text(json.dumps(photos, indent=2, ensure_ascii=False) + "\n", "utf-8", newline="\n")
    write_gallery(photos)

    used = {out_path(p["id"], s).name for p in photos for s in SIZES}
    for orphan in sorted(f.name for f in OUT.glob("*.webp") if f.name not in used):
        print(f"unused   assets/photos/{orphan} (not in photos.json; safe to delete)")
    missing_alt = [p["id"] for p in photos if not p.get("alt")]
    if missing_alt:
        print("no alt text yet: " + ", ".join(missing_alt))
    print(f"gallery: {len(photos)} photos")


if __name__ == "__main__":
    main()
