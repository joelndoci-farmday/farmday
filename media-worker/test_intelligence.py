"""Offline, deterministic checks for FarmDay review intelligence."""
import unittest
from intelligence import search_phrases, review_priority, ten_frame_evidence, music_activity

class IntelligenceTests(unittest.TestCase):
    def test_ten_frame_positions(self):
        evidence=ten_frame_evidence("unused.mp4",100)
        self.assertEqual(evidence["count"],10)
        self.assertEqual(evidence["timestamps"],[5,15,25,35,45,55,65,75,85,95])
    def test_ten_frame_missing_duration(self):
        self.assertEqual(ten_frame_evidence("unused.mp4",0)["status"],"unavailable")
    def test_music_signal_does_not_claim_rights(self):
        from unittest.mock import patch
        with patch("intelligence.subprocess.run") as runner:
            runner.return_value.returncode=0
            runner.return_value.stderr="silence_start: 1.2"
            evidence=music_activity("unused.mp4")
        self.assertFalse(evidence["rights_verified"])
        self.assertEqual(evidence["silence_events"],1)
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
