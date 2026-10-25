#!/usr/bin/env python3
"""
data/content.json から、サイト一式を生成します。
使い方:  python3 build.py
生成物:  index.html / works.html / news.html / sitemap.xml / robots.txt / llms.txt
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(ROOT, "data", "content.json"), encoding="utf-8"))
SITE = D["site"]
SEC = D["sections"]
LAB = D["labels"]
BASE = SITE["baseUrl"].rstrip("/") + "/"

try:
    from PIL import Image  # 画像サイズの取得（無くても動きます）
except Exception:  # pragma: no cover
    Image = None


# ---------- 小さな道具 ----------
def esc(s):
    return html.escape(str(s), quote=True)


def rich(s):
    """**強調** と 改行(\\n) だけを許可した、安全な簡易マークアップ。"""
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s.replace("\n", "<br>")


def J(o):
    return rich(o["ja"])


def A(o, attr="data-en"):
    """英語版を data-en 属性として添える。"""
    return f' {attr}="{esc(rich(o["en"]))}"'


def AT(o, name):
    """属性（alt / aria-label など）用の英語版。"""
    return f' data-en-{name}="{esc(o["en"])}"'


def exists(rel):
    return os.path.exists(os.path.join(ROOT, rel))


def img_tag(rel, alt_obj, cls="", lazy=True, eager=False):
    w = h = ""
    if Image and exists(rel):
        with Image.open(os.path.join(ROOT, rel)) as im:
            w, h = im.size
    size = f' width="{w}" height="{h}"' if w else ""
    loading = ' loading="lazy" decoding="async"' if lazy and not eager else ""
    klass = f' class="{cls}"' if cls else ""
    return (
        f'<img src="{esc(rel)}"{size}{klass}{loading} alt="{esc(alt_obj["ja"])}"{AT(alt_obj, "alt")}>'
    )


def date_disp(iso):
    return iso.replace("-", ".")


NEWS = sorted(D["news"], key=lambda n: n["date"], reverse=True)
LAST_UPDATED = NEWS[0]["date"]
CATS = {c["id"]: c["label"] for c in D["categories"]}
WORKS = D["works"]


def hours_chip(w):
    if not w.get("hours"):
        return ""
    ar = SEC["archive"]
    ja = f'{ar["hoursPrefix"]["ja"]}{w["hours"]}{ar["hoursSuffix"]["ja"]}'
    en = f'{ar["hoursPrefix"]["en"]}{w["hours"]}{ar["hoursSuffix"]["en"]}'
    return f'<span class="chip" data-en="{esc(en)}">{esc(ja)}</span>'


def cat_chip(cid):
    o = CATS[cid]
    return f'<span class="chip chip--cat"{A(o)}>{J(o)}</span>'


def ext(url):
    return ' target="_blank" rel="noopener"' if url.startswith("http") else ""


# ---------- 部品 ----------
def lang_switch(extra=""):
    return (
        f'<div class="lang {extra}" role="group" aria-label="{esc(LAB["langGroup"]["ja"])}"{AT(LAB["langGroup"], "aria")}>'
        '<button type="button" data-lang="ja" aria-pressed="true">日本語</button>'
        '<button type="button" data-lang="en" aria-pressed="false" lang="en">EN</button>'
        "</div>"
    )


def header(prefix):
    links = "".join(
        f'<li><a href="{prefix}{esc(n["href"])}"{A(n["label"])}>{J(n["label"])}</a></li>' for n in D["nav"]
    )
    cta = {"ja": "相談する", "en": "Get in touch"}
    return f"""
<a class="skip" href="#main"{A(LAB["skip"])}>{J(LAB["skip"])}</a>
<header class="site-header" id="siteHeader">
  <div class="container header__bar">
    <a class="brand" href="{prefix or './'}{'' if prefix else '#top'}" aria-label="{esc(SITE["brand"])}">
      <img src="assets/img/icon-192.png" width="32" height="32" alt="" class="brand__icon">
      <span class="brand__name">{esc(SITE["brand"])}</span>
    </a>
    <nav class="nav" id="siteNav" aria-label="Main">
      <ul>{links}</ul>
    </nav>
    <div class="header__tools">
      {lang_switch()}
      <a class="btn btn--accent btn--sm header__cta" href="{prefix}#contact"{A(cta)}>{J(cta)}</a>
      <button class="menu-btn" type="button" id="menuBtn" aria-expanded="false" aria-controls="siteNav" aria-label="{esc(LAB["menu"]["ja"])}"{AT(LAB["menu"], "aria")}>
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>"""


def footer(prefix):
    f = D["footer"]
    return f"""
