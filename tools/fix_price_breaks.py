#!/usr/bin/env python3
"""
Make the price unbreakable on narrow screens.

"9 900 DA" is written with ORDINARY spaces, so a 390px phone can wrap between
"9" and "900" — the one number on the page that must never be split
(observed on the real mobile render: "Offre 9" / "900 DA").

Replace with U+00A0 NO-BREAK SPACE in VISIBLE TEXT only. Deliberately NOT in:
  - <meta> description / og: / twitter:  (plain text for crawlers)
  - JSON-LD structured data               (must stay valid JSON)
  - inline JS string literals             (entity would show literally)

Run from the repo root:  python3 tools/fix_price_breaks.py [--check]
"""
import re
import sys

NBSP = " "
PRICE = "9 900 DA"
PATH = "index.html"

# Regions that must NEVER be rewritten, even though they contain visible-looking
# prices: JSON-LD structured data, inline JS, and <meta> tags. A no-break space
# inside JSON-LD is a real SEO regression — search engines match the plain form.
# The FAQ answers live in a JSON-LD block, so a naive "skip <script>" rule that
# only looked at tag NAMES is not enough; the whole <script> body is excluded.
GUARD = re.compile(r"(<script\b.*?</script>)|(<meta\b[^>]*>)", re.S | re.I)


def is_visible_segment(seg):
    """A segment is rewritable only if it is ordinary page markup.

    BOTH guards must be rejected here, not just <meta>: a <script> segment
    holds the FAQPage JSON-LD, and a no-break space there is a real SEO
    regression (search engines match the plain form). Checking only <meta>
    silently corrupts the structured data.
    """
    if not seg:
        return False
    head = seg.lstrip()[:8].lower()
    if head.startswith("<meta") or head.startswith("<script"):
        return False
    return PRICE in seg


def main():
    check_only = "--check" in sys.argv
    src = open(PATH, encoding="utf-8").read()

    # Split so script/meta regions are isolated and never rewritten.
    # re.split with capturing groups yields None for the non-participating
    # slots, so normalise before inspecting segments.
    parts = [p if p is not None else "" for p in GUARD.split(src)]
    changed = 0
    for i, seg in enumerate(parts):
        if not is_visible_segment(seg):
            continue
        n = seg.count(PRICE)
        if n:
            changed += n
            parts[i] = seg.replace(PRICE, f"9{NBSP}900{NBSP}DA")

    out = "".join(parts)

    if check_only:
        # Inspect the file AS IT IS ON DISK, not the rewritten `out`. Measuring
        # `out` makes the tool grade its own repair and always report clean,
        # which silently hides a price that was reverted by someone else.
        disk = src
        # NBSP is U+00A0 and Python's \s MATCHES it, so a \s-based check reports
        # false failures on already-fixed prices. Match the literal U+0020 only.
        spans = [(m.start(), m.end()) for m in
                 re.finditer(r"<script\b.*?</script>", disk, re.S | re.I)]
        spans += [(m.start(), m.end()) for m in
                  re.finditer(r"<meta\b[^>]*>", disk, re.S | re.I)]
        bad = 0
        for m in re.finditer(r"9\x20900\x20DA", disk):
            if any(a <= m.start() < b for a, b in spans):
                continue  # meta or script (JSON-LD / inline JS) — correct to leave
            bad += 1
        # Guard the guard: a no-break space inside JSON-LD is corruption —
        # search engines match the plain form. A no-break space in INLINE JS is
        # fine and often correct: that string becomes a visible button label
        # (e.g. the submit button's loading text), and must not split either.
        ld_corrupt = 0
        for m in re.finditer(
                r'(?s)<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                disk, re.I):
            ld_corrupt += m.group(1).count(f"9{NBSP}900{NBSP}DA")
        print(f"visible plain-space prices remaining: {bad}")
        print(f"no-break prices inside JSON-LD (must be 0): {ld_corrupt}")
        return 1 if (bad or ld_corrupt) else 0

    if out == src:
        print("no change needed")
        return 0
    open(PATH, "w", encoding="utf-8").write(out)
    print(f"made {changed} visible price(s) non-breaking")
    return 0


if __name__ == "__main__":
    sys.exit(main())
