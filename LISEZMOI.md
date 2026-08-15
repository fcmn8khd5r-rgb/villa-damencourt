# Villa Damencourt — site villa, Le Moule (Guadeloupe)

Application monopage bilingue FR/EN, 8 pages, construite sur le runtime
`dc-runtime` de Claude Design.

## Fichiers

| Fichier | Rôle |
|---|---|
| `Villa Damencourt.dc.html` | Le site entier : gabarit + logique + contenus |
| `support.js` | Runtime dc (généré — **ne pas modifier**) |
| `image-slot.js` | Composant d'image déposable (starter — réécrasable) |

## Voir le site

```bash
python3 -m http.server 8140
```

puis ouvrir <http://localhost:8140/Villa%20Damencourt.dc.html>.
Le nom de fichier doit conserver son extension `.dc.html` : le runtime s'en sert
pour s'amorcer. React est chargé automatiquement depuis unpkg.

## Corrections apportées

**Accessibilité**
- Les 10 photos ont un nom accessible (`role="img"` + `aria-label`).
  Le composant `image-slot` code `alt=""` en dur et n'expose pas d'attribut
  `alt` : nommer l'hôte est la seule façon d'y arriver sans toucher au starter.
- Les 4 boutons symboliques (‹ › × ×) sont nommés, dans les deux langues.
- `<html lang>` suit désormais la bascule FR/EN. Sans cela un lecteur d'écran
  prononçait le français avec une voix anglaise.
- Lien d'évitement et styles de focus clavier (il n'y en avait aucun).

**Formulaire de réservation**
- Vraie balise `<form>` : la touche Entrée valide, l'envoi natif est intercepté.
- `required`, `autocomplete`, validation de l'email par motif.
- Message d'erreur **sous le champ fautif** et focus placé dessus,
  au lieu d'un message global.

**Requêtes 404**
Le gabarit vit dans le DOM avant que le runtime ne le remplace : le navigateur
chargeait donc `{{ g.src }}` comme une URL, d'où une dizaine de 404 à chaque
visite. Les URL ont quitté les attributs ; elles sont posées après le montage
(`poseur` / `poseurVideo` dans le script). `image-slot` observe `src`, il réagit
normalement à cette pose tardive.

**Photographies**
Les cartes de « La région » et « Le journal » montraient des piscines de villa
quelle que soit leur légende. Douze photos ont été remplacées pour correspondre
au texte : lagon, surf, falaise, pointe, coucher de soleil, kite, persiennes,
mangues, jardin créole, distillerie, carnaval.

## À savoir

- Les photos viennent d'Unsplash, créditées par pseudonyme avec lien vers le
  profil. `image-slot` refuse d'afficher une photo Unsplash sans crédit.
- La requête vers `.image-slots.state.json` renvoie 404 tant qu'aucune image
  n'a été déposée à la main : c'est le fonctionnement prévu, pas un défaut.
