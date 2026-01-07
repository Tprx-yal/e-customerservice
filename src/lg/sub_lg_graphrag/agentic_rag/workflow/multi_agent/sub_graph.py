from typing import Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
# 导入输入输出状态定义
from lg.sub_lg_graphrag.agentic_rag.components.state import (
    InputState,
    OutputState,
    OverallState,
)
# 导入guardrails逻辑
from lg.sub_lg_graphrag.agentic_rag.components.guardrails.node import create_guardrails_node
# 导入分解节点
from lg.sub_lg_graphrag.agentic_rag.components.planner import create_planner_node
# 导入工具选择节点
from lg.sub_lg_graphrag.agentic_rag.components.tool_selection import create_tool_selection_node
# 导入 text2cypher 节点
from lg.sub_lg_graphrag.agentic_rag.components.cypher_tools import create_cypher_query_node
# 导入Cypher示例检索器基类
from lg.sub_lg_graphrag.agentic_rag.retrivers.base import BaseCypherExampleRetriever
# 导入预定义Cypher节点
from lg.sub_lg_graphrag.agentic_rag.components.predefined_cypher import create_predefined_cypher_node
# 导入自定义工具函数节点
from lg.sub_lg_graphrag.agentic_rag.components.customer_tools import create_graphrag_query_node

# from ...components.errors import create_error_tool_selection_node
from lg.sub_lg_graphrag.agentic_rag.components.final_answer import create_final_answer_node

from lg.sub_lg_graphrag.agentic_rag.components.summarize import create_summarization_node

from lg.sub_lg_graphrag.agentic_rag.workflow.multi_agent.edges import (
    guardrails_conditional_edge,
    map_reduce_planner_to_tool_selection,
)
from settings.lg_config import settings, ServiceType
from dataclasses import dataclass, field
from lg.lg_test.kg_neo4j_conn_test import get_neo4j_graph
from lg.sub_lg_graphrag.kg_tools_list import cypher_query, predefined_cypher, microsoft_graphrag_query
from lg.sub_lg_graphrag.agentic_rag.components.predefined_cypher.cypher_dict import predefined_cypher_dict
from lg.sub_lg_graphrag.agentic_rag.retrivers.northwind_retriever import NorthwindCypherRetriever
class MultiToolWorkflow:
            
    def __init__(self):
        if settings.AGENT_SERVICE == ServiceType.DEEPSEEK:
            self.llm = init_chat_model(
                model="deepseek-chat",
                api_key='sk-c6a046d027964a88b8a071758f3dfca2',
                base_url="https://api.deepseek.com",
            )
        else:
            raise ValueError(f"Unsupported AGENT_SERVICE: {settings.AGENT_SERVICE}")
        self.graph = get_neo4j_graph()
        self.tool_schemas: List[type[BaseModel]] = [cypher_query, predefined_cypher, microsoft_graphrag_query]
        self.cypher_retriever = NorthwindCypherRetriever()
        self.scope_description = """
            个人电商经营范围：智能家居产品，包括但不限于：
            - 智能照明（灯泡、灯带、开关）
            - 智能安防（摄像头、门锁、传感器）
            - 智能控制（温控器、遥控器、集线器）
            - 智能音箱（语音助手、音响）
            - 智能厨电（电饭煲、冰箱、洗碗机）
            - 智能清洁（扫地机器人、洗衣机）
            
            不包含：服装、鞋类、体育用品、化妆品、食品等非智能家居产品。
            """
        self.llm_cypher_validation = True
        self.default_to_text2cypher = True
    def create_workflow(self) -> CompiledStateGraph:
        """
        Create a multi tool Agent workflow using LangGraph.
        This workflow allows an agent to select from various tools to complete each identified task.
        """
        # 1. 如果通过guardrails，则会针对用户的问题进行任务分解
        planner = create_planner_node(llm=self.llm)

        # 2. 创建cypher_query节点，用来根据用户的问题生成Cypher查询语句
        cypher_query = create_cypher_query_node()

        predefined_cypher = create_predefined_cypher_node(
            graph=self.graph, predefined_cypher_dict=predefined_cypher_dict
        )

        customer_tools = create_graphrag_query_node()

        # 工具选择节点，根据用户的问题选择合适的工具
        tool_selection = create_tool_selection_node(
            llm=self.llm,
            tool_schemas=self.tool_schemas,
            default_to_text2cypher=self.default_to_text2cypher,
        )
        summarize = create_summarization_node(llm=self.llm)

        final_answer = create_final_answer_node()

        # 创建状态图
        main_graph_builder = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)

        main_graph_builder.add_node(planner) # type: ignore
        main_graph_builder.add_node("cypher_query", cypher_query) # type: ignore
        main_graph_builder.add_node(predefined_cypher) # type: ignore
        main_graph_builder.add_node("customer_tools", customer_tools) # type: ignore
        main_graph_builder.add_node(summarize) # type: ignore
        main_graph_builder.add_node(tool_selection) # type: ignore
        main_graph_builder.add_node(final_answer) # type: ignore

        # 添加边
        main_graph_builder.add_edge(START, "planner")
        main_graph_builder.add_conditional_edges(
            "planner",
            map_reduce_planner_to_tool_selection,  # type: ignore[arg-type, unused-ignore]
            ["tool_selection"],
        )
        main_graph_builder.add_edge("cypher_query", "summarize")
        main_graph_builder.add_edge("predefined_cypher", "summarize")
        main_graph_builder.add_edge("customer_tools", "summarize")
        
        main_graph_builder.add_edge("summarize", "final_answer")

        main_graph_builder.add_edge("final_answer", END)
        print("Multi-tool workflow created.")
        return main_graph_builder.compile()
    
multi_tool_workflow = MultiToolWorkflow().create_workflow()

# # 你们家篮球怎么卖的？
# # 你们家有哪些智能智能电饭煲？那些智能台灯？
# # 你们家有哪些智能智能电饭煲？你们家有哪些智能智能电饭煲？
# if __name__ == "__main__":
#     import asyncio
#     async def run_workflow():
#         input_state = {
#             "question": "智能电饭煲多少钱？",
#             "data": [],
#             "history": []
#         }
#         result = await multi_tool_workflow.ainvoke(input_state)
#         return result
#     result = asyncio.run(run_workflow())
#     print(result)