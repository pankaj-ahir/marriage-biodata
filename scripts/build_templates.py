#!/usr/bin/env python3
"""
Build category-wise biodata templates from a folder of artwork images.

Usage:
    python3 scripts/build_templates.py "/path/to/Marriage biodata format"

For every image it:
  1. maps the folder to one of the 12 categories (see FOLDER_MAP),
  2. normalises the image to the site's A4 ratio (1000x1414) without squashing corners,
  3. writes  public/templates/art/<id>.webp        (page background, used by the live preview + PDF)
            public/templates/art/thumb/<id>.webp   (gallery thumbnail)
  4. detects the free writing area and the text / heading colours,
  5. writes src/lib/artTemplates.generated.ts  (compact data; layout rules live in templates.ts).

To add more designs later: drop images into the matching category folder and run it again.
"""
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT_ART = ROOT / "public" / "templates" / "art"
OUT_THUMB = OUT_ART / "thumb"
OUT_TS = ROOT / "src" / "lib" / "artTemplates.generated.ts"

PAGE_W, PAGE_H = 1000, 1414
THUMB_W, THUMB_H = 400, 566

# folder name (whitespace trimmed, lower-case) -> category id
FOLDER_MAP = {
    "hindu biodata templates": "hindu",
    "muslim biodata templates": "muslim",
    "sikh biodata templates": "sikh",
    "christian biodata templates": "christian",
    "jain biodata templates": "jain",
    "buddhist biodata templates": "buddhist",
    "parsi biodata templates": "parsi",
    "jewish biodata templates": "jewish",
    "regional biodata templates": "regional",
    "modern biodata templates": "modern",
    "premium & royal biodata templates": "premium",
    "simple & minimal biodata templates": "simple",
    "flowers frame biodata template": "modern",
}
# loose images in the zip root default to "modern"; these file numbers are moved by hand
ROOT_OVERRIDES = {"IMG_1231": "muslim", "IMG_1239": "muslim"}
ROOT_DEFAULT = "modern"

CATEGORY_ORDER = [
    "hindu", "muslim", "sikh", "christian", "jain", "buddhist",
    "parsi", "jewish", "regional", "modern", "premium", "simple",
]
CATEGORY_LABEL = {
    "hindu": "Hindu", "muslim": "Muslim", "sikh": "Sikh", "christian": "Christian",
    "jain": "Jain", "buddhist": "Buddhist", "parsi": "Parsi", "jewish": "Jewish",
    "regional": "Regional", "modern": "Modern", "premium": "Premium & Royal",
    "simple": "Simple & Minimal",
}
# sub-folder inside "modern" that holds the floral frames (kept as a tag)
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# detection sanity limits (% of page) and the fallback writing area
MIN_W, MIN_H = 58.0, 46.0
DEFAULT_BOX = (11.0, 13.0, 89.0, 90.0)
# hand-tuned writing areas survive rebuilds: {"hindu-07": [x0, y0, x1, y1]} (% of page)
OVERRIDES_FILE = ROOT / "scripts" / "template_overrides.json"


