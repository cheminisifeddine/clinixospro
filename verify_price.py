#!/usr/bin/env python3
"""verify_price.py — ClinixOS 9,900 DA revert guard (2026-11-04).

Scans the landing pages for any leak of the OLD price
(19900 / 19 900 / 19,900 — i.e. the Oct 23 cutover price)
and confirms the NEW price (9900 / 9 900 / 9,900) is present in each.

Exit 1 on any old-price leak or missing new price; exit 0 when clean.

Scope note (2026-11-04): only the public landing HTML is guarded.
Operational files (order watcher, handbook) legitimately keep 19900
references for in-flight orders quoted at that price, so they are NOT
in FILES — do not add them back without accounting for that.

Usage: python3 verify_price.py [--self-test]
"""
import os
import re
import sys

WS = "/home/hatch/workspace"
REPO = WS + "/repos/clinixospro"
# Core money files: old price forbidden AND new price must be present.
FILES = [
    REPO + "/index.html",
    REPO + "/merci.html",
]
# Every other HTML page in the repo: old price forbidden (new-price
# presence not required — e.g. dental pages price at 19 000 by design).
SKIP_HTML = {"index-19900.html"}  # untracked scratch, never deployed

# Old price: 19900, or 19 900 / 19,900 (space or comma separator).
OLD = re.compile(r"19900|19[ ,]900")
# New price: "9900" not preceded by 1 (else it's 19900), or "9 900"/"9,900"
# not preceded by 1 (else it's 19 900 / 19,900).
NEW = re.compile(r"(?<!1)9900|(?<!1)9[ ,]900")


def scan_text(text):
    """Returns (old_hits, has_new).

    HTML entities and raw non-breaking spaces are normalized first: on
    2026-10-23 the merci page hid the old price as "9&nbsp;900"
    (rendered 9 900) and the raw-text scan missed it. Normalizing
    &nbsp; / &#160; / &#xA0; / raw U+00A0 to a space closes that hole
    for every file type scanned here.
    """
    norm = (text.replace("&nbsp;", " ").replace("&#160;", " ")
                .replace("&#xA0;", " ").replace("&#xa0;", " ")
                .replace(chr(160), " "))
    return OLD.findall(norm), bool(NEW.search(norm))


def scan_file(path):
    with open(path, encoding="utf-8") as f:
        return scan_text(f.read())


def main():
    if "--self-test" in sys.argv:
        hits, _ = scan_text("dummy copy: Prix : 19900 DA, soit 19 900 DA")
        if hits:
            print(f"SELF-TEST OK: dummy caught ({len(hits)} old-price hits) -> would exit 1")
            return 0
        print("SELF-TEST FAILED: dummy 19900 NOT caught — the checker is broken")
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
            print(f"FAIL {name}: new price 9900 not found")
        else:
            print(f"OK   {name}: no old price, 9900 present")
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
    print("RESULT:", "FAIL" if failed else "PASS — zero 19900 leaks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
