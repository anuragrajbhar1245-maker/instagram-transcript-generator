# 📸 Instagram Transcript Generator

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Whisper AI](https://img.shields.io/badge/AI-Faster--Whisper-orange.svg?logo=openai&logoColor=white)](https://github.com/SYSTRAN/faster-whisper)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A complete, self-contained AI-powered application to extract and generate timestamped transcripts from **Instagram Reels, Posts, and Videos** in **99+ languages** with instant SRT/VTT subtitle export and high-accuracy neural translation.

---

## ✨ Features

- **🎙️ 100% Free & Offline Capable**: Powered by `faster-whisper` on CPU (with `int8` quantization) — no paid API keys or external proxies required.
- **🌐 Universal Multilingual Speech-to-Text**:
  - Auto-detects 99+ spoken languages (English, Hindi, Spanish, French, German, Japanese, Arabic, Russian, Marathi, Bengali, Telugu, and more).
  - Preserves pure native script by default (e.g. हिन्दी / देवनागरी).
  - 1-Click instant neural translation to fluent English or any other language.
- **🖥️ Modern Glassmorphism Web UI**:
  - Live pipeline progress animation (Download → Transcribe → Format).
  - Built-in audio player with speed controls (1.0x, 1.25x, 1.5x, 2.0x).
  - **Synchronized transcript playback**: Click on any timestamp to jump the audio directly to that exact moment.
  - Live keyword search and highlight inside transcripts.
  - AI & heuristic executive summaries and bullet-point highlights.
  - Export to **SRT**, **WebVTT**, **Plain Text (.txt)**, **JSON**, and **Markdown (.md)**.
  - Local history drawer to easily re-open past transcripts.
  - **Direct File Upload Mode**: Drag and drop any `.mp4`, `.mp3`, `.m4a`, or `.wav` file to transcribe without link restrictions.
- **💻 Scriptable CLI**: Complete command-line interface for terminal automation and batch processing.
- **☁️ Cloud & Docker Ready**: Multi-stage `Dockerfile` and `render.yaml` blueprint included for 1-click cloud deployment.

---

## 📋 Prerequisites

Before running the project, make sure you have:
1. **Python 3.10 or higher** installed.
2. **FFmpeg** installed (required for audio extraction):
   - **Windows**: `winget install Gyan.FFmpeg` or `choco install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt update && sudo apt install -y ffmpeg`

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/anuragrajbhar1245-maker/instagram-transcript-generator.git
cd instagram-transcript-generator
```

### 2. Create and Activate a Virtual Environment
- **On Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **On macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the Web App
```bash
python app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your web browser!

---

## 📱 One-Click Public Link (Worldwide Access)

To access your local server from your mobile phone or share with others worldwide without deploying to cloud:

```bash
python run_public.py
```
This starts the local server and generates a free secure HTTPS tunnel URL (powered by `localtunnel`).

---

## 🛠️ CLI Usage (Command-Line)

You can transcribe Instagram Reels directly from your terminal:

```bash
# 1. Print transcript directly to terminal
python cli.py "https://www.instagram.com/reel/C8xxx..."

# 2. Export as SubRip (.srt) subtitle file
python cli.py "https://www.instagram.com/reel/C8xxx..." --format srt --output reel_subtitles.srt

# 3. Export in WebVTT (.vtt) format
python cli.py "https://www.instagram.com/reel/C8xxx..." --format vtt --output reel_subtitles.vtt

# 4. Export all formats (.txt, .srt, .vtt, .json, .md)
python cli.py "https://www.instagram.com/reel/C8xxx..." --format all --output my_transcript

# 5. Use a specific Whisper model (tiny, base, small, medium)
python cli.py "https://www.instagram.com/reel/C8xxx..." --model small
```

---

## 🐳 Docker Deployment

### Run with Docker Locally:
```bash
# Build the Docker image
docker build -t instagram-transcript-generator .

# Run the container on port 8000
docker run -p 8000:8000 instagram-transcript-generator
```
Open **[http://localhost:8000](http://localhost:8000)**.

---

## ☁️ 1-Click Free Cloud Deployment (Render.com)

1. Fork or push this repository to your GitHub account.
2. Go to **[Render.com Dashboard](https://dashboard.render.com/)** and sign in with GitHub.
3. Click **New +** ➔ **Web Service** ➔ Select `instagram-transcript-generator`.
4. Render will automatically detect the `Dockerfile` and `render.yaml`.
5. Select **Free** instance type and click **Deploy Web Service**!

---

## 📁 Project Architecture

```
instagram-transcript-generator/
├── app.py                  # FastAPI server & REST API endpoints
├── cli.py                  # Command-line interface tool
├── config.py               # Central configuration (paths, audio codec, ports)
├── downloader.py           # Instagram media downloader (yt-dlp + FFmpeg)
├── formatter.py            # Formats SRT, VTT, TXT, JSON, and Markdown
├── run_public.py           # One-click public tunnel runner (localtunnel)
├── summarizer.py           # Extractive & AI executive summarizer
├── transcriber.py          # Faster-Whisper & translation engine
├── requirements.txt        # Python package dependencies
├── Dockerfile              # Production multi-stage Docker container
├── render.yaml             # Render cloud deployment blueprint
├── static/                 # Single-page web application frontend
│   ├── index.html          # Responsive Tailwind CSS interface
│   ├── app.js              # Audio player sync, search, history & export logic
│   └── styles.css          # Glassmorphism dark mode styles
└── tests/                  # Pytest automated test suite
    ├── test_downloader.py  # Link validation and normalization tests
    ├── test_formatter.py   # Subtitle & timestamp generation tests
    └── test_transcriber.py # Multilingual & summary tests
```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status & loaded model information |
| `GET` | `/api/languages` | List of 99+ supported spoken language codes and names |
| `POST` | `/api/transcribe` | Transcribe an Instagram Reel/Post URL |
| `POST` | `/api/upload` | Upload & transcribe an audio/video file directly |
| `POST` | `/api/translate` | Translate an existing transcript into any target language |
| `GET` | `/api/audio/{task_id}` | Stream extracted audio for web player |
| `GET` | `/api/export/{task_id}/{format}` | Download subtitle/transcript file (`srt`, `vtt`, `txt`, `json`, `md`) |

---

## 🧪 Running Automated Tests

```bash
python -m pytest tests/ -v
```

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
