# ClinixOS Pro Landing

High-converting French landing page for ClinixOS Pro (medical clinic software, Algeria).

- Single-file HTML + CSS (no framework) — fast for Meta Andromeda post-click
- COD order form: name, phone, wilaya (58), commune, address — 5 visible fields
- Meta Pixel `3184145215124032` — Lead + Purchase events
- Live: **https://clinixospro.com** (+ `www`, Cloudflare zone active, Pages custom domains active)

## Local

```bash
python3 -m http.server 8765
open http://127.0.0.1:8765/
```

## Deploy

Push to `main`, then trigger a Pages deployment if the GitHub App webhook is quiet:

```bash
# CF Pages ad-hoc deploy (account token with Pages Deploy)
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT>/pages/projects/clinixospro/deployments" \
  -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" -d '{"branch":"main"}'
```

## Conversion v2 (2026-11)

- `index.html` — cold-traffic landing page optimised for Meta ads: mobile CTA above the fold, 5-field COD form, fixed 9 900 DA total, FAQ before the form, honest agency-vs-USB price anchor, no countdown / no paid options.
- `legal.html` — mentions légales, confidentialité, CGV, garantie 7 jours.
- `ADS.md` — Meta Ads playbook (angles, hooks, primary text, UTM links, test plan).
- Testimonials: fill `window.CX_TESTIMONIALS` in `index.html` with **real** doctor quotes. The section stays hidden until at least one quote is added.
- HTML is now sent with `Cache-Control: no-store` (the old 4h browser cache kept showing the countdown/upsell version on mobile).
- For ads, use a UTM-tagged URL (e.g. `?utm_source=facebook&utm_medium=paid&utm_campaign=cold_medecins_dz`) so mobile browsers never reuse a stale cached copy.
