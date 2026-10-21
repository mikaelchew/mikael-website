"""Delivery guarantee (21 Oct 2026): every paying buyer gets the ebook even when email fails.
Brief: Claude_Book_Editing/publishing/Delivery_Guarantee_Brief.md.

1. thank-you page: download buttons after the delivery script confirms the bill is paid;
2. tracked download links (?dl=) + a daily reminder / summary in book-delivery/apps-script.gs;
3. a self-service resend page (resend.html);
4. a WhatsApp line for buyers who can't pay (e.g. no OTP).
"""
import unittest
import urllib.parse

from tests.helpers import doc, read

WA = "https://wa.me/60195513038?text="


class TroublePayingTest(unittest.TestCase):
    def test_whatsapp_line_under_each_buy_form(self):
        for page, lang in (("book.html", "en"), ("early-readers.html", "en"),
                           ("zh/book.html", "zh"), ("zh/early-readers.html", "zh")):
            form = doc(page).xpath('//form[contains(@class,"book-buy-form")]')[0]
            line = form.xpath('./following-sibling::*[contains(@class,"pay-help")][1]') or \
                   form.xpath('.//*[contains(@class,"pay-help")]')
            self.assertTrue(line, page)
            a = line[0].xpath('.//a[starts-with(@href,"%s")]' % WA)
            self.assertTrue(a, page)
            text = urllib.parse.unquote(a[0].get("href"))
            self.assertIn("OTP", line[0].text_content(), page)
            if lang == "zh":
                self.assertIn("收不到 OTP", line[0].text_content(), page)
                self.assertRegex(text, r"[一-鿿]", page)
            else:
                self.assertIn("WhatsApp me", line[0].text_content(), page)


if __name__ == "__main__":
    unittest.main()
