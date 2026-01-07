from fastapi import APIRouter

from .v1 import v1_router
from .langgraph import rag_router

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/v1")
api_router.include_router(rag_router, prefix="/rag")

__all__ = ["api_router"]
