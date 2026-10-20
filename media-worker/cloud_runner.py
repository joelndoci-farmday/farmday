#!/usr/bin/env python3
"""Private FarmDay video analysis. Never infers copyright clearance or YPP approval."""
import json, os, sys, tempfile, subprocess, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from analyze import sha256, visual_hashes, audio_fp, media_metadata
from similarity import ranked_matches
from youtube_candidates import search as search_youtube
from intelligence import scenes, speech, search_phrases, review_priority

BASE=os.environ.get("SUPABASE_URL","").rstrip("/")
KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
BUCKET="farmday-admin-review"
ENGINE="farmday-cloud-intelligence-v3"
BATCH_SIZE=max(1,min(int(os.environ.get("FARMDAY_BATCH_SIZE","5")),20))
def api(path, method="GET", payload=None):
    url=BASE+path
    body=json.dumps(payload).encode() if payload is not None else None
    headers={"apikey":KEY,"Authorization":"Bearer "+KEY,"Accept":"application/json"}
    if body is not None: headers["Content-Type"]="application/json"
    if method=="POST" and (path.startswith("/rest/v1/farmday_media_analysis?") or path.startswith("/rest/v1/farmday_youtube_similarity_checks?")):
        headers["Prefer"]="return=representation,resolution=merge-duplicates"
    elif method in ("POST","PATCH"):
        headers["Prefer"]="return=representation"
    req=urllib.request.Request(url,data=body,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=90) as response:
            data=response.read()
    except urllib.error.HTTPError as error:
        detail=error.read(1000).decode('utf-8','replace')
        raise RuntimeError('Supabase '+method+' '+path.split('?')[0]+' returned HTTP '+str(error.code)+': '+detail[:500]) from error
    return json.loads(data) if data else None
def rows(table,params):
    return api("/rest/v1/"+table+"?"+urllib.parse.urlencode(params,safe=".,()*"))
def update(upload_id,record):
    return api("/rest/v1/farmday_media_analysis?on_conflict=upload_id","POST",{"upload_id":upload_id,**record})
def delete_staged_original(path):
    # Only the already-validated owner/session path may be removed.
    url=BASE+"/storage/v1/object/"+BUCKET+"/"+urllib.parse.quote(path,safe="/")
    req=urllib.request.Request(url,headers={"apikey":KEY,"Authorization":"Bearer "+KEY},method="DELETE")
    with urllib.request.urlopen(req,timeout=90) as response:
        response.read()
    print("Deleted temporary review original",flush=True)


def expire_overdue_jobs():
    """Persist overdue reviews. Never approve or publish a video automatically."""
    cutoff=datetime.now(timezone.utc)-timedelta(hours=1)
    uploads=rows("farmday_uploads",{"select":"id,created_at","created_at":"lt."+cutoff.isoformat(),"order":"created_at.desc","limit":"100"})
    for upload in uploads:
        uid=upload["id"]
        safety=rows("farmday_upload_safety",{"select":"screening_state","upload_id":"eq."+uid,"limit":"1"})
        if not safety or safety[0]["screening_state"] not in ("hold",):continue
        jobs=rows("farmday_media_jobs",{"select":"state","upload_id":"eq."+uid,"limit":"1"})
        if jobs and jobs[0]["state"]=="completed":continue
        api("/rest/v1/farmday_upload_safety?upload_id=eq."+uid,"PATCH",{"screening_state":"needs_evidence"})
        print("REVIEW_TIMEOUT_NEEDS_EVIDENCE",uid,flush=True)

