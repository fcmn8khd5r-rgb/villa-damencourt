/* =========================================================================
   Villa Damencourt — le peu de JavaScript dont le site a besoin.
   =========================================================================
   Une règle tient tout ce fichier : RIEN D'ESSENTIEL N'EN DÉPEND.

   La version précédente faisait l'inverse. Le contenu était masqué par une
   règle CSS et n'apparaissait que si React, ReactDOM et Babel avaient été
   téléchargés depuis unpkg, puis le site compilé dans le navigateur. Trois
   secondes et demie avant le premier mot sur une connexion locale, et une
   page définitivement blanche si l'un des trois manquait à l'appel.

   Ici, la page est complète et lisible avant que ce fichier n'existe. Il
   n'ajoute que de l'agrément : les apparitions au défilement, la
   visionneuse, les onglets. C'est lui qui pose « hz-anime » sur <html>, et
   c'est seulement à ce moment que le CSS s'autorise à masquer quoi que ce
   soit — donc jamais avant d'être capable de le révéler.
   ========================================================================= */
(function () {
  "use strict";
  var doux = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---- apparitions au défilement --------------------------------------- */
  var cibles = $$("[data-reveal]");
  if (cibles.length && !doux && "IntersectionObserver" in window) {
    // On ne prend la main qu'ici : le CSS ne masque rien tant que cette
    // classe n'est pas posée.
    document.documentElement.classList.add("hz-anime");

    // Ce qui est DÉJÀ à l'écran est révélé tout de suite, sans attendre que
    // l'observateur se prononce. Sans cela, le haut de la page reste
    // brièvement vide au chargement — et durablement vide si l'observateur
    // ne se déclenche jamais.
    var hauteur = window.innerHeight || 800;
    cibles.forEach(function (c) {
      var r = c.getBoundingClientRect();
      if (r.top < hauteur * 1.1) c.classList.add("hz-in");
    });

    var vu = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add("hz-in");
        vu.unobserve(e.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.04 });
    cibles.forEach(function (c) { vu.observe(c); });

    // Le filet n'est plus ici : il est en CSS (voir « hzSecours » dans
    // css/style.css). Un minuteur JavaScript peut être ralenti par le
    // navigateur — un onglet en arrière-plan suffit — et c'est exactement
    // ainsi qu'un bloc reste invisible. Une animation CSS différée, elle,
    // se joue sans que rien n'ait à s'exécuter.
  }

  /* ---- navigation mobile ------------------------------------------------ */
  var burger = $("[data-burger], .hz-burger");
  var tiroir = $("[data-drawer], .hz-drawer");
  if (burger && tiroir) {
    burger.addEventListener("click", function () {
      var ouvert = tiroir.hasAttribute("hidden");
      if (ouvert) tiroir.removeAttribute("hidden"); else tiroir.setAttribute("hidden", "");
      burger.setAttribute("aria-expanded", ouvert ? "true" : "false");
      document.body.style.overflow = ouvert ? "hidden" : "";
    });
  }

  /* ---- bascule de langue ------------------------------------------------ */
  /* Le bouton était piloté par React ; il devient un vrai lien vers la même
     page dans l'autre langue. Un lien, et non un bouton : on peut l'ouvrir
     dans un nouvel onglet, le partager, et il fonctionne sans JavaScript —
     c'est d'ailleurs pour cela qu'on le remplace à la construction plutôt
     qu'ici. Ce bloc ne sert que si la substitution n'a pas eu lieu. */
  var bLangue = document.querySelector('button[aria-label="Switch to English"], ' +
                                       'button[aria-label="Passer en français"]');
  if (bLangue) {
    bLangue.addEventListener("click", function () {
      var c = location.pathname;
      var vers = c.indexOf("/en/") === 0
        ? c.replace("/en/", "/")
        : "/en" + (c === "/" ? "/index.html" : c);
      location.href = vers;
    });
  }

  /* ---- visionneuse de la galerie ---------------------------------------- */
  /* Elle s'ouvre sur les images de la galerie. Sans ce script, un clic ne
     fait rien de spécial — la page reste entière et parcourable. */
  var vues = $$(".hz-img img").filter(function (im) {
    // Le balisage d'origine marque les vues agrandissables par un parent en
    // « cursor: zoom-in ». C'est le seul repère disponible, et il est fiable.
    var p = im.closest(".hz-img");
    p = p && p.parentElement;
    return p !== null && /zoom-in/.test(p.getAttribute("style") || "");
  });
  if (vues.length) {
    var boite = document.createElement("div");
    boite.className = "hz-visio";
    boite.setAttribute("role", "dialog");
    boite.setAttribute("aria-modal", "true");
    boite.hidden = true;
    boite.innerHTML =
      '<button class="hz-visio__x" type="button" aria-label="Fermer">&times;</button>' +
      '<img alt=""><p class="hz-visio__leg"></p>';
    document.body.appendChild(boite);
    var img = $("img", boite), leg = $(".hz-visio__leg", boite), courant = 0, ouvreur = null;

    var montrer = function (i) {
      courant = (i + vues.length) % vues.length;
      var v = vues[courant];
      img.src = v.currentSrc || v.src;
      img.alt = v.alt || "";
      leg.textContent = v.alt || "";
    };
    var ouvrir = function (i, depuis) {
      ouvreur = depuis; montrer(i);
      boite.hidden = false;
      document.body.style.overflow = "hidden";
      requestAnimationFrame(function () {
        boite.setAttribute("data-ouvert", "");
        requestAnimationFrame(function () { $(".hz-visio__x", boite).focus(); });
      });
    };
    var fermer = function () {
      boite.removeAttribute("data-ouvert");
      boite.hidden = true;
      document.body.style.overflow = "";
      if (ouvreur) ouvreur.focus();
    };
    vues.forEach(function (v, i) {
      var cadre = v.closest(".hz-img");
      if (!cadre) return;
      cadre.style.cursor = "zoom-in";
      cadre.setAttribute("tabindex", "0");
      cadre.setAttribute("role", "button");
      cadre.addEventListener("click", function () { ouvrir(i, cadre); });
      cadre.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); ouvrir(i, cadre); }
      });
    });
    $(".hz-visio__x", boite).addEventListener("click", fermer);
    boite.addEventListener("click", function (e) { if (e.target === boite) fermer(); });
    document.addEventListener("keydown", function (e) {
      if (boite.hidden) return;
      if (e.key === "Escape") fermer();
      if (e.key === "ArrowRight") montrer(courant + 1);
      if (e.key === "ArrowLeft") montrer(courant - 1);
    });
  }

  /* ---- calendrier de la page « séjour » ---------------------------------- */
  /* Il affiche deux mois et se navigue par les flèches. Il ne sert pas à
     choisir des dates : l'original ne le permettait pas non plus — cliquer un
     jour n'y produisait aucun effet, vérifié avant de le réécrire. On
     reproduit donc ce qu'il faisait, et rien de plus : deux mois, les jours
     pris barrés, et les flèches qui avancent ou reculent.

     Sans ce script, la page garde les deux mois figés au moment de la
     construction. C'est moins pratique, mais parfaitement lisible — le
     tableau des tarifs, lui, est du texte et ne dépend de rien. */
  var MOIS_FR = ["janvier","février","mars","avril","mai","juin","juillet",
                 "août","septembre","octobre","novembre","décembre"];
  var MOIS_EN = ["January","February","March","April","May","June","July",
                 "August","September","October","November","December"];
  var JOURS_FR = ["L","M","M","J","V","S","D"], JOURS_EN = ["M","T","W","T","F","S","S"];

  var STYLE_JOUR = "font-family: Jost, sans-serif; font-size: 13px; aspect-ratio: 1 / 1; " +
    "display: flex; align-items: center; justify-content: center; border-radius: 2px; " +
    "transition: background 250ms, color 250ms, border-color 250ms; " +
    "border: 1px solid rgb(220, 209, 191); ";
  var LIBRE = "background: transparent; color: rgb(43, 36, 30); cursor: pointer; text-decoration: none;";
  var PRIS  = "background: rgb(228, 218, 202); color: rgb(166, 150, 130); cursor: not-allowed; " +
              "text-decoration: line-through;";
  var STYLE_INITIALE = "font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; " +
    "text-align: center; color: rgb(154, 140, 124); padding-bottom: 8px;";

  /* Les périodes prises sont simulées — la villa est fictive. Elles doivent
     en revanche être STABLES : un calendrier qui change de réservations à
     chaque affichage se remarque tout de suite. On les tire donc d'une
     empreinte du mois, pas d'un tirage au sort. */
  function empreinte(a, m) {
    var h = 2166136261 ^ (a * 12 + m);
    h = Math.imul(h ^ (h >>> 13), 16777619);
    return ((h >>> 0) % 1000) / 1000;
  }
  function prises(a, m) {
    var n = new Date(Date.UTC(a, m + 1, 0)).getUTCDate();
    var e = empreinte(a, m);
    if (e > 0.62) return {};                       // un mois sur trois reste libre
    var debut = 1 + Math.floor(e * (n - 12));
    var duree = 7 + Math.floor(empreinte(a, m + 40) * 8);
    var out = {};
    for (var j = debut; j < Math.min(debut + duree, n + 1); j++) out[j] = true;
    return out;
  }

  var cal = (function () {
    var motif = /^(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$/i;
    var titres = $$("p").filter(function (p) { return motif.test((p.textContent || "").trim()); });
    if (titres.length < 2) return null;
    var blocs = titres.map(function (p) { return p.parentElement; });
    var fleches = $$("button").filter(function (b) { return /^[‹›]$/.test((b.textContent || "").trim()); });
    if (fleches.length < 2) return null;
    return { titres: titres, blocs: blocs, precedent: fleches[0], suivant: fleches[1] };
  })();

  if (cal) {
    var en = document.documentElement.lang === "en";
    var noms = en ? MOIS_EN : MOIS_FR, inits = en ? JOURS_EN : JOURS_FR;
    // On repart du mois affiché à la construction pour ne rien déplacer.
    var t0 = (cal.titres[0].textContent || "").trim().split(/\s+/);
    var base = new Date(Date.UTC(parseInt(t0[t0.length - 1], 10),
                                 Math.max(0, noms.findIndex(function (x) {
                                   return x.toLowerCase() === t0[0].toLowerCase(); })), 1));

    var dessiner = function (bloc, titre, d) {
      var a = d.getUTCFullYear(), m = d.getUTCMonth();
      titre.textContent = noms[m] + " " + a;
      var grille = Array.prototype.filter.call(bloc.children, function (c) {
        return c.tagName !== "P"; })[0];
      if (!grille) return;
      var pris = prises(a, m);
      var premier = (new Date(Date.UTC(a, m, 1)).getUTCDay() + 6) % 7;  // lundi = 0
      var n = new Date(Date.UTC(a, m + 1, 0)).getUTCDate();
      var html = inits.map(function (i) {
        return '<div style="' + STYLE_INITIALE + '"><span class="sc-interp">' + i + '</span></div>';
      }).join("");
      for (var v = 0; v < premier; v++) html += "<div></div>";
      for (var j = 1; j <= n; j++) {
        html += '<button type="button" style="' + STYLE_JOUR + (pris[j] ? PRIS : LIBRE) + '"' +
                (pris[j] ? ' disabled aria-label="' + j + ' ' + noms[m] + ' ' + a +
                           (en ? ', booked"' : ', réservé"') : "") +
                '><span class="sc-interp">' + j + '</span></button>';
      }
      grille.innerHTML = html;
    };

    var poser = function () {
      var d1 = new Date(base);
      var d2 = new Date(Date.UTC(base.getUTCFullYear(), base.getUTCMonth() + 1, 1));
      dessiner(cal.blocs[0], cal.titres[0], d1);
      dessiner(cal.blocs[1], cal.titres[1], d2);
      // On ne recule pas avant le mois courant : proposer un passé n'a pas de sens.
      var maintenant = new Date();
      var plancher = new Date(Date.UTC(maintenant.getFullYear(), maintenant.getMonth(), 1));
      cal.precedent.disabled = base <= plancher;
      cal.precedent.style.opacity = cal.precedent.disabled ? ".35" : "";
      cal.precedent.style.cursor = cal.precedent.disabled ? "not-allowed" : "pointer";
    };
    var glisser = function (n) {
      base = new Date(Date.UTC(base.getUTCFullYear(), base.getUTCMonth() + n, 1));
      poser();
    };
    cal.precedent.addEventListener("click", function () { if (!cal.precedent.disabled) glisser(-1); });
    cal.suivant.addEventListener("click", function () { glisser(1); });
    poser();
  }


  /* ---- onglets de chambres ---------------------------------------------- */
  /* Les six chambres sont toutes dans la page ; on montre celle qu'on demande.
     Sans ce script, la première reste affichée et les cinq autres restent
     masquées : la page reste lisible, seule la navigation entre chambres
     manque. C'est le compromis à retenir quand un script peut ne pas se
     charger — jamais l'inverse. */
  var onglets = $$("[data-onglet]");
  var chambres = $$("[data-chambre]");
  if (onglets.length && chambres.length) {
    var actif = onglets[0].getAttribute("style") || "";
    var repos = onglets[1] ? (onglets[1].getAttribute("style") || "") : actif;
    onglets.forEach(function (o) {
      o.addEventListener("click", function () {
        var cle = o.getAttribute("data-onglet");
        chambres.forEach(function (c) {
          if (c.getAttribute("data-chambre") === cle) c.removeAttribute("hidden");
          else c.setAttribute("hidden", "");
        });
        onglets.forEach(function (x) {
          var choisi = x === o;
          x.setAttribute("style", choisi ? actif : repos);
          if (choisi) x.setAttribute("aria-current", "true");
          else x.removeAttribute("aria-current");
        });
      });
    });
  }


  /* ---- foire aux questions ---------------------------------------------- */
  /* Les réponses sont dans la page, visibles. Le script les replie et les
     rouvre au clic — dans cet ordre, jamais l'inverse : si rien ne s'exécute,
     on lit les six réponses au lieu de six titres muets. */
  var questions = $$('[data-dc-tpl="327"]');
  var reponses = $$(".hz-faq-r");
  if (questions.length && questions.length === reponses.length) {
    var ouvrir = function (i, oui) {
      reponses[i].hidden = !oui;
      questions[i].setAttribute("aria-expanded", oui ? "true" : "false");
      var signe = questions[i].querySelector("span:last-child");
      if (signe) signe.style.transform = oui ? "rotate(45deg)" : "rotate(0deg)";
    };
    questions.forEach(function (q, i) {
      var r = reponses[i];
      var id = "hz-faq-" + i;
      r.id = id;
      q.setAttribute("aria-controls", id);
      ouvrir(i, false);
      q.addEventListener("click", function () {
        var etait = !r.hidden;
        // Une seule ouverte à la fois, comme dans la version d'origine.
        questions.forEach(function (_, j) { ouvrir(j, false); });
        ouvrir(i, !etait);
      });
    });
  }

  /* ---- formulaire de demande -------------------------------------------- */
  /* La villa est fictive : il n'y a rien à envoyer, et la version d'origine
     n'envoyait rien non plus — elle affichait un accusé de réception. On fait
     de même, en le disant. Sans script, le formulaire reste affiché et
     lisible : personne ne croit avoir envoyé quelque chose. */
  var champs = $$("#bk-name, #bk-email, #bk-msg");
  var envoi = $$("button").filter(function (b) {
    return /envoyer la demande|send the enquiry|send request/i.test((b.textContent || "").trim());
  })[0];
  if (envoi && champs.length) {
    var note = document.createElement("p");
    note.id = "hz-envoi-note";
    note.setAttribute("role", "status");
    note.setAttribute("aria-live", "polite");
    note.style.cssText = "margin:14px 0 0; font-size:14px; color:rgb(179,85,47)";
    envoi.parentElement.appendChild(note);
    envoi.addEventListener("click", function (e) {
      e.preventDefault();
      var vide = champs.filter(function (c) { return !(c.value || "").trim(); });
      var en = document.documentElement.lang === "en";
      if (vide.length) {
        note.style.color = "rgb(156,58,40)";
        note.textContent = en ? "Name, email and message are required."
                              : "Le nom, le courriel et le message sont nécessaires.";
        vide[0].focus();
        return;
      }
      note.style.color = "rgb(179,85,47)";
      note.textContent = en
        ? "Demonstration site — nothing was sent. Villa Damencourt is a fictional property."
        : "Site de démonstration — rien n'a été envoyé. La Villa Damencourt est une propriété fictive.";
    });
  }


  /* ---- vidéos ------------------------------------------------------------
     Elles portent autoplay, muted et playsinline : c'est la seule
     configuration que les navigateurs mobiles acceptent sans geste. Cela ne
     suffit pourtant pas toujours — l'économie d'énergie d'iOS et le mode
     données réduites refusent la lecture quoi qu'on fasse. Deux garde-fous
     donc : on retente à chaque occasion, et tant que rien ne joue, l'affiche
     dérive (voir .hz-video dans le CSS) plutôt que de rester figée. */
  var videos = $$(".hz-video");
  if (videos.length) {
    videos.forEach(function (v) {
      v.addEventListener("playing", function () { v.classList.add("hz-joue"); });
      v.addEventListener("pause", function () { v.classList.remove("hz-joue"); });

      /* RATTRAPAGE : la lecture peut avoir commencé AVANT ce script.
         Les <source> étant déclarées dans la page et la vidéo souvent déjà en
         cache, elle démarre parfois dès l'analyse du document — mesuré à
         507 ms, quand site.js n'arrivait qu'à 668. L'événement « playing »
         était alors passé sans personne pour l'entendre : la classe n'était
         jamais posée, et la vidéo jouait derrière une opacité nulle. On ne
         voyait que l'affiche, sur toute visite de retour. */
      if (!v.paused && v.readyState >= 3) v.classList.add("hz-joue");
      var tenter = function () {
        if (!v.paused) return;
        var p = v.play();
        if (p && p.catch) p.catch(function () { /* refusée : l'affiche dérive */ });
      };
      tenter();
      ["loadedmetadata", "loadeddata", "canplay"].forEach(function (e) {
        v.addEventListener(e, tenter);
      });

      /* Quelques essais espacés, le temps que le navigateur veuille bien.
         Les événements de chargement ne se produisent qu'une fois : si le
         refus tombe sur chacun d'eux, plus rien ne retente avant que la
         personne ne touche l'écran. Or l'autorisation n'est pas figée — elle
         peut être accordée quand l'onglet passe au premier plan ou quand le
         mode économie d'énergie est levé. Six secondes d'essais toutes les
         demi-secondes ne coûtent rien : un play() refusé rend une promesse
         rejetée, que l'on ignore. */
      var essais = 0;
      var relance = setInterval(function () {
        if (!v.paused || ++essais > 40) { clearInterval(relance); return; }
        tenter();
      }, 250);
      document.addEventListener("visibilitychange", function () {
        if (!document.hidden) tenter();
      });
      ["pointerdown", "keydown", "scroll"].forEach(function (e) {
        window.addEventListener(e, tenter, { once: true, passive: true });
      });
    });
  }

})();
