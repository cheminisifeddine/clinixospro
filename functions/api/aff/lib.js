// ClinixOS affiliate portal — shared backend helpers (Cloudflare Pages Functions + D1).
// The Google Sheet stays the back-office source of truth (validation, payouts);
// D1 owns accounts, sessions and portal data. Dual-write keeps both in sync.

export const GAS_EXEC = 'https://script.google.com/macros/s/AKfycbzvjQ9Yjm-oIrKqz1Ii1-XiCvNATamySYDrSEk1Pc0XEcdCBSXVmcVzgD-YoykESeS35w/exec';
export const SESSION_DAYS = 30;

export function json(data, status, headers) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, headers || {}),
  });
}

export function readSessionToken(req) {
  const c = req.headers.get('Cookie') || '';
  const m = c.match(/(?:^|;\s*)aff_session=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

export function sessionCookie(token) {
  return 'aff_session=' + encodeURIComponent(token) +
    '; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=' + SESSION_DAYS * 86400;
}

export function clearCookie() {
  return 'aff_session=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0';
}

export async function getAffiliate(db, req) {
  const token = readSessionToken(req);
  if (!token) return null;
  const s = await db.prepare(
    'SELECT s.affiliate_id, s.expires_at, a.* FROM aff_sessions s ' +
    'JOIN aff_affiliates a ON a.id = s.affiliate_id WHERE s.token = ?'
  ).bind(token).first();
  if (!s) return null;
  if (new Date(s.expires_at).getTime() < Date.now()) {
    await db.prepare('DELETE FROM aff_sessions WHERE token = ?').bind(token).run();
    return null;
  }
  return s;
}

export async function createSession(db, affiliateId) {
  const token = crypto.randomUUID() + crypto.randomUUID().replace(/-/g, '');
  const exp = new Date(Date.now() + SESSION_DAYS * 864e5).toISOString();
  await db.prepare('INSERT INTO aff_sessions (token, affiliate_id, expires_at) VALUES (?,?,?)')
    .bind(token, affiliateId, exp).run();
  return token;
}

function b64(bytes) {
  const b = new Uint8Array(bytes);
  let s = '';
  for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
  return btoa(s);
}

export function makeSalt() {
  return b64(crypto.getRandomValues(new Uint8Array(16)));
}

// PBKDF2-SHA256, 120k iterations — proper password hashing (WebCrypto).
export async function hashPassword(password, salt) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: enc.encode(salt), iterations: 100000, hash: 'SHA-256' },
    key, 256);
  return b64(bits);
}

export function cleanCode(s) {
  return String(s || '').toUpperCase().replace(/[^A-Z0-9\-_]/g, '').slice(0, 32);
}

export function validEmail(e) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(e || ''));
}

export function validDzPhone(t) {
  return /^(05|06|07)\d{8}$/.test(String(t || '').replace(/[\s.\-]/g, ''));
}

export function genCode(nom) {
  const stem = String(nom || '').toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^A-Z]/g, '').slice(0, 6) || 'AFF';
  return stem + '-' + Math.floor(10 + Math.random() * 90);
}

export function publicProfile(a) {
  return {
    code: a.code, nom: a.nom, telephone: a.telephone, plateforme: a.plateforme,
    pseudo: a.pseudo, abonnes: a.abonnes || '', email: a.email,
    paiement_type: a.paiement_type || '', paiement_num: a.paiement_num || '',
    titulaire: a.titulaire || '', taux: a.taux, statut: a.statut,
    has_password: !!(a.pass_hash && a.pass_salt),
    sheet_ok: !!a.sheet_ok, created_at: a.created_at,
  };
}

export function personalUrl(code) {
  return 'https://clinixospro.com/?ref=' + encodeURIComponent(code);
}

/* ---------- Google Apps Script bridge ---------- */
async function gasPost(params) {
  const body = new URLSearchParams(params);
  const res = await fetch(GAS_EXEC, { method: 'POST', body });
  if (!res.ok) throw new Error('gas http ' + res.status);
  return res.json();
}

// Dual-write: keep the "Affiliés" sheet in sync (validation + payouts happen there).
export async function gasSignup(aff) {
  const payload = {
    action: 'affiliate_signup',
    nom: aff.nom, telephone: aff.telephone, plateforme: aff.plateforme,
    pseudo: aff.pseudo, abonnes: aff.abonnes || '', email: aff.email,
    paiement: 'À compléter', titulaire: 'À compléter',
    code_souhaite: aff.code,
  };
  // Retry once: the Sheet is Oussama's back-office, the dual-write must land.
  // (affSignup_ rejects duplicate codes, so a retry can never create two rows.)
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const d = await gasPost(payload);
      if (d && d.result === 'success') return d.code || null;
    } catch (e) { /* transient: retry once */ }
    if (attempt === 0) await new Promise(r => setTimeout(r, 1500));
  }
  return null;
}

export async function gasStats(code) {
  const res = await fetch(GAS_EXEC + '?action=stats&code=' + encodeURIComponent(code) + '&_=' + Date.now());
  if (!res.ok) throw new Error('gas stats http ' + res.status);
  return res.json();
}

export async function gasSetPaiement(code, paiement, titulaire) {
  try {
    const d = await gasPost({ action: 'affiliate_set_paiement', code, paiement, titulaire });
    // Fail closed: only a deployed affSetPaiement_ returns paiement_updated.
    // (Unknown actions fall through to the order logic and return a bare success.)
    return !!(d && d.result === 'success' && d.paiement_updated === true);
  } catch (e) { return false; }
}
