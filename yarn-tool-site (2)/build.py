#!/usr/bin/env python3
"""Static site generator for the Yarn Yardage Calculator tool site.

Reads projects.json (tool pages) and guides.json (articles), pulls the
yardage table from calculator.js, and writes every page, sitemap.xml
and robots.txt. All output is static HTML — Cloudflare Pages ready.

SEO: unique titles (50-60 chars), meta descriptions (150-160 chars),
canonical + OG + Twitter tags, JSON-LD (FAQPage / BreadcrumbList /
WebApplication), semantic HTML5, single H1 per page.

To publish: set SITE_URL below to the real domain (no trailing slash),
run `python3 build.py`, then re-zip and deploy.
"""
import json, html, os, re, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

# ============ SITE CONFIG — edit these before publishing ============
SITE_URL = "https://www.example.com"   # <-- replace with the real domain, no trailing slash
SITE_NAME = "YarnYardage"
BRAND = "Yarn<span>Yardage</span>"
THEME_COLOR = "#2b2118"
CONTACT_EMAIL = "hello@example.com"    # <-- replace with a real contact address
# =====================================================================

with open(os.path.join(ROOT, "projects.json"), encoding="utf-8") as f:
    PROJECTS = json.load(f)
with open(os.path.join(ROOT, "guides.json"), encoding="utf-8") as f:
    GUIDES = json.load(f)


def load_yardage_table():
    """Extract PROJECT_YARDAGE from calculator.js so charts always match the tool."""
    src = open(os.path.join(ROOT, "calculator.js"), encoding="utf-8").read()
    m = re.search(r"var PROJECT_YARDAGE = (\{.*?\n\});", src, re.S)
    if not m:
        raise RuntimeError("PROJECT_YARDAGE not found in calculator.js")
    js = m.group(1)
    js = re.sub(r"([{,])\s*([A-Za-z0-9_-]+)\s*:", r'\1"\2":', js)
    return json.loads(js)


YARDAGE = load_yardage_table()

WEIGHT_COLS = [("Lace (0)", "lace"), ("Fingering (1)", "fingering"), ("Sport (2)", "sport"),
               ("DK (3)", "dk"), ("Worsted (4)", "worsted"), ("Bulky (5)", "bulky"),
               ("Super Bulky (6)", "superbulky")]

WEIGHT_REF = [
    ("Lace (0)", "600–800 yds / 100 g", "Lace shawls, fine doilies"),
    ("Super Fine / Fingering (1)", "400–460 yds / 100 g", "Socks, lightweight shawls"),
    ("Fine / Sport (2)", "300–350 yds / 100 g", "Baby garments, light sweaters"),
    ("Light / DK (3)", "250–300 yds / 100 g", "Sweaters, baby blankets"),
    ("Medium / Worsted (4)", "200–230 yds / 100 g", "Sweaters, blankets, scarves"),
    ("Bulky (5)", "100–130 yds / 100 g", "Quick knits, chunky blankets"),
    ("Super Bulky (6)", "60–80 yds / 100 g", "Arm knitting, rugs"),
]

INDEX_FAQS = [
    ("Does crochet use more yarn than knitting?",
     "Yes — crochet uses roughly 25–30% more yarn than knitting for the same finished size, because crochet stitches are taller and denser."),
    ("How many yards are in a skein of yarn?",
     "It depends on the weight: roughly 700 yards for lace, 440 for fingering, 330 for sport, 280 for DK, 220 for worsted, 120 for bulky, and 70 for super bulky per 100 g. Always check your yarn label — the calculator lets you enter the exact number."),
    ("Should I buy extra yarn?",
     "Yes. Buy at least one extra skein, and buy everything from the same dye lot — colors can vary slightly between batches."),
    ("What does yarn weight mean?",
     "Yarn weight is the thickness of the strand, numbered 0 (lace) to 7 (jumbo) by the Craft Yarn Council. It is not the physical weight of the skein — it is the thickness category."),
]

GUIDES_FAQS = [
    ("Are these guides free?", "Yes — every guide on YarnYardage is free, no account needed."),
    ("Do the guides work with the calculator?",
     "Yes. Each guide links to the relevant calculator pages so you can turn what you learn into exact yardage and skein counts."),
    ("Can I share these guides?", "Yes — link to them freely. Copying the full text to another site is not permitted."),
]

# ---------------------------------------------------------------- helpers

def esc(s):
    return html.escape(s, quote=True)


