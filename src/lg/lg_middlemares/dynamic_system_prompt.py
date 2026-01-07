from langchain.agents.middleware import dynamic_prompt, ModelRequest
from lg.lg_prompts import GET_ADDITIONAL_SYSTEM_PROMPT
@dynamic_prompt
def generate_sys_prompt(request:ModelRequest):
    """根据logic生成不同提示词"""
    logic = request.runtime.context.get("logic", "user") # type: ignore

    return GET_ADDITIONAL_SYSTEM_PROMPT.format(
            logic=logic
        )
