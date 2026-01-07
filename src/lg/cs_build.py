from lg.lg_prompts import (
    ROUTER_SYSTEM_PROMPT,
    GET_ADDITIONAL_SYSTEM_PROMPT,
    GENERAL_QUERY_SYSTEM_PROMPT,
    GET_IMAGE_SYSTEM_PROMPT,
    GUARDRAILS_SYSTEM_PROMPT,
    RAGSEARCH_SYSTEM_PROMPT,
    CHECK_HALLUCINATIONS,
    GENERATE_QUERIES_SYSTEM_PROMPT
)
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
# from settings.lg_config import settings, ServiceType
from langchain.chat_models import init_chat_model
# from log.log import logging_config
from typing import cast, Literal, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from lg.lg_states import AgentState, InputState, Router, GradeHallucinations
from lg.sub_lg_graphrag.agentic_rag.retrivers.northwind_retriever import NorthwindCypherRetriever
# from lg.sub_lg_graphrag.agentic_rag.components.planner.node import create_planner_node
from lg.sub_lg_graphrag.agentic_rag.workflow.multi_agent import multi_tool_workflow
# from repositories.kg_neo4j_conn import get_neo4j_graph
from pydantic import BaseModel
from typing import Dict, List
from langchain_core.messages import AIMessage
from langchain_core.runnables.base import Runnable
from langchain.agents import create_agent
# from lg.sub_lg_graphrag.agentic_rag.components.utils.utils import retrieve_and_parse_schema_from_graph_for_prompts
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents.middleware import before_model, wrap_model_call, ModelRequest, ModelResponse
import base64
import os
import aiohttp
import asyncio
import json
import time
from pathlib import Path
from settings.lg_config import settings, ServiceType
from typing import Literal,Callable,TypedDict
from pydantic import BaseModel, Field
from lg.lg_middlemares.dynamic_model import dynamic_model_router
from lg.lg_middlemares.safety_guardrail import SafetyGuardrail
from lg.lg_middlemares.dynamic_system_prompt import generate_sys_prompt

#可以配置LangSmith

class AdditionalGuardrailsOutput(BaseModel):
    """
    格式化输出，用于判断用户的问题是否与图谱内容相关
    """
    decision: Literal["end", "continue"] = Field(
        description="Decision on whether the question is related to the graph contents."
    )


# # 构建日志记录器
# logger = logging_config.setup_logger(service="cs_builder")

llm = init_chat_model(
            model="deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
intent_recognition_middlewares = [dynamic_model_router]
class Context(TypedDict):
    user_role: str  # 用户角色
# 意图识别模块
intent_recognition_agent = create_agent(
    model=llm,
    system_prompt=ROUTER_SYSTEM_PROMPT,
    # tools=tools,
    middleware=intent_recognition_middlewares,  # type: ignore
    debug=False,  # 关闭调试模式 
    checkpointer=InMemorySaver(),  # 内存检查点，用于存储状态
    context_schema=Context,  # 上下文模式，定义了状态的结构
    response_format=Router,  # 结构化输出格式
)

async def intent_recognition(state: AgentState):
    response = await intent_recognition_agent.ainvoke(
        {"messages": state.messages}, # type: ignore
        runtime_context={"user_role": "regular"}  # 示例角色，可根据实际情况调整
    )
    return {"router": response['structured_response']}
def route_query(
        state: AgentState,
) -> Literal[
    "respond_to_general_query", "get_additional", "create_research_plan"]:
    """根据查询分类确定下一步操作。

    Args:
        state (AgentState): 当前代理状态，包括路由器的分类。

    Returns:
        Literal["respond_to_general_query", "get_additional", "create_research_plan", "create_image_query", "create_file_query"]: 下一步操作。
    """
    print(f"Route to: {state.router['logic']} - {state.router['type']}")
    _type = state.router["type"]
    # TODO: 检查配置中是否有图片路径，如果有，优先处理为图片查询
    # if hasattr(state, "config") and state.config and state.config.get("configurable", {}).get("image_path"): # type: ignore
    #     # logger.info("检测到图片路径，转为图片查询处理")
    #     return "create_image_query"

    if _type == "general-query":
        return "respond_to_general_query"
    elif _type == "additional-query":
        return "get_additional"
    elif _type == "graphrag-query":
        return "create_research_plan"
    # elif _type == "image-query":
    #     return "create_image_query"
    # elif _type == "file-query":
    #     return "create_file_query"
    else:
        raise ValueError(f"Unknown router type {_type}")

async def respond_to_general_query(
        state: AgentState, *, config: RunnableConfig
) -> Dict[str, List[BaseMessage]]:
    """生成对一般查询的响应，完全基于大模型，不会触发任何外部服务的调用，包括自定义工具、知识库查询等。

    当路由器将查询分类为一般问题时，将调用此节点。

    Args:
        state (AgentState): 当前代理状态，包括对话历史和路由逻辑。
        config (RunnableConfig): 用于配置响应生成的模型。

    Returns:
        Dict[str, List[BaseMessage]]: 包含'messages'键的字典，其中包含生成的响应。
    """
    # logger.info("-----generate general-query response-----")

    # 使用大模型生成回复
    model = init_chat_model(
        model="deepseek-chat",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )

    system_prompt = GENERAL_QUERY_SYSTEM_PROMPT.format(
        logic=state.router["logic"]
    )

    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}