def full_url(path):
    return SITE_URL.rstrip("/") + "/" + path.lstrip("/")


def seo_title(h1):
    t = f"{h1} | YarnYardage Calculator"
    if len(t) > 60:
        t = f"{h1} | YarnYardage"
    if len(t) < 50:
        t = f"{h1} | Free YarnYardage Calculator"
    return t


def seo_meta(desc, tail=" Use the free calculator for exact yardage and skein counts for any yarn weight."):
    desc = (desc.strip() + tail).strip()
    if len(desc) > 160:
        cut = desc[:160]
        sp = cut.rfind(" ", 150, 160)  # keep the cut inside 150-160 chars
        if sp == -1:
            sp = cut.rfind(" ", 0, 150)
        desc = cut[:sp].rstrip(".,;:") + "…"
    return desc


def faq_ld(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"] if isinstance(f, dict) else f[0],
         "acceptedAnswer": {"@type": "Answer", "text": f["a"] if isinstance(f, dict) else f[1]}}
        for f in faqs]}


def breadcrumb_ld(crumbs):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": full_url(p)}
        for i, (n, p) in enumerate(crumbs)]}


def ad_slot(label):
    # Placeholder for a responsive AdSense unit. Replace this div with the real
    # <ins class="adsbygoogle"> snippet. Reserved height prevents layout shift.
    return (f'<!-- AdSense: {label} (responsive) — paste your ad unit code here -->\n'
            f'<div class="ad-slot" role="complementary" aria-label="Advertisement">'
            f'<span>Advertisement</span></div>')


def calc_widget(preset=None):
    attr = f' data-preset-project="{preset}"' if preset else ""
    return f"""<div class="calc-card" id="yarn-calc"{attr}>
  <div class="fields">
    <div class="field">
      <label for="f-project">Project</label>
      <select data-field="project" id="f-project"></select>
    </div>
    <div class="field">
      <label for="f-weight">Yarn weight</label>
      <select data-field="weight" id="f-weight"></select>
    </div>
    <div class="field">
      <label for="f-skein">Yards per skein (from your label)</label>
      <input data-field="skein" id="f-skein" type="number" min="1" step="1" inputmode="numeric">
      <div class="hint">Auto-filled for the chosen weight — change it to match your yarn.</div>
    </div>
    <div class="field">
      <label for="f-buffer">Safety buffer (%)</label>
      <input data-field="buffer" id="f-buffer" type="number" min="0" max="50" step="1" value="10" inputmode="numeric">
      <div class="hint">10–15% covers gauge differences and mistakes.</div>
    </div>
  </div>
  <div data-field="result" aria-live="polite"></div>
</div>"""


def faq_block(faqs):
    items = "\n".join(
        f"<details><summary>{esc(f['q'] if isinstance(f, dict) else f[0])}</summary>"
        f"<p>{esc(f['a'] if isinstance(f, dict) else f[1])}</p></details>"
        for f in faqs)
    return f'<div class="faq">\n<h2>Frequently asked questions</h2>\n{items}\n</div>'


def head(title, meta, path, css_rel, home, guides_home, ld_objects=None, og_type="website"):
    canon = full_url(path)
    ld_html = "\n".join(
        '<script type="application/ld+json">\n' + json.dumps(o, indent=2) + '\n</script>'
        for o in (ld_objects or []))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta)}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="{THEME_COLOR}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(meta)}">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(meta)}">
<link rel="stylesheet" href="{css_rel}">
{ld_html}
</head>
<body>
<a class="skip-link" href="#main-content">Skip to main content</a>
<header class="site"><div class="wrap">
<a class="brand" href="{home}">{BRAND}</a>
<nav class="top" aria-label="Main navigation"><a href="{home}">Calculator</a><a href="{guides_home}">Guides</a><a href="{home}#projects">Projects</a></nav>
</div></header>
<main id="main-content"><div class="wrap">
"""


def foot(home, guides_home, js_rel):
    year = datetime.date.today().year
    return f"""</div></main>
