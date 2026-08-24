import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from formatter import TranscriptFormatter, format_seconds_to_timestamp, format_seconds_short

def test_format_seconds():
    assert format_seconds_short(5) == "00:05"
    assert format_seconds_short(65) == "01:05"
    assert format_seconds_short(3665) == "1:01:05"

    assert format_seconds_to_timestamp(5.250, delimiter=":", millis_delimiter=",") == "00:00:05,250"
    assert format_seconds_to_timestamp(75.500, delimiter=":", millis_delimiter=".") == "00:01:15.500"

def test_to_srt():
    segments = [
        {"start": 0.0, "end": 2.5, "text": "Hello world"},
        {"start": 3.0, "end": 5.2, "text": "This is an Instagram reel transcript"}
    ]
    srt = TranscriptFormatter.to_srt(segments)
    assert "1\n00:00:00,000 --> 00:00:02,500\nHello world" in srt
    assert "2\n00:00:03,000 --> 00:00:05,200\nThis is an Instagram reel transcript" in srt

def test_to_vtt():
    segments = [
        {"start": 1.0, "end": 3.5, "text": "Testing WebVTT output"}
    ]
    vtt = TranscriptFormatter.to_vtt(segments)
    assert vtt.startswith("WEBVTT")
    assert "00:00:01.000 --> 00:00:03.500" in vtt
    assert "Testing WebVTT output" in vtt

def test_to_txt():
    segments = [
        {"start": 0.0, "end": 2.0, "text": "First segment"},
        {"start": 2.5, "end": 4.0, "text": "Second segment"}
    ]
    txt_with_ts = TranscriptFormatter.to_txt(segments, include_timestamps=True)
    assert "[00:00] First segment" in txt_with_ts
    assert "[00:02] Second segment" in txt_with_ts

    txt_raw = TranscriptFormatter.to_txt(segments, include_timestamps=False)
    assert txt_raw == "First segment\nSecond segment"

def test_to_markdown():
    res = {
        "detected_language": "en",
        "full_text": "This is full text.",
        "segments": [
            {"start": 0.0, "end": 3.0, "text": "This is segment one."}
        ]
    }
    meta = {
        "title": "Amazing AI Reel",
        "uploader": "tech_guru",
        "webpage_url": "https://instagram.com/reel/123",
        "duration_formatted": "00:30"
    }
    md = TranscriptFormatter.to_markdown(res, metadata=meta, summary="This is a test summary.")
    assert "# Amazing AI Reel" in md
    assert "@tech_guru" in md or "tech_guru" in md
    assert "This is a test summary." in md
    assert "- **`[00:00]`** This is segment one." in md