<footer class="site-footer">
  <div class="container footer__bar">
    <p class="footer__brand"><span{A(f["tagline"])}>{J(f["tagline"])}</span><br><small>{esc(f["copyright"])}</small></p>
    <p class="footer__links">
      <a href="{prefix or ''}works.html"{A(LAB["worksPageTitle"])}>{J(LAB["worksPageTitle"])}</a>
      <a href="{prefix or ''}news.html"{A(LAB["newsPageTitle"])}>{J(LAB["newsPageTitle"])}</a>
      <a href="{prefix}#top"{A(LAB["backTop"])}>{J(LAB["backTop"])}</a>
    </p>
    {lang_switch("lang--footer")}
  </div>
</footer>"""


def section_head(key, extra_lead=""):
    s = SEC[key]
    lead = ""
    if "lead" in s:
        lead = f'<p class="section__lead"{A(s["lead"])}>{J(s["lead"])}</p>'
    return f"""
    <p class="eyebrow">{esc(s["eyebrow"])}</p>
    <h2 class="section__title"{A(s["title"])}>{J(s["title"])}</h2>
    {lead}"""


def news_item(n, cta=True):
    t = SEC["notes"]["types"][n["type"]]
    link = ""
    if n.get("link") and n.get("cta"):
        link = f'<a class="link-arrow" href="{esc(n["link"])}"{A(n["cta"])}>{J(n["cta"])}</a>'
    return f"""
      <li class="news__item news__item--{n["type"]}">
        <div class="news__meta">
          <time datetime="{n["date"]}">{date_disp(n["date"])}</time>
          <span class="chip"{A(t)}>{J(t)}</span>
        </div>
        <div class="news__body">
          <h3{A(n["title"])}>{J(n["title"])}</h3>
          <p{A(n["body"])}>{J(n["body"])}</p>
          {link}
        </div>
      </li>"""


def work_card(w, show_img=False):
    img = ""
    if show_img and w.get("img"):
        img = f'<div class="work-card__img">{img_tag(w["img"], w["title"])}</div>'
    links = ""
    if w.get("url"):
        v = SEC["archive"]["view"]
        links += f'<a class="link-arrow" href="{esc(w["url"])}"{ext(w["url"])}{A(v)}>{J(v)}</a>'
    for x in w.get("extra", []):
        links += f'<a class="link-arrow" href="{esc(x["url"])}"{ext(x["url"])}{A(x["label"])}>{J(x["label"])}</a>'
    if w.get("demoUrl") and w.get("demoLive"):
        o = SEC["ec"]["openDemo"]
        links += f'<a class="link-arrow" href="{esc(w["demoUrl"])}"{ext(w["demoUrl"])}{A(o)}>{J(o)}</a>'
    elif w.get("ecCard"):
        o = SEC["ec"]["preparing"]
        links += f'<span class="muted"{A(o)}>{J(o)}</span>'
    return f"""
    <article class="work-card" data-cat="{w["cat"]}">
      {img}
      <div class="work-card__body">
        <div class="meta">{cat_chip(w["cat"])}{hours_chip(w)}</div>
        <h3{A(w["title"])}>{J(w["title"])}</h3>
        <p{A(w["summary"])}>{J(w["summary"])}</p>
        <div class="work-card__links">{links}</div>
      </div>
    </article>"""


# ---------- JSON-LD（検索・AI向けの構造化データ） ----------
def jsonld(graph):
    s = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)
    return '<script type="application/ld+json">' + s.replace("</", "<\\/") + "</script>"


def person_node():
    return {
        "@type": "Person",
        "@id": BASE + "#person",
        "name": SITE["personJa"],
        "alternateName": [SITE["personEn"], SITE["alternateName"]],
        "jobTitle": "Web Marketer / Digital Creator",
        "description": SITE["description"]["ja"],
        "url": BASE,
        "image": BASE + SITE["icon"],
        "email": SITE["email"],
        "knowsAbout": ["Web consulting", "Web marketing", "SEO", "Google Analytics", "AI adoption", "E-commerce development", "Website security and monitoring", "Japanese localization"],
        "hasCredential": [
            {"@type": "EducationalOccupationalCredential", "name": c["en"]} for c in D["certs"]
        ],
        **({"sameAs": SITE["sameAs"]} if SITE["sameAs"] else {}),
    }


def common_graph():
    return [
        {
            "@type": "WebSite",
            "@id": BASE + "#website",
            "url": BASE,
            "name": SITE["brand"],
            "inLanguage": ["ja", "en"],
            "publisher": {"@id": BASE + "#person"},
        },
        person_node(),
        {
            "@type": "ProfessionalService",
            "@id": BASE + "#service",
            "name": SITE["brand"] + " / " + SITE["personEn"],
            "url": BASE,
            "provider": {"@id": BASE + "#person"},
            "description": SITE["description"]["en"],
            "serviceType": [s["title"]["en"] for s in D["services"]],
            "availableLanguage": ["ja", "en"],
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": "Services",
                "itemListElement": [
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["title"]["en"], "description": s["text"]["en"]}}
                    for s in D["services"]
                ],
            },
        },
    ]


def works_itemlist(items, name):
    out = []
    for i, w in enumerate(items, 1):
        url = w.get("url") or (BASE + "works.html#" + w["id"])
        node = {"@type": "ListItem", "position": i, "item": {"@type": "CreativeWork", "name": w["title"]["en"], "alternateName": w["title"]["ja"], "description": w["summary"]["en"], "creator": {"@id": BASE + "#person"}, "url": url}}
        if w.get("img"):
            node["item"]["image"] = BASE + w["img"]
        out.append(node)
    return {"@type": "ItemList", "name": name, "itemListElement": out}


# ---------- ページの骨組み ----------
def page(fname, title, desc, body, graph, prefix="", canonical=""):
    og = BASE + SITE["ogImage"]
    canon = BASE + canonical
    head = f"""<!doctype html>
