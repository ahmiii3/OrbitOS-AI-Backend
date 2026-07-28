from typing import Any, Dict
from app.ai.agents.base import BaseAgent
from app.ai.orchestrator.state import AgentState
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from langchain_core.messages import AIMessage

SALES_SYSTEM_PROMPT = """You are the Head of Sales of OrbitOS AI.
You are an expert in B2B and B2C sales processes, cold outreach, CRM structuring, pipeline strategies, and sales messaging.

Your responsibilities:
- Create structured sales strategies, email sequences, and cold outreach templates.
- Provide advice on objection handling and lead qualification.
- Structure CRM pipelines tailored to specific business models.
- Use any uploaded business documents to align your pitches with the product's value proposition.

Guidelines:
- Keep your tone persuasive, direct, and professional.
- Format your responses using clear Markdown (headers, bullet points, bold text).
- Include practical, actionable steps for the sales team to execute.
"""

class SalesAgent(BaseAgent):
    """
    Sales Agent - Handles sales outreach, pipelines, and strategies.
    """
    
    def __init__(self):
        super().__init__(
            name="Sales Agent",
            description="Handles sales outreach, pipelines, and CRM strategies."
        )
    
    def _needs_context(self, query: str) -> bool:
        """Simple heuristic to determine if RAG context is needed based on query keywords."""
        keywords = ["product", "company", "our", "my", "business", "pitch", "value proposition", "target"]
        query_lower = query.lower()
        return any(kw in query_lower for kw in keywords)

    def _get_rag_context(self, workspace_id: str, query: str) -> str:
        """Fetch relevant documents from the Knowledge Base."""
        try:
            embedding_service = EmbeddingService()
            vector_store = VectorStoreService(embedding_service=embedding_service)
            
            results = vector_store.search(
                query=query,
                top_k=3,
                filter_dict={"workspace_id": workspace_id}
            )
            
            if not results:
                return ""
            
            context_parts = []
            for r in results:
                context_parts.append(r["content"])
            
            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            print(f"[SalesAgent] RAG search failed: {e}")
            return ""
    
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        print("--- [Node] Sales Agent Execution ---")
        
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [AIMessage(content="I need a query to work with. How can I assist your sales team?")],
                "current_agent": self.name
            }
        
        last_message = messages[-1].content
        workspace_id = state.get("workspace_id", "")
        business_goal = state.get("business_goal", "Not specified.")
        
        # Determine if we should query the Knowledge Base
        rag_context = ""
        if workspace_id and self._needs_context(last_message):
            print(f"--- [SalesAgent] Fetching context for: {last_message[:30]}... ---")
            rag_context = self._get_rag_context(workspace_id, last_message)
        
        # Build the prompt
        system_prompt = SALES_SYSTEM_PROMPT
        system_prompt += f"\n\nThe business owner's overarching goal is: {business_goal}"
        
        if rag_context:
            system_prompt += f"\n\n<BRAND_CONTEXT>\nThe following is relevant information from the business owner's uploaded documents:\n{rag_context}\n</BRAND_CONTEXT>"
        
        # Call LLM
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
sales_agent = SalesAgent()
