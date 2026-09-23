# ClinixOS Pro Landing

High-converting French landing page for ClinixOS Pro (medical clinic software, Algeria).

- Single-file HTML + CSS (no framework) — fast for Meta Andromeda post-click
- COD order form: name, specialty, phone, secondary phone, wilaya (58), city, address
- Meta Pixel `3184145215124032` — Lead + Purchase events
- Live: **https://clinixospro.com** (Cloudflare Pages + zone `nina`/`ram.ns.cloudflare.com`)

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
