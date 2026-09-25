#!/usr/bin/env python3
"""Génère les balises JSON-LD (SoftwareApplication + FAQPage) de index.html.

Les questions/réponses de la FAQ sont extraites du contenu visible de la page
pour que le balisage reste identique au texte affiché. Le bloc produit est
inséré avant </head> ; relancer après toute modification de la FAQ.

Aucune note, aucun avis et aucune affirmation médicale n'est généré : seules
les caractéristiques déjà affirmées sur la page sont reprises.
"""
import json
import re
import sys
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.html"
MARKER = "<!-- /seo:jsonld -->"
BRAND = "ClinixOS Pro"
ORIGIN = "https://clinixospro.com/"
IMAGE = "https://pub-3495f018eae749eaac503d3cf444cda2.r2.dev/finalversion.png"
SALE_PRICE = "9900"
LIST_PRICE = "35000"
CURRENCY = "DZD"
SOFTWARE_VERSION = "4.2"


def text_of(fragment: str) -> str:
    """Texte visible d'un fragment HTML, espaces normalisés."""
    clean = re.sub(r"<[^>]+>", " ", fragment)
    clean = clean.replace("&nbsp;", " ").replace("&amp;", "&")
    clean = clean.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return re.sub(r"\s+", " ", clean).strip()


def extract_faq(html: str) -> list[dict]:
    questions = [
        text_of(q) for q in re.findall(r"<button[^>]*class=\"[^\"]*faq-q[^\"]*\"[^>]*>(.*?)</button>", html, re.S)
    ]
    answers = [
        text_of(a) for a in re.findall(r"<div[^>]*class=\"[^\"]*faq-a[^\"]*\"[^>]*>(.*?)</div>", html, re.S)
    ]
    if len(questions) != len(answers):
        sys.exit(f"FAQ Questions/Réponses désalignées : {len(questions)} / {len(answers)}")

    faq = []
    for index, (question, answer) in enumerate(zip(questions, answers), start=1):
        # Le numéro "1." est un habillage visuel de la page, pas du contenu.
        faq.append(
            {
                "@type": "Question",
                "name": re.sub(r"^\d+\.\s*", "", question),
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
        )
    return faq


def build(faq: list[dict]) -> list[dict]:
    description = (
        "Logiciel de gestion de cabinet médical 100% hors-ligne pour médecins libéraux en Algérie : "
        "dossiers patients, ordonnances A5, salle d'attente, caisse et statistiques, "
        "avec synchronisation médecin-secrétaire sur réseau local."
    )
    return [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": ORIGIN + "#website",
            "url": ORIGIN,
            "name": BRAND,
            "inLanguage": "fr-DZ",
        },
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": ORIGIN + "#organization",
            "name": BRAND,
            "url": ORIGIN,
            "logo": {
                "@type": "ImageObject",
                "url": "https://clinixospro.com/img/logo.png",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": BRAND,
            "url": ORIGIN,
            "image": IMAGE,
            "description": description,
            "inLanguage": "fr-DZ",
            "applicationCategory": "MedicalApplication",
            "operatingSystem": "Windows 7, Windows 8, Windows 10, Windows 11",
            "softwareVersion": SOFTWARE_VERSION,
            "publisher": {"@id": ORIGIN + "#organization"},
            "offers": {
                "@type": "Offer",
                "price": SALE_PRICE,
                "priceCurrency": CURRENCY,
                "availability": "https://schema.org/InStock",
                "url": ORIGIN + "#commander",
                "priceSpecification": {
                    "@type": "PriceSpecification",
                    "price": LIST_PRICE,
                    "priceCurrency": CURRENCY,
                    "valueAddedTaxIncluded": False,
                },
                "businessFunction": "https://purl.org/goodrelations/v1#Sell",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "@id": ORIGIN + "#faq",
            "inLanguage": "fr-DZ",
            "mainEntity": faq,
        },
    ]


def main() -> None:
    html = INDEX.read_text(encoding="utf-8")
    faq = extract_faq(html)
    blocks = "\n".join(
        '<script type="application/ld+json">' + json.dumps(node, ensure_ascii=False, indent=2) + "</script>"
        for node in build(faq)
    )
    replacement = MARKER + "\n" + blocks + "\n"

    body = re.sub(
        re.escape(MARKER) + r".*?(?=</head>)",
        replacement,
        html,
        flags=re.S,
    )
    if body == html:
        sys.exit("Marqueur <!-- /seo:jsonld --> introuvable avant </head>.")

    INDEX.write_text(body, encoding="utf-8")
    print(f"JSON-LD écrit : {len(faq)} questions, {len(body)} octets au total.")


if __name__ == "__main__":
    main()
