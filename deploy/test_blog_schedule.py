"""A post dated in the future is validated but stays out of the build until its day (scheduled publishing)."""
import json, os, pathlib, shutil, sys, tempfile, unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import blog  # noqa: E402

ROOT = pathlib.Path(__file__).parent.parent
SRC_POST = ROOT / "blog" / "sl" / "uvoz-avtomobila-iz-nemcije.html"


class ScheduleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.addCleanup(os.environ.pop, "BLOG_TODAY", None)
        meta, body = blog.front_matter(SRC_POST)
        self.meta, self.body = meta, body
        (self.tmp / "blog" / "sl").mkdir(parents=True)
        img = self.tmp / meta["image"]["src"].lstrip("/")
        img.parent.mkdir(parents=True, exist_ok=True)
        img.write_bytes(b"x")

    def write(self, slug, published, updated):
        m = dict(self.meta, published=published, updated=updated, last_fact_check=published, legacy=[])
        (self.tmp / "blog" / "sl" / (slug + ".html")).write_text(
            "<!--meta\n%s\n-->\n%s" % (json.dumps(m, ensure_ascii=False), self.body)
        )

    def load(self):
        return blog.load(self.tmp, [{"code": "sl"}])

    def test_future_post_is_dropped_and_reported(self):
        os.environ["BLOG_TODAY"] = "2026-11-10"
        self.write("now", "2026-11-01", "2026-11-01")
        self.write("later", "2026-11-17", "2026-11-17")
        posts, groups = self.load()
        self.assertEqual([p["slug"] for p in posts["sl"]], ["now"])
        self.assertEqual(blog.SCHEDULED, ["sl/later:2026-11-17"])

    def test_post_appears_on_its_day(self):
        self.write("later", "2026-11-17", "2026-11-17")
        os.environ["BLOG_TODAY"] = "2026-11-16"
        self.assertEqual(self.load()[0]["sl"], [])
        os.environ["BLOG_TODAY"] = "2026-11-17"
        self.assertEqual([p["slug"] for p in self.load()[0]["sl"]], ["later"])
        self.assertEqual(blog.SCHEDULED, [])

    def test_future_update_of_a_published_post_is_still_refused(self):
        os.environ["BLOG_TODAY"] = "2026-11-10"
        self.write("now", "2026-11-01", "2026-11-20")
        with self.assertRaises(SystemExit):
            self.load()

    def test_scheduled_post_is_still_validated(self):
        os.environ["BLOG_TODAY"] = "2026-11-10"
        self.write("later", "2026-11-17", "2026-11-16")
        with self.assertRaises(SystemExit):
            self.load()


if __name__ == "__main__":
    unittest.main()
