#!/usr/bin/env python3
"""
한국어 음성 명령 어시스턴트
웨이크워드: "하이 라꾸"
사용법: python3 voice_assistant.py
"""
import sys
import os
import tempfile
import subprocess
import asyncio

import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper
import edge_tts

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

WAKE_SILENCE = 0.8   # 웨이크워드 감지 후 침묵 판단 시간 (초) — 짧게
CMD_SILENCE  = 1.5   # 명령어 감지 후 침묵 판단 시간 (초)

# Whisper가 다양하게 전사할 수 있어서 여러 표기 등록
WAKE_WORDS = ["하이라크", "하이 라크", "하이라코", "하이 라코",
              "하이 라꾸", "하이라꾸", "하이 락구", "하이락구",
              "hi 라꾸", "하이 라구", "하이라구", "하이 락"]

# ──────────────────────────────────────────────
# 명령어 정의
# ──────────────────────────────────────────────
COMMANDS = [
    {
        "keywords": ["유튜브"],
        "action": lambda: subprocess.Popen(["google-chrome", "--new-tab", "https://www.youtube.com"]),
        "message": "유튜브를 엽니다."
    },
    {
        "keywords": ["챗지피티", "챗 지피티", "채치피티", "채 치피티", "chatgpt", "chat gpt", "챗gpt", "챗 gpt"],
        "action": lambda: subprocess.Popen(["google-chrome", "--new-tab", "https://chat.openai.com"]),
        "message": "챗GPT를 엽니다."
    },
    {
        "keywords": ["절전", "절전모드", "잠자기", "결정 모드", "결전 모드"],
        "action": lambda: subprocess.run(["systemctl", "suspend"]),
        "message": "절전 모드로 전환합니다."
    },
    {
        "keywords": ["재시작", "다시 시작", "시작해줘", "시작해 줘"],
        "action": lambda: subprocess.run(["reboot"]),
        "message": "재시작합니다."
    },
    {
        "keywords": ["종료", "끄기", "컴퓨터 꺼", "컴 꺼"],
        "action": lambda: subprocess.run(["shutdown", "now"]),
        "message": "시스템을 종료합니다."
    },
    {
        "keywords": ["볼륨 올려", "소리 올려", "볼륨 높여", "소리 높여", "소리 키워"],
        "action": lambda: subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"]),
        "message": "볼륨을 올립니다."
    },
    {
        "keywords": ["볼륨 내려", "소리 내려", "볼륨 낮춰", "소리 낮춰", "소리 줄여"],
        "action": lambda: subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"]),
        "message": "볼륨을 내립니다."
    },
    {
        "keywords": ["화면 꺼", "모니터 꺼", "화면 끄기", "화면 꺼져"],
        "action": lambda: subprocess.run(["xset", "dpms", "force", "off"]),
        "message": "화면을 끕니다."
    },
]


# ──────────────────────────────────────────────
# 오디오 함수
# ──────────────────────────────────────────────
def calibrate_threshold() -> float:
    """2초간 주변 소음을 측정해 자동으로 임계값 설정"""
    print("주변 소음 측정 중... (2초간 조용히 해주세요)", flush=True)
    chunks = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        blocksize=BLOCK_SIZE, dtype="float32") as stream:
        for _ in range(int(2 * SAMPLE_RATE / BLOCK_SIZE)):
            data, _ = stream.read(BLOCK_SIZE)
            chunks.append(float(np.abs(data).mean()))
    ambient = float(np.mean(chunks))
    threshold = max(ambient * 4, 0.01)
    print(f"주변 소음: {ambient:.4f}  →  임계값: {threshold:.4f}", flush=True)
    return threshold


def record_until_silence(threshold: float, silence_duration: float) -> np.ndarray | None:
    """소리가 감지되면 녹음 시작 → silence_duration초 침묵 시 종료"""
    frames = []
    recording = False
    silent_chunk_count = 0
    silence_chunks_needed = int(silence_duration * SAMPLE_RATE / BLOCK_SIZE)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        blocksize=BLOCK_SIZE, dtype="float32") as stream:
        while True:
            data, _ = stream.read(BLOCK_SIZE)
            volume = float(np.abs(data).mean())

            if volume > threshold:
                if not recording:
                    recording = True
                frames.append(data.copy())
                silent_chunk_count = 0
            elif recording:
                frames.append(data.copy())
                silent_chunk_count += 1
                if silent_chunk_count >= silence_chunks_needed:
                    break

    if not frames:
        return None
    return np.concatenate(frames, axis=0)


