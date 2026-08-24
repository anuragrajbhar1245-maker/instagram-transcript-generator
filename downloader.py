import os
import re
import uuid
import logging
import subprocess
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import yt_dlp
from config import TEMP_DIR, AUDIO_CODEC, AUDIO_BITRATE, AUDIO_SAMPLE_RATE

logger = logging.getLogger("instagram_downloader")
logging.basicConfig(level=logging.INFO)

# Regex pattern matching various Instagram URL formats
INSTAGRAM_URL_REGEX = re.compile(
    r"^(https?://)?(www\.)?instagram\.com/(reel|p|tv|share)/([A-Za-z0-9_\-]+)",
    re.IGNORECASE
)

# Public Instagram App ID used by official web client
INSTAGRAM_WEB_APP_ID = "936619743392459"

def is_valid_instagram_url(url: str) -> bool:
    """Checks whether the provided URL is a valid Instagram Reel, Post, or Video link."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    return bool(INSTAGRAM_URL_REGEX.match(url) or "instagram.com" in url)

def normalize_instagram_url(url: str) -> str:
    """Cleans up tracking parameters and returns a clean URL."""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    
    # Strip URL tracking query parameters (?utm_source=..., ?igsh=..., etc.)
    base_url = url.split("?")[0]
    if not base_url.endswith("/"):
        base_url += "/"
    return base_url

class InstagramDownloader:
    def __init__(self, output_dir: Optional[Path] = None, cookies_path: Optional[str] = None):
        self.output_dir = output_dir or TEMP_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_path = cookies_path or os.getenv("INSTAGRAM_COOKIES_PATH")
        
        # Check project root cookies.txt
        root_cookies = Path(__file__).parent / "cookies.txt"
        if not self.cookies_path and root_cookies.exists():
            self.cookies_path = str(root_cookies)

        # Check for cookies in environment variable
        env_cookies_text = os.getenv("INSTAGRAM_COOKIES")
        if env_cookies_text and not self.cookies_path:
            cookies_file = self.output_dir / "cookies.txt"
            cookies_file.write_text(env_cookies_text, encoding="utf-8")
            self.cookies_path = str(cookies_file)

    def get_ydl_opts(self, output_template: str, custom_cookies: Optional[str] = None) -> Dict[str, Any]:
        """Returns configured yt-dlp options with Instagram web app authentication headers."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "X-IG-App-ID": INSTAGRAM_WEB_APP_ID,
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        }

        if custom_cookies:
            headers["Cookie"] = custom_cookies.strip()

        opts: Dict[str, Any] = {
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "noplaylist": True,
            "format": "bestaudio/bestvideo+bestaudio/best",
            "http_headers": headers,
            "extractor_args": {
                "instagram": {
                    "app_id": [INSTAGRAM_WEB_APP_ID],
                }
            }
        }

        if self.cookies_path and os.path.exists(self.cookies_path):
            opts["cookiefile"] = self.cookies_path

        return opts

    def download_audio(self, url: str, cookies: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Downloads media and converts audio from the Instagram URL.
        Returns (audio_filepath, metadata_dict).
        """
        clean_url = normalize_instagram_url(url)
        task_id = str(uuid.uuid4())
        raw_output_template = str(self.output_dir / f"{task_id}_raw.%(ext)s")
        expected_audio_path = str(self.output_dir / f"{task_id}.{AUDIO_CODEC}")

        ydl_opts = self.get_ydl_opts(raw_output_template, custom_cookies=cookies)

        # Attempt 1: Standard extraction
        raw_downloaded_file = None
        info = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=True)
                if info:
                    raw_downloaded_file = ydl.prepare_filename(info)
        except Exception as first_err:
            logger.warning(f"First download pass failed ({first_err}). Attempting fallback anonymous pass...")
            # Attempt 2: Fallback without cookies
            try:
                fallback_opts = self.get_ydl_opts(raw_output_template, custom_cookies=None)
                fallback_opts.pop("cookiefile", None)
                with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                    info = ydl.extract_info(clean_url, download=True)
                    if info:
                        raw_downloaded_file = ydl.prepare_filename(info)
            except Exception as e:
                err_msg = str(e)
                if "HTTP Error 400" in err_msg or "HTTP Error 404" in err_msg or "not found" in err_msg.lower() or "Video info extraction failed" in err_msg:
                    raise ValueError(
                        "This Instagram Reel or Post could not be found. It may have been deleted, "
                        "is from a private account, or the link is expired/invalid."
                    ) from e
                if "unable to obtain file audio codec" in err_msg or "silent" in err_msg.lower():
                    raise ValueError(
                        "This Instagram Reel/Video has no audio track (it is completely silent). "
                        "Please test with a video that has audio or speech."
                    ) from e
                if "HTTP Error 429" in err_msg or "rate-limit" in err_msg.lower():
                    raise ValueError(
                        "Instagram rate-limit reached. Please try uploading the media file directly in the Upload tab, or configure your Instagram cookies in Settings."
                    ) from e
                raise e

        if not info:
            raise ValueError("Failed to download media from the provided Instagram URL.")

        # Check if video is silent/muted
        formats = info.get("formats", [])
        has_audio = any(f.get("acodec") not in [None, "none", ""] for f in formats)
        if formats and not has_audio and info.get("acodec") in [None, "none", ""]:
            raise ValueError(
                "This Instagram Reel/Video does not have any audio track (it is silent or muted). "
                "Please provide an Instagram video that contains speech or sound."
            )

        # Convert downloaded media to standardized audio using direct FFmpeg
        if not os.path.exists(raw_downloaded_file):
            # Check for alternative extensions
            for ext in ["mp4", "webm", "m4a", "mp3", "mov", "mkv"]:
                alt_path = str(self.output_dir / f"{task_id}_raw.{ext}")
                if os.path.exists(alt_path):
                    raw_downloaded_file = alt_path
                    break

        if not os.path.exists(raw_downloaded_file):
            raise FileNotFoundError(f"Could not locate downloaded media file for task {task_id}")

        # Run direct FFmpeg extraction to MP3 (16kHz mono)
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", str(raw_downloaded_file),
            "-vn", "-ar", str(AUDIO_SAMPLE_RATE), "-ac", "1", "-b:a", AUDIO_BITRATE,
            str(expected_audio_path)
        ]
        res = subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        
        # Check if FFmpeg succeeded in producing the audio
        if not os.path.exists(expected_audio_path) or os.path.getsize(expected_audio_path) == 0:
            if "does not contain any stream" in res.stderr or "Output file is empty" in res.stderr or res.returncode != 0:
                raise ValueError(
                    "This Instagram Reel does not contain an audio track (it is silent). "
                    "Please provide a video with spoken words or audio."
                )

        # Cleanup raw video file to save disk space
        try:
            if os.path.exists(raw_downloaded_file):
                os.remove(raw_downloaded_file)
        except Exception:
            pass

        metadata = {
            "task_id": task_id,
            "id": info.get("id", task_id),
            "title": info.get("title") or info.get("description", "Instagram Reel")[:80],
            "description": info.get("description", ""),
            "uploader": info.get("uploader", "Instagram Creator"),
            "uploader_id": info.get("uploader_id", ""),
            "duration": info.get("duration", 0),
            "duration_formatted": f"{int(info.get('duration', 0) // 60):02d}:{int(info.get('duration', 0) % 60):02d}" if info.get('duration') else "Unknown",
            "thumbnail": info.get("thumbnail", ""),
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "comment_count": info.get("comment_count", 0),
            "webpage_url": info.get("webpage_url", clean_url),
            "subtitles": info.get("subtitles", {}),
            "automatic_captions": info.get("automatic_captions", {}),
        }

        return expected_audio_path, metadata
