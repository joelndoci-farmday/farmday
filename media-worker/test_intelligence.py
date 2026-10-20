"""Offline, deterministic checks for FarmDay review intelligence."""
import unittest
from intelligence import search_phrases, review_priority

class IntelligenceTests(unittest.TestCase):
    def test_spoken_search(self):
        segments={"segments":[{"text":"This is a distinctive spoken sentence about a mountain farm and tractors."}]}
        self.assertEqual(len(search_phrases(segments)),1)
    def test_exact_duplicate_priority(self):
        p=review_priority([{"exact_file":True}],{"candidates":[]},{"status":"analyzed"},{"status":"analyzed"})
        self.assertEqual(p["level"],"high")
    def test_metadata_is_not_copyright_proof(self):
        p=review_priority([],{"candidates":[{"metadata_rank":0.9}]},{"status":"analyzed"},{"status":"analyzed"})
        self.assertEqual(p["basis"],"youtube_metadata_only")
    def test_no_signals_not_clearance(self):
        p=review_priority([],{"candidates":[]},{"status":"analyzed"},{"status":"analyzed"})
        self.assertIn("unverified",p["reason"])

if __name__=="__main__":unittest.main()
