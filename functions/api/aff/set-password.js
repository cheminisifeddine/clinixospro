// POST /api/aff/set-password — step 2: the affiliate sets their password (enrollment).
import { json, getAffiliate, hashPassword, makeSalt, publicProfile } from './lib.js';

export async function onRequestPost({ request, env }) {
  const db = env.AFF_DB;
  if (!db) return json({ result: 'error', error: 'Base de données indisponible.' }, 500);
  const aff = await getAffiliate(db, request);
  if (!aff) return json({ result: 'error', error: 'Session expirée. Reconnectez-vous.' }, 401);

  let b;
  try { b = await request.json(); }
  catch (e) { return json({ result: 'error', error: 'Requête invalide.' }, 400); }
  const pw = String(b.password || '');
  if (pw.length < 8) return json({ result: 'error', error: 'Mot de passe : 8 caractères minimum.' }, 400);
  if (pw.length > 128) return json({ result: 'error', error: 'Mot de passe trop long.' }, 400);

  const salt = makeSalt();
  const hash = await hashPassword(pw, salt);
  await db.prepare('UPDATE aff_affiliates SET pass_hash = ?, pass_salt = ? WHERE id = ?')
    .bind(hash, salt, aff.affiliate_id).run();

  const row = await db.prepare('SELECT * FROM aff_affiliates WHERE id = ?').bind(aff.affiliate_id).first();
  return json({ result: 'success', affiliate: publicProfile(row) });
}