/**
 * Branded download route:
 * /downloads/ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe?lead=123
 *
 * The installer is hosted as a public GitHub release asset. This route:
 *  - only serves the expected filename;
 *  - marks downloaded_at for the lead;
 *  - streams from an optional R2 binding when available;
 *  - otherwise redirects to the public installer (Content-Disposition attachment
 *    is set by GitHub on the final asset response).
 */
const FILE_NAME = 'ClinixOS-Essai-7Jours-Setup-Universal-3.5.2.exe';
const GITHUB_URL = 'https://github.com/cheminisifeddine/clinixospro/releases/download/essai-3.5.2/' + FILE_NAME;
const FALLBACK_URL = 'https://gofile.io/d/GsM2Xlqw';

export async function onRequestGet({ request, env, params }) {
  if (params.file !== FILE_NAME) {
    return new Response('Fichier introuvable.', { status: 404 });
  }

  const url = new URL(request.url);
  const lead = url.searchParams.get('lead');

  if (lead && /^\d+$/.test(lead) && env.AFF_DB) {
    try {
      await env.AFF_DB.prepare('UPDATE trial_leads SET downloaded_at = ? WHERE id = ? AND downloaded_at IS NULL')
        .bind(new Date().toISOString(), Number(lead)).run();
    } catch (e) {
      // Never block the download because analytics or DB update failed.
    }
  }

  // Preferred: an R2 binding with the real file, served with an attachment header.
  if (env.TRIAL_R2) {
    try {
      const object = await env.TRIAL_R2.get(FILE_NAME);
      if (object) {
        return new Response(object.body, {
          status: 200,
          headers: {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment; filename="' + FILE_NAME + '"',
            'Content-Length': String(object.size),
            'Cache-Control': 'no-store',
            'X-Content-Type-Options': 'nosniff',
          },
        });
      }
    } catch (e) {
      // Fall through to the public release asset.
    }
  }

  const target = env.TRIAL_DOWNLOAD_URL || GITHUB_URL;
  return new Response(null, {
    status: 302,
    headers: {
      Location: target || FALLBACK_URL,
      'Cache-Control': 'no-store',
      'X-Robots-Tag': 'noindex',
    },
  });
}

export async function onRequestHead(context) {
  return onRequestGet(context);
}
