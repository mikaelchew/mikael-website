import glob
import json
import os
import re
import subprocess
import unittest

import lxml.html

from tests.helpers import ROOT, doc, read

CHROME = ("breadcrumb", "share-section", "post-share", "post-cta", "post-nav", "related-posts")


def posts():
    return sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "blog", "*.html")))


def on_main(path):
    try:
        out = subprocess.run(["git", "show", "main:" + path], cwd=ROOT, capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None  # a post that is new on this branch
    return lxml.html.fromstring(out)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def old_body_text(root):
    box = root.xpath('//section[contains(@class,"post-content")]/div[contains(@class,"container")]')[0]
    keep = [el for el in box if not any(c in (el.get("class") or "") for c in CHROME)]
    return norm(" ".join(el.text_content() for el in keep if isinstance(el.tag, str)))


def meta(root):
    return (
        root.xpath("string(//title)"),
        root.xpath('//meta[@name="description"]/@content'),
        root.xpath('//link[@rel="canonical"]/@href'),
        [json.loads(s.text) for s in root.xpath('//script[@type="application/ld+json"]')],
    )


class WritingTest(unittest.TestCase):
    def test_post_text_unchanged(self):
        checked = 0
        for p in posts():
            old = on_main(p)
            if old is None:
                continue
            body = doc(p).xpath('//article[contains(@class,"post")]//div[contains(@class,"post-body")]')
            self.assertEqual(len(body), 1, p)
            self.assertEqual(norm(body[0].text_content()), old_body_text(old), p)
            checked += 1
        self.assertGreaterEqual(checked, 25)

    def test_post_meta_unchanged(self):
        for p in posts():
            old = on_main(p)
            if old is not None:
                self.assertEqual(meta(doc(p)), meta(old), p)

    def test_posts_use_shell(self):
        for p in posts():
            src = read(p)
            self.assertIn("<!-- shell:header -->", src, p)
            self.assertIn('<body data-nav="writing"', src, p)
            self.assertNotIn("css/style.css", src, p)
            self.assertNotIn("fa-", src, p)

    def test_post_meta_line_has_author_date_and_read_time(self):
        for p in posts():
            spans = doc(p).xpath('//header[contains(@class,"post-head")]/p[contains(@class,"meta")]/span')
            self.assertEqual(len(spans), 3, p)

    def test_blog_filter_events(self):
        root = doc("blog.html")
        self.assertGreaterEqual(len(root.xpath('//button[contains(@class,"blog-filter")][@data-filter]')), 7)
        self.assertTrue(root.xpath('//*[@id="blog-show-more"]//button'))

    def test_index_lists_every_post_with_its_date(self):
        root = doc("blog.html")
        for p in posts():
            ld = [json.loads(s.text) for s in doc(p).xpath('//script[@type="application/ld+json"]')]
            date = next(x["datePublished"] for x in ld if "datePublished" in x)[:10]
            items = root.xpath('//*[contains(concat(" ",@class," ")," dispatch ")][.//a[@href="%s"]]' % p)
            self.assertEqual(len(items), 1, p)
            self.assertEqual(items[0].get("data-pubdate"), date, p)

    def test_index_cards_show_post_image(self):
        with open(os.path.join(ROOT, "data", "posts.json"), encoding="utf-8") as f:
            index = {p["slug"]: p for p in json.load(f)}
        root = doc("blog.html")
        for slug, p in index.items():
            card = root.xpath('//li[contains(concat(" ",@class," ")," dispatch ")][.//a[@href="blog/%s.html"]]' % slug)[0]
            imgs = card.xpath(".//img/@src")
            if "image" in p:
                self.assertEqual(imgs, [p["image"]], slug)
                self.assertTrue(os.path.exists(os.path.join(ROOT, p["image"])), p["image"])

    def test_future_posts_are_gated(self):
        js = read("js/site.js")
        self.assertIn("data-pubdate", js)
        self.assertIn("post-scheduled", js)

    def test_zh_post_for_every_post(self):
        for p in posts():
            self.assertTrue(os.path.exists(os.path.join(ROOT, "zh", p)), p)


if __name__ == "__main__":
    unittest.main()
