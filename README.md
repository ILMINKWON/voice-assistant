# Korean Voice Assistant

A wake-word based voice assistant for Linux that listens for **"하이 라꾸"** and executes system commands in Korean.

## Features

- Wake word activation — only listens for commands after hearing "하이 라꾸"
- Offline speech recognition using OpenAI Whisper
- Natural Korean female TTS response using Microsoft edge-tts
- Auto-starts on login via `~/.config/autostart`
- Auto-calibrates mic threshold based on ambient noise at startup
- Shows a popup with available commands when speech is not recognized

## Supported Commands

| Say | Action |
|-----|--------|
| 유튜브 열어줘 | Open YouTube in Chrome |
| 챗지피티 열어줘 | Open ChatGPT in Chrome |
| 절전 모드 해줘 | Suspend (sleep mode) |
| 재시작해줘 | Reboot |
| 종료해줘 | Shutdown |
| 볼륨 올려줘 | Volume +10% |
| 볼륨 내려줘 | Volume -10% |
| 화면 꺼줘 | Turn off monitor |

## How It Works

```
Boot → Login → Auto-start (5s delay)
→ Set mic volume to 100%
→ Load Whisper model
→ Pre-cache TTS audio
→ Measure ambient noise → set threshold

[Loop]
Listen → detect speech → Whisper transcribe
→ Wake word? NO → ignore
→ YES → speak "네! 말씀하세요."
→ Listen for command → Whisper transcribe
→ Match keyword → execute system command
→ No match → show zenity popup with command list
```

## Tech Stack

| Role | Tool |
|------|------|
| Speech Recognition (STT) | OpenAI Whisper (small, offline) |
| Text to Speech (TTS) | Microsoft edge-tts (`ko-KR-SunHiNeural`) |
| Mic input | sounddevice + numpy |
| Audio playback | mpg123 |
| Popup dialog | zenity |
| Mic volume control | pactl (PipeWire) |
| Auto-start | `~/.config/autostart/` |

## Installation

```bash
# System packages
sudo apt-get install -y portaudio19-dev libsndfile1 python3-venv ffmpeg espeak-ng mpg123

# Run install script (creates venv + installs Python packages)
bash install.sh
```

## Usage

```bash
bash run.sh
```

Or double-click `voice_assistant.desktop` on the desktop.

## Notes

- Whisper does not always transcribe Korean exactly as spoken.  
  e.g. "챗지피티" → recognized as "채치피티", "화면 꺼줘" → "화면 꺼져"  
  Use `wake_test.py` to check how Whisper hears your voice and add keywords accordingly.
- Requires internet connection for edge-tts (first run only — responses are cached locally).
- Tested on Ubuntu 24.04 with PipeWire audio.
