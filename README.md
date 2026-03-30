# Murmur

Private voice dictation for macOS and Windows. Your words stay yours.

## Quick Start

```bash
git clone https://github.com/aosinda/murmur.git
cd murmur
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

On first launch, Murmur walks you through setting up your API key and permissions.

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

## Building as Standalone App

### macOS (.app)

```bash
./scripts/build_macos.sh
```

Builds, signs, and installs to `/Applications`. Add Murmur to Accessibility permissions once.

### Windows (.exe)

```bash
scripts\build_windows.bat
```

Builds to `dist\Murmur\Murmur.exe`.

## Usage

### macOS Shortcuts

| Shortcut | Action |
|---|---|
| **Fn** (hold) | Push-to-talk: hold to record, release to transcribe |
| **Fn + Space** | Toggle mode: press to start, press Fn again to stop |
| **Escape** | Cancel current recording |
| **Ctrl + Cmd + V** | Re-insert last transcription |

### Windows Shortcuts

| Shortcut | Action |
|---|---|
| **Ctrl + Shift** (hold) | Push-to-talk: hold to record, release to transcribe |
| **Ctrl + Shift + Space** | Toggle mode: press to start, press again to stop |
| **Escape** | Cancel current recording |

### App UI

- **Dashboard** — weeks active, total words, WPM, sessions
- **History** — recent transcriptions with copy button (24h retention)
- **Settings** — mic, languages, vibe coding mode (via tray menu)
- **Dictionary** — custom word replacements (via tray menu)
- **Status bar** — shows ready / recording / processing

Click the green tray icon or right-click for the menu.

## Features

- Whisper transcription + GPT-5.4 Nano cleanup
- Multi-language — keeps your language, never translates
- Removes filler words (um, uh, like, you know, etc.)
- Formats spoken lists into numbered lists
- Custom dictionary for word replacements
- Vibe coding mode for dictating code
- First-launch onboarding for non-coders
- Cross-platform: macOS and Windows

## Roadmap

- Local Whisper model option (fully offline, zero cost)
- Auto-start on login
- Visual waveform during recording
- Signed macOS builds (no manual Accessibility setup)

## Requirements

- macOS 13+ or Windows 10+
- Python 3.11+
- OpenAI API key
