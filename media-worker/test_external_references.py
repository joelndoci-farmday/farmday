import json, tempfile, unittest
from pathlib import Path
from external_references import compare
class ExternalReferenceTests(unittest.TestCase):
    def test_identical_content_with_different_title(self):
        frames=['0123456789abcdef']*30
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'references.json'
            p.write_text(json.dumps([{'video_id':'gJGvMB-lJY0','title':'completely different title','frame_dhashes':frames,'audio_fingerprint':[]}]))
            found=compare(frames,[],p)
            self.assertEqual(len(found),1)
            self.assertEqual(found[0]['visual_score'],1)
            self.assertEqual(found[0]['copyright_status'],'unverified')
    def test_no_false_match_on_unrelated_frames(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'references.json'
            p.write_text(json.dumps([{'video_id':'gJGvMB-lJY0','frame_dhashes':['0000000000000000']*20}]))
            self.assertEqual(compare(['ffffffffffffffff']*20,[],p),[])
if __name__=='__main__':unittest.main()
