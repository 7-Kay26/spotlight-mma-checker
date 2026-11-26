from datetime import datetime, timezone
import unittest
from queue_reports import merge
class QueueTests(unittest.TestCase):
    def test_empty_poll_preserves_unprocessed_and_prunes_old(self):
        now=datetime(2026,11,26,tzinfo=timezone.utc)
        current={'url':'https://example.com/a','published':'2026-11-25T00:00:00+00:00'}
        old={'url':'https://example.com/b','published':'2026-01-01T00:00:00+00:00'}
        self.assertEqual(merge([current,old],[],now),[current])
        self.assertEqual(merge([current],[current],now),[current])
