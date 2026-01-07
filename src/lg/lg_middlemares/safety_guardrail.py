from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents.middleware import AgentMiddleware, hook_config
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional
from lg.lg_test.kg_neo4j_conn_test import get_neo4j_graph
from lg.lg_states import AgentState
from lg.lg_prompts import GUARDRAILS_SYSTEM_PROMPT
from lg.sub_lg_graphrag.agentic_rag.components.utils.utils import retrieve_and_parse_schema_from_graph_for_prompts


class AdditionalGuardrailsOutput(BaseModel):
    """
    格式化输出，用于判断用户的问题是否与图谱内容相关
    """
    decision: Literal["end", "continue"] = Field(
        description="Decision on whether the question is related to the graph contents."
    )

class SafetyGuardrail(AgentMiddleware):
    """
    [阶段 1: before_agent & before_model] RBAC 权限控制中间件
    在执行任何操作前验证用户权限
    """

    def __init__(self):
        super().__init__()
        # 定义电商经营范围
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
        self.model = init_chat_model(
            model="deepseek-chat",
            api_key='sk-c6a046d027964a88b8a071758f3dfca2',
            base_url="https://api.deepseek.com",
        ).with_structured_output(AdditionalGuardrailsOutput)
        self.prompt = self._get_prompt()

    def _get_prompt(self) -> ChatPromptTemplate:
        try:
            neo4j_graph = get_neo4j_graph()
        except Exception as e:
            # logger.error(f"failed to get Neo4j graph database connection: {e}")
            raise e

        scope_context = (
            f"参考此范围描述来决策:\n{self.scope_description}"
            if self.scope_description is not None
            else ""
        )

        # 动态从 Neo4j 图表中获取图表结构
        graph_context = (
            f"\n参考图表结构来回答:\n{retrieve_and_parse_schema_from_graph_for_prompts(neo4j_graph)}" # type: ignore
            if neo4j_graph is not None # type: ignore
            else ""
        )
        # print(graph_context)
        # exit()
        message = scope_context + graph_context + "\nQuestion: {question}"
        full_system_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    GUARDRAILS_SYSTEM_PROMPT,
                ),
                (
                    "human",
                    (message),
                ),
            ]
        )
        return full_system_prompt

    @hook_config(can_jump_to=["end"])  # 允许在 before_agent 阶段跳转到 end
    async def abefore_agent(self, state: Dict[str, Any], runtime) -> Optional[Dict[str, Any]]: # type: ignore
        # 构建格式化输出的 Chain， 如果匹配，返回 continue，否则返回 end
        
        guardrails_chain = self.prompt | self.model
        guardrails_output = await guardrails_chain.ainvoke(
            {"question": state["messages"][-1].content if state["messages"] else ""}
        )
        # 根据格式化输出的结果，返回不同的响应
        if guardrails_output.decision == "end": # type: ignore
            # logger.info("-----Fail to pass guardrails check-----")
            return {"messages": [AIMessage(content="抱歉，我家暂时没有这方面的商品，可以在别家看看哦~")], "jump_to": "end"}
        else:
            return None

            

    # def before_model(self, state: AgentState, runtime) -> Optional[Dict[str, Any]]:
    #     """在 before_model 阶段注入用户信息到 state"""
    #     try:
    #         # 从 runtime 获取用户信息
    #         current_user = self._get_user_from_runtime(runtime)

    #         # 获取用户角色的权限列表
    #         user_permissions = ROLE_PERMISSIONS.get(current_user['role'], [])

    #         log_with_timestamp(
    #             f"   📝 注入用户信息到 state - "
    #             f"用户: {current_user['username']}, "
    #             f"角色: {current_user['role'].value}"
    #         )

    #         # 将用户信息注入到 state
    #         return {
    #             "user_info": current_user,
    #             "user_permissions": [p.value for p in user_permissions]
    #         }
    #     except Exception as e:
    #         log_with_timestamp(f"   ❌ 用户信息注入异常: {str(e)}", "ERROR")
    #         return None