<html lang="ja" data-title-en="{esc(title["en"])}" data-desc-en="{esc(desc["en"])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title["ja"])}</title>
<meta name="description" content="{esc(desc["ja"])}">
<link rel="canonical" href="{esc(canon)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="author" content="{esc(SITE["personEn"])}">
<meta name="theme-color" content="#F7F9FC">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE["brand"])}">
<meta property="og:title" content="{esc(title["ja"])}">
<meta property="og:description" content="{esc(desc["ja"])}">
<meta property="og:url" content="{esc(canon)}">
<meta property="og:image" content="{esc(og)}">
<meta property="og:locale" content="ja_JP">
<meta property="og:locale:alternate" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title["ja"])}">
<meta name="twitter:description" content="{esc(desc["ja"])}">
<meta name="twitter:image" content="{esc(og)}">
<link rel="icon" href="assets/img/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&family=Noto+Sans+JP:wght@400;500;700&family=Plus+Jakarta+Sans:wght@500;700;800&display=swap">
<link rel="stylesheet" href="assets/css/style.css">
{jsonld(graph)}
<script>document.documentElement.classList.add("js")</script>
</head>
<body>
{header(prefix)}
<main id="main">
{body}
</main>
{footer(prefix)}
<script src="assets/js/main.js" defer></script>
</body>
</html>
"""
    with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as f:
        f.write(head)
    print("wrote", fname)


# ---------- トップページ ----------
def build_index():
    h = D["hero"]
    stats = "".join(
        f'<div class="stat"><div class="stat__value">{esc(s["value"])}</div><div class="stat__label"{A(s["label"])}>{J(s["label"])}</div></div>'
        for s in D["stats"]
    )
    certs = "".join(f'<li{A(c)}>{J(c)}</li>' for c in D["certs"])

    hero = f"""
