/**
 * POST /api/trial-lead
 * Saves a ClinixOS 7-day trial lead in D1, then returns the download URL.
 * The file itself is not exposed before a valid submission.
 */
const VERSION = '3.5.2';
const FILE_NAME = 'ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe';
const FILE_SIZE = '319 Mo';
const FILE_SHA256 = 'd3d7ff8fe33fbf54659d65308a26551c7b6a6c11530007e6ec254e4296208548';
const FALLBACK_URL = 'https://gofile.io/d/GsM2Xlqw';
const ALLOWED_ORIGINS = new Set([
  'https://clinixospro.com',
  'https://www.clinixospro.com',
]);

let schemaReady = false;

function json(data, status, headers) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: Object.assign({
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
    }, headers || {}),
  });
}

async function ensureSchema(db) {
  if (schemaReady) return;
  await db.prepare(`CREATE TABLE IF NOT EXISTS trial_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone_raw TEXT NOT NULL,
    phone_e164 TEXT NOT NULL,
    clinic TEXT DEFAULT '',
    email TEXT DEFAULT '',
    consent INTEGER NOT NULL DEFAULT 0,
    consent_at TEXT,
    source TEXT DEFAULT '',
    utm_source TEXT DEFAULT '',
    utm_medium TEXT DEFAULT '',
    utm_campaign TEXT DEFAULT '',
    page_url TEXT DEFAULT '',
    ip_hash TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    downloaded_at TEXT
  )`).run();
  await db.prepare('CREATE INDEX IF NOT EXISTS idx_trial_leads_created ON trial_leads(created_at)').run();
  await db.prepare('CREATE INDEX IF NOT EXISTS idx_trial_leads_phone ON trial_leads(phone_e164)').run();
  schemaReady = true;
}

function normalizePhone(value) {
  let d = String(value || '').replace(/\D/g, '');
  if (d.indexOf('00213') === 0) d = d.slice(5);
  else if (d.indexOf('213') === 0) d = d.slice(3);
  if (d.charAt(0) === '0') d = d.slice(1);
  return /^[5-7]\d{8}$/.test(d) ? '+213' + d : '';
}

function validName(value) {
  const s = String(value || '').trim();
  return s.length >= 2 && s.length <= 80 &&
    /^[\p{L}\p{M}][\p{L}\p{M}\s'’.\-]{1,79}$/u.test(s);
}

function validEmail(value) {
  return !value || /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(value));
}

function clean(value, max) {
  return String(value || '').trim().slice(0, max);
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

async function hashIp(ip, salt) {
  const data = new TextEncoder().encode(String(ip || 'unknown') + '|' + String(salt || 'clinixos-trial'));
  const digest = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function notifyOwner(env, lead) {
  if (!env.RESEND_API_KEY || !env.TRIAL_OWNER_EMAIL) return;
  const from = env.TRIAL_EMAIL_FROM || 'ClinixOS <onboarding@resend.dev>';
  const wa = 'https://wa.me/' + lead.phone_e164.replace(/\D/g, '');
  const html = `
    <h2>Nouvel essai ClinixOS</h2>
    <p><strong>Nom :</strong> ${escapeHtml(lead.full_name)}</p>
    <p><strong>Téléphone :</strong> ${escapeHtml(lead.phone_e164)}</p>
    <p><strong>Cabinet / ville :</strong> ${escapeHtml(lead.clinic || '—')}</p>
    <p><strong>E-mail :</strong> ${escapeHtml(lead.email || '—')}</p>
    <p><strong>Date :</strong> ${escapeHtml(lead.created_at)}</p>
    <p><strong>Source :</strong> ${escapeHtml(lead.source || '—')}</p>
    <p><strong>Consentement :</strong> oui (${escapeHtml(lead.consent_at || '—')})</p>
    <p><a href="${wa}">Contacter sur WhatsApp</a></p>
  `;
  await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: 'Bearer ' + env.RESEND_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from,
      to: [env.TRIAL_OWNER_EMAIL],
      subject: `Nouvel essai ClinixOS — ${lead.full_name} — ${lead.phone_e164}`,
      html,
    }),
  });
}