<footer class="site"><div class="wrap">
<nav class="foot-links" aria-label="Footer navigation"><a href="{home}">Calculator</a><a href="{guides_home}">Guides</a><a href="{home}#projects">All projects</a><a href="{home.rsplit('/', 1)[0] + '/' if '/' in home else ''}privacy-policy.html">Privacy Policy</a><a href="{home.rsplit('/', 1)[0] + '/' if '/' in home else ''}terms.html">Terms</a><a href="{home.rsplit('/', 1)[0] + '/' if '/' in home else ''}about.html">About</a><a href="{home.rsplit('/', 1)[0] + '/' if '/' in home else ''}contact.html">Contact</a></nav>
<p class="disclaimer">Yardage figures are planning estimates for average-size projects and typical gauges. Your gauge, stitch pattern, and finished size change the numbers — always buy an extra skein, and check your pattern's yardage first.</p>
<p class="disclaimer">Disclosure: {SITE_NAME} is reader-supported. We display ads served by Google AdSense and may earn a commission on qualifying purchases made through links on this site.</p>
<p>&copy; {year} {SITE_NAME}. Free yarn yardage calculator.</p>
</div></footer>
<div id="cookie-banner" class="cookie-banner" role="dialog" aria-label="Cookie consent" hidden>
<p>We use cookies to run this site and to serve ads via Google AdSense and its partners. See our <a href="{home.rsplit('/', 1)[0] + '/' if '/' in home else ''}privacy-policy.html">Privacy Policy</a>.</p>
<button type="button" id="cookie-ok">Got it</button>
</div>
<script>
(function(){{var b=document.getElementById('cookie-banner');
try{{if(!localStorage.getItem('yy_consent')){{b.hidden=false;}}}}catch(e){{b.hidden=false;}}
document.getElementById('cookie-ok').addEventListener('click',function(){{
try{{localStorage.setItem('yy_consent','1');}}catch(e){{}}b.hidden=true;}});}})();
</script>
<script src="{js_rel}"></script>
</body>
</html>"""


def policy_dir(home):
    # directory prefix for policy pages relative to the current page
    return home.rsplit("/", 1)[0] + "/" if "/" in home else ""

# ---------------------------------------------------------------- pages

def build_index():
    cards = "\n".join(
        f'<a href="projects/{p["slug"]}.html">{esc(p["h1"])}'
        f'<small>{esc(p["dims"])}</small></a>'
        for p in PROJECTS
    )
    weight_rows = "\n".join(
        f"<tr><td>{w}</td><td>{y}</td><td>{u}</td></tr>" for w, y, u in WEIGHT_REF
    )
    guide_cards = "\n".join(
        f'<a href="guides/{g["slug"]}.html"><strong>{esc(g["h1"])}</strong>'
        f'<small>{esc(g["lede"][:110])}…</small></a>'
        for g in GUIDES[:6]
    )
    webapp = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": "Yarn Yardage Calculator", "url": full_url("index.html"),
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": "Free calculator that estimates how much yarn a knitting or crochet project needs, in yards and skeins."}
    body = f"""
<h1>Yarn Yardage Calculator</h1>
<p class="lede">Find out exactly how much yarn your project needs — yardage and skein counts for knit and crochet, in seconds.</p>
{ad_slot("in-content: after intro")}
{calc_widget()}
{ad_slot("in-content: after calculator")}
<h2 id="projects">Yardage by project</h2>
<p>Pick your project for detailed yardage charts, skein counts, and FAQs:</p>
<div class="project-grid">
{cards}
</div>
<h2 id="weights">Standard yarn weights</h2>
<p>The Craft Yarn Council standardizes yarn by thickness. Thicker yarn needs less yardage for the same project — but each skein also holds fewer yards.</p>
<div class="table-scroll"><table class="data">
<tr><th>Weight</th><th>Yards per 100 g</th><th>Common uses</th></tr>
{weight_rows}
</table></div>
<h2>How to calculate yarn yardage</h2>
<p><strong>Step 1 — total yardage:</strong> multiply the skeins your pattern calls for by the yardage on the pattern's yarn label. <strong>Step 2 — your yarn:</strong> divide that total by the yardage per skein of the yarn you actually bought. <strong>Step 3:</strong> round up and add a 10–15% buffer.</p>
<h2>Yarn guides &amp; tutorials</h2>
<p>Learn the skills behind the numbers — from <a href="guides/yarn-weight-chart-explained.html">reading yarn weight charts</a> to <a href="guides/how-to-substitute-yarn-in-a-pattern.html">substituting yarn in patterns</a>:</p>
<div class="guide-grid">
{guide_cards}
</div>
<p><a href="guides/index.html">Browse all yarn guides &rarr;</a></p>
{ad_slot("in-content: before FAQs")}
{faq_block(INDEX_FAQS)}
"""
    title = "Yarn Yardage Calculator — How Much Yarn Do I Need?"
    meta = "Free yarn yardage calculator: find out how much yarn you need for blankets, sweaters, scarves, hats and more, with per-weight yardage charts and skein counts."
    return (head(title, meta, "index.html", "styles.css", "index.html", "guides/index.html",
                 ld_objects=[webapp, faq_ld([{"q": q, "a": a} for q, a in INDEX_FAQS])])
            + body + foot("index.html", "guides/index.html", "calculator.js"),
            title, meta)


def build_project(p, related):
    rows = []
    yd = YARDAGE[p["key"]]
    for wname, wid in WEIGHT_COLS:
        v = yd.get(wid)
        rows.append(f"<tr><td>{wname}</td><td>{f'{v:,} yds' if v else '—'}</td></tr>")
    rel_list = "\n".join(
        f'<li><a href="{q["slug"]}.html">{esc(q["h1"])}</a></li>' for q in related
    )
    secondary = ", ".join(esc(s) for s in p["secondary"])
    faqs = [{"q": f["q"], "a": f["a"]} for f in p["faqs"]]
    crumbs = [("Home", "index.html"), (p["h1"], f"projects/{p['slug']}.html")]
    body = f"""