<section class="hero" id="top">
  <div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div>
  <div class="container hero__grid">
    <div class="hero__copy">
      <p class="badge"><span class="dot" aria-hidden="true"></span><span{A(h["statusLabel"])}>{J(h["statusLabel"])}</span> <time datetime="{LAST_UPDATED}">{date_disp(LAST_UPDATED)}</time><span class="badge__sep">／</span><span{A(h["statusActive"])}>{J(h["statusActive"])}</span></p>
      <p class="eyebrow eyebrow--plain">{esc(h["eyebrow"]["ja"])}</p>
      <h1{A(h["title"])}>{J(h["title"])}</h1>
      <p class="lead"{A(h["lead"])}>{J(h["lead"])}</p>
      <div class="cta-row">
        <a class="btn btn--dark" href="#contact"{A(h["ctaPrimary"])}>{J(h["ctaPrimary"])}</a>
        <a class="btn btn--ghost" href="#latest"{A(h["ctaSecondary"])}>{J(h["ctaSecondary"])}</a>
      </div>
    </div>
    <aside class="profile-card" aria-label="Profile">
      <div class="profile-card__id">
        {img_tag(SITE["icon"], D["sections"]["about"]["iconAlt"], "avatar", eager=True)}
        <div><p class="profile-card__name">{esc(SITE["personJa"])}</p><p class="profile-card__en">{esc(SITE["personEn"])} / Web Marketer</p></div>
      </div>
      <div class="stats">{stats}</div>
      <ul class="certs">{certs}</ul>
    </aside>
  </div>
</section>"""

    band_items = "".join(
        f'<li><time datetime="{n["date"]}">{date_disp(n["date"])}</time><span class="chip"{A(SEC["notes"]["types"][n["type"]])}>{J(SEC["notes"]["types"][n["type"]])}</span><span{A(n["title"])}>{J(n["title"])}</span></li>'
        for n in NEWS[: SEC["notes"]["band"]]
    )
    band = f"""
<section class="container updates-band" aria-label="Updates">
  <p class="updates-band__label"><span class="dot dot--blue" aria-hidden="true"></span><span{A(h["statusLabel"])}>{J(h["statusLabel"])}</span> {date_disp(LAST_UPDATED)}</p>
  <ul class="updates-band__list">{band_items}</ul>
  <a class="link-arrow" href="news.html"{A(SEC["notes"]["all"])}>{J(SEC["notes"]["all"])}</a>
</section>"""

    L = SEC["latest"]
    latest_works = [w for w in WORKS if w.get("latest")]
    tiles = ""
    for i, w in enumerate(latest_works):
        big = " tile--big" if i == 0 else ""
        tiles += f"""
      <a class="tile{big}" href="{esc(w["url"])}"{ext(w["url"])}>
        {img_tag(w["img"], w["title"], eager=(i == 0))}
        <span class="tile__cap">
          <span class="tile__meta">{'LATEST / ' if i == 0 else ''}{hours_chip(w).replace('chip','tile__hours')}</span>
          <span class="tile__title"{A(w["title"])}>{J(w["title"])}</span>
          <span class="tile__sum"{A(w["summary"])}>{J(w["summary"])}</span>
        </span>
      </a>"""
    latest = f"""
<section class="section" id="latest" aria-labelledby="latestTitle">
  <div class="container">
    <div class="section__row">
      <div>{section_head("latest").replace('<h2 class="section__title"', '<h2 id="latestTitle" class="section__title"').replace(f'<p class="section__lead"{A(L["lead"])}>{J(L["lead"])}</p>', '')}
        <p class="section__lead"{A(L["lead"])}>{J(L["lead"])}</p></div>
      <a class="link-arrow" href="#archive"{A(L["more"])}>{J(L["more"])}</a>
    </div>
    <div class="bento">{tiles}
    </div>
  </div>
