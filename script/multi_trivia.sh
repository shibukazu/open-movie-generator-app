#!/bin/bash
set -e
# 自動的に複数個のトリビアショート動画を生成するスクリプト

SCRIPT_DIR="$(cd "$(dirname "$0")"; pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.."; pwd)"

json_file="${ROOT_DIR}/theme_manager.json"


themes=$(jq -r '.themes[:5][]' "$json_file") 

for theme in $themes; do
    echo "Processing theme: $theme"
    uv run src/cmd/main.py generate trivia $theme 
    jq --arg theme "$theme" 'del(.themes[] | select(. == $theme))' "$json_file" > tmp.json && mv tmp.json "$json_file"
done