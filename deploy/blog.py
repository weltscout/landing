"""Blog pages for build.py, per docs/BLOG-STANDARD-202610.md.

blog/<lang>/<slug>.html -> /<lang>/blog/<slug>/ plus the /<lang>/blog/ index. A post is an
HTML body fragment (exactly one <h1>, a "Na kratko" paragraph, then H2 sections) that starts
with a JSON front matter comment holding the standard's §6.1 fields:

    <!--meta
    {"title": "...", "meta_description": "...", "hreflang_group": "...", "audience": "b2b|b2c|both",
     "content_type": "guide", "primary_keyword": {"term": "...", "market": "SI",
     "source": "where the term was seen, e.g. Google autocomplete", "measured_on": "YYYY-MM-DD"}, "secondary_keywords": [],
     "reviewer": {"name": "...", "role": "..."},
     "editor_responsible": "...", "ai_assistance": "none|research|drafting|translation",
     "ai_disclosure_text": "...", "published": "YYYY-MM-DD", "updated": "YYYY-MM-DD",
     "last_fact_check": "YYYY-MM-DD", "status": "draft|review|published",
     "sources": [{"title": "...", "publisher": "...", "url": "https://...", "accessed": "YYYY-MM-DD", "kind": "official"}],
     "image": {"src": "/img/blog/x.webp", "alt": "...", "width": 1600, "height": 900},
     "changelog": [{"date": "YYYY-MM-DD", "change": "..."}], "legacy": ["/post/old-slug"]}
    -->

Authorship: a post with "author": {"name": "...", "type": "Person|Organization", "url": "https://..."}
shows that author (JSON-LD author, Person by default). The editorial team, defined once per language in
langs.json (blog.editorial: name, slug, label), is the editor of every post: the byline line
"<label>: <name>" links to about/<code>.html (built at /<code>/<slug>/) and the JSON-LD "editor" is the
team (Organization, parentOrganization the company, sameAs from langs.json org.sameAs). Only a post
without "author" is signed by the team as its author.

Posts sharing hreflang_group are translations of each other. "legacy" lists old URLs that
301 to the post. Only statuses listed in langs.json "blogIndexStatuses" are indexable (M40:
an unreviewed AI translation is built with noindex and left out of the sitemap).

"24/7", "real-time", "instant" and "non-stop" are refused in every post. Portal names (mobile.de,
AutoScout24, ...) are refused too, except in content_type "data-study" (a dated search with numbers).

about/<code>.html is the editorial team page of a language that has posts: front matter
{"title", "meta_description", "published", "updated"}, one <h1>, a <p class="short">, H2 sections.
"""

import datetime, html as htmllib, json, math, re, sys, unicodedata
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Ljubljana")
REQUIRED = (
    "title",
    "meta_description",
    "hreflang_group",
    "audience",
    "content_type",
    "primary_keyword",
    "editor_responsible",
    "ai_assistance",
    "published",
    "updated",
    "status",
    "image",
)
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DATE = "%Y-%m-%d"
BANNED_WORDING = re.compile(r"\b(24/7|real[- ]time|instant|non[- ]stop)\b", re.I)
BANNED_PORTALS = re.compile(r"\b(mobile\.de|autoscout24|avto\.net|njuskalo|willhaben|kleinanzeigen)\b", re.I)
PORTAL_NAMES_OK = ("data-study",)

WPM = 200
UI_KEYS = ("toc", "crumbs", "table", "date")
BLOG_KEYS = ("audience", "filter", "minutes", "all", "short", "cta", "home", "name", "latest")
FEED_SIZES = ("lead", "md", "md", "sm", "sm", "sm")
FEED_REST = "row"
REL_N = 3
HOME_N = 3

CARD_CSS = (
    ".kick{display:flex;flex-wrap:wrap;align-items:center;gap:6px 16px;margin:0;font-size:14px;color:var(--tx3)}"
    ".kick time{white-space:nowrap}"
    ".tag{display:inline-flex;align-items:center;min-height:28px;padding:2px 12px;border-radius:999px;background:var(--chip);color:var(--tx);font-size:13.5px;font-weight:500;line-height:1.2}"
    ".tag:before{content:\"\";width:6px;height:6px;margin-right:8px;border-radius:50%;background:var(--acc)}"
    ".tag[data-aud=b2c]:before{background:var(--azure-400)}.tag[data-aud=both]:before{background:linear-gradient(90deg,var(--acc) 50%,var(--azure-400) 50%)}"
    ".card{position:relative;min-width:0}"
    ".card img{width:100%;height:auto;aspect-ratio:3/2;object-fit:cover;border-radius:18px;background:var(--surf2)}"
    ".card-t{min-width:0}.card .kick{margin-top:18px}"
    ".card h2,.card h3,.bi-h h1,.final h2{overflow-wrap:break-word;hyphens:auto}.card h2,.card h3{margin:10px 0 0;font-size:21px;line-height:1.2;letter-spacing:-.02em;font-weight:600;color:var(--tx);text-wrap:balance}"
    ".card h2 a,.card h3 a{color:inherit;text-decoration:none}.card h2 a:after,.card h3 a:after{content:\"\";position:absolute;inset:0;border-radius:18px}"
    ".card:hover h2 a,.card:hover h3 a{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:4px}"
    ".card a:focus-visible{outline:none}.card:focus-within{outline:2px solid var(--acc);outline-offset:8px;border-radius:20px}"
    ".card .desc{margin:10px 0 0;color:var(--tx2);font-size:16px;line-height:1.55;text-wrap:pretty}"
)

