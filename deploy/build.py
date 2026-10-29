"""Build the site: one /<code>/ page per language declared in deploy/langs.json. Generated from langs.json (site, indexable, locale, crawlers): language switcher, hreflang, canonical, robots meta, Open Graph/Twitter tags, JSON-LD URLs and inLanguage, robots.txt, sitemap.xml, llms.txt, vercel.json. Fails loudly when an expected element is missing."""

import hashlib, html as htmllib, json, os, pathlib, re, shutil, struct, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import blog  # noqa: E402

SRC = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1])
CONF = json.loads((SRC / "deploy" / "langs.json").read_text())
if os.environ.get("WS_SITE"):
    CONF["site"] = os.environ["WS_SITE"].rstrip("/")
if os.environ.get("WS_GA") is not None:
    CONF.setdefault("analytics", {})["ga4"] = (
        "" if os.environ["WS_GA"].lower() in ("", "0", "off") else os.environ["WS_GA"]
    )
if os.environ.get("WS_INDEXABLE"):
    CONF["indexable"] = os.environ["WS_INDEXABLE"].lower() in ("1", "true", "yes")

SWITCH_CSS = (
    '<style id="lang-sw">.lang-m b{overflow:hidden;padding:0;background:none}'
    ".lang-m b img,.lang-b img{display:block;width:100%;height:100%;object-fit:cover;border-radius:4px}"
    ".lang-b .lf{display:block;flex:none;width:20px;height:15px}.lang-b .lf img{border-radius:3px}"
    ".mlangs{flex-wrap:wrap}.mlangs a{flex:1 0 21%;display:flex!important;align-items:center;justify-content:center;gap:6px}"
    ".mlangs img,footer .langs img{width:18px;height:13px;border-radius:2px;object-fit:cover}footer .langs{flex-wrap:wrap}"
    "footer .langs a{display:inline-flex;align-items:center;gap:6px}</style>"
)

CREDIT_CSS = (
    '<style id="credit">footer .credit{white-space:nowrap}'
    "footer .credit a{color:inherit;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}"
    "footer .credit a:hover{color:var(--tx)}"
    "@media (max-width:600px){footer .credit a{display:inline-block;padding:13px 4px;margin:-13px -4px}}</style>"
)


def footer_credit(html, lang):
    """The site credit at the end of the footer's legal line: link from langs.json "credit", label from the language's ui.credit."""
    credit = CONF.get("credit")
    if not credit:
        return html
    label = lang["ui"].get("credit")
    if not label:
        die(lang["code"], 'langs.json has a "credit" link but no ui.credit label for this language')
    legal = re.compile(r'(<div class="bot">\s*<span>)([^<]*)(</span>)')
    if len(legal.findall(html)) != 1:
        die(lang["code"], 'footer legal line <div class="bot"><span>...</span> not found for the credit')
    link = f'<span class="credit">{label} <a href="{credit["url"]}" rel="noopener">{credit["name"]}</a></span>'
    html = legal.sub(lambda m: f"{m[1]}{m[2]} · {link}{m[3]}", html, count=1)
    return html.replace("</head>", CREDIT_CSS + "</head>", 1)


def die(page, msg):
    sys.exit(f"{page}: {msg}")


def norm(s):
    s = htmllib.unescape(re.sub(r"<[^>]+>", "", s)).replace("\u2060", "")
    return re.sub(r"[\s\u00a0\u202f]+", " ", s).strip()


