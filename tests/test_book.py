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

    def test_amazon_link_is_the_kindle_product(self):
        for page in ("book.html", "zh/book.html"):
            src = read(page)
            self.assertNotIn("AMAZON_URL_PENDING", src, page)
            hrefs = doc(page).xpath('//a[contains(@href,"amazon.")]/@href')
            self.assertEqual(hrefs, ["https://www.amazon.com/dp/B0HLDGD5M3"], page)

    def test_buy_shown_by_phase_not_hidden_attr(self):
        buy = doc("book.html").xpath('//*[@id="buy"]')[0]
        self.assertIn("when-launched", buy.get("class", ""))
        self.assertIsNone(buy.get("hidden"))
        notify = doc("book.html").xpath('//*[@id="notify"]')[0]
        self.assertIn("when-prelaunch", notify.get("class", ""))

    def test_buy_form_and_notes_carried_over(self):
        root = doc("book.html")
        form = root.xpath('//form[contains(@class,"book-buy-form")]')[0]
        self.assertEqual(sorted(form.xpath('.//input/@name')), ["edition", "edition", "email", "name"])
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
        self.assertEqual(tags, ["book-chapter", "book-english", "book-launch", "book-print"])

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


class LaunchReadyTest(unittest.TestCase):
    """Nothing on the book page or homepage may still say 'launches on 20 October' once phase is launched."""

    def test_launch_faq_is_phase_gated(self):
        root = doc("book.html")
        pre = root.xpath('//details[contains(@class,"when-prelaunch")]//summary')
        post = root.xpath('//details[contains(@class,"when-launched")]//summary')
        self.assertEqual(len(pre), 1)
        self.assertEqual(len(post), 1)
        for s in root.xpath('//script[@type="application/ld+json"]'):
            self.assertNotIn("launches on", s.text)

    def test_home_dossier_label_has_no_date(self):
        label = doc("index.html").xpath('//a[contains(@class,"dossier")]/@aria-label')[0]
        self.assertNotIn("20 October", label)


class LaunchWeekWorkbookTest(unittest.TestCase):
    """Launch-week buyers (20 to 26 Oct 2026) get the 90-Day Workbook; the offer hides itself
    from 27 Oct (js/site.js data-until), when the free email sign-up takes over."""

    def test_offer_shown_until_26_october(self):
        root = doc("book.html")
        offers = root.xpath('//*[@data-until="2026-10-26"]')
        self.assertGreaterEqual(len(offers), 3)  # hero, buy section, FAQ
        text = " ".join(o.text_content() for o in offers)
        self.assertIn("90\u2011Day Workbook", text)
        self.assertIn("20", text)
        self.assertIn("26", text)
        self.assertTrue(root.xpath('//details[@data-until="2026-10-26"]/summary'))

    def test_offer_has_chinese_copy(self):
        for o in doc("zh/book.html").xpath('//*[@data-until="2026-10-26"]'):
            self.assertIn("工作簿", o.text_content())

    def test_script_hides_expired_offers(self):
        js = read("js/site.js")
        self.assertIn("data-until", js)


class IsbnTest(unittest.TestCase):
    """eISBNs from PNM: Chinese 978-629-93072-0-4 (30 Sep 2026), English 978-629-93072-1-1 (7 Oct 2026)."""
    ZH, EN = "978-629-93072-0-4", "978-629-93072-1-1"

    def test_each_edition_shows_its_eisbn(self):
        root = doc("book.html")
        cards = root.xpath('//*[contains(@class,"edition")][.//img]')
        text = {c.xpath('string(.//img/@src)'): c.text_content() for c in cards}
        self.assertIn(self.ZH, text["images/book-cover.jpg"])
        self.assertIn(self.EN, text["images/book-cover-en.jpg"])

    def test_structured_data_carries_the_isbns(self):
        root = doc("book.html")
        book = next(b for b in (json.loads(s.text) for s in root.xpath('//script[@type="application/ld+json"]'))
                    if b.get("@type") == "Book")
        isbns = {e["inLanguage"]: e.get("isbn") for e in book["workExample"]}
        self.assertEqual(isbns, {"zh-Hant": "9786299307204", "en": "9786299307211"})
