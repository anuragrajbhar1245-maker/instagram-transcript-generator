import re
from typing import Dict, Any, List, Optional
import requests

def extractive_summary(text: str, max_sentences: int = 4) -> Dict[str, Any]:
    """
    Offline extractive summarization algorithm based on sentence frequency and key phrases.
    Works 100% offline with zero dependencies and no API key.
    """
    if not text or not text.strip():
        return {
            "summary": "No speech detected in this video.",
            "key_points": []
        }

    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]
    if not sentences:
        sentences = [text.strip()]

    if len(sentences) <= max_sentences:
        return {
            "summary": " ".join(sentences),
            "key_points": [f"• {s}" for s in sentences]
        }

    # Word frequency analysis
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {
        "the", "a", "an", "and", "or", "but", "if", "in", "on", "with", "as", "at", "by", "for",
        "from", "into", "of", "to", "is", "are", "was", "were", "it", "this", "that", "these",
        "those", "i", "you", "he", "she", "we", "they", "my", "your", "his", "her", "our", "their",
        "so", "very", "just", "like", "what", "which", "who", "whom", "have", "has", "had", "do",
        "does", "did", "be", "been", "being", "will", "would", "shall", "should", "can", "could"
    }

    word_freq = {}
    for w in words:
        if w not in stop_words and len(w) > 2:
            word_freq[w] = word_freq.get(w, 0) + 1

    # Score sentences
    sentence_scores = []
    for s in sentences:
        s_words = re.findall(r'\b\w+\b', s.lower())
        score = sum(word_freq.get(w, 0) for w in s_words)
        # Normalize by length to prevent bias towards very long sentences
        normalized_score = score / (len(s_words) + 1)
        sentence_scores.append((normalized_score, s))

    # Pick top sentences while preserving original order
    top_scored = sorted(sentence_scores, key=lambda x: x[0], reverse=True)[:max_sentences]
    top_sentences_set = {s for _, s in top_scored}
    
    ordered_summary_sentences = [s for s in sentences if s in top_sentences_set]

    return {
        "summary": " ".join(ordered_summary_sentences),
        "key_points": [f"• {s}" for s in ordered_summary_sentences]
    }

def ai_summary(text: str, api_key: str, provider: str = "groq") -> Dict[str, Any]:
    """
    Summarization using direct Groq or OpenAI API.
    """
    prompt = (
        "You are an expert audio transcript summarizer. Summarize the following Instagram reel transcript "
        "into a concise 2-sentence executive summary followed by 3-5 bullet points of key takeaways.\n\n"
        f"Transcript:\n{text}"
    )

    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"
    else:
        url = "https://api.openai.com/v1/chat/completions"
        model = "gpt-4o-mini"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You provide clear, direct, and actionable transcript summaries."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"]
            return {
                "summary": content,
                "key_points": [line for line in content.split("\n") if line.strip().startswith(("-", "•", "*"))]
            }
    except Exception:
        pass

    # Fallback to local extractive summary
    return extractive_summary(text)
