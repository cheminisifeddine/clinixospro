# ClinixOS — Essai 7 jours — Test report

Date: **2026-11-14**  
Page: **https://clinixospro.com/essai**  
Commit: `b065fdf` (page/API/admin) + `86f2b1a` (headers) + UI contrast/touch fixes

## What was tested

| # | Acceptance test | Status | Evidence |
|---:|---|---|---|
| 1 | `/essai` opens on desktop and mobile | **PASS** | 200; tested at 360, 390, 768, 1440 px; no horizontal scroll |
| 2 | Form is visible on a phone without scrolling | **PASS** | Form starts at 434 px, first field at 565 px on 390×844 and 360×640 |
| 3 | `/trial`, `/7jours`, `/essai-gratuit`, `/free-trial` redirect to `/essai` | **PASS** | Live 301 to `https://clinixospro.com/essai` |
| 4 | Full name required | **PASS** | Client + server; invalid/empty returns French error; form not cleared |
| 5 | Phone required | **PASS** | Client + server |
| 6 | Invalid phone shows a clear error | **PASS** | `Numéro de téléphone invalide. Exemple : 0770 49 49 50.` |
| 7 | Consent required | **PASS** | Client + server; checkbox required |
| 8 | Valid form saves a lead | **PASS (local D1)** | Wrangler Pages dev + local D1 inserted lead; production binding is `AFF_DB`; table is lazy-created/migration included |
| 9 | Valid form starts the installer download | **PASS** | API returns `/downloads/…?lead=ID`; `window.location` starts download; fallback button present |
| 10 | Download file is the correct 319 MB installer | **PASS** | GitHub release asset: **334,214,279 bytes** (319 MiB) |
| 11 | SHA-256 matches `d3d7ff…08548` | **PASS** | Local source file hash matches exactly; same file uploaded |
| 12 | Lead appears in `/admin/essais` | **PASS (local)** | Admin login + list tested with a test token; live requires `TRIAL_ADMIN_TOKEN` |
| 13 | CSV export works | **PASS (local)** | Downloaded CSV with UTF-8 headers and escaped values |
| 14 | Owner receives an email notification | **NOT CONFIGURED** | Code uses Resend when `RESEND_API_KEY` + `TRIAL_OWNER_EMAIL` are set; no key was provided |
| 15 | WhatsApp link opens `wa.me/213770494950` | **PASS** | Link present in page/legal/success panel |
| 16 | QR code points to `/essai` | **PASS** | `img/essai-qr.png`, generated for `https://clinixospro.com/essai` |
| 17 | Accessible form errors / JS | **PASS** | `role="alert"`, focusable fields, inline errors; no console errors |
| 18 | Rate limit: max 3 submissions/IP/hour | **PASS (local)** | 4th valid request returned HTTP 429 |
| 19 | Honeypot blocks bots | **PASS** | Filled `website` field returns 400 and does not insert |
| 20 | No Gofile link visible before submission | **PASS** | Fallback `href` is `#`; set from API only in the success panel |
| 21 | Page loads under 3 seconds | **PASS** | Local Lighthouse FCP/LCP **0.7 s**, Speed Index **1.2 s**; page assets ~216 KB; 419 KB total with fonts |
| 22 | No console errors | **PASS** | Desktop/mobile Playwright checks |
| 23 | No horizontal scrolling on mobile | **PASS** | 360/390/768/1440; `scrollWidth === innerWidth` |
| 24 | Admin endpoint protected | **PASS** | Unauthenticated `/api/admin/essais` → 401; login requires `TRIAL_ADMIN_TOKEN`; signed HttpOnly cookie |
| 25 | HSTS enabled | **PASS** | Live `strict-transport-security: max-age=31536000; includeSubDomains` |
| 26 | Legal/privacy pages linked | **PASS** | `/essai/legal` 200; consent links to privacy/terms |
| 27 | SEO title/description/canonical/schema/sitemap | **PASS** | Exact title, description, canonical `/essai`, SoftwareApplication + FAQ schema, sitemap entry, robots index |
| 28 | Download route updates `downloaded_at` | **PASS (local)** | `/downloads/…?lead=1` updated the lead; admin showed `Oui` |
| 29 | Admin delete on request | **PASS (local)** | DELETE removed lead; list total decreased |
| 30 | Daily totals | **PASS (local)** | Admin API stats grouped by date |

## Lighthouse (trial page, local)

| Category | Score |
|---|---:|
| Performance | **74** (Meta Pixel main-thread cost) |
| Accessibility | **100** after contrast fix |
| Best Practices | **100** |
| SEO | **100** |

- FCP/LCP **0.7 s**, CLS **0.001**, Speed Index **1.2 s**.
- Total bytes **419 KiB** including fonts; page HTML/assets ~216 KiB.
- The performance score is limited by the Meta Pixel script, not the page assets.

## Installer hosting

- File: `ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe`
- Size: **334,214,279 bytes** (319 MiB)
- SHA-256: `d3d7ff8fe33fbf54659d65308a26551c7b6a6c11530007e6ec254e4296208548`
- Public asset:
  `https://github.com/cheminisifeddine/clinixospro/releases/download/essai-3.5.2/ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe`
- Branded route:
  `https://clinixospro.com/downloads/ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe?lead=ID`
  → 302 to the GitHub release asset, which returns `Content-Disposition: attachment`.
- Optional R2 streaming: bind `TRIAL_R2`; the route then streams with its own attachment header.

## Configuration required before going live

These are environment settings in the Cloudflare Pages project (not frontend secrets):

| Variable / binding | Required | Notes |
|---|---|---|
| `AFF_DB` | yes | Existing D1 binding; `trial_leads` is created lazily or via `schema/trial_leads.sql` |
| `TRIAL_ADMIN_TOKEN` | yes, for admin | Long random string; `/admin/essais` login returns 503 until set |
| `TRIAL_IP_SALT` | recommended | Salt used to hash IPs |
| `RESEND_API_KEY` | optional | Enables owner email notifications |
| `TRIAL_OWNER_EMAIL` | optional | Recipient for notifications |
| `TRIAL_EMAIL_FROM` | optional | Verified Resend sender |
| `TRIAL_DOWNLOAD_URL` | optional | Overrides the GitHub asset URL |
| `TRIAL_R2` | optional | Streams the installer from R2 instead of redirecting to GitHub |

Turnstile is not enabled by default (optional). The form already has a honeypot, consent enforcement, same-origin checks and a 3/IP/hour limit.

## Important notes

- No fake production lead was inserted during testing. Lead DB tests ran against local D1; the production code uses the same D1 binding.
- Email was not sent because no Resend credentials were provided. The code path is implemented and non-blocking.
- Admin live access requires setting `TRIAL_ADMIN_TOKEN`; the static login page is public but no lead data is returned without auth.
- The page uses the existing Meta Pixel `3184145215124032`; custom events are pushed to `fbq` and `window.dataLayer`.
- `trial_download_complete` is best-effort after the automatic download starts; a browser cannot reliably report download completion.
- Retention script: `schema/purge_trial_leads.sql` (24 months).
