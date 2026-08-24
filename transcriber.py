import os
import glob
import logging
from typing import Dict, Any, List, Optional
from faster_whisper import WhisperModel
import requests
from deep_translator import GoogleTranslator
from config import DEFAULT_WHISPER_MODEL, DEFAULT_DEVICE, DEFAULT_COMPUTE_TYPE

logger = logging.getLogger("transcriber")
logging.basicConfig(level=logging.INFO)

# Global model cache to avoid reloading on each request
_loaded_models: Dict[str, WhisperModel] = {}

# Major supported languages mapping
SUPPORTED_LANGUAGES = {
    "auto": "Auto Detect (99+ Languages)",
    "en": "English",
    "es": "Spanish (Español)",
    "hi": "Hindi (हिन्दी)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "it": "Italian (Italiano)",
    "pt": "Portuguese (Português)",
    "ru": "Russian (Русский)",
    "zh": "Chinese (中文)",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "ar": "Arabic (العربية)",
    "tr": "Turkish (Türkçe)",
    "nl": "Dutch (Nederlands)",
    "pl": "Polish (Polski)",
    "id": "Indonesian (Bahasa)",
    "vi": "Vietnamese (Tiếng Việt)",
    "th": "Thai (ไทย)",
    "te": "Telugu (తెలుగు)",
    "ta": "Tamil (தமிழ்)",
    "bn": "Bengali (বাংলা)",
    "mr": "Marathi (मराठी)",
    "gu": "Gujarati (ગુજરાતી)",
    "ur": "Urdu (اردو)",
    "fa": "Persian (فارسی)",
    "uk": "Ukrainian (Українська)",
    "sv": "Swedish (Svenska)",
    "el": "Greek (Ελληνικά)",
    "cs": "Czech (Čeština)",
    "he": "Hebrew (עברית)",
    "ro": "Romanian (Română)",
    "hu": "Hungarian (Magyar)",
    "da": "Danish (Dansk)",
    "fi": "Finnish (Suomi)",
    "no": "Norwegian (Norsk)"
}

def find_local_cached_model_path(model_size: str) -> Optional[str]:
    """Finds if the model snapshot is already downloaded in local HuggingFace cache."""
    cache_base = os.path.expanduser("~/.cache/huggingface/hub")
    pattern = os.path.join(cache_base, f"models--Systran--faster-whisper-{model_size}", "snapshots", "*")
    matches = glob.glob(pattern)
    if matches and os.path.isdir(matches[0]):
        candidate = matches[0]
        if os.path.exists(os.path.join(candidate, "model.bin")):
            return candidate
    return None

def get_whisper_model(model_size: str = DEFAULT_WHISPER_MODEL) -> WhisperModel:
    """Retrieves or initializes a cached WhisperModel."""
    if model_size not in _loaded_models:
        local_path = find_local_cached_model_path(model_size)
        if local_path:
            logger.info(f"Loading local cached Whisper model from '{local_path}' on {DEFAULT_DEVICE} ({DEFAULT_COMPUTE_TYPE})...")
            _loaded_models[model_size] = WhisperModel(
                local_path,
                device=DEFAULT_DEVICE,
                compute_type=DEFAULT_COMPUTE_TYPE,
                local_files_only=True
            )
        else:
            logger.info(f"Loading Whisper model '{model_size}' from Hub on {DEFAULT_DEVICE} ({DEFAULT_COMPUTE_TYPE})...")
            _loaded_models[model_size] = WhisperModel(
                model_size,
                device=DEFAULT_DEVICE,
                compute_type=DEFAULT_COMPUTE_TYPE
            )
        logger.info(f"Whisper model '{model_size}' loaded successfully.")
    return _loaded_models[model_size]

def translate_text(text: str, target_lang: str = "en", source_lang: str = "auto") -> str:
    """Translates plain text into the target language using deep-translator."""
    if not text or not text.strip():
        return ""
    if source_lang == target_lang and target_lang != "auto":
        return text
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text)
    except Exception as e:
        logger.warning(f"Translation failed for '{text[:30]}...': {e}")
        return text

def translate_segments(segments: List[Dict[str, Any]], target_lang: str = "en", source_lang: str = "auto") -> List[Dict[str, Any]]:
    """Translates a list of timestamped segments while preserving start and end timestamps."""
    if not segments or (source_lang == target_lang and target_lang != "auto"):
        return segments

    translated_segments = []
    translator = GoogleTranslator(source=source_lang, target=target_lang)

    for s in segments:
        original_text = s.get("text", "").strip()
        if not original_text:
            continue
        try:
            trans_text = translator.translate(original_text)
        except Exception:
            trans_text = original_text

        translated_segments.append({
            **s,
            "original_text": original_text,
            "text": trans_text
        })

    return translated_segments

