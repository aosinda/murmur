# Murmur

Private voice dictation for macOS and Windows. Your words stay yours.

## Quick Start

```bash
git clone https://github.com/aosinda/murmur.git
cd murmur
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

On first launch, Murmur walks you through setup — choose Cloud (OpenAI API) or Local (offline).

## Running

### macOS

Add **Terminal.app** to **System Settings > Privacy & Security > Accessibility** (one-time).

```bash
.venv/bin/python -m app.main
```

### Windows

```bash
.venv\Scripts\python -m app.main
```

## Usage

### macOS Shortcuts

| Shortcut | Action |
|---|---|
| **Fn** (hold) | Push-to-talk: hold to record, release to transcribe |
| **Fn + Space** | Toggle recording on |
| **Fn + Space** | Toggle recording off (same combo) |
| **Escape** | Cancel current recording |
| **Ctrl + Cmd + V** | Re-insert last transcription |

### Windows Shortcuts

| Shortcut | Action |
|---|---|
| **Ctrl + Shift** (hold) | Push-to-talk: hold to record, release to transcribe |
| **Ctrl + Shift + Space** | Toggle recording on/off |
| **Escape** | Cancel current recording |

### Bottom Bar

A persistent floating bar sits at the bottom of your screen:
- **Idle**: green play button — click to start recording
- **Recording**: cancel (✕), animated waveform, timer, stop (■)

The bar never steals focus from your active app.

### App UI

Click the green tray icon to open the dashboard:
- **Dashboard** — weeks active, total words, WPM, sessions
- **History** — recent transcriptions with copy button (24h retention)
- **Settings** — mic, languages, vibe coding mode (via tray menu)
- **Dictionary** — custom word replacements (via tray menu)

## Features

- **Two modes**: Cloud (OpenAI Whisper + GPT) or Local (offline, free)
- Multi-language — keeps your language, never translates
- Removes filler words (um, uh, like, you know, etc.)
- Formats spoken lists into numbered lists
- Custom dictionary for word replacements
- Vibe coding mode for dictating code
- First-launch onboarding for non-coders
- Cross-platform: macOS and Windows

## Roadmap

- Signed macOS .app bundle (no manual Accessibility setup)
- Auto-start on login
- Visual waveform driven by actual audio input
- Light/dark theme options

## Requirements

- macOS 13+ or Windows 10+
- Python 3.11+
- OpenAI API key (cloud mode only)
