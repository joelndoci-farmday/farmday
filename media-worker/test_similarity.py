import unittest
from similarity import audio_match,visual_match,ranked_matches
import json

class SimilarityTests(unittest.TestCase):
    def test_identical_visual(self):
        x=['0000000000000000','ffffffffffffffff']
        self.assertEqual(visual_match(x,x),1.0)
    def test_identical_audio(self):
        a=[(i*2654435761)&0xffffffff for i in range(80)]
        self.assertEqual(audio_match(a,a),1.0)
    def test_shifted_audio(self):
        a=[(i*2654435761)&0xffffffff for i in range(80)]
        self.assertGreater(audio_match(a[10:],a),0.9)
    def test_title_has_no_weight(self):
        a=[(i*2654435761)&0xffffffff for i in range(80)]
        refs=[{'upload_id':'other','video_sha256':'not-equal','visual_fingerprint':json.dumps({'frame_dhashes':['ffffffffffffffff']}),'audio_fingerprint':json.dumps(a),'title':'completely different'}]
        found=ranked_matches(['0000000000000000'],a,refs,'hash','mine')
        self.assertEqual(found[0]['audio_score'],1.0)
        self.assertEqual(found[0]['title_weight'],0)

if __name__=='__main__':unittest.main()
