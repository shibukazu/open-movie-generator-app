#!/bin/bash

# 掲示板の内容に基づいた動画を自動的に複数個生成するスクリプト

SCRIPT_DIR="$(cd "$(dirname "$0")"; pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.."; pwd)"

json_file="${ROOT_DIR}/source_manager.json"


urls=$(jq -r '.urls[:5][]' "$json_file") 

for url in $urls; do
    echo "Processing URL: $url"
    uv run src/cmd/main.py generate bulletin $url --movie-generator-type=irasutoya_short --thumbnail-generator-type=bulletin_board_short   
    jq --arg url "$url" 'del(.urls[] | select(. == $url))' "$json_file" > tmp.json && mv tmp.json "$json_file"
done