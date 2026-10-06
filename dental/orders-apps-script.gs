// ─── ClinixOS Dental — réception des commandes (Google Sheet dédié) ─────────
// Ce script écrit chaque commande du landing https://clinixospro.com/dental/
// dans une feuille Google Sheet SÉPARÉE ("ClinixOS Dental — Commandes"),
// pour ne jamais mélanger avec les commandes ClinixOS Pro.
//
// INSTALLATION (5 min, compte Google d'Oussama) :
//  1. Ouvrez https://script.new (connecté à votre compte Google)
//  2. Supprimez le code d'exemple, collez tout ce fichier
//  3. Déployer > Nouveau déploiement > type "Application Web"
//       - Exécuter en tant que : Moi
//       - Qui a accès : TOUS LES UTILISATEURS  ← critique, sinon les
//         commandes des visiteurs sont rejetées (403) et perdues
//  4. Autorisez l'accès quand Google le demande (Drive + Sheets)
//  5. Copiez l'URL qui se termine par /exec et transmettez-la pour
//     brancher le formulaire du landing page.
//
// La feuille est créée AUTOMATIQUEMENT (avec les en-têtes) à la première
// commande reçue. Rien d'autre à créer à la main.
//
// v2 (2026-10-05) — IDEMPOTENCE : le relais echo de Google
// (script.googleusercontent.com) renvoie parfois une page d'erreur HTML
// alors que la commande EST déjà enregistrée. Le formulaire réessaie alors
// avec le même submission_id ; ce script ignore le doublon grâce à la
// colonne "Submission ID" + un verrou (LockService). Sans ça, un réessai
// créerait 2 lignes pour la même commande.

var SHEET_NAME = 'ClinixOS Dental — Commandes';
var HEADERS = [
  'Date', 'Nom', 'Téléphone', 'Téléphone 2',
  'Wilaya', 'Commune', 'Adresse', 'Spécialité',
  'Produit', 'Formule', 'Prix (DA)', 'Paiement', 'Transporteur',
  'Code promo', 'Statut', 'Submission ID'
];

function getSheet() {
  var it = DriveApp.getFilesByName(SHEET_NAME);
  var ss = it.hasNext() ? SpreadsheetApp.open(it.next()) : SpreadsheetApp.create(SHEET_NAME);
  var sh = ss.getSheets()[0];
  if (sh.getLastRow() === 0) {
    sh.appendRow(HEADERS);
  } else if (sh.getRange('P1').getValue() !== 'Submission ID') {
    sh.getRange('P1').setValue('Submission ID');
  }
  return sh;
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var p = (e && e.parameter) || {};
  // Verrou anti-doublon : deux exécutions concurrentes du même réessai
  // ne peuvent pas passer le contrôle ci-dessous en même temps.
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sh = getSheet();
    var sid = String(p.submission_id || '');
    if (sid) {
      var last = sh.getLastRow();
      if (last > 1) {
        var ids = sh.getRange('P2:P' + last).getValues();
        for (var i = 0; i < ids.length; i++) {
          if (ids[i][0] === sid) {
            return json({ result: 'success', deduped: true });
          }
        }
      }
    }
    sh.appendRow([
      new Date(),
      p.name || '',
      // Apostrophe = stockage texte forcé : garde le 0 initial des numéros.
      // (setNumberFormat seul ne suffit pas, et formater 2 colonnes entières
      // à chaque commande ralentissait l'exécution.)
      (p.phone ? "'" + p.phone : ''),
      (p.phone2 ? "'" + p.phone2 : ''),
      p.wilaya || '',
      p.city || '',
      p.address || '',
      p.specialty || '',
      p.product || '',
      p.tier || '',
      p.price || '',
      p.payment || '',
      p.carrier || '',
      p.promo_code || '',
      'Nouveau',
      sid
    ]);
    return json({ result: 'success' });
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return json({ result: 'success', service: 'clinixos-dental-orders' });
}
