# ClinixOS Pro Landing

High-converting French landing page for ClinixOS Pro (medical clinic software, Algeria).

- Single-file HTML + CSS (no framework) — fast for Meta Andromeda post-click
- COD order form: name, specialty, phone, secondary phone, wilaya (58), city, address
- Meta Pixel Lead + Purchase events
- Deployed on Cloudflare Pages → clinixospro.com

## Local

```bash
python3 -m http.server 8765
open http://127.0.0.1:8765/
```

## Deploy

Push to `main` → Cloudflare Pages auto-deploys.
