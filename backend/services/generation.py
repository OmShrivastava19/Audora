"""Generation service - core business logic for note generation."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import PyPDF2

try:
    from groq import Groq
except Exception:
    Groq = None

try:
    import openai
except Exception:
    openai = None


LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Arabic": "ar",
    "Urdu": "ur",
    "Hindi": "hi",
    "Portuguese": "pt",
    "Japanese": "ja",
    "Mandarin": "zh",
}

AUDORA_SYSTEM_PROMPT = """
You are Audora, an academic note synthesis assistant.
Given a lecture transcript (and optional syllabus context), produce JSON only with keys:
{
  "title": "...",
  "summary": "...",
  "notes": [{"module": "...", "content": "..."}],
  "exam_radar": [{"hint": "...", "module": "...", "urgency": "HIGH|MEDIUM", "reason": "..."}],
  "filtered_count": 0,
  "language": "en"
}
Rules:
- Keep note content concrete and concise.
- Focus on concepts and likely exam-relevant material.
- Output valid JSON only, no markdown wrappers.
""".strip()


def _safe_json_parse(value: str) -> dict[str, Any]:
    text = (value or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _normalize_segments(raw_segments: Any, transcript_text: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    if isinstance(raw_segments, list):
        for idx, seg in enumerate(raw_segments, start=1):
            # Handle both dicts and objects (some SDKs return objects)
            if isinstance(seg, dict):
                text = str(seg.get("text", "") or "").strip()
                start_sec = float(seg.get("start", seg.get("start_sec", 0.0)) or 0.0)
                end_sec = float(seg.get("end", seg.get("end_sec", start_sec)) or start_sec)
            else:
                text = str(getattr(seg, "text", "") or "").strip()
                start_sec = float(getattr(seg, "start", getattr(seg, "start_sec", 0.0)) or 0.0)
                end_sec = float(getattr(seg, "end", getattr(seg, "end_sec", start_sec)) or start_sec)
            
            if not text:
                continue
                
            segments.append(
                {
                    "segment_id": f"seg_{idx:04d}",
                    "start_sec": round(start_sec, 3),
                    "end_sec": round(end_sec, 3),
                    "text": text,
                }
            )
    if not segments and transcript_text.strip():
        segments.append(
            {
                "segment_id": "seg_0001",
                "start_sec": 0.0,
                "end_sec": 0.0,
                "text": transcript_text.strip(),
            }
        )
    return segments


def _extract_syllabus_text(syllabus_file_path: Optional[str]) -> str:
    if not syllabus_file_path:
        return ""
    path = Path(syllabus_file_path)
    if not path.exists():
        return ""

    if path.suffix.lower() == ".pdf":
        text_chunks: list[str] = []
        try:
            with path.open("rb") as handle:
                reader = PyPDF2.PdfReader(handle)
                for page in reader.pages:
                    try:
                        text_chunks.append((page.extract_text() or "").strip())
                    except Exception:
                        continue
            return "\n".join(chunk for chunk in text_chunks if chunk).strip()
        except Exception:
            pass # Fall back to reading as text below if PDF parsing fails

    return path.read_text(encoding="utf-8", errors="ignore").strip()


def _first_reference_for_note(segment: dict[str, Any]) -> dict[str, Any]:
    return {
        "segment_id": segment.get("segment_id", "seg_0001"),
        "start_sec": float(segment.get("start_sec", 0.0)),
        "end_sec": float(segment.get("end_sec", 0.0)),
        "quote": str(segment.get("text", ""))[:220],
        "confidence": 0.6,
    }


def _build_practice(notes: list[dict[str, Any]], language_label: str) -> dict[str, Any]:
    flashcards = []
    quiz = []
    for idx, note in enumerate(notes[:8], start=1):
        module = str(note.get("module", f"Module {idx}"))
        content = str(note.get("content", "")).strip()
        if not content:
            continue

        flashcards.append(
            {
                "question": f"Key idea in {module}?",
                "answer": content[:240],
                "module": module,
                "difficulty": "medium",
            }
        )
        quiz.append(
            {
                "id": f"q_{idx}",
                "type": "short_answer",
                "module": module,
                "difficulty": "medium",
                "question": f"Explain one core concept from {module}.",
                "answer": content[:180],
                "explanation": "Derived from generated notes.",
            }
        )

    return {
        "metadata": {
            "title": "Practice Set",
            "language": language_label,
            "generated_from_modules": [str(n.get("module", "General")) for n in notes[:8]],
        },
        "flashcards": flashcards,
        "quiz": quiz,
    }


class GenerationService:
    """Service for handling lecture note generation."""

    def __init__(self, groq_key: Optional[str] = None, openai_key: Optional[str] = None):
        self.groq_key = groq_key
        self.openai_key = openai_key

    def _transcribe(self, lecture_file_path: str, provider: str, api_key: str) -> tuple[str, list[dict[str, Any]]]:
        lecture_path_obj = Path(lecture_file_path)
        lecture_name = lecture_path_obj.name

        if provider == "groq":
            if Groq is None:
                raise RuntimeError("groq package is not installed")
            client = Groq(api_key=api_key)
            with open(lecture_file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=(lecture_name, audio_file),
                    response_format="verbose_json",
                )
            
            # Convert response to dict if it has model_dump or dict method
            if hasattr(response, "model_dump"):
                payload = response.model_dump()
            elif hasattr(response, "dict"):
                payload = response.dict()
            else:
                payload = response
                
            transcript_text = str(payload.get("text", "") if isinstance(payload, dict) else getattr(payload, "text", "")).strip()
            raw_segments = payload.get("segments", []) if isinstance(payload, dict) else getattr(payload, "segments", [])
            segments = _normalize_segments(raw_segments, transcript_text)
            return transcript_text, segments

        if provider == "openai":
            if openai is None:
                raise RuntimeError("openai package is not installed")
            client = openai.OpenAI(api_key=api_key)
            with open(lecture_file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
            
            if hasattr(response, "model_dump"):
                payload = response.model_dump()
            elif hasattr(response, "dict"):
                payload = response.dict()
            else:
                payload = response
                
            transcript_text = str(payload.get("text", "") if isinstance(payload, dict) else getattr(payload, "text", "")).strip()
            raw_segments = payload.get("segments", []) if isinstance(payload, dict) else getattr(payload, "segments", [])
            segments = _normalize_segments(raw_segments, transcript_text)
            return transcript_text, segments

        raise ValueError(f"Unsupported provider: {provider}")

    def _generate_structured_payload(
        self,
        provider: str,
        api_key: str,
        transcript_text: str,
        syllabus_text: str,
        language_label: str,
    ) -> dict[str, Any]:
        user_prompt = (
            f"Target language: {language_label}\n"
            f"Syllabus context:\n{syllabus_text[:8000] or '[none]'}\n\n"
            f"Lecture transcript:\n{transcript_text[:18000]}"
        )

        if provider == "groq":
            if Groq is None:
                raise RuntimeError("groq package is not installed")
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": AUDORA_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = completion.choices[0].message.content or "{}"
            return _safe_json_parse(content)

        if provider == "openai":
            if openai is None:
                raise RuntimeError("openai package is not installed")
            client = openai.OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": AUDORA_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = completion.choices[0].message.content or "{}"
            return _safe_json_parse(content)

        raise ValueError(f"Unsupported provider: {provider}")

    async def generate_notes(
        self,
        lecture_file_path: str,
        syllabus_file_path: Optional[str] = None,
        provider: str = "groq",
        language: str = "English",
        api_key: Optional[str] = None,
    ) -> dict[str, Any]:
        language_iso = LANGUAGES.get(language, "en")
        effective_key = (api_key or (self.groq_key if provider == "groq" else self.openai_key) or "").strip()
        if not effective_key:
            raise ValueError(f"Missing API key for provider: {provider}")

        transcript_text, transcript_segments = self._transcribe(lecture_file_path, provider, effective_key)
        if not transcript_text:
            raise RuntimeError("Transcription produced no text.")

        syllabus_text = _extract_syllabus_text(syllabus_file_path)
        llm_payload = self._generate_structured_payload(
            provider=provider,
            api_key=effective_key,
            transcript_text=transcript_text,
            syllabus_text=syllabus_text,
            language_label=language,
        )

        notes_in = llm_payload.get("notes", []) if isinstance(llm_payload.get("notes", []), list) else []
        exam_in = llm_payload.get("exam_radar", []) if isinstance(llm_payload.get("exam_radar", []), list) else []
        first_seg = transcript_segments[0] if transcript_segments else {
            "segment_id": "seg_0001",
            "start_sec": 0.0,
            "end_sec": 0.0,
            "text": transcript_text[:220],
        }

        notes = []
        for idx, raw in enumerate(notes_in, start=1):
            if not isinstance(raw, dict):
                continue
            module = str(raw.get("module", f"Module {idx}")).strip() or f"Module {idx}"
            content = str(raw.get("content", "")).strip()
            if not content:
                continue
            ref = _first_reference_for_note(first_seg)
            notes.append(
                {
                    "module": module,
                    "content": content,
                    "references": [ref],
                    "source_refs": [f"{ref['start_sec']:.0f}s-{ref['end_sec']:.0f}s ({ref['segment_id']})"],
                    "confidence_score": 0.6,
                    "confidence_label": "MEDIUM",
                    "confidence_reason": "Generated from transcript with baseline reference mapping.",
                }
            )

        if not notes:
            notes = [
                {
                    "module": "General",
                    "content": transcript_text[:1200],
                    "references": [_first_reference_for_note(first_seg)],
                    "source_refs": ["0s-0s (seg_0001)"],
                    "confidence_score": 0.5,
                    "confidence_label": "LOW",
                    "confidence_reason": "Fallback summary because structured extraction was empty.",
                }
            ]

        exam_radar = []
        for item in exam_in[:8]:
            if not isinstance(item, dict):
                continue
            exam_radar.append(
                {
                    "hint": str(item.get("hint", "Important concept")),
                    "module": str(item.get("module", "General")),
                    "urgency": "HIGH" if str(item.get("urgency", "MEDIUM")).upper() == "HIGH" else "MEDIUM",
                    "reason": str(item.get("reason", "Potential assessment relevance.")),
                }
            )

        title = str(llm_payload.get("title", "Lecture Notes")).strip() or "Lecture Notes"
        summary = str(llm_payload.get("summary", transcript_text[:500])).strip() or transcript_text[:500]

        result = {
            "id": f"gen_{uuid.uuid4().hex[:12]}",
            "title": title,
            "summary": summary,
            "filtered_count": int(llm_payload.get("filtered_count", 0) or 0),
            "language": language,
            "notes": notes,
            "exam_radar": exam_radar,
            "transcript_segments": transcript_segments,
            "transcript_text": transcript_text,
            "syllabus_coverage": {
                "modules": [],
                "summary": {
                    "covered": 0,
                    "partial": 0,
                    "missing": 0,
                    "total": 0,
                },
                "error": None if syllabus_text else "No syllabus provided.",
            },
            "practice": _build_practice(notes, language),
            "provider": provider,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lecture_filename": Path(lecture_file_path).name,
            "audio_notes_url": None,
        }
        return result