export async function onRequestPost(context) {
  const { request, env, waitUntil } = context;
  const db = env.AFF_DB;
  if (!db) return json({ error: 'Base de données indisponible.' }, 500);

  let body;
  try { body = await request.json(); }
  catch (e) { return json({ error: 'Requête invalide.' }, 400); }

  const origin = request.headers.get('Origin');
  let sameOrigin = false;
  try { sameOrigin = !!origin && new URL(origin).host === request.headers.get('Host'); } catch (e) {}
  if (origin && !ALLOWED_ORIGINS.has(origin) && !sameOrigin) {
    return json({ error: 'Origine non autorisée.' }, 403);
  }
  if (request.headers.get('Sec-Fetch-Site') === 'cross-site') {
    return json({ error: 'Requête non autorisée.' }, 403);
  }

  // Honeypot: filled by bots only.
  if (clean(body.website, 120)) return json({ error: 'Requête invalide.' }, 400);

  const fullName = clean(body.fullName, 80);
  const phoneRaw = clean(body.phone, 25);
  const phoneE164 = normalizePhone(phoneRaw);
  const clinic = clean(body.clinic, 100);
  const email = clean(body.email, 120).toLowerCase();
  const consent = body.consent === true || body.consent === 1 || body.consent === 'true';

  if (!validName(fullName)) {
    return json({ error: 'Le nom complet est obligatoire (2 à 80 caractères, lettres uniquement).' }, 400);
  }
  if (!phoneE164) {
    return json({ error: 'Numéro de téléphone invalide. Exemple : 0770 49 49 50.' }, 400);
  }
  if (!validEmail(email)) {
    return json({ error: 'Adresse e-mail invalide.' }, 400);
  }
  if (!consent) {
    return json({ error: "Vous devez accepter d'être contacté." }, 400);
  }

  await ensureSchema(db);

  const ip = request.headers.get('CF-Connecting-IP') ||
    (request.headers.get('X-Forwarded-For') || '').split(',')[0].trim();
  const ipHash = await hashIp(ip, env.TRIAL_IP_SALT);
  const now = new Date().toISOString();
  const cutoff = new Date(Date.now() - 3600 * 1000).toISOString();

  const recent = await db.prepare(
    'SELECT COUNT(*) AS n FROM trial_leads WHERE ip_hash = ? AND created_at >= ?'
  ).bind(ipHash, cutoff).first();
  if (recent && Number(recent.n) >= 3) {
    return json({ error: 'Trop de demandes depuis cette connexion. Réessayez dans une heure ou contactez-nous sur WhatsApp.' }, 429);
  }

  const utmSource = clean(body.utm_source, 120);
  const utmMedium = clean(body.utm_medium, 120);
  const utmCampaign = clean(body.utm_campaign, 120);
  const pageUrl = clean(body.page_url, 500);
  const userAgent = clean(request.headers.get('User-Agent'), 300);
  const source = clean(body.source, 120) || 'clinixospro.com/essai';

  const result = await db.prepare(`INSERT INTO trial_leads
    (full_name, phone_raw, phone_e164, clinic, email, consent, consent_at, source,
     utm_source, utm_medium, utm_campaign, page_url, ip_hash, user_agent, created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).bind(
    fullName, phoneRaw, phoneE164, clinic, email, 1, now, source,
    utmSource, utmMedium, utmCampaign, pageUrl, ipHash, userAgent, now
  ).run();

  const id = result.meta && result.meta.last_row_id;
  if (!id) return json({ error: "La commande n'a pas pu être enregistrée." }, 500);

  const lead = {
    full_name: fullName, phone_e164: phoneE164, clinic, email,
    source, created_at: now, consent_at: now,
  };
  const mail = notifyOwner(env, lead).catch((err) => console.error('trial email failed', err));
  if (typeof waitUntil === 'function') waitUntil(mail);

  return json({
    ok: true,
    leadId: id,
    downloadUrl: '/downloads/' + FILE_NAME + '?lead=' + encodeURIComponent(id),
    fallbackUrl: FALLBACK_URL,
    version: VERSION,
    size: FILE_SIZE,
    sha256: FILE_SHA256,
  });
}
