// POST /api/aff/login — email + password.
import { json, validEmail, hashPassword, createSession, sessionCookie, publicProfile } from './lib.js';

function bad() {
  // Generic message: never reveal whether the email exists or the password was wrong.
  return json({ result: 'error', error: 'Email ou mot de passe incorrect.' }, 401);
}

export async function onRequestPost({ request, env }) {
  const db = env.AFF_DB;
  if (!db) return json({ result: 'error', error: 'Base de données indisponible.' }, 500);
  let b;
  try { b = await request.json(); }
  catch (e) { return json({ result: 'error', error: 'Requête invalide.' }, 400); }

  const email = String(b.email || '').trim().toLowerCase();
  const pw = String(b.password || '');
  if (!validEmail(email) || !pw) return bad();

  const row = await db.prepare('SELECT * FROM aff_affiliates WHERE email = ?').bind(email).first();
  if (!row || !row.pass_hash || !row.pass_salt) return bad();
  const hash = await hashPassword(pw, row.pass_salt);
  if (hash.length !== row.pass_hash.length || hash !== row.pass_hash) return bad();

  const token = await createSession(db, row.id);
  return json({ result: 'success', affiliate: publicProfile(row) },
    200, { 'Set-Cookie': sessionCookie(token) });
}
