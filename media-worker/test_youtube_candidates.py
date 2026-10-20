import unittest
from unittest.mock import patch
from youtube_candidates import search, score, seconds

class YouTubeCandidatesTests(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(seconds("PT2M15S"), 135)
        self.assertEqual(seconds("PT1H"), 3600)
    def test_score(self):
        self.assertGreater(score("Albanian farming tractor", "Farming tractor in Albania"), 0)
    def test_missing_key(self):
        with patch.dict("os.environ", {"FARMDAY_YOUTUBE_API_KEY":""}):
            self.assertEqual(search("Farm video")["state"], "not_configured")
    def test_rank_and_own_video_excluded(self):
        def fake_request(endpoint, params, key):
            if endpoint=="search":
                return {"items":[
                    {"id":{"videoId":"OWN"},"snippet":{"title":"Farm tractor"}},
                    {"id":{"videoId":"OTHER"},"snippet":{"title":"Farm tractor","channelTitle":"A"}}
                ]}
            return {"items":[{"id":"OTHER","contentDetails":{"duration":"PT2M"},"statistics":{"viewCount":"12"}}]}
        with patch.dict("os.environ", {"FARMDAY_YOUTUBE_API_KEY":"test"}), patch("youtube_candidates.request",side_effect=fake_request):
            result=search("Farm tractor",own_id="OWN",duration_seconds=120)
        self.assertEqual(result["state"],"candidates_found_not_verified")
        self.assertEqual([x["video_id"] for x in result["candidates"]],["OTHER"])
        self.assertEqual(result["candidates"][0]["duration_similarity"],1)