get_additional_middlewares = [SafetyGuardrail(), generate_sys_prompt]
get_additional_agent = create_agent(
    model=llm,
    # tools=tools,
    middleware=get_additional_middlewares,  # type: ignore
    debug=False,  # 关闭调试模式
    checkpointer=InMemorySaver(),  # 内存检查点，用于存储状态
    # context_schema=Context,  # 上下文模式，定义了状态的结构
    )
async def get_additional(state: AgentState) -> Dict[str, List[BaseMessage]]:
    """生成一个响应，要求用户提供更多信息。

    当路由确定需要从用户那里获取更多信息时，将调用此函数。

    Args:
        state (AgentState): 当前代理状态，包括对话历史和路由逻辑。

    Returns:
        Dict[str, List[BaseMessage]]: 包含'messages'键的字典，其中包含生成的响应。
    """
    response = await get_additional_agent.ainvoke(
        {"messages": state.messages}, # type: ignore
        context={"logic": state.router["logic"]}  # type: ignore
    )

    return response
    

async def create_research_plan(
        state: AgentState, *, config: RunnableConfig
) -> Dict[str, List[str] | str]:

    # last_message = state.messages[-1].content if state.messages else ""
    # print(f"-----generate research plan for: {last_message}-----")
    last_message = HumanMessage(content=state.router["logic"])
    input_state = {
        "question": last_message,
        "data": [],
        "history": []
    }
    response = await multi_tool_workflow.ainvoke(input_state)
    print(response)
    return {"messages": [AIMessage(content=response["answer"])]} # type: ignore

builder = StateGraph(AgentState, input_schema=InputState)
# 添加节点
builder.add_node(intent_recognition) # type: ignore
builder.add_node(respond_to_general_query) # type: ignore
builder.add_node(get_additional) # type: ignore
builder.add_node(create_research_plan) # type: ignore

builder.add_edge(START, "intent_recognition")
builder.add_conditional_edges("intent_recognition", route_query)

# graph = builder.compile(checkpointer=InMemorySaver())
graph = builder.compile() #langstudio
# 我买的篮球东西什么时候到？
# 你们家有那些智能电饭煲推荐？
# 智能电饭煲有那些使用注意？
if __name__ == "__main__":
    async def main():
        config = {"configurable": {"thread_id": "test-thread-final"}}
        input_state = InputState(messages="为什么我加入购物车后，价格变了？") # type: ignore
        
        # 使用异步调用
        response = await graph.ainvoke(
            input_state,
            runtime_context={"user_role": "regular"},
            config=config, # type: ignore
        )
        print(f"最终响应: {response}")

    # 运行异步函数
    if __name__ == "__main__":
        asyncio.run(main())