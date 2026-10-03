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


class ZhHeadingBreaksTest(unittest.TestCase):
    """Chinese headings wrap only at punctuation and marked phrase boundaries, never mid-word."""

    def test_css_keeps_words_whole(self):
        from tests.helpers import read
        css = read("css/site.css")
        self.assertIn("html:lang(zh-Hant) :is(h1, h2, h3)", css)
        self.assertIn("word-break: keep-all", css)

    def test_build_marks_phrase_boundaries(self):
        import build_zh
        page = ('<!DOCTYPE html><html lang="en"><head><title>t</title></head><body>'
                '<h1 data-en="x" data-zh="把實戰淬煉的策略智慧帶上你的舞台">x</h1>'
                '<h2 data-en="y" data-zh="願景、使命與價值觀">y</h2>'
                '<h2 data-en="z" data-zh="直銷孫子兵法之不戰而勝">z</h2>'
                '<p data-en="p" data-zh="這是內文的段落">p</p></body></html>')
        out = build_zh.transform_html(page, "x.html")
        self.assertIn("實戰淬煉的<wbr>策略智慧帶上你的<wbr>舞台", out)
        self.assertIn("願景、使命<wbr>與價值觀", out)
        self.assertIn("直銷孫子兵法之<wbr>不戰而勝", out)
        self.assertIn("這是內文的段落", out)  # body text is left alone
