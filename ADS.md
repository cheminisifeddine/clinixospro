# ClinixOS Pro — Meta Ads playbook (cold traffic, Algeria)

Objectif : **commandes COD à 9 900 DA**, CPA bas, trafic froid Facebook/Instagram.
Le site est optimisé pour la conversion, pas pour le SEO. Les balises SEO restent en place, mais la copie visible parle au médecin, pas à Google.

---

## 1. Funnel

```
Ad Meta (cold) → Landing page → formulaire (Lead) → appel de confirmation → livraison → paiement 9 900 DA (Purchase)
```

Événements Pixel déjà en place :

| Événement | Déclencheur | Utilité |
|---|---|---|
| `PageView` | arrivée sur la page | mesure |
| `InitiateCheckout` | premier focus dans le formulaire | intention |
| `Lead` | soumission du formulaire | optimisation principale au début |
| `Purchase` | page `merci.html` après succès serveur | optimisation quand volume suffisant |

**Recommandation :** commencez avec `Lead` comme événement d'optimisation. Passez à `Purchase` quand vous avez **50 Purchase/semaine** (sinon l'algorithme n'a pas assez de signal). Ajoutez la **Conversions API** côté serveur si possible (Apps Script → événement `Purchase` avec `event_id`).

---

## 2. Structure de campagne (Advantage+ / Andromeda)

- **1 campagne** Advantage+ Sales (ou Conversions).
- **1 ad set large** : Algérie, 25–60 ans, français, Advantage+ placements.
- **Pas d'empilement d'intérêts** au départ : Andromeda trouve l'audience à partir du créatif. Testez séparément un ad set « Médecins » (intérêt) pour comparer, mais ne bloquez pas la diffusion.
- **3 à 5 créatifs par ad set**, même angle, hooks différents.
- **Budget de test** : 3 000–5 000 DZD/jour, 3–5 jours minimum. Ne coupez pas après 24 h.
- **Exclusions** : clients existants (liste WhatsApp/Sheet), visiteurs de `merci.html` des 30 derniers jours.
- **Objectif** : Lead d'abord, Purchase ensuite. Le CPA cible doit être défini selon votre marge : (prix − coût produit/livraison − coût appel) × taux de livraison.

---

## 3. Angle de communication

Le médecin ne achète pas « un logiciel ». Il achète :

1. **Du temps** — retrouver un dossier en 1 clic, imprimer une ordonnance en 5 secondes.
2. **La tranquillité** — pas de panne Internet, pas de cloud, pas d'abonnement.
3. **Le contrôle** — ses données restent au cabinet, sa licence lui appartient.

La page répète ces trois promesses, avec une seule action : **commander la clé USB, payer à la livraison**.

---

## 4. Créatifs : 3 hooks à tester

### Hook A — Douleur (le plus large)
> **« Médecin en Algérie : combien d'heures par jour perdez-vous à chercher des dossiers ? »**
>
> Dossiers papier, ordonnances manuscrites, salle d'attente qui déborde… ClinixOS Pro remet votre cabinet en ordre en 10 minutes. 100 % hors-ligne, licence à vie, 9 900 DA. Livraison 58 wilayas, payez à la réception.

**Visuel :** écran réel du logiciel, recherche d'un patient, ordonnance A5 qui s'imprime. 15–25 s, vertical 9:16, sous-titres.

### Hook B — Internet / cloud
> **« Votre logiciel s'arrête quand la 4G coupe. Pas ClinixOS Pro. »**
>
> Dossiers, ordonnances, salle d'attente, caisse : tout fonctionne en local, sans Internet. Licence à vie, 2 postes, 9 900 DA une seule fois. Garantie 7 jours. Paiement à la livraison.

**Visuel :** médecin qui débranche le wifi / coupe la 4G, continue à travailler, ordonnance imprimée. Fin : « 100 % hors-ligne ».

### Hook C — Coût / abonnement
> **« Arrêtez de payer chaque mois pour un logiciel qui vous ralentit. »**
>
> ClinixOS Pro : 9 900 DA une seule fois, licence à vie, zéro abonnement. Installation en 2 clics, données dans votre cabinet. Livraison 58 wilayas, paiement à la livraison, garantie 7 jours.

**Visuel :** split screen « abonnement mensuel » vs « 9 900 DA une fois » + captures réelles.

### Hook D — Preuve / démo (retargeting)
> **« Regardez le logiciel en action — pas une maquette. »**
>
> 94 secondes de démo réelle : patients, ordonnances A5, salle d'attente, caisse. Licence à vie 9 900 DA, payez à la livraison.

**Visuel :** extrait de la vidéo de démo, 20 s, sous-titres.

---

## 5. Textes prêts à copier

### Version courte (feed)
> Médecin en Algérie ? Dossiers patients, ordonnances A5, salle d'attente et caisse dans un seul logiciel. 100 % hors-ligne, licence à vie, 9 900 DA. Livraison 58 wilayas. Payez à la livraison. Garantie 7 jours.

**Headline :** Logiciel cabinet médical — 9 900 DA
**Description :** 100 % hors-ligne · 2 postes · Paiement à la livraison
**CTA :** En savoir plus

### Version douleur
> Vos dossiers vous prennent 5 heures par jour ? ClinixOS Pro les retrouve en 1 clic. Ordonnances A5 en 5 secondes. Fonctionne sans Internet. 9 900 DA une seule fois, livraison incluse, payez à la réception.

**Headline :** Votre cabinet en ordre en 10 minutes
**Description :** Licence à vie · 58 wilayas · Garantie 7 jours

