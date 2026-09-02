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

  /* ---- visionneuse de la galerie ---------------------------------------- */
  /* Elle s'ouvre sur les images de la galerie. Sans ce script, un clic ne
     fait rien de spécial — la page reste entière et parcourable. */
  var vues = $$(".hz-img img").filter(function (im) {
    return im.closest("[data-galerie], .hz-gal, #hz-galerie") !== null;
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
})();
