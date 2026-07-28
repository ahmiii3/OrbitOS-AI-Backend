from typing import Any, Dict, List
from app.ai.agents.base import BaseAgent
from app.ai.orchestrator.state import AgentState
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from langchain_core.messages import AIMessage

STRATEGY_SYSTEM_PROMPT = """You are the Chief Strategy Officer (CSO) of OrbitOS AI. 
You are an expert in business strategy, competitive analysis, market positioning, goal decomposition, and roadmap planning.

Your responsibilities:
- Analyze the business owner's goals and break them into actionable strategic objectives.
- Provide SWOT analysis, competitive positioning, and market entry strategies.
- Create quarterly or annual business roadmaps.
- Recommend KPIs and success metrics for each strategic initiative.
- Use any uploaded business documents or context to ground your advice in the owner's real situation.

Guidelines:
- Always be specific and actionable, not generic.
- Format your responses in clear Markdown with headers, bullet points, and bold text.
- If business context is available from uploaded documents, reference it directly.
- If no context is available, ask clarifying questions to better understand the business.
"""


class StrategyAgent(BaseAgent):
    """
    Strategy Agent - Handles business planning, goal decomposition,
    competitive analysis, and strategic roadmap creation.
    """
    
    def __init__(self):
        super().__init__(
            name="Strategy Agent",
            description="Handles business planning, goal decomposition, and strategic analysis."
        )
    
    def _get_rag_context(self, workspace_id: str, query: str) -> str:
        """Fetch relevant documents from the Knowledge Base."""
        try:
            embedding_service = EmbeddingService()
            vector_store = VectorStoreService(embedding_service=embedding_service)
            
            results = vector_store.search(
                query=query,
                top_k=5,
                filter_dict={"workspace_id": workspace_id}
            )
            
            if not results:
                return ""
            
            context_parts = []
            for r in results:
                context_parts.append(r["content"])
            
            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            print(f"[StrategyAgent] RAG search failed (non-critical): {e}")
            return ""
    
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        print("--- [Node] Strategy Agent Execution ---")
        
        # 1. Get the latest user message
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [AIMessage(content="I need a message to work with. How can I help with your strategy?")],
                "current_agent": self.name
            }
        
        last_message = messages[-1].content
        workspace_id = state.get("workspace_id", "")
        business_goal = state.get("business_goal", "Not specified.")
        
        # 2. Retrieve relevant context from Knowledge Base
        rag_context = self._get_rag_context(workspace_id, last_message) if workspace_id else ""
        
        # 3. Build the prompt
        system_prompt = STRATEGY_SYSTEM_PROMPT
        system_prompt += f"\n\nThe business owner's overarching goal is: {business_goal}"
        
        if rag_context:
            system_prompt += f"\n\n<BUSINESS_CONTEXT>\nThe following is relevant information from the business owner's uploaded documents:\n{rag_context}\n</BUSINESS_CONTEXT>"
        
        # 4. Call LLM
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message}
        ]
        
        response = await self.llm.generate(prompt_messages)
        
        return {
            "messages": [AIMessage(content=response)],
            "current_agent": self.name
        }


# Singleton instance for the graph
strategy_agent = StrategyAgent()
