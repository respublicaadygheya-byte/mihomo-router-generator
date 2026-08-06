from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import json
import urllib.request
import yaml


BASE_DIR = Path(__file__).resolve().parent.parent
REMOTE_SOURCES_FILE = BASE_DIR / "sources" / "remote.yaml"
OUTPUT_FILE = BASE_DIR / "cache" / "imported" / "subscription_proxies.json"


def get_param(params, name, default=None):
    values = params.get(name)
    if not values:
        return default
    return values[0]


def parse_vless_url(url: str, role: str, subscription_name: str, index: int):
    parsed = urlparse(url.strip())

    if parsed.scheme.lower() != "vless":
        return None

    if not parsed.hostname or not parsed.username:
        return None

    params = parse_qs(parsed.query)

    server = parsed.hostname
    port = parsed.port or 443
    uuid = unquote(parsed.username)

    name = unquote(parsed.fragment) if parsed.fragment else f"{subscription_name} #{index}"

    security = get_param(params, "security", "none")
    network = get_param(params, "type", "tcp")

    # В некоторых VLESS-ссылках type=raw означает обычный TCP-транспорт.
    if network == "raw":
        network = "tcp"

    proxy = {
        "name": f"🌐 {name}",
        "type": "vless",
        "server": server,
        "port": port,
        "uuid": uuid,
        "network": network,
        "udp": True,
        "role": role,
        "_source": subscription_name,
    }

    if security in ("tls", "reality"):
        proxy["tls"] = True

    sni = get_param(params, "sni")

    if sni:
        proxy["servername"] = sni

    fingerprint = get_param(params, "fp")

    if fingerprint:
        proxy["client-fingerprint"] = fingerprint

    flow = get_param(params, "flow")

    if flow:
        proxy["flow"] = flow

    if security == "reality":
        public_key = get_param(params, "pbk")
        short_id = get_param(params, "sid")

        if public_key:
            proxy["reality-opts"] = {
                "public-key": public_key
            }

            if short_id:
                proxy["reality-opts"]["short-id"] = short_id

    if network == "ws":
        ws_opts = {}

        path = get_param(params, "path")

        if path:
            ws_opts["path"] = unquote(path)

        host = get_param(params, "host")

        if host:
            ws_opts["headers"] = {
                "Host": host
            }

        if ws_opts:
            proxy["ws-opts"] = ws_opts

    return proxy


def download_subscription(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Clash-Meta-Router/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def main():
    if not REMOTE_SOURCES_FILE.exists():
        print("REMOTE SOURCES FILE NOT FOUND")
        return

    with REMOTE_SOURCES_FILE.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    urls = config.get("urls", [])

    subscriptions = []

    for url in urls:
        subscriptions.append({
            "name": url.split("/")[-1],
            "url": url,
            "role": "",
            "enabled": True
        })

    all_proxies = []
    seen = set()
    duplicates = 0

    def proxy_key(proxy):
        return (
            proxy.get("server"),
            proxy.get("port"),
            proxy.get("uuid"),
            proxy.get("servername"),
            proxy.get("network"),
            proxy.get("flow"),
        )

    for subscription in subscriptions:
        if not subscription.get("enabled", True):
            continue

        name = subscription.get("name", "Subscription")
        url = subscription.get("url")
        role = subscription.get("role", "foreign")

        if not url:
            continue

        print(f"Загрузка подписки: {name}")

        try:
            content = download_subscription(url)
        except Exception as e:
            print(f"ОШИБКА ЗАГРУЗКИ: {e}")
            continue

        index = 0

        for line in content.splitlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if not line.lower().startswith("vless://"):
                continue

            index += 1

            try:
                proxy = parse_vless_url(
                    line,
                    role=role,
                    subscription_name=name,
                    index=index
                )

                if proxy:
                    key = proxy_key(proxy)

                    if key in seen:
                        duplicates += 1
                        continue

                    seen.add(key)
                    all_proxies.append(proxy)

            except Exception as e:
                print(f"ОШИБКА ПАРСИНГА #{index}: {e}")

        print(f"Импортировано VLESS: {index}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(all_proxies, f, ensure_ascii=False, indent=2)

    print()
    print(f"ИТОГО ИМПОРТИРОВАНО: {len(all_proxies)}")
    print(f"ДУБЛИКАТОВ УДАЛЕНО: {duplicates}")
    print(f"РЕЗУЛЬТАТ: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
