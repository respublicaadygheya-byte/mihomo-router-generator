#!/bin/bash

# Подгружаем системные пути, чтобы cron видел go и git
export PATH=$PATH:/usr/local/go/bin:/usr/bin:/bin

# Переходим в директорию
cd /root/mihomo-router-generator || exit 1

# Запускаем родной скрипт обновления
./update.sh

# Проверяем изменения и отправляем на GitHub
if [ -n "$(git status --porcelain)" ]; then
    git add .
    git commit -m "Auto-update config: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
fi
