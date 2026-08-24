# 📸 Instagram Transcript Generator

A complete, self-contained AI-powered application to extract and generate timestamped transcripts from Instagram Reels and Posts.

Features:
- **100% Free & Offline Capable**: Powered by `faster-whisper` on CPU (with `int8` quantization) — no paid API or external proxy required.
- **Modern Interactive Web UI**:
  - Live pipeline progress animation (Download → Transcribe → Format).
  - Built-in audio player with speed controls (1x, 1.25x, 1.5x, 2x).
  - Synchronized transcript playback: click on any timestamp to jump the audio directly to that moment.
  - Live keyword search and highlight inside transcripts.
  - AI & heuristic executive summaries and bullet points.
  - Export to **SRT**, **WebVTT**, **Plain Text**, **JSON**, and **Markdown**.
  - Local history drawer to easily re-open past transcripts.
- **Command Line Interface (CLI)**:
  - Scriptable transcription tool for single reels or batch processing.
- **Multi-Engine Support**:
  - Local Faster-Whisper (`tiny`, `base`, `small`, `medium`).
  - Optional direct Groq or OpenAI Whisper API key if instant cloud processing is desired.

---

## 🚀 Quick Start

### 1. Start the Web App
```bash
cd instagram-transcript-generator
python app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### 2. Using the CLI Tool
```bash
# Basic transcription (prints to terminal)
python cli.py "https://www.instagram.com/reel/C8xxx..."

# Export as SubRip (.srt) subtitle file
python cli.py "https://www.instagram.com/reel/C8xxx..." --format srt --output reel_subtitles.srt

# Export in all formats (.txt, .srt, .vtt, .json, .md)
python cli.py "https://www.instagram.com/reel/C8xxx..." --format all --output my_reel_transcript

# Use higher accuracy model (e.g. small or medium)
python cli.py "https://www.instagram.com/reel/C8xxx..." --model small
```

---

## 📁 Project Architecture

```
instagram-transcript-generator/
├── app.py                  # FastAPI server & REST API
├── cli.py                  # Command-line interface
├── downloader.py           # Instagram media downloader (yt-dlp + ffmpeg)
├── transcriber.py          # Faster-Whisper & cloud API transcription engine
├── formatter.py            # Formats SRT, VTT, TXT, JSON, Markdown
├── summarizer.py           # Extractive & AI summarizer
├── config.py               # Application configurations
├── requirements.txt        # Python package dependencies
├── static/                 # Single-page web application
│   ├── index.html          # Modern Tailwind CSS HTML5 interface
│   ├── app.js              # Audio player sync, search, history & export logic
│   └── styles.css          # Glassmorphism dark mode styles
└── tests/                  # Pytest test suite
    ├── test_downloader.py  # Link validation and normalization tests
    ├── test_formatter.py   # Subtitle & timestamp generation tests
    └── test_transcriber.py # Summary and parameter tests
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```
