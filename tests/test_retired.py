import glob
import os
import re
import unittest

from tests.helpers import ROOT, read

OLD = [
    (r"css/style\.css", "old stylesheet"),
    (r"js/main\.js", "old script"),
    (r"fontawesome", "Font Awesome"),
    (r"vendor/fonts/fonts\.css", "old font CSS"),
    (r"class=\"[^\"]*\bfa[bsr]?\s+fa-", "Font Awesome icon"),
    (r"\bfade-in\b", "old reveal class"),
    (r"data-theme", "old theme toggle"),
]


def pages():
    out = []
    for pat in ("*.html", "blog/*.html", "zh/*.html", "zh/blog/*.html"):
        out += glob.glob(os.path.join(ROOT, pat))
    return sorted(os.path.relpath(p, ROOT) for p in out)


class RetiredAssetsTest(unittest.TestCase):
    def test_nothing_references_old_assets(self):
        bad = []
        for p in pages():
            src = read(p)
            for pat, what in OLD:
                if re.search(pat, src):
                    bad.append("%s: %s" % (p, what))
        self.assertEqual(bad, [])

    def test_old_assets_deleted(self):
        for path in ("css/style.css", "js/main.js", "vendor/fontawesome", "vendor/fonts/fonts.css"):
            self.assertFalse(os.path.exists(os.path.join(ROOT, path)), path)

    def test_404_links_are_root_absolute(self):
        # GitHub Pages serves 404.html at whatever URL was missed (e.g. /blog/typo), so
        # relative links and assets would resolve against the wrong folder.
        for page in ("404.html", "zh/404.html"):
            src = read(page)
            links = re.findall(r'(?:href|src)="([^"#][^"]*)"', src)
            local = [u for u in links if not re.match(r"(https?:|mailto:|data:)", u)]
            self.assertTrue(local, page)
            self.assertEqual([u for u in local if not u.startswith("/")], [], page)

    def test_scorecard_stays_unlisted_and_untranslated(self):
        self.assertIn("'scorecard.html'", read("build_zh.py"))
        self.assertFalse(os.path.exists(os.path.join(ROOT, "zh", "scorecard.html")))
        for p in pages():
            if p != "scorecard.html":
                self.assertNotIn("scorecard.html", read(p), p)


if __name__ == "__main__":
    unittest.main()
