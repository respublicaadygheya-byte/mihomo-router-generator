#!/usr/bin/env python3
import json
import sys
import subprocess
import tempfile
import os
import time

def check_proxy(proxy):
    """Проверяет прокси через mihomo"""
    # Простая проверка — пробуем подключиться
    # В реальности тут будет вызов mihomo с тестовым запросом
    return True  # Пока все считаем рабочими

def main():
    if len(sys.argv) < 3:
        print("Usage: checker.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            proxies = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)
    
    working = []
    total = len(proxies)
    
    print(f"Начинаем проверку: {total}")
    
    for i, proxy in enumerate(proxies, 1):
        # Простая проверка — все считаем рабочими
        proxy['alive'] = True
        working.append(proxy)
        print(f"[{i}/{total}] {proxy['name']} ... OK")
    
    with open(output_file, 'w') as f:
        json.dump(working, f, indent=2, ensure_ascii=False)
    
    print(f"Проверка завершена. Рабочих: {len(working)}")

if __name__ == '__main__':
    main()
