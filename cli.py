#!/usr/bin/env python3
import sys
import argparse
import os
from pathlib import Path

from downloader import InstagramDownloader, is_valid_instagram_url
from transcriber import Transcriber
from formatter import TranscriptFormatter
from summarizer import extractive_summary, ai_summary
from config import DEFAULT_WHISPER_MODEL

def main():
    parser = argparse.ArgumentParser(
        description="Instagram Transcript Generator CLI - Transcribe Instagram Reels and Posts from link"
    )
    parser.add_argument("url", help="Instagram Reel or Post URL (e.g. https://www.instagram.com/reel/...)")
    parser.add_argument(
        "--model",
        default=DEFAULT_WHISPER_MODEL,
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size for local transcription (default: base)"
    )
    parser.add_argument(
        "--format",
        default="txt",
        choices=["txt", "srt", "vtt", "json", "md", "all"],
        help="Output transcript format (default: txt)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: prints to stdout or saves next to audio)"
    )
    parser.add_argument(
        "--language", "-l",
        default="auto",
        help="Language code (e.g., 'en', 'es', 'hi') or 'auto' for auto-detection"
    )
    parser.add_argument(
        "--groq-key",
        help="Groq API key for cloud transcription and AI summarization"
    )
    parser.add_argument(
        "--openai-key",
        help="OpenAI API key for cloud transcription and AI summarization"
    )

    args = parser.parse_args()

    url = args.url.strip()
    if not is_valid_instagram_url(url):
        print(f"Error: '{url}' does not appear to be a valid Instagram URL.", file=sys.stderr)
        sys.exit(1)

    print(f"\n[1/3] Downloading Instagram media from {url}...")
    downloader = InstagramDownloader()
    try:
        audio_path, metadata = downloader.download_audio(url)
        print(f" -> Found: '{metadata.get('title', 'Reel')[:60]}...' by @{metadata.get('uploader', 'Creator')}")
        print(f" -> Duration: {metadata.get('duration_formatted', 'N/A')}")
        print(f" -> Extracted audio: {audio_path}")
    except Exception as e:
        print(f"Error downloading Instagram audio: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n[2/3] Transcribing audio with Whisper ({args.model})...")
    transcriber = Transcriber(default_model=args.model)
    try:
        if args.groq_key:
            trans_result = transcriber.transcribe_groq(audio_path, api_key=args.groq_key, language=args.language)
        elif args.openai_key:
            trans_result = transcriber.transcribe_openai(audio_path, api_key=args.openai_key, language=args.language)
        else:
            trans_result = transcriber.transcribe_local(audio_path, model_size=args.model, language=args.language)

        print(f" -> Detected language: {trans_result.get('detected_language', 'unknown').upper()}")
        print(f" -> Generated {len(trans_result.get('segments', []))} transcript segments.")
    except Exception as e:
        print(f"Error during transcription: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n[3/3] Formatting output...")
    segments = trans_result.get("segments", [])
    summary_data = extractive_summary(trans_result.get("full_text", ""))

    formats = {
        "txt": TranscriptFormatter.to_txt(segments, include_timestamps=True),
        "srt": TranscriptFormatter.to_srt(segments),
        "vtt": TranscriptFormatter.to_vtt(segments),
        "json": TranscriptFormatter.to_json(trans_result),
        "md": TranscriptFormatter.to_markdown(trans_result, metadata=metadata, summary=summary_data.get("summary")),
    }

    if args.format == "all":
        base_name = args.output or f"transcript_{metadata['task_id'][:8]}"
        for fmt, content in formats.items():
            out_file = f"{base_name}.{fmt}"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f" -> Saved {fmt.upper()} to {out_file}")
    elif args.output:
        content = formats.get(args.format, formats["txt"])
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f" -> Transcript successfully saved to: {args.output}")
    else:
        print("\n================ TRANSCRIPT ================")
        print(formats.get(args.format, formats["txt"]))
        print("============================================\n")
        if summary_data.get("summary"):
            print("Summary:")
            print(summary_data["summary"])
            print()

if __name__ == "__main__":
    main()
