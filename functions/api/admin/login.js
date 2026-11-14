import { json, createAdminSession, adminCookie } from './_lib.js';

export async function onRequestPost({ request, env }) {
  if (!env.TRIAL_ADMIN_TOKEN) {
    return json({ error: 'Admin non configuré (TRIAL_ADMIN_TOKEN manquant).' }, 503);
  }
  let body;
  try { body = await request.json(); }
  catch (e) { return json({ error: 'Requête invalide.' }, 400); }

  const password = String(body.password || '');
  if (password !== env.TRIAL_ADMIN_TOKEN) {
    return json({ error: 'Mot de passe incorrect.' }, 401);
  }
  const session = await createAdminSession(env.TRIAL_ADMIN_TOKEN);
  return json({ ok: true }, 200, { 'Set-Cookie': adminCookie(session) });
}
