import os
import uuid
import socket
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import subprocess

from config import HOST, PORT, TEMP_DIR, STATIC_DIR, DEFAULT_WHISPER_MODEL, AUDIO_CODEC
from downloader import InstagramDownloader, is_valid_instagram_url
from transcriber import Transcriber, SUPPORTED_LANGUAGES, translate_segments, translate_text
from formatter import TranscriptFormatter
from summarizer import extractive_summary, ai_summary

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("instagram_transcript_app")

app = FastAPI(
    title="Instagram Transcript Generator",
    description="Extracts and transcribes audio from Instagram Reels and Posts into timestamped text with multi-format export and universal translation.",
    version="1.2.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active sessions & transcripts
task_store: Dict[str, Dict[str, Any]] = {}

downloader = InstagramDownloader(output_dir=TEMP_DIR)
transcriber = Transcriber(default_model=DEFAULT_WHISPER_MODEL)

class TranscribeRequest(BaseModel):
    url: str = Field(..., description="Instagram Reel or Post URL")
    model_size: str = Field(default=DEFAULT_WHISPER_MODEL, description="Whisper model size (tiny, base, small, medium)")
    engine: str = Field(default="local", description="Transcription engine ('local', 'groq', 'openai')")
    api_key: Optional[str] = Field(default=None, description="Optional API key for Groq or OpenAI")
    language: Optional[str] = Field(default="auto", description="Spoken language code (e.g. 'en', 'es', 'hi', 'auto')")
    task: str = Field(default="transcribe", description="'transcribe' for original verbatim, 'translate' for direct English")
    target_language: Optional[str] = Field(default=None, description="Optional target language code to translate into")
    cookies: Optional[str] = Field(default=None, description="Optional Instagram session cookies to bypass rate limits")

class TranslateRequest(BaseModel):
    task_id: str = Field(..., description="Task ID of previous transcript")
    target_language: str = Field(..., description="Target language code (e.g. 'es', 'hi', 'fr', 'ja')")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Instagram Transcript Generator",
        "default_model": DEFAULT_WHISPER_MODEL,
        "supported_languages_count": len(SUPPORTED_LANGUAGES)
    }

@app.get("/api/languages")
async def get_supported_languages():
    """Returns list of supported language codes and human-readable names."""
    return [{"code": k, "name": v} for k, v in SUPPORTED_LANGUAGES.items()]

