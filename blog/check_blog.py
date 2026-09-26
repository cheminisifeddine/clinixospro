#!/usr/bin/env python3
r"""Gate for the ClinixOS Pro blog.

Catches the defect class that renders as "looks fine, but nothing happened":
a utility class the prebuilt Tailwind bundle never generated, so the element
receives no padding/grid/typography at all and the section silently collapses.

Why the static scan is not the whole story
-------------------------------------------
styles.css is a PREBUILT, MINIFIED bundle. Two things break naive text search:
  * Tailwind escapes class names — .hover\:bg-blue-800, .h-\[72px\] — so a
    search for ".hover:bg-blue-800" reports a rule that is not there.
  * The file is minified onto few long lines, so a token can sit next to an
    unrelated one in ways a substring search misjudges.
The authoritative test is the RENDERER: apply the class and diff the computed
style. That is probe_deadutil3.js, run by --probe. Note that
document.styleSheets[].cssRules is SecurityError-blocked under file://, so
rule-existence checks inside the page are useless — computed style is the only
trustworthy signal available locally.

Run:  python3 blog/check_blog.py
      CLINIXOS_CDP_PORT=9444 python3 blog/check_blog.py --probe
Exit: 0 clean, 1 with findings.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path("/home/hatch/workspace/repos/clinixospro")
BLOG = REPO / "blog"
BUNDLE = REPO / "styles.css"
SHOTS = pathlib.Path("/home/hatch/workspace/shots")

findings = []


def note(level, page, msg):
    findings.append((level, page, msg))


bundle = BUNDLE.read_text(encoding="utf-8")
blog_css = (BLOG / "blog.css").read_text(encoding="utf-8")
own = set(re.findall(r'\.([a-z0-9_-]+)\s*(?:,|\{)', blog_css))

# page hooks and per-page classes, not bundle utilities
PAGE_HOOKS = {
    "blog", "clinixos", "post", "posts", "byline", "post-nav", "prev", "next",
    "t", "k", "dot", "post-time", "post-title", "post-excerpt", "post-meta",
    "post-eyebrow", "post-body", "callout", "hero", "wrap", "prose",
}


def esc_tw(cls):
    """Escape a class the way Tailwind does — and no more.

    Over-escaping is worse than not escaping: escaping "/" in
    hover:bg-blue-800 turns a LIVE rule into a phantom "dead" finding.
    """
    e = cls
    if ":" in e:
        e = e.replace(":", "\\:")
    if "[" in e or "]" in e:
        e = re.sub(r'([\[\].])', r'\\\1', e)
    return e


# ---------------------------------------------------------------- 1. utilities
for page in sorted(BLOG.rglob("*.html")):
    rel = page.parent.name if page.parent != BLOG else "blog/index"
    html = page.read_text(encoding="utf-8")
    # a page's own <style> block counts as a definition source
    inline_classes = set(re.findall(r'\.([a-z0-9_-]+)\s*[,{]', " ".join(
        re.findall(r'<style[^>]*>([\s\S]*?)</style>', html))))

    for m in re.finditer(r'class="([^"]+)"', html):
        for tok in m.group(1).split():
            if tok in PAGE_HOOKS or tok in own or tok in inline_classes:
                continue
            if not re.match(r'^[a-z0-9]', tok):
                continue
            base = tok.split(":")[-1]
            if base in own or base in inline_classes or base in PAGE_HOOKS or not base:
                continue
            if base.startswith("blog-"):
                continue
            # :hover / :focus cannot be judged statically. A missing hover
            # style is cosmetic; a missing box utility is a broken layout.
            if "hover" in base or "focus" in base:
                continue
            if f".{base}" in bundle or f".{esc_tw(base)}" in bundle:
                continue
            # Static scan only. On a MINIFIED bundle this both misses live
            # rules and invents dead ones; --probe is the authority.
            note("warn", rel, f"utility '{tok}' not found by static scan — verify with --probe")

# ---------------------------------------------------------------- 2. fonts
for page in sorted(BLOG.rglob("*.html")):
    rel = page.parent.name if page.parent != BLOG else "blog/index"
    html = page.read_text(encoding="utf-8")
    if "fonts.googleapis" in html or "fonts.gstatic" in html:
        note("err", rel, "loads a Google Fonts CDN stylesheet — silent offline fallback")
    if "'Inter'" in html:
        note("err", rel, "declares the Inter face, which is not vendored")
    if "Atkinson Hyperlegible" not in html:
        note("err", rel, "never declares the vendored product face")

# the @font-face src must point at a file that exists
for m in re.finditer(r'url\((?:"|\')?([^"\')]+)', blog_css):
    src = m.group(1)
    if src.startswith(("http", "//", "data:")):
        continue
    p = (REPO / src.lstrip("/")) if src.startswith("/") else (BLOG / src)
    if not p.exists():
        note("err", "blog/blog.css", f"@font-face/asset src does not exist: {src}")

# ---------------------------------------------------------------- 3. structure
idx = (BLOG / "index.html").read_text(encoding="utf-8")
n_cards = idx.count('class="post"')
if n_cards != 2:
    note("err", "blog/index", f"expected 2 article cards, found {n_cards}")
if idx.count('<time datetime=') < n_cards:
    note("err", "blog/index", "article cards lack machine-readable <time datetime>")
if '"@type": "Blog"' not in idx:
    note("err", "blog/index", "missing Blog JSON-LD")

for art in sorted(BLOG.glob("*/index.html")):
    t = art.read_text(encoding="utf-8")
    for need, label in [('class="byline"', "byline"),
                        ('class="post-nav"', "post/next navigation"),
                        ('"@type": "BlogPosting"', "BlogPosting JSON-LD"),
                        ('<time datetime=', "machine-readable date")]:
        if need not in t:
            note("err", art.parent.name, f"missing {label}")

for page in sorted(BLOG.rglob("*.html")):
    rel = page.parent.name if page.parent != BLOG else "blog/index"
    n = page.read_text(encoding="utf-8").count('/blog/blog.css')
    if n != 1:
        note("err", rel, f"blog.css linked {n}x, expected exactly 1")

# ---------------------------------------------------------------- 4. NBSP hygiene
# A non-breaking space in meta/JSON-LD breaks parsing; visible button labels are fine.
for page in sorted(BLOG.rglob("*.html")):
    rel = page.parent.name if page.parent != BLOG else "blog/index"
    t = page.read_text(encoding="utf-8")
    # NBSP inside a JSON-LD string is just French typography and parses fine.
    # What breaks is NBSP inside a <meta content="..."> attribute, which some
    # crawlers split on. Check attributes, not element text.
    for m in re.finditer(r'<meta\b[^>]*>', t):
        if "\u00a0" in m.group(0) or "\u202f" in m.group(0):
            note("err", rel, "NBSP/narrow-NBSP inside a <meta> tag — breaks meta parsing")
    # and a raw NBSP inside an inline <script> that is NOT type=ld+json
    for m in re.finditer(r'<script(?![^>]*ld\+json)(?![^>]*src=)[^>]*>([\s\S]*?)</script>', t):
        if "\u00a0" in m.group(1) or "\u202f" in m.group(1):
            note("warn", rel, "NBSP in a non-JSON-LD <script> — check it is intended")

# ---------------------------------------------------------------- 5. renderer proof
if "--probe" in sys.argv:
    env = {**os.environ, "CLINIXOS_CDP_PORT": os.environ.get("CLINIXOS_CDP_PORT", "9444")}
    subprocess.run([sys.executable, str(SHOTS / "mk_file_site.py")],
                   capture_output=True, text=True, env=env)
    breakpoints = {"sm", "md", "lg", "xl"}
    n_verified = 0
    verified = 0
    for width in (1440, 390):
        r = subprocess.run(
            [sys.executable, str(SHOTS / "probe.py"),
             "file:///tmp/blogsite/blog/index.html",
             str(SHOTS / "probe_deadutil3.js"), f"{width}x900"],
            capture_output=True, text=True, env=env)
        try:
            res = json.loads(r.stdout)
        except Exception:
            note("err", "probe", f"renderer proof failed at {width}px — cannot verify")
            continue
        if "exceptionId" in res:
            note("err", "probe", f"renderer probe threw at {width}px: {res.get('text')}")
            continue
        for cls in (k for k in res if k.startswith("blog-")):
            if not res[cls]["applies"]:
                note("err", "blog/blog.css",
                     f"'{cls}' does not apply at {width}px — the replacement is broken")
        dead = [k for k, v in res.items()
                if not v["applies"] and not k.startswith("blog-")
                and "hover" not in k and "focus" not in k]
        # a responsive class legitimately does nothing below its breakpoint
        dead = [d for d in dead
                if not (d.split(":")[0] in breakpoints and width < 1024)]
        # post-body / callout are defined in the ARTICLE pages' own <style>
        # blocks. The index has neither, so their absence here proves nothing.
        ARTICLE_ONLY = {"post-body", "callout", "leading-[1.15]", "sm:flex-row",
                        "mt-8", "p-5"}
        real = [d for d in dead if d not in ARTICLE_ONLY]
        for d in real:
            note("err", f"@{width}px",
                 f"utility '{d}' has no computed effect and its breakpoint is "
                 f"active at {width}px — silent no-op")
        verified = len(dead) - len(real)
        n_verified += sum(1 for k, v in res.items() if v["applies"])

# ---------------------------------------------------------------- report
errs = [f for f in findings if f[0] == "err"]
warns = [f for f in findings if f[0] == "warn"]
for lvl, page, msg in findings:
    print(f"  {lvl.upper():4} {page}: {msg}")
if "--probe" in sys.argv:
    print(f"  renderer: {n_verified} utilities proved live across 1440px + 390px; "
          f"{verified} confirmed dead here are article-page-only")
print(f"\n{len(errs)} errors, {len(warns)} warnings")
sys.exit(1 if errs else 0)
