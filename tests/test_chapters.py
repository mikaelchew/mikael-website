import json
import os
import unittest

import lxml.html

from tests.helpers import ROOT

FORBIDDEN = ["450+", "RM 28 in the bank", "Alex", "most successful partner", "50% stronger", "——", "177 hours", "5% rule",
             # superseded by Manuscript_v2.0_FINAL (44th partner on day 90; 100 'interested' people)
             "75 days", "75天", "50 interested", "50個「有興趣」"]


def data():
    with open(os.path.join(ROOT, "data", "chapters.json"), encoding="utf-8") as f:
        return json.load(f)


class ChapterDataTest(unittest.TestCase):
    def test_thirteen_chapters_in_four_parts(self):
        d = data()
        self.assertEqual(len(d["parts"]), 4)
        self.assertEqual(len(d["chapters"]), 13)
        counts = [sum(1 for c in d["chapters"] if c["part"] == p) for p in range(4)]
        self.assertEqual(counts, [3, 4, 2, 4])
        self.assertEqual([c["n"] for c in d["chapters"]], list(range(1, 14)))
        self.assertEqual([c for c in d["chapters"] if c.get("free")], [d["chapters"][0]])

    def test_every_chapter_has_both_languages_and_coordinates(self):
        for c in data()["chapters"]:
            for k in ("zh", "en", "line_en", "line_zh"):
                self.assertTrue(c[k].strip(), (c["n"], k))
            self.assertTrue(0 < c["x"] < 2400 and 0 < c["y"] < 1500, c["n"])

    def test_chapter_facts_current(self):
        blob = json.dumps(data(), ensure_ascii=False)
        for bad in FORBIDDEN:
            self.assertNotIn(bad, blob, bad)


class RenderTest(unittest.TestCase):
    def test_render_map_list(self):
        import build_chapters
        root = lxml.html.fragment_fromstring(build_chapters.render_map(data()), create_parent="div")
        items = root.xpath('//ol[contains(@class,"chapters")]/li')
        self.assertEqual(len(items), 13)
        first = items[0]
        self.assertEqual((first.get("data-x"), first.get("data-y"), first.get("data-part")), ("230", "1290", "0"))
        self.assertTrue(first.xpath('.//*[@data-en="Finding Your Dao"][@data-zh="發起召集"]'))
        self.assertTrue(first.xpath('.//a[@href="chapter-1.html"]'))
        self.assertEqual(len(root.xpath('//*[contains(@class,"part")]/h3')), 4)

    def test_render_book_cards(self):
        import build_chapters
        root = lxml.html.fragment_fromstring(build_chapters.render_book(data()), create_parent="div")
        self.assertEqual(len(root.xpath('//article[contains(@class,"brief")]')), 13)
        self.assertEqual(len(root.xpath('//*[contains(@class,"part")]/h3')), 4)

    def test_inject_between_markers_is_idempotent(self):
        import build_chapters
        page = "<p>a</p><!-- chapters:map -->old<!-- /chapters:map --><p>b</p>"
        once = build_chapters.inject(page, "map", "<ol>x</ol>")
        self.assertEqual(once, "<p>a</p><!-- chapters:map -->\n<ol>x</ol>\n<!-- /chapters:map --><p>b</p>")
        self.assertEqual(build_chapters.inject(once, "map", "<ol>x</ol>"), once)


if __name__ == "__main__":
    unittest.main()
