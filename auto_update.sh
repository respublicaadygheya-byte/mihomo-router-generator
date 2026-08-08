#!/bin/bash

# Переходим в директорию генератора
cd /root/mihomo-router-generator || exit 1

# 1. Запуск твоей команды генерации/обновления (замени main.go или нужный флаг при необходимости)
go run main.go

# 2. Проверка изменений и отправка на GitHub
if [ -n "$(git status --porcelain)" ]; then
    git add .
    git commit -m "Auto-update config: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
fi