# ---------------------------------------------------------------- normalise
def to_a4(im: Image.Image) -> Image.Image:
    """Resize to 1000x1414. If the ratio is far from A4, keep top/bottom bands (corner
    ornaments) untouched and stretch/squash only the middle band."""
    im = ImageOps.exif_transpose(im).convert("RGB")
    w0, h0 = im.size
    s = PAGE_W / w0
    h1 = max(1, round(h0 * s))
    scaled = im.resize((PAGE_W, h1), Image.LANCZOS)
    ratio = h1 / PAGE_W
    if abs(ratio - PAGE_H / PAGE_W) / (PAGE_H / PAGE_W) < 0.06:
        return scaled.resize((PAGE_W, PAGE_H), Image.LANCZOS)
    band = min(380, (h1 - 120) // 2, (PAGE_H - 120) // 2)
    top = scaled.crop((0, 0, PAGE_W, band))
    bot = scaled.crop((0, h1 - band, PAGE_W, h1))
    mid = scaled.crop((0, band, PAGE_W, h1 - band)).resize((PAGE_W, PAGE_H - 2 * band), Image.LANCZOS)
    out = Image.new("RGB", (PAGE_W, PAGE_H))
    out.paste(top, (0, 0))
    out.paste(mid, (0, band))
    out.paste(bot, (0, PAGE_H - band))
    return out


# ------------------------------------------------------------------ analyse
def lum(rgb):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def hexc(rgb):
    return "#%02x%02x%02x" % tuple(int(round(max(0, min(255, c)))) for c in rgb)


def fit_contrast(rgb, bg, target):
    """Darken (light bg) or lighten (dark bg) until contrast >= target."""
    c = np.array(rgb, dtype=float)
    dark_bg = lum(bg) < 0.3
    for _ in range(40):
        if contrast(c, bg) >= target:
            break
        c = c * 0.92 if not dark_bg else c + (255 - c) * 0.12
    return c


def analyse(page: Image.Image):
    """Return safe box [x0,y0,x1,y1] in % of page, bg colour, accent colour, is_dark."""
    sw, sh = 250, 354
    small = page.resize((sw, sh), Image.BILINEAR)
    a = np.asarray(small, dtype=np.float32)
    blur = np.asarray(small.filter(ImageFilter.GaussianBlur(9)), dtype=np.float32)
    hp = np.sqrt(((a - blur) ** 2).sum(axis=2))  # sharp features only (lines, ornaments)

    cx0, cx1, cy0, cy1 = int(sw * 0.35), int(sw * 0.65), int(sh * 0.35), int(sh * 0.65)
    centre = a[cy0:cy1, cx0:cx1].reshape(-1, 3)
    med = np.median(centre, axis=0)
    std = float(centre.std(axis=0).mean())
    dist = np.sqrt(((a - med) ** 2).sum(axis=2))
    # patterned / textured pages: raise the "sharp feature" bar so faint damask isn't treated as art
    hp_centre = hp[cy0:cy1, cx0:cx1]
    hp_t = max(16.0, 2.4 * float(np.percentile(hp_centre, 95)))
    art = (hp > hp_t) | (dist > max(80.0, 4.0 * std + 40.0))

    # grow a rectangle from the centre while the new edge strip stays "clean"
    x0, x1, y0, y1 = int(sw * 0.42), int(sw * 0.58), int(sh * 0.42), int(sh * 0.58)
    tol = 0.03
    grew = True
    while grew:
        grew = False
        if x0 > 0 and art[y0:y1, x0 - 1].mean() <= tol:
            x0 -= 1; grew = True
        if x1 < sw and art[y0:y1, x1].mean() <= tol:
            x1 += 1; grew = True
        if y0 > 0 and art[y0 - 1, x0:x1].mean() <= tol:
            y0 -= 1; grew = True
        if y1 < sh and art[y1, x0:x1].mean() <= tol:
            y1 += 1; grew = True

    box = [x0 / sw * 100 + 0.4, y0 / sh * 100 + 0.3, x1 / sw * 100 - 0.4, y1 / sh * 100 - 0.3]
    # keep a printable margin even on borderless artwork
    box = [max(box[0], 7.0), max(box[1], 6.0), min(box[2], 93.0), min(box[3], 94.0)]
    fallback = False
    if (box[2] - box[0]) < MIN_W or (box[3] - box[1]) < MIN_H:
        box = list(DEFAULT_BOX)  # busy / full-scene artwork: detection unreliable -> safe default
        fallback = True

    inner = a[y0:y1, x0:x1].reshape(-1, 3)
    bg = np.median(inner, axis=0)
    dark = lum(bg) < 0.28

    # accent = most saturated, reasonably common colour outside the safe box
    mask = np.ones((sh, sw), bool)
    mask[y0:y1, x0:x1] = False
    outer = a[mask & art]
    if len(outer) < 30:
        outer = a[mask]
    mx, mn = outer.max(axis=1), outer.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    val = mx / 255.0
    good = (sat > 0.28) & (val > 0.2)
    pool = outer[good] if good.sum() > 25 else outer
    if len(pool) > 25 and good.sum() > 25:
        s2 = sat[good]
        pool = pool[s2 >= np.percentile(s2, 55)]
    accent = np.median(pool, axis=0) if len(pool) else np.array([120.0, 90.0, 40.0])
    return box, bg, accent, dark, fallback


def style_for(bg, accent, dark):
    if dark:
        text = np.array([245, 239, 230.0])
        head = fit_contrast(accent, bg, 4.5)
        if lum(head) < 0.45:  # keep headings clearly lighter than the page
            head = head + (255 - head) * 0.35
    else:
        text = np.array([31, 31, 31.0])
        head = fit_contrast(accent, bg, 4.5)
    photo = fit_contrast(accent, bg, 3.0)
    return text, head, photo


# --------------------------------------------------------------------- main
def collect(src: Path):
    items = []  # (category, path)
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMG_EXT or p.name.startswith("."):
            continue
        rel = p.relative_to(src)
        if len(rel.parts) == 1:
            cat = ROOT_OVERRIDES.get(p.stem.upper(), ROOT_DEFAULT)
        else:
            key = re.sub(r"\s+", " ", rel.parts[0].strip().lower())
            cat = FOLDER_MAP.get(key)
            if cat is None:
                print(f"  ! unknown folder {rel.parts[0]!r} -> skipped")
                continue
        items.append((cat, p))
    return items


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    OUT_THUMB.mkdir(parents=True, exist_ok=True)
    for f in list(OUT_ART.glob("*.webp")) + list(OUT_THUMB.glob("*.webp")):
        f.unlink()  # rebuild cleanly so ids always match the data file

    items = collect(src)
    by_cat = {c: [] for c in CATEGORY_ORDER}
    for cat, p in items:
        by_cat[cat].append(p)

    overrides = json.loads(OVERRIDES_FILE.read_text()) if OVERRIDES_FILE.exists() else {}
    fallbacks = []
    rows = []
    for cat in CATEGORY_ORDER:
        files = by_cat[cat]
        pad = max(2, len(str(len(files))))
        for i, p in enumerate(files, 1):
            tid = f"{cat}-{i:0{pad}d}"
            page = to_a4(Image.open(p))
            page.save(OUT_ART / f"{tid}.webp", "WEBP", quality=80, method=5)
            page.resize((THUMB_W, THUMB_H), Image.LANCZOS).save(OUT_THUMB / f"{tid}.webp", "WEBP", quality=72, method=5)
            box, bg, accent, dark, fb = analyse(page)
            if tid in overrides:
                box, fb = overrides[tid], False
            if fb:
                fallbacks.append(tid)
            text, head, photo = style_for(bg, accent, dark)
            rows.append([
                tid, cat,
                round(box[0], 1), round(box[1], 1), round(box[2], 1), round(box[3], 1),
                hexc(text), hexc(head), hexc(photo), 1 if dark else 0, hexc(bg),
            ])
        print(f"{CATEGORY_LABEL[cat]:<20} {len(files):>4}")

    body = ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in rows)
    OUT_TS.write_text(
        "// AUTO-GENERATED by scripts/build_templates.py - do not edit by hand.\n"
        "// [id, category, safeX0%, safeY0%, safeX1%, safeY1%, textColor, headingColor, photoBorder, isDark, pageColor]\n"
        "export type GeneratedRow = [string, string, number, number, number, number, string, string, string, 0 | 1, string];\n\n"
        f"export const GENERATED_ROWS: GeneratedRow[] = [\n{body},\n];\n",
        encoding="utf-8",
    )
    if fallbacks:
        print(f"\n{len(fallbacks)} designs used the default writing area (busy artwork) - review: {', '.join(fallbacks)}")
    print(f"\n{len(rows)} templates written -> {OUT_TS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
