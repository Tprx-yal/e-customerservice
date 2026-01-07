from fastapi import APIRouter

from .query import langgraph_router

rag_router = APIRouter()
rag_router.include_router(langgraph_router, prefix="/langgraph")

__all__ = ["rag_router"]