class Transcriber:
    def __init__(self, default_model: str = DEFAULT_WHISPER_MODEL):
        self.default_model = default_model

    def transcribe_local(
        self,
        audio_path: str,
        model_size: Optional[str] = None,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribes or translates audio file using faster-whisper locally.
        - task="transcribe": transcribes original spoken language verbatim
        - task="translate": translates speech directly into English timestamps
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        chosen_model = model_size or self.default_model
        model = get_whisper_model(chosen_model)

        logger.info(f"Processing audio with local Whisper ({chosen_model}, task={task}, lang={language})...")
        segments_gen, info = model.transcribe(
            audio_path,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            language=language if language and language != "auto" else None,
            task=task,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400),
            word_timestamps=False
        )

        segments: List[Dict[str, Any]] = []
        full_text_parts = []

        for s in segments_gen:
            words = []
            if s.words:
                for w in s.words:
                    words.append({
                        "word": w.word.strip(),
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                        "probability": round(w.probability, 2)
                    })

            clean_text = s.text.strip()
            if clean_text:
                full_text_parts.append(clean_text)
                segments.append({
                    "id": s.id,
                    "seek": s.seek,
                    "start": round(s.start, 2),
                    "end": round(s.end, 2),
                    "text": clean_text,
                    "avg_logprob": round(s.avg_logprob, 2),
                    "no_speech_prob": round(s.no_speech_prob, 2),
                    "words": words
                })

        full_transcript = " ".join(full_text_parts)

        return {
            "engine": "local_whisper",
            "model": chosen_model,
            "task": task,
            "detected_language": info.language,
            "language_name": SUPPORTED_LANGUAGES.get(info.language, info.language.upper()),
            "language_probability": round(info.language_probability, 3) if info.language_probability else 1.0,
            "duration": round(info.duration, 2) if info.duration else 0.0,
            "full_text": full_transcript,
            "segments": segments
        }

    def transcribe_groq(
        self,
        audio_path: str,
        api_key: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Direct cloud transcription or English translation via Groq Whisper API.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        endpoint = "translations" if task == "translate" else "transcriptions"
        url = f"https://api.groq.com/openai/v1/audio/{endpoint}"
        headers = {"Authorization": f"Bearer {api_key}"}

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            data = {
                "model": "whisper-large-v3",
                "response_format": "verbose_json"
            }
            if language and language != "auto" and task == "transcribe":
                data["language"] = language

            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)

        if response.status_code != 200:
            raise RuntimeError(f"Groq API transcription failed ({response.status_code}): {response.text}")

        res_json = response.json()
        segments = []
        for idx, seg in enumerate(res_json.get("segments", [])):
            segments.append({
                "id": idx,
                "start": round(seg.get("start", 0), 2),
                "end": round(seg.get("end", 0), 2),
                "text": seg.get("text", "").strip()
            })

        det_lang = "en" if task == "translate" else res_json.get("language", "auto")
        return {
            "engine": "groq_api",
            "model": "whisper-large-v3",
            "task": task,
            "detected_language": det_lang,
            "language_name": SUPPORTED_LANGUAGES.get(det_lang, det_lang.upper()),
            "duration": round(res_json.get("duration", 0), 2),
            "full_text": res_json.get("text", "").strip(),
            "segments": segments
        }

    def transcribe_openai(
        self,
        audio_path: str,
        api_key: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Direct cloud transcription or English translation via OpenAI Whisper API.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        endpoint = "translations" if task == "translate" else "transcriptions"
        url = f"https://api.openai.com/v1/audio/{endpoint}"
        headers = {"Authorization": f"Bearer {api_key}"}

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            data = {
                "model": "whisper-1",
                "response_format": "verbose_json"
            }
            if language and language != "auto" and task == "transcribe":
                data["language"] = language

            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI API transcription failed ({response.status_code}): {response.text}")

        res_json = response.json()
        segments = []
        for idx, seg in enumerate(res_json.get("segments", [])):
            segments.append({
                "id": idx,
                "start": round(seg.get("start", 0), 2),
                "end": round(seg.get("end", 0), 2),
                "text": seg.get("text", "").strip()
            })

        det_lang = "en" if task == "translate" else res_json.get("language", "auto")
        return {
            "engine": "openai_api",
            "model": "whisper-1",
            "task": task,
            "detected_language": det_lang,
            "language_name": SUPPORTED_LANGUAGES.get(det_lang, det_lang.upper()),
            "duration": round(res_json.get("duration", 0), 2),
            "full_text": res_json.get("text", "").strip(),
            "segments": segments
        }
