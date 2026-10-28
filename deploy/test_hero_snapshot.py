import re
import unittest

import hero


class HeroSnapshot(unittest.TestCase):
    SLOT = '<p>x</p><figure class="digest" data-search="audi-a4-avant"></figure>'

    def test_every_listing_rendered_and_dated(self):
        search = hero.DATA["searches"][0]
        for code in hero.DATA["locales"]:
            html = hero.render(self.SLOT, code)
            self.assertEqual(html.count("<li "), len(search["listings"]), code)
            self.assertIn(f'datetime="{search["checked"]}"', html, code)
            self.assertNotIn("{", html, code)

    def test_locale_number_and_price_formats(self):
        self.assertIn("24.840 €", hero.render(self.SLOT, "sl"))
        self.assertIn("€24,840", hero.render(self.SLOT, "en"))
        self.assertIn("24 840 €", hero.render(self.SLOT, "fr"))
        self.assertIn("27.10.2026", hero.render(self.SLOT, "de"))

    def test_mobile_rows_and_remaining_count(self):
        search, mob = hero.DATA["searches"][0], hero.DATA["mobileRows"]
        html = hero.render(self.SLOT, "sl")
        self.assertEqual(len(re.findall(r'<li class="rv dsk">', html)), len(search["listings"]) - mob)
        self.assertIn(f"Še {search['results'] - mob} drugih", html)
        self.assertIn(f"Še {search['results'] - len(search['listings'])} drugih", html)

    def test_missing_slot_fails_loudly(self):
        with self.assertRaises(SystemExit):
            hero.render("<p>no slot</p>", "sl")

    def test_unknown_search_fails_loudly(self):
        with self.assertRaises(SystemExit):
            hero.render('<figure class="digest" data-search="nope"></figure>', "sl")


if __name__ == "__main__":
    unittest.main()