def transcribe(model: whisper.Whisper, audio: np.ndarray) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name
    try:
        sf.write(tmp_path, audio, SAMPLE_RATE)
        result = model.transcribe(tmp_path, language="ko", fp16=False)
        return result["text"].strip().lower()
    finally:
        os.unlink(tmp_path)


AUDIO_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".audio_cache")
VOICE = "ko-KR-SunHiNeural"

def _cache_path(text: str) -> str:
    import hashlib
    return os.path.join(AUDIO_CACHE_DIR, hashlib.md5(text.encode()).hexdigest() + ".mp3")

async def _generate(text: str, path: str):
    communicate = edge_tts.Communicate(text, voice=VOICE)
    await communicate.save(path)

def preload_voices(phrases: list[str]):
    """시작 시 자주 쓰는 문장을 미리 다운로드해서 캐싱"""
    os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
    for phrase in phrases:
        path = _cache_path(phrase)
        if not os.path.exists(path):
            print(f"음성 준비 중: '{phrase}'", flush=True)
            asyncio.run(_generate(phrase, path))

def speak(text: str):
    """캐시된 음성이 있으면 즉시 재생, 없으면 생성 후 재생"""
    path = _cache_path(text)
    if not os.path.exists(path):
        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
        asyncio.run(_generate(text, path))
    subprocess.run(["mpg123", "-q", path])


def is_wake_word(text: str) -> bool:
    return any(w in text for w in WAKE_WORDS)


COMMAND_HINTS = [
    "유튜브 열어줘",
    "챗지피티 열어줘",
    "절전 모드 해줘",
    "재시작해줘",
    "종료해줘",
    "볼륨 올려줘",
    "볼륨 내려줘",
    "화면 꺼줘",
]

def show_commands_alert(recognized: str):
    lines = "\n".join(f"• {h}" for h in COMMAND_HINTS)
    message = f"인식된 내용: '{recognized}'\n\n알아듣지 못했어요.\n\n이렇게 말해보세요:\n{lines}"
    subprocess.Popen(
        ["zenity", "--info", "--title=음성 어시스턴트", f"--text={message}", "--width=300"],
        stderr=subprocess.DEVNULL
    )


def execute_command(text: str) -> bool:
    for cmd in COMMANDS:
        for keyword in cmd["keywords"]:
            if keyword in text:
                print(f"[실행] {cmd['message']}", flush=True)
                cmd["action"]()
                return True
    print(f"[?] 알 수 없는 명령: '{text}'", flush=True)
    show_commands_alert(text)
    return False


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def print_banner():
    print("=" * 50)
    print("  한국어 음성 어시스턴트  (웨이크워드: 하이 라꾸)")
    print("=" * 50)
    print("사용 가능한 명령어:")
    for cmd in COMMANDS:
        print(f"  • {cmd['keywords'][0]}")
    print("\n종료: Ctrl+C")
    print("=" * 50)


def main():
    print_banner()
    print("\nWhisper 모델 로딩 중...", flush=True)
    model = whisper.load_model("small")

    preload_voices(["네! 말씀하세요.", "명령어를 듣지 못했습니다."])
    threshold = calibrate_threshold()
    print("\n대기 중...  '하이 라꾸' 라고 말하면 활성화됩니다.\n", flush=True)

    while True:
        try:
            # ── 1단계: 웨이크워드 대기 ──
            audio = record_until_silence(threshold, silence_duration=WAKE_SILENCE)
            if audio is None or len(audio) < SAMPLE_RATE * 0.2:
                continue

            text = transcribe(model, audio)

            if not is_wake_word(text):
                continue  # 웨이크워드 아니면 그냥 무시

            # ── 2단계: 웨이크워드 감지됨 ──
            print("네! 말씀하세요.", flush=True)
            speak("네! 말씀하세요.")

            # ── 3단계: 명령어 수신 ──
            audio = record_until_silence(threshold, silence_duration=CMD_SILENCE)
            if audio is None or len(audio) < SAMPLE_RATE * 0.3:
                print("명령어를 듣지 못했습니다.", flush=True)
                print("\n대기 중...", flush=True)
                continue

            print("분석 중...", flush=True)
            text = transcribe(model, audio)
            print(f"인식됨: '{text}'", flush=True)
            execute_command(text)

            print("\n대기 중...  '하이 라꾸' 라고 말하면 활성화됩니다.\n", flush=True)

        except KeyboardInterrupt:
            print("\n음성 어시스턴트를 종료합니다.")
            sys.exit(0)


if __name__ == "__main__":
    main()
