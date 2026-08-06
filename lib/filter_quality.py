#!/usr/bin/env python3

from pathlib import Path
import json
import subprocess
import time


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "cache" / "filtered" / "available.json"
OUTPUT_FILE = BASE_DIR / "cache" / "filtered" / "top500.json"

LIMIT = 500

TEST_URLS = [
    "https://www.gstatic.com/generate_204",
    "https://www.cloudflare.com/cdn-cgi/trace",
]


def test_proxy(proxy):
    start = time.perf_counter()

    name = proxy.get("name", "unknown")

    # используем уже проверенную задержку Mihomo
    latency = (
        proxy.get("_check", {})
        .get("latency_ms", 99999)
    )

    if latency > 1000:
        return None

    return proxy


def main():

    with INPUT_FILE.open(
        encoding="utf-8"
    ) as f:
        proxies = json.load(f)


    print("INPUT:", len(proxies))


    good = []

    for i, proxy in enumerate(proxies, 1):

        result = test_proxy(proxy)

        if result:
            good.append(result)

        if i % 500 == 0:
            print(
                "processed:",
                i,
                "/",
                len(proxies)
            )


    good.sort(
        key=lambda x:
        x.get("_check", {})
        .get("latency_ms", 99999)
    )


    result = good[:LIMIT]


    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )


    print()
    print("QUALITY FILTER COMPLETE")
    print("-----------------------")
    print("INPUT:", len(proxies))
    print("OUTPUT:", len(result))
    print("FILE:", OUTPUT_FILE)


    print()
    print("TOP 10:")

    for p in result[:10]:
        print(
            p.get("_check", {})
            .get("latency_ms"),
            p.get("name")
        )


if __name__ == "__main__":
    main()
