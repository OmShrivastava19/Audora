"""API routes for note generation."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
import tempfile
import traceback
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from backend.core.config import get_settings
from backend.schemas.models import GenerationResult
from backend.services.generation import GenerationService
from backend.services.auth import get_current_user_id
from backend.services.storage import ResultStore

router = APIRouter(prefix="/api", tags=["generation"])

STORE = ResultStore(Path(__file__).resolve().parents[3] / "data" / "results.json")


def get_generation_service() -> GenerationService:
    """Dependency to get generation service."""
    settings = get_settings()
    return GenerationService(
        groq_key=settings.GROQ_API_KEY,
        openai_key=settings.OPENAI_API_KEY,
    )


@router.post("/generate", response_model=GenerationResult)
async def generate_notes(
    lecture: UploadFile = File(...),
    syllabus: Optional[UploadFile] = File(None),
    provider: str = Form("groq"),
    language: str = Form("English"),
    apiKey: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id),
    service: GenerationService = Depends(get_generation_service),
) -> GenerationResult:
    """
    Generate structured notes from a lecture audio file.

    - **lecture**: Audio file (mp3, mp4, wav, etc.)
    - **syllabus**: Optional syllabus PDF for context
    - **provider**: LLM provider ('groq' or 'openai')
    - **language**: Output language (e.g., 'en', 'es', 'fr')
    - **apiKey**: Optional override API key for the provider
    """
    lecture_path: Optional[str] = None
    syllabus_path: Optional[str] = None
    try:
        # Validate file types
        lecture_bytes = await lecture.read()
        if not lecture_bytes:
            raise HTTPException(status_code=400, detail="Lecture file is empty")

        if syllabus:
            syllabus_bytes = await syllabus.read()
            if syllabus_bytes:
                ext = Path(syllabus.filename).suffix.lower() if syllabus.filename else ".txt"
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                    f.write(syllabus_bytes)
                    syllabus_path = f.name

        # Save lecture file temporarily, preserving the original extension
        # so that the Groq/OpenAI API can detect the audio format correctly
        lecture_ext = Path(lecture.filename).suffix.lower() if lecture.filename else ".mp3"
        if not lecture_ext:
            lecture_ext = ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=lecture_ext) as f:
            f.write(lecture_bytes)
            lecture_path = f.name

        # Use provided API key or fall back to configured key
        effective_key = apiKey or (
            get_settings().GROQ_API_KEY
            if provider == "groq"
            else get_settings().OPENAI_API_KEY
        )

        if not effective_key:
            raise HTTPException(
                status_code=400,
                detail=f"No API key available for provider '{provider}'",
            )

        # Generate notes
        result_payload = await service.generate_notes(
            lecture_file_path=lecture_path,
            syllabus_file_path=syllabus_path,
            provider=provider,
            language=language,
            api_key=effective_key,
        )

        STORE.save_result(user_id=user_id, result=result_payload)
        return GenerationResult(**result_payload)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Generation endpoint error:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Generation failed: {str(e)}"
        )
    finally:
        for temp_path in [lecture_path, syllabus_path]:
            if temp_path and Path(temp_path).exists():
                try:
                    Path(temp_path).unlink()
                except Exception:
                    pass
