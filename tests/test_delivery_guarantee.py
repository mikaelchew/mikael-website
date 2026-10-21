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



class DownloadAndResendPagesTest(unittest.TestCase):
    EP = "https://script.google.com/macros/s/AKfycbzKakMN9ShFaqKmWRPheQBYLdvWBPTh-ZaHjMnC7xa-nlDhERL0Pn54QlwXytkOM-LM_Q/exec"

    def test_new_pages_exist_hidden_from_search(self):
        for page in ("download.html", "zh/download.html", "resend.html", "zh/resend.html"):
            root = doc(page)
            self.assertIn("noindex", root.xpath('string(//meta[@name="robots"]/@content)'), page)
            self.assertNotIn(page, read("sitemap.xml"), page)
            self.assertTrue(root.xpath('//*[@data-endpoint="%s"]' % self.EP), page)

    def test_download_page_states(self):
        for page in ("download.html", "zh/download.html"):
            root = doc(page)
            for state in ("dl-working", "dl-ready", "dl-error"):
                self.assertTrue(root.xpath('//*[@id="%s"]' % state), (page, state))
            self.assertTrue(root.xpath('//*[@id="dl-error"]/following::a[contains(@href,"resend.html")]'), page)

    def test_resend_form(self):
        root = doc("resend.html")
        form = root.xpath('//form[contains(@class,"resend-form")]')[0]
        names = sorted(form.xpath('.//input/@name'))
        self.assertEqual(names, ["billId", "email", "newEmail", "website"])
        self.assertIsNotNone(form.xpath('.//input[@name="email"]')[0].get("required"))
        self.assertTrue(root.xpath('//*[contains(@class,"rs-ok")]'))
        js = read("js/site.js")
        self.assertIn("action: 'resend'", js)
        self.assertIn("initResendForm();", js)
        self.assertIn("initDownloadPage();", js)

    def test_thank_you_offers_downloads_after_verify(self):
        for page in ("book-thank-you.html", "zh/book-thank-you.html"):
            root = doc(page)
            self.assertTrue(root.xpath('//*[@id="ty-paid"]//*[@id="ty-dl"][@hidden]'), page)
            self.assertTrue(root.xpath('//*[@id="ty-paid"]//a[contains(@href,"resend.html")]'), page)
        src = read("book-thank-you.html")
        self.assertIn("'?verify=' + encodeURIComponent(bill)", src)


class GuaranteeScriptTest(unittest.TestCase):
    def setUp(self):
        self.gs = read("book-delivery/apps-script.gs")

    def test_entry_points_and_helpers(self):
        for s in ("if (p.verify) return handleVerify_(", "if (p.dl) return handleDownload_(",
                  "if (body.action === 'resend') return handleResend_(body);",
                  "sendBook_(bill.email, bill.name, lang_(bill), bill.id);",
                  "function dailyDownloadCheck()", "function installDailyTrigger()",
                  "function sendBook_(toEmail, toName, lang, billId)", "GUARANTEE_FROM = '2026-10-19'"):
            self.assertIn(s, self.gs, s)


if __name__ == "__main__":
    unittest.main()
