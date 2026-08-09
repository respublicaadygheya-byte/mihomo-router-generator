#!/bin/bash
set -e

export PATH=/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin

cd /root/mihomo-router-generator

echo "========================================"
echo "MIHOMO AUTO UPDATE"
echo "========================================"
echo "Started: $(date)"

./update.sh

echo
echo "Checking generated YAML..."

test -s publish/mihomo.yaml
test -s publish/openclash.yaml

echo "YAML files OK"

git add -f publish/mihomo.yaml publish/openclash.yaml

if git diff --cached --quiet; then
    echo "No changes to publish."
else
    git commit -m "Auto-update Mihomo configs: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
    echo "GitHub push completed."
fi

echo "Finished: $(date)"
echo "========================================"