@app.post("/api/transcribe")
async def transcribe_instagram(req: TranscribeRequest):
    """
    Main transcription endpoint for URLs.
    """
    url = req.url.strip()
    if not is_valid_instagram_url(url):
        raise HTTPException(
            status_code=400,
            detail="Invalid Instagram URL. Please provide a valid link to an Instagram Reel, Post, or Video."
        )

    try:
        logger.info(f"Processing transcription request for URL: {url} (task={req.task}, target_lang={req.target_language})")
        
        # Step 1: Download media & extract audio
        audio_path, metadata = downloader.download_audio(url, cookies=req.cookies)
        task_id = metadata["task_id"]

        # Step 2: Transcribe (Auto-use Groq Cloud if available for instant sub-second speed)
        active_groq_key = req.api_key if (req.engine == "groq" and req.api_key) else os.getenv("GROQ_API_KEY")
        active_openai_key = req.api_key if (req.engine == "openai" and req.api_key) else os.getenv("OPENAI_API_KEY")

        if active_groq_key:
            logger.info("Using ultra-fast Groq Whisper-large-v3 cloud engine...")
            trans_result = transcriber.transcribe_groq(
                audio_path,
                api_key=active_groq_key,
                language=req.language,
                task=req.task
            )
        elif active_openai_key:
            logger.info("Using OpenAI Whisper-1 cloud engine...")
            trans_result = transcriber.transcribe_openai(
                audio_path,
                api_key=active_openai_key,
                language=req.language,
                task=req.task
            )
        else:
            logger.info("Using local Faster-Whisper CPU engine...")
            trans_result = transcriber.transcribe_local(
                audio_path,
                model_size=req.model_size,
                language=req.language,
                task=req.task
            )

        # Step 3: Optional target language translation
        source_lang = trans_result.get("detected_language", "auto")
        if req.target_language and req.target_language not in ["auto", source_lang]:
            trans_result["translated_segments"] = translate_segments(
                trans_result.get("segments", []),
                target_lang=req.target_language,
                source_lang=source_lang
            )
            trans_result["translated_full_text"] = translate_text(
                trans_result.get("full_text", ""),
                target_lang=req.target_language,
                source_lang=source_lang
            )
            trans_result["target_language"] = req.target_language
            trans_result["target_language_name"] = SUPPORTED_LANGUAGES.get(req.target_language, req.target_language.upper())

        # Step 4: Summarize
        text_for_summary = trans_result.get("translated_full_text") or trans_result.get("full_text", "")
        if (req.engine in ["groq", "openai"]) and req.api_key:
            summary_info = ai_summary(text_for_summary, api_key=req.api_key, provider=req.engine)
        else:
            summary_info = extractive_summary(text_for_summary)

        # Step 5: Formats for active and original
        active_segments = trans_result.get("translated_segments") or trans_result.get("segments", [])
        orig_segments = trans_result.get("segments", [])

        txt_format = TranscriptFormatter.to_txt(active_segments, include_timestamps=True)
        txt_raw = TranscriptFormatter.to_txt(active_segments, include_timestamps=False)
        srt_format = TranscriptFormatter.to_srt(active_segments)
        vtt_format = TranscriptFormatter.to_vtt(active_segments)
        md_format = TranscriptFormatter.to_markdown(trans_result, metadata=metadata, summary=summary_info.get("summary"))

        orig_txt_format = TranscriptFormatter.to_txt(orig_segments, include_timestamps=True)
        orig_txt_raw = TranscriptFormatter.to_txt(orig_segments, include_timestamps=False)
        orig_srt_format = TranscriptFormatter.to_srt(orig_segments)
        orig_vtt_format = TranscriptFormatter.to_vtt(orig_segments)

        response_data = {
            "task_id": task_id,
            "metadata": metadata,
            "transcription": trans_result,
            "summary": summary_info,
            "audio_url": f"/api/audio/{task_id}",
            "formats": {
                "txt": txt_format,
                "txt_raw": txt_raw,
                "srt": srt_format,
                "vtt": vtt_format,
                "markdown": md_format,
                "orig_txt": orig_txt_format,
                "orig_txt_raw": orig_txt_raw,
                "orig_srt": orig_srt_format,
                "orig_vtt": orig_vtt_format,
            }
        }

        task_store[task_id] = {
            "audio_path": audio_path,
            "data": response_data
        }

        return response_data

    except Exception as e:
        logger.exception("Error during Instagram transcription:")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

