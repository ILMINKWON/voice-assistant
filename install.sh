#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================="
echo "  음성 어시스턴트 패키지 설치"
echo "============================="

# 시스템 패키지
sudo apt-get install -y portaudio19-dev libsndfile1 python3-venv ffmpeg

# 가상환경 생성
echo "가상환경 생성 중..."
python3 -m venv "$DIR/venv"

# 패키지 설치
echo "Python 패키지 설치 중... (시간이 걸릴 수 있습니다)"
"$DIR/venv/bin/pip" install --upgrade pip
"$DIR/venv/bin/pip" install openai-whisper sounddevice soundfile numpy

echo ""
echo "설치 완료! 아래 명령어로 실행하세요:"
echo "  bash ~/Desktop/voice_assistant/run.sh"
