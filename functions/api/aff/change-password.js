// POST /api/aff/change-password
import { json, getAffiliate, hashPassword, makeSalt } from './lib.js';

export async function onRequestPost({ request, env }) {
  const db = env.AFF_DB;
  if (!db) return json({ result: 'error', error: 'Base de données indisponible.' }, 500);
  const aff = await getAffiliate(db, request);
  if (!aff) return json({ result: 'error', error: 'Non connecté.' }, 401);

  let b;
  try { b = await request.json(); }
  catch (e) { return json({ result: 'error', error: 'Requête invalide.' }, 400); }
  const cur = String(b.current || '');
  const pw = String(b.password || '');
  if (pw.length < 8) return json({ result: 'error', error: 'Nouveau mot de passe : 8 caractères minimum.' }, 400);

  const row = await db.prepare('SELECT pass_hash, pass_salt FROM aff_affiliates WHERE id = ?')
    .bind(aff.affiliate_id).first();
  if (!row || !row.pass_hash) return json({ result: 'error', error: 'Aucun mot de passe défini.' }, 400);
  const h = await hashPassword(cur, row.pass_salt);
  if (h !== row.pass_hash) return json({ result: 'error', error: 'Mot de passe actuel incorrect.' }, 401);

  const salt = makeSalt();
  const hash = await hashPassword(pw, salt);
  await db.prepare('UPDATE aff_affiliates SET pass_hash = ?, pass_salt = ? WHERE id = ?')
    .bind(hash, salt, aff.affiliate_id).run();
  return json({ result: 'success' });
}