HOME_CSS = (
    ".hb{padding-top:0}.hb-h{max-width:var(--maxw);margin-left:auto;margin-right:auto;display:flex;flex-wrap:wrap;align-items:end;justify-content:space-between;gap:16px 32px}"
    ".hb-h .eyebrow{margin-bottom:12px}.hb-h h2{margin:0}"
    ".hb-all{display:inline-flex;align-items:center;gap:6px;min-height:44px;color:var(--tx);font-weight:500;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:5px}"
    ".hb-l{list-style:none;max-width:var(--maxw);margin:0 auto;padding:0 24px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32px}"
    "@media (max-width:900px){.hb-l{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.hb-l li:nth-child(3){display:none}}"
    "@media (max-width:600px){.hb-l{grid-template-columns:minmax(0,1fr);gap:28px;padding:0 16px}.hb-l li:nth-child(3){display:block}}"
    "#blog .hb-all-m{display:none}"
    "@media (max-width:600px){#blog .hb-h>.hb-all{display:none}#blog .hb-all-m{display:flex;width:max-content;margin:20px var(--gut,16px) 0}}"
)

BLOG_CSS = CARD_CSS + (
    ".prog{position:fixed;inset:0 0 auto;height:3px;z-index:60;pointer-events:none}"
    ".prog i{display:block;height:100%;background:var(--blue-500);transform:scaleX(0);transform-origin:0 50%}"
    ".ph .kick{margin-top:30px}.ph h1{margin-top:16px}.ph .crumbs [aria-current]{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}"
    ".by{display:flex;flex-wrap:wrap;gap:14px 44px;margin:30px 0 0;font-size:15px}.by dt{margin:0 0 3px;font-size:13px;color:var(--tx3)}"
    ".by dd{margin:0;color:var(--tx);font-weight:500;white-space:nowrap}.by a{color:inherit;text-underline-offset:3px}"
    ".hero-img{max-width:var(--maxw);margin:52px auto 0;padding:0 24px}"
    ".hero-img img{width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:24px;background:var(--surf2)}"
    ".post .doc{padding-top:72px}"
    ".short{margin:0 0 44px;padding:24px 28px 26px;border-radius:20px;background:var(--surf);box-shadow:var(--sh)}"
    ".short .short-k{margin:0 0 8px;font-size:14px;font-weight:600;color:var(--acc)}"
    ".short p:last-child{margin:0;font-size:19px;line-height:1.6;color:var(--tx);text-wrap:pretty}"
    ".qa{margin:1.2em 0 0;border-top:1px solid var(--line2)}.qa-i{padding:22px 0 6px;border-bottom:1px solid var(--line2)}"
    ".prose .qa-i h3{margin:0 0 .45em;font-size:19px}"
    ".prose .src,.prose .how{margin-top:72px;padding-top:28px;border-top:1px solid var(--line2);font-size:15px;line-height:1.6}"
    ".prose .src h2,.prose .how h2{margin:0 0 14px;font-size:20px}.prose .how h3{margin:20px 0 6px;font-size:16px}"
    ".src ol{padding-left:1.5em}.src li{margin:0 0 10px}.src .pub{color:var(--tx3)}"
    ".post .final,.bi .final{margin-top:112px}"
    ".final h2{font-size:clamp(30px,4vw,50px);font-weight:600;line-height:1.04;letter-spacing:-.035em;text-wrap:balance}"
    ".rel{max-width:var(--maxw);margin:96px auto 0;padding:0 24px}"
    ".rel>h2{margin:0 0 28px;font-size:clamp(24px,2.4vw,30px);font-weight:600;letter-spacing:-.025em}"
    ".rel ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32px}"
    ".bi-h{max-width:var(--maxw);margin:0 auto;padding:64px 24px 0;display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:24px 72px;align-items:end}"
    ".bi-h .crumbs{grid-column:1/-1}"
    ".bi-h h1{margin:0;font-size:clamp(40px,6vw,80px);line-height:.98;letter-spacing:-.048em;font-weight:600;max-width:15ch;text-wrap:balance}"
    ".bi-h .lead{margin:0 0 8px;font-size:19px;line-height:1.55;color:var(--tx2);max-width:40ch;text-wrap:pretty}"
    ".filt{max-width:var(--maxw);margin:48px auto 0;padding:20px 24px 0;display:flex;flex-wrap:wrap;gap:8px;border-top:1px solid var(--line)}"
    ".filt[hidden]{display:none}"
    ".filt button{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:0 16px;border-radius:999px;border:1px solid var(--line2);background:transparent;color:var(--tx2);font:500 15px Geist,'Geist Fallback',system-ui,sans-serif;cursor:pointer}"
    ".filt button:hover{color:var(--tx);border-color:var(--line3)}.filt button[aria-pressed=true]{background:var(--tx);border-color:var(--tx);color:var(--pg)}"
    ".filt .n{font-size:13px;color:var(--tx3);font-variant-numeric:tabular-nums}.filt [aria-pressed=true] .n{color:inherit}"
    ".feed{list-style:none;max-width:var(--maxw);margin:40px auto 0;padding:0 24px;display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:64px 32px}"
    ".feed>[hidden]{display:none!important}"
    ".feed [data-size=lead]{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:24px 56px;align-items:center}"
    ".feed [data-size=lead] img{aspect-ratio:4/3;border-radius:24px}.feed [data-size=lead] .kick{margin-top:0}"
    ".feed [data-size=lead] h2{margin-top:16px;font-size:clamp(30px,3.4vw,48px);line-height:1.04;letter-spacing:-.035em}"
    ".feed [data-size=lead] .desc{margin-top:18px;font-size:18px;max-width:42ch}"
    ".feed [data-size=md]{grid-column:span 6}.feed [data-size=md] img{aspect-ratio:16/10}.feed [data-size=md] h2{font-size:clamp(23px,2.2vw,28px)}"
    ".feed [data-size=sm]{grid-column:span 4}.feed [data-size=sm] .desc{display:none}"
    ".feed [data-size=row]{grid-column:span 6;display:grid;grid-template-columns:minmax(0,10rem) minmax(0,1fr);gap:16px 28px;align-items:start;padding-top:28px;margin-top:-36px;border-top:1px solid var(--line)}"
    ".feed [data-size=row] img{border-radius:14px}.feed [data-size=row] .kick{margin-top:0}.feed [data-size=row] h2{font-size:clamp(19px,1.6vw,22px)}"
    ".feed [data-size=row] .desc{font-size:15px}"
    "@media (max-width:900px){.bi-h{grid-template-columns:minmax(0,1fr);padding-top:40px}.bi-h .lead{max-width:none}"
    ".feed{gap:48px 20px}.feed [data-size=lead]{grid-template-columns:minmax(0,1fr)}.feed [data-size=lead] img{aspect-ratio:3/2}"
    ".feed [data-size=row]{grid-column:1/-1}.feed [data-size=md],.feed [data-size=sm]{grid-column:span 6}.rel ul{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.rel li:nth-child(3){display:none}}"
    "@media (max-width:600px){.bi-h,.filt,.feed,.rel{padding-left:16px;padding-right:16px}.filt{margin-top:32px}"
    ".feed{grid-template-columns:minmax(0,1fr);gap:36px}.feed>*{grid-column:1/-1!important}"
    ".feed [data-size=sm],.feed [data-size=md],.feed [data-size=row]{display:grid;grid-template-columns:6.5rem minmax(0,1fr);gap:0 16px;align-items:start;padding-top:24px;margin-top:-12px;border-top:1px solid var(--line)}"
    ".feed [data-size=sm] img,.feed [data-size=md] img,.feed [data-size=row] img{aspect-ratio:1;border-radius:12px}"
    ".feed [data-size=sm] .kick,.feed [data-size=md] .kick,.feed [data-size=row] .kick{margin-top:0;font-size:13px;gap:4px 12px}"
    ".feed [data-size] .kick .tag{display:none}.feed [data-size=lead] .kick .tag{display:inline-flex}"
    ".feed [data-size=sm] h2,.feed [data-size=md] h2,.feed [data-size=row] h2{margin-top:6px;font-size:18px}"
    ".feed [data-size=md] .desc,.feed [data-size=row] .desc{display:none}"
    ".rel ul{grid-template-columns:minmax(0,1fr);gap:28px}.rel li:nth-child(3){display:block}"
    ".hero-img{padding:0 16px;margin-top:32px}.hero-img img{aspect-ratio:3/2;border-radius:18px}.post .doc{padding-top:40px}"
    ".short{padding:20px 20px 22px}.short p:last-child{font-size:18px}.by{gap:12px 28px}}"
)