@app.post("/api/upload")
async def upload_and_transcribe(
    file: UploadFile = File(...),
    model_size: str = Form(DEFAULT_WHISPER_MODEL),
    engine: str = Form("local"),
    api_key: Optional[str] = Form(None),
    language: Optional[str] = Form("auto"),
    task: str = Form("transcribe"),
    target_language: Optional[str] = Form(None)
):
    """
    Direct file upload endpoint for audio/video (.mp3, .m4a, .mp4, .wav, .webm).
    """
    try:
        task_id = str(uuid.uuid4())
        original_ext = Path(file.filename).suffix or ".mp3"
        raw_file_path = TEMP_DIR / f"{task_id}_raw{original_ext}"
        audio_file_path = TEMP_DIR / f"{task_id}.{AUDIO_CODEC}"

        # Save uploaded file
        with open(raw_file_path, "wb") as f:
            f.write(await file.read())

        # Convert to audio using ffmpeg
        logger.info(f"Converting uploaded file '{file.filename}' to audio...")
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_file_path),
            "-vn", "-ar", "16000", "-ac", "1", "-b:a", "128k",
            str(audio_file_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        metadata = {
            "task_id": task_id,
            "id": task_id,
            "title": file.filename,
            "uploader": "Direct Upload",
            "duration_formatted": "Uploaded File",
            "thumbnail": "",
            "webpage_url": ""
        }

        # Transcribe
        active_groq_key = api_key if (engine == "groq" and api_key) else os.getenv("GROQ_API_KEY")
        active_openai_key = api_key if (engine == "openai" and api_key) else os.getenv("OPENAI_API_KEY")

        if active_groq_key:
            logger.info("Using ultra-fast Groq Whisper-large-v3 cloud engine for uploaded file...")
            trans_result = transcriber.transcribe_groq(str(audio_file_path), api_key=active_groq_key, language=language, task=task)
        elif active_openai_key:
            logger.info("Using OpenAI Whisper-1 cloud engine for uploaded file...")
            trans_result = transcriber.transcribe_openai(str(audio_file_path), api_key=active_openai_key, language=language, task=task)
        else:
            logger.info("Using local Faster-Whisper CPU engine for uploaded file...")
            trans_result = transcriber.transcribe_local(str(audio_file_path), model_size=model_size, language=language, task=task)

        # Translation
        source_lang = trans_result.get("detected_language", "auto")
        if target_language and target_language not in ["auto", source_lang]:
            trans_result["translated_segments"] = translate_segments(trans_result.get("segments", []), target_lang=target_language, source_lang=source_lang)
            trans_result["translated_full_text"] = translate_text(trans_result.get("full_text", ""), target_lang=target_language, source_lang=source_lang)
            trans_result["target_language"] = target_language
            trans_result["target_language_name"] = SUPPORTED_LANGUAGES.get(target_language, target_language.upper())

        # Summarize
        text_for_summary = trans_result.get("translated_full_text") or trans_result.get("full_text", "")
        summary_info = extractive_summary(text_for_summary)

        # Formats
        active_segments = trans_result.get("translated_segments") or trans_result.get("segments", [])
        txt_format = TranscriptFormatter.to_txt(active_segments, include_timestamps=True)
        txt_raw = TranscriptFormatter.to_txt(active_segments, include_timestamps=False)
        srt_format = TranscriptFormatter.to_srt(active_segments)
        vtt_format = TranscriptFormatter.to_vtt(active_segments)
        md_format = TranscriptFormatter.to_markdown(trans_result, metadata=metadata, summary=summary_info.get("summary"))

        response_data = {
            "task_id": task_id,
            "metadata": metadata,
            "transcription": trans_result,
            "summary": summary_info,
            "audio_url": f"/api/audio/{task_id}",
            "formats": {
                "txt": txt_format,
                "txt_raw": txt_raw,
                "srt": srt_format,
                "vtt": vtt_format,
                "markdown": md_format,
            }
        }

        task_store[task_id] = {
            "audio_path": str(audio_file_path),
            "data": response_data
        }

        return response_data

    except Exception as e:
        logger.exception("Error uploading audio:")
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@app.post("/api/translate")
async def translate_existing_transcript(req: TranslateRequest):
    """
    Translates an existing transcript into any other target language on-the-fly.
    """
    if req.task_id not in task_store:
        raise HTTPException(status_code=404, detail="Transcript session not found or expired.")

    task_entry = task_store[req.task_id]
    task_data = task_entry["data"]
    trans_result = task_data.get("transcription", {})
    source_lang = trans_result.get("detected_language", "auto")

    logger.info(f"Translating task {req.task_id} from {source_lang} to {req.target_language}")
    translated_segments = translate_segments(
        trans_result.get("segments", []),
        target_lang=req.target_language,
        source_lang=source_lang
    )
    translated_full_text = translate_text(
        trans_result.get("full_text", ""),
        target_lang=req.target_language,
        source_lang=source_lang
    )

    summary_info = extractive_summary(translated_full_text)

    # Generate updated formats
    txt_format = TranscriptFormatter.to_txt(translated_segments, include_timestamps=True)
    srt_format = TranscriptFormatter.to_srt(translated_segments)
    vtt_format = TranscriptFormatter.to_vtt(translated_segments)

    updated_transcription = {
        **trans_result,
        "translated_segments": translated_segments,
        "translated_full_text": translated_full_text,
        "target_language": req.target_language,
        "target_language_name": SUPPORTED_LANGUAGES.get(req.target_language, req.target_language.upper())
    }

    task_data["transcription"] = updated_transcription
    task_data["summary"] = summary_info
    task_data["formats"]["txt"] = txt_format
    task_data["formats"]["srt"] = srt_format
    task_data["formats"]["vtt"] = vtt_format

    return {
        "task_id": req.task_id,
        "target_language": req.target_language,
        "target_language_name": SUPPORTED_LANGUAGES.get(req.target_language, req.target_language.upper()),
        "translated_segments": translated_segments,
        "translated_full_text": translated_full_text,
        "summary": summary_info,
        "formats": task_data["formats"]
    }

@app.get("/api/audio/{task_id}")
async def get_audio(task_id: str):
    """Streams extracted audio for the web player."""
    if task_id not in task_store:
        for ext in ["mp3", "m4a", "wav", "aac"]:
            candidate = TEMP_DIR / f"{task_id}.{ext}"
            if candidate.exists():
                return FileResponse(str(candidate), media_type=f"audio/{ext}")
        raise HTTPException(status_code=404, detail="Audio file not found or expired.")

    audio_path = task_store[task_id]["audio_path"]
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found on server.")

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        headers={"Accept-Ranges": "bytes"}
    )

