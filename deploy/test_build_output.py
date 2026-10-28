"""deploy/build.py output that search engines and answer engines read directly:
sitemap.xml must parse, and every alternate it lists must be a page that was built.

    python3 -m unittest deploy/test_build_output.py -v
"""

import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
NS = {
    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "x": "http://www.w3.org/1999/xhtml",
}


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

if __name__ == "__main__":
    unittest.main()