</section>"""

    S = SEC["security"]
    rows = "".join(
        f"""
      <li class="status-row">
        <span class="status-row__no">{it["no"]}</span>
        <span class="status-row__text"><strong{A(it["title"])}>{J(it["title"])}</strong> <span class="muted"{A(it["text"])}>{J(it["text"])}</span></span>
        <span class="status-row__badge"{A(S["available"])}>{J(S["available"])}</span>
      </li>"""
        for it in S["items"]
    )
    steps = "".join(
        f'<li class="step"><span class="step__no">STEP {i}</span><strong{A(st["title"])}>{J(st["title"])}</strong><span{A(st["text"])}>{J(st["text"])}</span></li>'
        for i, st in enumerate(S["steps"], 1)
    )
    tiers = "".join(
        f'<li class="tier"><strong{A(t["title"])}>{J(t["title"])}</strong><span{A(t["text"])}>{J(t["text"])}</span></li>' for t in S["tiers"]
    )
    security = f"""
<section class="section section--tint" id="security" aria-labelledby="secTitle">
  <div class="container">
    {section_head("security").replace('<h2 class="section__title"', '<h2 id="secTitle" class="section__title"')}
    <ul class="status-panel">{rows}
    </ul>
    <h3 class="subhead"{A(S["stepsTitle"])}>{J(S["stepsTitle"])}</h3>
    <p class="muted"{A(S["stepsLead"])}>{J(S["stepsLead"])}</p>
    <ol class="steps">{steps}</ol>
    <h3 class="subhead"{A(S["tiersTitle"])}>{J(S["tiersTitle"])}</h3>
    <ul class="tiers">{tiers}</ul>
    <p class="closing"{A(S["closing"])}>{J(S["closing"])}</p>
    <div class="cta-line">
      <p class="muted"{A(S["note"])}>{J(S["note"])}</p>
      <a class="btn btn--accent" href="#contact"{A(S["cta"])}>{J(S["cta"])}</a>
    </div>
  </div>
</section>"""

    svc = ""
    for s in D["services"]:
        cls = "svc svc--lead" if s["lead"] else "svc"
        cta = ""
        if s.get("cta"):
            cta = f'<a class="link-arrow" href="#contact"{A(s["cta"])}>{J(s["cta"])}</a>'
        text = f'<p{A(s["text"])}>{J(s["text"])}</p>' if s["lead"] or s.get("text") else ""
        svc += f"""
      <li class="{cls}">
        <span class="svc__no">{s["no"]}</span>
        <h3{A(s["title"])}>{J(s["title"])}</h3>
        {text}
        {cta}
      </li>"""
    services = f"""
<section class="section" id="services" aria-labelledby="svcTitle">
  <div class="container">
    {section_head("services").replace('<h2 class="section__title"', '<h2 id="svcTitle" class="section__title"')}
    <ul class="services">{svc}
    </ul>
  </div>
</section>"""

    E = SEC["ec"]
    ec_cards = ""
    for w in [x for x in WORKS if x.get("ecCard")]:
        safety = ""
        if w.get("safety"):
            safety = f'<p class="safety"><strong{A(E["safety"])}>{J(E["safety"])}</strong>：<span{A(w["safety"])}>{J(w["safety"])}</span></p>'
        if w.get("demoLive") and w.get("demoUrl"):
            demo = f'<a class="btn btn--accent btn--sm" href="{esc(w["demoUrl"])}"{ext(w["demoUrl"])}{A(E["openDemo"])}>{J(E["openDemo"])}</a>'
        else:
            demo = f'<p class="muted"{A(E["preparing"])}>{J(E["preparing"])}</p>'
        ec_cards += f"""
      <article class="ec-card" id="{w["id"]}">
        <div class="ec-card__img">{img_tag(w["img"], w["title"])}</div>
        <div class="ec-card__body">
          <div class="meta"><span class="chip"{A(E["fictional"])}>{J(E["fictional"])}</span>{hours_chip(w)}<span class="chip">{esc(w["tech"])}</span></div>
          <h3{A(w["title"])}>{J(w["title"])}</h3>
          <p{A(w["summary"])}>{J(w["summary"])}</p>
          {safety}
          {demo}
        </div>
      </article>"""
    ec = f"""
<section class="section section--tint" id="ec" aria-labelledby="ecTitle">
  <div class="container">
    {section_head("ec").replace('<h2 class="section__title"', '<h2 id="ecTitle" class="section__title"')}
    <div class="ec-grid">{ec_cards}
    </div>
  </div>
