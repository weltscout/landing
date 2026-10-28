"""deploy/build.py output that search engines and answer engines read directly:
sitemap.xml must parse, and every alternate it lists must be a page that was built.

    python3 -m unittest deploy/test_build_output.py -v
"""

import json
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "deploy"))
import blog  # noqa: E402

CONF = json.loads((ROOT / "deploy" / "langs.json").read_text())
NS = {
    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "x": "http://www.w3.org/1999/xhtml",
}


def json_ld(html):
    return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))["@graph"]


class BuildOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "dist"
        r = subprocess.run(
            [sys.executable, str(ROOT / "deploy" / "build.py"), str(cls.out)],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            raise AssertionError(f"build failed: {r.stderr}")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def built(self, url):
        path = urlparse(url).path.strip("/")
        return any(
            (self.out / p).is_file()
            for p in (f"{path}/index.html", f"{path}.html", path or "index.html")
        )

    def test_sitemap_is_well_formed_and_lists_built_pages(self):
        tree = ET.parse(self.out / "sitemap.xml")
        urls = tree.getroot().findall("s:url", NS)
        self.assertTrue(urls)
        for u in urls:
            loc = u.find("s:loc", NS).text
            self.assertTrue(self.built(loc), loc)
            for alt in u.findall("x:link", NS):
                self.assertTrue(alt.get("hreflang"), loc)
                self.assertTrue(self.built(alt.get("href")), alt.get("href"))

    def test_every_sitemap_entry_with_alternates_lists_itself(self):
        for u in ET.parse(self.out / "sitemap.xml").getroot().findall("s:url", NS):
            alts = [a.get("href") for a in u.findall("x:link", NS)]
            if alts:
                self.assertIn(u.find("s:loc", NS).text, alts)


    # A post with an author shows that author and is edited by the team; only a post without one is signed by the team.
    def langs_with_posts(self):
        return [l for l in CONF["langs"] if any((ROOT / "blog" / l["code"]).glob("*.html"))]

    def built_posts(self):
        for l in self.langs_with_posts():
            for src in sorted((ROOT / "blog" / l["code"]).glob("*.html")):
                meta, _ = blog.front_matter(src)
                html = (self.out / l["code"] / "blog" / src.stem / "index.html").read_text()
                yield l, meta, html, src

    def team(self, l):
        ed = l["blog"]["editorial"]
        return ed, f"/{l['code']}/{ed['slug']}/", f"{CONF['site']}/#editorial"

    def check_team_node(self, graph, l, where):
        ed, _, ed_id = self.team(l)
        node = next(n for n in graph if n.get("@id") == ed_id)
        self.assertEqual(node["name"], ed["name"], where)
        self.assertEqual(node["sameAs"], CONF["org"]["sameAs"], where)
        self.assertEqual(node["parentOrganization"], {"@id": f"{CONF['site']}/#organization"}, where)

    def test_post_with_an_author_shows_the_author_and_the_team_as_editor(self):
        checked = 0
        for l, meta, html, src in self.built_posts():
            if "author" not in meta:
                continue
            ed, team_url, ed_id = self.team(l)
            self.assertIn(f"<dd>{meta['author']['name']}</dd>", html, src)
            self.assertIn(f'<dt>{ed["label"]}</dt><dd><a href="{team_url}">{ed["name"]}</a></dd>', html, src)
            self.assertNotIn('rel="author"', html, src)
            graph = json_ld(html)
            posting = next(n for n in graph if n["@type"] == "BlogPosting")
            self.assertEqual(posting["author"], [{"@type": meta["author"].get("type", "Person"), "name": meta["author"]["name"]}], src)
            self.assertEqual(posting["editor"], {"@id": ed_id}, src)
            self.check_team_node(graph, l, src)
            checked += 1
        self.assertGreater(checked, 0)

    def test_post_without_an_author_is_signed_by_the_team(self):
        checked = 0
        for l, meta, html, src in self.built_posts():
            if "author" in meta:
                continue
            ed, team_url, ed_id = self.team(l)
            self.assertIn(f'<a href="{team_url}" rel="author">{ed["name"]}</a>', html, src)
            self.assertNotIn(f'<dt>{ed["label"]}</dt>', html, src)
            graph = json_ld(html)
            posting = next(n for n in graph if n["@type"] == "BlogPosting")
            self.assertEqual(posting["author"], [{"@id": ed_id}], src)
            self.assertNotIn("editor", posting, src)
            self.check_team_node(graph, l, src)
            checked += 1
        self.assertGreater(checked, 0)

    # Posts merged into a stronger one (SEO keyword round, 28. 10. 2026): the old page is gone and
    # its URL, and the old Webflow URL it had inherited, reach the keeper in a single 301.
    CONSOLIDATED = {
        "/de/blog/gebrauchtwagen-schneller-finden/": "/de/blog/gebrauchtwagen-suchen-suchmaschine-und-suchagent/",
        "/de/post/kako-pohitriti-iskanje-avtov-na-portalih": "/de/blog/gebrauchtwagen-suchen-suchmaschine-und-suchagent/",
        "/en/blog/how-to-find-a-used-car-faster/": "/en/blog/best-place-to-find-a-used-car-online/",
        "/en/post/how-to-speed-up-the-search-for-cars-on-portals": "/en/blog/best-place-to-find-a-used-car-online/",
    }

    def test_merged_posts_redirect_once_to_a_page_that_exists_and_does_not_redirect(self):
        redirects = {r["source"]: r["destination"] for r in json.loads((self.out / "vercel.json").read_text())["redirects"]}
        for old, keeper in self.CONSOLIDATED.items():
            for form in (old.rstrip("/"), old.rstrip("/") + "/"):
                self.assertEqual(redirects.get(form), keeper, form)
            self.assertTrue(self.built(keeper), keeper)
            self.assertNotIn(keeper, redirects, f"{keeper} is itself redirected: two hops")
            if "/blog/" in old:
                self.assertFalse((self.out / old.strip("/") / "index.html").exists(), f"{old} is still built")

    def test_no_post_states_a_search_volume(self):
        # No source of absolute search volume exists (KEYWORDS.md section 1), so the front matter must not carry one.
        for l in self.langs_with_posts():
            for src in (ROOT / "blog" / l["code"]).glob("*.html"):
                self.assertNotIn("volume", blog.front_matter(src)[0]["primary_keyword"], src)

    def test_keyword_round_articles_have_answer_block_table_faq_and_dated_sources(self):
        # Articles of the 28. 10. 2026 keyword round (groups G20 and up): answer first, a table, questions, sources read that day.
        checked = 0
        for l in self.langs_with_posts():
            for src in (ROOT / "blog" / l["code"]).glob("*.html"):
                meta, body = blog.front_matter(src)
                if meta["hreflang_group"] < "G20":
                    continue
                self.assertIn('<p class="short"><strong>', body, src)
                self.assertIn("<table", body, src)
                self.assertRegex(body, r"<h3>[^<]*\?</h3>", src)
                self.assertTrue(meta.get("sources"), src)
                self.assertTrue(all(s["accessed"] == "2026-10-28" and s["url"].startswith("https://") for s in meta["sources"]), src)
                checked += 1
        self.assertGreaterEqual(checked, 7)

    def test_blog_url_without_slash_goes_to_the_hub_when_the_language_has_posts_else_to_the_home(self):
        redirects = {r["source"]: r["destination"] for r in json.loads((self.out / "vercel.json").read_text())["redirects"]}
        have = {l["code"] for l in self.langs_with_posts()}
        for l in CONF["langs"]:
            want = f"/{l['code']}/blog/" if l["code"] in have else f"/{l['code']}/"
            self.assertEqual(redirects[f"/{l['code']}/blog"], want, l["code"])
            if l["code"] in have:
                self.assertTrue(self.built(want), want)
                self.assertIn(f'href="{want}"', (self.out / l["code"] / "index.html").read_text(), l["code"])

    def test_every_language_with_posts_has_its_editorial_page(self):
        for l in self.langs_with_posts():
            self.assertTrue((self.out / l["code"] / l["blog"]["editorial"]["slug"] / "index.html").is_file(), l["code"])

    def test_editorial_page_is_in_the_sitemap_with_all_language_alternates(self):
        urls = {u.find("s:loc", NS).text: u for u in ET.parse(self.out / "sitemap.xml").getroot().findall("s:url", NS)}
        langs = self.langs_with_posts()
        for l in langs:
            loc = f"{CONF['site']}/{l['code']}/{l['blog']['editorial']['slug']}/"
            self.assertIn(loc, urls)
            alts = {a.get("hreflang"): a.get("href") for a in urls[loc].findall("x:link", NS)}
            for other in langs:
                self.assertEqual(alts[other["code"]], f"{CONF['site']}/{other['code']}/{other['blog']['editorial']['slug']}/")

    def langs(self):
        import json
        return [l["code"] for l in json.loads((ROOT / "deploy" / "langs.json").read_text())["langs"]]

    def test_every_response_carries_hsts_without_preload(self):
        import json
        cfg = json.loads((self.out / "vercel.json").read_text())
        glob = {h["key"]: h["value"] for r in cfg["headers"] if r["source"] == "/(.*)" for h in r["headers"]}
        hsts = glob.get("Strict-Transport-Security", "")
        self.assertRegex(hsts, r"^max-age=(\d+)$")
        self.assertGreaterEqual(int(hsts.split("=")[1]), 31536000)

    def test_branded_404_in_every_language_without_third_party_requests(self):
        for page in [self.out / "404.html"] + [self.out / c / "404.html" for c in self.langs()]:
            self.assertTrue(page.is_file(), page)
            html = page.read_text()
            self.assertIn('content="noindex', html, page)
            self.assertNotIn("fonts.bunny.net", html, page)
            # links to other hosts are fine; nothing may be loaded from one (fonts, styles, scripts, images)
            self.assertNotRegex(html, r'<(?:link|script|img|iframe|source|video)\b[^>]*\b(?:src|href)="(?:https?:)?//(?!www\.weltscout\.com/)', page)
            self.assertNotRegex(html, r"url\((?:['\"])?(?:https?:)?//", page)
            self.assertEqual(html.count("<h1"), 1, page)

    def test_hr_and_sr_home_titles_differ_and_hr_avoids_serbian_vocabulary(self):
        import re
        title = lambda c: re.search(r"<title>(.*?)</title>", (self.out / c / "index.html").read_text()).group(1)
        self.assertNotEqual(title("hr"), title("sr"))
        hr = (self.out / "hr" / "index.html").read_text()
        head = hr.split("</head>")[0]
        self.assertNotRegex(head, r"(?i)polovn")

    def test_no_internal_html_comments_ship(self):
        import re
        for page in self.out.rglob("*.html"):
            self.assertIsNone(re.search(r"<!--(?!\[)", page.read_text()), page)

    def home_ld(self, code):
        import json, re
        html = (self.out / code / "index.html").read_text()
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        return canon, {n["@type"]: n for n in ld["@graph"]}

    def test_social_previews_repeat_the_title_and_meta_description(self):
        # One source: og:* and twitter:* are derived from <title> and the meta description,
        # so a copy change cannot leave a stale preview behind.
        import re, html as h
        for c in self.langs():
            page = (self.out / c / "index.html").read_text()
            get = lambda pat: h.unescape(re.search(pat, page).group(1))
            title = get(r"<title>(.*?)</title>")
            desc = get(r'<meta name="description" content="([^"]*)"')
            self.assertEqual(get(r'<meta property="og:title" content="([^"]*)"'), title, c)
            self.assertEqual(get(r'<meta name="twitter:title" content="([^"]*)"'), title, c)
            self.assertEqual(get(r'<meta property="og:description" content="([^"]*)"'), desc, c)
            self.assertEqual(get(r'<meta name="twitter:description" content="([^"]*)"'), desc, c)
            self.assertEqual(len(re.findall(r'<meta property="og:title"', page)), 1, c)
            self.assertEqual(len(re.findall(r'<meta property="og:description"', page)), 1, c)

    def test_json_ld_entity_urls_point_at_the_language_page(self):
        for c in self.langs():
            canon, nodes = self.home_ld(c)
            for t in ("Organization", "WebSite", "WebApplication", "WebPage"):
                self.assertEqual(nodes[t]["url"], canon, (c, t))
            for offer in nodes["WebApplication"]["offers"]:
                self.assertEqual(offer["url"], canon + "#cenik", c)

    def test_llms_txt_lists_every_indexed_article_per_language(self):
        llms = (self.out / "llms.txt").read_text()
        posts = [u.find("s:loc", NS).text for u in ET.parse(self.out / "sitemap.xml").getroot().findall("s:url", NS)]
        posts = [u for u in posts if "/blog/" in u and not u.endswith("/blog/")]
        self.assertTrue(posts)
        for u in posts:
            self.assertIn(f"]({u})", llms)
        self.assertLess(len(llms.encode()), 40000)

    def test_api_source_is_not_crawled(self):
        robots = (self.out / "robots.txt").read_text()
        groups = [g for g in robots.split("\n\n") if "User-agent:" in g]
        self.assertTrue(groups)
        for g in groups:
            self.assertIn("Disallow: /api/", g, g)

    def test_latin_ext_font_is_preloaded_only_where_the_first_screen_needs_it(self):
        import re
        for c in self.langs():
            html = (self.out / c / "index.html").read_text()
            rng = re.search(r'geist-latin-ext\.woff2"\)[^}]*unicode-range:([^;}]+)', html).group(1)
            spans = []
            for part in rng.split(","):
                lo, _, hi = part.strip()[2:].partition("-")
                spans.append((int(lo, 16), int(hi or lo, 16)))
            # the first screen is the hero; the nav's hidden language menu does not render glyphs
            hero = re.search(r'<header class="hero">.*?</header>', html, re.S).group(0)
            copy = " ".join(re.findall(r'<h1.*?</h1>|<p class="lead".*?</p>|<div class="ctas">.*?</div>|<p class="note offer">.*?</p>', hero, re.S))
            import html as h
            first = h.unescape(re.sub(r"<[^>]+>", " ", copy))
            needs = any(lo <= ord(ch) <= hi for ch in first for lo, hi in spans)
            preloaded = bool(re.search(r'<link rel="preload" href="[^"]*geist-latin-ext\.woff2"', html))
            self.assertEqual(preloaded, needs, c)

    def test_every_same_as_is_in_json_ld_and_only_social_profiles_get_a_footer_icon(self):
        import json, re
        same = json.loads((ROOT / "deploy" / "langs.json").read_text())["org"]["sameAs"]
        html = (self.out / "sl" / "index.html").read_text()
        for url in same:
            self.assertIn(json.dumps(url), html.replace("\\/", "/"), url)
        footer = html[html.rindex("<footer"):]
        icons = re.findall(r'<div class="social">(.*?)</div>', footer, re.S)[0]
        self.assertIn("instagram.com", icons)
        self.assertNotIn("wikidata.org", icons)


class WordingRules(unittest.TestCase):
    """Portal names belong to dated data studies only; claims of constant or instant alerts are refused everywhere."""

    def parse(self, content_type, text):
        meta = {
            "title": "Test",
            "meta_description": "Test",
            "hreflang_group": "T01",
            "audience": "both",
            "content_type": content_type,
            "primary_keyword": {"term": "t", "market": "SI", "source": "t", "measured_on": "2026-10-28"},
            "editor_responsible": "WeltScout d.o.o.",
            "ai_assistance": "drafting",
            "published": "2026-10-28",
            "updated": "2026-10-28",
            "status": "review",
            "image": {"src": "/img/blog/g10.webp", "alt": "t", "width": 1600, "height": 1073},
        }
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "test.html"
            f.write_text(f"<!--meta\n{json.dumps(meta)}\n-->\n<h1>T</h1><p class=\"short\">{text}</p>")
            return blog.parse(f, ROOT)

    def test_portal_name_is_refused_in_a_guide_and_allowed_in_a_data_study(self):
        with self.assertRaises(SystemExit):
            self.parse("guide", "Most hits came from mobile.de.")
        self.assertEqual(self.parse("data-study", "Most hits came from mobile.de.")["slug"], "test")

    def test_constant_or_instant_alert_wording_is_refused_in_every_type(self):
        for kind in ("guide", "data-study"):
            for phrase in ("alerts 24/7", "real-time alerts", "instant alerts"):
                with self.assertRaises(SystemExit, msg=f"{kind}: {phrase}"):
                    self.parse(kind, phrase)

    def test_a_post_does_not_need_an_author(self):
        self.assertNotIn("author", self.parse("guide", "No author field here."))

if __name__ == "__main__":
    unittest.main()
