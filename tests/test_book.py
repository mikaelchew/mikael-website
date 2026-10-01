import json
import unittest

from tests.helpers import doc, read


def jsonld(root, kind):
    for s in root.xpath('//script[@type="application/ld+json"]'):
        d = json.loads(s.text)
        if d.get("@type") == kind:
            return d
    return None


class BookTest(unittest.TestCase):
    def test_legacy_anchors_exist(self):
        for page in ("book.html", "zh/book.html"):
            root = doc(page)
            for anchor in ("buy", "print", "chapters", "free-chapter", "notify"):
                self.assertTrue(root.xpath('//*[@id="%s"]' % anchor), (page, anchor))

    def test_buy_shown_by_phase_not_hidden_attr(self):
        buy = doc("book.html").xpath('//*[@id="buy"]')[0]
        self.assertIn("when-launched", buy.get("class", ""))
        self.assertIsNone(buy.get("hidden"))
        notify = doc("book.html").xpath('//*[@id="notify"]')[0]
        self.assertIn("when-prelaunch", notify.get("class", ""))

    def test_buy_form_and_notes_carried_over(self):
        root = doc("book.html")
        form = root.xpath('//form[contains(@class,"book-buy-form")]')[0]
        self.assertEqual(sorted(form.xpath('.//input/@name')), ["email", "name"])
        self.assertTrue(form.xpath('.//*[contains(@class,"book-buy-status")][@role="status"]'))
        text = root.xpath('//*[@id="buy"]')[0].text_content()
        for must in ("RM 29.90", "USD 9.99", "online banking (FPX)", "Ignite Ventures", "Refund policy"):
            self.assertIn(must, text, must)
        self.assertNotIn("BEST VALUE", text)

    def test_faq_no_english_edition_claim(self):
        root = doc("book.html")
        self.assertNotIn("being prepared in both English", root.text_content())
        faq = json.dumps(jsonld(root, "FAQPage"))
        self.assertNotIn("being prepared in both English", faq)
        self.assertNotIn("download Chapter 1", faq)

    def test_book_structured_data(self):
        book = jsonld(doc("book.html"), "Book")
        self.assertEqual(book["name"], "The Art of War for Direct Selling")
        self.assertEqual(book["alternateName"], "直銷孫子兵法之不戰而勝")
        self.assertEqual(book["author"]["name"], "Mikael Chew")
        self.assertEqual(book["datePublished"], "2026-10-20")

    def test_chapter_cards_from_data(self):
        root = doc("book.html")
        self.assertEqual(len(root.xpath('//*[@id="chapters"]//article[contains(@class,"brief")]')), 13)
        self.assertIn("<!-- chapters:book -->", read("book.html"))

    def test_kit_forms_and_tags(self):
        root = doc("book.html")
        tags = sorted(root.xpath('//form[@data-ajax]//input[@name="tags"]/@value'))
        self.assertEqual(tags, ["book-chapter", "book-launch", "book-print"])

    def test_no_freedom_promise_or_stat_bar(self):
        text = doc("book.html").text_content()
        self.assertNotIn("true freedom", text)
        self.assertFalse(doc("book.html").xpath('//*[contains(@class,"book-stat")]'))

    def test_book_uses_redesign_assets_only(self):
        src = read("book.html")
        for old in ("css/style.css", "js/main.js", "fontawesome", "vendor/fonts/fonts.css", "gtag('config'"):
            self.assertNotIn(old, src, old)
        self.assertIn('data-nav="book"', src)


if __name__ == "__main__":
    unittest.main()