</section>"""

    AR = SEC["archive"]
    chips = "".join(
        f'<a class="filter" href="works.html?cat={c["id"]}"{A(c["label"])}>{J(c["label"])}</a>' for c in D["categories"]
    )
    tops = [w for w in WORKS if w.get("top")][: AR["topCount"]]
    cards = "".join(work_card(w) for w in tops)
    archive = f"""
<section class="section" id="archive" aria-labelledby="arcTitle">
  <div class="container">
    {section_head("archive").replace('<h2 class="section__title"', '<h2 id="arcTitle" class="section__title"')}
    <div class="filters"><a class="filter is-active" href="works.html"{A(LAB["filterAll"])}>{J(LAB["filterAll"])}</a>{chips}</div>
    <div class="work-grid">{cards}
    </div>
    <p class="center"><a class="btn btn--ghost" href="works.html"{A(AR["all"])}>{J(AR["all"])}</a></p>
  </div>
</section>"""

    P = SEC["process"]
    pitems = "".join(
        f'<li class="proc"><span class="proc__no">0{i}</span><h3{A(p["title"])}>{J(p["title"])}</h3><p{A(p["text"])}>{J(p["text"])}</p></li>'
        for i, p in enumerate(P["items"], 1)
    )
    process = f"""
<section class="section section--tint" id="process" aria-labelledby="procTitle">
  <div class="container">
    {section_head("process").replace('<h2 class="section__title"', '<h2 id="procTitle" class="section__title"')}
    <ol class="process">{pitems}</ol>
  </div>
</section>"""

    AB = SEC["about"]
    if exists(SITE["photo"]):
        photo = img_tag(SITE["photo"], AB["photoAlt"], "about__photo")
    else:
        photo = '<div class="about__photo about__photo--ph" role="img" aria-label="photo placeholder"><span>assets/img/1.png</span></div>'
    paras = "".join(f'<p{A(p)}>{J(p)}</p>' for p in AB["paragraphs"])
    about = f"""
<section class="section" id="about" aria-labelledby="aboutTitle">
  <div class="container about">
    <div class="about__media">{photo}</div>
    <div class="about__text">
      {section_head("about").replace('<h2 class="section__title"', '<h2 id="aboutTitle" class="section__title"')}
      {paras}
      <p class="muted"{A(AB["areas"])}>{J(AB["areas"])}</p>
      <div class="names">
        {img_tag(SITE["icon"], AB["iconAlt"], "names__icon")}
        <div>
          <p class="names__title"{A(AB["namesTitle"])}>{J(AB["namesTitle"])}</p>
          <p{A(AB["namesText"])}>{J(AB["namesText"])}</p>
        </div>
      </div>
    </div>
  </div>
</section>"""

    N = SEC["notes"]
    troubles = "".join(f'<li{A(t)}>{J(t)}</li>' for t in N["troubles"])
    news_html = "".join(news_item(n) for n in NEWS[:5])
    notes = f"""
<section class="section section--tint" id="notes" aria-labelledby="notesTitle">
  <div class="container">
    {section_head("notes").replace('<h2 class="section__title"', '<h2 id="notesTitle" class="section__title"')}
    <div class="trouble-box">
      <h3{A(N["troublesTitle"])}>{J(N["troublesTitle"])}</h3>
      <ul class="trouble-list">{troubles}</ul>
      <div class="cta-line"><p class="muted"{A(N["troublesFlow"])}>{J(N["troublesFlow"])}</p><a class="btn btn--accent btn--sm" href="#contact"{A({"ja": "相談する", "en": "Get in touch"})}>相談する</a></div>
    </div>
    <ul class="news">{news_html}
    </ul>
    <p class="center"><a class="link-arrow" href="news.html"{A(N["all"])}>{J(N["all"])}</a></p>
  </div>
</section>"""

    faq_items = "".join(
        f'<details class="faq__item"><summary{A(f["q"])}>{J(f["q"])}</summary><p{A(f["a"])}>{J(f["a"])}</p></details>'
        for f in D["faq"]
    )
    faq = f"""
