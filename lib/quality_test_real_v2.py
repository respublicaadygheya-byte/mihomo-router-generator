#!/usr/bin/env python3

"""
Quality test v2
Использует существующий check_proxies_mihomo.py
"""

from pathlib import Path
import json
import time
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(BASE_DIR / "lib")
)

from check_proxies_mihomo import test_proxy


INPUT = BASE_DIR / "cache/filtered/quality_test_input.json"
OUTPUT = BASE_DIR / "cache/filtered/quality_test_real_v2.json"





def calculate_score(q):

    latency = q.get("latency_ms")

    if latency is None:
        return 0


    latency_score = max(
        0,
        70 - latency / 5
    )


    stable_score = 20


    speed = q.get(
        "speed_kbps",
        0
    )

    speed_score = min(
        10,
        speed / 100
    )


    return round(
        latency_score
        +
        stable_score
        +
        speed_score,
        2
    )



def main():

    print("="*60)
    print("REAL QUALITY TEST v2")
    print("="*60)


    with open(INPUT) as f:
        proxies=json.load(f)


    print(
        "INPUT:",
        len(proxies)
    )


    results=[]


    good=0


    for i,p in enumerate(proxies,1):

        name=p.get(
            "name",
            "unknown"
        )


        print(
            f"[{i}/{len(proxies)}]",
            name[:50],
            end=" "
        )


        result=test_proxy(
            p,
            timeout=15
        )


        quality={}


        quality["latency_ms"]=result.get(
            "latency_ms"
        )

        quality["available"]=result.get(
            "available",
            False
        )


        quality["speed_kbps"]=0


        quality["stable"]=(
            3
            if result.get("available")
            else 0
        )


        quality["country"]=None
            name
        )


        quality["score"]=calculate_score(
            quality
        )


        quality["ok"]=(
            quality["available"]
            and
            quality["latency_ms"]
            and
            quality["latency_ms"] < 400
            and
            quality["score"] >= 70
        )


        p["_quality"]=quality


        results.append(p)


        if quality["ok"]:
            good+=1
            print(
                "OK",
                quality["latency_ms"],
                quality["score"]
            )
        else:
            print(
                "FAIL"
            )


        time.sleep(0.2)



    with open(
        OUTPUT,
        "w"
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )


    print()
    print("="*60)
    print("DONE")
    print(
        "GOOD:",
        good
    )
    print(
        "BAD:",
        len(results)-good
    )
    print(
        "OUTPUT:",
        OUTPUT
    )



if __name__=="__main__":
    main()
