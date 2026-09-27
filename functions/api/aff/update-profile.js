// POST /api/aff/update-profile — editable fields: telephone, plateforme, pseudo, abonnes.
import { json, getAffiliate, validDzPhone, publicProfile } from './lib.js';

export async function onRequestPost({ request, env }) {
  const db = env.AFF_DB;
  if (!db) return json({ result: 'error', error: 'Base de données indisponible.' }, 500);
  const aff = await getAffiliate(db, request);
  if (!aff) return json({ result: 'error', error: 'Non connecté.' }, 401);

  let b;
  try { b = await request.json(); }
  catch (e) { return json({ result: 'error', error: 'Requête invalide.' }, 400); }
  const telephone = String(b.telephone || '').replace(/[\s.\-]/g, '');
  const plateforme = String(b.plateforme || '').trim();
  const pseudo = String(b.pseudo || '').trim();
  const abonnes = String(b.abonnes || '').trim();

  if (!validDzPhone(telephone)) return json({ result: 'error', error: 'Numéro algérien invalide.' }, 400);
  if (!plateforme) return json({ result: 'error', error: 'Plateforme requise.' }, 400);
  if (pseudo.length < 2) return json({ result: 'error', error: 'Pseudo requis.' }, 400);

  await db.prepare('UPDATE aff_affiliates SET telephone = ?, plateforme = ?, pseudo = ?, abonnes = ? WHERE id = ?')
    .bind(telephone, plateforme, pseudo, abonnes, aff.affiliate_id).run();
  const row = await db.prepare('SELECT * FROM aff_affiliates WHERE id = ?').bind(aff.affiliate_id).first();
  return json({ result: 'success', affiliate: publicProfile(row) });
}
