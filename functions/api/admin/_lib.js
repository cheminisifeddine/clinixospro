export function json(data, status, headers) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: Object.assign({
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
    }, headers || {}),
  });
}

function b64url(bytes) {
  let s = '';
  const arr = new Uint8Array(bytes);
  for (let i = 0; i < arr.length; i++) s += String.fromCharCode(arr[i]);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

async function hmac(value, secret) {
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(value));
  return b64url(sig);
}

export function cookieValue(request, name) {
  const raw = request.headers.get('Cookie') || '';
  const parts = raw.split(';');
  for (const part of parts) {
    const i = part.indexOf('=');
    if (i < 0) continue;
    if (part.slice(0, i).trim() === name) {
      try { return decodeURIComponent(part.slice(i + 1).trim()); }
      catch (e) { return part.slice(i + 1).trim(); }
    }
  }
  return '';
}

export async function createAdminSession(secret) {
  const payload = String(Date.now() + 12 * 3600 * 1000);
  return payload + '.' + await hmac(payload, secret);
}

export function adminCookie(token) {
  return 'trial_admin=' + encodeURIComponent(token) +
    '; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=43200';
}

export function clearAdminCookie() {
  return 'trial_admin=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0';
}

export async function isAdmin(request, env) {
  if (!env.TRIAL_ADMIN_TOKEN) return false;

  const auth = request.headers.get('Authorization') || '';
  if (auth === 'Bearer ' + env.TRIAL_ADMIN_TOKEN) return true;

  const token = cookieValue(request, 'trial_admin');
  if (!token) return false;
  const dot = token.lastIndexOf('.');
  if (dot < 1) return false;
  const payload = token.slice(0, dot);
  const signature = token.slice(dot + 1);
  const expected = await hmac(payload, env.TRIAL_ADMIN_TOKEN);
  if (signature !== expected) return false;
  return Number(payload) > Date.now();
}

export function csvEscape(value) {
  const s = String(value == null ? '' : value);
  return '"' + s.replace(/"/g, '""') + '"';
}
