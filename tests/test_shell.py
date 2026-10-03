import json
import os
import re
import unittest

import lxml.html

from tests.helpers import ROOT, en_pages, zh_pages, doc, read

SAMPLE = """<!DOCTYPE html>
<html lang="en">
<head><title>t</title></head>
<body data-nav="book">
<!-- shell:header --><!-- /shell:header -->
<main id="main"><p>kept</p></main>
<!-- shell:footer --><!-- /shell:footer -->
</body>
</html>"""

UNMARKED = """<!DOCTYPE html>
<html lang="en">
<head><title>t</title></head>
<body><header class="old">old header</header><main>kept</main></body>
</html>"""


def phase():
    with open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8") as f:
        return json.load(f)["phase"]


def header_of(root):
    h = root.xpath('//header[contains(concat(" ",normalize-space(@class)," ")," bar ")]')
    return h[0] if h else None


class ApplyTest(unittest.TestCase):
    def test_apply_injects_header_and_marks_current(self):
        import build_shell
        out = build_shell.apply(SAMPLE, page="book.html", phase="prelaunch")
        root = lxml.html.fromstring(out)
        self.assertEqual(root.get("data-phase"), "prelaunch")
        self.assertIsNotNone(header_of(root))
        cur = root.xpath('//a[@data-nav="book"]')
        self.assertTrue(cur and cur[0].get("aria-current") == "page")
        self.assertFalse(root.xpath('//a[@data-nav="about"][@aria-current]'))
        self.assertTrue(root.xpath('//footer'))
        self.assertIn("<p>kept</p>", out)

    def test_apply_is_idempotent(self):
        import build_shell
        once = build_shell.apply(SAMPLE, page="book.html", phase="prelaunch")
        self.assertEqual(once, build_shell.apply(once, page="book.html", phase="prelaunch"))

    def test_apply_leaves_unmarked_page_untouched_except_phase(self):
        import build_shell
        out = build_shell.apply(UNMARKED, page="about.html", phase="launched")
        self.assertEqual(re.sub(r' data-phase="[^"]*"', "", out), UNMARKED)
        self.assertIn('data-phase="launched"', out)

    def test_lang_link_and_paths_for_blog_pages(self):
        import build_shell
        out = build_shell.apply(SAMPLE, page="blog/comeback.html", phase="prelaunch")
        root = lxml.html.fromstring(out)
        self.assertEqual(root.xpath('//a[contains(@class,"lang-link")]/@href')[0], "../zh/blog/comeback.html")
        self.assertEqual(root.xpath('//a[@data-nav="book"]/@href')[0], "../book.html")


class SiteTest(unittest.TestCase):
    def test_phase_identical_on_every_page(self):
        want = phase()
        self.assertIn(want, ("prelaunch", "launched"))
        for p in en_pages() + zh_pages():
            self.assertEqual(doc(p).get("data-phase"), want, p)

    def test_header_identical_except_current(self):
        headers = {}
        for p in en_pages():
            if "<!-- shell:header -->" not in read(p):
                continue
            h = header_of(doc(p))
            self.assertIsNotNone(h, p)
            for a in h.xpath('.//a[@aria-current]'):
                del a.attrib["aria-current"]
            for a in h.xpath('.//a[contains(@class,"lang-link")]'):
                del a.attrib["href"]  # points at each page's own zh twin by design
            # paths differ by depth (and 404.html is root-absolute); compare with the prefix removed
            headers[p] = (lxml.html.tostring(h, encoding="unicode")
                          .replace('href="../', 'href="').replace('href="/', 'href="'))
        self.assertLessEqual(len(set(headers.values())), 1, list(headers))


if __name__ == "__main__":
    unittest.main()


class LanguageSwitchTest(unittest.TestCase):
    """The EN | 中文 switch sits in the bar, outside the collapsible nav, so it is visible on
    phones without opening the menu. The language being read is lit; the other is the link."""

    def _switch(self, page):
        root = doc(page)
        sws = root.xpath('//header[contains(@class,"bar")]//*[contains(@class,"lang-switch")]')
        self.assertEqual(len(sws), 1, page)
        self.assertFalse(root.xpath('//header//nav//*[contains(@class,"lang-switch") or contains(@class,"lang-link")]'), page)
        opts = sws[0].xpath('./*[contains(@class,"lang-opt")]')
        self.assertEqual([o.text_content() for o in opts], ["EN", "中文"], page)  # same order on both sites
        cur = [o for o in opts if "is-current" in o.get("class")]
        links = [o for o in opts if o.tag == "a"]
        self.assertEqual(len(cur), 1, page)
        self.assertEqual(cur[0].get("aria-current"), "true", page)
        self.assertEqual(len(links), 1, page)
        return cur[0], links[0]

    def test_english_pages_offer_chinese(self):
        for page in ("index.html", "book.html", "blog/comeback.html"):
            cur, link = self._switch(page)
            self.assertEqual(cur.text_content(), "EN", page)
            self.assertEqual(link.text_content(), "中文", page)
            self.assertEqual(link.get("lang"), "zh-Hant", page)
            self.assertTrue(link.get("href").endswith("zh/" + ("" if page == "index.html" else page)), page)

    def test_chinese_pages_offer_english(self):
        for page in ("zh/index.html", "zh/book.html", "zh/blog/comeback.html"):
            cur, link = self._switch(page)
            self.assertEqual(cur.text_content(), "中文", page)
            self.assertEqual(link.text_content(), "EN", page)
            self.assertEqual(link.get("lang"), "en", page)

    def test_bar_cta_follows_launch_phase(self):
        root = doc("index.html")
        ctas = root.xpath('//header//a[contains(@class,"bar-cta")]')
        self.assertEqual(sorted(a.get("href") for a in ctas), ["book.html#buy", "chapter-1.html"])
        pre = [a for a in ctas if "when-prelaunch" in a.get("class")]
        self.assertEqual(pre[0].get("href"), "chapter-1.html")
