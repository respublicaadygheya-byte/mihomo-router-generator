#!/usr/bin/env python3

import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "cache" / "filtered" / "quality_test_input.json"
OUTPUT_FILE = BASE_DIR / "cache" / "filtered" / "quality_test_real_v3.json"
TOP_FILE = BASE_DIR / "cache" / "filtered" / "top_quality_v3.json"


def latency_score(latency):
    if latency is None:
        return 0

    if latency < 100:
        return 70
    elif latency < 200:
        return 60
    elif latency < 300:
        return 45
    elif latency < 400:
        return 30
    else:
        return 0


def stable_score(stable):
    if stable == 3:
        return 20
    elif stable == 2:
        return 10
    return 0


def calculate_quality(check):
    available = check.get("available", False)
    latency = check.get("latency_ms")
    stable = 3 if available else 0

    score = 0

    if available:
        score += 10

    score += latency_score(latency)
    score += stable_score(stable)

    return {
        "available": available,
        "latency_ms": latency,
        "stable": stable,
        "score": score,
        "country": None,
        "speed_kbps": 0,
        "ok": (
            available
            and
            latency is not None
            and latency < 400
            and score >= 60
        )
    }


def main():

    with open(INPUT_FILE, encoding="utf-8") as f:
        proxies = json.load(f)

    results = []

    for proxy in proxies:

        check = proxy.get("_check", {})

        proxy["_quality"] = calculate_quality(check)

        results.append(proxy)


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )


    good = [
        p for p in results
        if p["_quality"]["ok"]
    ]

    top = sorted(
        good,
        key=lambda x:
        x["_quality"]["score"],
        reverse=True
    )


    with open(
        TOP_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            top[:100],
            f,
            indent=2,
            ensure_ascii=False
        )


    print("="*60)
    print("QUALITY TEST v3")
    print("="*60)

    print("TOTAL:", len(results))
    print("GOOD:", len(good))
    print("BAD:", len(results)-len(good))

    if good:

        scores=[
            x["_quality"]["score"]
            for x in good
        ]

        latency=[
            x["_quality"]["latency_ms"]
            for x in good
            if x["_quality"]["latency_ms"]
        ]

        print()
        print("AVG SCORE:",
              round(sum(scores)/len(scores),2))

        print(
            "AVG LATENCY:",
            round(sum(latency)/len(latency),2),
            "ms"
        )


    print()
    print("TOP FILE:")
    print(TOP_FILE)

    print()
    print("TOP 10:")
    
    for i,p in enumerate(top[:10],1):

        q=p["_quality"]

        print(
            i,
            "|",
            p.get("name","")[:50],
            "|",
            "score:",
            q["score"],
            "|",
            "lat:",
            q["latency_ms"]
        )


if __name__ == "__main__":
    main()