<p class="breadcrumb"><a href="../index.html">Home</a> &rsaquo; {esc(p["keyword"]).title()}</p>
<h1>{esc(p["h1"])}</h1>
<p class="lede">Project size: {esc(p["dims"])}</p>
{ad_slot("in-content: after intro")}
<div class="answer-box"><strong>Quick answer:</strong> {esc(p["intro"][0])}</div>
<p>{esc(p["intro"][1])}</p>
<h2>Calculate your exact yardage</h2>
{calc_widget(preset=p["key"])}
{ad_slot("in-content: after calculator")}
<h2>Yardage chart</h2>
<div class="table-scroll"><table class="data">
<tr><th>Yarn weight</th><th>Estimated yardage</th></tr>
{chr(10).join(rows)}
</table></div>
<p>Also searched as: {secondary}.</p>
{ad_slot("in-content: before FAQs")}
{faq_block(faqs)}
<div class="related">
<h2>Related projects</h2>
<ul>
{rel_list}
</ul>
</div>
<p><a href="../index.html">&larr; Back to the yarn yardage calculator</a></p>
"""
    title = seo_title(p["h1"])
    meta = seo_meta(p["meta_desc"])
    return (head(title, meta, f"projects/{p['slug']}.html", "../styles.css", "../index.html",
                 "../guides/index.html",
                 ld_objects=[faq_ld(faqs), breadcrumb_ld(crumbs)])
            + body + foot("../index.html", "../guides/index.html", "../calculator.js"),
            title, meta)


def build_guides_index():
    cards = "\n".join(
        f'<a href="{g["slug"]}.html"><strong>{esc(g["h1"])}</strong>'
        f'<small>{esc(g["lede"][:120])}…</small></a>'
        for g in GUIDES
    )
    body = f"""
<p class="breadcrumb"><a href="../index.html">Home</a> &rsaquo; Guides</p>
<h1>Yarn Guides &amp; Tutorials</h1>
<p class="lede">Practical, no-fluff guides to yarn weights, labels, substitution math, and project planning — each one paired with the <a href="../index.html">free yardage calculator</a>.</p>
{ad_slot("in-content: after intro")}
<div class="guide-grid">
{cards}
</div>
{ad_slot("in-content: mid-page")}
{faq_block([{"q": q, "a": a} for q, a in GUIDES_FAQS])}
"""
    title = "Free Yarn Guides & Tutorials: Charts, Tips & How-Tos"
    meta = seo_meta("Free yarn guides and tutorials: yarn weight charts, how to read yarn labels, substitution math, buffer rules, and project planning tips.",
                    tail=" Written for knitters and crocheters, beginners and beyond.")
    crumbs = [("Home", "index.html"), ("Guides", "guides/index.html")]
    return (head(title, meta, "guides/index.html", "../styles.css", "../index.html",
                 "index.html",
                 ld_objects=[breadcrumb_ld(crumbs),
                             faq_ld([{"q": q, "a": a} for q, a in GUIDES_FAQS])])
            + body + foot("../index.html", "index.html", "../calculator.js"),
            title, meta)


def build_guide(g, related):
    sections_html = []
    for i, s in enumerate(g["sections"]):
        sections_html.append(f"<h2>{esc(s['h2'])}</h2>\n{s['html']}")
        if i == 1:
            sections_html.append(ad_slot("in-content: mid-article"))
    faqs = [{"q": f["q"], "a": f["a"]} for f in g["faqs"]]
    rel = "\n".join(
        f'<li><a href="{r["slug"]}.html">{esc(r["h1"])}</a></li>' for r in related
    )
    crumbs = [("Home", "index.html"), ("Guides", "guides/index.html"),
              (g["h1"], f"guides/{g['slug']}.html")]
    body = f"""
