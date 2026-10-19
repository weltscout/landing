"""Blog pages for build.py, per docs/BLOG-STANDARD-202610.md.

blog/<lang>/<slug>.html -> /<lang>/blog/<slug>/ plus the /<lang>/blog/ index. A post is an
HTML body fragment (exactly one <h1>, a "Na kratko" paragraph, then H2 sections) that starts
with a JSON front matter comment holding the standard's §6.1 fields:

    <!--meta
    {"title": "...", "meta_description": "...", "hreflang_group": "...", "audience": "b2b|b2c|both",
     "content_type": "guide", "primary_keyword": {"term": "...", "market": "SI", "volume": null,
     "source": "...", "measured_on": "YYYY-MM-DD"}, "secondary_keywords": [],
     "author": {"name": "...", "url": "https://..."}, "reviewer": {"name": "...", "role": "..."},
     "editor_responsible": "...", "ai_assistance": "none|research|drafting|translation",
     "ai_disclosure_text": "...", "published": "YYYY-MM-DD", "updated": "YYYY-MM-DD",
     "last_fact_check": "YYYY-MM-DD", "status": "draft|review|published",
     "sources": [{"title": "...", "publisher": "...", "url": "https://...", "accessed": "YYYY-MM-DD", "kind": "official"}],
     "image": {"src": "/img/blog/x.webp", "alt": "...", "width": 1600, "height": 900},
     "changelog": [{"date": "YYYY-MM-DD", "change": "..."}], "legacy": ["/post/old-slug"]}
    -->

Posts sharing hreflang_group are translations of each other. "legacy" lists old URLs that
301 to the post. Only statuses listed in langs.json "blogIndexStatuses" are indexable (M40:
an unreviewed AI translation is built with noindex and left out of the sitemap).
"""

import datetime, html as htmllib, json, re, sys
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Ljubljana")
REQUIRED = (
    "title",
    "meta_description",
    "hreflang_group",
    "audience",
    "content_type",
    "primary_keyword",
    "author",
    "editor_responsible",
    "ai_assistance",
    "published",
    "updated",
    "status",
    "image",
)
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DATE = "%Y-%m-%d"
BANNED = re.compile(
    r"\b(24/7|real[- ]time|instant|non[- ]stop|mobile\.de|autoscout24|avto\.net|njuskalo|willhaben|kleinanzeigen)\b",
    re.I,
)

BLOG_CSS = (
    "main{overflow-wrap:break-word;hyphens:auto}"
    "nav.bc{font-size:14px;color:var(--tx3);margin:0 0 20px}nav.bc a{color:var(--tx2);text-decoration:none}"
    ".meta{font-size:14px;color:var(--tx3);margin:6px 0 28px}.meta b{color:var(--tx2);font-weight:500}"
    ".hero-img{margin:0 0 28px}.hero-img img{width:100%;height:auto;border-radius:16px;display:block}"
    "article img{max-width:100%;height:auto;border-radius:12px}figure{margin:24px 0}figcaption{font-size:14px;color:var(--tx3)}"
    ".short{padding:16px 20px;border-radius:14px;background:var(--surf);border:1px solid var(--line2);color:var(--tx)}"
    "blockquote{margin:20px 0;padding:4px 0 4px 18px;border-left:2px solid var(--line3);color:var(--tx2)}"
    ".src,.how{margin-top:48px;padding-top:20px;border-top:1px solid var(--line)}.src h2,.how h2{font-size:18px;margin-top:0}"
    ".how h3{font-size:15px;margin:18px 0 4px}.how p,.how li{font-size:14px}"
    ".cta{margin:48px 0 0;padding:24px;border-radius:16px;background:var(--surf);border:1px solid var(--line2)}"
    ".cta p{margin:0 0 14px;color:var(--tx);font-weight:600;font-size:18px}"
    ".cta a{display:inline-block;padding:12px 20px;border-radius:10px;background:var(--btn-bg);color:var(--btn-tx);text-decoration:none;font-weight:600}"
    ".rel{margin-top:40px}.rel ul{padding-left:18px}"
    ".list{list-style:none;padding:0;margin:32px 0 0}.list li{padding:22px 0;border-top:1px solid var(--line)}"
    ".list a{color:var(--tx);text-decoration:none;font-size:20px;font-weight:600;letter-spacing:-.01em}"
    ".list p{margin:6px 0 0}.list time{font-size:13px;color:var(--tx3)}"
)


