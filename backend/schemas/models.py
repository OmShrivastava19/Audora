"""Pydantic schemas for API requests and responses."""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    segment_id: str
    start_sec: float
    end_sec: float
    text: str


class NoteReference(BaseModel):
    segment_id: str
    start_sec: float
    end_sec: float
    quote: str
    confidence: Optional[float] = None


class StructuredNote(BaseModel):
    module: str
    content: str
    references: list[NoteReference] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    confidence_score: float = 0.5
    confidence_label: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    confidence_reason: str = "Derived from available transcript evidence."


class ExamHint(BaseModel):
    hint: str
    module: str
    urgency: Literal["HIGH", "MEDIUM"] = "MEDIUM"
    reason: str = "Auto-detected from generated summary."


class SyllabusCoverage(BaseModel):
    modules: list[dict] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    error: Optional[str] = None


class PracticePayload(BaseModel):
    metadata: dict = Field(default_factory=dict)
    flashcards: list[dict] = Field(default_factory=list)
    quiz: list[dict] = Field(default_factory=list)


class GenerationResult(BaseModel):
    """Response model expected by frontend."""

    id: str
    title: str
    summary: str
    filtered_count: int = 0
    language: str
    notes: list[StructuredNote] = Field(default_factory=list)
    exam_radar: list[ExamHint] = Field(default_factory=list)
    transcript_segments: list[TranscriptSegment] = Field(default_factory=list)
    transcript_text: str = ""
    syllabus_coverage: SyllabusCoverage = Field(default_factory=SyllabusCoverage)
    practice: PracticePayload = Field(default_factory=PracticePayload)
    provider: Literal["groq", "openai"]
    created_at: str
    lecture_filename: str
    audio_notes_url: Optional[str] = None


class LectureHistoryItem(BaseModel):
    """Item in lecture history list."""

    id: str
    title: str
    provider: Literal["groq", "openai"]
    language: str
    lecture_filename: str
    created_at: str
    notes_count: int = 0
    exam_hints_count: int = 0
    course: Optional[str] = None


class UserProfile(BaseModel):
    """User profile response model."""

    uid: str
    email: str
    plan: str
    generationsUsed: int
    createdAt: str
    lastLogin: str


class PublicConfig(BaseModel):
    """Public configuration that can be sent to frontend."""

    FIREBASE_WEB_API_KEY: str
    OAUTH_CLIENT_ID: str
    DEBUG: bool


class ErrorResponse(BaseModel):
    """Standard error response."""

    message: str
    status: int
    detail: Optional[str] = None
