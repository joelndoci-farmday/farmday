"""YouTube public metadata candidate search; never labels a title match as copyright proof."""
import os, re, json, urllib.request, urllib.parse, urllib.error, datetime
STOP={"the","and","for","with","from","video","official","a","an","of","in","on","at","to","my"}
def tokens(s):
    return set(w for w in re.findall(r"[^\W_]+",(s or "").casefold()) if len(w)>2 and w not in STOP)
def score(a,b):
    x,y=tokens(a),tokens(b)
    return round(len(x&y)/len(x|y),3) if x and y else 0.0
def request(endpoint,params,key):
    params={**params,"key":key}
    url="https://www.googleapis.com/youtube/v3/"+endpoint+"?"+urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url),timeout=25) as response:return json.load(response)
def seconds(duration):
    m=re.fullmatch(r"P(?:([0-9]+)D)?T?(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+)S)?",duration or "")
    if not m:return None
    d,h,mi,s=(int(x or 0) for x in m.groups());return d*86400+h*3600+mi*60+s
def search(title,own_id=None,description="",duration_seconds=None,spoken_phrases=None,visual_summary=""):
    key=os.environ.get("FARMDAY_YOUTUBE_API_KEY","").strip()
    if not key:return {"state":"not_configured","candidates":[],"error_code":"missing_youtube_api_key"}
    words=re.findall(r"[^\W_]+",description or "",flags=re.UNICODE)
    long_words=[w for w in words if len(w)>=5 and w.casefold() not in STOP]
    phrases=[title.strip()]
    # Search scene content independently of the uploader-controlled filename.
    scene_words=[w for w in re.findall(r"[^\\W_]+",visual_summary or "",flags=re.UNICODE) if len(w)>=5 and w.casefold() not in STOP]
    if len(scene_words)>=3:
        phrases.append(" ".join(scene_words[:7]))
    # Spoken phrases are independent of the uploader title and may reveal renamed copies.
    phrases.extend((p.strip()[:110] for p in (spoken_phrases or []) if len(p.strip()) >= 20))
    if len(long_words)>=4:
        phrases.extend([" ".join(long_words[:9])," ".join(long_words[-9:])])
    elif long_words:
        phrases.append(" ".join(long_words))
    phrases=list(dict.fromkeys(x.strip() for x in phrases if x.strip()))[:6]
    if not phrases:return {"state":"insufficient_metadata","candidates":[],"error_code":"no_search_terms"}
    found={}; errors=[]
    for phrase in phrases:
        try:
            data=request("search",{"part":"snippet","type":"video","maxResults":25,"q":phrase},key)
            for item in data.get("items",[]):
                vid=item.get("id",{}).get("videoId");sn=item.get("snippet") or {}
                if vid and vid!=own_id:found.setdefault(vid,{"video_id":vid,"title":sn.get("title", ""),"description":sn.get("description", ""),"channel":sn.get("channelTitle", ""),"published_at":sn.get("publishedAt"),"url":"https://www.youtube.com/watch?v="+vid})
        except urllib.error.HTTPError as e:errors.append("youtube_http_"+str(e.code))
        except (urllib.error.URLError,TimeoutError,ValueError) as e:errors.append(type(e).__name__)
    ids=list(found)
    for start in range(0,len(ids),50):
        try:
            data=request("videos",{"part":"contentDetails,status,statistics,snippet","id":",".join(ids[start:start+50])},key)
            for item in data.get("items",[]):
                c=found.get(item["id"])
                if not c:continue
                c["duration_seconds"]=seconds(item.get("contentDetails",{}).get("duration"))
                c["licensed_content"]=item.get("contentDetails",{}).get("licensedContent")
                c["view_count"]=int(item.get("statistics",{}).get("viewCount",0))
                c["description"]=item.get("snippet",{}).get("description",c["description"])
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError) as e:errors.append("details_"+type(e).__name__)
    candidates=[]
    for c in found.values():
        title_score=score(title,c["title"]);desc_score=score(description,c["description"]) if description else 0
        cd=c.get("duration_seconds")
        duration_score=round(max(0,1-abs(cd-duration_seconds)/max(cd,duration_seconds,1)),3) if cd is not None and duration_seconds else None
        spoken_score=max((score(phrase,c["title"]+" "+c["description"]) for phrase in (spoken_phrases or [])),default=0.0)
        visual_score=score(visual_summary,c["title"]+" "+c["description"]) if visual_summary else 0.0
        ranking=round(.30*title_score+.12*desc_score+.20*spoken_score+.13*visual_score+(.25*duration_score if duration_score is not None else 0),3)
        if title_score<.10 and desc_score<.12 and spoken_score<.10 and visual_score<.10:continue
        c.update({"title_similarity":title_score,"spoken_phrase_similarity":spoken_score,"description_similarity":desc_score,"visual_summary_similarity":visual_score,"duration_similarity":duration_score,"metadata_rank":ranking,"match_type":"youtube_metadata_candidate_unverified","duration_delta_seconds":round(abs(cd-duration_seconds),2) if cd is not None and duration_seconds is not None else None})
        candidates.append(c)
    candidates.sort(key=lambda x:x["metadata_rank"],reverse=True)
    return {"state":"search_partial" if errors else ("candidates_found_not_verified" if candidates else "no_metadata_candidates"),"candidates":candidates[:20],"error_code":",".join(sorted(set(errors))) or None,"query_text":" | ".join(phrases)}