<section class="section" id="faq" aria-labelledby="faqTitle">
  <div class="container container--narrow">
    {section_head("faq").replace('<h2 class="section__title"', '<h2 id="faqTitle" class="section__title"')}
    <div class="faq">{faq_items}</div>
  </div>
</section>"""

    C = SEC["contact"]
    F = C["form"]
    opts = "".join(f'<option value="{esc(t["ja"])}"{A(t)}>{esc(t["ja"])}</option>' for t in F["topics"])

    def qr(key, label):
        if exists(SITE[key]):
            return f'<figure class="qr">{img_tag(SITE[key], label)}<figcaption{A(label)}>{J(label)}</figcaption></figure>'
        return f'<figure class="qr qr--ph"><div class="qr__ph"><span{A(C["qrMissing"])}>{J(C["qrMissing"])}</span></div><figcaption{A(label)}>{J(label)}</figcaption></figure>'

    contact = f"""
<section class="section section--dark" id="contact" aria-labelledby="contactTitle">
  <div class="container contact">
    <div class="contact__copy">
      <p class="eyebrow eyebrow--light">{esc(C["eyebrow"])}</p>
      <h2 id="contactTitle" class="section__title"{A(C["title"])}>{J(C["title"])}</h2>
      <p{A(C["lead"])}>{J(C["lead"])}</p>
      <p class="qr-title"{A(C["qrTitle"])}>{J(C["qrTitle"])}</p>
      <div class="qr-row">{qr("qrLine", C["lineLabel"])}<div class="qr-mid">{img_tag(SITE["icon"], SEC["about"]["iconAlt"], "qr-mid__img")}</div>{qr("qrWhatsapp", C["waLabel"])}</div>
    </div>
    <form class="form" id="contactForm" action="mailto:{esc(SITE["email"])}" method="post" enctype="text/plain" data-to="{esc(SITE["email"])}" data-prefix-ja="{esc(F["subjectPrefix"]["ja"])}" data-prefix-en="{esc(F["subjectPrefix"]["en"])}">
      <label><span{A(F["name"])}>{J(F["name"])}</span><input name="name" type="text" autocomplete="name" required></label>
      <label><span{A(F["email"])}>{J(F["email"])}</span><input name="email" type="email" autocomplete="email" required></label>
      <label><span{A(F["topic"])}>{J(F["topic"])}</span><select name="topic">{opts}</select></label>
      <label><span{A(F["message"])}>{J(F["message"])}</span><textarea name="message" rows="5" required></textarea></label>
      <button class="btn btn--light" type="submit"{A(F["send"])}>{J(F["send"])}</button>
    </form>
  </div>
</section>"""

    body = hero + band + latest + security + services + ec + archive + process + about + notes + faq + contact

    graph = common_graph() + [
        {
            "@type": "WebPage",
            "@id": BASE + "#webpage",
            "url": BASE,
            "name": SITE["title"]["ja"],
            "description": SITE["description"]["ja"],
            "inLanguage": "ja",
            "isPartOf": {"@id": BASE + "#website"},
            "about": {"@id": BASE + "#person"},
            "dateModified": LAST_UPDATED,
        },
        {
            "@type": "FAQPage",
            "@id": BASE + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": f["q"]["ja"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]["ja"]}} for f in D["faq"]
            ],
        },
        works_itemlist(latest_works + [w for w in WORKS if w.get("ecCard")], "Featured works"),
    ]
    page("index.html", SITE["title"], SITE["description"], body, graph, prefix="", canonical="")


# ---------- 実績一覧 ----------
def build_works():
    ordered = [w for w in WORKS if w.get("latest")] + [w for w in WORKS if w.get("ecCard")] + [w for w in WORKS if not w.get("latest") and not w.get("ecCard")]
    chips = f'<button class="filter is-active" type="button" data-filter="all"{A(LAB["filterAll"])}>{J(LAB["filterAll"])}</button>' + "".join(
        f'<button class="filter" type="button" data-filter="{c["id"]}"{A(c["label"])}>{J(c["label"])}</button>' for c in D["categories"]
    )
    cards = "".join(work_card(w, show_img=True).replace('<article class="work-card"', f'<article id="{w["id"]}" class="work-card"', 1) for w in ordered)
    body = f"""
