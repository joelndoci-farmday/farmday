"""Find public YouTube candidates by title; never assert copyright infringement."""
import os, re, json, urllib.request, urllib.parse, urllib.error

STOP={"the","and","for","with","from","video","official","a","an","of","in","on","at","to","my"}
def tokens(s):
    return set(w for w in re.findall(r"[\w]+",(s or "").casefold()) if len(w)>2 and w not in STOP)
def score(a,b):
    x,y=tokens(a),tokens(b)
    return round(len(x&y)/len(x|y),3) if x and y else 0
def search(title,own_id=None):
    key=os.environ.get("FARMDAY_YOUTUBE_API_KEY","").strip()
    if not key: return {"state":"not_configured","candidates":[],"error_code":"missing_youtube_api_key"}
    query=" ".join(sorted(tokens(title))[:8]) or title
    params=urllib.parse.urlencode({"part":"snippet","type":"video","maxResults":25,"q":query,"key":key})
    req=urllib.request.Request("https://www.googleapis.com/youtube/v3/search?"+params)
    try:
        with urllib.request.urlopen(req,timeout=25) as resp: data=json.load(resp)
    except urllib.error.HTTPError as e:
        return {"state":"search_error","candidates":[],"error_code":"youtube_http_"+str(e.code)}
    except Exception:
        return {"state":"search_error","candidates":[],"error_code":"youtube_request_failed"}
    found=[]
    for item in data.get("items",[]):
        vid=item.get("id",{}).get("videoId")
        if not vid or vid==own_id: continue
        sn=item.get("snippet") or {}
        candidate_title=sn.get("title","")
        rank=score(title,candidate_title)
        if rank<0.15: continue
        found.append({"video_id":vid,"title":candidate_title,"channel":sn.get("channelTitle",""),"url":"https://www.youtube.com/watch?v="+vid,"title_similarity":rank,"match_type":"title_candidate_unverified"})
    found.sort(key=lambda x:x["title_similarity"],reverse=True)
    return {"state":"candidates_found_not_verified" if found else "no_title_candidates","candidates":found[:15],"error_code":None,"query_text":query}
