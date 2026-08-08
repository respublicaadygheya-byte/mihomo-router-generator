#!/usr/bin/env python3
import json
import sys
import argparse
import yaml
from pathlib import Path


used_names = set()


def sanitize_name(name):
    import re
    import unicodedata

    name = str(name)

    # Сохраняем Unicode, включая флаги стран.
    # Убираем только управляющие символы и явно проблемные YAML/OpenClash
    # разделители. Не пытаемся фильтровать Unicode через ASCII regex.

    cleaned = []

    for ch in name:
        category = unicodedata.category(ch)

        # Управляющие и невидимые форматирующие символы.
        if category in {"Cc", "Cf"}:
            cleaned.append(" ")
            continue

        # Проблемные символы для имени прокси.
        if ch in "|,*()[]":
            cleaned.append(" ")
            continue

        cleaned.append(ch)

    name = "".join(cleaned)

    # Нормализуем whitespace.
    name = re.sub(r"\s+", " ", name).strip()

    # Убираем повторные дефисы.
    name = re.sub(r"-+", "-", name)

    # Убираем пробелы/дефисы по краям.
    name = name.strip(" -")

    # Ограничение длины.
    name = name[:60].strip(" -")

    return name


def unique_name(name):
    original = name
    counter = 2

    reserved = {
        'FOREIGN',
        'PROXY',
        'DIRECT'
    }

    if name in reserved:
        name = f"{name}-node"

    while name in used_names:
        name = f"{original}-{counter}"
        counter += 1

    used_names.add(name)
    return name



def load_list(filepath):
    """Загружает список доменов/IP из файла"""
    if not filepath or not Path(filepath).exists():
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]


def clean_proxy(proxy):
    """Удаляет только внутренние служебные поля."""
    proxy.pop("alive", None)
    proxy.pop("_id", None)
    return proxy


def generate_config(ru_proxies, foreign_proxies, ru_domains, ru_ips):
    """Генерация простой целевой Mihomo-схемы."""

    proxies = []
    foreign_names = []

    # ВСЕ VPN-ноды идут в FOREIGN.
    # RU/FOREIGN — только классификация на этапе splitter,
    # но в итоговом YAML все ноды являются VPN-нodes.
    all_proxies = list(ru_proxies) + list(foreign_proxies)

    for p in all_proxies:
        p = clean_proxy(p)

        original_name = p.get('name', 'PROXY')
        p['name'] = unique_name(sanitize_name(original_name))

        foreign_names.append(p['name'])
        proxies.append(p)

    # --------------------------------------------------------
    # DIRECT: только RU domains/IP.
    # --------------------------------------------------------

    rules = []

    for domain in ru_domains:
        domain = domain.strip().lower()

        if domain and not domain.startswith('#'):
            rules.append(
                f"DOMAIN-SUFFIX,{domain},DIRECT"
            )

    for ip in ru_ips:
        ip = ip.strip()

        if ip and not ip.startswith('#'):
            rules.append(
                f"IP-CIDR,{ip},DIRECT,no-resolve"
            )

    # Всё остальное -> PROXY
    rules.append("MATCH,PROXY")

    # --------------------------------------------------------
    # Целевая схема:
    #
    # PROXY
    #   ├── FOREIGN
    #   ├── node1
    #   ├── node2
    #   └── ...
    #
    # FOREIGN
    #   └── url-test -> все VPN-ноды
    # --------------------------------------------------------

    config = {
        'mixed-port': 7890,
        'allow-lan': True,
        'bind-address': '*',
        'mode': 'rule',
        'log-level': 'warning',
        'external-controller': '127.0.0.1:9090',

        'proxies': proxies,

        'proxy-groups': [
            {
                'name': 'PROXY',
                'type': 'select',
                'proxies': [
                    'FOREIGN'
                ] + foreign_names
            },
            {
                'name': 'FOREIGN',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'tolerance': 100,
                'proxies': foreign_names
            }
        ],

        'rules': rules
    }

    return config


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--ru',
        required=True,
        help='RU proxies JSON'
    )

    parser.add_argument(
        '--foreign',
        required=True,
        help='Foreign proxies JSON'
    )

    parser.add_argument(
        '--ru-direct',
        action='append',
        help='RU direct lists'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Output file'
    )

    args = parser.parse_args()


    try:
        with open(args.ru, 'r', encoding='utf-8') as f:
            ru_proxies = json.load(f)

    except FileNotFoundError:
        ru_proxies = []


    try:
        with open(args.foreign, 'r', encoding='utf-8') as f:
            foreign_proxies = json.load(f)

    except FileNotFoundError:
        foreign_proxies = []


    ru_domains = []
    ru_ips = []


    if args.ru_direct:

        for item in args.ru_direct:

            if ':' in item:

                typ, path = item.split(':', 1)

                if typ == 'domains':
                    ru_domains.extend(load_list(path))

                elif typ == 'ips':
                    ru_ips.extend(load_list(path))


    config = generate_config(
        ru_proxies,
        foreign_proxies,
        ru_domains,
        ru_ips
    )


    with open(args.output, 'w', encoding='utf-8') as f:

        yaml.dump(
            config,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )


    print(f"✅ Конфиг сгенерирован: {args.output}")
    print(f"   Российских прокси: {len(ru_proxies)}")
    print(f"   Иностранных прокси: {len(foreign_proxies)}")
    print(f"   DIRECT доменов: {len(ru_domains)}")
    print(f"   DIRECT IP: {len(ru_ips)}")


if __name__ == '__main__':
    main()
