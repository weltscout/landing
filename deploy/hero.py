"""Hero digest: renders real, dated searches from hero-snapshot.json into each homepage (imported by build.py)."""
import html as htmllib
import json
import pathlib
import re
import sys

DATA = json.loads((pathlib.Path(__file__).resolve().parent / "hero-snapshot.json").read_text())
SLOT = re.compile(r'<figure class="digest" data-search="([^"]+)"></figure>')


def die(page, msg):
    sys.exit(f"{page}: {msg}")




def num(n, loc):
    return f"{n:,}".replace(",", loc["group"])


def date_of(iso, loc):
    y, m, d = (int(x) for x in iso.split("-"))
    mon = loc.get("months", [""] * 12)[m - 1]
    return loc["date"].format(d=d, m=m, dd=f"{d:02d}", mm=f"{m:02d}", y=y, mon=mon)


def render(html, page):
    """Fill the hero digest from deploy/hero-snapshot.json (real, dated searches); fails loudly, never guesses."""
    slots = SLOT.findall(html)
    if len(slots) != 1:
        die(page, f"expected one hero digest slot, found {len(slots)}")
    search = next((x for x in DATA["searches"] if x["id"] == slots[0]), None)
    loc = DATA["locales"].get(page)
    if not search or not loc:
        die(page, f"hero snapshot: no search {slots[0]!r} or no locale {page!r}")
    e = lambda v: htmllib.escape(str(v), quote=True)
    date = date_of(search["checked"], loc)
    mob = DATA["mobileRows"]
    rows = []
    for i, x in enumerate(search["listings"]):
        price = loc["price"].format(n=num(x["price"], loc))
        meta = f"{x['year']} · {num(x['km'], loc)} km · {x['kw']} kW"
        where = f"{x['portal']}, {loc['countries'][x['country']]}"
        cls = "rv" if i < mob else "rv dsk"
        rows.append(
            f'<li class="{cls}"><img class="fl" src="img/flags/{e(x["country"])}.webp" width="18" height="13" alt="">'
            f'<div><p class="t" lang="{e(x["lang"])}">{e(x["title"])}</p><p class="m">{meta}</p><p class="s">{e(where)}</p></div>'
            f'<p class="p">{price}</p></li>'
        )
    more = lambda k: e(loc["more"].format(n=num(search["results"] - k, loc)))
    out = (
        f'<figure class="digest" data-search="{e(search["id"])}"><div class="dg-chat">'
        f'<div class="dg-top" aria-hidden="true"><span class="dg-av">W</span><b>WeltScout</b><time datetime="{e(search["checked"])}">{date}</time></div>'
        f'<div class="dg-body"><div class="dg-msg"><p class="dg-h">{e(loc["search"].format(s=search["name"]))}</p>'
        f'<p class="dg-n">{e(loc["summary"].format(n=num(search["results"], loc), p=search["portals"]))}</p>'
        f'<ol class="dg-list">{"".join(rows)}</ol>'
        f'<p class="dg-more"><span class="d">{more(len(rows))}</span><span class="mo">{more(min(mob, len(rows)))}</span></p></div></div></div>'
        f'<figcaption>{e(loc["caption"].format(date=date))}</figcaption></figure>'
    )
    return SLOT.sub(lambda _: out, html, count=1)
