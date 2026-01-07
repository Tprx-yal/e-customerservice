from fastapi import APIRouter

from .query import router

langgraph_router = APIRouter()
langgraph_router.include_router(router, tags=["LangGraph查询模块"])

__all__ = ["langgraph_router"]
