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
