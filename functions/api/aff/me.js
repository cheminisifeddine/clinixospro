// GET /api/aff/me — current session profile.
import { json, getAffiliate, publicProfile } from './lib.js';

export async function onRequestGet({ request, env }) {
  const db = env.AFF_DB;
  if (!db) return json({ result: 'error', error: 'Base de données indisponible.' }, 500);
  const aff = await getAffiliate(db, request);
  if (!aff) return json({ result: 'error', error: 'Non connecté.' }, 401);
  return json({ result: 'success', affiliate: publicProfile(aff) });
}
