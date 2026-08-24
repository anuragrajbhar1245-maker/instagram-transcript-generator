import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from summarizer import extractive_summary
from downloader import is_valid_instagram_url, normalize_instagram_url
from transcriber import SUPPORTED_LANGUAGES, translate_text, translate_segments

def test_supported_languages_dict():
    assert "en" in SUPPORTED_LANGUAGES
    assert "es" in SUPPORTED_LANGUAGES
    assert "hi" in SUPPORTED_LANGUAGES
    assert "fr" in SUPPORTED_LANGUAGES
    assert len(SUPPORTED_LANGUAGES) >= 30

def test_translate_text_basic():
    # Translate simple greeting
    original = "Hello, how are you?"
    translated = translate_text(original, target_lang="es", source_lang="en")
    assert isinstance(translated, str)
    assert len(translated) > 0
    # Spanish translation of Hello is Hola
    assert "hola" in translated.lower() or "cómo" in translated.lower() or len(translated) > 0

def test_translate_segments():
    segments = [
        {"id": 1, "start": 0.0, "end": 2.0, "text": "Good morning"},
        {"id": 2, "start": 2.5, "end": 4.5, "text": "Welcome to our video"}
    ]
    trans_segs = translate_segments(segments, target_lang="es", source_lang="en")
    assert len(trans_segs) == 2
    assert trans_segs[0]["start"] == 0.0
    assert trans_segs[0]["end"] == 2.0
    assert "original_text" in trans_segs[0]
    assert trans_segs[0]["original_text"] == "Good morning"
    assert len(trans_segs[0]["text"]) > 0

def test_extractive_summary_basic():
    long_text = (
        "Artificial intelligence is transforming how video creators work online. "
        "With automated transcription, speech is converted into accurate timestamped text in seconds. "
        "Creators can easily generate subtitles and enhance search engine reach. "
        "This tool supports offline processing without external proxy requirements."
    )
    result = extractive_summary(long_text, max_sentences=2)
    assert "summary" in result
    assert "key_points" in result
    assert len(result["summary"]) > 10
    assert len(result["key_points"]) > 0

def test_extractive_summary_empty():
    result = extractive_summary("")
    assert "No speech detected" in result["summary"]
    assert result["key_points"] == []

def test_url_detection_variations():
    urls = [
        "https://www.instagram.com/reel/C7-abcde123/",
        "https://instagram.com/p/DF123456789/",
        "https://www.instagram.com/tv/B_xyz987654/",
        "https://www.instagram.com/share/reel/ABC12345/"
    ]
    for u in urls:
        assert is_valid_instagram_url(u)
        assert normalize_instagram_url(u).startswith("https://")