def fail(path, msg):
    sys.exit(f"{path}: {msg}")


def iso(day):
    d = datetime.datetime.strptime(day, DATE).replace(hour=8, tzinfo=TZ)
    return d.isoformat()


def front_matter(path):
    raw = path.read_text()
    m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        fail(path, "missing <!--meta {...} --> front matter")
    try:
        return json.loads(m.group(1)), raw[m.end() :]
    except json.JSONDecodeError as e:
        fail(path, f"front matter is not JSON: {e}")


def parse(path, src):
    meta, body = front_matter(path)
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
    if len(meta.get("seo_title") or meta["title"]) > 60:
        fail(path, f"title for search longer than 60 characters; shorten it or add a seo_title ({len(meta.get('seo_title') or meta['title'])})")
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
    scanned = text + " " + meta["title"] + " " + meta["meta_description"]
    hit = BANNED_WORDING.search(scanned) or (
        None if meta["content_type"] in PORTAL_NAMES_OK else BANNED_PORTALS.search(scanned)
    )
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


ABOUT_REQUIRED = ("title", "meta_description", "published", "updated")


def editorial(l):
    """The editorial team of a language (langs.json blog.editorial: name, slug, label): editor of every post, author of a post without its own."""
    t = l.get("blog", {}).get("editorial") or {}
    if not t.get("name") or not t.get("label") or not SLUG.fullmatch(t.get("slug", "")):
        sys.exit(f"{l['code']}: langs.json blog.editorial needs a name, a label and a lowercase ascii slug")
    return t


