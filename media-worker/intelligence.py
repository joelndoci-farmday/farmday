"""Evidence extraction for FarmDay. Signals are leads, never copyright proof."""
import json, os, re, subprocess

def scenes(path, limit=24):
    """Find scene-cut timestamps with ffmpeg; never downloads third-party videos."""
    command=["ffmpeg","-nostdin","-hide_banner","-i",str(path),"-vf","select=gt(scene\\,0.30),showinfo","-an","-f","null","-"]
    try:
        p=subprocess.run(command,capture_output=True,text=True,timeout=180)
        stamps=[]
        for match in re.finditer(r"pts_time:([0-9.]+)",p.stderr):
            t=round(float(match.group(1)),2)
            if not stamps or t-stamps[-1]>0.8: stamps.append(t)
            if len(stamps)>=limit:break
        return {"status":"analyzed" if p.returncode==0 else "partial","cut_timestamps_seconds":stamps,"sample_limit":limit}
    except (OSError,subprocess.TimeoutExpired,ValueError) as e:
        return {"status":"unavailable","reason":type(e).__name__}

def speech(path, limit=100):
    """Offline multilingual ASR. Keep model inference inside the trusted cloud runner."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return {"status":"unavailable","reason":"faster_whisper_not_installed","segments":[]}
    try:
        model=WhisperModel(os.environ.get("FARMDAY_WHISPER_MODEL","tiny"),device="cpu",compute_type="int8",cpu_threads=2)
        segments,info=model.transcribe(str(path),beam_size=1,vad_filter=True,condition_on_previous_text=False)
        out=[]
        for s in segments:
            t=" ".join(s.text.strip().split())
            if t:out.append({"start":round(s.start,2),"end":round(s.end,2),"text":t[:240]})
            if len(out)>=limit:break
        return {"status":"analyzed","language":info.language,"segments":out,"model":os.environ.get("FARMDAY_WHISPER_MODEL","tiny")}
    except Exception as e:
        return {"status":"unavailable","reason":type(e).__name__,"segments":[]}

def search_phrases(transcript, limit=2):
    """Extract distinctive spoken phrases; avoid searching short generic utterances."""
    phrases=[]
    for segment in transcript.get("segments",[]):
        t=segment.get("text","").strip()
        words=re.findall(r"[^\\W_]+",t,flags=re.UNICODE)
        if 5<=len(words)<=18 and len(t)>=30:
            phrases.append(t[:110])
        if len(phrases)>=limit:break
    return phrases

def review_priority(matches, youtube, transcript, scene_data):
    """Triage signal, not probability of infringement or authorization to publish."""
    if any(m.get("exact_file") for m in matches):
        return {"level":"high","reason":"Exact file duplicate in FarmDay library","basis":"file_sha256"}
    if any(m.get("visual_score",0)>=0.65 or m.get("audio_score",0)>=0.7 for m in matches):
        return {"level":"high","reason":"Strong internal audiovisual similarity","basis":"internal_fingerprints"}
    if any(c.get("metadata_rank",0)>=0.70 for c in youtube.get("candidates",[])):
        return {"level":"review","reason":"Strong YouTube metadata candidate; audiovisual content not compared","basis":"youtube_metadata_only"}
    if transcript.get("status")!="analyzed" or scene_data.get("status")=="unavailable":
        return {"level":"unknown","reason":"Some analysis signals unavailable; manual review required","basis":"incomplete_evidence"}
    return {"level":"normal","reason":"No strong signals in accessible comparison sources; copyright remains unverified","basis":"limited_screening"}
