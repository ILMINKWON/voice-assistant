#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

# 마이크 볼륨 100% 고정
MIC=$(pactl list sources short | grep "sofhdadsp_6__source" | awk '{print $2}')
if [ -n "$MIC" ]; then
    pactl set-source-volume "$MIC" 100%
fi

"$DIR/venv/bin/python3" "$DIR/voice_assistant.py"
