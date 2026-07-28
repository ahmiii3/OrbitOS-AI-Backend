from typing import Any, Dict, Literal
from pydantic import BaseModel, Field
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.orchestrator.state import AgentState
from langchain_core.messages import AIMessage

class RouteSchema(BaseModel):
    category: Literal["strategy", "marketing", "sales", "finance", "operations", "customer_success", "general"] = Field(
        description="The category of the user's intent."
    )

class OrchestratorRouter:
    """
    The Orchestrator's brain. It classifies user intent and routes the execution
    to the appropriate specialized AI agent using structured outputs.
    """
    def __init__(self):
        self.llm = OpenAIProvider()
        
    async def route(self, state: AgentState) -> Dict[str, Any]:
        print("--- [Node] Orchestrator Router Execution ---")
        
        # Get the latest message from the user
        messages = state.get("messages", [])
        if not messages:
            return {"next_step": "end"}
            
        last_message_obj = messages[-1]
        
        # Prevent infinite loops: if the last message is from an AI agent, we should stop
        if isinstance(last_message_obj, AIMessage):
            print("--- Orchestrator detected AI response, ending graph ---")
            return {"next_step": "end"}
            
        last_message = last_message_obj.content
        
        # System prompt for classification
        system_prompt = (
            "You are the Orchestrator for OrbitOS AI. Your job is to classify the user's request "
            "into exactly ONE of the provided categories based on their intent."
        )
        
        # Construct messages for the LLM
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message}
        ]
        
        # Call the LLM with structured output
        try:
            response = await self.llm.generate_structured(prompt_messages, RouteSchema)
            category = response.category
        except Exception as e:
            print(f"--- Orchestrator routing error: {e} ---")
            category = "general"
            
        print(f"--- Orchestrator routed intent to: {category.upper()} ---")
        
        return {"next_step": category}
