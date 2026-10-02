"""English edition on mikaelchew.com (launching with the Chinese edition on 20 Oct 2026).

data/site.json "english" is "off" | "preorder" | "live", set independently of the launch phase:
the English direct-buy card must only go live once the delivery script handles edition "en".
"""
import json
import os
import unittest

from tests.helpers import ROOT, doc, read

STATES = ("off", "preorder", "live")


def site():
    with open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8") as f:
        return json.load(f)


class EnglishSwitchTest(unittest.TestCase):
    def test_site_json_has_english_state(self):
        self.assertIn(site().get("english"), STATES)

    def test_every_page_carries_the_english_state(self):
        state = site()["english"]
        for page in ("index.html", "book.html", "chapter-1.html", "zh/book.html", "blog.html"):
            html = doc(page).getroottree().getroot()
            self.assertEqual(html.get("data-english"), state, page)

    def test_build_shell_writes_each_state(self):
        import build_shell
        for state in STATES:
            out = build_shell.apply('<html data-phase="prelaunch" lang="en"><body></body></html>', "x.html", "launched", state)
            self.assertIn('data-english="%s"' % state, out)
            self.assertIn('data-phase="launched"', out)

    def test_css_gates_each_state(self):
        css = read("css/site.css")
        for state in STATES:
            self.assertIn('[data-english="%s"]' % state, css)


class BookPageTest(unittest.TestCase):
    def test_both_editions_shown(self):
        root = doc("book.html")
        covers = root.xpath('//*[contains(@class,"edition")]//img/@src')
        self.assertIn("images/book-cover.jpg", covers)
        self.assertIn("images/book-cover-en.jpg", covers)
        self.assertTrue(os.path.exists(os.path.join(ROOT, "images", "book-cover-en.jpg")))
        self.assertIn("Winning Without Fighting", root.text_content())

    def test_buy_form_sends_its_edition(self):
        root = doc("book.html")
        forms = root.xpath('//form[contains(@class,"book-buy-form")]')
        self.assertEqual(len(forms), 1)
        radios = forms[0].xpath('.//input[@type="radio"][@name="edition"]')
        self.assertEqual(sorted(r.get("value") for r in radios), ["en", "zh"])
        zh = [r for r in radios if r.get("value") == "zh"][0]
        en = [r for r in radios if r.get("value") == "en"][0]
        self.assertIsNotNone(zh.get("checked"))  # the edition that is always on sale is the default
        # the English choice only shows when the delivery script sends English files
        self.assertTrue(en.xpath('ancestor::*[contains(@class,"when-en-live")]'))
        js = read("js/site.js")
        self.assertIn("edition: edition", js)

    def test_live_english_needs_its_kindle_link(self):
        root = doc("book.html")
        en_kindle = root.xpath('//a[contains(@href,"amazon.")][@data-edition="en"]')
        if site().get("english") == "live":
            self.assertTrue(en_kindle, 'add the English Kindle link (data-edition="en") before going live')
        for a in en_kindle:
            self.assertTrue(a.xpath('ancestor-or-self::*[contains(@class,"when-en-live")]'))

    def test_english_preorder_fallback_present(self):
        root = doc("book.html")
        self.assertTrue(root.xpath('//*[contains(@class,"when-en-preorder")]'))

    def test_faq_says_english_edition_exists(self):
        root = doc("book.html")
        ans = root.xpath('//details[summary[contains(., "English")]]/p')
        self.assertTrue(ans)
        text = " ".join(a.text_content() for a in ans)
        self.assertNotIn("being considered", text)
        self.assertIn("Winning Without Fighting", text)

    def test_structured_data_lists_both_editions(self):
        root = doc("book.html")
        book = [json.loads(s.text) for s in root.xpath('//script[@type="application/ld+json"]')]
        book = next(b for b in book if b.get("@type") == "Book")
        langs = sorted(e.get("inLanguage") for e in book.get("workExample", []))
        self.assertEqual(langs, ["en", "zh-Hant"])
        # the zh mirror relabels the page's language, never the English edition's
        zh = [json.loads(s.text) for s in doc("zh/book.html").xpath('//script[@type="application/ld+json"]')]
        zh = next(b for b in zh if b.get("@type") == "Book")
        self.assertEqual(sorted(e.get("inLanguage") for e in zh["workExample"]), ["en", "zh-Hant"])


class ChapterOneEnglishTest(unittest.TestCase):
    def test_english_page_reads_english(self):
        root = doc("chapter-1.html")
        body = root.xpath('//article[contains(@class,"chapter-body")]')[0]
        self.assertEqual(body.get("lang"), "en")
        self.assertIn("Chapter 1: Sound the Call", root.xpath("string(//h1)"))
        self.assertIn("Attempt 39", body.text_content())
        self.assertTrue(root.xpath('//a[@href="zh/chapter-1.html"]'))

    def test_chinese_page_reads_chinese(self):
        root = doc("zh/chapter-1.html")
        body = root.xpath('//article[contains(@class,"chapter-body")]')[0]
        self.assertEqual(body.get("lang"), "zh-Hant")
        self.assertIn("第一章：發起召集 - 尋找你的「道」", root.xpath("string(//h1)"))
        self.assertIn("第39次嘗試", body.text_content())
        self.assertTrue(root.xpath('//a[@href="../chapter-1.html"]'))

    def test_english_figures_exist(self):
        root = doc("chapter-1.html")
        srcs = root.xpath('//article[contains(@class,"chapter-body")]//figure/img/@src')
        self.assertEqual(len(srcs), 2)
        for s in srcs:
            self.assertTrue(s.endswith("-en.webp"), s)
            self.assertTrue(os.path.exists(os.path.join(ROOT, s)), s)


class SiteCopyTest(unittest.TestCase):
    def test_no_chinese_only_claims(self):
        for page in ("book.html", "chapter-1.html", "llms.txt"):
            self.assertNotIn("being considered for after launch", read(page), page)
            self.assertNotIn("The book is written in Traditional Chinese. This chapter", read(page), page)
        self.assertIn("English edition", read("llms.txt"))


if __name__ == "__main__":
    unittest.main()
