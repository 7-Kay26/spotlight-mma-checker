import unittest
from datetime import datetime, timezone
from checker import canonical, parse, select
class Tests(unittest.TestCase):
    def test_atom_rss(self):
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Fight confirmed</title><link href="https://example.com/a?utm_source=x"/><published>2026-11-26T10:00:00Z</published><summary>A &amp; B</summary></entry></feed>'
        item=list(parse(atom))[0]
        self.assertEqual(item['url'],'https://example.com/a')
        self.assertEqual(item['summary'],'A & B')
        rss=b'<rss><channel><item><title>UFC cancellation</title><link>https://example.com/b</link><pubDate>Thu, 26 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>'
        self.assertEqual(len(list(parse(rss))),1)
    def test_filter_and_duplicates(self):
        config={'mma_pattern':r'\bUFC\b','news_pattern':r'\bconfirmed\b'}
        seen={'urls':{},'titles':{}}
        base=dict(title='UFC fight confirmed',summary='',published='2026-11-26T10:00:00Z',url='https://example.com/a')
        entries=[base.copy(),dict(base,url='https://elsewhere.com/a'),dict(base,title='UFC old confirmed',published='2020-01-01T00:00:00Z'),dict(base,title='UFC future confirmed',published='2030-01-01T00:00:00Z'),dict(base,title='UFC undated confirmed',published=None),dict(base,title='Football confirmed')]
        now=datetime(2026,11,26,11,tzinfo=timezone.utc)
        result=select(entries,{'name':'test'},config,seen,now)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['status'],'needs_verification')
        self.assertEqual(select([base],{'name':'test'},config,seen,now),[])
    def test_urls(self):
        self.assertIsNone(canonical('javascript:alert(1)'))
        self.assertEqual(canonical('https://example.com/a?id=2&utm_medium=x#top'),'https://example.com/a?id=2')
if __name__=='__main__':
    unittest.main()
