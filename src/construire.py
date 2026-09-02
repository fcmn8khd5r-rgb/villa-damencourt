#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fige le site en pages statiques, à partir du DOM rendu.

Pourquoi une reconstruction. Le site était un document à runtime : il
téléchargeait React, ReactDOM et Babel depuis unpkg, se compilait dans le
navigateur, puis allait chercher ses photos chez Unsplash et sa vidéo chez
Pexels. Mesuré : 3,6 secondes avant le premier mot sur une connexion locale,
2 Mo de photos distantes pour la seule page d'accueil, et une vidéo Full HD
de 13,5 Mo qui n'arrivait jamais. Aucune retouche ne corrige cela — c'est
l'architecture qui est en cause.

Comment. Le design ne vit pas dans une feuille de style — elle ne pèse que
6 Ko — mais dans des styles posés en ligne par React. Le DOM rendu contient
donc l'apparence complète : on l'a capturé page par page, dans les deux
langues, et on le transforme ici en pages autonomes. Rien n'est redessiné,
donc rien ne peut différer.

Ce que la transformation change :
  · <image-slot> devient un <picture> pointant sur les images locales,
    en quatre largeurs, avec la place réservée et une vignette d'attente ;
  · la navigation, qui se faisait en JavaScript sur des href="#", devient
    de vrais liens entre de vraies pages ;
  · la vidéo distante de 13,5 Mo devient deux fichiers locaux, 3,9 Mo et
    1,8 Mo selon la taille de l'écran ;
  · le français vit à la racine, l'anglais sous /en/.

    python3 src/construire.py
