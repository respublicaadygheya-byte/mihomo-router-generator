#!/usr/bin/env python3
import json
import sys
import argparse
import yaml
from pathlib import Path


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
    """Очищает прокси от мусора и нормализует поля"""

    proxy.pop('alive', None)
    proxy.pop('_id', None)

    network = proxy.get('network', 'tcp')

    if network in ['xhttp', 'http', 'raw']:
        network = 'tcp'

    proxy['network'] = network

    if 'flow' in proxy and not proxy['flow']:
        del proxy['flow']

    if 'ws-opts' in proxy:
        ws_opts = proxy['ws-opts']

        if isinstance(ws_opts, dict):
            if not (
                'headers' in ws_opts
                and isinstance(ws_opts['headers'], dict)
            ):
                ws_opts['headers'] = {
                    'Host': ws_opts.get(
                        'host',
                        proxy.get('server', '')
                    )
                }

    return proxy


def generate_config(ru_proxies, foreign_proxies, ru_domains, ru_ips):
    """Генерация Mihomo конфига"""

    proxies = []

    #
    # Российские прокси сохраняем,
    # но НЕ используем как DIRECT.
    #
    for p in ru_proxies:
        p = clean_proxy(p)
        p['name'] = f"RU-{p['name']}"
        proxies.append(p)

    #
    # Иностранные прокси идут в FOREIGN
    #
    foreign_names = []

    for p in foreign_proxies:
        p = clean_proxy(p)
        p['name'] = f"FOREIGN-{p['name']}"
        foreign_names.append(p['name'])
        proxies.append(p)

    rules = []

    #
    # Российские домены -> настоящий DIRECT
    #
    for domain in ru_domains:
        domain = domain.strip().lower()

        if domain and not domain.startswith('#'):
            rules.append(
                f"DOMAIN-SUFFIX,{domain},DIRECT"
            )

    #
    # Российские IP -> настоящий DIRECT
    #
    for ip in ru_ips:
        ip = ip.strip()

        if ip and not ip.startswith('#'):
            rules.append(
                f"IP-CIDR,{ip},DIRECT,no-resolve"
            )

    #
    # Остальное через PROXY
    #
    rules.append("MATCH,🚀 PROXY")


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
                'name': '🌐 FOREIGN',
                'type': 'select',
                'proxies': foreign_names + ['DIRECT']
            },

            {
                'name': '🚀 PROXY',
                'type': 'select',
                'proxies': [
                    '🌐 FOREIGN',
                    'DIRECT'
                ]
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
