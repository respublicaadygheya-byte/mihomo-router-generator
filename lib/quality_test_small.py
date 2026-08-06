#!/usr/bin/env python3

import json
import time
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

INPUT = BASE / "cache/filtered/quality_test_input.json"
OUTPUT = BASE / "cache/filtered/quality_result.json"

TEST_URL = "https://www.cloudflare.com/cdn-cgi/trace"
SPEED_URL = "https://speed.cloudflare.com/__down?bytes=524288"


def test_proxy(p):

    result = {
        "name": p.get("name"),
        "latency_ms": p.get("_check", {}).get("latency_ms", 99999),
        "http": False,
        "speed_kbps": 0,
        "score": 0
    }

    try:
        # пока используем уже проверенные latency
        latency = result["latency_ms"]

        # через curl с оригинальным прокси пока не трогаем,
        # только готовим структуру

        if latency < 300:
            result["score"] = round(
                100 - latency / 10,
                2
            )

        return result

    except Exception:
        return result


def main():

    with open(INPUT) as f:
        proxies=json.load(f)

    print("INPUT:",len(proxies))

    results=[]

    for i,p in enumerate(proxies,1):

        r=test_proxy(p)
        results.append(r)

        print(
            f"[{i}/{len(proxies)}]",
            r["latency_ms"],
            r["score"],
            r["name"][:50]
        )


    results.sort(
        key=lambda x:x["score"],
        reverse=True
    )

    with open(OUTPUT,"w") as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("DONE")
    print("OUTPUT:",OUTPUT)


if __name__=="__main__":
    main()
