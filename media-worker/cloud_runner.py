#!/usr/bin/env python3
"""Private FarmDay video analysis. Never infers copyright clearance or YPP approval."""
import json, os, sys, tempfile, subprocess, urllib.request, urllib.parse
from pathlib import Path
from analyze import sha256, visual_hashes, audio_fp, similarity

BASE=os.environ.get("SUPABASE_URL","").rstrip("/")
KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
BUCKET="farmday-admin-review"
ENGINE="github-actions-ffmpeg-v1"
def api(path, method="GET", payload=None):
    url=BASE+path
    body=json.dumps(payload).encode() if payload is not None else None
    headers={"apikey":KEY,"Authorization":"Bearer "+KEY,"Accept":"application/json"}
    if body is not None: headers["Content-Type"]="application/json"
    if method in ("POST","PATCH"): headers["Prefer"]="return=representation,resolution=merge-duplicates"
    req=urllib.request.Request(url,data=body,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=90) as response:
        data=response.read()
    return json.loads(data) if data else None
def rows(table,params):
    return api("/rest/v1/"+table+"?"+urllib.parse.urlencode(params,safe=".,()*"))
def update(upload_id,record):
    return api("/rest/v1/farmday_media_analysis?upload_id=eq."+upload_id,"POST",{"upload_id":upload_id,**record})
def main():
    if not BASE.startswith("https://") or not KEY:
        raise SystemExit("Configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY as GitHub Actions secrets")
    requested=os.environ.get("FARMDAY_UPLOAD_ID","").strip()
    sessions=rows("farmday_youtube_upload_sessions",{"select":"id,user_id,youtube_video_id,state","state":"eq.completed","order":"updated_at.desc","limit":"100"})
    completed=0
    for session in sessions:
        uploads=rows("farmday_uploads",{"select":"id,user_id","storage_path":"eq.youtube-private/"+session["youtube_video_id"]})
        if not uploads: continue
        upload=uploads[0]
        if requested and upload["id"]!=requested:continue
        previews=rows("farmday_review_previews",{"select":"storage_path","session_id":"eq."+session["id"],"user_id":"eq."+session["user_id"],"limit":"1"})
        if not previews: continue
        existing=rows("farmday_media_analysis",{"select":"provider,video_analysis_status","upload_id":"eq."+upload["id"]})
        if existing and existing[0].get("provider")==ENGINE and existing[0].get("video_analysis_status")=="analyzed" and not requested:continue
        path=previews[0]["storage_path"]
        if not path.startswith(session["user_id"]+"/"+session["id"]+"/"):continue
        print("Analyzing upload",upload["id"])
        try:
            signed=api("/storage/v1/object/sign/"+BUCKET+"/"+urllib.parse.quote(path,safe="/"),"POST",{"expiresIn":600})
            signed_url=signed.get("signedURL") or signed.get("signedUrl")
            if not signed_url:raise RuntimeError("Missing signed download URL")
            url=BASE+signed_url if signed_url.startswith("/") else signed_url
            with tempfile.TemporaryDirectory() as tmp:
                dest=Path(tmp)/"original-video"
                req=urllib.request.Request(url)
                with urllib.request.urlopen(req,timeout=120) as source,open(dest,"wb") as target:
                    size=0
                    while True:
                        block=source.read(1024*1024)
                        if not block:break
                        size+=len(block)
                        if size>1024*1024*1024:raise RuntimeError("File exceeds 1 GiB")
                        target.write(block)
                if not size:raise RuntimeError("Empty original file")
                digest=sha256(dest)
                frames=visual_hashes(dest)
                audio=audio_fp(dest)
                others=rows("farmday_media_analysis",{"select":"upload_id,video_sha256,visual_fingerprint","video_analysis_status":"eq.analyzed","limit":"500"})
                exact=[]; visual=[]
                for other in others:
                    if other["upload_id"]==upload["id"]:continue
                    if other.get("video_sha256")==digest:exact.append(other["upload_id"])
                    try:
                        stored=json.loads(other.get("visual_fingerprint") or "{}")
                        score=similarity(frames,stored.get("frame_dhashes",[]))
                        if score>=0.3:visual.append({"upload_id":other["upload_id"],"match_ratio":score})
                    except (ValueError,TypeError):pass
                visual.sort(key=lambda x:x["match_ratio"],reverse=True)
                findings={"exact_duplicate_upload_ids":exact[:20],"possible_visual_matches":visual[:20],"audio_fingerprint_available":audio.get("status")=="analyzed","comparison_scope":"FarmDay previously analyzed videos only","limitations":"No global Content ID access; fingerprints do not establish rights"}
                record={"provider":ENGINE,"video_sha256":digest,"visual_fingerprint":json.dumps({"algorithm":"dhash-9x8-5sec-v1","frame_dhashes":frames}),"audio_fingerprint":str(audio.get("fingerprint") or "")[:20000],"video_analysis_status":"analyzed" if frames else "no_frames","audio_analysis_status":audio["status"],"duplicate_analysis_status":"possible_match" if exact or visual else "no_match_in_local_library","copyright_analysis_status":"requires_rights_evidence","findings":findings,"evidence":{"source":"private original upload","bytes":size,"engine":ENGINE},"decision":"hold","decision_reason":"Human rights and monetization review required"}
                update(upload["id"],record)
                completed+=1
                print("Analyzed",upload["id"],"frames",len(frames),"exact matches",len(exact),"visual candidates",len(visual))
        except Exception as error:
            print("Analysis failed for",upload["id"],str(error)[:300],file=sys.stderr)
            update(upload["id"],{"provider":ENGINE,"video_analysis_status":"failed","copyright_analysis_status":"unverified","decision":"hold","decision_reason":"Technical media analysis failed; manual review required","findings":{"error_type":type(error).__name__}})
    print("Completed",completed,"video(s). Videos without private originals are not marked analyzed.")
if __name__=="__main__":main()
