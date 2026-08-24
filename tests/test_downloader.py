import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from downloader import is_valid_instagram_url, normalize_instagram_url

def test_is_valid_instagram_url():
    # Valid reel URLs
    assert is_valid_instagram_url("https://www.instagram.com/reel/C8_abc123/")
    assert is_valid_instagram_url("https://instagram.com/reel/C8_abc123")
    assert is_valid_instagram_url("http://www.instagram.com/p/C9_xyz456/")
    assert is_valid_instagram_url("https://www.instagram.com/tv/C123456789/")
    assert is_valid_instagram_url("https://www.instagram.com/share/reel/ABCxyz/")
    
    # Invalid URLs
    assert not is_valid_instagram_url("https://youtube.com/watch?v=12345")
    assert not is_valid_instagram_url("https://tiktok.com/@user/video/12345")
    assert not is_valid_instagram_url("")
    assert not is_valid_instagram_url(None)

def test_normalize_instagram_url():
    url_with_tracking = "https://www.instagram.com/reel/C8_abc123/?igsh=MWQ1MjE2&utm_source=qr"
    clean_url = normalize_instagram_url(url_with_tracking)
    assert clean_url == "https://www.instagram.com/reel/C8_abc123/"

    url_without_schema = "instagram.com/reel/C8_abc123/"
    normalized = normalize_instagram_url(url_without_schema)
    assert normalized.startswith("https://instagram.com/reel/C8_abc123/")
