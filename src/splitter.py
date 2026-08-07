#!/usr/bin/env python3
import json
import sys
import re

# Российские домены и ключевые слова (расширенный список)
RU_KEYWORDS = [
    'russia', 'россия', 'ru', 'moscow', 'москва',
    'spb', 'санкт-петербург', 'ekb', 'екатеринбург',
    'russian', 'russland', 'rus', 'mosc', 'msk',
    'novosibirsk', 'новосибирск', 'kazan', 'казань',
    'nnov', 'нижний новгород', 'rostov', 'ростов',
    'samara', 'самара', 'ufa', 'уфа', 'krasnodar', 'краснодар'
]

def is_ru_proxy(proxy):
    name = proxy.get('name', '').lower()
    server = proxy.get('server', '').lower()
    
    for kw in RU_KEYWORDS:
        if kw in name:
            return True
    
    if server.endswith('.ru'):
        return True
    
    # Расширенная проверка IP (первые октеты российских сетей)
    ru_prefixes = ['5.255.', '5.45.', '31.13.', '37.9.', '37.140.', '46.0.', 
                   '62.0.', '77.0.', '80.64.', '85.0.', '87.0.', '88.0.', 
                   '89.0.', '91.0.', '92.0.', '93.0.', '94.0.', '95.0.',
                   '128.0.', '129.0.', '130.0.', '131.0.', '132.0.', '133.0.']
    
    for prefix in ru_prefixes:
        if server.startswith(prefix):
            return True
    
    return False

def main():
    if len(sys.argv) < 4:
        print("Usage: splitter.py <input_file> <ru_output> <foreign_output>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    ru_output = sys.argv[2]
    foreign_output = sys.argv[3]
    
    try:
        with open(input_file, 'r') as f:
            proxies = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)
    
    ru = []
    foreign = []
    
    for proxy in proxies:
        if is_ru_proxy(proxy):
            ru.append(proxy)
        else:
            foreign.append(proxy)
    
    with open(ru_output, 'w') as f:
        json.dump(ru, f, indent=2, ensure_ascii=False)
    
    with open(foreign_output, 'w') as f:
        json.dump(foreign, f, indent=2, ensure_ascii=False)
    
    print(f"Разделено: RU={len(ru)}, FOREIGN={len(foreign)}")

if __name__ == '__main__':
    main()