def img_size(path):
    d = path.read_bytes()
    if d[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", d[16:24])
    i = 2
    while d[:2] == b"\xff\xd8" and i < len(d):
        m = d[i + 1]
        n = struct.unpack(">H", d[i + 2 : i + 4])[0]
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", d[i + 5 : i + 9])
            return w, h
        i += 2 + n
    return None


def flag(cc, w, h):
    return (
        f'<img class="flag" src="/img/flags/{cc}.webp" alt="" width="{w}" height="{h}">'
    )


def replace_inner(html, pattern, inner, page):
    m = re.search(pattern, html, flags=re.S)
    if not m:
        sys.exit(f"{page}: language switcher not found: {pattern[:40]}")
    return html[: m.start()] + m.group(1) + inner + m.group(2) + html[m.end() :]


SOCIAL_ICONS = {
    "wikidata.org": None,
    "instagram.com": (
        "Instagram",
        '<path d="M12 2.2c3.2 0 3.6 0 4.8.1 3.3.1 4.8 1.7 4.9 4.9.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 3.2-1.7 4.8-4.9 4.9-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-3.3-.1-4.8-1.7-4.9-4.9C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8C2.4 3.9 3.9 2.4 7.2 2.3 8.4 2.2 8.8 2.2 12 2.2zm0 4.8a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 8.2a3.2 3.2 0 1 1 0-6.4 3.2 3.2 0 0 1 0 6.4zm5.2-9.6a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4z"/>',
    ),
    "facebook.com": (
        "Facebook",
        '<path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/>',
    ),
    "linkedin.com": (
        "LinkedIn",
        '<path d="M20.4 20.5h-3.6v-5.6c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9v5.7H9.3V9h3.4v1.6c.5-.9 1.6-1.8 3.4-1.8 3.6 0 4.3 2.4 4.3 5.5v6.2zM5.3 7.4a2.1 2.1 0 1 1 0-4.2 2.1 2.1 0 0 1 0 4.2zm1.8 13.1H3.5V9h3.6v11.5zM22.2 0H1.8C.8 0 0 .8 0 1.7v20.6c0 .9.8 1.7 1.8 1.7h20.4c1 0 1.8-.8 1.8-1.7V1.7C24 .8 23.2 0 22.2 0z"/>',
    ),
    "youtube.com": (
        "YouTube",
        '<path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z"/>',
    ),
    "tiktok.com": (
        "TikTok",
        '<path d="M19.6 6.7a4.8 4.8 0 0 1-3.8-4.2V2h-3.4v13.7a2.9 2.9 0 1 1-2-2.7V9.5a6.3 6.3 0 1 0 5.4 6.2V8.8a8.2 8.2 0 0 0 4.8 1.5V6.9a4.8 4.8 0 0 1-1-.2z"/>',
    ),
}


def social_links(html, page):
    if "{{SOCIAL}}" not in html:
        return html
    links = []
    for url in CONF["org"]["sameAs"]:
        host = re.sub(r"^www\.", "", url.split("/")[2])
        if host not in SOCIAL_ICONS:
            die(
                page,
                f"no footer icon for social link {url}; add {host} to SOCIAL_ICONS",
            )
        if SOCIAL_ICONS[host] is None:
            continue
        name, path = SOCIAL_ICONS[host]
        links.append(
            f'<a href="{url}" rel="me noopener" target="_blank" aria-label="{name}">'
            f'<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">{path}</svg></a>'
        )
    return html.replace("{{SOCIAL}}", f'<div class="social">{"".join(links)}</div>')


def localize(html, page, live):
    site = CONF["site"]
    links = "".join(
        f'<link rel="alternate" hreflang="{h}" href="{site}/{l["code"]}/">\n'
        for l in live
        for h in l["hreflang"]
    )
    links += f'<link rel="alternate" hreflang="x-default" href="{site}/{CONF["default"]}/">\n'
    html, n = re.subn(
        r'(?:<link rel="alternate" hreflang="[^"]+" href="[^"]+">\s*)+',
        lambda _: links,
        html,
        count=1,
    )
    if n != 1:
        sys.exit(f"{page}: hreflang links not found")

    def attrs(l):
        cur = ' aria-current="page"' if l["code"] == page else ""
        return f'href="/{l["code"]}/" hreflang="{l["code"]}" lang="{l["code"]}"{cur}'

    menu = "".join(
        f"<li><a {attrs(l)}><b>{flag(l['flag'], 30, 22)}</b>{l['name']}</a></li>"
        for l in live
    )
    chips = "".join(
        f"<a {attrs(l)}>{flag(l['flag'], 18, 13)}{l['code'].upper()}</a>" for l in live
    )
    codes = json.dumps([l["code"] for l in live])
    html, n = re.subn(
        r'"availableLanguage":\[[^\]]*\]',
        lambda _: f'"availableLanguage":{codes}',
        html,
    )
    if n < 1:
        sys.exit(f"{page}: availableLanguage not found")
    me = next(l for l in live if l["code"] == page)
    html, n = re.subn(
        r'(<button class="lang-b"[^>]*aria-label="[^":]*:\s?)[^"]*(">.*?<span>)[^<]*(</span>)',
        lambda m: (
            m.group(1)
            + f"{me['name']}, {page.upper()}"
            + re.sub(
                r"<svg.*?</svg>",
                lambda _: f'<span class="lf">{flag(me["flag"], 20, 15)}</span>',
                m.group(2),
                count=1,
                flags=re.S,
            )
            + page.upper()
            + m.group(3)
        ),
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        sys.exit(f"{page}: language button not found")
    html, n = re.subn(
        r'(<a class="logo" href=")/[a-z]{2}/(")', rf"\g<1>/{page}/\g<2>", html
    )
    if n < 1:
        sys.exit(f"{page}: logo link not found")
    html = replace_inner(
        html, r'(<ul class="lang-m" id="langm" hidden>).*?(</ul>)', menu, page
    )
    html = replace_inner(html, r'(<div class="mlangs"[^>]*>).*?(</div>)', chips, page)
    html = replace_inner(html, r'(<nav class="langs"[^>]*>).*?(</nav>)', chips, page)
    return html.replace("</head>", SWITCH_CSS + "</head>", 1)


def seo(html, page, live):
    site, indexable = CONF["site"], CONF["indexable"]
    me = next(l for l in live if l["code"] == page)
    url = f"{site}/{page}/"
    head = html.split("</head>", 1)[0]

    def need(pattern, what):
        m = re.search(pattern, head, re.S)
        if not m or not m.group(1).strip():
            die(page, f"missing {what}")
        return htmllib.unescape(m.group(1))

    title = need(r"<title>(.*?)</title>", "title")
    desc = need(r'<meta name="description" content="([^"]*)"', "meta description")
    # Social previews repeat the title and the meta description (one source per language page).
    ogt, ogd = title, desc
    html = re.sub(r'<meta property="og:(?:title|description)" content="[^"]*">\n?', "", html)
    need(r'<meta (name="twitter:card") content="summary_large_image"', "twitter:card")
    if len(re.findall(r"<h1[ >]", html)) != 1:
        die(page, "expected exactly one h1")
    if not re.search(rf'<html lang="{page}[-"]', html):
        die(page, "html lang does not match page code")
    ogimg_file = SRC / "img" / "og" / f"{page}.jpg"
    if not ogimg_file.exists() or img_size(ogimg_file) != (1200, 630):
        die(
            page,
            f"{ogimg_file.name}: og image missing or not 1200x630 (run deploy/og.js)",
        )
    ogimg = site + og_image_path(page)
    q = lambda v: htmllib.escape(v, quote=True)
    locs = [loc for l in live for loc in l["locale"]]
    html, n = re.subn(r'<link rel="icon"[^>]*>', lambda _: icon_tags(), html, count=1)
    if n != 1:
        die(page, "icon link not found")
    tags = [f'<link rel="canonical" href="{url}">']
    if not indexable:
        tags.append('<meta name="robots" content="noindex, nofollow">')
    tags += [
        f'<meta property="og:title" content="{q(ogt)}">',
        f'<meta property="og:description" content="{q(ogd)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:locale" content="{me["locale"][0]}">',
    ]
    tags += [
        f'<meta property="og:locale:alternate" content="{x}">'
        for x in locs
        if x != me["locale"][0]
    ]
    tags += [
        f'<meta property="og:image" content="{ogimg}">',
        '<meta property="og:image:type" content="image/jpeg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{q(ogt)}">',
        f'<meta name="twitter:title" content="{q(ogt)}">',
        f'<meta name="twitter:description" content="{q(ogd)}">',
        f'<meta name="twitter:image" content="{ogimg}">',
    ]
    html, n = re.subn(
        r'(<meta name="description" content="[^"]*">)',
        lambda m: m.group(1) + "\n" + "\n".join(tags),
        html,
        count=1,
    )
    if n != 1:
        die(page, "description tag not found for SEO block")

    ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if len(ld) != 1:
        die(page, "expected exactly one JSON-LD block")
    data = json.loads(ld[0].replace("{{SITE}}", site))
    nodes = {n["@type"]: n for n in data["@graph"]}
    for t in ("Organization", "WebSite", "WebApplication", "FAQPage"):
        if t not in nodes:
            die(page, f"JSON-LD missing {t}")
    inlang = me.get("inLanguage", page)
    nodes["WebSite"]["inLanguage"] = inlang
    nodes["FAQPage"]["inLanguage"] = inlang
    nodes["Organization"]["contactPoint"]["availableLanguage"] = [
        l["code"] for l in live
    ]
    org = CONF["org"]
    logo = SRC / org["logo"].lstrip("/")
    if not logo.exists():
        die(page, f"org logo {org['logo']} missing")
    lw, lh = img_size(logo)
    nodes["Organization"].update(
        {
            "legalName": org["legalName"],
            "identifier": org["companyRegistrationNo"],
            "logo": {
                "@type": "ImageObject",
                "url": site + org["logo"],
                "width": lw,
                "height": lh,
            },
            "sameAs": org["sameAs"],
        }
    )
    nodes["WebApplication"]["inLanguage"] = inlang
    for t in ("Organization", "WebSite", "WebApplication"):
        nodes[t]["url"] = url
    for offer in nodes["WebApplication"].get("offers", []):
        frag = offer.get("url", "").partition("#")[2]
        offer["url"] = url + (f"#{frag}" if frag else "")
    data["@graph"].append(
        {
            "@type": "WebPage",
            "@id": f"{url}#webpage",
            "url": url,
            "name": title,
            "description": desc,
            "inLanguage": inlang,
            "isPartOf": {"@id": nodes["WebSite"]["@id"]},
            "about": {"@id": nodes["WebApplication"]["@id"]},
            "primaryImageOfPage": {
                "@type": "ImageObject",
                "url": ogimg,
                "width": 1200,
                "height": 630,
            },
        }
    )
    visible = norm(
        re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    )
    vis_faq = [
        (norm(a), norm(b))
        for a, b in re.findall(
            r'<summary>(.*?)<span class="ic".*?</summary><div class="ans">(.*?)</div></details>',
            html,
            re.S,
        )
    ]
    ld_faq = [
        (norm(x["name"]), norm(x["acceptedAnswer"]["text"]))
        for x in nodes["FAQPage"]["mainEntity"]
    ]
    if not vis_faq or vis_faq != ld_faq:
        die(
            page,
            f"FAQPage JSON-LD differs from visible FAQ ({len(ld_faq)} vs {len(vis_faq)})",
        )
    for o in nodes["WebApplication"]["offers"]:
        if o["priceCurrency"] != "EUR" or not re.search(
            re.escape(o["price"]).replace(r"\.", "[,.]"), visible
        ):
            die(page, f"offer {o['name']} price {o['price']} not visible on page")
    m = re.search(r"const steps = (\[\s*\[.*?\])\s*;", html, re.S)
    if not m:
        die(page, "steps array for the how-it-works tabs not found")
    steps = json.loads(m.group(1))
    pm = re.search(
        r'(<div class="panel swap" id="p" role="tabpanel"><h3>(.*?)</h3>.*?</ul></div>)',
        html,
        re.S,
    )
    if not pm or norm(pm.group(2)) != norm(steps[0][0]):
        die(page, "static tab panel does not match steps[0]")
    extra = "".join(
        f"<h3>{a}</h3><p>{b}</p><ul>{''.join(f'<li>{x}</li>' for x in li)}</ul>"
        for a, b, li, *_ in steps[1:]
    )
    html = html.replace(
        pm.group(1), pm.group(1) + f'<div id="p-more" hidden>{extra}</div>', 1
    )
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    for a in set(re.findall(r'href="#([^"]+)"', html)):
        if a not in ids:
            die(page, f"anchor #{a} has no target")
    for tag in re.findall(r"<img\b[^>]*>", html):
        if " alt=" not in tag and "${" not in tag:
            die(page, f"img without alt: {tag[:80]}")
    out = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = html.replace(ld[0], out, 1).replace("{{SITE}}", site)
    app = CONF.get("app")
    if not app:
        die(page, 'langs.json has no "app" URL for {{APP}} links')
    if app.rstrip("/") in html:
        die(page, f"literal {app} in the page; link the web app with {{{{APP}}}}")
    if "{{APP}}" not in html:
        die(page, "no {{APP}} link to the web app")
    html = html.replace("{{APP}}", app)
    if "{{" in html:
        die(page, "unresolved {{ token")
    return html, {"title": title, "desc": desc}


def root_files(live, meta, posts):
    site, ind = CONF["site"], CONF["indexable"]
    lines = [
        "# Generated by deploy/build.py from deploy/langs.json.",
        "# D21: search and training AI crawlers are allowed; put a Disallow here, not in the * group.",
    ]
    if not ind:
        lines.append(
            "# Preview: crawling stays allowed so that noindex (header and meta) is read."
        )
    lines += [f"User-agent: {c}" for c in CONF["crawlers"]] + [
        "Allow: /",
        f"Disallow: {API_PREFIX}",
        "",
        "User-agent: *",
        "Allow: /",
        f"Disallow: {API_PREFIX}",
        "",
    ]
    if ind:
        lines.append(f"Sitemap: {site}/sitemap.xml")
    robots = "\n".join(lines) + "\n"

    alts = (
        "".join(
            f'<xhtml:link rel="alternate" hreflang="{h}" href="{site}/{l["code"]}/"/>'
            for l in live
            for h in l["hreflang"]
        )
        + f'<xhtml:link rel="alternate" hreflang="x-default" href="{site}/{CONF["default"]}/"/>'
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "".join(f"<url><loc>{site}/{l['code']}/</loc>{alts}</url>\n" for l in live)
        + "</urlset>\n"
    )

    ref = next((l for l in live if l["code"] == "en"), live[0])
    src = (SRC / ref["file"]).read_text()
    d = re.search(
        r'<div class="def"><p class="k">.*?</p><p>(.*?)</p>.*?<p class="st">(.*?)</p>',
        src,
        re.S,
    )
    if not d:
        sys.exit("llms.txt: definition block (.def / .st) not found on " + ref["code"])
    org = next(
        n
        for n in json.loads(
            re.search(
                r'<script type="application/ld\+json">(.*?)</script>', src, re.S
            ).group(1)
        )["@graph"]
        if n["@type"] == "Organization"
    )
    a = org["address"]
    out = [
        "# WeltScout",
        "",
        f"> {norm(d.group(1))}",
        "",
        f"{norm(d.group(2))}. Prices and facts are repeated on each language page below.",
        "",
        "## Pages",
        *[
            f"- [{l['name']}]({site}/{l['code']}/): {meta[l['code']]['desc']}"
            for l in live
        ],
        "",
        *[
            line
            for l in live
            for ps in [[p for p in posts.get(l["code"]) or [] if ind and p["status"] in CONF["blogIndexStatuses"]]]
            if ps
            for line in [f"## Articles: {l['name']}"]
            + [f"- [{p['title']}]({site}/{l['code']}/blog/{p['slug']}/): {p['meta_description']}" for p in ps]
            + [""]
        ],
        "## Company",
        f"- {org['name']}, {a['streetAddress']}, {a['postalCode']} {a['addressLocality']}, {a['addressCountry']}",
        f"- Contact: {org['email']}; support answers in: {', '.join(l['name'] for l in live)}",
        f"- VAT ID: {org['vatID']}",
        "",
    ]
    return robots, sitemap, "\n".join(out)


def icon_tags():
    ic = CONF["icons"]
    for p in ic.values():
        if not (SRC / p.lstrip("/")).exists():
            sys.exit(f"icon {p} missing")
    return (
        f'<link rel="icon" href="{ic["icon"]}" type="image/png" sizes="48x48">'
        f'<link rel="apple-touch-icon" href="{ic["appleTouch"]}" sizes="180x180">'
    )


LEGAL_DIR = SRC / "legal"
LEGAL_SLUGS = (
    sorted(p.stem for p in (LEGAL_DIR / CONF["legalFallback"]).glob("*.html"))
    if LEGAL_DIR.exists()
    else []
)
COOKIE_STEM = "cookie-policy"
API_PREFIX = "/api/"
FONT_EXT = "geist-latin-ext.woff2"
TERMS_STEM = "terms-and-conditions"
LEGAL_HUB = "/legal"


def og_image_path(code):
    """The OG image is published under a name that carries a hash of its bytes (copied in at the end of the build),
    so a re-rendered image gets a new URL and no CDN or social-network cache can keep showing the old one."""
    src = SRC / "img" / "og" / f"{code}.jpg"
    return f"/img/og/{code}-{hashlib.sha256(src.read_bytes()).hexdigest()[:10]}.jpg"


def legal_slug(code, stem):
    l = next((x for x in CONF["langs"] if x["code"] == code), {})
    s = l.get("legalSlugs", {}).get(stem)
    if not s or not blog.SLUG.fullmatch(s):
        sys.exit(f"{code}: langs.json legalSlugs has no valid slug for {stem}")
    return s


def legal_url(code, stem):
    return f"/{code}/{legal_slug(code, stem)}/"


def check_legal_slugs():
    if COOKIE_STEM not in LEGAL_SLUGS:
        sys.exit(
            f"legal/{CONF['legalFallback']}/{COOKIE_STEM}.html missing (consent links to it)"
        )
    for l in CONF["langs"]:
        got = [legal_slug(l["code"], s) for s in LEGAL_SLUGS]
        extra = sorted(set(l.get("legalSlugs", {})) - set(LEGAL_SLUGS))
        if extra:
            sys.exit(f"{l['code']}: legalSlugs keys without a legal/ file: {extra}")
        if len(set(got)) != len(got) or "blog" in got:
            sys.exit(f"{l['code']}: legalSlugs must be distinct and not 'blog': {got}")


def legal_redirects(live):
    """301s in one hop to the localized legal URL: /<lang>/<english stem> (preview, old Webflow) and the root /<stem>. Both slash forms, because redirect sources match strictly."""
    out = []

    def add(src, dst):
        out.extend(
            {"source": v, "destination": dst, "permanent": True}
            for v in (src, src + "/")
        )

    for l in live:
        for s in LEGAL_SLUGS:
            if legal_slug(l["code"], s) != s:
                add(f"/{l['code']}/{s}", legal_url(l["code"], s))
    for s in LEGAL_SLUGS:
        add(f"/{s}", legal_url(CONF["default"], s))
    add(LEGAL_HUB, legal_url(CONF["default"], TERMS_STEM))
    return out


CHROME_SEL = re.compile(
    r'^(?:\[data-theme="(?:light|dark)"\] )?(?:\*|html|body(?:>nav)?|a|img|nav|footer|:focus-visible|section\.(?:band|final)|'
    r"\.(?:btn|skip|logo|lg-[ld]|nav-in|links|right|login|lang|lang-[bm]|mlangs|burger|mnav|flag|sw|sr|band|final|note))(?![\w-])"
)
CHROME_KEYFRAMES = ("langin", "mnavin", "mitem")
CHROME_MUST = (
    ".nav-in{",
    ".burger{",
    ".mnav{",
    "footer .cols{",
    ".sw button{",
    ".lang-m{",
    ".skip{",
    ".final .btn{",
)
CHROME_JS = ("theme", "mobile menu", "nav indicator", "language switcher")


def css_blocks(css):
    out, i = [], 0
    while True:
        j = css.find("{", i)
        if j < 0:
            return out
        depth, k = 1, j + 1
        while depth:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        out.append((css[i:j].strip(), css[j + 1 : k - 1]))
        i = k


def chrome_rules(css):
    out = []
    for head, body in css_blocks(css):
        if head.startswith("@media"):
            inner = chrome_rules(body)
            if inner:
                out.append(f"{head}{{{inner}}}")
        elif head.startswith("@keyframes"):
            if head.split()[1] in CHROME_KEYFRAMES:
                out.append(f"{head}{{{body}}}")
        elif not head.startswith("@"):
            sel = ",".join(
                x.strip() for x in head.split(",") if CHROME_SEL.match(x.strip())
            )
            if sel:
                out.append(f"{sel}{{{body.strip()}}}")
    return "".join(out)


def chrome_parts(code, html, src):
    """Nav, footer, skip link, CTA band, their CSS and JS, cut from the language's own built homepage (one source of truth)."""

    def one(pattern, what):
        m = re.search(pattern, html, re.S)
        if not m:
            sys.exit(f"{code}: homepage {what} not found for the blog/legal chrome")
        return m.group(1)

    head = html.split("</head>", 1)[0]
    css = re.sub(
        r"/\*.*?\*/",
        "",
        "".join(re.findall(r"<style[^>]*>(.*?)</style>", head, re.S)),
        flags=re.S,
    )
    rules = chrome_rules(css)
    for need in CHROME_MUST:
        if need not in rules:
            sys.exit(f"{code}: chrome CSS rule {need}...}} not found on the homepage")
    script = one(
        r"<script>\s*\(\(\) => \{(.*?)\}\)\(\);?\s*</script>\s*</body>", "main script"
    )
    js = []
    for name in CHROME_JS:
        m = re.search(rf"/\* {name} \*/(.*?)(?=\n\s*/\* |\Z)", script, re.S)
        if not m:
            sys.exit(f"{code}: homepage script block /* {name} */ not found")
        js.append(m.group(1).strip())
    key = re.search(r'localStorage\.getItem\("([^"]+)"\)', js[0])
    theme = re.search(r'<html lang="[^"]+" data-theme="(\w+)"', html)
    fonts = re.findall(r'<link rel="preload" href="fonts/[^"]+" as="font"[^>]*>', head)
    if not key or not theme or not fonts:
        sys.exit(
            f"{code}: theme storage key, default theme or font preloads not found on the homepage"
        )
    page = lambda s: re.sub(r'href="#([^"]+)"', rf'href="/{code}/#\1"', s)
    cta = re.search(
        r'<section class="final band">.*?(<div class="ctas">.*?</div>)\s*<p class="note"[^>]*>(.*?)</p>',
        html,
        re.S,
    )
    if not cta:
        sys.exit(f"{code}: homepage final CTA band (.ctas + .note) not found")
    return {
        "css": "".join(theme_styles(code, src)) + rules,
        "skip": one(r'(<a class="skip" href="#main">[^<]*</a>)', "skip link"),
        "nav": page(
            one(
                r'(<nav aria-label="[^"]*">\s*<div class="nav-in">.*?</nav>)', "top nav"
            )
        ),
        "footer": page(one(r"(<footer>.*?</footer>)", "footer")),
        "ctas": page(cta.group(1)),
        "note": cta.group(2),
        "js": ";".join(js),
        "key": key.group(1),
        "theme": theme.group(1),
        "themes": json.dumps(
            sorted(set(re.findall(r':root\[data-theme="(\w+)"\]', css)))
        ),
        "fonts": "".join(fonts),
    }


def chrome_render(code, alt, current=None):
    """alt: {code: url} for every language-switcher link; current: href marked aria-current in nav and footer."""
    p, n_live = CHROME[code], len(CHROME)

    def langs(s, want):
        s, n = re.subn(
            r'href="/([a-z]{2})/"( hreflang="\1")',
            lambda m: f'href="{alt[m.group(1)]}"{m.group(2)}',
            s,
        )
        if n != want:
            sys.exit(f"{code}: expected {want} language links in the chrome, found {n}")
        if current:
            s = re.sub(
                rf'(<a href="{re.escape(current)}")(?![^>]*aria-current)',
                r'\1 aria-current="page"',
                s,
            )
        return s

    if set(alt) != set(CHROME):
        sys.exit(
            f"{code}: language switcher targets {sorted(alt)} do not cover {sorted(CHROME)}"
        )
    return langs(p["nav"], 2 * n_live), langs(p["footer"], n_live)


def doc_page(l, head, main, alt, css="", current=None, js="", cls=""):
    """Blog and legal page shell: the homepage chrome around <main>; head carries title, meta, canonical, hreflang, OG, JSON-LD."""
    code, p = l["code"], CHROME[l["code"]]
    nav, foot = chrome_render(code, alt, current)
    return (
        f'<!doctype html><html lang="{code}" data-theme="{p["theme"]}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'{head}{icon_tags()}{p["fonts"]}<link rel="stylesheet" href="tokens.css">'
        f'<script>try{{const t=localStorage.getItem("{p["key"]}");if({p["themes"]}.includes(t))document.documentElement.dataset.theme=t}}catch(e){{}}</script>'
        f"<style>{p['css']}{LEGAL_CSS}{css}</style></head><body>{p['skip']}{nav}"
        f'<main id="main"{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>{main}</main>{foot}'
        f"<script>(()=>{{const root=document.documentElement,$=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];{p['js']}}})()</script>"
        f"{js}</body></html>"
    )




LONE_WORD_MAX = 14


def no_widows(html):
    """Joins the last two words of every lead and h2/h3 with a no-break space, so a phone never shows a short last
    word alone on its own row (text-wrap: pretty is not applied by every browser). Tags inside are skipped; a last
    word longer than LONE_WORD_MAX stays breakable so a narrow screen cannot overflow."""

    def join(m):
        inner, i, word = m.group(3), len(m.group(3)) - 1, 0
        while i >= 0:
            ch = inner[i]
            if ch == ">":
                i = inner.rfind("<", 0, i) - 1
                continue
            if ch.isspace():
                if word:
                    break
            else:
                word += 1
            i -= 1
        if i < 0 or not word or word > LONE_WORD_MAX:
            return m.group(0)
        return m.group(1) + inner[:i] + "\u00a0" + inner[i + 1 :] + m.group(4)

    return re.sub(r'(<(h2|h3|p class="lead[^"]*")[^>]*>)(.*?)(</(?:h2|h3|p)>)', join, html, flags=re.S)


def lighter_preloads(page):
    """Preload the latin-ext font subset only when the hero copy (H1, lead, buttons, offer line) uses its glyphs. Text
    further down still gets it through unicode-range, without competing with the LCP image on the first request wave."""
    rng = re.search(re.escape(FONT_EXT) + r'"\)[^}]*unicode-range:([^;}]+)', page)
    hero = re.search(r'<header class="hero">.*?</header>', page, re.S)
    if not rng or not hero:
        sys.exit(f"lighter_preloads: {FONT_EXT} unicode-range or the hero not found")
    spans = []
    for part in rng.group(1).split(","):
        lo, _, hi = part.strip()[2:].partition("-")
        spans.append((int(lo, 16), int(hi or lo, 16)))
    copy = " ".join(re.findall(r'<h1.*?</h1>|<p class="lead".*?</p>|<div class="ctas">.*?</div>|<p class="note offer">.*?</p>', hero.group(0), re.S))
    text = htmllib.unescape(re.sub(r"<[^>]+>", " ", copy))
    if any(lo <= ord(ch) <= hi for ch in text for lo, hi in spans):
        return page
    return re.sub(r'<link rel="preload" href="[^"]*' + re.escape(FONT_EXT) + r'"[^>]*>\n?', "", page)


NOT_FOUND_CSS = ".nf-a{display:flex;flex-wrap:wrap;gap:12px;margin:32px 0 0}"


def write_not_found(live, posts):
    """A branded 404 per language (/<lang>/404.html) and the default language's at /404.html: noindex, no canonical,
    self-hosted assets only. The edge answers unknown paths with it (edge_core.js); Vercel uses /404.html itself."""
    e = lambda v: htmllib.escape(v, quote=True)
    for l in live:
        code, t = l["code"], l["notFound"]
        links = f'<a class="btn" href="/{code}/">{e(t["home"])}</a>'
        if posts.get(code):
            links += f'<a class="btn alt" href="/{code}/blog/">{e(l["blog"]["name"])}</a>'
        main = f'<header class="doc-h"><h1>{e(t["title"])}</h1><p class="upd">{e(t["text"])}</p><p class="nf-a">{links}</p></header>'
        head = f'<title>{e(t["title"])} | WeltScout</title><meta name="robots" content="noindex">'
        page = doc_page(l, head, main, {x["code"]: f"/{x['code']}/" for x in live}, css=NOT_FOUND_CSS, cls="nf")
        page = absolutize(consent(page, l, legal_url(code, COOKIE_STEM)))
        (OUT / code / "404.html").write_text(page)
        if code == CONF["default"]:
            (OUT / "404.html").write_text(page)


LEGAL_CSS = (
    "main{display:block;padding-bottom:24px}"
    "@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}"
    ".crumbs{font-size:14px;color:var(--tx3)}.crumbs ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;align-items:center}"
    '.crumbs li{display:inline-flex;align-items:center;min-width:0;max-width:100%}.crumbs li+li:before{content:"/";margin:0 10px;color:var(--tx3)}'
    ".crumbs a{display:inline-block;padding:4px 0;color:var(--tx2);text-decoration:none}.crumbs a:hover{color:var(--tx);text-decoration:underline}"
    ".crumbs [aria-current]{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:44ch}"
    ".doc-h,.doc{max-width:var(--maxw);margin:0 auto;padding:0 24px;display:grid;font-size:18px;"
    "grid-template-columns:minmax(0,15rem) minmax(0,68ch) minmax(0,1fr);column-gap:56px}"
    ".doc-h{padding-top:56px;padding-bottom:8px}.doc-h>*{grid-column:2/4;min-width:0}"
    ".doc-h h1{margin:22px 0 0;font-size:clamp(36px,5.4vw,66px);line-height:1.02;letter-spacing:-.042em;font-weight:600;color:var(--tx);max-width:19ch;text-wrap:balance;overflow-wrap:break-word;hyphens:auto}"
    ".upd{margin:18px 0 0;font-size:15px;color:var(--tx3)}"
    ".doc{padding-top:56px}"
    ".toc{grid-column:1;grid-row:1/span 20;align-self:start;position:sticky;top:104px;max-height:calc(100vh - 128px);overflow-y:auto;font-size:14px;padding:2px 4px 8px 0}"
    ".toc-h{margin:0 0 12px;font-weight:600;color:var(--tx)}"
    ".toc ol,.toc-m ol{list-style:none;margin:0;padding:0}.toc ol{border-left:1px solid var(--line2)}"
    ".toc a{display:block;margin-left:-1px;padding:6px 0 6px 14px;border-left:2px solid transparent;color:var(--tx2);text-decoration:none;line-height:1.35;text-wrap:pretty}"
    ".toc a:hover{color:var(--tx)}.toc a[aria-current]{color:var(--tx);border-left-color:var(--acc)}"
    ".toc-m{display:none;margin:0 0 44px;border-radius:16px;background:var(--surf);box-shadow:var(--sh);font-size:16px}"
    ".toc-m summary{display:flex;align-items:center;justify-content:space-between;min-height:52px;padding:0 20px;font-weight:600;color:var(--tx);cursor:pointer;list-style:none}"
    '.toc-m summary::-webkit-details-marker{display:none}.toc-m summary:after{content:"";width:8px;height:8px;border:solid var(--tx2);border-width:0 2px 2px 0;transform:translateY(-2px) rotate(45deg)}'
    ".toc-m[open] summary:after{transform:translateY(2px) rotate(-135deg)}.toc-m ol{padding:0 8px 10px}"
    ".toc-m a{display:block;padding:10px 12px;border-radius:10px;color:var(--tx2);text-decoration:none;line-height:1.35}.toc-m a:hover{background:var(--surf2);color:var(--tx)}"
    ".prose{grid-column:2;grid-row:1;min-width:0;color:color-mix(in srgb,var(--tx) 82%,var(--pg));line-height:1.7;overflow-wrap:break-word;hyphens:auto}"
    ".prose>:first-child{margin-top:0}.prose p,.prose ul,.prose ol{margin:0 0 1.15em}"
    ".prose h2{margin:2.3em 0 .6em;font-size:clamp(24px,2.3vw,30px);line-height:1.15;letter-spacing:-.025em;font-weight:600;color:var(--tx);text-wrap:balance;scroll-margin-top:104px}"
    ".prose h3{margin:1.7em 0 .45em;font-size:20px;line-height:1.3;letter-spacing:-.015em;font-weight:600;color:var(--tx)}"
    ".prose strong,.prose b{color:var(--tx);font-weight:600}"
    ".prose a{color:var(--acc);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}.prose a:hover{text-decoration-thickness:2px}"
    ".prose ul,.prose ol{padding-left:1.3em}.prose li{margin:.4em 0;padding-left:.25em}.prose li::marker{color:var(--acc);font-weight:600;font-variant-numeric:tabular-nums}"
    ".prose blockquote{margin:1.6em 0;padding:4px 0 4px 20px;border-left:2px solid var(--line3);color:var(--tx2)}"
    ".tw{margin:1.6em 0 2em;overflow-x:auto;border-radius:16px;background:var(--surf);box-shadow:var(--sh)}"
    # phones: breadcrumb and mobile contents links are 44 px touch targets
    "@media (max-width:600px){.crumbs a{display:inline-flex;align-items:center;min-height:44px;padding:0}.toc-m a{display:flex;align-items:center;min-height:44px}}"
    # a table wider than the screen scrolls inside its card; a soft shade at the edge that has more columns says so
    ".tw{--tw-sh:color-mix(in srgb,var(--tx) 16%,transparent);background:"
    "linear-gradient(90deg,var(--surf) 30%,transparent) left/32px 100% no-repeat local,"
    "linear-gradient(270deg,var(--surf) 30%,transparent) right/32px 100% no-repeat local,"
    "radial-gradient(farthest-side at 0 50%,var(--tw-sh),transparent) left/12px 100% no-repeat scroll,"
    "radial-gradient(farthest-side at 100% 50%,var(--tw-sh),transparent) right/12px 100% no-repeat scroll,var(--surf)}"
    ".tw table{width:100%;min-width:34rem;border-collapse:collapse;font-size:15px;line-height:1.5}"
    ".tw th{padding:13px 16px;background:var(--surf2);color:var(--tx);font-size:14px;font-weight:600;text-align:left;vertical-align:bottom}"
    ".tw td{padding:14px 16px;border-top:1px solid var(--line2);vertical-align:top}.tw td:first-child{color:var(--tx);font-weight:500}"
    ".tw tr>:first-child{padding-left:20px}.tw tr>:last-child{padding-right:20px}"
    "@media (max-width:1100px){.doc-h,.doc{grid-template-columns:minmax(0,68ch);justify-content:center}.doc-h>*,.prose{grid-column:1}.toc{display:none}.toc-m{display:block}}"
    "@media (max-width:600px){.doc-h,.doc{padding:0 16px;font-size:17px}.doc-h{padding-top:32px}.doc{padding-top:36px}.doc-h h1{font-size:clamp(30px,8.6vw,36px)}}"
)


def theme_styles(code, src):
    styles = re.findall(
        r'(@font-face\{[^}]*\}|:root(?:\[data-theme="(?:light|dark)"\])?\{[^}]*\})', src
    )
    if len(styles) < 3:
        sys.exit(f"{code}: theme tokens / font-face not found")
    return styles


def legal_names(code, src):
    out = {}
    for s in LEGAL_SLUGS:
        m = re.search(rf'href="/{s}"[^>]*>([^<]+)</a>', src)
        if not m:
            sys.exit(f"{code}: footer link to /{s} not found")
        out[s] = m.group(1)
    return out


def legal_pages(live, sources):
    site, written, fallback = CONF["site"], [], []
    e = lambda v: htmllib.escape(v, quote=True)
    for l in live:
        code, ui = l["code"], blog.ui(l)
        for s in LEGAL_SLUGS:
            f = LEGAL_DIR / code / f"{s}.html"
            own = f.exists()
            if not own:
                f = LEGAL_DIR / CONF["legalFallback"] / f"{s}.html"
                fallback.append(f"{code}/{s}")
            body = f.read_text()
            h1 = re.search(r"<h1>(.*?)</h1>", body, re.S)
            if not h1:
                sys.exit(f"{f}: no h1")
            first = re.search(
                r"<h2[^>]*>.*?</h2>.*?<p>(.*?)</p>", body, re.S
            ) or re.search(r"<p>(.*?)</p>", body, re.S)
            desc = norm(first.group(1)) if first else norm(h1.group(1))
            desc = desc if len(desc) <= 155 else desc[:152].rsplit(" ", 1)[0] + "…"
            canon = f"{site}{legal_url(code if own else CONF['legalFallback'], s)}"
            have = [x for x in live if (LEGAL_DIR / x["code"] / f"{s}.html").exists()]
            alts = "".join(
                f'<link rel="alternate" hreflang="{h}" href="{site}{legal_url(x["code"], s)}">'
                for x in have
                for h in x["hreflang"]
            ) + "".join(
                f'<link rel="alternate" hreflang="x-default" href="{site}{legal_url(x["code"], s)}">'
                for x in have
                if x["code"] == CONF["default"]
            )
            robots = (
                ""
                if CONF["indexable"]
                else '<meta name="robots" content="noindex, nofollow">'
            )
            for t in LEGAL_SLUGS:
                body = body.replace(f'href="../{t}/"', f'href="{legal_url(code, t)}"')
            upd = re.search(r'<p class="upd">.*?</p>', body, re.S)
            body = body.replace(h1.group(0), "", 1).replace(
                upd.group(0) if upd else "\0", "", 1
            )
            body, heads = blog.heading_ids(body)
            body = blog.wrap_tables(body, ui["table"])
            title = norm(h1.group(1))
            main = (
                f'<header class="doc-h">{blog.crumbs([(f"/{code}/", l["blog"]["home"])], title, ui)}'
                f"<h1>{h1.group(1)}</h1>{upd.group(0) if upd else ''}</header>"
                f'<div class="doc">{blog.toc(heads, ui)}<article class="prose">{blog.toc(heads, ui, mobile=True)}{body}</article></div>'
            )
            head = (
                f"<title>{title} | WeltScout</title>"
                f'<meta name="description" content="{e(desc)}">{robots}<link rel="canonical" href="{canon}">{alts}'
                f'<meta property="og:type" content="website"><meta property="og:title" content="{e(title)} | WeltScout">'
                f'<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">'
                f'<meta property="og:locale" content="{l["locale"][0]}"><meta property="og:image" content="{site}{og_image_path(code)}">'
                '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            )
            url = legal_url(code, s)
            page = doc_page(
                l,
                head,
                main,
                {x["code"]: legal_url(x["code"], s) for x in live},
                current=url,
                js=blog.TOC_JS,
                cls="lg",
            )
            d = OUT / code / legal_slug(code, s)
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(
                absolutize(consent(page, l, legal_url(code, COOKIE_STEM)))
            )
            written.append(f"{code}/{legal_slug(code, s)}")
    return written, fallback


CONSENT_CSS = (
    ".ck{position:fixed;left:16px;right:16px;bottom:16px;z-index:90;max-width:560px;margin:0 auto;padding:18px 20px;border-radius:16px;"
    "background:var(--surf);color:var(--tx);box-shadow:var(--sh-lg);border:1px solid var(--line2);font:15px/1.5 Geist,system-ui,sans-serif}"
    ".ck[hidden]{display:none}.ck p{margin:0 0 14px;color:var(--tx2)}.ck a{color:var(--acc)}"
    ".ck .b{display:flex;flex-wrap:wrap;gap:10px}.ck button{flex:1 1 140px;min-height:44px;border-radius:10px;font:600 15px Geist,system-ui,sans-serif;cursor:pointer;"
    "border:1px solid var(--line3);background:transparent;color:var(--tx)}.ck button:focus-visible,.ck-open:focus-visible{outline:2px solid var(--acc);outline-offset:2px}"
    ".ck-open{background:none;border:0;padding:0;font:inherit;color:inherit;text-decoration:underline;cursor:pointer}"
    "@media (min-width:900px){.ck{left:auto;right:24px;bottom:24px;max-width:400px;margin:0}}"
    "@media (max-width:600px){.ck{left:0;right:0;bottom:0;max-width:none;padding:10px 16px calc(10px + env(safe-area-inset-bottom));"
    "border-radius:16px 16px 0 0;border-width:1px 0 0;font-size:13px;line-height:1.38}.ck p{margin:0 0 8px}"
    ".ck .b{flex-wrap:nowrap}.ck button{flex:1 1 0;min-width:0}}"
)


def consent(html, l, legal_href):
    ga = CONF.get("analytics", {}).get("ga4", "")
    if not ga:
        return html
    if not re.fullmatch(r"G-[A-Z0-9]{6,}", ga):
        sys.exit(f"analytics.ga4 {ga!r} is not a GA4 measurement ID")
    t = l.get("consent")
    if not t:
        sys.exit(f"{l['code']}: consent strings missing in langs.json")
    e = lambda v: htmllib.escape(v, quote=True)
    banner = (
        f'<div class="ck" id="ck" role="region" aria-label="{e(t["settings"])}" hidden><p>{e(t["text"])} '
        f'<a href="{legal_href}">{e(t["more"])}</a></p><div class="b">'
        f'<button type="button" data-ck="granted">{e(t["accept"])}</button>'
        f'<button type="button" data-ck="denied">{e(t["reject"])}</button></div></div>'
    )
    js = (
        "<script>(()=>{const K='ws-consent',ID='"
        + ga
        + "',b=document.getElementById('ck');"
        "let v=null;try{v=localStorage.getItem(K)}catch(e){}"
        "const load=()=>{if(window.__ga)return;window.__ga=1;window.dataLayer=window.dataLayer||[];"
        "window.gtag=function(){dataLayer.push(arguments)};gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'granted'});"
        "gtag('js',new Date());gtag('config',ID);const s=document.createElement('script');s.async=true;"
        "s.src='https://www.googletagmanager.com/gtag/js?id='+ID;document.head.appendChild(s)};"
        "const clear=()=>{document.cookie.split(';').map(c=>c.trim().split('=')[0]).filter(n=>/^_ga/.test(n)).forEach(n=>{"
        "const h=location.hostname.split('.');for(let i=0;i<h.length-1;i++)document.cookie=n+'=;Max-Age=0;path=/;domain=.'+h.slice(i).join('.');document.cookie=n+'=;Max-Age=0;path=/'})};"
        "const set=x=>{try{localStorage.setItem(K,x)}catch(e){}b.hidden=true;if(x==='granted')load();else{clear();if(window.__ga)location.reload()}};"
        "b.querySelectorAll('[data-ck]').forEach(x=>x.addEventListener('click',()=>set(x.dataset.ck)));"
        "document.querySelectorAll('.ck-open').forEach(x=>x.addEventListener('click',()=>{b.hidden=false;b.querySelector('button').focus()}));"
        "if(v==='granted')load();else if(v!=='denied')b.hidden=false})()</script>"
    )
    opener = f'<button type="button" class="ck-open">{e(t["settings"])}</button>'
    html, n = re.subn(
        r'(<a href="' + re.escape(legal_href) + r'"[^>]*>[^<]*</a>)',
        lambda m: m.group(1) + opener,
        html,
        count=1,
    )
    if n != 1:
        sys.exit(
            f"{l['code']}: footer cookie-policy link {legal_href} not found for the consent opener"
        )
    html = html.replace("</head>", f"<style>{CONSENT_CSS}</style></head>", 1)
    return html.replace("</body>", banner + js + "</body>", 1)


def link_legal(html, page):
    for s in LEGAL_SLUGS:
        html, n = re.subn(rf'href="/{s}"', f'href="{legal_url(page, s)}"', html)
        if n < 1:
            die(page, f"footer link to /{s} not found")
    return html


def absolutize(html):
    html = re.sub(
        r'srcset="([^"]*)"',
        lambda m: (
            'srcset="' + re.sub(r"(^|,\s*)((?:img|fonts)/)", r"\1/\2", m.group(1)) + '"'
        ),
        html,
    )
    html = re.sub(r'((?:src|href|poster|srcset)=")((?:img|fonts)/)', r"\1/\2", html)
    html = re.sub(r'url\((["\']?)((?:img|fonts)/)', r"url(\1/\2", html)
    return html.replace('href="tokens.css"', 'href="/tokens.css"')


OUT.mkdir(parents=True, exist_ok=True)
for p in OUT.iterdir():
    if p.name != ".vercel":
        shutil.rmtree(p) if p.is_dir() else p.unlink()
live = [l for l in CONF["langs"] if (SRC / l["file"]).exists()]
check_legal_slugs()
CHROME = {}
BLOG_POSTS, _ = blog.load(SRC, live)
missing = [l["code"] for l in CONF["langs"] if l not in live]
meta, sources = {}, {}
for l in live:
    (OUT / l["code"]).mkdir()
    sources[l["code"]] = footer_credit(social_links((SRC / l["file"]).read_text(), l["code"]), l)
    page, meta[l["code"]] = seo(
        localize(sources[l["code"]], l["code"], live), l["code"], live
    )
    if BLOG_POSTS.get(l["code"]):
        page = blog.nav_link(page, l["code"], l["blog"]["name"])
    page = link_legal(page, l["code"])
    CHROME[l["code"]] = chrome_parts(l["code"], page, sources[l["code"]])
    page = blog.home_section(page, l, BLOG_POSTS.get(l["code"]))
    page = absolutize(consent(page, l, legal_url(l["code"], COOKIE_STEM)))
    page = lighter_preloads(no_widows(page))
    (OUT / l["code"] / "index.html").write_text(page)
    if l["code"] == CONF["default"]:
        (OUT / "index.html").write_text(page)
legal_written, legal_fallback = legal_pages(live, sources)
blog_out = blog.build(
    CONF,
    OUT,
    live,
    sources,
    {
        "src": SRC,
        "styles": lambda c: theme_styles(c, sources[c]),
        "legal_css": LEGAL_CSS,
        "icon_tags": icon_tags,
        "consent": consent,
        "absolutize": absolutize,
        "legal_slugs": LEGAL_SLUGS,
        "legal_names": lambda c: legal_names(c, sources[c]),
        "page": doc_page,
        "chrome": CHROME,
        "cookie_url": lambda c: legal_url(c, COOKIE_STEM),
    },
)
blog_out["redirects"] = legal_redirects(live) + blog_out["redirects"]
write_not_found(live, blog_out["posts"])
robots, sitemap, llms = root_files(live, meta, blog_out["posts"])
HTML_ALT = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">')
sitemap = sitemap.replace(
    "</urlset>\n",
    "".join(
        "<url><loc>{}</loc><lastmod>{}</lastmod>{}</url>\n".format(
            u,
            d,
            HTML_ALT.sub(r'<xhtml:link rel="alternate" hreflang="\1" href="\2"/>', a),
        )
        for u, d, a in blog_out["sitemap"]
    )
    + "</urlset>\n",
)
(OUT / "robots.txt").write_text(robots)
(OUT / "sitemap.xml").write_text(sitemap)
(OUT / "llms.txt").write_text(llms)
shutil.copy(SRC / "tokens.css", OUT / "tokens.css")
for d in ("img", "fonts"):
    shutil.copytree(SRC / d, OUT / d)
for l in live:
    shutil.copy(SRC / "img" / "og" / f"{l['code']}.jpg", OUT / og_image_path(l["code"]).lstrip("/"))
shutil.copytree(SRC / "deploy" / "api", OUT / "api")
cfg = json.loads((SRC / "deploy" / "vercel.base.json").read_text())
if CONF["indexable"]:
    for rule in cfg["headers"]:
        rule["headers"] = [h for h in rule["headers"] if h["key"] != "X-Robots-Tag"]
cfg["redirects"] = blog_out["redirects"] + [
    {
        "source": src,
        "destination": r["to"].replace("{default}", CONF["default"]),
        "permanent": True,
    }
    for r in CONF.get("legacyRedirects", [])
    for src in [r["from"].replace("{langs}", "|".join(l["code"] for l in live))]
]
(OUT / "vercel.json").write_text(json.dumps(cfg, indent=2))
HTML_COMMENT = re.compile(r"<!--(?!\[)[\s\S]*?-->\n?")
for f in OUT.rglob("*.html"):
    html = f.read_text()
    if "<!--" in html:
        f.write_text(HTML_COMMENT.sub("", html))
print(
    "built",
    [l["code"] for l in live],
    "| not yet translated:",
    missing,
    "| indexable:",
    CONF["indexable"],
)
print(
    "blog posts:",
    {c: len(p) for c, p in blog_out["posts"].items() if p},
    "| legacy redirects:",
    len(blog_out["redirects"]),
    "| not indexed (status):",
    len(blog_out["held"]),
)
print(
    "legal pages:",
    len(legal_written),
    "| %s text used for:" % CONF["legalFallback"],
    legal_fallback or "none",
)
