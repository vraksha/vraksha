###################################################################
# DEPRECATED
#
# Kept just for backup
###############################################################


"""
import abc
import inspect
import pathlib
from typing import Type, Callable
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from sub_agents.base import BaseSubAgent
from src.agent.orchestrator import orchestrator, 

class SystemDeps(BaseModel):
    session_id: str
    workspace_path: str



def register_agent(enabled: bool = True):
    '''
    Class decorator to explicitly mount a sub-agent to the orchestrator.
    Allows easy toggling and prevents unintended registration during testing/drafting.
    '''
    def decorator(cls: Type[BaseSubAgent]):
        if not enabled:
            return cls
            
        # Validate structure before binding
        for required in ['name', 'description', 'input_schema', 'output_schema']:
            if not hasattr(cls, required):
                raise TypeError(f"SubAgent Class '{cls.__name__}' missing configuration: '{required}'")
        
        # Instantiate and bootstrap
        instance = cls()
        
        # 1. Resolve skill.md from the file defining the sub-class
        module_file = inspect.getfile(cls)
        prompt_path = pathlib.Path(module_file).parent / "skill.md"
        system_prompt = prompt_path.read_text() if prompt_path.exists() else "Specialized Assistant."

        # 2. Build the Agent
        instance.agent = Agent(
            'openai:gpt-4o',
            deps_type=SystemDeps,
            result_type=cls.output_schema,
            system_prompt=system_prompt
        )

        # 3. Bind local tools
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if hasattr(attr, "_is_agent_tool"):
                instance.agent.tool(attr)

        # 4. Expose as Orchestrator Tool
        tool_name = f"delegate_to_{cls.name.lower().replace(' ', '_')}"
        
        @orchestrator.tool(name=tool_name)
        async def dynamic_tool(ctx: RunContext[SystemDeps], payload: cls.input_schema) -> cls.output_schema:
            result = await instance.agent.run(
                payload.model_dump_json(), 
                deps=ctx.deps, 
                usage=ctx.usage
            )
            return result.data

        dynamic_tool.__doc__ = f"{cls.description} Input: {cls.input_schema.__name__}"
        return cls

    return decorator

def agent_tool(func: Callable) -> Callable:
    func._is_agent_tool = True
    return 
    """