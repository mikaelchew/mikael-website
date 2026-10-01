import unittest

import lxml.html

SHELL_PAGE = """<!DOCTYPE html>
<html data-phase="prelaunch" lang="en">
<head><title>The Book — Mikael Chew</title><meta name="description" content="d"></head>
<body data-nav="book">
<a href="zh/book.html" class="lang-link keep" lang="zh-Hant" hreflang="zh-Hant">中文</a>
<h1 data-en="The Book" data-zh="著作">The Book</h1>
<span class="legend" data-zh-only><span class="v" data-en="x" data-zh="y">不戰而勝</span></span>
</body></html>"""


class ZhTransformTest(unittest.TestCase):
    def test_zh_lang_link_points_back(self):
        import build_zh
        root = lxml.html.fromstring(build_zh.transform_html(SHELL_PAGE, "book.html"))
        link = root.xpath('//a[contains(@class,"lang-link")]')[0]
        self.assertEqual(link.get("href"), "../book.html")
        self.assertEqual(link.text_content(), "English")
        self.assertEqual(link.get("lang"), "en")
        self.assertEqual(link.get("hreflang"), "en")

    def test_zh_lang_link_for_home_and_blog(self):
        import build_zh
        home = lxml.html.fromstring(build_zh.transform_html(SHELL_PAGE.replace("zh/book.html", "zh/"), "index.html"))
        self.assertEqual(home.xpath('//a[contains(@class,"lang-link")]/@href')[0], "../")
        post = lxml.html.fromstring(build_zh.transform_html(SHELL_PAGE.replace("zh/book.html", "../zh/blog/comeback.html"), "blog/comeback.html"))
        self.assertEqual(post.xpath('//a[contains(@class,"lang-link")]/@href')[0], "../../blog/comeback.html")

    def test_zh_only_untouched(self):
        import build_zh
        root = lxml.html.fromstring(build_zh.transform_html(SHELL_PAGE, "book.html"))
        self.assertEqual(root.xpath('//*[@class="v"]')[0].text_content(), "不戰而勝")

    def test_zh_skips_google_fonts_for_new_pages(self):
        import build_zh
        new = SHELL_PAGE.replace("<title>", '<link rel="stylesheet" href="css/site.css"><title>')
        self.assertNotIn("fonts.googleapis.com", build_zh.transform_html(new, "book.html"))
        self.assertIn("fonts.googleapis.com", build_zh.transform_html(SHELL_PAGE, "book.html"))

    def test_phase_carried(self):
        import build_zh
        root = lxml.html.fromstring(build_zh.transform_html(SHELL_PAGE, "book.html"))
        self.assertEqual(root.get("data-phase"), "prelaunch")
        self.assertEqual(root.get("lang"), "zh-Hant")


if __name__ == "__main__":
    unittest.main()
