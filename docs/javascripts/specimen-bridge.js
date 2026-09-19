/* Eventual JS bridge: cookbook pages → specimen catalog.
 *
 * Default prefix is today's Pages catalog (the site root). After MkDocs
 * becomes the Pages root and the catalog moves under /specimens/, set
 * <html data-specimen-root="/parch/specimens/">. No TOML builder
 * (exploratory G).
 */
(function () {
  const fallback = "https://yyolk.github.io/parch/";
  const root = (document.documentElement.dataset.specimenRoot || fallback).replace(
    /\/?$/,
    "/",
  );
  document.querySelectorAll("[data-specimen]").forEach((el) => {
    const dest = el.getAttribute("data-specimen");
    if (!dest || el.getAttribute("href")) return;
    el.setAttribute("href", root + dest.replace(/^\//, ""));
  });
})();
