#!/usr/bin/env python3
"""Run Farmday's existing Supabase atomic job queue from localhost."""
import os,sys,time,subprocess,shutil
from pathlib import Path
from cloud_runner import main

def start():
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        sys.exit("Missing local SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    if not os.getenv("FARMDAY_YOUTUBE_API_KEY"):
        sys.exit("Missing FARMDAY_YOUTUBE_API_KEY: cannot verify YouTube metadata candidates")
    for binary in ("ffmpeg","ffprobe","fpcalc"):
        if not shutil.which(binary):sys.exit("Missing dependency: "+binary)
    print("Farmday local worker started; poll interval 20s. Ctrl+C to stop.",flush=True)
    while True:
        try:main()
        except Exception as e:print("Worker iteration error:",str(e)[:250],file=sys.stderr,flush=True)
        time.sleep(20)
if __name__=="__main__":start()
