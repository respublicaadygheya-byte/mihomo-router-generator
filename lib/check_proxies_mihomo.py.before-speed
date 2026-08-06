#!/usr/bin/env python3

from pathlib import Path
import argparse
import json
import subprocess
import tempfile
import time
import socket
import urllib.request
import urllib.error
import urllib.parse
import yaml


BASE_DIR = Path(__file__).resolve().parent.parent

MIHOMO = BASE_DIR / "bin" / "mihomo"
IMPORTED_FILE = BASE_DIR / "cache" / "imported" / "proxies.json"
FILTERED_DIR = BASE_DIR / "cache" / "filtered"
AVAILABLE_FILE = FILTERED_DIR / "available.json"
LOG_DIR = FILTERED_DIR / "logs"

TEST_URL = "https://www.gstatic.com/generate_204"

SUPPORTED_MIHOMO_TYPES = {
    "vless",
    "vmess",
    "trojan",
    "hysteria2",
    "tuic",
    "ss",
    "ssr",
    "socks5",
    "http",
    "https",
}


def wait_port(host, port, timeout):
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            with socket.create_connection(
                (host, port),
                timeout=0.5
            ):
                return True
        except OSError:
            time.sleep(0.2)

    return False


def prepare_proxy_for_mihomo(proxy):
    prepared = dict(proxy)

    if prepared.get("type") == "hysteria2":
        username = prepared.pop("username", None)
        password = prepared.get("password")

        if username and password:
            prepared["password"] = (
                f"{username}:{password}"
            )

    return prepared


def make_config(proxy, mixed_port, controller_port):
    prepared_proxy = prepare_proxy_for_mihomo(proxy)

    return {
        "mixed-port": mixed_port,
        "external-controller": (
            f"127.0.0.1:{controller_port}"
        ),
        "mode": "global",
        "log-level": "info",
        "ipv6": False,

        "proxies": [
            prepared_proxy
        ],

        "proxy-groups": [
            {
                "name": "TEST",
                "type": "select",
                "proxies": [proxy["name"]],
            }
        ],

        "rules": [
            "MATCH,GLOBAL"
        ],
    }


