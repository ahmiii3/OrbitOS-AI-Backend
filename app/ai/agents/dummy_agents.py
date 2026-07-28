from typing import Any, Dict
from app.ai.agents.base import BaseAgent
from app.ai.orchestrator.state import AgentState
from langchain_core.messages import AIMessage

class DummyAgent(BaseAgent):
    """
    A generic dummy agent used as a placeholder for Phase 7 routing.
    """
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        print(f"--- [Node] {self.name} Execution ---")
        
        # In a real implementation, we would call self.llm.generate() here
        response_text = f"Hello from the {self.name}! I received your intent related to {self.name.split()[0].lower()}."
        
        return {
            "messages": [AIMessage(content=response_text)],
            "current_agent": self.name
        }

# Instantiate dummy agents for the LangGraph nodes
# (All Agents are now real agents)
# No dummy agents remaining.
