#!/usr/bin/env python3
import re
import json
import sys
import base64
from urllib.parse import urlparse, parse_qs, unquote

def parse_vless(link):
    """Парсит VLESS ссылку"""
    if not link.startswith('vless://'):
        return None
    
    # Очищаем ссылку от мусора
    link = link.strip()
    
    # Разбиваем по #
    parts = link.split('#', 1)
    name = parts[1] if len(parts) > 1 else "Unknown"
    
    # Убираем vless://
    data = parts[0][8:]
    
    # Находим @
    at_pos = data.find('@')
    if at_pos == -1:
        return None
    
    uuid = data[:at_pos]
    rest = data[at_pos+1:]
    
    # Находим порт (после последнего :)
    colon_pos = rest.rfind(':')
    if colon_pos == -1:
        return None
    
    server = rest[:colon_pos]
    port_and_params = rest[colon_pos+1:]
    
    # Отделяем порт от параметров
    if '?' in port_and_params:
        port_str, params = port_and_params.split('?', 1)
    else:
        port_str, params = port_and_params, ''
    
    # Очищаем порт от слешей и мусора
    port_str = re.sub(r'[^0-9]', '', port_str)
    if not port_str:
        return None
    
    port = int(port_str)
    
    # Парсим параметры
    params_dict = {}
    if params:
        for param in params.split('&'):
            if '=' in param:
                k, v = param.split('=', 1)
                params_dict[k] = unquote(v)
    
    # Декодируем имя
    try:
        # Пробуем base64 decode
        name_decoded = base64.urlsafe_b64decode(name + '==').decode('utf-8')
    except:
        try:
            # Пробуем URL decode
            name_decoded = unquote(name)
        except:
            name_decoded = name
    
    # Формируем прокси
    proxy = {
        'name': name_decoded,
        'type': 'vless',
        'server': server,
        'port': port,
        'uuid': uuid,
        'network': params_dict.get('type', 'tcp'),
        'encryption': params_dict.get('encryption', 'none'),
        'flow': params_dict.get('flow', '')
    }
    
    # Добавляем tls если есть
    if params_dict.get('security') == 'tls':
        proxy['tls'] = True
        proxy['sni'] = params_dict.get('sni', server)
    
    # Добавляем WS настройки если нужно
    if params_dict.get('type') == 'ws':
        proxy['ws-opts'] = {
            'path': params_dict.get('path', '/'),
            'headers': {'Host': params_dict.get('host', server)}
        }
    
    return proxy

def main():
    if len(sys.argv) < 3:
        print("Usage: parser.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    proxies = []
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Ищем все vless:// ссылки
        vless_pattern = r'vless://[^\s<>"\'{}|\\^`\[\]]+'
        matches = re.findall(vless_pattern, content)
        
        for link in matches:
            proxy = parse_vless(link)
            if proxy:
                proxies.append(proxy)
                
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing: {e}")
        sys.exit(1)
    
    # Удаляем дубликаты
    seen = set()
    unique = []
    for p in proxies:
        key = (p['server'], p['port'], p['uuid'])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    print(f"Импортировано: {len(unique)} уникальных прокси")

if __name__ == '__main__':
    main()
