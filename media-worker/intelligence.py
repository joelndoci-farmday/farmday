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
        words=re.findall(r"[^\W_]+",t,flags=re.UNICODE)
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

def ten_frame_evidence(path, duration_seconds=None):
    """Select ten spread-out frame positions. This is sampling, not AI recognition."""
    try:
        duration=float(duration_seconds or 0)
        if duration<=0:
            return {"status":"unavailable","reason":"unknown_duration","timestamps":[]}
        stamps=[round(duration*(i+0.5)/10,2) for i in range(10)]
        return {"status":"sampled","timestamps":stamps,"count":len(stamps),"interpretation":"Frames are sampled for visual fingerprints; no external video content recognition is implied"}
    except (TypeError,ValueError,OverflowError):
        return {"status":"unavailable","reason":"invalid_duration","timestamps":[]}

def music_activity(path):
    """Measure audio activity only; do not mislabel speech as licensed music."""
    try:
        result=subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","info","-i",str(path),"-vn","-af","silencedetect=noise=-35dB:d=1","-f","null","-"],capture_output=True,text=True,timeout=180)
        if result.returncode:
            return {"status":"unavailable","reason":"audio_decode_failed","rights_verified":False}
        return {"status":"analyzed","silence_events":len(re.findall(r"silence_start:",result.stderr)),"song_identification":"not_available_without_reference_catalog","rights_verified":False}
    except (OSError,subprocess.TimeoutExpired):
        return {"status":"unavailable","reason":"audio_processing_failed","rights_verified":False}

def vision_frame_urls(path, duration_seconds, count=3):
    """Create low-resolution data URLs for optional vision review; never persist images."""
    import base64
    try:
        duration=float(duration_seconds or 0)
        if duration<=0:return []
        frames=[]
        for i in range(min(3,max(0,int(count)))):
            at=duration*(i+0.5)/3
            p=subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-ss",str(at),"-i",str(path),"-frames:v","1","-vf","scale=320:-2","-q:v","8","-f","image2pipe","-vcodec","mjpeg","-"],capture_output=True,timeout=40)
            if p.returncode==0 and 0<len(p.stdout)<120000:
                frames.append("data:image/jpeg;base64,"+base64.b64encode(p.stdout).decode("ascii"))
        return frames
    except (OSError,ValueError,TypeError,subprocess.TimeoutExpired):
        return []

def optional_openai_vision(path, duration_seconds):
    """Off unless explicitly configured. Limit image count and output tokens."""
    import urllib.request, urllib.error
    key=os.environ.get("OPENAI_API_KEY","").strip()
    if not key or os.environ.get("FARMDAY_OPENAI_VISION_ENABLED","0")!="1":
        return {"status":"disabled","estimated_cost_usd":0,"usage":None}
    frames=vision_frame_urls(path,duration_seconds,3)
    if not frames:return {"status":"unavailable","reason":"no_frames"}
    model=os.environ.get("FARMDAY_OPENAI_VISION_MODEL","gpt-4.1-mini")
    content=[{"type":"input_text","text":"Describe the scenes, visible watermarks, logos, credits and likely stock footage clues. Do not determine copyright ownership. Return a concise factual description."}]
    content.extend({"type":"input_image","image_url":url,"detail":"low"} for url in frames)
    payload={"model":model,"input":[{"role":"user","content":content}],"max_output_tokens":160}
    req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=65) as response:data=json.load(response)
        usage=data.get("usage") or {}
        return {"status":"analyzed","model":model,"response_id":data.get("id"),"usage":usage,"summary":" ".join(x.get("text","") for o in data.get("output",[]) for x in o.get("content",[]) if x.get("type")=="output_text")[:1400],"cost_status":"requires_current_model_rate"}
    except (urllib.error.URLError,TimeoutError,ValueError) as error:
        return {"status":"failed","reason":type(error).__name__}
