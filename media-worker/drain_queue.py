#!/usr/bin/env python3
"""Run queued work in batches for one GitHub Actions job (no scheduled polling)."""
import os, time
from cloud_runner import main

def drain(run=main, clock=time.monotonic, sleep=time.sleep, budget=None):
    deadline=clock()+int(budget if budget is not None else os.getenv("FARMDAY_DRAIN_SECONDS","2400"))
    rounds=0
    while clock()<deadline:
        result=run()
        rounds+=1
        claimed=result.get("claimed",0)
        print("FARMDAY_DRAIN_ROUND",rounds,"claimed",claimed,flush=True)
        if not claimed:
            # A brief grace period catches uploads finishing during a running job.
            if rounds==1:
                sleep(8)
                result=run()
                if result.get("claimed",0):continue
            break
        if rounds>=500:break
    print("FARMDAY_DRAIN_FINISHED",rounds,flush=True)

if __name__=="__main__":drain()
