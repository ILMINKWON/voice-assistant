#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

# 이미 실행 중이면 종료
if pgrep -f "voice_assistant.py" > /dev/null; then
    echo "이미 실행 중입니다."
    exit 0
fi

# 마이크 볼륨 100% 고정
MIC=$(pactl list sources short | grep "sofhdadsp_6__source" | awk '{print $2}')
if [ -n "$MIC" ]; then
    pactl set-source-volume "$MIC" 100%
fi

"$DIR/venv/bin/python3" "$DIR/voice_assistant.py"
