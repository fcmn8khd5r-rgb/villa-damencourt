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
_faq = os.path.join(RACINE, "src/faq.json")
FAQ = json.load(open(_faq, encoding="utf-8")) if os.path.exists(_faq) else {}
SRC = json.load(open(os.path.join(RACINE, "src/images-source.json"), encoding="utf-8"))

# Une même photo apparaît sous plusieurs identifiants de slot : la page « la
# villa » réutilise trois vues de la galerie sous les noms hz-col-*. On
# retrouve donc l'image par l'identifiant Unsplash de sa source, et pas
# seulement par celui du slot — sinon trois images restaient non converties.
PAR_PHOTO = {v["id"]: k for k, v in SRC.items() if isinstance(v, dict) and "id" in v}

PAGES = [("index.html", "accueil"), ("la-villa.html", "la-villa"),
         ("chambres.html", "chambres"), ("galerie.html", "galerie"),
         ("sejour.html", "sejour"), ("la-region.html", "la-region"),
         ("journal.html", "journal"),
         # Huitième page, absente de la barre de navigation : on n'y arrive que
         # par les boutons « Réserver » et « Voir les disponibilités ». Elle
         # porte le formulaire de demande, les coordonnées et la foire aux
         # questions — et je l'avais d'abord manquée pour cette raison même.
         # On part de la capture DÉPLIÉE : les réponses de la foire aux
         # questions n'existent dans le DOM qu'une fois la question ouverte.
         # Repliées à la construction, elles seraient absentes de la page ;
         # dépliées, elles y sont toutes, et le script se contente de les
         # replier — donc sans script, on lit tout.
         ("reserver.html", "reserver-deplie")]

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
        "Ce qui se passe à la villa : les travaux, le jardin, la saison des mangues et le carnaval du Moule."),
        "reserver.html": ("Réserver — Villa Damencourt, Le Moule, Guadeloupe",
        "Demande de séjour sans engagement à la Villa Damencourt : dates, tarif exact et options confirmés avant tout versement. Réponse sous 24 heures.")},
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
        "What happens at the villa: the works, the garden, mango season and the Le Moule carnival."),
        "reserver.html": ("Enquire — Villa Damencourt, Le Moule, Guadeloupe",
        "A no-commitment enquiry for Villa Damencourt: dates, exact rate and options confirmed before any payment. We reply within 24 hours.")},
}



CHAMBRES = ["autrebord", "damencourt", "zévallos", "salabouelle", "portedenfer", "lecarbet"]


def _deux_blocs(html):
    """Sépare la barre d'onglets du contenu : ce sont les deux div de tête."""
    prof, debuts = 0, []
    for m in re.finditer(r"<(/?)(\w[\w-]*)[^>]*?(/?)>", html):
        if m.group(1):
            prof -= 1
            if prof == 0 and debuts:
                debuts[-1] = (debuts[-1][0], m.end())
        elif not m.group(3) and m.group(2) not in ("br", "img", "input", "source", "meta", "link"):
            if prof == 0:
                debuts.append((m.start(), None))
            prof += 1
    bouts = [html[a:b] for a, b in debuts if b]
    return (bouts + ["", ""])[:2]


def panneaux_chambres(lg):
    """Les six chambres réunies dans la page, une seule visible à la fois.

    La page capturée ne contenait que l'onglet actif au moment de la capture :
    les cinq autres n'existaient nulle part, et les boutons ne pouvaient rien
    montrer. Chaque onglet a donc été rouvert dans l'original et capturé à son
    tour. Ils sont ici réunis — la barre d'onglets une seule fois, puis les six
    contenus, dont un seul est affiché."""
    prefixe = "" if lg == "fr" else "en-"
    barre, panneaux = None, []
    for cle in CHAMBRES:
        f = os.path.join(CAPTURE, "%songlet-%s.html" % (prefixe, cle))
        if not os.path.exists(f):
            return None
        b, contenu = _deux_blocs(open(f, encoding="utf-8").read())
        if barre is None:
            barre = b
        panneaux.append('<div data-chambre="%s"%s>%s</div>'
                        % (cle, "" if cle == CHAMBRES[0] else ' hidden', contenu))
    # chaque bouton de la barre reçoit la clé de sa chambre, dans l'ordre
    i = [0]
    def marquer(m):
        if i[0] >= len(CHAMBRES):
            return m.group(0)
        cle = CHAMBRES[i[0]]; i[0] += 1
        return m.group(0)[:-1] + ' data-onglet="%s"%s>' % (
            cle, ' aria-current="true"' if cle == CHAMBRES[0] else "")
    barre = re.sub(r'<button[^>]*data-dc-tpl="134"[^>]*>', marquer, barre)
    return barre + "\n" + "\n".join(panneaux)


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