def parse_about(path):
    meta, body = front_matter(path)
    for k in ABOUT_REQUIRED:
        if not meta.get(k):
            fail(path, f"front matter field '{k}' missing")
    for k in ("published", "updated"):
        datetime.datetime.strptime(meta[k], DATE)
    if len(re.findall(r"<h1[ >]", body)) != 1 or not re.search(r'<p class="short">', body):
        fail(path, 'body needs exactly one <h1> and the <p class="short"> paragraph')
    if len(meta["meta_description"]) > 170 or len(meta["title"]) > 60:
        fail(path, "title over 60 or meta_description over 170 characters")
    hit = BANNED_WORDING.search(re.sub(r"<[^>]+>", " ", body) + meta["title"] + meta["meta_description"])
    if hit:
        fail(path, f"banned term {hit.group(0)!r}")
    meta["body"] = body
    return meta


def load(src, live):
    posts, seen_legacy, groups = {}, {}, {}
    for l in live:
        d = src / "blog" / l["code"]
        posts[l["code"]] = sorted(
            (parse(p, src) for p in d.glob("*.html")) if d.exists() else [],
            key=lambda p: (p["published"], p["updated"], p["slug"]),
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


def ui(l):
    """UI strings of a language (langs.json "ui" + "blog"); fails loudly when one is missing."""
    u, t = l.get("ui", {}), l.get("blog", {})
    miss = [k for k in UI_KEYS if not u.get(k)] + [f"blog.{k}" for k in BLOG_KEYS if not t.get(k)]
    if "{M}" in u.get("date", "") and len(u.get("months") or []) != 12:
        miss.append("months")
    if set(t.get("audience", {})) != {"b2b", "b2c", "both"}:
        miss.append("blog.audience{b2b,b2c,both}")
    if miss:
        sys.exit(f"{l['code']}: langs.json strings missing: {miss}")
    return u


def fmt_date(day, u):
    d = datetime.date.fromisoformat(day)
    return u["date"].format(d=d.day, dd=f"{d.day:02d}", m=d.month, mm=f"{d.month:02d}", y=d.year, M=(u.get("months") or [""] * 12)[d.month - 1])


def time_tag(day, u):
    return f'<time datetime="{day}">{fmt_date(day, u)}</time>'


def slugify(text):
    t = unicodedata.normalize("NFKD", htmllib.unescape(re.sub(r"<[^>]+>", "", text))).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def heading_ids(body):
    """Gives every <h2> an id (keeps existing ones); returns the body and [(id, text)] for the table of contents."""
    seen, heads = set(re.findall(r'\sid="([^"]+)"', body)), []

    def one(m):
        attrs, inner = m.group(1) or "", m.group(2)
        old = re.search(r'\sid="([^"]+)"', attrs)
        if old:
            hid = old.group(1)
        else:
            base = slugify(inner) or f"s{len(heads) + 1}"
            hid, k = base, 2
            while hid in seen:
                hid, k = f"{base}-{k}", k + 1
            seen.add(hid)
            attrs += f' id="{hid}"'
        heads.append((hid, re.sub(r"<[^>]+>", "", inner).strip()))
        return f"<h2{attrs}>{inner}</h2>"

    return re.sub(r"<h2(\s[^>]*)?>(.*?)</h2>", one, body, flags=re.S), heads


def toc(heads, u, mobile=False):
    items = "".join(f'<li><a href="#{i}">{htmllib.escape(t)}</a></li>' for i, t in heads)
    if not heads:
        return ""
    if mobile:
        return f'<details class="toc-m"><summary>{htmllib.escape(u["toc"])}</summary><ol>{items}</ol></details>'
    return f'<nav class="toc" aria-label="{htmllib.escape(u["toc"], quote=True)}"><p class="toc-h">{htmllib.escape(u["toc"])}</p><ol>{items}</ol></nav>'


def wrap_tables(body, label):
    """Scrollable, focusable region around each table, named after the section it sits in."""
    out, last = [], 0
    for m in re.finditer(r"<table\b.*?</table>", body, re.S):
        h = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", body[: m.start()], re.S)
        name = f"{label}: {re.sub(r'<[^>]+>', '', h[-1]).strip()}" if h else label
        table = re.sub(r'(<table\b[^>]*?) tabindex="0"', r"\1", m.group(0))
        out += [body[last : m.start()], f'<div class="tw" role="region" tabindex="0" aria-label="{htmllib.escape(htmllib.unescape(name), quote=True)}">{table}</div>']
        last = m.end()
    return "".join(out) + body[last:]


def qa_sections(body):
    """An H2 section made only of question H3s with answer paragraphs becomes a Q&A list."""
    parts = re.split(r"(?=<h2[\s>])", body)
    pair = r"<h3[^>]*>[^<]*\?\s*</h3>\s*(?:<p>.*?</p>\s*)+"
    for i, part in enumerate(parts):
        m = re.match(r"(<h2.*?</h2>)(.*)", part, re.S)
        if m and re.fullmatch(rf"\s*(?:{pair})+", m.group(2), re.S):
            items = re.sub(rf"({pair})", lambda x: f'<div class="qa-i">{x.group(1).strip()}</div>', m.group(2).strip(), flags=re.S)
            parts[i] = f'{m.group(1)}<div class="qa">{items}</div>'
    return "".join(parts)


def crumbs(trail, current, u):
    e = lambda v: htmllib.escape(v, quote=True)
    return (
        f'<nav class="crumbs" aria-label="{e(u["crumbs"])}"><ol>'
        + "".join(f'<li><a href="{h}">{e(n)}</a></li>' for h, n in trail)
        + f'<li aria-current="page">{e(current)}</li></ol></nav>'
    )


def minutes(p):
    return max(1, math.ceil(len(re.sub(r"<[^>]+>", " ", p["body"]).split()) / WPM))


TOC_JS = (
    "<script>(()=>{const L=[...document.querySelectorAll('.toc a')];if(!L.length||!('IntersectionObserver' in window))return;"
    "const M=new Map(L.map(a=>[decodeURIComponent(a.hash.slice(1)),a]));"
    "const io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;L.forEach(a=>a.removeAttribute('aria-current'));"
    "const a=M.get(e.target.id);if(a)a.setAttribute('aria-current','true')}),{rootMargin:'-15% 0px -75% 0px'});"
    "M.forEach((a,id)=>{const h=document.getElementById(id);if(h)io.observe(h)})})()</script>"
)
PROGRESS_JS = (
    "<script>(()=>{const a=document.querySelector('.prose'),b=document.querySelector('.prog i');if(!a||!b)return;let q=0;"
    "const f=()=>{q=0;const r=a.getBoundingClientRect(),h=r.height-innerHeight;b.style.transform='scaleX('+(h>0?Math.min(1,Math.max(0,-r.top/h)):1)+')'};"
    "const s=()=>{if(!q)q=requestAnimationFrame(f)};addEventListener('scroll',s,{passive:true});addEventListener('resize',s);f()})()</script>"
)
FILTER_JS = (
    "<script>(()=>{const g=document.querySelector('.filt'),F=document.querySelector('.feed');if(!g||!F)return;"
    "const S=F.dataset.sizes.split(','),R=F.dataset.rest,I=[...F.children];g.hidden=false;"
    "const set=f=>{g.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.f===f)));let i=0;"
    "I.forEach(li=>{const ok=f==='all'||li.dataset.aud===f||li.dataset.aud==='both';li.hidden=!ok;if(ok)li.dataset.size=S[i++]||R})};"
    "g.addEventListener('click',e=>{const b=e.target.closest('button');if(b)set(b.dataset.f)})})()</script>"
)


def _e(v):
    return htmllib.escape(str(v), quote=True)


def kick(p, t, u, date=True):
    return (
        f'<p class="kick"><span class="tag" data-aud="{p["audience"]}">{_e(t["audience"][p["audience"]])}</span>'
        f'<span>{_e(t["minutes"].format(n=minutes(p)))}</span>{time_tag(p["published"], u) if date else ""}</p>'
    )

def card(p, t, u, size, i, tag="h2"):
    img = p["image"]
    load_attr = 'fetchpriority="high"' if i == 0 else 'loading="lazy" decoding="async"'
    return (
        f'<li class="card"{f" data-size={chr(34)}{size}{chr(34)}" if size else ""} data-aud="{p["audience"]}">'
        f'<img src="{img["src"]}" alt="" width="{img["width"]}" height="{img["height"]}" {load_attr}>'
        f'<div class="card-t">{kick(p, t, u)}<{tag}><a href="/{p["lang"]}/blog/{p["slug"]}/">{_e(p["title"])}</a></{tag}>'
        f'<p class="desc">{_e(p["meta_description"])}</p></div></li>'
    )


def build(conf, out, live, sources, h):
    """h: helpers from build.py (src, page, consent, absolutize, cookie_url)."""
    site, default = conf["site"], conf["default"]
    posts, groups = load(h["src"], live)
    e = lambda v: htmllib.escape(str(v), quote=True)
    ok_status = set(conf.get("blogIndexStatuses", ["published"]))
    indexable = lambda p: conf["indexable"] and p["status"] in ok_status
    org_id = f"{site}/#organization"
    ed_id = f"{site}/#editorial"
    written, sitemap, redirects, held = [], [], [], []
    by_code = {l["code"]: l for l in live}
    abouts = {}
    for l in live:
        if posts.get(l["code"]):
            f = h["src"] / "about" / f"{l['code']}.html"
            if not f.exists():
                sys.exit(f"{l['code']}: has posts, so about/{l['code']}.html (the editorial team page) is required")
            abouts[l["code"]] = parse_about(f)
    about_path = lambda c: f"/{c}/{editorial(by_code[c])['slug']}/"

    def editorial_node(c):
        return {
            "@type": "Organization",
            "@id": ed_id,
            "name": editorial(by_code[c])["name"],
            "url": site + about_path(c),
            "parentOrganization": {"@id": org_id},
            "sameAs": conf["org"]["sameAs"],
        }

    def head(l, title, desc, canon, alts, ld, index, og_img=None):
        robots = "" if index else '<meta name="robots" content="noindex, nofollow">'
        og = (
            f'<meta property="og:image" content="{site}{og_img["src"]}"><meta property="og:image:width" content="{og_img["width"]}">'
            f'<meta property="og:image:height" content="{og_img["height"]}"><meta property="og:image:alt" content="{e(og_img["alt"])}">'
            f'<meta name="twitter:card" content="summary_large_image">'
            if og_img
            else ""
        )
        return (
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}">{robots}'
            f'<link rel="canonical" href="{canon}">{alts}'
            f'<meta property="og:type" content="{"article" if og_img else "website"}"><meta property="og:title" content="{e(title)}">'
            f'<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">'
            f'<meta property="og:locale" content="{l["locale"][0]}">{og}'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(",", ":"))}</script>'
        )

    def write(l, path, page):
        d = out / l["code"] / path
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(h["absolutize"](h["consent"](page, l, h["cookie_url"](l["code"]))))

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

    def switch(fn):
        return {c: fn(c) or (f"/{c}/blog/" if posts.get(c) else f"/{c}/") for c in by_code}

    def final(l, t):
        c = h["chrome"][l["code"]]
        return f'<section class="final band" aria-label="{e(t["cta"])}"><h2>{e(t["cta"])}</h2>{c["ctas"]}<p class="note">{c["note"]}</p></section>'

    for l in live:
        code, t, ps = l["code"], l["blog"], posts[l["code"]]
        u = ui(l)
        if not ps:
            continue
        ed = editorial(l)
        for p in ps:
            members = {
                c: q
                for c, q in groups[p["hreflang_group"]].items()
                if indexable(q) == indexable(p)
            }
            canon = url(site, p)
            alts = hreflangs(members, lambda c: url(site, members[c]))
            same = [q for q in ps if q is not p and q["audience"] in (p["audience"], "both")]
            rel = (same + [q for q in ps if q is not p and q not in same])[:REL_N]
            rv = p.get("reviewer") or {}
            img = p["image"]
            h1m = re.search(r"<h1[^>]*>(.*?)</h1>", p["body"], re.S)
            h1 = re.sub(r"<[^>]+>", "", h1m.group(1)).strip()
            body, heads = heading_ids(p["body"].replace(h1m.group(0), "", 1))
            body = wrap_tables(qa_sections(body), u["table"])
            src_html = (
                f'<section class="src" aria-labelledby="ws-sources"><h2 id="ws-sources">{e(t["sources"])}</h2><ol>'
                + "".join(
                    f'<li><a href="{e(s["url"])}" rel="noopener">{e(s["title"])}</a>'
                    + f' <span class="pub">{e(s["publisher"]) + ", " if s.get("publisher") else ""}{time_tag(s["accessed"], u)}</span></li>'
                    for s in p["sources"]
                )
                + "</ol></section>"
                if p.get("sources")
                else ""
            )
            disclosed = bool(p.get("ai_disclosure_text"))
            how = (
                f'<section class="how" aria-labelledby="ws-how"><h2 id="ws-how">{e(t["how"] if disclosed else t["changes"])}</h2>'
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
                        f'<li>{time_tag(c["date"], u)}: {e(c["change"])}</li>'
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
            heads += [(i, x) for i, x, ok in (("ws-sources", t["sources"], src_html), ("ws-how", t["how"] if disclosed else t["changes"], how)) if ok]
            body = re.sub(
                r'<p class="short">(.*?)</p>',
                lambda m: f'<div class="short"><p class="short-k">{e(t["short"])}</p><p>{m.group(1)}</p></div>{toc(heads, u, mobile=True)}',
                body,
                count=1,
                flags=re.S,
            )
            by = p.get("author") or {"name": ed["name"], "type": "Organization", "url": about_path(code), "team": True}
            author = e(by["name"])
            if by.get("url"):
                author = f'<a href="{e(by["url"])}" rel="author">{author}</a>'
            edited = (
                ""
                if by.get("team")
                else f'<div><dt>{e(ed["label"])}</dt><dd><a href="{about_path(code)}">{e(ed["name"])}</a></dd></div>'
            )
            byline = (
                f'<dl class="by"><div><dt>{e(t["author"])}</dt><dd>{author}</dd></div>'
                + edited
                + (f'<div><dt>{e(t["reviewer"])}</dt><dd>{e(rv["name"])}{f" ({e(rv['role'])})" if rv.get("role") else ""}</dd></div>' if rv.get("name") else "")
                + f'<div><dt>{e(t["published"])}</dt><dd>{time_tag(p["published"], u)}</dd></div>'
                + (f'<div><dt>{e(t["updated"])}</dt><dd>{time_tag(p["updated"], u)}</dd></div>' if p["updated"] != p["published"] else "")
                + "</dl>"
            )
            main = (
                '<div class="prog" aria-hidden="true"><i></i></div>'
                f'<header class="doc-h ph">{crumbs([(f"/{code}/", t["home"]), (f"/{code}/blog/", t["name"])], h1, u)}'
                f"{kick(p, t, u, date=False)}<h1>{h1m.group(1)}</h1>{byline}</header>"
                f'<figure class="hero-img"><img src="{img["src"]}" alt="{e(img["alt"])}" width="{img["width"]}" height="{img["height"]}" fetchpriority="high"></figure>'
                f'<div class="doc">{toc(heads, u)}<article class="prose">{body}{src_html}{how}</article></div>'
                + final(l, t)
                + (
                    f'<section class="rel" aria-labelledby="ws-rel"><h2 id="ws-rel">{e(t["related"])}</h2><ul>'
                    + "".join(card(q, t, u, None, 1, "h3") for q in rel)
                    + "</ul></section>"
                    if rel
                    else ""
                )
            )
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
                    editorial_node(code),
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
                            {"@id": ed_id}
                            if by.get("team")
                            else {
                                "@type": "Organization" if by.get("type") == "Organization" else "Person",
                                "name": by["name"],
                                **({"url": by["url"]} if by.get("url") else {}),
                            }
                        ],
                        **({} if by.get("team") else {"editor": {"@id": ed_id}}),
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
            page = h["page"](
                l,
                head(l, p.get("seo_title") or p["title"], p["meta_description"], canon, alts, ld, indexable(p), img),
                main,
                switch(lambda c: f"/{c}/blog/{members[c]['slug']}/" if c in members else None),
                BLOG_CSS,
                js=TOC_JS + PROGRESS_JS,
                cls="post",
            )
            write(l, f"blog/{p['slug']}", page)
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
                for legacy in p.get("legacy", [])
                for old in dict.fromkeys((legacy, legacy.rstrip("/") + "/"))
            ]
        canon = f"{site}/{code}/blog/"
        langs_with = [c for c in by_code if posts.get(c)]
        alts = hreflangs(langs_with, lambda c: f"{site}/{c}/blog/")
        counts = {"all": len(ps), **{a: sum(q["audience"] in (a, "both") for q in ps) for a in ("b2b", "b2c")}}
        chips = "".join(
            f'<button type="button" data-f="{f}" aria-pressed="{str(f == "all").lower()}">{e(t["all"] if f == "all" else t["audience"][f])}<span class="n">{n}</span></button>'
            for f, n in counts.items()
        )
        feed = "".join(card(p, t, u, FEED_SIZES[i] if i < len(FEED_SIZES) else FEED_REST, i) for i, p in enumerate(ps))
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
        main = (
            f'<header class="bi-h">{crumbs([(f"/{code}/", t["home"])], t["name"], u)}<h1>{e(t["title"])}</h1><p class="lead">{e(t["description"])}</p></header>'
            f'<div class="filt" role="group" aria-label="{e(t["filter"])}" hidden>{chips}</div>'
            f'<ul class="feed" data-sizes="{",".join(FEED_SIZES)}" data-rest="{FEED_REST}">{feed}</ul>'
            + final(l, t)
        )
        page = h["page"](
            l,
            head(l, t["title"], t["description"], canon, alts, ld, index_ok),
            main,
            switch(lambda c: None),
            BLOG_CSS,
            current=f"/{code}/blog/",
            js=FILTER_JS,
            cls="bi",
        )
        write(l, "blog", page)
        if index_ok:
            sitemap.append((canon, max(p["updated"] for p in ps if indexable(p)), alts))
    for code, a in abouts.items():
        l, ed = by_code[code], editorial(by_code[code])
        t, u, canon = l["blog"], ui(l), site + about_path(code)
        alts = hreflangs(list(abouts), lambda c: site + about_path(c))
        hm = re.search(r"<h1[^>]*>(.*?)</h1>", a["body"], re.S)
        h1 = re.sub(r"<[^>]+>", "", hm.group(1)).strip()
        body, heads = heading_ids(a["body"].replace(hm.group(0), "", 1))
        links = ", ".join(
            f'<a href="{e(s)}" rel="me noopener">{e(re.sub(r"^https?://(www[.])?|/$", "", s))}</a>' for s in conf["org"]["sameAs"]
        )
        body = wrap_tables(body.replace("{{SAMEAS}}", links), u["table"])
        body = re.sub(
            r'<p class="short">(.*?)</p>',
            lambda m: f'<div class="short"><p class="short-k">{e(t["short"])}</p><p>{m.group(1)}</p></div>{toc(heads, u, mobile=True)}',
            body,
            count=1,
            flags=re.S,
        )
        ld = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "AboutPage",
                    "@id": canon + "#page",
                    "url": canon,
                    "name": h1,
                    "inLanguage": l.get("inLanguage", code),
                    "isPartOf": {"@id": f"{site}/#website"},
                    "breadcrumb": {"@id": canon + "#crumbs"},
                    "mainEntity": {"@id": ed_id},
                    "datePublished": iso(a["published"]),
                    "dateModified": iso(a["updated"]),
                },
                editorial_node(code),
                {
                    "@type": "BreadcrumbList",
                    "@id": canon + "#crumbs",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "WeltScout", "item": f"{site}/{code}/"},
                        {"@type": "ListItem", "position": 2, "name": h1},
                    ],
                },
            ],
        }
        main = (
            f'<header class="doc-h">{crumbs([(f"/{code}/", t["home"])], h1, u)}<h1>{hm.group(1)}</h1>'
            f'<p class="upd">{e(t["updated"])}: {time_tag(a["updated"], u)}</p></header>'
            f'<div class="doc">{toc(heads, u)}<article class="prose">{body}</article></div>' + final(l, t)
        )
        page = h["page"](
            l,
            head(l, a["title"], a["meta_description"], canon, alts, ld, conf["indexable"]),
            main,
            {c: about_path(c) if c in abouts else f"/{c}/" for c in by_code},
            BLOG_CSS,
            current=about_path(code),
            js=TOC_JS,
            cls="post",
        )
        write(l, ed["slug"], page)
        written.append(f"{code}/{ed['slug']}")
        if conf["indexable"]:
            sitemap.append((canon, a["updated"], alts))
    index_redirects = [
        {"source": src, "destination": f"/{c}/blog/", "permanent": True}
        for c in by_code
        if posts.get(c)
        for src in ([f"/{c}/blog"] + (["/blog", "/blog/"] if c == default else []))
    ] + [
        {"source": src, "destination": f"/{c}/", "permanent": True}
        for c in by_code
        if not posts.get(c)
        for src in (f"/{c}/blog", f"/{c}/blog/")
    ]
    return {
        "posts": posts,
        "written": written,
        "sitemap": sitemap,
        "redirects": index_redirects + redirects,
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


def home_section(html, l, posts):
    """Latest HOME_N posts as blog cards before the homepage FAQ section; the page is unchanged when the language has no posts."""
    if not posts:
        return html
    t, u, code = l["blog"], ui(l), l["code"]
    sec = (
        f'<section id="blog" class="hb" aria-labelledby="hb-h"><div class="sec-h hb-h rv"><div><p class="eyebrow">{_e(t["name"])}</p>'
        f'<h2 id="hb-h">{_e(t["latest"])}</h2></div><a class="hb-all" href="/{code}/blog/">{_e(t["all"])}<span aria-hidden="true">→</span></a></div>'
        f'<ul class="hb-l">{"".join(card(p, t, u, None, 1, "h3") for p in posts[:HOME_N])}</ul>'
        f'<a class="hb-all hb-all-m" href="/{code}/blog/">{_e(t["all"])}<span aria-hidden="true">→</span></a></section>\n\n'
    )
    anchor = '<section id="vprasanja"'
    if html.count(anchor) != 1 or html.count("</head>") != 1:
        sys.exit(f"{code}: homepage needs exactly one {anchor} and one </head> for the blog section")
    return html.replace(anchor, sec + anchor).replace("</head>", f"<style>{CARD_CSS}{HOME_CSS}</style></head>")
