import unittest
from tests.helpers import en_pages, zh_pages, doc


class HarnessTest(unittest.TestCase):
    def test_every_en_page_parses(self):
        pages = en_pages()
        self.assertTrue(pages, "no EN pages found")
        for p in pages:
            self.assertEqual(doc(p).tag, "html", p)

    def test_page_sets_exclude_generated(self):
        self.assertNotIn("chapter-1.html", en_pages())
        self.assertTrue(zh_pages())
        self.assertTrue(all(p.startswith("zh/") for p in zh_pages()))
        self.assertFalse(any(p.startswith("redesign/") for p in en_pages()))


if __name__ == "__main__":
    unittest.main()
