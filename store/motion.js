/* Shared motion module for the storefront pages (store + general-store).
   Standardized with docs/workflow/MOTION_SYSTEM.md — this file only wires
   scroll-triggered reveals and the sticky-header compress; every visual
   transition lives in store/shared_style.css so it can be tuned in one
   place. Respects prefers-reduced-motion (CSS handles the visible states). */
(function () {
  "use strict";
  var root = document.documentElement;
  root.classList.add("js");

  /* sticky-header-compress */
  var topbar = document.querySelector(".topbar");
  if (topbar) {
    var onScroll = function () {
      topbar.classList.toggle("scrolled", window.scrollY > 8);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* scroll-triggered reveals */
  var targets = document.querySelectorAll(".reveal, .reveal-fade, .stagger");
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window)) {
    targets.forEach(function (el) { el.classList.add("in"); });
    return;
  }
  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -6% 0px" }
  );
  targets.forEach(function (el) { io.observe(el); });
})();