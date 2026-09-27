// POST /api/aff/logout
import { json, readSessionToken, clearCookie } from './lib.js';

export async function onRequestPost({ request, env }) {
  const db = env.AFF_DB;
  const token = readSessionToken(request);
  if (db && token) {
    try { await db.prepare('DELETE FROM aff_sessions WHERE token = ?').bind(token).run(); }
    catch (e) { /* best effort */ }
  }
  return json({ result: 'success' }, 200, { 'Set-Cookie': clearCookie() });
}
