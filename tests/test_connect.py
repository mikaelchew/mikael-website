"""connect.html: a digital business card for people Mikael meets in person.

Opened from a QR code (images/connect-qr.svg, made by tools/make_connect_qr.py) that points to
https://www.mikaelchew.com/connect. Mikael can also open /connect#qr on his own phone to show
the code. Kept out of search results and the sitemap.
"""
import os
import unittest
import urllib.parse

from tests.helpers import ROOT, doc, read

WA = "https://wa.me/60195513038?text="
URL = "https://www.mikaelchew.com/connect"


class ConnectPageTest(unittest.TestCase):
    def test_page_uses_site_shell_and_stays_out_of_search(self):
        src = read("connect.html")
        self.assertIn("<!-- shell:header -->", src)
        root = doc("connect.html")
        self.assertEqual(root.xpath('//meta[@name="robots"]/@content'), ["noindex"])
        self.assertIn("Mikael Chew", root.xpath("string(//h1)"))
        self.assertNotIn("/connect", read("sitemap.xml"))

    def test_whatsapp_button_prefills_a_greeting_in_each_language(self):
        en = doc("connect.html").xpath('//a[starts-with(@href,"%s")]' % WA)
        self.assertTrue(en)
        self.assertIn("we just met", urllib.parse.unquote(en[0].get("href")))
        zh = doc("zh/connect.html").xpath('//a[starts-with(@href,"%s")]' % WA)
        self.assertTrue(zh)
        self.assertRegex(urllib.parse.unquote(zh[0].get("href")), r"[一-鿿]")

    def test_links_to_linkedin_book_and_chapter_one(self):
        hrefs = doc("connect.html").xpath('//main//a/@href')
        self.assertIn("https://www.linkedin.com/in/mikaelchew/", hrefs)
        self.assertIn("book.html", hrefs)
        self.assertIn("chapter-1.html", hrefs)

    def test_qr_points_at_the_page(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "images", "connect-qr.svg")))
        self.assertIn(URL, read("tools/make_connect_qr.py"))
        qr = doc("connect.html").xpath('//*[@id="qr"]//img[@src="images/connect-qr.svg"]')
        self.assertTrue(qr)
        self.assertTrue(qr[0].get("alt"))

    def test_chinese_page(self):
        root = doc("zh/connect.html")
        self.assertEqual(root.get("lang"), "zh-Hant")
        self.assertTrue(root.xpath('//*[@id="qr"]//img[@src="../images/connect-qr.svg"]'))


if __name__ == "__main__":
    unittest.main()
