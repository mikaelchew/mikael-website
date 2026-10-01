import os
import unittest

from tests.helpers import ROOT, doc, read


class ChapterOneTest(unittest.TestCase):
    def test_chapter1_lang(self):
        body = doc("chapter-1.html").xpath('//article[contains(@class,"chapter-body")]')
        self.assertTrue(body)
        self.assertEqual(body[0].get("lang"), "zh-Hant")

    def test_chapter1_title_uses_plain_hyphen(self):
        h1 = doc("chapter-1.html").xpath("//h1")[0].text_content()
        self.assertIn("第一章：發起召集 - 尋找你的「道」", h1)
        self.assertNotIn("——", read("chapter-1.html"))

    def test_chapter1_ctas_follow_phase(self):
        ctas = doc("chapter-1.html").xpath('//aside[contains(@class,"chapter-cta")]')
        self.assertEqual(len(ctas), 2)
        for cta in ctas:
            self.assertTrue(cta.xpath('.//*[contains(@class,"when-prelaunch")]'))
            self.assertTrue(cta.xpath('.//*[contains(@class,"when-launched")]//a[contains(@class,"btn")] | .//a[contains(@class,"btn")][contains(@class,"when-launched")]'))

    def test_chapter1_boxes_rendered(self):
        root = doc("chapter-1.html")
        self.assertTrue(root.xpath('//blockquote[contains(@class,"epigraph")]//cite'))
        figs = root.xpath('//figure[img][figcaption]')
        self.assertEqual(len(figs), 2)
        for f in figs:
            src = f.xpath("./img/@src")[0]
            self.assertTrue(os.path.exists(os.path.join(ROOT, src)), src)
        self.assertTrue(root.xpath('//aside[contains(@class,"tip")]//li'))
        self.assertTrue(root.xpath('//aside[contains(@class,"summary")]'))

    def test_chapter1_uses_shell(self):
        src = read("chapter-1.html")
        self.assertIn("<!-- shell:header -->", src)
        self.assertIn('data-nav="book"', src)
        self.assertIn("css/site.css", src)
        self.assertNotIn("css/style.css", src)

    def test_figures_have_provenance(self):
        readme = read("images/chapter-1/README.md")
        for f in os.listdir(os.path.join(ROOT, "images", "chapter-1")):
            if f.endswith(".webp"):
                self.assertIn(f, readme, f)


class ThankYouTest(unittest.TestCase):
    def test_thanks_nav_book_and_seal(self):
        src = read("book-thank-you.html")
        self.assertIn('<body data-nav="book"', src)
        self.assertIn("#seal-sent", src)

    def test_thanks_states_kept(self):
        root = doc("book-thank-you.html")
        for state in ("ty-paid", "ty-pending", "ty-generic"):
            self.assertTrue(root.xpath('//*[@id="%s"]' % state), state)
        self.assertIn("billplz[paid]", read("book-thank-you.html"))

    def test_thanks_canonical_is_itself(self):
        root = doc("book-thank-you.html")
        self.assertEqual(root.xpath('//link[@rel="canonical"]/@href'), ["https://www.mikaelchew.com/book-thank-you.html"])
        self.assertIn('noindex', root.xpath('//meta[@name="robots"]/@content')[0])


if __name__ == "__main__":
    unittest.main()
