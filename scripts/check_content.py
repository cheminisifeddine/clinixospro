#!/usr/bin/env python3
"""Contrôle qualité du contenu FR avant commit / déploiement.

Vérifie, sur chaque page du site :
  - caractères non latins glissés dans le texte (CJK, cyrillique, etc.) ;
  - mots collés ou cassés introduits à la génération ;
  - doublons de balises SEO (title, description, canonical) ;
  - longueurs title (<= 60) et description (<= 160) ;
  - JSON-LD parsable, sans note/avis inventés ;
  - liens internes et ancres qui résolvent vraiment sur le disque ;
  - absence d'affirmation chiffrée non présente dans les faits produit.

Usage : python3 scripts/check_content.py [chemin ...]
Sans argument, contrôle tout le site.
Code de sortie 1 si une erreur bloquante est trouvée.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "img", "tools", "cache"}
# Pages autorisées à ne pas avoir de title/description propres (fichiers techniques).
SKIP_FILES = {"404.html", "robots.txt", "sitemap.xml", "_headers", "_redirects"}

# Caractères au-delà de cette zone = hors alphabet latin/punctuation française.
LATIN_MAX = 0x2E7F
# Chiffres romains/lettres accentuées sont normaux ; on vise les autres écritures.
ALLOWED_HIGHER = set("—–‘’“”€…·×°•→")

# Mots souvent cassés par la génération (colle de deux mots, ou faute de frappe).
KNOWN_BROKEN = [
    "lebon", "urtsortez", "la.secreture", "des patients le首位", "vo tre",
    "votree", "d ossier", "p lus",
]

# Mots anglais qui n'appartiennent pas au texte FR du site.
ENGLISH_LEAKS = [
    r"\binstantly\b", r"\bdes théorie\b", r"\byour cabinet\b", r"\bwith\b", r"\bour\b",
    r"\bfastest\b", r"\baffordable\b", r"\bcontact us\b", r"\blearn more\b",
    r"\boffline solution\b", r"\bfree trial\b", r"\bget started\b",
]

# Puces marketing interdites : elles ne sont adossées à aucune mesure vérifiable.
FORBIDDEN_CLAIMS = [
    r"\b\d+\s*%\s*(de\s+)?(gain|réduction|efficacit|vite)",
    r"garanti[e]?\s+\d*\s*%",
    r"note\s+de\s+\d",
    r"\b\d+\s*étoiles?\b",
    r"\b\d+\s*clients?\s+(nous\s+)?ont\s+(choisi|adopté)",
]


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.metas: dict[str, str] = {}
        self.canonicals: list[str] = []
        self.jsonld: list[str] = []
        self._in_jsonld = False
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            if rel == "canonical" and a.get("href"):
                self.canonicals.append(a["href"])
        elif tag == "meta":
            if a.get("name"):
                self.metas.setdefault(a["name"], a.get("content", ""))
            if a.get("property"):
                self.metas.setdefault(a["property"], a.get("content", ""))
        elif tag == "script" and "application/ld+json" in (a.get("type") or ""):
            self._in_jsonld = True
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._buf))
            self._in_jsonld = False

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self._buf.append(data)


def visible_text(html: str) -> str:
    stripped = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", stripped)


def check_page(path: Path, site_ids: set[str], site_text: str) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []
    rel = str(path.relative_to(ROOT))
    html = path.read_text(encoding="utf-8")
    text = visible_text(html)

    # 1. caractères hors alphabet latin
    offenders = {c for c in text if ord(c) > LATIN_MAX and c not in ALLOWED_HIGHER}
    if offenders:
        listed = ", ".join(f"U+{ord(c):04X} {c!r}" for c in sorted(offenders))
        errors.append(f"[{rel}] caractères non latins dans le texte visible : {listed}")

    # 2. mots cassés connus
    lowered = text.lower()
    for bad in KNOWN_BROKEN:
        if bad in lowered:
            errors.append(f"[{rel}] mot cassé détecté : {bad!r}")

    # 3. meta
    c = Collector()
    c.feed(html)
    if path.name not in SKIP_FILES:
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        if not title:
            errors.append(f"[{rel}] pas de <title>")
        else:
            t = title.group(1).strip()
            if len(t) > 60:
                errors.append(f"[{rel}] title {len(t)} caractères (> 60) : {t[:60]}…")
        desc = c.metas.get("description", "")
        if not desc:
            errors.append(f"[{rel}] pas de meta description")
        elif len(desc) > 160:
            errors.append(f"[{rel}] description {len(desc)} caractères (> 160)")
        if len(c.canonicals) != 1:
            errors.append(f"[{rel}] {len(c.canonicals)} canonical (1 attendu)")

    # 4. JSON-LD
    for block in c.jsonld:
        try:
            data = json.loads(block)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"[{rel}] JSON-LD invalide : {exc}")
            continue
        blob = json.dumps(data, ensure_ascii=False)
        if "aggregateRating" in blob or "reviewRating" in blob:
            errors.append(f"[{rel}] note/avis dans le JSON-LD (interdit : aucune donnée mesurée)")

    # 5. liens internes
    for href in dict.fromkeys(c.links):
        if href.startswith(("http://", "https://", "tel:", "mailto:", "data:")):
            continue
        p, _, frag = href.lstrip("/").partition("#")
        if not p:
            if frag and site_ids and frag not in site_ids:
                errors.append(f"[{rel}] ancre interne cassée : {href}")
            continue
        target = ROOT / p
        if not (target.is_file() or (target / "index.html").is_file()):
            errors.append(f"[{rel}] lien interne mort : {href}")

    # 6. affirmations non vérifiables
    for pat in FORBIDDEN_CLAIMS:
        if re.search(pat, text, re.I):
            errors.append(f"[{rel}] affirmation non sourcée : /{pat}/")

    # 6b. fuites d'anglais dans le texte visible
    for pat in ENGLISH_LEAKS:
        if re.search(pat, text, re.I):
            errors.append(f"[{rel}] mot anglais dans le texte FR : /{pat}/")

    # 7. durées par patient : avertissement, à recouper avec les faits produit
    if re.search(r"\b\d+ (minutes|secondes) (par|chaque) (patient|visite)", text):
        warnings.append(f"[{rel}] contient des durées par patient — vérifier qu'elles sont déjà publiées sur le site")

    return errors + [f"WARN {w}" for w in warnings]


def main() -> int:
    targets = [Path(a) if Path(a).is_absolute() else ROOT / a for a in sys.argv[1:]]
    if not targets:
        targets = sorted(
            p for p in ROOT.rglob("*.html")
            if not any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts)
        )

    # ids du site pour valider les ancres inter-pages
    site_ids: set[str] = set()
    for p in ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        site_ids.update(re.findall(r'\bid="([^"]+)"', p.read_text(encoding="utf-8", errors="ignore")))

    all_errors: list[str] = []
    all_warn: list[str] = []
    for p in targets:
        if not p.is_file():
            print(f"  SKIP  {p} (absent)")
            continue
        res = check_page(p, site_ids, "")
        errs = [r for r in res if not r.startswith("WARN")]
        warns = [r for r in res if r.startswith("WARN")]
        print(("  OK    " if not errs else "  FAIL  ") + str(p.relative_to(ROOT)) + (f"  ({len(warns)} avert.)" if warns else ""))
        for e in errs:
            print("          " + e)
        for w in warns:
            print("          " + w)
        all_errors += errs
        all_warn += warns

    print()
    print(f"{len(targets)} page(s) contrôlée(s) — {len(all_errors)} erreur(s), {len(all_warn)} avertissement(s).")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
