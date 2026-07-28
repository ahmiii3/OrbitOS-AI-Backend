from typing import Any, Dict
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.orchestrator.state import AgentState

class OrchestratorRouter:
    """
    The Orchestrator's brain. It classifies user intent and routes the execution
    to the appropriate specialized AI agent.
    """
    def __init__(self):
        self.llm = OpenAIProvider()
        
    async def route(self, state: AgentState) -> Dict[str, Any]:
        print("--- [Node] Orchestrator Router Execution ---")
        
        # Get the latest message from the user
        messages = state.get("messages", [])
        if not messages:
            return {"next_step": "end"}
            
        last_message = messages[-1].content
        
        # System prompt for classification
        system_prompt = (
            "You are the Orchestrator for OrbitOS AI. Your job is to classify the user's request "
            "into exactly ONE of the following categories based on their intent:\n"
            "- strategy (for business planning, goals, strategy)\n"
            "- marketing (for campaigns, SEO, content, ads)\n"
            "- sales (for leads, outreach, CRM)\n"
            "- finance (for budgeting, accounting, revenue)\n"
            "- operations (for logistics, HR, management)\n"
            "- customer_success (for support, retention, feedback)\n"
            "- general (if it doesn't fit any specific category or is just a general greeting)\n\n"
            "Return ONLY the category word in lowercase. Do not return any other text."
        )
        
        # Construct messages for the LLM
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message}
        ]
        
        # Call the LLM
        response = await self.llm.generate(prompt_messages)
        category = response.strip().lower()
        
        valid_routes = ["strategy", "marketing", "sales", "finance", "operations", "customer_success", "general"]
        if category not in valid_routes:
            category = "general"
            
        print(f"--- Orchestrator routed intent to: {category.upper()} ---")
        
        return {"next_step": category}
