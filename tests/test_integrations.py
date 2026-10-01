import os
import re
import subprocess
import unittest

from tests.helpers import ROOT, en_pages, doc, read

# Every GA4 event js/main.js sends on main as of 2026-10-01 (spec §8.1: none may regress).
GA4_EVENTS = [
    "begin_checkout", "whatsapp_click", "social_click", "social_share", "file_download",
    "newsletter_subscribe", "long_game_waitlist", "book_waitlist", "book_launch_waitlist",
    "book_print_waitlist", "scroll_depth", "blog_filter_click", "blog_show_more_click",
    "language_toggle",
]
KIT_FORMS = {"9983525", "9983575", "9983582"}
# Every tag value in use on main as of 2026-10-01.
KIT_TAGS = {"book-launch", "book-print", "book-chapter", "long-game-launch", "newsletter"}
TOKENS = {
    "--table": "#22303A", "--table-deep": "#19242C", "--acetate": "#F2F2EE", "--mute": "#B9C4C0",
    "--contour": "#B6C4BE", "--red": "#C0392B", "--red-lit": "#F0705F", "--red-text": "#A93226",
    "--paper": "#F5F0E8", "--ink": "#1A1A1A",
    "--ease-out": "cubic-bezier(.23,1,.32,1)", "--ease-move": "cubic-bezier(.77,0,.175,1)",
    "--ease-impact": "cubic-bezier(.55,0,1,.45)",
}


class SiteJsTest(unittest.TestCase):
    def setUp(self):
        self.js = read("js/site.js")

    def test_ga4_events_present(self):
        for name in GA4_EVENTS:
            self.assertIn("'%s'" % name, self.js, name)

    def test_preview_hosts_use_debug_mode(self):
        self.assertIn("www.mikaelchew.com", self.js)
        self.assertIn("debug_mode", self.js)

    def test_ajax_forms_fall_back_to_normal_post(self):
        self.assertIn("form[data-ajax]", self.js)
        self.assertIn("no-cors", self.js)
        self.assertRegex(self.js, r"\.submit\(\)")

    def test_buy_form_handler_ported(self):
        self.assertIn(".book-buy-form[data-endpoint]", self.js)
        self.assertIn("text/plain;charset=utf-8", self.js)
        self.assertIn("action: 'buy'", self.js)


class SiteCssTest(unittest.TestCase):
    def test_tokens_exact(self):
        css = read("css/site.css")
        for name, value in TOKENS.items():
            self.assertRegex(css, re.escape(name) + r"\s*:\s*" + re.escape(value) + r"\s*;", name)

    def test_phase_rules(self):
        css = read("css/site.css")
        self.assertIn('[data-phase="prelaunch"] .when-launched', css)
        self.assertIn('[data-phase="launched"] .when-prelaunch', css)

    def test_reduced_motion_supported(self):
        self.assertIn("prefers-reduced-motion", read("css/site.css"))


class FormsTest(unittest.TestCase):
    def test_forms_keep_action_and_method(self):
        for p in en_pages():
            for f in doc(p).xpath("//form[@data-ajax]"):
                action = f.get("action", "")
                self.assertTrue(action.startswith("https://app.kit.com/forms/") or action == "https://formspree.io/f/xreojdqa", (p, action))
                self.assertEqual(f.get("method", "").lower(), "post", p)

    def test_kit_ids_and_tags_valid(self):
        for p in en_pages():
            for f in doc(p).xpath('//form[starts-with(@action,"https://app.kit.com/forms/")]'):
                fid = f.get("action").split("/forms/")[1].split("/")[0]
                self.assertIn(fid, KIT_FORMS, p)
                for tag in f.xpath('.//input[@name="tags"]/@value'):
                    self.assertIn(tag, KIT_TAGS, (p, tag))

    def test_buy_form_endpoint_unchanged(self):
        main_book = subprocess.run(["git", "show", "722e978:book.html"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        want = re.search(r'class="book-buy-form" data-endpoint="([^"]+)"', main_book).group(1)
        got = doc("book.html").xpath("//form[contains(@class,'book-buy-form')]/@data-endpoint")
        self.assertEqual(got, [want])


if __name__ == "__main__":
    unittest.main()