### Version offre
> Le pack complet : clé USB + licence à vie + 2 postes + livraison 58 wilayas. 9 900 DA une seule fois. Pas d'abonnement. Vous vérifiez le colis avant de payer.

**Headline :** 9 900 DA — payez à la livraison
**Description :** Windows & Mac · Installation 2 clics · Garantie 7 jours

### Version retargeting
> Vous hésitez encore ? Testez ClinixOS Pro pendant 7 jours dans votre cabinet. Si ça ne vous convient pas, on vous rembourse les 9 900 DA. Paiement à la livraison, sans engagement.

**Headline :** Garantie 7 jours — testez chez vous
**Description :** Livraison 58 wilayas · Assistance WhatsApp

---

## 6. Créatifs : règles de production

- **Format :** 9:16 (Reels/Stories) + 4:5 (feed). 15–30 s.
- **3 premières secondes :** le hook à l'écran + à l'oral. Pas de logo au début.
- **Sous-titres** obligatoires (85 % regardent sans son).
- **Montrez le vrai logiciel** : recherche patient, ordonnance A5, file d'attente, caisse. Les captures réelles convertissent mieux que les illustrations.
- **Voix :** français simple, ton confrère, pas de jargon marketing.
- **Fin :** « 9 900 DA — payez à la livraison — garantie 7 jours » + logo.
- **À éviter :** fausses urgences, faux témoignages, « garanti 100 % », promesses médicales, images avant/après de patients, stock photos de médecins génériques.

---

## 7. Landing page : ce qui a été optimisé

- H1 mobile court : « Médecin en Algérie ? Votre cabinet, en ordre en 10 minutes. »
- Prix + CTA **au-dessus de la ligne de flottaison** sur mobile.
- CTA « Commander » toujours visible dans le header mobile.
- Formulaire réduit à **5 champs** : nom, téléphone, wilaya, commune, adresse.
- Suppression du compte à rebours et du poste supplémentaire ; migration proposée séparément sur devis. **Total du logiciel : 9 900 DA.**
- Ancien prix 35 000 DA expliqué honnêtement : version agence avec technicien vs version clé USB auto-installation. Pas de « offre à durée limitée ».
- Section témoignages prête : ajoutez uniquement de **vrais** avis dans `window.CX_TESTIMONIALS` (dans `index.html`). La section s'affiche automatiquement dès qu'il y a au moins un avis.
- Pages légales : `legal.html` (mentions, confidentialité, CGV, remboursement).
- Cache HTML corrigé : `Cache-Control: no-store` pour que les mobiles ne gardent pas l'ancienne version 4 heures.
- UTM/fbclid capturés dans le formulaire pour attribuer les commandes.

### URL à utiliser dans les ads

```
https://clinixospro.com/?utm_source=facebook&utm_medium=paid&utm_campaign=cold_medecins_dz&utm_content=hook_a&utm_term=advplus
```

Meta ajoute automatiquement `fbclid`. Le paramètre UTM force aussi un nouveau cache navigateur, donc vos visiteurs ne revoient pas l'ancienne page.

---

## 8. Plan de test (7 jours)

| Jour | Action |
|---|---|
| J1 | Lancer 1 campagne, 1 ad set large, 3 créatifs (A, B, C), budget 3 000–5 000 DZD/j |
| J2–J4 | Ne rien couper. Regarder hook rate (3 s), CTR, coût par Lead |
| J5 | Couper le créatif avec le coût par Lead le plus élevé ; garder les 2 meilleurs |
| J6 | Ajouter 2 variantes du meilleur hook (même angle, nouveau visuel) |
| J7 | Si CPA acceptable, dupliquer l'ad set gagnant et augmenter le budget de 20–30 %/jour |

**KPI à suivre :** CTR (objectif > 1,5 %), coût par Lead, taux de confirmation téléphonique, taux de livraison, CPA final. Le CPA final dépend de votre taux de confirmation : un Lead à 500 DZD avec 50 % de confirmation coûte 1 000 DZD par commande confirmée.

---

## 9. Social proof : mode d'emploi

La section témoignages est déjà codée dans `index.html` :

```js
window.CX_TESTIMONIALS = [
  // { quote: "J'ai retrouvé 2 heures par jour...", name: "Dr. A. B.", role: "Médecin généraliste", city: "Alger", initials: "AB" }
];
```

Envoyez-moi 3 à 6 vrais témoignages (nom, spécialité, wilaya, citation) et je les ajoute. **Ne mettez jamais de faux avis** : c'est illégal, contraire aux règles Meta, et les médecins le repèrent immédiatement.

En attendant, la page s'appuie sur des preuves vérifiables : captures réelles, démo vidéo, 58 wilayas, paiement après inspection, garantie 7 jours, licence à vie, 2 postes inclus, assistance WhatsApp.

---

## Contact policy for ads

- Landing page and footer show **WhatsApp only**: +213 558 495 780.
- No public phone number: avoids inbound support calls and keeps the team focused on order confirmation.
- **0770 49 49 50** is used only for **outbound confirmation calls**; never put it in the ad copy or landing page.
- In ads, use “Commandez en ligne / paiement à la livraison” and send people to the form or WhatsApp — not to a phone call.

## Migration (upsell séparé)

- Migration des anciens dossiers (EasyDoc, Daoini, Excel…) : **service payant sur devis**.
- Elle reste **séparée** du pack à 9 900 DA : le total du formulaire et la valeur `Purchase` restent **9900 DZD**.
- Angle retargeting : « Vous avez déjà EasyDoc/Daoini/Excel ? On migre vos dossiers. Demandez un devis. »
- Ne pas mettre la migration dans le prix du logiciel ni dans l'événement Purchase.
