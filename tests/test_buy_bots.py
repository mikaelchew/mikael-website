"""Bot checks on the direct-buy form (20 Oct 2026). Card payments are on in Billplz, so scripted
form submissions could test stolen cards. The page sends a honeypot field and the time since the
page loaded; book-delivery/apps-script.gs rejects filled honeypots, too-fast submissions and too
many bills per email or overall, before it creates a Billplz bill. Real buyers see no change."""
import re
import unittest

from tests.helpers import doc, read

PAGES = ("book.html", "zh/book.html", "early-readers.html", "zh/early-readers.html")


class BuyFormHoneypotTest(unittest.TestCase):
    def test_each_buy_form_has_a_hidden_honeypot(self):
        for page in PAGES:
            forms = doc(page).xpath('//form[contains(@class,"book-buy-form")]')
            self.assertEqual(len(forms), 1, page)
            hp = forms[0].xpath('.//input[@name="website"]')
            self.assertEqual(len(hp), 1, page)
            wrap = hp[0].getparent()
            self.assertEqual(wrap.get("aria-hidden"), "true", page)      # screen readers skip it
            self.assertIn("hp", wrap.get("class", ""), page)               # visually hidden
            self.assertEqual(hp[0].get("tabindex"), "-1", page)            # keyboard skips it
            self.assertEqual(hp[0].get("autocomplete"), "off", page)       # autofill never fills it
            self.assertIsNone(hp[0].get("required"), page)

    def test_honeypot_is_hidden_off_screen_not_display_none(self):
        css = read("css/site.css")
        self.assertRegex(css, r"\.hp\s*\{[^}]*position:\s*absolute[^}]*left:\s*-9999px")

    def test_script_sends_honeypot_and_elapsed_time(self):
        js = read("js/site.js")
        self.assertIn("hp: form.elements.website ? form.elements.website.value : ''", js)
        self.assertIn("t: Math.round(performance.now())", js)


class DeliveryScriptBotCheckTest(unittest.TestCase):
    def setUp(self):
        self.gs = read("book-delivery/apps-script.gs")

    def test_buy_handler_checks_before_creating_a_bill(self):
        handler = self.gs[self.gs.index("function handleBuy_("):]
        handler = handler[:handler.index("\n}\n")]
        self.assertLess(handler.index("botCheck_(p, email)"), handler.index("/bills'"))

    def test_rules(self):
        self.assertIn("String(p.hp || '') !== ''", self.gs)          # honeypot filled
        self.assertIn("MIN_FORM_MS = 3000", self.gs)                   # faster than a person
        self.assertIn("PER_EMAIL_PER_HOUR = 3", self.gs)
        self.assertIn("ALL_PER_10_MIN = 30", self.gs)
        self.assertRegex(self.gs, r"alertAdmin_\('Buy form rate limit")


if __name__ == "__main__":
    unittest.main()
