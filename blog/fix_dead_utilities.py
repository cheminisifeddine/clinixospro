#!/usr/bin/env python3
"""Fix the blog's dead utility classes, proven by the renderer.

styles.css is a PREBUILT Tailwind bundle. It contains only the utilities the
original pages happened to use. A new page that reaches for anything else gets
silently nothing — py-14 applies no padding, mt-8 applies no margin,
hover:underline does not underline, and nothing errors.

Method: probe the rendered page for the computed effect of each suspect class
(0 rules and an initial value == dead), then replace only those. Verified dead
against the renderer, not against a grep of the bundle, because Tailwind
escapes class names (.hover\\:bg-blue-800) and a text search both misses real
rules and invents fake ones.

Run: CLINIXOS_CDP_PORT=9444 python3 fix_dead_utilities.py
"""
import json
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path("/home/hatch/workspace/repos/clinixospro")
BLOG = REPO / "blog"
SHOTS = pathlib.Path("/home/hatch/workspace/shots")

# class -> what it was supposed to do, with the replacement we ship
FIXES = {
    "py-14":  ("section padding",        "blog-pad-y"),
    "py-12":  ("section padding",        "blog-pad-y"),
    "mt-10":  ("hero stat block",        "blog-mt-10"),
    "mt-8":   ("callout/box margin",     "blog-mt-8"),
    "p-5":    ("callout/box padding",    "blog-pad-5"),
    "gap-x-6": ("hero stats column gap",  "blog-gap-x"),
    "gap-y-5": ("hero stats row gap",     "blog-gap-y"),
    "items-baseline": ("section head baseline", "blog-baseline"),
    "md:text-5xl": ("hero h1 at md+",     "blog-h1-lg"),
    "hover:underline": ("inline link underline", "blog-link"),
    "border-white/10": ("hero divider",  "blog-rule"),
    "tabular-nums": ("numeric alignment", "blog-tnum"),
}

# Rebuild the file:// render copy from the CURRENT repo state, or the probe
# measures a stale page and "proves" classes are already dead.
subprocess.run([sys.executable, str(SHOTS / "mk_file_site.py")],
               capture_output=True, text=True, check=True)

print("probing the renderer for classes that are genuinely dead…")
out = subprocess.run(
    [sys.executable, str(SHOTS / "probe.py"),
     "file:///tmp/blogsite/blog/index.html", str(SHOTS / "probe_utilities.js"),
     "1440x1200"],
    capture_output=True, text=True,
    env={**os.environ, "CLINIXOS_CDP_PORT": os.environ.get("CLINIXOS_CDP_PORT", "9444")},
)
try:
    probed = json.loads(out.stdout)
except Exception:
    print("probe failed — cannot prove anything, aborting")
    print(out.stdout[-800:], out.stderr[-400:])
    sys.exit(2)

computed = probed["computed"]
# a class is dead when its computed value is the CSS initial value
INITIAL = {
    "paddingTop": "0px", "marginTop": "0px", "columnGap": "normal",
    "rowGap": "normal", "alignItems": "normal", "fontSize": "16px",
    "textDecorationLine": "none", "fontVariantNumeric": "normal",
}
dead = []
for cls in FIXES:
    prop_hint = {
        "py-14": "paddingTop", "py-12": "paddingTop", "mt-10": "marginTop",
        "mt-8": "marginTop", "p-5": "paddingTop", "gap-x-6": "columnGap",
        "gap-y-5": "rowGap", "items-baseline": "alignItems",
        "md:text-5xl": "fontSize", "hover:underline": "textDecorationLine",
        "border-white/10": "borderTopColor", "tabular-nums": "fontVariantNumeric",
    }[cls]
    val = computed.get(cls, {}).get("applied", "MISSING")
    # md:text-5xl and border-white/10 don't have a reliable "initial"; treat
    # a small font size and the default border colour as dead
    is_dead = (val == INITIAL.get(prop_hint)) if prop_hint in INITIAL else True
    if cls in ("md:text-5xl", "border-white/10") and val not in ("16px", "rgb(229, 231, 235)"):
        is_dead = False
    dead.append((cls, is_dead, val))

print()
for cls, is_dead, val in dead:
    print(f"  {'DEAD' if is_dead else 'live'}  {cls:18} -> {val}")

to_fix = {c for c, d, _ in dead if d}
print(f"\n{len(to_fix)} confirmed dead: {sorted(to_fix)}")
if not to_fix:
    print("nothing to do")
    sys.exit(0)

# ---------------------------------------------------------------- rewrite
changed = 0
for page in sorted(BLOG.rglob("*.html")):
    t = orig = page.read_text(encoding="utf-8")
    for cls in sorted(to_fix, key=len, reverse=True):
        rep = FIXES[cls][1]
        # replace whole tokens, including variant prefixes
        t = re.sub(rf'(?<![\w-]){re.escape(cls)}(?![\w-])', rep, t)
    if t != orig:
        page.write_text(t, encoding="utf-8")
        changed += 1
        print(f"  patched {page.parent.name or 'blog/index'}")

print(f"\n{changed} pages updated")
