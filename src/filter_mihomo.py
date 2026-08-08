#!/usr/bin/env python3

import os
import sys
import yaml
import tempfile
import subprocess


MIHOMO = "./bin/mihomo.bin"


def test_proxy(proxy):
    config = {
        "mixed-port": 7890,
        "proxies": [proxy],
        "proxy-groups": [{
            "name": "TEST",
            "type": "select",
            "proxies": [proxy["name"]],
        }],
    }

    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)

    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                config,
                f,
                allow_unicode=True,
                sort_keys=False,
            )

        result = subprocess.run(
            [MIHOMO, "-t", "-f", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        return result.returncode == 0, result.stderr.strip()

    finally:
        os.unlink(path)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} INPUT.yaml OUTPUT.yaml")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    proxies = config.get("proxies", [])

    valid = []
    rejected = []

    print(f"Проверяем {len(proxies)} прокси через Mihomo...")

    for i, proxy in enumerate(proxies, 1):
        ok, error = test_proxy(proxy)

        if ok:
            valid.append(proxy)
        else:
            rejected.append((proxy, error))
            print(
                f"REJECT [{i}/{len(proxies)}] "
                f"{proxy.get('name')} "
                f"{proxy.get('server')}"
            )

        if i % 100 == 0:
            print(f"  progress: {i}/{len(proxies)}")

    config["proxies"] = valid

    # Удаляем из proxy-groups ссылки на отброшенные proxy
    valid_names = {p["name"] for p in valid}

    for group in config.get("proxy-groups", []):
        if "proxies" in group:
            group["proxies"] = [
                name
                for name in group["proxies"]
                if name in valid_names
                or name in {"DIRECT", "REJECT", "FOREIGN", "PROXY"}
            ]

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            config,
            f,
            allow_unicode=True,
            sort_keys=False,
        )

    print()
    print("=== MIHOMO FILTER RESULT ===")
    print(f"Input:    {len(proxies)}")
    print(f"Valid:    {len(valid)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Output:   {output_file}")

    for proxy, error in rejected:
        first_error = next(
            (
                line.strip()
                for line in error.splitlines()
                if "error" in line.lower()
                or "invalid" in line.lower()
            ),
            "validation failed",
        )

        print(
            f"  - {proxy.get('name')} | "
            f"{proxy.get('server')} | {first_error}"
        )


if __name__ == "__main__":
    main()
