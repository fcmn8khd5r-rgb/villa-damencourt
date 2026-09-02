#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rapatrie les photos du site et les dérive en plusieurs largeurs.

Elles étaient chargées chez Unsplash à chaque visite. Mesuré sur la seule
page d'accueil : neuf requêtes, 2 Mo, des fichiers à 550 Ko mettant jusqu'à
2,3 secondes. Un site de démonstration ouvert depuis un téléphone en
déplacement n'a aucune chance dans ces conditions — et il dépend d'un tiers
qui peut ralentir, limiter ou disparaître.

On télécharge donc une fois, à bonne résolution, puis on dérive en AVIF et
WebP à quatre largeurs, comme pour les autres sites. La licence Unsplash
n'exige pas l'attribution ; elle est conservée dans le manifeste et affichée
sur le site, par correction.

    python3 src/rapatrier.py
"""
import base64, io, json, os, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = json.load(open(os.path.join(RACINE, "src/images-source.json"), encoding="utf-8"))
DOSSIER = os.path.join(RACINE, "assets", "img")
MANIFESTE = os.path.join(RACINE, "src", "manifeste-images.json")
ORIGINAUX = os.path.join(RACINE, "src", "orig")

LARGEURS = [480, 800, 1280, 1920]
Q_AVIF, Q_WEBP = 58, 80
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def telecharger(ident, vers):
    """Une seule fois, à 2400 px : assez pour toutes les dérivées."""
    if os.path.exists(vers):
        return
    url = ("https://images.unsplash.com/%s?auto=format&fit=crop&w=2400&q=85" % ident)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        io.open(vers, "wb").write(r.read())


def main():
    from PIL import Image
    os.makedirs(DOSSIER, exist_ok=True)
    os.makedirs(ORIGINAUX, exist_ok=True)
    man = json.load(open(MANIFESTE, encoding="utf-8")) if os.path.exists(MANIFESTE) else {}

    cles = [k for k in SRC if not k.startswith("_")]
    for i, cle in enumerate(sorted(cles), 1):
        info = SRC[cle]
        brut = os.path.join(ORIGINAUX, cle + ".jpg")
        telecharger(info["id"], brut)
        im = Image.open(brut).convert("RGB")

        # On recadre au rapport de forme voulu par la page : le fichier
        # d'origine n'a pas la même forme, et laisser le navigateur rogner
        # ferait télécharger des pixels jamais montrés.
        a, b = (float(x) for x in info["forme"].split("/"))
        cible = a / b
        if abs(im.width / im.height - cible) > 0.01:
            if im.width / im.height > cible:
                w = round(im.height * cible); x = (im.width - w) // 2
                im = im.crop((x, 0, x + w, im.height))
            else:
                h = round(im.width / cible); y = (im.height - h) // 2
                im = im.crop((0, y, im.width, y + h))

        variantes = {}
        for l in sorted({min(x, im.width) for x in LARGEURS} | {im.width}):
            h = max(1, round(im.height * l / im.width))
            p = im if l == im.width else im.resize((l, h), Image.LANCZOS)
            for ext, fmt, q in (("avif", "AVIF", Q_AVIF), ("webp", "WEBP", Q_WEBP)):
                chemin = os.path.join(DOSSIER, "%s-%d.%s" % (cle, l, ext))
                if not os.path.exists(chemin):
                    if fmt == "WEBP":
                        p.save(chemin, fmt, quality=q, method=6)
                    else:
                        p.save(chemin, fmt, quality=q)
                variantes.setdefault(str(l), {})[ext] = os.path.getsize(chemin)

        t = io.BytesIO()
        im.resize((16, max(1, round(16 * im.height / im.width)))).save(t, "WEBP", quality=45)
        man[cle] = {"l": im.width, "h": im.height, "forme": info["forme"],
                    "alt": info["alt"], "credit": info["credit"], "profil": info["profil"],
                    "variantes": variantes,
                    "attente": "data:image/webp;base64," + base64.b64encode(t.getvalue()).decode()}
        print("  %2d/%d  %-15s %4dx%-4d  %s" % (i, len(cles), cle, im.width, im.height,
              " ".join("%d:%dKo" % (int(l), v["avif"] // 1024)
                       for l, v in sorted(variantes.items(), key=lambda x: int(x[0])))), flush=True)

    json.dump(man, open(MANIFESTE, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, sort_keys=True)
    petites = sum(v["variantes"][min(v["variantes"], key=int)]["avif"] for v in man.values())
    print("\n%d images. Un téléphone recevrait au plus %.1f Mo pour la totalité du site."
          % (len(man), petites / 1e6))


if __name__ == "__main__":
    main()
