/**
 * Fresh HTML for the homepage.
 *
 * The zone-level Browser Cache TTL (4h) overrides the `_headers` no-store
 * rule for the static `/` document. After a deploy, Cloudflare's edge kept
 * serving the previous landing page (Black Friday) while `/index.html?v=...`
 * was already fresh.
 *
 * This middleware runs only for `/` and `/index.html` (GET/HEAD):
 *  - fetches the current index through a unique query string so the fetch
 *    cannot hit the stale cached copy;
 *  - returns it with no-store / no-cache headers.
 *
 * Non-HTML requests and the internal fresh fetch pass straight through.
 */
export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  const isRoot = url.pathname === '/' || url.pathname === '/index.html';
  const isDental = url.pathname === '/dental/' || url.pathname === '/dental/index.html';
  const isRead = request.method === 'GET' || request.method === 'HEAD';

  if ((!isRoot && !isDental) || !isRead || url.searchParams.has('__cx_fresh')) {
    return context.next();
  }

  let response;
  try {
    const freshUrl = new URL(isDental ? '/dental/' : '/', url.origin);
    freshUrl.searchParams.set('__cx_fresh', String(Date.now()));
    response = await fetch(freshUrl.toString(), {
      method: 'GET',
      headers: { 'Cache-Control': 'no-cache' },
      cf: { cacheTtl: 0, cacheEverything: false },
    });
  } catch {
    response = await context.next();
  }

  if (!response || !response.ok) {
    return context.next();
  }

  const headers = new Headers(response.headers);
  headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
  headers.set('CDN-Cache-Control', 'no-store');
  headers.set('Pragma', 'no-cache');
  headers.set('Expires', '0');
  headers.set('X-CX-Fresh', '1');

  return new Response(request.method === 'HEAD' ? null : response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
