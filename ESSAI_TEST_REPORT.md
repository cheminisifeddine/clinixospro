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
| 7 | Consent checkbox | **REMOVED** | Removed at owner request; form now asks only name + phone; server stores consent=0; legal review advised |
| 8 | Valid form saves a lead (name + phone only) | **PASS (production)** | Live `POST /api/trial-lead` created lead id 4 in D1 `clinixos-v2-db`; test lead deleted after verification |
| 9 | Valid form starts the installer download | **PASS** | API returns `/downloads/…?lead=ID`; `window.location` starts download; fallback button present |
| 10 | Download file is the correct 319 MB installer | **PASS** | GitHub release asset: **334,214,279 bytes** (319 MiB) |
| 11 | SHA-256 matches `d3d7ff…08548` | **PASS** | Local source file hash matches exactly; same file uploaded |
| 12 | Lead appears in `/admin/essais` | **PASS (production)** | Live admin login + list; test lead visible before deletion |
| 13 | CSV export works | **PASS (production)** | Live CSV with UTF-8 headers and escaped values |
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
| 24 | Admin endpoint protected | **PASS** | `GET /api/admin/essais` → 405 (never cached); unauth `POST` → 401; cross-origin `POST` → 403; signed HttpOnly cookie |
| 25 | HSTS enabled | **PASS** | Live `strict-transport-security: max-age=31536000; includeSubDomains` |
| 26 | Legal/privacy pages linked | **PASS** | `/essai/legal` 200; privacy/terms linked in footer |
| 27 | SEO title/description/canonical/schema/sitemap | **PASS** | Exact title, description, canonical `/essai`, SoftwareApplication + FAQ schema, sitemap entry, robots index |
| 28 | Download route updates `downloaded_at` | **PASS (production)** | `/downloads/…?lead=4` updated the lead; admin showed `Oui` |
| 29 | Admin delete on request | **PASS (production)** | DELETE removed the test lead; list total decreased |
| 30 | Daily totals | **PASS (production)** | Admin API stats grouped by date |
| 31 | Admin data cannot be cached by Cloudflare | **PASS** | Admin reads use POST; GET returns 405; unauth POST returns 401 |

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

Turnstile is not enabled by default (optional). The form has a honeypot, same-origin checks and a 3/IP/hour limit. Consent checkbox removed at owner request.

## Important notes

- Two production test leads (ids 4 and 5) were inserted through the live API to verify the end-to-end flow, then deleted. Leads 1–3 are real/user leads and were left untouched.
- The zone Page Rules use Cache Everything + 2 h Edge TTL, which overrides `no-store`. Admin reads therefore use POST (never cached), and `/essai` must be purged after each deploy. Recommended permanent fix: set the Page Rules to Cache Level Standard or add bypass rules for `/api/*`, `/admin/*` and `/essai*`.
- Email was not sent because no Resend credentials were provided. The code path is implemented and non-blocking.
- Admin live access requires setting `TRIAL_ADMIN_TOKEN`; the static login page is public but no lead data is returned without auth.
- The page uses the existing Meta Pixel `3184145215124032`; custom events are pushed to `fbq` and `window.dataLayer`.
- `trial_download_complete` is best-effort after the automatic download starts; a browser cannot reliably report download completion.
- Retention script: `schema/purge_trial_leads.sql` (24 months).