<section class="section page-head">
  <div class="container">
    <p><a class="link-arrow" href="./"{A(LAB["back"])}>{J(LAB["back"])}</a></p>
    <h1 class="section__title"{A(LAB["worksPageTitle"])}>{J(LAB["worksPageTitle"])}</h1>
    <p class="section__lead"{A(LAB["worksPageLead"])}>{J(LAB["worksPageLead"])}</p>
    <div class="filters" id="filters">{chips}</div>
    <div class="work-grid work-grid--all" id="workGrid">{cards}
    </div>
  </div>
</section>"""
    title = {"ja": LAB["worksPageTitle"]["ja"] + " | " + SITE["personEn"], "en": LAB["worksPageTitle"]["en"] + " | " + SITE["personEn"]}
    graph = common_graph() + [works_itemlist(ordered, "All works")]
    page("works.html", title, LAB["worksPageLead"], body, graph, prefix="./", canonical="works.html")


# ---------- 更新履歴 ----------
def build_news():
    items = "".join(news_item(n) for n in NEWS)
    body = f"""
<section class="section page-head">
  <div class="container container--narrow">
    <p><a class="link-arrow" href="./"{A(LAB["back"])}>{J(LAB["back"])}</a></p>
    <h1 class="section__title"{A(LAB["newsPageTitle"])}>{J(LAB["newsPageTitle"])}</h1>
    <p class="section__lead"{A(LAB["newsPageLead"])}>{J(LAB["newsPageLead"])}</p>
    <ul class="news">{items}
    </ul>
  </div>
</section>"""
    title = {"ja": LAB["newsPageTitle"]["ja"] + " | " + SITE["personEn"], "en": LAB["newsPageTitle"]["en"] + " | " + SITE["personEn"]}
    graph = common_graph()
    page("news.html", title, LAB["newsPageLead"], body, graph, prefix="./", canonical="news.html")


# ---------- sitemap / robots / llms.txt ----------
def build_extras():
    urls = [("", "1.0"), ("works.html", "0.8"), ("news.html", "0.6")]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pr in urls:
        sm.append(f"  <url><loc>{BASE}{u}</loc><lastmod>{LAST_UPDATED}</lastmod><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n")
    open(os.path.join(ROOT, ".nojekyll"), "w").write("")

    lines = [
        f"# {SITE['personEn']}（{SITE['personJa']}） / {SITE['brand']}",
        "",
        f"> {SITE['description']['ja']}",
        f"> {SITE['description']['en']}",
        "",
        "## Names / 名前表記",
        f"- {SITE['personEn']}（{SITE['personJa']}）: legal name, used for all business communication / 本名・業務用の名義",
        f"- {SITE['alternateName']}: creative name for creative work and social media / 創作・SNS用のクリエイティブネーム",
        "",
        "## Services / できること",
    ]
    for s in D["services"]:
        lines.append(f"- {s['title']['en']} / {s['title']['ja']}: {s['text']['en']}")
    lines += ["", "## Key pages", f"- [Top]({BASE}): profile, services, security, FAQ, contact", f"- [All works]({BASE}works.html)", f"- [Updates]({BASE}news.html)", "", "## Featured works"]
    for w in WORKS:
        if w.get("latest") or w.get("ecCard"):
            u = w.get("url") or BASE + "works.html#" + w["id"]
            lines.append(f"- [{w['title']['en']}]({u}): {w['summary']['en']}")
    lines += ["", "## Notes", "- E-commerce sites (TABITOKI MARKET, C.C.Donuts) are fictional demo sites built for practice and proposals; no real payments occur.", "- Security measures are described only at a high level on purpose.", "", "## Contact", f"- Email: {SITE['email']}", f"- Last updated: {LAST_UPDATED}"]
    open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote sitemap.xml robots.txt llms.txt")


if __name__ == "__main__":
    build_index()
    build_works()
    build_news()
    build_extras()
    print("done. last updated:", LAST_UPDATED)
