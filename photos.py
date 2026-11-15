"""Dev-only: turn originals in photos/<album>/ into stripped WebP files for the site.

    pip install -r requirements-dev.txt
    python photos.py

Writes static/photos/<stem>-800.webp and -1600.webp (EXIF removed, rotated upright,
never upscaled) and appends new files to data/photos.json. Existing alt/caption are kept.
Originals in photos/ are git-ignored.
"""
import json
import os
import sys

from PIL import Image, ImageOps

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "photos")
OUT = os.path.join(BASE, "static", "photos")
INDEX = os.path.join(BASE, "data", "photos.json")
WIDTHS = (800, 1600)
EXTS = {".jpg", ".jpeg", ".png"}

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    EXTS.add(".heic")
except ImportError:
    pass


def resized(img, width):
    if img.width <= width:
        return img.copy()
    return img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)


def convert(path, stem):
    """Write both sizes; return (width, height) of the 800 version."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        size = None
        for w in WIDTHS:
            out = resized(im, w)
            # a fresh image has no EXIF; save without passing exif or icc profile
            out.save(os.path.join(OUT, f"{stem}-{w}.webp"), "WEBP", quality=80, method=6)
            if w == WIDTHS[0]:
                size = out.size
    return size


def main():
    if not os.path.isdir(SRC):
        sys.exit("No photos/ folder. Put originals in photos/<album>/.")
    os.makedirs(OUT, exist_ok=True)
    with open(INDEX, encoding="UTF-8") as f:
        entries = json.load(f)
    known = {e["file"] for e in entries}
    skipped_heic = False
    added = 0
    for album in sorted(os.listdir(SRC)):
        folder = os.path.join(SRC, album)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            stem, ext = os.path.splitext(name)
            if ext.lower() == ".heic" and ".heic" not in EXTS:
                skipped_heic = True
                print(f"skip {album}/{name}: install pillow-heif for HEIC")
                continue
            if ext.lower() not in EXTS or stem in known:
                continue
            w, h = convert(os.path.join(folder, name), stem)
            entries.append({"file": stem, "album": album, "alt": "", "caption": "", "width": w, "height": h})
            known.add(stem)
            added += 1
            print(f"added {album}/{stem} ({w}x{h})")
    with open(INDEX, "w", encoding="UTF-8") as f:
        json.dump(entries, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"{added} new photo(s); fill in alt text in data/photos.json")
    if skipped_heic:
        print("note: some HEIC files were skipped")


if __name__ == "__main__":
    main()
