# Murmur

Private voice dictation for macOS. Your words stay yours.

## Quick Start

```bash
# 1. Clone and set up
git clone https://github.com/aosinda/murmur.git
cd murmur
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Running

**Required:** Add Terminal.app to **System Settings > Privacy & Security > Accessibility** (one-time setup).

```bash
.venv/bin/python -m app.main
```

A green dot appears in your menu bar. You're ready to dictate.

## Usage

| Shortcut | Action |
|---|---|
| **Fn** (hold) | Push-to-talk: hold to record, release to transcribe |
| **Fn + Space** | Toggle mode: press to start, stays on after release |
| **Fn** (while toggle active) | Stop recording and transcribe |
| **Escape** | Cancel current recording |
| **Ctrl + Cmd + V** | Re-insert last transcription into focused text field |
| **System tray** | Right-click green dot for Settings, Dictionary, Stats |

## Features

- Whisper transcription + GPT-5.4 Nano cleanup
- Multi-language — keeps your language, never translates (English, Bosnian, Danish, and more)
- Removes filler words (um, uh, like, you know, etc.)
- Formats spoken lists into numbered lists
- Custom dictionary for word replacements
- Vibe coding mode for dictating code
- Usage stats and 24-hour ephemeral history
- Bottom-anchored recording bar with timer

## Roadmap

- Signed macOS .app bundle (no manual Accessibility setup)
- Auto-start on login
- Local Whisper model option (fully offline)
- Transcription history with copy/paste
- Visual waveform during recording

## Requirements

- macOS 13+
- Python 3.11+
- OpenAI API key