def fail(path, msg):
    sys.exit(f"{path}: {msg}")


def iso(day):
    d = datetime.datetime.strptime(day, DATE).replace(hour=8, tzinfo=TZ)
    return d.isoformat()


def parse(path, src):
    raw = path.read_text()
    m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        fail(path, "missing <!--meta {...} --> front matter")
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        fail(path, f"front matter is not JSON: {e}")
    body = raw[m.end() :]
    for k in REQUIRED:
        if not meta.get(k):
            fail(path, f"front matter field '{k}' missing")
    for k in ("published", "updated", "last_fact_check"):
        if meta.get(k):
            datetime.datetime.strptime(meta[k], DATE)
    if meta["updated"] < meta["published"]:
        fail(path, "updated is before published")
    if meta["updated"] > datetime.date.today().isoformat():
        fail(path, "updated is in the future")
    for k, allowed in (
        ("audience", ("b2b", "b2c", "both")),
        ("status", ("draft", "review", "published")),
        ("ai_assistance", ("none", "research", "drafting", "translation")),
    ):
        if meta[k] not in allowed:
            fail(path, f"{k} must be one of {allowed}")
    if not SLUG.fullmatch(path.stem):
        fail(path, "slug must be lowercase ascii words joined by '-'")
    if len(meta["meta_description"]) > 170:
        fail(
            path,
            f"meta_description longer than 170 characters ({len(meta['meta_description'])})",
        )
    if "copy of" in meta["title"].lower():
        fail(path, "title still says 'Copy of'")
    if len(re.findall(r"<h1[ >]", body)) != 1:
        fail(path, "body needs exactly one <h1> (M11)")
    if not re.search(r'<p class="short">', body):
        fail(
            path,
            'body needs the "Na kratko" paragraph <p class="short"> under the h1 (M04)',
        )
    text = re.sub(r"<[^>]+>", " ", body)
    hit = BANNED.search(text + " " + meta["title"] + " " + meta["meta_description"])
    if hit:
        fail(path, f"banned term {hit.group(0)!r} (D15 portal names / D19 wording)")
    for s in meta.get("sources", []):
        if not str(s.get("url", "")).startswith("https://") or not s.get("accessed"):
            fail(path, f"source {s} needs an https url and an accessed date (M20)")
    img = meta["image"]
    if not (src / img["src"].lstrip("/")).exists() or not img.get("alt"):
        fail(path, f"image {img.get('src')} missing on disk or without alt")
    for tag in re.findall(r"<img\b[^>]*>", body):
        if " alt=" not in tag:
            fail(path, f"img without alt: {tag[:80]}")
        s = re.search(r'src="([^"]+)"', tag)
        if (
            s
            and s.group(1).startswith("/")
            and not (src / s.group(1).lstrip("/")).exists()
        ):
            fail(path, f"body image {s.group(1)} missing on disk")
    meta["slug"], meta["body"] = path.stem, body
    return meta


def load(src, live):
    posts, seen_legacy, groups = {}, {}, {}
    for l in live:
        d = src / "blog" / l["code"]
        posts[l["code"]] = sorted(
            (parse(p, src) for p in d.glob("*.html")) if d.exists() else [],
            key=lambda p: (p["updated"], p["slug"]),
            reverse=True,
        )
        for p in posts[l["code"]]:
            p["lang"] = l["code"]
            for old in p.get("legacy", []):
                if old in seen_legacy:
                    sys.exit(
                        f"legacy URL {old} claimed by {seen_legacy[old]} and {l['code']}/{p['slug']}"
                    )
                seen_legacy[old] = f"{l['code']}/{p['slug']}"
            g = groups.setdefault(p["hreflang_group"], {})
            if l["code"] in g:
                sys.exit(
                    f"hreflang_group {p['hreflang_group']} has two posts in {l['code']}"
                )
            g[l["code"]] = p
    return posts, groups


