from typing import Any, Callable, Coroutine, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from log.log import logging_config
from langchain.agents import create_agent
# 获取日志记录器
logger = logging_config.setup_logger(service="planner_node")

from .models import Task, PlannerOutput
from .prompts import create_planner_prompt_template
from ..state import InputState
from lg.sub_lg_graphrag.prompts import PLANNER_SYSTEM_PROMPT
from lg.lg_middlemares.safety_guardrail import SafetyGuardrail
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command, Send
from langchain.agents.middleware import hook_config
# 定义planner prompt
planner_prompt = create_planner_prompt_template()


def create_planner_node(
        llm: BaseChatModel, ignore_node: bool = False, next_action: str = "tool_selection"
) -> Callable[[InputState], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Create a planner node to be used in a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM used to process data.
    ignore_node : bool, optional
        Whether to ignore this node in the workflow, by default False

    Returns
    -------
    Callable[[InputState], OverallState]
        The LangGraph node.
    """
    planner_middlewares = [SafetyGuardrail()]
    planner_agent = create_agent(
        model=llm,
        system_prompt=PLANNER_SYSTEM_PROMPT,
        # tools=tools,
        middleware=planner_middlewares,  # type: ignore
        debug=False,  # 关闭调试模式
        response_format=PlannerOutput,  # 结构化输出格式
    )
    # # 创建planner chain
    # planner_chain: Runnable[Dict[str, Any], Any] = (
    #         planner_prompt | llm.with_structured_output(PlannerOutput)
    # )

    async def planner(state: InputState) -> Dict[str, Any]|Command:
        """
        Break user query into chunks, if appropriate.
        """
        if not ignore_node:
            planner_output = await planner_agent.ainvoke(
                {"messages": state.get("question", "")} # type: ignore
            ) # type: ignore
            if 'structured_response' in planner_output:
                planner_output = planner_output['structured_response']
            else:
                return Command(goto=Send("final_answer", {
                    "summary": planner_output['messages'][-1].content,
                }))
        else:
            planner_output = PlannerOutput(tasks=[])

        planner_task_decomposition = {
            "next_action": next_action,
            "tasks": planner_output.tasks
                     or [
                         Task(
                             question=state.get("question", ""),
                             parent_task=state.get("question", ""),
                         )
                     ]
        }

        # 日志打印格式，分别打印每个任务
        logger.info(f"Total Sub Task: {len(planner_task_decomposition['tasks'])}")

        for i, task in enumerate(planner_task_decomposition['tasks']):
            logger.info(f"Sub Task[{i + 1}]: {task.question}")

        return planner_task_decomposition

    return planner
