#!/usr/bin/env python3
"""
Whisper가 내 말을 어떻게 인식하는지 확인하는 테스트
'하이 라꾸'를 여러 번 말해보세요.
"""
import sys, os, tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

print("Whisper 로딩 중...", flush=True)
model = whisper.load_model("small")

# 소음 측정
print("소음 측정 중... (2초 조용히)", flush=True)
chunks = []
with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=BLOCK_SIZE, dtype="float32") as s:
    for _ in range(int(2 * SAMPLE_RATE / BLOCK_SIZE)):
        d, _ = s.read(BLOCK_SIZE)
        chunks.append(float(np.abs(d).mean()))
threshold = max(float(np.mean(chunks)) * 4, 0.01)
print(f"임계값: {threshold:.4f}\n", flush=True)
print("'하이 라꾸' 라고 말해보세요. (종료: Ctrl+C)\n", flush=True)
print(f"[임계값: {threshold:.4f}] — 이 값보다 높아야 녹음 시작\n", flush=True)

count = 0
while True:
    try:
        frames = []
        recording = False
        silent = 0
        needed = int(0.8 * SAMPLE_RATE / BLOCK_SIZE)

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=BLOCK_SIZE, dtype="float32") as s:
            while True:
                data, _ = s.read(BLOCK_SIZE)
                vol = float(np.abs(data).mean())
                bar = "#" * int(vol * 300)
                print(f"볼륨: {vol:.4f} [{bar:<30}]  {'[녹음중]' if recording else ''}", end="\r", flush=True)
                if vol > threshold:
                    if not recording:
                        print("\n녹음 시작!", flush=True)
                        recording = True
                    frames.append(data.copy())
                    silent = 0
                elif recording:
                    frames.append(data.copy())
                    silent += 1
                    if silent >= needed:
                        break

        if not frames:
            continue

        audio = np.concatenate(frames)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, SAMPLE_RATE)
            result = model.transcribe(f.name, language="ko", fp16=False)
            os.unlink(f.name)

        count += 1
        text = result["text"].strip()
        print(f"[{count}회] Whisper 인식 결과: '{text}'", flush=True)

    except KeyboardInterrupt:
        print("\n테스트 종료.")
        sys.exit(0)
