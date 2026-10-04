import json
import os
import unittest

from tests.helpers import ROOT, doc, read


def quotes():
    with open(os.path.join(ROOT, "data", "testimonials.json"), encoding="utf-8") as f:
        return json.load(f)


class TestimonialsTest(unittest.TestCase):
    def test_all_recommendations_shown_word_for_word(self):
        for page in ("index.html", "about.html"):
            root = doc(page)
            shown = {q.get("data-en") for q in root.xpath('//*[contains(@class,"c-grid")]//blockquote')}
            for q in quotes():
                self.assertIn(q["en"], shown, (page, q["name"]))
                self.assertTrue(root.xpath('//*[contains(@class,"c-grid")]//footer/b[text()="%s"]' % q["name"]), (page, q["name"]))

    def test_eight_real_names_and_no_stars(self):
        self.assertEqual(len(quotes()), 8)
        for page in ("index.html", "about.html", "speaking.html", "work-with-me.html"):
            self.assertNotIn("fa-star", read(page))
            self.assertNotIn("★", read(page))


if __name__ == "__main__":
    unittest.main()


class QuoteRailTest(unittest.TestCase):
    """The eight recommendations are one row that moves right-to-left as the page scrolls
    (js/site.js), and can be swiped; it stays still with reduced motion."""

    def test_rail_markup(self):
        for page in ("index.html", "about.html", "zh/index.html"):
            rail = doc(page).xpath('//*[contains(@class,"c-rail")]')
            self.assertEqual(len(rail), 1, page)
            self.assertEqual(rail[0].get("tabindex"), "0", page)
            self.assertTrue(rail[0].get("aria-label"), page)
            self.assertEqual(len(rail[0].xpath('.//article[contains(@class,"c")]')), 8, page)

    def test_rail_is_scroll_linked_and_respects_reduced_motion(self):
        js = read("js/site.js")
        self.assertIn("c-rail", js)
        self.assertIn("prefers-reduced-motion", js)
        css = read("css/site.css")
        self.assertIn(".c-rail", css)
        self.assertIn("scroll-snap-type: x", css)
