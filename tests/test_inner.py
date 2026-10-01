import re
import unittest

from tests.helpers import doc, read

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
        # Manuscript author bio: 8 years in the field, then 15 in corporate (23 years from 2003).
        text = doc("about.html").xpath("string(//main)")
        self.assertIn("2003", text)
        self.assertIn("8 years", text)
        self.assertIn("15 years", text)
        self.assertNotRegex(text, r"\b(2009|2011|2016|2018)\b")

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
