"""API routes for history and results."""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends

from backend.schemas.models import LectureHistoryItem, GenerationResult
from backend.services.auth import get_current_user_id
from backend.services.storage import ResultStore

router = APIRouter(prefix="/api", tags=["history"])

STORE = ResultStore(Path(__file__).resolve().parents[3] / "data" / "results.json")


@router.get("/history", response_model=list[LectureHistoryItem])
async def get_lecture_history(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
) -> list[LectureHistoryItem]:
    """
    Get user's lecture generation history.

    - **limit**: Maximum number of items to return
    - **offset**: Pagination offset
    """
    rows = STORE.list_history(user_id=user_id, limit=limit, offset=offset)
    payload: list[LectureHistoryItem] = []
    for row in rows:
        payload.append(
            LectureHistoryItem(
                id=row.get("id", ""),
                title=row.get("title", "Lecture Notes"),
                provider=row.get("provider", "groq"),
                language=row.get("language", "English"),
                lecture_filename=row.get("lecture_filename", "lecture.mp3"),
                created_at=row.get("created_at", ""),
                notes_count=len(row.get("notes", [])),
                exam_hints_count=len(row.get("exam_radar", [])),
                course=None,
            )
        )
    return payload


@router.get("/results/{result_id}", response_model=GenerationResult)
async def get_result(result_id: str, user_id: str = Depends(get_current_user_id)) -> GenerationResult:
    """
    Get a specific generation result by ID.

    - **result_id**: The generation result ID
    """
    row = STORE.get_result(user_id=user_id, result_id=result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    return GenerationResult(**row)
