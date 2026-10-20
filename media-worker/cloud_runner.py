#!/usr/bin/env python3
"""Private FarmDay video analysis. Never infers copyright clearance or YPP approval."""
import json, os, sys, tempfile, subprocess, urllib.request, urllib.parse
from pathlib import Path
from analyze import sha256, visual_hashes, audio_fp, media_metadata
from similarity import ranked_matches
from youtube_candidates import search as search_youtube

BASE=os.environ.get("SUPABASE_URL","").rstrip("/")
KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
BUCKET="farmday-admin-review"
ENGINE="github-actions-ffmpeg-v2"
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

def main():
    if not BASE.startswith("https://") or not KEY:
        raise SystemExit("Configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY as GitHub Actions secrets")
    requested=os.environ.get("FARMDAY_UPLOAD_ID","").strip()
    # Atomic claim: concurrent runners cannot process the same video simultaneously.
    jobs=api("/rest/v1/rpc/farmday_claim_media_jobs","POST",{"p_limit":BATCH_SIZE})
    stats={"claimed":len(jobs),"analyzed":0,"failed":0,"incomplete":0}
    print("FARMDAY_QUEUE_CLAIMED",len(jobs),flush=True)
    for job in jobs:
        upload_id=job["upload_id"]
        session_id=job["session_id"]
        try:
            if requested and requested!=upload_id:
                api("/rest/v1/rpc/farmday_finish_media_job","POST",{"p_upload_id":upload_id,"p_success":False,"p_error":"Not requested by targeted run"})
                continue
            sessions=rows("farmday_youtube_upload_sessions",{"select":"id,user_id,state","id":"eq."+session_id,"limit":"1"})
            previews=rows("farmday_review_previews",{"select":"storage_path","session_id":"eq."+session_id,"limit":"1"})
            if not sessions or not previews or sessions[0]["state"]!="completed":
                raise RuntimeError("Completed session or registered private original missing")
            session=sessions[0]
            path=previews[0]["storage_path"]
            if not path.startswith(session["user_id"]+"/"+session_id+"/"):
                raise RuntimeError("Private original session ownership mismatch")
            existing=rows("farmday_media_analysis",{"select":"provider,video_analysis_status,audio_analysis_status","upload_id":"eq."+upload_id})
            if existing and existing[0].get("provider")==ENGINE and existing[0].get("video_analysis_status")=="analyzed" and existing[0].get("audio_analysis_status")=="analyzed":
                api("/rest/v1/rpc/farmday_finish_media_job","POST",{"p_upload_id":upload_id,"p_success":True})
                delete_staged_original(path)
                stats["analyzed"]+=1
                print("Already analyzed",upload_id,flush=True)
                continue
            print("Analyzing upload",upload_id,"attempt",job["attempts"],flush=True)
            signed=api("/storage/v1/object/sign/"+BUCKET+"/"+urllib.parse.quote(path,safe="/"),"POST",{"expiresIn":3600})
            signed_url=signed.get("signedURL") or signed.get("signedUrl")
            if not signed_url: raise RuntimeError("Missing signed download URL")
            url=(BASE+("/storage/v1"+signed_url if signed_url.startswith("/object/") else signed_url)) if signed_url.startswith("/") else signed_url
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
                audio=audio_fp(dest)
                others=rows("farmday_media_analysis",{"select":"upload_id,video_sha256,visual_fingerprint,audio_fingerprint","video_analysis_status":"eq.analyzed","limit":"500"})
                audio_raw=audio.get("fingerprint") if isinstance(audio.get("fingerprint"),list) else []
                matches=ranked_matches(frames,audio_raw,others,digest,upload_id)
                findings={
                    "similar_media":matches,
                    "technical_metadata":metadata,
                    "ranking_weights":{"visual":0.60,"audio":0.35,"exact_file":0.05,"title":0.0},
                    "audio_fingerprint_available":audio.get("status")=="analyzed",
                    "comparison_scope":"FarmDay previously analyzed videos only",
                    "youtube_search_scope":"YouTube title results are separate candidates, NOT fingerprint matches",
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
                if not frames or audio["status"]!="analyzed":
                    raise RuntimeError("Video/audio analysis incomplete: frames="+str(len(frames))+" audio="+audio["status"])
                api("/rest/v1/rpc/farmday_finish_media_job","POST",{"p_upload_id":upload_id,"p_success":True})
                try:
                    delete_staged_original(path)
                except Exception as cleanup_error:
                    print("WARNING: Temporary media cleanup failed:",str(cleanup_error)[:200],file=sys.stderr,flush=True)
                stats["analyzed"]+=1
                print("Analyzed",upload_id,"frames",len(frames),"audio samples",len(audio_raw),"matches",len(matches),flush=True)
        except Exception as error:
            stats["failed"]+=1
            print("Analysis failed",upload_id,str(error)[:300],file=sys.stderr,flush=True)
            try:
                update(upload_id,{"provider":ENGINE,"video_analysis_status":"failed","audio_analysis_status":"failed","copyright_analysis_status":"unverified","decision":"hold","decision_reason":"Technical media analysis failed; manual review required","findings":{"error_type":type(error).__name__,"error":str(error)[:250]}})
                api("/rest/v1/rpc/farmday_finish_media_job","POST",{"p_upload_id":upload_id,"p_success":False,"p_error":str(error)[:500]})
            except Exception as recording_error:
                print("Could not persist job failure",str(recording_error)[:300],file=sys.stderr,flush=True)
    # Independently search titles for completed uploads, including ones analyzed in earlier runs.
    # Never modifies YouTube visibility or safety-review approvals.
    try:
        uploads=rows("farmday_uploads",{"select":"id,title","order":"created_at.desc","limit":"30"})
        for item in uploads:
            upload_id=item["id"]
            old=rows("farmday_youtube_similarity_checks",{"select":"upload_id,engine_version","upload_id":"eq."+upload_id,"limit":"1"})
            if old and old[0].get("engine_version")=="youtube-title-ranked-v1": continue
            safety=rows("farmday_upload_safety",{"select":"youtube_video_id","upload_id":"eq."+upload_id,"limit":"1"})
            result=search_youtube(item.get("title") or "",safety[0].get("youtube_video_id") if safety else None)
            record={"upload_id":upload_id,"query_text":result.get("query_text") or item.get("title") or "",
                "state":result["state"],"candidates":result["candidates"],"candidate_count":len(result["candidates"]),
                "error_code":result.get("error_code"),"engine_version":"youtube-title-ranked-v1" if result["state"] not in ("not_configured","search_error") else "youtube-title-pending-v1",
                "checked_at":"now()"}
            record.pop("checked_at")
            api("/rest/v1/farmday_youtube_similarity_checks?on_conflict=upload_id","POST",record)
            print("YOUTUBE_TITLE_CANDIDATES",upload_id,result["state"],len(result["candidates"]),flush=True)
    except Exception as e:
        print("WARNING: YouTube candidate search:",str(e)[:300],file=sys.stderr,flush=True)
    print("FARMDAY_WORKER_SUMMARY",json.dumps(stats),flush=True)
    if stats["failed"]:raise SystemExit("Some media analyses failed; queued for retry where attempts remain")
if __name__=="__main__":main()
