#!/usr/bin/env python3
"""마이크 볼륨 테스트 - 현재 볼륨 수치를 실시간으로 출력"""
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

print("마이크 테스트 시작 (종료: Ctrl+C)")
print("말을 해보세요. 볼륨 수치가 올라가면 마이크가 정상입니다.\n")

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                    blocksize=BLOCK_SIZE, dtype="float32") as stream:
    while True:
        try:
            data, _ = stream.read(BLOCK_SIZE)
            volume = float(np.abs(data).mean())
            bar = "#" * int(volume * 1000)
            print(f"볼륨: {volume:.5f}  [{bar:<40}]", end="\r")
        except KeyboardInterrupt:
            break

print("\n\n현재 SILENCE_THRESHOLD = 0.012")
print("말할 때 볼륨이 0.012 이상이면 정상, 이하면 임계값을 낮춰야 합니다.")
