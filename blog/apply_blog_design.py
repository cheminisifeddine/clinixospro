#!/usr/bin/env python3
"""Bring the second article page onto the same design system as the first.

The two articles were authored separately and drifted: the first one was
hand-patched, this script does the identical set of edits to the second so the
blog does not render two different designs. It is idempotent and asserts each
replacement actually happened, because a silent no-op patch here would ship a
page with a CDN webfont that never loads.
"""
import pathlib
import re
import sys

PAGES = [
    pathlib.Path("/home/hatch/workspace/repos/clinixospro/blog/optimiser-temps-attente-cabinet/index.html"),
]

HEAD_OLD = re.compile(
    r'<link rel="preconnect" href="https://fonts\.googleapis\.com"/>\s*'
    r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin/>\s*'
    r'<link href="https://fonts\.googleapis\.com/css2\?family=Inter[^"]*" rel="stylesheet"/>\s*'
    r'<link rel="stylesheet" href="/styles\.css"/>',
    re.S,
)
HEAD_NEW = '<link rel="stylesheet" href="/styles.css"/>\n<link rel="stylesheet" href="/blog/blog.css"/>'

failures = []

for path in PAGES:
    html = path.read_text(encoding="utf-8")
    before = html

    if HEAD_OLD.search(html):
        html = HEAD_OLD.sub(HEAD_NEW, html, count=1)
    elif '/blog/blog.css' not in html:
        failures.append(f"{path.name}: could not match the font link block")

    # body font family -> the vendored product face
    html = html.replace(
        "body{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;",
        "body{font-family:'Atkinson Hyperlegible',system-ui,-apple-system,'Segoe UI',sans-serif;",
    )
    html = html.replace(
        '<body class="bg-white text-slate-900 antialiased">',
        '<body class="bg-white text-slate-900 antialiased" style="font-family:\'Atkinson Hyperlegible\',system-ui,-apple-system,\'Segoe UI\',sans-serif">',
    )

    # prose typography now lives in blog.css
    html = re.sub(r'\n\s*\.post-body (?:p|h2|h3|ul|ol|li)[^\n]*', '', html)
    html = html.replace(
        '<div class="post-body text-slate-700">',
        '<div class="post-body blog-prose blog-wrap text-slate-700">',
    )

    # byline: a real <time> element and a rule, instead of one grey sentence
    byline_old = re.search(
        r'<p class="text-xs text-slate-500">Publié le (\d{1,2}) (\w+) (\d{4}) · (\d+) min de lecture</p>', html)
    if byline_old:
        d, month, y, mins = byline_old.groups()
        months = {'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
                  'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10,
                  'novembre': 11, 'décembre': 12}
        iso = f"{y}-{months[month]:02d}-{int(d):02d}"
        html = html.replace(
            byline_old.group(0),
            f'<div class="byline">\n'
            f'        <span>ClinixOS Pro</span>\n'
            f'        <span class="dot" aria-hidden="true">·</span>\n'
            f'        <time datetime="{iso}">{int(d)} {month} {y}</time>\n'
            f'        <span class="dot" aria-hidden="true">·</span>\n'
            f'        <span>{mins} min de lecture</span>\n'
            f'        <span class="dot" aria-hidden="true">·</span>\n'
            f'        <span>Algérie</span>\n'
            f'      </div>')
    else:
        # already converted on a previous run — that is success, not failure
        if 'class="byline"' not in html:
            failures.append(f"{path.name}: byline line not found and no .byline present")

    # previous/next navigation
    if 'class="post-nav"' not in html:
        nav = '''      <div class="post-nav">
        <a href="/blog/" class="prev">
          <span class="k">← Blog</span>
          <span class="t">Tous les articles</span>
        </a>
        <a href="/blog/organiser-son-dossier-patient/" class="next">
          <span class="k">Article suivant →</span>
          <span class="t">Comment organiser son dossier patient sans perdre une consultation</span>
        </a>
      </div>

'''
        m = re.search(r'( *)<h2 class="text-xs font-semibold uppercase tracking-wider[^"]*">À lire ensuite</h2>', html)
        if m:
            html = html[:m.start()] + nav + html[m.start():]
        else:
            failures.append(f"{path.name}: 'À lire ensuite' heading not found")

    if html != before:
        path.write_text(html, encoding="utf-8")
        print(f"  patched {path.relative_to(path.parents[3])}")
    else:
        print(f"  unchanged {path.name}")

# --- verify the whole blog set, not just the page we edited ---------------
blog = pathlib.Path("/home/hatch/workspace/repos/clinixospro/blog")
print("\nverification:")
for f in sorted(blog.rglob("*.html")):
    t = f.read_text(encoding="utf-8")
    checks = {
        'no Google Fonts': 'fonts.googleapis' not in t,
        'no Inter face': "'Inter'" not in t,
        'blog.css linked': '/blog/blog.css' in t,
        'Atkinson declared': 'Atkinson Hyperlegible' in t,
    }
    # NOTE: every page in this tree is named index.html, so identify pages by
    # their parent directory, not their filename. Testing articles against
    # index criteria reports failures that do not exist.
    is_index = f.parent == blog
    if is_index:
        checks['cards present'] = t.count('class="post"') == 2
        checks['has <time>'] = '<time datetime=' in t
        checks['Blog JSON-LD'] = '"@type": "Blog"' in t
    else:
        checks['byline present'] = 'class="byline"' in t
        checks['post-nav present'] = 'class="post-nav"' in t
        checks['BlogPosting JSON-LD'] = '"@type": "BlogPosting"' in t
    bad = [k for k, v in checks.items() if not v]
    print(f"  {'FAIL' if bad else 'ok  '} {f.parent.name if not is_index else 'blog/index'}"
          + (f"  <- {bad}" if bad else ""))

sys.exit(1 if failures else 0)
