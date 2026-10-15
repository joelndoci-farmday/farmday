#!/usr/bin/env python3
"""Local/worker media fingerprint engine; requires ffmpeg/ffprobe, optional fpcalc.
No copyright clearance or monetization approval is inferred from similarity alone.
"""
import argparse, hashlib, json, shutil, subprocess, tempfile, os
from pathlib import Path
from datetime import datetime, timezone

def cmd(args):
    p=subprocess.run(args,check=True,capture_output=True,text=True)
    return p.stdout

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def visual_hashes(path):
    # Perceptual 8x8 grayscale frame hash, sampled once per 5 seconds.
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-i',str(path),'-vf','fps=1/5,scale=9:8,format=gray','-frames:v','360','-f','image2',str(Path(d)/'f%04d.pgm')],check=True)
        hashes=[]
        for f in sorted(Path(d).glob('*.pgm')):
            b=f.read_bytes(); start=0
            # Parse binary PGM header (P5), then 72 grayscale pixels.
            import re
            m=re.match(rb'P5\s+(?:#[^\n]*\n\s*)*9\s+8\s+255\s',b)
            if not m:continue
            pixels=b[m.end():m.end()+72]
            if len(pixels)!=72:continue
            bits=0
            for y in range(8):
                for x in range(8):bits=(bits<<1)|int(pixels[y*9+x]>pixels[y*9+x+1])
            hashes.append(f'{bits:016x}')
        return hashes

def audio_fp(path):
    if not shutil.which('fpcalc'):return {'status':'unavailable','reason':'Chromaprint fpcalc is not installed'}
    try:
        data=json.loads(cmd(['fpcalc','-raw','-json','-length','120',str(path)]))
        return {'status':'analyzed','fingerprint':data.get('fingerprint'),'duration':data.get('duration')}
    except Exception as e:return {'status':'failed','reason':str(e)[:200]}

def similarity(a,b):
    if not a or not b:return 0.0
    # Matching any sampled frames can flag possible shared footage; not proof.
    matches=sum(min((int(x,16)^int(y,16)).bit_count() for y in b)<=8 for x in a)
    return round(matches/len(a),3)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('video');ap.add_argument('--references',default='');ap.add_argument('--output',default='report.json');a=ap.parse_args()
    if not shutil.which('ffmpeg'):ap.error('ffmpeg must be installed')
    video=Path(a.video);frames=visual_hashes(video);audio=audio_fp(video)
    references=[]
    if a.references and Path(a.references).exists():
        for p in Path(a.references).glob('*.json'):
            try:
                r=json.loads(p.read_text());score=similarity(frames,r.get('visual',{}).get('frame_dhashes',[]))
                if score>0:references.append({'reference':p.name,'visual_sample_match_ratio':score})
            except (ValueError,OSError):pass
    references.sort(key=lambda x:x['visual_sample_match_ratio'],reverse=True)
    report={'engine_version':'0.1','analyzed_at':datetime.now(timezone.utc).isoformat(),'file_sha256':sha256(video),'visual':{'status':'analyzed' if frames else 'no_frames','frame_dhashes':frames,'sampling':'5s, up to 360 frames'},'audio':audio,'reference_matches':references[:20],'copyright':{'status':'unverified','reason':'Fingerprint similarity cannot establish ownership or licenses'},'monetization':{'status':'unverified','reason':'Requires rights evidence, reused-content policy and channel eligibility review'}}
    Path(a.output).write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('Wrote',a.output,'frames:',len(frames),'reference matches:',len(references))
if __name__=='__main__':main()
