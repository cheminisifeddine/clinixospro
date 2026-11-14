import { json, isAdmin, csvEscape } from './_lib.js';

let schemaReady = false;

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
  schemaReady = true;
}

const COLUMNS = 'id, full_name, phone_raw, phone_e164, clinic, email, consent, consent_at, source, utm_source, utm_medium, utm_campaign, created_at, downloaded_at';

function sameOrigin(request) {
  const origin = request.headers.get('Origin');
  if (!origin) return true;
  try {
    return new URL(origin).host === request.headers.get('Host');
  } catch (e) {
    return false;
  }
}

// Admin data must never be served over GET: the zone has a Cache Everything
// Page Rule that ignores origin cache headers and could cache a response
// containing leads. POST is never cached by Cloudflare.
export async function onRequestGet() {
  return json({ error: 'Méthode non autorisée.' }, 405);
}

export async function onRequestPost({ request, env }) {
  if (!sameOrigin(request)) return json({ error: 'Origine non autorisée.' }, 403);
  if (!(await isAdmin(request, env))) return json({ error: 'Non autorisé.' }, 401);
  const db = env.AFF_DB;
  if (!db) return json({ error: 'Base de données indisponible.' }, 500);
  await ensureSchema(db);

  let body = {};
  try {
    body = await request.json();
  } catch (e) {}

  const q = String(body.q || '').trim().slice(0, 100);
  const format = body.format === 'csv' ? 'csv' : '';
  const rawLimit = parseInt(body.limit || 500, 10);
  const limit = Math.min(5000, Math.max(1, Number.isFinite(rawLimit) ? rawLimit : 500));

  let where = '';
  let params = [];
  if (q) {
    where = 'WHERE full_name LIKE ? OR phone_e164 LIKE ? OR phone_raw LIKE ? OR clinic LIKE ? OR email LIKE ?';
    const like = '%' + q + '%';
    params = [like, like, like, like, like];
  }

  const stmt = db.prepare(
    'SELECT ' + COLUMNS + ' FROM trial_leads ' + where + ' ORDER BY created_at DESC LIMIT ?'
  );
  const rows = await stmt.bind(...params, limit).all();
  const leads = rows.results || [];

  if (format === 'csv') {
    const header = ['id', 'date', 'nom', 'telephone', 'telephone_normalise', 'source', 'utm_source', 'utm_medium', 'utm_campaign', 'telecharge_le'];
    const lines = [header.map(csvEscape).join(',')];
    for (const l of leads) {
      lines.push([
        l.id, l.created_at, l.full_name, l.phone_raw, l.phone_e164,
        l.source || '',
        l.utm_source || '', l.utm_medium || '', l.utm_campaign || '', l.downloaded_at || '',
      ].map(csvEscape).join(','));
    }
    return new Response(lines.join('\r\n'), {
      status: 200,
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': 'attachment; filename="clinixos-essais-' + new Date().toISOString().slice(0, 10) + '.csv"',
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
      },
    });
  }

  const stats = await db.prepare(
    "SELECT substr(created_at,1,10) AS day, COUNT(*) AS total FROM trial_leads GROUP BY day ORDER BY day DESC LIMIT 14"
  ).all();
  const total = await db.prepare('SELECT COUNT(*) AS n FROM trial_leads').first();

  return json({
    ok: true,
    leads,
    total: total ? Number(total.n) : leads.length,
    stats: stats.results || [],
    query: q,
  });
}

export async function onRequestDelete({ request, env }) {
  if (!sameOrigin(request)) return json({ error: 'Origine non autorisée.' }, 403);
  if (!(await isAdmin(request, env))) return json({ error: 'Non autorisé.' }, 401);
  const db = env.AFF_DB;
  if (!db) return json({ error: 'Base de données indisponible.' }, 500);
  await ensureSchema(db);

  const url = new URL(request.url);
  let id = parseInt(url.searchParams.get('id') || '0', 10);
  if (!id) {
    try {
      const body = await request.json();
      id = parseInt(body.id || 0, 10);
    } catch (e) {}
  }
  if (!id) return json({ error: 'Identifiant manquant.' }, 400);
  await db.prepare('DELETE FROM trial_leads WHERE id = ?').bind(id).run();
  return json({ ok: true });
}
