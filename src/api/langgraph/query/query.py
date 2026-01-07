from fastapi import APIRouter, Query, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from log.log import logging_config
from pathlib import Path
from datetime import datetime
import os
from utils.uuid import new_uuid
from lg.cs_build import graph
from lg.lg_states import InputState
from langgraph.types import Command
import json

logger = logging_config.setup_logger(service="langgraph_query")
router = APIRouter()
@router.post("/query")
async def langgraph_query(
        query: str = Form(...),
        user_id: int = Form(...),
        conversation_id: Optional[str] = Form(None),
        image: Optional[UploadFile] = File(None)                
):
    """使用LangGraph处理用户查询，支持图片上传"""
    try:
        logger.info(f"Processing LangGraph query for user {user_id} and conversation {conversation_id}")

        # 处理图片上传
        image_path = None
        if image:
            # 创建图片存储目录
            image_dir = Path("uploads/images")
            image_dir.mkdir(parents=True, exist_ok=True)

            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name, ext = os.path.splitext(image.filename) # type: ignore
            new_filename = f"{original_name}_{timestamp}{ext}"
            image_path = image_dir / new_filename

            # 保存图片
            content = await image.read()
            with open(image_path, "wb") as f:
                f.write(content)

            logger.info(f"Saved image {new_filename} for user {user_id}")

        # 使用conversation_id作为thread_id，如果没有提供则创建新的
        thread_id = conversation_id if conversation_id else new_uuid()
        thread_config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
                "image_path": str(image_path) if image_path else None
            }
        }

        # 获取当前线程状态
        state_history = None
        try:
            # 检查是否有现有的会话状态
            if thread_id:
                state_history = graph.get_state(thread_config) # type: ignore
                if state_history:
                    logger.info(f"Found existing conversation state for thread_id: {thread_id}")
        except Exception as e:
            logger.warning(f"Error retrieving state: {e}. Starting with fresh state.")

        # 准备输入状态 - 如果是现有会话，直接传入查询文本
        if state_history and len(state_history) > 0 and len(state_history[-1]) > 0:
            logger.info("Using existing conversation state")

            # 如果有现有会话，使用resume命令继续对话
            async def process_stream():
                async for c, metadata in graph.astream(
                        Command(resume=query),
                        stream_mode="messages",
                        config=thread_config # type: ignore
                ):
                    # 只处理最终展示给用户的内容，跳过中间工具调用和内部状态
                    if c.content and "research_plan" not in metadata.get("tags", []) and not c.additional_kwargs.get( # type: ignore
                            "tool_calls"):
                        # 关键修改：使用json.dumps处理content，确保特殊字符如换行符被正确处理
                        content_json = json.dumps(c.content, ensure_ascii=False) # type: ignore
                        yield f"data: {content_json}\n\n"

                    # 工具调用单独处理，不发送给前端
                    elif c.additional_kwargs.get("tool_calls"): # type: ignore
                        tool_data = c.additional_kwargs.get("tool_calls")[0]["function"].get("arguments") # type: ignore
                        logger.debug(f"Tool call: {tool_data}")

                # 处理中断情况
                state = graph.get_state(thread_config) # type: ignore
                if len(state) > 0 and len(state[-1]) > 0:
                    if len(state[-1][0].interrupts) > 0: # type: ignore
                        interrupt_json = json.dumps({"interruption": True, "conversation_id": thread_id})
                        yield f"data: {interrupt_json}\n\n"
        else:
            # 新会话或找不到现有状态，创建新的输入状态
            logger.info("Creating new conversation state")
            input_state = InputState(messages=query) # type: ignore

            # 流式处理查询
            async def process_stream():
                async for c, metadata in graph.astream(
                        input=input_state,
                        stream_mode="messages",
                        config=thread_config # type: ignore
                ):
                    # 只处理最终展示给用户的内容，跳过中间工具调用和内部状态
                    if c.content and "research_plan" not in metadata.get("tags", []) and not c.additional_kwargs.get( # type: ignore
                            "tool_calls"):
                        # 关键修改：使用json.dumps处理content，确保特殊字符如换行符被正确处理
                        content_json = json.dumps(c.content, ensure_ascii=False) # type: ignore
                        yield f"data: {content_json}\n\n"

                    # 工具调用单独处理，不发送给前端
                    elif c.additional_kwargs.get("tool_calls"): # type: ignore
                        tool_data = c.additional_kwargs.get("tool_calls")[0]["function"].get("arguments") # type: ignore
                        logger.debug(f"Tool call: {tool_data}")

                # 处理中断情况
                state = graph.get_state(thread_config) # type: ignore
                if len(state) > 0 and len(state[-1]) > 0:
                    if len(state[-1][0].interrupts) > 0: # type: ignore
                        interrupt_json = json.dumps({"interruption": True, "conversation_id": thread_id})
                        yield f"data: {interrupt_json}\n\n"

        response = StreamingResponse(
            process_stream(),
            media_type="text/event-stream"
        )

        # 添加会话ID到响应头，方便前端获取
        response.headers["X-Conversation-ID"] = thread_id

        return response

    except Exception as e:
        logger.error(f"LangGraph query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))