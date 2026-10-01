import datetime
import glob
import json
import os
import re
import unittest

from tests.helpers import ROOT, doc, read

# Words the new posts must not use: no income, earnings or financial-freedom claims
# (standing rule for all Zinzino and book copy).
FORBIDDEN = [r"passive income", r"financial freedom", r"\bincome\b", r"\bearn(ing|ings)?\b", r"guarantee",
             r"被動收入", r"財務自由", r"收入", r"保證"]


def sources():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "content", "posts", "*.json"))):
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def index():
    with open(os.path.join(ROOT, "data", "posts.json"), encoding="utf-8") as f:
        return {p["slug"]: p for p in json.load(f)}


class NewPostsTest(unittest.TestCase):
    def test_each_source_renders_a_post(self):
        for s in sources():
            page = "blog/%s.html" % s["slug"]
            root = doc(page)
            self.assertTrue(root.xpath('//article[contains(@class,"post")]//div[contains(@class,"post-body")]'), page)
            self.assertEqual(root.xpath("//h1/@data-zh"), [s["title_zh"]], page)
            ld = [json.loads(x.text) for x in root.xpath('//script[@type="application/ld+json"]')]
            post = next(x for x in ld if x.get("@type") == "BlogPosting")
            self.assertEqual(post["datePublished"], s["date"], page)
            self.assertTrue(os.path.exists(os.path.join(ROOT, "zh", page)), page)

    def test_sources_are_in_the_index(self):
        idx = index()
        for s in sources():
            self.assertIn(s["slug"], idx)
            self.assertEqual(idx[s["slug"]]["date"], s["date"])
            self.assertEqual(idx[s["slug"]]["title_zh"], s["title_zh"])

    def test_one_post_a_week_without_gaps(self):
        dates = sorted(datetime.date.fromisoformat(p["date"]) for p in index().values())
        new = sorted(datetime.date.fromisoformat(s["date"]) for s in sources())
        if not new:
            return
        last_old = max(d for d in dates if d < new[0])
        steps = [(b - a).days for a, b in zip([last_old] + new, new)]
        self.assertEqual(set(steps), {7}, steps)

    def test_no_income_or_guarantee_language(self):
        for s in sources():
            text = json.dumps(s, ensure_ascii=False)
            for pat in FORBIDDEN:
                self.assertIsNone(re.search(pat, text, re.I), (s["slug"], pat))

    def test_voice_rules(self):
        # Mikael's anti-AI writing rules (Vault/100 Areas/Identity/anti-ai-writing-style.md)
        banned = ["delve", "harness", "tapestry", "paradigm", "cutting-edge", "revolutioni", "landscape", "synergy",
                  "leverage", "game-changer", "unlock", "realm", "showcase", "vibrant", "unparalleled",
                  "groundbreaking", "utiliz", "foster", "pivotal", "testament", "commendable", "meticulous",
                  "navigat", "empower", "journey", "elevate", "robust", "holistic", "streamline", "spearhead",
                  "uncover", "ignite", "embark", "underscore", "furthermore", "moreover", "notably",
                  "it's worth noting", "interestingly", "in today's world", "at the end of the day",
                  "let's dive", "here's the thing"]
        for s in sources():
            en = " ".join(x for b in s["blocks"] for x in ([b[1]] if b[0] != "ul" else [e for e, _ in b[1]]))
            en += " " + " ".join([s["title_en"], s["excerpt_en"], s["description_en"]])
            low = en.lower()
            for w in banned:
                self.assertNotIn(w, low, (s["slug"], w))
            self.assertLessEqual(en.count("—"), 2, (s["slug"], "em dashes"))
            self.assertLessEqual(en.count("..."), 1, (s["slug"], "ellipses"))

    def test_no_raw_entities_in_visible_text(self):
        # build_zh only parses data-zh as markup when it contains "<", so an escaped entity
        # would show as literal "&larr;" on the Chinese page.
        for s in sources():
            for page in ("blog/%s.html" % s["slug"], "zh/blog/%s.html" % s["slug"]):
                text = doc(page).xpath("string(//body)")
                self.assertIsNone(re.search(r"&[a-z]+;", text), page)

    def test_sitemap_skips_future_posts(self):
        today = datetime.date.today().isoformat()
        xml = read("sitemap.xml")
        for s in sources():
            listed = "/blog/%s.html</loc>" % s["slug"] in xml
            self.assertEqual(listed, s["date"] <= today, s["slug"])

    def test_chinese_has_no_double_dash(self):
        for s in sources():
            self.assertNotIn("——", read("zh/blog/%s.html" % s["slug"]), s["slug"])

    def test_neighbours_link_both_ways(self):
        order = sorted(index().values(), key=lambda p: p["date"])
        slugs = [p["slug"] for p in order]
        for s in sources():
            i = slugs.index(s["slug"])
            root = doc("blog/%s.html" % s["slug"])
            prev = root.xpath('//nav[contains(@class,"post-nav")]/a[contains(@class,"prev")]/@href')
            self.assertEqual(prev, ["%s.html" % slugs[i - 1]], s["slug"])
            if i + 1 < len(slugs):
                nxt = root.xpath('//nav[contains(@class,"post-nav")]/a[contains(@class,"next")]/@href')
                self.assertEqual(nxt, ["%s.html" % slugs[i + 1]], s["slug"])
        first = [s for s in sources() if slugs.index(s["slug"]) == slugs.index("winning-gen-z") + 1]
        if first:
            nxt = doc("blog/winning-gen-z.html").xpath('//nav[contains(@class,"post-nav")]/a[contains(@class,"next")]/@href')
            self.assertEqual(nxt, ["%s.html" % first[0]["slug"]])


if __name__ == "__main__":
    unittest.main()
