/* ATLAS TO PARADISE — main.js（依存なし） */
(function () {
  "use strict";
  var root = document.documentElement;

  function store(k, v) {
    try {
      if (v === undefined) return localStorage.getItem(k);
      localStorage.setItem(k, v);
    } catch (e) { return null; }
  }

  /* ---------- 日本語 / English 切り替え ---------- */
  var ATTRS = [["data-en-alt", "alt"], ["data-en-aria", "aria-label"]];
  var jaTitle = document.title;
  var metaDesc = document.querySelector('meta[name="description"]');
  var jaDesc = metaDesc ? metaDesc.getAttribute("content") : "";

  function setLang(lang) {
    var en = lang === "en";
    root.lang = en ? "en" : "ja";
    document.querySelectorAll("[data-en]").forEach(function (el) {
      if (el.dataset.ja === undefined) el.dataset.ja = el.innerHTML;
      el.innerHTML = en ? el.getAttribute("data-en") : el.dataset.ja;
    });
    ATTRS.forEach(function (p) {
      document.querySelectorAll("[" + p[0] + "]").forEach(function (el) {
        var k = "ja" + p[1].replace(/-/g, "");
        if (el.dataset[k] === undefined) el.dataset[k] = el.getAttribute(p[1]) || "";
        el.setAttribute(p[1], en ? el.getAttribute(p[0]) : el.dataset[k]);
      });
    });
    document.title = en && root.dataset.titleEn ? root.dataset.titleEn : jaTitle;
    if (metaDesc) metaDesc.setAttribute("content", en && root.dataset.descEn ? root.dataset.descEn : jaDesc);
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.lang === (en ? "en" : "ja")));
    });
    store("lang", en ? "en" : "ja");
  }

  document.querySelectorAll(".lang button").forEach(function (b) {
    b.addEventListener("click", function () { setLang(b.dataset.lang); });
  });
  var q = new URLSearchParams(location.search).get("lang");
  var saved = q || store("lang");
  if (saved === "en") setLang("en");

  /* ---------- モバイルメニュー ---------- */
  var btn = document.getElementById("menuBtn");
  var nav = document.getElementById("siteNav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", String(open));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("is-open");
        btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- 実績のカテゴリ絞り込み（?cat=xxx 対応） ---------- */
  var filters = document.getElementById("filters");
  var grid = document.getElementById("workGrid");
  if (filters && grid) {
    var cards = grid.querySelectorAll(".work-card");
    var apply = function (cat) {
      filters.querySelectorAll(".filter").forEach(function (f) {
        f.classList.toggle("is-active", f.dataset.filter === cat);
      });
      cards.forEach(function (c) { c.hidden = !(cat === "all" || c.dataset.cat === cat); });
    };
    filters.addEventListener("click", function (e) {
      var f = e.target.closest(".filter");
      if (!f) return;
      apply(f.dataset.filter);
      var url = new URL(location.href);
      if (f.dataset.filter === "all") url.searchParams.delete("cat");
      else url.searchParams.set("cat", f.dataset.filter);
      history.replaceState(null, "", url);
    });
    var c0 = new URLSearchParams(location.search).get("cat");
    if (c0 && filters.querySelector('[data-filter="' + c0 + '"]')) apply(c0);
  }

  /* ---------- スクロール表示 ---------- */
  var targets = document.querySelectorAll(".tile,.svc,.work-card,.ec-card,.proc,.status-row,.step,.tier,.faq__item,.news__item,.trouble-box,.names");
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    targets.forEach(function (t) { t.classList.add("reveal"); io.observe(t); });
  }

  /* ---------- お問い合わせ → メール作成 ---------- */
  var form = document.getElementById("contactForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var en = root.lang === "en";
      var f = new FormData(form);
      var prefix = en ? form.dataset.prefixEn : form.dataset.prefixJa;
      var subject = prefix + f.get("topic");
      var body = (en ? "Name: " : "お名前: ") + f.get("name") + "\n" +
                 (en ? "Email: " : "メール: ") + f.get("email") + "\n\n" + f.get("message");
      location.href = "mailto:" + form.dataset.to + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
    });
  }
})();
