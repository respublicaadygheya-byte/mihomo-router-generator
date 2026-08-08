#!/bin/bash
set -e

echo "=============================="
echo "CLASH META ROUTER GENERATOR"
echo "=============================="

# ============================================
# ШАГ 1: Импорт источников
# ============================================
echo "[1/4] Import sources"

# Очищаем старый кеш
rm -rf cache/imported/*
rm -rf cache/filtered/*

# Скачиваем источники
SOURCES=(
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
    "https://raw.githubusercontent.com/aviamastersgh/vpn-free-russia/main/verified_configs.txt"
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-all.txt"
    "https://github.com/AvenCores/goida-vpn-configs/raw/refs/heads/main/githubmirror/26.txt"
)

# Собираем все прокси в один файл
> cache/imported/raw_proxies.txt
for url in "${SOURCES[@]}"; do
    echo "  Download: $url"
    curl -sL "$url" >> cache/imported/raw_proxies.txt 2>/dev/null || echo "  FAILED: $url"
    echo "" >> cache/imported/raw_proxies.txt
done

# Парсим VLESS ссылки
python3 src/parser.py cache/imported/raw_proxies.txt cache/imported/proxies.json

COUNT=$(jq '. | length' cache/imported/proxies.json 2>/dev/null || echo "0")
echo "  Прокси импортировано: $COUNT"

# ============================================
# ШАГ 2: Проверка прокси
# ============================================
echo "[2/4] Check proxies"

# Запускаем проверку через Mihomo
python3 src/checker.py cache/imported/proxies.json cache/filtered/available.json

AVAIL=$(jq '. | length' cache/filtered/available.json 2>/dev/null || echo "0")
echo "  Рабочих прокси: $AVAIL"

# ============================================
# ШАГ 3: Разделение на категории
# ============================================
echo "[3/4] Split by categories"

# Разделяем на российские и иностранные
python3 src/splitter.py cache/filtered/available.json cache/filtered/ru.json cache/filtered/foreign.json

RU_COUNT=$(jq '. | length' cache/filtered/ru.json 2>/dev/null || echo "0")
FOREIGN_COUNT=$(jq '. | length' cache/filtered/foreign.json 2>/dev/null || echo "0")
echo "  Российских: $RU_COUNT"
echo "  Иностранных: $FOREIGN_COUNT"

# ============================================
# ШАГ 4: Генерация конфига
# ============================================
echo "[4/4] Generate config"

python3 src/generator.py \
    --ru cache/filtered/ru.json \
    --foreign cache/filtered/foreign.json \
    --ru-direct domains:lists/ru_direct_domains.txt \
    --ru-direct ips:lists/ru_direct_ips.txt \
    --output publish/mihomo.yaml

# ============================================
# ШАГ 5: Финальная валидация через Mihomo
# ============================================
echo "[5/5] Validate generated config with Mihomo"

python3 src/filter_mihomo.py \
    publish/mihomo.yaml \
    publish/mihomo-filtered.yaml

# Финальный конфиг после отбрасывания
# прокси, которые Mihomo не принимает.
mv publish/mihomo-filtered.yaml publish/mihomo.yaml

# Копируем для OpenClash
cp publish/mihomo.yaml publish/openclash.yaml

echo "=============================="
echo "UPDATE COMPLETE"
echo "=============================="
ls -lh publish/
