"""Stripe checkout for cards from outside Malaysia (24 Oct 2026).
Brief: Claude_Book_Editing/publishing/Stripe_Brief.md. Billplz stays the main way to pay; Stripe is a second button.
Stripe orders use the id STRIPE-<checkout session id>, so download links, the events tab, the daily check,
resend and the course work exactly as for Billplz bills.
"""
import re
import unittest

from tests.helpers import doc, read


class StripeSiteTest(unittest.TestCase):
    def test_stripe_button_in_the_buy_form(self):
        for page in ("book.html", "zh/book.html"):
            form = doc(page).xpath('//form[contains(@class,"book-buy-form")]')[0]
            b = form.xpath('.//button[@type="submit"][@name="gateway"][@value="stripe"]')
            self.assertTrue(b, page)
            self.assertIn("Stripe", b[0].text_content(), page)
            # 24 Oct: a real (outlined) button, not a text link, so overseas buyers see it
            self.assertIn("btn--ghost", b[0].get("class"), page)
            self.assertIn("Mastercard", form.xpath('string(.//*[contains(@class,"pay-alt")])'), page)
        self.assertIn("海外", doc("zh/book.html").xpath('string(//button[@value="stripe"])'))

    def test_buy_form_sends_the_gateway(self):
        js = read("js/site.js")
        self.assertIn("e.submitter", js)
        self.assertIn("gateway: stripe ? 'stripe' : undefined", js)

    def test_thank_you_verifies_stripe_sessions(self):
        for page in ("book-thank-you.html", "zh/book-thank-you.html"):
            self.assertIn("'STRIPE-' + session", read(page), page)

    def test_store_buyers_receipt_line(self):
        for page, word in (("book.html", "receipt"), ("zh/book.html", "收據")):
            line = doc(page).xpath('string(//*[contains(@class,"store-receipt")])')
            self.assertIn(word, line, page)
            self.assertIn("mikael@mikaelchew.com", line, page)

    def test_payment_note_names_both_processors(self):
        for page in ("book.html", "zh/book.html"):
            note = doc(page).xpath('string(//span[contains(@class,"buy-note")])')
            self.assertIn("Billplz", note, page)
            self.assertIn("Stripe", note, page)


class StripeScriptTest(unittest.TestCase):
    def setUp(self):
        self.gs = read("book-delivery/apps-script.gs")

    def test_entry_points(self):
        for s in ("if (p.gateway === 'stripe') return stripeCheckout_(email, name, lang);",
                  "function pollStripe()", "function installStripePoller()",
                  "function deliverStripe_(bill)", "var STRIPE_PREFIX = 'STRIPE-';",
                  "'metadata[product]': 'ebook'", "session_id={CHECKOUT_SESSION_ID}",
                  "STRIPE_SECRET_KEY"):
            self.assertIn(s, self.gs, s)

    def test_no_keys_in_the_repo(self):
        self.assertIsNone(re.search(r"(sk|rk|pk)_(test|live)_[A-Za-z0-9]{8}", self.gs))


if __name__ == "__main__":
    unittest.main()
