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


    # Every post without its own author is signed by the language's editorial team, defined once in langs.json.
    def langs_with_posts(self):
        return [l for l in CONF["langs"] if (ROOT / "blog" / l["code"]).is_dir()]

    def test_every_post_links_to_the_editorial_page_and_its_json_ld(self):
        checked = 0
        for l in self.langs_with_posts():
            code, ed = l["code"], l["blog"]["editorial"]
            team_url = f"/{code}/{ed['slug']}/"
            self.assertTrue((self.out / code / ed["slug"] / "index.html").is_file(), team_url)
            for post in sorted((self.out / code / "blog").glob("*/index.html")):
                html = post.read_text()
                self.assertIn(f'<a href="{team_url}" rel="author">{ed["name"]}</a>', html, post)
                graph = json_ld(html)
                posting = next(n for n in graph if n["@type"] == "BlogPosting")
                self.assertEqual(posting["author"], [{"@id": f"{CONF['site']}/#editorial"}], post)
                node = next(n for n in graph if n.get("@id") == f"{CONF['site']}/#editorial")
                self.assertEqual(node["sameAs"], CONF["org"]["sameAs"], post)
                self.assertEqual(node["name"], ed["name"], post)
                checked += 1
        self.assertGreater(checked, 0)

    def test_editorial_page_is_in_the_sitemap_with_all_language_alternates(self):
        urls = {u.find("s:loc", NS).text: u for u in ET.parse(self.out / "sitemap.xml").getroot().findall("s:url", NS)}
        langs = self.langs_with_posts()
        for l in langs:
            loc = f"{CONF['site']}/{l['code']}/{l['blog']['editorial']['slug']}/"
            self.assertIn(loc, urls)
            alts = {a.get("hreflang"): a.get("href") for a in urls[loc].findall("x:link", NS)}
            for other in langs:
                self.assertEqual(alts[other["code"]], f"{CONF['site']}/{other['code']}/{other['blog']['editorial']['slug']}/")


class WordingRules(unittest.TestCase):
    """Portal names belong to dated data studies only; claims of constant or instant alerts are refused everywhere."""

    def parse(self, content_type, text):
        meta = {
            "title": "Test",
            "meta_description": "Test",
            "hreflang_group": "T01",
            "audience": "both",
            "content_type": content_type,
            "primary_keyword": {"term": "t", "market": "SI", "volume": None, "source": "t", "measured_on": "2026-10-28"},
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
