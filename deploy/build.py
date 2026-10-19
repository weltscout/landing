"""Build the site: one /<code>/ page per language declared in deploy/langs.json. Generated from langs.json (site, indexable, locale, crawlers): language switcher, hreflang, canonical, robots meta, Open Graph/Twitter tags, JSON-LD URLs and inLanguage, robots.txt, sitemap.xml, llms.txt, vercel.json. Fails loudly when an expected element is missing."""

import html as htmllib, json, os, pathlib, re, shutil, struct, sys

SRC = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1])
CONF = json.loads((SRC / "deploy" / "langs.json").read_text())
if os.environ.get("WS_SITE"):
    CONF["site"] = os.environ["WS_SITE"].rstrip("/")
if os.environ.get("WS_INDEXABLE"):
    CONF["indexable"] = os.environ["WS_INDEXABLE"].lower() in ("1", "true", "yes")

SWITCH_CSS = (
    '<style id="lang-sw">.lang-m b{overflow:hidden;padding:0;background:none}'
    ".lang-m b img,.lang-b img{display:block;width:100%;height:100%;object-fit:cover;border-radius:4px}"
    ".mlangs{flex-wrap:wrap}.mlangs a{flex:1 0 21%;display:flex!important;align-items:center;justify-content:center;gap:6px}"
    ".mlangs img,footer .langs img{width:18px;height:13px;border-radius:2px;object-fit:cover}footer .langs{flex-wrap:wrap}"
    "footer .langs a{display:inline-flex;align-items:center;gap:6px}</style>"
)


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
        lambda m: m.group(1) + me["name"] + m.group(2) + page.upper() + m.group(3),
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
    ogt = need(r'<meta property="og:title" content="([^"]*)"', "og:title")
    ogd = need(r'<meta property="og:description" content="([^"]*)"', "og:description")
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
    ogimg = f"{site}/img/og/{page}.jpg"
    q = lambda v: htmllib.escape(v, quote=True)
    locs = [loc for l in live for loc in l["locale"]]
    html, n = re.subn(r'<link rel="icon"[^>]*>', lambda _: icon_tags(), html, count=1)
    if n != 1:
        die(page, "icon link not found")
    tags = [f'<link rel="canonical" href="{url}">']
    if not indexable:
        tags.append('<meta name="robots" content="noindex, nofollow">')
    tags += [
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
    if "{{" in html:
        die(page, "unresolved {{ token")
    return html, {"title": title, "desc": desc}


def root_files(live, meta):
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
        "",
        "User-agent: *",
        "Allow: /",
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
LEGAL_CSS = (
    "body{margin:0;background:var(--pg);color:var(--tx);font:16px/1.65 Geist,system-ui,sans-serif}"
    "header,main,footer{max-width:760px;margin:0 auto;padding:0 24px}"
    "header{display:flex;align-items:center;justify-content:space-between;padding-top:28px;padding-bottom:28px;border-bottom:1px solid var(--line)}"
    "header img{display:block;height:20px;width:auto}header a{color:var(--tx2);text-decoration:none;font-size:14px}"
    "main{padding-top:48px;padding-bottom:72px}h1{font-size:clamp(32px,5vw,44px);line-height:1.1;letter-spacing:-.03em;margin:0 0 8px}"
    "h2{font-size:22px;letter-spacing:-.015em;margin:44px 0 10px}h3{font-size:17px;margin:28px 0 6px}"
    "p,li{color:var(--tx2)}a{color:var(--acc)}.upd{font-size:14px;color:var(--tx3)}"
    "table{width:100%;border-collapse:collapse;font-size:14px;margin:16px 0;display:block;overflow-x:auto}"
    "th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--tx)}"
    "footer{padding-top:24px;padding-bottom:48px;border-top:1px solid var(--line);display:flex;flex-wrap:wrap;gap:8px 20px;font-size:14px}"
    "footer a{color:var(--tx2);text-decoration:none}footer a[aria-current]{color:var(--tx)}"
)


def legal_pages(live, sources):
    site, written, fallback = CONF["site"], [], []
    for l in live:
        src = sources[l["code"]]
        styles = re.findall(
            r'(@font-face\{[^}]*\}|:root(?:\[data-theme="(?:light|dark)"\])?\{[^}]*\})',
            src,
        )
        if len(styles) < 3:
            sys.exit(f"{l['code']}: theme tokens / font-face not found for legal pages")
        names = {
            s: re.search(rf'href="/{s}"[^>]*>([^<]+)</a>', src) for s in LEGAL_SLUGS
        }
        for s, m in names.items():
            if not m:
                sys.exit(f"{l['code']}: footer link to /{s} not found")
        for s in LEGAL_SLUGS:
            f = LEGAL_DIR / l["code"] / f"{s}.html"
            own = f.exists()
            if not own:
                f = LEGAL_DIR / CONF["legalFallback"] / f"{s}.html"
                fallback.append(f"{l['code']}/{s}")
            body = f.read_text()
            h1 = re.search(r"<h1>(.*?)</h1>", body, re.S)
            if not h1:
                sys.exit(f"{f}: no h1")
            first = re.search(r"<p>(.*?)</p>", body, re.S)
            desc = norm(first.group(1)) if first else norm(h1.group(1))
            desc = desc if len(desc) <= 155 else desc[:152].rsplit(" ", 1)[0] + "…"
            canon = f"{site}/{l['code'] if own else CONF['legalFallback']}/{s}/"
            alts = "".join(
                f'<link rel="alternate" hreflang="{h}" href="{site}/{x["code"]}/{s}/">'
                for x in live
                if (LEGAL_DIR / x["code"] / f"{s}.html").exists()
                for h in x["hreflang"]
            )
            robots = (
                ""
                if CONF["indexable"]
                else '<meta name="robots" content="noindex, nofollow">'
            )
            foot = "".join(
                f'<a href="/{l["code"]}/{t}/"{' aria-current="page"' if t == s else ""}>{names[t].group(1)}</a>'
                for t in LEGAL_SLUGS
            ) + "".join(
                f'<a href="/{x["code"]}/{s}/" hreflang="{x["code"]}" lang="{x["code"]}">{x["code"].upper()}</a>'
                for x in live
            )
            page = (
                f'<!doctype html><html lang="{l["code"]}" data-theme="dark"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width,initial-scale=1">'
                f"<title>{norm(h1.group(1))} | WeltScout</title>"
                f'<meta name="description" content="{htmllib.escape(desc, quote=True)}">{robots}'
                f'<link rel="canonical" href="{canon}">{alts}{icon_tags()}<link rel="stylesheet" href="tokens.css">'
                f"<style>{''.join(styles)}{LEGAL_CSS}</style></head><body>"
                f'<header><a href="/{l["code"]}/"><img src="/img/logo-weltscout-dark.svg" alt="WeltScout" width="120" height="20"></a>'
                f'<a href="/{l["code"]}/">WeltScout</a></header>'
                f"<main>{body}</main><footer>{foot}</footer></body></html>"
            )
            d = OUT / l["code"] / s
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(absolutize(page))
            written.append(f"{l['code']}/{s}")
    return written, fallback


def link_legal(html, page):
    for s in LEGAL_SLUGS:
        html, n = re.subn(rf'href="/{s}"', f'href="/{page}/{s}/"', html)
        if n < 1:
            die(page, f"footer link to /{s} not found")
    return html


def absolutize(html):
    html = re.sub(r'((?:src|href|poster|srcset)=")((?:img|fonts)/)', r"\1/\2", html)
    html = re.sub(r'url\((["\']?)((?:img|fonts)/)', r"url(\1/\2", html)
    return html.replace('href="tokens.css"', 'href="/tokens.css"')


OUT.mkdir(parents=True, exist_ok=True)
for p in OUT.iterdir():
    if p.name != ".vercel":
        shutil.rmtree(p) if p.is_dir() else p.unlink()
live = [l for l in CONF["langs"] if (SRC / l["file"]).exists()]
missing = [l["code"] for l in CONF["langs"] if l not in live]
meta, sources = {}, {}
for l in live:
    (OUT / l["code"]).mkdir()
    sources[l["code"]] = (SRC / l["file"]).read_text()
    page, meta[l["code"]] = seo(localize(sources[l["code"]], l["code"], live), l["code"], live)
    page = absolutize(link_legal(page, l["code"]))
    (OUT / l["code"] / "index.html").write_text(page)
    if l["code"] == CONF["default"]:
        (OUT / "index.html").write_text(page)
legal_written, legal_fallback = legal_pages(live, sources)
robots, sitemap, llms = root_files(live, meta)
(OUT / "robots.txt").write_text(robots)
(OUT / "sitemap.xml").write_text(sitemap)
(OUT / "llms.txt").write_text(llms)
shutil.copy(SRC / "tokens.css", OUT / "tokens.css")
for d in ("img", "fonts"):
    shutil.copytree(SRC / d, OUT / d)
shutil.copytree(SRC / "deploy" / "api", OUT / "api")
cfg = json.loads((SRC / "deploy" / "vercel.base.json").read_text())
if CONF["indexable"]:
    for rule in cfg["headers"]:
        rule["headers"] = [h for h in rule["headers"] if h["key"] != "X-Robots-Tag"]
cfg["redirects"] = [
    {"source": f"/{slug}", "destination": f"/{CONF['default']}/{slug}/", "permanent": True}
    for slug in LEGAL_SLUGS
]
(OUT / "vercel.json").write_text(json.dumps(cfg, indent=2))
print(
    "built",
    [l["code"] for l in live],
    "| not yet translated:",
    missing,
    "| indexable:",
    CONF["indexable"],
)
print("legal pages:", len(legal_written), "| %s text used for:" % CONF["legalFallback"], legal_fallback or "none")