<p class="breadcrumb"><a href="../index.html">Home</a> &rsaquo; <a href="index.html">Guides</a> &rsaquo; {esc(g["h1"])}</p>
<article>
<h1>{esc(g["h1"])}</h1>
<p class="lede">{esc(g["lede"])}</p>
{ad_slot("in-content: after intro")}
{chr(10).join(sections_html)}
{ad_slot("in-content: before FAQs")}
{faq_block(faqs)}
<div class="related">
<h2>More yarn guides</h2>
<ul>
{rel}
</ul>
</div>
<p><a href="../index.html">Try the free yarn yardage calculator &rarr;</a></p>
</article>
"""
    title = g["title"]
    meta = g["meta_desc"]
    return (head(title, meta, f"guides/{g['slug']}.html", "../styles.css", "../index.html",
                 "index.html", ld_objects=[faq_ld(faqs), breadcrumb_ld(crumbs)],
                 og_type="article")
            + body + foot("../index.html", "index.html", "../calculator.js"),
            title, meta)


POLICY_PAGES = {
    "privacy-policy": {
        "h1": "Privacy Policy",
        "title": "YarnYardage Privacy Policy: Cookies, Ads & Your Data",
        "meta": "Privacy Policy for YarnYardage: what data we collect (almost none), how cookies and Google AdSense advertising work, and how to opt out of personalized ads.",
        "body": """<div class="prose">