@app.get("/api/export/{task_id}/{export_format}")
async def export_transcript(task_id: str, export_format: str):
    """Exports transcript file for direct download."""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Transcript session not found or expired.")

    task_data = task_store[task_id]["data"]
    formats = task_data.get("formats", {})
    export_format = export_format.lower()

    if export_format == "srt":
        content = formats.get("srt", "")
        media_type = "text/plain"
        filename = f"transcript_{task_id[:8]}.srt"
    elif export_format == "vtt":
        content = formats.get("vtt", "")
        media_type = "text/vtt"
        filename = f"transcript_{task_id[:8]}.vtt"
    elif export_format == "txt":
        content = formats.get("txt", "")
        media_type = "text/plain"
        filename = f"transcript_{task_id[:8]}.txt"
    elif export_format == "md" or export_format == "markdown":
        content = formats.get("markdown", "")
        media_type = "text/markdown"
        filename = f"transcript_{task_id[:8]}.md"
    elif export_format == "json":
        content = TranscriptFormatter.to_json(task_data)
        media_type = "application/json"
        filename = f"transcript_{task_id[:8]}.json"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {export_format}")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# Mount static files for the web interface
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

def is_port_available(host: str, port: int) -> bool:
    """Checks if a port is available on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

def find_available_port(host: str, start_port: int = 8000, max_attempts: int = 10) -> int:
    """Finds the first available port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        if is_port_available(host, p):
            return p
    return start_port

if __name__ == "__main__":
    import argparse
    env_port = int(os.getenv("PORT", os.getenv("SPACE_PORT", PORT)))
    env_host = os.getenv("HOST", "0.0.0.0" if os.getenv("SPACE_ID") or os.getenv("RENDER") else HOST)

    parser = argparse.ArgumentParser(description="Instagram Transcript Generator Web App")
    parser.add_argument("--host", default=env_host, help=f"Host to bind to (default: {env_host})")
    parser.add_argument("--port", "-p", type=int, default=env_port, help=f"Port to listen on (default: {env_port})")
    args = parser.parse_args()

    selected_host = args.host
    selected_port = args.port

    if not is_port_available(selected_host, selected_port):
        fallback_port = find_available_port(selected_host, start_port=selected_port + 1)
        logger.warning(f"Port {selected_port} is already in use. Automatically switching to http://{selected_host}:{fallback_port}")
        selected_port = fallback_port

    logger.info(f"Starting Instagram Transcript Generator web server on http://{selected_host}:{selected_port}")
    uvicorn.run("app:app", host=selected_host, port=selected_port, reload=False)
