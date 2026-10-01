import os
import unittest

from tests.helpers import ROOT, read


class FontsTest(unittest.TestCase):
    def test_collect_reads_cjk_display_from_partials(self):
        import build_fonts
        chars = build_fonts.collect()
        for ch in "周俊德著作十月上市免費試讀已發送":
            self.assertIn(ch, chars, ch)
        self.assertFalse(any(ord(c) < 0x2E80 for c in chars), "only CJK should be collected")

    def test_subset_covers_display_chars(self):
        import build_fonts
        from fontTools.ttLib import TTFont
        chars = build_fonts.collect()
        for weight in (600, 900):
            path = os.path.join(ROOT, "vendor", "fonts", f"noto-serif-tc-{weight}-subset.woff2")
            cmap = TTFont(path).getBestCmap()
            missing = [c for c in chars if ord(c) not in cmap]
            self.assertEqual(missing, [], weight)

    def test_subset_is_small(self):
        for weight in (600, 900):
            size = os.path.getsize(os.path.join(ROOT, "vendor", "fonts", f"noto-serif-tc-{weight}-subset.woff2"))
            self.assertLess(size, 150 * 1024, weight)

    def test_overpass_latin_weights_present(self):
        for w in (400, 600, 800, 900):
            self.assertTrue(os.path.exists(os.path.join(ROOT, "vendor", "fonts", f"overpass-{w}-latin.woff2")), w)

    def test_font_css_declares_families(self):
        css = read("vendor/fonts/site-fonts.css")
        self.assertIn("font-family: 'Overpass'", css)
        self.assertIn("font-family: 'Noto Serif TC Display'", css)
        self.assertEqual(css.count("font-display: swap"), 6)


if __name__ == "__main__":
    unittest.main()
