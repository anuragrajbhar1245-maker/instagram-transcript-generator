import json
from typing import Dict, Any, List, Optional

def format_seconds_to_timestamp(seconds: float, delimiter: str = ":", millis_delimiter: str = ",") -> str:
    """Converts seconds (e.g. 75.4) to 00:01:15,400 or 00:01:15.400."""
    total_seconds = int(seconds)
    millis = int((seconds - total_seconds) * 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}{delimiter}{minutes:02d}{delimiter}{secs:02d}{millis_delimiter}{millis:03d}"
    else:
        return f"00{delimiter}{minutes:02d}{delimiter}{secs:02d}{millis_delimiter}{millis:03d}"

def format_seconds_short(seconds: float) -> str:
    """Converts seconds (e.g. 75.4) to 01:15 or 1:01:15."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

class TranscriptFormatter:
    @staticmethod
    def to_txt(segments: List[Dict[str, Any]], include_timestamps: bool = True) -> str:
        """Exports transcript as plain text."""
        lines = []
        for s in segments:
            text = s.get("text", "").strip()
            if not text:
                continue
            if include_timestamps:
                start_ts = format_seconds_short(s.get("start", 0))
                lines.append(f"[{start_ts}] {text}")
            else:
                lines.append(text)
        return "\n".join(lines)

    @staticmethod
    def to_srt(segments: List[Dict[str, Any]]) -> str:
        """Exports transcript to standard SubRip (.srt) subtitle format."""
        srt_blocks = []
        for idx, s in enumerate(segments, start=1):
            text = s.get("text", "").strip()
            if not text:
                continue
            start_str = format_seconds_to_timestamp(s.get("start", 0), delimiter=":", millis_delimiter=",")
            end_str = format_seconds_to_timestamp(s.get("end", 0), delimiter=":", millis_delimiter=",")

            block = f"{idx}\n{start_str} --> {end_str}\n{text}\n"
            srt_blocks.append(block)

        return "\n".join(srt_blocks)

    @staticmethod
    def to_vtt(segments: List[Dict[str, Any]]) -> str:
        """Exports transcript to standard WebVTT (.vtt) format."""
        vtt_blocks = ["WEBVTT\n"]
        for idx, s in enumerate(segments, start=1):
            text = s.get("text", "").strip()
            if not text:
                continue
            start_str = format_seconds_to_timestamp(s.get("start", 0), delimiter=":", millis_delimiter=".")
            end_str = format_seconds_to_timestamp(s.get("end", 0), delimiter=":", millis_delimiter=".")

            block = f"{idx}\n{start_str} --> {end_str}\n{text}\n"
            vtt_blocks.append(block)

        return "\n".join(vtt_blocks)

    @staticmethod
    def to_json(result: Dict[str, Any]) -> str:
        """Exports complete transcription and metadata as JSON string."""
        return json.dumps(result, indent=2, ensure_ascii=False)

    @staticmethod
    def to_markdown(result: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, summary: Optional[str] = None) -> str:
        """Exports complete transcript formatted as readable Markdown."""
        meta = metadata or {}
        title = meta.get("title", "Instagram Reel Transcript")
        uploader = meta.get("uploader", "Unknown Creator")
        url = meta.get("webpage_url", "")
        duration = meta.get("duration_formatted", "N/A")
        language = result.get("detected_language", "auto").upper()

        md_parts = [
            f"# {title}",
            "",
            f"- **Creator:** {uploader}",
            f"- **Source:** [{url}]({url})" if url else "",
            f"- **Duration:** {duration}",
            f"- **Language:** {language}",
            "",
            "---",
            ""
        ]

        if summary:
            md_parts.extend([
                "## Summary & Key Takeaways",
                "",
                summary,
                "",
                "---",
                ""
            ])

        md_parts.extend([
            "## Transcript",
            ""
        ])

        segments = result.get("segments", [])
        if segments:
            for s in segments:
                text = s.get("text", "").strip()
                if text:
                    start_ts = format_seconds_short(s.get("start", 0))
                    md_parts.append(f"- **`[{start_ts}]`** {text}")
        else:
            md_parts.append(result.get("full_text", "No transcript available."))

        return "\n".join([p for p in md_parts if p is not None])