def url(site, p):
    return f"{site}/{p['lang']}/blog/{p['slug']}/"


def build(conf, out, live, sources, h):
    """h: helpers from build.py (src, styles, legal_css, icon_tags, consent, absolutize, legal_slugs, legal_names)."""
    site, default = conf["site"], conf["default"]
    posts, groups = load(h["src"], live)
    e = lambda v: htmllib.escape(str(v), quote=True)
    ok_status = set(conf.get("blogIndexStatuses", ["published"]))
    indexable = lambda p: conf["indexable"] and p["status"] in ok_status
    org_id = f"{site}/#organization"
    written, sitemap, redirects, held = [], [], [], []
    by_code = {l["code"]: l for l in live}

    def shell(l, title, desc, canon, alts, body, ld, index, og_img=None):
        robots = "" if index else '<meta name="robots" content="noindex, nofollow">'
        og = (
            f'<meta property="og:image" content="{site}{og_img["src"]}"><meta property="og:image:width" content="{og_img["width"]}">'
            f'<meta property="og:image:height" content="{og_img["height"]}"><meta property="og:image:alt" content="{e(og_img["alt"])}">'
            f'<meta name="twitter:card" content="summary_large_image">'
            if og_img
            else ""
        )
        return (
            f'<!doctype html><html lang="{l["code"]}" data-theme="dark"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}">{robots}'
            f'<link rel="canonical" href="{canon}">{alts}{h["icon_tags"]()}<link rel="stylesheet" href="tokens.css">'
            f'<meta property="og:type" content="{"article" if og_img else "website"}"><meta property="og:title" content="{e(title)}">'
            f'<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">'
            f'<meta property="og:locale" content="{l["locale"][0]}">{og}'
            f"<style>{''.join(h['styles'](l['code']))}{h['legal_css']}{BLOG_CSS}</style>"
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script></head><body>'
            f'<header><a href="/{l["code"]}/"><img src="/img/logo-weltscout-dark.svg" alt="WeltScout" width="120" height="20"></a>'
            f'<a href="/{l["code"]}/blog/">{e(l["blog"]["name"])}</a></header><main>{body}</main><footer>'
            + "".join(
                f'<a href="/{l["code"]}/{s}/">{e(h["legal_names"](l["code"])[s])}</a>'
                for s in h["legal_slugs"]
            )
            + "</footer></body></html>"
        )

    def hreflangs(members, path_of):
        tags = "".join(
            f'<link rel="alternate" hreflang="{x}" href="{path_of(code)}">'
            for code in members
            for x in by_code[code]["hreflang"]
        )
        xd = default if default in members else ("en" if "en" in members else None)
        return tags + (
            f'<link rel="alternate" hreflang="x-default" href="{path_of(xd)}">'
            if xd
            else ""
        )

    for l in live:
        code, t, ps = l["code"], l["blog"], posts[l["code"]]
        if not ps:
            continue
        for p in ps:
            members = {
                c: q
                for c, q in groups[p["hreflang_group"]].items()
                if indexable(q) == indexable(p)
            }
            canon = url(site, p)
            alts = hreflangs(members, lambda c: url(site, members[c]))
            rel = [q for q in ps if q is not p][:3]
            rv = p.get("reviewer") or {}
            img = p["image"]
            meta_line = (
                f'<p class="meta"><b>{e(t["author"])}:</b> {e(p["author"]["name"])}'
                + (
                    f" · <b>{e(t['reviewer'])}:</b> {e(rv['name'])}"
                    + (f" ({e(rv['role'])})" if rv.get("role") else "")
                    if rv.get("name")
                    else ""
                )
                + f' · {e(t["published"])} <time datetime="{p["published"]}">{p["published"]}</time>'
                + f' · {e(t["updated"])} <time datetime="{p["updated"]}">{p["updated"]}</time></p>'
                + f'<figure class="hero-img"><img src="{img["src"]}" alt="{e(img["alt"])}" width="{img["width"]}" height="{img["height"]}" fetchpriority="high"></figure>'
            )
            body = re.sub(
                r"(</h1>)", lambda m: m.group(1) + meta_line, p["body"], count=1
            )
            body = re.sub(r"<table(?![^>]*tabindex)", '<table tabindex="0"', body)
            src_html = (
                f'<section class="src"><h2>{e(t["sources"])}</h2><ul>'
                + "".join(
                    f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["title"])}</a>'
                    + (f", {e(s['publisher'])}" if s.get("publisher") else "")
                    + f" ({e(s['accessed'])})</li>"
                    for s in p["sources"]
                )
                + "</ul></section>"
                if p.get("sources")
                else ""
            )
            disclosed = bool(p.get("ai_disclosure_text"))
            how = (
                f'<section class="how"><h2>{e(t["how"] if disclosed else t["changes"])}</h2>'
                + (
                    f"<p>{e(p['ai_disclosure_text'])}</p>"
                    f"<p><b>{e(t['editor'])}:</b> {e(p['editor_responsible'])}</p>"
                    if disclosed
                    else ""
                )
                + (
                    (f"<h3>{e(t['changes'])}</h3>" if disclosed else "")
                    + "<ul>"
                    + "".join(
                        f'<li><time datetime="{c["date"]}">{c["date"]}</time>: {e(c["change"])}</li>'
                        for c in p["changelog"]
                    )
                    + "</ul>"
                    if p.get("changelog")
                    else ""
                )
                + "</section>"
                if disclosed or p.get("changelog")
                else ""
            )
            rel_html = (
                f'<section class="rel"><h2>{e(t["related"])}</h2><ul>'
                + "".join(
                    f'<li><a href="/{code}/blog/{q["slug"]}/">{e(q["title"])}</a></li>'
                    for q in rel
                )
                + "</ul></section>"
                if rel
                else ""
            )
            cta = f'<div class="cta"><p>{e(t["cta"])}</p><a href="{conf["appRegister"]}">{e(t["ctaBtn"])}</a></div>'
            crumbs = (
                f'<nav class="bc" aria-label="Breadcrumb"><a href="/{code}/">{e(t["home"])}</a> / '
                f'<a href="/{code}/blog/">{e(t["name"])}</a></nav>'
            )
            h1 = re.sub(
                r"<[^>]+>",
                "",
                re.search(r"<h1[^>]*>(.*?)</h1>", p["body"], re.S).group(1),
            ).strip()
            page_node = {
                "@type": "WebPage",
                "@id": canon + "#page",
                "url": canon,
                "name": p["title"],
                "inLanguage": l.get("inLanguage", code),
                "isPartOf": {"@id": f"{site}/#website"},
                "breadcrumb": {"@id": canon + "#crumbs"},
                "mainEntity": {"@id": canon + "#post"},
            }
            if rv.get("name"):
                page_node["reviewedBy"] = {
                    "@type": "Person",
                    "name": rv["name"],
                    **({"url": rv["url"]} if rv.get("url") else {}),
                }
            if p.get("last_fact_check"):
                page_node["lastReviewed"] = p["last_fact_check"]
            ld = {
                "@context": "https://schema.org",
                "@graph": [
                    page_node,
                    {
                        "@type": "BlogPosting",
                        "@id": canon + "#post",
                        "headline": h1,
                        "description": p["meta_description"],
                        "inLanguage": l.get("inLanguage", code),
                        "image": [site + img["src"]],
                        "datePublished": iso(p["published"]),
                        "dateModified": iso(p["updated"]),
                        "author": [
                            {
                                "@type": "Organization"
                                if p["author"].get("type") == "Organization"
                                else "Person",
                                "name": p["author"]["name"],
                                **(
                                    {"url": p["author"]["url"]}
                                    if p["author"].get("url")
                                    else {}
                                ),
                            }
                        ],
                        "publisher": {"@id": org_id},
                        "mainEntityOfPage": {"@id": canon + "#page"},
                        **(
                            {
                                "citation": [
                                    {
                                        "@type": "WebPage",
                                        "name": s["title"],
                                        "url": s["url"],
                                    }
                                    for s in p["sources"]
                                ]
                            }
                            if p.get("sources")
                            else {}
                        ),
                    },
                    {
                        "@type": "BreadcrumbList",
                        "@id": canon + "#crumbs",
                        "itemListElement": [
                            {
                                "@type": "ListItem",
                                "position": 1,
                                "name": "WeltScout",
                                "item": f"{site}/{code}/",
                            },
                            {
                                "@type": "ListItem",
                                "position": 2,
                                "name": t["name"],
                                "item": f"{site}/{code}/blog/",
                            },
                            {"@type": "ListItem", "position": 3, "name": h1},
                        ],
                    },
                ],
            }
            page = shell(
                l,
                p["title"],
                p["meta_description"],
                canon,
                alts,
                f"{crumbs}<article>{body}{src_html}{how}</article>{cta}{rel_html}",
                ld,
                indexable(p),
                img,
            )
            d = out / code / "blog" / p["slug"]
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(
                h["absolutize"](h["consent"](page, l, f"/{code}/cookie-policy/"))
            )
            written.append(f"{code}/{p['slug']}")
            if indexable(p):
                sitemap.append((canon, p["updated"], alts))
            else:
                held.append(f"{code}/{p['slug']}:{p['status']}")
            redirects += [
                {
                    "source": old,
                    "destination": f"/{code}/blog/{p['slug']}/",
                    "permanent": True,
                }
                for old in p.get("legacy", [])
            ]
        canon = f"{site}/{code}/blog/"
        langs_with = [c for c in by_code if posts.get(c)]
        alts = hreflangs(langs_with, lambda c: f"{site}/{c}/blog/")
        items = "".join(
            f'<li><a href="/{code}/blog/{p["slug"]}/">{e(p["title"])}</a><p>{e(p["meta_description"])}</p>'
            f'<time datetime="{p["updated"]}">{p["updated"]}</time></li>'
            for p in ps
        )
        ld = {
            "@context": "https://schema.org",
            "@type": "Blog",
            "@id": canon,
            "name": t["title"],
            "inLanguage": l.get("inLanguage", code),
            "publisher": {"@id": org_id},
            "blogPost": [{"@id": url(site, p) + "#post"} for p in ps if indexable(p)],
        }
        index_ok = conf["indexable"] and any(indexable(p) for p in ps)
        page = shell(
            l,
            t["title"],
            t["description"],
            canon,
            alts,
            f'<h1>{e(t["title"])}</h1><p>{e(t["description"])}</p><ul class="list">{items}</ul>',
            ld,
            index_ok,
        )
        (out / code / "blog").mkdir(parents=True, exist_ok=True)
        (out / code / "blog" / "index.html").write_text(
            h["absolutize"](h["consent"](page, l, f"/{code}/cookie-policy/"))
        )
        if index_ok:
            sitemap.append((canon, max(p["updated"] for p in ps if indexable(p)), alts))
    return {
        "posts": posts,
        "written": written,
        "sitemap": sitemap,
        "redirects": redirects,
        "held": held,
    }


def nav_link(html, code, label):
    """Adds a Blog link after the pricing link in the desktop nav, mobile nav and footer (the pair #stranke, #cenik)."""
    html, n = re.subn(
        r'(<a href="#stranke">[^<]*</a><a href="#cenik">[^<]*</a>)',
        lambda m: m.group(1) + f'<a href="/{code}/blog/">{label}</a>',
        html,
    )
    if n != 3:
        sys.exit(f"{code}: expected 3 nav places for the blog link, found {n}")
    return html
