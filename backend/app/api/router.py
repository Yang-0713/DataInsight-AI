from fastapi import APIRouter

from app.api.routes.analysis import router as analysis_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dataset import router as dataset_router
from app.api.routes.health import router as health_router
from app.api.routes.machine_learning import router as machine_learning_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dataset_router)
api_router.include_router(analysis_router)
api_router.include_router(machine_learning_router)


@api_router.get("", tags=["root"])
def api_root() -> dict[str, str]:
    return {
        "name": "DataInsight AI API",
        "version": "0.5.0",
        "docs": "/docs",
    }
