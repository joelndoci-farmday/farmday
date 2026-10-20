import unittest
from similarity import audio_match,visual_match,ranked_matches
import json
from unittest.mock import patch
from analyze import media_metadata

class SimilarityTests(unittest.TestCase):
    def test_metadata_probe(self):
        fixture={'format':{'format_name':'mov,mp4','duration':'12.50','bit_rate':'800000'},
                 'streams':[{'codec_type':'video','codec_name':'h264','width':1280,'height':720,'avg_frame_rate':'30000/1001'},
                            {'codec_type':'audio','codec_name':'aac','channels':2,'sample_rate':'48000'}]}
        with patch('analyze.cmd',return_value=json.dumps(fixture)):
            result=media_metadata('example.mp4')
        self.assertEqual(result['duration_seconds'],12.5)
        self.assertEqual(result['video']['fps'],29.97)
        self.assertEqual(result['audio']['sample_rate_hz'],48000)
    def test_video_without_audio(self):
        with patch('analyze.cmd',return_value=json.dumps({'format':{},'streams':[{'codec_type':'video','avg_frame_rate':'0/0'}]})):
            result=media_metadata('silent.mp4')
        self.assertFalse(result['audio']['present'])
        self.assertIsNone(result['video']['fps'])
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
