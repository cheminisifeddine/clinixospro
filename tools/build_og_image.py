#!/usr/bin/env python3
"""Build the 1200x630 link-preview card for clinixospro.com.

WHY: the previous og:image was a 1341x336 PNG wordmark banner. Facebook,
WhatsApp and Telegram previews are 1200x630 (1.91:1); a 3.99:1 banner is
either letterboxed into a strip or cropped down to the mark, so the preview
said almost nothing.

DESIGN CONSTRAINT: no invented branding. Everything in the card is either
(a) the real ClinixOS Pro mark, (b) a real product screenshot already in
img/, or (c) the site's own Tailwind palette (slate-900 #0F172A, blue-700
#1D4ED8, slate-600 #475569, slate-200 #E2E8F0). The type is Inter, the face
the site itself now self-hosts in fonts/.

Reads its two font binaries from fonts/*.woff2 and converts them in memory;
no build step, no new dependency beyond Pillow + fontTools.

    python3 tools/build_og_image.py            # write img/og-1200x630.jpg
    python3 tools/build_og_image.py --check    # verify, don't write
"""
import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
MARK = ROOT / "img" / "logo.png"          # the real wordmark, 1341x336
SHOT = ROOT / "img" / "dashboard-1600.jpg"  # a real capture from the product
REG = ROOT / "fonts" / "inter-latin.woff2"
BOLD = REG  # one variable file covers weights 100-900

W, H = 1200, 630

# Site palette, lifted from styles.css (Tailwind 3.4.19 default scale).
INK = (15, 23, 42)        # slate-900
BLUE = (29, 78, 216)      # blue-700
SLATE = (71, 85, 105)     # slate-600
LINE = (226, 232, 240)    # slate-200

PAD = 72


def face(woff2: Path, size: int) -> ImageFont.FreeTypeFont:
    """woff2 -> ttf in memory, because Pillow cannot read woff2.

    Fonts are read from Inter, the face the site actually ships in
    fonts/. (The vendored fonts/atkinson-*.woff2 subsets are NOT usable: both
    of their cmap subtables omit 0x41 and every other ASCII codepoint, mapping
    them +0x100 into the PUA instead, so the browser silently substitutes a
    fallback face. See the note in tools/fetch_inter.py.)
    """
    from fontTools.ttLib import TTFont

    f = TTFont(str(woff2))
    f.flavor = None
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, do not write")
    ap.add_argument("--out", default=str(ROOT / "img" / "og-1200x630.jpg"))
    args = ap.parse_args()

    out = Path(args.out)
    if args.check:
        if not out.exists():
            print(f"FAIL {out.name} does not exist")
            return 1
        with Image.open(out) as im:
            got = im.size
        ok = got == (W, H)
        print(f"{'PASS' if ok else 'FAIL'} og image is {got[0]}x{got[1]} (want {W}x{H})")
        return 0 if ok else 1

    # ---- canvas: dark slate, matching the site's ink colour -------------
    card = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(card)

    # Product shot, TOP-RIGHT. Everything else lives in a left column that is
    # measured against the space the shot leaves, so copy can never run under
    # it. (The first version of this card did exactly that.)
    shot = Image.open(SHOT).convert("RGB")
    sw, sh = 452, 254
    shot = shot.resize((sw, sh), Image.Resampling.LANCZOS)
    sx, sy = W - PAD - sw, PAD + 4

    frame = Image.new("RGB", (sw + 8, sh + 8), (30, 41, 59))  # slate-800 edge
    card.paste(frame, (sx - 8, sy - 8))
    card.paste(shot, (sx, sy))
    # Hairline in slate-200, same weight as the site's 1px borders.
    d.rectangle([sx, sy, W - PAD - 1, sy + sh], outline=LINE, width=1)

    # ---- the real wordmark, top-left -----------------------------------
    mark = Image.open(MARK).convert("RGBA")
    mw = 288
    mark = mark.resize((mw, round(mark.height * mw / mark.width)), Image.Resampling.LANCZOS)
    card.paste(mark, (PAD, PAD), mark)

    # ---- copy ----------------------------------------------------------
    h1 = face(BOLD, 58)
    h2 = face(REG, 27)
    tag = face(BOLD, 20)

    # The copy column stops 40px short of the screenshot.
    col_w = sx - 40 - PAD

    def fits(lines_, f):
        return all(d.textlength(t, font=f) <= col_w for t in lines_)

    headline = ["Logiciel de gestion", "de cabinet médical", "algérien"]
    # Shrink the headline until every line fits the column.
    while h1.size > 30 and not fits(headline, h1):
        h1 = face(BOLD, h1.size - 2)

    x = PAD
    y = PAD + mark.height + 30

    # Blue accent bar, the same 1D4ED8 used for every CTA on the site.
    d.rectangle([x, y, x + 58, y + 6], fill=BLUE)
    y += 24

    for line in headline:
        d.text((x, y), line, font=h1, fill=(255, 255, 255))
        y += round(h1.size * 1.14)
    y += 16

    d.text((x, y), "Logiciel de gestion de cabinet médical Algérie",
           font=h2, fill=LINE)
    y += 48

    # Facts already stated on the page. No new claims. They wrap onto as many
    # rows as the column actually needs, rather than being allowed to overrun.
    badge_w = d.textlength("9 900 DA", font=tag) + 36
    d.rounded_rectangle([x, y, x + badge_w, y + 40], 6, fill=BLUE)
    d.text((x + 18, y + 10), "9 900 DA", font=tag, fill=(255, 255, 255))

    cx, cy, rows = x + badge_w + 22, y + 10, 1
    for label in ["Licence à vie", "100 % hors-ligne", "Paiement à la livraison"]:
        w = d.textlength(label, font=h2)
        if cx > x and cx + w > x + col_w:          # wrap to a new row
            cx, cy, rows = x, cy + 36, rows + 1
        d.text((cx, cy), label, font=h2, fill=LINE)
        cx += w + 22

    # Every drawn element must sit inside the card with a real margin. A size
    # assertion alone would have passed the first, broken version of this card.
    if y + 40 + (rows - 1) * 36 > H - PAD:
        raise RuntimeError(
            f"fact block overruns the card bottom: "
            f"{y + 40 + (rows - 1) * 36}px used of {H - PAD}px")
    for line in headline:
        if x + d.textlength(line, font=h1) > W - PAD:
            raise RuntimeError(f"headline line overruns the card: {line!r}")

    card.save(out, "JPEG", quality=88, optimize=True, progressive=True)
    with Image.open(out) as im:
        print(f"wrote {out} {im.size[0]}x{im.size[1]} {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
