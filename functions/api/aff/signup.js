// POST /api/aff/signup — create an affiliate account (step 1: identity).
import { json, validEmail, validDzPhone, cleanCode, genCode, createSession, sessionCookie, gasSignup, publicProfile } from './lib.js';

export async function onRequestPost({ request, env }) {
  const db = env.AFF_DB;
  if (!db) return json({ result: 'error', error: 'Base de données indisponible.' }, 500);
  let b;
  try { b = await request.json(); }
  catch (e) { return json({ result: 'error', error: 'Requête invalide.' }, 400); }

  const nom = String(b.nom || '').trim();
  const telephone = String(b.telephone || '').replace(/[\s.\-]/g, '');
  const plateforme = String(b.plateforme || '').trim();
  const pseudo = String(b.pseudo || '').trim();
  const abonnes = String(b.abonnes || '').trim();
  const email = String(b.email || '').trim().toLowerCase();
  const want = cleanCode(b.code_souhaite).slice(0, 20);

  if (nom.length < 3) return json({ result: 'error', error: 'Nom incomplet.' }, 400);
  if (!validDzPhone(telephone)) return json({ result: 'error', error: 'Numéro algérien invalide (05/06/07).' }, 400);
  if (!plateforme) return json({ result: 'error', error: 'Plateforme requise.' }, 400);
  if (pseudo.length < 2) return json({ result: 'error', error: 'Pseudo requis.' }, 400);
  if (!validEmail(email)) return json({ result: 'error', error: 'Email invalide.' }, 400);

  const emailTaken = await db.prepare('SELECT id FROM aff_affiliates WHERE email = ?').bind(email).first();
  if (emailTaken) return json({ result: 'error', error: 'Cet email a déjà un compte affilié.' }, 409);

  let code = want || genCode(nom);
  for (let i = 0; i < 25; i++) {
    const taken = await db.prepare('SELECT id FROM aff_affiliates WHERE code = ?').bind(code).first();
    if (!taken) break;
    code = (want || genCode(nom)) + '-' + (i + 2);
  }

  const r = await db.prepare(
    'INSERT INTO aff_affiliates (code, nom, telephone, plateforme, pseudo, abonnes, email) VALUES (?,?,?,?,?,?,?)'
  ).bind(code, nom, telephone, plateforme, pseudo, abonnes, email).run();
  const id = r.meta.last_row_id;

  // Dual-write to the Sheet (back-office). Adopt the final code if deduped there.
  const aff = { nom, telephone, plateforme, pseudo, abonnes, email, code };
  const sheetCode = await gasSignup(aff);
  if (sheetCode && sheetCode !== code) {
    await db.prepare('UPDATE aff_affiliates SET code = ? WHERE id = ?').bind(sheetCode, id).run();
    aff.code = sheetCode;
  }
  await db.prepare('UPDATE aff_affiliates SET sheet_ok = ? WHERE id = ?').bind(sheetCode ? 1 : 0, id).run();

  const token = await createSession(db, id);
  const row = await db.prepare('SELECT * FROM aff_affiliates WHERE id = ?').bind(id).first();
  return json({ result: 'success', affiliate: publicProfile(row) },
    200, { 'Set-Cookie': sessionCookie(token) });
}
