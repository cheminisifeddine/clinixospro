// GET /api/aff/stats — profile + live stats (proxied from the Sheet via Apps Script).
import { json, getAffiliate, publicProfile, gasStats, personalUrl } from './lib.js';

export async function onRequestGet({ request, env }) {
  const db = env.AFF_DB;
  if (!db) return json({ result: 'error', error: 'Base de données indisponible.' }, 500);
  const aff = await getAffiliate(db, request);
  if (!aff) return json({ result: 'error', error: 'Non connecté.' }, 401);

  let stats = null;
  try {
    const d = await gasStats(aff.code);
    if (d && d.result === 'success') stats = d;
  } catch (e) { /* fall through to degraded response */ }

  if (!stats) {
    return json({
      result: 'success', degraded: true,
      affiliate: publicProfile(aff), personal_url: personalUrl(aff.code),
      stats: { clicks_30d: 0, orders: 0, delivered: 0, commission_earned: 0,
               commission_pending: 0, commission_paid: 0, recent: [] },
    });
  }
  return json({
    result: 'success',
    affiliate: publicProfile(aff), personal_url: personalUrl(aff.code),
    stats: {
      clicks_30d: stats.clicks_30d || 0, orders: stats.orders || 0,
      delivered: stats.delivered || 0, commission_earned: stats.commission_earned || 0,
      commission_pending: stats.commission_pending || 0,
      commission_paid: stats.commission_paid || 0, recent: stats.recent || [],
    },
  });
}
