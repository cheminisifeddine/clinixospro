// POST /api/aff/payout — save payout details (CCP/RIP + holder). Synced to the Sheet.
import { json, getAffiliate, gasSetPaiement, publicProfile } from './lib.js';

const TYPES = ['CCP', 'BaridiMob', 'Virement bancaire'];

export async function onRequestPost({ request, env }) {
  const db = env.AFF_DB;
  if (!db) return json({ result: 'error', error: 'Base de données indisponible.' }, 500);
  const aff = await getAffiliate(db, request);
  if (!aff) return json({ result: 'error', error: 'Non connecté.' }, 401);

  let b;
  try { b = await request.json(); }
  catch (e) { return json({ result: 'error', error: 'Requête invalide.' }, 400); }
  const type = String(b.paiement_type || '').trim();
  const num = String(b.paiement_num || '').replace(/[\s.\-]/g, '');
  const titulaire = String(b.titulaire || '').trim();

  if (TYPES.indexOf(type) < 0) return json({ result: 'error', error: 'Moyen de paiement invalide.' }, 400);
  if (num.length < 5) return json({ result: 'error', error: 'Numéro de compte invalide.' }, 400);
  if (titulaire.length < 3) return json({ result: 'error', error: 'Titulaire du compte requis.' }, 400);

  // Sheet first: Oussama's payouts read the Sheet. Don't save anywhere if it fails.
  const ok = await gasSetPaiement(aff.code, type + ' ' + String(b.paiement_num || '').trim(), titulaire);
  if (!ok) return json({ result: 'error', error: 'Enregistrement impossible pour le moment — réessayez.' }, 502);

  await db.prepare('UPDATE aff_affiliates SET paiement_type = ?, paiement_num = ?, titulaire = ? WHERE id = ?')
    .bind(type, String(b.paiement_num || '').trim(), titulaire, aff.affiliate_id).run();
  const row = await db.prepare('SELECT * FROM aff_affiliates WHERE id = ?').bind(aff.affiliate_id).first();
  return json({ result: 'success', affiliate: publicProfile(row) });
}