<h2>What we collect</h2>
<p>YarnYardage does not require an account and does not collect names, email addresses, or other personal information through the calculator. The calculator runs entirely in your browser — your inputs never leave your device.</p>
<h2>Cookies</h2>
<p>We use a cookie (via your browser's local storage) to remember that you dismissed the cookie notice. We do not set tracking cookies ourselves.</p>
<h2>Advertising and third-party vendors</h2>
<p>We show ads served by Google AdSense. Google and its partners use cookies to serve ads based on your prior visits to this and other websites. Google's use of advertising cookies enables it and its partners to serve ads based on your visit to our site and other sites on the Internet. You may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" rel="nofollow">Google Ads Settings</a> or <a href="https://optout.aboutads.info/" rel="nofollow">aboutads.info</a>. Learn more in Google's <a href="https://policies.google.com/technologies/ads" rel="nofollow">advertising privacy policy</a>.</p>
<h2>Analytics</h2>
<p>If we enable privacy-friendly analytics in the future, this policy will be updated to describe it.</p>
<h2>Contact</h2>
<p>Questions about this policy: <a href="contact.html">contact us</a>.</p>
</div>""",
    },
    "terms": {
        "h1": "Terms of Service",
        "title": "YarnYardage Terms of Service: Use, Content & Liability",
        "meta": "Terms of Service for YarnYardage: acceptable use of the calculator, accuracy of yardage estimates, intellectual property rules, and limitation of liability.",
        "body": """<div class="prose">
<h2>Use of the calculator</h2>
<p>Yardage figures on this site are planning estimates for average-size projects and typical gauges. They are not guarantees — your gauge, stitch pattern, and finished size change the actual yardage required. Always check your pattern and buy extra yarn.</p>
<h2>Acceptable use</h2>
<p>You may use this site for personal, non-commercial purposes. Do not scrape, republish, or redistribute substantial portions of the site's content without permission.</p>
<h2>Intellectual property</h2>
<p>All text, yardage tables, and code on YarnYardage are owned by the site operator unless otherwise noted.</p>
<h2>Limitation of liability</h2>
<p>This site is provided "as is" without warranties of any kind. We are not liable for yarn purchased based on our estimates.</p>
<h2>Changes</h2>
<p>We may update these terms at any time; continued use of the site constitutes acceptance.</p>
</div>""",
    },
    "about": {
        "h1": "About YarnYardage",
        "title": "About YarnYardage — Free Yarn Calculator, Charts & Guides",
        "meta": "About YarnYardage: a free yarn yardage calculator plus practical knitting and crochet guides — built to answer 'how much yarn do I need?' in seconds. Start here.",
        "body": """<div class="prose">
<p>YarnYardage started with a simple frustration: "how much yarn do I need?" is one of the most-asked questions in knitting and crochet, and the answers were scattered across forums, charts, and guesswork.</p>
<p>This site gives you a straight answer. Pick your project and yarn weight in the <a href="index.html">free calculator</a> and get yardage plus skein counts in seconds — with a built-in buffer for gauge differences. The <a href="guides/index.html">guides</a> teach the skills behind the numbers: reading labels, substituting yarn, and planning big projects like temperature blankets.</p>
<p>Everything here is free. The site is supported by advertising, which keeps the calculator free for everyone.</p>
</div>""",
    },
    "contact": {
        "h1": "Contact",
        "title": "Contact YarnYardage: Questions, Errors & Advertising",
        "meta": "Contact YarnYardage: report an error in a yardage chart, suggest a new calculator feature or project, or ask about advertising. We reply within a few days.",
        "body": f"""<div class="prose">
<p>Spotted an error in a yardage chart? Want a project added to the calculator? Get in touch:</p>
<p><strong>Email:</strong> <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
<p>We read every message and typically reply within a few days. For advertising inquiries, please include "Advertising" in the subject line.</p>
</div>""",
    },
}


def build_policy(slug):
    p = POLICY_PAGES[slug]
    crumbs = [("Home", "index.html"), (p["h1"], f"{slug}.html")]
    body = f"""
<p class="breadcrumb"><a href="index.html">Home</a> &rsaquo; {esc(p["h1"])}</p>
<h1>{esc(p["h1"])}</h1>
{p["body"]}
"""
    meta = seo_meta(p["meta"], tail="")
    return (head(p["title"], meta, f"{slug}.html", "styles.css", "index.html",
                 "guides/index.html", ld_objects=[breadcrumb_ld(crumbs)])
            + body + foot("index.html", "guides/index.html", "calculator.js"),
            p["title"], meta)


def build_robots():
    return f"""User-agent: *
Allow: /

Sitemap: {full_url("sitemap.xml")}
"""


def build_sitemap(urls):
    today = datetime.date.today().isoformat()
    items = "\n".join(
        f"  <url><loc>{full_url(u)}</loc><lastmod>{today}</lastmod></url>" for u in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>
"""


def check(title, meta, label, problems):
    if not (50 <= len(title) <= 60):
        problems.append(f"{label}: title {len(title)} chars — {title!r}")
    if not (150 <= len(meta) <= 160):
        problems.append(f"{label}: meta {len(meta)} chars")


def main():
    problems = []
    os.makedirs(os.path.join(ROOT, "projects"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "guides"), exist_ok=True)
    urls = []

    def write_page(rel, html_text, title, meta):
        check(title, meta, rel, problems)
        # JSON-LD must parse
        for m in re.finditer(r'<script type="application/ld\+json">\n(.*?)\n</script>', html_text, re.S):
            try:
                json.loads(m.group(1))
            except json.JSONDecodeError as e:
                problems.append(f"{rel}: JSON-LD invalid — {e}")
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as f:
            f.write(html_text)
        urls.append(rel)

    html_text, t, m = build_index()
    write_page("index.html", html_text, t, m)

    for i, p in enumerate(PROJECTS):
        others = [q for q in PROJECTS if q["slug"] != p["slug"]]
        related = others[i:i + 8] if i + 8 <= len(others) else others[:8]
        html_text, t, m = build_project(p, related)
        write_page(f"projects/{p['slug']}.html", html_text, t, m)

    html_text, t, m = build_guides_index()
    write_page("guides/index.html", html_text, t, m)
    for i, g in enumerate(GUIDES):
        others = [x for x in GUIDES if x["slug"] != g["slug"]]
        related = others[i:i + 4] if i + 4 <= len(others) else others[:4]
        html_text, t, m = build_guide(g, related)
        write_page(f"guides/{g['slug']}.html", html_text, t, m)

    for slug in POLICY_PAGES:
        html_text, t, m = build_policy(slug)
        write_page(f"{slug}.html", html_text, t, m)

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(urls))
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(build_robots())

    print(f"Built {len(urls)} pages + sitemap.xml + robots.txt")
    if problems:
        print("PROBLEMS:")
        for pr in problems:
            print(" -", pr)
    else:
        print("All SEO checks passed (titles 50-60, metas 150-160, JSON-LD valid).")


if __name__ == "__main__":
    main()