def test_proxy(proxy, timeout):
    proxy_name = proxy.get("name", "Unnamed")
    proxy_type = proxy.get("type", "").lower()

    if proxy_type not in SUPPORTED_MIHOMO_TYPES:
        return {
            "available": False,
            "status": "unsupported",
            "error": (
                f"Mihomo does not support proxy type: "
                f"{proxy_type}"
            ),
            "latency_ms": None,
        }

    with tempfile.TemporaryDirectory(
        prefix="clash-test-"
    ) as tmpdir:

        tmpdir = Path(tmpdir)

        mixed_port = 18000 + (
            int(time.time() * 1000) % 1000
        )

        controller_port = mixed_port + 1

        config_file = tmpdir / "config.yaml"
        log_file = LOG_DIR / (
            f"{proxy_name.replace('/', '_')}.log"
        )

        config = make_config(
            proxy,
            mixed_port,
            controller_port,
        )

        config_file.write_text(
            yaml.safe_dump(
                config,
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        test_result = subprocess.run(
            [
                str(MIHOMO),
                "-t",
                "-f",
                str(config_file),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if test_result.returncode != 0:
            output = (
                test_result.stdout
                + "\n"
                + test_result.stderr
            )

            log_file.write_text(
                output,
                encoding="utf-8",
            )

            return {
                "available": False,
                "status": "config_error",
                "error": output[-4000:],
                "latency_ms": None,
            }

        process = subprocess.Popen(
            [
                str(MIHOMO),
                "-f",
                str(config_file),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            if not wait_port(
                "127.0.0.1",
                mixed_port,
                timeout,
            ):
                return {
                    "available": False,
                    "status": "mihomo_start_timeout",
                    "error": (
                        "Mihomo mixed-port "
                        "did not start"
                    ),
                    "latency_ms": None,
                }

            proxy_url = (
                f"http://127.0.0.1:{mixed_port}"
            )

            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler(
                    {
                        "http": proxy_url,
                        "https": proxy_url,
                    }
                )
            )

            started = time.perf_counter()

            # 1. Healthcheck через Cloudflare 204
            check_res = subprocess.run(
                [
                    "curl",
                    "-4",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    str(timeout),
                    "--proxy",
                    proxy_url,
                    "--output",
                    "/dev/null",
                    "--write-out",
                    "%{http_code}",
                    "https://www.gstatic.com/generate_204",
                ],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )

            elapsed = round((time.perf_counter() - started) * 1000, 2)

            if check_res.returncode != 0:
                return {
                    "available": False,
                    "status": "curl_error",
                    "error": check_res.stderr.strip() or f"exit code {check_res.returncode}",
                    "latency_ms": None,
                    "exit_ip": None,
                }

            http_code = check_res.stdout.strip()
            if http_code not in ("200", "204"):
                return {
                    "available": False,
                    "status": "http_error",
                    "error": f"HTTP status {http_code}",
                    "latency_ms": None,
                    "exit_ip": None,
                }

                        # 2. Exit IP и Геолокация
            exit_ip = None
            country = None
            country_code = None
            try:
                # Пробуем ipinfo.io/json
                ip_res = subprocess.run(
                    [
                        "curl",
                        "-s",
                        "-4",
                        "-A", "Mozilla/5.0",
                        "--max-time", "5",
                        "--proxy", proxy_url,
                        "https://ipinfo.io/json",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                if ip_res.returncode == 0 and ip_res.stdout:
                    import json
                    data = json.loads(ip_res.stdout)
                    exit_ip = data.get("ip")
                    country_code = data.get("country")
                    country = country_code  # По умолчанию код страны

                # Если ipinfo не ответил — фоллбэк на ip-api.com
                if not exit_ip:
                    ip_res = subprocess.run(
                        [
                            "curl",
                            "-s",
                            "-4",
                            "-A", "Mozilla/5.0",
                            "--max-time", "5",
                            "--proxy", proxy_url,
                            "http://ip-api.com/json",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=8,
                    )
                    if ip_res.returncode == 0 and ip_res.stdout:
                        import json
                        data = json.loads(ip_res.stdout)
                        if data.get("status") == "success":
                            exit_ip = data.get("query")
                            country = data.get("country")
                            country_code = data.get("countryCode")
            except Exception as e:
                pass

            return {
                "available": True,
                "status": "ok",
                "error": None,
                "latency_ms": elapsed,
                "exit_ip": exit_ip,
                "country": country,
                "country_code": country_code,
            }

        except Exception as error:
            mihomo_output = ""

            try:
                if process.poll() is not None:
                    mihomo_output = (
                        process.stdout.read()
                        if process.stdout
                        else ""
                    )
            except Exception:
                pass

            error_text = str(error)

            if mihomo_output:
                error_text += (
                    "\\nMihomo output:\\n"
                    + mihomo_output[-4000:]
                )

            log_file.write_text(
                error_text,
                encoding="utf-8",
            )

            return {
                "available": False,
                "status": "connection_error",
                "error": error_text,
                "latency_ms": None,
            }

        finally:
            process.terminate()

            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
    )

    args = parser.parse_args()

    FILTERED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with IMPORTED_FILE.open(
        "r",
        encoding="utf-8",
    ) as f:
        proxies = json.load(f)

    if args.limit > 0:
        proxies = proxies[:args.limit]

    print(
        f"Начинаем проверку через Mihomo: "
        f"{len(proxies)}"
    )

    available = []

    for index, proxy in enumerate(
        proxies,
        start=1,
    ):
        name = proxy.get(
            "name",
            "Unnamed",
        )

        proxy_type = proxy.get(
            "type",
            "",
        ).lower()

        print(
            f"[{index}/{len(proxies)}] "
            f"{name} ... ",
            end="",
            flush=True,
        )

        if proxy_type not in SUPPORTED_MIHOMO_TYPES:
            print(
                f"SKIP: unsupported type "
                f"({proxy_type})"
            )

            continue

        started = time.perf_counter()

        result = test_proxy(
            proxy,
            args.timeout,
        )

        total_time = round(
            (
                time.perf_counter()
                - started
            ) * 1000,
            2,
        )

        result_data = dict(proxy)

        result_data["_check"] = {
            "name": name,
            "type": proxy_type,
            "server": proxy.get(
                "server"
            ),
            "port": proxy.get(
                "port"
            ),
            "available": result[
                "available"
            ],
            "status": result[
                "status"
            ],
            "latency_ms": result[
                "latency_ms"
            ],
            "error": result[
                "error"
            ],
            "total_time_ms": total_time,
            "exit_ip": result.get("exit_ip"),
            "country": result.get("country"),
            "country_code": result.get("country_code"),
        }

        if result.get("exit_ip"):
            result_data["exit_ip"] = result["exit_ip"]
            result_data["country"] = result.get("country")
            result_data["country_code"] = result.get("country_code")

        if result["available"]:
            print(
                f"OK "
                f"({result['latency_ms']} ms)"
            )

            available.append(
                result_data
            )

        else:
            print(
                f"FAIL: "
                f"{result['status']}"
            )

            if result.get("error"):
                print(
                    f"      ERROR: "
                    f"{result['error']}"
                )

    with AVAILABLE_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            available,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Проверка завершена")
    print("----------------------------")
    print(
        f"Всего:       {len(proxies)}"
    )
    print(
        f"Рабочих:     {len(available)}"
    )
    print(
        f"Результат:   {AVAILABLE_FILE}"
    )


if __name__ == "__main__":
    main()
