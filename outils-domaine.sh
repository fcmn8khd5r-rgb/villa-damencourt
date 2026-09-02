#!/bin/bash
# =============================================================================
# Substitue le domaine réel du site au domaine d'attente, à la construction.
#
# Les pages portent une adresse canonique, des variantes hreflang et des
# balises de partage — toutes absolues, car ces informations n'ont aucun sens
# en relatif. Le générateur y inscrit un domaine d'attente, faute de savoir où
# le site sera publié.
#
# Netlify, lui, le sait : il expose l'adresse du site dans $URL au moment de
# construire. On la substitue donc ici. Conséquence utile : on peut renommer
# le site, changer de domaine ou en créer un second sans rien retoucher dans
# le dépôt — l'adresse suit toute seule.
#
# Sans cette substitution, chaque page déclarerait aux moteurs que sa vraie
# adresse se trouve ailleurs, sur un domaine qui n'existe pas. C'est le défaut
# que portaient Villa Lakou et Kaz Lanmè, et qu'on ne voit jamais en local.
# =============================================================================
set -e
cd "$(dirname "$0")"

python3 - "${URL:-}" "${DEPLOY_PRIME_URL:-}" <<'PY'
import glob, os, sys

ATTENTE = "https://villa-damencourt.example"
reel = (sys.argv[1] or sys.argv[2] or "").rstrip("/")

if not reel:
    print("  domaine : %s conservé (l'hébergeur n'a fourni aucune adresse)" % ATTENTE)
    raise SystemExit

n = 0
for f in glob.glob("*.html") + glob.glob("en/*.html") + ["robots.txt"]:
    if not os.path.exists(f):
        continue
    s = open(f, encoding="utf-8").read()
    if ATTENTE in s:
        open(f, "w", encoding="utf-8").write(s.replace(ATTENTE, reel))
        n += 1
print("  domaine : %s -> %s (%d fichiers)" % (ATTENTE, reel, n))
PY
