import os
import re
import unittest

from tests.helpers import ROOT, doc, read


class HomeTest(unittest.TestCase):
    def test_home_content_present_without_js(self):
        root = doc("index.html")
        self.assertEqual(len(root.xpath('//ol[contains(@class,"chapters")]/li')), 13)
        self.assertTrue(root.xpath('//a[@href="chapter-1.html"][contains(@class,"btn")]'))
        kit = root.xpath('//form[@action="https://app.kit.com/forms/9983525/subscriptions"][@data-ajax]')
        self.assertTrue(kit)
        self.assertTrue(any(f.xpath('.//input[@name="tags"][@value="book-launch"]') for f in kit))
        self.assertEqual(root.xpath('//h1'), root.xpath('//h1')[:1], "exactly one h1")

    def test_home_uses_redesign_assets_only(self):
        src = read("index.html")
        for old in ("css/style.css", "js/main.js", "fontawesome", "vendor/fonts/fonts.css", "fonts.googleapis.com"):
            self.assertNotIn(old, src, old)
        for new in ("css/site.css", "css/map.css", "js/site.js", "js/map.js", "vendor/fonts/site-fonts.css"):
            self.assertIn(new, src, new)

    def test_ga4_config_only_in_site_js(self):
        self.assertNotIn("gtag('config'", read("index.html"))
        self.assertIn("G-ENGNTZ3PPC", read("index.html"))

    def test_zh_home_briefing_strings_are_chinese(self):
        root = doc("zh/index.html")
        for p in root.xpath('//ol[contains(@class,"chapters")]/li//p'):
            text = p.text_content()
            self.assertRegex(text, r"[一-鿿]", text)
            words = [w for w in re.findall(r"[A-Za-z]{4,}", text) if w not in ("FORMHD", "Aunty", "Vivian")]
            self.assertEqual(words, [], text)

    def test_zh_home_has_no_english_ui_strings(self):
        root = doc("zh/index.html")
        main = root.xpath('//main')[0]
        for el in main.xpath('.//*[@data-en][@data-zh]'):
            want = el.get("data-zh").strip()
            if el.tag in ("input", "textarea"):
                self.assertEqual(el.get("placeholder"), want)
            elif "<" not in want:
                self.assertEqual(el.text_content().strip(), want)

    def test_prints_have_phone_variant(self):
        for img in doc("index.html").xpath('//*[contains(@class,"print")]//img'):
            self.assertIn("-600.webp", img.get("srcset", ""), img.get("src"))

    def test_print_provenance(self):
        readme = read("images/print/README.md")
        for folder in ("images/print", "images/map"):
            for f in os.listdir(os.path.join(ROOT, folder)):
                if f.endswith((".webp", ".svg")):
                    self.assertIn(f, readme, f)

    def test_map_has_static_fallback_hooks(self):
        js = read("js/map.js")
        self.assertIn("deviceMemory", read("index.html"))
        self.assertIn("prefers-reduced-motion", read("index.html"))
        self.assertIn("34", js)
        self.assertIn("IntersectionObserver", js)


if __name__ == "__main__":
    unittest.main()
