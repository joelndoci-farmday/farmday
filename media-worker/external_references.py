"""Opt-in external reference fingerprints. Never asserts ownership or Content ID matches."""
import json
from pathlib import Path
from similarity import visual_match, audio_match, audio_samples

REGISTRY=Path(__file__).with_name('reference_fingerprints.json')

def compare(frames, audio, registry=None):
    path=Path(registry) if registry is not None else REGISTRY
    if not path.is_file():return []
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,list):raise ValueError('Reference registry must be a JSON array')
    matches=[]
    for ref in data:
        if not isinstance(ref,dict) or not isinstance(ref.get('video_id'),str):continue
        visual=visual_match(frames,ref.get('frame_dhashes',[]))
        sound=audio_match(audio,audio_samples(ref.get('audio_fingerprint')))
        if visual>=0.70 or sound>=0.75:
            matches.append({'reference_video_id':ref['video_id'],
                            'reference_url':'https://www.youtube.com/watch?v='+ref['video_id'],
                            'visual_score':visual,'audio_score':sound,
                            'match_type':'user_supplied_reference_fingerprint',
                            'reference_provenance':ref.get('provenance','unverified'),
                            'copyright_status':'unverified'})
    return sorted(matches,key=lambda m:max(m['visual_score'],m['audio_score']),reverse=True)[:20]
