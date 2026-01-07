from typing import Any, Callable, Coroutine, Dict, List

from pydantic import BaseModel, Field

from log.log import logging_config

import json
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
import asyncio

# 获取日志记录器
logger = logging_config.setup_logger(service="cypher_tools")

# 定义GraphRAG查询的输入状态类型
class CypherQueryInputState(BaseModel):
    task: str
    query: str
    steps: List[str]

# 定义GraphRAG查询的输出状态类型
class CypherQueryOutputState(BaseModel):
    task: str
    query: str
    errors: List[str]
    records: Dict[str, Any]
    steps: List[str]

# 定义GraphRAG API包装器

def create_cypher_query_node(
) -> Callable[
    [CypherQueryInputState],
    Coroutine[Any, Any, Dict[str, List[CypherQueryOutputState] | List[str]]],
]:
    """
    创建 Text2Cypher 查询节点，用于LangGraph工作流。

    返回
    -------
    Callable[[CypherQueryInputState], Dict[str, List[CypherQueryOutputState] | List[str]]]
        名为`cypher_query`的LangGraph节点。
    """

    async def cypher_query(
        state: Dict[str, Any],
    ) -> Dict[str, List[CypherQueryOutputState] | List[str]]:
        input_state = {
            "test_state": {  # 包装在 test_state 字段中
            "task": state.get("task", ""),
            "query": state.get("query", ""),
            "steps": [],
        }
    }
        # 构造 MCP 工具所需的输入格式
        url = "http://localhost:6000/mcp"  # 对应 FastMCP 的 host/port 和默认 path /mcp
        async with streamable_http_client(url) as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool("text2cypher", input_state)
                response_data = json.loads(res.content[0].text) # type: ignore
            
                # 获取 ["cyphers"][0]["records"] 部分
                records = response_data["cyphers"][0]

        

        # 封装 单次子任务执行的 输出结果并通过Pydantic模型限定格式
        return {
            "cyphers": [
                CypherQueryOutputState(
                        **{
                            "task": state.get("task", ""),
                            "query": state.get("query", ""),
                            "statement": "",
                            "parameters":"",
                            "errors": records["errors"],
                            "records": {"result": records["records"]} if records["records"] is not None else {"result": []},
                            "steps": ["execute_cypher_query"],
                        }
                    )
                ],
                "steps": ["execute_cypher_query"],
            }
  
    return cypher_query

