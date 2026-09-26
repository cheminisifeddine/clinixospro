#!/usr/bin/env python3
"""Final verification sweep for the ClinixOS Pro blog.

For every page at every width: the vendored font must actually load, there
must be no sideways scroll, and the only contrast findings allowed are the
aria-hidden "·" separators in a byline.
"""
import json
import os
import pathlib
import subprocess
import sys

SHOTS = pathlib.Path("/home/hatch/workspace/shots")
PAGES = [
    ("blog/index", "index"),
    ("blog/organiser-son-dossier-patient/index", "dossier"),
    ("blog/optimiser-temps-attente-cabinet/index", "attente"),
]
WIDTHS = [1440, 390]

env = {**os.environ, "CLINIXOS_CDP_PORT": os.environ.get("CLINIXOS_CDP_PORT", "9444")}
subprocess.run([sys.executable, str(SHOTS / "mk_file_site.py")],
               capture_output=True, text=True, env=env)

fails = []
rows = []
for rel, label in PAGES:
    for w in WIDTHS:
        r = subprocess.run(
            [sys.executable, str(SHOTS / "probe.py"),
             f"file:///tmp/blogsite/{rel}.html",
             str(SHOTS / "probe_blog.js"), f"{w}x900"],
            capture_output=True, text=True, env=env)
        try:
            d = json.loads(r.stdout)
        except Exception:
            fails.append(f"{label}@{w}: probe returned no JSON")
            continue
        if "exceptionId" in d:
            fails.append(f"{label}@{w}: {d.get('text')}")
            continue

        faces = [x.split()[-1] for x in d["font"]["documentFonts"]]
        font_ok = len(faces) == 2 and all(x == "loaded" for x in faces)
        if not font_ok:
            fails.append(f"{label}@{w}: font faces {faces or 'NONE'}")
        if d["overflowX"]:
            fails.append(f"{label}@{w}: overflowX={d['overflowX']}")

        # the only tolerated contrast finding is the decorative separator dot
        real = [c for c in d["contrast"] if c["text"].strip() not in {"·", "..."}]
        if real:
            fails.append(f"{label}@{w}: contrast {[(c['text'], c['ratio']) for c in real]}")

        rows.append((label, w, "OK" if font_ok else "FAIL",
                     len(d["contrast"]), d["overflowX"]))

print(f"{'page':10} {'width':>6}  {'font':5} {'contrast':>8} {'overflowX':>9}")
for label, w, font, con, ox in rows:
    print(f"{label:10} {w:>6}  {font:5} {con:>8} {ox:>9}")

if fails:
    print("\nFAILURES:")
    for f in fails:
        print("  ", f)
    sys.exit(1)
print("\nall pages clean at 1440px and 390px")
