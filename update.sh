#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "=============================="
echo "CLASH META ROUTER UPDATE"
echo "=============================="

echo "[1/3] Import sources"

python3 lib/import_sources.py


echo "[2/3] Check proxies"

python3 lib/check_proxies_mihomo.py


echo "[3/3] Generate config"

python3 lib/generate_config.py


echo "=============================="
echo "UPDATE COMPLETE"
echo "=============================="

ls -lh config/generated.yaml
