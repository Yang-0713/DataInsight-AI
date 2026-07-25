from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Confirm that the API process is ready to receive requests."""
    return {"status": "ok", "service": "DataInsight AI API"}

