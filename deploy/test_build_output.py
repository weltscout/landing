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


if __name__ == "__main__":
    unittest.main()