MENU_MOTS = {
  "fr": {"ouvrir": "Ouvrir le menu", "fermer": "Fermer le menu"},
  "en": {"ouvrir": "Open menu",      "fermer": "Close menu"},
}


def poser_menu(corps, lg):
    """Ajoute un menu escamotable à la barre de navigation.

    La barre d'origine était calculée en JavaScript : sous une certaine
    largeur, React retirait la liste des sept liens et montrait un burger.
    Ma capture ayant été prise à 1280 px, elle a figé la version bureau — et
    sur un téléphone les sept liens, larges de 707 px en tout, se
    chevauchaient dans une barre de 390. Les liens sont donc recopiés ici
    dans un tiroir ; la feuille de style masque la liste sous 860 px et
    montre le burger, sans rien changer au-dessus.

    Le tiroir est écrit dans la page et ouvert par « :target » — donc en
    CSS seul. Ni le burger ni la fermeture ne dépendent du JavaScript : si le
    script ne s'exécute pas, le menu s'ouvre quand même. C'est la raison du
    choix ; un burger piloté par script aurait supprimé toute navigation
    mobile le jour où le script manque.
    """
    mots = MENU_MOTS[lg]
    bloc = re.search(r'(<div data-dc-tpl="10"[^>]*>)(.*?)(</div>)', corps, re.S)
    if not bloc:
        print("  ATTENTION : liste de navigation non trouvée (%s)" % lg)
        return corps

    liens = re.findall(r'<a\b[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', bloc.group(2), re.S)
    if len(liens) < 5:
        print("  ATTENTION : %d liens de navigation seulement (%s)" % (len(liens), lg))
        return corps

    burger = ('<a class="hz-burger" href="#hz-tiroir" role="button" '
              'aria-label="%s"><i></i></a>' % mots["ouvrir"])
    corps = corps[:bloc.end()] + burger + corps[bloc.end():]
    corps = corps.replace('<nav data-dc-tpl="8"', '<nav id="hz-haut" data-dc-tpl="8"', 1)

    tiroir = ['<div class="hz-tiroir" id="hz-tiroir">',
              '<a class="hz-tiroir__x" href="#hz-haut" role="button" '
              'aria-label="%s">&times;</a>' % mots["fermer"]]
    for href, dedans in liens:
        texte = re.sub(r"<[^>]+>", "", dedans).strip()
        tiroir.append('<a href="%s">%s</a>' % (href, texte))

    # Ouvert, le tiroir recouvre la barre : la bascule de langue et « Réserver »
    # disparaîtraient le temps qu'il est ouvert. On les reprend en bas, séparés
    # des pages par un filet. Ce sont les deux actions qu'un visiteur cherche
    # justement quand il ouvre un menu.
    barre = corps[corps.find("<nav"):corps.find("</nav>")]
    autre = re.search(r'<a[^>]*?href="([^"]+)"[^>]*?hreflang="(\w+)"[^>]*>(.*?)</a>', barre, re.S)
    if autre:
        tiroir.append('<a class="hz-tiroir__2" href="%s" hreflang="%s" lang="%s">%s</a>'
                      % (autre.group(1), autre.group(2), autre.group(2),
                         re.sub(r"<[^>]+>", "", autre.group(3)).strip()))
    resa = re.search(r'<a[^>]*?href="([^"]+)"[^>]*?data-dc-tpl="14"[^>]*>(.*?)</a>', barre, re.S)
    if resa:
        tiroir.append('<a class="hz-tiroir__2" href="%s">%s</a>'
                      % (resa.group(1), re.sub(r"<[^>]+>", "", resa.group(2)).strip()))
    tiroir.append('</div>')

    fin = corps.find("</nav>")
    if fin == -1:
        print("  ATTENTION : fin de la barre de navigation non trouvée (%s)" % lg)
        return corps
    fin += len("</nav>")
    return corps[:fin] + "".join(tiroir) + corps[fin:]


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

    # 2 bis. les six chambres, réunies dans la page
    if fichier == "chambres.html":
        tout = panneaux_chambres(lg)
        if tout:
            # la section des chambres est celle qui porte les boutons d'onglet
            def remplacer_section(m):
                return m.group(1) + tout + m.group(3)
            corps, n = re.subn(
                r'(<section\b[^>]*>)(.*?data-dc-tpl="134".*?)(</section>)',
                remplacer_section, corps, count=1, flags=re.S)
            if not n:
                print("  ATTENTION : section des chambres non trouvée (%s)" % lg)
            # Les panneaux réunis apportent leurs propres <image-slot> : on
            # repasse la conversion, sans quoi cinq chambres sur six
            # afficheraient un emplacement vide.
            corps = re.sub(r'<image-slot\b(.*?)>\s*</image-slot>', remplacer_image,
                           corps, flags=re.S)

    # 2 ter. Les boutons d'appel à l'action naviguaient en JavaScript : ils
    #        deviennent de vrais liens. Sans cela ils restaient inertes — un
    #        visiteur cliquait « Réserver » et rien ne se passait.
    APPELS = {
      "fr": {"Arrivée": "sejour.html", "Départ": "sejour.html",
             "Voir les disponibilités": "reserver.html",
             "Découvrir la villa": "la-villa.html",
             "Toute la galerie": "galerie.html",
             "Tout le journal": "journal.html",
             "Réserver": "reserver.html"},
      "en": {"Arrival": "sejour.html", "Departure": "sejour.html",
             "See availability": "reserver.html",
             "See the villa": "la-villa.html",
             "The whole gallery": "galerie.html",
             "All entries": "journal.html",
             "Enquire": "reserver.html"},
    }
    def bouton_en_lien(m):
        interieur = m.group(2)
        nu = re.sub(r"<[^>]+>", "", interieur)
        nu = re.sub(r"\s+", " ", H.unescape(nu)).strip().rstrip("—").strip()
        cible = APPELS[lg].get(nu)
        if not cible:
            return m.group(0)
        return '<a href="%s"%s>%s</a>' % (lien(cible, lg), m.group(1), interieur)
    corps = re.sub(r'<button([^>]*)>(.*?)</button>', bouton_en_lien, corps, flags=re.S)

    # 2 quater. Les réponses de la foire aux questions.
    #   Elles n'existaient dans le DOM qu'une fois la question ouverte, et
    #   l'accordéon n'en ouvre qu'une à la fois : aucune capture ne pouvait
    #   donc les contenir toutes. Elles sont reprises du tableau de données de
    #   l'original, et posées VISIBLES sous chaque question. Le script les
    #   replie ; sans lui, on lit l'ensemble — jamais l'inverse.
    if fichier == "reserver.html":
        faq = FAQ.get(lg, [])
        etat = {"i": 0}
        def poser_reponse(m):
            i = etat["i"]
            if i >= len(faq):
                return m.group(0)
            etat["i"] += 1
            return (m.group(0) +
                    '<div class="hz-faq-r" data-faq="%d" style="padding:0 0 22px; max-width:62ch; '
                    'font-size:15px; line-height:1.66; color:rgb(107,96,85)">%s</div>'
                    % (i, H.escape(faq[i]["a"])))
        corps = re.sub(r'<button[^>]*data-dc-tpl="327"[^>]*>.*?</button>',
                       poser_reponse, corps, flags=re.S)
        if etat["i"] != len(faq):
            print("  ATTENTION : %d réponses posées pour %d questions (%s)"
                  % (etat["i"], len(faq), lg))

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
    # Deux plans distincts, et non un seul : la page d'accueil montre la plage,
    # « la région » une vue aérienne. Les avoir confondus mettait le mauvais
    # plan sur la seconde. On les reconnaît à l'identifiant Pexels de la source
    # d'origine.
    VIDEOS = {
      "12021278": ("plage", "hz-exp-1", [480, 800, 1280, 1800]),
      "31931891": ("aerienne", "hz-exp-2", [480, 800, 1280, 1920, 2400]),
    }
    def remplacer_video(m):
        t = m.group(0)
        ident = re.search(r"video-files/(\d+)/", t)
        nom, base, tailles = VIDEOS.get(ident.group(1) if ident else "", VIDEOS["12021278"])
        affiche = "/assets/img/%s-800.webp" % base
        # On conserve le style d'origine : c'est lui qui donne la forme du
        # cadre (plein écran sur l'accueil, bandeau 21/9 sur la région).
        #
        # Sauf l'animation. Le style capturé portait « animation: … hzFade »,
        # et un style en ligne l'emporte sur la feuille : le Ken Burns de
        # repli, prévu dans .hz-video pour que l'affiche dérive quand la
        # lecture est refusée, ne s'appliquait donc jamais. Sur un appareil
        # qui refuse la lecture automatique — économie d'énergie, réglage
        # Safari « ne jamais lire » — on voyait une image parfaitement figée,
        # d'où l'impression d'un site en panne qu'il faut démarrer à la main.
        # L'animation est retirée d'ici pour que la feuille en dispose, et
        # elle y compose le fondu d'entrée AVEC la dérive.
        style = re.search(r'style="([^"]*)"', t)
        propre = re.sub(r'\s*animation\s*:[^;"]*;?', '',
                        style.group(1) if style else '') or \
                 "width:100%;height:100%;object-fit:cover"
        # Une vraie image SOUS la vidéo, et la vidéo cachée tant qu'elle ne
        # joue pas.
        #
        # Il n'y avait ici que l'attribut « poster ». Or un navigateur qui
        # refuse la lecture automatique — Safari avec l'économie d'énergie, ou
        # le réglage « ne jamais lire » — dessine SON PROPRE bouton de lecture
        # par-dessus l'élément vidéo. C'est le « play » qu'il fallait presser.
        # Sur Maison Rorota le même refus ne se voyait pas, parce que la vidéo
        # y est transparente tant qu'elle ne joue pas et qu'une image la
        # double : le bouton du navigateur était dessiné, mais invisible.
        #
        # Même dispositif ici. L'image porte la dérive, la vidéo apparaît en
        # fondu quand elle joue vraiment, et le bouton du navigateur ne peut
        # plus se voir. La vidéo cachée ne reçoit pas les clics : c'est la
        # page entière qui écoute, et un clic n'importe où relance la lecture.
        def jeu(ext):
            return ", ".join("/assets/img/%s-%d.%s %dw" % (base, w, ext, w)
                             for w in tailles)
        return ('<picture class="hz-affiche" aria-hidden="true">'
                '<source type="image/avif" srcset="%s" sizes="100vw">'
                '<source type="image/webp" srcset="%s" sizes="100vw">'
                '<img src="%s" alt="" decoding="async" style="%s">'
                '</picture>'
                '<video class="hz-video" autoplay muted loop playsinline preload="auto" '
                'aria-hidden="true" poster="%s" style="%s">'
                '<source src="/assets/video/%s-640.mp4" type="video/mp4" media="(max-width:700px)">'
                '<source src="/assets/video/%s-960.mp4" type="video/mp4">'
                '</video>'
                % (jeu("avif"), jeu("webp"), affiche, propre,
                   affiche, propre, nom, nom))
    corps = re.sub(r'<video\b[^>]*>.*?</video>', remplacer_video, corps, flags=re.S)

    # 5. le lien restant vers Unsplash ou Pexels n'a plus lieu d'être
    corps = corps.replace("https://images.unsplash.com/", "/assets/img/")
    # 6. le menu escamotable de la barre de navigation
    corps = poser_menu(corps, lg)

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
# Le numéro de version force le navigateur à reprendre CSS et JavaScript.
# À monter dès qu'on touche à l'un des deux : sans cela, un visiteur déjà
# venu — et le développeur lui-même — continue de recevoir l'ancien fichier.
VERSION = "20"


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
