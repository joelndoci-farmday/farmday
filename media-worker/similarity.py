"""Conservative A/V similarity signals within the FarmDay analyzed-video library.

Frame dHash is tolerant of modest image changes. Chromaprint raw samples are
compared with offset alignment, allowing music/audio appearing later in a clip.
Scores are screening hints, not copyright findings.
"""
import json

def visual_match(a,b):
    if not a or not b:return 0.0
    reference=[int(x,16) for x in b[:360] if isinstance(x,str) and len(x)==16]
    if not reference:return 0.0
    matched=0
    for x in a[:360]:
        try:
            v=int(x,16)
            if min((v^y).bit_count() for y in reference)<=8:matched+=1
        except (TypeError,ValueError):continue
    return round(matched/min(len(a),360),3)

def audio_match(a,b):
    """Find 20+ consecutive, aligned Chromaprint raw samples.

    Chromaprint samples are ~0.1238s apart; 20 samples are ~2.5 seconds.
    Allow modest noise; require multiple good frames to reduce false positives.
    """
    if not isinstance(a,list) or not isinstance(b,list) or len(a)<20 or len(b)<20:return 0.0
    a=[int(v)&0xffffffff for v in a[:900]]
    b=[int(v)&0xffffffff for v in b[:900]]
    best=0.0
    # Compare alignment offsets, including clips with a leading intro/outro.
    for shift in range(-min(len(b)-20,250),min(len(a)-20,250)+1,2):
        ia=max(0,shift);ib=max(0,-shift)
        n=min(len(a)-ia,len(b)-ib)
        if n<20:continue
        good=sum((a[ia+i]^b[ib+i]).bit_count()<=10 for i in range(n))
        score=good/n
        if score>best:best=score
    return round(best,3)

def audio_samples(value):
    if not value:return []
    try:
        raw=json.loads(value) if isinstance(value,str) else value
        return raw if isinstance(raw,list) else []
    except (TypeError,ValueError):return []

def ranked_matches(frames,audio,other_rows,digest,own_id):
    results=[]
    for other in other_rows:
        if other.get('upload_id')==own_id:continue
        exact=bool(digest and other.get('video_sha256')==digest)
        try:
            stored=json.loads(other.get('visual_fingerprint') or '{}')
            visual=visual_match(frames,stored.get('frame_dhashes',[]))
        except (ValueError,TypeError):visual=0.0
        sound=audio_match(audio,audio_samples(other.get('audio_fingerprint')))
        # Visual 60%, audio 35%, exact file 5%; title has NO effect.
        score=round(0.60*visual+0.35*sound+0.05*int(exact),3)
        if exact or visual>=0.30 or sound>=0.35:
            results.append({'upload_id':other['upload_id'],'visual_score':visual,
                            'audio_score':sound,'exact_file':exact,'combined_score':score,
                            'title_weight':0})
    return sorted(results,key=lambda x:(x['exact_file'],x['combined_score']),reverse=True)[:20]
