from langchain.chat_models import init_chat_model
from langchain.agents.middleware import before_model, wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
# from log.log import logger

@wrap_model_call # type: ignore
async def dynamic_model_router(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    large_model = init_chat_model(
        model="deepseek-chat",
        api_key='sk-c6a046d027964a88b8a071758f3dfca2',
        base_url="https://api.deepseek.com",
    )
    """
    根据对话上下文动态切换模型
    """
    # 获取当前对话的状态（例如消息列表）
    state = request.state
    messages = state.get("messages", [])

    # === 逻辑判断示例 ===
    # 场景 A: 如果对话轮数超过 5 轮，切换到大模型处理复杂上下文
    if len(messages) > 2:
        # logger.info("检测到对话轮数超过 5 轮，切换至 GPT-4o")
        # 使用 .override() 方法替换本次调用的模型
        request = request.override(model=large_model) # type: ignore
    # 场景 B: 如果用户角色为 VIP，始终使用大模型
    # elif request.runtime.context.get("user_role") == "VIP":
    #     print("--- [Middleware] 检测到 VIP 用户，切换至 GPT-4o ---")
    #     request = request.override(model=large_model) # type: ignore
    else:
        print("--- [Middleware] 使用默认小模型 GPT-4o-mini ---")
        # 默认使用 create_agent 初始化时传入的模型（即 small_model）

    # 继续执行调用
    return await handler(request) # type: ignore