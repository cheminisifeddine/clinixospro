#!/usr/bin/env python3
"""verify_price.py — ClinixOS 19,900 DA cutover guard (2026-10-23).

Scans the 4 price-bearing files for any leak of the OLD price
(9900 / 9 900 / 9,900 as a standalone price — i.e. not the tail of 19900)
and confirms the NEW price (19900 / 19 900 / 19,900) is present in each.

Exit 1 on any old-price leak or missing new price; exit 0 when clean.

Usage: python3 verify_price.py [--self-test]
"""
import os
import re
import sys

WS = "/home/hatch/workspace"
GOAL = WS + "/goals/clinixos-500-000-dzd-month-revenue/hidden_files"
REPO = WS + "/repos/clinixospro"
# Core money files: old price forbidden AND new price must be present.
FILES = [
    REPO + "/index.html",
    REPO + "/merci.html",
    GOAL + "/order-confirmation/watch_orders.py",
    GOAL + "/clinixos-handbook.md",
]
# Every other HTML page in the repo: old price forbidden (new-price
# presence not required — e.g. dental pages price at 19 000 by design).
# Added 2026-10-23 late: the old price also lived on home.html (a stale
# duplicate landing with its own form + pixel), the blog, the affiliation
# page, the hors-ligne landing and 404.html — the 4-file guard missed them.
SKIP_HTML = {"index-19900.html"}  # untracked scratch, never deployed

# Old price: "9900" not preceded by 1 (else it's 19900), or "9 900"/"9,900"
# not preceded by 1 (else it's 19 900 / 19,900).
OLD = re.compile(r"(?<!1)9900|(?<!1)9[ ]900|(?<!1)9,900")
# New price marker: any of 19900 / 19 900 / 19,900 / 19 900 (nbsp).
NEW = re.compile(r"19[ , ]?900")


def scan_text(text):
    """Returns (old_hits, has_new).

    HTML entities are normalized first: on 2026-10-23 the merci page hid
    the old price as "9&nbsp;900" (rendered 9 900) and the raw-text scan
    missed it. Normalizing &nbsp; / &#160; / &#xA0; to a space closes
    that hole for every file type scanned here.
    """
    norm = (text.replace("&nbsp;", " ").replace("&#160;", " ")
                .replace("&#xA0;", " ").replace("&#xa0;", " "))
    return OLD.findall(norm), bool(NEW.search(norm))


def scan_file(path):
    with open(path, encoding="utf-8") as f:
        return scan_text(f.read())


def main():
    if "--self-test" in sys.argv:
        hits, _ = scan_text("dummy copy: Prix : 9900 DA, soit 9 900 DA")
        if hits:
            print(f"SELF-TEST OK: dummy caught ({len(hits)} old-price hits) -> would exit 1")
            return 0
        print("SELF-TEST FAILED: dummy 9900 NOT caught — the checker is broken")
        return 2

    failed = False
    for path in FILES:
        hits, has_new = scan_file(path)
        name = path.replace(WS + "/", "")
        if hits:
            failed = True
            print(f"FAIL {name}: {len(hits)} old-price leak(s): {hits[:5]}")
        elif not has_new:
            failed = True
            print(f"FAIL {name}: new price 19900 not found")
        else:
            print(f"OK   {name}: no old price, 19900 present")
    extra = 0
    for root, dirs, names in os.walk(REPO):
        if ".git" in root:
            continue
        for fn in names:
            if not fn.endswith(".html") or fn in SKIP_HTML:
                continue
            path = os.path.join(root, fn)
            if path in FILES:
                continue
            hits, _ = scan_file(path)
            if hits:
                failed = True
                print(f"FAIL {path.replace(WS + '/', '')}: "
                      f"{len(hits)} old-price leak(s): {hits[:5]}")
            extra += 1
    print(f"(also scanned {extra} additional HTML pages for old-price leaks)")
    print("RESULT:", "FAIL" if failed else "PASS — zero 9900 leaks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