def main():
    if not BASE.startswith("https://") or not KEY:
        raise SystemExit("Configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY locally (never in browser or ZIP)")
    # Atomic claim: concurrent runners cannot process the same video simultaneously.
    jobs=api("/rest/v1/rpc/farmday_claim_media_jobs","POST",{"p_limit":BATCH_SIZE})
    stats={"claimed":len(jobs),"analyzed":0,"failed":0,"incomplete":0}
    print("FARMDAY_QUEUE_CLAIMED",len(jobs),flush=True)
    if not jobs: expire_overdue_jobs()
    for job in jobs:
        upload_id=job["upload_id"]
        session_id=job["session_id"]
        try:
            sessions=rows("farmday_youtube_upload_sessions",{"select":"id,user_id,state","id":"eq."+session_id,"limit":"1"})
            previews=rows("farmday_review_previews",{"select":"storage_path","session_id":"eq."+session_id,"limit":"1"})
            if not sessions or not previews or sessions[0]["state"]!="completed":
                raise RuntimeError("Completed session or registered private original missing")
            session=sessions[0]
            path=previews[0]["storage_path"]
            if not path.startswith(session["user_id"]+"/"+session_id+"/"):
                raise RuntimeError("Private original session ownership mismatch")
            existing=rows("farmday_media_analysis",{"select":"provider,video_analysis_status,audio_analysis_status","upload_id":"eq."+upload_id})
            if existing and existing[0].get("provider")==ENGINE and existing[0].get("video_analysis_status")=="analyzed" and existing[0].get("audio_analysis_status") in ("analyzed","no_audio_stream"):
                api("/rest/v1/rpc/farmday_finish_media_job","POST",{"p_upload_id":upload_id,"p_success":True})
                stats["analyzed"]+=1
                print("Already analyzed",upload_id,flush=True)
                continue
            print("Analyzing upload",upload_id,"attempt",job["attempts"],flush=True)
            signed=api("/storage/v1/object/sign/"+BUCKET+"/"+urllib.parse.quote(path,safe="/"),"POST",{"expiresIn":3600})
            signed_url=signed.get("signedURL") or signed.get("signedUrl")
            if not signed_url: raise RuntimeError("Missing signed download URL")
            if signed_url.startswith("/object/"):
                url=BASE+"/storage/v1"+signed_url
            elif signed_url.startswith("/storage/v1/"):
                url=BASE+signed_url
            elif signed_url.startswith("https://"):
                url=signed_url
            else:
                raise RuntimeError("Unexpected signed download URL")
            with tempfile.TemporaryDirectory() as tmp:
                dest=Path(tmp)/"original-video"
                with urllib.request.urlopen(urllib.request.Request(url),timeout=180) as source,open(dest,"wb") as target:
                    size=0
                    while True:
                        block=source.read(1024*1024)
                        if not block:break
                        size+=len(block)
                        if size>1024*1024*1024:raise RuntimeError("File exceeds 1 GiB")
                        target.write(block)
                if not size:raise RuntimeError("Empty original file")
                metadata=media_metadata(dest)
                digest=sha256(dest)
                frames=visual_hashes(dest)
                audio=audio_fp(dest) if metadata.get("audio",{}).get("present") else {"status":"no_audio_stream","fingerprint":[]}
                others=rows("farmday_media_analysis",{"select":"upload_id,video_sha256,visual_fingerprint,audio_fingerprint","video_analysis_status":"eq.analyzed","limit":"500"})
                audio_raw=audio.get("fingerprint") if isinstance(audio.get("fingerprint"),list) else []
                matches=ranked_matches(frames,audio_raw,others,digest,upload_id)
                scene_data=scenes(dest)
                transcript=speech(dest)
                findings={
                    "similar_media":matches,
                    "scene_analysis":scene_data,
                    "speech_transcript":transcript,
                    "technical_metadata":metadata,
                    "ranking_weights":{"visual":0.60,"audio":0.35,"exact_file":0.05,"title":0.0},
                    "audio_fingerprint_available":audio.get("status")=="analyzed",
                    "comparison_scope":"Technical fingerprints of uploaded original; not compared to YouTube video bytes",
                    "youtube_search_scope":"YouTube public metadata candidates; NOT audiovisual matches",
                    "limitations":"No global Content ID access. Media matching is not copyright or monetization clearance."
                }
                record={
                    "provider":ENGINE,"video_sha256":digest,
                    "visual_fingerprint":json.dumps({"algorithm":"dhash-9x8-5sec-v1","frame_dhashes":frames}),
                    "audio_fingerprint":json.dumps(audio_raw),
                    "video_analysis_status":"analyzed" if frames else "no_frames",
                    "audio_analysis_status":audio["status"],
                    "duplicate_analysis_status":"possible_match" if matches else "no_match_in_local_library",
                    "copyright_analysis_status":"requires_rights_evidence",
                    "findings":findings,
                    "evidence":{"source":"private original upload","bytes":size,"engine":ENGINE},
                    "decision":"hold","decision_reason":"Human rights and YouTube monetization review required"
                }
                update(upload_id,record)
                if not frames or audio["status"] not in ("analyzed", "no_audio_stream"):
                    raise RuntimeError("Video/audio analysis incomplete: frames="+str(len(frames))+" audio="+audio["status"])
                # Search YouTube BEFORE marking the job complete. Search errors remain explicit.
                upload_rows=rows("farmday_uploads",{"select":"title,description","id":"eq."+upload_id,"limit":"1"})
                safety_rows=rows("farmday_upload_safety",{"select":"youtube_video_id","upload_id":"eq."+upload_id,"limit":"1"})
                u=upload_rows[0] if upload_rows else {}
                spoken=" ".join(search_phrases(transcript))
                yt=search_youtube(u.get("title") or "",safety_rows[0].get("youtube_video_id") if safety_rows else None,(u.get("description") or "")+" "+spoken,metadata.get("duration_seconds"))
                findings["review_priority"]=review_priority(matches,yt,transcript,scene_data)
                update(upload_id,{"findings":findings})
                api("/rest/v1/farmday_youtube_similarity_checks?on_conflict=upload_id","POST",{
                    "upload_id":upload_id,"query_text":yt.get("query_text") or u.get("title") or "",
                    "state":yt["state"],"candidates":yt["candidates"],"candidate_count":len(yt["candidates"]),
                    "error_code":yt.get("error_code"),"engine_version":"youtube-metadata-v2"})
                if yt["state"] in ("search_error","not_configured","search_partial"):
                    raise RuntimeError("YouTube candidate search incomplete: "+str(yt.get("error_code") or yt["state"]))
                api("/rest/v1/rpc/farmday_finish_media_job","POST",{"p_upload_id":upload_id,"p_success":True})
                # Temporary source stays private until an explicit, verified cleanup phase.
                # Do not remove it here: administrator preview/evidence may still need it.
                stats["analyzed"]+=1
                print("Analyzed",upload_id,"frames",len(frames),"audio samples",len(audio_raw),"matches",len(matches),flush=True)
        except Exception as error:
            stats["failed"]+=1
            print("Analysis failed",upload_id,str(error)[:300],file=sys.stderr,flush=True)
            try:
                previous=rows("farmday_media_analysis",{"select":"provider,video_analysis_status,audio_analysis_status","upload_id":"eq."+upload_id,"limit":"1"})
                if not previous or previous[0].get("video_analysis_status")!="analyzed":
                    update(upload_id,{"provider":ENGINE,"video_analysis_status":"failed","audio_analysis_status":"failed","copyright_analysis_status":"unverified","decision":"hold","decision_reason":"Technical media analysis failed; manual review required","findings":{"error_type":type(error).__name__,"error":str(error)[:250]}})
                else:
                    print("Preserving completed technical report after downstream failure",upload_id,flush=True)
                api("/rest/v1/rpc/farmday_finish_media_job","POST",{"p_upload_id":upload_id,"p_success":False,"p_error":str(error)[:500]})
            except Exception as recording_error:
                print("Could not persist job failure",str(recording_error)[:300],file=sys.stderr,flush=True)
    print("FARMDAY_WORKER_SUMMARY",json.dumps(stats),flush=True)
    if stats["failed"]:print("WARNING: Some jobs failed; retry policy is managed by Supabase queue",flush=True)
    return stats
if __name__=="__main__":main()
