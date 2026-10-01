import os
import re
import unittest

import lxml.html

from tests.helpers import ROOT, doc, read

INNER = ("about.html", "speaking.html", "work-with-me.html", "concepts.html", "contact.html")


class InnerPagesTest(unittest.TestCase):
    def test_inner_use_shell(self):
        for page in INNER + tuple("zh/" + p for p in INNER):
            src = read(page)
            self.assertIn("<!-- shell:header -->", src, page)
            self.assertIn("<!-- shell:footer -->", src, page)
            self.assertIn("css/site.css", src, page)
            self.assertNotIn("css/style.css", src, page)

    def test_inner_nav_marks_current_page(self):
        expected = {"about.html": "about", "speaking.html": "speaking",
                    "work-with-me.html": "work", "concepts.html": "writing", "contact.html": "contact"}
        for page, nav in expected.items():
            self.assertEqual(doc(page).xpath("//body/@data-nav"), [nav], page)

    def test_contact_formspree(self):
        root = doc("contact.html")
        forms = root.xpath('//form[@data-ajax][@action="https://formspree.io/f/xreojdqa"]')
        self.assertEqual(len(forms), 1)
        self.assertTrue(forms[0].xpath('following::*[contains(@class,"form-ok")]'))

    def test_formspree_posted_as_ajax_json(self):
        # Formspree only records a fetch submission (no reCAPTCHA page) when it asks for JSON,
        # and only then can the page tell a failure from a success.
        js = read("js/site.js")
        self.assertIn("formspree.io", js)
        self.assertIn("'Accept': 'application/json'", js)
        self.assertIn("res.ok", js)

    def test_about_timeline_facts(self):
        # Mikael, 2026-10-01: 2003-09 in the field with the first company, then corporate from 2009;
        # a second field spell (2016-17, another company) makes 8 field years in total, 15 corporate.
        # Spec §6.4: the 2016-18 period is not described specifically.
        text = doc("about.html").xpath("string(//main)")
        for fact in ("2003", "2009", "8 years", "15 years"):
            self.assertIn(fact, text)
        self.assertNotRegex(text, r"\b(2011|2016|2017|2018)\b")

    def test_no_return_to_field_claim(self):
        # Mikael, 2026-10-02: the site must not say he is moving back to the field in 2026.
        for page in ("about.html", "zh/about.html", "index.html", "zh/index.html"):
            src = read(page)
            # ("field leaders" as a general term elsewhere on the page is fine)
            for phrase in ("full circle", "corporate chair", "back to the field", "Author and field leader",
                           "ground up again", "重返前線", "回歸原點", "作者與前線領袖", "重新從零"):
                self.assertNotIn(phrase, src, (page, phrase))

    def test_no_boardroom_wording(self):
        # Mikael, 2026-10-02: say "management" / "corporate management", never "boardroom".
        import glob
        for p in glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "blog", "*.html")):
            text = lxml.html.parse(p).getroot().xpath("string(//body)")
            attrs = " ".join(lxml.html.parse(p).getroot().xpath("//@data-en | //@alt"))
            self.assertNotIn("boardroom", (text + attrs).lower(), os.path.relpath(p, ROOT))

    def test_no_invented_outcomes(self):
        root = doc("work-with-me.html")
        for q in root.xpath("//blockquote"):
            q.getparent().remove(q)
        text = root.xpath("string(//main)").lower()
        self.assertNotIn("%", text)
        self.assertNotIn("income", text)
        self.assertNotIn("results guaranteed", text)

    def test_inner_no_em_dash_in_chinese(self):
        for page in INNER:
            self.assertNotIn("——", read("zh/" + page), page)


if __name__ == "__main__":
    unittest.main()
