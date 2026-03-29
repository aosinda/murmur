# Murmur

Private voice dictation for macOS. Your words stay yours.

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and add your OpenAI API key
# Also copied to ~/.murmur/.env on first run
```

## Running

**Important:** Terminal.app must have Accessibility permission.
Go to **System Settings > Privacy & Security > Accessibility** and add Terminal.app.

```bash
cd ~/projects/murmur && .venv/bin/python -m app.main
```

To run with debug logging:

```bash
cd ~/projects/murmur && .venv/bin/python -m app.main 2>&1 | tee /tmp/murmur_debug.log
```

## Usage

| Shortcut | Action |
|---|---|
| **Fn** (hold) | Push-to-talk: hold to record, release to transcribe |
| **Fn + Space** | Toggle mode: press to start recording, stays on after release |
| **Fn** (while toggle active) | Stop recording and transcribe |
| **Escape** | Cancel current recording |
| **Ctrl + Cmd + V** | Re-insert last transcription into focused text field |
| **System tray** | Right-click green dot for Settings, Dictionary, Stats |

## Features

- Whisper API transcription + GPT-5.4 Nano formatting
- Keeps original language (Bosnian, Danish, English, etc.) — no translation
- Removes filler words (um, uh, like, you know, etc.)
- Formats spoken lists into numbered lists
- Dictionary for custom word replacements
- Vibe coding mode for code dictation
- 24-hour ephemeral history, lifetime stats kept permanently
- Bottom-anchored recording bar with cancel/stop controls

## Building as .app (standalone)

```bash
# Rebuild the app bundle
pip install pyinstaller
pyinstaller murmur.spec

# Copy to Applications
cp -r dist/Murmur.app /Applications/

# Then add Murmur to Accessibility permissions:
# System Settings > Privacy & Security > Accessibility > "+" > Murmur
```

Note: Every rebuild changes the binary, so you must re-add Murmur to Accessibility permissions after each build.
