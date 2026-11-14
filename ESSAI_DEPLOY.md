# ClinixOS — Essai gratuit 7 jours

## URLs

- Canonical: **https://clinixospro.com/essai**
- Redirects: `/essai-gratuit`, `/trial`, `/7jours`, `/free-trial`, `/essai/` → `/essai` (301)
- Admin: **https://clinixospro.com/admin/essais**
- Legal: **https://clinixospro.com/essai/legal**
- QR code: `/img/essai-qr.png` → `https://clinixospro.com/essai`

## Installer

- File: `ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe`
- Size: `334,214,279` bytes (319 MiB)
- SHA-256: `d3d7ff8fe33fbf54659d65308a26551c7b6a6c11530007e6ec254e4296208548`
- Hosted as public GitHub release asset:
  `https://github.com/cheminisifeddine/clinixospro/releases/download/essai-3.5.2/ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe`
- Branded route: `/downloads/ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe?lead=ID`
  - Updates `downloaded_at`
  - Streams from `TRIAL_R2` if bound
  - Otherwise 302 to the GitHub release asset (attachment disposition set by GitHub)
  - `TRIAL_DOWNLOAD_URL` overrides the release URL
- Gofile fallback is only shown after a successful form submission.

## Backend

- D1 binding: **`AFF_DB`** (same database as the affiliate portal)
- Table: `trial_leads` — lazy-created by the API; migration in `schema/trial_leads.sql`
- `POST /api/trial-lead` — validates name/phone, normalizes phone to `+213…`, rate-limits to 3 submissions/IP/hour, stores UTM/fbclid context, writes the lead, returns download URL.
- `GET/DELETE /api/admin/essais` — protected list/search/CSV/delete endpoint.
- `POST /api/admin/login` / `POST /api/admin/logout` — signed HttpOnly admin cookie.

## Environment variables / bindings

| Name | Required | Purpose |
|---|---|---|
| `TRIAL_ADMIN_TOKEN` | yes (admin) | Admin password/token; also HMAC secret for the admin cookie |
| `TRIAL_IP_SALT` | recommended | Salt for the stored IP hash |
| `TRIAL_OWNER_EMAIL` | optional | Where new-lead emails are sent |
| `RESEND_API_KEY` | optional | Resend API key for email notifications |
| `TRIAL_EMAIL_FROM` | optional | Verified Resend sender |
| `TRIAL_DOWNLOAD_URL` | optional | Override the GitHub release asset URL |
| `TRIAL_R2` | optional | R2 binding with the installer for streamed branded downloads |

Without `TRIAL_ADMIN_TOKEN`, `/admin/essais` stays inaccessible (503). Without Resend variables, leads are still saved and the download still works; no email is sent.

## Security / legal

- Server-side validation and parameterized D1 queries.
- Consent checkbox removed at the owner's request: the form asks only name + phone; the server stores the phone/name and does not require a consent flag. Legal review is recommended (Algerian Law 18-07).
- Honeypot + same-origin (`Origin`/`Sec-Fetch-Site`) checks.
- IP stored as SHA-256 hash only.
- Rate limit: 3 submissions per IP per hour.
- Admin cookie: HttpOnly, Secure, SameSite=Lax, HMAC-signed, 12 h.
- `/admin/*` is `noindex,nofollow`; `/api/*` and `/downloads/*` are `no-store`.
- HSTS added in `_headers`.
- Privacy/terms: `/essai/legal`; retention 24 months (`schema/purge_trial_leads.sql`).
- Turnstile is **not** enabled by default (optional; add `TURNSTILE_SECRET` + widget if bot volume appears).

## Analytics

Page events pushed to `fbq('trackCustom', …)` and `window.dataLayer`:

`trial_page_view`, `trial_form_start`, `trial_form_submit`, `trial_download_start`, `trial_download_complete` (best-effort after the auto-download), `whatsapp_click`.

## Notes

- The form starts the download immediately after the API accepts the lead.
- The direct `/downloads/...` URL is not shown before submission.
- If the GitHub asset is unavailable, the success panel exposes the Gofile fallback.
- Admin list/search/CSV/delete are implemented; email is optional and never blocks the lead/download.
