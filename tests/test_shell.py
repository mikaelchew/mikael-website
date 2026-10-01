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
            # paths differ by depth; compare with the prefix removed
            headers[p] = lxml.html.tostring(h, encoding="unicode").replace('href="../', 'href="')
        self.assertLessEqual(len(set(headers.values())), 1, list(headers))


if __name__ == "__main__":
    unittest.main()
