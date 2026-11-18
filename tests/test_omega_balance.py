import unittest
from pathlib import Path
from urllib.parse import urlparse
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
class OmegaBalance(unittest.TestCase):
 def test_page_and_local_assets(self):
  page=ROOT/'omega-balance/index.html'; doc=html.fromstring(page.read_text())
  for node in doc.xpath('//*[@src] | //link[@href]'):
   path=node.get('src') or node.get('href')
   if not urlparse(path).scheme: self.assertTrue((page.parent/path).exists(),path)
  for a in doc.xpath('//a[starts-with(@href,"#")]'):
   self.assertTrue(doc.xpath('//*[@id=$id]',id=a.get('href')[1:]))
  self.assertEqual(len(doc.xpath('//img')),6)
  self.assertIn('tel:+60195513038',doc.xpath('//a/@href'))
  self.assertIn('mailto:mikael@mikaelchew.com',doc.xpath('//a/@href'))
  self.assertNotIn('stripe',page.read_text().lower())
  self.assertEqual(doc.xpath('//link[@rel="canonical"]/@href'),['https://mikaelchew.com/omega-balance/'])