"""
import html as H
import json, os, re

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURE = os.path.join(RACINE, "src", "capture")
MAN = json.load(open(os.path.join(RACINE, "src/manifeste-images.json"), encoding="utf-8"))
SRC = json.load(open(os.path.join(RACINE, "src/images-source.json"), encoding="utf-8"))

# Une même photo apparaît sous plusieurs identifiants de slot : la page « la
# villa » réutilise trois vues de la galerie sous les noms hz-col-*. On
# retrouve donc l'image par l'identifiant Unsplash de sa source, et pas
# seulement par celui du slot — sinon trois images restaient non converties.
PAR_PHOTO = {v["id"]: k for k, v in SRC.items() if isinstance(v, dict) and "id" in v}

PAGES = [("index.html", "accueil"), ("la-villa.html", "la-villa"),
         ("chambres.html", "chambres"), ("galerie.html", "galerie"),
         ("sejour.html", "sejour"), ("la-region.html", "la-region"),
         ("journal.html", "journal")]

LIBELLES = {
  "fr": {"Accueil": "index.html", "La villa": "la-villa.html", "Chambres": "chambres.html",
         "Galerie": "galerie.html", "Séjour": "sejour.html", "La région": "la-region.html",
         "Journal": "journal.html", "Villa Damencourt": "index.html"},
  "en": {"Home": "index.html", "The villa": "la-villa.html", "Bedrooms": "chambres.html",
         "Gallery": "galerie.html", "Stay": "sejour.html", "The region": "la-region.html",
         "Journal": "journal.html", "Villa Damencourt": "index.html"},
}

TITRES = {
 "fr": {"index.html": ("Villa Damencourt — location de villa au Moule, Guadeloupe",
        "Case créole contemporaine ouverte sur l'Atlantique, à quatre minutes à pied de la plage de l'Autre Bord. Six chambres climatisées, douze hôtes, une seule location à la fois."),
        "la-villa.html": ("La villa — Villa Damencourt, Le Moule, Guadeloupe",
        "La case créole, ses volumes et sa varangue : six chambres, douze hôtes, une piscine et un jardin ouvert sur l'Atlantique."),
        "chambres.html": ("Chambres — Villa Damencourt, Guadeloupe",
        "Six chambres climatisées pour douze hôtes, toutes avec salle d'eau, dans une case créole du Moule en Grande-Terre."),
        "galerie.html": ("Galerie — Villa Damencourt",
        "La villa en images : la maison, la piscine, le salon ouvert, la grande table et le jardin créole."),
        "sejour.html": ("Séjour — tarifs et disponibilités — Villa Damencourt",
        "Tarifs à la semaine, conditions de location et calendrier des disponibilités de la Villa Damencourt, au Moule."),
        "la-region.html": ("La région — Villa Damencourt, Grande-Terre, Guadeloupe",
        "L'Autre Bord, le lagon, le spot de surf, la Porte d'Enfer : ce qu'il y a à faire autour du Moule, en Grande-Terre."),
        "journal.html": ("Journal — Villa Damencourt",
        "Ce qui se passe à la villa : les travaux, le jardin, la saison des mangues et le carnaval du Moule.")},
 "en": {"index.html": ("Villa Damencourt — villa rental in Le Moule, Guadeloupe",
        "A contemporary creole house open to the Atlantic, four minutes on foot from Autre Bord beach. Six air-conditioned bedrooms, twelve guests, one booking at a time."),
        "la-villa.html": ("The villa — Villa Damencourt, Le Moule, Guadeloupe",
        "The creole house, its volumes and its verandah: six bedrooms, twelve guests, a pool and a garden open to the Atlantic."),
        "chambres.html": ("Bedrooms — Villa Damencourt, Guadeloupe",
        "Six air-conditioned bedrooms for twelve guests, each with its own bathroom, in a creole house in Le Moule, Grande-Terre."),
        "galerie.html": ("Gallery — Villa Damencourt",
        "The villa in pictures: the house, the pool, the open living room, the long table and the creole garden."),
        "sejour.html": ("Stay — rates and availability — Villa Damencourt",
        "Weekly rates, rental conditions and the availability calendar for Villa Damencourt, in Le Moule."),
        "la-region.html": ("The region — Villa Damencourt, Grande-Terre, Guadeloupe",
        "Autre Bord, the lagoon, the surf spot, Porte d'Enfer: what there is to do around Le Moule, in Grande-Terre."),
        "journal.html": ("Journal — Villa Damencourt",
        "What happens at the villa: the works, the garden, mango season and the Le Moule carnival.")},
}


def lien(fichier, lg):
    base = "/" if lg == "fr" else "/en/"
    return base if fichier == "index.html" else base + fichier


def srcset(cle, ext):
    v = MAN[cle]["variantes"]
    return ", ".join("/assets/img/%s-%s.%s %sw" % (cle, l, ext, l) for l in sorted(v, key=int))


def moyenne(cle, ext="webp"):
    v = sorted(MAN[cle]["variantes"], key=int)
    return "/assets/img/%s-%s.%s" % (cle, v[min(1, len(v) - 1)], ext)


ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')


def remplacer_image(m):
    """Un <image-slot> devient un <picture>, à la place exacte."""
    att = dict(ATTR.findall(m.group(1)))
    cle = att.get("id", "")
    if cle not in MAN:
        ident = re.search(r"photo-[0-9a-f-]+", att.get("src", "") or "")
        cle = PAR_PHOTO.get(ident.group(0), "") if ident else ""
    if cle not in MAN:
        return m.group(0)
    f = MAN[cle]
    style = H.unescape(att.get("style", "width:100%"))
    alt = H.unescape(att.get("aria-label", f.get("alt", "")))
    # sizes : ces images occupent au plus la colonne de contenu
    sizes = "(max-width:700px) 100vw, (max-width:1100px) 50vw, 620px"
    return (
      '<div class="hz-img" style="%s">'
      '<picture>'
      '<source type="image/avif" srcset="%s" sizes="%s">'
      '<source type="image/webp" srcset="%s" sizes="%s">'
      '<img src="%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async" '
      'style="background:url(%s) center/cover">'
      '</picture></div>'
      % (H.escape(style, quote=True), srcset(cle, "avif"), sizes,
         srcset(cle, "webp"), sizes, moyenne(cle), H.escape(alt, quote=True),
         f["l"], f["h"], f["attente"]))


def transformer(corps, lg, fichier):
    # 1. les images
    corps = re.sub(r'<image-slot\b(.*?)>\s*</image-slot>', remplacer_image, corps, flags=re.S)

    # 2. la navigation : des href="#" pilotés en JavaScript deviennent de
    #    vrais liens. Une page par adresse, indexable, partageable.
    def nav(m):
        avant, texte = m.group(1), m.group(2)
        cible = LIBELLES[lg].get(texte.strip())
        if not cible:
            return m.group(0)
        return '<a%shref="%s"%s><span class="sc-interp">%s</span></a>' % (
            m.group("pre1"), lien(cible, lg), m.group("pre2"), texte)
    corps = re.sub(
        r'<a(?P<pre1>[^>]*?)href="#"(?P<pre2>[^>]*?)><span class="sc-interp">([^<]+)</span></a>',
        lambda m: '<a%shref="%s"%s><span class="sc-interp">%s</span></a>' % (
            m.group("pre1"), lien(LIBELLES[lg].get(m.group(3).strip(), "index.html"), lg),
            m.group("pre2"), m.group(3)),
        corps)

    # 3. la bascule de langue : un bouton piloté par React devient un lien.
    #    Un lien s'ouvre dans un nouvel onglet, se partage, et fonctionne sans
    #    JavaScript — ce qu'un bouton ne fait pas.
    autre = "en" if lg == "fr" else "fr"
    def langue(m):
        return ('<a href="%s" hreflang="%s" lang="%s"%s>%s</a>'
                % (lien(fichier, autre), autre, autre, m.group(1), m.group(2)))
    corps = re.sub(
        r'<button[^>]*aria-label="(?:Switch to English|Passer en français)"([^>]*)>(.*?)</button>',
        langue, corps, flags=re.S)

    # 4. la vidéo : deux fichiers locaux au lieu d'un Full HD distant
    corps = re.sub(
        r'<video\b[^>]*>.*?</video>',
        '<video class="hz-video" autoplay muted loop playsinline preload="metadata" '
        'aria-hidden="true" poster="/assets/img/hz-exp-2-800.webp" '
        'style="width:100%;height:100%;object-fit:cover">'
        '<source src="/assets/video/plage-640.mp4" type="video/mp4" media="(max-width:700px)">'
        '<source src="/assets/video/plage-960.mp4" type="video/mp4">'
        '</video>', corps, flags=re.S)

    # 5. le lien restant vers Unsplash ou Pexels n'a plus lieu d'être
    corps = corps.replace("https://images.unsplash.com/", "/assets/img/")
    return corps


GABARIT = """<!doctype html>
<html lang="%(lg)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(titre)s</title>
<meta name="description" content="%(desc)s">
<meta name="theme-color" content="#201B17">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="canonical" href="%(canonique)s">
%(alternates)s
<meta property="og:type" content="website">
<meta property="og:site_name" content="Villa Damencourt">
<meta property="og:locale" content="%(locale)s">
<meta property="og:title" content="%(titre)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canonique)s">
<meta property="og:image" content="%(apercu)s">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fonts/marcellus-400-latin.woff2">
<link rel="stylesheet" href="/css/polices.css?v=1">
<link rel="stylesheet" href="/css/style.css?v=%(v)s">
</head>
<body>
%(corps)s
<script src="/js/site.js?v=%(v)s" defer></script>
</body>
</html>
"""

SITE = "https://villa-damencourt.example"
VERSION = "1"


def main():
    os.makedirs(os.path.join(RACINE, "en"), exist_ok=True)
    n = 0
    for lg in ("fr", "en"):
        for fichier, cle in PAGES:
            src = os.path.join(CAPTURE, ("" if lg == "fr" else "en-") + cle + ".html")
            if not os.path.exists(src):
                print("  capture absente :", src); continue
            corps = transformer(open(src, encoding="utf-8").read(), lg, fichier)
            titre, desc = TITRES[lg][fichier]
            alt = "\n".join(
              '<link rel="alternate" hreflang="%s" href="%s%s">' % (l, SITE, lien(fichier, l))
              for l in ("fr", "en"))
            alt += '\n<link rel="alternate" hreflang="x-default" href="%s%s">' % (
              SITE, lien(fichier, "fr"))
            page = GABARIT % {
              "lg": lg, "titre": H.escape(titre, quote=True), "desc": H.escape(desc, quote=True),
              "canonique": SITE + lien(fichier, lg), "alternates": alt,
              "locale": "fr_FR" if lg == "fr" else "en_GB",
              "apercu": SITE + "/assets/img/hz-home-a-1280.webp",
              "corps": corps, "v": VERSION}
            dest = os.path.join(RACINE, fichier if lg == "fr" else os.path.join("en", fichier))
            open(dest, "w", encoding="utf-8").write(page)
            n += 1
            print("  %-8s %-16s %6d octets" % (lg, fichier, len(page)))
    print("\n%d pages écrites." % n)


if __name__ == "__main__":
    main()
