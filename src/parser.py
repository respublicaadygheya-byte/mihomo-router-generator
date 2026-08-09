#!/usr/bin/env python3

import json
import re
import sys
from urllib.parse import unquote


def parse_query(query):
    params = {}

    for item in query.split("&"):
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        params[key] = unquote(value)

    return params


def parse_vless(link):
    link = link.strip()

    if not link.startswith("vless://"):
        return None

    try:
        body = link[len("vless://"):]

        if "#" in body:
            body, name = body.split("#", 1)
            name = unquote(name)
        else:
            name = "Unknown"

        if "?" not in body:
            return None

        user_host, query = body.split("?", 1)

        if "@" not in user_host:
            return None

        uuid, server_port = user_host.rsplit("@", 1)

        if ":" not in server_port:
            return None

        server, port = server_port.rsplit(":", 1)

        proxy = {
            "name": name,
            "type": "vless",
            "server": server,
            "port": int(port),
            "uuid": uuid,
        }

        params = parse_query(query)

        if "type" in params:
            proxy["network"] = params["type"]

        if "encryption" in params:
            proxy["encryption"] = params["encryption"]

        if "flow" in params:
            proxy["flow"] = params["flow"]

        security = params.get("security")

        if security == "reality":
            public_key = params.get("pbk")

            if not public_key:
                return None

            proxy["tls"] = True

            reality_opts = {
                "public-key": public_key,
            }

            if "sid" in params and params["sid"] != "":
                reality_opts["short-id"] = params["sid"]

            proxy["reality-opts"] = reality_opts

            if "sni" in params and params["sni"] != "":
                proxy["servername"] = params["sni"]

            if "fp" in params and params["fp"] != "":
                proxy["client-fingerprint"] = params["fp"]

        elif security == "tls":
            proxy["tls"] = True

            if "sni" in params and params["sni"] != "":
                proxy["servername"] = params["sni"]

            if "fp" in params and params["fp"] != "":
                proxy["client-fingerprint"] = params["fp"]

        if params.get("type") == "ws":
            ws_opts = {}

            if "path" in params:
                ws_opts["path"] = params["path"]

            if "host" in params:
                ws_opts["headers"] = {
                    "Host": params["host"]
                }

            if ws_opts:
                proxy["ws-opts"] = ws_opts

        return proxy

    except (ValueError, TypeError):
        return None



def parse_hysteria2(link):
    link = link.strip()

    if link.startswith("hysteria2://"):
        prefix = "hysteria2://"
    elif link.startswith("hy2://"):
        prefix = "hy2://"
    else:
        return None

    try:
        body = link[len(prefix):]

        if "#" in body:
            body, name = body.split("#", 1)
            name = unquote(name)
        else:
            name = "Unknown-Hy2"

        query = ""

        if "?" in body:
            body, query = body.split("?", 1)

        if "@" not in body:
            return None

        password, server_port = body.rsplit("@", 1)

        if ":" not in server_port:
            return None

        server, port = server_port.rsplit(":", 1)

        proxy = {
            "name": name,
            "type": "hysteria2",
            "server": server,
            "port": int(port),
            "password": unquote(password),
        }

        params = parse_query(query) if query else {}

        if params.get("sni"):
            proxy["sni"] = params["sni"]

        if params.get("insecure") in ("1", "true"):
            proxy["skip-cert-verify"] = True

        if params.get("obfs") and params["obfs"] != "none":
            proxy["obfs"] = params["obfs"]

        if params.get("obfs-password"):
            proxy["obfs-password"] = params["obfs-password"]

        return proxy

    except (ValueError, TypeError):
        return None


def main():
    if len(sys.argv) != 3:
        print("Usage: parser.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(
        input_file,
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        content = f.read()

    pattern = r'(?:vless|hysteria2|hy2)://[^\s<>"\'{}|\\`\[\]]+'
    links = re.findall(pattern, content)

    proxies = []

    for link in links:
        if link.startswith("vless://"):
            proxy = parse_vless(link)
        elif link.startswith(("hysteria2://", "hy2://")):
            proxy = parse_hysteria2(link)
        else:
            proxy = None

        if proxy:
            proxies.append(proxy)

    # Дубликат = полная конфигурация подключения,
    # а не только server/port/uuid.
    seen = set()
    unique = []

    for proxy in proxies:
        key = json.dumps(
            proxy,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(proxy)

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            unique,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Импортировано: {len(unique)} уникальных прокси")


if __name__ == "__main__":
    main()
